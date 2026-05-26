# operating-google-docs-from-claude skill

**Trigger phrases (say any of these to Claude):**
- "audit my google docs automation"
- "audit my google sheets automation"
- "audit my google slides automation"
- "audit my drive automation setup"
- "operating google docs checklist"
- "is my doc / sheet / slide automation safe"
- "why is my drive skill failing on shared drives"
- "my agent broke a google doc / sheet / deck, what now"
- "USER_ENTERED vs RAW question"
- "my slide object ids stopped working"

---

## What this skill does

When triggered, Claude works through the audit checklist from Rick Watson's [*Operating Google Drive, Docs, Sheets, and Slides from Claude*](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-docs-from-claude.md) guide, asks targeted questions about the user's setup, and produces:

1. A surface-by-surface pattern adherence report (Docs / Sheets / Slides / Drive)
2. A connector-parity diagnosis if the user has hit the "works in prompt, fails in skill" failure mode
3. A non-native file readiness check for Drive-touching skills (does the automation handle `.docx` / PDF / images?)
4. Specific, prioritized fixes with effort estimates and a one-line workaround per gap
5. A check-your-work section: post-fix tests to verify each fix landed

---

## Session protocol

### Step 0 — Route by surface first

Ask the user what surface(s) the automation touches. Each has its own diagnostic flow:

- **Drive only** (search / list / move / copy / share, no content) → Step 1, then Step 2 (connector parity), then Step 6 (hard limits) for `.docx`/`.pdf` handling.
- **Docs** (read / write document body, styling, images) → Step 1, then Step 2 (if applicable), then **Step 3 (Docs patterns)**.
- **Sheets** (cells, ranges, formulas, formatting) → Step 1, then **Step 4 (Sheets patterns)**.
- **Slides** (presentations, slides, shapes, images) → Step 1, then **Step 5 (Slides patterns)** — and **always surface the MCP-coverage shallowness** up front (production MCP servers expose ~7 Slides tools; most deck automation needs raw `presentations.batchUpdate` payloads).

Mixed setups (e.g., an automation that writes a Doc and embeds Sheets data) run multiple flows.

### Step 1 — Gather the setup

Ask the user for:
- What does the automation do? (one sentence: the surface, the operation, the trigger)
- What MCP server does it use? (local Google Workspace MCP — typically `taylorwilsdon/google_workspace_mcp` — vs claude.ai connector, vs raw REST helper)
- Where does it run? (local Claude Code on a dev machine, claude.ai conversation, scheduled cloud job)
- Does it touch Shared Drives or My Drive only?
- Does it read non-native files (`.docx`, `.xlsx`, `.pptx`, `.pdf`, images)?
- Is there an existing failure mode that prompted this audit? Get the symptom in one sentence.

If the user reports "works in prompt, fails in skill," **jump immediately to Step 2 (connector parity)** before any other gap check. That failure mode is its own diagnostic path and the rest of the checklist will mislead them otherwise.

### Step 2 — Connector parity diagnosis (only if the symptom matches)

Symptom signatures:
- `drive_list_files(folderId=<shared_drive_id>)` returns `{ files: [] }` when a Shared Drive contains files
- `drive_get_file(fileId=<shared_drive_id>)` returns `MESSAGE_NOT_FOUND` or `NOT_FOUND`
- The same calls return correct results for My Drive content
- Direct-prompt invocations work; skill-context invocations don't

Diagnostic steps:
1. Confirm the user's connector. The local Google Workspace MCP (typically `mcp__google-docs__*`) and the claude.ai connector (typically `mcp__claude_ai_Google_Drive__*`) behave differently.
2. Check the OAuth scope of the failing connector. If it's `drive.file`, the connector is **per-file / picker-mediated** by spec — it cannot see Shared Drives unless the file was created or opened by the app. That's behavior, not a regression.
3. If the scope is correct (`drive`) and the failure is My-Drive-works / Shared-Drive-empty, the user is hitting [anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442) — a Cowork connector regression. Anthropic owns the fix; there is no workaround inside the skill code.
4. **The durable workaround:** local-first. Pull the file down via whatever read path does work, do agent work on the local copy, sync back to Drive in a separate write step.

Surface a clear verdict in the gap report:
- "Connector regression — Anthropic owns the fix; route through local-first workflow"
- "Scope mismatch — connector configured with `drive.file`; broaden to `drive` scope"
- "Skill-vs-prompt code-path divergence — your skill's tool invocation shape differs from direct-prompt; show me both call shapes side-by-side"

### Step 3 — Docs pattern gap check (D1–D9)

Work through each as a question. PASS / GAP / N/A per item. The order matches the article's `Where to spend your time — Docs` priority table.

