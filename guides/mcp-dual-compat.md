# Building One MCP Server That Works in Both Claude and ChatGPT

**Four design decisions that determine whether a remote MCP server connects from all four surfaces — or just one.**

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Cited material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR — what's in it for you

- One remote MCP server can serve Claude (claude.ai, Claude mobile, Claude Code) and OpenAI (ChatGPT apps, the Responses API) without branching your codebase.
- Four decisions drive whether it works: transport, session model, auth shape, and tool shape. Get them right up front and the rest is plumbing.
- Most "works in Claude but not ChatGPT" failures trace to a single root cause: the server requires a session ID that OpenAI's client never sends.
- The Claude side of this guide is live-tested on a deployed server. The OpenAI side is verified at the protocol and transport layer against OpenAI's documented requirements — not by clicking through the ChatGPT consumer UI. The article says so where it matters.

### Where to spend your time, in priority order

| # | Decision | Choose | Why it matters | Effort |
|---|---|---|---|---|
| 1 | Transport | Streamable HTTP (single `POST`/`GET` endpoint) | The old HTTP+SSE two-endpoint transport is deprecated in the MCP spec as of 2025-03-26; Streamable HTTP is the current standard. Both Claude and OpenAI support it. ([spec](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)) | 30 min |
| 2 | Session model | Stateless | OpenAI's MCP client re-initializes per call and sends no `Mcp-Session-Id`. A server that requires one breaks on OpenAI while working fine on Claude. | 15 min |
| 3 | Auth shape | Token in URL path (`/t/<secret>/mcp`) for widest consumer-app reach; OAuth 2.1 for published apps or per-user identity | The consumer UIs (claude.ai, ChatGPT) cannot send custom HTTP headers. `Authorization: Bearer` only reaches Claude Code and the Responses API directly. | 1–4 hrs |
| 4 | Tool shape | Arbitrary named tools | Works everywhere. The special `search` + `fetch` schema is only for ChatGPT's company-knowledge / deep-research feature, not ordinary tool-calling. | Negligible |

**Most readers should get #1 and #2 right and stop. Auth is the only decision that significantly branches based on your audience.**

---

## How to use this

The operational form of this guide is the Claude Code skill at [`skills/mcp-dual-compat/`](../skills/mcp-dual-compat/). Install it once:

```bash
# from a clone of this repo
mkdir -p ~/.claude/skills && cp -r skills/mcp-dual-compat ~/.claude/skills/
```

Then describe your MCP server — what it does, what transport it uses, what auth it requires — and say one of these:

> "Audit my MCP server for dual compatibility"
> "Why does my MCP server work in Claude but not ChatGPT?"
> "Apply the dual-compat checklist to my server"

Claude will load the skill and work through the four decisions against your specific setup. The article below is the reasoning; the skill is the how.

---

## 1. Transport: Streamable HTTP, not the old HTTP+SSE

The MCP spec defines two remote transports. The older one — **HTTP+SSE** (two separate endpoints: an SSE endpoint for server-to-client and a POST endpoint for client-to-server) — is deprecated as of spec version 2025-03-26 ([source](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports)). The current standard is **Streamable HTTP**: one endpoint that accepts both `POST` (client-to-server) and `GET` (server-to-client SSE stream), with the server choosing whether to return `application/json` or `text/event-stream` per response.

A clarification worth having: Streamable HTTP still *uses* SSE for streaming responses. What was deprecated is the two-endpoint design, not SSE as a streaming mechanism.

**Why this matters for dual compatibility:** Claude's Custom Connectors use Streamable HTTP natively. The OpenAI Responses API supports both Streamable HTTP and the old HTTP+SSE transport ([OpenAI docs](https://developers.openai.com/api/docs/guides/tools-connectors-mcp)). Building on Streamable HTTP satisfies both today and doesn't force a migration when clients drop the old transport.

With the official `mcp` Python SDK (FastMCP):

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server", stateless_http=True, json_response=True)
app = mcp.streamable_http_app()   # mount under your ASGI framework
```

---

## 2. Statelessness — the cross-platform gotcha most people hit

Claude is happy to open a session, exchange an `Mcp-Session-Id`, and reuse it. OpenAI's MCP client does not: it re-initializes per call and sends no session header between requests. If your server returns a session ID during `initialize` and then requires it on the next request, OpenAI calls fail while Claude works. This is the most common "works in Claude, not ChatGPT" bug.

Fix: run stateless (`stateless_http=True` above). Verify it the way OpenAI's client behaves — fire three independent requests with no session header and confirm each succeeds on its own:

```bash
EP="https://your-server.example.com/mcp"
H=(-H 'content-type: application/json' -H 'accept: application/json, text/event-stream')

curl -s "${H[@]}" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"probe","version":"1"}}}' "$EP"

curl -s "${H[@]}" -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' "$EP"

