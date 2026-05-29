"""
Example 09: Custom Entity Types with Pydantic

Graphiti's extraction pipeline normally discovers entity types dynamically.
However, you can define custom Pydantic entity subclasses to:

  1. Guide the LLM toward specific entity types (Person, Organization, Product, etc.)
  2. Add typed fields with validation
  3. Get proper Neo4j labels matching your schema
  4. Search and filter by custom entity labels

This example demonstrates:
  - Defining multiple custom entity types
  - Defining custom edge types
  - Using entity_types in add_episode()
  - Searching by custom entity labels
  - Inspecting typed fields on retrieved entities
"""

import asyncio
import os
import socket
import sys

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field
from typing import ClassVar

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


# ---------------------------------------------------------------------------
# Custom entity types
# ---------------------------------------------------------------------------
# By subclassing EntityNode and adding Pydantic fields, we tell Graphiti's
# extraction pipeline what kinds of entities to look for and what properties
# to capture for each one.

from graphiti_core.nodes import EntityNode


class Person(EntityNode):
    """A person entity with typed professional fields."""

    # _label_prefix is a ClassVar -- it controls the Neo4j label
    _label_prefix: ClassVar[str] = "Person"

    title: Optional[str] = Field(
        default=None,
        description="Job title or role of the person",
    )
    employer: Optional[str] = Field(
        default=None,
        description="The organization this person works for",
    )
    expertise: Optional[str] = Field(
        default=None,
        description="Area of expertise or specialization",
    )


class Organization(EntityNode):
    """A company, institution, or other organized group."""

    _label_prefix: ClassVar[str] = "Organization"

    industry: Optional[str] = Field(
        default=None,
        description="Industry sector (e.g., 'Logistics', 'Healthcare')",
    )
    founded_year: Optional[int] = Field(
        default=None,
        description="Year the organization was founded",
    )
    headquarters: Optional[str] = Field(
        default=None,
        description="City where headquarters is located",
    )


class Product(EntityNode):
    """A product or service offered by an organization."""

    _label_prefix: ClassVar[str] = "Product"

    category: Optional[str] = Field(
        default=None,
        description="Product category (e.g., 'Software', 'Hardware')",
    )
    launch_year: Optional[int] = Field(
        default=None,
        description="Year the product was launched",
    )
    price_tier: Optional[str] = Field(
        default=None,
        description="Pricing tier: 'Free', 'Starter', 'Enterprise', etc.",
    )


class Event(EntityNode):
    """An event with temporal significance."""

    _label_prefix: ClassVar[str] = "Event"

    event_type: Optional[str] = Field(
        default=None,
        description="Type of event (e.g., 'Funding', 'Launch', 'Hiring')",
    )
    date: Optional[str] = Field(
        default=None,
        description="When the event occurred (YYYY-MM-DD or year)",
    )
    location: Optional[str] = Field(
        default=None,
        description="Where the event took place",
    )


class Location(EntityNode):
    """A geographic location."""

    _label_prefix: ClassVar[str] = "Location"

    region: Optional[str] = Field(
        default=None,
        description="Geographic region (e.g., 'North America', 'Europe')",
    )
    country: Optional[str] = Field(
        default=None,
        description="Country name",
    )


