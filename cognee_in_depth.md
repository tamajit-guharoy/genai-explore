# Cognee In-Depth: The Complete Developer's Handbook

> **A comprehensive guide to building AI memory systems with Cognee — from first principles to production.**

---

## PART 0: FOUNDATIONS

### Chapter 0 — Preface & Who This Guide Is For

**Target audience:** This guide is written for AI engineers, agent builders, and developers who have worked with RAG (Retrieval-Augmented Generation) and are hitting its limits. You should be comfortable with Python 3.10+, async/await patterns, and basic LLM concepts (embeddings, prompts, token limits). No prior knowledge of knowledge graphs is assumed.

**What you'll build:** By the end of this guide, you'll have 25 working examples covering everything from a minimal "hello world" pipeline to production deployments with custom data points, multi-modal ingestion, permissioned multi-tenancy, and observable, self-improving knowledge graphs.

**How this guide is structured:** We start with the problem Cognee solves (Part 0), then drill into its architecture (Part 1), master its APIs (Part 2), explore advanced features (Part 3), apply everything to real-world use cases (Part 4), deploy to production (Part 5), and finally examine the architectural trade-offs that shaped Cognee's design (Part 6-7). Each chapter builds on the previous one. Code examples are numbered and live in the `cognee_examples/` directory.

**Prerequisites:**
```bash
pip install cognee openai
# or for local LLM support:
pip install cognee[local]
```

---

### Chapter 1 — What Problem Cognee Solves

#### 1.1 The Stateless Agent Problem

LLMs have no memory between calls. Every conversation turn, every API request, starts from a blank slate. Developers work around this by stuffing context into the prompt — chat history, retrieved documents, system instructions. But prompts have token limits, and context windows, while growing, don't solve the fundamental problem: **the LLM has no persistent, structured understanding of your world.**

Consider a customer support agent. Without memory:
- Turn 1: User asks about a refund. The agent retrieves the refund policy from a vector store and answers.
- Turn 2: User asks "How long will it take?" The agent has no idea what "it" refers to unless you re-retrieve context and re-stuff the prompt.
- Turn 3: User mentions a payment outage. The agent cannot connect "refund policy" → "payment gateway outage" → "SLA implications" because those connections exist as relationships between facts, not as semantically similar chunks.

#### 1.2 Why Vector-Only RAG Hits a Wall

Traditional RAG works like this:

```
Document → Chunk → Embed → Vector Store → Retrieve top-K → Feed to LLM
```

This pipeline has a fundamental flaw: **semantic fragmentation**. When you chunk a document, you break the logical connections between facts. A refund policy might be in chunk #7, the payment outage SLA in chunk #142, and the escalation procedure in chunk #89. Vector similarity will retrieve chunks that are semantically similar to the query, but it cannot traverse relationships:

- "Refund policy" is semantically close to "Return procedure" — vector search finds that easily.
- "Refund policy IMPLIES SLA commitment WHICH IS AFFECTED BY Payment outage" — vector search cannot make this multi-hop connection because it doesn't model relationships.

**The result:** Standard RAG achieves ~60% accuracy on multi-hop reasoning tasks. The LLM gets fragments of related text but must reconstruct the logical chain itself, with no structural scaffolding to guide it.

#### 1.3 Cognee's Elevator Pitch

Cognee is a **persistent, relationship-aware memory engine** for AI agents. It:

1. **Ingests** data from 30+ sources (PDFs, databases, Slack, images, audio, APIs)
2. **Builds a knowledge graph** — extracting entities and their relationships using LLMs
3. **Stores** the graph alongside vector embeddings and relational metadata
4. **Retrieves** using hybrid search: graph traversal for relationships + vector similarity for semantics
5. **Evolves** over time — strengthening, weakening, or invalidating facts as new information arrives

Instead of asking "which chunks are similar to this query?", Cognee asks "which subgraph of knowledge answers this question?"

---

### Chapter 2 — Cognee vs RAG vs GraphRAG: Architectural Positioning

#### 2.1 The Spectrum of Memory Systems

AI memory systems exist on a spectrum from simple to sophisticated:

```
Simple Retrieval  ←——————————————————————————→  Structured Memory
     │                                                    │
  Vector RAG         GraphRAG         Graphiti        Cognee
  (semantic only)    (communities)    (temporal KG)   (poly-store KG)
```

**Vector RAG** (basic): Chunk → embed → retrieve. Flat, stateless, no relationships. ~60% accuracy on multi-hop. Best for: simple Q&A over documentation.

**Microsoft GraphRAG**: Adds community detection on top of entities. Summarizes clusters of related entities, then retrieves summaries + raw chunks. Better at global summarization ("what are the main themes?") than Cognee, but less suited to targeted multi-hop queries. No session memory, no multi-tenancy, no self-improvement.

**Graphiti (Zep)**: Episode-based temporal knowledge graph. Every fact carries `valid_from`/`valid_to` timestamps. Excellent for "what was true in January?" audit-trail queries. But: requires managing Neo4j/FalkorDB, no multimodal ingestion, no data connectors beyond episode ingest. Scored 63.8% on LongMemEval (GPT-4o).

**Cognee**: Poly-store architecture (relational + vector + graph). 30+ data connectors, multimodal ingestion, session-aware memory, self-improving skills, multi-tenancy. ~90% accuracy on tuned HotPotQA. Best for: extracting structured knowledge from diverse corpora and serving it to agents.

#### 2.2 The Three-Tier Comparison

| Capability | Vector RAG | MS GraphRAG | Graphiti | Cognee |
|---|---|---|---|---|
| Retrieval method | Vector similarity | Community summaries + chunks | Graph traversal + time | Graph traversal + vectors + metadata |
| Multi-hop reasoning | ❌ Fails | ⚠️ Partial (summaries) | ✅ Temporal multi-hop | ✅ Strong (hybrid) |
| Persistent memory | ❌ Per-query only | ❌ Per-index build | ✅ Episode-based | ✅ Evolving graph |
| Data source breadth | ✅ Any text | ⚠️ Text only | ❌ Conversation only | ✅ 30+ formats |
| Accuracy ceiling | ~60% | ~70% | ~74% (untuned) | ~90% (tuned) |

#### 2.3 Decision Flowchart: Should I Use Cognee?

```
Are you just doing simple semantic search over docs?
  YES → Use basic RAG (LangChain/LlamaIndex). Cognee is overkill.
  NO ↓

Do you need to connect facts across multiple documents/hops?
  NO → RAG is still fine.
  YES ↓

Do you need temporal reasoning ("what changed between Q1 and Q2?")?
  YES → Consider Graphiti. Cognee's temporal support is weaker.
  NO ↓

Do you need to ingest diverse sources (PDFs, Slack, images, databases)?
  YES → Use Cognee. This is its core strength.
  NO ↓

Do you need persistent, evolving agent memory across sessions?
  YES → Use Cognee. The V2 Memory API was designed for this.
  NO → RAG + a session cache may suffice.
```

---

## PART 1: CORE CONCEPTS & ARCHITECTURE

### Chapter 3 — The ECL Pipeline Deep Dive

Cognee replaces the traditional ETL (Extract-Transform-Load) paradigm with **ECL: Extract → Cognify → Load**. The key difference: in ETL, the transform is deterministic code. In ECL, the transform is an LLM-powered cognitive process.

#### 3.1 Phase 1: Extract

The Extract phase brings data into Cognee's internal representation. It handles:

- **Format detection and parsing**: 30+ adapters for PDF, DOCX, PPTX, Markdown, CSV, JSON, images (OCR/vision), audio (ASR), code files, Slack exports, Notion pages, URLs, S3 objects, GitHub repos, and databases (via DLT).
- **Content hashing**: Each document is hashed to enable incremental processing — only new or changed files go through the expensive Cognify phase on subsequent runs.
- **Metadata extraction**: File names, paths, timestamps, MIME types, and custom metadata are preserved.
- **Dataset grouping**: Data is organized into named datasets for scoped queries.

```python
# Multiple ingestion patterns
await cognee.add("Raw text string")                         # String
await cognee.add("path/to/file.pdf")                        # File path
await cognee.add("https://docs.example.com/page")           # URL
await cognee.add("s3://bucket/key")                         # S3 object
await cognee.add("gh:owner/repo:path/to/file")              # GitHub file
await cognee.add(data_list, dataset_name="my_dataset")      # Named dataset
```

#### 3.2 Phase 2: Cognify

This is the heart of Cognee. The Cognify phase runs a pipeline of tasks:

```
Raw Data
  │
  ▼
[1. Classification] ──→ Determine data type and route to appropriate handlers
  │
  ▼
[2. Chunking] ──→ Split into semantic units (paragraph, sentence, fixed-size)
  │
  ▼
[3. Embedding] ──→ Generate vector embeddings for each chunk via configured embedder
  │
  ▼
[4. Entity Extraction] ──→ LLM identifies entities (people, orgs, concepts, etc.)
  │                          using Instructor/BAML for structured JSON output
  │
  ▼
[5. Relationship Extraction] ──→ LLM identifies edges: "belongs_to", "causes",
  │                               "references", "depends_on", temporal, causal, etc.
  │
  ▼
[6. Graph Construction] ──→ Build nodes (entities) and edges (relationships)
  │                          in the knowledge graph with provenance and confidence
  │
  ▼
[7. Summarization] ──→ Generate concise summaries for nodes and subgraphs
```

