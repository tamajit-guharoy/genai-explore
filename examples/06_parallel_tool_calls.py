#!/usr/bin/env python3
"""
06_parallel_tool_calls.py — Parallel Tool Calls

Demonstrates two aspects of tool calling with multiple independent tools:
  1. PARALLEL (default): Claude can invoke multiple tools in a single response.
     We execute them concurrently with ThreadPoolExecutor and return results
     as a single tool_result array.
  2. SEQUENTIAL: How to disable parallel tool calls so Claude calls one at a
     time using disable_parallel_tool_use=True on each tool.

Tools: get_weather, get_time, get_stock_price (all mock implementations).

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 06_parallel_tool_calls.py
"""

from dotenv import load_dotenv
import anthropic
from anthropic.types import (
    ToolUseBlock,
    TextBlock,
    ToolResultBlockParam,
)
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
from datetime import datetime

load_dotenv()


# ── Mock tool implementations ──────────────────────────────────────────────

def get_weather(location: str, unit: str = "celsius") -> str:
    """Mock weather lookup."""
    data = {
        "San Francisco, CA": {"celsius": 18, "fahrenheit": 64, "condition": "Foggy"},
        "New York, NY":      {"celsius": 22, "fahrenheit": 72, "condition": "Sunny"},
        "London, UK":        {"celsius": 12, "fahrenheit": 54, "condition": "Rainy"},
    }
    loc_data = data.get(location, {"celsius": 25, "fahrenheit": 77, "condition": "Unknown"})
    temp = loc_data[unit.lower()]
    return json.dumps({
        "location": location,
        "temperature": temp,
        "unit": unit,
        "condition": loc_data["condition"],
    })


def get_time(timezone: str = "UTC") -> str:
    """Mock time lookup — returns current time formatted for the timezone."""
    # In a real implementation you'd use pytz; here we just return a mock.
    mock_times = {
        "America/New_York":  "10:30 AM EDT",
        "America/Los_Angeles": "7:30 AM PDT",
        "Europe/London":     "3:30 PM BST",
        "Asia/Tokyo":        "11:30 PM JST",
        "UTC":               "14:30 UTC",
    }
    t = mock_times.get(timezone, f"14:30 {timezone.split('/')[-1]}")
    return json.dumps({"timezone": timezone, "local_time": t,
                       "requested_at": datetime.utcnow().isoformat()})


def get_stock_price(symbol: str) -> str:
    """Mock stock price lookup."""
    prices = {
        "AAPL": 198.50,
        "GOOGL": 175.20,
        "MSFT": 420.80,
        "AMZN": 185.30,
        "TSLA": 245.60,
    }
    price = prices.get(symbol.upper(), 100.00)
    return json.dumps({
        "symbol": symbol.upper(),
        "price": price,
        "currency": "USD",
        "change_pct": round((price - 100) / 100 * 100, 2),
    })


# ── Tool schemas ───────────────────────────────────────────────────────────

TOOLS_PARALLEL = [
    {
        "name": "get_weather",
        "description": "Get the current weather for a location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {"type": "string"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
            },
            "required": ["location"],
        },
    },
    {
        "name": "get_time",
        "description": "Get the current local time for a timezone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "timezone": {
                    "type": "string",
                    "description": "Timezone like 'America/New_York' or 'Europe/London'",
                },
            },
            "required": ["timezone"],
        },
    },
    {
        "name": "get_stock_price",
        "description": "Get the current stock price for a ticker symbol.",
        "input_schema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock ticker symbol like 'AAPL' or 'GOOGL'",
                },
            },
            "required": ["symbol"],
        },
    },
]

# Same tools but with disable_parallel_tool_use=True
TOOLS_SEQUENTIAL = [
    {**tool, "disable_parallel_tool_use": True}
    for tool in TOOLS_PARALLEL
]


# ── Tool dispatcher ────────────────────────────────────────────────────────

TOOL_IMPLS = {
    "get_weather": get_weather,
    "get_time": get_time,
    "get_stock_price": get_stock_price,
}

def execute_tool(name: str, input_data: dict) -> str:
    impl = TOOL_IMPLS.get(name)
    if impl is None:
        return json.dumps({"error": f"Unknown tool: {name}"})
    print(f"    Executing {name}... ", end="", flush=True)
    result = impl(**input_data)
    print("done")
    return result


