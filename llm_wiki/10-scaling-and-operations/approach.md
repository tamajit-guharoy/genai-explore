# Scaling & Operations: Managing a Growing Wiki

> How to add, update, and delete knowledge. What happens to speed and tokens as the wiki grows. And how to scale from 10 pages to 1 TB.

---

## Part 1: Adding New Raw Files to Existing Knowledge

This is the ingest workflow — the most frequent operation. Done right, new sources enrich existing pages rather than creating duplicates. Done wrong, the wiki fragments.

### The Standard Ingest Flow

```
1. DROP source in raw/
   raw/articles/new-paper-2026.md

2. ASK agent to ingest
   "Ingest raw/articles/new-paper-2026.md"

3. AGENT: ORIENT
   → Read SCHEMA.md (conventions)
   → Read index.md (what exists?)

4. AGENT: EXTRACT from source
   → Entities: [Company X, Person Y, Product Z]
   → Concepts: [Technique A, Pattern B]
   → Claims: [X outperforms Y on benchmark Z]

5. AGENT: CROSS-CHECK (CRITICAL — prevents duplicates)
   → For EACH extracted entity/concept:
       grep index.md for existing pages
       OR: search_files "Entity Name" across wiki/
   → Results:
       "Company X" → entities/company-x.md EXISTS → will UPDATE
       "Person Y" → NO existing page → will CREATE
       "Technique A" → concepts/technique-a.md EXISTS → will UPDATE
       "Pattern B" → NO existing page → but only mentioned once → SKIP (threshold)

6. AGENT: WRITE/UPDATES
   → CREATE entities/person-y.md (new)
   → UPDATE entities/company-x.md (add new info, bump updated date)
   → UPDATE concepts/technique-a.md (add new findings)

7. AGENT: CROSS-REFERENCE
   → New page [[person-y]] must link to 2+ existing pages
   → Updated pages must link to [[person-y]] if relevant
   → Check: does [[company-x]] already link to [[person-y]]? If not, add.

8. AGENT: UPDATE NAVIGATION
   → Add [[person-y]] to index.md under Entities
   → Bump "Last updated" date in index header
   → Append to log.md

9. AGENT: REPORT
   "Ingested new-paper-2026.md. Created 1 page (entities/person-y.md).
    Updated 2 pages (entities/company-x.md, concepts/technique-a.md).
    No contradictions found. Wiki now: 24 pages."
```

### Bulk Ingest (Multiple Sources at Once)

When adding 5+ new sources simultaneously, batch the cross-check step:

```
BAD (inefficient — 5 separate ingestions):
  Ingest doc1 → cross-check → write → cross-ref → update index → log
  Ingest doc2 → cross-check → write → cross-ref → update index → log
  ...repeats 5x, each cross-check is redundant, each index update is a point write

GOOD (efficient — one batch):
  1. Read ALL 5 sources
  2. Extract entities/concepts across ALL sources (one pass)
  3. Cross-check ALL extracted items against index.md (one pass)
  4. Create ALL new pages in one batch
  5. Update ALL existing pages in one batch (each page touched once)
  6. Cross-reference everything in one pass
  7. Update index.md ONCE
  8. Write ONE log entry
```

This avoids updating the same page 5 times when 3 sources all mention the same entity.

### Deduplication: How the Agent Avoids Creating Duplicate Pages

The agent uses multiple strategies:

| Strategy | How It Works | Example |
|---|---|---|
| **Index scan** | Read index.md — all pages listed. If entity is there, page exists. | "Anthropic" → in index → entities/anthropic.md exists |
| **Filename search** | `search_files "anthropic" target="files"` → finds exact filename | `entities/anthropic.md` found |
| **Content search** | `search_files "Anthropic" target="content"` → finds mentions even if not a page | Finds "Anthropic" mentioned in `entities/claude.md` — maybe needs its own page? |
| **Fuzzy name matching** | "Andrej Karpathy" vs "Karpathy, Andrej" vs "A. Karpathy" | Agent normalizes to canonical name; checks all variants |
| **Frontmatter scan** | `search_files "tags:.*person"` — find all person-entity pages | Checks if person already exists under a different filename |

### What Happens When a Source Contradicts Existing Knowledge

This is the most important case. The agent follows SCHEMA.md's Update Policy:

