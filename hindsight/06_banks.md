# 6. Bank Management — Configuration & Lifecycle

Memory banks are the top-level organizational unit in Hindsight. Each bank is a
self-contained memory store with its own facts, entities, observations, and configuration.

## Bank Lifecycle

```
create_bank()  →  configure()  →  retain()/recall()/reflect()  →  monitor()  →  delete()
```

---

## Creating a Bank

### Minimal Creation

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Create or update (PUT semantics)
client.create_bank(
    bank_id="my-bank",     # Unique ID (required)
    name="My Bank"          # Display name
)
```

### Full Creation with All Options

```python
client.create_bank(
    bank_id="production-assistant",
    name="Production AI Assistant",

    # Reflect configuration
    reflect_mission="""
    I am a senior backend engineer assistant.
    I prioritize security, reliability, and proven solutions.
    I track the team's tech stack, preferences, and architectural decisions.
    """,

    # Retain configuration
    retain_mission="""
    Extract all technical details: frameworks, versions, configurations,
    deployment targets, and architectural decisions.
    Capture user preferences about coding style, tools, and workflows.
    """,
    retain_extraction_mode="detailed",     # "standard", "detailed", "concise"
    retain_custom_instructions=None,       # Custom extraction guidance
    retain_chunk_size=3000,                # Characters per chunk
    retain_structured_chunk_size=2000,     # For structured content

    # Observation configuration
    enable_observations=True,              # Auto-consolidate facts
    observations_mission=None,             # Optional consolidation guidance

    # Disposition (deprecated — use directives for hard rules)
    disposition={
        "skepticism": 3,   # 1 (trusting) to 5 (skeptical)
        "literalism": 3,   # 1 (flexible) to 5 (literal)
        "empathy": 3       # 1 (detached) to 5 (empathetic)
    }
)
```

---

## Bank Configuration Options Reference

### Reflect Options

| Parameter | Type | Description |
|-----------|------|-------------|
| `reflect_mission` | str | Bank's identity and knowledge priorities |
| `directives` | list[str] | Hard rules that must never be violated |
| `disposition` | dict | Soft personality traits (skepticism, literalism, empathy) |

### Retain Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `retain_mission` | str | — | Guidance for fact extraction |
| `retain_extraction_mode` | str | `standard` | `standard`, `detailed`, `concise` |
| `retain_custom_instructions` | str | — | Custom extraction instructions |
| `retain_chunk_size` | int | model-dependent | Chunk size for long content |
| `retain_structured_chunk_size` | int | model-dependent | Chunk size for structured content |

### Observation Options

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_observations` | bool | `true` | Auto-consolidate related facts |
| `observations_mission` | str | — | Guidance for consolidation |

---

## Updating a Bank

Use `update_bank()` for partial updates:

```python
# Update just the mission
client.update_bank(
    bank_id="my-bank",
    reflect_mission="Updated mission text..."
)

# Switch to detailed extraction
client.update_bank(
    bank_id="my-bank",
    retain_extraction_mode="detailed"
)

# Add directives
client.update_bank(
    bank_id="my-bank",
    directives=[
        "Never share user data outside this bank.",
        "Always cite sources."
    ]
)
```

---

## Listing Banks

```python
banks = client.list_banks()

for bank in banks:
    print(f"ID: {bank.id}")
    print(f"Name: {bank.name}")
    print(f"Facts: {bank.fact_count}")
    print(f"Last document: {bank.last_document_at}")
    print("---")
```

---

## Bank Statistics

```python
stats = client.get_bank_stats(bank_id="my-bank")

print(f"Total memories: {stats.total_memories}")
print(f"World facts: {stats.world_facts}")
print(f"Experience facts: {stats.experience_facts}")
print(f"Observations: {stats.observations}")
print(f"Entities: {stats.entity_count}")
print(f"Graph edges: {stats.edge_count}")
print(f"Pending operations: {stats.pending_operations}")
print(f"Last consolidation: {stats.last_consolidation_time}")
```

---

## Bank Health — LLM Connectivity Check

```python
health = client.check_bank_llm_health(bank_id="my-bank")

# Health check results for retain, consolidation, and reflect
# Each returns success/failure and latency
print(health)
# {
#   "retain": {"status": "ok", "latency_ms": 234},
#   "consolidation": {"status": "ok", "latency_ms": 456},
#   "reflect": {"status": "ok", "latency_ms": 789}
# }
```

> Note: This endpoint can be disabled globally with
> `HINDSIGHT_API_ENABLE_BANK_LLM_HEALTH=false`.

---

## Memory Management

### Listing Memories

