"""
07_rest_api_client.py — Call Cognee via its REST API from Python.

This example demonstrates how to interact with a running Cognee API server
using HTTP requests. Useful when:
- Your main app is not Python
- Cognee runs as a separate service
- You want to isolate memory infrastructure from application code

Prerequisites:
    pip install cognee requests
    # Start the server first: cognee-cli -ui
    # Or: python -m cognee.api
"""

import asyncio
import time

import requests


class CogneeClient:
    """Minimal Cognee REST API client."""

    def __init__(self, base_url: str = "http://localhost:8000", api_key: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if api_key:
            self.session.headers["X-Api-Key"] = api_key
        # If using JWT instead, get a token first:
        # self.session.headers["Authorization"] = f"Bearer {token}"

    def add(self, data: str, dataset_name: str | None = None) -> dict:
        """Ingest data into Cognee."""
        payload = {"data": data}
        if dataset_name:
            payload["dataset_name"] = dataset_name
        resp = self.session.post(f"{self.base_url}/api/v1/add", json=payload)
        resp.raise_for_status()
        return resp.json()

    def cognify(self, datasets: list[str] | None = None) -> dict:
        """Trigger knowledge graph construction."""
        payload = {}
        if datasets:
            payload["datasets"] = datasets
        resp = self.session.post(f"{self.base_url}/api/v1/cognify", json=payload)
        resp.raise_for_status()
        return resp.json()

    def search(self, query: str, dataset: str | None = None) -> list[dict]:
        """Query the knowledge graph."""
        params = {"query": query}
        if dataset:
            params["dataset"] = dataset
        resp = self.session.get(f"{self.base_url}/api/v1/search", params=params)
        resp.raise_for_status()
        return resp.json()

    def remember(self, data: str, session_id: str | None = None) -> dict:
        """V2: Store a memory."""
        payload = {"data": data}
        if session_id:
            payload["session_id"] = session_id
        resp = self.session.post(f"{self.base_url}/api/v1/remember", json=payload)
        resp.raise_for_status()
        return resp.json()

    def recall(self, query: str, session_id: str | None = None) -> list[dict]:
        """V2: Recall memories."""
        payload = {"query": query}
        if session_id:
            payload["session_id"] = session_id
        resp = self.session.post(f"{self.base_url}/api/v1/recall", json=payload)
        resp.raise_for_status()
        return resp.json()

    def list_datasets(self) -> list[dict]:
        """List all datasets."""
        resp = self.session.get(f"{self.base_url}/api/v1/datasets")
        resp.raise_for_status()
        return resp.json()

    def delete_dataset(self, dataset_name: str) -> dict:
        """Delete a dataset."""
        resp = self.session.delete(
            f"{self.base_url}/api/v1/datasets/{dataset_name}"
        )
        resp.raise_for_status()
        return resp.json()

    def health_check(self) -> bool:
        """Check if the Cognee API server is running."""
        try:
            resp = self.session.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except requests.ConnectionError:
            return False


async def main():
    client = CogneeClient()

    # Check if server is running
    print("Checking Cognee API server...")
    if not client.health_check():
        print(" Cognee API server is not running!")
        print("   Start it with: cognee-cli -ui")
        print("   Or: python -m cognee.api")
        print("\nThis example requires a running server. Skipping live calls.")
        print("See the code for the full API reference.")
        return

    print(" Server is running!\n")

    # ── V1 Pipeline via REST ──────────────────────────────────────────
    print("Ingesting data via REST API...")
    client.add(
        "FastAPI is a modern Python web framework for building APIs. "
        "It was created by Sebastián Ramírez and first released in 2018. "
        "FastAPI is built on Starlette for the web parts and Pydantic for "
        "the data parts. It is one of the fastest Python frameworks and "
        "features automatic OpenAPI documentation generation.",
        dataset_name="python_frameworks",
    )

    print("Triggering cognify...")
    client.cognify(datasets=["python_frameworks"])

    # Wait for processing
    time.sleep(5)

    print("\nSearching...")
    results = client.search(
        "What is FastAPI and who created it?",
        dataset="python_frameworks",
    )
    for r in results:
        print(f"  → {r}")

    # ── V2 Memory via REST ────────────────────────────────────────────
    print("\nUsing V2 Memory API via REST...")
    client.remember("The user prefers concise responses.", session_id="rest_demo")
    memories = client.recall("user preferences", session_id="rest_demo")
    print(f"Recalled memories: {memories}")

    print("\nDone! The REST API enables any language to use Cognee.")


if __name__ == "__main__":
    asyncio.run(main())
