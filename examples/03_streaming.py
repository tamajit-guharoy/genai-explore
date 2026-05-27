#!/usr/bin/env python3
"""
03_streaming.py — Streaming Responses

Demonstrates two approaches to streaming with the Anthropic Claude API:
  1. Simple: stream.text_stream — iterate over text delta chunks
  2. Detailed: full event loop — inspect each event type
  3. Final message: stream.get_final_message() for usage stats after streaming

Streaming is essential for responsive UIs and long generations.

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 03_streaming.py
"""

from dotenv import load_dotenv
import anthropic
from anthropic.types import (
    MessageStartEvent,
    MessageDeltaEvent,
    MessageStopEvent,
    ContentBlockStartEvent,
    ContentBlockDeltaEvent,
    ContentBlockStopEvent,
)
import os

load_dotenv()


def example_simple_text_stream(client: anthropic.Anthropic) -> None:
    """Iterate over text deltas as they arrive — clean and simple."""
    print("\n" + "=" * 60)
    print("EXAMPLE 1: Simple text_stream")
    print("=" * 60)

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": "Write a haiku about streaming data.",
            }
        ],
    ) as stream:
        print("Streaming: ", end="", flush=True)
        for text_delta in stream.text_stream:
            print(text_delta, end="", flush=True)
        print()

    # After the context manager exits, get the final message for metadata.
    final = stream.get_final_message()
    print(f"\n  [Model: {final.model} | "
          f"Input tokens: {final.usage.input_tokens} | "
          f"Output tokens: {final.usage.output_tokens}]")


def example_full_event_loop(client: anthropic.Anthropic) -> None:
    """Inspect every event in the stream — useful for advanced handling."""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Full event loop")
    print("=" * 60)

    with client.messages.stream(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": "Count from 1 to 5, one per line.",
            }
        ],
    ) as stream:
        collected_text = ""

        for event in stream:
            # ── Message start ─────────────────────────────────────────────
            if isinstance(event, MessageStartEvent):
                print(f"[Event] MessageStart — id={event.message.id}, "
                      f"model={event.message.model}")

            # ── Content block start ───────────────────────────────────────
            elif isinstance(event, ContentBlockStartEvent):
                print(f"[Event] ContentBlockStart — index={event.index}, "
                      f"type={event.content_block.type}")

            # ── Content block delta (the actual text tokens!) ─────────────
            elif isinstance(event, ContentBlockDeltaEvent):
                delta = event.delta
                if hasattr(delta, "text") and delta.text:
                    collected_text += delta.text
                    print(f"[Event] ContentBlockDelta — text so far: "
                          f"{collected_text!r}")

            # ── Content block stop ────────────────────────────────────────
            elif isinstance(event, ContentBlockStopEvent):
                print(f"[Event] ContentBlockStop — index={event.index}")

            # ── Message delta (top-level metadata changes) ────────────────
            elif isinstance(event, MessageDeltaEvent):
                print(f"[Event] MessageDelta — stop_reason={event.delta.stop_reason}, "
                      f"stop_sequence={event.delta.stop_sequence}, "
                      f"output_tokens={event.usage.output_tokens}")

            # ── Message stop ──────────────────────────────────────────────
            elif isinstance(event, MessageStopEvent):
                print(f"[Event] MessageStop")

        print(f"\n  Final collected text:\n  {collected_text}")

    # Get usage from the final message.
    final = stream.get_final_message()
    print(f"\n  Usage — Input: {final.usage.input_tokens}, "
          f"Output: {final.usage.output_tokens}")


def main() -> None:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    example_simple_text_stream(client)
    example_full_event_loop(client)


if __name__ == "__main__":
    main()
