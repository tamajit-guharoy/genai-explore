"""
21_hr_knowledge.py — Enterprise HR & Internal Knowledge Management.

Builds an organizational knowledge graph connecting people, teams, projects,
and skills to answer questions about who knows what, who's available, and
how teams are structured.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Building Organizational Knowledge Graph...")
    print("=" * 60)

    # ── People and teams ───────────────────────────────────────────────
    await cognee.add("""
    ORGANIZATION STRUCTURE — TechCorp Inc.

    ALICE JOHNSON — Senior Backend Engineer, Platform Team (Berlin office)
    Skills: Go, Kubernetes, PostgreSQL, gRPC, Terraform
    Current projects: Payment Service Migration (Lead), API Gateway v2
    Previously: Auth Service Redesign (2024-2025)
    Joined: March 2023
    Certifications: CKA (Certified Kubernetes Administrator), AWS Solutions Architect

    BOB CHEN — Staff Engineer, Platform Team (Berlin office)
    Skills: Kubernetes, Go, Rust, Distributed Systems, Service Mesh
    Current projects: Service Mesh Rollout (Lead)
    Previously: Monolith Decomposition (2023-2024)
    Joined: January 2022
    Certifications: CKA, CKAD, AWS DevOps Professional

    CAROL MARTINEZ — ML Engineer, AI Team (Remote — Spain)
    Skills: Python, PyTorch, Transformers, MLOps, Kubernetes
    Current projects: Recommendation Engine v2 (Lead), Model Serving Platform
    Previously: Customer Segmentation Model (2024)
    Joined: June 2024
    Note: Has Kubernetes experience from previous role at Spotify
    """, dataset_name="org")

    await cognee.add("""
    ORGANIZATION STRUCTURE (continued):

    DAVID PARK — Frontend Lead, Web Team (Berlin office)
    Skills: React, TypeScript, Next.js, GraphQL, Design Systems
    Current projects: Dashboard Redesign (Lead), Design System v2
    Previously: Mobile Web App (2023-2024)
    Joined: August 2022

    EMMA WILSON — Engineering Manager, Platform Team (Berlin office)
    Skills: Engineering Management, Agile, System Design, Incident Response
    Manages: Alice Johnson, Bob Chen
    Current projects: Platform Reliability Initiative
    Joined: November 2021

    FRANK ZHANG — DevOps Engineer, Platform Team (Berlin office)
    Skills: Terraform, AWS, GitHub Actions, Prometheus, Grafana
    Current projects: CI/CD Pipeline Modernization (Lead), Infrastructure as Code
    Joined: April 2024
    Certifications: AWS DevOps Professional, HashiCorp Terraform Associate
    """, dataset_name="org")

    # ── Projects ───────────────────────────────────────────────────────
    await cognee.add("""
    PROJECTS:

    PROJECT: Payment Service Migration
    Status: In Progress (started Jan 2026, target June 2026)
    Lead: Alice Johnson
    Team: Alice Johnson, Bob Chen (reviewer), Frank Zhang (CI/CD)
    Description: Migrate the legacy payment service from Python monolith to
    Go microservices on Kubernetes. Requires: Go, Kubernetes, PostgreSQL,
    gRPC, and domain knowledge of the payment system.
    Dependencies: API Gateway v2 (must be completed first)

    PROJECT: Service Mesh Rollout
    Status: In Progress (started Feb 2026, target September 2026)
    Lead: Bob Chen
    Team: Bob Chen, Frank Zhang (IaC support)
    Description: Roll out Istio service mesh across all Kubernetes clusters.
    Requires: Kubernetes, service mesh, Istio, distributed systems expertise.

    PROJECT: Recommendation Engine v2
    Status: In Progress (started March 2026, target August 2026)
    Lead: Carol Martinez
    Team: Carol Martinez
    Description: Rebuild recommendation engine with transformer-based models
    on Kubernetes. Requires: Python, PyTorch, Transformers, Kubernetes, MLOps.
    Note: Looking for a Kubernetes-experienced backend engineer to pair with.
    """, dataset_name="org")

    # ── Skills and certifications ──────────────────────────────────────
    await cognee.add("""
    SKILL MATRIX:

    KUBERNETES: Bob Chen (expert), Alice Johnson (advanced), Carol Martinez
    (intermediate), Frank Zhang (intermediate)

    GO: Alice Johnson (advanced), Bob Chen (advanced)

    TERRAFORM: Alice Johnson (intermediate), Frank Zhang (expert)

    MLOPS/ML: Carol Martinez (expert)

    FRONTEND: David Park (expert)

    DISTRIBUTED SYSTEMS: Bob Chen (expert)

    INCIDENT RESPONSE: Emma Wilson (expert), Bob Chen (advanced)

    AWS: Frank Zhang (expert), Alice Johnson (advanced), Bob Chen (intermediate)
    """, dataset_name="org")

    await cognee.cognify()

    # ── Organizational queries ─────────────────────────────────────────
    print("\n── HR & Organizational Queries ──\n")

    queries = [
        # Skills search
        "Who in the Berlin office has Kubernetes experience and is not "
        "currently fully allocated to a project?",

        # Team structure
        "How is the Platform team structured and what projects are they "
        "working on?",

        # Staffing recommendation
        "The Recommendation Engine v2 project needs Kubernetes and backend "
        "engineering help. Who in the company has the right skills and "
        "capacity to support it?",

        # Onboarding context
        "If we hire a new backend engineer for the Platform team, what "
        "technologies and projects would they need to ramp up on?",

        # Cross-team dependencies
        "What dependencies exist between the Payment Service Migration and "
        "other projects?",
    ]

    for query in queries:
        print(f" Q: {query}")
        print("-" * 60)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Done! Org knowledge graphs enable sophisticated people+skills+project")
    print("queries that would take hours of manual cross-referencing.")


if __name__ == "__main__":
    asyncio.run(main())
