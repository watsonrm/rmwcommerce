---
title: "Your First Claude Code Project: A Paste-Along Tutorial for Non-Developers"
description: Most "first project" advice tells non-developers to pick something. Choosing the project is the hardest part for someone who has never built anything. This guide hands you one specific project (a one-page personal site), gives you the exact prompts to paste, tells you what to look for at each step, and walks you through a deliberate break-and-recover exercise so you feel the safety net work. About 45 minutes start to finish. You will end with a working page, a commit history, and the muscle memory for the approval loop.
date: 2026-05-27
author: Rick Watson
agent_friendly: true
keywords: Claude Code tutorial non-developer, first Claude Code project, paste-along Claude Code, Claude Code HTML site tutorial, Claude Code beginner project, what to build first Claude Code, Claude Code approval loop tutorial, Claude Code commit tutorial, recover from a mistake Claude Code
---

# Your First Claude Code Project: A Paste-Along Tutorial for Non-Developers

**Most "first project" advice tells non-developers to pick something. Choosing the project is the hardest part for someone who has never built anything. This guide hands you one specific project (a one-page personal site), gives you the exact prompts to paste, tells you what to look for at each step, and walks you through a deliberate break-and-recover exercise so you feel the safety net work. About 45 minutes start to finish. You will end with a working page, a commit history, and the muscle memory for the approval loop.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-27 · Roughly 12 min read · 45 min to complete*

Who this is for: a non-developer who has Claude Code installed and a paid Claude account, but has not actually built anything yet. If you do not have Claude Code installed, start with [Your First Session](claude-code-non-developers-first-session.md) — the **Right Now** block at the top gets you installed in ten minutes, and then come back here.

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what you will do

| Step | What you do | What you'll feel |
|:--|:---|:---|
| 1 | Make a folder, open Claude Code in it | "OK, I'm in." |
| 2 | Paste the safety-basics prompt | Watching git, .gitignore, and the first commit get set up *for* you |
| 3 | Approve each step after a quick look | First reps of the approval loop |
| 4 | Paste the build-the-page prompt with your name in it | Anticipation |
| 5 | Approve the file, then open it in your browser | "I made a thing." |
| 6 | Commit the working state | Save game |
| 7 | Change the sentence, commit again | Loop feels normal already |
| 8 | **Break the page on purpose, then recover with one prompt** | The safety net working — this is the point of the exercise |
| 9 | Name what you just learned | Confidence |

You don't need to read more before starting. Skip to Step 1.

---

## Before you start: three checks