**D1 — Verify every style via JSON read, not tool success** (highest leverage)
- "After any `applyTextStyle` or `applyParagraphStyle` call, does your code re-read the doc as JSON and confirm the values landed correctly?"
- Common silent failures: bold overwritten by font-only restyling, bullet textRuns left as `textStyle: {}`, `weightedFontFamily.weight: 400` even when `bold: true` was requested. "Tool returned success" is not proof. The fix: pass `weightedFontFamily: {fontFamily: X, weight: 700}` AND `bold: true` together with both fields in the mask.

**D2 — Brand styling sequence (the only 5-step order that works)**
- "After a body write, does your code apply styles in this order: body sweep → cascade check → heading paragraph styles → heading text styles → inline bold prefixes for label-prefixed bullets?"
- Common deviations: skipping the body sweep (Arial body), skipping the cascade check (overflow), batching all paragraph styles before any text styles (interruption-prone), assuming bullets inherit parent-range styling (they don't).

**D3 — Cascade-check both directions after every paragraph-style write**
- "Does your code count `namedStyleType` distribution in the post-write JSON, in BOTH directions? Excess H1 cascade (overflow) AND missing headings (strip)?"
- The two failure modes are opposite but stem from the same fragility. Catching one but not the other is partial defense.

**D4 — Pre-resize images at the file level**
- "When you insert images, do you pre-resize the source file (with `sips` on macOS or equivalent) before calling `insertImage`?"
- Three discipline checks: (a) does the user maintain a `.assets/` cache of canonical pre-sized variants? (b) is there a denylist of ad-hoc source paths (`~/Downloads/`, ad-hoc dirs)? (c) does the skill verify image URL `Content-Type` is `image/*` before handoff (broken CDN URLs and login-walled images return 200 with HTML, producing silent broken-image placeholders)?

**D5 — Copy from template for any doc that needs a page-number footer**
- "For docs with page numbers, does your create flow use `copyFile` from a template that already has the footer baked in, or does it `createDocument` (which produces a footerless doc)?"
- The Docs API cannot create `PAGE_NUMBER` / `PAGE_COUNT` auto-text in existing docs (long-standing limitation).

**D6 — Edit existing docs in place, never recreate to "prepend"**
- "When your automation updates a tracked Google Doc, does it use `replaceDocumentWithMarkdown` on a stable `doc_id`, or does it create a new doc and trash the old one?"
- If the user has duplicate files in any tracked folder (multiple files with the same name), this is likely the cause.

**D7 — Treat all existing human content as load-bearing**
- "Before any `replaceRangeWithMarkdown` or `deleteRange`, does your code scan the JSON for `inlineObjectElement` / `richLink` / `person`?"
- Failure: range replace silently destroys pasted images, smart chips, manual edits.

**D8 — Idempotency: search-before-create, body-match-before-update, date-match-before-prepend**
- "If your automation runs twice on the same input, does it reach the same Drive state — no duplicate files, no duplicate sections?"

**D9 — State.json breadcrumbs for resume-from-interruption**
- "If your write process gets killed mid-cascade, can the next dispatch detect that and recover, or does it layer a fresh write on top of a half-styled doc?"
- High-effort item; relevant for unattended orchestrators that touch the same doc repeatedly.

### Step 3b — Docs production-pattern checks (new since the original guide)

These came from auditing real production codebases. Each is its own PASS/GAP question.

**Three-write-path awareness**
- "If MCP isn't available in your environment, does the automation know about the Drive HTML-import fallback?" The three paths: MCP `replaceDocumentWithMarkdown`, raw Docs API `batchUpdate`, Drive HTML-import (multipart upload with `mimeType=application/vnd.google-apps.document`). HTML-import is the canonical "no MCP available" path; Drive strips inline CSS so a follow-up styling pass is mandatory.

**Tab-enabled docs**
- "Does the doc have document tabs (the `tabs` field in the JSON)?" If yes, the legacy table tools (`listDocumentTables`, `updateTableBorders`, `updateTableCellStyle`, `updateTableColumnWidth`) fail with a field-mask error. Workaround: edit table structure in the Drive UI, or `.docx` export-edit-reimport.

**Validators don't write**
- "Does the user's validator agent have write tools (`insertText`, `applyTextStyle`, `replaceRangeWithMarkdown`) AND fix-in-run behavior?" That's a second writer, contradicting the single-writer pattern. Validators should emit typed outcomes and dispatch the writer; they should not also have write tools.

**Surface ownership**
- "Does each skill explicitly name which Drive surfaces it owns vs doesn't?" Mixed surfaces (human curates, agent prepends a section, separate process synthesizes) are the failure mode. Naming surface ownership in the skill preamble prevents reflexive "summarize the call into the same doc I prepended" loss.

**Concurrency cap on writer fan-out**
- "When the orchestrator dispatches N parallel jobs that each spawn the writer, does it cap N to stay under the MCP server's tolerance (typically 4–6 concurrent writes)?"

**Cloud / interactive parity flags**
- "When the cloud helper writes an unstyled body, does the typed return distinguish that outcome (`*_pending_interactive` with a `pending[]` list) from a fully-styled interactive write?" The flag lets the next interactive run only do the missing work.

### Step 4 — Sheets pattern gap check (S1–S5)

Run only if the user touches Sheets. Per the article's `Sheets — where to spend your time` table.

**S1 — `valueInputOption=USER_ENTERED` for almost every write**
- "When your automation writes cell values, does it pass `valueInputOption=USER_ENTERED` explicitly?" The most common Sheets API mistake: writing `=SUM(A1:A10)` with `RAW` lands the literal string starting with `=` in the cell. USER_ENTERED parses input the way the UI does.

**S2 — Set the `fields` mask on every `UpdateCellsRequest`**
- "When updating cell properties via `spreadsheets.batchUpdate`, does the code set the narrowest possible `fields` mask?" Omitting or passing `"*"` silently wipes cell properties you didn't intend to touch.

**S3 — Collapse N writes into one `batchUpdate`**
- "When writing multiple cells / ranges, does the code build one `values.batchUpdate` (content) or `spreadsheets.batchUpdate` (structure) call, or does it loop single calls?" Per-user quota is 60 req/min; the per-project quota is 300 req/min. A loop of `values.update` burns 60 units for what one batch costs.

**S4 — Pin `valueRenderOption=UNFORMATTED_VALUE` for any compute path**
- "When reading values for computation, does the code pin `valueRenderOption=UNFORMATTED_VALUE`?" Default `FORMATTED_VALUE` returns locale-rendered strings. Read-math-write-back round-trips can silently mangle commas, decimals, dates.

**S5 — Developer metadata to anchor sheet position**
- "Does the automation use hardcoded `Sheet1!A1:Z1000` ranges, or developer metadata for stable anchors?" Hardcoded ranges break the moment a tab is renamed or rows extend past row 1000. [Developer metadata](https://developers.google.com/sheets/api/guides/metadata) tags survive renames and reorders.

### Step 4b — Sheets hard-limit awareness

Note these in the gap report if the user has hit them:
- **No `CellImage` (blob) inserts via the API** — Apps Script `SpreadsheetApp.newCellImage()` only; or `IMAGE()` formula with public URL
- **No partial pivot table edits** — must rewrite the entire `pivotTable` field via `UpdateCellsRequest`
- **No full chart styling** — API supports limited chart settings; Apps Script for advanced
- **No revision-locked concurrency** — no If-Match / ETag; serialize dependent writes in one `batchUpdate`
- **10 million cell ceiling** (20M in the 2026 beta) per spreadsheet
- **No triggers, custom menus, or sidebars** — Apps Script only

### Step 5 — Slides pattern gap check (L1–L5)

Run only if the user touches Slides. **Always lead with the MCP-coverage gap** — most production MCP servers expose ~7 Slides tools versus ~14 Docs / ~13 Sheets, so the user is probably authoring raw `presentations.batchUpdate` payloads. Confirm that assumption first.

**L1 — Pre-assign your own `objectId` at create time, persist content/alt-text as the lookup key**
- "Does the automation rely on object IDs that have round-tripped through the Slides editor?" Per Google's docs: "you cannot depend on an object ID being unchanged after a presentation is changed in the Slides UI." If the user persists IDs and humans edit the deck, the lookups break. Fix: persist text content or alt-text, re-resolve to current object ID on each batch.

**L2 — Always pair `InsertText` with a preceding `DeleteText` against placeholder shapes**
- "When inserting text into a placeholder shape, does the code first `DeleteText` the placeholder prompt?" Layout-inherited placeholders ship with prompt text ("Click to add title"). InsertText at index 0 prepends, leaving `Click to add titleYour Real Content` in the slide.

**L3 — Bundle every related mutation into one `batchUpdate` (atomic)**
- "Does the automation make one `batchUpdate` call per mutation, or does it bundle 50–200 requests in one atomic call?" Write quota is 600/min/project, 60/min/user. Batching is the documented norm.

**L4 — Always set `fields` mask on `Update*Request`**
- Same rule as Sheets and Docs. Omitting the mask resets every property in the message to its default.

**L5 — For template-driven decks, copy via Drive `files.copy` then mutate the copy**
- "Does the automation operate on the template directly, or copy first then mutate the copy?" Google's explicit instruction: never mutate the primary template. `files.copy` first.

### Step 5b — Slides hard-limit awareness

Surface these in the gap report:
- **Slide transitions, element animations** — None via API. Apply in editor; survives `DuplicateObject`. [Open issue since 2016](https://issuetracker.google.com/issues/36761236).
- **Notes formatting beyond plain text** — Notes shape accepts text body only.
- **Private Drive image insertion** — Slides cannot fetch private Drive content. Workaround: make file public for ~30s, mint a GCS signed URL, or upload-then-share via Drive API.
- **Auto-refresh linked Sheets chart** — Manual `RefreshSheetsChartRequest` per chart.
- **ReplaceAllText reformatting** — Inherits formatting from the first character of the matched range; follow with `UpdateTextStyleRequest`.
- **Listing presentations** — Slides API has no `list`; use Drive `files.list` with `mimeType = "application/vnd.google-apps.presentation"`.

### Step 6 — Non-native file readiness check

For any Drive-touching automation that takes "a file id" as input:

- "Does your code call `get_file_metadata` first and switch on `mimeType` before deciding how to read?"
- Native Google Docs → `readDocument`
- `.docx` → `files.create` with `mimeType: "application/vnd.google-apps.document"` to convert, OR `download_file_content` for raw bytes
- `.xlsx`, `.pptx` → same conversion path with `.spreadsheet` / `.presentation` mimeType targets
- PDFs and images → `download_file_content`, then route to a model with the right modality
- Unknown mime type → return a clear error, don't try to `readDocument`

Common failure: a user-facing skill takes a Drive URL as input. The user pastes a `.docx`. The skill calls `readDocument`, which errors. The skill reports "couldn't read the doc" with no useful detail. The user assumes it's a permissions problem.

### Step 7 — Deliver the gap report

Format:

```
## Workspace Automation Audit — <user's setup>

### Surfaces in scope
- [Docs / Sheets / Slides / Drive — which apply]

### Connector-parity (Step 2)
- [Verdict if relevant; skip section if not applicable]

### Docs patterns (D1–D9 + production checks)
- [ ] D1 JSON verification
- [ ] D2 Brand styling sequence
- [ ] D3 Cascade-check both directions
- [ ] D4 Pre-resize images
- [ ] D5 Copy template for footers
- [ ] D6 Edit in place
- [ ] D7 Human content preservation
- [ ] D8 Idempotency
- [ ] D9 State.json breadcrumbs
- [ ] Three-write-path awareness
- [ ] Tab-enabled-docs handling
- [ ] Validators don't write
- [ ] Surface ownership named
- [ ] Concurrency cap on fan-out
- [ ] Cloud / interactive parity flags

### Sheets patterns (S1–S5, if applicable)
- [ ] S1 USER_ENTERED
- [ ] S2 fields mask
- [ ] S3 batch collapse
- [ ] S4 UNFORMATTED_VALUE for compute
- [ ] S5 Developer metadata anchors

### Slides patterns (L1–L5, if applicable)
- [ ] MCP-coverage gap acknowledged
- [ ] L1 objectId stability
- [ ] L2 InsertText / DeleteText pairing
- [ ] L3 batchUpdate batching
- [ ] L4 fields mask on Update*
- [ ] L5 Template-copy workflow

### Non-native files
- [ ] mimeType check before reading

### Hard limits the user has hit
- [list with workaround per row]

### Recommended fix order
1. [highest-impact gap with one-line fix]
2. [next]
3. [next]

### Check-your-work commands
- [exact commands or test cases the user can run to verify each fix]
```

### Step 8 — Where to read more

Always end with:
> Full guide: [Operating Google Drive, Docs, Sheets, and Slides from Claude](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-docs-from-claude.md)
> Bug tracker for Cowork Shared Drive issue: [anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442)
> Slides API transitions / animations issue: [issuetracker.google.com/issues/36761236](https://issuetracker.google.com/issues/36761236)

---

## What this skill does NOT do

- Direct read/write access to the user's Workspace. It diagnoses; the user executes.
- Fix the Cowork connector regression — that's Anthropic's bug.
- Recommend specific brand styling (fonts, colors). Operator-specific choices outside the article's scope.
- Handle Gmail / Calendar specifically. Those have their own gotchas worth a separate skill.

---

## Voice

Direct. Verdict-first. Specific. Cite the article's patterns by ID (D1 / D5 / S3 / L2 / Limit 3 etc.) so the user can cross-reference. If the user has hit a connector regression, say so plainly — don't make them debug their own skill code for a bug Anthropic owns. If the user is building Slides automation, lead with the MCP-coverage shallowness so they understand why their tool surface feels thinner than the Docs path.
