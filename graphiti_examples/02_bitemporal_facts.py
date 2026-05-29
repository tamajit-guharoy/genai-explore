"""
Example 02: Bi-temporal Facts -- How Facts Change Over Time

Graphiti's core superpower is its **bi-temporal model**. Every fact is tracked
along two time dimensions:

  1. **Statement time** (valid_at / invalid_at)
     When the fact is claimed to be true in the real world. If a fact is
     superseded, it gets an invalid_at timestamp marking when it ceased to
     be true.

  2. **Ingestion time**
     When the fact was added to the knowledge graph (the episode's
     reference_time).

This example adds facts about "Project Falcon" across three quarters (Q1-Q3),
showing how facts can be added, superseded, and searched with full temporal
awareness.

The fictional company is still Acme Corp -- Project Falcon is their internal
codename for a new real-time tracking platform.
"""

import asyncio
import os
import sys

from datetime import datetime, timezone, timedelta

# ---------------------------------------------------------------------------
# Environment / connectivity check
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY is not set. Graphiti uses an LLM to extract "
        "entities and relationships. Without it, extraction will fail.\n"
        "Set it via:  export OPENAI_API_KEY='sk-...'  (Linux/Mac)\n"
        "or:          $env:OPENAI_API_KEY='sk-...'   (Windows PowerShell)\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
    import socket

    host, _, port_str = NEO4J_URI.replace("bolt://", "").replace("neo4j://", "").partition(":")
    try:
        port = int(port_str) if port_str else 7687
    except ValueError:
        port = 7687
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except (OSError, socket.timeout):
        return False


# ---------------------------------------------------------------------------
# Helper to print temporal edges
# ---------------------------------------------------------------------------
def print_edges(edges, heading: str = ""):
    """Pretty-print a list of edges with their temporal metadata."""
    if heading:
        print(f"\n  --- {heading} ---")
    if not edges:
        print("  (no results)")
        return
    for i, e in enumerate(edges, 1):
        print(f"  [{i}] fact:     {e.fact}")
        print(f"      source:   {e.source_node_name} --> {e.target_node_name}")
        if e.valid_at:
            print(f"      valid at: {e.valid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        if e.invalid_at:
            print(f"      expired:  {e.invalid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()


# ===================================================================
#  Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 02: Bi-temporal Facts")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start Neo4j via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    group_id = "project_falcon"

    # ------------------------------------------------------------------
    # Q1 2025 -- Early stage
    # ------------------------------------------------------------------
    q1_time = datetime(2025, 3, 15, tzinfo=timezone.utc)

    print("\n>>> Q1 2025: Project Falcon is initiated")
    print("-" * 50)

    await graphiti.add_episode(
        name="falcon_q1_init",
        episode_body=(
            "Project Falcon was initiated in January 2025 at Acme Corp. "
            "Alice Zhang is the project lead. The project has 3 engineers. "
            "The estimated launch date is Q4 2025."
        ),
        source=EpisodeType.text,
        source_description="Q1 status report",
        reference_time=q1_time,
        group_id=group_id,
    )

    await graphiti.add_episode(
        name="falcon_q1_stack",
        episode_body=(
            "Project Falcon will be built with Python and React. "
            "The budget is $500,000. "
            "James Miller is the executive sponsor."
        ),
        source=EpisodeType.text,
        source_description="Q1 planning document",
        reference_time=q1_time,
        group_id=group_id,
    )

    # ------------------------------------------------------------------
    # Q2 2025 -- Mid stage: team grew, budget changed
    # ------------------------------------------------------------------
    q2_time = datetime(2025, 6, 20, tzinfo=timezone.utc)

    print(">>> Q2 2025: Updated status (team grew, budget increased)")
    print("-" * 50)

    await graphiti.add_episode(
        name="falcon_q2_update",
        episode_body=(
            "Project Falcon now has 8 engineers. "
            "Maria Gonzalez joined as product manager. "
            "The estimated launch date has moved to Q1 2026 due to scope creep."
        ),
        source=EpisodeType.text,
        source_description="Q2 status report",
        reference_time=q2_time,
        group_id=group_id,
    )

    await graphiti.add_episode(
        name="falcon_q2_budget",
        episode_body=(
            "Project Falcon budget revised to $1,200,000 to accommodate "
            "additional hiring and infrastructure costs."
        ),
        source=EpisodeType.text,
        source_description="Q2 budget revision",
        reference_time=q2_time,
        group_id=group_id,
    )

    # ------------------------------------------------------------------
    # Q3 2025 -- Late stage: renamed, delayed again
    # ------------------------------------------------------------------
    q3_time = datetime(2025, 9, 10, tzinfo=timezone.utc)

    print(">>> Q3 2025: Renamed to 'FalconTrack', delayed further")
    print("-" * 50)

    await graphiti.add_episode(
        name="falcon_q3_rename",
        episode_body=(
            "Project Falcon has been officially renamed to FalconTrack. "
            "The team has grown to 15 engineers. "
            "The new estimated launch is Q2 2026."
        ),
        source=EpisodeType.text,
        source_description="Q3 product update",
        reference_time=q3_time,
        group_id=group_id,
    )

    await graphiti.add_episode(
        name="falcon_q3_budget",
        episode_body=(
            "FalconTrack budget has been increased to $2,500,000. "
            "Alice Zhang remains the project lead."
        ),
        source=EpisodeType.text,
        source_description="Q3 financial review",
        reference_time=q3_time,
        group_id=group_id,
    )

    # ------------------------------------------------------------------
    # Now search across different temporal contexts
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Searching with different temporal queries")
    print("=" * 72)

    queries_and_context = [
        (
            "What is the budget for Project Falcon?",
            "Current view (as of Q3) -- should show the latest $2,500,000 budget",
        ),
        (
            "How many engineers work on Project Falcon?",
            "Latest count should be 15 engineers (Q3 update superseded Q1 and Q2)",
        ),
        (
            "Who leads Project Falcon?",
            "Alice Zhang has been the lead from the start -- should appear in all results",
        ),
    ]

    for query, context_note in queries_and_context:
        print(f'\n  Query: "{query}"')
        print(f"  Context: {context_note}")
        edges = await graphiti.search(
            query=query,
            group_ids=[group_id],
            num_results=5,
        )
        print_edges(edges)

    # ------------------------------------------------------------------
    # Demonstrate that superseded facts carry invalid_at timestamps
    # ------------------------------------------------------------------
    print("=" * 72)
    print("Temporal metadata deep-dive")
    print("=" * 72)
    print(
        "Notice above: when facts were superseded (e.g., budget changed from "
        "$500K to $1.2M to $2.5M), the OLD edges get an invalid_at timestamp.\n"
        "This means a query like 'what is the budget' returns the *most recently "
        "valid* fact, but ALL historical facts remain in the graph.\n"
    )

    # Clean up
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
