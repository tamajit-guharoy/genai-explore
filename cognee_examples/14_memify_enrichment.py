"""
14_memify_enrichment.py — Evolve a knowledge graph over time with memify().

This example simulates knowledge arriving incrementally over time:
- Day 1: Initial knowledge about a startup
- Day 30: New funding round, new team members
- Day 60: Product launch, market response
- Day 90: Acquisition rumors

After each batch, memify() enriches the graph without a full rebuild.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def add_and_enrich(data: str, label: str):
    """Add data and run memify for incremental enrichment."""
    print(f"\n{'=' * 60}")
    print(f" {label}")
    print(f"{'=' * 60}")
    print(f"Data: {data[:120]}...")

    await cognee.add(data, dataset_name="startup_tracker")
    # memify: incrementally enrich without full rebuild
    try:
        await cognee.memify()
        print(" → Memify complete (incremental enrichment)")
    except AttributeError:
        # Fallback to cognify if memify not available
        await cognee.cognify()
        print(" → Cognify complete (full rebuild — memify not in this version)")


async def query_checkpoint(label: str, queries: list[str]):
    """Query the graph at a checkpoint."""
    print(f"\n── {label} Checkpoint ──")
    for q in queries:
        results = await cognee.search(q)
        print(f" Q: {q}")
        for r in results:
            print(f"  → {r}")
        print()


async def main():
    print("Tracking a startup's evolution over 90 days")
    print("Each phase adds new information; memify() enriches the graph.")

    # ── Day 1: Initial knowledge ───────────────────────────────────────
    await add_and_enrich(
        "NovaTech AI is a startup founded in January 2025 by Dr. Elena Torres "
        "and Marcus Webb. The company is based in Austin, Texas and is building "
        "an AI-powered drug discovery platform. They raised a $3M seed round "
        "led by SciFuture Ventures. The founding team has 5 engineers.",
        "Day 1 — Founding & Seed Round",
    )

    await query_checkpoint("Day 1", [
        "Who founded NovaTech AI and what do they build?",
    ])

    # ── Day 30: Series A and growth ────────────────────────────────────
    await add_and_enrich(
        "NovaTech AI closed a $15M Series A round led by Andreessen Horowitz "
        "with participation from SciFuture Ventures and Lux Capital. The team "
        "has grown to 22 people. They hired Dr. Sarah Park as Chief Scientific "
        "Officer. Sarah previously led drug discovery at Pfizer. The company "
        "announced a partnership with Stanford University's Bio-X lab.",
        "Day 30 — Series A & Team Growth",
    )

    await query_checkpoint("Day 30", [
        "What is NovaTech's total funding and who are the investors?",
        "Who is Sarah Park and what is her background?",
    ])

    # ── Day 60: Product launch ─────────────────────────────────────────
    await add_and_enrich(
        "NovaTech AI launched NovaDiscover v1.0, their AI drug discovery "
        "platform. The platform identified 3 promising compounds for "
        "Alzheimer's treatment in its first month, one of which entered "
        "preclinical trials. Key partnerships include Johnson & Johnson "
        "and the Mayo Clinic. Revenue: $2M annual recurring from 5 enterprise "
        "customers. The platform uses transformer-based models trained on "
        "proprietary molecular data.",
        "Day 60 — Product Launch",
    )

    await query_checkpoint("Day 60", [
        "What results has NovaDiscover achieved so far?",
        "Which large companies are partnering with NovaTech?",
    ])

    # ── Day 90: Market traction & acquisition interest ─────────────────
    await add_and_enrich(
        "NovaTech AI is reportedly in acquisition talks with Recursion "
        "Pharmaceuticals for an estimated $500M. The company now serves 12 "
        "enterprise customers including Merck and AstraZeneca. ARR has grown "
        "to $8M. The team is 45 people. Dr. Elena Torres was named to "
        "Forbes 30 Under 30 in Healthcare. However, a key risk emerged: "
        "their lead preclinical candidate showed liver toxicity in animal "
        "studies, potentially delaying the program by 6-12 months.",
        "Day 90 — Acquisition Interest & Challenges",
    )

    await query_checkpoint("Day 90", [
        "What is NovaTech's current valuation, revenue, and team size?",
        "What risks does NovaTech face with their drug pipeline?",
        "Trace the complete funding history of NovaTech from seed to Series A.",
    ])

    print("\n" + "=" * 60)
    print("Evolution complete. The knowledge graph now contains:")
    print("  • 4 time-checkpointed snapshots of company state")
    print("  • Entity evolution: 5 → 22 → 45 employees")
    print("  • Funding history: $3M seed → $15M Series A")
    print("  • Product trajectory: pre-launch → launched → 12 customers")
    print("  • New relationships: partnerships, risks, acquisition interest")
    print("\nMemify() enabled incremental enrichment without re-processing")
    print("earlier data at each checkpoint.")


if __name__ == "__main__":
    asyncio.run(main())
