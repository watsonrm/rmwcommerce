# DRY / Article-Structure Standard — Red-Team Rubric

You are reviewing ONE rmwcommerce article against Rick Watson's **new article-structure / DRY / agent-legibility standard**. This is a FOCUSED red-team — only the redundancy + structure + machine-legibility dimension, NOT a full correctness/URL review. Read-only: never edit the article.

## The standard (canonical)

1. **DRY — state each idea exactly once.**
   - ONE top-of-doc roll-up. Never a *stack* of overview sections (master-map + capability-inventory + aggregate-limits + TL;DR) that re-encode the same priority list. If >2 distinct summary sections precede the first deep section and restate the same list → defect.
   - No per-Part summary that is a subset of a per-Part table (e.g. a "TL;DR — five non-obvious bits" that repeats that Part's "Where to spend your time" table) → keep the table, cut the summary.
   - Per-surface capability/limits live INSIDE their Part, not also aggregated into the front matter.
   - Shared cross-Part mechanics: **canonicalize-and-point** — explain a shared setup once, then one-line pointer; don't re-derive.
   - The structural template describes JOBS each done once — NOT a checklist of sections to add to every Part.

2. **The basic human reader is the primary audience.** Clean simple prose for them. Machine-readability is secondary and NEVER justifies repeating content in prose.

3. **Agent legibility (the counterintuitive part):**
   - A reasoning LLM gets NO comprehension boost from JSON-LD over a clean labeled block in the body. JSON-LD's real job is **discovery + entity disambiguation by crawlers/knowledge graphs**, not comprehension. Flag any text that claims JSON-LD/structured data improves agent *comprehension* or *citation* as causation.
   - ONE visible machine-readable block in the content stream, pointed at by prose — not facts repeated in prose "for the agent."
   - Never hide machine data in HTML comments (`<!-- -->`) — markdown→text extractors strip them, so it's dropped by the very agents it targets → HIGH.
   - Never hand-maintain duplicate structured data (same facts in prose/front-matter AND JSON-LD blocks, hand-written) → MEDIUM "generate from one source."

## Detector passes — run all, cite line numbers

- **N1 Repeated-concept:** a whole concept fully explained (mechanism + rationale) in ≥2 places → HIGH. Fix = canonicalize-and-point. A one-line echo with a link is fine.
- **N2 Summary-is-subset:** a summary block (TL;DR / "the N things" / numbered roll-up) whose items are a near-subset of a table/section 10–30 lines away in the SAME part → HIGH, cut the summary keep the table. The ONE intended top-of-doc roll-up is exempt.
- **N3 Stacked-summaries-before-body:** count distinct overview/summary sections between title and first deep section. >2 re-encoding the same list → HIGH.
- **N4 Cross-Part duplication:** a mechanic explained in full in ≥2 Parts where canonicalize+pointer would do → MEDIUM. NOT a finding when the two surfaces genuinely differ.
- **A6 reversals (don't recommend re-adding what DRY removes):** a per-Part "TL;DR" restating that Part's table → HIGH cut; an aggregate front-matter capability/limits table duplicating per-Part ones → HIGH dissolve. Never flag the ABSENCE of a duplicate structure.
- **A7 machine surface:** machine data in HTML comments → HIGH; hand-maintained duplicate JSON-LD → MEDIUM; prose restating a fact solely for machine extraction → MEDIUM.
- **Dim-5 framing:** JSON-LD/structured-data over-claimed for comprehension/citation rather than discovery → HIGH (the load-bearing correction).

## Required output — return EXACTLY this structure, nothing else

```
ARTICLE: <filename>
LINES: <n>
SHAPE: <multi-part guide | single-flow article | reference/glossary | tutorial | short>
VERDICT: PASS | NEEDS WORK | FAIL
  (PASS = each idea once; NEEDS WORK = 1–2 nameable duplications; FAIL = the "same list many times" pattern / structural de-dup needed before any republish)
TOP FINDINGS (ranked, ≤5; [] if none):
  - [HIGH|MED|LOW] <one line, with line refs> → <fix: canonicalize-and-point / cut / dissolve>
CROSS-ARTICLE NOTE: <only if this article heavily overlaps another named article; else "none">
ONE-LINE SUMMARY: <≤120 chars for the consolidated report>
```

Be precise and conservative: cite line numbers, prefer canonicalize-and-point fixes, and never recommend adding a section that already exists elsewhere. A clean article should come back PASS — do not invent findings.
