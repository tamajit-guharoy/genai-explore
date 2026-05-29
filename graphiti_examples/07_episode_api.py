"""
Example 07: Episode API -- Comprehensive Reference

This example is a deep-dive into Graphiti's episode API, covering every major
operation related to episode management:

  1. add_episode()             -- Ingest a single episode with full parameters
  2. add_episode_bulk()        -- Batch-ingest multiple episodes efficiently
  3. group_id isolation        -- Episodes in different groups are isolated
  4. reference_time            -- Temporal anchoring of episodes
  5. retrieve_episodes()       -- Read back episodes from the graph
  6. remove_episode()          -- Delete an episode and its extracted data
  7. Queue system behavior     -- Episodes are processed sequentially per
                                 group_id (order-preserving per group)

All examples use Acme Corp's customer support team as the narrative thread.
"""

import asyncio
import os
import sys
import time

from datetime import datetime, timezone, timedelta

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
    """Pretty-print a list of edges."""
    if heading:
        print(f"\n  --- {heading} ---")
    if not edges:
        print("  (no results)")
        return
    for i, e in enumerate(edges, 1):
        print(f"  [{i}] {e.fact}")
        print(f"      {e.source_node_name} --> {e.target_node_name}")
        if e.valid_at:
            print(f"      valid at: {e.valid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()


# ===================================================================
#  Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 07: Episode API -- Comprehensive Reference")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start Neo4j via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    now = datetime.now(timezone.utc)

    # ==================================================================
    # 1. add_episode() -- Single episode with all parameters
    # ==================================================================
    print("\n" + "=" * 60)
    print("1. add_episode() -- Single episode, full parameter reference")
    print("=" * 60)

    ep = await graphiti.add_episode(
        # name: A unique identifier for this episode
        name="ep_api_single",

        # episode_body: The text content to be extracted.
        episode_body=(
            "Acme Corp's support team handled 1,200 tickets this week. "
            "Top agent Priya Sharma resolved 150 tickets. "
            "The most common issue was 'login timeout' at 35% of tickets."
        ),

        # source: One of EpisodeType.text / .message / .json / .fact_triple
        source=EpisodeType.text,

        # source_description: Human-readable description of where this data
        # came from. Stored as metadata on the episode node.
        source_description="Weekly support metrics from Zendesk",

        # reference_time: When this episode occurred in the real world.
        # Used for temporal anchoring of extracted facts.
        reference_time=now - timedelta(days=7),

        # group_id: Logical namespace for grouping episodes. Episodes in
        # different groups are isolated during search.
        group_id="ep_api_demo",
    )

    print(f"\n  Created episode:")
    print(f"    name:              {ep.name}")
    print(f"    uuid:              {ep.uuid}")
    print(f"    source:            {ep.source}")
    print(f"    source_description: {ep.source_description}")
    print(f"    reference_time:    {ep.reference_time.strftime('%Y-%m-%d %H:%M UTC')}")
    print(f"    group_id:          {ep.group_id}")
    print(f"    created_at:        {ep.created_at.strftime('%Y-%m-%d %H:%M UTC')}")

    # ==================================================================
    # 2. add_episode_bulk() -- Batch processing
    # ==================================================================
    print("\n" + "=" * 60)
    print("2. add_episode_bulk() -- Batch ingest multiple episodes")
    print("=" * 60)
    print(
        "  More efficient than calling add_episode() in a loop because\n"
        "  episodes are processed concurrently (up to max_coroutines).\n"
    )

    batch_episodes = [
        {
            "name": "ep_bulk_1",
            "episode_body": (
                "New support agent Carlos Mendez joined the Acme Corp support "
                "team this week. He handled 45 tickets under supervision."
            ),
            "source": EpisodeType.text,
            "source_description": "New hire report",
            "reference_time": now - timedelta(days=1),
            "group_id": "ep_api_demo",
        },
        {
            "name": "ep_bulk_2",
            "episode_body": (
                "Acme Corp launched a new AI chatbot for customer support. "
                "It handled 800 tickets in its first week with 92% satisfaction. "
                "Priya Sharma trained the chatbot's response model."
            ),
            "source": EpisodeType.text,
            "source_description": "Product launch report",
            "reference_time": now,
            "group_id": "ep_api_demo",
        },
        {
            "name": "ep_bulk_3",
            "episode_body": (
                "Customer satisfaction score dropped to 4.2 this month. "
                "The main complaint was slow response times during peak hours. "
                "Carlos Mendez suggested adding a callback feature."
            ),
            "source": EpisodeType.text,
            "source_description": "Monthly CSAT report",
            "reference_time": now,
            "group_id": "ep_api_demo",
        },
    ]

    bulk_results = await graphiti.add_episode_bulk(batch_episodes)
    print(f"\n  Bulk-added {len(bulk_results)} episodes:")
    for ep in bulk_results:
        print(f"    - {ep.name:20s}  uuid: {ep.uuid}")

    # ==================================================================
    # 3. group_id isolation
    # ==================================================================
    print("\n" + "=" * 60)
    print("3. group_id Isolation -- Episodes are namespaced")
    print("=" * 60)
    print(
        "  Episodes in different group_ids are isolated. Searching within\n"
        "  one group won't return facts from another.\n"
    )

    # Create episodes in two different groups
    await graphiti.add_episode(
        name="group_a_ep",
        episode_body=(
            "Acme Corp group A is working on the mobile app redesign. "
            "The team lead is Alice Zhang."
        ),
        source=EpisodeType.text,
        source_description="Group A standup",
        reference_time=now,
        group_id="group_a",
    )

    await graphiti.add_episode(
        name="group_b_ep",
        episode_body=(
            "Acme Corp group B is building the analytics dashboard. "
            "The team lead is James Miller."
        ),
        source=EpisodeType.text,
        source_description="Group B standup",
        reference_time=now,
        group_id="group_b",
    )

    # Search group A -- should only find Alice Zhang, not James Miller
    edges_a = await graphiti.search(
        query="Who is the team lead?",
        group_ids=["group_a"],
        num_results=5,
    )
    print_edges(edges_a, "Searching group 'group_a' (should show Alice Zhang)")

    # Search group B -- should only find James Miller
    edges_b = await graphiti.search(
        query="Who is the team lead?",
        group_ids=["group_b"],
        num_results=5,
    )
    print_edges(edges_b, "Searching group 'group_b' (should show James Miller)")

    # Search both -- should find both
    edges_both = await graphiti.search(
        query="Who is the team lead?",
        group_ids=["group_a", "group_b"],
        num_results=5,
    )
    print_edges(edges_both, "Searching BOTH groups (should show both leads)")

    # ==================================================================
    # 4. reference_time -- Temporal anchoring
    # ==================================================================
    print("\n" + "=" * 60)
    print("4. reference_time -- Temporal anchoring")
    print("=" * 60)
    print(
        "  reference_time tells Graphiti WHEN the episode occurred in the\n"
        "  real world. Facts extracted from the episode get valid_at set to\n"
        "  this time. This is essential for the bi-temporal model.\n"
    )

    yesterday = now - timedelta(days=1)
    last_month = now - timedelta(days=30)
    last_year = now - timedelta(days=365)

    await graphiti.add_episode(
        name="temp_anchor_last_year",
        episode_body=(
            "Acme Corp had 50 employees and was operating only in San Francisco."
        ),
        source=EpisodeType.text,
        source_description="Old company profile",
        reference_time=last_year,
        group_id="ep_api_demo",
    )

    await graphiti.add_episode(
        name="temp_anchor_last_month",
        episode_body=(
            "Acme Corp has 200 employees. Offices in San Francisco and Austin."
        ),
        source=EpisodeType.text,
        source_description="Recent company profile",
        reference_time=last_month,
        group_id="ep_api_demo",
    )

    await graphiti.add_episode(
        name="temp_anchor_yesterday",
        episode_body=(
            "Acme Corp now has 350 employees. New office in New York opened."
        ),
        source=EpisodeType.text,
        source_description="Today's update",
        reference_time=yesterday,
        group_id="ep_api_demo",
    )

    print("  Added 3 episodes with different reference_times:\n"
          "    - 1 year ago:    50 employees, SF only\n"
          "    - 1 month ago:   200 employees, SF + Austin\n"
          "    - yesterday:     350 employees, SF + Austin + NY\n")

    edges_employees = await graphiti.search(
        query="How many employees does Acme Corp have?",
        group_ids=["ep_api_demo"],
        num_results=10,
    )
    print_edges(edges_employees,
                "Employee count facts (notice the valid_at timestamps differ)")

    # ==================================================================
    # 5. retrieve_episodes() -- Read back episodes
    # ==================================================================
    print("\n" + "=" * 60)
    print("5. retrieve_episodes() -- Reading episodes from the graph")
    print("=" * 60)

    # Retrieve episodes from the main demo group
    retrieved = await graphiti.retrieve_episodes(group_ids=["ep_api_demo"])
    print(f"\n  Retrieved {len(retrieved)} episode(s) from 'ep_api_demo':")
    for ep in retrieved:
        print(f"    - name={ep.name:25s}  source={ep.source.name:10s}  "
              f"created={ep.created_at.strftime('%m/%d %H:%M')}")

    # Retrieve from group_a
    retrieved_a = await graphiti.retrieve_episodes(group_ids=["group_a"])
    print(f"\n  Retrieved {len(retrieved_a)} episode(s) from 'group_a':")
    for ep in retrieved_a:
        print(f"    - {ep.name}")

    # ==================================================================
    # 6. remove_episode() -- Delete episodes
    # ==================================================================
    print("\n" + "=" * 60)
    print("6. remove_episode() -- Deleting episodes and their data")
    print("=" * 60)
    print(
        "  Removing an episode also removes all entity edges (relationships)\n"
        "  that were extracted from that episode. Entity nodes that are only\n"
        "  connected to this episode may also be cleaned up.\n"
    )

    # First, let's count episodes in group 'group_a'
    eps_before = await graphiti.retrieve_episodes(group_ids=["group_a"])
    print(f"\n  Episodes in 'group_a' before removal: {len(eps_before)}")

    if eps_before:
        target = eps_before[0]
        print(f"  Removing episode: '{target.name}' (uuid: {target.uuid})")

        # Search before removal to confirm we find facts
        before_search = await graphiti.search(
            query="mobile app redesign",
            group_ids=["group_a"],
            num_results=5,
        )
        print(f"  Search results BEFORE removal: {len(before_search)} edge(s)")

        # Remove the episode
        await graphiti.remove_episode(target.uuid)
        print("  Remove operation completed.")

        # Verify removal
        eps_after = await graphiti.retrieve_episodes(group_ids=["group_a"])
        print(f"  Episodes in 'group_a' after removal: {len(eps_after)}")

        after_search = await graphiti.search(
            query="mobile app redesign",
            group_ids=["group_a"],
            num_results=5,
        )
        print(f"  Search results AFTER removal: {len(after_search)} edge(s)")
        print("  (Facts extracted from the removed episode should be gone.)")

    # ==================================================================
    # 7. Queue system behavior
    # ==================================================================
    print("\n" + "=" * 60)
    print("7. Queue System -- Sequential processing per group_id")
    print("=" * 60)
    print(
        "  Graphiti processes episodes sequentially within the same group_id.\n"
        "  This ensures temporal ordering: facts from episode 1 are in the\n"
        "  graph before episode 2's extraction runs. This matters because\n"
        "  episode 2 might reference entities introduced in episode 1.\n"
        "\n"
        "  Across different group_ids, episodes can be processed concurrently.\n"
    )

    print("  Timeline of sequential processing (single group):")
    print("""
    Time ──────────────────────────────────────────────>
          │              │              │
    Episode 1 added ──> Pipeline runs ──> Entities/edges written to graph
          │                             │              │
          │                    Episode 2 added ──> Pipeline runs
          │                                            │
          │                                   Episode 3 queued (waits for ep2)
          │                                            │
          │                                   Pipeline runs for ep3
    """)

    print(
        "  This is transparent to the caller: add_episode() returns once the\n"
        "  pipeline has completed for that episode. add_episode_bulk() queues\n"
        "  all episodes and waits for all of them to complete.\n"
    )

    # ==================================================================
    # Summary
    # ==================================================================
    print("=" * 60)
    print("Episode API Reference Summary")
    print("=" * 60)
    print("""
  Method                   Description
  -----------------------  ------------------------------------------------
  add_episode()            Ingest a single episode (name, body, source,
                            source_description, reference_time, group_id)

  add_episode_bulk()       Batch-ingest multiple episodes (list of dicts)

  retrieve_episodes()      Read back episodes (by group_ids)

  remove_episode()         Delete an episode + its extracted edges

  Key parameters:
    - group_id:            Namespace for isolation
    - reference_time:      Temporal anchor for facts
    - source:              EpisodeType (text / message / json / fact_triple)
    - source_description:  Human-readable provenance

  Queue behavior:
    - Sequential per group_id (ordered processing)
    - Concurrent across group_ids
""")

    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
