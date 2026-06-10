---
description: >
  Applies the five disciplines for building proper Claude Code skills to a user's SKILL.md or skill description.
  Diagnoses registration failures, description/trigger problems, single-source-of-truth drift, deterministic work in prompts, and missing verification steps.
when_to_use: >
  Trigger when user says "audit this skill", "review my SKILL.md", "why isn't my skill firing",
  "is this skill registered correctly", "how do I add a verification step", "my skill errors as unknown",
  "skill fires at the wrong time", or pastes a SKILL.md for review.
  Also applies when someone asks "should my skill have a when_to_use field" or "where do I put trigger phrases".
---

## When to use this skill

Use when someone is building, debugging, or auditing a Claude Code skill. Entry points:
- They paste a SKILL.md and ask for a review
- They describe a skill that errors as "unknown skill" or never fires automatically
- They have a long playbook and a stub SKILL.md that are drifting apart
- They have a skill that's slow, variable, or fails silently
- They ask about frontmatter fields, trigger phrases, or skill discovery paths

## The five disciplines (apply in order)

### 1. Registration — is it where the runtime can find it?

Check the skill's location. Valid discovery paths:

| Level | Path |
|:------|:-----|
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` |
| Project | `.claude/skills/<skill-name>/SKILL.md` |
| Enterprise | Managed settings |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` |

The command name comes from the **directory name**, not the `name` frontmatter field. A skill that lives outside these paths will not be discovered — it's a document, not a skill.

**Failure test:** Does running `/skill-name` return "unknown skill"? If yes, the issue is registration, not the instructions.

**Fix:** Move or copy the directory to `~/.claude/skills/<skill-name>/` (personal, all projects) or `.claude/skills/<skill-name>/` (project-only).

### 2. Description and when_to_use — does the selector field do the work?

Inspect `description` and `when_to_use` in the frontmatter. Both are read at selection time, before the skill body loads.

- **`description`**: What the skill does. Key use case first. Used by Claude to decide when to load automatically.
- **`when_to_use`**: Trigger phrases and example requests. "Run when user asks X, says Y, pastes Z." This is where trigger phrases belong — not buried in the skill body.
- Both fields combined are truncated to 1,536 characters in the skill listing.

**Failure tests:**
- Skill never fires automatically → description doesn't contain the phrases the user actually says. Add them to `when_to_use`.
- Skill fires on unrelated requests → description is too broad. Add "not for X; use [sibling-skill] instead" to `when_to_use`.
- User wants manual-only invocation → add `disable-model-invocation: true` to frontmatter.

### 3. Single source of truth — is there a drifting duplicate?

Ask: is there a second copy of these instructions somewhere else (a longer playbook, a CLAUDE.md section, a wiki doc)?

If yes, choose:
- **Inline**: move the canonical content into SKILL.md, delete the other copy.
- **Thin shim**: keep SKILL.md as frontmatter + one line — "Read and follow `path/to/playbook.md` and execute it." The playbook is the source of truth; the shim provides registration only.

**Never** leave two full copies. They will drift.

### 4. Deterministic work — is it in code?

Look for loops, rankings, classifications, or aggregations inside the skill instructions that should always produce the same output for the same input. These belong in a script or in dynamic context injection — a shell command prefixed with `!` inside backticks, run before the prompt is sent — not in a prompt.

**Test:** If you ran the skill twice on identical input, would you get the identical result? If no, something deterministic is being asked of the model.

**Fix:** Extract that work into a script; have the skill call the script and interpret the result. Or use a `!`-prefixed backtick command to pre-compute and inject the result before the model sees the prompt. (Note: write that injection syntax only where you intend it to run — a literal `!`-and-backtick token placed in a skill body executes at load time.)

### 5. Self-verification — does it check its own work?

Read the skill's final step. Does it explicitly verify the output and report pass/fail?

"The model double-checks in prose" is not verification. A real check:
- Re-reads the file/row/state that was supposed to change
- Asserts the change landed
- Diffs the result against the requested shape
- Reports pass or fail explicitly

If the skill ends with "done" or a summary without checking, add a verification step.

## Output format

For each discipline, report: PASS / NEEDS-FIX / N/A with one sentence of reasoning. Then list fixes in priority order (registration failures first). Keep it concrete — if something is wrong, say exactly what to change.

## Reference

Source article: [Building Proper Claude Skills](../../building-proper-claude-skills.md)
Ladder placement: Rung 2 — see [The Prompts-to-Agents Ladder](../../the-prompts-to-agents-ladder.md#rung-2--skill)
Glossary: [Skill (Rung 2)](../../glossary.md#skill-rung-2)
