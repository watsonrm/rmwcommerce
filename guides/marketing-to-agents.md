---
title: Marketing to Agents
description: The authoritative playbook for making any website readable, citable, and operable across every class of AI agent — indexer bots, AI search surfaces, chat assistants, and agentic browsers. Every claim sourced. 22-item checklist impact-ordered by evidence weight.
date: 2026-05-21
last_modified_at: 2026-05-24
author: Rick Watson
agent_friendly: true
keywords: AI agents, AI search, LLM citation, robots.txt, llms.txt, AGENTS.md, MCP, JSON-LD, agentic browsers, generative engine optimization, GEO
---

# Marketing to Agents

**The authoritative playbook for making any website readable, citable, and operable across every class of AI agent: indexer bots, AI search surfaces, chat assistants, and agentic browsers. Every claim sourced. 22-item checklist impact-ordered by evidence weight.**

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from vendor primary documentation, peer-reviewed research, and large-N industry studies. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

**Published:** <time datetime="2026-05-21">2026-05-21</time>  ·  **Last updated:** <time datetime="2026-05-24">2026-05-24</time>  ·  **Author:** [Rick Watson](https://www.rmwcommerce.com/), Principal, RMW Commerce Consulting  ·  **Canonical URL:** [`github.com/watsonrm/rmwcommerce/blob/main/guides/marketing-to-agents.md`](https://github.com/watsonrm/rmwcommerce/blob/main/guides/marketing-to-agents.md)

### Machine-readable identity (this article practices what it preaches)

The JSON-LD any agent-friendly hosting layer should serve for this article. Drop it into the `<head>` of an HTML render; it satisfies Tier 1 #2 of the [22-item priority checklist](#the-22-item-priority-checklist) below.

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Marketing to Agents",
  "description": "The authoritative playbook for making any website readable, citable, and operable across every class of AI agent: indexer bots, AI search surfaces, chat assistants, and agentic browsers.",
  "datePublished": "2026-05-21T09:00:00-04:00",
  "dateModified": "2026-05-24T09:00:00-04:00",
  "inLanguage": "en",
  "url": "https://github.com/watsonrm/rmwcommerce/blob/main/guides/marketing-to-agents.md",
  "mainEntityOfPage": "https://github.com/watsonrm/rmwcommerce/blob/main/guides/marketing-to-agents.md",
  "author": {
    "@type": "Person",
    "name": "Rick Watson",
    "url": "https://www.rmwcommerce.com/",
    "jobTitle": "Principal, RMW Commerce Consulting",
    "sameAs": [
      "https://www.linkedin.com/in/rickmwatson/",
      "https://x.com/RMW_Commerce",
      "https://github.com/watsonrm",
      "https://watsonweekly.com/"
    ]
  },
  "publisher": {
    "@type": "Organization",
    "name": "RMW Commerce Consulting",
    "url": "https://www.rmwcommerce.com/",
    "logo": {
      "@type": "ImageObject",
      "url": "https://images.squarespace-cdn.com/content/v1/5e924549c2923c644b9de05f/7e088230-031b-46d3-ad75-366f63a3d443/favicon.ico?format=100w"
    }
  },
  "license": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
  "copyrightHolder": {
    "@type": "Person",
    "name": "Rick Watson"
  },
  "copyrightYear": 2026,
  "keywords": "AI agents, AI search, LLM citation, robots.txt, llms.txt, AGENTS.md, MCP, JSON-LD, agentic browsers, generative engine optimization, GEO"
}
```

---

## TL;DR — what's in it for you

- Understand which of four agent classes is visiting your site, what each rewards, and how to avoid blocking the ones your customers use.
- Know exactly which structural signals drive citation in ChatGPT, Google AI Overviews, Perplexity, Claude, Grok, and Microsoft Copilot — ranked by evidence weight, not guesswork.
- Get a complete, tested `robots.txt` template that separates training opt-outs from search allowlists from user-triggered fetchers.
- Make your site navigable by agentic browsers and legible to coding agents reading your docs — the newest class, and the most underspecified.

### The foundational move — before any checklist

Earn citations from authoritative third-party domains and a Wikipedia/Wikidata entity if you're eligible. Brands in the top 25% of web mentions earn 10× more AI citations than the next quartile ([Semrush AI visibility data](https://www.semrush.com/blog/most-cited-domains-ai/)). This is multi-year work — press relations, conference talks, earned media, original research, open-source contributions — and no on-your-site checklist item replaces it. Section [The known-entity flywheel](#the-known-entity-flywheel) covers what "earn citations" actually means in practice.

Everything in the rest of this guide is what you do *on your own site* to convert that earned authority into citations. The site work is necessary. It is not sufficient.

### Where to spend your time, in priority order

The top seven on-your-site moves, ordered by evidence weight. Each maps to an item in [the 22-item priority checklist](#the-22-item-priority-checklist) at the end of the guide.

| Rank | Practice | Why it matters | Effort | Checklist item |
|---|---|---|---|---|
| 1 | Serve content as server-rendered HTML — headline, body, dates visible in the raw response before JS runs | Most AI crawlers (GPTBot, ClaudeBot, CCBot, PerplexityBot) do not execute JavaScript. Content hidden behind hydration is invisible to ~80% of AI crawlers ([Google JS SEO docs](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)) | Medium | Tier 1 #1 |
| 2 | Publish `Article` / `Organization` / `Person` JSON-LD with `datePublished`, `dateModified`, `author`, `publisher`, and `sameAs` arrays to Wikipedia / Wikidata / ORCID / official profiles | ~71% of ChatGPT-cited pages and ~65% of Google AI Mode-cited pages carry structured data ([SEranking dataset via PPC.land](https://ppc.land/23-factors-that-actually-get-your-content-cited-by-ai-search-engines/)). The cheapest signal that lifts citation rate across every surface | Low | Tier 1 #2 |
| 3 | Write a deliberate `robots.txt` that separates training crawlers from search/answer crawlers from user-triggered fetchers | Blanket `Disallow: /` blocks ChatGPT-User, Claude-User, and Perplexity-User — meaning a user who explicitly asks the LLM to read your page is refused. The single most common self-inflicted wound in 2026 ([OpenAI bot docs](https://developers.openai.com/api/docs/bots)) | Low | Tier 1 #4 |
| 4 | Publish `sitemap.xml` with truthful `<lastmod>` and reference it from `robots.txt` | `<lastmod>` is the only freshness signal Google and Bing publicly use; `<changefreq>` and `<priority>` are ignored ([sitemaps.org](https://www.sitemaps.org/protocol.html)). Perplexity's Sonar resets freshness on minor edits | Low | Tier 1 #5 |
| 5 | Front-load the answer in the first 30% of the page in a 40–75 word paragraph | 44% of citations come from the first third of a page; 75% from the first two-thirds ([ALM Corp content-placement study](https://almcorp.com/blog/chatgpt-citations-study-44-percent-first-third-content/)) | Low | Tier 2 #6 |
| 6 | Pass WCAG 2.2 AA — semantic HTML5, ARIA labels on every interactive element, alt text on every meaningful image | OpenAI Operator, Anthropic Computer Use, and Google Project Mariner navigate via the accessibility tree — the same data structure built for screen readers | Medium | Tier 2 #12 |
| 7 | Subscribe to Bing Webmaster Tools — AI Performance | The only major surface that gives publishers per-query AI citation data. Google Search Console does not break out AI Overview clicks ([Bing Webmaster blog](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview)) | Low | Tier 4 #22 |

Most readers should complete Tier 1 of [the 22-item priority checklist](#the-22-item-priority-checklist) and the foundational move above, then stop. Everything else is amplification.

---

## How to use this

The operational form of this guide is the Claude Code skill at [`skills/marketing-to-agents/`](../skills/marketing-to-agents/). Install it once:

```bash
# from a clone of this repo
cp -r skills/marketing-to-agents ~/.claude/skills/
```

Then describe your site to Claude — tech stack, site URL, whether you publish editorial content or developer docs — and say one of these:

> "audit my site for agent-friendliness"
> "run the marketing-to-agents checklist on my site"
> "how well does my site work for AI agents"

Claude will load the skill on demand, work through the 22-item checklist against your actual setup, and deliver a gap report with customized `robots.txt` and JSON-LD snippets. The article below is the reasoning behind the checklist — read it for the *why*; the skill is the *how*.

---

## Why this matters now

Search engines were one kind of automated reader. Sites optimized for them by ranking in result lists humans clicked. The 2025–2026 transition is not a search-engine update — it is a change in the composition of the audience that reads your site at all.

Cloudflare's May 2025 telemetry on AI crawler traffic captured the shift in one stat: AI bot requests are ~80% training-oriented and ~20% referral-driving, with crawl-to-click ratios that look nothing like Googlebot's ([Cloudflare on the crawl-to-click gap](https://blog.cloudflare.com/crawlers-click-ai-bots-training/)):

| Operator | Crawls per referral (July 2025) |
|---|---|
| Anthropic | 38,065.7 |
| OpenAI | 1,091.4 |
| Perplexity | 194.8 |
| Google | 5.4 |

The implication is not that AI crawling is parasitic — it is that the relationship between being read and being clicked has decoupled. A site can be cited millions of times inside ChatGPT, Claude, and Perplexity answers without ever appearing in a referral log. Influence is now an output of citation in the answer, not just a click on a SERP.

That is the audience this guide is written for. The rest explains, layer by layer, what each class of agent rewards, what they punish, and what you can do that matters.

---

## The four classes of agent

Every move in this guide maps to one or more of four classes. Hold this taxonomy in your head as you read; the rest of the document repeatedly references it.

1. **Indexer bots** — automated crawlers that fetch your pages for someone else to read later. Three sub-types: training crawlers (GPTBot, ClaudeBot, Google-Extended, CCBot, etc.), search-index crawlers (OAI-SearchBot, PerplexityBot, Claude-SearchBot), and user-triggered fetchers (ChatGPT-User, Claude-User, Perplexity-User).
2. **AI search surfaces** — grounded retrieval products that show citations alongside generative answers. Google AI Overviews and AI Mode, Microsoft Copilot Search, Perplexity, OpenAI's ChatGPT Search / SearchGPT, Apple Intelligence / Siri.
3. **Chat assistants** — conversational LLMs with optional browsing or search. ChatGPT, Claude, Perplexity, Google Gemini, Microsoft Copilot, xAI Grok, Mistral Le Chat, You.com, DeepSeek.
4. **Agentic systems** — agents that act on your site (browse, click, fill, transact) or build against your docs (coding agents reading your reference and generating code that calls your APIs). Operator, Anthropic Computer Use, Browser Use, Perplexity Comet, Claude Code, Cursor, Cline, Aider, Windsurf, Devin, OpenAI Codex, GitHub Copilot Agent.

The first three classes overlap heavily — the same bots feed the same indexes that ground the same answers. The fourth class is structurally different: agentic systems need machine-readable structured surfaces (accessibility trees, `AGENTS.md`, `llms.txt`, MCP servers), not just well-written prose.

---

## Part 1 — Who's actually crawling you

Bot traffic in 2026 is dominated by a knowable, finite set of operators. Each major AI vendor runs three crawlers, not one, and the most common publisher mistake is treating them as a single thing.

### The three-class taxonomy

Adopting the taxonomy used by OpenAI, Anthropic, and Mistral in their own bot documentation:

1. **Training crawlers** systematically fetch pages to feed model pre-training corpora. Block these if you want to opt out of being part of foundation-model training data.
2. **Search-index crawlers** build the real-time retrieval index used by an AI search product. Block these and you delist from that product's answer surface — the AI-search equivalent of blocking Googlebot.
3. **User-triggered fetchers** fetch a single URL because a human inside a chat product asked the model to read it. Most vendors say their user-fetcher honors `robots.txt`; some (Perplexity-User, Meta-ExternalFetcher) openly do not.

The publisher decision is independent for each. Most sites should disallow some training crawlers (your business decision) while always allowing search-index crawlers and user-triggered fetchers (your customers are asking the LLM to look at you).

### The bot zoo — verified user agents and links

**OpenAI** ([developers.openai.com/api/docs/bots](https://developers.openai.com/api/docs/bots)):

- `GPTBot` — training. UA: `Mozilla/5.0 ... GPTBot/1.3; +https://openai.com/gptbot`. IPs at `openai.com/gptbot.json`. Honors `robots.txt`.
- `OAI-SearchBot` — ChatGPT Search index. IPs at `openai.com/searchbot.json`. Honors `robots.txt`. Blocking this delists you from ChatGPT Search citations.
- `ChatGPT-User` — user-initiated fetch. IPs at `openai.com/chatgpt-user.json`. OpenAI's stated posture per the December 2025 docs revision: `robots.txt` rules may not apply to user-initiated actions ([PPC.land summary of the revision](https://ppc.land/openai-revises-chatgpt-crawler-documentation-with-significant-policy-changes/)).

