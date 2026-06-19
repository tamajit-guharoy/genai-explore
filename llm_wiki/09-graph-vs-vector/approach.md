# Graph vs Vector: When the Wiki Replaces RAG

> The LLM Wiki isn't originally framed as a RAG replacement — but it genuinely beats RAG when documents have complex relationships. Here's why, when, and how.

---

## Part 1: What the LLM Wiki Actually Is (Clarified)

The LLM Wiki is often misunderstood as either "self-improving agents" or "RAG replacement." It's neither — but both get invoked to explain it. Here's the clear picture.

### The Core Idea

The LLM Wiki is a **new paradigm for personal knowledge management**. The division of labor:

```
Traditional:  You read sources → You organize → You write notes → You query
LLM Wiki:     You curate sources → Agent builds wiki → Agent maintains → You query
```

Karpathy's own words: *"Instead of you maintaining a knowledge base and occasionally asking an AI questions, an AI maintains the knowledge base and you occasionally read it."*

### Three Layers of Improvement (Why People Confuse It)

The wiki pattern operates at three levels. Only Level 1 is essential:

```
Level 1: WIKI COMPOUNDS (more sources → richer pages → better answers)
         ↑ THE CORE IDEA. Works with ANY agent, even stateless ones.
         ↑ One topic → 100 pages, 400K words. Karpathy never wrote a word.

Level 2: AGENT REMEMBERS YOU (preferences, conventions, corrections)
         ↑ Persistent memory (Hermes Agent). Nice multiplier, not essential.
         ↑ "The agent that remembers you always beats the one that doesn't."

Level 3: AGENT REMEMBERS HOW (skills improve with reuse)
         ↑ Self-improving procedural memory (Hermes Agent skills).
         ↑ Failed approaches auto-corrected. Workflows get faster.
```

**Level 1 is Karpathy's original insight.** It's transformative on its own. Levels 2 and 3 are accelerants that make it even better over time, but they're not the engine.

### Why People Compare It to RAG

Karpathy made the RAG comparison to explain **why he chose structured pages over vector search**. It's a design rationale, not the core claim:

| | RAG | LLM Wiki |
|---|---|---|
| Retrieval | Semantic similarity over flat chunks | Navigate structured, interlinked pages |
| Synthesis | Re-derived every query | Compiled once, kept current |
| Cross-references | None (chunks are isolated) | Built-in via `[[wikilinks]]` |
| Compounding | Zero — every query starts fresh | Accumulates with every source |
| Contradictions | Silently returned (both sides) | Explicitly flagged in frontmatter |

RAG and Wiki are **different architectures for different use cases**. The wiki isn't a "better RAG" — it's a different thing. But in domains with complex document relationships, it genuinely produces better answers.

### Summary: What It Is vs What It Isn't

| Claim | True? | Clarification |
|---|---|---|
| "It's about self-improving agents" | Partially | Agent improvement is a multiplier (Level 2–3), not the core idea (Level 1) |
| "It's a RAG replacement" | Sometimes | For complex relational documents, yes. For flat fact retrieval, RAG is fine |
| "It's a new knowledge management paradigm" | Yes | Human curates sources → agent builds/maintains → human queries. That's the shift |
| "It's a knowledge graph in markdown" | Yes | Pages are nodes, `[[wikilinks]]` are edges, frontmatter is metadata |
| "It makes RAG pipelines obsolete" | No | Complementary — RAG for discovery, wiki for synthesis |

---

## Part 2: Where RAG Fails — And Why the Wiki Wins

RAG is elegant: chunk documents, embed chunks, search by similarity, inject into context. It works wonderfully for flat fact retrieval. But it has a structural blind spot: **semantic similarity ≠ narrative connection**.

### The Core Problem

RAG treats every chunk as an independent island in embedding space. But real documents form graphs:

- Paper A cites Paper B for a specific finding
- Document X describes an acquisition; Document Y describes the consequences
- Regulation R1 modifies Regulation R2, which was challenged in Case C
- Code module M1 calls M2, which depends on library L3

These are **graph relationships** — citations, causality, dependency, hierarchy. RAG's flat embedding space can't represent them. Two chunks can be causally connected but live in different embedding neighborhoods.

### Failure Mode 1: Causal Chains

