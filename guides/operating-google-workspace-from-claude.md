---
title: Operating Google Drive, Docs, Sheets, and Slides from Claude
description: The patterns, hard limits, and anti-patterns of writing to Google Drive, Docs, Sheets, and Slides from Claude or any AI agent. Workarounds for what the APIs simply cannot do, plus surface-specific deep dives (Docs styling cascade; Sheets USER_ENTERED + values-vs-structure split; Slides object-ID stability + the under-served MCP surface). Every claim grounded in a specific failure mode.
date: 2026-05-25
last_modified_at: 2026-05-25
author: Rick Watson
agent_friendly: true
keywords: Google Drive, Google Docs, Google Sheets, Google Slides, Sheets API, Slides API, MCP, model context protocol, AI agents, Claude, automation, document automation, OAuth, Drive API, Docs API, valueInputOption, developer metadata, objectId, presentations batchUpdate
---

# Operating Google Drive, Docs, Sheets, and Slides from Claude

**Most production Drive/Docs/Sheets/Slides automation fails for five reasons. This guide names each one, gives the workaround, and shows the agent pattern that survives mid-write interruptions.**

**Published:** <time datetime="2026-05-25">2026-05-25</time>  ·  **Last updated:** <time datetime="2026-05-25">2026-05-25</time>  ·  **Author:** [Rick Watson](https://www.rmwcommerce.com/), Principal, RMW Commerce Consulting  ·  **Canonical URL:** [`github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-workspace-from-claude.md`](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-workspace-from-claude.md)  ·  **Reading time:** 10-min skim · 55-min deep read

Who this is for: developers and operators using Claude (or any AI agent) to read and write Google Drive files, Google Docs, Google Sheets, and Google Slides at scale. Anyone who has watched an agent overwrite styled formatting, create four files with the same title, write a formula that lands as a literal string, hand-craft a `batchUpdate` for a deck because the MCP didn't expose it, or report "all styles applied successfully" while the document renders broken.

**Jump to:** [60-second map](#the-60-second-map--what-youre-actually-working-with) · [What's possible](#whats-possible--the-headline-capabilities) · [What's NOT possible](#whats-not-possible--and-the-workaround) · [Where to spend your time](#where-to-spend-your-time--docs) · [TL;DR](#tldr--the-five-non-obvious-bits) · [Sheets (Part 7)](#part-7--operating-google-sheets) · [Slides (Part 8)](#part-8--operating-google-slides) · [Full TOC](#whats-in-this-article)

---

## The 60-second map — what you're actually working with

Four surfaces, four different mental models. The most common production bug is confusing them.

| Surface | What it is | What it's good for | Addressing model |
|---|---|---|---|
| **Drive** | The file system | List, search, copy, move, share, manage permissions. File metadata. **Never content.** | File ID |
| **Docs** | The document editor | Read body, write text, apply styles, insert images, manage comments. | Character index into body |
| **Sheets** | The spreadsheet | Cells, ranges, formulas, formatting, conditional rules, charts. | A1 ranges OR zero-based GridRange |
| **Slides** | The presentation editor | Slides, shapes, tables, images, charts, speaker notes. | String `objectId` per element |

You reach Drive through `mcp__google-docs__searchDriveFiles`, the lighter `mcp__claude_ai_Google_Drive__*` family, or the [Drive REST API v3](https://developers.google.com/workspace/drive/api/reference/rest/v3) directly. Docs (~80 tools) and Sheets (~20 tools) go through `mcp__google-docs__*`. Slides has the shallowest MCP coverage — production servers expose ~7 tools, most agents end up authoring raw `presentations.batchUpdate` payloads. [Part 1](#part-1--the-toolset-and-the-mental-model) covers connector / scope / write-path trade-offs; [Part 8](#part-8--operating-google-slides) covers the Slides shape in depth.

### If you read nothing else, this is the minimum viable pattern

```
1. readDocument(doc_id, format: "json")        // baseline JSON
2. replaceDocumentWithMarkdown(doc_id, markdown)  // body write
3. applyTextStyle / applyParagraphStyle          // brand styling (mandatory — markdown imports leave defaults)
4. readDocument(doc_id, format: "json")        // verify the styles landed
5. Compare expected vs actual per paragraph    // tool success ≠ task success
```

That five-step skeleton catches the largest share of real-world failure modes. The rest of this guide is the named failures it prevents, the architectural pattern that makes it survive interruptions, and the Sheets equivalent.

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from the public Google Workspace APIs and Anthropic's Model Context Protocol. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## What's possible — the headline capabilities

| You want to... | Tool you reach for | Notes |
|---|---|---|
| Create a Doc from markdown content | `replaceDocumentWithMarkdown` on a newly-created file | Apply brand styling AFTER — markdown imports leave Arial / default heading sizes |
| Update a Doc body | Same tool, existing `doc_id` | Scan for embedded human content first (smart chips, pasted images, comments) |
| Prepend a styled section to a Doc | Read existing → assemble → full-body replace | NOT raw `insertText` at index 1 — markdown tokens land as literal characters |
| Insert an image | Pre-resize source with `sips` → `insertImage` with `localImagePath` | API `width`/`height` parameters are unreliable; pre-resize is the constraint |
| Read a Doc as data | `readDocument` with `format: "json"` | Walk paragraphs; inspect `textRun`, `inlineObjectElement`, `richLink`, `person` |
| Style a Doc per brand | 5-step sequence: body sweep → cascade check → paragraph styles → text styles → inline bold | Part 2 — the only order that works |
| Create a Sheet | `createSpreadsheet` | |
| Write Sheet cell values | `writeSpreadsheet` with `valueInputOption=USER_ENTERED` | `RAW` lands `=SUM(...)` as a literal string starting with `=` |
| Read Sheet values for computation | `readSpreadsheet` with `valueRenderOption=UNFORMATTED_VALUE` | `FORMATTED_VALUE` returns locale-rendered strings; round-trip risk |
| Search / find / copy Drive files | `searchDriveFiles` or `mcp__claude_ai_Google_Drive__search_files` | Connector parity differs; test in both contexts |
| Copy a templated file | `copyFile` (Drive `files.copy`) | The only path for docs needing page numbers or footers |
| Convert `.docx` / `.xlsx` / `.pptx` to native | Upload via `files.create` with target mimeType (e.g. `application/vnd.google-apps.document`) | The original Office file stays untouched |
| Read non-native file content | `download_file_content` (Drive) | `readDocument` errors on non-native; check `mimeType` before reading |

---

## What's NOT possible — and the workaround

The hard limits the APIs simply do not support. Each row names a workaround. Scan this table before assuming you've found a new bug — most "the API can't do X" complaints land on a known limit.

| You want to... | Reality | Workaround |
|---|---|---|
| Create `PAGE_NUMBER` / `PAGE_COUNT` auto-text in an existing Doc | No `CreateAutoTextRequest` exists; `createFooter` makes an empty footer only | `copyFile` from a template that already has the footer baked in |
| Resize an image via `insertImage` parameters | The width/height fields don't reliably constrain rendered size | Pre-resize the source file (`sips --resampleWidth`); cache canonical variants |
| Edit doc-level named styles via API | `NamedStyles` is read-only | Drive UI: Format → Paragraph styles → "Update Normal text to match" |
| Avoid the consecutive-`**Label:**` collapse on markdown import | The markdown converter collapses adjacent label lines into one paragraph, stripping bold | Blank line between every `**Label:**` row in source |
| Edit a table in a tab-enabled Doc | `listDocumentTables`, `updateTableBorders`, `updateTableCellStyle`, `updateTableColumnWidth` fail with a field-mask error on any doc with the `tabs` field | Drive UI, or `.docx` export → edit → re-import as native Doc |
| Insert blob images (`CellImage`) into Sheet cells | No API insert method | Apps Script `SpreadsheetApp.newCellImage()`, OR `IMAGE()` formula with a public URL |
| Partially edit a pivot table | No fields-mask path | Rewrite the entire `pivotTable` value via `UpdateCellsRequest` |
| Style Sheets charts comprehensively | API exposes limited chart settings | Apps Script for advanced styling, or render the chart elsewhere + `IMAGE()` |
| Concurrent Sheets writes without races | No If-Match / ETag concurrency on values | Serialize dependent writes in one `batchUpdate` |
| Trigger on cell edit / render Sheets sidebar UI | API has no triggers or UI surface | Apps Script (`onEdit`, `onChange`, time-driven), or external orchestration |
| Read Shared Drive content from a skill (Cowork) | Works in direct prompt; fails in skill context | [Tracked as anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442). Local-first workflow until fixed: pull file via working read path, edit locally, sync back |
| Insert page-number footer into an existing Watson Weekly–style doc | Same root limit as PAGE_NUMBER above; can only flag and surface | Doc swap (`copyFile` template → overlay body → trash old → rename) OR one-click UI fix in the Drive editor |
| Trust tool-call success without verification | `applyTextStyle` returns success while overwriting bold runs, leaving bullets as `textStyle: {}`, or setting `weightedFontFamily.weight: 400` even when `bold: true` was set | Read JSON, walk paragraphs, verify per-paragraph values explicitly after every style write |

---

## Where to spend your time — Docs

Once the map is clear, here are the patterns that close the largest share of real-world failure modes. **The reader who only adopts items 1–5 closes the largest share of real-world failure modes.** These cover **Docs** specifically — Sheets has its own priority table in [Part 7](#part-7--operating-google-sheets).

| # | Pattern | Why it matters | Effort |
|---|---|---|---|
| 1 | **Verify every style via JSON read, not tool success** | The single most expensive failure mode. `applyTextStyle` returns success while silently overwriting bold, leaving bullets as `textStyle: {}`, or setting wrong font weight. The JSON is the only ground truth. | Low |
| 2 | **Brand styling sequence: body sweep → cascade check → heading paragraph styles → heading text styles → inline bold prefixes** | The only 5-step order that works. Every other order produces a visually broken doc that passes individual tool-call success checks. | Medium |
| 3 | **Cascade-check both directions after every paragraph-style write** | Two opposite failure modes: HEADING_1 cascades across too many paragraphs (huge bold body) AND mid-write interruption leaves every paragraph as NORMAL_TEXT (no headings). Detect both before declaring success. | Medium |
| 4 | **Pre-resize images at the file level (`sips` on macOS) before `insertImage`** | API width/height parameters don't reliably constrain rendered size. Source file pixel dimensions win. | Low |
| 5 | **Copy from template for any doc that needs a page-number footer** | The Docs API cannot create `PAGE_NUMBER` / `PAGE_COUNT` auto-text. `copyFile` from a template that has the footer baked in is the only path. | Medium |
| 6 | **Edit existing docs in place — never recreate to "prepend"** | Recreating a doc with the same title to insert content at top is how duplicates accumulate. Use `replaceDocumentWithMarkdown` on a stable `doc_id`. | Low |
| 7 | **Treat all existing human content as load-bearing** | Range replaces and `deleteRange` silently overwrite pasted images, smart chips, comments, manual edits. Inspect JSON for `inlineObjectElement`, `richLink`, `person` first. | Medium |
| 8 | **Idempotency: search-before-create, body-match-before-update, date-match-before-prepend** | Rerunning the same write must reach the same Drive state. Prevents duplicate-title accumulation when an orchestrator retries on transient errors. | Low |
| 9 | **State.json breadcrumbs for resume-from-interruption** | A write killed mid-cascade strands the doc half-styled. State.json lets the next dispatch detect the interruption and recover before compounding damage. | High |

Most readers should adopt items 1–5 and stop. Items 6–9 are amplification, mostly relevant once you're running document writes from an unattended orchestrator.

---

## TL;DR — the five non-obvious bits

If you read nothing else, internalize these. They're the highest-leverage corrections most operators need to make to existing automation. None of them are obvious from reading Google's docs.

1. **Tool success ≠ task success.** After every style write, read the doc as JSON and verify the values actually landed. Silent partial-success is the single most expensive failure mode in production.
2. **Markdown imports leave Google Docs defaults.** A markdown write is a body write, not a style write. Brand styling is the next 30 lines of code — there is no skipping it.
3. **For Sheets, `USER_ENTERED` is the load-bearing default.** `=SUM(A1:A10)` with `RAW` lands the literal string in the cell. Pass `USER_ENTERED` explicitly on every write.
4. **The Docs API cannot insert PAGE_NUMBER footers into an existing doc.** Period. Page-numbered docs must come from `copyFile` of a template you built. No API path adds the footer afterward.
5. **Same MCP server name, different products, different bugs.** A skill that works in a direct prompt can fail in skill-dispatch context. Test in both before shipping.

---

## What's in this article

- [Part 1 — The toolset and the mental model](#part-1--the-toolset-and-the-mental-model) — including [connector parity gotchas](#connector-parity-is-not-guaranteed)
- [Part 2 — Patterns that work (Docs)](#part-2--patterns-that-work)
- [Part 3 — Hard limits the API does not support](#part-3--hard-limits-the-api-does-not-support) — including [non-native files](#limit-5--non-native-files-need-download_file_content-not-readdocument)
- [Part 4 — Anti-patterns to recognize](#part-4--anti-patterns-to-recognize)
- [Part 5 — Architecture: the single-writer pattern](#part-5--architecture-the-single-writer-pattern)
- [Part 6 — How to measure whether your writes are healthy](#part-6--how-to-measure-whether-your-writes-are-healthy)
- [Part 7 — Operating Google Sheets](#part-7--operating-google-sheets) — values-vs-structure split, A1 vs GridRange, USER_ENTERED defaults, developer metadata, Sheets-specific hard limits
- [Part 8 — Operating Google Slides](#part-8--operating-google-slides) — object-ID addressing, the under-served MCP surface, template-copy workflow, placeholder-text gotcha, no-transitions / no-animations / no-private-images limits
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

**A naming note for the rest of this article.** Tool names like `replaceDocumentWithMarkdown`, `copyFile`, `applyTextStyle`, `insertImage`, and `getDocumentInfo` are **MCP server tool names**, not Google REST API methods. Each wraps one or more underlying Google API calls. `replaceDocumentWithMarkdown` is a server-side wrapper that uploads markdown via [`files.update`](https://developers.google.com/workspace/drive/api/reference/rest/v3) with the right mimeType; `applyTextStyle` wraps the Docs API's [`updateTextStyle`](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/batchUpdate) request type. The canonical production MCP that exposes these is [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) (~2.5k stars, OAuth 2.1, actively maintained); other implementations exist. When this article mentions a tool name, assume it's the server-side wrapper. When it cites a Google API field or method, the link goes to Google's own reference. The distinction matters only when you're reading code or filing a bug against the right project.

### Connector parity is not guaranteed

The same MCP server name in different products can behave differently. As of mid-2026, three real divergences hit production:

- **Shared Drive access in claude.ai / Cowork.** The Google Drive connector has had documented regressions where `drive_list_files`, `drive_get_file`, and `drive_search_files` return empty results for Shared Drive content when called from a skill context, while the same calls work from a direct prompt. My Drive content works in both contexts. The regression has been reported publicly ([anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442)). Anthropic owns the fix.
- **OAuth scope differences.** Local Google Workspace MCP installations on Claude Code typically use the broad [`https://www.googleapis.com/auth/drive`](https://developers.google.com/workspace/drive/api/guides/api-specific-auth) scope. User-facing connectors in claude.ai may run with the narrower `drive.file` scope — which Google defines as "per-file access to files created or opened by the app" via a picker flow. A connector running `drive.file` is not Shared-Drive-aware by default and will not see Shared Drive files the user has full Workspace permissions on. Worth checking the scope of any connector before assuming a permissions or access regression.
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

### Three write paths, not two

There are actually three paths to get body content into a Google Doc, not two. Each has trade-offs.

| Path | What it is | Strengths | Trade-offs |
|---|---|---|---|
| **MCP `replaceDocumentWithMarkdown`** | The MCP server wraps markdown upload via Drive `files.update`. One call. | Default for any MCP-enabled environment. Handles paragraphs, headings, bullets, basic formatting in one shot. | Leaves Google Docs defaults on every paragraph (Arial body, default heading sizes, no brand colors). Styling pass mandatory. |
| **Raw Docs API `batchUpdate`** | Per-element `insertText` / `applyParagraphStyle` / `applyTextStyle` requests assembled into one batched call. | Surgical. No markdown round-trip. Full control over every textRun. | Multiples more code. The failure modes in Part 4 cluster around this path. |
| **Drive HTML-import** | Multipart upload of inline-CSS HTML with `mimeType=application/vnd.google-apps.document`. Drive converts to a native Doc. | Faster than markdown for large content. Preserves headings, links, bold, lists, tables natively. The canonical "no MCP available" workaround. | Drive's HTML import **strips inline CSS for fonts and colors** — you still need a follow-up `batchUpdate` styling pass. Tables and nested lists can come through with subtle structural differences. |

Most automation uses path 1 for the common case and falls back to path 3 in cloud environments where the MCP server isn't reachable. Path 2 is for surgical edits inside an otherwise-styled doc, not for full body composition.

The catch shared across all three: every path leaves Google Docs **defaults** on the body unless you run an explicit styling pass after the upload. Mentally, treat the body-content write as "set the body content," not as "set the body content as it should look." Looks-as-it-should is the next 30 lines of code, regardless of which path delivered the body.

### Workspace plans + personal accounts: what's different

This article assumes you're operating against a Google Workspace org with broad programmatic access. That isn't every reader. Material differences exist by plan tier and account type — most don't matter until they do, and then they matter completely.

| Surface | What changes | Affects |
|---|---|---|
| **Shared Drives** | Available on every **paid** Workspace edition including Business Starter (since Sep 2024) and on Enterprise / Education Standard+. Not available on personal `@gmail.com` accounts. ([Workspace Updates, Aug 2024](https://workspaceupdates.googleblog.com/2024/08/shared-drive-access-business-starter.html)) | Any code that lists / writes Shared Drive content fails on personal accounts. The [Cowork connector regression](https://github.com/anthropics/claude-code/issues/53442) is about Shared Drives specifically — personal-account users aren't affected because the surface doesn't exist for them. |
| **Service accounts + domain-wide delegation** | Service accounts can live in any GCP project (including personal-account-owned). But **DWD authorization requires a Workspace super admin**, and impersonation only works against managed Workspace users — never against `@gmail.com` accounts. ([Workspace Admin Help](https://support.google.com/a/answer/162106)) | Any headless / scheduled write that depends on impersonation requires a Workspace target. The cloud-secret-proxy pattern in Part 5 assumes this works. |
| **Admin API access control** | **Every** Workspace edition's super admin can use Admin Console → Security → Access and data control → API controls → App access control to block third-party apps org-wide, restrict by scope, or mark apps as trusted / limited / blocked. The setting overrides user-level OAuth grants. ([Workspace Admin Help](https://support.google.com/a/answer/7281227)) | An app that works for the developer can fail with opaque 403s when an external user from a managed org tries to install it. Always check admin-side blocks before debugging code. |
| **Restricted-scope OAuth verification** | External apps requesting `https://www.googleapis.com/auth/drive` (the broad "restricted" scope) for personal Google account users need Google verification plus an annual [CASA Tier 2 assessment](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification) by an approved lab. Internal Workspace apps (Internal user type, same-org users only) skip both. | Any app shipped to personal-account users with broad Drive scope hits this gate. Building for internal Workspace use only is much faster to launch. |
| **Context-Aware Access** | Available on Enterprise Standard / Plus, Education Standard / Plus, Frontline Standard, Cloud Identity Premium, and Enterprise Essentials Plus. ([Workspace Admin Help](https://support.google.com/a/answer/9275380)) Not on Business tier or personal accounts. VPC Service Controls is a separate Google Cloud feature available alongside these tiers. | Enterprise environments can block API calls by network, device posture, or service perimeter — even with valid tokens. Calls succeed in dev, fail in prod from a non-corporate network. |
| **Drive classification labels** | Manual labels: Business Standard / Plus, Enterprise Standard / Plus, Education Standard / Plus, Frontline (all tiers), Essentials / Enterprise Essentials. ([Workspace Admin Help](https://support.google.com/a/answer/13127870)) DLP rules that auto-apply labels: narrower — Frontline Standard / Plus, Enterprise Standard / Plus, Education Fundamentals / Standard / Plus. Not on any Business tier. | Reads / writes may interact with label-based access controls; DLP can block writes that match policy. |
| **Audit logs and Vault** | Admin audit logging of API writes is generally available across Workspace editions since [May 2024](https://workspaceupdates.googleblog.com/2024/05/audit-logs-for-API-based-actions.html). Vault (eDiscovery / retention) is included on Business **Plus**, Enterprise (Standard / Plus / Essentials), and Education Standard+ — **not** Business Starter or Business Standard. Personal accounts have neither. | Some operators (legal-sensitive sectors) need to know their writes are auditable; some need to know they aren't. |
| **Document tabs** | Available on all Workspace plans AND personal `@gmail.com` accounts since [October 2024](https://workspaceupdates.googleblog.com/2024/10/tabs-in-google-docs.html). The `tabs` field appears in the Docs API JSON regardless of account type. | The tab-enabled-docs MCP gotcha (next section) affects every reader, not just Workspace ones. |

**What's NOT a plan-tier difference** — API quotas. The default per-user / per-project quotas (60 req/min/user on Sheets, similar elsewhere) are tied to the GCP project that owns the OAuth client, not to any Workspace SKU. Quota-increase requests go through the GCP console for any project owner — personal accounts included. Approval is at Google's discretion based on usage justification, not on what Workspace plan the user holds.

### The tab-enabled-docs MCP gotcha

Google Docs added document tabs (multiple tab surfaces inside a single doc, similar to Sheets) to the production UI in 2024. Any doc created in the new editor carries a `tabs` field at the document root, and the Docs API's legacy text/table tools fail on these docs with a field-mask error along the lines of `document.tabs and legacy text-level fields cannot be specified in the same request`. As of mid-2026, the MCP-exposed tools that hit this failure include `listDocumentTables`, `updateTableBorders`, `updateTableCellStyle`, and `updateTableColumnWidth`. The body-text tools (`insertText`, `applyTextStyle`, `applyParagraphStyle`, `replaceDocumentWithMarkdown`) work fine; the failure is specific to the table-manipulation surface.

Workarounds: edit table structure manually in the Drive UI, or export to `.docx`, edit, and re-import as a native Doc. The native re-import does not carry the `tabs` field forward.

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
3. **`weightedFontFamily.weight: 400` can appear even when `bold: true` was set.** Visually bold appears, but the font variant is wrong. Per the [TextStyle reference](https://googleapis.dev/java/google-api-services-docs/latest/com/google/api/services/docs/v1/model/TextStyle.html), `weightedFontFamily` is applied first and weight defaults to 400; the `bold` flag is applied separately and the two can disagree. Mitigation: pass `weightedFontFamily: {fontFamily: "X", weight: 700}` AND `bold: true` together on the same request, and include both subfields in the `fields` mask. Inspect both `bold` and `weightedFontFamily.weight` in the post-write JSON; re-apply if they disagree.
4. **Agents report "all styles applied successfully" when JSON inspection shows they weren't.** This is the most common subagent failure mode in production. Mitigation: do not trust the success message; the JSON is the contract.

The cost of verification is one `getDocumentInfo` call per style operation. The cost of not verifying is a doc that ships broken and a human who catches it later. The trade is unambiguous.

### Pattern 3 — Pre-resize images at the file level

`insertImage`'s `width` / `height` parameters do not reliably constrain rendered size. Google Docs renders the image at the source file's natural pixel dimensions regardless of what the API request says.

Confirmed against the same logo file: API width passed as 216 → 504 → 360 → 200 → visually identical in the rendered doc at every value. Pre-resizing the PNG to 400px wide produced the correct rendered size in one shot.

**The working pattern (macOS):**

```bash
sips --resampleWidth <target_px> path/to/source.png --out path/to/source_<target_px>.png
```

Then call `insertImage` with `localImagePath` pointing at the pre-resized file. Passing `width` and `height` alongside a pre-resized file is fine and often correctly constrains the rendered size; the failure mode is passing `width` *without* pre-resizing and expecting it to do the work. The constraint comes from Google's image-insertion model; Kanshi Tanaike's [Limitations for inserting images to Google Docs](https://tanaikech.github.io/2019/04/05/limitations-for-inserting-images-to-google-docs/) documents both this and the lesser-known 25-million-pixel² area limit.

**Three discipline rules around this pattern:**

1. **Cache canonical pre-sized variants.** Once you've resized a logo or brand asset, store the pre-sized copy at a known path (e.g., a project-level `.assets/` folder). Never re-resize on every invocation — the deterministic output of `sips` is fine, but multiple resize passes accumulate compression artifacts.
2. **Denylist ad-hoc source paths.** Maintain an explicit allowlist of where canonical assets live, plus a denylist of common drift sources (`~/Downloads/`, ad-hoc desktop folders). Agents have a strong tendency to grab the most-recent file with a matching name, which is often a stale download.
3. **Verify image URL content-type BEFORE handing off to `insertImage`.** Broken CDN URLs and login-walled images both return HTTP 200 with non-image content-types (HTML error pages, login redirects). `insertImage` will silently place a broken-image placeholder with no error. The fix: a HEAD or GET on the URL upstream, check `Content-Type` starts with `image/`, only hand off verified URLs.

The same rule applies to `appendMarkdown` and `replaceDocumentWithMarkdown` — markdown image syntax has no size hint, so size always reflects file dimensions.

For frequently-used assets (logos, brand marks), cache canonical pre-sized variants in a known location and reference them by path. Never let an agent decide which size to resize to — that's a configuration choice the operator owns.

### Pattern 4 — Cascade-check both directions

After every paragraph-style write, walk the JSON and count `namedStyleType` distribution (the legal values are `TITLE`, `HEADING_1` through `HEADING_6`, `NORMAL_TEXT`, plus a few list/quote variants — see [Format text in a Google Doc](https://developers.google.com/workspace/docs/api/how-tos/format-text)). Two opposite regressions are possible; check for both.

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

After any `replaceDocumentWithMarkdown` write, apply styling in **exactly this order**. The MCP wraps the underlying [`updateTextStyle`](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/batchUpdate) and `updateParagraphStyle` request types; the steps below are the call sequence that survives every interaction failure mode documented in Pattern 4 and Anti-pattern 2:

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

`createFooter` makes an empty footer. `insertText` can put plain text in the footer. But the API has no method to create the [`AutoText`](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents) elements that render `PAGE_NUMBER` and `PAGE_COUNT` — there is no `CreateAutoTextRequest` in the [batchUpdate request catalog](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/request). Tracked publicly on Google's issue tracker as [#162801033](https://issuetracker.google.com/issues/162801033) (sign-in required to read; the limitation is also discussed in community threads on [page-number workarounds](https://community.latenode.com/t/how-to-add-footer-page-numbering-in-google-docs-via-api-using-php/38578)).

**Workaround: `copyFile` from a template.**

1. Maintain a template document that already has the footer baked in. Page numbers live in `documentStyle.defaultFooterId` and the footer body contains `PAGE_NUMBER` + `PAGE_COUNT` `autoTextType` elements.
2. For any doc that needs the footer, use the [Drive `files.copy`](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/copy) call (the MCP server typically exposes this as `copyFile`) to clone the template, then overlay your body content with `replaceDocumentWithMarkdown`. Some MCP server implementations expose a `firstHeadingAsTitle: false` option on the markdown overlay; **verify it exists on your specific server before relying on it.** When supported, set it so the body H1 stays a `HEADING_1` rather than getting promoted to the doc title (which would interact badly with the template's title styling). When the flag isn't supported, the workaround is to skip the body H1 in the markdown source and apply title styling separately. The footer survives because it lives at the `documentStyle` level, not in the body stream that the markdown replacement touches.
3. **Never** use `createDocument` for a doc that needs page numbers — that path produces a doc without a footer and there's no way to add the auto-text back after the fact.

**Repair path for an existing doc missing the footer** is a doc swap: `copyFile` template → `replaceDocumentWithMarkdown` overlay → trash the old doc → rename the new one. Doc swap changes the doc id, which breaks every external reference (bookmarks, Asana comments, briefing links). Get explicit authorization before doing this. The alternative is a one-off UI fix: open the doc, `Insert → Page numbers`. Surface the missing footer to the human; let them choose between the swap and the click.

### Limit 2 — MCP availability differs by environment

The Google Workspace MCP server typically runs locally with credentials in Keychain (macOS) or equivalent. In automation environments (cloud functions, scheduled routines, CI runners), Keychain is unreachable. The MCP cannot run there.

**Workarounds:**

1. **Stdlib helper.** Write a small Python (or equivalent) helper that talks to the Drive + Docs REST APIs directly, with credentials from environment variables instead of Keychain. The helper handles `create`, `update`, `prepend` against the same logical contract as the MCP. Limited to body content; **the helper does not apply brand styling** (no MCP-grade paragraph/text-style calls). The styling step waits until an interactive run on the human's machine picks the doc up.
2. **Cloud-secret-proxy.** Stand up a small HTTPS endpoint backed by Google Cloud Secret Manager. The proxy holds the Drive/Docs OAuth credentials and exposes narrow write endpoints (`POST /drive-doc/write`, `POST /drive-doc/prepend`). The cloud automation calls the proxy; the proxy talks to the Google APIs. This separates credential storage from execution and works without Keychain.
3. **Mode marker on the input.** Whichever path you take, mark the doc's freshness: cloud-rendered docs are unstyled at the cascade level, and the next interactive run by the human reapplies brand styling. Mention this explicitly in the agent's return: `"created via cloud proxy; brand cascade pending interactive run"`.

The asymmetry is annoying. It exists because Anthropic's claude.ai Google Workspace connector doesn't yet have a writer-side org-level deployment. Until it does, the workaround stack is the cost of running Drive automation outside the human's laptop.

**Plan-tier caveat:** both workarounds above use OAuth user-token credentials. The conceptually-cleaner alternative — a service account with domain-wide delegation — is **Workspace-only**: DWD authorization requires a Workspace super admin and impersonation only works against managed Workspace users. Personal `@gmail.com` accounts cannot use this path. See [Workspace plans + personal accounts: what's different](#workspace-plans--personal-accounts-whats-different) in Part 1.

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
- For Office documents specifically: upload-with-conversion via [`files.create`](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create) with a target `mimeType` (`application/vnd.google-apps.document` for `.docx`, `application/vnd.google-apps.spreadsheet` for `.xlsx`, `application/vnd.google-apps.presentation` for `.pptx` — see [Google's MIME type list](https://developers.google.com/workspace/drive/api/guides/mime-types)). The result is a native Doc/Sheet/Slide that `readDocument` works on. The original Office file stays untouched. Some MCP servers wrap this conversion under a `copyFile` tool name; some require a separate upload step.
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

**A specific failure mode worth naming:** "unstyled" does not mean "markdown source as the doc body." Cloud helpers that deliberately skip the styling pass (because brand cascade requires the MCP, which the cloud env doesn't have) sometimes prepend raw markdown via `insertText` and label the result "intentionally unstyled, will be re-styled by the next interactive run." That's wrong twice. First, the markdown tokens (`#`, `**`, `-`) land as literal characters and stay there until the interactive run re-styles — readers in the meantime see `**Format:**` as `**Format:**`, not as bold. Second, the interactive re-style runs `applyTextStyle` on the existing body, which won't convert markdown tokens to formatting; it'll just bold the literal `**` characters. The cloud helper must either skip the prepend until interactive is available, or assemble the full body and use the HTML-import path (which produces real styled content even without MCP).

### Anti-pattern 4 — Deleting human content during a reformat

The bright line is **information loss**, not formatting. Reformatting (P1 → bullets, header level changes, italic → bold) is fine. **Deleting, paraphrasing, or silently dropping content** — including pasted images, smart chips, comments, attachments, and typed prose — is not.

The failure mode: an agent runs `replaceRangeWithMarkdown` over a range that includes a pasted image. The reformat is correct; the image silently disappears. The image is gone from the doc and the original is gone from the agent's context. No recovery.

**Before any `replaceRangeWithMarkdown`, `deleteRange`, or `replaceDocumentWithMarkdown` that touches existing content:** read the JSON for the affected range and scan for:

- `inlineObjectElement` (pasted images, embedded files)
- `richLink` (linked Drive files rendered inline)
- `person` (smart chips for people)
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
  pre_state.json   # getDocumentInfo before the write — required for update mode; optional for prepend when content is assembled offline
  post_state.json  # getDocumentInfo after the write + cascade check
  log.txt          # one line per tool call: timestamp, tool, duration, ok/fail
  error.txt        # only on failure; full error payload
```

The log path makes silent failures debuggable later. Without it, "the doc looked wrong yesterday" is a question with no answer. With it, the post-write JSON sits on disk forever.

### Single writer per doc — and verifiers don't write either

The single-writer pattern is "one specialized subagent owns all writes." Extend that rule one step further: **validator / linter / drift-detector agents that find brand-styling issues must NOT also write the fix**. They should dispatch the writer.

The risk is concurrency. If a validator has `applyTextStyle` in its tools allowlist and runs alongside the writer, both think they own the cascade-check state for the same doc. Both write. The second write doesn't know about the first; cascade and JSON verification race; the final state depends on tool call interleaving rather than either agent's intended outcome. A validator with write tools is a second writer, regardless of how narrowly its prose says it should be used.

The clean shape: validators emit a typed outcome (`ok | drift_detected | flagged`); on `drift_detected`, the orchestrator re-dispatches `drive-doc-writer` with the corrected content. The writer keeps its sole-ownership invariant on cascade-check state. Validators stay read-only.

### Surface ownership — which docs are NOT yours to write

The writer pattern assumes the agent owns the surfaces it writes to. In practice, many Drive docs are **mixed surfaces** — humans curate the body, an agent prepends a dated section, and a separate process synthesizes the meeting afterward. Agents reflexively want to "summarize the call" or "consolidate the notes" into the same doc they prepended into. Both impulses produce information loss (Anti-pattern 4).

The discipline: every Drive-touching skill should explicitly name the surfaces it does and does not own. Examples:

| Skill | Owns | Doesn't own |
|---|---|---|
| Meeting prep | The "upcoming meeting" prep section at the top | The rest of the running-notes doc |
| Post-meeting synthesis | A dated decisions-log entry in a separate file | The meeting-notes prep section at the top of running-notes |
| Brand validator | Read-only; emits drift findings | Every doc body (validators don't write — see above) |

Putting this in the skill's preamble (or in the agent's tools allowlist) prevents the reflexive "I see a doc I just touched; let me summarize what happened" failure mode. The right answer is almost always: a different file, owned by a different skill.

### Concurrency cap on writer fan-out

When an orchestrator dispatches N parallel jobs that each fan out to M specialists (including the writer), the total in-flight agent count is N × M. The Google Workspace MCP has a soft concurrency tolerance — typically four to six simultaneous writes before quota errors and 5xx responses start cascading. Cap the parent dispatches so total in-flight writes stay under the tolerance. A reasonable starting point: cap parent jobs to four when each spawns a writer.

### Cloud / interactive write parity — discriminated-union return states

When a single logical write can land via two paths — the MCP locally on a developer machine, or a stdlib helper / proxy in cloud — the typed return must distinguish them. A successful cloud write that produced an unstyled body is *not* the same as a successful interactive write with brand cascade applied; calling both `updated` hides the gap.

The robust shape extends the discriminated union:

```ts
type DriveDocWriterResult =
  | { type: "created"; doc_id: string; url: string; styled: true }
  | { type: "updated"; doc_id: string; url: string; sections_added: number; styled: true }
  | { type: "created_pending_interactive"; doc_id: string; url: string; pending: ("brand_cascade" | "watson_weekly_logo" | "watson_weekly_footer")[] }
  | { type: "updated_pending_interactive"; doc_id: string; url: string; pending: string[] }
  | { type: "skipped_idempotent"; doc_id: string; url: string; reason: "already_current" }
  | { type: "failed"; reason: string; message: string };
```

The `*_pending_interactive` variants carry an explicit list of what didn't run. A later interactive run can dispatch on that list and only do the missing work, instead of re-running the full styling pass blindly.

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

## Part 7 — Operating Google Sheets

Sheets is structurally different from Docs and the patterns reflect it. A Docs document is a tree of paragraphs with index-based addressing; a Sheets spreadsheet is a collection of 2D grids addressed by row/column. The same MCP server typically exposes both, but the failure modes don't transfer. This part covers what's unique to Sheets.

### The mental model — two endpoint families, one spreadsheet

Per Google's [Sheets API concepts](https://developers.google.com/sheets/api/guides/concepts), a Spreadsheet contains an array of Sheet resources, each a 2D grid of Cells keyed by row and column index (not stable IDs). The API splits into two surface families and **mixing them is the #1 mental-model error**:

- **`spreadsheets.values.*`** — read/write **cell content only** (strings, numbers, formulas). Endpoints: `get`, `update`, `append`, `clear`, `batchGet`, `batchUpdate`, `batchClear`.
- **`spreadsheets.batchUpdate`** — read/write **structure** (sheets, formatting, charts, conditional rules, named/protected ranges, dimensions, data validation). Omnibus endpoint accepting a list of typed `Request` objects. See [Google's batchUpdate guide](https://developers.google.com/sheets/api/guides/batchupdate).

Touching cell values → `values.*`. Touching anything visual or structural → `spreadsheets.batchUpdate`. Code that mixes these reveals an author who hasn't internalized the model.

### Range notation — A1 vs GridRange

Two parallel addressing schemes coexist:

- **A1 notation** for `values.*`: `Sheet1!A1:B2`, `'Class Data'!A2:A4`. Sheet names with spaces or special characters **must** be single-quoted.
- **GridRange** for structural requests: `{sheetId, startRowIndex, endRowIndex, startColumnIndex, endColumnIndex}`. Per the [GridRange reference](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#GridRange), "All indexes are zero-based. Indexes are half open, i.e. the start index is inclusive and the end index is exclusive — `[startIndex, endIndex)`. Missing indexes indicate the range is unbounded on that side."

`endRowIndex: 5` means rows 0–4 inclusive, equivalent to A1 `A1:A5`. Off-by-one between the two systems is the most common bug in Sheets automation. The `"Unable to parse range"` 400 response — the single most-reported Sheets API error — is almost always one of: a sheet renamed since the config was written, missing single quotes around a name with a space, or a tab that was deleted.

### Sheets — where to spend your time

| # | Pattern | Why it matters | Effort |
|---|---|---|---|
| S1 | **`valueInputOption=USER_ENTERED` for almost every write** | The single most-common Sheets API mistake: writing `=SUM(A1:A10)` with `RAW` lands the literal string starting with `=` in the cell. USER_ENTERED parses input the way the UI does — formulas become formulas, `Mar 1 2026` becomes a date. | Low |
| S2 | **Set the `fields` mask on every `UpdateCellsRequest`** | Omitting `fields` or passing `"*"` silently wipes cell properties you didn't intend to touch. The narrowest path beats the broadest. | Low |
| S3 | **Collapse N writes into one `batchUpdate`** | Per-user quota is 60 requests/min ([Sheets API limits](https://developers.google.com/sheets/api/limits)). A loop of `values.update` calls burns 60 quota units for what a single `values.batchUpdate` costs as one. | Low |
| S4 | **Pin `valueRenderOption=UNFORMATTED_VALUE` for any compute path** | Default `FORMATTED_VALUE` returns locale-rendered strings. Read → math → write-back round-trips can silently mangle commas, decimals, and dates if you don't pin the render mode. | Low |
| S5 | **Use developer metadata to anchor sheet position** | Hardcoded `Sheet1!A1:Z1000` ranges break the moment a tab is renamed or rows extend past row 1000. [Developer metadata](https://developers.google.com/sheets/api/guides/metadata) tags survive renames and reorders. | Medium |

### Pattern S1 — USER_ENTERED is the load-bearing default

Per the [values guide](https://developers.google.com/sheets/api/guides/values):

> `RAW`: "The input is not parsed and is inserted as a string. For example, the input `=1+2` places the string, not the formula, `=1+2` in the cell."
>
> `USER_ENTERED`: "The input is parsed exactly as if it were entered into the Sheets UI. For example, `Mar 1 2016` becomes a date, and `=1+2` becomes a formula."

The default in most clients is `INPUT_VALUE_OPTION_UNSPECIFIED`, which defaults server-side to a stricter mode and produces the literal-string failure mode. **Always pass `USER_ENTERED` explicitly** unless the input is genuinely a string that begins with `=` and you want it preserved that way.

The corresponding read-side companion is `valueRenderOption`. Three values:

- `FORMATTED_VALUE` (default) — locale-rendered strings. Good for display, bad for computation.
- `UNFORMATTED_VALUE` — typed values. The compute-path default.
- `FORMULA` — the formula source as a string. Use for round-tripping or auditing.

If your code reads with `FORMATTED_VALUE`, does math on the result, and writes back, you've already round-tripped through the user's locale at least once. The math may be wrong before it ever reaches the cell.

### Pattern S2 — Date handling: the 1899-12-30 epoch

Sheets stores dates as serial numbers using the **Lotus 1-2-3 epoch of December 30, 1899** (whole part = days since, fraction = time of day). Per the [formats guide](https://developers.google.com/sheets/api/guides/formats), reads default to `dateTimeRenderOption=SERIAL_NUMBER` unless `valueRenderOption=FORMATTED_VALUE` (which overrides). Sheets correctly treats 1900 as a non-leap year, unlike Excel's leap-year bug.

Rendered output depends on the spreadsheet's `properties.timeZone` and `properties.locale`, both writable via `UpdateSpreadsheetPropertiesRequest`. A date round-tripped through USER_ENTERED can land as a serial number that's visible to formulas but invisible to a downstream string-compare. Always pin `valueRenderOption` explicitly when dates are in play.

### Pattern S3 — Batch every structural write

`spreadsheets.batchUpdate` accepts a list of typed `Request` objects in one round trip and is atomic per the [batchUpdate guide](https://developers.google.com/sheets/api/guides/batchupdate): "if one request is unsuccessful, none of the other (potentially dependent) changes are written."

Combine that with the quota math (60 req/min/user, 300 req/min/project) and the rule writes itself: every multi-step structural change must be one `batchUpdate` call. A loop of single-request calls burns quota and creates partial-failure recovery problems that the atomic batch wouldn't have.

### Pattern S4 — Developer metadata for stable anchors

The durable answer to "the sheet keeps moving and my pipeline breaks." [`AddDeveloperMetadataRequest`](https://developers.google.com/sheets/api/guides/metadata) tags rows, columns, sheets, or the spreadsheet itself with key/value metadata that survives renames and reorders. Read back via `batchGetByDataFilter` with a `DataFilter` that matches the metadata key.

The pattern: tag the header row of a data range with `key: "primary_data"` once at setup. Every subsequent read filters by that key. The tab can be renamed, the sheet reordered, rows can be inserted above — the metadata anchor survives all of it.

### Sheets hard limits the API does not support

**Limit S1 — No `CellImage` (blob) inserts via the API.** The Sheets API can write `IMAGE()` formula URLs through USER_ENTERED, but uploaded image blobs anchored to specific cells require Apps Script's [`SpreadsheetApp.newCellImage()`](https://developers.google.com/apps-script/reference/spreadsheet/cell-image). `IMAGE()` also won't load from `drive.google.com` URLs and won't render SVG.

**Limit S2 — No partial pivot table edits.** Editing an existing pivot table requires writing the entire `pivotTable` field again via `UpdateCellsRequest`. There is no fields-mask path to update just the rows or columns of a pivot. Plan pivot writes as full replaces.

**Limit S3 — No full chart styling.** Per Google's [charts samples](https://developers.google.com/sheets/api/samples/charts): "The Sheets API doesn't yet grant full control of charts… some chart types and certain chart settings (such as background color or axis label formatting) can't be accessed or selected with the current API." The supported subset (column, bar, line, pie, scatter, area, combo) covers most cases but the styling ceiling is real.

**Limit S4 — No revision-locked concurrency.** There is no `If-Match` / ETag concurrency control on Sheets writes. Parallel `append` calls or an `append` fired immediately after a `DeleteDimensionRequest` exhibit real race conditions ([Google Dev forum thread](https://discuss.google.dev/t/row-offsets-occur-when-append-requests-run-immediately-after-deletedimension-suggesting-the-delete-isn-t-fully-applied-yet/345218)) where the append lands at the pre-delete row index. Serialize dependent writes within a single batch.

**Limit S5 — 10 million cell ceiling per spreadsheet** (20M in the [2026 beta](https://workspaceupdates.googleblog.com/2026/04/faster-performance-and-doubled-cell-limits-in-Google-Sheets.html) for opted-in Workspace orgs). The limit counts across all tabs. `batchUpdate` returns `INVALID_ARGUMENT` once exceeded; no soft-deny. Plan for sharding into multiple spreadsheets before you approach the ceiling.

**Limit S6 — No triggers, custom menus, or sidebar UI.** These are Apps Script territory only. If your automation needs to fire on cell edit, schedule on a time-driven trigger, or render a sidebar UI, the API is the wrong surface. Apps Script reaches the same Sheets and adds the UI/trigger layer the API doesn't.

### Sheets anti-patterns

**A-S1 — Writing formulas with `valueInputOption=RAW`.** Covered in Pattern S1. The most-common Sheets API mistake; spot it in code review by looking for any formula string written without an explicit USER_ENTERED flag.

**A-S2 — Hardcoded `Sheet1!A1:Z1000` ranges.** Brittle. Every rename, reorder, or row-extension breaks the pipeline. Use developer metadata (Pattern S5) or named ranges instead.

**A-S3 — Looping `values.update` calls.** N quota units for what one `values.batchUpdate` costs as one. Always collapse.

**A-S4 — Omitting the `fields` mask on `UpdateCellsRequest`.** Silently wipes cell properties you didn't intend to touch. The mask should be the narrowest path that covers what you're writing.

**A-S5 — Reading FORMATTED_VALUE, doing math, writing back.** Locale round-trip mangle. Pin `UNFORMATTED_VALUE` for compute paths.

**A-S6 — `values.append` with INSERT_ROWS into a table that has a totals row below it.** Append's "table" detection uses contiguous non-empty cells, but it pushes the totals row down forever with INSERT_ROWS — or splats over data with OVERWRITE. For sheets with structural rows below the data, append is the wrong shape; explicit `UpdateCellsRequest` is.

### Apps Script vs Sheets API — where the line falls

The two surfaces overlap significantly but each has things the other can't do. From [Tanaike's benchmarks](https://tanaikech.github.io/2018/10/12/benchmark-reading-and-writing-spreadsheet-using-google-apps-script/), the Sheets API beats Apps Script's `SpreadsheetApp` for large ranges (~35% read, ~19% write savings), but `setValues()` wins on small ranges with many columns (crossover near 75 columns).

| Surface | Strengths | Limits |
|---|---|---|
| Sheets API | Bulk `batchUpdate`, server-side scheduling outside Google quotas, OAuth-token-scoped programmatic access | No triggers, no UI (menus / sidebars), no `CellImage` blob inserts, no custom functions |
| Apps Script | Triggers (`onEdit`, `onChange`, time-driven), custom menus and sidebars, `CellImage` blob inserts, custom functions, live access inside the editor session | Slower at bulk; runs inside Google's Apps Script quotas; awkward outside Google Workspace itself |

Most production automations land somewhere on the spectrum. The decision rule: if the workflow needs to fire on a cell edit or render a UI inside Sheets, Apps Script. If the workflow needs bulk write throughput or external orchestration, Sheets API. Mixed setups are normal — an Apps Script `onEdit` trigger that calls out to an external service which talks to the Sheets API for the heavy lift.

---

## Part 8 — Operating Google Slides

Slides is the third Workspace surface and the most under-served by production MCP tooling. The mental model is different from both Docs and Sheets; the failure modes are different; the API surface is different.

### The mental model — one batch endpoint, object-ID addressing

A presentation is a tree: **Presentation → Page → PageElement**. Four page types (Slide, Master, Layout, Notes); page elements are Shape, Table, Image, Video, Line, WordArt, SheetsChart, or Group. Style inheritance flows up: slide ← layout ← master. Per the [Slides API overview](https://developers.google.com/workspace/slides/api/guides/overview), all mutation goes through one endpoint — `presentations.batchUpdate` — which accepts a list of typed `Request` objects and applies them atomically.

Slides addressing is **string `objectId` per element**. Unlike Docs (start/end indices into a flat document) and unlike Sheets (`A1` ranges or `GridRange`), every page and page element has an explicit ID.

> **The #1 Slides gotcha — object IDs are not stable.** Per Google's own docs: *"you cannot depend on an object ID being unchanged after a presentation is changed in the Slides UI."* If a human opens the deck in the Slides editor between your batch writes, your saved object IDs may not match anymore. The discovery patterns that survive: persist the **text content** of a shape (find shapes whose text contains "Title — {{date}}") or the **alt-text** (find shapes whose alt-text is `"primary_chart"`), and re-resolve to the current object ID before each batch.

### Slides — where to spend your time

| # | Pattern | Why it matters | Effort |
|---|---|---|---|
| L1 | **Pre-assign your own `objectId` at create time, persist content/alt-text as the lookup key** | Solves the round-trip-instability problem. Every `Create*Request` accepts an optional `objectId`. Generate stable IDs and look up by text/alt-text on each subsequent batch. | Low |
| L2 | **Always pair `InsertText` with a preceding `DeleteText` against placeholder shapes** | Layout-inherited placeholders ship with prompt text ("Click to add title"). InsertText at index 0 prepends; you end up with `Click to add titleMy Real Title`. | Low |
| L3 | **Bundle every related mutation into one `batchUpdate` (atomic) — never one-request-per-mutation** | Write quota is 600/min/project, 60/min/user. 50–200 requests in one batch is the documented norm and atomicity prevents half-applied decks. | Low |
| L4 | **Always set `fields` mask on `Update*Request`** | Same rule as Sheets and Docs. Omitting the mask or passing `"*"` resets every property in the message to its default — silently wiping styling you didn't intend to touch. | Low |
| L5 | **For template-driven decks, copy the template via Drive `files.copy`, then `ReplaceAllText` into the copy** | Google's explicit instruction: *"make a copy and use the Slides API to manipulate the copy. Don't use the Slides API to manipulate your primary 'template' copy!"* | Medium |

### What's possible — Slides headline capabilities

| You want to... | Request | Notes |
|---|---|---|
| Create a presentation | `presentations.create` | Returns the empty presentation with a single blank slide |
| Add a slide from a layout | `CreateSlideRequest` + `placeholderIdMappings` | Pre-assign IDs to inherited placeholders so subsequent `InsertText` calls have stable targets |
| Insert text into a shape | `InsertTextRequest` with `objectId` + `insertionIndex` | For table cells: also pass `cellLocation: {rowIndex, columnIndex}` |
| Style text | `UpdateTextStyleRequest` with `Range` (`ALL` / `FIXED_RANGE` / `FROM_START_INDEX`) | `fields` mask required |
| Insert an image | `CreateImageRequest` with public URL + `elementProperties` (size + transform) | URL must be publicly accessible at request time; max 50 MB, 25 megapixels; PNG/JPEG/GIF only |
| Embed a Sheets chart | `CreateSheetsChartRequest` with `spreadsheetId`, `chartId`, `linkingMode: LINKED` | Refresh requires manual `RefreshSheetsChartRequest`; no auto-update |
| Read/write speaker notes | `InsertText` against `slide.slideProperties.notesPage.notesProperties.speakerNotesObjectId` | Only text content is editable; formatting is not |
| Duplicate a slide or element | `DuplicateObjectRequest` | New IDs assigned automatically; transform stays the same |
| Reorder slides | `UpdateSlidesPositionRequest` | |
| Tag-substitution across the deck | `ReplaceAllTextRequest` with `containsText` | Inherits formatting from the first character of the matched range — see anti-pattern below |
| Generate slide thumbnail | `presentations.pages.getThumbnail` | Expensive read; rate-limited |

### What's NOT possible — and the workaround (Slides)

| Hard limit | Workaround |
|---|---|
| **Slide transitions** (fade, slide, dissolve) | None via API. Apply in editor UI; survives `DuplicateObject`. [Open issue tracker entry since 2016](https://issuetracker.google.com/issues/36761236). |
| **Element animations / builds** (entrance, exit, motion path) | Same — editor only. Cannot author programmatically. |
| **Notes formatting beyond plain text** | Notes shape accepts text body only; bold/italic/color/font in notes are not editable via API. Generate as plain text. |
| **Notes master and handout master edits** | Read-only via API. Build in editor; survives template clones. |
| **Listing presentations in a folder** | Slides API has no `list`. Use Drive `files.list` with `mimeType = "application/vnd.google-apps.presentation"`. |
| **Inserting private Drive images** | Make the file public for ~30s during the request, OR mint a GCS signed URL (15-min lifetime), OR upload-then-share via Drive API. Per [the open issue](https://github.com/googleapis/google-api-python-client/issues/2215), Slides cannot fetch private Drive content even with full Drive + Slides OAuth scopes. |
| **Auto-refresh linked Sheets chart** | Manual `RefreshSheetsChartRequest` per chart per refresh; nothing auto-fires when the source Sheet changes. |
| **Restyling during `ReplaceAllText`** | The replace inherits formatting from the first character of the matched range. Follow with `UpdateTextStyleRequest` over the resulting range to restyle. |
| **Custom slide backgrounds beyond color or stretched-picture fill** | `UpdatePageProperties` is limited; crop/position control for background images is missing. Use a full-bleed `CreateImageRequest` sized to the page as a workaround. |
| **Text effects** (shadow, glow, reflection) | Not in `TextStyle`. Apps Script `SlidesApp` exposes some; otherwise apply in the editor. |
| **Auto-fit / shrink-to-fit measurement** | Cannot read the rendered text size via API. Pre-measure client-side or use Apps Script. |
| **Table column width / row height edits** | Long-standing gap in `SlidesApp` per [Tanaike, 2023](https://tanaikech.github.io/2023/07/01/managing-row-height-and-column-width-of-table-on-google-slides-using-google-apps-script/); REST API supports `UpdateTableColumnPropertiesRequest`. Use the REST API path. |

### Production MCP coverage for Slides is shallow

This matters and deserves to be named explicitly. As of mid-2026:

- The production Google Workspace MCP servers (taylorwilsdon/google_workspace_mcp, matteoantoci/google-slides-mcp) expose ~7 Slides tools — `create_presentation`, `get_presentation`, `batch_update_presentation`, `get_page`, `get_page_thumbnail`, `list_presentation_comments`, `manage_presentation_comment`.
- Compare to Docs (~14 tools, fine-grained: `insertText`, `applyTextStyle`, `applyParagraphStyle`, `insertImage`, `replaceDocumentWithMarkdown`, etc.) and Sheets (~13 tools, equally fine-grained).
- The Slides MCP path funnels every mutation through `batch_update_presentation`, so the agent ends up authoring raw `Request` JSON. There is no `insertImage`-style convenience tool, no `applyTextStyle`, no `replaceAllText` shortcut.

**Practical implication:** building decks from an agent today means either (a) authoring raw `presentations.batchUpdate` payloads directly, or (b) writing a thin local helper that exposes higher-level operations (create slide with layout, insert text into placeholder, etc.) on top of the REST API. The latter is the right shape for any operator who builds more than a handful of decks programmatically.

### Slides anti-patterns

**A-L1 — Trusting object IDs after a human edits the deck.** Once the editor touches the file, your stored IDs may be stale. Cover by re-resolving via text content or alt-text on each batch.

**A-L2 — `InsertText` at index 0 of a placeholder without first `DeleteText`.** Placeholder prompt text ("Click to add title") stays in the cell. The resulting slide reads `Click to add titleYour Real Content`. Pair every InsertText against a placeholder with a preceding DeleteText.

**A-L3 — Calling `ReplaceAllText` and expecting it to restyle.** ReplaceAllText changes the text only; formatting carries from the first character of the matched range. For a redesign, always follow with `UpdateTextStyleRequest`.

**A-L4 — Posting one-request-per-mutation.** Quota is per-project (600/min) and per-user (60/min). Bundle 50–200 requests in a single `batchUpdate`; atomic semantics prevent partial-failure mess.

**A-L5 — Using the Slides API to manipulate your "template" copy.** Google's explicit warning. Always `files.copy` the template into a working folder first, then mutate the copy. The template stays clean and reusable.

**A-L6 — Passing `*` as the `fields` mask on Update requests.** Resets every property in the message to its default, silently wiping styling. Use the narrowest path that covers what you're writing.

### Apps Script vs Slides API — where the line falls

The same overlap as Sheets, with one structural difference: **production MCP coverage for Slides is so thin that for any non-trivial deck automation, the REST API is the only path** — Apps Script becomes the fallback for things the REST API genuinely cannot do.

| Only Apps Script (`SlidesApp`) | Only REST API | Both |
|---|---|---|
| Custom menus, sidebars, on-open triggers | True batch atomicity across 100s of mutations | Create / duplicate slides |
| Simple imperative text styling (`setFontSize`, `setForegroundColor`) | Service-account auth, headless long-running jobs | Insert / delete text, shapes, images, tables |
| Direct iteration over slide elements without rebuilding the objectId graph | High-throughput template generation | Speaker notes text |
| User-bound auth out of the box | Field-masked partial property updates | `ReplaceAllText`, chart embed, `DuplicateObject` |
| Some text effects (shadow / glow / reflection) | Per-row column-width control on tables | Sheets-chart refresh |

---

## What we still don't know

1. **Whether and when Google will ship API support for creating PAGE_NUMBER auto-text in existing docs.** The limitation has been around for years; the workaround (template + `copyFile`) is stable, but a future API change would make a lot of footer-related code obsolete. Watch the Google Docs API changelog.

2. **Whether Anthropic ships an org-level Workspace MCP for writer-side ops.** The current connector is read-heavy and primarily user-facing. A writer-side org-level connector would remove the need for the stdlib helper / cloud-secret-proxy stack documented in Limit 2. Until it lands, the workaround is real cost.

3. **Whether `replaceDocumentWithMarkdown` will stabilize on metadata-row formatting.** The current consecutive-`**Label:**` collapse is a quirk of the markdown converter, not a deliberate behavior. A future MCP release may fix it; until then, the source-side rule (blank line between every `**Label:**` row) is the durable defense.

4. **Whether the cascade-style failure modes will reduce as MCP servers mature.** Both excess cascade and namedStyleType strip are interactions between the markdown converter and the doc's named styles. As the converter gets smarter, the regressions may become rarer. Keep cascade-check as a defense regardless — the cost is one extra `getDocumentInfo` per write, and the failure modes are too expensive to leave undefended.

5. **Whether Google ships revision-locked concurrency for Sheets writes.** No If-Match / ETag mechanism exists today; concurrent `append` calls and append-after-deleteDimension races are real. A future API change would let serialized pipelines run truly parallel. Until then, the workaround is to keep dependent writes inside a single `batchUpdate` call.

6. **Whether the Sheets API will expose `CellImage` blob inserts.** Today only Apps Script can anchor uploaded image blobs to specific cells; the API can only write `IMAGE()` formula URLs (which won't accept Drive-hosted URLs and won't render SVG). The asymmetry is annoying for any automation that wants to embed generated images in a Sheets dashboard.

7. **Whether production MCP servers will close the Slides coverage gap.** Today Slides exposes ~7 tools versus Docs' ~80 and Sheets' ~20 in the canonical Google Workspace MCP. Building decks programmatically means authoring raw `presentations.batchUpdate` payloads — slower iteration than the Docs/Sheets surfaces. A future MCP release with fine-grained Slides tools (`insertText`, `applyTextStyle`, `replaceAllText` as first-class tools) would close the gap.

8. **Whether Slides will ship API support for transitions, animations, and private-Drive image insertion.** All three are [tracked as open issues](https://issuetracker.google.com/issues/36761236), some since 2016. The workarounds (apply transitions in the editor, mint public URLs for images) are durable; an API change would obsolete a real chunk of deck-automation code.

---

## Machine-readable identity (this article's own schema)

This article applies the [Marketing to Agents](marketing-to-agents.md) playbook to itself — JSON-LD `Article` schema is auto-emitted in `<head>` by the repository's Jekyll `_includes/head-custom.html` whenever a guide carries `agent_friendly: true` in its frontmatter (this one does). Agents indexing the rendered HTML at [watsonrm.github.io/rmwcommerce](https://watsonrm.github.io/rmwcommerce/guides/operating-google-workspace-from-claude.html) see a typed `Article` with author `sameAs` references to Rick's LinkedIn, X, GitHub, and Watson Weekly profiles; publisher `Organization` is RMW Commerce Consulting; license is CC BY-NC-ND 4.0. Agents fetching the raw markdown see the equivalent metadata in the YAML frontmatter at the top of this file.

---

## Sources & Attribution

This guide synthesizes patterns and failure modes from running Google Drive + Docs automation in production through 2025–2026. The source taxonomy applied throughout: **failure mode > workaround > pattern**. Every limitation has a documented failure that produced it, and every pattern has a workaround it replaces.

### Anthropic / Model Context Protocol

- [Model Context Protocol specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25) — the protocol every MCP server implements; covers connector model and JSON-Schema tool inputs/outputs
- [MCP server registry / community list](https://github.com/modelcontextprotocol/servers) — production MCP servers; the Google Drive server is now in `servers-archived`
- [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) — the production-grade Google Workspace MCP referenced throughout this article (~2.5k stars, MIT, OAuth 2.1, actively maintained)
- [Claude Agent SDK — Subagents reference](https://code.claude.com/docs/en/agent-sdk/subagents) — authoritative for Claude Code subagent semantics; the basis for the single-writer pattern in Part 5
- [How Anthropic built its multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system) — orchestrator-worker pattern and typed-return-contract design that the `DriveDocWriterResult` discriminated union implements

### Google Workspace APIs

- [Google Docs API reference](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents) — Document resource JSON schema; the structure inspected during verification
- [Google Drive API v3 reference](https://developers.google.com/workspace/drive/api/reference/rest/v3) — file-level operations (copy, create, list, search)
- [Document structure concepts](https://developers.google.com/workspace/docs/api/concepts/structure) — body → StructuralElement → Paragraph → ParagraphElement → TextRun model; the index/coordinate system
- [batchUpdate reference](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/batchUpdate) — full catalog of update request types (the underlying calls MCP tools wrap)
- [Format text in a Google Doc](https://developers.google.com/workspace/docs/api/how-tos/format-text) — official how-to covering `namedStyleType` values, inheritance, and `updateTextStyle` fields-mask semantics
- [TextStyle reference (JavaDoc)](https://googleapis.dev/java/google-api-services-docs/latest/com/google/api/services/docs/v1/model/TextStyle.html) — confirms the `bold` + `weightedFontFamily` interaction documented in Pattern 2's "weight 400 even when bold: true" failure mode
- [Extract text from a Google Doc](https://developers.google.com/workspace/docs/api/samples/extract-text) — canonical `body.content` walking pattern
- [Output document contents as JSON](https://developers.google.com/workspace/docs/api/samples/output-json) — the JSON-read habit baseline; supports the verification pattern
- [Google Docs API release notes](https://developers.google.com/workspace/docs/api/release-notes) — where to watch for changes that would obsolete the workarounds in Part 3
- [Insert inline images how-to](https://developers.google.com/workspace/docs/api/how-tos/images) — confirms `objectSize` is optional with no guaranteed enforcement
- [Drive files.copy reference](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/copy) — the underlying call behind the template-copy footer workaround
- [Drive files.create reference](https://developers.google.com/workspace/drive/api/reference/rest/v3/files/create) — the upload-with-conversion path for `.docx` / `.xlsx` / `.pptx`
- [Google Workspace and Drive MIME types](https://developers.google.com/workspace/drive/api/guides/mime-types) — canonical list of `application/vnd.google-apps.*` strings for conversion targets
- [Export MIME types for Google Workspace documents](https://developers.google.com/workspace/drive/api/guides/ref-export-formats) — the reverse direction (Doc → `.docx` / `.pdf` etc.)

### Documented limitations

- [Google issue tracker #162801033](https://issuetracker.google.com/issues/162801033) — PAGE_NUMBER / PAGE_COUNT auto-text limitation referenced in Limit 1 (sign-in required to read the issue body)
- [Community thread on footer page-numbering workaround](https://community.latenode.com/t/how-to-add-footer-page-numbering-in-google-docs-via-api-using-php/38578) — independent confirmation of the auto-text limit and the template-copy workaround
- [batchUpdate request type catalog](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/request) — the absence of any `CreateAutoTextRequest` is the structural evidence for Limit 1
- [Limitations for inserting images to Google Docs (Tanaike)](https://tanaikech.github.io/2019/04/05/limitations-for-inserting-images-to-google-docs/) — Kanshi Tanaike's primary-ish reference on the `objectSize` and area-limit constraints documented in Pattern 3 and Limit 3
- [NamedStyles model reference (JavaDoc)](https://googleapis.dev/java/google-api-services-docs/latest/com/google/api/services/docs/v1/model/NamedStyles.html) — confirms `UpdateNamedStylesRequest` does not exist, the structural evidence for Limit 4
- [anthropics/claude-code#53442](https://github.com/anthropics/claude-code/issues/53442) — Cowork Shared Drive access regression referenced in the connector parity section

### Authentication & credentials

- [Choose Google Drive API scopes](https://developers.google.com/workspace/drive/api/guides/api-specific-auth) — the canonical scope guide; defines `drive` vs `drive.file` vs `drive.readonly` exactly
- [OAuth 2.0 scopes for Google APIs](https://developers.google.com/identity/protocols/oauth2/scopes) — full scopes catalog
- [Google OAuth 2.0 for installed applications](https://developers.google.com/identity/protocols/oauth2/native-app) — the consent flow used by every MCP-installed helper
- [Google Cloud Secret Manager](https://cloud.google.com/secret-manager/docs) — the canonical place for credentials in the cloud-secret-proxy pattern
- [Restricted-scope OAuth verification (CASA assessment)](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification) — the verification gate external apps hit when requesting the broad `drive` scope
- [Control which apps access Workspace data (Admin Help)](https://support.google.com/a/answer/7281227) — how Workspace admins block / allow / restrict third-party app API access org-wide
- [Domain-wide delegation (Admin Help)](https://support.google.com/a/answer/162106) — how to authorize a service account to impersonate Workspace users

### Workspace plan / account-type references

- [Shared Drives now on Business Starter (Workspace Updates, Aug 2024)](https://workspaceupdates.googleblog.com/2024/08/shared-drive-access-business-starter.html) — the rollout that changed Shared Drives from "Business Standard+" to "every paid edition"
- [Context-Aware Access (Admin Help)](https://support.google.com/a/answer/9275380) — which plans get it and what it controls
- [Create classification labels (Admin Help)](https://support.google.com/a/answer/13127870) — Drive labels by plan tier
- [Audit logs for API-based actions (Workspace Updates, May 2024)](https://workspaceupdates.googleblog.com/2024/05/audit-logs-for-API-based-actions.html) — when admin audit logs started covering API writes
- [Google Vault product page](https://workspace.google.com/products/vault/) — Vault availability by edition
- [Tabs in Google Docs (Workspace Updates, Oct 2024)](https://workspaceupdates.googleblog.com/2024/10/tabs-in-google-docs.html) — confirms tabs rolled out to all account types (Workspace + personal)

### Markdown ↔ Docs conversion

- [CommonMark specification](https://commonmark.org/) — the markdown variant most MCP servers implement against
- [Import and export Markdown in Google Docs](https://workspaceupdates.googleblog.com/2024/07/import-and-export-markdown-in-google-docs.html) — Google's official July 2024 announcement; what `replaceDocumentWithMarkdown` ultimately wraps

### Google Sheets — primary references

- [Sheets API concepts](https://developers.google.com/sheets/api/guides/concepts) — the data model: Spreadsheet → Sheet → Cell; A1 vs R1C1 notation
- [Sheets API values guide](https://developers.google.com/sheets/api/guides/values) — `valueInputOption` (RAW vs USER_ENTERED), `valueRenderOption`, `dateTimeRenderOption`, `majorDimension`
- [Sheets API batchUpdate guide](https://developers.google.com/sheets/api/guides/batchupdate) — the structural request catalog and the atomicity statement
- [GridRange reference](https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets/other#GridRange) — exact "zero-based, half-open" phrasing for structural addressing
- [Sheets API limits](https://developers.google.com/sheets/api/limits) — 60 req/min/user, 300 req/min/project, backoff formula
- [Sheets number and date formats](https://developers.google.com/sheets/api/guides/formats) — the 1899-12-30 epoch and the NumberFormat pattern grammar
- [Sheets developer metadata guide](https://developers.google.com/sheets/api/guides/metadata) — the durable answer to "the sheet moved, my pipeline broke"
- [Faster performance and doubled cell limits in Google Sheets (Apr 2026)](https://workspaceupdates.googleblog.com/2026/04/faster-performance-and-doubled-cell-limits-in-Google-Sheets.html) — the 10M → 20M cell beta
- [Sheets API charts samples](https://developers.google.com/sheets/api/samples/charts) — confirms the chart-styling ceiling referenced in Limit S3
- [Apps Script CellImage class](https://developers.google.com/apps-script/reference/spreadsheet/cell-image) — the only path to blob-image-in-cell inserts (Limit S1)
- [Tanaike: benchmark reading and writing spreadsheet using Google Apps Script](https://tanaikech.github.io/2018/10/12/benchmark-reading-and-writing-spreadsheet-using-google-apps-script/) — the ~75-column crossover between API and `setValues()` for write throughput
- [Google Dev forum: append-after-deleteDimension race condition](https://discuss.google.dev/t/row-offsets-occur-when-append-requests-run-immediately-after-deletedimension-suggesting-the-delete-isn-t-fully-applied-yet/345218) — concrete confirmation of the no-revision-lock concurrency limit

### Google Slides — primary references

- [Slides API overview](https://developers.google.com/workspace/slides/api/guides/overview) — mental model: Presentation → Page → PageElement; the load-bearing warning about object ID instability after editor edits
- [Pages, Page Elements, and Properties](https://developers.google.com/workspace/slides/api/concepts/page-elements) — the four page types (Slide / Master / Layout / Notes) and the style-inheritance chain
- [`presentations.batchUpdate` reference](https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations/batchUpdate) — canonical list of every Request type and the atomicity contract
- [Slides API request reference](https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations/request) — the ~35 typed Request shapes
- [Text Structure and Styling](https://developers.google.com/slides/api/concepts/text) — `TextRange` semantics and the `Range` type values
- [Editing and Styling Text guide](https://developers.google.com/workspace/slides/api/guides/styling) — `fields` mask discipline for text style updates
- [Add images to a slide](https://developers.google.com/workspace/slides/api/guides/add-image) — public-URL requirement, size limits, and the workaround for private Drive images
- [Adding charts to your slides](https://developers.google.com/workspace/slides/api/guides/add-chart) — LINKED vs NOT_LINKED_IMAGE and the manual `RefreshSheetsChartRequest` semantics
- [Merge data into a presentation](https://developers.google.cn/slides/api/guides/merge) — tag-based template substitution via `ReplaceAllText`
- [Work with speaker notes](https://developers.google.com/workspace/slides/api/guides/notes) — `speakerNotesObjectId` discovery and the "text only" limit
- [Slides API usage limits](https://developers.google.com/workspace/slides/api/limits) — 600 writes/min/project, 60 writes/min/user, exponential-backoff guidance
- [Open issue: expose transitions/animations via Slides API](https://issuetracker.google.com/issues/36761236) — the canonical "out of scope" reference (open since 2016)
- [Tanaike — Slides topic index](https://tanaikech.github.io/topics/slides/) — community gotchas by Google Developer Expert Kanshi Tanaike (text manipulation, table column widths, replace-all formatting limits)
- [taylorwilsdon/google_workspace_mcp](https://github.com/taylorwilsdon/google_workspace_mcp) — the production MCP server; Slides exposes ~7 tools (vs ~14 Docs / ~13 Sheets), confirming the under-served MCP-coverage gap

The patterns and anti-patterns documented here emerged from real production failures across 2025–2026. Each was caught the first time by a human, fixed once, and lifted into the writer agent's playbook so it cannot recur silently. The article is the public form of that playbook.
