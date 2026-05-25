---
title: Operating Google Drive and Google Docs from Claude
description: The patterns, hard limits, and anti-patterns of writing to Google Drive and Google Docs from Claude or any AI agent. Five workarounds for things the API simply cannot do. Every claim grounded in a specific failure mode.
date: 2026-05-25
last_modified_at: 2026-05-25
author: Rick Watson
agent_friendly: true
keywords: Google Drive, Google Docs, MCP, model context protocol, AI agents, Claude, automation, document automation, OAuth, Drive API, Docs API
---

# Operating Google Drive and Google Docs from Claude

**The patterns, hard limits, and anti-patterns of writing to Google Drive and Google Docs from Claude or any AI agent. Five workarounds for things the API simply cannot do. Every claim grounded in a specific failure mode.**

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from the public Google Workspace APIs and Anthropic's Model Context Protocol. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-25 · Roughly 30 min read*

Who this is for: developers and operators using Claude (or any AI agent) to read and write Google Drive files and Google Docs at scale. Anyone who has watched an agent overwrite styled formatting, create four files with the same title, or report "all styles applied successfully" while the document renders broken.

---

## TL;DR — what's in it for you

- The Google Docs MCP exposes ~80 tools; Drive exposes ~8. Most of the failure modes don't come from missing tools — they come from trusting tool success without verifying the document state.
- Five things the API genuinely cannot do, and a tested workaround for each.
- A single-writer agent pattern that survives mid-write interruptions, prevents duplicate files, and detects style regressions before they ship.
- The 5-step brand-styling sequence is the only order that works. Every other order leaves Arial body text or huge bold headings.

### Where to spend your time, in priority order

Highest-leverage moves first. The reader who only adopts items 1–5 closes the largest share of real-world failure modes.

| # | Pattern | Why it matters | Effort |
|---|---|---|---|
| 1 | **Edit existing docs in place — never recreate to "prepend"** | Recreating a doc with the same title to insert content at the top is how duplicates accumulate. Real incident: four files all named the same string in one folder, only one was the live source. | Low |
| 2 | **Verify every style via JSON read, not tool success** | `applyTextStyle` returns success while silently overwriting bold runs, leaving bullet items as `textStyle: {}`, or setting `weightedFontFamily.weight: 400` when `bold: true` was passed. The JSON is the only ground truth. | Low |
| 3 | **Pre-resize images at the file level (sips on macOS) before `insertImage`** | `insertImage`'s `width` / `height` parameters do not reliably constrain rendered size in Google Docs. The source file's pixel dimensions win. | Low |
| 4 | **Cascade-check both directions after every paragraph-style write** | Two opposite failure modes exist: HEADING_1 cascades across far more paragraphs than the markdown intended (huge bold Arial body), AND a mid-write interruption leaves every paragraph as NORMAL_TEXT (every heading rendered as body). Detect both before declaring success. | Medium |
| 5 | **Copy from template for any doc that needs a page-number footer** | The Docs API cannot create PAGE_NUMBER / PAGE_COUNT auto-text in an existing document — a long-standing limitation. The only path to a properly-footed doc is `copyFile` from a template that already carries the footer. | Medium |
| 6 | **Treat all existing human content as load-bearing** | Range replaces and `deleteRange` calls silently overwrite pasted images, smart chips, comments, and manual edits. Inspect the JSON for `inlineObjectElement`, `richLink`, `personElement` before any wholesale range operation. | Medium |
| 7 | **Brand styling sequence: body sweep → cascade check → heading paragraph styles → heading text styles → inline bold prefixes** | The only 5-step order that works. Every other order produces a visually broken doc that passes individual tool-call success checks. | Medium |
| 8 | **Idempotency: search-before-create, body-match-before-update, date-match-before-prepend** | Rerunning a write on the same input must reach the same Drive state. This is the rule that prevents duplicate-title accumulation when an orchestrator retries. | Low |
| 9 | **State.json breadcrumbs for resume-from-interruption** | A write killed mid-cascade strands the doc half-styled. State.json lets the next dispatch detect the interruption, run cascade-check first, and recover before compounding the damage. | High |

Most readers should adopt items 1–5 and stop. Items 6–9 are amplification, mostly relevant once you're running document writes from an unattended orchestrator.

---

## What's in this article

