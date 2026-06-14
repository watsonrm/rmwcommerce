---
title: "Where to Run Your Claude Automation: Local LaunchAgent vs. claude.ai Routines vs. Cloud Run"
description: A decision framework for choosing the right runtime surface for a Claude automation — covering cadence, uptime, auth, code delivery, local resource access, and the gotchas that bite you when you default to wherever you built it.
date: 2026-06-14
author: Rick Watson
agent_friendly: true
keywords: Claude automation, LaunchAgent, launchd, claude.ai routines, Cloud Run Jobs, Cloud Scheduler, scheduling Claude, where to run Claude, claude.ai scheduled routines, GCP Cloud Run, local vs cloud automation, Claude Code routines, cron floor, gcloud reauth, macOS sleep automation
---

# Where to Run Your Claude Automation: Local LaunchAgent vs. claude.ai Routines vs. Cloud Run

**A decision framework for choosing the right runtime surface — and the gotchas that burn you when you default to wherever you built it.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-06-14*

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- There are three distinct runtime surfaces for Claude automations, each with a different sweet spot. Choosing wrong doesn't break things immediately — it just causes silent failures you discover three days later when your Mac was off.
- The most common mistake is keeping an automation local because that's where you built it, then being surprised when overnight or weekend runs don't happen.
- The decision comes down to five questions: cadence, uptime requirement, auth model, whether the job needs to land code changes, and what local resources it touches.
- Each surface has one non-obvious gotcha that's cheap to avoid once you know it and expensive to debug after the fact.

### Where to spend your time, in priority order

| # | Decision | Why it matters | Effort |
|---|---|---|---|
| 1 | Determine uptime requirement first | If the automation must run when your Mac is off, the choice is already made — local is out | 5 min |
| 2 | Check cadence against the 1-hour floor | claude.ai routines reject sub-hour cron expressions; if you need faster, go local or Cloud Scheduler | 5 min |
| 3 | Decide before you build, not after | Retrofitting a local automation to cloud requires rethinking auth and state; it's not a copy-paste | 30 min |
| 4 | Wire the gcloud reauth before it bites you in production | Workspace session-control policy expires your credentials on a schedule your org controls | 15 min |
| 5 | Read what the cloud session actually pushes before assuming it lands on main | By default, claude.ai routines push to `claude/`-prefixed branches, not main | 5 min |

Most readers should answer the first two questions and pick a surface. The rest is setup detail.

---

## How to use this

The operational form of this guide is the Claude Code skill at [`skills/where-to-run-claude-automation/`](../skills/where-to-run-claude-automation/). Install it once:

```bash
# from a clone of this repo
mkdir -p ~/.claude/skills && cp -r skills/where-to-run-claude-automation ~/.claude/skills/
```

Then describe your automation — what it does, how often it needs to run, whether you need it overnight — and say one of these:

> "which surface should I run this automation on"
> "help me pick between local launchd and cloud routines"
> "audit my automation runtime choice"
> "why did my launchd job not run overnight"

Claude will load the skill and walk through the decision framework for your situation. The article below is the reasoning — read it for the *why*; the skill is the *how*.

---

## The decision table

This is the core framework. Match your requirements to the right column.

