# Approach 5: Agent-Driven LLM Wiki

> Let an AI agent do all the work: read sources, write pages, cross-reference, maintain. This is what Karpathy actually does.

This is the real LLM Wiki. The agent is the engine. You're the curator.

## Overview

| Agent | How to Build a Wiki | Best For |
|---|---|---|
| **Hermes Agent** | Built-in `llm-wiki` skill — just say "build me a wiki" | Long-term personal wikis, memory + skills compound |
| **Claude Code** | Custom instructions / CLAUDE.md + manual agent prompts | Heavy research with best reasoning |
| **Codex (OpenAI)** | Custom instructions in VS Code / CLI | GitHub-integrated workflows |
| **ChatGPT / Claude Chat** | Copy-paste workflow — manual but works | Casual, small-scale wikis |
| **Cursor** | Agent mode with custom rules | Karpathy's actual setup (Cursor + agent) |

## Approach 5a: Hermes Agent with `llm-wiki` Skill

Hermes Agent ships with an `llm-wiki` skill that implements Karpathy's full pattern. This is the most turnkey approach.

### Setup

```bash
# 1. Set wiki location (optional, defaults to ~/wiki)
echo 'WIKI_PATH="$HOME/wiki"' >> ~/.hermes/.env

# 2. Start Hermes
hermes

# 3. Initialize the wiki
you > Build me an LLM wiki for AI/ML research. Create the directory structure, SCHEMA.md, and index.md.
```

### Daily Workflow

```
# Drop a source
you > Save this article to my wiki: https://example.com/ai-agents-2026

# Hermes:
#   → web_extract the URL
#   → Save to raw/articles/
#   → Read SCHEMA.md
#   → Extract entities & concepts
#   → Search existing pages
#   → Create/update wiki pages
#   → Cross-reference with [[wikilinks]]
#   → Update index.md
#   → Append to log.md
#   → Report: "Created 3 pages, updated 2. New entity: Nous Research."
```

```bash
# Query the wiki
you > What does my wiki know about attention mechanisms?

# Hermes:
#   → Read index.md
#   → Find concepts/attention-mechanism.md
#   → Read the page
#   → Read linked pages (transformer-architecture.md)
#   → Synthesize answer with citations
```

```bash
# Health check
you > Lint my wiki

# Hermes:
#   → Scan for orphan pages (no inbound links)
#   → Check for broken wikilinks
#   → Validate frontmatter completeness
#   → Flag pages not in index.md
#   → Check for contradictions
#   → Report: "2 orphans, 1 broken link, 3 pages with missing tags"
```

### Why Hermes Wins for Wikis

- **Memory persists** — Hermes remembers your wiki structure, preferences, and conventions across sessions. You don't re-explain SCHEMA.md preferences.
- **llm-wiki skill** — Pre-built, battle-tested implementation of Karpathy's pattern. Already knows the three-layer architecture, frontmatter conventions, linting procedures.
- **Cron for auto-maintenance** — Schedule weekly wiki health checks: `Every Sunday at 9am, lint my wiki and report issues.`
- **Messaging gateway** — "Hermes, ingest this article I just sent you on Telegram" — works from your phone.
- **Multiple model providers** — Use a cheap model for wiki linting, frontier model for complex ingestions.
- **Free** — Self-hosted; you only pay for model API calls.

### Concrete Example

See the [hermes-with-llm-wiki-skill.md](hermes-with-llm-wiki-skill.md) for a full walkthrough.

## Approach 5b: Claude Code

Claude Code doesn't have a built-in wiki skill, but you can instruct it to follow the pattern.

### Setup

Create a `CLAUDE.md` in your wiki directory:

```markdown
# Claude Code Instructions for LLM Wiki

When I ask you to "ingest" a source, follow this procedure:

1. Read the source
2. Read SCHEMA.md to understand conventions
3. Read index.md to see existing pages
4. Extract entities, concepts, and claims
5. For each significant entity/concept:
   a. Search existing wiki pages for it
   b. Create new page (with YAML frontmatter + [[wikilinks]]) if new AND significant
   c. Update existing page if already covered
6. Cross-reference: ensure new pages link to 2+ existing pages and vice versa
7. Update index.md — add new pages under correct section
8. Append to log.md with all files created/updated
9. Report what changed

Use the file structure:
- raw/ (immutable sources)
- entities/ (people, orgs, products)
- concepts/ (ideas, techniques, topics)
- comparisons/ (side-by-side analyses)
- SCHEMA.md (conventions)
- index.md (catalog)
- log.md (action log)
```

