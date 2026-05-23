# Configuring `.claude/settings.local.json`: What Actually Matters

**A field guide to Claude Code's permissions file — what's real, what's cargo cult, and where new users almost always over-engineer.**

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's public documentation. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- Most "I want to skip this prompt" wishes are already met. Anthropic ships a built-in read-only allowlist for `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, and read-only `git`. Adding `Bash(ls:*)` to your settings does nothing.
- The matcher already decomposes compound commands (`&&`, `||`, `;`, `|`, `|&`, `&`, newlines). You don't need to approve the whole pipeline — a matching rule for each subcommand is what matters.
- Real value comes from two places: adding wildcards for MCP servers you trust (`mcp__some-server__*`), and adding wildcards for write-capable tools (`sed`, `awk`, `gh`, `git`, `gcloud`, `python3`, `curl`).
- Don't try to constrain Bash arguments via patterns. Anthropic's docs call it "fragile" — and they list exactly why.

### Where to spend your time, in priority order

| # | Practice | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| **1** | Add server-level wildcards for MCP servers you trust (`mcp__server__*`) | Kills the most approval prompts per line added. Every tool from that server is covered. | 5 min |
| **2** | Add wildcards for write-capable tools you use (`git`, `gh`, `sed -n`, `python3 -c`) | Read-only tools are already covered by the built-in list. Write-capable tools are the actual source of friction. | 10 min |
| **3** | Remove redundant rules already on the built-in read-only list | File hygiene — fewer rules, easier to audit which ones are doing real work. | 15 min quarterly |
| **4** | Replace argument-constraining patterns with WebFetch domain rules or hooks | Argument patterns are fragile. They won't hold for the next variant of the same command. | As needed |
| **5** | Add `Bash(*)` to skip all prompts | Negative. You give up the audit trail without actually bypassing Claude Code's safety classifier. | Don't |

Most readers should handle the first two and stop.

---

## Real lessons

### 1. The read-only allowlist is built in. Stop adding to it.

Anthropic's [permissions doc](https://code.claude.com/docs/en/permissions) is direct:

> Claude Code recognizes a built-in set of Bash commands as read-only and runs them without a permission prompt in every mode. These include `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, and read-only forms of `git`. The set is not configurable; to require a prompt for one of these commands, add an `ask` or `deny` rule for it.

Rules like `Bash(ls:*)`, `Bash(grep:*)`, `Bash(cat:*)`, `Bash(echo:*)`, `Bash(find:*)`, `Bash(head:*)`, `Bash(tail:*)`, `Bash(wc:*)`, `Bash(stat *)`, `Bash(diff:*)` are all redundant. They don't break anything — they just bloat the file and make it harder to see which rules are actually doing work.

One data point: a 213-line `settings.local.json` from a year of heavy daily use had at least 9 rules from this redundant set. Removing them cuts the file by ~5% and makes the effective rules legible.

### 2. Compound commands are decomposed automatically. The matcher handles `&&`.

> Claude Code is aware of shell operators, so a rule like `Bash(safe-cmd *)` won't give it permission to run the command `safe-cmd && other-cmd`. The recognized command separators are `&&`, `||`, `;`, `|`, `|&`, `&`, and newlines. A rule must match each subcommand independently.

When a prompt fires on `cd /path && find . | head -10`, the matcher already split it into three checks. If `find` and `head` are read-only by default, the blocker is whatever isn't auto-allowed — usually a tool not on the built-in list, or a `cd` to a path outside the working directory.

Adding the literal compound string to your allowlist won't help. The next invocation will have a slightly different form and won't match.

One caveat: `cd` combined with `git` in a single compound command always prompts, regardless of the target directory. This is a documented behavior in Claude Code, not a pattern you can configure away. The simplest fix is to separate the `cd` and `git` calls across steps.

When you click "Yes, don't ask again" on a compound command, Claude Code saves a separate rule for each subcommand that needs approval — not a single rule for the full string. Future invocations of those subcommands are recognized individually, which is more useful than a compound-specific rule.

### 3. Add wildcards for tools that are not auto-read-only.

These have write-capable flags, or simply aren't on the built-in list, and need explicit rules:

| Pattern | Why it's worth having | What it covers |
| :--- | :--- | :--- |
| `Bash(sed -n:*)` | `sed -n` prints; `-i` writes. The pattern lets through the read form only. | `sed -n '20,40p' file.md` |
| `Bash(awk:*)` | Not on the auto-list; standard use has no write side effects. | `awk '{print $1}' file` |
| `Bash(unzip -p:*)`, `Bash(unzip -l:*)` | Pipe-to-stdout and list-contents are read-only; `-o` writes. | Inspecting archives |
| `Bash(date)`, `Bash(date +*)` | `date` is not on the read-only list. | Timestamping output |
| `Bash(python3 -c:*)` | One-liners for JSON parsing and similar tasks. | `python3 -c "import json..."` |
| `Bash(curl -s:*)`, `Bash(curl -sS:*)` | The GET-oriented forms. Still prompts for `-X POST` if you don't add that. | API reads |
| `Bash(gh pr:*)`, `Bash(gh api:*)`, `Bash(gh run:*)` | GitHub CLI is heavily used and not covered by the read-only list. | GitHub reads and trusted side effects |
| `Bash(git *)` | All git subcommands — useful once you've decided git is inside your trust boundary. | `git status`, `git commit`, `git push` |
| `Bash(gcloud *)` | GCP CLI, not covered by any built-in list. | Cloud Run, Secret Manager, etc. |
| `mcp__server-name__*` | Pre-approves every tool from a trusted MCP server. | See Lesson 4. |

Adding 10–20 of these covers the majority of real friction.

### 4. MCP wildcards eliminate the most prompts per line.

If you use MCP servers — Slack, Google Drive, Asana, Calendar, Gmail — the highest-leverage pattern is a server-level wildcard:

```json
{
  "permissions": {
    "allow": [
      "mcp__claude_ai_Slack__*",
      "mcp__claude_ai_Google_Drive__*",
      "mcp__claude_ai_Asana__*",
      "mcp__claude_ai_Gmail__*",
      "mcp__google-docs__*"
    ]
  }
}
```

One wildcard pre-approves every tool from that server. In a typical knowledge-work session with several active MCP servers, this single category of rules eliminates more prompts than anything else.

### 5. Read and Edit deny rules block built-in tools — not arbitrary scripts.

> Read and Edit deny rules apply to Claude's built-in file tools and to file commands Claude Code recognizes in Bash, such as `cat`, `head`, `tail`, and `sed`. They do not apply to arbitrary subprocesses that read or write files indirectly, like a Python or Node script that opens files itself. For OS-level enforcement that blocks all processes from accessing a path, [enable the sandbox](https://code.claude.com/docs/en/sandboxing).

For real guarantees that a path is off-limits — `.env` files, secrets directories — pair a `Read(./.env)` deny rule with sandboxing enabled. The deny rule alone won't stop a Python script that opens the file with `open()`.

### 6. The `:*` and ` *` suffixes are equivalent — at the end only.

> The `:*` suffix is an equivalent way to write a trailing wildcard, so `Bash(ls:*)` matches the same commands as `Bash(ls *)`.

Pick whichever form reads better. The permission dialog writes the space form when you click "Yes, don't ask again."

The `:*` form is only recognized at the end. In a pattern like `Bash(git:* push)`, the colon is treated as a literal character and won't match git commands. Use `Bash(git * push)` for "any git command whose last token is push."

### 7. Permission rules merge across scopes. Everything else overrides.

> Permission rules behave differently because they merge across scopes rather than override.

The precedence order for settings in general, highest to lowest: managed > command line arguments > local project (`.claude/settings.local.json`) > shared project (`.claude/settings.json`) > user (`~/.claude/settings.json`).

Local settings beat project settings — the reverse of how most people expect it.

For permissions specifically, the scopes union rather than replace. If a managed-level rule denies a command, no project-level allow rule can undo it. If your user-level `~/.claude/settings.json` allows an MCP server globally, project-level rules add new allowances without revoking the global ones.

This union behavior is the source of most "why is this still blocked?" confusion: a deny rule at any scope wins, regardless of an allow rule at another scope.

### 8. Process wrappers are stripped before matching.

> Before matching Bash rules, Claude Code strips a fixed set of process wrappers so a rule like `Bash(npm test *)` also matches `timeout 30 npm test`. The recognized wrappers are `timeout`, `time`, `nice`, `nohup`, and `stdbuf`.

Bare `xargs` (with no flags) is also stripped, so `Bash(grep *)` matches `xargs grep pattern`. But `xargs` with flags — like `xargs -n1 grep pattern` — is not stripped and is matched as an `xargs` command.

You don't need separate `Bash(timeout npm test)` rules. The wrapper list is built in and not configurable.

These are not in the auto-strip list: `watch`, `setsid`, `ionice`, `flock`, `find -exec`, `find -delete`, and `xargs` with flags. These always prompt. For those, an exact-match rule is required if you want to skip the prompt.

### 9. Settings file scope picks itself.

Three files, three purposes:

| File | Scope | Use for | Git status |
| :--- | :--- | :--- | :--- |
| `~/.claude/settings.json` | You, every project | MCP servers you always trust, your shell preferences | Personal — not tracked |
| `.claude/settings.json` | Everyone on this repo | Team agreements: "we always allow `npm run test`", deny rules for secrets | Committed to git |
| `.claude/settings.local.json` | You, this repo only | Project-specific paths, in-flight experimentation | Gitignored by default |

The "do I have to re-approve next session?" question has a clear answer: no. Both `.json` files persist across sessions, reboots, and new terminal windows. Claude Code watches these files and reloads them when they change — edits apply to the running session without a restart.

---

## Widely thought but not useful

### Adding `Bash(ls:*)`, `Bash(cat:*)`, `Bash(echo:*)` to your allowlist.

Not needed. These are on the built-in read-only list. Most existing `.claude/settings.local.json` files accumulate 5–10 of these from "accept once and remember" dialogs. They're harmless but obscure which rules are actually doing work. Clean them up on a quarterly pass.

### Copying the exact compound string into your allowlist after a prompt.

When `cd /abs/path && find ... | head -10` prompts, the temptation is to paste that exact string. The matcher will never see that compound again — the next variant won't match. Address the subcommand that's actually failing: usually a tool not on the auto-list (`sed`, `git`, `gh`).

### Using `Bash(*)` to skip everything.

Tempting if you trust your own judgment. But:

> Command injection detection: Suspicious bash commands require manual approval even if previously allowlisted.
> Fail-closed matching: Unmatched commands default to requiring manual approval.

`Bash(*)` doesn't skip everything. Claude Code's safety classifier still re-prompts on commands it flags as risky. You give up a readable audit trail of what you've trusted without getting full bypass in return.

If you want unattended execution for a specific task, use `--permission-mode bypassPermissions` for that session instead. Even bypass mode prompts for `rm -rf /` and `rm -rf ~` as a circuit breaker.

### Constraining Bash arguments via patterns.

> Bash permission patterns that try to constrain command arguments are fragile. For example, `Bash(curl http://github.com/ *)` intends to restrict curl to GitHub URLs, but won't match variations like:
> - Options before URL: `curl -X GET http://github.com/...`
> - Different protocol: `curl https://github.com/...`
> - Redirects: `curl -L http://bit.ly/xyz` (redirects to github)
> - Variables: `URL=http://github.com && curl $URL`
> - Extra spaces: `curl  http://github.com`

For domain restrictions, use `WebFetch(domain:github.com)` and a deny rule on `Bash(curl *)`. For dynamic policies, use a [PreToolUse hook](https://code.claude.com/docs/en/hooks-guide).

### Believing settings expire when you restart.

They don't. `.claude/settings.local.json` is a file on disk. It persists across sessions, reboots, and new terminals. The rules "go away" only if you edit the file, delete it, or work in a different repository.

### Redundant variants of the same command.

A real allowlist excerpt:

```
"Bash(curl -sS -o /dev/null -w \"%{http_code}\\\\n\" https://qa-newsletter-pmapapyfla-uc.a.run.app/healthz)",
"Bash(curl -sS -w \"\\\\nHTTP %{http_code}\\\\n\" https://qa-newsletter-pmapapyfla-uc.a.run.app/healthz)",
"Bash(curl -sS -o /dev/null -w \"HTTP %{http_code}\\\\n%{redirect_url}\\\\n\" -L https://qa-newsletter-pmapapyfla-uc.a.run.app/healthz)",
"Bash(curl -sS -o /dev/null -w \"HTTP %{http_code}\\\\n\" https://qa-newsletter-pmapapyfla-uc.a.run.app/)",
"Bash(curl *)"
```

The last line makes the first four redundant. This happens because "yes, don't ask again" got clicked early in a session, then a broader pattern was added later. Prune periodically.

---

## Starter recipe for a typical knowledge-work setup

If you're starting from scratch, this covers most friction. Drop into `.claude/settings.local.json`:

```json
{
  "permissions": {
    "allow": [
      "mcp__claude_ai_Slack__*",
      "mcp__claude_ai_Google_Drive__*",
      "mcp__claude_ai_Google_Calendar__*",
      "mcp__claude_ai_Gmail__*",
      "mcp__claude_ai_Asana__*",
      "mcp__google-docs__*",
      "WebFetch",
      "Bash(git *)",
      "Bash(gh *)",
      "Bash(gcloud *)",
      "Bash(python3 -c:*)",
      "Bash(python3 *.py)",
      "Bash(sed -n:*)",
      "Bash(awk:*)",
      "Bash(unzip -p:*)",
      "Bash(unzip -l:*)",
      "Bash(date)",
      "Bash(date +*)",
      "Bash(curl -s:*)",
      "Bash(curl -sS:*)",
      "Read(//tmp/**)"
    ],
    "deny": [
      "Read(./.env)",
      "Read(./.env.*)",
      "Read(./secrets/**)"
    ]
  }
}
```

For reference: a one-year-old `.claude/settings.local.json` from heavy daily use accumulated 213 lines. Most were one-shot exact-command approvals from "yes, don't ask again." A periodic audit can shrink it to ~50 useful lines — the redundancy from the read-only list removed, and one-shot approvals promoted to wildcards.

You can also add `"$schema": "https://json.schemastore.org/claude-code-settings.json"` at the top of the file for inline validation and autocomplete in VS Code and Cursor.

---

## Audit checklist

Run through your `.claude/settings.local.json` once a quarter:

1. Remove rules for commands on the built-in read-only list: `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`, `diff`, `stat`, `du`, `cd`, read-only `git`.
2. Remove exact-command strings covered by a broader wildcard elsewhere in the file (e.g., specific `curl` invocations covered by `Bash(curl *)`).
3. Promote per-tool MCP rules (`mcp__claude_ai_Slack__slack_read_thread`) to server-level wildcards (`mcp__claude_ai_Slack__*`) once you've used 3+ tools from the same server.
4. Flag any `Bash(...)` rules that try to constrain arguments. Replace with WebFetch domain rules or hooks.
5. Move tool-class wildcards (MCP servers, common CLIs) up to `~/.claude/settings.json` so they apply across projects.

---

## Sources & Attribution

- Anthropic, Claude Code: Configure permissions — primary source on permission-rule syntax, wildcards, compound-command decomposition, read-only allowlist, process wrappers, and tool-specific gotchas. ([https://code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions))
- Anthropic, Claude Code: Settings — settings file locations, precedence, merge order, hot-reload behavior. ([https://code.claude.com/docs/en/settings](https://code.claude.com/docs/en/settings))
- Anthropic, Claude Code: Security — permission architecture, command injection detection, fail-closed matching, sandbox model. ([https://code.claude.com/docs/en/security](https://code.claude.com/docs/en/security))
- Anthropic, Claude Code: Settings JSON schema — add as `$schema` in your file for autocomplete and inline validation in VS Code and Cursor. ([https://json.schemastore.org/claude-code-settings.json](https://json.schemastore.org/claude-code-settings.json))

All claims in this guide were verified against the live docs as of 2026-05-22.

**Corrections from prior circulating versions:**

Two errors in earlier drafts of this guide:

1. The settings precedence order was stated as "managed > project > local > user." The correct order is managed > command line > local > project > user. Local settings override project settings, not the reverse.
2. The process-wrapper list omitted bare `xargs`. Bare `xargs` (no flags) is pre-stripped before matching, so `Bash(grep *)` covers `xargs grep pattern`. `xargs` with flags is not stripped.

---

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's public documentation. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.