| | **Local (launchd / cron)** | **claude.ai Routines** | **GCP Cloud Run Jobs + Cloud Scheduler** |
|---|---|---|---|
| **Cadence floor** | Sub-second (launchd) / 1-minute (cron) | 1 hour minimum ([Anthropic docs](https://code.claude.com/docs/en/routines)) | 1 minute minimum ([Cloud Scheduler docs](https://cloud.google.com/scheduler/docs/creating)) |
| **Overnight / weekend uptime** | No — machine must be awake | Yes — Anthropic-managed cloud infrastructure | Yes — always-on |
| **Auth model** | Keychain, local tokens, ADC — all the local auth you already have | MCP connectors (OAuth as you), environment variables in the routine config | Service accounts, Secret Manager, Workload Identity |
| **Can it land code to main?** | Yes, full git push | By default, no — pushes to `claude/`-prefixed branches only; unrestricted push requires explicit opt-in per repo | Yes — your containerized job can push with a service account that has write permission |
| **Local resource access** | Full — local files, Keychain, local DBs, chat.db, local model index | None — runs in Anthropic's cloud; sees only cloned repos + connector tools | None — unless you mount Cloud Storage or call your own APIs |
| **Setup cost** | Near zero — plist file or crontab entry | Low — web UI or `/schedule` in the CLI, no servers | Real — containerize the job, deploy, wire Scheduler, manage secrets |
| **Best for** | Sub-hour cadence, dev iteration, jobs that need local resources or interactive auth | Recurring agentic tasks that authenticate via connectors and don't need your machine | Overnight ingestion, high-cadence cron, jobs that own their own secrets and run unattended |

---

## The three-question decision tree

**1. Does it need to run when your machine is off?**
Yes → not local. Go to question 2.

**2. Does it need sub-hour cadence?**
Yes → not claude.ai routines (1-hour floor). Use local launchd (if machine-on is acceptable) or Cloud Scheduler.

**3. Does it need to commit code that lands on a protected branch?**
Yes → not a cloud claude.ai session alone. Either wire a post-run merge step, enable unrestricted branch pushes in the routine config, or drive the commit from a Cloud Run job with the right service-account permission.

If you answered No to all three, any surface works — pick the one with the lowest setup cost.

---

## Surface 1 — Local: launchd and cron

**The sweet spot:** automations you're actively iterating on, jobs that need local resources — Keychain credentials, a local model index, a local database, `chat.db` for iMessage — and anything that must run faster than once an hour.

**How it works:** macOS `launchd` reads property-list files in `~/Library/LaunchAgents/` and fires jobs on schedule. `cron` does the same via `/usr/bin/crontab`. Both run as long as the machine is awake.

**The sleep distinction that matters:**

There are two local schedulers, and they handle sleep differently.

`launchd` with `StartCalendarInterval`: if the job was scheduled to fire while the Mac was asleep, **it runs when the machine wakes up.** It does not skip the missed run. ([Apple developer docs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html))

`cron`: if the system is asleep at the scheduled time, the job does not execute and does not catch up. It waits for the next scheduled time. The Apple developer docs are explicit: "If the system is turned off or asleep, `cron` jobs do not execute; they will not run until the next designated time occurs." ([Apple developer docs](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html))

If you need missed runs to fire on wake, use launchd, not cron. If your Mac was off (not sleeping) when a launchd job should have run, it also skips — the catch-up only applies to sleep, not power-off.

**The killer constraint:** none of this matters if the machine is off overnight. `pmset` scheduled-wake and Power Nap have narrow exceptions — Power Nap allows some background tasks on supported hardware — but neither is a reliable substitute for a cron scheduler on a machine that's asleep on a schedule you don't control. Anything that must run overnight or early-AM, every night, belongs in the cloud.

**When local is the right answer:**
- You're building and debugging — fast iteration, full local context
- The job needs to read a local file, query a local index, or touch `chat.db`
- You need sub-minute cadence (launchd supports it; cloud options don't)
- The job uses interactive auth that can't be packaged into a long-lived secret

---

## Surface 2 — claude.ai Routines

**The sweet spot:** recurring agentic tasks that authenticate entirely through MCP connectors (Google Drive, Slack, Linear, GitHub), where once-an-hour or slower is fine, and where you don't want to manage any infrastructure.

**How it works:** Create a routine at `claude.ai/code/routines` or with `/schedule` in the CLI. Specify a prompt, one or more GitHub repos, connectors, and a trigger (schedule, API, or GitHub event). Anthropic's cloud infrastructure runs the session. ([Anthropic docs](https://code.claude.com/docs/en/routines))

**Gotcha A — the 1-hour floor:**
The minimum scheduling interval is one hour. Cron expressions that fire more frequently are rejected by the platform. This is documented behavior: "The minimum interval is one hour; expressions that run more frequently are rejected." ([Anthropic docs, routines scheduling](https://code.claude.com/docs/en/routines)) If your automation needs to run every 15 minutes, every 30 minutes, or on any sub-hour cadence, claude.ai routines cannot do it. Use local launchd or Cloud Scheduler.

**Gotcha B — code lands on `claude/` branches by default:**
A cloud routine session can edit files and push commits — but by default, pushes go to branches prefixed with `claude/`, not to `main` or any protected branch. This is intentional: the platform prevents routines from accidentally modifying long-lived branches. To push to other branches, you must explicitly enable "Allow unrestricted branch pushes" per repository in the routine config. ([Anthropic docs](https://code.claude.com/docs/en/routines))

The implication: if you want a cloud session to edit code and land it on `main`, you need to either enable unrestricted pushes (which removes the safety guard) or design the workflow so a human reviews and merges the `claude/` branch. Don't design a routine that expects to commit directly to `main` without that explicit opt-in.

**Gotcha C — the session only sees what you point it at:**
The routine clones the repositories you specify and can use MCP connectors you include. It cannot read your local files, your Keychain, your local database, or anything else on your machine. If your automation's prompt says "read the current state from that SQLite file on my Mac," it won't work in a cloud routine. That resource either needs to be in a connected repo, reachable via a connector, or replaced with a cloud-hosted equivalent.

**When cloud routines are the right answer:**
- Daily or weekly recurring agentic workflows — backlog grooming, PR review, docs drift checks
- Connectors handle all auth — no long-lived secrets to manage yourself
- You want the job to run when your laptop is closed
- The routine's output is a PR, a Slack post, a Drive doc, or some other connector-writable artifact

---

## Surface 3 — GCP Cloud Run Jobs + Cloud Scheduler

**The sweet spot:** always-on, always-unattended, any cadence down to 1 minute, jobs that own their own secrets, and jobs where the container is what needs to run (not a Claude reasoning session — those belong in surface 2).

**How it works:** Package your job as a container, push it to Artifact Registry, create a Cloud Run Job, and attach a Cloud Scheduler trigger. The scheduler fires the job on your cron; the job runs to completion and exits. You pay only for execution time. ([Cloud Run Jobs docs](https://cloud.google.com/run/docs/create-jobs))

The Cloud Run primitive distinction matters: Cloud Run **Services** handle inbound HTTP requests and keep running between them. Cloud Run **Jobs** run to completion and exit — the right primitive for anything triggered on a schedule, not a request. ([Google Cloud docs](https://cloud.google.com/run/docs/create-jobs))

**On cadence:** Cloud Scheduler supports standard 5-field cron syntax and fires as frequently as every minute (`* * * * *`). Sub-minute scheduling is not supported. For most automation scenarios, per-minute is more than enough. ([Cloud Scheduler docs](https://cloud.google.com/scheduler/docs/creating))

**On cost:** the free tier is generous at low volume. Cloud Run Jobs includes 180,000 vCPU-seconds and 1 million requests per month at no charge. A job running once an hour for one minute on 1 vCPU uses roughly 3,600 vCPU-seconds per month — well inside the free tier. The pattern described in the companion guide ([Calling Google Cloud Services from Claude Code](guides/google-cloud-from-claude/index.md)) ran a set of hourly fetchers for under a dollar a month. ([Cloud Run pricing](https://cloud.google.com/run/pricing))

**On state:** Cloud Run containers are ephemeral. Each run starts fresh and has no memory of the previous run. If your job needs to track where it left off — a cursor, a "last processed" timestamp, a queue — that state must live outside the container: Cloud Storage, Firestore, a Cloud SQL row, or similar. This is not optional; it's the architecture.

**On secrets:** the right pattern is Secret Manager. Your container reads credentials from environment variables that are populated from Secret Manager at runtime — nothing sensitive in the container image, nothing in a prompt, nothing in a git repo. The Keychain stays the source of truth locally; Secret Manager is seeded from it once at deploy time. ([Secret Manager docs](https://cloud.google.com/secret-manager))

For the full setup mechanics — enabling APIs, deploying a job, wiring Cloud Scheduler, the secret proxy pattern — see the companion guide: [Calling Google Cloud Services from Claude Code](guides/google-cloud-from-claude/index.md). The guide you're reading is the *where* decision; that one covers the *how*.

**When Cloud Run Jobs are the right answer:**
- Overnight or weekend ingestion that must run whether your machine is on or not
- Any cadence between 1 minute and 1 hour (the gap claude.ai routines can't fill)
- Jobs that run custom code, not a Claude reasoning session
- Heavier compute — data processing, fetchers, indexers, anything with memory/CPU requirements

---

## Cross-cutting concern — gcloud credential expiry

This one deserves its own section because it affects surface 3 and catches people who have GCP running fine for a week and then suddenly broken.

If your Google Workspace org has a session-control policy configured, your gcloud credentials expire on a schedule the admin controls. The Workspace admin console allows session lengths from 1 hour to 24 hours; anything beyond that requires reauthentication. When the session expires, any code using Application Default Credentials returns a reauth-related error, and `gcloud` commands start failing until you run `gcloud auth login` again. ([Google Workspace session control docs](https://support.google.com/a/answer/9368756))

This is the "my gcloud keeps logging me out" problem. It's not a bug — it's a policy. Three paths forward:

1. **For manual setup and one-off deploys:** accept the friction. When it expires, `gcloud auth login` re-authenticates. It's one command.
2. **For durable unattended runs:** don't rely on your user credentials at all. Use a service account or Workload Identity Federation for the Cloud Run job itself. The job authenticates as a service account, not as you, and service accounts don't have session-length policies.
3. **For CI-driven deploys:** trigger deploys from GitHub Actions with a service account key or Workload Identity — your user session is not involved. The local gcloud expiry then only affects you when you're working manually.

The worst pattern: a Cloud Run job that authenticates as your user `gcloud` credentials, which then expire mid-week, and you discover the failure by noticing that nothing ran for three days. Use service accounts for anything that runs unattended.

---

## The failure mode this guide is named after

The default is to run an automation wherever you built it. You build locally because that's where you iterate; the job works; you ship it. Three days later someone asks why the overnight data pull didn't run. Your Mac was closed.

This isn't a mistake with an obvious error message. The job doesn't log a failure — it just doesn't run. You have to look at the last successful run timestamp and notice the gap.

The fix is deciding *before* you build what cadence and uptime the job requires, then choosing the surface that matches those requirements from the start. A three-minute decision up front prevents a three-hour debugging session later.

---

## Decision summary

Pick local if: sub-hour cadence, active development, or the job needs something only reachable on your machine.

Pick claude.ai routines if: hourly-or-slower, you want zero infrastructure, and auth is handled by MCP connectors.

Pick Cloud Run Jobs if: overnight uptime required, any cadence between 1 minute and 1 hour, or the job is custom code that needs to run unattended indefinitely.

Pick both 2 and 3 together if: you want the agentic reasoning of a claude.ai session AND always-on uptime. Route the trigger from Cloud Scheduler to the claude.ai Routine API endpoint (`POST /fire`) rather than scheduling the routine directly — you get the cloud uptime with the agentic session.

---

## Sources & Attribution

All technical claims in this guide are sourced from primary documentation or verified from field experience as noted.

**Anthropic / claude.ai Routines:**
- [Automate work with routines — Claude Code Docs](https://code.claude.com/docs/en/routines) — 1-hour floor, branch behavior, connector model, environment constraints. Verified 2026-06-14.

**Apple / macOS scheduling:**
- [Scheduling Timed Jobs — Apple Developer Library](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/ScheduledJobs.html) — launchd `StartCalendarInterval` catch-up-on-wake behavior vs. cron sleep behavior. Verified 2026-06-14.

**Google Cloud Run Jobs:**
- [Create jobs — Cloud Run — Google Cloud Documentation](https://cloud.google.com/run/docs/create-jobs) — Jobs vs. Services distinction, run-to-completion model. Verified 2026-06-14.
- [Cloud Run pricing — Google Cloud](https://cloud.google.com/run/pricing) — 180,000 vCPU-seconds free tier per month. Verified 2026-06-14.

**Google Cloud Scheduler:**
- [Manage cron jobs — Cloud Scheduler — Google Cloud Documentation](https://cloud.google.com/scheduler/docs/creating) — 5-field cron support, 1-minute minimum interval. Verified 2026-06-14.

**Google Workspace session control:**
- [Set session length for Google Cloud services — Google Workspace Help](https://support.google.com/a/answer/9368756) — session length range (1–24 hours), impact on gcloud credentials. Verified 2026-06-14.

**Google Secret Manager:**
- [Secret Manager documentation — Google Cloud](https://cloud.google.com/secret-manager) — credentials model for Cloud Run jobs.

**Companion reading:**
- [Calling Google Cloud Services from Claude Code](guides/google-cloud-from-claude/index.md) — setup mechanics for Cloud Run, Cloud Scheduler, Secret Manager, and the local-vs.-cloud architecture decision. The guide you're reading is the *where* decision; the companion covers the *how*.

**Field experience (not externally citable):**
- The gcloud session-expiry failure mode, its discovery pattern (silent gap in run timestamps), and the service-account remedy come from operating a real system through this failure.
- The claim that the most common mistake is keeping automations local because that's where you built them comes from observation, not a study.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
