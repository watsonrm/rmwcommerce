# operating-google-docs-from-claude skill

**Trigger phrases (say any of these to Claude):**
- "audit my google docs automation"
- "audit my drive automation setup"
- "operating google docs checklist"
- "is my doc-writing setup safe"
- "why is my drive skill failing on shared drives"
- "my agent broke a google doc, what now"

---

## What this skill does

When triggered, Claude works through the 9-item priority checklist from Rick Watson's [*Operating Google Drive and Google Docs from Claude*](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-docs-from-claude.md) guide, asks targeted questions about the user's setup, and produces:

1. A pattern-by-pattern gap report (Patterns 1–5 first — these are the 80/20)
2. A connector-parity diagnosis if the user has hit the "works in prompt, fails in skill" failure mode
3. A non-native file readiness check (does the automation handle `.docx` / PDF / images?)
4. Specific, prioritized fixes with effort estimates and a one-line workaround per gap
5. A check-your-work section: post-fix tests to verify each fix landed

---

## Session protocol

### Step 1 — Gather the setup

Ask the user for:
- What does the automation do? (read a doc / write a doc / both / file management)
- What MCP server(s) does it use? (local Google Workspace MCP, claude.ai connector, custom Drive REST helper, mix)
- Where does it run? (local Claude Code on a developer machine, claude.ai conversation, scheduled cloud job, all three)
- Does it touch Shared Drives or My Drive only?
- Does it read non-native files (`.docx`, `.xlsx`, `.pptx`, `.pdf`, images), or only native Google Docs?
- Does it write at all, or is it read-only?
- Is there an existing failure mode that prompted this audit? Get the symptom in one sentence.

If the user reports "works in prompt, fails in skill," **jump immediately to Step 2 (connector parity diagnosis)** before any other gap check. That failure mode is its own diagnostic path and the rest of the checklist will mislead the user otherwise.

### Step 2 — Connector parity diagnosis (only if the symptom matches)

Symptom signatures:
- `drive_list_files(folderId=<shared_drive_id>)` returns `{ files: [] }` when a Shared Drive contains files
- `drive_get_file(fileId=<shared_drive_id>)` returns `MESSAGE_NOT_FOUND` or `NOT_FOUND`
- The same calls return correct results for My Drive content
- Direct-prompt invocations work; skill-context invocations don't

Diagnostic steps:
1. Confirm the user's connector identity. The local Google Workspace MCP (typically `mcp__google-docs__*`) and the claude.ai connector (typically `mcp__claude_ai_Google_Drive__*`) behave differently.
2. Have the user check the OAuth scope of the failing connector. If it's `drive.file` (instead of the broader `drive`), the connector **cannot** see Shared Drives — that's by spec, not a regression.
3. If the scope is correct (`drive`) and the failure is My-Drive-works / Shared-Drive-empty, the user is hitting [anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442) — a Cowork connector regression. Anthropic owns the fix; there is no workaround inside the skill code.
4. **The durable workaround:** local-first. Pull the file down via whatever read path does work, do agent work on the local copy, sync back to Drive in a separate write step. The local copy bypasses every connector-level access regression.

Surface a clear verdict in the gap report:
- "Connector regression — Anthropic owns the fix; while waiting, route through local-first workflow"
- "Scope mismatch — connector configured with `drive.file`; reconfigure with `drive` scope"
- "Skill-vs-prompt code-path divergence — your skill's tool invocation shape differs from the direct-prompt shape; show me both call shapes side-by-side"

### Step 3 — Patterns 1–5 gap check (the 80/20)

Work through each as a question. PASS / GAP / N/A per item.

**P1 — Edit existing docs in place, never recreate to "prepend"**
- "When your automation updates a tracked Google Doc, does it use `replaceDocumentWithMarkdown` (or `insertText` / `replaceRangeWithMarkdown`) on the existing doc id — or does it create a new doc and trash the old one?"
- The recreate path is the failure mode. If the user has duplicate files in any tracked folder (multiple files with the same name), this is likely the cause.

**P2 — Verify every style via JSON read, not tool success**
- "After any `applyTextStyle` or `applyParagraphStyle` call, does your code re-read the doc as JSON and confirm the values landed correctly?"
- Common silent failures to name explicitly: bold overwritten by font-only restyling, bullet textRuns left as `textStyle: {}`, `weightedFontFamily.weight: 400` when `bold: true` was requested. "Tool returned success" is not proof.

**P3 — Pre-resize images at the file level**
- "When you insert images, do you pre-resize the source file (with `sips` on macOS or equivalent) before calling `insertImage`?"
- Quick diagnostic: ask if the user has ever spent rounds tuning `width` / `height` parameters to `insertImage`. If yes, they're hitting the limit. The parameters don't reliably constrain rendered size.

**P4 — Cascade-check both directions after every paragraph-style write**
- "Does your code count `namedStyleType` distribution in the post-write JSON, in both directions? Excess H1 cascade (overflow) AND missing headings (strip)?"
- The two failure modes are opposite but stem from the same fragility. Catching one but not the other is partial defense.

