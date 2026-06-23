# 4. Recall — TEMPR Multi-Strategy Retrieval

`recall()` is Hindsight's **read operation**. Unlike simple vector search,
it runs **four parallel retrieval strategies** and fuses them into a single,
reranked result set.

## TEMPR: The Four Retrieval Strategies

```
                     query("What does Alice do?")
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
    ┌──────────┐       ┌──────────┐        ┌──────────┐
    │ Semantic │       │ Keyword  │        │  Graph   │
    │ (vector) │       │  (BM25)  │        │(entities)│
    └────┬─────┘       └────┬─────┘        └────┬─────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            ▼
                    ┌──────────────┐
                    │  RRF Fusion   │  ← Reciprocal Rank Fusion
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │ Cross-Encoder │  ← Reranking model
                    │   Reranker    │
                    └──────┬───────┘
                           ▼
                    ┌──────────────┐
                    │  Trim to      │
                    │  token budget │
                    └──────┬───────┘
                           ▼
                      Final Results
```

---

## Basic Usage

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Simple recall
results = client.recall(
    bank_id="my-bank",
    query="What programming language does the user prefer?"
)

# results.results is a list of RecallResult objects
for r in results.results:
    print(f"Type: {r.type}")    # world, experience, observation
    print(f"Text: {r.text}")    # The memory content
    print(f"Score: {r.score}")   # Relevance score
    print("---")
```

---

## Full Parameter Reference

```python
results = client.recall(
    bank_id="my-bank",          # str: Target bank
    query="...",                # str: What to search for (required)
    types=["world", "observation"],  # list: Filter by memory type
    max_tokens=4096,            # int: Token budget for results
    budget="high",              # str: Search depth — "low", "mid", "high"
    tags=["project:alpha"],     # list: Filter by tags
    tags_match="any",           # str: "any" or "all" tags
    metadata_filter={           # dict: Filter by metadata
        "user_id": "alice"
    },
    include_chunks=True,        # bool: Include source text chunks
    max_chunk_tokens=500,       # int: Token budget per chunk
    include_entities=True,      # bool: Include extracted entities
    trace=True,                 # bool: Include retrieval trace for debugging
)
```

---

## Parameter Deep Dive

### `query`
Natural language query. Hindsight is NOT keyword-dependent — write like you'd ask a colleague:
- ✅ "What does the user think about Python?"
- ✅ "What happened in the March deployment?"
- ✅ "Summarize the user's framework preferences"

### `types` — Memory Type Filtering

Filter by one or more memory types:

```python
# Only world facts and observations (exclude experiences)
results = client.recall(
    bank_id="bank",
    query="What tools does the team use?",
    types=["world", "observation"]
)

# Only the agent's own experiences
results = client.recall(
    bank_id="bank",
    query="deployment",
    types=["experience"]
)
```

Available types: `"world"`, `"experience"`, `"observation"`

> Note: Mental models are not directly filterable via `types` — they surface during
> `reflect()` as the highest-priority knowledge source.

### `budget` — Search Depth

Controls how extensively Hindsight searches:

| Budget | Vector neighbors | Keyword results | Graph hops | Best for |
|--------|-----------------|-----------------|------------|----------|
| `low` | 20 | 10 | 1 | Quick lookups, simple queries |
| `mid` | 50 | 25 | 2 | General use (default) |
| `high` | 100 | 50 | 3 | Complex questions, thorough recall |

```python
# Lightweight check
quick = client.recall(bank_id="bank", query="user name", budget="low")

# Deep research
deep = client.recall(bank_id="bank", query="full project history", budget="high")
```

### `max_tokens`
Caps the total token count of returned results. Hindsight trims to fit:

```python
# Get just the top hits
concise = client.recall(bank_id="bank", query="...", max_tokens=1024)

# Get comprehensive context
comprehensive = client.recall(bank_id="bank", query="...", max_tokens=8192)
```

### `tags` & `tags_match`
Tag-based filtering. Tags can be attached during `retain()` or via the API:

```python
# Recall only memories about Project Alpha
results = client.recall(
    bank_id="bank",
    query="deployment status",
    tags=["project:alpha", "environment:production"],
    tags_match="all"  # Must have ALL tags (default: "any")
)
```

### `metadata_filter`
Filter by metadata key-value pairs. Most commonly used for per-user isolation:

```python
# Alice's view
alice_results = client.recall(
    bank_id="shared-bank",
    query="preferences",
    metadata_filter={"user_id": "alice"}
)

# Bob's view — completely different results from the same bank
bob_results = client.recall(
    bank_id="shared-bank",
    query="preferences",
    metadata_filter={"user_id": "bob"}
)
```

### `include_chunks` & `max_chunk_tokens`
When `True`, each result includes the original source text chunks:

```python
response = client.recall(
    bank_id="bank",
    query="Python preferences",
    include_chunks=True,
    max_chunk_tokens=500
)

for r in response.results:
    print(f"Memory: {r.text}")
    if r.chunks:
        for chunk in r.chunks:
            print(f"  Source: {chunk.text[:200]}...")
