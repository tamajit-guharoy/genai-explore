# Claude API Development — Complete Guide (2026)

> **Target Audience:** Python developers building applications with the Anthropic Claude API.  
> **SDK Version:** `anthropic` (Python) — latest as of May 2026.  
> **API Version:** `anthropic-version: 2023-06-01`  
> **Models Covered:** Claude Opus 4.7, Opus 4.6, Sonnet 4.6, Haiku 4.5

---

## Table of Contents

### Part 1: Setup & Core Messaging
1. [Installation & Authentication](#1-installation--authentication)
2. [Messages API — The Core](#2-messages-api--the-core)
3. [Content Blocks Reference](#3-content-blocks-reference)
4. [Streaming — SSE Events](#4-streaming--sse-events)

### Part 2: Model Selection & Output Control
5. [Model Selection Guide](#5-model-selection-guide)
6. [Output Parameters](#6-output-parameters)

### Part 3: Reasoning & Thinking
7. [Extended Thinking & Adaptive Thinking](#7-extended-thinking--adaptive-thinking)
8. [Interleaved Thinking](#8-interleaved-thinking)

### Part 4: Tool Use & Function Calling
9. [Custom Tool Use — Function Calling](#9-custom-tool-use--function-calling)
10. [Parallel Tool Calls](#10-parallel-tool-calls)
11. [Built-in Server-Side Tools](#11-built-in-server-side-tools)
12. [Computer Use](#12-computer-use)

### Part 5: Structured Output & Citations
13. [Structured Outputs / JSON Mode](#13-structured-outputs--json-mode)
14. [Citations API](#14-citations-api)

### Part 6: Prompt Engineering Techniques
15. [Pre-filling Assistant Responses](#15-pre-filling-assistant-responses)
16. [Multi-System Messages](#16-multi-system-messages)
17. [Prompt Caching](#17-prompt-caching)
18. [Cache Diagnostics](#18-cache-diagnostics)

### Part 7: Context & Files
19. [Context Compaction](#19-context-compaction)
20. [Files API](#20-files-api)
21. [Token Counting API](#21-token-counting-api)

### Part 8: Managed Agents (Beta)
22. [Agents, Environments & Sessions](#22-agents-environments--sessions)
23. [Session Events & SSE Streaming](#23-session-events--sse-streaming)
24. [Session Resources & Webhooks](#24-session-resources--webhooks)

### Part 9: Agent Skills
25. [Writing & Using Skills](#25-writing--using-skills)
26. [Progressive Disclosure](#26-progressive-disclosure)

### Part 10: Administration & Operations
27. [Models API](#27-models-api)
28. [Usage & Cost API](#28-usage--cost-api)
29. [Data Residency](#29-data-residency)
30. [Service Tiers](#30-service-tiers)
31. [Fast Mode](#31-fast-mode)

### Part 11: Batch Processing & Reliability
32. [Batch API](#32-batch-api)
33. [Error Handling & Retries](#33-error-handling--retries)
34. [Idempotency](#34-idempotency)
35. [Rate Limits & Throttling](#35-rate-limits--throttling)

### Part 12: Examples
36. [Complete Working Examples](#36-complete-working-examples)

---

## Part 1: Setup & Core Messaging

### 1. Installation & Authentication

#### Install the SDK

```bash
pip install anthropic
```

#### Set Your API Key

```python
import os
from anthropic import Anthropic

# Option A: Pass explicitly
client = Anthropic(api_key="sk-ant-api03-...")

# Option B: Environment variable (recommended)
# export ANTHROPIC_API_KEY="sk-ant-api03-..."
client = Anthropic()  # reads ANTHROPIC_API_KEY automatically

# Option C: From a secrets manager
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
```

#### Required Headers

Every request includes these behind the scenes:

| Header | Value | Purpose |
|--------|-------|---------|
| `x-api-key` | `sk-ant-api03-...` | Authenticates you |
| `anthropic-version` | `2023-06-01` | API version pinning |
| `content-type` | `application/json` | Request format |

You set `anthropic-version` once on the client; the SDK sends it automatically:

```python
client = Anthropic(
    api_key="sk-ant-api03-...",
    default_headers={"anthropic-version": "2023-06-01"},
)
```

#### API Base URL

The SDK defaults to `https://api.anthropic.com`. For AWS Bedrock or GCP Vertex, use a custom base URL or the provider-specific SDK.

---

### 2. Messages API — The Core

The Messages API is the primary (and only) way to interact with Claude. It replaces the older Text Completions API, which was retired.

**Endpoint:** `POST https://api.anthropic.com/v1/messages`

#### First API Call

```python
import anthropic

client = anthropic.Anthropic()

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system="You are a helpful assistant who speaks like a pirate.",
    messages=[
        {"role": "user", "content": "What be the fastest sea creature?"}
    ],
)

print(response.content[0].text)
# "Arrr, the sailfish be the fastest, clockin' in at 68 knots!"
```

#### Message Structure

```python
messages=[
    {"role": "user", "content": "Hello"},                    # Turn 1 — user
    {"role": "assistant", "content": "Hi! How can I help?"}, # Turn 1 — assistant
    {"role": "user", "content": "Tell me a joke"},           # Turn 2 — user
]
```

**Rules:**
- Messages alternate: `user` → `assistant` → `user` → `assistant` ...
- Must start with a `user` message
- Must end with a `user` message (you can't have trailing `assistant`)
- The `system` parameter is separate (not part of `messages`)

#### Response Object

```python
{
    "id": "msg_01AbCdEfGhIjKlMnOp",
    "type": "message",
    "role": "assistant",
    "content": [
        {
            "type": "text",
            "text": "Here's your answer..."
        }
    ],
    "model": "claude-sonnet-4-6",
    "stop_reason": "end_turn",
    "stop_sequence": None,
    "usage": {
        "input_tokens": 25,
        "output_tokens": 87,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0
    }
}
```

#### Stop Reasons

| `stop_reason` | Meaning |
|---|---|
| `end_turn` | Normal completion — Claude finished naturally |
| `max_tokens` | Hit the `max_tokens` limit — response truncated |
| `stop_sequence` | Hit a custom stop sequence you defined |
| `tool_use` | Claude wants to call a tool (you must respond with `tool_result`) |

#### Multi-Turn Conversation

```python
messages = []

# Turn 1
messages.append({"role": "user", "content": "What is Python?"})
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=messages,
)
messages.append({"role": "assistant", "content": resp.content})

# Turn 2
messages.append({"role": "user", "content": "Now explain the GIL."})
resp = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=messages,
)
messages.append({"role": "assistant", "content": resp.content})
```

#### Including Images in Messages

```python
import base64

with open("chart.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode("utf-8")

messages = [{
    "role": "user",
    "content": [
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/png",
                "data": image_data,
            },
        },
        {"type": "text", "text": "Describe this chart."},
    ],
}]
```

Supported image formats: `image/jpeg`, `image/png`, `image/gif`, `image/webp`.

---

### 3. Content Blocks Reference

Every Claude response contains `content` — an array of **content blocks**. Each block has a `type`.

#### Text Block

```json
{"type": "text", "text": "Hello, world!"}
```

#### Tool Use Block

Claude requests a function call:

```json
{
    "type": "tool_use",
    "id": "toolu_01AbCdEfGhIjKlMnOp",
    "name": "get_weather",
    "input": {"city": "Paris", "unit": "celsius"}
}
```

#### Tool Result Block

You return the result of a tool call:

```json
{
    "type": "tool_result",
    "tool_use_id": "toolu_01AbCdEfGhIjKlMnOp",
    "content": "Paris: 22°C, partly cloudy"
}
```

#### Thinking Block

When extended thinking is enabled:

```json
{
    "type": "thinking",
    "thinking": "Let me break this down. First, I need to...",
    "signature": "abc123..."
}
```

#### Redacted Thinking Block

When thinking is redacted for safety:

```json
{
    "type": "redacted_thinking",
    "data": "..."
}
```

#### Server Tool Use Block

Built-in server-side tool calls (web search, code execution, etc.):

```json
{
    "type": "server_tool_use",
    "id": "srv_01AbCd...",
    "name": "web_search",
    "input": {"query": "latest AI news 2026"},
    "status": "completed",
    "delta": null
}
```

The `status` field can be: `pending` → `executing` → `completed` or `errored`. For `code_execution`, partial results stream via `delta`.

#### Image Block (input only)

```json
{
    "type": "image",
    "source": {
        "type": "base64",
        "media_type": "image/png",
        "data": "iVBORw0KGgo..."
    }
}
```

Or via URL:

```json
{
    "type": "image",
    "source": {
        "type": "url",
        "url": "https://example.com/chart.png"
    }
}
```

#### Compaction Block

When context compaction is triggered (see Section 19):

```json
{
    "type": "compaction",
    "content": "Summary of prior conversation: The user is building a web app..."
}
```

---

### 4. Streaming — SSE Events

Streaming delivers tokens in real time via Server-Sent Events (SSE).

#### Basic Streaming

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a haiku about coding."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

#### Full Event Stream

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
) as stream:
    for event in stream:
        print(f"[{event.type}] {event}")

    # After the stream ends, get the final message:
    final_message = stream.get_final_message()
    print(f"Stop reason: {final_message.stop_reason}")
    print(f"Usage: {final_message.usage}")
```

#### SSE Event Types

| Event | When | Key Fields |
|---|---|---|
| `message_start` | Response begins | `message.id`, `message.model` |
| `content_block_start` | A new content block begins | `content_block.type`, `index` |
| `content_block_delta` | Incremental content in the current block | `delta.type` (`text_delta`, `input_json_delta`, `thinking_delta`, `signature_delta`) |
| `content_block_stop` | A content block finishes | `index` |
| `message_delta` | Top-level message changes | `delta.stop_reason`, `delta.stop_sequence`, `usage.output_tokens` |
| `message_stop` | Entire response is done | Final marker |
| `ping` | Keep-alive heartbeat | Ignore in application code |

#### Streaming Best Practices

1. **Use `text_stream` for simple cases** — it filters to just text deltas
2. **Use the event loop for tool calls** — you need `content_block_start` to detect `tool_use` blocks
3. **Always call `get_final_message()`** — the stream itself is for real-time display; the final message has the canonical `usage` and `stop_reason`
4. **Handle `ping` by ignoring it** — the SDK handles this automatically when you use the `with` block

---

## Part 2: Model Selection & Output Control

### 5. Model Selection Guide

#### Active Models (May 2026)

| Model | Context | Max Output | Thinking | Best For |
|---|---|---|---|---|
| **Opus 4.7** | 1M tokens | 128K tokens | Adaptive (`effort`) | Most capable — complex reasoning, long-horizon agents, deep analysis |
| **Opus 4.6** | 1M tokens | 128K tokens | Extended + Adaptive | Near-Opus-4.7 capability, supports `temperature`/`top_p`/`top_k` |
| **Sonnet 4.6** | 1M tokens | 64K tokens | Extended + Adaptive | Best balance of speed, cost, and capability — daily driver |
| **Haiku 4.5** | 200K tokens | 8K tokens | None | Fastest, cheapest — classification, extraction, simple chat |

#### Model String IDs

```python
# Use these exact strings:
"claude-opus-4-7"       # Latest, most capable
"claude-opus-4-6"       # Previous generation
"claude-sonnet-4-6"     # Best all-rounder
"claude-haiku-4-5"      # Fast and cheap
```

#### Pricing

| Model | Input ($/MTok) | Output ($/MTok) | Cache Write ($/MTok) | Cache Read ($/MTok) |
|---|---|---|---|---|
| Opus 4.7 / 4.6 | $5.00 | $25.00 | $6.25 (5m) / $10.00 (1h) | $0.50 |
| Sonnet 4.6 | $3.00 | $15.00 | $3.75 (5m) / $6.00 (1h) | $0.30 |
| Haiku 4.5 | $1.00 | $5.00 | N/A | N/A |

#### Key Differences: Opus 4.7 vs Opus 4.6

Opus 4.7 has **breaking changes**:
- **`temperature`, `top_p`, `top_k` are REMOVED** — the model handles output control internally
- **`thinking.budget_tokens` is REMOVED** — use `thinking: {"type": "adaptive"}` with `output_config.effort` instead
- **New tokenizer** — token counts differ from Opus 4.6
- **High-res vision** — up to 2,576px on the long edge (vs 1,568px)

#### Model Selection Decision Tree

```
Need deep reasoning on complex problems?
├── YES + longest context + highest capability → Opus 4.7
├── YES + need temperature control → Opus 4.6
└── NO → Continue...

Need balanced performance/cost for daily tasks?
├── YES → Sonnet 4.6
└── NO → Continue...

Need fastest + cheapest for simple tasks?
└── YES → Haiku 4.5
```

---

### 6. Output Parameters

#### `max_tokens` (REQUIRED)

The maximum number of tokens Claude can generate. **You must always set this.**

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,  # REQUIRED — no default
    messages=[...],
)
```

**Guidelines:**
- Set it higher than you think you need — you're billed for actual tokens, not the cap
- 1024 is good for short answers; 4096 for medium; 16384+ for long-form / code generation
- If Claude hits `max_tokens`, `stop_reason` will be `"max_tokens"` — check for truncation

#### `temperature` (Opus 4.6, Sonnet 4.6, Haiku 4.5 only)

Controls randomness. Range: `0.0` to `1.0`.

```python
# Deterministic — best for math, code, classification
response = client.messages.create(temperature=0.0, ...)

# Creative — best for writing, brainstorming, ideation
response = client.messages.create(temperature=0.9, ...)

# Balanced (default)
response = client.messages.create(temperature=0.5, ...)
```

**Note: Opus 4.7 does NOT support `temperature`**, `top_p`, or `top_k`. The model handles output control internally.

#### `top_p` (Nucleus Sampling)

Range: `0.0` to `1.0`. The model considers only the smallest set of tokens whose cumulative probability exceeds `top_p`.

```python
response = client.messages.create(top_p=0.9, ...)
```

#### `top_k`

Integer. Only sample from the top K most likely tokens.

```python
response = client.messages.create(top_k=40, ...)
```

#### `stop_sequences`

Custom strings that cause Claude to stop generating. Useful for structured formats.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    stop_sequences=["END", "---", "```"],
    messages=[{"role": "user", "content": "Write a story. End with END."}],
)
# stop_reason will be "stop_sequence" if triggered
```

#### `metadata`

Attach arbitrary key-value pairs (useful for filtering in the Usage API, logs, etc.):

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    metadata={"user_id": "usr_123", "session_id": "sess_abc"},
    messages=[...],
)
```

---

## Part 3: Reasoning & Thinking

### 7. Extended Thinking & Adaptive Thinking

Claude can "think" before responding — performing internal reasoning that improves answer quality on complex tasks. There are two thinking modes.

#### Extended Thinking (Opus 4.6, Sonnet 4.6)

You specify a **budget** in tokens (minimum 1,024). Claude uses up to that many tokens for internal reasoning.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    thinking={
        "type": "enabled",
        "budget_tokens": 2000,  # minimum 1024
    },
    messages=[{
        "role": "user",
        "content": "Solve this integral: ∫(x² + 3x + 2)dx from 0 to 5"
    }],
)

# Check if thinking happened
for block in response.content:
    if block.type == "thinking":
        print(f"Claude thought for {len(block.thinking)} chars")
    elif block.type == "text":
        print(f"Answer: {block.text}")

# Usage includes thinking tokens
print(f"Input: {response.usage.input_tokens}")
print(f"Output (including thinking): {response.usage.output_tokens}")
```

#### Adaptive Thinking (Opus 4.7, Opus 4.6, Sonnet 4.6)

Instead of a fixed budget, Claude dynamically decides how much to think based on task complexity.

**Opus 4.7:**

```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},  # xhigh | high | medium | low
    messages=[{"role": "user", "content": "Explain quantum entanglement."}],
)
```

**Opus 4.6 / Sonnet 4.6:**

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    thinking={
        "type": "adaptive",
        "budget_tokens": 4000,  # still required as fallback on 4.6
    },
    messages=[{"role": "user", "content": "Explain quantum entanglement."}],
)
```

#### Effort Levels (Opus 4.7)

| Level | Description | Use Case |
|---|---|---|
| `xhigh` | Maximum reasoning | Research-level analysis, complex math proofs |
| `high` | Significant reasoning | Hard coding problems, architecture decisions |
| `medium` | Moderate reasoning | Standard analytical tasks |
| `low` | Minimal reasoning | Simple Q&A, when speed matters |

#### When to Use Thinking

| Use Thinking | Don't Use Thinking |
|---|---|
| Math, logic, coding problems | Simple Q&A, chitchat |
| Multi-step reasoning | Classification with clear rules |
| Analyzing complex documents | Translation (unless highly nuanced) |
| Architecture/design decisions | When latency is critical |
| "Gotcha" or trick questions | Haiku 4.5 (doesn't support thinking) |

#### Streaming with Thinking

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    thinking={"type": "enabled", "budget_tokens": 2000},
    messages=[...],
) as stream:
    for event in stream:
        if event.type == "content_block_delta":
            if event.delta.type == "thinking_delta":
                print(f"[THINKING] {event.delta.thinking}", end="")
            elif event.delta.type == "text_delta":
                print(event.delta.text, end="")
```

#### Thinking Signatures

Each thinking block includes a `signature` field. This is a cryptographic verification that the thinking is genuine and hasn't been tampered with. You don't need to verify it yourself — the API validates it.

---

### 8. Interleaved Thinking

Interleaved thinking lets Claude reason **between tool calls** during an agentic loop, not just at the beginning. This is critical for complex multi-step tasks where the next action depends on analyzing previous results.

**Supported on:** Opus 4.6, Opus 4.7

#### How It Works

Without interleaved thinking, Claude thinks once at the start, then executes all tool calls. With it, Claude can:

1. Think → Call Tool A → Get result → Think about result → Call Tool B → Think → Respond

#### Usage

```python
tools = [
    {
        "name": "read_file",
        "description": "Read contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"}
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_code",
        "description": "Search codebase for a pattern",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"}
            },
            "required": ["pattern"],
        },
    },
]

messages = [
    {
        "role": "user",
        "content": "Find all places where we use `User.objects.filter` and check if any are missing `.select_related()` for the 'profile' field."
    }
]

# Interleaved thinking happens automatically on supported models
# when you use tool use with thinking enabled
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},
    tools=tools,
    messages=messages,
)

# Claude may interleave multiple thinking + tool_use pairs
for block in response.content:
    if block.type == "thinking":
        print(f"[THOUGHT] {block.thinking[:200]}...")
    elif block.type == "tool_use":
        print(f"[TOOL] {block.name}({block.input})")
```

#### Multi-Turn Loop with Interleaved Thinking

```python
import json

def run_agent(user_task):
    messages = [{"role": "user", "content": user_task}]

    while True:
        response = client.messages.create(
            model="claude-opus-4-7",
            max_tokens=4096,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            tools=tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        # Check if done
        if response.stop_reason == "end_turn":
            return response.content

        # Execute all tool calls
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result = execute_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

        messages.append({"role": "user", "content": tool_results})
```

---

## Part 4: Tool Use & Function Calling

### 9. Custom Tool Use — Function Calling

Tool use (function calling) lets Claude request external function calls. Your application executes them and returns results.

#### Defining a Tool

```python
tools = [
    {
        "name": "get_stock_price",
        "description": "Get the current stock price for a given ticker symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. AAPL, GOOGL",
                },
            },
            "required": ["ticker"],
        },
    },
]
```

#### Full Tool Use Flow

```python
import anthropic
import yfinance as yf

client = anthropic.Anthropic()

def get_stock_price(ticker: str) -> dict:
    stock = yf.Ticker(ticker)
    price = stock.fast_info.get("lastPrice", 0)
    return {"ticker": ticker, "price": price}

tools = [
    {
        "name": "get_stock_price",
        "description": "Get the current stock price for a given ticker.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Stock ticker symbol, e.g. AAPL",
                },
            },
            "required": ["ticker"],
        },
    },
]

def run_conversation():
    messages = [{"role": "user", "content": "What's the current price of AAPL and MSFT?"}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            tools=tools,
            messages=messages,
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Done — print final text
            for block in response.content:
                if block.type == "text":
                    print(block.text)
            break

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "get_stock_price":
                        result = get_stock_price(block.input["ticker"])
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": str(result),
                        })

            messages.append({"role": "user", "content": tool_results})
```

#### Tool Choice

Control whether Claude uses tools:

```python
# Auto (default): Claude decides whether to use tools
response = client.messages.create(tool_choice={"type": "auto"}, ...)

# Any: Claude MUST use at least one tool
response = client.messages.create(
    tool_choice={"type": "any"}, ...
)

# Specific tool: Claude MUST use this exact tool
response = client.messages.create(
    tool_choice={"type": "tool", "name": "get_stock_price"}, ...
)

# None: Claude must NOT use any tools (text-only response)
response = client.messages.create(
    tool_choice={"type": "none"}, ...  # disables all tools for this request
)

# Disable a subset of tools (use only SOME):
response = client.messages.create(
    tool_choice={
        "type": "tools",
        "tools": [
            {"type": "tool", "name": "read_file"},
            {"type": "tool", "name": "search_code"},
        ]
    },
    tools=[all_my_tools],  # full list
    ...
)
```

#### Tool Definition Best Practices

1. **Descriptive `name`**: Use `snake_case`, be specific: `search_customer_by_email`, not `search`
2. **Detailed `description`**: Include when to use AND when NOT to use it
3. **Precise `input_schema`**: Use `description` on every property; use `enum` for constrained values; use `required` for mandatory fields
4. **Return clean results**: Return `str` or `dict` (will be stringified). Keep it concise — the result goes into context
5. **Return errors too**: If a tool fails, return the error message — Claude can recover or try alternatives

```python
# Good tool definition
{
    "name": "search_customers",
    "description": "Search customer database by email or name. Use this to look up customer details before creating tickets. Do NOT use for analytics queries.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search string — email address or partial/full name",
            },
            "search_by": {
                "type": "string",
                "enum": ["email", "name", "auto"],
                "description": "Field to search. 'auto' tries email first, then name.",
            },
        },
        "required": ["query"],
    },
}
```

---

### 10. Parallel Tool Calls

Claude can request multiple tool calls in a single response when they're independent of each other.

#### When Parallel Calls Happen

Claude automatically parallelizes when tool calls are **independent** — i.e., Tool B's input doesn't depend on Tool A's output.

```python
messages = [{
    "role": "user",
    "content": "Get the weather for Paris, Tokyo, and New York simultaneously."
}]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[weather_tool],
    messages=messages,
)

# response.content may contain MULTIPLE tool_use blocks
for block in response.content:
    if block.type == "tool_use":
        print(f"{block.name}({block.input['city']})")  # 3 calls in one response
```

#### Handling Parallel Results

```python
import concurrent.futures

def execute_parallel_tools(response):
    tool_calls = [block for block in response.content if block.type == "tool_use"]

    def call_tool(block):
        result = execute_single_tool(block.name, block.input)
        return {"type": "tool_result", "tool_use_id": block.id, "content": str(result)}

    with concurrent.futures.ThreadPoolExecutor() as executor:
        return list(executor.map(call_tool, tool_calls))
```

#### Disabling Parallel Tool Calls

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "auto", "disable_parallel_tool_use": True},
    messages=messages,
)
```

---

### 11. Built-in Server-Side Tools

Claude provides server-side tools that Anthropic hosts and executes. You don't need to handle the tool execution yourself.

#### Web Search (`web_search_20260209`)

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[
        {
            "type": "web_search_20260209",
            "name": "web_search",
            "user_location": {
                "type": "approximate",
                "city": "San Francisco",
                "country": "US",
                "region": "California",
            },
        }
    ],
    messages=[{
        "role": "user",
        "content": "What were the top technology news stories today?"
    }],
)

for block in response.content:
    if block.type == "text":
        print(block.text)
    elif block.type == "server_tool_use":
        print(f"Search status: {block.status}")  # "completed"
```

**Pricing:** $10 per 1,000 searches. Usage tracked automatically.

#### Web Fetch (`web_fetch_20260209`)

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    tools=[
        {"type": "web_fetch_20260209", "name": "web_fetch"},
    ],
    messages=[{
        "role": "user",
        "content": "Fetch and summarize the article at https://example.com/article"
    }],
)
```

**Pricing:** Free (token costs only). Included in standard input/output pricing.

#### Code Execution (`code_execution_20250825`)

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    tools=[
        {
            "type": "code_execution_20250825",
            "name": "code_execution",
        },
    ],
    messages=[{
        "role": "user",
        "content": """Analyze this dataset and create a summary plot:

Month, Sales, Expenses
Jan, 12000, 8000
Feb, 15000, 9000
Mar, 11000, 8500
Apr, 18000, 10000
May, 20000, 12000
Jun, 17000, 11000"""
    }],
)

# Results appear in server_tool_use blocks
for block in response.content:
    if block.type == "server_tool_use" and block.name == "code_execution":
        print(f"Status: {block.status}")
        # block may contain image outputs (plots), text, stdout
```

**Pricing:** Free when bundled with web tools. $0.05 per container-hour after 1,550 free hours/month.

#### Text Editor (`text_editor_20250728`)

```python
tools = [
    {
        "type": "text_editor_20250728",
        "name": "text_editor",
    },
]

response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=2048,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "Create a file called hello.py with a greeting function, then view it."
    }],
)
```

The text editor tool supports three operations:
- `view` — Read a file
- `create` — Create a new file
- `str_replace` — Replace a string in a file
- `insert` — Insert text at a line
- `undo_edit` — Revert the last edit

#### Bash (`bash_20250124`)

```python
tools = [
    {
        "type": "bash_20250124",
        "name": "bash",
    },
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    tools=tools,
    messages=[{
        "role": "user",
        "content": "List all Python files in the current directory and count lines in each."
    }],
)
```

#### Memory (`memory_20250818`)

Persistent file-based memory for long-running sessions.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[
        {"type": "memory_20250818", "name": "memory"},
    ],
    messages=[{
        "role": "user",
        "content": "Remember that I prefer British English spellings and my name is Sam."
    }],
)
```

---

### 12. Computer Use

The Computer Use tool lets Claude control a desktop environment — viewing screenshots, clicking, typing, scrolling.

**Tool ID:** `computer_20251124`

#### Tool Definition

```python
computer_tool = {
    "type": "computer_20251124",
    "name": "computer",
    "display_width_px": 1280,
    "display_height_px": 800,
    "display_number": 0,
}
```

#### Available Actions

| Action | Description | Required Params |
|---|---|---|
| `key` | Press a key or key combination | `text` (e.g., "ctrl+c", "Enter") |
| `type` | Type a string of text | `text` |
| `mouse_move` | Move cursor to (x, y) | `coordinate` (array [x, y]) |
| `left_click` | Left mouse click | `coordinate` |
| `right_click` | Right mouse click | `coordinate` |
| `middle_click` | Middle mouse click | `coordinate` |
| `double_click` | Double click | `coordinate` |
| `left_click_drag` | Click and drag | `coordinate`, `end_coordinate` |
| `scroll` | Scroll up/down | `coordinate`, `pixels` |
| `screenshot` | Capture the screen | (none) |
| `cursor_position` | Get cursor location | (none) |

#### Full Example

```python
import time
import base64
import anthropic

client = anthropic.Anthropic()

tools = [{
    "type": "computer_20251124",
    "name": "computer",
    "display_width_px": 1280,
    "display_height_px": 800,
    "display_number": 0,
}]

messages = [{
    "role": "user",
    "content": "Open the browser, navigate to weather.com, and tell me the temperature in Paris."
}]

while True:
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        tools=tools,
        messages=messages,
    )

    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":
        for block in response.content:
            if block.type == "text":
                print(block.text)
        break

    # Execute computer actions
    tool_results = []
    for block in response.content:
        if block.type == "tool_use" and block.name == "computer":
            # Action is in block.input
            action = block.input["action"]

            # Execute the computer action via your display server
            if action == "screenshot":
                screenshot = capture_screen()  # your implementation
                image_data = base64.standard_b64encode(screenshot).decode()
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        }
                    ],
                })
            else:
                execute_computer_action(action, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "Action executed successfully.",
                })

    messages.append({"role": "user", "content": tool_results})
```

---

## Part 5: Structured Output & Citations

### 13. Structured Outputs / JSON Mode

Force Claude to produce valid JSON output, optionally conforming to a schema.

#### Simple JSON Mode

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    output_config={"format": {"type": "json_object"}},
    messages=[{
        "role": "user",
        "content": "List 3 popular Python web frameworks with their latest versions."
    }],
)

import json
result = json.loads(response.content[0].text)
# {"frameworks": [{"name": "Django", "version": "5.1"}, ...]}
```

#### JSON Mode with Schema (Structured Outputs)

```python
from anthropic.types import TextBlock

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    output_config={
        "format": {
            "type": "json_schema",
            "name": "movie_review",
            "schema": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "year": {"type": "integer"},
                    "rating": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 10,
                    },
                    "genres": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "summary": {
                        "type": "string",
                        "maxLength": 200,
                    },
                    "recommended": {"type": "boolean"},
                },
                "required": ["title", "year", "rating", "genres", "summary", "recommended"],
            },
            "strict": True,  # reject non-conforming output
        }
    },
    messages=[{
        "role": "user",
        "content": "Review the movie Inception.",
    }],
)

review = json.loads(response.content[0].text)
```

#### Combining Tool Use with Structured Outputs

```python
# Definition: the tool's output MUST conform to a schema
tools = [{
    "name": "classify_email",
    "description": "Classify a customer email",
    "input_schema": {
        "type": "object",
        "properties": {
            "email_text": {"type": "string"},
        },
        "required": ["email_text"],
    },
}]

# Force Claude to use the tool with structured output expectations
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    tool_choice={"type": "tool", "name": "classify_email"},
    output_config={
        "format": {
            "type": "json_schema",
            "name": "classification",
            "schema": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": ["complaint", "inquiry", "feedback", "urgent"]},
                    "sentiment": {"type": "string", "enum": ["positive", "neutral", "negative"]},
                    "priority": {"type": "integer", "minimum": 1, "maximum": 5},
                    "key_topics": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["category", "sentiment", "priority", "key_topics"],
            },
            "strict": True,
        }
    },
    messages=[{"role": "user", "content": "Email: My order #12345 arrived damaged and I need a replacement ASAP!"}],
)
```

#### When Structured Output Fails

If `strict: True` and Claude's output doesn't match the schema, you get an error. Without `strict`, Claude may still produce valid JSON most of the time. For critical pipelines, always:

1. Use `strict: True`
2. Add retry logic (see Section 33)
3. Validate the parsed JSON before using it

---

### 14. Citations API

Citations let Claude reference specific passages from documents you provide, with inline citation markers.

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "source": {
                    "type": "text",
                    "media_type": "text/plain",
                    "data": "The Theory of Relativity, developed by Albert Einstein...",
                },
                "title": "Relativity Overview",
                "context": "Physics textbook chapter on relativity",
                "citations": {"enabled": True},
            },
            {
                "type": "document",
                "source": {
                    "type": "text",
                    "media_type": "text/plain",
                    "data": "Quantum mechanics describes nature at the smallest scales...",
                },
                "title": "Quantum Mechanics Intro",
                "context": "Physics textbook chapter on quantum mechanics",
                "citations": {"enabled": True},
            },
            {
                "type": "text",
                "text": "Compare relativity and quantum mechanics. Use citations.",
            },
        ],
    }],
)

# Response includes citation content blocks
for block in response.content:
    if block.type == "text":
        print(block.text)
        # Text includes citation markers like [1], [2]
        # "Relativity [1] and quantum mechanics [2] differ in..."
    elif block.type == "citation":
        print(f"Citation {block.index}: {block.text}")
        print(f"  Document: {block.document_title}")
        print(f"  Start offset: {block.start_offset}")
        print(f"  End offset: {block.end_offset}")
```

#### Supported Document Types

| Source Type | Supported |
|---|---|
| `text/plain` | Yes |
| `application/pdf` (as base64) | Yes |
| Custom content blocks | Yes |

#### Streaming with Citations

Citations stream like any other content block:

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[...],  # documents with citations enabled
) as stream:
    for event in stream:
        if event.type == "content_block_start":
            if event.content_block.type == "citation":
                print(f"\n[Citation block starting]")
        elif event.type == "content_block_delta":
            if event.delta.type == "text_delta":
                print(event.delta.text, end="")
```

---

## Part 6: Prompt Engineering Techniques

### 15. Pre-filling Assistant Responses

You can "pre-fill" part of Claude's response by starting the last message as `assistant`. Claude will continue from where you left off. This is a powerful technique for controlling format, tone, and behavior.

#### Pre-filling Text

```python
messages = [
    {"role": "user", "content": "Write a JSON object with my details: name John, age 30, city NYC"},
    {"role": "assistant", "content": "{"},  # Force Claude to start with {
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=messages,
)
# Claude continues: "name": "John", "age": 30, "city": "NYC"}
```

#### Pre-filling Tool Use

Force Claude to use a specific tool with specific parameters:

```python
messages = [
    {"role": "user", "content": "Search for Python tutorials"},
    {
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "toolu_placeholder_001",  # fake ID, Claude fills real one
                "name": "web_search",
                "input": {},  # Claude fills the input
            }
        ],
    },
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[web_search_tool],
    messages=messages,
)
```

#### Common Pre-fill Patterns

```python
# Force XML/Markdown format
{"role": "assistant", "content": "<response>\n  <analysis>"}

# Force code-only response
{"role": "assistant", "content": "```python\n"}

# Force specific tone
{"role": "assistant", "content": "Certainly! Here's your answer in a professional tone:\n\n"}

# Prevent preamble
{"role": "assistant", "content": "The answer is: "}
```

---

### 16. Multi-System Messages

Claude supports multiple `system` blocks, allowing you to compose prompts from separate components. Each can be individually cached.

#### Simple Multi-System

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a helpful coding assistant.",
        },
        {
            "type": "text",
            "text": "Always respond in Japanese.",
        },
    ],
    messages=[{"role": "user", "content": "Explain recursion."}],
)
```

#### Multi-System with Caching

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are a helpful coding assistant.",
            "cache_control": {"type": "ephemeral"},  # Cache this block
        },
        {
            "type": "text",
            "text": "Always respond in Japanese.",
            # Not cached — different per request
        },
    ],
    messages=[{"role": "user", "content": "Explain recursion."}],
)
```

#### Use Cases for Multi-System

| Pattern | Example |
|---|---|
| Base persona + dynamic rules | `[core_persona_system_msg]` + `[per_session_rules]` |
| Cached prefix + live suffix | `[large_cached_docs]` + `[query_specific_instructions]` |
| Guardrails + behavior | `[safety_rules]` + `[task_instructions]` |
| Multi-tenant | `[tenant_A_prompt]` + `[user_specific_context]` |

---

### 17. Prompt Caching

Prompt caching stores reusable prefixes (system prompts, tool definitions, documents) server-side, reducing latency and cost on subsequent calls.

#### How It Works

1. **Write**: On the first call, include `cache_control: {"type": "ephemeral"}` on content blocks you want cached. Claude writes them to cache.
2. **Read**: On subsequent calls, if the same prefix appears, Claude reads from cache — **90% cheaper** input and lower latency.
3. **Expiry**: Cache entries live for 5 minutes (default) or 1 hour. After expiry, they're re-written on next use.

#### Basic Caching

```python
# Cache the system prompt
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert Python developer... " * 100,  # Large system prompt
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": "Write a function to merge two sorted lists."}],
)

