# The Claude Code Workflow Optimizer

**A curated compilation of Claude Code best practices, ranked by real-world ROI.**

*By [Rick Watson](https://rmwcommerce.com) · Published 2026-05-21 · Updated 2026-05-22*

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

The operational form of this guide is the Claude Code skill at [`skills/claude-code-optimizer/`](skills/claude-code-optimizer/). Install it once:

```bash
# from a clone of this repo
cp -r skills/claude-code-optimizer ~/.claude/skills/
```

Then describe your setup to Claude — project type, daily tasks, what feels slow or expensive — and say one of these (the skill's trigger phrases):

> Audit my Claude Code workflow.
> Optimize my Claude Code.
> Why is Claude Code burning so many tokens?
> Tune my setup.

Claude will load the skill on demand, walk through the diagnostic pillars (context, `CLAUDE.md`, model routing, verification, parallelism), find the first real smell, and prescribe one concrete fix to make next. The article below is the reasoning behind each pillar — read it for the *why*; the skill is the *how*.

---

## Pillar 1: Context and configuration discipline (highest ROI)

This pillar is where the bulk of the gains live. Do this before anything else.

### 1. Treat the context window like RAM

Anthropic's official docs are explicit about the constraint driving every other best practice: *"Most best practices are based on one constraint: Claude's [context window](glossary.md#context-window) fills up fast, and performance degrades as it fills."* ([source](https://code.claude.com/docs/en/best-practices)) The docs continue: *"LLM performance degrades as context fills. When the context window is getting full, Claude may start 'forgetting' earlier instructions or making more mistakes."*

**Execution:**

- **Track it.** Run `/context` to see what's currently using space.
- **Compact proactively.** Run `/compact` manually around the 50% mark — mid-session summaries preserve more detail than last-minute ones. Use the focus argument to direct what survives: `/compact focus on the API changes` ([source](https://code.claude.com/docs/en/best-practices)).
- **Clear between unrelated tasks.** `/clear` resets the conversation. When you switch from a backend route to frontend styling, run it. Don't let yesterday's debugging session pay rent on today's work.

### 2. Cap `CLAUDE.md` at 200 lines

Anthropic's official memory docs are explicit: *"target under 200 lines per [CLAUDE.md](glossary.md#claudemd) file. Longer files consume more context and reduce adherence."* ([source](https://code.claude.com/docs/en/memory)) The troubleshooting section adds: *"Files over 200 lines consume more context and may reduce adherence."*

> [!NOTE]
> ### Sidebar: CLAUDE.md vs. auto-memory
>
> Claude Code now ships a separate auto-memory system at `~/.claude/projects/<slug>/memory/MEMORY.md`. That file is loaded into every conversation just like `CLAUDE.md`, but it's user-scoped (not repo-scoped) and grows by accretion as Claude saves feedback and preferences from prior sessions. Treat MEMORY.md with the same ≤200-line discipline as CLAUDE.md — run a consolidation pass when it bloats. Mine has ~50 entries; each entry is one line linking to a file in the same memory directory. The masters consolidate; the granular drafts get deleted.

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

Anthropic officially endorses this [worktree / worktree fleet](glossary.md#worktree--worktree-fleet) pattern: *"Anthropic recommends using worktrees to run separate CLI sessions in isolated git checkouts."* ([source](https://code.claude.com/docs/en/best-practices))

**When it pays off:** You're shipping multiple features in parallel, running experiments on independent branches, or maintaining several long-running investigations at once.

**When it doesn't:** You're doing one task at a time. The setup overhead exceeds the gain.

**Execution:**

- `git worktree add ../my-feature feature-branch`
- Launch a fresh Claude Code session in each worktree.
- Cap yourself at 3–5 concurrent sessions. Beyond that, you can't actually track what's happening.

### 2. Skills and MCP for recurring work

These two patterns are under-emphasized in most Claude Code tips content and worth knowing:

- **Skills** — for recurring workflows (API testing, database migrations, security review), define a Skill rather than re-explaining the process every session. Skills load on demand without bloating `CLAUDE.md`. ([source](https://code.claude.com/docs/en/best-practices))
- **[MCP servers](glossary.md#mcp-model-context-protocol)** — for any external service you talk to repeatedly (GitHub, Slack, databases, internal APIs), an MCP server eliminates the token cost of explaining HTTP and parsing responses. Claude calls the service natively. See [AI Agent Discoverability and Protocols](ai-discoverability-and-protocols.md) for the broader protocol landscape.

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

Fill this in and paste it to Claude. With the [`claude-code-optimizer`](skills/claude-code-optimizer/) skill installed, Claude will load the diagnostic procedure and run it against your answers — naming the first real smell and the single fix to make next.

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

## Does this translate to Codex?

About 80% of this playbook ports to Codex CLI with cosmetic renames. The two tools have converged on the same primitives: slash commands, project-memory files, named effort tiers, MCP, skills (`SKILL.md`), subagents, worktrees, and `@`-file mentions. ChatGPT Codex — the hosted cloud agent at chatgpt.com/codex — is a different surface: its context, sandbox, and model picker are OpenAI-managed, so the local-discipline pillars mostly don't apply there.

### Pillar-by-pillar

| # | Pillar | Codex CLI equivalent | Verdict |
| :-- | :--- | :--- | :--- |
| 1 | **Context discipline** (`/clear`, `/compact`, `/context`) | `/clear` and `/compact` are identical in name and purpose. `/status` replaces `/context` — it shows active model, approval policy, writable roots, and remaining context capacity. Codex also adds `/fork` (branch the current thread) and `/side` (ephemeral side conversation) for non-destructive branching. Note: Codex's `/compact` has no focus-steering argument — to steer the summary, prompt it post-compaction. ([Codex CLI slash commands](https://developers.openai.com/codex/cli/slash-commands)) | **Transfers 1:1.** The context-hygiene surface is a superset; `/compact` focus-argument is the one gap. |
| 2 | **`CLAUDE.md` hygiene** (200-line target, path-scoped rules) | `AGENTS.md` is the filename. Budget is byte-based: `project_doc_max_bytes = 32768` (32 KiB combined cascade by default). Path-scoped overrides are built in — Codex walks Git-root to cwd, applying `AGENTS.md` (or `AGENTS.override.md`) at each level. `~/.codex/AGENTS.md` for global defaults. `/init` scaffolds the file. ([AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)) | **Adapts cleanly.** Rename `CLAUDE.md` → `AGENTS.md`; swap "under 200 lines" for "well under 32 KiB combined." The native cascade replaces Claude Code's separate `.claude/rules/` mechanism. |
| 3 | **Verification-first** | Same pattern. Codex adds `/review` — a dedicated reviewer that reads the working-tree diff and reports findings without writing anything. `approvals_reviewer = "auto_review"` routes eligible approval requests through that reviewer automatically. ([Sandbox concepts](https://developers.openai.com/codex/concepts/sandboxing)) | **Transfers 1:1.** Codex has stronger built-in scaffolding here. |
| 4 | **Model routing & effort tiers** | `model_reasoning_effort` accepts `minimal \| low \| medium \| high \| xhigh` (xhigh is model-dependent). `/model` switches mid-session. Named profiles in `config.toml` bake model + effort + approval policy into one preset. ([Config reference](https://developers.openai.com/codex/config-reference), [Codex models](https://developers.openai.com/codex/models)) | **Transfers 1:1.** Same named-tier surface. Profiles are a slight ergonomic edge over per-invocation switching. |
| 5 | **Permissions** (default-deny + `bypassPermissions`) | Two axes instead of one. `sandbox_mode`: `read-only` / `workspace-write` / `danger-full-access`. `approval_policy`: `untrusted` / `on-request` / `never`. The IDE permission selector labels these as **Default permissions** / **Full access** / **Custom (config.toml)**. Default is `workspace-write` + `on-request`. `/permissions` switches mid-session. ([Sandbox concepts](https://developers.openai.com/codex/concepts/sandboxing)) | **Different mental model.** Pick *both* axes. The optimizer's "default-deny + bypass for trusted work" translates as: Default permissions for normal work; `danger-full-access` + `never` only inside Git worktrees or cloud sandboxes. |
| 6 | **Skills, subagents, worktrees** | Skills: same `SKILL.md` convention, built on the open [agentskills.io](https://agentskills.io) standard. Subagents: `[agents]` block in `config.toml`, `/agent` to switch, explicit-spawn only — per the docs: "Codex doesn't spawn subagents automatically… only when you explicitly ask." Worktrees: Local and Worktree thread types with Handoff to move a thread + its Git state between checkouts. ([Skills](https://developers.openai.com/codex/skills), [Subagents](https://developers.openai.com/codex/concepts/subagents), [App worktrees](https://developers.openai.com/codex/app/worktrees)) | **Transfers 1:1.** |
| 7 | **MCP / tool ecosystem** | `[mcp_servers]` block in `config.toml`, same protocol, `/mcp` to inspect. ([Config reference](https://developers.openai.com/codex/config-reference)) | **Transfers 1:1.** |
| 8 | **Prompt expression density** (`@file`, structured output) | `@` opens fuzzy file search over the workspace root. `@Browser` / `@Chrome` / `@Computer` dispatch those tools directly. `!` prefix runs a local shell command and feeds the output back as a user-provided result. ([Codex CLI slash commands](https://developers.openai.com/codex/cli/slash-commands)) | **Transfers 1:1, and the `@` syntax doubles as a tool dispatcher.** |

### What Codex has that Claude Code doesn't

- **Profiles** — named `[profiles.<name>]` config bundles that pin model + reasoning effort + approval policy + MCP servers in one switch (`codex --profile deep-review`).
- **GitHub `@codex` mention** — tag `@codex` on any PR or issue to spawn a cloud task that proposes a diff.
- **Handoff** — move a thread and its Git state between Local and Worktree checkouts without manual branch operations.
- **`/review` as a built-in role** — dedicated reviewer, no writes, available in both CLI and GitHub PR integration.

### Where this doesn't translate

ChatGPT Codex (chatgpt.com/codex) runs in OpenAI-managed containers. You can't tune the sandbox, can't change the default model per task, and there's no `/clear` or `/compact` to run against a thread. If you're using the cloud surface specifically, the only pillar that fully transfers is verification-first.

### How to apply this guide as a Codex user

1. Rename `CLAUDE.md` → `AGENTS.md`. Treat "under 200 lines" as "well under 32 KiB combined cascade."
2. Use Default permissions as your baseline; reserve `danger-full-access` + `never` for worktrees.
3. Define one or two named Profiles in `config.toml` — e.g., a deep-review profile pinning higher effort and the reviewer subagent.
4. Use `/review` instead of an ad-hoc review prompt. Same idea, built-in support.
5. `SKILL.md` skills are portable across both tools — the [agentskills.io](https://agentskills.io) standard underlies both.
6. On ChatGPT Codex specifically, skip the context-discipline pillars and focus on verification.

---

## Sources & attribution

This guide is a curated compilation. The underlying techniques originate from Anthropic's official Claude Code documentation. Every technical claim above has been verified against a primary source.

**Tier 1 — Anthropic documentation (official, with direct quotes):**

- Anthropic Engineering — *Claude Code Best Practices*: https://www.anthropic.com/engineering/claude-code-best-practices
- Claude Code docs — *Best Practices* (the canonical guidance on context management, verification, subagents, and worktrees): https://code.claude.com/docs/en/best-practices
- Claude Code docs — *Memory / CLAUDE.md* (source for the 200-line target and adherence guidance): https://code.claude.com/docs/en/memory
- Claude Code docs — *How Claude Code Works*: https://code.claude.com/docs/en/how-claude-code-works
- Claude Code docs — *Permissions*: https://code.claude.com/docs/en/permissions
- Claude Code docs — *Quickstart*: https://code.claude.com/docs/en/quickstart
- Claude API — *Effort Parameter* (source for named effort tiers: `low`, `medium`, `high`, `xhigh`, `max`): https://platform.claude.com/docs/en/build-with-claude/effort.md

**Tier 1 — Codex documentation (OpenAI official, verified live 2026-05-22):**

- OpenAI Codex — *Slash commands*: https://developers.openai.com/codex/cli/slash-commands
- OpenAI Codex — *Custom instructions with AGENTS.md*: https://developers.openai.com/codex/guides/agents-md
- OpenAI Codex — *Sandbox concepts* (sandbox modes, approval policies, IDE permission labels): https://developers.openai.com/codex/concepts/sandboxing
- OpenAI Codex — *Models* (gpt-5.5, gpt-5.4, gpt-5.4-mini, gpt-5.3-codex, gpt-5.3-codex-spark): https://developers.openai.com/codex/models
- OpenAI Codex — *Config reference* (`model_reasoning_effort` tiers, `[profiles.<name>]`, `[agents]`, `[mcp_servers]`): https://developers.openai.com/codex/config-reference
- OpenAI Codex — *Skills*: https://developers.openai.com/codex/skills
- OpenAI Codex — *Subagents concepts*: https://developers.openai.com/codex/concepts/subagents
- OpenAI Codex — *App worktrees* (Local/Worktree thread types, Handoff): https://developers.openai.com/codex/app/worktrees
- agentskills.io — open agent-skills standard underlying both Codex Skills and Claude Code Skills: https://agentskills.io

**Supporting sources (Tier 2 — primary source, contextual):**

- Lenny's Newsletter — interview with Boris Cherny (creator of Claude Code): https://www.lennysnewsletter.com/p/head-of-claude-code-what-happens
- Anthropic Webinars — *Claude Code for Service Delivery*: https://www.anthropic.com/webinars/claude-code-service-delivery

**Corrections from prior circulating versions:** The Codex section draft (reader-feedback version) included two claims that did not survive verification against OpenAI's live documentation: (1) `/compact` was shown with a `focus` argument — this argument is not documented in Codex CLI; the command runs without parameters. (2) The IDE permission-selector labels were listed as `Chat` / `Agent` / `Agent (Full Access)` — the documented labels are `Default permissions` / `Full access` / `Custom (config.toml)`. Both have been corrected in the section above. Earlier Claude Code guides have also referenced `claude --bare`, `.claudeignore`, and `/effort 85` as official features. None of these exist in Claude Code as of publication. Use `.gitignore` with the `respectGitignore` setting, and the named `effort` tiers (`low`/`medium`/`high`/`xhigh`/`max`) via the `output_config` API parameter. Earlier versions of this guide stated a 40–60% token savings figure without a primary-source citation — that figure has been removed; the official docs confirm the qualitative dynamic (context bloat degrades output and burns tokens) without publishing a specific percentage.

**Compilation, ranking, and commentary © 2026 Rick Watson, RMW Commerce Consulting.** Linked sources are the property of their respective owners. Found an error or have a sharper pattern to add? Open an issue or PR.