- [Part 1 — The toolset and the mental model](#part-1--the-toolset-and-the-mental-model) — including [connector parity gotchas](#connector-parity-is-not-guaranteed)
- [Part 2 — Patterns that work](#part-2--patterns-that-work)
- [Part 3 — Hard limits the API does not support](#part-3--hard-limits-the-api-does-not-support) — including [non-native files](#limit-5--non-native-files-need-download_file_content-not-readdocument)
- [Part 4 — Anti-patterns to recognize](#part-4--anti-patterns-to-recognize)
- [Part 5 — Architecture: the single-writer pattern](#part-5--architecture-the-single-writer-pattern)
- [Part 6 — How to measure whether your writes are healthy](#part-6--how-to-measure-whether-your-writes-are-healthy)
- [What we still don't know](#what-we-still-dont-know)

---

## Part 1 — The toolset and the mental model

### Three APIs, three mental models

| Surface | What it is | What it gives you |
|---|---|---|
| **Drive** | The filesystem | List, search, copy, move, delete, share. File-level metadata. No content editing. |
| **Docs** | The document editor | Read, write, structure, style, comments, suggestions. Content lives here. |
| **Sheets** | The spreadsheet editor | Cells, ranges, formulas, formatting, conditional formatting. Parallel surface to Docs. |

Most production failures come from confusing these. A `copyFile` operation is a Drive call. A `replaceDocumentWithMarkdown` is a Docs call. The Drive call on a Doc duplicates the file; the Docs call on the duplicate edits its body. Reading code that mixes these up tells you the author hasn't thought through whether they're operating on the file or the content.

### MCP tool families

In practice you'll work through the Model Context Protocol layer rather than the raw REST APIs. As of 2026 there are two production-grade MCP servers worth knowing:

- **The full Google Workspace MCP** (typically registered as `mcp__google-docs__*`) — covers ~80 operations across Documents, Sheets, Drive, Comments, Gmail, Calendar. This is the toolset for any non-trivial automation. Requires OAuth.
- **The claude.ai Google Drive connector** (`mcp__claude_ai_Google_Drive__*`) — ~8 tools covering search, read, copy, list-recent, file-metadata, permissions. This is the user-facing connector available in claude.ai conversations. Lighter; intended for interactive use.

Decision rule: prefer `mcp__google-docs__*` for any automation that writes. Reach for `mcp__claude_ai_Google_Drive__*` when you need to read arbitrary user-authenticated Drive content from inside a conversation and you don't have an OAuth-backed server registered.

### Connector parity is not guaranteed

The same MCP server name in different products can behave differently. As of mid-2026, three real divergences hit production:

- **Shared Drive access in claude.ai / Cowork.** The Google Drive connector has had documented regressions where `drive_list_files`, `drive_get_file`, and `drive_search_files` return empty results for Shared Drive content when called from a skill context, while the same calls work from a direct prompt. My Drive content works in both contexts. The regression has been reported publicly ([anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442)). Anthropic owns the fix.
- **OAuth scope differences.** The local Google Workspace MCP installations Rick and other operators run on Claude Code typically use the broad `https://www.googleapis.com/auth/drive` scope. The user-facing connectors in claude.ai may run with the narrower `drive.file` scope — which only sees files the app itself created. A connector with `drive.file` **cannot** see Shared Drives, regardless of the user's actual Workspace permissions. Worth checking the scope of any connector before debugging access issues.
- **Skill context vs direct prompt context.** A skill that's bundled as a runnable artifact may invoke MCP tools through a different code path than a direct conversation does — different argument shapes, different error handling. A skill that works when you test it in a direct prompt may fail when the same logic runs inside a skill dispatch. Always test in both contexts before shipping a Drive-touching skill.

The practical implication: when a skill that touches Drive works in a direct prompt but fails inside the deployed skill, **the bug is most often in the connector or the scope configuration, not in the skill code**. Don't waste hours rewriting skill logic to chase a connector regression.

**The durable workaround when connector parity breaks: work on a local copy.** Pull the file down to local storage with whatever read path does work (`download_file_content`, manual download, a different connector), do all the agent work locally, then sync back to Drive as a separate write step. The local copy bypasses every connector-level access regression — you fight one specific bug instead of a moving target. It's the pattern Rick has used reliably for years on `.pptx` and other non-native files that connector parity especially struggles with.

### The shape of a Docs operation

Most Docs API operations want either a `documentId` (the file you're editing) or a pair of `(documentId, index)` coordinates inside the document. The index is a character offset into the body text — counting whitespace, line breaks, the leading "1" at the top of the doc, every character. A paragraph at "the third heading" might be at index 1847. The index of the same paragraph after you insert 50 characters above it is 1897. **Indices shift with every write.** Code that hardcodes index values is broken before the second invocation.

The safe pattern for index work:

1. `getDocumentInfo` immediately before the operation.
2. Walk `body.content` paragraphs, find your target by content match (heading text, paragraph prefix).
3. Operate on the index returned in that same JSON snapshot.

If you read indices, do other work, then write — the indices may be stale. Re-fetch.

### Why markdown is the right wire format

`replaceDocumentWithMarkdown` and `appendMarkdown` are the highest-leverage tools in the entire Docs MCP. They handle the markdown → Google Docs body conversion (paragraphs, headings, bullets, basic formatting) in one call. Hand-stitching the equivalent via `insertText` + paragraph styles + text styles is multiple times more code and a magnet for the failure modes covered in Part 4.

The catch: markdown imports leave Google Docs **defaults** on every paragraph. Arial body, default heading sizes, no brand colors. The styling step exists because the markdown step erases custom styling. Mentally, treat `replaceDocumentWithMarkdown` as "set the body content," not as "set the body content as it should look." Looks-as-it-should is the next 30 lines of code.

---

## Part 2 — Patterns that work

### Pattern 1 — Edit existing documents in place

When updating any tracked Google Doc:

1. Read with `readDocument` (`format: "markdown"`).
2. Assemble new content.
3. Overwrite with `replaceDocumentWithMarkdown`, or `insertText` / `replaceRangeWithMarkdown` for surgical edits.

Never create a new Doc with the same title as a way to "prepend" content. This was a common workaround in 2024–2025 when in-place editing tools were incomplete or unstable. The MCPs released through 2025 close that gap. Holding onto the recreate-pattern as a habit produces duplicate files indefinitely.

**The failure mode this prevents.** A real incident: four files named `2026 ClientB Advisory Running Notes` in the same Drive folder. One was the live doc that all external bookmarks and Asana comments pointed at. The other three were stale recreations from earlier sessions that had silently fallen back to the recreate path. Spotted only because a human noticed; an unattended agent would have kept producing recreations forever. Three were trashed; the canonical doc id was pinned in config so subsequent runs couldn't drift.

**If a configured doc id doesn't resolve, STOP and ask** before creating a replacement. Silent recreation is exactly how duplicates accumulate. After every update, the agent should search Drive by title and confirm exactly one file matches. Two matches is a bug.

### Pattern 2 — Verify every style via JSON read, not tool success

After any `applyTextStyle` or `applyParagraphStyle` call, read the doc as JSON (`readDocument` with `format: "json"`) and inspect the actual values per paragraph in the affected range.

Inspect:

- `namedStyleType` (`TITLE` / `HEADING_1` / `HEADING_2` / `HEADING_3` / `NORMAL_TEXT`)
- `bullet` (present or absent?)
- For each `textRun`: `content`, `textStyle.fontFamily` and `weightedFontFamily.fontFamily`, `textStyle.bold`, `textStyle.foregroundColor`, `fontSize.magnitude`

**Silent failure modes that pass the tool-call success check:**

1. `applyTextStyle` with `{fontFamily: "X"}` (no `bold` flag) **overwrites existing bold formatting** on bold runs. Markdown's `**bold**` styling gets erased when you re-style. Mitigation: always include an explicit `bold: true` (or `false` for body sweeps) on every text-style application.
2. **Paragraph-range styles don't reliably cascade into bullet textRuns.** Bullets end up with `textStyle: {}` even when the parent paragraph range was styled. Mitigation: style each bullet individually with `matchInstance: N`. Don't rely on a parent range.
3. **`weightedFontFamily.weight: 400` can appear even when `bold: true` was set.** Visually bold appears, but the font variant is wrong. Mitigation: inspect both `bold` and `weightedFontFamily.weight` and re-apply if they disagree.
4. **Agents report "all styles applied successfully" when JSON inspection shows they weren't.** This is the most common subagent failure mode in production. Mitigation: do not trust the success message; the JSON is the contract.

The cost of verification is one `getDocumentInfo` call per style operation. The cost of not verifying is a doc that ships broken and a human who catches it later. The trade is unambiguous.

### Pattern 3 — Pre-resize images at the file level

`insertImage`'s `width` / `height` parameters do not reliably constrain rendered size. Google Docs renders the image at the source file's natural pixel dimensions regardless of what the API request says.

Confirmed against the same logo file: API width passed as 216 → 504 → 360 → 200 → visually identical in the rendered doc at every value. Pre-resizing the PNG to 400px wide produced the correct rendered size in one shot.

**The working pattern (macOS):**

```bash
sips --resampleWidth <target_px> path/to/source.png --out path/to/source_<target_px>.png
```

Then call `insertImage` with `localImagePath` pointing at the pre-resized file. Do **not** pass `width` — it's ignored or partially ignored, and you'll burn rounds tuning a number that has no effect.

The same rule applies to `appendMarkdown` and `replaceDocumentWithMarkdown` — markdown image syntax has no size hint, so size always reflects file dimensions.

For frequently-used assets (logos, brand marks), cache canonical pre-sized variants in a known location and reference them by path. Never let an agent decide which size to resize to — that's a configuration choice the operator owns.

### Pattern 4 — Cascade-check both directions

After every paragraph-style write, walk the JSON and count `namedStyleType` distribution. Two opposite regressions are possible; check for both.

**Failure mode A — Excess cascade.** A `replaceDocumentWithMarkdown` write cascades HEADING_1 across far more paragraphs than the markdown intended. Real example: a doc with 4 expected H1 headings rendered with 116 paragraphs all set to HEADING_1, producing huge-bold-Arial body throughout. Detection: if actual H1 count > 1.5× expected, the cascade fired.

**Recovery from excess cascade:**

1. `applyParagraphStyle` with `namedStyleType: NORMAL_TEXT` across the affected range.
2. Re-apply HEADING_1 only to the lines that should be H1, using `applyParagraphStyle` + `textToFind` per heading.
3. Re-apply heading text styles via `applyTextStyle`.
4. Re-read JSON. Confirm count now matches.

**Failure mode B — namedStyleType strip.** The inverse. A partial write — typically `replaceDocumentWithMarkdown` followed by the agent dying or being interrupted before the heading re-apply step ran — leaves every paragraph as NORMAL_TEXT. What should be the doc TITLE, section H1s, topic H2s, and sub-H3s all render as plain body text. Detection: if actual count of `(TITLE + HEADING_1 + HEADING_2 + HEADING_3)` < 0.5× expected, strip is live.

**Recovery from strip — atomic per heading**, do NOT separate the paragraph-style and text-style passes:

1. Parse expected headings from the markdown source. Build a list of `{ level, exact_text }`.
2. For each expected heading, in document order:
   - `applyParagraphStyle` with `namedStyleType: HEADING_<level>` and `textToFind` = the exact heading text.
   - Immediately `applyTextStyle` on the same `textToFind` with the right font, size, color, and `bold: true`.
   - Move to next heading.
3. Do not batch all paragraph styles, then all text styles. The gap between phases is exactly when an interruption strands the doc in a half-styled state.
4. Re-read JSON. Confirm heading count meets expected.

The asymmetry is important. The two failure modes look opposite but stem from the same fragility — the doc's style state is built up in multiple tool calls, and any interruption between calls leaves it inconsistent.

### Pattern 5 — Brand styling sequence: the only order that works

After any `replaceDocumentWithMarkdown` write, apply styling in **exactly this order**:

1. **Body sweep.** `applyTextStyle` with `{fontFamily: <body>, fontSize: <body>, foregroundColor: <body>, bold: false}` across the full document range (`startIndex: 1, endIndex: <doc end>`). This sets the baseline. Without it, body text stays Arial.
2. **Cascade check (interlude).** Read JSON, count HEADING_1s. If excess, reset to NORMAL_TEXT before going further.
3. **Re-apply paragraph style for each heading.** `applyParagraphStyle` with `namedStyleType: HEADING_1/2/3` and `textToFind: "<exact heading text>"`.
4. **Apply heading text style for each heading.** `applyTextStyle` with `{fontFamily: <heading>, fontSize: <heading>, foregroundColor: <heading>, bold: true}`. **`bold: true` is non-negotiable.** Omitting it overwrites the inherited bold and renders the heading visually weak.
5. **Inline bold prefixes inside bullets.** For label-prefixed bullets (`**Context:** ...`, `**Action Items:** ...`), each prefix must be styled individually via `applyTextStyle` with `textToFind: "Context:"` and `matchInstance: N`. Bullets do not inherit a parent range's styling.

Skipping any step produces a visually broken doc. Reordering the steps produces the same. The order is the pattern; treat it as load-bearing.

### Pattern 6 — Idempotency

Every write mode has an idempotency rule. Apply it before the write, not after.

| Mode | Idempotency check |
|---|---|
| `create` | `searchDriveFiles` in the target folder by title. If a match exists, return the existing doc id; do not create a new one. |
| `update` | `readDocument`, normalize whitespace, compare first ~500 chars of existing body to first ~500 of new content. Match → no-op. |
| `prepend` | Scan the top ~2000 chars for a section dated today. If one exists and overlaps with the new entry, no-op. |

Running the same write twice must reach the same Drive state. If it doesn't, the write is not idempotent — and your orchestrator's retry logic will silently duplicate content the first time a transient error fires.

---

## Part 3 — Hard limits the API does not support

These are not pattern errors. The Docs API genuinely lacks these capabilities as of mid-2026. Each has a working workaround; none have a "right" API call.

### Limit 1 — Cannot create PAGE_NUMBER / PAGE_COUNT auto-text in an existing doc

`createFooter` makes an empty footer. `insertText` can put plain text in the footer. But the API has no method to create the `AUTO_TEXT` elements that render `PAGE_NUMBER` and `PAGE_COUNT`. This has been a documented limitation for years (Google issue tracker reference: 162801033) and is unlikely to change soon.

**Workaround: `copyFile` from a template.**

1. Maintain a template document that already has the footer baked in. Page numbers live in `documentStyle.defaultFooterId` and the footer body contains `PAGE_NUMBER` + `PAGE_COUNT` `autoTextType` elements.
2. For any doc that needs the footer, use `copyFile` (Drive API) to clone the template, then `replaceDocumentWithMarkdown` with `firstHeadingAsTitle: false` to overlay your body content. The footer survives because it lives at the `documentStyle` level, not in the body stream that the markdown replacement touches.
3. **Never** use `createDocument` for a doc that needs page numbers — that path produces a doc without a footer and there's no way to add the auto-text back after the fact.

**Repair path for an existing doc missing the footer** is a doc swap: `copyFile` template → `replaceDocumentWithMarkdown` overlay → trash the old doc → rename the new one. Doc swap changes the doc id, which breaks every external reference (bookmarks, Asana comments, briefing links). Get explicit authorization before doing this. The alternative is a one-off UI fix: open the doc, `Insert → Page numbers`. Surface the missing footer to the human; let them choose between the swap and the click.

### Limit 2 — MCP availability differs by environment

The Google Workspace MCP server typically runs locally with credentials in Keychain (macOS) or equivalent. In automation environments (cloud functions, scheduled routines, CI runners), Keychain is unreachable. The MCP cannot run there.

**Workarounds:**

1. **Stdlib helper.** Write a small Python (or equivalent) helper that talks to the Drive + Docs REST APIs directly, with credentials from environment variables instead of Keychain. The helper handles `create`, `update`, `prepend` against the same logical contract as the MCP. Limited to body content; **the helper does not apply brand styling** (no MCP-grade paragraph/text-style calls). The styling step waits until an interactive run on the human's machine picks the doc up.
2. **Cloud-secret-proxy.** Stand up a small HTTPS endpoint backed by Google Cloud Secret Manager. The proxy holds the Drive/Docs OAuth credentials and exposes narrow write endpoints (`POST /drive-doc/write`, `POST /drive-doc/prepend`). The cloud automation calls the proxy; the proxy talks to the Google APIs. This separates credential storage from execution and works without Keychain.
3. **Mode marker on the input.** Whichever path you take, mark the doc's freshness: cloud-rendered docs are unstyled at the cascade level, and the next interactive run by the human reapplies brand styling. Mention this explicitly in the agent's return: `"created via cloud proxy; brand cascade pending interactive run"`.

The asymmetry is annoying. It exists because Anthropic's claude.ai Google Workspace connector doesn't yet have a writer-side org-level deployment. Until it does, the workaround stack is the cost of running Drive automation outside the human's laptop.

### Limit 3 — `insertImage` width / height parameters are unreliable

Covered in Pattern 3 above. Rendered size in Google Docs reflects the source file's pixel dimensions, not the API request. Workaround: pre-resize with `sips` or equivalent before insert. Don't pass `width` at all.

### Limit 4 — Named styles can only be edited via the Drive UI

Each Google Doc has a set of named styles (`Normal text`, `Heading 1`, `Heading 2`, etc.) defined at the document level. The MCP can read these (`getDocumentInfo` → `namedStyles`) but cannot update them. If a doc's `NORMAL_TEXT` named style is configured as Arial 11pt black, every paragraph that inherits from `NORMAL_TEXT` will render Arial 11pt black, regardless of how many `applyTextStyle` calls run on individual ranges.

**Workaround:** the only fix is in the Drive UI. `Format → Paragraph styles → Normal text → "Update Normal text to match"`. After applying brand styling once, click that menu item to bake it into the named style. From then on, the named style itself carries the brand defaults.

The agent's job is to surface the mismatch in its prose summary so the human knows to do the one-time UI click. Don't loop trying to fix it via the API — there's no API path that will work.

### Limit 5 — Non-native files need `download_file_content`, not `readDocument`

`readDocument` works on native Google Docs. For everything else in Drive — Microsoft Office documents (`.docx`, `.xlsx`, `.pptx`), PDFs, images, plain text, CSV — it errors or returns empty. These files don't have a Google Docs document structure.

**Workaround:**

- For raw content: `download_file_content` (Drive API) returns the file bytes. The agent does whatever processing it needs in memory or in a temp file.
- For Office documents specifically: `copyFile` with `mimeType: "application/vnd.google-apps.document"` (for `.docx`) or `application/vnd.google-apps.spreadsheet` (for `.xlsx`) converts to a native Doc/Sheet as part of the copy. Then `readDocument` works on the converted file. The original `.docx` stays untouched.
- For images and PDFs: pass the downloaded bytes to a model that supports the corresponding modality. Vision-capable models read images natively; PDF text extraction needs either server-side extraction tools or model-side PDF parsing.

The most common skill-level failure mode: calling `readDocument` on a Drive file id that resolves to a `.docx`. The error message rarely names this as the cause; the skill ends up reporting "couldn't read the doc" with no useful detail. Audit any skill that accepts "a Drive file id" as input — does it check `mimeType` before deciding how to read? If not, it's brittle on non-native files. The check is one extra `get_file_metadata` call and a switch on the returned mime type.

### Limit 6 — `replaceDocumentWithMarkdown` collapses consecutive `**Label:**` rows

When several `**Label:**` markdown lines sit on consecutive lines without blank lines between them, the markdown converter collapses them into a single paragraph and **strips the bold runs**. The result: a wall-of-text paragraph containing `**Format:** ... **Participants:** ... **Purpose:** ...` concatenated, with no bold formatting on any of the labels.

**Workaround on the source side:** when assembling markdown, give every `**Label:**` field its own paragraph with a blank line between each. Treat each label row as if it were a mini sub-heading.

**Workaround on the verify side:** after the write, walk paragraphs in the affected range. Within each paragraph, count distinct `**Label:**`-shaped runs. If any paragraph contains > 1, the collapse fired. Repair:

1. Identify the paragraph's start/end indices from the JSON.
2. Construct the corrected markdown — one `**Label:** value` per paragraph, blank line between.
3. `replaceRangeWithMarkdown` over the offending range.
4. Re-apply label styling on each via `applyTextStyle` with `textToFind: "Label:"`.

Cannot declare the write done until zero paragraphs contain ≥ 2 `**Label:**` runs.

---

## Part 4 — Anti-patterns to recognize

### Anti-pattern 1 — Recreating a doc with the same title to "prepend"

If you find code that creates a new doc, writes the prepend content + a separator + the old content, and then trashes the old doc, that's the recreate-pattern. It was a legitimate workaround in 2024 before in-place editing tools matured. It is the wrong move now.

Why it persists: it "works" until the trash step fails or the doc has external references that point at the old id. Then you have two files, or four, or eight. Spot it in code review by looking for `createDocument` calls inside what should be an "update" or "prepend" path.

Fix: switch to `replaceDocumentWithMarkdown` (full body replace) or `insertText` at index 1 (surgical prepend). The doc id stays stable.

### Anti-pattern 2 — Trusting tool success without JSON verification

If your code looks like this:

```
result = applyTextStyle(...)
if result.success:
    return "Styles applied"
```

…you have shipped the silent-failure failure mode. The tool returns success when:

- The API request succeeded, even though the doc didn't update the way you expected.
- The style was applied to one textRun but not the parent paragraph.
- Bold was overwritten on existing bold runs because no `bold: true` flag was passed.
- The cascade fired on a different range than intended.

Fix: every style operation is followed by a `getDocumentInfo` read and a JSON inspection of the affected range. Make this routine, not exceptional.

### Anti-pattern 3 — `insertText` at index 1 for a styled prepend

`insertText` inserts plain text. If your prepend content has `# H1` and `**bold**` markdown syntax in it, those tokens go into the doc as literal `#` characters and `**` characters with no styling applied.

For a prepend that needs styling, the right move is:

1. `readDocument` (`format: "markdown"`) to get the current body.
2. Assemble the new full body: `<new entry>\n\n---\n\n<existing body>`.
3. `replaceDocumentWithMarkdown` with the assembled full body.
4. Re-apply brand styling per Pattern 5.

`insertText` is the right tool for adding unstyled text (a tracker line, a timestamp). For styled content, use the markdown path.

### Anti-pattern 4 — Deleting human content during a reformat

The bright line is **information loss**, not formatting. Reformatting (P1 → bullets, header level changes, italic → bold) is fine. **Deleting, paraphrasing, or silently dropping content** — including pasted images, smart chips, comments, attachments, and typed prose — is not.

The failure mode: an agent runs `replaceRangeWithMarkdown` over a range that includes a pasted image. The reformat is correct; the image silently disappears. The image is gone from the doc and the original is gone from the agent's context. No recovery.

**Before any `replaceRangeWithMarkdown`, `deleteRange`, or `replaceDocumentWithMarkdown` that touches existing content:** read the JSON for the affected range and scan for:

- `inlineObjectElement` (pasted images, embedded files)
- `richLink` (linked Drive files rendered inline)
- `personElement` (smart chips for people)
- Any text runs the agent didn't author

If found, do not use a wholesale range replace. Instead: use surgical `applyTextStyle` / `applyParagraphStyle` on the existing structure, or `insertText` / `deleteRange` paragraph-by-paragraph around the embedded objects. If a wholesale replace is genuinely the right shape, extract the embedded objects first and re-insert them in the new content at the same logical position.

### Anti-pattern 5 — A subagent that reports "all styles applied successfully"

If a subagent's return message says "applied styling" without a JSON verification step, the message is unreliable. The verification step might be in the subagent's code, but if the message doesn't tell you the post-write state — heading counts, font names per heading, body color — the subagent is reporting tool-call success, not document state.

Fix: require the subagent's return contract to include a `verification` field with the actual post-write JSON inspection results. The orchestrator (or the human) reads the verification field, not the prose message.

---

## Part 5 — Architecture: the single-writer pattern

Most Drive/Docs automation fails because multiple agents touch the same doc with no coordination. One agent writes the body; another applies styling; a third inserts an image. None of them know what the others did. The cascade fires on a write that was supposed to be a no-op. The image gets inserted at the wrong index because the body shifted between dispatch and execution. The doc ends up in a state none of the agents intended.

The robust shape is the **single-writer pattern**: one specialized subagent owns all writes to Drive. Every orchestrator that needs to write a doc dispatches to that subagent. The subagent serializes its own work, owns the cascade-check, and returns a typed result.

### The typed input/output contract

```ts
type DriveDocWriterInput = {
  run_id: string;                 // orchestrator's run identifier (for logs)
  invocation_id: string;          // this dispatch's id (for logs)
  mode: "create" | "update" | "prepend";
  target:
    | { doc_id: string }
    | { folder_id: string; title: string };
  content: string;                // full markdown body
  brand: string;                  // your brand identifier, or "none"
};

type DriveDocWriterResult =
  | { type: "created"; doc_id: string; url: string }
  | { type: "updated"; doc_id: string; url: string; sections_added: number }
  | { type: "skipped_idempotent"; doc_id: string; url: string; reason: "already_current" }
  | { type: "failed"; reason: "trashed" | "permission_denied" | "api_error" | "target_unresolvable" | "empty_content"; message: string };
```

Four closed legal outcomes. Orchestrators dispatch on `reason`. `trashed` → ask a human to repoint. `permission_denied` → ask a human to fix sharing. `api_error` → retry later. `target_unresolvable` → the configured doc id doesn't match any file (typo or stale config). `empty_content` → the orchestrator bugged out and tried to write nothing; the writer refuses rather than wiping the doc.

The `message` is a one-line human-readable detail. Closed enums let orchestrators handle each path automatically; the message is for the human watching logs.

### State.json breadcrumbs

Before any `replaceDocumentWithMarkdown` / `replaceRangeWithMarkdown` / `insertText` call:

```json
{
  "doc_id": "...",
  "run_id": "...",
  "invocation_id": "...",
  "started_at": "ISO-8601",
  "phase": "body_write",
  "status": "in_progress",
  "expected_headings": { "TITLE": 1, "HEADING_1": 4, "HEADING_2": 8, "HEADING_3": 0 }
}
```

Write this to a known path (e.g., `/tmp/agent-runs/<run_id>/drive-doc-writer/<invocation_id>/state.json`). Update `phase` as you advance: `body_write` → `cascade_check` → `heading_styles` → `verify` → `done`. Set `status: "completed"` when the verify step passes.

If an interruption kills the process between phases, the file is the breadcrumb the recovery path uses.

### Resume-from-interruption

The next dispatch against the same doc looks for `state.json` files with `status: "in_progress"` for that `doc_id`. If one exists:

1. Read the interrupted run's `state.json` to learn which phase died.
2. Run cascade-check on the current document state (both directions — excess and strip).
3. Apply the matching reset-and-reapply path.
4. Mark the interrupted run's `state.json` as `status: "recovered_by_<new_run_id>"`.
5. Only then proceed with the new invocation's write.

Layering a fresh write on top of a half-styled doc compounds the damage. The recovery path prevents that.

### The four-layer post-write verify

Before declaring the write done, the writer runs four checks in order. Failure of any check triggers a single reapply attempt; persistent failure surfaces in the return.

| Layer | Check | What it catches |
|---|---|---|
| 1 | **Heading count** — tally `TITLE + HEADING_1 + HEADING_2 + HEADING_3` against expected, in both directions | Cascade overflow AND strip regression |
| 2 | **Per-paragraph style** — confirm font, size, color, bold per heading/body | Silent style overwrites from missing `bold` flags or wrong cascade |
| 3 | **Metadata-row collapse** — scan for paragraphs with > 1 `**Label:**` run | The markdown-collapse failure mode |
| 4 | **Named-style sanity** — inspect doc-level `namedStyles.NORMAL_TEXT`; if Arial / wrong size, flag in prose | Drive UI fix needed; surface to the human |

These run after the brand sequence, not in place of it. A doc that passes all four checks is healthy. A doc that fails any check ships with a flag in the agent's return so the human or the next orchestrator knows.

### Logging

Every invocation writes to a known per-invocation directory:

```
/tmp/agent-runs/<run_id>/drive-doc-writer/<invocation_id>/
  input.json       # the DriveDocWriterInput; content field truncated
  content.md       # full markdown actually written
  output.json      # the DriveDocWriterResult emitted
  pre_state.json   # getDocumentInfo before the write (update/prepend only)
  post_state.json  # getDocumentInfo after the write + cascade check
  log.txt          # one line per tool call: timestamp, tool, duration, ok/fail
  error.txt        # only on failure; full error payload
```

The log path makes silent failures debuggable later. Without it, "the doc looked wrong yesterday" is a question with no answer. With it, the post-write JSON sits on disk forever.

---

## Part 6 — How to measure whether your writes are healthy

Three observability surfaces, in order of leverage:

1. **Per-write log directories** (per the logging section above). The post-write JSON is the ground truth for any past write. Diff `pre_state` vs `post_state` to see exactly what changed and didn't.
2. **A daily drift report.** Run a scheduled job that walks every tracked doc and inspects:
   - Heading counts vs expected (from the doc's owning config or skill)
   - Named-style state (Arial drift on `NORMAL_TEXT`)
   - Footer presence on docs that should have one
   - Duplicate-title files in any tracked folder

   Surface drift in a single dashboard or message. A doc that drifts is one that an agent wrote into a state nobody intended.

3. **A post-deploy smoke test.** Whenever you change any styling code or the writer agent itself, run an end-to-end test: dispatch a `create` write into a sandbox folder, dispatch a `prepend` write to the same doc, read the JSON, assert the four verify-layers pass. Failing builds catch regressions before they hit production docs.

The Drive UI is not a measurement tool. "It looked right when I opened it" is not the same as "the JSON state matches what was written." Always go to JSON for the ground truth.

---

## What we still don't know

1. **Whether and when Google will ship API support for creating PAGE_NUMBER auto-text in existing docs.** The limitation has been around for years; the workaround (template + `copyFile`) is stable, but a future API change would make a lot of footer-related code obsolete. Watch the Google Docs API changelog.

2. **Whether Anthropic ships an org-level Workspace MCP for writer-side ops.** The current connector is read-heavy and primarily user-facing. A writer-side org-level connector would remove the need for the stdlib helper / cloud-secret-proxy stack documented in Limit 2. Until it lands, the workaround is real cost.

3. **Whether `replaceDocumentWithMarkdown` will stabilize on metadata-row formatting.** The current consecutive-`**Label:**` collapse is a quirk of the markdown converter, not a deliberate behavior. A future MCP release may fix it; until then, the source-side rule (blank line between every `**Label:**` row) is the durable defense.

4. **Whether the cascade-style failure modes will reduce as MCP servers mature.** Both excess cascade and namedStyleType strip are interactions between the markdown converter and the doc's named styles. As the converter gets smarter, the regressions may become rarer. Keep cascade-check as a defense regardless — the cost is one extra `getDocumentInfo` per write, and the failure modes are too expensive to leave undefended.

---

## Sources & Attribution

This guide synthesizes patterns and failure modes from running Google Drive + Docs automation in production through 2025–2026. The source taxonomy applied throughout: **failure mode > workaround > pattern**. Every limitation has a documented failure that produced it, and every pattern has a workaround it replaces.

### Anthropic / Model Context Protocol

- [Model Context Protocol specification](https://modelcontextprotocol.io/) — the protocol every MCP server implements
- [MCP server registry / community list](https://github.com/modelcontextprotocol/servers) — production MCP servers including Google Workspace implementations

### Google Workspace APIs

- [Google Docs API reference](https://developers.google.com/docs/api/reference/rest) — the underlying REST API every MCP wraps
- [Google Drive API reference](https://developers.google.com/drive/api/reference/rest/v3) — file-level operations
- [Document object JSON schema](https://developers.google.com/docs/api/reference/rest/v1/documents) — the structure inspected during verification

### Documented limitations

- [Google issue tracker #162801033](https://issuetracker.google.com/issues/162801033) — the long-standing PAGE_NUMBER auto-text limitation referenced in Limit 1
- [Docs API named styles documentation](https://developers.google.com/docs/api/concepts/styles) — confirms named-style edits are document-level and require the UI for the "Update Normal text to match" operation
- [anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442) — the Cowork Shared Drive access regression referenced in the connector parity section

### Authentication & credentials

- [Google OAuth 2.0 for installed applications](https://developers.google.com/identity/protocols/oauth2/native-app) — the consent flow used by every MCP-installed helper
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs) — the canonical place for credentials in the cloud-secret-proxy pattern

### Markdown ↔ Docs conversion

- [CommonMark specification](https://commonmark.org/) — the markdown variant most MCP servers implement against
- [Google Docs markdown import behavior](https://workspaceupdates.googleblog.com/2024/07/import-markdown-google-docs.html) — the official announcement that grounds the `replaceDocumentWithMarkdown` behavior

The patterns and anti-patterns documented here emerged from real production failures across 2025–2026. Each was caught the first time by a human, fixed once, and lifted into the writer agent's playbook so it cannot recur silently. The article is the public form of that playbook.
