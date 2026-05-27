#!/usr/bin/env python3
"""
04_streaming_with_thinking.py — Streaming with Extended Thinking

Demonstrates how to use Claude's extended thinking feature (visible chain-of-
thought) with streaming. This requires a model that supports thinking and the
`thinking` parameter in the request.

Key events in a thinking stream:
  - thinking_delta:  the chain-of-thought tokens (shown separately)
  - text_delta:      the visible response text
  - signature_delta: a cryptographic signature for the thinking block
  - Input usage is reported in MessageStart; output usage in MessageDelta

The thinking content is returned as a separate content block before the text,
so the response has two content blocks: [thinking, text].

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 04_streaming_with_thinking.py
"""

from dotenv import load_dotenv
import anthropic
from anthropic.types import (
    MessageStartEvent,
    MessageDeltaEvent,
    ContentBlockStartEvent,
    ContentBlockDeltaEvent,
    ContentBlockStopEvent,
    MessageStopEvent,
)
import os

load_dotenv()


def main() -> None:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    print("=" * 60)
    print("STREAMING WITH EXTENDED THINKING")
    print("=" * 60)
    print()

    with client.messages.stream(
        # claude-sonnet-4-6 supports extended thinking
        model="claude-sonnet-4-6-latest",
        max_tokens=4096,
        thinking={"type": "enabled", "budget_tokens": 2000},
        messages=[
            {
                "role": "user",
                "content": "Explain step-by-step how a transformer model "
                           "processes a sentence like 'The cat sat on the mat.' "
                           "Use concrete examples.",
            }
        ],
    ) as stream:
        thinking_text = ""
        visible_text = ""
        current_block_index: int | None = None
        current_block_type: str | None = None

        for event in stream:
            # ── Message start ─────────────────────────────────────────────
            if isinstance(event, MessageStartEvent):
                print(f"[MessageStart] id={event.message.id[:12]}... "
                      f"model={event.message.model}")
                print(f"  Input tokens: {event.message.usage.input_tokens}")
                print()

            # ── Content block start ───────────────────────────────────────
            elif isinstance(event, ContentBlockStartEvent):
                current_block_index = event.index
                current_block_type = event.content_block.type
                print(f"[Block {event.index} starts] type={current_block_type}")

                # If this is a thinking block, print its signature (if any)
                if hasattr(event.content_block, "signature"):
                    sig = event.content_block.signature
                    print(f"  Thinking signature: {sig[:40]}...")
                print()

            # ── Content block delta ───────────────────────────────────────
            elif isinstance(event, ContentBlockDeltaEvent):
                delta = event.delta

                # Thinking token
                if hasattr(delta, "type") and delta.type == "thinking_delta":
                    if delta.thinking:
                        thinking_text += delta.thinking
                        print(f"\033[90m{delta.thinking}\033[0m", end="", flush=True)

                # Signature delta (appended to thinking block)
                elif hasattr(delta, "type") and delta.type == "signature_delta":
                    print(f"\n  [Signature delta received: {delta.signature[:40]}...]")

                # Visible text token
                elif hasattr(delta, "type") and delta.type == "text_delta":
                    if delta.text:
                        visible_text += delta.text
                        print(delta.text, end="", flush=True)

                # Fallback for older SDK versions (plain TextDelta)
                elif hasattr(delta, "text"):
                    visible_text += delta.text
                    print(delta.text, end="", flush=True)

            # ── Content block stop ────────────────────────────────────────
            elif isinstance(event, ContentBlockStopEvent):
                block_type = current_block_type or "unknown"
                print(f"\n  [Block {event.index} stops] type={block_type}")
                print()

            # ── Message delta ─────────────────────────────────────────────
            elif isinstance(event, MessageDeltaEvent):
                print(f"\n[MessageDelta] stop_reason={event.delta.stop_reason}")
                print(f"  Output tokens: {event.usage.output_tokens}")

            # ── Message stop ──────────────────────────────────────────────
            elif isinstance(event, MessageStopEvent):
                print(f"[MessageStop]")

    # After streaming, get the complete message for accurate usage.
    final = stream.get_final_message()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Model:                   {final.model}")
    print(f"  Stop reason:             {final.stop_reason}")
    print(f"  Content blocks:          {len(final.content)}")
    print(f"  Thinking length (chars): {len(thinking_text)}")
    print(f"  Visible text length:     {len(visible_text)}")
    print(f"  Input tokens:            {final.usage.input_tokens}")
    print(f"  Output tokens:           {final.usage.output_tokens}")
    print(f"  Cache creation tokens:   "
          f"{getattr(final.usage, 'cache_creation_input_tokens', 0)}")
    print(f"  Cache read tokens:       "
          f"{getattr(final.usage, 'cache_read_input_tokens', 0)}")
    print()

    # Print the thinking vs visible text side by side summary
    if thinking_text:
        print("--- THINKING (first 300 chars) ---")
        print(thinking_text[:300])
        print("...")
    print()
    print("--- VISIBLE TEXT (first 500 chars) ---")
    print(visible_text[:500])
    print("=" * 60)


if __name__ == "__main__":
    main()
