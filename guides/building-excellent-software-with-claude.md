# Building Excellent Software (with Claude)

**A real case study: what disciplines you have to apply to a Claude-built artifact to get it from working to production-grade.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Technical claims are grounded in the public source repositories and Anthropic documentation cited throughout — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- The tokenmin v0.12.1 → v0.12.5 build happened in roughly 12 hours of focused work. The code is public. You can read every decision.
- "Claude built it" is not a quality guarantee — it's a starting point. The disciplines in this article are what close the gap.
- This isn't about software development specifically. Every one of these lessons applies to any consequential artifact you build with Claude's help: a proposal, an analysis, an automation, a report.
- If you take nothing else: the metric that seems right can be the most dangerous one. Fix the framing before you fix the calculation.

### Where to spend your time, in priority order

| # | Discipline | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | Dogfood relentlessly | A spec review never catches what five minutes of real use catches | Ongoing |
| **2** | File the bug, then fix it | Design clarity before code; the issue is the spec | Per session |
| **3** | Be honest about cost and benefit | Technically correct and contextually wrong is worse than no metric | Design phase |
| **4** | Encode every constraint as a test | Claude doesn't remember constraints across sessions — the test does | Per constraint |
| **5** | Red-team your own work | Your threat model has more gaps than you think, and Claude will find them if you ask | Pre-release |
| **6** | Check the ranking, not just the output | An accurate finding ranked #1 when it shouldn't be is a UX problem | Per release |
| **7** | Build for survival | Software that only works while you're watching isn't software yet | Architecture |

Most readers should absorb the first three and stop. The rest matter, but rows 1–3 address the failure modes that actually ship.

---

## How to use this guide

This guide is the reasoning. The companion skill at [`skills/building-excellent-software/`](../skills/building-excellent-software/) is the live coach.

Install it once:

```bash
# from a clone of this repo
cp -r skills/building-excellent-software ~/.claude/skills/
```

Then describe your build to Claude — what you're building, where you are in the process, what's going wrong — and say one of these:

> "Apply the excellent software checklist to this"
> "Where am I on the dogfood-to-production ladder?"
> "Red-team what I just built"

Claude will load the skill and work through the relevant disciplines against your actual artifact. The article below is the reasoning behind each discipline. The skill is how you apply them.

---

## The case study: tokenmin v0.12.1 → v0.12.5

Tokenmin is a Claude usage audit tool — it scans your local Claude session history, anonymizes it, and surfaces where you're wasting tokens or spending in the wrong places. The public scanner is open source at [github.com/watsonrm/tokenmin-scanner](https://github.com/watsonrm/tokenmin-scanner) under Apache-2.0.

The v0.12.1 → v0.12.5 sprint covered roughly 12 hours of focused work. Every decision is traceable to a filed issue or a commit on main. That traceability is part of the discipline — not a post-hoc documentation exercise.

This article pulls from what actually happened during that sprint. Where a claim is grounded in a public issue or a specific test, I link it. Where I'm summarizing my own working method, I say so.

---

## 1. Dogfood relentlessly

The only honest source of UX feedback is using your own artifact on your own real work.

During the tokenmin sprint, every release got installed on my actual laptop within minutes of the commit landing on main. Not deployed to staging. Not run against synthetic fixtures. Installed as a real user would install it, against my real `~/.claude/` session history.

This caught things no spec review would have caught. The install output was noisy — 24 lines of terminal output before the tool even did anything meaningful. That's not a number I got from analyzing the install script. That's a number I got from watching my own terminal fill up and thinking "this is too much." The fix was a CI guard that asserts install completes in five lines or fewer. The spec review would have said "installation should be quiet." The dogfood session said "here are the 24 lines."

The second thing dogfooding caught was the model routing signal. Tokenmin fired `model_overspend` as its top finding on my setup — "100% Opus, route to Sonnet." The finding was factually accurate about the main session. But I run 16 explicitly-routed subagents: 7 on Haiku, 9 on Sonnet, 0 inheriting from the main session. The subagent routing I'd already done was invisible to the detector. The main session is 100% Opus on purpose — it handles judgment work. The recommendation to route to Sonnet was wrong for my setup. ([scanner #9](https://github.com/watsonrm/tokenmin-scanner/issues/9))

Neither of these would have shown up in a code review. They both showed up immediately in five minutes of use.

**The principle:** use your own artifact on your own real problem before you declare it done. "Real use" means the messy version — your actual data, your actual workflow, your actual reaction when something looks off. Synthetic inputs produce synthetic confidence.

---

