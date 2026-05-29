"""
Example 10: Community Detection and Analysis

Graphiti can discover "communities" -- clusters of related entities that form
coherent sub-graphs. This is useful for:

  1. Understanding the natural structure of your knowledge graph
  2. Improving retrieval: community-aware search can surface broader context
  3. Summarization: each community gets a name and summary

The workflow:
  1. Add a substantial set of episodes covering multiple topics
  2. Run build_communities() to detect community structure
  3. Inspect community nodes and their properties
  4. See how community-aware search differs from flat search

In this example, we'll seed the graph with data about two distinct fictional
companies -- Acme Corp (logistics AI) and MediCore (healthtech) -- plus some
overlapping entities to create interesting community structure.
"""

import asyncio
import os
import socket
import sys

from datetime import datetime, timezone

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
    print("Example 10: Community Detection and Analysis")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  To run this example, start a Neo4j instance and set:\n"
            f"    NEO4J_URI={NEO4J_URI}  NEO4J_USER={NEO4J_USER}  NEO4J_PASSWORD=...\n"
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

    group_id = "communities_demo"
    now = datetime.now(timezone.utc)

    # ---- Seed the graph with diverse episodes ------------------------------
    section("Seeding the graph with multi-company data")

    # --- Acme Corp episodes (logistics AI company) ---
    acme_episodes = [
        (
            "acme_founding",
            (
                "Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco. "
                "Sarah is the CEO and holds a PhD in Computer Science. "
                "Acme builds AI-powered supply chain optimization software."
            ),
        ),
        (
            "acme_product",
            (
                "RouteOptimizer Pro is Acme Corp's flagship product. It uses ML "
                "to reduce delivery costs by up to 35%. James Miller, VP of "
                "Engineering, led the development team."
            ),
        ),
        (
            "acme_customers",
            (
                "GlobalFreight Inc and QuickShip Logistics are Acme Corp customers. "
                "GlobalFreight uses RouteOptimizer Pro for their fleet of 1200 trucks. "
                "QuickShip started a pilot in Q2 2024."
            ),
        ),
        (
            "acme_funding",
            (
                "Acme Corp raised $30M Series B in 2024 from VentureCap Partners. "
                "David Park from VentureCap joined the board. The funding supports "
                "European expansion and engineering growth."
            ),
        ),
        (
            "acme_austin",
            (
                "Acme Corp's Austin office opened in 2023, led by Maria Gonzalez. "
                "The office has 45 engineers focused on real-time routing algorithms."
            ),
        ),
    ]

    # --- MediCore episodes (healthtech company) ---
    medicore_episodes = [
        (
            "medicore_founding",
            (
                "MediCore Health was founded in 2018 by Dr. Priya Patel in Boston. "
                "Priya is the CTO and has a background in bioinformatics. "
                "MediCore develops AI-powered diagnostic imaging tools."
            ),
        ),
        (
            "medicore_product",
            (
                "MediCore's platform, DiagnosAI, helps radiologists detect anomalies "
                "in medical scans with 94% accuracy. It was FDA-cleared in 2022. "
                "The lead scientist is Dr. Robert Kim."
            ),
        ),
        (
            "medicore_customers",
            (
                "MediCore's customers include MassGeneral Hospital and Cleveland Clinic. "
                "MassGeneral uses DiagnosAI in their radiology department. "
                "Cleveland Clinic began a pilot in early 2024."
            ),
        ),
        (
            "medicore_funding",
            (
                "MediCore raised a $45M Series C in 2023. The round was led by "
                "HealthVentures Capital. The funding will expand the AI research "
                "team and support European regulatory approvals."
            ),
        ),
        (
            "medicore_partnership",
            (
                "MediCore partnered with CloudMed Infrastructure in 2024 to deploy "
                "DiagnosAI on their HIPAA-compliant cloud platform. "
                "CloudMed is led by CEO Thomas Park."
            ),
        ),
    ]

    # --- Overlapping entities (people who span both worlds) ---
    bridging_episodes = [
        (
            "venture_capital_connections",
            (
                "VentureCap Partners, led by David Park, invested in both Acme Corp "
                "and MediCore Health. David Park sits on the board of both companies. "
                "His brother Thomas Park is CEO of CloudMed Infrastructure. "
                "David previously worked at HealthVentures Capital."
            ),
        ),
        (
            "conference",
            (
                "At the 2024 AI in Enterprise conference in Chicago, Sarah Chen "
                "(Acme Corp) and Priya Patel (MediCore) co-presented a session on "
                "\"Practical AI: From Supply Chains to Scans.\" James Miller and "
                "Robert Kim also attended. The conference was sponsored by "
                "VentureCap Partners."
            ),
        ),
    ]

    all_episodes = acme_episodes + medicore_episodes + bridging_episodes

    for name, body in all_episodes:
        ep = await graphiti.add_episode(
            name=name,
            episode_body=body,
            source=EpisodeType.text,
            source_description="Community demo data",
            reference_time=now,
            group_id=group_id,
        )
        print(f"  Added episode: {ep.name}")

    print(f"\n  Total episodes added: {len(all_episodes)}")

    # ---- Build communities -------------------------------------------------
    section("Building communities")

    print(
        "  Community detection groups related entities into clusters based on\n"
        "  graph structure (connections, shared entities, relationship density).\n"
    )

    print("  Running build_communities() ...")
    communities = await graphiti.build_communities()
    print(f"  build_communities() finished.\n")

    # ---- Inspect communities -----------------------------------------------
    section("Inspecting community structure")

    # Graphiti stores communities as Community nodes in Neo4j.
    # Each community has a name, summary, and links to member entities.
    # Let's retrieve them using the graph's search or direct node lookups.

    print("  Searching for communities in the graph:\n")

    # Use a broad query to surface community information
    community_search = await graphiti.search_(
        query="community clusters of companies and people",
        group_ids=[group_id],
        num_results=10,
    )

    print(f"  search_() returned {len(community_search.nodes)} nodes")
    # Filter to likely community nodes by checking names
    community_nodes = [
        n for n in community_search.nodes
        if n.name and ("Community" in n.name or "community" in (n.summary or "").lower())
    ]
    if community_nodes:
        for cn in community_nodes[:5]:
            print(f"    Community node: {cn.name}")
            if cn.summary:
                print(f"      Summary: {cn.summary[:120]}...")
            print()
    else:
        # Communities may not always appear via search; show what we found
        print("  (No explicit community nodes in search results; this is expected")
        print("   if the communities are recent and need vector indices to refresh.)")
        print()
        print("  Names of all returned nodes:")
        for n in community_search.nodes:
            print(f"    - {n.name} ({n.label})")

    # ---- Community-aware search vs flat search -----------------------------
    section("Community-aware vs flat search comparison")

    # Build a config that uses community context
    community_config = SearchConfig(
        recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
        num_results=5,
        # The SearchRecipes that include community retrieval typically use
        # the community structure to expand the search context.
    )

    flat_config = SearchConfig(
        recipe=SearchRecipes.HNSW_KNN,
        num_results=5,
    )

    test_query = "Which companies use AI for their products?"

    print(f'  Query: "{test_query}"\n')

    print("  --- Flat search (HNSW_KNN) ---")
    flat_results = await graphiti.search_(
        query=test_query,
        group_ids=[group_id],
        config=flat_config,
    )
    print(f"  Flat found {len(flat_results.edges)} edges, {len(flat_results.nodes)} nodes:")
    for e in flat_results.edges[:3]:
        print(f"    - {e.fact}")

    print()
    print("  --- Community-aware search (COMBINED_HYBRID_SEARCH_CROSS_ENCODER) ---")
    community_results = await graphiti.search_(
        query=test_query,
        group_ids=[group_id],
        config=community_config,
    )
    print(f"  Community-aware found {len(community_results.edges)} edges, {len(community_results.nodes)} nodes:")
    for e in community_results.edges[:5]:
        print(f"    - {e.fact}")

    print()
    print("  Key insight: Community-aware retrieval tends to surface broader,")
    print("  contextually related facts beyond the exact query match.")

    # ---- How communities improve retrieval ---------------------------------
    section("How communities improve retrieval for broad queries")

    broad_queries = [
        "What funding rounds have happened and who was involved?",
        "Tell me about the leadership teams across companies",
    ]

    for query in broad_queries:
        print(f'  Broad query: "{query}"\n')

        # Flat search
        flat = await graphiti.search(
            query=query,
            group_ids=[group_id],
            num_results=3,
        )
        print(f"  Flat search returned {len(flat)} edges:")
        for e in flat:
            print(f"    - {e.fact}")

        print()

        # Community-aware
        ca_config = SearchConfig(
            recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
            num_results=5,
        )
        ca = await graphiti.search_(
            query=query,
            group_ids=[group_id],
            config=ca_config,
        )
        print(f"  Community-aware returned {len(ca.edges)} edges, {len(ca.nodes)} nodes:")
        for e in ca.edges[:5]:
            print(f"    - {e.fact}")
        print()

    # ---- Community properties summary --------------------------------------
    section("Community properties reference")

    print(
        "  Each Community node in Graphiti has these key properties:\n"
        "    name        -- Auto-generated community name\n"
        "    summary     -- LLM-generated summary of the community\n"
        "    uuid        -- Unique identifier\n"
        "    entity_uuids -- List of entity UUIDs that belong to this community\n"
        "    created_at   -- When the community was detected\n"
        "    group_id     -- The group this community belongs to\n"
        "\n"
        "  Communities are created by:\n"
        "    1. Building a graph from extracted entities and edges\n"
        "    2. Running hierarchical community detection (Leiden algorithm)\n"
        "    3. Generating a summary for each community via the LLM\n"
        "\n"
        "  During search, community context helps by:\n"
        "    - Expanding the query with related entity context\n"
        "    - Surfacing facts from the same community cluster\n"
        "    - Improving recall for broad or ambiguous queries\n"
    )

    # ---- cleanup -----------------------------------------------------------
    section("Cleanup")
    print(f"Deleting group {group_id} ...")
    await graphiti.delete_group(group_id=group_id)
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
