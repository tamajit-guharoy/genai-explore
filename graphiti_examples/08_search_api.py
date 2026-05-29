"""
Example 08: Search API Deep Dive

This example explores Graphiti's search functionality in depth:

  1. search() vs search_() -- understanding the two search entry points
  2. SearchConfig -- controlling every aspect of retrieval
  3. SearchFilters -- narrowing results by entity type, time, and group
  4. center_node_uuid -- proximity-based relevance ranking
  5. Interpreting EdgeSearchResult and NodeSearchResult objects
  6. Search recipes and their trade-offs

The example populates the graph with Acme Corp data, then runs a series of
targeted searches to demonstrate each feature.
"""

import asyncio
import os
import socket
import sys

from datetime import datetime, timezone
from typing import Optional

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


# ---------------------------------------------------------------------------
# Helper to print section headers
# ---------------------------------------------------------------------------
def section(title: str):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}\n")


async def main():
    print("=" * 72)
    print("Example 08: Search API Deep Dive")
    print("=" * 72)

    # ---- connectivity check -------------------------------------------------
    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  To run this example, start a Neo4j instance and set:\n"
            f"    NEO4J_URI={NEO4J_URI}  NEO4J_USER={NEO4J_USER}  NEO4J_PASSWORD=...\n"
            f"  The easiest way is via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    from graphiti_core.search.search_config import SearchConfig, SearchRecipes
    from graphiti_core.search.search_filters import SearchFilters
    from graphiti_core.edges import EntityEdge

    # ---- initialise ---------------------------------------------------------
    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    print("\nBuilding indices and constraints ...")
    await graphiti.build_indices_and_constraints()

    group_id = "search_api_demo"
    now = datetime.now(timezone.utc)

    # ---- seed the graph with realistic episodes -----------------------------
    section("Seeding the knowledge graph")

    episodes_data = [
        (
            "acme_overview",
            (
                "Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco. "
                "Sarah is the CEO and has a PhD in Computer Science from Stanford. "
                "Acme builds AI-powered supply chain optimization software."
            ),
        ),
        (
            "route_optimizer",
            (
                "Acme Corp's flagship product is RouteOptimizer Pro, launched in 2021. "
                "It uses machine learning to reduce delivery costs by up to 35%. "
                "James Miller is the VP of Engineering who led the development. "
                "The product is built on a microservices architecture running on AWS."
            ),
        ),
        (
            "austin_office",
            (
                "In 2023, Acme Corp opened an office in Austin, Texas. "
                "The Austin office is led by Maria Gonzalez, Regional Director. "
                "Maria previously led operations out of Denver for a competitor. "
                "The Austin team has 45 engineers focused on real-time routing."
            ),
        ),
        (
            "customers",
            (
                "Acme Corp's customers include GlobalFreight Inc and QuickShip Logistics. "
                "GlobalFreight uses RouteOptimizer Pro for their entire US fleet of 1200 trucks. "
                "QuickShip began a pilot program in Q2 2024 with 200 vehicles. "
                "Dr. Sarah Chen personally presented the roadmap to both clients."
            ),
        ),
        (
            "fundraising",
            (
                "Acme Corp raised a $30M Series B in 2024 led by VentureCap Partners. "
                "The funds will be used to expand the engineering team and open a "
                "European office. Board members include Sarah Chen and VentureCap partner "
                "David Park."
            ),
        ),
        (
            "competition",
            (
                "Acme Corp's main competitor is LogiTech Solutions, founded by Alice Wu. "
                "LogiTech raised a $50M Series C in 2023. Another competitor, "
                "ShipSmart Inc, focuses exclusively on last-mile delivery optimization. "
                "Acme differentiates through predictive AI features that competitors lack."
            ),
        ),
    ]

    for name, body in episodes_data:
        ep = await graphiti.add_episode(
            name=name,
            episode_body=body,
            source=EpisodeType.text,
            source_description="Tutorial example data",
            reference_time=now,
            group_id=group_id,
        )
        print(f"  Added episode: {ep.name}  [{ep.uuid[:8]}...]")

    # ---- 1. search() vs search_() -----------------------------------------
    section("1. search() vs search_()  -- two entry points")

    print("  search() returns EdgeSearchResult objects (relationships only).")
    print("  search_() returns a SearchResult with both nodes and edges.\n")

    # search() -- returns list[EntityEdge]
    print('  --- search() with query "Who founded Acme?" ---')
    edges: list[EntityEdge] = await graphiti.search(
        query="Who founded Acme Corp?",
        group_ids=[group_id],
        num_results=3,
    )
    print(f"  Type of result: {type(edges).__name__}")
    print(f"  Number of edges: {len(edges)}")
    for edge in edges:
        print(f"    Edge fact: {edge.fact}")
        print(f"      Source node: {edge.source_node_uuid}")
        print(f"      Target node: {edge.target_node_uuid}")
        print(f"      Valid at:    {edge.valid_at}")
        print()

    # search_() -- returns a rich SearchResult
    print('  --- search_() with query "Who founded Acme?" ---')
    from graphiti_core.search.search_result import SearchResult

    search_result: SearchResult = await graphiti.search_(
        query="Who founded Acme Corp?",
        group_ids=[group_id],
        num_results=3,
    )
    print(f"  Type of result: {type(search_result).__name__}")
    print(f"  Number of nodes:  {len(search_result.nodes)}")
    print(f"  Number of edges:  {len(search_result.edges)}")
    for node in search_result.nodes[:3]:
        print(f"    Node: {node.name}  (label: {node.label}, uuid: {node.uuid[:8]}...)")
    for edge in search_result.edges[:3]:
        print(f"    Edge: {edge.fact}")
    print()
    print("  Key takeaway: use search() when you only need relationships;")
    print("  use search_() when you also want entity nodes in the results.")

    # ---- 2. SearchConfig with all parameters --------------------------------
    section("2. SearchConfig -- full control over retrieval")

    print("  SearchConfig wraps parameters that control how Graphiti searches.\n")

    # Demonstrate a basic config
    config = SearchConfig(
        recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
        num_results=5,
        max_depth=3,
        reranker="cross-encoder",
    )
    print("  Config used:")
    print(f"    recipe:       {config.recipe}")
    print(f"    num_results:  {config.num_results}")
    print(f"    max_depth:    {config.max_depth}")
    print(f"    reranker:     {config.reranker}")

    results = await graphiti.search_(
        query="What products does Acme offer?",
        group_ids=[group_id],
        config=config,
    )
    print(f"\n  Search with config returned {len(results.edges)} edges, {len(results.nodes)} nodes.")

    # ---- 3. SearchFilters ---------------------------------------------------
    section("3. SearchFilters -- narrowing results")

    # Create a SearchConfig with filters
    filters = SearchFilters(
        group_ids=[group_id],
    )
    # Note: SearchFilters also supports:
    #   - entity_labels: filter by entity type (e.g. ["Person", "Organization"])
    #   - temporal constraints: valid_at / valid_before / valid_after
    # These will be demonstrated later.

    config_with_filters = SearchConfig(
        recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
        num_results=10,
        filters=filters,
    )

    print("  Filtering by group_ids keeps results within this tutorial's data.")
    print(f"  (All our episodes use group_id='{group_id}')\n")

    # ---- 4. Search recipes and their trade-offs -----------------------------
    section("4. Search recipes -- trade-offs at a glance")

    recipes = {
        "HNSW_KNN": SearchRecipes.HNSW_KNN,
        "HYBRID_SEARCH_CROSS_ENCODER": SearchRecipes.HYBRID_SEARCH_CROSS_ENCODER,
        "COMBINED_HYBRID_SEARCH_CROSS_ENCODER": SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    }

    print(f"{'Recipe':<45} {'Speed':<10} {'Accuracy':<10} {'Use case'}")
    print(f"{'-' * 45} {'-' * 10} {'-' * 10} {'-' * 30}")
    comparisons = [
        ("HNSW_KNN", "Fast", "Moderate",
         "Quick vector-only lookups; best for simple fact retrieval"),
        ("HYBRID_SEARCH_CROSS_ENCODER", "Moderate", "High",
         "Hybrid vector + keyword with reranking; good balance"),
        ("COMBINED_HYBRID_SEARCH_CROSS_ENCODER", "Slower", "Highest",
         "Multiple retrieval strategies combined; best for complex queries"),
    ]
    for name, speed, accuracy, use_case in comparisons:
        print(f"{name:<45} {speed:<10} {accuracy:<10} {use_case}")

    print()
    print("  Demonstrating HNSW_KNN (fastest, least accurate):")
    fast_config = SearchConfig(recipe=SearchRecipes.HNSW_KNN, num_results=3)
    fast_results = await graphiti.search_(
        query="Acme Corp funding",
        group_ids=[group_id],
        config=fast_config,
    )
    print(f"    Got {len(fast_results.edges)} edges, {len(fast_results.nodes)} nodes.")

    print()
    print("  Demonstrating COMBINED_HYBRID_SEARCH_CROSS_ENCODER (most accurate):")
    best_config = SearchConfig(
        recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
        num_results=3,
    )
    best_results = await graphiti.search_(
        query="Acme Corp funding",
        group_ids=[group_id],
        config=best_config,
    )
    print(f"    Got {len(best_results.edges)} edges, {len(best_results.nodes)} nodes.")
    for e in best_results.edges:
        print(f"    - {e.fact}")

    # ---- 5. center_node_uuid for proximity-based ranking --------------------
    section("5. center_node_uuid -- proximity-based ranking")

    print(
        "  When you pass center_node_uuid, results closer to that node in the\n"
        "  graph (within max_depth hops) are ranked higher.\n"
    )

    # First, find an entity node to use as center. Let's find "Sarah Chen".
    node_results = await graphiti.search_(
        query="Dr. Sarah Chen",
        group_ids=[group_id],
        num_results=1,
    )
    if node_results.nodes:
        center_node = node_results.nodes[0]
        print(f"  Using center node: {center_node.name} (uuid: {center_node.uuid[:8]}...)")

        # Search without center
        no_center_config = SearchConfig(
            recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
            num_results=5,
        )
        no_center = await graphiti.search_(
            query="tell me about people and companies",
            group_ids=[group_id],
            config=no_center_config,
        )

        # Search with center -- results near Sarah Chen get boosted
        center_config = SearchConfig(
            recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
            num_results=5,
            center_node_uuid=center_node.uuid,
            max_depth=2,
        )
        with_center = await graphiti.search_(
            query="tell me about people and companies",
            group_ids=[group_id],
            config=center_config,
        )

        print(f"\n  Without center_node_uuid: {len(no_center.edges)} edges")
        for e in no_center.edges[:3]:
            print(f"    {e.fact}")

        print(f"\n  With center_node_uuid (Sarah Chen): {len(with_center.edges)} edges")
        for e in with_center.edges[:3]:
            print(f"    {e.fact}")
        print("\n  Results near Sarah Chen rise to the top when center_node_uuid is set.")
    else:
        print("  Could not find Sarah Chen node to demonstrate center_node_uuid.")

    # ---- 6. Understanding result objects ------------------------------------
    section("6. Interpreting EdgeSearchResult and NodeSearchResult")

    print("  EdgeSearchResult (EntityEdge) key fields:\n")
    sample_edge = edges[0] if edges else None
    if sample_edge:
        import inspect

        edge_fields = [
            ("uuid", "Unique edge identifier"),
            ("fact", "The relationship fact as text"),
            ("source_node_uuid", "UUID of the source entity node"),
            ("target_node_uuid", "UUID of the target entity node"),
            ("valid_at", "When this fact became true (timestamp)"),
            ("invalid_at", "When this fact ceased to be true (None if still valid)"),
            ("created_at", "When this edge was created in the graph"),
            ("fact_embedding", "Vector embedding of the fact text"),
        ]
        for field_name, desc in edge_fields:
            val = getattr(sample_edge, field_name, "<not available>")
            print(f"    {field_name}:")
            print(f"      Value: {val}")
            print(f"      Description: {desc}")
            print()

    print("  NodeSearchResult (EntityNode) key fields:\n")
    if search_result.nodes:
        sample_node = search_result.nodes[0]
        node_fields = [
            ("uuid", "Unique node identifier"),
            ("name", "Entity name (e.g., 'Sarah Chen', 'Acme Corp')"),
            ("label", "Entity type label (e.g., 'Person', 'Organization')"),
            ("embedding", "Vector embedding of the entity summary"),
            ("summary", "Summarized description of the entity"),
            ("group_id", "Group this entity belongs to"),
            ("created_at", "When this node was created"),
        ]
        for field_name, desc in node_fields:
            val = getattr(sample_node, field_name, "<not available>")
            print(f"    {field_name}:")
            val_str = str(val)
            if len(val_str) > 80:
                val_str = val_str[:77] + "..."
            print(f"      Value: {val_str}")
            print(f"      Description: {desc}")
            print()

    # ---- cleanup -----------------------------------------------------------
    section("Cleanup")

    # Remove the test group from the graph
    print(f"Deleting group {group_id} ...")
    await graphiti.delete_group(group_id=group_id)
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
