"""
04_custom_pipeline.py — Build a pipeline with custom extraction logic.

This example shows how to create a custom task and integrate it into
Cognee's pipeline. We create a task that extracts technology maturity
levels (experimental, production, deprecated) from text.

Prerequisites:
    pip install cognee
"""

import asyncio
import re

import cognee


# ── Custom extraction task ─────────────────────────────────────────────
# This is a custom task that could run as part of the cognify pipeline.
# In practice, you'd register it with Cognee's task system.

async def extract_tech_maturity(text: str) -> list[dict]:
    """
    Extract technology maturity indicators from text.

    Returns list of {technology, maturity, confidence} dicts.
    This is a simplified example — a real implementation would use an LLM.
    """
    maturity_patterns = {
        "production": [
            r"(\w+)\s+is\s+(widely\s+)?(used|deployed|adopted)",
            r"(\w+)\s+(powers|runs|drives)\s+(production|critical)",
        ],
        "deprecated": [
            r"(\w+)\s+(is|has\s+been)\s+(deprecated|retired|sunset)",
            r"(\w+)\s+is\s+no\s+longer\s+(supported|maintained)",
        ],
        "experimental": [
            r"(\w+)\s+is\s+(experimental|in\s+beta|in\s+preview)",
            r"(\w+)\s+is\s+being\s+(tested|evaluated|trialled)",
        ],
    }

    results = []
    for maturity, patterns in maturity_patterns.items():
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                results.append({
                    "technology": match.group(1),
                    "maturity": maturity,
                    "confidence": 0.7 if "widely" in match.group(0) else 0.5,
                })

    return results


async def main():
    # ── Ingest technical documentation ─────────────────────────────────
    print("Ingesting technology documentation...")

    tech_docs = """
    React is widely used in production across millions of websites. It powers
    critical frontend infrastructure at companies like Meta, Netflix, and Airbnb.

    AngularJS (version 1.x) has been deprecated and is no longer supported by
    Google. Teams are advised to migrate to Angular (version 2+).

    Vue 3's Composition API is being tested by many teams but the Options API
    remains the production standard.

    Svelte 5 introduces runes, which are currently experimental and in preview.
    The Svelte team recommends using Svelte 4 for production applications.

    Next.js is the recommended production framework for React, widely deployed
    on Vercel's edge network. It supports both server-side rendering and
    static site generation.

    Remix, acquired by Shopify, is being evaluated by many e-commerce teams
    but has not reached the same adoption level as Next.js.
    """

    await cognee.add(tech_docs, dataset_name="tech_radar")
    await cognee.cognify()

    # ── Run our custom extraction ──────────────────────────────────────
    print("\nRunning custom maturity extraction...")
    maturity_results = await extract_tech_maturity(tech_docs)

    print("\nCustom extraction results:")
    print("-" * 40)

    # Group by maturity level
    by_maturity: dict[str, list[str]] = {}
    for item in maturity_results:
        level = item["maturity"]
        if level not in by_maturity:
            by_maturity[level] = []
        by_maturity[level].append(f"{item['technology']} ({item['confidence']:.0%})")

    for level in ["production", "experimental", "deprecated"]:
        if level in by_maturity:
            print(f"\n {level.upper()}:")
            for tech in by_maturity[level]:
                print(f"    • {tech}")

    # ── Compare with Cognee's built-in extraction ──────────────────────
    print("\n" + "=" * 60)
    print("Cognee knowledge graph query results:")
    print("-" * 40)

    queries = [
        "Which frameworks are recommended for production use?",
        "Which technologies are deprecated or no longer supported?",
    ]

    for query in queries:
        print(f"\n Q: {query}")
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")

    print("\nNote: In a production setup, you would register")
    print("extract_tech_maturity as a Cognee Task and add it to the")
    print("cognify pipeline for integrated extraction.")


if __name__ == "__main__":
    asyncio.run(main())
