#!/usr/bin/env python3
"""
02_multi_turn_conversation.py — Multi-Turn Conversation

Demonstrates how to maintain conversation state across multiple turns:
  - Start with a messages list and append each assistant + user exchange
  - Run a 3-turn conversation: ask a question, follow up, follow up again
  - Show the full conversation history at the end

Key lesson: the messages list must alternate user/assistant/user/assistant.
Each assistant response is appended, then the next user message is appended
before the next API call.

Run:
    pip install anthropic python-dotenv
    echo ANTHROPIC_API_KEY=sk-ant-... > .env
    python 02_multi_turn_conversation.py
"""

from dotenv import load_dotenv
import anthropic
import os

load_dotenv()


def main() -> None:
    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY"),
    )

    # ── Conversation history — starts empty ───────────────────────────────
    messages: list[dict] = []

    # ── Turn 1: Ask an initial question ───────────────────────────────────
    print("=" * 60)
    print("TURN 1")
    print("=" * 60)
    messages.append({"role": "user", "content": "What is the capital of France?"})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=messages,
    )

    reply_1 = response.content[0].text
    print(f"User:      What is the capital of France?")
    print(f"Assistant: {reply_1}")
    messages.append({"role": "assistant", "content": reply_1})
    print()

    # ── Turn 2: Follow-up ─────────────────────────────────────────────────
    print("=" * 60)
    print("TURN 2")
    print("=" * 60)
    messages.append({"role": "user", "content": "What about its most famous landmark?"})

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=messages,
    )

    reply_2 = response.content[0].text
    print(f"User:      What about its most famous landmark?")
    print(f"Assistant: {reply_2}")
    messages.append({"role": "assistant", "content": reply_2})
    print()

    # ── Turn 3: Another follow-up ─────────────────────────────────────────
    print("=" * 60)
    print("TURN 3")
    print("=" * 60)
    messages.append(
        {"role": "user", "content": "When was that landmark built?"}
    )

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=512,
        messages=messages,
    )

    reply_3 = response.content[0].text
    print(f"User:      When was that landmark built?")
    print(f"Assistant: {reply_3}")
    messages.append({"role": "assistant", "content": reply_3})
    print()

    # ── Print full conversation history ───────────────────────────────────
    print("\n" + "=" * 60)
    print("FULL CONVERSATION HISTORY")
    print("=" * 60)
    for i, msg in enumerate(messages):
        role = msg["role"].capitalize()
        content = msg["content"]
        # Truncate very long messages for display
        if len(content) > 300:
            content = content[:300] + "..."
        print(f"\n[{role}]")
        print(f"  {content}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
