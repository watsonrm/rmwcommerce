---
name: claude-token-optimization
description: Audit a Claude setup for token waste and recommend the single highest-leverage cost reduction. Trigger when user says "audit my token spend", "why is Claude so expensive", "optimize my token usage", "find what's burning tokens", "reduce my Claude costs", "/optimize-tokens", or "token cost audit".
---

# Claude Token Optimization

Practitioner playbook for diagnosing token spend in Claude API and Claude Code workflows, and prescribing the one fix that returns the most savings.

## When to use this skill

Invoke when the user reports any of:
- Claude API or Claude Code costs feel high or have grown unexpectedly
- Session logs show token counts much higher than expected
- A workload that should be cheap is running expensive
- Tokenmin's report flagged a specific pattern and the user wants to act on it
- The user wants to audit their setup before costs scale up

Do not invoke for one-off prompt tuning on a single call — this skill targets structural patterns that compound across many sessions.

## Core levers (with diagnostic question for each)

1. **Prompt caching.** Ask: are stable inputs (system prompt, tool definitions, reference docs) marked with `cache_control`? What is the current cache hit ratio? Is the workload frequent enough to benefit (more than once every 5 minutes)?
2. **Model routing.** Ask: which model is handling file reads, reformatting, and simple lookups vs. complex reasoning? Is Opus used for mechanical tasks that Haiku would handle at 15× lower cost?
3. **Context discipline.** Ask: when was `/clear` last used? How many lines is the project CLAUDE.md? Are sessions running into context limits without a compact in between?
4. **Tool call design.** Ask: how many tools are loaded in the system prompt? Are tool calls running in parallel or sequentially? Are the same files being re-read multiple times per session?
5. **Output length control.** Ask: is extended thinking enabled by default? Are prompts vague in ways that generate long responses?
6. **Batch API.** Ask: are there async workloads (bulk evaluations, content moderation at scale) that don't require real-time responses?

## Diagnostic procedure

Run these in order. Stop at the first lever that returns a clear opportunity — that is the fix to recommend.

1. **Frame the workload.** Ask the user to describe what they're running: API, Claude Code, or both? Typical session length? Rough daily token volume or cost?
2. **Surface the pain.** Ask what specifically feels expensive or has grown recently. Pin to a concrete example if possible.
3. **Check caching.** Is `cache_control` in use? If yes, what is the cache hit ratio? If no, is the workload bursty enough to benefit?
4. **Check model routing.** Which model is the default? Are there mechanical tasks (file reads, reformatting, lookups) on Opus or Sonnet that Haiku could handle?
5. **Check context state.** In Claude Code: how long are sessions before `/clear`? What does the CLAUDE.md line count look like?
6. **Check tool count.** How many tools are loaded in the system prompt? Is the average tool calls per message above 1.0 (indicating parallel use)?
7. **Prescribe one fix.** Name the exact change: which API parameter to add, which model to route to, what to trim from CLAUDE.md. One fix per session — don't stack.

## Anti-patterns and smells

- No `cache_control` on a repeated workload with a stable system prompt
- Opus selected as the default for routine file reads and reformatting
- CLAUDE.md over 200 lines — loads in full on every session
- `/clear` never used between unrelated tasks in Claude Code; context well over 50% mid-session
- 20+ tools loaded when the active task needs two or three
- Tool calls running sequentially (average tools per message at or near 1.0) where parallel calls would eliminate round-trip overhead
- Same file read 3+ times in a session (file already in context — re-reading adds tokens without new information)
- Extended thinking enabled by default; thinking tokens billed on routine work that doesn't benefit from deep reasoning
- Dynamic content (user question) placed before stable content (system prompt, docs) in API call structure — breaks prefix caching
- Subagents spawned for small reads — cold-starts a new cache for a task that doesn't justify it

## Highest-leverage fixes (cheat sheet)

| Smell | Fix | Where |
| --- | --- | --- |
| No caching on repeated workloads | Add `cache_control: {"type": "ephemeral"}` to stable system prompt blocks | API call structure |
| Opus for everything | Route Haiku for exploration/reads, Sonnet as default, Opus for hard reasoning only | Model selector or API `model` param |
| CLAUDE.md too long | Trim to under 200 lines; move scoped rules to `.claude/rules/<scope>.md` | Project root |
| Context never cleared | `/clear` between unrelated tasks; `/compact` near 50% mark | Claude Code session |
| Too many tools loaded | Load only tools the task needs; consolidate specialized tools into composable ones | System prompt / tool config |
| Sequential tool calls | Add parallel tool use prompt; return all results in one user message | System prompt + API call handler |
| Same file re-read repeatedly | Add a read-once hook that logs already-read files | `.claude/hooks/` |
| Extended thinking on routine work | Leave thinking off by default; enable per-call with `effort: "low"` or `"medium"` on Opus 4.7 | API `output_config.effort` |

## Recommendation format

When delivering the fix:
1. Name the lever and the specific smell observed.
2. Give the exact change: file, API parameter, or command (e.g., "add `cache_control` to the system prompt block — your workload sends 200+ requests per session and none are cached").
3. One sentence on the expected payoff (cost reduction, context headroom, or token count).
4. A one-line check to confirm it worked (e.g., "check usage dashboard for cache hit ratio after 100 calls" or "`wc -l CLAUDE.md` returns under 200").

Do not recommend a second fix until the first lands.

## Key numbers (verified against Anthropic docs)

- Cache hit cost: 0.1× standard input (90% discount)
- Cache write cost: 1.25× (5-min TTL) or 2× (1-hour TTL) standard input
- Cache minimum: 1,024 tokens for Sonnet 4.6/4.5; 4,096 for Opus 4.7/4.5 and Haiku 4.5
- Negative-ROI threshold: workloads with less than one call per 5 minutes
- Haiku vs. Opus price spread: 15× on input, 15× on output
- CLAUDE.md official guidance: under 200 lines per file
- Tool consolidation measured impact: 37% token reduction (43,588 → 27,297 avg) — Anthropic engineering, "Advanced tool use"
- Tool search measured impact: 36% context reduction (191,300 → 122,800 tokens) — same source
- Manual `budget_tokens` extended thinking: **removed on Opus 4.7** (returns 400 error); deprecated on Sonnet 4.6 and Opus 4.6 — use `effort` parameter instead

## Where this fits in the ladder

This skill is the cost-focused companion to the `claude-code-optimizer` skill (which covers workflow quality and speed). If the user's problem is about agent coordination or scaling, route them to `prompts-to-agents-ladder` to confirm the right rung before adding infrastructure.

---

Source article: https://tokenmin.ai/guides/claude-token-optimization
Full guide: https://github.com/watsonrm/tokenmin-site/blob/main/guides/claude-token-optimization.md