**Anthropic** ([support.claude.com/en/articles/8896518](https://support.claude.com/en/articles/8896518)):

- `ClaudeBot` — training. Honors `robots.txt`, supports `Crawl-delay:`.
- `Claude-User` — user-initiated fetch from inside Claude. Honors `robots.txt` (unusual posture for a user fetcher; aligns with OpenAI's ChatGPT-User stance).
- `Claude-SearchBot` — index for Claude's web search. Honors `robots.txt`.
- IPs at [`claude.com/crawling/bots.json`](https://claude.com/crawling/bots.json).
- Legacy strings `anthropic-ai` and `claude-web` appear in older trackers; include them in `robots.txt` for backwards coverage.

**Google** ([developers.google.com/search/docs/crawling-indexing/google-common-crawlers](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers)):

- `Googlebot` — Search, Discover, Images, Video, News. Honors `robots.txt`. Blocking Googlebot delists from Search and from AI Overviews.
- `Google-Extended` — robots.txt-only token applied to Googlebot's existing fetches. Controls "whether content Google crawls from their sites may be used for training future generations of Gemini models that power Gemini Apps and Vertex AI" ([Search Engine Land coverage](https://searchengineland.com/google-extended-crawler-432636)). Does not affect Search ranking or indexation, and does not opt content out of AI Overview citations ([Nieman Lab, May 2025](https://www.niemanlab.org/2025/05/google-is-using-content-from-publishers-who-opt-out-of-other-ai-training-to-power-ai-overviews/)).
- `GoogleOther`, `GoogleOther-Image`, `GoogleOther-Video` — generic R&D crawlers freeing Googlebot capacity for Search.
- `Google-CloudVertexBot` — crawls customer-specified sites for Vertex AI Search.
- `Google-Safety` — the only Google crawler that explicitly ignores robots.txt, used for malware discovery on publicly-posted links.

**Perplexity** ([docs.perplexity.ai/guides/bots](https://docs.perplexity.ai/guides/bots)):

- `PerplexityBot` — index for Perplexity answers. IPs at `perplexity.com/perplexitybot.json`. Honors `robots.txt` per Perplexity's docs.
- `Perplexity-User` — user-initiated fetch. IPs at `perplexity.com/perplexity-user.json`. Perplexity's own docs concede this "generally ignores `robots.txt` rules" because fetches are user-initiated.
- **Documented stealth crawling** — Cloudflare's August 2025 investigation [Perplexity is using stealth, undeclared crawlers to evade website no-crawl directives](https://blog.cloudflare.com/perplexity-is-using-stealth-undeclared-crawlers-to-evade-website-no-crawl-directives/) documented Perplexity returning answers about brand-new domains whose `robots.txt` blocked all crawlers, generating 3–6M daily requests from IPs outside Perplexity's published JSON range using a rotated `Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)` user-agent across ASN switches. Cloudflare delisted Perplexity from "verified bots" in response. Wired's June 2024 investigation reached similar conclusions for Wired's and Forbes's content.

**Apple** ([support.apple.com/en-us/119829](https://support.apple.com/en-us/119829)):

- `Applebot` — Siri, Spotlight, Safari search. Honors `robots.txt`. If no Applebot rules are set, Applebot follows Googlebot rules — an unusual fallback.
- `Applebot-Extended` — `robots.txt`-only token controlling whether Applebot-crawled content is used to train Apple foundation models. Does not affect Search.

**Meta** ([developers.facebook.com/docs/sharing/webmasters/web-crawlers](https://developers.facebook.com/docs/sharing/webmasters/web-crawlers)):

- `Meta-ExternalAgent` — training crawler. Honors `robots.txt`.
- `Meta-ExternalFetcher` — user-initiated; Meta's docs say it "may bypass `robots.txt` rules".
- `facebookexternalhit` — link unfurler. Notoriously ignores `User-agent: *` wildcards; must be named explicitly.
- `Meta-WebIndexer` — Meta AI search index.

**ByteDance — Bytespider**:

- Officially claims to respect `robots.txt`. Multiple independent analyses (DataDome, Cloudflare, the [ai.robots.txt community list](https://github.com/ai-robots-txt/ai.robots.txt/blob/main/table-of-bot-metrics.md)) classify Bytespider as non-compliant. Recommended posture: block at the WAF / CDN layer, not just `robots.txt`.

**Common Crawl — CCBot** ([commoncrawl.org/ccbot](https://commoncrawl.org/ccbot)):

- The Common Crawl Foundation is a nonprofit, not an AI vendor. But at least 64% of LLMs released between 2019 and October 2023 used some filtered version of Common Crawl during pre-training — for GPT-3 specifically, Common Crawl contributed ~60% of the weighted pre-training mix ([Mozilla Foundation analysis](https://www.mozillafoundation.org/en/research/library/generative-ai-training-data/common-crawl/)).
- Blocking CCBot is the single most leveraged training opt-out available because it cascades through every downstream model that builds on Common Crawl corpora.
- Honors `robots.txt`, publishes verifiable IP ranges, verifies via reverse DNS to `*.crawl.commoncrawl.org`.

**Others worth knowing**:

- `Amazonbot` — Alexa, Nova, Bedrock-adjacent training pipelines. Honors `robots.txt`, also respects `nofollow`/`noindex`/`noarchive`. Caches `robots.txt` up to 30 days ([Amazon developer docs](https://developer.amazon.com/amazonbot)).
- `DuckAssistBot` — DuckDuckGo AI answers. Honors `robots.txt`. Not used for training ([DuckDuckGo help](https://duckduckgo.com/duckduckgo-help-pages/results/duckassistbot)).
- `YouBot` — You.com index ([docs.you.com/youbot](https://docs.you.com/youbot)).
- `MistralAI-User` / `MistralAI-Index` — Le Chat fetcher and index. Honors `robots.txt`. Index crawler content is not used for training ([docs.mistral.ai/robots](https://docs.mistral.ai/robots)).
- `Diffbot` — knowledge-graph extraction; sells the resulting structured corpus to many AI products. Honors `robots.txt` ([Diffbot docs](https://docs.diffbot.com/docs/does-crawl-respect-robotstxt)).

### Cloudflare's May 2025 AI-crawler share

From [Cloudflare's "From Googlebot to GPTBot"](https://blog.cloudflare.com/from-googlebot-to-gptbot-whos-crawling-your-site-in-2025/):

| Rank | Bot | Share of all crawler traffic | YoY change |
|---|---|---|---|
| 1 | Googlebot | 50% | +96% |
| 2 | Bingbot | 8.7% | +2% |
| 3 | GPTBot | 7.7% | +305% |
| 4 | ClaudeBot | 5.4% | −46% |

Within AI-only traffic: GPTBot 30%, ClaudeBot 21%, Meta-ExternalAgent 19%, Amazonbot 11%, Bytespider 7.2%. PerplexityBot requests grew 157,490% year-over-year; ChatGPT-User grew 2,825%. As of mid-2025, approximately 14% of the top 10,000 domains carry AI-specific directives in `robots.txt`, with GPTBot both the most-blocked (312 domains) and most-explicitly-allowed (61 domains).

### A working `robots.txt` template

The pattern below separates training from search from user-fetch correctly. Adjust the training section to your business policy.

```
# Default: allow everything
User-agent: *
Allow: /

# Training crawlers — opt out of being part of foundation-model training
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: Bytespider
User-agent: Meta-ExternalAgent
User-agent: CCBot
Disallow: /
# (To allow training, remove the bot from this block. Don't change Disallow to Allow
# inside it — under RFC 9309 longest-match-wins, the most specific UA block governs,
# so removing the entry is the clean way to fall back to the wildcard Allow above.)

# Search-index crawlers — always allow if you want to be cited
User-agent: OAI-SearchBot
User-agent: Claude-SearchBot
User-agent: PerplexityBot
User-agent: Googlebot
User-agent: Bingbot
User-agent: Applebot
User-agent: YouBot
User-agent: MistralAI-Index
Allow: /

# User-initiated fetchers — these are humans on the other end. Always allow.
User-agent: ChatGPT-User
User-agent: Claude-User
User-agent: Perplexity-User
User-agent: MistralAI-User
User-agent: DuckAssistBot
Allow: /

Sitemap: https://example.com/sitemap.xml
```

For Bytespider specifically, layer a WAF block on top of the `robots.txt` entry — historical compliance is unreliable. Cloudflare's managed-rules ruleset, Fastly's bot management, and AWS WAF all ship pre-built rulesets for AI bots.

---

## Part 2 — Being cited in AI search

The grounded-retrieval surfaces — Google AI Overviews, Microsoft Copilot Search in Bing, Perplexity, ChatGPT Search / SearchGPT, Apple Intelligence — are different from chat assistants in three ways: they live next to or inside traditional search engines, they cite heavily, and they inherit classical ranking signals from their parent indexes.

### Google AI Overviews and AI Mode

Google announced AI Overviews at I/O 2024 ([Sundar Pichai keynote, May 14 2024](https://blog.google/inside-google/message-ceo/google-io-2024-keynote-sundar-pichai/)) as the production-grade successor to the Search Generative Experience labs experiment. AI Mode — a separate, more agentic surface that decomposes a question into many parallel sub-queries — followed at I/O 2025.

Google's stated stance on what gets cited is straightforward (from [developers.google.com/search/docs/appearance/ai-features](https://developers.google.com/search/docs/appearance/ai-features)):

> "There are no additional requirements to appear in AI Overviews or AI Mode, nor other special optimizations necessary."
> "AI is built into Search and integral to how Search functions."

The controls are the standard Search controls: `noindex`, `nosnippet`, `data-nosnippet` for sections, `max-snippet:[number]`, and `robots.txt` for Googlebot. There is no AI-specific opt-out for AI Overviews. Blocking AI Overviews means blocking yourself from Google Search.

The data partially contradicts the official line. Ahrefs' 2026 follow-up study of 863,000 keywords found that only 38% of AI Overview citations rank in Google's top 10 organically for the same query — down from 76% in [Ahrefs' July 2025 baseline](https://ahrefs.com/blog/search-rankings-ai-citations/) ([2026 update](https://ahrefs.com/blog/ai-overview-citations-top-10/); [ALM Corp summary](https://almcorp.com/blog/google-ai-overview-citations-drop-top-ranking-pages-2026/)). 26.2% rank 11–100 organically; 36.7% rank outside the top 100 entirely. AI Overview eligibility is increasingly orthogonal to organic ranking.

Source patterns inside AI Overviews, from multiple independent studies:

- Wikipedia dominates raw mentions — roughly 11% of AI Overview citations in one large sample.
- Reddit holds approximately 21% of AIO citations specifically; the top user-generated source even after YouTube overtook Reddit across all LLM answers in early 2026 ([Adweek on the Peec AI 30M-source study](https://www.adweek.com/media/youtube-just-overtook-reddit-on-llm-citations/)).
- YouTube has roughly a 200x advantage over any competing video source inside AIOs; transcripts function as citable text.
- Fandom.com leads in Google AI Mode specifically.
- News (Forbes, Gartner, major newspapers) and `.gov` / `.edu` sources are over-represented for YMYL (your-money-your-life) queries.
- The top 15 domains capture ~68% of citations — a concentration higher than classical PageRank-era SERPs ([ALM Corp top-domains analysis](https://almcorp.com/blog/top-domains-cited-by-ai-search/)).

The information gain patent, US Patent 12013887B2 ([Search Engine Journal coverage](https://www.searchenginejournal.com/googles-information-gain-patent-for-ranking-web-pages/524464/)), was granted to Google in June 2024 and uses the term *automated assistant* 69 times versus *search engine* 25 times. The patent describes a scoring mechanism that ranks documents by "additional information that is included in the document beyond information contained in documents that were previously viewed" — session-relative novelty, not global novelty. It is the closest thing to a Google-confirmed AI-search-specific ranking signal. Practical implication: original data, expert commentary, frameworks, and case studies — content that says something not already in the model's training set — are disproportionately good follow-up candidates inside AI surfaces.

### Microsoft Copilot and Bing

Microsoft now operates two grounded-AI surfaces atop the Bing index: Copilot Search in Bing (launched April 2025, [blogs.bing.com](https://blogs.bing.com/search/April-2025/Introducing-Copilot-Search-in-Bing)) and the chat product at `copilot.microsoft.com`.

The most concrete publisher-facing development in the entire AI-search space is **Bing Webmaster Tools — AI Performance**, launched as a public preview in February 2026 ([Bing Webmaster blog](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview)). Five metrics for any verified site:

1. Total Citations across Copilot, Bing AI answers, and partner integrations
2. Average Cited Pages (daily unique URLs cited)
3. Grounding Queries — the actual phrases AI used to retrieve the content
4. Page-level Citation Activity
5. Visibility Trends over time

This is the only major AI surface that gives publishers query-level retrieval data as of May 2026. Google Search Console does not break out AI Overview clicks; Anthropic, OpenAI, and Perplexity offer nothing equivalent. For any site serious about measuring AI-search outcomes, Bing Webmaster Tools is the ground-truth dataset.

Microsoft's verbatim publisher guidance from the launch post:

- **Strengthen expertise** — "Deepening coverage in related areas can reinforce authority."
- **Improve structure** — "Clear headings, tables, and FAQ sections help surface key information and make content easier for AI systems to reference accurately."
- **Support claims** — "Examples, data, and cited sources help build trust when content is reused in AI-generated answers."
- **Keep current** — "Regular updates help ensure AI systems reference the most current version of your content."
- **Reduce ambiguity** — "Align text, images, and video so they consistently represent the same entities, products, or concepts."

Microsoft additionally recommends IndexNow ([indexnow.org](https://indexnow.org)) for freshness signaling — the open protocol Bing and Yandex co-developed for instant change notifications. Free, low-effort, supported by Bing, Yandex, Naver, Seznam, and other indexes that some AI surfaces ground on.

### Perplexity

Perplexity is the most citation-native consumer answer engine and the only major surface with a revenue-share program for publishers. The Comet Plus model, expanded August 2025 ([Digiday on Perplexity's revenue model](https://digiday.com/media/how-perplexity-new-revenue-model-works-according-to-its-head-of-publisher-partnerships/)):

- 80/20 split — publishers receive 80% of the pooled subscription revenue, Perplexity keeps 20%.
- $42.5M payout pool committed in 2025.
- Revenue is allocated across direct visits, citations in answers, and Comet-agent task completions.
- Launch partners: Time, Fortune, Der Spiegel, Entrepreneur, The Texas Tribune, WordPress.com, Gannett, The Independent, Blavity, with 15+ partners added since launch.

Among consumer chat surfaces, Perplexity has the highest URL overlap with Google rankings — 28.6% of Perplexity citations also appear in Google's top 10 for the same query ([Ahrefs 15K-query overlap study, July 2025](https://ahrefs.com/blog/ai-search-overlap/)). That's roughly 4x ChatGPT's overlap and 4–5x Gemini's. Perplexity behaves the most like a traditional search engine, which means classical SEO is unusually load-bearing for Perplexity citation share.

Perplexity also disproportionately cites:

- Reddit — 6.6% of all Perplexity citations across the Profound 680M-citation dataset, more than 3.5x Reddit's share on ChatGPT ([Profound, summarized at ALM Corp](https://almcorp.com/blog/top-domains-cited-by-ai-search/)).
- PDFs — Sonar's crawl-and-embed pipeline appears to favor cleanly structured PDFs over noisy HTML in multiple independent audits.
- FAQ-schema-tagged content — independent testing reports FAQ JSON-LD measurably increases Perplexity citation rates ([ziptie.dev on FAQ schema for AI](https://ziptie.dev/blog/faq-schema-for-ai-answers/)). Sonar often uses the FAQ question as anchor text.

### OpenAI's ChatGPT Search / SearchGPT

OpenAI announced SearchGPT in July 2024 ([openai.com/searchgpt](https://openai.com/searchgpt)) and folded it into ChatGPT as ChatGPT Search in October 2024. It is now available to all ChatGPT users including logged-out web visitors.

The publisher-control model is the cleanest in the industry — three crawlers, three independent `robots.txt` controls (the full table is in Part 1). The standard 2026 posture is disallow GPTBot, allow OAI-SearchBot, allow ChatGPT-User — opt out of training, opt into traffic.

ChatGPT also adds `utm_source=chatgpt.com` to outbound referral links automatically, which makes analytics measurement trivial. Among major AI surfaces, only ChatGPT and Bing make this measurable today.

### Apple Intelligence and Siri

Apple's grounded-AI footprint is smaller than Google's or Microsoft's but increasing because of distribution. Surfaces include Siri (with optional ChatGPT handoff via the Apple/OpenAI integration in iOS 18+), Apple Intelligence Writing Tools, Spotlight, and Safari summaries.

`Applebot` (search) and `Applebot-Extended` (training opt-out) are documented at [support.apple.com/en-us/119829](https://support.apple.com/en-us/119829). The unusual property: if no Applebot-specific rules are set in `robots.txt`, Applebot follows Googlebot rules. Default Google-friendly configurations work for Apple by inheritance.

When Siri hands off to ChatGPT, grounding comes from OpenAI's surface — so the OAI-SearchBot controls apply. Practical posture for most sites: allow both Applebot and Applebot-Extended unless there's a specific reason to opt out of Apple training. The cost of opting out is zero in Search visibility.

### The known-entity flywheel

The single most durable AI-citation signal is being a known entity in the open web's knowledge graph. It is the foundational move flagged at the top of this guide. This section is what "earn citations" actually means.

**The path is the same regardless of vendor:**

1. Earn third-party citations from authoritative outlets (press, `.edu`, `.gov`, trade publications, conference proceedings).
2. A Wikipedia article becomes possible once the entity meets Wikipedia's notability threshold (cited by reliable secondary sources, not self-published).
3. A Wikidata entry follows. Wikidata's bar is lower than Wikipedia's but still requires verifiable references.
4. The site adds `Organization` and `Person` schema with `sameAs` linking to those Wikidata + Wikipedia URLs.

The knowledge-graph layer is what lets a grounded-AI surface confidently say "X is a Y who does Z" and attach a citation. Wikidata's Q-IDs power entity disambiguation across Google Knowledge Graph, Bing, Apple, Perplexity, and Gemini. Eighteen to thirty-six months is a realistic timeline. There is no shortcut.

**What actually earns citations**, ranked by leverage:

1. **Original research.** Publish data nobody else has — a survey, a benchmark, a primary-research teardown, a longitudinal tracker. Original data is the single highest-yield citation magnet because every secondary write-up cites the source. The 1.4M-prompt Ahrefs study, the 13-week Semrush study, the Cloudflare bot telemetry posts are cited dozens of times in industry analysis, including in this guide. That citation tail compounds.

2. **Earned press.** Bylines or quotes in outlets the knowledge graph already trusts — Reuters, Bloomberg, Forbes, Wired, your trade's flagship publication, major newspapers, Wikipedia-eligible academic press. One Reuters mention beats fifty SEO blog placements.

3. **Conference talks at named events.** Speaking slots at events with their own Wikipedia entries (NRF, RSA, SIGGRAPH, AWS re:Invent, ICML, ICLR, etc.) leave durable third-party traces — programs, recordings, abstracts. The conference's own page is a citation. The recording on YouTube is a citation. The press write-up of the talk is a citation.

4. **Open-source contributions** with named authorship. A merged PR to a high-star repo, a contributed example to a vendor cookbook, a published library — each lives at a permanent URL with your name attached. Especially load-bearing for technical entities Wikidata can't otherwise verify.

5. **Wikipedia notability gates** are stricter than most operators realize. The bar is "significant coverage in reliable secondary sources independent of the subject." Press releases do not count. Sponsored content does not count. The company's own blog does not count. Two or three independent feature-length articles in qualifying outlets is the minimum realistic bar; for individuals, expect five or more.

6. **Wikidata is the cheaper, faster step.** Wikidata accepts entries with any verifiable reference and is the entity layer Google Knowledge Graph, Apple, and Perplexity disambiguate against. If a Wikipedia article is two years away, a Wikidata Q-ID is achievable in months. Create one and bind your site's `Organization`/`Person` schema to it via `sameAs`.

7. **The sameAs array is hygiene, not magic.** Point at high-authority external references that already exist: Wikidata, Wikipedia, Crunchbase, ORCID, GitHub, the official LinkedIn URL. Pointing at your own Twitter and Facebook pages adds nothing. Pointing at a Wikipedia article you own *yourself* is a flag, not a signal.

**What does not work:** sponsored content, press-release-grade brand mentions on the long tail of SEO-content farms, paid placements that no editorial outlet actually fact-checked, bought reviews, AI-generated commentary citing your name back at you, link-network schemes. AI surfaces increasingly weight citation source by the same authority graph Google's quality raters do. Cheap mentions degrade your score; they don't raise it.

**The compounding measurement.** Brand-mention monitoring tools (Ahrefs Brand Radar, Semrush Brand24, Profound, Peec AI) track third-party mentions across the web. The metric to watch is unique-authoritative-domain count over time. A site that grows from 20 mentions in 5 outlets to 200 mentions in 60 outlets in 18 months is on the flywheel. A site stuck on the same 5 outlets is not.

---

## Part 3 — Being cited in chat assistants

The chat layer overlaps with AI search but has its own dynamics. The volume of empirical research on consumer chat citation behavior expanded dramatically in 2025–2026, and the patterns are consistent enough across studies to write down with confidence.

### ChatGPT

The largest published citation-behavior study to date: Ahrefs' 1.4M-prompt analysis of ChatGPT (February 2025) at [ahrefs.com/blog/why-chatgpt-cites-pages](https://ahrefs.com/blog/why-chatgpt-cites-pages). Headline findings:

- ChatGPT retrieves ~33 URLs per prompt and cites roughly half (49.98% cite rate).
- 88% of cited URLs come from the general "search" retrieval channel. The other channels are far less likely to surface citations: News 12.0%, Reddit 1.93%, YouTube 0.51%, Academia 0.40%.
- ChatGPT pulls Reddit constantly to understand a topic but almost never cites it — 67.8% of non-cited URLs in the dataset were from Reddit.
- Pages at Google position 1 were cited 3.5x more often than pages outside Google's top 20. Google ranking remains the strongest single retrieval signal.
- Cited evergreen content had a median age of ~500 days; cited news had a median age of ~200 days versus ~300 days for non-cited news. Freshness matters when intent is news.
- Cosine similarity between prompt and cited page title averaged 0.602 versus 0.484 for non-cited. Title-query semantic match is the strongest within-retrieval-set predictor of citation.
- Natural-language URLs cited 89.78% of the time versus 81.11% for opaque URL slugs.

Semrush's 13-week tracking study (July 14–October 12, 2025; >230,000 prompts; 100M+ citations across ChatGPT, Google AI Mode, and Perplexity, at [semrush.com/blog/most-cited-domains-ai](https://www.semrush.com/blog/most-cited-domains-ai/)) documented a sharp inflection: ChatGPT cited Reddit ~60% of the time pre-mid-September 2025, then collapsed to ~10% by mid-September. Wikipedia fell from ~55% to under 20% in the same window. Forbes doubled its ChatGPT citation share in the post-September window. The most credible interpretation is an OpenAI tuning change that reweighted Reddit and Wikipedia downward in favor of editorial publishers.

Profound's 680M-citation dataset (August 2024 – June 2025) cited at [ALM Corp's top-domains summary](https://almcorp.com/blog/top-domains-cited-by-ai-search/) found Wikipedia at 7.8% of all ChatGPT citations, with the top-10 ChatGPT sources concentrated on Wikipedia (47.9% of that bucket), Reddit, Forbes, G2, TechRadar, NerdWallet, Business Insider, NY Post, Reuters.

Ahrefs' "most-cited pages" follow-up ([ahrefs.com/blog/chatgpts-most-cited-pages](https://ahrefs.com/blog/chatgpts-most-cited-pages/)) found 67% of ChatGPT's top 1,000 most-cited pages were on platforms not open to traditional marketing — Wikipedia, Reddit, government / NIH, Amazon, YouTube.

ALM Corp's content-placement study ([almcorp.com](https://almcorp.com/blog/chatgpt-citations-study-44-percent-first-third-content/)) found 44% of ChatGPT citations are sourced from the first 30% of a webpage, with 31% from the 30–70% middle. Combined, three-quarters from the first two-thirds. Front-loading the answer in a 40–75 word paragraph immediately after the lede is the most testable structural intervention.

### Claude

Anthropic ships a first-party `web_search` tool on the Claude API ([platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool)). The current tool version `web_search_20260209` supports dynamic filtering via the code execution tool. Claude.ai consumers can use web search interactively.

Two structural features matter for publishers:

1. Citations are always on and cannot be turned off, and Anthropic's docs explicitly require: "when displaying API outputs directly to end users, citations must be included to the original source".
2. The `cited_text`, `title`, and `url` fields do not count against token usage. Anthropic is structurally incentivizing developers to surface citations because the source attribution is free in tokens.

Pricing: $10 per 1,000 searches on top of standard token costs. Developers can constrain with `allowed_domains` / `blocked_domains` — meaning any Claude app can hard-allowlist or hard-blocklist publishers, a different dynamic from consumer Claude.ai where Anthropic controls the search surface.

Large-N research on Claude citation behavior is thinner than for ChatGPT or Perplexity. The Ahrefs July 2025 overlap study did not break Claude out; the Semrush 13-week study didn't include Claude; the Profound dataset focuses on ChatGPT, AIO, and Perplexity. This is a real research gap. What is observable: Claude with web_search heavily favors documentation, Wikipedia, and established editorial publishers in qualitative tests; `page_age` is exposed as a signal so freshness is structurally available; dynamic filtering biases toward pages whose first chunks pass the relevance check, reinforcing the front-load-the-answer pattern.

### Perplexity

Already covered from the search-product angle in Part 2. The chat-side specifics:

- Perplexity has the highest URL overlap with Google rankings of any AI assistant — 28.6% in the Ahrefs 15K-query study.
- Reddit dominance — 46.7% share within Perplexity's top-10 most-cited sources, the highest of any major assistant.
- LinkedIn under-indexes — 5.3% on Perplexity versus 14.3% on ChatGPT Search and 13.5% on Google AI Mode ([Semrush LinkedIn AI visibility study](https://www.semrush.com/blog/linkedin-ai-visibility-study/)).
- Sonar is officially recency-biased; multiple independent tests show even minor edits reset the freshness signal for ranking purposes ([Growth Marshal's Perplexity playbook](https://www.growthmarshal.io/field-notes/the-perplexity-playbook)).

### Google Gemini

Gemini's grounding tool is documented at [ai.google.dev/gemini-api/docs/google-search](https://ai.google.dev/gemini-api/docs/google-search). When grounding is on, Gemini returns `groundingChunks` (the retrieved passages) and `groundingSupports` (text-to-source bindings with character offsets) — the cleanest machine-readable citation graph of any major assistant.

Despite running on Google Search infrastructure, Gemini has the lowest Google-rank overlap of any AI assistant studied: 6% URL overlap with Google's top 10 in the Ahrefs long-tail study, 8.2% in the broader analysis. Gemini's citation choices diverge sharply from Google organic rankings.

Inclusion is governed by Google Search's normal indexing and quality systems. `Google-Extended` opts out of training only; it does not affect grounding eligibility.

### Microsoft Copilot (chat)

Copilot's overlap with Bing top 10 is 16.6% — higher than its overlap with Google, as expected. Independent audits report Copilot's citation algorithm prioritizes freshness, structural clarity, and demonstrated expertise ([Pedowitz Group on Copilot sourcing](https://www.pedowitzgroup.com/how-bing-copilot-sources-answers-aeo-for-microsoft-search)). SEranking data finds ~71% of pages cited by ChatGPT include structured data — Copilot's bias toward schema is at least as strong and is officially encouraged by Microsoft. The Bing Webmaster Tools AI Performance dashboard makes Copilot the most measurable chat surface in 2026.

### xAI Grok

Grok runs on xAI models inside X (Twitter) and at grok.com, using two server-side tools — `web_search` and `x_search` ([docs.x.ai](https://docs.x.ai/developers/tools/web-search)). The Live Search API was deprecated January 12, 2026 in favor of these tools.

Documented heavy X-bias: Grok preferences X posts, arXiv preprints, and certain creator subsets over conventional editorial sources. JSTOR, Reuters, and NYT under-index relative to X primary sources. Presence on X is the single largest driver of citation eligibility on Grok. For non-X-native publishers, the only lever is being cited by an X-active source.

### The cross-cutting pattern

Across primary docs and large-N studies, the signals correlating with citation in 2025–2026 cluster into seven groups, in descending order of evidence weight:

1. **Domain authority and brand prominence.** Wikipedia, Reddit, YouTube, established institutional and editorial domains dominate every major dataset. Brands in the top 25% of web mentions earn 10x more AI citations than the next quartile.
2. **Conventional search ranking on the backing index.** Page-1 Google ranking is cited 3.5x more than rank-20+ on ChatGPT. Perplexity 28.6% Google-top-10 overlap, Copilot 16.6% Bing-top-10 overlap. Traditional SEO is the floor, not the ceiling.
3. **Answer-first content placement.** 44% of citations from the first third; 75% from the first two-thirds. Front-load the answer.
4. **Title-query semantic match.** Cosine similarity 0.602 (cited) versus 0.484 (non-cited). Plain, descriptive, question-aligned titles outperform brand-led or clever titles. Natural-language URLs outperform opaque slugs.
5. **Recency and freshness.** ChatGPT-cited URLs average 458 days newer than the matching Google organic result. News content has dramatically tighter freshness windows than evergreen. Use IndexNow, visible dates, and accurate Last-Modified headers.
6. **Structured data and schema markup.** ~71% of ChatGPT citations and ~65% of Google AI Mode citations include structured data. FAQ JSON-LD is the highest-leverage schema for citation rate. Microsoft officially confirms schema helps Copilot.
7. **Third-party validation and distribution.** Syndicated content earns up to 325% more AI citations than single-site content. Review-rich brands moved from 1% to 75% citation rates in one tracked cohort ([PR Newswire summary](https://www.prnewswire.com/news-releases/brands-that-build-trust-through-reviews-increase-ai-citations-from-1-to-75-earn-competitive-advantage-over-invisible-brands-302768554.html)). Branded mentions, YouTube presence, Reddit discussion, and Wikipedia coverage are all leading indicators.

**Signals that diverge sharply by platform:**

- Reddit — large on Perplexity (6.6%), small on ChatGPT (1.93% post-September 2025), tiny on Gemini.
- LinkedIn — 14.3% ChatGPT Search, 13.5% Google AI Mode, only 5.3% Perplexity.
- PDFs — outsized on Perplexity, less so elsewhere.
- X posts — dominant on Grok, near-zero everywhere else.
- News publications — 34% of AI Overview citations, smaller share on ChatGPT post-September 2025.

**Signals that are louder than the data supports:** `llms.txt` (no major chat assistant has officially confirmed automatic consumption — see Part 4 for the honest treatment). Long-form word count alone divorced from semantic completeness. Backlink count divorced from brand mentions. Generic "E-E-A-T" optimization without underlying entity recognition.

### Academic research on retrieval bias

Multiple peer-reviewed papers from 2025–2026 corroborate the practitioner data:

- *Source Coverage and Citation Bias in LLM-based vs Traditional Search Engines* ([arxiv.org/html/2512.09483v1](https://arxiv.org/html/2512.09483v1), December 2025) — measures domain-popularity-driven citation authority bias.
- *Do Large Language Models Favor Recent Content? A Study on Recency Bias in LLM-Based Reranking* ([arxiv.org/html/2509.11353v1](https://arxiv.org/html/2509.11353v1), SIGIR-AP 2025) — confirms LLM rerankers systematically favor recent content.
- *Data, Not Model: Explaining Bias toward LLM Texts in Neural Retrievers* ([arxiv.org/pdf/2604.06163](https://arxiv.org/pdf/2604.06163)) — neural retrievers prefer LLM-shaped passages over human-written content of similar semantic content.
- *Who Gets Cited? Gender- and Majority-Bias in LLM-Driven Reference Selection* ([arxiv.org/html/2508.02740](https://arxiv.org/html/2508.02740), August 2025).
- Health-specific work documenting that >75% of ChatGPT's health citations come from a narrow institutional core — Mayo Clinic, Cleveland Clinic, Wikipedia, NHS, PubMed.

The combined picture: strong domain authority bias, strong recency bias, structural preference for LLM-shaped writing, and concentration on a narrow institutional core for high-stakes topics. Optimizing for AI citation means optimizing for the same authority graph that wins in classical search, plus the specific structural moves listed above.

---

## Part 4 — Being usable by agentic systems

Agentic systems are the newest of the four classes and the most underspecified. They split cleanly into two sub-types with different needs:

- **Agents that act on websites** — browser agents that operate a real browser to complete tasks. OpenAI Operator, Anthropic Computer Use, Browser Use (open source), Perplexity Comet, OpenAI's Atlas, Microsoft Playwright MCP, Google Project Mariner.
- **Agents that build software** — coding agents that read documentation in order to generate code. Claude Code, Cursor, Cline, Aider, Windsurf, Devin, GitHub Copilot Agent, OpenAI Codex, Google Jules.

### How agentic browsers actually see a page

The dominant 2026 architecture is a hybrid of pixels, accessibility tree, and DOM, with the accessibility tree doing most of the work. This matters because it tells you what to optimize.

OpenAI's CUA (Computer-Using Agent), which powers Operator and ChatGPT's agent mode, is described in OpenAI's own developer guide as a screenshot loop ([developers.openai.com/api/docs/guides/tools-computer-use](https://developers.openai.com/api/docs/guides/tools-computer-use)):

> "Your harness acts as the hands on the keyboard and mouse, while the model uses screenshots to understand the current state."

The action vocabulary is fixed: `click`, `double_click`, `scroll`, `type`, `keypress`, `drag`, `move`, `wait`, `screenshot`.

Anthropic's Computer Use, available behind the `computer-use-2025-11-24` beta header on Claude Opus 4.5+ and Sonnet 4.5+, has the same surface area ([platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool)): screenshot capture, mouse control, keyboard input, plus optional bash and text-editor tools. Anthropic's [February 2026 acquisition of Vercept](https://www.anthropic.com/news/acquires-vercept) lifted Claude Sonnet's OSWorld score from under 15% to 72.5%, signaling that visual perception is where current capability gains are coming from.

Browser Use (the open-source library at [github.com/browser-use/browser-use](https://github.com/browser-use/browser-use), 95k+ GitHub stars as of May 2026) makes the hybrid explicit: feeds the model screenshots, DOM, accessibility tree, and an indexed list of "clickable elements" the model can address by number. Playwright is the underlying driver.

Browserbase ([browserbase.com](https://www.browserbase.com/)) is the infrastructure layer underneath much of this — isolated cloud browsers, session replay (Inspector), delegated authentication (Identity), an SDK called Stagehand that translates natural language into Playwright actions. 1,000+ customers including Microsoft, DeepMind, Clay, Amplitude, Ramp, Lovable. After a [$40M Series B in June 2025 at a $300M valuation](https://www.prnewswire.com/news-releases/browserbase-launches-director-to-automate-the-web-for-everyone-announces-40m-series-b-302483761.html), Browserbase became the default infrastructure layer for production browser agents.

The convergence across CUA, Computer Use, Browser Use, Atlas, Comet, and Playwright MCP, per [Search Engine Journal's analysis](https://www.searchenginejournal.com/how-ai-agents-see-your-website-and-how-to-build-for-them/570443/):

> "OpenAI Atlas, Microsoft Playwright MCP, and Perplexity's Comet all rely on accessibility data… industry is converging on the accessibility tree as the most reliable method."

Google's response: WebMCP. In February 2026, Google shipped WebMCP in Chrome Canary — a protocol letting a website expose its functions as MCP tools directly to the browser, so an agent inside Chrome can call them without DOM scraping. This is the first browser-vendor-shipped "the page is also a tool surface" standard. It is the agentic-browser analog of `llms.txt` for docs.

### What an agentic browser rewards

What makes a site work for an agent is what makes it work for a screen reader. The accessibility community has carried water on semantic HTML, ARIA roles, and accessible state representation for twenty years. The agent era turns that work into an economic asset.

Concrete moves for site owners:

1. **Use real semantic HTML.** `<button>` not `<div onClick>`. `<nav>`, `<main>`, `<form>`, `<label for="…">`. Agents trained on the accessibility tree handle these natively. Div-soup forces fall-back to pixel-matching — slower and less reliable.
2. **Label every interactive element.** `aria-label`, `aria-describedby`, visible text labels on icon-only buttons. An agent told "click the cart icon" finds it via `aria-label="Shopping cart"` before it ever screenshots.
3. **Express state as text, not only as color or icon.** "Out of stock" is a string in the DOM, not a greyed-out button. An agent reading the accessibility tree sees text, not chroma.
4. **Predictable, RESTful URL structure.** `/products/123` beats `/p?x=abc&t=xyz`. Stable URLs let agents skip the navigate-and-search step.
5. **No CAPTCHA on read flows.** Reserve CAPTCHA for write actions (checkout, signup), and prefer passive challenges (hCaptcha, Cloudflare Turnstile) over puzzle CAPTCHAs.
6. **Don't fingerprint headless Chromium aggressively.** Browserbase, Hyperbrowser, and Bright Data all offer CAPTCHA solvers, but every gate adds latency and failure modes. Treating legitimate-agent traffic as adversarial blocks your customers' agents.
7. **Stable element IDs.** `data-testid="add-to-cart"` survives redesigns. Treat key flows' test-ids as a public contract.
8. **Auth that works for delegated agents.** Browserbase Identity, OAuth-for-agents proposals, scoped API tokens with clear revoke UX. Sites that demand re-auth every session or fight cookies-cleared-between-sessions are hostile to agent-operated workflows.
9. **Don't rely on hover-only menus.** Hover doesn't translate cleanly to the CUA action vocabulary. Click-to-open or always-visible navigation works for agents and accessibility alike.
10. **Expose an MCP server or WebMCP descriptor for high-value actions** — search, checkout, ticket, schedule. This is the agentic-web equivalent of "we have an API."

### Agentic commerce — what it takes for an agent to actually buy from you

The browser-agent moves above keep an agent from getting *stuck*. They don't make checkout work. Commerce is the surface where most sites that look agent-friendly fail in practice — the agent navigates fine, adds to cart fine, and then the checkout flow throws a CAPTCHA, demands a fresh login, or rejects a stored card with no recovery path. Most agentic-commerce attempts fail somewhere between "agent has cart" and "merchant has order." The failure modes are knowable:

1. **Cart state survives the navigation the agent makes.** Cart-as-cookie that vanishes on a fresh session is a write-off for delegated agents. Cart-as-account-state, accessible via the same auth the agent already holds, works. Server-persisted carts win; localStorage-only carts lose.

2. **Auth that supports delegation.** Passkeys with scoped grants beat passwords. OAuth-for-agents proposals (and the early implementations from Browserbase Identity, Skyfire, and emerging spec work at the W3C) are where this is headed. Sites that force re-auth on every session, send SMS OTPs as a hard gate, or terminate sessions when User-Agent doesn't match are hostile to agentic checkout — they treat legitimate delegated traffic as fraud.

3. **Inventory and price freshness as structured fields.** `Offer` schema with `availability`, `price`, `priceCurrency`, and `priceValidUntil` lets an agent confirm what it's buying without scraping a "Add to cart" button to find out the item is out of stock. SKU- and variant-level structured data is meaningfully more useful to an agent than to a human shopper.

4. **A machine-readable returns and refund policy.** `MerchantReturnPolicy` schema (`returnPolicyCategory`, `merchantReturnDays`, `returnMethod`) lets the agent confirm the deal before committing. Hiding the return policy behind three clicks and a PDF is hostile to agentic buyers.

5. **Payment handoff that doesn't punish stored credentials.** Agents reusing a saved payment method should not face the same friction as a card typed for the first time. If your processor's adaptive-fraud model treats every agent session as suspect, you've blocked the buyer your customer wants to send. Work with the processor on agent-session signals (request-signed scoped tokens, attestation headers) instead of stricter blocks.

6. **A confirmation surface the agent can read.** Order-confirmation pages with `Order` schema (`orderNumber`, `orderStatus`, `orderDate`, line items with `OrderItem`) close the loop. Receipt-only-in-email is a black box to the agent.

7. **Expose checkout as an MCP tool.** For high-volume merchants, the most durable agentic-commerce play is `add_to_cart()`, `apply_promo()`, `checkout()` as MCP tools with documented argument shapes — not "agent figures out our DOM." Stripe is already shipping `mcp-server-stripe`; Shopify has agentic-checkout experiments in motion. This is the surface where commerce platforms compete on whose merchants get the agent traffic.

Most of this is invisible to humans visiting your site. That's exactly the point — agentic commerce is a parallel set of failure modes that classical UX QA never tests. A merchant whose human-side checkout has a 70% completion rate may be at 5% on agent sessions and not know it.

### How coding agents consume docs

Coding agents read documentation by pasting it into a context window and asking the model. The patterns that reward this consumption are consistent across Claude Code, Cursor, Cline, Aider, Windsurf, Devin, and Codex.

The 2026 cross-tool standard is `AGENTS.md` ([agents.md](https://agents.md/)), adopted by 60,000+ open-source repositories. Originating contributors: OpenAI Codex, Amp, Google Jules, Cursor, Factory. Now stewarded by the Agentic AI Foundation under the Linux Foundation. Compatible tools per agents.md include OpenAI Codex, Google Jules, Cursor, Aider, VS Code, Devin, GitHub Copilot, Zed, Warp, JetBrains Junie, Gemini CLI, Windsurf, Ona, RooCode.

There are no required fields. It is plain Markdown placed at the project root (or in subdirectories, where it scopes to that subtree). Common sections: project overview, build/test commands, code-style guidelines, testing instructions, security considerations.

The conspicuous absentee is Claude Code. Anthropic kept `CLAUDE.md` as its own convention. From the official Claude Code memory docs ([docs.anthropic.com/en/docs/claude-code/memory](https://docs.anthropic.com/en/docs/claude-code/memory)):

> "Claude Code reads `CLAUDE.md`, not `AGENTS.md`. If your repository already uses `AGENTS.md` for other coding agents, create a `CLAUDE.md` that imports it so both tools read the same instructions without duplicating them."

The recommended pattern when supporting both:

```markdown
@AGENTS.md

## Claude Code

Use plan mode for changes under src/billing/.
```

Or a symlink: `ln -s AGENTS.md CLAUDE.md`. For any public repo in 2026, the default should be: ship `AGENTS.md` at the root; if your team uses Claude Code, add a one-line `CLAUDE.md` that imports it. That single move covers ~95% of coding-agent users.

The other patterns coding agents reward:

1. **Code blocks with language tags.** ` ```python ` not ` ``` `. Agents use the tag to choose tooling.
2. **Copy-pasteable examples that run standalone.** No "assume you've already done step 3." Hidden prerequisites are the primary reason coding agents produce broken code from docs.
3. **A single canonical example per task.** Not five variants. Stripe and Twilio docs are the canonical examples of this discipline.
4. **Stable, versioned URLs.** `docs.stripe.com/checkout/quickstart`, not `docs.stripe.com/v3-beta-2/checkout/draft`. Doc links should still work in 18 months.
5. **Quickstart in under 100 lines.** Zero-to-working in one screen. Anthropic, Stripe, Vercel, Cloudflare, Twilio all do this — agents are token-bounded and lose fidelity on 5-screen quickstarts.
6. **Distinct page per task, not megapages.** Lets `llms.txt` index them precisely and lets the agent pull just the one it needs.
7. **OpenAPI / JSON Schema for APIs.** Machine-readable spec is worth more than prose. Stripe ships an OpenAPI spec; many SDK generators (and many coding agents) consume it directly.
8. **An MCP server for your API.** More below.

### llms.txt and llms-full.txt — what's real, what's aspirational

**The verdict.** Publish `llms.txt` if you ship developer docs. Skip it for marketing-only sites. No major frontier lab has confirmed `llms.txt` is a privileged crawl signal the way Google treats `/robots.txt` or `/sitemap.xml` — its real value today is toolchain-mediated (Mintlify, Cursor docs integrations, Devin's repo onboarding, Claude Code's `/init`), not model-consumed by default.

Proposed by Jeremy Howard of Answer.AI in September 2024 at [llmstxt.org](https://llmstxt.org/). Format: H1 → blockquote summary → free-form Markdown → H2-delimited file lists (`- [name](url): notes`). Companion convention: every HTML page also published as `.md` at the same path with `.md` appended. `llms.txt` is the curated index; `llms-full.txt` concatenates the full content.

**Live-verified `llms.txt` files** (fetched during research for this guide):

| Site | URL | Notes |
|---|---|---|
| Anthropic | [`platform.claude.com/llms.txt`](https://platform.claude.com/llms.txt) | 1,541 English pages indexed, 11 languages, every page has a `.md` twin |
| Stripe | [`docs.stripe.com/llms.txt`](https://docs.stripe.com/llms.txt) | Embedded agent instructions ("always check the npm registry…"), ~25 product sections |
| Cloudflare | [`developers.cloudflare.com/llms.txt`](https://developers.cloudflare.com/llms.txt) | Tree structure: top-level routes to per-product `llms.txt` files |
| Vercel | [`vercel.com/llms.txt`](https://vercel.com/llms.txt) | Hierarchical, points to `vercel.com/docs/llms-full.txt` |
| Mintlify | Auto-generated for every hosted docs site | Zero customer config |

Mintlify ([mintlify.com/docs/ai/llmstxt](https://mintlify.com/docs/ai/llmstxt)) is the model to copy: auto-generates `/llms.txt`, `/llms-full.txt`, `/.well-known/` variants per RFC 8615, and HTTP discovery headers. Auth-gated docs produce auth-gated `llms.txt` files. Override with a hand-curated file when you need to; delete the override and auto-generation resumes. [directory.llmstxt.cloud](https://directory.llmstxt.cloud/) tracks 849+ adopting sites; [llmstxt.site](https://llmstxt.site/) shows token counts (Next.js 675K, Nuxt 637K, Convex 408K).

What's actually consuming `llms.txt` today: coding agents with project context (Claude Code, Cursor, Cline, Windsurf, Aider) probe for it when pointed at a docs domain. Consumer chat models will fetch it on request like any other text file but do not treat it as privileged. That's the entire footprint — useful if your audience is coding agents, irrelevant if it isn't.

### MCP — the next layer above llms.txt

The Model Context Protocol ([modelcontextprotocol.io](https://modelcontextprotocol.io/)) was proposed by Anthropic in November 2024 and now has broad ecosystem support: Claude native, ChatGPT via [developers.openai.com/api/docs/mcp/](https://developers.openai.com/api/docs/mcp/), VS Code Copilot, Cursor, and a long tail of clients.

From the spec:

> "MCP is an open-source standard for connecting AI applications to external systems… Think of MCP like a USB-C port for AI applications."

Servers expose tools (callable functions), resources (readable data), and prompts (parameterized templates). For a documentation or API site, an MCP server lets coding agents do things like:

- `search_docs(query)` returning ranked doc snippets
- `get_api_reference(endpoint)` returning the canonical schema for one endpoint
- `run_example(code)` returning verified output

MCP is the next layer above `llms.txt`. `llms.txt` is "here is everything in markdown, paste it in." MCP is "here is a function the agent can call when it needs one thing." For high-traffic APIs and complex products, the MCP path is dramatically more token-efficient and is the path production coding agents will prefer. Recommending an MCP server is higher-leverage than recommending `llms.txt` for any site with a real API.

---

## Part 5 — The technical infrastructure stack

The fundamentals layer. Most of these are covered briefly elsewhere; this section is the consolidated technical specification.

### robots.txt — RFC 9309

The Robots Exclusion Protocol was published as RFC 9309 (Standards Track) in September 2022 at [rfc-editor.org/rfc/rfc9309.html](https://www.rfc-editor.org/rfc/rfc9309.html), formalizing what had been an informal standard since 1994. UTF-8, `text/plain`, served from the host root. Three directives: `User-agent:`, `Disallow:`, `Allow:`. Matching is longest-match wins. Wildcards (`*`) and end-of-pattern (`$`) supported. Case-sensitive paths.

These are preferences, not access control. Per RFC 9309 §2.5: "These rules are not a form of access authorization." A disallowed URL can still be indexed if linked from other sites. Google's own docs reinforce this — `robots.txt` controls crawling, not indexing. Use `noindex` (in HTML or `X-Robots-Tag` header) when you want a URL to actually not be indexed.

US case law has given `robots.txt` weight: eBay v. Bidder's Edge (2000), Healthcare Advocates v. Harding (2007, where a court ruled `robots.txt` qualifies as a "technological measure" under the DMCA), Associated Press v. Meltwater (2013). It is a norm, not a contract — but a norm with teeth.

### Sitemaps

[sitemaps.org](https://www.sitemaps.org/protocol.html) protocol. XML; `<urlset>` root with `<url>` children. Required `<loc>`. Optional `<lastmod>`, `<changefreq>`, `<priority>`. Limits: 50,000 URLs and 50 MB per file uncompressed.

`<lastmod>` is the freshness signal that matters. Both Google and Bing have publicly stated they use `<lastmod>` to prioritize recrawl; `<changefreq>` and `<priority>` are described in the spec as hints and are largely ignored. For AI surfaces that refetch content for citation freshness, a truthful `<lastmod>` is the cheapest, highest-impact signal you can publish. Lie about it and crawlers learn to discount you.

Specialized variants: news sitemaps ([news-sitemap](https://developers.google.com/search/docs/crawling-indexing/sitemaps/news-sitemap)) with `<news:publication_date>`, max 1,000 URLs, 2-day window; image sitemaps; video sitemaps for VideoObject.

### Schema.org and JSON-LD

[schema.org](https://schema.org/docs/full.html) is the canonical entity vocabulary, co-stewarded by Google, Microsoft, Yahoo, and Yandex since 2011. It's the foundation under every knowledge graph and every implicit graph an LLM builds.

Most-relevant types for AI consumption:

| Type | Use case |
|---|---|
| `Article` / `NewsArticle` / `BlogPosting` / `ScholarlyArticle` | Editorial |
| `FAQPage` | Q&A blocks (rich result deprecated, schema still useful) |
| `HowTo` | Step-by-step |
| `Product` / `Review` / `AggregateRating` | Commerce |
| `Organization` / `Person` | Publisher and author identity |
| `BreadcrumbList` | Site hierarchy |
| `SoftwareApplication`, `Event`, `VideoObject`, `Dataset`, `Recipe`, `JobPosting`, `LocalBusiness` | Specialized |

Google explicitly recommends JSON-LD over Microdata or RDFa ([developers.google.com/search/docs/appearance/structured-data/intro-structured-data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data)):

> "In general, Google recommends using JSON-LD for structured data if your site's setup allows it, as it's the easiest solution for website owners to implement and maintain at scale."

Web Almanac 2024 ([almanac.httparchive.org/en/2024/structured-data](https://almanac.httparchive.org/en/2024/structured-data)) shows JSON-LD on 41% of pages (up from 34% in 2022). 70% of sites that annotate structured data use JSON-LD as the primary format.

The `sameAs` property is the underrated entity-graph signal. Every `Organization` and `Person` should carry a `sameAs` array linking to authoritative external references: Wikipedia article, Wikidata Q-number URL (`wikidata.org/wiki/Q…`), official social profiles, Crunchbase, ORCID. This is how a knowledge graph confirms that the "Rick Watson" on rmwcommerce.com is the same Rick Watson cited elsewhere.

Minimum JSON-LD for editorial content:

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Marketing to Agents",
  "datePublished": "2026-05-24T09:00:00-04:00",
  "dateModified": "2026-05-24T09:00:00-04:00",
  "author": {
    "@type": "Person",
    "name": "Rick Watson",
    "url": "https://rmwcommerce.com/about",
    "sameAs": [
      "https://www.wikidata.org/wiki/...",
      "https://en.wikipedia.org/wiki/..."
    ]
  },
  "publisher": {
    "@type": "Organization",
    "name": "RMW Commerce Consulting",
    "url": "https://rmwcommerce.com"
  },
  "mainEntityOfPage": "https://rmwcommerce.com/marketing-to-agents"
}
```

The two non-negotiable fields for freshness: `datePublished` and `dateModified` in ISO 8601 (RFC 3339 profile, e.g., `2026-05-24T09:00:00-04:00`), not locale-prose ("May 24, 2026"). LLMs are unreliable at parsing locale dates; they're perfect at ISO 8601.

### Open Graph and Twitter Cards

[Open Graph](https://ogp.me/) — the protocol Facebook originated in 2010, still actively maintained. Required: `og:title`, `og:type`, `og:image`, `og:url`. Recommended: `og:description`, `og:site_name`, `og:locale`, `article:published_time`, `article:author`.

Who actually consumes Open Graph: every link unfurler — Slack, Discord, iMessage, Signal, WhatsApp, every chat-client embed. AI assistants that surface link previews (ChatGPT in chat, Claude in artifacts) inherit OG via their unfurling layer.

Web Almanac 2024: 64% of pages carry Open Graph data. Twitter Cards (`twitter:card`, `twitter:title`, `twitter:description`, `twitter:image`) — keep them. X has deprioritized the spec, but other unfurlers still consume `twitter:*` as fallback. Web Almanac 2024 shows 44% of mobile pages still carry Twitter Card markup despite X's neglect.

### Canonical URLs and duplicate content

`<link rel="canonical" href="…">` in `<head>` or the equivalent `Link:` HTTP header. The publisher's vote for which of N duplicate URLs is authoritative. Web Almanac 2024: 65% of pages carry canonicals.

LLM crawlers behave differently from Googlebot on deduplication. Observed: GPTBot, ClaudeBot, and CCBot fetch the full URL set they discover regardless of canonical declarations, and dedup at the corpus-processing layer via shingled-hash near-dup detection. Canonical declarations won't stop training-time inclusion of duplicates, but they do affect which URL gets cited at answer time (the canonical wins because that's what's in the answer engine's index). Still set `rel="canonical"` correctly — it controls citation, not crawl.

### HTTP signals

`X-Robots-Tag` ([MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/X-Robots-Tag)) — HTTP response header equivalent of `<meta name="robots">`, used for non-HTML resources (PDFs, images, JSON endpoints). Supported directives include `noindex`, `nofollow`, `nosnippet`, `noimageindex`, `max-snippet:N`, `unavailable_after:`, plus bot-specific scoping (`X-Robots-Tag: GPTBot: noindex, nofollow`). Robots.txt blocks happen before X-Robots-Tag is ever seen.

`Cache-Control`, `ETag`, `Last-Modified` per RFC 9111. Serve real ETags and accurate Last-Modified; respond `304 Not Modified` to conditional requests. Cloudflare's bot telemetry shows 304-aware sites consume ~70% less crawler bandwidth than always-200 sites — translates directly to faster recrawl windows.

`Content-Type: text/html; charset=utf-8` — non-negotiable; agents fail unpredictably on missing charsets.

`Content-Encoding: gzip` or `br` — essential at scale; modern AI crawlers support brotli.

HTTP/2 has been Googlebot's default since November 2020 ([Search Central blog](https://developers.google.com/search/blog/2020/09/googlebot-will-soon-speak-http2)). HTTP/3 (QUIC) is mixed across AI crawlers as of 2026; HTTP/2 is the safe target. Multiplexing reduces TCP overhead — a real win for bots hammering many URLs per session.

### Markdown as a first-class output format

Serve `.md` alongside `.html`. Implementations in the wild: Stripe (`docs.stripe.com/path.md`), Anthropic (every doc page on `platform.claude.com` has a sibling `.md`), Cloudflare, Vercel, every Mintlify-hosted docs site.

Content negotiation: `text/markdown` is a registered IANA media type per RFC 7763 ([rfc-editor.org/rfc/rfc7763.html](https://www.rfc-editor.org/rfc/rfc7763.html), March 2016). The header form:

```
GET /article HTTP/2
Accept: text/markdown
```

Adoption is still niche. The community direction is "always serve the `.md` at a stable URL" rather than negotiate on a header. Cheapest implementation: a Cloudflare Worker or middleware mapping `Accept: text/markdown` to `/<path>.md`.

Why agents prefer markdown: no HTML stripping, no CSS / JS / nav cruft to filter, structure intact, 30–60% fewer tokens than equivalent HTML. For agent-driven retrieval (RAG indexing, MCP doc-server consumption) markdown is materially cheaper to process. Not offering a `.md` version is now a competitive disadvantage for documentation sites.

### Server-rendered HTML vs JS SPAs

Google is the only major crawler that renders JavaScript at scale (headless Chromium, multi-phase pipeline per [Google's JS SEO docs](https://developers.google.com/search/docs/crawling-indexing/javascript/javascript-seo-basics)):

> "Server-side or pre-rendering is still a great idea because it makes your website faster for users and crawlers, and not all bots can run JavaScript."

Most AI crawlers fall into "not all." GPTBot, ClaudeBot, CCBot, PerplexityBot fetch raw HTML and do not execute JS. Bytespider and Applebot run JS but inconsistently. Content that exists only after hydration is invisible to roughly 80% of AI crawlers. Web Almanac 2024 shows the rendered-vs-raw word count gap is 13.6–17.5% on homepages — most of the web is already server-rendered. Don't be the exception.

Hydration patterns that work: Next.js App Router with React Server Components, Astro's islands architecture, Remix's full SSR, SvelteKit and Nuxt with SSR/SSG modes.

Anti-patterns that break agent access: pure CSR React/Vue/Angular SPAs with empty `<div id="root">` and content injected only after JS; content gated behind client-side auth; headlines or dates loaded via XHR after first paint.

Quick test:

```
curl -A "GPTBot" https://example.com/article | grep -c "<h1"
```

If the headline isn't in raw HTML, no JS-disabled crawler will see it.

### Performance

Core Web Vitals ([web.dev/articles/vitals](https://web.dev/articles/vitals)): LCP ≤ 2.5s, INP ≤ 200ms (replaced FID in March 2024), CLS ≤ 0.1 — at the 75th percentile of user experience. Pages meeting all three are eligible for Google's page-experience boost.

For AI crawlers specifically: a site with TTFB > 800ms gets crawled less aggressively than one at < 200ms — visible in Cloudflare's per-bot rate telemetry. For citation freshness, fast TTFB literally means more frequent recrawl, which means a fresher snapshot in the answer engine's cache.

JavaScript bundles >500KB compressed are a tax on every crawler that does render. Image weights matter less to AI crawlers (most don't load images) but matter a lot to user-triggered fetchers under user-perceived latency budgets.

### Accessibility as agent-friendliness

The accessibility tree is the same data structure agentic browsers see. WCAG 2.2 ([w3.org/TR/wcag22](https://www.w3.org/TR/wcag22/)) Success Criterion 1.3.1:

> "Information, structure, and relationships conveyed through presentation can be programmatically determined or are available in text."

That is the literal requirement for agent-readability, written twenty years before agents existed. A site passing WCAG AA is by construction a site Operator and Computer Use can drive. A site failing it — `<div onclick>` buttons, image-only nav, missing alt text — is a site agents fail on.

### Visual content for vision-capable agents

Most large frontier models now process images natively — GPT-4o, Gemini 2.5+, Claude with vision input, Apple Intelligence's on-device VLM. Agentic browsers (Operator, Anthropic Computer Use, Atlas, Comet) all loop on screenshots. Image-as-citation is a small but growing surface.

Concrete moves:

1. **Descriptive alt text, not decorative alt text.** "Bar chart showing AI bot share of all crawler traffic in 2025: Googlebot 50%, GPTBot 7.7%, ClaudeBot 5.4%" beats "chart." Alt text is what a VLM-blind agent uses; for VLM-capable agents, alt text is still cheaper to read than the image itself.
2. **`ImageObject` schema** with `contentUrl`, `caption`, `description`, and `representativeOfPage` lets grounded-AI surfaces select the right image for a citation thumbnail.
3. **Image sitemaps** ([Google image sitemap docs](https://developers.google.com/search/docs/crawling-indexing/sitemaps/image-sitemaps)) with `<image:caption>` and `<image:title>` on key visuals. Underused.
4. **Open Graph image dimensions accurate.** `og:image:width` / `og:image:height` enables link-unfurler agents to render previews without round-tripping for the file.
5. **Charts and tables as text first, image second.** Publish the underlying data table in HTML; the image is the human-friendly rendering. Agents that can't parse the image can still parse the table; agents that can parse the image will cite the table for precision.
6. **EXIF / IPTC metadata on photography.** For visual journalism, product imagery, and primary-source documentation, embedded metadata (photographer, date, location, rights) is the only signal a VLM has about provenance.

The whole space is still settling. Today's leverage is alt-text discipline plus `ImageObject` schema; the rest is amplification.

### How to measure — did any of this work

For a moving target with no single dashboard, measurement is the weakest part of the agent-marketing stack. The current 2026 reality:

| Surface | Tool | What it tells you | Cost |
|---|---|---|---|
| Microsoft Copilot, Bing AI summaries | [Bing Webmaster Tools — AI Performance](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview) | Per-query citation count, cited pages, grounding queries, visibility trends | Free |
| ChatGPT, ChatGPT Search | Analytics filter on `utm_source=chatgpt.com` referrals | Click-through volume only; not citations | Free |
| Google AI Overviews | Google Search Console — no AI Overview breakout exists | Inferred from total impressions/clicks plus position drops | Free (incomplete) |
| Cross-surface citation tracking | Profound, Peec AI, Ahrefs Brand Radar, Semrush Brand24 | Mention/citation tracking across ChatGPT, Perplexity, AIO, Claude | Paid |
| Crawler activity | Cloudflare bot analytics, server logs, Google Search Console crawl stats | Per-bot fetch volume, 304 rate, response time | Free if on Cloudflare |

What to actually track, monthly, in one report:

1. Bing AI Performance — citation count, top cited pages, grounding queries
2. `utm_source=chatgpt.com` and `utm_source=perplexity.ai` referral volume from analytics
3. Brand-mention monitor — unique authoritative domains citing your brand month-over-month
4. Crawler logs — confirm GPTBot, ClaudeBot, OAI-SearchBot, PerplexityBot, Googlebot, ChatGPT-User, Claude-User, Perplexity-User are all returning 200 OK on the URLs you care about

If you cannot answer "did Bing's AI Performance dashboard show more citations this month than last," you cannot defend any investment in this work. Get the dashboard set up before you ship anything else from this guide.

---

## The 22-item priority checklist

Impact-ordered. Items 1–5 are the 80/20.

### Tier 1 — Do this first
1. Serve content as raw server-rendered HTML — headline, body copy, dates visible in the response before JS runs.
2. Publish `Article` / `Organization` / `Person` JSON-LD on every editorial page with `datePublished`, `dateModified`, `author`, `publisher`, and `sameAs` arrays linking to Wikipedia / Wikidata / official profiles.
3. Set `rel="canonical"` on every page; never let two URLs serve the same content without one canonicalizing to the other.
4. Write a deliberate `robots.txt` that separates training crawlers from search/answer crawlers from user-triggered fetchers. Always allow `ChatGPT-User`, `Claude-User`, `Perplexity-User`, `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot`, `Googlebot`, `Bingbot`, `Applebot` regardless of training stance.
5. Publish `sitemap.xml` with truthful `<lastmod>` timestamps and reference it from `robots.txt`.

### Tier 2 — High leverage
6. Front-load the answer in the first 30% of every long-form page (40–75 words after the lede).
7. Open Graph + Twitter Card meta tags on every page.
8. ISO 8601 timestamps in JSON-LD and visible `<time datetime="…">` elements.
9. Author bylines linked to author pages with `Person` schema and `sameAs` external links.
10. `Cache-Control`, `ETag`, `Last-Modified` headers; respond `304` to conditional requests.
11. Brotli/gzip compression; HTTP/2 minimum.
12. Pass WCAG 2.2 AA. This is your agentic-browser readiness check.

### Tier 3 — If you have docs or structured content
13. `BreadcrumbList`, `FAQPage`, `HowTo` schema where applicable.
14. Ship `.md` mirrors of every important HTML page; map `Accept: text/markdown` to the markdown.
15. Publish `/llms.txt` (and optionally `/llms-full.txt`) if you're a docs site.
16. Ship `AGENTS.md` at every public-repo root; for Claude Code users add a one-line `CLAUDE.md` that imports it.
17. Publish OpenAPI / JSON Schema for any API at a stable URL.
18. Run an MCP server for the high-value actions on your site (search, checkout, file ticket, schedule). Register at modelcontextprotocol.io.

### Tier 4 — Polish and measurement
19. Hit Core Web Vitals at p75 (LCP ≤ 2.5s, INP ≤ 200ms, CLS ≤ 0.1).
20. `X-Robots-Tag` HTTP headers on non-HTML resources (PDFs, JSON APIs).
21. Disclose AI-assisted content per E-E-A-T guidance; image alt text on every meaningful image.
22. Subscribe to Bing Webmaster Tools — AI Performance for Copilot citation telemetry. Monitor `utm_source=chatgpt.com` referrals. Use brand-mention monitoring (Ahrefs Brand Radar, Semrush, Profound, Peec AI) for the surfaces that don't expose citation data directly.

---

## What we still don't know

Here's what we don't know yet. The major open questions:

1. **`llms.txt` consumption by frontier labs.** No major lab (Anthropic, OpenAI, Google, Meta) has publicly confirmed automatic crawl-based consumption of `/llms.txt`. Current value is real but toolchain-mediated. Publish it if you ship docs; skip it for marketing sites.

2. **Why Reddit and Wikipedia citation collapsed on ChatGPT in September 2025.** The shift is documented in Semrush's 13-week tracking. The most credible explanation is an OpenAI tuning change. Whether the shift is permanent, partial, or reversible is unknown.

3. **The Ahrefs March 2026 finding** that Google AI Overview / top-10 overlap dropped from 76% to 38% in seven months. Either the trend continues (and AI Overview ranking diverges further from organic), the metric stabilizes around 30–40%, or Google course-corrects. The right posture is to optimize for the durable signals — entity, E-E-A-T, structured data, information gain — and re-measure quarterly.

4. **Claude citation research is thin.** The biggest large-N studies (Ahrefs, Semrush, Profound) excluded or under-sampled Claude. Anthropic's own product policy ("citations must be included") and structural design (free citation fields, dynamic filtering) suggest Claude rewards answer-first, well-structured pages — but the empirical confirmation is not yet at the scale we have for ChatGPT or Perplexity.

5. **Stealth crawling from Perplexity and others.** Cloudflare's August 2025 documentation of Perplexity's undeclared crawlers is solid for Perplexity. The June 2024 TollBit allegations against OpenAI and Anthropic have not been reproduced at scale by independent investigation. Sites with sensitive content should layer WAF and bot-management controls on top of `robots.txt` regardless.

6. **The agentic-web monetization model.** Perplexity's 80/20 publisher revenue share is the only meaningful production model. OpenAI has bilateral licensing deals (News Corp, Vox Media, Axel Springer, FT, etc.) but no programmatic revenue share. Google, Anthropic, and Microsoft have nothing comparable. Whether the Perplexity model spreads or stays unique is a major open question for publisher economics.

7. **Whether WebMCP becomes a standard.** Google's February 2026 ship in Chrome Canary is the first browser-vendor "page-as-tool-surface" move. If Chromium adopts it (Edge, Brave, Arc, Opera) it becomes a real standard. If not, the agentic-web action layer stays MCP-server-side.

8. **How agentic-browser auth gets standardized.** Browserbase Identity, OAuth-for-agents proposals, and the various scoped-credential patterns are still bespoke per agent. A standard for delegated agent authentication would unlock significant agentic-commerce flow. Nothing public from W3C or IETF as of May 2026.

We will revise this guide as the answers land. The publication date and modification date in the JSON-LD header are the canonical truth for which version of the world this article is calibrated to.

---

## Sources & Attribution

This guide synthesizes research from primary vendor documentation, peer-reviewed academic work, and large-N industry studies. The source taxonomy applied throughout: **data > primary docs > opinion**. Every URL here was verified during research in May 2026.

### Vendor primary documentation

**OpenAI** — [developers.openai.com/api/docs/bots](https://developers.openai.com/api/docs/bots) · [openai.com/searchgpt](https://openai.com/searchgpt) · [developers.openai.com/api/docs/guides/tools-web-search](https://developers.openai.com/api/docs/guides/tools-web-search) · [developers.openai.com/api/docs/guides/tools-computer-use](https://developers.openai.com/api/docs/guides/tools-computer-use) · [developers.openai.com/api/docs/mcp](https://developers.openai.com/api/docs/mcp)

**Anthropic** — [support.claude.com/en/articles/8896518](https://support.claude.com/en/articles/8896518) · [platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool) · [platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool) · [docs.anthropic.com/en/docs/claude-code/memory](https://docs.anthropic.com/en/docs/claude-code/memory) · [platform.claude.com/llms.txt](https://platform.claude.com/llms.txt)

**Google** — [developers.google.com/search/docs/appearance/ai-features](https://developers.google.com/search/docs/appearance/ai-features) · [developers.google.com/search/docs/crawling-indexing/overview-google-crawlers](https://developers.google.com/search/docs/crawling-indexing/overview-google-crawlers) · [developers.google.com/search/docs/crawling-indexing/google-common-crawlers](https://developers.google.com/search/docs/crawling-indexing/google-common-crawlers) · [developers.google.com/search/docs/appearance/structured-data/intro-structured-data](https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data) · [developers.google.com/search/blog/2022/12/google-raters-guidelines-e-e-a-t](https://developers.google.com/search/blog/2022/12/google-raters-guidelines-e-e-a-t) · [ai.google.dev/gemini-api/docs/google-search](https://ai.google.dev/gemini-api/docs/google-search)

**Microsoft** — [blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview](https://blogs.bing.com/webmaster/February-2026/Introducing-AI-Performance-in-Bing-Webmaster-Tools-Public-Preview) · [blogs.bing.com/search/April-2025/Introducing-Copilot-Search-in-Bing](https://blogs.bing.com/search/April-2025/Introducing-Copilot-Search-in-Bing) · [learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/generative-ai-public-websites](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/generative-ai-public-websites) · [indexnow.org](https://indexnow.org)

**Perplexity** — [docs.perplexity.ai/guides/bots](https://docs.perplexity.ai/guides/bots) · [perplexity.ai/hub/blog/introducing-the-perplexity-publishers-program](https://www.perplexity.ai/hub/blog/introducing-the-perplexity-publishers-program)

**Apple** — [support.apple.com/en-us/119829](https://support.apple.com/en-us/119829)

**Meta** — [developers.facebook.com/docs/sharing/webmasters/web-crawlers](https://developers.facebook.com/docs/sharing/webmasters/web-crawlers)

**Mistral** — [docs.mistral.ai/robots](https://docs.mistral.ai/robots)

**xAI** — [docs.x.ai/developers/tools/web-search](https://docs.x.ai/developers/tools/web-search)

**Common Crawl** — [commoncrawl.org/ccbot](https://commoncrawl.org/ccbot)

**Amazon** — [developer.amazon.com/amazonbot](https://developer.amazon.com/amazonbot)

### Standards bodies

[RFC 9309 (Robots Exclusion Protocol)](https://www.rfc-editor.org/rfc/rfc9309.html) · [RFC 7763 (text/markdown media type)](https://www.rfc-editor.org/rfc/rfc7763.html) · [sitemaps.org](https://www.sitemaps.org/protocol.html) · [schema.org](https://schema.org/docs/full.html) · [ogp.me](https://ogp.me/) · [W3C WCAG 2.2](https://www.w3.org/TR/wcag22/) · [llmstxt.org](https://llmstxt.org/) · [agents.md](https://agents.md/) · [modelcontextprotocol.io](https://modelcontextprotocol.io/)

### Large-N industry studies

**Ahrefs** — [Why ChatGPT cites pages (1.4M prompts, Feb 2025)](https://ahrefs.com/blog/why-chatgpt-cites-pages/) · [AI search overlap study (15K queries, July 2025)](https://ahrefs.com/blog/ai-search-overlap/) · [ChatGPT's most-cited pages](https://ahrefs.com/blog/chatgpts-most-cited-pages/) · [Google AI Overviews study](https://ahrefs.com/blog/google-ai-overviews/)

**Semrush** — [Most-cited domains in AI (~230K prompts, 100M+ citations)](https://www.semrush.com/blog/most-cited-domains-ai/) · [LinkedIn AI visibility study](https://www.semrush.com/blog/linkedin-ai-visibility-study/) · [AI Mode comparison study](https://www.semrush.com/blog/ai-mode-comparison-study/) · [Semrush AI Overviews study (10M+ keywords)](https://www.semrush.com/blog/semrush-ai-overviews-study/)

**Profound, ALM Corp, Writesonic, Similarweb, BrightEdge, SEranking** — [Top domains cited by AI search](https://almcorp.com/blog/top-domains-cited-by-ai-search/) · [44% of ChatGPT citations in first third](https://almcorp.com/blog/chatgpt-citations-study-44-percent-first-third-content/) · [AI Overview citations drop](https://almcorp.com/blog/google-ai-overview-citations-drop-top-ranking-pages-2026/) · [LLM AI search citation study (Writesonic)](https://writesonic.com/blog/llm-ai-search-citation-study-dominant-domains) · [Most-cited domains LLMs (Similarweb)](https://www.similarweb.com/blog/marketing/geo/most-cited-domains-llms/) · [BrightEdge AI search reports](https://www.brightedge.com/resources/research-reports/ai-search-visits-in-surging-2025)

**Cloudflare** — [From Googlebot to GPTBot: who's crawling your site in 2025](https://blog.cloudflare.com/from-googlebot-to-gptbot-whos-crawling-your-site-in-2025/) · [The crawl-to-click gap](https://blog.cloudflare.com/crawlers-click-ai-bots-training/) · [Perplexity stealth crawlers](https://blog.cloudflare.com/perplexity-is-using-stealth-undeclared-crawlers-to-evade-website-no-crawl-directives/)

**Reuters Institute, Mozilla Foundation, Web Almanac** — [How many news websites block AI crawlers](https://reutersinstitute.politics.ox.ac.uk/how-many-news-websites-block-ai-crawlers) · [Common Crawl in LLM training corpora](https://www.mozillafoundation.org/en/research/library/generative-ai-training-data/common-crawl/) · [Web Almanac 2024 — Structured Data](https://almanac.httparchive.org/en/2024/structured-data) · [Web Almanac 2024 — SEO](https://almanac.httparchive.org/en/2024/seo)

### Academic / peer-reviewed

[Source Coverage and Citation Bias in LLM-based vs Traditional Search Engines](https://arxiv.org/html/2512.09483v1) · [Do LLMs Favor Recent Content?](https://arxiv.org/html/2509.11353v1) · [Data, Not Model: Explaining Bias toward LLM Texts in Neural Retrievers](https://arxiv.org/pdf/2604.06163) · [Who Gets Cited? Gender- and Majority-Bias in LLM-Driven Reference Selection](https://arxiv.org/html/2508.02740)

### Directories and trackers

[Known Agents (formerly Dark Visitors)](https://knownagents.com/agents) · [Cloudflare Radar Bots Directory](https://radar.cloudflare.com/bots) · [ai-robots-txt community list](https://github.com/ai-robots-txt/ai.robots.txt) · [directory.llmstxt.cloud](https://directory.llmstxt.cloud/) · [llmstxt.site (with token counts)](https://llmstxt.site/)

### Industry analysis

[Search Engine Journal: How AI Agents See Your Website](https://www.searchenginejournal.com/how-ai-agents-see-your-website-and-how-to-build-for-them/570443/) · [Search Engine Land: Google-Extended crawler](https://searchengineland.com/google-extended-crawler-432636) · [Nieman Lab: Google using opted-out content for AI Overviews](https://www.niemanlab.org/2025/05/google-is-using-content-from-publishers-who-opt-out-of-other-ai-training-to-power-ai-overviews/) · [PPC.land: 23 factors that get content cited by AI search](https://ppc.land/23-factors-that-actually-get-your-content-cited-by-ai-search-engines/) · [Digiday on Perplexity revenue model](https://digiday.com/media/how-perplexity-new-revenue-model-works-according-to-its-head-of-publisher-partnerships/) · [Pedowitz Group on Bing Copilot sourcing](https://www.pedowitzgroup.com/how-bing-copilot-sources-answers-aeo-for-microsoft-search) · [Growth Marshal Perplexity playbook](https://www.growthmarshal.io/field-notes/the-perplexity-playbook) · [Ziptie.dev on FAQ schema for AI](https://ziptie.dev/blog/faq-schema-for-ai-answers/) · [Adweek on YouTube overtaking Reddit in LLM citations](https://www.adweek.com/media/youtube-just-overtook-reddit-on-llm-citations/)

**Corrections from prior circulating versions:**

- `news.designrush.com` link → replaced with primary source `ahrefs.com/blog/google-ai-overviews/`
- `code.claude.com/docs/en/memory` → corrected to `docs.anthropic.com/en/docs/claude-code/memory` (redirects to same destination; both work)
- `docs.x.ai/docs/guides/live-search` → corrected to `docs.x.ai/developers/tools/web-search` (Live Search API deprecated January 12, 2026)
- Copyright notice → updated to 2026 RMW Commerce Consulting standard template

---

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from vendor primary documentation, peer-reviewed research, and large-N industry studies. See [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.