curl -s "${H[@]}" -d '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"your_tool","arguments":{}}}' "$EP"
```

A stateless server answers `tools/list` and `tools/call` even on separate connections with no session state. If request 2 or 3 fails with a "missing session" error, the server is not stateless.

---

## 3. Auth: pick the shape your clients can actually send

This is where most cross-platform plans fall apart. The consumer apps — claude.ai (web + mobile) and ChatGPT's connector UI — do not let you attach a custom HTTP header. So a standard `Authorization: Bearer <token>` header only reaches Claude Code and the OpenAI Responses API (which accepts it via a separate `authorization` parameter in the tool definition). It does not reach the consumer UIs.

Auth options, ranked by how many surfaces they reach:

| Scheme | Claude Code | claude.ai / mobile | ChatGPT consumer UI | Responses API |
|---|---|---|---|---|
| No auth (public server) | ✅ | ✅ | ✅ | ✅ |
| Secret in URL path (`/t/<secret>/mcp`) | ✅ | ✅ | ✅ (no-auth UI option + URL) | Undocumented; use `authorization` param instead |
| `Authorization: Bearer` header | ✅ | ❌ (no header field in UI) | ❌ | ✅ (via `authorization` param) |
| OAuth 2.1 + Dynamic Client Registration | ✅ | ✅ | ✅ | ✅ |

*Claude columns: live-tested on a deployed server. ChatGPT consumer UI column and Responses API column: verified against OpenAI's published documentation — not tested via a live ChatGPT UI click-through.*

**Practical guidance:**

- **Fastest path for human-clicks-a-URL reach (claude.ai + ChatGPT consumer UI):** put a long, random, per-user secret in the URL path (`/t/<secret>/mcp`), compare it in constant time, and return an identical 404 for bad-token / wrong-scope / unknown-path so there's no auth oracle. The Responses API has its own `authorization` parameter for programmatic access, so URL-secret serves the consumer UI audience while the Responses API uses its own channel.
- **Hosting caveat:** a secret in the URL appears in your host's request logs. On Cloud Run, add a log-sink exclusion for the service's request logs; your application code should never print the path directly. These were verified on a live Cloud Run deployment.
- **Step up to OAuth 2.1 + Dynamic Client Registration** when you need real per-user identity, you're publishing a ChatGPT app through OpenAI's review process, or the audience is larger than a handful of trusted people.

---

## 4. Tool shape: arbitrary tools work — with one exception

In Claude, ChatGPT Developer Mode, and the Responses API, your tools can be named anything with any JSON schema. The one exception: ChatGPT's **company-knowledge / deep-research** feature (previously called "connectors," renamed "apps" as of December 2025 ([OpenAI apps SDK](https://developers.openai.com/apps-sdk/concepts/mcp-server))) expects exactly two read-only tools — `search` and `fetch` — with a specific response schema. If you want to feed that specific feature, implement those two; for ordinary tool-calling you don't need them.

A token-economy note that helps on both platforms: keep the tool list small with terse descriptions, return snippet-first results with a `search` → `get` ladder, and cap output size. A smaller, sharper tool list means better tool selection and lower cost on every client.

---

## 5. Three host-level gotchas

These don't affect the protocol design but will burn hours if you hit them unprepared.

**DNS-rebinding protection 421s your cloud host.** The MCP Python SDK ships with a localhost-only Host allowlist by default. Behind a cloud platform's domain (Cloud Run, Railway, Fly), every request returns 421 ("Invalid Host header"). For a server already behind TLS and its own token auth, disable it:

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.transport_security import TransportSecuritySettings

mcp = FastMCP(
    "my-server",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(enable_dns_rebinding_protection=False),
)
```

