# shallow-research

**Bounded one-context web research with a hard escalation guardrail.**

## Trigger phrases

- `/shallow-research: <question>`
- `shallow research: <question>`
- `quick research: <question>`

## When to use this skill

Use when you need a fast, grounded answer to a factual question or comparison and the stakes don't justify a full multi-agent deep-research pass. Good for: product feature or pricing comparisons, "current state of X" lookups, quick vendor due diligence, spotting what changed in a spec or policy.

Use the deep-research tier instead when: you're making a decision with significant financial or legal exposure, primary sources contradict each other, or the question requires synthesis across many sources.

## Hard caps — enforced, not aspirational

```
MAX_SEARCHES = 3        (fired as one parallel batch)
MAX_FETCHES  = 5        (primary sources only — full page reads, not snippets)
SUBAGENTS    = 0        (everything runs inline in this context)
WORKFLOWS    = 0        (no orchestration layer)
```

Before every WebSearch or WebFetch call, check the running counter. If adding the call would exceed the cap, fire the escalation guardrail instead. Do not proceed past the cap without explicit human authorization.

## Execution steps

**Step 1 — Parse the question.**
Identify what kind of answer is needed: a price or limit (needs a source read, not just a snippet), a yes/no capability (same), a comparison (table), or a current-state summary (synthesis). Note which claims will be load-bearing — those require an actual fetch, not just a search result snippet.

**Step 2 — Run searches (≤3, parallel batch).**
Fire all searches in one parallel batch. Do not fire them sequentially. Count each WebSearch call against MAX_SEARCHES.

**Step 3 — Select and fetch primary sources (≤5).**
From the search results, select up to 5 primary sources to read in full. Prefer: official documentation, vendor pricing pages, primary research, news articles with a dateline. Skip: aggregator pages, SEO-farm summaries, sources older than 18 months unless the question is historical.

Count each WebFetch call against MAX_FETCHES. Check the counter before each fetch.

**Step 3a — Escalation guardrail.**
Before any tool call that would exceed a cap:

1. Stop.
2. Explain what the question needs that the shallow tier can't provide (e.g., "This pricing comparison requires reading 7 vendor pages — the shallow tier only covers 5").
3. Offer the deep tier: "Do you want me to run a deeper pass on this?"
4. Halt. Do not proceed until the human responds.

This guard applies to subagents and workflow calls unconditionally — zero is the cap, no exceptions.

**Step 4 — Inline sanity check.**
For every load-bearing claim (a price, a hard yes/no, a version number, a capacity limit), confirm it traces to a source actually fetched and read in this pass, not just a search snippet. If a claim can't be confirmed this way, mark it "unverified."

**Step 5 — Write the answer.**
Structure:

1. **Answer / recommendation** — first 1–2 sentences. Lead with the conclusion.
2. **Comparison table** (if comparing 2+ options) — rows are options, columns are the decision-relevant dimensions.
3. **Key caveats** — anything that could change the answer (date sensitivity, regional variation, plan-tier dependency).
4. **Confidence note** — one line: "High confidence — primary sources read" / "Medium — some claims from snippets, not full reads" / "Low — primary sources unavailable or contradictory."
5. **Sources** — bulleted list of URLs actually fetched, with a one-line description of what each one confirmed.

## What "unverified" means here

"Unverified" means: the claim appeared in a search snippet or was mentioned in a source but you did not read the primary page that makes the assertion. Mark it explicitly:

> `[unverified — from search snippet only, not confirmed against primary source]`

Never assert an unverified claim as fact. Never omit the marker to make the output look cleaner.

## Verify before returning

- All MAX_SEARCHES and MAX_FETCHES counts are at or under cap.
- Every load-bearing claim either traces to a fetched source or is marked unverified.
- Sources list contains only URLs actually fetched, not search queries.
- If the escalation guardrail fired, the response ends with the escalation offer — no additional tool calls follow.

## See also

- [`guides/shallow-research.md`](../../guides/shallow-research.md) — the reasoning behind this two-tier model, when deep research is warranted, and the design decisions behind the caps.