**Documents:**
```
Doc A: "Company X acquired Company Y for $2B in Q3 2024."
Doc B: "Company X discontinued Product Z (formerly Company Y's flagship) in Q1 2025."
Doc C: "Company X reported a $500M impairment charge related to the Y acquisition in Q2 2025."
```

**RAG query:** *"What happened with Company X's acquisition of Company Y?"*

RAG retrieves Doc A chunk (high similarity to "acquisition Company Y"). Misses B and C entirely — "discontinued product" and "impairment charge" are in different embedding neighborhoods.

RAG answer: *"Company X acquired Company Y for $2B in Q3 2024."*
**Missing:** Product Z was killed, $500M was written off. RAG told a third of the story.

**Wiki answer:** Agent ingests all three. Builds:

```markdown
# Company X
Acquired [[company-y]] for $2B (Q3 2024). Discontinued [[product-z]] (Q1 2025).
Took $500M writedown on the acquisition (Q2 2025). ^[raw/doc-c.md]
```

Query: agent reads `entities/company-x.md`, follows wikilinks to `entities/company-y.md` and `entities/product-z.md`, returns the full causal chain in one traversal.

### Failure Mode 2: Citation Networks

**Documents (5 academic papers):**
```
Paper A (2020): "Method M achieves 85% accuracy on benchmark B."
Paper B (2021): "We replicate Method M — only 78% accuracy on benchmark B."
Paper C (2021): "Method M improved to 91% with our data augmentation technique D."
Paper D (2022): "Method M fails entirely on out-of-distribution data."
Paper E (2023): "Survey: Method M is the most-cited technique despite replication issues."
```

**RAG query:** *"How well does Method M perform?"*

RAG retrieves chunks from Papers A and C (high similarity: "Method M accuracy 91%"). Returns a glowing picture. Papers B, D, and E are in different embedding regions (they use words like "replicate," "fails," "despite") and never retrieved.

RAG answer: *"Method M achieves 85-91% accuracy on benchmark B."*
**Missing:** Replication issues. Out-of-distribution failure. Most-cited-despite-problems controversy.

**Wiki answer:** Agent ingests all 5 papers. Builds a concept page with all claims, contradictions flagged:

```markdown
---
title: Method M
contested: true
contradictions: []
---

| Claim | Source | Year | Confidence |
|---|---|---|---|
| 85% accuracy on B | Paper A | 2020 | medium |
| Only 78% on replication | Paper B | 2021 | high |
| 91% with augmentation D | Paper C | 2021 | medium |
| Fails on OOD data | Paper D | 2022 | high |
| Most-cited despite issues | Paper E | 2023 | high |

## Synthesis
Method M's reported performance is contested. Early claims (85%) were not replicated
(78%). Improvements require data augmentation (91%) and the method fails on
out-of-distribution data. Despite replication concerns, it remains the most-cited
technique in its subfield — a paradox flagged by Paper E. ^[raw/papers/paper-e.md]
```

Query: agent reads `concepts/method-m.md`, sees the full landscape including the controversy. Returns a nuanced answer with confidence levels.

### Failure Mode 3: Multi-Document Narrative

**Documents (news reports across 6 months):**
```
Jan: "Startup S raises $50M Series A at $500M valuation."
Mar: "Startup S's CEO departs abruptly. No reason given."
Apr: "Former employees allege Startup S inflated revenue figures."
May: "Startup S's lead investor writes down investment by 60%."
Jun: "Startup S lays off 80% of staff, pivots to enterprise."
```

**RAG query:** *"What happened to Startup S?"*

RAG retrieves the Jan article (strongest match for "Startup S") and maybe the Jun one. Misses the middle — the three articles that explain *why* it pivoted.

RAG answer: *"Startup S raised $50M and later pivoted to enterprise."*
**Missing:** The fraud allegations, the CEO departure, the write-down. The narrative arc is invisible to vectors.

**Wiki answer:** Agent ingests all 5. Builds `entities/startup-s.md` with a timeline:

```markdown
## Timeline
1. Jan — Raised $50M Series A at $500M valuation ^[raw/articles/jan.md]
2. Mar — CEO departed abruptly, no reason given ^[raw/articles/mar.md]
3. Apr — Former employees alleged revenue inflation ^[raw/articles/apr.md]
4. May — Lead investor wrote down investment by 60% ^[raw/articles/may.md]
5. Jun — Laid off 80% of staff, pivoted to enterprise ^[raw/articles/jun.md]
```

