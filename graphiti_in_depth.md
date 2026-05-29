# Graphiti In-Depth: The Complete Developer's Handbook

> **A comprehensive guide to building temporal knowledge graphs with Graphiti — from first principles to production.**

---

## PART 0: FOUNDATIONS

### Chapter 0 — Preface & Who This Guide Is For

**Target audience:** This guide is written for AI engineers, agent builders, and developers who have worked with RAG (Retrieval-Augmented Generation) and are hitting its limits — specifically around temporal reasoning and fact evolution. You should be comfortable with Python 3.10+, async/await patterns, and basic LLM concepts (embeddings, prompts, token limits). No prior knowledge of knowledge graphs or Neo4j is assumed.

**What you'll build:** By the end of this guide, you'll have 28 working examples covering everything from a minimal "hello world" to production deployments with custom entity types, multi-provider setups, temporal point-in-time queries, contradiction handling, MCP server integration, and real-world agent memory simulations.

**How this guide is structured:** We start with the problem Graphiti solves (Part 0), then drill into its architecture (Part 1), master its APIs (Part 2), explore advanced features (Part 3), apply everything to real-world use cases (Part 4), deploy to production (Part 5), and finally examine the architectural trade-offs that shaped Graphiti's design (Part 6-7). Each chapter builds on the previous one. Code examples are numbered and live in the `graphiti_examples/` directory.

**Prerequisites:**
```bash
pip install graphiti-core openai
# or with specific backends:
pip install graphiti-core[falkordb]
pip install graphiti-core[kuzu]
pip install graphiti-core[anthropic,google-genai,groq]

# You'll also need a graph database. Options:
# 1. Neo4j (primary/recommended) — Docker: docker run -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:5
# 2. Kuzu (embedded, zero dependency) — pip install graphiti-core[kuzu]
# 3. FalkorDB — Docker: docker run -p 6379:6379 falkordb/falkordb:latest
```

---

### Chapter 1 — What Problem Graphiti Solves

#### 1.1 The Stale Facts Problem

LLMs have no built-in mechanism for tracking when facts change. If you stuff context into a prompt, every retrieved fact looks equally current. Consider a customer support agent:

- Day 1: User reports "I can't log in." The agent stores this fact.
- Day 3: Agent retrieves context: "The user can't log in." Agent tries login troubleshooting again.
- Day 5: User says "The login issue was fixed." But the fact "user can't log in" is still in the vector store, retrieved with the same relevance score as the newer "issue was fixed" fact.

Vector RAG has no notion of **fact validity windows**. A fact retrieved with cosine similarity of 0.92 is presented to the LLM with the same authority whether it's 5 minutes old or 5 years old.

#### 1.2 The "When Was This True?" Problem

Vector similarity answers "what is similar to this query?" but cannot answer:

- "What was true in January that is no longer true?"
- "What did we believe about the customer before the investigation?"
- "How has this relationship changed over the past quarter?"
- "Show me the audit trail of this fact."

These are **temporal reasoning** questions. They require knowing not just what facts exist, but when each fact was valid and when it was superseded.

#### 1.3 The "What Changed?" Problem

In a dynamic world, facts don't just appear — they evolve. A CEO resigns. A product price changes. A bug is fixed. A preference is updated. Without explicit change tracking:

- Old facts linger in vector stores, polluting retrieval
- There's no audit trail of what changed and why
- Conflicting facts coexist without resolution
- Agents cannot reason about causality or sequence

#### 1.4 Graphiti's Elevator Pitch

Graphiti is a **temporal knowledge graph engine** that:

1. **Ingests** data as discrete **episodes** (conversations, events, structured facts) — each with provenance metadata
2. **Extracts** entities and relationships using LLMs, resolving duplicates and detecting contradictions
3. **Stores** facts as **bi-temporal edges** — every fact carries `valid_at`/`invalid_at` (event time) and `created_at`/`expired_at` (system time)
4. **Retrieves** using **hybrid search**: semantic embeddings + BM25 full-text + graph traversal, merged via Reciprocal Rank Fusion
5. **Evolves** the graph incrementally — new episodes integrate immediately without full recomputation. Contradicted facts are **expired, not deleted**, preserving history.

Instead of asking "which chunks are similar to this query?", Graphiti asks "which facts are true right now, how did they get here, and what do they connect to?"

---

### Chapter 2 — Graphiti vs RAG vs GraphRAG vs Cognee: Architectural Positioning

#### 2.1 The Spectrum of Memory Systems

AI memory systems exist on a spectrum from simple to sophisticated:

```
Simple Retrieval  ←——————————————————————————→  Structured Memory
     │                                                    │
  Vector RAG         GraphRAG        Graphiti          Cognee
  (semantic only)    (communities)   (temporal KG)     (poly-store KG)
```

**Vector RAG** (basic): Chunk → embed → retrieve. Flat, stateless, no relationships. ~60% accuracy on multi-hop. Best for: simple Q&A over static documentation.

**Microsoft GraphRAG**: Adds community detection on top of entities. Summarizes clusters of related entities, then retrieves summaries + raw chunks. Better at global summarization ("what are the main themes?") than targeted multi-hop queries. No session memory, no temporal reasoning.

**Graphiti (Zep)**: Episode-based temporal knowledge graph. Every fact carries `valid_at`/`valid_to` timestamps. Excellent for "what was true in January?" audit-trail queries. Hybrid retrieval (semantic + BM25 + graph traversal + rerank). Incremental processing — no batch recomputation. Scored 63.8% on LongMemEval (GPT-4o).

**Cognee**: Poly-store architecture (relational + vector + graph). 30+ data connectors, multimodal ingestion, session-aware memory, self-improving skills, multi-tenancy. ~90% accuracy on tuned HotPotQA. Best for: extracting structured knowledge from diverse corpora and serving it to agents.

#### 2.2 The Comparison Table

| Capability | Vector RAG | MS GraphRAG | Graphiti | Cognee |
|---|---|---|---|---|
| Retrieval method | Vector similarity | Community summaries + chunks | Semantic + BM25 + graph + rerank | Graph traversal + vectors + metadata |
| Temporal reasoning | No | Basic timestamps | Bi-temporal (event + system time) | Metadata only |
| Multi-hop reasoning | Fails | Partial (summaries) | Temporal multi-hop | Strong (hybrid) |
| Persistent memory | Per-query only | Per-index build | Episode-based, evolving | Evolving graph |
| Data source breadth | Any text | Text only | Conversation/episode focused | 30+ formats (PDFs, images, audio) |
| Incremental updates | Re-embed | Re-index | Real-time, per-episode | Incremental (memify) or full (cognify) |
| Accuracy ceiling | ~60% | ~70% | ~74% (untuned) / 63.8% LongMemEval | ~90% (tuned HotPotQA) |
| Graph DB required | No | No | Yes (Neo4j/FalkorDB/Kuzu) | Optional (Kuzu/Neo4j) |
| SDK Languages | Varies | Python | Python, TypeScript, Go | Python |

#### 2.3 Decision Flowchart: Should I Use Graphiti?

```
Do you need to track how facts change over time?
  NO → Basic RAG or vector store may suffice. Graphiti adds complexity you don't need.
  YES ↓

Do you need point-in-time queries ("what was true in Q1?")?
  NO → GraphRAG or Cognee may be sufficient.
  YES ↓

Are you working primarily with conversations/agent interactions (not documents)?
  NO → Consider Cognee for document-heavy ingestion (PDFs, images, databases).
  YES ↓

Do you need sub-second retrieval with no LLM call at query time?
  NO → GraphRAG with LLM-based summarization at query time is an option.
  YES ↓

Can you run and manage a graph database (Neo4j, FalkorDB, or Kuzu)?
  NO → Consider Zep Cloud (managed) or Mem0 (Docker-based, simpler ops).
  YES → Use Graphiti. This is its sweet spot.
```

---

## PART 1: CORE CONCEPTS & ARCHITECTURE

### Chapter 3 — The Three-Layer Knowledge Graph Architecture

Graphiti builds a knowledge graph with three distinct layers, each serving a different purpose in the memory system.

#### 3.1 Layer 1: Episodic Memory (`EpisodicNode`)

The foundational layer. Every piece of data ingested into Graphiti becomes an **EpisodicNode**. This is the provenance layer — it records exactly what was ingested, when, and from which source.

```
EpisodicNode properties:
├── name: str              — Human-readable episode identifier
├── content: str            — The raw episode content (messages, text, JSON)
├── source: EpisodeType     — message, text, json, or fact_triple
├── source_description: str — Where this data came from
├── valid_at: datetime      — When the content was created/received
├── group_id: str           — Namespace/tenant isolation
└── uuid: str               — Unique identifier
```

Episodes are linked to entities via `MENTIONS` edges: `(Episode)-[:MENTIONS]->(Entity)`. This creates a vital audit trail — every fact in the graph can be traced back to its source episode.

#### 3.2 Layer 2: Entity Knowledge (`EntityNode` + `EntityEdge`)

The semantic layer. Entities (people, organizations, concepts, products, preferences) are extracted from episodes by the LLM and stored as **EntityNodes**. Relationships between entities become **EntityEdges**.

```
EntityNode properties:
├── name: str               — Human-readable entity name
├── summary: str             — Aggregated description with relationship context
├── labels: list[str]        — Entity type labels (Person, Organization, etc.)
├── name_embedding: list     — Vector embedding for semantic search
├── group_id: str            — Namespace isolation
├── created_at: datetime     — System timestamp
└── attributes: dict         — Custom properties from Pydantic models

EntityEdge properties:
├── fact: str                — The relationship expressed in natural language
├── fact_embedding: list     — Vector embedding for semantic search
├── valid_at: datetime       — When the fact became true (event time)
├── invalid_at: datetime     — When the fact stopped being true (event time)
├── created_at: datetime     — When the fact was ingested (system time)
├── expired_at: datetime     — When the fact was superseded (system time)
├── uuid: str                — Unique identifier
└── group_id: str            — Namespace isolation
```

EntityEdges carry the **bi-temporal metadata** that makes Graphiti unique. The edge `(Alice)-[:RELATES_TO {fact: "is CEO of Acme Corp"}]->(Acme Corp)` carries timestamps telling you exactly when this was believed to be true and when it was ingested.

#### 3.3 Layer 3: Community Clusters (`CommunityNode`)

The organizational layer. After entity extraction and relationship building, Graphiti runs community detection (label propagation algorithm) to identify clusters of semantically related entities. Each cluster becomes a **CommunityNode** with an LLM-generated name and summary.

```
CommunityNode properties:
├── name: str               — Community name (e.g., "Product Development Team")
├── summary: str             — LLM-generated description of the community
├── group_id: str            — Namespace isolation
└── created_at: datetime     — System timestamp
```

Entities are linked to communities via `HAS_MEMBER` edges: `(Community)-[:HAS_MEMBER]->(Entity)`.

Communities improve retrieval for broad queries — instead of searching the entire graph, the system can focus on relevant communities. They also reveal emergent structure: entities that frequently co-occur in episodes naturally cluster together.

#### 3.4 How the Layers Interact

During a query, Graphiti can traverse all three layers:

```
Query: "Who worked on the Falcon project in Q2 2024?"
     │
     ▼
[Community layer] → Find the "Falcon Project" community
     │
     ▼
[Entity layer] → Find Person entities connected to "Project Falcon" via
                 RELATES_TO edges with valid_at in Q2 2024
     │
     ▼
[Episode layer] → Trace back to source episodes for provenance
```

This layered architecture means Graphiti can answer both specific factual queries ("what is Alice's role?") and broad exploratory queries ("what's happening in the Falcon project?") from the same graph structure.

#### 3.5 Example 1: Hello Graphiti

See `graphiti_examples/01_hello_graphiti.py`

```python
import asyncio
import os
from datetime import datetime, timezone
from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

async def main():
    # Connect to Neo4j
    neo4j_uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.environ.get("NEO4J_USER", "neo4j")
    neo4j_password = os.environ.get("NEO4J_PASSWORD", "password")

    graphiti = Graphiti(uri=neo4j_uri, user=neo4j_user, password=neo4j_password)
    await graphiti.build_indices_and_constraints()

    # Step 1: Add episodes about a fictional company
    await graphiti.add_episode(
        name="company_intro",
        episode_body="Acme Corp is a robotics company founded in 2020 by Alice Chen. "
                     "The company is headquartered in San Francisco and employs 250 people.",
        source=EpisodeType.text,
        source_description="Company profile",
        reference_time=datetime(2024, 1, 15, tzinfo=timezone.utc),
        group_id="acme"
    )

    await graphiti.add_episode(
        name="product_launch",
        episode_body="Acme Corp launched its flagship product, the Falcon-X delivery drone, "
                     "in March 2024. The Falcon-X can carry up to 5kg and has a range of 15km.",
        source=EpisodeType.text,
        source_description="Press release",
        reference_time=datetime(2024, 3, 10, tzinfo=timezone.utc),
        group_id="acme"
    )

    await graphiti.add_episode(
        name="team_structure",
        episode_body="The Falcon-X engineering team is led by Bob Martinez. "
                     "The team includes 12 engineers specializing in aerodynamics, "
                     "battery systems, and navigation software.",
        source=EpisodeType.text,
        source_description="Internal wiki",
        reference_time=datetime(2024, 4, 1, tzinfo=timezone.utc),
        group_id="acme"
    )

    # Step 2: Search for facts
    print("=== Search: Who founded Acme Corp? ===")
    edges = await graphiti.search(
        query="Who founded Acme Corp?",
        group_ids=["acme"],
        num_results=5
    )
    for edge in edges:
        print(f"  Fact: {edge.fact}")
        print(f"  Valid at: {edge.valid_at}")
        print(f"  UUID: {edge.uuid}")
        print()

    print("=== Search: What is the Falcon-X? ===")
    edges = await graphiti.search(
        query="What is the Falcon-X drone and what are its capabilities?",
        group_ids=["acme"],
        num_results=5
    )
    for edge in edges:
        print(f"  Fact: {edge.fact}")
        print()

    await graphiti.close()

if __name__ == "__main__":
    asyncio.run(main())
```

**What's happening under the hood:** Each episode is chunked and sent to the LLM for entity extraction. The LLM identifies entities like `Acme Corp`, `Alice Chen`, `Falcon-X`, `Bob Martinez` and relationships like `Alice Chen -[founded]-> Acme Corp`, `Falcon-X -[launched_by]-> Acme Corp`. These are stored as EntityNodes and EntityEdges in Neo4j. The edges carry `valid_at` timestamps from the episode's `reference_time`. When you search, Graphiti combines semantic similarity (embedding match), BM25 keyword match, and graph traversal to find the most relevant facts.

