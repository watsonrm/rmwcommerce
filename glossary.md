# RMW Commerce Glossary: Every Named Concept Defined

**Every term used across Rick's guides, defined once — with hype vs. reality marked per entry.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- One place to look up any named concept from Rick's guides, without hunting across seven articles.
- Each entry follows the same five-field template: what it is, value, hype, what to do, source.
- The discoverability and protocol terms (llms.txt, MCP, WebMCP, A2A, openapi.yaml) get the most space here because they're the most contested. See the companion article [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md) for the full treatment.
- Skim by category. Jump via anchors. Cross-links go to the guide where each concept is used most.

### How to read each entry

Every entry uses this five-field template:

- **What it is:** one-sentence definition
- **What's in it for you:** concrete value if you adopt or understand it
- **What's hype:** the overclaim — or "n/a" with a one-line reason if there isn't one
- **What to do:** the practical action
- **Source:** primary doc + cross-link to the guide where it's used most

Where a field genuinely doesn't apply, the entry says so rather than padding.

---

## Category index

1. [Rungs and roles](#rungs-and-roles)
2. [Agentic design patterns](#agentic-design-patterns)
3. [Engineering contracts](#engineering-contracts)
4. [Claude Code primitives](#claude-code-primitives)
5. [Permissions model](#permissions-model)
6. [Context discipline](#context-discipline)
7. [Discoverability and protocols](#discoverability-and-protocols)
8. [Adjacent products and surfaces](#adjacent-products-and-surfaces)
9. [Cultural shorthand and framings](#cultural-shorthand-and-framings)
10. [Measurement and benchmarks](#measurement-and-benchmarks)

---

## Rungs and roles

*Full treatment: [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md)*

---

### Prompt (Rung 1)

- **What it is:** A single instruction in a chat session — stateless, no reuse infrastructure, no tooling beyond what the model has by default.
- **What's in it for you:** Zero setup. The right starting point for everything — run any task as a bare prompt before packaging it, to verify it works before investing in automation.
- **What's hype:** The framing that "prompt engineering is dead" now that agents exist. Prompts are still the foundation; agents are just structured prompts in loops.
- **What to do:** Stay here until you've done the same task setup more than twice. The trigger to move up is reuse, not sophistication.
- **Source:** [Prompts-to-agents ladder — Rung 1](the-prompts-to-agents-ladder.md#rung-1--prompt)

---

### Skill (Rung 2)

- **What it is:** A packaged, reusable instruction set that loads on demand — in Claude Code, a folder with a `SKILL.md` file, optional scripts, and optional tool allowlists. Runs one task well per invocation. Human still reviews each output.
- **What's in it for you:** Reuse without the context tax of re-explaining your setup every session. Handles a surprising majority of useful AI workflows.
- **What's hype:** n/a — solidly useful primitive. The hype goes the other direction: teams skip this rung and jump straight to agents when a skill would have done the job faster and with less maintenance.
- **What to do:** Before building an agent, ask whether a skill would handle it. If a human reviews each output and the task doesn't require decisions between tool calls, it's a skill.
- **Source:** [Anthropic — Equipping Agents for the Real World with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills); [Prompts-to-agents ladder — Rung 2](the-prompts-to-agents-ladder.md#rung-2--skill)

---

### Agent (Rung 3)

- **What it is:** A skill plus a decision-making loop plus tools plus verification logic. The model reasons, acts, observes the result, and decides what to do next — the ReAct loop in practice.
- **What's in it for you:** Measurably better results on tasks requiring multi-step reasoning. GPT-3.5 in an agentic loop achieves 95.1% on HumanEval vs. 48.1% zero-shot — the loop itself changes the output quality ceiling. ([source](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/))
- **What's hype:** Treating "agent" as a synonym for "better AI." An agent is the right tool for specific conditions (unattended work, multi-step decisions, non-trivial verification) — not a default upgrade from a skill.
- **What to do:** Graduate to an agent when: (1) the task needs multiple tool calls in sequence with decisions between them, (2) unattended operation is required, or (3) verification logic is non-trivial. Otherwise, stay at Rung 2.
- **Source:** [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents); [Prompts-to-agents ladder — Rung 3](the-prompts-to-agents-ladder.md#rung-3--agent)

---

### Multi-agent system (Rung 4)

- **What it is:** A thin orchestrator coordinating multiple specialized subagents, each with typed return contracts. Enables parallel fan-out, specialization, and context-window management beyond what a single agent can hold.
- **What's in it for you:** Real gains on parallelizable research and breadth-first workflows. Anthropic's internal system — Claude Opus 4 as lead agent, Claude Sonnet 4 subagents — outperformed single-agent Claude Opus 4 by 90.2% on their research evaluation. ([source](https://www.anthropic.com/engineering/multi-agent-research-system))
- **What's hype:** Treating multi-agent as a destination to aim for. It's the right tool when work has genuine fan-out, genuine specialization needs, or a context-window overflow problem — not otherwise.
- **What to do:** Read [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) before building. Implement typed return contracts and intermediate-state logging before adding fan-out.
- **Source:** [Anthropic — Multi-Agent Research System](https://www.anthropic.com/engineering/multi-agent-research-system); [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md)

---

### Orchestrator

- **What it is:** The lead agent in a multi-agent system. Plans, dispatches work to subagents, and aggregates typed results. Does not execute work it could delegate.
- **What's in it for you:** Keeps context usable across a full session by holding reference rows rather than full prose. The orchestrator shape determines whether a multi-agent system degrades or stays coherent at scale.
- **What's hype:** n/a — structural role, not an overclaim target.
- **What to do:** Keep it thin. An orchestrator that receives typed reference rows from eight subagents stays coherent. One that receives prose summaries degrades around the third agent return.
- **Source:** [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents); [Multi-Agent Fan-Out and Verification — Pillar 4](multi-agent-fan-out-and-verification.md#pillar-4-orchestrator-shape)

---

### Subagent

- **What it is:** A specialized agent dispatched by an orchestrator to execute a scoped task — one read, one write, one lookup — and return a typed result. Gets a complete brief; doesn't improvise scope.
- **What's in it for you:** Parallel fan-out for reads. Context isolation (noisy work stays out of the orchestrator's context). Independent testability and replaceability.
- **What's hype:** n/a — engineering building block with clear utility when used correctly.
- **What to do:** Give each subagent a narrow scope, a tool allowlist, and a typed return contract. Use general-purpose models (Sonnet, Haiku) for subagents; reserve Opus for the orchestrator on complex reasoning.
- **Source:** [Multi-Agent Fan-Out and Verification — Pillar 4](multi-agent-fan-out-and-verification.md#pillar-4-orchestrator-shape)

---

### Autonomy slider (Karpathy)

- **What it is:** Andrej Karpathy's concept from his June 2025 YC AI Startup School keynote: the same agent architecture can operate at very different levels of autonomy depending on how many human approval steps it requires. Low = agent proposes, human approves each action. High = human reviews only the final output.
- **What's in it for you:** A framework for calibrating agent deployment risk. More autonomy = more verification overhead owed, not less.
- **What's hype:** Framing high autonomy as the goal. High autonomy is appropriate only for reversible actions on well-understood tasks where the agent has earned trust.
- **What to do:** Start low on the slider, move up as the agent proves itself. As autonomy increases, typed contracts and intermediate-state logging become more load-bearing.
- **Source:** [Karpathy — YC AI Startup School keynote (Jun 2025)](https://www.youtube.com/watch?v=LCEmiRjPEtQ); [The Prompts-to-Agents Ladder — Rung 3](the-prompts-to-agents-ladder.md#rung-3--agent)

---

## Agentic design patterns

*Full treatment: [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md), [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md)*

---

### ReAct loop (Yao et al.)

- **What it is:** The foundational agent pattern from Yao et al. (arXiv 2022, ICLR 2023): Thought → Action → Observation, repeated until the task is done. The model interleaves reasoning traces with concrete actions. This is what distinguishes an agent from a skill at runtime.
- **What's in it for you:** Benchmark evidence that it works: ReAct outperformed imitation and RL baselines by +34% on ALFWorld and +10% on WebShop. ([source](https://arxiv.org/abs/2210.03629)) Every agent you build runs this loop.
- **What's hype:** n/a — well-documented pattern with measured benchmark results.
- **What to do:** Use it as the vocabulary for reasoning about what your agent is doing between tool calls. If you can describe your agent's steps without using the word "decides," it's a skill, not an agent.
- **Source:** [Yao et al. — ReAct (arXiv 2210.03629)](https://arxiv.org/abs/2210.03629); [The Prompts-to-Agents Ladder — Rung 3](the-prompts-to-agents-ladder.md#rung-3--agent)

---

### Reflection (Ng pattern 1)

- **What it is:** The agent examines its own output to find ways to improve it — a self-critique loop before returning a final result. One of Andrew Ng's four agentic design patterns.
- **What's in it for you:** Quality improvement without human review on each iteration. Particularly useful for writing, code generation, and structured data extraction where the model can evaluate its own output against defined criteria.
- **What's hype:** Infinite reflection loops. Reflection should be bounded (one or two passes, not open-ended) or it inflates latency and cost without proportional quality gain.
- **What to do:** Add one bounded reflection pass to any agent producing outputs where quality matters. Define what "better" means in the prompt so the model has a real criterion to evaluate against.
- **Source:** [Ng / DeepLearning.AI — Agentic Design Patterns (Mar 2024)](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/); [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md#rung-3--agent)

---

### Tool use (Ng pattern 2)

- **What it is:** The agent calls external functions — search, database reads, API calls, code execution — to gather information or take action. The model emits a structured request; your code executes it and returns the result.
- **What's in it for you:** Connects the model to real-world state. Without tool use, agents are reasoning about static knowledge; with it, they act on live data.
- **What's hype:** n/a — foundational capability. The hype is in calling something "agentic" when it only has tool use (that's a skill, not an agent, unless it has planning or reflection on top).
- **What to do:** Define narrow tool interfaces. Each tool should do one thing and return a typed result. Broad, poorly-scoped tool interfaces are the most common source of agent unpredictability.
- **Source:** [Ng / DeepLearning.AI — Agentic Design Patterns (Mar 2024)](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/)

---

### Planning (Ng pattern 3)

- **What it is:** The agent decomposes a goal into a multi-step plan and executes it, adapting as intermediate results arrive. Combines with tool use and reflection in a full agent loop.
- **What's in it for you:** Makes complex multi-step tasks tractable. The model handles the decomposition — you describe the goal, not the steps.
- **What's hype:** Treating planning as equivalent to getting the task done correctly. A plan is a proposal; each execution step can still fail. Planning requires verification at each step, not just at the end.
- **What to do:** Separate plan mode from execution mode (Claude Code's `Shift+Tab` for Plan Mode). Review the plan before authorizing execution on anything with side effects.
- **Source:** [Ng / DeepLearning.AI — Agentic Design Patterns (Mar 2024)](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/)

---

### Multi-agent collaboration (Ng pattern 4)

- **What it is:** Multiple agents divide work and, in some architectures, debate solutions. Each agent brings a specialized prompt, tool set, or domain context. Corresponds to Rung 4 on the ladder.
- **What's in it for you:** Parallel throughput on breadth-first tasks. Specialization that makes each agent independently testable.
- **What's hype:** Using multi-agent collaboration for decision-composition tasks where subagents need to merge outputs into a coherent whole. Cognition's "Don't Build Multi-Agents" identifies this failure mode precisely. ([source](https://cognition.ai/blog/dont-build-multi-agents))
- **What to do:** Use for reads with typed returns, not for decisions that compose. Typed return contracts are the boundary mechanism.
- **Source:** [Ng / DeepLearning.AI — Agentic Design Patterns (Mar 2024)](https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/); [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md)

---

### Orchestrator-workers pattern (Anthropic)

- **What it is:** Anthropic's name for a central LLM that dynamically breaks down unpredictable tasks and delegates to worker LLMs, with subtask decomposition determined at runtime. Defined in "Building Effective Agents."
- **What's in it for you:** Scales to complex tasks where the full subtask list isn't known up front. The orchestrator decides what the tasks are, not just how to split a known list.
- **What's hype:** n/a — this is Anthropic's own named pattern with measured production results.
- **What to do:** Implement with typed return contracts at every worker boundary. Thin orchestrator, fat subagents — the orchestrator plans and aggregates; workers execute.
- **Source:** [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents); [Multi-Agent Fan-Out and Verification — Pillar 4](multi-agent-fan-out-and-verification.md#pillar-4-orchestrator-shape)

---

### Evaluator-optimizer pattern

- **What it is:** One LLM generates output; a second LLM evaluates it against defined criteria and provides feedback; the first iterates. A structured version of reflection using a separate model or prompt as the evaluator.
- **What's in it for you:** Catches output quality problems before delivery. The evaluator can be a smaller, cheaper model if the evaluation criteria are well-specified.
- **What's hype:** Using evaluator-optimizer for tasks where human review is faster and better. The pattern earns its cost only for high-volume, well-specified outputs.
- **What to do:** Define the evaluation rubric in the evaluator prompt. If you can't write the rubric concretely, the human review is probably cheaper.
- **Source:** [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)

---

### Routing pattern

- **What it is:** A classifier step that directs inputs to the appropriate specialist agent or workflow branch based on input type. Separates the "what kind of task is this" decision from the "execute the task" logic.
- **What's in it for you:** Keeps specialist agents narrow and testable. Without routing, a single agent tries to handle all input types, which degrades each type.
- **What's hype:** n/a — plumbing pattern, not an overclaim target.
- **What to do:** Build routing as a small, cheap classifier prompt before deploying specialist agents. The routing step is worth getting right — a misclassified input breaks the downstream agent.
- **Source:** [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)

---

### Prompt chaining

- **What it is:** Passing the output of one LLM call as the input to the next in a defined sequence. Each step processes the result of the previous one. The simplest multi-step LLM workflow pattern.
- **What's in it for you:** Breaks complex tasks into verifiable sub-steps without requiring a full agent loop. Intermediate outputs can be validated before proceeding.
- **What's hype:** Calling prompt chaining "agentic." It's a workflow pattern — there's no model-driven decision between steps. That's the boundary.
- **What to do:** Use for tasks with clear sequential stages where each step's output is the next step's input and human review at each step is acceptable. Graduate to an agent only when the model needs to decide what to do next based on intermediate results.
- **Source:** [Anthropic — Building Effective Agents](https://www.anthropic.com/engineering/building-effective-agents)

---

## Engineering contracts

*Full treatment: [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md)*

---

### Typed return contract

- **What it is:** A defined schema — TypeScript-style or JSON Schema — that every agent must emit as its return. The orchestrator validates the return against the schema and fails fast if the contract is violated rather than passing bad state downstream.
- **What's in it for you:** The single highest-leverage change for any existing multi-agent system. GitHub's framing: "Natural language is messy. Typed schemas make it reliable." Failures surface at the boundary instead of poisoning downstream steps.
- **What's hype:** n/a — verified engineering practice, not an AI-specific overclaim.
- **What to do:** Define the schema first, before writing the agent. The schema is the specification. Use it in both the subagent prompt (what to return) and the orchestrator (what to expect).
- **Source:** [GitHub Engineering — Multi-agent workflows often fail](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/); [Multi-Agent Fan-Out and Verification — Pillar 1](multi-agent-fan-out-and-verification.md#pillar-1-typed-return-contracts)

---

### Discriminated-union action schema

- **What it is:** A pattern for write-agent return types: enumerate every legal outcome (ok / fixed / flagged, or created / updated / skipped / failed), require the agent to pick one, and let no fifth option exist. Any situation that doesn't fit a named union variant returns a failure — not an invented variant.
- **What's in it for you:** Kills the bug class where a write agent reports "looks good" while silently skipping a check it couldn't perform. Forces the agent to be explicit about what happened.
- **What's hype:** n/a — precise engineering pattern for a real failure mode.
- **What to do:** Every write agent needs a discriminated union, not an open-ended "status" field. If the agent's return could be interpreted differently by downstream steps, it's not tight enough.
- **Source:** [GitHub Engineering — Multi-agent workflows often fail](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/); [Multi-Agent Fan-Out and Verification — Pillar 2](multi-agent-fan-out-and-verification.md#pillar-2-action-schemas-for-write-agents)

---

### Intermediate-state log

- **What it is:** A directory written by every agent invocation containing: `input.json` (what was passed in), `output.json` (the typed return), `log.txt` (tool calls, durations, retries), and `error.txt` (only on failure). Path format: `/tmp/agent-runs/<run_id>/<agent_name>/<invocation_id>/`.
- **What's in it for you:** Makes partial failures debuggable without re-running the whole workflow. Without it, a scheduled agent that fails leaves no trace. With it, you read the log.
- **What's hype:** n/a — logging practice that applies equally to traditional distributed systems. Not AI-specific.
- **What to do:** Implement before adding fan-out. The log is the foundation for recovery, idempotency, and debugging. For automated or scheduled workflows, use a persistent path rather than `/tmp/`.
- **Source:** [Multi-Agent Fan-Out and Verification — Pillar 3](multi-agent-fan-out-and-verification.md#pillar-3-design-for-failure)

---

### Idempotent write

- **What it is:** A write operation that produces the same result whether run once or ten times on the same input. A document-writing agent checks for an existing document before creating. A calendar agent updates in place rather than creating a duplicate. Re-running an agent on the same input never duplicates state.
- **What's in it for you:** Safe retries. Debuggable replays. Automated workflows that can recover from interruption without creating duplicate artifacts.
- **What's hype:** n/a — foundational distributed-systems principle, not an AI innovation.
- **What to do:** Build idempotency in by default for every write agent. `skipped_idempotent` should be a first-class return variant in the discriminated union, not an exception.
- **Source:** [Multi-Agent Fan-Out and Verification — Pillar 3](multi-agent-fan-out-and-verification.md#pillar-3-design-for-failure)

---

## Claude Code primitives

*Full treatment: [Claude Code Workflow Optimizer](claude-code-optimizer.md), [Claude Code for Non-Developers: Your First Session](claude-code-non-developers-first-session.md)*

---

### CLAUDE.md

- **What it is:** A markdown file at your project root (or `~/.claude/CLAUDE.md` for user-global instructions) that Claude Code reads at the start of every session. Contains: environment commands, syntax conventions, architectural rules, and pointers to where more detail lives.
- **What's in it for you:** Persistent project context without re-explaining setup every session. The file loads automatically — no copy-paste required.
- **What's hype:** Treating CLAUDE.md as a place to dump everything. Past ~200 lines, instructions get ignored: Anthropic's docs state directly that files over 200 lines "consume more context and may reduce adherence."
- **What to do:** Keep it under 200 lines. Use path-scoped rules under `.claude/rules/` for anything that only applies to certain files. Move reference material to linked docs.
- **Source:** [Anthropic — Claude Code Memory](https://code.claude.com/docs/en/memory); [Claude Code Workflow Optimizer — Pillar 1](claude-code-optimizer.md#pillar-1-context-and-configuration-discipline-highest-roi)

---

### Slash commands (general)

- **What it is:** Claude Code's built-in commands prefixed with `/`. Used for session management (`/clear`, `/compact`), inspection (`/context`, `/permissions`), and agent management (`/agents`). Slash commands are also extensible — you can define custom commands that invoke skills.
- **What's in it for you:** Direct control over session state without needing to prompt Claude about it. `/context` shows what's consuming your context window; `/permissions` shows all active rules and their source files.
- **What's hype:** n/a — utility commands, not an overclaim target.
- **What to do:** Learn `/clear`, `/compact`, `/context`, and `/permissions` first. They cover the session-management and debugging needs that come up most.
- **Source:** [Anthropic — Claude Code Best Practices](https://code.claude.com/docs/en/best-practices)

---

### /clear

- **What it is:** Resets the current conversation — full context wipe. Stateless restart while keeping the session open.
- **What's in it for you:** Removes accumulated context between unrelated tasks. Yesterday's debugging session has no business in today's feature build.
- **What's hype:** n/a — thirty-second habit with meaningful quality impact.
- **What to do:** Run between tasks. The cost is one slash command; the benefit is a clean context for the next task.
- **Source:** [Anthropic — Claude Code Best Practices](https://code.claude.com/docs/en/best-practices); [Claude Code Workflow Optimizer](claude-code-optimizer.md)

---

### /compact

- **What it is:** Summarizes the conversation history, preserving what matters while freeing context space. Accepts a focus argument to direct what survives the summarization: `/compact focus on the API changes`.
- **What's in it for you:** Mid-session summaries are more accurate than last-minute ones. Running `/compact` proactively around the 50% context mark preserves detail that vanishes if you wait until the context is full.
- **What's hype:** n/a — solidly useful session-management primitive.
- **What to do:** Run around the 50% context mark on long sessions, with a focus argument. Don't wait for the context-full warning — the summary quality drops as context approaches the limit.
- **Source:** [Anthropic — Claude Code Best Practices](https://code.claude.com/docs/en/best-practices); [Claude Code Workflow Optimizer](claude-code-optimizer.md)

---

### MCP server (definitional)

*See the full entry in [Discoverability and protocols — MCP](#mcp-model-context-protocol) below for the protocol treatment.*

- **What it is:** A process that exposes tools, data sources, or prompts to Claude via the Model Context Protocol. In Claude Code, MCP servers are configured under `.claude/settings.json` and appear as `mcp__<servername>__<toolname>` in the permissions model.
- **What's in it for you:** Any external service you talk to repeatedly — GitHub, Slack, databases, internal APIs — becomes natively callable without explaining HTTP and parsing responses.
- **What's hype:** n/a in the Claude Code primitives context — MCP servers are plumbing. The hype is in the broader protocol landscape; see the discoverability section.
- **What to do:** Add MCP servers for services you use in more than a few sessions per week. Start with read-only MCP tools; add write tools at the project level only.
- **Source:** [Anthropic — Claude Code Settings](https://code.claude.com/docs/en/settings); [Claude Code Workflow Optimizer — Pillar 3](claude-code-optimizer.md#pillar-3-parallelism-and-scale-advanced)

---

### Statusline

- **What it is:** The status bar at the bottom of Claude Code's terminal interface, showing current context usage, active model, and session state.
- **What's in it for you:** Real-time view of context consumption without needing to run `/context`. The fill level tells you when to run `/compact` before context degradation starts.
- **What's hype:** n/a — display element.
- **What to do:** Glance at it periodically. When it reaches ~50% full, run `/compact` with a focus argument.
- **Source:** [Anthropic — Claude Code interface docs](https://code.claude.com/docs/en/best-practices)

---

### Hooks

- **What it is:** Scripts that run at defined points in Claude Code's execution cycle — before or after tool calls, on session start, on file write. Configured in `.claude/settings.json` under the `hooks` key.
- **What's in it for you:** Automation that fires without you having to ask. Post-write hooks can run linters, formatters, or tests automatically after Claude edits a file.
- **What's hype:** n/a — automation primitive with clear utility.
- **What to do:** Start with a post-write format hook for your primary language if you use a formatter. That's the highest-value, lowest-risk hook for most setups.
- **Source:** [Anthropic — Claude Code Settings](https://code.claude.com/docs/en/settings)

---

### Plan mode

- **What it is:** A Claude Code session mode (toggled via `Shift+Tab`) that separates planning from execution. In plan mode, Claude proposes a plan but does not write files or run commands. You review the plan before authorizing execution.
- **What's in it for you:** Prevents cascading misunderstandings in multi-file changes. Particularly useful for ambiguous requests where the implementation choices matter.
- **What's hype:** Using plan mode for every task. It adds overhead for small, scoped requests. Worth the cost for complex multi-file work; overhead for `git status` equivalents.
- **What to do:** Use for any task where you care about how it's done, not just what gets done. Skip for clearly bounded, low-stakes operations.
- **Source:** [Anthropic — Claude Code Best Practices](https://code.claude.com/docs/en/best-practices); [Claude Code Workflow Optimizer — Pillar 2](claude-code-optimizer.md#pillar-2-model-routing)

---

### Worktree / worktree fleet

- **What it is:** Git worktrees are separate working copies of the same repo at different paths, each on an independent branch. A worktree fleet is multiple concurrent Claude Code sessions, each in its own worktree — Anthropic's officially endorsed pattern for parallel development. (`git worktree add ../my-feature feature-branch`)
- **What's in it for you:** True parallelism without branch-switching friction. Three features can be in-flight simultaneously without any one Claude session knowing about the others.
- **What's hype:** Starting with worktree fleets before single-session workflow is clean. The overhead is real; the payoff only materializes when juggling 3+ active branches at once.
- **What to do:** Reach for this when parallel work is genuine. Cap concurrent sessions at 3–5 — beyond that, oversight quality drops.
- **Source:** [Anthropic — Claude Code Best Practices](https://code.claude.com/docs/en/best-practices); [Claude Code Workflow Optimizer — Pillar 3](claude-code-optimizer.md#pillar-3-parallelism-and-scale-advanced)

---

### Background agent

- **What it is:** A Claude Code agent running asynchronously — work that happens without occupying your foreground session. Configured via the subagents docs. Appropriate for tasks that take minutes and don't require real-time redirection.
- **What's in it for you:** Removes narration from your foreground session for long-running work. The work runs, you check the output when it's done.
- **What's hype:** n/a — operational pattern with clear use case.
- **What to do:** If you find yourself watching Claude work for more than a few minutes without actively redirecting it, the work belongs in a background agent.
- **Source:** [Anthropic — Claude Code Subagents](https://code.claude.com/docs/en/sub-agents); [Why Is Claude Code So Noisy?](claude-code-noise.md)

---

### Output style / verbosity tuning

- **What it is:** Claude Code settings that adjust how much the model narrates its work — the volume of reasoning traces, status updates, and intermediate summaries visible in your terminal.
- **What's in it for you:** Marginal noise reduction. Worth experimenting with once the main levers (context discipline, subagents for noisy work) are already dialed in.
- **What's hype:** Treating verbosity tuning as the primary noise fix. It's the last lever, not the first.
- **What to do:** Configure via `defaultMode` in settings after the context discipline and subagent patterns are in place. Don't reach for it first.
- **Source:** [Anthropic — Claude Code Settings](https://code.claude.com/docs/en/settings); [Why Is Claude Code So Noisy?](claude-code-noise.md)

---

## Permissions model

*Full treatment: [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md)*

---

### Allow / ask / deny semantics

- **What it is:** The three permission rule types in Claude Code. Allow = proceed without prompting. Ask = always prompt. Deny = block outright (bare tool name removes it from context entirely; scoped rule blocks matching commands only). Evaluation order: deny → ask → allow. First matching rule wins.
- **What's in it for you:** Precise control over what Claude can do without asking. The right allow/deny mix eliminates most interruption friction while keeping safety checkpoints on operations that matter.
- **What's hype:** n/a — the model is what it is; the documentation is precise.
- **What to do:** Use allow for zero-side-effect operations (read-only MCP, safe Bash reads). Use deny for operations you never want Claude to execute. Let ask remain on everything write-consequential until you've built trust.
- **Source:** [Anthropic — Claude Code Permissions](https://code.claude.com/docs/en/permissions); [Claude Permissions Guide — Section 2](claude-permissions-guide.md#section-2-the-claude-code-permission-model-in-depth)

---

### Bash wildcard pattern

- **What it is:** Claude Code's glob-pattern syntax for Bash permission rules. `Bash(git *)` matches any command starting with `git `. `Bash(find:*)` is equivalent to `Bash(find *)`. A space before `*` enforces a word boundary — `Bash(ls *)` matches `ls -la` but not `lsof`.
- **What's in it for you:** One wildcard covers a whole command family instead of approving each variant individually. The mechanism that keeps `settings.local.json` manageable.
- **What's hype:** n/a — syntax specification, not an overclaim target.
- **What to do:** Wait until you've approved several similar commands, then promote to a wildcard and delete the specific entries. Tight-then-wildcard is the right rhythm.
- **Source:** [Anthropic — Claude Code Permissions](https://code.claude.com/docs/en/permissions); [Claude Permissions Guide — Section 2](claude-permissions-guide.md#section-2-the-claude-code-permission-model-in-depth)

---

### MCP wildcard pattern

- **What it is:** Permission rule format for MCP server tools: `mcp__<servername>__<toolname>`. Whole-server wildcard: `mcp__puppeteer__*` (or just `mcp__puppeteer`). Per-tool: `mcp__puppeteer__puppeteer_navigate`.
- **What's in it for you:** Allows allowing all reads from a trusted MCP server with one rule, while separately managing write tools.
- **What's hype:** n/a — syntax specification.
- **What to do:** Use whole-server wildcards for trusted read-only MCP servers. Use per-tool rules for servers that mix read and write operations.
- **Source:** [Anthropic — Claude Code Permissions](https://code.claude.com/docs/en/permissions); [Claude Permissions Guide — Section 2](claude-permissions-guide.md#section-2-the-claude-code-permission-model-in-depth)

---

### Settings hierarchy (global / global-local / project / project-local)

- **What it is:** Claude Code's four-level settings file precedence: (1) managed/org settings (highest), (2) `~/.claude/settings.json` (user-global), (3) `.claude/settings.json` (shared project), (4) `.claude/settings.local.json` (personal project, not committed). Deny at any level blocks allow at any lower level.
- **What's in it for you:** The right mental model for where to put each permission rule. Global for operations safe everywhere. Project for project-specific authorizations. Local for one-off approvals that shouldn't be committed.
- **What's hype:** n/a — the model is the model.
- **What to do:** Put read-only MCP and safe Bash wildcards in `~/.claude/settings.json`. Put write MCP in `.claude/settings.json` per project. Let `.claude/settings.local.json` fill up with specifics, then consolidate.
- **Source:** [Anthropic — Claude Code Settings](https://code.claude.com/docs/en/settings); [Claude Permissions Guide — Section 1](claude-permissions-guide.md#section-1-the-three-environments-and-how-they-differ)

---

### Drift consolidation

- **What it is:** The periodic process of auditing `settings.local.json` and `~/.claude/settings.json` to group specific one-off approvals into wildcards, promote wildcards to the appropriate level, and delete the specific entries they supersede.
- **What's in it for you:** Prevents the settings file from filling with hundreds of hyper-specific rules that could be three wildcards. The actual fix for permission hell over months of use.
- **What's hype:** n/a — maintenance practice.
- **What to do:** Do it every month or two. Group by command family (all `curl` against the same API → one wildcard), promote to the right level, delete specifics.
- **Source:** [Claude Permissions Guide — Section 4](claude-permissions-guide.md#section-4-the-drift-problem-and-how-to-consolidate)

---

### Layered allowlist

- **What it is:** Rick's framework for building permission rules: start tight (per-call approval), broaden specifically as trust is established, and consolidate to wildcards when patterns are clear. A deliberate risk-calibration approach rather than a one-time configuration.
- **What's in it for you:** Avoids both extremes: approving everything (security risk, no checkpoints) and approving nothing (constant friction, agents can't run).
- **What's hype:** n/a — this is Rick's working practice, not a vendor claim.
- **What to do:** Apply the three tiers: Tier A (read MCP, allow globally), Tier B (write MCP, allow per-project), Tier C (Bash, wildcard once a category is proven safe).
- **Source:** [Claude Permissions Guide — Section 3](claude-permissions-guide.md#section-3-my-starter-defaults--the-working-set)

---

### Tier A / B / C starter defaults (Rick's framing)

- **What it is:** Rick's three-tier categorization for permission allowlisting. Tier A = read-only MCP (allow globally, no side effects). Tier B = write MCP (allow per-project, has side effects). Tier C = Bash wildcards (allow globally once a command category is proven safe).
- **What's in it for you:** A starting point rather than building from scratch. Tier A and Tier C cover most of the common interruption friction with minimal risk.
- **What's hype:** n/a — first-person configuration notes, explicitly framed as "what I run" not universal prescription.
- **What to do:** Copy the starter JSON from the permissions guide as a baseline. Adjust MCP tool names to match your actual server configuration — run `/permissions` in a live session to verify.
- **Source:** [Claude Permissions Guide — Section 3](claude-permissions-guide.md#section-3-my-starter-defaults--the-working-set)

---

## Context discipline

*Full treatment: [Claude Code Workflow Optimizer](claude-code-optimizer.md), [Why Is Claude Code So Noisy?](claude-code-noise.md)*

---

### Context window

- **What it is:** The maximum amount of text (tokens) a model can hold in a single conversation — everything visible to Claude in the current session, including CLAUDE.md, conversation history, file reads, command outputs, and MCP server descriptions.
- **What's in it for you:** The fundamental resource constraint in Claude Code. Every best practice follows from it. Anthropic's docs state: "LLM performance degrades as context fills."
- **What's hype:** The notion that a larger context window eliminates the management problem. Larger windows reduce urgency but don't eliminate the dynamic — performance still degrades as context fills, just later.
- **What to do:** Treat it like RAM. Track it with `/context`. Manage it with `/compact` and `/clear`.
- **Source:** [Anthropic — Claude Code Best Practices](https://code.claude.com/docs/en/best-practices); [Claude Code Workflow Optimizer — Pillar 1](claude-code-optimizer.md#pillar-1-context-and-configuration-discipline-highest-roi)

---

### 200-line CLAUDE.md target (Anthropic primary)

- **What it is:** Anthropic's official guidance: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." Past the threshold, instructions start getting ignored.
- **What's in it for you:** Instructions that actually get followed, rather than a long file Claude references but doesn't consistently act on.
- **What's hype:** n/a — this is a direct quote from the official docs. Not a heuristic; a documented threshold.
- **What to do:** Count your lines. If you're over, prune. Move non-universal instructions to path-scoped rules in `.claude/rules/`.
- **Source:** [Anthropic — Claude Code Memory](https://code.claude.com/docs/en/memory); [Claude Code Workflow Optimizer](claude-code-optimizer.md)

---

### Tool result truncation

- **What it is:** Piping long Bash outputs through `head` or `tail`, and instructing Claude via CLAUDE.md to read only relevant file sections rather than full files. The most immediate fix for tool-result spam.
- **What's in it for you:** Eliminates the most common immediate noise: two hundred lines of JSON from a command that only needed the first five.
- **What's hype:** n/a — practical tactic.
- **What to do:** Add to CLAUDE.md: "When running commands that produce long output, pipe through `head -50` unless I ask for the full output." One line.
- **Source:** [Why Is Claude Code So Noisy? — Source 1](claude-code-noise.md#source-1-tool-result-spam)

---

### Cache hit / prompt caching

- **What it is:** Anthropic's prompt caching feature — when the beginning of a prompt matches a prior request, the cached computation is reused, reducing latency and token cost for repeated prompt prefixes.
- **What's in it for you:** Lower cost and faster responses on workflows that repeatedly use the same large system prompt or CLAUDE.md.
- **What's hype:** Treating prompt caching as a significant architectural decision for most Claude Code users. It's Tier 2 optimization — relevant when you're paying close attention to token economics, not a first-session concern.
- **What to do:** Structure large CLAUDE.md files to put stable content at the top (where cache hits are most likely). Don't restructure your workflow around prompt caching until context discipline is already optimized.
- **Source:** [Anthropic — Prompt Caching](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)

---

### The four sources of noise

- **What it is:** Rick's taxonomy of Claude Code noise sources: (1) tool result spam (raw Bash output flooding the session), (2) subagent narration (reasoning traces from multi-step investigation), (3) status and reminder churn (TodoWrite updates in long sessions), (4) context bloat (the root cause that amplifies the other three).
- **What's in it for you:** Knowing which source is hurting you tells you which tactic to reach for. Treating all noise the same leads to the wrong fix.
- **What's hype:** n/a — observational taxonomy.
- **What to do:** Diagnose which source is dominant before adjusting settings. Context bloat is the root cause; fix it first before addressing surface symptoms.
- **Source:** [Why Is Claude Code So Noisy? — The four sources](claude-code-noise.md#the-four-sources-of-noise)

---

## Discoverability and protocols

*Full treatment: [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md)*

---

### robots.txt (agent-relevant interpretation)

- **What it is:** A decades-old standard text file at a site's root (`/robots.txt`) that tells crawlers what they can and can't access via User-agent rules. AI crawlers and shopping agents now read it; specifying known agent user-agents (GPTBot, ClaudeBot, Google-Extended) is the current practice.
- **What's in it for you:** Agent discovery and rate control without blocking legitimate AI traffic. Blanket-blocking is the wrong move — you lose discovery; agents route to competitors.
- **What's hype:** "The winning robots.txt strategy." There isn't one. It's plumbing — set it correctly and forget it.
- **What to do:** List known agent user-agents explicitly. Rate-limit at WAF level, don't block. See [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#robotstxt--the-agent-relevant-view) for current user-agent strings.
- **Source:** [robotstxt.org](https://www.robotstxt.org/); [Stripe — How to prepare for agentic commerce](https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide)

---

### llms.txt

- **What it is:** A proposed standard (Jeremy Howard / Answer.AI, September 2024) for a markdown file at a site's root (`/llms.txt`) that gives LLM consumers a curated index of a site's content — analogous to robots.txt for crawlers but for LLM inference-time use. Full content lives in `llms-full.txt`.
- **What's in it for you:** Low-cost signal for LLM-powered discovery tools. If your site has long-form guides or documentation, this file gives AI crawlers a curated path rather than trying to parse your full HTML.
- **What's hype:** "llms.txt is the new SEO." It's a proposal, not a ratified standard. No major LLM provider publicly commits to consuming it as canonical. Adoption is growing but uneven as of 2026.
- **What to do:** Deploy if you have curated content. Low cost, modest upside, no downside. Don't over-engineer.
- **Source:** [llmstxt.org](https://llmstxt.org/); [Answer.AI — llms.txt proposal (Sep 2024)](https://www.answer.ai/posts/2024-09-03-llmstxt.html); [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#llmstxt)

---

### /.well-known/ai-plugin.json (deprecated)

- **What it is:** OpenAI's manifest format for ChatGPT Plugins, launched March 2023 — a JSON file at `/.well-known/ai-plugin.json` that described plugin capabilities for the ChatGPT Plugins ecosystem.
- **What's in it for you:** Very little in 2026. ChatGPT Plugins were effectively deprecated April 2024 in favor of Custom GPTs, removing the primary consumer of this format.
- **What's hype:** Any claim that you need this file in 2026 is hype. Some agent ecosystems still read it as a discovery hint but it is no longer a load-bearing format.
- **What to do:** Ignore unless maintaining a legacy ChatGPT Plugin integration. If you have an existing plugin, migrate to a Custom GPT or MCP server.
- **Source:** [Stripe — How to prepare for agentic commerce](https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide) (names it as one of four files agents currently read, describing current agent behavior — not endorsing longevity); [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#wellknownai-pluginjson)

---

### openapi.yaml / openapi.json

- **What it is:** A machine-readable description of an API in the OpenAPI Specification format — YAML or JSON. Maintained by the OpenAPI Initiative (a Linux Foundation project). The de facto standard for describing REST APIs. Every major agentic ecosystem reads it: Custom GPT Actions, MCP server tool definitions, function-calling schemas are all derivable from or translatable to OpenAPI.
- **What's in it for you:** If you have a public API and want AI agents to be able to call it, you need a current, accurate OpenAPI spec at a stable URL. This is the load-bearing format.
- **What's hype:** n/a — solidly useful. The only legitimate critique is verbosity.
- **What to do:** Maintain a current spec. If you don't have one, modern frameworks emit it natively (FastAPI, NestJS, Spring, etc.). See [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#openapiyaml--openapijson).
- **Source:** [OpenAPI Initiative — What is OpenAPI](https://www.openapis.org/what-is-openapi); [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#openapiyaml--openapijson)

---

### MCP (Model Context Protocol)

- **What it is:** Anthropic's open protocol (announced November 2024, donated to the Agentic AI Foundation / Linux Foundation in December 2025) for connecting LLMs to tools, data, and prompts. The growing standard for the tool/data connection problem across the Anthropic ecosystem and beyond.
- **What's in it for you:** If you maintain a service AI agents should query or act on, expose an MCP server. Over 10,000 active servers and 97 million monthly SDK downloads as of knowledge cutoff.
- **What's hype:** "MCP is the universal standard." As of mid-2026, it's primarily Anthropic-ecosystem-centric for production use, though OpenAI has begun supporting it. OpenAI ecosystem still primarily uses function calling directly.
- **What to do:** Deploy MCP servers for data and tools your AI users actually need. Start read-only. Use official SDKs (Python, TypeScript). See [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#mcp-model-context-protocol) for depth.
- **Source:** [Anthropic — Model Context Protocol announcement](https://www.anthropic.com/news/model-context-protocol); [modelcontextprotocol.io](https://modelcontextprotocol.io/introduction)

---

### WebMCP

- **What it is:** An emerging spec (multiple active proposals) for running MCP-style tool calls in browser JavaScript contexts, so that in-page AI assistants can discover and invoke tools exposed by the webpage itself. The W3C Web Machine Learning Community Group is incubating a formal spec at `webmachinelearning.github.io/webmcp/`. A separate MCP-B implementation extends MCP specifically for browser tab contexts.
- **What's in it for you:** If you build webapps where you want users' in-page AI assistants to act on the page, WebMCP is the convergence path being developed. Today's alternative is custom JS bridges or vendor-specific extensions.
- **What's hype:** "WebMCP will replace MCP." No — they're complementary surfaces. WebMCP is the browser-side surface for what MCP is doing server-side. They solve different deployment contexts.
- **What to do:** Track the spec. Don't deploy production code against it yet unless explicitly experimenting. For production, MCP is the current standard.
- **Source:** [W3C WebMCP spec](https://webmachinelearning.github.io/webmcp/); [MCP-B (browser extension)](https://github.com/MiguelsPizza/WebMCP); [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#webmcp)

---

### A2A (Agent-to-Agent, Google)

- **What it is:** Google's open protocol for inter-agent communication, announced April 2025 at Google Cloud Next, donated to the Linux Foundation June 2025. Designed for letting one agent delegate tasks to another across vendor boundaries, with auth, state, and result handoff. Uses HTTP, Server-Sent Events, and JSON-RPC 2.0.
- **What's in it for you:** Relevant only if you're building multi-agent systems that need to cross trust or vendor boundaries. Inside a single vendor's ecosystem (Anthropic + your own subagents), you don't need A2A.
- **What's hype:** Positioning A2A as "the standard for agent interop." There is no ratified standard yet; A2A is one well-supported proposal. The Agent Communication Protocol (ACP) and others compete. A2A has 150+ organizational supporters but production adoption is early.
- **What to do:** Read about it. Don't deploy unless you have a concrete cross-vendor agent-delegation problem. See [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) for current patterns for intra-vendor multi-agent systems.
- **Source:** [Google Developers Blog — A2A announcement (Apr 2025)](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/); [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md#a2a-agent-to-agent-protocol)

---

### Function calling

- **What it is:** OpenAI-coined term (June 2023) for the model API capability of returning structured tool-invocation JSON — the model sees function definitions and outputs a JSON object with arguments for calling them. Now a generic capability across all major vendors. Anthropic calls it "tool use"; same underlying mechanism.
- **What's in it for you:** The underlying capability that everything else (MCP, ChatGPT Actions, custom agents) sits on top of. Every modern LLM API has it.
- **What's hype:** Positioning function calling as a strategy. It's a capability, not a strategy. The strategy decisions are about what tools to expose, how to define them, and what protocol to use for discovery and invocation.
- **What to do:** Use SDK function-calling primitives directly when building single-agent systems. Use MCP when you want a standardized discovery and invocation surface across multiple consumers.
- **Source:** [OpenAI — Function Calling announcement (Jun 2023)](https://openai.com/index/function-calling-and-other-api-updates/); [Anthropic — Tool Use overview](https://platform.claude.com/docs/en/docs/build-with-claude/tool-use/overview)

---

## Adjacent products and surfaces

---

### Anthropic Skills (product)

- **What it is:** Anthropic's named pattern (launched October 2025) for packaged, reusable Claude workflows — a folder with a `SKILL.md` file, optional scripts, and optional tool allowlists. The official term for Rung 2 on the prompts-to-agents ladder.
- **What's in it for you:** Reusable workflows without building a full agent. Load on demand via trigger phrases or slash commands.
- **What's hype:** n/a — a named and documented pattern with clear utility.
- **What to do:** This is the right default for most recurring workflows. Build skills before building agents.
- **Source:** [Anthropic — Equipping Agents for the Real World with Agent Skills (Oct 2025)](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

---

### OpenAI Custom GPTs

- **What it is:** OpenAI's parallel pattern to Anthropic Skills — a tailored GPT configuration with custom instructions, external knowledge, and allowed actions (including API calls via Actions). Launched November 2023. The successor to ChatGPT Plugins in the OpenAI ecosystem.
- **What's in it for you:** Similar packaging to Anthropic Skills but within the OpenAI ecosystem. If your audience is ChatGPT users, Custom GPTs are the distribution mechanism.
- **What's hype:** n/a in concept — same as Skills, different vendor.
- **What to do:** Use if your workflow lives in the OpenAI ecosystem. The underlying design pattern (packaged, reusable, one task per invocation) is the same as Skills.
- **Source:** [OpenAI — Introducing GPTs (Nov 2023)](https://openai.com/index/introducing-gpts/)

---

### claude.ai (the chat product)

- **What it is:** Anthropic's web and mobile chat interface — the consumer-facing Claude product at claude.ai. Separate from Claude Code (the CLI/IDE product) and Claude Desktop. Has its own permissions model via Integrations/Connectors settings.
- **What's in it for you:** The accessible entry point for Claude. No installation, no CLI. Appropriate for Rung 1 (prompts) and Rung 2 (via Projects and custom instructions) work.
- **What's hype:** n/a — a product, not an overclaim.
- **What to do:** Use for conversational work and quick tasks. Graduate to Claude Code when you need file system access, skill systems, and persistent project context.
- **Source:** [Anthropic — claude.ai](https://claude.ai)

---

### Claude Desktop / Cowork

- **What it is:** Anthropic's desktop application — available both as "Claude Desktop" and "Claude Cowork" depending on context. Has a workspace-level permission model for file system access, skill allowlists, and MCP server connections. Sits between claude.ai (no file access) and Claude Code (full CLI) in capability.
- **What's in it for you:** File system access and MCP connections without the CLI. A middle ground for non-developer users who need more than the web interface.
- **What's hype:** n/a — a product with a clear capability position.
- **What to do:** Use if you need file access and MCP integrations but don't want to work in a terminal.
- **Source:** [Claude Permissions Guide — Section 1](claude-permissions-guide.md#claude-desktop--cowork)

---

### Claude Code (the CLI / IDE)

- **What it is:** Anthropic's terminal-based agentic coding tool — the CLI and IDE extension that provides full file system access, skill systems, subagent dispatch, MCP integration, and the full permission model. The environment Rick's guides are written for.
- **What's in it for you:** The highest-capability Claude interface — full tool access, persistent project context, skill and agent systems, worktree fleets. The trade-off is terminal exposure and permission management.
- **What's hype:** n/a — a product with documented capabilities.
- **What to do:** Start with [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) if you're not a developer. Start with [Claude Code Workflow Optimizer](claude-code-optimizer.md) if you're already in it.
- **Source:** [Anthropic — Claude Code](https://code.claude.com)

---

### Replit / Cursor

- **What it is:** Replit is a cloud-based development environment with built-in AI coding assistance. Cursor is an IDE with deep AI integration, including MCP server support. Both are practitioner-ecosystem tools that sit adjacent to Claude Code.
- **What's in it for you:** Replit is lower-friction for beginners (no local setup). Cursor is popular in the developer community for IDE-native AI editing. Named here as context — Rick's guides are focused on Claude Code, not these tools.
- **What's hype:** n/a in definition context — these are specific products with specific audiences.
- **What to do:** Cursor supports MCP servers natively, making it a legitimate deployment target for MCP-based tooling. Replit is useful for quick experiments without local environment management.
- **Source:** n/a — named here as practitioner-ecosystem context.

---

## Cultural shorthand and framings

---

### Vibe coding (Karpathy)

- **What it is:** Andrej Karpathy's term (February 2025) for fully committing to what the model produces — operating on feel, forgetting the code even exists, not debugging or reading code directly. "You fully give in to the vibes, embrace exponentials, and forget that the code even exists."
- **What's in it for you:** Permission to not understand every line of code you approve. Also a useful warning: vibe coding works best when you can see what you're vibing with (Claude Code's transparent output) rather than when abstraction hides mistakes.
- **What's hype:** The implication that vibe coding is an advanced or reckless practice. It describes what most practitioners actually do after they've built pattern recognition. The risk is real — not debugging code means not catching mistakes — but the transparency of Claude Code's output is the mitigation.
- **What to do:** Vibe code with Claude Code (where you can see the output) rather than with abstraction tools (where mistakes hide). Build the pattern recognition that lets you know when something looks obviously wrong without parsing every line.
- **Source:** [Karpathy — X/Twitter (Feb 2025)](https://x.com/karpathy/status/1886192184808149383); [Claude Code for Non-Developers — Section 2](claude-code-for-non-developers.md#section-2-why-claude-code-specifically-the-matrix-section)

---

### Software 3.0 (Karpathy)

- **What it is:** Andrej Karpathy's framing from his June 2025 YC AI Startup School keynote: LLMs are a new kind of computer, and you program them in English. Software 1.0 = explicit programming. Software 2.0 = neural networks trained on data. Software 3.0 = LLMs programmed in natural language.
- **What's in it for you:** The mental model that you're programming a new kind of system, not just talking to a chatbot. This reframes what it means to be non-technical in a Claude Code context.
- **What's hype:** Using "Software 3.0" as a reason to skip understanding what you're building. The framing lowers the barrier to entry; it doesn't eliminate the need for judgment about what Claude proposes.
- **What to do:** Internalize the framing: you are writing programs in English. That raises the standard for what you write, not just what you prompt.
- **Source:** [Karpathy — YC AI Startup School keynote (Jun 2025)](https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again); [Claude Code for Non-Developers — Section 1](claude-code-for-non-developers.md#section-1-the-mindset-shift)

---

### "The Matrix" framing (Rick's voice)

- **What it is:** Rick's metaphor for Claude Code's transparency: you see the code directly — file edits, Bash outputs, diffs — without abstraction layers hiding what's happening. Like Neo learning to read the Matrix: you don't need to understand every character, but you learn to recognize when something looks wrong.
- **What's in it for you:** The counterintuitive insight that transparent tools are better for non-developers than abstraction tools, past a certain scale. Abstraction tools hide Claude's mistakes; Claude Code surfaces them.
- **What's hype:** n/a — a metaphor, not a technical claim.
- **What to do:** Accept the transparency as a feature, not a bug. Build the pattern recognition that lets you catch obvious errors without needing to understand implementations.
- **Source:** [Claude Code for Non-Developers — Section 2](claude-code-for-non-developers.md#section-2-why-claude-code-specifically-the-matrix-section)

---

### "Team of programmers" framing (Rick's voice)

- **What it is:** Rick's framing for the shift from single-session chat to Claude Code with skills and subagents: instead of talking to one assistant one exchange at a time, you're directing a team — one agent drafts while another researches while a third verifies.
- **What's in it for you:** The mental model that makes multi-agent systems make sense for non-developers. The interface is still you typing; the leverage is categorically different.
- **What's hype:** n/a — a framing device, not a technical claim.
- **What to do:** Use this framing to evaluate whether you're using the tool at its ceiling. If every session is a one-on-one chat, you're probably leaving leverage on the table.
- **Source:** [Claude Code for Non-Developers — Section 1](claude-code-for-non-developers.md#section-1-the-mindset-shift)

---

## Measurement and benchmarks

*Each entry is one-line definition + primary source. These are evaluation datasets used to measure LLM and agent performance.*

---

### SWE-bench / SWE-bench Verified

- **What it is:** A benchmark of real GitHub issues requiring code changes — models are evaluated on whether they can correctly resolve software engineering tasks in actual repositories. SWE-bench Verified is a human-validated subset with confirmed solvable issues.
- **Source:** [SWE-bench paper (arXiv 2310.06770)](https://arxiv.org/abs/2310.06770); [swe-bench.github.io](https://www.swebench.com/)

---

### HumanEval

- **What it is:** OpenAI's benchmark of 164 Python programming problems evaluated by functional correctness — tests whether generated code produces correct outputs, not just syntactically valid code.
- **Source:** [Chen et al. — Evaluating Large Language Models Trained on Code (arXiv 2107.03374)](https://arxiv.org/abs/2107.03374)

---

### HotpotQA

- **What it is:** A multi-hop question-answering dataset requiring reasoning across multiple Wikipedia passages to answer questions — tests whether models can connect information across sources rather than retrieve single facts.
- **Source:** [Yang et al. — HotpotQA (arXiv 1809.09600)](https://arxiv.org/abs/1809.09600)

---

### ALFWorld

- **What it is:** A multi-step text-based household task benchmark (learning tasks in language grounded in simulated physical environments) — used in ReAct paper to demonstrate agent decision-making performance. ReAct achieved +34% success rate over imitation and RL baselines.
- **Source:** [Shridhar et al. — ALFWorld (arXiv 2010.03768)](https://arxiv.org/abs/2010.03768); cited in [Yao et al. — ReAct (arXiv 2210.03629)](https://arxiv.org/abs/2210.03629)

---

### τ-bench (tau-bench)

- **What it is:** A benchmark for evaluating tool-augmented language model agents on realistic tasks requiring multi-turn tool use — designed to measure agent reliability and task completion in practical tool-calling scenarios.
- **Source:** [τ-bench paper (arXiv 2406.12045)](https://arxiv.org/abs/2406.12045)

---

### BFCL (Berkeley Function Calling Leaderboard)

- **What it is:** UC Berkeley's ongoing leaderboard evaluating models on function/tool calling accuracy across multiple categories (simple, parallel, nested) — the primary ongoing benchmark for comparing models on the tool-use capability underlying agents.
- **Source:** [Berkeley Function Calling Leaderboard](https://gorilla.cs.berkeley.edu/leaderboard.html)

---

## Sources & Attribution

**Tier 1 — Primary sources with measured results:**

- Anthropic — *How we built our multi-agent research system* (90.2% improvement, fan-out thresholds): https://www.anthropic.com/engineering/multi-agent-research-system
- Shunyu Yao et al. — *ReAct: Synergizing Reasoning and Acting in Language Models* (ICLR 2023): https://arxiv.org/abs/2210.03629
- Andrew Ng / DeepLearning.AI — *Agentic Design Patterns* (HumanEval benchmark data: GPT-3.5 agentic 95.1% vs. zero-shot 48.1%): https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance/
- OpenAI — *Function Calling and other API updates* (June 2023): https://openai.com/index/function-calling-and-other-api-updates/
- Stripe — *How to prepare for agentic commerce: A technical field guide*: https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide

**Tier 2 — Trusted primary documentation:**

- Anthropic — *Building Effective Agents* (Dec 2024): https://www.anthropic.com/engineering/building-effective-agents
- Anthropic — *Equipping Agents for the Real World with Agent Skills* (Oct 2025): https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- Anthropic — *Claude Code Best Practices*: https://code.claude.com/docs/en/best-practices
- Anthropic — *Claude Code Memory / CLAUDE.md*: https://code.claude.com/docs/en/memory
- Anthropic — *Claude Code Permissions*: https://code.claude.com/docs/en/permissions
- Anthropic — *Claude Code Settings*: https://code.claude.com/docs/en/settings
- Anthropic — *Claude Code Subagents*: https://code.claude.com/docs/en/sub-agents
- Anthropic — *Model Context Protocol announcement* (Nov 2024): https://www.anthropic.com/news/model-context-protocol
- Anthropic — *Prompt Caching*: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching
- Anthropic — *Tool Use overview*: https://platform.claude.com/docs/en/docs/build-with-claude/tool-use/overview
- GitHub Engineering — *Multi-agent workflows often fail. Here's how to engineer ones that don't*: https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/
- Google Developers Blog — *Announcing the Agent2Agent Protocol (A2A)* (Apr 2025): https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
- Jeremy Howard / Answer.AI — *A proposal to standardize on /llms.txt* (Sep 2024): https://www.answer.ai/posts/2024-09-03-llmstxt.html
- llmstxt.org — official specification: https://llmstxt.org/
- Model Context Protocol — specification: https://modelcontextprotocol.io/introduction
- OpenAPI Initiative — *What is OpenAPI*: https://www.openapis.org/what-is-openapi
- W3C Web Machine Learning Community Group — *WebMCP specification*: https://webmachinelearning.github.io/webmcp/

**Tier 3 — Practitioner perspectives (supporting role):**

- Andrej Karpathy — *Software Is Changing (Again)*, YC AI Startup School (Jun 2025): https://www.youtube.com/watch?v=LCEmiRjPEtQ
- Andrej Karpathy — vibe coding coinage (Feb 2025): https://x.com/karpathy/status/1886192184808149383
- Lilian Weng — *LLM Powered Autonomous Agents* (Jun 2023): https://lilianweng.github.io/posts/2023-06-23-agent/
- Walden Yan / Cognition — *Don't Build Multi-Agents* (Jun 2025): https://cognition.ai/blog/dont-build-multi-agents

**Related work in this series:** [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md), [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md), [Claude Code Workflow Optimizer](claude-code-optimizer.md), [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md), [Why Is Claude Code So Noisy?](claude-code-noise.md), [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md), [Claude Code for Non-Developers: Your First Session](claude-code-non-developers-first-session.md), [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md)

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