Query: agent reads the page, returns the full narrative arc with dates and sources.

### Failure Mode 4: Dependency Graphs (Technical Docs)

**Documents:**
```
README.md:       "App requires Python 3.11+ and PostgreSQL 16+"
migration.md:    "V2 migration drops support for SQLite. Must use PostgreSQL."
docker.md:       "Docker image bundles Python 3.10 for compatibility."
changelog.md:    "V2.1 upgrades PostgreSQL requirement from 15 to 16."
bug-report.md:   "App crashes with PostgreSQL 15 after upgrade to V2.1."
```

**RAG query:** *"What database version do I need?"*

RAG retrieves README.md chunk: "PostgreSQL 16+." Misses the nuance — why 16, what happens with 15, the SQLite drop, the Docker complication.

RAG answer: *"PostgreSQL 16+."*
**Missing:** Context about the migration, the crash bug, the Docker mismatch.

**Wiki answer:** Agent ingests all, cross-references, builds `concepts/database-requirements.md`:

```markdown
## Database Requirements
- **Minimum:** PostgreSQL 16+ (required since V2.1) ^[raw/docs/changelog.md]
- **Migration note:** V2 dropped SQLite support entirely ^[raw/docs/migration.md]
- **Known issue:** PostgreSQL 15 crashes after V2.1 upgrade ^[raw/docs/bug-report.md]
- **Docker caveat:** Docker image currently bundles Python 3.10, creating a
  compatibility gap with the Python 3.11+ requirement ^[raw/docs/docker.md]
```

Query: agent returns the full matrix — version, migration path, known bugs, container caveat.

---

## Part 3: The Architecture — Graph-Based Retrieval Without Vectors

What's happening in all these examples is fundamentally different from RAG:

```
RAG:
  Query → Embed query vector → Cosine similarity search → Inject top-K chunks → Generate

Wiki (Graph-Based Retrieval):
  Query → Read index.md → Identify relevant pages → Read pages → Follow [[wikilinks]]
         → Read linked pages → Synthesize across the graph → Generate
```

**No vectors. No embeddings. No chunking. No cosine similarity.**

The retrieval quality comes from the **knowledge graph the agent built**, not from embedding alignment. The graph is:

| Graph Element | Wiki Equivalent |
|---|---|
| Nodes | Wiki pages (entities, concepts, comparisons) |
| Edges | `[[wikilinks]]` between pages |
| Node metadata | YAML frontmatter (tags, dates, confidence, sources) |
| Edge types | Implicit in the linking context (cites, contradicts, extends, depends-on) |
| Graph traversal | Agent reads page → follows wikilinks → reads linked pages |
| Centrality | Pages with most inbound wikilinks are most important |

### Query Resolution Algorithm (What the Agent Does)

```
1. PARSE QUERY
   "What do we know about X?"

2. LOCATE ENTRY POINTS
   → Read index.md → find pages mentioning X
   → Or: search_files "X" across wiki/*.md
   → Returns: [entities/x.md, concepts/related-concept.md]

3. READ PRIMARY PAGES
   → read_file entities/x.md
   → Extract facts, claims, relationships, source references

4. TRAVERSE THE GRAPH
   → For each [[wikilink]] in the page:
       If relevant to query → read linked page
       If linked page has relevant [[wikilinks]] → read those too
   → Depth: typically 1-2 hops. Can go deeper for specific questions.

5. SYNTHESIZE
   → Compile findings across all read pages
   → Note contradictions (from frontmatter: contested, contradictions)
   → Note confidence levels
   → Cite sources (provenance markers ^[raw/...])

6. FORMULATE ANSWER
   → Return synthesis with citations
   → Optionally file as queries/ page if substantial
```

### Why This Beats RAG for Complex Documents

