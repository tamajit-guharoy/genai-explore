# 3. Retain — Storing Memories

`retain()` is Hindsight's **write operation**. It converts raw text into structured,
indexable facts through LLM-powered extraction.

## Basic Usage

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Simplest form
client.retain(
    bank_id="my-bank",
    content="Alice works at Google as a software engineer"
)
```

Internally, Hindsight:
1. Sends the content to an LLM for fact extraction
2. Identifies entities (Alice, Google)
3. Extracts relationships (works_at → Google, role → software engineer)
4. Tags temporal information if present
5. Normalizes facts into canonical form
6. Indexes across all 4 retrieval strategies (semantic, keyword, graph, temporal)
7. Triggers observation consolidation (if related facts exist)

---

## Full Parameter Reference

```python
client.retain(
    bank_id="my-bank",          # str: Target memory bank ID
    content="...",              # str: The text to store (required)
    context="career update",    # str: Optional context label
    timestamp="2026-06-15T10:00:00Z",  # str/datetime: When this happened
    document_id="conv_001",     # str: Group related retains together
    metadata={"source": "slack", "channel": "engineering"},  # dict: Custom metadata
    retain_async=False,         # bool: Process in background (default: sync)
)
```

### Parameter Details

#### `content` (required)
The raw text to process. Can be:
- A user message: *"I prefer Python for data science"*
- A conversation summary: *"Discussed deployment options. User chose AWS ECS."*
- A tool result: *"Database migration completed. 3 tables altered."*
- A feedback note: *"User said the last recommendation was too technical."*

No length limit, but very long content should be chunked (set `retain_chunk_size` on the bank).

#### `context`
A short label to categorize the memory. Useful for filtering later:

```python
# Tag with context
client.retain(bank_id="bank", content="Deployed v2.1 to production", context="deployment")
client.retain(bank_id="bank", content="User reported bug in login flow", context="bug_report")
client.retain(bank_id="bank", content="Team decided to use Redis for caching", context="architecture")
```

#### `timestamp`
When the event described in `content` occurred (NOT when it was stored).
Accepts ISO 8601 strings or Python datetime objects:

```python
from datetime import datetime, timezone

client.retain(
    bank_id="bank",
    content="Signed contract with Acme Corp",
    timestamp="2026-06-15T14:30:00Z"
)

# Python datetime also works
client.retain(
    bank_id="bank",
    content="Quarterly review meeting",
    timestamp=datetime(2026, 6, 15, 14, 30, tzinfo=timezone.utc)
)
```

This enables temporal queries like "what happened in June 2026?"

#### `document_id`
Groups related retains together. When you update or delete, you can target by document:

```python
# All these belong to the same conversation
doc_id = "conv_2026_06_15_001"

client.retain(bank_id="bank", content="User asked about Kubernetes", document_id=doc_id)
client.retain(bank_id="bank", content="I explained EKS vs GKE tradeoffs", document_id=doc_id)
client.retain(bank_id="bank", content="User decided on EKS for familiarity", document_id=doc_id)
```

#### `metadata`
Arbitrary key-value pairs for filtering and isolation. The most common use case is
**per-user memory isolation**:

```python
# Store per-user
client.retain(
    bank_id="shared-bank",
    content="User prefers dark mode",
    metadata={"user_id": "alice"}
)

client.retain(
    bank_id="shared-bank",
    content="User prefers light mode",
    metadata={"user_id": "bob"}
)

