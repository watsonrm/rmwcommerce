# Multi-Agent Fan-Out and Verification

**How to structure Claude agent systems that scale without silently breaking — architecture, theory, and the strongest counterargument.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. This guide synthesizes patterns from Anthropic's engineering blog, GitHub's engineering blog, and published research by Lilian Weng, Shunyu Yao et al., and Walden Yan — quoted material is the property of its respective owners and used under fair use with attribution. See [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

*Not sure you need a multi-agent system yet? Start with [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — it covers when to use a prompt, a skill, or a single agent before committing to this architecture.*

---

## TL;DR — what's in it for you

The strongest empirical case for multi-agent architecture: Anthropic tested a system using Claude Opus 4 as the lead agent with Claude Sonnet 4 subagents against a single-agent Claude Opus 4 on their internal research evaluation. The multi-agent system outperformed by **90.2%**. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) That result was on a parallelizable research workload — identifying board members of S&P 500 IT companies, a breadth-first task that benefits from parallel investigation. For sequential decision-composition work, the gains are different and the risks are higher (covered in the counterargument below).

If you're building or refactoring a multi-agent Claude system, applying these patterns will:

- Eliminate the class of bug where a subagent returns bad output and the orchestrator propagates it silently across every downstream step
- Reduce orchestrator context size substantially on workflows that currently return full prose blobs from each agent
- Make partial failures debuggable without re-running the whole workflow from scratch
- Give you a concrete phasing strategy so you don't have to rewrite everything at once

### Where to spend your time, in priority order

Most readers should implement the first two before anything else. They prevent the failure modes that make multi-agent systems harder to trust than single-agent ones — and they're the same defenses that address Cognition's core critique of the architecture (see "The case against fan-out" below).

| # | Practice | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | **Typed return contracts** — every agent returns a defined schema, not freeform prose | Failures surface at the boundary instead of poisoning downstream state. This is also the primary defense against subagent decision-composition failures. The single highest-leverage change for any existing system. | 1–2 hrs per agent |
| **2** | **Intermediate-state logging** — every run writes input, output, and log to a known path | Without this, partial failures are unrecoverable. Silent failures look like successes. This is the idempotency and debuggability foundation. | 2–3 hrs once, then copy the pattern |
| **3** | **Thin orchestrator / fat subagents** — orchestrator plans and aggregates; subagents execute | Reduces noise in the orchestrator context. Scoped subagents are easier to test and replace. Matches Anthropic's orchestrator-workers composition pattern. | Refactor by skill |
| **4** | **Fan-out by complexity** — match parallelism to the task, not to a fixed number | Explicit fan-out caps prevent runaway token spend on simple queries. Anthropic's system uses 1 agent for simple fact-finding, 2–4 for comparisons, 10+ for complex research. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) Use fan-out only for parallelizable reads, not for decisions that need to compose. | 1 hr (policy + prompt) |
| **5** | **Action schemas for write agents** — discriminated union of legal outcomes | Prevents write agents from inventing a fourth option. Tight contracts on destructive operations. | 30 min per write agent |
| **6** | **Full Anthropic-style 10+ subagent fan-out** — complex research with many parallel specialists | Real gains for deep research workflows: Anthropic's system cuts research time by up to 90% for complex queries using parallel tool calling. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) Most consulting/operations systems don't need this level to start. Begin with items 1–3. | Days |

---

## How to use this

Open a fresh Claude Code session. Paste this guide along with one or two of your existing agent spec files (`.claude/agents/` definitions or skill playbooks). Then run:

> Review my agent specs against this guide. For each agent: (1) identify whether it returns a typed schema or freeform prose, (2) flag any that could silently fail without logging intermediate state, and (3) tell me which typed contract from the examples here most closely matches what this agent should be returning. Produce a prioritized list of contracts to add, starting with the highest-reuse agents.

The output is a punch list of schema gaps, ordered by the agents your orchestrators call most often.

---

## Where this comes from

Four engineering sources and two research papers, converging on the same structural conclusions.

Anthropic published two pieces that form the theoretical and applied foundation. The first — "Building Effective Agents" by Erik Schluntz and Barry Zhang (Dec 2024) — defines the workflow-vs-agent distinction and catalogs five core composition patterns: prompt chaining, routing, parallelization, orchestrator-workers, and evaluator-optimizer. ([source](https://www.anthropic.com/engineering/building-effective-agents)) The orchestrator-workers pattern is the direct theoretical ancestor of the fan-out architecture in this guide: a central LLM dynamically breaks down unpredictable tasks and delegates to worker LLMs, with subtask decomposition determined at runtime rather than pre-defined. The second Anthropic piece covers their internal multi-agent research system — a production implementation of these patterns. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) Its headline result: a multi-agent system with Claude Opus 4 as lead agent and Claude Sonnet 4 subagents outperformed single-agent Claude Opus 4 by **90.2%** on their internal research evaluation. The central architectural principle: keep the orchestrator thin, give subagents complete scoped briefs, have subagents write heavy outputs to disk and return lightweight references.

GitHub Engineering published a separate analysis of why multi-agent workflows fail in practice. ([source](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/)) Their diagnosis: agents fail not because the model is bad but because the contracts between agents are loose. Natural language instructions produce inconsistent returns; freeform outputs propagate errors downstream. The fix is typed schemas enforced at every boundary.

OpenAI's counterpart guide (April 2025) covers much of the same ground with a different emphasis. ([source](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)) Where Anthropic leans on composition patterns, OpenAI leans on guardrails as a layered defense: *"Think of guardrails as a layered defense mechanism. While a single one is unlikely to provide sufficient protection, using multiple, specialized guardrails together creates more resilient agents."* Both sources recommend starting with a single agent and adding multi-agent complexity only when prompts become difficult to scale or tool overlap becomes a real problem.

Cognition's "Don't Build Multi-Agents" (Walden Yan, June 2025) offers the strongest counter-position. ([source](https://cognition.ai/blog/dont-build-multi-agents)) It's worth reading before committing to the architecture. That counterargument gets its own section below.

Lilian Weng's "LLM Powered Autonomous Agents" (June 2023) provides the foundational taxonomy — planning, memory, tool use — that every later agent discussion inherits. ([source](https://lilianweng.github.io/posts/2023-06-23-agent/)) Yao et al.'s ReAct paper (ICLR 2023) describes the reason-act-observe loop that underlies what a single agent does inside that architecture, and demonstrated that the approach outperformed imitation and reinforcement learning baselines by an absolute success rate of 34% on ALFWorld and 10% on WebShop in decision-making tasks. ([source](https://arxiv.org/abs/2210.03629))

Applied together to a real ~20-skill consulting and media workflow (the system behind this repo's tooling), both architecture patterns held. The failure modes that surfaced were: brand-styling regressions in document-generation agents that fixed themselves in one place and re-broke in another; silent failures in scheduled cron-style agents that left no trace of what happened; raw API JSON from external services flooding the orchestrator context and degrading output quality mid-session. Every one of those is addressed by the patterns below.

---

## The building blocks: what agents actually do

Before getting into architecture, it helps to have a shared vocabulary for what an individual agent is doing at runtime.

Weng's taxonomy (2023) breaks an LLM-powered agent into three components: planning, memory, and tool use. ([source](https://lilianweng.github.io/posts/2023-06-23-agent/)) Planning covers how the agent decomposes a complex task into manageable subgoals and how it reflects on its own progress. Memory covers what it can see in context (short-term) versus what it retrieves from external stores (long-term). Tool use covers how it calls external APIs or runs code to act on the world.

The ReAct paper (Yao et al., 2022) shows how these components work together in the moment: the agent interleaves reasoning traces with concrete actions in a loop. ([source](https://arxiv.org/abs/2210.03629)) The reasoning trace updates the agent's internal model of the situation; the action updates the external environment or retrieves new information; the result feeds the next reasoning step. This reason-act-observe loop is what each individual subagent is doing while the orchestrator waits for its typed return.

The multi-agent architectures in the rest of this guide are coordination layers on top of this loop — ways of running multiple instances of it in parallel and aggregating the results.

---

## The case against fan-out

Read this before building. Cognition (the team behind Devin) published a direct argument against multi-agent architectures in June 2025. ([source](https://cognition.ai/blog/dont-build-multi-agents)) It's worth engaging with seriously, not dismissing.

Walden Yan's core claim: multi-agent systems are fragile because decision-making ends up too dispersed and context can't be shared thoroughly enough between agents. When agents work in parallel on subdivided tasks, each subagent makes implicit decisions the orchestrator can't see. Those decisions can conflict. A final agent tasked with combining the outputs inherits inconsistencies it has no way to resolve. As Yan writes: *"Actions carry implicit decisions, and conflicting decisions carry bad results."*

Yan's proposed default is a single-threaded linear agent that maintains continuous context through its full task. For longer tasks, he suggests an LLM trained to compress conversation history into key decisions rather than spawning parallel subagents.

This critique is correct for a specific class of problems: workloads where subagents need to make decisions that compose into a unified output. If you're asking four subagents to each write a section of a document in a consistent style, you're asking them to make implicit formatting, tone, and scoping decisions that the orchestrator can't adjudicate after the fact. The architecture works against you.

This is where the asymmetry between the two arguments matters. Cognition's critique is rhetorical and applies specifically to decision-composition workloads — tasks where subagent outputs need to merge into a coherent whole. Anthropic's 90.2% improvement is measured on parallelizable research workloads — breadth-first queries where subagents independently fetch discrete data points and return typed results. Both can be simultaneously true. The gap is about task structure, not model capability.

Fan-out works well under the conditions Anthropic tested: parallelizable read operations with clear typed returns, where each subagent fetches or synthesizes a discrete piece of data and hands it back to the orchestrator, which makes all the decisions. Meeting prep is a practical example: eight parallel CRM lookups, each returning a typed `CRMLookupResult`, finish faster than eight sequential ones and the orchestrator can reason over all eight simultaneously. The subagents aren't making decisions; they're retrieving data.

The resolution: use fan-out for reads with typed returns, not for decisions that need to compose. Typed contracts (Pillar 1 below) are the mechanism that keeps this boundary sharp. If a subagent's return includes anything that could be interpreted differently by downstream steps, you're already in decision-composition territory and fan-out is working against you.

Karpathy's "autonomy slider" framing adds another dimension here: the more autonomous you make an agent, the more verification you owe it. ([source](https://www.youtube.com/watch?v=LCEmiRjPEtQ)) Increasing fan-out is increasing autonomy — you're asking more agents to make more decisions without human review. The answer isn't to avoid autonomy; it's to match the verification investment to the autonomy level. More fan-out agents → more rigorous typed contracts → more explicit logging → more specific recovery logic.

---

## Pillar 1: Typed return contracts

This is the highest-ROI change for most existing systems, and the one most often skipped.

The problem is that natural language is inherently ambiguous. When a subagent returns a paragraph summarizing what it found, the orchestrator has to parse prose under uncertainty. Field names drift. Optional data gets included or excluded depending on what the agent thought was relevant that run. One malformed return poisons every step that follows.

GitHub's framing is direct: *"Natural language is messy. Typed schemas make it reliable."* ([source](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/)) Treat agent collaboration the way you'd treat an API contract between two engineering teams: define the schema up front, validate at the boundary, fail fast when the contract is violated rather than passing bad state downstream.

Typed contracts are also the primary defense against the decision-composition failure mode Cognition describes. When every subagent return is a validated schema, the orchestrator can see exactly what it received and make decisions based on structured data rather than inferred prose. The implicit decision problem doesn't disappear, but it becomes detectable at the boundary.

In Claude Code's Agent tool, the practical convention is: the agent emits a JSON block as the last content of its return, and the orchestrator parses it. The typed schemas live in a shared contracts file that both the subagent spec and the orchestrator reference.

### Read-specialist contracts

Read-only specialists return structured data. Here are concrete schemas for common specialist types:

```ts
type EngagementContextResult = {
  path: string;                          // disk path to full snapshot
  engagement: string;                    // "ClientA" | "ClientB" | ...
  open_asks: number;
  recent_decisions: number;              // last 14 days
  last_touchpoint_iso: string | null;
  files_read: string[];                  // relative paths actually read
  files_missing: string[];               // expected but not present
};

type CRMLookupResult = {
  path: string;
  found: boolean;
  person_id: number | null;
  deals: number;
  prior_meetings: number;
  last_met_iso: string | null;
  summary: string;                       // 80 chars max: "Met 3x, last 2026-04-12"
};

type MessagingSearchResult = {
  path: string;
  n_hits: number;
  top_hit_iso: string | null;
  needs_reply: boolean;
};

type PhotoLookupResult = {
  url: string | null;
  source: "company" | "crunchbase" | "press" | "podcast" | "conference" | null;
  verified: boolean;                     // HTTP 200 confirmed
};

type WebResearchResult = {
  path: string;
  headline: string;                      // 100 chars max
  recent_press_count: number;
};

type CalendarReaderResult = {
  path: string;
  events: Array<{
    event_id: string;
    title: string;
    start_iso: string;
    end_iso: string;
    branch: "A" | "B" | "C" | "D" | "E" | null;
    engagement: string | null;
    attendee_count: number;
    external_attendee_count: number;
    needs_prep: boolean;
    is_recurring: boolean;
    location_kind: "remote" | "off_site" | "none";
  }>;
};
```

These schemas produce small, precise returns. An orchestrator prepping eight meetings holds twenty-four reference rows — not twenty-four prose summaries. Context stays usable for the full session rather than filling up after the first two meetings.

### The noise fix, in concrete terms

Orchestrator context overflow is the multi-agent extension of the same problem that context discipline addresses at the single-user level — see [The Claude Code Workflow Optimizer](claude-code-optimizer.md)'s Pillar 1 for the single-session version of this constraint, and [Why Is Claude Code So Noisy?](claude-code-noise.md) for the full treatment of noise sources and filtering tactics at the session level. At the multi-agent level, the mechanism shifts from `/compact` to typed returns and artifact offloading, but the underlying dynamic is the same: bloated context degrades output quality.

Anthropic's system took this further: subagents write their full output to the filesystem and return only a lightweight reference. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) The orchestrator sees `{path, 1-line summary}`. It only reads the full output if it needs to. This is the "artifact system" — specialized agents create outputs that persist independently, then pass lightweight references back to the coordinator. The result is substantially reduced token overhead and lower information loss in multi-stage processing.

For a web research agent, the return might be `{path: "/tmp/agent-runs/run123/web-research/inv-001/output.json", headline: "Filed Chapter 11, Feb 2026"}`. The orchestrator can make routing decisions from the headline alone. It pulls the full report only if something downstream actually needs it.

---

## Pillar 2: Action schemas for write agents

Read specialists return data. Write specialists make decisions. These need stricter contracts.

The pattern is a discriminated union: enumerate every legal outcome the agent is allowed to return. If the situation doesn't fit one of them, the agent should return a failure — not invent a new variant.

GitHub's formulation: *"Vague intent breaks agents. Action schemas make it clear."* ([source](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/)) Their example uses a four-way union for a triage agent. The agent picks one. No fifth option.

Applied to common write operations:

```ts
type ValidatorResult =
  | { type: "ok" }
  | { type: "fixed"; what: ("prep_event" | "running_notes" | "brand_styling")[] }
  | { type: "flagged"; reasons: string[]; missing_artifact: "prep_event" | "running_notes" | "drive_doc" | "free_slot" };

type DocumentWriterResult =
  | { type: "created"; doc_id: string; url: string }
  | { type: "updated"; doc_id: string; url: string; sections_added: number }
  | { type: "skipped_idempotent"; doc_id: string; url: string; reason: "already_current" }
  | { type: "failed"; reason: "trashed" | "permission_denied" | "api_error" | "target_unresolvable" | "empty_content"; message: string };

type CalendarWriterResult =
  | { type: "created"; event_id: string }
  | { type: "updated"; event_id: string }
  | { type: "skipped_no_free_slot"; meeting_event_id: string; minutes_available: number };

type TriageResolverResult = {
  cleared: Array<{ envelope: string; pattern: string }>;
  ambiguous: Array<{ envelope: string; default_recommendation: string }>;
  patterns_added: string[];              // new routing patterns the agent suggests; orchestrator decides whether to apply
};
```

The `ValidatorResult` example is the sharpest illustration. Three legal outcomes: it's fine, it fixed something (and named what), or it couldn't fix something (and named why). There is no fourth option. This kills an entire class of validation bugs where the agent reports "looks good" while silently skipping a check it couldn't perform.

The `DocumentWriterResult` shows the idempotency contract built into the schema: `skipped_idempotent` is a first-class return, not an exception. The orchestrator can see "already current" and move on without re-running.

Write specialists do not auto-retry. They return a failure union variant and let the orchestrator decide whether to retry, escalate, or skip.

---

## Pillar 3: Design for failure

Anthropic's system runs research that can take dozens of tool calls across many subagents. GitHub's framing treats agents like distributed systems, not chat flows. The shared assumption is that things will fail — network errors, API rate limits, partial data, model outputs that don't match the expected schema. Design for it up front rather than adding recovery logic after the first production incident.

Karpathy's autonomy-slider framing sharpens this: the more autonomous the system, the more systematic the failure design needs to be. ([source](https://www.youtube.com/watch?v=LCEmiRjPEtQ)) A system that works most of the time in a demo is not a system that works reliably in production. As you increase agent autonomy (more parallel subagents, longer task chains, fewer human checkpoints), the verification overhead grows in proportion. The verification-first principle that anchors [The Claude Code Workflow Optimizer](claude-code-optimizer.md) at the single-user level — write the test before the code, define success before execution — scales directly to multi-agent: every fan-out step adds verification debt, and that debt compounds faster than it does in a single session. Logging, typed contracts, and idempotent writes are the mechanisms that let you increase autonomy without proportionally increasing risk.

Multi-agent permissions compound — every subagent inherits its own approval surface, and an orchestrator dispatching ten subagents is generating ten independent permission footprints. See [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md) for the strategy of managing that surface without losing the safety checkpoints that make autonomous operation trustworthy.

Two rules, both non-negotiable.

**Every write is idempotent.** A document-writing agent searches for an existing document before creating. A calendar-event agent updates in place. A synthesis agent checks a tracker before re-processing a source. Re-running an agent on the same input never duplicates state. This matters both for reliability (you can safely retry failed runs) and for debugging (you can replay any run without side effects).

**Every run logs intermediate state.** Every agent invocation writes to a known path:

```
/tmp/agent-runs/<run_id>/<agent_name>/<invocation_id>/
  input.json    # what the orchestrator passed in
  output.json   # the typed return
  log.txt       # tool calls, durations, retry attempts
  error.txt     # only on failure
```

The `run_id` comes from the orchestrator and is the same for all agents in a single workflow execution. The `invocation_id` is unique per agent dispatch. Together they make every step in a multi-agent workflow individually traceable.

This pattern catches the failure mode that shows up most often in practice: a scheduled or automated agent ran, produced no visible output, and left no evidence of what happened. Without intermediate-state logging, the only diagnostic is to re-run and hope the failure repeats. With it, you read the log.

OpenAI's guide adds a complementary guardrails perspective: treat safety and reliability checks as a layered stack rather than a single gate. ([source](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)) LLM-based classifiers, rules-based filters, and human escalation paths form independent layers — no single layer is sufficient on its own. Applied to multi-agent systems, this means the orchestrator doesn't rely solely on the subagent's typed return to know if something went wrong; it also has its own output validation and escalation logic.

---

## Pillar 4: Orchestrator shape

Once the contract and logging foundations are in place, the orchestrator architecture follows naturally.

Anthropic names this the **orchestrator-workers pattern**: a central LLM dynamically breaks down unpredictable tasks and delegates to worker LLMs, with the subtask decomposition determined at runtime. ([source](https://www.anthropic.com/engineering/building-effective-agents)) This is distinct from simple parallelization — the orchestrator isn't just splitting a known task across workers; it's deciding what the tasks are. The principle that follows is: thin orchestrator, fat subagents. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) The lead agent plans, dispatches, and aggregates references. It does not execute. Each subagent gets a complete, scoped brief — objective, output format, tools allowed, token budget. The orchestrator never does the work it could delegate.

OpenAI describes two variants on this at scale. ([source](https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf)) In the **manager pattern**, a central agent controls workflow execution and maintains user context, delegating to specialist agents through tool calls. In the **decentralized pattern**, agents operate as peers, transferring control to one another based on specialization without a central coordinator. The manager pattern maps more directly to the orchestrator-workers architecture and is the better default for most systems; decentralized is appropriate when no single agent needs to maintain oversight across the full workflow.

This has a direct effect on context quality. An orchestrator that receives typed reference rows from eight subagents stays coherent through a full session. An orchestrator that receives prose summaries, raw API JSON, and partial outputs starts degrading somewhere around the third agent return.

### Fan-out by complexity

Anthropic built explicit scaling thresholds into their system based on query complexity: simple fact-finding uses one agent with a handful of tool calls; direct comparisons need two to four subagents with ten to fifteen calls each; complex research deploys ten or more subagents with clearly divided responsibilities. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) They also report that parallel tool calling across this architecture reduced research time by up to 90% for complex queries, and that token usage alone explains 80% of performance variance on their benchmarks — making token spend the primary lever to watch.

The practical version for most systems is simpler: identify the workflows where you're doing sequential work that could run in parallel. A meeting-prep workflow that looks up eight attendees sequentially is doing eight network round-trips one at a time. Eight parallel subagents, each returning a typed CRM lookup result, finish in roughly the time of one.

The fan-out pattern only makes sense after Pillars 1 and 2 are in place. Parallelism with loose contracts amplifies noise; parallelism with typed schemas amplifies precision. And per the Cognition critique: fan-out only for reads with typed returns, not for decisions that compose.

### Subagent specialization

Per-subagent specialization matters for a different reason than performance: it makes each agent independently testable and replaceable.

When validation logic lives in every orchestrator, a change to the validation rule requires touching every orchestrator. When it lives in one validator agent, you change it once. The same applies to document formatting, photo lookup, CRM queries — any concern that currently appears in more than one skill or orchestrator is a candidate for extraction.

Here's a catalog of specialist types that appear across common consulting and operations workflows. Each has a clear scope, a tool allowlist, and a typed return:

| Subagent type | Scope | Returns to orchestrator |
| :--- | :--- | :--- |
| Calendar reader | Pull events in a time window; classify by engagement | `CalendarReaderResult` with lightweight event array |
| CRM lookup | Per-contact: activities, deals, last interaction | `CRMLookupResult` with path + summary |
| Messaging search | Per query, top N results | `MessagingSearchResult` with path + hit count |
| Engagement context reader | Per engagement: docs, backlog, recent decisions | `EngagementContextResult` with path + open counts |
| Photo lookup | Per person, verified URL | `PhotoLookupResult` |
| Web research | Per target, recent news + profile | `WebResearchResult` with path + headline |
| Document writer | Take assembled brief → write/update doc with brand | `DocumentWriterResult` |
| Calendar event writer | Take prep card → write/update calendar event | `CalendarWriterResult` |
| Validator | Per artifact: check both exist + brand is correct | `ValidatorResult` |
| Source synthesizer | One source → wiki updates | Typed result with paths touched + item counts |
| Triage resolver | Apply routing rules to inbox | `TriageResolverResult` |

---

## Migration: how to phase this in without breaking what works

Don't rewrite everything at once. The phasing below is ordered so each step validates a piece of the contract convention before the next one inherits it.

### Phase 1 — Foundation (build in this order)

1. **Validator agent** — smallest, clearest scope, with the most concrete existing contract (most skills already have a validation step you can extract). Establishes the typed-return and action-schema conventions for everything else.

2. **Document writer** — single point of truth for brand styling, idempotent by contract. If document-formatting regressions are a recurring problem, this agent eliminates the class of bug.

3. **Engagement context reader** — first read-only specialist. Validates that the typed-return convention works for reads too. Straightforward to extract from most orchestrators.

4. **CRM lookup** — highest-reuse read specialist. Once extracted, every orchestrator that currently does its own CRM calls delegates to this agent instead.

After Phase 1, the contract and logging conventions are proven. Every subsequent agent inherits them.

### Phase 2 — Specialist set for the highest-frequency workflow

5. Messaging search agent — eliminates raw API JSON in orchestrator context
6. Photo lookup agent
7. Web research agent
8. Calendar reader
9. Calendar event writer

After Phase 2, your highest-frequency workflow (often meeting prep or daily briefing) should shrink from a single large monolithic skill to a thin orchestrator plus nine typed specialists. The orchestrator holds reference rows, not full prose.

### Phase 3 — Heavier synthesis workflows

10. Source synthesizer — extracted from summary/synthesis loops
11. Triage resolver — extracted from inbox routing

### Rollback safety

Keep your current skill files as `-legacy` variants for one week after the new orchestrator goes live. If the new orchestrator misbehaves, the fallback is a one-line change. After a week without regression, delete the legacy files.

### Metrics worth tracking

- Tokens consumed per workflow run (before vs. after)
- Wall-clock time per workflow
- Contract violations caught at agent boundaries (should be nonzero in early days, trending to zero)
- Cache hit rate on the orchestrator context

---

## Implementation notes

A few practical questions that come up when applying these patterns in Claude Code:

**Where typed schemas live.** The contracts file should be a shared reference both subagent definitions and orchestrators can read. In practice, this means one canonical contracts file (e.g., `agent_contracts/` or similar) with the typed schemas, plus orchestrators and subagent specs that reference it explicitly. Schema validation can be handled with Pydantic or Zod if you want automated enforcement at the boundary.

**Token budget enforcement.** Anthropic's system has explicit per-subagent budgets. Claude Code subagents don't have a hard token cap — enforce it in the prompt ("max N tool calls", "max N words in return") and validate post-hoc via the intermediate-state log. Contract violations and oversized returns are both visible in the log.

**Intermediate-state log durability.** `/tmp/agent-runs/` is local and wipes on reboot, which is fine for interactive debugging. For automated or scheduled workflows, you'll want a persistent location so the log survives session restarts. A git-ignored directory in your project root works; so does any mounted persistent storage.

**How Claude Code serializes agent returns.** The Agent tool returns a string, not a typed struct. The convention is: the agent emits a JSON block as the last content of its response, and the orchestrator parses it. The typed schemas above describe the shape of that JSON. The orchestrator should validate the return against the expected schema and re-dispatch with the violation as feedback if it doesn't match — once, then escalate rather than retry indefinitely.

**Starting point vs. multi-agent.** Both Anthropic and OpenAI recommend starting with a single agent and adding fan-out only when a single agent's prompt becomes hard to maintain or tool overlap becomes a real problem. If you're asking yourself whether you need multi-agent, you probably don't yet. Build the typed contracts and logging infrastructure first; that work pays off regardless of whether you end up with two agents or twenty.

---

## Where to go next

Climbing back down: if your multi-agent system feels over-engineered, [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) helps decide which rung is actually right for the work you're doing. Going deeper on single-user practice: [The Claude Code Workflow Optimizer](claude-code-optimizer.md).

---

## Want the runnable form?

The operational core of this guide is packaged as a Claude Code skill: [`skills/multi-agent-fan-out/`](skills/multi-agent-fan-out/). Drop that folder into `~/.claude/skills/` and Claude will load it on demand when the trigger phrases in the SKILL.md frontmatter match what you're asking.

---

## Sources & Attribution

All source URLs verified live as of 2026-05-22.

**Tier 1 — Primary sources with measured results:**

- Anthropic Engineering — *How we built our multi-agent research system* (source for the 90.2% improvement, fan-out thresholds, 90% speed gain from parallel tool calling, and the artifact/filesystem pattern): https://www.anthropic.com/engineering/multi-agent-research-system
- Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao — *ReAct: Synergizing Reasoning and Acting in Language Models*, arXiv 2210.03629 (Oct 2022, ICLR 2023) (source for +34% ALFWorld, +10% WebShop success rates over imitation/RL baselines): https://arxiv.org/abs/2210.03629

**Tier 2 — Trusted primary documentation:**

- Erik Schluntz & Barry Zhang / Anthropic Engineering — *Building Effective Agents* (Dec 2024, source for the five composition patterns and orchestrator-workers definition): https://www.anthropic.com/engineering/building-effective-agents
- GitHub Engineering — *Multi-agent workflows often fail. Here's how to engineer ones that don't.* (source for typed schemas and action-schema framing): https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/
- OpenAI — *A Practical Guide to Building Agents* (Apr 2025, source for guardrails-as-layers and manager/decentralized pattern taxonomy): https://cdn.openai.com/business-guides-and-resources/a-practical-guide-to-building-agents.pdf
- Lilian Weng — *LLM Powered Autonomous Agents* (Jun 2023, foundational planning/memory/tool-use taxonomy): https://lilianweng.github.io/posts/2023-06-23-agent/

**Tier 3 — Practitioner perspectives (supporting role only):**

- Walden Yan / Cognition — *Don't Build Multi-Agents* (Jun 2025, strongest counterargument; critique is valid for decision-composition workloads): https://cognition.ai/blog/dont-build-multi-agents
- Andrej Karpathy — *Software Is Changing (Again)*, YC AI Startup School (Jun 2025, autonomy-slider framing for calibrating verification overhead): https://www.youtube.com/watch?v=LCEmiRjPEtQ

**Attribution:** The Anthropic multi-agent research system article provides both the primary empirical evidence (90.2% improvement) and the applied architecture (filesystem-as-state, subagent specialization, fan-out thresholds). The "Building Effective Agents" article provides the theoretical composition patterns. GitHub's article provides the protocol layer (typed schemas, discriminated-union action schemas). OpenAI adds the guardrails-layers framing and manager/decentralized taxonomy. Weng's taxonomy gives the vocabulary for what individual agents do. ReAct provides the benchmark-verified description of the reason-act-observe loop. Karpathy's autonomy-slider is the risk-calibration frame for "design for failure." Cognition's critique is the strongest counterargument and is engaged with directly rather than dismissed. The synthesis, ranking, implementation notes, phasing strategy, TypeScript-style schemas, and the resolution of the Cognition critique against Anthropic's measured data are Rick Watson's original work, validated against a production multi-agent consulting and media workflow.

**Compilation, ranking, and commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or a sharper pattern to add? Open an issue or PR.