**P5 — Brand styling sequence (the only 5-step order that works)**
- "After a `replaceDocumentWithMarkdown` write, does your code apply styles in this order: body sweep → cascade check → heading paragraph styles → heading text styles → inline bold prefixes for label-prefixed bullets?"
- Common deviations: skipping the body sweep (Arial body), skipping the cascade check (overflow), batching all paragraph styles before any text styles (interruption-prone), assuming bullets inherit parent-range styling (they don't).

### Step 4 — Patterns 6–9 (amplification)

Only deep-dive into these if Patterns 1–5 are PASS or explicitly deprioritized by the user.

**P6 — Treat all existing human content as load-bearing**
- "Before any `replaceRangeWithMarkdown` or `deleteRange`, does your code scan the JSON for `inlineObjectElement` / `richLink` / `personElement`?"
- The failure: range replace silently destroys pasted images, smart chips, manual edits.

**P7 — Idempotency: search-before-create, body-match-before-update, date-match-before-prepend**
- "If your automation runs twice on the same input, does it reach the same Drive state — no duplicate files, no duplicate sections?"

**P8 — State.json breadcrumbs for resume-from-interruption**
- "If your write process gets killed mid-cascade, can the next dispatch detect that and recover, or does it layer a fresh write on top of a half-styled doc?"
- High-effort item; only relevant for unattended orchestrators that touch the same doc repeatedly.

**P9 — Logging and post-write verification artifacts on disk**
- "When a doc renders wrong yesterday, can you read the pre-write and post-write JSON from disk to diagnose what changed?"

### Step 5 — Non-native file readiness check

Specifically for any automation that takes "a Drive file id" as input:

- "Does your code call `get_file_metadata` first and switch on `mimeType` before deciding how to read?"
- Native Google Docs → `readDocument`
- `.docx`, `.xlsx`, `.pptx` → `copyFile` with `mimeType` conversion, OR `download_file_content` for raw bytes
- PDFs and images → `download_file_content`, then route to a model with the right modality
- Unknown mime type → return a clear error, don't try to `readDocument`

Common failure: a user-facing skill takes a Drive URL as input. The user pastes a `.docx`. The skill calls `readDocument`, which errors. The skill reports "couldn't read the doc" with no useful detail. The user assumes it's a permissions problem.

### Step 6 — Hard-limit awareness

For each of these, ask if the user's setup has encountered them yet, and note the workaround:

- **PAGE_NUMBER / PAGE_COUNT auto-text in existing docs** — API cannot create these. Workaround: `copyFile` from a template that already has the footer.
- **MCP availability differs by environment** — Mac (local MCP) vs cloud (no MCP, needs stdlib helper or cloud-secret-proxy). Surface which environments the user runs in.
- **`insertImage` size parameters unreliable** — pre-resize the source file.
- **Named styles edited via UI only** — if the doc's `NORMAL_TEXT` named style drifted to Arial, no API call will fix it. Drive UI → Format → Paragraph styles → Normal text → "Update Normal text to match" is the only path.
- **Consecutive `**Label:**` rows collapse on markdown import** — source-side: blank line between every label row.

### Step 7 — Deliver the gap report

Format:

```
## Google Docs Automation Audit — <user's setup>

### Connector-parity (Step 2)
- [Verdict — if relevant; skip section if not applicable]

### Patterns 1–5 (the 80/20)
- [ ] P1 Edit-in-place: <PASS / GAP — one sentence + workaround>
- [ ] P2 JSON verification: <PASS / GAP>
- [ ] P3 Pre-resize images: <PASS / GAP>
- [ ] P4 Cascade-check both directions: <PASS / GAP>
- [ ] P5 Brand styling sequence: <PASS / GAP>

### Patterns 6–9 (amplification)
- [ ] P6 Human-content preservation
- [ ] P7 Idempotency
- [ ] P8 State.json breadcrumbs
- [ ] P9 Logging artifacts

### Non-native files
- [ ] mimeType check before reading: <PASS / GAP>

### Hard limits the user has hit
- [list]

### Recommended order of operations
1. [highest-impact gap with one-line fix]
2. [next]
3. [next]

### Check-your-work commands
- [exact commands or test cases the user can run to verify each fix]
```

### Step 8 — Where to read more

Always end with:
> Full guide: [Operating Google Drive and Google Docs from Claude](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-docs-from-claude.md)
> Bug tracker for Cowork Shared Drive issue: [anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442)

---

## What this skill does NOT do

- It does not have direct read/write access to the user's Drive or Docs. It diagnoses; the user executes.
- It does not fix the Cowork connector regression. That's Anthropic's bug to fix.
- It does not recommend specific brand styling (fonts, colors). Those are operator-specific choices outside the article's scope.
- It does not handle Sheets / Gmail / Calendar — only Drive + Docs. Those surfaces have their own gotchas worth a separate skill.

---

## Voice

Direct. Verdict-first. Specific. Cite the article's patterns by number (P1 / P5 / Limit 3 etc.) so the user can cross-reference. If the user has hit a connector regression, say so plainly — don't make them debug their own skill code for a bug Anthropic owns.
