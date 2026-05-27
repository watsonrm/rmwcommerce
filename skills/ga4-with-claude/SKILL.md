---
name: ga4-with-claude
description: >
  Read Google Analytics 4 (GA4) data with Claude and produce digests, conversion
  and user-behavior analysis, or paid-media funnel views. Picks the right GA4
  surface for the question (the Data API / official GA4 MCP server for quick
  dashboard-matching answers, the BigQuery export for exact, complex, or
  cross-channel work), wires read-only access with cost guardrails, and labels
  every number observed or modeled. TRIGGER when the user says "read my GA4 with
  Claude", "set up GA4 analytics for Claude", "build my GA4 weekly digest",
  "analyze my GA4 in BigQuery", "GA4 conversion analysis", or "blended ROAS / CAC
  from GA4 and ad spend". The full reasoning lives in the companion guide,
  guides/ga4-with-claude.md.
---

# GA4 with Claude — Data API, BigQuery, and the Multi-Source Warehouse

Operational procedure for reading GA4 with an agent. The guide is the *why*; this
is the *how*. Work top to bottom: pick the surface, wire it read-only, read it,
label the numbers, verify.

## Step 1 — Pick the surface from the question

Ask the user what they want to learn and which property, then route:

- **One property, standard questions, wants dashboard-matching numbers**
  (sessions, top pages, conversion rate by channel, GA4's own funnels), or
  **realtime (last ~30 min)** → **Data API / official GA4 MCP server** (Step 2A).
  Do not stand up a warehouse for this.
- **Exact/unsampled numbers, a question the report shape can't express**
  (per-user paths, custom funnels, full long tail), **heavy iteration**, or
  **history older than 14 months** → **BigQuery export** (Step 2B).
- **Paid-media funnels: blended ROAS, CAC, cross-channel attribution** → BigQuery
  with ad spend loaded beside GA4 (Step 2B + Step 5).
- **Act on the data** (push an audience to Google Ads/Meta, suppress converters)
  → reverse-ETL (Hightouch, Fivetran Activations); out of scope for a read agent, flag it.

If the user is unsure, default to 2A for a single small site, 2B once they mention
exact numbers, ad spend, or "doesn't match my other tool."

## Step 2A — Wire the Data API path (official GA4 MCP server)

`googleanalytics/google-analytics-mcp` wraps the Data + Admin APIs (ADC auth).
It returns the same modeled numbers as the dashboard. Confirm it is installed and
configured in the client; then use `run_report`, `run_realtime_report`,
`run_funnel_report`, `get_account_summaries`.

Limits to respect and surface to the user: 10 metrics / 9 dimensions per request,
10,000 rows per request (paginate with `limit`/`offset` for more), sampling on
large or segmented queries, 200k-token/day budget on standard properties, and no
joins to non-GA4 data. When a request hits a wall, switch to 2B.

## Step 2B — Wire the BigQuery path, read-only

Require these before querying. Never skip the guardrails.

1. **Read-only service account**, dataset-scoped where possible:
   `roles/bigquery.jobUser` (run jobs) + `roles/bigquery.dataViewer` on the GA4
   export dataset. No write/DDL roles.
2. **Serve it via the MCP Toolbox** (`googleapis/mcp-toolbox`) with a
   write-blocked, dataset-restricted source:
   ```yaml
   sources:
     ga4-export:
       kind: bigquery
       project: <gcp-project>
       writeMode: blocked
       allowedDatasets: [analytics_<property_id>]
   ```
3. **Cap every query.** Dry-run for the byte estimate first (free), then run with
   a hard ceiling. A query over the cap fails without charge.
   ```bash
   bq query --use_legacy_sql=false --dry_run '<sql>'
   bq query --use_legacy_sql=false --maximum_bytes_billed=1000000000 '<sql>'
   ```
4. **Always filter the date partition.** Every query constrains
   `_TABLE_SUFFIX BETWEEN 'YYYYMMDD' AND 'YYYYMMDD'`. A wildcard with no filter
   scans every exported day and is the main cost-blowout.

## Step 3 — Read sessions/conversions from the modeled layer, not raw events

Sessions, engaged sessions, channel grouping, and attribution are NOT columns in
`events_*`. Do not compute them ad hoc. If the project has the **dbt-ga4** package
(Velir) built, query its `dim_/fct_` session and channel models. If it does not,
say so and offer to (a) use the package or (b) write vetted views first. Raw-event
session math is the top source of numbers that disagree with the dashboard.

A minimal, partition-pruned sessions/users query (use only if no modeled layer
exists, and label it observed):
```sql
SELECT
  PARSE_DATE('%Y%m%d', event_date) AS date,
  COUNT(DISTINCT user_pseudo_id) AS users,
  COUNT(DISTINCT CONCAT(user_pseudo_id, '-',
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key='ga_session_id'))) AS sessions
FROM `<project>.analytics_<id>.events_*`
WHERE _TABLE_SUFFIX BETWEEN '<start>' AND '<end>'
GROUP BY date ORDER BY date;
```

## Step 4 — Label every number observed vs modeled

This is mandatory in any output. For each figure, state the source:

- **BigQuery export = observed.** Only events actually recorded. No Consent-Mode
  modeling, no modeled conversions, no Google Signals dedup.
- **Data API / dashboard = modeled.** Includes ML estimates for declined-consent
  users and cross-device dedup. This is the official KPI.

If a BigQuery number is lower than the dashboard, that is usually modeling, not a
bug. Say which number you are quoting. Reconcile contested figures against the
dashboard for official KPIs and against BigQuery for "what actually happened."

## Step 5 — Cross-channel (only when asked for ROAS/CAC/attribution)

GA4 cannot answer these alone (no ad cost). Confirm ad spend is in the warehouse:
Google sources via the free BigQuery Data Transfer Service; Meta/TikTok/LinkedIn
via a connector (no free export). Join spend to GA4-derived revenue/conversions in
SQL. Caveat the result: attribution windows, timezone, and currency differ across
platforms, so report blended ROAS (total revenue / total spend) as the defensible
top-line and footnote per-channel splits as "models differ."

## Step 6 — Verify before anything ships

- Recent days are provisional (daily tables settle ~72h; run digests on data ≥3
  days old).
- Standard-property daily export caps at 1M events/day and can drop days; if the
  property is high-traffic, confirm streaming export is on, or flag possible gaps.
- A human spot-checks headline numbers, expecting the observed-vs-modeled gap.

## Guardrails (never violate)

- Read-only IAM, `writeMode: blocked`, byte cap, partition filter: all four, every
  time, before an autonomous query.
- Never present a BigQuery figure as the dashboard's official number.
- Never compute sessions/conversions off raw events without a vetted model.
- Never recommend paying a connector to *extract GA4* (the export is free and more
  accurate); connectors are for the non-GA4 sources and for activation.