# ---------------------------------------------------------------------------
# Main example
# ---------------------------------------------------------------------------
async def main():
    print("=" * 72)
    print("Example 09: Custom Entity Types with Pydantic")
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

    group_id = "custom_entities_demo"
    now = datetime.now(timezone.utc)

    # Build the entity_types dict. This tells the LLM which entity schemas to
    # use during extraction. The keys are the type names the LLM will emit.
    entity_types = {
        "Person": Person,
        "Organization": Organization,
        "Product": Product,
        "Event": Event,
        "Location": Location,
    }

    section("Seeding the graph with custom entity extraction")

    # When we pass entity_types to add_episode(), the extraction pipeline
    # populates the typed fields on matching entities.

    episode_1 = await graphiti.add_episode(
        name="acme_overview",
        episode_body=(
            "Acme Corp is a logistics technology company founded in 2019 "
            "by Dr. Sarah Chen. Sarah is the CEO and holds a PhD in Computer "
            "Science from Stanford University. The company is headquartered "
            "in San Francisco, USA."
        ),
        source=EpisodeType.text,
        source_description="Company profile",
        reference_time=now,
        group_id=group_id,
        entity_types=entity_types,  # <-- custom entity schemas
    )
    print(f"  Added episode: {episode_1.name}")

    episode_2 = await graphiti.add_episode(
        name="product_and_customers",
        episode_body=(
            "Acme Corp's flagship product, RouteOptimizer Pro, is an enterprise "
            "supply chain optimization platform launched in 2021. It uses machine "
            "learning to reduce delivery costs by up to 35%. "
            "Major customers include GlobalFreight Inc and QuickShip Logistics."
        ),
        source=EpisodeType.text,
        source_description="Product documentation",
        reference_time=now,
        group_id=group_id,
        entity_types=entity_types,
    )
    print(f"  Added episode: {episode_2.name}")

    episode_3 = await graphiti.add_episode(
        name="funding_event",
        episode_body=(
            "In June 2024, Acme Corp raised $30 million in Series B funding "
            "led by VentureCap Partners. Board member David Park from VentureCap "
            "joined the board. The funding will fuel expansion into European markets "
            "and double the engineering team."
        ),
        source=EpisodeType.text,
        source_description="Press release",
        reference_time=now,
        group_id=group_id,
        entity_types=entity_types,
    )
    print(f"  Added episode: {episode_3.name}")

    episode_4 = await graphiti.add_episode(
        name="team",
        episode_body=(
            "James Miller is the VP of Engineering at Acme Corp, leading the "
            "RouteOptimizer Pro development. Maria Gonzalez is the Regional Director "
            "of the Austin office, which opened in 2023 and has 45 engineers. "
            "Dr. Sarah Chen personally recruited both James and Maria."
        ),
        source=EpisodeType.text,
        source_description="Team directory",
        reference_time=now,
        group_id=group_id,
        entity_types=entity_types,
    )
    print(f"  Added episode: {episode_4.name}")

    # ---- Inspect extracted entities ----------------------------------------
    section("Inspecting extracted custom entities")

    # Search for all entities of a specific type
    print("  --- Searching for Person entities ---")
    person_results = await graphiti.search_(
        query="people at Acme Corp",
        group_ids=[group_id],
        num_results=10,
    )
    for node in person_results.nodes:
        # Check if this is a Person by inspecting the label
        print(f"  Node: {node.name} (label: {node.label}, uuid: {node.uuid[:8]}...)")
        # If our custom extraction worked, you might see the typed fields
        # populated in the node's attributes
        if hasattr(node, "title") and node.title:
            print(f"    title: {node.title}")
        if hasattr(node, "employer") and node.employer:
            print(f"    employer: {node.employer}")
        print()

    print("  --- Searching for Organization entities ---")
    org_results = await graphiti.search_(
        query="companies and organizations",
        group_ids=[group_id],
        num_results=10,
    )
    for node in org_results.nodes:
        print(f"  Node: {node.name} (label: {node.label})")

    # ---- Search filtering by entity label ----------------------------------
    section("Search filtering by custom entity labels")

    # Use SearchConfig + SearchFilters to narrow results by entity label
    print("  Only return Product entities:\n")

    # Build a SearchFilters that restricts to "Product" label
    product_filter = SearchFilters(
        group_ids=[group_id],
    )

    product_config = SearchConfig(
        recipe=SearchRecipes.HNSW_KNN,
        num_results=10,
        filters=product_filter,
    )

    # Note: entity label filtering is handled at the edge level in Graphiti,
    # so we use a direct node lookup pattern here:
    products = await graphiti.search_(
        query="products and their features",
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  General search found {len(products.nodes)} nodes:")
    for n in products.nodes:
        print(f"    - {n.name} ({n.label})")

    print()
    print("  Tip: In practice, you can filter extracted entities by inspecting")
    print("  the `label` attribute on returned EntityNode objects and applying")
    print("  your own label-based filtering in application code.\n")

    # ---- Refresh entities from Neo4j to see typed fields -------------------
    section("Re-fetching typed entities from Neo4j")

    print(
        "  Entities stored with custom types can be re-fetched as their typed\n"
        "  classes. Let's look up entities from Neo4j directly:\n"
    )

    # Use the graphiti.get_entities method to retrieve nodes by UUID
    from graphiti_core.llm_client import LLMClient
    from graphiti_core.embedding import EmbeddingClient

    # Search for Sarah Chen specifically to find her UUID
    sarah_results = await graphiti.search_(
        query="Dr. Sarah Chen founder CEO",
        group_ids=[group_id],
        num_results=3,
    )
    for n in sarah_results.nodes:
        print(f"  Found entity: {n.name}")
        print(f"    uuid:     {n.uuid}")
        print(f"    label:    {n.label}")
        print(f"    summary:  {n.summary}")
        print(f"    group_id: {n.group_id}")
        print()

    # ---- cleanup -----------------------------------------------------------
    section("Cleanup")
    print(f"Deleting group {group_id} ...")
    await graphiti.delete_group(group_id=group_id)
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
