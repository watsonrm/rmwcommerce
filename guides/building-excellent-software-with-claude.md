---
title: Building excellent software (with Claude)
description: '"Claude built it" reads like a quality stamp and isn''t. The code compiles, the tests pass, the metric calculates — and three weeks later a customer asks why your dashboard says revenue is up when their bank statement says it''s down. A technically correct, contextually wrong metric is worse than no metric. This is the seven-discipline list that closes the gap between Claude''s output and something you''d stake your name on.'
date: 2026-05-24
author: Rick Watson
agent_friendly: true
keywords: Claude built code is wrong, Claude technically correct but wrong, production-grade Claude output, dogfood Claude code, Claude metric framing wrong, ship Claude code safely, Claude code review checklist, contextually wrong metric
---

# Building excellent software (with Claude)

**"Claude built it" reads like a quality stamp and isn't. The code compiles, the tests pass, the metric calculates — and three weeks later a customer asks why your dashboard says revenue is up when their bank statement says it's down. A technically correct, contextually wrong metric is worse than no metric. This is the seven-discipline list that closes the gap between Claude's output and something you'd stake your name on.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-24 · Roughly 15 min read*

Who this is for: anyone shipping consequential work built with Claude — code, proposals, automations, reports — who wants to close the gap between "Claude built it" and production-grade.

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Technical claims are grounded in Anthropic documentation cited throughout — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- "Claude built it" is not a quality guarantee. It is a starting point. The seven disciplines in this article are what close the gap.
- These lessons are not specific to software. Every one applies to any consequential artifact you build with Claude's help: a proposal, an analysis, an automation, a report.
- If you take nothing else: a metric that is technically correct and contextually wrong is worse than no metric at all. Fix the framing before you fix the calculation.

### Where to spend your time, in priority order

| # | Discipline | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | Be honest about cost and benefit | A contextually wrong metric damages trust in everything else | 1–2 hours at design |
| **2** | Dogfood before you ship | Real use catches what spec reviews miss | Every release |
| **3** | File the bug, then fix it | The issue defines acceptance before the fix begins | Every fix |
| **4** | CI guards every behavior you care about | Claude doesn't carry constraints across sessions — the test does | Every new constraint |
| **5** | Red-team your own work | The threat model is your job; Claude will find gaps if you ask | Once before launch |
| **6** | Check the ranking, not just the output | A correct finding ranked first when it shouldn't be is a UX problem | Every release |
| **7** | Build for survival | Software that only runs while you're watching isn't software yet | Once per project |

Most readers should absorb the first three and stop. Rows 4–7 matter, but rows 1–3 address the failure modes that actually ship.

---

## How to use this guide

The companion skill at [`skills/building-excellent-software/`](../skills/building-excellent-software/) is the operational form of this guide. Install it once:

```bash
# from a clone of this repo
mkdir -p ~/.claude/skills && cp -r skills/building-excellent-software ~/.claude/skills/
```

Then describe your build to Claude — what you're building, where you are in the process, what's going wrong — and say one of these:

> "Apply the excellent software checklist to this"
> "Where am I on the dogfood-to-production ladder?"
> "Red-team what I just built"

Claude will load the skill and work through the relevant disciplines against your actual artifact. The article below is the reasoning behind each discipline.

---

## Related guides

The seven disciplines below assume you've already chosen the right shape for what you're building. If you haven't, start there:

- **[The Prompts-to-Agents Ladder](../the-prompts-to-agents-ladder.md)** — prompt, skill, single agent, or multi-agent system. The wrong rung is not rescued by good testing or red-teaming.

Two peer guides cover the tactical layer once the shape is set:

- **[Making Claude Faster](making-claude-faster.md)** — the six levers that turn a working build into a fast one.
- **[Multi-Agent Fan-Out and Verification](../multi-agent-fan-out-and-verification.md)** — the architecture playbook for Rung 4 builds: where verification belongs and where it doesn't.

---

## 1. Be honest about cost and benefit

