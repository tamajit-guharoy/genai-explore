# Pros & Cons — Every Approach Compared

> Honest, no-marketing comparison of every LLM Wiki approach. Use this to decide what's right for you.

## Quick-Reference Table

| Approach | Quality | Time/ Source | Setup | Monthly Cost | Scale | Memory | Auto-Maintenance | Mobile |
|---|---|---|---|---|---|---|---|---|
| **A: Manual (zero tools)** | ⭐⭐⭐⭐⭐ | 40–90 min | 5 min | $0 | ~20 pages | No | No | No |
| **B: Manual + Obsidian** | ⭐⭐⭐⭐⭐ | 30–60 min | 15 min | $0 | ~50 pages | No | No | Read-only |
| **C: Manual + Obsidian + NotebookLM** | ⭐⭐⭐⭐⭐ | 25–50 min | 15 min | $0 | ~50 pages | No | No | Read-only |
| **D: Hermes + Obsidian + NotebookLM** | ⭐⭐⭐⭐ | 2–5 min | 30 min | $5–30 | 100+ pages | Yes | Yes (cron) | Full |
| **E: Hermes + Terminal** | ⭐⭐⭐⭐ | 2–5 min | 30 min | $5–30 | 100+ pages | Yes | Yes (cron) | No |
| **F: Claude Code + Obsidian** | ⭐⭐⭐⭐⭐ | 2–5 min | 15 min | $20–200 | 100+ pages | Per-project | Manual | No |
| **G: Dual-Agent (Claude + Hermes)** | ⭐⭐⭐⭐⭐ | 2–5 min | 45 min | $15–115 | 100+ pages | Yes | Yes (cron) | Full |
| **H: Codex + GitHub** | ⭐⭐⭐⭐ | 2–5 min | 15 min | $20–200 | 100+ pages | No | Manual | No |
| **I: Cursor Agent** | ⭐⭐⭐⭐ | 2–5 min | 10 min | $20 | 100+ pages | No | Manual | No |
| **J: ChatGPT copy-paste** | ⭐⭐⭐ | 15–30 min | 0 min | $0 | ~10 pages | No | No | No |

---

## Detailed Analysis

### A: Manual (Zero Tools)

**Pros:**
- Complete control — every word is yours
- Deep engagement with material
- Zero cost, zero dependencies
- Works offline anywhere
- No risk of LLM hallucination in pages

**Cons:**
- 40–90 minutes per source is unsustainable at scale
- Quality varies with energy and focus
- You're the bottleneck — wiki growth capped by your time
- No auto-maintenance — contradictions and staleness accumulate
- Missing cross-references — humans are bad at spotting connections across 20+ pages

**Bottom line:** Great for learning. Great for one small, high-value wiki. Not viable long-term.

---

### B: Manual + Obsidian

**Pros:**
- Same control as manual
- Graph view reveals knowledge structure
- Backlinks panel spots orphans
- Autocomplete speeds up wikilink creation
- Dataview provides database-like queries

**Cons:**
- Still manual — Obsidian doesn't reduce the writing/thinking burden
- Graph becomes overwhelming with 50+ pages
- No auto-maintenance
- Obsidian Sync costs money if you want multi-device

**Bottom line:** The best manual experience. If you enjoy curation and have a small wiki, this is pleasant.

---

### C: Manual + Obsidian + NotebookLM

**Pros:**
- NotebookLM speeds up source exploration ("what's in here?")
- Same Obsidian benefits
- Audio overviews are genuinely useful

**Cons:**
- NotebookLM adds a step without reducing the core manual work
- Switching between tools creates friction
- Still doesn't solve the scaling problem

**Bottom line:** A slight improvement over B. Worth it if you already use NotebookLM. Doesn't change the fundamental manual bottleneck.

---

### D: Hermes + Obsidian + NotebookLM (Full Stack)

**Pros:**
- **Compounds over time** — the wiki gets better with every source
- **Minimal human time** — 2–5 min per source (just "save to wiki")
- **Auto-maintenance** — cron handles linting, contradiction detection, stale page flagging
- **Cross-platform** — ingest from phone via Telegram, browse in Obsidian
- **Persistent memory** — Hermes remembers your preferences across sessions
- **Cost-effective** — use cheap models for routine work, frontier only when needed
- **Self-hosted** — data never leaves your machine
- **Open-source** — no vendor lock-in

**Cons:**
- **Setup time** — 30 min initial configuration
- **Self-hosting overhead** — you manage the Hermes process
- **Model quality dependent** — extraction quality varies with the model you choose
- **Obsidian Sync costs** — if you want multi-device Obsidian
- **Two moving parts** — Hermes + Obsidian to maintain

**Bottom line:** The recommended setup for anyone serious about compounding knowledge. The upfront investment pays off within a week.

---

### E: Hermes + Terminal (Minimalist)

**Pros:**
- Same Hermes benefits as D (memory, cron, skills)
- Zero GUI dependencies — runs on any server
- SSH-accessible from anywhere
- No Obsidian maintenance

**Cons:**
- No graph view — harder to see knowledge structure visually
- Terminal-only reading — less pleasant for long browsing
- No mobile reading (unless you use Terminal on phone)
- Can't easily share wiki pages with non-technical people

**Bottom line:** The server-native approach. Perfect for developers who live in the terminal. Add Obsidian later if you want visuals.

---

### F: Claude Code + Obsidian

