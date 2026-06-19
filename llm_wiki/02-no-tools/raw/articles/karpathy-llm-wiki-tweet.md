---
source_url: https://x.com/karpathy/status/2039805659525644595
ingested: 2026-06-19
sha256: placeholder
---

# Andrej Karpathy's LLM Wiki Tweet (April 2, 2026)

## Original Tweet Thread

Something I'm finding very useful recently: using LLMs to build personal knowledge bases for various topics of research interest. In this way, a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge.

The setup is something like a small personal wiki of markdown files, which I only read (but rarely write) and instead the LLM writes and maintains. I interact with the wiki with my IDE (cursor), talking to an agent that can both read and write many files simultaneously.

The architecture is something like 3 folders:

- `raw/` — source material (articles, papers, transcripts, etc.) that I collect. The LLM only reads these.
- `wiki/` — the LLM writes and maintains interlinked markdown pages here. This is what I read.
- `SCHEMA.md` — defines the structure, conventions, and rules for the wiki. The LLM follows this.

When I find a new source, I drop it in raw/, and ask the LLM to ingest it. It reads the source, extracts entities and concepts, checks existing wiki pages, creates new pages or updates existing ones, cross-references everything, and updates the index.

The magic: after a few weeks of this, I have a wiki on a topic that is 100+ pages, 400K+ words, deeply interlinked, with contradictions flagged and confidence levels marked. I didn't write a single word of it. But I can query it and it knows everything I've collected on that topic.

This is different from RAG. RAG rediscovers from scratch on every query. A wiki compiles knowledge once and keeps it current. It's the difference between searching a library and having a research assistant who has already read everything and written you a synthesis.

## Follow-up Tweet

Important to note that the LLM writes and maintains all of the data of the wiki, I rarely touch it directly. I've played with a few Obsidian plugins to render and view data in other ways (e.g. Marp for slides).

## Community Response

The tweet spawned:
- A detailed GitHub Gist with the full specification
- Multiple community implementations (llm-wiki-compiler, Obsidian templates)
- Integration into AI agent platforms (Hermes Agent added an `llm-wiki` skill)
- Debate about whether this pattern makes personal RAG pipelines obsolete
