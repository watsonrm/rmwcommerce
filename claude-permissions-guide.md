# Claude Permissions: Stop the Interruption Hell

**A layered allowlist strategy for every Claude environment — claude.ai, Claude Desktop, and Claude Code — with my working starter defaults.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- Permissions feel like hell because they're layered, environment-specific, and grow drift over months.
- The fix is a layered allowlist strategy: start tight with read-only, broaden specifically as you build trust, periodically consolidate drift into wildcards.
- There are three different environments with three different permission systems. Each one has a different place where settings live.
- What follows is what I've landed on. This is still evolving. I'll update this article as I refine it.

### Where to spend your time, first-time setup

If you're just getting started with permissions configuration, these five moves cover most of the gain.

| # | First move | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | **Identify your environment** — Claude Code, Desktop, or claude.ai web | Permission settings live in different places. Wrong environment, wrong fix. | 2 min |
| **2** | **Add Tier A (read-only MCP) to your global allowlist** | Read-only operations have no side effects. No reason to approve them every time. | 10 min |
| **3** | **Add safe-read Bash wildcards to your global allowlist** | `git *`, `find:*`, `grep:*`, `ls:*` — these fire constantly and are safe. One wildcard ends the repetition. | 5 min |
| **4** | **Decide which write operations belong in each project** | Write operations have side effects. Approve them at the project level, not globally. | Per-project |
| **5** | **Audit `settings.local.json` every month or two** — consolidate specific patterns into wildcards | The drift problem. Unchecked, your settings file fills with hundreds of one-off approvals that could be three wildcards. | 20 min quarterly |

Most readers should do steps 1–3 today and return to 4–5 over the next few weeks. Steps 1–3 eliminate the most common interruptions with the least risk.

