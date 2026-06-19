# Andrej Karpathy's LLM Wiki — In-Depth Tutorial

> A comprehensive guide to building an AI-powered personal knowledge base (Second Brain) using Karpathy's LLM Wiki pattern. Covers every approach from bare metal to full automation, with worked examples, sample files, and honest pros/cons.

---

## What This Tutorial Covers

On **April 2, 2026**, Andrej Karpathy — former Tesla AI lead, OpenAI co-founder, and one of the most respected AI researchers — posted a tweet that reshaped how people think about using LLMs. He described a shift: instead of spending tokens on code generation, he was spending them on **knowledge manipulation**. An LLM agent builds and maintains a personal wiki from raw source material, autonomously writing pages, cross-referencing concepts, and running health checks — without him writing a single word.

This tutorial explores the concept in depth and shows you every way to implement it.

---

## Table of Contents

| Section | Description |
|---|---|
| [01 — What is an LLM Wiki?](01-concept/what-is-llm-wiki.md) | The concept, Karpathy's original tweet & gist, why it's different from RAG |
| [02 — Manual (No Tools)](02-no-tools/) | Build an LLM wiki with nothing but a text editor and your brain |
| [03 — Obsidian as Viewer](03-obsidian/) | Use Obsidian's graph, backlinks, and Dataview on top of a wiki |
| [04 — NotebookLM](04-notebooklm/) | What NotebookLM does well, what it can't do, and where it fits |
| [05 — Agent-Driven](05-agent-driven/) | Let an AI agent (Hermes, Claude Code, Codex, ChatGPT) build and maintain the wiki |
| [06 — Combinations](06-combinations/) | Mixed approaches: Agent + Obsidian, NotebookLM + Agent, full-stack setups |
| [07 — Skills & Tools](07-skills-and-tools/) | Available skills (Hermes `llm-wiki`), `llm-wiki-compiler`, and other ecosystem tools |
| [08 — Pros & Cons](08-pros-cons/) | Honest comparison of every approach: cost, effort, quality, maintenance |
| [09 — Graph vs Vector](09-graph-vs-vector/) | When the wiki genuinely beats RAG: causal chains, citations, narratives, dependencies |
| [10 — Scaling & Operations](10-scaling-and-operations/) | Add/update/delete knowledge, token economics, scaling to 1 TB |
| [Example Wiki](wiki/) | A fully built example wiki from shared sample sources |
| [Sample Raw Files](raw/) | Articles, papers, and transcripts you can use to test each approach |

---

## Quick Navigation for Different Readers

- **I just want to understand the idea** → [01-concept/](01-concept/what-is-llm-wiki.md)
- **I want the simplest possible setup** → [02-no-tools/](02-no-tools/approach.md)
- **I already use Obsidian** → [03-obsidian/](03-obsidian/approach.md)
- **I want an agent to do all the work** → [05-agent-driven/](05-agent-driven/approach.md)
- **I want to understand when it beats RAG** → [09-graph-vs-vector/](09-graph-vs-vector/approach.md)
- **I want to know how to scale it** → [10-scaling-and-operations/](10-scaling-and-operations/approach.md)
- **I want to compare everything** → [08-pros-cons/](08-pros-cons/comparison.md)
- **I want to see a real example** → [wiki/](wiki/)

---

## Key Takeaways (TL;DR)

1. **The LLM Wiki is a directory of markdown files.** No database, no special tooling required.
2. **Three-layer architecture:** Raw sources (immutable) → Wiki pages (agent-written) → Schema (rules).
3. **The agent is the engine.** Obsidian, VS Code, any editor — they're just viewers.
4. **It compounds.** Unlike RAG (which re-discovers from scratch), a wiki accumulates cross-references and synthesis.
5. **You can start today** with nothing but a terminal and an LLM chat window.

---

*Tutorial written June 2026 against the Karpathy LLM Wiki pattern as described in his April 2026 tweet and [GitHub Gist](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f).*