This discipline matters most for anyone building instrumentation, reporting, or any tool that puts a number in front of a user. Getting it wrong is the highest-cost mistake, which is why it is ranked first.

The failure mode is subtle: a metric can be mathematically correct and still be wrong for the user. An API-equivalent dollar figure shown to a flat-fee subscriber is accurate at the token level and misleading at the plan level. A "dollars saved per month" framing shown to a user who has already paid a fixed price is internally coherent and contextually incoherent. The math clears. The trust does not.

The fix has two parts. First, **plan-aware framing**: match the unit of measure to what the user actually experiences. A subscriber on a flat monthly fee should see quota stretch and time, not dollar amounts. Second, **externalized pricing**: if the tool's output depends on current pricing, the prices need to live in a config file with a staleness warning — not hardcoded constants that silently go stale when rates change.

Anthropic's prompt caching documentation makes a related point on the technical side: cache misses produce real latency that users feel even when they cannot quantify it. ([Anthropic: Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)) The framing extension — that perceived cost is the cost that matters — is the principle here: validate framing, not just calculation.

**The principle:** a technically correct metric that is contextually wrong is worse than no metric. It damages trust in everything else the tool says.

---

## 2. Dogfood before you ship

The only honest source of UX feedback is using your own artifact on your own real work.

Anthropic engineering describes this pattern in a specific context: when they built tools for Claude, they tested against their internal workspace rather than synthetic fixtures. Their post notes the evaluations were run against "our internal workspace, mirroring the complexity of our internal workflows, including real projects, documents, and messages." ([Anthropic: Writing effective tools for agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents))

What real-use testing catches that a spec review will not: a terminal that fills with 24 lines of output before the tool does anything useful; a detector misfiring on a sophisticated setup because it lacks visibility into a second layer of the user's architecture. Neither finding surfaces in a code review. Both surface within minutes of real use.

