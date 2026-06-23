# 2. Core Concepts — Hindsight Architecture

## The Biomimetic Memory Model

Hindsight's memory structure is inspired by human memory. Instead of storing flat
"chunks" of text, it classifies every piece of information into one of four
interconnected memory networks:

```
┌─────────────────────────────────────────────────────┐
│                  MEMORY BANK                          │
│                                                       │
│  ┌──────────────┐  ┌──────────────┐                  │
│  │  WORLD FACTS  │  │ EXPERIENCES  │  ← Raw inputs    │
│  │  (objective)  │  │ (agent's own)│                  │
│  └──────┬───────┘  └──────┬───────┘                  │
│         │                 │                           │
│         └──────┬──────────┘                           │
│                ▼                                      │
│       ┌────────────────┐                             │
│       │  OBSERVATIONS   │  ← Auto-consolidated        │
│       │  (synthesized)  │     from multiple facts     │
│       └───────┬────────┘                             │
│               │                                       │
│               ▼                                       │
│       ┌────────────────┐                             │
│       │ MENTAL MODELS   │  ← User-curated knowledge   │
│       │  (curated)      │     takes highest priority  │
│       └────────────────┘                             │
│                                                       │
│       ┌────────────────┐                             │
│       │   OPINIONS      │  ← Beliefs with confidence  │
│       │  (subjective)   │     formed during reflect() │
│       └────────────────┘                             │
└─────────────────────────────────────────────────────┘
```

---

## The Four Memory Types

### 1. World Facts
**Objective facts about the world.** External information fed into the agent.

| Example | Entity |
|---------|--------|
| "Alice works at Google" | Alice, Google |
| "The product ships to 37 countries" | product |
| "PostgreSQL 14+ is required for pgvector" | PostgreSQL, pgvector |

World facts are **timeless** — they describe reality as reported at a point in time.
When new contradictory information arrives, Hindsight creates a new fact rather
than overwriting. Observations handle the reconciliation.

### 2. Experience Facts
**The agent's own actions and interactions.** First-person ("I did X").

| Example | Context |
|---------|---------|
| "I recommended Python to Bob on March 3rd" | Agent action |
| "I ran the deployment script and it failed with error E302" | Tool result |
| "I asked the user for clarification about the database choice" | Conversation turn |

Experiences are **timestamped** and **owned by the agent**. They build the agent's
sense of "what happened when I tried X."

### 3. Observations
**Automatically consolidated knowledge from multiple facts.** Hindsight's "aha" moments.

Observations are NOT manually created. They emerge from the **observation consolidation
process** that runs after `retain()`:

- **Deduplication**: "Alice works at Google" + "Alice is a Googler" → single observation
- **Evidence tracking**: Each observation cites source facts with exact quotes
- **Continuous refinement**: New evidence updates (not overwrites) observations
- **Freshness awareness**: When newer unconsolidated memories exist, `reflect()` treats
  affected observations as "stale" and verifies them against raw facts

Example: After processing 20 user interactions about coding preferences, an observation
might emerge: *"User consistently prefers functional over OOP patterns (15 examples, high confidence)"*

### 4. Mental Models
**User-curated summary knowledge.** The highest-priority knowledge layer.

Unlike observations (auto-generated), mental models are explicitly created by users
or agents. They represent distilled wisdom:

| Mental Model | Use Case |
|-------------|----------|
| "Team communication best practices" | Onboarding context for new team members |
| "Project Alpha architecture decisions (as of Q2)" | Reference for all Alpha-related work |
| "Known pitfalls when deploying to staging" | Pre-flight checklist for agents |

During `reflect()`, retrieval priority is: **Mental Models → Observations → Raw Facts**.

### 5. Opinions
**Subjective beliefs with confidence scores.** Formed during `reflect()` calls.

Opinions capture what the agent *thinks* (not just what it *knows*):
- "User likely prefers Python over JavaScript" — confidence: 0.78
- "This deployment approach is risky given past failures" — confidence: 0.92
- "Customer is price-sensitive but values speed" — confidence: 0.65

Confidence scores update as new evidence arrives.

---

## The Three Core Operations

### retain(content) — Store
```
Raw text  →  LLM Extraction  →  Canonical Facts  →  Index (4 paths)
                │
                ├── Entity extraction (Alice, Google, Mountain View)
                ├── Relationship detection (works_at, located_in)
                ├── Temporal tagging (when did this happen?)
                └── Fact normalization (canonical representation)
```

Key point: **Nothing is stored as raw transcript.** Every `retain()` call goes through
LLM-powered extraction that converts unstructured text into structured, indexable facts.

