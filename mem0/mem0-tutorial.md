# Mem0: The Universal Memory Layer for AI Agents — Complete Tutorial

> **Mem0** (pronounced "mem-zero") is a universal, self-improving memory layer for LLM applications that enables persistent, personalized context across sessions. Built by [mem0.ai](https://mem0.ai), it powers stateful AI agents that remember, learn, and evolve.
>
> - GitHub: <https://github.com/mem0ai/mem0>
> - Docs: <https://docs.mem0.ai>
> - PyPI: `mem0ai`
> - Stars: 59k+ | Version: 2.0.0 (2026)

---

## Table of Contents

1. [What is Mem0? Why Does It Matter?](#1-what-is-mem0-why-does-it-matter)
2. [Installation & Setup](#2-installation--setup)
3. [Architecture Deep Dive](#3-architecture-deep-dive)
4. [Basic CRUD Operations](#4-basic-crud-operations)
5. [Search & Retrieval](#5-search--retrieval)
6. [Configuration: LLMs, Embedders, Vector Stores](#6-configuration-llms-embedders-vector-stores)
7. [Advanced Metadata Filtering](#7-advanced-metadata-filtering)
8. [Reranker-Enhanced Search](#8-reranker-enhanced-search)
9. [Async Memory (AsyncMemory)](#9-async-memory-asyncmemory)
10. [Graph Memory](#10-graph-memory)
11. [Multimodal Support (Images)](#11-multimodal-support-images)
12. [Custom Instructions (Fact Extraction Control)](#12-custom-instructions-fact-extraction-control)
13. [Memory Client (Platform API)](#13-memory-client-platform-api)
14. [CLI Tool (mem0-cli)](#14-cli-tool-mem0-cli)
15. [MCP Integration](#15-mcp-integration)
16. [Real-World Patterns & Recipes](#16-real-world-patterns--recipes)
17. [Platform vs OSS Comparison](#17-platform-vs-oss-comparison)
18. [Best Practices](#18-best-practices)
19. [Troubleshooting & FAQ](#19-troubleshooting--faq)
20. [Jupyter Notebook Reference](#20-jupyter-notebook-reference)

---

## 1. What is Mem0? Why Does It Matter?

### The Problem: Stateless AI

Most AI assistants are **stateless** — they process a query, respond, and forget everything. Even with large context windows:

| Aspect | Context Window | Mem0 Memory |
|--------|---------------|-------------|
| **Retention** | Temporary (one session) | Persistent (forever) |
| **Cost** | Grows with input tokens | Optimized (only relevant facts) |
| **Recall** | Token proximity | Semantic relevance + intent |
| **Personalization** | None across sessions | Deep, evolving user profile |
| **Behavior** | Reactive | Adaptive, learning |

### Mem0's Innovation: V3 Algorithm (April 2026)

Mem0's V3 pipeline introduced a **single-pass ADD-only extraction** model with multi-signal retrieval:

- **Entity linking** — entities are extracted, embedded, and linked across memories
- **Multi-signal retrieval** — semantic + BM25 keyword + entity matching, scored in parallel and fused
- **Temporal reasoning** — time-aware retrieval that ranks by recency and relevance

Benchmarks (vs previous algorithm):
- **91.6** on LoCoMo (+20 points)
- **94.8** on LongMemEval (+27 points)
- **64.1** on BEAM (1M tokens)

### Memory Types in Mem0

Mem0 mimics human memory categories:

| Memory Type | Description | Example |
|-------------|-------------|---------|
| **Working Memory** | Short-term session awareness | Current conversation context |
| **Factual Memory** | Long-term structured knowledge | "User prefers dark mode" |
| **Episodic Memory** | Records of past conversations | "User asked about Python last Tuesday" |
| **Semantic Memory** | General knowledge built over time | "User is a data scientist" |

### Mem0 vs RAG

| Aspect | RAG | Mem0 |
|--------|-----|------|
| **Statefulness** | Stateless | Stateful |
| **Recall Type** | Document lookup | Evolving user context |
| **Use Case** | Ground answers in data | Guide behavior across time |

They're **complementary**: RAG fetches facts from documents; Mem0 provides continuity across sessions.

---

## 2. Installation & Setup

### Prerequisites

- Python 3.10+ (Python SDK) or Node.js 14+ (TypeScript SDK)
- An LLM provider API key (OpenAI by default)
- For OSS: a vector store (local Qdrant by default)

### Install

```bash
# Python SDK
pip install mem0ai

# With graph memory support
pip install "mem0ai[graph]"

# Node.js SDK
npm install mem0ai

# CLI tool
pip install mem0-cli
# or
npm install -g @mem0/cli
```

### Quick Start (OSS — Local)

```python
import os
from mem0 import Memory

# Set your OpenAI key (or any supported LLM)
os.environ["OPENAI_API_KEY"] = "sk-..."

# Initialize with defaults:
#   LLM: OpenAI gpt-5-mini
#   Embedder: OpenAI text-embedding-3-small
#   Vector store: Qdrant (local at /tmp/qdrant)
#   History: SQLite (~/.mem0/history.db)
memory = Memory()

# Add a memory
messages = [
    {"role": "user", "content": "Hi, I'm Alex. I'm a vegetarian and love sci-fi movies."},
    {"role": "assistant", "content": "Got it, Alex! I'll remember that."}
]
memory.add(messages, user_id="alex")

# Search memories
results = memory.search("What are Alex's dietary preferences?", filters={"user_id": "alex"})
print(results)
```

### Quick Start (Platform — Managed API)

```python
from mem0 import MemoryClient

client = MemoryClient(api_key="your-mem0-api-key")

client.add([
    {"role": "user", "content": "I'm a vegetarian and allergic to nuts."},
    {"role": "assistant", "content": "Got it! I'll remember your dietary preferences."}
], user_id="user123")

results = client.search("What are my dietary restrictions?", filters={"user_id": "user123"})
print(results)
```

---

## 3. Architecture Deep Dive

### The Memory Pipeline

```
┌──────────────┐     ┌─────────────────┐     ┌──────────────────┐
│  User/Agent  │────▶│  Mem0.add()     │────▶│  Extraction LLM  │
│  Messages    │     │  (conversation) │     │  (gpt-5-mini)    │
└──────────────┘     └─────────────────┘     └────────┬─────────┘
                                                      │
                                          ┌───────────▼───────────┐
                                          │  Extracted Facts +     │
                                          │  Entities + Metadata   │
                                          └───────────┬───────────┘
                                                      │
                              ┌───────────────────────┼───────────────────────┐
                              │                       │                       │
                    ┌─────────▼─────────┐  ┌──────────▼──────────┐  ┌────────▼─────────┐
                    │  Vector Store     │  │   Graph Store       │  │  History Store   │
                    │  (Qdrant/PGVector)│  │   (Neo4j/Memgraph)  │  │  (SQLite)        │
                    └───────────────────┘  └─────────────────────┘  └──────────────────┘
```

### Search Pipeline (V3 — Hybrid Retrieval)

```
Query ──▶ Embedding ──▶ Vector Search ──▶ Candidate Set
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    │                         │                         │
              ┌─────▼─────┐           ┌──────▼──────┐           ┌──────▼──────┐
              │ Semantic  │           │   BM25      │           │   Entity    │
              │ Score     │           │   Keyword   │           │   Match     │
              └─────┬─────┘           └──────┬──────┘           └──────┬──────┘
                    │                         │                         │
                    └─────────────────────────┼─────────────────────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │   Score Fusion    │
                                    │   (weighted)      │
                                    └─────────┬─────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │  Optional:        │
                                    │  Reranker Pass    │
                                    └─────────┬─────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │  Ranked Results   │
                                    │  + Relations      │
                                    └───────────────────┘
```

### Default Components (OSS)

| Component | Default | Location |
|-----------|---------|----------|
| **Extraction LLM** | OpenAI `gpt-5-mini` | Via `OPENAI_API_KEY` |
| **Embedding Model** | OpenAI `text-embedding-3-small` (1536d) | Via `OPENAI_API_KEY` |
| **Vector Store** | Qdrant (local) | `/tmp/qdrant` |
| **History Store** | SQLite | `~/.mem0/history.db` |
| **Reranker** | Disabled | Configure to enable |

---

## 4. Basic CRUD Operations

### 4.1 Adding Memories (`add`)

The `add` method extracts facts from conversation messages and stores them.

```python
from mem0 import Memory

memory = Memory()

# Basic add — LLM extracts facts
messages = [
    {"role": "user", "content": "My name is Priya. I work at Stripe as an SRE."},
    {"role": "assistant", "content": "Nice to meet you, Priya!"}
]
result = memory.add(messages, user_id="priya")
# Returns: [{"id": "mem_abc", "memory": "Name is Priya", "event": "ADD"},
#            {"id": "mem_def", "memory": "Works at Stripe as an SRE", "event": "ADD"}]

# Add with metadata
result = memory.add(
    messages,
    user_id="priya",
    metadata={"source": "onboarding", "confidence": "high"}
)

# Raw insert (no LLM extraction — stores messages verbatim)
result = memory.add(messages, user_id="priya", infer=False)
```

**Key parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `messages` | list[dict] | List of `{"role": "...", "content": "..."}` dicts |
| `user_id` | str | Scopes memory to a user |
| `agent_id` | str | Scopes memory to an agent |
| `run_id` | str | Scopes memory to a session/run |
| `app_id` | str | Scopes memory to an app |
| `metadata` | dict | Custom key-value pairs attached to all extracted memories |
| `infer` | bool (default True) | False = store raw messages without LLM extraction |
| `custom_instructions` | str | Override extraction prompt for this call |
| `enable_graph` | bool (default True) | Whether to extract graph nodes/edges |

> At least one of `user_id`, `agent_id`, `run_id`, or `app_id` is required.

### 4.2 Getting Memories (`get_all`, `get`)

```python
# Get all memories for a user (paginated)
memories = memory.get_all(filters={"user_id": "priya"}, page=1, page_size=50)
print(memories["count"])  # total count
for mem in memories["results"]:
    print(mem["memory"], mem["created_at"])

# Get a single memory by ID
result = memory.get(memory_id="mem_abc")
print(result["memory"])

# Get with date range filtering
memories = memory.get_all(
    filters={
        "AND": [
            {"user_id": "priya"},
            {"created_at": {"gte": "2026-01-01", "lte": "2026-06-30"}}
        ]
    },
    page=1,
    page_size=100
)
```

### 4.3 Updating Memories (`update`)

```python
# Update a memory's content
memory.update(memory_id="mem_abc", data="Priya now works at Google as a Staff SRE")

# Update with metadata
memory.update(
    memory_id="mem_abc",
    data="Priya now works at Google",
    metadata={"updated_via": "user_correction"}
)

# On Platform: batch update up to 1000 memories
client.batch_update([
    {"memory_id": "id1", "text": "Updated fact 1"},
    {"memory_id": "id2", "text": "Updated fact 2"}
])
```

### 4.4 Deleting Memories (`delete`, `delete_all`)

```python
# Delete a single memory
memory.delete(memory_id="mem_abc")

# Delete all memories for a user
memory.delete_all(user_id="priya")

# Delete all memories for an agent
memory.delete_all(agent_id="old-bot")

# Wildcard delete — ALL memories for ALL users (use with caution!)
# memory.delete_all(user_id="*")

# Platform: batch delete up to 1000
client.batch_delete([{"memory_id": "id1"}, {"memory_id": "id2"}])
```

### 4.5 History (`history`)

```python
# Get change history for a memory
changes = memory.history(memory_id="mem_abc")
for change in changes:
    print(change["event"], change["created_at"])
    # events: ADD, UPDATE, DELETE
```

---

## 5. Search & Retrieval

### 5.1 Basic Semantic Search

```python
# Simple search — scoped to a user
results = memory.search(
    "What does Priya do for work?",
    filters={"user_id": "priya"}
)

# Results include:
# {
#   "results": [
#     {
#       "id": "mem_def",
#       "memory": "Works at Stripe as an SRE",
#       "user_id": "priya",
#       "score": 0.89,
#       "categories": ["work"],
#       "metadata": {"source": "onboarding"},
#       "created_at": "2026-06-22T10:00:00Z",
#       "updated_at": null
#     }
#   ]
# }
```

### 5.2 Search Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | str | required | Natural-language search query |
| `filters` | dict | required | Must contain at least one entity ID |
| `top_k` | int | 10 | Number of results (1-1000) |
| `threshold` | float | 0.1 | Minimum relevance score (0-1). 0.0 to disable |
| `rerank` | bool | False | Apply reranker for better ordering |
| `reference_date` | str/int | None | Temporal anchor (Unix epoch, YYYY-MM-DD, ISO datetime) |

### 5.3 Temporal Search

```python
# Search with temporal bias — "current" preferences rank higher
results = memory.search(
    "What is Priya's job?",
    filters={"user_id": "priya"},
    reference_date="2026-06-22"  # anchor time
)

# Unix epoch also works
import time
results = memory.search(
    "What is Priya's job?",
    filters={"user_id": "priya"},
    reference_date=int(time.time())
)
```

### 5.4 Score Interpretation

The `score` field (0-1) is a **combined relevance score** fusing:
- **Semantic similarity** (embedding cosine distance)
- **BM25 keyword match** (lexical relevance)
- **Entity boost** (shared entities between query and memory)

Higher is better. Default threshold of 0.1 filters out noise. Adjust per use case.

---

## 6. Configuration: LLMs, Embedders, Vector Stores

Mem0's OSS is **fully configurable** — swap every component.

### 6.1 Configuration Methods

**Method A: Python dict**
```python
from mem0 import Memory

config = {
    "vector_store": {
        "provider": "qdrant",
        "config": {"host": "localhost", "port": 6333}
    },
    "llm": {
        "provider": "openai",
        "config": {"model": "gpt-4.1-mini", "temperature": 0.1}
    },
    "embedder": {
        "provider": "openai",
        "config": {"model": "text-embedding-3-small"}
    }
}
memory = Memory.from_config(config)
```

**Method B: YAML file**
```yaml
# config.yaml
vector_store:
  provider: qdrant
  config:
    host: localhost
    port: 6333

llm:
  provider: openai
  config:
    model: gpt-4.1-mini
    temperature: 0.1

embedder:
  provider: openai
  config:
    model: text-embedding-3-small
```

```python
memory = Memory.from_config_file("config.yaml")
```

### 6.2 Supported LLM Providers (Python)

| Provider | Config Example |
|----------|---------------|
| **OpenAI** | `{"provider": "openai", "config": {"model": "gpt-4.1-mini"}}` |
| **Anthropic** | `{"provider": "anthropic", "config": {"model": "claude-sonnet-4-6"}}` |
| **Ollama** | `{"provider": "ollama", "config": {"model": "qwen3:32b"}}` |
| **Groq** | `{"provider": "groq", "config": {"model": "llama-3.1-70b"}}` |
| **DeepSeek** | `{"provider": "deepseek", "config": {"model": "deepseek-chat"}}` |
| **Google AI** | `{"provider": "google", "config": {"model": "gemini-2.0-flash"}}` |
| **AWS Bedrock** | `{"provider": "bedrock", "config": {"model": "..."}}` |
| **Together** | `{"provider": "together", "config": {"model": "..."}}` |
| **Azure OpenAI** | `{"provider": "azure_openai", "config": {}}` |
| **LiteLLM** | `{"provider": "litellm", "config": {}}` |
| **xAI** | `{"provider": "xai", "config": {"model": "grok-3"}}` |
| **LM Studio** | `{"provider": "lmstudio", "config": {}}` |
| **LangChain** | `{"provider": "langchain", "config": {}}` |

### 6.3 Supported Embedder Providers

| Provider | Config Example |
|----------|---------------|
| **OpenAI** | `{"provider": "openai", "config": {"model": "text-embedding-3-small"}}` |
| **Ollama** | `{"provider": "ollama", "config": {"model": "nomic-embed-text"}}` |
| **HuggingFace** | `{"provider": "huggingface", "config": {"model": "BAAI/bge-small-en"}}` |
| **Google AI** | `{"provider": "google", "config": {"model": "text-embedding-004"}}` |
| **Vertex AI** | `{"provider": "vertexai", "config": {"model": "textembedding-gecko@003"}}` |
| **Together** | `{"provider": "together", "config": {"model": "..."}}` |
| **AWS Bedrock** | `{"provider": "bedrock", "config": {}}` |
| **Azure OpenAI** | `{"provider": "azure_openai", "config": {}}` |
| **LM Studio** | `{"provider": "lmstudio", "config": {}}` |
| **LangChain** | `{"provider": "langchain", "config": {}}` |

### 6.4 Supported Vector Store Providers

| Provider | Use Case |
|----------|----------|
| **Qdrant** (default) | Local dev, self-hosted |
| **Postgres + pgvector** | Production self-hosted |
| **Chroma** | Lightweight local |
| **Weaviate** | Hybrid search |
| **Pinecone** | Managed cloud |
| **Milvus** | Large-scale |
| **Redis** | Low-latency caching |
| **Neo4j** | Graph-native |
| **FAISS** | In-memory, no server |

### 6.5 Complete Configuration Example

```python
config = {
    # Extraction LLM — keep temperature LOW for deterministic extraction
    "llm": {
        "provider": "anthropic",
        "config": {
            "model": "claude-sonnet-4-6",
            "temperature": 0.1,
            "max_tokens": 2000
        }
    },
    # Embedding model — must match vector dimensions
    "embedder": {
        "provider": "ollama",
        "config": {
            "model": "nomic-embed-text",
            "embedding_dims": 768
        }
    },
    # Vector store — where embeddings live
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "host": "localhost",
            "port": 6333,
            "collection_name": "my_app_memories"
        }
    },
    # History store — audit trail
    "history_db_path": "~/.mem0/my_app_history.db",
    # Custom instructions for fact extraction
    "custom_instructions": """
        Extract only work-related facts: job title, company, projects, skills.
        Ignore casual conversation and personal hobbies.
    """,
    # Graph store (optional)
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": "bolt://localhost:7687",
            "username": "neo4j",
            "password": "password"
        }
    }
}

memory = Memory.from_config(config)
```

---

## 7. Advanced Metadata Filtering

Mem0 supports a rich filter DSL with logical operators, comparisons, and wildcards.

### 7.1 Operator Reference

| Operator | Meaning | Example |
|----------|---------|---------|
| `eq` / `ne` | Equals / Not equals | `{"status": {"eq": "active"}}` |
| `gt` / `gte` | Greater than / or equal | `{"priority": {"gte": 5}}` |
| `lt` / `lte` | Less than / or equal | `{"confidence": {"lt": 0.9}}` |
| `in` / `nin` | In list / Not in list | `{"category": {"in": ["work", "health"]}}` |
| `contains` / `icontains` | Substring match (case-sensitive/insensitive) | `{"title": {"icontains": "meeting"}}` |
| `*` | Wildcard (field exists) | `{"category": "*"}` |
| `AND` / `OR` / `NOT` | Logical combinators | `{"AND": [{"user_id": "alice"}, {"priority": {"gte": 5}}]}` |

### 7.2 Filtering Patterns

```python
# Basic key-value
results = memory.search(
    "preferences",
    filters={"user_id": "alice", "category": "food"}
)

# Comparison operators
results = memory.search(
    "high priority items",
    filters={
        "user_id": "alice",
        "priority": {"gte": 7},
        "confidence": {"gt": 0.8}
    }
)

# List-based (whitelist / blacklist)
results = memory.search(
    "interests",
    filters={
        "user_id": "alice",
        "category": {"in": ["work", "health", "finance"]},
        "status": {"nin": ["archived", "deleted"]}
    }
)

# Substring matching
results = memory.search(
    "meetings",
    filters={
        "user_id": "alice",
        "title": {"contains": "meeting"},
        "description": {"icontains": "important"}
    }
)

# Wildcard — any memory with a category
results = memory.search(
    "all categorized",
    filters={"user_id": "alice", "category": "*"}
)

# Logical AND
results = memory.search(
    "urgent work items",
    filters={
        "AND": [
            {"user_id": "alice"},
            {"category": "work"},
            {"priority": {"gte": 7}},
            {"status": {"ne": "completed"}}
        ]
    }
)

# Logical OR
results = memory.search(
    "anything urgent",
    filters={
        "user_id": "alice",
        "OR": [
            {"category": "urgent"},
            {"priority": {"gte": 9}},
            {"deadline": {"icontains": "today"}}
        ]
    }
)

# Logical NOT (exclusion)
results = memory.search(
    "active items only",
    filters={
        "user_id": "alice",
        "NOT": [
            {"category": "archived"},
            {"status": "deleted"}
        ]
    }
)

# Complex nested logic
results = memory.search(
    "advanced query",
    filters={
        "AND": [
            {"user_id": "alice"},
            {
                "OR": [
                    {"category": "work"},
                    {"category": "personal"}
                ]
            },
            {"priority": {"gte": 5}},
            {
                "NOT": [
                    {"status": "archived"}
                ]
            }
        ]
    }
)

# Temporal filtering with get_all
memories = memory.get_all(
    filters={
        "AND": [
            {"user_id": "alice"},
            {"created_at": {"gte": "2026-01-01", "lte": "2026-06-30"}}
        ]
    }
)
```

---

## 8. Reranker-Enhanced Search

Rerankers add a **second scoring pass** after initial vector retrieval. This boosts precision for nuanced queries or large memory collections.

### 8.1 When to Use Rerankers

- **Nuanced queries** requiring deep semantic understanding
- **Large collections** where vector search returns many near-matches
- **Consistency** across different vector providers

> **Trade-off:** Reranking adds latency and API cost. Benchmark before deploying.

### 8.2 Supported Reranker Providers

| Provider | Latency | Quality | Cost | Local? |
|----------|---------|---------|------|--------|
| **Cohere** | Medium | High | API cost | No |
| **Sentence Transformer** | Low | Good | Free | Yes |
| **HuggingFace** | Low-Medium | Variable | Free | Yes |
| **LLM Reranker** (OpenAI) | High | Very High | API cost | No |
| **Zero Entropy** | - | High | - | - |

### 8.3 Configuration

```python
# Cohere reranker
config = {
    "reranker": {
        "provider": "cohere",
        "config": {
            "model": "rerank-english-v3.0",
            "api_key": "your-cohere-key"
        }
    }
}
memory = Memory.from_config(config)

# Sentence Transformer (local, free, GPU)
config["reranker"] = {
    "provider": "sentence_transformer",
    "config": {
        "model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
        "device": "cuda",       # or "cpu"
        "max_length": 512
    }
}

# LLM-based reranker (OpenAI)
config["reranker"] = {
    "provider": "llm_reranker",
    "config": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "top_k": 5
    }
}
```

### 8.4 Using Rerankers per Request

```python
# Rerank on a specific search
results = memory.search(
    "complex multi-faceted query",
    filters={"user_id": "alice"},
    rerank=True,
    top_k=5
)

# Smart toggling — only rerank for complex queries
def smart_search(memory, query, user_id):
    use_rerank = len(query.split()) > 3  # multi-word queries
    return memory.search(
        query,
        filters={"user_id": user_id},
        rerank=use_rerank
    )

# Fallback pattern — always have a backup
try:
    results = memory.search("query", filters={"user_id": "alice"}, rerank=True)
except Exception:
    results = memory.search("query", filters={"user_id": "alice"}, rerank=False)
```

### 8.5 Best Practices

1. **Start local**: Use `sentence_transformer` to validate before paying for APIs
2. **Minimize `top_k`**: Smaller candidate pools = faster reranking
3. **Verify**: Check for `score` in results — missing means reranker didn't run
4. **A/B test**: Log both reranked and non-reranked lists during rollout

---

## 9. Async Memory (AsyncMemory)

`AsyncMemory` is Mem0's **non-blocking, asyncio-native** interface. Perfect for FastAPI, background workers, and any async Python application.

### 9.1 Initialization

```python
import asyncio
from mem0 import AsyncMemory

# Default config
memory = AsyncMemory()

# Custom config
from mem0.configs.base import MemoryConfig
config = MemoryConfig(/* ... */)
memory = AsyncMemory(config=config)
```

### 9.2 Full Async Method Parity

| Operation | Async Method | Notes |
|-----------|-------------|-------|
| **Create** | `await memory.add(...)` | Same args as sync `Memory.add` |
| **Search** | `await memory.search(...)` | Returns dict with `results` |
| **List** | `await memory.get_all(...)` | Filter by entity IDs |
| **Get one** | `await memory.get(memory_id=...)` | Raises ValueError if missing |
| **Update** | `await memory.update(memory_id=..., data=...)` | Partial updates |
| **Delete one** | `await memory.delete(memory_id=...)` | Confirmation payload |
| **Delete all** | `await memory.delete_all(...)` | Requires at least one filter |
| **History** | `await memory.history(memory_id=...)` | Change log |

### 9.3 Concurrent Operations

```python
async def batch_add_users():
    memory = AsyncMemory()
    tasks = [
        memory.add(
            messages=[{"role": "user", "content": f"User {i}: I love {hobby}"}],
            user_id=f"user_{i}"
        )
        for i, hobby in enumerate(["gaming", "cooking", "hiking", "reading", "coding"])
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"User {i} failed: {result}")
        else:
            print(f"User {i} added: {len(result)} facts")

asyncio.run(batch_add_users())
```

### 9.4 Resilience Patterns

```python
async def with_timeout_and_retry(operation, max_retries=3, timeout=10.0):
    """Retry with exponential backoff and timeout."""
    import asyncio
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(operation(), timeout=timeout)
        except asyncio.TimeoutError:
            print(f"Timeout on attempt {attempt + 1}")
        except Exception as exc:
            print(f"Error on attempt {attempt + 1}: {exc}")
        if attempt < max_retries - 1:
            await asyncio.sleep(2 ** attempt)  # exponential backoff
    raise Exception(f"Operation failed after {max_retries} attempts")
```

### 9.5 Lifecycle Management

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_memory():
    memory = AsyncMemory()
    try:
        yield memory
    finally:
        # cleanup resources if needed
        pass

async def main():
    async with get_memory() as memory:
        results = await memory.search("test", filters={"user_id": "alice"})
        print(results)
```

---

## 10. Graph Memory

Graph Memory persists **nodes and edges** alongside embeddings, connecting people, places, events, and relationships.

### 10.1 When to Use Graph Memory

- **Multi-actor conversations** where vectors blur entity identities
- **Compliance/auditing** requiring who-said-what-and-when trails
- **Agent teams** needing shared context without duplicating memories
- **Relationship-heavy domains** (social networks, org charts, supply chains)

### 10.2 How It Works

```
Conversation → Extraction LLM → Vector Store (embeddings)
                               → Graph Store (nodes + edges)
Query → Vector Store → Candidates → Graph Store → Contextual Recall
```

### 10.3 Setup (Neo4j Aura — Free Tier)

```bash
pip install "mem0ai[graph]"

export NEO4J_URL="neo4j+s://<your-instance>.databases.neo4j.io"
export NEO4J_USERNAME="neo4j"
export NEO4J_PASSWORD="your-password"
```

```python
import os
from mem0 import Memory

config = {
    "graph_store": {
        "provider": "neo4j",
        "config": {
            "url": os.environ["NEO4J_URL"],
            "username": os.environ["NEO4J_USERNAME"],
            "password": os.environ["NEO4J_PASSWORD"],
            "database": "neo4j",
        }
    }
}

memory = Memory.from_config(config)

# Add a conversation with entities and relationships
conversation = [
    {"role": "user", "content": "Alice met Bob at GraphConf 2025 in San Francisco."},
    {"role": "assistant", "content": "Great! Logging that connection."},
]
memory.add(conversation, user_id="demo-user")

# Search — results include `relations` array with graph context
results = memory.search(
    "Who did Alice meet at GraphConf?",
    filters={"user_id": "demo-user"},
    limit=3
)

for hit in results["results"]:
    print(hit["memory"])
    # Relations show entity connections
    if "relations" in hit:
        print("  Relations:", hit["relations"])
```

### 10.4 Supported Graph Stores

| Provider | Type | Notes |
|----------|------|-------|
| **Neo4j** | Graph-native DB | Cloud (Aura) or self-hosted |
| **Memgraph** | In-memory graph | Low-latency |
| **Neptune** | AWS managed | Enterprise |
| **Kuzu** | Embedded graph | No server needed |
| **Apache AGE** | PostgreSQL extension | SQL + graph |

### 10.5 Graph Controls

```python
# Custom extraction prompt — control what becomes nodes/edges
config["graph_store"]["custom_prompt"] = (
    "Please only capture people, organizations, and project links."
)

# Confidence threshold — filter noisy edges
config["graph_store"]["config"]["threshold"] = 0.75

# Toggle graph per request
memory.add(messages, user_id="alice", enable_graph=False)   # skip graph extraction
results = memory.search("query", filters={"user_id": "alice"}, enable_graph=False)  # skip graph lookup
```

### 10.6 Verify in Neo4j Browser

```cypher
-- See all person nodes and their relationships
MATCH (p:Person)-[r]->(q:Person) RETURN p, r, q LIMIT 10;

-- See full graph for a user
MATCH (n) RETURN n LIMIT 25;
```

---

## 11. Multimodal Support (Images)

Mem0 can extract memories from both **text** and **images** (screenshots, receipts, product photos, diagrams).

### 11.1 Technical Specs

- **Max file size:** 20 MB (recommended: < 5 MB)
- **Supported formats:** JPEG, PNG, WebP, GIF
- **Vision model:** Uses configured LLM's vision capabilities

### 11.2 Adding Images via URL

```python
messages = [
    {"role": "user", "content": "Here's my receipt from yesterday's dinner."},
    {
        "role": "user",
        "content": {
            "type": "image_url",
            "image_url": {"url": "https://example.com/receipt.jpg"}
        }
    }
]
memory.add(messages, user_id="alice")
```

### 11.3 Adding Local Images (Base64)

```python
import base64

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

base64_img = encode_image("receipt.jpg")

messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "What's in this receipt?"},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_img}"
            }
        }
    ]
}]
memory.add(messages, user_id="alice")
```

### 11.4 Error Handling

```python
from mem0.exceptions import InvalidImageError, FileSizeError

try:
    memory.add(messages, user_id="alice")
except InvalidImageError:
    print("Invalid image format or corrupted file")
except FileSizeError:
    print("Image too large (max 20 MB)")
```

### 11.5 Best Practices

1. **Add text context**: Always include a text message explaining the image
2. **Quality matters**: Clear, well-lit images extract better
3. **Size down**: Resize to under 5 MB for faster processing
4. **Split bulk uploads**: Separate `add` calls to isolate failures
5. **Validate client-side**: Check file size before base64 encoding

---

## 12. Custom Instructions (Fact Extraction Control)

Custom instructions let you **precisely control** what facts are extracted from conversations.

### 12.1 Why Use Custom Instructions?

- Extract only **domain-specific facts** (e.g., order numbers, customer info)
- Enforce a **predefined schema** for extracted memories
- **Prevent irrelevant chatter** from entering long-term storage
- Reduce noise and **improve search precision**

### 12.2 Writing Custom Instructions

A good custom instruction prompt should:

1. State allowed fact types explicitly
2. Include few-shot examples (positive AND negative)
3. Show empty `[]` output for irrelevant messages
4. Strictly require JSON with a `facts` key only

```python
custom_instructions = """
Please only extract entities containing customer support information,
order details, and user account information.

Here are few-shot examples:

Input: Hi, how are you?
Output: {"facts": []}

Input: My order #12345 hasn't arrived yet.
Output: {"facts": ["Order #12345 has not arrived"]}

Input: I need to change my shipping address to 123 Main St, Austin TX 78701.
Output: {"facts": ["Shipping address changed to 123 Main St, Austin TX 78701"]}

Input: I like going on hikes on weekends.
Output: {"facts": []}

Return the facts in JSON format as shown above.
Only extract facts related to orders, shipping, and account information.
"""
```

### 12.3 Configuration

```python
config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": "gpt-4.1-mini",
            "temperature": 0.1  # low temp for deterministic extraction
        }
    },
    "custom_instructions": custom_instructions
}
memory = Memory.from_config(config)

# Test: irrelevant message should return empty
result = memory.add(
    [{"role": "user", "content": "I love hiking on weekends!"}],
    user_id="alice"
)
# result should be [] or have very few facts

# Test: relevant message should extract facts
result = memory.add(
    [{"role": "user", "content": "My order #98765 was delivered damaged."}],
    user_id="alice"
)
# result should contain the order fact
```

### 12.4 Per-Call Override

```python
# Override custom_instructions for a specific add call
per_call_instructions = "Only extract facts about food preferences and allergies."

result = memory.add(
    messages,
    user_id="alice",
    custom_instructions=per_call_instructions
)
```

### 12.5 Best Practices

1. **Be precise**: Name exact categories/fields to capture
2. **Include negatives**: Show examples that return `[]`
3. **Strict JSON**: Only `{"facts": [...]}`, no extra keys
4. **Version control**: Track prompt changes for rollbacks
5. **Spot-check**: Regularly review stored memories for prompt drift

---

## 13. Memory Client (Platform API)

The `MemoryClient` connects to Mem0's **managed cloud platform** — zero-ops, scalable, with a visual dashboard.

### 13.1 Setup

```python
from mem0 import MemoryClient

# Get your API key from https://app.mem0.ai/dashboard/api-keys
client = MemoryClient(api_key="your-api-key")

# Or set environment variable
# export MEM0_API_KEY="your-api-key"
client = MemoryClient()  # reads from MEM0_API_KEY env var
```

### 13.2 Platform vs OSS Method Comparison

| Operation | Platform (MemoryClient) | OSS (Memory) |
|-----------|------------------------|--------------|
| Add | `client.add(messages, user_id="...")` | `memory.add(messages, user_id="...")` |
| Search | `client.search(query, filters={...})` | `memory.search(query, filters={...})` |
| Get all | `client.get_all(filters={...})` | `memory.get_all(filters={...})` |
| Get one | `client.get(memory_id=...)` | `memory.get(memory_id=...)` |
| Update | `client.update(memory_id=..., text=...)` | `memory.update(memory_id=..., data=...)` |
| Delete | `client.delete(memory_id=...)` | `memory.delete(memory_id=...)` |
| Delete all | `client.delete_all(user_id=...)` | `memory.delete_all(user_id=...)` |
| Batch update | `client.batch_update([...])` | Loop manually |
| Batch delete | `client.batch_delete([...])` | Loop manually |

### 13.3 Async Platform Client

```python
from mem0 import AsyncMemoryClient

async def main():
    client = AsyncMemoryClient(api_key="your-api-key")

    await client.add(messages, user_id="alice")
    results = await client.search("query", filters={"user_id": "alice"})
    print(results)

asyncio.run(main())
```

### 13.4 Platform-Only Features

- **Visual Dashboard**: Inspect, search, and manage memories at [app.mem0.ai](https://app.mem0.ai)
- **Webhooks**: Real-time notifications for memory events
- **Organizations & Projects**: Multi-tenant support with access control
- **Managed rerankers**: Toggle `rerank=True` — no config needed
- **Rate limits**: Managed quotas per workspace
- **GDPR/CCPA compliance**: Built-in data subject access and erasure

### 13.5 Event Tracking (Async Processing)

Platform `add` calls are **asynchronous** — they return immediately with an `event_id`.

```python
# Add returns immediately
result = client.add(messages, user_id="alice")
# result = {"message": "Memory processing has been queued...",
#           "status": "PENDING", "event_id": "evt-abc123"}

# Poll event status
event = client.get_event(result["event_id"])
# event = {"status": "SUCCEEDED", "memories": [...]]}
```

---

## 14. CLI Tool (mem0-cli)

Mem0 provides a CLI for quick operations without writing code.

### 14.1 Install

```bash
pip install mem0-cli
# or
npm install -g @mem0/cli
```

### 14.2 Agent Signup (No Email Required!)

AI agents can mint a working API key in **under five seconds**:

```bash
mem0 init --agent --agent-caller claude-code

# Add a memory
mem0 add "I am using mem0"

# Search
mem0 search "am I using mem0"
```

The human owner can claim the account later with `mem0 init --email <email>`.

### 14.3 Common Commands

```bash
# Initialize
mem0 init --api-key "your-key"       # with existing key
mem0 init --agent --agent-caller <name>  # agent signup
mem0 init --email user@example.com   # human signup

# CRUD
mem0 add "I love pizza" --user-id alice
mem0 search "food preferences" --user-id alice
mem0 get --memory-id mem_abc123
mem0 update --memory-id mem_abc123 --text "I love pasta"
mem0 delete --memory-id mem_abc123

# Filters
mem0 search "query" --user-id alice --agent-id bot-1
mem0 get-all --user-id alice --page 1 --page-size 50

# Advanced
mem0 search "query" --rerank --top-k 5 --threshold 0.2
mem0 add "text" --metadata '{"source":"cli"}' --infer false
```

---

## 15. MCP Integration

Mem0 provides an **MCP (Model Context Protocol) server** that lets AI agents manage memories autonomously.

### 15.1 What MCP Enables

Instead of hardcoding `memory.add()` calls, your agent can **decide when** to save, search, and update memories automatically. The MCP server exposes Mem0 as tools the LLM can call.

### 15.2 Setup

```bash
# Install MCP server
pip install mem0-mcp

# Configure in your MCP client (e.g., Claude Desktop's mcp.json)
{
  "mcpServers": {
    "mem0": {
      "command": "mem0-mcp",
      "env": {
        "MEM0_API_KEY": "your-api-key"
      }
    }
  }
}
```

### 15.3 Available Tools (via MCP)

| Tool | Description |
|------|-------------|
| `add_memory` | Store new facts from a conversation |
| `search_memories` | Semantic search across stored memories |
| `get_memories` | List all memories for an entity |
| `update_memory` | Modify an existing memory |
| `delete_memory` | Remove a memory |
| `delete_all_memories` | Bulk delete by filter |

### 15.4 How Agents Use It

The LLM decides autonomously:

```
User: "I just moved to Berlin and started a new job at Spotify."

Agent (thinking): New personal info detected — should save this.
Agent calls: add_memory("User moved to Berlin", user_id="alice")
Agent calls: add_memory("User started job at Spotify", user_id="alice")

Agent: "Congrats on the move and new job! I've saved that. How can I help?"

---

User (next week): "What's a good neighborhood near my office?"

Agent (thinking): I need location and job info.
Agent calls: search_memories("work location", user_id="alice")
Result: "Started job at Spotify" + "Moved to Berlin"

Agent: "Spotify's office is in Mitte. Prenzlauer Berg is nearby and very popular."
```

---

## 16. Real-World Patterns & Recipes

### 16.1 Personalized AI Assistant

```python
from mem0 import Memory
from openai import OpenAI

memory = Memory()
llm = OpenAI()

def chat_with_memory(message: str, user_id: str) -> str:
    """Chat with memory-augmented responses."""
    # Step 1: Retrieve relevant memories
    relevant = memory.search(message, filters={"user_id": user_id}, top_k=5)
    memories_str = "\n".join(
        f"- {m['memory']}" for m in relevant["results"]
    )

    # Step 2: Build system prompt with memories
    system_prompt = f"""You are a helpful AI assistant.
User Memories (from past conversations):
{memories_str}

Use these memories to personalize your responses.
If memories are irrelevant, ignore them."""

    # Step 3: Generate response
    response = llm.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
    )
    reply = response.choices[0].message.content

    # Step 4: Store new memories from this exchange
    memory.add([
        {"role": "user", "content": message},
        {"role": "assistant", "content": reply}
    ], user_id=user_id)

    return reply
```

### 16.2 Multi-User Customer Support Bot

```python
class SupportBot:
    """Customer support bot with per-user memory."""

    def __init__(self):
        self.memory = Memory()
        self.llm = OpenAI()

    def handle_ticket(self, message: str, user_id: str, ticket_id: str) -> str:
        # Search user's history and previous tickets
        user_history = self.memory.search(
            message,
            filters={
                "AND": [
                    {"user_id": user_id},
                    {"category": {"in": ["support", "issue", "preference"]}}
                ]
            },
            top_k=5
        )

        # Build context-aware prompt
        context = "\n".join(m["memory"] for m in user_history["results"])

        response = self.llm.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": f"""You are a support agent.
User history: {context}
Current ticket: {ticket_id}"""},
                {"role": "user", "content": message}
            ]
        )
        reply = response.choices[0].message.content

        # Store with metadata
        self.memory.add([
            {"role": "user", "content": message},
            {"role": "assistant", "content": reply}
        ], user_id=user_id, metadata={
            "ticket_id": ticket_id,
            "category": "support",
            "timestamp": "2026-06-22T10:00:00Z"
        })

        return reply

    def get_customer_context(self, user_id: str) -> dict:
        """Aggregate all known info about a customer."""
        memories = self.memory.get_all(
            filters={"user_id": user_id},
            page=1, page_size=200
        )
        return {
            "total_interactions": memories["count"],
            "recent_issues": [m for m in memories["results"]
                            if "issue" in str(m.get("categories", []))],
            "preferences": [m for m in memories["results"]
                          if "preference" in str(m.get("categories", []))]
        }
```

### 16.3 Session-Based Learning Agent

```python
import uuid

class LearningAgent:
    """Agent that learns across sessions using Mem0."""

    def __init__(self):
        self.memory = Memory()

    def run_session(self, user_id: str, user_message: str):
        # Create a unique run_id for this session
        run_id = str(uuid.uuid4())

        # Retrieve relevant past memories (across all sessions)
        past_memories = self.memory.search(
            user_message,
            filters={"user_id": user_id},
            top_k=5
        )

        # Retrieve this-session working memory
        session_memories = self.memory.search(
            user_message,
            filters={
                "AND": [
                    {"user_id": user_id},
                    {"run_id": run_id}
                ]
            },
            top_k=3
        )

        # Combine and respond
        # ... (LLM call with past + session context)

        # Store with run_id to scope this session
        self.memory.add(
            messages=[{"role": "user", "content": user_message}],
            user_id=user_id,
            run_id=run_id
        )

    def end_session(self, user_id: str, run_id: str):
        """Clean up session-specific memories."""
        self.memory.delete_all(user_id=user_id, run_id=run_id)
```

### 16.4 Feedback-Driven Memory Self-Correction

```python
class SelfCorrectingMemory:
    """Memory that learns from user corrections."""

    def __init__(self):
        self.memory = Memory()

    def handle_correction(self, user_id: str, correction_message: str):
        """User says something that contradicts stored memory."""

        # Search for the fact being corrected
        related = self.memory.search(
            correction_message,
            filters={"user_id": user_id},
            top_k=3
        )

        if related["results"]:
            # Update the most relevant memory
            old_memory = related["results"][0]
            self.memory.update(
                memory_id=old_memory["id"],
                data=f"[CORRECTED] {correction_message}",
                metadata={"corrected": True, "previous": old_memory["memory"]}
            )

        # Also add the correction as a new fact
        self.memory.add(
            [{"role": "user", "content": correction_message}],
            user_id=user_id,
            metadata={"type": "correction"}
        )
```

### 16.5 Observability: Logging All Memory Operations

```python
import logging
from datetime import datetime

class ObservableMemory:
    """Wrapper that logs all memory operations for debugging."""

    def __init__(self, memory: Memory, logger: logging.Logger):
        self.memory = memory
        self.logger = logger

    def add(self, messages, **kwargs):
        start = datetime.now()
        result = self.memory.add(messages, **kwargs)
        elapsed = (datetime.now() - start).total_seconds()
        self.logger.info(
            f"ADD | user={kwargs.get('user_id')} | "
            f"messages={len(messages)} | facts={len(result)} | "
            f"time={elapsed:.2f}s"
        )
        return result

    def search(self, query, **kwargs):
        start = datetime.now()
        result = self.memory.search(query, **kwargs)
        elapsed = (datetime.now() - start).total_seconds()
        self.logger.info(
            f"SEARCH | query='{query[:50]}...' | "
            f"results={len(result['results'])} | time={elapsed:.2f}s"
        )
        return result

    # ... wrap other methods similarly
```

### 16.6 Full RAG + Memory Pipeline

```python
class Mem0RAGPipeline:
    """Combine document retrieval (RAG) with user memory (Mem0)."""

    def __init__(self, vector_db, memory: Memory):
        self.vector_db = vector_db   # e.g., Pinecone for docs
        self.memory = memory         # Mem0 for user context
        self.llm = OpenAI()

    def query(self, question: str, user_id: str) -> str:
        # 1. Retrieve relevant documents (RAG)
        docs = self.vector_db.similarity_search(question, k=3)
        doc_context = "\n".join(d.page_content for d in docs)

        # 2. Retrieve user memories (Mem0)
        memories = self.memory.search(
            question,
            filters={"user_id": user_id},
            top_k=5
        )
        memory_context = "\n".join(
            m["memory"] for m in memories["results"]
        )

        # 3. Combined prompt
        response = self.llm.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{
                "role": "system",
                "content": f"""You are a helpful assistant.

Relevant documents:
{doc_context}

User context (from past interactions):
{memory_context}

Answer based on BOTH documents and user context."""
            }, {
                "role": "user",
                "content": question
            }]
        )
        answer = response.choices[0].message.content

        # 4. Store this interaction
        self.memory.add([
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer}
        ], user_id=user_id, metadata={"pipeline": "rag+mem0"})

        return answer
```

---

## 17. Platform vs OSS Comparison

| Feature | Mem0 Platform | Mem0 OSS |
|---------|--------------|----------|
| **Deployment** | Fully managed cloud | Self-hosted |
| **Setup** | API key + `pip install mem0ai` | Configure LLM + Vector Store + embedder |
| **Scaling** | Automatic | Manual / your infra |
| **Dashboard** | Visual UI at app.mem0.ai | None (CLI + logs) |
| **API Keys** | Per-user, scoped | None (your app handles auth) |
| **Webhooks** | Yes | No (build your own) |
| **Organizations** | Multi-tenant, RBAC | App-level isolation |
| **Rerankers** | Toggle `rerank=True` | Configure provider yourself |
| **Batch Operations** | `batch_update`, `batch_delete` (up to 1000) | Loop manually |
| **Event Tracking** | `event_id` polling | Synchronous returns |
| **Rate Limits** | Managed | By your LLM/DB provider |
| **Cost** | Pay per operation | Your infra + API costs |
| **Data Residency** | Mem0 cloud | Your servers |
| **GDPR/CCPA** | Built-in | Your responsibility |
| **Offline** | No | Yes (fully local) |
| **Pricing Model** | Per-request / tiered | Free (OSS) + provider costs |

**When to choose Platform:** Production apps, teams, need dashboard, don't want to manage infra.
**When to choose OSS:** Compliance requirements, offline needs, full customization, cost sensitivity at scale.

---

## 18. Best Practices

### 18.1 Fact Extraction

1. **Keep LLM temperature ≤ 0.2** for deterministic extraction
2. **Use custom instructions** to scope extraction to your domain
3. **Include negative examples** in few-shot prompts
4. **Spot-check stored memories** weekly for extraction quality

### 18.2 Search & Retrieval

1. **Always scope searches** with entity IDs (`user_id`, `agent_id`, etc.)
2. **Use threshold 0.1-0.3** to filter noise (raise for precision, lower for recall)
3. **Set reasonable `top_k`** (10-20 for production, lower for latency-sensitive apps)
4. **Use `reference_date`** for time-sensitive queries
5. **A/B test** reranked vs non-reranked before rolling out

### 18.3 Performance

1. **Batch operations** where possible (Platform's `batch_update`/`batch_delete`)
2. **Use AsyncMemory** for concurrent workloads
3. **Keep images under 5 MB** for faster multimodal processing
4. **Minimize reranker `top_k`** — larger candidate pools = slower reranking
5. **Use local rerankers** (Sentence Transformers) for cost-sensitive deployments

### 18.4 Data Hygiene

1. **Implement TTL/deletion policies** for session-scoped memories
2. **Version your custom instructions** — track changes for rollbacks
3. **Monitor memory growth** — prune stale facts periodically
4. **Separate concerns** — use different `user_id`/`agent_id`/`run_id` scopes
5. **Handle corrections gracefully** — update, don't delete-and-recreate

### 18.5 Security

1. **Never expose API keys** in client-side code
2. **Scope API keys** to specific projects/users on the Platform
3. **Use environment variables** for all secrets
4. **Audit delete_all calls** — wildcard `"*"` is powerful
5. **Monitor history** for unexpected mutations

---

## 19. Troubleshooting & FAQ

### Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| **Empty search results** | Embedder model mismatch (different dimensions) | Check embedder config — dimensions must match vector store |
| **Qdrant connection errors** | Port 6333 not exposed or wrong host | Verify Qdrant is running: `curl localhost:6333/health` |
| **`Unknown reranker` error** | SDK version too old | `pip install --upgrade mem0ai` |
| **Memory.add() returns nothing** | LLM extracted no facts (too strict custom instructions) | Broaden custom_instructions or add negative examples |
| **Slow multimodal processing** | Image too large | Resize to under 5 MB |
| **Duplicate facts** | Mixed `infer=True` and `infer=False` for same content | Use one inference mode consistently |
| **Platform add returns PENDING** | Async processing (by design) | Poll `GET /v1/event/{event_id}/` or wait a few seconds |
| **400 error on search** | Entity IDs not inside `filters` object | Use `filters={"user_id": "alice"}`, NOT top-level |

### FAQ

**Q: Can I use Mem0 without OpenAI?**
A: Yes. Mem0 supports 15+ LLM providers (Anthropic, Ollama, Groq, DeepSeek, Gemini, etc.) and 10+ embedder providers.

**Q: Is Mem0 free?**
A: The OSS version is free and open source (Apache 2.0). You pay only for your LLM/embedder API calls. The Platform has usage-based pricing.

**Q: Can I run Mem0 completely offline?**
A: Yes. Use Ollama for LLM + embeddings, Qdrant (local) for vector store. No internet needed after model download.

**Q: How is Mem0 different from a vector database?**
A: Mem0 is a full memory engine — it handles fact extraction (LLM), deduplication, conflict resolution, temporal reasoning, graph relationships, and multi-signal retrieval. A vector DB just stores and retrieves embeddings.

**Q: Can I use Mem0 with my existing agent framework?**
A: Yes. Mem0 is framework-agnostic. Use it with LangChain, CrewAI, AutoGen, custom agents, or directly with any LLM SDK.

**Q: How many memories can I store?**
A: OSS: limited by your vector store. Platform: scales to millions of memories per project.

---

## 20. Jupyter Notebook Reference

A companion Jupyter notebook with all the code examples from this tutorial is available at:

```
mem0/mem0_tutorial.ipynb
```

The notebook contains 15+ runnable cells covering every topic in this tutorial, with detailed comments. Open it with:

```bash
jupyter notebook mem0/mem0_tutorial.ipynb
# or in VS Code: open the .ipynb file directly
```

---

## Quick Reference Card

```python
# ── Import ──────────────────────────────────────────────
from mem0 import Memory, AsyncMemory, MemoryClient

# ── Init ────────────────────────────────────────────────
memory = Memory()                                    # defaults (OpenAI + Qdrant)
memory = Memory.from_config(config_dict)             # custom config dict
memory = Memory.from_config_file("config.yaml")      # custom YAML config
client = MemoryClient(api_key="key")                 # platform (managed)

# ── CRUD ───────────────────────────────────────────────
memory.add(messages, user_id="...", metadata={...})  # store facts
memory.get(memory_id="...")                          # one memory
memory.get_all(filters={"user_id": "..."})           # paginated list
memory.update(memory_id="...", data="new text")      # modify
memory.delete(memory_id="...")                       # remove one
memory.delete_all(user_id="...")                     # bulk remove
memory.history(memory_id="...")                      # change log

# ── Search ─────────────────────────────────────────────
memory.search(query, filters={"user_id": "..."},     # basic
              top_k=10, threshold=0.1)
memory.search(query, filters={"user_id": "..."},     # with rerank
              rerank=True, top_k=5)
memory.search(query, filters={                        # advanced filters
    "AND": [{"user_id": "..."}, {"category": {"in": ["work"]}}]
})

# ── Config ─────────────────────────────────────────────
config = {
    "llm": {"provider": "openai", "config": {"model": "gpt-4.1-mini"}},
    "embedder": {"provider": "openai", "config": {"model": "text-embedding-3-small"}},
    "vector_store": {"provider": "qdrant", "config": {"host": "localhost", "port": 6333}},
    "reranker": {"provider": "cohere", "config": {"model": "rerank-english-v3.0"}},
    "graph_store": {"provider": "neo4j", "config": {"url": "...", "username": "...", "password": "..."}},
    "custom_instructions": "Only extract order and shipping facts...",
    "history_db_path": "~/.mem0/history.db"
}
```

---

*Tutorial written 2026-06-22. Mem0 v2.0.0. Source: [docs.mem0.ai](https://docs.mem0.ai), [github.com/mem0ai/mem0](https://github.com/mem0ai/mem0).*
