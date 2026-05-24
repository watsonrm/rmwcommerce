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

## This repo

A public landing point. Links, references, and anything Rick wants to share openly will live here over time.

### Guides

- [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — start here if you're not a developer. The meta-skill is knowing what to ask Claude, not learning implementations. Written by a non-developer who runs a 20+ skill agent system daily.
- [Claude Code for Non-Developers: Your First Session](claude-code-non-developers-first-session.md) — the hands-on companion to the field guide. Installation, conservative permissions, asking Claude to handle the technical setup, and the approval process as it plays out in a real session.
- [Claude Code Workflow Optimizer](claude-code-optimizer.md) — patterns for reducing token waste and rework in Claude Code, ranked by ROI. Context-window discipline, CLAUDE.md hygiene, verification-first workflow, model routing, and worktree fleets — all grounded in Anthropic's official documentation.
- [Making Claude Respond Faster](guides/making-claude-faster.md) — prompt caching, model selection, parallel tool calls, and the patterns that slow you down. 17 sources across primary docs, Anthropic engineering, independent practitioners, and peer-reviewed research.
- [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when to stay with a prompt, when to package a skill, when to build an agent, and when a multi-agent system is actually warranted. The on-ramp before the multi-agent guide.
- [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — how to structure Claude agent systems that scale without silently breaking. Typed return contracts, intermediate-state logging, thin-orchestrator architecture, and a concrete phasing strategy.
- [Why Is Claude Code So Noisy? What to Do About It](claude-code-noise.md) — your terminal looks like a wall of text by design. Explains the four sources of noise and ranks the tactics for filtering what matters from what's just volume.
- [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md) — the interruption problem isn't your imagination. Covers the permission model across claude.ai, Claude Desktop, and Claude Code, with starter defaults and a drift-consolidation strategy.
- [Configuring Claude Code permissions: real lessons vs. cargo cult](configuring-claude-code-permissions.md) — what the built-in read-only allowlist covers, what patterns are cargo cult, and when hooks and sandboxing are better tools than hand-rolled rules. 13 cited sources.
- [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md) — concept by concept on the AI-agent discoverability and protocol stack: what's deployable, what's wait-and-see, what's already dead. Includes audience-specific recommendations and direct attribution of hype.
- [RMW Commerce Glossary](glossary.md) — every named concept across all guides defined once, with hype vs. reality marked per entry. Organized by category; deep-linkable by anchor.
- [Building Excellent Software (with Claude)](guides/building-excellent-software-with-claude.md) — the tokenmin v0.12.1 → v0.12.5 case study: eight disciplines for taking a Claude-built artifact from working to production-grade. Grounded in the public issue backlog and test suite.
- [Marketing to Agents](guides/marketing-to-agents.md) — the authoritative playbook for making any website readable, citable, and operable across every class of AI agent: indexer bots, AI search surfaces, chat assistants, and agentic browsers. Every claim sourced; 22-item checklist impact-ordered by evidence weight.

### Skills

These are the runnable, on-demand forms of the guides above. Drop any folder into `~/.claude/skills/` and Claude Code will load it when the trigger phrases match.

- [skills/prompts-to-agents-ladder/](skills/prompts-to-agents-ladder/) — apply the 4-rung ladder to a workflow and recommend the right rung
- [skills/claude-code-optimizer/](skills/claude-code-optimizer/) — audit a Claude Code workflow and prescribe one high-leverage fix
- [skills/multi-agent-fan-out/](skills/multi-agent-fan-out/) — design or audit a multi-agent system before building
- [skills/claude-code-for-non-developers/](skills/claude-code-for-non-developers/) — coach a non-developer through ongoing Claude Code work
- [skills/claude-code-first-session/](skills/claude-code-first-session/) — walk a first-time non-developer through their initial session
- [skills/claude-token-optimization/](skills/claude-token-optimization/) — audit Claude API or Claude Code token spend and recommend one concrete cost reduction
- [skills/building-excellent-software/](skills/building-excellent-software/) — apply the excellent-software checklist to a Claude-built artifact and surface the highest-leverage gap before shipping

### Token optimization

Token cost analysis and the full optimization guide live at tokenmin.ai, the measurement product built on top of these patterns.

- [Token Optimization for Claude: The Full Guide Lives at tokenmin.ai](tokenmin-optimization-pointer.md) — 3-bullet TL;DR plus links to the complete guide and the runnable skill