# Check if it was a cache write or read
print(f"Cache write tokens: {response.usage.cache_creation_input_tokens}")  # > 0 = write
print(f"Cache read tokens: {response.usage.cache_read_input_tokens}")  # > 0 = read

# Second call — cache hit
response2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": "You are an expert Python developer... " * 100,  # Same text
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": "Write a binary search function."}],
)
print(f"Cache read tokens: {response2.usage.cache_read_input_tokens}")  # Should be > 0!
```

#### Cache Breakpoint Rules

- `cache_control` marks the **end** of a cacheable segment
- All content up to and including the marked block is cached
- Cacheable prefix must start from the beginning of `system` or `messages[0]`
- Can place breakpoints on: `system` text blocks, `user` message text blocks, tool definitions, tool result blocks
- Minimum cacheable size: 1,024 tokens

#### Cache TTL Options

```python
# 5-minute cache (default) — 1.25x write cost
{"cache_control": {"type": "ephemeral"}}

# 1-hour cache — 2x write cost
{"cache_control": {"type": "ephemeral", "ttl": 3600}}
```

#### Auto-Caching

On supported models, a single `cache_control` at any block auto-caches the last cacheable block:

```python
# Auto-caching: place cache_control on the LAST block you want cached
system=[
    {"type": "text", "text": "Large doc 1..."},
    {"type": "text", "text": "Large doc 2..."},
    {"type": "text", "text": "Large doc 3..."},
    {"type": "text", "text": "Final block...", "cache_control": {"type": "ephemeral"}},
    # Everything above gets cached
]
```

#### What to Cache

| Good to Cache | Don't Cache |
|---|---|
| System prompts (> 1K tokens) | Short system prompts (< 1K tokens) |
| Tool definitions (many/complex tools) | Unique per-request user messages |
| Reference documents / knowledge base | Rapidly changing data |
| Few-shot examples | Sensitive data you want to expire fast |
| Style guides, formatting rules | Content you only use once |

#### Cache Cost Savings

| Model | Base Input | Cache Read | Savings |
|---|---|---|---|
| Opus 4.7 | $5.00/MTok | $0.50/MTok | **90%** |
| Sonnet 4.6 | $3.00/MTok | $0.30/MTok | **90%** |

Cache writes cost 1.25x (5-min TTL) or 2x (1-hour TTL) the base input price.

---

### 18. Cache Diagnostics

The Cache Diagnostics API (beta) tells you **why** a cache miss occurred.

**Beta header:** `cache-diagnosis-2026-04-07`

```python
# First call
response1 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    extra_headers={"anthropic-beta": "cache-diagnosis-2026-04-07"},
    system=[
        {
            "type": "text",
            "text": "You are an expert Python developer... " * 100,
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": "What is a list comprehension?"}],
)

message_id = response1.id  # Store the message ID

# Second call — pass previous_message_id for diagnostics
response2 = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    extra_headers={"anthropic-beta": "cache-diagnosis-2026-04-07"},
    diagnostics={"previous_message_id": message_id},
    system=[
        {
            "type": "text",
            "text": "You are an expert Python developer... " * 100,
            "cache_control": {"type": "ephemeral"},
        }
    ],
    messages=[{"role": "user", "content": "What is a decorator?"}],
)

