---
name: building-ai-agent-workforce
description: Audit an AI agent or agent system against six dimensions — organizational design, containment, escalation, trust calibration, measurement, and production-readiness — and produce a prioritized fix list. Trigger when user says "audit this agent workforce", "production-transition checklist for this agent", "six-dimension agent audit", "is this agent production-ready", "agent workforce review", or "agent system audit".
---

# Building an AI-Agent Workforce — Live Audit

Six-dimension audit for AI agents and agent systems. The research and reasoning behind this framework are in [guides/building-ai-agent-workforce.md](../../guides/building-ai-agent-workforce.md).

## When to use this skill

Invoke when the user:
- Has an agent (or multi-agent system) they're about to deploy or already running
- Wants to move an agent from prototype to production
- Suspects an agent has a containment, escalation, or trust calibration gap
- Says "is this production-ready?" or "what would break first?"

Works for single agents, orchestrator-worker systems, and always-on daemons.

## Step 0: intake

Ask the user to describe the agent:
- What does it do? (scope)
- What tools does it have? (exact tool names if known)
- What stage is it at? (prototype, staging, deployed)
- What's the last thing that went wrong, if anything?

If the user has already provided this, skip asking and proceed to Step 1.

## Six-dimension audit — apply in order

### Dimension 1: Organizational design

Ask: "Does the agent have a job description — scope, tools, risk level per tool, escalation line, escalation triggers, quality gates, and autonomy level?"

Smell: the agent's role is described in prose or a system prompt, but there is no explicit list of what it may and may not do.

Fix: draft a one-page job description with these fields:
- Scope (one sentence: what it does, what it explicitly does not do)
- Tool inventory (name, risk tier: LOW / MEDIUM / HIGH)
- Reporting and escalation line (who gets paged and when)
- Escalation triggers (retry threshold; irreversible/external/financial action)
- Quality gates (what it checks before calling a task done)
- Autonomy level (read-only / reversible-writes / full — and the reliability bar to move up)

Also ask: "Is there a Working Conventions document — numbered, citable rules with RFC-2119 keywords, each with a stable id?" Example rule: `RISK-01: The agent MUST escalate any irreversible or external action rather than execute it`. If not, draft three starter rules covering the highest-risk behaviors.

### Dimension 2: Containment

Ask: "Which high-risk capabilities are absent from the tool surface entirely — not just discouraged in the prompt?"

Smell: the system prompt says "do not send email" but the agent's runtime includes an email-send tool. Prompt instructions are the weakest link.

Fix: enumerate every tool the agent currently has. For each HIGH-risk tool (irreversible, external, financial, shell), ask: "Can this be removed from the runtime and replaced with a draft-and-escalate path?" Curate the tool surface so containment is environmental, not behavioral.

Secondary check: "Does the agent run with least-privilege credentials?" If not, name which permissions to narrow.

### Dimension 3: Escalation and failure handling

Ask: "What happens when the agent hits an error? Does it retry indefinitely, silently continue, or halt and hand off?"

Smell: failure paths are not explicit — errors are swallowed, the agent continues on wrong assumptions, or work silently disappears.

Fix: verify two things:
1. The agent halts and hands off on any irreversible or external action (never silently continues).
2. Failed actions leave work in a durable queue under a claim that retries — a teammate's message is never dropped.

Also check for honest degradation: when a tool fails, the agent should report it plainly and hand off, not fabricate success or a commitment it has no mechanism to fulfill.

### Dimension 4: Trust calibration

Ask: "Is trust in this agent calibrated to its demonstrated reliability, or maximized by default?"

Smell: the team either over-relies (rubber-stamps approval prompts, doesn't question outputs) or under-relies (re-does the agent's work manually, routes around it). Both are documented failure modes.

Fix: surface uncertainty honestly — the agent should ask a clarifying question on detected ambiguity rather than produce a confident wrong answer. Grant autonomy progressively as the agent demonstrates reliability, not by default. Ask: "What is the agent's reliability history, and does its current autonomy level match it?"

### Dimension 5: Measurement

Ask: "How do you know the agent is working? What dimensions are you measuring?"

Smell: "it seems to work" or a single accuracy metric.

Fix: measure at least: cost per task, latency, task completion rate, policy-adherence rate (does it escalate when it should?), and reliability (uptime / no-drop rate). Set internal SLA targets for each.

Also verify: "Do you have a living battery of user-voiced test scenarios?" These are messages phrased the way an actual teammate would write them, with assertions on what the agent should do. Run them before every change. Unit tests in the API's voice miss the integration bugs that matter.

### Dimension 6: Production-readiness checklist

Work through this checklist in order. Stop at the first item that fails and fix it before continuing.

- [ ] **Fail closed at startup.** The agent refuses to act until every credential and config is verifiably present. A missing secret is a hard stop, not a silent fallback.
- [ ] **No half-configured deploys can act.** Going live is a deliberate human step — mint the secret, register events, prove the sandbox — each leaving an audit trail.
- [ ] **Execution model understood.** If running on a serverless platform: background tasks scheduled after returning a response may silently freeze (CPU is throttled to near-zero when idle; idle-shutdown fires with no clean error). Work that must complete runs inline, within the request, with idempotency to handle platform retries.
- [ ] **Daemons monitored by heartbeat.** If the agent is an always-on loop: health is monitored by presence-of-heartbeat (the loop self-reports on its own clock), not by exit code (a daemon that never exits never produces one). Absence of a beat is the failure signal.
- [ ] **Cost routing in place.** If there are both free/local and metered/cloud paths: a lightweight heartbeat routes to the free engine when available; the metered path tiers models by task difficulty; stable context is cached.
- [ ] **User-voiced test battery exists.** Messages phrased the way an actual teammate would send them. Run it before every change. Check for: natural-phrasing variants of high-risk triggers, allowlist gaps in outbound channels, deploy quirks that silently disable writes.
- [ ] **Working Conventions document exists.** Numbered, citable rules with stable ids. At minimum: a comms rule, a risk-escalation rule, an activation rule.
- [ ] **Blast radius documented.** Every authorization change (especially enabling reversible writes) has a written blast radius note: who else gains access, what they can do, reviewed before activation.

## Diagnostic procedure

1. Collect intake (Step 0).
2. Work through dimensions 1–5 in order. Stop at the first gap.
3. For each gap: name the exact fix — not a category, but the specific action.
4. Run the production-readiness checklist (Dimension 6) only after dimensions 1–5 pass.
5. Report a prioritized fix list: what to fix first, what can wait, and why the ordering is correct.

## Check your work

After the audit:
- Every gap was named and assigned a fix (not just flagged)
- The fix is grounded in the agent's actual tool surface and deployment state, not assumptions
- The production-readiness checklist has explicit pass/fail for each item, not "likely passes"