**Incremental processing:** Cognee tracks which documents have been processed. On re-running `cognify()`, only new or modified documents pass through the pipeline. This is critical for production — you don't re-process a 10 GB corpus every time you add a paragraph.

**Concurrency:** Pipeline tasks use `asyncio.Semaphore` to control concurrent LLM calls. Default is 10 concurrent requests; tune with `COGNEE_CONCURRENCY` env var.

#### 3.3 Phase 3: Load

The Load phase writes to three stores simultaneously:

| Store | Default (Dev) | Production | What's Stored |
|---|---|---|---|
| Relational | SQLite | PostgreSQL | Documents, chunks, metadata, provenance, permissions |
| Vector | LanceDB | Qdrant / Pinecone / Weaviate | Embeddings for chunks, summaries, and nodes |
| Graph | KuzuDB | Neo4j / FalkorDB | Nodes (entities), edges (relationships), properties |

This triple-write is the foundation of Cognee's hybrid retrieval. A query can combine:
1. **Graph traversal** — follow edges to find connected entities ("all suppliers of components in products affected by tariff X")
2. **Vector similarity** — find semantically similar content ("documents about supply chain disruption")
3. **Metadata filtering** — scope by date, dataset, permissions, tags

#### 3.4 Example 1: Hello Cognee

See `cognee_examples/01_hello_cognee.py`

```python
import asyncio
import cognee
import os

async def main():
    # Configure your LLM (OpenAI, Anthropic, Ollama, etc.)
    # Set LLM_API_KEY in environment or pass directly

    # Step 1: Add data
    await cognee.add("""
    Natural Language Processing (NLP) is a subfield of artificial intelligence
    focused on the interaction between computers and human language. Deep learning
    models like transformers, introduced in the 2017 paper "Attention Is All You
    Need" by Vaswani et al., revolutionized NLP by enabling parallel processing
    of sequential data. BERT, developed by Google, uses bidirectional attention
    to understand context from both directions simultaneously.
    """)

    # Step 2: Cognify — build the knowledge graph
    await cognee.cognify()

    # Step 3: Search — hybrid graph + vector retrieval
    results = await cognee.search("What is the relationship between transformers and BERT?")

    print("Search results:")
    for i, result in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

**What's happening under the hood:** The text is chunked, embedded, and then an LLM extracts entities like `Natural Language Processing`, `transformers`, `BERT`, `Google`, `Vaswani et al.` and relationships like `BERT -[uses]-> transformers`, `BERT -[developed_by]-> Google`, `transformers -[introduced_in]-> "Attention Is All You Need"`. These are loaded into the graph and vector stores. The search then traverses the graph to find the connection path between "transformers" and "BERT."

---

### Chapter 4 — The Poly-Store Architecture

#### 4.1 Why Three Databases?

Cognee's architecture uses three specialized databases because no single database type excels at all three access patterns:

| Access Pattern | Best DB Type | Why |
|---|---|---|
| **Metadata lookups** ("get all chunks from dataset X, filtered by date") | Relational (SQL) | Indexed columns, JOINs, filtering, ACID |
| **Semantic similarity** ("find content similar to this query") | Vector | Approximate nearest neighbor (ANN) search over high-dimensional embeddings |
| **Relationship traversal** ("find all entities connected to X through path Y") | Graph | Native graph traversal algorithms, edge-first storage, relationship-centric queries |

**Could you use just Postgres + pgvector?** For small projects, yes. But:
- pgvector's ANN performance degrades past ~1M vectors compared to purpose-built vector DBs like Qdrant or Pinecone
- SQL is poor at recursive graph traversal (CTEs work for depth 2-3, but multi-hop traversals get exponential)
- You lose graph-specific features: centrality algorithms, community detection, path enumeration

Cognee's bet: use the right tool for each job, and keep them in sync.

#### 4.2 Storage Backend Options

| Layer | Development | Production | Enterprise |
|---|---|---|---|
| Relational | SQLite | PostgreSQL | PostgreSQL + read replicas |
| Vector | LanceDB (embedded) | Qdrant | Pinecone / Weaviate |
| Graph | KuzuDB (embedded) | Neo4j | FalkorDB (Redis-based) |

**Configuration:**
```python
import cognee

# Configure backends
cognee.config.set({
    "graph_database_provider": "neo4j",       # kuzu, neo4j, networkx, falkordb
    "graph_database_url": "bolt://localhost:7687",
    "graph_database_username": "neo4j",
    "graph_database_password": "password",

    "vector_database_provider": "qdrant",     # lancedb, qdrant, weaviate, chroma
    "vector_database_url": "http://localhost:6333",

    "relational_database_provider": "postgresql",
    "relational_database_url": "postgresql://user:pass@localhost:5432/cognee",
})
```

#### 4.3 Consistency Model

Cognee uses **eventual consistency** across the three stores. When you `cognify()`:

1. All writes go to the relational store first (source of truth for document/chunk metadata)
2. Vector embeddings and graph nodes are written in parallel
3. If a write fails, it's retried

There is no distributed transaction across stores. This is a deliberate trade-off: ACID across three heterogeneous databases would require a two-phase commit protocol, doubling write latency. Instead, Cognee accepts that for a brief window (milliseconds to seconds), the three stores may disagree. In practice, this is acceptable because:
- Writes are batched (you `cognify()` a dataset, not individual documents)
- Reads are scoped to named datasets, so partial writes to a dataset-in-progress are invisible until the full dataset is committed
- The relational store acts as the arbiter of what's been processed

#### 4.4 Example 2: Exploring the Stores

See `cognee_examples/02_exploring_stores.py` — this example shows how to inspect what gets written to each store after cognify.

---

### Chapter 5 — DataPoints & Ontology

#### 5.1 DataPoints: The Atomic Unit of Memory

A **DataPoint** is a Pydantic model that defines a typed node or edge in the knowledge graph. Every DataPoint gets:
- An auto-assigned **UUID**
- A **version number** and **timestamp**
- Field-level indexing metadata via `index_fields`

```python
from cognee.modules.data.models import DataPoint
from pydantic import Field
from uuid import UUID
from datetime import datetime

class Person(DataPoint):
    name: str = Field(..., index_fields=["name"])
    role: str = Field(default="unknown")
    organization: str = Field(default="unknown")
    # Auto-inherited: id (UUID), created_at, updated_at, version

class Company(DataPoint):
    name: str = Field(..., index_fields=["name"])
    industry: str = Field(default="unknown")
    founded: int | None = None
    headquarters: str | None = None

class Employment(DataPoint):
    """An edge connecting Person → Company"""
    person_id: UUID
    company_id: UUID
    start_date: datetime | None = None
    end_date: datetime | None = None
    title: str = Field(default="employee")
```

**`index_fields`** tells Cognee which fields to generate targeted embeddings for. For `Person`, embeddings are generated for the `name` field specifically, enabling precise entity resolution ("is 'John Smith' in document A the same person as 'J. Smith' in document B?").

#### 5.2 Implicit Ontology Through Typed Fields

By defining DataPoints with explicit field types and relationships, you create an **implicit ontology**. This is different from explicit OWL/RDF ontologies (which Cognee also supports) — it's "schema-on-write" rather than "schema-first." Your Pydantic models define:

- **What entities exist** (Person, Company, Product, Event, etc.)
- **What properties they have** (name, date, industry, etc.)
- **How they relate** (Employment edge connects Person to Company)

The LLM extraction step uses these models as its target schema — it's told "extract entities matching these types" and "identify relationships matching these edge types."

#### 5.3 Recursive DataPoints

DataPoints can nest:

```python
class Address(DataPoint):
    street: str
    city: str
    country: str

class Company(DataPoint):
    name: str
    headquarters: Address  # Nested DataPoint — creates a sub-node
```

During cognify, nested DataPoints are recursively unpacked. The `Company` node gets an edge to its `Address` sub-node. This enables queries like "find all companies headquartered in Berlin" without flattening the address into the company node.

#### 5.4 RDF/OWL Ontology Support

For domains with existing formal ontologies (finance, life sciences, legal), Cognee can ingest OWL files:

```python
await cognee.add("path/to/ontology.owl")
await cognee.cognify()
```

The ontology enriches the knowledge graph with predefined entity types and relationships, improving extraction accuracy for domain-specific terminology.

#### 5.5 Example 3: Custom DataPoints

See `cognee_examples/03_datapoints_ontology.py` — defines a domain ontology for a tech company and demonstrates precise entity extraction.

---

### Chapter 6 — The Cognify Pipeline Tasks (In Detail)

#### 6.1 The Task System

Every step in the Cognify phase is a **Task** — a modular processing unit with defined inputs, outputs, and configuration. Tasks are composed into **Pipelines**.

```python
from cognee.tasks import Task
from cognee.pipelines import Pipeline

