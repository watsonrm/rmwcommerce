# The Claude Code Workflow Optimizer

**A curated compilation of Claude Code best practices, ranked by real-world ROI.**

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's official Claude Code documentation — see [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

If you spend more than an hour a day in Claude Code, the patterns here will typically:

- Reduce token waste from bloated context and rework loops
- Eliminate most "wrong-output, do-it-again" correction cycles
- Let you safely run more work in parallel without losing track

### Where to spend your time, in priority order

Most readers should fix the first two and stop. They produce the bulk of the gains.

| # | Practice | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | **Context discipline** — `/clear` between tasks, `/compact` with focus around the 50% mark | Compounds every turn. Anthropic's docs state directly: *"LLM performance degrades as context fills."* A bloated context burns tokens on irrelevant history and drives wrong output. | 30 sec per task switch |
| **2** | **`CLAUDE.md` hygiene** — keep under 200 lines, prune on a schedule | Loads on every session. The official docs state: *"target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."* Past the threshold, instructions get ignored. | 20 min once, 5 min quarterly |
| **3** | **Verification-first workflow** — write the test, screenshot, or success criterion before asking for code | Anthropic calls this *"the single highest-leverage thing you can do."* Claude *"performs dramatically better when it can verify its own work."* Cuts correction rounds per task. | Upfront per task |
| **4** | **Plan Mode for ambiguous work** — `Shift+Tab` to cycle into it | Separates "what should we build" from "build it." Prevents cascading misunderstandings in multi-file changes. | 2 min per complex task |
| **5** | **Subagents for noisy investigation** — large codebase reads, log analysis, test suite parsing | Runs in a separate context. Your main session never sees the noise. | 5 min one-time setup |
| **6** | **Git worktree fleets** — parallel sessions on isolated branches | Real but narrower payoff. Only matters if you're juggling 3+ active branches at once. Don't start here. | Per-task |

