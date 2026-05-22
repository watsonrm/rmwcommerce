# Claude Code for Non-Developers: Your First Session

**A hands-on companion to the field guide — from installation through your first working project.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- You can have Claude Code installed, safety rails configured, and a git repository initialized in under an hour.
- Setting up safety first — before building anything interesting — is the single decision that separates a smooth first 10 hours from a painful one.
- The failure modes in the [field guide](claude-code-for-non-developers.md) are not hypothetical. They happen on day one to people who skip rows 1–3 of the table below and jump straight to "let me build something."
- By the end of your first real session you'll have a working project, a commit history to roll back from, and a personal sense of where your gaps are.

### Where to spend your time, in priority order — first 10 hours

Ranked by time-to-value multiplied by blast-radius prevention. Most readers will want to skip rows 1–3 and start building. Do not do that.

| # | What to do | Why now | Time |
|:--|:-----------|:--------|:-----|
| 1 | Install Claude Code + set conservative permission defaults | Before you can do anything dangerous, set up the brakes | 30 min |
| 2 | Initialize git in your project directory + write `.gitignore` | First commit = first undo button. Your safety net for everything that follows. | 15 min |
| 3 | Set up the secrets pattern (`.env` + gitignore entry) | Cheapest mistake to prevent; most expensive to clean up after | 15 min |
| 4 | Pick a contained first project + draft a `CLAUDE.md` under 200 lines | The container for your work. Project boundaries prevent scope creep. | 1 hour |
| 5 | First session: describe what you want in plain English, review what Claude proposes | The actual work. By now your safety rails are in place. | 2–4 hours |
| 6 | Daily ritual: `git commit` at every working state | Cheap insurance. Costs seconds, saves hours. | 30 sec per checkpoint |

Most readers should get rows 1–3 done in a single afternoon and not build anything they care about keeping until row 4 is complete.

---

## How to use this guide

Work through it in order, the first time through. Sections 1–3 are setup; do those before you touch any project work. Sections 4–6 are the first real session. Sections 7–9 are references you'll come back to when things go wrong or you're ready to go deeper.

If you haven't read [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) yet, start there. This guide assumes you've absorbed that one — specifically the six-item concept curriculum and the failure modes section.

---

## Section 1: Install Claude Code + set conservative permissions

### Install

Anthropic's quickstart documentation is the authoritative source for installation steps: [code.claude.com/docs/en/quickstart](https://code.claude.com/docs/en/quickstart). Read it before the commands below — the doc covers platform-specific details for macOS, Windows, and Linux that this guide doesn't duplicate.

The one-liner for macOS and Linux:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://claude.ai/install.ps1 | iex
```

After installation, confirm it worked:

```bash
claude --version
```

You need a Pro, Max, Team, or Enterprise account. The free Claude.ai plan does not include Claude Code access. ([source](https://code.claude.com/docs/en/getting-started))

### Set conservative permissions — do this before your first session

The permissions system is what separates "Claude Code as a powerful tool" from "Claude Code as a thing that deletes your files." Anthropic's documentation describes a tiered system with three approval behaviors:

> "Read-only: File reads, Grep — Approval required: No. Bash commands: Shell execution — Approval required: Yes. File modification: Edit/write files — Approval required: Yes." ([source](https://code.claude.com/docs/en/permissions))

The default mode (`default`) prompts for permission on first use of each tool. That's your starting point. Don't change it until you understand what you're doing.

Three things to configure before your first real session:

**1. Don't enable `bypassPermissions` mode.** This skips all permission prompts. Anthropic's own documentation warns: "Only use this mode in isolated environments like containers or VMs where Claude Code cannot cause damage." ([source](https://code.claude.com/docs/en/permissions)) For a first session on your main machine, this mode has no place.

**2. Understand what each tool type does.** Read-only tools (file reads, grep) run without a prompt. Bash commands and file modifications always prompt by default. When Claude proposes a Bash command you don't recognize, ask it to explain before you approve.

**3. Build an explicit Bash allowlist.** You can allow specific safe commands so they don't require approval every time, while everything else still prompts. A reasonable starting allowlist looks like this in your project's `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": [
      "Bash(git status)",
      "Bash(git log *)",
      "Bash(git diff *)",
      "Bash(ls *)",
      "Bash(npm run *)",
      "Bash(python *)"
    ]
  }
}
```

Expand this list only when you understand what a command does. The full permission rule syntax — including wildcards, deny rules, and tool-specific patterns — is documented at [code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions).

---

## Section 2: Git init + .gitignore (the undo button)

Every working state you commit is a state you can return to. Without commits, when Claude Code produces something broken and you can't figure out what changed, you have nowhere to go. This happens to everyone in the first 10 hours. The only variable is whether you have a safety net when it does.

### Initialize a repository

Open a terminal in the directory where your project lives:

```bash
cd /path/to/your/project
git init
```

If this directory doesn't exist yet, create it first:

```bash
mkdir my-project
cd my-project
git init
```

### Write a .gitignore before your first commit

This file tells git which files to never track. Create it in your project root before anything else:

```
# Secrets — never commit these
.env
.env.local
.env.*.local

