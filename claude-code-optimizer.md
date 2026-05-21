# The Claude Code Workflow Optimizer

**A curated compilation of Claude Code best practices, ranked by real-world ROI.**

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's public documentation and from Boris Cherny (creator of Claude Code) — see [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

If you spend more than an hour a day in Claude Code, the patterns here will typically:

- Cut token spend **40–60%** on a normal workday
- Eliminate most "wrong-output, do-it-again" rework loops
- Let you safely run more work in parallel without losing track

### Where to spend your time, in priority order

Most readers should fix the first two and stop. They produce the bulk of the gains.

| # | Practice | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | **Context discipline** — `/clear` between tasks, `/compact` with focus around the 50% mark | Compounds every turn. A bloated context degrades all output quality and burns tokens on irrelevant history. | 30 sec per task switch |
| **2** | **`CLAUDE.md` hygiene** — keep under 200 lines, prune ruthlessly | Loads on every session. Past ~200 lines, adherence actually *drops* per Anthropic's own docs. | 20 min once, 5 min quarterly |
| **3** | **Verification-first workflow** — write the test, screenshot, or success criterion before asking for code | Cuts 1–3 correction rounds per task. The biggest hidden token sink isn't generation — it's redoing wrong output. | Upfront per task |
| **4** | **Plan Mode for ambiguous work** — `Shift+Tab` to cycle into it | Separates "what should we build" from "build it." Prevents cascading misunderstandings in multi-file changes. | 2 min per complex task |
| **5** | **Subagents for noisy investigation** — large codebase reads, log analysis, test suite parsing | Runs in a separate context. Your main session never sees the noise. | 5 min one-time setup |
| **6** | **Git worktree fleets** — parallel sessions on isolated branches | Real but narrower payoff. Only matters if you're juggling 3+ active branches at once. Don't start here. | Per-task |

