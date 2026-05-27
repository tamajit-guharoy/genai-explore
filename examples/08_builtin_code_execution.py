#!/usr/bin/env python3
"""
08_builtin_code_execution.py — Built-in Code Execution Tool

Demonstrates Claude's built-in code execution capability for data analysis:
  - code_execution_20250825: Claude can write and execute Python code
    (including pandas, matplotlib, etc.) in a sandboxed environment.

We provide CSV-formatted sales data and ask Claude to:
  1. Analyze the data using pandas
  2. Create a visualization using matplotlib
  3. Provide insights and recommendations

The response is streamed to show progress, including server_tool_use blocks
with status transitions (pending -> completed).

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 08_builtin_code_execution.py
"""

from dotenv import load_dotenv
import anthropic
from anthropic.types import (
    ContentBlockDeltaEvent,
    ContentBlockStartEvent,
    ContentBlockStopEvent,
    MessageStartEvent,
    MessageDeltaEvent,
    MessageStopEvent,
)
import os

load_dotenv()


# ── Sample CSV data to analyze ─────────────────────────────────────────────

SALES_CSV = """
Date,Product,Category,Units_Sold,Unit_Price,Total_Revenue,Region
2026-01-05,Laptop,Electronics,15,1200.00,18000.00,North
2026-01-12,Phone,Electronics,30,800.00,24000.00,North
2026-01-19,Tablet,Electronics,20,500.00,10000.00,North
2026-01-26,Headphones,Electronics,45,150.00,6750.00,North
2026-02-02,Laptop,Electronics,12,1200.00,14400.00,South
2026-02-09,Phone,Electronics,25,800.00,20000.00,South
2026-02-16,Tablet,Electronics,18,500.00,9000.00,South
2026-02-23,Headphones,Electronics,50,150.00,7500.00,South
2026-03-02,Laptop,Electronics,20,1200.00,24000.00,East
2026-03-09,Phone,Electronics,35,800.00,28000.00,East
2026-03-16,Tablet,Electronics,22,500.00,11000.00,East
2026-03-23,Headphones,Electronics,60,150.00,9000.00,East
2026-04-06,Laptop,Electronics,18,1200.00,21600.00,West
2026-04-13,Phone,Electronics,28,800.00,22400.00,West
2026-04-20,Tablet,Electronics,15,500.00,7500.00,West
2026-04-27,Headphones,Electronics,40,150.00,6000.00,West
"""


def main() -> None:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    print("=" * 60)
    print("BUILT-IN CODE EXECUTION — DATA ANALYSIS")
    print("=" * 60)
    print("Streaming response with code execution...\n")

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=8192,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "I have the following CSV sales data. Please:\n"
                            "1. Load it into a pandas DataFrame\n"
                            "2. Compute summary statistics by product and region\n"
                            "3. Create a matplotlib bar chart showing total revenue "
                            "by product category\n"
                            "4. Provide insights and recommendations\n\n"
                            f"```csv\n{SALES_CSV}\n```\n\n"
                            "Use the code execution tool to run the Python analysis "
                            "and show me the results."
                        ),
                    }
                ],
            }
        ],
    ) as stream:
        # Stream and show events as they arrive
        text_blocks: list[str] = [""]
        current_block_idx = 0

        for event in stream:
            if isinstance(event, MessageStartEvent):
                print(f"[Message Start] id={event.message.id[:12]}... "
                      f"model={event.message.model}")
                print(f"  Input tokens: {event.message.usage.input_tokens}")

            elif isinstance(event, ContentBlockStartEvent):
                print(f"\n[Block {event.index} Start] type={event.content_block.type}")
                if event.index >= len(text_blocks):
                    text_blocks.append("")
                current_block_idx = event.index

                # If this is a server_tool_use block, show its initial status
                if hasattr(event.content_block, "status"):
                    print(f"  Server tool status: {event.content_block.status}")

            elif isinstance(event, ContentBlockDeltaEvent):
                delta = event.delta
                # Handle text deltas
                if hasattr(delta, "text") and delta.text:
                    text_blocks[current_block_idx] += delta.text
                    print(delta.text, end="", flush=True)
                # Handle server_tool_use status updates
                elif hasattr(delta, "type") and delta.type == "server_tool_use_changed":
                    print(f"\n  [Tool status: {delta.status}]")
                    if hasattr(delta, "output") and delta.output:
                        print(f"  [Tool output preview: {str(delta.output)[:200]}...]")

            elif isinstance(event, ContentBlockStopEvent):
                print(f"\n[Block {event.index} Stop]")

                # Briefly note what we accumulated
                if current_block_idx < len(text_blocks) and text_blocks[current_block_idx]:
                    length = len(text_blocks[current_block_idx])
                    print(f"  Text length: {length} chars")

            elif isinstance(event, MessageDeltaEvent):
                print(f"\n[Message Delta] stop_reason={event.delta.stop_reason}")
                print(f"  Output tokens so far: {event.usage.output_tokens}")

            elif isinstance(event, MessageStopEvent):
                print(f"\n[Message Stop]")

    # Get the final message for accurate usage
    final = stream.get_final_message()

    print()
    print("=" * 60)
    print("FULL ANALYSIS RESULT")
    print("=" * 60)

    # Print each content block with its type
    for i, block in enumerate(final.content):
        print(f"\n--- Content Block {i} (type={block.type}) ---")
        if block.type == "text":
            # Print a shorter preview
            print(block.text)
        elif block.type == "server_tool_use":
            print(f"  Tool: {block.name}")
            print(f"  Status: {block.status}")
            if hasattr(block, "input") and block.input:
                inp_str = str(block.input)
                print(f"  Input: {inp_str[:300]}...")
            if hasattr(block, "output") and block.output:
                out_str = str(block.output)
                print(f"  Output: {out_str[:500]}...")
        else:
            print(f"  {block}")

    # Usage summary
    print()
    print("=" * 60)
    print("USAGE SUMMARY")
    print("=" * 60)
    print(f"  Model:              {final.model}")
    print(f"  Stop reason:        {final.stop_reason}")
    print(f"  Content blocks:     {len(final.content)}")
    print(f"  Input tokens:       {final.usage.input_tokens}")
    print(f"  Output tokens:      {final.usage.output_tokens}")
    print(f"  Cache creation:     "
          f"{getattr(final.usage, 'cache_creation_input_tokens', 0)}")
    print(f"  Cache read:         "
          f"{getattr(final.usage, 'cache_read_input_tokens', 0)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
