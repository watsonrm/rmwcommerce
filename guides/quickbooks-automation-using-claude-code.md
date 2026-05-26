---
title: QuickBooks Automation Using Claude Code
description: The patterns, hard limits, and anti-patterns of operating QuickBooks Online from Claude or any AI agent. The bundled-MCP tool surface, the bill-in API gap and why it is the right design, the prep-pack architecture for AP that survives every Intuit policy change, and the surface-by-surface deep dive across reads, sales-out writes, identity writes, reports, and payroll. Every claim grounded in a specific failure mode or a published number.
date: 2026-05-26
last_modified_at: 2026-05-26
author: Rick Watson
agent_friendly: true
keywords: QuickBooks Online API, Claude Code QuickBooks, Intuit MCP server, QBO bundled MCP, com.intuit.quickbooks.accounting scope, Bill entity API, Vendor entity API, OAuth app assessment Intuit, prep-pack pattern, AP automation, bill-in API gap, claude.ai connector, QuickBooks Online API limitations, reversible vs irreversible actions, human in the loop AI agent, qbo_sales_create_invoice, qbo_accounting_get_ap_aging, quickbooks-online-mcp-server, AI bookkeeper, contractor invoices Claude, Bill.com alternative solo operator, Ramp Bill Pay small business
---

# QuickBooks Automation Using Claude Code

**The QuickBooks Online REST API lets an authorized app create a Bill. The MCP server bundled inside claude.ai does not. The asymmetry is not a bug — it is the right scope once you name the underlying principle: AI should prepare high-stakes money decisions for human approval, not execute them. This guide names every surface the bundled MCP exposes, every hard limit it imposes, the prep-pack architecture that fills the gap durably, and the anti-patterns that look like progress but ship books in worse shape than they started.**

