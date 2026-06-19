# Approach 6: Combinations — Mix and Match

> The LLM Wiki is a markdown directory. That means any tool that reads/writes markdown can be part of the stack. Here are the combinations that work well, and why.

## Combination Matrix

| # | Agent (Builder) | Viewer | Discovery | Maintenance | Best For |
|---|---|---|---|---|---|
| A | None (Manual) | None (Terminal) | None | None | Learning the architecture |
| B | None (Manual) | Obsidian | None | Manual lint | Small, high-value wikis |
| C | None (Manual) | Obsidian | NotebookLM | Manual lint | Visual thinker with few sources |
| D | Hermes Agent | Obsidian | NotebookLM | Hermes cron | **Full stack — best overall** |
| E | Hermes Agent | Terminal | None | Hermes cron | Minimalist, CLI-only |
| F | Claude Code | Obsidian | NotebookLM | Manual | Best reasoning quality |
| G | Claude Code + Hermes | Obsidian | NotebookLM | Hermes cron | **Dual-agent — best of both** |
| H | Codex | GitHub | None | Manual | GitHub-centric team wiki |
| I | Cursor Agent | Cursor | None | Manual | Karpathy's actual setup |
| J | ChatGPT Chat | Manual copy-paste | None | None | Zero-install trial |

## Combo A: Pure Manual (Zero Tools)

```
You → Read sources → Write pages → Cross-reference → Index → Log
```

**Stack:** Text editor + brain.

**Cost:** Free. **Time per source:** 40–90 min. **Scale ceiling:** ~20 pages before it falls apart.

**Use case:** Learning the pattern. Building one small, high-quality wiki on a topic you care deeply about.

---

## Combo B: Manual + Obsidian Viewer

```
You → Read sources → Write pages in Obsidian → [[wikilinks]] auto-complete → Graph view
```

**Stack:** Obsidian (editor + viewer).

**Cost:** Free (Obsidian personal). **Time per source:** 30–60 min (wikilink autocomplete saves time). **Scale ceiling:** ~50 pages.

**Use case:** You enjoy the curation process. Graph view helps you spot connections you missed. Good for writers and researchers who want maximum control.

---

## Combo C: Manual + Obsidian + NotebookLM Discovery

```
NotebookLM → Quick exploration of sources → Identify key themes
You → Write wiki pages in Obsidian → Graph view → Dataview queries
```

**Stack:** NotebookLM (discovery) + Obsidian (editor/viewer) + Human (writer).

**Cost:** Free. **Time per source:** 25–50 min (NotebookLM speeds up "what's in here?"). **Scale ceiling:** ~50 pages.

**Use case:** Research-heavy workflows where you're dealing with dense papers and want AI help understanding them, but still want to write the synthesis yourself.

---

## Combo D: Hermes Agent + Obsidian + NotebookLM (Full Stack)

```
NotebookLM → Quick exploration, identify valuable sources
Hermes Agent → Ingest sources → Build full wiki → Auto-lint weekly
Obsidian → Browse graph → Read pages → Dataview queries
Telegram → "Save this to my wiki" from phone
```

**Stack:** NotebookLM (discovery) + Hermes Agent (builder, maintainer) + Obsidian (viewer) + Telegram (mobile input).

**Cost:** Hermes (free) + NotebookLM (free) + Obsidian (free) + model API (~$5–30/mo). **Time per source:** 2–5 min (your time). **Scale ceiling:** Hundreds of pages.

**Use case:** The full Karpathy experience. All you do is feed sources and ask questions. The agent builds, the cron maintains, Obsidian makes it beautiful. This is the setup recommended for anyone serious about compounding knowledge.

### Daily Workflow

```
Morning:    See interesting article on phone → Telegram it to Hermes → "Save to wiki"
Lunch:      Open Obsidian → Graph view → Notice new node cluster → Read updated pages
Evening:    Terminal → "What does my wiki know about X?" → Agent synthesizes from wiki pages
Sunday:     Auto-lint runs → Telegram message: "Wiki healthy. 27 pages. 0 issues."
```

---

## Combo E: Hermes Agent + Terminal (Minimalist)

```
Hermes Agent → Ingest sources → Build wiki → Auto-lint weekly
Terminal → hermes "What does my wiki say about X?"
```

**Stack:** Hermes Agent (builder, viewer, maintainer) + Terminal (query interface).

**Cost:** Hermes (free) + model API (~$5–30/mo). **Time per source:** 2–5 min. **Scale ceiling:** Hundreds of pages.

**Use case:** CLI purists. Server-based wikis. No GUI needed. You live in the terminal and want minimal dependencies.

---

## Combo F: Claude Code + Obsidian + NotebookLM