The Claude Code best practices documentation frames this precisely: Claude "performs dramatically better when it can verify its own work" — and the same logic applies to the builder. Without a real feedback loop, plausible-looking artifacts fail in ways that only real use reveals. ([Claude Code: Best practices](https://code.claude.com/docs/en/best-practices))

**The principle:** use your own artifact on your own real problem before declaring it done. Synthetic inputs produce synthetic confidence.

---

## 3. File the bug, then fix it

When something goes wrong during real use, the temptation is to fix it immediately. Resist this. File the issue first.

Filing forces you to articulate what is actually wrong — and more importantly, what the correct behavior should be. The issue is the spec. It defines acceptance before the fix begins, which means you know when you are done. A fix without an issue is a fix without a definition of done.

This also solves a Claude-specific problem. Claude does not carry context across sessions. A decision made in one session does not survive to the next without explicit encoding. The issue backlog is the durable form of your intent. Anthropic's context engineering guidance describes the same technique for agents: regularly writing notes to memory outside the context window, so the agent can track progress across a complex task. ([Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) A public issue tracker is that external memory for the humans directing the build.

The discipline produces a traceable record: each issue has a description of the problem, a repro path, and a fix sketch. That is the spec. The fix is constrained by the issue, not by whatever seemed easy to implement. Working repositories following this pattern accumulate a public issue backlog where every closed issue is a proof of that discipline.

**The principle:** the issue is the spec. File it before the fix. When the fix goes wrong, there is a record of what you were trying to do, and Claude has something to read in the next session.

---

## 4. CI guards every behavior you care about

As §3 noted, Claude doesn't carry constraints across sessions — so the test suite is the durable encoding of that intent. A decision made in session 1 — "install output must be quiet" — does not survive to session 12 without explicit encoding. The test suite is the only reliable mechanism for persistent constraints.

Anthropic's evaluation guidance describes the same architecture for agent work: convert manual checks into test cases, run them on every commit, and graduate passing evals to regression suites that maintain a near-100% pass rate. ([Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)) The principle transfers directly to CI for software built with Claude.

### What to test

The decision of what to pin in a test is the actual hard part. Pin too little and constraints decay silently across sessions. Pin too much and the test suite ossifies the implementation — Claude can no longer refactor cleanly because every internal change cascades into test churn.

The working rule: pin **observable behavior at the surface a user can see**, not implementation choices behind it. A test that asserts "subscriber reports contain no dollar amounts in the TL;DR" is durable because it describes the user-visible outcome. A test that asserts "the internal formatting helper is called once per finding" is brittle because it grades the implementation, which you might legitimately want to change later.

### A taxonomy of test types worth having

*Where to start: output-framing tests if your tool surfaces numbers; command-contract tests if you ship a CLI; release-feature tests if you ship to others.*

**Property tests** assert invariants that hold across all inputs in the relevant space — idempotency, salt sensitivity, secret-pattern coverage across token formats. Stronger than example-based tests for code where adversarial input is plausible.

**Behavioral contract tests** assert what the user sees and what survives a given operation, not how the code gets there. "This command produces exactly one line of output." "The dev-tree safety guard prevents destructive operations on a source checkout."

**Output framing tests** catch a class of bug that unit-level number-correctness tests cannot: the math is right, but the *unit* is wrong for the user. "Subscriber-plan reports contain no dollar amounts anywhere in summary cards." These tests guard against the failure mode in §1.

**Command contract tests** lock down CLI surface expectations. "The `--check` flag does not pull." "The status cache expires correctly." "SHA comparison uses prefix matching" — this last one guards a bug pattern where full SHAs from one source are compared against short SHAs from another, producing matches that never fire.

**Release-feature regression tests** tie each shipped behavior to a specific test so regressions are localized when they happen. One test per shipped behavior.

### The integration test at the seams

Property tests give strong guarantees on the components they cover; integration tests catch the failures at the seams between them. An anonymizer-leak gate — constructing a synthetic directory with planted identifiers, running the full pipeline, failing if any plaintext markers survive — catches anonymization regressions that are easy to introduce when adding new scraper paths and nearly impossible to catch in a code review. It exercises the full pipeline end-to-end, not just individual components.

### File-then-test-then-fix

The discipline from §3 extends one step: file → write the test for the correct behavior → write the fix. The test sits between the issue and the fix, and it does specific work:

- It forces the fix to be defined in terms the test can grade. If you cannot express the correct behavior as a test, you have not defined the fix clearly enough yet.
- It prevents the regression. The fix may decay across future Claude sessions; the test does not.
- It documents the constraint in code, where future sessions of Claude will read it, rather than in prose where they will not.

### Red-teaming your test suite

The test suite is itself a Claude-built artifact, and it can fail in all the ways the rest of this article warns about.

**Are the tests overly brittle?** Anthropic's evaluation guidance specifically warns against tests that grade tool sequences or implementation paths rather than outcomes — "agents regularly find valid approaches that eval designers didn't anticipate." ([Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)) Assert on observable outcomes; leave the path unconstrained.

**Do the tests reflect real failure modes, or synthetic ones?** A test fixture is a hypothesis about how the code will be used. If fixtures only resemble code-review examples and never resemble real adversarial input — the mangled session files, the edge-case paths with spaces and unicode — passing tests will coexist with real bugs.

**Are mocks hiding real failures?** A common pattern: a test patches a function in a way that bypasses the production code path entirely. The test passes; the bug ships. The fix is to mock at the boundary, not inside the unit under test. If a test mocks a function that is part of the behavior you are trying to verify, the test is verifying the mock.

**Are the tests deterministic?** A flaky test that fails 5% of the time will be ignored within a week. Once it is ignored, every other test in the suite has less authority — the discipline of "every red test blocks the merge" decays. Treat a flaky test as a real failure with an unknown root cause.

**Are the tests fast enough to actually run?** A suite that takes 20 minutes per push will be skipped under deadline pressure. Anthropic's prompt caching docs are relevant here at the principle level: time-to-feedback is a cost, and that cost is paid by the developer's discipline. ([Anthropic: Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)) Keep the fast tests pure and the integration tests scoped narrow.

**Is the test count being used as a metric?** The count itself proves nothing. Twenty tests against the wrong behavior is worse than four tests against the right behavior. The relevant question is "for each shipped behavior, is there a test that would fail if the behavior regressed?"

**Are the tests readable to someone who did not write them?** Tests are documentation. A test named `test_x_works` with five unrelated assertions tells the next reader nothing. Name tests for the contract they enforce: `test_subscriber_reports_contain_no_dollar_amounts`, `test_uninstall_produces_one_line_output`. The name is the spec.

**The principle:** the test suite is the durable form of every behavioral constraint, but tests can lie in all the same ways the artifact can. Test the right thing, at the right layer, in a way that does not silently rot.

---

## 5. Red-team your own work

Building with Claude creates a specific risk: Claude will build what you ask for. If you ask for a telemetry system, you will get a telemetry system. If you do not specify a threat model, Claude will not invent one.

Anthropic's guidance on building effective agents notes that autonomous agents involve "higher costs, and the potential for compounding errors," and recommends "extensive testing in sandboxed environments, along with the appropriate guardrails." ([Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)) For security specifically, the threat model is the builder's responsibility, not Claude's default output.

Four patterns that show up in a serious security pass on any tool that handles user data:

*Skip this section if your tool only runs on your own files and never accepts third-party input.*

**Identifier hashing strength.** SHA-256 to anonymize predictable values — file paths, configuration keys — is not enough. An adversary who guesses that a path like `~/.ssh/known_hosts` is likely present can precompute its hash and reverse-identify it. The fix is HMAC with a random salt generated on first run and stored with restricted permissions. The salt means precomputed tables fail.

**ReDoS defense.** A tool that runs regex patterns against potentially adversarial content faces exponential backtracking from a carefully crafted input string. The fix is an input size cap: truncate before the regex engine sees it. Bad lines are dropped, not raised on.

**ANSI injection.** A value with planted ANSI escape sequences in a rendered field can hijack the terminal output. The fix is a control-character strip before rendering any user-visible string, covered by a property test.

**Credentials in configuration.** Writing authentication tokens to a config file that is read by other tools exposes them. The fix is a per-install credential file with restricted permissions, separate from any shared config.

None of these are exotic findings. The OWASP and NIST literature covers all four. The point is that Claude will not surface them unless you ask with a specific threat-modeling framing: "What would a security researcher flag in this?" produces different results than "is this secure?"

**The principle:** ask Claude to red-team what it built — it is good at this — but give it a specific bar to work against.

---

## 6. Check the ranking, not just the output

A correct finding ranked first when it should not be is a UX problem, not just a logic problem. The user's response to a list of recommendations depends heavily on what is at the top.

Consider a detector that classifies a setup as "critical" based on main-session model data, in a tool used by people who have already routed cheaper work to lower-cost subagents. The detector is technically correct about the main session. The recommendation is wrong for the user's actual setup. The detector lacks visibility into a second layer of the architecture it is analyzing.

A disclaimer added to the finding's evidence text is honest but insufficient — it is a footnote on a ranking that is wrong. The right fix is context-aware ranking: signals that indicate the user has already addressed the concern should downgrade confidence substantially.

The same failure mode appears from a different angle when detectors fire on configurations they cannot see. A check for global configuration that does not account for project-scoped equivalents serving the same function will fire on sophisticated setups where it is irrelevant — making the tool least useful for exactly the people who would benefit most.

Anthropic's evaluation guidance frames the underlying principle: avoid "overly brittle" tests that grade specific tool sequences rather than outcomes, because agents "regularly find valid approaches that eval designers didn't anticipate." ([Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)) Detection and ranking need equal rigor.

**The principle:** a correct finding ranked first when it shouldn't be is a UX problem. Detection and ranking need equal rigor.

---

## 7. Build for survival

There is a meaningful difference between using Claude to do work and building software with Claude that does work. The former requires a human in the loop every time. The latter runs the relevant parts without one.

Anthropic's multi-agent research system post describes this directly: the system was designed so "the model must operate autonomously for many turns, making decisions about which directions to pursue based on intermediate findings," with the architecture decoupling computation from human availability. ([Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)) Their managed agents post goes further, describing a design where if a container fails mid-task, the harness catches the error and Claude resumes from the durable session log — not from scratch. ([Anthropic: Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents)) The principle is the same: software that depends on a human being present for routine operation is not software — it is an elaborate prompt.

The applied form for a research or monitoring tool: a weekly GitHub Actions workflow that watches relevant sources, files issues for newly-seen items, and commits its seen-state back to the repo after each run so it does not re-file what it has already found. (Applies to research / monitoring tools that need fresh data — skip if your artifact is interactive or one-shot.) It survives laptop shutdown, network outages, and weeks where the maintainer does not think about the project at all. The research continues without human involvement.

The automation does not need to be sophisticated — a cron job, a scheduled GitHub Action, a watched folder. What matters is that the answer to "what happens when the builder is unavailable for a week?" is not "nothing runs."

**The principle:** for any recurring task your artifact handles, build the automation before declaring the artifact done. Software that requires a human in the loop for routine operation is not software yet.

---

## When these disciplines are wrong

For a prototype you plan to throw away, running five test suites and a red-team pass is over-engineering. For an hour-long exploration you will not revisit, filing a GitHub issue before fixing a bug is bureaucracy. For internal tooling that handles no user data and runs only on your own machine, a formal threat model is probably waste.

The disciplines in this article apply to artifacts that will be used by people who are not you, that hold data or make decisions that matter, or that are supposed to keep running when you stop watching. If that description doesn't fit what you're building, apply proportionally less. The goal is not process — it's closing the gap between "Claude built it" and something you can stand behind.

---

## What this means outside software development

Every discipline in this article has a non-software version.

Dogfooding is using your own deliverable as a real user before sending it to a client. File-then-fix is writing a clear description of what is wrong and what correct looks like before touching the draft. Red-teaming is asking Claude to take the opposing view on your proposal before you present it. Tests are checklists with acceptance criteria rechecked on every revision. Cost-and-benefit honesty is making sure the metric in your report means what your client thinks it means.

Claude is capable of building things quickly. The gap between "quickly built" and "production-grade" is the set of disciplines above applied consistently across a real build. None of them require programming knowledge. All of them require the willingness to slow down at the moment when it is tempting to ship.

---

## Sources & Attribution

**Primary sources — Anthropic first-party documentation:**

- [Claude Code: Best practices](https://code.claude.com/docs/en/best-practices) — context window management, verification, subagent routing
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — autonomous agent loops, parallel tool use, survival architecture
- [Anthropic: Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) — decoupling brain from hands, durable session log, error recovery
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — sandboxed testing, guardrails, poka-yoke tool design
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — eval methodology, CI integration, regression suites
- [Anthropic: Writing effective tools for agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — dogfooding on internal infrastructure, using Claude to improve Claude's tools
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — persistent state, just-in-time retrieval, external memory
- [Anthropic: Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — perceived latency as a cost, cache pre-warming, time-to-first-token

**Illustrative example:**

- [tokenmin-scanner](https://github.com/watsonrm/tokenmin-scanner) — a public Claude usage audit tool referenced as an illustrative example throughout this guide

**Corrections from prior circulating versions:**

This article has been revised and red-teamed across multiple passes since initial draft. The most significant structural change was rebalancing the examples: earlier versions grounded each principle primarily in a specific open-source tool's build record. The rewrite leads with the principle and Anthropic's documentation, using illustrative examples in abstract form. The priority ordering, the seven disciplines, and the Anthropic citations are unchanged. The full revision history is in the [git log](https://github.com/watsonrm/rmwcommerce/commits/main/guides/building-excellent-software-with-claude.md).

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. See [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
