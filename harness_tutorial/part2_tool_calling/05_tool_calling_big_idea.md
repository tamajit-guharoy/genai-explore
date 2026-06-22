# Chapter 05 — Tool Calling: The Big Idea

## What You'll Learn

- What tool calling actually is beneath the marketing
- The mental model: model as manager, tools as specialists
- The raw API exchange: exactly what gets sent and received
- How tool calling differs between Anthropic (tool_use blocks) and OpenAI (function calls)
- Why structured tool-use blocks are better than JSON-in-a-string

---

## The Manager Analogy

The best mental model for tool calling isn't technical — it's organizational:

> **The LLM is a manager sitting in an office. Tools are specialists she can call on the phone.**

The manager (model) has a Rolodex of specialists (tools) with their phone numbers (function names) and what they need to know to help (parameter schemas). When a task comes in:

```
┌──────────────────────────────────────────────────────────┐
│  User: "What's the weather in Tokyo and should I pack?  │
│         Also, convert 72°F to Celsius."                  │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Manager (LLM): "Hmm, I need two specialists."           │
│                                                          │
│  📞 Calls get_weather(city="Tokyo")                      │
│     → Specialist replies: "22°C, sunny, 60% humidity"   │
│                                                          │
│  📞 Calls convert_temperature(value=72, from="F", to="C")│
│     → Specialist replies: "22.2°C"                       │
│                                                          │
│  Manager (LLM): "Tokyo is 22°C and sunny. 72°F is about  │
│                  22°C — so it's actually the same temp!   │
│                  You probably don't need heavy layers."   │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

The manager doesn't DO the work. She coordinates. She knows WHO to call and how to interpret their results. That's exactly what tool calling enables.

---

## What Tool Calling ACTUALLY Is

Forget the marketing. At the protocol level, tool calling is three things:

1. **A JSON Schema** you send to the model describing available functions
2. **A structured response** from the model specifying which function to call and with what arguments
3. **A loop** where you execute the function and feed the result back

That's it. No magic. Just JSON.

---

## The Raw API Exchange

Let's look at exactly what gets sent and received. This is the "see the matrix" moment:

### What YOU Send to Anthropic

```json
{
  "model": "claude-sonnet-4-20250514",
  "max_tokens": 1024,
  "tools": [
    {
      "name": "get_weather",
      "description": "Get the current weather for a city. Returns temperature, conditions, and humidity.",
      "input_schema": {
        "type": "object",
        "properties": {
          "city": {
            "type": "string",
            "description": "The city name, e.g. 'Tokyo' or 'San Francisco'"
          },
          "units": {
            "type": "string",
            "enum": ["celsius", "fahrenheit"],
            "description": "Temperature unit (default: celsius)"
          }
        },
        "required": ["city"]
      }
    }
  ],
  "messages": [
    {
      "role": "user",
      "content": "What's the weather in Tokyo?"
    }
  ]
}
```

### What Anthropic Returns (When the Model Wants to Use a Tool)

```json
{
  "id": "msg_01AbCdEfGhIjKlMnOp",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "Let me check the weather in Tokyo for you."
    },
    {
      "type": "tool_use",
      "id": "toolu_01XyZAbCdEfGhIjKl",
      "name": "get_weather",
      "input": {
        "city": "Tokyo",
        "units": "celsius"
      }
    }
  ],
  "stop_reason": "tool_use",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 350,
    "output_tokens": 45
  }
}
```

Key observations:

- **`content` is an array** with TWO blocks: a `text` block ("Let me check...") AND a `tool_use` block
- **`stop_reason` is `"tool_use"`**, not `"end_turn"` — this is how you know there's more work to do
- **The `tool_use` block has an `id`** — you MUST echo this back when returning results (the model uses it to match results to calls)
- **`input` is a JSON object** matching the schema you defined — already parsed, not a string

### What YOU Send Back (Tool Result)

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_01XyZAbCdEfGhIjKl",
      "content": "Tokyo: 22°C, Sunny, 60% humidity"
    }
  ]
}
```

Notice: the role is `"user"` but the content type is `"tool_result"`. This is Anthropic's convention — tool results are "injected" into the conversation as if the user provided them.

### What Anthropic Returns (Final Text Response)

```json
{
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "It's currently 22°C (about 72°F) and sunny in Tokyo with 60% humidity. Pretty pleasant weather!"
    }
  ],
  "stop_reason": "end_turn"
}
```

Now `stop_reason` is `"end_turn"` — the model is done. No more tools to call.

---

## Anthropic vs. OpenAI: Tool Calling Formats

This is a frequent source of confusion. Both providers support tool calling, but the formats are different:

| Aspect | Anthropic | OpenAI |
|---|---|---|
| **Schema location** | `tools` parameter (array of tool defs) | `tools` parameter (array of tool defs) |
| **Tool definition** | `name`, `description`, `input_schema` | `type: "function"`, `function: {name, description, parameters}` |
| **Response format** | Typed `content` blocks: `{"type": "tool_use", ...}` | `tool_calls` array on the message object |
| **Result format** | `{"type": "tool_result", "tool_use_id": ..., "content": ...}` | `{"role": "tool", "tool_call_id": ..., "content": ...}` |
| **Parallel calls** | Multiple `tool_use` blocks in one `content` array | Multiple entries in `tool_calls` array |
| **Streaming** | Content block deltas with `content_block_start` / `content_block_delta` events | Function call deltas with `tool_call_delta` events |

### Why We Use Anthropic in This Tutorial

Anthropic's typed content blocks are structurally superior for harness engineering:

- **No JSON parsing** — `tool_use.input` is already a Python dict, not a JSON string you have to `json.loads()`
- **Text + tool_use coexistence** — the model can explain what it's doing (text block) while also making tool calls (tool_use block) in the same response
- **Explicit tool_use_id** — every tool call has a unique ID that you echo back; no ambiguity about which result matches which call

---

## The Full Flow, Visualized

```
┌──────────┐     ┌───────────┐     ┌──────────┐
│  USER    │     │  HARNESS  │     │  MODEL   │
└────┬─────┘     └─────┬─────┘     └────┬─────┘
     │                 │                │
     │ "Weather in     │                │
     │  Tokyo?"        │                │
     │────────────────>│                │
     │                 │  messages +    │
     │                 │  tools schema  │
     │                 │───────────────>│
     │                 │                │
     │                 │  tool_use:     │
     │                 │  get_weather   │
     │                 │  (city="Tokyo")│
     │                 │<───────────────│
     │                 │                │
     │                 │──┐ call Python │
     │                 │  │ function    │
     │                 │<─┘ "22°C, sun" │
     │                 │                │
     │                 │  tool_result + │
     │                 │  messages      │
     │                 │───────────────>│
     │                 │                │
     │                 │  text: "It's   │
     │                 │  22°C and      │
     │                 │  sunny!"       │
     │                 │<───────────────│
     │                 │                │
     │  "It's 22°C     │                │
     │   and sunny!"   │                │
     │<────────────────│                │
```

---

## What's Coming

In Chapter 06, we'll implement a single tool call — define a `get_weather` function, register it with the model, parse the response, execute it, and return the result. One tool, one call, one result.

In Chapter 07, we'll build **the agentic loop** — the full multi-step cycle where the model can call multiple tools across multiple turns until it has everything it needs.

---

**Previous:** [04 — System Prompts & Personality](04_system_prompts_personality.md)  
**Next:** [06 — Single-Step Tool Use](06_single_step_tool_use.md)