```
1. CHECK DATES
   New source (2025) contradicts existing page claim from old source (2020)
   → Newer source generally supersedes, BUT...

2. CHECK CONFIDENCE
   Existing claim: confidence: high (backed by 3 sources)
   New claim: single source, preprint
   → Don't overwrite. Note BOTH.

3. FLAG THE CONTRADICTION
   In existing page frontmatter:
   contested: true
   contradictions: [new-source-filename]

   In page body, add:
   ## Contested
   - Claim A (2020, 3 sources): X = 94% ^[raw/papers/old-paper.md]
   - Claim B (2025, 1 source): X = 89% ^[raw/papers/new-paper.md]
   - ⚠️ UNRESOLVED: Awaiting additional replication. Flag for human review.

4. LOG IT
   Append to log.md: "## 2025-07-15 | ingest | New claim contradicts existing"
```

The agent NEVER silently overwrites. Contradictions are surfaced, not resolved. The human decides.

---

## Part 2: Deleting and Updating Existing Knowledge

### Updating Wiki Pages

Wiki pages are mutable — that's the point. They evolve as new sources arrive.

**Updating facts:**
```markdown
# Before (entity page)
OpenAI was founded in 2015 by Elon Musk, Sam Altman, and others.

# After (new source clarifies)
OpenAI was founded in 2015 by Sam Altman, Greg Brockman, Elon Musk,
Ilya Sutskever, and others. Musk departed the board in 2018. ^[raw/articles/openai-history.md]
```

The `updated` date in frontmatter bumps. The old claim is preserved in the raw source (immutable) and in log.md (version history).

**Updating when a page gets too long:**
```markdown
# entities/openai.md grows to 250 lines → SCHEMA.md says split at 200

# Split into:
entities/openai.md            ← overview, history, key people
entities/openai-gpt-models.md ← GPT-1 through GPT-5, architecture, benchmarks
entities/openai-products.md   ← ChatGPT, Codex, API, DALL-E
```

All three cross-link to each other. The index is updated. The original long page is archived.

### Deleting Knowledge

There are three scenarios:

#### 1. Deleting a Raw Source (The Source Was Wrong)

**Principle:** Raw sources are IMMUTABLE. Don't delete them — annotate instead.

```markdown
# raw/articles/flawed-paper.md

---
source_url: https://example.com/flawed-paper
ingested: 2025-01-15
sha256: abc123
status: SUPERSEDED  # ← add this
superseded_by: raw/articles/correction-2025.md
superseded_reason: "Paper retracted by authors. Methodology error in Section 3."
---
```

The wiki pages that cited this source will have their `sources:` updated and claims annotated with "retracted." The raw file stays for provenance — you want to know you once believed this.

#### 2. Deleting a Wiki Page (The Page Is No Longer Relevant)

**Process: Archiving, not deleting.**

```bash
# Move to archive (preserves history)
mkdir -p wiki/_archive/entities
mv wiki/entities/old-company.md wiki/_archive/entities/old-company.md

# Remove from index.md
# Update pages that linked to it:
#   Replace [[old-company]] with "Old Company (archived — acquired by Google, 2023)"

# Log
## 2025-07-15 | archive | old-company.md — acquired, no longer independent
```

Archiving preserves the knowledge graph's history. If someone asks "what happened to Old Company?" the archive has the answer. The index no longer lists it (it's not "current knowledge") but it's retrievable if needed.

#### 3. Deleting Incorrect Information from a Wiki Page

Don't delete — correct and annotate:

```markdown
# Before
SparseFormer achieves 94.2% on GLUE. ^[raw/papers/paper-a.md]

# After (with correction)
SparseFormer originally claimed 94.2% on GLUE. ^[raw/papers/paper-a.md]
This was not replicated; independent evaluation found 89.1%. ^[raw/papers/paper-b.md]
The authors later corrected to 91.7% using standard evaluation. ^[raw/papers/paper-d.md]
```

The incorrect claim is preserved WITH its correction. Future readers see the full evolution of knowledge, not a sanitized final answer.

### The Philosophy: Append, Don't Overwrite

```
Wrong approach:  "Delete the wrong claim. Write the right one."
Right approach:  "The original claim was X (source A, 2020).
                  This was contradicted by Y (source B, 2021).
                  Current consensus is Z (sources C, D; 2025)."
```

This is the difference between a wiki and a blog post. A blog post can be silently updated. A wiki should show the evolution of understanding. The provenance markers and contradiction flags make this possible.

---

## Part 3: Token Usage and Speed as the Wiki Grows

The honest answer: queries get slightly more expensive as the wiki grows, but the relationship is sub-linear, and with architecture choices it can be near-constant.

### How a Query Works (Token Breakdown)

