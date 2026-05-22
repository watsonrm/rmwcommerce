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

3. **Pick a contained first project.** Ask the user what they want to try. Steer toward: a static personal website, a small CLI script, a one-file data transformation. Steer away from: anything touching production, multi-user systems, paid APIs without spend caps. Success: a one-sentence project description with a clear "done" criterion.

4. **Set up safety basics.** Propose running git init and writing a `.gitignore` that excludes `.env`, credentials, and OS junk. Show the user the proposed `.gitignore` contents before applying. Success: project directory has a git repo and gitignore, committed as the first commit.

5. **Draft CLAUDE.md via /init.** Tell the user to run `/init` so Claude can draft a project context file. Review the draft together — keep it under 200 lines, cut anything that does not help. Success: a committed `CLAUDE.md` the user has actually read.

6. **Take one small swing at the project.** Ask the user to describe in plain English what they want, with a specific success criterion ("the page shows my name and a photo", "the script prints a CSV with two columns"). Propose the smallest change that gets there. Success: user approves and the change applies cleanly.

7. **Demonstrate the approval loop.** Before each Bash command or file write, pause and explain in one line what it will do and why. If the user asks "what does this do," answer plainly. If they say "stop" or "wrong direction," halt and ask what to try instead. Success: user has redirected at least once and seen what that feels like.

8. **Commit the working state.** As soon as something works, propose a commit with a short message describing what now works. Do not batch multiple unrelated changes. Success: `git log` shows a commit the user can point at.

9. **Show recovery in plain English.** Tell the user they never need to learn git commands to recover. They can say: "something broke, take us back to the last working state," or "undo your last changes," or `/clear` to start fresh with tighter scope. Success: user can repeat back at least one of these phrases.

10. **Stop while ahead.** Once one thing works and is committed, end the session. Do not start a second feature. Tell the user that disorientation in the first couple hours is normal.

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
