# GA4 with Claude — Data API, BigQuery, and the Multi-Source Warehouse

**Which of the four ways an AI agent can read GA4 is right for your question — and how to avoid the two expensive mistakes: building a warehouse you didn't need, or quoting a sampled number you didn't know was sampled.**

*~10-min skim · ~35-min deep read. For operators improving site conversion, reading user and conversion behavior, and analyzing paid-media funnels with Claude.*

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Google's public Analytics, BigQuery, and Cloud documentation, from Anthropic's Model Context Protocol, and from the named practitioner sources. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

> If you run one small site and want answers that match your GA4 dashboard, do step 1, use the official GA4 MCP server (Path 1), and skip the rest. The warehouse work starts paying off the moment you need exact numbers or you bring in ad spend.

Jump to: [TL;DR](#tldr) · [How to use this](#how-to-use-this) · [The four surfaces](#the-four-surfaces) · [Which one do you need?](#which-surface-do-you-need) · [Path 1: GA4 on its own](#path-1) · [Path 2: BigQuery](#path-2) · [Path 3: the multi-source warehouse](#path-3) · [Path 4: acting on the data](#path-4) · [The traps](#the-traps) · [Sources](#sources--attribution)

---

<a name="tldr"></a>
## TL;DR — what's in it for you

- Most one-site questions are solved by the official GA4 MCP server in 10 minutes. The warehouse only earns its keep when you need exact numbers or you blend in ad spend — knowing which is which is most of this article.
- The one distinction that explains most GA4 confusion: the reporting API and the dashboard show *modeled* numbers; the BigQuery export shows *observed* events. They disagree on purpose. You will be able to say which one your agent is quoting.
- Copy-paste setup for the path most serious work lands on: read-only BigQuery access for Claude, with the SQL, the IAM grant, and the cost cap that keep an autonomous agent from scanning a terabyte by accident.
- An honest read on third-party connectors: when they earn their fee (the data that *isn't* GA4) and when they sell you sampled data you can get raw for free.

### Where to spend your time, in priority order

| # | Practice | Why it matters | Effort |
|---|---|---|---|
| 1 | Decide your surface before you build anything (the [decision tree](#which-surface-do-you-need)) | Most wasted effort here is a warehouse built for a question the dashboard already answers, or an agent quoting sampled numbers it didn't know were sampled | Low |
| 2 | If you need exact or cross-channel data, enable the BigQuery export today | It's free, unsampled, and not retroactive, so a day not exporting is a day you can never query | Low |
| 3 | Put a modeled session layer (the dbt-ga4 package) between the agent and raw events | Sessions and conversions are not columns in the export; computing them ad hoc is the top source of wrong answers | Medium |
| 4 | Lock the agent's BigQuery access read-only, with a byte cap and a required date filter | The difference between a safe agent and a four-figure query bill | Low |
| 5 | Label every number observed or modeled, and keep a human check before anything ships | Stops the agent from presenting the export's number as the dashboard's | Low |

---

<a name="how-to-use-this"></a>
## How to use this

The operational form of this guide is the Claude skill at [`skills/ga4-with-claude/`](skills/ga4-with-claude/). Install it once:

```bash
# from a clone of this repo
cp -r skills/ga4-with-claude ~/.claude/skills/
```

Then describe your setup to Claude (property type, whether the BigQuery export is on, and what you want to learn) and say one of these:

> "help me read my GA4 with Claude"
> "set up GA4 analytics for Claude"
> "build my GA4 weekly digest"

Claude loads the skill on demand, picks the right surface for your question, runs the reads with the read-only guardrails below, and labels each number as observed or modeled. The article is the reasoning; the skill is the procedure.

---

<a name="the-four-surfaces"></a>
## The four surfaces

"GA4" is not one API. It is four surfaces with different access, different freshness, and different *numbers*.

| Surface | What it gives you | How an agent reads it | Sampled? | Freshness |
|---|---|---|---|---|
| **Data API v1** (`runReport`, `runRealtimeReport`) | Pre-aggregated reports that match the dashboard | REST, or the official GA4 MCP server | Yes, on large or complex queries | Standard 24–48h; realtime ~30 min |
| **BigQuery export** | Raw, event-level rows | SQL, via the MCP Toolbox or a read-only service account | No. Unsampled, un-thresholded | Daily next-day; streaming continuous |
| **Admin API v1** | Read and write *config* (custom dimensions, audiences) | REST | n/a | Near-immediate |
| **Measurement Protocol v2** | Send *new* events server-side (the only data write) | HTTPS POST | n/a | After processing |

Two facts decide almost everything that follows. First, the Data API and the dashboard return numbers that have passed through sampling, thresholding, and machine-learning modeling; the BigQuery export has not. Second, the Data API can only see GA4. It has no way to sit beside your ad spend or your orders. Hold those two, and the right surface for any given job falls out on its own.

---

<a name="which-surface-do-you-need"></a>
## Which surface do you actually need?

Start from the question you want answered, not from an architecture.

**Your question is about one website, fits what the GA4 dashboard already shows, and you want numbers that match that dashboard.** Sessions last week, top landing pages, conversion rate by channel, the funnels GA4 builds for you. Use the Data API or the official GA4 MCP server. This is [Path 1](#path-1), and for a single property it is frequently the whole job. Do not build a warehouse for it.

**You need exact numbers, or a question the report shape can't express, or history past GA4's retention window.** Anything that gets sampled, per-user path and sequence analysis, custom funnels, the full long tail the dashboard hides in its `(other)` row, or an agent that iterates over hundreds of queries. Land the data in BigQuery and let Claude write SQL. This is [Path 2](#path-2).

**You want paid-media funnels: blended ROAS, customer-acquisition cost, attribution across Google and Meta.** This needs ad spend sitting next to site conversions, which GA4 cannot do alone. You need a warehouse with more than GA4 in it. This is [Path 3](#path-3).

**You want to act on the analysis, not just read it.** Push a high-value audience back into Google Ads, suppress recent converters, sync a segment to your CRM. This is [Path 4](#path-4), reverse-ETL.

Most teams start at Path 1, discover a question it can't answer, and graduate to Path 2 or 3. The rest of this guide is each path in turn, with the setup you need to run it.

---

<a name="path-1"></a>
## Path 1 — GA4 on its own (Data API and the official GA4 MCP server)

For a single property and standard questions, GA4's own reporting is the right tool, not a fallback. Setup is close to zero, and the numbers match the dashboard your stakeholders already look at, because you are reading the same modeled figures (more on that under [Path 2](#path-2)).

Google now ships an official MCP server, `googleanalytics/google-analytics-mcp` (Apache-2.0, self-labeled *Experimental*, actively maintained). It wraps the Data and Admin APIs and hands Claude tools such as `run_report`, `run_realtime_report`, `run_funnel_report`, and `get_account_summaries`, authenticating through Application Default Credentials ([repo](https://github.com/googleanalytics/google-analytics-mcp), [Google docs](https://developers.google.com/analytics/devguides/MCP)). A Claude Desktop entry looks like this (install the server per the repo, then point the config at it):

```jsonc
// claude_desktop_config.json
{
  "mcpServers": {
    "google-analytics": {
      "command": "pipx",
      "args": ["run", "google-analytics-mcp"],
      "env": { "GOOGLE_APPLICATION_CREDENTIALS": "/path/to/key.json" }
    }
  }
}
```

The best use case, precisely: a person talking to one GA4 property, asking standard-report questions, wanting dashboard-matching answers, with no warehouse. "How did organic do last week versus the week before? Which landing pages converted best? How many active users right now?" It also owns the one thing no other surface does cleanly, the realtime view of the last 30 minutes, which the BigQuery export lags by hours.

Know its ceilings before you lean on it. Every request caps at 10 metrics and 9 dimensions, returns up to 10,000 rows per request (paginate with `limit` and `offset` for larger result sets), rejects incompatible dimension and metric pairs, and draws against a 200,000-token-per-day budget on standard properties ([Data API basics](https://developers.google.com/analytics/devguides/reporting/data/v1/basics), [quotas](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas)). Large or segmented queries get sampled. None of it can join to data outside GA4. When a question runs into one of those walls, you are on Path 2.

The Admin API rides the same server for *config*: read your data streams and custom definitions, or create a custom dimension. Writing config needs the `analytics.edit` scope, a real step up from read-only, so grant it deliberately and leave it off for analysis work.

---

<a name="path-2"></a>
## Path 2 — BigQuery, when GA4's reporting isn't enough

Enable the export from GA4 Admin under BigQuery links. It is free (you pay only BigQuery storage and query), it captures every raw event with no sampling or thresholding, and it is **not retroactive**, so turn it on before you need the history. High-traffic standard properties should also enable streaming export, because the daily export caps at one million events per day and can pause if you persistently exceed it ([setup](https://support.google.com/analytics/answer/9823238), [export details](https://support.google.com/analytics/answer/9358801)). The export keeps your events for as long as you choose, which matters because GA4 standard properties retain event-level and Explorations data for at most 14 months ([data retention](https://support.google.com/analytics/answer/7667196)).

### What "the number" means: observed vs modeled

This is the idea that trips up every agent setup, so here it is in plain terms. GA4's numbers come in two kinds:

- **Observed**: events that were recorded. A real browser fired a real event and GA4 collected it. The BigQuery export is exactly this, every raw recorded event, nothing added.
- **Modeled**: numbers GA4 estimates for activity it could not record directly. When a visitor declines cookies, GA4 can't see that person, so in the *dashboard* it uses machine learning to estimate how many users and conversions that group probably represented, and adds the estimate to the total. It also merges the same person across phone and laptop using Google Signals. None of these estimates are real recorded events, so none of them reach the BigQuery export ([Google: UI vs BigQuery](https://developers.google.com/analytics/blog/2023/bigquery-vs-ui), [Behavioral modeling for Consent Mode](https://support.google.com/analytics/answer/11161109)).

A worked example. Say 1,000 people converted last week and GA4 directly recorded 800 of them; the other 200 had declined cookies. Your dashboard shows roughly 1,000 conversions (800 observed plus a ~200 modeled estimate). BigQuery shows 800 (only what was recorded). Neither is wrong. The dashboard is estimating the full picture; the export reports what happened. It can run the other way too: Google Signals merges duplicate people in the dashboard, so the dashboard's *user* count can land below the export's count of distinct device IDs.

So when this guide treats BigQuery as the source of truth, it means observed-event truth. For "what happened in the data," the export wins. For "GA4's official conversion number," the figure your boss or your ad platform sees, the dashboard is authoritative by definition, because that number *is* the modeled one. An agent's job is to know which it is quoting and say so ([ga4bigquery.com on why the two don't match](https://www.ga4bigquery.com/why-your-bigquery-results-dont-exactly-match-with-the-google-analytics-reports/)).

### The schema you are querying

An agent writing GA4 SQL has to know the shape of the data or it writes wrong and expensive queries. The export creates one table per day, `events_YYYYMMDD`, which is date-*sharded*, not a single partitioned table. `event_params`, `user_properties`, and `items` are arrays of structs, so you `UNNEST` them to read a value. `event_timestamp` is microseconds since the Unix epoch in UTC; `event_date` is a string in the property's timezone. Session identity lives inside `event_params` as `ga_session_id` ([export schema](https://support.google.com/analytics/answer/7029846), [Adswerve on UNNEST](https://adswerve.com/blog/ga4-bigquery-tips-event-parameters-and-other-repeated-fields-part-two)). A correct, partition-pruned count of sessions and users looks like this:

```sql
SELECT
  PARSE_DATE('%Y%m%d', event_date) AS date,
  COUNT(DISTINCT user_pseudo_id) AS users,
  COUNT(DISTINCT CONCAT(
    user_pseudo_id, '-',
    (SELECT value.int_value FROM UNNEST(event_params) WHERE key = 'ga_session_id')
  )) AS sessions
FROM `your-project.analytics_123456789.events_*`
WHERE _TABLE_SUFFIX BETWEEN '20260501' AND '20260527'   -- prune partitions; never omit this
GROUP BY date
ORDER BY date;
```

The `_TABLE_SUFFIX` filter is not optional. Without it, the wildcard scans every day you have ever exported, which is the main way an agent runs up a bill.

### Don't compute sessions by hand

That query counts sessions, but engaged sessions, channel grouping, and attribution are not columns either; you reconstruct them from GA4's own logic (30-minute timeout, the `session_engaged` parameter, a source-to-channel mapping, an attribution lookback). Free-handing that per question is the top source of numbers that disagree with the dashboard and with each other. Use the [dbt-ga4 package](https://github.com/Velir/dbt-ga4) (BigQuery-only, maintained). It consolidates the sharded tables into one date-partitioned table, reprocesses the trailing three days to match GA4's late-data window, and ships session, user, and channel models plus last-non-direct attribution and Google's channel mapping. Point the agent at the dbt models, not raw `events_*`. The one caveat to carry: dbt-ga4 is still observed-only, so it gets close to the dashboard but will not equal the modeled number, and that gap is expected.

### Wire Claude to BigQuery, read-only

Serve BigQuery to Claude through Google's MCP Toolbox for Databases, `googleapis/mcp-toolbox` (Apache-2.0, a stable release and actively maintained, the most-starred option). It is a binary that speaks MCP to Claude Desktop or Claude Code and connects to BigQuery, and it locks down cleanly: set the source to block writes and restrict it to your export dataset ([MCP Toolbox repo](https://github.com/googleapis/mcp-toolbox), [Google Cloud guide](https://cloud.google.com/bigquery/docs/pre-built-tools-with-mcp-toolbox)).

```yaml
# tools.yaml
sources:
  ga4-export:
    kind: bigquery
    project: your-gcp-project
    writeMode: blocked          # SELECT-only; rejects INSERT/UPDATE/DDL
    allowedDatasets:
      - analytics_123456789     # restrict the agent to the GA4 export dataset
```

Google also runs a fully managed remote BigQuery MCP server at `bigquery.googleapis.com/mcp` whose docs name Claude as a client; check the [current status](https://cloud.google.com/bigquery/docs/use-bigquery-mcp) before depending on it in production.

Give the agent's service account read-only rights, scoped to the export dataset where possible:

```bash
SA="claude-ga4-reader@your-gcp-project.iam.gserviceaccount.com"
gcloud iam service-accounts create claude-ga4-reader --display-name="Claude GA4 read-only"
# let it run query jobs (project level)
gcloud projects add-iam-policy-binding your-gcp-project \
  --member="serviceAccount:$SA" --role="roles/bigquery.jobUser"
```

```sql
-- let it READ only the GA4 export dataset (least privilege), run in BigQuery
GRANT `roles/bigquery.dataViewer`
ON SCHEMA `your-gcp-project.analytics_123456789`
TO "serviceAccount:claude-ga4-reader@your-gcp-project.iam.gserviceaccount.com";
```

Then cap the spend on every query. Estimate first with a dry run (free), and set a hard byte ceiling so an oversized query fails instead of billing ([cost controls](https://cloud.google.com/bigquery/docs/best-practices-costs)):

```bash
# free estimate: prints the bytes the query would scan
bq query --use_legacy_sql=false --dry_run 'SELECT ... '
# hard cap: a query that would scan more than 1 GB fails, no charge
bq query --use_legacy_sql=false --maximum_bytes_billed=1000000000 'SELECT ... '
```

For belt and suspenders, set `require_partition_filter` on your tables (it forces the date filter shown above) and expose a curated, pre-sessionized view to the agent rather than the raw tables. Read-only role, byte cap, required partition filter, a dry run before execution: those four turn an autonomous agent from a billing risk into a safe reader.

---

<a name="path-3"></a>
## Path 3 — The multi-source warehouse (GA4 as one lens)

The questions that drive real decisions are rarely about GA4 alone. Blended ROAS needs ad spend next to revenue. Customer-acquisition cost needs spend next to new customers. Attribution needs paid and organic in one table. The GA4 Data API exposes only GA4's own metrics and the export omits ad cost entirely, so none of these are answerable inside GA4. You answer them by landing GA4 and the other sources in one warehouse and joining ([Simo Ahava](https://www.simoahava.com/), [Adswerve](https://adswerve.com/)). That is why serious paid-media work ends up in BigQuery: not because BigQuery is fashionable, but because it is the only place the spend and the conversions can sit in the same query.

The sources split cleanly by who owns them:

- **Google's own properties load free and first-party.** The BigQuery Data Transfer Service moves Google Ads, YouTube, Search Ads 360, Campaign Manager 360, Display & Video 360, and Merchant Center into BigQuery, and Google Ads and YouTube transfers are provided at no cost ([DTS docs](https://cloud.google.com/bigquery/docs/dts-introduction)). For the Google stack you need no third party.
- **Everything else is where a connector earns its fee.** Meta, TikTok, LinkedIn, email, and CRM have painful APIs and no free export, so a managed connector (Fivetran, Airbyte, Supermetrics, Funnel) is a reasonable buy. One precise note: Google's DTS now ships a native Facebook Ads connector, but third-party connectors like it follow consumption-based pricing once they leave preview, and TikTok and LinkedIn have no native path at all.

### The connector red-team

The common advice is to buy a connector to get GA4 into your agent workflow. For the GA4 part specifically, that advice is mostly wrong, and here is the test that shows why. Classify any connector by the surface it reads: the **Data API** (sampled, capped at 9 dimensions and 10 metrics) or the **native BigQuery export** (raw). I classified about 18 ingestion tools this way (Airbyte, Hevo, Improvado, Adverity, Dataddo, Rivery, Estuary, Portable, Skyvia, Keboola, Matillion, Daton, Domo, the Power BI and Tableau native connectors, the Singer taps, plus Supermetrics, Funnel, Coupler, Windsor, and Stitch). Sixteen read the Data API. The only genuine native-export reader in the group is Google Connected Sheets, plus any direct SQL client.

So a paid GA4 connector buys convenience, never accuracy: it relays the same sampled numbers your own `runReport` would, and the only unsampled path is the free native export. Three sales claims to distrust:

1. "GA4 to BigQuery" that is Data-API-into-BigQuery in disguise. Rivery's kit, Daton, and Airbyte-to-BigQuery all load Data API output into BigQuery. The rows land in BigQuery but carry every Data API limit. This is not the native export.
2. "No sampling" that covers only standard report endpoints. Improvado markets it; large or segmented queries still sample.
3. "Real-time CDC" on a polling API. Estuary advertises sub-100ms change-data-capture on its GA4 source; the Data API has no CDC mechanism. Under the hood it polls.

Where connectors genuinely earn the money: blending the non-Google sources above, activating data (Path 4), serving non-technical teams with no warehouse, and self-hosted pipelines where data residency matters. None of those is "better GA4 data."

One caution for the agent to voice when it blends: cross-channel numbers never reconcile perfectly. Attribution windows differ (GA4's data-driven model versus Google Ads last-click versus Meta's 7-day click), and so do timezones and currency. Blended ROAS (total revenue over total spend) is the defensible top-line; per-channel splits deserve a "models differ" footnote.

---

<a name="path-4"></a>
## Path 4 — Acting on the data: reverse-ETL

Reading GA4 is half the loop; acting on it is the other half, and it uses a different kind of tool. Reverse-ETL platforms read your warehouse and push records out to SaaS destinations. The GA4-relevant flow: GA4 streams to BigQuery, you build an audience or conversion set in SQL, and the tool activates it into Google Ads, DV360, or Meta ([Hightouch on GA4 reverse-ETL](https://hightouch.com/blog/ga4-reverse-etl)). This is the path for an agent that should *do* something with the analysis, resize an audience or suppress recent converters, and there is no first-party equivalent. It pairs with the export rather than replacing it. Check current pricing before committing to a vendor — the category has seen significant changes: Census was acquired by Fivetran in 2025 and rebranded as Fivetran Activations; Hightouch offers a free tier plus paid plans.

---

<a name="the-traps"></a>
## The traps

Most failures here are silent: the agent returns a number that isn't the one you think.

| You might expect | Reality | What to do |
|---|---|---|
| BigQuery matches the dashboard | It will not. The dashboard adds modeled data the export never receives | Use the export for "what happened," the dashboard for the official KPI; label which |
| `sessions` / `conversions` are columns | They are derived from event rows, not stored | Use the dbt-ga4 models, not hand-rolled session SQL |
| `SELECT *` is fine | BigQuery bills by bytes scanned; a wildcard with no date filter scans every day you have exported | Always filter `_TABLE_SUFFIX`; set `maximum_bytes_billed`; dry-run first |
| The export is complete | Standard properties cap the daily export at 1M events/day and can pause it, dropping days, with no backfill | Enable streaming export, or use 360; treat recent days as provisional |
| Yesterday is final | Daily tables keep updating for ~72h as late events land | Run digests on data three days old; mark recent days provisional |
| The Data API returns everything | It samples large queries and caps each request at 9 dimensions and 10 metrics | Go to BigQuery for exact or wide analysis |
| A "GA4 to BigQuery" connector gives me the export | Most load sampled Data-API output instead | Use the free native export; verify what a connector actually reads |
| Measurement Protocol can backfill history | It sends new events only, within 72 hours | There is no historical write path |

**Anti-patterns, in one place:** pointing an agent at the Data API as the foundation for serious work; computing sessions off raw events; calling BigQuery "ground truth" without the observed-versus-modeled caveat; running an agent over BigQuery with no byte cap; paying a connector to extract GA4 when the export is free and more accurate; and presenting a blended cross-channel number as precise.

---

## Sources & Attribution

**Primary, Google documentation**

- [UI vs BigQuery export: why the numbers differ (modeling, Signals, sampling)](https://developers.google.com/analytics/blog/2023/bigquery-vs-ui) · [Behavioral modeling for Consent Mode](https://support.google.com/analytics/answer/11161109) · [Data retention](https://support.google.com/analytics/answer/7667196)
- [BigQuery Export schema](https://support.google.com/analytics/answer/7029846) · [BigQuery Export setup, freshness, 1M/day cap](https://support.google.com/analytics/answer/9358801) · [Set up the export](https://support.google.com/analytics/answer/9823238)
- [Data API: create a report (10 metrics / 9 dimensions / 10k rows per request)](https://developers.google.com/analytics/devguides/reporting/data/v1/basics) · [Data API limits and quotas](https://developers.google.com/analytics/devguides/reporting/data/v1/quotas)
- [BigQuery cost controls (dry run, maximum_bytes_billed, partitions)](https://cloud.google.com/bigquery/docs/best-practices-costs) · [BigQuery access control / IAM](https://cloud.google.com/bigquery/docs/access-control)
- [BigQuery Data Transfer Service](https://cloud.google.com/bigquery/docs/dts-introduction)

**Primary, agent tooling**

- [Official GA4 MCP server: `googleanalytics/google-analytics-mcp`](https://github.com/googleanalytics/google-analytics-mcp) · [Google docs](https://developers.google.com/analytics/devguides/MCP)
- [MCP Toolbox for Databases: `googleapis/mcp-toolbox`](https://github.com/googleapis/mcp-toolbox) · [Toolbox docs](https://github.com/googleapis/mcp-toolbox/tree/main/docs) · [pre-built BigQuery tools (Google Cloud)](https://cloud.google.com/bigquery/docs/pre-built-tools-with-mcp-toolbox)
- [Managed remote BigQuery MCP server (check current status)](https://cloud.google.com/bigquery/docs/use-bigquery-mcp)

**Trusted practitioners**

- [ga4bigquery.com (Johan van de Werken): why BigQuery and the UI don't match, sessionization, consent mode](https://www.ga4bigquery.com/why-your-bigquery-results-dont-exactly-match-with-the-google-analytics-reports/)
- [Simo Ahava: observed vs modeled, Consent Mode](https://www.simoahava.com/) · [Adswerve: GA4 BigQuery users/sessions and UNNEST](https://adswerve.com/blog/ga4-bigquery-tips-event-parameters-and-other-repeated-fields-part-two) · [InfoTrust: sampling, cardinality, thresholding](https://infotrust.com/articles/google-analytics-4-reports-sampling-cardinality-thresholding/)
- [dbt-ga4 package (Velir)](https://github.com/Velir/dbt-ga4)

**Connector and activation references**

- [Fivetran GA4 connector (Data API)](https://fivetran.com/docs/connectors/applications/google-analytics-4) and [GA4 Export connector (BigQuery)](https://fivetran.com/docs/connectors/applications/google-analytics-4-export) · [Power BI native GA4 connector (documented sampling/row limits)](https://learn.microsoft.com/en-us/power-query/connectors/google-analytics) · [Google Connected Sheets (reads BigQuery, which contains the native export)](https://support.google.com/docs/answer/9702507) · [Hightouch GA4 reverse-ETL](https://hightouch.com/blog/ga4-reverse-etl)
- The 18-tool Data-API-vs-export classification is the author's, built from each vendor's own docs; the tools named (Airbyte, Hevo, Improvado, Adverity, Dataddo, Rivery, Estuary, Portable, Skyvia, Keboola, Matillion, Daton, Domo, Tableau, the Singer taps, Supermetrics, Funnel, Coupler, Windsor, Stitch) were each checked for which surface they read.

**Corrections from prior circulating versions:** most "GA4 + AI" writing says to point a model at the reporting API or to buy a connector. Both are wrong for exact or cross-channel agent work: the reporting API samples and cannot join, and most connectors merely relay it (several "GA4 to BigQuery" products load Data-API output, not the native export). The correct surface for that work is the free native BigQuery export. This guide also corrects the common claim that "BigQuery is the real GA4 number": the export is observed-event data, the dashboard is modeled, and Google's own engineers state the two are not expected to reconcile. The Data API row limit per request is 10,000 (paginate for larger sets), not 100,000 as sometimes stated — the 100k figure was the old Universal Analytics API ceiling. Reverse-ETL vendor pricing and structure changes frequently: Census was acquired by Fivetran in 2025 and is now Fivetran Activations; specific pricing figures have been removed in favor of checking vendor sites directly.

*Source-quality note: figures here trace to primary Google pages; a few that move over time and region (BigQuery price per TiB, the Data API per-report row ceiling, current DTS connector pricing, repo star counts and versions) should be re-confirmed against the live pages at publication. Vendor pricing is 2026-indicative, and vendor documentation pages may block automated link checks.*

---

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. Underlying API and product behavior is the property of Google and documented in the sources above. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
