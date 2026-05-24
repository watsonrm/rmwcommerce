# AGENTS.md

Guidance for AI agents and human contributors working in this repository.

## Project overview

This is the public publication home for Rick Watson and RMW Commerce Consulting — long-form guides, reference docs, and runnable Claude Code skills on ecommerce, AI tooling, Claude usage, multi-agent systems, and related topics. Content covers everything from non-developer onboarding to Claude Code through to the agentic-web playbook that this repo's [`guides/marketing-to-agents.md`](guides/marketing-to-agents.md) documents.

Rick Watson is the principal of RMW Commerce Consulting and host of *The Watson Weekly*. Author identity, contact, and business links live in [`README.md`](README.md).

The repository carries an explicit copyright notice on each guide ("© 2026 Rick Watson / RMW Commerce Consulting") reserving rights on original commentary while permitting brief quotation with attribution. There is no separate `LICENSE` file. Treat each guide's masthead block as the canonical licensing statement for that document.

## Conventions

Every guide in this repository follows Rick's house style. Agents touching content should hold the same line:

- **Front-loaded answer.** Every long-form guide opens with a `TL;DR — what's in it for you` block, followed by a `Where to spend your time` priority table inside the first 30% of the file. Readers should be able to act after the table alone.
- **Three-tier source taxonomy.** Rank evidence as **data > primary docs > opinion**. Cite primary vendor documentation, peer-reviewed papers, and large-N industry studies in preference to commentary. Mark hype explicitly when consensus framing is wrong.
- **Verify every URL and every number before commit.** Soften or strip any claim that can't be sourced to a load-bearing document. Stale or fabricated citations are the fastest way to lose reader trust.
- **Inline citations + Sources & Attribution at the end.** Every load-bearing claim links inline; every guide closes with a `Sources & Attribution` section organized by category (vendor primary docs, standards bodies, industry studies, academic, etc.).
- **No AI tells, no emoji in headings.** Avoid em-dash–heavy throat-clearing, "in conclusion", "delve into", "navigate the landscape", "it's important to note", and similar register tics. Headings are plain English; do not decorate them.
- **ISO 8601 for any date you publish.** `YYYY-MM-DD` minimum; prefer `<time datetime="…">` where the rendering surface supports it.
- **Visible byline.** Every guide carries `*By [Rick Watson](https://rmwcommerce.com) · YYYY-MM-DD*` (or `· Published P · Updated U` if the dates differ) on the line between the tagline and the copyright blockquote. When you edit a guide, bump the `Updated` date to that day's ISO 8601 string (and switch to the two-date form if it isn't already).

## How publishing works

This repository is a maintainer-owned publication, not a community-contribution surface.

- **Author**: Rick Watson edits and approves all content.
- **Subagent pipeline**: All publication runs through the `rmwcommerce-publisher` subagent in Rick's Claude Code configuration. The subagent enforces the conventions above before anything lands.
- **Workflow**: Direct commits to `main`. No PR flow for the maintainer; PRs from third parties may be opened for discussion but the canonical path is direct-to-`main` via the publisher subagent.
- **Skills directory**: Each long-form guide has a runnable companion in [`skills/`](skills/). Skills are designed to be dropped into `~/.claude/skills/` and triggered by phrase; treat them as derivative of the corresponding guide and keep them in sync.

## Files agents should know about

- [`README.md`](README.md) — repository index and the canonical list of every guide. Start here when enumerating content.
- [`guides/marketing-to-agents.md`](guides/marketing-to-agents.md) — **the load-bearing reference for this entire repository's agent-friendliness posture**. The 22-item priority checklist in that guide is the standard the rest of this repo is held to. Read it before proposing structural or discoverability changes.
- [`guides/`](guides/) — newer long-form guides. The repo also has historical long-form guides at the root level (`ai-discoverability-and-protocols.md`, `claude-code-*.md`, `the-prompts-to-agents-ladder.md`, `multi-agent-fan-out-and-verification.md`, `claude-permissions-guide.md`, `configuring-claude-code-permissions.md`, `glossary.md`, `tokenmin-optimization-pointer.md`). Both locations are canonical; do not move existing guides.
- [`skills/`](skills/) — runnable Claude Code skills, one folder per skill, paired with the guide of the same name.
- [`llms.txt`](llms.txt) — curated index of this repository's content for LLM consumption. Regenerate when a new guide lands.
- [`llms-full.txt`](llms-full.txt) — concatenated full text of every guide in `llms.txt` order. Regenerate when any guide is edited.
- [`CLAUDE.md`](CLAUDE.md) — imports this file; no separate instructions.

## A note on the spec this repo applies to itself

`guides/marketing-to-agents.md` includes a 22-item priority checklist for agent-friendly publication. This repository deliberately applies only the subset of that checklist that survives GitHub's HTML sanitization: structured root files (`AGENTS.md`, `CLAUDE.md`, `llms.txt`, `llms-full.txt`) and content-level signals (visible bylines, ISO dates, front-loaded answers, citation discipline). JSON-LD-on-page, custom `<meta>` tags, `robots.txt` ownership, and HTTP-header items are out of scope here because GitHub controls the rendering surface; they apply when this content is republished to a controlled domain.
