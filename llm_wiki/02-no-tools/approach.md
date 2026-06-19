# Approach 2: Manual Implementation — No Tools

> Build an LLM wiki with nothing but a text editor, your brain, and a markdown renderer.

This is the simplest, most transparent approach. It's also the most labor-intensive. But it teaches you the architecture deeply and works on any machine, anywhere, with zero dependencies.

## What You Need

- A text editor (VS Code, Vim, Notepad, anything)
- A markdown previewer (optional — VS Code built-in, or any browser extension)
- Your brain

## Step-by-Step: Build a Manual Wiki

We'll ingest sample sources about AI agents and build a wiki by hand. All sample files referenced here exist in this directory — open them and follow along.

### Step 1: Create the Directory Structure

```bash
mkdir -p ~/wiki/{raw/{articles,papers,transcripts,assets},entities,concepts,comparisons,queries}
```

### Step 2: Write SCHEMA.md

Your constitution. Rules to keep pages consistent even when you're the one writing them.

```markdown
# Wiki Schema

## Domain
AI/ML research — architectures, training techniques, tools, and companies.

## Conventions
- File names: lowercase, hyphens, no spaces
- Every page starts with YAML frontmatter (title, created, updated, type, tags, sources)
- Use [[wikilinks]] to link between pages
- Minimum 1 outbound link per page (aim for 2+)
- When updating a page, bump the updated date

## Tag Taxonomy
- architecture, training, inference, benchmark
- company, person, open-source, product
- technique, concept, comparison, controversy

## Page Thresholds
- Create a page when an entity/concept appears in 2+ sources
- Add to existing page for mentions of already-covered items
- Skip passing mentions
```

### Step 3: Save a Raw Source

Copy an article into `raw/articles/`. For example, our sample article about AI agents (see [`raw/articles/ai-agent-landscape-2026.md`](raw/articles/ai-agent-landscape-2026.md)).

Add frontmatter:

```yaml
---
source_url: https://example.com/ai-agent-landscape-2026
ingested: 2026-06-19
sha256: <computed hash>
---
```

*(To compute the hash: `shasum -a 256 raw/articles/ai-agent-landscape-2026.md | awk '{print $1}'`)*

### Step 4: Read and Extract

Read the raw source. With a notepad open, list:

- **Entities mentioned:** OpenAI, Anthropic, Nous Research, Andrej Karpathy, Claude, GPT-4, Hermes Agent
- **Concepts discussed:** AI agents, tool use, autonomous coding, memory, skills, RAG vs wiki
- **Claims:** "Agents with tool access outperform chat-only models on complex tasks"
- **Comparisons:** Hermes vs Claude Code vs Codex vs Manus

### Step 5: Check Existing Pages

Before creating anything, search your wiki for these entities and concepts:

```bash
grep -r "OpenAI" wiki/
grep -r "autonomous coding" wiki/
```

If it's a new wiki, you'll find nothing — so everything is new.

### Step 6: Write Wiki Pages

For each entity/concept that appears prominently (or in 2+ sources), write a page.

**Example: `entities/nous-research.md`**

```markdown
---
title: Nous Research
created: 2026-06-19
updated: 2026-06-19
type: entity
tags: [company, open-source]
sources: [raw/articles/ai-agent-landscape-2026.md]
---

# Nous Research

## Overview
AI research company focused on open-source models and agent infrastructure.
Creator of Hermes model series and [[hermes-agent]].

## Key Products
- **Hermes models** — Open-weight LLMs optimized for tool use and agentic behavior
- **[[hermes-agent]]** — Open-source, self-hosted autonomous AI agent platform
- **Nous Portal** — Hosted inference for Hermes models

## Role in Agent Ecosystem
Hermes Agent is one of the major open-source alternatives to proprietary agents
like [[claude-code]] and [[codex]]. Its differentiator is persistent memory and
self-improving skills that compound over time — the "agent that grows with you."

## See Also
- [[ai-agents]] — broader agent landscape
- [[hermes-agent]] — detailed agent page
- [[llm-wiki-pattern]] — Karpathy's wiki approach (used by Hermes)
```

**Example: `concepts/ai-agents.md`**

```markdown
---
title: AI Agents
created: 2026-06-19
updated: 2026-06-19
type: concept
tags: [concept, technique]
sources: [raw/articles/ai-agent-landscape-2026.md]
---

# AI Agents

## Definition
An AI agent is an LLM-powered system that can use tools, maintain state,
and take multi-step actions autonomously. Unlike chatbots (single-turn Q&A),
agents plan, execute, observe results, and adapt.

## Key Capabilities
- **Tool use** — Terminal, browser, API calls, file operations
- **Memory** — Persistent state across sessions and conversations
- **Planning** — Break complex tasks into steps, execute sequentially
- **Self-correction** — Observe tool output, retry on failure, adjust approach

## Major Agents (2026)
| Agent | Creator | Key Differentiator |
|---|---|---|
| [[claude-code]] | Anthropic | Deep reasoning, code generation |
| [[codex]] | OpenAI | Fast execution, GitHub integration |
| [[hermes-agent]] | [[nous-research]] | Persistent memory, self-improving skills |
| Manus | Manus AI | Browser automation focus |

## Open Question
Will agents converge on a common tool-calling protocol, or will fragmentation continue?
The [[agentskills.io]] standard is one attempt at convergence for skills specifically.

## See Also
- [[llm-wiki-pattern]] — using agents to build knowledge bases
- [[tool-use]] — the underlying capability
- [[agent-comparison-2026]] — detailed feature matrix
```

