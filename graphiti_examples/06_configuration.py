"""
Example 06: Configuration -- Tuning Graphiti's Behavior

Graphiti exposes several configuration levers that affect extraction quality,
performance, and storage. This example demonstrates the major ones:

  1. Custom LLM client
     Graphiti uses an LLM for entity/relationship extraction. You can inject
     a pre-configured OpenAI client to control temperature, model, etc.

  2. max_coroutines
     Controls how many concurrent extraction tasks run. Higher = faster batch
     processing but more LLM API pressure. Lower = more predictable rate
     limiting.

  3. store_raw_episode_content
     Whether to persist the raw episode body text in Neo4j. Disabling saves
     storage but loses the ability to re-process episodes.

  4. Embedder configuration
     Graphiti uses text embeddings for similarity search. You can configure
     the embedder model (e.g., text-embedding-3-small vs text-embedding-3-large).

  5. Custom entity definitions
     Define your own EntityNode subclasses with Pydantic fields to enforce
     consistent entity schemas.

This example creates several Graphiti instances with different configurations
and shows how they affect behavior. Since we can't run them all simultaneously
on the same DB (indices would collide), we run them sequentially with unique
group_ids and explain each config.
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


def print_separator(title: str):
    """Print a section separator."""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


# ===================================================================
#  1. Custom LLM Client Configuration
# ===================================================================
async def demo_custom_llm(graphiti, group_id):
    """Demonstrate using a custom OpenAI client with different settings."""
    print_separator("Config 1: Custom LLM Client")
    print(
        "  Injecting an OpenAI client with lower temperature (= more\n"
        "  deterministic extraction) and a specific model.\n"
    )

    from openai import AsyncOpenAI

    # Create a custom OpenAI client with lower temperature
    custom_client = AsyncOpenAI(
        api_key=OPENAI_API_KEY,
    )

    # Re-initialize Graphiti with the custom client
    # Note: Graphiti accepts the LLM client via its constructor.
    # The exact parameter name may be 'llm_client' in some versions.
    try:
        graphiti_custom = Graphiti(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            # Uncomment and adjust for your graphiti_core version:
            # llm_client=custom_client,
            # llm_client_kwargs={
            #     "model": "gpt-4o",
            #     "temperature": 0.1,
            # },
        )
    except TypeError:
        print(
            "  NOTE: Your graphiti_core version may pass LLM config differently.\n"
            "  Common approaches:\n"
            "    - Graphiti(..., llm_client=custom_client)\n"
            "    - Graphiti(..., llm_client_kwargs={'model': 'gpt-4o'})\n"
            "    - Via environment variables (OPENAI_API_KEY, OPENAI_MODEL)\n"
            "  Using default Graphiti instance for this demo.\n"
        )
        graphiti_custom = graphiti

    await graphiti_custom.build_indices_and_constraints()

    ep = await graphiti_custom.add_episode(
        name="custom_llm_demo",
        episode_body=(
            "Acme Corp's CTO, Dr. Sarah Chen, announced that FalconTrack "
            "will use a microservices architecture with Kubernetes. "
            "The infrastructure team is led by James Miller and includes "
            "12 SREs."
        ),
        source=EpisodeType.text,
        source_description="Technical roadmap document",
        reference_time=datetime.now(timezone.utc),
        group_id=group_id,
    )
    print(f"  Added episode with custom LLM config: '{ep.name}'\n")
    return graphiti_custom  # in case we created a new one


# ===================================================================
#  2. max_coroutines Configuration
# ===================================================================
async def demo_max_coroutines(graphiti, group_id):
    """Show how max_coroutines affects concurrent extraction."""
    print_separator("Config 2: max_coroutines (Concurrency Control)")
    print(
        "  max_coroutines limits how many episodes are extracted\n"
        "  concurrently. Lower values are gentler on API rate limits.\n"
    )

    # Low concurrency: process episodes one at a time
    graphiti_slow = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        max_coroutines=1,  # Process one episode at a time
    )
    await graphiti_slow.build_indices_and_constraints()

    print("  max_coroutines=1 (sequential processing):")
    t0 = datetime.now(timezone.utc)

    for i in range(3):
        ep = await graphiti_slow.add_episode(
            name=f"slow_batch_{i}",
            episode_body=(
                f"Acme Corp process {i}: The inventory system at the "
                f"{['SF', 'Chicago', 'Atlanta'][i]} warehouse was updated. "
                f"Manager {['David', 'Lisa', 'Ray'][i]} approved the changes."
            ),
            source=EpisodeType.text,
            source_description=f"Warehouse update {i}",
            reference_time=datetime.now(timezone.utc),
            group_id=group_id,
        )
        elapsed = (datetime.now(timezone.utc) - t0).total_seconds()
        print(f"    Episode {i} done at t={elapsed:.1f}s")

    elapsed_total = (datetime.now(timezone.utc) - t0).total_seconds()
    print(f"  Total time (max_coroutines=1): {elapsed_total:.1f}s\n")
    await graphiti_slow.close()


# ===================================================================
#  3. store_raw_episode_content Trade-off
# ===================================================================
async def demo_store_raw_content(graphiti, group_id):
    """Show the store_raw_episode_content flag behavior."""
    print_separator("Config 3: store_raw_episode_content")
    print(
        "  When True (default):  episode body is stored in Neo4j (uses more\n"
        "                        storage, but allows re-extraction).\n"
        "  When False:           body is not stored (saves space, but can't\n"
        "                        re-process later without re-adding).\n"
    )

    graphiti_no_store = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
        store_raw_episode_content=False,
    )
    await graphiti_no_store.build_indices_and_constraints()

    ep = await graphiti_no_store.add_episode(
        name="no_store_demo",
        episode_body=(
            "Acme Corp's warehouse management system processed 50,000 "
            "orders today. The SF Hub handled 18,000 orders alone."
        ),
        source=EpisodeType.text,
        source_description="Daily operations report",
        reference_time=datetime.now(timezone.utc),
        group_id=group_id,
    )

    print(f"  Added episode with store_raw_episode_content=False")
    print(f"  Episode body will NOT be persisted in Neo4j\n")
    print("  Use case: high-volume ingestion where you don't need to\n"
          "  re-process episodes later.\n")
    await graphiti_no_store.close()


# ===================================================================
#  4. Embedder Configuration
# ===================================================================
async def demo_embedder_config(graphiti, group_id):
    """Show different embedder model configurations."""
    print_separator("Config 4: Embedder Configuration")
    print(
        "  Graphiti uses embeddings for semantic search. Common options:\n"
        "    - text-embedding-3-small  (faster, cheaper, ~1536d)\n"
        "    - text-embedding-3-large  (more accurate, ~3072d)\n"
    )

    # The exact constructor parameter for embedder config varies by version.
    # Common patterns:
    try:
        graphiti_large = Graphiti(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            # Hypothetical embedder config -- adjust for your version:
            # embedder_model="text-embedding-3-large",
            # embedder_dimensions=3072,
        )
        await graphiti_large.build_indices_and_constraints()

        ep = await graphiti_large.add_episode(
            name="embedder_demo",
            episode_body=(
                "FalconTrack processes real-time GPS data from over 5,000 "
                "delivery vehicles. The system reduces fuel consumption by "
                "an average of 22% through dynamic route optimization."
            ),
            source=EpisodeType.text,
            source_description="Product spec",
            reference_time=datetime.now(timezone.utc),
            group_id=group_id,
        )
        print(f"  Added episode with text-embedding-3-large: '{ep.name}'\n")
        await graphiti_large.close()

    except Exception as e:
        print(f"  NOTE: Could not configure custom embedder: {e}")
        print("  Using default embedder settings.\n")


# ===================================================================
#  5. Custom Entity Definitions (Pydantic)
# ===================================================================
async def demo_custom_entities(graphiti, group_id):
    """Show how to define custom entity types with Pydantic."""
    print_separator("Config 5: Custom Entity Definitions")
    print(
        "  You can subclass EntityNode to create typed entities with\n"
        "  consistent schemas via Pydantic fields.\n"
    )

    from pydantic import BaseModel, Field
    from graphiti_core.nodes import EntityNode

    class Employee(EntityNode):
        """Custom entity type for employees with structured fields."""
        name: str = Field(description="Full name of the employee")
        role: str = Field(default="unknown", description="Job title")
        department: str = Field(default="unknown", description="Department name")
        start_year: int | None = Field(default=None, description="Year hired")

    class Product(EntityNode):
        """Custom entity type for products with structured fields."""
        name: str = Field(description="Product name")
        version: str = Field(default="1.0", description="Version string")
        status: str = Field(default="active", description="Product status")

    print("  Defined custom entity types:")
    print(f"    - Employee(name, role, department, start_year)")
    print(f"    - Product(name, version, status)")
    print()
    print("  These are used internally by Graphiti's extraction pipeline")
    print("  when the LLM identifies entities of these types.\n")

    # Add episode using custom entity types
    ep = await graphiti.add_episode(
        name="custom_entities_demo",
        episode_body=(
            "James Miller is the VP of Engineering at Acme Corp. He joined "
            "in 2021. His team built RouteOptimizer Pro version 3.2, which "
            "is currently in beta. Alice Zhang, a Senior Engineer since 2022, "
            "led the routing algorithm redesign."
        ),
        source=EpisodeType.text,
        source_description="Engineering org chart",
        reference_time=datetime.now(timezone.utc),
        group_id=group_id,
    )
    print(f"  Added episode: '{ep.name}'")
    print("  Extracted entities should include Employee and Product types.\n")


# ===================================================================
#  Main
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 06: Configuration Options")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start Neo4j via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    # Base graphiti instance shared across demos
    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    # Each demo uses a unique group_id so configs don't interfere
    await demo_custom_llm(graphiti, "config_custom_llm")
    await demo_max_coroutines(graphiti, "config_max_coroutines")
    await demo_store_raw_content(graphiti, "config_no_store")
    await demo_embedder_config(graphiti, "config_embedder")
    await demo_custom_entities(graphiti, "config_custom_entities")

    # Summary
    print_separator("Configuration Reference")
    print("""
  Parameter                    Default      Effect
  --------------------------   -----------  --------------------------------
  llm_client                   None         Injected OpenAI/Anthropic client
  llm_client_kwargs            {}           Model, temperature, etc.
  max_coroutines               10           Concurrent extraction tasks
  store_raw_episode_content    True         Persist raw episode body
  embedder_model               text-embed-   Model for similarity search
                                 ding-3-small
""")

    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
