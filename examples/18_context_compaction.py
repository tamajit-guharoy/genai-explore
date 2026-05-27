#!/usr/bin/env python3
"""
Example 18: Context Compaction (Beta)

Demonstrates the context compaction beta feature which allows you to
automatically compact (summarize) older messages in a long conversation
to stay within the model's context window.

Key concepts:
- Using the beta API: client.beta.messages.create()
- Passing betas=["compact-2026-01-12"] header
- Setting a low trigger_threshold for demonstration
- Custom compaction instructions (compact_instructions)
- pause_after_compaction: True to handle compaction manually
- stop_reason == "compaction" and resuming after compaction
- Reading the compaction_summary from the response

Note: This is a BETA feature. It requires the beta header and may not be
available on all accounts. A graceful fallback is included.
"""

import os
import sys
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


def demonstrate_compaction():
    """
    Demonstrate context compaction by simulating a long conversation
    that triggers the compaction mechanism.
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = "claude-sonnet-4-20250514"

    print("=" * 72)
    print("CONTEXT COMPACTION DEMO (beta: compact-2026-01-12)")
    print("=" * 72)
    print()
    print("Context compaction automatically summarizes older messages when")
    print("the conversation approaches the context window limit.")
    print()

    # Build a conversation with many messages to potentially trigger compaction.
    messages = []
    for i in range(10):
        messages.append({
            "role": "user",
            "content": f"What is {i + 1} + {i + 2}? Answer in exactly one sentence.",
        })
        messages.append({
            "role": "assistant",
            "content": f"{i + 1} + {i + 2} = {(i + 1) + (i + 2)}.",
        })

    # Add a final message that should be answered
    messages.append({
        "role": "user",
        "content": "Now, given all our previous math, what is 100 + 200?",
    })

    try:
        print("Sending message with compaction enabled...")
        print(f"  Messages count: {len(messages)}")
        print(f"  Model: {model}")
        print(f"  Beta: compact-2026-01-12")
        print(f"  Trigger threshold: 50000 tokens (low for demo)")
        print(f"  Pause after compaction: True")
        print()

        response = client.beta.messages.create(
            betas=["compact-2026-01-12"],
            model=model,
            max_tokens=1000,
            # Set a low threshold so compaction triggers more easily in demo
            trigger_threshold=50000,
            # Custom instructions for what the compaction summary should emphasize
            compact_instructions=(
                "Focus on preserving all mathematical results and the exact "
                "numerical answers given. Keep the assistant's concise style."
            ),
            # Pause so we can inspect the compaction
            pause_after_compaction=True,
            messages=messages,
        )

        print(f"Stop reason: {response.stop_reason}")
        print(f"Stop sequence: {response.stop_sequence}")
        print()

        # Check if compaction was triggered
        if response.stop_reason == "compaction":
            print(">>> COMPACTION TRIGGERED <<<")
            print()
            print("Compaction summary:")
            print("-" * 72)

            if hasattr(response, "compaction_summary") and response.compaction_summary:
                for block in response.compaction_summary:
                    if block.type == "text":
                        print(block.text)
                    elif block.type == "thinking":
                        print(f"[thinking: {len(block.thinking)} chars]")
            else:
                print("(No compaction_summary in response — compaction may have been")
                print(" handled server-side without returning details.)")
            print("-" * 72)
            print()

            # Resume the conversation after compaction
            print("Resuming after compaction...")
            print()

            # The previous messages have been compacted. We send a new message.
            # NOTE: In a real application you would typically discard the old
            # messages and rely on the compacted context on the server side.
            resume_response = client.beta.messages.create(
                betas=["compact-2026-01-12"],
                model=model,
                max_tokens=500,
                trigger_threshold=50000,
                compact_instructions=(
                    "Focus on preserving all mathematical results."
                ),
                messages=[
                    {
                        "role": "user",
                        "content": (
                            "Continuing after compaction: What was the result "
                            "of 5 + 7 from earlier? Answer briefly."
                        ),
                    },
                ],
            )

            print(f"Resume response stop_reason: {resume_response.stop_reason}")
            for block in resume_response.content:
                if block.type == "text":
                    print(f"Claude says: {block.text}")

        else:
            # Compaction did not trigger — show what we got
            print("Compaction did NOT trigger (the demo threshold may need tuning).")
            print(f"Response content:")
            for block in response.content:
                if block.type == "text":
                    print(f"  {block.text[:200]}...")

            # Check if compaction_summary is available
            if hasattr(response, "compaction_summary") and response.compaction_summary:
                print()
                print("Compaction summary (returned even without stop_reason=compaction):")
                for block in response.compaction_summary:
                    if block.type == "text":
                        print(f"  {block.text[:300]}")

    except Exception as e:
        error_msg = str(e)
        print()
        print(f"<<< BETA FEATURE UNAVAILABLE >>>")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {error_msg}")
        print()
        print("Context compaction is a beta feature (compact-2026-01-12).")
        print("It requires:")
        print("  1. The 'compact-2026-01-12' beta to be enabled on your API key")
        print("  2. Using client.beta.messages.create() instead of client.messages.create()")
        print("  3. The Anthropic Python SDK version 0.70.0 or later")
        print()
        print("See: https://docs.anthropic.com/en/docs/build-with-claude/context-compaction")
        print()

        # Fallback: Show what the code would look like conceptually
        print("=" * 72)
        print("FALLBACK: Conceptual outline")
        print("=" * 72)
        print("""
    # Key API shape:
    response = client.beta.messages.create(
        betas=["compact-2026-01-12"],
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[...],
        trigger_threshold=50000,           # Tokens at which to compact
        compact_instructions="...",        # Instructions for the summary
        pause_after_compaction=True,       # Pause so you can review the summary
    )

    if response.stop_reason == "compaction":
        summary = response.compaction_summary
        # Display or log the summary
        # Then send a new message (old context is now compacted)
    """)


def main():
    demonstrate_compaction()


if __name__ == "__main__":
    main()