### Step 7: Write the Index

Every page goes in `index.md`:

```markdown
# Wiki Index

> Content catalog. Every wiki page listed with one-line summary.
> Last updated: 2026-06-19 | Total pages: 5

## Entities
- [[nous-research]] — AI research company, creator of Hermes models and Hermes Agent

## Concepts
- [[ai-agents]] — LLM-powered autonomous systems with tool use and memory
- [[tool-use]] — Agent capability to invoke external tools (terminal, browser, API)
- [[llm-wiki-pattern]] — Karpathy's approach to agent-built knowledge bases

## Comparisons
- [[agent-comparison-2026]] — Claude Code vs Codex vs Hermes Agent vs Manus
```

### Step 8: Log the Action

Append to `log.md`:

```markdown
## 2026-06-19 | ingest | AI Agent Landscape 2026
- Source saved: raw/articles/ai-agent-landscape-2026.md
- Created: entities/nous-research.md
- Created: concepts/ai-agents.md
- Created: concepts/tool-use.md
- Created: concepts/llm-wiki-pattern.md
- Created: comparisons/agent-comparison-2026.md
- Updated: index.md
```

### Step 9: Cross-Reference Check

Go through every new page and ensure:
- At least 1–2 `[[wikilinks]]` point to other pages
- At least one other page links back (no orphans)
- Tags are from the taxonomy in SCHEMA.md
- Frontmatter has all required fields

### Step 10: Repeat

For each new source you add, repeat steps 3–9.

## The Manual Workflow in Practice

Here's what a session looks like when you find an interesting article:

```
1. Read the article (10–30 min)
2. Save markdown copy to raw/articles/ (2 min)
3. List entities, concepts, claims on scratch paper (5 min)
4. Search existing wiki for each (2 min)
5. Write/update wiki pages (15–45 min depending on how many)
6. Update index.md (3 min)
7. Append to log.md (1 min)
8. Cross-reference check (5 min)
-------------------------------------------
Total: ~40–90 minutes per source
```

This is why people usually don't maintain wikis manually — it's a significant time investment per source. But it forces deep engagement with the material, and the resulting wiki reflects *your* understanding, not an LLM's.

## Sample Files to Explore

All these files exist in this directory as worked examples:

```
02-no-tools/
├── approach.md                          ← you are here
├── raw/
│   ├── articles/
│   │   ├── karpathy-llm-wiki-tweet.md     ← the original tweet, saved as raw source
│   │   ├── ai-agent-landscape-2026.md     ← fictional survey article
│   │   └── gpt4-technical-report.md       ← excerpt from GPT-4 report
│   ├── papers/
│   │   └── attention-is-all-you-need.md   ← the classic Transformer paper
│   └── transcripts/
│       └── karpathy-lex-fridman.md        ← interview transcript excerpt
└── wiki/
    ├── SCHEMA.md                          ← the constitution
    ├── index.md                           ← full page catalog
    ├── log.md                             ← action log
    ├── entities/
    │   ├── openai.md
    │   ├── anthropic.md
    │   ├── nous-research.md
    │   └── andrej-karpathy.md
    ├── concepts/
    │   ├── ai-agents.md
    │   ├── attention-mechanism.md
    │   ├── transformer-architecture.md
    │   ├── tool-use.md
    │   └── llm-wiki-pattern.md
    └── comparisons/
        ├── agent-comparison-2026.md
        └── llm-wiki-vs-rag.md
```

## Pros and Cons of Manual

### Pros
- **Zero cost** — no API keys, no subscriptions
- **Total control** — every word is yours, every link is intentional
- **Deep understanding** — you learn the material by writing about it
- **No drift** — no risk of LLM hallucination in your wiki pages
- **Works offline** — airport, airplane, anywhere

### Cons
- **High time cost** — 40–90 min per source
- **Inconsistent** — quality varies with your energy and focus
- **Doesn't scale** — 5 sources is fine; 50 is overwhelming
- **Missed connections** — humans are bad at spotting cross-references across dozens of pages
- **No health checks** — stale pages and contradictions accumulate silently
- **You're the bottleneck** — wiki growth is gated by your available time

### Verdict
Manual is excellent for **learning the architecture** and for **small, high-value wikis** (5–20 sources on a topic you care deeply about). For anything larger, you'll want automation.

---

*Next: [03 — Obsidian as Viewer](../03-obsidian/approach.md)*
