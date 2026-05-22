---
name: prompts-to-agents-ladder
description: Apply Rick Watson's 4-rung prompt-to-agent ladder to a user's workflow, identify which rung they're on, flag over-climbing, recommend the highest-leverage next move. Trigger when user says "prompts to agents ladder", "which rung am I on", "should this be a skill or an agent", "am I over-engineering this agent", "do I need a multi-agent system", or "apply the ladder".
---

## When to use this skill

Invoke when the user is deciding whether to build, repackage, or refactor an AI workflow and needs to know the right level of abstraction. Specific cues:

- They describe a recurring prompt and ask if they should "make it a skill" or "turn it into an agent"
- They have a working agent and it feels fragile, slow, or over-built
- They're considering multi-agent fan-out and aren't sure it's warranted
- They paste a workflow description and ask which rung fits

## The four rungs

- **Rung 1 — Prompt.** A single instruction in a chat session. No reuse artifact. Right for one-offs and for thinking out loud. Climb when the same setup text is pasted more than twice.
- **Rung 2 — Skill.** A packaged, reusable instruction set with optional tool allowlist and scripts. Single invocation, no loop, human reviews each output. Climb only when the task needs sequential tool calls with decisions between them, must run unattended, or needs its own verification logic.
- **Rung 3 — Agent.** Skill plus decision loop plus tools plus verification. The model reasons, acts, observes, and decides the next step. Climb only when there is genuine fan-out, genuine sub-task specialization, or a single context window can't hold the state.
- **Rung 4 — Multi-agent system.** Thin orchestrator dispatching to specialized subagents with typed return contracts. Not a destination. Only correct once Rung 3 has been outgrown for a specific reason.

## Where to spend your time (decision table)

| # | Situation | Right move | Why |
| :-- | :--- | :--- | :--- |
| 1 | You paste the same prompt setup more than twice | Package it as a skill (Rung 2) | Reuse without the context tax. Biggest gain, lowest effort. |
| 2 | You have a skill but it needs multiple tool calls in sequence, with decisions between them | Graduate to an agent (Rung 3) | Skills are single-invocation. Once the model needs to reason about intermediate results, you need a loop. |
| 3 | You have an agent but you keep adding tools and it's getting fragile | Refine the skill spec and tool allowlist before adding more tools | Complexity at Rung 3 compounds. Narrower scope is almost always the fix, not more tooling. |
| 4 | You have a working single agent and the work has clear natural fan-out | Consider multi-agent (Rung 4) | See the companion guide. Don't start here. |

## How to apply

1. Ask the user to describe their current workflow in concrete terms: what they're building, how they invoke it today, what's breaking or feeling over-built. If they pasted enough already, skip the question.
2. Identify the rung they are currently on. Map their description to one of the four rungs above. State the rung explicitly and quote the one signal that places them there.
3. Check for over-climbing. Apply the three failure tests:
   - Can you describe what the agent does without using the word "decides"? If yes, it's a skill in agent's clothing.
   - Have they done this task fewer than five times, or does context vary materially each time? If yes, stay at Rung 1.
   - Do they have real fan-out, real specialization, or a context overflow problem? If none, Rung 4 is overhead.
4. Recommend exactly one move. The single highest-leverage change — usually "finish Rung 2 properly" rather than climbing. Be specific: name the artifact to build, modify, or delete.
5. Cite the relevant deeper guide. For Rung 1–2 practitioner tactics inside Claude Code, point to the `claude-code-optimizer` skill or the article at https://github.com/watsonrm/rmwcommerce/blob/main/claude-code-optimizer.md. For Rung 4 architecture, point to the `multi-agent-fan-out` skill or https://github.com/watsonrm/rmwcommerce/blob/main/multi-agent-fan-out-and-verification.md. For everything else, link the source article.

## Anti-patterns to flag

- Building an agent loop that runs one or two iterations and returns. The "decisions" between steps are trivial; the verification step checks things that weren't at risk. This is a skill.
- Building a full skill with scripts, trigger phrase, and tool allowlist for a task done twice a year or one where context varies materially each time. Stay at Rung 1.
- Reaching for multi-agent because the architecture sounds impressive. Without fan-out, specialization, or a context window problem, the orchestrator is overhead without payoff.
- Adding more tools to a fragile Rung 3 agent instead of narrowing its scope. Complexity at Rung 3 compounds — narrower spec beats more tooling.
- Treating Rung 4 as a destination to aim for. It's the right tool only for workflows that have demonstrably outgrown a single well-configured agent.

## Output shape

Return to the user:
1. **Current rung:** one sentence with the signal that places them there.
2. **Over-climbing check:** pass/fail on each of the three failure tests, one line each.
3. **The one move:** a single concrete recommendation, named artifact, named change.
4. **Deeper reading:** one link to the relevant companion guide.

---

Source article: https://github.com/watsonrm/rmwcommerce/blob/main/the-prompts-to-agents-ladder.md

Packaging credit: Matt Ezyk first proposed and prototyped the SKILL.md form of this guide.
