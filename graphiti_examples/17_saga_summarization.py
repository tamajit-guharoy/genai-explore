"""
Example 17: Saga Summarization (v0.29.0+)

A "saga" is a collection of related episodes that together tell a larger story.
Graphiti's saga abstraction (available in v0.29.0+) lets you:

  1. Group episodes under a common saga_id
  2. Call summarize_saga(saga_id) to produce a narrative rollup of the
     entire multi-episode arc
  3. Distinguish saga-level summaries from individual episode facts
     and community-level aggregations

In this example, we follow a customer's journey across five stages:

    Signup  ->  Onboarding  ->  First Purchase  ->  Support Issue  ->  Resolution

The saga captures the holistic customer story, while individual episodes
capture specific facts at each stage.
"""

import asyncio
import os
import socket
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
        "WARNING: OPENAI_API_KEY is not set. Graphiti needs an LLM for extraction.\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
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


def print_edges(edges, heading: str = ""):
    """Pretty-print a list of edges with their temporal metadata."""
    if heading:
        print(f"\n  --- {heading} ---")
    if not edges:
        print("  (no results)")
        return
    for i, e in enumerate(edges, 1):
        print(f"  [{i}] {e.source_node_name} --[{e.fact}]--> {e.target_node_name}")
        if e.valid_at:
            print(f"      valid: {e.valid_at.strftime('%Y-%m-%d')}")


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 17: Saga Summarization")
    print("=" * 72)
    print(
        "\n"
        "  A saga groups related episodes into a narrative arc.\n"
        "  Unlike individual episodes (which capture atomic facts) or\n"
        "  communities (which cluster entities), a saga provides a\n"
        "  multi-step story rollup.\n"
    )

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

    # ------------------------------------------------------------------
    # The Customer Journey: Jane from QuickShop
    # ------------------------------------------------------------------
    # We assign one saga_id across all episodes so Graphiti knows they
    # form a single narrative arc.
    saga_id = "jane_quickshop_onboarding"
    group_id = "customer_journey"

    # Timeline: Day 0, 1, 5, 10, 12
    base_time = datetime.now(timezone.utc)

    print("\n" + "=" * 72)
    print("Customer Journey: Jane from QuickShop")
    print("=" * 72)

    # -- Episode 1: Signup --------------------------------------------------
    print("\n>>> Episode 1 (Day 0): Jane signs up")
    print("-" * 50)

    await graphiti.add_episode(
        name="jane_signup",
        episode_body=(
            "Jane Mitchell, VP of Operations at QuickShop Retail, signed up "
            "for Acme Corp's RouteOptimizer Pro on a 30-day free trial. "
            "QuickShop operates 45 stores across the Midwest."
        ),
        source=EpisodeType.text,
        source_description="Sales CRM entry",
        reference_time=base_time,
        group_id=group_id,
        saga_id=saga_id,
    )
    print("  Added: signup episode (saga_id={saga_id})")

    # -- Episode 2: Onboarding ----------------------------------------------
    print("\n>>> Episode 2 (Day 1): Onboarding call")
    print("-" * 50)

    day_1 = base_time + timedelta(days=1)
    await graphiti.add_episode(
        name="jane_onboarding",
        episode_body=(
            "During onboarding, Jane's team was trained by Acme's solutions "
            "architect, Tom Hardy. QuickShop plans to integrate RouteOptimizer "
            "Pro with their existing ERP system, Oracle NetSuite. "
            "Jane's primary goal is reducing last-mile delivery costs."
        ),
        source=EpisodeType.text,
        source_description="Onboarding session notes",
        reference_time=day_1,
        group_id=group_id,
        saga_id=saga_id,
    )
    print("  Added: onboarding episode")

    # -- Episode 3: First Purchase ------------------------------------------
    print("\n>>> Episode 3 (Day 5): First purchase made")
    print("-" * 50)

    day_5 = base_time + timedelta(days=5)
    await graphiti.add_episode(
        name="jane_first_purchase",
        episode_body=(
            "After the trial, QuickShop purchased RouteOptimizer Pro for 20 "
            "of their 45 stores. The annual contract is valued at $120,000. "
            "Jane negotiated a 15% discount for a 2-year commitment. "
            "The implementation is scheduled for Q3 2025."
        ),
        source=EpisodeType.text,
        source_description="Contract signed",
        reference_time=day_5,
        group_id=group_id,
        saga_id=saga_id,
    )
    print("  Added: first purchase episode")

    # -- Episode 4: Support Issue -------------------------------------------
    print("\n>>> Episode 4 (Day 10): Support issue reported")
    print("-" * 50)

    day_10 = base_time + timedelta(days=10)
    await graphiti.add_episode(
        name="jane_support_issue",
        episode_body=(
            "Jane reported a critical issue: the route optimization algorithm "
            "is not accounting for stores with limited loading dock hours. "
            "Three stores in Chicago have specific dock schedules (6-10 AM only) "
            "that the system is ignoring, causing missed delivery windows. "
            "Ticket #QS-4421 was opened."
        ),
        source=EpisodeType.text,
        source_description="Support ticket QS-4421",
        reference_time=day_10,
        group_id=group_id,
        saga_id=saga_id,
    )
    print("  Added: support issue episode")

    # -- Episode 5: Resolution ----------------------------------------------
    print("\n>>> Episode 5 (Day 12): Issue resolved")
    print("-" * 50)

    day_12 = base_time + timedelta(days=12)
    await graphiti.add_episode(
        name="jane_resolution",
        episode_body=(
            "Acme Corp deployed a hotfix for the loading dock constraint issue. "
            "The fix adds a 'dock_hours' parameter to store profiles in "
            "RouteOptimizer Pro. Jane confirmed the fix works for the three "
            "affected Chicago stores. QuickShop decided to expand to all 45 stores."
        ),
        source=EpisodeType.text,
        source_description="Support ticket resolution",
        reference_time=day_12,
        group_id=group_id,
        saga_id=saga_id,
    )
    print("  Added: resolution episode")

    # ------------------------------------------------------------------
    # Now query individual episode facts (specific, atomic)
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Query 1: Individual Episode Facts (specific details)")
    print("=" * 72)

    queries = [
        "What was the issue Jane reported?",
        "What integration does QuickShop use?",
        "What discount did Jane negotiate?",
    ]

    for query in queries:
        print(f'\n  Query: "{query}"')
        edges = await graphiti.search(
            query=query,
            group_ids=[group_id],
            num_results=3,
        )
        print_edges(edges)

    # ------------------------------------------------------------------
    # Demonstrate saga summarization (narrative rollup)
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Query 2: Saga-Level Summary (the big picture)")
    print("=" * 72)

    print(
        "\n  Individual episodes give you atomic facts. A saga summarization\n"
        "  gives you a narrative rollup -- the "story" across all episodes.\n"
        "  This is different from:\n"
        "    - Individual episodes: atomic facts per step\n"
        "    - Community detection: entity clustering by connectedness\n"
        "    - Saga: temporal narrative across a sequence of related episodes\n"
    )

    # We call summarize_saga(saga_id) to get a narrative summary.
    # This uses the LLM to synthesize all episodes under this saga_id.
    print(f"\n  Summarizing saga: {saga_id}")
    saga_summary = await graphiti.summarize_saga(saga_id=saga_id)

    if saga_summary:
        print(f"\n  Saga Summary:")
        print(f"  {'=' * 50}")
        print(f"  {saga_summary}")
        print(f"  {'=' * 50}")
    else:
        print("  (no saga summary returned -- may not be supported in this version)")

    # ------------------------------------------------------------------
    # Query saga-summarized content (search across the saga's embeddings)
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Query 3: Searching Saga-Summarized Content")
    print("=" * 72)

    print(
        "\n  Sagas also participate in search. You can query across all\n"
        "  episodes belonging to a saga to find holistic answers.\n"
    )

    saga_query = "How did QuickShop's experience with Acme Corp evolve?"
    print(f'  Query: "{saga_query}"')
    edges = await graphiti.search(
        query=saga_query,
        group_ids=[group_id],
        num_results=3,
    )
    print_edges(edges)

    # ------------------------------------------------------------------
    # Explain how saga differs from community
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Saga vs Community vs Episode -- Key Differences")
    print("=" * 72)

    print(
        """
  | Dimension       | Episode                  | Saga                       | Community               |
  |-----------------|--------------------------|----------------------------|-------------------------|
  | Scope           | Single text chunk        | Multi-episode narrative    | Entity cluster          |
  | Grouping        | group_id                 | saga_id                    | Automatic (algorithmic) |
  | Temporal        | Single point in time     | Time-spanning arc          | No temporal dimension   |
  | Granularity     | Atomic facts             | Story-level summary        | Entity relationships    |
  | Use case        | "What did Jane sign?"    | "What was Jane's journey?" | "Who is connected to?"  |
  | Created by      | add_episode()            | summarize_saga()           | detect_communities()   |

  Think of it as:
    - Episodes = scenes in a movie
    - Saga     = the movie's plot summary
    - Community = a cast of characters who appear together
"""
    )

    # -- Cleanup ------------------------------------------------------------
    await graphiti.close()
    print("\nDone. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
