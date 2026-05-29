"""
Example 12: REST API Client Examples

Graphiti provides a REST API server (via FastAPI) for applications that need
to interact with the knowledge graph over HTTP rather than through the Python
SDK. This is useful when:

  - Your application is not written in Python
  - You want to decouple graph operations into a microservice
  - You need to expose graph capabilities to frontend applications
  - You want to use Graphiti in serverless or containerized environments

This example demonstrates:
  1. Starting the Graphiti REST API server
  2. POST /ingest/messages -- adding episodes via HTTP
  3. POST /ingest/entity-node -- creating entity nodes directly
  4. POST /retrieve/search -- searching via REST
  5. POST /retrieve/get-memory -- specialized memory retrieval
  6. DELETE /ingest/group/{group_id} -- cleanup

NOTE: This example requires the Graphiti REST server to be running.
Run it in a separate terminal with:
    python -m graphiti_core.rest_api.server

Or start it programmatically (shown below).
"""

import asyncio
import json
import os
import socket
import sys
import time
import uuid

from datetime import datetime, timezone
from typing import Optional

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Where the REST API server will listen
REST_API_HOST = "127.0.0.1"
REST_API_PORT = 8000
REST_API_BASE = f"http://{REST_API_HOST}:{REST_API_PORT}"

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY is not set. Graphiti uses an LLM to extract "
        "entities and relationships. Without it, extraction will fail.\n"
        "Set it via:  export OPENAI_API_KEY='sk-...'  (Linux / Mac)\n"
        "or:          $env:OPENAI_API_KEY='sk-...'   (Windows PowerShell)\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
    host, _, port_str = (
        NEO4J_URI.replace("bolt://", "")
        .replace("neo4j://", "")
        .partition(":")
    )
    try:
        port = int(port_str) if port_str else 7687
    except ValueError:
        port = 7687
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except (OSError, socket.timeout):
        return False


def check_rest_server() -> bool:
    """Return True if the REST API server appears reachable."""
    try:
        with socket.create_connection((REST_API_HOST, REST_API_PORT), timeout=3):
            return True
    except (OSError, socket.timeout):
        return False


def section(title: str):
    print(f"\n{'=' * 72}")
    print(f"  {title}")
    print(f"{'=' * 72}\n")


async def main():
    print("=" * 72)
    print("Example 12: REST API Client Examples")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  To run this example, start a Neo4j instance:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    section("Step 1: Checking / Starting the REST API server")

    if check_rest_server():
        print(f"  REST API server is reachable at {REST_API_BASE}")
    else:
        print(
            f"  REST API server is NOT reachable at {REST_API_BASE}\n"
            f"  This example requires the Graphiti REST server running.\n"
            f"  Start it in another terminal with:\n"
            f"    python -m graphiti_core.rest_api.server\n"
            f"  Or via uvicorn:\n"
            f"    uvicorn graphiti_core.rest_api.server:app --host 0.0.0.0 --port 8000\n"
            f"\n"
            f"  Attempting to start a demonstration using the Python SDK directly\n"
            f"  to simulate what the REST API would do...\n"
        )
        # Fall back to SDK-based demonstration
        await run_sdk_demonstration()
        return

    # If the REST server is running, make actual HTTP calls
    await run_rest_api_demonstration()


