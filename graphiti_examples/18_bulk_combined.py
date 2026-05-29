"""
Example 18: Combined Extraction and Bulk Processing

Graphiti offers two extraction modes:

  1. **Individual extraction** (default): Each add_episode() makes separate
     LLM calls for entity extraction and relationship extraction.
     Higher quality, but slower and more expensive.

  2. **Combined extraction**: A single LLM call extracts both nodes and edges
     simultaneously. Faster and cheaper, but may miss subtle relationships.

  3. **Multi-episode batching**: Process many episodes in one batch for higher
     throughput. Reduces the number of LLM API calls.

  4. **Decoupled timestamp resolution**: Resolve temporal references after
     extraction, reducing the per-episode LLM workload.

This example demonstrates all four approaches and compares their performance,
cost, and quality trade-offs.

Best Practices:
  - Use combined extraction for simple, well-structured text
  - Use individual extraction for complex, ambiguous text
  - Batch size of 5-10 episodes is a good starting point
  - Decouple timestamps when many episodes share the same time context
"""

import asyncio
import os
import socket
import sys
import time

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
        "WARNING: OPENAI_API_KEY is not set. Graphiti needs an LLM for extraction.\n"
    )


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


# ===================================================================
# Test data: 8 episodes about company developments
# ===================================================================
TEST_EPISODES = [
    {
        "name": "ceo_change",
        "body": (
            "Acme Corp announced that Dr. Sarah Chen is stepping down as CEO "
            "after 6 years. Former COO Robert Kim will take over as CEO "
            "effective March 1, 2025."
        ),
    },
    {
        "name": "new_cfO",
        "body": (
            "Acme Corp hired Lisa Patel as their new CFO. Lisa previously "
            "served as CFO at DataStream Inc for 4 years. She will start "
            "on April 15, 2025."
        ),
    },
    {
        "name": "product_launch",
        "body": (
            "Acme Corp launched WarehouseAI, a new warehouse optimization "
            "product. The product uses computer vision to track inventory. "
            "VP of Engineering James Miller led the development."
        ),
    },
    {
        "name": "europe_expansion",
        "body": (
            "Acme Corp opened a European headquarters in Berlin, Germany. "
            "The office will be led by Dr. Sarah Chen in her new role as "
            "President of International Operations."
        ),
    },
    {
        "name": "partnership",
        "body": (
            "Acme Corp formed a strategic partnership with FreightHub Europe. "
            "The partnership gives Acme access to FreightHub's logistics "
            "network across 12 European countries."
        ),
    },
    {
        "name": "revenue_milestone",
        "body": (
            "Acme Corp reported $50M ARR in Q4 2025, a 60% increase year-over-year. "
            "RouteOptimizer Pro contributed 70% of revenue. WarehouseAI "
            "contributed 20% in its first quarter."
        ),
    },
    {
        "name": "funding_round",
        "body": (
            "Acme Corp raised $100M in Series C funding led by Meridian Ventures. "
            "Existing investors Sequoia Capital and A16Z also participated. "
            "The funding will support European expansion."
        ),
    },
    {
        "name": "board_change",
        "body": (
            "Acme Corp appointed Dr. Sarah Chen to the board of directors. "
            "She will also serve as chair of the new International Strategy "
            "Committee. Robert Kim will report to the board quarterly."
        ),
    },
]


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 18: Combined Extraction and Bulk Processing")
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

    base_time = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Method 1: Individual extraction (default)
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Method 1: Individual Extraction (default)")
    print("=" * 72)
    print(
        "  Each add_episode() call performs two LLM requests:\n"
        "    1. Entity extraction (identify nodes)\n"
        "    2. Relationship extraction (identify edges)\n"
        "  Higher quality but also higher cost and latency.\n"
    )

    graphiti_individual = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    await graphiti_individual.build_indices_and_constraints()

    individual_start = time.perf_counter()
    for ep in TEST_EPISODES[:4]:  # Use first 4 episodes for comparison
        await graphiti_individual.add_episode(
            name=ep["name"],
            episode_body=ep["body"],
            source=EpisodeType.text,
            source_description="Individual extraction demo",
            reference_time=base_time,
            group_id="method_individual",
        )
    individual_duration = time.perf_counter() - individual_start
    print(f"  Processed 4 episodes in {individual_duration:.2f}s")
    print(f"  Average: {individual_duration / 4:.2f}s per episode")

    # ------------------------------------------------------------------
    # Method 2: Combined extraction (single LLM call)
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Method 2: Combined Node+Edge Extraction")
    print("=" * 72)
    print(
        "  Uses a single LLM call to extract both nodes and edges\n"
        "  simultaneously. Fewer API calls = faster, cheaper.\n"
        "  Trade-off: may miss subtle or implicit relationships.\n"
    )

    graphiti_combined = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    await graphiti_combined.build_indices_and_constraints()

    combined_start = time.perf_counter()
    for ep in TEST_EPISODES[:4]:
        await graphiti_combined.add_episode(
            name=ep["name"],
            episode_body=ep["body"],
            source=EpisodeType.text,
            source_description="Combined extraction demo",
            reference_time=base_time,
            group_id="method_combined",
            # Combined mode: extract nodes and edges in one LLM call
            extraction_mode="combined",
        )
    combined_duration = time.perf_counter() - combined_start
    print(f"  Processed 4 episodes in {combined_duration:.2f}s")
    print(f"  Average: {combined_duration / 4:.2f}s per episode")
    if combined_duration < individual_duration:
        print(f"  Speedup: {individual_duration / combined_duration:.1f}x faster")
    else:
        print("  (combined mode not substantially faster -- quality may differ)")

    # ------------------------------------------------------------------
    # Method 3: Bulk batching (multi-episode)
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Method 3: Multi-Episode Batching (bulk processing)")
    print("=" * 72)
    print(
        "  Process multiple episodes in a single batch, reducing total\n"
        "  LLM API calls. Best for ingesting large datasets.\n"
        "  Recommended batch size: 5-10 episodes.\n"
    )

    graphiti_bulk = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    await graphiti_bulk.build_indices_and_constraints()

    # Prepare episodes as a list of dicts for bulk ingestion
    bulk_episodes = [
        {
            "name": ep["name"],
            "episode_body": ep["body"],
            "source": EpisodeType.text,
            "source_description": "Bulk processing demo",
            "reference_time": base_time,
            "group_id": "method_bulk",
        }
        for ep in TEST_EPISODES
    ]

    bulk_start = time.perf_counter()
    # Bulk add processes all episodes together, batching LLM calls
    results = await graphiti_bulk.add_episodes(bulk_episodes)
    bulk_duration = time.perf_counter() - bulk_start
    print(f"  Processed {len(bulk_episodes)} episodes in bulk in {bulk_duration:.2f}s")
    print(f"  Average: {bulk_duration / len(bulk_episodes):.2f}s per episode")

    # ------------------------------------------------------------------
    # Method 4: Decoupled timestamp resolution
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Method 4: Decoupled Timestamp Resolution")
    print("=" * 72)
    print(
        "  When many episodes share the same temporal context, you can\n"
        "  decouple timestamp resolution from extraction. This means:\n"
        "    - Extract entities and relationships first (timestamp-agnostic)\n"
        "    - Resolve temporal references in a separate pass\n"
        "  Reduces per-episode LLM work when timestamps are uniform.\n"
    )

    graphiti_decoupled = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    await graphiti_decoupled.build_indices_and_constraints()

    decoupled_start = time.perf_counter()
    for ep in TEST_EPISODES[:4]:
        await graphiti_decoupled.add_episode(
            name=ep["name"],
            episode_body=ep["body"],
            source=EpisodeType.text,
            source_description="Decoupled timestamp demo",
            reference_time=base_time,
            group_id="method_decoupled",
            # Decouple timestamp: extract facts without resolving timestamps now
            resolve_timestamps=False,
        )
    # Now resolve timestamps in a single batch pass
    await graphiti_decoupled.resolve_timestamps(group_ids=["method_decoupled"])
    decoupled_duration = time.perf_counter() - decoupled_start
    print(f"  Processed 4 episodes (decoupled timestamps) in {decoupled_duration:.2f}s")

    # ------------------------------------------------------------------
    # Performance comparison
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Performance Comparison Summary")
    print("=" * 72)

    print(
        f"""
  Method                   | Episodes | Total Time | Per Episode
  ---------------------------------------------------------------
  Individual extraction    |    4     | {individual_duration:>6.2f}s   | {individual_duration / 4:>6.2f}s
  Combined extraction      |    4     | {combined_duration:>6.2f}s   | {combined_duration / 4:>6.2f}s
  Bulk batching            |    {len(bulk_episodes)}     | {bulk_duration:>6.2f}s   | {bulk_duration / len(bulk_episodes):>6.2f}s
  Decoupled timestamps     |    4     | {decoupled_duration:>6.2f}s   | {decoupled_duration / 4:>6.2f}s

  Trade-off Guide:

  | Mode                   | Cost  | Quality | Speed | Best for                  |
  |------------------------|-------|---------|-------|---------------------------|
  | Individual (default)   | High  | Best    | Slow  | Complex, ambiguous text   |
  | Combined               | Low   | Good    | Fast  | Simple, structured text   |
  | Bulk batch             | Low   | Good    | Fast  | Large ingestion jobs      |
  | Decoupled timestamps   | Med   | Good    | Med   | Uniform temporal context  |

  Batch size best practices:
    - Small batches (2-5):  For diverse, unrelated content
    - Medium batches (5-10): General purpose, good balance
    - Large batches (10-20): Homogeneous content (same topic/time)
    - Avoid > 20 per batch: Quality degrades beyond this
"""
    )

    # -- Cleanup ------------------------------------------------------------
    for name, g in [
        ("Individual", graphiti_individual),
        ("Combined", graphiti_combined),
        ("Bulk", graphiti_bulk),
        ("Decoupled", graphiti_decoupled),
    ]:
        await g.close()
        print(f"  Closed {name} connection.")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
