#!/usr/bin/env python3
"""
Example 17: Pre-filling the Assistant Response

Demonstrates how to pre-fill the assistant's response to steer Claude's output
toward a specific format, such as JSON, code blocks, or tool_use blocks.

Key concepts:
- Pre-filling with {"role": "assistant", "content": "..."} in the messages list
- Forcing JSON output by starting the assistant's JSON response
- Forcing code-only output by starting a code block
- Pre-filling a tool_use block to force Claude to use a specific tool
- Claude continues naturally from where the pre-fill left off
"""

import os
import json
import time
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = "claude-sonnet-4-20250514"

    print("=" * 72)
    print("EXAMPLE 1: Pre-fill to force JSON output")
    print("=" * 72)

    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": "List 3 popular Python web frameworks. Return ONLY valid JSON "
                           "with keys: name, creator, year_released.",
            },
            {
                # Pre-fill the opening brace so Claude knows we want JSON
                "role": "assistant",
                "content": "{\n  \"frameworks\": [",
            },
        ],
    )

    prefill = '{\n  "frameworks": ['
    continuation = response.content[0].text
    full_text = prefill + continuation

    print(f"Pre-fill prefix : {prefill}")
    print(f"Claude continued: {continuation}")
    print(f"Full JSON       :")
    try:
        parsed = json.loads(full_text)
        print(json.dumps(parsed, indent=2))
    except json.JSONDecodeError as e:
        print(f"(partial JSON — {e})")
        print(full_text)
    print()

    # ── Example 2 ──────────────────────────────────────────────────────────

    print("=" * 72)
    print("EXAMPLE 2: Pre-fill to force code-only response")
    print("=" * 72)

    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": "Write a Python function that computes the nth Fibonacci "
                           "number. Return ONLY the code, no explanation.",
            },
            {
                # Pre-fill the opening of a Python code block
                "role": "assistant",
                "content": "```python\n",
            },
        ],
    )

    prefill_code = "```python\n"
    continuation = response.content[0].text
    full_code = prefill_code + continuation

    print(f"Pre-fill prefix : {repr(prefill_code)}")
    print(f"Claude continued: {continuation}")
    print(f"Full response:")
    print(full_code)
    print()

    # ── Example 3 ──────────────────────────────────────────────────────────

    print("=" * 72)
    print("EXAMPLE 3: Pre-fill a tool_use block to force tool selection")
    print("=" * 72)

    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "units": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
        {
            "name": "get_time",
            "description": "Get the current time in a city",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                },
                "required": ["location"],
            },
        },
    ]

    tool_use_id = f"toolu_{int(time.time())}"

    response = client.messages.create(
        model=model,
        max_tokens=500,
        tools=tools,
        messages=[
            {
                "role": "user",
                "content": "What's the weather like in Tokyo right now, and what time is it there?",
            },
            {
                # Pre-fill a tool_use block to force Claude to call get_weather first
                "role": "assistant",
                "content": [
                    {
                        "type": "tool_use",
                        "id": tool_use_id,
                        "name": "get_weather",
                        "input": {"location": "Tokyo", "units": "celsius"},
                    },
                ],
            },
        ],
    )

    print(f"Pre-filled tool_use block forced Claude to call 'get_weather'.")
    print(f"Claude's response after the pre-filled tool call:\n")

    for block in response.content:
        if block.type == "text":
            print(f"  [text]: {block.text}")
        elif block.type == "tool_use":
            print(f"  [tool_use] name={block.name}, id={block.id}")
            print(f"              input: {json.dumps(block.input, indent=16)}")
        elif block.type == "tool_result":
            print(f"  [tool_result] id={block.id}")

    print()
    print("The pre-filled tool_use block appears in the assistant turn just like a")
    print("real tool call. Claude may follow it with additional tool calls or text.")


if __name__ == "__main__":
    main()