```
Query: "What do we know about attention mechanisms?"

1. INDEX SCAN (~500–5,000 tokens)
   → Read index.md → find relevant pages
   → 100 pages:   index is ~100 lines → ~1,500 tokens
   → 1,000 pages: index is ~1,000 lines → ~15,000 tokens
   → 10,000 pages: index is ~10,000 lines → ~150,000 tokens ← PROBLEM

2. PAGE READS (~2,000–10,000 tokens per page)
   → Read concepts/attention-mechanism.md (~3,000 tokens)
   → Read concepts/transformer-architecture.md (~4,000 tokens)
   → Follow wikilinks → read concepts/multi-head-attention.md (~3,000 tokens)
   → Total page tokens: ~10,000
   → KEY INSIGHT: page read count depends on query DEPTH, not wiki SIZE
   → A 100-page wiki and a 10,000-page wiki: same query reads ~3 pages

3. SYNTHESIS (~1,000–3,000 tokens)
   → Agent combines page contents into answer
   → Output tokens scale with answer length, not wiki size

TOTAL for 100-page wiki:   ~1,500 (index) + ~10,000 (pages) + ~2,000 (output) = ~13,500 tokens
TOTAL for 1,000-page wiki: ~15,000 (index) + ~10,000 (pages) + ~2,000 (output) = ~27,000 tokens
```

### The Index Is the Scaling Bottleneck

Everything else is near-constant per query. The index.md grows linearly with page count. Here's when it becomes a problem:

| Pages | Index Lines | Index Tokens | Problem? |
|---|---|---|---|
| 100 | 100 | ~1,500 | No |
| 500 | 500 | ~7,500 | No |
| 1,000 | 1,000 | ~15,000 | Borderline — still fits in context |
| 5,000 | 5,000 | ~75,000 | Yes — too many tokens to read |
| 10,000 | 10,000 | ~150,000 | Yes — exceeds most context windows |

### Solution: Multi-Level Index (Hierarchical Navigation)

Don't have ONE flat index. Have a pyramid:

```
index.md (TOPIC MAP) — 50 lines, ~750 tokens
  ├── "Transformer architectures" → see topic-index/transformers.md
  ├── "AI agents" → see topic-index/ai-agents.md
  ├── "Training techniques" → see topic-index/training.md
  └── ...

topic-index/transformers.md (SECTION INDEX) — 30 lines, ~450 tokens
  ├── [[attention-mechanism]] — Core operation, scaled dot-product
  ├── [[multi-head-attention]] — Parallel attention heads
  ├── [[transformer-architecture]] — Full encoder-decoder design
  ├── [[sparse-attention]] — O(n log n) alternatives
  └── ...

topic-index/ai-agents.md (SECTION INDEX) — 25 lines, ~400 tokens
  ├── [[ai-agents]] — Concept overview
  ├── [[tool-use]] — Agent tool invocation
  ├── [[agent-comparison-2026]] — Feature matrix
  └── ...
```

**Query resolution with hierarchy:**
```
1. Read index.md (50 lines, 750 tokens) → find "Transformers" topic
2. Read topic-index/transformers.md (30 lines, 450 tokens) → find relevant pages
3. Read the 3 relevant pages (~10,000 tokens)
TOTAL: ~11,200 tokens — NEAR-CONSTANT regardless of total wiki size
```

A 10,000-page wiki with this hierarchy uses roughly the same tokens per query as a 100-page flat wiki. The topic map absorbs the scaling.

### Page Size Governance

Unbounded page size is the second scaling killer:

```markdown
# BAD: One massive page
concepts/transformers.md → 5,000 lines, 75,000 tokens
# Every query about transformers reads 75K tokens even if you only need attention

# GOOD: Split at 200 lines (per SCHEMA.md)
concepts/transformer-architecture.md  → 150 lines (overview)
concepts/attention-mechanism.md       → 180 lines (deep dive)
concepts/multi-head-attention.md      → 120 lines (variant)
concepts/positional-encoding.md       → 100 lines (sub-component)
concepts/transformer-variants.md      → 160 lines (BERT, GPT, T5, ViT)
# Query about attention reads ONLY attention-mechanism.md (~2,700 tokens)
```

**Rule:** No wiki page exceeds 200 lines. Split aggressively. Cross-link all fragments.

### The Real Token Economics

For a 1,000-page wiki with proper hierarchy:

```
Query type               | Pages read | Tokens    | Monthly cost (100 queries)
-------------------------|------------|-----------|---------------------------
Simple lookup            | 1 page     | ~3,000    | ~$1.50 (at $5/1M tokens)
Moderate question        | 3 pages    | ~12,000   | ~$6.00
Deep synthesis           | 8 pages    | ~40,000   | ~$20.00
Cross-domain comparison  | 12 pages   | ~60,000   | ~$30.00
Weekly lint (automated)  | All pages  | ~500,000  | ~$2.50 (one run)
```

Compare this to RAG for the same 1,000-document corpus:
- RAG query: embed (~$0.001) + retrieve chunks + inject ~5 chunks (~5,000 tokens) + generate (~2,000 tokens) = ~$0.035/query
- Wiki query (moderate): ~12,000 tokens = ~$0.06/query

Wiki is slightly more expensive per query. But:
- Wiki answers are more complete for complex relationships
- Wiki build cost is paid once (RAG pays retrieval cost every query forever)
- Wiki lint catches issues automatically (RAG has no self-audit)

**Break-even:** After ~50 queries on the same domain, the wiki's amortized build cost is paid off, and the per-query quality advantage is pure profit.

---

## Part 4: Scaling to 1 TB

1 TB is a serious knowledge base. Let's be realistic about what that means and how to handle it.

### What 1 TB of Raw Sources Looks Like

| Content Type | Approximate Size | Count |
|---|---|---|
| Academic papers (PDF) | 1–10 MB each | 100K–1M papers |
| Web articles (markdown) | 10–100 KB each | 10M–100M articles |
| Books (text) | 500 KB–2 MB each | 500K–2M books |
| Transcripts (text) | 50–500 KB each | 2M–20M transcripts |
| Code repositories (text) | 10 MB–1 GB each | 1K–100K repos |

If your raw/ is 1 TB, you have millions of documents. You cannot wiki-fy all of them. You need curation, tiering, and compression.

### Tiered Knowledge Architecture

Not all sources deserve wiki pages. Apply a tier system:

```
TIER 1: Wiki Pages (the structured knowledge graph)
  → Size: ~100 MB (10,000 pages × 10 KB each)
  → What: Synthesized, cross-referenced knowledge
  → Access: Agent reads directly. Near-instant. <50K tokens/query.
  → Covers: Entities, concepts, comparisons that matter

TIER 2: Summarized Sources (compressed raw)
  → Size: ~10 GB (1M summaries × 10 KB each)
  → What: 1-paragraph summaries of every raw source, with metadata
  → Access: Agent searches summaries first; reads full source if needed
  → Covers: Everything ingested, but at summary depth

TIER 3: Raw Sources (the 1 TB)
  → Size: ~1 TB
  → What: Original PDFs, articles, transcripts
  → Access: Agent retrieves specific files on demand. Never reads all at once.
  → Covers: The primary evidence behind Tier 1 and 2
```

**Query resolution at 1 TB scale:**
```
1. Read index.md (topic map, 50 lines) → find topic
2. Read topic index (30 lines) → find wiki pages (TIER 1)
3. Read wiki pages (~10,000 tokens) → answer from structured knowledge
4. IF wiki pages don't cover it → search Tier 2 summaries
5. IF summaries suggest a relevant raw source → retrieve specific file from Tier 3
```

Most queries resolve at step 3. The full 1 TB is never read — it's backing evidence, not search space.

### Compression Strategies

**1. Source Summarization (Tier 2)**

Every raw source gets a one-paragraph summary when ingested. Even at 1M sources × 10 KB summaries = 10 GB — manageable.

```markdown
# tier2-summaries/2025/papers/attention-is-all-you-need.md
---
source: raw/papers/attention-is-all-you-need.md
words: 6,200
entities: [transformer, attention, Vaswani]
concepts: [self-attention, multi-head-attention, positional-encoding]
key_findings: "Transformer achieves SOTA on translation without recurrence.
               BLEU 28.4 EN-DE, 41.0 EN-FR. Faster training than RNN/CNN."
---
```

The agent searches this index (NOT the full raw source) to find relevant documents. Only when a document is highly relevant does it read the full raw file.

**2. Page-to-Summary Cascade**

For very large wikis, pages themselves get compressed summaries:

```
entities/openai.md                                ← full page (5,000 tokens)
entities/_summaries/openai.md                     ← 1-paragraph summary (200 tokens)
topic-index/ai-companies.md                       ← lists all company summaries
```

Query: "What companies work on AI agents?"
→ Read topic-index/ai-companies.md (summaries of 20 companies, ~4,000 tokens)
→ Identify 3 most relevant → read full entities/openai.md, entities/anthropic.md, entities/nous-research.md

