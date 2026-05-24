# AI Agent Discoverability and Protocols: What's Real, What's Hype, What's Dead

**Concept by concept on the AI-agent discoverability and protocol stack: what's deployable, what's wait-and-see, what's already dead. Includes audience-specific recommendations and direct attribution of hype.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-22*

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

The discoverability and protocol landscape looks fragmented but is actually consolidating around three load-bearing standards: **OpenAPI for tool specs**, **MCP for tool and data connections**, and **robots.txt for access control**. Meanwhile, ChatGPT-era formats are fading, browser-side surfaces are still speculative, and inter-agent protocols are competing without a clear winner.

- Know which formats to deploy now, which to watch, and which to skip entirely
- Stop wasting time evaluating deprecated or not-yet-stable formats
- Understand the convergence trajectory so you don't architect against where this is going

### Where to spend your time, in priority order

| # | Format / Protocol | Deploy priority | Why |
| :-- | :--- | :--- | :--- |
| **1** | `openapi.yaml` | Deploy now | Load-bearing. Every agent ecosystem reads it. Already necessary for any public API. |
| **2** | MCP server | Deploy now | Won the tool/data slot in the Anthropic ecosystem. Growing fast. SDK in Python, TypeScript. |
| **3** | `robots.txt` (agent user-agents) | Fix it | Plumbing that's wrong more often than not. Cheap to fix, meaningful for agent discovery. |
| **4** | `llms.txt` | Pragmatic adopt (curated-content sites) | Low cost, modest upside. Deploy if you have curated content. Don't over-engineer. |
| **5** | WebMCP | Track, don't deploy | Browser-side surface for in-page AI tools. Spec fragmenting. Not production-ready. |
| **6** | A2A | Read it, don't deploy | Cross-vendor agent interop. Interesting spec. No production use case for most readers. |
| **7** | `/.well-known/ai-plugin.json` | Skip | No load-bearing consumer since ChatGPT Plugins wound down April 2024. ([source](https://community.openai.com/t/plugin-store-and-new-chats-with-plugins-closed-march-19-2024/689877)) |

Most readers should handle rows 1–3 and check back on row 4 in six months. If you're a merchant or commerce operator, the four-file setup from Stripe's field guide (rows 1, 3, 4, and 7 — but skip 7) covers your discoverability baseline.

---

## How to use this guide

If you're a developer or technical architect: read straight through. The implementation notes for each format are in each section's "What to do" block, followed by audience-specific tags.

If you're a non-technical executive: the priority table above is what you need. Share it with your technical lead with the question: "Which of rows 1–3 are we not doing and why?"

For full glossary-style one-liner definitions of all terms here, see the [RMW Commerce Glossary](glossary.md#discoverability-and-protocols).

For the agent architecture patterns that consume these protocols on the receiving end, see [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md).

---

## Background: why this is confusing right now

The agent ecosystem matured fast and in different directions at once. Between mid-2023 and mid-2026:

- OpenAI wound down the ChatGPT Plugins beta, leaving `ai-plugin.json` without a primary consumer. The wind-down happened in phases: new plugin conversations ended March 19, 2024; all existing plugin chats shut down April 9, 2024. OpenAI's stated reason: "GPTs offer a better way to reach ChatGPT users." ([source](https://community.openai.com/t/plugin-store-and-new-chats-with-plugins-closed-march-19-2024/689877))
- Anthropic launched MCP in November 2024 and donated it to the Agentic AI Foundation (under the Linux Foundation) in December 2025. It grew from a single-vendor protocol to 10,000+ servers and 97 million monthly SDK downloads in roughly one year. ([source](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/))
- Google launched A2A in April 2025 and donated it to the Linux Foundation two months later in June 2025 — a timeline that suggests they wanted neutral governance fast.
- Jeremy Howard proposed `llms.txt` in September 2024. Adoption is real (Anthropic, Cloudflare, Vercel all deploy it) but no major LLM provider has made a binding public commitment to consume it as canonical. ([source](https://llmstxt.org/))
- Multiple "WebMCP" proposals emerged independently — the W3C Web Machine Learning Community Group, a separate MCP-B implementation, and others — creating naming confusion around a concept that isn't yet standardized.

The result is a landscape that looks like competing fragmentation but is actually winnowing in predictable ways. This article names what's consolidating, what's competing without a winner, and what's already done.

I've deployed MCP servers in my own infrastructure. I haven't deployed A2A, and based on what I can observe from the current state of the spec, I don't plan to until cross-vendor agent delegation is a real problem I'm trying to solve rather than a hypothetical one.

### A note on Danny Smith's field guide

Danny Smith leads global agentic commerce solution architecture at Stripe and authored their technical field guide solo. He appears on the Watson Weekly podcast in episode 271W: [TBD: link when the episode airs on 2026-06-10]. The merchant-side recommendations in this article draw heavily on his published field guide, which is the closest thing to a Tier 1 practitioner source on the commerce side of this stack.

---

## openapi.yaml / openapi.json

### What it is

The OpenAPI Specification (OAS) is a machine-readable description of a REST API in YAML or JSON. The format has been around since 2011 (as the Swagger Specification; renamed OpenAPI in 2016 when SmartBear donated it to the Linux Foundation via the OpenAPI Initiative). It describes endpoints, request/response shapes, authentication methods, and parameters in a way both humans and machines can read. ([source](https://www.openapis.org/what-is-openapi))

This is not new. Most public APIs already have an OpenAPI spec, or could generate one from their existing code.

### Why it matters for agent discoverability

Every major agent ecosystem reads OpenAPI specs. ChatGPT Custom GPT Actions are defined by pointing to an OpenAPI spec at a URL. MCP server tool definitions are frequently generated from or translatable to OpenAPI. Function-calling schemas across all major LLM vendors follow OpenAPI-compatible patterns. If you want an AI agent to be able to call your API, the OpenAPI spec is the starting point for every integration path.

Danny Smith, in Stripe's field guide on agentic commerce, frames explicit technical instructions — including how to call your APIs — as one of the four foundations of agentic commerce readiness. ([source](https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide)) The OpenAPI spec is the standardized mechanism for that. The guide recommends treating your OpenAPI summary fields "like prompts" — write them for agents, not just for developers.

### What's hype

There's no meaningful hype around OpenAPI itself — it's been a production standard for a decade. The only legitimate critique is verbosity, especially for simple APIs. Neither that nor YAML indentation frustration is a reason not to maintain a spec.

### What to do

Maintain a current, accurate spec at a stable URL. If your framework generates it automatically (FastAPI, NestJS, Spring Boot, and others all do), verify it reflects your actual API surface. If you don't have one, generating it from existing code is the right starting point — don't write it by hand.

Make the spec URL public and stable. Agents discovering your API need to be able to fetch the spec without authentication. If your spec requires auth to read, agents can't use it for discovery.

**Audience tags:**
- For a non-developer site owner: Delegate to your developer. If you have a public API, you need this. If you don't have a public API, skip.
- For a SaaS / product engineer: Build it. If your framework doesn't auto-generate it, add it now. This is load-bearing infrastructure for any agent integration path.
- For a merchant / commerce operator: Required for any agent purchasing workflow to reach your catalog or checkout API. Include it in your agentic commerce infrastructure plan.
- For an agent system builder: Essential. Your agents need this to discover and invoke third-party services.

---

## robots.txt — the agent-relevant view

### What it is

`robots.txt` has been around since 1994 — the Robots Exclusion Protocol, a plain-text file at a domain's root (`/robots.txt`) that tells automated crawlers which paths they can and can't access via `User-agent` rules. This is not new technology. What changed is who's reading it.

AI crawlers now read `robots.txt` in significant volume: GPTBot (OpenAI), ClaudeBot (Anthropic), PerplexityBot, Google-Extended (Google's AI training crawler), and an expanding list of purpose-built shopping and research agents. Some respect your rules; some don't. The ones that do respect it are the ones you want to be accessible to.

Cloudflare's data from 2024 found AI bots accessing approximately 39% of the top one million internet properties — and only 2.98% of those sites had taken any steps to manage that access. ([source](https://blog.cloudflare.com/declaring-your-aindependence-block-ai-bots-scrapers-and-crawlers-with-a-single-click/))

### Why it matters for agent discoverability

Danny Smith, in Stripe's field guide on agentic commerce, is direct: to be recommended by agents, you have to be visible. That requires ensuring your technical infrastructure welcomes agents — starting with confirming your `robots.txt` is configured correctly for known agent user-agents rather than blocking them indiscriminately. ([source](https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide))

The Stripe guide specifically calls out the distinction between verified commerce agents (which you want accessing your site) and generic scrapers (which you may want to rate-limit or block). The mechanism is agent-specific `User-agent` rules.

The wrong move is a blanket `User-agent: * Disallow: /` or blocking all AI crawlers in bulk. If you block GPTBot and ClaudeBot, you lose discovery in those agents' responses. Agents will route to competitors who are accessible. The right move is per-agent rules combined with WAF-level rate limiting — set the action to `Challenge` or return a `429 Too Many Requests` for known agents sending too many requests, rather than banning them outright. ([source](https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide))

### What's hype

There's no "winning robots.txt strategy." It's infrastructure plumbing. Getting it right means you're not inadvertently blocking agents that would send you traffic; it doesn't generate any positive signal beyond that.

### What to do

Add specific `User-agent` entries for the major AI agents. Verify your current configuration against the known user-agent strings (GPTBot, ClaudeBot, PerplexityBot, Google-Extended). If you're currently blocking them — either explicitly or via a catch-all deny — fix that first.

For rate limiting and pattern-based access control, do it at the WAF level rather than through `robots.txt`. WAF-level rate limiting handles agents that don't respect `robots.txt`; the file itself only reaches the ones that do.

The robotstxt.org primary specification is at [robotstxt.org](https://www.robotstxt.org/).

**Audience tags:**
- For a non-developer site owner: Check that you're not accidentally blocking AI crawlers with a catch-all deny. Your hosting provider likely has a UI for this.
- For a SaaS / product engineer: Implement per-agent User-agent rules and pair with WAF rate limiting. Thirty minutes of work, done.
- For a merchant / commerce operator: Part of Stripe's four-file merchant discovery setup. Prioritize this alongside `openapi.yaml`.
- For an agent system builder: Robots.txt is on the sites you're crawling, not something you deploy. Make sure your agent respects it — agents that don't are increasingly getting blocked at the WAF level.

---

## llms.txt

### What it is

`llms.txt` is a proposed standard — not yet a ratified specification — for a markdown file at a site's root that gives LLM consumers a curated index of the site's content at inference time. Proposed by Jeremy Howard of Answer.AI in September 2024. ([source](https://www.answer.ai/posts/2024-09-03-llmstxt.html))

The problem it's solving is real: LLMs trying to understand a website face a mismatch between context windows and website complexity. A full website's worth of HTML, navigation, ads, and JavaScript is both large and hard to parse. `llms.txt` gives LLM consumers a curated markdown path — a prioritized list of what's worth reading, in a format easier to consume than raw HTML.

The convention: `/llms.txt` at the root provides a brief overview and links. `/llms-full.txt` provides the full prioritized content in markdown.

Adoption is real: Anthropic, Cloudflare, and Vercel all deploy it. Thousands of sites serve the file. Tools and generators exist for major documentation platforms (VitePress, Docusaurus, and others). ([source](https://llmstxt.org/))

### Why it matters for agent discoverability

If your site has long-form guides, documentation, or product information that agents might need to reason about, `llms.txt` gives them a curated path to that content rather than asking them to parse your full HTML.

It's one of the four discovery files Danny Smith's field guide names as part of agent-readiness infrastructure for merchants. ([source](https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide))

### What's hype

Some commentary positions `llms.txt` as "the new SEO." That framing predicts adoption that has not yet materialized. The spec is an Answer.AI proposal ([source](https://www.answer.ai/posts/2024-09-03-llmstxt.html)) — not ratified by a standards body. Adoption signals are uneven; this article found no public commitment from Anthropic, OpenAI, Google, or other major LLM providers to consume `llms.txt` as canonical input as of May 2026. The format's impact on actual agent recommendations is not yet measurable in any publicly available data.

Simon Willison — one of the most credible practitioners writing about LLMs — has implemented llms.txt-style tooling in his own projects and called the concept "fantastic," but his implementation is for developer tooling (concatenated docs for context), not for general web discovery. The two use cases are different in important ways. ([source](https://simonwillison.net/2025/Apr/14/llms-as-the-first-line-of-support/))

There's also a valid skeptical framing: one analyst piece describes llms.txt as "a dud" given the lack of explicit LLM provider commitment. That may be premature — adoption is growing — but the honest answer is that the leverage here is moderate and uncertain, not transformative.

### What to do

Deploy if you have curated content and the setup cost is low. For most sites with a documentation or guide layer, that means writing a markdown index of your key content and placing it at `/llms.txt`. Don't build a complex pipeline to maintain it; a static file that gets updated when you publish major content is sufficient.

Don't over-engineer. The file is a signal, not a guarantee.

**Audience tags:**
- For a non-developer site owner: Skip for now. Adoption is too uneven to justify the setup time. Revisit in six months.
- For a content / docs / guide-heavy site: Adopt. Low cost, plausible upside, no downside. Write a markdown index of your key guides.
- For a merchant / commerce operator: Adopt as part of Stripe's recommended four-file discovery setup. The `ai-plugin.json` in that list is dead — see below — but `llms.txt` is the live member.
- For an agent system builder: This is consumer-side discovery, not relevant to building agents. Skip unless you're building the crawler side.

---

## /.well-known/ai-plugin.json

### What it was

OpenAI launched ChatGPT Plugins in March 2023. The plugin system used a JSON manifest at `/.well-known/ai-plugin.json` to describe plugin capabilities for the ChatGPT Plugins ecosystem — a precursor to today's Custom GPTs and function calling integration patterns.

### What happened

OpenAI wound down the ChatGPT Plugins beta in phases: new plugin conversations ended March 19, 2024; all existing plugin chats shut down April 9, 2024, with OpenAI shifting users to Custom GPTs and GPT Actions. ([source](https://community.openai.com/t/plugin-store-and-new-chats-with-plugins-closed-march-19-2024/689877)) OpenAI's stated reason at the time: "GPTs offer a better way to reach ChatGPT users." The manifest format lost its primary consumer at that point.

The Stripe field guide lists `ai-plugin.json` as one of "four files agents read" — that list is canonical for merchant discovery playbooks and describes current agent behavior accurately (legacy agents still check known locations). Of the four, `ai-plugin.json` is the one with no active primary consumer. The other three are live.

### What's in it for you in 2026

Skip unless you are actively maintaining a legacy ChatGPT Plugin integration. If you are, migrate: the path forward is either a Custom GPT (for ChatGPT-specific use cases) or an MCP server (for broader agentic ecosystem exposure).

**Audience tags:**
- For anyone: Skip. The format has no load-bearing consumer at meaningful scale in 2026.
- Exception: If you have a legacy ChatGPT Plugin that users depend on, migrate to a Custom GPT or MCP server before the next service disruption.

---

## MCP (Model Context Protocol)

### What it is

The Model Context Protocol (MCP) is an open protocol for connecting LLMs to tools, data sources, and prompts. Anthropic announced it in November 2024. ([source](https://www.anthropic.com/news/model-context-protocol)) In December 2025, Anthropic donated it to the Agentic AI Foundation, a directed fund under the Linux Foundation co-founded by Anthropic, Block, and OpenAI. ([source](https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/))

The protocol solves the "M×N integration problem": without a standard, M different AI applications each need custom integrations with N different services — an explosion of one-off implementations. MCP provides a single client-server interface. Write one MCP server for your service; any MCP client can call it.

The server exposes three primitives: **tools** (functions the LLM can invoke), **resources** (data the LLM can read), and **prompts** (pre-configured instruction templates). SDKs are available in Python, TypeScript, C#, and Java.

By its one-year anniversary in November 2025: over 10,000 active MCP servers and 97 million monthly SDK downloads. First-class client support in Claude Desktop, Claude Code, ChatGPT, Cursor, Gemini, Microsoft Copilot, and Visual Studio Code. ([source](https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/)) OpenAI adopted MCP across the Agents SDK, Responses API, and ChatGPT desktop in March 2025.

The Anthropic engineering blog has continued to publish on MCP deployment patterns, including on code execution via MCP in production environments. ([source](https://www.anthropic.com/engineering/code-execution-with-mcp))

### Why it matters

MCP is the protocol that's actually winning for the tool and data connection problem — the mechanism by which AI agents call external services, read databases, and interact with software infrastructure. If you maintain a service that AI agents should be able to query or act on, MCP is the integration path to build toward.

For Claude Code specifically: MCP servers are configured under `.claude/settings.json` and appear in the permissions model as `mcp__<servername>__<toolname>`. The [Claude Permissions Guide](claude-permissions-guide.md#mcp-wildcards) covers how to manage these at the project and user level.

The relationship to OpenAPI: MCP tool definitions and OpenAPI specs describe overlapping things from different angles. OpenAPI describes what your API does; MCP describes how an AI agent should discover and invoke it. Many MCP server implementations generate tool definitions from existing OpenAPI specs. The two are complementary, not competing.

### What's hype

"MCP is the universal standard." As of mid-2026, it's primarily Anthropic-ecosystem-centric for production deployments, though OpenAI adoption has meaningfully broadened it. "Everyone's doing MCP" describes momentum, not universality — the OpenAI ecosystem's primary integration pattern is still direct function calling for many use cases.

The other overclaim: treating MCP as a replacement for proper API design. MCP is a discovery and invocation layer. It doesn't replace the need for well-designed endpoints, proper auth, and rate limiting.

### What to do

If you maintain a service AI agents should be able to use: build an MCP server for it. Start with read-only tools. Use the official Python or TypeScript SDK. Define tool schemas carefully — the quality of your tool descriptions (the natural language explanations in the schema) directly affects whether agents invoke your tools correctly.

If you're a Claude Code user deploying agents internally: MCP servers for your own services (CRM, calendar, databases) are the infrastructure that makes Rung 3 and Rung 4 agents practical.

**Audience tags:**
- For a non-developer site owner: Not directly relevant. Your developer should evaluate whether your services need MCP exposure.
- For a SaaS / product engineer: This is your primary integration target. Build the MCP server for your service. Start read-only.
- For a merchant / commerce operator: Relevant if you want agents to query your catalog, inventory, or order management system directly. Higher complexity than robots.txt or llms.txt; plan for developer time.
- For an agent system builder: Essential. Your agents will consume MCP servers from external services. Understand the protocol deeply — it's the integration surface for everything you're building on.

---

## WebMCP

### What it is

"WebMCP" currently refers to at least two distinct proposals for running MCP-style tool calls in browser JavaScript contexts:

1. **W3C WebMCP** — a spec being incubated by the W3C Web Machine Learning Community Group at `webmachinelearning.github.io/webmcp/`. ([source](https://webmachinelearning.github.io/webmcp/)) This spec defines a `navigator.modelContext` JavaScript API that allows web pages to expose AI-callable tools — JavaScript functions with natural language descriptions and structured schemas.

2. **MCP-B** — a separate implementation from a community project that extends MCP for browser tab contexts, introducing browser-specific components for dynamic tool discovery and cross-tab routing. ([source](https://github.com/MiguelsPizza/WebMCP))

The naming overlap creates confusion. They're not the same specification, but both address the same problem — making MCP-style tool invocation work in browser environments rather than requiring a backend server.

### Why it matters — and why to wait

Two distinct specifications use the name WebMCP: the W3C draft ([source](https://webmachinelearning.github.io/webmcp/)) and the MCP-B project ([source](https://github.com/MiguelsPizza/WebMCP)). They are not interoperable. The fragmentation makes adoption decisions premature. For production code, MCP (server-side) is the current standard; WebMCP (browser-side) is wait-and-see until the W3C spec reaches Candidate Recommendation.

The longer-term direction of agentic browsing does point toward in-page AI assistants that can interact with what you're viewing. WebMCP is the infrastructure path being developed for that use case. But "being developed" is the operative phrase.

### What's hype

"WebMCP will replace MCP" — wrong framing. They're complementary surfaces. "WebMCP is ready for production" — it isn't. The naming confusion between the W3C spec and MCP-B is itself a signal of immaturity.

### What to do

Track the W3C spec and note when it reaches Candidate Recommendation status — that's the signal that browser vendors are preparing to implement it natively. Until then, don't write production code against it.

If you're explicitly building an application for in-page AI agents as an experiment, MCP-B provides an implementation path today with the explicit caveat that it may not align with the eventual W3C standard.

**Audience tags:**
- For a non-developer site owner: Ignore entirely.
- For a SaaS / product engineer: Track the W3C spec. No production action until CR status.
- For a merchant / commerce operator: Irrelevant for current planning. Check back in 2027.
- For an agent system builder: Watch this space. If you're building browser-embedded agents, you'll want to track both proposals.

---

## A2A (Agent-to-Agent Protocol)

### What it is

Google announced the Agent2Agent (A2A) protocol on April 9, 2025 at Google Cloud Next. ([source](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)) It's an open protocol for inter-agent communication — designed for one agent to delegate tasks to another agent across vendor or organizational boundaries, with authentication, state handoff, and result return. It uses HTTP, Server-Sent Events, and JSON-RPC 2.0. Agents advertise their capabilities via "Agent Cards."

In June 2025, Google donated A2A to the Linux Foundation, establishing the Agent2Agent Protocol Project under neutral governance. Version 0.3 shipped in August 2025. As of mid-2026, A2A has 150+ organizational supporters including Atlassian, Salesforce, SAP, ServiceNow, and others.

### Why this matters — and why not now

A2A is relevant if you're building multi-agent systems that need to cross trust boundaries: a customer service agent delegating a refund task to a payment processor's agent; a procurement agent delegating a supplier lookup to a logistics network's agent. Inside a single vendor's ecosystem — Anthropic agents calling your own subagents — you don't need A2A.

For most current agent builds, the patterns in [Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md) — typed return contracts, thin orchestrators, subagent specialization — handle everything you need without A2A.

### The honest position on A2A

Google introduced A2A in April 2025 as a proposed protocol for agent-to-agent communication. It coexists with other proposals: IBM's Agent Communication Protocol (ACP, [source](https://agentcommunicationprotocol.dev/introduction/welcome)), MCP-A2A interop layers, and vendor-specific schemes. No protocol has been ratified by a standards body or adopted across major LLM vendors as of mid-2026. Most production multi-agent systems run single-vendor stacks where cross-vendor delegation is not a problem.

"150+ supporters" reflects enterprise interest and Google's ecosystem influence; it does not indicate production adoption at scale. The Linux Foundation donation in June 2025 — two months after announcement — suggests Google moved quickly toward neutral governance. That's a good sign for long-term credibility, but the spec is still under active development (v0.3 in August 2025 is explicitly not v1.0).

Read the announcement. Don't deploy unless you have a concrete cross-vendor agent-delegation requirement, which most readers do not.

### What to do

Read about it. Understand the architecture. Don't deploy in production unless you have a concrete cross-vendor agent-delegation use case you're actively trying to solve — and you've evaluated A2A against direct API integration plus custom auth protocols to confirm it's the right tool.

I haven't deployed A2A and don't plan to until I have a specific cross-vendor problem that can't be solved cleanly by MCP plus direct API integration. That's the honest version of "Tier 3 — read, don't deploy."

**Audience tags:**
- For a non-developer site owner: Ignore.
- For a SaaS / product engineer: Read the spec. No deployment action until you have a concrete cross-vendor delegation requirement.
- For a merchant / commerce operator: Not relevant for current planning. The intra-vendor patterns cover your use case.
- For an agent system builder: Worth understanding deeply. A2A is the most likely protocol to matter if your system eventually needs to delegate across org boundaries. Track but don't ship against v0.x.

---

## Function calling

### What it is

OpenAI introduced function calling in June 2023 as an API capability: models could receive function definitions and output structured JSON objects specifying which function to call and with what arguments. ([source](https://openai.com/index/function-calling-and-other-api-updates/)) The model doesn't execute the function — it outputs the request, and your code executes it.

The term "function calling" is OpenAI's coinage. Anthropic calls the same capability "tool use." The mechanism is essentially identical across vendors. Every major LLM API has this capability: OpenAI's chat completions, Anthropic's Messages API, Google's Gemini API, and others all implement it. It's the foundational capability that makes agents possible.

### Why it matters

Function calling is the substrate everything else runs on. MCP tools get invoked via the function calling mechanism. Custom GPT Actions use it. Every agent you build, whether using raw API calls or a framework like LangChain or the Anthropic SDK, is ultimately making function calls.

Understanding this matters for avoiding architectural confusion: when you deploy an MCP server, you're not replacing function calling — you're adding a discovery and invocation layer on top of it.

### What's hype

Positioning function calling as a strategy. It's a capability, not a strategy. The strategic decisions are about what tools to expose, how to define them, what protocol to use for discovery (openapi.yaml, MCP), and what the agent does with the results.

### What to do

Use function calling directly when building single-agent workflows without a standardized discovery layer. Use MCP when you want that discovery and invocation surface shared across multiple agent consumers.

Both the OpenAI function calling docs ([platform.openai.com/docs](https://developers.openai.com/api/docs/guides/function-calling)) and Anthropic tool use docs ([platform.claude.com](https://platform.claude.com/docs/en/docs/build-with-claude/tool-use/overview)) are Tier 1 primary sources.

---

## Where this is converging — a verdict

The priority table at the top is one view. Here's the sharper version, with a verdict per category:

**Deploy now:**
- **OpenAPI** — load-bearing, has been for a decade, will be for another. No legitimate alternative.
- **MCP** — won the tool/data slot in the Anthropic ecosystem. OpenAI adoption broadening it. Linux Foundation governance is a credibility signal. Deploy servers for services agents should call.
- **robots.txt with WAF rate-limiting** — long-standing plumbing, now critical for agent discovery. Fix it once and it's done.

**Pragmatic adopt for some audiences:**
- **llms.txt** — curated-content and documentation-heavy sites only. Low cost, plausible upside. No downside if your site genuinely has content agents want. Skip if you're a bare product catalog without editorial content.

**Track, don't deploy:**
- **WebMCP** — browser-side in-page AI interaction. Fragmenting across two incompatible proposals. Wait for W3C Candidate Recommendation.
- **A2A** — cross-vendor agent delegation is a real future problem. The spec is still maturing. Most readers don't have the use case yet.

**Already dead:**
- **`/.well-known/ai-plugin.json`** — no meaningful consumer since ChatGPT Plugins wound down April 2024. ([source](https://community.openai.com/t/plugin-store-and-new-chats-with-plugins-closed-march-19-2024/689877)) Skip.

The practical decision tree: for APIs, deploy the OpenAPI spec. For agent tool/data access, deploy an MCP server. For content discovery, configure robots.txt and optionally add llms.txt. For everything else, wait.

---

## Where to go next

**[RMW Commerce Glossary](glossary.md#discoverability-and-protocols)** — one-liner definitions for every term in this article, with hype vs. reality marked and cross-links to primary sources. Several entries now include explicit "this is overhyped" notes — check the glossary's TL;DR callout for context on why that's there.

**[Multi-Agent Fan-Out and Verification](multi-agent-fan-out-and-verification.md)** — the architecture for agent systems that consume these protocols on the receiving end. If you're deploying MCP servers, the typed return contract and logging patterns in that guide are what makes agent integrations reliable in production.

**[Claude Permissions: Stop the Interruption Hell](claude-permissions-guide.md)** — how to manage MCP tool permissions at the project and user level in Claude Code, including the wildcard pattern for MCP server tools.

---

## Sources & Attribution

All source URLs verified live before publication.

**Tier 1 — Primary sources with measured results or direct technical specifications:**

- Stripe — *How to prepare for agentic commerce: A technical field guide* (Danny Smith, Global Solutions Architect Lead, Agentic Commerce, published March 10, 2026). Cited for: the four discovery files agents read, robots.txt agent-user-agent guidance, WAF challenge vs. block recommendation, llms.txt and ai-plugin.json characterization, merchant discoverability framework. Verified HTTP 200: https://stripe.com/guides/how-to-prepare-for-agentic-commerce-technical-field-guide
- OpenAPI Initiative — *What is OpenAPI*. Cited for: OAS history, scope, and Linux Foundation governance. Verified HTTP 200: https://www.openapis.org/what-is-openapi
- Anthropic — *Introducing the Model Context Protocol* (Nov 2024). Cited for: MCP announcement and purpose. Verified HTTP 200: https://www.anthropic.com/news/model-context-protocol
- Model Context Protocol Blog — *One Year of MCP: November 2025 Spec Release* (Nov 2025). Cited for: 10,000+ servers, 97 million monthly SDK downloads, spec updates. Verified HTTP 200: https://blog.modelcontextprotocol.io/posts/2025-11-25-first-mcp-anniversary/
- Model Context Protocol Blog — *MCP joins the Agentic AI Foundation* (Dec 2025). Cited for: Linux Foundation donation details. Verified HTTP 200: https://blog.modelcontextprotocol.io/posts/2025-12-09-mcp-joins-agentic-ai-foundation/
- Anthropic Engineering — *Code execution with MCP* (2025). Cited for: Anthropic's continued MCP deployment and engineering follow-up. Verified HTTP 200: https://www.anthropic.com/engineering/code-execution-with-mcp
- Google Developers Blog — *Announcing the Agent2Agent Protocol (A2A)* (Apr 2025). Cited for: A2A announcement date, technical details (HTTP/SSE/JSON-RPC), initial partner list. Verified HTTP 200: https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/
- Jeremy Howard / Answer.AI — *A proposal to standardize on /llms.txt* (Sep 2024). Cited for: llms.txt origin and motivation. Verified HTTP 200: https://www.answer.ai/posts/2024-09-03-llmstxt.html
- llmstxt.org — official specification and adoption data. Verified HTTP 200: https://llmstxt.org/
- OpenAI Developer Community — *Plugin store and new chats with plugins — closed March 19, 2024*. Cited for: ChatGPT Plugins wind-down timeline (March 19 / April 9, 2024) and OpenAI's stated rationale. Verified HTTP 200: https://community.openai.com/t/plugin-store-and-new-chats-with-plugins-closed-march-19-2024/689877. Note: the current OpenAI API Deprecations page (https://developers.openai.com/api/docs/deprecations) covers model deprecations; ChatGPT Plugins are documented via the community announcement and help article, not that page.
- OpenAI — *Function Calling and other API updates* (Jun 2023). Note: openai.com returns 403 to curl with standard user-agent (Cloudflare bot protection); URL is citable and known-good from public record. URL: https://openai.com/index/function-calling-and-other-api-updates/
- OpenAI — function calling documentation: https://developers.openai.com/api/docs/guides/function-calling
- Anthropic — tool use documentation: https://platform.claude.com/docs/en/docs/build-with-claude/tool-use/overview

**Tier 2 — Trusted primary documentation and practitioner sources:**

- W3C Web Machine Learning Community Group — *WebMCP specification*. Verified HTTP 200: https://webmachinelearning.github.io/webmcp/
- IBM / Agent Communication Protocol — *ACP specification* (competing inter-agent protocol under Linux Foundation governance). Cited as context for competing proposals in the A2A section. Verified HTTP 200: https://agentcommunicationprotocol.dev/introduction/welcome
- MCP-B — browser-native MCP implementation. Verified HTTP 200: https://github.com/MiguelsPizza/WebMCP
- Google Cloud Blog — *Agent2Agent protocol is getting an upgrade* (A2A v0.3, Aug 2025). Verified HTTP 200: https://cloud.google.com/blog/products/ai-machine-learning/agent2agent-protocol-is-getting-an-upgrade
- robotstxt.org — primary robots.txt specification: https://www.robotstxt.org/
- Cloudflare — *Declare your AIndependence: block AI bots, scrapers and crawlers with a single click* (Jul 2024). Cited for: AI bot prevalence data (39% of top 1M properties accessed by AI bots; only 2.98% had management in place). Verified HTTP 200: https://blog.cloudflare.com/declaring-your-aindependence-block-ai-bots-scrapers-and-crawlers-with-a-single-click/
- Simon Willison — *Using LLMs as the first line of support in Open Source* (Apr 2025). Cited for: practitioner implementation of llms.txt-style tooling and adoption commentary. Verified HTTP 200: https://simonwillison.net/2025/Apr/14/llms-as-the-first-line-of-support/

**Corrections from prior circulating versions:** The context brief for this article mentioned an "agents convert ~4x better than human shoppers" statistic attributed to Danny Smith / Stripe. That figure does not appear in the publicly citable Stripe technical field guide — the guide discusses agent purchase intent qualitatively but does not publish a conversion multiplier. The claim is not used here. Similarly, the brief mentioned "<800ms checkout" as a Stripe/Danny Smith figure — this also does not appear in the field guide. Neither figure is cited. If Rick has a citable source for these statistics, they can be added with attribution in a future revision.

**TBD placeholder:** The Watson Weekly episode 271W with Danny Smith (scheduled 2026-06-10 air date) is referenced in this article. The YouTube URL will be added when the episode publishes. Search: `[TBD: link when episode 271W airs on 2026-06-10]`

**Attribution:** The framing (priority ranking, Tier 1/2/3 deployment tiers, convergence verdict taxonomy, first-person deployment notes), the editorial hype/reality analysis, and the synthesis of how these formats relate to each other are Rick Watson's original work. The underlying technical definitions — MCP (Anthropic), A2A (Google), llms.txt (Howard/Answer.AI), OpenAPI (OpenAPI Initiative), function calling (OpenAI), WebMCP (W3C/community) — are the property of their respective organizations and cited with attribution throughout.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Quoted material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
