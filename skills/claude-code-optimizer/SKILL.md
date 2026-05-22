---
name: claude-code-optimizer
description: Audit a Claude Code workflow and recommend the single highest-leverage fix (context, model routing, verification, skill/MCP hygiene). Trigger when user says "audit my workflow", "optimize claude code", "claude code is slow", "burning tokens", "agent keeps missing things", "context is full", "/optimize", "claude-code-optimizer", or "tune my setup".
---

# Claude Code Workflow Optimizer

Practitioner playbook for diagnosing a Claude Code workflow and prescribing the one fix that returns the most speed, quality, or token savings.

## When to use this skill

Invoke when the user reports any of:
- Sessions feel slow or expensive (token burn, long turn times)
- Claude is missing instructions, forgetting earlier turns, or repeating work
- A subagent is producing low-quality or scattered output
- The user asks to "audit", "optimize", "tune", or "clean up" their Claude Code setup
- The user is starting a new project and wants the setup right the first time

Do not invoke for one-off bug fixes inside a single file — this skill targets workflow-level problems.

## Core pillars (with the diagnostic question for each)

1. **Context discipline.** Ask: when did you last run `/clear` or `/compact`, and what does `/context` show right now?
2. **CLAUDE.md hygiene.** Ask: how many lines is your top-level CLAUDE.md, and does it link out to path-scoped rules under `.claude/rules/`?
3. **Model routing.** Ask: which model is handling file exploration vs. architecture vs. default edits? Is the `effort` tier set per task?
4. **Verification-first.** Ask: does the workflow write tests or a check command before code, or does Claude self-report success?
5. **Parallelism.** Ask: are long-running or noisy tasks running in subagents or git worktrees, or polluting the main session?
6. **Expression density.** Ask: are prompts commanding with `@file` coordinates and required output shape, or describing intent loosely?

## Diagnostic procedure

Run these in order. Stop at the first pillar that returns a clear smell — that is the fix to recommend.

1. **Frame the goal.** Ask the user what they are trying to do (project type, daily tasks, team size). One sentence is enough.
2. **Surface the pain.** Ask what specifically feels slow, expensive, or wrong. Pin it to a concrete recent example if possible.
3. **Check context state.** Have the user run `/context` and report capacity. Anything above ~50% with mixed topics is a context-discipline issue.
4. **Inspect CLAUDE.md.** Read the project's `CLAUDE.md` (and `~/.claude/CLAUDE.md` if relevant). Count lines. Over 200 is a hygiene issue.
5. **Map model routing.** Ask which model and effort tier are in use. Opus-for-everything or unset effort is a routing issue.
6. **Look for a verify step.** Check whether tests, a lint script, or a `verify` skill runs after edits. Missing verification is the single highest-leverage fix per Anthropic.
7. **Prescribe one fix.** Name the exact file, setting, or command to change. One fix per session — do not stack recommendations.

## Anti-patterns and smells

- CLAUDE.md over 200 lines, or a wall of prose with no links to scoped rules
- `/clear` never used between unrelated tasks; context above 50% mid-session
- Opus selected as the default for routine edits and file reads
- `effort` set to a numeric value (e.g. `effort 85`) instead of a named tier (`low`, `medium`, `high`, `xhigh`, `max`)
- 20+ MCP tools loaded when the active task only needs two or three
- No verification step — Claude reports "done" without running tests or a check command
- Long-running or noisy work (codemods, large refactors, log scrapes) running in the main session instead of a subagent or worktree
- Prompts that describe intent ("could you maybe look at the auth stuff") instead of commanding with `@file` paths and required output shape

## Highest-leverage fixes (cheat sheet)

| Smell | Fix | Where |
| --- | --- | --- |
| Context bloated | `/clear` between tasks; `/compact focus on <topic>` near 50% | session |
| CLAUDE.md too long | Trim to under 200 lines; move details to `.claude/rules/<scope>.md` | project root |
| Opus for everything | Route Haiku for exploration, Sonnet default, Opus for architecture | model selector |
| No verify step | Add a `verify` skill or post-edit test command | `.claude/skills/` or hooks |
| Noisy work in main session | Move to subagent under `.claude/agents/` or a git worktree | project config |
| Loose prompts | Use `@file` refs, demand structured output, give file coordinates | prompt itself |

## Recommendation format

When delivering the fix, give the user:
1. The pillar name and the specific smell observed.
2. The exact file, setting, or command to change (e.g. "trim `CLAUDE.md` from 412 lines to under 200 — move the testing section to `.claude/rules/testing.md`").
3. One sentence on the expected payoff (speed, token savings, or quality).
4. A one-line check they can run afterward to confirm it worked (e.g. `/context` shows lower baseline, or `wc -l CLAUDE.md` returns under 200).

Do not recommend a second fix until the first lands.

## Where this fits in the ladder

This skill is the practitioner companion for Rung 1–2 of the prompts-to-agents ladder (single prompts and repeatable skills). If the user's problems are about coordinating multiple agents or scheduling, route them to the `prompts-to-agents-ladder` skill to reassess the rung, then to `multi-agent-fan-out` if Rung 4 is justified.

---

Source article: https://github.com/watsonrm/rmwcommerce/blob/main/claude-code-optimizer.md
