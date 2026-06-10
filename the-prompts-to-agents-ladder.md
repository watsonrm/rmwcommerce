---
title: The Prompts-to-Agents Ladder
description: "Decision table for choosing between a prompt, a packaged skill, a single agent, and a multi-agent system — with exact trigger conditions for each rung and the four anti-patterns named."
date: 2026-05-22
last_modified_at: 2026-05-25
author: Rick Watson
agent_friendly: true
keywords: when to package a prompt as a skill, when to use an agent vs prompt, prompt vs skill vs agent, stuck pasting the same prompt, Claude skill vs prompt, multi-agent overkill, AI over-engineering, AI under-packaging, when do I need an agent, my agent is slower than my prompt, rebuilt prompt as agent, climbing the agent ladder, never packaged my prompt
---

# The Prompts-to-Agents Ladder

**You're pasting the same setup into a fresh chat for the tenth time this week — and you've never packaged it as a skill. Or you went the other way — rebuilt a prompt as an agent, then as a multi-agent system, and now it's slower, more expensive, and no more correct than the prompt was. Both are wrong-rung failures on the same ladder. Each rung has an exact condition that justifies climbing it — or staying put. Miss it and the bill arrives in one of those two shapes. This is the decision table, with all four anti-patterns named.**

*By [Rick Watson](https://rmwcommerce.com) · Published 2026-05-22 · Updated 2026-05-25 · 15 min read · sources verified live before publication*

I run a production system of 20+ Claude skills and a multi-agent fleet across my consulting practice. The ladder below is what I apply before writing a single line of skill spec, and what I walk clients through before they spend money on the wrong shape. I have made all four failure modes in both directions — the one I see in every engagement is the quietest: a recurring workflow that should have been a skill three months ago and isn't.

Who this is for: anyone using LLMs who needs to decide whether the right shape is a prompt, a skill, a single agent, or a multi-agent system — whether that's deciding to finally package a workflow you've been re-typing for months, or deciding whether your next agent build is actually warranted.

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Quoted sources include: Andrew Ng / DeepLearning.AI, Anthropic, OpenAI, Shunyu Yao et al., Lilian Weng, Andrej Karpathy, Ethan Mollick, Simon Willison, Yohei Nakajima, and Riley Goodside. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

Already working at Rung 1–2 inside Claude Code? Practitioner tactics — context discipline, model routing, verification-first — are in [The Claude Code Workflow Optimizer](claude-code-optimizer.md). Already committed to Rung 4? The architecture playbook is in [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md).

If you can identify the right rung on this ladder before you build, you will ship faster and waste fewer tokens than teams that skip this question. Specifically:

- Avoid rebuilding a prompt as a full agent and then wondering why it's slower, harder to debug, and no more correct
- Know the exact trigger that justifies moving from a packaged skill to an autonomous agent loop
- See the anti-patterns in plain terms — most AI over-engineering is one specific mistake, repeated
- Walk away with a decision table you can apply to your next project in five minutes

### Where to spend your time, in priority order

Most readers are somewhere between Rung 1 and Rung 2. The highest-value move for most people is finishing Rung 2 properly — not climbing to Rung 3.

| # | Situation | Right move | Why |
| :-- | :--- | :--- | :--- |
| **1** | You paste the same prompt setup more than twice | Package it as a [skill (Rung 2)](#rung-2--skill) | Reuse without the [context tax](claude-code-optimizer.md#pillar-1-context-and-configuration-discipline-highest-roi). Biggest gain, lowest effort. |
| **2** | You have a skill but it needs multiple tool calls in sequence, with decisions between them | Graduate to an [agent (Rung 3)](#rung-3--agent) | Skills are single-invocation. Once the model needs to reason about intermediate results, you need a [loop](#rung-3--agent). |
| **3** | You have an agent but you keep adding tools and it's getting fragile | Refine the [skill spec](#rung-2--skill) and tool allowlist before adding more tools | Complexity at Rung 3 compounds. Narrower scope is the fix, not more tooling. |
| **4** | You have a working single agent and the work has clear natural fan-out | Consider [multi-agent (Rung 4)](#rung-4--multi-agent-system) | See [the companion guide](multi-agent-fan-out-and-verification.md) for the full treatment. Don't start here. |

---

## The four rungs

There is a four-rung ladder from single [prompt (Rung 1)](glossary.md#prompt-rung-1) to [multi-agent system (Rung 4)](glossary.md#multi-agent-system-rung-4). Each rung adds capability — and each adds cost. As the lede says: both directions of wrong-rung failure are real. Anthropic's own guidance puts it directly: *"success in the LLM space isn't about building the most sophisticated system. It's about building the right system for your needs."* ([source](https://www.anthropic.com/engineering/building-effective-agents))

Climbing unnecessarily compounds three costs:

- **Complexity.** Each new abstraction layer is a new place for bugs to hide and a new thing to maintain.
- **Latency.** Agentic loops trade speed for task performance. That's sometimes a good trade. It's a bad trade for work that one model call would finish in 200ms.
- **Verification debt.** The harder it is to see what your system actually did, the harder it is to catch when it does something wrong.

The ladder gives you a framework for asking the right question before building: *is the increment in capability worth the increment in those three costs?*

---

## Rung 1 — Prompt

A prompt is a single instruction in a chat session. No state. No reuse infrastructure.

**What it is:** You type something, the model responds, you're done. The context lives in your head and in the chat window. There is no artifact, no trigger mechanism, no tooling beyond what the model has by default.

**Where it works:** Tasks you do rarely, tasks where context varies materially each time, or tasks where you need to think out loud with the model to figure out what you actually want. A prompt is also the right starting point for *everything* — you should run a thing as a bare prompt before packaging it, to make sure it actually works.

**The trigger to move up:** You find yourself pasting the same setup text more than twice. Or you're onboarding a teammate by sharing your favorite prompt template. Riley Goodside — one of the first people hired anywhere in the industry specifically as a Staff Prompt Engineer — has described prompt engineering as a discipline for precisely specifying tasks in ways that also sharpen the engineer's own thinking. ([source](https://thegradientpub.substack.com/p/riley-goodside-the-art-and-craft)) When a prompt has done that work — when the specific phrasing is what carries the value, not just the general intent — it has earned its own artifact. That's when you package it.

---

## Rung 2 — Skill

A skill is a packaged, reusable instruction set. It loads on demand. It does one thing well per invocation.

**What it adds over a prompt:** Reuse, optional tool allowlists, optional scripts the skill can call, and versioning you can reason about. In Claude Code, a skill is a folder with a `SKILL.md` file — instructions, scripts, and reference docs that Claude loads when the skill is relevant. ([source](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)) Trigger phrases or slash commands route to it. Anthropic introduced this as a named pattern in October 2025 with their Agent Skills release. For Claude Code specifically, the practitioner tactics that make Rung 1–2 work well — context discipline, model routing, verification-first — are documented in [The Claude Code Workflow Optimizer](claude-code-optimizer.md).

OpenAI's parallel pattern is Custom GPTs: a tailored configuration with custom instructions, external knowledge, and allowed actions — same concept, different implementation. Ethan Mollick, Wharton professor and one of the most widely read practitioners on applied AI use, described Custom GPTs as a more repeatable and shareable form of prompt packaging. ([source](https://www.oneusefulthing.org/p/almost-an-agent-what-gpts-can-do)) He was also precise about what they are not: *"GPTs aren't autonomous agents yet. I had to give feedback to the AI a few times."* Rung 2 is where a human is still present for each output. That is not a bug — it is the right design for any workflow where review is cheaper than verification.

Simon Willison, who covered the Anthropic skills launch the day it shipped, noted the core architectural simplicity: Skills are Markdown files with optional scripts that compose without requiring a new protocol or agent runtime. ([source](https://simonwillison.net/2025/Oct/16/claude-skills/))

For the how-to side of this rung — registration, description writing, single source of truth, pushing deterministic work into code, self-verification — see [Building Proper Claude Skills](building-proper-claude-skills.md).

**What a skill is NOT:** Autonomous. A skill runs in a user's session, not in a loop. The user invokes it, it runs, it returns. There is no decision-making between steps. If the skill needs to call a tool, it calls one tool and returns the result — it doesn't decide what to do next based on what the tool returned.

**Where to stay:** A skill handles most useful AI workflows. The test is: does a human review each output before anything consequential happens? If yes, a skill's verification model is human review, which is the cheapest and most reliable option available. The cost of a skill is low; the verification cost of an agent is not.

Anthropic's guide names this class "workflows" — *"systems where LLMs and tools are orchestrated through predefined code paths."* ([source](https://www.anthropic.com/engineering/building-effective-agents)) A skill is the packaged, reusable version of a workflow.

**The trigger to move up:** Three conditions, any one of which justifies graduating to an agent:

1. The task needs multiple tool calls in sequence with the model making decisions between them based on intermediate results.
2. The user shouldn't have to be present for each step — the work needs to run unattended.
3. Verification is non-trivial enough to require its own logic (the model needs to check its own work, not just return output for a human to review).

If none of those is true, the right answer is a better skill, not an agent. Expect to double your testing time. An agent is 2-3× the maintenance of a skill.

---

## Rung 3 — Agent

An agent is a skill plus a decision-making loop plus tools plus verification logic. The model reasons, acts, observes the result, and decides what to do next.

**The empirical case first.** Andrew Ng's "Agentic Design Patterns" series (DeepLearning.AI, March 2024) reported a result that makes the capability jump concrete: GPT-3.5 in zero-shot mode achieves 48.1% on the HumanEval coding benchmark. The same model running in an agentic loop achieves 95.1% — beating GPT-4 zero-shot at 67.0%. ([source](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/)) An agent isn't a stylistic upgrade over a skill. The loop itself produces measurably different results, which is exactly why it's worth being deliberate about when to reach for it — and when not to.

**The formal definition.** Shunyu Yao et al.'s [ReAct loop](glossary.md#react-loop-yao-et-al) paper (ICLR 2023) established the pattern: *"LLMs generate both reasoning traces and task-specific actions in an interleaved manner."* ([source](https://arxiv.org/abs/2210.03629)) Thought → Action → Observation, repeated until the task is done or the agent hits a stopping condition. This loop is what distinguishes an agent from a skill. A skill is one pass. An agent is many passes with reasoning between them.

At the API level, the loop is concrete: your application sends a request with a tools array, Claude responds with `stop_reason: "tool_use"` and one or more `tool_use` blocks, your code executes the tools and returns `tool_result` blocks, and the cycle repeats until `stop_reason` is `"end_turn"`. ([source](https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/how-tool-use-works)) The model never executes anything itself — it emits a structured request and waits for the result.

**What distinguishes Rung 3 from Rung 2.** Ng's series named four patterns that characterize agentic workflows: [reflection (Ng pattern 1)](glossary.md#reflection-ng-pattern-1) (the model examines its own output to find ways to improve it), [tool use (Ng pattern 2)](glossary.md#tool-use-ng-pattern-2) (calling external functions to gather information or take action), [planning (Ng pattern 3)](glossary.md#planning-ng-pattern-3) (decomposing a goal into a multi-step plan and executing it), and [multi-agent collaboration (Ng pattern 4)](glossary.md#multi-agent-collaboration-ng-pattern-4) (multiple agents dividing work and debating solutions). ([source](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/)) A skill exhibits only one of these — tool use. An agent exhibits all four, or at minimum reflection and planning in addition to tool use. That is the sharpest vocabulary for the Rung 2 → Rung 3 line: if your system only has tool use, you have a skill. If it has reflection or planning on top of that, you have an agent.

Lilian Weng's taxonomy describes the three foundational components: planning (decompose the task, decide the next step), memory (track what's happened so far), and tool use (call external systems to gather information or take action). ([source](https://lilianweng.github.io/posts/2023-06-23-agent/)) The Ng four-pattern framing adds reflection explicitly and extends multi-agent as a fourth design axis; the two taxonomies are complementary. The line is sharp: when the model decides between steps rather than following a fixed path, you have crossed into agent territory.

**What this costs.** The three costs from [The four rungs](#the-four-rungs) — complexity, latency, verification debt — all compound here. Anthropic's guide is direct: *"agentic systems often trade latency and cost for better task performance."* ([source](https://www.anthropic.com/engineering/building-effective-agents)) Human oversight is also more expensive — the agent is doing more between check-ins, so each check-in has more to review.

**The autonomy dimension.** Andrej Karpathy introduced the concept of the [autonomy slider](glossary.md#autonomy-slider-karpathy) at YC AI Startup School in June 2025: the same agent architecture can operate at very different levels of autonomy depending on how much approval it needs from a human. ([source](https://www.youtube.com/watch?v=LCEmiRjPEtQ)) Low on the slider: the agent proposes each action and a human approves before execution. High on the slider: the human reviews only the final output. Neither is wrong — the right position depends on how reversible the actions are and how much trust the agent has earned.

This is the key design variable for Rung 3 that Rung 2 doesn't have: you can tune how autonomous your agent is, and you should start it lower and move it up as it proves itself. As autonomy increases, permission tuning becomes more load-bearing — see [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md) for the strategy.

**Where to stay:** One agent doing one well-defined job is enough for most workflows that need agentic behavior. The tools are clear, verification is solvable inside the agent's own loop, and a single context window can hold the relevant state.

**The trigger to move up:** Three conditions, any one of which justifies a multi-agent system:

1. The work has natural fan-out — many independent reads or tasks that can run in parallel.
2. Different sub-tasks genuinely need different prompts, tools, or domain expertise (specialization wins).
3. A single context window can't hold all the relevant state without degrading output quality.

If none of those is true, a single well-configured agent is the right answer. The companion guide covers what to do when one of them is.

---

## Rung 4 — Multi-agent system

A multi-agent system coordinates multiple agents — a thin [orchestrator](glossary.md#orchestrator) dispatching work to specialized [subagents](glossary.md#subagent), each with [typed return contracts](glossary.md#typed-return-contract).

This rung has its own guide: [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md). The short version: the payoff is real (parallel fan-out, specialization, context size management) but so are the failure modes (silent errors propagating through loose contracts, verification gaps at agent boundaries). The guide covers the architecture, the contracts, and a concrete phasing strategy for getting there.

The one thing worth saying here: **Rung 4 is not a destination to aim for.** It's the right tool for workflows that have genuinely outgrown Rung 3. The multi-agent guide assumes you've already established that.

---

## The four failure modes

Most AI mistakes are not model selection errors or prompt quality errors. They're abstraction layer errors — work running on the wrong rung. The priority ranking is in the table above; what follows are the named anti-patterns and their diagnostic tests:

### Failure 1: Prompt where a skill would do

This is the most common failure, by a lot. You have a setup you paste into a fresh chat multiple times a week — a rewriting style guide, a code-review checklist, a meeting-notes format, the way you like data summarized. You have never packaged it. Every invocation costs you the tokens to re-paste the context, the cognitive overhead of remembering what to include, and the consistency loss from forgetting one piece of it.

What happened: the leap from "I keep doing this" to "I should package this" feels bigger than it is. It is not. A SKILL.md is a markdown file with a name, a one-paragraph description, and your prompt. No scripts required. No tool allowlist required. No multi-step workflow required. Just the file.

The test: count how many times in the last month you pasted approximately the same setup text into a fresh chat. If the count is more than five and the context didn't vary materially, the skill has earned its place. The fix takes 30 minutes once. The savings compound every week after.

Why this is undercounted: the cost is invisible per-incident — you don't notice the tax until you add it up. The cost of *over*-climbing is loud (a failed agent build is a thing you have to debug). The cost of *under*-climbing is quiet (a workflow that's slower and noisier than it has to be, indefinitely). Both are real; only one announces itself.

### Failure 2: Agent where a skill would do

The most common over-climbing failure. The signs: the agent's loop runs one or two iterations and then returns. The "decisions" it makes between steps are trivial — things a human would resolve in seconds, or things the skill spec could have just specified. The verification step checks things that weren't actually at risk.

What happened: someone saw the agent architecture, liked how it sounded, and built it — without asking whether the loop was necessary. The cost is real: latency goes up, the failure surface expands, and debugging a one-iteration agent loop is harder than reading a skill's output.

The test: write out what the agent actually does, step by step. If you can describe it without using the word "decides," it's a skill.

There is a useful historical reference point here. In March 2023, Yohei Nakajima published BabyAGI — a task-driven autonomous agent that spawned tasks, prioritized them, and executed them in a loop. ([source](https://github.com/yoheinakajima/babyagi)) The project generated significant attention, and teams across the industry started building autonomous agent loops on the same pattern. Most of those early systems were unstable in production: the loop would drift, accumulate errors, or fail silently in ways that were hard to diagnose. The creator's own repository notes explicitly that BabyAGI is "not meant for production use." The autonomous-loop-with-LLM pattern only became reliable once typed contracts, intermediate-state logging, and verification at agent boundaries were added — which is what the multi-agent companion guide addresses.

### Failure 3: Multi-agent where a single agent would do

The companion guide covers this in detail. The short version: if you don't have genuine fan-out, genuine specialization, or a context window problem, the orchestrator layer is overhead without payoff. See [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) for the cases where Rung 4 is actually warranted.

### Failure 4: Skill where a prompt would do

The rarest of the four, because most people don't over-package. But it happens: building an entire Claude Skill for a task you do twice a year, with custom scripts and a trigger phrase and a tool allowlist, is engineering for the sake of engineering. The skill takes time to build, requires maintenance, and saves you approximately nothing.

The test: how many times have you done this task the same way? If the answer is fewer than five, stay at Rung 1. If the context varies materially each time, stay at Rung 1.

> [!CAUTION]
> ### When to ignore this advice
>
> If the task is **high-stakes one-off** (a keynote, a board meeting, a single-take podcast taping), pre-build the skill even on first use. The "twice a year" / "fewer than five" threshold optimizes for token cost; high-stakes one-offs optimize for not forgetting the recipe at 3am the night before. My `speaking-script` and `panel-moderation` skills both started as one-offs for specific events — they earned their place by being there when I needed them, not by being run three times first. Expect 30-60 min upfront vs. risking 30 min of fumbling at the moment.

---

## Apply this to your own workflow

The operational form of this guide is the Claude Code skill at [`skills/prompts-to-agents-ladder/`](skills/prompts-to-agents-ladder/). Install it once:

```bash
# from a clone of this repo
cp -r skills/prompts-to-agents-ladder ~/.claude/skills/
```

Then describe your current workflow to Claude — what you're building, how you're invoking it, what's breaking or feeling over-built — and say one of these (the skill's trigger phrases):

> Apply the prompts-to-agents ladder to my workflow.
> Which rung am I on?
> Should this be a skill or an agent?
> Am I over-engineering this agent?
> Do I need a multi-agent system?

Claude will load the skill on demand, identify your current rung, check for over-climbing, and recommend the single highest-leverage move.

---

## Where to go next

If you've worked through this ladder and concluded that a multi-agent system is genuinely the right tool — your work has fan-out, or your agents need specialization, or your context is overflowing — the architecture playbook lives in [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md). That guide covers typed return contracts, intermediate-state logging, thin-orchestrator architecture, and a concrete phasing strategy for getting there without breaking what already works.

If you're still deciding whether you need Rung 3 at all, the right move is to build a Rung 2 skill first. It's faster, it's verifiable, and it tells you exactly what the agent would need to do that the skill can't — which is the clearest possible specification for the agent you'd eventually build.

---

## Sources & Attribution

All primary sources were verified live before publication (2026-05-22).

**Tier 1 — Primary sources with measured results:**

- Andrew Ng / DeepLearning.AI — *Agentic Design Patterns Part 1: Four AI Agent Strategies That Improve GPT-4 and GPT-3.5 Performance* (March 20, 2024) — source for the HumanEval benchmark data: GPT-3.5 zero-shot 48.1%, GPT-3.5 agentic loop 95.1%, GPT-4 zero-shot 67.0%: https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/
- Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao — *ReAct: Synergizing Reasoning and Acting in Language Models* (arXiv Oct 2022, ICLR 2023) — source for the reason-act-observe loop definition and the benchmark evidence (+34% ALFWorld, +10% WebShop vs. imitation/RL baselines): https://arxiv.org/abs/2210.03629

**Tier 2 — Trusted primary documentation:**

- Anthropic Engineering — *Equipping Agents for the Real World with Agent Skills* (Oct 16, 2025): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Anthropic Engineering — *Building Effective Agents*, Erik Schluntz and Barry Zhang (Dec 19, 2024): https://www.anthropic.com/engineering/building-effective-agents
- Anthropic — *Tool use with Claude: How tool use works* (2026): https://platform.claude.com/docs/en/docs/agents-and-tools/tool-use/how-tool-use-works
- OpenAI — *A Practical Guide to Building Agents* (April 2025): https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
- Lilian Weng — *LLM Powered Autonomous Agents* (June 23, 2023): https://lilianweng.github.io/posts/2023-06-23-agent/

**Tier 3 — Practitioner perspectives (supporting role only):**

- Andrej Karpathy — *Software Is Changing (Again)*, YC AI Startup School keynote (June 2025) — autonomy-slider concept: https://www.youtube.com/watch?v=LCEmiRjPEtQ
- Ethan Mollick — *Almost an Agent: What GPTs can do*, One Useful Thing (Nov 7, 2023): https://www.oneusefulthing.org/p/almost-an-agent-what-gpts-can-do
- Simon Willison — *Claude Skills are awesome, maybe a bigger deal than MCP* (Oct 16, 2025): https://simonwillison.net/2025/Oct/16/claude-skills/
- Yohei Nakajima — *BabyAGI* (March 2023, archived September 2024) — historical reference on early autonomous-loop experiments: https://github.com/yoheinakajima/babyagi
- Riley Goodside — *The Art and Craft of Prompt Engineering*, The Gradient (podcast, 2023): https://thegradientpub.substack.com/p/riley-goodside-the-art-and-craft

**Attribution:** The framing, ranking, decision criteria, anti-pattern analysis, and "where to stay / when to move up" structure are Rick Watson's original work. The underlying technical definitions and research — the HumanEval data (Ng), the workflow/agent distinction (Anthropic), the planning/memory/tools taxonomy (Weng), the ReAct loop and benchmark evidence (Yao et al.), the tool-use API loop description (Anthropic), the four agentic design patterns (Ng), the autonomy slider concept (Karpathy), the skills pattern (Anthropic, Willison), the practitioner framing (Mollick), and the prompt-engineering craft perspective (Goodside) — are the property of their respective authors and cited with attribution. BabyAGI (Nakajima) is included as a historical reference on the evolution of the autonomous-agent pattern. OpenAI introduced Custom GPTs in November 2023 as their parallel to the skills pattern (see https://openai.com/index/introducing-gpts/).

**Corrections from prior circulating versions:** An earlier version of this article cited a specific Riley Goodside X/Twitter post (status/1614125922332061698) — that URL now returns a 403 error from X's bot-blocking infrastructure. The citation has been replaced with the Gradient podcast interview, which contains his documented thinking on the craft of prompt engineering. The substance of the point is unchanged.

**Original commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or a sharper framing? Open an issue or PR.

**Packaging credit:** Matt Ezyk first prototyped the SKILL.md form of this guide and pushed Rick to apply the same packaging to the rest of the rmwcommerce articles.