# If cache miss, the response includes:
# cache_miss_reason explaining why (expired, content_changed, etc.)
```

#### Common Cache Miss Reasons

| Reason | Meaning |
|---|---|
| `ttl_expired` | Cache entry's TTL elapsed |
| `content_changed` | The cached prefix was modified |
| `model_not_supporting` | The model doesn't support caching |
| `request_too_small` | Cached prefix below 1,024 token minimum |
| `cache_not_found` | No matching cache entry exists |

---

## Part 7: Context & Files

### 19. Context Compaction

Context compaction automatically summarizes older conversation turns when approaching the context window limit. This enables effectively infinite conversations.

**Beta header:** `compact-2026-01-12`  
**Supported on:** Opus 4.7, Opus 4.6, Sonnet 4.6

#### Basic Usage

```python
messages = [{"role": "user", "content": "Let's discuss the architecture for a new microservice."}]

response = client.beta.messages.create(
    betas=["compact-2026-01-12"],
    model="claude-opus-4-7",
    max_tokens=4096,
    messages=messages,
    context_management={
        "edits": [{"type": "compact_20260112"}],
    },
)

# If compaction occurred, response contains a "compaction" content block
for block in response.content:
    if block.type == "compaction":
        print(f"Compaction summary: {block.content[:200]}...")
    elif block.type == "text":
        print(block.text)
