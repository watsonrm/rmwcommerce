---
name: multi-agent-fan-out
description: Design or audit a multi-agent system with proper fan-out, typed returns, verification, and idempotency before building. Trigger when user says "build a multi-agent system", "architect multiple agents", "fan out to subagents", "orchestrator and subagents", "verify agent output", "should I split this skill", or "parallelize my agents".
---

# Multi-Agent Fan-Out and Verification

Help the user design a multi-agent system, or audit one they have already built. Most users asking this question have not actually hit the wall that justifies fan-out — your first job is to check that, then guide the design.

## When to use this skill

Trigger on phrases like:
- "I want to build a multi-agent system"
- "how do I architect multiple agents"
- "should I fan out / parallelize agents"
- "how do I verify agent output"
- "orchestrator vs subagent design"
- "my skill does too many things, should I split it"

## Precondition check (run this first, every time)

Before any architecture work, confirm the user is actually at Rung 4. Ask them:

1. Is the current bottleneck "one prompt is doing too much" or "sequential reads are too slow"? If neither, fan-out is over-engineering — stop and point them at the `prompts-to-agents-ladder` skill to revisit Rung 2/3.
2. Have they tried a single agent with good tools and a tight prompt? If not, send them back to Rung 3 first.
3. Is the task parallelizable reads, or decision composition? Fan-out works for reads with typed returns. It does not work when subagent outputs must merge into a single coherent decision or document — that path produces conflicting decisions and bad results.

If the user fails the check, say so directly and recommend the cheaper rung. Do not proceed.

## Core patterns (and the failure each prevents)

1. **Typed return contracts** — every subagent returns a defined schema, not prose. Prevents silent drift and downstream parsing failures. Example: a CRM lookup returns `{path, found, person_id, deals, last_met_iso, summary}`, never a paragraph.
2. **Action schemas for writes** — write agents return discriminated unions of enumerated outcomes (e.g. `{type: "ok"} | {type: "fixed", what: [...]} | {type: "flagged", reasons: [...]}`). Prevents agents inventing outcomes the orchestrator cannot handle.
3. **Intermediate-state logging** — every invocation writes input, output, and log to `/tmp/agent-runs/<run_id>/<agent_name>/<invocation_id>/`. Prevents unrecoverable silent partial failures and makes runs debuggable.
4. **Thin orchestrator, fat subagents** — orchestrator plans and aggregates; subagents execute fully within a scoped brief. Prevents orchestrator context bloat and keeps composition decisions in one place.
5. **Idempotent writes** — re-running a subagent must not duplicate state. Document writers search for an existing doc first; calendar agents update in place. Prevents corruption on retry.

## Design procedure

Walk the user through these steps in order. Do not skip ahead.

1. **Identify the natural fan-out axis.** What is the user actually doing N times in sequence today? Per-row, per-attendee, per-source — name it explicitly. If you cannot name one axis, there is no fan-out.
2. **List specialists vs. orchestrator responsibilities.** Write two columns. Orchestrator: planning, dispatch, aggregation. Specialists: one job each, scoped brief, typed return. If a specialist needs to call another specialist, collapse them or hoist the call to the orchestrator.
3. **Define typed return shapes per specialist.** Write the schema before writing the prompt. Reads return reference rows. Writes return discriminated unions.
4. **Place verification gates.** Decide where the orchestrator validates returns before aggregating. Required after every write specialist. Recommended after any read specialist whose output drives a downstream branch.
5. **Decide the idempotency strategy per write.** For each write specialist, document: how does it detect "already done"? Search by id, search by path, dedupe key, or update-in-place — pick one and write it into the specialist brief.
6. **Decide retries and timeouts.** Per specialist: max retries, timeout, and the failure mode the orchestrator must handle (e.g. return `{type: "flagged"}` on timeout, never silently drop).
7. **Decide context-passing shape.** Orchestrator passes briefs in, holds reference rows out. Never pass full transcripts between subagents. Never share mutable state — only typed returns.
8. **Phase the rollout.** Extract one specialist at a time, keep the legacy path as `-legacy` fallback for a week, delete after no regressions. Do not rewrite the whole system in one cut.

## Anti-patterns and smells

Flag any of these in the user's design and push back:

- **Freeform prose returns** — natural-language outputs between agents. Replace with a schema.
- **Parallel decision composition** — fan-out where subagent outputs must merge into a unified judgment or document. Collapse to a single agent.
- **Agents calling other agents in chains** — A calls B calls C. Hoist the dispatch to the orchestrator.
- **No verification gate after writes** — orchestrator trusts whatever the write agent returned. Add a typed-outcome check.
- **Non-idempotent writes** — no dedupe key, no "search first" step, no update-in-place rule. Re-runs will corrupt state.
- **Missing intermediate-state logs** — scheduled or background agents that produce no trace. Unrecoverable on failure.
- **Fan-out without an aggregation step** — N subagents run, results scattered, nothing reduces them. Add the aggregator.

## Output to the user

After walking the procedure, give the user:
- The one-line fan-out axis
- The orchestrator/specialist split as a two-column list
- A typed-return schema per specialist
- The verification gate placements
- The idempotency strategy per write
- The phase-1 specialist to extract first (pick the single highest-reuse read)

If the user resists the precondition check or pushes for fan-out on a decision-composition task, hold the line and recommend a single agent.

---

Source article: https://github.com/watsonrm/rmwcommerce/blob/main/multi-agent-fan-out-and-verification.md
