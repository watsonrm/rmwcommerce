---
title: Shallow Research — Grounded AI Web Research Without Breaking the Bank
description: A bounded one-context research tier that answers most questions for a fraction of the cost — and a clear rule for when to escalate to the expensive deep tier.
date: 2026-06-12
author: Rick Watson
agent_friendly: true
keywords: AI research cost, deep research too expensive, shallow research AI, bounded research tier, AI web research workflow, cost-discipline AI, research escalation rule, cheap AI research pattern
---

# Shallow Research: Grounded AI Web Research Without Breaking the Bank

**Most AI research questions don't need a fleet. A bounded one-context pass answers them for a fraction of the cost — and the one design decision that matters most is the rule that stops cost from silently creeping up the moment the question gets harder.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-06-12 · Roughly 12 min read*

Who this is for: anyone running AI research workflows who has noticed the bill from "deep research" features doesn't match what most of those questions actually needed.

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved. Quoting brief excerpts with attribution is fine. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- Most research questions — product comparisons, quick factual lookups, "what's the current state of X" — can be answered with three searches, a handful of source reads, and one synthesis pass. No subagents. No orchestration overhead.
- The expensive multi-agent tier exists for genuinely hard questions. The discipline is not "use the cheap one when you can" but "never let the cheap tier silently upgrade itself into the expensive one."
- The escalation guardrail is the load-bearing design decision: the moment the task wants to spawn an agent, open a workflow, or read a 6th+ source, it stops and asks you whether the question is worth the deeper spend.
- A companion skill — [`skills/shallow-research/`](../skills/shallow-research/) — packages this as a runnable Claude Code workflow.

### Where to spend your time, in priority order

The first two rows are the whole pattern. The rest is implementation detail for people building their own tier.

| # | Practice | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | **Hard caps in the cheap tier** — ≤3 searches, ≤5 fetches, zero subagents | Without explicit caps, "cheap" research will naturally expand to fill the question. The caps are what make the tier cheap, not the intent. | Config / prompt, 15 min |
| **2** | **The escalation guardrail** — stop and ask before crossing any cap | Silent cost creep is the failure mode, not expensive research. The guard prevents cost from scaling under a "cheap" label while the human is unaware. | One conditional in your prompt/skill |
| **3** | **Output discipline** — answer first, confidence marked, sources listed | Saves re-reading time. "Unverified" is better than a wrong assertion presented as fact. | Style rule |
| **4** | **Decision criteria for which tier to use** — stakes of the decision, not complexity of the topic | The question "what's the best NoSQL DB for my use case" and "which vendor should I commit $200K to" look similar. They're not. | Judgment |

Most readers should apply the first two and stop. The caps + the escalation guard are the whole method.

---

## How to use this

The operational form of this guide is the Claude Code skill at [`skills/shallow-research/`](../skills/shallow-research/). Install it once:

```bash
# from a clone of this repo
mkdir -p ~/.claude/skills && cp -r skills/shallow-research ~/.claude/skills/
```

Then describe what you're trying to research and say one of these:

> `/shallow-research: what are the current pricing tiers for Klaviyo vs Attentive?`
> `/shallow-research: is there a well-regarded open-source alternative to Segment?`
> `shallow research: what changed in Google's Shopping feed spec this year?`

Claude will run the bounded pass and surface an answer with sources. If the question warrants the deeper tier, it will say so and stop — you decide whether to proceed. The article below is the reasoning behind the two-tier model; the skill is the working implementation.

---

## Why "always use deep research" is a cost problem

The multi-agent research pattern is genuinely powerful. Anthropic's published multi-agent research system — which fans out 3–5 parallel subagents (up to 10+ for complex queries) and uses parallelized tool calling — cut research time by up to 90% for complex queries in their internal evaluation. ([source](https://www.anthropic.com/engineering/multi-agent-research-system)) That's a real gain on the right workload.

The problem is that each subagent is its own context window and its own billing event. Fan out five agents and you're paying for five parallel contexts. Fan out ten and the cost multiplies accordingly. For a question that needed one focused read of two or three sources, that overhead buys nothing.

The pattern people fall into is wiring their AI tool to always use the expensive tier because it's available and because "more research is better." On individual queries, the delta is small enough to ignore. Across a workflow that runs dozens of research queries — or a team running them concurrently — it compounds into a meaningful line item for questions that didn't need it.

The fix is not to avoid multi-agent research. It's to have two tiers and a clear rule for when to use each.

---

## The two-tier model

The distinction between the tiers is not quality. A shallow research pass on a straightforward factual question will usually produce a better answer than a deep research pass on the same question, because the deep pass introduces orchestration overhead and synthesis from many partially-relevant sources. The distinction is what the question actually requires.

