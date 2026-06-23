# Hindsight Tutorial: Agent Memory That Learns

> **Hindsight** is an open-source, state-of-the-art memory system for AI agents by [Vectorize](https://vectorize.io).
> It gives agents persistent, biomimetic memory — they don't just recall, they *learn*.
>
> - GitHub: https://github.com/vectorize-io/hindsight (16.8k+ stars)
> - Docs: https://hindsight.vectorize.io
> - Paper: https://arxiv.org/abs/2512.12818
> - PyPI: `hindsight-client`, `hindsight-api`, `hindsight-all`

---

## Table of Contents

| # | Topic | File | Notebook |
|---|-------|------|----------|
| 1 | **Getting Started** — What is Hindsight, installation, quick start | [01_getting_started.md](01_getting_started.md) | [01_getting_started.ipynb](notebooks/01_getting_started.ipynb) |
| 2 | **Core Concepts** — Architecture, memory types, the 3 operations | [02_core_concepts.md](02_core_concepts.md) | — |
| 3 | **Retain** — Storing memories, fact extraction, entities, batching | [03_retain.md](03_retain.md) | [03_retain.ipynb](notebooks/03_retain.ipynb) |
| 4 | **Recall** — TEMPR multi-strategy retrieval, chunks, filtering | [04_recall.md](04_recall.md) | [04_recall.ipynb](notebooks/04_recall.ipynb) |
| 5 | **Reflect** — Reasoning over memories, disposition traits, beliefs | [05_reflect.md](05_reflect.md) | [05_reflect.ipynb](notebooks/05_reflect.ipynb) |
| 6 | **Bank Management** — Creating/configuring banks, mission, directives | [06_banks.md](06_banks.md) | [06_banks.ipynb](notebooks/06_banks.ipynb) |
| 7 | **Mental Models & Observations** — Knowledge consolidation | [07_mental_models.md](07_mental_models.md) | [07_mental_models.ipynb](notebooks/07_mental_models.ipynb) |
| 8 | **Async & Batch** — High-throughput memory operations | [08_async_batch.md](08_async_batch.md) | [08_async_batch.ipynb](notebooks/08_async_batch.ipynb) |
| 9 | **Integrations** — Claude Code, LangChain, CrewAI, MCP, and more | [09_integrations.md](09_integrations.md) | [09_mcp_integration.ipynb](notebooks/09_mcp_integration.ipynb) |
| 10 | **Production** — Docker, PostgreSQL, scaling, monitoring | [10_production.md](10_production.md) | — |
| A | **Appendix** — Full API reference, cookbook links, glossary | [appendix.md](appendix.md) | — |

---

## Prerequisites

- **Python 3.11+**
- A running Hindsight server (Docker or pip)
- An LLM API key (OpenAI, Anthropic, Gemini, Groq, Ollama, etc.)
- **Jupyter** (for notebooks)

### Quick Setup

```bash
# 1. Start Hindsight server (Docker)
export OPENAI_API_KEY=sk-xxx
docker run -d --name hindsight --restart unless-stopped \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -v hindsight-data:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest

# 2. Install Python client
pip install hindsight-client jupyter

# 3. Verify
curl http://localhost:8888/health
```

---

## What You'll Learn

By the end of this tutorial, you will be able to:

- Run Hindsight locally via Docker or pip
- Use `retain()`, `recall()`, and `reflect()` to build agents with persistent memory
- Configure memory banks with missions, directives, and disposition traits
- Use multi-strategy retrieval (TEMPR): semantic, keyword, graph, and temporal
- Build mental models and observations that consolidate knowledge over time
- Integrate Hindsight with agent frameworks (LangChain, CrewAI, Claude Code, MCP)
- Deploy Hindsight in production with PostgreSQL and monitoring

---

## Architecture at a Glance

```
┌──────────────────────────────────────────────────┐
│                  Your AI Agent                     │
│  retain(content)  recall(query)  reflect(query)   │
└──────────┬──────────────┬──────────────┬──────────┘
           │              │              │
     ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼──────┐
     │  Extract   │  │  TEMPR    │  │  Synthesize│
     │  Entities  │  │  Search   │  │  Beliefs   │
     │  & Facts   │  │  4 paths  │  │  w/ traits │
     └─────┬─────┘  └─────┬─────┘  └─────┬──────┘
           │              │              │
     ┌─────▼──────────────▼──────────────▼──────┐
     │         Memory Bank (PostgreSQL)          │
     │  ┌────────┐ ┌────────────┐ ┌───────────┐ │
     │  │ World  │ │ Experiences│ │ Opinions  │ │
     │  │ Facts  │ │            │ │ / Models  │ │
     │  └────────┘ └────────────┘ └───────────┘ │
     └──────────────────────────────────────────┘
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Biomimetic memory** | World facts, experiences, mental models (like human memory) |
| **TEMPR retrieval** | Semantic + Keyword + Graph + Temporal, fused and reranked |
| **Retain** | LLM-powered fact extraction, entity resolution, temporal tagging |
| **Recall** | 4-strategy parallel search with reciprocal rank fusion |
| **Reflect** | Disposition-aware reasoning, belief synthesis with confidence |
| **Observation consolidation** | Auto-dedup, evidence tracking, continuous refinement |
| **Mental models** | User-curated knowledge that takes priority over raw facts |
| **54 integrations** | Claude Code, Cursor, LangChain, CrewAI, MCP, and more |
| **Production ready** | PostgreSQL, connection pooling, read replicas, Prometheus metrics |

---

## Quick Example

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Create a bank
client.create_bank(
    bank_id="tutorial",
    name="Tutorial Bank",
    mission="You are a helpful coding assistant. Remember user preferences."
)

# Store memories
client.retain(bank_id="tutorial", content="User prefers Python over JavaScript")
client.retain(bank_id="tutorial", content="Project uses FastAPI with PostgreSQL")
client.retain(bank_id="tutorial", content="Deployed on AWS ECS with Docker")

# Recall later
results = client.recall(bank_id="tutorial", query="What stack does the project use?")
for r in results.results:
    print(f"[{r.type}] {r.text}")

# Reflect - generate reasoned answer
answer = client.reflect(bank_id="tutorial", query="Suggest a logging solution")
print(answer.text)  # Will consider Python + FastAPI + AWS context
```

---

*Tutorial created June 2026 against Hindsight v0.8.x.*