**Pros:**
- **Best extraction quality** — Claude's reasoning is top-tier for nuanced synthesis
- Better at handling ambiguity, conflicting sources, and subtle relationships
- Simple setup — just a CLAUDE.md

**Cons:**
- **Expensive** — Claude API costs add up fast with large wikis
- **No persistent memory** — forgets your wiki conventions between sessions (mitigated by CLAUDE.md)
- **No cron** — can't schedule maintenance; everything is manual
- **No mobile** — terminal only
- **Single model provider** — locked to Anthropic

**Bottom line:** Best for quality-focused users with budget who don't need automation. The Porsche of wiki builders.

---

### G: Dual-Agent (Claude + Hermes) — Best of Both

**Pros:**
- **Best quality when it matters** — Claude for complex sources
- **Cost-efficient for routine** — Hermes + cheap model for everyday
- **Automated maintenance** — Hermes cron handles linting, health checks
- **Cross-platform** — Hermes gateway for mobile
- **Persistent memory** — Hermes remembers across sessions
- **Two agents, one wiki** — they share the same markdown files

**Cons:**
- **Most complex setup** — two agent systems to configure
- **Higher total cost** — Claude API + Hermes model costs
- **Potential for inconsistency** — Claude and Hermes might write pages differently
- **Overkill for small wikis**

**Bottom line:** The no-compromises setup. Best extraction (Claude) + best automation (Hermes). Worth it for serious researchers with budget.

---

### H: Codex + GitHub

**Pros:**
- **Native GitHub integration** — PRs, reviews, CI for wiki changes
- **Team-friendly** — code review workflow for wiki edits
- **GitHub Pages** — publish wiki as static site
- Good for developer teams already using GitHub

**Cons:**
- **Session-bound** — no persistent memory across sessions
- **Expensive** — OpenAI API costs
- **No auto-maintenance**
- **Less transparent reasoning** than Claude
- **GitHub-centric** — tight coupling to one platform

**Bottom line:** Best for software teams that want a wiki as part of their repo. Not ideal for personal use.

---

### I: Cursor Agent

**Pros:**
- **Karpathy's actual setup** — battle-tested
- **IDE-integrated** — edit wiki alongside code
- **Multi-file aware** — sees all wiki files at once
- Good reasoning (uses Claude/GPT under the hood)
- Fixed monthly cost ($20)

**Cons:**
- **No persistent memory** — session-bound
- **No auto-maintenance** — no cron
- **No mobile** — IDE only
- **Cursor subscription required**

**Bottom line:** Perfect if you already use Cursor. Not worth switching for just the wiki.

---

### J: ChatGPT Copy-Paste

**Pros:**
- **Zero setup** — start in 30 seconds
- **Free** — ChatGPT free tier
- **Good for learning** — understand the pattern before committing
- **No dependencies**

**Cons:**
- **Heavy manual overhead** — copy-paste context, copy-paste output, file manually
- **Tiny scale ceiling** — falls apart after ~10 pages
- **No cross-session memory** — re-paste SCHEMA.md every time
- **Context window limits** — can only work with a few pages
- **Manual filing errors** — easy to forget to update index.md

**Bottom line:** Weekend experiment. Try it, see if you like the pattern, then graduate to an agent.

---

## Decision Framework

```
1. HOW MANY SOURCES?
   <20 total → Manual + Obsidian (B) is fine
   20–100 → Hermes (D/E) will pay off
   100+ → You need an agent. Hermes or Dual-Agent (G).

2. WHAT'S YOUR BUDGET?
   $0 → Manual (A/B/C) or ChatGPT trial (J)
   $5–30/mo → Hermes with cheap model (D/E)
   $20–200/mo → Claude Code (F) or Dual-Agent (G)

3. HOW IMPORTANT IS QUALITY?
   "Every detail matters" → Manual (A/B) or Claude Code (F)
   "Good enough, I verify important claims" → Hermes (D/E)
   "No compromises" → Dual-Agent (G)

4. DO YOU NEED MOBILE?
   Yes → Hermes with messaging gateway (D/G)
   No → Any approach

5. DO YOU NEED AUTOMATION?
   Yes → Hermes with cron (D/E/G)
   No → Any other approach

6. ARE YOU A TEAM?
   Yes → Codex + GitHub (H) or shared git repo
   No → Personal wiki

7. WHAT'S YOUR TECHNICAL COMFORT?
   CLI-native → Hermes + Terminal (E)
   GUI-preferred → Hermes + Obsidian (D)
   IDE-native → Cursor (I)
   Zero-tech → ChatGPT (J) or Manual + Obsidian (B)
```

---

## The Honest Bottom Line

The LLM Wiki pattern is **genuinely excellent**. It solves the maintenance burden that kills most second-brain attempts. But the quality of your wiki depends entirely on:

1. **The quality of your sources** — garbage in, garbage out
2. **The quality of your agent/model** — Claude extracts better than GPT-4, which extracts better than smaller models
3. **Your curation** — you still choose what goes in and verify important claims

No tool eliminates the need for human judgment. What the tools eliminate is the **mechanical work** — summarization, cross-referencing, filing, formatting, maintenance. That's the right division of labor: human curates, agent executes.

Karpathy's own words sum it up best:

> "I'm still the one curating what goes in, I'm still the one verifying the important claims, I'm still the one asking the questions. But I'm not the one doing the mechanical work of summarization and cross-referencing. That's what machines are for."

---

*End of tutorial. Return to [README.md](../README.md) for the overview.*