# Built-in tasks (partial list):
# - IngestionTask: parse and normalize raw data
# - TextChunkingTask: split into semantic chunks
# - EmbeddingTask: generate vector embeddings
# - EntityExtractionTask: LLM-based entity identification
# - RelationshipExtractionTask: LLM-based relationship identification
# - GraphConstructionTask: build nodes and edges
# - SummarizationTask: generate summaries for nodes and chunks
# - DeduplicationTask: merge identical entities
```

#### 6.2 Built-in Task Details

**TextChunkingTask:**
- Strategies: paragraph-based, sentence-based, fixed-size (1024 tokens default), or `RecursiveCharacterTextSplitter` (LangChain-compatible)
- Overlap: configurable (default 0 for paragraph, 50 tokens for fixed-size)
- Metadata preservation: each chunk carries source document ID, position, and page number

**EntityExtractionTask:**
- Uses LLM with structured output (Instructor library with BAML/openai function-calling)
- Prompt includes the DataPoint type definitions as the target schema
- Batch processing with configurable chunk size
- Returns typed Pydantic objects, not raw JSON

**RelationshipExtractionTask:**
- Second LLM pass over extracted entities
- Identifies edges between entities within and across chunks
- Edge types: `belongs_to`, `references`, `causes`, `depends_on`, `is_a`, `part_of`, `temporal`, `causal`, and custom types
- Confidence scores assigned to each relationship

**GraphConstructionTask:**
- Creates nodes from entities, edges from relationships
- Deduplicates: same entity extracted from multiple chunks → single node with multiple provenance references
- Assigns UUIDs, timestamps, and version numbers
- Links to source documents and chunks

**DeduplicationTask:**
- Post-construction merge of likely-duplicate entities using embedding similarity + field matching
- Configurable threshold (default: 0.85 cosine similarity)
- Merges properties from duplicates into the surviving node

#### 6.3 Custom Tasks

You can create custom tasks and insert them into the pipeline:

```python
from cognee.tasks import Task, register_task

@register_task
async def extract_acronyms(chunks: list, llm_client):
    """Custom task: extract acronyms and their expansions."""
    acronyms = {}
    for chunk in chunks:
        # Custom extraction logic
        prompt = f"Extract all acronyms and their full forms from: {chunk.text}"
        response = await llm_client.complete(prompt)
        # Parse and accumulate
        for acronym, expansion in parse_acronyms(response):
            acronyms[acronym] = expansion
    return acronyms

# Use in a pipeline
pipeline = Pipeline([
    Task(extract_acronyms),
    # ... other tasks
])
```

#### 6.4 Concurrency Model

Cognee uses `asyncio.Semaphore` to limit concurrent LLM calls:

```python
# Default: 10 concurrent LLM calls
# Override via env var:
# export COGNEE_CONCURRENCY=20
```

This is important because:
- LLM APIs have rate limits (OpenAI: 500 RPM for GPT-4o on Tier 1)
- Each cognify phase can trigger hundreds of LLM calls (entity extraction per chunk, relationship extraction per batch, summarization per node)
- Without a semaphore, you'd hit rate limits and get 429 errors
- With too low a value, processing time increases linearly

#### 6.5 Example 4: Custom Pipeline

See `cognee_examples/04_custom_pipeline.py` — builds a pipeline with a custom domain-specific extraction task.

---

## PART 2: API DEEP DIVE

### Chapter 7 — V1 Pipeline API (`add` / `cognify` / `search`)

#### 7.1 Complete Function Signatures

```python
async def add(
    data: str | list[str] | Path | DataObject,
    dataset_name: str | None = None,
    user_id: str | None = None,
    metadata: dict | None = None,
) -> list[DataObject]:
    """Ingest data into Cognee.

    Args:
        data: Text string, file path, URL, S3 URI, GitHub ref, or DataObject
        dataset_name: Optional dataset name for scoped queries
        user_id: Optional user/tenant identifier for multi-tenancy
        metadata: Optional dict of custom metadata to attach

    Returns:
        List of DataObject instances representing the ingested data
    """

async def cognify(
    datasets: list[str] | None = None,
    user_id: str | None = None,
) -> None:
    """Transform ingested data into a knowledge graph.

    Args:
        datasets: Optional list of dataset names to process (None = all unprocessed)
        user_id: Optional user/tenant scope
    """

async def search(
    query: str,
    query_type: SearchType = SearchType.GRAPH_COMPLETION,
    dataset: str | None = None,
    user_id: str | None = None,
    top_k: int = 10,
    filters: dict | None = None,
) -> list[SearchResult]:
    """Query the knowledge graph.

    Args:
        query: Natural language question
        query_type: SearchType enum controlling retrieval strategy
        dataset: Optional dataset name to scope search
        user_id: Optional user/tenant scope
        top_k: Number of results to return
        filters: Optional metadata filters (tags, dates, etc.)

    Returns:
        List of SearchResult objects with content and source citations
    """
```

#### 7.2 SearchType Strategies

| SearchType | Behavior | Best For |
|---|---|---|
| `GRAPH_COMPLETION` | Graph traversal + vector search + LLM synthesis | Multi-hop questions, relationship queries |
| `CHUNKS` | Pure vector similarity over chunks | "Find me the exact paragraph about X" |
| `INSIGHTS` | Summarized insights extracted during cognify | High-level thematic questions |
| `SUMMARY` | Document and node summaries | "Summarize everything about topic Y" |
| `GRAPH` | Pure graph traversal without LLM synthesis | Programmatic graph queries |

#### 7.3 Data Source Patterns

```python
# From files
await cognee.add("reports/q4_2025.pdf")
await cognee.add(["doc1.pdf", "doc2.pdf", "doc3.docx"])

# From URLs
await cognee.add("https://docs.example.com/api-reference")

# From S3
await cognee.add("s3://my-bucket/path/to/docs/*.pdf")

# From GitHub
await cognee.add("gh:topoteretes/cognee:README.md")

# With custom metadata
await cognee.add(
    "confidential_report.pdf",
    dataset_name="legal",
    metadata={"classification": "confidential", "owner": "legal-team"}
)
```

#### 7.4 Example 5: V1 API Workflow

See `cognee_examples/05_v1_api_workflow.py` — full pipeline with multiple data sources, dataset scoping, and different search types.

---

### Chapter 8 — V2 Memory API (`remember` / `recall` / `improve` / `forget`)

#### 8.1 The Shift from Pipeline to Agent Memory

The V1 API (`add` → `cognify` → `search`) is a **batch processing pipeline**. It assumes you have a corpus of documents and want to build a knowledge graph from them. This is great for knowledge base construction but awkward for agent interactions.

The V2 API (`remember` / `recall` / `improve` / `forget`) is designed for **agent-centric memory**. It treats memory as a living thing — facts arrive through conversation, some are ephemeral, some get promoted to permanent storage, and some eventually become stale.

```python
# V1: batch pipeline thinking
await cognee.add(documents)
await cognee.cognify()
results = await cognee.search(question)

# V2: agent memory thinking
await cognee.remember("The user's name is Alice and she prefers dark mode.")
await cognee.remember("Alice reported bug #4521 about the login page.", session_id="conv_123")
results = await cognee.recall("What do I know about Alice's preferences?")

# Later, when the bug is resolved:
await cognee.improve("Bug #4521 was resolved in PR #7820.", session_id="conv_123")
# Or promote session memory to permanent:
await cognee.improve(session_id="conv_123", promote_to_permanent=True)
```

#### 8.2 Session-Aware Memory

The `session_id` parameter is the key innovation. It creates two tiers of memory:

| Tier | Lifetime | Storage | Example |
|---|---|---|---|
| **Working memory** | Single session | Redis cache (optional) | Current conversation context |
| **Short-term memory** | Tied to `session_id` | Session store | Facts from recent interactions |
| **Long-term memory** | Permanent | Knowledge graph + vectors | Facts promoted from sessions |

When you `recall(query, session_id="conv_123")`, Cognee searches both the permanent knowledge graph AND the session's short-term memory, merging results. This means the agent can reference facts from the current conversation alongside permanent knowledge.

#### 8.3 Session Promotion

The `improve()` method can promote session facts to permanent memory:

```python
# After a support conversation where useful knowledge emerged:
await cognee.improve(
    session_id="conv_123",
    promote_to_permanent=True,
    feedback="User confirmed this solution worked for the login bug."
)
```

The promotion process:
1. Extracts entities and relationships from the session's accumulated facts
2. Merges them into the permanent knowledge graph (deduplication)
3. Adds provenance linking back to the session
4. Applies feedback-based weighting (facts with positive feedback get higher confidence)

#### 8.4 Forgetting

```python
# Scoped deletion:
await cognee.forget(session_id="conv_123")              # Forget a session
await cognee.forget(dataset="experimental_data")         # Forget a dataset
await cognee.forget(user_id="user_456")                  # Forget all data for a user

# Time-based:
await cognee.forget(older_than=datetime(2025, 1, 1))    # Forget old data
```

Under the hood, `forget()` orchestrates deletion across all three stores. The relational store tracks what's been deleted (soft delete by default, with a trash/undo mechanism in v0.5.7+).

#### 8.5 Example 6: Agent Memory with Sessions

See `cognee_examples/06_v2_memory_api.py` — simulates a multi-turn agent conversation with session memory and promotion.

---

### Chapter 9 — REST API & MCP Server

#### 9.1 REST API Endpoints

Cognee ships with a FastAPI server (`cognee-cli -ui` or standalone):

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/add` | Ingest data (files, URLs, text) |
| POST | `/api/v1/cognify` | Trigger knowledge graph construction |
| GET/POST | `/api/v1/search` | Query the knowledge graph |
| GET | `/api/v1/datasets` | List datasets |
| DELETE | `/api/v1/datasets/{name}` | Delete a dataset |
| POST | `/api/v1/remember` | V2 memory: store a fact |
| POST | `/api/v1/recall` | V2 memory: retrieve facts |
| POST | `/api/v1/improve` | V2 memory: enrich/evolve |
| DELETE | `/api/v1/delete` | Delete specific data |
| POST | `/api/v1/permissions` | Manage access control |