Pick model tier deliberately too (covered in [Pillar 2](#pillar-2-model-routing)) — Sonnet handles ~90% of work; reach for Opus only on hard architecture or stateful debugging.

---

## How to use this

Open a fresh Claude Code session in your project. Paste this document into the chat along with your `CLAUDE.md` (if you have one) and a short description of how you currently use the tool. Then run:

> Analyze my Claude Code workflows against this guide. Identify my top three sources of token waste, evaluate how I'm routing between models, and give me concrete changes to my `CLAUDE.md` and CLI usage that would cut token spend 40–60% without hurting output quality.

Claude will produce a customized audit and punch list.

---

## Pillar 1: Context and configuration discipline (highest ROI)

This pillar is where 80% of the gains live. Do this before anything else.

### 1. Treat the context window like RAM

The official Anthropic docs are explicit: *"Most best practices are based on one constraint: Claude's context window fills up fast, and performance degrades as it fills."* ([source](https://code.claude.com/docs/en/best-practices.md))

**Execution:**

- **Track it.** Run `/context` to see what's currently using space.
- **Compact proactively.** Run `/compact` manually around the 50% mark — mid-session summaries preserve more detail than last-minute ones. Use the focus argument to direct what survives: `/compact focus on the API changes` ([source](https://code.claude.com/docs/en/best-practices.md)).
- **Clear between unrelated tasks.** `/clear` resets the conversation. When you switch from a backend route to frontend styling, run it. Don't let yesterday's debugging session pay rent on today's work.

### 2. Cap `CLAUDE.md` at 200 lines

Anthropic's official guidance: *"target under 200 lines per `CLAUDE.md` file. Longer files consume more context and reduce adherence."* ([source](https://code.claude.com/docs/en/memory.md))

**Execution:**

- Reserve `CLAUDE.md` for: environment commands you run constantly, syntax conventions, non-negotiable architectural rules, and pointers to where more detail lives.
- Move everything else to linked docs the model pulls on demand, or into **path-scoped rules** under `.claude/rules/` — these load only when matching files are open, so you get precision without the every-session tax.
- Use `.gitignore` (with the `respectGitignore` setting enabled) to keep Claude out of `node_modules/`, `dist/`, `build/`, and large log files. *Note: an earlier widely-circulated guide referenced a `.claudeignore` file — this is not an official Claude Code feature. Use `.gitignore` plus the settings flag.*

### 3. Verify before you generate

Claude performs dramatically better when it can check its own work. Without an explicit success criterion it produces plausible-but-wrong output, which triggers a correction round, which adds tokens and noise, which degrades the next round. Break the loop by giving it something to verify against:

- Write the failing test first, then ask for the implementation.
- Capture the bug as a screenshot, then ask for the fix.
- State the expected log output, then ask for the change.

This is the single biggest quality lever in the tool.

---

## Pillar 2: Model routing

Once your context is clean, match the model to the task.

### 1. Pick the right tier

Official Anthropic guidance is light here, but the rough shape is consistent across their docs and Boris Cherny's interviews:

| Tier | Use it for | Avoid for |
| :--- | :--- | :--- |
| **Haiku** | File exploration, repo indexing, syntax lookups, bash one-liners, mechanical refactors, text formatting | Architectural design, stateful debugging |
| **Sonnet** | Multi-file code generation, business logic, code review, day-to-day driver | Leaving extended reasoning on for trivial edits |
| **Opus** | Distributed-systems debugging, greenfield architecture, complex type-system work, hard algorithms | Reading logs, basic shell operations |

The official quickstart confirms: *"Sonnet handles most coding tasks well. Opus provides stronger reasoning for complex architectural decisions."* ([source](https://code.claude.com/docs/en/quickstart.md))

### 2. Use extended reasoning sparingly

The reasoning effort parameter exists at the API level with named tiers: `low`, `medium`, `high`, `xhigh`, `max` ([source](https://platform.claude.com/docs/en/build-with-claude/effort.md)).

- **`low`** for boilerplate, simple test updates, formatting passes.
- **`medium`** as a default for most application work.
- **`high` / `xhigh`** for multi-step architectural decisions or hard debugging.
- **`max`** only for cryptographic logic, financial math, or anything where wrong-but-confident is catastrophic.

*Note: an earlier guide referenced `/effort 85` as a magic number — the parameter is named, not numeric, and `85` does not map to anything in the official API.*

### 3. Delegate noisy work to subagents

Subagents are configured under `.claude/agents/` and managed via the `/agents` slash command ([source](https://code.claude.com/docs/en/best-practices.md)). They run in their own context, so verbose work — recursive scans, large log parses, Playwright test runs — never pollutes your main session. The parent only sees the structured summary.

---

## Pillar 3: Parallelism and scale (advanced)

Reach for this pillar only when the first two are dialed in.

### 1. Git worktree fleets

Anthropic officially endorses this pattern: *"Anthropic recommends using worktrees to run separate CLI sessions in isolated git checkouts."* ([source](https://code.claude.com/docs/en/best-practices.md))

**When it pays off:** You're shipping multiple features in parallel, running experiments on independent branches, or maintaining several long-running investigations at once.

**When it doesn't:** You're doing one task at a time. The setup overhead exceeds the gain.

**Execution:**

- `git worktree add ../my-feature feature-branch`
- Launch a fresh Claude Code session in each worktree.
- Cap yourself at 3–5 concurrent sessions. Beyond that, you can't actually track what's happening.

### 2. Skills and MCP for recurring work

These two patterns are under-emphasized in most "Claude Code tips" content and worth knowing:

- **Skills** — for recurring workflows (API testing, database migrations, security review), define a Skill rather than re-explaining the process every session. Skills load on demand without bloating `CLAUDE.md`.
- **MCP servers** — for any external service you talk to repeatedly (GitHub, Slack, databases, internal APIs), an MCP server eliminates the token cost of explaining HTTP and parsing responses. Claude calls the service natively.

Both are documented in the official Claude Code docs.

---

## Pillar 4: Density of expression

When Claude is doing engineering work, conversational filler is operational waste. Push it from assistant mode into execution mode.

1. **Command, don't ask.** Replace *"explain how to implement X"* with *"give me a minimal, production-ready implementation of X. No commentary."*
2. **Demand structured output.** Specify the shape — JSON, a code block only, a key-value list — in the prompt itself.
3. **Scope by coordinate.** Vague: *"look around the auth files and find the error."* Precise: *"Fix the session-expiration edge case in `src/auth/session.ts` lines 42–68."*
4. **Use `@file` to reference, not `read this file`.** `@src/api.ts` is more token-efficient than describing the file or asking Claude to read it from scratch.

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

## Sources & attribution

This guide is a curated compilation. The underlying techniques originate from Anthropic's official documentation and from public talks and interviews with Boris Cherny, creator and head of Claude Code at Anthropic. Every technical claim above has been verified against an authoritative source.

**Primary sources:**

- Anthropic Engineering — *Claude Code Best Practices*: https://www.anthropic.com/engineering/claude-code-best-practices
- Claude Code docs — *Best Practices*: https://code.claude.com/docs/en/best-practices.md
- Claude Code docs — *Memory / CLAUDE.md*: https://code.claude.com/docs/en/memory.md
- Claude Code docs — *How It Works*: https://code.claude.com/docs/en/how-claude-code-works.md
- Claude Code docs — *Permissions*: https://code.claude.com/docs/en/permissions.md
- Claude Code docs — *Quickstart*: https://code.claude.com/docs/en/quickstart.md
- Claude API — *Effort Parameter*: https://platform.claude.com/docs/en/build-with-claude/effort.md
- Lenny's Newsletter — interview with Boris Cherny: https://www.lennysnewsletter.com/p/head-of-claude-code-what-happens
- Anthropic Webinars — *Claude Code for Service Delivery*: https://www.anthropic.com/webinars/claude-code-service-delivery

**Corrections from prior circulating versions:** Earlier guides have referenced `claude --bare`, `.claudeignore`, and `/effort 85` as official features. None of these exist in Claude Code as of publication. Use `.gitignore` with the `respectGitignore` setting, and the named `effort` tiers (`low`/`medium`/`high`/`xhigh`/`max`).

**Compilation, ranking, and commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or have a sharper pattern to add? Open an issue or PR.
