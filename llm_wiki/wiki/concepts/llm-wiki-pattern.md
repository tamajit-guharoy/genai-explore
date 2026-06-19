---
title: LLM Wiki Pattern
created: 2026-06-19
updated: 2026-06-19
type: concept
tags: [concept, technique]
sources:
  - raw/articles/karpathy-llm-wiki-tweet.md
  - raw/transcripts/karpathy-lex-fridman.md
  - raw/articles/ai-agent-landscape-2026.md
confidence: high
---

# LLM Wiki Pattern

## Definition
A knowledge management pattern where an LLM agent builds and maintains a personal wiki of interlinked markdown files from raw source material. The human curates sources; the agent writes, cross-references, and maintains. Popularized by [[andrej-karpathy]] in April 2026. ^[raw/articles/karpathy-llm-wiki-tweet.md]

## Core Principle
> "Instead of you maintaining a knowledge base and occasionally asking an AI questions, an AI maintains the knowledge base and you occasionally read it."

## Three-Layer Architecture
```
raw/       → Immutable source material (articles, papers, transcripts)
wiki/      → Agent-written interlinked pages (entities, concepts, comparisons)
SCHEMA.md  → Rules governing structure and conventions
```

## Workflow
1. Drop a source into `raw/`
2. Ask the agent to ingest it
3. Agent reads → extracts entities/concepts → checks existing → writes/updates pages → cross-references → updates index → logs

One source often triggers 5–15 page changes — the compounding effect.

## Why It Beats RAG
| Dimension | RAG | LLM Wiki |
|---|---|---|
| Retrieval | Vector search over chunks | Navigate interlinked pages |
| Synthesis | Re-derived per query | Compiled once, kept current |
| Cross-refs | None | Built-in `[[wikilinks]]` |
| Compounding | Zero | Accumulates over time |

## Implementations
- [[hermes-agent]] — Built-in `llm-wiki` skill
- [[claude-code]] — Via custom instructions (CLAUDE.md)
- llm-wiki-compiler — Standalone CLI
- Manual — Any text editor

## Karpathy's Results
One topic → ~100 pages, ~400K words. He never wrote a word. ^[raw/articles/karpathy-llm-wiki-tweet.md]

## See Also
- [[andrej-karpathy]] — creator
- [[llm-wiki-vs-rag]] — detailed comparison
- [[ai-agents]] — the agents that power wikis
