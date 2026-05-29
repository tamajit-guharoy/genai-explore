"""
Example 23: Multi-Agent Collaboration Memory

This example simulates three AI agents collaborating on a software project.
Each agent maintains its own isolated memory (via group_id), while a shared
group enables cross-agent knowledge sharing.

Key concepts demonstrated:
  1. Per-agent isolated memory using distinct group_ids
  2. A shared group_id for cross-agent knowledge exchange
  3. Fact provenance: which agent contributed which fact
  4. Contradiction handling when agents disagree
  5. Cross-agent querying across shared and private memory
  6. Temporal ordering of agent contributions

Agent roles:
  - Agent A (Architect): Makes design decisions about the system
  - Agent B (Developer): Implements features, discovers issues
  - Agent C (QA): Tests features, reports bugs

Domain: Building a fictional "QuantumCart" e-commerce platform.
"""

import asyncio
import os
import sys

from datetime import datetime, timezone, timedelta
from textwrap import dedent

# ---------------------------------------------------------------------------
# Environment / connectivity check
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY is not set. Graphiti uses an LLM to extract "
        "entities and relationships. Without it, extraction will fail.\n"
        "Set it via:  export OPENAI_API_KEY='sk-...'  (Linux/Mac)\n"
        "or:          $env:OPENAI_API_KEY='sk-...'   (Windows PowerShell)\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
    import socket

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


