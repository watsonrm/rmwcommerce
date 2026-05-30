---
name: marketing-to-agents
description: >
  Audit a website for AI-agent friendliness and AI-search citation readiness.
  Works through the 22-item checklist from Rick Watson's Marketing to Agents
  guide, asks targeted questions about the site's current setup, and produces a
  tier-by-tier gap report (Tier 1 / the 80-20 first), prioritized fixes with
  effort estimates, and a robots.txt template customized to the chosen training
  opt-out stance. Trigger when the user says "audit my site for agent-
  friendliness", "run the marketing-to-agents checklist on my site", "how well
  does my site work for AI agents", "agent-readiness audit", or "am I getting
  cited by AI search".
---

# marketing-to-agents skill

**Trigger phrases (say any of these to Claude):**
- "audit my site for agent-friendliness"
- "run the marketing-to-agents checklist on my site"
- "how well does my site work for AI agents"
- "agent-readiness audit"
- "am I getting cited by AI search"

---

## What this skill does

When triggered, Claude will work through the 22-item agent-friendliness checklist from Rick Watson's *Marketing to Agents* guide (github.com/watsonrm/rmwcommerce), ask you targeted questions about your site's current setup, and produce:

1. A tier-by-tier gap report (Tier 1 gaps first — these are the 80/20)
2. Specific, prioritized fixes with effort estimates
3. A `robots.txt` template customized to your training opt-out stance
4. JSON-LD schema snippets for your site type
5. A check-your-work section: tests you can run to verify each fix landed

---

## Session protocol

### Step 1 — Gather site basics

Ask the user for:
- Site URL (or describe it if not public)
- Tech stack (WordPress, Shopify, custom Next.js, etc.)
- Primary audience (consumers, developers, B2B buyers)
- Whether they publish editorial content, developer docs, or both

If the user can share a `curl -A "GPTBot" <url>` output, ask for it — it immediately reveals whether headlines and body are server-rendered.

### Step 2 — Tier 1 gap check (do all five before moving on)

Work through each Tier 1 item as a question:

**T1-1. Server-rendered HTML**
- "Does your headline and body text appear in the raw HTML source before JavaScript runs?"
- Quick test: `curl -A "GPTBot" <url> | grep -c "<h1"` — if zero, content is JS-only.

**T1-2. JSON-LD structured data**
- "Do your editorial pages carry Article / Organization / Person JSON-LD with datePublished, dateModified, author, publisher, and sameAs fields?"
- Tool: Google's Rich Results Test at search.google.com/test/rich-results

**T1-3. robots.txt — three-class separation**
- "Does your robots.txt separate training crawlers from search-index crawlers from user-triggered fetchers?"
- Fetch it live: `curl https://<domain>/robots.txt`
- The most common error: a blanket `Disallow: /` that blocks ChatGPT-User and Claude-User (your customers' agents).

**T1-4. Answer-first content placement**
- "Does the first 30% of each long-form page contain a 40–75 word paragraph that directly answers the page's core question?"
- 44% of ChatGPT citations come from the first third of a page.

**T1-5. Third-party citations and entity graph**
- "Is your brand or organization cited by authoritative third-party domains — trade press, .edu, .gov, major publications?"
- "Does a Wikipedia or Wikidata entry exist for your organization?"
- This is the highest-effort, highest-durability signal. Flag it clearly and set realistic expectations.

### Step 3 — Tier 2 and 3 gaps (abbreviated)

For each item the user hasn't confirmed, note the gap and effort. Do not deep-dive into Tier 2/3 until all Tier 1 gaps are addressed or explicitly deprioritized by the user.

Tier 2 items: front-load answer, Open Graph tags, ISO 8601 timestamps, author bylines with schema, cache headers, compression + HTTP/2, WCAG 2.2 AA.

Tier 3 items: BreadcrumbList / FAQPage / HowTo schema, `.md` mirrors, `/llms.txt` (docs sites only), `AGENTS.md` (dev repos only), OpenAPI spec, MCP server.

### Step 4 — Deliver gap report

Format:

```
## Agent-Friendliness Audit — <site domain>

### Tier 1 — Do these first (80/20)
- [ ] T1-1 Server-rendered HTML: <PASS / GAP — one sentence on what's missing>
- [ ] T1-2 JSON-LD structured data: <PASS / GAP>
- [ ] T1-3 robots.txt three-class separation: <PASS / GAP>
- [ ] T1-4 Answer-first placement: <PASS / GAP>
- [ ] T1-5 Third-party citation / entity graph: <PASS / GAP>

### Tier 2 — High leverage
[abbreviated list of gaps only — skip items that already pass]

### Tier 3 — If you have docs or structured content
[abbreviated list of gaps only]

### Tier 4 — Polish and measurement
[abbreviated list of gaps only]

## Recommended fix order
1. <highest-impact gap> — effort: Low/Medium/High
2. ...

## robots.txt template for <domain>
[customized template based on user's training opt-out stance]

## Check your work
[per-fix test commands or tools]
```

### Step 5 — Check your work (mandatory per skill verification rule)

After delivering the report, give the user at least three concrete verification steps:

1. `curl -A "GPTBot" https://<domain>/<key-page> | grep -i "<h1\|datePublished\|@type"` — confirms server-rendered HTML + JSON-LD visible to bots
2. Google Rich Results Test (search.google.com/test/rich-results) — validates JSON-LD schema
3. `curl https://<domain>/robots.txt` — visual confirm of three-class separation
4. For Bing citation tracking: Bing Webmaster Tools → AI Performance tab (only surface with per-query citation data as of May 2026)
5. For ChatGPT referrals: filter `utm_source=chatgpt.com` in analytics

---

## Source guide

Full reasoning, data sources, and the "What we still don't know" section:
[`guides/marketing-to-agents.md`](../../guides/marketing-to-agents.md) in this repo.

Every numerical claim in this skill is sourced in that guide. If a user challenges a number, point them there.
