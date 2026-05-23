# Making Claude Respond Faster

**A practical guide to reducing Claude latency and verbosity — covering prompt caching, model selection, parallel tool calls, and the patterns that slow you down.**

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's official Claude API and Claude Code documentation — see [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

## TL;DR

If you use Claude in production — via the API, Claude Code, or claude.ai — the patterns here will:

- Eliminate repeated full-context reprocessing through prompt caching. Cache reads cost 0.1× standard input rate and start streaming sooner ([source](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching))
- Cut multi-step workflows by issuing independent tool calls in one turn instead of one-at-a-time ([source](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/parallel-tool-use))
- Match the model to the task. Haiku is labeled "Fastest," Sonnet "Fast," Opus "Moderate" ([source](https://docs.anthropic.com/en/docs/about-claude/models/overview))
- Skip extended thinking on routine work. It is off by default for a reason

### Where to spend your time, in priority order

Most readers should act on the first two and stop. They handle the largest share of wasted wall-clock time.

| # | Lever | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| 1 | **Prompt caching** — put stable context before dynamic content, mark it with `cache_control` | Cache hits bill at 0.1× input; cache misses reprocess the entire prefix. Repeated workloads recover the write premium quickly | 1–2 hrs one-time refactor |
| 2 | **Right model for the task** — Haiku for mechanical work, Sonnet for daily driver, Opus only for hard reasoning | Anthropic's own latency labels: Haiku 4.5 "Fastest," Sonnet 4.6 "Fast," Opus 4.7 "Moderate." Pricing scales the same way | Per-task discipline |
| 3 | **Parallel tool calls** — multiple `tool_use` blocks in one turn, all `tool_result` blocks in one user message | Sequential calls are wall-clock-additive. Three reads, one round-trip | One prompt addition |
| 4 | **Skip extended thinking on simple work** — leave it off (the default) unless the task is genuinely multi-step reasoning | Thinking tokens are billed; routine queries get no quality lift from thinking | API flag |
| 5 | **Stream responses** — render tokens as they arrive | Perceived latency falls immediately; total compute is unchanged | SDK flag |
| 6 | **Trim context payload** — use `/compact` at task breaks, scope CLAUDE.md to under 200 lines | Larger context slows time-to-first-token | Ongoing discipline |

---

## How to use this

Feed the relevant sections to Claude with this prompt to get a self-audit:

> I'm trying to reduce Claude response latency in my setup. Here is a guide on the main levers: [paste guide]. Review how I'm currently using Claude — [describe your setup: API, Claude Code, tool count, typical prompts] — and tell me which of these I'm not using, starting with the highest-impact one.

---

## Section 1: Prompt caching — the biggest lever you're probably not using

### The problem

Every API call, by default, reprocesses every token you send. If your system prompt is 5,000 tokens and you send 50 requests per session, that's 250,000 tokens of overhead before your actual questions even reach the model. On call-heavy workloads, that overhead is the majority of your bill and a meaningful share of your wait time.

### The fix

Prompt caching lets the API skip reprocessing content it has already seen. You mark stable sections with `cache_control`. The API stores them server-side. Subsequent calls that share the same prefix read from cache instead of reprocessing.

### The pricing (Claude Sonnet 4.6)

| Token type | Cost per million tokens | Multiplier |
| :--- | :--- | :--- |
| Standard input | $3.00 | 1× |
| Cache write (5-minute TTL) | $3.75 | 1.25× |
| Cache write (1-hour TTL) | $6.00 | 2× |
| Cache hit / refresh | $0.30 | 0.1× |

The write is slightly more expensive than standard. On any repeated workload, the math favors caching quickly. ([source: pricing multipliers](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching))

### The rules

- **Minimum tokens to cache.** Claude Sonnet 4.6 and Sonnet 4.5 cache from 1,024 tokens. Claude Opus 4.7, 4.6, and 4.5 require 4,096 tokens. Claude Haiku 4.5 also requires 4,096 tokens. Shorter prompts are processed without caching — no error is returned.
- **TTL options.** 5 minutes (default) or 1 hour (at the higher write rate above). From the docs: "The cache is refreshed for no additional cost each time the cached content is used." Continuous work stays warm; the 1-hour TTL matters for workloads with gaps between calls.
- **Prefix-matched, exact match.** Anything that changes before your `cache_control` breakpoint invalidates the cache for everything after it. Stable content (system prompt, tool definitions, reference documents) goes before dynamic content (the user's question).
- **Parallel requests don't share the first cache write.** The cache entry becomes available only after the first response begins. For fleet workloads, warm the cache with one serial request before fanning out.

### What goes in the cache

- **Cache:** system prompts, tool definitions, reference documents, long few-shot example blocks, code files you read repeatedly. These change rarely.
- **Don't cache:** the user's current message, dynamic state, turn-specific tool results. Caching them provides no benefit.

### Concrete API example

```json
{
  "model": "claude-sonnet-4-6",
  "system": [
    {
      "type": "text",
      "text": "You are a commerce data analyst...",
      "cache_control": {"type": "ephemeral"}
    },
    {
      "type": "text",
      "text": "[5,000-token product catalog reference document here]",
      "cache_control": {"type": "ephemeral"}
    }
  ],
  "messages": [
    {"role": "user", "content": "Which SKUs had the highest return rate last month?"}
  ]
}
```

The catalog is cached. Every subsequent question about the catalog reads from cache at $0.30 per million tokens instead of $3.00, and starts responding sooner.

### In Claude Code

Claude Code manages prompt caching automatically. The system prompt, tool definitions, and project context (CLAUDE.md) sit in the stable prefix; your messages append at the end. What kills the cache in Claude Code ([source](https://docs.claude.com/en/docs/claude-code/prompt-caching)):

- **Switching models mid-session** — each model has its own cache; a switch starts cold
- **Connecting or disconnecting an MCP server** — tool definitions are in the system prompt layer
- **Running `/compact`** — replaces message history with a summary, rebuilding the prefix
- **Upgrading Claude Code** — new version typically changes the system prompt

Practical takeaway: pick your model and connect MCP servers at the top of a session, then save `/compact` for natural breaks between tasks.

### Note on subagents

Each subagent starts its own conversation with no cache hits on its first call. Subagents build their own cache across their turns, separate from the parent. Don't spawn a subagent to read two files — that cold-starts a fresh context for a task that doesn't warrant it.

---

## Section 2: Model selection — the simplest latency lever

### The facts

Anthropic's models overview labels comparative latency as follows ([source](https://docs.anthropic.com/en/docs/about-claude/models/overview)):

| Model | Comparative latency | Pricing (input / output per MTok) |
| :--- | :--- | :--- |
| Claude Haiku 4.5 | **Fastest** | $1 / $5 |
| Claude Sonnet 4.6 | **Fast** | $3 / $15 |
| Claude Opus 4.7 | **Moderate** | $5 / $25 |

From the same page, verbatim: Haiku 4.5 is "the fastest model with near-frontier intelligence"; Sonnet 4.6 is "the best combination of speed and intelligence"; Opus 4.7 is "our most capable generally available model for complex reasoning and agentic coding."

### The discipline

- **Default to Haiku for:** file reads, reformatting data, simple lookups, yes/no checks, search-and-replace refactors.
- **Default to Sonnet for:** multi-file code generation, code review, business logic, most day-to-day API work.
- **Reach for Opus only for:** complex reasoning, hard architecture decisions, agentic coding, problems where you've already tried Sonnet and it fell short.

In Claude Code: use `/model haiku` or `/model sonnet` to switch mid-session. Cost: one cache-busting turn (see Section 1) — worth it if the task genuinely fits a faster model.

### The `effort` parameter

On Claude Opus 4.7 (and other models that support [adaptive thinking](https://docs.anthropic.com/en/docs/build-with-claude/adaptive-thinking)), the Messages API exposes an `effort` parameter inside `output_config` with values `low`, `medium`, `high`, `xhigh`, and `max`. Lower effort trades depth for speed. ([source: Messages API reference](https://docs.anthropic.com/en/api/messages))

---

## Section 3: Parallel tool calls — stop paying sequential overhead

### The problem

By default, when Claude needs data from multiple sources, the natural pattern is one tool, wait for result, next tool. If you ask "summarize these three files," that's three full round-trips where one should suffice.

### The mechanism

Claude supports multiple `tool_use` blocks in a single assistant response. From the docs, verbatim: "Tool calls in a single assistant turn are unordered. You can run them concurrently (`Promise.all`, `asyncio.gather`), sequentially, or in any order." ([source](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/parallel-tool-use))

### Getting Claude to use it

Claude 4 models support parallel tool use by default. If you're not seeing it, add this to your system prompt (Anthropic's own recommendation):

```text
For maximum efficiency, whenever you need to perform multiple independent
operations, invoke all relevant tools simultaneously rather than sequentially.
```

For stronger parallelism (also from Anthropic's docs):

```text
<use_parallel_tool_calls>
For maximum efficiency, whenever you perform multiple independent operations,
invoke all relevant tools simultaneously rather than sequentially. Prioritize
calling tools in parallel whenever possible. For example, when reading 3 files,
run 3 tool calls in parallel to read all 3 files into context at the same time.
When running multiple read-only commands like ls or list_dir, always run all
of the commands in parallel. Err on the side of maximizing parallel tool calls
rather than running too many tools sequentially.
</use_parallel_tool_calls>
```

### The critical formatting rule

Return all tool results in a **single** user message. Sending them in separate messages teaches Claude that sequential calls are normal — and parallel behavior degrades.

```json
// Wrong — separate messages, breaks parallel behavior
[
  {"role": "assistant", "content": [tool_use_1, tool_use_2]},
  {"role": "user", "content": [tool_result_1]},
  {"role": "user", "content": [tool_result_2]}
]

// Correct — all results in one message
[
  {"role": "assistant", "content": [tool_use_1, tool_use_2]},
  {"role": "user", "content": [tool_result_1, tool_result_2]}
]
```

### Verify it's working

```python
# Average tool calls per tool-calling message should be > 1.0
tool_call_messages = [
    m for m in messages
    if any(b.type == "tool_use" for b in m.content)
]
total = sum(
    len([b for b in m.content if b.type == "tool_use"])
    for m in tool_call_messages
)
avg = total / len(tool_call_messages) if tool_call_messages else 0.0
print(f"Avg tools per message: {avg}")  # target > 1.0
```

### Dependencies between batched calls

If Claude batches two calls that turn out to depend on each other, return `is_error: true` in the failing `tool_result` with the natural error message. Claude reissues the call after the prerequisite completes. Don't switch to sequential execution to avoid this — that adds latency on every call.

---

## Section 4: Extended thinking — leave it off for routine work

### The facts

Extended thinking is **off by default**. You opt in by setting `thinking: {type: "enabled", budget_tokens: N}` on the Messages API. The `budget_tokens` parameter sets the maximum tokens Claude can allocate to internal reasoning. ([source](https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking))

### When to use it

Extended thinking improves output quality on:

- Multi-step math or formal logic
- Complex code architecture decisions
- Tasks where the reasoning chain is as valuable as the answer

### When to skip it

- Summarization
- Data extraction
- Reformatting
- File reads
- Single-fact lookups
- Generating boilerplate

Thinking tokens are billed even when not displayed. On routine work, you pay for reasoning that doesn't improve the answer.

### Faster perceived latency when you do use it

Setting `display: "omitted"` in the thinking config makes the server skip streaming thinking tokens entirely. From the docs, verbatim: "The primary benefit is faster time-to-first-text-token when streaming: The server skips streaming thinking tokens entirely and delivers only the signature, so the final text response begins streaming sooner."

Note: this reduces perceived latency, not cost. You're still billed for the full thinking tokens generated.

### Opus 4.7 — adaptive thinking only

As of Claude Opus 4.7, manual extended thinking is **no longer supported**. From the docs, verbatim: "Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is no longer supported on Claude Opus 4.7 and returns a 400 error."

The replacement is **adaptive thinking** with the `effort` parameter (see Section 2). The `budget_tokens` parameter is also deprecated on Claude Sonnet 4.6 and Claude Opus 4.6 and will be removed in a future model release.

If you're using Claude Code and want to eliminate thinking overhead on routine queries, prompt explicitly: "Respond directly. No internal reasoning before the answer."

---

## Section 5: Streaming — fix perceived latency immediately

### The problem

Without streaming enabled, your application waits for the entire response to complete before rendering anything. For a 500-token response at typical output speeds, that's seconds of blank screen before the first word.

### The fix

Streaming delivers tokens as they're generated. Anthropic's SDKs expose it via the `stream` parameter. This is a one-line change in most setups and has no downside for interactive applications.

```python
# Python SDK
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "..."}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

Streaming does not reduce total tokens generated or model compute time. It reduces the gap between "request sent" and "first word on screen." For users, that gap is the experience.

---

## Section 6: Context size discipline — don't pay for what you're not using

### The problem

Time-to-first-token scales with context size. A 200,000-token context takes longer to process than a 10,000-token context, all else equal. Dumping an entire codebase for a question that only needs two files is latency and cost overhead with no quality gain.

### The rules

**Trim conversation history at natural breaks.** In Claude Code, `/compact` summarizes and replaces history. Use it between tasks, not as an emergency measure when context is full. Compacting mid-task adds overhead; compacting at a break is efficient.

**Send only what the task needs.** In API calls, extract the relevant section of a reference document rather than sending the whole thing.

**CLAUDE.md size discipline.** The Claude Code memory docs say, verbatim: "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." Path-scoped rules (`.claude/rules/`) load only when matching files are accessed — use them instead of bloating the global file. ([source](https://docs.claude.com/en/docs/claude-code/memory))

**Subagents for isolated, large reads.** A subagent in its own context keeps your main session compact. Worth it for genuinely large reads. Not worth it for two-file lookups where a direct call is faster — see Section 1's note on cold-start cost.

---

## Section 7: Batch API — for async workloads only

If you're processing large volumes of non-interactive requests — content moderation at scale, dataset analysis, bulk evaluations — the Message Batches API processes them asynchronously at 50% lower cost. Most batches finish in under an hour. ([source](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing))

This is not a latency optimization for interactive use. The Batch API has no SLA on turnaround. Use it only when immediate responses aren't required and cost efficiency matters more than speed.

---

## Anti-patterns — what slows you down

**Spawning a subagent to read two files.** Subagents start with a cold cache. Use direct tool calls for small, bounded reads. Reserve subagents for genuinely isolated work or large reads that would otherwise bloat your main context.

**Switching models mid-session in Claude Code.** Each switch is a cache miss on the full context. Decide your model at session start.

**Enabling extended thinking by default.** It's a cost and latency penalty on anything that doesn't require multi-step reasoning. Leave it off; opt in per call.

**Sending tool results in separate user messages.** Breaks parallel tool behavior. Claude reverts to sequential calls.

**Putting dynamic content before stable content.** Cache is prefix-matched. If the user's question precedes your system prompt or reference document, nothing caches downstream.

**Asking for long explanations when you want a short answer.** Claude calibrates response length to perceived task complexity. If you want shorter output, say so explicitly: "Result only. No explanation."

**Bloating CLAUDE.md.** The official guidance is under 200 lines. Larger files reduce adherence and consume context on every session.

---

## Sources & Attribution

All technical claims in this guide are backed by primary Anthropic documentation. No third-party benchmarks are cited for model speed comparisons — only Anthropic's own qualitative labels ("Fastest," "Fast," "Moderate") from the models overview page, since third-party benchmark figures change frequently and can reflect infrastructure differences rather than model capability.

| Source | URL | What it backs |
| :--- | :--- | :--- |
| Prompt Caching | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching | Cache TTL (5-min default, 1-hour option), pricing multipliers (1.25× / 2× / 0.1×), minimum tokens by model, prefix-match mechanics |
| Models Overview | https://docs.anthropic.com/en/docs/about-claude/models/overview | Comparative latency labels (Haiku "Fastest," Sonnet "Fast," Opus "Moderate"), pricing per million tokens, model capabilities |
| Parallel Tool Use | https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/parallel-tool-use | Multiple `tool_use` blocks per response, unordered execution, single-message rule for tool results, recommended system prompt patterns |
| Extended Thinking | https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking | `budget_tokens` parameter, `display: "omitted"` faster TTFT, Opus 4.7 manual thinking deprecation, Sonnet 4.6 / Opus 4.6 budget_tokens deprecation |
| Adaptive Thinking | https://docs.anthropic.com/en/docs/build-with-claude/adaptive-thinking | Adaptive thinking model behavior on Opus 4.7 |
| Messages API | https://docs.anthropic.com/en/api/messages | `effort` parameter (low / medium / high / xhigh / max) at `output_config.effort`, full parameter surface |
| Message Batches API | https://docs.anthropic.com/en/docs/build-with-claude/batch-processing | 50% cost reduction, async processing, sub-1-hour typical turnaround |
| Claude Code: Prompt Caching | https://docs.claude.com/en/docs/claude-code/prompt-caching | Cache invalidation triggers in Claude Code, subagent cache isolation |
| Claude Code: Memory (CLAUDE.md) | https://docs.claude.com/en/docs/claude-code/memory | 200-line guidance for CLAUDE.md, path-scoped rules, MEMORY.md 200-line / 25KB limit |

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's official Claude API and Claude Code documentation — see [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.