**3. Rotating Archives**

Pages not accessed in 6 months → move to `_archive/` → remove from topic indexes. They still exist but don't pollute navigation. If a query needs them, the agent searches `_archive/`.

### Hybrid Search: When the Wiki Gets Too Big for Pure Traversal

At 10K+ pages, even hierarchical indexes become unwieldy. Introduce a lightweight search layer:

```
Query: "What's the relationship between X and Y?"

Option A (pure traversal — best for <5K pages):
  → Read index → topic index → find pages → read pages

Option B (hybrid — best for >5K pages):
  → search_files "X AND Y" across wiki/*.md → find candidate pages (1,000 tokens)
  → Read the top 3 candidate pages (~10,000 tokens)
  → Follow their wikilinks if relevant
```

`search_files` is ripgrep, not embeddings. It's cheap and exact. It's used as a **discovery shortcut**, not as retrieval. The actual answer still comes from reading pages and traversing wikilinks — search just tells you WHICH pages to read.

This keeps the "no vectors" property while scaling past what hierarchical indexes can handle alone.

### The Cost of Scale

| Scale | Pages | Raw Size | Query Tokens | Build Cost | Monthly Maintenance |
|---|---|---|---|---|---|
| **Small** | 100 | 100 MB | ~13K | $2–10 | $1–3 (lint) |
| **Medium** | 1,000 | 1 GB | ~27K | $20–100 | $5–15 |
| **Large** | 10,000 | 10 GB | ~40K (with hierarchy) | $200–1,000 | $25–75 |
| **Huge** | 100,000 | 100 GB | ~50K (hybrid) | $2,000–10,000 | $100–300 |
| **1 TB** | 1M summaries + 10K pages | 1 TB raw + 10 GB summaries | ~60K | $10K–50K | $300–1,000 |

**The build cost is the investment.** Once built, queries are surprisingly cheap even at 1 TB scale because you never read the raw data — you read the compressed knowledge graph.

### What Breaks at 1 TB (And How to Fix It)

| Problem | At What Scale | Fix |
|---|---|---|
| Index.md too large to read | 5K+ pages | Multi-level topic map |
| Page reads too many tokens | Page >200 lines | Split aggressively |
| Can't find relevant pages | 10K+ pages | Hybrid: ripgrep search → read |
| Raw source retrieval too slow | 100K+ raw files | Tier 2 summaries as search index |
| Lint takes too long/tokens | 5K+ pages | Incremental lint (only pages touched since last lint) |
| Index update on every ingest | 1K+ pages | Batch index updates (hourly, not per-source) |
| Cross-referencing too many pages | 10K+ pages | Limit to 2-hop neighborhood for each new page |
| Git repo too large | 1 GB+ wiki | Separate git repos per topic; no raw/ in git |

### Incremental Lint (Don't Lint Everything Every Time)

Naive lint at 10K pages reads every page → 500K tokens → expensive.

```
SMART LINT:
1. Read log.md → find pages modified since last lint (~50 pages)
2. Lint ONLY those 50 pages for frontmatter, wikilinks, index presence
3. Run FULL orphan scan monthly (not weekly) — cheaper as batch
4. Run source drift check quarterly (cheap — just recompute sha256)
```

Weekly lint cost drops from 500K tokens to ~25K tokens.

### Architecture Diagram (1 TB Scale)

```
┌─────────────────────────────────────────────────────┐
│ RAW SOURCES (1 TB)                                   │
│ raw/papers/  raw/articles/  raw/transcripts/  ...    │
│ NEVER SEARCHED DIRECTLY — evidence layer              │
└──────────────────┬──────────────────────────────────┘
                   │ ingested → summarized
                   ▼
┌─────────────────────────────────────────────────────┐
│ TIER 2: SOURCE SUMMARIES (~10 GB)                    │
│ One paragraph per source + metadata                  │
│ SEARCHED by ripgrep — discovery layer                 │
└──────────────────┬──────────────────────────────────┘
                   │ synthesized → wiki pages
                   ▼
┌─────────────────────────────────────────────────────┐
│ TIER 1: WIKI PAGES (~100 MB)                         │
│ entities/  concepts/  comparisons/  queries/         │
│ TRAVERSED by agent — answers come from here           │
└──────────────────┬──────────────────────────────────┘
                   │ navigated via
                   ▼
┌─────────────────────────────────────────────────────┐
│ NAVIGATION LAYER                                     │
│ index.md (topic map, 50 lines)                       │
│   → topic-index/*.md (section indexes, 30 lines)      │
│   → wiki pages                                        │
│ OR: search_files (ripgrep) for discovery              │
└─────────────────────────────────────────────────────┘
```