```python
# All memories
all_memories = client.list_memories(bank_id="my-bank", limit=50)

# Filtered
world_facts = client.list_memories(
    bank_id="my-bank",
    type="world",
    limit=100
)

# Text search
alice_memories = client.list_memories(
    bank_id="my-bank",
    search_query="Alice",
    limit=50
)

# Pagination
page2 = client.list_memories(
    bank_id="my-bank",
    limit=50,
    offset=50
)
```

### Getting a Single Memory

```python
memory = client.get_memory(
    bank_id="my-bank",
    memory_id="mem_abc123"
)

print(f"Type: {memory.type}")
print(f"Text: {memory.text}")
print(f"Created: {memory.created_at}")
print(f"Entities: {memory.entities}")
```

### Updating (Curating) a Memory

```python
# Edit the text
client.update_memory(
    bank_id="my-bank",
    memory_id="mem_abc123",
    text="Corrected fact text...",
    context="Updated context"
)

# Invalidate a memory (mark as no longer valid)
client.update_memory(
    bank_id="my-bank",
    memory_id="mem_abc123",
    state="invalidated",
    reason="Superseded: server decommissioned 2026-06-01"
)

# Revalidate
client.update_memory(
    bank_id="my-bank",
    memory_id="mem_abc123",
    state="valid"
)
```

Invalidating a memory triggers **re-consolidation** — observations that depended on it
are re-evaluated.

### Deleting Memories

```python
# Delete specific types (DESTRUCTIVE!)
client.delete_memories(
    bank_id="my-bank",
    types=["experience"]  # Deletes all experience facts
)

# Delete ALL memories (EXTREMELY DESTRUCTIVE!)
client.delete_memories(bank_id="my-bank")
# This deletes everything: world, experience, observations
```

---

## Memory Time-Series

```python
# Ingestion timeline
timeseries = client.get_memory_timeseries(
    bank_id="my-bank",
    period="7d"  # Options: 1h, 12h, 1d, 7d, 30d, 90d
)

for bucket in timeseries:
    print(f"{bucket.timestamp}: {bucket.count} memories")
```

---

## Entity Graph Inspection

```python
graph = client.get_graph(bank_id="my-bank")

# Nodes are entities
print(f"Entities: {len(graph.nodes)}")
for node in graph.nodes[:5]:
    print(f"  {node.name} ({node.type})")

# Edges are relationships
print(f"Relationships: {len(graph.edges)}")
for edge in graph.edges[:5]:
    print(f"  {edge.source} --{edge.relationship}--> {edge.target}")
```

---

## Tags

### Listing Tags

```python
tags = client.list_tags(bank_id="my-bank")

for tag in tags:
    print(f"Tag: {tag.name}, Count: {tag.count}")

# Wildcard search
project_tags = client.list_tags(bank_id="my-bank", search="project:*")

# Mental model tags only
mm_tags = client.list_tags(bank_id="my-bank", source="mental_models")
```

---

## Deleting a Bank

```python
# IRREVERSIBLE — deletes everything
client.delete_bank(bank_id="my-bank")
```

---

## Bank Design Patterns

### Pattern 1: One Bank Per User

```python
# Each user gets their own bank
def get_user_bank(user_id):
    bank_id = f"user-{user_id}"
    try:
        client.get_bank_stats(bank_id=bank_id)
    except:
        client.create_bank(
            bank_id=bank_id,
            name=f"User {user_id}",
            reflect_mission=f"Personal assistant for user {user_id}."
        )
    return bank_id
```

### Pattern 2: Shared Bank with Metadata Isolation

```python
# Single bank, filter by metadata
SHARED_BANK = "shared-assistant"

def store_for_user(user_id, content):
    client.retain(
        bank_id=SHARED_BANK,
        content=content,
        metadata={"user_id": user_id}
    )

def recall_for_user(user_id, query):
    return client.recall(
        bank_id=SHARED_BANK,
        query=query,
        metadata_filter={"user_id": user_id}
    )
```

### Pattern 3: Project Banks

```python
# One bank per project
for project in ["alpha", "beta", "gamma"]:
    client.create_bank(
        bank_id=f"project-{project}",
        name=f"Project {project.upper()}",
        reflect_mission=f"Knowledge base for Project {project.upper()}."
    )
```

### Pattern 4: Tiered Banks

```python
# Global knowledge bank (shared across all agents)
client.create_bank(
    bank_id="global-knowledge",
    name="Global Knowledge Base",
    reflect_mission="Company-wide knowledge: policies, architecture, best practices."
)

# Per-agent banks (agent-specific learning)
client.create_bank(
    bank_id="agent-sales",
    name="Sales Agent Memory",
    reflect_mission="Sales agent: track leads, preferences, deal history."
)

# Cross-reference: agent banks retain facts that overlap with global knowledge
```

---

Continue to:
- **[07_mental_models.md](07_mental_models.md)** — Mental models and observations
- Run the notebook: `notebooks/06_banks.ipynb`
