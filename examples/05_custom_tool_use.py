#!/usr/bin/env python3
"""
05_custom_tool_use.py — Custom Tool Use (Function Calling)

Demonstrates how to define tools and implement the full tool-use loop:
  1. Define tool schemas for get_weather and calculate
  2. Send a message with `tools` parameter
  3. Detect tool_use blocks in the response
  4. Execute the tool (mock implementation)
  5. Return tool_result via a new user message with role: user + content
     containing a tool_result block
  6. Repeat until Claude responds with stop_reason: "end_turn"

This is the most common pattern for giving Claude access to external data
or APIs.

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 05_custom_tool_use.py
"""

from dotenv import load_dotenv
import anthropic
from anthropic.types import (
    ToolUseBlock,
    TextBlock,
    ToolResultBlockParam,
)
import os
import json

load_dotenv()


# ── Mock tool implementations ──────────────────────────────────────────────

def get_weather(location: str, unit: str = "celsius") -> str:
    """Mock weather lookup — returns hardcoded data."""
    data = {
        "San Francisco, CA": {"celsius": 18, "fahrenheit": 64, "condition": "Foggy"},
        "New York, NY":      {"celsius": 22, "fahrenheit": 72, "condition": "Sunny"},
        "London, UK":        {"celsius": 12, "fahrenheit": 54, "condition": "Rainy"},
        "Tokyo, Japan":      {"celsius": 20, "fahrenheit": 68, "condition": "Cloudy"},
    }
    loc = data.get(location, {"celsius": 25, "fahrenheit": 77, "condition": "Unknown"})
    temp = loc[unit.lower()]
    return json.dumps({
        "location": location,
        "temperature": temp,
        "unit": unit,
        "condition": loc["condition"],
    })


def calculate(expression: str) -> str:
    """Safely evaluate a mathematical expression."""
    allowed = {"abs", "int", "float", "round", "min", "max", "sum", "pow"}
    try:
        # Use a restricted eval for demonstration — only basic arithmetic.
        result = eval(expression, {"__builtins__": {}}, {})
        return json.dumps({"expression": expression, "result": result})
    except Exception as e:
        return json.dumps({"expression": expression, "error": str(e)})


# ── Tool schemas ───────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and state/country, e.g. 'San Francisco, CA'",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit",
                },
            },
            "required": ["location"],
        },
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A mathematical expression like '2 + 2' or '15 * 3'",
                },
            },
            "required": ["expression"],
        },
    },
]


# ── Tool dispatcher ────────────────────────────────────────────────────────

def execute_tool(name: str, input_data: dict) -> str:
    """Dispatch a tool call to the correct implementation."""
    print(f"  >> Executing tool: {name}({json.dumps(input_data)})")
    if name == "get_weather":
        return get_weather(**input_data)
    elif name == "calculate":
        return calculate(**input_data)
    else:
        return json.dumps({"error": f"Unknown tool: {name}"})


def main() -> None:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                "What's the weather like in San Francisco and New York? "
                "Also, what is 245 * 137?"
            ),
        }
    ]

    print("=" * 60)
    print("CUSTOM TOOL USE — FULL LOOP")
    print("=" * 60)
    print(f"User: {messages[0]['content']}")
    print()

    max_tool_rounds = 10  # safety limit
    turn_count = 0

    while turn_count < max_tool_rounds:
        turn_count += 1
        print(f"--- Turn {turn_count} ---")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=TOOLS,
            messages=messages,
        )

        # Check the stop reason
        print(f"  Stop reason: {response.stop_reason}")

        # Process each content block
        for block in response.content:
            if isinstance(block, TextBlock):
                print(f"\n[Assistant text block]:\n{block.text}\n")

            elif isinstance(block, ToolUseBlock):
                print(f"\n[Tool use: {block.name}] id={block.id}")
                print(f"  Input: {json.dumps(block.input, indent=2)}")

                # Execute the tool
                result = execute_tool(block.name, dict(block.input))
                print(f"  Result: {result}")

        # If Claude stopped because it wants to use a tool, continue the loop.
        if response.stop_reason == "tool_use":
            # Append the assistant response (which contains tool_use blocks)
            # and then a user message with the tool_result(s).
            assistant_content: list = []
            tool_result_content: list[ToolResultBlockParam] = []

            for block in response.content:
                if isinstance(block, ToolUseBlock):
                    assistant_content.append({"type": "tool_use", "id": block.id,
                                              "name": block.name,
                                              "input": dict(block.input)})
                    result = execute_tool(block.name, dict(block.input))
                    tool_result_content.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })
                elif isinstance(block, TextBlock):
                    assistant_content.append({"type": "text", "text": block.text})

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_result_content})
            print("\n  >>> Sending tool results back to Claude...\n")
        else:
            # end_turn or max_tokens — done
            print(f"\n  Conversation complete (stop_reason={response.stop_reason})")
            break

    # Print the final synthesized answer
    print()
    print("=" * 60)
    print("FINAL SYNTHESIZED ANSWER")
    print("=" * 60)
    for block in response.content:
        if isinstance(block, TextBlock):
            print(block.text)
    print("=" * 60)


if __name__ == "__main__":
    main()
