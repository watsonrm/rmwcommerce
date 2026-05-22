# The Prompts-to-Agents Ladder

**When to stay with a prompt, when to package a skill, when to build an agent — and when a multi-agent system is actually warranted.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

If you can identify the right rung on this ladder before you build, you will ship faster and waste fewer tokens than most teams building with LLMs today. Specifically:

- Avoid rebuilding a prompt as a full agent and then wondering why it's slower, harder to debug, and no more correct
- Know the exact trigger that justifies moving from a packaged skill to an autonomous agent loop
- See the anti-patterns in plain terms — most AI over-engineering is one specific mistake, repeated
- Walk away with a decision table you can apply to your next project in five minutes

### Where to spend your time, in priority order

Most readers are somewhere between Rung 1 and Rung 2. The highest-value move for most people is finishing Rung 2 properly — not climbing to Rung 3.

| # | Situation | Right move | Why |
| :-- | :--- | :--- | :--- |
| **1** | You paste the same prompt setup more than twice | Package it as a skill (Rung 2) | Reuse without the context tax. Biggest gain, lowest effort. |
| **2** | You have a skill but it needs multiple tool calls in sequence, with decisions between them | Graduate to an agent (Rung 3) | Skills are single-invocation. Once the model needs to reason about intermediate results, you need a loop. |
| **3** | You have an agent but you keep adding tools and it's getting fragile | Refine the skill spec and tool allowlist before adding more tools | Complexity at Rung 3 compounds. Narrower scope is almost always the fix, not more tooling. |
| **4** | You have a working single agent and the work has clear natural fan-out | Consider multi-agent (Rung 4) | See the companion guide for the full treatment. Don't start here. |

---

## How to use this

Open a fresh Claude Code session. Paste this guide along with a description of your current workflow — what you're building, how you're running it, and what's breaking or feeling over-built. Then run:

> Apply the prompts-to-agents ladder to my workflow. Identify which rung I'm on, whether I've over-climbed, and tell me the one change that would give me the most leverage right now. Be specific.

---

## Background: why the ladder matters

There is a four-rung ladder from single prompt to multi-agent system. Each rung adds capability — and each adds cost: complexity, latency, and verification debt.

The most common failure mode in agent engineering today is reaching for Rung 3 (autonomous agent) when Rung 2 (packaged skill) would have done the job. The second most common is reaching for Rung 4 (multi-agent system) when a single well-configured agent was sufficient. Anthropic's own guidance on the topic puts it directly: *"success in the LLM space isn't about building the most sophisticated system. It's about building the right system for your needs."* ([source](https://www.anthropic.com/engineering/building-effective-agents))

Climbing unnecessarily compounds three costs:

- **Complexity.** Each new abstraction layer is a new place for bugs to hide and a new thing to maintain.
- **Latency.** Agentic loops trade speed for task performance. That's sometimes a good trade. It's a bad trade for work that one model call would finish in 200ms.
- **Verification debt.** The harder it is to see what your system actually did, the harder it is to catch when it does something wrong.

The ladder gives you a framework for asking the right question before building: *is the increment in capability worth the increment in those three costs?*

---

## Rung 1 — Prompt

A prompt is a single instruction in a chat session. Stateless or near-stateless. No reuse infrastructure.

**What it is:** You type something, the model responds, you're done. The context lives in your head and in the chat window. There is no artifact, no trigger mechanism, no tooling beyond what the model has by default.

**Where it works:** Tasks you do rarely, tasks where context varies materially each time, or tasks where you need to think out loud with the model to figure out what you actually want. A prompt is also the right starting point for *everything* — you should run a thing as a bare prompt before packaging it, to make sure it actually works.

**The trigger to move up:** You find yourself pasting the same setup text more than twice. Or you're onboarding a teammate by sharing your favorite prompt template. At that point, you're already maintaining a skill — you just haven't packaged it yet.

---

## Rung 2 — Skill

A skill is a packaged, reusable instruction set. It loads on demand. It does one thing well per invocation.

**What it adds over a prompt:** Reuse, optional tool allowlists, optional scripts the skill can call, and versioning you can reason about. In Claude Code, a skill is a folder with a `SKILL.md` file — instructions, scripts, and reference docs that Claude loads when the skill is relevant. ([source](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)) Trigger phrases or slash commands route to it. Anthropic introduced this as a named pattern in October 2025 with their Agent Skills release.