# Package dependencies — recreated from manifest, not committed
node_modules/
__pycache__/
*.pyc
.venv/
venv/

# System files
.DS_Store
Thumbs.db

# Logs and temp files
*.log
*.tmp
```

Claude Code can generate this for you — just ask: "Create a .gitignore for a [Python/Node.js/whatever] project." Verify that `.env` is in there before you proceed.

### Make your first commit

```bash
git add .
git commit -m "Initial commit"
```

That first commit is your floor. Everything you build from here has a return point.

### The daily rhythm

Don't commit at the end of the day. Commit whenever something works. Specifically: any time you can describe what you have as "working," commit it. That description becomes your commit message.

```bash
git add .
git commit -m "CSV parser reads input file and strips whitespace"
```

Twenty seconds of friction versus hours of recovery. The Pro Git book — free at [git-scm.com/book/en/v2](https://git-scm.com/book/en/v2) — is the authoritative reference if you want to go deeper on any of this.

---

## Section 3: The secrets pattern (the cheap insurance)

A secret is any string that grants access to a paid or sensitive system: API keys, database passwords, authentication tokens. The rule is absolute — secrets never appear in your code files and never get committed to any repository, public or private.

### What a .env file is

A `.env` file sits at the root of your project and holds your secrets in a simple format:

```
OPENAI_API_KEY=sk-...
DATABASE_URL=postgres://user:password@host/db
STRIPE_SECRET_KEY=sk_live_...
```

Your code reads these as environment variables rather than having the values typed directly into the source. This separation is the core argument of the Twelve-Factor App methodology: "The twelve-factor app stores config in environment variables. Env vars are easy to change between deploys without changing any code; unlike config files, there is little chance of them being checked into the code repo accidentally." ([source](https://12factor.net/config))

Claude Code reads from `.env` automatically in most project types. When you ask Claude to connect to an API, tell it to use an environment variable rather than a hardcoded key.

### The non-negotiable rule

`.env` must be in your `.gitignore`. Always. Every project. Before the first commit.

If you ask Claude Code to set up a project from scratch, tell it explicitly: "Set up a .env file for secrets and add it to .gitignore immediately." Verify the .gitignore entry before you commit anything.

### What to do if you committed a key

Act in this order, immediately:

1. Go to the service that issued the key — OpenAI, Stripe, AWS, wherever — and revoke it. Generate a new one.
2. Update your local `.env` with the new key.
3. Add `.env` to `.gitignore` if it isn't already.
4. Make a new commit.

Don't spend time trying to remove the key from git history first. Bots scan public repositories constantly. By the time you've figured out how to rewrite history, the key may already be compromised. Revoke first, then clean up. The old key is dead either way once you revoke it.

---

## Section 4: Pick a contained first project

The first project should teach you Claude Code's mechanics without exposing you to production risk. Here are four good options, ranked by safety.

### Option 1: A static personal site

A site with HTML files, maybe a CSS file, no backend. Jekyll and Eleventy (11ty) are two static site generators that Claude Code handles well. The worst that goes wrong is the site looks wrong. No data loss, no charges, no multi-user impact.

Why it's a good first project: immediate visual feedback, no environment complexity, completely self-contained. You can commit early and often because every state either looks right or doesn't.

### Option 2: A personal CLI script

A script that does one thing on your own machine — organize your downloads folder by file type, rename photos by date, convert a folder of files from one format to another. Runs only when you run it. Touches only your files. No network calls.

Why it's a good first project: you'll understand exactly what it does because you specified it, you can test it on a copy of your data, and the scope is naturally narrow.

### Option 3: A data transformation script

Read a CSV, do something to the data, write a new CSV. Maybe filter rows, rename columns, or reformat dates. Nothing writes back to a database or calls an API.

Why it's a good first project: data work is common in non-developer contexts (spreadsheets, exports, reports), the input and output are easy to inspect, and you can verify the result visually.

### Option 4: A simple automation for personal use

Fetch your own data from a service you already pay for, format it, and write it somewhere useful. Pulling your own email into a daily summary, for instance.

Why it's a good first project but worth a caveat: this starts involving API calls, which means environment variables and rate limits. Do option 1 or 2 first if this is your first week.

### What not to build first

Anything that touches money (payment processors, subscription logic). Anything multi-user (authentication, databases with other people's data). Anything that calls a paid API in a loop without a spend cap set at the provider level. These categories don't mean "never build them with Claude Code" — they mean "not until you've built something smaller first and understand what you're approving."

---

## Section 5: Writing a first CLAUDE.md

`CLAUDE.md` is the configuration file Claude Code loads at the start of every session. It's how you tell Claude about your project — its purpose, its structure, the commands you run, and any conventions you care about.

Anthropic's memory documentation is direct on sizing: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." ([source](https://code.claude.com/docs/en/memory)) This isn't a soft suggestion. Files longer than that produce worse results because the instructions occupy context space that Claude needs for the actual work.

### A minimal first CLAUDE.md

Create this file at the root of your project directory. Fill in the bracketed sections:

```markdown
# [Project Name]

