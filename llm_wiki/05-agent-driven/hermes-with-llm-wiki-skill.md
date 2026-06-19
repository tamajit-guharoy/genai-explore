# Hermes Agent + llm-wiki Skill — Full Walkthrough

> A complete, step-by-step example of building an LLM Wiki with Hermes Agent's built-in `llm-wiki` skill.

## Prerequisites

- Hermes Agent installed (`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`)
- A model configured with ≥64K context (`hermes setup`)
- The `llm-wiki` skill available (ships with Hermes, no install needed)

## Step 1: Initialize the Wiki

```
you > Create an LLM wiki for my AI/ML research at ~/wiki. Follow Karpathy's
      pattern — create the full directory structure, SCHEMA.md, and index.md.
```

Hermes (using `llm-wiki` skill):
→ Creates `~/wiki/` with raw/, entities/, concepts/, comparisons/, queries/
→ Writes SCHEMA.md customized for AI/ML domain
→ Writes initial index.md and log.md
→ Reports: "Wiki initialized at ~/wiki with AI/ML domain schema."

## Step 2: Ingest Your First Source

```
you > Ingest this article into my wiki:
      https://karpathy.github.io/2026/04/02/llm-wiki/
```

Hermes:
1. Calls `web_extract(url)` → gets markdown of the article
2. Saves to `raw/articles/karpathy-llm-wiki-2026.md` with frontmatter + sha256
3. Reads SCHEMA.md for conventions
4. Reads index.md for existing pages (empty — first source)
5. Extracts: entity "Andrej Karpathy", concept "LLM Wiki", concept "RAG"
6. Creates `entities/andrej-karpathy.md`
7. Creates `concepts/llm-wiki-pattern.md`
8. Creates `comparisons/llm-wiki-vs-rag.md`
9. Cross-references all three with `[[wikilinks]]`
10. Updates index.md with all new pages
11. Appends to log.md

Reports:
```
Ingested: Karpathy's LLM Wiki article
Created 3 pages:
  - entities/andrej-karpathy.md — AI researcher, creator of LLM Wiki pattern
  - concepts/llm-wiki-pattern.md — Agent-built personal knowledge bases
  - comparisons/llm-wiki-vs-rag.md — Wiki vs vector search comparison
```

## Step 3: Ingest a Second Source (Compounding)

```
you > Save this transcript to raw/ and ingest it:
      https://www.youtube.com/watch?v=example-karpathy-lex
```

Hermes:
1. Extracts YouTube transcript via `web_extract`
2. Saves to `raw/transcripts/karpathy-lex-fridman.md`
3. Reads index.md — sees existing pages for Karpathy, LLM wiki pattern
4. Extracts: mentions of "Hermes Agent", "Claude Code", "persistent memory"
5. Updates `entities/andrej-karpathy.md` — adds his views on agents, memory
6. Creates `entities/nous-research.md` — Karpathy mentioned Hermes Agent
7. Creates `entities/anthropic.md` — mentioned Claude Code
8. Creates `concepts/ai-agents.md` — the broader discussion
9. Updates `concepts/llm-wiki-pattern.md` — adds direct quotes from interview
10. Searches for all entities: finds references to "OpenAI" — creates `entities/openai.md`
11. Cross-references everything with `[[wikilinks]]`
12. Updates index.md
13. Appends to log.md

Reports:
```
Ingested: Karpathy on Lex Fridman
Created 4 pages: nous-research, anthropic, openai, ai-agents
Updated 2 pages: andrej-karpathy, llm-wiki-pattern
Total wiki: 10 pages
```

Notice: a second source **didn't just add 1 page** — it triggered 6 file changes. This is the compounding effect.

## Step 4: Bulk Ingest (Batch Mode)

```
you > Ingest all 5 papers in raw/papers/ at once.
```

Hermes:
1. Reads all 5 files
2. Extracts entities and concepts across ALL sources (one extraction pass, not 5)
3. Checks existing pages for everything extracted (one search pass, not N)
4. Creates/updates pages in one batch (avoids updating the same page 5 times)
5. Updates index.md once at the end
6. Writes one log entry

