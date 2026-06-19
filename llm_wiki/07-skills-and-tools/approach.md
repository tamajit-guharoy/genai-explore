# Skills & Tools for LLM Wiki

> Skills, CLI tools, plugins, and templates that help build and maintain LLM Wikis.

## Agent-Native Skills

These are skills that run inside AI agents (Hermes, Claude Code) — they give the agent procedural knowledge for wiki operations.

### Hermes Agent: `llm-wiki` Skill

The most complete implementation. Ships with Hermes Agent.

**What it does:**
- Full three-layer architecture (SCHEMA.md, raw/, wiki/)
- Ingest workflow: capture source → extract → cross-check → write → link → index → log
- Query workflow: read index → find pages → synthesize with citations
- Lint workflow: orphans, broken links, frontmatter validation, contradictions, source drift, stale content, tag audit
- Bulk ingest: batch processing multiple sources efficiently
- Health checks: 12-point audit with severity-ranked findings
- Obsidian integration: headless sync for server-based wikis
- Log rotation: auto-detects >500 entries, suggests rotation

**How to use:**
```
you > /skills                          # verify llm-wiki is available
you > skill_view("llm-wiki")           # load the full skill
you > Build me a wiki for AI research  # start using it
```

**Skill location:** `~/.hermes/skills/research/llm-wiki/SKILL.md`

---

### Claude Code: Wiki Instructions (CLAUDE.md)

Not a formal skill, but you can create a `CLAUDE.md` in your wiki root:

```markdown
# Wiki Conventions (follow these when ingesting sources)

## Architecture
- raw/ — immutable sources (never edit)
- entities/ — people, companies, products
- concepts/ — ideas, techniques, topics
- comparisons/ — side-by-side analyses

## Frontmatter (required on every page)
---
title: ...
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison
tags: [from SCHEMA.md taxonomy]
sources: [raw/...]
---

## Rules
- Use [[wikilinks]] for all cross-references (min 2 per page)
- Add new pages to index.md
- Log all actions to log.md
- Never edit raw/ files
- Check SCHEMA.md for conventions before ingesting
```

---

## Standalone CLI Tools

### llm-wiki-compiler

A Node.js CLI that compiles a source directory into a concept wiki. Obsidian-compatible.

```bash
npm install -g llm-wiki-compiler
llmwiki compile sources/ --output wiki/
```

**What it does:**
- Batch processes source files into wiki pages
- Generates `[[wikilinks]]` between related concepts
- Creates index and log files
- Good for initial wiki population from many sources

**Trade-off vs agent-driven:**
- **Pro:** One command, fast batch processing
- **Con:** Static — doesn't update incrementally. Re-run on the entire source set for new pages.
- **Con:** Less nuanced extraction than an LLM agent (uses embeddings + rules, not reasoning)
- **Best for:** Bootstrapping a wiki from 50+ existing source files. Then hand off to an agent for incremental updates.

**Repo:** https://github.com/atomicmemory/llm-wiki-compiler

---

## Obsidian Plugins (Viewer Layer)

These don't build the wiki — they enhance browsing.

| Plugin | What It Does | Useful For |
|---|---|---|
| **Dataview** | Query wiki as a database: list pages by tag, type, date | Dashboard, stale page detection, tag overview |
| **Graph Analysis** | Centrality measures, community detection | Finding knowledge clusters and gaps |
| **Marp Slides** | Generate presentation slides from wiki pages | Presenting wiki findings |
| **Note Refactor** | Split long pages into smaller ones | Manual page splitting |
| **Tag Wrangler** | Rename/merge tags | Tag taxonomy maintenance |
| **Obsidian Git** | Auto-commit wiki changes to git | Backup and version history |

### Dataview Query Examples

**Dashboard — recently updated:**
```dataview
TABLE updated, type
FROM "entities" OR "concepts" OR "comparisons"
SORT updated DESC
LIMIT 15
```

**Pages needing review (contested):**
```dataview
TABLE sources, updated
FROM ""
WHERE contested = true
```

**Orphan detection (no inbound links):**
*Dataview can't do this directly — use agent lint for orphan detection.*

**Pages by confidence:**
```dataview
TABLE type, tags
FROM ""
WHERE confidence = "low"
```

**Page count by type:**
```dataview
TABLE length(rows) as Count
FROM ""
GROUP BY type
```

---

## Templates

### Entity Page Template
```markdown
---
title: "{{title}}"
created: {{date}}
updated: {{date}}
type: entity
tags: []
sources: []
---

# {{title}}

## Overview

## Key Facts

## Relationships

## Source References

## See Also
```

### Concept Page Template
```markdown
---
title: "{{title}}"
created: {{date}}
updated: {{date}}
type: concept
tags: []
sources: []
confidence: medium
---

# {{title}}

## Definition

## Current State of Knowledge

## Open Questions / Debates

## Related Concepts

## See Also
```

### Comparison Page Template
```markdown
---
title: "{{title}}"
created: {{date}}
updated: {{date}}
type: comparison
tags: [comparison]
sources: []
---

# {{title}}

## What's Being Compared & Why

## Dimensions

| Dimension | A | B |
|---|---|---|

## Synthesis / Verdict

## See Also
```

---

## NotebookLM Templates

### Pre-Ingestion Exploration Prompt

When using NotebookLM as a discovery layer before wiki ingestion:

```
I'm going to build a wiki from these sources. Before I do, help me understand:

1. What are the 10 most important entities (people, companies, products) mentioned?
2. What are the 10 most important concepts or techniques?
3. Are there any direct contradictions between sources?
4. Which sources are most central (cited by others, foundational)?
5. Which sources are peripheral (add detail but aren't essential)?

Answer with specific citations so I can verify.
```

---

## Sync & Backup Tools

### Git
```bash
cd ~/wiki
git init
git add -A
git commit -m "Initialize wiki"
# Push to private repo
git remote add origin git@github.com:you/private-wiki.git
git push -u origin main
```

### Obsidian Sync
Paid ($5–10/mo). Syncs vault across devices. Works with headless mode for servers.

### Syncthing
Free, open-source. Sync wiki directory between devices. No cloud involved.

### rclone
Sync wiki to cloud storage (S3, GCS, Dropbox, etc.).

---

## The agentskills.io Standard

The open standard for portable agent skills. Both Hermes Agent and Claude Code support it.

**Why it matters for wikis:**
- A wiki skill written for Hermes can be used with Claude Code
- Community can share wiki templates and conventions
- No lock-in — switch agents without losing your wiki workflow

**Current state (June 2026):**
- Hermes Agent: full support (ships with `llm-wiki` skill in agentskills.io format)
- Claude Code: supports skills via the standard
- Codex: partial support in progress
- Others: watching

---

## What NOT to Use

### Vector Databases (Pinecone, Weaviate, Chroma)
These are for RAG, not wikis. Different paradigm. If you want vector search over your sources, that's complementary (as a discovery layer) — but it won't build structured, interlinked wiki pages.

### Notion / Confluence
Proprietary formats with limited LLM agent APIs. You can use them as a wiki VIEWER (export to markdown, view in Notion), but they're not good as the wiki STORE — too much friction for agent read/write operations.

### Google Docs
Not structured for wiki-style interlinking. No `[[wikilinks]]`. No frontmatter. Hard for agents to navigate programmatically.

---

*Next: [08 — Pros & Cons](../08-pros-cons/)*
