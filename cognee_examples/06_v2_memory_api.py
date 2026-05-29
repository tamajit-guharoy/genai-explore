"""
06_v2_memory_api.py — Agent memory with sessions (remember/recall/improve/forget).

Simulates a multi-turn customer support conversation where:
1. Each turn uses remember() to store facts in session memory
2. recall() retrieves both session facts and permanent knowledge
3. improve() promotes useful session facts to permanent memory
4. forget() cleans up the session when done

Prerequisites:
    pip install cognee
"""

import asyncio
import uuid

import cognee


async def simulate_support_conversation():
    """Simulate a multi-turn support conversation using Cognee memory."""
    session_id = f"support_{uuid.uuid4().hex[:8]}"
    user_id = "agent_support_bot"

    print(f"Session: {session_id}")
    print("=" * 60)

    # ── Turn 1: User reports an issue ──────────────────────────────────
    print("\n[Turn 1] User: 'I can't log in to the dashboard. Getting error 503.'")

    await cognee.remember(
        "User reported login failure with HTTP 503 error on the dashboard. "
        "The error started around 14:30 UTC today. User is on the Pro plan.",
        session_id=session_id,
        user_id=user_id,
    )

    # Agent recalls known information about error 503
    context = await cognee.recall(
        "What causes HTTP 503 errors on the dashboard and what's the SLA "
        "for Pro plan users?",
        session_id=session_id,
    )
    print(f"Agent recalls: {context[:300]}..." if len(str(context)) > 300 else f"Agent recalls: {context}")

    # Agent responds
    print("Agent: 'I see you're on the Pro plan. 503 errors are typically "
          "caused by backend service unavailability. Your SLA guarantees "
          "99.9% uptime. Let me check for ongoing incidents.'")

    # ── Turn 2: Agent investigates ─────────────────────────────────────
    print("\n[Turn 2] Agent action: Checking incident reports...")

    await cognee.remember(
        "Investigation revealed the authentication-service pod is in a "
        "CrashLoopBackOff state. The issue started after a config push at "
        "14:28 UTC. The deployment was to update OAuth2 client credentials. "
        "Rolling back to the previous config version should resolve the issue.",
        session_id=session_id,
        user_id=user_id,
    )

    await cognee.remember(
        "Root cause identified: expired OAuth2 client secret in the new "
        "config. The secret rotation process did not update the dashboard "
        "service's environment variables. This is a known gap in the "
        "automated secret rotation pipeline.",
        session_id=session_id,
        user_id=user_id,
    )

    # Agent summarizes findings
    findings = await cognee.recall(
        "What caused the login failure and how can it be fixed?",
        session_id=session_id,
    )
    print(f"Agent report: {findings}")

    # ── Turn 3: Resolution and promotion ───────────────────────────────
    print("\n[Turn 3] Agent: 'Rollback completed. Can you try logging in now?'")
    print("User: 'It works now! Thank you.'")

    await cognee.remember(
        "Issue resolved by rolling back config deployment. User confirmed "
        "login is working. The permanent fix is to update the automated "
        "secret rotation pipeline to include dashboard service env vars.",
        session_id=session_id,
        user_id=user_id,
    )

    # Promote the root cause and fix to permanent memory
    print("\nPromoting session knowledge to permanent memory...")
    await cognee.improve(
        session_id=session_id,
        promote_to_permanent=True,
        feedback="Root cause: expired OAuth2 secret not propagated to dashboard. "
                 "Fix: update secret rotation pipeline. Resolution: config rollback.",
    )

    # Verify permanent memory promotion
    permanent_knowledge = await cognee.recall(
        "What is the fix for dashboard login failures caused by OAuth2 issues?",
    )
    print(f"Permanent memory: {permanent_knowledge}")

    # ── Clean up session ───────────────────────────────────────────────
    print(f"\nCleaning up session {session_id}...")
    await cognee.forget(session_id=session_id)

    print("Session cleaned up. Permanent knowledge retained.")
    print("\nDone! The V2 Memory API enables agent conversations with")
    print("persistent, evolving memory across sessions.")


async def main():
    await simulate_support_conversation()


if __name__ == "__main__":
    asyncio.run(main())
