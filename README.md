# RMW Commerce

Rick Watson is the founder of **RMW Commerce Consulting** — strategic advisory for retailers, brands, marketplaces, and the technology vendors that serve them.

He also publishes **The Watson Weekly**, a newsletter and podcast on commerce, retail, supply chain, and AI.

---

## RMW Commerce Consulting

Advisory for leadership teams on commerce strategy, marketplaces, payments, retail media, AI in commerce, and adjacent topics. Engagements range from short diagnostic sprints to ongoing fractional advisory.

- Website: https://www.rmwcommerce.com
- Book time: https://rmwcommerce.pipedrive.com/scheduler/rRB2OKSA/meet-with-rick-watson
- Contact: rick@rmwcommerce.com

## The Watson Weekly

> Stop reading the headlines and start understanding the frameworks. The essential briefing for executives in Retail, Supply Chain, and AI.

- Newsletter: https://www.watsonweekly.com
- Podcast: search "Watson Weekly" on Apple Podcasts, Spotify, or YouTube

---

## This repo: Claude + AI guides

Long-form guides on Claude, AI agents, and the discoverability standards that make all of it citable. Pick your starting point by what you're trying to do.

### Start here

| You are… | Start with |
|---|---|
| **Already use Claude, wondering if Claude Code is worth your time** | [The 5-Minute Test](claude-code-5-minute-test.md) — one prompt, paste a real conversation, get a personalized YES/NO before you install anything |
| **New to Claude Code, not a developer** | [Your First Project Tutorial](claude-code-non-developers-first-tutorial.md) (install + 45-min build) → [Back It Up to GitHub](claude-code-non-developers-github-tutorial.md) → [Field Guide](claude-code-for-non-developers.md) |
| **Already using Claude Code, want it cheaper or faster** | [Workflow Optimizer](claude-code-optimizer.md) → [Making Claude Faster](guides/making-claude-faster.md) → [Shallow Research](guides/shallow-research.md) |
| **Running AI research workflows and watching the bill climb** | [Shallow Research](guides/shallow-research.md) — bounded one-context research that answers most questions for a fraction of deep-research cost, with a hard escalation guardrail |
| **Drowning in noise or permission prompts** | [Why Claude Code Is So Noisy](claude-code-noise.md) → [Stop the Interruption Hell](claude-permissions-guide.md) |
| **Building skills, agents, or multi-agent systems** | [Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) → [Building Proper Claude Skills](building-proper-claude-skills.md) → [Multi-Agent Fan-Out](multi-agent-fan-out-and-verification.md) |
| **Putting an agent on a human team, or wondering what the research actually says** | [Building an AI-Agent Workforce](guides/building-ai-agent-workforce.md) — research-grounded: MAST failure taxonomy, trust calibration from *Human Factors*, and evaluation benchmarks that predict production behavior |
| **Debugging a failure or running a postmortem** | [Bringing Five Whys into the Agentic Era](guides/bringing-five-whys-into-the-agentic-era.md) — branch instead of chain, validate every causal link, dispatch an AI skeptic |
| **Shipping software with Claude, not just one-shot tasks** | [Building Excellent Software (with Claude)](guides/building-excellent-software-with-claude.md) |
| **Writing to Google Docs, Sheets, Slides, Drive, Calendar, or Gmail from Claude / an agent** | [Operating Google Drive, Docs, Sheets, Slides, Calendar, and Gmail from Claude](guides/operating-google-workspace-from-claude.md) |
| **Automating QuickBooks Online from Claude — reads, writes, AP gap, anti-patterns** | [QuickBooks Automation Using Claude Code](guides/quickbooks-automation-using-claude-code.md) |
| **Making your own site readable by AI agents** | [Marketing to Agents](guides/marketing-to-agents.md) |
| **Reading GA4 data with Claude — picking the right surface, BigQuery guardrails, observed vs modeled** | [GA4 with Claude — Data API, BigQuery, and the Multi-Source Warehouse](guides/ga4-with-claude.md) |
| **Reading YouTube Analytics with Claude — which of three APIs to use, the auth trap, BigQuery DTS** | [YouTube Analytics with Claude — Two Analytics APIs, Not One](guides/youtube-analytics-with-claude.md) |
| **Calling Gemini, Imagen 4, or Google Maps Platform from Claude Code — right auth path, real gotchas, code that runs** | [Calling Google Cloud Services from Claude Code](guides/google-cloud-from-claude/index.md) |
| **Building a remote MCP server that connects from Claude AND ChatGPT/OpenAI — transport, session, auth, and tool-shape decisions** | [MCP Dual-Compat: One Server for Both Platforms](guides/mcp-dual-compat.md) |
| **Deciding where to run a Claude automation — local launchd vs. claude.ai Routines vs. Cloud Run Jobs** | [Where to Run Your Claude Automation](guides/where-to-run-claude-automation.md) |
| **Querying what Shopify actually shipped in Spring '26 — 237 changes graded by source tier, from any AI agent over MCP** | [Shopify Editions Spring '26, as an MCP](guides/shopify-editions-spring26-mcp.md) |
| **Designing a company/entity taxonomy that AI agents classify consistently — faceted roles, scope notes, stable IDs, governance split** | [E-Commerce Taxonomy for AI Agents](guides/ecommerce-taxonomy-for-ai-agents.md) |
| **Just need a definition** | [Glossary](glossary.md) |