---

### Chapter 4 — The Bi-Temporal Data Model (Deep Dive)

The bi-temporal model is Graphiti's defining architectural feature. Every fact (EntityEdge) carries **four timestamps** spanning **two time dimensions**.

#### 4.1 Event Time: When Facts Were True in Reality

| Field | Purpose |
|---|---|
| `valid_at` | When the fact became true in the real world |
| `invalid_at` | When the fact stopped being true in the real world |

Event time answers: "What was the state of the world at time T?"

If Alice became CEO in January 2024 and stepped down in June 2024, the fact "Alice is CEO" would have `valid_at: 2024-01-15` and `invalid_at: 2024-06-01`. A point-in-time query for March 2024 would find this fact as active. A query for August 2024 would find it as expired.

#### 4.2 System Time: When Facts Were Recorded

| Field | Purpose |
|---|---|
| `created_at` | When the fact was ingested into the graph |
| `expired_at` | When the fact was superseded by a contradictory fact |

System time answers: "What did the system believe at time T?"

This distinction matters enormously. You might learn about an old fact today:

- **Event time**: Alice was CEO from Jan-June 2024
- **System time**: You ingested this information on August 15, 2024

This means you can query both "who was CEO in May 2024?" (event time) and "what did we know about the CEO when we made decision X on July 1, 2024?" (system time). The latter is critical for audit trails and debugging agent behavior.

#### 4.3 Why Two Time Dimensions Matter

Consider this scenario:

```
Timeline:
  Jan 2024 — Alice becomes CEO (event time)
  Mar 2024 — Agent ingests fact: "Alice is CEO" (system time: March)
  Jun 2024 — Alice resigns (event time)
  Jul 2024 — Agent ingests fact: "Bob is CEO" (system time: July)

Query: "Who was the CEO when we sent the investor email in April 2024?"
  → Graphiti checks valid_at/invalid_at, finds Alice was CEO in April.
  → Returns: Alice, with provenance to the March ingestion.

Query: "What did the system tell us about the CEO in May 2024?"
  → Graphiti checks created_at/expired_at, finds the fact was active in May.
  → Returns: Alice was believed to be CEO at that point.
```

#### 4.4 Fact Lifecycle: Birth → Active → Contradicted → Expired

Every fact goes through a lifecycle:

```
[Episode ingested] → [Entity extracted] → [Edge created with valid_at]
                                                 │
                                                 ▼
                                          [Fact is ACTIVE]
                                                 │
                                    New contradictory episode arrives
                                                 │
                                                 ▼
                              [Old edge: expired_at = now()]
                              [New edge: created_at = now(), valid_at = new time]
                                                 │
                                                 ▼
                              [Old edge persists — audit trail preserved]
```

**Facts are never deleted.** When a contradiction is detected (e.g., "Bob is now the CEO"), the old fact (`Alice -[is_CEO]-> Acme Corp`) gets its `expired_at` timestamp set. It remains in the graph for audit purposes but is excluded from "current state" queries.

#### 4.5 Point-in-Time Queries

Graphiti's search API can filter by temporal constraints:

```python
from graphiti_core.search.search_filters import SearchFilters

# Facts valid as of a specific date
filters = SearchFilters(
    valid_at=datetime(2024, 5, 1, tzinfo=timezone.utc)  # May 2024 state
)

# Facts that were active during a date range
filters = SearchFilters(
    valid_at_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
    valid_at_end=datetime(2024, 6, 30, tzinfo=timezone.utc)
)
```

#### 4.6 Example 2: Bi-Temporal Facts

See `graphiti_examples/02_bitemporal_facts.py` — this example adds facts about "Project Falcon" across multiple quarters, showing how facts change over time with different reference_time values, and how search results include valid_at/invalid_at timestamps.

---

### Chapter 5 — Episode-Based Ingestion

#### 5.1 Episodes as the Atomic Unit

In Graphiti, data enters as **episodes** — discrete, timestamped pieces of information. This is fundamentally different from the document-chunking approach used by traditional RAG:

| Approach | Unit | Provenance | Temporal |
|---|---|---|---|
| Traditional RAG | Document chunk | Lost after embedding | Not tracked |
| Graphiti | Episode | Preserved via MENTIONS edges | Bi-temporal on every fact |

An episode is a self-contained piece of information: a conversation turn, a JSON event, a fact triple, or a block of text. Each episode carries metadata about its source, when it occurred, and which namespace it belongs to.

#### 5.2 EpisodeType: The Four Ingest Formats

| EpisodeType | Use Case | Example |
|---|---|---|
| `message` | Conversation turns with speaker/role metadata | `{"speaker": "user", "content": "I can't log in"}` |
| `text` | Free-form narrative text | "Acme Corp launched Falcon-X in March 2024." |
| `json` | Structured data with fields | `{"company": "Acme Corp", "product": "Falcon-X", "price": 4999}` |
| `fact_triple` | Explicit subject-predicate-object triples | `("Alice Chen", "founded", "Acme Corp")` |

Each type is processed differently:
- **message**: The LLM extracts entities and relationships from conversation context, preserving speaker identity
- **text**: Standard entity/relationship extraction from narrative text
- **json**: Structured fields are directly mapped to entity properties; relationships inferred from object structure
- **fact_triple**: Minimal extraction needed — the triple is essentially pre-extracted; Graphiti handles deduplication and temporal annotation

#### 5.3 The Ingestion Pipeline

When you call `add_episode()`, a multi-step pipeline runs:

```
[1. Context Retrieval]
    Fetch the last EPISODE_WINDOW_LEN (default 3) episodes for temporal context.
    This helps the LLM understand what's already known and detect changes.
         │
         ▼
[2. Node Resolution]
    Extract entities from the episode content.
    For each extracted entity:
      a. Exact match: is there an existing entity with the same name?
      b. Fuzzy match: is there an entity with a similar name + embedding?
      c. LLM resolution: are these two entities the same real-world thing?
    If found → merge with existing entity (update summary, add labels).
    If not found → create new EntityNode.
         │
         ▼
[3. Edge Resolution]
    Extract relationships between entities.
    For each relationship:
      a. Is this fact already known? (same source, target, and fact text)
      b. Does this contradict an existing fact? (same source/target, different fact)
      c. Is this a new fact?
    If contradiction → expire the old edge, create new edge.
    If new → create new EntityEdge with temporal metadata.
         │
         ▼
[4. Community Update]
    Run label propagation to update community clusters.
    New entities may join existing communities or create new ones.
    Existing communities may split as new information arrives.
```

#### 5.4 Incremental Processing — No Full Rebuilds

Traditional GraphRAG requires periodic full re-indexing to incorporate new data. Graphiti is designed for **incremental updates**:

- Each new episode processes independently
- Only new/changed entities and relationships are affected
- The `EPISODE_WINDOW_LEN` context window ensures the LLM has enough temporal context to detect changes
- Community detection runs incrementally after each episode

This means you can add episodes in real-time as conversations happen, and the graph evolves continuously — no batch windows, no re-indexing delays.

#### 5.5 `EPISODE_WINDOW_LEN` and Temporal Context

The `EPISODE_WINDOW_LEN` parameter (default 3) controls how many previous episodes are retrieved as context for each new episode. This is critical for:

- **Contradiction detection**: "Bob is now the CEO" only contradicts "Alice is the CEO" if the LLM sees both facts
- **Entity co-reference**: "She" in the current episode refers to "Alice Chen" from the previous episode
- **Relationship continuity**: Understanding that a new fact builds on, modifies, or supersedes a previous one

Higher values provide more context but increase token costs (more episodes in the LLM prompt).

#### 5.6 Example 3: Episode Ingestion Patterns

See `graphiti_examples/03_episode_patterns.py` — this example demonstrates all four EpisodeTypes (message, text, json, fact_triple) and shows how each processes differently in the resulting graph structure.

---

### Chapter 6 — Entity & Relationship Extraction Pipeline

#### 6.1 Step-by-Step Walkthrough

The extraction pipeline is where the LLM does its heavy lifting. Here's what happens when you call `add_episode()`:

**Step 1: Episode Preprocessing**
The episode content is normalized based on its `EpisodeType`. Messages get formatted with speaker/role metadata. JSON is parsed and flattened for the LLM. Text passes through as-is.

**Step 2: Context Assembly**
The last `EPISODE_WINDOW_LEN` episodes (up to 3 by default) are retrieved and included in the LLM prompt. This gives the LLM the temporal context needed for co-reference resolution and contradiction detection.

**Step 3: Entity Extraction (LLM Call)**
The LLM receives:
- The episode content
- The temporal context (previous episodes)
- The entity type definitions (custom Pydantic models or defaults)
- Instructions to extract entities in structured JSON format

The LLM returns extracted entities with their properties, matching the defined schema.

**Step 4: Node Resolution**
For each extracted entity, Graphiti searches the existing graph:
1. **Exact name match** — fastest, most reliable
2. **Embedding similarity** — fuzzy matching for "J. Smith" vs "John Smith"
3. **LLM-based resolution** — for ambiguous cases where context is needed

If the entity exists, properties are merged (new information enriches existing entities). If not, a new `EntityNode` is created.

**Step 5: Relationship Extraction (LLM Call)**
The LLM receives the extracted entities (both new and existing) and identifies relationships between them. Each relationship becomes an `EntityEdge` with a natural-language `fact` field.

**Step 6: Edge Resolution**
For each extracted relationship:
- **Duplicate detection**: Is this exact fact already in the graph? Skip.
- **Contradiction detection**: Does this fact contradict an existing fact between the same entities? If so, expire the old edge, create the new one.
- **New fact**: Create a new edge with full temporal metadata.

**Step 7: Community Update**
Label propagation re-runs to incorporate new and updated entities into community clusters.

#### 6.2 Combined Extraction (v0.29.0+)

Starting in v0.29.0, Graphiti supports **combined extraction** — entity extraction and relationship extraction in a single LLM call. This reduces LLM costs by roughly 50% for the extraction step:

```python
await graphiti.add_episode(
    name="ep_1",
    episode_body="Alice Chen founded Acme Corp in 2020.",
    source=EpisodeType.text,
    reference_time=datetime.now(timezone.utc),
    group_id="acme",
    # combined_extraction=True  # opt-in, single LLM call for nodes + edges
)
```

The trade-off: combined extraction can be slightly less accurate for complex episodes with many entities and nuanced relationships. For simple episodes, the cost savings are worth it.

#### 6.3 Multi-Episode Batching

For bulk ingestion, Graphiti can process multiple episodes in a single LLM call:

```python
episodes = [
    {"name": "ep_1", "episode_body": "Alice founded Acme Corp.", ...},
    {"name": "ep_2", "episode_body": "Bob joined as CTO.", ...},
    {"name": "ep_3", "episode_body": "Acme Corp raised $10M Series A.", ...},
]
await graphiti.add_episode_bulk(episodes, group_id="acme")
```

Batching reduces per-episode LLM costs by sharing prompt overhead across multiple episodes. The trade-off is that each episode within the batch gets less individual LLM attention.

#### 6.4 Confidence Scores and Deduplication

Each extracted relationship carries an implicit confidence based on:
- How clearly the fact was stated in the episode text
- Whether the fact was corroborated by multiple episodes
- Whether the fact contradicted existing knowledge

When the same fact is extracted from multiple episodes, its confidence increases (the edge summary may be enriched, and the fact persists even if one source episode is later removed).

#### 6.5 Example 4: Extraction Pipeline

See `graphiti_examples/04_extraction_pipeline.py` — demonstrates the extraction pipeline in detail, showing how to use `retrieve_episodes()` to inspect processed episodes and their extracted entities and edges.

---

### Chapter 7 — Hybrid Search Architecture

#### 7.1 Three Retrieval Strategies

Graphiti's search combines three complementary retrieval methods:

| Method | What It Finds | Strengths | Weaknesses |
|---|---|---|---|
| **Semantic (embeddings)** | Content similar in meaning to the query | Handles paraphrases, synonyms, conceptual similarity | Misses exact keyword matches, struggles with rare terms |
| **BM25 (full-text)** | Content containing the exact words in the query | Excellent for names, IDs, technical terms | Misses paraphrases, no semantic understanding |
| **Graph traversal** | Entities connected via relationships | Multi-hop reasoning, relationship context | Needs a starting point, can be noisy without pruning |

#### 7.2 Reciprocal Rank Fusion (RRF)

The results from all three methods are merged using **Reciprocal Rank Fusion**:

```
RRF_score(d) = Σ 1 / (k + rank_i(d))
```

Where `k` is a constant (typically 60) and `rank_i(d)` is the rank of document `d` in method `i`.

RRF has a powerful property: results that rank highly in **multiple** retrieval methods get a significant boost. An edge that appears in the top 3 for semantic AND in the top 3 for BM25 will rank higher than an edge that's #1 in one method but absent from the other. This naturally favors results that are both semantically relevant AND keyword-precise.

#### 7.3 Graph-Proximity Reranking

When you provide a `center_node_uuid`, Graphiti adds a fourth dimension: **graph distance** from the center node. Facts about entities that are directly connected (1 hop) rank higher than facts about entities 3+ hops away.

```python
# Search for facts, preferring those connected to a specific entity
edges = await graphiti.search_(
    query="What is the team structure?",
    config=SearchConfig(
        recipe=SearchRecipes.EDGE_HYBRID_SEARCH_NODE_DISTANCE
    ),
    group_ids=["acme"],
    center_node_uuid="<uuid-of-acme-corp-node>",
    num_results=10
)
```

This is particularly powerful for multi-hop reasoning: start from a known entity, find connected entities, then explore their connections.

#### 7.4 Cross-Encoder Reranking

For maximum accuracy, Graphiti can use a cross-encoder to rerank results:

```python
search_config = SearchConfig(
    recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER
)
```

