#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Article-research synthesis stage — Stage 2 (Claude-judged suggestions).

Stage 2 of the two-stage article-research workflow (parallels the
detector-research / detector-synthesize pair in watsonrm/tokenmin-scanner):

    Stage 1 (bin/article-freshness.py) — URL extraction + liveness + drift
    detection across every `guides/**/*.md`. Pure stdlib. Writes the per-
    article drift report to bin/.article-fresh.json. Always runs.

    Stage 2 (this file) — for each article with drift events, ask Claude
    per event:
      - Is the article's claim still accurate given the URL's current state?
      - Has anything been published recently that contradicts / updates the claim?
      - Is there new content worth incorporating into the article?

    Then file OR update ONE issue per article (title `Article freshness:
    <relative-path>`, label `article-freshness`). The issue is kept open
    and edited in place — same article + same drift on the next cron just
    refreshes the body, no new issue.

Cost-cap math (default $1.00/run, same shape as detector-synthesize):
  - Sonnet 4.6 pricing: $3/MTok input, $15/MTok output (as of 2026-05).
  - Typical synthesis call: ~10K input tokens (prompt + article + URL body)
    + ~400 output tokens (markdown suggestions) ≈ $0.036/call.
  - $1.00 cap → ~28 events per run before stop, then the rest are noted as
    "not triaged this week (cost cap)" in the per-article issue body.
  - Cost cap is a SOFT ceiling: we stop calling the API the moment cumulative
    usage exceeds it. Already-applied article issues are not rolled back.

Stdlib only. HTTP POST direct to the Anthropic Messages API — no `anthropic`
SDK install needed in CI.

Environment:
  - ANTHROPIC_API_KEY     required; the secret Rick has to add to the repo
  - GITHUB_REPOSITORY     auto-set by GitHub Actions
  - GH_TOKEN              for `gh` CLI calls
  - TOKENMIN_SYNTH_MODEL  optional override; default 'claude-sonnet-4-6'
  - TOKENMIN_SYNTH_BUDGET optional USD cap as float; default 1.00
  - TOKENMIN_SYNTH_MAX_FETCH_CHARS optional; default 40_000

Self-healing: if the API errors mid-loop, the failing event is recorded as
"api error" in the article issue and the loop continues. Partial results >
zero results.
"""
from __future__ import annotations

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
FRESH_PATH = BIN_DIR / ".article-fresh.json"
PROMPT_PATH = BIN_DIR / "article-prompt.md"

DEFAULT_MODEL = "claude-sonnet-4-6"
DEFAULT_BUDGET_USD = 1.00
DEFAULT_MAX_FETCH_CHARS = 40_000
DEFAULT_MAX_ARTICLE_CHARS = 30_000
USER_AGENT = "rmwcommerce-article-suggest/1.0 (+https://github.com/watsonrm/rmwcommerce)"
TIMEOUT_SEC = 30

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

# Per-million-token USD pricing. Used only for the cost cap; if a model isn't
# listed we fall back to Sonnet's rates (worst case = stop sooner).
PRICING_PER_MTOK = {
    "claude-sonnet-4-6":  (3.00, 15.00),
    "claude-sonnet-4-7":  (3.00, 15.00),
    "claude-opus-4-6":    (15.00, 75.00),
    "claude-opus-4-7":    (15.00, 75.00),
    "claude-haiku-4-5":   (0.80,  4.00),
}


# ----- HTTP helpers ---------------------------------------------------------

def _fetch_url_content(url: str, max_chars: int) -> str:
    """GET a URL and return its body truncated to max_chars. Raw HTML is fine —
    Claude reads it directly without stripping.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_SEC) as r:
        raw = r.read(max_chars * 4)
    body = raw.decode("utf-8", errors="replace")
    if len(body) > max_chars:
        body = body[:max_chars] + "\n\n[...truncated by article-suggest-updates...]"
    return body