| Property | RAG (Vector) | Wiki (Graph) |
|---|---|---|
| Handles causal chains | ❌ Chunks don't know what comes before/after | ✓ Pages linked in sequence |
| Handles citations | ❌ Citation text in different embedding region | ✓ Citation explicitly linked via [[page]] |
| Handles contradictions | ❌ Returns both sides without flagging | ✓ Flagged in frontmatter, synthesis notes both |
| Handles narrative arcs | ❌ No temporal awareness between chunks | ✓ Timeline sections in entity pages |
| Handles dependency graphs | ❌ "Requires X" text doesn't match "X version" embedding | ✓ Dependencies explicitly linked |
| Handles confidence/quality | ❌ All chunks weighted equally | ✓ Confidence field in frontmatter |
| Cost per query | Medium (embedding + LLM) | Low (reading pages, no embedding step) |
| Cost to build | Low (just chunk and index) | High upfront (agent builds wiki) |
| Amortization | Flat — same cost per query forever | Declining — build once, cheap queries forever |

### When RAG Is Still Better

| Scenario | Why RAG Wins |
|---|---|
| One-off document set (query once, never return) | Wiki build cost isn't amortized |
| Very large corpora (100K+ docs) | Wiki build time becomes prohibitive; RAG scales better |
| Need verbatim passages | RAG returns exact chunks; wiki summarizes |
| Exploratory search ("find anything about X") | RAG's fuzzy matching excels at discovery |
| Frequently changing documents | Wiki requires re-ingestion; RAG re-indexes quickly |
| No curation desired | Wiki requires human source selection; RAG is automatic |

---

## Part 4: Can We Fine-Tune a Model for This?

Short answer: yes, but the more practical path is different.

### What You'd Fine-Tune For
A model specifically trained on wiki-building tasks — given raw source(s), produce structured pages with correct `[[wikilinks]]`, accurate frontmatter, and provenance markers.

**Feasibility:** Medium-high. The task is well-defined:
- Input: Raw document(s) + SCHEMA.md + existing wiki pages
- Output: New/updated wiki pages with frontmatter, wikilinks, provenance markers

Training data could come from Wikipedia itself (massive dataset of raw sources → structured interlinked articles).

**What would improve with fine-tuning:**
- Extraction precision (fewer missed entities)
- Link prediction accuracy (which pages should connect)
- Contradiction detection (spotting when new info conflicts with existing)
- Confidence calibration (reliable high/medium/low judgments)
- Schema adherence (following SCHEMA.md conventions more consistently)

### Why Fine-Tuning Isn't the Priority

Frontier models (Claude, GPT-4, DeepSeek V3) already do wiki-building well with good prompting. The bottlenecks are usually:

1. **Agent runtime quality** — Can it read/write many files? Does it have persistent memory? Can it schedule maintenance?
2. **Schema quality** — A well-written SCHEMA.md improves output more than a better model with a vague schema
3. **Skill quality** — The `llm-wiki` skill is effectively "prompt-tuning" without touching model weights
4. **Feedback loops** — Lint → find issues → agent fixes them → wiki improves. This cycle matters more than model quality

Think of it like: fine-tuning the model is 10% improvement for 90% effort. Better schema + skills + linter feedback is 80% improvement for 10% effort.

### The Real Tuning Target: Agent + Schema + Skills

What actually makes wikis better:

| Intervention | Impact | Effort |
|---|---|---|
| Domain-specific SCHEMA.md with precise tag taxonomy | High | Low (write once) |
| Well-crafted `llm-wiki` skill with pitfalls | High | Medium |
| Persistent agent memory (remembers conventions) | Medium | Low (use Hermes) |
| Automated lint → fix → verify loop | High | Low (use cron) |
| Multi-model strategy (Claude for complex, cheap model for routine) | Medium | Low |
| Fine-tuned extraction model | Low-Medium | High (data, training, eval) |

### The Pragmatic Path

1. Start with a frontier model + good schema + agent skill → 90% quality
2. Add persistent memory + cron linting → 95% quality
3. If you have 10K+ wiki pages and need the last 5%, then consider fine-tuning

For most users, step 1 is sufficient. Step 2 adds compounding benefits. Step 3 is for specialized production systems.

---

## Part 5: Building a Non-Vectorized RAG System

If you wanted to package the wiki pattern as a formal "retrieval system" that replaces RAG for complex documents:

### System Architecture

