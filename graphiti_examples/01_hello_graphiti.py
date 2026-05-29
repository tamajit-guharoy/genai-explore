"""
Example 01: Hello Graphiti -- Your First Temporal Knowledge Graph

This is the minimal working example to get started with Graphiti.
It demonstrates the core workflow:
  1. Connect to Neo4j and initialize the graph database
  2. Add several "episodes" (text chunks containing facts)
  3. Let Graphiti's extraction pipeline identify entities and relationships
  4. Search the graph for specific facts
  5. Inspect the resulting edges (relationships) with temporal metadata

The example uses a fictional company, Acme Corp, to keep the data relatable.
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
# Main example
# ---------------------------------------------------------------------------
async def main():
    print("=" * 72)
    print("Example 01: Hello Graphiti")
    print("=" * 72)

    # ---- connectivity -----------------------------------------------------
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

    print(f"\nConnecting to Neo4j at {NEO4J_URI} ...")
    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )

    # Initialise database schema (indices & constraints).
    # Run this once when setting up a new database.
    print("Building indices and constraints ...")
    await graphiti.build_indices_and_constraints()

    # ---- add episodes -----------------------------------------------------
    # Each call to add_episode() ingests a piece of text, runs the extraction
    # pipeline (LLM -> entities + relationships), and stores the result as a
    # directed, temporal property graph in Neo4j.
    #
    # Episodes with the same group_id are considered part of the same
    # conversation / context window for extraction purposes.

    group_id = "acme_corp_overview"
    now = datetime.now(timezone.utc)

    print("\n--- Adding episodes about Acme Corp ---\n")

    episode_1 = await graphiti.add_episode(
        name="acme_founding",
        episode_body=(
            "Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco. "
            "Sarah started the company to revolutionize supply chain logistics "
            "using AI-powered predictive routing."
        ),
        source=EpisodeType.text,
        source_description="Company history document",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added episode 1:  name={episode_1.name}, uuid={episode_1.uuid}")

    episode_2 = await graphiti.add_episode(
        name="acme_product_launch",
        episode_body=(
            "Acme Corp's flagship product, RouteOptimizer Pro, was launched in "
            "2021. It uses machine learning to reduce delivery costs by up to 35%. "
            "The VP of Engineering, James Miller, led the development team."
        ),
        source=EpisodeType.text,
        source_description="Product documentation",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added episode 2:  name={episode_2.name}, uuid={episode_2.uuid}")

    episode_3 = await graphiti.add_episode(
        name="acme_office_expansion",
        episode_body=(
            "In 2023, Acme Corp opened a new office in Austin, Texas to support "
            "its growing US operations. The Austin office is led by regional "
            "director Maria Gonzalez, who previously ran operations out of Denver."
        ),
        source=EpisodeType.text,
        source_description="Company news announcement",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added episode 3:  name={episode_3.name}, uuid={episode_3.uuid}")

    episode_4 = await graphiti.add_episode(
        name="acme_customers",
        episode_body=(
            "Acme Corp's customers include GlobalFreight Inc and QuickShip Logistics. "
            "GlobalFreight uses RouteOptimizer Pro for their entire US fleet. "
            "QuickShip began a pilot program in Q2 2024. Dr. Sarah Chen personally "
            "presented the roadmap to both clients."
        ),
        source=EpisodeType.text,
        source_description="Customer success report",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Added episode 4:  name={episode_4.name}, uuid={episode_4.uuid}")

    # ---- search the graph -------------------------------------------------
    print("\n--- Searching the knowledge graph ---\n")

    queries = [
        "Who founded Acme Corp and where?",
        "What products does Acme Corp offer?",
        "Which companies use Acme Corp's technology?",
    ]

    for query in queries:
        print(f'  Query: "{query}"')
        edges = await graphiti.search(
            query=query,
            group_ids=[group_id],
            num_results=5,
        )
        print(f"  Found {len(edges)} edge(s):")
        for edge in edges:
            print(f"    - {edge.fact}")
            if edge.valid_at:
                print(f"      valid from: {edge.valid_at.isoformat()}")
            if edge.invalid_at:
                print(f"      invalid at: {edge.invalid_at.isoformat()}")
        print()

    # ---- cleanup ----------------------------------------------------------
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
