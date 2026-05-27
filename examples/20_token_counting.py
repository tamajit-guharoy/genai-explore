#!/usr/bin/env python3
"""
Example 20: Token Counting & Cost Estimation

Demonstrates how to count tokens before sending a request using
client.messages.count_tokens(), and how to estimate API costs across
different Claude models.

Key concepts:
- client.messages.count_tokens() for simple messages
- Counting tokens with system prompts
- Counting tokens with tool definitions
- Counting tokens with images (programmatically created)
- Implementing a cost estimation function
- Comparing costs across Opus 4.7, Sonnet 4.6, and Haiku 4.5
- Printing a cost comparison table
"""

import os
import json
import math
from dotenv import load_dotenv
from anthropic import Anthropic, NOT_GIVEN

load_dotenv()

# Pricing per million tokens (USD) — as of mid 2026
# These are illustrative; check the latest pricing at anthropic.com/pricing
MODEL_PRICING = {
    "claude-opus-4-20250514": {
        "input_per_mtok": 15.00,
        "output_per_mtok": 75.00,
        "label": "Opus 4.7",
    },
    "claude-sonnet-4-20250514": {
        "input_per_mtok": 3.00,
        "output_per_mtok": 15.00,
        "label": "Sonnet 4.6",
    },
    "claude-haiku-4-20250514": {
        "input_per_mtok": 0.80,
        "output_per_mtok": 4.00,
        "label": "Haiku 4.5",
    },
}


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
    cache_read_tokens: int = 0,
    cache_write_tokens: int = 0,
) -> dict:
    """
    Estimate the cost of an API call.

    Args:
        input_tokens: Number of input (prompt) tokens.
        output_tokens: Number of output (completion) tokens.
        model: Model identifier string.
        cache_read_tokens: Tokens read from cache (90% discounted).
        cache_write_tokens: Tokens written to cache (premium).

    Returns:
        dict with estimated costs in USD.
    """
    pricing = MODEL_PRICING.get(model)
    if not pricing:
        return {"error": f"Unknown model: {model}"}

    input_per_token = pricing["input_per_mtok"] / 1_000_000
    output_per_token = pricing["output_per_mtok"] / 1_000_000

    # Cache read is 90% cheaper than base input
    cache_read_per_token = input_per_token * 0.10
    # Cache write is typically 25% more expensive than base input
    cache_write_per_token = input_per_token * 1.25

    base_input_cost = input_tokens * input_per_token
    cache_read_cost = cache_read_tokens * cache_read_per_token
    cache_write_cost = cache_write_tokens * cache_write_per_token
    output_cost = output_tokens * output_per_token

    return {
        "model_label": pricing["label"],
        "input_cost": round(base_input_cost, 6),
        "cache_read_cost": round(cache_read_cost, 6),
        "cache_write_cost": round(cache_write_cost, 6),
        "output_cost": round(output_cost, 6),
        "total_cost": round(
            base_input_cost + cache_read_cost + cache_write_cost + output_cost, 6
        ),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }


def print_cost_table(costs: list[dict]):
    """Print a formatted cost comparison table."""
    header = (
        f"{'Model':<20} {'Input $':<14} {'Output $':<14} "
        f"{'Input Tokens':<16} {'Output Tokens':<16} {'Total $':<14}"
    )
    sep = "-" * len(header)

    print()
    print("COST COMPARISON TABLE")
    print(sep)
    print(header)
    print(sep)

    for c in costs:
        if "error" in c:
            print(f"{'ERROR':<20} {c['error']}")
        else:
            print(
                f"{c['model_label']:<20} "
                f"${c['input_cost']:<12.6f} "
                f"${c['output_cost']:<12.6f} "
                f"{c['input_tokens']:<16} "
                f"{c['output_tokens']:<16} "
                f"${c['total_cost']:<12.6f}"
            )
    print(sep)
    print()