---

## Part 5: Operational Commands Reference

### Ingestion

```bash
# Single source
"Ingest raw/articles/new-paper.md"

# Bulk
"Ingest all 7 files in raw/papers/"

# From URL
"Ingest https://example.com/article into my wiki"

# From paste
"Ingest this into my wiki: [paste article text]"
```

### Query

```bash
# Simple lookup
"What does my wiki know about attention mechanisms?"

# Cross-domain
"Compare what the wiki says about RLHF vs Constitutional AI"

# With confidence
"What are the low-confidence claims in my wiki about SparseFormer?"

# Timeline
"Show me the timeline of MegaCorp's NanoAI acquisition from the wiki"
```

### Maintenance

```bash
# Full lint
"Lint my wiki"

# Incremental lint (large wikis)
"Lint only pages modified in the last week"

# Find orphans
"Show me wiki pages with no inbound links"

# Find broken links
"Check all [[wikilinks]] in my wiki for broken references"

# Stale content
"Flag wiki pages not updated in 6+ months"

# Contradiction review
"List all contested: true pages in my wiki"
```

### Updates and Deletions

```bash
# Archive a page
"Archive entities/old-company.md — acquired, no longer relevant"

# Mark source as superseded
"Mark raw/articles/retracted-paper.md as superseded by raw/articles/correction.md"

# Split a long page
"entities/openai.md is 280 lines. Split it into separate pages."

# Correct a claim
"Update concepts/sparseformer.md: the 94.2% claim was not replicated.
 Add the 89.1% replication result from raw/papers/replication-study.md"
```

### Scaling Operations

```bash
# Create multi-level index
"My wiki has 800 pages. Create topic indexes to reduce index.md below 50 lines."

# Generate Tier 2 summaries
"Generate one-paragraph summaries for all 500 raw sources"

# Rotate inactive pages
"Archive wiki pages not accessed in 6 months"

# Audit scale
"How many pages, wikilinks, and total tokens is my wiki?"
```

---

## Part 6: Where the Prompts Live — You Never Repeat Yourself

This is the question that determines whether a wiki workflow is sustainable or dead on arrival: *"Do I have to re-explain the ingest procedure every time I add a file?"*

**Answer: No. The instructions live in persistent files that the agent reads automatically.** You speak one-liners. The agent follows the full procedure from its stored knowledge.

### How Each Setup Handles Persistent Instructions

| Setup | Where instructions live | You say | Agent does |
|---|---|---|---|
| **Hermes + llm-wiki skill** | `~/.hermes/skills/research/llm-wiki/SKILL.md` | "Ingest raw/articles/new.md" | Reads skill → follows full 9-step ingest workflow |
| **Hermes + memory** | Agent's SQLite memory DB (auto-saved) | "I prefer short entity pages. Split at 150 lines, not 200." | Remembers preference permanently |
| **Claude Code** | `~/wiki/CLAUDE.md` | "Ingest the new paper in raw/papers/" | Reads CLAUDE.md → follows wiki conventions |
| **Cursor** | `~/wiki/.cursorrules` | "Ingest raw/articles/new.md" | Reads .cursorrules → follows conventions |
| **ChatGPT (manual)** | NOWHERE — you paste it every time | "Here are my wiki conventions: [paste full SCHEMA.md + ingest rules]. Now ingest this: [paste article]" | Follows for this turn only |
| **Codex** | `~/wiki/CODE.md` or `.codexrules` | "Ingest raw/articles/new.md" | Reads CODE.md → follows conventions |

The file-based approaches (Hermes skill, CLAUDE.md, .cursorrules) are **zero-repetition**. You say one sentence per source forever. The manual ChatGPT approach requires re-pasting the full context every session.

### What's Actually in the Instruction File

The instruction file contains the PROCEDURE — the steps, conventions, and rules. Here's the difference between what YOU say and what the AGENT knows:

