# Shopify Editions Spring '26, as an MCP

**An open, queryable MCP server that lets any AI agent ask what Shopify actually shipped — with per-claim source grades and a public corrections log.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. The underlying data, source grading, and corrections log are independent analysis, not affiliated with or endorsed by Shopify. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- **237 distinct changes catalogued** (Shopify announced "150+"), each with a source-confidence grade. You know which claims are backed by operational docs and which are inferred from Shopify's own marketing.
- **Queryable from any MCP-capable agent** — Claude Code, Claude Desktop, Cursor, Cline, Windsurf, ChatGPT, and more — in one `mcp add` or one hosted URL.
- **A public corrections log** ships with it. Errors that were caught during the build — including one significant deletion and several "coming soon" items mislabeled as live — are documented, not hidden.
- **The opinion layer (`rick_lens`) is forthcoming.** What's here now is the sourced factual record. Verdicts come separately.

### Where to spend your time, in priority order

| # | What | Why it matters | Effort |
|---|---|---|---|
| 1 | [Connect the MCP and run `unreleased`](#how-to-connect-it) | See the 12 announced-but-not-live items before you plan around them | 2 minutes |
| 2 | [Run `query {domain:"agentic"}`](#what-you-can-ask-it) | The agentic/UCP headline is the most hyped area and also the one with the most nuance | 30 seconds |
| 3 | [Run `customers`](#what-you-can-ask-it) | The merchant showcase tells you what Shopify is confident enough to demo publicly — and what's conspicuously absent | 30 seconds |
| 4 | [Read `methodology`](#what-you-can-ask-it) | Understand the source tiers before quoting any specific claim downstream | 5 minutes |

Most readers should run the first two and stop. The rest is for people who need to brief a team or build a plan off this data.

---

## What this is

Shopify's Spring '26 Edition dropped on June 17, 2026. The marketing says "150+ updates." The actual count, after a systematic diff-and-inventory pass, is 237 distinct changes.

That gap isn't misleading — Shopify bundles related items and counts in marketing-round-numbers. But if you're trying to advise a merchant or a vendor on what changed and why it matters, you need the unbundled list with source citations, not the marketing deck.

This is that list, packaged as an MCP server any AI agent can query.

The medium fits the subject. The Spring '26 Edition is the one where Shopify formally announced the Universal Commerce Protocol and positioned itself as the infrastructure layer for agentic commerce. An MCP server that lets AI agents interrogate that claim — against Shopify's own primary docs — seemed like the right format.

---

## How to connect it

**Hosted (no install — anything that speaks MCP over HTTP):**

```
https://editions.rmwcommerce.com
direct: https://shopify-editions-spring26-mcp-1649969634.us-central1.run.app
```

The branded URL is the canonical one. The direct Cloud Run URL is the live fallback if the CNAME isn't resolving for you.

**Claude Code:**

```bash
# hosted (recommended — no Node required)
claude mcp add --transport http shopify-editions https://editions.rmwcommerce.com

# local stdio (requires Node/npx)
claude mcp add shopify-editions -- npx -y shopify-editions-spring26-mcp
```

**Claude Desktop, Cursor, Cline, Windsurf, Zed, VS Code (1.99+):**

Add to your MCP config:

```json
{
  "mcpServers": {
    "shopify-editions": {
      "command": "npx",
      "args": ["-y", "shopify-editions-spring26-mcp"]
    }
  }
}
```

**ChatGPT (developer mode / connectors):** Settings → Connectors → add MCP server → paste `https://editions.rmwcommerce.com`. (ChatGPT doesn't run local stdio; hosted only.)

**Raw HTTP (no MCP client):**

```bash
# health check
curl -s https://editions.rmwcommerce.com

# list tools
curl -s https://editions.rmwcommerce.com \
  -X POST -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'

# call a tool
curl -s https://editions.rmwcommerce.com \
  -X POST -d '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"unreleased"}}'
```

Full per-surface install steps: [INSTALL.md](https://github.com/watsonrm/shopify-editions-spring26-mcp/blob/main/INSTALL.md).

---

## What you can ask it

Seven tools:

| Tool | What it returns |
|---|---|
| `query {topic:"b2b"}` | Everything matching a topic or domain (b2b, payments, agentic, pos, etc.) |
| `query {domain:"agentic"}` | All items tagged to a specific domain |
| `get {id:"ucp_protocol"}` | The full record for one feature, including trust block and history |
| `unreleased` | The 12 announced-but-not-live items, with status and caveats |
| `deprecations` | What's going away and when |
| `customers` | The merchants Shopify showcased as proof of the Edition |
| `methodology` | How the dataset was built, source trust tiers, and the full corrections log |
| `easter` | It's in there |

---

## How the dataset was built

The pipeline ran in stages: diff against the prior Edition → 6-domain inventory → hardening against help.shopify.com → validation against shopify.dev/docs → video-transcript mining from the Editions keynote and feature reels → adversarial fact-check → merchant-proof scan → red-team gate → full re-validation (every claim re-checked against primary sources, both directions). Re-runnable: `pipeline.workflow.js` in the repo ([github.com/watsonrm/shopify-editions-spring26-mcp](https://github.com/watsonrm/shopify-editions-spring26-mcp)).

### Source trust tiers

Every claim is graded by the best source backing it:

| Tier | Sources | What it means |
|---|---|---|
| 1 — Operational | help.shopify.com, shopify.dev/docs, changelog.shopify.com, shopify.engineering | Feature is live/GA. Operational docs don't exist for things that haven't shipped. |
| 2 — First-party marketing | shopify.com/editions, Shopify news briefs | Shopify claims it. True-as-described, but marketing ships before docs and before GA. |
| 3 — Video | Editions keynote, feature reels (cited by ID + timestamp) | Confirms the mechanic and supplies quotes. On-screen, not operational. |
| Per-entity primary | A third party's own newsroom (Salesforce, PayPal, Google, etc.) | Authoritative for that company's participation. Not Shopify's to confirm. |

**The result: 104 confirmed** (backed by Tier-1 operational sources), **129 inferred** (Shopify marketing, flagged), **4 unverified** (contradicted or no source found). That split is visible per-item in the dataset.

---

## What the data shows — empirical observations

These are observations from the dataset, not verdicts. The opinion layer is coming separately.

**On agentic commerce and UCP:**
- The Spring '26 keynote demo showed no real merchant transacting via an agent. The demo used mock products and a synthetic persona.
- There are no agent-GMV numbers anywhere in Shopify's public materials around this Edition.
- The Universal Commerce Protocol is co-developed with Google, with a 21-company coalition across three tiers. The coalition list was rebuilt from 21 per-entity primary sources (Amazon, Meta, Microsoft, Salesforce, and others each announced participation via their own newsrooms and the April 24 UCP Tech Council release — not Shopify's pages).

**On what's actually live:**
- 12 items were announced but are not yet live. The `unreleased` tool lists them.
- WhatsApp campaigns are "coming soon" — the consent layer is live, campaigns are not.
- POS pickup, transfers, and cash management enhancements are POS Pro, not Plus-exclusive as some coverage has it.

**On the source-confidence architecture:**
- Every item carries a `trust` block showing the confidence call, why it was made, and a `history` field if the confidence was upgraded or downgraded. No silent reclassification.

---

## The corrections that got caught

Rigor means logging what was wrong. From the public corrections log (accessible via the `methodology` tool):

**The UCP-endorser deletion.** An over-cautious red-team pass deleted Amazon, Meta, Microsoft, and Salesforce from the endorser list as "fabricated — not in Shopify's posts." They were real. Each announced participation via its own newsroom and the April 24 UCP Tech Council release. The root cause was a rule failure: "couldn't find it in source X" was escalated to "fabricated → delete," instead of stopping at "unverified — flag and widen the search." The coalition was rebuilt from 21 per-entity primary sources. The rule is now hard in the pipeline: *couldn't-find never deletes a claim.*

Other corrections: WhatsApp campaigns labeled live (fixed to coming soon), POS features attributed to Plus instead of Pro, "50 pinned metafields" annotated as announced-but-docs-still-say-20 (`unverified`), Managed Markets UK/Canada downgraded from GA to early access, Hydrogen/Oxygen framing corrected.

Full machine-readable log: `methodology()` → `corrections_log`.

---

## What this is not

A recommendation layer. The factual record of what shipped, what's coming, and what's still unconfirmed is here. Rick's read on what it means for merchants, brands, and vendors is a separate piece — the `rick_lens` fields in the dataset are the scaffolding for it.

It's also a June 17, 2026 snapshot. Items marked `coming_soon`, `preview`, or `early_access` will change. The pipeline is re-runnable when they do.

---

## License and corrections

Code and schema: MIT. All underlying information rights are due their respective holders. The `rick_lens` opinions are © Rick Watson / RMW Commerce, reuse with attribution.

Not affiliated with or endorsed by Shopify.

Corrections welcome: **info@rmwcommerce.com**. Every confirmed fix lands in the public corrections log and is visible via `methodology`.

---

## Sources & Attribution

- Shopify Editions Spring '26 landing page: [https://www.shopify.com/editions/spring2026](https://www.shopify.com/editions/spring2026)
- Shopify Help Center (help.shopify.com) — primary source for Tier-1 operational claims
- Shopify Developer Docs (shopify.dev/docs) — primary source for developer-facing Tier-1 claims
- Shopify Changelog (changelog.shopify.com) — primary source for dated release entries
- Shopify Engineering Blog (shopify.engineering) — primary source for architectural claims
- UCP Tech Council announcement (April 24, 2026) — primary source for coalition composition
- Per-entity newsrooms: Amazon, Meta, Microsoft, Salesforce, PayPal, Google, and 15 others — primary source for each company's UCP participation
- Shopify Editions Spring '26 keynote video — Tier-3 source; cited by timestamp where used
- MCP repo and dataset: [https://github.com/watsonrm/shopify-editions-spring26-mcp](https://github.com/watsonrm/shopify-editions-spring26-mcp)
- Full METHODOLOGY.md: [https://github.com/watsonrm/shopify-editions-spring26-mcp/blob/main/METHODOLOGY.md](https://github.com/watsonrm/shopify-editions-spring26-mcp/blob/main/METHODOLOGY.md)

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary.