[One sentence: what this project does and why it exists.]

## Key commands

- Start/run: [e.g., `python main.py` or `npm start`]
- Test: [e.g., `python -m pytest` or `npm test`]
- Install dependencies: [e.g., `pip install -r requirements.txt` or `npm install`]

## File layout

- `[main entry file]` — [what it does]
- `[data or config folder]` — [what lives there]

## Conventions

- [Any specific decisions Claude should know: naming patterns, libraries in use, anything you've decided once and don't want relitigated]

## What not to do

- [Anything off-limits: don't call external APIs in tests, don't commit the .env file, etc.]
```

Run `/init` inside Claude Code to have it generate a starting `CLAUDE.md` automatically. Claude will analyze your project files and draft something reasonable. Edit it down rather than adding more — shorter, more specific instructions produce better behavior.

For the deeper treatment of what goes into an effective CLAUDE.md, see [Pillar 1 of the Claude Code Workflow Optimizer](claude-code-optimizer.md).

---

## Section 6: Your first session — the actual mechanics

You have installation done, git initialized, `.gitignore` written, first commit made, secrets pattern set up, a project scope chosen, and a `CLAUDE.md` drafted. Now:

**Open Claude Code from your project directory.**

```bash
cd /path/to/your/project
claude
```

Claude reads your `CLAUDE.md` immediately on startup. If something in there is wrong or incomplete, fix it before you go further — it's the context Claude works from.

**Describe what you want in plain English, with specific success criteria.**

Vague: "Build me a script that handles my files."

Better: "Write a Python script that reads all .jpg files from my `~/Downloads` folder, checks the EXIF date, and moves each file into a subfolder named `YYYY-MM` based on when the photo was taken. If a file has no EXIF date, move it to a `no-date` folder."

The specificity matters. Claude will ask clarifying questions when it needs more, but a precise first prompt produces a closer first draft.

**Read what Claude proposes before you approve it.**

When Claude proposes to run a Bash command, read it. Not skim it — read it. If you don't understand what it does, type: "Before running that, explain what this command does and what it will change." Claude will explain. This is not a sign of weakness or inexperience; it's correct behavior.

When Claude proposes file edits, look at the diff. You don't need to understand every line. You need to notice if Claude is touching files you didn't ask it to touch, or if anything looks structurally off.

**When things go off-track, say so.**

If Claude writes something that's heading in the wrong direction, don't keep approving and hope it corrects. Stop. Say: "This isn't what I meant. Let me re-explain." Then describe the problem differently. Three rounds of approving wrong code is harder to undo than one correction.

**Commit at every working state.**

Any time you can run the code and it works — even partially — commit. You're building a ladder, not a high dive.

```bash
git add .
git commit -m "Script reads Downloads folder and lists files by extension"
```

Then continue. If the next thing breaks, you have that rung to fall back to.

---

## Section 7: When things go wrong — recovery rituals

### You broke something and don't know what changed

```bash
git status    # shows which files have changed since last commit
git diff      # shows the actual line-by-line changes
```

Read the diff. If you can't tell what Claude changed from the diff alone, describe the symptom to Claude: "The script was working after my last commit. Since then, something changed and now I'm getting [error]. Here's what git diff shows." Claude can often diagnose from the diff.

If the diff is too large to reason about, use `git stash` to set everything aside temporarily and return to your last commit state. You haven't lost the changes — they're stored in the stash.

### You want to undo the last set of changes

If you haven't committed since things broke:

```bash
git checkout -- .    # reverts all unstaged changes to last committed state
```

If you've committed something broken and want to go back:

```bash
git reset --hard HEAD~1    # removes the last commit and reverts the files
```

Use `git log` first to see your commit history and confirm you know which state you're reverting to. `--hard` is permanent for the working directory — make sure you want it.

### You want to throw away a whole experimental direction

Before you start anything speculative, branch off:

```bash
git checkout -b experiment/new-approach
```

Build on the branch. If it works, merge it back. If it doesn't, delete the branch and return to main:

```bash
git checkout main
git branch -d experiment/new-approach
```

This costs 10 seconds before you start. It saves the pain of an awkward reset after.

### Claude is going in circles

Stop. Run `/clear` to start a fresh session. Then restart with a tighter scope than you started with. If the original prompt was "build the whole thing," narrow it to one specific piece. Circular behavior usually means the context has gotten tangled — the conversation is carrying too much history of attempts that didn't work. A fresh session with a precise prompt almost always unsticks it.

### You committed a secret

Revoke and rotate the key immediately at the service provider. Generate a new one, update your `.env`, verify `.gitignore` has the `.env` entry. Then commit. Don't try to remove the key from git history as your first move — that's a slow process and the key is already compromised the moment it hit a public remote. Kill the key first. Cleanup second.

---

## Section 8: First 10 hours — what to expect

Hour 1–2: disorientation. You're reading diffs you don't fully understand, approving things you're not certain about, and possibly getting errors you don't know how to interpret. This is normal. Every non-developer goes through it. The safety rails you set up in sections 1–3 mean the disorientation can't turn into catastrophe.

Hour 3–5: you'll have one or two moments where the model does something surprising and useful. A function you described in plain English that works on the first try. An error you couldn't decode that Claude explains clearly. These moments are why you're here.

Hour 6–8: you'll make your first real mistake. A command you approved that you shouldn't have, or a direction you pursued that turned out to be wrong, or an environment issue that breaks something. This is the learning. Your git history and your permissions setup are what make this recoverable rather than catastrophic.

Hour 9–10: you'll have a working first project. Not perfect, but working. And you'll have a personal sense of where your skill gaps are. Maybe it's that you don't understand error messages well enough to diagnose them. Maybe it's that your `CLAUDE.md` is too vague and Claude keeps misunderstanding the scope. Whatever it is, you'll know.

Past hour 10: move to the optimizer.

---

## Section 9: Where to go next

[Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — the prerequisite to this guide. The concept curriculum, the failure modes, and the mindset shift. If you came here first, go back and read that.

[Claude Code Workflow Optimizer](claude-code-optimizer.md) — once you're working in Claude Code regularly, this is where you cut token spend and sharpen your workflow. Pillar 1 (CLAUDE.md hygiene) is the most immediately applicable. Start there.

[The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when you start wondering whether to package your work as something more reusable. Most people climb this ladder too fast; this guide helps you know when you're ready.

[Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — only if you've committed to building a multi-agent system at the API level. Read the ladder guide first.

---

## Sources & Attribution

**Tier 1 — primary, data-bearing sources:**

- Anthropic Claude Code getting started and advanced setup documentation. ([code.claude.com/docs/en/getting-started](https://code.claude.com/docs/en/getting-started)) — installation steps, account requirements, platform support. Verified HTTP 200, 2026-05-22.
- Anthropic Claude Code permissions documentation. ([code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions)) — permission tiers, default mode behavior, `bypassPermissions` warning, Bash allowlist syntax. Verified HTTP 200, 2026-05-22.
- Anthropic Claude Code memory documentation. ([code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)) — CLAUDE.md 200-line guidance, quoted: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." Verified HTTP 200, 2026-05-22.
- The Twelve-Factor App, Factor III: Config. ([12factor.net/config](https://12factor.net/config)) — environment variable pattern for secrets and configuration, quoted directly. Verified HTTP 200, 2026-05-22.
- Scott Chacon and Ben Straub, Pro Git (free online). ([git-scm.com/book/en/v2](https://git-scm.com/book/en/v2)) — authoritative reference for git commands and concepts. Verified HTTP 200, 2026-05-22.

**Related work in this series:**

- [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — the why piece; prerequisite to this guide.
- [Claude Code Workflow Optimizer](claude-code-optimizer.md) — the next read after your first 10 hours.
- [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when to graduate from prompts to skills to agents.
- [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — architecture for multi-agent systems at scale.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
