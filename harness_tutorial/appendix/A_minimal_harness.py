# ═══════════════════════════════════════════════════════════════════
# Appendix A: Minimal Harness (~30 lines)
# ═══════════════════════════════════════════════════════════════════
#
# The absolute simplest working agent harness.
# Self-contained — single file, single pip install.
#
# Dependencies: pip install anthropic
#
# Usage:
#   python A_minimal_harness.py

# /// script
# requires-python = ">=3.10"
# dependencies = ["anthropic>=0.39.0"]
# ///

import asyncio
import os

import anthropic


async def minimal_harness(user_message: str) -> str:
    """The simplest possible agentic loop.

    This is the reference minimal implementation. Everything else
    in this tutorial builds from this core pattern.
    """
    client = anthropic.AsyncAnthropic(                           # Async client — essential for real apps
        api_key=os.environ.get("ANTHROPIC_API_KEY", "sk-ant-..."),
    )

    # ── Message history ──
    messages: list[dict] = [
        {"role": "user", "content": user_message},
    ]

    # ── The agentic loop ──
    MAX_TURNS = 5                                                 # Safety: prevent infinite loops
    for turn in range(MAX_TURNS):
        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system="You are a helpful assistant.",
            messages=messages,
        )

        # Check if the model wants to call a tool
        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

        if not tool_use_blocks:
            # No tool calls — return the text response
            text = "".join(b.text for b in response.content if b.type == "text")
            return text

        # Handle tool calls (this is where you'd dispatch to real tools)
        for block in tool_use_blocks:
            # Add the assistant's tool use to history
            messages.append({
                "role": "assistant",
                "content": [{"type": "tool_use", "id": block.id,
                             "name": block.name, "input": block.input}],
            })
            # Simulate tool result (replace with real execution!)
            messages.append({
                "role": "user",
                "content": [{"type": "tool_result",
                             "tool_use_id": block.id,
                             "content": f"Result of {block.name}({block.input})"}],
            })

    return "Max turns exceeded"


# ═══ Run it ═══
if __name__ == "__main__":
    result = asyncio.run(minimal_harness("What is 2+2?"))
    print(result)
