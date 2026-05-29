"""
Example 16: Alternative Graph Database Backends

Graphiti supports multiple graph database backends. While Neo4j is the default
and most feature-rich option, you can also use FalkorDB or Kuzu depending on
your deployment constraints.

Database Comparison:

  | Feature              | Neo4j               | FalkorDB          | Kuzu              |
  |----------------------|---------------------|-------------------|-------------------|
  | Type                 | Server (Java)       | Server (Redis)    | Embedded (C++)    |
  | Setup                | Docker / Cloud      | Docker            | pip install       |
  | External dependency  | Yes (Java VM)       | Yes (Redis)       | No (in-process)   |
  | Data persistence     | Full                | Optional (RDB)    | File-based        |
  | Query language       | Cypher              | Cypher-subset     | Cypher-subset     |
  | Best for             | Production, scale   | Low-latency       | Dev, testing, CI  |
  | License              | Source-available    | Redis-based       | MIT               |

When to use which:

  - **Neo4j**: Production deployments, complex graph queries, full ACID,
    large-scale graphs. The recommended default.

  - **FalkorDB**: When you need ultra-low-latency graph operations and
    are already running Redis. Good for real-time applications.

  - **Kuzu**: Development, testing, CI/CD pipelines, and single-machine
    deployments. No external server needed -- ideal for tutorials!
"""

import asyncio
import os
import socket
import sys

from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Environment variables -- only Neo4j vars are load-bearing for initial check
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

FALKORDB_URL = os.getenv("FALKORDB_URL", "redis://localhost:6379")

# Kuzu stores its database as a local directory
KUZU_DB_PATH = os.getenv("KUZU_DB_PATH", "./kuzu_graphiti_db")


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


def check_falkordb_connection() -> bool:
    """Return True if FalkorDB (Redis) appears reachable."""
    host, _, port_str = FALKORDB_URL.replace("redis://", "").partition(":")
    try:
        port = int(port_str) if port_str else 6379
    except ValueError:
        port = 6379
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except (OSError, socket.timeout):
        return False


