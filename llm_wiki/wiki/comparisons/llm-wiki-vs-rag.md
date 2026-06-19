---
title: LLM Wiki vs RAG
created: 2026-06-19
updated: 2026-06-19
type: comparison
tags: [comparison]
sources:
  - raw/articles/karpathy-llm-wiki-tweet.md
  - raw/articles/ai-agent-landscape-2026.md
confidence: high
---

# LLM Wiki vs RAG — When to Use Each

## What's Being Compared
Two approaches for using AI with personal documents: RAG (vector search over raw chunks) vs LLM Wiki (agent-built structured knowledge base).

## How They Work

### RAG
User asks → embed to vector → search vector DB → inject top-K chunks → LLM generates answer

### LLM Wiki
Agent reads sources upfront → writes structured wiki pages → cross-references → maintains. User queries by navigating pages.

## Comparison

| Dimension | RAG | LLM Wiki |
|---|---|---|
| Retrieval | Semantic similarity search | Navigate interlinked pages |
| Synthesis | Re-derived every query | Compiled once, kept current |
| Cross-references | None | `[[wikilinks]]` |
| Contradictions | Silent | Explicitly flagged |
| Compounding | Zero | Accumulates |
| Setup effort | Medium (vector DB) | Low (markdown files) |
| Cost per query | Embedding + LLM | Reading pages (cheaper) |
| Auditability | Opaque | Traced via `^[raw/...]` |

## When RAG Wins
- Large static corpora (10K+ docs)
- Exploratory "find anything about X" queries
- One-off analysis
- Need exact verbatim passages

## When Wiki Wins
- Ongoing research (add sources for months/years)
- Want compounding value
- Need cross-source synthesis
- Value traceable claims

## Can You Use Both?
Yes — complementary. RAG for discovery ("find relevant passages"), Wiki for synthesis ("what do we know?").

## Karpathy's Verdict
"This is different from RAG. RAG rediscovers from scratch on every query. A wiki compiles knowledge once and keeps it current. It's the difference between searching a library and having a research assistant who has already read everything and written you a synthesis." ^[raw/articles/karpathy-llm-wiki-tweet.md]

## See Also
- [[llm-wiki-pattern]]
- [[ai-agents]]