**Authentication:** Bearer token (JWT) via `/api/v1/auth/login` or `X-Api-Key` header.

**Example request:**
```bash
curl -X POST http://localhost:8000/api/v1/add \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"data": "Cognee is an AI memory engine.", "dataset_name": "docs"}'

curl -X POST http://localhost:8000/api/v1/cognify \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"datasets": ["docs"]}'

curl "http://localhost:8000/api/v1/search?query=What%20is%20Cognee?" \
  -H "Authorization: Bearer $TOKEN"
```

#### 9.2 MCP Server

The Model Context Protocol (MCP) server exposes Cognee as tools for AI assistants (Claude Desktop, Cursor, Cline, etc.):

**Setup (Claude Desktop):**
```json
{
  "mcpServers": {
    "cognee": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "cognee/cognee-mcp:main"]
    }
  }
}
```

**Available MCP tools:**
- `add` — ingest data
- `cognify` — build knowledge graph
- `search` — hybrid query (with `SearchType`)
- `save_interaction` — record agent interaction for learning
- `get_skill_context` — retrieve skill-related context (v0.5.4rc1+)
- `load_skill` / `execute_skill` / `observe_skill_run` / `promote_skill_runs` — skills management

#### 9.3 TypeScript Client

```typescript
import { CogneeConfig, addData, cognify, search, SearchType } from '@lineai/cognee-api';

const config: CogneeConfig = {
  baseUrl: 'http://localhost:8000',
  apiKey: process.env.COGNEE_API_KEY,
};

await addData(config, { data: 'Your text here', dataset_name: 'my_data' });
await cognify(config, { datasets: ['my_data'] });
const results = await search(config, 'Your question?', SearchType.GRAPH_COMPLETION);
```

#### 9.4 Example 7: REST API Client

See `cognee_examples/07_rest_api_client.py` — demonstrates calling Cognee via HTTP from Python (or any language).

---

### Chapter 10 — CLI & UI

#### 10.1 CLI Commands

```bash
# Ingest data
cognee-cli add "path/to/document.pdf"
cognee-cli add "https://example.com/page"

# Build knowledge graph
cognee-cli cognify
cognee-cli cognify --datasets my_dataset

# Search
cognee-cli search "What is the refund policy?"
cognee-cli search --type CHUNKS "Find exact text about..."

# Launch full UI (backend + frontend + MCP)
cognee-cli -ui

# Skills management (v0.5.4rc1+)
cognee-cli skills ingest --path ./my_skill/
cognee-cli skills list
cognee-cli skills execute --name my_skill
```

#### 10.2 Graph Visualization

```python
import cognee

# After cognify, generate an interactive graph visualization
await cognee.visualize_graph(
    output_path="graph.html",
    dataset="my_dataset",
    max_nodes=200,               # Limit for performance
    include_edges=True
)
```

The generated HTML uses D3.js for an interactive force-directed graph where you can:
- Drag nodes to explore connections
- Click nodes to see properties
- Zoom and pan
- Search/highlight specific entities
- Filter by node type or relationship type

#### 10.3 Example 8: CLI & UI Workflows

See `cognee_examples/08_cli_and_ui.md` — reference of common CLI workflows and UI features.

---

## PART 3: ADVANCED FEATURES

### Chapter 11 — Multimodal Ingestion

Cognee supports six data modalities through a unified pipeline:

| Modality | Input Formats | Processing |
|---|---|---|
| **Text** | Plain text, Markdown, HTML | Direct parsing |
| **Documents** | PDF, DOCX, PPTX, ODT | Text extraction + layout preservation |
| **Images** | PNG, JPEG, TIFF, GIF | OCR (Tesseract) + vision model description |
| **Audio** | MP3, WAV, FLAC, M4A | ASR (Whisper) → text transcript |
| **Video** | MP4, AVI, MOV | Frame extraction → vision + audio track → ASR |
| **Structured** | CSV, JSON, XML, SQL tables | Schema-aware parsing |

#### 11.1 Cross-Modal Knowledge Representation

When Cognee processes multimodal data, it links information across modalities through shared entity IDs. For example, if you ingest:
- A PDF report mentioning "Project Falcon"
- An image of a product labeled "Falcon v2"
- An audio recording of a meeting discussing "the Falcon launch"

Cognee extracts entities from each modality independently, then the deduplication task links them — creating a unified `Project Falcon` node connected to all three sources. A subsequent query about "Falcon" retrieves the combined knowledge.

#### 11.2 Configuration

```python
# Configure vision model for image processing
cognee.config.set({
    "vision_model": "gpt-4o",          # or "claude-opus-4-7"
    "ocr_engine": "tesseract",          # or "azure-vision"
    "asr_model": "whisper-1",           # or local "whisper-large-v3"
})
```

#### 11.3 Example 9: Multimodal Pipeline

See `cognee_examples/09_multimodal.py` — ingests a mix of PDFs, images, and audio, demonstrating cross-modal entity linking.

---

### Chapter 12 — DLT (Data Loading Tool) Integration

#### 12.1 Direct Database Ingestion

