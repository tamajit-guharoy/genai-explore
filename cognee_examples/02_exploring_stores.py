"""
02_exploring_stores.py — Inspect what gets written to each store.

After cognify(), Cognee writes to three stores: relational, vector, and graph.
This example shows how to inspect each one to understand what was created.

Cognee v1.1.0 API — uses add/cognify/search with the current module layout.

Prerequisites:
    pip install cognee
    # Set LLM_API_KEY in your environment
"""

import asyncio

import cognee
from cognee.infrastructure.engine.models.DataPoint import DataPoint
from pydantic import Field


# Define custom DataPoints for structured extraction
class Technology(DataPoint):
    name: str = Field(..., index_fields=["name"])
    category: str = Field(default="unknown")
    year_introduced: int | None = None


class Organization(DataPoint):
    name: str = Field(..., index_fields=["name"])
    org_type: str = Field(default="unknown")


class Creates(DataPoint):
    """Edge: Organization created Technology"""
    organization_name: str
    technology_name: str
    year: int | None = None


async def main():
    # ── Ingest and cognify ─────────────────────────────────────────────
    print("Ingesting data...")
    await cognee.add("""
    Docker is a containerization platform created by Docker Inc. in 2013.
    Kubernetes is an orchestration platform originally created by Google in 2014
    and later donated to the Cloud Native Computing Foundation (CNCF).
    Helm is a package manager for Kubernetes created by Microsoft in 2015.
    All three technologies are fundamental to modern cloud-native development.
    """)

    print("Running cognify...")
    await cognee.cognify()

    # ── Inspect datasets ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("RELATIONAL STORE — Datasets and metadata")
    try:
        datasets = await cognee.datasets.list_datasets()
        print(f"Datasets: {datasets}")
    except AttributeError:
        print("datasets: use cognee.datasets to inspect (API varies by version)")

    # ── Vector store: semantic similarity search ────────────────────────
    print("\n" + "=" * 60)
    print("VECTOR STORE — Semantic similarity over text chunks:")

    chunk_results = await cognee.search(
        "container orchestration",
        query_type=cognee.SearchType.CHUNKS,
    )
    for r in chunk_results:
        print(f"  → {r}")

    # ── Graph store: relationship traversal ────────────────────────────
    print("\n" + "=" * 60)
    print("GRAPH STORE — Graph traversal + LLM synthesis:")

    graph_results = await cognee.search(
        "How are Docker, Kubernetes, and Helm related?",
        query_type=cognee.SearchType.GRAPH_COMPLETION,
    )
    for r in graph_results:
        print(f"  → {r}")

    # ── Pure graph traversal (no LLM) ──────────────────────────────────
    print("\n" + "=" * 60)
    print("GRAPH STORE — Pure graph traversal (no LLM synthesis):")
    try:
        raw_graph = await cognee.search(
            "Docker Kubernetes relationship",
            query_type=cognee.SearchType.GRAPH,
        )
        for r in raw_graph:
            print(f"  → {r}")
    except Exception as e:
        print(f"  Graph-only search not available in this version: {e}")

    print("\n" + "=" * 60)
    print("Summary of what was stored:")
    print("  • Relational: document metadata, chunk positions, dataset membership")
    print("  • Vector: embeddings for each chunk, enabling semantic similarity search")
    print("  • Graph: entity nodes (Docker, Kubernetes, Google, etc.) + relationship edges")


if __name__ == "__main__":
    asyncio.run(main())
