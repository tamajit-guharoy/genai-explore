"""
22_local_dev.py — Fully local Cognee setup with Ollama.

This example configures Cognee to run entirely on local infrastructure
using Ollama for LLM inference. No API keys, no cloud dependencies.

IMPORTANT CAVEAT: Local models below ~70B parameters struggle with Cognee's
structured output requirements (entity extraction returns typed JSON).
For reliable production use, consider:
- Using commercial APIs (OpenAI, Anthropic) for the cognify phase
- Running a large local model (70B+) with careful prompt engineering
- Using Cognee's built-in fallback/recovery for malformed extractions

Prerequisites:
    pip install cognee
    # Install Ollama: https://ollama.com
    ollama pull llama3.1:8b  # or any supported model
"""

import asyncio
import os

import cognee


def configure_local_llm():
    """Configure Cognee to use a local Ollama model."""
    cognee.config.set({
        "llm_provider": "ollama",
        "llm_model": "llama3.1:8b",           # Change to your model
        "llm_api_base": "http://localhost:11434/v1",
        "llm_api_key": "not-needed",          # Ollama doesn't use API keys

        # Use a local embedding model too
        "embedding_provider": "ollama",
        "embedding_model": "nomic-embed-text", # or "llama3.1:8b"

        # Keep the default local databases
        "graph_database_provider": "kuzu",    # Embedded graph DB
        "vector_database_provider": "lancedb", # Embedded vector DB
        "relational_database_provider": "sqlite", # Embedded relational DB

        # Lower concurrency — local models are slower
        "concurrency": 2,
    })

    print("Configured for fully local operation:")
    print(f"  LLM: {cognee.config.get('llm_provider')}/{cognee.config.get('llm_model')}")
    print(f"  Embeddings: {cognee.config.get('embedding_provider')}/{cognee.config.get('embedding_model')}")
    print(f"  Graph DB: {cognee.config.get('graph_database_provider')}")
    print(f"  Vector DB: {cognee.config.get('vector_database_provider')}")
    print(f"  Relational DB: {cognee.config.get('relational_database_provider')}")


async def main():
    print("Fully Local Cognee Setup")
    print("=" * 60)

    # Configure for local operation
    configure_local_llm()

    print("\n" + "=" * 60)
    print("Testing local pipeline with simple data...")

    try:
        # ── Simple ingestion ───────────────────────────────────────────
        await cognee.add(
            "Python is a high-level programming language created by Guido "
            "van Rossum and first released in 1991. It emphasizes code "
            "readability with its notable use of significant indentation. "
            "Python is dynamically typed and garbage-collected.",
            dataset_name="local_test",
        )

        print("Data added. Running cognify (this may take a while on local models)...")
        await cognee.cognify()

        # ── Search ─────────────────────────────────────────────────────
        print("\nSearching...")
        results = await cognee.search("Who created Python and when?")

        for r in results:
            print(f"  → {r}")

        print("\n Local pipeline working!")

    except Exception as e:
        print(f"\n Local pipeline encountered an issue: {e}")
        print("\nCommon issues with local models:")
        print("  1. Structured output failures — model returns invalid JSON")
        print("     → Try a larger model (llama3.1:70b, mixtral:8x22b)")
        print("     → Or use a commercial API for cognify phase only")
        print("  2. Ollama not running")
        print("     → Run: ollama serve")
        print("  3. Model not pulled")
        print("     → Run: ollama pull llama3.1:8b")
        print("\nHybrid approach (recommended for reliability):")
        print("  # Use OpenAI/Anthropic for entity extraction:")
        print("  cognee.config.set({")
        print('      "llm_provider": "openai",')
        print('      "llm_model": "gpt-4o",')
        print('      "llm_api_key": "sk-...",')
        print("  })")
        print("  # Everything else runs locally (graph, vectors, metadata)")


if __name__ == "__main__":
    asyncio.run(main())
