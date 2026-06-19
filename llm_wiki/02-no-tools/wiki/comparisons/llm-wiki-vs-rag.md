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
Two approaches for using AI with a personal document collection. This comparison helps you choose the right pattern for your use case.

## How They Work

### RAG (Retrieval-Augmented Generation)
1. User asks a question
2. System converts question to embedding vector
3. Searches vector database for similar document chunks
4. Injects top-K chunks into LLM context
5. LLM generates answer from those chunks

### LLM Wiki (Karpathy Pattern)
1. Agent reads source documents up front
2. Agent writes structured wiki pages (entities, concepts, comparisons)
3. Agent cross-references pages with `[[wikilinks]]`
4. Agent maintains consistency as new sources arrive
5. User queries by navigating wiki pages (or asking the agent to read them)

## Head-to-Head

| Dimension | RAG | LLM Wiki |
|---|---|---|
| **Retrieval** | Semantic similarity search | Navigate interlinked pages |
| **Synthesis** | Re-derived on every query | Compiled once, kept current |
| **Cross-references** | None — chunks are isolated | `[[wikilinks]]` connect related concepts |
| **Contradictions** | Both sides returned without flagging | Explicitly marked in frontmatter |
| **Compounding value** | Zero — every query starts fresh | Accumulates with every source |
| **Setup effort** | Medium (vector DB, embedding model) | Low (markdown files, any editor) |
| **Query flexibility** | Very flexible — ask anything | Good for the domain; limited outside it |
| **Source fidelity** | Direct chunk retrieval | Filtered through agent's summary (risk of omission) |
| **Cost per query** | Embedding + LLM tokens | LLM reading pages (typically cheaper) |
| **Maintenance** | Re-index on source changes | Agent updates wiki pages |
| **Freshness** | As fresh as the index | As fresh as the last agent run |
| **Auditability** | Opaque — "why this chunk?" | Traceable — provenance markers `^[raw/file.md]` |

## When RAG Wins

- **Large, static corpora** — 10,000+ documents you'll query but rarely add to
- **Exploratory queries** — "find anything about X" when you don't know what's there
- **One-off analysis** — ingest a document set for a single project
- **Need exact passages** — legal documents, regulations where verbatim text matters
- **No curation effort** — don't want to review/verify agent-written pages

## When LLM Wiki Wins

- **Ongoing research** — you'll add sources for months/years
- **Want compounding value** — each new source makes the whole wiki better
- **Need synthesis** — want the system to connect dots across sources
- **Value auditability** — want to trace claims back to specific sources
- **Prefer structured knowledge** — encyclopedia-style reference over search results
- **Multiple readers** — share the wiki with colleagues

## Can You Use Both?

Yes — they're complementary, not mutually exclusive:

```
RAG for: "Find all passages about transformer attention in my 500 papers"
Wiki for: "What do we know about attention mechanisms across all my research?"
```

Some practitioners use RAG as the *discovery layer* and the Wiki as the *synthesis layer*. RAG finds relevant passages; the agent then updates wiki pages incorporating the new findings.

## The Cost Question

For a corpus of 50 documents queried 100 times:
- **RAG:** ~100 embedding lookups + ~100 LLM synthesis calls
- **Wiki:** ~1 agent run to build the wiki (costly but one-time) + 100 cheap page reads

Wiki amortizes better the more you query the same domain. RAG is better for one-off or highly varied queries.

## Karpathy's Verdict
From his tweet: "This is different from RAG. RAG rediscovers from scratch on every query. A wiki compiles knowledge once and keeps it current. It's the difference between searching a library and having a research assistant who has already read everything and written you a synthesis." ^[raw/articles/karpathy-llm-wiki-tweet.md]

## See Also
- [[llm-wiki-pattern]] — the full pattern
- [[ai-agents]] — the agents that power wikis
- [[agent-comparison-2026]] — which agents are best for wiki-building
