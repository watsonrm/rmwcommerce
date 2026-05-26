#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Article freshness checker — Stage 1 of article-research.

Runs from GitHub Actions on a weekly schedule. Pure stdlib (urllib + re +
hashlib + json) — no pip install in CI. For every guide under `guides/**/*.md`:

  1. Extract every URL cited in the article (markdown `[text](url)` + bare URLs).
  2. For each URL: HEAD/GET it, capture HTTP status, Last-Modified header,
     and a SHA-256 of the response body for change detection.
  3. Diff against bin/.article-state.json (per-URL last-seen status / mtime / hash).
  4. Emit a per-article drift report into bin/.article-fresh.json — Stage 2
     (bin/article-suggest-updates.py) consumes that as the handoff artifact.

Two-stage architecture (same shape as detector-research in tokenmin-scanner):
  Stage 1 (this file): URL liveness + change detection. Pure stdlib. Always
    runs. Writes the per-article drift list. Optionally files raw issues
    when --legacy-file-issues is set (used when no ANTHROPIC_API_KEY).
  Stage 2 (article-suggest-updates.py): per-drift LLM judgment + suggested
    edits. Updates one open issue per article (kept-open, edited in place).

State file lives at bin/.article-state.json, committed to repo by the
workflow. Survives laptop shutdown by living in the repo, not on disk.

Drift event types (set in the per-event `change` field):
  - new-url            : URL appears in an article but has never been tracked
  - status-changed     : HTTP status changed since last check (e.g. 200 → 404)
  - content-changed    : body hash changed since last check
  - last-modified-bump : server Last-Modified is newer than last seen
  - moved              : final URL after redirects differs from cited URL
  - fetch-failed       : the URL could not be fetched this run (timeout / DNS)

Failure-isolated: one broken URL doesn't kill the article; one broken article
doesn't kill the run. We always write a valid .article-fresh.json so Stage 2
can run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = REPO_ROOT / "bin"
GUIDES_DIR = REPO_ROOT / "guides"
STATE_PATH = BIN_DIR / ".article-state.json"
FRESH_PATH = BIN_DIR / ".article-fresh.json"

USER_AGENT = "rmwcommerce-article-research/1.0 (+https://github.com/watsonrm/rmwcommerce)"
TIMEOUT_SEC = 20
# Soft cap on bytes hashed per URL — anything over this we still hash, just
# slice; keeps memory bounded on the rare giant-PDF citation.
MAX_BODY_BYTES = 2_000_000


# ----- URL extraction -------------------------------------------------------

# Markdown link: [text](url) — url is anything up to the first whitespace or `)`
# Bare URL: starts with http(s):// and runs until whitespace, `)`, `]`, `<`, `>`,
# or trailing punctuation.
_MD_LINK_RE = re.compile(r"\[(?:[^\]]*)\]\((https?://[^\s)]+)\)")
_BARE_URL_RE = re.compile(r"(?<![\(\"'<])(https?://[^\s\)\]<>'\"`]+)")
# Trailing punctuation that should not be part of the URL.
_URL_TRAIL_STRIP = ".,;:!?)]}>"


def _normalize_url(url: str) -> str:
    """Strip trailing punctuation + fragment that doesn't change the resource."""
    url = url.strip()
    while url and url[-1] in _URL_TRAIL_STRIP:
        url = url[:-1]
    return url


def extract_urls(md_text: str) -> list[str]:
    """Return every distinct URL cited in the markdown, in stable order."""
    found: list[str] = []
    seen: set[str] = set()
    for m in _MD_LINK_RE.finditer(md_text):
        u = _normalize_url(m.group(1))
        if u and u not in seen:
            seen.add(u)
            found.append(u)
    for m in _BARE_URL_RE.finditer(md_text):
        u = _normalize_url(m.group(1))
        if u and u not in seen:
            seen.add(u)
            found.append(u)
    return found


# ----- Fetch ----------------------------------------------------------------

