#!/usr/bin/env python3
"""
Example 23: Managed Agents — Session API (Beta)

Demonstrates the Managed Agents API which allows creating persistent,
stateful agents with their own environments and sessions. This is useful
for long-running, context-aware interactions.

Key concepts:
- client.beta.agents.create() — create a reusable agent
- client.beta.environments.create() — create an isolated environment
- client.beta.sessions.create() — create a session within an environment
- client.beta.sessions.events.stream() — SSE event stream for the session
- Sending user message events
- Reading agent.message, agent.tool_use, session.status_idle events
- Full session lifecycle

Note: This is a BETA feature. It requires:
  - Beta: managed-agents-2026-04-01
  - Special API access (contact Anthropic to enable)
  - Anthropic Python SDK >= 0.70.0

A graceful fallback is included if the API returns 403/404.
"""

import os
import json
import time
import sys
from typing import Optional
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


def demonstrate_managed_agents():
    """Demonstrate the Managed Agents API with graceful fallback."""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    print("=" * 72)
    print("MANAGED AGENTS — SESSION API (Beta)")
    print("=" * 72)
    print()
    print("  Beta: managed-agents-2026-04-01")
    print("  This feature requires special API access.")
    print()

    agent_id: Optional[str] = None
    environment_id: Optional[str] = None

    try:
        # ── Step 1: Create an agent ─────────────────────────────────

        print(">>> Step 1: Creating an agent...")

        agent = client.beta.agents.create(
            name="demo-assistant",
            model="claude-sonnet-4-20250514",
            instructions="You are a helpful assistant that answers questions concisely.",
            tools=[
                {
                    "name": "get_time",
                    "description": "Get the current date and time",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "timezone": {
                                "type": "string",
                                "description": "IANA timezone string",
                            },
                        },
                        "required": [],
                    },
                },
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        agent_id = agent.id
        print(f"  Agent ID:  {agent_id}")
        print(f"  Name:      {agent.name}")
        print(f"  Model:     {agent.model}")
        print()

        # ── Step 2: Create an environment ───────────────────────────

        print(">>> Step 2: Creating an environment...")

        environment = client.beta.environments.create(
            name="demo-environment",
            agent_id=agent_id,
            # Optional: configure environment variables
            # environment_variables={"MY_VAR": "value"},
        )
        environment_id = environment.id
        print(f"  Environment ID: {environment_id}")
        print(f"  Name:           {environment.name}")
        print()

        # ── Step 3: Create a session ────────────────────────────────

        print(">>> Step 3: Creating a session...")

        session = client.beta.sessions.create(
            environment_id=environment_id,
            agent_id=agent_id,
        )
        session_id = session.id
        print(f"  Session ID: {session_id}")
        print(f"  Status:     {session.status}")
        print()

        # ── Step 4: Open SSE stream and interact ────────────────────

        print(">>> Step 4: Opening SSE event stream...")
        print()

        with client.beta.sessions.events.stream(
            session_id=session_id,
        ) as stream:
            # Send a user message event to the agent
            print("  Sending user message event...")
            stream.send(
                type="user.message",
                content="What time is it right now? Also, what is the capital of Japan?",
            )
            print("  (Message sent, listening for events...)")
            print()

            # Read events from the stream
            event_count = 0
            max_events = 20

            for event in stream:
                event_type = getattr(event, "type", str(event))
                event_count += 1

                if event_type == "agent.message":
                    # The agent has produced a text response
                    content = getattr(event, "content", "")
                    if isinstance(content, list):
                        text_parts = [
                            block.text
                            for block in content
                            if hasattr(block, "text")
                        ]
                        text = " ".join(text_parts)
                    else:
                        text = str(content)
                    print(f"  [EVENT {event_count}] agent.message:")
                    print(f"    {text[:300]}")
                    print()

                elif event_type == "agent.tool_use":
                    # The agent is calling a tool
                    name = getattr(event, "name", "unknown")
                    tool_input = getattr(event, "input", {})
                    print(f"  [EVENT {event_count}] agent.tool_use:")
                    print(f"    Tool: {name}")
                    print(f"    Args: {json.dumps(tool_input, indent=6)}")
                    print()

                elif event_type == "agent.message.delta":
                    # Streaming delta — could accumulate these for real-time UI
                    delta = getattr(event, "delta", "")
                    print(f"  [EVENT {event_count}] agent.message.delta: {delta}")

                elif event_type == "session.status_idle":
                    # The agent has finished processing and is waiting
                    print(f"  [EVENT {event_count}] session.status_idle")
                    print(f"    Agent is done processing. Waiting for next input...")
                    print()

                elif event_type == "session.error":
                    error_info = getattr(event, "error", "unknown error")
                    print(f"  [EVENT {event_count}] session.error: {error_info}")
                    print()

                else:
                    # Print any other event type for visibility
                    event_data = str(event)[:200]
                    print(f"  [EVENT {event_count}] {event_type}: {event_data}")
                    print()

                if event_count >= max_events:
                    print(f"  (Reached max {max_events} events, stopping.)")
                    break

        print("  (Stream closed.)")
        print()

        # ── Step 5: Session lifecycle ───────────────────────────────

        print(">>> Step 5: Session lifecycle management")
        print()

        # Retrieve session status
        updated_session = client.beta.sessions.retrieve(session_id=session_id)
        print(f"  Session status: {updated_session.status}")
        print(f"  Created at:     {updated_session.created_at}")

        # List all sessions (if supported)
        try:
            sessions_list = client.beta.sessions.list(environment_id=environment_id)
            print(f"  Sessions in environment: {len(sessions_list.data)}")
        except Exception as e:
            print(f"  Could not list sessions: {e}")

        print()

    except Exception as e:
        error_msg = str(e)
        status_code = getattr(e, "status_code", None)

        if status_code in (403, 404) or "beta" in error_msg.lower():
            print("=" * 72)
            print("BETA FEATURE UNAVAILABLE")
            print("=" * 72)
            print()
            print(f"  Error: {type(e).__name__}: {error_msg}")
            print()
            print("  The Managed Agents API is a restricted beta feature.")
            print("  You need:")
            print("    1. Beta access enabled on your Anthropic account")
            print("    2. The 'managed-agents-2026-04-01' beta header")
            print()
            print("  Contact Anthropic at: https://www.anthropic.com/contact")
            print()

            # Fallback: show conceptual outline
            print("=" * 72)
            print("FALLBACK: Conceptual API outline")
            print("=" * 72)
            print("""
    # Create an agent
    agent = client.beta.agents.create(
        name="my-agent",
        model="claude-sonnet-4-20250514",
        instructions="You are a helpful assistant.",
        tools=[...],
    )

    # Create an environment
    env = client.beta.environments.create(
        name="my-env",
        agent_id=agent.id,
    )

    # Create a session
    session = client.beta.sessions.create(
        environment_id=env.id,
        agent_id=agent.id,
    )

    # Open an SSE stream and interact
    with client.beta.sessions.events.stream(session_id=session.id) as stream:
        stream.send(type="user.message", content="Hello!")
        for event in stream:
            if event.type == "agent.message":
                print(event.content)
            elif event.type == "session.status_idle":
                break

    # Clean up
    client.beta.sessions.delete(session_id=session.id)
    client.beta.environments.delete(environment_id=env.id)
    client.beta.agents.delete(agent_id=agent.id)
    """)
        else:
            print(f"  Unexpected error: {type(e).__name__}: {e}")
        return

    # ── Cleanup ────────────────────────────────────────────────────

    print(">>> Cleanup: Deleting resources...")
    try:
        if session_id:
            client.beta.sessions.delete(session_id=session_id)
            print(f"  Deleted session: {session_id}")
    except Exception as e:
        print(f"  Could not delete session: {e}")

    try:
        if environment_id:
            client.beta.environments.delete(environment_id=environment_id)
            print(f"  Deleted environment: {environment_id}")
    except Exception as e:
        print(f"  Could not delete environment: {e}")

    try:
        if agent_id:
            client.beta.agents.delete(agent_id=agent_id)
            print(f"  Deleted agent: {agent_id}")
    except Exception as e:
        print(f"  Could not delete agent: {e}")

    print()
    print("=" * 72)
    print("MANAGED AGENTS DEMO COMPLETE")
    print("=" * 72)


def main():
    demonstrate_managed_agents()


if __name__ == "__main__":
    main()
