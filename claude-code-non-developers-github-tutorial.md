---
title: "Make Your Work Survive Your Laptop: Your First Private GitHub Repo (A Paste-Along Tutorial for Non-Developers)"
description: Your Claude Code project lives in one folder on one laptop. If the laptop dies, gets stolen, or you accidentally delete the folder, the project is gone. A private GitHub repo fixes that in 30 minutes — and unlocks portability, history-on-your-phone, fearless experimentation, and a future where bringing on a collaborator is one invite click. This guide is the paste-along walkthrough. Exact prompts, exact commands, and a deliberate "pretend you lost your laptop" recovery exercise so you feel the backup work before you ever actually need it.
date: 2026-05-27
author: Rick Watson
agent_friendly: true
keywords: GitHub for non-developers, private GitHub repo tutorial, backup Claude Code project, gh CLI tutorial, first GitHub push, non-developer git push, recover laptop project from GitHub, GitHub Claude Code, push private repo Claude
---

# Make Your Work Survive Your Laptop: Your First Private GitHub Repo

**Your Claude Code project lives in one folder on one laptop. If the laptop dies, gets stolen, or you accidentally delete the folder, the project is gone. A private GitHub repo fixes that in 30 minutes — and unlocks portability, history-on-your-phone, fearless experimentation, and a future where bringing on a collaborator is one invite click. This guide is the paste-along walkthrough. Exact prompts, exact commands, and a deliberate "pretend you lost your laptop" recovery exercise so you feel the backup work before you ever actually need it.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-27 · Roughly 10 min read · 30 min to complete*

Who this is for: a non-developer who has completed [Your First Project: A Paste-Along Tutorial](claude-code-non-developers-first-tutorial.md) and has a working `my-first-site` folder on their Desktop with a few commits in it. If you don't have that yet, do that tutorial first.

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what you will do

| Step | What you do | What you'll feel |
|:--|:---|:---|
| 1 | Create a free GitHub account (skip if you have one) | Standard signup, two minutes |
| 2 | Ask Claude to install the `gh` command-line tool | Eating the dog food — Claude installs Claude's neighbor |
| 3 | Authenticate `gh` with your GitHub account | One slightly fiddly browser handoff, then you're in |
| 4 | Ask Claude to create a private repo from your project | Your work is now backed up |
| 5 | Visit the repo on github.com and see your code | "Oh — my work is on the internet now (privately)." |
| 6 | Make a change locally, commit, push | The new loop: edit → commit → push |
| 7 | **Pretend you lost your laptop. Delete the local folder. Clone it back.** | The backup working — this is the point of the exercise |
| 8 | Name what you just unlocked | Confidence about backup, portability, collaboration |

You can skip the reading and start at Step 1.

---

## Why a private repo specifically (60 seconds)

Public vs private is the first question GitHub asks you. For a non-developer who is using GitHub as a safety net (not as a portfolio), private is the right default. You are not publishing to the internet — you are putting your work in a vault that only you can see.

What a private repo unlocks for you:

1. **Backup.** Your laptop dies tomorrow. Your work is fine. Clone it onto a new machine; keep going.
2. **Portability.** Install Claude Code on a different computer (your iPad with a keyboard, a hotel laptop, a coworking desktop). Clone the repo. You're exactly where you left off.
3. **History on your phone.** GitHub renders your commit log nicely. You can look at what you changed last Tuesday from your phone, in line at coffee.
4. **Fearless experimentation.** Try something wild locally. If it fails, the GitHub copy is the snapshot you clone fresh from. The local mess goes in the trash.
5. **One-click collaboration when you're ready.** A year from now when you want a freelancer to help, they're an invite away. The repo is already there. No retrofit.

Private = none of this requires you to be ready to show your work to the world. That's the unlock.

---

## Before you start: two checks

1. **You completed [tutorial 1](claude-code-non-developers-first-tutorial.md).** Your `~/Desktop/my-first-site` folder exists, has a working `index.html`, and has at least two commits.
2. **Claude Code is open in that folder.** In Terminal: `cd ~/Desktop/my-first-site && claude`. You should see the Claude Code prompt.

That's it. No editor, no GitHub experience, no command-line background beyond what you already did in tutorial 1.

---

## Step 1 — Create a free GitHub account (2 minutes; skip if you have one)

