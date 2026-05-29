"""
Example 03: Episode Patterns -- All Four Episode Types

Graphiti supports four episode source types, each processed differently by the
extraction pipeline:

  1. EpisodeType.text
     Free-form natural language. The LLM extracts entities and relationships
     from the narrative. Best for documents, articles, reports.

  2. EpisodeType.message
     A structured message with a speaker/role prefix. Useful for chat logs,
     interview transcripts, or any dialogue where speaker attribution matters.
     Graphiti uses the speaker as an entity.

  3. EpisodeType.json
     Structured JSON data. Graphiti extracts entities and relationships by
     interpreting the JSON schema and values. Ideal for programmatic data
     ingestion (APIs, logs, database exports).

  4. EpisodeType.fact_triple
     Explicit (subject, predicate, object) triples. No LLM extraction needed
     -- the triples are directly added as graph edges. Useful when you already
     have structured knowledge you want to inject verbatim.

This example adds episodes about Acme Corp's supply chain using all four types,
then searches across all of them to show how the graph integrates the results.
"""

import asyncio
import json
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
        if e.valid_at:
            print(f"      valid at: {e.valid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()


# ===================================================================
#  Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 03: Episode Patterns -- All Four Episode Types")
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

    group_id = "episode_patterns_demo"
    now = datetime.now(timezone.utc)

    # ==================================================================
    #  1. EpisodeType.text  -- Natural language narrative
    # ==================================================================
    print("\n" + "=" * 60)
    print("1. EpisodeType.text -- Free-form narrative")
    print("=" * 60)
    print(
        "  The LLM parses the text, extracts named entities (people, companies,\n"
        "  products, locations) and relationships between them.\n"
    )

    ep_text = await graphiti.add_episode(
        name="text_supply_chain",
        episode_body=(
            "Acme Corp operates three major warehouses: the San Francisco Hub, "
            "the Chicago Distribution Center, and the Atlanta Regional Depot. "
            "The SF Hub handles West Coast orders and is managed by David Park. "
            "The Chicago facility manages Midwest logistics and was recently "
            "upgraded with automated sorting systems from AutoSort Inc."
        ),
        source=EpisodeType.text,
        source_description="Supply chain overview document",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added text episode: {ep_text.name} (uuid: {ep_text.uuid})\n")

    # ==================================================================
    #  2. EpisodeType.message -- Speaker-attributed dialogue
    # ==================================================================
    print("=" * 60)
    print("2. EpisodeType.message -- Speaker/role dialogue")
    print("=" * 60)
    print(
        "  Graphiti parses the speaker prefix (e.g., 'Alice: ...') and creates\n"
        "  an EntityNode for each speaker, linking their statements to them.\n"
    )

    ep_message = await graphiti.add_episode(
        name="message_team_sync",
        episode_body=(
            "Alice Zhang: The SF Hub is running at 92% capacity. We need to "
            "redistribute some inventory to Chicago.\n"
            "David Park: I can coordinate the transfer. Chicago has room for "
            "an additional 15,000 pallets.\n"
            "Maria Gonzalez: Let's schedule the transfer for next week. I'll "
            "notify the logistics team.\n"
            "James Miller: Good. Also, AutoSort Inc wants to demo their new "
            "robotic pickers at the Atlanta Depot."
        ),
        source=EpisodeType.message,
        source_description="Team sync chat transcript",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added message episode: {ep_message.name} (uuid: {ep_message.uuid})\n")

    # ==================================================================
    #  3. EpisodeType.json -- Structured JSON data
    # ==================================================================
    print("=" * 60)
    print("3. EpisodeType.json -- Structured JSON data")
    print("=" * 60)
    print(
        "  Graphiti interprets JSON keys/values to extract entities and\n"
        "  relationships. Keys like 'ceo', 'employees', 'location' become\n"
        "  relationship predicates or entity attributes.\n"
    )

    warehouse_data = json.dumps(
        {
            "warehouses": [
                {
                    "name": "San Francisco Hub",
                    "capacity_pallets": 50000,
                    "utilization_pct": 92,
                    "manager": "David Park",
                    "region": "West Coast",
                },
                {
                    "name": "Chicago Distribution Center",
                    "capacity_pallets": 75000,
                    "utilization_pct": 65,
                    "manager": "Lisa Kim",
                    "region": "Midwest",
                },
                {
                    "name": "Atlanta Regional Depot",
                    "capacity_pallets": 60000,
                    "utilization_pct": 78,
                    "manager": "Ray Johnson",
                    "region": "Southeast",
                },
            ]
        },
        indent=2,
    )

    ep_json = await graphiti.add_episode(
        name="json_warehouse_data",
        episode_body=warehouse_data,
        source=EpisodeType.json,
        source_description="Warehouse inventory snapshot from ERP system",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added JSON episode: {ep_json.name} (uuid: {ep_json.uuid})")
    print(f"  Body was:\n{warehouse_data}\n")

    # ==================================================================
    #  4. EpisodeType.fact_triple -- Explicit (S, P, O) triples
    # ==================================================================
    print("=" * 60)
    print("4. EpisodeType.fact_triple -- Explicit subject-predicate-object")
    print("=" * 60)
    print(
        "  Triples bypass the LLM extraction entirely. Each line is parsed as\n"
        "  subject | predicate | object and directly added to the graph.\n"
    )

    triples = """Acme Corp | has_warehouse | San Francisco Hub
Acme Corp | has_warehouse | Chicago Distribution Center
Acme Corp | has_warehouse | Atlanta Regional Depot
Acme Corp | ceo | Dr. Sarah Chen
Dr. Sarah Chen | founded | Acme Corp
David Park | manages | San Francisco Hub
Lisa Kim | manages | Chicago Distribution Center
Ray Johnson | manages | Atlanta Regional Depot
San Francisco Hub | located_in | San Francisco
Chicago Distribution Center | located_in | Chicago
Atlanta Regional Depot | located_in | Atlanta"""

    ep_triple = await graphiti.add_episode(
        name="triple_warehouse_org",
        episode_body=triples,
        source=EpisodeType.fact_triple,
        source_description="Organizational chart as explicit triples",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added fact_triple episode: {ep_triple.name} (uuid: {ep_triple.uuid})")
    print(f"  Body was:\n{triples}\n")

    # ==================================================================
    #  Search across all episode types
    # ==================================================================
    print("=" * 60)
    print("Search results (integrated across all 4 episode types)")
    print("=" * 60)

    queries = [
        "Who manages the San Francisco Hub?",
        "What warehouses does Acme Corp operate?",
        "What is the capacity of the Chicago Distribution Center?",
        "What did Alice Zhang say about the SF Hub?",
    ]

    for query in queries:
        print(f'\n  Query: "{query}"')
        edges = await graphiti.search(
            query=query,
            group_ids=[group_id],
            num_results=5,
        )
        print_edges(edges)

    # ==================================================================
    #  Summary
    # ==================================================================
    print("=" * 60)
    print("Key takeaways")
    print("=" * 60)
    print(
        "  - EpisodeType.text:      Best for unstructured narrative / documents\n"
        "  - EpisodeType.message:   Best for chats, interviews, dialogue\n"
        "  - EpisodeType.json:      Best for structured data (APIs, logs)\n"
        "  - EpisodeType.fact_triple: Best when you already have extracted\n"
        "                           relations and want lossless injection\n"
        "  - All types coexist in the same graph and can be searched together.\n"
    )

    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
