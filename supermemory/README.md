# Supermemory Tutorial

> **Supermemory** is the state-of-the-art memory and context engine for AI agents. **#1 on LongMemEval, LoCoMo, and ConvoMem** — the three major benchmarks for AI memory evaluation.
>
> - Docs: https://supermemory.ai/docs
> - GitHub: https://github.com/supermemoryai/supermemory
> - PyPI: https://pypi.org/project/supermemory/
> - npm: https://www.npmjs.com/package/supermemory

---

## What is Supermemory?

Supermemory solves the "Goldfish Memory" problem — AI systems forgetting everything between conversations. It automatically:

- **Extracts facts** from conversations, documents, and any content
- **Builds evolving user profiles** — static long-term facts + dynamic recent context
- **Resolves contradictions** — when new info conflicts with old, it *updates* rather than duplicates
- **Auto-forgets** expired/temporary information
- **Delivers relevant context** on demand with sub-300ms hybrid search (vector + keyword)

It's a **living knowledge graph**, not static document storage. Memories are connected through relationships (updates, extends, derives), so information evolves naturally.

---

## Tutorial Structure

| # | Notebook | What You'll Learn |
|---|----------|-------------------|
| 01 | [Introduction & Setup](notebooks/01_introduction_and_setup.ipynb) | API keys, installing the SDK, first client, understanding the mental model |
| 02 | [Adding Memories](notebooks/02_adding_memories.ipynb) | Text, URLs, files, bulk ingestion, customId for updates, containerTags for scoping |
| 03 | [Searching Memories](notebooks/03_searching_memories.ipynb) | Semantic search, hybrid search, threshold tuning, pagination, relevance scoring |
| 04 | [User Profiles](notebooks/04_user_profiles.ipynb) | Static vs dynamic profiles, auto-building, profile+search together, use cases |
| 05 | [Graph Memory & Relationships](notebooks/05_graph_memory_and_relationships.ipynb) | Updates, Extends, Derives — how Supermemory builds a living knowledge graph |
| 06 | [Metadata & Advanced Filtering](notebooks/06_metadata_and_filtering.ipynb) | Custom metadata, AND/OR filters, containerTags, organizing at scale |
| 07 | [Async Operations](notebooks/07_async_operations.ipynb) | AsyncSupermemory, concurrent ingestion, async search, performance patterns |
| 08 | [Self-Hosting Supermemory](notebooks/08_self_hosting.ipynb) | Single binary install, local embeddings, bring-your-own-model, air-gapped setup |
| 09 | [Integrating with LLMs](notebooks/09_integrating_with_llms.ipynb) | Chatbots with memory, agent workflows, RAG pipelines, AI SDK integration |
| 10 | [Production Patterns](notebooks/10_production_patterns.ipynb) | Error handling, retries, timeouts, caching, rate limits, logging, monitoring |

### Example Scripts

| File | Description |
|------|-------------|
| [chatbot_with_memory.py](examples/chatbot_with_memory.py) | Full chatbot with Supermemory-backed user profiles |
| [agent_memory.py](examples/agent_memory.py) | AI agent that remembers tasks, preferences, and results |
| [rag_with_supermemory.py](examples/rag_with_supermemory.py) | RAG pipeline using Supermemory as the knowledge store |

---

## Quick Start

```bash
# 1. Install
pip install supermemory

# 2. Get an API key: https://console.supermemory.ai → API Keys → Create
export SUPERMEMORY_API_KEY="sm_your_key_here"

# 3. First call
python -c "
from supermemory import Supermemory
client = Supermemory()
client.add(content='Hello, Supermemory!', container_tag='demo')
print('Memory added!')
print(client.profile(container_tag='demo'))
"
```

---

## Core Concepts at a Glance

```
                    ┌──────────────────────────┐
                    │     YOUR APPLICATION      │
                    └────────────┬─────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │    Supermemory SDK/API    │
                    │  add() profile() search() │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   ┌────▼─────┐          ┌──────▼──────┐          ┌──────▼──────┐
   │  Memory  │          │    User     │          │   Hybrid    │
   │  Graph   │          │  Profiles   │          │   Search    │
   │          │          │             │          │             │
   │ • Facts  │◄────────►│ • Static    │◄────────►│ • Vector    │
   │ • Prefs  │          │ • Dynamic   │          │ • Keyword   │
   │ • Epi-   │          │             │          │ • Semantic  │
   │   sodes  │          └─────────────┘          └─────────────┘
   └──────────┘
```

---

## Key API Methods (Python SDK)

| Method | Description |
|--------|-------------|
| `client.add(content, container_tag, metadata, custom_id)` | Add content for memory extraction |
| `client.profile(container_tag, q)` | Get user profile + relevant memories |
| `client.search.documents(q, container_tags, filters, limit)` | Hybrid semantic + keyword search |
| `client.search.execute(q, ...)` | Search across all documents |
| `client.memory.create(content, ...)` | Create a memory directly |
| `client.documents.list(container_tags, limit, offset)` | List documents |
| `client.documents.delete(doc_id)` | Delete a document |
| `client.documents.upload_file(file, ...)` | Upload PDF/image/video for processing |

---

## Self-Hosting (One Binary)

```bash
# Install and run — zero config
curl -fsSL https://supermemory.ai/install | bash

# Or with npx
npx supermemory local

# Point SDK to local server
from supermemory import Supermemory
client = Supermemory(
    api_key="sm_local_key",
    base_url="http://localhost:6767"
)
```

---

## Requirements

- Python 3.9+
- Supermemory API key (free tier: 100K tokens stored)
- Or: self-host with any LLM (OpenAI, Anthropic, Ollama, etc.)

---

## Resources

- [Official Documentation](https://supermemory.ai/docs)
- [REST API Reference](https://supermemory.ai/docs/api-reference)
- [OpenAPI Spec](https://api.supermemory.ai/v3/openapi)
- [Python SDK Repo](https://github.com/supermemoryai/python-sdk)
- [Discord Community](https://supermemory.link/discord)
- [Self-Hosting Guide](https://supermemory.ai/docs/self-hosting/overview)
