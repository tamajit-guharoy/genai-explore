# Appendix B: Provider API Cheat Sheet

> **See also:** [Chapter 17: Multi-Provider Abstraction](../part5_advanced/17_multi_provider_abstraction.md)

---

## Quick Comparison Table

| Property | Anthropic | OpenAI | Gemini |
|---|---|---|---|
| **SDK Package** | `anthropic` | `openai` | `google-generativeai` |
| **Import** | `import anthropic` | `from openai import OpenAI` | `import google.generativeai as genai` |
| **API Endpoint** | `https://api.anthropic.com/v1/messages` | `https://api.openai.com/v1/chat/completions` | `generativelanguage.googleapis.com` |
| **Auth Header** | `x-api-key: sk-ant-...` | `Authorization: Bearer sk-...` | `?key=AIza...` (query param) |
| **Client Init** | `anthropic.Anthropic(api_key=...)` | `OpenAI(api_key=...)` | `genai.configure(api_key=...)` |
| **Model Param** | `model="claude-sonnet-4-20250514"` | `model="gpt-4o"` | `model_name="gemini-2.0-flash"` |
| **Max Tokens** | `max_tokens=4096` | `max_completion_tokens=4096` | `max_output_tokens=4096` |
| **Temperature** | `temperature=0.7` | `temperature=0.7` | `temperature=0.7` |
| **System Prompt** | Top-level `system=` param | In `messages` as `{"role":"system"}` | `system_instruction=` or model config |
| **Streaming** | `client.messages.stream(...)` context mgr | `stream=True` param | `stream=True` param |
| **Tool Calling** | Native `tools=` param | Native `tools=` param | Native `tools=` param |
| **Token Count** | `client.count_tokens(text)` | `tiktoken` library | `model.count_tokens(text)` |
| **Image Input** | `{"type":"image","source":{...}}` | `{"type":"image_url","image_url":{...}}` | `{"inline_data":{"mime_type":"...","data":"..."}}` |
| **Async Client** | `anthropic.AsyncAnthropic` | `openai.AsyncOpenAI` | `generate_content_async()` |

---

## Authentication

```python
# ═══ Anthropic ═══
import anthropic
client = anthropic.Anthropic(api_key="sk-ant-api03-...")
# Or set: export ANTHROPIC_API_KEY=sk-ant-...

# ═══ OpenAI ═══
from openai import OpenAI
client = OpenAI(api_key="sk-...")
# Or set: export OPENAI_API_KEY=sk-...

# ═══ Gemini ═══
import google.generativeai as genai
genai.configure(api_key="AIza...")
# Or set: export GEMINI_API_KEY=AIza...
```

---

## Basic Chat Request

```python
# ═══ Anthropic ═══
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.content[0].text)

# ═══ OpenAI ═══
response = client.chat.completions.create(
    model="gpt-4o",
    max_completion_tokens=1024,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
print(response.choices[0].message.content)

# ═══ Gemini ═══
model = genai.GenerativeModel(
    "gemini-2.0-flash",
    system_instruction="You are a helpful assistant.",
)
response = model.generate_content("Hello!")
print(response.text)
```

---

## Tool Calling

```python
# ═══ Anthropic (native tool use) ═══
tools = [{
    "name": "get_weather",
    "description": "Get current weather for a location.",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {"type": "string", "description": "City name"}
        },
        "required": ["location"],
    },
}]

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
)

# Claude returns tool_use blocks in response.content
for block in response.content:
    if block.type == "tool_use":
        print(f"Tool: {block.name}({block.input})")

# ═══ OpenAI ═══
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"],
        },
    },
}]

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
)
tc = response.choices[0].message.tool_calls[0]
print(f"Tool: {tc.function.name}({tc.function.arguments})")

# ═══ Gemini ═══
tools = [{
    "function_declarations": [{
        "name": "get_weather",
        "description": "Get current weather for a location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"}
            },
            "required": ["location"],
        },
    }],
}]

model = genai.GenerativeModel("gemini-2.0-flash", tools=tools)
response = model.generate_content("What's the weather in Tokyo?")
for part in response.candidates[0].content.parts:
    if hasattr(part, "function_call"):
        print(f"Tool: {part.function_call.name}({part.function_call.args})")
```

---

## Streaming

```python
# ═══ Anthropic ═══
with client.messages.stream(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Tell me a story."}],
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)

# ═══ OpenAI ═══
stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Tell me a story."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)

# ═══ Gemini ═══
model = genai.GenerativeModel("gemini-2.0-flash")
response = model.generate_content("Tell me a story.", stream=True)
for chunk in response:
    print(chunk.text, end="", flush=True)
```

---

## Token Counting

```python
# ═══ Anthropic ═══
count = client.count_tokens("Hello, world!")  # Returns int (Anthropic endpoint)

# ═══ OpenAI (via tiktoken) ═══
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4o")
count = len(enc.encode("Hello, world!"))

# ═══ Gemini ═══
model = genai.GenerativeModel("gemini-2.0-flash")
count = model.count_tokens("Hello, world!").total_tokens
```

---

## Async Chat (Full Example)

```python
# ═══ Anthropic ═══
import asyncio
import anthropic

async def anthropic_chat():
    client = anthropic.AsyncAnthropic()
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        messages=[{"role": "user", "content": "Hello!"}],
    )
    return response.content[0].text

# ═══ OpenAI ═══
from openai import AsyncOpenAI

async def openai_chat():
    client = AsyncOpenAI()
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    return response.choices[0].message.content

# ═══ Gemini ═══
import google.generativeai as genai

async def gemini_chat():
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = await model.generate_content_async("Hello!")
    return response.text
```

---

## Common Gotchas

| Provider | Gotcha | Fix |
|---|---|---|
| Anthropic | `tools` cannot be `None` or `[]` — use `anthropic.NOT_GIVEN` | `tools=tools_list or anthropic.NOT_GIVEN` |
| Anthropic | MUST include `description` in tool schemas | Add `"description": "What this tool does"` |
| Anthropic | System prompt is a string, not a message | Use `system="..."` param, not a message with `role="system"` |
| OpenAI | `max_tokens` is deprecated — use `max_completion_tokens` | Replace with `max_completion_tokens` |
| OpenAI | Tool call arguments are JSON strings, not dicts | `json.loads(tc.function.arguments)` |
| Gemini | Roles are "user" and "model", not "assistant" | Map `"assistant"` → `"model"` |
| Gemini | Tools wrap in `function_declarations` array | Nest all tools in one `function_declarations` |
| Gemini | No tool call IDs | Generate your own for tracking |

---

> **See also:** [Appendix C: Tool Schema Reference](C_tool_schema_reference.md) — Complete translation table
