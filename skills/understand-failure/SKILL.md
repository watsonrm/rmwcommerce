---
name: understand-failure
description: Run a rigorous, adversarial Five Whys on any failure or wrong-outcome — software, systems, or AI reasoning/verification errors. Build a branching cause tree (not a linear chain), validate every link counterfactually, then dispatch an independent skeptic to break the analysis before trusting it. Trigger when the user says "understand why this failed", "why did this break", "root-cause this", "5-whys this", "do a postmortem on this", "why did you reach that conclusion", "why did the agent assert that", or hands over an incident, outage, broken job, wrong conclusion, or mis-verified fact and asks for the cause.
---

# understand-failure

Produce a high-quality root-cause analysis of a failure. The output is a branching, counterfactually-validated cause tree with system-targeted remediations — deliberately *not* a single linear "root cause." This is diagnosis, not a fix: produce the analysis; only implement remediations if the user then asks.

This skill is the runnable companion to the guide ["Bringing Five Whys into the Agentic Era."](https://github.com/watsonrm/rmwcommerce/blob/main/guides/bringing-five-whys-into-the-agentic-era.md) The naive Five Whys is unreliable for software because it forces a linear chain onto a non-linear event and stops at an arbitrary depth. This skill does the opposite in five specific ways.

## When to use this skill

Trigger on phrases like:
- "understand why X failed" / "why did this break / stop working"
- "root-cause this" / "5-whys this" / "do a postmortem"
- "what actually caused this outage"
- "why did you reach that conclusion" / "why did the agent assert that" / "why did you say X was false"
- "understand why I got the wrong answer" / "self-RCA" / "why did the verification step fail"
- a handed-over incident, stack trace, broken pipeline, wrong conclusion, or mis-verified fact

Scale to the failure: a one-file bug gets a small tree and an inline skeptic pass; a real outage or reasoning error gets the full treatment with a *dispatched* skeptic agent and a grounded timeline.

## The method (six moves)

### 1. Establish the facts before any cause
Write down what was *observed*, separate from what is *inferred*:
- the symptom in concrete terms (error, wrong output, missing data, downtime window) with timestamps;
- the blast radius — what was and was not affected;
- the timeline, in order;
- what was *normal* at the time (real failures are usually triggered by minor, near-normal events activating long-standing latent factors — don't hunt for a dramatic trigger).

If you're missing facts, say so and mark those branches `[UNVERIFIED]`. Never paper a gap with a plausible cause.

### 2. Frame it blamelessly, out loud
State the assumption at the top: *everyone acted reasonably given what they knew, saw, and were incentivized to do at the time. You can fix systems and processes; you cannot fix people.* When a branch heads toward "person P erred," that's the signal to go deeper: what made P's action look correct in the moment? What did the tooling invite? What was missing?

### 3. Ask "how," not "why"
"Why did you do that?" invites a defense and slides toward blame. "How did this make sense given what you saw?" elicits the *conditions* — which are the thing you can actually change.

### 4. Branch, don't chain
At every node ask: "what were *all* the conditions necessary for this — what else had to be true?" Recurse on each. A node usually has 2–4 contributing conditions, not one. Build a cause **tree**. Tag each node by layer:
- **[PROXIMATE]** — the immediate trigger.
- **[CONTRIBUTING]** — conditions that had to co-exist for the trigger to do harm.
- **[SYSTEMIC/LATENT]** — long-standing design/process factors that made the system vulnerable. These are worth fixing. A tree with no systemic nodes hasn't gone deep enough.

### 5. Validate every link counterfactually
For each edge ask: **"If this single factor had not been present, everything else equal, would the failure have been prevented?"**
- Yes → sufficient on its own on this path; a strong lever.
- No, but it was needed → necessary-but-not-sufficient → a genuine co-contributor; keep it and its siblings (this is the case a linear chain throws away).
- No, and removing it changes nothing → noise → prune it.
Write the verdict next to each surviving node.

### 6. Remediate the system, not the people
For each surviving systemic node, propose a fix that is system/process-level (a guard, a test, a default, an alert, a removed footgun), owner-assignable, and linked to the node it removes. "Be more careful" is not a remediation. Prefer fixes that neutralize a factor sitting under multiple branches.

## The adversarial step (do not skip)

Do not trust your own first tree. Run an **independent skeptic** whose only job is to break it. For a substantial incident, dispatch a *separate* agent given only the tree + the facts (not your reasoning). For a small one, switch hats explicitly. The skeptic must return five things:

1. **The missing branch** — name a contributing cause absent from the tree, or argue convincingly it's complete.
2. **The blame smell** — does any leaf reduce to "human error," "should have been more careful," or a name? If so, push it deeper.
3. **The single-cause smell** — has the tree collapsed into one dominant chain with the rest as garnish? If only one branch has depth, branching failed.
4. **The counterfactual challenge** — take the two nodes the analyst is most confident about and argue the *opposite* (that removing them wouldn't have prevented the failure). If it holds, the node is mis-rated.
5. **The stopping-rule challenge** — where did each branch stop, and is the stop principled (hit an actionable system lever) or arbitrary (ran out of ideas / hit five)?

Fold the findings back in. If the skeptic found a real missing branch, the analysis isn't done — recurse. A skeptic that returns "nothing wrong" on the first try is suspect; make it name a candidate missing branch regardless.

## Output format

```
FAILURE: <one-line symptom, concrete>
Blast radius: <what was / wasn't affected>
Frame: blameless — everyone acted reasonably on what they knew.

TIMELINE
  <ts> …

CAUSE TREE  (✓ passed counterfactual · ⚠ necessary-not-sufficient · ✂ pruned)
● <symptom>
├─ [PROXIMATE] <trigger>  ✓
│   ├─ [CONTRIBUTING] <condition A>  ⚠
│   │   └─ [SYSTEMIC] <latent factor>  ✓  → R1
│   └─ [CONTRIBUTING] <condition B>  ⚠
│       └─ [SYSTEMIC] <latent factor>  ✓  → R2
└─ [CONTRIBUTING] <parallel branch a chain would miss>  ✓
    └─ [SYSTEMIC] <latent factor>  ✓  → R3

SKEPTIC PASS
  Missing branch / blame / single-cause / counterfactual / stopping-rule: …
  → changes folded in: …

REMEDIATIONS (system/process-level, owner-assignable)
  R1 — <action> · addresses <node> · owner <?>
  …  ← note any that sit under multiple branches (highest leverage)

CONFIDENCE & GAPS
  <per branch; what's [UNVERIFIED] and what evidence would close it>
```

## Verification (run before delivering)

The analysis must pass all of these; fix any failure before presenting:
1. **No single-chain** — 2+ branches with real depth and 1+ systemic node.
2. **No banned terminal** — no leaf is "human error," "should have been more careful," a name, or "couldn't find it / not found therefore false/fabricated." Absence of evidence in a search is not evidence of absence; cap at "unverified — flagging for the human" and search where the fact would *live* before escalating.
3. **Every link validated** — each surviving node has a counterfactual verdict.
4. **Skeptic actually ran** — and found a gap (folded in) or affirmatively argued completeness.
5. **Remediations are system-level + owner-assignable** and each cites the node it removes.
6. **Evidence-grounded** — every proximate/timeline claim traces to something observed; ungrounded inferences are marked `[UNVERIFIED]`.
7. **Provenance checked for reasoning/verification failures** — if the failure was a wrong conclusion or mis-verified fact, confirm the source record (proposal, deal note, source artifact) was checked before any label was applied.

State in one line which checks passed.

## Notes

- "Root cause" is a request, not a constraint. If the user asks for "the root cause," give the tree and name the highest-leverage systemic factor(s) — while being honest that the failure was jointly caused.
- Don't fix during diagnosis. Produce the tree; wait for a go before changing anything.
- For the architecture behind dispatching the skeptic as a reliable subagent (typed returns, verification, scoping), see the guide [Multi-Agent Fan-Out and Verification](https://github.com/watsonrm/rmwcommerce/blob/main/multi-agent-fan-out-and-verification.md).
