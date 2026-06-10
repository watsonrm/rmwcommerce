# SKILL: MCP Dual-Compat Audit

**Trigger phrases:**
- "Audit my MCP server for dual compatibility"
- "Why does my MCP server work in Claude but not ChatGPT?"
- "Apply the dual-compat checklist to my server"
- "MCP dual-compat"
- "Check my MCP server for cross-platform issues"

**What this skill does:** Works through the four design decisions that determine whether a remote MCP server connects from Claude (claude.ai, Claude Code, mobile) AND OpenAI (ChatGPT apps, Responses API). Asks targeted questions, diagnoses the likely root cause, and prescribes the minimal fix.

---

## Procedure

### Step 0 — Gather context

Ask the user for:
1. How the server is deployed (Cloud Run, Railway, Fly, local, other)
2. What transport it uses (Streamable HTTP / old HTTP+SSE / stdio)
3. What auth it uses (no auth / Bearer header / URL-secret / OAuth)
4. Whether it uses sessions (`stateless_http=True` or not)
5. What surfaces they've tested (Claude Code / claude.ai / ChatGPT / Responses API)
6. What error or behavior they're seeing on the failing surface

If the user pastes code or a config, read it directly.

### Step 1 — Run the four-decision checklist

For each decision, state PASS / FAIL / UNKNOWN and explain why:

**Decision 1: Transport**
- PASS: Server uses Streamable HTTP (single endpoint, accepts both POST and GET)
- FAIL: Server uses old HTTP+SSE (two-endpoint design from spec 2024-11-05) — deprecated in MCP spec 2025-03-26
- FIX: `mcp = FastMCP("name", stateless_http=True); app = mcp.streamable_http_app()`

**Decision 2: Session model**
- PASS: Server runs stateless (`stateless_http=True`)
- FAIL: Server assigns and requires `Mcp-Session-Id` — OpenAI's client sends no session header, so every call after initialize fails
- FIX: Set `stateless_http=True`. Verify with three independent curl calls (no session header) — all three must succeed.
- TEST: `curl -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' -H 'content-type: application/json' -H 'accept: application/json, text/event-stream' https://your-server.example.com/mcp` — must return tool list with no prior initialize

**Decision 3: Auth shape**
- PASS for widest reach: URL-path secret (`/t/<secret>/mcp`) or no auth
- PARTIAL: Bearer header — works for Claude Code + Responses API, not claude.ai or ChatGPT consumer UI
- FAIL for consumer apps: any scheme that requires a custom request header
- FIX if consumer UI is needed: move auth to URL path or OAuth 2.1
- NOTE: Responses API uses a separate `authorization` parameter, not a URL-embedded secret

**Decision 4: Tool shape**
- PASS: Arbitrary named tools
- ONLY NEEDED: `search` + `fetch` tools with specific schema if targeting ChatGPT company-knowledge / deep-research feature
- No action needed for ordinary tool-calling

### Step 2 — Host-level gotchas check

Ask or infer:
- **421 errors from cloud host?** → DNS-rebinding protection is on. Fix: `TransportSecuritySettings(enable_dns_rebinding_protection=False)` (safe if behind TLS + own auth)
- **First cold-start call fails/times out?** → Background init is being throttled. Fix: move init inside first request path with a bounded wait, or use CPU-always-allocated
- **Redirect at mount path?** → Check for 307 `/mcp` → `/mcp/` redirect leaking auth path. Fix: mount so path resolves directly
- **User says it works in text chat but not in voice?** → This is expected: Claude voice mode does not discover or call any MCP connectors — custom servers and built-in connectors alike. Anthropic closed the tracking issue as "not planned" (anthropics/claude-ai-mcp #146). The fix is to tell users the server is text-chat only; there is no server-side workaround.

### Step 3 — Prescribe one fix

Identify the highest-priority failing decision (1 > 2 > 3 > 4 in priority order) and give the exact code change or config change. Show the before/after.

### Step 4 — Provide the test ladder

Give the user the three-step verification sequence:
1. Stateless curl probe (three independent requests, no session header — section 2 of the guide)
2. OpenAI Responses API call with `gpt-5.5` and `require_approval: "never"`
3. Claude Code `mcp add --transport http` confirmation

Tell them: if steps 1 and 2 pass, the server is protocol-correct for both platforms. Step 3 (consumer app UI) is the only human-in-the-loop test.

### Step 5 — Check your work

Before finishing:
- Confirm the user's described server state against each decision
- If you diagnosed a session issue, verify the fix actually results in stateless behavior (can they run the curl probe successfully?)
- If you recommended URL-secret auth, confirm they know to exclude the path from request logs
- Surface any remaining unknowns explicitly — don't leave the user with open questions unaddressed

---

## Reference: key numbers and versions

- Current MCP spec version: `2025-03-26`
- protocolVersion string for curl/initialize: `"2025-03-26"`
- OpenAI Responses API model (quickstart): `gpt-5.5`
- Old HTTP+SSE transport spec: `2024-11-05` (deprecated)

## Reference: full guide

[Building One MCP Server That Works in Both Claude and ChatGPT](../../guides/mcp-dual-compat.md) — the reasoning, citations, and full correction history behind this skill.
