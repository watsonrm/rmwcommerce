---
name: canonical-cloud-fetcher
description: >
  Apply the canonical cloud fetcher pattern to a described external source.
  Diagnoses dedup key choices, checks the seven-part anatomy, flags invariant
  violations, and produces a filled-in scaffold checklist for the specific source.
when_to_use: >
  Load this skill when the user describes a new data source they want to ingest
  into a content or knowledge pipeline, asks how to replicate an existing fetcher
  for a new source, wants to audit an existing fetcher against the canonical
  pattern, or asks about dedup strategies, watermark management, or envelope design.
  Trigger phrases: "apply the canonical cloud fetcher pattern",
  "scaffold a cloud fetcher for", "audit my fetcher against the canonical pattern",
  "how do I add a new source to my pipeline", "help me ingest [source] into my pipeline",
  "what's the right dedup key for", "why is my fetcher dropping content".
---

# Skill: canonical-cloud-fetcher

## Purpose

Apply the seven-part canonical cloud fetcher pattern to a user-described source. The pattern turns any external source (Slack workspace, email mailbox, file drive, API feed, RSS/Atom feed, webhook stream) into a first-class pipeline input by writing a small cloud poller that emits canonical envelopes — while the router, search index, tagging pipeline, and all downstream consumers remain unchanged.

The pattern's main promise: a new source costs ~350–450 lines of source-specific code, not a new system.

## Procedure

### Step 0: gather source description

Ask the user for (or extract from what they've shared):
- What source? (Slack, email, file drive, API, RSS feed, webhook, etc.)
- What's the natural unit of content? (message thread, email, file, post, event, …)
- What cadence is needed? (real-time, hourly, daily, …)
- What downstream consumers will use the envelopes? (search index, tagging, digest, all of the above)
- Does an existing auth/client module already exist for this workspace?

If the user says "scaffold" or "apply the pattern," gather what's missing before proceeding.

### Step 1: recommend the dedup key

This is the most consequential decision. Present the tradeoff clearly:

**Key too coarse:** A per-day key on a high-frequency source drops content after the first run of the day. New items arrive; the watermark already covers their day; they're skipped.

**Key too fine:** A per-message key on a threaded conversation source emits hundreds of envelopes per thread. Low signal density, high volume.

Recommend based on source type:
- **Threaded / low-volume (discussions, email threads):** per-conversation-day key. Re-emit if new replies arrive.
- **High-frequency feed (posts, links, events):** per-item ID using watermark as primary bound; seen-ID index as secondary safety net.
- **File drive:** use the drive's change/delta token, not modification timestamps (timestamps are not globally consistent).
- **Webhook stream:** per-event ID; seen-ID index for dedup on replay.

State the recommended key explicitly and explain why.

### Step 2: check the seven-part anatomy

Walk through each part against what the user has described. For each, either confirm or flag a gap:

1. **Source poll** — Does the source offer a cursor-based API? Is there an existing auth module to reuse?
2. **Dedup state** — Will this run locally or in the cloud? Cloud → needs optimistic-concurrency state (GCS/S3 generation precondition). Cold-start handled with `--allow-cold-start`?
3. **Canonical envelope** — Is `source` string unique and stable? Is `envelope.json` written last?
4. **Object-store sink** — Staging prefix + finalize into `incoming/`? Or local-mode direct write?
5. **Delivery bridge** — Does one already exist? A new fetcher adds nothing here.
6. **Router** — Does the routing rule exist? Is it placed before any broader catch-all?
7. **Liveness registry** — Are all four entries present? (cadence, perf-warn, known list, display-order list — both of the last two, not just one)

### Step 3: check the three production failure modes

For each, ask if the described implementation is at risk:

**Failure mode 1 — wrong dedup key:** Covered in Step 1. If the key looks wrong, flag it again here and state the consequence.

**Failure mode 2 — rate-limit truncation without watermark hold:** Does the fetcher hold the watermark if any sub-source errors? If not, a 429 will silently create a permanent gap. Flag this as HIGH priority if the source has rate limits (most do).

**Failure mode 3 — missing run.invoker binding (GCP-specific):** If the fetcher will run on Cloud Run triggered by Cloud Scheduler, is the `run.invoker` binding in the deploy script? A missing binding causes a silent 403 — the scheduler fires successfully but the container never starts.

### Step 4: produce the filled-in scaffold checklist

Output a copy of the scaffold checklist (Steps 1–6 from the guide) with each item marked:
- [x] Already done / present
- [ ] Not yet done — describe what's needed
- [SKIP] Not applicable to this source — explain why

Include concrete values where you know them (the `source` string, the dedup key, the routing rule shape, the cadence).

### Step 5: flag invariant violations

Check all five invariants:
1. Envelope.json written last?
2. Router and consumers stay local — fetcher does not write directly to knowledge base?
3. One writer per state file?
4. Heartbeat on every run including no-ops, but NOT on skipped (locked) runs?
5. Cadence in Cloud Scheduler and in health registry match?

For each violation found, state: what's wrong, what the consequence is if left unFixed, and the minimal fix.

## Output format

Present findings in this order:
1. **Recommended dedup key** — one sentence, stated plainly.
2. **Anatomy gaps** — a table: Part | Status | Gap/fix needed.
3. **Failure mode risks** — one line each, flagging which are HIGH risk for this source.
4. **Filled-in scaffold checklist** — the six-step checklist with each item marked.
5. **Invariant violations** — only those that apply; omit clean ones.

Keep it concrete. If the user has shared enough information to make definite recommendations, make them. Don't list options when the pattern gives a clear answer.

---

## Reference

Full anatomy, gotchas, and production failure modes: [The Canonical Cloud Fetcher Pattern](https://github.com/watsonrm/rmwcommerce/blob/main/guides/canonical-cloud-fetcher.md)
