# Claude Code for Non-Developers: Your First Session

**A hands-on companion to the field guide — from installation through your first working project, focused on the one skill that matters most: the approval process.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- You can have Claude Code installed, permissions configured conservatively, and the safety basics set up in under an hour.
- The approval process — reading what Claude proposes before clicking yes — is your actual job. This guide is built around that.
- You don't need to learn git commands, `.gitignore` syntax, or `.env` patterns. Ask Claude to handle all of that, then review what it proposes.
- By the end of your first real session you'll have a working project, a commit history to roll back from, and a personal sense of where your gaps are.

### First-session priorities, in order

| # | First-session move | Why now |
|:--|:---|:---|
| 1 | Install Claude Code + set conservative permission defaults | Preserve the approval process before you start; don't auto-approve everything |
| 2 | Ask Claude to set up safety basics for the project | Delegate the technical setup; read and approve what Claude proposes |
| 3 | Pick a contained first project | Scope is the difference between a useful first session and a rabbit hole |
| 4 | Have Claude draft your `CLAUDE.md` | Project context for every future session |
| 5 | Start working — describe what you want in plain English | The actual work |
| 6 | Ask Claude to commit at every working state | Cheap insurance |

---

## How to use this guide

Work through it in order the first time. Section 1 is install and permissions — do that before anything else. Sections 2–5 are the setup sequence. Sections 6–9 are the first real session and what comes after.

If you haven't read [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) yet, start there. This guide assumes you've absorbed the mindset shift, the question templates, and the failure modes in that one.

---

## Section 1: Install Claude Code + set conservative permissions

### Install

Anthropic's quickstart documentation is the authoritative source: [code.claude.com/docs/en/quickstart](https://code.claude.com/docs/en/quickstart). Read it before the commands below — the doc covers platform-specific details for macOS, Windows, and Linux that this guide doesn't duplicate.

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

### Set conservative permissions — and understand why

This is where the approval process starts. Before you run a single session, configure Claude Code so that you, not the tool, are deciding what happens.

Anthropic's documentation describes what requires approval by default:

