---
name: google-cloud-from-claude
description: >
  Help a developer or operator choose the right Google Cloud access path from
  Claude Code — Gemini API (AI Studio key vs. Vertex AI), image generation
  (Imagen 4 / Nano Banana), or Google Maps Platform — diagnose auth and billing
  failures, audit credential hygiene, and walk through setup from scratch.
  Trigger when the user says "which door should I use for this Google API call",
  "help me set up Gemini access on Vertex", "audit my Google Cloud credential
  setup", "why is my Gemini API key returning 429", "set up image generation
  with Google", "call Google Maps from my agent", or "my gcloud auth isn't
  working".
---

# google-cloud-from-claude skill

**Trigger phrases (say any of these to Claude):**
- "which door should I use for this Google API call"
- "help me set up Gemini access on Vertex"
- "audit my Google Cloud credential setup"
- "why is my Gemini API key returning 429"
- "set up image generation with Google"
- "call Google Maps from my agent"
- "my gcloud auth isn't working"
- "does my Workspace Gemini plan give me API access"
- "Gemini API vs Workspace Gemini, what's the difference"
- "set up Imagen 4 from the terminal"
- "geocoding from Claude Code"
- "static maps API from a script"
- "Vertex AI setup from scratch"

---

## What this skill does

When triggered, Claude applies the three-doors framework from Rick Watson's
[*Calling Google Cloud Services from Claude Code*](https://github.com/watsonrm/rmwcommerce/blob/main/guides/google-cloud-from-claude/index.md)
guide to the user's situation and produces:

1. A door assignment: which of the three paths (MCP / Gemini API / Maps) fits the stated need
2. Auth diagnosis for the chosen door (AI Studio key vs. Vertex, gcloud ADC vs. service account)
3. A billing + API-enable checklist with the exact `gcloud services enable` commands needed
4. Credential hygiene audit: are keys in the Keychain, are they restricted, is anything hardcoded
5. A working code snippet (curl or Python) for the specific call described
6. A check-your-work step to verify the setup actually works before writing more code

---

## Session protocol

### Step 0 — Classify the need

Ask the user what they are trying to do. Three paths diverge immediately:

- **Read or write Gmail / Docs / Drive / Calendar / Sheets / Slides** → Door 1 (MCP server). This skill does not cover MCP setup; point them to [Operating Google Workspace from Claude](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-workspace-from-claude.md) and stop.
- **Call a language model (text, vision, chat, classification) or generate an image** → Door 2 (Gemini API). Continue to Step 1.
- **Geocoding, static maps, places, routes** → Door 3 (Maps Platform). Jump to Step 4.
- **Cloud infrastructure (Cloud Run, Cloud Scheduler, Secret Manager, Storage)** → infrastructure layer. Continue to Step 1 for auth context, then Step 5.

### Step 1 — Clarify the Gemini path (Door 2 only)

Ask:
- Do you already have a Google Cloud project with billing enabled?
- Are you putting real client or business data through this call, or is it a prototype?
- Do you have `gcloud` installed and authenticated locally?

**Decision:**
- Prototype + no GCP project: AI Studio key (fast path, 2-minute setup). Warn about free-tier training on inputs.
- Real data OR existing GCP project: Vertex AI (preferred path). Billing through GCP, no training data use.
- Has a key already minted: check whether it is a Developer API key (AI Studio billing) or a Vertex IAM path. A 429 "prepayment credits depleted" on a key from a billing-enabled project is the Developer API's separate prepaid billing being zero — not a GCP billing issue. Vertex does not have this problem.

### Step 2 — Walk through Vertex setup (if chosen)

Run through this checklist:

**Enable the API:**
```bash
gcloud services enable aiplatform.googleapis.com --project "$PROJECT"
```

**Get a bearer token (no key needed):**
```bash
TOKEN=$(gcloud auth print-access-token)
```

**Make the call:**
```bash
PROJECT=your-project
LOC=us-central1
curl -s "https://${LOC}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOC}/publishers/google/models/gemini-2.5-flash:generateContent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"contents":[{"role":"user","parts":[{"text":"Hello, Vertex."}]}]}'
```

**Check-your-work:** response should carry `candidates[0].content.parts[0].text`. A `403` means the API is not yet enabled on the project. A `401` means the token is stale — re-run `gcloud auth print-access-token`.

**For scripts that run unattended:** use a service account with the `roles/aiplatform.user` IAM role, store the JSON key in Secret Manager, and load it via the `GOOGLE_APPLICATION_CREDENTIALS` env var. Do not store the key file in the repo or the script.

### Step 3 — Image generation (Imagen 4 or Nano Banana)

Ask whether the user wants:
- **Imagen 4** (`imagen-4.0-fast-generate-001`): `:predict` endpoint, PNG returned as base64
- **Gemini native models** ("Nano Banana" — e.g., `gemini-2.5-flash-image`): `generateContent` endpoint, same auth as text calls, stronger at conversational editing and text-in-image

**Imagen 4 call pattern:**
```bash
curl -s "https://${LOC}-aiplatform.googleapis.com/v1/projects/${PROJECT}/locations/${LOC}/publishers/google/models/imagen-4.0-fast-generate-001:predict" \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"instances":[{"prompt":"..."}],"parameters":{"sampleCount":1}}' \
  -o out.json

python3 -c "import json,base64; d=json.load(open('out.json')); open('img.png','wb').write(base64.b64decode(d['predictions'][0]['bytesBase64Encoded']))"
```

Note on usage rights: every Google-generated image carries a SynthID watermark marking it AI-generated. SynthID does not restrict commercial use.

**Check current model IDs** (they change frequently):
```bash
curl -s "https://generativelanguage.googleapis.com/v1beta/models" \
  -H "x-goog-api-key: $GEMINI_API_KEY" | python3 -m json.tool | grep '"name"'
```

### Step 4 — Maps Platform (Door 3)

**Enable and mint a restricted key:**
```bash
gcloud services enable \
  geocoding-backend.googleapis.com \
  static-maps-backend.googleapis.com \
  places-backend.googleapis.com \
  --project "$PROJECT"

gcloud services api-keys create \
  --display-name="claude-code-maps" \
  --api-target=service=geocoding-backend.googleapis.com \
  --api-target=service=static-maps-backend.googleapis.com \
  --project "$PROJECT"
```

**Store the key in the Keychain:**
```bash
security add-generic-password -U -s gmaps-api-key -a "$USER" -w 'AIza...'
export GMAPS_API_KEY="$(security find-generic-password -s gmaps-api-key -w)"
```

**Geocoding call:**
```bash
curl -s "https://maps.googleapis.com/maps/api/geocode/json?address=350+5th+Ave,New+York,NY&key=$GMAPS_API_KEY"
```

**Static map call:**
```bash
curl -s -o map.png "https://maps.googleapis.com/maps/api/staticmap?center=40.7484,-73.9857&zoom=14&size=600x400&markers=color:red%7C40.7484,-73.9857&key=$GMAPS_API_KEY"
```

**Cost context:** the flat $200/month credit ended March 2025. Current model: per-service monthly free caps (~10,000 calls/month for Geocoding and Static Maps on the Essentials tier). Geocoding ~$5/1k beyond the cap; static maps ~$2/1k. Enable billing on the project before production use.

**Check-your-work:** geocoding response should include `status: "OK"` and a `geometry.location` object. A `REQUEST_DENIED` means billing is not enabled or the specific API is not turned on for the project.

### Step 5 — Credential hygiene audit

Run this for any setup where the user has keys. PASS / GAP per item:

- **No key in a script or .env file** — keys must come from the Keychain (local) or Secret Manager (cloud)
- **No key in a prompt or CLAUDE.md** — prompts persist in conversation history and logs
- **Key restricted by API** — a key with no API restrictions is a liability; restrict to the specific services it needs
- **One key per purpose** — don't share a Maps key with a Gemini key
- **Keychain write confirmed** — verify with `security find-generic-password -s <name> -w` before assuming it stored
- **Token freshness in scripts** — `gcloud auth print-access-token` tokens expire in ~1 hour; for unattended scripts, use a service account

If a key was ever hardcoded and committed, even briefly: rotate it immediately. Git history is permanent.

### Step 6 — Deliver the setup summary

Format:

```
## Google Cloud Setup — <user's stated goal>

### Door assignment
- [Door 1 / 2 / 3 — one line on why]

### Auth path chosen
- [AI Studio key / Vertex IAM / Maps API key — and why]

### Checklist
- [ ] GCP project exists with billing enabled
- [ ] APIs enabled (list the gcloud commands)
- [ ] Key/credential stored in Keychain or Secret Manager
- [ ] Key restricted by API and application
- [ ] No key in any script, prompt, or repo

### Working code snippet
[exact curl or Python for the user's specific call]

### Check-your-work
[exact command + expected response to confirm the setup works]

### Common failure modes for this path
[list the 1–2 most likely errors and their fixes]
```

---

## Common failure modes and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `429 RESOURCE_EXHAUSTED — prepayment credits depleted` | Developer API key with zero AI Studio balance | Switch to Vertex AI path; or add credits in AI Studio billing |
| `403 Request had insufficient authentication scopes` | Using a key where ADC/token is needed, or vice versa | Vertex: use `gcloud auth print-access-token`; AI Studio: use `x-goog-api-key` header |
| `403 API not enabled` | API not turned on for the project | `gcloud services enable <api>.googleapis.com --project $PROJECT` |
| `REQUEST_DENIED` on Maps | Billing not enabled, or API not enabled for the key's project | Enable billing + `gcloud services enable geocoding-backend.googleapis.com` |
| `401 UNAUTHENTICATED` | Bearer token expired | Re-run `gcloud auth print-access-token` |
| Maps key works in curl, fails in script | Key not in Keychain, or env var not exported | `export GMAPS_API_KEY=...` or read from Keychain in the script |

---

## What this skill does NOT do

- MCP server setup for Google Workspace (Docs / Drive / Gmail / Sheets / Calendar) — that is the [operating-google-workspace-from-claude](../operating-google-workspace-from-claude/SKILL.md) skill
- Direct API calls on the user's behalf — diagnoses and provides code; the user runs it
- Keep model IDs or prices current — always verify against the linked Google docs pages

---

## Voice

Direct. Verdict-first. Name the specific error code or symptom the user has hit before explaining why. If they have a Developer API key with a 429, say "this is a separate billing account in AI Studio, not a GCP billing issue" — don't make them read four pages to discover that. For Workspace Gemini confusion, lead with the one-sentence distinction: "the app and the API are different products; your Workspace plan doesn't unlock the API."
