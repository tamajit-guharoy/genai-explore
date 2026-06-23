#!/usr/bin/env python3
"""
chatbot_with_memory.py -- Full chatbot with Supermemory-backed user profiles

Demonstrates the Profile -> Chat -> Store pattern:
  1. Profile: Get user context before every LLM call
  2. Chat: Inject profile into system prompt for personalized responses
  3. Store: Save the conversation so the agent learns over time

Usage:
    python chatbot_with_memory.py

Requirements:
    pip install supermemory openai
    export SUPERMEMORY_API_KEY="sm_..."
    export OPENAI_API_KEY="sk-..."
"""

import os
import sys
from supermemory import Supermemory


class MemoryChatbot:
    """A chatbot that remembers users across conversations using Supermemory."""

    def __init__(self, user_id: str):
        self.sm = Supermemory()
        self.user_id = user_id
        self.container_tag = f"user_{user_id}"
        self.conversation_history: list[dict] = []

    def _build_system_prompt(self, user_message: str) -> str:
        """Build a system prompt enriched with user profile and relevant memories."""
        try:
            profile = self.sm.profile(
                container_tag=self.container_tag,
                q=user_message,
            )

            static = "\n".join(f"- {f}" for f in profile.profile.static)
            dynamic = "\n".join(f"- {f}" for f in profile.profile.dynamic)
            memories = "\n".join(
                f"- {r.get('memory', str(r))}"
                for r in profile.search_results.results[:5]
            )

            return f"""You are a helpful, personalized assistant.

USER PROFILE (long-term facts):
{static if static else 'No profile built yet. Keep conversing to build one.'}

CURRENT CONTEXT (recent activity):
{dynamic if dynamic else 'No recent context.'}

RELEVANT MEMORIES:
{memories if memories else 'No relevant past conversations.'}

Use this context to personalize your responses. Address the user by name if known.
Be concise, warm, and helpful."""

        except Exception as e:
            print(f"[WARNING] Profile lookup failed: {e}", file=sys.stderr)
            return "You are a helpful assistant."

    def chat(self, user_message: str) -> str:
        """Process a user message and return an LLM response with memory context."""
        # Step 1: Build enriched system prompt
        system_prompt = self._build_system_prompt(user_message)

        # Step 2: Build messages with conversation history
        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[-20:],  # Last 10 exchanges
            {"role": "user", "content": user_message},
        ]

        # Step 3: Call LLM
        try:
            from openai import OpenAI
            llm = OpenAI()
            response = llm.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            assistant_message = response.choices[0].message.content
        except ImportError:
            # Fallback for demo without OpenAI installed
            print("[INFO] OpenAI not installed -- using demo mode.")
            fake_responses = [
                "That's an interesting question! Based on your profile, "
                "I can help you with that.",
                "I remember you mentioned this earlier. Let me help!",
                "Great point! Drawing from our previous conversations, "
                "here's what I think...",
            ]
            import random
            assistant_message = random.choice(fake_responses)

        # Step 4: Store the exchange for future context
        self._store_conversation(user_message, assistant_message)

        return assistant_message

    def _store_conversation(self, user_msg: str, assistant_msg: str):
        """Persist the conversation turn to Supermemory."""
        conv_text = f"user: {user_msg}\nassistant: {assistant_msg}"
        try:
            self.sm.add(content=conv_text, container_tag=self.container_tag)
        except Exception as e:
            print(f"[WARNING] Failed to store conversation: {e}", file=sys.stderr)

        # Keep local history for multi-turn context within this session
        self.conversation_history.append({"role": "user", "content": user_msg})
        self.conversation_history.append(
            {"role": "assistant", "content": assistant_msg}
        )

    def show_profile(self):
        """Display the user's stored profile."""
        try:
            profile = self.sm.profile(container_tag=self.container_tag)
            print("\n--- Your Stored Profile ---")
            print("Static facts:")
            for f in profile.profile.static:
                print(f"  - {f}")
            print("Dynamic facts:")
            for f in profile.profile.dynamic:
                print(f"  - {f}")
            print("---\n")
        except Exception as e:
            print(f"Error fetching profile: {e}")

    def clear_session_history(self):
        """Clear local conversation history (Supermemory memories persist)."""
        self.conversation_history.clear()
        print("[Session history cleared. Supermemory memories persist.]")


def main():
    user_id = input("Enter your user ID: ").strip() or "demo_user"
    bot = MemoryChatbot(user_id=user_id)

    print(f"\n=== Memory Chatbot (user: {user_id}) ===")
    print("Type /clear  to clear session history")
    print("Type /profile to see your stored profile")
    print("Type /exit   to quit\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() == "/exit":
            print("Goodbye!")
            break
        elif user_input.lower() == "/clear":
            bot.clear_session_history()
            continue
        elif user_input.lower() == "/profile":
            bot.show_profile()
            continue

        response = bot.chat(user_input)
        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()