Cognee integrates with [dlt](https://dlthub.com/) (data load tool) for direct ingestion from databases:

```python
import cognee
from cognee.modules.ingestion.dlt import DLTIngestion

# Ingest directly from PostgreSQL
await cognee.add(
    DLTIngestion(
        source="postgres",
        credentials={
            "host": "localhost",
            "database": "my_db",
            "username": "user",
            "password": "pass",
        },
        query="SELECT * FROM products JOIN categories ON products.category_id = categories.id"
    ),
    dataset_name="product_catalog"
)

await cognee.cognify()
```

**Supported DLT sources:**
- PostgreSQL, MySQL, BigQuery, Snowflake, Redshift
- REST APIs (with pagination, auth)
- S3, GCS, Azure Blob Storage
- Notion, Slack, Google Drive

#### 12.2 SQL Safety & FK Extraction

When ingesting from relational databases:
- **Read-only queries**: Cognee wraps DLT queries in read-only transactions
- **Foreign key extraction**: Table relationships become graph edges (e.g., `Product -[belongs_to]-> Category`)
- **Schema mapping**: Column types map to DataPoint field types

#### 12.3 Example 10: DLT Ingestion

See `cognee_examples/10_dlt_ingestion.py` — pulls product + category data from a SQLite database and builds a knowledge graph from foreign key relationships.

---

### Chapter 13 — Graph Visualization & Exploration

#### 13.1 Interactive Visualization

```python
await cognee.visualize_graph(
    output_path="my_graph.html",
    dataset="my_dataset",
    max_nodes=500,
    include_edges=True,
    node_color_by="type",        # Color nodes by entity type
    edge_color_by="relationship", # Color edges by relationship type
    layout="force_directed",      # or "hierarchical", "radial"
)
```

#### 13.2 NodeSet-Based Subgraph Scoping

NodeSets are labels that group related facts:

```python
# During ingestion
await cognee.add(sales_data, dataset="company", nodeset="sales")
await cognee.add(hr_data, dataset="company", nodeset="hr")

# Visualize only the sales subgraph
await cognee.visualize_graph(dataset="company", nodeset_filter=["sales"])
```

#### 13.3 Example 11: Graph Visualization

See `cognee_examples/11_graph_viz.py` — generates and explores graph visualizations with NodeSet filtering.

---

### Chapter 14 — Permissions & Multi-Tenancy

#### 14.1 Role-Based Access Control

Cognee implements RBAC at the dataset level:

| Role | Permissions |
|---|---|
| **Reader** | Can search within datasets they have access to |
| **Writer** | Can add data and trigger cognify on allowed datasets |
| **Admin** | Can manage permissions, delete data, configure pipelines |
| **Owner** | Full control over their own data; can share with others |

```python
# Grant access
await cognee.permissions.grant(
    user_id="user_789",
    dataset="legal_docs",
    roles=["reader"]
)

# Revoke
await cognee.permissions.revoke(
    user_id="user_789",
    dataset="legal_docs"
)
```

#### 14.2 Multi-Tenant Isolation

Each user/tenant gets isolated data access. Queries are automatically scoped:

```python
# User A's data is invisible to User B
await cognee.add(data, dataset="private", user_id="user_a")
await cognee.search(query, user_id="user_a")  # ✅ Sees their data
await cognee.search(query, user_id="user_b")  # ❌ Sees nothing (no access)
```

The user_id is propagated through all three stores — relational WHERE clauses, vector metadata filters, and graph node properties all carry the user_id for enforcement.

#### 14.3 Example 12: Multi-Tenant Setup

See `cognee_examples/12_permissions.py` — sets up isolated workspaces for two teams sharing the same Cognee instance.

---

### Chapter 15 — The Skills System (`cognee-skills`)

#### 15.1 Self-Improving Skills

Introduced in v0.5.4rc1, the skills system allows Cognee to observe its own performance and self-correct. A **skill** is a packaged capability with six lifecycle phases:

```
[1. Ingest] ──→ [2. Route] ──→ [3. Execute] ──→ [4. Observe] ──→ [5. Evaluate] ──→ [6. Amend]
                                                       │
                                                       └──→ feedback loop: amend → re-execute
```

1. **Ingest**: Auto-parse skill definition from 38+ formats
2. **Route**: Skill orchestration engine matches requests to skills
3. **Execute**: Run the skill against data
4. **Observe**: Record interaction logs and outputs
5. **Evaluate**: LLM-based scoring on 12 metrics (accuracy, response speed, relevance, consistency, etc.)
6. **Amend**: If score below threshold, auto-generate corrections

#### 15.2 Creating a Custom Skill

```python
from cognee.skills import Skill, SkillConfig

class SummarizationSkill(Skill):
    config = SkillConfig(
        name="legal_summarizer",
        description="Summarizes legal documents with domain-specific accuracy",
        evaluation_metrics=["accuracy", "completeness", "citation_correctness"],
        auto_amend_threshold=0.75  # Auto-correct if score < 0.75
    )

    async def execute(self, input_data: dict) -> dict:
        # Skill implementation
        result = await self.llm.complete(
            prompt=f"Summarize this legal document: {input_data['text']}",
            system="You are a legal document summarizer. Preserve all citations and key dates."
        )
        return {"summary": result}
```

#### 15.3 Skill Orchestration

The orchestration engine can automatically compose skills for complex tasks:

```python
# The engine decomposes this into: intent_analysis → sentiment_detection → recommendation
result = await cognee.skills.execute_composite(
    goals=["classify customer complaint", "suggest resolution"],
    data=complaint_text
)
```

#### 15.4 Example 13: Custom Skill

See `cognee_examples/13_skills.py` — creates a domain-specific extraction skill with automated quality evaluation.

---

### Chapter 16 — Memify: Graph Enrichment & Evolution

#### 16.1 Beyond Cognify

`cognify()` builds the initial knowledge graph. `memify()` enriches it over time without full rebuilds:

```python
await cognee.add(initial_corpus)
await cognee.cognify()

# ... time passes, new data arrives ...

await cognee.add(new_data)
await cognee.memify()  # Incrementally enriches the existing graph
```

#### 16.2 What Memify Does

| Operation | Description |
|---|---|
| **Entity merging** | Find and merge newly extracted entities with existing ones |
| **Relationship strengthening** | Increase confidence for relationships confirmed by multiple sources |
| **Stale node cleanup** | Downgrade or remove nodes with no recent references |
| **Temporal reweighting** | Boost recent facts, decay old ones (configurable decay rate) |
| **Association discovery** | Find indirect connections ("A and B are both connected to C, maybe A and B are related") |

#### 16.3 Memify vs Re-Cognify: When to Use Which

| Scenario | Use |
|---|---|
| Added a few new documents to an existing dataset | `memify()` |
| Added a large new dataset on a new topic | `cognify()` (fresh graph construction) |
| Correcting extraction errors | `memify()` with feedback |
| Changed the DataPoint schema | Re-`cognify()` (schema change requires re-extraction) |
| Periodic maintenance | `memify()` (weekly cron) |

#### 16.4 Example 14: Graph Evolution

See `cognee_examples/14_memify_enrichment.py` — demonstrates graph evolution across multiple time steps with new information arriving incrementally.

---

### Chapter 17 — Observability & Tracing (OpenTelemetry)

#### 17.1 Built-in OTEL Tracing

```python
import cognee

# Enable tracing
cognee.enable_tracing()  # Starts OTEL exporter

await cognee.add(data)
await cognee.cognify()

# Retrieve traces
last_trace = cognee.get_last_trace()
all_traces = cognee.get_all_traces()

print(f"Pipeline duration: {last_trace['duration_ms']}ms")
print(f"LLM calls: {last_trace['llm_call_count']}")
print(f"Entities extracted: {last_trace['entity_count']}")
```

Each trace captures:
- **Span hierarchy**: `cognify` → `entity_extraction` → `llm_call` (with timing)
- **LLM metrics**: prompt tokens, completion tokens, latency, model used
- **Error traces**: stack traces for failed extractions, rate limit hits
- **Data metrics**: documents processed, chunks created, entities extracted, relationships found

#### 17.2 Exporting to Observability Platforms

```python
# Export to any OTEL-compatible backend
cognee.config.set({
    "otel_exporter_endpoint": "https://api.honeycomb.io/v1/traces",
    "otel_exporter_headers": {"x-honeycomb-team": "your-api-key"},
})
```

Supported exporters: Jaeger, Zipkin, Honeycomb, Datadog, Grafana Tempo, any OTLP endpoint.

#### 17.3 Example 15: Observability

See `cognee_examples/15_observability.py` — traces a full pipeline run and analyzes the trace data.

---

## PART 4: REAL-WORLD USE CASES

### Chapter 18 — Customer Support Knowledge Base

**Scenario:** A SaaS company wants an AI agent that can answer support questions by reasoning across FAQs, product documentation, past support tickets, and incident postmortems.

**What Cognee enables:**
- Multi-hop: "A customer on the Pro plan reports a payment failure during checkout. What SLA applies, and which team handles this?"
- Relationship traversal: `Payment Failure` → `caused_by` → `Payment Gateway Outage` → `covered_by` → `SLA Section 4.2` → `escalated_to` → `Payments Team`

**Implementation:** See `cognee_examples/16_support_kb.py` — ingests mock support docs, tickets, and incident reports, then demonstrates multi-hop support queries.

---

### Chapter 19 — Legal Document & Compliance Analysis

**Scenario:** A legal team needs to track obligations across hundreds of contracts, regulations, and policies.

**What Cognee enables:**
- Entity extraction: parties, effective dates, termination clauses, governing law, liability caps
- Cross-reference: "Show all clauses in vendor contracts that conflict with GDPR Article 28"
- Temporal tracking: "Which contracts expire in Q3 2026?"

**Implementation:** See `cognee_examples/17_legal_compliance.py` — simulates contract analysis with clause-level extraction and cross-referencing.

---

### Chapter 20 — Codebase Understanding & Architecture Analysis

**Scenario:** A development team wants an AI assistant that understands their codebase's structure, dependencies, and architecture.

**What Cognee enables:**
- Ingest source code with AST-based parsing
- Build a code KG: modules → classes → functions → parameters → dependencies
- Query: "What breaks if I change the signature of `authenticate()`?"
- Query: "Show me all callers of `process_payment()` across the codebase"

**Implementation:** See `cognee_examples/18_code_analysis.py` — ingests a sample Python project, builds a code knowledge graph, and demonstrates architecture queries.

---

### Chapter 21 — Research Assistant & Literature Review

**Scenario:** A researcher needs to survey papers, identify methods, track claims, and find contradictions.

**What Cognee enables:**
- Ingest PDFs from arXiv, extract: methods, findings, datasets, baselines, citations
- Build research KG: Paper → [proposes] → Method → [evaluated_on] → Dataset → [achieves] → Score
- Query: "What methods exist for X, and which papers disagree about effectiveness?"
- Query: "Trace the evolution of method Y from its origin paper to current variants"

**Implementation:** See `cognee_examples/19_research_assistant.py` — ingests mock research abstracts and demonstrates literature graph queries.

---

### Chapter 22 — Financial Intelligence & Market Analysis

**Scenario:** An analyst needs to track companies, their suppliers, events, and market impacts.

**What Cognee enables:**
- Ingest: earnings reports, news articles, SEC filings
- Extract: companies, execs, products, events, financial metrics
- Multi-hop: "Which suppliers to Apple are exposed to the new tariff on semiconductor imports?"
- Temporal: "How did the supply chain disruption in Taiwan affect stock prices of US tech companies in Q1 2026?"

**Implementation:** See `cognee_examples/20_financial_intel.py` — simulates financial document ingestion with supply chain reasoning.

---

### Chapter 23 — Enterprise HR & Internal Knowledge Management

**Scenario:** An HR department wants intelligent search over employee handbooks, org charts, project docs, and skill matrices.

**What Cognee enables:**
- Ingest: HR docs, org charts, project wikis, training records
- Build KG: Person → [works_on] → Project → [requires] → Skill → [possessed_by] → Person
- Query: "Who in the Berlin office has Kubernetes experience and is not currently on a project?"
- Query: "What's the onboarding checklist for a new backend engineer?"

**Implementation:** See `cognee_examples/21_hr_knowledge.py` — builds an org knowledge graph and demonstrates internal knowledge queries.

---

## PART 5: DEPLOYMENT & PRODUCTION

### Chapter 24 — Local Development & Self-Hosting

#### 24.1 Development Setup

The default stack runs entirely locally with zero external dependencies:

```
pip install cognee
# That's it. SQLite + LanceDB + KuzuDB are embedded.
```

```python
import cognee
import asyncio

async def main():
    await cognee.add("Your data")
    await cognee.cognify()
    results = await cognee.search("Your query")
    print(results)

asyncio.run(main())
```

No Docker, no database servers, no API keys (if using Ollama for local LLM).

#### 24.2 Using Ollama for Fully Local LLMs

```bash
# Install Ollama and pull a model
ollama pull llama3.1:8b

# Set environment
export LLM_PROVIDER=ollama
export LLM_MODEL=llama3.1:8b
export LLM_API_BASE=http://localhost:11434/v1
```

**Critical caveat:** Local models struggle with Cognee's structured output requirements. Models below ~70B parameters frequently fail to produce valid JSON matching the DataPoint schemas. For reliable entity extraction, you typically need:
- A commercial API (OpenAI GPT-4o, Anthropic Claude) with native function-calling / structured output
- Or a very large local model (70B+) with careful prompt engineering

See `cognee_examples/22_local_dev.py` for a working local setup with guidance on model selection.

#### 24.3 Example 22: Local Development

See `cognee_examples/22_local_dev.py` — fully local Cognee setup with Ollama, including structured output workarounds.

---

### Chapter 25 — Production Deployment Strategies

#### 25.1 Docker Compose (Recommended for Small Teams)

```yaml
# docker-compose.yml
version: '3.8'
services:
  cognee-api:
    image: cognee/cognee:latest
    ports: ["8000:8000"]
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
      - GRAPH_DB_PROVIDER=neo4j
      - GRAPH_DB_URL=bolt://neo4j:7687
      - VECTOR_DB_PROVIDER=qdrant
      - VECTOR_DB_URL=http://qdrant:6333
      - RELATIONAL_DB_PROVIDER=postgresql
      - RELATIONAL_DB_URL=postgresql://cognee:pass@postgres:5432/cognee
    depends_on: [neo4j, qdrant, postgres]

  neo4j:
    image: neo4j:5
    environment:
      - NEO4J_AUTH=neo4j/password
    volumes: [neo4j_data:/data]

  qdrant:
    image: qdrant/qdrant:latest
    volumes: [qdrant_data:/qdrant/storage]

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      - POSTGRES_USER=cognee
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=cognee
    volumes: [pg_data:/var/lib/postgresql/data]

volumes:
  neo4j_data:
  qdrant_data:
  pg_data:
```

#### 25.2 Kubernetes with Helm

```bash
helm repo add cognee https://charts.cognee.ai
helm install cognee-prod cognee/cognee \
  --set graphDatabase.provider=neo4j \
  --set vectorDatabase.provider=pinecone \
  --set replicaCount=3 \
  --set autoscaling.enabled=true
```

#### 25.3 Cognee Cloud (Serverless)

For teams that don't want to manage infrastructure:

```python
# Point at Cognee Cloud
cognee.config.set({
    "api_base": "https://api.cognee.ai",
    "api_key": "cognee_sk_..."
})

# Same API, managed infrastructure with auto-scaling
await cognee.add(data)
await cognee.cognify()
```

Free tier: 1 GB data processing + 10,000 API calls/month. Paid: ~$25/month for more capacity.

#### 25.4 Example 23: Production Stack

See `cognee_examples/23_docker_compose/` — complete production Docker Compose setup with health checks and backups.

---

### Chapter 26 — Scaling & Performance Tuning

#### 26.1 Scaling Dimensions

| Dimension | Bottleneck | Solution |
|---|---|---|
| **Write throughput** | LLM rate limits | Distributed pipelines (multiple API keys, parallel containers) |
| **Read latency** | Graph traversal depth | Redis cache for frequent subgraphs |
| **Multi-agent concurrency** | Kuzu file locking | Switch to Neo4j or FalkorDB |
| **Vector search (scale)** | LanceDB local-only | Switch to Qdrant/Pinecone with horizontal scaling |
| **Data volume** | Cognify time | Incremental processing; only cognify new/changed docs |

#### 26.2 Distributed Pipelines

Set `COGNEE_DISTRIBUTED=true` to run cognify across multiple containers:

```bash
# Each container processes a subset of documents
docker run -e COGNEE_DISTRIBUTED=true \
           -e LLM_API_KEY=$LLM_API_KEY \
           cognee/cognee:latest
```

Performance benchmarks:
- **1 GB dataset**: ~30 minutes with 100+ containers (vs. 8.5 hours single-process)
- **100 GB dataset**: hours instead of weeks
- **Cost**: ~81% savings vs. dedicated servers (due to serverless auto-scaling)

#### 26.3 Caching with Redis

```python
cognee.config.set({
    "cache_provider": "redis",
    "cache_url": "redis://localhost:6379",
    "cache_ttl_seconds": 3600,       # Cache subgraphs for 1 hour
    "cache_max_size_mb": 2048,
})
```

Redis caches:
- Frequently accessed subgraphs (avoid repeated graph traversals)
- Session memory (faster than hitting the graph DB for recent facts)
- Embedding results (avoid re-computing embeddings for common queries)

#### 26.4 Example 24: Scaling Guide

See `cognee_examples/24_scaling_guide.md` — scaling checklist, benchmarks, and Redis configuration.

---

### Chapter 27 — Security, Compliance & Data Privacy

#### 27.1 Authentication

```python
# JWT-based auth
cognee.config.set({
    "auth_provider": "auth0",              # or "cognito", "firebase", "custom"
    "auth_domain": "your-tenant.auth0.com",
    "auth_audience": "https://api.cognee.ai",
})

# API key auth (simpler, for internal services)
cognee.config.set({
    "auth_provider": "api_key",
    "api_keys": ["cognee_sk_prod_abc123..."]
})
```

#### 27.2 Network Security

- All API traffic should go through HTTPS/TLS in production
- Cognee's MCP server uses local stdio by default (no network exposure)
- REST API supports CORS configuration: `CORS_ALLOWED_ORIGINS` env var

#### 27.3 Data Privacy & PII

Cognee does not automatically redact PII (as of v0.5.7), but you can:
- Pre-process data with a PII detection library before calling `add()`
- Use dataset-level access controls to limit PII exposure
- Audit all data access via OTEL traces

A PII compliance engine (GDPR-aware auto-redaction) is on the roadmap.

#### 27.4 Compliance Considerations

- **SOC 2**: Available via Zep Cloud (Graphiti); Cognee Cloud certification in progress
- **HIPAA**: Neither Cognee nor Graphiti currently HIPAA-compliant for self-hosted; Zep Cloud has HIPAA
- **GDPR**: Data scoping by user_id enables deletion requests; `forget()` handles right-to-erasure

#### 27.5 Example 25: Security Configuration

See `cognee_examples/25_security_config.md` — security hardening guide covering auth, network, PII, and audit.

---

## PART 6: ARCHITECTURAL DECISIONS & TRADEOFFS

### Chapter 28 — Why Three Databases? (Poly-Store Rationale)

**The trilemma:** No single database type is good at document metadata (filtering, JOINs), semantic search (ANN over embeddings), AND graph traversal (recursive edge following).

| Approach | Document Metadata | Semantic Search | Graph Traversal |
|---|---|---|---|
| Postgres + pgvector | ✅ Good | ⚠️ Degrades > 1M vectors | ❌ SQL CTEs choke on depth > 3 |
| Elasticsearch | ✅ Good | ✅ Good (dense vectors) | ❌ No native graph support |
| Neo4j | ❌ Not designed for it | ❌ No vector support (pre-v5) | ✅ Excellent |
| **Cognee's poly-store** | ✅ PostgreSQL | ✅ Qdrant/Pinecone | ✅ Neo4j |

**The cost:** Write amplification. One `cognify()` call fans out to three stores. If any store is down, writes to that store queue and retry. Consistency is eventual, not strict.

**Why not just Postgres?** pgvector works for moderate scale but its ANN performance degrades with dimensionality and scale. And recursive CTEs for graph traversal become impractical beyond 2-3 hops (exponential join explosion).

**The bet:** Storage is cheap. LLM calls are expensive. It's better to pay the storage cost (three copies of metadata plus indexes) to save on LLM costs (precise retrieval means fewer tokens in context).

---

### Chapter 29 — ECL vs ETL: Why the LLM in the Middle?

Traditional ETL pipelines have deterministic transforms:

```
Raw Data → [Python/Spark/SQL transform] → Clean Data → Load
```

Cognee's ECL has a non-deterministic, expensive transform:

```
Raw Data → [LLM entity extraction + relationship detection] → Knowledge Graph → Load
```

**Why pay this cost?** Because the LLM is the only viable entity extractor for unstructured text. Rule-based NER (spaCy, Stanford NER) works for well-defined categories (person, org, location) but fails on domain-specific entities (product names, contract clauses, research methods, code symbols). The LLM generalizes across domains without retraining.

**The cost implication:** LLM inference dominates write costs. Extracting entities and relationships from 1 GB of text can require 40+ minutes and millions of tokens. This is why Cognee is designed for **"write once, read many"** — the expensive extraction happens once, then queries are cheap (subgraph retrieval + focused LLM synthesis vs. dumping 50 chunks into context).

**When this breaks:** Real-time streaming data (social media feeds, live chat). Cognee's write path is too slow for sub-second ingestion. For those use cases, batch-process periodically and use simpler RAG for real-time.

---

### Chapter 30 — Structured Output Dependency: The Double-Edged Sword

Cognee relies on LLMs producing valid, schema-compliant JSON. This is its greatest strength and biggest operational risk.

**The strength:** Structured output (via Instructor/BAML with OpenAI function-calling or Anthropic tool use) means Cognee gets typed DataPoints directly from the LLM — no regex parsing, no fragile post-processing. Entity types, relationships, and properties all match the defined schema.

**The risk:** This ties Cognee's reliability to the LLM's structured output capability. Local models (Ollama with Llama 3.1 8B, Mistral 7B) frequently produce malformed JSON or hallucinate field names. In testing, models up to 24B parameters *all failed* on real-world PDF extraction. The 120B model couldn't run on consumer hardware. Only commercial APIs (GPT-4o, Claude Opus/Sonnet, Gemini) reliably produce valid structured output.

**The implication for self-hosters:** If you need an air-gapped deployment, you'll need either:
- A very large local model (70B+) with careful prompt engineering and validation/retry logic
- Acceptance that extraction quality will be lower
- A hybrid: use a commercial API for the initial cognify, then run queries locally

**Future direction:** Fine-tuned small models specifically for entity extraction (like NuMind, GLiNER, or custom distilled models) could close this gap. Cognee's task system is designed to swap in different extraction backends as they improve.

---

### Chapter 31 — Incremental vs Full Rebuild: Memify Trade-offs

When new data arrives, you have two options:

| Approach | Pros | Cons |
|---|---|---|
| **Re-cognify entire dataset** | Clean, consistent graph; no drift | Expensive (re-process everything); slow |
| **Memify (incremental)** | Fast; only processes new data | Graph drift over time; stale entities; missed cross-document connections |

**Memify's algorithm:**
1. Only cognify the new/changed documents
2. Merge new entities into existing graph (dedup by embedding similarity)
3. Add new relationships
4. Attempt to discover cross-document connections between new and old entities
5. Re-weight existing relationships based on new evidence

**When memify works well:**
- Adding a single new document to a large existing corpus
- Periodically ingesting new articles/reports in the same domain
- User feedback that corrects a specific extraction error

**When memify produces drift:**
- Adding a dataset on a fundamentally new topic (old entity extraction patterns don't apply)
- Schema changes (new DataPoint types need re-extraction of old documents)
- Large batches of new data (cost of memify approaches cost of re-cognify)

**Recommendation:** Memify weekly; re-cognify monthly. Or set a freshness threshold — when more than 20% of documents have changed, do a full re-cognify.

---

### Chapter 32 — Cognee vs Building Your Own: Build vs Buy

**What Cognee gives you (that you'd have to build yourself):**

| Component | Effort to Build Yourself |
|---|---|
| 30+ data format adapters (PDF, DOCX, images, audio, Slack, Notion, etc.) | 2-3 engineer-months |
| LLM-based entity/relationship extraction with structured output | 1-2 months (Instructor/BAML integration, retry logic, batching) |
| Triple-store sync (relational + vector + graph) with eventual consistency | 2-3 months |
| Task/pipeline orchestration with concurrency control | 1 month |
| Session-aware memory (short-term cache + long-term graph + promotion) | 1-2 months |
| REST API + MCP server + CLI + TypeScript SDK | 1-2 months |
| Permissions/RBAC with multi-tenancy | 1 month |
| Graph visualization (D3.js interactive HTML) | 2-3 weeks |
| OpenTelemetry tracing | 1-2 weeks |
| Documentation, tests, community | Priceless |

**Total DIY estimate:** 9-15 engineer-months for a production-quality equivalent.

**When NOT to use Cognee:**

1. **Simple semantic search** — If you just need "find similar documents," use LangChain + Chroma. Cognee adds complexity you don't need.
2. **Real-time streaming** — Cognee's write path is too slow for sub-second ingestion. Use a streaming RAG approach.
3. **Pure temporal reasoning** — If your primary need is "what was true at time T?", Graphiti's bi-temporal model is purpose-built for this.
4. **Fully air-gapped with small models** — If you must run on consumer hardware with local LLMs, Cognee's structured output dependency will frustrate you.
5. **You only have one data type** — If all your data is in one format and you don't need relationships, you're over-engineering.

---

## PART 7: PROS & CONS — THE HONEST ASSESSMENT

### Chapter 33 — Pros: Where Cognee Shines

1. **Multi-hop reasoning accuracy** (~90% tuned vs ~60% for RAG): The knowledge graph provides structural scaffolding for the LLM to reason across facts. Instead of the LLM reconstructing logical chains from flat chunks, it traverses pre-built edges.

2. **Persistent, evolving memory**: Facts don't disappear between queries. The graph accumulates knowledge over time, with memify() handling incremental updates and confidence decay.

3. **Poly-store architecture**: Each access pattern gets the right database. You're not forcing SQL to do graph traversals or vector DBs to do metadata filtering.

4. **Session-aware agent memory**: The V2 API's `session_id` concept enables short-term → long-term memory promotion — exactly what AI agents need for multi-turn conversations that build lasting knowledge.

5. **30+ data source adapters out of the box**: PDFs, DOCX, images, audio, databases, APIs, Slack, Notion, GitHub, S3 — a breadth no other memory framework matches.

6. **Self-improving skills system**: Skills can observe their own performance and auto-correct, reducing the maintenance burden of knowledge graph quality.

7. **Open source core** (Apache 2.0): No vendor lock-in. Self-hostable. Active community with 14K+ GitHub stars and €7.5M in funding.

8. **Incremental processing**: Don't re-process your entire corpus when you add one document. Content hashing ensures only changed data goes through the expensive cognify pipeline.

9. **Multi-tenancy built in**: Dataset-level RBAC with user/tenant isolation — essential for SaaS products and enterprise deployments.

10. **Observability**: OpenTelemetry tracing gives you visibility into pipeline performance, LLM costs, and extraction quality.

---

### Chapter 34 — Cons & Gotchas

1. **Slow writes** — LLM-powered entity extraction dominates cost and latency. ~40 minutes per GB. Budget for LLM API costs during ingestion.

2. **Structured output dependency** — Self-hosting with local LLMs (< 70B parameters) is unreliable. You need commercial APIs (OpenAI, Anthropic) for consistent extraction quality. This creates a vendor dependency and makes air-gapped deployments challenging.

3. **Python-only SDK** — No native TypeScript, Go, or Java clients. TypeScript projects need a REST API wrapper or the `@lineai/cognee-api` package (which is thin).

4. **Default dev stack is not production-ready** — SQLite + LanceDB + Kuzu works great for development but Kuzu's file-based locking blocks concurrent multi-agent access. You must upgrade to Neo4j + Qdrant + PostgreSQL for production.

5. **Documentation lag** — The API evolves faster than the docs. You'll sometimes need to read source code for advanced use cases. The DeepWiki API reference helps but isn't official.

6. **Cold-start problem** — The knowledge graph needs ~20+ entries before meaningful structure emerges. For brand-new use cases, expect low-quality results until you've fed enough data.

7. **Large-graph latency** — Queries over graphs with 1B+ nodes can exceed 2 seconds. For latency-sensitive applications, cache frequent subgraphs in Redis.

8. **Overkill for simple search** — If you just need semantic document search, Cognee's complexity (three databases, LLM extraction, schema design) is wasteful. Use LangChain + Chroma.

9. **No LongMemEval score** — Unlike Graphiti (63.8%), Cognee hasn't published on the standard long-term memory benchmark. Existing benchmarks are Cognee's own, with Cognee in tuned configuration vs competitors on defaults.

10. **Evolving API** — The V1 → V2 API shift means tutorials and examples from early 2025 may use deprecated patterns. Check the changelog if something doesn't work.

---

### Chapter 35 — Comparison Matrix (Cognee vs Alternatives)

| Feature | Cognee | MS GraphRAG | LlamaIndex | Mem0 | Graphiti (Zep) | Hindsight |
|---|---|---|---|---|---|---|
| Knowledge Graph | ✅ Native | ✅ Communities | ✅ PropertyGraphIndex | ❌ | ✅ Temporal KG | ✅ |
| Vector Search | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Session Memory | ✅ V2 API | ❌ | ❌ | ✅ | ✅ Episode model | ✅ |
| Multi-Modal | ✅ Images/Audio | ❌ | ✅ | ❌ | ❌ Text-focused | ❌ |
| Temporal Reasoning | ⚠️ Metadata only | ❌ | ❌ | ❌ | ✅ Bi-temporal facts | ✅ |
| Self-Improving | ✅ Skills | ❌ | ❌ | ❌ | ❌ | ✅ |
| Multi-Tenant | ✅ RBAC | ❌ | ❌ | ❌ | ✅ Zep Cloud | ❌ |
| Data Source Connectors | ✅ 30+ | ❌ | ✅ 20+ | ❌ | ❌ Episode-only | ❌ |
| SDK Languages | Python | Python | Python, TS | Python, TS | Python, TS, Go | Python |
| Open Source | ✅ Apache 2.0 | ✅ MIT | ✅ MIT | ✅ Apache 2.0 | ✅ Apache 2.0 | ✅ Commercial |
| Self-Hosted | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Managed Cloud | ✅ Cognee Cloud | ❌ | ✅ LlamaCloud | ✅ | ✅ Zep Cloud | ✅ |
| LongMemEval Score | Not published | Not published | Not published | ✅ | ✅ 63.8% (GPT-4o) | Not published |

**Key takeaways from the matrix:**

- **Cognee** is the most feature-complete option: only one with multimodal + multi-tenant + self-improving + 30+ connectors. The cost is Python-only SDK and no published standard benchmark.
- **Graphiti** leads on temporal reasoning and has the strongest SDK language support (Python, TS, Go). But it's text-focused and episode-only — no document ingestion.
- **Microsoft GraphRAG** is best for global summarization of large corpora ("what are the themes?") but lacks session memory, permissions, and self-improvement.
- **Mem0** is the simplest: lightweight, fast, good for preference recording. No knowledge graph means limited multi-hop reasoning.
- **Hindsight** has the most sophisticated retrieval (semantic + BM25 + graph + temporal) but is commercial, not open source.
- **LlamaIndex** is the most flexible toolkit — build whatever you want — but you'll be assembling components yourself rather than getting a ready-made memory system.

---

## APPENDICES

### Appendix A — Quick Reference Card

#### V1 Pipeline API

```python
await cognee.add(data, dataset_name=None, user_id=None, metadata=None)
await cognee.cognify(datasets=None, user_id=None)
await cognee.search(query, query_type=SearchType.GRAPH_COMPLETION,
                     dataset=None, user_id=None, top_k=10, filters=None)
await cognee.memify(extraction_tasks=None, dataset=None)
await cognee.visualize_graph(output_path="graph.html", dataset=None,
                              max_nodes=200, include_edges=True)
```

#### V2 Memory API

```python
await cognee.remember(data, session_id=None, user_id=None)
await cognee.recall(query, session_id=None, user_id=None, top_k=10)
await cognee.improve(data=None, session_id=None, promote_to_permanent=False, feedback=None)
await cognee.forget(dataset=None, session_id=None, user_id=None, older_than=None)
```

#### SearchType Enum

```python
SearchType.GRAPH_COMPLETION  # Hybrid: graph traversal + vector + LLM synthesis
SearchType.CHUNKS             # Pure vector similarity over chunks
SearchType.INSIGHTS           # Summarized insights from cognify
SearchType.SUMMARY            # Document and node summaries
SearchType.GRAPH              # Pure graph traversal (no LLM synthesis)
```

#### DataPoint Pattern

```python
from cognee.modules.data.models import DataPoint
from pydantic import Field

class MyEntity(DataPoint):
    name: str = Field(..., index_fields=["name"])
    description: str = Field(default="")
    # Inherited: id (UUID), created_at, updated_at, version
```

#### Environment Variables

```bash
LLM_API_KEY=sk-...              # API key for LLM provider
LLM_PROVIDER=openai             # openai, anthropic, ollama, google
LLM_MODEL=gpt-4o                # Model name
LLM_API_BASE=https://...        # Custom API endpoint
EMBEDDING_PROVIDER=openai       # Embedding provider
EMBEDDING_MODEL=text-embedding-3-small
GRAPH_DB_PROVIDER=kuzu          # kuzu, neo4j, falkordb, networkx
GRAPH_DB_URL=bolt://...         # Graph DB connection
VECTOR_DB_PROVIDER=lancedb      # lancedb, qdrant, weaviate, chroma, pinecone
VECTOR_DB_URL=http://...        # Vector DB connection
RELATIONAL_DB_PROVIDER=sqlite   # sqlite, postgresql
RELATIONAL_DB_URL=postgresql://... # Relational DB connection
COGNEE_CONCURRENCY=10           # Max concurrent LLM calls
COGNEE_DISTRIBUTED=false        # Enable distributed pipeline
CORS_ALLOWED_ORIGINS=*          # CORS configuration
```

---

### Appendix B — Troubleshooting Common Issues

| Symptom | Likely Cause | Solution |
|---|---|---|
| `cognify()` hangs | LLM rate limits | Reduce `COGNEE_CONCURRENCY`; check API key quota |
| `search()` returns empty | Dataset scoping mismatch | Check `dataset=` parameter; verify data was added to that dataset |
| `search()` returns empty | Embedder mismatch | Ensure same embedder used for cognify and search |
| Kuzu lock error | Multi-agent concurrent access to file-based Kuzu | Switch to Neo4j (`GRAPH_DB_PROVIDER=neo4j`) |
| Structured output failures | Local LLM too small | Use GPT-4o or Claude for extraction; local models < 70B struggle |
| High LLM costs | Too many chunks being processed | Increase chunk size; reduce document set; use incremental processing |
| Slow queries on large graph | Graph traversal depth | Add Redis cache; limit traversal depth; use NodeSet scoping |
| Duplicate entities in graph | Dedup threshold too strict | Lower dedup similarity threshold (default 0.85 → 0.75) |
| `forget()` didn't remove data | Soft delete (trash enabled) | Check trash TTL config; use `forget(..., permanent=True)` in v0.5.7+ |
| REST API 401 | Missing/invalid auth | Check `Authorization: Bearer` header or `X-Api-Key` |

---

### Appendix C — Configuration Reference

All configuration options via `cognee.config.set({...})`:

```python
{
    # LLM Configuration
    "llm_provider": "openai",           # openai, anthropic, ollama, google
    "llm_model": "gpt-4o",
    "llm_api_key": "sk-...",
    "llm_api_base": None,               # Custom endpoint for proxies
    "llm_temperature": 0.0,             # Lower = more deterministic extraction
    "llm_max_tokens": 4096,

    # Embedding Configuration
    "embedding_provider": "openai",
    "embedding_model": "text-embedding-3-small",
    "embedding_dimensions": 1536,

    # Vision/Audio
    "vision_model": None,               # Model for image description
    "ocr_engine": "tesseract",
    "asr_model": "whisper-1",

    # Database Providers
    "graph_database_provider": "kuzu",
    "graph_database_url": None,
    "graph_database_username": None,
    "graph_database_password": None,

    "vector_database_provider": "lancedb",
    "vector_database_url": None,
    "vector_database_api_key": None,

    "relational_database_provider": "sqlite",
    "relational_database_url": None,

    # Cache
    "cache_provider": None,             # None, redis
    "cache_url": None,
    "cache_ttl_seconds": 3600,
    "cache_max_size_mb": 2048,

    # Pipeline
    "concurrency": 10,                  # Max concurrent LLM calls
    "chunk_size": 1024,                 # Tokens per chunk
    "chunk_overlap": 50,               # Token overlap between chunks
    "distributed": False,              # Enable distributed pipeline

    # Observability
    "tracing_enabled": False,
    "otel_exporter_endpoint": None,
    "otel_exporter_headers": {},

    # Auth
    "auth_provider": None,             # auth0, cognito, firebase, api_key, custom
    "auth_domain": None,
    "auth_audience": None,
    "api_keys": [],

    # Server
    "api_host": "0.0.0.0",
    "api_port": 8000,
    "cors_allowed_origins": "*",
}
```

---

### Appendix D — Glossary

| Term | Definition |
|---|---|
| **Cognify** | The pipeline phase that transforms raw data into a knowledge graph: chunking → embedding → entity extraction → relationship extraction → graph construction |
| **DataPoint** | A typed Pydantic model representing a node or edge in the knowledge graph. The atomic unit of memory. |
| **ECL** | Extract-Cognify-Load: Cognee's pipeline paradigm. Unlike ETL (deterministic transforms), ECL uses LLMs for the "Cognify" transform. |
| **Entity Extraction** | The LLM-based task that identifies named entities (people, orgs, concepts, etc.) in text and returns them as typed DataPoints. |
| **Knowledge Graph** | A structured representation of entities (nodes) connected by relationships (edges), stored in a graph database (Kuzu/Neo4j). |
| **Memify** | The post-cognify enrichment pipeline that incrementally updates the knowledge graph: entity merging, relationship strengthening, stale node cleanup, temporal reweighting. |
| **NodeSet** | A labeling system that groups related facts into named sets, enabling scoped queries without separate databases. |
| **Poly-Store** | Cognee's three-database architecture: relational (metadata), vector (semantic search), graph (relationships). |
| **Session Memory** | Short-term memory tied to a `session_id`. Can be promoted to permanent graph memory via `improve()`. |
| **Session Promotion** | The process of moving facts from short-term session memory to the permanent knowledge graph, with provenance and feedback weighting. |
| **Skill** | A packaged, self-improving capability with six lifecycle phases: ingest, route, execute, observe, evaluate, amend. |

---

### Appendix E — Migration Guide: V1 Pipeline API → V2 Memory API

| V1 Pattern | V2 Equivalent | Notes |
|---|---|---|
| `await cognee.add(data)` | `await cognee.remember(data)` | V2 combines add + cognify for simple cases |
| `await cognee.add(data); await cognee.cognify()` | `await cognee.remember(data)` | V2 infers when full cognify is needed |
| `await cognee.search(query)` | `await cognee.recall(query)` | V2 adds session awareness |
| `await cognee.search(query, dataset="X")` | `await cognee.recall(query)` | V2 doesn't need dataset scoping (automatic) |
| `await cognee.memify()` | `await cognee.improve()` | V2 adds session promotion and feedback weighting |
| N/A (no V1 equivalent) | `await cognee.forget(session_id="X")` | V2 adds scoped deletion |
| N/A (no V1 equivalent) | `await cognee.improve(session_id="X", promote_to_permanent=True)` | V2 adds session promotion |
| N/A (no V1 equivalent) | `await cognee.remember(data, session_id="X")` | V2 adds session-scoped memory |

**When to stay on V1:**
- You're doing batch processing of large document corpora
- You don't need session-aware memory
- You have existing V1 pipelines you don't want to refactor yet

**When to migrate to V2:**
- You're building AI agents (chatbots, assistants, copilots)
- You need short-term → long-term memory promotion
- You want the simpler API surface (`remember`/`recall` vs `add`/`cognify`/`search`)

**Migration is gradual:** V1 and V2 APIs coexist. You can use V2 for agent memory while keeping V1 for batch corpus processing in the same codebase.

---

> **That's the complete Cognee In-Depth handbook.** All example code referenced throughout lives in the `cognee_examples/` directory. Each example is a self-contained, runnable script. Start with `01_hello_cognee.py` and work your way up. For questions or corrections, file an issue at [github.com/topoteretes/cognee](https://github.com/topoteretes/cognee).