This article focuses primarily on Claude Code, which has the most complex permission model. For the short version on claude.ai web and Claude Desktop, see [Section 1](#section-1-the-three-environments). For the full Claude Code model, see [Section 2](#section-2-the-claude-code-permission-model-in-depth).

---

## Section 1: The three environments and how they differ

Claude's permissions look different depending on where you're using it. Each environment has a different model, different settings location, and a different audience for this guide.

### Claude.ai (web)

The web interface at claude.ai manages permissions through the **Integrations** and **Connectors** settings. The relevant location: **Settings → Integrations** (or similar, depending on your plan). Anthropic maintains a connectors directory, and each connector — Slack, GitHub, Google Drive, Google Calendar, Asana, and others — has its own permission scope that you approve when connecting. ([source](https://support.claude.com/en/collections/15399129-connectors))

What you control: which integrations are enabled, whether a given integration can take actions (write) or just read, and which projects have access to which integrations. The connector model is relatively coarse — you're approving entire integrations, not individual operations within them.

The interruption pattern on claude.ai is usually: you're getting prompted every time a connector action fires because the integration needs re-authorization, or a specific write action hasn't been approved for the current project context. The fix is usually in the Integrations settings panel, not in any config file.

### Claude Desktop / Cowork

Claude Desktop (which Anthropic also ships as "Cowork" in some contexts) has a workspace-level permission model managed through the **Desktop app preferences**. The settings for file system access, skill allowlists, and MCP server connections live in the app's preferences UI.

The key permission surface in Claude Desktop:
- **File system access scope** — which directories Claude can read and write
- **Skill allowlists** — which skills can run what tools without prompting
- **MCP server connections** — which MCP servers are active and what they're allowed to do

The interruption pattern in Desktop is usually: a skill or MCP tool is trying to take an action that hasn't been approved for the current workspace scope. Check the preferences panel and expand the scope for actions you've decided are safe.

### Claude Code

The most complex permission model of the three, and where most practitioners spend their configuration time. Settings live in four places, with a defined precedence order:

1. **`~/.claude/settings.json`** — user settings, apply to every project
2. **`.claude/settings.json`** — shared project settings, checked into source control
3. **`.claude/settings.local.json`** — personal project settings, not checked in (Claude Code configures git to ignore this when it creates the file) ([source](https://code.claude.com/docs/en/settings))
4. **Managed settings** — organization-wide, cannot be overridden

Precedence runs from managed (highest) → local project → shared project → user (lowest). A deny rule at any level blocks even an allow rule at a lower level. ([source](https://code.claude.com/docs/en/permissions))

The permission UI inside Claude Code: run `/permissions` to see all active rules, which file they're sourced from, and what's being allowed or denied.

Everything in Sections 2–7 covers Claude Code specifically.

---

## Section 2: The Claude Code permission model in depth

This section assumes you're already using Claude Code and feeling the interruption problem. It covers the mechanics of how the permission model works, which is what you need to tune it.

### Allow, ask, and deny — the three rule types

Anthropic's permissions docs describe the evaluation order:

> *"Rules are evaluated in order: deny → ask → allow. The first matching rule wins, so deny rules always take precedence."* ([source](https://code.claude.com/docs/en/permissions))

**Allow** rules let a tool call proceed without prompting. **Ask** rules always prompt for that tool use. **Deny** rules block the tool call outright — a bare tool name like `Bash` removes the tool from Claude's context entirely, while a scoped rule like `Bash(rm *)` leaves the tool available but blocks matching commands.

### Tool categories

The main tool categories you'll encounter in permission rules:

- **`Read`** — file reads, grep, glob. Read-only by default; no approval required in most modes.
- **`Edit`** / **`Write`** — file modification. Requires approval by default.
- **`Bash`** — shell command execution. Requires approval by default, with pattern-matching for wildcards.
- **`WebFetch`** — web requests. Can be scoped to specific domains.
- **`WebSearch`** — search operations.
- **MCP-prefixed tools** — `mcp__<servername>__<toolname>` format for any MCP server tool.
- **`Agent`** — subagent use. Can be allowed or denied by agent name.

The full permission table from Anthropic's docs:

| Tool type | Example | Approval required by default |
| :--- | :--- | :--- |
| Read-only | File reads, Grep | No |
| Bash commands | Shell execution | Yes |
| File modification | Edit/write files | Yes |

([source](https://code.claude.com/docs/en/permissions))

### Wildcard syntax in Bash patterns

This is where most of the practical configuration lives. Anthropic's docs explain the semantics precisely:

> *"Bash rules support glob patterns with `*`. Wildcards can appear at any position in the command, including at the beginning, middle, or end."* ([source](https://code.claude.com/docs/en/permissions))

Key behaviors:
- `Bash(git *)` matches `git log --oneline --all`, `git diff HEAD`, `git status` — any command starting with `git `.
- `Bash(ls *)` matches `ls -la` but **not** `lsof` — the space before `*` enforces a word boundary.
- `Bash(ls*)` (no space) matches both `ls -la` and `lsof`.
- The `:*` suffix is equivalent to a trailing ` *`, so `Bash(find:*)` means the same as `Bash(find *)`.
- A single `*` matches any sequence including spaces, so one wildcard can span multiple arguments.
- Compound commands (`&&`, `||`, `;`, `|`) are parsed separately — a rule must match each subcommand independently.

There are also built-in read-only commands that run without prompting regardless of your settings: `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, and read-only forms of `git`. You don't need allowlist entries for these; they're covered by default.

One important caveat the docs call out explicitly:

> *"Bash permission patterns that try to constrain command arguments are fragile."* ([source](https://code.claude.com/docs/en/permissions))

A pattern like `Bash(curl http://github.com/ *)` won't cover variations in argument order, protocols, or redirects. For constraining network access, use `WebFetch(domain:github.com)` plus a `Bash` deny rule for curl, rather than trying to constraint curl's arguments with a pattern.

### MCP wildcards

MCP tool names follow the format `mcp__<servername>__<toolname>`. Permission rules use the same format:

- `mcp__puppeteer` — matches any tool from the puppeteer server
- `mcp__puppeteer__*` — also matches all tools from the puppeteer server (equivalent)
- `mcp__puppeteer__puppeteer_navigate` — matches only that specific tool

([source](https://code.claude.com/docs/en/permissions))

Use whole-server wildcards for trusted read-only MCP servers; use per-tool rules for servers that mix read and write operations where you want to approve only the reads.

### The layered file model and what wins in conflicts

From the Anthropic settings docs, the precedence order from highest to lowest:

1. **Managed settings** — cannot be overridden by any other level
2. **Command line arguments** — temporary session overrides
3. **Local project settings** (`.claude/settings.local.json`)
4. **Shared project settings** (`.claude/settings.json`)
5. **User settings** (`~/.claude/settings.json`)

The important implication: *"If a tool is denied at any level, no other level can allow it."* ([source](https://code.claude.com/docs/en/permissions)) A user-level deny blocks a project-level allow. A managed deny blocks everything.

This means your global `~/.claude/settings.json` is the right place for allow rules that should apply everywhere. Project `.claude/settings.json` is for project-specific approvals. And `.claude/settings.local.json` is where one-off approvals accumulate (and where the drift problem starts — more on this in Section 4).

---

## Section 3: My starter defaults — the working set

What follows is what I run. Treat it as a starting point, not a definitive answer. I'm still refining this, and I'll update the article as I do.

The logic behind the tiers: some operations have zero meaningful side effects (read MCP, safe Bash reads), some have side effects that require per-project authorization (write MCP), and some should always require a prompt regardless of context (destructive operations, outbound comms). The three tiers reflect that structure.

### Tier A — Read-only MCP: allow globally

These go in `~/.claude/settings.json` under `permissions.allow`. They have no write operations, no costs, no side effects. No reason to be prompted on them every time.

```json
{
  "permissions": {
    "allow": [
      "mcp__claude_ai_Slack__slack_search_messages",
      "mcp__claude_ai_Slack__slack_read_channel",
      "mcp__claude_ai_Slack__slack_read_thread",
      "mcp__claude_ai_Slack__slack_search_users",
      "mcp__claude_ai_Google_Drive__search_files",
      "mcp__claude_ai_Google_Drive__read_file_content",
      "mcp__claude_ai_Google_Drive__get_file_metadata",
      "mcp__claude_ai_Google_Calendar__list_events",
      "mcp__claude_ai_Google_Calendar__list_calendars",
      "mcp__claude_ai_Asana__get_my_tasks",
      "mcp__claude_ai_Asana__get_projects",
      "mcp__google-docs__readDocument",
      "mcp__google-docs__searchDriveFiles"
    ]
  }
}
```

These are zero-risk reads. Search Slack, read calendar events, look up Drive files — none of these write, send, or charge anything. Approving them every session is friction with no safety value.

### Tier B — Write MCP: allow at the project level

These go in `.claude/settings.json` inside the specific project that has earned the right to use them. Not in your global settings.

```json
{
  "permissions": {
    "allow": [
      "mcp__claude_ai_Google_Calendar__create_event",
      "mcp__claude_ai_Google_Calendar__update_event",
      "mcp__claude_ai_Google_Drive__create_file",
      "mcp__google-docs__replaceDocumentWithMarkdown",
      "mcp__claude_ai_Asana__update_tasks"
    ]
  }
}
```

Reasoning: these have side effects. Approving calendar event creation globally means any project could create calendar events. That's more than I want to pre-authorize. Once I've decided a project should be automating calendar management, I add those specific tools to that project's settings.

**Slack `send_message` specifically**: I keep this on per-call approval even in projects that otherwise have write MCP allowlisted. Outbound messages have real-world side effects, and I have a separate authorization rule requiring explicit channel and audience confirmation before any send. The interruption is the safety feature.

### Tier C — Bash: wildcard once a category is proven safe

These also go in `~/.claude/settings.json`. The logic is: once I've used `git diff --stat | head` enough times to know it's safe, I don't want to approve `git diff --stat | head -10` as a separate new entry. One wildcard covers the whole category.

```json
{
  "permissions": {
    "allow": [
      "Bash(git *)",
      "Bash(find:*)",
      "Bash(grep:*)",
      "Bash(ls:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(cat:*)",
      "Bash(wc:*)",
      "Bash(curl *)",
      "Bash(gh *)",
      "Bash(python3 *)"
    ]
  }
}
```

A few notes on the more permissive entries:

`Bash(curl *)` — debatable. curl can hit anything. But in practice, once I trust a project, the alternative is approving every curl variant individually, which is what fills up `settings.local.json`. I've landed on allowing it globally and relying on CLAUDE.md guidance to shape what Claude actually tries to do.

`Bash(gh *)` — the GitHub CLI. Same logic as curl. I use it regularly and trust the projects I run it in.

`Bash(python3 *)` — this means any Python script. I've decided that's acceptable in my setup. If you're running untrusted code or are more cautious about script execution, keep this as per-call approval.

Note: as documented above, `ls`, `cat`, `head`, `tail`, `grep`, `find`, and `wc` are already in Claude Code's built-in read-only set and run without prompts by default. I include them in my allowlist anyway to make my intent explicit and to ensure they're covered in non-default permission modes.

### The combined starter JSON

This is what you could drop into `~/.claude/settings.json` as a starting point. It combines Tier A (read MCP) and Tier C (safe Bash) — the categories with no meaningful side effects.

Do not add Tier B (write MCP) to this file. Those belong in project-level settings after you've decided that project should automate those operations.

```json
{
  "permissions": {
    "allow": [
      "mcp__claude_ai_Slack__slack_search_messages",
      "mcp__claude_ai_Slack__slack_read_channel",
      "mcp__claude_ai_Slack__slack_read_thread",
      "mcp__claude_ai_Slack__slack_search_users",
      "mcp__claude_ai_Google_Drive__search_files",
      "mcp__claude_ai_Google_Drive__read_file_content",
      "mcp__claude_ai_Google_Drive__get_file_metadata",
      "mcp__claude_ai_Google_Calendar__list_events",
      "mcp__claude_ai_Google_Calendar__list_calendars",
      "mcp__claude_ai_Asana__get_my_tasks",
      "mcp__claude_ai_Asana__get_projects",
      "mcp__google-docs__readDocument",
      "mcp__google-docs__searchDriveFiles",
      "Bash(git *)",
      "Bash(find:*)",
      "Bash(grep:*)",
      "Bash(ls:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(cat:*)",
      "Bash(wc:*)",
      "Bash(curl *)",
      "Bash(gh *)",
      "Bash(python3 *)"
    ]
  }
}
```

Your MCP tool names may differ from these depending on how your MCP servers are configured. Check `/permissions` in a live session to see what names Claude Code is using for your tools.

---

## Section 4: The drift problem and how to consolidate

This is the actual source of permission hell for long-term users.

When you start using Claude Code, you approve commands one at a time. Each time you select "Yes, don't ask again," Claude Code writes a specific rule to `.claude/settings.local.json`. Over months, that file fills up. You end up with entries like:

```json
"Bash(curl -s 'https://api.pipedrive.com/v1/persons?api_token=...')",
"Bash(curl -sI 'https://api.pipedrive.com/v1/deals?...')",
"Bash(curl -X GET 'https://api.pipedrive.com/v1/activities...')",
```

That's three entries for essentially the same operation — curl against the Pipedrive API. Multiply that by every command you've approved over six months and you have hundreds of hyper-specific rules that could be three wildcards.

The fix: periodic consolidation. Every month or two, open `~/.claude/settings.json` and `.claude/settings.local.json` and look for patterns.

**The consolidation process:**

1. Group similar entries. All `curl` against the same API base URL → one `Bash(curl *)` or `Bash(curl -s 'https://api.pipedrive.com/*')`.
2. Look for command families. Twenty specific `python3 _scripts/foo.py` entries → one `Bash(python3 _scripts/*)`.
3. Promote the wildcards to the right level. If the wildcard should apply everywhere, move it to `~/.claude/settings.json`. If it's project-specific, keep it in `.claude/settings.json` for that project.
4. Delete the specific entries you've just superseded.

The rhythm: approve specifically until you see the pattern, then promote to wildcard and delete the specifics. Tight-then-wildcard. This keeps your settings file readable and your interruption rate low.

You can view all active rules and their source files by running `/permissions` inside a Claude Code session.

---

## Section 5: When not to broaden

Some operations should never be auto-approved, regardless of how often they fire.

**Destructive file operations.** `rm -rf` and any command that permanently deletes files should always prompt. The interruption is the checkpoint. Claude Code's docs note that even in `bypassPermissions` mode, removals targeting root or home directories still prompt as a circuit breaker. ([source](https://code.claude.com/docs/en/permissions)) Take that as the principle: destructive operations should always have a human in the loop.

**Outbound communications.** Slack `send_message`, email sends, Pipedrive contact creation, any operation that puts something into the world that another person will see. These have real-world side effects that can't be undone by a `git revert`. I keep these on per-call approval even in projects that otherwise have broad write permissions, and I have an additional two-gate rule: explicit channel, explicit audience, draft confirmation before any send.

**Paid API operations in loops.** Any tool call that costs money and could run in a loop deserves a prompt. A single mistaken loop can generate a surprising bill. Approve these per-call and add spending limits at the API provider level.

**Credential operations.** Key rotation, password changes, `security` keychain commands — anything touching credentials should always prompt.

The principle: the interruption is the safety feature. These aren't annoyances to optimize away. They're the moments where a human in the loop is genuinely valuable.

---

## Section 6: What's still unsolved

Rick said: *"I don't think I am there yet."* Here's the honest accounting of what's still annoying.

**Drift management is manual.** There's no automated consolidation. Auditing `settings.local.json` requires opening files and reading JSON across multiple directories. I do it by hand every month or two. It would be better if Claude Code had a `/permissions audit` command that surfaced consolidation opportunities automatically.

**No UI for the layered settings.** `/permissions` shows active rules and their source files, which helps. But to actually understand the combined effect of four overlapping settings files, you have to read them yourself and reason about precedence. A visual diff showing "what's being allowed globally vs. project vs. local" would be useful.

**MCP tool naming inconsistency.** Across projects I've seen the same underlying tool appear as `mcp__Asana__*` in one settings file and `mcp__claude_ai_Asana__*` in another, depending on how the MCP server was configured or when it was set up. When I audit my settings, I sometimes find rules that are no longer matching because the tool name drifted. There's no warning when this happens.

**Cross-environment parity.** My claude.ai web permissions, Desktop preferences, and Claude Code settings are three separate systems with no sync. If I grant a Google Calendar integration permission in Claude Desktop and then try to do the same thing in Claude Code, I'm configuring the same underlying capability in a different place with different syntax. Maintaining consistency requires checking all three.

**The `bypassPermissions` temptation.** After enough interruptions, `bypassPermissions` starts looking appealing. Anthropic's docs are clear: *"Only use this mode in isolated environments like containers or VMs where Claude Code cannot cause damage."* ([source](https://code.claude.com/docs/en/permissions)) I haven't used it, and I'm not going to on my main machine. But the fact that it's tempting means the permission friction is still too high in some situations.

These are the problems I'm working on. I'll update this article when I find better answers.

---

## Section 7: Quick reference card

Starter allowlist for `~/.claude/settings.json`. Covers read-only MCP plus safe Bash wildcards. Does not include write MCP — add those per-project.

Adjust MCP tool names to match how your MCP servers are actually configured. Run `/permissions` in a session to verify the names Claude Code uses for your tools.

```json
{
  "permissions": {
    "allow": [
      "mcp__claude_ai_Slack__slack_search_messages",
      "mcp__claude_ai_Slack__slack_read_channel",
      "mcp__claude_ai_Slack__slack_read_thread",
      "mcp__claude_ai_Slack__slack_search_users",
      "mcp__claude_ai_Google_Drive__search_files",
      "mcp__claude_ai_Google_Drive__read_file_content",
      "mcp__claude_ai_Google_Drive__get_file_metadata",
      "mcp__claude_ai_Google_Calendar__list_events",
      "mcp__claude_ai_Google_Calendar__list_calendars",
      "mcp__claude_ai_Asana__get_my_tasks",
      "mcp__claude_ai_Asana__get_projects",
      "mcp__google-docs__readDocument",
      "mcp__google-docs__searchDriveFiles",
      "Bash(git *)",
      "Bash(find:*)",
      "Bash(grep:*)",
      "Bash(ls:*)",
      "Bash(head:*)",
      "Bash(tail:*)",
      "Bash(cat:*)",
      "Bash(wc:*)",
      "Bash(curl *)",
      "Bash(gh *)",
      "Bash(python3 *)"
    ]
  }
}
```

**After copying this:** run `/permissions` in Claude Code to confirm the rules loaded and to verify MCP tool names match your actual server configuration.

---

## Where to go next

**[Why Is Claude Code So Noisy?](claude-code-noise.md)** — the noise half of the interruption problem. Permission prompts and verbose output are related but distinct. That article covers the output side; this one covers the prompt side.

**[Claude Code for Non-Developers: Your First Session](claude-code-non-developers-first-session.md)** — Section 1 covers the conservative first-session permissions setup. Read this article after you've had a few weeks of sessions and want to tune from there.

**[The Claude Code Workflow Optimizer](claude-code-optimizer.md)** — Pillar 1 (context discipline) reduces the frequency of some prompt triggers. Pillar 3 (verification-first) addresses how permission prompts fit into the verification loop.

**[The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md)** — as you graduate from prompts to agents, permission tuning becomes more important. Agents running unattended have a different permission profile than interactive sessions.

**[Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md)** — multi-agent systems compound the permission surface. Every subagent has its own approval requirements. The design-for-failure section covers how to think about permissions at scale.

---

## Sources & Attribution

**Tier 1 — Primary sources (Anthropic official documentation):**

- Anthropic Claude Code — *Permissions*. Cited for: the full permission model (allow/ask/deny, evaluation order, tool categories, Bash wildcard semantics, MCP patterns, layered file model, `bypassPermissions` warning). Verbatim quotes used where describing semantics. Verified HTTP 200, 2026-05-22: https://code.claude.com/docs/en/permissions
- Anthropic Claude Code — *Settings*. Cited for: settings file locations and names, precedence order, permission-related settings keys. Verified HTTP 200, 2026-05-22: https://code.claude.com/docs/en/settings
- Anthropic Claude Code — *Memory / CLAUDE.md*. Cited for: CLAUDE.md sizing guidance. Verified HTTP 200, 2026-05-22: https://code.claude.com/docs/en/memory
- Anthropic Support — *Connectors*. Cited for: claude.ai connector permission model reference. Verified HTTP 200, 2026-05-22: https://support.claude.com/en/collections/15399129-connectors

**First-person data — Rick's working configuration:**

The Tier A, Tier B, and Tier C allowlist examples are drawn directly from my own `settings.json` files. They're not citations — they're what I run. I've framed them as "what I've landed on" throughout. MCP tool names in particular reflect how my servers are configured, which may differ from your setup.

**Related work in this series:**

- [Claude Code for Non-Developers: Your First Session](claude-code-non-developers-first-session.md) — the first-session conservative permissions baseline.
- [Why Is Claude Code So Noisy?](claude-code-noise.md) — the output-noise companion to this guide.
- [Claude Code Workflow Optimizer](claude-code-optimizer.md) — context discipline and verification-first workflow.
- [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — permission considerations as autonomy increases.
- [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — multi-agent permission surface.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
