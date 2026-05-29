"""
Example 15: Multi-Provider Plugin Architecture

Graphiti supports multiple LLM providers for entity and relationship extraction,
as well as configurable embedders and rerankers. This example demonstrates how
to configure Graphiti with:

  - **OpenAI** (default) -- gpt-4o for extraction, text-embedding-3-small for embeddings
  - **Anthropic Claude** -- claude-sonnet-4-20250514 for extraction
  - **Ollama** (local) -- any local model via OpenAI-compatible endpoint
  - **Azure OpenAI** -- enterprise OpenAI through Azure's gateway
  - **Custom embedders** -- override the default embedding model
  - **Custom rerankers** -- improve search relevance with cross-encoders

This lets you choose providers based on cost, latency, privacy requirements,
or geographic availability.
"""

import asyncio
import os
import socket
import sys

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Environment variables
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
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
# Provider Selection Guide (in-code documentation)
# ---------------------------------------------------------------------------
PROVIDER_GUIDE = """
=== PROVIDER SELECTION GUIDE ===

OpenAI (default):
  - Best for: General purpose, fastest extraction, best JSON mode
  - Model: gpt-4o (extraction), text-embedding-3-small (embeddings)
  - Pros: Reliable JSON mode, fast, widely available
  - Cons: Requires internet, API costs, data goes to OpenAI servers
  - Set: OPENAI_API_KEY

Anthropic Claude:
  - Best for: Long documents, nuanced extraction, safety-sensitive apps
  - Model: claude-sonnet-4-20250514 (extraction)
  - Pros: Larger context window, strong at following complex instructions
  - Cons: No native JSON mode (uses prompt-based JSON), slightly slower
  - Set: ANTHROPIC_API_KEY

Ollama (local):
  - Best for: Privacy-sensitive, offline, air-gapped environments
  - Model: Any local model (llama3, mistral, qwen2, etc.)
  - Pros: Free, no data leaves your machine, no API key needed
  - Cons: Slower extraction, lower quality with smaller models
  - Requires: Ollama running locally on port 11434

Azure OpenAI:
  - Best for: Enterprise compliance, existing Azure contracts
  - Model: Same as OpenAI but through Azure gateway
  - Pros: Enterprise security, compliance certifications
  - Cons: Requires Azure subscription, regional availability
  - Set: AZURE_OPENAI_KEY, AZURE_OPENAI_ENDPOINT

Embedders (configurable via embedder param):
  - openai: text-embedding-3-small (default, 1536d)
  - openai_large: text-embedding-3-large (3072d, better quality)
  - azure_openai: Azure-hosted embeddings
  - Options extendable with custom implementations

Rerankers (configurable via reranker param):
  - None: Default, no reranking (fastest, lowest quality)
  - cross_encoder: Uses a cross-encoder model to rerank search results
    - Improves relevance but adds latency
    - Good for: Production search where quality matters
"""


