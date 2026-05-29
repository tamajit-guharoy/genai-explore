"""
Example 19: Observability and Cost Tracking

When building production knowledge graph pipelines, you need visibility into:

  - How long each episode takes to process
  - How many LLM tokens each extraction consumes
  - How many entities and edges are extracted per episode
  - How fast graph database queries execute
  - What each run costs (OpenAI API pricing)

This example implements a simple observability framework with:

  1. A tracing decorator to time functions
  2. Token counting for LLM calls
  3. Entity/edge counting per episode
  4. Graph DB query timing
  5. Cost estimation (OpenAI pricing)
  6. A consolidated processing report

NOTE: Token counts and costs are estimated based on typical usage patterns
since Graphiti may not expose raw token counts directly. For production,
integrate with a telemetry platform like OpenTelemetry or LangSmith.
"""

import asyncio
import functools
import os
import socket
import sys
import time

from datetime import datetime, timezone
from typing import Any, Callable

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
# Observability Framework
# ===================================================================

class ProcessingReport:
    """Collects and summarizes processing metrics for a run."""

    def __init__(self):
        self.episodes: list[dict[str, Any]] = []
        self.db_queries: list[dict[str, Any]] = []
        self.total_llm_calls = 0
        self.total_estimated_tokens = 0
        self.total_estimated_cost = 0.0

    def record_episode(
        self,
        name: str,
        duration_s: float,
        entity_count: int,
        edge_count: int,
        estimated_tokens: int,
        estimated_cost: float,
    ):
        """Record metrics for a single episode processing run."""
        record = {
            "name": name,
            "duration_s": round(duration_s, 2),
            "entity_count": entity_count,
            "edge_count": edge_count,
            "estimated_tokens": estimated_tokens,
            "estimated_cost": estimated_cost,
        }
        self.episodes.append(record)
        self.total_llm_calls += 2  # entity extraction + relationship extraction
        self.total_estimated_tokens += estimated_tokens
        self.total_estimated_cost += estimated_cost

    def record_db_query(self, query_description: str, duration_s: float):
        """Record a database query timing."""
        self.db_queries.append({
            "description": query_description,
            "duration_s": round(duration_s, 3),
        })

    def print_report(self):
        """Print a formatted processing report."""
        print("\n" + "=" * 72)
        print("PROCESSING REPORT")
        print("=" * 72)

        print(f"\n{'Episode':<25} {'Time':>8} {'Entities':>9} {'Edges':>7} {'Tokens':>8} {'Cost':>8}")
        print("-" * 72)

        for ep in self.episodes:
            print(
                f"{ep['name']:<25} "
                f"{ep['duration_s']:>6.2f}s "
                f"{ep['entity_count']:>6d}  "
                f"{ep['edge_count']:>5d}  "
                f"{ep['estimated_tokens']:>6d}  "
                f"${ep['estimated_cost']:<6.4f}"
            )

        print("-" * 72)
        total_time = sum(ep["duration_s"] for ep in self.episodes)
        total_entities = sum(ep["entity_count"] for ep in self.episodes)
        total_edges = sum(ep["edge_count"] for ep in self.episodes)
        print(
            f"{'TOTAL':<25} "
            f"{total_time:>6.2f}s "
            f"{total_entities:>6d}  "
            f"{total_edges:>5d}  "
            f"{self.total_estimated_tokens:>6d}  "
            f"${self.total_estimated_cost:<6.4f}"
        )

        print(f"\n  Total LLM calls:        {self.total_llm_calls}")
        print(f"  Total estimated tokens: {self.total_estimated_tokens}")
        print(f"  Total estimated cost:   ${self.total_estimated_cost:.4f}")
        print(f"  Avg tokens per episode: {self.total_estimated_tokens // max(len(self.episodes), 1)}")

        if self.db_queries:
            print(f"\n  Database Queries:")
            for q in self.db_queries:
                print(f"    {q['description']:<50} {q['duration_s']:>6.3f}s")

        print("\n  (Costs estimated at OpenAI gpt-4o pricing:")
        print("   Input: $2.50 / 1M tokens, Output: $10.00 / 1M tokens)")
        print("=" * 72)


