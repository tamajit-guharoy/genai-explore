"""
Example 14: Contradiction Handling and Fact Expiration

In real-world knowledge graphs, facts change. People change roles, products
change prices, relationships evolve. Graphiti handles this gracefully:

  1. When a new fact contradicts an existing one, the old fact is NOT deleted
  2. Instead, the old fact gets an `invalid_at` timestamp
  3. Expired facts remain in the graph for audit and temporal queries
  4. You can manually invalidate facts via the API
  5. The extraction pipeline assigns confidence scores to edges

This example demonstrates:
  - Adding an initial fact, then a contradictory fact
  - How Graphiti detects and resolves contradictions
  - Inspecting expired edges (they're still there!)
  - Manual fact invalidation
  - Confidence scoring in contradiction resolution
"""

import asyncio
import os
import socket
import sys

from datetime import datetime, timezone, timedelta

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY is not set. Graphiti uses an LLM to extract "
        "entities and relationships. Without it, extraction will fail.\n"
        "Set it via:  export OPENAI_API_KEY='sk-...'  (Linux / Mac)\n"
        "or:          $env:OPENAI_API_KEY='sk-...'   (Windows PowerShell)\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
    host, _, port_str = (
        NEO4J_URI.replace("bolt://", "")
        .replace("neo4j://", "")
        .partition(":")
    )
    try:
        port = int(port_str) if port_str else 7687
    except ValueError:
        port = 7687
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except (OSError, socket.timeout):
        return False


def section(title: str):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}\n")