> "Read-only: File reads, Grep — Approval required: No. Bash commands: Shell execution — Approval required: Yes. File modification: Edit/write files — Approval required: Yes." ([source](https://code.claude.com/docs/en/permissions))

The default mode prompts for permission on first use of each tool. That's your starting point. Don't change it until you understand what you're doing.

Three things to configure before your first real session:

Don't enable `bypassPermissions` mode. This skips all permission prompts. Anthropic's own documentation warns: "Only use this mode in isolated environments like containers or VMs where Claude Code cannot cause damage." ([source](https://code.claude.com/docs/en/permissions)) For a first session on your main machine, this mode has no place.

When Claude proposes a Bash command you don't recognize, ask it to explain before you approve. This isn't weakness — it's the job. "Before running that, what does this command do and what will it change?" Claude will tell you. Approve informed; don't approve blind.

You can allow specific safe commands to run without prompting every time, while everything else still prompts. A reasonable starting allowlist in your project's `.claude/settings.json`:

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

Expand this list only when you understand what a command does. The full permission rule syntax is documented at [code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions).

---

## Section 2: Ask Claude to set up safety basics

This replaces what earlier versions of this guide taught as separate curricula for git, `.gitignore`, and secrets. You don't need any of that. You need one prompt.

At the start of any new project, before doing anything else, open Claude Code in your project directory and say:

> "Set up safety basics for this project — git initialized, .gitignore configured so I don't accidentally publish secrets, and any other defaults a non-developer should have."

Claude will propose what to do. Read what it proposes — not to understand every line, but to check that it looks like what you asked for. If anything looks off, ask before approving: "What does this do?" or "Why is that entry there?"

Approve. You're done. The technical setup is handled.

If you want to verify the result — which is a reasonable thing to do — ask Claude: "Is there anything in this project that I should be careful not to push to a public repository?" Claude will check.

That's the entire section. The implementation — git init, the `.gitignore` template, the `.env` pattern — belongs to Claude. The review and approval belong to you.

---

## Section 3: Your real job — the approval process

Non-developers often assume their job is to learn enough to understand what Claude is doing. That's the wrong frame. Your job is to pay attention before clicking yes.

The distinction matters. Understanding every line of code Claude writes is not a realistic goal, and chasing it leads to either paralysis or resignation. But attention — pausing when Claude proposes something, reading it, and asking about anything you don't recognize — that's achievable on day one.

What the approval process actually looks like:

When Claude proposes a Bash command, read it. If you recognize what it does, approve. If you don't, ask: "What does this command do and what will it change?" Then decide. This takes ten seconds. Skipping it is how things go wrong.

When Claude proposes file edits, look at the diff. You don't need to understand every line. You need to notice if Claude is touching files you didn't ask it to touch, or if anything looks structurally off. A diff that changes twenty files when you asked about one file is a signal to ask questions before approving.

When Claude is about to make a multi-step change, ask it to walk you through the plan first: "What are you about to do?" Review the plan. Approve the plan, then let it run. This is especially useful for anything that involves deleting files or modifying configuration.

When something looks wrong — wrong output, unexpected behavior, a direction that's clearly off — stop. Don't approve three more rounds hoping it self-corrects. Say: "This isn't what I meant. Let me re-explain." Then describe the problem differently. One good correction is easier than unwinding several rounds of wrong work.

The approval process doesn't slow you down. It's what keeps the tool working for you instead of against you.

---

## Section 4: Pick a contained first project

The first project should teach you Claude Code's mechanics without exposing you to production risk.

A static personal site is the safest option. A site with HTML files, maybe a CSS file, no backend. Jekyll and Eleventy (11ty) are two static site generators that Claude Code handles well. The worst that goes wrong is the site looks wrong — no data loss, no charges, no multi-user impact.

A personal CLI script is equally safe. A script that does one thing on your own machine: organize your downloads folder by file type, rename photos by date, convert a folder of files from one format to another. Runs only when you run it. Touches only your files.

A data transformation script is also good for a first project. Read a CSV, do something to the data, write a new CSV. Nothing writes to a database or calls an API. Input and output are easy to inspect.

A personal automation that fetches your own data from a service you already pay for is a reasonable step up — but it involves API calls and environment variables. Do one of the above first if this is your first week.

What not to build first: anything that touches money, anything multi-user, anything that calls a paid API in a loop without a spend cap set at the provider level. These aren't permanent exclusions — they mean "not until you've built something smaller first and understand what you're approving."

---

## Section 5: Have Claude draft your CLAUDE.md

`CLAUDE.md` is the configuration file Claude Code loads at the start of every session. It tells Claude about your project — its purpose, structure, commands, and conventions. Without it, Claude starts each session cold.

Ask Claude to create it: run `/init` inside Claude Code, and Claude will analyze your project files and draft a starting `CLAUDE.md`. ([source](https://code.claude.com/docs/en/memory))

Review what it drafts. Edit it down rather than adding more. Anthropic's guidance on sizing is direct: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." ([source](https://code.claude.com/docs/en/memory)) More than 200 lines and you're paying for context space that Claude needs for the actual work.

The things worth keeping in a first `CLAUDE.md`: what the project does, how to run it, what files do what, and any conventions you've decided once and don't want relitigated. Everything else is probably noise.

For a deeper treatment of what makes an effective `CLAUDE.md`, see [Pillar 1 of the Claude Code Workflow Optimizer](claude-code-optimizer.md).

---

## Section 6: Your first session — the actual mechanics

You have installation done, permissions set conservatively, safety basics configured, a project scope chosen, and a `CLAUDE.md` drafted. Now:

Open Claude Code from your project directory:

```bash
claude
```

Claude reads your `CLAUDE.md` immediately on startup. If something in there is wrong or incomplete, fix it before you go further — it's the context Claude works from.

Describe what you want in plain English, with specific success criteria.

Vague: "Build me a script that handles my files."

Better: "Write a Python script that reads all .jpg files from my `~/Downloads` folder, checks the EXIF date, and moves each file into a subfolder named `YYYY-MM` based on when the photo was taken. If a file has no EXIF date, move it to a `no-date` folder."

The specificity matters. Claude will ask clarifying questions when it needs more, but a precise first prompt produces a closer first draft.

Then: apply the approval process from Section 3. Read before approving. Ask about anything unfamiliar. Stop and redirect when something's heading wrong.

When something works — ask Claude to commit it: "Commit this — describe what's working." That's a working state preserved. Keep going.

---

## Section 7: When things go wrong — recovery without git commands

### You broke something and don't know what changed

Ask Claude: "Something broke. Show me what changed since the last commit and take us back to the last working state."

Claude can see the diff, explain what changed, and revert. You don't need to know the git commands yourself.

### You want to undo the last set of changes

Ask Claude: "Undo your last set of changes."

If you want to be more specific about which state to return to, say: "Take us back to when [the specific thing] was working." Claude has the commit history and can navigate it.

### Claude is going in circles

Stop. Run `/clear` to start a fresh session. Restart with a tighter scope than you started with. If the original prompt was "build the whole thing," narrow it to one specific piece. Circular behavior usually means the context has gotten tangled — the conversation is carrying too much history of attempts that didn't work. A fresh session with a precise prompt almost always unsticks it.

### You think you committed a secret

Ask Claude: "Did I just commit any secrets? If so, what do I need to do?"

Claude will check the recent commits and, if it finds something, walk you through revoking the key at the service provider and cleaning up the repository. Revoke first — don't spend time on git history cleanup while the key is still live. Once it's revoked, the old key is dead regardless of what's in the history.

### You want to try something experimental without risking what works

Ask Claude: "Make a commit of the current state so I have a checkpoint, then let's try something different."

You don't need branches. A checkpoint commit is enough. If the experiment fails, ask Claude to take you back to that commit.

---

## Section 8: First 10 hours — what to expect

Hours 1–2: disorientation. You're reading diffs you don't fully understand, approving things you're not certain about, possibly getting errors you don't know how to interpret. This is normal. Every non-developer goes through it. The conservative permissions and the safety basics you set up earlier mean the disorientation can't turn into catastrophe.

Hours 3–5: you'll have one or two moments where Claude does something surprising and useful. A function you described in plain English that works on the first try. An error you couldn't decode that Claude explains clearly and fixes. These moments are why you're here.

Hours 6–8: you'll make your first real mistake. A command you approved that you shouldn't have, or a direction you pursued that turned out to be wrong, or something that broke and you're not sure why. This is the learning. Your commit history and your permissions setup are what make this recoverable rather than catastrophic.

Hours 9–10: you'll have a working first project. Not perfect, but working. And you'll have a personal sense of where your gaps are — maybe your prompts are too vague, maybe you're approving too fast, maybe your `CLAUDE.md` is too thin. Whatever it is, you'll know.

Past hour 10: move to the optimizer.

---

## Section 9: Where to go next

[Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — the prerequisite to this guide. The mindset shift, the question templates, and the failure modes. If you came here first, go back and read that.

[Claude Code Workflow Optimizer](claude-code-optimizer.md) — once you're working in Claude Code regularly, this is where you cut token spend and sharpen your workflow. Pillar 1 (CLAUDE.md hygiene) is the most immediately applicable.

[The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when you start wondering whether to package your work as something more reusable. Most people climb this ladder too fast; this guide helps you know when you're ready.

[Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — only if you've committed to building a multi-agent system. Read the ladder guide first.

---

## Sources & Attribution

**Tier 1 — primary, data-bearing sources:**

- Anthropic Claude Code getting started documentation. ([code.claude.com/docs/en/getting-started](https://code.claude.com/docs/en/getting-started)) — installation steps, account requirements, platform support. Verified HTTP 200, 2026-05-22.
- Anthropic Claude Code permissions documentation. ([code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions)) — permission tiers, default mode behavior, `bypassPermissions` warning, Bash allowlist syntax. Verified HTTP 200, 2026-05-22.
- Anthropic Claude Code memory documentation. ([code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory)) — CLAUDE.md 200-line guidance and `/init` command. Quoted: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." Verified HTTP 200, 2026-05-22.

**Related work in this series:**

- [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — the why piece; prerequisite to this guide.
- [Claude Code Workflow Optimizer](claude-code-optimizer.md) — the next read after your first 10 hours.
- [The Prompts-to-Agents Ladder](the-prompts-to-agents-ladder.md) — when to graduate from prompts to skills to agents.
- [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — architecture for multi-agent systems at scale.

**Corrections from prior circulating versions:**

The prior version of this guide taught git commands (`git reset --hard`, `git checkout -- .`, `git stash`), `.gitignore` templates, `.env` file patterns, virtualenv setup, and branch management as direct skills for non-developers. That framing turned this guide into a junior developer tutorial. The reframe is intentional: non-developers should ask Claude to handle those implementations, then review and approve what Claude proposes. The recovery section (Section 7) has been rewritten to reflect question-to-Claude patterns rather than git command recipes.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
