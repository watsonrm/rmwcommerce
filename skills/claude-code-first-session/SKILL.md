---
name: claude-code-first-session
description: Walk a first-time non-developer Claude Code user through their initial ~30-minute session — install check, safety setup, tiny first project, approval workflow, commit. Trigger when user says "I just installed Claude Code", "first time using this", "I'm new to Claude Code", "walk me through my first session", "what should I do first", "help me get started", or "got it open now what".
---

## When to use this skill

Invoke on these triggers:

- "I just installed Claude Code"
- "first time using this" / "I'm new"
- "walk me through my first session"
- "what should I do first" / "where do I start"
- "help me get started"
- "I got it open, now what"

If the user is past their first session and asking about ongoing work, do not use this skill — hand off to `claude-code-for-non-developers`.

## What we're going to do

This is a first session, not a tutorial. Goal: one small working result, committed to git, with the user understanding the approval process. Aim for ~30 minutes. Avoid scope creep. The skill the user is actually learning is "decide before approving" — not coding.

## First-session procedure

Run these in order. After each step, wait for the user before moving on.

1. **Confirm install.** Ask the user to confirm Claude Code is running in a terminal and they can see the prompt. Success: they paste back the welcome screen or confirm it is open.

2. **Set conservative permissions.** Tell the user not to enable `bypassPermissions`. Explain: every Bash command will pop an approval — that is the point. Success: user acknowledges they will read before clicking yes.

3. **Give the user the first project — do not ask them to pick one.** The default project is a one-page personal HTML site that says their name and one sentence about what they do. Picking the project is the hardest part for a non-developer; you remove that friction by handing them one. The canonical walkthrough is [Your First Project: A Paste-Along Tutorial](https://github.com/watsonrm/rmwcommerce/blob/main/claude-code-non-developers-first-tutorial.md) — follow its 9-step sequence verbatim. If the user pushes for something more ambitious, say "let's get one thing committed first, then session two can be whatever you want." Success: user agrees to the default and is ready for step 4.

4. **Set up safety basics.** Propose running git init and writing a `.gitignore` that excludes `.env`, credentials, and OS junk. Show the user the proposed `.gitignore` contents before applying. Run each command one at a time and explain in one sentence before each one. Success: project directory has a git repo and gitignore, committed as the first commit.

5. **Skip `/init` and CLAUDE.md for a one-file project.** A single-file HTML site does not need a CLAUDE.md — the file *is* the project. Save `/init` and CLAUDE.md drafting for session two when there's actually structure worth describing. Don't burn first-session attention on configuration that won't pay off until later.

6. **Build the page.** Ask the user for their name and one sentence about what they do. Propose a single `index.html` with inline CSS — no JavaScript, no frameworks, no separate stylesheet. Show the file before saving and explain in one sentence what each major part does. Open it in the user's default browser after saving (`open index.html` on macOS, `start index.html` on Windows, `xdg-open index.html` on Linux). Success: user sees their page render in a browser.

7. **Demonstrate the approval loop.** Before each Bash command or file write, pause and explain in one line what it will do and why. If the user asks "what does this do," answer plainly. If they say "stop" or "wrong direction," halt and ask what to try instead. Success: user has redirected at least once and seen what that feels like.

8. **Commit the working state.** As soon as something works, propose a commit with a short message describing what now works. Do not batch multiple unrelated changes. Success: `git log` shows a commit the user can point at.

9. **Make one change, commit again.** Have the user change the sentence to something different. Show the diff before saving. Approve. Commit. This second rep is what makes the approval loop feel normal instead of foreign. Success: two commits in `git log`.

10. **The break-and-recover exercise.** This is the most important step. Ask Claude (yourself, in the session) to *"break the page on purpose — delete a critical piece of the HTML so it renders blank or visibly broken, save the change, don't commit, and don't tell me what you deleted."* Have the user refresh their browser and see the broken page. Then have them paste: *"Take us back to the last working state."* Restore via git. Have them refresh — page is back. This is the safety net the rest of their Claude Code life depends on; making them feel it work once locks it in. Success: user has experienced a recovery from a deliberate break.

11. **Name what they learned.** Before they close the terminal, walk through what they did out loud: installed Claude Code, set up safety basics by asking Claude, approved proposed changes after reviewing them, built a webpage, committed working states, broke something and recovered with one English prompt. That list is everything a non-developer needs.

12. **Stop while ahead.** Do not start a second feature. Tell the user the first hour or two is supposed to feel disorienting; that fades by hour five.

## Things to watch for in a first session

- User trying to ship a full app in session one — push back, shrink scope to one visible result.
- User clicking approve without reading — slow down, narrate each command in one line, ask them to read the diff out loud once.
- Secrets risk — if the user mentions API keys, passwords, or `.env` files, stop and confirm gitignore covers them before any commit.
- Too-ambitious first project (production systems, paid APIs, multi-user) — redirect to a contained sandbox project.
- User getting lost in unfamiliar diffs — acknowledge it is normal hours 1–2, summarize the diff in plain English, keep moving.
- Circular progress where the same fix keeps failing — call it out, suggest `/clear` and a tighter restart rather than piling on more changes.

## Wrap-up before ending the session

Confirm all of these before letting the user close the terminal:

- One thing works end-to-end and is committed.
- User knows the absolute path to the project directory on disk.
- User knows how to resume: open a terminal, `cd` to that path, run `claude`.
- User knows the recovery phrases ("take us back to the last working state", `/clear`).
- `.gitignore` is in place and no secrets are in the repo.

Tell the user what to expect next: hours 3–5 they will see Claude do something surprisingly useful; hours 6–8 they will hit their first real mistake and recover from it; by hours 9–10 they will have a working first project.

For ongoing work after the first session, hand off to the `claude-code-for-non-developers` skill.

---

Source article: https://github.com/watsonrm/rmwcommerce/blob/main/claude-code-non-developers-first-session.md