```

#### Custom Trigger Threshold

```python
response = client.beta.messages.create(
    betas=["compact-2026-01-12"],
    model="claude-opus-4-7",
    max_tokens=4096,
    messages=messages,
    context_management={
        "edits": [{
            "type": "compact_20260112",
            "trigger": {
                "type": "input_tokens",
                "value": 100000,  # Compact at 100K tokens (default: 150K, minimum: 50K)
            },
        }],
    },
)
```

#### Pause After Compaction

When `pause_after_compaction: True`, Claude stops after generating the compaction block (`stop_reason="compaction"`). You can then add additional content before continuing.

```python
response = client.beta.messages.create(
    betas=["compact-2026-01-12"],
    model="claude-opus-4-7",
    max_tokens=4096,
    messages=messages,
    context_management={
        "edits": [{
            "type": "compact_20260112",
            "pause_after_compaction": True,
        }],
    },
)

if response.stop_reason == "compaction":
    # We can now add important recent messages before continuing
    messages.append({"role": "assistant", "content": response.content})

    # Add a note about what to preserve
    messages.append({
        "role": "user",
        "content": "IMPORTANT: Remember we decided to use PostgreSQL as the database."
    })

    # Continue the conversation...
```

#### Custom Compaction Instructions

```python
response = client.beta.messages.create(
    betas=["compact-2026-01-12"],
    model="claude-opus-4-7",
    max_tokens=4096,
    messages=messages,
    context_management={
        "edits": [{
            "type": "compact_20260112",
            "instructions": """When compacting, prioritize:
1. Technical decisions and architecture choices
2. Code snippets and their explanations
3. User preferences and constraints
4. Open questions and action items

De-prioritize: casual conversation, repeated information, resolved questions.""",
        }],
    },
)
```

#### Compaction with Prompt Caching

When compaction runs, it can write the summary to cache:

```python
response = client.beta.messages.create(
    betas=["compact-2026-01-12"],
    model="claude-opus-4-7",
    max_tokens=4096,
    messages=messages,
    context_management={
        "edits": [{
            "type": "compact_20260112",
            "cache_control": {"type": "ephemeral"},  # Cache the compaction summary
        }],
    },
)
```

---

### 20. Files API

The Files API lets you upload and manage files for use in Messages API requests without re-uploading each time.

#### Upload a File

```python
from anthropic import Anthropic

