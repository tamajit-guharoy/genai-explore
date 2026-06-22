# Chapter 06 — Single-Step Tool Use

## What You'll Learn

- How to define a tool with its JSON schema and Python implementation
- How to parse the model's `tool_use` content block
- How to execute the function and return the result
- The complete request-response-result cycle in code
- Error handling when the model doesn't call a tool

---

## The Goal

Before we build the full agentic loop, we need to handle the simplest case: the model calls **one tool**, we execute it, and we return the result. No multi-step reasoning, no parallel calls — just the fundamental pattern.

---

## Defining a Tool

A "tool" in our harness is two things paired together:

| Component | What It Does | Where It Lives |
|---|---|---|
| **JSON Schema** | Tells the model WHAT the function does and WHAT arguments it needs | Sent to the API |
| **Python Function** | Actually DOES the work | Runs in our harness |

They must stay in sync. If the schema says the parameter is `city` but your Python function expects `location`, the model will call it correctly but your function will crash.

---

## The Code

```python
# ═══════════════════════════════════════════════════
# CHAPTER 06 — Single-Step Tool Use
# ═══════════════════════════════════════════════════
import anthropic

# ═══ STEP 1: Create the client ═══
client = anthropic.Anthropic(
    api_key="sk-ant-..."  # Replace with your key
)

# ═══════════════════════════════════════════════════
# STEP 2: Define a tool — SCHEMA + FUNCTION
# ═══════════════════════════════════════════════════

# ── 2a: The Python function (what actually runs) ──
# This is a regular Python function. Nothing special about it.
# It takes keyword arguments matching the schema's properties.
# It can do ANYTHING — call an API, read a file, query a database, compute.
def get_weather(city: str, units: str = "celsius") -> str:
    """
    Get the current weather for a city.
    
    In a real app, this would call a weather API (OpenWeatherMap, etc.).
    For the tutorial, we return simulated data so you can run it offline.
    """
    # Simulated weather database — in production, replace with API call
    weather_db = {
        "tokyo":       {"temp": 22, "conditions": "Sunny", "humidity": 60},
        "london":      {"temp": 15, "conditions": "Cloudy", "humidity": 75},
        "new york":    {"temp": 28, "conditions": "Partly cloudy", "humidity": 55},
        "san francisco": {"temp": 18, "conditions": "Foggy", "humidity": 80},
    }
    
    # Normalize the city name for lookup (lowercase, strip whitespace)
    city_key = city.lower().strip()
    
    if city_key not in weather_db:
        # Return a helpful error as a STRING — the model can read this
        # and explain to the user that the city wasn't found.
        # NEVER raise an exception here unless you catch it in the harness.
        available = ", ".join(weather_db.keys())
        return f"City '{city}' not found. Available cities: {available}"
    
    data = weather_db[city_key]
    
    # Convert temperature if needed
    if units == "fahrenheit":
        temp = data["temp"] * 9/5 + 32
        unit_symbol = "°F"
    else:
        temp = data["temp"]
        unit_symbol = "°C"
    
    return (f"{city.title()}: {temp:.0f}{unit_symbol}, "
            f"{data['conditions']}, {data['humidity']}% humidity")


# ── 2b: The JSON Schema (tells the model how to call it) ──
# This schema is sent to the API as part of the 'tools' parameter.
# The model uses it to decide: (a) whether to call this tool, and
# (b) what arguments to pass.
# 
# CRITICAL: The schema keys (name, description, input_schema) are
# Anthropic-specific. OpenAI uses a different format — see Chapter 05.
get_weather_schema = {
    "name": "get_weather",         # Must match the function name
    "description": (
        "Get the current weather for a city. "
        "Returns temperature, conditions, and humidity."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "The city name, e.g. 'Tokyo' or 'San Francisco'"
            },
            "units": {
                "type": "string",
                "enum": ["celsius", "fahrenheit"],  # Model can only pick from these
                "description": "Temperature unit (default: celsius)"
            }
        },
        "required": ["city"]  # The model MUST provide a city
    }
}

# ═══════════════════════════════════════════════════
# STEP 3: The tool registry
# ═══════════════════════════════════════════════════
# A registry maps tool names → (function, schema).
# In Chapter 07, this will grow to multiple tools.
# For now, it's just one entry — but the pattern scales.
TOOL_REGISTRY = {
    "get_weather": (get_weather, get_weather_schema)
}


# ═══════════════════════════════════════════════════
# STEP 4: The harness function
# ═══════════════════════════════════════════════════
def chat_with_tools(user_message: str) -> str:
    """
    Send a message, handle ONE tool call if the model makes one,
    return the final text response.
    
    This is a SINGLE-STEP tool handler — it handles at most one
    round of tool calling. For multi-step, see Chapter 07.
    """
    
    # ── 4a: Build the tools list from the registry ──
    # Extract just the schemas (the second element of each tuple).
    # We send ALL schemas to the model — it decides which (if any) to use.
    tool_schemas = [schema for _, schema in TOOL_REGISTRY.values()]
    
    # ── 4b: First model call (model may or may not use a tool) ──
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tool_schemas,  # ← THE KEY ADDITION: tool schemas
        messages=[
            {"role": "user", "content": user_message}
        ]
    )
    
    # ═══════════════════════════════════════════════
    # STEP 5: Check if the model wants to use a tool
    # ═══════════════════════════════════════════════
    # The model's response can contain:
    #   - A text block only (stop_reason="end_turn") → no tool needed
    #   - A tool_use block (stop_reason="tool_use") → execute the tool
    
    # ── 5a: Case 1 — No tool call, just text ──
    # If the model doesn't call a tool, we just return the text.
    # This happens when the question doesn't require external data.
    if response.stop_reason == "end_turn":
        # The response was purely text — no tools needed
        return response.content[0].text
    
    # ── 5b: Case 2 — Model wants to use a tool ──
    # We need to find the tool_use block in the content array.
    # There might be BOTH a text block ("Let me check...") and a tool_use block.
    # We only care about the tool_use block here.
    
    # Find all tool_use blocks in the response
    tool_use_blocks = [
        block for block in response.content
        if block.type == "tool_use"
    ]
    
    if not tool_use_blocks:
        # This shouldn't happen if stop_reason=="tool_use", but guard anyway
        return "Error: model indicated tool_use but no tool_use block found"
    
    # For single-step, we only handle the first tool call
    tool_block = tool_use_blocks[0]
    
    # ── 5c: Extract tool call details ──
    tool_name = tool_block.name        # e.g., "get_weather"
    tool_id = tool_block.id            # e.g., "toolu_01XyZ..."
    tool_input = tool_block.input      # e.g., {"city": "Tokyo"} — already a dict!
    
    print(f"\n[TOOL CALL] {tool_name}({tool_input})")
    
    # ── 5d: Look up and execute the function ──
    # The registry maps tool names to (function, schema) tuples.
    # We extract the function and call it with **tool_input to unpack
    # the dict as keyword arguments.
    if tool_name not in TOOL_REGISTRY:
        result = f"Error: unknown tool '{tool_name}'"
    else:
        try:
            func, _ = TOOL_REGISTRY[tool_name]
            # **tool_input unpacks {"city": "Tokyo"} → func(city="Tokyo")
            result = func(**tool_input)
        except Exception as e:
            # Catch ALL exceptions — a crashed tool should produce a result
            # string the model can understand, not a traceback.
            result = f"Error executing {tool_name}: {str(e)}"
    
    print(f"[TOOL RESULT] {result}")
    
    # ═══════════════════════════════════════════════
    # STEP 6: Send the tool result back to the model
    # ═══════════════════════════════════════════════
    # We build a new messages array that includes:
    #   1. The original user message
    #   2. The model's response (with the tool_use block)
    #   3. The tool result
    
    final_response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=tool_schemas,
        messages=[
            # The original user message
            {"role": "user", "content": user_message},
            
            # The model's response (with the tool_use block)
            # This MUST be included so the model knows what it asked for
            {"role": "assistant", "content": response.content},
            
            # The tool result — note the content structure!
            # It's a list of content blocks, each with type "tool_result"
            {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tool_id,  # Echo back the tool_use ID
                        "content": result         # The function's return value
                    }
                ]
            }
        ]
    )
    
    # ── 6a: Return the final text response ──
    # After receiving the tool result, the model synthesizes a final answer.
    return final_response.content[0].text


# ═══════════════════════════════════════════════════
# STEP 7: Demo
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    # Test 1: A question that needs the weather tool
    print("=" * 60)
    print("TEST 1: Tool-required question")
    print("=" * 60)
    result = chat_with_tools("What's the weather in Tokyo?")
    print(f"\nFINAL ANSWER: {result}")
    
    # Test 2: A question that doesn't need any tool
    print("\n" + "=" * 60)
    print("TEST 2: No-tool question")
    print("=" * 60)
    result = chat_with_tools("What's the capital of France?")
    print(f"\nFINAL ANSWER: {result}")
    
    # Test 3: Fahrenheit units
    print("\n" + "=" * 60)
    print("TEST 3: Tool with optional parameter")
    print("=" * 60)
    result = chat_with_tools("What's the weather in London in Fahrenheit?")
    print(f"\nFINAL ANSWER: {result}")
```

