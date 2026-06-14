---
name: where-to-run-claude-automation
description: Decision framework for choosing between local launchd, claude.ai Routines, and GCP Cloud Run Jobs for a Claude automation. Applies the five-question decision tree, flags the key gotchas (1-hour floor, sleep behavior, branch permissions, gcloud reauth), and recommends a surface with reasoning.
when_to_use: >
  Load this skill when the user describes a Claude automation and asks where to run it,
  which scheduling surface to use, why a job didn't run overnight, or how to move an
  automation from local to cloud. Trigger phrases: "which surface should I run this automation on",
  "help me pick between local launchd and cloud routines", "audit my automation runtime choice",
  "why did my launchd job not run overnight", "should I use claude.ai routines or Cloud Run".
---

# Skill: where-to-run-claude-automation

## Purpose

Apply the three-surface decision framework to a described automation and recommend the right runtime, with specific reasoning tied to the automation's requirements.

## Decision framework

### Five questions (in order)

**Q1. Does it need to run when the machine is off (overnight / weekends)?**
- Yes → local is out. Go to Q2.
- No → local is viable. Evaluate Q2 for cadence.

**Q2. Does it need sub-hour cadence?**
- Yes → claude.ai routines are out (1-hour floor, documented). Use local launchd or Cloud Scheduler (1-minute minimum).
- No → claude.ai routines remain viable.

**Q3. Does it need to commit code that lands on a protected branch (main)?**
- Yes → a cloud claude.ai session alone won't do it by default. Options: enable unrestricted branch pushes in the routine config, design a human-merge step for the `claude/` branch, or use a Cloud Run job with a service account that has write permission.
- No → all cloud surfaces remain viable.

**Q4. Does it need local resources — Keychain, local files, local database, chat.db, local model index?**
- Yes → it must run locally (at least in part). If it also needs overnight uptime, these are in tension — the resolution is usually to separate the local-resource step from the cloud-scheduled step.
- No → all cloud surfaces remain viable.

**Q5. Does it need to run custom code (not a Claude reasoning session)?**
- Yes → Cloud Run Jobs, not claude.ai routines. Routines run Claude Code sessions; Cloud Run runs your container.
- No → claude.ai routines remain the lower-complexity option.

### Surface selection matrix

| Requirement | Local launchd | claude.ai Routines | Cloud Run Jobs |
|---|---|---|---|
| Sub-hour cadence | Yes | No (1h floor) | Yes (1-min min) |
| Overnight uptime | No | Yes | Yes |
| Local resource access | Yes | No | No |
| Zero-infra setup | Yes | Yes | No |
| Custom code execution | Yes | No | Yes |
| Auth via MCP connectors | No | Yes | No (use SA) |

---

## Per-surface gotcha checklist

Run through these for whatever surface you're recommending.

### Local (launchd)
- [ ] Using `StartCalendarInterval` (not cron) if missed-run catch-up is needed
- [ ] Mac is not off overnight — only sleeping is handled by launchd's catch-up behavior
- [ ] Not relying on this for anything that truly must run unattended 24/7

### claude.ai Routines
- [ ] Cadence is hourly or slower (1-hour floor enforced by the platform)
- [ ] Branch behavior understood — by default pushes to `claude/`-prefixed branches, not main
- [ ] All needed resources are accessible via connector tools (no local-only resources)
- [ ] Secrets are in environment variables in the routine config, not hardcoded in the prompt

### Cloud Run Jobs
- [ ] State managed externally (Cloud Storage / Firestore / Cloud SQL) — containers are ephemeral
- [ ] Credentials in Secret Manager, not in the container image or a prompt
- [ ] Auth uses a service account, not user credentials (avoids Workspace session-control expiry)
- [ ] gcloud deploy path does not depend on user credentials that expire under session-control policy

---

## gcloud reauth catch

If the user mentions that their gcloud commands are failing or that deployments stopped working unexpectedly: this is almost certainly the Workspace session-control policy expiring their credentials. The fix is surface-specific:

- For manual setup: `gcloud auth login` to re-authenticate.
- For unattended runs: switch the Cloud Run job to service-account auth. User sessions expire; service accounts do not have session-length policies.
- For CI-driven deploys: use a service account key or Workload Identity in GitHub Actions.

---

## Output format

After applying the framework, report:

1. **Recommended surface** — one of: Local, claude.ai Routines, Cloud Run Jobs, or a combination.
2. **Reasoning** — which questions drove the decision and why.
3. **Gotchas to address** — the checklist items that apply to the recommended surface.
4. **If changing surfaces** — what the migration requires (auth model, state externalization, containerization, etc.).

Keep it concrete. If the user gave enough information about their automation, make a definite recommendation rather than listing options.

---

## Reference

Full framework, decision table, and cited sources: [Where to Run Your Claude Automation](https://github.com/watsonrm/rmwcommerce/blob/main/guides/where-to-run-claude-automation.md)