# ---------------------------------------------------------------------------
# SDK-based demonstration (fallback when REST server is not running)
# ---------------------------------------------------------------------------
async def run_sdk_demonstration():
    """Demonstrate equivalent operations using the Python SDK."""

    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    graphiti = Graphiti(
        uri=NEO4J_URI,
        user=NEO4J_USER,
        password=NEO4J_PASSWORD,
    )
    await graphiti.build_indices_and_constraints()

    group_id = "rest_api_demo"
    now = datetime.now(timezone.utc)

    section("Simulating POST /ingest/messages (add episode)")

    print("  --- Adding episode about Acme Corp ---")
    ep = await graphiti.add_episode(
        name="acme_overview",
        episode_body=(
            "Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco. "
            "Acme builds AI-powered supply chain optimization software. "
            "Their product RouteOptimizer Pro reduces delivery costs by up to 35%."
        ),
        source=EpisodeType.text,
        source_description="Company profile",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Episode added: {ep.name} (uuid: {ep.uuid[:8]}...)")
    print(f"  Endpoint equivalent: POST {REST_API_BASE}/ingest/messages")
    print(f"  Body: {{ \"name\": \"...\", \"episode_body\": \"...\", \"group_id\": \"...\" }}")
    print()

    print("  --- Adding a second episode ---")
    ep2 = await graphiti.add_episode(
        name="funding_round",
        episode_body=(
            "Acme Corp raised $30M Series B in 2024 from VentureCap Partners. "
            "David Park from VentureCap joined the board."
        ),
        source=EpisodeType.text,
        source_description="Press release",
        reference_time=now,
        group_id=group_id,
    )
    print(f"  Episode added: {ep2.name} (uuid: {ep2.uuid[:8]}...)")

    section("Simulating POST /retrieve/search (search the graph)")

    print('  Query: "What does Acme Corp do?"')
    edges = await graphiti.search(
        query="What does Acme Corp do?",
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Found {len(edges)} edge(s):")
    for edge in edges:
        print(f"    - {edge.fact}")
    print()
    print("  Endpoint equivalent: POST /retrieve/search")
    print("  Body: { \"query\": \"...\", \"group_ids\": [...], \"num_results\": 5 }")

    section("Simulating POST /retrieve/get-memory (memory retrieval)")

    print('  Query: "Tell me about Acme leadership"')
    memory_results = await graphiti.search_(
        query="Tell me about Acme leadership",
        group_ids=[group_id],
        num_results=5,
    )
    print(f"  Got {len(memory_results.edges)} facts, {len(memory_results.nodes)} entities")
    for edge in memory_results.edges[:3]:
        print(f"    - {edge.fact}")
    print()
    print("  /retrieve/get-memory returns a structured memory response")
    print("  combining relevant edges and nodes for conversational context.")

    section("Simulating DELETE /ingest/group/{group_id} (cleanup)")

    print(f"  Deleting group: {group_id}")
    print(f"  Endpoint equivalent: DELETE /ingest/group/{group_id}")
    await graphiti.delete_group(group_id=group_id)
    print("  Group deleted successfully.")

    section("REST API Reference (quick summary)")

    print(
        "  Endpoint                             Method  Description\n"
        "  -----------------------------------  ------  ------------------------------\n"
        "  /ingest/messages                     POST    Add an episode for extraction\n"
        "  /ingest/entity-node                  POST    Create an entity node directly\n"
        "  /retrieve/search                     POST    Search the knowledge graph\n"
        "  /retrieve/get-memory                 POST    Get memory context for an agent\n"
        "  /ingest/group/{group_id}            DELETE  Remove all data for a group\n"
        "  /health                              GET     Server health check\n"
        "  /                                    GET     Server info / documentation\n"
    )

    await graphiti.close()
    print("Done.")


# ---------------------------------------------------------------------------
# REST API demonstration (actual HTTP calls when server is running)
# ---------------------------------------------------------------------------
async def run_rest_api_demonstration():
    """Make real HTTP requests to the Graphiti REST API."""

    try:
        import httpx
    except ImportError:
        print(
            "  The httpx library is required for REST API calls.\n"
            "  Install it with: pip install httpx\n"
            "  Falling back to SDK demonstration...\n"
        )
        await run_sdk_demonstration()
        return

    group_id = f"rest_api_demo_{uuid.uuid4().hex[:8]}"

    async with httpx.AsyncClient(base_url=REST_API_BASE, timeout=30) as client:

        # ---- Health check --------------------------------------------------
        section("GET /health -- server status")
        try:
            response = await client.get("/health")
            print(f"  Status: {response.status_code}")
            print(f"  Response: {response.json()}")
        except Exception as e:
            print(f"  Health check failed: {e}")
            return

        # ---- Ingest messages -----------------------------------------------
        section("POST /ingest/messages -- adding episodes")

        messages = [
            {
                "name": "acme_overview",
                "episode_body": (
                    "Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco. "
                    "Acme builds AI-powered supply chain optimization software. "
                    "Their product RouteOptimizer Pro reduces delivery costs by up to 35%."
                ),
                "group_id": group_id,
            },
            {
                "name": "funding_round",
                "episode_body": (
                    "Acme Corp raised $30M Series B in 2024 from VentureCap Partners. "
                    "David Park from VentureCap joined the board of directors."
                ),
                "group_id": group_id,
            },
            {
                "name": "team",
                "episode_body": (
                    "James Miller is VP of Engineering at Acme Corp. "
                    "Maria Gonzalez is Regional Director of the Austin office. "
                    "Both report to CEO Sarah Chen."
                ),
                "group_id": group_id,
            },
        ]

        for msg in messages:
            print(f'  Adding episode: {msg["name"]}')
            response = await client.post("/ingest/messages", json=msg)
            print(f"    Status: {response.status_code}")
            data = response.json()
            if response.is_success:
                print(f"    Episode UUID: {data.get('episode_uuid', 'N/A')[:8]}...")
            else:
                print(f"    Error: {data}")
            print()

        # ---- Search --------------------------------------------------------
        section("POST /retrieve/search -- searching the graph")

        search_payloads = [
            {
                "query": "Who founded Acme Corp?",
                "group_ids": [group_id],
                "num_results": 5,
            },
            {
                "query": "Acme Corp funding and investors",
                "group_ids": [group_id],
                "num_results": 5,
            },
        ]

        for payload in search_payloads:
            print(f'  Query: "{payload["query"]}"')
            response = await client.post("/retrieve/search", json=payload)
            if response.is_success:
                data = response.json()
                edges = data.get("edges", [])
                print(f"  Found {len(edges)} edge(s):")
                for edge in edges[:3]:
                    print(f"    - {edge.get('fact', 'N/A')}")
            else:
                print(f"  Error: {response.text}")
            print()

        # ---- Get Memory (context for conversational agents) ---------------
        section("POST /retrieve/get-memory -- memory retrieval")

        memory_payload = {
            "query": "Tell me about Acme Corp leadership and funding",
            "group_ids": [group_id],
        }
        print(f'  Query: "{memory_payload["query"]}"')
        response = await client.post("/retrieve/get-memory", json=memory_payload)
        if response.is_success:
            data = response.json()
            print(f"  Memory context returned: {json.dumps(data, indent=2)[:500]}...")
        else:
            print(f"  Error: {response.text}")

        # ---- Create entity node directly -----------------------------------
        section("POST /ingest/entity-node -- direct entity creation")

        entity_payload = {
            "name": "CustomProjectX",
            "group_id": group_id,
            "label": "Project",
            "summary": "A special project mentioned outside of episode extraction",
        }
        print(f'  Creating entity: {entity_payload["name"]}')
        response = await client.post("/ingest/entity-node", json=entity_payload)
        if response.is_success:
            data = response.json()
            print(f"  Entity UUID: {data.get('entity_uuid', 'N/A')[:8]}...")
        else:
            print(f"  Error: {response.text}")

        # ---- Cleanup -------------------------------------------------------
        section(f"DELETE /ingest/group/{group_id} -- cleanup")

        print(f"  Deleting all data for group: {group_id}")
        response = await client.delete(f"/ingest/group/{group_id}")
        if response.is_success:
            print(f"  Group deleted successfully.")
        else:
            print(f"  Error: {response.text}")

    section("Authentication patterns")

    print(
        "  The Graphiti REST API supports several authentication patterns:\n"
        "  1. No auth (development): Run on localhost, no auth headers\n"
        "  2. API Key header: Pass an API key via X-API-Key header\n"
        "      headers = { 'X-API-Key': 'your-api-key' }\n"
        "  3. Bearer token: Pass a JWT or token via Authorization header\n"
        "      headers = { 'Authorization': 'Bearer <token>' }\n"
        "  4. Environment-based: Configure auth via server environment variables\n"
        "\n"
        "  Example of passing auth headers with httpx:\n"
        "    client = httpx.AsyncClient(\n"
        "        base_url='http://localhost:8000',\n"
        "        headers={'X-API-Key': 'my-secret-key'},\n"
        "        timeout=30,\n"
        "    )\n"
    )

    print("Done with REST API example.")


if __name__ == "__main__":
    asyncio.run(main())