def demo_parallel(client: anthropic.Anthropic) -> None:
    """Claude calls multiple tools at once; we execute them in parallel."""
    print("\n" + "=" * 60)
    print("DEMO 1: PARALLEL TOOL CALLS (default)")
    print("=" * 60)

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                "Get me the weather in San Francisco, the current time in Tokyo, "
                "and the stock price for Apple (AAPL)."
            ),
        }
    ]

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=TOOLS_PARALLEL,
        messages=messages,
    )

    # Check how many tool_use blocks we got
    tool_blocks = [b for b in response.content if isinstance(b, ToolUseBlock)]
    text_blocks = [b for b in response.content if isinstance(b, TextBlock)]

    print(f"Claude responded with {len(tool_blocks)} tool call(s) and "
          f"{len(text_blocks)} text block(s).")
    print(f"Stop reason: {response.stop_reason}")
    print()

    # Execute all tool calls in parallel
    print("Executing tool calls in parallel:")
    results: list[ToolResultBlockParam] = []
    tool_use_blocks: list[ToolUseBlock] = []

    for block in response.content:
        if isinstance(block, ToolUseBlock):
            tool_use_blocks.append(block)

    with ThreadPoolExecutor(max_workers=5) as executor:
        fut_to_block = {
            executor.submit(execute_tool, block.name, dict(block.input)): block
            for block in tool_use_blocks
        }
        for future in as_completed(fut_to_block):
            block = fut_to_block[future]
            result = future.result()
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result,
            })
    print()

    # Build assistant content and send results back
    assistant_content = []
    for block in response.content:
        if isinstance(block, TextBlock):
            assistant_content.append({"type": "text", "text": block.text})
        elif isinstance(block, ToolUseBlock):
            assistant_content.append({
                "type": "tool_use",
                "id": block.id,
                "name": block.name,
                "input": dict(block.input),
            })

    messages.append({"role": "assistant", "content": assistant_content})
    messages.append({"role": "user", "content": results})

    final = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        tools=TOOLS_PARALLEL,
        messages=messages,
    )

    print("Final synthesized answer:")
    for block in final.content:
        if isinstance(block, TextBlock):
            print(f"  {block.text}")


def demo_sequential(client: anthropic.Anthropic) -> None:
    """With disable_parallel_tool_use=True, Claude calls one tool at a time."""
    print("\n" + "=" * 60)
    print("DEMO 2: SEQUENTIAL TOOL CALLS (parallel disabled)")
    print("=" * 60)

    messages: list[dict] = [
        {
            "role": "user",
            "content": (
                "Get me the weather in London, the time in New York, "
                "and the MSFT stock price. Call them one at a time."
            ),
        }
    ]

    max_rounds = 10
    for turn in range(1, max_rounds + 1):
        print(f"\n--- Turn {turn} ---")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            tools=TOOLS_SEQUENTIAL,
            messages=messages,
        )

        tool_blocks = [b for b in response.content if isinstance(b, ToolUseBlock)]
        if tool_blocks:
            print(f"Claude called {len(tool_blocks)} tool(s) this turn "
                  f"(expect 1 since parallel is disabled)")

        # Build assistant content and results
        assistant_content = []
        results: list[ToolResultBlockParam] = []
        for block in response.content:
            if isinstance(block, TextBlock):
                assistant_content.append({"type": "text", "text": block.text})
                print(f"  Text: {block.text[:80]}...")
            elif isinstance(block, ToolUseBlock):
                print(f"  Tool: {block.name}({json.dumps(dict(block.input))})")
                assistant_content.append({
                    "type": "tool_use", "id": block.id,
                    "name": block.name, "input": dict(block.input),
                })
                result = execute_tool(block.name, dict(block.input))
                print(f"  Result: {result[:80]}")
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result,
                })

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": results})
        else:
            print(f"\nDone — stop_reason={response.stop_reason}")
            print("\nFinal answer:")
            for block in response.content:
                if isinstance(block, TextBlock):
                    print(f"  {block.text}")
            break


def main() -> None:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    demo_parallel(client)
    demo_sequential(client)


if __name__ == "__main__":
    main()