```

This is essential for **evidence-backed answers** — show the user where a belief came from.

### `include_entities`
Returns extracted entities with each result:

```python
results = client.recall(
    bank_id="bank",
    query="Alice career",
    include_entities=True
)

for r in results.results:
    print(f"Text: {r.text}")
    if r.entities:
        for entity in r.entities:
            print(f"  Entity: {entity.name} ({entity.type})")
```

### `trace`
For debugging, includes the retrieval trace showing what each strategy contributed:

```python
results = client.recall(
    bank_id="bank",
    query="test query",
    trace=True
)

# results.trace shows hits per strategy, RRF scores, reranker output
```

---

## Results Structure

```python
class RecallResponse:
    results: list[RecallResult]   # The matched memories
    trace: dict | None            # Debug trace (if requested)

class RecallResult:
    id: str                       # Memory ID
    text: str                     # Memory text
    type: str                     # "world", "experience", "observation"
    score: float                  # Relevance score (0-1)
    entities: list[Entity] | None # Extracted entities
    chunks: list[Chunk] | None    # Source text chunks
    tags: list[str] | None        # Tags
    metadata: dict | None         # Custom metadata
    timestamp: str | None         # When the memory was created
    occurred_at: str | None       # When the event happened
```

---

## Strategy Deep Dive

### 1. Semantic Search (Vector)
- Embedding model converts query to vector
- Finds nearest neighbors by cosine similarity in pgvector index
- Best for: conceptual similarity, paraphrased queries, "what's similar to X?"
- Weakness: struggles with exact names, IDs, version numbers

### 2. Keyword Search (BM25)
- Full-text search using BM25 (Okapi BM25 algorithm)
- Considers term frequency, document length, rarity
- Best for: names ("Alice"), technical terms ("Kubernetes"), exact matches
- Weakness: misses paraphrases, synonyms, related concepts

### 3. Graph Search
- Traverses the entity-relationship graph
- Starting from entities in the query, follows links to find related facts
- Best for: "Who works with Alice?", connected facts, indirect relationships
- Weakness: requires well-established entity graph

### 4. Temporal Search
- Filters by time ranges mentioned in the query or explicitly specified
- Understands relative time: "last spring", "in June", "recently"
- Best for: "What happened last month?", timeline construction
- Weakness: requires accurate timestamps on memories

---

## Reciprocal Rank Fusion (RRF)

Each strategy produces a ranked list. RRF merges them:

```
RRF_score(d) = Σ (1 / (k + rank_s(d)))
```
where `k` is a constant (typically 60) and `rank_s(d)` is the rank of document `d`
in strategy `s`.

This formula:
- **Rewards** items that rank high across multiple strategies
- **Penalizes** items that only score in one strategy
- **Resists domination** by any single strategy

After RRF, a **cross-encoder model** re-ranks the top candidates for final ordering.

---

## Practical Patterns

### Pattern 1: Context Injection
Recall before every agent turn to inject relevant context:

```python
def get_context(bank_id, user_message):
    """Retrieve relevant memories to inject into the agent's prompt."""
    results = client.recall(
        bank_id=bank_id,
        query=user_message,
        budget="mid",
        max_tokens=4096
    )
    return "\n".join([f"- {r.text}" for r in results.results])

# In your agent loop:
context = get_context("my-agent", user_message)
prompt = f"""Context from past interactions:
{context}

User: {user_message}
Assistant:"""
```

### Pattern 2: Per-User Isolation

```python
class UserMemory:
    def __init__(self, client, bank_id, user_id):
        self.client = client
        self.bank_id = bank_id
        self.user_filter = {"user_id": user_id}

    def remember(self, content):
        self.client.retain(
            bank_id=self.bank_id,
            content=content,
            metadata=self.user_filter
        )

    def recall(self, query):
        return self.client.recall(
            bank_id=self.bank_id,
            query=query,
            metadata_filter=self.user_filter
        )
```

### Pattern 3: Temporal Window

```python
from datetime import datetime, timedelta

# Recall memories from the last 30 days
results = client.recall(
    bank_id="bank",
    query="deployment issues",
    query_timestamp=datetime.utcnow().isoformat() + "Z",
    # The TEMPR temporal strategy handles recency automatically
)
```

---

## Debugging Recall

If recall isn't returning what you expect:

1. **Check `trace=True`** to see what each strategy found
2. **Verify timestamps** on retained facts
3. **Try broader query**: more general language hits semantic better
4. **Try specific names**: BM25 catches exact terms semantic misses
5. **Check entity graph**: `GET /bank/{id}/graph` to verify entity links
6. **Use include_chunks**: see what raw text is being retrieved

```python
# Debug trace
results = client.recall(
    bank_id="bank",
    query="Alice",
    trace=True,
    budget="high"
)
print("Semantic hits:", len(results.trace.get("semantic", [])))
print("Keyword hits:", len(results.trace.get("keyword", [])))
print("Graph hits:", len(results.trace.get("graph", [])))
print("Temporal hits:", len(results.trace.get("temporal", [])))
```

---

Continue to:
- **[05_reflect.md](05_reflect.md)** — Master disposition-aware reasoning
- Run the notebook: `notebooks/04_recall.ipynb`