### recall(query) — Search (TEMPR)

Four strategies run **in parallel**:

| Strategy | Engine | Best for |
|----------|--------|----------|
| **Semantic** | Vector embeddings (pgvector) | Conceptual similarity, paraphrasing |
| **Keyword** | BM25 full-text search | Names, technical terms, exact matches |
| **Graph** | Entity relationship traversal | Connected facts, indirect links |
| **Temporal** | Time-range filtering | "last spring", "in June", recency |

Results are merged using **Reciprocal Rank Fusion (RRF)** and then **reranked by a
cross-encoder model** before being trimmed to fit the token budget.

### reflect(query) — Reason
```
Query  →  Recall relevant memories  →  Synthesize using LLM
                                          │
                                          ├── Applies mission context
                                          ├── Respects directives (hard rules)
                                          └── Influenced by disposition traits
```

`reflect()` doesn't just retrieve — it **reasons**. It looks at evidence, considers
the bank's personality (disposition), and produces a belief-grounded answer.

---

## Entity Graph

Hindsight automatically builds an **entity graph** from retained facts:

```
Alice ──works_at──▶ Google ──located_in──▶ Mountain View
  │                                           │
  └──colleague_of──▶ Bob ──works_at────────────┘
```

This graph enables:
- **Graph traversal during recall**: "Who are Alice's colleagues?" finds Bob through
  the `colleague_of` relationship even if the query doesn't mention Google.
- **Indirect fact inference**: "Where does Alice work?" can be answered by traversing
  Alice → Google → Mountain View.
- **Relationship-aware retrieval**: Connected facts surface together.

---

## Observation Consolidation

This is Hindsight's secret sauce — what makes it a *learning* system, not just a
database.

### How It Works

1. **After every `retain()` call**, Hindsight checks if new facts relate to existing ones.
2. Related facts are **merged into observations** — deduplicated, evidence-grounded beliefs.
3. Each observation tracks:
   - **Source memories** (with exact quotes)
   - **Proof count** (how many facts support it)
   - **History** (how the observation evolved over time)
4. When contradictory evidence arrives, the observation is **updated** (not overwritten),
   preserving the full history.

### Example: Consolidation in Action

```python
# Day 1
client.retain(bank_id="b", content="User uses React for frontend")
client.retain(bank_id="b", content="User prefers TypeScript over JavaScript")
# → Observation: "User is a React developer who uses TypeScript"

# Day 30
client.retain(bank_id="b", content="User is migrating from React to Vue")
# → Observation UPDATED: "User was a React enthusiast but is now switching to Vue"
#   (history preserved: can see when the shift happened)
```

---

## Mission, Directives & Disposition

These configuration settings shape how `reflect()` reasons. They do NOT affect `recall()`.

### Mission
**Natural-language identity.** Tells Hindsight what knowledge to prioritize.

```python
mission = """
I am a research assistant specializing in machine learning.
I prefer simplicity and proven approaches over cutting-edge.
I track user preferences about ML frameworks and datasets.
"""
```

### Directives
**Hard rules — guardrails.** Must never be violated.

```python
directives = [
    "Never recommend specific stocks or financial instruments.",
    "Always cite sources when providing factual claims.",
    "If uncertain, ask for clarification rather than guessing.",
]
```

### Disposition
**Soft personality traits** (scale 1–5) that influence reasoning style:

| Trait | 1 (low) | 5 (high) |
|-------|---------|----------|
| **Skepticism** | Trusting — accepts claims at face value | Skeptical — demands strong evidence |
| **Literalism** | Flexible — reads between the lines | Literal — takes statements at exact word |
| **Empathy** | Detached — purely analytical | Empathetic — considers emotional context |

---

## Key Design Principles

1. **Structure over storage**: Store structured facts, not raw text. This enables
   deduplication, consolidation, and multi-strategy retrieval.

2. **Compose, don't overwrite**: New information adds to the memory graph. Contradictions
   create updated observations with preserved history.

3. **Evidence over claims**: Every observation and opinion traces back to source facts.
   Confidence scores quantify uncertainty.

4. **Learning is the default**: Observations automatically consolidate. Mental models
   accumulate. The system gets smarter with use.

5. **Separation of concerns**: World facts ≠ experiences ≠ observations ≠ opinions.
   Conflating them corrupts state over time.

---

Now continue to the deep dives:
- **[03_retain.md](03_retain.md)** — Master the retain operation
- **[04_recall.md](04_recall.md)** — Master TEMPR multi-strategy retrieval
- **[05_reflect.md](05_reflect.md)** — Master disposition-aware reasoning
