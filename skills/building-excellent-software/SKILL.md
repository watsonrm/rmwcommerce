---
name: building-excellent-software
description: Apply the excellent-software checklist to a Claude-built artifact and surface the highest-leverage gap. Trigger when user says "apply the excellent software checklist", "where am I on the dogfood-to-production ladder", "red-team what I just built", "is this production-grade", "audit my build", "what's missing before I ship", or "excellent software check".
---

# Building Excellent Software — Live Coach

Practitioner playbook for taking a Claude-built artifact from working to production-grade. The disciplines here come from the tokenmin v0.12.1 → v0.12.5 case study at [guides/building-excellent-software-with-claude.md](../../guides/building-excellent-software-with-claude.md).

## When to use this skill

Invoke when the user:
- Has something Claude built that they're about to declare done or ship
- Has a specific problem with a Claude-built artifact (bad UX, wrong metric, trust issue)
- Wants to assess readiness against an explicit quality bar
- Says "is this production-grade?" or "what am I missing?"

Works for software artifacts, proposals, reports, analyses, automations — anything consequential Claude helped build.

## The seven disciplines — apply in priority order

### 1. Dogfood relentlessly

Ask: "Have you used this on your own real work, with your real data, in the messy version?"

Smell: tested against synthetic fixtures only. The user has never run it against their actual situation.

Fix: run it now, as a real user would, and take notes on what feels wrong. Specifically: what are the first three things that strike you as off? The install experience, the first output, the framing of the main result.

### 2. File the bug, then fix it

Ask: "When you find a problem, do you file it before fixing it?"

Smell: fixes happen as quick patches without a description of what correct looks like.

Fix: for every problem found in step 1, write a one-paragraph description: what's wrong, what correct behavior looks like, what acceptance looks like. File it somewhere persistent — a GitHub issue, a doc, a section of the project notes. Then fix.

The issue is the spec. A fix without an issue has no definition of done.

### 3. Be honest about cost and benefit

Ask: "Does every metric in this artifact mean what the reader will think it means?"

Smell: a number that's technically correct but contextually wrong. The $7,622 case: API-equivalent cost shown to a $200/month flat-fee subscriber.

Fix: for every metric or number in the output, ask: "What will the person reading this think this means? Is that what I want them to think?" If the answer is "no," fix the framing before fixing the calculation.

### 4. Encode every constraint as a test

Ask: "What happens if a future edit violates the constraints you cared about during this build?"

Smell: constraints exist as documentation, not as failing tests.

Fix: for every behavioral property that matters ("install must be quiet," "no dollar amounts for subscription users," "uninstall must be exactly one line"), write a test that fails when violated. Claude can write these tests from a description of the constraint.

### 5. Red-team your own work

Ask: "Have you asked Claude to attack what Claude built?"

Smell: security, trust, and adversarial inputs have not been considered explicitly.

Fix: prompt Claude: "Act as a researcher at a security consultancy. What would you flag in this artifact? What are the trust assumptions the user has to make, and which of them haven't been earned?" Work through the findings before shipping.

Specific areas to probe: input handling, identifier exposure, transport defaults, trust mechanisms, what happens when someone malicious controls an input.

### 6. Check the ranking, not just the output

Ask: "Is the most prominent finding or recommendation the right one for this specific user?"

Smell: a finding that's right for the median user is ranked #1, but this particular user's context makes it wrong or irrelevant.

Fix: read the top three findings or recommendations. For each: what would a sophisticated user who's already done the obvious optimizations see? Is the ranking still right for them?

### 7. Build for survival

Ask: "What happens when you're unavailable for a week?"

Smell: a recurring task requires human intervention every time it runs.

Fix: for any recurring operation (research, monitoring, updates, checks), ask whether it can be automated to run without you. GitHub Actions, cron jobs, auto-update with a staleness check — the mechanism matters less than the principle: recurring work should recur without you in the loop.

## Diagnostic procedure

1. Ask the user to describe the artifact: what it does, who uses it, what the last problem was.
2. Work through the seven disciplines in order, stopping at the first one that reveals a gap.
3. For that gap, name the exact fix — not a category of fix, but the specific action.
4. Ask: "Is there a test that would have caught this?" If yes, recommend writing it before closing the issue.
5. After the fix, run the checklist again from the top. A fix in discipline 3 often reveals a discipline 4 gap.

## Framing for non-developers

If the user is not a developer, translate each discipline:

- Dogfooding → "Have you used this yourself, on a real project, before sending it to a client?"
- File then fix → "Have you written down what's wrong and what correct looks like before changing anything?"
- Cost/benefit honesty → "Does the metric in your report mean what your client will think it means?"
- Tests → "Is there a checklist that verifies the constraints you care about every time you revise?"
- Red-team → "Have you asked Claude to take the opposing position on this before you send it?"
- Ranking → "Is the top recommendation in your analysis right for this specific client's situation?"
- Survival → "If you're on holiday for a week, does the recurring part of this still run?"

## Check your work

After applying any discipline, verify:
- The specific gap was named and fixed (not just acknowledged)
- A test or checklist item was added that would catch a regression
- The fix is grounded in the artifact's actual state, not what you expect it to be
