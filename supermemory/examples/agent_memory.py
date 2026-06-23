#!/usr/bin/env python3
"""
agent_memory.py -- AI agent that remembers tasks, preferences, and results

Demonstrates:
  - Recording task outcomes for future learning
  - Storing user preferences that persist across sessions
  - Retrieving relevant context before executing new tasks
  - Error handling and graceful degradation

Usage:
    python agent_memory.py

Requirements:
    pip install supermemory
    export SUPERMEMORY_API_KEY="sm_..."
"""

from datetime import datetime
from supermemory import Supermemory, APIError


class MemoryAgent:
    """An AI agent with persistent memory via Supermemory."""

    def __init__(self, agent_name: str):
        self.sm = Supermemory()
        self.agent_name = agent_name
        self.container_tag = f"agent_{agent_name}"

    # ── Context Retrieval ─────────────────────────────

    def get_context(self, task_description: str) -> dict:
        """Get all relevant context before executing a task."""
        try:
            profile = self.sm.profile(
                container_tag=self.container_tag,
                q=task_description,
            )
            return {
                "static_facts": profile.profile.static,
                "dynamic_facts": profile.profile.dynamic,
                "relevant_memories": [
                    r.get("memory", str(r))
                    for r in profile.search_results.results[:5]
                ],
            }
        except APIError as e:
            print(f"[WARNING] Context retrieval failed: {e}")
            return {
                "static_facts": [],
                "dynamic_facts": [],
                "relevant_memories": [],
            }

    def get_preferences(self) -> list[str]:
        """Get stored user preferences."""
        try:
            results = self.sm.search.documents(
                q="user preference",
                container_tags=[self.container_tag],
                limit=10,
            )
            return [
                r.get("memory", str(r))
                for r in results.results
                if "preference" in r.get("memory", "").lower()
            ]
        except APIError as e:
            print(f"[WARNING] Preference retrieval failed: {e}")
            return []

    # ── Memory Recording ──────────────────────────────

    def record_task(
        self,
        task: str,
        result: str,
        success: bool,
        metadata: dict | None = None,
    ):
        """Record a completed task with its outcome."""
        status = "SUCCESS" if success else "FAILED"
        content = (
            f"TASK EXECUTED: {task}\n"
            f"OUTCOME ({status}): {result}\n"
            f"AGENT: {self.agent_name}"
        )
        try:
            self.sm.add(
                content=content,
                container_tag=self.container_tag,
                metadata={
                    "type": "task_execution",
                    "success": success,
                    "timestamp": datetime.now().isoformat(),
                    **(metadata or {}),
                },
            )
            print(f"[MEMORY] Recorded task: {task[:60]}... -> {status}")
        except APIError as e:
            print(f"[ERROR] Failed to record task: {e}")

    def record_preference(self, preference: str):
        """Record a user preference."""
        content = f"USER PREFERENCE: {preference}"
        try:
            self.sm.add(
                content=content,
                container_tag=self.container_tag,
                metadata={"type": "preference"},
            )
            print(f"[MEMORY] Recorded preference: {preference[:60]}...")
        except APIError as e:
            print(f"[ERROR] Failed to record preference: {e}")

    def record_learning(self, lesson: str, category: str = "general"):
        """Record a lesson learned for future reference."""
        content = f"LESSON LEARNED [{category}]: {lesson}"
        try:
            self.sm.add(
                content=content,
                container_tag=self.container_tag,
                metadata={"type": "learning", "category": category},
            )
            print(f"[MEMORY] Recorded learning [{category}]: {lesson[:60]}...")
        except APIError as e:
            print(f"[ERROR] Failed to record learning: {e}")

    # ── Task History ──────────────────────────────────

    def get_task_history(self, limit: int = 10) -> list[str]:
        """Get recent task execution history."""
        try:
            results = self.sm.search.documents(
                q="TASK EXECUTED",
                container_tags=[self.container_tag],
                limit=limit,
            )
            return [r.get("memory", str(r)) for r in results.results]
        except APIError as e:
            print(f"[WARNING] Task history retrieval failed: {e}")
            return []

    def get_learnings(self, category: str | None = None) -> list[str]:
        """Get lessons learned, optionally filtered by category."""
        try:
            filters = {"AND": [{"key": "type", "value": "learning"}]}
            if category:
                filters["AND"].append({"key": "category", "value": category})
            results = self.sm.search.documents(
                q="LESSON LEARNED",
                container_tags=[self.container_tag],
                filters=filters,
                limit=20,
            )
            return [r.get("memory", str(r)) for r in results.results]
        except APIError as e:
            print(f"[WARNING] Learning retrieval failed: {e}")
            return []


def demo():
    """Demonstrate the MemoryAgent capabilities."""
    agent = MemoryAgent(agent_name="deployment_bot")

    print("=" * 60)
    print("MemoryAgent Demo -- Deployment Bot")
    print("=" * 60)

    # 1. Record preferences
    print("\n--- Recording Preferences ---")
    agent.record_preference(
        "User prefers deployments on Tuesdays at 10:00 AM PST"
    )
    agent.record_preference(
        "Always run integration tests before deploying to production"
    )
    agent.record_preference(
        "Notify #engineering Slack channel after each deployment"
    )

    # 2. Execute and record tasks
    print("\n--- Executing Tasks ---")
    agent.record_task(
        task="Deploy v2.3.1 to staging",
        result="Deployment successful. All 142 tests passed. "
               "No performance regressions detected.",
        success=True,
        metadata={"version": "2.3.1", "environment": "staging"},
    )
    agent.record_task(
        task="Deploy v2.3.1 to production",
        result="Deployment failed. Database migration lock timeout "
               "on users table. Rolled back successfully.",
        success=False,
        metadata={"version": "2.3.1", "environment": "production"},
    )

    # 3. Record learnings from failures
    print("\n--- Recording Learnings ---")
    agent.record_learning(
        "Database migrations on large tables need a lock timeout "
        "of at least 60 seconds. Use lock_timeout=60000 in migration config.",
        category="database",
    )
    agent.record_learning(
        "Always run migrations against a production-sized dataset "
        "in staging before deploying to production.",
        category="deployment",
    )

    # 4. Retrieve context for a new task
    print("\n--- Context for New Task ---")
    ctx = agent.get_context("deploy to production")
    print(f"Static facts ({len(ctx['static_facts'])}):")
    for f in ctx["static_facts"]:
        print(f"  - {f}")
    print(f"Dynamic facts ({len(ctx['dynamic_facts'])}):")
    for f in ctx["dynamic_facts"]:
        print(f"  - {f}")
    print(f"Relevant memories ({len(ctx['relevant_memories'])}):")
    for m in ctx["relevant_memories"]:
        print(f"  - {m[:80]}...")

    # 5. Query preferences
    print("\n--- Stored Preferences ---")
    prefs = agent.get_preferences()
    for p in prefs:
        print(f"  - {p[:100]}...")

    # 6. Query learnings
    print("\n--- Lessons Learned ---")
    learnings = agent.get_learnings()
    for i, l in enumerate(learnings, 1):
        print(f"  {i}. {l[:100]}...")

    print("\n" + "=" * 60)
    print("Demo complete! The agent now has persistent memory.")
    print("Next deployment task will benefit from all recorded context.")


if __name__ == "__main__":
    demo()
