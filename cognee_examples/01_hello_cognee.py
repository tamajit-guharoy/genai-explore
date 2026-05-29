"""
01_hello_cognee.py — Minimal add → cognify → search pipeline.

This is the simplest possible Cognee workflow. It ingests a paragraph of text,
builds a knowledge graph from it, and then queries it with a multi-hop question.

Prerequisites:
    pip install cognee

Quick start (OpenAI):
    $env:LLM_API_KEY="sk-..."
    python cognee_examples/01_hello_cognee.py

Using DeepSeek (or any OpenAI-compatible API) for LLM + FastEmbed for embeddings:
    $env:LLM_API_KEY="sk-your-deepseek-key"
    $env:LLM_ENDPOINT="https://api.deepseek.com/v1"
    $env:LLM_MODEL="openai/deepseek-chat"
    $env:EMBEDDING_PROVIDER="fastembed"
    $env:EMBEDDING_MODEL="BAAI/bge-small-en-v1.5"
    $env:EMBEDDING_DIMENSIONS="384"
    python cognee_examples/01_hello_cognee.py

    pip install cognee[local]   # includes FastEmbed

Other OpenAI-compatible providers work the same way — just set LLM_ENDPOINT
to their base URL and LLM_API_KEY to their key.
"""

import asyncio
import os

import cognee


async def main():
    # ── Configuration ────────────────────────────────────────────────────
    # Cognee reads these environment variables (Pydantic Settings, auto-uppercased):
    #
    #   LLM_PROVIDER   (default: "openai")    — provider name
    #   LLM_MODEL      (default: "openai/gpt-5-mini") — model identifier
    #   LLM_ENDPOINT   (default: "")          — custom API base URL
    #   LLM_API_KEY    (default: None)        — API key
    #
    #   EMBEDDING_PROVIDER   (default: "openai")
    #   EMBEDDING_MODEL      (default: "openai/text-embedding-3-large")
    #   EMBEDDING_ENDPOINT   (default: None)
    #   EMBEDDING_API_KEY    (default: None)
    #
    # For any OpenAI-compatible API (DeepSeek, Groq, Together, local vLLM, etc.),
    # the provider stays "openai" — just point LLM_ENDPOINT at the right URL.

    provider = os.environ.get("LLM_PROVIDER", "openai")
    model = os.environ.get("LLM_MODEL", "openai/gpt-5-mini")
    endpoint = os.environ.get("LLM_ENDPOINT", "")
    api_key = os.environ.get("LLM_API_KEY", "")

    if endpoint:
        print(f"Using {model} @ {endpoint}")
    elif api_key:
        print(f"Using {model} (default endpoint)")
    else:
        print("No LLM_API_KEY set — set it before running, e.g.:")
        print('  $env:LLM_API_KEY="sk-..."')
        print("Or for DeepSeek:")
        print('  $env:LLM_API_KEY="sk-your-deepseek-key"')
        print('  $env:LLM_ENDPOINT="https://api.deepseek.com/v1"')
        print('  $env:LLM_MODEL="openai/deepseek-chat"')
        return

    # ── Step 1: Add data ─────────────────────────────────────────────────
    print("Adding data...")
    await cognee.add("""
    Natural Language Processing (NLP) is a subfield of artificial intelligence
    focused on the interaction between computers and human language.

    Deep learning models called transformers, introduced in the 2017 paper
    "Attention Is All You Need" by Vaswani et al., revolutionized NLP by
    enabling parallel processing of sequential data.

    BERT (Bidirectional Encoder Representations from Transformers) was developed
    by Google researchers and uses the transformer architecture's encoder to
    understand context from both directions simultaneously.

    GPT (Generative Pre-trained Transformer) was developed by OpenAI and uses
    the transformer's decoder to generate text autoregressively.

    Both BERT and GPT are built on the transformer architecture, but BERT is
    optimized for understanding tasks (classification, NER, QA) while GPT is
    optimized for generation tasks (completion, summarization, dialogue).
    """)

    # ── Step 2: Cognify — build the knowledge graph ──────────────────────
    print("Building knowledge graph (this may take a moment)...")
    await cognee.cognify()

    # ── Step 3: Search — hybrid graph + vector retrieval ─────────────────
    print("\n" + "=" * 60)

    queries = [
        "What is the relationship between transformers and BERT?",
        "Who developed GPT and what architecture does it use?",
        "How do BERT and GPT differ in what they're optimized for?",
    ]

    for query in queries:
        print(f"\n Query: {query}")
        print("-" * 40)
        results = await cognee.search(query)
        for i, result in enumerate(results):
            print(f"Result {i + 1}: {result}")
        print()

    print("Done! The knowledge graph now persists and can be queried again.")


if __name__ == "__main__":
    asyncio.run(main())
