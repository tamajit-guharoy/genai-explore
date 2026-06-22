# Appendix C: Tool Schema Reference

> **See also:** [Chapter 17: Multi-Provider Abstraction](../part5_advanced/17_multi_provider_abstraction.md) — Provider implementations  
> **See also:** [Appendix B: Provider API Cheat Sheet](B_provider_api_cheatsheet.md) — API comparison

---

## How Tool Definitions Differ Across Providers

Each provider formats tool definitions differently. Here's the same tool (`get_weather`) in all three formats:

### Anthropic Format

```json
{
    "name": "get_weather",
    "description": "Get the current weather for a location",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "City name, e.g. 'Tokyo'"
            },
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],
                "description": "Temperature unit"
            }
        },
        "required": ["location"]
    }
}
```

### OpenAI Format

```json
{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name, e.g. 'Tokyo'"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit"
                }
            },
            "required": ["location"]
        }
    }
}
```

### Gemini Format

```json
{
    "function_declarations": [
        {
            "name": "get_weather",
            "description": "Get the current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name, e.g. 'Tokyo'"
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        }
    ]
}
```

---

## Field-by-Field Translation Table

| Our Unified Field | Anthropic | OpenAI | Gemini |
|---|---|---|---|
| `name` | `name` (top-level) | `function.name` (nested) | `name` in `functionDeclarations[i]` |
| `description` | `description` | `function.description` | `description` in `functionDeclarations[i]` |
| `parameters.type` | `input_schema.type` | `function.parameters.type` | `parameters.type` |
| `parameters.properties` | `input_schema.properties` | `function.parameters.properties` | `parameters.properties` |
| `parameters.required` | `input_schema.required` | `function.parameters.required` | `parameters.required` |
| Container | Direct array of tool objects | Array of `{type, function}` objects | One object with `functionDeclarations` array |

---

## The ToolSchemaTranslator Class

```python
# ═══════════════════════════════════════════════════════════════════
# tool_schema_translator.py — Copy-paste into your project
# ═══════════════════════════════════════════════════════════════════

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolDefinition:
    """Unified tool definition — your project's single source of truth."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema


class ToolSchemaTranslator:
    """Convert unified ToolDefinitions to each provider's format."""

    @staticmethod
    def to_anthropic(tools: list[ToolDefinition]) -> list[dict]:
        """Anthropic: [{"name":..., "description":..., "input_schema":{...}}]"""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.parameters,
            }
            for t in tools
        ]

    @staticmethod
    def to_openai(tools: list[ToolDefinition]) -> list[dict]:
        """OpenAI: [{"type":"function","function":{...}}]"""
        return [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                },
            }
            for t in tools
        ]

    @staticmethod
    def to_gemini(tools: list[ToolDefinition]) -> list[dict]:
        """Gemini: [{"function_declarations": [...]}]"""
        declarations = [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in tools
        ]
        return [{"function_declarations": declarations}]

    @staticmethod
    def to_openrouter(tools: list[ToolDefinition]) -> list[dict]:
        """OpenRouter uses OpenAI-compatible format."""
        return ToolSchemaTranslator.to_openai(tools)


# ═══ Usage ═══
tools = [
    ToolDefinition(
        name="search_web",
        description="Search the internet",
        parameters={
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Search query"}},
            "required": ["query"],
        },
    ),
    ToolDefinition(
        name="calculate",
        description="Evaluate a mathematical expression",
        parameters={
            "type": "object",
            "properties": {"expression": {"type": "string", "description": "Math expression"}},
            "required": ["expression"],
        },
    ),
]

# One line per provider:
anthropic_tools = ToolSchemaTranslator.to_anthropic(tools)
openai_tools    = ToolSchemaTranslator.to_openai(tools)
gemini_tools    = ToolSchemaTranslator.to_gemini(tools)
```

---

## Tool Response Formats (Tool Results)

After executing a tool, you feed the result back. Each provider expects a different format:

### Anthropic Tool Result

```json
{
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": "toolu_01ABC123...",
            "content": "The weather in Tokyo is 24°C, partly cloudy."
        }
    ]
}
```

### OpenAI Tool Result

```json
{
    "role": "tool",
    "tool_call_id": "call_abc123",
    "content": "The weather in Tokyo is 24°C, partly cloudy."
}
```

### Gemini Tool Result

```json
{
    "role": "user",
    "parts": [
        {
            "functionResponse": {
                "name": "get_weather",
                "response": {
                    "result": "The weather in Tokyo is 24°C, partly cloudy."
                }
            }
        }
    ]
}
```

---

## Common Gotchas

### 1. Anthropic REQUIRES `description` on ALL fields

```python
# ❌ WRONG — Anthropic rejects this
{
    "name": "search",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string"}       # Missing "description"!
        }
    }
}

# ✅ CORRECT
{
    "name": "search",
    "description": "Search the web",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query"  # Required!
            }
        }
    }
}
```

### 2. Anthropic: `tools` cannot be `None`

```python
# ❌ WRONG
response = client.messages.create(tools=None, ...)  # Error!

# ✅ CORRECT
import anthropic
response = client.messages.create(tools=anthropic.NOT_GIVEN, ...)
# Or:
tools_list = [...] if has_tools else anthropic.NOT_GIVEN
```

### 3. OpenAI: tool call arguments are STRINGS, not dicts

```python
# OpenAI returns arguments as a JSON string
tc = response.choices[0].message.tool_calls[0]
args = json.loads(tc.function.arguments)  # Must parse!
```

### 4. Gemini: ALL tools go in ONE `function_declarations` array

```python
# ❌ WRONG — multiple tool objects
tools = [
    {"function_declarations": [tool1]},
    {"function_declarations": [tool2]},
]

# ✅ CORRECT — single object with all declarations
tools = [
    {"function_declarations": [tool1, tool2]},
]
```

### 5. Gemini: No tool call IDs

```python
# Gemini doesn't provide unique IDs for tool calls.
# Generate your own for tracking:
tool_call_id = f"gemini-{tool_name}-{uuid.uuid4().hex[:8]}"
```

### 6. OpenAI's `strict` mode

```python
# GPT-4o+ supports strict structured output
# When using strict: true, ALL fields must have descriptions
# and additionalProperties: false must be set
{
    "type": "function",
    "function": {
        "name": "search",
        "strict": True,                     # Enforce exact schema
        "parameters": {
            "type": "object",
            "properties": { ... },
            "required": [...],
            "additionalProperties": False,   # Required for strict mode
        }
    }
}
```

---

> **See also:** [Appendix B: Provider API Cheat Sheet](B_provider_api_cheatsheet.md) — Full API comparison