Much more efficient than ingesting one-by-one.

## Step 5: Query the Wiki

```
you > What does my wiki know about attention mechanisms?
```

Hermes:
1. Reads index.md → finds `concepts/attention-mechanism.md`
2. Reads the page → finds [[transformer-architecture]] wikilink
3. Reads `concepts/transformer-architecture.md` → finds references to GPT-4, Claude
4. Reads `entities/openai.md` for GPT-4 context
5. Synthesizes answer: "Your wiki covers attention from Vaswani et al. (2017)..."
6. Notes: this was filed in `queries/` as it's a substantial question

## Step 6: Health Check

```
you > Lint my wiki.
```

Hermes:
1. Scans all pages for orphans (zero inbound `[[wikilinks]]`)
2. Finds broken wikilinks (pointing to non-existent pages)
3. Validates all frontmatter (required fields present, tags in taxonomy)
4. Checks index.md completeness (every page listed)
5. Checks for contradictions (pages with conflicting claims)
6. Flags stale pages (not updated in 90+ days despite new relevant sources)
7. Checks raw/ files for drift (sha256 mismatch)
8. Checks log.md size (>500 entries → suggest rotation)

Reports:
```
Wiki Health: 2 issues found
  BROKEN: entities/gpt-5.md references [[constitutional-ai]] which doesn't exist
  STALE: concepts/rnn-architectures.md last updated 2025-03 — 15 months ago
  NOTE: 15 pages healthy, no orphans, all frontmatter valid.
```

## Step 7: Schedule Auto-Maintenance

```
you > Every Sunday at 9am, lint my wiki and message me on Telegram with any issues.
```

Hermes (using built-in cron):
→ Creates scheduled job "wiki-health-check"
→ Every Sunday 9am: reads SCHEMA.md, runs full lint, delivers report via Telegram
→ You wake up Monday to a message: "Wiki healthy. 0 issues. 23 pages, 142 wikilinks."

## Step 8: Cross-Platform Ingestion

```
[On your phone, in Telegram]
you > Found a great article: https://example.com/transformer-variants-2026
      Save it to my wiki.
```

Hermes (via messaging gateway):
→ Receives message on Telegram
→ Recognizes it's for the wiki (same agent, same memory, same skills)
→ Ingests the article → creates new pages → reports back on Telegram
→ Next time you open the terminal: pages are already there in the wiki

## The Power: 6 Months Later

After 6 months of this workflow:
- **100–200 wiki pages** covering your research domain
- **Deeply interlinked** — hundreds of `[[wikilinks]]` forming a knowledge graph
- **Self-maintained** — weekly health checks catch issues early
- **Indexed and searchable** — find anything in seconds
- **Provenance tracked** — every claim traces to a source
- **Contradictions flagged** — you know what's contested vs settled
- **Accessible anywhere** — terminal, phone (Telegram), Obsidian (viewer)

And you wrote **zero wiki pages** yourself. You just fed sources and asked questions.

## Integration with Obsidian

Point Obsidian at `~/wiki` to browse the graph:

```
~/wiki/
├── entities/    → Red nodes in graph view
├── concepts/    → Blue nodes
├── comparisons/ → Green nodes
└── raw/         → Gray nodes
```

Open graph view, zoom out, see your entire knowledge domain as a network. Local clusters = areas you've researched deeply. Sparse areas = gaps to fill.

## Troubleshooting

| Issue | Fix |
|---|---|
| Agent creates duplicate pages | Re-read SCHEMA.md — might need clearer page thresholds |
| Pages missing frontmatter | Ask "lint my wiki" — it'll flag and offer to fix |
| Agent misses cross-references | Explicitly ask: "check cross-references for the last 3 pages created" |
| Wiki growing too fast, hard to navigate | Add sub-sections to index.md; increase page split threshold |
| log.md getting huge | Lint will suggest rotation; say yes |

---

*Next: [06 — Combinations](../06-combinations/)*
