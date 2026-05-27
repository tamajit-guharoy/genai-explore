#!/usr/bin/env python3
"""
07_builtin_web_search.py — Built-in Web Search & Web Fetch Tools

Demonstrates Claude's built-in tools for web access:
  - web_search_20260209:  Claude searches the web for recent information.
  - web_fetch_20260209:   Claude fetches and reads the content of a specific URL.

These tools are built-in to the API — no tool definitions needed. You just
pass `tool_choice` or the tools are automatically available when the model
determines it needs them (they are always enabled in the model's training).

We also demonstrate `user_location` for geo-aware search results.

The response includes server_tool_use blocks that show the status of each
tool call (pending -> completed) along with the raw search/fetch results,
plus a synthesized text answer.

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 07_builtin_web_search.py
"""

from dotenv import load_dotenv
import anthropic
from anthropic.types import (
    TextBlock,
)
import os

load_dotenv()


def main() -> None:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # ── 1. Web search example ─────────────────────────────────────────────
    print("=" * 60)
    print("BUILT-IN WEB SEARCH")
    print("=" * 60)
    print("Asking Claude to search for recent AI news...\n")

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        # The built-in web search tool is available automatically.
        # We can also explicitly request it:
        # tools=[{"type": "web_search_20260209"}],
        messages=[
            {
                "role": "user",
                "content": "Search the web for the latest news about "
                           "artificial intelligence advancements in 2026.",
            }
        ],
        # Provide location context for better search results
        user_location={
            "type": "approximate",
            "city": "San Francisco",
            "country": "United States",
            "region": "California",
        },
    )

    print("--- Content Blocks ---")
    for i, block in enumerate(response.content):
        print(f"\n  Block {i}: type={block.type}")

        if isinstance(block, TextBlock):
            print(f"  Text (first 400 chars):")
            print(f"  {block.text[:400]}...")
        elif block.type == "tool_use":
            print(f"  Tool name: {block.name}")
            print(f"  Tool input: {block.input}")
        elif block.type == "tool_result":
            print(f"  Tool result (first 300 chars): {str(block.content)[:300]}...")
        elif block.type == "server_tool_use":
            print(f"  Server tool status: {block.status}")
            print(f"  Server tool name: {block.name}")
            if hasattr(block, "input") and block.input:
                print(f"  Input: {block.input}")
        else:
            print(f"  (full block: {block})")

    print(f"\n  Stop reason: {response.stop_reason}")
    print(f"  Usage — Input: {response.usage.input_tokens}, "
          f"Output: {response.usage.output_tokens}")

    # ── 2. Web fetch example ──────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("BUILT-IN WEB FETCH")
    print("=" * 60)
    print("Asking Claude to fetch a specific URL...\n")

    response2 = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2048,
        messages=[
            {
                "role": "user",
                "content": (
                    "Fetch the content from https://www.anthropic.com and "
                    "summarize what you find on the page."
                ),
            }
        ],
    )

    print("--- Content Blocks ---")
    for i, block in enumerate(response2.content):
        print(f"\n  Block {i}: type={block.type}")

        if isinstance(block, TextBlock):
            print(f"  Text (first 500 chars):")
            print(f"  {block.text[:500]}...")
        elif block.type == "tool_use":
            print(f"  Tool name: {block.name}")
            print(f"  Tool input: {block.input}")
        elif block.type == "tool_result":
            print(f"  Tool result (first 300 chars): {str(block.content)[:300]}...")
        elif block.type == "server_tool_use":
            print(f"  Server tool status: {block.status}")
            print(f"  Server tool name: {block.name}")
            if hasattr(block, "input"):
                print(f"  Input: {block.input}")
            if hasattr(block, "output"):
                print(f"  Output (first 200 chars): {str(block.output)[:200]}...")
        else:
            print(f"  (full block: {block})")

    print(f"\n  Stop reason: {response2.stop_reason}")
    print(f"  Usage — Input: {response2.usage.input_tokens}, "
          f"Output: {response2.usage.output_tokens}")

    # ── Summary ───────────────────────────────────────────────────────────
    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Search response had {len(response.content)} content block(s).")
    print(f"Fetch response had {len(response2.content)} content block(s).")
    print()
    print("The final text blocks contain the synthesized answers.")

    # Print the final synthesized text for the search
    print()
    print("--- SEARCH FINAL ANSWER (first 600 chars) ---")
    for block in response.content:
        if isinstance(block, TextBlock):
            print(block.text[:600])
            break
    print("=" * 60)


if __name__ == "__main__":
    main()
