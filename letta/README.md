# Letta (formerly MemGPT) — Comprehensive Tutorial

> **Letta** is an open-source platform for building **stateful AI agents** with
> advanced memory that can learn and self-improve over time. Originally published
> as the [MemGPT paper](https://arxiv.org/abs/2310.08560) from UC Berkeley (2023),
> it was rebranded to Letta as the project grew into a full agent framework.

---

## Table of Contents

| # | File | Focus | Level |
|---|------|-------|-------|
| 01 | `markdown/01_letta_fundamentals.md` | Memory architecture, OS-inspired hierarchy, core concepts | Beginner |
| 02 | `markdown/02_getting_started.md` | Installation, API keys, creating your first agent | Beginner |
| 03 | `markdown/03_memory_blocks.md` | Core memory blocks (human, persona, custom), read/write patterns | Intermediate |
| 04 | `markdown/04_archival_memory.md` | Passages, semantic search, long-term storage | Intermediate |
| 05 | `markdown/05_tools_and_functions.md` | Custom tools, function calling, server-side tools | Intermediate |
| 06 | `markdown/06_multi_agent_systems.md` | Multiple agents, shared memory, agent collaboration | Advanced |
| 07 | `markdown/07_advanced_patterns.md` | Agent types, compaction, templates, sleep-time compute | Advanced |
| 08 | `markdown/08_letta_code_intro.md` | Letta Code CLI / Agent SDK V2 (MemFS, skills, subagents) | Advanced |
| 09 | `markdown/09_production_deployment.md` | Self-hosting, Docker, best practices | Advanced |

### Standalone Config Files

| File | Purpose |
|------|---------|
| `configs/docker-compose.yml` | Production Docker Compose stack (Letta + optional Postgres/Redis) |
| `configs/.env.example` | All environment variables with documentation |
| `configs/letta_agent_service.py` | Production-ready Python wrapper with retry logic and health checks |

---

## Why Markdown, Not Jupyter?

This tutorial was originally published as `.ipynb` notebooks. We converted to markdown because:

- **Notebook 01** has zero executable code — it was pure documentation trapped in JSON
- **Notebooks 02–07** require a live Letta API key — readers can't actually run them interactively
- **Notebook 08** mixes bash, TypeScript, and YAML — none of which execute in a Python kernel
- **Notebook 09** is configuration documentation — `docker-compose.yml` and `.env` belong as standalone files
- Markdown is readable on GitHub, diffable in git, and works with any editor

The original `.ipynb` files are preserved in the `legacy/` directory.

---

## Key Concepts at a Glance

```
┌─────────────────────────────────────────────────────┐
│                 LETTA MEMORY HIERARCHY               │
├─────────────────┬───────────────────────────────────┤
│  MAIN CONTEXT   │  EXTERNAL CONTEXT                 │
│  (RAM analogy)  │  (Disk analogy)                   │
├─────────────────┼───────────────────────────────────┤
│ • System prompt │  • Recall Memory                  │
│ • Memory Blocks │    (recent message history,       │
│   (human,       │     searchable on demand)         │
│    persona,     │                                   │
│    custom)      │  • Archival Memory                │
│ • Recent msgs   │    (long-term knowledge base,     │
│                 │     vector-searchable passages)   │
└─────────────────┴───────────────────────────────────┘
```

- **Memory Blocks** — Labeled, persistent strings the agent can read/write via tool calls.  Standard labels: `human` (what the agent knows about the user), `persona` (the agent's self-description).
- **Recall Memory** — Searchable recent conversation history.  Agents can query "what did we discuss last week?"
- **Archival Memory** — Vector-store-backed long-term knowledge.  Agents insert and search passages.

---

## Quick Install

```bash
# Python SDK (V1 — stable, memory blocks + archival memory + server tools)
pip install letta-client

# Or the older package name:
pip install letta

# Letta Code CLI (V2 — Node.js, MemFS, skills, subagents)
npm install -g @letta-ai/letta-code
```

**API Key**: Sign up at https://app.letta.com → API Keys → `export LETTA_API_KEY='...'`

---

## Quick Start: Production Deployment

```bash
cd configs/
cp .env.example .env
# Edit .env with your API keys
docker-compose up -d
```

---

## Sources

- [Letta GitHub](https://github.com/letta-ai/letta) — 16k+ stars
- [Letta Docs](https://docs.letta.com)
- [MemGPT Paper (arXiv 2310.08560)](https://arxiv.org/abs/2310.08560)
- [Letta Blog — Agent Memory](https://www.letta.com/blog/agent-memory)

*Tutorial created June 2026 against Letta v0.16.x (V1 SDK) and Agent SDK beta (V2).*
*Converted from Jupyter notebooks to markdown + standalone configs June 2026.*