**Published:** <time datetime="2026-05-26">2026-05-26</time>  ·  **Last updated:** <time datetime="2026-05-26">2026-05-26</time>  ·  **Author:** [Rick Watson](https://www.rmwcommerce.com/), Principal, RMW Commerce Consulting  ·  **Canonical URL:** [`github.com/watsonrm/rmwcommerce/blob/main/guides/quickbooks-automation-using-claude-code.md`](https://github.com/watsonrm/rmwcommerce/blob/main/guides/quickbooks-automation-using-claude-code.md)  ·  **Reading time:** 12-min skim · 55-min deep read

Who this is for: small-business operators and solo principals using Claude Code or claude.ai who want to read or write QuickBooks Online from an AI agent. Anyone who has clicked "Add QuickBooks" inside claude.ai and noticed there is no `create_bill` tool. Builders deciding whether to author against the bundled connector, register an Intuit Developer app, or stand up the official Intuit MCP server. Anyone trying to figure out where the human checkpoint belongs in an otherwise-autonomous bookkeeping workflow.

**Jump to:** [60-second map](#the-60-second-map--what-youre-actually-working-with) · [What's possible](#whats-possible--the-headline-capabilities) · [What's NOT possible](#whats-not-possible--and-the-workaround) · [Where to spend your time](#where-to-spend-your-time) · [TL;DR](#tldr--the-five-non-obvious-bits) · [Bill-in gap (Part 4)](#part-4--the-bill-in-gap-and-the-prep-dont-act-principle) · [Architecture (Part 7)](#part-7--architecture-of-the-prep-pack) · [Full TOC](#whats-in-this-article)

---

## The 60-second map — what you're actually working with

Five surfaces, two write paths, one OAuth scope. The most common production confusion is treating "QuickBooks Online API access" as a single thing when it is layered.

| Surface | What it is | What it's good for | How you reach it |
|---|---|---|---|
| **Reads — accounting reports** | AR/AP aging, balance sheet, P&L, sales-by-customer, sales-by-product, balance | Daily / weekly / monthly dashboards; period-end snapshots; agent-driven "where do I stand" prompts | Bundled MCP (33 read tools) OR Intuit MCP OR REST |
| **Writes — sales-out** | Invoices, estimates, payment links, sales settings | Send the customer-facing document the human has already decided to send | Bundled MCP (13 sales-write tools) OR Intuit MCP OR REST |
| **Writes — identity** | Customer create, Product/Service create | Stand up a record before the first invoice/estimate references it | Bundled MCP (2 identity-write tools) OR Intuit MCP OR REST |
| **Writes — bill-in (AP)** | Bill create, Vendor create, BillPayment, JournalEntry | File a vendor bill, create the vendor record, pay it, post a manual journal entry | **Intuit MCP only, OR REST directly**. Bundled MCP exposes ZERO of these. |
| **Admin** | Company info update, transaction import (bank-feed reconciliation, NOT bill creation) | Light profile edits; matching bank-feed transactions to existing entries | Bundled MCP (2 admin tools) OR REST |

The single OAuth scope `com.intuit.quickbooks.accounting` covers reads and writes — there is no separate "write" scope to grant. What changes between paths is the path to the credentials, not the scope of access. Sandbox credentials are immediate from the [Intuit Developer portal](https://developer.intuit.com/app/developer/qbo/docs/develop); production credentials require completing Intuit's app-assessment process. [Part 1](#part-1--the-toolset-and-the-mental-model) covers connector / scope / write-path trade-offs in depth; [Part 4](#part-4--the-bill-in-gap-and-the-prep-dont-act-principle) is the load-bearing argument for why the bundled MCP's omission of bill-in is the right default, not a defect.

### Quick glossary — terms used throughout

- **MCP (Model Context Protocol)** — the protocol Claude and other LLMs use to call external tools. A "QuickBooks MCP" is a server exposing QBO operations as callable tools. [Spec](https://modelcontextprotocol.io/).
- **OAuth** — the credential model QBO uses. You authorize an app once; the app holds a refresh token to call the API on your behalf going forward.
- **REST API** — Intuit's underlying HTTP interface. Both the bundled claude.ai MCP and the official Intuit MCP are wrappers over this.
- **GL (general ledger)** — the chart-of-accounts category every transaction is coded to (e.g., "Subcontractors", "Software Subscriptions"). Bookkeepers think in GL codes; most operators don't.
- **AP (accounts payable)** — bills you owe to vendors. The bill-in side.
- **AR (accounts receivable)** — money customers owe you. The sales-out side.

If you already speak this vocabulary, skip past. If not, the rest of the article assumes these.

### If you read nothing else, this is the minimum viable prep-pack

```
1. Inventory the recurring money decision         // five contractor bills/month, two SaaS bills, one rent
2. Identify the irreversible step                 // posting the bill; paying the bill; creating a vendor
3. Have Claude assemble the one-screen-per-bill   // vendor matched, GL proposed, delta-vs-prior, PDF link
4. Stop. Do NOT call any qbo_*_create_* tool      // the bundled MCP cannot post bills anyway
5. Human reviews the queue, decides, pastes into QBO UI in two clicks per row
```

That five-step skeleton is the AP equivalent of the workspace article's verify-by-JSON pattern: the agent writes an artifact, the human verifies the artifact, the human commits. It survives every Intuit policy change, every connector regression, every MCP surface adjustment — because it never crosses the API boundary. [Part 7](#part-7--architecture-of-the-prep-pack) is the typed-contract version of this skeleton, ready to drop into a Claude Code skill.

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's published research on agent autonomy, Intuit's QuickBooks Online developer documentation, and the practitioner sources listed in [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## What's possible — the headline capabilities

The capabilities every reasonably-equipped Claude environment can hit today. Bundled MCP coverage noted per row; Intuit MCP / REST coverage assumed unless otherwise stated.

| You want to... | Tool you reach for | Notes |
|---|---|---|
| Read AR aging (summary or by-customer detail) | `qbo_accounting_get_ar_aging_summary`, `qbo_accounting_get_ar_aging_detail` | Bundled MCP. Daily/weekly dashboard staple. |
| Read AP aging (summary or by-vendor detail) | `qbo_accounting_get_ap_aging_summary`, `qbo_accounting_get_ap_aging_detail` | Bundled MCP. Read-only on the AP side — the system can tell you what you owe; it cannot help you file what you owe. |
| Pull balance sheet for a date | `qbo_accounting_get_balance_sheet` | Bundled MCP. As-of dates pin the snapshot. |
| Pull P&L for a period | `profit-loss-generator`, `profit-loss-quickbooks-account` | Bundled MCP. The two-tool split: `profit-loss-quickbooks-account` is the live-QBO read; `profit-loss-generator` is a synthesizer for forecasting / what-if. |
| Cash flow read | `cash-flow-generator`, `cash-flow-quickbooks-account` | Same split as P&L. |
| Read sales-by-customer summary | `qbo_accounting_get_sales_by_customer_summary` | Bundled MCP. Period-bounded. |
| Read sales-by-product summary | `qbo_accounting_get_sales_by_product_summary` | Bundled MCP. Useful for SKU-level revenue cuts. |
| Read product / service list | `qbo_accounting_get_product_service_list` | Bundled MCP. Catalog dump. |
| Search a customer by name / id | `qbo_contact_search_customer` | Bundled MCP. Returns the match list plus the IDs you need for an invoice line. |
| Search a product by name / sku | `qbo_catalog_search_products` | Bundled MCP. Same shape as customer search. |
| Read sales settings | `qbo_sales_get_settings` | Bundled MCP. Default terms, default tax, sales-form prefs. |
| Read company info | `company-info` | Bundled MCP. Industry classification, address, EIN visibility. |
| Read industry benchmarks | `benchmarking-against-industry`, `benchmarking-quickbooks-account`, `industry-recommendation` | Bundled MCP. Three tools cover the comparative reads. |
| Read payroll (employees, pay types, last run, payslips, deductions) | `qbo_payroll_get_*` family | Bundled MCP. Nine read tools covering employees, payslips, deductions/contributions, pay types, time-off. Most relevant for owner-payroll review. |
| Read peer lending offers | `qbo_lending_get_peer_offers` | Bundled MCP. QBO Capital surface read. |
| Create a customer | `qbo_contact_create_customer` | Bundled MCP. **The one identity-write the bundled MCP allows.** |
| Create a product / service | `qbo_catalog_create_product` | Bundled MCP. **The other identity-write.** |
| Create an invoice | `qbo_sales_create_invoice` | Bundled MCP. Customer-already-decided write. Verify-after-write (Part 3). |
| Send / update / duplicate / delete an invoice | `qbo_sales_send_invoice`, `qbo_sales_update_invoice`, `qbo_sales_duplicate_invoice`, `qbo_sales_delete_invoice` | Bundled MCP. Full invoice lifecycle on the sales-out side. |
| Create / send / update / duplicate / delete an estimate | `qbo_sales_create_estimate` family (5 tools) | Bundled MCP. Same shape as invoices. |
| Create / send a payment link | `qbo_sales_create_payment_link`, `qbo_sales_send_payment_link` | Bundled MCP. The lighter-weight "get paid" write path. |
| Update sales settings | `qbo_sales_update_settings` | Bundled MCP. Default terms, tax, sales-form configuration. |
| Update company profile | `quickbooks-profile-info-update` | Bundled MCP. Narrow admin write. |
| Read estimates / invoices / payment links | `qbo_sales_get_estimates`, `qbo_sales_get_invoices`, `qbo_sales_get_payment_links` | Bundled MCP. The corresponding reads to every sales-side write above. |
| Pull a transaction's PDF document | `qbo_sales_get_transaction_document` | Bundled MCP. Returns the rendered sales doc for review or download. |
| Create a Bill (vendor invoice) | **`create_bill` in [intuit/quickbooks-online-mcp-server](https://github.com/intuit/quickbooks-online-mcp-server) — bundled MCP has no equivalent** | Intuit MCP or REST only. Requires Intuit Developer app + production credentials. See Part 4. |
| Create a Vendor record | **`create_vendor` in Intuit MCP — bundled MCP has no equivalent** | Same path as `create_bill`. The vendor-record gap pairs with the bill-creation gap. |
| Create a BillPayment | **`create_bill_payment` in Intuit MCP — bundled MCP has no equivalent** | Same path. |
| Post a JournalEntry | **`create_journal_entry` in Intuit MCP — bundled MCP has no equivalent** | Same path. Use sparingly; bookkeepers consider journal entries a last resort. |

---

## What's NOT possible — and the workaround

The hard limits the bundled MCP imposes, what the underlying API actually supports, and the workaround for each. Scan this table before assuming you've found a new bug — most "the API can't do X" complaints land on a known limit or a different layer of the stack.

| You want to... | Reality | Workaround |
|---|---|---|
| **Create a Bill (vendor invoice) from the bundled claude.ai MCP** | The bundled MCP exposes zero AP-side writes. There is no `qbo_create_bill`, no `qbo_ap_create_bill`. The REST API supports it; the bundled connector does not. | Either (a) the prep-pack — Claude assembles per-bill context, human pastes into QBO UI; or (b) register an Intuit Developer app, complete app assessment, install [intuit/quickbooks-online-mcp-server](https://github.com/intuit/quickbooks-online-mcp-server). Per-task path-A vs. path-B choice covered in Part 4. |
| **Create a Vendor record from the bundled MCP** | Same gap as Bill. No `qbo_contact_create_vendor`. Bundled MCP exposes Customer create (`qbo_contact_create_customer`) and Product/Service create (`qbo_catalog_create_product`) only. | Prep-pack: the queue entry surfaces "this is a new vendor" so the human creates the vendor record in the UI before posting the first bill. Or via Intuit MCP / REST. |
| **Create a BillPayment from the bundled MCP** | No `qbo_create_bill_payment`. The bundled connector cannot pay a bill. | Pay through the QBO UI after the bill is filed, or via Intuit MCP / REST. |
| **Post a JournalEntry from the bundled MCP** | No `qbo_create_journal_entry`. The bundled connector cannot post manual journal entries. | Intuit MCP / REST. Note: even when you can, journal entries should be a last resort — they bypass the audit trail of normal AP/AR flows. |
| **Edit a closed period** | QBO blocks writes against any period closed in the close-the-books process; the API returns a `BusinessValidationException`. | Reopen the period in the UI (admin only), or post the adjustment in the current period with a memo referencing the prior. |
| **Use `quickbooks-transaction-import` to create bills from a CSV** | This tool wraps the bank-feed / reconciliation surface, NOT bill creation. [Apideck's bank-feed integration guide](https://www.apideck.com/blog/quickbooks-bank-feed-integration) documents that QBO bank feeds run through Intuit's Financial Data Partner program and the OFX protocol — a separate path from the core accounting API. ["For Review" bank transactions are not exposed via the public accounting API](https://satvasolutions.com/blog/top-5-quickbooks-api-limitations-to-know-before-developing-qbo-app) per practitioner reports. The tool name is misleading. | If you want to create bills, use `create_bill` (Intuit MCP / REST). If you want bank-feed reconciliation, that lives in a separate Intuit FDP-only path most readers will never touch from an agent. See [anti-pattern A-5](#anti-pattern-a-5--using-quickbooks-transaction-import-thinking-it-creates-bills). |
| **Retrieve original bank-statement line items via API** | Per Intuit policy ("economic and security constraints"), bank-statement raw lines are not exposed; the platform expects integrators to use Plaid / Yodlee / similar bank-data services for that surface. | Pull bank data from the bank-data provider (Plaid, Yodlee, MX), not from QBO. Then write reconciled transactions back into QBO using the regular create endpoints. |
| **Reach the production write surface from the bundled connector** | The bundled claude.ai MCP runs against a connector scope that does not include the bill-side write tools. Adding "more permissions" to the connector won't surface them — they don't exist in that codepath. | Walk the Intuit Developer app path (next row). The connector and the developer-app path are separate codepaths. |
| **Skip Intuit's app-assessment process for production credentials** | Intuit requires a published-app review for all production credentials touching live customer data. The official stated timeline is ~3 weeks (3-day technical + 7-day security + 5-day marketing per [Intuit's review guide](https://developer.intuit.com/app/developer/qbo/docs/go-live/list-on-the-app-store/what-to-expect-during-the-review)); practitioner walkthroughs report [6 weeks to 6+ months](https://satvasolutions.com/blog/intuit-app-store-approval-timeline-developer-guide) in real-world cases, with security review often the longest phase. | Sandbox credentials are immediate and free; develop and test there. For production, plan for weeks, not days. There is no fast-track for narrow internal-use apps as of 2026. |
| **Run the MCP server from a cloud function with no persistent storage** | Refresh tokens rotate; the Intuit MCP server expects `QUICKBOOKS_REFRESH_TOKEN` as an environment variable. A short-lived cloud worker cannot survive a refresh cycle without writing the new token somewhere persistent. | Persist refresh tokens in Secret Manager / Vault and rotate the env-var on update. Or run the MCP server as a long-lived service. Same constraint workspace operators see with Drive/Docs OAuth tokens. |
| **Trust the MCP success message without verifying the QBO state changed** | Like every API, the MCP can return success for a request that didn't actually take effect — partial validation, async commit lag, or a webhook the write triggered failed downstream. The bundled `qbo_sales_create_invoice` returns a structured success regardless of whether downstream reporting picked up the entry. | Read-back-after-write: call `qbo_sales_get_invoices` (or the entity-matching read) immediately after the create. Confirm the invoice id appears with the values expected. The same verify-by-JSON pattern as Google Docs. See [Part 3 §3.4](#33--verify-after-write-the-qbo-equivalent-of-verify-by-json). |
| **Loop write calls without idempotency** | Reruns produce duplicates. QBO doesn't enforce uniqueness on (vendor, amount, date) — two identical bills can both land in AP. | Search-before-create on a stable natural key (vendor + invoice number + invoice date for bills; customer + invoice number for sales). If found, return the existing id; do not create. [Pattern P-6](#36--idempotency-search-before-create-on-stable-natural-keys). |
| **Invoice yourself for a contractor bill using `qbo_sales_create_invoice`** | Wrong direction of money. An Invoice is what YOU send to a customer; a Bill is what a vendor sends to you. Creating an Invoice for a contractor bill credits AR and debits revenue — the opposite of what AP needs. Audit reports get wrong, books reconcile wrong, taxes get wrong. | Don't. The right tool for a vendor bill is `create_bill` (Intuit MCP / REST). Until you have production credentials, the prep-pack and a UI paste is the right answer. See [anti-pattern A-1](#anti-pattern-a-1--using-qbo_sales_create_invoice-to-record-a-vendor-bill). |
| **Use the bundled MCP from a deployed Claude Code skill in the same way as a direct prompt** | Connector parity gotchas mirror the Google Drive case — the connector surface available in a direct claude.ai prompt can be narrower or behave differently inside a deployed skill or sub-agent context. Test in both. | Same workaround as the workspace article's connector-parity section: test in both contexts before shipping; on regression, fall back to a local path (prep-pack writes to a local file) until the connector is fixed. |

---

## Where to spend your time

Once the map is clear, here are the patterns that close the largest share of real-world failure modes. **The reader who only adopts items 1–4 closes the largest share of "should I automate this?" decisions correctly.** Items 5–9 are amplification, mostly relevant once you've decided to invest in a longer-lived skill or agent.

| # | Pattern | Why it matters | Effort |
|---|---|---|---|
| 1 | **Prep, don't act** | For any recurring task that ends in a money, identity, or commitment write, the AI's job is to assemble a one-screen-per-decision package — vendor matched, GL proposed, delta-vs-prior surfaced — so the human's job collapses to a 30-second yes/no. The single highest leverage point in QBO automation. | Per-task discipline |
| 2 | **Resist filling the bill-in gap until volume justifies it** | The bundled MCP's lack of `create_bill` is not a defect; it is the right default for non-bookkeeper users. Filling it via the Intuit Developer + production-credential path is multi-week setup + ongoing maintenance. For < 50 bills/month it does not pencil out. | Pre-commitment to honesty about ROI |
| 3 | **Read-back-after-write on every QBO write** | Tool success is not state success. After any `create_*` / `update_*` / `delete_*` call, read the entity back from QBO and confirm the values match what was written. The same discipline as `getDocumentInfo`-after-write in the workspace article. | Low |
| 4 | **Search-before-create on stable natural keys** | Rerunning the same write must reach the same QBO state. Search by (vendor + invoice number + date) for bills, (customer + invoice number) for invoices, (vendor name) for vendor records. Match → return existing id; do not create. | Low |
| 5 | **Pin the OAuth scope and connector path in the skill metadata** | The single scope `com.intuit.quickbooks.accounting` covers reads and writes — but the bundled MCP and the Intuit MCP run through different connector codepaths. State which path a skill expects. Hardcoding "QuickBooks tools" without naming the path is brittle. | Low |
| 6 | **Treat sandbox as the only safe place to develop write logic** | Sandbox credentials are immediate, free, and isolated from your real books. Develop every write path against sandbox; only promote to production after the read-back-after-write check passes for the live entity shape. | Low |
| 7 | **State.json breadcrumbs for any multi-step QBO workflow** | A skill killed mid-write between "vendor created" and "bill posted" leaves the books in an intermediate state. Persist the in-progress state to a known path so the next dispatch detects the interruption and reconciles before compounding. | Medium |
| 8 | **Single-writer pattern: one specialized sub-agent owns all QBO writes** | Multiple agents writing to the same QBO entity in parallel race on (a) idempotency lookups and (b) read-back-after-write checks. Centralize all QBO writes in one writer agent; validators stay read-only. Same shape as the Drive single-writer pattern. | Medium |
| 9 | **Daily drift report on AR / AP aging delta** | The cheapest possible production observability: a scheduled task that pulls `qbo_accounting_get_ar_aging_summary` and `qbo_accounting_get_ap_aging_summary` daily, diffs against yesterday, and surfaces any unexpected jump. Catches duplicate bills, duplicate invoices, and missing customer payments before month-end. | Medium |

Most readers should adopt items 1–4 and stop. Items 5–9 matter once the volume is real and the skill is unattended.

---

## TL;DR — the five non-obvious bits

If you read nothing else, internalize these. They're the highest-leverage corrections most QBO-touching automation needs. None are obvious from reading Intuit's docs.

1. **The bundled MCP has 33 read tools, 13 sales-write tools, 2 identity-write tools, and zero AP-write tools.** The omission is deliberate, not a defect. Sales-out is what-the-human-already-decided; bill-in is what-the-human-must-still-decide. Don't ask the bundled MCP to file bills — it can't, and the right answer is the prep-pack, not a workaround.
2. **`quickbooks-transaction-import` does NOT create bills.** The name is misleading. It wraps the bank-feed / reconciliation / company-admin surface — bank-statement transactions arriving via Intuit's separate FDP/OFX path. Calling it on a CSV of vendor invoices will not file bills. See [anti-pattern A-5](#anti-pattern-a-5--using-quickbooks-transaction-import-thinking-it-creates-bills).
3. **Anthropic's own deployed-agent data is the design pattern for AP.** Across roughly one million tool calls audited in late 2025 through early 2026, only 0.8% of agent actions appeared irreversible, 73% had a human in the loop, and 80% had at least one safeguard (restricted permissions or human approval). The prep-don't-act pattern is what those numbers describe, applied to one specific domain.
4. **Tool success is not state success — same rule as Google Docs.** Every QBO write needs a read-back to confirm the entity landed with the right values. The same verify-by-JSON discipline from the workspace article applies, just with `qbo_sales_get_invoices` instead of `readDocument`.
5. **The single OAuth scope is `com.intuit.quickbooks.accounting`.** There is no separate "write" scope to grant. What changes between the bundled-MCP path and the Intuit-MCP / REST path is the connector and the credentials, not the scope. Granting "more permissions" to the bundled connector won't unlock bill-write tools — they aren't in that codepath.

### The volume-threshold decision rule

> **Under ~50 bills/month → Path A (prep-pack).** Claude prepares each bill as a one-screen review entry; you commit through the QBO UI in two clicks. Setup: one hour. Maintenance: zero.
>
> **Over ~50 bills/month, OR a bookkeeper already in the loop → Path B (full Intuit MCP + production OAuth).** Walk Intuit's app-assessment process; install the official MCP server; let Claude post bills via the REST API after explicit human approval. Setup: weeks. Maintenance: ongoing token rotation and connector breakage.
>
> The threshold is judgment, not a sourced statistic — but the asymmetry is real. Below the line, the prep-pack is faster end-to-end than the integration project. Above it, the manual step becomes the bottleneck. [Part 4 §4.7](#47--the-two-path-build-choice-honestly) is the full argument.

---

## What's in this article

- [Part 1 — The toolset and the mental model](#part-1--the-toolset-and-the-mental-model) — bundled MCP vs. Intuit MCP vs. raw REST; OAuth scope; app-assessment gate; the full tool inventory
- [Part 2 — Reading from QuickBooks](#part-2--reading-from-quickbooks) — reports, search, financial generators, payroll, benchmarks
- [Part 3 — Sales-out writes](#part-3--sales-out-writes) — invoices, estimates, payment links; verify-after-write; idempotency; the human-already-decided framing
- [Part 4 — The bill-in gap and the prep-don't-act principle](#part-4--the-bill-in-gap-and-the-prep-dont-act-principle) — the load-bearing argument
- [Part 5 — Customers, vendors, products, services](#part-5--customers-vendors-products-services) — identity writes; the vendor-record gap parallel
- [Part 6 — Anti-patterns to recognize](#part-6--anti-patterns-to-recognize) — six specific failure shapes
- [Part 7 — Architecture of the prep-pack](#part-7--architecture-of-the-prep-pack) — typed contract, state.json, post-write verify, single-writer rule
- [Part 8 — How to measure whether your QBO automation is healthy](#part-8--how-to-measure-whether-your-qbo-automation-is-healthy) — drift reports, failure smells, ground truth
- [What we still don't know](#what-we-still-dont-know)
- [Sources & Attribution](#sources--attribution)

---

## Part 1 — The toolset and the mental model

### 1.1 — Three paths to QuickBooks Online, one OAuth scope

The same QBO company file can be reached from three paths. Pick the wrong one and either the surface you need doesn't exist or the maintenance burden is wildly disproportionate to the task.

| Path | What it is | What you get | Trade-offs |
|---|---|---|---|
| **Bundled claude.ai Intuit MCP** | The Intuit connector available inside claude.ai itself. Add it from the connector menu; OAuth-consent against your QBO company. | 50 tools: 33 reads, 13 sales writes, 2 identity writes, 2 admin writes. Zero AP-side writes, zero vendor-record creation. | Fastest setup (one click). Narrow on writes by design. No bill-in surface. Production-grade for the surfaces it exposes. |
| **Intuit official MCP server** | [`intuit/quickbooks-online-mcp-server`](https://github.com/intuit/quickbooks-online-mcp-server) — Apache-2.0, ~144 tools across 29 entity types, full CRUD plus 11 reports. Self-hosted; requires Intuit Developer app + production credentials. | Bill / Vendor / BillPayment / JournalEntry / Purchase / Deposit / Transfer / Class / Department / Tax. Everything the bundled connector omits. | Multi-week setup (app assessment). Ongoing token-rotation maintenance. Right for >50 bills/month or any volume where the per-bill prep time outweighs the setup cost. |
| **Raw REST API** | Direct HTTPS calls against `quickbooks.api.intuit.com/v3/company/<realmid>/<entity>`. Same scope, same credentials as the Intuit MCP path. | Everything the API supports — strictly a superset of either MCP. | Most code to write and maintain. Right when you need a workflow that neither MCP exposes (e.g., custom field manipulation, batch operations across entities). |

The OAuth scope is the same across all three: `com.intuit.quickbooks.accounting`. There is no separate "read" or "write" or "AP" scope to grant. What changes between paths is the path to the credentials and the surface of the wrapper, not the underlying authorization. This is a structural feature of Intuit's design; cross-reference the [Intuit OAuth FAQ](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/faq).

**Naming note for the rest of the article.** Tool names like `qbo_sales_create_invoice`, `qbo_accounting_get_ap_aging_summary`, `create_bill`, and `create_vendor` are **MCP server tool names**, not Intuit REST API methods. Each wraps one or more underlying REST calls. `qbo_sales_create_invoice` wraps `POST /v3/company/<realmid>/invoice`; `create_bill` (Intuit MCP) wraps `POST /v3/company/<realmid>/bill`. The distinction matters only when reading code or filing a bug — at the conceptual level, the same QBO entity is being created either way.

### 1.2 — The bundled MCP tool inventory (full count)

The bundled claude.ai Intuit MCP, as available in this session, exposes **50 tools** across the categories below. The breakdown is the load-bearing fact of this article: the asymmetry between sales-out (broad coverage) and bill-in (zero coverage) is the principle that drives the rest of the guide.

**Reads — accounting reports (8):**

- `qbo_accounting_get_ap_aging_detail`, `qbo_accounting_get_ap_aging_summary`
- `qbo_accounting_get_ar_aging_detail`, `qbo_accounting_get_ar_aging_summary`
- `qbo_accounting_get_balance_sheet`
- `qbo_accounting_get_product_service_list`
- `qbo_accounting_get_sales_by_customer_summary`
- `qbo_accounting_get_sales_by_product_summary`

**Reads — sales-out (5):**

- `qbo_sales_get_estimates`, `qbo_sales_get_invoices`, `qbo_sales_get_payment_links`, `qbo_sales_get_settings`, `qbo_sales_get_transaction_document`

**Reads — contact / catalog search (2):**

- `qbo_contact_search_customer`, `qbo_catalog_search_products`

**Reads — financial generators (4):**

- `cash-flow-generator`, `cash-flow-quickbooks-account` (the synthesize / live-read split)
- `profit-loss-generator`, `profit-loss-quickbooks-account` (same split)

**Reads — company / industry (2):**

- `company-info`, `industry-recommendation`

**Reads — benchmarking (2):**

- `benchmarking-against-industry`, `benchmarking-quickbooks-account`

**Reads — payroll (9):**

- `qbo_payroll_get_company_deductions_contributions`, `qbo_payroll_get_company_info`, `qbo_payroll_get_company_last_payroll_run`, `qbo_payroll_get_company_pay_types`, `qbo_payroll_get_company_timeoff_details`, `qbo_payroll_get_employees`, `qbo_payroll_get_payslip_details`, `qbo_payroll_get_payslips`, `qbo_payroll_search_employee`

**Reads — lending (1):**

- `qbo_lending_get_peer_offers`

Total reads: **33 tools** spanning aging, balance sheet, P&L, cash flow, sales reports, catalog, payroll, lending, benchmarking, and company info.

**Writes — sales-out (13):**

- Estimate (5): `qbo_sales_create_estimate`, `qbo_sales_update_estimate`, `qbo_sales_delete_estimate`, `qbo_sales_duplicate_estimate`, `qbo_sales_send_estimate`
- Invoice (5): `qbo_sales_create_invoice`, `qbo_sales_update_invoice`, `qbo_sales_delete_invoice`, `qbo_sales_duplicate_invoice`, `qbo_sales_send_invoice`
- Payment link (2): `qbo_sales_create_payment_link`, `qbo_sales_send_payment_link`
- Settings (1): `qbo_sales_update_settings`

**Writes — identity (2):**

- `qbo_contact_create_customer`, `qbo_catalog_create_product`

**Writes — admin (2):**

- `quickbooks-profile-info-update`, `quickbooks-transaction-import`

**Writes — bill-in (AP): ZERO.** No `qbo_create_bill`. No `qbo_contact_create_vendor`. No `qbo_create_bill_payment`. No `qbo_create_journal_entry`. No `qbo_create_purchase`. No `qbo_create_vendor_credit`. The bundled MCP cannot file a vendor bill, create a vendor record, pay a bill, or post a manual journal entry. This is the headline fact.

Total: **50 tools** — 33 reads, 15 writes (13 sales + 2 identity), 2 admin, 0 AP, 0 vendor-creation. The asymmetry is the design.

### 1.3 — The Intuit official MCP server inventory

[`intuit/quickbooks-online-mcp-server`](https://github.com/intuit/quickbooks-online-mcp-server) — Apache-2.0, ~238 GitHub stars at the time of writing — exposes **~144 tools across 29 entity types** plus **11 financial reports**. The README states "complete CRUD operations are available for all entity types" with five operations per entity (Create, Get, Update, Delete, Search) except for a handful where specific operations don't apply (Account / Class / Department / Term / Payment Method have no Delete; Tax Code / Tax Rate / Tax Agency are read-only; Company Info supports Get + Update only).

**Entity coverage:**

- **Sales-side (overlaps with bundled MCP):** Customer, Invoice, Estimate, Payment, Sales Receipt, Credit Memo, Refund Receipt
- **AP-side (NOT in bundled MCP):** **Bill, Vendor, Bill Payment, Purchase, Purchase Order, Vendor Credit**
- **General accounting (NOT in bundled MCP):** **Journal Entry, Deposit, Transfer, Account, Item, Employee, Time Activity**
- **Configuration (NOT in bundled MCP for most):** Class, Department, Term, Payment Method, Tax Code, Tax Rate, Tax Agency, Company Info, Attachable

**Reports (11):** Balance Sheet, Profit & Loss, Cash Flow, Trial Balance, General Ledger, Customer Sales, Aged Receivables, Customer Balance, Aged Payables, Vendor Expenses, plus one more report depending on QBO edition. Several of these overlap with the bundled MCP's report tools; the rest are net-additional.

**Environment variables required:**

```
QUICKBOOKS_CLIENT_ID
QUICKBOOKS_CLIENT_SECRET
QUICKBOOKS_ENVIRONMENT       # "sandbox" or "production"
QUICKBOOKS_REFRESH_TOKEN
QUICKBOOKS_REALM_ID
```

The refresh token is the operational hot-spot: Intuit rotates refresh tokens periodically, and a long-lived deployment needs to persist the new token after each refresh cycle. A short-lived cloud worker without persistent secret storage will eventually fail authentication. The README's standard hygiene applies (`.env` is gitignored; real credentials stay local).

**The structural takeaway:** the Intuit MCP is a superset of the bundled MCP on every dimension. The trade-off is the path to credentials. Bundled MCP = one-click OAuth, narrow on writes. Intuit MCP = Intuit Developer app + production-credential approval (weeks) + self-hosted refresh-token plumbing, broad on writes.

### 1.4 — The app-assessment gate

Sandbox credentials from the [Intuit Developer portal](https://developer.intuit.com/app/developer/qbo/docs/develop) are immediate. Production credentials require Intuit's app-assessment process. The official structure per [Intuit's review guide](https://developer.intuit.com/app/developer/qbo/docs/go-live/list-on-the-app-store/what-to-expect-during-the-review) and the [app-assessment FAQ](https://help.developer.intuit.com/s/article/New-app-assessment-process-FAQ):

| Phase | Stated timeline | Real-world timeline (per practitioner sources) |
|---|---|---|
| Technical review (API compliance, token storage, error handling) | 3 business days | 2–4 weeks; one reported case of 1 month 10 days; another reported nearly 3 months with no response |
| Security review (penetration testing, encryption, vulnerability scan) | 7 business days | 4–8 weeks; the longest phase in practice |
| Marketing review (app-store listing, marketing assets) | 5 business days | 1–2 weeks |
| **Total stated** | **~15 business days (~3 weeks)** | **6 weeks to 6+ months** per [Satva Solutions' practitioner walkthrough](https://satvasolutions.com/blog/intuit-app-store-approval-timeline-developer-guide) and corroborating threads in the [Intuit developer community](https://help.developer.intuit.com/s/article/New-app-assessment-process-FAQ) |

There is no fast-track for narrow internal-use apps as of mid-2026. A single-operator app that will never touch another company's data goes through the same gate as a multi-tenant marketplace product. The implication for any small-business operator considering the Intuit MCP path: budget for weeks of approval before the production write surface is reachable.

Independent confirmations: [Codat's QBO integration setup guide](https://docs.codat.io/integrations/accounting/quickbooksonline/accounting-quickbooksonline-new-setup), [Knit's QBO API integration walkthrough](https://www.getknit.dev/blog/quickbooks-online-api-integration-guide-in-depth), [Satva Solutions' app-setup blog](https://satvasolutions.com/blog/quickbooks-online-app-using-intuit-developer-portal).

### 1.5 — Connector parity gotchas

Connector parity in the QBO surface mirrors the workspace article's connector-parity section. Three known divergences hit production:

- **Bundled MCP vs. direct REST vs. Intuit MCP — different surfaces, different OAuth flows, same scope name.** A skill written against `qbo_sales_create_invoice` doesn't transfer line-for-line to the Intuit MCP's `create_invoice` even though they hit the same REST endpoint. Field naming differs; default values differ; the tool-call envelope differs.
- **Skill-context vs. direct-prompt context.** A skill bundled as a runnable artifact may invoke the QBO connector through a different codepath than a direct claude.ai conversation does. Test in both before shipping; if a write works in a direct prompt but fails in a deployed skill, suspect connector wiring before suspecting your code.
- **Sandbox vs. production credentials.** The same code that works against a sandbox QBO company can fail against a production company if (a) the entity has custom fields the sandbox didn't, (b) the production company is on a different QBO edition with different available entities, or (c) production has a closed accounting period the sandbox doesn't. Always smoke-test against the production company shape once credentials are live.

The durable workaround when connector parity breaks: **work on a local artifact**. The prep-pack writes a markdown queue file locally; the human's UI paste happens against QBO directly; nothing in the pipeline depends on the connector being available. This is the same pattern the workspace article documents for `.pptx` files when the Drive connector regresses.

### 1.6 — The shape of a QBO write

Every QBO write is structurally a POST or PUT to `https://quickbooks.api.intuit.com/v3/company/<realmid>/<entity>` with an `Authorization: Bearer <access_token>` header. The Intuit-side semantics most operators trip on:

1. **VendorRef on a Bill is required.** You cannot create a Bill without referencing an existing Vendor record. The Vendor must exist first. (This is the structural reason the bill-in gap and the vendor-create gap pair — fixing one without the other doesn't get you anywhere.)
2. **CustomerRef on an Invoice is required.** Same shape, customer side. Either match an existing customer or create one first.
3. **Accounting periods can be closed.** Writes against a closed period return a `BusinessValidationException`. The error name does not always make the cause obvious.
4. **Sparse updates vs. full replaces.** QBO supports both. Sparse update (`sparse: true` in the payload) only changes the fields you specify; full update replaces the entity. Default to sparse for partial-edit safety.
5. **Idempotency is the caller's job.** QBO does not enforce uniqueness on natural keys; two identical bills can land in AP. Always search-before-create. See [Pattern P-6](#36--idempotency-search-before-create-on-stable-natural-keys).
6. **Webhooks vs. polling.** QBO supports webhooks for many entity changes; if a downstream system needs to react, prefer webhooks over polling. The MCP servers don't expose webhook setup tools — that's a separate developer-portal configuration.

The verify-after-write discipline (Part 3 §3.4) catches most failures that violate any of the above.

---

## Part 2 — Reading from QuickBooks

Reads are the safe surface. The bundled MCP exposes 33 read tools spanning accounting reports, sales documents, contact/catalog search, financial generators, payroll, and benchmarking. None of these change QBO state; the worst failure mode is a stale or empty result. This is the surface where AI agents add the most value with the least risk.

### 2.1 — The big-five accounting reads

For any QBO automation, five reads are load-bearing. They answer "where do I stand" and gate every subsequent decision.

| Read | Tool | Returns | Typical use |
|---|---|---|---|
| AR aging summary | `qbo_accounting_get_ar_aging_summary` | Total outstanding by aging bucket (current / 1–30 / 31–60 / 61–90 / 90+) | Daily dashboard; who's late on paying me |
| AR aging detail | `qbo_accounting_get_ar_aging_detail` | Per-invoice breakdown across buckets | Pre-call prep for a collections conversation |
| AP aging summary | `qbo_accounting_get_ap_aging_summary` | Total owed by aging bucket | Daily dashboard; who do I owe and when |
| Balance sheet | `qbo_accounting_get_balance_sheet` | Assets / Liabilities / Equity at an as-of date | Month-end / quarter-end snapshot |
| P&L | `profit-loss-quickbooks-account` (live) or `profit-loss-generator` (synthesized for forecasting) | Revenue / Cost of Goods / Operating Expense / Net Income for a date range | Monthly review; what did I make last month |

Pinning a stable as-of date and a stable period grain is the discipline. Reports are sensitive to (a) whether the company uses accrual or cash basis (set in QBO settings; readable via `qbo_sales_get_settings` and `company-info`), (b) what fiscal year the company runs, and (c) what custom date ranges are passed. Two reads at "last month" against the same data can differ by hundreds of dollars if one uses cash and one uses accrual; always confirm the basis before reporting numbers.

### 2.2 — The sales-by reads and the catalog dump

For any business with a catalog (products, services, SKUs), three reads close the loop on "what's selling":

- `qbo_accounting_get_sales_by_customer_summary` — revenue per customer for a period.
- `qbo_accounting_get_sales_by_product_summary` — revenue per item for a period.
- `qbo_accounting_get_product_service_list` — the full catalog as it exists today.

The combination is the "where's the revenue coming from" prompt for any consulting / agency / services business with multiple billable lines. For an e-commerce business, the same trio answers SKU-level mix questions: which items are pulling weight, which are dead, which are growing.

The catalog dump is also the precondition for any new-invoice automation: you can't reference an item on an invoice line unless that item exists in the catalog. A prep-pack that proposes a new invoice should always check the catalog first — and if the item is missing, surface that fact rather than silently creating a new one (which `qbo_catalog_create_product` allows; see Part 5 for the discipline around when to do that).

### 2.3 — Customer and product search

`qbo_contact_search_customer` and `qbo_catalog_search_products` are the resolve-by-name reads. They take a query string, return a match list. Two reasons every write workflow uses them first:

1. **Resolve display names to IDs.** The QBO write APIs require IDs (`CustomerRef.value`, `ItemRef.value`), not display names. The search tool is the only way to map "Acme Corp" to the customer ID Acme Corp has in the company file.
2. **Detect duplicates before creating.** Before running `qbo_contact_create_customer` on "Acme Corp", search first. If the search returns "Acme Corp", "ACME Corp", and "Acme Corp." as three separate matches, the customer already exists — possibly three times, which is its own data-quality problem worth surfacing. (Duplicate-vendor and duplicate-customer drift is the classic QBO data-hygiene failure; see [Part 8 §8.3](#83--failure-smells).)

Pattern: every write workflow that creates an entity searches first, matches on a normalized form of the name (case-folded, punctuation-stripped, whitespace-collapsed), and returns the existing id if the match is unambiguous.

### 2.4 — The two-tool split: live read vs. synthesized generator

Four bundled-MCP tools come in pairs:

- `cash-flow-generator` ↔ `cash-flow-quickbooks-account`
- `profit-loss-generator` ↔ `profit-loss-quickbooks-account`

The `*-quickbooks-account` variant is the live QBO read — it returns what the books currently say. The `*-generator` variant is a synthesizer: it takes inputs and produces a forecast or what-if. The naming is subtle enough that operators sometimes confuse them, asking the generator for live state or asking the live read for a forecast. Both return data; only one matches the question.

The discipline: when you want what the books currently say, use `*-quickbooks-account`. When you want a "what would the next 90 days look like if I did X" projection, use `*-generator`. Cross-reference both against the source-of-truth balance sheet for sanity.

### 2.5 — Payroll reads

The bundled MCP exposes nine payroll reads: employees, pay types, last payroll run, payslip details, payslips, deductions / contributions, company payroll info, time-off, employee search. Together they cover the read surface a single-owner or small-team payroll review needs:

- **Owner's own paycheck:** `qbo_payroll_search_employee` for the owner record, then `qbo_payroll_get_payslip_details` for the latest payslip. Verify pay against the prior period; flag deltas.
- **Headcount and pay types:** `qbo_payroll_get_employees` + `qbo_payroll_get_company_pay_types` cover the static surface for team review.
- **Compliance reads:** `qbo_payroll_get_company_deductions_contributions` for the deduction/contribution mix; `qbo_payroll_get_company_timeoff_details` for PTO balances.

No payroll write tools in the bundled MCP. Same pattern as bill-in: read everything, change nothing. Payroll writes are a separate Intuit Payroll API and a separate set of permissions; an agent that wants to run payroll programmatically is in even deeper territory than one filing bills.

### 2.6 — Benchmarking and industry

Three tools cover the comparative-context surface:

- `benchmarking-against-industry` — how does this company compare to its industry peers
- `benchmarking-quickbooks-account` — pull the QBO-side benchmarking data
- `industry-recommendation` — suggestion-shaped output for industry classification

These are useful for the kind of "where do I stand relative to peers" question that turns up in monthly review or fundraising prep. They're also useful for sanity-checking whether the company's GL is coded the way other businesses in the same industry code theirs (if your "marketing" expense is 5% of revenue and the industry median is 12%, that's a question worth asking).

### 2.7 — When to use the read tools vs. just open QBO

A common operator mistake: using Claude to ask "what's my AR aging?" when the QBO UI has the same report two clicks away. The agent's value isn't replacing a click — it's combining reads that the UI doesn't combine.

Examples of agent-only value:

- **Pre-meeting brief.** Read AR aging detail + sales-by-customer for the last 12 months + the customer's invoice history. Output: one page summarizing where you stand with the customer ahead of a call. The QBO UI gives you each report individually; the agent gives you the merged brief.
- **Drift detection.** Diff today's AR aging against yesterday's. Surface jumps. The UI doesn't do diffs.
- **Cross-period analysis.** Read P&L for each month of the last 12 months. Compute month-over-month delta on each line. Surface anomalies. The UI gives you one period at a time.
- **Cross-source reconciliation.** Read AP aging + read your bank account in another system + compute what's about to clear. The UI can't see the bank.

The right framing for reads: use them to assemble context the QBO UI doesn't assemble. If the question is answerable in two clicks, the UI is faster.

---

## Part 3 — Sales-out writes

The sales-out surface is the broad write capability in the bundled MCP. Thirteen tools cover the full lifecycle of customer-facing documents — invoices, estimates, payment links, settings. This is the surface where AI agents can do real work today against the bundled connector without any production-credential setup.

The conceptual framing: every sales-out write is the human-already-decided write. The customer was qualified by the owner. The amount was agreed in advance. The line items match prior work. The send action confirms a decision already made. This is materially different from the bill-in side, where every write is a decision about whether to commit money out — and the design implication shows up in the bundled MCP's coverage.

### 3.1 — The invoice lifecycle (5 tools)

`qbo_sales_create_invoice` ↔ `qbo_sales_update_invoice` ↔ `qbo_sales_delete_invoice` ↔ `qbo_sales_duplicate_invoice` ↔ `qbo_sales_send_invoice`. The five tools cover the full invoice CRUD plus duplicate and send.

The typical agent shape:

1. **Resolve the customer.** `qbo_contact_search_customer` returns the CustomerRef id. If not found, either `qbo_contact_create_customer` (and surface that the agent created a new customer in its return) or stop and surface "customer doesn't exist; please create" — depending on the skill's authorization scope.
2. **Resolve each line item.** `qbo_catalog_search_products` for each line. Same shape as customer resolution.
3. **Build the invoice payload.** CustomerRef, line items with ItemRef + amount + description, due date, terms (from `qbo_sales_get_settings` if not explicit).
4. **Search-before-create.** Run `qbo_sales_get_invoices` filtered to (customer, invoice number, date). If a match exists, return that invoice id; do not create.
5. **Create.** `qbo_sales_create_invoice`.
6. **Verify.** Read the created invoice back via `qbo_sales_get_invoices` with the new id. Confirm line items, amount, customer, due date match expected.
7. **Optionally send.** `qbo_sales_send_invoice` with the verified id. Send is a separate tool because send is a separate decision — file the invoice now, send later, or send immediately.

### 3.2 — The estimate lifecycle (5 tools)

Same shape, different entity. `qbo_sales_create_estimate`, `update`, `delete`, `duplicate`, `send`. Estimates are the pre-acceptance counterpart to invoices: customer hasn't said yes yet, no AR is created, no payment is due. Sales workflows that use estimates as proposals tend to want:

- Create estimate
- Send estimate
- On customer acceptance, convert to invoice (which in the API is a separate `qbo_sales_create_invoice` call referencing the estimate id, not a single "convert" tool)

The duplicate tool (`qbo_sales_duplicate_estimate`) is the recurring-proposal pattern — duplicate last quarter's estimate to this customer, update the dates and line items, send.

### 3.3 — Payment links (3 tools)

`qbo_sales_create_payment_link`, `qbo_sales_send_payment_link`, `qbo_sales_get_payment_links`. The lighter-weight "get paid" path. Payment links bypass the invoice entity entirely — they're a direct customer-pays-money mechanism, useful for off-cycle charges, deposits, or "send me money for X" without the full invoice ceremony.

When to use payment link vs. invoice:

- **Payment link:** one-off charge, no formal AR record needed, customer is paying immediately.
- **Invoice:** ongoing customer relationship, formal AR record needed for reporting / collections, payment may be deferred.

Most agency / consulting work uses invoices. Most "one-off small charge" cases use payment links.

### 3.4 — Verify-after-write: the QBO equivalent of verify-by-JSON

The single most expensive failure mode in QBO automation, structurally identical to the workspace article's "tool success ≠ task success" pattern:

```
result = qbo_sales_create_invoice(payload)
if result.success:
    return "Invoice created"
```

The tool returns success when:

- The API request validated and the entity was created — but the line items got dropped because of a CustomerRef sub-validation that didn't trigger an error
- The entity was created with a different customer than intended (search returned an ambiguous match the agent picked at random)
- The entity was created but the email address on the customer record was wrong, so the send step that followed bounced silently
- The entity was created but tax was computed wrong because the customer's tax exemption status changed since the agent last read it

Fix: every QBO write is followed by a read of the same entity. The read returns the entity as QBO sees it. The agent compares expected vs. actual on the load-bearing fields and either confirms success or surfaces the mismatch.

The verify pattern in pseudo-shape:

```
1. expected = { customer_id, invoice_number, line_items, total }
2. created = qbo_sales_create_invoice(expected)
3. actual = qbo_sales_get_invoices(id=created.id)
4. for field in [customer_id, invoice_number, line_items.length, total]:
       assert actual[field] == expected[field], f"mismatch on {field}"
5. return "verified"
```

The cost is one extra read per write. The cost of skipping it is books that look right in the success message and wrong in QBO. The trade is unambiguous.

### 3.5 — Send is a separate decision from create

`qbo_sales_create_invoice` files the invoice in QBO. `qbo_sales_send_invoice` emails it to the customer. They are deliberately separate tools because the decisions are deliberately separate:

- Create-then-send: standard outbound flow.
- Create-then-don't-send: file the invoice now, send later (after a review, after a billing cycle, after another customer confirms).
- Create-then-mark-paid: file the invoice for an already-paid transaction (customer paid by check before the invoice was filed); no send needed.

A skill that always sends-on-create assumes one of the three shapes. Be explicit about which.

### 3.6 — Idempotency: search-before-create on stable natural keys

Rerunning a write must reach the same QBO state. The orchestrator's retry logic will fire on transient errors; the second call must not produce a duplicate entity.

The natural keys for each sales-side entity:

| Entity | Natural key | Search tool |
|---|---|---|
| Invoice | (CustomerRef, DocNumber, TxnDate) | `qbo_sales_get_invoices` with filter |
| Estimate | (CustomerRef, DocNumber, TxnDate) | `qbo_sales_get_estimates` with filter |
| Payment link | (CustomerRef, Amount, created_within_5min) | `qbo_sales_get_payment_links` with filter |
| Customer | (DisplayName normalized) | `qbo_contact_search_customer` |
| Product/Service | (Name normalized) | `qbo_catalog_search_products` |

Always search first. Match → return the existing id and skip the create. Don't match → create, then re-search to confirm uniqueness post-create (catches the race where two agents both miss the existing record and both create a new one).

### 3.7 — Settings updates: low-frequency, high-impact

`qbo_sales_update_settings` changes defaults that affect every future invoice. Default terms (Net 30 vs. Net 15), default tax behavior, default sales-form preferences. Two disciplines around it:

1. **Always read settings before updating.** `qbo_sales_get_settings` gives you the current state. Diff against the change you intend; only write the fields that actually differ. Mass-overwriting the whole settings payload can revert other defaults a human set manually.
2. **Surface the change in the agent's return.** Settings changes are easy to lose track of. The skill's output should say "changed default terms from Net 30 to Net 15 on [date]" so it's grep-able later when invoices start landing with unexpected terms.

### 3.8 — The sales-out skill template

Concrete skill shape for a "draft this month's invoices" agent, against the bundled MCP:

```
1. Read sales-by-customer for the last 90 days       // historical baseline
2. For each recurring customer:
   - Read their last 3 invoices                        // pattern detection
   - Compare against the expected line items this month
   - Search-before-create: does an invoice already exist for this period?
3. If not, draft the invoice payload (do NOT call create yet)
4. Write a queue file with one entry per drafted invoice:
   - Customer name, last-month total, this-month proposed total, line items
5. Stop. Human reviews the queue, approves each entry, agent posts approved ones
6. For each approved entry: qbo_sales_create_invoice → read-back-verify → qbo_sales_send_invoice
7. Update queue file with sent invoice ids
```

The prep-pack pattern surfaces here too — even on the sales-out side where writes are allowed, the durable shape is prep-then-approve. The agent could in principle skip step 4 and post directly, but the failure modes (wrong customer, wrong amount, wrong period) are expensive enough to be worth the 30 seconds of human review per row. This is the same trade-off Anthropic's deployed-agent data points at: 73% of agent traffic has a human in the loop in some way, and the expensive failure modes are concentrated in the irreversible-action tail.

---

## Part 4 — The bill-in gap and the prep-don't-act principle

This is the load-bearing argument. Everything in Parts 1–3 builds toward it; everything in Parts 5–8 generalizes from it.

### 4.1 — The Tuesday-afternoon scenario

A consulting firm with no employees and a handful of recurring contractors. Once a month each contractor sends a PDF invoice to Gmail. The owner drops them into QuickBooks Online, codes them to the right expense category, and pays them. The whole queue takes maybe fifteen minutes a month — the cognitive cost is the friction of context-switching into QBO, not the data entry itself.

This is the canonical task that begs for an AI skill. Recurring, low-novelty, slight tax on attention, predictable shape, no creativity required. Claude can read Gmail. Claude can read PDFs. Claude knows QuickBooks vocabulary. The skill writes itself.

So you go to write the skill. You check which tools are available. The bundled claude.ai Intuit MCP exposes the 13 sales-write tools enumerated in Part 1. On the bill-in side: zero. No `create_bill`. No `create_vendor`. The closest read tools are `qbo_accounting_get_ap_aging_summary` and `qbo_accounting_get_ap_aging_detail`. You can ask the system "what do I owe?" — you cannot ask it "file this bill."

The first reaction is "well, that's an obvious gap; surely it'll be filled in the next release." The second reaction — the right one — is to look at what's on each side of the asymmetry.

### 4.2 — Naming the asymmetry precisely

The bundled MCP's sales-out coverage describes the workflow a small-business owner ships **to a customer they have already decided to bill**. The customer was qualified by the owner. The amount was agreed in advance. The line items match prior work. The send action confirms a decision already made.

The bundled MCP's bill-in coverage — or absence — describes the workflow a contractor or vendor sends **to a small-business owner who still has to decide**:

- Decide whether the vendor record matches (or whether a new vendor needs to be created)
- Decide whether the amount looks right against prior bills from this vendor
- Decide which GL category to code it to
- Decide whether the line items match the agreed work
- Decide whether to pay now, schedule for later, or sit on it pending verification
- Decide whether to dispute, ask for a corrected invoice, or move forward

Every one of those is a small-stakes-individually-but-compounds-quickly decision. Every one is judgment work a bookkeeper does explicitly, not implicitly. The bundled MCP's omission of bill-write tools is not a missing feature — it is the design encoding of "this is the human's job, and the AI is the wrong layer to be making these calls."

The gap is between "send the thing the human already decided" and "decide the thing the human hasn't yet." That is exactly where you want the human checkpoint.

### 4.3 — The API gap is not actually an API gap

It is worth being precise about what is missing where.

The QuickBooks Online REST API fully supports POSTing a Bill entity. The endpoint is documented at [`developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/bill`](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/bill). Creating a Bill requires a VendorRef (the vendor must exist first — see [Vendor entity reference](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/vendor)). The OAuth scope is `com.intuit.quickbooks.accounting`, the same one the sales-out tools use. Bills, BillPayments, Vendors, JournalEntries — all of it, all in the same API.

There is also an official Intuit-published MCP server: [`intuit/quickbooks-online-mcp-server`](https://github.com/intuit/quickbooks-online-mcp-server). Apache-2.0. ~238 GitHub stars at the time of writing. ~144 tools across 29 entity types with full CRUD plus 11 reports (Part 1 §1.3). Bill creation is one of them. Vendor creation is one of them. BillPayment is one of them. The path is fully available; the surface exists.

**What is missing is the path from "click Add QuickBooks in claude.ai" to "create a bill in production."** That path stops at the bundled connector. To get from there to bill writes, walk the specific journey:

1. **Register an Intuit Developer app** at [developer.intuit.com](https://developer.intuit.com/app/developer/qbo/docs/develop). Sandbox credentials are immediate.
2. **Complete Intuit's App Assessment** before Intuit unblocks production keys. Per the [app assessment FAQ](https://help.developer.intuit.com/s/article/New-app-assessment-process-FAQ), the questionnaire covers token storage, data retention, use case, security posture. Stated timeline ~3 weeks; real-world commonly 6 weeks to 6+ months ([Satva Solutions practitioner walkthrough](https://satvasolutions.com/blog/intuit-app-store-approval-timeline-developer-guide)).
3. **Host the OAuth bridge yourself.** Client ID, Client Secret, refresh token, realm ID — wired into either the Intuit MCP server or your own client. Refresh tokens rotate; you need persistent secret storage.
4. **Maintain it.** Refresh-token rotation, OAuth scope migrations between minor API versions, connector breakage on Intuit API version bumps.

That is not nothing. For a 5-contractor-a-month workflow it is a multi-week setup followed by ongoing maintenance for a process that takes fifteen minutes a month manually. Even at generous estimates of cognitive savings the math does not pencil out. For a 50-bill-a-month operation it absolutely does.

The bundled-MCP omission is therefore not a limitation but a sensible default. It exposes the parts of the API safe to use without bookkeeper-level judgment and stops short of the parts that need it. The asymmetry encodes Intuit's view (and Anthropic's view, by way of which tools shipped in the connector) of what a non-bookkeeper user should be doing through an AI assistant. That view is correct.

### 4.4 — The principle: prep, don't act

The instinct most operators have when they first see this gap is to want to fill it. "If Claude can't post the bill, fine, I'll write the OAuth bridge." Some readers of this article are mid-typing that response.

Filling the gap is the wrong direction. The right direction is preparing the decision so cleanly that the human's job collapses to a 30-second yes/no.

Concretely, for the contractor-invoice workflow, what a prep-pack looks like:

A new bill appears as a queue entry in a local markdown file (or a Drive doc, or a Sheet — the surface doesn't matter). The entry has:

- **Vendor name pre-matched against QBO's existing vendor list** — so the human knows whether a new vendor record needs to be created first
- **Proposed GL category** based on what category that vendor's prior bills were coded to — so the human is reviewing one suggestion, not deciding from scratch
- **Dollar amount and invoice date** extracted from the PDF
- **One-line delta from the previous month's bill from the same vendor** — a $400 invoice from a vendor who has billed $200 every month for two years stands out
- **Link to the original PDF** — in case the human wants to verify any specific line

The human reads the entry, makes one of three decisions — approve, approve with edit, reject — and either pastes the line items into QuickBooks themselves (the bundled-MCP path) or one-clicks a "post" button that hits the write API (the Intuit-MCP path, if they walked that path).

Total human time per bill: fifteen to thirty seconds. Not because the prep replaced the human decision but because the prep loaded the entire context for the decision into one screen, eliminating every navigation step that was the actual friction. The decision itself is fast; the navigation around it was slow.

This is the same shape as how Claude Code's own permission model works. When Claude wants to delete a file or run a Bash command, it doesn't do the thing and ask forgiveness; it presents the action with context, and the human says yes or no. The [Claude Code best-practices guide](https://code.claude.com/docs/en/best-practices) is direct: Claude pauses for "actions that might modify your system" — file writes, Bash commands, MCP tools — and the default is interruption-then-approval rather than autonomous execution. The permission model is itself the prep-pack pattern, applied at the tool-call layer.

### 4.5 — Anthropic's deployed-agent data is the design pattern

The prep-don't-act principle isn't a hunch. Anthropic published the supporting data in their [Measuring AI Agent Autonomy in Practice](https://www.anthropic.com/research/measuring-agent-autonomy) report (February 18 2026), based on roughly one million tool calls from Claude's public API during late 2025 through early 2026. Three numbers carry the argument:

> *80% of tool calls come from agents that appear to have at least one kind of safeguard (like restricted permissions or human approval requirements).*
>
> *73% appear to have a human in the loop in some way.*
>
> *Only 0.8% of actions appear to be irreversible (such as sending an email to a customer).*

Three observations that land directly on the bill-in design choice:

1. **Irreversibility is rare in well-designed agents because designers route around it.** Operators with experience building production agents already concentrate the irreversible actions behind a human checkpoint. The bundled MCP's bill-in omission is the connector-level expression of that pattern.
2. **Human-in-the-loop is the majority of production agent traffic.** This isn't a niche pattern for cautious operators; it's how the median deployed Claude agent works. Designing without a human checkpoint is the outlier.
3. **Safeguards include restricted permissions.** The bundled MCP's narrow write surface IS a safeguard. Granting "more permissions" to make it broader removes the safeguard.

The data is the design pattern. Operators who notice this and lean into it ship faster and break less than operators who try to push the human out of the loop on principle.

### 4.6 — What about dedicated AP platforms?

The natural next question: isn't the prep-pack reinventing what BILL, Ramp Bill Pay, Mercury Bill Pay, and similar already do?

The honest answer: they do solve adjacent problems, and they're right for many operators. They're wrong for solo principals with a handful of recurring contractors.

**BILL (formerly Bill.com).** [Pricing page](https://www.bill.com/product/pricing) starts at $49/user/month for the Essentials tier (AP/AR), scaling through Team at $65, Corporate at $89, Enterprise custom. Per-user means a solo principal pays the full per-user rate for themselves; adding a bookkeeper doubles the cost. Payment types layer per-transaction fees on top of subscription. Built for accounting departments where approval routing, dual-control, vendor onboarding workflows, and 1099 reporting at scale outweigh the per-user cost. For a solo operator with five contractors a month, $588/year is procurement-platform money for a 15-minute monthly review task.

**Ramp Bill Pay.** Offered at no separate subscription cost when bundled with Ramp's cards, positioned at small businesses per [Ramp's own marketing](https://ramp.com/blog/bill-pay-guides/small-business). The catch: the bundling assumes you want to centralize spend on Ramp cards in the first place. If your business banking is already settled and the bill workflow is the only piece, you're signing up for a card program to get the AP tool — which may or may not be the right move depending on independent factors.

The shared structural critique: dedicated AP platforms are built for the world where AP volume justifies an AP function. For a solo principal whose AP volume is five bills a month, the AP tool is the wrong unit of automation. The right unit is the per-bill prep — which Claude does for the cost of one chat session per month, with no per-user license, no procurement-platform onboarding, no dependence on a separate vendor's API stability.

This is the same shape as why most solo consultants use a folder structure plus a calendar instead of a project-management platform: the lightweight tool wins as long as the volume is light, and the heavyweight tool only wins past a threshold most solo operations never reach.

### 4.6.5 — What about the autonomous-AI-bookkeeper category?

The harder counter-argument isn't BILL or Ramp — it's the autonomous-AI-bookkeeper category that has been raising real money on the pitch that the AI does the whole loop. [Pilot.com launched its fully autonomous AI bookkeeper in February 2026](https://www.accountingtoday.com/news/pilot-launches-fully-autonomous-ai-bookkeeper); Botkeeper, Digits, and Booke AI have parallel offerings ([alternatives roundup](https://getuku.com/articles/botkeeper-alternatives)). The pitch: skip the human-in-loop, let the model code transactions, post bills, reconcile bank feeds, close the books. The implicit promise is that AI is finally good enough to remove the bookkeeper from the AP path entirely.

The counter-counter-argument is the same data Part 4 §4.5 leans on. Across roughly one million tool calls Anthropic audited across deployed agents, 73% had a human in the loop and only 0.8% of actions appeared irreversible. The vendors selling autonomous bookkeeping are pitching the opposite distribution — closer to 0% human-in-loop on bill-side writes, with the irreversibility-rate-times-volume math left as an exercise for the buyer. For a category where every error is irreversible in the practical sense (a posted bill in the wrong GL code in March is a tax-return problem in October), the math does not pencil for a solo operator.

Three operational realities the category mostly papers over:

1. **Vendor identity write errors compound.** Creating "Acme Hosting" as a new vendor when "Acme Hosting Inc." already exists splits the spend across two records; six months later the AP aging report misrepresents both. Autonomous tools catch this through fuzzy-match heuristics that are right ~95% of the time, which means one in twenty bills creates a duplicate the human will eventually have to unwind. The prep-pack catches it through the human's read at one-screen review.
2. **GL coding requires business context the model doesn't have.** The same vendor invoice can be "Software Subscriptions" for one client engagement and "Cost of Revenue" for another, depending on whether it's billable through to the client. The model can guess from prior coding; the operator knows from the current engagement context. The autonomous tool's accuracy on this category is bounded by what's encoded in QBO; the prep-pack's accuracy is bounded by what's in the operator's head.
3. **The fix-the-error workflow is slower than the prevent-the-error workflow.** Discovering a misposted bill in QBO requires opening the entity, identifying the error, deleting or voiding the bill, recreating it correctly, and reconciling any payments that flowed through it. For an operator who would have caught the error in two seconds at prep-pack-review time, the autonomous loop is net-negative even at perfect uptime.

The case for autonomous AI bookkeeping is real for companies that already have a bookkeeper-in-the-loop and want the human time spent on supervision rather than data entry. The case is materially weaker for solo operators whose binding constraint is not data-entry time but business-context judgment — which is exactly what the prep-pack preserves.

The Anthropic data is the load-bearing rebuttal: the durable pattern across deployed agents at scale is human-in-loop with safeguards, not autonomous execution. Vendor pitches that ignore that data are selling against the empirical floor.

### 4.7 — The two-path build choice, honestly

Two paths to landing contractor invoices in QuickBooks with AI help today, for an operator who does not already have an Intuit Developer presence. Both are valid; one is right for almost every reader.

**Path A — The prep-pack.**

- Claude reads Gmail, extracts the PDF, matches the vendor, proposes the GL category, writes a queue entry to a markdown file or Drive doc, and stops.
- The human reviews the queue once a month, approves each entry, and pastes the bill into QuickBooks through the regular UI.
- "Less automated" but materially faster end-to-end for small-volume operations.
- Total setup: one skill file, an hour of writing and testing.
- Ongoing maintenance: zero outside Gmail and Drive read tokens, which every Claude Code user already has.
- Survives every Intuit policy change because it never touches the write API.

**Path B — The full integration.**

- Register the Intuit Developer app.
- Walk through the app-assessment questionnaire.
- Get production credentials approved (weeks to months).
- Install [intuit/quickbooks-online-mcp-server](https://github.com/intuit/quickbooks-online-mcp-server).
- Wire the OAuth bridge into Claude Code as an MCP server.
- Let Claude post bills directly into the API after human confirmation.
- Total setup: weeks for approval plus days of OAuth integration work.
- Ongoing maintenance: token rotation, scope migrations, connector breakage on Intuit API version bumps.
- Pays for itself somewhere north of 50 bills a month, or in any context where a bookkeeper is the human-in-the-loop and the volume is procurement-shaped.

For most readers of this article, path A is correct. Not because path B is bad but because path A is what the actual task wants. The instinct to reach for path B is the instinct to over-engineer because the engineering itself is interesting, and that instinct is the most common way solo operators waste their own time.

### 4.8 — The honest version of the argument

The honest version of this section: **resist the urge to automate what is already fast.** Use Claude to prepare the decision and stop. Reach for the API integration only when the volume and the role mix actually justify it.

This is a rare position to take in a category whose dominant marketing pitch is "AI bookkeeper" or "autonomous AP." It is the correct position for the median small-business operator. The numbers in Anthropic's deployed-agent report — 0.8% irreversibility, 73% human-in-loop, 80% safeguards — are the empirical version of the same argument. Operators using AI agents at scale already converge on this pattern; the marketing pitch is just slow to catch up.

---

## Part 5 — Customers, vendors, products, services

The identity-write surface. The bundled MCP exposes two identity-write tools (`qbo_contact_create_customer`, `qbo_catalog_create_product`) and zero vendor-creation tools. The asymmetry is structurally identical to the bill-in gap — and for the same reasons.

### 5.1 — The two identity writes the bundled MCP allows

`qbo_contact_create_customer` creates a customer record. The required fields are minimal — DisplayName is the load-bearing one — but most workflows want to also pass an email (for sending), billing address (for invoices), payment terms (for default Net 30 vs. Net 15), and notes (for human context).

`qbo_catalog_create_product` creates a Product / Service record. Similar shape — Name is required; most workflows also pass IncomeAccountRef (so the item maps to the right revenue account), description (for invoice line text), unit price (for default invoicing), and active status.

Both are deliberately scoped to the surfaces that gate invoice creation. You can't invoice a customer who doesn't exist; you can't line-item a product that isn't in the catalog. The bundled MCP exposes the minimum identity-write needed to make the sales-out flow self-sufficient.

### 5.2 — The vendor-record gap pairs with the bill-creation gap

What the bundled MCP does NOT expose:

- **`qbo_contact_create_vendor`** — create a vendor record. Required precondition for any Bill.
- **`qbo_create_bill`** — create a vendor bill.
- **`qbo_create_bill_payment`** — pay a vendor bill.
- **`qbo_create_purchase`** — record a check / cash / credit-card purchase against a vendor.
- **`qbo_create_vendor_credit`** — record a credit a vendor owes you.

Five missing tools, all on the same side of the books. They pair structurally: you can't file a bill without a vendor record; you can't pay a bill without filing it first; you can't credit a vendor without an existing vendor relationship.

The same Tuesday-afternoon scenario from Part 4 has a Tuesday-afternoon corollary for vendor creation: a brand-new contractor sends a first invoice, the bundled MCP cannot create the vendor record, the human has to do that step in the UI before any subsequent automation can refer to the vendor by ID. The prep-pack's job is to surface the gap clearly: "This vendor doesn't exist in QBO yet — create the record before posting the bill."

### 5.3 — Pattern: identity-write idempotency

Identity entities (customer, product, vendor) are the highest-stakes idempotency surface. A duplicate vendor record is hard to clean up — the dupes accumulate transactions independently; merging requires manual work in QBO; until merged, AP aging splits across both records and reports get wrong.

The discipline: every identity-write workflow searches first on a normalized form of the natural key, only creates if no match is found, then re-searches post-create to confirm uniqueness.

```
1. normalized_name = normalize(display_name)        // case-fold, strip punctuation, collapse whitespace
2. matches = qbo_contact_search_customer(normalized_name)
3. if matches.length >= 1:
       return matches[0].id                         // existing record; use it
4. created = qbo_contact_create_customer(payload)
5. re_matches = qbo_contact_search_customer(normalized_name)
6. if re_matches.length > 1:
       flag("duplicate-customer race detected: " + re_matches.ids)
7. return created.id
```

Steps 1–2 prevent the most common duplicate cause (agent didn't search before creating). Step 5–6 catch the rarer race condition (two agents both searched, both missed, both created). The cost is two extra search calls; the cost of skipping is dupes that compound over months.

### 5.4 — The product-create case is similar but lower-stakes

Duplicate products are easier to clean up than duplicate customers or vendors — fewer transactions reference any given product, and merging is a one-screen operation in QBO. But the same idempotency discipline applies: search first, create second, re-search third. Treat product creation as a serious write, not a casual one; the catalog is referenced by every invoice line.

### 5.5 — When NOT to create the identity record from the agent

Some workflows are better off NOT creating the customer / vendor / product even when the tool is available. The discipline:

- **If the entity's metadata is contested** (the display name could be "Acme Corp" or "Acme Corporation"; the billing address comes from three different sources with different values), don't create — surface the contention to the human.
- **If the entity affects tax or compliance** (a new vendor that should be 1099-tracked; a new customer in a tax-exempt jurisdiction), don't create — the human's first interaction with that entity should be in the UI where the relevant flags are visible.
- **If the entity is brand-new and the human hasn't seen it yet** (first invoice from a vendor; first sale to a customer), the right pattern is to flag in the prep-pack and let the human create the record. The agent's reflex to "just create it" optimizes for a savings (~30 seconds per record) that's smaller than the cost of getting any field wrong (cleanup is hours).

The general rule: identity writes are higher-stakes than sales-out writes because every subsequent transaction inherits the entity's defaults. Get the entity wrong once and every invoice or bill afterward has the wrong defaults. Get a single sales-out invoice wrong and only that invoice is affected.

---

## Part 6 — Anti-patterns to recognize

Six specific failure shapes that look like progress but ship books in worse shape than they started. Each names a real failure mode and the workaround.

### Anti-pattern A-1 — Using `qbo_sales_create_invoice` to record a vendor bill

The bundled MCP can create invoices and cannot create bills. The reflexive workaround some operators reach for: "if I just have Claude create an invoice with the vendor as the customer, that's basically the same thing, right?"

It is not. An Invoice is what YOU send to a customer — it credits AR and debits revenue. A Bill is what a vendor sends to YOU — it credits AP and debits expense. Creating an Invoice for a contractor bill credits AR and debits revenue, exactly the opposite of what AP needs:

- The vendor shows up in your customer list, polluting customer reports.
- The contractor "owes you" the amount on the invoice, when in fact you owe them.
- Your revenue is inflated by every contractor invoice booked this way.
- AR aging shows fake receivables.
- Sales reports include line items that weren't real sales.
- At tax time the discrepancy between booked revenue and bank deposits is non-trivial to reconcile.

The right tool for a vendor bill is `create_bill` (Intuit MCP / REST). Until you have production credentials, the prep-pack and a UI paste is the right answer. Never bend the sales-out tools to do AP work.

**Recovery if it has already happened:** delete the misposted invoices via `qbo_sales_delete_invoice` (the bundled MCP supports this) and either file the bills correctly via the UI or, if production credentials exist, via `create_bill`. The deletion is reversible up to the close-the-books date.

### Anti-pattern A-2 — Trusting MCP tool success without verifying QBO state

```
result = qbo_sales_create_invoice(...)
if result.success:
    return "Invoice created"
```

Same shape as the workspace article's anti-pattern 2. The tool returns success when:

- The API request succeeded, even though the entity didn't land with the expected values (wrong customer due to ambiguous search match; line items dropped due to silent validation; tax computed against the wrong jurisdiction)
- An async commit lag hasn't yet propagated to the reports surface
- A downstream webhook the write triggered failed silently

Fix: every QBO write is followed by a read of the same entity. Compare expected vs. actual on the load-bearing fields. Only declare success if both match.

This is structurally identical to the verify-by-JSON pattern in the workspace article. Tool success ≠ state success, anywhere. The Drive analog is `getDocumentInfo` after `applyTextStyle`; the QBO analog is `qbo_sales_get_invoices` after `qbo_sales_create_invoice`. Make the verify call routine, not exceptional.

### Anti-pattern A-3 — Calling write tools in a loop without idempotency

A skill that walks a list of invoices and calls `qbo_sales_create_invoice` for each one, with no search-before-create. Rerunning the skill produces duplicates. The orchestrator's retry-on-transient-error logic produces duplicates. Two parallel agents both produce duplicates.

Fix: every write workflow that runs more than once does search-before-create on a stable natural key. Match → return existing id; do not create. (Part 3 §3.6 enumerates the natural keys per entity.)

The general anti-pattern shape to spot in code review: a `qbo_*_create_*` call without a preceding `qbo_*_get_*` (or `_search_*`) on the same entity in the same skill. Every create needs a paired search.

### Anti-pattern A-4 — Trying to back into a Bill via JournalEntry without a vendor record

The bundled MCP cannot create bills or vendors. A clever (wrong) workaround: have Claude post a journal entry that debits expense and credits AP for the bill amount, sidestepping the Bill entity entirely.

This is wrong for three reasons:

1. **The bundled MCP can't post journal entries either.** No `qbo_create_journal_entry`. Same gap as Bill / Vendor / BillPayment.
2. **Even via Intuit MCP / REST, journal entries that hit AP without a Vendor reference create "untraceable" AP** — the balance shows up on AR aging but nothing in QBO connects it to a specific vendor for collections / payment / 1099 reporting.
3. **Bookkeepers consider journal entries a last-resort tool.** They bypass the audit trail of normal AP/AR flows. Using JE to do work that should be a Bill obscures the books and makes the auditor's life hard for no good reason.

Fix: if you have production credentials, use `create_bill` with a `VendorRef`. Create the vendor first if needed (`create_vendor`). If you don't have production credentials, use the prep-pack and a UI paste — the human-facing UI files the bill correctly with one click, and the books reconcile.

### Anti-pattern A-5 — Using `quickbooks-transaction-import` thinking it creates bills

The bundled MCP exposes a tool called `quickbooks-transaction-import`. The name strongly suggests "import transactions" — and a reasonable operator reads "transactions" as inclusive of bills.

It is not. The tool wraps Intuit's bank-feed / reconciliation / company-admin surface. Bank-feed transactions are bank-statement line items that flow into QBO via Intuit's separate Financial Data Partner program and the OFX protocol — documented in [Apideck's bank-feed integration guide](https://www.apideck.com/blog/quickbooks-bank-feed-integration). Per practitioner walkthroughs, "For Review" bank-statement line items are not exposed via the public accounting API at all ([Satva Solutions' top-5 QBO API limitations](https://satvasolutions.com/blog/top-5-quickbooks-api-limitations-to-know-before-developing-qbo-app); [an Intuit developer-community thread](https://help.developer.intuit.com/s/question/0D54R00009bVhVySAK/how-to-fetch-or-retrieve-for-review-bank-transactions-from-quickbooks-online-api) where the response confirms bank-statement retrieval is restricted by policy).

Calling `quickbooks-transaction-import` on a CSV of vendor invoices does not file bills. It does not create bill entities. It does not credit AP. It interacts with the bank-feed / company-admin path, which is a different surface entirely.

Fix: if you want to create bills, use `create_bill` (Intuit MCP / REST) or the prep-pack-and-UI-paste path. If you want bank-feed reconciliation, that lives in a separate Intuit FDP-only path most readers will never touch from an agent. The tool name is the source of the confusion; the underlying surface is unrelated to bill creation.

### Anti-pattern A-6 — A validator agent with QBO write tools

The workspace article's "validators don't write either" rule applies identically here. A QBO drift-detector or audit agent that finds problems and also has write tools is structurally a second writer, with the same race-condition risks.

The clean shape: validators emit a typed outcome (`ok | drift_detected | flagged`); on `drift_detected`, the orchestrator re-dispatches the writer agent with corrected content. The writer keeps its sole-ownership invariant on idempotency and verify-after-write state. Validators stay read-only.

The risk if you skip this: a validator that finds a duplicate vendor and writes "fix" the merge directly will race with any concurrent writer touching the same vendor record. The merge can leave AP transactions orphaned, vendor totals split, or worse.

---

## Part 7 — Architecture of the prep-pack

The prep-don't-act principle (Part 4) is the conceptual frame. This section is the concrete implementation: the markdown queue file shape, the per-vendor category memory, the delta-vs-prior-month annotation, the one-screen-per-bill discipline, the human-approval contract, the state.json for resume, the single-writer rule. The architecture that makes prep-don't-act survive interruptions, resumes, and real production load.

### 7.1 — The queue file shape

A markdown file at a known path. One H3 section per bill. Each section is a one-screen-per-bill package: vendor matched, GL proposed, delta-vs-prior surfaced, PDF link, posted-as field for the post-confirm round-trip.

The shape converged on in real practice (a working consulting firm's `~/wiki/07-operations/ap_queue.md`):

```markdown
## Pending bills

### 2026-05-24 — Acme Contractor LLC / Acme Contractor LLC — ClientA Phase 1 — `[VERIFY $ FROM PDF]`

- [ ] **Vendor:** Acme Contractor LLC / Acme Contractor LLC (`nick@example.com`)
- **Vendor in QBO:** ⚠️ **NOT in current AP aging summary.** Either no current balance (paid up) OR no vendor record yet. Verify in QBO UI: Expenses → Vendors → search "Acme" / "Acme Contractor LLC." If absent, create vendor before posting bill.
- **GL category:** `Subcontractors:ClientA` (per [vendor memory](vendor_categories.json); engagement-billable to ClientA)
- **Invoice #:** INV-2026-001
- **Invoice date:** 2026-05-24 (received in Gmail)
- **Due date:** "Pay them whenever" per Nick — schedule for end-of-month
- **Amount:** `[VERIFY from PDF]`
- **Delta vs prior:** `[no prior Acme invoices in AP aging snapshot 2026-05-26; first verifiable Acme bill captured by this queue]`
- **PDF:** [Gmail thread 5/24 "ClientA Invoices" — attachment 1](https://mail.google.com/mail/u/0/#inbox/<thread-id>)
- **Decision:** approve / approve-with-edit / reject
- **Posted as:** _(fill: txnId + paid-via after QBO entry)_

---

## Recently posted (last 30 days)

| Posted | Vendor | Description | Amount | GL | QBO txnId | Paid via |
|---|---|---|---|---|---|---|
| 2026-04-26 | Acme Hosting Inc | Hosting | $147.00 | Web Hosting Expense | 9123 | Brex ACH |
```

Five shape choices worth flagging because they paid off in practice:

1. **Markdown checkbox (`- [ ]`) on the vendor line.** The human checks the box when the bill is posted. The state of every row is visible at a glance — no parsing required, no separate `STATE:` field to keep in sync.
2. **`[VERIFY from PDF]` in the title and on the Amount line.** The dollar amount is the highest-stakes field on the entry. Leaving it as a literal `[VERIFY from PDF]` placeholder — instead of an OCR'd guess — forces the human to open the PDF and read the number. See [§7.3.5](#735--why-the-prep-pack-stops-short-of-extracting-the-dollar-amount) for the principle.
3. **"Vendor in QBO" line with explicit UI navigation when the vendor is missing.** Not "vendor flagged for review" but literally "Expenses → Vendors → search 'Acme' / 'Acme Contractor LLC.' If absent, create vendor before posting bill." The human's next action is on the page; there is no thinking required.
4. **"Posted as" field on every row.** After the human posts the bill in QBO, the QBO transaction ID and the paid-via method land here. The completed row is now an audit-grade record of who got paid, when, by what method, and against which QBO entity — no separate ledger needed.
5. **"Recently posted (last 30 days)" table at the bottom.** Rows move from the pending H3-sections to this compact table on post-confirm. Thirty days of history is enough to answer "did I pay this last month?" without scrolling; older rows archive to `_archive/ap_queue_<YYYY-MM>.md` at month-end.

The shape is deliberately scannable. A human reading the queue file on a Saturday morning should be able to triage every entry in a few seconds. The "everything in one screen" rule (Part 7 §7.4) is the editorial discipline.

### 7.2 — Per-vendor category memory

The "GL category suggested" line is load-bearing. Without it, the human is deciding from scratch every month; with it, the human is reviewing one suggestion that's right 95% of the time.

The mechanism: a small JSON file (canonical default `vendor_categories.json`) keyed by vendor display name. The shape that converged in real practice carries four fields beyond the obvious GL category, each earning its place:

```json
{
  "_meta": {
    "purpose": "Per-vendor GL category + sender-email + bill-pattern memory.",
    "schema_version": 1,
    "source_of_truth": "QBO vendor records are canonical; this file is the local memory the prep-pack uses to PROPOSE categorization. The human verifies on every post."
  },
  "vendors": {
    "Acme Contractor LLC": {
      "aliases": ["Acme Contractor LLC", "Acme", "Acme, LLC"],
      "sender_emails": ["nick@example.com"],
      "default_gl_category": "Subcontractors:ClientA",
      "note": "Engagement-billable subcontractor; all 2026 work on ClientA engagement.",
      "last_seen_invoice": null,
      "last_seen_amount": null,
      "confidence": "high"
    },
    "Beacon Editorial LLC": {
      "aliases": ["Beacon Editorial LLC", "Beacon"],
      "sender_emails": ["hendrik@example.com"],
      "default_gl_category": "Subcontractors:ClientB",
      "note": "Watson Weekly editorial + research lead. Recurring monthly.",
      "last_seen_invoice": "INV-2026-014",
      "last_seen_amount": null,
      "confidence": "high"
    },
    "Cardinal Marketing LLC": {
      "aliases": [],
      "sender_emails": [],
      "default_gl_category": null,
      "note": "Outstanding balance $1,200 in 91+ bucket per AP aging 2026-05-26. GL category unconfirmed — operator to populate.",
      "last_seen_invoice": null,
      "last_seen_amount": 1200,
      "confidence": "unconfirmed"
    }
  }
}
```

Five fields, each earning its place:

- **`aliases`** — vendor names drift over time ("Acme Corp" → "Acme Corp Inc" → "ACME Corp"). Matching the incoming PDF sender against an aliases list catches the case where the canonical QBO display name has shifted but the email signature hasn't. Saves the human from re-coding the vendor every time someone updates their letterhead.
- **`sender_emails`** — the Gmail-scan join key. The prep-pack queries Gmail for new messages from any address in any vendor's `sender_emails`; matches resolve to a vendor record and a proposed GL category in one lookup.
- **`default_gl_category`** — the load-bearing proposal. `null` when the human hasn't confirmed a category yet; the prep-pack surfaces "GL category unconfirmed" on those entries and the human populates it on first post.
- **`last_seen_invoice` / `last_seen_amount`** — the delta-vs-prior baseline ([§7.3](#73--delta-vs-prior-month-annotation)). Updated only on post-confirm, after the human commits the bill in QBO.
- **`confidence: high | medium | unconfirmed`** — the trust level for the proposed GL category. `high` = vendor has prior posted bills with this category. `medium` = inferred from vendor name + invoice memo but not yet confirmed by a posted bill. `unconfirmed` = no GL category proposed; the human must pick one on first post. The prep-pack surfaces low-confidence proposals more prominently in the queue entry so the human knows to scrutinize.

The confidence field is the refinement most operators won't think to add up front but converge on within the first two months. Without it, every category proposal looks equally trustworthy in the queue entry, and the human ends up second-guessing the safe ones to avoid missing the risky ones. With it, the human's attention concentrates on `medium` and `unconfirmed` entries; `high` entries are one-second approvals.

Population: on first run, read every existing bill from QBO via the Intuit MCP (or via the QBO Bills export if you don't have production credentials yet) and back-fill the mapping. Each entry's category is the most-recent GL category that vendor's bills used; confidence starts `high` for vendors with ≥3 prior bills in the same category, `medium` for 1–2 prior bills, `unconfirmed` for no prior bills (the AP aging surfaces the vendor exists; the category memory hasn't been built yet).

Maintenance: on every approved queue entry, update the corresponding mapping if the human edited the suggested category. Promote confidence (`unconfirmed` → `medium` → `high`) as the same vendor's bills compound the same coding.

The category memory survives even when the queue file is rebuilt from scratch (Gmail re-scanned, prior queue archived). The vendor-category mapping is the durable knowledge; the queue is the ephemeral working surface.

### 7.3 — Delta-vs-prior-month annotation

The single most-valuable annotation in a queue entry. A $400 invoice from a vendor who has billed $200 every month for two years isn't necessarily wrong — but it's the kind of thing the human should pause on. A $147 invoice from a vendor who has billed $147 every month for twelve months is the kind of thing the human can approve in one second.

The mechanism: for each new bill, look up the same vendor's prior month's bill amount; compute the delta.

```
prior_month_amount = lookup(vendor_id, current_month - 1)
delta_amount = current_amount - prior_month_amount
delta_percent = delta_amount / prior_month_amount if prior_month_amount else None
```

Surface in the queue entry:

- `Delta vs prior month: $0.00 — identical to 12 prior months.` (the normal case; one-second human review)
- `Delta vs prior month: +$50 (+12.5%) — first increase since 2025-09-01.` (worth a glance)
- `Delta vs prior month: +$200 (+136%) — largest single-month increase from this vendor on record.` (worth a careful look at the invoice line items)
- `Delta vs prior month: N/A (first bill from this vendor).` (new vendor; the annotation is the absence of prior data, which is itself information)

The delta is what turns the prep-pack from data entry into actual review. The agent's job isn't to suppress the human's judgment; it's to focus the human's attention on the bills that actually need it.

### 7.3.5 — Why the prep-pack stops short of extracting the dollar amount

The most tempting "improvement" a builder will reach for after seeing the prep-pack work: have the agent OCR the dollar amount out of the PDF and fill in the Amount field automatically. The Amount field is the highest-value field on the entry; auto-filling it looks like the obvious win.

Don't. The dollar amount is the one field that should stay a literal `[VERIFY from PDF]` placeholder. The reasoning:

1. **The Amount is the irreversibility multiplier.** Every other field on the entry is recoverable cheaply if the prep-pack gets it wrong: a misclassified GL category re-codes in two clicks, a wrong invoice number gets corrected at post time, a wrong vendor surfaces in the AP aging the next day. A wrong Amount that the human approves on autopilot books the wrong number into AP — and from there propagates into cash forecasting, into the next month's variance analysis, into the tax return.
2. **OCR and PDF text-extraction are right ~98% of the time on clean invoices and ~80% of the time on the ones that matter** (scanned receipts, hand-modified amounts, multi-page invoices with the total on a later page). The 2% / 20% failure mode is silent: the agent confidently fills in `$1,470` for a $14,700 bill and the human's eyes glide right past because the agent has filled in every other field correctly.
3. **The whole point of the prep-pack is to focus the human's attention.** Auto-filling the Amount defeats that focus. With the literal `[VERIFY from PDF]` placeholder, the human must open the PDF and read the number — which means the human's eyes are on the actual source of truth at the moment of the decision. With an OCR'd Amount pre-filled, the human's eyes are on the queue entry, treating it as ground truth.

The general principle: **the prep-pack pre-fills every field that's cheap to fix and leaves a placeholder on every field that's expensive to fix.** Vendor, GL category, invoice number, due date, delta-vs-prior — all pre-filled, all easy to correct if wrong. Amount — placeholder, forcing the human to verify against the PDF.

This is the operator-side complement to Anthropic's broader irreversibility-rate finding (Part 4 §4.5). Within a single prep-pack entry, the same logic applies: pre-fill the reversible fields, leave the irreversible-when-wrong field as the human's job.

The article's earlier framing of "delta annotation focuses attention" (§7.3) is the field-level analog. The Amount placeholder is the entry-level analog. Both flow from the same principle: AI prepares, human commits, the system encodes that boundary at every level of granularity it can.

### 7.4 — The one-screen-per-bill discipline

Every queue entry should fit on one screen at a normal terminal / editor size. If it doesn't, the prep-pack failed at its job. The discipline:

- Bill metadata (vendor, invoice number, date, amount) — five lines max.
- Match status (vendor matched / new vendor / category) — three lines max.
- Delta annotation — one line.
- Source link — one line.
- Action — one or two lines.

Total: 11–13 lines per entry. Comfortably one screen for any modern editor / terminal.

If a bill genuinely needs more context (line-item-level review, multi-PDF attachment, disputed amount), the queue entry should surface that and link to a longer expanded review document — not balloon the queue file itself. The queue is the at-a-glance surface; the deep review lives in a separate per-bill file when needed.

### 7.5 — The human-approval contract

The queue file is the human's interface; the human-approval contract is the agent's interface back. Three structured outcomes per entry:

| Outcome | Marker | Agent's next step |
|---|---|---|
| Approved | `**State:** APPROVED` | If production credentials available: post via `create_bill`. Otherwise: nothing — human pastes into QBO UI directly. |
| Approved with edit | `**State:** APPROVED — edits: [list]` | Apply edits to the payload before posting (or surface edits in the UI-paste instructions). |
| Rejected | `**State:** REJECTED — reason: [text]` | Archive the queue entry to `~/inbox/bills-queue-rejected.md` with the reason. Do not post. |
| Needs human action upstream | `**State:** NEEDS_VENDOR_CREATION` / `NEEDS_PDF` / etc. | Stop. Wait for human to resolve before processing further. |

The agent never auto-marks `APPROVED`. The agent's role ends at `PENDING_REVIEW`; the human transitions to `APPROVED` or `REJECTED`. This is the bright line between prep and act.

### 7.6 — How the prep-pack composes with Claude Code's permission model

The prep-pack is structurally the same shape as Claude Code's own permission model. Claude Code pauses before any modify-system action (file write, Bash command, MCP tool call) and asks the human; the human says yes or no. The prep-pack pauses before any modify-books action (bill post, vendor create, bill payment) and surfaces a queue entry; the human approves or rejects.

The composability: a Claude Code skill that implements the prep-pack runs entirely within the existing permission model. The skill reads Gmail, reads Drive PDFs, writes a local markdown file. None of those steps need explicit per-bill permission — they're all read-and-prep, which the permission model defaults to allowing.

The post-approval step (UI-paste path A; `create_bill` path B) is what crosses the modify-books threshold. In path A, the modify-books step happens entirely in the QBO UI, outside Claude Code's permission scope — the human IS the permission. In path B, the modify-books step is a write tool call (`create_bill`) which Claude Code intercepts and asks the human about per default, layering the platform's permission model on top of the prep-pack's queue-entry approval.

The two layers are independent and additive. The queue-entry approval is the business-logic approval (yes, this is a real bill, code it this way). The Claude Code permission prompt is the tool-call approval (yes, run this MCP tool with these arguments). Both fire; both have to pass.

### 7.7 — State.json for resume

A skill that's processing 20 bills can be interrupted halfway through. State.json is the breadcrumb that lets the next dispatch detect the interruption and resume cleanly.

Shape, similar to the workspace article:

```json
{
  "run_id": "2026-05-26T10-15-00Z-bills",
  "started_at": "2026-05-26T10:15:00Z",
  "phase": "queue_assembly",
  "status": "in_progress",
  "processed": 7,
  "total": 20,
  "current_bill": {
    "vendor": "Acme Hosting Inc",
    "gmail_thread_id": "abc123",
    "step": "category_lookup"
  }
}
```

Write the file before each major phase change. On resume, the next dispatch reads it and either (a) picks up at the recorded step or (b) starts fresh after confirming the prior run completed cleanly.

The four-phase shape for a bills-queue skill:

1. **gmail_scan** — list new bill threads in Gmail
2. **pdf_extract** — extract structured data from each PDF
3. **queue_assembly** — match vendors, look up categories, compute deltas, write queue entries
4. **verify** — re-read the queue file, confirm every Gmail thread is represented exactly once

A skill killed in phase 3 with 7 of 20 processed leaves a half-built queue file. The next dispatch reads state.json, sees `phase: queue_assembly, processed: 7`, and resumes at bill #8. Without state.json, the next dispatch either reprocesses all 20 (creating duplicate queue entries) or skips ahead without knowing where to restart (missing the 13 unprocessed bills).

### 7.8 — The typed contract for a bills-queue-writer sub-agent

If the prep-pack lives inside a Claude Code sub-agent, the typed input/output is the same shape as the workspace article's DriveDocWriter:

```ts
type BillsQueueWriterInput = {
  run_id: string;
  invocation_id: string;
  mode: "scan" | "rebuild" | "verify";
  source: { gmail_label: string } | { drive_folder_id: string };
  queue_file_path: string;             // canonical default: "~/inbox/bills-queue.md"
  vendor_categories_path: string;      // canonical default: "~/inbox/vendor-categories.json"
};

type BillsQueueWriterResult =
  | { type: "scanned"; queue_file_path: string; entries_added: number; entries_flagged: number }
  | { type: "rebuilt"; queue_file_path: string; entries_total: number }
  | { type: "verified"; queue_file_path: string; entries_matched: number; missing_threads: string[] }
  | { type: "skipped_idempotent"; queue_file_path: string; reason: "no_new_threads" }
  | { type: "failed"; reason: "gmail_unauthorized" | "pdf_parse_failed" | "qbo_unreachable" | "queue_file_locked"; message: string };
```

Closed legal outcomes. Orchestrators dispatch on `type` and `reason`. The `failed` variant carries a structured reason so the parent can decide whether to retry, escalate, or fail outright.

### 7.9 — Single-writer rule for QBO

Same shape as the workspace article's single-writer pattern: **one specialized sub-agent owns all QBO writes.** Every orchestrator dispatches to that writer. The writer serializes its own work, owns the idempotency-check and verify-after-write, and returns a typed result.

The risk if you skip this: two agents writing to the same QBO entity in parallel race on idempotency lookups. Both search; both miss; both create. The race window is the time between search and create — typically hundreds of milliseconds, but enough to produce duplicates.

The clean shape: any agent that finds a need to write to QBO dispatches the `qbo-writer` sub-agent. Validators stay read-only. Multiple parallel orchestrators all serialize through the same writer.

### 7.10 — Logging

Every invocation writes to a known per-invocation directory:

```
/tmp/agent-runs/<run_id>/bills-queue-writer/<invocation_id>/
  input.json       # the BillsQueueWriterInput
  state.json       # phase-by-phase breadcrumbs
  queue.md         # snapshot of the queue file after the run
  vendor-categories.json   # snapshot of the category mapping after the run
  output.json      # the BillsQueueWriterResult emitted
  log.txt          # one line per tool call: timestamp, tool, duration, ok/fail
  error.txt        # only on failure; full error payload
```

The same logging discipline as the workspace article. The post-run JSON sits on disk forever; "the books looked wrong yesterday" becomes a question with an answer.

---

## Part 8 — How to measure whether your QBO automation is healthy

Three observability surfaces, in order of leverage.

### 8.1 — Per-write log directories

Per the logging section above. The post-run snapshot is the ground truth for any past prep-pack run or QBO write. Diff `pre_state` (vendor-categories.json before the run, AR/AP aging before the write) vs. `post_state` (the same files / reads after the run) to see exactly what changed and didn't.

This catches the question "did the bill that landed in QBO Tuesday actually come from my agent, or did somebody enter it manually?" in seconds rather than as a multi-hour reconciliation.

### 8.2 — Sources of truth (daily drift report)

A scheduled job that walks every tracked QBO surface and computes deltas against the prior run.

| Source | Read | What a drift indicates |
|---|---|---|
| AR aging delta | `qbo_accounting_get_ar_aging_summary` — diff day-over-day | New invoices landed, customers paid, invoices were voided, or duplicate-invoice drift |
| AP aging delta | `qbo_accounting_get_ap_aging_summary` — diff day-over-day | New bills landed, vendors were paid, or duplicate-bill drift |
| Queue staleness | Read `~/inbox/bills-queue.md` mtime + count `PENDING_REVIEW` entries | If staleness > 1 week or count > 10, the prep-pack is producing entries faster than the human is reviewing them — operational signal |
| Vendor record count | `qbo_contact_search_customer` with empty query — count records (or use the Intuit MCP's `search_vendor` for the AP side if production credentials exist) | Sudden jump = the agent over-created records. Sudden drop = a merge or deletion happened that should be audited. |
| Catalog count | `qbo_accounting_get_product_service_list` — count | Same shape: jump or drop = surface for audit. |
| Cash position | Balance sheet bank-account row delta | Out-of-band drift = a bank transaction landed that wasn't expected; AP/AR shouldn't change cash directly. |

Run the drift report daily as a scheduled task; surface results in a single channel (email, Slack, dashboard). A day with no drift is the desired state; a day with drift is a single question to triage.

### 8.3 — Failure smells

Five specific failure shapes that show up in a healthy-looking system and indicate the prep-pack is breaking down or an anti-pattern (Part 6) is in play:

1. **Bills booked twice.** Same vendor, same date, same amount, two entries in AP. Diagnosis: a write workflow without search-before-create. See Anti-pattern A-3.
2. **Vendor records duplicated.** "Acme Corp" and "ACME Corp" both appear in the vendor list. Diagnosis: identity-write idempotency skipped name normalization. See Part 5 §5.3.
3. **Sales-out entries showing up as AP, or vice versa.** Revenue inflated by vendor invoices; or AP credits showing as customer credits. Diagnosis: someone used `qbo_sales_create_invoice` to record a bill. See Anti-pattern A-1.
4. **Prep-pack entries that never close.** The queue file accumulates `PENDING_REVIEW` entries faster than the human approves them. Diagnosis: either the prep-pack is over-scoping (catching things it shouldn't surface) or the human's review cadence isn't matching the prep-pack's production rate. Operational: dial back the prep-pack's scan frequency or set up a calendar reminder for a regular review window.
5. **`quickbooks-transaction-import` calls in skill logs followed by no AP changes.** Diagnosis: someone is using the transaction-import tool thinking it creates bills. See Anti-pattern A-5. Either retrain the skill prompt or remove the tool from the skill's allowlist if it's never the right tool for that workflow.

### 8.4 — Post-deploy smoke test

Whenever you change any QBO-touching skill (or the Intuit MCP server itself), run an end-to-end smoke test against the sandbox QBO company:

1. Dispatch the skill with sandbox credentials and a known small set of test inputs.
2. Read the resulting QBO state via the corresponding `qbo_*_get_*` tool.
3. Confirm every expected entity landed; confirm no unexpected entities appeared.
4. Confirm the queue file (if applicable) has the expected entries.

A failing smoke test catches regressions before they hit the production QBO company. This is especially important after Intuit API version bumps, MCP server updates, or any change to the prep-pack's per-vendor category memory.

### 8.5 — The QBO UI is not a measurement tool

"It looked right when I opened QBO" is not the same as "the JSON state matches what was written." Always go to the entity reads for ground truth. The UI renders state with formatting, sometimes with delays, and sometimes with summaries that hide individual entity counts. The reads are the contract.

This is the QBO analog of the workspace article's "the Drive UI is not a measurement tool" — same principle, different platform.

---

## What we still don't know

1. **Whether Anthropic will expand the bundled claude.ai Intuit MCP to include bill-side writes.** The current asymmetry is consistent with deliberate scoping — only sales-out writes are exposed because they correspond to actions the user has already decided on. A future expansion would be useful for users who have already done bookkeeper training; the absence is not a defect. Watch the connector release notes.

2. **Whether Intuit will streamline the app-assessment process for narrow internal-use apps.** The current process is the same regardless of whether the app is a public marketplace product or a single-operator integration. A faster lane for the latter — analogous to Google's "Internal" OAuth user type, which skips verification — would close the path-B math gap for a much larger share of solo operators. As of mid-2026, no such lane exists.

3. **Whether the "AI bookkeeper" category will converge on the prep-pack pattern or push autonomous execution.** Most current pitches in the category lean autonomous. Anthropic's own published data — 0.8% irreversibility, 73% human-in-loop — suggests the durable design pattern is prep-then-approve, but the market has not finished sorting yet. Practitioner-survey-style empirical data on which pattern produces fewer bookkeeping errors would settle it.

4. **Whether QuickBooks Online's UI will close the prep-pack gap natively.** A "review queue from Gmail" feature in QBO itself would obsolete the markdown-queue version of this pattern. The current QBO inbox feature handles PDFs from email but does not do vendor-matching, category-proposal, or delta-vs-prior-month annotation. If those land, the prep-pack moves into the platform — but the underlying principle (AI prepares, human approves) survives unchanged.

5. **Whether the Intuit MCP server's refresh-token rotation will get more operationally friendly.** Today the deployment-shape constraint (persistent secret storage required) rules out cloud-function-only architectures. A future Intuit OAuth flow that supports machine-to-machine credentials, or a longer-lived refresh-token model, would expand the deployable surface. No public roadmap commitment as of mid-2026.

6. **Whether bank-feed transactions will become reachable via the standard accounting API.** Today "For Review" bank-statement line items are explicitly out of scope per Intuit policy; integrators are expected to use Plaid / Yodlee / similar bank-data services. A future opening of that surface would simplify a lot of reconciliation automation. Unlikely soon (Intuit has cited "economic and security constraints"), but worth tracking.

7. **Whether QBO will add a typed-output mode for entity writes that includes a verify hash.** Today every QBO write returns the created entity in the response; verifying requires comparing field-by-field. A future API that returns a content-hash of the entity as committed would let agents verify in one comparison instead of N. Speculative; no public hint.

8. **Whether the connector parity issues that affect Google Drive will hit the QBO connector too.** The workspace article documents skill-context-vs-direct-prompt regressions in Drive. As more skills get deployed against the bundled QBO connector, the same class of regression seems likely to appear. Watch the [claude-code issue tracker](https://github.com/anthropics/claude-code/issues) for QBO-tagged reports.

---

## Your next step

Three concrete moves depending on where you are today:

- **You have ≤10 contractor or recurring bills per month and don't yet have a bills queue.** Start with the minimum viable prep-pack from the [60-second map](#if-you-read-nothing-else-this-is-the-minimum-viable-prep-pack). One skill file, one hour of setup, no Intuit Developer account required. The next bill that arrives in your inbox is the first one you run it on.
- **You have 10–50 bills/month or a bookkeeper-in-the-loop.** Stay on Path A but invest in the per-vendor category memory ([§7.2](#72--per-vendor-category-memory)) and the delta-vs-prior-month annotation ([§7.3](#73--delta-vs-prior-month-annotation)). The compounding value is in not having to re-decide categories every month. Path B is a six-to-twelve-month watch item — revisit when the manual review feels like the bottleneck, not the friction.
- **You have 50+ bills/month or are building an internal-use tool for a client.** Start the Intuit Developer app-assessment process today; the timeline is the binding constraint, not the OAuth integration. While that's in flight, build the prep-pack as the interim and as the human-in-the-loop layer that survives the cutover. [Part 1 §1.3](#13--the-intuit-official-mcp-server-inventory) covers the official MCP server setup.

The article's load-bearing claim is that the right answer is volume-dependent, and that for most readers of an article like this one, Path A is the answer for longer than instinct suggests.

---

## Sources & Attribution

This guide synthesizes patterns and failure modes from running QuickBooks Online automation in production through 2025–2026, the live tool inventory of the bundled claude.ai Intuit MCP, primary documentation from Anthropic and Intuit, and practitioner sources on Intuit's developer-portal journey. The source taxonomy applied throughout: **data > primary docs > opinion**. Every load-bearing claim links inline; every load-bearing number was checked against its primary source.

### Anthropic — primary documentation and research

- [Measuring AI Agent Autonomy in Practice](https://www.anthropic.com/research/measuring-agent-autonomy) — Anthropic research, Feb 18 2026. Source of the 80% / 73% / 0.8% figures on safeguards, human-in-loop, and irreversibility across deployed Claude agents. The data anchor for the prep-don't-act argument; the verbatim statistics quoted in Part 4 §4.5.
- [Best practices for Claude Code](https://code.claude.com/docs/en/best-practices) — the canonical reference for Claude Code's interruption-then-approval default; "Claude Code requests permission for actions that might modify your system" verbatim. The basis for treating the prep-pack as the same shape as Claude's own permission gate.
- [Building Effective AI Agents](https://www.anthropic.com/research/building-effective-agents) — the evaluator-optimizer pattern and the discussion of agents pausing for human feedback at checkpoints; the architectural backbone of the prep-pack-as-pattern framing.
- [Claude Agent SDK — Subagents reference](https://code.claude.com/docs/en/agent-sdk/subagents) — authoritative for Claude Code sub-agent semantics; the basis for the single-writer pattern in Part 7 and the typed-contract shape of `BillsQueueWriterInput` / `BillsQueueWriterResult`.
- [How Anthropic built its multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system) — the orchestrator-worker pattern and typed-return-contract design that the prep-pack's discriminated-union return implements.
- [Model Context Protocol specification (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25) — the protocol every MCP server implements; covers the connector model and JSON-Schema tool inputs/outputs that both the bundled MCP and the Intuit MCP conform to.

### Intuit — primary developer documentation

- [QuickBooks Online Bill API reference](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/bill) — the official Bill entity reference; documents the POST endpoint and the VendorRef requirement. Cited for the API surface that the bundled MCP omits.
- [QuickBooks Online Vendor API reference](https://developer.intuit.com/app/developer/qbo/docs/api/accounting/all-entities/vendor) — the official Vendor entity reference; documents the create endpoint that pairs with Bill. The structural source of the "vendor-record gap pairs with the bill-creation gap" claim in Part 4 and Part 5.
- [QuickBooks Online Accounting API](https://developer.intuit.com/app/developer/qbo/docs/develop) — the developer-portal entry point for app registration; the gate that begins the production-credential journey.
- [QuickBooks Online publishing platform requirements](https://developer.intuit.com/app/developer/qbo/docs/go-live/publish-app/platform-requirements) — the page Intuit lists for app review requirements; cited for the existence of the assessment gate without verbatim quotation (page is SPA-rendered).
- [What to expect during the app review process](https://developer.intuit.com/app/developer/qbo/docs/go-live/list-on-the-app-store/what-to-expect-during-the-review) — Intuit's own stated 3-day technical / 7-day security / 5-day marketing breakdown.
- [App assessment process FAQ](https://help.developer.intuit.com/s/article/New-app-assessment-process-FAQ) — Intuit help article on the assessment process structure.
- [QuickBooks API OAuth 2.0 and authorization FAQ](https://developer.intuit.com/app/developer/qbo/docs/develop/authentication-and-authorization/faq) — Intuit's own FAQ for the OAuth flow; cited for the single-scope (`com.intuit.quickbooks.accounting`) design and the token rotation behavior.
- [QuickBooks Online API rate limits](https://developer.intuit.com/app/developer/qbo/docs/develop/rest-api-features) — context for the throughput limits the Intuit MCP path inherits.

### Intuit — official MCP server

- [intuit/quickbooks-online-mcp-server](https://github.com/intuit/quickbooks-online-mcp-server) — Intuit's Apache-2.0 MCP server, ~238 stars at the time of writing, exposing 144 tools across 29 entity types with full Bill / Vendor / BillPayment / JournalEntry CRUD. The reference implementation for path B. README verified by direct WebFetch on the canonical README.
- [intuit/quickbooks-online-mcp-server README](https://github.com/intuit/quickbooks-online-mcp-server/blob/main/README.md) — exact tool list and environment-variable requirements quoted in Part 1 §1.3.

### Documented limitations

- [Top 5 QuickBooks API Rate Limits (Satva Solutions, 2026)](https://satvasolutions.com/blog/top-5-quickbooks-api-limitations-to-know-before-developing-qbo-app) — independent practitioner walkthrough of QBO API rate limits and gotchas.
- [How to fetch or retrieve For Review Bank Transactions from QuickBooks Online API — Intuit Developer community Q&A](https://help.developer.intuit.com/s/question/0D54R00009bVhVySAK/how-to-fetch-or-retrieve-for-review-bank-transactions-from-quickbooks-online-api) — primary source for "bank-statement line items are not exposed via the public API," the structural evidence behind Anti-pattern A-5.
- [QuickBooks Bank Feed Integration Guide (Apideck)](https://www.apideck.com/blog/quickbooks-bank-feed-integration) — primary practitioner source for the FDP / OFX separation. Establishes that `quickbooks-transaction-import` does not wrap the Bill creation API.
- [Bank transactions reconciliation with QBO Bank Feeds (Codat docs)](https://docs.codat.io/bank-feeds/guides/bank-feeds-tutorial) — corroborating reference: documents QBO bank-feeds as a distinct integration category from the core accounting API.
- [QuickBooks Bank Feeds: Integrate Bank Transactions (Rutter blog)](https://www.rutter.com/blog/introducing-quickbooks-bank-feeds-integrate-bank-transactions-with-your-accounting-platform) — corroborating reference: integrator-platform perspective on the bank-feed path as a distinct surface.
- [QuickBooks Online API: Bill entity overview (Intuit help)](https://quickbooks.intuit.com/learn-support/global/help-articles/quickbooks-online-help-search/00/online-help-search) — QBO end-user help corroborating the Bill vs Invoice semantic distinction at the product level.
- [Standard model: Vendor entity (Codat reference)](https://docs.codat.io/accounting-api/schemas/accounting-vendor) — third-party integrator's normalized view of the Vendor entity across accounting platforms; cross-checks the required-fields shape for `create_vendor`.
- [QuickBooks Payments API overview](https://developer.intuit.com/app/developer/qbpayments/docs/learn/explore-the-quickbooks-payments-api) — the separate payments API (distinct from the accounting API); cited to clarify that payment links from the bundled MCP wrap the accounting-API surface, not the payments API.

### Practitioner sources on the QuickBooks app-assessment process

- [QuickBooks Online API Integration Guide (Knit, 2026)](https://www.getknit.dev/blog/quickbooks-online-api-integration-guide-in-depth) — independent practitioner walkthrough of the OAuth flow and scope model; cross-checks the `com.intuit.quickbooks.accounting` scope name and the multi-week production-credential timeline.
- [Set up the QuickBooks Online integration (Codat docs)](https://docs.codat.io/integrations/accounting/quickbooksonline/accounting-quickbooksonline-new-setup) — practitioner reference for the app-assessment questionnaire and the typical multi-week production-credential turnaround.
- [QuickBooks Intuit Developer Portal: App Setup Guide (Satva Solutions, 2026)](https://satvasolutions.com/blog/quickbooks-online-app-using-intuit-developer-portal) — independent confirmation of the same review process structure.
- [How Long Does Intuit App Store Approval Take? 2026 Developer Timeline (Satva Solutions)](https://satvasolutions.com/blog/intuit-app-store-approval-timeline-developer-guide) — primary source for the "6 weeks to 6+ months" real-world timeline cited in Part 1 §1.4 and Part 4 §4.3; documents the divergence between stated 3-day technical review and real-world months-long waits.
- [QuickBooks Community: marketplace review timeline thread](https://quickbooks.intuit.com/learn-support/en-us/reports-and-accounting/can-we-expect-the-app-to-be-published-on-the-marketplace-soon-i/00/1447233) — corroborating community discussion of the assessment timeline.

### Dedicated AP platforms — pricing and positioning

- [BILL Pricing & Plans](https://www.bill.com/product/pricing) — BILL's own pricing page, source of the $49 / $65 / $89 per-user-per-month tier numbers for the AP/AR product.
- [How Small Businesses Use Ramp Bill Pay to Automate AP](https://ramp.com/blog/bill-pay-guides/small-business) — Ramp's own positioning of Bill Pay for small businesses, used to characterize the bundled-with-cards model.
- [Pilot launches fully autonomous AI bookkeeper (Accounting Today, Feb 2026)](https://www.accountingtoday.com/news/pilot-launches-fully-autonomous-ai-bookkeeper) — primary source for the autonomous-AI-bookkeeper counter-argument addressed in Part 4 §4.6.5.
- [Botkeeper alternatives (GetUku)](https://getuku.com/articles/botkeeper-alternatives) — practitioner overview of the autonomous-AI-bookkeeping vendor landscape (Botkeeper, Digits, Booke AI, others); used to scope §4.6.5 beyond a single vendor.

### Trusted community voices on AI + QuickBooks

- [I Needed an AI Bookkeeper, So I Gave QuickBooks 143 New Tools (Eric Grill)](https://www.ericgrill.com/blog/quickbooks-mcp-ai-bookkeeper) — the practitioner who expanded the `intuit/quickbooks-online-mcp-server` from its initial surface to 144 tools across 29 entity types. Grill's blog is the primary practitioner walkthrough of the path-B build experience; the tool-count claim in Part 1 §1.3 ultimately traces to Grill's work, not Intuit's marketing.
- [Designing agentic loops (Simon Willison)](https://simonw.substack.com/p/designing-agentic-loops) — Simon Willison's general framework for agent-loop design, with explicit guidance on isolating financial-spend operations behind human approval. The prep-pack-as-permission-gate framing in Part 4 §4.4 is downstream of Willison's broader argument that high-stakes side effects must be reversible-by-design.
- [HN: AI coding is sexy, but accounting is the real low-hanging target](https://news.ycombinator.com/item?id=46238354) — Hacker News thread surfacing the same operator observation this article makes from a different angle: small-business accounting is structurally underserved by AI tooling. Top comments echo the prep-pack thesis without the explicit naming.
- [HN: How AI Is Changing Bookkeeping](https://news.ycombinator.com/item?id=45110329) — Hacker News thread with top comments from bookkeepers and CFO-for-hire practitioners on where AI helps and where it doesn't. Independent corroboration of the "AI assists, human commits" pattern from the supply side.
- [QuickBooks MCP: Setup Guide for Controllers (Numeric)](https://www.numeric.io/blog/quickbooks-mcp) — controller-perspective walkthrough of the QBO MCP setup process; cross-checks the Intuit MCP installation path and surfaces the practitioner-friction points the official docs don't surface.

### Adjacent technique references from the RMW Commerce library

- [Operating Google Drive, Docs, Sheets, and Slides from Claude](https://github.com/watsonrm/rmwcommerce/blob/main/guides/operating-google-workspace-from-claude.md) — the "verify-by-JSON" pattern transfers directly to the prep-pack: the queue entry is the human's audit trail before the API write happens. The same discipline of treating tool-call success as separate from task success applies in QBO writes (Part 3 §3.4, Part 6 anti-pattern A-2). The single-writer pattern, the typed-contract shape, the state.json breadcrumbs, the daily drift report — all imported wholesale from the workspace article and adapted to the QBO entity model.
- [The Prompts-to-Agents Ladder](https://github.com/watsonrm/rmwcommerce/blob/main/the-prompts-to-agents-ladder.md) — the ladder framework Rick uses to decide whether a workflow stays as a prompt, becomes a skill, or graduates to an agent. The contractor-invoice prep-pack lives on the skill rung; the full Intuit-MCP integration with sub-agents lives on the agent rung. The judgment about which rung any workflow belongs on is the load-bearing decision; this article is one applied case.
- [Claude Code for Non-Developers: A Field Guide](https://github.com/watsonrm/rmwcommerce/blob/main/claude-code-for-non-developers.md) — the meta-skill framing. The audience for the present article overlaps significantly; readers who want the broader version of "what to ask Claude to do for you" should start there.
- [Making Claude Faster](https://github.com/watsonrm/rmwcommerce/blob/main/making-claude-faster.md) — the six levers for skill / agent / routine speed. Lever 1 (prompt caching) and lever 3 (parallel tool calls) are directly applicable to the prep-pack: cache the per-vendor category mapping in a stable file; parallelize the Gmail-scan + PDF-extract + QBO-vendor-search reads.

### Machine-readable identity

This article applies the [Marketing to Agents](https://github.com/watsonrm/rmwcommerce/blob/main/marketing-to-agents.md) playbook to itself — JSON-LD `Article` schema is auto-emitted in `<head>` by the repository's Jekyll `_includes/head-custom.html` whenever a guide carries `agent_friendly: true` in its frontmatter (this one does). Agents indexing the rendered HTML at [watsonrm.github.io/rmwcommerce](https://watsonrm.github.io/rmwcommerce/guides/quickbooks-automation-using-claude-code.html) see a typed `Article` with author `sameAs` references; publisher `Organization` is RMW Commerce Consulting; license is CC BY-NC-ND 4.0. Agents fetching the raw markdown see the equivalent metadata in the YAML frontmatter at the top of this file.

---

The patterns and anti-patterns documented here emerged from a real Tuesday afternoon attempt to write a skill that would file contractor bills in QuickBooks, a check of which tools were actually available in the author's claude.ai environment, and the realization that the bundled MCP's omission of bill-side writes was load-bearing rather than incidental. The prep-don't-act principle generalized from that single workflow into a pattern applicable across every QBO write surface, and from there into a coherent architecture (Part 7) and measurement discipline (Part 8). The article is the public form of that working note, expanded into a reference manual for any operator considering an AI-assisted QuickBooks workflow.
