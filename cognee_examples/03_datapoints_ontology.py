"""
03_datapoints_ontology.py — Define custom DataPoints and domain ontology.

This example builds a custom data model for a tech company domain:
- Company (entity)
- Person (entity)
- FundingRound (entity)
- WorksAt (relationship)
- InvestedIn (relationship)

Then feeds structured + unstructured data and queries the resulting graph.

Prerequisites:
    pip install cognee pydantic
"""

import asyncio
from datetime import datetime
from uuid import UUID

from pydantic import Field

from cognee.infrastructure.engine.models.DataPoint import DataPoint


# ── Define domain entities ─────────────────────────────────────────────

class Company(DataPoint):
    """A company entity."""
    name: str = Field(..., index_fields=["name"])
    industry: str = Field(default="technology")
    founded_year: int | None = None
    headquarters: str | None = None
    website: str | None = None


class Person(DataPoint):
    """A person entity."""
    name: str = Field(..., index_fields=["name"])
    role: str = Field(default="unknown")
    expertise: list[str] = Field(default_factory=list)


class FundingRound(DataPoint):
    """A funding event entity."""
    company_name: str = Field(..., index_fields=["company_name"])
    round_type: str = Field(default="unknown")  # Seed, Series A, B, C, etc.
    amount_usd: int | None = None
    date: str | None = None
    lead_investor: str | None = None


# ── Define relationships ───────────────────────────────────────────────

class WorksAt(DataPoint):
    """Edge: Person works at Company"""
    person_name: str
    company_name: str
    title: str = Field(default="employee")
    start_year: int | None = None


class InvestedIn(DataPoint):
    """Edge: Investor (Company or Person) invested in a funding round"""
    investor_name: str
    target_company: str
    round_type: str = Field(default="unknown")
    amount_usd: int | None = None


async def main():
    import cognee

    # ── Ingest structured data ─────────────────────────────────────────
    print("Building a tech company knowledge graph...")

    company_data = """
    Acme AI is an artificial intelligence company founded in 2021 in San Francisco.
    Their website is acme.ai. They specialize in large language model deployment.

    Jane Smith is the CEO and co-founder of Acme AI. She previously worked at Google
    as a Senior ML Engineer. Her expertise includes distributed systems and NLP.

    Bob Chen is the CTO of Acme AI. He joined in 2022 after working at Meta as an
    AI Research Scientist. His expertise includes transformer architectures and
    model optimization.

    In March 2024, Acme AI raised a $25 million Series A round led by Sequoia Capital,
    with participation from Andreessen Horowitz. This followed their $5 million seed
    round in 2022 led by Y Combinator.

    In January 2026, Acme AI raised an $80 million Series B led by Founders Fund.
    """

    await cognee.add(company_data, dataset_name="acme_ai")

    # ── Cognify with custom DataPoints ─────────────────────────────────
    print("Extracting entities and relationships...")
    await cognee.cognify()

    # ── Query the structured knowledge ─────────────────────────────────
    print("\n" + "=" * 60)

    queries = [
        "Who invested in Acme AI and how much did they raise?",
        "What is Jane Smith's background and role?",
        "Trace the funding history of Acme AI from seed to Series B.",
        "Who has expertise in transformer architectures?",
    ]

    for query in queries:
        print(f"\n Query: {query}")
        print("-" * 40)
        results = await cognee.search(query)
        for result in results:
            print(f"  → {result}")
        print()

    print("Done! The knowledge graph stores typed entities and their relationships.")


if __name__ == "__main__":
    asyncio.run(main())
