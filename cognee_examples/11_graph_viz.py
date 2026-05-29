"""
11_graph_viz.py — Generate and explore knowledge graph visualizations.

After cognify, you can export an interactive D3.js HTML visualization of your
knowledge graph. This example builds a graph of a fictional tech ecosystem
and exports it for visual exploration.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Building a tech ecosystem knowledge graph...")

    # ── Create a rich, interconnected dataset ─────────────────────────
    ecosystem_data = """
    Cloud Platform Ecosystem:

    Amazon Web Services (AWS) was launched in 2006 and is the market leader in
    cloud computing with 32% market share. AWS offers EC2 for compute, S3 for
    storage, and Lambda for serverless computing. Andy Jassy led AWS until 2021.

    Microsoft Azure is the second-largest cloud provider with 23% market share.
    Azure was launched in 2010. It is deeply integrated with Microsoft's
    enterprise products like Office 365, Active Directory, and GitHub (acquired
    in 2018). Satya Nadella championed Azure's growth.

    Google Cloud Platform (GCP) holds 11% market share. GCP is known for its
    strength in Kubernetes (which Google created), BigQuery for data analytics,
    and TensorFlow for machine learning. Thomas Kurian has led GCP since 2019.

    Docker is the dominant containerization platform. It was created by
    Solomon Hykes and launched in 2013. Docker containers can run on any
    cloud platform, making applications portable across AWS, Azure, and GCP.

    Kubernetes (K8s) was originally designed by Google based on their internal
    Borg system. It was open-sourced in 2014 and is now managed by the CNCF.
    Kubernetes orchestrates Docker containers and runs on all major clouds.

    Terraform by HashiCorp enables Infrastructure as Code across AWS, Azure,
    and GCP. Mitchell Hashimoto created Terraform in 2014. It uses HCL
    (HashiCorp Configuration Language) to define infrastructure declaratively.

    The CNCF (Cloud Native Computing Foundation) hosts Kubernetes, Prometheus
    (monitoring), Envoy (service mesh), and many other cloud-native projects.
    CNCF is a subsidiary of the Linux Foundation.
    """

    await cognee.add(ecosystem_data, dataset_name="tech_ecosystem")
    await cognee.cognify()

    # ── Generate graph visualization ──────────────────────────────────
    print("\nGenerating interactive graph visualization...")

    try:
        await cognee.visualize_graph(
            output_path="tech_ecosystem_graph.html",
            dataset="tech_ecosystem",
            max_nodes=100,
            include_edges=True,
        )
        print(" Graph saved to: tech_ecosystem_graph.html")
        print("   Open this file in a browser to explore:")
        print("   • Drag nodes to rearrange")
        print("   • Click nodes to see properties")
        print("   • Zoom and pan to explore connections")
        print("   • Search for specific entities")
        print("   • Filter by node type (Company, Person, Technology, etc.)")
    except Exception as e:
        print(f" Visualization export not available: {e}")
        print("   (The visualize_graph feature may require additional setup)")

    # ── Alternative: text-based graph exploration ─────────────────────
    print("\n" + "=" * 60)
    print("Text-based graph exploration (always available):")

    exploration_queries = [
        "Show all connections between Google and Kubernetes.",
        "What technologies are managed by the CNCF?",
        "How do Docker and Kubernetes relate to each other and to cloud platforms?",
        "Who created Terraform and what cloud platforms does it support?",
    ]

    for query in exploration_queries:
        print(f"\n Q: {query}")
        print("-" * 40)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Done! The knowledge graph captures the complex web of relationships")
    print("between cloud providers, technologies, and people.")


if __name__ == "__main__":
    asyncio.run(main())
