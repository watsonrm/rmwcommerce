---
title: Operating Google Drive, Docs, Sheets, Slides, Calendar, and Gmail from Claude
description: The patterns, hard limits, and anti-patterns of writing to Google Drive, Docs, Sheets, Slides, Calendar, and Gmail from Claude or any AI agent. Workarounds for what the APIs simply cannot do, plus surface-specific deep dives (Docs styling cascade; Sheets USER_ENTERED + values-vs-structure split; Slides object-ID stability + the under-served MCP surface; Calendar sendUpdates silent-add failure; Gmail base64url vs base64 and the threading-headers gap). Every claim grounded in a specific failure mode.
date: 2026-05-25
last_modified_at: 2026-05-26
author: Rick Watson
agent_friendly: true
keywords: Google Drive, Google Docs, Google Sheets, Google Slides, Google Calendar, Gmail, Sheets API, Slides API, Calendar API, Gmail API, MCP, model context protocol, AI agents, Claude, automation, document automation, OAuth, Drive API, Docs API, valueInputOption, developer metadata, objectId, presentations batchUpdate, applyTextStyle bold lost, tool success not task success, google docs renders wrong, replaceDocumentWithMarkdown styling lost, weightedFontFamily weight 400, silent style failure, sendUpdates default none, base64url Gmail, threading headers In-Reply-To
---

# Operating Google Drive, Docs, Sheets, Slides, Calendar, and Gmail from Claude

**Six Workspace surfaces — Drive, Docs, Sheets, Slides, Calendar, Gmail — are now reachable from Claude as production write targets. Done well, an agent ships a branded doc from a markdown payload, lands formulas as live formulas, builds decks from templates, schedules meetings with working Meet links, and drafts mail a human can review and send in one click. The connective tissue between those wins is the verify-after-write habit: read the JSON, confirm what landed, dispatch the next step against ground truth. This guide names the patterns that produce reliable output on each surface, the workarounds for the things the APIs genuinely cannot do, and the few high-leverage decisions that close the largest share of real-world breakage.**