def print_edges(edges, heading: str = ""):
    """Pretty-print a list of edges with temporal metadata."""
    if heading:
        print(f"\n  --- {heading} ---")
    if not edges:
        print("  (no results)")
        return
    for i, e in enumerate(edges, 1):
        print(f"  [{i}] fact:     {e.fact}")
        print(f"      source:   {e.source_node_name} --> {e.target_node_name}")
        if hasattr(e, 'group_id') and e.group_id:
            print(f"      group:    {e.group_id}")
        if e.valid_at:
            print(f"      valid at: {e.valid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        if e.invalid_at:
            print(f"      expired:  {e.invalid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()


# ===================================================================
# Helper: add an episode attributed to a specific agent
# ===================================================================
async def agent_says(
    graphiti,
    agent_name: str,
    agent_group: str,
    shared_group: str,
    episode_name: str,
    message: str,
    reference_time: datetime,
):
    """
    Add an episode attributed to a specific agent. The episode is added to
    both the agent's private group (isolated memory) and the shared group
    (cross-agent knowledge).

    Using EpisodeType.message ensures the speaker is attributed as an entity.
    """
    from graphiti_core.nodes import EpisodeType

    # Agent's private memory
    ep_private = await graphiti.add_episode(
        name=f"{episode_name}_private",
        episode_body=dedent(f"{agent_name}: {message}"),
        source=EpisodeType.message,
        source_description=f"Private memory for {agent_name}",
        reference_time=reference_time,
        group_id=agent_group,
    )

    # Shared cross-agent memory
    ep_shared = await graphiti.add_episode(
        name=f"{episode_name}_shared",
        episode_body=dedent(f"{agent_name}: {message}"),
        source=EpisodeType.message,
        source_description=f"Shared cross-agent memory",
        reference_time=reference_time,
        group_id=shared_group,
    )

    print(f"  [{reference_time.strftime('%H:%M UTC')}] {agent_name}: "
          f"'{message[:70]}...' -> private & shared")
    return ep_private, ep_shared


# ===================================================================
# Simulation timeline
# ===================================================================
async def simulate_collaboration():
    """Add episodes representing the full agent collaboration timeline."""
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    # ---- Group IDs ----
    # Each agent has a private group for isolated memory
    group_architect = "agent_architect"
    group_developer = "agent_developer"
    group_qa = "agent_qa"
    # Shared group for cross-agent knowledge
    group_shared = "quantumcart_shared"

    base_time = datetime(2025, 6, 1, 8, 0, 0, tzinfo=timezone.utc)

    # ==================================================================
    # Phase 1: Architecture Design (Agent A)
    # ==================================================================
    print("\n" + "=" * 72)
    print("PHASE 1: Architecture Design (Agent A -- Architect)")
    print("=" * 72)

    t = base_time
    await agent_says(
        graphiti,
        "ArchitectAgent",
        group_architect,
        group_shared,
        "arch_decision_1",
        (
            "I have designed the system architecture for QuantumCart. "
            "The system will use a microservices architecture with 4 core services: "
            "ProductService, OrderService, PaymentService, and UserService. "
            "Communication will be via gRPC with protobuf serialization. "
            "PostgreSQL will be the primary database with Redis for caching. "
            "The system will handle 10K concurrent users at launch."
        ),
        t,
    )

    t += timedelta(minutes=5)
    await agent_says(
        graphiti,
        "ArchitectAgent",
        group_architect,
        group_shared,
        "arch_decision_2",
        (
            "Authentication will use OAuth 2.0 with JWT tokens. "
            "The token expiry is set to 24 hours. "
            "Refresh tokens will be valid for 7 days. "
            "We will use bcrypt for password hashing."
        ),
        t,
    )

    t += timedelta(minutes=3)
    await agent_says(
        graphiti,
        "ArchitectAgent",
        group_architect,
        group_shared,
        "arch_decision_3",
        (
            "The data model for ProductService includes: "
            "product_id (UUID), name, description, price (decimal), "
            "category, inventory_count, created_at, updated_at. "
            "All monetary values are stored in cents (integer) to avoid "
            "floating-point rounding issues."
        ),
        t,
    )

    # Architect's private note (only in private group)
    print(f"  [{t.strftime('%H:%M UTC')}] ArchitectAgent: "
          f"(private note about risk assessment)")
    await graphiti.add_episode(
        name="arch_private_risk",
        episode_body=dedent(
            "ArchitectAgent: I have concerns about the PaymentService "
            "scalability under peak load. The current design uses synchronous "
            "gRPC calls which may become a bottleneck during Black Friday sales. "
            "I should discuss this with the team later."
        ),
        source=EpisodeType.message,
        source_description="Private risk assessment",
        reference_time=t,
        group_id=group_architect,
    )

    # ==================================================================
    # Phase 2: Development (Agent B)
    # ==================================================================
    print("\n" + "=" * 72)
    print("PHASE 2: Development (Agent B -- Developer)")
    print("=" * 72)

    t += timedelta(hours=2)

    await agent_says(
        graphiti,
        "DeveloperAgent",
        group_developer,
        group_shared,
        "dev_impl_1",
        (
            "I implemented the ProductService according to the architecture spec. "
            "The service handles CRUD operations for products. "
            "I used FastAPI with async SQLAlchemy for the PostgreSQL connection. "
            "The gRPC endpoints return protobuf messages as specified."
        ),
        t,
    )

    t += timedelta(minutes=45)
    await agent_says(
        graphiti,
        "DeveloperAgent",
        group_developer,
        group_shared,
        "dev_impl_issue",
        (
            "I found an issue during implementation. The gRPC communication "
            "between ProductService and InventoryService causes high latency "
            "under load testing -- around 500ms per call. "
            "I think we should switch to async message queues (RabbitMQ) "
            "for inter-service communication instead of synchronous gRPC. "
            "This contradicts the original architecture decision."
        ),
        t,
    )

    t += timedelta(minutes=30)
    await agent_says(
        graphiti,
        "DeveloperAgent",
        group_developer,
        group_shared,
        "dev_impl_2",
        (
            "I implemented the UserService with OAuth 2.0 authentication. "
            "However, I found that JWT tokens with 24-hour expiry are a "
            "security concern. Industry best practice is 15-60 minutes for "
            "access tokens. I changed the token expiry to 30 minutes and "
            "extended refresh token validity to 30 days instead of 7."
        ),
        t,
    )

    # Developer's private note
    print(f"  [{t.strftime('%H:%M UTC')}] DeveloperAgent: "
          f"(private note about technical debt)")
    await graphiti.add_episode(
        name="dev_private_debt",
        episode_body=dedent(
            "DeveloperAgent: The ProductService implementation has some "
            "technical debt. The test coverage is only 60%. I need to go "
            "back and add unit tests for the edge cases in the pricing logic. "
            "Also, the database migration scripts need better error handling."
        ),
        source=EpisodeType.message,
        source_description="Private technical debt note",
        reference_time=t,
        group_id=group_developer,
    )

    # ==================================================================
    # Phase 3: QA Testing (Agent C) -- Discovers bugs
    # ==================================================================
    print("\n" + "=" * 72)
    print("PHASE 3: QA Testing (Agent C -- Quality Assurance)")
    print("=" * 72)

    t += timedelta(hours=3)

    await agent_says(
        graphiti,
        "QAAgent",
        group_qa,
        group_shared,
        "qa_test_1",
        (
            "I completed integration testing of the ProductService. "
            "The basic CRUD operations pass. However, I found a critical bug: "
            "the inventory count goes negative when two concurrent orders "
            "request the same product simultaneously. This is a race condition "
            "in the inventory update logic."
        ),
        t,
    )

    t += timedelta(minutes=20)
    await agent_says(
        graphiti,
        "QAAgent",
        group_qa,
        group_shared,
        "qa_test_2",
        (
            "Load testing results: the system handles 8K concurrent users "
            "before response times exceed 2 seconds. This is below the 10K "
            "target specified by the architecture. The bottleneck is the "
            "synchronous gRPC calls between ProductService and InventoryService. "
            "I recommend using RabbitMQ for async communication."
        ),
        t,
    )

    t += timedelta(minutes=15)
    await agent_says(
        graphiti,
        "QAAgent",
        group_qa,
        group_shared,
        "qa_test_3",
        (
            "Security audit: I found that the JWT token implementation is "
            "secure (30-minute expiry is appropriate). However, the password "
            "reset flow does not rate-limit requests -- this is a vulnerability "
            "to brute-force attacks on the reset token endpoint."
        ),
        t,
    )

    # QA's private note
    print(f"  [{t.strftime('%H:%M UTC')}] QAAgent: "
          f"(private note about regression concerns)")
    await graphiti.add_episode(
        name="qa_private_regression",
        episode_body=dedent(
            "QAAgent: I notice the DeveloperAgent changed the JWT expiry "
            "from 24 hours to 30 minutes. I need to verify that all "
            "authentication flows still work correctly with this change. "
            "The refresh token mechanism needs particular attention."
        ),
        source=EpisodeType.message,
        source_description="Private regression concern",
        reference_time=t,
        group_id=group_qa,
    )

    # ==================================================================
    # Phase 4: Architect responds to Developer's contradiction
    # ==================================================================
    print("\n" + "=" * 72)
    print("PHASE 4: Architect Responds to Contradiction")
    print("=" * 72)

    t += timedelta(hours=1)

    await agent_says(
        graphiti,
        "ArchitectAgent",
        group_architect,
        group_shared,
        "arch_response_grpc",
        (
            "I reviewed the DeveloperAgent's finding about gRPC latency. "
            "After analysis, I agree that RabbitMQ is better for this use case. "
            "The architecture decision for synchronous gRPC is hereby revised. "
            "Updated design: use RabbitMQ for inter-service communication, "
            "keep gRPC only for external API gateway communication. "
            "This supersedes my earlier gRPC decision."
        ),
        t,
    )

    t += timedelta(minutes=10)
    await agent_says(
        graphiti,
        "ArchitectAgent",
        group_architect,
        group_shared,
        "arch_response_jwt",
        (
            "I approve the DeveloperAgent's change to JWT token expiry. "
            "30 minutes for access tokens and 30 days for refresh tokens "
            "is indeed better security practice than my original 24-hour proposal. "
            "The original authentication design is updated."
        ),
        t,
    )

    return graphiti, {
        "architect": group_architect,
        "developer": group_developer,
        "qa": group_qa,
        "shared": group_shared,
    }


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 23: Multi-Agent Collaboration Memory")
    print("Three AI agents collaborate on QuantumCart e-commerce platform")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start Neo4j via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    graphiti, groups = await simulate_collaboration()

    # ==================================================================
    # Demonstration 1: Isolated agent memory
    # ==================================================================
    print("\n" + "=" * 72)
    print("DEMONSTRATION 1: Isolated Agent Memory")
    print("=" * 72)
    print(
        "  Each agent has a private group_id. Queries scoped to that group\n"
        "  only return facts that agent contributed.\n"
    )

    for agent_name, group_id in [
        ("ArchitectAgent", groups["architect"]),
        ("DeveloperAgent", groups["developer"]),
        ("QAAgent", groups["qa"]),
    ]:
        edges = await graphiti.search(
            query="What did this agent contribute to the project?",
            group_ids=[group_id],
            num_results=5,
        )
        print(f"\n  >>> {agent_name}'s private memory (group: {group_id}):")
        print_edges(edges)

    # ==================================================================
    # Demonstration 2: Cross-agent querying via shared group
    # ==================================================================
    print("\n" + "=" * 72)
    print("DEMONSTRATION 2: Cross-Agent Querying via Shared Group")
    print("=" * 72)
    print(
        "  The shared group contains facts from ALL agents. This enables\n"
        "  a unified view of the project's knowledge.\n"
    )

    queries = [
        "What is the current architecture design for QuantumCart?",
        "What issues were discovered during development and testing?",
        "What security measures are in place for authentication?",
    ]

    for query in queries:
        print(f'\n  >>> Query: "{query}"')
        edges = await graphiti.search(
            query=query,
            group_ids=[groups["shared"]],
            num_results=8,
        )
        print_edges(edges)

    # ==================================================================
    # Demonstration 3: Fact provenance (who said what)
    # ==================================================================
    print("\n" + "=" * 72)
    print("DEMONSTRATION 3: Fact Provenance -- Who Said What")
    print("=" * 72)
    print(
        "  Since we use EpisodeType.message, each fact is attributed to its\n"
        "  speaker (agent name). The graph preserves provenance. Episodes from\n"
        "  different group_ids can be traced back to specific agents.\n"
    )

    # Query for contributions by a specific entity
    for agent_name in ["ArchitectAgent", "DeveloperAgent", "QAAgent"]:
        edges = await graphiti.search(
            query=f"What did {agent_name} contribute to the project?",
            group_ids=[groups["shared"]],
            num_results=4,
        )
        print(f"\n  >>> Facts from {agent_name} (in shared memory):")
        for i, e in enumerate(edges, 1):
            print(f"  [{i}] {e.fact}")

    # ==================================================================
    # Demonstration 4: Contradiction handling
    # ==================================================================
    print("\n" + "=" * 72)
    print("DEMONSTRATION 4: Contradiction Handling")
    print("=" * 72)
    print(
        "  The DeveloperAgent contradicted the ArchitectAgent's original design\n"
        "  decision about gRPC communication. The Architect later revised the\n"
        "  decision. Graphiti preserves both the original and revised facts with\n"
        "  temporal metadata.\n"
    )

    edges = await graphiti.search(
        query="How should services communicate in QuantumCart? gRPC vs message queues?",
        group_ids=[groups["shared"]],
        num_results=10,
    )
    print_edges(edges, "Communication architecture evolution")

    print(
        "  Notice: The original gRPC decision and the revised RabbitMQ decision\n"
        "  both exist in the graph. The original is marked with invalid_at\n"
        "  (it was superseded), while the revision is the current valid fact.\n"
    )

    # ==================================================================
    # Demonstration 5: Temporal ordering of agent contributions
    # ==================================================================
    print("\n" + "=" * 72)
    print("DEMONSTRATION 5: Temporal Ordering of Events")
    print("=" * 72)
    print(
        "  Because each fact has a valid_at timestamp, we can reconstruct the\n"
        "  entire timeline: Architect designed -> Developer implemented ->\n"
        "  QA tested -> Architect revised.\n"
    )

    edges = await graphiti.search(
        query="What is the complete timeline of decisions, implementations, and discoveries?",
        group_ids=[groups["shared"]],
        num_results=15,
    )
    print_edges(edges, "Full project timeline")

    # ==================================================================
    # Summary
    # ==================================================================
    print("=" * 72)
    print("Key Takeaways")
    print("=" * 72)
    print("""
  1. Per-agent isolation
     Each agent uses a private group_id for facts only they should see.
     This enables secure, partitioned memory for multi-agent systems.

  2. Shared knowledge
     A shared group_id enables cross-agent information exchange.
     All agents can contribute to and query from a common knowledge pool.

  3. Fact provenance
     EpisodeType.message preserves speaker attribution, so you can always
     trace which agent contributed which fact.

  4. Contradiction resolution
     When agents disagree (e.g., gRPC vs RabbitMQ), both viewpoints are
     preserved. The graph tracks when facts were superseded or reaffirmed.

  5. Temporal awareness
     Every fact carries timestamps, enabling full timeline reconstruction
     of decisions and their revisions.
""")

    # Clean up all groups
    print("\nCleaning up...")
    for group_name, group_id in groups.items():
        print(f"  Deleting group '{group_name}'...")
        await graphiti.delete_group(group_id=group_id)
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