```
YOU SAY (every time):          AGENT KNOWS (from file, loaded once):

"Ingest raw/articles/          1. Read SCHEMA.md for conventions
 new-paper.md"                 2. Read index.md for existing pages
                               3. Read the source from raw/
                               4. Extract entities, concepts, claims
                               5. Cross-check against existing pages
                                  (search_files, index scan, fuzzy names)
                               6. Apply page thresholds:
                                  - 2+ mentions → create page
                                  - 1 mention, central → create page
                                  - passing mention → skip
                               7. Write new pages with:
                                  - YAML frontmatter (all required fields)
                                  - [[wikilinks]] (min 2 outbound)
                                  - provenance markers ^[raw/...]
                                  - confidence levels
                               8. Update existing pages:
                                  - add new info
                                  - bump updated date
                                  - flag contradictions
                                  - add cross-references to new pages
                               9. Cross-reference: new pages ← → existing
                               10. Update index.md: add new pages
                               11. Append to log.md: all changes
                               12. Report: created X, updated Y, total now Z

One sentence.                 Twelve steps executed automatically.
```

### Hermes Agent: The Skill File (Most Complete)

The `llm-wiki` skill is a detailed markdown file at `~/.hermes/skills/research/llm-wiki/SKILL.md`. It contains:

```markdown
---
name: llm-wiki
description: "Karpathy's LLM Wiki: build/query interlinked markdown KB."
---

# Karpathy's LLM Wiki
[~2,000 words of procedure]

## Core Operations
### 1. Ingest
① Capture the raw source → save to raw/ with frontmatter + sha256
② Discuss takeaways with user
③ Check what already exists → search index + search_files
④ Write or update wiki pages:
   - New entities/concepts: create if meeting Page Thresholds
   - Existing pages: add info, bump updated date, handle contradictions
   - Cross-reference: min 2 outbound [[wikilinks]]
   - Tags: only from SCHEMA.md taxonomy
   - Provenance: ^[raw/...] markers when 3+ sources
⑤ Update navigation: add to index.md, append to log.md
⑥ Report what changed

### 2. Query
① Read index.md → identify relevant pages
② For 100+ page wikis → also search_files for key terms
③ Read relevant pages → synthesize with citations
④ File valuable answers → queries/ or comparisons/
⑤ Update log.md

### 3. Lint
[12-point health check procedure]
```

**Loading mechanism:**
```
Session start → Hermes injects skill list into system prompt
You say "ingest this" → Hermes recognizes the task → invokes skill_view("llm-wiki")
→ Skill content loaded into context → agent follows procedure step by step
```

You never see this. You just say "ingest this" and it works.

### Skill Self-Improvement (The Meta-Loop)

The skill IMPROVES with use. If a step fails during ingestion:

```
Session: Agent tries to cross-reference → misses a page because filename was different
         → User corrects: "You should also check for 'anthropic' not just 'Anthropic Inc'"
         → Agent patches the skill:
           skill_manage(action='patch', name='llm-wiki',
             old_string="Search existing pages for each entity",
             new_string="Search existing pages for each entity using MULTIPLE variants:
                         exact name, lowercase, acronym, and common alternate forms")

Next session: The updated skill is loaded → fuzzy name matching is now standard procedure
              → No user correction needed
```

This is Level 3 from the [graph-vs-vector tutorial](../09-graph-vs-vector/approach.md) — the agent remembers HOW. The instruction file isn't static; it's a living document that gets better every time it's used.

### Claude Code: CLAUDE.md (Simpler, File-Based)

Create `~/wiki/CLAUDE.md`:

```markdown
# Claude Code Instructions for LLM Wiki

When I ask you to "ingest" a source, follow this exact procedure:

1. Read SCHEMA.md for conventions
2. Read index.md to see existing pages
3. Read the new source from raw/
4. Extract entities, concepts, and significant claims
5. For each entity/concept:
   a. Search existing wiki for it (search_files or grep)
   b. If found → UPDATE the existing page
   c. If NOT found AND significant → CREATE new page
   d. If NOT found AND minor → SKIP
6. Every new/updated page MUST have:
   - YAML frontmatter (title, created, updated, type, tags, sources)
   - At least 2 [[wikilinks]] to other wiki pages
   - When 3+ sources: provenance markers ^[raw/...]
7. After ALL pages are written:
   - Update index.md (add new pages under correct section)
   - Append to log.md (timestamp, action, files changed)
   - Report: created X, updated Y, total now Z

File structure:
- raw/ = immutable sources (never edit)
- entities/ = people, companies, products
- concepts/ = ideas, techniques, topics
- comparisons/ = side-by-side analyses
- SCHEMA.md = conventions and rules
- index.md = page catalog
- log.md = action log
```

