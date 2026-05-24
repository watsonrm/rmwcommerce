# Configuring Claude Code permissions: real lessons vs. cargo cult

**A field guide to `.claude/settings.local.json`, cross-checked against Anthropic's primary docs and the official example settings.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-22*

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's public documentation. See [Sources](#sources). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

## TL;DR

1. Common read commands (`ls`, `cat`, `grep`, `find`, `head`, `tail`, `diff`, `cd` into your working dir, read-only `git`) are already on a built-in auto-allowlist. Adding `Bash(ls:*)` does nothing. [^perms-readonly]
2. The matcher decomposes compound commands (`&&`, `||`, `;`, `|`, newlines) and evaluates each subcommand independently. You don't need to allowlist the literal pipeline. [^perms-compound]
3. Spend your effort on three things: MCP-server wildcards, write-capable tool wildcards (`sed`, `awk`, `gh`, `gcloud`, `curl`, `python3`), and choosing the right file scope. The rest is noise.
4. Don't try to constrain Bash arguments with patterns. Anthropic's docs call this "fragile" and list five ways it gets bypassed. Use [WebFetch domain rules](https://code.claude.com/docs/en/permissions#webfetch) or [PreToolUse hooks](https://code.claude.com/docs/en/hooks-guide) instead. [^perms-fragile]

## Where to spend your time

| Effort | Payoff | Recommendation | Best for |
|---|---|---|---|
| MCP server wildcards (`mcp__server__*`) | Highest — kills the most prompts in a typical session | Do this first | solo on own machine |
| Wildcards for write-capable tools you trust | High | Do this second | team / shared machines |
| Removing rules already covered by the built-in read-only list | File hygiene | One audit pass | regulated or enterprise |
| Trying to constrain Bash arguments via patterns | Low and fragile | Don't bother | agents running unattended |
| Adding `Bash(*)` to skip prompts | Negative — defeats the safety classifier | Don't | any user using paid AI tools |

## What's real

### The built-in read-only auto-allowlist

> Claude Code recognizes a built-in set of Bash commands as read-only and runs them without a permission prompt in every mode. These include `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, and read-only forms of `git`. The set is not configurable; to require a prompt for one of these commands, add an `ask` or `deny` rule for it. [^perms-readonly]

Rules like `Bash(ls:*)`, `Bash(grep:*)`, `Bash(cat:*)`, `Bash(echo:*)`, `Bash(find:*)`, `Bash(diff:*)` are redundant. An audit on a one-year-old `.claude/settings.local.json` from heavy daily use found ~9 such rules out of 222, all dead weight.

### Compound commands are auto-decomposed

> Claude Code is aware of shell operators, so a rule like `Bash(safe-cmd *)` won't give it permission to run the command `safe-cmd && other-cmd`. The recognized command separators are `&&`, `||`, `;`, `|`, `|&`, `&`, and newlines. A rule must match each subcommand independently. [^perms-compound]

When a `cd /path && ls files/ && echo done` prompts, the matcher already split it into three checks. The blocker is usually a `cd` to a path outside the working directory or a write-capable subcommand. Allowlisting the literal compound string won't help — the next variant won't match.

### Pattern syntax has three rules worth knowing

1. **`:*` and ` *` are equivalent at the end of a pattern.** `Bash(ls:*)` matches the same commands as `Bash(ls *)`. The `:*` form only works at the end — `Bash(git:* push)` treats the colon as a literal character. [^perms-syntax]
2. **MCP wildcards cover all tools from a server.** `mcp__claude_ai_Slack__*` pre-approves every Slack tool. This is the single highest-leverage rule in a typical config. [^perms-mcp]
3. **Process wrappers auto-strip.** `timeout`, `time`, `nice`, `nohup`, `stdbuf`, and bare `xargs` (no flags) are pre-stripped before matching, so `Bash(npm test *)` covers `timeout 30 npm test`. `xargs -n1`, `watch`, `setsid`, `flock`, `find -exec`, and `find -delete` are NOT auto-stripped — those need exact rules. [^perms-wrappers]

### Scope picks itself

| File | Scope | Use for | Git status |
|---|---|---|---|
| `~/.claude/settings.json` | You, every project | Tool-class wildcards, MCP servers you always trust | Personal |
| `.claude/settings.json` | Everyone on this repo | Team agreements; deny rules for secrets | Committed |
| `.claude/settings.local.json` | You, this repo only | Project-specific paths, in-flight experimentation | Gitignored by default |

Permission rules merge across scopes rather than override. A deny at any level beats an allow at any other level. [^perms-merge]

## What's cargo cult

These patterns are common in the wild and don't pay off:

- **`Bash(ls:*)`, `Bash(cat:*)`, `Bash(echo:*)`, etc.** — Already auto-allowed. File bloat without effect.
- **Allowlisting the exact compound string after a denial.** The next variant won't match. Address the failing subcommand instead.
- **`Bash(*)` to skip everything.** Doesn't actually skip — Anthropic's command-injection classifier still flags risky commands. You give up the file-level documentation of what you trust without getting a full bypass. For unattended runs, use `--dangerously-skip-permissions` for that session, not a permanent rule. [^security-classifier]
- **`Bash(curl http://github.com/ *)` to "restrict curl to GitHub."** Anthropic's docs label this "fragile" and list five bypasses: options before the URL, different protocol, redirects, shell variables, extra whitespace. Use `WebFetch(domain:github.com)` plus a deny rule on `Bash(curl *)`, or a `PreToolUse` hook. [^perms-fragile][^hooks]
- **Believing settings expire.** They don't. `.claude/settings.local.json` persists across sessions, restarts, and new terminals in the same repository. [^settings-reload]
- **Read/Edit deny rules as hard guarantees.** They block built-in file tools and `cat`/`head`/`sed` in Bash. They don't block arbitrary Python or Node scripts that open files themselves. For hard guarantees, enable [sandboxing](https://code.claude.com/docs/en/sandboxing). [^perms-readedit]

## Faster paths than hand-rolling rules

When custom rules feel like the wrong tool, here are three alternatives Anthropic documents:

1. **Start from the official example configurations.** Anthropic publishes three starter files: `settings-lax.json` (permissive), `settings-strict.json` (restrictive), and `settings-bash-sandbox.json` (sandboxed). Fork the one that matches your posture. [^examples] Permissive for solo. Restrictive for shared or team. Sandboxed for CI or contractor agents.
2. **For URL or argument constraints, use a `PreToolUse` hook.** Hooks run before the permission prompt and can deny, allow, or force-prompt programmatically. This is the documented escape hatch for anything Bash patterns can't express reliably. [^hooks]
3. **For OS-level enforcement, enable the sandbox.** The Bash sandbox restricts filesystem and network access at the operating-system level for every Bash subprocess. The default `autoAllowBashIfSandboxed: true` lets sandboxed commands run without prompts. This is the right answer if your threat model needs guarantees that survive a compromised agent. [^sandbox] Expect 30-min setup. Skip unless you're running unattended agents.

## Sources

[^perms-readonly]: Anthropic. *Configure permissions — Read-only commands.* Claude Code Docs. <https://code.claude.com/docs/en/permissions#read-only-commands>
[^perms-compound]: Anthropic. *Configure permissions — Compound commands.* Claude Code Docs. <https://code.claude.com/docs/en/permissions#compound-commands>
[^perms-syntax]: Anthropic. *Configure permissions — Permission rule syntax.* Claude Code Docs. <https://code.claude.com/docs/en/permissions#permission-rule-syntax>
[^perms-mcp]: Anthropic. *Configure permissions — MCP.* Claude Code Docs. <https://code.claude.com/docs/en/permissions#mcp>
[^perms-wrappers]: Anthropic. *Configure permissions — Process wrappers.* Claude Code Docs. <https://code.claude.com/docs/en/permissions#process-wrappers>
[^perms-merge]: Anthropic. *Claude Code settings — How scopes interact.* "Permission rules behave differently because they merge across scopes rather than override." <https://code.claude.com/docs/en/settings#how-scopes-interact>
[^perms-fragile]: Anthropic. *Configure permissions — Bash permission limitations.* "Bash permission patterns that try to constrain command arguments are fragile." <https://code.claude.com/docs/en/permissions#bash>
[^perms-readedit]: Anthropic. *Configure permissions — Read and Edit.* "Read and Edit deny rules apply to Claude's built-in file tools and to file commands Claude Code recognizes in Bash ... They do not apply to arbitrary subprocesses that read or write files indirectly." <https://code.claude.com/docs/en/permissions#read-and-edit>
[^settings-reload]: Anthropic. *Claude Code settings — When edits take effect.* "Claude Code watches your settings files and reloads them when they change, so edits to most keys apply to the running session without a restart." <https://code.claude.com/docs/en/settings#when-edits-take-effect>
[^security-classifier]: Anthropic. *Security — Built-in protections.* "Command injection detection: Suspicious bash commands require manual approval even if previously allowlisted." <https://code.claude.com/docs/en/security#built-in-protections>
[^hooks]: Anthropic. *Automate workflows with hooks.* Claude Code Docs. <https://code.claude.com/docs/en/hooks-guide>
[^sandbox]: Anthropic. *Configure the sandboxed Bash tool.* Claude Code Docs. <https://code.claude.com/docs/en/sandboxing>
[^examples]: Anthropic. *Example Claude Code settings files.* GitHub. <https://github.com/anthropics/claude-code/tree/main/examples/settings>

The JSON schema for `settings.json` is published at <https://json.schemastore.org/claude-code-settings.json>. Adding it as `"$schema"` in your file enables autocomplete and inline validation in VS Code, Cursor, and any editor that supports JSON schema.

All facts verified against the docs as of 2026-05-22.

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's public documentation. See [Sources](#sources). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.
