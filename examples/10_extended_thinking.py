#!/usr/bin/env python3
"""
Example 10: Extended thinking with Claude.

Demonstrates both modes of extended thinking available in the Anthropic API:
  1. Enabled thinking (claude-sonnet-4-6) with a specific token budget
  2. Adaptive thinking (claude-opus-4-7) with effort configuration

Uses complex math/logic puzzles to show Claude's reasoning process.
Shows how to access thinking content blocks and compare thinking vs. visible
response length.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()

import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
THINKING_MODEL = "claude-sonnet-4-6-20250515"  # supports enabled thinking
ADAPTIVE_MODEL = "claude-opus-4-20250514"  # supports adaptive thinking
MAX_TOKENS = 8192  # must be > thinking budget

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def print_header(label: str) -> None:
    """Print a section header."""
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}")


def count_tokens(text: str | None) -> int:
    """Rough character-based token estimate (chars / 4)."""
    if not text:
        return 0
    return len(text) // 4


# ===================================================================
# Part 1: Enabled thinking with claude-sonnet-4-6
# ===================================================================
def demonstrate_enabled_thinking() -> None:
    """Show enabled thinking with a fixed budget."""
    print_header("PART 1: Enabled thinking on claude-sonnet-4-6 (budget=2000 tokens)")

    prompt = (
        "I have three boxes: one contains only apples, one contains only oranges, "
        "and one contains both apples and oranges. All three boxes are mislabeled. "
        "You are allowed to pick exactly ONE piece of fruit from ONE box "
        "(without looking inside). How can you determine the correct labels for "
        "all three boxes? Explain your reasoning step by step."
    )

    print(f"Prompt:\n{prompt}\n")

    try:
        with client.messages.stream(
            model=THINKING_MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "enabled", "budget_tokens": 2000},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = stream.get_final_message()

        # Separate thinking and visible content
        thinking_blocks = [b for b in response.content if b.type == "thinking"]
        text_blocks = [b for b in response.content if b.type == "text"]
        signature_blocks = [b for b in response.content if b.type == "redacted_thinking"]

        print(f"Stop reason: {response.stop_reason}")
        print(f"Total content blocks: {len(response.content)}")
        print(f"  - Thinking blocks: {len(thinking_blocks)}")
        print(f"  - Text blocks:     {len(text_blocks)}")
        print(f"  - Redacted blocks: {len(signature_blocks)}")

        if thinking_blocks:
            full_thinking = "\n".join(b.thinking for b in thinking_blocks)
            print_header("THINKING OUTPUT")
            print(full_thinking)
            print(f"\n[Thinking: ~{count_tokens(full_thinking)} tokens, "
                  f"{len(full_thinking)} characters]")

        if text_blocks:
            full_text = "\n".join(b.text for b in text_blocks)
            print_header("VISIBLE RESPONSE")
            print(full_text)
            print(f"\n[Visible: ~{count_tokens(full_text)} tokens, "
                  f"{len(full_text)} characters]")

        # Compare lengths
        think_chars = sum(len(b.thinking) for b in thinking_blocks)
        text_chars = sum(len(b.text) for b in text_blocks)
        ratio = think_chars / max(text_chars, 1)
        print_header("THINKING vs. VISIBLE COMPARISON")
        print(f"Thinking characters:  {think_chars}")
        print(f"Visible characters:   {text_chars}")
        print(f"Thinking/visible ratio: {ratio:.1f}x")

    except Exception as e:
        print(f"ERROR in enabled thinking: {e}")


# ===================================================================
# Part 2: Adaptive thinking with claude-opus-4-7
# ===================================================================
def demonstrate_adaptive_thinking() -> None:
    """Show adaptive thinking with high effort."""
    print_header("PART 2: Adaptive thinking on claude-opus-4-7 (effort=high)")

    prompt = (
        "A snail climbs 3 meters up a wall during the day and slips 2 meters "
        "down at night. The wall is 30 meters tall. How many days does it take "
        "the snail to reach the top? Carefully explain your reasoning -- there "
        "is a well-known trick to this problem."
    )

    print(f"Prompt:\n{prompt}\n")

    try:
        with client.messages.stream(
            model=ADAPTIVE_MODEL,
            max_tokens=MAX_TOKENS,
            thinking={"type": "adaptive"},
            output_config={"effort": "high"},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            response = stream.get_final_message()

        thinking_blocks = [b for b in response.content if b.type == "thinking"]
        text_blocks = [b for b in response.content if b.type == "text"]

        print(f"Stop reason: {response.stop_reason}")
        print(f"Total content blocks: {len(response.content)}")
        print(f"  - Thinking blocks: {len(thinking_blocks)}")
        print(f"  - Text blocks:     {len(text_blocks)}")

        if thinking_blocks:
            full_thinking = "\n".join(b.thinking for b in thinking_blocks)
            print_header("THINKING OUTPUT")
            print(full_thinking)
            print(f"\n[Thinking: ~{count_tokens(full_thinking)} tokens, "
                  f"{len(full_thinking)} characters]")

        if text_blocks:
            full_text = "\n".join(b.text for b in text_blocks)
            print_header("VISIBLE RESPONSE")
            print(full_text)

        # Compare
        think_chars = sum(len(b.thinking) for b in thinking_blocks)
        text_chars = sum(len(b.text) for b in text_blocks)
        ratio = think_chars / max(text_chars, 1)
        print_header("THINKING vs. VISIBLE COMPARISON")
        print(f"Thinking characters:  {think_chars}")
        print(f"Visible characters:   {text_chars}")
        print(f"Thinking/visible ratio: {ratio:.1f}x")

    except anthropic.NotFoundError:
        print(f"\nNOTE: Model '{ADAPTIVE_MODEL}' is not available in this API "
              f"key's region.")
        print("This is expected -- adaptive thinking requires the latest model.")
    except Exception as e:
        print(f"\nNOTE: Adaptive thinking failed gracefully: {type(e).__name__}: {e}")
        print("This is expected if claude-opus-4-7 is not yet deployed.")


# ===================================================================
def main() -> None:
    """Run both extended thinking demonstrations."""
    print_header("EXTENDED THINKING DEMONSTRATION")
    print("This example shows two modes of extended thinking.")
    print("Part 1 uses enabled thinking with a fixed budget.")
    print("Part 2 uses adaptive thinking with configurable effort.\n")

    demonstrate_enabled_thinking()
    demonstrate_adaptive_thinking()

    print_header("SUMMARY")
    print("Extended thinking allows Claude to 'think' before responding.")
    print(" - Enabled thinking: You set a fixed token budget.")
    print(" - Adaptive thinking: Claude decides how much to think based on effort.")
    print("Thinking blocks can be accessed separately from visible text blocks.")
    print("This enables applications like showing a 'thinking' spinner to users.")


if __name__ == "__main__":
    main()