client = Anthropic()

# Upload a text file
with open("large_document.txt", "rb") as f:
    file = client.files.create(
        file=("large_document.txt", f, "text/plain"),
        purpose="messages",  # "messages" or "fine-tune"
    )

print(f"File ID: {file.id}")
print(f"Filename: {file.filename}")
print(f"Size: {file.bytes} bytes")
print(f"Created: {file.created_at}")
```

#### List Files

```python
files = client.files.list()
for f in files:
    print(f"{f.id}: {f.filename} ({f.bytes} bytes)")

# With pagination
files = client.files.list(limit=10, after="file_abc123")
```

#### Retrieve a File

```python
file = client.files.retrieve("file_abc123")
print(file.filename, file.purpose)
```

#### Delete a File

```python
client.files.delete("file_abc123")
```

#### Using Uploaded Files in Messages

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=2048,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "file",
                "file_id": "file_abc123",  # Reference by ID
            },
            {
                "type": "text",
                "text": "Summarize this document in 3 bullet points.",
            },
        ],
    }],
)
```

#### Supported File Types

- `text/plain`
- `application/pdf`
- `image/jpeg`
- `image/png`
- `image/gif`
- `image/webp`
- `text/html`
- `application/json`
- `text/csv`

---

### 21. Token Counting API

Estimate token usage before making a call. Useful for cost estimation and staying within context limits.

**Endpoint:** `POST https://api.anthropic.com/v1/messages/count_tokens`

```python
# Count tokens for a message
response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="You are a helpful assistant.",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
)

print(f"Input tokens: {response.input_tokens}")
```

#### Counting with Tools

```python
response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    system="You are a helpful assistant.",
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather?"}],
)

print(f"Tokens including tools: {response.input_tokens}")
```

#### Counting with Images

```python
import base64

with open("large_image.png", "rb") as f:
    image_data = base64.standard_b64encode(f.read()).decode()

response = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {"type": "base64", "media_type": "image/png", "data": image_data},
            },
            {"type": "text", "text": "Describe this image."},
        ],
    }],
)

print(f"Tokens (including image): {response.input_tokens}")
```

#### Pre-Flight Cost Estimation

```python
def estimate_cost(model, input_tokens, predicted_output_tokens=None):
    pricing = {
        "claude-opus-4-7": (5.00, 25.00),
        "claude-sonnet-4-6": (3.00, 15.00),
        "claude-haiku-4-5": (1.00, 5.00),
    }

    input_price, output_price = pricing[model]

    input_cost = (input_tokens / 1_000_000) * input_price

    if predicted_output_tokens:
        output_cost = (predicted_output_tokens / 1_000_000) * output_price
        return input_cost + output_cost

    return input_cost

# Estimate
token_count = client.messages.count_tokens(
    model="claude-sonnet-4-6",
    messages=[...],
)

estimated = estimate_cost("claude-sonnet-4-6", token_count.input_tokens, 500)
print(f"Estimated cost: ${estimated:.4f}")
```

---

## Part 8: Managed Agents (Beta)

### 22. Agents, Environments & Sessions

Managed Agents provide a fully managed, sandboxed agent harness with built-in tools. Claude manages the agentic loop — you just send tasks and read results.

**Beta header:** `managed-agents-2026-04-01`

#### Core Concepts

| Concept | API Endpoint | Purpose |
|---|---|---|
| **Agent** | `POST /v1/agents` | Versioned config: model, system prompt, tools, skills |
| **Environment** | `POST /v1/environments` | Sandboxed execution runtime (cloud VMs) |
| **Session** | `POST /v1/sessions` | A single conversation/execution instance |
| **Thread** | Within a session | Per-subagent execution context |

#### Creating an Agent

```python
from anthropic import Anthropic

client = Anthropic(
    default_headers={"anthropic-beta": "managed-agents-2026-04-01"},
)

agent = client.beta.agents.create(
    name="Data Analyst Agent",
    model="claude-sonnet-4-6",
    system="You are a data analyst. Use Python to analyze data and create visualizations.",
    tools=[
        {"type": "code_execution_20250825"},
        {"type": "web_search_20260209"},
    ],
    description="Analyzes datasets and produces summary reports with plots.",
)

print(f"Agent ID: {agent.id}")  # agent_abc123
```

#### Creating an Environment

```python
environment = client.beta.environments.create(
    name="Data Analysis Sandbox",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},  # Allows internet access
    },
)

print(f"Environment ID: {environment.id}")  # env_xyz789
```

#### Creating a Session

```python
# Using bare string — uses the latest agent version
session = client.beta.sessions.create(
    agent="agent_abc123",
    environment_id="env_xyz789",
    title="Sales Q1 2026 Analysis",
)

# Using a pinned version
session = client.beta.sessions.create(
    agent={"type": "agent", "id": "agent_abc123", "version": 1},
    environment_id="env_xyz789",
    title="Sales Q1 2026 Analysis",
)

print(f"Session ID: {session.id}")
print(f"Status: {session.status}")  # "idle"
```

#### Session Statuses

| Status | Meaning |
|---|---|
| `idle` | Waiting for input; created sessions start here |
| `running` | Actively executing a task |
| `rescheduling` | Transient error, automatically retrying |
| `terminated` | Unrecoverable error — session is dead |

