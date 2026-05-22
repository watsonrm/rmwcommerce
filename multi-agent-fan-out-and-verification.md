# Multi-Agent Fan-Out and Verification

**How to structure Claude agent systems that scale without silently breaking — architecture from Anthropic, protocol from GitHub.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. This guide synthesizes patterns from Anthropic's engineering blog and GitHub's engineering blog — quoted material is the property of its respective owners and used under fair use with attribution. See [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

If you're building or refactoring a multi-agent Claude system, applying these patterns will:

- Eliminate the class of bug where a subagent returns bad output and the orchestrator propagates it silently across every downstream step
- Cut orchestrator context size by 60–80% on workflows that currently return full prose blobs from each agent
- Make partial failures debuggable without re-running the whole workflow from scratch
- Give you a concrete phasing strategy so you don't have to rewrite everything at once

### Where to spend your time, in priority order

Most readers should implement the first two before anything else. They prevent the failure modes that make multi-agent systems harder to trust than single-agent ones.

| # | Practice | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | **Typed return contracts** — every agent returns a defined schema, not freeform prose | Failures surface at the boundary instead of poisoning downstream state. This is the single highest-leverage change for any existing system. | 1–2 hrs per agent |
| **2** | **Intermediate-state logging** — every run writes input, output, and log to a known path | Without this, partial failures are unrecoverable. Silent failures look like successes. This is the idempotency and debuggability foundation. | 2–3 hrs once, then copy the pattern |
| **3** | **Thin orchestrator / fat subagents** — orchestrator plans and aggregates; subagents execute | Reduces noise in the orchestrator context. Scoped subagents are easier to test and replace. | Refactor by skill |
| **4** | **Fan-out by complexity** — match parallelism to the task, not to a fixed number | Explicit fan-out caps prevent runaway token spend on simple queries and ensure hard queries get enough coverage. | 1 hr (policy + prompt) |
| **5** | **Action schemas for write agents** — discriminated union of legal outcomes | Prevents write agents from inventing a fourth option. Tight contracts on destructive operations. | 30 min per write agent |
| **6** | **Full Anthropic-style 10+ subagent fan-out** — complex research with many parallel specialists | Real gains for deep research workflows, but most consulting/operations systems don't need this level. Start with items 1–3. | Days |

---

## How to use this

Open a fresh Claude Code session. Paste this guide along with one or two of your existing agent spec files (`.claude/agents/` definitions or skill playbooks). Then run:

> Review my agent specs against this guide. For each agent: (1) identify whether it returns a typed schema or freeform prose, (2) flag any that could silently fail without logging intermediate state, and (3) tell me which typed contract from the examples here most closely matches what this agent should be returning. Produce a prioritized list of contracts to add, starting with the highest-reuse agents.

The output is a punch list of schema gaps, ordered by the agents your orchestrators call most often.

---

## Where this comes from

Two engineering blog posts, published independently, describe patterns that compose.

Anthropic published a detailed account of how they built their internal multi-agent research system. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) The central insight is architectural: keep the orchestrator thin, give subagents complete scoped briefs, have subagents write heavy outputs to disk and return lightweight references. This is the shape of the system.

GitHub Engineering published a separate analysis of why multi-agent workflows fail in practice and how to prevent it. ([source](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/)) Their diagnosis: agents fail not because the model is bad but because the contracts between agents are loose. Natural language instructions produce inconsistent returns; freeform outputs propagate errors downstream. The fix is typed schemas enforced at every boundary.

Applied together to a real ~20-skill consulting and media workflow (the system behind this repo's tooling), both patterns held. The failure modes that surfaced were: brand-styling regressions in document-generation agents that fixed themselves in one place and re-broke in another; silent failures in scheduled cron-style agents that left no trace of what happened; raw API JSON from external services flooding the orchestrator context and degrading output quality mid-session. Every one of those is addressed by the patterns below.

---

## Pillar 1: Typed return contracts

This is the highest-ROI change for most existing systems, and the one most often skipped.

The problem is that natural language is inherently ambiguous. When a subagent returns a paragraph summarizing what it found, the orchestrator has to parse prose under uncertainty. Field names drift. Optional data gets included or excluded depending on what the agent thought was relevant that run. One malformed return poisons every step that follows.

GitHub's framing is direct: *"Natural language is messy. Typed schemas make it reliable."* ([source](https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/)) Treat agent collaboration the way you'd treat an API contract between two engineering teams: define the schema up front, validate at the boundary, fail fast when the contract is violated rather than passing bad state downstream.

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

The Anthropic system took this further: subagents write their full output to the filesystem and return only a lightweight reference. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) The orchestrator sees `{path, 1-line summary}`. It only reads the full output if it needs to.

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

The Anthropic system runs research that can take dozens of tool calls across many subagents. GitHub's framing treats agents like distributed systems, not chat flows. The shared assumption is that things will fail — network errors, API rate limits, partial data, model outputs that don't match the expected schema. Design for it up front rather than adding recovery logic after the first production incident.

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

---

## Pillar 4: Orchestrator shape

Once the contract and logging foundations are in place, the orchestrator architecture follows naturally.

The Anthropic principle is: thin orchestrator, fat subagents. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) The lead agent plans, dispatches, and aggregates references. It does not execute. Each subagent gets a complete, scoped brief — objective, output format, tools allowed, token budget. The orchestrator never does the work it could delegate.

This has a direct effect on context quality. An orchestrator that receives typed reference rows from eight subagents stays coherent through a full session. An orchestrator that receives prose summaries, raw API JSON, and partial outputs starts degrading somewhere around the third agent return.

### Fan-out by complexity

Anthropic built explicit scaling thresholds into their system: simple fact-finding uses one agent with a handful of tool calls; comparisons need two to four subagents; complex research deploys ten or more with divided responsibilities. ([source](https://www.anthropic.com/engineering/multi-agent-research-system))

The practical version for most systems is simpler: identify the workflows where you're doing sequential work that could run in parallel. A meeting-prep workflow that looks up eight attendees sequentially is doing eight network round-trips one at a time. Eight parallel subagents, each returning a typed CRM lookup result, finish in roughly the time of one.

The fan-out pattern only makes sense after Pillars 1 and 2 are in place. Parallelism with loose contracts amplifies noise; parallelism with typed schemas amplifies precision.

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

---

## Sources & Attribution

Both source articles are live as of 2026-05-22 and were verified before publication.

**Primary sources:**

- Anthropic Engineering — *How we built our multi-agent research system*: https://www.anthropic.com/engineering/multi-agent-research-system
- GitHub Engineering — *Multi-agent workflows often fail. Here's how to engineer ones that don't.*: https://github.blog/ai-and-ml/generative-ai/multi-agent-workflows-often-fail-heres-how-to-engineer-ones-that-dont/

**Attribution:** The Anthropic article covers the architectural layer (orchestrator shape, fan-out thresholds, filesystem-as-state, subagent specialization). The GitHub article covers the protocol layer (typed schemas, discriminated-union action schemas, design-for-failure with logged intermediate state). The synthesis, ranking, implementation notes, phasing strategy, and TypeScript-style schemas above are Rick Watson's original work, validated against a production multi-agent consulting and media workflow.

**Compilation, ranking, and commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or a sharper pattern to add? Open an issue or PR.
