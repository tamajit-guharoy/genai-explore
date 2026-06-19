# Approach 3: Obsidian as Viewer

> Use Obsidian as the display layer on top of your LLM Wiki. Obsidian doesn't build the wiki — it makes it beautiful to browse.

## What Obsidian Brings

Obsidian is a markdown-based knowledge management app. Since an LLM Wiki is just a directory of markdown files, it works as an Obsidian vault out of the box. No conversion, no import.

### Features That Enhance a Wiki

| Obsidian Feature | What It Does for Your Wiki |
|---|---|
| **Graph View** | Visualizes `[[wikilinks]]` as a network. See which pages are central, which are isolated, where knowledge clusters form. |
| **Backlinks Panel** | Every page shows what links to it. Spot orphans instantly — pages with no inbound links need attention. |
| **Dataview Plugin** | Query your wiki like a database: `TABLE tags FROM "entities" WHERE contains(tags, "company")` |
| **Search** | Full-text search across all wiki pages (faster than grep for interactive browsing) |
| **Marp Slides** | Generate presentation slides from wiki pages (Karpathy mentioned using this) |
| **Canvas** | Arrange wiki pages on an infinite whiteboard — good for brainstorming the wiki structure |
| **Templates** | Standard templates for entity, concept, and comparison pages (insert with one click) |

### Features That DON'T Help

| Obsidian Feature | Why It's Not the Engine |
|---|---|
| **AI plugins** | Local LLM plugins in Obsidian can summarize, but they don't do multi-file cross-referencing, health checks, or index maintenance |
| **Daily notes** | Not relevant — the wiki is topic-structured, not date-structured |
| **Community plugins** | Most are UI polish, not knowledge synthesis |

## Setup

### 1. Point Obsidian at Your Wiki Directory

```
Obsidian → Open folder as vault → Select ~/wiki/
```

That's it. Your entire wiki — SCHEMA.md, index.md, entities, concepts, comparisons, raw sources — is now browsable in Obsidian.

### 2. Enable Useful Settings

- **Settings → Files & Links → Wikilinks:** ON (uses `[[wikilinks]]`)
- **Settings → Files & Links → Default location for new attachments:** `raw/assets/`
- **Community Plugins → Install Dataview** — for querying your wiki as a database
- **Community Plugins → Install Marp Slides** — if you want to present from wiki pages

### 3. Add Templates

Create `_templates/entity.md`:

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

## See Also
```

Useful if you occasionally create pages manually between agent runs.

## Workflow: Agent + Obsidian

The correct division of labor:

```
Agent (Hermes / Claude Code):  Read raw sources → Write wiki pages → Cross-reference → Update index → Log
Obsidian:                       Browse the graph → Read pages → Search → Enjoy
```

You don't use Obsidian's AI plugins to build the wiki. You use the agent for that. Obsidian is the reading room, not the writing desk.

### Example Session

1. **Morning:** Drop 3 new papers into `raw/papers/`
2. **Agent:** "Ingest the 3 new papers in raw/papers/"
3. **Agent:** Creates/updates 8 wiki pages, cross-references, updates index
4. **Afternoon:** Open Obsidian, browse Graph View to see new knowledge clusters, read updated pages, check Dataview for any `contested: true` pages needing review

## Obsidian-Specific Optimizations

### Dataview Queries

Add a `_meta/dashboard.md` page:

```markdown
# Wiki Dashboard

## Recently Updated
```dataview
TABLE updated, type, tags
FROM "entities" OR "concepts" OR "comparisons"
SORT updated DESC
LIMIT 10
```

## Contested Pages (Needs Review)
```dataview
TABLE updated, sources
FROM ""
WHERE contested = true
```

## Orphan Pages (No Inbound Links)
*Manual check — use [[llm-wiki-pattern|lint]] procedure*
```

### Graph View Grouping

Use Obsidian's graph groups to color-code by type:
- **Red:** entities/
- **Blue:** concepts/
- **Green:** comparisons/
- **Gray:** raw/

This visually distinguishes source material from synthesized knowledge.

### Bookmarks

Bookmark frequently referenced pages:
- `SCHEMA.md` — the constitution
- `index.md` — the catalog
- `log.md` — recent activity
- Dashboard page

## Pros and Cons

### Pros
- **Beautiful browsing** — graph view, backlinks, search make the wiki a joy to explore
- **Zero lock-in** — the wiki is still just markdown files; stop using Obsidian any time
- **Visual quality control** — orphan pages jump out in graph view; stale dates visible in Dataview
- **Shareable** — Obsidian Publish can make your wiki a public website
- **Mobile** — Obsidian mobile app lets you read your wiki on the go

### Cons
- **It's just a viewer** — Obsidian doesn't build or maintain the wiki; you still need an agent or manual effort
- **Obsidian Sync costs money** — $5–10/mo for sync across devices (or use free alternatives like git)
- **Plugin maintenance** — plugins break on updates, need occasional attention
- **Graph view can be overwhelming** — 200+ page wikis produce dense, hard-to-read graphs
- **Not collaborative** — Obsidian is single-user; sharing with a team requires Publish or git

## Without an Agent: Obsidian-Only Wiki

You CAN use Obsidian alone — just manually create all the pages. This is the same as the [manual approach](../02-no-tools/approach.md) but with a prettier editor:

```
1. Read a source
2. Create entity.md with frontmatter → type manually
3. Create concept.md → type manually
4. Add [[wikilinks]] → type manually
5. Update index.md → type manually
6. Log in log.md → type manually
```

Obsidian makes steps 2–6 slightly nicer (autocomplete for wikilinks, templates, live preview) but doesn't reduce the core cost: **you're still doing all the thinking and writing**. Graph view is cool, but it doesn't write pages for you.

## Verdict

Obsidian is the best viewer for an LLM Wiki. The graph, backlinks, Dataview, and mobile access make it the richest reading experience. But it's not the builder. Pair it with an agent (Section 5) for the full experience, or use it solo if you have a small wiki and enjoy the curation process.

---

*Next: [04 — NotebookLM](../04-notebooklm/approach.md)*
