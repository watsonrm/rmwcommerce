# Token Optimization for Claude: The Full Guide Lives at tokenmin.ai

**This repo is the home for Claude coding patterns and workflow guides. Token cost analysis lives at tokenmin.ai — here's what you need to know and where to go.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-23 · Roughly 2 min read*

Who this is for: anyone running Claude in production who wants the short version of which three levers actually move token cost — the three highest-ROI of the six covered in the full guide.

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved. Quoting brief excerpts with attribution is fine. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## The short version

Three things that move Claude token spend, in the order they pay off:

- **Prompt caching.** Mark stable inputs (system prompt, tool definitions, reference docs) with `cache_control`. Cache hits bill at 0.1× standard input — Anthropic's own numbers put the savings at up to 90% on repeated workloads. This is a one-time API change, and it's the single largest lever for most setups. API users only. Skip if your traffic is sporadic (<1 call per 5 min) — cache writes cost more than reads save.
- **Model routing.** Haiku costs $1/MTok input; Opus costs $15/MTok. For mechanical tasks — file reads, reformatting, simple lookups — the cheaper model produces the same output at a fraction of the cost. Routing deliberately is the simplest cost reduction with no quality trade-off on those tasks. Per-task discipline. Skip if you only run one workflow daily.
- **Context discipline.** Every token in the context window costs money on every turn. A CLAUDE.md over 200 lines, a conversation history never cleared between tasks, and the same files re-read three times in a session — these compound into a 2–4× per-session cost increase that's invisible until measured. About 20 min one-time trim. Applies to anyone with a long-running Claude Code project.

## The full guide

The complete version of this guide — with cited numbers, API examples, tool call design patterns, and the anti-patterns list — is at:

**[tokenmin.ai/guides/claude-token-optimization](https://tokenmin.ai/guides/claude-token-optimization)**

It covers six levers in priority order, with every load-bearing claim backed by primary Anthropic documentation or Anthropic engineering writing.

## The runnable form

If you want Claude to audit your own setup and recommend one fix:

```bash
# from a clone of this repo
cp -r skills/claude-token-optimization ~/.claude/skills/
```

Then describe your Claude usage to Claude and say one of these:

> Audit my token spend.
> Why is Claude so expensive?
> Optimize my token usage.
> Find what's burning tokens.

Claude will load the [`skills/claude-token-optimization/`](skills/claude-token-optimization/) skill and walk through the levers in priority order, looking for the first real gap.

## Why tokenmin.ai

This repo covers the thinking side: frameworks, patterns, when-to-use decisions. Tokenmin.ai is the measurement side: it reads your Claude session logs (anonymized — no prompt text, no tool outputs), surfaces where the spend is actually going, and produces a ranked plan of what to fix first.

The guides on tokenmin.ai are written to be actionable whether or not you use the product.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved. Quoting brief excerpts with attribution is fine. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