# ===================================================================
# Setup instructions (shown at runtime)
# ===================================================================
SETUP_INSTRUCTIONS = """
=== BACKEND SETUP INSTRUCTIONS ===

Neo4j (recommended for production):
  docker run --rm \\
    --name neo4j \\
    -p 7687:7687 -p 7474:7474 \\
    -e NEO4J_AUTH=neo4j/password \\
    neo4j:5

FalkorDB (for low-latency use cases):
  docker run --rm \\
    --name falkordb \\
    -p 6379:6379 \\
    falkordb/falkordb:latest

Kuzu (for development/testing -- no external server needed!):
  pip install kuzu
  The database is created automatically as a local file.
"""


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 16: Alternative Graph Database Backends")
    print("=" * 72)
    print(SETUP_INSTRUCTIONS)

    if not OPENAI_API_KEY:
        print(
            "NOTE: OPENAI_API_KEY is not set. Graphiti needs an LLM for extraction.\n"
            "Set it with:  $env:OPENAI_API_KEY='sk-...'  (Windows)\n"
            "or:           export OPENAI_API_KEY='sk-...'   (Mac/Linux)\n"
        )

    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    now = datetime.now(timezone.utc)

    # Data that we will add to each backend (same data, same group_id)
    # This demonstrates that the same code works across backends.
    episodes = [
        {
            "name": "acme_founding",
            "body": (
                "Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco. "
                "The company uses AI to optimize supply chain logistics."
            ),
        },
        {
            "name": "acme_product",
            "body": (
                "Acme Corp's flagship product RouteOptimizer Pro uses machine learning "
                "to reduce delivery costs by up to 35%."
            ),
        },
        {
            "name": "acme_customers",
            "body": (
                "Acme Corp serves GlobalFreight Inc and QuickShip Logistics. "
                "Both companies use RouteOptimizer Pro for fleet management."
            ),
        },
    ]

    # ------------------------------------------------------------------
    # 1. Neo4j backend
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("1. Neo4j Backend (default, production-grade)")
    print("=" * 72)

    neo4j_available = check_neo4j_connection()
    if not neo4j_available:
        print(
            f"  [SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start it with:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        neo4j_graphiti = None
    else:
        neo4j_graphiti = Graphiti(
            uri=NEO4J_URI,
            user=NEO4J_USER,
            password=NEO4J_PASSWORD,
        )
        await neo4j_graphiti.build_indices_and_constraints()

        for ep in episodes:
            await neo4j_graphiti.add_episode(
                name=ep["name"],
                episode_body=ep["body"],
                source="text",
                source_description="Neo4j backend demo",
                reference_time=now,
                group_id="backend_neo4j",
            )
        print("  Added 3 episodes to Neo4j backend.")

    # ------------------------------------------------------------------
    # 2. FalkorDB backend
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("2. FalkorDB Backend (low-latency, Redis-based)")
    print("=" * 72)

    falkordb_available = check_falkordb_connection()
    if not falkordb_available:
        print(
            f"  [SKIP] Cannot reach FalkorDB at {FALKORDB_URL}\n"
            f"  Start it with:\n"
            f"    docker run --rm -p 6379:6379 falkordb/falkordb:latest\n"
        )
        falkordb_graphiti = None
    else:
        falkordb_graphiti = Graphiti(
            uri=FALKORDB_URL,
            user="",  # FalkorDB typically doesn't need auth
            password="",
        )
        await falkordb_graphiti.build_indices_and_constraints()

        for ep in episodes:
            await falkordb_graphiti.add_episode(
                name=ep["name"],
                episode_body=ep["body"],
                source="text",
                source_description="FalkorDB backend demo",
                reference_time=now,
                group_id="backend_falkordb",
            )
        print("  Added 3 episodes to FalkorDB backend.")

    # ------------------------------------------------------------------
    # 3. Kuzu embedded backend
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("3. Kuzu Backend (embedded, no external server needed!)")
    print("=" * 72)

    try:
        import kuzu
    except ImportError:
        print("  [SKIP] kuzu is not installed.")
        print("  Install it with:  pip install kuzu\n")
        print("  Kuzu is an embedded graph database that stores data in a local")
        print("  file. No server process needed -- perfect for development, CI,")
        print("  and single-machine deployments.")
        kuzu_graphiti = None
    else:
        # Kuzu stores the database to a local directory. Clean up any previous
        # run so we start fresh.
        import shutil

        if os.path.exists(KUZU_DB_PATH):
            shutil.rmtree(KUZU_DB_PATH)

        kuzu_graphiti = Graphiti(
            uri=KUZU_DB_PATH,
            user="",
            password="",
        )
        await kuzu_graphiti.build_indices_and_constraints()

        for ep in episodes:
            await kuzu_graphiti.add_episode(
                name=ep["name"],
                episode_body=ep["body"],
                source="text",
                source_description="Kuzu backend demo",
                reference_time=now,
                group_id="backend_kuzu",
            )
        print("  Added 3 episodes to Kuzu embedded backend.")
        print(f"  Database stored at: {os.path.abspath(KUZU_DB_PATH)}")

    # ------------------------------------------------------------------
    # Query across all available backends
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Querying all available backends")
    print("=" * 72)

    query = "Who founded Acme Corp and what products do they offer?"

    backends = [
        ("Neo4j", neo4j_graphiti, "backend_neo4j"),
        ("FalkorDB", falkordb_graphiti, "backend_falkordb"),
        ("Kuzu", kuzu_graphiti, "backend_kuzu"),
    ]

    for name, g, gid in backends:
        if g is None:
            continue
        print(f"\n  --- {name} ---")
        try:
            edges = await g.search(
                query=query,
                group_ids=[gid],
                num_results=3,
            )
            if edges:
                for edge in edges:
                    print(f"    {edge.source_node_name} --[{edge.fact}]--> {edge.target_node_name}")
            else:
                print("    (no results returned)")
        except Exception as e:
            print(f"    Error querying {name}: {e}")

    # ------------------------------------------------------------------
    # Summary: performance characteristics
    # ------------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Performance Characteristics Summary")
    print("=" * 72)

    print(
        "\n"
        "  Neo4j:\n"
        "    - Startup: ~5-15 seconds (Java VM)\n"
        "    - Query latency: ~10-50ms (warm)\n"
        "    - Max graph size: Billions of nodes\n"
        "    - Best for: Production, complex traversals\n"
        "\n"
        "  FalkorDB:\n"
        "    - Startup: ~1-2 seconds (Redis-based)\n"
        "    - Query latency: ~1-5ms (in-memory)\n"
        "    - Max graph size: RAM-bound\n"
        "    - Best for: Real-time, low-latency, caching layer\n"
        "\n"
        "  Kuzu:\n"
        "    - Startup: Instant (in-process)\n"
        "    - Query latency: ~2-10ms\n"
        "    - Max graph size: Disk-bound (columnar storage)\n"
        "    - Best for: Dev, testing, CI/CD, single-machine\n"
        "\n"
        "  NOTE: The same Graphiti code works on all three backends.\n"
        "  To switch backends, just change the URI/user/password passed\n"
        "  to the Graphiti constructor.\n"
    )

    # -- Cleanup ------------------------------------------------------------
    print("\n" + "=" * 72)
    print("Cleanup")
    print("=" * 72)

    for name, g in [
        ("Neo4j", neo4j_graphiti),
        ("FalkorDB", falkordb_graphiti),
        ("Kuzu", kuzu_graphiti),
    ]:
        if g is not None:
            await g.close()
            print(f"  Closed {name} connection.")

    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())