Go to [github.com/signup](https://github.com/signup) in your browser. Use a personal email you'll keep forever — switching accounts later is annoying.

Pick a username you won't be embarrassed by. Lowercase, no numbers if you can avoid them. Yes, it shows up in URLs of any repo you make public later.

Verify the email. Free plan. You're done. Note your username — you'll need it in two minutes.

---

## Step 2 — Ask Claude to install the `gh` command-line tool (3 minutes)

`gh` is GitHub's official command-line tool. You won't type its commands yourself; Claude will. But it needs to exist on your machine first.

Paste this into Claude Code:

> *"Install the GitHub CLI tool, `gh`, on my machine. Pick whichever installation method is most appropriate for my operating system (Homebrew on macOS, winget on Windows, apt on Linux, etc.) and explain in one sentence what you're about to run before running it. Wait for my approval. After it installs, confirm by running `gh --version`."*

Claude will detect your OS and propose one install command. Approve. After install, it runs `gh --version` and shows you the version number. That's confirmation it worked.

If you hit an error — "Homebrew not installed" is the most common one on a fresh Mac — paste the error back to Claude with: *"That failed — fix it and try again."* Claude will install whatever prerequisite is missing and retry.

---

## Step 3 — Authenticate `gh` with your GitHub account (5 minutes)

This is the fiddliest step in the whole tutorial. It involves a brief browser handoff. Read this whole section before starting.

Paste this into Claude Code:

> *"Run `gh auth login` to authenticate me with GitHub. I want to use GitHub.com, HTTPS protocol, authenticate Git with my GitHub credentials, and log in via web browser. Walk me through what happens at each prompt and tell me when I need to do something in my browser."*

What's about to happen:

1. Claude runs `gh auth login` and accepts the defaults you just specified.
2. The terminal will display a **one-time code** that looks like `XXXX-XXXX`. **Copy it.**
3. The terminal will say something like "Press Enter to open github.com in your browser." Press Enter.
4. Your browser opens to a GitHub page that says "Device Activation."
5. Paste the code from step 2. Click Continue. Click Authorize.
6. Switch back to the terminal. You'll see "✓ Logged in as your-username."

If the browser doesn't open automatically, GitHub gives you a URL (something like `https://github.com/login/device`). Open it manually and paste the code there.

**If anything goes wrong**, paste the exact error into Claude: *"that didn't work, here's what I see: [paste]. Fix it."* The most common failures are (a) the code expired because too much time passed — start over from the prompt — or (b) you authorized the wrong GitHub account because you have multiple browser tabs logged in as different users. Both are recoverable; Claude knows.

---

## Step 4 — Ask Claude to create a private repo from your project (3 minutes)

The payoff step. Paste this into Claude Code:

> *"Create a private GitHub repository called `my-first-site` from this folder. Use the `gh` CLI. Push the current branch as the initial state. Set up `origin` as the remote. Confirm afterward by showing me the repo URL on GitHub."*

Claude proposes the command. It'll look roughly like:

```bash
gh repo create my-first-site --private --source=. --remote=origin --push
```

Approve. In about ten seconds, Claude tells you the URL — something like `https://github.com/your-username/my-first-site`.

Your work is now backed up. That's it. That was the step.

---

## Step 5 — Visit the repo on github.com and see your code (1 minute)

Open the URL Claude gave you. You'll see your repository on GitHub:

- A file list showing `.gitignore`, `index.html`, and any other files
- Your commit history (the messages you wrote when you committed in tutorial 1)
- A green "Code" button you'd use to clone the repo onto another machine

Click `index.html`. GitHub renders your HTML as the raw code, with line numbers. (To see the page itself rendered in a browser, you'd need GitHub Pages — a topic for the next session.)

Take a beat. Your work is on the internet now. Only you can see it. That's the new reality.

---

## Step 6 — Make a change, commit, push (3 minutes)

You now have one more rep added to your workflow: **push**. The full loop is now describe → review → approve → commit → push.

Paste:

> *"Change the sentence on the page to: '[YOUR NEW SENTENCE]'. Show me the diff before saving. After I approve, commit with a short message, then push to GitHub."*

Claude shows the diff. Approve. Claude saves, commits, and pushes — three steps you used to do separately. Refresh the GitHub repo page in your browser. You'll see the new commit at the top of the history.

That's the loop forever now. Edit → commit → push. The push step takes one second and gives you a backup of every working state.

---

## Step 7 — Pretend you lost your laptop (5 minutes)

This is the most important step in this tutorial. Most non-developers never get a safe chance to feel the backup work. You're about to.

Quit Claude Code by typing `/exit` (or pressing Ctrl+C twice).

Now, in Terminal, delete the entire local project — like your hard drive failed:

```bash
cd ~/Desktop
rm -rf my-first-site
```

(`rm -rf` deletes a folder and everything in it. You'd never run this on real work without thinking; we're doing it deliberately on a project that's backed up.)

Verify it's gone:

```bash
ls ~/Desktop | grep my-first-site
```

(That command should print nothing — the folder is gone from your Desktop.)

Feel the small drop. That's the feeling you'd have if you hadn't pushed to GitHub. You're about to make it go away in one command.

Now clone it back from GitHub. Replace `your-username` with your actual GitHub username:

```bash
gh repo clone your-username/my-first-site
cd my-first-site
ls
```

You see your files back. All of them. Every commit you ever made.

Re-open Claude Code in the folder:

```bash
claude
```

You're exactly where you left off. Different folder on disk (it was just re-created), but identical contents, identical history, identical everything that matters.

That's the backup, working. You just felt it.

---

## What you just unlocked

Out loud, in order:

- **Backup.** Your project survives anything that happens to your laptop. You just proved it.
- **Portability.** You can install Claude Code on any other machine (a borrowed laptop, a new one, a desktop at the coworking spot) and `gh repo clone` to be exactly where you left off.
- **History on your phone.** Open github.com on your phone. Navigate to the repo. You can read every commit message and every line of every file. From the line at coffee.
- **Fearless experimentation.** Anything you try locally that goes wrong, you can `rm -rf` the folder and `gh repo clone` your way back to safety. You just rehearsed the exact recovery.
- **Collaboration-ready.** When you eventually want to bring on a freelancer, friend, or contractor, they're one invite click away. The repo is already there.

That's the entire unlock. You got it in 30 minutes without learning a single git command beyond `commit` and `push` — both of which Claude runs for you.

---

## What to do next

Pick one.

- **Push your other projects.** Anything else you've built (or will build) gets the same `gh repo create ... --private --source=. --remote=origin --push` treatment. Ask Claude to do it; the prompt from Step 4 works on any folder.
- **Deploy the page publicly.** When you're ready for a public URL, ask Claude: *"Set up GitHub Pages for this repo so my index.html is reachable at a public URL."* That moves you from "private backup" to "live website." Save it for session three.
- **Set up Claude Code on a second machine.** Install Claude Code on another laptop, run `gh auth login` again, then `gh repo clone your-username/my-first-site`. You'll have your work in two places. Useful when you travel.
- **Read the why.** [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — mindset and question templates. The right thing to read on the couch after two sessions of doing.

---

## When this tutorial doesn't go smoothly

**"`gh: command not found` after Step 2 installs."** Close the terminal, open a new one, and try again. The new terminal will pick up the install path. If that still fails, paste the install output back to Claude and ask: *"the install said it succeeded but `gh --version` says command not found — what's wrong?"*

**"The browser handoff in Step 3 failed and I don't know what state I'm in."** Run `gh auth status` (Claude can do this). If it says "not logged in," start the auth from scratch. If it says "logged in" but with the wrong account, run `gh auth logout` first, then re-do Step 3.

**"`gh repo create` said the repo already exists."** Someone else (or a past you) already claimed that name on your account. Pick a different name: `my-first-site-2`, `rick-personal-site`, whatever. Re-run the Step 4 prompt with the new name.

**"`git push` was rejected after Step 6."** This usually means the remote has commits your local doesn't (maybe you edited a file on github.com). Paste the error to Claude with: *"my push was rejected, here's the error: [paste]. Walk me through fixing it without losing my work."* Claude will pull, merge, and re-push.

**"I want to delete the GitHub repo and start over."** Ask Claude: *"Delete the `my-first-site` repo from my GitHub account, then re-do Steps 4 through 6 from scratch."* Claude will use `gh repo delete --yes` (with your confirmation). The local folder stays untouched.

**"I accidentally pushed something I didn't want public."** Since the repo is **private**, this is much less urgent than if it were public. Still — if there's a credential or secret in a commit, ask Claude: *"I committed a secret to this repo. The repo is private. Walk me through removing it from the history and rotating the secret at the provider."* The private status buys you time; you don't have to rush.

---

## Sources & Attribution

This is a first-party tutorial. The commands come from GitHub's own CLI documentation and from Git's documentation.

**Primary sources:**

- GitHub CLI documentation, `gh auth login`. ([cli.github.com/manual/gh_auth_login](https://cli.github.com/manual/gh_auth_login)) — web-browser auth flow and protocol choice.
- GitHub CLI documentation, `gh repo create`. ([cli.github.com/manual/gh_repo_create](https://cli.github.com/manual/gh_repo_create)) — `--private`, `--source`, `--remote`, `--push` flag semantics.
- GitHub Docs, "About repositories." ([docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories](https://docs.github.com/en/repositories/creating-and-managing-repositories/about-repositories)) — public vs private distinction; private repo access rules.

**Related work in this series:**

- [Your First Session](claude-code-non-developers-first-session.md) — install Claude Code, conservative permissions. The prerequisite to tutorial 1.
- [Your First Project: A Paste-Along Tutorial](claude-code-non-developers-first-tutorial.md) — the project this tutorial backs up. The prerequisite to this one.
- [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — mindset and question templates. Read after this.
- [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md) — what to read when permission prompts start feeling constant.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
