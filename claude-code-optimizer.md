# Claude Code Workflow Optimizer

A practical guide to getting more out of Claude Code — how to structure sessions, route between models, manage the context window, and run agents in parallel without bloating token spend.

I use Claude Code daily for client work at RMW Commerce. The patterns below are the ones that have actually moved the needle on speed, quality, and cost. Sharing it as a reference for anyone doing serious work in the tool.

---

## How to use this

Open a fresh Claude Code session in your project. Paste this entire document into the chat, along with your `CLAUDE.md` (if you have one) and a short description of how you currently use the tool. Then run this prompt:

> Analyze my Claude Code workflows against the standards in this guide. Identify my top three areas of token waste, evaluate how I'm routing between models, and give me concrete changes to my `CLAUDE.md` and CLI usage that would cut token spend 50–75% without hurting output quality.

Claude will produce a customized audit of your setup and a punch list of changes.

---

## Pillar 1: Architecture for agentic engineering

Treat Claude not as an interactive chat utility, but as a pool of programmable cognitive infrastructure. The shift is from "conversational trial-and-error" to "orchestrated execution pipelines."

### 1. Run a fleet of git worktrees

**The trap:** Keeping a single monolithic Claude Code session alive for days while juggling feature work, code reviews, and bug fixes. Conversation history snowballs and every turn pays a token tax on the whole accumulated context.

**The strategy:** Treat sessions like ephemeral compute processes. Run parallel, narrowly-scoped sessions across isolated directories that share the same git history via worktrees.

**Execution:**
- Split tasks into discrete worktrees.
- Spin up several concurrent Claude Code instances (3–5 terminal panes is a reasonable working volume), each with its own clean context window for one task.
- Rule of thumb: don't make one brain do every job. Run many clean, narrow brains in parallel.

### 2. Plan first, then execute

**The trap:** Letting Claude jump straight into multi-file diffs. If it misreads your architecture, you get cascading errors, CI failures, and thousands of output tokens spent rewriting its own work — all of it baked into the session history.

**The strategy:** Separate structural specification from mechanical execution.

**Execution:**
- Start complex work in Plan Mode (`Shift+Tab`, or an explicit planning phase).
- Iterate on the architectural plan — file paths, function signatures, implementation logic — until it's locked.
- Then flip to execution mode. Claude can usually one-shot the code generation once the plan is solid, eliminating the back-and-forth retry loop.

### 3. Treat the context window like RAM

**The trap:** Letting files read early in a session sit in memory indefinitely, or relying on auto-compaction only after the window is nearly full. Late compaction loses fidelity and forces Claude to re-derive logic it already had.

**The strategy:** Load, release, and compact context proactively at predictable thresholds.

**Execution:**
- **Proactive compaction.** Track context with `/context`. Run `/compact` manually around the **50%** mark — mid-session summaries are higher fidelity than last-minute ones.
- **Targeted compaction.** Direct what survives: `/compact Focus on core code samples, type definitions, and API contracts.`
- **The `/clear` habit.** When you switch tasks (backend route → frontend styling), run `/clear`. If you'll come back to the prior context, `/rename <name>` first, then `/resume <name>` later.

### 4. Audit your `CLAUDE.md` and tool list

**The trap:** Treating `CLAUDE.md` like a project wiki, or wiring up every MCP server you can find. A 5,000-token `CLAUDE.md` is a flat tax on every single interaction.

**The strategy:** Keep core configuration small and fast.

**Execution:**
- **Cap `CLAUDE.md` around 300–600 tokens.** Reserve it for environment commands, syntax conventions, and architectural rules you actually want enforced. Everything else belongs in linked docs the model can pull on demand.
- **`claude --bare` for utility work.** Skips `CLAUDE.md`, custom settings, and MCP schemas. Useful for one-off scripts or ad-hoc tasks where project rules don't matter.
- **`.claudeignore` aggressively.** Block `node_modules/`, `dist/`, `build/`, large log files, and anything else Claude has no business indexing. Every token spent scanning unedited files degrades signal-to-noise.

---

## Pillar 2: Model routing and reasoning calibration

Match task complexity to model tier and reasoning depth. Don't pay Opus prices for Haiku work.

### 1. Pick the right tier for the job

| Tier | Best for | Avoid for | Profile |
| :--- | :--- | :--- | :--- |
| **Haiku** | File exploration, repo indexing, syntax lookups, bash scripts, mechanical refactors, text formatting | Architectural design, stateful debugging | Low cost, fast |
| **Sonnet** | Multi-file code generation, business logic, standard code review, general daily driver | Leaving reasoning maxed out on trivial edits | Balanced, fits ~90% of work |
| **Opus / extended reasoning** | Distributed-systems debugging, greenfield architecture, complex type-system work, algorithm design | Reading logs, basic shell ops | Maximum depth, slower, higher burn |

### 2. Tune the reasoning window

Extended thinking helps on multi-step architectural problems and burns tokens on mundane ones.

- **`/effort 85`** is a useful default — high accuracy without circular reasoning loops.
- **`low` / `0`** for boilerplate, simple test updates, markdown reformatting. Forces direct execution.
- **`max`** only for high-ambiguity bugs, cryptographic logic, financial math, or anything where wrong-but-confident is catastrophic.

### 3. Use sub-agents for high-volume work

**The trap:** Running recursive scans, large log analyses, or cross-cutting migrations in your main shell. The verbose output pollutes your working context.

**The strategy:** Delegate noisy analytical work to single-use child agents that return only a structured summary.

**Execution:** Use `--agent` configurations to spawn sandboxed operations (a Playwright test run, a dependency audit, a log parse). The parent context never sees the noise — only the conclusion.

---

## Pillar 3: Code density — less prose, more output

When Claude is doing engineering work, conversational filler is operational waste. Push it from assistant mode into execution mode.

1. **Command, don't ask.** Replace *"explain how to implement X"* with *"give me a minimal, production-ready implementation of X with no commentary."*
2. **Demand structured output.** Specify the shape — JSON, a code block only, a key-value list — in the prompt.
3. **Scope by coordinate.** Vague: *"look around the auth files and find the error."* Precise: *"Fix the session-expiration edge case in `src/auth/session.ts` lines 42–68."*

---

## Self-audit template

Copy this section, fill it in, and feed it back to Claude to generate a customized optimization plan.

### Environment
1. **Primary stack:** [e.g., TypeScript / Next.js / Go]
2. **Project size:** [e.g., 50k LOC, monorepo, microservices]
3. **Tooling:** [e.g., Claude Code CLI, Desktop, which MCPs are wired up]

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
- Which workflows feel like they spike cost or blow the context window fastest? (deep debugging, dependency refactors, test-suite runs, etc.)
  > [Your answer]

---

*Curated by Rick Watson, RMW Commerce. If you find this useful or have improvements, open an issue or PR.*