A cross-encoder (like OpenAI's reranker) takes the query and each candidate document as a pair, producing a relevance score based on deep semantic interaction. This is more accurate than embedding similarity alone, but adds latency and cost.

#### 7.5 Built-in Search Recipes

Graphiti ships with pre-configured search recipes:

| Recipe | Methods | Reranking | Best For |
|---|---|---|---|
| `EDGE_HYBRID_SEARCH_RRF` | Semantic + BM25 | RRF fusion | Default — good balance of speed and accuracy |
| `EDGE_HYBRID_SEARCH_NODE_DISTANCE` | Semantic + BM25 | RRF + graph distance | Queries where you have a known starting entity |
| `COMBINED_HYBRID_SEARCH_CROSS_ENCODER` | Semantic + BM25 + Graph | Cross-encoder | Maximum accuracy, higher latency |

#### 7.6 SearchConfig and SearchFilters

```python
from graphiti_core.search.search_config import SearchConfig, SearchRecipes
from graphiti_core.search.search_filters import SearchFilters

config = SearchConfig(
    recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
    num_results=20,
    max_depth=3,           # Max graph traversal depth
)

filters = SearchFilters(
    group_ids=["acme"],    # Scope to namespace
    valid_at=datetime(2024, 6, 1, tzinfo=timezone.utc),  # Point-in-time
    edge_labels=["RELATES_TO"],  # Filter by edge type
    node_labels=["Person"],      # Filter by entity type
)

results = await graphiti.search_(
    query="Who worked on Falcon-X?",
    config=config,
    filters=filters
)
```

#### 7.7 Example 5: Search Strategies

See `graphiti_examples/05_search_strategies.py` — demonstrates all search approaches with comparisons of results from different strategies.

---

## PART 2: API DEEP DIVE

### Chapter 8 — The Graphiti Class: Construction & Configuration

#### 8.1 Constructor Parameters

```python
from graphiti_core import Graphiti
from openai import AsyncOpenAI

graphiti = Graphiti(
    # Graph database connection
    uri="bolt://localhost:7687",        # Neo4j / FalkorDB URI
    user="neo4j",                       # Database username
    password="password",                # Database password

    # LLM configuration
    llm_client=AsyncOpenAI(             # Default: OpenAI
        api_key="sk-...",
        # model="gpt-4o"                # Model selection
    ),

    # Embedder configuration
    embedder=AsyncOpenAI(               # Can be different from llm_client
        api_key="sk-..."
    ),

    # Optional: Cross-encoder for reranking
    cross_encoder=None,                 # AsyncOpenAI reranker or None

    # Optional: Graph driver override
    graph_driver=None,                  # Custom driver for non-Neo4j backends

    # Storage configuration
    store_raw_episode_content=True,     # Keep raw episode text in the graph

    # Concurrency
    max_coroutines=10,                  # Max concurrent LLM calls

    # Text normalization
    ensure_ascii=False,                 # Convert Unicode to ASCII
)
```

#### 8.2 LLM Client Configuration

Graphiti is LLM-agnostic. Any async client that implements the expected interface works:

```python
# OpenAI
from openai import AsyncOpenAI
llm_client = AsyncOpenAI(api_key="sk-...", model="gpt-4o")

# Anthropic
from anthropic import AsyncAnthropic
llm_client = AsyncAnthropic(api_key="sk-ant-...")

# Azure OpenAI
from openai import AsyncAzureOpenAI
llm_client = AsyncAzureOpenAI(
    api_key="...",
    api_version="2024-02-15-preview",
    azure_endpoint="https://your-resource.openai.azure.com"
)

# Ollama (local)
from openai import AsyncOpenAI
llm_client = AsyncOpenAI(
    api_key="ollama",
    base_url="http://localhost:11434/v1"
)

# Google Gemini
# Using the gemini plugin: pip install graphiti-core[google-genai]
```

#### 8.3 Embedder Configuration

The embedder generates vector embeddings for entities and facts:

```python
# Default: same as LLM client (OpenAI text-embedding-3-small)
graphiti = Graphiti(uri=uri, user=user, password=password)

# Different embedder
embedder = AsyncOpenAI(api_key="sk-...")
graphiti = Graphiti(
    uri=uri, user=user, password=password,
    llm_client=llm_client,
    embedder=embedder
)
```

#### 8.4 `max_coroutines` and Concurrency Control

`max_coroutines` (default 10) limits the number of concurrent LLM calls during extraction. This is the primary knob for tuning throughput vs rate limits:

- **Higher values** (16-32): Faster bulk ingestion, but may hit OpenAI rate limits (500 RPM for GPT-4o on Tier 1)
- **Lower values** (2-5): Slower but safer, works within free-tier limits
- **Production**: Set based on your API tier; monitor for 429 errors

#### 8.5 `store_raw_episode_content`

When `True` (default), the full raw episode content is stored in the `EpisodicNode`. This enables:
- Full episode retrieval for context assembly
- Audit trail completeness
- Re-processing episodes with updated extraction logic

When `False`, save storage but lose the ability to retrieve original episode content.

#### 8.6 Lifecycle: Create → Use → Close

```python
graphiti = Graphiti(uri=uri, user=user, password=password)

# One-time setup: create indices and constraints
await graphiti.build_indices_and_constraints()

# Use the graph...
await graphiti.add_episode(...)
results = await graphiti.search(...)

# Always close when done
await graphiti.close()
```

`build_indices_and_constraints()` creates Neo4j indexes for efficient lookups. It should be called once when setting up a new database. It's idempotent — safe to call multiple times.

#### 8.7 Example 6: Graphiti Configuration

See `graphiti_examples/06_configuration.py` — demonstrates all major constructor options and their effects on behavior.

---

### Chapter 9 — Episode API (`add_episode` / `add_episode_bulk`)

#### 9.1 `add_episode()` — Complete Signature

```python
async def add_episode(
    name: str,                          # Unique episode identifier
    episode_body: str,                  # The content to ingest
    source: EpisodeType,                # message, text, json, or fact_triple
    source_description: str = "",       # Human-readable source description
    reference_time: datetime = None,    # When the content was created/received
    group_id: str = None,               # Namespace/tenant identifier
    uuid: str = None,                   # Optional: pre-assigned UUID
    entity_types: dict = None,          # Custom entity type definitions
    combined_extraction: bool = False,  # Single LLM call for nodes + edges
) -> AddEpisodeResults:
```

**Parameters explained:**

- **`name`**: Must be unique within a `group_id`. Used for episode retrieval and deduplication.
- **`episode_body`**: The raw content. For `message` type, include speaker metadata. For `json` type, pass a JSON string.
- **`source`**: Determines how the content is preprocessed before LLM extraction.
- **`source_description`**: Metadata for provenance. "Slack message #general", "Customer email", etc.
- **`reference_time`**: The event time for the episode. All extracted facts inherit this as their `valid_at` unless the LLM identifies a more specific time. If `None`, defaults to `datetime.now(timezone.utc)`.
- **`group_id`**: Critical for multi-tenancy. Episodes in different groups are invisible to each other. Same `group_id` = shared memory.
- **`entity_types`**: Dict mapping entity type names to Pydantic subclasses of `EntityNode`. `{"Person": Person, "Organization": Organization}`.
- **`combined_extraction`**: When `True`, nodes and edges extracted in one LLM call. Saves ~50% LLM cost, may reduce accuracy for complex episodes.

**Return value:** `AddEpisodeResults` contains the extracted entities, edges, and the episode node itself.

#### 9.2 `add_episode_bulk()` — Batch Processing

```python
episodes = [
    {
        "name": "ep_1",
        "episode_body": "Alice founded Acme Corp in 2020.",
        "source": EpisodeType.text,
        "reference_time": datetime(2020, 3, 15, tzinfo=timezone.utc),
    },
    {
        "name": "ep_2",
        "episode_body": "Acme Corp raised $5M seed round in 2021.",
        "source": EpisodeType.text,
        "reference_time": datetime(2021, 6, 1, tzinfo=timezone.utc),
    },
]

await graphiti.add_episode_bulk(
    episodes,
    group_id="acme",
    entity_types=None,
    combined_extraction=False,
)
```

Bulk processing is more efficient than calling `add_episode` in a loop because the LLM can process multiple episodes in a single prompt, sharing context overhead.

#### 9.3 `group_id` for Namespace Isolation

The `group_id` parameter is Graphiti's multi-tenancy mechanism:

```python
# User A's data
await graphiti.add_episode(
    name="a_1", episode_body="Alice likes Python.",
    source=EpisodeType.text, reference_time=datetime.now(timezone.utc),
    group_id="user_a"
)

# User B's data — completely isolated
await graphiti.add_episode(
    name="b_1", episode_body="Bob likes Rust.",
    source=EpisodeType.text, reference_time=datetime.now(timezone.utc),
    group_id="user_b"
)

# Search scoped to User A
results = await graphiti.search(
    query="What programming language does the user like?",
    group_ids=["user_a"]  # Only sees User A's data
)
```

You can also search across multiple groups:
```python
results = await graphiti.search(
    query="...",
    group_ids=["user_a", "shared_knowledge"]
)
```

#### 9.4 Queue System: Per-Group Sequential Processing

Each `group_id` gets its own processing queue. Episodes for the same group are processed **sequentially** (preserving chronological order), while different groups process **concurrently**. This prevents race conditions: if two episodes for the same user arrive simultaneously, they're processed in order, ensuring the second one can correctly detect contradictions from the first.

#### 9.5 Example 7: Episode API Workflow

See `graphiti_examples/07_episode_api.py` — comprehensive demonstration of single episode, bulk processing, group_id isolation, reference_time anchoring, episode retrieval, and removal.

---

### Chapter 10 — Search API (`search` / `search_`)

#### 10.1 `search()` — Basic Hybrid Search

```python
async def search(
    query: str,                         # Natural language query
    group_ids: list[str] = None,        # Scope to specific groups
    num_results: int = 10,              # Maximum results to return
    center_node_uuid: str = None,       # Graph-proximity ranking anchor
    filters: SearchFilters = None,      # Temporal/label/type filters
) -> list[EntityEdge]:
```

The basic `search()` method returns `EntityEdge` objects — facts with their temporal metadata, source entities, and target entities. It uses the default RRF hybrid search recipe.

#### 10.2 `search_()` — Advanced Search with Configuration

```python
async def search_(
    query: str,
    config: SearchConfig,               # Recipe, depth, pagination
    group_ids: list[str] = None,
    center_node_uuid: str = None,
    filters: SearchFilters = None,
) -> SearchResults:                     # Richer result type
```

`search_()` returns a `SearchResults` object containing:
- `edges`: list of matching `EntityEdge` objects
- `nodes`: list of matching `EntityNode` objects
- `episodes`: relevant `EpisodicNode` objects
- `communities`: relevant `CommunityNode` objects

#### 10.3 SearchConfig

```python
from graphiti_core.search.search_config import SearchConfig, SearchRecipes

config = SearchConfig(
    recipe=SearchRecipes.EDGE_HYBRID_SEARCH_RRF,
    num_results=20,
    max_depth=3,            # Graph traversal depth (hops from center node)
    reranker=None,          # Optional cross-encoder for reranking
    min_score=0.5,          # Minimum relevance score threshold
)
```

#### 10.4 SearchFilters

```python
from graphiti_core.search.search_filters import SearchFilters

filters = SearchFilters(
    # Temporal constraints
    valid_at=datetime(2024, 6, 1, tzinfo=timezone.utc),        # Point-in-time
    valid_at_start=datetime(2024, 1, 1, tzinfo=timezone.utc),  # Range start
    valid_at_end=datetime(2024, 12, 31, tzinfo=timezone.utc),  # Range end
    created_at_start=datetime(2024, 6, 1, tzinfo=timezone.utc),# System time

    # Label constraints
    edge_labels=["RELATES_TO", "DEPENDS_ON"],
    node_labels=["Person", "Organization"],

    # Group scoping
    group_ids=["user_a", "shared"],
)
```

#### 10.5 Example 8: Search API Deep Dive

See `graphiti_examples/08_search_api.py` — demonstrates `search()` vs `search_()`, SearchConfig with all parameters, SearchFilters for temporal and label filtering, center_node_uuid proximity ranking, and result interpretation.

---

### Chapter 11 — Custom Entities with Pydantic

#### 11.1 Why Custom Entities?

By default, Graphiti extracts generic entities with a `name` and `summary`. For domain-specific applications, you need entities with typed properties:

- A **Person** entity with `role`, `email`, `department`
- A **Product** entity with `sku`, `price`, `category`
- A **Requirement** entity with `project_name`, `priority`, `status`

Custom entities tell the LLM exactly what to extract and in what schema.

#### 11.2 Defining Custom Entity Types

```python
from pydantic import BaseModel, Field
from graphiti_core.nodes import EntityNode
from typing import Optional
from datetime import datetime

class Person(EntityNode):
    """A person entity with role and organization."""
    name: str
    role: str = Field(default="unknown", description="Job title or role")
    organization: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)

class Organization(EntityNode):
    """An organization entity."""
    name: str
    industry: Optional[str] = Field(default=None)
    headquarters: Optional[str] = Field(default=None)
    founded: Optional[int] = Field(default=None)

class Product(EntityNode):
    """A product entity."""
    name: str
    category: Optional[str] = Field(default=None)
    price: Optional[float] = Field(default=None)
    version: Optional[str] = Field(default=None)
```

The Pydantic field descriptions serve as extraction hints to the LLM. A field like `role: str = Field(default="unknown", description="Job title or role")` tells the LLM to look for job titles.

#### 11.3 Using Custom Entities in Episodes

```python
entity_types = {
    "Person": Person,
    "Organization": Organization,
    "Product": Product,
}

await graphiti.add_episode(
    name="company_data",
    episode_body="Alice Chen, CTO of Acme Corp, announced the Falcon-X drone. "
                 "The Falcon-X is priced at $4,999 and targets the logistics industry.",
    source=EpisodeType.text,
    reference_time=datetime.now(timezone.utc),
    group_id="acme",
    entity_types=entity_types,
)
```

The LLM now extracts `Alice Chen` as a `Person` with `role: "CTO"` and `organization: "Acme Corp"`, `Acme Corp` as an `Organization` with `industry: "robotics"`, and `Falcon-X` as a `Product` with `price: 4999`.

#### 11.4 Custom Edge Types

You can also define typed edges for domain-specific relationships:

```python
from graphiti_core.nodes import EntityEdge

class EmploymentEdge(EntityEdge):
    """Employment relationship between Person and Organization."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    title: Optional[str] = None

class DependencyEdge(EntityEdge):
    """Dependency relationship between entities."""
    dependency_type: str = "requires"  # requires, optional, conflicts
    version_constraint: Optional[str] = None
```

#### 11.5 Built-in Custom Types: Preference, Procedure, Requirement

Graphiti ships with three agent-focused entity types that are commonly used in AI assistant applications:

| Type | Fields | Use Case |
|---|---|---|
| **Preference** | `category`, `description` | "I prefer dark mode", "I like short emails" |
| **Procedure** | `description` | Multi-step workflows, instructions, how-tos |
| **Requirement** | `project_name`, `description` | Needs, specifications, constraints |

These are available in the MCP server with the `--use-custom-entities` flag.

#### 11.6 Example 9: Custom Entities

See `graphiti_examples/09_custom_entities.py` — defines Person, Organization, Product, Event, and Location entities with typed properties, and demonstrates typed extraction.

---

### Chapter 12 — Community Detection & Graph Analysis

#### 12.1 What Community Detection Does

After episodes are processed and entities extracted, Graphiti runs a **label propagation algorithm** over the entity graph to identify clusters of semantically related entities.

```
Before community detection:
  Alice──works_at──Acme Corp──produces──Falcon-X
  Bob────works_at──Acme Corp──designs───Falcon-X
  Charlie─works_at──Acme Corp──markets──Falcon-X
  Diana──works_at──Beta Inc──produces──Omega-S

After community detection:
  Community "Acme Corp & Falcon-X Team"
    ├── Alice
    ├── Bob
    ├── Charlie
    ├── Acme Corp
    └── Falcon-X

  Community "Beta Inc & Omega-S Team"
    ├── Diana
    ├── Beta Inc
    └── Omega-S
```

#### 12.2 Running Community Detection

```python
# Automatically triggered after each add_episode
await graphiti.add_episode(...)

# Or run manually
await graphiti.build_communities()
```

Community detection is **automatically triggered** after each `add_episode()` call in the MCP server. In the core library, you call `build_communities()` explicitly after adding episodes.

#### 12.3 Label Propagation Algorithm

The algorithm works by:
1. Each entity node starts with its own label
2. Each node adopts the label most common among its neighbors
3. Repeat until convergence (labels stop changing, or max iterations reached)
4. Nodes with the same label form a community

This is efficient (near-linear in the number of edges) and naturally produces communities that reflect the graph's structure.

#### 12.4 LLM-Based Community Summarization

After communities are identified, the LLM generates a name and summary for each community. This makes communities human-readable and useful for broad queries:

```
Community: "Acme Corp Engineering Team"
Summary: "A group of entities related to the engineering department at Acme Corp,
          including team members Alice, Bob, and Charlie, their roles, the Falcon-X
          project, and technical decisions made during the Q1-Q3 2024 development cycle."
```

#### 12.5 Using Communities in Search

Communities improve retrieval for broad queries:

- "What's happening at Acme Corp?" → retrieves relevant communities whose summaries match
- "Tell me about the Falcon-X team" → finds the community, then retrieves all member entities
- Without communities: would need keyword matching on individual entities, losing the group context

#### 12.6 Example 10: Community Detection

See `graphiti_examples/10_communities.py` — adds episodes across related topics, runs community detection, and demonstrates community-aware search.

---

### Chapter 13 — MCP Server

#### 13.1 What the MCP Server Exposes

Graphiti ships with a Model Context Protocol (MCP) server that exposes the knowledge graph as tools for AI assistants (Claude Desktop, Cursor, Cline, etc.).

**Available MCP tools:**

| Tool | Purpose |
|---|---|
| `add_episode` | Add content (text, JSON, messages) to the knowledge graph |
| `search_nodes` | Hybrid semantic search for entity nodes |
| `search_facts` | Search for relationships (edges/facts) between entities |
| `get_episodes` | Retrieve recent episodes for a group |
| `get_entity_edge` | Retrieve a specific relationship by UUID |
| `delete_entity_edge` | Remove a specific fact/edge |
| `delete_episode` | Remove an episode and its associated graph elements |
| `clear_graph` | Destructive reset of all graph data (use with caution) |
| `get_status` | Health check and graph statistics |

#### 13.2 Setup with Claude Desktop

**Step 1: Install**
```bash
pip install graphiti-core
```

**Step 2: Configure Claude Desktop**

Add to `claude_desktop_config.json` (or `~/.claude/claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "graphiti": {
      "command": "python",
      "args": ["-m", "graphiti_core.mcp_server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

**Step 3: Use in Claude**

Once connected, you can ask Claude to:
- "Remember that I prefer dark mode and short responses"
- "What do you know about my preferences?"
- "Search my knowledge graph for information about Project Falcon"

Claude will use the MCP tools to add episodes and search the graph.

#### 13.3 Environment Configuration

```bash
# Required
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=sk-...

# Optional
LLM_MODEL=gpt-4o                          # Default model
EMBEDDING_MODEL=text-embedding-3-small    # Default embedder
USE_CUSTOM_ENTITIES=true                  # Enable Preference/Procedure/Requirement types
MAX_COROUTINES=10                         # Concurrency control
```

#### 13.4 Transport Options

| Transport | Description | Best For |
|---|---|---|
| **stdio** | Standard input/output (default) | Local development, Claude Desktop |
| **SSE** | Server-Sent Events over HTTP | Web-based clients, remote access |
| **Streamable HTTP** | Stateless HTTP (newer MCP spec) | Serverless deployments |

#### 13.5 Example 11: MCP Server Setup

See `graphiti_examples/11_mcp_server/README.md` — complete setup guide with Claude Desktop configuration, tool reference, and troubleshooting.

---

### Chapter 14 — REST API Server

#### 14.1 Starting the REST Server

Graphiti includes a FastAPI-based REST API server:

```bash
# Start the REST API server
python -m graphiti_core.rest_server

# Or programmatically:
from graphiti_core.rest.server import create_app
app = create_app()
```

#### 14.2 Endpoint Reference

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/ingest/messages` | Add episodes to the knowledge graph |
| POST | `/ingest/entity-node` | Create entity nodes directly |
| DELETE | `/ingest/group/{group_id}` | Delete all data for a group |
| POST | `/retrieve/search` | Search the knowledge graph |
| POST | `/retrieve/get-memory` | Specialized memory retrieval for agents |
| GET | `/retrieve/episodes/{group_id}` | Get recent episodes for a group |

**Example: Ingest via REST**
```bash
curl -X POST http://localhost:8000/ingest/messages \
  -H "Content-Type: application/json" \
  -d '{
    "name": "user_message_1",
    "episode_body": "I prefer dark mode in all my applications.",
    "source": "message",
    "group_id": "user_123",
    "reference_time": "2024-06-15T10:30:00Z"
  }'
```

**Example: Search via REST**
```bash
curl -X POST http://localhost:8000/retrieve/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are my preferences?",
    "group_ids": ["user_123"],
    "num_results": 10
  }'
```

#### 14.3 Example 12: REST API Client

See `graphiti_examples/12_rest_api.py` — Python client examples for all REST endpoints using httpx.

---

## PART 3: ADVANCED FEATURES

### Chapter 15 — Temporal Reasoning & Point-in-Time Queries

#### 15.1 The Power of Temporal Queries

Temporal reasoning is Graphiti's defining capability. Unlike static knowledge graphs where facts are either present or absent, Graphiti enables questions like:

- "Who was the CEO in Q2 2024?"
- "What was the product roadmap as of the board meeting in March?"
- "How has the team structure changed over the past year?"
- "What did we believe about this customer before the investigation?"

Each of these requires understanding not just what facts exist, but **when each fact was valid**.

#### 15.2 Querying at a Specific Point in Time

```python
from datetime import datetime, timezone
from graphiti_core.search.search_filters import SearchFilters

# What was true on June 1, 2024?
filters = SearchFilters(
    valid_at=datetime(2024, 6, 1, tzinfo=timezone.utc)
)

edges = await graphiti.search_(
    query="Who is the CEO?",
    config=SearchConfig(),
    group_ids=["acme"],
    filters=filters
)
```

Graphiti checks each fact's `valid_at`/`invalid_at` window. Facts where `valid_at <= query_time < invalid_at` are returned. Facts that expired before the query time are excluded.

#### 15.3 Querying a Date Range

```python
# Facts active at any point during Q2 2024
filters = SearchFilters(
    valid_at_start=datetime(2024, 4, 1, tzinfo=timezone.utc),
    valid_at_end=datetime(2024, 6, 30, tzinfo=timezone.utc)
)
```

This returns all facts that overlapped with Q2 2024 — including facts that started before Q2 and ended during it, facts that started and ended within Q2, and facts that started during Q2 and continued beyond.

#### 15.4 Tracking Fact Evolution

```python
# Add facts at different points in time
await graphiti.add_episode(
    name="q1_status",
    episode_body="Project Falcon is in the planning phase with a $500K budget.",
    source=EpisodeType.text,
    reference_time=datetime(2024, 1, 15, tzinfo=timezone.utc),
    group_id="acme"
)

await graphiti.add_episode(
    name="q2_status",
    episode_body="Project Falcon is in active development with a $1.2M budget.",
    source=EpisodeType.text,
    reference_time=datetime(2024, 4, 15, tzinfo=timezone.utc),
    group_id="acme"
)

await graphiti.add_episode(
    name="q3_status",
    episode_body="Project Falcon is in beta testing with a $2.5M budget. "
                 "It has been renamed to FalconTrack.",
    source=EpisodeType.text,
    reference_time=datetime(2024, 7, 15, tzinfo=timezone.utc),
    group_id="acme"
)

# Now compare states
q1_edges = await graphiti.search_(
    query="What is the status of Project Falcon?",
    filters=SearchFilters(valid_at=datetime(2024, 2, 1, tzinfo=timezone.utc)),
    config=SearchConfig(), group_ids=["acme"]
)

q2_edges = await graphiti.search_(
    query="What is the status of Project Falcon?",
    filters=SearchFilters(valid_at=datetime(2024, 5, 1, tzinfo=timezone.utc)),
    config=SearchConfig(), group_ids=["acme"]
)

# Q1: planning, $500K | Q2: development, $1.2M | Q3: beta, $2.5M, renamed
```

#### 15.5 Temporal Constraints Reference

```python
SearchFilters(
    # Point-in-time: facts valid at this exact moment
    valid_at=datetime(2024, 6, 1, tzinfo=timezone.utc),

    # Range: facts valid at any point in this window
    valid_at_start=datetime(2024, 1, 1, tzinfo=timezone.utc),
    valid_at_end=datetime(2024, 12, 31, tzinfo=timezone.utc),

    # System time: facts ingested after this date
    created_at_start=datetime(2024, 6, 1, tzinfo=timezone.utc),

    # Combine event time and system time
    # "What active facts did we know about on July 1?"
    valid_at=datetime(2024, 7, 1, tzinfo=timezone.utc),
    created_at_start=None,  # All ingestion times
)
```

#### 15.6 Example 13: Temporal Queries

See `graphiti_examples/13_temporal_queries.py` — follows a company from 2020-2025 across temporally-anchored episodes, demonstrating point-in-time queries and fact evolution tracking.

---

### Chapter 16 — Contradiction Handling & Fact Expiration

#### 16.1 How Contradictions Are Detected

When a new episode is processed, the LLM extracts relationships. During **edge resolution**, Graphiti checks each extracted relationship against existing edges:

1. **Same subject, same predicate, same object** → duplicate. Skip.
2. **Same subject, same predicate, different object** → potential contradiction.
3. **Same subject and object, different fact text** → the LLM evaluates whether this is a refinement or a contradiction.

For case 2 and 3, Graphiti marks the existing edge as expired (`expired_at = now()`) and creates a new edge with the updated fact.

#### 16.2 The Contradiction Process in Detail

```
Initial state:
  (Alice) -[RELATES_TO {fact: "Alice is CEO of Acme Corp",
                         valid_at: 2024-01-15, invalid_at: None,
                         created_at: 2024-01-15, expired_at: None}]-> (Acme Corp)

New episode ingested: "Bob Martinez is the new CEO of Acme Corp, effective June 2024."
  Reference time: 2024-07-01

After processing:
  Old edge (Alice → CEO):
    invalid_at: 2024-06-01    ← Set — Alice stopped being CEO
    expired_at: 2024-07-01    ← Set — System now knows this fact is outdated

  New edge (Bob → CEO):
    valid_at: 2024-06-01      ← When Bob became CEO
    invalid_at: None          ← Still true (no end date known)
    created_at: 2024-07-01    ← When system learned this
    expired_at: None          ← Still the current fact
```

#### 16.3 Expired ≠ Deleted

This is the critical design principle: **expired edges remain in the graph**. They are simply excluded from "current state" queries (by default). This preserves:

- **Audit trail**: "Show me every CEO Acme Corp has had, in order"
- **Historical queries**: "Who was CEO in March 2024?"
- **Debugging**: "What did the system tell the user in April?"

#### 16.4 Retrieving Expired Edges

By default, `search()` and `search_()` return only active edges. To retrieve historical facts:

```python
# Include expired edges in results
filters = SearchFilters(
    valid_at_start=datetime(2020, 1, 1, tzinfo=timezone.utc),
    valid_at_end=datetime(2024, 12, 31, tzinfo=timezone.utc),
    # No valid_at point-in-time constraint = get all edges in range
)
```

#### 16.5 Manual Fact Invalidation

You can manually invalidate a specific edge:

```python
# Get the edge UUID
edge_uuid = "some-uuid-here"

# Mark it as expired
await graphiti.delete_entity_edge(edge_uuid)
# Or use the MCP tool: delete_entity_edge
```

This is useful when you know a fact is wrong (not just outdated) and want to remove it without adding a replacement.

#### 16.6 Confidence in Contradiction Resolution

Graphiti doesn't blindly accept every new fact. If the LLM detects a contradiction but the new fact has low confidence (vaguely stated, ambiguous language), it may:
- Add the new fact as a separate, competing edge
- Not expire the old edge
- Flag both for later resolution

This prevents low-quality information from prematurely expiring well-established facts.

#### 16.7 Example 14: Contradiction Handling

See `graphiti_examples/14_contradictions.py` — demonstrates fact seeding, contradiction detection, expiration vs deletion, and audit trail retrieval.

---

### Chapter 17 — Multi-Provider Plugin Architecture

#### 17.1 The Plugin Model

Graphiti's architecture is modular. Every component that makes external calls (LLM, embeddings, reranking, graph storage) is swappable via a plugin interface:

```
┌──────────────────────────────────────────┐
│              Graphiti Core                │
│                                           │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ LLM      │  │ Embedder │  │ Cross-  │ │
│  │ Client   │  │          │  │ Encoder │ │
│  └────┬─────┘  └────┬─────┘  └────┬────┘ │
│       │              │              │      │
│  ┌────┴──────────────┴──────────────┴────┐ │
│  │         Graph Driver                  │ │
│  │   (Neo4j / FalkorDB / Kuzu / Neptune) │ │
│  └───────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

You can swap any component at construction time without changing your application code.

#### 17.2 LLM Providers

```python
# OpenAI (default)
from openai import AsyncOpenAI
llm = AsyncOpenAI(api_key="sk-...")
graphiti = Graphiti(uri=uri, user=user, password=password, llm_client=llm)

# Anthropic Claude
from anthropic import AsyncAnthropic
llm = AsyncAnthropic(api_key="sk-ant-...")
graphiti = Graphiti(uri=uri, user=user, password=password, llm_client=llm)

# Google Gemini
# pip install graphiti-core[google-genai]
from google import genai
llm = genai.Client(api_key="...")
graphiti = Graphiti(uri=uri, user=user, password=password, llm_client=llm)

# Groq (fast inference)
# pip install graphiti-core[groq]
from groq import AsyncGroq
llm = AsyncGroq(api_key="...")
graphiti = Graphiti(uri=uri, user=user, password=password, llm_client=llm)

# Azure OpenAI
from openai import AsyncAzureOpenAI
llm = AsyncAzureOpenAI(
    api_key="...",
    api_version="2024-02-15-preview",
    azure_endpoint="https://your-resource.openai.azure.com"
)
graphiti = Graphiti(uri=uri, user=user, password=password, llm_client=llm)

# Ollama (fully local)
llm = AsyncOpenAI(api_key="ollama", base_url="http://localhost:11434/v1")
graphiti = Graphiti(uri=uri, user=user, password=password, llm_client=llm)
```

#### 17.3 Provider Selection Guide

| Provider | Strengths | Weaknesses | Best For |
|---|---|---|---|
| **OpenAI (GPT-4o)** | Best structured output, fastest | Cost, privacy concerns | Default choice, production |
| **Anthropic (Claude)** | Nuanced understanding, long context | Slightly slower | Complex relationship extraction |
| **Google Gemini** | Competitive pricing, long context | Structured output less reliable | Cost-sensitive deployments |
| **Groq** | Extremely fast inference | Model selection limited | High-throughput bulk ingestion |
| **Ollama (local)** | Zero API cost, full privacy | Requires GPU, lower quality extraction | Air-gapped environments, development |
| **Azure OpenAI** | Enterprise compliance, SLA | Setup complexity | Enterprise deployments |

#### 17.4 Embedder Providers

```python
# OpenAI embeddings (default)
embedder = AsyncOpenAI(api_key="sk-...")

# Voyage AI (high quality)
# pip install voyageai
import voyageai
embedder = voyageai.AsyncClient(api_key="...")

# Cohere
# pip install cohere
import cohere
embedder = cohere.AsyncClient(api_key="...")

# Local (sentence-transformers)
# Requires custom wrapper implementing the embedder interface
```

#### 17.5 Example 15: Multi-Provider Setup

See `graphiti_examples/15_multi_provider.py` — demonstrates OpenAI, Anthropic, Ollama, and Azure OpenAI configurations with a factory function and provider selection guide.

---

### Chapter 18 — Graph Database Backends

#### 18.1 Backend Overview

Graphiti supports four graph database backends, each with different trade-offs:

| Backend | Type | Setup Complexity | Production Ready | Best For |
|---|---|---|---|---|
| **Neo4j 5.26+** | Client-server | Medium (Docker) | Yes | Production, multi-user, large graphs |
| **FalkorDB 1.1.2+** | Client-server (Redis-based) | Medium (Docker) | Yes | Low-latency, Redis ecosystem |
| **Kuzu 0.11.2+** | Embedded | None (zero deps) | Single-user only | Development, testing, CLI tools |
| **Amazon Neptune** | Managed cloud | High (AWS) | Yes | AWS-native, serverless |

#### 18.2 Neo4j (Primary/Recommended)

```bash
# Docker
docker run -d --name neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5

# Or use Neo4j Desktop / Neo4j AuraDB
```

```python
graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password"
)
```

Neo4j is the most mature option: rich query language (Cypher), built-in visualization (Neo4j Browser), robust replication and clustering.

#### 18.3 FalkorDB (Redis-Based, Lower Latency)

```bash
docker run -d --name falkordb \
  -p 6379:6379 \
  falkordb/falkordb:latest
```

```python
# pip install graphiti-core[falkordb]
from graphiti_core.drivers.falkordb_driver import FalkorDBDriver

driver = FalkorDBDriver(host="localhost", port=6379)
graphiti = Graphiti(
    uri="redis://localhost:6379",
    graph_driver=driver
)
```

FalkorDB is built on Redis, offering lower latency for graph operations. It's a good choice for latency-sensitive applications already using Redis.

#### 18.4 Kuzu (Embedded, Zero Dependency)

```bash
pip install graphiti-core[kuzu]
```

```python
# Kuzu requires no external server
graphiti = Graphiti(
    uri="kuzu://./graphiti_data",  # Local directory
    # No user/password needed
    graph_driver=KuzuDriver(db_path="./graphiti_data")
)
```

Kuzu is embedded directly in the Python process — no external database server needed. Ideal for:
- Development and testing
- CLI tools and single-user applications
- Scenarios where you can't run a database server

Limitations: file-based locking means only one process can access the database at a time. Not suitable for multi-user servers.

#### 18.5 Amazon Neptune (Cloud, Serverless)

```python
# pip install graphiti-core[neptune]
# Requires AWS credentials configured
graphiti = Graphiti(
    uri="wss://your-neptune-cluster.neptune.amazonaws.com:8182/gremlin",
    graph_driver=NeptuneDriver(
        neptune_endpoint="your-cluster.neptune.amazonaws.com",
        # Uses boto3 default credential chain
    )
)
```

Best for teams already on AWS who want a managed graph database.

#### 18.6 Backend Selection Decision Matrix

```
Single developer, local machine?
  → Kuzu. Zero setup. You're coding in 5 minutes.

Small team, one Neo4j instance is fine?
  → Neo4j via Docker. Mature, reliable, well-documented.

Already running Redis? Need lowest possible latency?
  → FalkorDB. Familiar ops, fast graph queries.

AWS shop? Need serverless, auto-scaling?
  → Amazon Neptune. Managed, integrates with AWS ecosystem.

Multi-region? Hundreds of concurrent agents?
  → Neo4j AuraDB (managed) or Neo4j Enterprise with clustering.
```

#### 18.7 Example 16: FalkorDB Backend

See `graphiti_examples/16_falkordb_backend.py` — demonstrates all four backends with setup instructions and performance characteristics.

---

### Chapter 19 — Saga Abstraction & Narrative Rollups

#### 19.1 What Is a Saga?

A **saga** is a multi-episode narrative that forms a coherent story arc. Introduced in v0.29.0, the saga abstraction allows you to group related episodes and get an LLM-generated narrative summary.

```
Episode 1: "User signed up for QuickShop"              ─┐
Episode 2: "User completed onboarding tutorial"         ─┤
Episode 3: "User made first purchase ($49.99)"          ─┼── Saga: "QuickShop User Journey"
Episode 4: "User reported login issue"                  ─┤
Episode 5: "Support resolved login issue (password)"    ─┘
```

#### 19.2 Using `summarize_saga()`

```python
# Add episodes with saga_id
await graphiti.add_episode(
    name="signup",
    episode_body="Jane signed up for QuickShop on March 1, 2024.",
    source=EpisodeType.text,
    reference_time=datetime(2024, 3, 1, tzinfo=timezone.utc),
    group_id="quickshop",
    saga_id="user_jane_journey"
)

await graphiti.add_episode(
    name="first_purchase",
    episode_body="Jane made her first purchase of $49.99 on March 5.",
    source=EpisodeType.text,
    reference_time=datetime(2024, 3, 5, tzinfo=timezone.utc),
    group_id="quickshop",
    saga_id="user_jane_journey"
)

await graphiti.add_episode(
    name="support_issue",
    episode_body="Jane reported a login issue on March 10. "
                 "Support resolved it by helping her reset her password.",
    source=EpisodeType.text,
    reference_time=datetime(2024, 3, 10, tzinfo=timezone.utc),
    group_id="quickshop",
    saga_id="user_jane_journey"
)

# Get the narrative rollup
saga_summary = await graphiti.summarize_saga(
    saga_id="user_jane_journey",
    group_id="quickshop"
)
print(saga_summary)
# → "Jane signed up for QuickShop on March 1, 2024. She completed onboarding
#    and made her first purchase of $49.99 on March 5. On March 10, she
#    encountered a login issue which support resolved by resetting her password."
```

#### 19.3 Saga vs Episode vs Community

| Concept | Scope | Purpose |
|---|---|---|
| **Episode** | Single data point | Atomic unit of ingestion |
| **Saga** | Sequence of related episodes | Narrative rollup, user journey, incident timeline |
| **Community** | Cluster of related entities | Structural organization, broad retrieval |

Sagas are about **story**. Communities are about **structure**. Use sagas for user journeys, incident timelines, project histories — anything that unfolds as a sequence of events.

#### 19.4 Example 17: Saga Summarization

See `graphiti_examples/17_saga_summarization.py` — follows a customer journey across 5 episodes with saga summarization.

---

### Chapter 20 — Combined Extraction & Bulk Processing

#### 20.1 Four Extraction Modes

Graphiti offers four extraction modes with different cost/quality trade-offs:

| Mode | LLM Calls per Episode | Accuracy | Cost | Best For |
|---|---|---|---|---|
| **Individual (default)** | 2 (entities + relationships) | Highest | Highest | Important episodes, complex narratives |
| **Combined** | 1 (entities + relationships together) | High | ~50% less | Most episodes |
| **Bulk** | Shared across N episodes | Good | ~30-40% less | High-throughput ingestion |
| **Bulk + Combined** | 1 shared across N episodes | Moderate | ~60-70% less | Background batch processing |

#### 20.2 Combined Extraction (v0.29.0+)

```python
# Default: two LLM calls
await graphiti.add_episode(
    name="ep_1",
    episode_body="Alice Chen founded Acme Corp in 2020.",
    source=EpisodeType.text,
    reference_time=datetime(2020, 1, 15, tzinfo=timezone.utc),
    group_id="acme"
    # combined_extraction=False (default)
)

# Combined: one LLM call for entities AND relationships
await graphiti.add_episode(
    name="ep_2",
    episode_body="Bob Martinez joined Acme Corp as CTO in 2021.",
    source=EpisodeType.text,
    reference_time=datetime(2021, 6, 1, tzinfo=timezone.utc),
    group_id="acme",
    combined_extraction=True  # Single LLM call
)
```

The LLM receives a prompt asking it to extract both entities and their relationships in one pass. This cuts the per-episode LLM calls in half but can miss nuanced relationships in complex episodes with many entities.

#### 20.3 Bulk Episode Processing

```python
episodes = [
    {
        "name": f"ticket_{i}",
        "episode_body": f"Support ticket #{i}: {description}",
        "source": EpisodeType.text,
        "reference_time": datetime(2024, 6, i, tzinfo=timezone.utc),
    }
    for i, description in enumerate(support_tickets, 1)
]

await graphiti.add_episode_bulk(
    episodes,
    group_id="support",
    combined_extraction=True  # Optional: also use combined extraction
)
```

Bulk processing sends multiple episodes in a single LLM prompt. The LLM is asked to process all episodes at once, extracting entities and relationships from each. This reduces per-episode token costs by sharing the prompt overhead.

#### 20.4 When to Use Which Mode

```
Is this a single, important episode with complex relationships?
  → Individual (default). Highest accuracy for what matters most.

Is this a routine episode in a high-volume stream (chat, logs)?
  → Combined. Good enough for routine content, half the cost.

Processing a backlog of historical data?
  → Bulk + Combined. Throughput matters more than per-episode precision.

Real-time agent conversation?
  → Individual or Combined. Latency matters; don't batch.
```

#### 20.5 Example 18: Bulk & Combined Extraction

See `graphiti_examples/18_bulk_combined.py` — compares all four extraction modes on the same dataset with timing and cost analysis.

---

### Chapter 21 — Observability & LLM Cost Tracking

#### 21.1 Why Observability Matters

Graphiti's primary operational cost is LLM inference. Understanding where your tokens are going is essential for:

- **Cost control**: OpenAI GPT-4o costs ~$2.50/1M input tokens, ~$10/1M output tokens
- **Performance tuning**: Identifying slow episodes, large extractions
- **Capacity planning**: Projecting costs as data volume grows
- **Debugging**: Understanding why a specific extraction produced unexpected results

#### 21.2 Tracking Episode Processing

```python
import time
from datetime import datetime, timezone

class EpisodeTracker:
    def __init__(self):
        self.episodes = []

    async def track(self, graphiti, name, episode_body, **kwargs):
        start = time.time()
        result = await graphiti.add_episode(
            name=name, episode_body=episode_body, **kwargs
        )
        elapsed = time.time() - start

        # Estimate tokens (rough: ~4 chars per token)
        input_tokens = len(episode_body) / 4
        entities = len(result.nodes) if hasattr(result, 'nodes') else 0
        edges = len(result.edges) if hasattr(result, 'edges') else 0

        self.episodes.append({
            "name": name,
            "time": elapsed,
            "estimated_input_tokens": int(input_tokens),
            "entities_extracted": entities,
            "edges_extracted": edges,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        return result

    def report(self):
        total_time = sum(e["time"] for e in self.episodes)
        total_tokens = sum(e["estimated_input_tokens"] for e in self.episodes)
        estimated_cost = (total_tokens / 1_000_000) * 2.50  # GPT-4o input pricing

        print(f"=== Processing Report ===")
        print(f"Episodes processed: {len(self.episodes)}")
        print(f"Total time: {total_time:.1f}s")
        print(f"Estimated input tokens: {total_tokens:,}")
        print(f"Estimated LLM cost: ${estimated_cost:.4f}")
        print(f"Avg time per episode: {total_time/len(self.episodes):.2f}s")
```

#### 21.3 Production Observability Stack

For production, integrate with established observability tools:

```python
# OpenTelemetry
from opentelemetry import trace
from opentelemetry.exporter.otlp import OTLPSpanExporter

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("graphiti.add_episode")
async def traced_add_episode(graphiti, **kwargs):
    result = await graphiti.add_episode(**kwargs)
    span = trace.get_current_span()
    span.set_attribute("episode.name", kwargs["name"])
    span.set_attribute("episode.group_id", kwargs.get("group_id", "default"))
    return result

# Export to Honeycomb, Datadog, Grafana Tempo, etc.
```

#### 21.4 LLM Cost Optimization Strategies

| Strategy | Savings | Trade-off |
|---|---|---|
| **Combined extraction** | ~50% | Slight accuracy reduction |
| **Bulk processing** | ~30-40% | Batched latency |
| **Prompt compression** | 20-30% | May lose nuance |
| **Smaller model for simple episodes** | 50-80% | Use for routine/structured content |
| **Caching frequent subgraphs** | 30-50% retrieval cost | Redis infrastructure |
| **Classical NLP for deduplication** | 10-20% | Less accurate entity resolution |

#### 21.5 Example 19: Observability

See `graphiti_examples/19_observability.py` — implements a ProcessingReport class with timing, token estimation, cost tracking, and formatted reporting.

---

## PART 4: REAL-WORLD USE CASES

### Chapter 22 — Customer Support Agent with Temporal Memory

**Scenario:** A SaaS company wants an AI support agent that remembers user history across sessions, connects related issues, and tracks resolution over time.

**What Graphiti enables:**
- Remember issues across sessions (3 days, 3 weeks, 3 months apart)
- Connect related issues: "This payment failure is caused by the same account problem from last week"
- Track resolution: "The login workaround from Day 1 was replaced by the permanent fix on Day 14"
- Temporal queries: "What issues did this user report in Q2?"
- Audit trail: Full history of every interaction, visible to both agent and supervisor

**Implementation:** See `graphiti_examples/20_support_agent.py` — simulates a 3-session support conversation over 14 days with a `SupportAgent` class that queries its own memory at each step.

**Architecture pattern:**
```
User sends message → Agent retrieves relevant history → Agent responds
                         │
                         ▼
              Agent stores the interaction as an episode
                         │
                         ▼
         Graphiti extracts entities (Issue, Solution, User)
         and relationships (reported, resolved_by, related_to)
         with temporal metadata (when each was true)
```

---

### Chapter 23 — Personal Assistant with Preference Learning

**Scenario:** An AI assistant that learns user preferences over time, tracks changing preferences, remembers procedures, and proactively uses accumulated knowledge.

**What Graphiti enables:**
- Preference extraction with custom entity types
- Contradiction handling when preferences change ("I used to prefer dark mode, now I like light mode")
- Procedure memory ("How to prepare the weekly report")
- Proactive assistance based on accumulated knowledge
- Full audit trail of preference evolution

**Implementation:** See `graphiti_examples/21_personal_assistant.py` — simulates a `PersonalAssistant` over 4 weeks with preference learning, contradiction handling, procedure memory, and proactive assistance.

**Key pattern — Preference evolution:**
```python
# Week 1: User states a preference
await assistant.remember(
    "I prefer dark mode in all my applications.",
    reference_time=week1
)
# → Extracted: Preference(category="UI", description="dark mode")

# Week 3: User changes their mind
await assistant.remember(
    "Actually, I've switched to light mode. It's easier on my eyes.",
    reference_time=week3
)
# → Old preference: expired_at = now
# → New preference: Preference(category="UI", description="light mode")

# Both preferences remain in the graph — audit trail preserved
```

---

### Chapter 24 — Research & Knowledge Management

**Scenario:** A researcher tracks AI/ML papers, methods, findings, and evolving conclusions over several years.

**What Graphiti enables:**
- Ingest paper summaries as episodes
- Track methods, datasets, baselines, claims
- Temporal: "What was the consensus on attention mechanisms before Mamba?"
- Contradiction: "Which papers challenge the 'attention is all you need' claim?"
- Communities: Auto-detect research clusters (efficiency methods, architecture innovations, etc.)
- Evolution: Trace how a method evolved from its origin paper to current variants

**Implementation:** See `graphiti_examples/22_research_knowledge.py` — simulates tracking AI/ML papers from 2023-2025 with Paper, Method, Author, Dataset, and Finding entities.

**Entity model:**
```python
class Paper(EntityNode):
    title: str
    authors: list[str]
    year: int
    venue: str

class Method(EntityNode):
    name: str
    category: str  # attention, state-space, mixture-of-experts, etc.

class Finding(EntityNode):
    claim: str
    evidence: str
    confidence: float
```

---

### Chapter 25 — Multi-Agent Collaboration Memory

**Scenario:** Multiple AI agents collaborate on a project, each with private memory and shared team memory.

**What Graphiti enables:**
- Per-agent isolation via `group_id`
- Shared memory via common groups
- Cross-agent fact discovery
- Provenance: which agent contributed which fact
- Conflict resolution when agents disagree

**Implementation:** See `graphiti_examples/23_multi_agent.py` — simulates 3 agents (Architect, Developer, QA) collaborating on a software project.

**Architecture pattern:**
```
Agent A (Architect)
  ├── group_id: "agent_a_private"  (personal memory)
  └── group_id: "project_falcon"   (shared team memory)

Agent B (Developer)
  ├── group_id: "agent_b_private"
  └── group_id: "project_falcon"   ← same shared group

Search across ["agent_a_private", "project_falcon"] → sees own + shared
Search across ["project_falcon"] → sees only shared
```

---

### Chapter 26 — Codebase Evolution Tracking

**Scenario:** Track how a codebase changes across releases — which APIs were available when, what was deprecated, what replaced what.

**What Graphiti enables:**
- Entities: Module, Class, Function, API
- Temporal edges: `deprecated_in`, `replaced_by`, `introduced_in`, `depends_on`
- Point-in-time: "What APIs were available in v2.0?"
- Impact analysis: "What depends on `authenticate_v1()`?"
- Migration path: "What replaced `authenticate_v1()`?"

**Implementation:** See `graphiti_examples/24_code_evolution.py` — simulates a software project across 3 releases with deprecation and replacement tracking.

**Entity model:**
```python
class API(EntityNode):
    name: str
    signature: str
    module: str
    version_introduced: str

class Deprecation(EntityEdge):
    deprecated_in_version: str
    replacement_api: Optional[str]
    migration_guide: Optional[str]
```

---

## PART 5: DEPLOYMENT & PRODUCTION

### Chapter 27 — Local Development

#### 27.1 Three Local Dev Setups

**Option 1: Neo4j Desktop** (Windows/Mac/Linux)
- Download Neo4j Desktop from neo4j.com
- Create a local database, set password to "password"
- Start the database — Bolt URI will be `bolt://localhost:7687`
- Best for: visual exploration, Cypher debugging via Neo4j Browser

**Option 2: Docker Compose**
```yaml
# docker-compose.yml
version: '3.8'
services:
  neo4j:
    image: neo4j:5
    ports:
      - "7474:7474"
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_PLUGINS=["apoc"]
    volumes:
      - neo4j_data:/data
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"]
      interval: 10s
      retries: 5

volumes:
  neo4j_data:
```

**Option 3: Kuzu Embedded** (zero dependency)
```python
# No Docker, no server — just pip install
graphiti = Graphiti(
    uri="kuzu://./graphiti_data",
    # Kuzu runs in-process
)
```

#### 27.2 Ollama for Fully Local LLMs
```bash
ollama pull llama3.1:8b
# Or for better extraction quality:
ollama pull llama3.1:70b  # needs ~40GB RAM

# Configure Graphiti
export OPENAI_API_KEY=ollama
export OPENAI_BASE_URL=http://localhost:11434/v1
```

**Critical caveat:** Models below ~70B parameters frequently fail Graphiti's structured output requirements. For reliable entity extraction, use GPT-4o or Claude for production, or a 70B+ local model with careful prompt engineering.

#### 27.3 Example 25: Local Dev Setup

See `graphiti_examples/25_local_dev/README.md` — complete local development guide with all three options, Ollama setup, and verification steps.

---

### Chapter 28 — Production Deployment

#### 28.1 Production Docker Compose

```yaml
version: '3.8'
services:
  neo4j:
    image: neo4j:5-enterprise
    ports:
      - "7687:7687"
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_dbms_memory_heap_max__size=4G
      - NEO4J_dbms_memory_pagecache_size=2G
    volumes:
      - neo4j_data:/data
      - neo4j_backup:/backup
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "${NEO4J_PASSWORD}", "RETURN 1"]
      interval: 15s
      retries: 5
      start_period: 30s
    restart: unless-stopped
    deploy:
      resources:
        limits:
          memory: 8G

  graphiti-mcp:
    image: python:3.11-slim
    command: python -m graphiti_core.mcp_server
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - LLM_MODEL=${LLM_MODEL:-gpt-4o}
    depends_on:
      neo4j:
        condition: service_healthy
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import socket; s=socket.socket(); s.connect(('localhost',8000)); s.close()"]
      interval: 30s

volumes:
  neo4j_data:
  neo4j_backup:
```

#### 28.2 Neo4j Backup Strategy

```bash
# Online backup (Neo4j Enterprise)
neo4j-admin database backup --to-path=/backup neo4j

# For Community edition: use neo4j-admin dump/load
docker exec neo4j neo4j-admin database dump neo4j --to-path=/backup/
docker cp neo4j:/backup/neo4j.dump ./backups/neo4j-$(date +%Y%m%d).dump
```

Schedule: daily incremental, weekly full. Retain: 7 daily, 4 weekly, 12 monthly.

#### 28.3 Zep Cloud vs Self-Hosted

| Aspect | Zep Cloud | Self-Hosted Graphiti |
|---|---|---|
| Setup time | Minutes | Hours to days |
| Infrastructure | None | Neo4j + app server + monitoring |
| Scaling | Automatic | Manual or Kubernetes |
| Compliance | SOC 2, HIPAA BAA | Your responsibility |
| Cost | Free tier → $25/mo Flex → Enterprise | Infrastructure + LLM costs |
| Data residency | US, EU | Anywhere you deploy |
| Dashboard/analytics | Included | Build your own |
| SDK support | Python, TS, Go, REST | Python (Graphiti-core), TS/Go (Zep SDK) |

#### 28.4 Example 26: Production Docker

See `graphiti_examples/26_production_docker/README.md` — complete production deployment guide with Docker Compose, backup strategy, monitoring, and migration path.

---

### Chapter 29 — Scaling Strategies

#### 29.1 The Scaling Dimensions

| Dimension | Challenge | Solution |
|---|---|---|
| **Write throughput** | LLM rate limits (500 RPM/tier) | Bulk processing, combined extraction, multiple API keys |
| **Read latency** | Graph traversal depth | Redis cache, Kuzu for single-user, FalkorDB for low latency |
| **Multi-agent concurrency** | Kuzu file locking | Neo4j or FalkorDB for multi-user |
| **LLM costs** | $2.50-10/1M tokens | Combined extraction, smaller models for simple episodes |
| **Data volume** | Graph size growth | Incremental community updates, periodic cleanup of expired edges |

#### 29.2 Parallel Episode Processing

Each `group_id` processes episodes sequentially, but different groups process in parallel:

```python
# These process concurrently
await asyncio.gather(
    graphiti.add_episode(name="a1", ..., group_id="user_a"),
    graphiti.add_episode(name="b1", ..., group_id="user_b"),
    graphiti.add_episode(name="c1", ..., group_id="user_c"),
)
```

For high-throughput ingestion, partition data across groups and process in parallel.

#### 29.3 Redis Caching for Frequent Subgraphs

```python
import redis
import json

cache = redis.Redis(host="localhost", port=6379, decode_responses=True)

async def cached_search(graphiti, query, group_ids, ttl=3600):
    cache_key = f"search:{hash(query)}:{':'.join(group_ids)}"
    cached = cache.get(cache_key)
    if cached:
        return json.loads(cached)

    results = await graphiti.search(query=query, group_ids=group_ids)
    cache.setex(cache_key, ttl, json.dumps([r.dict() for r in results]))
    return results
```

#### 29.4 Zep's Production Optimization Patterns

From Zep's 30x scaling experience:

1. **Separate search from graph storage**: Move vector and BM25 search to dedicated infrastructure. Let the graph DB focus on graph operations only.
2. **Use classical NLP where possible**: Shannon entropy for information density, TF-IDF for deduplication, LSH for similarity matching. Cuts LLM token usage by 50%.
3. **Rewrite LLM gateway in a low-overhead language**: Go for the API gateway layer — tiny memory footprint, intelligent rate limiting.
4. **Pre-purchase inference capacity**: For consistent workloads, reserved capacity is cheaper than pay-per-token.

**Results:** Graph search P95 600ms → 150ms, context retrieval P95 → 200ms, episode processing latency improved 92%.

#### 29.5 Example 27: Scaling Guide

See `graphiti_examples/27_scaling_guide.md` — scaling checklist, benchmarks, Redis configuration, and capacity planning.

---

### Chapter 30 — Security, Multi-Tenancy & Compliance

#### 30.1 Multi-Tenancy with `group_id`

The `group_id` parameter provides namespace-level data isolation:

```python
# Users are isolated
await graphiti.add_episode(..., group_id="tenant_a")
await graphiti.add_episode(..., group_id="tenant_b")

# Each tenant only sees their data
results = await graphiti.search(..., group_ids=["tenant_a"])
```

This is **logical** isolation, not physical. For strict multi-tenant requirements, run separate Neo4j databases.

#### 30.2 Neo4j Authentication

```bash
# Production Neo4j configuration
NEO4J_dbms_security_auth__enabled=true
NEO4J_dbms_security_auth__minimum__password__length=12
NEO4J_dbms_security_procedures_unrestricted=apoc.*  # Limit in production
```

Create separate Neo4j users for different services:
```cypher
CREATE USER graphiti_service SET PASSWORD 'strong-password-here' CHANGE NOT REQUIRED;
GRANT ROLE editor TO graphiti_service;
CREATE USER read_only_service SET PASSWORD 'another-password' CHANGE NOT REQUIRED;
GRANT ROLE reader TO read_only_service;
```

#### 30.3 API Key Management

```bash
# Never hardcode API keys
export OPENAI_API_KEY=$(vault read -field=api_key secret/openai)
export NEO4J_PASSWORD=$(vault read -field=password secret/neo4j)
```

Use a secrets manager in production: HashiCorp Vault, AWS Secrets Manager, GCP Secret Manager, or Kubernetes Secrets.

#### 30.4 PII Considerations

Graphiti stores raw episode content (when `store_raw_episode_content=True`). If episodes contain PII:

- **Pre-process**: Strip PII before calling `add_episode()` using a library like `presidio-analyzer` or `spacy`
- **Data residency**: Deploy Neo4j in the required region
- **Access control**: Use `group_id` scoping to limit who can search which data

#### 30.5 GDPR Right-to-Erasure

```python
# Delete all data for a specific user
await graphiti.delete_group(group_id="user_123")
# Or remove specific episodes
await graphiti.remove_episode(episode_uuid="...")
```

This cascades: deleting an episode removes its MENTIONS edges to entities, but shared entities (referenced by other episodes) are preserved.

#### 30.6 Compliance Matrix

| Standard | Self-Hosted Graphiti | Zep Cloud |
|---|---|---|
| SOC 2 Type 2 | Your responsibility | Yes |
| HIPAA BAA | Your responsibility | Yes |
| GDPR | Tools provided (delete_group, remove_episode) | Built-in |
| Data residency | Any region you deploy | US, EU |
| Encryption at rest | Neo4j encryption (Enterprise) | Yes |
| Encryption in transit | TLS (configure Neo4j) | Yes |
| Audit logging | Neo4j query log + OTEL traces | Built-in dashboard |

#### 30.7 Example 28: Security Configuration

See `graphiti_examples/28_security.md` — security hardening checklist with authentication, network security, PII handling, GDPR compliance, and threat model.

---

## PART 6: ARCHITECTURAL DECISIONS & TRADEOFFS

### Chapter 31 — Why Bi-Temporal? (Event Time vs System Time)

#### 31.1 The Problem with Single-Timeline Systems

Most databases track one time dimension: `created_at` / `updated_at`. This tells you when data was **recorded**, not when it was **true**. For knowledge graphs serving AI agents, this distinction is critical:

- **"created_at: March 2024"** — The system learned about a fact in March
- **"valid_at: January 2024"** — The fact was true in January

Without this distinction, you can't answer: "What did the agent know when it made that decision in February 2024?" The agent might have learned something in March about events in January — and that knowledge wasn't available in February.

#### 31.2 The Four-Timestamp Architecture

Every EntityEdge carries four timestamps:

```
valid_at     — "Alice became CEO on Jan 15, 2024" (event time start)
invalid_at   — "Alice stopped being CEO on Jun 1, 2024" (event time end)
created_at   — "System learned about Alice being CEO on Feb 1, 2024" (system time start)
expired_at   — "System learned Alice is no longer CEO on Jul 15, 2024" (system time end)
```

This enables:
- **Event-time queries**: "Who was CEO in May 2024?" → Alice (valid_at <= May < invalid_at)
- **System-time queries**: "What did the system believe in March 2024?" → Alice was CEO (created_at <= March < expired_at)
- **Audit queries**: "Show me the complete CEO history with when each fact was known"

#### 31.3 The Storage Cost of Keeping Expired Edges

Expired edges accumulate. A graph tracking a company over 10 years might have 10 CEO terms, each with an expired edge. The storage cost is negligible (bytes per edge) compared to the value of preserved history.

The real cost is **query complexity**: every "current state" query must filter out expired edges. Graphiti handles this transparently — expired edges are excluded from default searches.

#### 31.4 When Bi-Temporal Is Overkill

For applications where:
- Facts never change (static knowledge base)
- There's no need for audit trails
- "Last write wins" is sufficient

...a simple key-value store or vector DB with `updated_at` is simpler and cheaper. Use bi-temporality when tracking fact evolution is a **core requirement**, not a nice-to-have.

---

### Chapter 32 — Episode-Based vs Batch Processing

#### 32.1 Why Episodes Instead of Document Chunks

Traditional RAG chunks documents and loses provenance. Graphiti's episode model preserves:

- **Who** said it (source_description, group_id)
- **When** it was said (reference_time, created_at)
- **What else** was said at the same time (co-occurring facts)
- **Why** it might have changed (episode ordering reveals causality)

A document chunk tells you "this text exists." An episode tells you "at this specific time, from this specific source, this specific information was received."

#### 32.2 The Cost of Per-Episode Processing

Each episode triggers LLM calls. For high-volume data streams (chat messages, log entries, sensor readings), this can be expensive:

- 1,000 episodes/day × ~1,000 tokens/episode × $2.50/1M tokens = ~$2.50/day in LLM costs
- 100,000 episodes/day = ~$250/day

Mitigation: combined extraction, bulk processing, smaller models for routine content.

#### 32.3 When Batch Processing Would Be Better

Episode-based ingestion is suboptimal when:
- You're ingesting a large static document corpus (Cognee or GraphRAG is better)
- You don't need temporal tracking (simple RAG is sufficient)
- Episodes arrive faster than the LLM can process them (need a queue/deferred processing pattern)

---

### Chapter 33 — Hybrid Search Rationale

#### 33.1 Why One Retrieval Method Isn't Enough

| Query | Semantic (embeddings) | BM25 (keywords) | Graph (traversal) |
|---|---|---|---|
| "What's the Falcon-X?" | Good — finds related concepts | OK — matches "Falcon-X" | OK — finds connected entities |
| "Falcon-X" (exact name) | OK — embeddings capture it | Excellent — exact match | N/A — no graph starting point |
| "Who worked on the drone project?" | Good — "drone" ≈ "Falcon-X" | Poor — "drone" not in text | Excellent — follows team relationships |
| "What's related to Alice's work?" | Poor — vague query | Poor — no keywords | Excellent — graph neighborhood |

No single method handles all query types well. The combination handles each other's weaknesses.

#### 33.2 RRF vs Linear Combination vs Learning-to-Rank

**RRF (Reciprocal Rank Fusion):**
- Simple, parameter-free (beyond `k`)
- Handles score scale differences between methods naturally
- Proven effective in practice (used by Twitter, Spotify, academic search)

**Why not a learned model?** Learning-to-rank requires training data — relevance judgments for (query, edge) pairs. Graphiti operates in domains where such data rarely exists. RRF works out of the box.

#### 33.3 The Cross-Encoder Trade-Off

Cross-encoder reranking (query+document → relevance score) is more accurate than embedding similarity (cosine between separate embeddings) because the model sees the interaction between query and document. But it's **computationally expensive**: you must run the model on every candidate pair, whereas embedding similarity is a pre-computed dot product.

Graphiti's design: use fast methods (embeddings + BM25 + graph) for candidate generation, apply cross-encoder only if you need maximum accuracy and can tolerate the latency.

---

### Chapter 34 — LLM Dependency in Extraction: The Double-Edged Sword

#### 34.1 Why LLMs for Entity Extraction

Classical NER (spaCy, Stanford NER) works well for predefined categories: Person, Organization, Location. It fails on:
- Domain-specific entities: product SKUs, API names, research methods, contract clauses
- Implicit entities: "the login issue" (not a named entity, but a distinct concept)
- Relationship extraction: "Alice left Acme Corp to join Beta Inc" — classical methods miss the temporal implication

LLMs generalize across entity types without retraining. They understand context and can extract entities matching your custom schema.

#### 34.2 The Structured Output Dependency

This is Graphiti's biggest operational risk. The LLM must produce valid, schema-compliant JSON for every episode. When it fails (malformed JSON, hallucinated fields, wrong types), the extraction fails.

**Mitigations:**
- Use models with strong structured output: GPT-4o, Claude Opus/Sonnet (avoid GPT-3.5, small local models)
- Set `temperature=0` for deterministic extraction
- Implement retry logic for failed extractions
- Validate extracted entities against the Pydantic schema before inserting

#### 34.3 Zep's Production Pattern: Replace LLM with Classical NLP

From Zep's scaling blog post: they replaced LLM calls with classical NLP for specific tasks:

| Task | Before | After | Savings |
|---|---|---|---|
| Information density | LLM scoring | Shannon Entropy | Eliminated LLM call |
| Entity deduplication | LLM comparison | TF-IDF + LSH | Eliminated LLM call |
| Similarity matching | LLM reasoning | Cosine similarity | Eliminated LLM call |

Total: 50% reduction in LLM token usage. The lesson: use LLMs for what they're uniquely good at (understanding natural language, extracting structured entities), and use classical methods for everything else.

---

### Chapter 35 — Graph DB Choice: Neo4j vs FalkorDB vs Kuzu

#### 35.1 Decision Matrix

| Criteria | Neo4j | FalkorDB | Kuzu | Amazon Neptune |
|---|---|---|---|---|
| Setup complexity | Medium | Medium | None | High |
| Multi-user support | Excellent | Good | None (file lock) | Excellent |
| Query latency | <100ms typical | <50ms typical | <10ms (in-process) | 100-500ms (network) |
| Max graph size | Billions of nodes | Billions of nodes | Millions of nodes | Billions of nodes |
| Cypher support | Native | Limited (Redis Graph) | Limited (Kuzu Cypher) | No (Gremlin/openCypher) |
| Vector search | v5.0+ built-in | Via Redis Stack | No (separate store) | Via OpenSearch |
| Operational maturity | Very high (15+ years) | Moderate (3+ years) | Low (newer project) | High (AWS managed) |
| Cost | Free (Community) / Paid (Enterprise) | Free (OSS) / FalkorDB Cloud | Free (OSS) | AWS pricing |

#### 35.2 The Kuzu Advantage

Kuzu's embedded architecture is unique. No server process, no network calls, no authentication configuration. For development, testing, and single-user tools, this eliminates an entire class of operational problems. But the file-based locking means you cannot have concurrent writers — a hard limitation for multi-agent systems.

#### 35.3 The Neo4j Reality

Neo4j is the default for a reason: it's the most mature graph database, with the best tooling (Neo4j Browser, Bloom visualization, Cypher query language), the largest community, and the most documentation. But it's also a separate service to manage, monitor, back up, and scale. For teams without graph DB expertise, this is a real operational burden.

---

### Chapter 36 — Graphiti vs Building Your Own: Build vs Buy

#### 36.1 What Graphiti Gives You

| Component | Effort to Build Yourself |
|---|---|
| Bi-temporal data model with four timestamps | 2-4 engineer-weeks |
| LLM-based entity/relationship extraction with structured output | 4-8 engineer-weeks |
| Entity deduplication (exact + fuzzy + LLM resolution) | 2-3 engineer-weeks |
| Contradiction detection with edge expiration | 2-3 engineer-weeks |
| Hybrid search (semantic + BM25 + graph + RRF + rerank) | 6-10 engineer-weeks |
| Incremental community detection with LLM summarization | 2-4 engineer-weeks |
| Multi-provider plugin architecture (5 LLM + 4 graph DBs) | 4-6 engineer-weeks |
| MCP server + REST API | 2-3 engineer-weeks |
| SDK (Python) + TypeScript + Go (Zep platform) | 4-8 engineer-weeks |
| Documentation, tests, 24K GitHub stars community | Priceless |

**Total DIY estimate:** 28-49 engineer-weeks (7-12 months) for a production-quality equivalent.

#### 36.2 When NOT to Use Graphiti

1. **Simple chat memory** — If you just need "remember what was said in this conversation," use a buffer or vector store. Graphiti is overkill.
2. **Static document Q&A** — If your data doesn't change, Microsoft GraphRAG or LlamaIndex are better fits.
3. **Fully air-gapped with small models** — If you must run on consumer hardware with local LLMs < 70B parameters, Graphiti's structured output dependency will frustrate you.
4. **No graph DB expertise or willingness to acquire it** — Running Neo4j in production is a skill. If you don't want to learn it, use Zep Cloud.
5. **Real-time streaming (sub-second ingestion)** — Graphiti's write path includes LLM calls (seconds per episode). For sub-second ingestion, buffer and batch-process.
6. **Document-heavy, multimodal ingestion** — If you need PDF, image, and audio ingestion, Cognee's 30+ adapters are a better fit. Graphiti is text/episode-focused.
7. **You need the absolute best benchmark scores** — Hindsight scores 91.4% on LongMemEval vs Graphiti's 63.8%. If this is your primary metric, look at Hindsight.

---

## PART 7: PROS & CONS — THE HONEST ASSESSMENT

### Chapter 37 — Pros: Where Graphiti Shines

1. **Bi-temporal fact tracking** — The only open-source framework with true dual-timeline (event time + system time) on every fact. This is Graphiti's defining feature.

2. **Incremental, real-time updates** — New episodes integrate immediately. No batch recomputation, no re-indexing delays. The graph evolves continuously as data arrives.

3. **Sub-second hybrid retrieval** — Semantic + BM25 + graph traversal, merged via RRF, with optional cross-encoder reranking. No LLM call at query time means fast, predictable latency.

4. **Fact provenance** — Every EntityEdge traces back to its source Episode via MENTIONS edges. You always know where a fact came from.

5. **Contradiction handling with audit trail** — Old facts are expired, not deleted. Full history preserved for audit, debugging, and temporal queries.

6. **Episode-based ingestion model** — Episodes preserve context: who said what, when, and in what order. This is natural for agent conversations, user interactions, and event streams.

7. **Multi-provider flexibility** — Swap LLMs (OpenAI, Anthropic, Gemini, Groq, Ollama), embedders, and graph databases (Neo4j, FalkorDB, Kuzu, Neptune) without changing application code.

8. **Production battle-tested** — Zep's 30x scaling story proves the architecture works at scale. P95 search latency dropped from 600ms → 150ms under production load.

9. **MCP-native** — First-class AI assistant integration via MCP server. Claude Desktop, Cursor, and other MCP clients can use Graphiti directly.

10. **Open source (Apache 2.0) with managed cloud option** — Self-host for control, or use Zep Cloud for zero-ops. No vendor lock-in.

---

### Chapter 38 — Cons & Gotchas

1. **Graph DB dependency** — You must run and manage Neo4j, FalkorDB, or Kuzu. This is non-negotiable operational complexity that simpler memory systems (Mem0 Docker, vector stores) avoid.

2. **LLM costs at ingest** — Every episode triggers LLM calls for extraction. At scale, this is the dominant cost. Plan your LLM budget accordingly.

3. **Not for static document corpora** — If you're indexing a PDF library, Cognee or GraphRAG is better. Graphiti is designed for dynamic, evolving data.

4. **Limited multimodal support** — Text-focused. No native PDF parsing, image OCR, or audio transcription. If you need these, preprocess data yourself or use Cognee.

5. **Pre-1.0 API stability** — The API is evolving. Breaking changes are possible between minor versions. Pin your `graphiti-core` version and check the changelog.

6. **LongMemEval 63.8%** — Good, but not best-in-class. Hindsight (91.4%) and MemOS (85.4%) score higher. If raw benchmark performance is your primary metric, Graphiti isn't the leader.

7. **Cold-start problem** — The knowledge graph needs episodes (roughly 10-20+) before meaningful structure emerges. First queries on a fresh graph will return sparse results.

8. **Overkill for simple chat memory** — If you just need to remember recent conversation turns, use a sliding window buffer or a vector store. Graphiti's complexity is wasted on simple use cases.

9. **No built-in visualization** — Unlike Cognee (D3.js HTML export) or Neo4j Bloom, Graphiti has no graph visualization. You'll need Neo4j Browser or a custom solution.

10. **Self-hosting ≠ Zep Cloud** — The open-source library lacks the managed platform's dashboard, analytics, automatic scaling, and compliance certifications. These gaps matter in enterprise deployments.

---

### Chapter 39 — Comparison Matrix (Graphiti vs Alternatives)

| Feature | Graphiti | Cognee | MS GraphRAG | Mem0 | Hindsight | LlamaIndex |
|---|---|---|---|---|---|---|
| Knowledge Graph | Temporal KG | Poly-store KG | Communities | Vector + Graph (Pro) | Multi-strategy KG | PropertyGraph |
| Temporal Reasoning | Bi-temporal | Metadata only | Basic timestamps | No | Yes | No |
| Vector Search | Yes | Yes | Yes | Yes | Yes | Yes |
| BM25/Full-text | Yes | No | No | No | Yes | No |
| Graph Traversal | Yes | Yes | Partial (communities) | No | Yes | Yes |
| Hybrid Search | Semantic+BM25+Graph+RRF | Graph+Vectors | Communities+Chunks | Vector only | 4 parallel retrievers | PropertyGraph |
| Session/Episode Memory | Episode model | V2 API (session_id) | No | Yes | Yes | No |
| Multi-Modal | Text-focused | Images/Audio/Video | Text only | No | No | Yes |
| Data Connectors | Episode-only (message, text, json, fact_triple) | 30+ formats | Text only | API-based | Episode-based | 20+ |
| Custom Entities | Yes (Pydantic) | Yes (DataPoints) | No | No | Yes | Yes |
| Community Detection | Yes (label propagation) | No | Yes (Leiden) | No | No | No |
| SDK Languages | Python, TS, Go | Python | Python | Python, TS | Python | Python, TS |
| Self-Hosted | Yes (Neo4j req) | Yes | Yes | Yes (Docker) | Yes (Docker) | Yes |
| Managed Cloud | Zep Cloud | Cognee Cloud | No | Mem0 Cloud | Yes | LlamaCloud |
| MCP Server | Yes | Yes | No | Yes | No | No |
| LongMemEval Score | 63.8% (GPT-4o) | Not published | Not published | 49.0% | 91.4% | Not published |
| Open Source License | Apache 2.0 | Apache 2.0 | MIT | Apache 2.0 | MIT | MIT |
| GitHub Stars | ~24K (Zep ecosystem) | ~14K | ~25K | ~25K | ~3K | ~38K |

---

## APPENDICES

### Appendix A — Quick Reference Card

#### Graphiti Constructor

```python
from graphiti_core import Graphiti

graphiti = Graphiti(
    uri="bolt://localhost:7687",
    user="neo4j",
    password="password",
    llm_client=None,           # AsyncOpenAI (default)
    embedder=None,              # AsyncOpenAI (default)
    cross_encoder=None,         # Optional reranker
    graph_driver=None,          # Custom Neo4j/FalkorDB/Kuzu driver
    store_raw_episode_content=True,
    max_coroutines=10,
    ensure_ascii=False,
)
await graphiti.build_indices_and_constraints()
```

#### Episode API

```python
await graphiti.add_episode(
    name="unique_name",
    episode_body="...",
    source=EpisodeType.text,      # text, message, json, fact_triple
    source_description="",
    reference_time=datetime.now(timezone.utc),
    group_id="namespace",
    entity_types={"Person": Person},
    combined_extraction=False,
)

await graphiti.add_episode_bulk(episodes_list, group_id="namespace")

await graphiti.retrieve_episodes(
    group_ids=["namespace"],
    limit=10,
)

await graphiti.remove_episode(episode_uuid)
```

#### Search API

```python
# Basic
edges = await graphiti.search(
    query="...",
    group_ids=["namespace"],
    num_results=10,
    center_node_uuid=None,
    filters=None,
)

# Advanced
from graphiti_core.search.search_config import SearchConfig, SearchRecipes
from graphiti_core.search.search_filters import SearchFilters

results = await graphiti.search_(
    query="...",
    config=SearchConfig(
        recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
        num_results=20,
        max_depth=3,
    ),
    group_ids=["namespace"],
    center_node_uuid=None,
    filters=SearchFilters(
        valid_at=datetime(...),
        valid_at_start=datetime(...),
        valid_at_end=datetime(...),
        edge_labels=["RELATES_TO"],
        node_labels=["Person"],
        group_ids=["namespace"],
    ),
)
```

#### Community Detection

```python
await graphiti.build_communities()
```

#### Saga Summarization

```python
summary = await graphiti.summarize_saga(
    saga_id="saga_identifier",
    group_id="namespace",
)
```

#### EpisodeType Enum

```python
from graphiti_core.nodes import EpisodeType

EpisodeType.message      # Conversation message with speaker/role
EpisodeType.text          # Free-form narrative text
EpisodeType.json          # Structured JSON data
EpisodeType.fact_triple   # Subject-predicate-object triple
```

#### Custom Entity Pattern

```python
from pydantic import Field
from graphiti_core.nodes import EntityNode
from typing import Optional

class MyEntity(EntityNode):
    name: str
    description: str = Field(default="")
    category: Optional[str] = Field(default=None)
```

#### Cleanup

```python
await graphiti.close()                    # Close connection
await graphiti.delete_group(group_id)     # Delete all data for a group
```

---

### Appendix B — Troubleshooting Common Issues

| Symptom | Likely Cause | Solution |
|---|---|---|
| `add_episode()` hangs | LLM rate limits | Reduce `max_coroutines`; check API key quota; check for 429 errors |
| `search()` returns empty | No episodes ingested yet | Add at least 10-20 episodes before expecting rich results |
| `search()` returns empty | group_id mismatch | Verify you're searching the same group_id used in add_episode |
| Neo4j connection refused | Neo4j not running | `docker ps` — check if Neo4j container is up; check port 7687 |
| Kuzu lock error | Another process accessing the database | Kuzu is single-writer; close other connections |
| Structured output failures | LLM model too small | Use GPT-4o or Claude; local models < 70B struggle with JSON schema |
| Duplicate entities | Dedup threshold too high | Default threshold is fine; check if entities are genuinely different |
| High LLM costs | Too many individual episodes | Use `combined_extraction=True` and `add_episode_bulk()` |
| Slow queries on large graph | Graph traversal too deep | Reduce `max_depth` in SearchConfig; add Redis cache |
| `remove_episode()` didn't remove entities | Entity referenced by other episodes | Entities with multiple episode references are preserved — by design |
| MCP server doesn't start | Wrong Python path | Verify `python -m graphiti_core.mcp_server` resolves correctly |
| REST API 500 errors | Missing environment variables | Check NEO4J_URI, OPENAI_API_KEY are set |
| Communities not appearing | Not enough episodes | Need ~10+ episodes for meaningful community structure |

---

### Appendix C — Configuration Reference

#### Environment Variables

```bash
# Graph Database
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# LLM Provider
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o                          # Default model for extraction
EMBEDDING_MODEL=text-embedding-3-small    # Default model for embeddings
MAX_COROUTINES=10                         # Concurrent LLM calls

# MCP Server
USE_CUSTOM_ENTITIES=true                  # Enable Preference/Procedure/Requirement types
CORS_ALLOWED_ORIGINS=*                    # For REST API server

# Alternative providers (set in Graphiti constructor, not env)
# Anthropic: ANTHROPIC_API_KEY
# Google: GOOGLE_API_KEY
# Groq: GROQ_API_KEY
# Azure: AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT
```

#### Graphiti Constructor — All Parameters

```python
Graphiti(
    uri: str,                               # Database URI
    user: str = "neo4j",                    # Database user
    password: str = "password",             # Database password
    llm_client: Any = None,                 # Async LLM client
    embedder: Any = None,                   # Async embedder client
    cross_encoder: Any = None,              # Async cross-encoder for reranking
    graph_driver: Any = None,               # Custom graph driver
    store_raw_episode_content: bool = True, # Keep raw episode text
    max_coroutines: int = 10,              # Max concurrent LLM calls
    ensure_ascii: bool = False,            # Convert Unicode to ASCII
    episode_window_len: int = 3,           # Previous episodes for context
)
```

#### SearchConfig — All Parameters

```python
SearchConfig(
    recipe: SearchRecipes = EDGE_HYBRID_SEARCH_RRF,
    num_results: int = 10,
    max_depth: int = 3,
    reranker: Any = None,                  # Cross-encoder instance
    min_score: float = 0.0,
)
```

#### SearchFilters — All Parameters

```python
SearchFilters(
    group_ids: list[str] = None,
    valid_at: datetime = None,
    valid_at_start: datetime = None,
    valid_at_end: datetime = None,
    created_at_start: datetime = None,
    created_at_end: datetime = None,
    edge_labels: list[str] = None,
    node_labels: list[str] = None,
)
```

---

### Appendix D — Glossary

| Term | Definition |
|---|---|
| **Episode** | The atomic unit of data ingestion. Contains content, timestamp, source metadata, and namespace. |
| **EpisodicNode** | Neo4j node representing an ingested episode. Links to extracted entities via MENTIONS edges. |
| **EntityNode** | Neo4j node representing a real-world entity (person, org, concept, product). Carries name, summary, labels, and embedding. |
| **EntityEdge** | Neo4j relationship between two EntityNodes. Carries the fact text, bi-temporal timestamps, and embedding. |
| **CommunityNode** | Neo4j node representing a cluster of semantically related entities, identified by label propagation. |
| **Bi-temporal** | Tracking two time dimensions: event time (when facts were true) and system time (when facts were ingested). |
| **valid_at** | Event time: when the fact became true in reality. |
| **invalid_at** | Event time: when the fact stopped being true in reality. |
| **created_at** | System time: when the fact was ingested into the graph. |
| **expired_at** | System time: when the fact was superseded by a contradictory fact. |
| **RRF** | Reciprocal Rank Fusion — algorithm for merging ranked results from multiple retrieval methods. |
| **Node Resolution** | The process of determining whether a newly extracted entity matches an existing entity (exact match → fuzzy match → LLM reasoning). |
| **Edge Resolution** | The process of determining whether a newly extracted relationship duplicates or contradicts an existing edge. |
| **group_id** | Namespace identifier for multi-tenancy. Episodes and entities are scoped to groups. |
| **Saga** | A sequence of related episodes sharing a `saga_id`, summarizable into a narrative rollup. |
| **Label Propagation** | Community detection algorithm where nodes iteratively adopt the most common label among their neighbors. |
| **Cross-Encoder** | A model that scores a (query, document) pair together, producing more accurate relevance judgments than separate embeddings. |
| **MCP** | Model Context Protocol — standard for exposing tools to AI assistants. Graphiti ships with an MCP server. |
| **Reference Time** | The event time assigned to an episode. All extracted facts inherit this as their `valid_at` baseline. |
| **Episode Window** | The number of previous episodes retrieved as context for a new episode (`EPISODE_WINDOW_LEN`, default 3). |

---

### Appendix E — Migration Guide: Zep Community Edition → Raw Graphiti

#### What Was Deprecated

Zep Community Edition (the self-hosted version of the Zep platform) was deprecated in February 2026. Users must migrate to raw Graphiti (the open-source library) or Zep Cloud.

#### Terminology Mapping

| Zep CE Concept | Graphiti Equivalent | Notes |
|---|---|---|
| Session | group_id | Sessions are now just groups |
| Thread | group_id | Threads are now just groups |
| Graph | group_id | Standalone Graphs = additional group_ids |
| User memory | group_id="user_{id}" | Use a naming convention for user-specific groups |
| Message | Episode (EpisodeType.message) | Same concept, different API |
| Fact | EntityEdge | Facts are edges with temporal metadata |
| Fact Rating | Not available | Use custom entity types and user summary instructions instead |
| Mode parameter (getUserContext) | SearchConfig recipe | Different search strategies via recipes |
| Min score parameter | SearchConfig min_score | Still available in search_() |

#### API Migration

```python
# Zep CE: Add memory
# POST /v2/sessions/{session_id}/memory
# {"messages": [{"role": "user", "content": "I prefer dark mode"}]}

# Graphiti equivalent:
await graphiti.add_episode(
    name="memory_1",
    episode_body="I prefer dark mode",
    source=EpisodeType.message,
    reference_time=datetime.now(timezone.utc),
    group_id="session_123",
)

# Zep CE: Search memory
# POST /v2/sessions/{session_id}/search
# {"query": "What are my preferences?", "min_score": 0.5}

# Graphiti equivalent:
results = await graphiti.search_(
    query="What are my preferences?",
    config=SearchConfig(min_score=0.5),
    group_ids=["session_123"],
)
```

#### Data Migration

Zep CE stored data in a PostgreSQL database with a different schema than raw Graphiti (which stores directly in Neo4j). There is no automated migration tool. The recommended approach:

1. Export data from Zep CE as JSON (using the Zep API)
2. Transform to episode format
3. Re-ingest into Graphiti via `add_episode_bulk()`

This is essentially a re-processing of your historical data, which means you'll incur LLM costs during migration. Plan accordingly for large datasets.

---

### Appendix F — Further Reading & Resources

#### Official Resources
- **GitHub Repository**: [github.com/getzep/graphiti](https://github.com/getzep/graphiti)
- **Official Documentation**: [help.getzep.com/graphiti](https://help.getzep.com/graphiti)
- **Zep Platform Docs**: [help.getzep.com](https://help.getzep.com)
- **PyPI**: [pypi.org/project/graphiti-core](https://pypi.org/project/graphiti-core/)

#### Research & Papers
- **Zep Architecture Paper**: [Zep: A Temporal Knowledge Graph Architecture for Agent Memory](https://arxiv.org/abs/2501.13956) (arXiv:2501.13956)
- **LongMemEval Benchmark**: Long-term memory evaluation for AI agents
- **Deep Memory Retrieval (DMR)**: Benchmark used alongside LongMemEval

#### Community & Forks
- **rawr-ai/mcp-graphiti**: Enhanced MCP server with additional tools
- **Facronactz/Graphiti-MCP**: Expanded entity types (8+), FalkorDB support, YAML configuration
- **mjunaidca/graphiti_memory_mcp_server**: Streamable HTTP transport for MCP

#### Engineering Blog Posts
- **How We Scaled Zep 30x in 2 Weeks**: [blog.getzep.com/scaling-agent-memory-zep-30x](https://blog.getzep.com/scaling-agent-memory-zep-30x/)
- **Neo4j: Graphiti Knowledge Graph Memory**: [neo4j.com/blog/developer/graphiti-knowledge-graph-memory](https://neo4j.com/blog/developer/graphiti-knowledge-graph-memory/)

#### Comparisons (Third-Party)
- **Vectorize.io: Zep vs Cognee**: Detailed comparison of agent memory frameworks
- **Vectorize.io: Mem0 vs Zep**: Comparison focusing on self-hosting complexity
- **Atlan: Best AI Agent Memory Frameworks 2026**: Market overview and rankings

#### Notebooks & Tutorials
- **NirDiamant/Agent_Memory_Techniques**: 30 runnable Jupyter notebooks covering Graphiti, Mem0, Letta, and others (Technique #24: Graph Memory with Graphiti)
- **FalkorDB: Get Started with Graphiti**: [falkordb.com/blog/graphiti-get-started](https://www.falkordb.com/blog/graphiti-get-started/)

---

> **That's the complete Graphiti In-Depth handbook.** All example code referenced throughout lives in the `graphiti_examples/` directory. Each example is a self-contained, runnable script. Start with `01_hello_graphiti.py` and work your way up. For questions or corrections, file an issue at [github.com/getzep/graphiti](https://github.com/getzep/graphiti).