OpenAI's parallel pattern is Custom GPTs: *"a tailored version of ChatGPT"* configured with custom instructions, external knowledge, and allowed actions — same concept, different implementation.

Simon Willison, who covered the Anthropic skills launch the day it shipped, described the core simplicity well: *"The core simplicity of the skills design is why I'm so excited about it."* ([source](https://simonwillison.net/2025/Oct/16/claude-skills/)) Skills are Markdown files with optional scripts. They compose. They don't require a new protocol or a new agent runtime.

**What a skill is NOT:** Autonomous. A skill runs in a user's session, not in a loop. The user invokes it, it runs, it returns. There is no decision-making between steps. If the skill needs to call a tool, it calls one tool and returns the result — it doesn't decide what to do next based on what the tool returned.

**Where to stay:** A skill handles a surprising majority of useful AI workflows. The test is: does a human review each output before anything consequential happens? If yes, a skill's verification model is human review, which is often the cheapest and most reliable option. The cost of a skill is low; the verification cost of an agent is not.

Anthropic's guide names this class "workflows" — *"systems where LLMs and tools are orchestrated through predefined code paths."* ([source](https://www.anthropic.com/engineering/building-effective-agents)) A skill is the packaged, reusable version of a workflow.

**The trigger to move up:** Three conditions, any one of which justifies graduating to an agent:

1. The task needs multiple tool calls in sequence with the model making decisions between them based on intermediate results.
2. The user shouldn't have to be present for each step — the work needs to run unattended.
3. Verification is non-trivial enough to require its own logic (the model needs to check its own work, not just return output for a human to review).

If none of those is true, the right answer is a better skill, not an agent.

---

## Rung 3 — Agent

An agent is a skill plus a decision-making loop plus tools plus verification logic. The model reasons, acts, observes the result, and decides what to do next.

**The formal definition:** Shunyu Yao et al.'s ReAct paper (ICLR 2023) established the pattern: *"LLMs generate both reasoning traces and task-specific actions in an interleaved manner."* ([source](https://arxiv.org/abs/2210.03629)) Thought → Action → Observation, repeated until the task is done or the agent hits a stopping condition. This loop is what distinguishes an agent from a skill. A skill is one pass. An agent is many passes with reasoning between them.

Lilian Weng's taxonomy describes the three components that define an agent: planning (decompose the task, decide the next step), memory (track what's happened so far), and tool use (call external systems to gather information or take action). ([source](https://lilianweng.github.io/posts/2023-06-23-agent/)) A skill typically has tool use. An agent has all three.

Anthropic's framing distinguishes agents from workflows on the axis of control: agents are *"systems where LLMs dynamically direct their own processes and tool usage, maintaining control over how they accomplish tasks."* ([source](https://www.anthropic.com/engineering/building-effective-agents)) The model is in the driver's seat, not the code.

**What this costs.** Anthropic's guide is direct: *"agentic systems often trade latency and cost for better task performance."* Human oversight is also more expensive — the agent is doing more between check-ins, so each check-in has more to review. OpenAI's practical guide to building agents puts the same tradeoff in its framework for deciding whether an agent is warranted: the task needs to be complex enough and long-running enough that the benefit outweighs the added cost and latency. ([source](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf))

**The autonomy dimension.** Andrej Karpathy introduced the concept of the autonomy slider at YC AI Startup School in June 2025: the same agent architecture can operate at very different levels of autonomy depending on how much approval it needs from a human. ([source](https://www.youtube.com/watch?v=LCEmiRjPEtQ)) Low on the slider: the agent proposes each action and a human approves before execution. High on the slider: the human reviews only the final output. Neither is wrong — the right position depends on how reversible the actions are and how much trust the agent has earned.

This is the key design variable for Rung 3 that Rung 2 doesn't have: you can tune how autonomous your agent is, and you should start it lower and move it up as it proves itself.

**Where to stay:** One agent doing one well-defined job is enough for most workflows that genuinely need agentic behavior. The tools are clear, verification is solvable inside the agent's own loop, and a single context window can hold the relevant state.

**The trigger to move up:** Three conditions, any one of which justifies a multi-agent system:

1. The work has natural fan-out — many independent reads or tasks that can run in parallel.
2. Different sub-tasks genuinely need different prompts, tools, or domain expertise (specialization wins).
3. A single context window can't hold all the relevant state without degrading output quality.

If none of those is true, a single well-configured agent is the right answer. The companion guide covers what to do when one of them is.

---

## Rung 4 — Multi-agent system

A multi-agent system coordinates multiple agents — a thin orchestrator dispatching work to specialized subagents, each with typed return contracts.

This rung has its own guide: [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md). The short version: the payoff is real (parallel fan-out, specialization, context size management) but so are the failure modes (silent errors propagating through loose contracts, verification gaps at agent boundaries). The guide covers the architecture, the contracts, and a concrete phasing strategy for getting there.

The one thing worth saying here: **Rung 4 is not a destination to aim for.** It's the right tool for workflows that have genuinely outgrown Rung 3. The multi-agent guide assumes you've already established that.

---

## The over-climbing problem

Most AI engineering mistakes are not model selection errors or prompt quality errors. They're abstraction layer errors. Here are the three failure modes, in order of how often they come up.

### Failure 1: Agent where a skill would do

This is the most common failure. The signs: the agent's loop runs one or two iterations and then returns. The "decisions" it makes between steps are trivial — things a human would resolve in seconds, or things the skill spec could have just specified. The verification step checks things that weren't actually at risk.

What happened: someone saw the agent architecture, liked how it sounded, and built it — without asking whether the loop was necessary. The cost is real: latency goes up, the failure surface expands, and debugging a one-iteration agent loop is harder than reading a skill's output.

The test: write out what the agent actually does, step by step. If you can describe it without using the word "decides," it's a skill.

### Failure 2: Skill where a prompt would do

Building an entire Claude Skill for a task you do twice a year, with custom scripts and a trigger phrase and a tool allowlist, is engineering for the sake of engineering. The skill takes time to build, requires maintenance, and saves you approximately nothing.

The test: how many times have you done this task the same way? If the answer is fewer than five, stay at Rung 1. If the context varies materially each time, stay at Rung 1.

### Failure 3: Multi-agent where a single agent would do

The companion guide covers this in detail. The short version: if you don't have genuine fan-out, genuine specialization, or a context window problem, the orchestrator layer is overhead without payoff. See [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) for the cases where Rung 4 is actually warranted.

---

## Where to go next

If you've worked through this ladder and concluded that a multi-agent system is genuinely the right tool — your work has fan-out, or your agents need specialization, or your context is overflowing — the next step is [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md). That guide covers typed return contracts, intermediate-state logging, thin-orchestrator architecture, and a concrete phasing strategy for getting there without breaking what already works.

If you're still deciding whether you need Rung 3 at all, the right move is to build a Rung 2 skill first. It's faster, it's verifiable, and it tells you exactly what the agent would need to do that the skill can't — which is the clearest possible specification for the agent you'd eventually build.

---

## Sources & Attribution

All primary sources were verified live before publication (2026-05-22).

**Primary sources:**

- Anthropic Engineering — *Equipping Agents for the Real World with Agent Skills* (Oct 16, 2025): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Anthropic Engineering — *Building Effective Agents*, Erik Schluntz and Barry Zhang (Dec 19, 2024): https://www.anthropic.com/engineering/building-effective-agents
- Lilian Weng — *LLM Powered Autonomous Agents* (June 23, 2023): https://lilianweng.github.io/posts/2023-06-23-agent/
- Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao — *ReAct: Synergizing Reasoning and Acting in Language Models* (arXiv Oct 2022, ICLR 2023): https://arxiv.org/abs/2210.03629
- Simon Willison — *Claude Skills are awesome, maybe a bigger deal than MCP* (Oct 16, 2025): https://simonwillison.net/2025/Oct/16/claude-skills/
- Andrej Karpathy — *Software Is Changing (Again)*, YC AI Startup School keynote (June 2025): https://www.youtube.com/watch?v=LCEmiRjPEtQ
- OpenAI — *A Practical Guide to Building Agents* (April 2025): https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf

**Attribution:** The framing, ranking, decision criteria, anti-pattern analysis, and "where to stay / when to move up" structure are Rick Watson's original work. The underlying technical definitions and research — the workflow/agent distinction (Anthropic), the planning/memory/tools taxonomy (Weng), the ReAct loop (Yao et al.), the autonomy slider concept (Karpathy), the skills pattern (Anthropic, Willison) — are the property of their respective authors and cited with attribution. OpenAI introduced Custom GPTs in November 2023 as their parallel to the skills pattern (see https://openai.com/index/introducing-gpts/).

**Original commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or a sharper framing? Open an issue or PR.