**Serverless CPU throttling stalls background initialization.** If you clone a repo, build an index, or do any heavy init in a background task at startup, platforms that throttle CPU outside request handling (Cloud Run's default CPU allocation mode) will stall it. Either run initialization inside the first request path (bounded, returns one slow call on cold start rather than an error), or set CPU-always-allocated. Prefer the bounded-wait approach: one slow first call is a better failure mode than silently broken tools.

**Mount path redirects can leak the token.** If the framework issues a 307 redirect from `/mcp` to `/mcp/`, the `Location` header can expose the path without the token. Mount the path so it resolves without a redirect.

---

## 6. How to test — cheapest to most real

**Step 1 — MCP Inspector (protocol smoke test).** Anthropic's CLI confirms `initialize` and the tool list. No API key required:

```bash
npx @modelcontextprotocol/inspector
```

Connect to your URL, verify `initialize` succeeds and tools appear. ([docs](https://modelcontextprotocol.io/docs/tools/inspector))

**Step 2 — Stateless curl probe.** The three-request sequence from section 2. Proves the no-session path that OpenAI's client uses.

**Step 3 — OpenAI Responses API (authoritative OpenAI-side test).** Scriptable with an API key — no ChatGPT Plus needed. OpenAI's quickstart uses an unauthenticated public server; for a private server pass an `authorization` value:

```python
from openai import OpenAI

client = OpenAI()
r = client.responses.create(
    model="gpt-5.5",
    tools=[{
        "type": "mcp",
        "server_label": "my-server",
        "server_url": "https://your-server.example.com/mcp",
        "require_approval": "never",
        # "authorization": "Bearer <token>",  # add if your server requires it
    }],
    input="List the available tools and call one.",
)
print(r.output_text)
```

([OpenAI docs](https://developers.openai.com/api/docs/guides/tools-connectors-mcp))

**Step 4 — Claude Code.** The first consumer surface to add — quick feedback loop:

```bash
claude mcp add --transport http my-server https://your-server.example.com/mcp
```

Confirm "Connected" appears. Test a tool call.

**Step 5 — Consumer apps** (the only human-in-the-loop step). Add the URL as a custom connector in claude.ai (Settings → Connectors) and in ChatGPT (Settings → Connectors → Developer Mode → "No authentication"). Enable in a chat and call a tool.

If steps 1–4 pass, step 5 usually passes too. When it doesn't, it's typically the consumer UI's auth handling. The fix is OAuth, not transport.

---

## 7. What users installing this will actually see

Both consumer apps show a trust/permission dialog when you add a custom connector. This is client-side — you cannot suppress it from the server. ChatGPT Developer Mode is the most prominent: it gates custom connectors behind an explicit "this is powerful, only add servers you trust" warning ([OpenAI community](https://community.openai.com/t/mcp-server-tools-now-in-chatgpt-developer-mode/1357233)). claude.ai shows a single "make sure you trust this connector" confirmation.

Three things that reduce friction:

- **Name the server like a product.** The `serverInfo.name` you return surfaces in the consent UI. "Family Backlog" reads as a safe personal tool; `acme-internal-mcp-v2` reads as something suspicious. One string, real UX difference.
- **Have the technical owner do the one-time setup.** Clicking through the warnings on the user's account takes two minutes. After that the connector is just present — daily use is plain conversation, no dialogs.
- **OAuth replaces the generic warning with a first-party consent screen.** If you need a clean branded sign-in experience for a non-technical audience, OAuth 2.1 (and for ChatGPT, publishing through OpenAI's review process) is the only way to replace the "unverified connector" warning with something reassuring. More work — worth it only for a wide or non-technical audience.

---

## Sources & Attribution

All sources verified as live and accessible on 2026-06-10.

- **OpenAI — MCP and Connectors (Responses API):** https://developers.openai.com/api/docs/guides/tools-connectors-mcp
- **OpenAI — Building MCP servers (apps SDK):** https://developers.openai.com/apps-sdk/concepts/mcp-server
- **OpenAI — Remote MCP server guide (platform.openai.com redirect):** https://platform.openai.com/docs/guides/tools-remote-mcp (redirects to above)
- **ChatGPT Developer Mode announcement (OpenAI community):** https://community.openai.com/t/mcp-server-tools-now-in-chatgpt-developer-mode/1357233
- **MCP Specification — Transports (2025-03-26):** https://modelcontextprotocol.io/specification/2025-03-26/basic/transports
- **MCP Inspector docs:** https://modelcontextprotocol.io/docs/tools/inspector
- **DevOps.com — ChatGPT Developer Mode context:** https://devops.com/chatgpt-developer-mode-full-mcp-access-with-serious-responsibilities/

**Corrections from prior circulating versions:**

- *Model name:* Early drafts used `model="gpt-5"` in the Responses API example. OpenAI's current quickstart uses `gpt-5.5`. Corrected.
- *Protocol version string:* Early drafts used `"protocolVersion": "2025-06-18"` in curl examples. The current published MCP spec version is `2025-03-26`. Corrected.
- *Responses API + URL-secret:* Early drafts showed URL-embedded secrets as working with the Responses API. OpenAI's Responses API uses a separate `authorization` parameter for auth — it does not document URL-embedded secrets. Corrected in auth table and prose.
- *SSE deprecation framing:* "SSE is deprecated" is misleading. The *old HTTP+SSE two-endpoint transport* (spec version 2024-11-05) is deprecated. Streamable HTTP still uses SSE for streaming. Clarified throughout.
- *OpenAI SSE support:* Early drafts implied the Responses API only works with Streamable HTTP. OpenAI documents support for both Streamable HTTP and old HTTP+SSE. Streamable HTTP remains the forward-looking choice for new builds; the absolute claim was softened.

---

> © 2026 Rick Watson / RMW Commerce Consulting. All rights reserved on original commentary. Cited material is the property of its respective owners and used under fair use with attribution — see [Sources & Attribution](#sources--attribution). Republishing in whole or in substantial part requires written permission: rick@rmwcommerce.com.