---

## Sample Output

```
============================================================
TEST 1: Tool-required question
============================================================

[TOOL CALL] get_weather({'city': 'Tokyo'})
[TOOL RESULT] Tokyo: 22°C, Sunny, 60% humidity

FINAL ANSWER: It's currently 22°C (about 72°F) and sunny in Tokyo with 
60% humidity. Perfect weather for going out!

============================================================
TEST 2: No-tool question
============================================================

FINAL ANSWER: The capital of France is Paris.

============================================================
TEST 3: Tool with optional parameter
============================================================

[TOOL CALL] get_weather({'city': 'London', 'units': 'fahrenheit'})
[TOOL RESULT] London: 59°F, Cloudy, 75% humidity

FINAL ANSWER: London is 59°F, cloudy, with 75% humidity. 
Classic London weather — you'll want a jacket!
```

---

## Key Patterns to Remember

### 1. The Tool Result Content Block Structure

This is the #1 thing people get wrong. The tool result MUST use this exact structure:

```python
{
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": tool_id,   # ← MUST match the tool_use block's ID
            "content": result          # ← The function return value as a string
        }
    ]
}
```

Not `{"role": "tool_use_result", ...}` — that doesn't exist.  
Not `{"role": "assistant", ...}` — tool results use `"user"`.  
Not a plain string for content — it must be a list with the `tool_result` block.

### 2. Error Handling Inside Tools

Your tool functions should **return error strings, not raise exceptions**:

```python
# ✅ GOOD: The model can understand this
def my_tool(x):
    if x < 0:
        return "Error: x must be positive"
    return do_work(x)

# ❌ BAD: This crashes the harness
def my_tool(x):
    if x < 0:
        raise ValueError("x must be positive")
    return do_work(x)
```

If you DO raise exceptions, catch them in the harness (see step 5d above). But it's cleaner to return error strings and let the model decide how to present them to the user.

### 3. The Assistant Response Must Include the tool_use Block

When you send the tool result back, you MUST include the model's previous response (with the tool_use block) as an assistant message. If you don't, the model "forgets" that it asked for the tool and gets confused about why it's receiving a result.

---

## What's Next

This chapter handles exactly ONE tool call. But real agents need multiple tools, multiple calls, and a loop that keeps going until the task is done. That's Chapter 07 — the agentic loop.

---

**Previous:** [05 — Tool Calling: The Big Idea](05_tool_calling_big_idea.md)  
**Next:** [07 — The Agentic Loop](07_the_agentic_loop.md)
