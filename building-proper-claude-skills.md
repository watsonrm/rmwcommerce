---
title: Building Proper Claude Skills
description: "Five disciplines that separate a Claude Code skill that works from a markdown file that merely exists — registration, description-as-trigger, single source of truth, deterministic work in code, and self-verification."
date: 2026-06-10
author: Rick Watson
agent_friendly: true
keywords: how to build a Claude skill, SKILL.md, Claude Code skills tutorial, skill registration, description trigger phrases, skill vs agent, Claude skill YAML frontmatter, progressive disclosure Claude, when_to_use field, skill discovery paths
---

# Building Proper Claude Skills

**The five disciplines that separate a skill that works from a markdown file that merely exists.**

*By [Rick Watson](https://rmwcommerce.com) · Published 2026-06-10 · 12 min read · Claude Code mechanics verified against Anthropic documentation before publication*

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. The Claude Code mechanics described here are sourced from Anthropic's official Claude Code Skills documentation and their Agent Skills engineering article — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- Stop losing time to skills that don't fire, fire at the wrong times, or produce different output every run.
- Know exactly where to put a skill so the runtime discovers it without you having to remember to open the file.
- Understand the one frontmatter field that matters most — and the second field that most people miss.
- Walk away with a five-item checklist you can apply to any existing skill in 30 minutes.

### Where to spend your time, in priority order

This guide assumes you've already decided to build a skill — not an agent. If you're still on that decision, start with [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md), which covers the when. This guide is the how.

| # | Problem | Go to |
|:--|:--------|:------|
| **1** | Your skill errors as "unknown" or nobody runs it | [§1 Register it](#1-register-it-dont-just-write-it) — this is the most common failure |
| **2** | Skill fires at the wrong times, or never fires automatically | [§2 Description and when_to_use](#2-description-and-when_to_use-are-the-trigger) — the selector fields |
| **3** | You maintain a long playbook plus a stub that keep drifting apart | [§3 One source of truth](#3-keep-one-source-of-truth) — inline or thin shim |
| **4** | Skill is slow, expensive, or gives different answers on identical input | [§4 Push the work into code](#4-push-the-deterministic-work-into-code) — orchestrate vs. decide |
| **5** | Skill sometimes produces wrong output and nobody notices | [§5 Self-verification](#5-make-it-verify-itself) — the check-your-work step |

Most readers should fix §1 and §2 and stop. The rest are improvements, not emergencies.

## How to use this

The operational form of this guide is the Claude Code skill at [`skills/building-proper-claude-skills/`](skills/building-proper-claude-skills/). Install it once:

```bash
# from a clone of this repo
mkdir -p ~/.claude/skills && cp -r skills/building-proper-claude-skills ~/.claude/skills/
```

Then describe your skill — paste the SKILL.md, describe what's broken, or say what you're trying to build — and say one of these:

> Audit this skill against the five disciplines.
> Why isn't my skill firing?
> Review my SKILL.md.
> Is this skill registered correctly?
> How do I add a verification step to this skill?

Claude will load the skill on demand and apply the five disciplines to your situation. The article below is the reasoning behind each discipline; the skill is the operational form.

---

## 0. Where this sits on the ladder

On [the prompts-to-agents ladder](the-prompts-to-agents-ladder.md#rung-2--skill), a **Skill (Rung 2)** is a packaged single-invocation pattern: one tool-use shape per run, human reviews the output, no decision loop between intermediate results. If your work needs the model to reason about intermediate results between tool calls, you need a Rung-3 agent — but build the skill first anyway, because a working skill is the clearest possible specification for the agent you'd eventually build.

Everything below assumes you've made that call and you're building a skill.

---

## 1. Register it, don't just write it

The most common failure: a "skill" that is a markdown file full of good instructions which the runtime has no idea exists. It only runs if someone remembers to open it. That is a document with fragile routing, not a skill.

A real skill is **discovered by the runtime**. In Claude Code that means a `SKILL.md` with YAML frontmatter, placed where the runtime scans:

| Level | Path | Applies to |
|:------|:-----|:-----------|
| Enterprise | See managed settings | All users in your organization |
| Personal | `~/.claude/skills/<skill-name>/SKILL.md` | All your projects |
| Project | `.claude/skills/<skill-name>/SKILL.md` | This project only |
| Plugin | `<plugin>/skills/<skill-name>/SKILL.md` | Where plugin is enabled |

([source](https://code.claude.com/docs/en/skills))

Once registered, Claude loads the skill's description into its context at session start and can invoke it automatically when the description matches — or you can invoke it directly with `/skill-name`. The directory name is the command you type; the optional `name` frontmatter field sets the display label in skill listings but does not change the slash command.

The tell that you have this wrong: you reach for the skill the obvious way and the runtime says **"unknown skill."** The instructions existed; the registration didn't. The fix is not "remember to open the file next time." That reinstalls the fragile path. The fix is to register the skill so the runtime enforces the routing. *Enforce, don't remember.*

Minimum viable structure:

```
.claude/skills/
  my-skill/
    SKILL.md        # frontmatter + body (supporting files optional)
```

```markdown
---
description: >
  One paragraph: what this skill does. Put the key use case first — this is
  what Claude reads to decide whether to load the skill.
when_to_use: >
  Trigger phrases and example requests: "do the thing", "run the workflow",
  "when someone asks about X". See §2.
---

# my-skill

<the actual instructions, or a pointer to them — see §3>
```

A corollary: maintain a clean line between **skills a person invokes** and **internal playbooks an orchestrator calls by path**. The first kind must be registered — that's how it gets invoked. The second kind can stay as plain files. Registering everything is noise; registering nothing is the failure above. Register what humans reach for.

---

## 2. Description and when_to_use are the trigger

The runtime decides which skill to load by reading two frontmatter fields: `description` and `when_to_use`. Together they are truncated to 1,536 characters in the skill listing, so every word costs something. ([source](https://code.claude.com/docs/en/skills))

**`description`** is the primary field. Write it for the selector, not for a human skimming a catalog. The Anthropic docs put it precisely: "What the skill does and when to use it. Claude uses this to decide when to apply the skill. Put the key use case first." ([source](https://code.claude.com/docs/en/skills))

**`when_to_use`** is the right place for trigger phrases and example requests. It's appended to `description` in the listing and counts toward the same 1,536-character cap. Most people skip this field entirely and crowd trigger phrases into `description`, which works but reduces the space available for the "what it does" language the selector also needs.

A description like "handles invoices" gives the model nothing to match against. The real trigger surface belongs here: the slash command, the natural phrasings ("categorize this invoice", "how should I code this bill"), and any artifacts that should fire it ("a vendor bill PDF").

Two failure modes this fixes:

- **Never fires automatically.** The user says the thing, the model doesn't connect it to the skill, because the description didn't contain that phrasing. Trigger phrases buried in the skill body — which loads only *after* selection — are invisible at selection time.
- **Fires at the wrong time.** Equally a description problem. Specify what the skill is *not* for, and which sibling skill owns the adjacent case, to reduce false positives.

One additional field worth knowing: `disable-model-invocation: true` prevents Claude from loading the skill automatically. Use it for workflows with side effects you want to control manually — a `/deploy` or `/send-message` skill that you should trigger, not Claude. ([source](https://code.claude.com/docs/en/skills))

---

## 3. Keep one source of truth

Once you register a skill, you often have two artifacts: the registered `SKILL.md` and a longer playbook the team already maintained. Two copies of the same instructions will drift — someone updates the playbook, the registered copy silently goes stale, and the skill now does the old thing.

Resolve it one of two ways:

- **Inline** the instructions in `SKILL.md` and delete the other copy.
- Make `SKILL.md` a **thin shim**: frontmatter (for discovery and triggering) plus a one-line body that points at the canonical playbook — "read and follow `path/to/playbook.md` and execute it." The playbook stays the single source of truth; the shim provides registration and routing without forking the content.

The shim pattern is the cheaper migration when you already have a large, working playbook. What you must not do is leave two full copies and trust yourself to keep both current.

Progressive disclosure handles the related concern about context cost: the skill's description loads into Claude's context at session start, but the full body loads only when the skill is actually invoked. ([source](https://code.claude.com/docs/en/skills)) Long reference material bundled as supporting files in the skill directory costs nothing until Claude reads them.

---

## 4. Push the deterministic work into code

The expensive, slow, non-deterministic part of a skill is asking the model to do work that isn't actually judgment — sorting, ranking, classifying, aggregating, deduplicating. If the same inputs should always produce the same output, that's code, not a prompt.

The pattern: a script does the deterministic work and emits a structured result; the skill's instructions orchestrate around it and handle the parts that genuinely require judgment. A ranking that runs in a script finishes in under a second and produces the identical result every time. The same ranking done by re-reading every input through the model is slow, costs tokens proportional to the data, and varies run to run.

Rule of thumb: **the model orchestrates, the code decides.** Every loop you can move from the context window into a deterministic script makes the skill faster, cheaper, and reproducible — and shrinks the surface where it can be wrong.

Claude Code supports dynamic context injection (the `` !`command` `` syntax) that runs a shell command before the skill content is sent to the model. The command output replaces the placeholder inline. This is the right place to pre-compute or pre-fetch anything deterministic — the model receives actual data, not a task to go get it. ([source](https://code.claude.com/docs/en/skills))

---

## 5. Make it verify itself

A skill that produces an output and stops is a skill that fails silently. The last step of a proper skill checks its own work against the goal it was given, and says plainly whether it passed.

Verification is not "the model double-checks in prose." It's a concrete gate: re-read the artifact that was supposed to be written and confirm the change landed; assert the row was added; diff the result against the requested shape; re-run the deterministic check and compare. If the gate fails, the skill says so rather than reporting success. For anything that writes to the world, this is the difference between a skill you can trust and one that quietly corrupts state.

If you can add only one thing to an existing skill, add the check-your-work step.

---

## A minimal checklist

- [ ] Registered where the runtime discovers it — personal, project, or plugin path — not just a file you open manually.
- [ ] `description` contains what the skill does and when to use it, with the key use case first.
- [ ] `when_to_use` contains the slash command, natural-language trigger phrases, and what the skill is *not* for.
- [ ] One source of truth — instructions inlined in `SKILL.md`, or a thin shim pointing at the canonical playbook. No drifting duplicate.
- [ ] Deterministic work (sort, rank, classify, aggregate) lives in code or dynamic context injection, not in the prompt.
- [ ] Ends with a verification step that can report failure explicitly.
- [ ] Sits at the right rung — if it's growing a decision loop between tool calls, that's the signal to promote it to an agent, not to bolt more onto the skill. See [the ladder](the-prompts-to-agents-ladder.md#rung-3--agent) for the exact promotion conditions.

---

## Sources & Attribution

All primary sources verified before publication (2026-06-10).

**Tier 1 — Authoritative primary documentation:**

- Anthropic — *Extend Claude with Skills*, Claude Code documentation (current): https://code.claude.com/docs/en/skills — source for frontmatter field table, discovery paths, skill content lifecycle, progressive disclosure, control who invokes, dynamic context injection.
- Anthropic Engineering — *Equipping Agents for the Real World with Agent Skills* (Oct 16, 2025): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills — source for description-driven selection, progressive disclosure architecture (name/description in system prompt; full content on demand; supporting files on further demand), the Agent Skills standard.

**Tier 2 — Practitioner coverage:**

- Simon Willison — *Claude Skills are awesome, maybe a bigger deal than MCP* (Oct 16, 2025): https://simonwillison.net/2025/Oct/16/claude-skills/ — covers the architectural simplicity, YAML frontmatter, and description-driven selection.

**Cross-references in this repo:**

- [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when a skill is the right rung, and when to promote to an agent (Rung 3).
- [RMW Commerce Glossary — Skill (Rung 2)](glossary.md#skill-rung-2) — one-entry definition with hype/reality assessment.

**Attribution:** The five disciplines, their names, and the prioritization are Rick Watson's original work, grounded in first-party experience building and operating a skill library in Claude Code — specifically the registration / "unknown skill" failure mode and its fix, the thin-shim single-source pattern, the deterministic-code-over-model discipline, and the mandatory verification step. The Claude Code mechanics (frontmatter fields, discovery paths, progressive disclosure, invocation model) are Anthropic's work, cited with attribution.

**Corrections from prior circulating versions:** The draft source conflated the `description` and `when_to_use` frontmatter fields, treating `description` as the only selector field. Per Anthropic's current documentation, `when_to_use` is a distinct field specifically for trigger phrases and example requests, appended to `description` in the skill listing. The draft also implied the `name` frontmatter field sets the command name — per documentation, the command name comes from the directory name; `name` sets only the display label in skill listings. Both corrections have been applied above.

**Original commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or a sharper framing? Open an issue or PR at https://github.com/watsonrm/rmwcommerce.