#### Listing & Managing Sessions

```python
# List all sessions
sessions = client.beta.sessions.list(limit=20)
for s in sessions:
    print(f"{s.id}: {s.title} [{s.status}]")

# Get a specific session
session = client.beta.sessions.retrieve("session_xyz")

# Update session metadata
client.beta.sessions.update("session_xyz", title="Updated Title")

# Archive (preserves history, prevents new events)
client.beta.sessions.archive("session_xyz")

# Delete (permanently — must not be running)
client.beta.sessions.delete("session_xyz")
```

---

### 23. Session Events & SSE Streaming

Sessions are driven by events. You send events (user messages, tool results) and receive events (agent messages, tool use requests, status changes) via an SSE stream.

#### Sending Events and Streaming Responses

```python
session = client.beta.sessions.create(
    agent="agent_abc123",
    environment_id="env_xyz789",
)

with client.beta.sessions.events.stream(session.id) as stream:
    # Send a user message
    client.beta.sessions.events.send(
        session.id,
        events=[{
            "type": "user.message",
            "content": [
                {"type": "text", "text": "Analyze this sales data and create a trend chart:"},
                {"type": "text", "text": "Month,Sales\nJan,12000\nFeb,15000\nMar,11000\nApr,18000\nMay,20000\nJun,17000"},
            ],
        }],
    )

    # Read events from the stream
    for event in stream:
        match event.type:
            case "agent.message":
                for block in event.content:
                    if block.get("type") == "text":
                        print(block["text"], end="")

            case "agent.tool_use":
                print(f"\n[Tool: {event.tool_name}]")

            case "agent.tool_result":
                print(f"[Tool result received]")

            case "session.status_idle":
                print("\n[Agent finished]")
                break

            case "session.status_terminated":
                print(f"\n[Error: {event.error}]")
                break
```

#### Key Event Types

| Event | Direction | Description |
|---|---|---|
| `user.message` | You → Agent | A user message to process |
| `agent.message` | Agent → You | Text content from the agent |
| `agent.tool_use` | Agent → You | Agent is calling a built-in tool |
| `agent.custom_tool_use` | Agent → You | Agent is calling your custom tool |
| `agent.tool_result` | Agent → You | Tool execution completed |
| `session.status_idle` | System | Agent is done, waiting for input |
| `session.status_running` | System | Agent is actively working |
| `session.status_rescheduling` | System | Transient error, retrying |
| `session.status_terminated` | System | Unrecoverable error |
| `error` | System | Stream-level error |

#### Polling Events (Alternative to Streaming)

```python
# List past events (paginated)
events = client.beta.sessions.events.list(
    session_id="session_xyz",
    limit=50,
)

for event in events:
    print(f"[{event.type}]")
```

#### Multi-Agent Threads

When an agent spawns sub-agents, each runs in its own thread:

```python
# List threads in a session
threads = client.beta.sessions.threads.list("session_xyz")
for thread in threads:
    print(f"Thread: {thread.id}, Status: {thread.status}")

# Stream events from a specific thread
with client.beta.sessions.threads.events.stream(
    session_id="session_xyz",
    thread_id="thread_abc",
) as thread_stream:
    for event in thread_stream:
        print(f"[Thread {event.thread_id}] {event.type}")

# Archive a thread
client.beta.sessions.threads.archive("session_xyz", "thread_abc")
```

#### Custom Tool Integration

```python
def handle_tool_call(tool_name: str, input: dict) -> dict:
    """Your custom tool handler."""
    if tool_name == "query_database":
        return run_query(input["sql"])
    elif tool_name == "send_email":
        return send_email(**input)
    raise ValueError(f"Unknown tool: {tool_name}")

# In the event loop:
for event in stream:
    if event.type == "agent.custom_tool_use":
        result = handle_tool_call(event.tool_name, event.input)

        # Send the result back
        client.beta.sessions.events.send(
            session.id,
            events=[{
                "type": "custom_tool_result",
                "tool_use_id": event.tool_use_id,
                "content": str(result),
            }],
        )
```

---

### 24. Session Resources & Webhooks

#### Attaching Resources to Sessions

```python
# Attach a file
client.beta.sessions.resources.add(
    session_id="session_xyz",
    resource={
        "type": "file",
        "file_id": "file_abc123",
    },
)

# Attach a GitHub repository
client.beta.sessions.resources.add(
    session_id="session_xyz",
    resource={
        "type": "github_repository",
        "owner": "my-org",
        "repo": "my-repo",
        "branch": "main",
    },
)

# Attach a memory store
client.beta.sessions.resources.add(
    session_id="session_xyz",
    resource={
        "type": "memory_store",
        "memory_store_id": "mem_xyz789",
    },
)
```

#### Listing and Managing Resources

```python
resources = client.beta.sessions.resources.list("session_xyz")
for r in resources:
    print(f"{r.type}: {r.id}")

# Get specific resource
resource = client.beta.sessions.resources.get("session_xyz", "res_abc")

# Update resource
client.beta.sessions.resources.update("session_xyz", "res_abc", metadata={"label": "v2"})

# Remove resource
client.beta.sessions.resources.delete("session_xyz", "res_abc")
```

#### Webhooks

Managed Agents can send webhook events when session state changes:

```python
# Configure webhook when creating an agent
agent = client.beta.agents.create(
    name="Webhook-Aware Agent",
    model="claude-sonnet-4-6",
    webhook_config={
        "url": "https://my-app.example.com/webhooks/claude",
        "secret": "whsec_abc123def456",  # For HMAC signature verification
        "events": [
            "session.status_idle",
            "session.status_terminated",
            "agent.tool_use",
        ],
    },
)

# On your server, verify webhook signatures:
import hmac
import hashlib

def verify_webhook(body: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## Part 9: Agent Skills

### 25. Writing & Using Skills

Agent Skills package reusable instructions, scripts, and resources into modular bundles. Claude loads them via progressive disclosure — metadata first, full content only when needed.

#### Skill Structure

A skill is a folder containing at minimum a `SKILL.md` file:

```
my-skill/
├── SKILL.md          # Instructions + YAML frontmatter (REQUIRED)
├── scripts/
│   └── analyze.py    # Optional: executable scripts
├── templates/
│   └── report.j2     # Optional: Jinja2 templates
└── data/
    └── reference.csv  # Optional: static data / docs
```

#### SKILL.md Format

```markdown
---
name: data-analyzer
description: Analyze CSV/JSON datasets with pandas. Generates summary stats, plots, and written reports. Use when the user asks to analyze data, find patterns, or create charts.
---

# Data Analyzer Skill

## When to Use
- User uploads or references a dataset (CSV, JSON, Excel)
- User asks for statistical analysis, trends, correlations
- User wants charts or visualizations

## When NOT to Use
- Simple data format conversion (use a simpler approach)
- Real-time streaming data analysis
- Analyzing code or configuration files

## Workflow
1. **Load** the data with pandas
2. **Profile**: Show shape, dtypes, missing values, summary statistics
3. **Analyze**: Identify trends, outliers, correlations
4. **Visualize**: Create at least one relevant chart with matplotlib
5. **Report**: Write a concise summary of findings

## Code Conventions
- Use `import pandas as pd` and `import matplotlib.pyplot as plt`
- Handle missing values explicitly — never drop silently
- Use `df.head()` to preview before operations
```

#### Invoking a Skill via API

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    skills=[
        {
            "type": "skill",
            "path": "/path/to/my-skill",  # Local path
        }
    ],
    messages=[{
        "role": "user",
        "content": "Analyze the trends in this sales data: [CSV data here]",
    }],
)
```

#### Versioning Skills

```python
# Pin a skill at a specific version
skills_config = [
    {
        "type": "skill",
        "path": "/path/to/skills/data-analyzer",
        "version": "v1.2.0",  # SemVer
    }
]
```

#### Skills with Code Execution

Skills often need code execution capability:

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    tools=[{"type": "code_execution_20250825"}],  # Enable code exec
    skills=[
        {"type": "skill", "path": "/path/to/data-analyzer"},
    ],
    messages=[{"role": "user", "content": "..."}],
)
```

---

### 26. Progressive Disclosure

Progressive disclosure is the mechanism by which Claude efficiently uses Skills without bloating the context window.

#### How It Works

1. **Registration**: Skills are registered with their paths
2. **Metadata scan**: Claude reads only the YAML frontmatter (`name` + `description`) from each SKILL.md
3. **Selection**: Claude picks relevant skills based on the task
4. **Full load**: Only selected skills have their complete content loaded into context
5. **Execution**: Claude follows the skill instructions

#### Designing for Progressive Disclosure

**Good — narrow, descriptive metadata:**

```yaml
---
name: sales-report-generator
description: Generate structured sales reports from CRM data exports. Creates Excel workbooks with charts. Use when the user provides a CSV export from Salesforce and asks for a report, dashboard, or analysis.
---
```

**Bad — vague metadata:**

```yaml
---
name: helper
description: Helps with stuff.
---
```

#### Composability Pattern

Design skills to work independently and in combination:

```python
# Skills can be combined
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4096,
    skills=[
        {"type": "skill", "path": "/path/to/data-loader"},     # Loads data
        {"type": "skill", "path": "/path/to/data-analyzer"},   # Analyzes it
        {"type": "skill", "path": "/path/to/report-writer"},   # Generates report
    ],
    messages=[{"role": "user", "content": "..."}],
)
```

Each skill does one job. Claude composes them as needed.

#### Skill Best Practices

1. **One skill = one capability** — don't create mega-skills
2. **Precise name + description** — include negative triggers ("Don't use when...")
3. **Use scripts for determinism** — Python scripts for math, data processing, file generation
4. **Keep SKILL.md lean** — link to deeper docs, don't dump everything
5. **Test each skill independently** before composing
6. **Version pin in production** — avoid surprises from skill changes

---

## Part 10: Administration & Operations

### 27. Models API

List available models, their capabilities, and deprecation schedules.

```python
# List all available models
models = client.models.list()
for model in models:
    print(f"{model.id}: context={model.context_window}, max_output={model.max_output_tokens}")