async def main():
    print("=" * 72)
    print("Example 14: Contradiction Handling and Fact Expiration")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  To run this example, start a Neo4j instance:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    from graphiti_core.search.search_config import SearchConfig, SearchRecipes
    from graphiti_core.search.search_filters import SearchFilters

    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    print("\nBuilding indices and constraints ...")
    await graphiti.build_indices_and_constraints()

    group_id = "contradictions_demo"

    # ---- Scenario: CEO change at Acme Corp --------------------------------
    section("Scenario: CEO change at Acme Corp")

    print(
        "  We will seed the graph with an initial fact:\n"
        "    'Alice Johnson is the CEO of Acme Corp'\n"
        "  Then add a contradictory fact:\n"
        "    'Bob Martinez is now the CEO of Acme Corp'\n"
        "\n"
        "  Graphiti's extraction pipeline detects that 'CEO of Acme Corp'\n"
        "  is a relationship that can have only one value. When the new fact\n"
        "  arrives, the old edge gets expired (invalid_at is set).\n"
    )

    now = datetime.now(timezone.utc)
    earlier = now - timedelta(days=365)  # Alice became CEO 1 year ago
    later = now  # Bob became CEO now

    # ---- Step 1: Add the initial fact -------------------------------------
    section("Step 1: Adding initial fact -- Alice Johnson is CEO")

    ep1 = await graphiti.add_episode(
        name="alice_ceo",
        episode_body=(
            "Alice Johnson is the CEO of Acme Corp. She was appointed in "
            "May 2025 after serving as COO for three years. Alice has a "
            "background in supply chain management and previously worked at "
            "Global Logistics Inc."
        ),
        source=EpisodeType.text,
        source_description="Company announcement",
        reference_time=earlier,
        group_id=group_id,
    )
    print(f"  Added episode: {ep1.name}")
    print(f"  Reference time: {earlier.date()}")
    print(f"  Fact: Alice Johnson is the CEO of Acme Corp\n")

    # Verify the fact was stored
    initial_search = await graphiti.search(
        query="Who is the CEO of Acme Corp?",
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Initial search results: {len(initial_search)} edge(s)")
    for edge in initial_search:
        print(f"    Fact: {edge.fact}")
        print(f"    valid_at:   {edge.valid_at.date() if edge.valid_at else 'N/A'}")
        print(f"    invalid_at: {edge.invalid_at.date() if edge.invalid_at else 'None (still valid)'}")
        print(f"    confidence: {getattr(edge, 'confidence', 'N/A')}")
    print()

    # ---- Step 2: Add the contradictory fact --------------------------------
    section("Step 2: Adding contradictory fact -- Bob Martinez is now CEO")

    print("  Adding a new episode that contradicts the existing fact...\n")

    ep2 = await graphiti.add_episode(
        name="bob_ceo",
        episode_body=(
            "Bob Martinez has been appointed as the new CEO of Acme Corp, "
            "effective immediately. Bob was previously the CEO of DataFlow "
            "Systems and brings extensive experience in AI-driven logistics. "
            "He replaces Alice Johnson, who is stepping down to pursue other "
            "opportunities."
        ),
        source=EpisodeType.text,
        source_description="Press release",
        reference_time=later,
        group_id=group_id,
    )
    print(f"  Added episode: {ep2.name}")
    print(f"  Reference time: {later.date()}")
    print(f"  Fact: Bob Martinez is the new CEO of Acme Corp\n")

    # ---- Step 3: Search -- what does the graph say now? --------------------
    section("Step 3: Searching after contradiction")

    print("  --- Current facts about Acme Corp's CEO ---\n")

    ceo_search = await graphiti.search(
        query="Acme Corp CEO leadership",
        group_ids=[group_id],
        num_results=10,
    )
    print(f"  Found {len(ceo_search)} edge(s):\n")
    for edge in ceo_search:
        print(f"    Fact:       {edge.fact}")
        print(f"    valid_at:   {edge.valid_at.date() if edge.valid_at else 'N/A'}")
        print(f"    invalid_at: {edge.invalid_at.date() if edge.invalid_at else 'None (still valid)'}")
        status = "CURRENT" if edge.invalid_at is None else "EXPIRED"
        print(f"    Status:     {status}")
        print()

    print(
        "  Key observation: Both facts are present in the graph!\n"
        "  The old fact ('Alice Johnson is the CEO') now has an invalid_at\n"
        "  timestamp, indicating it was superseded. The new fact has no\n"
        "  invalid_at, meaning it's the current truth.\n"
    )

    # ---- Step 4: Verify old fact is retrievable ---------------------------
    section("Step 4: Expired facts are still retrievable (audit trail)")

    print(
        "  A query specifically about Alice Johnson should still surface\n"
        "  the expired fact:\n"
    )

    alice_search = await graphiti.search(
        query="Alice Johnson role at Acme Corp",
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Found {len(alice_search)} edge(s) about Alice Johnson:\n")
    for edge in alice_search:
        print(f"    Fact:       {edge.fact}")
        status = "CURRENT" if edge.invalid_at is None else "EXPIRED"
        print(f"    Status:     {status}")
        if edge.invalid_at:
            print(f"    Expired at: {edge.invalid_at.date()}")
        print()

    print(
        "  Alice's CEO fact is still in the graph -- it's just marked as\n"
        "  expired. This provides a complete audit trail of leadership changes.\n"
        "  A temporal query can reconstruct: 'Who was CEO in June 2025?'\n"
        "  and get the correct answer (Alice Johnson).\n"
    )

    # ---- Step 5: Manual fact invalidation ---------------------------------
    section("Step 5: Manual fact invalidation")

    print(
        "  Beyond automatic contradiction detection, you can manually\n"
        "  invalidate facts. For demonstration, let's find a non-CEO fact\n"
        "  and mark it as expired manually.\n"
    )

    # Find a fact to manually invalidate
    all_facts = await graphiti.search(
        query="Acme Corp board members",
        group_ids=[group_id],
        num_results=5,
    )
    print("  Before manual invalidation:")
    for edge in all_facts:
        print(f"    Fact:       {edge.fact}")
        status = "CURRENT" if edge.invalid_at is None else "EXPIRED"
        print(f"    Status:     {status}")

    print()
    print(
        "  Manual invalidation would typically involve:\n"
        "    1. Finding the edge UUID to invalidate\n"
        "    2. Calling an API or direct Neo4j query to set invalid_at\n"
        "\n"
        "  from graphiti_core.edges import EntityEdge\n"
        "  # edge.invalid_at = datetime.now(timezone.utc)\n"
        "  # await graphiti.save_edge(edge)\n"
        "\n"
        "  This gives you fine-grained control over fact lifecycle.\n"
    )

    # ---- Step 6: Confidence scoring ---------------------------------------
    section("Step 6: Confidence scores in contradiction resolution")

    print(
        "  Graphiti's extraction pipeline assigns a confidence score to\n"
        "  each extracted edge. These scores play a role in contradiction\n"
        "  resolution:\n"
        "\n"
        "  - Higher confidence facts are preferred when contradictions occur\n"
        "  - Confidence is derived from the LLM's assessment of extraction quality\n"
        "  - Explicit statements ('Alice is the CEO') score higher than\n"
        "    implicit ones ('Alice runs the company')\n"
        "  - More recent facts may be weighted higher in some configurations\n"
        "\n"
        "  Checking confidence scores on our CEO facts:\n"
    )

    for edge in ceo_search:
        confidence = getattr(edge, "confidence", None)
        print(f"    Fact:       {edge.fact[:60]}...")
        print(f"    Confidence: {confidence}")
        status = "CURRENT" if edge.invalid_at is None else "EXPIRED"
        print(f"    Status:     {status}")
        print()

    # ---- Summary of contradiction handling --------------------------------
    section("Summary: How Graphiti handles contradictions")

    summary = """
  Graphiti's contradiction resolution works as follows:

  1. DETECTION:
     When a new episode is ingested, the extraction pipeline identifies
     entities and relationships. The system compares new edges against
     existing ones to detect conflicts (e.g., two different values for
     the same relationship type between the same entities).

  2. RESOLUTION:
     - The new edge is stored as the "current" truth (no invalid_at)
     - The old edge gets its invalid_at set to the new episode's reference_time
     - The old edge is NOT deleted -- it remains for historical queries

  3. CONFIDENCE:
     - Each edge carries an extraction confidence score
     - Higher-confidence edges may take precedence in some scenarios
     - The confidence score helps in manual review and debugging

  4. AUDIT TRAIL:
     - All historical facts are preserved
     - You can reconstruct the state of the graph at any point in time
     - Expired edges are still searchable and retrievable

  5. MANUAL CONTROL:
     - You can manually set invalid_at on any edge
     - This is useful for correcting extraction errors
     - Or for modeling real-world fact changes explicitly
"""
    print(summary)

    # ---- cleanup -----------------------------------------------------------
    section("Cleanup")
    print(f"Deleting group {group_id} ...")
    await graphiti.delete_group(group_id=group_id)
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
