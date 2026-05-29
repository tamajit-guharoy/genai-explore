"""
09_multimodal.py — Ingest a mix of text, PDF content, and image descriptions.

While Cognee supports true multimodal ingestion (PDFs, images, audio) via its
adapters, this example works WITHOUT needing actual files on disk. It simulates
multimodal data by passing text extracted from different modalities, then shows
how Cognee links entities across them.

To use real multimodal ingestion, replace the string data with actual file paths:
    await cognee.add("path/to/whitepaper.pdf")
    await cognee.add("path/to/product_image.png")
    await cognee.add("path/to/earnings_call.mp3")

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Simulating multimodal ingestion (text + image descriptions + transcript)")
    print("=" * 60)

    # ── Document 1: A PDF report (simulated as text) ──────────────────
    report_text = """
    Q4 2025 PRODUCT LAUNCH RETROSPECTIVE
    Executive Summary: Project Falcon, our next-generation analytics platform,
    launched on November 15, 2025. The launch exceeded expectations with
    50,000 signups in the first week, driven primarily by the new AI-powered
    anomaly detection feature. John Chen (VP Engineering) noted that the
    infrastructure held up well, handling 10x the projected load. The marketing
    campaign, led by Sarah Kim, generated 2M impressions across LinkedIn and
    Twitter. Key risks identified: mobile responsiveness needs improvement
    (35% bounce rate on mobile vs 12% on desktop) and the onboarding flow
    has a 40% drop-off at step 3.
    """

    # ── Document 2: Image descriptions (simulated) ─────────────────────
    image_description = """
    IMAGE: Product screenshot of Project Falcon dashboard showing the anomaly
    detection interface. The dashboard displays a time-series graph with a
    highlighted anomaly spike at 14:32 UTC. Below the graph, an AI-generated
    explanation reads: "Unusual spike in API latency detected. Correlated with
    increased traffic from the /api/search endpoint. Recommended action: check
    Elasticsearch cluster health." The UI uses a dark theme with blue accent
    colors. Navigation sidebar shows: Overview, Anomalies, Reports, Settings.
    """

    # ── Document 3: Meeting transcript (simulated) ────────────────────
    meeting_transcript = """
    AUDIO TRANSCRIPT — Sprint Review — January 5, 2026
    Sarah Kim: The Falcon launch metrics are strong, but mobile is a real
    concern. We're losing a third of users before they see the AI features.
    John Chen: Agreed. My team is prioritizing the mobile responsive redesign
    for Sprint 24. We should have it ready for testing by end of January.
    Sarah Kim: Also, the anomaly detection demo at the SaaStr conference
    generated a ton of inbound interest. We have 200 demo requests to process.
    Let's prioritize enterprise accounts with >500 seats.
    """

    # ── Ingest all three modalities into the same dataset ──────────────
    await cognee.add(report_text, dataset_name="project_falcon")
    await cognee.add(image_description, dataset_name="project_falcon")
    await cognee.add(meeting_transcript, dataset_name="project_falcon")

    print("Building unified knowledge graph from multimodal data...")
    await cognee.cognify()

    # ── Cross-modal queries ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("Cross-modal query results:")

    queries = [
        # Entity linking: "John Chen" appears in both report and transcript
        "What did John Chen say about the infrastructure and what is his team working on?",
        # Feature linking: "anomaly detection" across report, image, and transcript
        "What is the status of the anomaly detection feature?",
        # Risk linking: mobile issues mentioned in report, addressed in transcript
        "What is the mobile responsiveness issue and what is being done about it?",
    ]

    for query in queries:
        print(f"\n Q: {query}")
        print("-" * 40)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Note: Cognee deduplicated entities across modalities.")
    print("'John Chen' from the PDF report = 'John Chen' from the audio transcript.")
    print("This is cross-modal entity resolution in action.")


if __name__ == "__main__":
    asyncio.run(main())