**Published:** <time datetime="2026-05-25">2026-05-25</time>  ·  **Last updated:** <time datetime="2026-05-26">2026-05-26</time>  ·  **Author:** [Rick Watson](https://www.rmwcommerce.com/), Principal, RMW Commerce Consulting  ·  **Canonical URL:** [`github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-workspace-from-claude.md`](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-workspace-from-claude.md)  ·  **Reading time:** 10-min skim · 75-min deep read

Who this is for: developers and operators using Claude (or any AI agent) to read and write Google Drive files, Google Docs, Google Sheets, Google Slides, Google Calendar events, and Gmail messages at scale. Anyone who wants an agent to produce branded docs, live-formula sheets, template-driven decks, working calendar invites, and reviewable mail — without watching the agent overwrite styled formatting, create four files with the same title, write a formula that lands as a literal string, hand-craft a `batchUpdate` for a deck because the MCP didn't expose it, add attendees silently with no invitation email, or get `400 invalidArgument` from Gmail because standard base64 isn't base64url.

**Jump to:** [60-second map](#the-60-second-map--what-youre-actually-working-with) · [Master priority map](#master-priority-map--highest-leverage-pattern-per-surface) · [What you can do today](#what-you-can-do-today--capability-inventory) · [Hard limits + workarounds](#hard-limits--workarounds) · [TL;DR](#tldr--the-five-highest-leverage-decisions) · [Sheets (Part 7)](#part-7--operating-google-sheets) · [Slides (Part 8)](#part-8--operating-google-slides) · [Calendar (Part 9)](#part-9--operating-google-calendar) · [Gmail (Part 10)](#part-10--operating-gmail) · [Full TOC](#whats-in-this-article)

---

## The 60-second map — what you're actually working with

Six surfaces, six different mental models. The most common production bug is confusing them.

| Surface | What it is | What it's good for | Addressing model |
|---|---|---|---|
| **Drive** | The file system | List, search, copy, move, share, manage permissions. File metadata. **Never content.** | File ID |
| **Docs** | The document editor | Read body, write text, apply styles, insert images, manage comments. | Character index into body |
| **Sheets** | The spreadsheet | Cells, ranges, formulas, formatting, conditional rules, charts. | A1 ranges OR zero-based GridRange |
| **Slides** | The presentation editor | Slides, shapes, tables, images, charts, speaker notes. | String `objectId` per element |
| **Calendar** | The scheduling surface | Events, recurring series, freebusy, ACL sharing, push notifications. | `(calendarId, eventId)` OR `(calendarId, iCalUID)` |
| **Gmail** | The mail surface | Send, draft, label, search, thread, push notifications, filter management. | `messageId` / `threadId` / `labelId` (opaque strings) |

You reach Drive through `mcp__google-docs__searchDriveFiles`, the lighter `mcp__claude_ai_Google_Drive__*` family, or the [Drive REST API v3](https://developers.google.com/workspace/drive/api/reference/rest/v3) directly. Docs (~80 tools) and Sheets (~20 tools) go through `mcp__google-docs__*`. Slides has the shallowest MCP coverage — production servers expose ~7 tools, most agents end up authoring raw `presentations.batchUpdate` payloads. Calendar and Gmail both have MCP coverage in the canonical Google Workspace MCP but production agents regularly need REST for edge cases (sync tokens, push channels, ACL writes, MIME assembly). [Part 1](#part-1--the-toolset-and-the-mental-model) covers connector / scope / write-path trade-offs; [Part 8](#part-8--operating-google-slides) covers the Slides shape; [Part 9](#part-9--operating-google-calendar) covers Calendar; [Part 10](#part-10--operating-gmail) covers Gmail.

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

## Master priority map — highest-leverage pattern per surface

One row per surface. The top pattern on each row is the single decision that closes the largest share of real-world breakage for that surface; the per-Part `Where to spend your time` tables that follow expand items 2 through N. **If you adopt only the six patterns in this table, you ship the bulk of the wins this guide is about.**

| Surface | Highest-leverage pattern | Why this pattern wins |
|---|---|---|
| **Drive** | Search-before-create + `copyFile` from templates for any doc needing footers / page numbers | Idempotent runs reach the same Drive state instead of accumulating duplicates; templates carry the `PAGE_NUMBER` auto-text and footer structure the Docs API genuinely cannot author from scratch |
| **Docs** | Brand-styling sequence: body sweep → cascade check → paragraph styles → heading text styles → inline bold prefixes | The only call order that produces a doc rendering the way the markdown intended; every other order leaves Arial body, missing headings, or overwritten bold runs |
| **Sheets** | `valueInputOption=USER_ENTERED` on writes; `valueRenderOption=UNFORMATTED_VALUE` on compute reads | Formulas land as formulas and dates land as dates; compute paths read typed values instead of locale-rendered strings, eliminating the round-trip mangle |
| **Slides** | Pre-assign your own `objectId` at create time; look up shapes by text content or alt-text on each batch | Object IDs returned by the API are not stable across editor edits per Google's docs; durable lookups need a stable handle the caller controls |
| **Calendar** | Pass `sendUpdates=all` explicitly on every insert / update / delete with attendees | The documented default is `false` (= no notifications fire) per the [insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert); attendees get added silently otherwise — the most common reason an agent-created meeting "never went out" |
| **Gmail** | `drafts.create` for outbound; humans review and send via `drafts.send` | Agent-authored drafts are reviewable and revocable before delivery; the alternative is direct `messages.send`, which puts mail on the wire before any human sees it |

Each per-Part `Where to spend your time` table below expands its surface's row into the full priority stack. Drive does not get its own deep dive Part — Drive operations are folded into the Docs Part because almost every Drive write is in service of a Docs / Sheets / Slides body change.

---

## What you can do today — capability inventory

The capabilities the Workspace APIs deliver at the present production state. Each row pairs the result with the tool that produces it; notes carry the load-bearing flag or option that decides whether the call ships the result or a near-miss.

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

## Hard limits + workarounds

A handful of capabilities the Workspace APIs simply do not expose today. Each row names the workaround that closes the gap. Scan this table before assuming you've found a new bug — most "the API can't do X" reports land on a known limit with a documented path forward.

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

## TL;DR — the five highest-leverage decisions

If you read nothing else, internalize these five. Each leads with the decision that produces the win; the watch-out follows. The five surfaces are deliberately mixed — none of these are obvious from reading Google's docs.

1. **Verify every Docs style write by reading the JSON.** After every `applyTextStyle` / `applyParagraphStyle` call, read the doc as JSON and confirm the values landed per paragraph. The JSON is the contract — tool-call success isn't. Silent partial-success is the single most expensive case to handle in production.
2. **Pass `USER_ENTERED` explicitly on every Sheets write.** Sheets parses input the way the UI does — formulas become formulas, `Mar 1 2026` becomes a date. Without the explicit flag, `=SUM(A1:A10)` lands as a literal string starting with `=` and downstream math reads zero.
3. **Pass `sendUpdates=all` on every Calendar insert / update / delete with attendees.** The documented default is `false` (= no notifications fire). Without the explicit flag, attendees get added silently and never see the invite — the most common reason an agent-created meeting "didn't go through."
4. **Draft, don't send, from Gmail — and use base64url on every `raw` field.** `drafts.create` keeps a reviewable artifact in the user's drafts folder before mail goes on the wire. The MIME `raw` field is base64url-encoded (URL-safe alphabet, no `+` or `/`) per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending); standard base64 passes plaintext tests and fails the first HTML or binary payload with `400 invalidArgument`.
5. **Use `copyFile` from a template for any Doc that needs page numbers.** The Docs API cannot insert `PAGE_NUMBER` auto-text into an existing doc. Page-numbered docs come from cloning a template you built — that's the path, not a missing API.

---

## What's in this article

- [Part 1 — The toolset and the mental model](#part-1--the-toolset-and-the-mental-model) — including [connector parity gotchas](#connector-parity-is-not-guaranteed)
- [Part 2 — Patterns that work (Docs)](#part-2--patterns-that-work)
- [Part 3 — Hard limits + workarounds (Drive & Docs)](#part-3--hard-limits--workarounds-drive--docs) — including [non-native files](#limit-5--non-native-files-need-download_file_content-not-readdocument)
- [Part 4 — Patterns to avoid (Drive & Docs)](#part-4--patterns-to-avoid-drive--docs)
- [Part 5 — Architecture: the single-writer pattern](#part-5--architecture-the-single-writer-pattern)
- [Part 6 — How to measure whether your writes are healthy](#part-6--how-to-measure-whether-your-writes-are-healthy)
- [Part 7 — Operating Google Sheets](#part-7--operating-google-sheets) — values-vs-structure split, A1 vs GridRange, USER_ENTERED defaults, developer metadata, Sheets-specific hard limits
- [Part 8 — Operating Google Slides](#part-8--operating-google-slides) — object-ID addressing, the under-served MCP surface, template-copy workflow, placeholder-text gotcha, no-transitions / no-animations / no-private-images limits
- [Part 9 — Operating Google Calendar](#part-9--operating-google-calendar) — eventId vs iCalUID addressing, sendUpdates silent-add failure, read-mutate-write discipline, recurring-event data model, async Meet links, sync tokens, ETag concurrency, push channels, ACL writes, service-account DWD
- [Part 10 — Operating Gmail](#part-10--operating-gmail) — base64url vs base64, label addressing by ID, threading headers, MIME assembly, send vs insert vs import, scope hierarchy, push notifications + historyId, service-account DWD
- [What we still don't know](#what-we-still-dont-know)

---
## Part 1 — The toolset and the mental model

### What this surface unlocks — Drive & Docs

Drive plus Docs together are the canonical "agent writes a document a human will read" surface. From a markdown payload you can land a branded company doc, prepend a dated section to an existing running-notes file, copy a templated proposal that carries its own page-number footer, or convert an inbound `.docx` to a native Google Doc for further editing. Drive provides idempotent addressing (file IDs) and the templating mechanism; Docs provides the body and styling surface. The patterns in Parts 2 through 6 show exactly how to make those writes land the way the markdown intended, on the first attempt, with verification baked in.

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
| **Raw Docs API `batchUpdate`** | Per-element `insertText` / `applyParagraphStyle` / `applyTextStyle` requests assembled into one batched call. | Surgical. No markdown round-trip. Full control over every textRun. | Multiples more code. The watch-outs in Part 4 cluster around this path. |
| **Drive HTML-import** | Multipart upload of inline-CSS HTML with `mimeType=application/vnd.google-apps.document`. Drive converts to a native Doc. | Faster than markdown for large content. Preserves headings, links, bold, lists, tables natively. The canonical "no MCP available" workaround. | Drive's HTML import **strips inline CSS for fonts and colors** — you still need a follow-up `batchUpdate` styling pass. Tables and nested lists can come through with subtle structural differences. |

Most automation uses path 1 for the common case and falls back to path 3 in cloud environments where the MCP server isn't reachable. Path 2 is for surgical edits inside an otherwise-styled doc, not for full body composition.

The catch shared across all three: every path leaves Google Docs **defaults** on the body unless you run an explicit styling pass after the upload. Mentally, treat the body-content write as "set the body content," not as "set the body content as it should look." Looks-as-it-should is the next 30 lines of code, regardless of which path delivered the body.

### Workspace plans + personal accounts: what's different

This article assumes you're operating against a Google Workspace org with broad programmatic access. That isn't every reader. Material differences exist by plan tier and account type — most don't matter until they do, and then they matter completely.

| Surface | What changes | Affects |
|---|---|---|
| **Shared Drives** | Available on every **paid** Workspace edition including Business Starter (since Sep 2024) and on Enterprise / Education Standard+. Not available on personal `@gmail.com` accounts. ([Workspace Updates, Aug 2024](https://workspaceupdates.googleblog.com/2024/08/shared-drive-access-business-starter.html)) | Any code that lists / writes Shared Drive content fails on personal accounts. The [Cowork connector regression](https://github.com/anthropics/claude-code/issues/53442) is about Shared Drives specifically — personal-account users aren't affected because the surface doesn't exist for them. |
| **Service accounts + domain-wide delegation** | Service accounts can live in any GCP project (including personal-account-owned). But **DWD authorization requires a Workspace super admin**, and impersonation only works against managed Workspace users — never against `@gmail.com` accounts. ([Workspace Admin Help](https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation)) | Any headless / scheduled write that depends on impersonation requires a Workspace target. The cloud-secret-proxy pattern in Part 5 assumes this works. |
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

### Where to spend your time — Docs

Once the map is clear, here are the patterns that close the largest share of real-world failure modes on the Docs surface. **The reader who only adopts items 1–5 closes the largest share of real-world failure modes.** Sheets has its own priority table in [Part 7](#part-7--operating-google-sheets); Slides, Calendar, and Gmail each have theirs in Parts 8–10.

| # | Pattern | Why this pattern wins | Effort |
|---|---|---|---|
| 1 | **Verify every style via JSON read, not tool success** | The JSON is the only ground truth for what's on the page. Reading it after every style write catches every silent-overwrite case — bold runs erased, bullets left as `textStyle: {}`, wrong font weight — before they ship. | Low |
| 2 | **Brand styling sequence: body sweep → cascade check → heading paragraph styles → heading text styles → inline bold prefixes** | The only 5-step order that produces a doc rendering the way the markdown intended. Every other order leaves Arial body, missing headings, or overwritten bold runs that still pass individual tool-call success checks. | Medium |
| 3 | **Cascade-check both directions after every paragraph-style write** | Two opposite cases need detection: HEADING_1 cascades across too many paragraphs (huge bold body) AND mid-write interruption leaves every paragraph as NORMAL_TEXT (no headings). Catching both before declaring success is what keeps the doc shipping clean. | Medium |
| 4 | **Pre-resize images at the file level (`sips` on macOS) before `insertImage`** | Pre-resizing the source file is the only path that reliably constrains rendered size — the API width/height parameters do not. One `sips` call, then the image lands at the size you asked for. | Low |
| 5 | **Copy from template for any doc that needs a page-number footer** | `copyFile` clones a template you built with the footer already baked in, then `replaceDocumentWithMarkdown` overlays the body. The footer survives because it lives at the `documentStyle` level, not in the body stream. | Medium |
| 6 | **Edit existing docs in place — never recreate to "prepend"** | Editing in place keeps the `doc_id` stable, so every external bookmark, Asana comment, and briefing link keeps working. Recreate-to-prepend is the canonical way to accumulate four files with the same title. | Low |
| 7 | **Treat all existing human content as load-bearing** | Inspecting the JSON for `inlineObjectElement`, `richLink`, `person`, and any unauthored text runs before any range replace preserves pasted images, smart chips, comments, and manual edits that would otherwise vanish into a wholesale replace. | Medium |
| 8 | **Idempotency: search-before-create, body-match-before-update, date-match-before-prepend** | Rerunning the same write reaches the same Drive state. That's the property an orchestrator's retry-on-transient-error loop needs to avoid silently duplicating content the first time the network blips. | Low |
| 9 | **State.json breadcrumbs for resume-from-interruption** | The breadcrumb file lets the next dispatch detect that a previous write died mid-cascade and recover the doc before layering a fresh write on top of a half-styled state. | High |

Most readers should adopt items 1–5 and stop. Items 6–9 are amplification, mostly relevant once you're running document writes from an unattended orchestrator.

### Pattern 1 — Edit existing documents in place

When updating any tracked Google Doc:

1. Read with `readDocument` (`format: "markdown"`).
2. Assemble new content.
3. Overwrite with `replaceDocumentWithMarkdown`, or `insertText` / `replaceRangeWithMarkdown` for surgical edits.

The doc id stays stable across the update, which means every external reference — bookmarks, Asana comments, briefing links — keeps working.

**The watch-out this prevents.** A real incident: four files named `2026 ClientB Advisory Running Notes` in the same Drive folder. One was the live doc that all external bookmarks and Asana comments pointed at. The other three were stale recreations from earlier sessions that had silently fallen back to a recreate path. Spotted only because a human noticed; an unattended agent would have kept producing recreations forever. Three were trashed; the canonical doc id was pinned in config so subsequent runs couldn't drift.

**If a configured doc id doesn't resolve, STOP and ask** before creating a replacement. Silent recreation is exactly how duplicates accumulate. After every update, the agent should search Drive by title and confirm exactly one file matches. Two matches is a bug.

### Pattern 2 — Verify every style via JSON read, not tool success

After any `applyTextStyle` or `applyParagraphStyle` call, read the doc as JSON (`readDocument` with `format: "json"`) and inspect the actual values per paragraph in the affected range.

Inspect:

- `namedStyleType` (`TITLE` / `HEADING_1` / `HEADING_2` / `HEADING_3` / `NORMAL_TEXT`)
- `bullet` (present or absent?)
- For each `textRun`: `content`, `textStyle.fontFamily` and `weightedFontFamily.fontFamily`, `textStyle.bold`, `textStyle.foregroundColor`, `fontSize.magnitude`

The JSON is the contract. A handful of edges to handle:

1. `applyTextStyle` with `{fontFamily: "X"}` (no `bold` flag) **overwrites existing bold formatting** on bold runs. Markdown's `**bold**` styling gets erased when you re-style. Mitigation: always include an explicit `bold: true` (or `false` for body sweeps) on every text-style application.
2. **Paragraph-range styles don't reliably cascade into bullet textRuns.** Bullets end up with `textStyle: {}` even when the parent paragraph range was styled. Mitigation: style each bullet individually with `matchInstance: N`. Don't rely on a parent range.
3. **`weightedFontFamily.weight: 400` can appear even when `bold: true` was set.** Visually bold appears, but the font variant is wrong. Per the [TextStyle reference](https://googleapis.dev/java/google-api-services-docs/latest/com/google/api/services/docs/v1/model/TextStyle.html), `weightedFontFamily` is applied first and weight defaults to 400; the `bold` flag is applied separately and the two can disagree. Mitigation: pass `weightedFontFamily: {fontFamily: "X", weight: 700}` AND `bold: true` together on the same request, and include both subfields in the `fields` mask. Inspect both `bold` and `weightedFontFamily.weight` in the post-write JSON; re-apply if they disagree.
4. **Agents report "all styles applied successfully" when JSON inspection shows they weren't.** This is the most common subagent miss in production. Mitigation: do not trust the success message; the JSON is the contract.

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

**Edge A — Excess cascade.** A `replaceDocumentWithMarkdown` write cascades HEADING_1 across far more paragraphs than the markdown intended. Real example: a doc with 4 expected H1 headings rendered with 116 paragraphs all set to HEADING_1, producing huge-bold-Arial body throughout. Detection: if actual H1 count > 1.5× expected, the cascade fired.

**Recovery from excess cascade:**

1. `applyParagraphStyle` with `namedStyleType: NORMAL_TEXT` across the affected range.
2. Re-apply HEADING_1 only to the lines that should be H1, using `applyParagraphStyle` + `textToFind` per heading.
3. Re-apply heading text styles via `applyTextStyle`.
4. Re-read JSON. Confirm count now matches.

**Edge B — namedStyleType strip.** The inverse. A partial write — typically `replaceDocumentWithMarkdown` followed by the agent dying or being interrupted before the heading re-apply step ran — leaves every paragraph as NORMAL_TEXT. What should be the doc TITLE, section H1s, topic H2s, and sub-H3s all render as plain body text. Detection: if actual count of `(TITLE + HEADING_1 + HEADING_2 + HEADING_3)` < 0.5× expected, strip is live.

**Recovery from strip — atomic per heading**, do NOT separate the paragraph-style and text-style passes:

1. Parse expected headings from the markdown source. Build a list of `{ level, exact_text }`.
2. For each expected heading, in document order:
   - `applyParagraphStyle` with `namedStyleType: HEADING_<level>` and `textToFind` = the exact heading text.
   - Immediately `applyTextStyle` on the same `textToFind` with the right font, size, color, and `bold: true`.
   - Move to next heading.
3. Do not batch all paragraph styles, then all text styles. The gap between phases is exactly when an interruption strands the doc in a half-styled state.
4. Re-read JSON. Confirm heading count meets expected.

The asymmetry is important. The two edges look opposite but stem from the same fragility — the doc's style state is built up in multiple tool calls, and any interruption between calls leaves it inconsistent.

### Pattern 5 — Brand styling sequence: the only order that works

After any `replaceDocumentWithMarkdown` write, apply styling in **exactly this order**. The MCP wraps the underlying [`updateTextStyle`](https://developers.google.com/workspace/docs/api/reference/rest/v1/documents/batchUpdate) and `updateParagraphStyle` request types; the steps below are the call sequence that survives every interaction edge documented in Pattern 4 and the patterns-to-avoid list in Part 4:

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

## Part 3 — Hard limits + workarounds (Drive & Docs)

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

The most common skill-level edge: calling `readDocument` on a Drive file id that resolves to a `.docx`. The error message rarely names this as the cause; the skill ends up reporting "couldn't read the doc" with no useful detail. Audit any skill that accepts "a Drive file id" as input — does it check `mimeType` before deciding how to read? If not, it's brittle on non-native files. The check is one extra `get_file_metadata` call and a switch on the returned mime type.

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

## Part 4 — Patterns to avoid (Drive & Docs)

Five patterns that look reasonable in code review and produce wrong output in production. Each entry leads with the constructive alternative — the shape to course-correct toward when you spot the pattern.

### Avoid 1 — Recreating a doc with the same title to "prepend"; do an in-place update instead

If you find code that creates a new doc, writes the prepend content + a separator + the old content, and then trashes the old doc, that's the recreate-pattern. It was a legitimate workaround in 2024 before in-place editing tools matured. The MCPs released through 2025 close that gap; the in-place path is now the right move.

Why the recreate pattern persists: it "works" until the trash step fails or the doc has external references that point at the old id. Then you have two files, or four, or eight. Spot it in code review by looking for `createDocument` calls inside what should be an "update" or "prepend" path.

**Course-correct to:** `replaceDocumentWithMarkdown` (full body replace) or `insertText` at index 1 (surgical prepend). The doc id stays stable; bookmarks keep working.

### Avoid 2 — Trusting tool success without JSON verification; read the JSON instead

If your code looks like this:

```
result = applyTextStyle(...)
if result.success:
    return "Styles applied"
```

…you've shipped the silent-overwrite case to handle. The tool returns success when:

- The API request succeeded, even though the doc didn't update the way you expected.
- The style was applied to one textRun but not the parent paragraph.
- Bold was overwritten on existing bold runs because no `bold: true` flag was passed.
- The cascade fired on a different range than intended.

**Course-correct to:** every style operation is followed by a `getDocumentInfo` read and a JSON inspection of the affected range. Make this routine, not exceptional.

### Avoid 3 — `insertText` at index 1 for a styled prepend; use the full-body markdown path

`insertText` inserts plain text. If your prepend content has `# H1` and `**bold**` markdown syntax in it, those tokens go into the doc as literal `#` characters and `**` characters with no styling applied.

**Course-correct to:** for a prepend that needs styling, the right move is:

1. `readDocument` (`format: "markdown"`) to get the current body.
2. Assemble the new full body: `<new entry>\n\n---\n\n<existing body>`.
3. `replaceDocumentWithMarkdown` with the assembled full body.
4. Re-apply brand styling per Pattern 5.

`insertText` is the right tool for adding unstyled text (a tracker line, a timestamp). For styled content, use the markdown path.

**A specific case worth naming:** "unstyled" does not mean "markdown source as the doc body." Cloud helpers that deliberately skip the styling pass (because brand cascade requires the MCP, which the cloud env doesn't have) sometimes prepend raw markdown via `insertText` and label the result "intentionally unstyled, will be re-styled by the next interactive run." That's wrong twice. First, the markdown tokens (`#`, `**`, `-`) land as literal characters and stay there until the interactive run re-styles — readers in the meantime see `**Format:**` as `**Format:**`, not as bold. Second, the interactive re-style runs `applyTextStyle` on the existing body, which won't convert markdown tokens to formatting; it'll just bold the literal `**` characters. The cloud helper must either skip the prepend until interactive is available, or assemble the full body and use the HTML-import path (which produces real styled content even without MCP).

### Avoid 4 — Deleting human content during a reformat; scan and preserve embedded objects first

The bright line is **information loss**, not formatting. Reformatting (P1 → bullets, header level changes, italic → bold) is fine. **Deleting, paraphrasing, or silently dropping content** — including pasted images, smart chips, comments, attachments, and typed prose — is not.

The case to handle: an agent runs `replaceRangeWithMarkdown` over a range that includes a pasted image. The reformat is correct; the image silently disappears. The image is gone from the doc and the original is gone from the agent's context. No recovery.

**Course-correct to:** before any `replaceRangeWithMarkdown`, `deleteRange`, or `replaceDocumentWithMarkdown` that touches existing content, read the JSON for the affected range and scan for:

- `inlineObjectElement` (pasted images, embedded files)
- `richLink` (linked Drive files rendered inline)
- `person` (smart chips for people)
- Any text runs the agent didn't author

If found, do not use a wholesale range replace. Instead: use surgical `applyTextStyle` / `applyParagraphStyle` on the existing structure, or `insertText` / `deleteRange` paragraph-by-paragraph around the embedded objects. If a wholesale replace is genuinely the right shape, extract the embedded objects first and re-insert them in the new content at the same logical position.

### Avoid 5 — A subagent that reports "all styles applied successfully"; require a verification field instead

If a subagent's return message says "applied styling" without a JSON verification step, the message is unreliable. The verification step might be in the subagent's code, but if the message doesn't tell you the post-write state — heading counts, font names per heading, body color — the subagent is reporting tool-call success, not document state.

**Course-correct to:** require the subagent's return contract to include a `verification` field with the actual post-write JSON inspection results. The orchestrator (or the human) reads the verification field, not the prose message.

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
| 3 | **Metadata-row collapse** — scan for paragraphs with > 1 `**Label:**` run | The markdown-collapse case |
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

The log path makes silent partial-success — the most expensive case to handle in production — debuggable later. Without it, "the doc looked wrong yesterday" is a question with no answer. With it, the post-write JSON sits on disk forever.

### Single writer per doc — and verifiers don't write either

The single-writer pattern is "one specialized subagent owns all writes." Extend that rule one step further: **validator / linter / drift-detector agents that find brand-styling issues must NOT also write the fix**. They should dispatch the writer.

The risk is concurrency. If a validator has `applyTextStyle` in its tools allowlist and runs alongside the writer, both think they own the cascade-check state for the same doc. Both write. The second write doesn't know about the first; cascade and JSON verification race; the final state depends on tool call interleaving rather than either agent's intended outcome. A validator with write tools is a second writer, regardless of how narrowly its prose says it should be used.

The clean shape: validators emit a typed outcome (`ok | drift_detected | flagged`); on `drift_detected`, the orchestrator re-dispatches `drive-doc-writer` with the corrected content. The writer keeps its sole-ownership invariant on cascade-check state. Validators stay read-only.

### Surface ownership — which docs are NOT yours to write

The writer pattern assumes the agent owns the surfaces it writes to. In practice, many Drive docs are **mixed surfaces** — humans curate the body, an agent prepends a dated section, and a separate process synthesizes the meeting afterward. Agents reflexively want to "summarize the call" or "consolidate the notes" into the same doc they prepended into. Both impulses produce information loss (Avoid 4 in Part 4).

The discipline: every Drive-touching skill should explicitly name the surfaces it does and does not own. Examples:

| Skill | Owns | Doesn't own |
|---|---|---|
| Meeting prep | The "upcoming meeting" prep section at the top | The rest of the running-notes doc |
| Post-meeting synthesis | A dated decisions-log entry in a separate file | The meeting-notes prep section at the top of running-notes |
| Brand validator | Read-only; emits drift findings | Every doc body (validators don't write — see above) |

Putting this in the skill's preamble (or in the agent's tools allowlist) prevents the reflexive "I see a doc I just touched; let me summarize what happened" case. The right answer is almost always: a different file, owned by a different skill.

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

### What this surface unlocks — Sheets

Sheets is the second-most-developed Workspace surface for agent automation, after Docs. From a single MCP server you can create a spreadsheet, write cell values that land as live formulas and typed dates, batch dozens of structural changes atomically, anchor data ranges with developer metadata so renames don't break the pipeline, and read computation-ready values without locale round-trip. The decisions in this Part — `USER_ENTERED` on writes, `UNFORMATTED_VALUE` on compute reads, `batchUpdate` over per-cell loops, developer metadata over hardcoded ranges — are what separate a working data pipeline from one that quietly mangles formulas, dates, and numbers under load.

Sheets is structurally different from Docs and the patterns reflect it. A Docs document is a tree of paragraphs with index-based addressing; a Sheets spreadsheet is a collection of 2D grids addressed by row/column. The same MCP server typically exposes both, but the failure modes don't transfer. This part covers what's unique to Sheets.

### What you can do today — Sheets capability inventory

| You want to... | Tool you reach for | Notes |
|---|---|---|
| Create a spreadsheet | `createSpreadsheet` | Returns the new file's `spreadsheetId` |
| Write cell values (text, numbers, dates) | `writeSpreadsheet` / REST `values.update` with `valueInputOption=USER_ENTERED` | Parses input the way the UI does — `Mar 1 2026` lands as a date, `=SUM(...)` lands as a formula |
| Write a formula | Same call; `USER_ENTERED` is non-negotiable | `RAW` lands the literal string starting with `=` in the cell |
| Read values for computation | `readSpreadsheet` / `values.get` with `valueRenderOption=UNFORMATTED_VALUE` | Returns typed values; `FORMATTED_VALUE` returns locale-rendered strings — round-trip risk for any compute path |
| Read formulas as source text | Same call with `valueRenderOption=FORMULA` | For round-tripping or auditing formula contents |
| Atomic multi-step structural change | REST `spreadsheets.batchUpdate` with a list of typed `Request` objects | Atomic per Google's [batchUpdate guide](https://developers.google.com/sheets/api/guides/batchupdate); one failure rolls back the whole batch |
| Anchor a data range that survives renames / reorders | `AddDeveloperMetadataRequest`; read via `batchGetByDataFilter` with a DataFilter | Tags carry through tab renames, reorders, inserted rows — see [developer metadata](https://developers.google.com/sheets/api/guides/metadata) |
| Format cells (color, borders, number format) | REST `spreadsheets.batchUpdate` with `RepeatCellRequest` / `UpdateBordersRequest` / `UpdateCellsRequest` | Always set a narrow `fields` mask; `"*"` resets every property in the message to default |
| Add or rename a sheet (tab) | `AddSheetRequest` / `UpdateSheetPropertiesRequest` | sheetId is stable across renames; tab names are not |
| Apply conditional formatting | `AddConditionalFormatRuleRequest` | Range is a `GridRange`; ordering of rules matters |
| Insert a chart | `AddChartRequest` | Chart styling ceiling is real — see Limit S3 below |
| Embed an image via formula | `IMAGE(<public-url>)` cell value with `USER_ENTERED` | Public URL required; Drive-hosted URLs don't load; SVG not supported |

### Where to spend your time — Sheets

| # | Pattern | Why this pattern wins | Effort |
|---|---|---|---|
| S1 | **`valueInputOption=USER_ENTERED` for almost every write** | Formulas become formulas, dates become dates — the UI's parse behavior, applied at the API. Without it, `=SUM(A1:A10)` lands as the literal string starting with `=` and downstream math reads zero. | Low |
| S2 | **Set the `fields` mask on every `UpdateCellsRequest`** | The narrowest mask covers exactly what you're writing and leaves every other property intact. Omitting the mask or passing `"*"` writes the message's defaults across every property in the cell. | Low |
| S3 | **Collapse N writes into one `batchUpdate`** | Per-user quota is 60 requests/min ([Sheets API limits](https://developers.google.com/sheets/api/limits)). One batchUpdate is one quota unit; an N-call loop is N. The batch is also atomic — partial-failure recovery problems vanish. | Low |
| S4 | **Pin `valueRenderOption=UNFORMATTED_VALUE` for any compute path** | Compute reads typed values directly, with no locale round-trip. The default `FORMATTED_VALUE` returns locale-rendered strings — readable for display, but a quiet mangle the moment math touches them. | Low |
| S5 | **Use developer metadata to anchor sheet position** | Developer metadata tags survive every rename, reorder, and row insertion. The pipeline reads "the row tagged `primary_data`" instead of "row 1 of the sheet named exactly `Data`" — the former survives every human edit. | Medium |

### Pattern S1 — USER_ENTERED is the load-bearing default

Per the [values guide](https://developers.google.com/sheets/api/guides/values):

> `RAW`: "The input is not parsed and is inserted as a string. For example, the input `=1+2` places the string, not the formula, `=1+2` in the cell."
>
> `USER_ENTERED`: "The input is parsed exactly as if it were entered into the Sheets UI. For example, `Mar 1 2016` becomes a date, and `=1+2` becomes a formula."

The default in most clients is `INPUT_VALUE_OPTION_UNSPECIFIED`, which defaults server-side to a stricter mode and produces the literal-string behavior. **Always pass `USER_ENTERED` explicitly** unless the input is genuinely a string that begins with `=` and you want it preserved that way.

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

### Hard limits + workarounds — Sheets

**Limit S1 — No `CellImage` (blob) inserts via the API.** The Sheets API can write `IMAGE()` formula URLs through USER_ENTERED, but uploaded image blobs anchored to specific cells require Apps Script's [`SpreadsheetApp.newCellImage()`](https://developers.google.com/apps-script/reference/spreadsheet/cell-image). `IMAGE()` also won't load from `drive.google.com` URLs and won't render SVG.

**Limit S2 — No partial pivot table edits.** Editing an existing pivot table requires writing the entire `pivotTable` field again via `UpdateCellsRequest`. There is no fields-mask path to update just the rows or columns of a pivot. Plan pivot writes as full replaces.

**Limit S3 — No full chart styling.** Per Google's [charts samples](https://developers.google.com/sheets/api/samples/charts): "The Sheets API doesn't yet grant full control of charts… some chart types and certain chart settings (such as background color or axis label formatting) can't be accessed or selected with the current API." The supported subset (column, bar, line, pie, scatter, area, combo) covers most cases but the styling ceiling is real.

**Limit S4 — No revision-locked concurrency.** There is no `If-Match` / ETag concurrency control on Sheets writes. Parallel `append` calls or an `append` fired immediately after a `DeleteDimensionRequest` exhibit real race conditions ([Google Dev forum thread](https://discuss.google.dev/t/row-offsets-occur-when-append-requests-run-immediately-after-deletedimension-suggesting-the-delete-isn-t-fully-applied-yet/345218)) where the append lands at the pre-delete row index. Serialize dependent writes within a single batch.

**Limit S5 — 10 million cell ceiling per spreadsheet** (20M in the [2026 beta](https://workspaceupdates.googleblog.com/2026/04/faster-performance-and-doubled-cell-limits-in-Google-Sheets.html) for opted-in Workspace orgs). The limit counts across all tabs. `batchUpdate` returns `INVALID_ARGUMENT` once exceeded; no soft-deny. Plan for sharding into multiple spreadsheets before you approach the ceiling.

**Limit S6 — No triggers, custom menus, or sidebar UI.** These are Apps Script territory only. If your automation needs to fire on cell edit, schedule on a time-driven trigger, or render a sidebar UI, the API is the wrong surface. Apps Script reaches the same Sheets and adds the UI/trigger layer the API doesn't.

### Patterns to avoid — Sheets

**A-S1 — Writing formulas with `valueInputOption=RAW`; pass `USER_ENTERED` instead.** Covered in Pattern S1. The most-common Sheets API mistake; spot it in code review by looking for any formula string written without an explicit `USER_ENTERED` flag.

**A-S2 — Hardcoded `Sheet1!A1:Z1000` ranges; use developer metadata or named ranges.** Hardcoded ranges break the moment a tab is renamed, reordered, or rows extend past row 1000. Developer metadata (Pattern S4) or named ranges survive every human edit.

**A-S3 — Looping `values.update` calls; collapse into one `values.batchUpdate`.** N quota units for what one batch call costs as one. Always collapse.

**A-S4 — Omitting the `fields` mask on `UpdateCellsRequest`; set the narrowest mask that covers the write.** Omitting the mask silently writes the message's defaults across every property in the cell. The mask should be the narrowest path that covers what you're writing.

**A-S5 — Reading `FORMATTED_VALUE`, doing math, writing back; pin `UNFORMATTED_VALUE` for compute paths.** Locale round-trip mangle. The compute path always pins `UNFORMATTED_VALUE`.

**A-S6 — `values.append` with `INSERT_ROWS` into a table that has a totals row below it; use `UpdateCellsRequest` instead.** Append's "table" detection uses contiguous non-empty cells, but it pushes the totals row down forever with `INSERT_ROWS` — or splats over data with `OVERWRITE`. For sheets with structural rows below the data, append is the wrong shape; explicit `UpdateCellsRequest` is.

### Apps Script vs Sheets API — where the line falls

The two surfaces overlap significantly but each has things the other can't do. From [Tanaike's benchmarks](https://tanaikech.github.io/2018/10/12/benchmark-reading-and-writing-spreadsheet-using-google-apps-script/), the Sheets API beats Apps Script's `SpreadsheetApp` for large ranges (~35% read, ~19% write savings), but `setValues()` wins on small ranges with many columns (crossover near 75 columns).

| Surface | Strengths | Limits |
|---|---|---|
| Sheets API | Bulk `batchUpdate`, server-side scheduling outside Google quotas, OAuth-token-scoped programmatic access | No triggers, no UI (menus / sidebars), no `CellImage` blob inserts, no custom functions |
| Apps Script | Triggers (`onEdit`, `onChange`, time-driven), custom menus and sidebars, `CellImage` blob inserts, custom functions, live access inside the editor session | Slower at bulk; runs inside Google's Apps Script quotas; awkward outside Google Workspace itself |

Most production automations land somewhere on the spectrum. The decision rule: if the workflow needs to fire on a cell edit or render a UI inside Sheets, Apps Script. If the workflow needs bulk write throughput or external orchestration, Sheets API. Mixed setups are normal — an Apps Script `onEdit` trigger that calls out to an external service which talks to the Sheets API for the heavy lift.

---

## Part 8 — Operating Google Slides

### What this surface unlocks — Slides

Slides is the surface where production decks come from agents — copy a template, swap in fresh data, restyle, ship. Done well, an agent clones a master template via Drive `files.copy`, batch-updates 50–200 atomic mutations across the whole deck in one call, replaces tag tokens (`{{title}}`, `{{date}}`) with current data, embeds a live Sheets chart, and writes speaker notes. The decisions in this Part — pre-assigning your own `objectId` for stable addressing, deleting placeholder prompt text before insert, bundling mutations in one `batchUpdate`, copying-not-mutating templates — are what produce decks that round-trip cleanly across editor edits.

Slides is the third Workspace surface and the most under-served by production MCP tooling. The mental model is different from both Docs and Sheets; the failure modes are different; the API surface is different.

### What you can do today — Slides capability inventory

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
| Tag-substitution across the deck | `ReplaceAllTextRequest` with `containsText` | Inherits formatting from the first character of the matched range — see avoid-list below |
| Generate slide thumbnail | `presentations.pages.getThumbnail` | Expensive read; rate-limited |

### Where to spend your time — Slides

| # | Pattern | Why this pattern wins | Effort |
|---|---|---|---|
| L1 | **Pre-assign your own `objectId` at create time, persist content/alt-text as the lookup key** | Caller-controlled IDs plus content/alt-text lookup survive every editor round-trip. Object IDs returned by the API are not stable per Google's docs; a deck a human opens between batches needs a re-resolvable handle, and text or alt-text is it. | Low |
| L2 | **Always pair `InsertText` with a preceding `DeleteText` against placeholder shapes** | Inserting against an empty shape lands clean text; inserting against a placeholder still carrying its prompt text (`Click to add title`) concatenates. The `DeleteText` first guarantees the shape is empty before the insert. | Low |
| L3 | **Bundle every related mutation into one `batchUpdate` (atomic) — never one-request-per-mutation** | 50–200 requests in a single call is the documented norm. Atomicity prevents half-applied decks; quota math (600/min/project, 60/min/user) collapses N round-trips into one. | Low |
| L4 | **Always set `fields` mask on `Update*Request`** | The narrowest mask updates exactly what you're targeting and leaves every other property intact. Same rule as Sheets and Docs. | Low |
| L5 | **For template-driven decks, copy the template via Drive `files.copy`, then `ReplaceAllText` into the copy** | Google's explicit instruction: *"make a copy and use the Slides API to manipulate the copy. Don't use the Slides API to manipulate your primary 'template' copy!"* — keeps the template clean and reusable for the next deck. | Medium |

### The mental model — one batch endpoint, object-ID addressing

A presentation is a tree: **Presentation → Page → PageElement**. Four page types (Slide, Master, Layout, Notes); page elements are Shape, Table, Image, Video, Line, WordArt, SheetsChart, or Group. Style inheritance flows up: slide ← layout ← master. Per the [Slides API overview](https://developers.google.com/workspace/slides/api/guides/overview), all mutation goes through one endpoint — `presentations.batchUpdate` — which accepts a list of typed `Request` objects and applies them atomically.

Slides addressing is **string `objectId` per element**. Unlike Docs (start/end indices into a flat document) and unlike Sheets (`A1` ranges or `GridRange`), every page and page element has an explicit ID.

> **The #1 Slides gotcha — object IDs are not stable.** Per Google's own docs: *"you cannot depend on an object ID being unchanged after a presentation is changed in the Slides UI."* If a human opens the deck in the Slides editor between your batch writes, your saved object IDs may not match anymore. The discovery patterns that survive: persist the **text content** of a shape (find shapes whose text contains "Title — {{date}}") or the **alt-text** (find shapes whose alt-text is `"primary_chart"`), and re-resolve to the current object ID before each batch.

### Production MCP coverage for Slides is shallow

This matters and deserves to be named explicitly. As of mid-2026:

- The production Google Workspace MCP servers (taylorwilsdon/google_workspace_mcp, matteoantoci/google-slides-mcp) expose ~7 Slides tools — `create_presentation`, `get_presentation`, `batch_update_presentation`, `get_page`, `get_page_thumbnail`, `list_presentation_comments`, `manage_presentation_comment`.
- Compare to Docs (~14 tools, fine-grained: `insertText`, `applyTextStyle`, `applyParagraphStyle`, `insertImage`, `replaceDocumentWithMarkdown`, etc.) and Sheets (~13 tools, equally fine-grained).
- The Slides MCP path funnels every mutation through `batch_update_presentation`, so the agent ends up authoring raw `Request` JSON. There is no `insertImage`-style convenience tool, no `applyTextStyle`, no `replaceAllText` shortcut.

**Practical implication:** building decks from an agent today means either (a) authoring raw `presentations.batchUpdate` payloads directly, or (b) writing a thin local helper that exposes higher-level operations (create slide with layout, insert text into placeholder, etc.) on top of the REST API. The latter is the right shape for any operator who builds more than a handful of decks programmatically.

### Hard limits + workarounds — Slides

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

### Patterns to avoid — Slides

**A-L1 — Trusting object IDs after a human edits the deck; re-resolve via text content or alt-text.** Once the editor touches the file, your stored IDs may be stale. Cover by re-resolving via text content or alt-text on each batch.

**A-L2 — `InsertText` at index 0 of a placeholder without first `DeleteText`; pair every InsertText against a placeholder with a preceding DeleteText.** Placeholder prompt text ("Click to add title") stays in the cell. The resulting slide reads `Click to add titleYour Real Content`. Pairing fixes it.

**A-L3 — Calling `ReplaceAllText` and expecting it to restyle; follow with `UpdateTextStyleRequest`.** ReplaceAllText changes the text only; formatting carries from the first character of the matched range. For a redesign, always follow with `UpdateTextStyleRequest`.

**A-L4 — Posting one-request-per-mutation; bundle 50–200 in a single `batchUpdate`.** Quota is per-project (600/min) and per-user (60/min). Bundle 50–200 requests in a single `batchUpdate`; atomic semantics prevent partial-failure mess.

**A-L5 — Using the Slides API to manipulate your "template" copy; always `files.copy` first, mutate the copy.** Google's explicit warning. Always `files.copy` the template into a working folder first, then mutate the copy. The template stays clean and reusable.

**A-L6 — Passing `*` as the `fields` mask on Update requests; set the narrowest mask that covers the write.** Passing `*` resets every property in the message to its default. Use the narrowest path that covers what you're writing.

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

4. **Whether the cascade-style edges will reduce as MCP servers mature.** Both excess cascade and namedStyleType strip are interactions between the markdown converter and the doc's named styles. As the converter gets smarter, the regressions may become rarer. Keep cascade-check as a defense regardless — the cost is one extra `getDocumentInfo` per write, and the cases to handle are too expensive to leave undefended.

5. **Whether Google ships revision-locked concurrency for Sheets writes.** No If-Match / ETag mechanism exists today; concurrent `append` calls and append-after-deleteDimension races are real. A future API change would let serialized pipelines run truly parallel. Until then, the workaround is to keep dependent writes inside a single `batchUpdate` call.

6. **Whether the Sheets API will expose `CellImage` blob inserts.** Today only Apps Script can anchor uploaded image blobs to specific cells; the API can only write `IMAGE()` formula URLs (which won't accept Drive-hosted URLs and won't render SVG). The asymmetry is annoying for any automation that wants to embed generated images in a Sheets dashboard.

7. **Whether production MCP servers will close the Slides coverage gap.** Today Slides exposes ~7 tools versus Docs' ~80 and Sheets' ~20 in the canonical Google Workspace MCP. Building decks programmatically means authoring raw `presentations.batchUpdate` payloads — slower iteration than the Docs/Sheets surfaces. A future MCP release with fine-grained Slides tools (`insertText`, `applyTextStyle`, `replaceAllText` as first-class tools) would close the gap.

8. **Whether Slides will ship API support for transitions, animations, and private-Drive image insertion.** All three are [tracked as open issues](https://issuetracker.google.com/issues/36761236), some since 2016. The workarounds (apply transitions in the editor, mint public URLs for images) are durable; an API change would obsolete a real chunk of deck-automation code.

---

## Part 9 — Operating Google Calendar

### What this surface unlocks — Calendar

Calendar is where an agent moves from documents to scheduled actions. From a single API surface you can create single and recurring events with attendees, book Workspace resource calendars (rooms, equipment) that auto-accept during free windows, attach a Google Meet link that resolves asynchronously, store structured app state on the event via `extendedProperties`, push-subscribe to inbox changes, and run optimistic-concurrency updates that catch concurrent writers. The decisions in this Part — passing `sendUpdates=all` so attendees actually get notified, populating `start.timeZone` with an IANA ID, read-mutate-write to avoid full-replace wipes, persisting `syncToken` for incremental change tracking — are the ones that separate working calendar automation from agents that silently add attendees no one ever sees on their invite list.

Calendar is the fourth Workspace surface and the first one in this guide where the addressing model is genuinely tricky. Docs uses character indices, Sheets uses A1 ranges, Slides uses string `objectId`. Calendar uses **two parallel identifiers** (`eventId` vs `iCalUID`), plus a third (`recurringEventId` + `originalStartTime`) for instances of recurring events. Production bugs cluster on choosing the wrong one.

### The 60-second map — Calendar

A calendar is a collection of events identified by an email-shaped string (`primary` for the authenticated user, or `someone@example.com` for shared calendars). An event is owned by exactly one calendar — the organizer's. Per Google's [events & calendars concepts](https://developers.google.com/workspace/calendar/api/concepts/events-calendars), the resource hierarchy is:

| Resource | What it is | Addressing model |
|---|---|---|
| `Calendars` | Calendar metadata (summary, default timeZone, location) | calendarId (email-shaped string) |
| `CalendarList` | The user's subscription to calendars they didn't create | calendarId |
| `Events` | The events themselves (single or recurring) | `(calendarId, eventId)` OR `(calendarId, iCalUID)` |
| `Instances` | Individual occurrences of a recurring event | `(calendarId, recurringEventId, originalStartTime)` |
| `Acl` | Per-calendar access rules | role + scope (user / group / domain) |
| `Freebusy` | Aggregate busy intervals across multiple calendars | array of items, max 50 |
| `Settings` | Per-user calendar settings (default timezone, working hours, etc.) | key/value pairs |
| `Colors` | Color palette IDs for calendars and events | enum of `colorId` strings |
| `Channels` | Push-notification subscriptions | webhook receiver |

The Calendar API exposes 11 endpoints on the Events resource per the [Events reference](https://developers.google.com/workspace/calendar/api/v3/reference/events): `delete`, `get`, `import`, `insert`, `instances`, `list`, `move`, `patch`, `quickAdd`, `update`, `watch` — plus `freebusy.query` and the `calendarList.*` / `acl.*` / `calendars.*` / `settings.*` / `colors.*` / `channels.*` resources at the top level. Most MCP wrappers cover a subset — typically `list`, `get`, `insert`, `update`, `delete`, plus `freebusy` and `events.instances` for the recurring case. Anything not exposed by the wrapper (sync tokens, conferenceData polling, ACL edits, freebusy queries against >50 calendars, ETag concurrency) drops to direct REST against the [Calendar API v3 reference](https://developers.google.com/workspace/calendar/api/v3/reference).

### What you can do today — Calendar capability inventory

| You want to... | Tool you reach for | Notes |
|---|---|---|
| Create a single-time event | REST [`events.insert`](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert) | Pass `start.dateTime` + `end.dateTime` + `timeZone` (IANA ID, never a UTC offset) |
| Create an all-day event | `events.insert` with `start.date` + `end.date` (no time, no timeZone) | The `end.date` is **exclusive** — a one-day event ending Tuesday has `end.date = Wednesday` per the [events concepts page](https://developers.google.com/workspace/calendar/api/concepts/events-calendars) |
| Create a recurring event | `events.insert` with `recurrence: ["RRULE:FREQ=WEEKLY;BYDAY=MO;UNTIL=20261231T235900Z"]` | RRULE/RDATE/EXDATE syntax per [RFC 5545](https://www.rfc-editor.org/info/rfc5545/). Recurrence requires `timeZone` on the start so the API can expand instances |
| Send invitation emails to attendees | Same insert/update + `sendUpdates=all` query parameter | Per the [events.insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert), "the default is `false`" — behaviorally equivalent to `none`, so attendees get added silently with no notification |
| Mark an event as Free (not busy) on the organizer's calendar | `events.insert/patch` with `transparency: "transparent"` | Default is `opaque` (= shows as busy in freebusy and to other invitees). Per the [Event resource reference](https://developers.google.com/workspace/calendar/api/v3/reference/events#resource) |
| Update one instance of a recurring event | `events.patch` on the **instance ID** returned from `events.instances` | Creates an exception. Modifies that one occurrence only |
| Update this-and-following instances | Two calls: trim the original's `UNTIL` + insert a new recurring event from the split point | No single API call. Documented in the [recurring events guide](https://developers.google.com/workspace/calendar/api/guides/recurringevents) |
| Add a Google Meet link | `events.insert/patch` + `conferenceData.createRequest` + query param `conferenceDataVersion=1` | Async — initial response status is `pending`; poll the event until `success` per the [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events) |
| Get free/busy across many calendars | REST [`freebusy.query`](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query) | Max 50 calendars per query (`calendarExpansionMax`); returns busy intervals, you compute free |
| Book a room or resource calendar | `events.insert` with the resource calendar email in `attendees[]` + `sendUpdates=all` | Workspace resource calendars auto-accept invitations during free windows and auto-decline on conflicts. Resource emails come from the Admin Console resource directory; treat them like any other invitee at the API layer |
| Store structured app state on an event | `extendedProperties.private` or `extendedProperties.shared` | 44-char key cap, 1024-char value cap, 300 properties per event, 32 KB total ([extended properties guide](https://developers.google.com/workspace/calendar/api/guides/extended-properties)) |
| Search events by app-stored key | List + `privateExtendedProperty=key=value` query parameter | Multiple repeats OR'd within a type, AND'd across types |
| Grant another principal access to a calendar | REST [`acl.insert`](https://developers.google.com/workspace/calendar/api/v3/reference/acl/insert) | `role` ∈ `none` / `freeBusyReader` / `reader` / `writer` / `owner`; `scope.type` ∈ `default` / `user` / `group` / `domain` with `scope.value` carrying the email or domain |
| Move an event to a different calendar | REST [`events.move`](https://developers.google.com/workspace/calendar/api/v3/reference/events/move) with `destination` | Only `eventType=default` is movable; `birthday`, `focusTime`, `fromGmail`, `outOfOffice`, `workingLocation` cannot |
| Incrementally sync changes | List with `syncToken` from the prior response's `nextSyncToken` | Token incompatible with most filters; `410 GONE` means resync from scratch ([sync guide](https://developers.google.com/workspace/calendar/api/guides/sync)) |
| Receive push notifications on changes | [`events.watch`](https://developers.google.com/workspace/calendar/api/guides/push) on a webhook channel | Channel expiration returned in the response; per the [push guide](https://developers.google.com/workspace/calendar/api/guides/push), renewal requires a new `watch` call with a new channel `id` |
| Submit many Calendar calls in one HTTP round-trip | JSON batch endpoint `https://www.googleapis.com/batch/calendar/v3` per the [batch guide](https://developers.google.com/workspace/calendar/api/guides/batch) | 1000 calls per batch hard cap; each call still counts individually against quota |

### Where to spend your time — Calendar

The patterns that close the largest share of real-world Calendar cases to handle. The top four are non-negotiable — every Calendar agent gets them wrong at least once.

| # | Pattern | Why this pattern wins | Effort |
|---|---|---|---|
| 1 | **Always pass `sendUpdates=all` explicitly on insert / update / delete when attendees are present** | Attendees get the invitation email and actually show up to the meeting. The documented default is `false` (= no notifications fire) per the [insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert) — without the explicit flag the meeting "didn't go through." | Low |
| 2 | **Populate `start.timeZone` with an [IANA](https://www.iana.org/time-zones) ID, never an offset; recurring events MUST have a timeZone** | IANA IDs (`America/New_York`) carry DST rules and political-change history; the API expands recurrences correctly across DST transitions. Hardcoded offsets like `-05:00` drift by an hour twice a year. | Low |
| 3 | **Read-mutate-write, never partial-update via raw object construction** | The full event resource round-trips through the update — attendees, reminders, conferenceData, transparency all stay intact. Constructing an update body from scratch silently wipes every field you forgot to populate. | Low |
| 4 | **For series edits, decide series-vs-instance up front; never modify instances individually as a backdoor "edit series"** | Series-level edits propagate to every instance cleanly. Per-instance edits accumulate as exceptions that clutter the calendar, slow access, and flood attendees with change notifications. | Medium |
| 5 | **Use `extendedProperties.private` as the source of app state — not the description field** | App-key state survives every human edit to the description, stays out of search indexes and exports, and is directly queryable via `privateExtendedProperty`. | Low |
| 6 | **Poll `conferenceData.createRequest.status` after creating a Meet event before reporting the link** | The Meet link is async per the [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events). Polling until `success` ensures the event ships with a working join URL. | Low |
| 7 | **Persist `syncToken` per calendar in durable storage; handle `410 GONE` as full-resync, not an error** | The token is the only path to "what changed since last poll" including cancellations; `updatedMin` polling misses deletes. Treating 410 as expected lets the sync loop recover cleanly. | Medium |
| 8 | **Always pass `singleEvents=true` on `events.list` when expanding recurring events** | One row per instance instead of one row per series; per-instance metadata (rescheduled time, attendee responses) becomes visible. Default returns the series resource only. | Low |
| 9 | **Use ETag + `If-Match` on every read-modify-write to avoid silent overwrites** | A concurrent writer's change triggers `412 Precondition Failed` instead of silent overwrite; the loser re-reads and retries instead of clobbering. | Medium |
| 10 | **For >50 calendars in freebusy lookup, batch into chunks of 50; cache aggressively** | One query returns up to 50 calendars' busy intervals per the [freebusy.query reference](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query); chunking lets large room-finders scale without hitting `400 invalidParameter`. | Medium |

Most readers should fix patterns 1–4 and stop. Items 5–10 matter once agents are managing series, app-key state, or real-time calendar sync.

### TL;DR — five non-obvious Calendar bits

1. **`sendUpdates` default is `false` (= `none` behavior).** Per the [insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert), the literal documented default is the string `false`, which fires no notifications — equivalent to passing `none`. Every insert / update with attendees that doesn't pass `sendUpdates=all` adds them silently. The most common reason an agent-created meeting "didn't go through."
2. **Recurring events need an explicit `timeZone`.** The API needs an IANA timezone to expand the recurrence rule. A field that looks optional is load-bearing.
3. **`events.update` is a full replace.** The [update reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/update) is explicit: omitting `attendees` or `conferenceData` wipes them. Read first, mutate, write the full object back — or use `events.patch`.
4. **The Meet link is async.** `conferenceData.createRequest` returns `status: pending` on the initial response. Poll until `success` before reporting the link.
5. **Use ETag + `If-Match` on read-modify-write.** Calendar implements optimistic concurrency per the [version-resources guide](https://developers.google.com/workspace/calendar/api/guides/version-resources). Skip the ETag and concurrent writers silently overwrite each other — no error, no warning, the second write wins.

### Deep dive — recurrence, time zones, and the four ways to break a series

Recurrence is where Calendar production bugs concentrate. The data model has four interacting pieces, and every common case to handle comes from confusing two of them.

**The four pieces:**

1. **The series event** — has a `recurrence` field (an array of RRULE / RDATE / EXDATE strings per [RFC 5545](https://www.rfc-editor.org/info/rfc5545/)), one `id`, one `iCalUID`. The `start.dateTime` is the FIRST occurrence; everything else is computed from the RRULE.
2. **Instances** — `events.instances(calendarId, eventId)` returns occurrences expanded from the RRULE. Each instance has `recurringEventId` (pointing back at the series) and `originalStartTime` (the time per the RRULE, distinct from `start.dateTime` if the instance was rescheduled).
3. **Exceptions** — an instance modified individually. Same `recurringEventId`, but lives as its own resource with its own `id`. Sending `status: "cancelled"` on an instance cancels just that occurrence.
4. **EXDATE** — an exclusion date inside the series's `recurrence` array. The series itself knows "skip 2026-06-15"; the user sees that date as not-an-occurrence at all. Different from cancelling an exception — EXDATE never produced an instance in the first place.

**The four ways to break a series:**

**Break #1 — modifying instances individually to "edit the series."** Looping `events.instances` and calling `events.patch` on each produces N exceptions, each cluttering the calendar and firing change notifications. Per the [recurring events guide](https://developers.google.com/workspace/calendar/api/guides/recurringevents): "creates lots of exceptions that clutter the calendar, slowing down access and sending a high number of change notifications." Edit the series event (the one with `recurrence` set); the change propagates to all non-exception instances.

**Break #2 — `events.update` on the series wipes existing exceptions.** Update payload omits the `recurrence` field, the API treats the omission as "remove recurrence" (per the [update reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/update): "always updates the entire event resource"), and the series collapses to a single event. Read-mutate-write the entire resource.

**Break #3 — splitting at an instance to do "this and following."** No single API call exists. Two steps: (a) update the original series's RRULE `UNTIL` (or `COUNT`) to stop before the target instance, (b) `events.insert` a new series starting from the target instance. Per the [recurring events guide](https://developers.google.com/workspace/calendar/api/guides/recurringevents), this operation resets any exceptions occurring after the split. Pre-snapshot via `events.instances` and replay the exceptions onto the new series.

**Break #4 — no `timeZone` on the series.** RRULE expansion needs a timezone to know when "weekly on Monday 10am" actually fires. Set `start.timeZone` to an IANA Time Zone Database ID per [IANA](https://www.iana.org/time-zones) (`America/New_York`, never `EST`, never `-05:00`). The [events concepts page](https://developers.google.com/workspace/calendar/api/concepts/events-calendars) documents the `timeZone` field shape and the [recurring events guide](https://developers.google.com/workspace/calendar/api/guides/recurringevents) documents the expansion requirement.

### Deep dive — the read-mutate-write loop, in code

`events.update` is a full replace. The defensible pattern is `events.get` → mutate → `events.update`, with the ETag carried as `If-Match` to catch concurrent writes. All Python snippets in this part use `urllib.request` + a Bearer token so they work without an SDK; substitute the SDK call shape if preferred.

```python
import json, urllib.request

def update_event(token, cal_id, event_id, mutate):
    base = f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events/{event_id}"
    # 1. Read the full event; the response carries an ETag the API uses for concurrency
    req = urllib.request.Request(base, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        etag = r.headers["ETag"]               # opaque per-resource-version string
        event = json.loads(r.read())
    mutate(event)                              # caller-supplied in-place mutation
    body = json.dumps(event).encode()
    # 2. Write back with If-Match so a concurrent writer's change triggers 412 instead of silent overwrite
    req = urllib.request.Request(base, data=body, method="PUT",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": "application/json",
                 "If-Match": etag})
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 412:                      # another writer beat us; caller retries from get
            raise ConcurrentWriteError()
        raise
```

The `If-Match` header is the only durable defense against the "two agents mutate the same event simultaneously, the second silently wins" case to handle. On 412, re-read and retry; don't blind-overwrite.

### Deep dive — sendUpdates, attendees, and the silent-add failure mode

`sendUpdates` is a query parameter, not a body field. It governs whether attendees get notification email when an insert / update / delete includes them. Per the [insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert), three legal enum values plus an omitted-parameter default:

| Value | Behavior |
|---|---|
| `all` | Notifications fire to every guest |
| `externalOnly` | "Notifications are sent to non-Google Calendar guests only" (i.e. guests who don't use Google Calendar — typically external mail providers like Outlook / Yahoo). Guests at other Workspace orgs who do use Google Calendar are NOT notified |
| `none` | No notifications fire at all |
| _(omitted)_ | The [insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert) documents the default as `false` — a string carryover from the deprecated `sendNotifications` boolean parameter `sendUpdates` replaced. Behavior is identical to `none` — no notifications fire |

**Omitting the parameter sends no notifications.** Per the doc, "the default is `false`." Code that doesn't pass the parameter explicitly does not send invitations. The agent reports "event created with 5 attendees," the API returns 200, and not one of the five gets an email.

The caveat the docs add: "Note that some emails might still be sent." Workspace orgs with calendar-side settings (default-notification policies, recipient-side filters) can override the parameter in both directions. For mission-critical "this person has to see the invite" cases, the durable defense is belt-and-braces: pass `sendUpdates=all` AND fire a parallel Gmail message with the event details outside the Calendar pipeline.

A symmetric watch-out exists on `delete` and on `update` of an existing event. Both honor `sendUpdates` the same way. Cancelling a meeting without `sendUpdates=all` removes it from the organizer's calendar and from invitee responses, but doesn't notify them. They show up to an empty room.

### Deep dive — transparency, busy/free, and how an event appears in freebusy

Every event has a `transparency` field with two legal values per the [Event resource reference](https://developers.google.com/workspace/calendar/api/v3/reference/events#resource):

- `opaque` (default) — the event blocks time on the organizer's calendar; `freebusy.query` returns it as busy
- `transparent` — the event is on the calendar but does NOT block time; `freebusy.query` skips it

Two production patterns hinge on this field.

**Pattern A — marking a personal block as Free.** Hold-time blocks, focus-time placeholders, internal context windows. Inserting with `transparency: "transparent"` keeps the event visible on the organizer's calendar but invisible to schedulers looking for open time.

**Pattern B — reverting a previously-busy event to Free, or vice versa.** A patch payload that doesn't include `transparency` leaves the existing value alone (patch is field-mask aware). An `events.update` payload that omits `transparency` resets it to the default `opaque` per the [update reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/update). The read-mutate-write rule (see the code block above) applies here too: an update that intended to change the title and forgot to carry `transparency` forward flips the event from Free to Busy and breaks every downstream scheduler that was treating it as available time.

A related watch-out is the `eventType` field. Events typed `outOfOffice`, `focusTime`, and `workingLocation` carry their own visibility semantics independent of `transparency` — `outOfOffice` events block invitations during the window per the [Event resource reference](https://developers.google.com/workspace/calendar/api/v3/reference/events#resource). Treat the type and the transparency as orthogonal but interacting: a `default` event with `transparency: "transparent"` is the generic "block on calendar, don't show as busy" shape; a typed event has additional side effects.

### Deep dive — conferenceData, the async Meet link, and the polling loop

Per the [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events), creating a Google Meet link is not synchronous. Three required pieces: a client-generated `requestId`, the `conferenceSolutionKey.type: "hangoutsMeet"`, and the `conferenceDataVersion=1` query parameter. The polling pattern:

```python
import json, time, uuid, urllib.request

def create_event_with_meet(token, cal_id, body):
    body["conferenceData"] = {"createRequest": {
        "requestId": str(uuid.uuid4()),             # idempotency key; persist before send so retries reuse it
        "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
    url = (f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events"
           f"?conferenceDataVersion=1&sendUpdates=all")   # version=1 required or conferenceData is silently dropped
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        event = json.loads(r.read())                # initial response: status="pending", no hangoutLink yet
    # Poll until success — exponential backoff, ~60s ceiling. Meet creation usually resolves in <5s
    delay = 1.0
    for _ in range(8):
        status = event.get("conferenceData", {}).get("createRequest", {}).get("status", {}).get("statusCode")
        if status == "success": return event        # hangoutLink + entryPoints now populated
        if status == "failure": raise MeetCreateError(event)
        time.sleep(delay); delay = min(delay * 2, 30)
        get = urllib.request.Request(
            f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events/{event['id']}",
            headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(get) as r:
            event = json.loads(r.read())
    raise MeetCreateTimeout(event)                  # bail rather than report a half-created event
```

The `requestId` is the idempotency key. If the request transiently fails and a retry sends the same `requestId`, the API recognizes the duplicate and doesn't create a second conference. Different `requestId` = different conference. Generate it client-side, persist it before sending the insert request, reuse on retry.

The cases to handle:

- **Reporting success on the initial response.** The 200 is real, but the conference is not done. The event ships with no Meet link.
- **Forgetting `conferenceDataVersion=1`.** Without the query parameter, the API silently ignores `conferenceData` in the request body. The event creates fine, but with no conference attached.
- **Mutating an event with a conference attached without re-passing `conferenceDataVersion=1`.** Same silent-strip behavior — the conference field is treated as "not supported" by the version-0 client and dropped from the update.

### Deep dive — sync tokens vs timeMin / updatedMin, and the 410 dance

For "what changed since last poll," there are two patterns and only one of them is correct.

**The wrong pattern: `updatedMin` polling.** Filter `events.list` by `updatedMin >= <last poll timestamp>`. Looks reasonable, fails in two ways: (a) deleted events disappear from the response — no way to detect a cancellation; (b) the clock-skew boundary requires hand-rolled deduplication.

**The right pattern: `syncToken`.** Per the [sync guide](https://developers.google.com/workspace/calendar/api/guides/sync), the loop is initial-full-sync → persist token → poll-with-token → handle 410 → walk pages carefully:

```python
import json, urllib.request, urllib.parse

def incremental_sync(token, cal_id, store):
    params = {"singleEvents": "true", "showDeleted": "true"}
    sync_token = store.get(cal_id)                   # None on first ever sync for this calendar
    if sync_token: params["syncToken"] = sync_token
    page_token, changes = None, []
    while True:
        if page_token: params["pageToken"] = page_token
        url = (f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events"
               f"?{urllib.parse.urlencode(params)}")
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req) as r: page = json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 410:                        # token expired (ACL changed, server rotated, etc.)
                store.pop(cal_id, None); return incremental_sync(token, cal_id, store)  # fall back to full sync
            raise
        changes.extend(page.get("items", []))        # cancelled events arrive with status="cancelled" as tombstones
        page_token = page.get("nextPageToken")
        if not page_token:
            store[cal_id] = page["nextSyncToken"]    # only the LAST page carries nextSyncToken
            return changes
```

The two gotchas the loop above handles:

- **`syncToken` is incompatible with most filters.** The [sync guide](https://developers.google.com/workspace/calendar/api/guides/sync) notes the restriction without enumerating; the full per-parameter list lives on the [events.list reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/list). `singleEvents` and `showDeleted` are sync-compatible; `q`, `timeMin`/`timeMax` after the initial sync, `iCalUID`, `privateExtendedProperty`, and `updatedMin` are not. For filtered incremental sync, run two parallel pipelines (filtered full reads + unfiltered sync) and reconcile.
- **`410 GONE` means full resync, not an error.** Sync tokens expire — per the guide: "Sometimes sync tokens are invalidated by the server, for various reasons including token expiration or changes in related ACLs." On 410, drop the persisted token and redo the initial full sync.

Pagination interacts subtly: intermediate pages have `nextPageToken` but no `nextSyncToken`. Only the last page of a multi-page sync carries the `nextSyncToken`. Code that grabs `nextSyncToken` off the first page silently misses changes on subsequent pages.

### Deep dive — expanding recurring events with `singleEvents`

`events.list` returns the series resource by default; per the [events.list reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/list), `singleEvents=true` expands the recurrence into individual instances. The difference is observable on every "what's on the calendar this week" query.

```python
import json, urllib.request, urllib.parse

def list_instances(token, cal_id, time_min, time_max):
    params = urllib.parse.urlencode({
        "timeMin": time_min, "timeMax": time_max,
        "singleEvents": "true",                  # expand RRULE into one resource per occurrence
        "orderBy": "startTime"})                 # only legal with singleEvents=true; otherwise 400
    url = f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/events?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r:
        return [e for e in json.loads(r.read())["items"]
                if e.get("status") != "cancelled"]   # filter tombstones; pass-through if caller wants them
```

Two interactions worth flagging. First, `orderBy: "startTime"` is only legal with `singleEvents=true` — call it without and the API returns `400`. Second, when sync-token incremental syncs return cancelled-instance tombstones (status `"cancelled"`), they appear alongside live instances; the consumer must filter or pass them through to the local-state delete path.

### Deep dive — `events.move` vs delete-and-recreate

Calendar exposes a first-class `events.move` operation. Per the [move reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/move), it changes the event's organizer (and therefore the calendar that owns it) without losing the event ID, history, or attendee responses. The signature: `POST /calendars/{calendarId}/events/{eventId}/move?destination={destinationCalendarId}`.

The constraints:

- Only `eventType=default` events are movable. `birthday`, `focusTime`, `fromGmail`, `outOfOffice`, and `workingLocation` events reject with 400 — explicitly enumerated in the [move reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/move).
- The source and destination calendars must both be writable by the authenticated user.
- For recurring events, `events.move` operates on the **series** — instances follow. Don't move instances individually.

Delete-and-recreate is the wrong shape when `events.move` would work. The recreate loses the event ID (any external systems holding it point at a tombstone), loses attendee response state (everyone re-receives an invitation), and re-fires notifications. Reach for `events.move` first; fall back to delete-and-recreate only when `eventType` blocks it.

### Deep dive — freeBusy for room booking and resource calendars

Workspace resource calendars (rooms, equipment) live in the Admin Console resource directory and are addressable by email like any other calendar. The booking pattern is two-step: check availability via `freebusy.query`, then invite the resource via `events.insert` with the resource email in `attendees[]`. Resources auto-accept invitations during free windows and auto-decline on conflicts.

The constraints worth naming:

- `freebusy.query` has the same 50-calendar cap as user-calendar lookups per the [freebusy.query reference](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query); chunk into batches if querying many rooms.
- Resources surface their `responseStatus` in the event's `attendees[]` array after the invite — `accepted` means booked, `declined` means a conflict the resource auto-rejected (the API returns 200 in both cases).
- Resource ACLs determine who can book; if the authenticated user lacks `writer` on the resource calendar's ACL, the invitation arrives but the auto-accept is suppressed.

### Deep dive — push channels, verification handshake, and the X-Goog headers

`events.watch` registers a push channel; per the [push guide](https://developers.google.com/workspace/calendar/api/guides/push), Google immediately confirms the registration with a sync notification, then begins delivering change notifications. Three headers carry the meaning:

- `X-Goog-Resource-State`: `sync` on the initial verification message, then `exists` (or `not_exists`) on subsequent changes.
- `X-Goog-Channel-Id`: the channel ID the caller chose at `watch` time.
- `X-Goog-Channel-Token`: an opaque caller-chosen string from the `watch` request body. Use it as a shared secret — reject any inbound webhook whose token doesn't match what was registered. Google does not validate the token itself; it just echoes whatever the caller provided.
- `X-Goog-Message-Number`: `1` on the sync message, monotonically increasing thereafter.

The verification handshake is "Google sends a request to the webhook URL with `X-Goog-Resource-State: sync` and expects an HTTP 200 response; if the URL returns non-2xx or times out, the channel is not active." The receiver pattern: on `sync`, store the channel as active and ack 200; on subsequent events, verify the `X-Goog-Channel-Token` matches the registered secret before dispatching.

### Deep dive — shared calendars and ACL writes

Per the [ACL resource reference](https://developers.google.com/workspace/calendar/api/v3/reference/acl), each calendar has an ACL list governing who can read or write it. The five roles (`none` / `freeBusyReader` / `reader` / `writer` / `owner`) and four scope types (`default` / `user` / `group` / `domain`) cover the full sharing model. Common operator pattern: grant another user `writer` so an agent acting as that user can add events to a shared team calendar.

```python
import json, urllib.request

def grant_writer(token, cal_id, user_email):
    rule = {"role": "writer", "scope": {"type": "user", "value": user_email}}
    url = f"https://www.googleapis.com/calendar/v3/calendars/{cal_id}/acl"
    req = urllib.request.Request(url, data=json.dumps(rule).encode(), method="POST",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())          # returned rule has an opaque id; persist to support later revoke
```

Two operational notes. The `id` field on the returned ACL rule is the only durable handle for `acl.delete` later; persist it if the agent ever revokes its own grant. And `acl.insert` with `scope.type: "default"` (public) fires a Workspace admin warning if your org's external-sharing policy is restrictive — most agents should never use `default` scope.

### Deep dive — service-account auth and domain-wide delegation (Calendar)

The article's snippets above assume OAuth-user auth — the agent runs with a user's access token. For production multi-user agents (one process acting on behalf of many Workspace users), the better pattern is a **service account with domain-wide delegation**: a single SA impersonates each user via the `subject` parameter, no per-user OAuth flow.

When to choose which:

- **OAuth-user** — single-user agents, desktop / interactive tools, personal `@gmail.com` accounts (DWD is Workspace-only), any context where the user explicitly consents on their own device.
- **Service account + DWD** — headless multi-user agents inside a Workspace org, scheduled background jobs that act as different users, server-side automations where per-user OAuth would be infeasible.

The setup per Google's [service-account guide](https://developers.google.com/identity/protocols/oauth2/service-account) and the [Workspace DWD admin guide](https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation):

1. Create a service account in GCP. Note the **numeric Client ID** (not the email — using the email triggers `unauthorized_client`).
2. As a Workspace super admin (required role), open Admin Console → Security → Access and data control → API Controls → Domain-wide delegation.
3. Add the SA's numeric Client ID with the exact OAuth scopes the agent will request (e.g. `https://www.googleapis.com/auth/calendar`). Propagation can take up to 24 hours per Google's guidance.
4. In code, build a credential with `subject=<user-to-impersonate>`. The SA's token then carries that user's identity.

The most common watch-out: **the SA is configured but the OAuth Client ID was never authorized in the Admin Console**, or it was authorized with the SA's email instead of the numeric Client ID. Symptom: every API call returns `unauthorized_client`. The fix is always in the Admin Console, not the code. Also worth flagging: DWD does not work for `@gmail.com` consumer accounts — it's a Workspace-only mechanism per the admin guide.

### Hard limits + workarounds — Calendar

| You want to... | Reality | Workaround |
|---|---|---|
| Mix all-day and timed in one event (`start.date` + `end.dateTime`) | API rejects with `400 invalid`. Per the [concepts doc](https://developers.google.com/workspace/calendar/api/concepts/events-calendars): "The start and end of the event must both be timed or both be all-day. For example, it is not valid to specify `start.date` and `end.dateTime`." | Two separate events, or pick one shape |
| Atomically update a recurring series AND following exceptions | The two-call split (trim `UNTIL` + insert new series) **resets any exceptions** occurring after the target instance, per the [recurring events guide](https://developers.google.com/workspace/calendar/api/guides/recurringevents) | Snapshot the exceptions via `events.instances` first, replay them onto the new series |
| Guarantee invitation delivery even with `sendUpdates=all` | The [insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert) qualifies the parameter: "Note that some emails might still be sent." Calendar-side notification settings can override in both directions | For mission-critical sends, pass `sendUpdates=all` AND fire a parallel Gmail message outside the Calendar pipeline |
| Hardcode a UTC offset in `start.dateTime` and trust it across DST | Offsets become wrong on DST transitions and political changes. Recurring events with no `timeZone` field can't be expanded reliably | Always populate `start.timeZone` with an [IANA Time Zone Database](https://www.iana.org/time-zones) ID (`America/New_York`), never `-05:00` |
| Get a guaranteed `hangoutLink` on the create-event response | `conferenceData.createRequest` is async per the [create-events guide](https://developers.google.com/workspace/calendar/api/guides/create-events): the initial response has `status: pending` and no `hangoutLink` populated | Poll `events.get` until `conferenceData.createRequest.status.statusCode == "success"` |
| Filter `events.list` by `q` + sync incrementally in one call | `syncToken` is incompatible with most filters per the [sync guide](https://developers.google.com/workspace/calendar/api/guides/sync); combining returns `400 invalidParameter` | Two parallel pipelines: filtered full-list reads, plus a separate unfiltered sync-token pipeline |
| Subscribe to push notifications indefinitely without re-registration | `events.watch` channels expire; the response carries an `expiration` field as a millisecond Unix timestamp. Per the [push guide](https://developers.google.com/workspace/calendar/api/guides/push), "there's no automatic way to renew a notification channel" | Schedule a re-watch before expiration; persist + re-issue any active `syncToken` on the new channel |
| Use an arbitrary `event.id` | `event.id` must be base32hex (lowercase `a-v` + `0-9`), 5–1024 chars, unique-per-calendar per the [Event resource reference](https://developers.google.com/workspace/calendar/api/v3/reference/events#resource); uppercase or punctuation rejects | Use `iCalUID` (RFC 5545 format) and `events.import` for cross-system event copies |
| Refetch an event using its iCalUID directly | `events.get` requires `eventId`; iCalUID lookup is via list-with-filter only per the [Events reference](https://developers.google.com/workspace/calendar/api/v3/reference/events) | `events.list?iCalUID=...` returns the matching event (or 0 results); pull `id` from the first item |
| Move a non-default event type between calendars | `events.move` rejects with 400 — only `eventType=default` is movable per the [move reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/move) | Delete + recreate as a new `default` event on the destination calendar (loses history) |
| Treat `events.update` as a partial update | The [update reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/update) is explicit: "This method does not support patch semantics and always updates the entire event resource." Omitted fields reset to default and may wipe attendees, reminders, conferenceData | Read with `events.get`, mutate the returned object in place, write it back — or use `events.patch` if partial-write semantics actually apply |
| Avoid silent overwrite on concurrent writers | Use ETag + `If-Match`. Calendar implements optimistic concurrency per the [version-resources guide](https://developers.google.com/workspace/calendar/api/guides/version-resources) | On `412 Precondition Failed`, re-read and retry |

### Patterns to avoid — Calendar

**A-C1 — Inserting attendees without `sendUpdates=all`; pass it explicitly.** Covered above. The single most common case to handle. If the `events.insert` call doesn't pass the parameter explicitly, attendees get added silently and no invitation fires.

**A-C2 — Hardcoded UTC offsets in `dateTime`; use IANA `timeZone` IDs.** `2026-06-15T10:00:00-05:00` looks fine on June 15 but in NY at that date DST is in effect (UTC-4) — so the value lands as 11am local, not 10am. Use `start.dateTime: "2026-06-15T10:00:00"` + `start.timeZone: "America/New_York"` instead. IANA IDs are the canonical names per the [IANA Time Zone Database](https://www.iana.org/time-zones).

**A-C3 — Iterating `events.instances` to do a bulk series edit; edit the series itself.** Edit the series itself, let the instance changes propagate. Looping instances generates one exception per occurrence, slows down the calendar, and floods attendees with change notifications.

**A-C4 — Treating `events.update` like patch; construct the body from a fresh `events.get`.** The update verb replaces the entire resource per the [update reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/update). Construct the payload from a fresh `events.get`, mutate the field, write the full object back. Code that builds an update body from scratch silently wipes fields it forgot to populate — including `transparency`, which flips Free events to Busy and breaks downstream schedulers.

**A-C5 — Reporting success on the initial conferenceData response; poll until success.** The Meet link is async. The `pending` state is not done. Poll until `status.statusCode == "success"` before declaring the event ready.

**A-C6 — `updatedMin` polling instead of `syncToken` for change tracking; use `syncToken`.** Misses cancellations entirely. Use `syncToken` or accept that you don't actually know what changed.

**A-C7 — Forgetting `singleEvents=true` on `events.list` when expanding recurring events; always pass it.** Per the [events.list reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/list), the default returns the series resource only; instance times and per-occurrence metadata are hidden. Symptom: a "what's happening this week" query returns one row per recurring meeting (the series) instead of N rows (the instances). Always pass `singleEvents=true` when the agent needs instance-level data, and remember `orderBy: "startTime"` requires it.

**A-C8 — Not handling `status: "cancelled"` tombstones on incremental sync; branch on `status` first.** Sync responses with `showDeleted=true` (and `singleEvents=true` for recurring instance cancellations) carry deleted events as tombstones with `status: "cancelled"`. Code that doesn't check `status` either crashes reading missing fields on the tombstone, or — worse — silently treats cancelled events as live and leaves them in the local cache. Branch on `status` first; route tombstones to the local delete path.

**A-C9 — Storing identifier state in event titles or descriptions to look up app records; use `extendedProperties.private`.** Humans rename events, breaking the lookup. Search indexes descriptions. Exports include them. Use `extendedProperties.private` for app-key state and query via `privateExtendedProperty=key=value` per the [extended properties guide](https://developers.google.com/workspace/calendar/api/guides/extended-properties).

---

## Part 10 — Operating Gmail

### What this surface unlocks — Gmail

Gmail is the surface where agent-authored outbound and inbox monitoring meet a human review loop. From the API you can draft mail a human signs off on, send plaintext or full multipart MIME (HTML + plain alternative + attachment + inline image), label by stable ID, reply in-thread so the message lands grouped on the recipient's side, monitor inbox changes via push notifications, manage filters and forwarding addresses, and operate alias sends from verified `sendAs` resources. The decisions in this Part — drafting instead of sending directly, base64url instead of standard base64, labelId instead of display name, all three threading conditions instead of just `threadId` — are what produce mail that ships when intended, threads on the recipient's side, and survives every label rename downstream.

Gmail is the fifth Workspace surface and the one where the largest gap exists between the casual API and the production API. The casual path (`messages.send` with a hand-constructed `raw` field) works for plaintext one-shot sends. Anything with HTML, attachments, threading, inline images, or "make this look like a reply" needs the production path — multipart MIME assembly per [RFC 2822](https://www.rfc-editor.org/info/rfc2822/) (which the Gmail docs cite by name; [RFC 5322](https://www.rfc-editor.org/info/rfc5322/) obsoletes 2822 with the same headers), base64url-not-base64 encoding, and label-ID-not-display-name addressing. Production bugs cluster in the gap.

### The 60-second map — Gmail

Gmail's data model is a tree of mailboxes, each containing messages grouped into threads, with labels applied to either layer. Drafts are a parallel structure that becomes a message on send.

| Resource | What it is | Addressing model |
|---|---|---|
| `Messages` | Individual emails (sent or received) | `messageId` (opaque string) |
| `Threads` | Groups of messages that hang together in the Gmail UI | `threadId` (opaque string) |
| `Drafts` | Unsent message + threadId references | `draftId` (opaque string) |
| `Labels` | The way Gmail organizes everything | `labelId` (`INBOX` / `SENT` / ... for system; opaque per-mailbox string for user labels) |
| `History` | Append-only log of mailbox changes | `historyId` (monotonic uint64) |
| `Attachments` | Binary blobs attached to messages | `attachmentId` (per-message-scoped) |

The Gmail API surface ([Gmail API v1 REST reference](https://developers.google.com/workspace/gmail/api/reference/rest)) exposes the full Users / Messages / Threads / Drafts / Labels / History / Attachments tree plus `users.settings.sendAs`, `users.settings.filters`, and `users.settings.forwardingAddresses` for mailbox-configuration management. MCP wrappers typically cover roughly a dozen high-level operations — `search_threads`, `get_thread`, `create_draft`, `list_drafts`, `list_labels`, `create_label`, `delete_label`, `update_label`, `label_message`, `label_thread`, `unlabel_*`. **One omission worth naming up front: many production agent-facing connectors deliberately omit a direct `messages.send` tool** — the human-in-the-loop pattern is `drafts.create` → human reviews → human sends. Send-capable automation needs an OAuth scope that grants send — `gmail.send` is the narrowest sufficient scope per the [scopes reference](https://developers.google.com/workspace/gmail/api/auth/scopes); `gmail.compose`, `gmail.modify`, or `mail.google.com/` also qualify — plus REST against the [messages.send reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send).

### What you can do today — Gmail capability inventory

| You want to... | Tool you reach for | Notes |
|---|---|---|
| Send a plaintext email | REST [`messages.send`](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send) with `raw` = base64url(MIME) | Requires `gmail.send` scope. Per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending), the raw field is base64url-encoded RFC 2822 |
| Draft an email for human review | REST [`drafts.create`](https://developers.google.com/workspace/gmail/api/reference/rest) | Same MIME shape as send. The recommended agent default for outbound |
| Send the draft (after human review) | `drafts.send(draftId)` | Same quota cost as `messages.send` per the [quota reference](https://developers.google.com/workspace/gmail/api/reference/quota) |
| Update an existing draft (e.g. add an attachment) | REST [`drafts.update`](https://developers.google.com/workspace/gmail/api/reference/rest) | **Full replace** — same shape as `events.update`. Omitted fields wipe; build the new MIME payload from scratch including everything that should persist |
| Search messages or threads | `messages.list` (or `threads.list`) with `q` operator string | Same syntax as the Gmail web UI: `from:`, `subject:`, `is:unread`, `has:attachment`, `newer_than:7d` ([advanced search reference](https://support.google.com/mail/answer/7190)) |
| Read a thread with all messages | `threads.get` | Returns array of messages; bodies are base64url-encoded |
| Apply a label to a message or thread | REST `messages.modify` / `threads.modify` | Pass `labelId`, NOT the display name. System label IDs are documented in the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels) |
| List all labels (to map name → ID) | REST `labels.list` | Cache the mapping — labels rarely change but every modify needs a labelId |
| Create / rename / delete a user label | `labels.create` / `labels.update` / `labels.delete` | Cannot create labels with reserved system names per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels) |
| Reply in-thread | Compose with matching `Subject` + `In-Reply-To` + `References` headers, set `threadId` on the resource | Conditions per the [threads guide](https://developers.google.com/workspace/gmail/api/guides/threads); miss any and the reply will likely land as a new thread on the recipient's side |
| Send an HTML email | Multipart MIME: `text/plain` + `text/html` alternative parts | Both parts required for client compat; HTML-only sends often penalized by spam filters. MIME shape per [RFC 2822](https://www.rfc-editor.org/info/rfc2822/) (Gmail docs' cited spec; [RFC 5322](https://www.rfc-editor.org/info/rfc5322/) is the current obsoleting standard) |
| Send with attachments | Multipart MIME: alternative parts wrapped in a `multipart/mixed` outer | Per the consumer Gmail [attachment size limits help](https://support.google.com/mail/answer/6584), personal accounts cap attachments at 25 MB; Workspace caps are admin-configurable. Base64 overhead (~37%) further reduces the practical binary-attachment ceiling — for the 25 MB consumer cap, that means a raw-binary ceiling of roughly 18 MB |
| Send from an alias address (`replies@company.com`, support inbox, etc.) | Pre-create the alias via `users.settings.sendAs.create` + verify; then set `From: <alias>` at MIME assembly time | Per the [send-as reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.sendAs), `sendAs.create` requires verification before the alias is usable. The `From` header must match a configured + verified `sendAsEmail`; mismatch returns `400` at send time |
| Manage user-level filters | REST [`users.settings.filters`](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.filters) with criteria + action | `create` / `delete` / `get` / `list`; criteria supports `from`/`to`/`subject`/`query`/`hasAttachment`/`size`; action supports `addLabelIds`/`removeLabelIds`/`forward` |
| Manage forwarding addresses | REST [`users.settings.forwardingAddresses`](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.forwardingAddresses) | `create` / `delete` / `get` / `list`; new forwarding addresses require verification before they can be used as a filter `forward` target |
| Set up push notifications on inbox changes | `users.watch` + Cloud Pub/Sub topic per the [push guide](https://developers.google.com/workspace/gmail/api/guides/push) | Watch expires after 7 days — re-watch daily or stop receiving events |
| Process changes since last notification | `history.list(startHistoryId=<from push event>)` | History retains a limited window (Google doesn't publicize the exact length); `historyNotFound` errors mean the consumer fell too far behind and must full-resync |
| Get attachment bytes | `messages.attachments.get(messageId, attachmentId)` | Returns base64url-encoded `data` field per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending)'s base64URL encoding statement (which applies symmetrically on read); decode before writing to disk |
| Batch reads of many messages | HTTP JSON batch endpoint per the [batch guide](https://developers.google.com/workspace/gmail/api/guides/batch) | Limit 100 calls per batch; "sending batches larger than 50 requests is not recommended" |

### Where to spend your time — Gmail

| # | Pattern | Why this pattern wins | Effort |
|---|---|---|---|
| 1 | **Draft, don't send: agents create drafts via `drafts.create`, humans review and click send** | Agent-authored mail goes through a human before it leaves the building. The review step catches everything the model gets wrong before it becomes a recall situation. | Low |
| 2 | **Use `urlsafe_b64encode`, not `b64encode`, for the `raw` field** | URL-safe encoding lands the `raw` field with no `+` or `/` characters; the API accepts the payload across plaintext, HTML, and binary contents identically. Standard base64 passes on simple ASCII test inputs and fails the first production HTML / binary message. | Low |
| 3 | **Address labels by ID, not display name; cache the name→ID map at app startup** | Stable IDs survive every label rename; the app keeps working through reorganizations. Display names are mutable per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels). | Low |
| 4 | **For threaded replies, set BOTH `threadId` on the resource AND `In-Reply-To` / `References` headers AND matching Subject** | The reply lands in-thread on the sender's mailbox AND on the recipient's. Per the [threads guide](https://developers.google.com/workspace/gmail/api/guides/threads), `threadId` only governs the sender's side; the RFC 2822 headers are what recipient mail clients use for grouping. | Low |
| 5 | **Pick the narrowest scope: `gmail.send` (sensitive) vs `gmail.modify` / `gmail.readonly` (restricted)** | Sensitive scopes ship faster than restricted scopes — Google's [restricted-scope verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification) gate is the difference between a one-week launch and a multi-week annual security assessment via the App Defense Alliance / CASA framework. | Medium |
| 6 | **Treat `messages.send` as a 100-quota-unit operation; budget against the [per-user 6,000 units/minute cap](https://developers.google.com/workspace/gmail/api/reference/quota)** | 60 sends/minute/user is the practical ceiling. Budgeting against it surfaces throttling before it hits production. | Low |
| 7 | **Re-watch every Pub/Sub subscription daily, not weekly** | Daily renewals give a 6-day safety margin against the 7-day hard expiration in the [push guide](https://developers.google.com/workspace/gmail/api/guides/push). Notifications never go silent. | Medium |
| 8 | **Use the `q` parameter to narrow `messages.list` at the server, not pull-then-filter client-side** | Server-side filters drop messages before they count against `messages.get` quota. Per the [quota reference](https://developers.google.com/workspace/gmail/api/reference/quota), `messages.list` is 5 units; `messages.get` is 20 — a `q` filter that drops 80% saves 4× quota on the read leg. | Low |
| 9 | **For attachments, decode `messages.attachments.get` results with base64url, not base64** | The returned `data` field is base64url per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending); the symmetric decode lands every binary correctly — PDFs readable, images clean. | Low |
| 10 | **Walk `payload.parts[]` recursively on multipart messages — don't read `payload.body.data` directly** | The recursive walk finds the body wherever it lives in the parts tree, plus every attachment. Reading `payload.body.data` directly works on single-part text only; multipart messages put the body in nested leaves. | Low |

Most readers should implement items 1–4 first. Items 5–10 matter once agents are doing bulk send, monitoring inboxes, or processing attachments.

### TL;DR — five non-obvious Gmail bits

1. **Base64 ≠ base64url.** The `raw` field on `messages.send` and the `data` field on `messages.attachments.get` are base64url-encoded per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending) — URL-safe alphabet, no `+` or `/`. Standard base64 fails on payloads containing characters that map to those symbols.
2. **Labels are addressed by ID, not display name.** System labels look like `INBOX`. User labels are opaque per-mailbox strings. The display name is not a valid `labelId` per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels).
3. **Threading needs three things.** Per the [threads guide](https://developers.google.com/workspace/gmail/api/guides/threads), an in-thread reply requires `threadId` on the resource, matching `Subject`, and `In-Reply-To` + `References` headers (per RFC 2822, which the threads guide cites by name). The first governs the sender's mailbox; the headers govern recipient-side threading.
4. **Watch expires every 7 days.** Push notifications via Pub/Sub silently stop receiving after a week without re-registration per the [push guide](https://developers.google.com/workspace/gmail/api/guides/push). Renew daily.
5. **Multipart messages put the body in `payload.parts[]`, not `payload.body.data`.** Code that always reads `payload.body.data` returns empty bodies on any HTML / attachment-bearing message. Walk the parts tree recursively; the body is in a leaf with `mimeType: "text/plain"` or `"text/html"`.

### Deep dive — multipart MIME assembly, HTML + plain-text + attachment

The `raw` field on `messages.send` is a base64URL-encoded RFC 2822 message per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending) (which states verbatim "The Gmail API requires MIME email messages compliant with RFC 2822"; [RFC 5322](https://www.rfc-editor.org/info/rfc5322/) is the obsoleting current spec, same headers). The casual plaintext case fits in five lines:

```python
import base64
from email.mime.text import MIMEText

msg = MIMEText("hello")
msg["To"] = "alice@example.com"
msg["Subject"] = "test"
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
# gmail.users().messages().send(userId="me", body={"raw": raw}).execute()
```

The production case — HTML + plain-text fallback + attachment — needs the full multipart tree. Outer `multipart/mixed` wraps `multipart/alternative` (the body) and one or more attachment parts:

```python
import base64, mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

def build_message(to, subject, plain, html, attachment_path):
    outer = MIMEMultipart("mixed")                    # outer container holds body + attachments
    outer["To"], outer["From"], outer["Subject"] = to, "me@example.com", subject
    body = MIMEMultipart("alternative")               # inner alternative: plain first, html second
    body.attach(MIMEText(plain, "plain"))             # plain MUST come first per RFC 2046 — clients pick the last viewable part
    body.attach(MIMEText(html, "html"))
    outer.attach(body)
    ctype, _ = mimetypes.guess_type(attachment_path)  # set Content-Type from filename or default to octet-stream
    maintype, subtype = (ctype or "application/octet-stream").split("/", 1)
    with open(attachment_path, "rb") as f:
        part = MIMEBase(maintype, subtype); part.set_payload(f.read())
    encoders.encode_base64(part)                      # base64-encode the binary payload (standard base64 inside the MIME — only the outer raw is base64url)
    part.add_header("Content-Disposition", "attachment", filename=attachment_path.rsplit("/", 1)[-1])
    outer.attach(part)
    return {"raw": base64.urlsafe_b64encode(outer.as_bytes()).decode()}   # outer wrap is base64url for the Gmail API
```

Three places this breaks in production.

**Watch-out 1 — Standard base64 instead of urlsafe for the outer `raw` field.** `base64.b64encode` produces `+` and `/` in its output. Both are reserved characters in URL-safe base64 per [RFC 4648 §5](https://www.rfc-editor.org/info/rfc4648/). Any non-trivial payload produces these characters in the encoded output, and the Gmail API rejects with `400 Bad Request: Invalid value for ByteString`. Simple ASCII-only test inputs may encode without producing `+` or `/` and pass; production payloads (HTML, binary attachments, longer text) will not. Always `base64.urlsafe_b64encode` (Python) / `Buffer.from(...).toString('base64url')` (Node). The Node symptom is the same — request rejected with `400 invalidArgument` — but the message wording is "Invalid base64url encoding" rather than the Python client's "Invalid value for ByteString." The symmetric watch-out on reads — calling `Base64.decode64` instead of `Base64.urlsafe_decode64` on the `raw` field returned by `messages.get(format=raw)` — is documented community-side in [googleapis/google-api-ruby-client #145](https://github.com/googleapis/google-api-ruby-client/issues/145) (community-observed).

**Watch-out 2 — HTML-only sends without a text/plain alternative.** Modern spam filters penalize HTML-only messages. The defensible shape is `multipart/alternative` with `text/plain` first and `text/html` second, per [RFC 2046](https://www.rfc-editor.org/info/rfc2046/).

**Watch-out 3 — Inline images vs attached images.** An inline image (rendering in the body) needs a `Content-ID` header on the image part AND a matching `cid:<content-id>` reference in the HTML body, per [RFC 2046 §4](https://www.rfc-editor.org/info/rfc2046/) and [RFC 2392](https://www.rfc-editor.org/info/rfc2392/). An attached image is just another `multipart/mixed` part. The two are not interchangeable. Inline-image emails missing `Content-ID` render as broken thumbnails. Use `MIMEImage` with an explicit `Content-ID` for inline; a plain attachment part for attached.

Per the consumer [attachment size limits help](https://support.google.com/mail/answer/6584), personal Gmail caps attachment size at 25 MB per message; Workspace caps are admin-configurable. Base64 MIME overhead is ~37%, so the practical binary-attachment ceiling is roughly 18 MB raw binary for the 25 MB consumer cap. Larger files should be Drive-shared with a link in the body — Gmail's web UI does this automatically; API senders must do it explicitly.

### Deep dive — threading, In-Reply-To, and the recipient-side reality

Per the [threads guide](https://developers.google.com/workspace/gmail/api/guides/threads), conditions for a reply to land in-thread on **the recipient's side**:

1. The `threadId` on the sent message resource matches the recipient's thread (governs the sender's mailbox only).
2. The `In-Reply-To` header contains the `Message-ID` of the parent message ([RFC 2822 §3.6.4](https://www.rfc-editor.org/info/rfc2822/), the spec the Gmail docs cite; same field exists in [RFC 5322](https://www.rfc-editor.org/info/rfc5322/)).
3. The `References` header contains the chain of `Message-ID` values back to the thread root.
4. The `Subject` header matches the parent (Gmail tolerates `Re:` / `Fwd:` / translated prefixes; it does NOT tolerate substantive subject changes).

The non-obvious one is that **the `threadId` only affects the sender's mailbox**. With `threadId` set but `In-Reply-To` / `References` missing, the sent message lands in-thread on the sender's Gmail but appears as a new thread on the recipient's. Same edge documented community-side in [googleapis/google-api-nodejs-client #1938](https://github.com/googleapis/google-api-nodejs-client/issues/1938) (community-observed).

The full threaded-reply payload pulls the parent's `Message-ID` and the existing `References` chain from a fresh `messages.get`, then appends the parent ID:

```python
import base64, urllib.request, json
from email.mime.text import MIMEText

def build_reply(token, user_id, parent_message_id, reply_body):
    # 1. Fetch the parent message headers to source Message-ID + References + Subject
    url = (f"https://gmail.googleapis.com/gmail/v1/users/{user_id}"
           f"/messages/{parent_message_id}?format=metadata"
           "&metadataHeaders=Message-ID&metadataHeaders=References&metadataHeaders=Subject")
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as r: parent = json.loads(r.read())
    headers = {h["name"]: h["value"] for h in parent["payload"]["headers"]}
    parent_id = headers["Message-ID"]                    # literal header name; some servers send Message-Id with lowercase d
    refs = headers.get("References", "") + " " + parent_id      # chain back to root; whitespace separator per RFC 2822
    # 2. Build the reply MIME with the threading headers populated
    msg = MIMEText(reply_body)
    msg["Subject"] = headers["Subject"] if headers["Subject"].startswith("Re:") else "Re: " + headers["Subject"]
    msg["In-Reply-To"] = parent_id                       # the load-bearing header for recipient-side threading
    msg["References"] = refs.strip()
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    return {"raw": raw, "threadId": parent["threadId"]}  # threadId governs the sender's mailbox; headers govern the recipient's
```

The literal header name returned in `payload.headers` is `Message-ID` (some mail servers emit `Message-Id`; treat the lookup as case-insensitive). The threadId is on the parent message resource.

### Deep dive — send-as aliases and the From header

Sending "from" an alias address (e.g. `replies@company.com` aliased to a real account) needs two pieces. First, the alias must exist as a `sendAs` resource on the user's settings, created via `users.settings.sendAs.create` and verified per the [send-as reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.sendAs). Verification fires a confirmation email to the alias address and blocks send until accepted. Second, the MIME `From` header at send time must exactly match a configured + verified `sendAsEmail` — mismatch returns `400` at send.

The pattern works in three steps: `sendAs.create` once (admin op), wait for `verificationStatus == "accepted"`, then set `msg["From"] = "<alias-address>"` at MIME assembly. The `displayName` on the `sendAs` resource is what renders in the recipient's "From" column; it's settable independently from the underlying address.

### Deep dive — filters and forwarding management

Gmail's user-level filters live under `users.settings.filters`; forwarding addresses live under `users.settings.forwardingAddresses`. Both are per-user resources, queried/mutated by the authenticated user (or a SA with DWD impersonating that user).

Filter shape per the [filters reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.filters): `criteria` selects the messages, `action` decides what happens. Criteria fields include `from`, `to`, `subject`, `query` (the same `q` syntax as `messages.list`), `hasAttachment`, `size`, `sizeComparison`. Action fields include `addLabelIds`, `removeLabelIds`, `forward` (the forwarding-address email — which must be pre-created and verified). Operators building inbox-automation tools commonly use filters to auto-label inbound by sender domain, or to forward specific categories to a triage inbox.

Forwarding addresses per the [forwardingAddresses reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.forwardingAddresses) follow the same create-then-verify pattern as send-as aliases. `create` fires a verification email; `verificationStatus` flips from `pending` to `accepted` once the recipient confirms. Filters can only `forward` to addresses already in `accepted` state — referring to a `pending` address in a filter returns `400`.

### Deep dive — `messages.send` vs `messages.insert` vs `messages.import`

Three Gmail methods place a message into a mailbox; only one actually delivers to recipients. Picking the wrong one breaks migration and archival agents.

| Method | What it does | When to reach for it |
|---|---|---|
| `messages.send` | Standard outbound delivery: the API processes the MIME, signs / routes / delivers via SMTP | Any normal "send an email" path; this is the only one that delivers to external recipients |
| `messages.insert` | Per the [insert reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/insert): "directly inserts a message into only this user's mailbox similar to `IMAP APPEND`, bypassing most scanning and classification. **Does not send a message.**" | Archival imports where the message is already a record of something that happened; restoring from a backup; building a local mailbox snapshot |
| `messages.import` | Per the [import reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/import): "Imports a message into only this user's mailbox, with standard email delivery scanning and classification similar to receiving via SMTP." Also does not send — only the importing user sees it | Migration agents bringing mail from another provider, where spam/inbox classification needs to run as if the message had arrived via SMTP |

The watch-out: an agent meant to deliver outbound mail that reaches for `import` or `insert` puts the message in the sender's own mailbox and **never delivers it to the recipient**. The sender sees the message in Sent (or wherever it was inserted) and the recipient never gets it. Reach for `send` unless explicitly building an archival or migration path.

### Deep dive — bounce handling and the MAILER-DAEMON pattern

Gmail does not expose RFC 8098 Message Disposition Notifications or per-recipient delivery state — "send succeeded" only means "the message left the API." When a recipient's mailbox is full, the domain is dead, or the address doesn't exist, the bounce arrives as **a new inbound message** from `MAILER-DAEMON@googlemail.com` (or the equivalent at the bouncing provider). Agents that need to know about delivery failures have to parse the bounce themselves.

The detection pattern: monitor the inbox via `users.watch` + `history.list`, and on each new message check the `From:` header for `MAILER-DAEMON` and the `X-Failed-Recipients:` header for the original recipient. The `Auto-Submitted: auto-replied` header is a common ([RFC 3834](https://www.rfc-editor.org/info/rfc3834/)) signal that the message is automated and not from a human, useful for auto-classifying bounces vs vacation responders. The bounce body itself usually contains a `Diagnostic-Code:` header from the bouncing server with an SMTP-style reason code (`550 5.1.1` = address doesn't exist, `552 5.2.2` = mailbox full, etc.).

The minimum-viable bounce handler reads the `X-Failed-Recipients:` header, looks up the originally-sent message by `Message-ID` (carried in the bounce's `References:` chain), and marks the local delivery state as `bounced`. Don't rely on Subject heuristics alone — `Subject: Mail Delivery Subsystem` is conventional but providers vary.

### Deep dive — system labels vs user labels, and the addressing rule

Gmail's label model has two tiers per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels):

**System labels** — reserved IDs, all uppercase, fixed set per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels): `INBOX`, `SENT`, `DRAFT`, `TRASH`, `SPAM`, `IMPORTANT`, `STARRED`, `UNREAD`, plus the category labels (`CATEGORY_PERSONAL`, `CATEGORY_SOCIAL`, `CATEGORY_PROMOTIONS`, `CATEGORY_UPDATES`, `CATEGORY_FORUMS`). These cannot be created, renamed, or deleted. Some apply automatically (`SENT`, `DRAFT`); others are user-applicable (`INBOX`, `STARRED`, `IMPORTANT`).

**User labels** — created via `labels.create`, returned with opaque IDs. The display name is mutable; the ID is stable. Folders are user labels too — Gmail conflates folder and label semantics via the `messageListVisibility` and `labelListVisibility` fields on the label resource.

**The addressing rule: pass labelId, never displayName.** `messages.modify(messageId, addLabelIds=["INBOX"])` works. `messages.modify(messageId, addLabelIds=["Inbox"])` returns `400 invalidArgument` (case-sensitive). `messages.modify(messageId, addLabelIds=["my-followups"])` returns 400 regardless of casing — the API has no name-to-ID lookup, the lookup is the caller's job.

The production pattern: `labels.list` once at startup, build a `{name: labelId}` map, pass `labelId` at modify time. Refresh the map on any label-create / label-update / label-delete performed in the same process.

Two more subtle bits:

- `threads.modify` applies the label to every existing message in the thread but per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels), "newly added messages won't inherit previously applied labels" — a new message later in the thread doesn't auto-inherit.
- Drafts can't be labeled. `messages.modify` on a draft message returns `400`. Send the draft, then label the resulting message.

### Deep dive — push notifications, history IDs, and the polling-fallback dance

Gmail push works through Cloud Pub/Sub per the [push guide](https://developers.google.com/workspace/gmail/api/guides/push). The lifecycle:

```
1. Create a Pub/Sub topic in your GCP project
2. Grant gmail-api-push@system.gserviceaccount.com publish rights on the topic
3. Call users.watch with topicName + (optional) labelIds + labelFilterBehavior
4. Watch response: { historyId: "12345", expiration: "1684886400000" }  // 7 days from now
5. Persist historyId per user
6. On every inbound Pub/Sub message:
   history.list(startHistoryId=<persisted>) to enumerate every change since last poll
7. Re-call users.watch before expiration — recommended daily, hard limit 7 days
```

The cases to handle:

**Case 1 — watch expires silently.** Per the [push guide](https://developers.google.com/workspace/gmail/api/guides/push): "You must call the watch at least once every 7 days or you'll stop receiving updates for the user. We recommend calling watch once per day." No warning, no inbound failure event, just silence. The defensive pattern is daily re-watch via a scheduled job — gives a 6-day safety margin.

**Case 2 — historyId out of range.** Gmail retains history for a limited window (Google does not publicize the exact length). If the consumer falls behind (process crashes, queue backed up, debugger pause), `history.list(startHistoryId=<too old>)` returns `404 historyNotFound`. Recovery: drop the persisted ID, full-sync the mailbox via `messages.list`, persist the new `historyId` from the most-recent message.

**Case 3 — Pub/Sub delivery is at-least-once by default.** Per the [Cloud Pub/Sub exactly-once delivery documentation](https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery), exactly-once is an opt-in feature on pull subscriptions only; default delivery (including push) is at-least-once. A handler may see the same notification twice and must be idempotent — keyed on the `(history.id, message.id, change_type)` triple from `history.list`, not on the Pub/Sub event ID.

**Case 4 — watch's labelFilter doesn't filter `history.list`.** `users.watch(labelIds=["INBOX"], labelFilterBehavior="INCLUDE")` filters which changes generate notifications. Once `history.list(startHistoryId=...)` is called, the returned change list spans ALL labels in that window regardless of the watch's filter. Filter history results client-side.

### Deep dive — search syntax, quota costs, and the read-cheap pattern

Gmail's `q` parameter on `messages.list` accepts the same syntax as the web UI's advanced search per the [advanced search reference](https://support.google.com/mail/answer/7190):

| Operator | Meaning |
|---|---|
| `from:alice@example.com` | Messages from this address |
| `to:bob@example.com` | Messages to this address |
| `subject:"Q2 plan"` | Subject contains this exact phrase |
| `label:followups` | Carries this label (display name is allowed in `q` — distinct from `modify`, which requires labelId) |
| `is:unread` / `is:read` / `is:starred` / `is:important` | State flags |
| `has:attachment` | Has any attachment |
| `filename:pdf` | Has an attachment with this extension or filename |
| `newer_than:7d` / `older_than:30d` | Relative date |
| `after:2026/01/01` / `before:2026/02/01` | Absolute dates |
| `in:sent` / `in:inbox` / `in:trash` | Folder/label shorthand |
| `-from:noreply@` | Exclude (negation) |
| `{from:a OR from:b}` | Braces = OR |
| space between terms | Implicit AND |

Key non-SQL constraints:

- No parentheses for grouping. Grouping is via braces, and only for OR.
- No general boolean nesting. `(from:a AND subject:b) OR (from:c AND subject:d)` has no direct equivalent — run two queries and union client-side.
- Phrases with spaces need double quotes. `subject:"Q2 plan"` matches the literal phrase; `subject:Q2 plan` parses as `subject:Q2 AND plan`.
- Dates use `YYYY/MM/DD` form per the [advanced search reference](https://support.google.com/mail/answer/7190): `after:2026/01/01`, `before:2026/02/01`. Relative forms (`newer_than:7d`) are also supported.

**Quota costs.** Per the [Gmail quota reference](https://developers.google.com/workspace/gmail/api/reference/quota), representative method costs:

| Method | Cost (quota units) |
|---|---|
| `messages.list` | 5 |
| `messages.get` | 20 |
| `messages.send` | 100 |
| `drafts.create` | 10 |
| `drafts.send` | 100 |
| `messages.modify` | 5 |
| `labels.list` | 1 |
| `labels.get` | 1 |

Per-user cap is 6,000 quota units per minute per project. A naïve "list 500 messages, read each one" pipeline costs 5 + 500×20 = 10,005 units — over the per-user-minute cap. Mitigations: tight `q` filter to reduce list cardinality; request `format: "metadata"` or `format: "minimal"` on `messages.get` when full body isn't needed; use `messages.batchModify` / `messages.batchDelete` for bulk label operations (one call instead of N modifies). The batch endpoint per the [batch guide](https://developers.google.com/workspace/gmail/api/guides/batch) accepts up to 100 calls in one HTTP request (50 recommended) and reduces connection overhead but each call still counts individually against quota.

### Deep dive — scopes and the restricted-scope verification gate

Gmail's OAuth scope hierarchy per the [Gmail API OAuth scopes reference](https://developers.google.com/workspace/gmail/api/auth/scopes):

| Scope | Capability | Verification posture |
|---|---|---|
| `gmail.labels` | Read/write label resources only | Non-sensitive |
| `gmail.send` | Send mail; no read | Sensitive. Per the [restricted-scope verification doc](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification), the CASA security-assessment gate is documented as applying to Restricted scopes; Sensitive scopes like `gmail.send` are not covered by that gate (inference from scope-of-the-doc, not an explicit exemption statement) |
| `gmail.metadata` | Read message metadata (headers, no body) | Restricted |
| `gmail.readonly` | Read all mail | Restricted |
| `gmail.modify` | Read + write labels + delete | Restricted |
| `gmail.compose` | Compose, read drafts, send | Restricted |
| `gmail.insert` | Add to mailbox without sending (e.g. import) | Restricted |
| `https://mail.google.com/` | Full access — read, write, send, permanently delete | Restricted; highest scrutiny. Easiest scope to copy from old examples and the most expensive to ship — if the app needs read + label + send, `gmail.modify` + `gmail.send` is materially cheaper to verify |

Per the [restricted-scope verification documentation](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification), apps requesting restricted scopes for **external** use must undergo a security assessment "through the App Defense Alliance and cloud application security assessment framework (CASA)" — an annual review by an approved lab. The verification doc addresses only Restricted scopes; Sensitive scopes like `gmail.send` are not within its scope, so a send-only app appears to skip the CASA assessment gate (inference from the verification-doc's stated scope, not an explicit Sensitive-exemption statement).

**Internal-only apps skip the assessment entirely.** Per the [restricted-scope verification doc](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification), apps configured as "Internal" in the OAuth consent screen (same-Workspace-org users only) don't go through restricted-scope review. Building for internal use only is the fastest path to production.

### Deep dive — service-account auth and domain-wide delegation (Gmail)

The same OAuth-user vs service-account-DWD choice exists for Gmail as for Calendar. The decision rule is the same: single-user / interactive / consumer accounts use OAuth-user; multi-user Workspace-internal agents use SA + DWD.

The setup is mostly identical to the Calendar walkthrough per Google's [service-account guide](https://developers.google.com/identity/protocols/oauth2/service-account) and the [DWD admin guide](https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation), with two Gmail-specific points:

- **Scope grants matter exactly.** The Admin Console DWD entry authorizes the SA for specific scopes only. Adding `https://www.googleapis.com/auth/gmail.send` does NOT also authorize `gmail.modify` — every scope the agent uses must be listed. Mismatch returns `unauthorized_client` with no helpful message about which scope is missing.
- **The `subject` parameter is the impersonated user's email.** Gmail-via-DWD acts as that user — the resulting tokens are scoped to their mailbox, watch channels register on their mailbox, etc. The SA itself has no mailbox; calls without `subject` return 400.

The same most-common watch-out as Calendar applies: the Admin Console authorization step is easy to skip ("the SA exists in GCP, why is auth failing?"). Verify in the Admin Console under Security → Access and data control → API Controls → Domain-wide delegation that the SA's numeric Client ID (not email) is listed with the exact scopes the agent requests. Propagation can take up to 24 hours.

DWD does not work for consumer `@gmail.com` accounts — it's a Workspace-only mechanism. For consumer Gmail, OAuth-user is the only option.

### Hard limits + workarounds — Gmail

| You want to... | Reality | Workaround |
|---|---|---|
| Send a large attachment past the account's size cap | API rejects once the encoded payload exceeds the account's per-message cap. Per the consumer [attachment size limits help](https://support.google.com/mail/answer/6584), personal Gmail caps at 25 MB per message; Workspace caps are admin-configurable. Base64 overhead (~37%) reduces the practical binary-attachment ceiling further — ~18 MB raw binary for the 25 MB consumer cap | Drive-share the file, link it in the body; or use the Workspace SMTP relay for higher caps |
| Reply in-thread by passing only `threadId` on the resource | Per the [threads guide](https://developers.google.com/workspace/gmail/api/guides/threads), three conditions must all hold: `threadId` on the resource, `References` + `In-Reply-To` headers per [RFC 2822](https://www.rfc-editor.org/info/rfc2822/) (the spec the Gmail docs cite by name), and a matching `Subject` | Set `threadId` AND populate `In-Reply-To`/`References` AND keep `Subject` matching (with or without `Re:` prefix) |
| Apply a user label by display name | Labels are addressed by ID per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels). Display names are mutable; IDs are stable. Passing a display name returns `400 invalidArgument` | `labels.list` once at app startup, build a name→ID map, pass IDs at write time |
| Apply a label to a draft | Per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels): "You can't apply labels to draft messages" | Send the draft, then apply the label to the resulting message (or rely on the system `DRAFT` label) |
| Base64-encode the MIME with standard `base64` | Per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending), the `raw` field requires base64url (URL-safe alphabet: `-` / `_` instead of `+` / `/`, optional `=` padding stripped). Standard base64 fails because its `+` / `/` characters are not in the URL-safe alphabet; encoding any non-trivial payload produces these characters and the API rejects with `400 invalidArgument`. The symmetric decode-side watch-out exists on reads (see [googleapis/google-api-ruby-client #145](https://github.com/googleapis/google-api-ruby-client/issues/145) — community-observed decoding bug on `messages.get` with `format=raw`) | Always `base64.urlsafe_b64encode()` (Python) / `Buffer.toString('base64url')` (Node) |
| Exceed Workspace daily-send caps from a regular Gmail account | Daily-send caps are enforced at the account level per the [Workspace sending limits documentation](https://knowledge.workspace.google.com/admin/gmail/gmail-sending-limits-in-google-workspace). Exceeding triggers a temporary lockout | SMTP relay for transactional volume; user-bound API for human-paced sends |
| Use `q` filters with sync via `historyId` | `history.list` only accepts `startHistoryId` — no `q` overlay. History is "everything that changed" | Two pipelines: poll history for change detection, hit `messages.get` for each, filter at read |
| Use full boolean nesting in `q` | Per the [advanced search reference](https://support.google.com/mail/answer/7190), `q` supports implicit AND (space), brace-grouped OR (`{from:a from:b}`), and prefix-negation (`-from:c`). No general parens or nesting | Run multiple queries client-side and union results, or accept the limited grammar |
| Edit a sent message after sending | Sent messages are immutable; there is no `messages.update` in the [Gmail API v1 reference](https://developers.google.com/workspace/gmail/api/reference/rest) | Send a follow-up correction or use Workspace admin recall (not API-driven) |
| Subscribe to push notifications indefinitely without re-registration | `watch` expires; per the [push guide](https://developers.google.com/workspace/gmail/api/guides/push): "You must call the watch at least once every 7 days or you'll stop receiving updates" | Cron-schedule daily re-watch; persist `historyId` from the last event so the new watch picks up where the old one left off |
| Read message bodies in bulk without N round-trips | `messages.list` returns IDs only. Each `messages.get` is a separate call per the [quota reference](https://developers.google.com/workspace/gmail/api/reference/quota) | Use `format: "metadata"` to avoid pulling full body when only headers are needed; batch via the [JSON batch endpoint](https://developers.google.com/workspace/gmail/api/guides/batch) |
| Get a guaranteed delivery receipt | Gmail does not expose RFC 8098 Message Disposition Notifications or per-recipient delivery state in the public API | None — accept that "send succeeded" only means "the message left the API"; bounces arrive as inbound messages (see the bounce-handling deep dive above) |

### Patterns to avoid — Gmail

**A-G1 — Using `base64` instead of `base64url`; always `urlsafe_b64encode`.** The most common Gmail-from-automation case to handle. Standard base64 contains `+` and `/`, which break the URL-safe encoding the API expects per the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending). Symptom: intermittent `400 Bad Request: Invalid value for ByteString` errors. Course-correct to `urlsafe_b64encode` (Python) / `base64url` (Node).

**A-G2 — Addressing labels by display name; maintain a name→ID map at startup.** `addLabelIds=["My Followups"]` returns 400 per the [labels guide](https://developers.google.com/workspace/gmail/api/guides/labels). The API has no display-name lookup. Maintain a name→ID map at app startup.

**A-G3 — Setting `threadId` without `In-Reply-To` and `References`; populate both headers from the parent's `Message-ID`.** Per the [threads guide](https://developers.google.com/workspace/gmail/api/guides/threads), all three conditions must hold for in-thread display on the recipient's side; `threadId` alone governs only the sender's mailbox. Always populate the RFC 2822 headers from the parent message's `Message-ID`.

**A-G4 — Letting an agent fire `messages.send` without human review; use `drafts.create` + human send.** A draft + human send loop avoids the worst-case agent-authored outbound. The pattern is `drafts.create` → human reviews → human sends.

**A-G5 — Polling `messages.list` instead of `history.list` for change detection; use history + watch.** `messages.list` returns all messages in the inbox; `history.list` returns only what changed per the [push guide](https://developers.google.com/workspace/gmail/api/guides/push). For monitoring tasks, history + watch is dramatically cheaper.

**A-G6 — Hand-rolling MIME boundaries via string concatenation; use the language's MIME library.** Boundary mismatch produces messages that render in some clients (Gmail web UI) and break in others (Outlook, Apple Mail). Use the language's MIME library (`email.mime` in Python, `nodemailer` in Node) and never hand-write boundary strings.

**A-G7 — Forgetting that watch expires every 7 days; schedule a daily re-watch.** Schedule a daily re-watch; persist `historyId` to bridge across the renewal.

**A-G8 — Reading `payload.body.data` on a multipart message instead of walking `payload.parts[]` recursively; walk the tree.** Multipart `messages.get` puts the actual body inside the leaf parts (`payload.parts[].body.data`, possibly nested), not `payload.body.data` at the top. Code that assumes the latter returns empty bodies on HTML / attachment-bearing messages and misses attachments entirely. Symptom: agent sees empty mail or no attachments where the Gmail web UI shows full content. Walk the parts tree until the leaf with `mimeType: "text/plain"` or `"text/html"` is found; attachment bytes live in a separate `messages.attachments.get` call keyed on the part's `attachmentId`.

**A-G9 — Using `internalDate` when the operator means the user's `Date:` header; parse the `Date:` header from `payload.headers`.** Per the Gmail API, `internalDate` is server-side receive time in milliseconds since epoch — useful for the receiving mailbox's view but not for the sender's local-time perspective. When an agent reports "this message was sent at 9am" from `internalDate`, users in different timezones see the wall-clock shifted by the offset between the server and the user's zone. Symptom: time-zone-shifted timestamps in reports. For user-perspective time, parse the `Date:` header from `payload.headers` (RFC 2822 format) instead.

---

## Machine-readable identity (this article's own schema)

This article applies the [Marketing to Agents](marketing-to-agents.md) playbook to itself — JSON-LD `Article` schema is auto-emitted in `<head>` by the repository's Jekyll `_includes/head-custom.html` whenever a guide carries `agent_friendly: true` in its frontmatter (this one does). Agents indexing the rendered HTML at [watsonrm.github.io/rmwcommerce](https://watsonrm.github.io/rmwcommerce/guides/operating-google-workspace-from-claude.html) see a typed `Article` with author `sameAs` references to Rick's LinkedIn, X, GitHub, and Watson Weekly profiles; publisher `Organization` is RMW Commerce Consulting; license is CC BY-NC-ND 4.0. Agents fetching the raw markdown see the equivalent metadata in the YAML frontmatter at the top of this file.

---

## Sources & Attribution

This guide synthesizes patterns and case handling from running Google Drive + Docs automation in production through 2025–2026. The source taxonomy applied throughout: **capability > workaround > pattern**. Every limit is paired with the workaround that closes it, and every pattern names the case it makes routine.

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
- [TextStyle reference (JavaDoc)](https://googleapis.dev/java/google-api-services-docs/latest/com/google/api/services/docs/v1/model/TextStyle.html) — confirms the `bold` + `weightedFontFamily` interaction documented in Pattern 2's "weight 400 even when bold: true" case
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
- [Domain-wide delegation (Admin Help)](https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation) — how to authorize a service account to impersonate Workspace users

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

### Google Calendar — primary references

- [Calendar API v3 reference](https://developers.google.com/workspace/calendar/api/v3/reference) — resource catalog: Acl, CalendarList, Calendars, Channels, Colors, Events, Freebusy, Settings.
- [Events resource reference](https://developers.google.com/workspace/calendar/api/v3/reference/events) — event types (`default`, `birthday`, `focusTime`, `fromGmail`, `outOfOffice`, `workingLocation`), transparency, eventId / iCalUID; iCalUID lookup via `events.list`.
- [events.insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/insert) — `sendUpdates` enum values and the documented default (`false` — behaves like `none`); `conferenceDataVersion` parameter shape; `externalOnly` defined as "non-Google Calendar guests."
- [events.update reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/update) — "always updates the entire event resource" full-replace semantics.
- [events.list reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/list) — `singleEvents=true` expansion behavior, `orderBy: "startTime"` requiring `singleEvents=true`, the canonical place to look up which filters break incremental sync.
- [events.move reference](https://developers.google.com/workspace/calendar/api/v3/reference/events/move) — explicit `default`-only event-type restriction.
- [ACL resource reference](https://developers.google.com/workspace/calendar/api/v3/reference/acl) and [acl.insert reference](https://developers.google.com/workspace/calendar/api/v3/reference/acl/insert) — the five roles (`none`/`freeBusyReader`/`reader`/`writer`/`owner`) and four scope types (`default`/`user`/`group`/`domain`) governing per-calendar access.
- [Events & Calendars concepts](https://developers.google.com/workspace/calendar/api/concepts/events-calendars) — "both timed or both all-day" rejection rule and event-type taxonomy.
- [Recurring events guide](https://developers.google.com/workspace/calendar/api/guides/recurringevents) — RRULE / RDATE / EXDATE semantics, the "this and following" two-call procedure, and the documented warning against individual-instance edits as a backdoor series edit.
- [Create events guide](https://developers.google.com/workspace/calendar/api/guides/create-events) — `conferenceData.createRequest` async flow and the `pending` / `success` state machine.
- [Extended properties guide](https://developers.google.com/workspace/calendar/api/guides/extended-properties) — 44-char keys, 1024-char values, 300 properties per event, 32 KB total.
- [Sync token guide](https://developers.google.com/workspace/calendar/api/guides/sync) — `nextSyncToken` lifecycle, `410 GONE` resync semantics, filter-incompatibility rule, multi-page pagination.
- [Push notifications guide (Calendar)](https://developers.google.com/workspace/calendar/api/guides/push) — `events.watch` channel expiration, sync verification handshake (`X-Goog-Resource-State: sync`), `X-Goog-Channel-Token` validation pattern, "no automatic way to renew a notification channel."
- [Calendar API batch guide](https://developers.google.com/workspace/calendar/api/guides/batch) — `https://www.googleapis.com/batch/calendar/v3` endpoint, 1000-call hard cap, per-call quota accounting.
- [Freebusy query reference](https://developers.google.com/workspace/calendar/api/v3/reference/freebusy/query) — 50-calendar cap (`calendarExpansionMax`) and busy-interval format.
- [Get specific versions of resources](https://developers.google.com/workspace/calendar/api/guides/version-resources) — ETag / `If-Match` / 412 optimistic-concurrency semantics for Event reads.
- [RFC 5545 — Internet Calendaring and Scheduling Core Object Specification (iCalendar)](https://www.rfc-editor.org/info/rfc5545/) — RRULE / RDATE / EXDATE syntax used in the Calendar API `recurrence` field; canonical reference for iCalUID format.
- [IANA Time Zone Database](https://www.iana.org/time-zones) — canonical IANA zone names (`America/New_York`, etc.) required by `start.timeZone` in the Calendar API.

### Gmail — primary references

- [Gmail API v1 REST reference](https://developers.google.com/workspace/gmail/api/reference/rest) — full resource catalog: Users, Messages, Threads, Drafts, Labels, History, Attachments, plus `users.settings.*` for sendAs / filters / forwardingAddresses.
- [messages.send reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/send) — `raw` field shape and base64url requirement.
- [messages.insert reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/insert) — IMAP-APPEND-like direct insertion that does not deliver.
- [messages.import reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages/import) — SMTP-style spam classification on import that still does not deliver to external recipients.
- [Sending mail guide](https://developers.google.com/workspace/gmail/api/guides/sending) — base64URL encoding requirement, RFC 2822 compliance for MIME messages, multipart MIME assembly.
- [Gmail attachment size limits (consumer help)](https://support.google.com/mail/answer/6584) — 25 MB cap on personal Gmail; Workspace caps are admin-configurable.
- [Manage threads guide](https://developers.google.com/workspace/gmail/api/guides/threads) — the three conditions for in-thread reply (`threadId` + RFC 2822 headers + matching Subject); cites RFC 2822 by name.
- [Manage labels guide](https://developers.google.com/workspace/gmail/api/guides/labels) — system labels vs user labels, thread vs message label inheritance, draft-labeling restriction.
- [users.settings.sendAs reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.sendAs) — send-as alias resource, verification workflow, `From`-header binding.
- [users.settings.filters reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.filters) — user-level filter criteria and actions; `addLabelIds` / `removeLabelIds` / `forward`.
- [users.settings.forwardingAddresses reference](https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.settings.forwardingAddresses) — forwarding-address create-then-verify pattern referenced by filter `forward` actions.
- [Advanced search syntax (consumer docs)](https://support.google.com/mail/answer/7190) — canonical reference for `from:` / `to:` / `subject:` / `is:` / `has:` / `newer_than:` / etc.
- [Push notifications guide (Gmail)](https://developers.google.com/workspace/gmail/api/guides/push) — Pub/Sub topic setup, `users.watch`, the 7-day expiration rule.
- [Batch request guide (Gmail)](https://developers.google.com/workspace/gmail/api/guides/batch) — JSON batch endpoint, 100-call hard cap (50 recommended).
- [Gmail API OAuth scopes reference](https://developers.google.com/workspace/gmail/api/auth/scopes) — full scope hierarchy with verification posture per scope.
- [Gmail API usage limits / quota reference](https://developers.google.com/workspace/gmail/api/reference/quota) — quota-unit costs, 6,000-units-per-minute per-user cap.
- [Workspace sending limits](https://knowledge.workspace.google.com/admin/gmail/gmail-sending-limits-in-google-workspace) — per-account daily send caps for Workspace and SMTP relay.
- [Cloud Pub/Sub exactly-once delivery documentation](https://docs.cloud.google.com/pubsub/docs/exactly-once-delivery) — clarifies that default delivery is at-least-once and exactly-once is an opt-in feature on pull subscriptions, so push-subscription handlers must be idempotent.
- [RFC 2822 — Internet Message Format](https://www.rfc-editor.org/info/rfc2822/) — the message-format spec the Gmail docs cite by name for `In-Reply-To` / `References` / `Message-ID` / `Subject` header syntax.
- [RFC 5322 — Internet Message Format](https://www.rfc-editor.org/info/rfc5322/) — obsoletes RFC 2822; same headers, current canonical Internet Message Format spec.
- [RFC 2046 — Multipurpose Internet Mail Extensions Part Two: Media Types](https://www.rfc-editor.org/info/rfc2046/) — `multipart/alternative` and `multipart/mixed` container semantics.
- [RFC 2392 — Content-ID and Message-ID Uniform Resource Locators](https://www.rfc-editor.org/info/rfc2392/) — `cid:` URI scheme for inline-image references in HTML mail bodies.
- [RFC 3834 — Recommendations for Automatic Responses to Electronic Mail](https://www.rfc-editor.org/info/rfc3834/) — `Auto-Submitted:` header semantics for distinguishing automated mail from human mail.
- [RFC 4648 — The Base16, Base32, and Base64 Data Encodings](https://www.rfc-editor.org/info/rfc4648/) — §5 defines the URL-safe (base64url) alphabet required by Gmail's `raw` field.

### Authentication — Calendar and Gmail (service accounts + DWD)

- [Using OAuth 2.0 for server-to-server applications (service accounts)](https://developers.google.com/identity/protocols/oauth2/service-account) — service-account creation, the `subject` impersonation parameter, the numeric Client ID requirement, and the `unauthorized_client` failure mode when the Admin Console authorization step is missed.
- [Control API access with domain-wide delegation (Workspace Admin)](https://knowledge.workspace.google.com/admin/apps/control-api-access-with-domain-wide-delegation) — super-admin role requirement, the Admin Console path (Security → Access and data control → API Controls → Domain-wide delegation), per-scope authorization, and propagation timing. (URL updated from the original `support.google.com/a/answer/162106`, which now redirects here.)

### Community-observed (Tier 3 — use only as additional evidence)

- [googleapis/google-api-ruby-client #145](https://github.com/googleapis/google-api-ruby-client/issues/145) — symmetric decode-side base64url bug on `messages.get` with `format=raw` (calling `Base64.decode64` instead of `Base64.urlsafe_decode64`). Community-observed; the authoritative source is the [sending guide](https://developers.google.com/workspace/gmail/api/guides/sending).
- [googleapis/google-api-nodejs-client #1938](https://github.com/googleapis/google-api-nodejs-client/issues/1938) — threading-headers gotcha. Community-observed; the authoritative source is the [threads guide](https://developers.google.com/workspace/gmail/api/guides/threads).
- [Restricted-scope OAuth verification](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification) — App Defense Alliance / CASA security-assessment gate for external apps requesting restricted scopes.

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

The patterns and patterns-to-avoid documented here emerged from real production cases across 2025–2026. Each was caught the first time by a human, fixed once, and lifted into the writer agent's playbook so it cannot recur silently. The article is the public form of that playbook.
