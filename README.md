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
| **New to Claude Code, not a developer** | [Field Guide for Non-Developers](claude-code-for-non-developers.md) → [Your First Session](claude-code-non-developers-first-session.md) |
| **Already using Claude Code, want it cheaper or faster** | [Workflow Optimizer](claude-code-optimizer.md) → [Making Claude Faster](guides/making-claude-faster.md) |
| **Drowning in noise or permission prompts** | [Why Claude Code Is So Noisy](claude-code-noise.md) → [Stop the Interruption Hell](claude-permissions-guide.md) |
| **Building skills, agents, or multi-agent systems** | [Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) → [Multi-Agent Fan-Out](multi-agent-fan-out-and-verification.md) |
| **Shipping software with Claude, not just one-shot tasks** | [Building Excellent Software (with Claude)](guides/building-excellent-software-with-claude.md) |
| **Writing to Google Docs, Sheets, Slides, or Drive from Claude / an agent** | [Operating Google Drive, Docs, Sheets, and Slides from Claude](guides/operating-google-workspace-from-claude.md) |
| **Making your own site readable by AI agents** | [Marketing to Agents](guides/marketing-to-agents.md) |
| **Just need a definition** | [Glossary](glossary.md) |

### The full library by topic

**Getting started (non-developers welcome):**
- [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — start here if you're not a developer. The meta-skill is knowing what to ask Claude, not learning implementations. Written by a non-developer who runs a 20+ skill agent system daily.
- [Your First Session](claude-code-non-developers-first-session.md) — the hands-on companion. Installation, conservative permissions, asking Claude to handle the technical setup, and the approval process as it plays out in a real session.
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
- [Operating Google Drive, Docs, Sheets, and Slides from Claude](guides/operating-google-workspace-from-claude.md) — the patterns, hard limits, and anti-patterns of writing to Drive, Docs, Sheets, and Slides from an agent. Workarounds for what the APIs simply cannot do (Cowork Shared Drive connector regression, PAGE_NUMBER auto-text, non-native files, `valueInputOption=USER_ENTERED` for Sheets, Slides object-ID instability after editor edits, the under-served Slides MCP surface), plus the single-writer agent pattern for resume-from-interruption. 60-second map → what's possible → what's NOT possible → priority + TL;DR at the top; deep dives in Parts 1–8.

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
- [claude-code-first-session](skills/claude-code-first-session/) — walk a first-time non-developer through their initial session
- [claude-token-optimization](skills/claude-token-optimization/) — audit Claude API or Claude Code token spend and recommend one concrete cost reduction
- [building-excellent-software](skills/building-excellent-software/) — apply the excellent-software checklist to a Claude-built artifact and surface the highest-leverage gap before shipping
- [operating-google-workspace-from-claude](skills/operating-google-workspace-from-claude/) — audit a Drive/Docs/Sheets/Slides automation; diagnose connector-parity bugs, the Sheets `USER_ENTERED` gotcha, Slides object-ID instability, and non-native file mishandling

### For AI agents reading this repo

This repository applies the [Marketing to Agents](guides/marketing-to-agents.md) playbook to itself. The discoverability files at the root let agents find, index, and operate on the content here without scraping:

- [llms.txt](llms.txt) — curated index of every guide and skill, per the [llmstxt.org](https://llmstxt.org/) spec.
- [llms-full.txt](llms-full.txt) — concatenated full text of every guide for one-shot LLM ingestion.
- [AGENTS.md](AGENTS.md) — house conventions, source taxonomy, and publishing process for agents and human contributors working in this repo.