```
NotebookLM → Exploration
Claude Code → Ingest sources → Build wiki (best reasoning quality)
Obsidian → Browse → Graph view
```

**Stack:** NotebookLM (discovery) + Claude Code (builder) + Obsidian (viewer).

**Cost:** Claude API (~$20–200/mo depending on volume) + Obsidian (free). **Time per source:** 2–5 min. **Scale ceiling:** Hundreds of pages.

**Use case:** You prioritize extraction quality above all else. Claude's reasoning is best-in-class for nuanced synthesis. You're willing to pay more and handle maintenance manually.

### Trade-off vs Hermes

| Dimension | Claude Code | Hermes Agent |
|---|---|---|
| Extraction quality | Excellent | Very good (model-dependent) |
| Persistent memory | Per-project only | Cross-session |
| Auto-maintenance | Manual | Cron-powered |
| Mobile input | No | Telegram/Discord/etc |
| Cost (monthly) | Higher (Claude-only) | Lower (use cheap models) |

---

## Combo G: Dual-Agent (Claude Code + Hermes) — Best of Both

```
Claude Code → Complex ingestions (dense papers, nuanced topics)
Hermes Agent → Routine ingestions → Auto-maintenance → Queries → Telegram access
Obsidian → Browse everything
```

**Stack:** Claude Code (quality ingester) + Hermes Agent (volume ingester, maintainer, query interface) + Obsidian (viewer).

**Cost:** Hermes (free) + Claude API (~$10–100/mo) + cheap model for Hermes (~$5–15/mo). **Time per source:** 2–5 min.

**Workflow:**
```
# Complex paper → Claude Code
you > claude "Ingest this dense 40-page survey paper into the wiki. Be thorough."
# Claude produces deeper, more nuanced pages

# Routine article → Hermes (cheaper, faster)
# "Save this to wiki" on Telegram → Hermes handles it with a cheap model

# Maintenance → Hermes cron
# Weekly lint, contradiction detection, stale page flagging

# Queries → Hermes (remembers context across sessions)
you > hermes "What's the consensus on RLHF vs Constitutional AI across my wiki?"
# Hermes reads wiki pages AND remembers previous discussions about alignment
```

**Use case:** You want the absolute best quality without paying Claude rates for everything. High-value sources get Claude; routine ones get Hermes + cheap model. Maintenance is automated.

---

## Combo H: Codex + GitHub (Team Wiki)

```
Codex → Ingest sources → Create/update wiki pages → Commit to git → Open PR
Team → Review PR → Merge
GitHub Pages → Publish wiki as static site
```

**Stack:** Codex (builder) + GitHub (version control, review) + GitHub Pages (publishing).

**Cost:** Codex subscription + GitHub (free for public). **Time per source:** 2–5 min (agent) + review time.

**Use case:** Team wikis where you want PR review before changes go live. GitHub-native workflow.

---

## Combo I: Cursor Agent (Karpathy's Setup)

```
Cursor Agent → Read SCHEMA.md → Read existing pages → Ingest source → Write pages → Cross-reference
Cursor → View diffs → Accept/reject changes
```

**Stack:** Cursor (IDE + agent). This is what Karpathy actually uses.

**Cost:** Cursor subscription (~$20/mo). **Time per source:** 2–5 min.

**Use case:** You already use Cursor. You want the agent integrated into your IDE. Works well for developer-heavy wikis.

---

## Combo J: ChatGPT Chat (Zero-Install Trial)

```
ChatGPT → Paste SCHEMA.md → Paste index.md → Paste source → "Write wiki pages per the schema"
You → Copy output → Create .md files → manually link
```

**Stack:** Any chat LLM + file manager.

**Cost:** Free (ChatGPT free tier). **Time per source:** 15–30 min (lots of copy-paste). **Scale ceiling:** ~10 pages.

**Use case:** Trying the concept. You want to see what an LLM Wiki feels like before installing anything. Good for a weekend experiment.

---

## Which Combo Should You Pick?

```
Are you just learning?               → Combo A (Manual, zero tools)
Want best visuals?                   → Combo B (Manual + Obsidian)
Ready to commit?                     → Combo D (Hermes + Obsidian + NotebookLM)
CLI purist?                          → Combo E (Hermes + Terminal)
Quality over everything?             → Combo F (Claude Code + Obsidian)
Want the absolute best?              → Combo G (Dual-Agent: Claude + Hermes)
Team wiki?                           → Combo H (Codex + GitHub)
Already use Cursor?                  → Combo I (Cursor Agent)
Just trying the concept?             → Combo J (ChatGPT copy-paste)
```

---

*Next: [07 — Skills & Tools](../07-skills-and-tools/)*