# Recall filtered by user
results = client.recall(
    bank_id="shared-bank",
    query="display preferences",
    metadata_filter={"user_id": "alice"}  # Only Alice's memories
)
```

#### `retain_async`
When `True`, the call returns immediately and processing happens in the background.
Useful for high-throughput scenarios:

```python
# Fire and forget — returns immediately
client.retain(
    bank_id="bank",
    content="Log entry: request served in 23ms",
    retain_async=True
)
# Returns: {"success": True, "operation_id": "op_abc123"}
```

You can poll the operation status via the bank stats endpoint.

---

## Batch Retain

For storing multiple items at once, use `retain_batch()`:

```python
client.retain_batch(
    bank_id="my-bank",
    items=[
        {"content": "Alice works at Google", "context": "career"},
        {"content": "Bob is a data scientist", "context": "career"},
        {"content": "Carol leads the ML team", "context": "career", "timestamp": "2026-01-01T00:00:00Z"},
    ],
    document_id="team_intros",
    retain_async=False
)
```

Batch is **much faster** than individual calls for bulk loading:
- Single LLM call for fact extraction across all items
- Single indexing pass
- Atomic: all or nothing

---

## Dry-Run Extraction

Preview what facts Hindsight would extract without storing:

```python
# See what Hindsight would extract — no storage
preview = client.dry_run_extract(
    bank_id="my-bank",
    content="Alice started at Google in 2020 and was promoted to senior engineer in 2023. She works on the Search team."
)
# Returns candidate facts, entities, and relationships without committing
```

This is useful for:
- Debugging extraction quality
- Testing different extraction modes before committing
- Understanding how Hindsight interprets ambiguous content

---

## Extraction Modes

Configure how Hindsight extracts facts via the bank's `retain_extraction_mode`:

| Mode | Description | Best for |
|------|-------------|----------|
| `standard` | Balanced extraction | General use |
| `detailed` | More granular facts, more entities | Knowledge-heavy domains |
| `concise` | Fewer, higher-level facts | Chat summaries, simple interactions |

```python
# Set on bank creation
client.create_bank(
    bank_id="detailed-bank",
    name="Detailed Bank",
    retain_extraction_mode="detailed",
    mission="Extract all technical details from conversations"
)
```

---

## Custom Retain Instructions

You can provide custom instructions to guide fact extraction:

```python
client.create_bank(
    bank_id="medical-bank",
    name="Medical Records Bank",
    retain_custom_instructions="""
    When extracting facts:
    - Always capture medication names, dosages, and frequencies
    - Flag any allergies as high-priority
    - Extract lab results with numeric values and reference ranges
    - Note patient-reported symptoms separately from physician observations
    """
)
```

---

## Retain Chunk Size

For very long content, Hindsight automatically chunks. Configure via:

```python
client.create_bank(
    bank_id="long-form-bank",
    name="Long Form Bank",
    retain_chunk_size=3000,          # Characters per chunk (default varies by model)
    retain_structured_chunk_size=2000  # For structured content
)
```

---

## What Happens After retain()

```
retain("Alice got promoted", bank_id="my-bank")
    │
    ▼
┌─────────────────────────┐
│ 1. LLM Fact Extraction   │
│    • Entity: Alice        │
│    • Event: promotion     │
│    • Temporal: now        │
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│ 2. Entity Resolution     │
│    • Is "Alice" the same │
│      as existing entity? │
│    • Link to existing    │
│      relationships       │
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│ 3. Indexing (4 paths)   │
│    • Semantic (vector)   │
│    • Keyword (BM25)      │
│    • Graph (entity links)│
│    • Temporal (date)     │
└─────────┬───────────────┘
          ▼
┌─────────────────────────┐
│ 4. Consolidation Check  │
│    • Related facts exist?│
│    • Update observations │
│    • Merge if redundant  │
└─────────────────────────┘
```

---

## Best Practices

1. **Retain after every turn**: The agent should `retain()` user messages and its own
   responses to build a complete memory.

2. **Use metadata for isolation**: Tag with `user_id`, `session_id`, `project_id` to
   filter during recall.

3. **Batch for bulk loads**: Use `retain_batch()` when ingesting existing data.

4. **Set timestamps**: Whenever possible, provide the actual event time, not storage time.

5. **Use context for categorization**: Makes later filtering and recall more precise.

6. **Dry-run first**: Test extraction quality with `dry_run_extract()` before committing
   large volumes.

7. **Async for high throughput**: Use `retain_async=True` in production loops.

---

Now continue to:
- **[04_recall.md](04_recall.md)** — Master TEMPR multi-strategy retrieval
- Run the notebook: `notebooks/03_retain.ipynb`