**Loading mechanism:**
```
Claude Code starts in ~/wiki/ → reads CLAUDE.md automatically
→ CLAUDE.md content injected into system prompt at session start
→ "Ingest raw/articles/new.md" → Claude follows the CLAUDE.md procedure

Next session: CLAUDE.md is re-read → same procedure → no repetition
```

The limitation: Claude Code doesn't auto-update CLAUDE.md (no self-improving skills). You'd manually improve it when you find gaps.

### Stateless Chat: The Repetition Trap

This is what you DON'T want:

```
# Session 1
You: "I have a wiki at ~/wiki. SCHEMA.md defines conventions. When I give you a source,
     you should: [paste 500 words of procedure]. Now ingest this: [paste article]."
Claude: [follows procedure, creates wiki pages]

# Session 2 (new chat — agent remembers NOTHING)
You: "I have a wiki at ~/wiki. SCHEMA.md defines conventions. When I give you a source,
     you should: [paste SAME 500 words again]. Now ingest this: [paste new article]."
Claude: [follows procedure, creates pages]

# Session 50
You: [paste 500 words YET AGAIN] ← this is why people quit manual wikis
```

**This is the single biggest reason to use an agent platform rather than raw chat.** The instruction persistence is what makes a wiki sustainable beyond 3 sources. Without it, every session is a fresh onboarding.

### What Happens When Raw Files Are Added or Removed

**Adding a raw file:**
```
→ Agent detects new file in raw/ (you tell it, or it notices)
→ Agent reads instruction file (skill / CLAUDE.md / .cursorrules)
→ Agent follows ingest procedure
→ Wiki pages created/updated
→ Index updated
→ Log appended
→ Done. The persistency is automatic.
```

**Removing a raw file:**
```
→ You tell the agent: "raw/articles/old-paper.md is retracted"
→ Agent follows procedure from instruction file:
   - Marks raw file as SUPERSEDED (doesn't delete it)
   - Updates wiki pages that cited it:
     "Claim X (originally from retracted paper, 2024) was superseded by Y (2025)"
   - Removes it from source lists
   - Logs the action
→ Done. The raw file stays for provenance.
```

In neither case do you re-explain the procedure. The instruction file handles it.

### The One-Liner Interface

After initial setup, your entire interaction with a well-configured wiki is one-liners:

```
"Ingest raw/articles/new-paper.md"
"Ingest all 5 files in raw/papers/"
"Ingest https://example.com/article"
"Archive entities/old-company.md"
"Split entities/openai.md — it's 280 lines"
"Update concepts/sparseformer.md with findings from raw/papers/replication.md"
"Lint my wiki"
"What does my wiki know about attention mechanisms?"
```

That's it. The instruction file — whether a Hermes skill, CLAUDE.md, or .cursorrules — handles everything else. You never repeat the procedure.

### Setting It Up Once

```bash
# Hermes Agent (best — self-improving instructions)
hermes
> Load the llm-wiki skill
> Build me a wiki for AI/ML research at ~/wiki
# Done. Say "ingest <file>" forever.

# Claude Code
echo "[paste CLAUDE.md content from above]" > ~/wiki/CLAUDE.md
claude  # starts in ~/wiki, reads CLAUDE.md automatically
# Done. Say "ingest <file>" forever.

# Cursor
echo "[paste .cursorrules content]" > ~/wiki/.cursorrules
# Open ~/wiki in Cursor → agent mode reads .cursorrules
# Done. Say "ingest <file>" forever.
```

One-time setup. Lifetime of one-liners.

---

## Summary: The Scaling Playbook

| Scale | Key Strategy |
|---|---|
| 0–100 pages | Flat index.md. Full lint weekly. Simple. |
| 100–1,000 pages | Split pages at 200 lines. Bulk ingest. Incremental lint. |
| 1,000–5,000 pages | Multi-level topic indexes. Batch index updates. Monthly full lint. |
| 5,000–10,000 pages | Hybrid search (ripgrep + traversal). Topic indexes mandatory. |
| 10,000–100,000 pages | Tier 2 source summaries. Incremental everything. Archive cold pages. |
| 1 TB (raw) | Tier 2 summaries as primary search. Wiki stays at 5K–10K pages — the knowledge graph, not the archive. Raw is evidence only. |

**The core insight:** The wiki doesn't scale to 1 TB by having 1M wiki pages. It scales by being a **compressed, structured representation** of 1 TB of sources. The 1 TB lives in raw/. The wiki is the 100 MB lens you use to see it.

---

*Next: [09 — Graph vs Vector](../09-graph-vs-vector/approach.md) for when the wiki beats RAG.*