1. **Paid Claude account.** Pro, Max, Team, or Enterprise — the free Claude.ai tier does not include Claude Code. ([upgrade page](https://claude.ai/upgrade))
2. **Claude Code installed.** Open a terminal and type `claude --version`. You should see a version number, not "command not found." If you don't, run through the **Right Now** block in [Your First Session](claude-code-non-developers-first-session.md) before this tutorial.
3. **A browser open** in another window. You will use it to view the page you build.

That's it. No editor, no framework knowledge, no git background.

---

## Step 1 — Make the folder and open Claude Code (1 minute)

In Terminal, paste this exact line for your platform:

```bash
# macOS / Linux
mkdir ~/Desktop/my-first-site && cd ~/Desktop/my-first-site && claude
```

```powershell
# Windows PowerShell
mkdir $env:USERPROFILE\Desktop\my-first-site; cd $env:USERPROFILE\Desktop\my-first-site; claude
```

What just happened: you made a new empty folder on your Desktop called `my-first-site`, moved into it, and launched Claude Code inside that folder. Claude Code's prompt should now be ready for you to type.

If it isn't, the most common cause is that `claude --version` doesn't actually work yet — close the terminal, open a new one, and try again. The new terminal will pick up the install.

---

## Step 2 — Paste the safety-basics prompt (3 minutes)

Copy this verbatim and paste it into the Claude Code prompt:

> *"I'm new to Claude Code. I'm not a developer. Set up safety basics for this folder — initialize git, write a .gitignore that keeps secrets and OS junk out of the repository, and make a first commit. Explain each command in one sentence before running it, and wait for me to approve each one. One step at a time."*

Two things to notice in that prompt:

- **"Explain each command in one sentence before running it."** This forces Claude to teach you what it's doing as it goes. You won't have to look anything up.
- **"One step at a time."** Without this, Claude might bundle several commands into a single approval. You want each one separate at first so the rhythm of the approval loop sinks in.

---

## Step 3 — Approve each step (after actually looking) (3 minutes)

Claude will propose three things in sequence. For each one, do this:

**Read the one-sentence explanation.** It will be plain English. "I'm going to initialize git so we can track changes." That's the kind of sentence to expect.

**Look at what's about to happen.** For `git init`, there's nothing visual — it just creates a hidden folder. For `.gitignore`, Claude will show you the file contents before saving. You'll see lines like:

```
.env
.DS_Store
node_modules/
*.log
```

You do not need to know what each line does. You need to recognize: "this looks like a list of file types to exclude." That's enough.

**Approve.** Press the approve key (Claude Code will show you which one).

**If anything looks weird** — Claude wants to touch files outside this folder, the list is enormous, anything that doesn't match what it just described — type *"What is that for?"* and read the answer before approving. This is the meta-skill.

After three approvals (git init, .gitignore, first commit), you have a safety net. Anything that happens next, you can roll back.

---

## Step 4 — Paste the build-the-page prompt (2 minutes)

Now the visible part. Before pasting the prompt below, swap in your own name and one sentence about what you do.

> *"Now build me a single-page personal HTML site. It should have my name as the heading and one sentence underneath that says: 'I run a marketing consultancy helping retail brands grow their direct-to-consumer business.' Use simple inline CSS — center the content, readable font, nothing fancy. One file, called index.html. No JavaScript, no frameworks, no separate stylesheet. Show me the file before saving and explain in one sentence what each major part does."*

Edit the sentence in quotes to be about you. Keep everything else exactly as written.

---

## Step 5 — Approve the file, then open it (3 minutes)

Claude will show you the proposed `index.html`. It will look something like this:

```html
<!DOCTYPE html>
<html>
  <head><title>Your Name</title></head>
  <body style="font-family: sans-serif; max-width: 600px; margin: 4em auto; text-align: center;">
    <h1>Your Name</h1>
    <p>Your sentence here.</p>
  </body>
</html>
```

What to check: does it have your name? Does it have your sentence? Yes? Approve.

The CSS details don't matter for the first session. You are not auditing the code — you are confirming the thing Claude is about to save matches what you asked for. That is the entire approval skill.

Once it saves, ask Claude:

> *"Open index.html in my default browser so I can see it."*

A browser tab opens. You see your page. Take a beat. You shipped a thing.

---

## Step 6 — Commit the working state (1 minute)

Type:

> *"Commit this — describe what works now."*

Claude proposes a commit message like *"Add initial one-page personal site with name and headline."* Approve.

You now have a save point. If anything breaks after this, you can come back to exactly this state with one prompt. That's the second meta-skill the rest of this tutorial is built around.

---

## Step 7 — Change the sentence, commit again (2 minutes)

Pick a new sentence — anything. Type:

> *"Change the sentence on the page to: 'I help retail leadership teams make sharper decisions about commerce, AI, and what to bet on next.' Show me the diff before saving."*

(Use your own sentence, not mine.)

Claude shows you the diff — the lines that will change. Approve. Refresh the browser tab. New sentence is live.

Then:

> *"Commit this."*

That's the entire workflow: describe → review → approve → commit. You will do this exact loop thousands of times in your Claude Code life. You just did it twice in ten minutes.

---

## Step 8 — Break it on purpose, then recover (5 minutes)

This is the most important step in this tutorial. Most non-developers never get a safe, deliberate chance to feel the recovery work. You are about to.

Paste this:

> *"Break the page on purpose — delete a critical piece of the HTML so it renders blank or visibly broken. Don't tell me what you deleted. Save the change. Don't commit it."*

Refresh the browser tab. Page is blank, or visibly broken.

Pause. Notice the small drop in your chest. That's the feeling you'd have on a real project if you hadn't been committing. You're about to make it go away in one prompt.

Paste:

> *"Take us back to the last working state."*

Claude reads the git log, identifies the most recent commit, and restores the file. Refresh the browser. Page is back to your last committed sentence.

You just did, in plain English, what most developers do with `git reset --hard HEAD`. You don't need to know that command exists. Claude knows. You just need to know the English version: *"take us back to the last working state."*

That recovery — that exact prompt — is the safety net the rest of this series of guides keeps pointing at. You just felt it work.

---

## What you just learned

Out loud, in order. (Reading it silently doesn't lock it in. Say it.)

- You installed Claude Code and ran your first project.
- You set up the safety basics for a project — git, .gitignore, first commit — by asking Claude. You did not memorize any of the commands.
- You approved Claude's proposed changes after reviewing them. That is the entire meta-skill of Claude Code for non-developers. Everything else is reps.
- You built a webpage that renders in a browser.
- You changed it and committed the working state.
- You broke it on purpose and recovered with one English-language prompt.

That is everything a non-developer needs to use Claude Code productively. The next thirty hours of your practice are reps of those same skills on bigger projects. There is no further mountain to climb before you start.

---

## What to do next

Pick one. Not several.

- **Read the why.** [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) explains the mindset behind what you just did. It's the right thing to read on the couch after the first session, not before.
- **Pick a second project.** Section 4 of [Your First Session](claude-code-non-developers-first-session.md#section-4-pick-a-contained-first-project) has three second-project options (a CLI script, a CSV transform, a personal automation). Pick the one that maps to a real chore in your week.
- **Add a photo to your page.** Drop a JPG into the `my-first-site` folder and ask Claude: *"Add this photo to the page, centered above my name, sized so it fits nicely. Show me the diff."* That's the next rep of the same approval loop. (Then commit.)
- **Deploy the page.** When you're ready, ask: *"What's the simplest way to put this page on the public internet?"* Claude will walk you through GitHub Pages, Netlify, or similar. Save that for session two — you don't need it today.

When permission prompts start interrupting you constantly, that's the signal to read [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md). Not before.

---

## When this tutorial doesn't go smoothly

**"Claude wants me to approve something that doesn't match what it described."** Don't approve. Type *"that doesn't match what you said you were going to do — explain again."* The approval loop only works if you stop when something looks off.

**"My browser tab is blank and I don't know why."** Ask Claude: *"The page is blank in my browser. Check what's in index.html and tell me what's wrong."* It will diagnose and propose a fix. Approve the fix.

**"Claude keeps proposing more changes than I asked for."** Type *"stop — I only asked for one thing. Roll back any changes you've made since my last prompt and do just the one thing I asked for."* Scope discipline is something you'll get from Claude on request; you don't have to enforce it manually.

**"I lost track of what state the project is in."** Type *"Walk me through the current state of the project — what files exist, what the last commit was, and what's uncommitted."* Claude will summarize. This is also the answer when you come back to the project a week later.

**"I want to start over."** Quit Claude Code (`Ctrl+C` twice or type `/exit`), delete the `my-first-site` folder from your Desktop, and restart from Step 1. The whole tutorial fits in under an hour even on a second pass — there's no cost to starting over.

---

## Sources & Attribution

This is a first-party tutorial. The commands and the approval-loop framing come from Anthropic's own documentation and from the related guides in this series.

**Primary sources:**

- Anthropic Claude Code getting started documentation. ([code.claude.com/docs/en/getting-started](https://code.claude.com/docs/en/getting-started)) — install, account requirements.
- Anthropic Claude Code permissions documentation. ([code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions)) — approval defaults, Bash allowlist behavior.

**Related work in this series:**

- [Claude Code for Non-Developers: A Field Guide](claude-code-for-non-developers.md) — the mindset and question-templates piece. Read after your first session.
- [Your First Session](claude-code-non-developers-first-session.md) — install, conservative permissions, and the broader narrative this tutorial is the practical 45-minute cut of.
- [Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md) — what to read when permission prompts start to feel constant.
- [The Claude Code Workflow Optimizer](claude-code-optimizer.md) — once you have ten hours of Claude Code under your belt.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
