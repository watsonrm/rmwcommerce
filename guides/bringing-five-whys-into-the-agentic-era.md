---
title: Bringing Five Whys into the Agentic Era
description: The Five Whys has been the default failure-analysis tool in software for decades, and for decades practitioners have warned it produces a single linear story for failures that don't have one. This guide keeps the question and fixes the method — branch instead of chain, validate every link counterfactually, and dispatch an independent AI skeptic whose only job is to break your analysis. Worked through a real outage where the skeptic caught the cause the first pass missed.
date: 2026-06-08
last_modified_at: 2026-06-10
author: Rick Watson
agent_friendly: true
keywords: five whys, 5 whys software, root cause analysis software, blameless postmortem, adversarial root cause analysis, incident analysis AI agent, why complex systems fail, John Allspaw infinite hows, cause tree vs five whys, AI skeptic agent, agentic postmortem
---

# Bringing Five Whys into the Agentic Era

**The Five Whys has been the default failure-analysis tool in software for decades, and for decades the best practitioners have warned that it produces a single linear story for failures that don't have one. The fix is not to abandon the question — it's to change the method around it: branch instead of chain, validate every causal link counterfactually, then dispatch an independent AI skeptic whose only job is to break your analysis. This guide walks the upgrade through a real outage where the skeptic caught the contributing cause the first pass missed.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-06-08 · Roughly 18 min read*

Who this is for: engineers, SREs, and operators who run postmortems — anyone wiring an AI agent into their incident process and wondering whether it can do more than summarize the timeline — and anyone investigating why an agent or AI reasoning step reached a wrong conclusion, mis-verified a fact, or took a wrong action.

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. This guide synthesizes published work by John Allspaw, Richard Cook, the SNAFUcatchers (STELLA report), and Google's SRE organization — quoted material is the property of its respective owners and used under fair use with attribution. See [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

*The AI skeptic in this guide is a dispatched subagent. If you're deciding whether a job like that should be a prompt, a skill, or a full agent, start with [The Prompts-to-Agents Ladder](../the-prompts-to-agents-ladder.md); for the architecture that keeps dispatched subagents from silently returning garbage, see [Multi-Agent Fan-Out and Verification](../multi-agent-fan-out-and-verification.md).*

---

## TL;DR — what's in it for you

The Five Whys asks a good question ("why did this happen?") and then, run naively, answers it badly: it walks one cause backward through five steps and stops. Real software failures don't have one cause walking backward. They have several latent conditions that were each necessary and only jointly sufficient, and the naive method is structurally blind to all but one of them.

You don't need a new question. You need four changes to the method, and one of them is newly cheap in 2026:

1. **Branch, don't chain.** At every step ask "what were *all* the conditions for this?" — build a tree, not a line.
2. **Ask "how," not "why."** "Why" slides toward "who" (blame). "How did this make sense at the time?" surfaces the conditions instead.
3. **Validate every link counterfactually.** "If I remove just this one factor, does the failure still happen?" That test is what separates a real contributing cause from a story.
4. **Dispatch an adversarial skeptic.** The newly cheap part: a second AI agent, given only your analysis and told to refute it — find the missing branch, call out the blame smell, attack your most confident link.

### Where to spend your time, in priority order

| # | Change | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| 1 | **Branch instead of chain** | The single highest-value fix. A linear chain throws away every co-cause; a tree keeps them. Most "we fixed it and it happened again" stories are a chain that pruned the cause that actually mattered. | Low — it's a question change |
| 2 | **Counterfactual-validate each link** | Stops you from shipping a plausible story. Each link must earn its place: remove it, does the failure still occur? | Low |
| 3 | **Ban two stopping points** | "Human error" and "we hit the fifth why" are where bad analyses end. Both are arbitrary. Outlaw them. | Low |
| 4 | **Dispatch an AI skeptic** | Catches what you can't see in your own analysis. Adversarial-by-construction beats one model nodding along with itself. | Medium — one well-scoped agent |

The first three are free and you can apply them in your next postmortem. The fourth is the part this guide is really about: it was impractical to staff a dedicated devil's advocate for every incident, and now it isn't.

## How to use this

The operational form of this guide is the Claude Code skill at [`skills/understand-failure/`](../skills/understand-failure/). Install it once:

```bash
# from a clone of this repo
mkdir -p ~/.claude/skills && cp -r skills/understand-failure ~/.claude/skills/
```

Then describe the failure to Claude — paste the error, incident timeline, or broken job output — and say one of these:

> "understand why this failed"
> "root-cause this"
> "do a postmortem on this"
> "5-whys this"

Claude will load the skill and run the full branching analysis: facts, blameless frame, cause tree, counterfactual validation, adversarial skeptic pass, and system-level remediations. The article below is the reasoning behind the method — read it for the *why*; the skill is the *how*.

---

## 1. The method is as old as software's habits

The Five Whys did not come from software. It came from Toyota. Sakichi Toyoda, the founder of the company that became Toyota, developed the practice of asking "why" iteratively to get past a symptom to the thing behind it; Taiichi Ohno formalized it into the Toyota Production System in the mid-twentieth century and called it ["the basis of Toyota's scientific approach."](https://en.wikipedia.org/wiki/Five_whys) Ohno's own framing: "by repeating *why* five times, the nature of the problem as well as its solution becomes clear."

Ohno's own worked example, from his 1988 book *Toyota Production System*, is a machine that stopped:

1. Why did the machine stop? A fuse blew from an overload.
2. Why the overload? The bearing wasn't lubricated enough.
3. Why not enough lubrication? The lubrication pump wasn't pumping enough.
4. Why? The pump shaft was worn.
5. Why was it worn? No filter, so metal scrap got in.

Five whys, one cause per step, and a satisfying answer at the bottom: install a filter. It is a wonderful tool for a worn pump on an assembly line, and it migrated into software incident reviews because it is cheap, requires no training, and feels rigorous.

The trouble is that the worn pump and a distributed-systems outage are not the same kind of problem, and the method that solves the first quietly misleads on the second.

## 2. Why naive Five Whys quietly fails for software

The most-cited treatment of this in the software world is John Allspaw's 2014 essay ["The Infinite Hows (or, the Dangers of the Five Whys)."](https://www.kitchensoap.com/2014/11/14/the-infinite-hows-or-the-dangers-of-the-five-whys/) Allspaw — then CTO of Etsy, later co-founder of Adaptive Capacity Labs, and one of the people who put "blameless postmortem" into the industry's vocabulary — lays out the structural problems. They come down to four.

**It forces a line onto something that isn't one.** Allspaw's verdict: "At best, it locks you into a causal chain, which is not how the world actually works." A worn pump has a tidy chain. A production incident has a web. When you walk a chain backward, every branch you don't take is a cause you've silently discarded.

**There is no single root cause to find.** This is the part most people resist, so it's worth quoting the primary sources. Richard Cook, in his 1998 treatise ["How Complex Systems Fail,"](https://how.complexsystems.fail/) Point 3: "Catastrophe requires multiple failures — single point failures are not enough... Each of these small failures is necessary to cause catastrophe but only the combination is sufficient." And Point 7, even more bluntly: "Post-accident attribution to a 'root cause' is fundamentally wrong... Because overt failure requires multiple faults, there is no isolated 'cause' of an accident."

Allspaw names the hidden assumption the Five Whys smuggles in: each presenting symptom has only one sufficient cause. Drop that assumption and the whole single-chain structure collapses. The right mental model is his phrase from a [companion essay](https://www.kitchensoap.com/2012/02/10/each-necessary-but-only-jointly-sufficient/): failures in complex systems require multiple contributing causes, **each necessary but only jointly sufficient.**

The SNAFUcatchers [STELLA report](https://snafucatchers.github.io/) (2017), a study of real software and distributed-systems anomalies by Cook, Allspaw, David Woods and others, found exactly this in the field: "There was no root cause. Instead, the anomalies arose from multiple latent factors that combined to generate a vulnerability." Those latent factors had often been present for weeks or months, and the thing that "activated" them was usually minor — a near-normal event, not a dramatic one.

**"Why" slides into "who."** Allspaw again: "asking *why?* too easily gets you to an answer to the question *who?* (which in almost every case is irrelevant)." This is the blame trap. The moment a branch terminates at a person, the analysis stops learning. Google's SRE organization built its entire [postmortem culture](https://sre.google/sre-book/postmortem-culture/) around closing this trap: "You can't 'fix' people, but you can fix systems and processes to better support people making the right choices…" If your analysis ends at "they should have been more careful," you have found someone to blame and nothing you can fix.

**Stopping at "human error" is hindsight, not analysis.** Cook, Point 8: hindsight bias "remains the primary obstacle to accident investigation," because after the fact the path to failure looks obvious and the operators look careless. They weren't. Point 17: "failure free operations are the result of activities of people who work to keep the system within the boundaries of tolerable performance." People are usually what *keeps* the system up; an analysis that treats them as the cause of its going down has the sign backward.

And one structural problem the Five Whys can't escape even in principle: where you start and where you stop are arbitrary. Allspaw, citing the safety researcher Nancy Leveson, points out that these causes aren't discovered, they're *constructed* — "we are the ones that are choosing where (and when) to start asking questions, and where/when to stop asking the questions." The "fifth" why has no special status; the [Wikipedia summary](https://en.wikipedia.org/wiki/Five_whys) of the standard critiques puts it plainly: there's a "tendency for investigators to stop at symptoms rather than going on to lower-level root causes," and "the arbitrary depth of the fifth why is unlikely to correlate with the root cause."

So: a method that draws a line where there's a web, slides toward blame, and stops at an arbitrary depth chosen by the investigator. The question is fine. The method around it needs work.

## 3. The rigorous version: keep the question, change the method

None of the critics above say "stop asking why." They say ask it better. Here is the method that survives their objections, assembled from their work. It has six moves.

**1. Establish the facts before you touch a cause.** Write down what was *observed* — the symptom in concrete terms, the blast radius, the timeline with timestamps — separately from what you *infer*. The STELLA finding that activators are usually minor matters here: don't go looking for a dramatic trigger, and don't paper over a gap in the evidence with a plausible-sounding cause. If you don't know, mark it unknown.

**2. Frame it blamelessly, out loud.** State the assumption explicitly at the top: everyone involved acted reasonably given what they knew, saw, and were incentivized to do at the time. This isn't decoration; it changes the questions. When a branch heads toward "person P made a mistake," the blameless frame turns that into the *next question*: what made P's action look correct in the moment? What did the tooling invite? What information was missing?

**3. Ask "how," not "why."** Allspaw's central practical swap. "Why did you deploy?" invites a defense. "How did deploying make sense given what you saw on the dashboard?" invites a description of the conditions — and the conditions are the thing you can actually change. As he puts it, asking *how* "gets you to describe (at least some of) the conditions that allowed an event to take place, and provides rich operational data."

**4. Branch, don't chain.** This is the heart of it. At every node, ask "what were *all* the conditions necessary for this — what else had to be true?" Then recurse on each one. A node usually has two to four contributing conditions, not one. You are building a cause **tree**. Tag each node by layer:

- **Proximate** — the immediate trigger, the thing that fired.
- **Contributing** — the conditions that had to co-exist for the trigger to do harm.
- **Systemic / latent** — the long-standing design or process factors, present for weeks or months, that made the system vulnerable. These are the ones worth fixing. A tree with no systemic nodes hasn't gone deep enough.

**5. Validate every link counterfactually.** For each edge in the tree, apply one test — the operational form of "necessary but only jointly sufficient":

> If this single factor had not been present, everything else equal, would the failure have been prevented?

Three outcomes. If yes, this factor was sufficient on its own on this path — a strong lever. If "no, but it was needed," it's necessary-but-not-sufficient: a genuine co-contributor, and you **keep it and its siblings** — this is exactly the case the naive chain throws away. If removing it changes nothing, it's noise — prune it. Every surviving node carries its verdict.

**6. Remediate the system, not the people.** For each systemic node that survived, propose a fix that is system- or process-level (a guard, a test, a default, an alert, a removed footgun), owner-assignable, and linked to the node it removes. Cook, Point 16: "Safety is an emergent property of systems... it does not reside in a person, device or department." "Be more careful next time" is not a remediation. Prefer fixes that neutralize a factor sitting under *multiple* branches — that's your highest leverage.

That's the rigorous method, and it has existed in this shape since roughly the STELLA report. What's new is being able to attack it cheaply.

## 4. Bringing it into the agentic era

Here is the honest problem with everything in Section 3: it depends on a kind of discipline that erodes under pressure, late at night, when the person writing the postmortem is also the person who shipped the change. You are asking the author of an analysis to find the flaws in their own analysis — to notice the branch they didn't think of, to catch themselves sliding toward blame, to attack the conclusion they're relieved to have reached. People are bad at this about their own work, and the worse the week, the worse they are.

The classical answer was a human devil's advocate, a second reviewer whose job is to disagree. It works, and almost nobody can afford to staff it for every incident.

In 2026 you can. The move is to encode the method as a repeatable skill, and split it across two roles:

- **The analyst** (you, or you-plus-an-assistant) gathers the facts and builds the tree.
- **The skeptic** is a *separate, independent AI agent*, handed only the tree and the facts and given exactly one job: **break it.**

The independence is the whole point, and it's a design decision, not a vibe. The skeptic does not see your reasoning, your relief, or your stake in the conclusion — it sees the artifact. Its prompt is adversarial by construction: not "review this," which gets you agreement, but "assume the analyst missed something; find it." Concretely, the skeptic is told to return five things:

1. **The missing branch.** Name a contributing cause absent from the tree, or argue convincingly that it's complete.
2. **The blame smell.** Does any leaf reduce to "human error," "should have been more careful," or a person's name? If so it isn't a leaf — push it deeper into the conditions that made the action sensible.
3. **The single-cause smell.** Has the tree secretly collapsed into one dominant chain with the rest as garnish? If only one branch has depth, the branching failed.
4. **The counterfactual challenge.** Take the two nodes the analyst is most confident about and argue the *opposite* — that removing them would *not* have prevented the failure. If that argument holds, the node is mis-rated.
5. **The stopping-rule challenge.** Where did each branch stop, and is the stop principled (it hit an actionable system lever) or arbitrary (it ran out of ideas, or hit five)?
6. **The premise audit.** Take each branch's load-bearing *factual* claim — especially any claim about how a deterministic system behaved ("it routed there," "no rule matched," "that field was empty") — and check that the analyst actually read the *mechanism that produces the behavior*: the function, the config it reads, the state file. A cause asserted from the symptom plus inference, or from "I searched and didn't find it," is presumed wrong until the decider itself has been read. This is the question that catches the most expensive miss — an analysis that is rigorous, well-branched, skeptically reviewed, and built on a fact that was never true.

The sixth item is the one I learned to add the expensive way — after an analysis of mine ran clean through the first five and still reached a confident, wrong conclusion, because its central claim about how a piece of routing code behaved was inferred from the symptom and never checked against the code itself. Then you fold the skeptic's findings back in. If it found a real missing branch, the analysis isn't done — recurse.

Two cautions, because a skeptic agent is still an agent. First, a skeptic that comes back "looks good, nothing wrong" on the first pass is suspect — make it name a candidate missing branch regardless, the way a good reviewer can always find *something*. Second, the skeptic's output is a claim, not a verdict; you still read it and decide. The architecture that keeps a dispatched subagent from confidently returning nonsense — typed contracts, giving it only the inputs it needs, verifying its output rather than trusting "it ran" — is its own subject, covered in [Multi-Agent Fan-Out and Verification](../multi-agent-fan-out-and-verification.md). The relevant point here is narrower: the *reasoning method* has a step that humans reliably skip, and that step is now cheap to run with real independence.

The last move is a verification gate the whole analysis must pass before anyone trusts it: the tree has at least two branches with real depth and at least one systemic node; no leaf is "human error" or a name; every link has a counterfactual verdict; the skeptic actually ran and either found a gap (folded in) or argued completeness; every remediation is system-level and owner-assignable; every proximate claim traces to something observed — and for a claim about how a system behaved, to the mechanism that *produced* the behavior, not merely the symptom it produced; and the analysis closes with a plain-language TL;DR — what broke, the real cause, the fix — that a reader can understand without decoding the tree. Miss any one and you're not done.

That last item is easy to wave off as cosmetic, and it isn't. A rigorous tree is dense by design — layered tags, counterfactual verdicts, a skeptic pass — and the person who has to *act* on it is usually not the person who built it. An analysis nobody can read is an analysis nobody acts on, which is the same outcome as not running it. So the gate requires a TL;DR with the jargon stripped out: what happened in a sentence, the one to three causes that actually matter, and the single fix worth saying yes to. The tree earns the conclusion; the TL;DR delivers it.

When the failure is a reasoning or verification error — an agent concluded something false, asserted an unverified fact, or took a wrong action on a wrong premise — the method does not change, but one guard becomes critical: the **verification-corpus discipline** and the **absence-of-evidence trap**.

Example: an agent asserted that a true, well-documented commitment (the $30K RetailClub title slot is committed) was "fabricated" and moved to strip it from outbound emails. It was wrong on every count. Why? The agent searched the event wiki and a structured data snapshot — the right-looking places — but the *actual* fact lived in source-notes, Gmail threads, and deal records it didn't think to check first. Worse, it escalated "not found in my search" into "does not exist / is fabricated" — absence-of-evidence treated as evidence-of-absence, the maximally accusatory label. The fix: when an unconfirmed fact materially changes an outward action, the guard is (1) search where the fact would *live*, not where the search grammar suggests; (2) never label in-system work or human-recorded facts "fabricated" or "false" without first searching the source record; cap at "unverified — flagging for the human"; (3) if the fact originated in a proposal, deal note, or source artifact the agent itself created or read, check *that* (provenance first). The systemic lever: a true fact stuck in a source-notes layer but never promoted to the structured layer that verification reads is a state-machine gap; fix that sync and the failure cannot recur regardless of how the agent searches.

## 5. What this caught in practice (a real, sanitized example)

The day I wrote this guide, one of my own automations gave me a live test.

A small background job ran every five minutes to copy freshly-fetched content from cloud storage down to a local machine. One morning a document I knew had been collected — a customer call transcript — simply wasn't there locally. It turned out the job had been quietly doing nothing for four days. Three hundred-odd runs, every one reporting success, every one a no-op.

The naive Five Whys writes itself, and it's a trap:

> Why was the file missing? The sync didn't run. Why? It exited early every time. Why? Its "is another copy already running?" lock check failed. Why? The lock used a command that doesn't exist on that operating system. Why? Nobody tested it on that OS. Fix: use a lock that works. Done.

That chain is true, and fixing the lock was necessary, and stopping there would have left the system about to fail again. Here's what the branching version found instead.

The **proximate** cause was real and as above: a lock mechanism borrowed from one operating system silently failed on another, and — this is the important shape — it failed *closed into silence*. The missing command produced an error that the script interpreted as "another copy is already running, so I'll exit quietly." Absence of the tool looked identical to normal contention. Fail-closed-quiet.

But branching surfaced two more conditions the chain skipped entirely. First, **nothing was watching the job.** The health monitor watched the individual workers but not the one process whose job was to deliver the workers' own health signals — a blind spot at exactly the chokepoint. Worse, when that process died, it stopped delivering everyone else's signals too, so the rest of the dashboard lit up with false "stale" warnings that would have buried the real cause even if someone had looked. Second — and this is the branch I missed on the first pass — the job's design had a *second, independent* way to die silently: it ran under a credential that an unattended automation policy will quietly revoke. Fix the lock and nothing else, and the job would have run for about a week and then silently died again for a completely different reason.

I didn't find that second branch. The skeptic agent did.

I built the cause tree, validated the links, and felt finished. Then I handed the tree and the facts to a separate agent and told it to break the analysis. It came back with the missing branch named outright: *this is a competent single-fault analysis of a component that had two independent silent-death paths; you fixed one and the tree doesn't even mention the other.* It also caught that I'd inflated one cause into three near-duplicate branches to make the tree look broader than it was, and — the correction I least wanted — that I'd called the monitoring fix the "highest-leverage" change when monitoring doesn't *prevent* anything; it shortens detection from four days to fifteen minutes. The prevention lever was a pre-deploy test on the actual target operating system. Those are different stages of the same failure and the analysis needs both.

The remediations split cleanly once the tree was honest, and the split is the lesson. *Prevention* fixes stop this specific bug: a working lock, a pre-deploy smoke test on the real OS, running under a durable credential. *Detection* fixes catch the next silent failure whatever its cause: a heartbeat on the delivery process itself, suppressing the false-stale storm, and — the deepest one, which the skeptic pushed me to — an end-to-end assertion that expected data actually arrived, rather than trusting any single component to announce its own death. The naive chain would have shipped one prevention fix and called it a postmortem.

## 6. Steal this

The whole upgrade fits on an index card. Next time something breaks:

- **Write the facts first** — symptom, blast radius, timeline — and keep them separate from your guesses.
- **Say the blameless assumption out loud** before you start: everyone acted reasonably on what they knew.
- **Ask "how did this make sense at the time?"** not "why did you do that?"
- **Branch at every node:** "what were *all* the conditions here?" Build a tree, tag each node proximate / contributing / systemic.
- **Test every link:** "remove just this — does the failure still happen?" Keep the necessary-but-not-sufficient ones; prune the noise.
- **Ban two endings:** never stop at "human error" / "should've been careful," and never stop just because you counted to five.
- **Dispatch a skeptic** — a person or an independent AI agent — and make it find the missing branch, the blame smell, and the weakest link. Fold it back in.
- **Fix systems, not people.** Every remediation should be something you could assign to an owner, and prefer the ones that sit under more than one branch.
- **Verify where facts would live.** When investigating a reasoning or verification failure, search the source record and the canonical layer where a fact would live *first*, not where the search grammar suggests. Never label work or human-recorded facts "fabricated" without checking provenance; cap at "unverified — flagging for the human."
- **End with a jargon-free TL;DR.** Close with three plain lines — what happened, the cause(s) that matter, the one fix worth saying yes to — readable by someone who never saw the tree. The rigor is for you; the TL;DR is for whoever has to act.

The runnable version of this — the skill that builds the tree, validates the links, and dispatches the skeptic — is published alongside this guide as [`skills/understand-failure/`](../skills/understand-failure/). Drop it into `~/.claude/skills/` — it is the canonical method for ANY failure or wrong-outcome investigation, regardless of phrasing — and it triggers when you say "understand why this failed", "root-cause this", "why did you reach that conclusion", or any of the enumerated triggers in the skill Trigger section.

The Five Whys was never wrong to ask why. It was wrong to expect one answer.

---

## Sources & Attribution

This guide synthesizes a small set of primary sources. Every quotation is drawn from the linked original.

- **John Allspaw, "The Infinite Hows (or, the Dangers of the Five Whys)"** (2014) — https://www.kitchensoap.com/2014/11/14/the-infinite-hows-or-the-dangers-of-the-five-whys/ (republished on O'Reilly Radar: https://www.oreilly.com/radar/the-infinite-hows/). The canonical software-domain critique; source of the linear-chain, "why-becomes-who," construction-of-cause, and ask-how arguments.
- **John Allspaw, "Each necessary, but only jointly sufficient"** (2012) — https://www.kitchensoap.com/2012/02/10/each-necessary-but-only-jointly-sufficient/. Source of the necessary-but-jointly-sufficient framing.
- **Richard Cook, "How Complex Systems Fail"** (1998) — https://how.complexsystems.fail/. Points 3, 7, 8, 16, and 17 quoted; the foundational "no single root cause," hindsight-bias, and emergent-safety arguments.
- **SNAFUcatchers, "STELLA: Report from the SNAFUcatchers Workshop on Coping with Complexity"** (2017) — https://snafucatchers.github.io/. The field study finding multiple latent factors and no root cause in real software anomalies.
- **Google, "Site Reliability Engineering" — Postmortem Culture** — https://sre.google/sre-book/postmortem-culture/. The blameless-postmortem industry standard; "You can't 'fix' people, but you can fix systems and processes to better support people making the right choices…"
- **"Five whys," Wikipedia** — https://en.wikipedia.org/wiki/Five_whys. Origin (Toyoda / Ohno) and the standard list of documented criticisms.

Further reading on the alternatives referenced: Sidney Dekker's *The Field Guide to Understanding Human Error* (the "new view"), Nancy Leveson's STAMP/CAST, and Salesforce Engineering's "How, Not Why" all extend the same line of argument.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. This guide synthesizes published work by John Allspaw, Richard Cook, the SNAFUcatchers (STELLA report), and Google's SRE organization — quoted material is the property of its respective owners and used under fair use with attribution. See [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