def trace_db_query(report: ProcessingReport):
    """Decorator that times a database query and records it in the report."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = await func(*args, **kwargs)
            duration = time.perf_counter() - start
            report.record_db_query(func.__name__, duration)
            return result
        return async_wrapper

    return decorator


# Simple cost estimation based on typical gpt-4o usage
# Each extraction call processes roughly 500-2000 tokens of text
# and generates 200-800 tokens of structured output.
GPT4O_INPUT_COST_PER_TOKEN = 2.50 / 1_000_000  # $2.50 per 1M input tokens
GPT4O_OUTPUT_COST_PER_TOKEN = 10.00 / 1_000_000  # $10.00 per 1M output tokens


def estimate_extraction_cost(episode_text: str) -> tuple[int, float]:
    """
    Estimate LLM tokens and cost for extracting entities + relationships
    from a given text. Returns (estimated_tokens, estimated_cost_usd).

    This is a rough estimate. Actual token counts depend on the LLM
    provider, model, prompt template, and output length.
    """
    # Rough heuristic: 1 token ~= 4 characters for English text
    input_chars = len(episode_text)
    input_tokens = input_chars // 4

    # Prompt overhead: system prompt + instructions (~800 tokens)
    prompt_overhead = 800

    # Entity extraction output: ~100 tokens per entity found
    # Relationship extraction output: ~80 tokens per relationship
    # We estimate ~3-5 entities and ~3-5 relationships for typical text
    output_tokens_entities = 400  # ~4 entities * 100 tokens
    output_tokens_relations = 320  # ~4 relationships * 80 tokens

    total_input_tokens = (input_tokens + prompt_overhead) * 2  # 2 LLM calls
    total_output_tokens = output_tokens_entities + output_tokens_relations

    cost = (
        total_input_tokens * GPT4O_INPUT_COST_PER_TOKEN
        + total_output_tokens * GPT4O_OUTPUT_COST_PER_TOKEN
    )

    return total_input_tokens + total_output_tokens, cost


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 19: Observability and Cost Tracking")
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

    # Create the processing report
    report = ProcessingReport()

    # We'll time and instrument the search method by wrapping it
    original_search = graphiti.search

    async def timed_search(query, group_ids, num_results=5):
        start = time.perf_counter()
        result = await original_search(query, group_ids=group_ids, num_results=num_results)
        duration = time.perf_counter() - start
        report.record_db_query(f"search: '{query[:50]}...'", duration)
        return result

    graphiti.search = timed_search

    group_id = "observability_demo"
    base_time = datetime.now(timezone.utc)

    # ------------------------------------------------------------------
    # Process episodes with observability
    # ------------------------------------------------------------------
    print("\n--- Processing episodes with observability enabled ---\n")

    episodes_data = [
        {
            "name": "company_founding",
            "body": (
                "Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco. "
                "Sarah serves as CEO. The company focuses on AI-powered logistics."
            ),
        },
        {
            "name": "product_launch",
            "body": (
                "In 2021, Acme launched RouteOptimizer Pro. "
                "The product uses ML to reduce delivery costs by 35%. "
                "James Miller is VP of Engineering."
            ),
        },
        {
            "name": "customer_wins",
            "body": (
                "Acme Corp's customers include GlobalFreight Inc and QuickShip "
                "Logistics. GlobalFreight signed a $2M annual contract in 2024."
            ),
        },
        {
            "name": "europe_office",
            "body": (
                "In 2025, Acme Corp opened a Berlin office to serve European "
                "customers. Maria Gonzalez leads European operations. "
                "The Berlin team has 25 employees."
            ),
        },
    ]

    for ep_data in episodes_data:
        # Estimate cost before processing
        estimated_tokens, estimated_cost = estimate_extraction_cost(ep_data["body"])

        # Time the extraction
        start_time = time.perf_counter()
        episode_result = await graphiti.add_episode(
            name=ep_data["name"],
            episode_body=ep_data["body"],
            source=EpisodeType.text,
            source_description="Observability demo",
            reference_time=base_time,
            group_id=group_id,
        )
        duration = time.perf_counter() - start_time

        # Count entities and edges (approximate from episode metadata)
        # In a real scenario, you would query the graph to get exact counts.
        # Here we estimate based on the text content.
        entity_count_estimate = len(
            [w for w in ["Acme Corp", "Sarah", "CEO", "San Francisco", "RouteOptimizer"]
             if w in ep_data["body"] or w.split()[-1] in ep_data["body"]]
        ) + 2  # base entities
        edge_count_estimate = max(1, entity_count_estimate - 1)

        report.record_episode(
            name=ep_data["name"],
            duration_s=duration,
            entity_count=entity_count_estimate,
            edge_count=edge_count_estimate,
            estimated_tokens=estimated_tokens,
            estimated_cost=estimated_cost,
        )

        print(
            f"  Processed '{ep_data['name']}': "
            f"{duration:.2f}s, "
            f"~{estimated_tokens} tokens, "
            f"~${estimated_cost:.4f}"
        )

    # ------------------------------------------------------------------
    # Run some queries and track DB performance
    # ------------------------------------------------------------------
    print("\n--- Running queries with DB timing ---\n")

    queries = [
        "Who founded Acme Corp?",
        "What products does Acme offer?",
        "Which customers does Acme Corp have?",
        "Where is the European office located?",
    ]

    for query in queries:
        print(f'  Query: "{query}"')
        edges = await graphiti.search(
            query=query,
            group_ids=[group_id],
            num_results=3,
        )
        if edges:
            for edge in edges:
                print(f"    -> {edge.fact}")
        else:
            print("    (no results)")
        print()

    # ------------------------------------------------------------------
    # Print the consolidated report
    # ------------------------------------------------------------------
    report.print_report()

    # ------------------------------------------------------------------
    # Discuss production observability
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Production Observability Recommendations")
    print("=" * 72)

    print(
        """
  For production deployments, consider:

  1. **OpenTelemetry** -- Trace every Graphiti operation with spans:
     from opentelemetry import trace
     tracer = trace.get_tracer("graphiti")
     with tracer.start_as_current_span("add_episode"):
         await graphiti.add_episode(...)

  2. **LangSmith / LangFuse** -- If using LangChain with Graphiti:
     - Track LLM calls, token counts, and latency
     - Compare extraction quality across model versions

  3. **Custom middleware** -- Wrap Graphiti methods with:
     - Logging (structured JSON logs)
     - Metrics (Prometheus counters/histograms)
     - Cost tracking (per-episode, per-group, per-user)

  4. **Token counting** -- For precise token counts:
     import tiktoken
     encoding = tiktoken.encoding_for_model("gpt-4o")
     tokens = encoding.encode(text)
     actual_token_count = len(tokens)

  5. **Cost estimation formula** (OpenAI gpt-4o, Jan 2025):
     Input:  $2.50 / 1M tokens  ($0.00250 / 1K tokens)
     Output: $10.00 / 1M tokens ($0.01000 / 1K tokens)
     Cache hit: $1.25 / 1M tokens (50% discount)
"""
    )

    # -- Cleanup ------------------------------------------------------------
    await graphiti.close()
    print("\nDone. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
