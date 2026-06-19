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
A knowledge management pattern where an LLM agent builds and maintains a personal wiki of interlinked markdown files from raw source material. The human curates sources and directs research; the agent does all writing, cross-referencing, and maintenance. Popularized by [[andrej-karpathy]] in April 2026. ^[raw/articles/karpathy-llm-wiki-tweet.md]

## Core Principle

> "Instead of you maintaining a knowledge base and occasionally asking an AI questions, an AI maintains the knowledge base and you occasionally read it."

This inverts the traditional note-taking workflow. The human is editor-in-chief, not writer.

## Three-Layer Architecture

```
raw/       → Immutable source material (articles, papers, transcripts)
wiki/      → Agent-written interlinked markdown pages (entities, concepts, comparisons)
SCHEMA.md  → Rules governing structure, conventions, and tag taxonomy
```

### Layer 1: Raw Sources
Preserved verbatim. Never edited. Every file has frontmatter with `source_url`, `ingested` date, and `sha256` for drift detection.

### Layer 2: Wiki Pages
Organized by type:
- `entities/` — People, companies, products, models
- `concepts/` — Ideas, techniques, topics
- `comparisons/` — Side-by-side analyses
- `queries/` — Filed answers to important questions

Every page has YAML frontmatter, `[[wikilinks]]` to other pages (min 2 outbound), and provenance markers (`^[raw/file.md]`).

### Layer 3: Schema
The constitution. Defines domain, naming conventions, allowed tags, page thresholds, update policy, and contradiction handling.

## Workflow

1. **Drop** a source into `raw/`
2. **Ask** the agent to ingest it
3. **Agent** reads source, extracts entities/concepts, checks existing pages, creates/updates wiki pages, cross-references, updates index and log
4. **Repeat** for each new source

One source often triggers updates across 5–15 wiki pages — the compounding effect.

## Why It Beats RAG

| Dimension | RAG | LLM Wiki |
|---|---|---|
| Retrieval | Vector search over raw chunks | Navigate structured pages |
| Synthesis | Re-derived every query | Compiled once, kept current |
| Cross-references | None (chunks isolated) | Built-in via wikilinks |
| Contradictions | Silently returned | Explicitly flagged |
| Compounding | Zero | Accumulates over time |

## Implementations

- **[[hermes-agent]]** — Ships with `llm-wiki` skill that implements the full pattern
- **[[claude-code]]** — Can follow the pattern using custom instructions or skills
- **llm-wiki-compiler** — Standalone Node.js CLI for batch compilation
- **Manual** — Any text editor, just slower (see [manual approach](../02-no-tools/approach.md))

## Karpathy's Results
One research topic grew to ~100 pages, ~400K words without him writing a single word. He queries the wiki through his IDE using an agent that reads multiple files. ^[raw/articles/karpathy-llm-wiki-tweet.md]

## See Also
- [[wiki-health-check]] — linting and maintenance procedures
- [[llm-wiki-vs-rag]] — detailed comparison
- [[andrej-karpathy]] — creator of the pattern
- [[ai-agents]] — the agents that power wikis
