# Building excellent software (with Claude)

**Seven disciplines that close the gap between "Claude built it" and production-grade — grounded in the public tokenmin-scanner build record.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Technical claims are grounded in the public source repositories and Anthropic documentation cited throughout — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- "Claude built it" is not a quality guarantee. It is a starting point. The seven disciplines in this article are what close the gap.
- Every principle here is verifiable in the public [tokenmin-scanner](https://github.com/watsonrm/tokenmin-scanner) repo — filed issues, committed tests, CI workflows, and SECURITY.md form the audit trail.
- These lessons are not specific to software. Every one applies to any consequential artifact you build with Claude's help: a proposal, an analysis, an automation, a report.
- If you take nothing else: a metric that is technically correct and contextually wrong is worse than no metric at all. Fix the framing before you fix the calculation.

### Where to spend your time, in priority order

| # | Discipline | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | Be honest about cost and benefit | A contextually wrong metric damages trust in everything else | 1–2 hours at design |
| **2** | Dogfood before you ship | Real use catches what spec reviews miss | Every release |
| **3** | File the bug, then fix it | The issue defines acceptance before the fix begins | Every fix |
| **4** | Encode every constraint as a test | Claude doesn't carry constraints across sessions — the test does | Every new constraint |
| **5** | Red-team your own work | The threat model is your job; Claude will find gaps if you ask | Once before launch |
| **6** | Check the ranking, not just the output | A correct finding ranked first when it shouldn't be is a UX problem | Every release |
| **7** | Build for survival | Software that only runs while you're watching isn't software yet | Once per project |

Most readers should absorb the first three and stop. Rows 4–7 matter, but rows 1–3 address the failure modes that actually ship.

---

## How to use this guide

The companion skill at [`skills/building-excellent-software/`](../skills/building-excellent-software/) is the operational form of this guide. Install it once:

```bash
# from a clone of this repo
cp -r skills/building-excellent-software ~/.claude/skills/
```

Then describe your build to Claude — what you're building, where you are in the process, what's going wrong — and say one of these:

> "Apply the excellent software checklist to this"
> "Where am I on the dogfood-to-production ladder?"
> "Red-team what I just built"

Claude will load the skill and work through the relevant disciplines against your actual artifact. The article below is the reasoning behind each discipline.

---

## The case study: tokenmin-scanner

[tokenmin-scanner](https://github.com/watsonrm/tokenmin-scanner) is an open-source Claude usage audit tool — it scans local Claude session history, anonymizes it, and surfaces where tokens are wasted or spent in the wrong places. The scanner is public under Apache-2.0.

The examples in this article come from the issue backlog, test files, and CI workflows in that public repo. Every claim links to its source. Where an example illustrates a general principle, the principle is stated separately so it generalizes beyond this specific tool.

---

## 1. Be honest about cost and benefit

This is the discipline that matters most for anyone building instrumentation, reporting, or any tool that puts a number in front of a user — and it is ranked first because getting it wrong is the highest-cost mistake.

The tokenmin-scanner issue backlog documents a concrete failure of this kind. [Scanner #2](https://github.com/watsonrm/tokenmin-scanner/issues/2) describes a scenario where the tool reported an API-equivalent cost that was mathematically correct — input tokens plus output tokens plus cache reads and writes, priced at retail API rates — but wrong for the user's actual plan. A Claude Pro or Max subscriber who sees an API-equivalent dollar figure does not pay that figure. The number is accurate at the token level and misleading at the plan level. ([scanner #3](https://github.com/watsonrm/tokenmin-scanner/issues/3) documents the same problem in the savings framing: showing a dollar-per-month savings to a user on a flat-fee plan is equally incoherent.)

The fix had two parts.

**Plan-aware framing.** Pro and Max reports no longer show dollar amounts in the TL;DR or savings cards. Subscribers see quota stretch percentage, token volume, and time instead. The underlying API-equivalent cost is still computed — the math is preserved — but the framing matches what the user actually pays. API and unknown-plan users see dollars unchanged.

**Externalized pricing.** Before the fix, model prices were hardcoded constants in source. When Anthropic changes pricing, every installed copy is silently wrong until the user updates. The fix moved prices to `engine/pricing.json` with a `last_updated` field and a staleness warning threshold. The 18 tests in `test_cost_framing.py` guard both properties. The lead fixture comment states the acceptance criterion directly: a subscriber who sees an implausible dollar figure distrust the tool before getting any value from it.

The principle generalizes to every reporting context: when a metric lands in front of someone, you are making an implicit claim about what it means to them. The right question is not "is this number accurate?" but "does this number mean what the user thinks it means?" Anthropic's own prompt caching documentation frames the same idea: the latency cost of a cache miss is real, and users feel it even if they cannot quantify it — perceived cost is the cost that matters. ([Anthropic: Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching))

**The principle:** validate framing, not just calculation. A technically correct metric that is contextually wrong is worse than no metric — it damages trust in everything else the tool says.

---

## 2. Dogfood before you ship

The only honest source of UX feedback is using your own artifact on your own real work.

Anthropic engineering describes this pattern in a specific context: when they built tools for Claude, they tested against their internal workspace rather than synthetic fixtures. Their post notes the evaluations were run against "our internal workspace, mirroring the complexity of our internal workflows, including real projects, documents, and messages." ([Anthropic: Writing effective tools for agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents))

The tokenmin-scanner build record shows what this catches. One early release produced 24 lines of terminal output before the tool did anything meaningful. That number was not derived from analyzing the install script — it was observed by watching a real terminal fill up and noticing that something was wrong. The fix was a CI guard asserting that install completes in five lines or fewer. The spec review would have said "installation should be quiet." The dogfood session said "here are the 24 lines."

A second thing real-use testing caught was a detector misfiring on a sophisticated multi-layer setup. [Scanner #9](https://github.com/watsonrm/tokenmin-scanner/issues/9) documents the pattern: the `model_overspend` detector classified the main-session model mix as "critical" without visibility into subagent routing. The detector was reading a real signal and drawing a wrong conclusion from it. Neither finding would have shown up in a code review. Both showed up within minutes of real use.

The Claude Code best practices documentation frames this precisely: Claude "performs dramatically better when it can verify its own work" — and the same logic applies to the builder. Without a real feedback loop, plausible-looking artifacts fail in ways that only real use reveals. ([Claude Code: Best practices](https://code.claude.com/docs/en/best-practices))

**The principle:** use your own artifact on your own real problem before you declare it done. Synthetic inputs produce synthetic confidence.

---

## 3. File the bug, then fix it

When something goes wrong during real use, the temptation is to fix it immediately. Resist this. File the issue first.

Filing forces you to articulate what is actually wrong — and more importantly, what the correct behavior should be. The issue is the spec. It defines acceptance before the fix begins, which means you know when you are done. A fix without an issue is a fix without a definition of done.

This also solves a Claude-specific problem. Claude does not carry context across sessions. A decision made in one session does not survive to the next without explicit encoding. The issue backlog is the durable form of your intent. Anthropic's context engineering guidance describes the same technique for agents: regularly writing notes to memory outside the context window, so the agent can track progress across a complex task. ([Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)) The GitHub issue tracker is that external memory for the humans directing the build.

The tokenmin-scanner issue backlog for the v0.12.x sprint is public and traceable:

- [#1](https://github.com/watsonrm/tokenmin-scanner/issues/1) — `models_used_families` values reported as 0 due to integer-flooring on the percentage calculation. Filed with exact repro; closed after fix and test.
- [#2](https://github.com/watsonrm/tokenmin-scanner/issues/2) — cost framing misleading for Pro/Max subscribers.
- [#3](https://github.com/watsonrm/tokenmin-scanner/issues/3) — savings shown in dollars per month for flat-fee plan users.
- [#5](https://github.com/watsonrm/tokenmin-scanner/issues/5) — low-impact findings diluting the main report.
- [#6](https://github.com/watsonrm/tokenmin-scanner/issues/6) — `tokenmin show <id>` leaking dollar amounts on Pro/Max plans.
- [#7](https://github.com/watsonrm/tokenmin-scanner/issues/7) — audit not disclosing subagent-model invisibility.
- [#8](https://github.com/watsonrm/tokenmin-scanner/issues/8) — `no_global_claude_md` and `no_custom_agents` firing when the user has project-scoped configuration that makes them irrelevant.
- [#9](https://github.com/watsonrm/tokenmin-scanner/issues/9) — `model_overspend` ranking wrong for subagent-heavy users.

Each issue has a description of the problem, a repro path, and a fix sketch. That is the spec. The fix is constrained by the issue, not by whatever seemed easy to implement. This forces a clear answer to "what does fixed look like?" before a line of code changes.

**The principle:** the issue is the spec. File it before the fix. When the fix goes wrong, you have a record of what you were trying to do, and Claude has something to read in the next session.

---

## 4. CI guards every behavior you care about

Claude does not remember constraints across sessions. A decision made in session 1 — "install output must be quiet" — does not survive to session 12 without explicit encoding. The test suite is the only reliable mechanism for persistent constraints.

Anthropic's evaluation guidance describes the same architecture for agent work: convert manual checks into test cases, run them on every commit, and graduate passing evals to regression suites that maintain a near-100% pass rate. ([Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)) The principle transfers directly to CI for software built with Claude.

The tokenmin-scanner test structure at v0.12.5 shows what this looks like in practice:

**56 tests across 5 suites.** The examples below cover four of them — the ones that most directly illustrate constraint encoding:

- `test_scrubber.py` (15 tests) — idempotent scrub, secret-pattern coverage (Anthropic, OpenAI, Stripe, JWT, npm, Google, AWS, GitHub, Slack tokens, PEM blocks), ReDoS input cap, salt sensitivity and stability, HTTPS-only enforcement, snapshot file permissions.

- `test_cost_framing.py` (18 tests) — asserts that Pro/Max plan reports contain no dollar amounts in the TL;DR or savings cards. Subscription users see quota stretch percentage, tokens, and hours instead. API and unknown-plan users continue showing dollars. Pricing loads from `engine/pricing.json`, not from hardcoded constants.

- `test_update_ux.py` (8 tests) — covers the `tokenmin update` command contract: `--check` does not pull, cache expires correctly, SHA comparison uses prefix.

- `test_v0_12_4.py` (10 tests) — guards four specific behaviors shipped in v0.12.4: low-impact findings filter, plan-aware cost framing on `tokenmin show`, subagent invisibility footnote in the `model_overspend` evidence, and project-scoped CLAUDE.md detection.

Every push to main runs all five suites across Python 3.10, 3.11, and 3.12. The CI configuration is [public](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/ci.yml).

The CI suite also includes an anonymizer-leak check: it constructs a synthetic `~/.claude/` directory with planted identifiers, runs the scanner against it, and fails if any plaintext markers survive the scrub. The step lives in `.github/workflows/ci.yml` alongside the other test suites. This catches anonymization regressions that are easy to introduce when adding new scraper paths and nearly impossible to catch in a code review.

**The principle:** when a constraint surfaces during real use, your first question should be "what test would have caught this?" Write that test, then write the fix. The test is what makes the constraint stick across sessions.

---

## 5. Red-team your own work

Building with Claude creates a specific risk: Claude will build what you ask for. If you ask for a telemetry system, you will get a telemetry system. If you do not specify a threat model, Claude will not invent one.

Anthropic's guidance on building effective agents notes that autonomous agents involve "higher costs, and the potential for compounding errors," and recommends "extensive testing in sandboxed environments, along with the appropriate guardrails." ([Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)) For security specifically, the threat model is the builder's responsibility, not Claude's default output.

The tokenmin-scanner [SECURITY.md](https://github.com/watsonrm/tokenmin-scanner/blob/main/SECURITY.md) documents the findings from a dedicated red-team pass after the v0.12.x build. Four findings are instructive as patterns:

**Identifier hashing.** The initial design used SHA-256 to anonymize file paths and identifiers. SHA-256 is not enough: an adversary who guesses that a path like `~/.ssh/known_hosts` is likely present can precompute its hash and reverse-identify it. The fix was HMAC-SHA256 with a 32-byte salt generated on first run and stored at `~/.tokenmin/.salt` (chmod 0600). The salt means precomputed tables fail.

**ReDoS defense.** The anonymizer runs regex patterns against potentially adversarial content from session files. A carefully crafted input string can cause exponential backtracking in a naive regex engine — a denial-of-service against the user's own machine. The fix was a 64 KiB input cap: every string is truncated before the scrubber sees it. Bad lines are dropped, not raised on.

**ANSI injection.** A session file with planted ANSI escape sequences in project or file names could hijack the terminal when the tool rendered them. The fix was a `_strip_ctl()` helper that removes ANSI CSI/OSC sequences and C0/C1 control characters before rendering any displayed string. There is a property test covering this in the scrubber suite.

**Token handling in configuration.** The initial approach wrote authentication tokens to `.git/config`, where `git config --list` would expose them. The fix was a per-install credential helper file (chmod 0600) that keeps the token out of the config entirely.

The open-source approach to the scanner itself — the code that decides what leaves the user's machine — is a trust mechanism: anyone can diff their installed copy against the public repo. That is documented in the README as an explicit bargain, not a general claim about open source being more secure.

**The principle:** Claude will implement what you specify. The threat model is your job. Ask Claude to red-team what it built — it is good at this — but give it a specific bar to work against. "What would a security researcher flag in this?" produces different results than "is this secure?"

---

## 6. Check the ranking, not just the output

A correct finding ranked first when it should not be is a UX problem, not just a logic problem. The user's response to a list of recommendations depends heavily on what is at the top.

[Scanner #9](https://github.com/watsonrm/tokenmin-scanner/issues/9) documents this failure mode. The `model_overspend` detector classified a user's setup as "critical" based on main-session model data. The detector is technically correct — the main session is using a premium model — and the recommendation is wrong for users who have already routed cheaper work to lower-cost models at the subagent layer. The detector sees the main session only. It cannot see subagent routing.

The v0.12.4 response was to add a disclaimer to the `model_overspend` evidence text noting that "this only measures your main session." That was honest but insufficient. The finding still ranked first with a critical severity label. A disclaimer is a footnote on a ranking that is wrong.

The issue remains open. The right fix is context-aware ranking: high subagent call volume should downgrade confidence substantially, because a user with significant Agent tool call activity over a given period has already separated cheap work from judgment work at the subagent layer.

[Scanner #8](https://github.com/watsonrm/tokenmin-scanner/issues/8) illustrates the same pattern from a different angle: the `no_global_claude_md` and `no_custom_agents` detectors fired on a project-scoped setup where they are irrelevant. The detector fired because it only checks for global configuration, not for project-scoped equivalents that serve the same function.

The same principle appears in Anthropic's evaluation guidance: avoid "overly brittle" tests that grade specific tool sequences rather than outcomes, because agents "regularly find valid approaches that eval designers didn't anticipate." ([Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)) A detector that is right for the median user is wrong for sophisticated users in ways that make the tool less useful for exactly the people who would benefit most.

**The principle:** a correct finding ranked first when it shouldn't be is a UX problem, not just a logic problem. Detection and ranking need equal rigor.

---

## 7. Build for survival

There is a meaningful difference between using Claude to do work and building software with Claude that does work. The former requires a human in the loop every time. The latter runs the relevant parts without one.

Anthropic's multi-agent research system post describes this directly: the system was designed so "the model must operate autonomously for many turns, making decisions about which directions to pursue based on intermediate findings," with the architecture decoupling computation from human availability. ([Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system)) Their managed agents post goes further, describing a design where if a container fails mid-task, the harness catches the error and Claude resumes from the durable session log — not from scratch. ([Anthropic: Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents)) The principle is the same: software that depends on a human being present for routine operation is not software, it is an elaborate prompt.

The tokenmin-scanner [detector-research workflow](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/detector-research.yml) illustrates the applied form. The workflow runs in GitHub Actions every Monday at 13:23 UTC. It watches Anthropic's news feed, engineering blog, Claude Code releases, and cookbook commits for new posts. It files a GitHub issue for each newly-seen item so the maintainer can triage it as a detector candidate or not. The state is committed back to the repo after each run so it does not re-file what it has already seen.

The workflow survives laptop shutdown, network outages, and weeks where the maintainer does not think about the project at all. The research continues without human involvement.

[Scanner #15](https://github.com/watsonrm/tokenmin-scanner/issues/15) documents the output of one such research session: 15 candidate detectors, each grounded in a specific Anthropic source, each with a detection signal derivable from the snapshot schema. The issue is the artifact; the workflow is what keeps producing similar artifacts on schedule.

**The principle:** for any recurring task your artifact handles, ask what happens when the builder is unavailable for a week. If the answer is "nothing runs," build the automation before declaring the artifact done. Software that requires a human in the loop for routine operation is not software yet.

---

## When these disciplines are wrong

For a prototype you plan to throw away, running five test suites and a red-team pass is over-engineering. For an hour-long exploration you will not revisit, filing a GitHub issue before fixing a bug is bureaucracy. For internal tooling that handles no user data and runs only on your own machine, a formal threat model is probably waste.

The disciplines in this article apply to artifacts that will be used by people who are not you, that hold data or make decisions that matter, or that are supposed to keep running when you stop watching. If that description doesn't fit what you're building, apply proportionally less. The goal is not process — it's closing the gap between "Claude built it" and something you can stand behind.

---

## What this means outside software development

Every discipline in this article has a non-software version.

Dogfooding is using your own deliverable as a real user before sending it to a client. File-then-fix is writing a clear description of what is wrong and what correct looks like before touching the draft. Red-teaming is asking Claude to take the opposing view on your proposal before you present it. Tests are checklists with acceptance criteria rechecked on every revision. Cost-and-benefit honesty is making sure the metric in your report means what your client thinks it means.

The version-number-specific details in this article are specific to tokenmin-scanner. The disciplines are not. Claude is capable of building things quickly. The gap between "quickly built" and "production-grade" is the set of disciplines above applied consistently across a real build.

None of them require programming knowledge. All of them require the willingness to slow down at the moment when it is tempting to ship.

---

## Sources & Attribution

**Primary sources — public repositories:**

- [tokenmin-scanner](https://github.com/watsonrm/tokenmin-scanner) — Apache-2.0 scanner, anonymizer, CLI, tests, CI
- [scanner #1](https://github.com/watsonrm/tokenmin-scanner/issues/1) — `models_used_families` flooring bug (closed)
- [scanner #2](https://github.com/watsonrm/tokenmin-scanner/issues/2) — cost framing misleading for Pro/Max subscribers
- [scanner #3](https://github.com/watsonrm/tokenmin-scanner/issues/3) — savings shown in dollars per month for flat-fee plans
- [scanner #5](https://github.com/watsonrm/tokenmin-scanner/issues/5) — low-impact findings diluting main report
- [scanner #6](https://github.com/watsonrm/tokenmin-scanner/issues/6) — `tokenmin show` leaking dollars on Pro/Max
- [scanner #7](https://github.com/watsonrm/tokenmin-scanner/issues/7) — subagent-model invisibility not disclosed
- [scanner #8](https://github.com/watsonrm/tokenmin-scanner/issues/8) — project-scoped setup not detected
- [scanner #9](https://github.com/watsonrm/tokenmin-scanner/issues/9) — `model_overspend` ranking wrong for subagent-heavy users
- [scanner #15](https://github.com/watsonrm/tokenmin-scanner/issues/15) — v0.12.6+ detector candidates
- [tokenmin-scanner SECURITY.md](https://github.com/watsonrm/tokenmin-scanner/blob/main/SECURITY.md) — threat model, HMAC design, ReDoS defense, transport defaults
- [tokenmin-scanner CI workflow](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/ci.yml)
- [detector-research workflow](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/detector-research.yml) — weekly cloud research agent

**Primary sources — Anthropic first-party documentation:**

- [Claude Code: Best practices](https://code.claude.com/docs/en/best-practices) — context window management, verification, subagent routing
- [Anthropic: How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — autonomous agent loops, parallel tool use, survival architecture
- [Anthropic: Scaling Managed Agents](https://www.anthropic.com/engineering/managed-agents) — decoupling brain from hands, durable session log, error recovery
- [Anthropic: Building effective agents](https://www.anthropic.com/engineering/building-effective-agents) — sandboxed testing, guardrails, poka-yoke tool design
- [Anthropic: Demystifying evals for AI agents](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) — eval methodology, CI integration, regression suites
- [Anthropic: Writing effective tools for agents — with agents](https://www.anthropic.com/engineering/writing-tools-for-agents) — dogfooding on internal infrastructure, using Claude to improve Claude's tools
- [Anthropic: Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — persistent state, just-in-time retrieval, external memory
- [Anthropic: Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — perceived latency as a cost, cache pre-warming, time-to-first-token

**Corrections from prior circulating versions:**

The article previously listed the priority order with "Dogfood relentlessly" as discipline #1. The rewritten version re-ranks "Be honest about cost and benefit" to #1. Cost-framing errors are the failure mode most likely to ship: they are subtle, they survive spec review, they survive code review, and they damage user trust immediately on first use. Dogfooding is what catches them — so dogfooding is the mechanism, and cost-honesty is the most important thing to catch.

The prior version referenced the "v0.12.1 → v0.12.5 build" and "roughly 12 hours of focused work" as the case study framing. Those phrases have been removed. The time claim was unverifiable from the public repo, and the specific-version framing added no generalized value. The case study now refers to the issue backlog and CI record, both of which are verifiable.

The prior version referenced the F&F bundle and tokenmin-site (a private repository). Those references have been stripped. Claims grounded only in private repos cannot be verified by readers.

The prior version's Sources section cited `anthropic.com/engineering/claude-code-best-practices`. That URL redirects permanently (HTTP 308) to `code.claude.com/docs/en/best-practices`. The canonical URL is used throughout this version.

The prior version cited three Anthropic sources. This version cites eight, with each citation tied to the specific principle it grounds.

**Corrections from the 2026-05-24 red-team pass:**

- Title restored to Rick's original spec: `Building excellent software (with Claude)` (sentence case, parenthetical). The prior version had drifted to title case with no parenthetical.
- §2 (Dogfood): overstated Anthropic's general practice. Prior text said "Anthropic's own engineering teams follow this practice" — too broad. Replaced with the specific context: Anthropic engineering tested Claude's tool design against their internal workspace. This is one example, not a company-wide policy.
- §3 (File the bug): quote from context engineering doc was slightly misrendered. Actual text describes "a technique where the agent regularly writes notes persisted to memory outside of the context window." Rewritten as a paraphrase rather than a quotation.
- §6 (multi-agent quote): prior version truncated to "making decisions about which directions to pursue." Full sentence is "making decisions about which directions to pursue based on intermediate findings." Restored.
- §4 (CI): "synthetic-leak gate" phrasing implied a dedicated subsystem. Reframed: it is one step in the CI suite in `.github/workflows/ci.yml`.
- §4 (CI): install/uninstall one-line assertion example removed. It illustrated UX, not constraint encoding, which is the section's actual thesis. The tests still exist in the repo; they are simply not the right example for this section.
- TL;DR effort column: placeholder-style cadences (Design phase / Ongoing / Per session) replaced with time-shaped values (1–2 hours at design / Every release / Every fix / etc.).
- §6 principle closer: tightened from two sentences to one. Prior: "build ranking logic with the same care you give detection logic. A correct finding ranked wrong is a UX problem that erodes confidence in the whole tool." — the second sentence was doing the work; the first was advice-fortune-cookie.
- §4 principle closer: tightened. Removed "tests are how you delegate memory to the system" as a standalone framing line — the section makes this case well enough without a slogan.
- Added "When these disciplines are wrong" section before the closing section. A case study without counterargument is a sales pitch.
- Scanner issues #9 and #15 on watsonrm/tokenmin-scanner were edited to remove personal repro details (specific plan name, exact subagent counts, tool call volumes, per-workflow lists) that had leaked into the public issue bodies. The technical pattern descriptions are preserved; only the personal specifics are removed. The article itself did not contain this data, but the linked issues did.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. See [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
