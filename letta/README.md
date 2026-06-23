# Letta (formerly MemGPT) — Comprehensive Tutorial

> **Letta** is an open-source platform for building **stateful AI agents** with
> advanced memory that can learn and self-improve over time. Originally published
> as the [MemGPT paper](https://arxiv.org/abs/2310.08560) from UC Berkeley (2023),
> it was rebranded to Letta as the project grew into a full agent framework.

---

## Table of Contents

| # | Notebook | Focus | Level |
|---|----------|-------|-------|
| 01 | `01_letta_fundamentals.ipynb` | Memory architecture, OS-inspired hierarchy, core concepts | Beginner |
| 02 | `02_getting_started.ipynb` | Installation, API keys, creating your first agent | Beginner |
| 03 | `03_memory_blocks.ipynb` | Core memory blocks (human, persona, custom), read/write patterns | Intermediate |
| 04 | `04_archival_memory.ipynb` | Passages, semantic search, long-term storage | Intermediate |
| 05 | `05_tools_and_functions.ipynb` | Custom tools, function calling, server-side tools | Intermediate |
| 06 | `06_multi_agent_systems.ipynb` | Multiple agents, shared memory, agent collaboration | Advanced |
| 07 | `07_advanced_patterns.ipynb` | Agent types, compaction, templates, sleep-time compute | Advanced |
| 08 | `08_letta_code_intro.ipynb` | Letta Code CLI / Agent SDK V2 (MemFS, skills, subagents) | Advanced |
| 09 | `09_production_deployment.ipynb` | Self-hosting, Docker, best practices | Advanced |

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

## Sources

- [Letta GitHub](https://github.com/letta-ai/letta) — 16k+ stars
- [Letta Docs](https://docs.letta.com)
- [MemGPT Paper (arXiv 2310.08560)](https://arxiv.org/abs/2310.08560)
- [Letta Blog — Agent Memory](https://www.letta.com/blog/agent-memory)

*Tutorial created June 2026 against Letta v0.16.x (V1 SDK) and Agent SDK beta (V2).*
