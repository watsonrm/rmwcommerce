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
| **Already using Claude Code, want it cheaper or faster** | [Workflow Optimizer](claude-code-optimizer.md) → [Making Claude Faster](guides/making-claude-faster.md) |
| **Drowning in noise or permission prompts** | [Why Claude Code Is So Noisy](claude-code-noise.md) → [Stop the Interruption Hell](claude-permissions-guide.md) |
| **Building skills, agents, or multi-agent systems** | [Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) → [Multi-Agent Fan-Out](multi-agent-fan-out-and-verification.md) |
| **Shipping software with Claude, not just one-shot tasks** | [Building Excellent Software (with Claude)](guides/building-excellent-software-with-claude.md) |
| **Writing to Google Docs, Sheets, Slides, Drive, Calendar, or Gmail from Claude / an agent** | [Operating Google Drive, Docs, Sheets, Slides, Calendar, and Gmail from Claude](guides/operating-google-workspace-from-claude.md) |
| **Automating QuickBooks Online from Claude — reads, writes, AP gap, anti-patterns** | [QuickBooks Automation Using Claude Code](guides/quickbooks-automation-using-claude-code.md) |
| **Making your own site readable by AI agents** | [Marketing to Agents](guides/marketing-to-agents.md) |
| **Reading GA4 data with Claude — picking the right surface, BigQuery guardrails, observed vs modeled** | [GA4 with Claude — Data API, BigQuery, and the Multi-Source Warehouse](guides/ga4-with-claude.md) |
| **Reading YouTube Analytics with Claude — which of three APIs to use, the auth trap, BigQuery DTS** | [YouTube Analytics with Claude — Two Analytics APIs, Not One](guides/youtube-analytics-with-claude.md) |
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
- [Token Optimization Pointer](tokenmin-optimization-pointer.md) — 3-bullet TL;DR plus a link to the full Claude-token guide at tokenmin.ai.

**Permissions:**
- [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md) — covers the permission model across claude.ai, Claude Desktop, and Claude Code, with starter defaults and a drift-consolidation strategy.
- [Configuring Claude Code Permissions: real lessons vs. cargo cult](configuring-claude-code-permissions.md) — what the built-in read-only allowlist covers, what's cargo cult, when hooks and sandboxing are better tools than hand-rolled rules. 13 cited sources.

**Building agent systems:**
- [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when to stay with a prompt, when to package a skill, when to build an agent, and when a multi-agent system is actually warranted. The on-ramp before the multi-agent guide.
- [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — how to structure Claude agent systems that scale without silently breaking. Typed return contracts, intermediate-state logging, thin-orchestrator architecture, phasing strategy.
- [Building Excellent Software (with Claude)](guides/building-excellent-software-with-claude.md) — the tokenmin v0.12.1 → v0.12.5 case study. Eight disciplines for taking a Claude-built artifact from working to production-grade, grounded in the public issue backlog and test suite.
- [Operating Google Drive, Docs, Sheets, Slides, Calendar, and Gmail from Claude](guides/operating-google-workspace-from-claude.md) — the patterns, hard limits, and anti-patterns of writing to all six Workspace surfaces from an agent. Covers PAGE_NUMBER auto-text limits, `valueInputOption=USER_ENTERED` for Sheets, Slides object-ID instability, the `sendUpdates` silent-add failure in Calendar, base64url vs base64 in Gmail, threading headers, and the single-writer agent pattern for resume-from-interruption. 60-second map → what's possible → what's NOT possible → priority + TL;DR per surface; deep dives in Parts 1–10.
- [QuickBooks Automation Using Claude Code](guides/quickbooks-automation-using-claude-code.md) — the bundled MCP's real tool inventory (50 tools, 0 AP writes), the bill-in API gap and why it is the right design, the prep-pack architecture for AP that survives every Intuit policy change, and six anti-patterns to recognize before they corrupt your books.
- [GA4 with Claude — Data API, BigQuery, and the Multi-Source Warehouse](guides/ga4-with-claude.md) — which of GA4's four surfaces to point an agent at, when the Data API is enough and when you need the BigQuery export, the observed-vs-modeled distinction that explains most agent errors, read-only wiring with cost guardrails, and an honest assessment of which "GA4 to BigQuery" connectors actually deliver the native export.
- [YouTube Analytics with Claude — Two Analytics APIs, Not One](guides/youtube-analytics-with-claude.md) — which of YouTube's three APIs answers your question (Data API v3 for metadata, Analytics API for ad-hoc and the audience-retention curve, Reporting API for recurring bulk work), why service accounts don't work on YouTube and how to solve it once, and why BigQuery's Data Transfer Service is the cleanest unattended-agent setup.

**Publishing for AI agents:**
- [Marketing to Agents](guides/marketing-to-agents.md) — the authoritative playbook for making any website readable, citable, and operable across every class of AI agent: indexer bots, AI search surfaces, chat assistants, and agentic browsers. Every claim sourced; 22-item checklist impact-ordered by evidence weight.
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