# Get a specific model
model = client.models.retrieve("claude-opus-4-7")
print(f"Model: {model.id}")
print(f"Context window: {model.context_window}")
print(f"Max output: {model.max_output_tokens}")
print(f"Deprecation date: {model.deprecation_date}")
print(f"Supports vision: {model.supports_vision}")
print(f"Supports thinking: {model.supports_thinking}")
print(f"Supports caching: {model.supports_prompt_caching}")
```

#### Active Models (May 2026)

```python
# Best for the most complex tasks
"claude-opus-4-7"    # 1M context, 128K output, adaptive thinking

# Near-Opus quality, more parameter control
"claude-opus-4-6"    # 1M context, 128K output, extended + adaptive thinking

# Best balance — recommended default
"claude-sonnet-4-6"  # 1M context, 64K output, all features

# Fast and cheap for simple tasks
"claude-haiku-4-5"   # 200K context, 8K output, no thinking
```

#### Upcoming Deprecations

| Model | Retirement Date |
|---|---|
| Claude Sonnet 4.0 | June 15, 2026 |
| Claude Opus 4.0 | June 15, 2026 |
| Claude Haiku 3.0 | Already retired (April 20, 2026) |
| Claude Sonnet 3.7 | Already retired (February 19, 2026) |

---

### 28. Usage & Cost API

Track token consumption and costs programmatically.

```python
import datetime

# Get usage for a date range
usage = client.usage.get(
    start_date=datetime.date(2026, 5, 1),
    end_date=datetime.date(2026, 5, 27),
)

print(f"Total tokens: {usage.total_tokens}")
print(f"Total cost: ${usage.total_cost:.2f}")

# Breakdown by model
for model_usage in usage.by_model:
    print(f"{model_usage.model}: {model_usage.tokens} tokens, ${model_usage.cost:.2f}")

# Breakdown by workspace
for workspace in usage.by_workspace:
    print(f"{workspace.name}: {workspace.tokens} tokens, ${workspace.cost:.2f}")

# Breakdown by API key (when applicable)
for key_usage in usage.by_api_key:
    print(f"Key {key_usage.api_key_id}: {key_usage.tokens} tokens")
```

---

### 29. Data Residency

Control which geographic region processes your inference requests.

```python
# Process inference in the US only
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    inference_geo="us",
    messages=[{"role": "user", "content": "Hello"}],
)

# Available regions:
# "us" — United States (1.1x pricing for models post-Feb 1, 2026)
# "eu" — Europe (where available)

# Default: no geographic restriction (processed in nearest available region)
```

---

### 30. Service Tiers

Choose between standard (reserved capacity) and auto (flex capacity) service tiers.

```python
# Auto tier (default): may use flexible capacity for lower latency
response = client.messages.create(service_tier="auto", ...)

# Standard only: always uses reserved capacity
# Guarantees availability but may have higher latency when busy
response = client.messages.create(service_tier="standard_only", ...)
```

| Tier | Availability | Latency | Best For |
|---|---|---|---|
| `auto` (default) | Flexible capacity | Lowest | Most use cases |
| `standard_only` | Reserved only | May queue | Production, guaranteed capacity |

---

### 31. Fast Mode

Dramatically faster output on Opus 4.7 by optimizing for speed.

**Beta header:** `fast-mode-2026-02-01`

```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    extra_headers={"anthropic-beta": "fast-mode-2026-02-01"},
    speed="fast",
    messages=[{"role": "user", "content": "Explain the theory of relativity."}],
)
```

Fast Mode reduces latency significantly while maintaining quality on most tasks. It's ideal for:
- Interactive chat applications
- Real-time agentic workflows
- High-throughput production systems

Note: Fast Mode may slightly reduce reasoning depth on the most complex tasks. For research-level problems, use the default speed.

---

## Part 11: Batch Processing & Reliability

### 32. Batch API

Send large volumes of requests asynchronously at **50% discount**. Perfect for evaluation runs, content generation at scale, and offline processing.

**Endpoint:** `POST https://api.anthropic.com/v1/messages/batches`

#### Creating a Batch

```python
import json
import time

# Step 1: Prepare requests as JSONL
requests = []
for i in range(100):
    requests.append(json.dumps({
        "custom_id": f"request-{i}",
        "params": {
            "model": "claude-haiku-4-5",  # Cheapest for bulk work
            "max_tokens": 256,
            "messages": [
                {"role": "user", "content": f"Summarize document #{i}: ..."}
            ],
        },
    }))

# Write to JSONL file
with open("batch_requests.jsonl", "w") as f:
    f.write("\n".join(requests))

# Step 2: Upload and create batch
with open("batch_requests.jsonl", "rb") as f:
    batch = client.messages.batches.create(
        requests=("batch_requests.jsonl", f),
    )

print(f"Batch ID: {batch.id}")
print(f"Status: {batch.processing_status}")  # "in_progress"
```

#### Checking Batch Status

```python
batch = client.messages.batches.retrieve("msgbatch_abc123")
print(f"Status: {batch.processing_status}")

# Possible statuses:
# "in_progress" — still processing
# "ended" — completed (check results)
# "canceled" — you canceled it
# "expired" — TTL expired before completion
```

#### Polling Until Complete

```python
batch_id = "msgbatch_abc123"

while True:
    batch = client.messages.batches.retrieve(batch_id)
    status = batch.processing_status

    if status == "ended":
        print("Batch complete!")
        break
    elif status in ("canceled", "expired"):
        print(f"Batch {status}")
        break

    print(f"Progress: {batch.request_counts}")
    # {"processing": 45, "succeeded": 30, "errored": 2, "canceled": 0, "expired": 0}
    time.sleep(30)
```

#### Retrieving Results

```python
# Get the results file
results = client.messages.batches.results("msgbatch_abc123")

# Results is an iterable of (custom_id, result) pairs
for custom_id, result in results:
    if result.type == "succeeded":
        text = result.result.message.content[0].text
        print(f"{custom_id}: {text[:100]}...")
    else:
        print(f"{custom_id}: ERROR — {result.error}")
```

#### Batch Limits

| Constraint | Limit |
|---|---|
| Max requests per batch | 10,000 |
| Max batch size (file) | 200 MB |
| Batch TTL | 24 hours |
| Max concurrent batches | Varies by tier |

#### Batch Pricing

Batches cost **50% less** than synchronous API calls:

| Model | Batch Input | Batch Output |
|---|---|---|
| Opus 4.7 | $2.50/MTok | $12.50/MTok |
| Sonnet 4.6 | $1.50/MTok | $7.50/MTok |
| Haiku 4.5 | $0.50/MTok | $2.50/MTok |

---

### 33. Error Handling & Retries

#### Error Types

```python
from anthropic import (
    Anthropic,
    APIError,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    ConflictError,
    InternalServerError,
)

def safe_call(client, **kwargs):
    try:
        return client.messages.create(**kwargs)
    except RateLimitError as e:
        # 429 — too many requests
        retry_after = float(e.response.headers.get("Retry-After", 10))
        print(f"Rate limited. Retry after {retry_after}s")
        time.sleep(retry_after)
        return safe_call(client, **kwargs)

    except (APIConnectionError, APITimeoutError) as e:
        # Network issues — retry
        print(f"Connection/timeout error: {e}")
        time.sleep(2)
        return safe_call(client, **kwargs)

    except InternalServerError as e:
        # 5xx — Anthropic server error, retry
        print(f"Server error: {e}")
        time.sleep(5)
        return safe_call(client, **kwargs)

    except BadRequestError as e:
        # 400 — your fault, don't retry
        print(f"Bad request: {e.body}")
        raise

    except AuthenticationError:
        # 401 — bad API key
        print("Invalid API key!")
        raise

    except PermissionDeniedError:
        # 403 — no access to this model/feature
        print("Permission denied. Check your plan.")
        raise

    except APIError as e:
        # Catch-all for other API errors
        print(f"API error: {e}")
        raise
```

#### Exponential Backoff Pattern

```python
import random

def call_with_backoff(client, max_retries=5, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except (RateLimitError, InternalServerError, APIConnectionError) as e:
            if attempt == max_retries - 1:
                raise

            # Exponential backoff with jitter
            delay = min(2 ** attempt + random.uniform(0, 1), 60)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
            time.sleep(delay)
        except (BadRequestError, AuthenticationError, PermissionDeniedError):
            raise  # Don't retry client errors
```

#### Handling Overloaded Errors

The `overloaded_error` (HTTP 529) means Anthropic's servers are under heavy load:

```python
try:
    response = client.messages.create(...)
except APIStatusError as e:
    if e.status_code == 529:
        print("Anthropic servers overloaded. Waiting 30s...")
        time.sleep(30)
        # Retry with backoff
```

#### Error Response Structure

```json
{
    "type": "error",
    "error": {
        "type": "invalid_request_error",
        "message": "`max_tokens` is required"
    }
}
```

---

### 34. Idempotency

Idempotency keys prevent duplicate processing when you safely retry a request. If the same key is used within 24 hours, the original response is returned instead of re-processing.

```python
import uuid

request_id = str(uuid.uuid4())

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "What is the capital of France?"}],
    extra_headers={
        "Idempotency-Key": request_id,
    },
)

# If this request times out but was actually processed by the server,
# retrying with the same Idempotency-Key returns the original response:
# (HTTP 200 with the cached response, not a duplicate charge)
```