| | Shallow tier | Deep tier |
| :-- | :--- | :--- |
| **Architecture** | Single context, inline execution | Multi-agent fan-out, orchestration layer |
| **Search queries** | ≤3, fired as one parallel batch | Unbounded; agents spawn and recurse |
| **Source reads** | ≤5 primary sources | ~15+ sources across parallel agents |
| **Verification** | Inline sanity check — every load-bearing claim traces to a source actually read | Adversarial multi-pass — agents cross-check each other's findings |
| **Subagents** | Zero | Multiple (3–5 minimum; 10+ for complex queries) |
| **Output** | Answer + sources in one response | Synthesized cited report, usually multi-section |
| **Cost** | One context, minimal overhead | Multiple contexts; scales with fan-out |
| **Right for** | Factual lookups, product comparisons, "current state of X," quick due diligence | Legal/medical/financial decisions, deep competitive analysis, any question where you'll act on the answer with real money |

The column that matters most for deciding which tier to use is the last row: **the stakes of the decision, not the complexity of the topic.** A complicated topic with low stakes (curiosity, background reading, internal tooling choices) still belongs in the cheap tier. A simple-sounding question with high stakes ("should we switch payment processors?" asked before a contract renewal) belongs in the deep tier.

---

## The escalation guardrail — the load-bearing idea

Caps alone don't solve the problem. If the task silently expands past the cap — reads a sixth source because the fifth one linked to something relevant, spawns a subagent because the question turned out harder than expected — you end up with deep-research costs under a shallow-research label, with no visibility into when or why it crossed the line.

The escalation guardrail closes that gap. The rule is:

> The moment the task wants to spawn an agent, open a workflow, or read beyond the cap, it stops and surfaces the decision to the human. It doesn't proceed. It says: "This question is pushing past the shallow tier — here's why. Do you want me to run the deep pass?"

This is different from a soft suggestion. The shallow tier must be incapable of exceeding its caps without explicit human authorization. Cost can only escalate with consent.

The practical form this takes in a skill or a prompt: before any tool call that would push past the limit, check the count. If adding this call would exceed the cap, emit a clear message explaining what the question needs that the shallow tier can't provide, offer the deep tier, and halt. The user decides whether the question is worth the spend.

In Rick's `/shallow-research` skill, this looks like a hard counter on searches and fetches, with a pre-call check before each tool invocation. The output message when the guardrail fires is specific: it names what the question needs (a third search to disambiguate vendor claims, a sixth source to cross-check a pricing table) and what the deep tier would do differently. The human gets enough information to make the escalation decision intelligently.

---

## Build your own shallow tier

The pattern works regardless of which AI tool you're using. The components:

**1. Hard caps.** Pick numbers and write them into the prompt or skill definition. Rick's defaults: ≤3 web searches, ≤5 page fetches. These aren't magic — pick what fits your typical question size. The important thing is that they're explicit and enforced, not aspirational.

**2. Single context.** No subagents. No tool calls that spawn parallel agents or open a new conversation. Everything happens inline in one response. This is what keeps the overhead low.

**3. Parallel execution within the budget.** Fire all searches in one batch, not sequentially. The cap is on count, not on parallelism — parallelism within the cap is free speed.

**4. Inline source verification.** Before asserting a load-bearing fact (a price, a hard yes/no, a version number, a limit), confirm it traces to a source actually fetched, not just a search snippet. Search snippets are often stale, truncated, or from the wrong page version. This is not a full adversarial check — it's a quick "did I actually read this?" pass.

**5. Output discipline.** Lead with the answer. Use comparison tables when you're comparing more than two things. Mark anything you couldn't verify as "unverified" rather than asserting it. End with a sources list of URLs actually used, not search queries.

**6. The escalation guardrail.** Described above. This is not optional — without it, "shallow research" is just a guideline you'll ignore when the question gets interesting.

---

## When shallow is not enough

The shallow tier is wrong — not just suboptimal, actually wrong — for a few specific situations:

**High-stakes decisions with real money or legal exposure.** If you'll use the answer to sign a contract, make a hire, or inform a financial projection, the cheap tier's sanity check is not enough. The deep tier's adversarial cross-check exists for exactly this.

**Topics where the primary sources contradict each other.** Three fetches aren't enough to adjudicate a disputed technical question. If your first two sources disagree and the question matters, escalate.

**Anything requiring synthesis across many primary sources.** Literature reviews, competitive landscapes with more than five meaningful players, policy analysis — these are structurally multi-source problems. Trying to do them in five fetches produces an answer shaped by whichever sources happened to come up first.

**Questions where being wrong is not recoverable.** Security decisions, infrastructure choices that are hard to reverse, anything where the cost of a wrong answer exceeds the cost of thorough research by a wide margin.

For everything else — the factual lookups, the quick comparisons, the "what's the current state of X" passes that make up most day-to-day AI research use — the shallow tier is faster, cheaper, and often more focused than the deep one.

---

## Sources & Attribution

- Anthropic, [Building a multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — cited for the multi-agent fan-out architecture, parallel subagent counts, and the "up to 90% research time reduction" figure. The specific deep-research design parameters (verification loop structure, source caps) described in this guide are from Rick's own `/deep-research` skill implementation, not from the Anthropic article.
- Anthropic, [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — background on single-agent vs. multi-agent tradeoffs.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved. Quoting brief excerpts with attribution is fine. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
