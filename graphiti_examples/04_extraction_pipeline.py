"""
Example 04: Extraction Pipeline -- How Episodes Become Graph Entities

When you call add_episode(), Graphiti runs a multi-stage extraction pipeline:

  1. Entity extraction
     The LLM identifies named entities (people, organizations, products,
     locations, concepts) from the episode body.

  2. Relationship extraction
     The LLM identifies relationships (edges) between those entities, with
     descriptive fact strings.

  3. Node resolution
     Graphiti checks if extracted entities already exist in the graph (by
     name similarity). If so, it merges them; if not, it creates new nodes.

  4. Edge creation
     New relationships are written to the graph with temporal metadata
     (valid_at / invalid_at) based on the episode's reference_time.

  5. Episode linking
     All extracted entities and edges are linked back to the source episode
     node, preserving provenance.

This example adds episodes and then uses retrieve_episodes() to inspect what
was extracted. We'll examine the entity nodes, the edges (relationships), and
how everything traces back to the original episode.
"""

import asyncio
import os
import sys

from datetime import datetime, timezone

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


# ===================================================================
#  Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 04: Extraction Pipeline -- Deep Dive")
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
    from graphiti_core.nodes import EpisodeType, EntityNode

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    group_id = "extraction_pipeline_demo"
    now = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Phase 1: Add episodes
    # ------------------------------------------------------------------
    print("\n>>> Phase 1: Adding episodes (triggers extraction pipeline)")

    ep1 = await graphiti.add_episode(
        name="pipeline_partners",
        episode_body=(
            "Acme Corp has partnered with DataStream Analytics to integrate "
            "real-time tracking into FalconTrack. DataStream's CEO, Priya Patel, "
            "signed the partnership agreement last week. The integration will "
            "be led by Alice Zhang from Acme and Raj Mehta from DataStream."
        ),
        source=EpisodeType.text,
        source_description="Partnership announcement",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added episode 1: '{ep1.name}'  (uuid: {ep1.uuid})")

    ep2 = await graphiti.add_episode(
        name="pipeline_acquisition",
        episode_body=(
            "Acme Corp acquired a small AI startup called MindForge AI for "
            "$45 million. MindForge was founded by Dr. Elena Voss in 2022 and "
            "specializes in predictive logistics models. The acquisition will "
            "strengthen FalconTrack's routing engine. Elena Voss will join Acme "
            "as Director of AI Research."
        ),
        source=EpisodeType.text,
        source_description="Acquisition news",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added episode 2: '{ep2.name}'  (uuid: {ep2.uuid})")

    # ------------------------------------------------------------------
    # Phase 2: Retrieve episodes and inspect extraction results
    # ------------------------------------------------------------------
    print("\n>>> Phase 2: Retrieving episodes to inspect extracted data")

    # Retrieve all episodes for this group
    episodes = await graphiti.retrieve_episodes(group_ids=[group_id])
    print(f"\n  Retrieved {len(episodes)} episode(s) for group '{group_id}'")

    for ep in episodes:
        print(f"\n  {'=' * 55}")
        print(f"  Episode: {ep.name}")
        print(f"  UUID:    {ep.uuid}")
        print(f"  Source:  {ep.source} ({ep.source_description})")
        print(f"  Body preview: {ep.body[:120]}...")

        # Each episode has entity_edges (the extracted relationships).
        # These are EntityEdge objects linking source_node --> target_node.
        if hasattr(ep, "entity_edges") and ep.entity_edges:
            print(f"\n  --- Extracted relationships ({len(ep.entity_edges)}) ---")
            for edge in ep.entity_edges:
                print(f"  [{edge.source_node_name}] --[{edge.fact}]--> [{edge.target_node_name}]")
                if edge.valid_at:
                    print(f"       valid_at: {edge.valid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        else:
            print("\n  (no entity_edges attribute on episode -- "
                  "they are stored as graph edges directly)")

        print(f"\n  --- Episode metadata ---")
        print(f"  created_at:  {ep.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"  group_id:    {ep.group_id}")

    # ------------------------------------------------------------------
    # Phase 3: Search the graph to see the integrated knowledge
    # ------------------------------------------------------------------
    print("\n>>> Phase 3: Search the integrated knowledge graph\n")

    edges = await graphiti.search(
        query="What companies has Acme Corp partnered with or acquired?",
        group_ids=[group_id],
        num_results=10,
    )

    print(f"  Found {len(edges)} relationship(s):")
    for i, e in enumerate(edges, 1):
        print(f"\n  [{i}] Fact:        {e.fact}")
        print(f"      Source:      {e.source_node_name}")
        print(f"      Target:      {e.target_node_name}")
        print(f"      Valid at:    {e.valid_at.strftime('%Y-%m-%d %H:%M UTC') if e.valid_at else 'N/A'}")
        print(f"      Invalid at:  {e.invalid_at.strftime('%Y-%m-%d %H:%M UTC') if e.invalid_at else 'N/A'}")

    # ------------------------------------------------------------------
    # Summary diagram
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Extraction Pipeline Flow")
    print("=" * 72)
    print("""
  Episode text
       |
       v
  [1] LLM Entity Extraction   --->  Person / Organization / Product / ...
       |
       v
  [2] LLM Relationship Extract --->  (Entity A) --[fact]--> (Entity B)
       |
       v
  [3] Node Resolution         --->  Deduplicate / merge by name similarity
       |
       v
  [4] Edge Creation           --->  Temporal edges with valid_at / invalid_at
       |
       v
  [5] Episode Linking         --->  All nodes + edges trace back to episode
""")

    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
