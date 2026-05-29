"""
05_v1_api_workflow.py — Full V1 pipeline with multiple data sources.

Demonstrates:
- Ingesting from multiple sources (file paths, URLs, raw text)
- Dataset scoping for organized knowledge
- Multiple SearchType strategies
- Incremental processing (re-running cognify only processes new data)

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    # ── Ingest multiple data sources into separate datasets ────────────
    print("Ingesting data from multiple sources...")

    # Raw text
    await cognee.add(
        "Microservices architecture decomposes applications into small, "
        "independent services that communicate over APIs. Each service owns "
        "its own data store and can be deployed independently. This pattern "
        "was popularized by companies like Netflix, Amazon, and Uber.",
        dataset_name="architecture",
    )

    await cognee.add(
        "Event-driven architecture uses events to trigger and communicate "
        "between decoupled services. Apache Kafka, developed at LinkedIn, is "
        "the most widely used event streaming platform. Events are immutable "
        "facts about what happened in the system.",
        dataset_name="architecture",
    )

    # Simulate multiple documents
    await cognee.add(
        "Service meshes like Istio and Linkerd handle service-to-service "
        "communication in microservices. They provide observability, traffic "
        "management, and security without requiring code changes. Istio was "
        "originally developed by Google, IBM, and Lyft.",
        dataset_name="infrastructure",
    )

    await cognee.add(
        "Kubernetes has become the standard for container orchestration. "
        "It was originally designed by Google based on their internal Borg "
        "system. CNCF now hosts the project, which has over 100,000 GitHub "
        "stars and contributions from thousands of companies.",
        dataset_name="infrastructure",
    )

    # ── Cognify all datasets ───────────────────────────────────────────
    print("Building knowledge graphs...")
    await cognee.cognify()

    # ── Search with different strategies ───────────────────────────────
    print("\n" + "=" * 60)

    # Strategy 1: Graph completion — best for multi-hop questions
    print("\n── GRAPH_COMPLETION (hybrid: graph + vector + LLM) ──")
    results = await cognee.search(
        "What technologies did Google create and how do they relate to "
        "microservices?",
        query_type=cognee.SearchType.GRAPH_COMPLETION,
    )
    for r in results:
        print(f"  → {r}")

    # Strategy 2: Chunks — pure vector similarity
    print("\n── CHUNKS (pure vector similarity) ──")
    results = await cognee.search(
        "event streaming and messaging platforms",
        query_type=cognee.SearchType.CHUNKS,
    )
    for r in results:
        print(f"  → {r}")

    # Strategy 3: Insights — summarized insights from cognify
    print("\n── INSIGHTS (extracted insights) ──")
    try:
        results = await cognee.search(
            "microservices best practices",
            query_type=cognee.SearchType.INSIGHTS,
        )
        for r in results:
            print(f"  → {r}")
    except Exception:
        print("  (INSIGHTS search may not be available in this version)")

    # ── Scoped search within a dataset ─────────────────────────────────
    print("\n── Scoped to 'infrastructure' dataset ──")
    results = await cognee.search(
        "container orchestration",
        dataset="infrastructure",
    )
    for r in results:
        print(f"  → {r}")

    # ── Demonstrate incremental processing ─────────────────────────────
    print("\n" + "=" * 60)
    print("Adding new data and re-running cognify (incremental)...")

    await cognee.add(
        "Docker Swarm is Docker's native orchestration tool, but it has "
        "largely been superseded by Kubernetes in production environments.",
        dataset_name="infrastructure",
    )
    await cognee.cognify()  # Only processes the new text

    results = await cognee.search(
        "How does Docker Swarm compare to Kubernetes?",
        dataset="infrastructure",
    )
    for r in results:
        print(f"  → {r}")

    print("\nDone! The V1 pipeline supports multiple sources, datasets, and search strategies.")


if __name__ == "__main__":
    asyncio.run(main())