```
┌─────────────┐    ┌──────────────┐    ┌──────────────┐
│ Raw Sources  │───▶│ Agent Builds │───▶│  Wiki Pages  │
│ (docs, PDFs) │    │    Wiki      │    │  (markdown)  │
└─────────────┘    └──────────────┘    └──────┬───────┘
                                              │
                    ┌─────────────────────────┘
                    ▼
            ┌──────────────┐    ┌──────────────┐
            │   Query      │───▶│ Graph Traverse│
            │ (user asks)  │    │  (read pages) │
            └──────────────┘    └──────┬───────┘
                                       │
                                       ▼
                               ┌──────────────┐
                               │   Synthesize │
                               │  (LLM + pages)│
                               └──────────────┘
```

### Query Pipeline (No Vectors)

```
1. QUERY → INDEX LOOKUP
   "What's the relationship between X and Y?"
   → grep index.md for X and Y
   → Find: entities/x.md, entities/y.md

2. PRIMARY PAGE READ
   → read_file entities/x.md
   → Extract: [[wikilinks]], facts, sources
   → Find: "X acquired Y in 2024" with [[company-y]] link

3. GRAPH TRAVERSAL
   → Follow [[company-y]] → read entities/company-y.md
   → Extract: "Acquired by X, product Z discontinued"
   → Follow [[product-z]] → read entities/product-z.md
   → Extract: "Discontinued post-acquisition"
   → Stop: no more relevant wikilinks at depth 2

4. SYNTHESIS
   → Compile: X acquired Y → Y's product Z discontinued
   → Check: any contradictions? (frontmatter check)
   → Cite: ^[raw/acquisition-report.md], ^[raw/product-discontinuation.md]

5. RESPONSE
   "X acquired Y in 2024. Following the acquisition, Y's flagship
    product Z was discontinued. Sources: acquisition report, product
    discontinuation notice."
```

### When This Makes Sense as a Product

| Criterion | This Approach | Traditional RAG |
|---|---|---|
| Document set size | 10–10,000 docs | 1,000–1,000,000+ docs |
| Document relationships | Complex (citations, causality, dependency) | Simple (mostly independent) |
| Query pattern | Repeated queries on same domain | Ad-hoc, varied queries |
| Cost sensitivity | High per-query cost sensitivity | Cost-tolerant |
| Latency requirement | Low (pages pre-built) | Medium (embedding + search per query) |
| Accuracy requirement | High (structured synthesis) | Medium (retrieval of relevant passages) |
| Maintenance | Scheduled lint + re-ingestion | Re-index on document change |

---

## Part 6: The Hybrid — Graph + Vector

The most powerful approach is combining both:

```
Discovery layer (RAG):   "Find me everything about X across my 500 papers"
                          → Vector search returns relevant passages
                          → Agent reads passages, identifies important but un-wikified entities

Synthesis layer (Wiki):  Agent updates wiki pages with new findings from discovery
                          → Pages now capture what vector search found

Query layer (Wiki):      User asks question → agent traverses wiki graph
                          → If wiki doesn't cover it → fall back to RAG
```

This is how Karpathy himself likely works:
1. New paper drops → RAG-like search: "what's novel here?"
2. Agent ingests paper → updates wiki
3. Future queries → wiki (faster, better synthesis)

The vector search is for **exploration and discovery**. The wiki is for **structured, persistent, compound knowledge**. They're complementary, not competitive.

---

## Summary

| Question | Answer |
|---|---|
| Is the LLM Wiki about self-improving agents? | No — that's a multiplier (Levels 2–3). The core (Level 1) is agent-built structured knowledge |
| Is it a RAG replacement? | In domains with complex document relationships — yes, genuinely. In flat fact retrieval — no, RAG is fine |
| Can you fine-tune a model for it? | Yes, but schema + skills + linting give 90% of the gain for 10% of the effort |
| What's the retrieval mechanism? | Graph traversal over interlinked wiki pages — no vectors, no embeddings |
| Where does it beat RAG hardest? | Causal chains, citation networks, multi-document narratives, dependency graphs |
| Where is RAG still better? | One-off corpora, 100K+ docs, verbatim passage retrieval, zero-curation scenarios |
| Best overall approach? | Hybrid — RAG for discovery, wiki for synthesis and query |

---

*Next: [08 — Pros & Cons](../08-pros-cons/comparison.md) for the broader comparison across all approaches.*