# ===================================================================
# Factory: build a Graphiti instance for any provider
# ===================================================================
def build_graphiti(
    provider: str = "openai",
    embedder: str = "openai",
    reranker: str | None = None,
):
    """
    Create and return a Graphiti instance configured for the given provider.

    Parameters
    ----------
    provider : str
        One of "openai", "anthropic", "ollama", "azure_openai".
    embedder : str
        Embedding model identifier passed to Graphiti.
    reranker : str or None
        Reranker identifier or None to skip reranking.

    Returns
    -------
    tuple of (Graphiti, str) -- the instance and a human-readable label.
    """
    from graphiti_core import Graphiti

    label = f"{provider} (embedder={embedder}, reranker={reranker})"

    if provider == "openai":
        # -- OpenAI (default) ------------------------------------------------
        # When no llm_client is passed, Graphiti uses OpenAI by default.
        from openai import AsyncOpenAI

        llm_client = AsyncOpenAI(api_key=OPENAI_API_KEY)
        graphiti = Graphiti(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            llm_client=llm_client,
        )
        return graphiti, label

    elif provider == "anthropic":
        # -- Anthropic Claude ------------------------------------------------
        # Pass the Anthropic client directly. Graphiti will use it for
        # entity/relationship extraction.
        from anthropic import AsyncAnthropic

        llm_client = AsyncAnthropic(api_key=ANTHROPIC_API_KEY)
        graphiti = Graphiti(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            llm_client=llm_client,
        )
        return graphiti, label

    elif provider == "ollama":
        # -- Ollama (via OpenAI-compatible endpoint) -------------------------
        # Ollama exposes an OpenAI-compatible API when you set the base_url.
        # The api_key can be any placeholder -- Ollama doesn't check it.
        from openai import AsyncOpenAI

        llm_client = AsyncOpenAI(
            api_key="ollama",  # placeholder, Ollama ignores it
            base_url="http://localhost:11434/v1",
        )
        graphiti = Graphiti(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            llm_client=llm_client,
        )
        return graphiti, label

    elif provider == "azure_openai":
        # -- Azure OpenAI ----------------------------------------------------
        # Uses the same AsyncOpenAI client but pointed at your Azure endpoint.
        from openai import AsyncOpenAI

        llm_client = AsyncOpenAI(
            api_key=AZURE_OPENAI_KEY,
            base_url=AZURE_OPENAI_ENDPOINT,
            api_version="2024-10-21",
        )
        graphiti = Graphiti(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
            llm_client=llm_client,
        )
        return graphiti, label

    else:
        raise ValueError(f"Unknown provider: {provider}")


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 15: Multi-Provider Plugin Architecture")
    print("=" * 72)
    print(PROVIDER_GUIDE)

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

    group_id = "provider_demo"
    now = datetime.now(timezone.utc)

    # -- 1. OpenAI provider (default) ---------------------------------------
    print("\n" + "=" * 72)
    print("1. OpenAI Provider (default)")
    print("=" * 72)

    if not OPENAI_API_KEY:
        print("  [SKIP] OPENAI_API_KEY not set. Set it to run OpenAI examples.")
        openai_graphiti = None
    else:
        openai_graphiti, label = build_graphiti(provider="openai")
        print(f"\n  Initialized: {label}")
        await openai_graphiti.build_indices_and_constraints()

        await openai_graphiti.add_episode(
            name="openai_demo",
            episode_body=(
                "Dr. Sarah Chen founded Acme Corp in 2019 to revolutionize "
                "supply chain logistics. The company's RouteOptimizer Pro "
                "reduces delivery costs by up to 35% using AI."
            ),
            source=EpisodeType.text,
            source_description="Processed via OpenAI gpt-4o",
            reference_time=now,
            group_id=group_id,
        )
        print("  Added episode via OpenAI extraction\n")

    # -- 2. Anthropic Claude provider ---------------------------------------
    print("\n" + "=" * 72)
    print("2. Anthropic Claude Provider")
    print("=" * 72)

    if not ANTHROPIC_API_KEY:
        print("  [SKIP] ANTHROPIC_API_KEY not set. Set it to run Anthropic examples.")
        claude_graphiti = None
    else:
        claude_graphiti, label = build_graphiti(provider="anthropic")
        print(f"\n  Initialized: {label}")
        await claude_graphiti.build_indices_and_constraints()

        await claude_graphiti.add_episode(
            name="anthropic_demo",
            episode_body=(
                "Acme Corp opened an Austin office in 2023 led by Maria Gonzalez. "
                "The Austin team focuses on expanding RouteOptimizer Pro's "
                "capabilities for the healthcare logistics sector."
            ),
            source=EpisodeType.text,
            source_description="Processed via Anthropic Claude",
            reference_time=now,
            group_id=group_id,
        )
        print("  Added episode via Anthropic extraction\n")

    # -- 3. Ollama local provider -------------------------------------------
    print("\n" + "=" * 72)
    print("3. Ollama (Local) Provider")
    print("=" * 72)

    # Check if Ollama is running by trying to connect to its port
    ollama_available = False
    try:
        with socket.create_connection(("localhost", 11434), timeout=2):
            ollama_available = True
    except (OSError, socket.timeout):
        pass

    if not ollama_available:
        print("  [SKIP] Ollama not detected on localhost:11434.")
        print("  Start it with:  ollama serve")
        print("  Then pull a model:  ollama pull llama3.2")
        ollama_graphiti = None
    else:
        ollama_graphiti, label = build_graphiti(provider="ollama")
        print(f"\n  Initialized: {label}")
        print("  NOTE: Ollama extraction quality depends on the model you have pulled.")
        await ollama_graphiti.build_indices_and_constraints()

        await ollama_graphiti.add_episode(
            name="ollama_demo",
            episode_body=(
                "Acme Corp's customers include GlobalFreight Inc and "
                "QuickShip Logistics. GlobalFreight uses RouteOptimizer Pro "
                "for their entire US fleet."
            ),
            source=EpisodeType.text,
            source_description="Processed via local Ollama model",
            reference_time=now,
            group_id=group_id,
        )
        print("  Added episode via Ollama extraction\n")

    # -- 4. Azure OpenAI provider -------------------------------------------
    print("\n" + "=" * 72)
    print("4. Azure OpenAI Provider")
    print("=" * 72)

    if not AZURE_OPENAI_KEY or not AZURE_OPENAI_ENDPOINT:
        print("  [SKIP] AZURE_OPENAI_KEY or AZURE_OPENAI_ENDPOINT not set.")
        azure_graphiti = None
    else:
        azure_graphiti, label = build_graphiti(provider="azure_openai")
        print(f"\n  Initialized: {label}")
        await azure_graphiti.build_indices_and_constraints()

        await azure_graphiti.add_episode(
            name="azure_demo",
            episode_body=(
                "Acme Corp is exploring an IPO in 2026. Goldman Sachs has "
                "been engaged as the lead underwriter. The company has "
                "grown revenue to $50M ARR."
            ),
            source=EpisodeType.text,
            source_description="Processed via Azure OpenAI",
            reference_time=now,
            group_id=group_id,
        )
        print("  Added episode via Azure OpenAI extraction\n")

    # -- 5. Different embedders ---------------------------------------------
    print("\n" + "=" * 72)
    print("5. Configuring Different Embedders")
    print("=" * 72)

    if OPENAI_API_KEY:
        print(
            "\n  Graphiti accepts an `embedder` parameter to override the\n"
            "  default embedding model. Common options:\n"
            "\n"
            "    embedder='openai'\n"
            "        Uses text-embedding-3-small (1536 dimensions)\n"
            "        Best for: general purpose, lower cost\n"
            "\n"
            "    embedder='openai_large'\n"
            "        Uses text-embedding-3-large (3072 dimensions)\n"
            "        Best for: higher quality retrieval, more expensive\n"
            "\n"
            "  Example:\n"
            "    from graphiti_core import Graphiti\n"
            "    graphiti = Graphiti(uri=..., embedder='openai_large')\n"
        )

        # We don't instantiate a new Graphiti here since it would require
        # a separate DB, but the configuration is shown above.
        print("  (Configuration demonstrated -- no additional DB calls needed)\n")

    # -- 6. Rerankers / cross-encoders --------------------------------------
    print("\n" + "=" * 72)
    print("6. Configuring Rerankers / Cross-Encoders")
    print("=" * 72)

    print(
        "\n  Rerankers improve search quality by re-scoring candidate edges\n"
        "  with a cross-encoder model. This adds ~50-200ms per query but\n"
        "  significantly boosts relevance.\n"
        "\n"
        "  Example:\n"
        "    graphiti = Graphiti(\n"
        "        uri=...,\n"
        "        reranker='cross_encoder',  # enables cross-encoder reranking\n"
        "    )\n"
        "\n"
        "  When to use:\n"
        "    - Production search where ranking quality matters\n"
        "    - Large graphs (1000+ edges) where embedding-only search degrades\n"
        "    - When you need the top-1 result to be highly relevant\n"
        "\n"
        "  When to skip:\n"
        "    - Prototyping / development\n"
        "    - Latency-sensitive real-time applications\n"
        "    - Small graphs (< 100 edges)\n"
    )

    # -- Cleanup ------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Cleanup: closing all connections")
    print("=" * 72)

    for name, g in [
        ("OpenAI", openai_graphiti),
        ("Anthropic", claude_graphiti),
        ("Ollama", ollama_graphiti),
        ("Azure", azure_graphiti),
    ]:
        if g is not None:
            await g.close()
            print(f"  Closed {name} connection.")

    print("\nDone. All provider connections closed.")


if __name__ == "__main__":
    asyncio.run(main())