def create_sample_image_png() -> bytes:
    """
    Create a very small PNG image programmatically (1x1 red pixel).
    This produces a minimal valid PNG without external dependencies.
    """
    import struct
    import zlib

    # PNG signature
    signature = b"\\x89PNG\\r\\n\\x1a\\n"

    # IHDR chunk: 1x1 pixel, 8-bit RGB
    width, height = 1, 1
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data)
    ihdr_chunk = (
        struct.pack(">I", len(ihdr_data))
        + b"IHDR"
        + ihdr_data
        + struct.pack(">I", ihdr_crc & 0xFFFFFFFF)
    )

    # IDAT chunk: raw pixel data (filter byte 0 + RGB)
    raw_data = b"\\x00\\xff\\x00\\x00"  # filter none, red
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b"IDAT" + compressed)
    idat_chunk = (
        struct.pack(">I", len(compressed))
        + b"IDAT"
        + compressed
        + struct.pack(">I", idat_crc & 0xFFFFFFFF)
    )

    # IEND chunk
    iend_crc = zlib.crc32(b"IEND")
    iend_chunk = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc & 0xFFFFFFFF)

    return signature + ihdr_chunk + idat_chunk + iend_chunk


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print("=" * 72)
    print("TOKEN COUNTING & COST ESTIMATION")
    print("=" * 72)

    # ── 1. Count tokens for a simple message ────────────────────────────

    print("\\n>>> 1. Simple message token count")
    simple_messages = [
        {"role": "user", "content": "What is the capital of France?"}
    ]
    simple_count = client.messages.count_tokens(
        model="claude-sonnet-4-20250514",
        messages=simple_messages,
    )
    print(f"  Input messages: {simple_messages}")
    print(f"  Input tokens:   {simple_count.input_tokens}")
    simple_input_tokens = simple_count.input_tokens
    print()

    # ── 2. Count tokens with system prompt ─────────────────────────────

    print(">>> 2. Token count with system prompt")
    system_prompt = "You are a helpful geography expert. Answer concisely and accurately."
    system_messages = [
        {"role": "user", "content": "What is the capital of each G7 country?"}
    ]
    system_count = client.messages.count_tokens(
        model="claude-sonnet-4-20250514",
        system=system_prompt,
        messages=system_messages,
    )
    print(f"  System prompt: {system_prompt}")
    print(f"  System tokens: {system_count.input_tokens - simple_input_tokens}")
    print(f"  Total input tokens: {system_count.input_tokens}")
    print()

    # ── 3. Count tokens with tool definitions ──────────────────────────

    print(">>> 3. Token count with tool definitions")
    tools = [
        {
            "name": "get_weather",
            "description": "Get the current weather for a given location.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state/country, e.g. 'Tokyo, Japan'",
                    },
                    "units": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit",
                    },
                },
                "required": ["location"],
            },
        },
        {
            "name": "get_time",
            "description": "Get the current time for a given location.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City and state/country",
                    },
                    "timezone": {
                        "type": "string",
                        "description": "Optional IANA timezone, e.g. 'Asia/Tokyo'",
                    },
                },
                "required": ["location"],
            },
        },
    ]
    tool_messages = [
        {"role": "user", "content": "What's the weather and time in Tokyo?"}
    ]
    tool_count = client.messages.count_tokens(
        model="claude-sonnet-4-20250514",
        tools=tools,
        messages=tool_messages,
    )
    print(f"  Number of tools: {len(tools)}")
    print(f"  Tools input tokens: {tool_count.input_tokens}")
    print()

    # ── 4. Count tokens with an image ─────────────────────────────────

    print(">>> 4. Token count with image content")

    # Generate a tiny PNG programmatically (1x1 red pixel)
    png_bytes = create_sample_image_png()
    import base64
    b64_data = base64.standard_b64encode(png_bytes).decode("ascii")

    image_messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": b64_data,
                    },
                },
                {
                    "type": "text",
                    "text": "Describe this image.",
                },
            ],
        }
    ]
    image_count = client.messages.count_tokens(
        model="claude-sonnet-4-20250514",
        messages=image_messages,
    )
    print(f"  Image size: {len(png_bytes)} bytes")
    print(f"  Image + text input tokens: {image_count.input_tokens}")
    # Images typically cost ~150 tokens per image tile
    print(f"  (Images use ~150 tokens per tile; a 1x1 image uses 1 tile)")
    print()

    # ── 5. Cost estimation comparison ─────────────────────────────────

    print(">>> 5. Cost estimation across models")
    print("    Assuming 200 output tokens for each model.")

    estimated_output = 200
    input_tokens_tool = tool_count.input_tokens

    costs = []
    for model_id in MODEL_PRICING:
        c = estimate_cost(
            input_tokens=input_tokens_tool,
            output_tokens=estimated_output,
            model=model_id,
        )
        costs.append(c)

    print_cost_table(costs)

    # ── 6. Summarize usage ────────────────────────────────────────────

    total_input_so_far = (
        simple_input_tokens
        + system_count.input_tokens
        + tool_count.input_tokens
        + image_count.input_tokens
    )
    print(f"  Total input tokens counted in this demo: {total_input_so_far}")
    print()

    # Show cost of all counting requests (negligible — count_tokens is free)
    print("  Note: client.messages.count_tokens() does NOT incur any cost.")
    print("  It only counts tokens without generating a response.")
    print()

    # ── 7. Real-world cost example ────────────────────────────────────

    print(">>> 6. Real-world scenario: Chat with 8K input + 1K output")
    scenario_costs = []
    for model_id in MODEL_PRICING:
        c = estimate_cost(
            input_tokens=8000,
            output_tokens=1000,
            model=model_id,
        )
        scenario_costs.append(c)

    print_cost_table(scenario_costs)

    print("=" * 72)
    print("TIP: Use count_tokens() BEFORE sending the full request to")
    print("  estimate cost, check context limits, and choose the right model.")
    print("=" * 72)


if __name__ == "__main__":
    main()
