#!/usr/bin/env python3
"""
01_basic_chat.py — Simplest Claude API Call

Demonstrates the most basic usage of the Anthropic Claude API:
  - Loading the API key from a .env file via python-dotenv
  - Creating a client with anthropic.Anthropic()
  - Sending a system prompt + user message via client.messages.create()
  - Printing the text response
  - Inspecting response metadata: model, stop_reason, usage (input/output tokens)

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 01_basic_chat.py
"""

from dotenv import load_dotenv
import anthropic
import os

load_dotenv()  # reads ANTHROPIC_API_KEY from .env


def main() -> None:
    # ── 1. Create the client ──────────────────────────────────────────────
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # ── 2. Make the API call ──────────────────────────────────────────────
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system="You are a helpful assistant that speaks like a pirate.",
        messages=[
            {"role": "user", "content": "Tell me a short fun fact about the ocean."},
        ],
    )

    # ── 3. Print the text response ────────────────────────────────────────
    print("=" * 60)
    print("ASSISTANT RESPONSE")
    print("=" * 60)
    for block in response.content:
        if block.type == "text":
            print(block.text)
    print()

    # ── 4. Print response metadata ────────────────────────────────────────
    print("=" * 60)
    print("METADATA")
    print("=" * 60)
    print(f"  Model:       {response.model}")
    print(f"  Stop reason: {response.stop_reason}")
    print(f"  Stop seq:    {response.stop_sequence}")
    print()
    print(f"  Usage:")
    print(f"    Input tokens:  {response.usage.input_tokens}")
    print(f"    Output tokens: {response.usage.output_tokens}")
    print(f"    Cache creation: {getattr(response.usage, 'cache_creation_input_tokens', 0)}")
    print(f"    Cache read:     {getattr(response.usage, 'cache_read_input_tokens', 0)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