#### When to Use Idempotency

| Use Idempotency | Don't Use |
|---|---|
| POST requests that mutate state or cost money | GET or read-only requests |
| Payment-related operations | Streaming requests (not supported) |
| Database writes triggered by API output | Requests with unique content each time |
| Production systems where duplicates are harmful | |
| When you implement automatic retry logic | |

#### Idempotency Key Requirements

- Must be unique per request (use UUIDs)
- Max 255 characters
- Valid for 24 hours (after which a key can be reused)
- If a request with a previously-used key differs from the original, you get a `400` error

```python
def safe_create_message(client, messages, model, max_tokens, **kwargs):
    """Create a message with automatic retry and idempotency."""
    key = str(uuid.uuid4())

    for attempt in range(3):
        try:
            return client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=messages,
                extra_headers={"Idempotency-Key": key},
                **kwargs,
            )
        except (APIConnectionError, APITimeoutError, InternalServerError) as e:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)
        except (RateLimitError) as e:
            if attempt == 2:
                raise
            retry_after = float(e.response.headers.get("Retry-After", 10))
            time.sleep(retry_after)
        # Don't retry on 4xx errors
```

---

### 35. Rate Limits & Throttling

#### Rate Limit Tiers (Post-May 2026 Update)

| Tier | Input Tokens/Min | Notes |
|---|---|---|
| Tier 1 | 500,000 ITPM | New accounts |
| Tier 2 | 2,000,000 ITPM | After some usage history |
| Tier 3 | 5,000,000 ITPM | Higher volume |
| Tier 4 | 10,000,000 ITPM | Enterprise |

Output token throughput also increases proportionally with tier.

#### Checking Your Current Limits

Rate limit headers are present in every response:

```python
response = client.messages.create(...)

# Check the response headers
print(response._response.headers.get("anthropic-ratelimit-input-tokens-limit"))
print(response._response.headers.get("anthropic-ratelimit-input-tokens-remaining"))
print(response._response.headers.get("anthropic-ratelimit-input-tokens-reset"))
print(response._response.headers.get("anthropic-ratelimit-output-tokens-limit"))
print(response._response.headers.get("anthropic-ratelimit-output-tokens-remaining"))
print(response._response.headers.get("anthropic-ratelimit-output-tokens-reset"))
```

#### Token Bucket Queuing Pattern

```python
import threading
import queue
import time
from dataclasses import dataclass

@dataclass
class RateLimitState:
    input_remaining: int
    input_reset: float  # Unix timestamp
    output_remaining: int
    output_reset: float

    @classmethod
    def from_response(cls, response):
        headers = response._response.headers
        return cls(
            input_remaining=int(headers.get("anthropic-ratelimit-input-tokens-remaining", 0)),
            input_reset=float(headers.get("anthropic-ratelimit-input-tokens-reset", 0)),
            output_remaining=int(headers.get("anthropic-ratelimit-output-tokens-remaining", 0)),
            output_reset=float(headers.get("anthropic-ratelimit-output-tokens-reset", 0)),
        )

class RateLimitedClient:
    def __init__(self, api_key):
        self.client = Anthropic(api_key=api_key)
        self.state = RateLimitState(0, 0, 0, 0)
        self.lock = threading.Lock()

    def create_message(self, **kwargs):
        with self.lock:
            # Estimate tokens for this request
            estimated_input = 1000  # Better: use count_tokens()

            # Check if we need to wait
            now = time.time()
            if self.state.input_remaining < estimated_input and now < self.state.input_reset:
                wait = self.state.input_reset - now + 1
                print(f"Rate limit approaching. Waiting {wait:.1f}s...")
                time.sleep(wait)

        # Make the call
        response = self.client.messages.create(**kwargs)

        # Update state
        with self.lock:
            self.state = RateLimitState.from_response(response)

        return response
```

#### When Rate Limited

Always check the `Retry-After` header and respect it:

```python
except RateLimitError as e:
    retry_after = int(e.response.headers.get("Retry-After", 10))
    print(f"Rate limited. Waiting {retry_after}s...")
    time.sleep(retry_after + 1)  # Add 1s buffer
```

#### Avoiding Rate Limits

1. **Use prompt caching** — reduces input tokens per request
2. **Batch non-urgent work** via the Batch API
3. **Monitor headers** and implement client-side throttling BEFORE getting 429s
4. **Distribute load over time** — don't spike
5. **Use smaller models** (Haiku) for high-throughput classification/extraction
6. **Request a tier upgrade** when your usage consistently approaches limits

---

## Part 12: Examples

### 36. Complete Working Examples

All examples below are complete, runnable Python scripts. Each is self-contained and demonstrates a specific feature of the Claude API.

**Requirements:**
```bash
pip install anthropic python-dotenv
```

**Setup:** Create a `.env` file with your API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

All examples are in the [`examples/`](./examples/) directory. See the individual files for full source code.

| # | File | Feature | Key Concepts |
|---|---|---|---|
| 1 | `01_basic_chat.py` | First API Call | Messages API, system prompt, response parsing |
| 2 | `02_multi_turn_conversation.py` | Multi-Turn Chat | Maintaining message history, context |
| 3 | `03_streaming.py` | Streaming | `text_stream`, SSE events, `get_final_message()` |
| 4 | `04_streaming_with_thinking.py` | Streaming + Thinking | `thinking_delta`, `text_delta`, event loop |
| 5 | `05_custom_tool_use.py` | Tool Use | Tool definition, `tool_use` loop, `tool_result` |
| 6 | `06_parallel_tool_calls.py` | Parallel Tools | Independent tool calls, `disable_parallel_tool_use` |
| 7 | `07_builtin_web_search.py` | Web Search & Fetch | `web_search_20260209`, `web_fetch_20260209` |
| 8 | `08_builtin_code_execution.py` | Code Execution | `code_execution_20250825`, server_tool_use |
| 9 | `09_text_editor_bash.py` | Text Editor & Bash | File create/view/edit, shell commands |
| 10 | `10_extended_thinking.py` | Adaptive Thinking | `effort` levels, budget tokens, model differences |
| 11 | `11_interleaved_thinking.py` | Interleaved Thinking | Thinking between tool calls, agentic loop |
| 12 | `12_prompt_caching.py` | Prompt Caching | `cache_control`, cache hits, cost savings |
| 13 | `13_vision_image_analysis.py` | Vision (Images) | Base64 images, URL images, multi-image |
| 14 | `14_vision_pdf.py` | Vision (PDF) | PDF as image, multi-page, analysis |
| 15 | `15_structured_output.py` | Structured Outputs | JSON mode, `json_schema`, `strict` mode |
| 16 | `16_citations.py` | Citations | Document citations, `citation` blocks |
| 17 | `17_prefill_assistant.py` | Pre-filling | Partial assistant response, format control |
| 18 | `18_context_compaction.py` | Context Compaction | Auto-summarization, custom triggers |
| 19 | `19_files_api.py` | Files API | Upload, list, reference, delete files |
| 20 | `20_token_counting.py` | Token Counting | `count_tokens`, cost estimation |
| 21 | `21_batch_processing.py` | Batch API | JSONL, batch creation, polling, results |
| 22 | `22_error_retry_idempotency.py` | Error Handling | Backoff, idempotency keys, error types |
| 23 | `23_managed_agents_session.py` | Managed Agents | Agents, environments, sessions, SSE |
| 24 | `24_agent_skills.py` | Agent Skills | SKILL.md, skill invocation |
| 25 | `25_full_agentic_loop.py` | Full Agentic Loop | Thinking + tools + web search + code exec |

---

## Quick Reference

### Common Patterns

#### Python SDK Import Convention

```python
import anthropic
from anthropic import Anthropic

client = Anthropic()  # reads ANTHROPIC_API_KEY from env
```

#### Minimal Working Call

```python
import anthropic
client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
)
print(response.content[0].text)
```

#### Streaming Call

```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}],
) as stream:
    for text in stream.text_stream:
        print(text, end="")
```

#### Tool Use Loop

```python
messages = [{"role": "user", "content": "..."}]
while True:
    resp = client.messages.create(model=..., max_tokens=..., tools=..., messages=messages)
    messages.append({"role": "assistant", "content": resp.content})
    if resp.stop_reason == "end_turn":
        break
    results = execute_tools(resp.content)
    messages.append({"role": "user", "content": results})
```

#### Thinking on Opus 4.7

```python
response = client.messages.create(
    model="claude-opus-4-7",
    max_tokens=4096,
    thinking={"type": "adaptive"},
    output_config={"effort": "high"},
    messages=[{"role": "user", "content": "..."}],
)
```

#### With Caching

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    system=[{"type": "text", "text": "...", "cache_control": {"type": "ephemeral"}}],
    messages=[{"role": "user", "content": "..."}],
)
```

---

## Appendix: Migration Notes

### Opus 4.6 → Opus 4.7

| Feature | Opus 4.6 | Opus 4.7 |
|---|---|---|
| Thinking | `thinking: {"type": "enabled", "budget_tokens": N}` | `thinking: {"type": "adaptive"}` with `output_config.effort` |
| Temperature | `temperature: 0.7` | **Removed** |
| `top_p` / `top_k` | Supported | **Removed** |
| Vision | Up to 1,568px | Up to 2,576px |
| Tokenizer | Legacy | New tokenizer |
| Output control | Sampling params | `effort` only |

---

*Document version: 1.0 — May 2026. All features documented against the Anthropic API as of May 2026. Examples in the `examples/` directory target the live Anthropic API.*
