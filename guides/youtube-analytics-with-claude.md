# YouTube Analytics with Claude — Two Analytics APIs, Not One

**Which of YouTube's three APIs answers your question — the ad-hoc Analytics API, the bulk Reporting API, or the metadata Data API — and the one auth constraint that quietly breaks every unattended agent.**

*~10-min skim · ~30-min deep read. For creators, podcast operators, and media teams reading YouTube performance data with Claude.*

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Google's public YouTube API documentation, from Anthropic's Model Context Protocol, and from the named community sources. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

> If you just want a weekly performance digest, skip to the [decision tree](#which-surface-do-you-need): for serious recurring work, point BigQuery's Data Transfer Service at YouTube and let Claude query the warehouse ([Path 4](#path-4)); for a quick one-off, schedule a Reporting API job and slice the CSV. If you want one video's retention curve, it's the Analytics API and nothing else. The hour you'll lose is almost always the OAuth setup — do it once and persist the grant.

Jump to: [TL;DR](#tldr) · [Where to spend your time](#where-to-spend) · [The three surfaces](#the-three-surfaces) · [Which one do you need?](#which-surface-do-you-need) · [Path 1: metadata](#path-1) · [Path 2: the Analytics API](#path-2) · [Path 3: the Reporting API](#path-3) · [Path 4: BigQuery](#path-4) · [The auth trap](#auth) · [The MCP reality](#mcp) · [The traps](#the-traps) · [Sources](#sources--attribution)

---

<a name="tldr"></a>
## TL;DR — what's in it for you

- The mental model that prevents most wasted work: YouTube performance lives behind **three** APIs, and the analytics half is **two**, not one. The **Analytics API** answers questions you didn't know you'd ask — ad-hoc, one video at a time, and it owns the audience-retention curve. The **Reporting API** answers the questions you ask every week — bulk CSV you slice yourself, with no quota worry. The **Data API** gives you metadata and public counts, and never watch time.
- The constraint nobody mentions until it breaks: **YouTube rejects service accounts.** There is no key-in-a-file path for unattended analytics. Do one interactive OAuth consent, persist the refresh token, and your agent runs off that. Plan for it up front — it is the single most common reason a scheduled YouTube agent silently fails.
- The cleanest unattended-agent setup is a **BigQuery warehouse**: Google's Data Transfer Service auto-loads YouTube's bulk reports into BigQuery for free, after a one-time interactive OAuth. The agent then only ever reads BigQuery — read-only, cost-capped — and never holds a YouTube token. This sidesteps the no-service-account problem entirely.
- The honest MCP read: there is **no official Google YouTube MCP server**, and the popular community ones are metadata-only despite "analytics" in their names. The real agent path is REST-via-OAuth, or a BigQuery warehouse the agent queries with the GA4 guide's read-only wiring.
- The revenue trap: a creator querying their own channel gets **no revenue from the API at all** — revenue analytics is a content-owner (partner / MCN) capability. And current-period revenue is always *estimated* until AdSense finalizes after month-end.

<a name="where-to-spend"></a>
### Where to spend your time, in priority order

| # | Practice | Why it matters | Effort |
|---|---|---|---|
| 1 | Pick your API before building anything (the [decision tree](#which-surface-do-you-need)) | The classic waste is polling the Analytics API on a schedule for data the Reporting API drops as a free CSV — or reaching for analytics when you only needed a title and a view count | Low |
| 2 | Solve the OAuth refresh-token setup once | Service accounts don't work on YouTube; an unattended agent needs a persisted refresh token. This breaks more agent setups than any quota or query bug | Medium |
| 3 | For serious recurring work, let BigQuery's Data Transfer Service load YouTube for you | Free, auto-creates the reporting jobs, and the agent just reads a warehouse — no quota, no token-in-the-agent, full history you control | Medium |
| 4 | For a quick recurring report, schedule a Reporting API job and slice the CSV | Same bulk data without standing up BigQuery — quota is a non-issue and you get deep per-video / traffic / device breakdowns | Medium |
| 5 | For one video's story, use the Analytics API `reports.query` | It is the *only* path to the audience-retention curve — 100 points across the video, one video per call | Low |
| 6 | Label estimated revenue as provisional, and know what the API never gives | Revenue isn't on creator channels at all, and current-period numbers move until month-end | Low |

---

<a name="the-three-surfaces"></a>
## The three surfaces

"YouTube Analytics" is not one API. It is three surfaces with different jobs, different auth, and — critically — different *data*. Two of them carry performance analytics; one carries only metadata.

| Surface | What it gives you | How an agent reads it | Auth | Freshness |
|---|---|---|---|---|
| **Data API v3** | Metadata + public counts: titles, descriptions, playlists, search, comments, transcripts, and `viewCount` / `likeCount` / `commentCount` | REST; API key for public reads, OAuth for owned/private | API key OK for public | Near-immediate for metadata |
| **Analytics API** (`reports.query`) | Ad-hoc aggregated analytics — watch time, retention curves, traffic sources, demographics, this-week-vs-last | REST, one targeted query at a time | OAuth required | ~2–3 day floor |
| **Reporting API** | Bulk predefined CSV reports — deep per-video / traffic / device / geography breakdowns, generated daily | Schedule a job once; download daily CSVs | OAuth required | First report ≤48h after job; ~2-day activity lag |

Two facts decide most of what follows. First, the Data API's `statistics` object stops at public engagement counts — `viewCount`, `likeCount`, `commentCount`. It has **no** watch time, retention, traffic source, or demographics; those live only in the two analytics APIs. Second, every analytics request is about a *specific authenticated owner's* private data, so analytics is OAuth-only — there is no public, key-based path. Hold those two and the right surface for any job falls out.

There's a fourth thing that isn't a fourth API: **BigQuery**. Google's Data Transfer Service lands the Reporting API's bulk data into a warehouse for you on a schedule, which is where serious recurring analysis ends up and the cleanest place to point an agent. It's [Path 4](#path-4), and it's the Reporting API (Path 3) delivered managed rather than a new data source.

---

<a name="which-surface-do-you-need"></a>
## Which surface do you actually need?

Start from the question, not the architecture.

**Your question is about metadata or public counts** — a video's title and description, what's in a playlist, the transcript, a search across the catalog, total views / likes / comments. Use the **Data API v3** ([Path 1](#path-1)). A public API key is enough unless you're touching owner-only fields.

**You're asking an ad-hoc analytical question about your own channel or one video** — how did this upload retain viewers, where did traffic come from this week, this week versus last, which age groups watched. Use the **Analytics API** `reports.query` ([Path 2](#path-2)). It is the only surface that returns the per-video **audience-retention curve**.

**You run the same report every week, or you need deep per-video / per-traffic-source / per-device history at scale.** Use the bulk **Reporting API**. Two ways to take delivery: let **BigQuery's Data Transfer Service** auto-load it into a warehouse ([Path 4](#path-4) — the right call for anything serious or unattended), or schedule the Reporting job yourself and download daily CSVs ([Path 3](#path-3) — fine for a lightweight one-off). Either way quota stops being a concern, because you pull the bulk data once and query it locally.

The split between the two analytics APIs is the decision most writing skips. The shorthand: the Analytics API is for *questions you ask once*; the Reporting API is for *questions you ask every week*. A weekly digest agent built on `reports.query` will hammer the API and still can't get the deep breakdowns at scale — the right shape is bulk Reporting data in a warehouse, with `reports.query` reserved for the one-off retention deep-dive.

---

<a name="path-1"></a>
## Path 1 — The Data API v3 (metadata and public counts)

This is the metadata surface: `videos`, `channels`, `playlists`, `playlistItems`, `search`, `commentThreads`, `captions`, and more. It answers "what is this video" and "what's the public count," and it is the join layer your analytics hangs off — you map a `videoId` to a human title here, then pull that video's watch time from the Analytics API.

Public reads work with a plain API key; anything touching owned or private data, and every write, needs OAuth. The quota is the one most people have met: a **default 10,000 units per day**, resetting at midnight Pacific ([getting started](https://developers.google.com/youtube/v3/getting-started), [quota costs](https://developers.google.com/youtube/v3/determine_quota_cost)). The cost is per method, not per call, and the spread is wide:

| Method | Cost (units) |
|---|---|
| `videos.list`, `channels.list`, `playlists.list`, `playlistItems.list`, `commentThreads.list` | 1 |
| `captions.list` | 50 |
| `search.list` | **100** |
| `videos.update`, `videos.delete`, `playlists.insert` | 50 |
| `captions.insert` / `captions.update` | 400 / 450 |
| `videos.insert` (upload) | high — confirm on the live Quota Calculator before relying on it |

The rough rule Google itself uses — a read costs ~1, a write ~50 — holds *except* for the exceptions that bite: `search.list` is 100, caption writes are in the hundreds. A weekly digest that runs a `search.list` per video burns quota fast; resolve videos by ID (`videos.list`, 1 unit) wherever you can, and cache metadata — it rarely changes.

The hard boundary to hold: the Data API gives you the *what*, never the *how well*. The moment your question involves watch time, retention, where viewers came from, or who they are, you are on Path 2 or 3.

---

<a name="path-2"></a>
## Path 2 — The Analytics API (ad-hoc queries and the retention curve)

The Analytics API is a single endpoint, `GET https://youtubeanalytics.googleapis.com/v2/reports`, that returns aggregated metrics over the dimensions and filters you name ([reference](https://developers.google.com/youtube/analytics/reference/reports/query)). It is built for targeted, real-time questions — you pass `ids`, `startDate`, `endDate`, `metrics`, and optionally `dimensions`, `filters`, and `sort`, and get rows back immediately. A channel owner reads their own data with `ids=channel==MINE`; a partner reads across managed channels with `ids=contentOwner==OWNER_NAME` ([channel reports](https://developers.google.com/youtube/analytics/channel_reports), [content-owner reports](https://developers.google.com/youtube/analytics/content_owner_reports)).

A this-week-versus-last query for one channel, with an OAuth bearer token:

```bash
curl -s -G 'https://youtubeanalytics.googleapis.com/v2/reports' \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode 'ids=channel==MINE' \
  --data-urlencode 'startDate=2026-05-18' \
  --data-urlencode 'endDate=2026-05-24' \
  --data-urlencode 'metrics=views,estimatedMinutesWatched,averageViewDuration,subscribersGained' \
  --data-urlencode 'dimensions=day' \
  --data-urlencode 'sort=day'
```

### The audience-retention curve — only here

The one report worth knowing this API for is **audience retention**, because no other surface gives it. You ask for the `elapsedVideoTimeRatio` dimension, filtered to a single `video==VIDEO_ID`, and YouTube returns **100 data points** from 0.01 to 1.0 — the shape of the drop-off across the video ([dimensions](https://developers.google.com/youtube/analytics/dimensions), [metrics](https://developers.google.com/youtube/analytics/metrics)):

```bash
curl -s -G 'https://youtubeanalytics.googleapis.com/v2/reports' \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  --data-urlencode 'ids=channel==MINE' \
  --data-urlencode 'startDate=2026-01-01' \
  --data-urlencode 'endDate=2026-05-24' \
  --data-urlencode 'metrics=audienceWatchRatio,relativeRetentionPerformance' \
  --data-urlencode 'dimensions=elapsedVideoTimeRatio' \
  --data-urlencode 'filters=video==YOUR_VIDEO_ID'
```

`audienceWatchRatio` is the absolute share of viewers still watching at each point; `relativeRetentionPerformance` (0–1) is how this video holds viewers against all YouTube videos of similar length — the same "above/below typical" read Studio shows. One video per call: there is no comma-separated list here, and there is **no bulk retention report** in the Reporting API, so a per-video retention sweep is genuinely a loop of single calls.

This is the right place to correct a common claim: retention, traffic sources (`insightTrafficSourceType`), and demographics (`ageGroup`, `gender`) are **not** Studio-only. They are all dimensions in the Analytics API. The genuinely Studio-only surface is narrower than people think — see [the traps](#the-traps).

On freshness: the API returns "data up until the last day for which all metrics in the query are available," so the slowest metric in your query sets the floor, and the most recent two to three days are typically not yet final ([data model](https://developers.google.com/youtube/analytics/data_model)). Run digests on data that's a few days old and mark recent days provisional.

---

<a name="path-3"></a>
## Path 3 — The Reporting API (bulk CSV, the recurring-digest engine)

For anything you run on a schedule, this is the surface to build on. Instead of querying live, you create a **job** for a report type once; YouTube then generates a CSV every day and holds it for you to download. Google's own framing: "Quota usage is not an issue because data is retrieved once and then filtered, sorted, and queried within the application" ([Reporting API overview](https://developers.google.com/youtube/reporting)). That single property — pull bulk, slice locally — is why a weekly digest agent belongs here, not on `reports.query`.

The lifecycle is four steps, on the `youtubereporting.googleapis.com` host:

```bash
# 1. List available report types (IDs carry version suffixes — read them live, don't hard-code)
curl -s 'https://youtubereporting.googleapis.com/v1/reportTypes' \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 2. Create a job for one report type
curl -s -X POST 'https://youtubereporting.googleapis.com/v1/jobs' \
  -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Content-Type: application/json' \
  -d '{"reportTypeId":"channel_basic_a3","name":"weekly-basic"}'

# 3. List the CSV reports the job has generated
curl -s 'https://youtubereporting.googleapis.com/v1/jobs/JOB_ID/reports' \
  -H "Authorization: Bearer $ACCESS_TOKEN"

# 4. Download a report's CSV from its downloadUrl
curl -sL 'DOWNLOAD_URL' -H "Authorization: Bearer $ACCESS_TOKEN"
```

Three timing facts shape how you schedule this ([reports guide](https://developers.google.com/youtube/reporting/v1/reports)):

- **First report ≤48h after job creation.** Create the job, then wait — the first CSV (for the day you scheduled it) lands within about two days. (Google's `jobs.create` reference says 24h while the overview says 48h; treat 48h as the planning number and verify by timing a real job.)
- **~30-day backfill on job creation.** When you create a job, YouTube also generates reports for the 30 days *prior*. You cannot get history older than that through the Reporting API — so create the jobs you'll want before you need the data, exactly like the GA4 export.
- **Retention of the files: 60 days for ongoing reports, 30 days for the backfill batch.** Download and store anything you want to keep; the CSVs age out.

The report-type catalog is where the depth lives — `channel_basic_a3`, `channel_traffic_source_a3`, `channel_device_os_a3`, `channel_demographics_a1`, `channel_playback_location_a3`, and more, with a content-owner superset that adds `content_owner_estimated_revenue_a1` and ad-rate reports ([channel report types](https://developers.google.com/youtube/reporting/v1/reports/channel_reports), [content-owner report types](https://developers.google.com/youtube/reporting/v1/reports/content_owner_reports)). The version suffix (`_a1`, `_a3`, `_a4`) increments when Google revises a report's schema and retires the old one, so **call `reportTypes.list` for the live set** rather than hard-coding an ID that will eventually 404.

The prep-pack pattern: schedule the handful of report jobs you care about, drop the daily CSVs into a folder, and point Claude at *that*. The agent reads structured local data — no live quota, no rate limits, full history you control — and the only live calls left are the occasional retention deep-dive on Path 2. When you'd rather not run the download-and-store plumbing yourself, [Path 4](#path-4) hands it to BigQuery.

---

<a name="path-4"></a>
## Path 4 — The BigQuery warehouse (Data Transfer Service)

For serious or unattended work, don't run the Reporting job lifecycle by hand — let Google run it into a warehouse. The **BigQuery Data Transfer Service** ships two native YouTube connectors, **YouTube Channel** and **YouTube Content Owner**, that load the Reporting API's bulk reports into BigQuery on a daily schedule ([channel transfer](https://cloud.google.com/bigquery/docs/youtube-channel-transfer), [content-owner transfer](https://cloud.google.com/bigquery/docs/youtube-content-owner-transfer)). It even creates the reporting jobs for you: "If you don't have existing reporting jobs, setting up the transfer automatically enables YouTube reporting jobs." So this is Path 3 with the plumbing removed.

What you get and what it costs:

- **The transfer is free.** On the pricing page, YouTube Channel and YouTube Content Owner sit in the no-charge connector list, and loading into native BigQuery tables is free — you pay only standard BigQuery **storage and query** ([BigQuery pricing](https://cloud.google.com/bigquery/pricing)). Don't read that as "free end to end"; the warehouse itself still bills storage and queries.
- **One table per report type, date-partitioned.** Each report becomes an ingestion-time-partitioned table prefixed `p_` plus your suffix (e.g. `p_channel_basic_a3_<suffix>`), with a matching view; query by date with the view or the `_PARTITIONTIME` pseudocolumn. Re-running a date overwrites that partition, so backfills never duplicate ([channel transformation](https://cloud.google.com/bigquery/docs/youtube-channel-transformation), [content-owner transformation](https://cloud.google.com/bigquery/docs/youtube-content-owner-transformation)).
- **Schedule and history.** Daily, with a one-day refresh window; the first run lags up to 48 hours while the reporting jobs spin up; backfill reaches only as far as YouTube's source retention (30 days historical, 60 days otherwise). Same lesson as Path 3 and the GA4 export — turn it on before you need the history.
- **Revenue is content-owner-only here too.** The Channel transfer has no revenue tables at all; the Content Owner transfer carries the estimated-revenue, ad-rate, and subscription-revenue families — and you must leave "Hide revenue data" unchecked in the content-owner report settings.

### Why this is the cleanest agent setup

The setup needs a **one-time interactive OAuth grant**, signed in as the human Google Account that owns the channel or content owner (a federated identity or service account can't create the transfer — same YouTube ownership rule as everywhere else). After that, DTS runs the transfer on its schedule unattended. The agent never holds a YouTube token: it reads BigQuery, which is exactly the read-only, cost-capped surface the [GA4 guide](ga4-with-claude.md) already covers. Reuse that wiring directly — the [read-only service account, byte cap, and dry-run guardrails](ga4-with-claude.md#wire-claude-to-bigquery-read-only) are identical for a YouTube dataset. And if you're also landing GA4 and ad spend, you're already building the [multi-source warehouse](ga4-with-claude.md#path-3) where YouTube becomes one more lens. (One hedge: the docs describe scheduled recurring runs but don't promise zero re-auth forever — a revoked grant breaks runs, so monitor it.)

This is the path that turns the [no-service-account trap](#auth) from a blocker into a non-issue: pay the interactive-OAuth cost once at setup, and the agent side stays a plain BigQuery reader.

---

<a name="auth"></a>
## The auth trap — no service accounts

This is the constraint that breaks unattended agents, so it gets its own section. **Both analytics APIs are OAuth-2.0-only.** An API key authorizes public Data API reads; it does nothing for analytics, because analytics is always a specific owner's private data ([authorization guide](https://developers.google.com/youtube/reporting/guides/authorization)).

And the part that surprises people building automation: **YouTube does not support service accounts.** "Since there is no way to link a Service Account to a YouTube account, attempts to authorize requests with this flow will generate a `NoLinkedYouTubeAccount` error" ([authentication](https://developers.google.com/youtube/v3/guides/authentication)). The device flow is unsupported too. Everywhere else in Google Cloud you'd hand an agent a service-account key file and move on; here that path is closed.

The pattern that works: complete an **interactive OAuth user-consent flow once**, capture the **refresh token**, and store it where the agent can read it (a secret manager, or your platform's keychain). The agent exchanges that refresh token for short-lived access tokens unattended, forever, without a human present again. The relevant read scopes:

- `https://www.googleapis.com/auth/youtube.readonly` — Data API, owned reads
- `https://www.googleapis.com/auth/yt-analytics.readonly` — non-monetary analytics
- `https://www.googleapis.com/auth/yt-analytics-monetary.readonly` — adds revenue/ad metrics (content-owner only; see the traps)

For a single creator reading one channel, plain channel OAuth (`ids=channel==MINE`) is all you need. Content-owner credentials (`ids=contentOwner==OWNER_NAME`, plus the `youtubepartner` scope) are for partners and multi-channel networks reading across many channels — and, as the next section's trap notes, they're the *only* way to get revenue out of the API at all.

If holding and refreshing that token inside your agent makes you nervous, don't: [Path 4](#path-4) is the way out. Authorize the BigQuery transfer once, interactively, and the token lives with Google's managed service — your agent reads BigQuery and never touches a YouTube credential.

---

<a name="mcp"></a>
## The MCP reality — there isn't an official one

If you came hoping to drop in a YouTube MCP server and be done, here is the honest state as of this writing. **There is no official Google YouTube MCP server**, for either the Data API or analytics. Google ships a first-party *Google Analytics 4* MCP server (`googleanalytics/google-analytics-mcp`), but that is web/app analytics, not YouTube.

The community fills the gap unevenly. The popular servers — the ones with real adoption, like `ZubeidHendricks/youtube-mcp-server` — are **Data-API-only** despite "analytics" in their names; what they call analytics is the public engagement counts, not watch time or retention. The servers that *do* claim the Analytics API (for example `pauling-ai/youtube-mcp-server`) are early and low-adoption. None is a safe load-bearing dependency yet. (Repo maturity moves fast — re-check before you build.)

So the practical agent path is the one this guide describes directly: **REST-via-OAuth** for live questions, or a **Reporting API CSV drop into a warehouse** for everything recurring, with a community Data-API MCP only if you want metadata and transcripts. That's not a workaround — given the no-service-account constraint, owning the OAuth flow yourself is the more durable setup anyway.

---

<a name="the-traps"></a>
## The traps

Most failures here are quiet: the agent returns a number that's real but not the one you meant, or a scheduled job silently never authorizes.

| You might expect | Reality | What to do |
|---|---|---|
| A service-account key runs the agent | YouTube rejects service accounts (`NoLinkedYouTubeAccount`) | Do interactive OAuth once; persist and refresh the token |
| The Data API gives watch time / retention | It stops at public counts (`viewCount`, `likeCount`, `commentCount`) | Use the Analytics or Reporting API for any performance metric |
| A creator can pull their own revenue | Channel reports expose **no** revenue; the monetary scope doesn't unlock it there | Revenue is content-owner (partner/MCN) only, via `content_owner_estimated_revenue_a1` |
| Today's revenue number is final | Current-period revenue is *estimated* and moves until month-end | Label it provisional; reconcile against finalized AdSense (≈7th–12th next month) |
| The Reporting API can give a retention curve | There is no bulk retention report type | Use the Analytics API `elapsedVideoTimeRatio`, one video per call |
| Polling `reports.query` weekly is the digest pattern | It can't give deep breakdowns at scale and burns against quota | Schedule a Reporting job; slice the CSV locally |
| A hard-coded report-type ID keeps working | Version suffixes (`_a3` → `_a4`) retire old IDs | Call `reportTypes.list` for the live set |
| The Reporting API can backfill old history | It backfills only ~30 days at job creation | Create jobs before you need the data; store the CSVs (they age out at 60 / 30 days) |
| The BigQuery DTS transfer is "free," so the warehouse is free | The transfer (orchestration + load) is no-charge; BigQuery storage and queries still bill | Apply the GA4 guide's byte cap and read-only role; the savings is the transfer, not the warehouse |
| DTS can pull years of YouTube history on setup | Backfill reaches only YouTube's 30/60-day source retention | Turn the transfer on early; it accrues history going forward |
| Retention, traffic, and demographics are Studio-only | All three are Analytics API dimensions | Only the Studio **Research / Trends** search-insights tab has no creator API |
| Yesterday's analytics are final | The most recent ~2–3 days aren't fully available | Run digests on data a few days old; mark recent days provisional |

**Anti-patterns, in one place:** authorizing an unattended agent with a service account; building a recurring digest on `reports.query` instead of a Reporting job; pointing at the Data API for performance metrics; hard-coding report-type IDs; presenting estimated current-period revenue as final; and assuming a community MCP labeled "analytics" actually reads the Analytics API.

---

## Sources & Attribution

**Primary, Google documentation — Data API v3**

- [Getting started + default 10,000-unit/day quota](https://developers.google.com/youtube/v3/getting-started) · [Quota costs by method](https://developers.google.com/youtube/v3/determine_quota_cost) · [`videos` resource (`statistics` fields)](https://developers.google.com/youtube/v3/docs/videos) · [Authentication / service accounts unsupported](https://developers.google.com/youtube/v3/guides/authentication)

**Primary, Google documentation — Analytics API**

- [`reports.query` reference](https://developers.google.com/youtube/analytics/reference/reports/query) · [Channel reports (incl. audience retention, no-revenue note)](https://developers.google.com/youtube/analytics/channel_reports) · [Content-owner reports (revenue, monetary scope)](https://developers.google.com/youtube/analytics/content_owner_reports) · [Dimensions](https://developers.google.com/youtube/analytics/dimensions) · [Metrics](https://developers.google.com/youtube/analytics/metrics) · [Data model / freshness](https://developers.google.com/youtube/analytics/data_model)

**Primary, Google documentation — Reporting API**

- [Reporting API overview (Analytics-vs-Reporting comparison, quota-non-issue)](https://developers.google.com/youtube/reporting) · [Bulk reports: lifecycle, 48h first report, 30-day backfill, 60/30-day retention](https://developers.google.com/youtube/reporting/v1/reports) · [`jobs.create` reference](https://developers.google.com/youtube/reporting/v1/reference/rest/v1/jobs/create) · [Channel report types](https://developers.google.com/youtube/reporting/v1/reports/channel_reports) · [Content-owner report types](https://developers.google.com/youtube/reporting/v1/reports/content_owner_reports) · [Authorization (OAuth required, scopes)](https://developers.google.com/youtube/reporting/guides/authorization)

**Primary, Google documentation — BigQuery Data Transfer Service**

- [YouTube Channel transfer](https://cloud.google.com/bigquery/docs/youtube-channel-transfer) · [YouTube Content Owner transfer](https://cloud.google.com/bigquery/docs/youtube-content-owner-transfer) · [Channel report transformation (table list)](https://cloud.google.com/bigquery/docs/youtube-channel-transformation) · [Content-owner transformation (revenue tables)](https://cloud.google.com/bigquery/docs/youtube-content-owner-transformation) · [BigQuery pricing (DTS free-connector list)](https://cloud.google.com/bigquery/pricing)

**Companion guide (BigQuery wiring reused here)**

- [GA4 with Claude — Data API, BigQuery, and the Multi-Source Warehouse](ga4-with-claude.md): the [read-only BigQuery service account + byte cap + dry-run](ga4-with-claude.md#wire-claude-to-bigquery-read-only) and the [multi-source warehouse](ga4-with-claude.md#path-3) apply unchanged to a YouTube dataset.

**Primary, Google documentation — Studio behavior & freshness**

- [YouTube Analytics data delays, estimated vs finalized revenue, claimed-view differences](https://support.google.com/youtube/answer/6085583) · [Studio Research / Trends tab (no creator API)](https://support.google.com/youtube/answer/11962757)

**Agent tooling**

- [Anthropic Model Context Protocol](https://modelcontextprotocol.io) · [Official MCP registry (no first-party YouTube server)](https://registry.modelcontextprotocol.io) · [Google's GA4 MCP server — GA4, not YouTube](https://github.com/googleanalytics/google-analytics-mcp) · community servers: [`ZubeidHendricks/youtube-mcp-server` (Data API only)](https://github.com/ZubeidHendricks/youtube-mcp-server), [`pauling-ai/youtube-mcp-server` (claims Analytics API; early)](https://github.com/pauling-ai/youtube-mcp-server)

**Corrections from prior circulating versions:** most "YouTube analytics + AI" writing treats YouTube as one API and tells you to poll it. That's the expensive mistake: the Analytics API and the Reporting API are different products, and recurring work belongs on the bulk Reporting CSV, not on ad-hoc `reports.query`. Two more corrections this guide makes against common claims. First, retention, traffic sources, and demographics are *not* Studio-only — they're all Analytics API dimensions; only the Research/Trends search-insights tab lacks a creator API. Second, a creator cannot pull their own revenue from the API: revenue analytics is a content-owner capability, and the monetary scope does nothing on channel reports. The no-service-account constraint is also routinely omitted from agent guides and is the top cause of silent failures in unattended setups — and the free BigQuery Data Transfer path that resolves it (authorize once, then the agent reads a warehouse) goes almost entirely unmentioned in "YouTube + AI" writing.

*Source-quality note: figures here trace to primary Google pages, but several move over time and should be re-confirmed against the live docs at use — the Data API per-method quota costs (especially `videos.insert`), the Analytics API's numeric query quota (read it from the Cloud console, not a doc), the 24h-vs-48h first-report discrepancy in Google's own pages, report-type version suffixes, and the maturity of any community MCP server named above. On the BigQuery path: the DTS "no-charge" connector classification is current as of writing but the pricing page notes a Data Transfer Service SKU relabel landing 2026-08-11, so re-check the free-connector list if publishing after that; and "runs unattended after one-time auth" is the documented recurring-transfer behavior, not a verbatim "never re-auth" guarantee — a revoked OAuth grant breaks runs. Non-core metrics and dimensions (including the retention metrics) are not covered by Google's deprecation policy and can change without notice.*

---

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. Underlying API and product behavior is the property of Google and documented in the sources above. Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