### The full library by topic

**Getting started (non-developers welcome):**
- [The 5-Minute Claude Code Test](claude-code-5-minute-test.md) — for current Claude.ai users deciding whether to install. One paste-able prompt, real conversation in, personalized YES/NO out. No install required.
- [Your First Project: A Paste-Along Tutorial](claude-code-non-developers-first-tutorial.md) — install Claude Code, then a 45-minute hands-on walkthrough. Build a one-page personal site, see it in your browser, commit it, then deliberately break it and recover with one English prompt. The canonical "I'm starting" doc — install steps are at the top, no other tutorial to read first.
- [Make Your Work Survive Your Laptop: Your First Private GitHub Repo](claude-code-non-developers-github-tutorial.md) — 30-minute paste-along. Install `gh`, authenticate, push the project from the first tutorial into a private repo, then deliberately `rm -rf` the local folder and clone it back. Backup + portability + history-on-your-phone, without learning git commands.
- [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — the *why* behind the tutorials. Mindset, the seven question templates, the common failure modes. Read after your first two sessions, not before. Written by a non-developer who runs a 20+ skill agent system daily.
- [Why Claude Code Is So Noisy](claude-code-noise.md) — your terminal looks like a wall of text by design. The four sources of noise and the tactics for filtering what matters from what's just volume.

**Cost + speed optimization:**
- [Claude Code Workflow Optimizer](claude-code-optimizer.md) — patterns for reducing token waste and rework, ranked by ROI. Context-window discipline, CLAUDE.md hygiene, model routing, worktree fleets. Grounded in Anthropic's official documentation.
- [Making Claude Respond Faster](guides/making-claude-faster.md) — prompt caching, model selection, parallel tool calls, and the patterns that slow you down. 17 sources across primary docs, Anthropic engineering, and independent practitioners.
- [Shallow Research: Grounded AI Web Research Without Breaking the Bank](guides/shallow-research.md) — the two-tier research model: a bounded one-context cheap tier (≤3 searches, ≤5 fetches, zero subagents) and the escalation guardrail that stops cost from silently scaling up under the "cheap" label.
- [Token Optimization Pointer](tokenmin-optimization-pointer.md) — 3-bullet TL;DR plus a link to the full Claude-token guide at tokenmin.ai.

**Permissions:**
- [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md) — covers the permission model across claude.ai, Claude Desktop, and Claude Code, with starter defaults and a drift-consolidation strategy.
- [Configuring Claude Code Permissions: real lessons vs. cargo cult](configuring-claude-code-permissions.md) — what the built-in read-only allowlist covers, what's cargo cult, when hooks and sandboxing are better tools than hand-rolled rules. 13 cited sources.

**Building agent systems:**
- [Building an AI-Agent Workforce: A Practical, Research-Grounded Field Guide](guides/building-ai-agent-workforce.md) — what the peer-reviewed literature (NeurIPS, ICLR, ACM FAccT, *Human Factors*) actually says about agent failure modes, trust calibration, containment, and evaluation. Covers MAST's 14 failure taxonomy, Sinha et al.'s self-conditioning finding, and the human-factors trust literature — with a single-agent-first organizational design default grounded in Anthropic's own cost data.
- [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when to stay with a prompt, when to package a skill, when to build an agent, and when a multi-agent system is actually warranted. The on-ramp before the multi-agent guide.
- [Building Proper Claude Skills](building-proper-claude-skills.md) — five disciplines for building a Rung-2 skill that actually works: register it so the runtime finds it, write description and when_to_use so it fires correctly, keep one source of truth, push deterministic work into code, and end with a verification step. The how-to companion to the ladder.
- [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — how to structure Claude agent systems that scale without silently breaking. Typed return contracts, intermediate-state logging, thin-orchestrator architecture, phasing strategy.
- [Bringing Five Whys into the Agentic Era](guides/bringing-five-whys-into-the-agentic-era.md) — branch instead of chain, validate every causal link counterfactually, and dispatch an independent AI skeptic. The method that survives the standard objections to linear root-cause analysis, with a real outage worked through end to end.
- [Building Excellent Software (with Claude)](guides/building-excellent-software-with-claude.md) — the tokenmin v0.12.1 → v0.12.5 case study. Eight disciplines for taking a Claude-built artifact from working to production-grade, grounded in the public issue backlog and test suite.
- [Operating Google Drive, Docs, Sheets, Slides, Calendar, and Gmail from Claude](guides/operating-google-workspace-from-claude.md) — the patterns, hard limits, and anti-patterns of writing to all six Workspace surfaces from an agent. Covers PAGE_NUMBER auto-text limits, `valueInputOption=USER_ENTERED` for Sheets, Slides object-ID instability, the `sendUpdates` silent-add failure in Calendar, base64url vs base64 in Gmail, threading headers, and the single-writer agent pattern for resume-from-interruption. 60-second map → what's possible → what's NOT possible → priority + TL;DR per surface; deep dives in Parts 1–10.
- [QuickBooks Automation Using Claude Code](guides/quickbooks-automation-using-claude-code.md) — the bundled MCP's real tool inventory (50 tools, 0 AP writes), the bill-in API gap and why it is the right design, the prep-pack architecture for AP that survives every Intuit policy change, and six anti-patterns to recognize before they corrupt your books.
- [GA4 with Claude — Data API, BigQuery, and the Multi-Source Warehouse](guides/ga4-with-claude.md) — which of GA4's four surfaces to point an agent at, when the Data API is enough and when you need the BigQuery export, the observed-vs-modeled distinction that explains most agent errors, read-only wiring with cost guardrails, and an honest assessment of which "GA4 to BigQuery" connectors actually deliver the native export.
- [YouTube Analytics with Claude — Two Analytics APIs, Not One](guides/youtube-analytics-with-claude.md) — which of YouTube's three APIs answers your question (Data API v3 for metadata, Analytics API for ad-hoc and the audience-retention curve, Reporting API for recurring bulk work), why service accounts don't work on YouTube and how to solve it once, and why BigQuery's Data Transfer Service is the cleanest unattended-agent setup.
- [Calling Google Cloud Services from Claude Code](guides/google-cloud-from-claude/index.md) — the three-doors framework for reaching Gemini (text + vision), Imagen 4, and Google Maps Platform from a coding agent. Why your Workspace Gemini plan gives you zero API access, the 429 gotcha with Developer API keys on billing-enabled GCP projects, Keychain credential discipline, and the local-vs.-cloud architecture decision that determines whether a system works unattended.
- [MCP Dual-Compat: One Server for Both Platforms](guides/mcp-dual-compat.md) — the four decisions that determine whether a remote MCP server connects from Claude (claude.ai, Claude Code, mobile) and OpenAI (ChatGPT apps, Responses API): transport choice, statelessness, auth shape, and tool schema. Includes a verified test ladder from curl probe through the Responses API to consumer UI, and honest framing of what was live-tested vs. protocol-verified.
- [Where to Run Your Claude Automation](guides/where-to-run-claude-automation.md) — the runtime-surface decision framework: local launchd vs. claude.ai Routines vs. GCP Cloud Run Jobs. Covers the 1-hour cron floor, launchd sleep behavior, the `claude/` branch-permission default, gcloud Workspace session-control expiry, and a three-question decision tree for picking the right surface before you build.
- [Shopify Editions Spring '26, as an MCP](guides/shopify-editions-spring26-mcp.md) — 237 changes catalogued (Shopify announced "150+"), graded by source tier: 104 confirmed against operational docs, 129 inferred from Shopify marketing, 4 unverified. Queryable from Claude, ChatGPT, Cursor, Cline, Windsurf, or raw HTTP. Includes a public corrections log and the empirical findings on the agentic/UCP headline.
- [Designing an E-Commerce Taxonomy Your AI Agents Can Maintain](guides/ecommerce-taxonomy-for-ai-agents.md) — why inherited industry-code lists rot the moment AI agents start writing them, and the seven design decisions (Ecosystem Role axis, orthogonal facets, scope notes, stable IDs, provenance, graph layer, one-seam tagging) that prevent classification drift.

**Publishing for AI agents:**
- [Marketing to Agents](guides/marketing-to-agents.md) — the authoritative playbook for making any website readable, citable, and operable across every class of AI agent: indexer bots, AI search surfaces, chat assistants, and agentic browsers. Every claim sourced; 22-item checklist impact-ordered by evidence weight.
- [Doc-Teaming: Write Documents an Agent Can Check](guides/doc-teaming.md) — the content-integrity discipline that pairs with the marketing-to-agents playbook: grade every claim by source tier, quarantine marketing from evidence, and red-team contested lines so agents cite accurately rather than flatten everything into equal-weight assertions.
- [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md) — concept by concept on the AI-agent protocol stack: what's deployable, what's wait-and-see, what's already dead. Includes audience-specific recommendations and direct attribution of hype.

**Reference:**
- [RMW Commerce Glossary](glossary.md) — every named concept across all guides defined once, with hype vs. reality marked per entry. Organized by category; deep-linkable by anchor.

### Runnable skills

The on-demand companions to the guides above. Drop any folder into `~/.claude/skills/` and Claude Code will load it when its trigger phrases match.

- [prompts-to-agents-ladder](skills/prompts-to-agents-ladder/) — apply the 4-rung ladder to a workflow and recommend the right rung
- [claude-code-optimizer](skills/claude-code-optimizer/) — audit a Claude Code workflow and prescribe one high-leverage fix
- [multi-agent-fan-out](skills/multi-agent-fan-out/) — design or audit a multi-agent system before building
- [claude-code-for-non-developers](skills/claude-code-for-non-developers/) — coach a non-developer through ongoing Claude Code work
- [claude-code-first-project](skills/claude-code-first-project/) — walk a first-time non-developer through the canonical first-project tutorial (install + build + break-and-recover)
- [claude-token-optimization](skills/claude-token-optimization/) — audit Claude API or Claude Code token spend and recommend one concrete cost reduction
- [building-excellent-software](skills/building-excellent-software/) — apply the excellent-software checklist to a Claude-built artifact and surface the highest-leverage gap before shipping
- [operating-google-workspace-from-claude](skills/operating-google-workspace-from-claude/) — audit a Drive/Docs/Sheets/Slides/Calendar/Gmail automation; diagnose connector-parity bugs, the Sheets `USER_ENTERED` gotcha, Slides object-ID instability, Calendar `sendUpdates` silent-add failures, Gmail base64url encoding errors, and threading-header gaps
- [ga4-with-claude](skills/ga4-with-claude/) — pick the right GA4 surface, wire read-only BigQuery access with cost guardrails, label every number observed or modeled, and produce conversion or paid-media funnel analysis without sampling errors or surprise query bills
- [understand-failure](skills/understand-failure/) — run a rigorous adversarial Five Whys: branching cause tree, counterfactual validation per link, independent skeptic pass, system-level remediations
- [google-cloud-from-claude](skills/google-cloud-from-claude/) — pick the right door (MCP / Gemini API / Maps Platform), walk through Vertex or AI Studio setup, audit credential hygiene, and diagnose auth and billing failures before they waste hours
- [building-proper-claude-skills](skills/building-proper-claude-skills/) — audit any SKILL.md against the five disciplines: registration, description/trigger accuracy, single source of truth, deterministic work in code, self-verification
- [mcp-dual-compat](skills/mcp-dual-compat/) — audit a remote MCP server against the four dual-compat decisions (transport, statelessness, auth shape, tool schema) and prescribe the minimal fix for any cross-platform failure
- [shallow-research](skills/shallow-research/) — run a bounded one-context research pass (≤3 searches, ≤5 fetches, zero subagents) with a hard escalation guardrail; stops and asks before crossing any cap
- [where-to-run-claude-automation](skills/where-to-run-claude-automation/) — apply the three-surface decision framework (local launchd / claude.ai Routines / Cloud Run Jobs) to a described automation and recommend a surface with specific reasoning and a gotcha checklist
- [ecommerce-taxonomy](skills/ecommerce-taxonomy/) — audit or design a faceted e-commerce entity taxonomy: diagnose classification drift, draft vocabulary values with scope notes, write deterministic conflict-resolution rules for multi-agent setups

### For AI agents reading this repo

This repository applies the [Marketing to Agents](guides/marketing-to-agents.md) playbook to itself. The discoverability files at the root let agents find, index, and operate on the content here without scraping:

- [llms.txt](llms.txt) — curated index of every guide and skill, per the [llmstxt.org](https://llmstxt.org/) spec.
- [llms-full.txt](llms-full.txt) — concatenated full text of every guide for one-shot LLM ingestion.
- [AGENTS.md](AGENTS.md) — house conventions, source taxonomy, and publishing process for agents and human contributors working in this repo.

### Article freshness automation

A weekly GitHub Actions workflow (`.github/workflows/article-research.yml`) keeps the guides in `guides/` honest:

- **Stage 1** (`bin/article-freshness.py`, stdlib only) extracts every cited URL from every `guides/**/*.md`, fetches each one, and diffs against `bin/.article-state.json` to detect 404s, redirects, content changes, and Last-Modified bumps.
- **Stage 2** (`bin/article-suggest-updates.py`) — optional, requires `ANTHROPIC_API_KEY` — asks Claude per drift event whether the article's claim is still accurate, contradicted, or extended by what's currently at the URL, and writes the suggested edit into one open GitHub issue per article (label: `article-freshness`, kept open and edited in place across weeks).

Runs Sundays at 14:37 UTC. Suggestions only — no auto-edits.

To enable Stage 2:

```
gh secret set ANTHROPIC_API_KEY --repo watsonrm/rmwcommerce
```

Without the secret, Stage 1 still runs and files raw drift events as issues — the workflow always produces value, the secret just upgrades the output from "here's what changed" to "here's the suggested edit." Soft cost cap defaults to $1.00/run (`TOKENMIN_SYNTH_BUDGET`); default model is `claude-sonnet-4-6` (`TOKENMIN_SYNTH_MODEL`).