def _fetch_meta(url: str) -> dict:
    """Fetch a URL, return status + Last-Modified + body hash + final URL.

    Returns a dict with keys:
      - status        : int HTTP status code (0 if fetch failed entirely)
      - last_modified : str header value or "" if missing
      - body_sha256   : hex digest of (up to MAX_BODY_BYTES of) the body
      - final_url     : str URL after redirects (may equal input URL)
      - error         : str empty on success, else a short error description
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
            body = r.read(MAX_BODY_BYTES)
            return {
                "status": r.status,
                "last_modified": r.headers.get("Last-Modified", "") or "",
                "body_sha256": hashlib.sha256(body).hexdigest(),
                "final_url": r.geturl() or url,
                "error": "",
            }
    except urllib.error.HTTPError as exc:
        # Server responded with an error code (4xx/5xx). Capture the code so
        # we can detect 200→404 drift cleanly.
        return {
            "status": int(exc.code or 0),
            "last_modified": exc.headers.get("Last-Modified", "") if exc.headers else "",
            "body_sha256": "",
            "final_url": url,
            "error": f"http {exc.code}",
        }
    except (urllib.error.URLError, OSError, ValueError) as exc:
        return {
            "status": 0,
            "last_modified": "",
            "body_sha256": "",
            "final_url": url,
            "error": str(exc)[:160],
        }


# ----- State I/O ------------------------------------------------------------

def _load_state() -> dict:
    """Schema: { 'urls': { url: { status, last_modified, body_sha256, last_checked } } }"""
    if STATE_PATH.is_file():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    return {"urls": {}}


def _save_state(state: dict) -> None:
    STATE_PATH.write_text(
        json.dumps(state, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _save_fresh(payload: dict) -> None:
    FRESH_PATH.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


# ----- Diff -----------------------------------------------------------------

def diff_url(url: str, meta: dict, prior: dict | None) -> dict | None:
    """Compare current meta vs prior state for one URL. Return a drift event
    dict if anything notable changed, else None.

    Drift kinds (priority order; we emit the first that matches):
      1. new-url            (no prior record)
      2. fetch-failed       (status == 0)
      3. status-changed     (prior.status != current.status)
      4. moved              (final_url != requested url AND prior didn't already track it)
      5. content-changed    (body_sha256 differs from prior)
      6. last-modified-bump (Last-Modified header advanced)
    """
    if prior is None:
        return {
            "url": url,
            "change": "new-url",
            "status": meta["status"],
            "final_url": meta["final_url"],
            "note": "first time this URL has been seen by article-freshness",
        }
    if meta["status"] == 0:
        return {
            "url": url,
            "change": "fetch-failed",
            "status": 0,
            "final_url": meta["final_url"],
            "note": meta.get("error", "fetch failed"),
        }
    if prior.get("status") and prior["status"] != meta["status"]:
        return {
            "url": url,
            "change": "status-changed",
            "status": meta["status"],
            "prior_status": prior["status"],
            "final_url": meta["final_url"],
            "note": f"HTTP status {prior['status']} → {meta['status']}",
        }
    if meta["final_url"] and meta["final_url"] != url and meta["final_url"] != prior.get("final_url"):
        return {
            "url": url,
            "change": "moved",
            "status": meta["status"],
            "final_url": meta["final_url"],
            "note": f"redirects to {meta['final_url']}",
        }
    if meta["body_sha256"] and prior.get("body_sha256") and meta["body_sha256"] != prior["body_sha256"]:
        return {
            "url": url,
            "change": "content-changed",
            "status": meta["status"],
            "final_url": meta["final_url"],
            "note": "response body hash changed since last check",
        }
    if meta["last_modified"] and prior.get("last_modified") and meta["last_modified"] != prior["last_modified"]:
        return {
            "url": url,
            "change": "last-modified-bump",
            "status": meta["status"],
            "final_url": meta["final_url"],
            "note": f"Last-Modified advanced to {meta['last_modified']}",
        }
    return None


# ----- Legacy filing (no API key path) --------------------------------------

def _file_drift_issue(repo: str, article_rel: str, events: list[dict]) -> bool:
    """Open OR update a per-article 'Article freshness' issue with raw drift
    events. Used when ANTHROPIC_API_KEY is not configured (legacy fallback).

    Mirrors the kept-open-and-edited behavior Stage 2 will use; without
    the LLM section, just the raw drift list.
    """
    title = f"Article freshness: {article_rel}"
    now_iso = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    lines = [
        f"**Article:** `{article_rel}`",
        f"**Last checked:** {now_iso}",
        "",
        "## Drift events this week",
        "",
    ]
    for ev in events:
        lines.append(
            f"- **{ev['change']}** — {ev['url']}"
            + (f" — _{ev.get('note', '')}_" if ev.get("note") else "")
        )
    lines += [
        "",
        "## Suggested edits (from Claude)",
        "",
        "_Stage 2 not run this cycle (no `ANTHROPIC_API_KEY` configured)._",
        "",
        "## Verdict",
        "",
        "- [ ] Review",
        "- [ ] Apply edits / re-anchor sources",
        "- [ ] Close",
        "",
        "---",
        "_Auto-filed by `bin/article-freshness.py`. Kept open and edited in "
        "place as the weekly cron runs._",
    ]
    body = "\n".join(lines)

    existing_number = _find_open_issue(repo, title)
    if existing_number is not None:
        try:
            subprocess.run(
                ["gh", "issue", "edit", str(existing_number),
                 "--repo", repo,
                 "--body", body],
                check=True, capture_output=True, text=True, timeout=30,
            )
            print(f"  ~ updated existing issue #{existing_number}: {title[:80]}")
            return True
        except subprocess.CalledProcessError as exc:
            print(f"  ! gh issue edit failed: {exc.stderr}", file=sys.stderr)
            return False

    try:
        subprocess.run(
            ["gh", "issue", "create",
             "--repo", repo,
             "--title", title,
             "--body", body,
             "--label", "article-freshness"],
            check=True, capture_output=True, text=True, timeout=30,
        )
        print(f"  + filed: {title[:80]}")
        return True
    except subprocess.CalledProcessError as exc:
        print(f"  ! gh issue create failed: {exc.stderr}", file=sys.stderr)
        return False


def _find_open_issue(repo: str, title: str) -> int | None:
    """Return the issue number of an open issue whose title matches exactly,
    or None.
    """
    try:
        r = subprocess.run(
            ["gh", "issue", "list",
             "--repo", repo,
             "--state", "open",
             "--label", "article-freshness",
             "--search", f'"{title}" in:title',
             "--json", "number,title",
             "--limit", "10"],
            check=True, capture_output=True, text=True, timeout=30,
        )
        for it in json.loads(r.stdout or "[]"):
            if it.get("title") == title:
                return int(it.get("number"))
    except subprocess.CalledProcessError as exc:
        print(f"  ! gh issue list failed: {exc.stderr}", file=sys.stderr)
    return None


# ----- Main -----------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="article-freshness stage-1 URL liveness + drift detection")
    parser.add_argument(
        "--legacy-file-issues",
        action="store_true",
        help=(
            "Fallback mode: file (or update) one issue per article with drift, "
            "without the LLM-suggested-edits section. Used when ANTHROPIC_API_KEY "
            "is not configured for Stage 2."
        ),
    )
    parser.add_argument(
        "--guides-dir",
        default=str(GUIDES_DIR),
        help="Override the guides directory (default: %(default)s)",
    )
    args = parser.parse_args(argv)

    repo = os.environ.get("GITHUB_REPOSITORY", "watsonrm/rmwcommerce")
    guides_dir = Path(args.guides_dir).resolve()
    if not guides_dir.is_dir():
        print(f"article-freshness: guides dir {guides_dir} does not exist; nothing to do.")
        _save_fresh({"generated_at": datetime.now(tz=timezone.utc).isoformat(), "articles": []})
        return 0

    articles = sorted(guides_dir.rglob("*.md"))
    mode = "legacy (per-article issues)" if args.legacy_file_issues else "stage-1 (handoff to suggest-updates)"
    print(f"article-freshness [{mode}]: {len(articles)} article(s), target repo={repo}")

    state = _load_state()
    urls_state: dict[str, dict] = state.setdefault("urls", {})

    now_iso = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")

    articles_payload: list[dict] = []
    total_urls = 0
    total_drift = 0
    fetched_this_run: dict[str, dict] = {}  # url → meta, so we don't refetch when 2 articles cite same URL

    for art_path in articles:
        rel = art_path.relative_to(REPO_ROOT).as_posix()
        try:
            text = art_path.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"  ! {rel}: read failed: {exc}", file=sys.stderr)
            continue
        urls = extract_urls(text)
        total_urls += len(urls)
        print(f"  {rel}: {len(urls)} URL(s)")

        events: list[dict] = []
        for url in urls:
            meta = fetched_this_run.get(url)
            if meta is None:
                meta = _fetch_meta(url)
                fetched_this_run[url] = meta
            prior = urls_state.get(url)
            ev = diff_url(url, meta, prior)
            if ev is not None:
                events.append(ev)

        if events:
            total_drift += len(events)
            articles_payload.append({
                "article": rel,
                "events": events,
            })
            print(f"    drift: {len(events)} event(s)")

    # Persist current observations for every URL we touched this run, even
    # if there was no drift — that's what makes future diffs meaningful.
    for url, meta in fetched_this_run.items():
        urls_state[url] = {
            "status": meta["status"],
            "last_modified": meta["last_modified"],
            "body_sha256": meta["body_sha256"],
            "final_url": meta["final_url"],
            "last_checked": now_iso,
        }
    _save_state(state)

    fresh_payload = {
        "generated_at": now_iso,
        "articles": articles_payload,
    }
    _save_fresh(fresh_payload)

    print(
        f"  summary: {total_urls} URL fetch(es), {total_drift} drift event(s) "
        f"across {len(articles_payload)} article(s)"
    )

    if args.legacy_file_issues:
        if not articles_payload:
            print("  nothing to file (no drift this week). Done.")
            return 0
        for art in articles_payload:
            _file_drift_issue(repo, art["article"], art["events"])
        return 0

    print(f"  wrote {FRESH_PATH.name} for stage 2 (article-suggest-updates.py).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
