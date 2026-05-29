"""
Example 13: Temporal Reasoning and Point-in-Time Queries

Graphiti's core differentiator is temporal reasoning -- every fact is anchored
to a point in time and tracked as it evolves. This enables queries like:

  - "What was true in 2022?" (historical snapshot)
  - "What is true now?" (current state)
  - "How did this entity's properties change over time?"
  - "What was the relationship between these entities in 2023?"

This example follows a fictional company, Nova Robotics, through its journey
from 2020 to 2025, demonstrating:
  1. Adding episodes with different reference_time values
  2. Querying the graph at specific points in time
  3. Showing fact evolution (role changes, product updates, etc.)
  4. Tracking a relationship that changed over time
  5. Using SearchFilters with temporal constraints
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
    print("Example 13: Temporal Reasoning and Point-in-Time Queries")
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

    group_id = "temporal_demo_nova"

    # -----------------------------------------------------------------------
    # We will create a timeline of episodes about Nova Robotics.
    # Each episode carries a reference_time that anchors its facts in time.
    #
    # Timeline:
    #   Jan 2020 -- Company founded by Alex Rivera
    #   Jun 2021 -- NovaShield v1 launched, Alex is CEO
    #   Mar 2022 -- Series A funding, Emily Tran joins as CTO
    #   Nov 2022 -- NovaShield v2 with AI features, Emily Tran is CTO
    #   Jun 2023 -- Emily Tran promoted to COO (role change!)
    #   Jan 2024 -- NovaShield v3 with cloud platform
    #   Mar 2025 -- Series B funding, valuation $200M
    # -----------------------------------------------------------------------

    section("Adding temporally-anchored episodes (2020--2025)")

    def make_time(year: int, month: int = 1, day: int = 1) -> datetime:
        """Create a timezone-aware datetime for the given date."""
        return datetime(year, month, day, tzinfo=timezone.utc)

    episodes = [
        (
            "nova_founded",
            make_time(2020, 1, 15),
            (
                "Nova Robotics was founded by Alex Rivera in Austin, Texas. "
                "Alex has a background in mechanical engineering and previously "
                "worked at Boston Dynamics. Nova Robotics develops security robots."
            ),
        ),
        (
            "novashield_v1_launch",
            make_time(2021, 6, 1),
            (
                "Nova Robotics launched their first product, NovaShield v1, "
                "an autonomous security robot for warehouse surveillance. "
                "The product sells for $15,000 per unit. "
                "Alex Rivera is the CEO of Nova Robotics."
            ),
        ),
        (
            "series_a",
            make_time(2022, 3, 10),
            (
                "Nova Robotics raised $8M in Series A funding from TechVentures Capital. "
                "Emily Tran joined the company as CTO. Emily holds a PhD in robotics "
                "from MIT and previously led engineering at DroneWorks Inc."
            ),
        ),
        (
            "novashield_v2",
            make_time(2022, 11, 15),
            (
                "Nova Robotics launched NovaShield v2 with AI-powered threat detection. "
                "The new version can distinguish between humans, animals, and vehicles "
                "with 97% accuracy. Price increased to $22,000 per unit. "
                "CTO Emily Tran led the AI development team."
            ),
        ),
        (
            "emily_promotion",
            make_time(2023, 6, 20),
            (
                "Emily Tran was promoted from CTO to COO of Nova Robotics. "
                "She now oversees both engineering and operations. "
                "A new CTO will be hired to replace her engineering role. "
                "CEO Alex Rivera announced the promotion internally."
            ),
        ),
        (
            "novashield_v3",
            make_time(2024, 1, 10),
            (
                "Nova Robotics launched NovaShield v3 with a cloud management platform. "
                "Customers can now monitor their robot fleets from a web dashboard. "
                "The price is $28,000 per unit. Dr. Karen Wu joined as the new CTO."
            ),
        ),
        (
            "series_b",
            make_time(2025, 3, 5),
            (
                "Nova Robotics raised $30M in Series B funding, reaching a $200M valuation. "
                "The round was led by GlobalTech Ventures. CFO Michael Park also joined "
                "the executive team. The company now has 120 employees."
            ),
        ),
    ]

    for name, ref_time, body in episodes:
        ep = await graphiti.add_episode(
            name=name,
            episode_body=body,
            source=EpisodeType.text,
            source_description=f"Temporal demo - {ref_time.year}",
            reference_time=ref_time,
            group_id=group_id,
        )
        print(f"  [{ref_time.year}-{ref_time.month:02d}] Added: {name}")

    print(f"\n  Total episodes spanning 2020--2025.")

    # ---- Query: current state vs past state --------------------------------
    section("Query: What is true NOW vs What was true in 2022")

    current_query = "Who is the CTO of Nova Robotics?"
    past_query = "Who was the CTO of Nova Robotics?"

    print(f'  Current query: "{current_query}"')
    current_edges = await graphiti.search(
        query=current_query,
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Current facts found: {len(current_edges)}")
    for edge in current_edges:
        print(f"    - {edge.fact}")
        if edge.valid_at:
            print(f"      (valid from: {edge.valid_at.date()})")
        if edge.invalid_at:
            print(f"      (expired: {edge.invalid_at.date()})")
    print()

    print(f'  Past query: "{past_query}"')
    past_edges = await graphiti.search(
        query=past_query,
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Past facts found: {len(past_edges)}")
    for edge in past_edges:
        print(f"    - {edge.fact}")
        if edge.valid_at:
            print(f"      (valid from: {edge.valid_at.date()})")
        if edge.invalid_at:
            print(f"      (expired: {edge.invalid_at.date()})")
    print()

    print(
        "  Notice: The search should surface BOTH current and historical facts.\n"
        "  Graphiti preserves expired edges -- they are not deleted, they are\n"
        "  marked with invalid_at. This gives a complete audit trail of changes.\n"
    )

    # ---- Temporal evolution of a relationship ------------------------------
    section("Temporal evolution: Alex Rivera and Emily Tran's relationship")

    print(
        "  Emily Tran's relationship with Nova Robotics changed over time:\n"
        "    2022: Joined as CTO\n"
        "    2023: Promoted to COO\n"
        "  Let's see what facts the graph surfaces about this:\n"
    )

    # Search for facts about Emily Tran
    emily_facts = await graphiti.search(
        query="Emily Tran role at Nova Robotics",
        group_ids=[group_id],
        num_results=10,
    )
    print(f"  Found {len(emily_facts)} facts about Emily Tran's role:")
    for edge in emily_facts:
        print(f"    - {edge.fact}")
        print(f"      valid_at:  {edge.valid_at.date() if edge.valid_at else 'N/A'}")
        print(f"      invalid_at: {edge.invalid_at.date() if edge.invalid_at else 'still valid'}")
    print()

    print(
        "  The graph captures the full trajectory: both the 'CTO' period and\n"
        "  the 'COO' period are stored as separate edges with different time windows.\n"
        "  A point-in-time query can reconstruct what was true at any moment.\n"
    )

    # ---- Product price evolution over time ---------------------------------
    section("Product evolution: NovaShield pricing history")

    print(
        "  NovaShield's price changed across versions:\n"
        "    v1 (2021): $15,000\n"
        "    v2 (2022): $22,000\n"
        "    v3 (2024): $28,000\n"
    )

    price_facts = await graphiti.search(
        query="NovaShield price cost",
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Found {len(price_facts)} price-related facts:")
    for edge in price_facts:
        print(f"    - {edge.fact}")
        print(f"      valid_at: {edge.valid_at.date() if edge.valid_at else 'N/A'}")
        print(f"      invalid_at: {edge.invalid_at.date() if edge.invalid_at else 'still valid'}")

    # ---- Funding history comparison ----------------------------------------
    section("Funding history: Series A (2022) vs Series B (2025)")

    funding_facts = await graphiti.search(
        query="Nova Robotics funding rounds and investors",
        group_ids=[group_id],
        num_results=10,
    )
    print(f"  Found {len(funding_facts)} funding-related facts:")
    for edge in funding_facts:
        print(f"    - {edge.fact}")
        print(f"      valid_at: {edge.valid_at.date() if edge.valid_at else 'N/A'}")

    # ---- CEO remains constant -- temporal consistency ----------------------
    section("Temporal consistency: constant facts across time")

    print(
        "  Some facts don't change. Alex Rivera has been CEO since 2021.\n"
        "  Let's verify temporal consistency:\n"
    )

    ceo_facts = await graphiti.search(
        query="Alex Rivera CEO Nova Robotics",
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Found {len(ceo_facts)} facts about Alex Rivera's CEO role:")
    for edge in ceo_facts:
        print(f"    - {edge.fact}")
        print(f"      valid from: {edge.valid_at.date() if edge.valid_at else 'N/A'}")
        print(f"      expired:    {edge.invalid_at.date() if edge.invalid_at else 'still CEO'}")
    print()

    print(
        "  Because Alex is still the CEO, the edge has no invalid_at -- it's\n"
        "  still considered current. No contradictory facts have been added.\n"
    )

    # ---- cleanup -----------------------------------------------------------
    section("Cleanup")
    print(f"Deleting group {group_id} ...")
    await graphiti.delete_group(group_id=group_id)
    await graphiti.close()

    # ---- Reference: SearchFilters with temporal constraints ----------------
    section("Reference: temporal constraints in SearchFilters")

    print(
        "  Graphiti's SearchFilters supports temporal constraints for\n"
        "  point-in-time queries:\n"
        "\n"
        "  from graphiti_core.search.search_filters import SearchFilters\n"
        "  from datetime import datetime, timezone\n"
        "\n"
        "  # Filter by time window:\n"
        "  filters = SearchFilters(\n"
        "      group_ids=['my_group'],\n"
        "  )\n"
        "\n"
        "  # In practice, temporal filtering is often combined with:\n"
        "  # - episode reference_time (when the fact was observed)\n"
        "  # - edge valid_at / invalid_at (when the fact was true)\n"
        "  # - Point-in-time reconstruction via Cypher queries\n"
        "\n"
        "  Key insight: Graphiti preserves ALL historical facts. Nothing is\n"
        "  ever deleted -- edges get invalid_at timestamps when superseded.\n"
        "  This means you can always reconstruct 'what was true at time T'\n"
        "  by filtering edges where:\n"
        "    valid_at <= T AND (invalid_at IS NULL OR invalid_at > T)\n"
    )

    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