### Daily Workflow

```bash
# Drop sources into raw/
cp ~/Downloads/paper.pdf wiki/raw/papers/

# Ingest
claude "Ingest the new paper in raw/papers/paper.pdf into the wiki"

# Query
claude "What does my wiki say about transformer attention heads?"
```

### Pros/Cons vs Hermes
- **Better reasoning** — Claude's models are excellent at nuanced extraction and synthesis
- **No persistent memory** — Claude Code forgets your wiki conventions between sessions (unless in CLAUDE.md)
- **No cron** — Can't schedule maintenance tasks
- **No cross-platform** — Terminal only, no Telegram/Discord access
- **Cost** — Claude API calls are more expensive than Hermes + cheap model

## Approach 5c: Codex (OpenAI)

Similar to Claude Code but with OpenAI models. Create a `.codexrules` or CODE.md file with the same instructions as the CLAUDE.md above.

Codex's advantage: deep GitHub integration. If your wiki is a git repo (recommended), Codex can manage commits, PRs, and CI for wiki changes.

## Approach 5d: ChatGPT / Claude Chat (Manual Copy-Paste)

The simplest agent-driven approach. No CLI, no setup — just a chat window.

### Workflow

1. **Paste SCHEMA.md** into chat: "Here are the rules for my wiki."
2. **Paste index.md**: "Here's what's in my wiki so far."
3. **Paste a source**: "Ingest this article. Create/update wiki pages per the schema."
4. **Copy the LLM's output** (it will generate markdown for new pages)
5. **Paste into files** — create the .md files manually

### Why This Is Painful
- Copy-pasting context every session
- LLM output needs manual filing
- No file-system access — can't read existing pages, can't write to disk
- Context window limits — can only work with a few pages at a time
- No memory across sessions

This is the "I want to try the concept without installing anything" approach. It works for a 5-page wiki. It doesn't scale.

## Approach 5e: Cursor Agent Mode (Karpathy's Actual Setup)

Karpathy mentioned using Cursor (VS Code fork) with its agent mode. This is what he actually uses:

1. Open the wiki directory in Cursor
2. Cursor's agent has full read/write access to all wiki files
3. Add `.cursorrules` with the wiki conventions
4. Ask the agent to ingest sources, create pages, cross-reference

Cursor's advantage: it sees the entire codebase (wiki), can read/write multiple files simultaneously, and the agent mode handles multi-step tasks well.

## Cost Comparison

| Agent | Setup Cost | Per-Ingestion Cost | Monthly Maintenance |
|---|---|---|---|
| **Hermes + cheap model** | 30 min | ~$0.05–0.50 | ~$1–5 (cron linting) |
| **Hermes + frontier model** | 30 min | ~$0.50–3.00 | ~$10–30 |
| **Claude Code** | 15 min (CLAUDE.md) | ~$0.50–5.00 | Manual (no cron) |
| **Codex** | 15 min (.codexrules) | ~$0.50–5.00 | Manual |
| **ChatGPT/Claude Chat** | 0 min | Free (manual) | Free (manual) |
| **Cursor** | 10 min (.cursorrules) | Included in subscription | Included |

## Recommendation

| Your Situation | Best Approach |
|---|---|
| I want this to compound over years | Hermes Agent — memory + skills + cron |
| I want the best single-ingestion quality | Claude Code — best reasoning |
| I already pay for Cursor | Cursor agent mode |
| I want to try without installing anything | ChatGPT/Claude Chat with copy-paste |
| I have a GitHub-centric workflow | Codex |
| I want cross-platform access (phone, messaging) | Hermes Agent (messaging gateway) |

---

*Next: [06 — Combinations](../06-combinations/)*