## 2. File the bug, then fix it

When something goes wrong during dogfooding, the temptation is to fix it immediately. Resist this. File the issue first.

Filing forces you to articulate what's actually wrong — and more importantly, what the correct behavior should be. The issue is the spec. It defines acceptance before the fix begins, which means you know when you're done. A fix without an issue is a fix without a definition of done.

The tokenmin issue backlog during the v0.12.x sprint:

- [#1](https://github.com/watsonrm/tokenmin-scanner/issues/1) — `models_used_families` values reported as 0 because of an integer-flooring bug on the percentage calculation. Filed with exact repro. Closed after fix + test.
- [#2](https://github.com/watsonrm/tokenmin-scanner/issues/2) — cost framing misleading for Pro/Max subscription users (the $7,622 moment — more on this in section 5).
- [#3](https://github.com/watsonrm/tokenmin-scanner/issues/3) — savings shown in dollars per month doesn't apply to flat-fee plan users.
- [#5](https://github.com/watsonrm/tokenmin-scanner/issues/5) — low-impact findings diluting the main report.
- [#6](https://github.com/watsonrm/tokenmin-scanner/issues/6) — `tokenmin show <id>` leaks dollar amounts on Pro/Max plans.
- [#7](https://github.com/watsonrm/tokenmin-scanner/issues/7) — audit doesn't disclose subagent-model invisibility.
- [#8](https://github.com/watsonrm/tokenmin-scanner/issues/8) — `no_global_claude_md` and `no_custom_agents` fire when the user has a project-scoped setup that makes them irrelevant.
- [#9](https://github.com/watsonrm/tokenmin-scanner/issues/9) — `model_overspend` fires as the top finding even when the user has already optimized via subagent routing.

Each issue has a description of the problem, a repro path, and a fix sketch. That's the spec. The fix that follows is constrained by the issue, not by whatever seemed easy to implement. This forces a clear answer to "what does fixed look like?" before a line of code changes.

The secondary benefit: when the fix goes wrong, you have a clear record of what you were trying to do. Claude doesn't carry context across sessions. The issue backlog does.

---

## 3. Red-team your own work

Building with Claude creates a specific risk: Claude will build what you ask for. If you ask for "a telemetry system," you'll get a telemetry system. If you don't ask about the threat model, Claude won't invent one.

The tokenmin security bar was explicit: "Glasswing-level security" — meaning the kind of care a well-run security consultancy would apply to a new product collecting user data.

After the v0.12.x build, I ran a dedicated red-team pass. Here's what it found and fixed:

**Identifier hashing.** The initial design used SHA-256 to anonymize file paths and identifiers. SHA-256 is not enough: an adversary who guesses that a path like `~/.ssh/known_hosts` is likely present can precompute its hash and reverse-identify it. The fix was HMAC-SHA256 with a 32-byte salt generated on first run and stored at `~/.tokenmin/.salt` (chmod 0600). The salt means precomputed tables fail. This is documented in [SECURITY.md](https://github.com/watsonrm/tokenmin-scanner/blob/main/SECURITY.md) and verifiable in the source.

**ReDoS defense.** The anonymizer runs regex patterns against potentially adversarial content from session files. A carefully crafted input string can cause exponential backtracking in a naive regex engine — a denial-of-service against the user's own machine. The fix was a 64 KiB input cap: every string is truncated before the scrubber sees it. Bad lines are dropped, not raised on.

**ANSI injection.** A session file with planted ANSI escape sequences in project or file names could hijack the user's terminal when `tokenmin watch` rendered them. The fix was a `_strip_ctl()` helper that removes ANSI CSI/OSC sequences and C0/C1 control characters before rendering any displayed string. There's a property test covering this in the scrubber suite.

**Token handling in git config.** The F&F installer wrote authentication tokens to `.git/config`, where `git config --list` would expose them. The fix was a per-install git credential helper file (chmod 0600) that keeps the token out of the config entirely.

**Open-source as a trust mechanism.** The scanner — the code that decides what leaves your machine — is fully open source under Apache-2.0. Not because open source makes software more secure by default, but because "trust me" is not a threat model. Anyone can diff their installed copy against the public repo. That's the stated deal in the README: "Read it. Diff it against your install. Then decide if you trust the bargain."

**The GitHub PAT incident.** When I attempted to embed a PAT in the public repo for telemetry routing, GitHub's push protection blocked the commit. The right response was not to encode or obfuscate the token to evade the protection ("ick" was my exact word at the time). It was to go private on the telemetry repo and use GitHub Pro. The protection was correct. Evading it would have been a security regression dressed up as an implementation shortcut.

**The principle:** Claude will implement what you specify. The threat model is your job. Ask Claude to red-team what it built — it's good at this — but give it a specific bar to work against, not just "check for security issues." "What would a researcher at a security consultancy flag in this?" produces different results than "is this secure?"

---

## 4. CI guards every behavior you care about

Claude does not remember constraints across sessions. A decision made in session 1 ("install output must be quiet") does not survive to session 12 without explicit encoding. The test suite is the only reliable mechanism for persistent constraints.

The tokenmin test structure at v0.12.5:

**56 tests across 5 suites.** Each suite guards a specific behavioral contract:

- `test_scrubber.py` (15 tests) — idempotent scrub, secret-pattern coverage (Anthropic, OpenAI, Stripe, JWT, npm, Google, AWS, GitHub, Slack tokens, PEM blocks), ReDoS input cap, salt sensitivity and stability, HTTPS-only enforcement, snapshot file permissions.

- `test_uninstall.py` (5 tests) — asserts that uninstall produces exactly one line of output (`tokenmin 0.12.5 uninstalled`), that dev-tree safety prevents accidental `rm -rf` of a checkout, that idempotent re-run on an already-uninstalled system exits cleanly.

- `test_cost_framing.py` (18 tests) — asserts that Pro/Max plan reports contain no dollar amounts in the TL;DR or savings cards. Subscription users see quota stretch percentage, tokens, and hours instead. API/unknown plans continue showing dollars. Pricing loads from `engine/pricing.json`, not from hardcoded constants.

- `test_update_ux.py` (8 tests) — covers the `tokenmin update` command contract: `--check` doesn't pull, cache expires correctly, SHA comparison uses prefix (the short SHA from `_version_info()` must match against the 40-char full SHA from `git ls-remote`).

- `test_v0_12_4.py` (10 tests) — guards the four specific behaviors shipped in v0.12.4: low-impact findings filter, plan-aware cost framing on `tokenmin show`, subagent invisibility footnote in the `model_overspend` evidence, and project-scoped CLAUDE.md detection.

Every push to main runs all five suites across Python 3.10, 3.11, and 3.12. The CI configuration is [public](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/ci.yml).

There's also a **synthetic-leak gate** in CI: it builds a fake `~/.claude/` directory with planted client names and file paths, runs the scanner against it, and fails the build if any plaintext leaks through the anonymizer. This catches anonymization regressions that are easy to introduce when adding new scraper paths and nearly impossible to catch in a code review.

The mirror-parity check confirms the scanner files in the private F&F bundle are bit-identical to the public scanner repo. If they drift, CI fails.

**The principle:** tests are how you delegate memory to the system. When you discover a constraint during dogfooding, your first question should be "what test would have caught this?" Write that test, then write the fix. The test is the durable form of the lesson. The fix without the test just defers the regression.

---

## 5. Be honest about cost and benefit

This is the one that matters most for anyone building instrumentation, reporting, or any tool that puts a number in front of a user.

During the tokenmin F&F dogfood, the tool reported `$7,622 spent` over a 14-day window. The calculation was mathematically correct: input tokens + output tokens + cache reads + cache writes, priced at retail API rates. The problem was that I pay $200 per month for a Claude Max subscription, not $7,622.

The number was technically right and contextually wrong. For a metered API user, it's the right framing. For a flat-fee subscriber, it's a number that makes you distrust the tool before you've gotten any value from it. ([scanner #2](https://github.com/watsonrm/tokenmin-scanner/issues/2))

The v0.12.3 fix had two parts:

**E: Plan-aware framing.** Pro and Max reports no longer show dollar amounts in the TL;DR or savings cards. Instead they show quota stretch percentage, token volume, and time. The underlying API-equivalent cost is still computed — the math is right — but the framing matches what the user actually pays. API and unknown-plan users see dollars unchanged.

**C: Externalized pricing.** Before v0.12.3, model prices were hardcoded constants in source. When Anthropic changes pricing, every installed tokenmin was silently wrong until the user updated. The fix moved prices to `engine/pricing.json` with a `last_updated` field and a staleness warning threshold. A future auto-update mechanism can refresh the pricing file without requiring a software release.

The 18 tests in `test_cost_framing.py` guard both of these properties. The lead fixture comment explains the exact failure mode: "A user on Max who sees $7,622 spent is confused, then doubts the tool." That's the acceptance criterion. The test either passes or it doesn't.

**The principle:** when you put a metric in front of someone, you're making an implicit claim about what it means to them. A metric that's technically correct but contextually wrong is worse than no metric — it damages trust in everything else the tool says. The right question isn't "is this number accurate?" but "does this number mean what the user thinks it means?"

---

## 6. Time-to-value is the only metric users feel

Every interaction before the user has seen value is a tax. Prompts, warnings, confirmation dialogs, setup steps — all of them feel small in isolation and compound into an experience that people don't return to.

The tokenmin install target was: one command, one response, working state.

```
curl --proto '=https' --tlsv1.2 -fsSL https://tokenmin.ai/install.sh | bash
```

Output on success:

```
tokenmin 0.12.5 installed → run: tokenmin
```

Uninstall:

```
tokenmin 0.12.5 uninstalled
```

The `tokenmin update` command bypasses the 24-hour cooldown for explicit user-initiated updates, reports the current and new version, and completes without confirmation prompts. The `--version` flag shows an "update available" hint when the local install is behind, so users know without having to check.

This maps to the same principle behind Anthropic's prompt caching design: perceived latency is a cost, and users feel it even when they can't quantify it. ([Anthropic prompt caching docs](https://platform.claude.com/docs/en/build-with-claude/prompt-caching)) The analogy isn't perfect — install UX and API latency are different problems — but the underlying logic is the same: the time between a user deciding to try something and seeing evidence that it works determines whether they keep going.

The CI guard for install UX asserts that install completes in five lines of stdout. If a future change makes the install noisy again, the build fails. The constraint is encoded, not just documented.

**The principle:** time-to-value is the moment a user sees that the artifact does what you claimed. Every second before that moment is borrowed attention. Design for that moment first, then add everything else.

---

## 7. Don't trust the obvious recommendation

The `model_overspend` detector fired as the top finding on my Max account with a "critical" severity rating: 100% Opus across 52 sessions, $7,055/month recoverable, confidence 55%. The recommendation was to route mechanical work to Sonnet.

For most users, this is good advice. For my setup, it was wrong in a specific way that didn't become obvious until I read the evidence carefully.

The detector looks at main-session model usage. My main session is 100% Opus on purpose — it handles synthesis, proposal drafting, meeting prep dispatch, and design decisions. The cheap-routing wins are realized at the subagent layer: 375 Agent tool calls over 14 days, spread across 16 subagents, 7 on Haiku, 9 on Sonnet, 0 inheriting from the main session. The detector couldn't see any of that. It saw "100% Opus" and fired. ([scanner #9](https://github.com/watsonrm/tokenmin-scanner/issues/9))

v0.12.4 added a disclaimer to the `model_overspend` evidence text: "this only measures your main session." That was honest but insufficient — the finding still ranked first with a critical severity label. The disclaimer is a footnote on a ranking that was wrong.

This is filed as an open issue. The right fix isn't just a disclaimer; it's making the detector context-aware: high subagent call volume should downgrade confidence substantially, because a user with 375 Agent calls in 14 days has already separated cheap work from judgment work.

The same principle applies to the `no_global_claude_md` and `no_custom_agents` detectors — both fired on my setup, both are wrong because I have project-scoped configuration that makes them irrelevant. ([scanner #8](https://github.com/watsonrm/tokenmin-scanner/issues/8))

**The principle:** a detector that's right for the median user can be wrong for sophisticated users in ways that make the tool less useful for exactly the people who would benefit most. When you build recommendations, build the ranking logic with the same care you'd give the detection logic. A correct finding ranked wrong is a UX problem.

---

## 8. Build for survival

At the end of the v0.12.5 sprint, I filed scanner #15: 15 candidate detectors, each grounded in a specific Anthropic source, each with a detection signal derivable from the tokenmin snapshot schema. ([scanner #15](https://github.com/watsonrm/tokenmin-scanner/issues/15)) The research for that issue came from a single in-foreground session of reading Anthropic docs and engineering posts. One session, 15 candidates.

The problem with that approach: it only runs when I'm watching. The next useful research session happens when I remember to run it. That's not a system — it's a habit, and habits degrade.

The v0.12.5 commit that shipped alongside the sprint also added a GitHub Actions workflow at [`.github/workflows/detector-research.yml`](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/detector-research.yml). It runs in the cloud every Monday at 13:23 UTC. It watches Anthropic's news feed, engineering blog, Claude Code releases, and cookbook commits for new posts. It files a GitHub issue for each newly-seen item so I can triage it as a detector candidate or not. The state is committed back to the repo after each run so it doesn't re-file what it's already seen.

The workflow survives laptop shutdown, network outages on my end, and weeks where I don't think about tokenmin at all. The research continues without me.

This is the distinction between using Claude to do work and building software with Claude that does work. The former requires you in the loop every time. The latter runs the relevant parts without you.

The workflow itself is about 60 lines of YAML and a Python script in `bin/detector-research.py`. Claude wrote the first version in a single session from a spec I dictated. The spec was: "watch these sources, file issues for new posts, track what you've seen so you don't duplicate." The implementation is verifiable in the public repo.

**The principle:** software that requires a human in the loop for routine operation isn't software — it's an elaborate prompt. Ask yourself, for any recurring task your artifact handles: what happens when I'm unavailable for a week? If the answer is "nothing runs," build the automation before you declare the artifact done.

---

## What this means for non-developers

Every discipline in this article has a non-software version.

Dogfooding is using your own deliverable as a real user before sending it to a client. File-then-fix is writing a clear description of what's wrong and what correct looks like before touching the draft. Red-teaming is asking Claude to take the opposing view on your proposal before you present it. Tests are checklists with acceptance criteria that get rechecked on every revision. Cost-and-benefit honesty is making sure the metric in your report means what your client thinks it means.

The version-number-specific details in this article are specific to tokenmin. The disciplines are not.

Claude is good at building things quickly. The gap between "quickly built" and "production-grade" is the set of disciplines above applied consistently across a real build. None of them require programming knowledge. All of them require the willingness to slow down at the moment when it's tempting to ship.

---

## Sources & Attribution

**Primary sources — data and first-party documentation:**

- [tokenmin-scanner public repo](https://github.com/watsonrm/tokenmin-scanner) — Apache-2.0 scanner, anonymizer, CLI, tests, CI
- [scanner #1](https://github.com/watsonrm/tokenmin-scanner/issues/1) — `models_used_families` flooring bug (closed)
- [scanner #2](https://github.com/watsonrm/tokenmin-scanner/issues/2) — cost framing misleading for Pro/Max users
- [scanner #3](https://github.com/watsonrm/tokenmin-scanner/issues/3) — savings shown in $/mo for flat-fee plans
- [scanner #5](https://github.com/watsonrm/tokenmin-scanner/issues/5) — low-impact findings dilute main report
- [scanner #6](https://github.com/watsonrm/tokenmin-scanner/issues/6) — `tokenmin show` leaks dollars on Pro/Max
- [scanner #7](https://github.com/watsonrm/tokenmin-scanner/issues/7) — subagent-model invisibility not disclosed
- [scanner #8](https://github.com/watsonrm/tokenmin-scanner/issues/8) — project-scoped setup not detected
- [scanner #9](https://github.com/watsonrm/tokenmin-scanner/issues/9) — `model_overspend` ranking wrong for subagent-heavy users
- [scanner #15](https://github.com/watsonrm/tokenmin-scanner/issues/15) — 15 v0.12.6+ detector candidates
- [tokenmin-scanner SECURITY.md](https://github.com/watsonrm/tokenmin-scanner/blob/main/SECURITY.md) — threat model, HMAC design, ReDoS defense, transport defaults
- [tokenmin-scanner CI workflow](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/ci.yml) — scrubber, uninstall, cost-framing, mirror-parity tests
- [detector-research workflow](https://github.com/watsonrm/tokenmin-scanner/blob/main/.github/workflows/detector-research.yml) — weekly cloud research agent
- [Anthropic: Prompt caching](https://platform.claude.com/docs/en/build-with-claude/prompt-caching) — TTL design, latency-as-cost framing
- [Anthropic: Claude Code best practices](https://code.claude.com/docs/en/best-practices) — subagent routing, context hygiene
- [Anthropic: Built a multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) — parallel tool-use, agent architecture tradeoffs

**Corrections from prior circulating versions:**

The brief that seeded this article listed the issue count for the v0.12.x sprint as covering "#4-#8 (low-impact filter, show leaks dollars, subagent invisibility, project-scoped)." Issue #4 in the public repo is a pull request (the fix for #2), not a standalone issue. The correct issue numbers for those four items are #5, #6, #7, and #8. All four are linked above.

The brief cited "55 tests across 5 suites." The actual count at v0.12.5 is 56: 18 + 15 + 5 + 8 + 10 across the five files in `tests/`. The claim has been corrected throughout.

The brief mentioned an `install-smoke.yml` CI workflow in `watsonrm/tokenmin-site`. That repo is private; the workflow could not be independently verified. The CI claim in this article is limited to what's verifiable in the public `tokenmin-scanner` repo.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. See [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
