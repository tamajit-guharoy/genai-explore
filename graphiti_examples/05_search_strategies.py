"""
Example 05: Search Strategies -- Different Ways to Query the Graph

Graphiti provides multiple search strategies with different trade-offs between
recall, precision, latency, and cost. The main approaches are:

  1. Basic search()
     A simple text-to-Cypher or embedding-similarity search. Best for simple
     factual questions.

  2. Advanced search_() with SearchConfig
     Uses configurable "recipes" that combine embedding similarity, keyword
     search, and cross-encoder re-ranking:

     Recipes (SearchRecipes.*):
       COMBINED_HYBRID_SEARCH_CROSS_ENCODER
         Best overall quality. Uses embedding + keyword search, then re-ranks
         with a cross-encoder. Higher latency but best precision.

       EDGE_HYBRID_SEARCH_RRF
         Reciprocal Rank Fusion of embedding and keyword scores. Good balance
         of speed and quality.

       EDGE_HYBRID_SEARCH_NODE_DISTANCE
         Ranks edges by graph proximity to the query entities. Fast but may
         miss indirect relationships.

  3. SearchFilters
     Constrain results by:
       - group_ids: which conversation groups to search
       - time range: valid_at / invalid_at boundaries
       - node labels: only include edges with specific entity labels

  4. center_node_uuid
     Rank edges by their graph distance from a specific entity node. Useful
     for "what's happening around this person?" queries.

All strategies return a list of EntityEdge objects with temporal metadata.
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


def print_edges(edges, heading: str = ""):
    """Pretty-print a list of edges."""
    if heading:
        print(f"\n  --- {heading} ---")
    if not edges:
        print("  (no results)")
        return
    for i, e in enumerate(edges, 1):
        print(f"  [{i}] {e.fact}")
        print(f"      {e.source_node_name} --> {e.target_node_name}")
        if hasattr(e, "distance") and e.distance is not None:
            print(f"      graph distance: {e.distance:.4f}")
        print()


async def main():
    print("=" * 72)
    print("Example 05: Search Strategies")
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
    from graphiti_core.search.search_config import SearchConfig, SearchRecipes
    from graphiti_core.search.search_filters import SearchFilters

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    group_id = "search_strategies_demo"
    now = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Seed the graph with rich data across multiple entity types
    # ------------------------------------------------------------------
    print("\n--- Seeding the graph with Acme Corp data ---\n")

    episodes_data = [
        (
            "Acme Corp was founded by Dr. Sarah Chen. "
            "Sarah holds a PhD in Operations Research from MIT."
        ),
        (
            "Acme Corp CEO Dr. Sarah Chen announced a new partnership "
            "with GlobalFreight Inc. GlobalFreight is led by CEO Tom Erikson."
        ),
        (
            "Acme Corp's RouteOptimizer Pro is used by GlobalFreight Inc. "
            "GlobalFreight also uses AutoShip from DataStream Analytics."
        ),
        (
            "FalconTrack is Acme Corp's next-gen product. It is being built "
            "by a team led by Alice Zhang and Maria Gonzalez."
        ),
        (
            "Acme Corp has offices in San Francisco (HQ) and Austin. "
            "The Austin office is led by Maria Gonzalez."
        ),
        (
            "Dr. Sarah Chen is also on the board of DataStream Analytics, "
            "a logistics AI company based in Seattle."
        ),
    ]

    for i, body in enumerate(episodes_data, 1):
        await graphiti.add_episode(
            name=f"seed_{i}",
            episode_body=body,
            source=EpisodeType.text,
            source_description="Seed data for search demo",
            reference_time=now - timedelta(hours=len(episodes_data) - i),
            group_id=group_id,
        )
        print(f"  Seeded episode {i}")

    print(f"\n  Graph seeded with {len(episodes_data)} episodes.")

    # ==================================================================
    # Strategy 1: Basic search()
    # ==================================================================
    print("\n" + "=" * 60)
    print("STRATEGY 1: Basic search()")
    print("=" * 60)
    print("  Simple query -- engine chooses the approach automatically.\n")

    edges = await graphiti.search(
        query="Who founded Acme Corp?",
        group_ids=[group_id],
        num_results=5,
    )
    print_edges(edges, "Basic search: 'Who founded Acme Corp?'")

    # ==================================================================
    # Strategy 2: SearchConfig with different recipes
    # ==================================================================
    print("\n" + "=" * 60)
    print("STRATEGY 2: Advanced search_() with SearchConfig recipes")
    print("=" * 60)
    print(
        "  SearchConfig provides fine-grained control over the search "
        "algorithm.\n"
    )

    query = "What products does Acme Corp offer?"

    # --- Recipe 1: COMBINED_HYBRID_SEARCH_CROSS_ENCODER ---
    print("  Recipe 1: COMBINED_HYBRID_SEARCH_CROSS_ENCODER")
    print("  (Best quality: embedding + keyword + cross-encoder re-rank)\n")

    config_ce = SearchConfig(
        recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
        num_results=5,
    )
    try:
        edges_ce = await graphiti.search_(
            query=query,
            group_ids=[group_id],
            search_config=config_ce,
        )
        print_edges(edges_ce, f"Results ({len(edges_ce)} edges)")
    except Exception as e:
        print(f"  (cross-encoder recipe not available: {e})\n")

    # --- Recipe 2: EDGE_HYBRID_SEARCH_RRF ---
    print("  Recipe 2: EDGE_HYBRID_SEARCH_RRF")
    print("  (Good balance: Reciprocal Rank Fusion of embedding + keyword)\n")

    config_rrf = SearchConfig(
        recipe=SearchRecipes.EDGE_HYBRID_SEARCH_RRF,
        num_results=5,
    )
    edges_rrf = await graphiti.search_(
        query=query,
        group_ids=[group_id],
        search_config=config_rrf,
    )
    print_edges(edges_rrf, f"Results ({len(edges_rrf)} edges)")

    # --- Recipe 3: EDGE_HYBRID_SEARCH_NODE_DISTANCE ---
    print("  Recipe 3: EDGE_HYBRID_SEARCH_NODE_DISTANCE")
    print("  (Fast: rank by graph proximity to query entities)\n")

    config_nd = SearchConfig(
        recipe=SearchRecipes.EDGE_HYBRID_SEARCH_NODE_DISTANCE,
        num_results=5,
    )
    edges_nd = await graphiti.search_(
        query=query,
        group_ids=[group_id],
        search_config=config_nd,
    )
    print_edges(edges_nd, f"Results ({len(edges_nd)} edges)")

    # ==================================================================
    # Strategy 3: SearchFilters for temporal / label constraints
    # ==================================================================
    print("\n" + "=" * 60)
    print("STRATEGY 3: SearchFilters -- Temporal & label-based filtering")
    print("=" * 60)

    # Filter by time range: only facts from the last 1 hour (ep. 1-2)
    one_hour_ago = now - timedelta(hours=2)
    filters_recent = SearchFilters(
        group_ids=[group_id],
        valid_at_start=one_hour_ago,
        valid_at_end=now,
    )

    edges_recent = await graphiti.search(
        query="What partnerships does Acme Corp have?",
        group_ids=[group_id],
        search_filter=filters_recent,
        num_results=5,
    )
    print_edges(edges_recent, "Facts from the last 2 hours only")

    # Filter by entity label (if labels are used in your graph)
    # Note: Graphiti assigns "Person", "Organization", "Product", etc. labels
    filters_labels = SearchFilters(
        group_ids=[group_id],
        # Hypothetical label filter -- exact API depends on graphiti_core version
        # node_labels=["Person"],
    )
    print("  Label filtering: See SearchFilters.node_labels in your version's API.\n")

    # ==================================================================
    # Strategy 4: center_node_uuid -- Graph proximity ranking
    # ==================================================================
    print("=" * 60)
    print("STRATEGY 4: center_node_uuid -- Graph-proximity ranking")
    print("=" * 60)
    print(
        "  Rank edges by distance from a specific entity. Useful for\n"
        "  'what's happening around this person/entity?' queries.\n"
    )

    # First, find edges containing Dr. Sarah Chen
    edges_all = await graphiti.search(
        query="Dr. Sarah Chen",
        group_ids=[group_id],
        num_results=10,
    )

    if edges_all:
        # Use the first edge's source_node_uuid as center
        center_uuid = edges_all[0].source_node_uuid
        print(f"  Using center_node: {edges_all[0].source_node_name}")
        print(f"  UUID: {center_uuid}\n")

        # Search with proximity ranking
        edges_proximity = await graphiti.search(
            query="What does this person do?",
            group_ids=[group_id],
            center_node_uuid=center_uuid,
            num_results=5,
        )
        print_edges(edges_proximity, "Edges ranked by proximity to Sarah Chen")

    # ==================================================================
    # Summary
    # ==================================================================
    print("=" * 60)
    print("Strategy Comparison")
    print("=" * 60)
    print("""
  Strategy                              Quality   Speed    Use Case
  ------------------------------------  -------   ------   -------------------------
  Basic search()                        Good      Fast     Simple factual questions
  COMBINED_HYBRID_SEARCH_CROSS_ENCODER  Best      Slow     High-precision retrieval
  EDGE_HYBRID_SEARCH_RRF                Better    Medium   Good general-purpose
  EDGE_HYBRID_SEARCH_NODE_DISTANCE      Good      Fast     "What's around X?"
  SearchFilters                         --        --       Constrain by time/label
  center_node_uuid                      --        --       Entity-centric ranking
""")

    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
