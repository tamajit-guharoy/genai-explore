# What is an LLM Wiki?

## The Origin: Karpathy's Tweet (April 2, 2026)

On April 2, 2026, Andrej Karpathy posted a thread on X that accumulated **19.6 million views, 55K likes, and 6.5K reposts**. Here's the core of what he said:

> "Something I'm finding very useful recently: using LLMs to build personal knowledge bases for various topics of research interest. In this way, a large fraction of my recent token throughput is going less into manipulating code, and more into manipulating knowledge."

He followed up with a [GitHub Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) that laid out the full architecture. The numbers he shared: a single research topic had grown to **~100 articles and ~400,000 words** — longer than most PhD dissertations — without him writing a single word directly.

## The Core Idea

> Instead of you maintaining a knowledge base and occasionally asking an AI questions, an AI maintains the knowledge base and you occasionally read it.

This is the inversion. Traditional workflows:

```
You → Read sources → Write notes → Organize → Occasionally ask AI
```

Karpathy's LLM Wiki:

```
You → Feed sources to agent → Agent writes/links/maintains wiki → You query the wiki
```

## The Three-Layer Architecture

```
raw/       → Layer 1: Immutable source material
wiki/      → Layer 2: LLM-generated knowledge pages
SCHEMA.md  → Layer 3: Rules that govern how the wiki operates
```

### Layer 1 — Raw Sources (`raw/`)

These are **immutable**. The agent reads them but never modifies them. They are the ground truth.

```
raw/
├── articles/       # Web articles, blog posts, clippings
├── papers/         # Academic papers, PDFs, arxiv extracts
├── transcripts/    # YouTube transcripts, podcasts, interviews
└── assets/         # Images, diagrams referenced by sources
```

Every raw file gets a small YAML frontmatter with `source_url`, `ingested` date, and `sha256` hash of content — so re-ingesting the same URL can detect drift and skip unchanged content.

### Layer 2 — Wiki Pages (`entities/`, `concepts/`, `comparisons/`, `queries/`)

These are **agent-owned**. The agent creates, updates, and cross-references them. Types:

| Type | Purpose | Example |
|---|---|---|
| `entities/` | People, orgs, products, models | `entities/openai.md`, `entities/andrej-karpathy.md` |
| `concepts/` | Topics, ideas, techniques | `concepts/attention-mechanism.md` |
| `comparisons/` | Side-by-side analyses | `comparisons/llm-wiki-vs-rag.md` |
| `queries/` | Filed answers to important questions | `queries/best-transformer-variant-2026.md` |

Every wiki page has YAML frontmatter with `title`, `created`, `updated`, `type`, `tags`, `sources`, and optional quality signals (`confidence`, `contested`, `contradictions`).

### Layer 3 — Schema (`SCHEMA.md`)

The constitution. It defines:

- **Domain:** What this wiki covers
- **Conventions:** Naming, linking rules, frontmatter requirements
- **Tag taxonomy:** The allowed tags — no freeform tag sprawl
- **Page thresholds:** When to create a page (2+ source mentions) vs. add to existing vs. skip
- **Update policy:** How to handle contradictions, superseded content, archiving

### Supporting Files

```
index.md     # Sectioned catalog of every wiki page with one-line summaries
log.md       # Append-only chronological action log (ingest, update, lint, query)
```

## Why This Beats RAG for Personal Knowledge

| Dimension | RAG (Vector Search) | LLM Wiki |
|---|---|---|
| **Retrieval** | Semantic search over raw chunks | Navigate structured, interlinked pages |
| **Synthesis** | Re-derived per query | Compiled once, kept current |
| **Cross-references** | None (chunks are isolated) | Built-in via `[[wikilinks]]` |
| **Contradictions** | Silently returned (both sides) | Explicitly flagged in frontmatter |
| **Compounding** | Zero — every query starts fresh | Accumulates over time |
| **Auditability** | Opaque — "why this chunk?" | Traceable — `^[raw/article.md]` provenance markers |

RAG is great for "find relevant passages in a corpus I'll query once." A wiki is better for "I'm going to think about this topic for months/years and want my understanding to compound."

## What the Agent Actually Does

When you feed a new source to the wiki:

1. **Capture** — Save raw source to `raw/` with frontmatter and sha256
2. **Extract** — Identify entities, concepts, claims, relationships
3. **Cross-check** — Search existing wiki pages for mentioned entities/concepts
4. **Write/Update** — Create new pages (if 2+ mentions), update existing ones, add info
5. **Cross-reference** — Ensure new and existing pages link to each other (min 2 outbound links per page)
6. **Update navigation** — Add new pages to `index.md`, append to `log.md`
7. **Flag issues** — Note contradictions, mark low-confidence claims

A single source can trigger updates across 5–15 wiki pages. This is the *compounding effect*.

## Division of Labor

| Who | Responsibility |
|---|---|
| **You (human)** | Curate sources, direct research, review flagged contradictions, read the wiki |
| **Agent (LLM)** | Summarize, cross-reference, write pages, maintain consistency, run health checks |

The human is the editor-in-chief, not the writer.

## The Minimal Viable Wiki

You don't need the full structure to start. A minimal LLM wiki is:

```
~/wiki/
├── SCHEMA.md       # Even just 10 lines defining the domain and conventions
├── index.md        # Can start as an empty header
├── raw/            # One article you care about
└── concepts/       # One page the agent writes about that article
```

That's it. Four files. It grows from there.

## Key Principles

1. **Markdown is the universal format.** Any tool can read it. No lock-in.
2. **`[[wikilinks]]` are the connective tissue.** They make the graph navigable.
3. **Frontmatter enables automation.** Tags, dates, confidence — all machine-readable.
4. **Raw sources are sacred.** Never edited. Corrections go in wiki pages.
5. **The schema constrains the agent.** Without rules, quality decays.
6. **The log is your audit trail.** Every action is timestamped and explainable.
7. **It's a living document.** Unlike a static summary, it evolves with new information.

## The "Second Brain" Connection

Tiago Forte's "Building a Second Brain" popularized the idea of external knowledge management. Karpathy's LLM Wiki is that idea, but with one crucial difference: **you're not the one doing the building**. The agent does the capturing, organizing, distilling, and expressing (Forte's CODE framework). You just feed it sources and ask questions.

The maintenance burden that kills most second-brain attempts? Gone. The agent handles it.

---

*Next: [02 — Manual Implementation (No Tools)](../02-no-tools/approach.md)*