def _call_anthropic(api_key: str, model: str, system: str, user_msg: str) -> dict:
    """POST to /v1/messages. Returns parsed JSON response.

    System prompt is sent with `cache_control: ephemeral` so multi-event runs
    only pay full input rate on the first call — subsequent calls hit the
    cache for the prompt portion.
    """
    payload = {
        "model": model,
        "max_tokens": 1024,
        "system": [
            {
                "type": "text",
                "text": system,
                "cache_control": {"type": "ephemeral"},
            },
        ],
        "messages": [
            {"role": "user", "content": user_msg},
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def _verdict_from_response(resp: dict) -> dict:
    """Parse the strict-JSON verdict out of the model reply. Defensively strip
    ```json``` fences in case the model slips up.
    """
    content_blocks = resp.get("content", [])
    text_blob = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text").strip()
    text_blob = re.sub(r"^```(?:json)?\s*", "", text_blob)
    text_blob = re.sub(r"\s*```$", "", text_blob)
    return json.loads(text_blob)


def _usage_cost_usd(model: str, usage: dict) -> float:
    """Compute USD cost from the Anthropic usage block.

    Counts cache_creation as input (1.25x), cache_read as input (0.10x); rest
    at full input rate. Output at output rate.
    """
    in_rate, out_rate = PRICING_PER_MTOK.get(model, PRICING_PER_MTOK[DEFAULT_MODEL])
    input_tok = usage.get("input_tokens", 0)
    cache_creation = usage.get("cache_creation_input_tokens", 0)
    cache_read = usage.get("cache_read_input_tokens", 0)
    output_tok = usage.get("output_tokens", 0)
    cost = (
        input_tok        * in_rate           / 1_000_000
        + cache_creation * (in_rate * 1.25)  / 1_000_000
        + cache_read     * (in_rate * 0.10)  / 1_000_000
        + output_tok     * out_rate          / 1_000_000
    )
    return cost


# ----- GitHub issue helpers -------------------------------------------------

def _find_open_issue(repo: str, title: str) -> int | None:
    """Return the issue number of an open `article-freshness` issue whose
    title exactly matches, or None.
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


def _upsert_article_issue(repo: str, title: str, body: str) -> bool:
    """Create the issue if it doesn't exist; otherwise edit in place. Returns
    True on success.
    """
    existing = _find_open_issue(repo, title)
    if existing is not None:
        try:
            subprocess.run(
                ["gh", "issue", "edit", str(existing),
                 "--repo", repo,
                 "--body", body],
                check=True, capture_output=True, text=True, timeout=30,
            )
            print(f"  ~ updated existing issue #{existing}: {title[:80]}")
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


# ----- Article context helpers ----------------------------------------------

def _load_article_excerpt(article_rel: str, url: str, max_chars: int) -> str:
    """Return a slice of the article surrounding the URL, so Claude can judge
    the claim in context instead of being handed only the URL.

    Strategy: find every line that contains the URL, return up to 12 lines of
    leading + trailing context around each match. If the URL isn't found
    verbatim (e.g. we normalized off trailing punctuation), fall back to the
    first N chars of the article.
    """
    path = REPO_ROOT / article_rel
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    lines = text.splitlines()
    hits = [i for i, ln in enumerate(lines) if url in ln]
    if not hits:
        # Couldn't pinpoint — give Claude the lead so it can still judge tone.
        return text[:max_chars]
    excerpts: list[str] = []
    used: set[int] = set()
    for i in hits[:5]:  # cap excerpts so we don't blow the budget
        lo = max(0, i - 6)
        hi = min(len(lines), i + 7)
        chunk_lines: list[str] = []
        for j in range(lo, hi):
            if j in used:
                continue
            used.add(j)
            chunk_lines.append(lines[j])
        if chunk_lines:
            excerpts.append("\n".join(chunk_lines))
    joined = "\n\n---\n\n".join(excerpts)
    if len(joined) > max_chars:
        joined = joined[:max_chars] + "\n\n[...truncated...]"
    return joined


# ----- Issue body assembly --------------------------------------------------

def _build_issue_body(
    article_rel: str,
    now_iso: str,
    event_results: list[dict],
    deferred_events: list[dict],
    model: str,
    total_cost: float,
    budget_usd: float,
) -> str:
    """Render the per-article issue body. event_results carries the Claude
    output per drift event; deferred_events lists events we skipped under
    the cost cap.
    """
    lines = [
        f"**Article:** `{article_rel}`",
        f"**Last checked:** {now_iso}",
        f"**Model:** `{model}` · cost this run: ${total_cost:.4f} / ${budget_usd:.2f}",
        "",
        "## Drift events this week",
        "",
    ]
    for r in event_results:
        ev = r["event"]
        lines.append(
            f"- **{ev['change']}** — {ev['url']}"
            + (f" — _{ev.get('note', '')}_" if ev.get("note") else "")
        )
    for ev in deferred_events:
        lines.append(
            f"- **{ev['change']}** — {ev['url']} _(not triaged this week — cost cap)_"
        )

    lines += ["", "## Suggested edits (from Claude)", ""]
    any_suggestions = False
    for r in event_results:
        ev = r["event"]
        verdict = r.get("verdict") or {}
        err = r.get("error", "")
        lines.append(f"### {ev['change']} · {ev['url']}")
        lines.append("")
        if err:
            lines.append(f"_Skipped: {err}_")
            lines.append("")
            continue
        any_suggestions = True
        accurate = verdict.get("claim_still_accurate", "")
        contradicted = verdict.get("recent_contradiction", "")
        new_content = verdict.get("new_content_worth_incorporating", "")
        suggested = (verdict.get("suggested_edit") or "").strip()
        recommendation = verdict.get("recommendation", "")
        evidence = (verdict.get("evidence_quote") or "").strip()

        lines.append(f"- **Claim still accurate?** {accurate or '(no verdict)'}")
        lines.append(f"- **Recent contradiction?** {contradicted or '(none reported)'}")
        lines.append(f"- **New content worth incorporating?** {new_content or '(none reported)'}")
        lines.append(f"- **Recommendation:** {recommendation or '(none)'}")
        if suggested:
            lines.append("")
            lines.append("**Suggested edit:**")
            lines.append("")
            lines.append("> " + suggested.replace("\n", "\n> "))
        if evidence:
            lines.append("")
            lines.append("**Evidence (verbatim quote from source):**")
            lines.append("")
            lines.append("> " + evidence.replace("\n", "\n> "))
        lines.append("")
    if not any_suggestions and not deferred_events:
        lines.append("_No actionable suggestions this cycle._")
        lines.append("")

    if deferred_events:
        lines += [
            "## Deferred (cost cap)",
            "",
            "These events hit the per-run cost cap and will be picked up by the "
            "next weekly cron:",
            "",
        ]
        for ev in deferred_events:
            lines.append(f"- {ev['url']} ({ev['change']})")
        lines.append("")

    lines += [
        "## Verdict",
        "",
        "- [ ] Review and apply",
        "- [ ] No action needed",
        "- [ ] Source moved (update link target)",
        "- [ ] Source dead (replace citation)",
        "",
        "---",
        "_Auto-maintained by `bin/article-suggest-updates.py`. Kept open and "
        "edited in place as the weekly cron runs — same drift on the next "
        "run just refreshes this body, no new issue._",
    ]
    return "\n".join(lines)


# ----- Main -----------------------------------------------------------------

def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("article-suggest-updates: ANTHROPIC_API_KEY not set; nothing to do.")
        # Exit 0 — Stage 1 has already filed raw drift issues in legacy mode.
        return 0

    if not FRESH_PATH.is_file():
        print(
            "article-suggest-updates: no .article-fresh.json yet "
            "(first run or stage-1 found nothing). Done."
        )
        return 0

    try:
        fresh_payload = json.loads(FRESH_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"article-suggest-updates: can't read fresh list: {exc}", file=sys.stderr)
        return 1
    articles = fresh_payload.get("articles", [])
    if not articles:
        print("article-suggest-updates: fresh list is empty. Nothing to judge.")
        return 0

    repo = os.environ.get("GITHUB_REPOSITORY", "watsonrm/rmwcommerce")
    model = os.environ.get("TOKENMIN_SYNTH_MODEL", DEFAULT_MODEL)
    try:
        budget_usd = float(os.environ.get("TOKENMIN_SYNTH_BUDGET", DEFAULT_BUDGET_USD))
    except ValueError:
        budget_usd = DEFAULT_BUDGET_USD
    try:
        max_fetch = int(os.environ.get("TOKENMIN_SYNTH_MAX_FETCH_CHARS", DEFAULT_MAX_FETCH_CHARS))
    except ValueError:
        max_fetch = DEFAULT_MAX_FETCH_CHARS

    prompt = PROMPT_PATH.read_text(encoding="utf-8")
    now_iso = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")

    print(
        f"article-suggest-updates: {len(articles)} article(s) with drift, repo={repo}, "
        f"model={model}, budget=${budget_usd:.2f}"
    )

    cumulative_cost = 0.0
    total_events_judged = 0
    total_events_skipped_cap = 0
    total_events_failed = 0

    for art in articles:
        article_rel = art.get("article", "")
        events = art.get("events", [])
        if not article_rel or not events:
            continue

        per_article_cost = 0.0
        event_results: list[dict] = []
        deferred: list[dict] = []

        for ev in events:
            if cumulative_cost >= budget_usd:
                deferred.append(ev)
                total_events_skipped_cap += 1
                continue

            url = ev.get("url", "")
            change = ev.get("change", "")

            # For fetch-failed and status-changed (4xx/5xx), don't bother
            # asking Claude to read the page — we already know the answer.
            # Synthesize a deterministic verdict.
            if change in ("fetch-failed",) or (change == "status-changed" and ev.get("status", 0) >= 400):
                event_results.append({
                    "event": ev,
                    "verdict": {
                        "claim_still_accurate": "unknown — source is unreachable",
                        "recent_contradiction": "n/a",
                        "new_content_worth_incorporating": "n/a",
                        "suggested_edit": (
                            "Find a working replacement URL for this citation, "
                            "or remove the citation and soften the surrounding "
                            "claim to what can be supported by remaining sources."
                        ),
                        "recommendation": "source-moved-or-dead",
                        "evidence_quote": "",
                    },
                    "error": "",
                })
                total_events_judged += 1
                continue

            try:
                page = _fetch_url_content(url, max_fetch)
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                print(f"  ! fetch failed for {url}: {exc}", file=sys.stderr)
                event_results.append({"event": ev, "error": f"fetch failed: {exc}"})
                total_events_failed += 1
                continue

            article_excerpt = _load_article_excerpt(article_rel, url, DEFAULT_MAX_ARTICLE_CHARS)

            user_msg = (
                f"Article: {article_rel}\n"
                f"Drift change kind: {change}\n"
                f"Drift note: {ev.get('note', '')}\n"
                f"Cited URL: {url}\n"
                f"Final URL after redirects: {ev.get('final_url', url)}\n\n"
                f"--- BEGIN ARTICLE EXCERPT (the citation in context) ---\n"
                f"{article_excerpt}\n"
                f"--- END ARTICLE EXCERPT ---\n\n"
                f"--- BEGIN CITED PAGE CONTENT (current state) ---\n"
                f"{page}\n"
                f"--- END CITED PAGE CONTENT ---"
            )

            try:
                resp = _call_anthropic(api_key, model, prompt, user_msg)
            except (urllib.error.URLError, urllib.error.HTTPError, OSError) as exc:
                print(f"  ! anthropic call failed for {url}: {exc}", file=sys.stderr)
                event_results.append({"event": ev, "error": f"api error: {exc}"})
                total_events_failed += 1
                continue

            usage = resp.get("usage", {}) or {}
            call_cost = _usage_cost_usd(model, usage)
            cumulative_cost += call_cost
            per_article_cost += call_cost

            try:
                verdict = _verdict_from_response(resp)
            except (ValueError, json.JSONDecodeError) as exc:
                print(f"  ! verdict parse failed for {url}: {exc}", file=sys.stderr)
                event_results.append({"event": ev, "error": f"parse error: {exc}"})
                total_events_failed += 1
                continue

            event_results.append({"event": ev, "verdict": verdict, "error": ""})
            total_events_judged += 1

        title = f"Article freshness: {article_rel}"
        body = _build_issue_body(
            article_rel=article_rel,
            now_iso=now_iso,
            event_results=event_results,
            deferred_events=deferred,
            model=model,
            total_cost=per_article_cost,
            budget_usd=budget_usd,
        )
        _upsert_article_issue(repo, title, body)

    print(
        f"  done: events_judged={total_events_judged}, "
        f"events_failed={total_events_failed}, "
        f"events_deferred_cost_cap={total_events_skipped_cap}, "
        f"cumulative_cost=${cumulative_cost:.4f} / ${budget_usd:.2f}"
    )

    # Clear the fresh artifact so a later stage-2 re-run on the same checkout
    # is a no-op rather than re-billing the same events.
    FRESH_PATH.write_text(
        json.dumps({"generated_at": now_iso, "articles": []}, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