Pick model tier deliberately too (covered in [Pillar 2](#pillar-2-model-routing)) — Sonnet handles the bulk of daily work; reach for Opus on hard architecture or stateful debugging.

---

## How to use this

Open a fresh Claude Code session in your project. Paste this document into the chat along with your `CLAUDE.md` (if you have one) and a short description of how you currently use the tool. Then run:

> Analyze my Claude Code workflows against this guide. Identify my top three sources of token waste, evaluate how I'm routing between models, and give me concrete changes to my `CLAUDE.md` and CLI usage that would reduce rework and cut token spend. Be specific.

Claude will produce a customized audit and punch list.

---

## Pillar 1: Context and configuration discipline (highest ROI)

This pillar is where the bulk of the gains live. Do this before anything else.

### 1. Treat the context window like RAM

Anthropic's official docs are explicit about the constraint driving every other best practice: *"Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills."* ([source](https://code.claude.com/docs/en/best-practices)) The docs continue: *"LLM performance degrades as context fills. When the context window is getting full, Claude may start 'forgetting' earlier instructions or making more mistakes."*

**Execution:**

- **Track it.** Run `/context` to see what's currently using space.
- **Compact proactively.** Run `/compact` manually around the 50% mark — mid-session summaries preserve more detail than last-minute ones. Use the focus argument to direct what survives: `/compact focus on the API changes` ([source](https://code.claude.com/docs/en/best-practices)).
- **Clear between unrelated tasks.** `/clear` resets the conversation. When you switch from a backend route to frontend styling, run it. Don't let yesterday's debugging session pay rent on today's work.

### 2. Cap `CLAUDE.md` at 200 lines

Anthropic's official memory docs are explicit: *"target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."* ([source](https://code.claude.com/docs/en/memory)) The troubleshooting section adds: *"Files over 200 lines consume more context and may reduce adherence."*

For a deeper treatment of how context bloat manifests as noise in your terminal output — and the full set of noise sources and filtering tactics — see [Why Is Claude Code So Noisy?](claude-code-noise.md).

Structuring your `CLAUDE.md` and packaging recurring workflows as skills is also the move from Rung 1 to Rung 2 on [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — the point where ad-hoc prompts become reusable, versioned artifacts.

**Execution:**

- Reserve `CLAUDE.md` for: environment commands you run constantly, syntax conventions, non-negotiable architectural rules, and pointers to where more detail lives.
- Move everything else to linked docs the model pulls on demand, or into **path-scoped rules** under `.claude/rules/` — these load only when matching files are open, so you get precision without the every-session tax.
- Use `.gitignore` (with the `respectGitignore` setting enabled) to keep Claude out of `node_modules/`, `dist/`, `build/`, and large log files. *Note: an earlier widely-circulated guide referenced a `.claudeignore` file — this is not an official Claude Code feature. Use `.gitignore` plus the settings flag.*

### 3. Verify before you generate

Anthropic's best practices page identifies this as *"the single highest-leverage thing you can do"*: *"Claude performs dramatically better when it can verify its own work, like run tests, compare screenshots, and validate outputs. Without clear success criteria, it might produce something that looks right but actually doesn't work. You become the only feedback loop, and every mistake requires your attention."* ([source](https://code.claude.com/docs/en/best-practices))

Break the loop by giving it something to verify against:

- Write the failing test first, then ask for the implementation.
- Capture the bug as a screenshot, then ask for the fix.
- State the expected log output, then ask for the change.

This is the single biggest quality lever in the tool. Permission prompts are part of the verification loop — they're the human checkpoint before an action executes. For tuning them without losing that verification value, see [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md).

---

## Pillar 2: Model routing

Once your context is clean, match the model to the task.

### 1. Pick the right tier

The official Claude Code docs describe three primary tiers, with Sonnet as the workhorse for most coding tasks. The effort parameter (covered below) gives you additional granularity within a model.

| Tier | Use it for | Avoid for |
| :--- | :--- | :--- |
| **Haiku** | File exploration, repo indexing, syntax lookups, bash one-liners, mechanical refactors, text formatting | Architectural design, stateful debugging |
| **Sonnet** | Multi-file code generation, business logic, code review, day-to-day driver | Leaving high effort on for trivial edits |
| **Opus** | Distributed-systems debugging, greenfield architecture, complex type-system work, hard algorithms | Reading logs, basic shell operations |

The subagent configuration docs confirm: Sonnet and Haiku are appropriate model choices for subagents running isolated tasks, while Opus carries more intelligence for complex reasoning. ([source](https://code.claude.com/docs/en/best-practices))

### 2. Use the effort parameter deliberately

The `effort` parameter controls how many tokens Claude spends on a response, trading thoroughness for speed and cost ([source](https://platform.claude.com/docs/en/build-with-claude/effort.md)). The named tiers are:

| Tier | Use it for |
| :--- | :--- |
| `low` | Subagent tasks, simple lookups, high-volume batch operations where latency matters most |
| `medium` | Default for most application work — balanced cost and quality |
| `high` | Default when parameter is omitted — complex reasoning, architectural decisions |
| `xhigh` | Advanced coding and long-horizon agentic work (Claude Opus 4.7) |
| `max` | Absolute maximum capability, no token constraints — cryptographic logic, financial math, or tasks where wrong-but-confident output is costly |

The API parameter is `output_config: { effort: "medium" }` — it is a named string value, not a numeric one. *Note: earlier guides referenced `/effort 85` as a magic number — this does not correspond to any feature in the official Claude Code or Claude API.*

### 3. Delegate noisy work to subagents

Subagents are configured under `.claude/agents/` and managed via the `/agents` slash command ([source](https://code.claude.com/docs/en/best-practices)). They run in their own context, so verbose work — recursive scans, large log parses, Playwright test runs — never pollutes your main session. For the full treatment of subagents as a noise-reduction tactic — including the four noise sources and the complete filtering framework — see [Why Is Claude Code So Noisy?](claude-code-noise.md). The parent only sees the structured summary. The best practices docs describe a Writer/Reviewer pattern where a fresh subagent context improves code review quality because the reviewer hasn't been biased by the code it just wrote. Using Claude Code subagents this way is Rung 2.5 on the autonomy scale — packaged like a skill, autonomous enough to run unsupervised for a scoped task; [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) covers when this pattern graduates into a full Rung 3 agent with its own decision loop.

---

## Pillar 3: Parallelism and scale (advanced)

Reach for this pillar only when the first two are dialed in.

### 1. Git worktree fleets

Anthropic officially endorses this pattern: *"Anthropic recommends using worktrees to run separate CLI sessions in isolated git checkouts."* ([source](https://code.claude.com/docs/en/best-practices))

**When it pays off:** You're shipping multiple features in parallel, running experiments on independent branches, or maintaining several long-running investigations at once.

**When it doesn't:** You're doing one task at a time. The setup overhead exceeds the gain.

**Execution:**

- `git worktree add ../my-feature feature-branch`
- Launch a fresh Claude Code session in each worktree.
- Cap yourself at 3–5 concurrent sessions. Beyond that, you can't actually track what's happening.

### 2. Skills and MCP for recurring work

These two patterns are under-emphasized in most Claude Code tips content and worth knowing:

- **Skills** — for recurring workflows (API testing, database migrations, security review), define a Skill rather than re-explaining the process every session. Skills load on demand without bloating `CLAUDE.md`. ([source](https://code.claude.com/docs/en/best-practices))
- **MCP servers** — for any external service you talk to repeatedly (GitHub, Slack, databases, internal APIs), an MCP server eliminates the token cost of explaining HTTP and parsing responses. Claude calls the service natively.

Both are documented in the official Claude Code docs.

---

## Pillar 4: Density of expression

When Claude is doing engineering work, conversational filler is operational waste. Push it from assistant mode into execution mode.

1. **Command, don't ask.** Replace *"explain how to implement X"* with *"give me a minimal, production-ready implementation of X. No commentary."*
2. **Demand structured output.** Specify the shape — JSON, a code block only, a key-value list — in the prompt itself.
3. **Scope by coordinate.** Vague: *"look around the auth files and find the error."* Precise: *"Fix the session-expiration edge case in `src/auth/session.ts` lines 42–68."*
4. **Use `@file` to reference, not `read this file`.** `@src/api.ts` is more token-efficient than describing the file or asking Claude to read it from scratch.

If you're starting to wonder when Claude Code's single-session pattern stops being enough — when you want work to happen without you in the loop — read [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md). If you've decided to build a multi-agent system at the API level, [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) is the architecture playbook.

---

## Self-audit template

Copy this, fill it in, and feed it back to Claude with the prompt at the top of this doc.

### Environment
1. **Primary stack:** [e.g., TypeScript / Next.js / Go]
2. **Project size:** [e.g., 50k LOC, monorepo, microservices]
3. **Tooling:** [Claude Code CLI, Desktop, which MCPs are wired up]

### Current habits
- How long do your average Claude sessions last before `/clear` or a fresh chat?
  > [Your answer]
- Do you use Plan Mode before edits, or let Claude write files directly?
  > [Your answer]
- Paste your current `CLAUDE.md`:
  ```markdown
  [Paste here]
  ```

### Token burn profile
- Which workflows feel like they spike cost or fill the context window fastest?
  > [Your answer]

---

---

## Want the runnable form?

The operational core of this guide is packaged as a Claude Code skill: [`skills/claude-code-optimizer/`](skills/claude-code-optimizer/). Drop that folder into `~/.claude/skills/` and Claude will load it on demand when the trigger phrases in the SKILL.md frontmatter match what you're asking.

---

## Sources & attribution

This guide is a curated compilation. The underlying techniques originate from Anthropic's official Claude Code documentation. Every technical claim above has been verified against a primary source.

**Primary sources (Tier 1 — official Anthropic documentation with direct quotes):**

- Anthropic Engineering — *Claude Code Best Practices*: https://www.anthropic.com/engineering/claude-code-best-practices
- Claude Code docs — *Best Practices* (the canonical guidance on context management, verification, subagents, and worktrees): https://code.claude.com/docs/en/best-practices
- Claude Code docs — *Memory / CLAUDE.md* (source for the 200-line target and adherence guidance): https://code.claude.com/docs/en/memory
- Claude Code docs — *How Claude Code Works*: https://code.claude.com/docs/en/how-claude-code-works
- Claude Code docs — *Permissions*: https://code.claude.com/docs/en/permissions
- Claude Code docs — *Quickstart*: https://code.claude.com/docs/en/quickstart
- Claude API — *Effort Parameter* (source for named effort tiers: `low`, `medium`, `high`, `xhigh`, `max`): https://platform.claude.com/docs/en/build-with-claude/effort.md

**Supporting sources (Tier 2 — primary source, contextual):**

- Lenny's Newsletter — interview with Boris Cherny (creator of Claude Code): https://www.lennysnewsletter.com/p/head-of-claude-code-what-happens
- Anthropic Webinars — *Claude Code for Service Delivery*: https://www.anthropic.com/webinars/claude-code-service-delivery

**Corrections from prior circulating versions:** Earlier guides have referenced `claude --bare`, `.claudeignore`, and `/effort 85` as official features. None of these exist in Claude Code as of publication. Use `.gitignore` with the `respectGitignore` setting, and the named `effort` tiers (`low`/`medium`/`high`/`xhigh`/`max`) via the `output_config` API parameter. Earlier versions of this guide stated a 40–60% token savings figure without a primary-source citation — that figure has been removed; the official docs confirm the qualitative dynamic (context bloat degrades output and burns tokens) without publishing a specific percentage.

**Compilation, ranking, and commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or have a sharper pattern to add? Open an issue or PR.
