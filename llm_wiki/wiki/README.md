# Example Wiki — AI/ML Research

> This is a fully-built example LLM Wiki, created from the sample sources in [../raw/](../raw/).
> It demonstrates the final product after ingesting 5 sources: the structure, cross-references, frontmatter, and navigation.

## Wiki Structure

```
wiki/
├── SCHEMA.md                          # Constitution — rules and conventions
├── index.md                           # Every page cataloged with one-line summary
├── log.md                             # Chronological action log
├── entities/                          # People, companies, products
│   ├── openai.md                      # Creator of GPT and Codex
│   ├── anthropic.md                   # Creator of Claude and Claude Code
│   ├── nous-research.md               # Creator of Hermes Agent
│   └── andrej-karpathy.md            # AI researcher, LLM Wiki creator
├── concepts/                          # Ideas, techniques, topics
│   ├── ai-agents.md                   # The agent paradigm
│   ├── attention-mechanism.md         # Core Transformer operation
│   ├── transformer-architecture.md    # Foundation of modern LLMs
│   ├── tool-use.md                    # Agent capability to invoke tools
│   └── llm-wiki-pattern.md           # Karpathy's knowledge base pattern
├── comparisons/                       # Side-by-side analyses
│   ├── agent-comparison-2026.md       # Claude Code vs Codex vs Hermes vs Manus
│   └── llm-wiki-vs-rag.md            # Wiki-based vs vector search knowledge
└── queries/                           # Filed answers to important questions
    └── (empty — populated as questions are asked)
```

## How to Use This Example

1. **Read SCHEMA.md** — understand the conventions
2. **Read index.md** — see the full catalog
3. **Pick a page** — start with [concepts/llm-wiki-pattern.md](concepts/llm-wiki-pattern.md) or [entities/andrej-karpathy.md](entities/andrej-karpathy.md)
4. **Follow wikilinks** — `[[wikilinks]]` connect related pages
5. **Check log.md** — see the ingestion history

## Key Metrics

| Metric | Value |
|---|---|
| Total pages | 11 |
| Entities | 4 (OpenAI, Anthropic, Nous Research, Andrej Karpathy) |
| Concepts | 5 (AI agents, Attention, Transformer, Tool use, LLM Wiki) |
| Comparisons | 2 (Agent comparison, Wiki vs RAG) |
| Sources ingested | 5 (3 articles, 1 paper, 1 transcript) |
| Cross-references (wikilinks) | 60+ |
| Contradictions flagged | 0 |
| Pages with confidence: high | 8 |
| Pages with confidence: medium | 3 |

## Source Provenance

Every claim can be traced back to a raw source. Pages synthesizing 3+ sources use `^[raw/...]` markers to show which source each claim comes from. This is the audit trail that makes the wiki trustworthy.

## Try It Yourself

1. Copy this entire directory to `~/wiki/`
2. Open in Obsidian: `Obsidian → Open folder as vault → ~/wiki`
3. Browse Graph View to see the knowledge network
4. Follow wikilinks between pages
5. Add a new source to `raw/` and try ingesting it manually
6. Or: point Hermes Agent at this wiki and say "ingest this new source"
