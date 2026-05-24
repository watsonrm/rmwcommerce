# Making Claude Respond Faster

**A practical, evidence-backed guide to reducing Claude latency and verbosity — covering prompt caching, model selection, parallel tool calls, and the patterns that slow you down. Every claim cited to primary documentation, Anthropic engineering writing, named practitioners, peer-reviewed research, or cross-vendor confirmation.**

*By [Rick Watson](https://rmwcommerce.com) · 2026-05-22*

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's official Claude API and Claude Code documentation, supplemented by Anthropic engineering writing and the independent practitioner and research voices listed in [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.

---

> *"Every command has a cost, so be smart and efficient. Aim to complete tasks in the least number of steps."*
>
> — Lilian Weng (then OpenAI Head of Applied Research), "[LLM Powered Autonomous Agents](https://lilianweng.github.io/posts/2023-06-23-agent/)" (Jun 23, 2023)

---

## TL;DR

If you use Claude in production — via the API, Claude Code, or claude.ai — the patterns below will measurably reduce wall-clock time and cost. The article cites every load-bearing number and quote so you can audit it yourself.

Before the levers, the honest framing — from Anthropic's own engineering team:

> *"Agentic systems often trade latency and cost for better task performance."*
>
> — Anthropic, "[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)" (Dec 19, 2024)

Speed is not always the goal. But when it is the constraint, here are the levers, in priority order.

### Where to spend your time

Most readers should act on the first two and stop. They handle the largest share of wasted wall-clock time.

| # | Lever | Why it matters | Effort |
| :-- | :--- | :--- | :--- |
| 1 | **Prompt caching** — put stable context before dynamic content, mark it with `cache_control` | Cache hits bill at 0.1× input; cache misses reprocess the entire prefix. Repeated workloads recover the write premium quickly. Skip if traffic <1 call per 5 min (negative ROI from cache writes) | 1–2 hrs one-time refactor |
| 2 | **Right model for the task** — Haiku for mechanical work, Sonnet for daily driver, Opus only for hard reasoning | Anthropic's own latency labels: Haiku 4.5 "Fastest," Sonnet 4.6 "Fast," Opus 4.7 "Moderate." Pricing scales the same way | Per-task discipline |
| 3 | **Parallel tool calls** — multiple `tool_use` blocks in one turn, all `tool_result` blocks in one user message | Anthropic engineering reports parallel-tool + subagent parallelism "cut research time by up to 90% for complex queries" on their internal research system | One prompt addition |
| 4 | **Skip extended thinking on simple work** — leave it off (the default) unless the task is genuinely multi-step reasoning | Thinking tokens are billed; routine queries get no quality lift from thinking | API flag |
| 5 | **Stream responses** — render tokens as they arrive | Perceived latency falls immediately; total compute is unchanged | SDK flag |
| 6 | **Trim context payload** — use `/compact` at task breaks, scope CLAUDE.md to under 200 lines | Larger context slows time-to-first-token | Ongoing discipline |

---

## How to use this

Feed the relevant sections to Claude with this prompt to get a self-audit:

> I'm trying to reduce Claude response latency in my setup. Here is a guide on the main levers: [paste guide]. Review how I'm currently using Claude — [describe your setup: API, Claude Code, tool count, typical prompts] — and tell me which of these I'm not using, starting with the highest-impact one.

---

## Why these levers work — the systems foundation

Before the practical lever-by-lever guidance, a short grounding in *why* these techniques deliver the gains they do. If you already know the mechanism, skip to [Section 1](#section-1-prompt-caching--the-biggest-lever-youre-probably-not-using).

### The KV-cache and quadratic attention

Every token an LLM produces requires attending to every token before it. Naïvely, the cost of generating the N-th token scales linearly with N (the cost of the full response is therefore quadratic). The **KV-cache** stores the key and value tensors from previously processed tokens so they don't need to be recomputed — but a naïve implementation reserves contiguous memory per request, wasting most of it.

The vLLM project (Kwon et al., UC Berkeley) measured this:

> *"Existing systems suffer from internal and external memory fragmentation. ... they waste 60% – 80% of memory."*
>
> — Kwon et al., "[Efficient Memory Management for Large Language Model Serving with PagedAttention](https://arxiv.org/abs/2309.06180)" (arXiv:2309.06180, Sep 12, 2023)

Their **PagedAttention** mechanism (the foundation of vLLM, which powers a substantial share of open-source LLM serving) cuts waste to under 4% and improves throughput **14–24× over HuggingFace Transformers** on single-output requests, and **2–4× over FasterTransformer / Orca** at the same latency ([vLLM blog, Jun 20, 2023](https://vllm.ai/blog/2023-06-20-vllm); [paper, Sep 12, 2023](https://arxiv.org/abs/2309.06180)).

You don't need to understand PagedAttention to use Claude faster. You do need to understand the consequence: **the more an LLM serving stack can amortize KV-cache work across requests, the faster and cheaper everything gets.** Prompt caching is the user-facing API that exposes this benefit.

### Why caching shifts the cost curve

Eugene Yan, an applied-ML practitioner widely cited in production-LLM literature, frames the user-facing effect in one sentence:

> *"By serving from a cache, we shift the latency from generation (typically seconds) to cache lookup (milliseconds)."*
>
> — Eugene Yan, "[Patterns for Building LLM-based Systems & Products](https://eugeneyan.com/writing/llm-patterns/)"

This is the underlying principle for the rest of the article. Every speed lever below is a mechanism for shifting work from expensive paths (full generation, full-context reprocessing, sequential round-trips) to cheap paths (cache hits, parallel execution, smaller models).

---

## Section 1: Prompt caching — the biggest lever you're probably not using

### The problem

Every API call, by default, reprocesses every token you send. If your system prompt is 5,000 tokens and you send 50 requests per session, that's 250,000 tokens of overhead before your actual questions reach the model. On call-heavy workloads, that overhead is the majority of your bill and a meaningful share of your wait time.

### The fix

Prompt caching lets the API skip reprocessing content it has already seen. You mark stable sections with `cache_control`. The API stores them server-side. Subsequent calls that share the same prefix read from cache instead of reprocessing ([Anthropic prompt caching docs](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching)).

### The pricing (Claude Sonnet 4.6)

| Token type | Cost per million tokens | Multiplier |
| :--- | :--- | :--- |
| Standard input | $3.00 | 1× |
| Cache write (5-minute TTL) | $3.75 | 1.25× |
| Cache write (1-hour TTL) | $6.00 | 2× |
| Cache hit / refresh | $0.30 | 0.1× |

The write is slightly more expensive than standard. On any repeated workload, the math favors caching quickly. ([source: pricing multipliers](https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching))

Simon Willison — likely the most-cited independent voice on practical LLM patterns — confirmed the cost shape at launch:

> *"Cached tokens are charged at a significant discount: ~10% of the cost of sending those uncached tokens. ... The cache TTL is reset every time it gets a cache hit, so any application running more than one prompt every five minutes should see significant price decreases from this."*
>
> — Simon Willison, "[Prompt caching with Claude](https://simonwillison.net/2024/Aug/14/prompt-caching-with-claude/)" (Aug 14, 2024)

### The caveat Anthropic's docs don't surface

Willison also flagged a constraint the official docs gloss over:

> *"Apps prompting less frequently than once per five minutes will see negative ROI since cache writing costs exceed retrieval savings."*

If your workload is sporadic (one user query every 10 minutes, say), turning on caching can *cost* you money. The pattern is built for repeated, bursty workloads — interactive sessions, batch processing, RAG pipelines hitting the same reference document. Stop and check your traffic pattern before enabling caching app-wide.

### This is not Anthropic-specific

Prompt caching is now industry-standard. Cross-vendor confirmation:

| Vendor | Cache hit discount | Minimum tokens | Default TTL |
| :--- | :--- | :--- | :--- |
| Anthropic (Claude Sonnet 4.6) | 90% off (0.1× base) | 1,024 | 5 min (1 hr opt-in) |
| Google ([Gemini context caching](https://ai.google.dev/gemini-api/docs/caching)) | 75% off | 1,024 (Flash) / 4,096 (Pro) | 1 hr (configurable) |
| DeepSeek (per Willison) | Up to ~90% off | — | — |

The pattern works because the underlying KV-cache mechanism is universal. If you're building production LLM applications, learning the caching mental model pays off across vendors.

### The rules (Anthropic-specific)

- **Minimum tokens to cache.** Claude Sonnet 4.6 and Sonnet 4.5 cache from 1,024 tokens. Claude Opus 4.7, 4.6, and 4.5 require 4,096 tokens. Claude Haiku 4.5 also requires 4,096 tokens. Shorter prompts are processed without caching — no error is returned.
- **TTL options.** 5 minutes (default) or 1 hour (at the higher write rate above). From the docs, verbatim: *"The cache is refreshed for no additional cost each time the cached content is used."* Continuous work stays warm; the 1-hour TTL matters for workloads with gaps between calls.
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

*Applies to API-level builds; in Claude Code the runtime handles this for you.*

Each subagent starts its own conversation with no cache hits on its first call. Subagents build their own cache across their turns, separate from the parent. Don't spawn a subagent to read two files — that cold-starts a fresh context for a task that doesn't warrant it. Reserve subagents for either (a) genuinely isolated work that would bloat your main context, or (b) parallelism you can't get from a single agent (see Section 3).

---

## Section 2: Model selection — the simplest latency lever

### The facts

Anthropic's models overview labels comparative latency as follows ([source](https://docs.anthropic.com/en/docs/about-claude/models/overview)):

| Model | Comparative latency | Pricing (input / output per MTok) |
| :--- | :--- | :--- |
| Claude Haiku 4.5 | **Fastest** | $1 / $5 |
| Claude Sonnet 4.6 | **Fast** | $3 / $15 |
| Claude Opus 4.7 | **Moderate** | $5 / $25 |

From the same page, verbatim: Haiku 4.5 is *"the fastest model with near-frontier intelligence"*; Sonnet 4.6 is *"the best combination of speed and intelligence"*; Opus 4.7 is *"our most capable generally available model for complex reasoning and agentic coding."*

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

Claude supports multiple `tool_use` blocks in a single assistant response. From the docs, verbatim:

> *"Tool calls in a single assistant turn are unordered. You can run them concurrently (`Promise.all`, `asyncio.gather`), sequentially, or in any order."*
>
> — Anthropic, "[Parallel tool use](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/parallel-tool-use)"

### What this actually buys you

Anthropic's engineering team measured the wall-clock impact on their internal research system, which uses parallelism aggressively at two layers (subagent fan-out and parallel tool calls):

> *"These changes cut research time by up to 90% for complex queries, allowing Research to do more work in minutes instead of hours."*
>
> — Anthropic, "[How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)" (Jun 13, 2025)

That's a 10× wall-clock speedup on a real production workload, attributable to parallelism. The exact number won't transfer to your application — but the order of magnitude indicates how badly sequential execution under-performs on multi-step tasks.

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

Setting `display: "omitted"` in the thinking config makes the server skip streaming thinking tokens entirely. From the docs, verbatim: *"The primary benefit is faster time-to-first-text-token when streaming: The server skips streaming thinking tokens entirely and delivers only the signature, so the final text response begins streaming sooner."*

Note: this reduces perceived latency, not cost. You're still billed for the full thinking tokens generated.

### Opus 4.7 — adaptive thinking only

As of Claude Opus 4.7, manual extended thinking is **no longer supported**. From the docs, verbatim: *"Manual extended thinking (`thinking: {type: "enabled", budget_tokens: N}`) is no longer supported on Claude Opus 4.7 and returns a 400 error."*

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

**CLAUDE.md size discipline.** The Claude Code memory docs say, verbatim: *"target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence."* Path-scoped rules (`.claude/rules/`) load only when matching files are accessed — use them instead of bloating the global file. ([source](https://docs.claude.com/en/docs/claude-code/memory))

**Subagents for isolated, large reads.** A subagent in its own context keeps your main session compact. Worth it for genuinely large reads. Not worth it for two-file lookups where a direct call is faster — see Section 1's note on cold-start cost.

Anthropic's engineering team framed subagent context isolation this way:

> *"subagents facilitate compression by operating in parallel with their own context windows, exploring different aspects of the question simultaneously before condensing the most important tokens."*
>
> — Anthropic, "[How we built our multi-agent research system](https://www.anthropic.com/engineering/built-multi-agent-research-system)" (Jun 13, 2025)

The trade-off is the cold cache (Section 1). Use subagents when the context-isolation win exceeds the cold-cache loss — typically when the subtask is large enough to warrant its own session.

---

## Section 7: Batch API — for async workloads only

If you're processing large volumes of non-interactive requests — content moderation at scale, dataset analysis, bulk evaluations — the Message Batches API processes them asynchronously at 50% lower cost. Most batches finish in under an hour. ([source](https://docs.anthropic.com/en/docs/build-with-claude/batch-processing))

This is not a latency optimization for interactive use. The Batch API has no SLA on turnaround. Use it only when immediate responses aren't required and cost efficiency matters more than speed.

---

## Section 8: Measure your own latency

Optimization without measurement is guesswork. The four numbers worth tracking, drawn from standard SRE practice:

| Metric | What it measures | Why it matters |
| :--- | :--- | :--- |
| **TTFT (time to first token)** | Wall-clock from request sent to first response token received | Dominated by prompt processing + queuing. The number caching most directly improves |
| **Output tokens/second** | Generation throughput once streaming begins | Model- and load-dependent. Streaming hides this from users but it's the cap on long responses |
| **Total wall-clock time** | Request sent → response complete | What the user actually waits |
| **Tail latency (p95 / p99)** | Slowest 5% and 1% of requests | Median latency lies; tails dominate user experience |

Track these per model, per workload type, before and after each lever in this guide. Median (p50) numbers are noisy and improve under load just because faster requests dominate the average. **Watch the p95.** If a change moves the median down but the p95 up, you've made the experience worse for the people most likely to abandon.

A minimal measurement loop in Python:

```python
import time, statistics
from anthropic import Anthropic

client = Anthropic()
latencies_ttft, latencies_total = [], []

for prompt in test_prompts:
    t0 = time.perf_counter()
    first_token_time = None
    with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for text in stream.text_stream:
            if first_token_time is None:
                first_token_time = time.perf_counter()
    t1 = time.perf_counter()
    latencies_ttft.append(first_token_time - t0)
    latencies_total.append(t1 - t0)

def p(values, q): return statistics.quantiles(values, n=100)[q-1]
print(f"TTFT  p50={p(latencies_ttft, 50):.2f}s  p95={p(latencies_ttft, 95):.2f}s")
print(f"Total p50={p(latencies_total, 50):.2f}s  p95={p(latencies_total, 95):.2f}s")
```

Run this **before** enabling caching, parallel tool calls, or a model downgrade — and again after. The deltas tell you whether the lever actually moved your workload, or just moved someone else's.

---

## Anti-patterns — what slows you down

**Spawning a subagent to read two files.** Subagents start with a cold cache. Use direct tool calls for small, bounded reads. Reserve subagents for genuinely isolated work or large reads that would otherwise bloat your main context.

**Switching models mid-session in Claude Code.** Each switch is a cache miss on the full context. Decide your model at session start.

**Enabling extended thinking by default.** It's a cost and latency penalty on anything that doesn't require multi-step reasoning. Leave it off; opt in per call.

**Sending tool results in separate user messages.** Breaks parallel tool behavior. Claude reverts to sequential calls.

**Putting dynamic content before stable content.** Cache is prefix-matched. If the user's question precedes your system prompt or reference document, nothing caches downstream.

**Asking for long explanations when you want a short answer.** Claude calibrates response length to perceived task complexity. If you want shorter output, say so explicitly: "Result only. No explanation."

**Bloating CLAUDE.md.** The official guidance is under 200 lines. Larger files reduce adherence and consume context on every session.

**Enabling caching on a low-traffic workload.** Per Simon Willison's launch-day analysis, apps prompting less than once every five minutes can pay more for cache writes than they save on hits. Cache is for repeated, bursty traffic.

**Optimizing the median when the p95 is what hurts.** Tail latency is the user experience for the user most likely to leave. Track p95 / p99, not just the average.

---

## Sources & Attribution

Sources are listed by tier, from primary documentation outward. Every claim in this guide ties back to a numbered source below. Every URL was verified end-to-end (followed redirects, confirmed the cited claim is on the destination page) at the time of publication.

### Tier 1 — Primary Anthropic documentation

| # | Source | URL | What it backs |
| :- | :--- | :--- | :--- |
| 1 | Prompt Caching | https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching | Cache TTL, pricing multipliers, minimum tokens by model, prefix-match mechanics |
| 2 | Models Overview | https://docs.anthropic.com/en/docs/about-claude/models/overview | Latency labels, pricing per million tokens, model capabilities |
| 3 | Parallel Tool Use | https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/parallel-tool-use | Multiple `tool_use` blocks per response, single-message rule for results, recommended system prompts |
| 4 | Extended Thinking | https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking | `budget_tokens` parameter, `display: "omitted"` TTFT benefit, Opus 4.7 manual-thinking deprecation, Sonnet 4.6 / Opus 4.6 `budget_tokens` deprecation |
| 5 | Adaptive Thinking | https://docs.anthropic.com/en/docs/build-with-claude/adaptive-thinking | Adaptive thinking model behavior on Opus 4.7 |
| 6 | Messages API | https://docs.anthropic.com/en/api/messages | `effort` parameter (`low`/`medium`/`high`/`xhigh`/`max`) at `output_config.effort`, full parameter surface |
| 7 | Message Batches API | https://docs.anthropic.com/en/docs/build-with-claude/batch-processing | 50% cost reduction, async processing, sub-1-hour typical turnaround |
| 8 | Claude Code: Prompt Caching | https://docs.claude.com/en/docs/claude-code/prompt-caching | Cache invalidation triggers in Claude Code, subagent cache isolation |
| 9 | Claude Code: Memory (CLAUDE.md) | https://docs.claude.com/en/docs/claude-code/memory | 200-line guidance for CLAUDE.md, path-scoped rules |

### Tier 2 — Anthropic engineering writing

| # | Source | URL | What it backs |
| :- | :--- | :--- | :--- |
| 10 | "Building effective agents" (Dec 19, 2024) | https://www.anthropic.com/engineering/building-effective-agents | The latency/cost vs. task-performance tradeoff framing |
| 11 | "How we built our multi-agent research system" (Jun 13, 2025) | https://www.anthropic.com/engineering/built-multi-agent-research-system | "Cut research time by up to 90% for complex queries" via parallel subagent + tool execution; subagent context isolation framing |

### Tier 3 — Cross-vendor confirmation

| # | Source | URL | What it backs |
| :- | :--- | :--- | :--- |
| 12 | Google Gemini context caching | https://ai.google.dev/gemini-api/docs/caching | Industry-standard caching mechanism; 75% discount, 1-hour default TTL, 1,024 / 4,096-token minimums |

### Tier 4 — Independent practitioner voices

| # | Source | URL | What it backs |
| :- | :--- | :--- | :--- |
| 13 | Lilian Weng, "LLM Powered Autonomous Agents" (Jun 23, 2023) | https://lilianweng.github.io/posts/2023-06-23-agent/ | Foundational "every command has a cost" framing for agent efficiency |
| 14 | Simon Willison, "Prompt caching with Claude" (Aug 14, 2024) | https://simonwillison.net/2024/Aug/14/prompt-caching-with-claude/ | Independent confirmation of ~10% cache-hit cost; the negative-ROI caveat for sub-5-minute traffic; cross-vendor pricing context (Gemini 75%, DeepSeek ~90%) |
| 15 | Eugene Yan, "Patterns for Building LLM-based Systems & Products" | https://eugeneyan.com/writing/llm-patterns/ | "Shift latency from generation (seconds) to cache lookup (milliseconds)" — conceptual anchor for the caching section |

### Tier 5 — Peer-reviewed research foundation

| # | Source | URL | What it backs |
| :- | :--- | :--- | :--- |
| 16 | Kwon et al., "Efficient Memory Management for Large Language Model Serving with PagedAttention" (arXiv:2309.06180, Sep 12, 2023) | https://arxiv.org/abs/2309.06180 | KV-cache memory fragmentation (60–80% waste in naïve systems, under 4% with PagedAttention); 2–4× throughput improvement vs. FasterTransformer / Orca at the same latency |
| 17 | vLLM project blog, "vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention" (Jun 20, 2023) | https://vllm.ai/blog/2023-06-20-vllm | 14–24× throughput improvement vs. HuggingFace Transformers |

---

> © 2026 Rick Watson / RMW Commerce Consulting. This compilation, its ranking, and the original commentary are copyrighted. The underlying techniques originate from Anthropic's official Claude API and Claude Code documentation, supplemented by Anthropic engineering writing and the independent practitioner and research voices listed in [Sources & Attribution](#sources--attribution). Quoting brief excerpts with attribution is fine. Republishing the compilation in whole or in substantial part requires written permission: rick@rmwcommerce.com.
