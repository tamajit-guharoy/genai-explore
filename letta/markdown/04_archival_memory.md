# Archival Memory — Long-Term Knowledge Storage

> **Goal**: Master archival memory — passages, semantic search, and building
> knowledge bases that agents can read from and write to autonomously.

---

## 1. Archival vs Core Memory — When to Use Which

| | Core Memory (Blocks) | Archival Memory (Passages) |
|---|---|---|
| **What** | Key facts about user, agent, current task | Curated knowledge documents |
| **Size** | Small (<5K chars per block) | Unlimited (vector DB) |
| **In context?** | YES — always in the prompt | NO — searched on demand |
| **Edited how?** | Agent replaces entire value | Agent inserts/deletes passages |
| **Search** | N/A (always visible) | Semantic (vector) or text search |
| **Best for** | "Who am I talking to?" | "What do we know about X?" |

**Rule of thumb**: If it changes frequently → core memory. If it's reference
knowledge that grows over time → archival memory.

## 2. Setup — Creating an Agent with Archival Memory

```python
from letta_client import Letta
import os

client = Letta(api_key=os.environ["LETTA_API_KEY"])

# Create a fresh agent — the embedding model enables archival memory
agent = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",  # Required for archival search
    memory_blocks=[
        {
            "label": "human",
            "value": "Name: Alex\nRole: Research Analyst\nInterests: AI, biotech, climate tech",
            "limit": 3000
        },
        {
            "label": "persona",
            "value": (
                "I am Quinn, a research analyst. "
                "I maintain a knowledge base of industry research. "
                "When I learn something important, I save it to archival memory. "
                "When asked a question, I search archival memory first."
            ),
            "limit": 3000
        }
    ]
)

AGENT_ID = agent.id
print(f"Agent created: {AGENT_ID}")
```

## 3. Inserting Passages — Building the Knowledge Base

Passages are text chunks stored in a vector database. They can have metadata
for filtering.

```python
def insert_passage(agent_id: str, text: str, metadata: dict = None):
    """
    Insert a passage into an agent's archival memory.
    
    The passage is automatically embedded and becomes searchable.
    Metadata enables filtered search (e.g., by source, date, tags).
    """
    passage = {
        "text": text,
        "agent_id": agent_id
    }
    if metadata:
        passage["metadata"] = metadata
    
    result = client.agents.passages.create(agent_id, **passage)
    return result

# Build a knowledge base about tech companies
passages_data = [
    {
        "text": "OpenAI raised $40B at a $300B valuation in March 2026. "
                "Led by SoftBank with participation from Microsoft, Thrive Capital, "
                "and others. Plans to use funds for compute infrastructure and research.",
        "metadata": {"company": "OpenAI", "type": "funding", "date": "2026-03",
                     "tags": ["AI", "funding", "LLM"]}
    },
    {
        "text": "Anthropic released Claude Opus 4.5 in Q2 2026 with a 200K context window. "
                "Key improvements: better reasoning, reduced hallucination, "
                "computer use capability, and a 30% price reduction vs Opus 4.",
        "metadata": {"company": "Anthropic", "type": "product", "date": "2026-Q2",
                     "tags": ["AI", "LLM", "product"]}
    },
    {
        "text": "Google DeepMind's Gemini 3 Ultra achieved SOTA on MMLU-Pro (92.4%), "
                "HumanEval (96.1%), and MATH (95.8%). Features native multimodal input "
                "and a 2M token context window.",
        "metadata": {"company": "Google", "type": "benchmark", "date": "2026-06",
                     "tags": ["AI", "benchmark", "LLM"]}
    },
    {
        "text": "Letta (formerly MemGPT) released Context Repositories in Feb 2026 — "
                "a git-based memory system where agent memory lives as markdown files. "
                "Supports branching, merging, and version history for agent knowledge.",
        "metadata": {"company": "Letta", "type": "product", "date": "2026-02",
                     "tags": ["AI", "memory", "agents"]}
    },
    {
        "text": "Meta released Llama 4 in April 2026 — a family of open-weight models "
                "ranging from 8B to 405B parameters. The 405B model matches GPT-5 "
                "on several benchmarks while being fully open-source.",
        "metadata": {"company": "Meta", "type": "product", "date": "2026-04",
                     "tags": ["AI", "open-source", "LLM"]}
    },
]

for pdata in passages_data:
    result = insert_passage(AGENT_ID, pdata["text"], pdata["metadata"])
    company = pdata["metadata"]["company"]
    print(f"✓ Inserted: {company} ({pdata['metadata']['type']})")

print(f"\nTotal passages in archival memory: 5")
```

## 4. Searching Archival Memory

Search with natural language — Letta handles the embedding + similarity matching.

```python
def search_archival(agent_id: str, query: str, limit: int = 3):
    """
    Semantic search over archival memory.
    
    Returns passages ranked by vector similarity to the query.
    """
    results = client.agents.passages.search(
        agent_id,
        query=query,
        limit=limit
    )
    return results

# Example searches
queries = [
    "Which AI companies raised funding recently?",
    "What are the latest LLM benchmark results?",
    "Tell me about open-source AI models",
]

for query in queries:
    print(f"\n{'='*60}")
    print(f"Query: {query}")
    print(f"{'='*60}")
    
    results = search_archival(AGENT_ID, query, limit=2)
    
    for i, passage in enumerate(results):
        score = getattr(passage, 'score', 'N/A')
        text = getattr(passage, 'text', str(passage))
        metadata = getattr(passage, 'metadata', {})
        
        print(f"\n  Result {i+1} (similarity: {score}):")
        print(f"  Source: {metadata.get('company', 'N/A')} | "
              f"Type: {metadata.get('type', 'N/A')} | "
              f"Date: {metadata.get('date', 'N/A')}")
        print(f"  {text[:200]}...")
```

## 5. Letting the Agent Search Archival Memory

The agent can call `archival_memory_search` as a tool during conversation:

```python
# Ask the agent a question that requires searching archival memory

response = client.agents.messages.create(
    AGENT_ID,
    input="What do we know about Anthropic's latest model release? Check the knowledge base."
)

# Show the agent's process — it should call archival_memory_search first
for msg in response.messages:
    msg_type = getattr(msg, 'message_type', getattr(msg, 'role', '?'))
    
    # Show tool calls
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"🔧 Tool Call: {tc.function.name}")
            args = tc.function.arguments[:250]
            print(f"   Args: {args}")
    
    # Show tool results
    if msg_type == 'tool' or hasattr(msg, 'name'):
        name = getattr(msg, 'name', 'tool')
        content = getattr(msg, 'content', '')
        print(f"📦 Tool Result [{name}]: {str(content)[:200]}")
    
    # Show assistant messages
    if msg_type == 'assistant' and hasattr(msg, 'content') and msg.content:
        text = msg.content if isinstance(msg.content, str) else str(msg.content)
        print(f"💬 Assistant: {text[:500]}")
```

## 6. Agent-Driven Insertion — Letting the Agent Save Knowledge

When the agent learns something new, it should save it to archival memory
for future reference.

```python
# Give the agent new information and ask it to remember

response = client.agents.messages.create(
    AGENT_ID,
    input=(
        "I just read that Tesla's Optimus humanoid robot started production in June 2026, "
        "with an initial run of 1,000 units for factory automation at $20,000 each. "
        "Please save this to our knowledge base for future reference."
    )
)

# Check if the agent called archival_memory_insert
for msg in response.messages:
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            if 'archival' in tc.function.name.lower():
                print(f"✓ Agent called: {tc.function.name}")
                print(f"  Content: {tc.function.arguments[:300]}")
    if hasattr(msg, 'content') and msg.content:
        text = msg.content if isinstance(msg.content, str) else str(msg.content)
        if text.strip():
            print(f"💬 {text[:300]}")

# Verify it was saved
print("\n" + "="*60)
print("Searching for the new knowledge...")
results = search_archival(AGENT_ID, "Tesla Optimus robot production", limit=2)
for r in results:
    print(f"  Found: {getattr(r, 'text', str(r))[:200]}...")
```

## 7. Metadata-Filtered Search

Search with metadata filters to narrow results:

```python
# Search only for funding-related passages

funding_results = client.agents.passages.search(
    AGENT_ID,
    query="company investments and funding rounds",
    limit=5,
    # Optional: metadata filter
    # metadata_filters={"type": "funding"}
)

print("Funding-related passages:")
for passage in funding_results:
    metadata = getattr(passage, 'metadata', {})
    text = getattr(passage, 'text', str(passage))
    if metadata.get('type') == 'funding':
        print(f"  • [{metadata.get('company')}] {text[:150]}...")

# List ALL passages with their metadata
print("\n\nAll passages in archival memory:")
all_passages = client.agents.passages.list(AGENT_ID, limit=20)
for p in all_passages:
    metadata = getattr(p, 'metadata', {})
    text_preview = getattr(p, 'text', str(p))[:80].replace('\n', ' ')
    print(f"  [{metadata.get('type', '?')}] {metadata.get('company', '?'):12s} | {text_preview}...")
```

## 8. Bulk Insertion — Seeding a Knowledge Base

For production systems, you often need to seed the knowledge base from
existing documents:

```python
def seed_knowledge_base(agent_id: str, documents: list[dict]):
    """
    Bulk-insert passages into archival memory.
    
    Each document should have:
        - text: The passage content
        - metadata: Dict of metadata (source, date, tags, etc.)
    
    For large datasets, batch and add rate limiting.
    """
    import time
    
    inserted = 0
    errors = 0
    
    for doc in documents:
        try:
            client.agents.passages.create(
                agent_id,
                text=doc["text"],
                metadata=doc.get("metadata", {})
            )
            inserted += 1
        except Exception as e:
            print(f"Error inserting: {doc.get('text', '')[:50]}... → {e}")
            errors += 1
        
        # Rate limiting for large batches (100/minute for Letta Cloud free tier)
        if inserted % 50 == 0:
            print(f"  Inserted {inserted} passages...")
            time.sleep(1)
    
    print(f"Done: {inserted} inserted, {errors} errors")
    return inserted

# Example: seed with industry reports
industry_docs = [
    {
        "text": "The global AI market is projected to reach $1.8 trillion by 2030, "
                "growing at a CAGR of 37.3% from 2025. Key drivers: generative AI adoption, "
                "enterprise automation, and AI-native startups.",
        "metadata": {"source": "Industry Report 2026", "type": "market_research",
                     "topic": "AI market size"}
    },
    {
        "text": "Vector databases market: Pinecone ($3.5B), Weaviate ($2.1B), "
                "Milvus/Zilliz ($1.6B), Qdrant ($1.2B), Chroma ($800M). "
                "Key trend: shift from standalone DBs to embedded solutions.",
        "metadata": {"source": "DB Market Report Q2 2026", "type": "market_research",
                     "topic": "vector databases"}
    },
    {
        "text": "Agent frameworks market share (Q2 2026): LangGraph 34%, "
                "CrewAI 22%, AutoGen 18%, Letta 12%, Others 14%. "
                "Fastest growing: Letta (+85% YoY) driven by persistent memory demand.",
        "metadata": {"source": "AI Engineer Survey 2026", "type": "market_research",
                     "topic": "agent frameworks"}
    },
]

# seed_knowledge_base(AGENT_ID, industry_docs)
```

## 9. Deleting Passages — Memory Hygiene

Old or incorrect knowledge should be removed:

```python
# Get all passages
all_passages = client.agents.passages.list(AGENT_ID, limit=100)

# Delete a specific passage by ID
# client.agents.passages.delete(AGENT_ID, passage_id="passage-abc123")

# Or delete all passages (fresh start)
# for p in all_passages:
#     client.agents.passages.delete(AGENT_ID, p.id)
# print(f"Deleted {len(all_passages)} passages")

# Count by type
from collections import Counter
types = Counter()
for p in all_passages:
    md = getattr(p, 'metadata', {})
    if isinstance(md, dict):
        types[md.get('type', 'unknown')] += 1

print("Passage types distribution:")
for t, count in types.most_common():
    print(f"  {t}: {count}")
```

## 10. Archival Memory Best Practices

### DO:
- ✅ Use descriptive metadata (source, date, tags, type)
- ✅ Keep passages focused — 1-3 sentences each for granular retrieval
- ✅ Let the agent insert important facts during conversation
- ✅ Seed with existing documentation for immediate value
- ✅ Periodically review and remove outdated passages

### DON'T:
- ❌ Store entire documents as single passages (chunk them!)
- ❌ Use archival memory for ephemeral state (use memory blocks instead)
- ❌ Forget to include embedding model during agent creation
- ❌ Skip metadata — filted search is much faster than pure semantic

### Passage Chunking Guide:
| Content Type | Ideal Passage Size |
|-------------|-------------------|
| Facts / definitions | 50-200 chars |
| News / updates | 200-500 chars |
| Tutorials / how-tos | 500-1000 chars |
| Research summaries | 300-800 chars |

## 11. Cleanup

```python
Clean up this notebook's agent
client.agents.delete(AGENT_ID)
print(f"Agent {AGENT_ID} deleted.")
```

## Key Takeaways

1. **Archival memory = vector DB** — unlimited storage, semantic search.
2. **Passages are the unit** — small text chunks with metadata.
3. **Agent can both read AND write** — it searches when asked, inserts when it learns.
4. **Metadata matters** — enables filtered search and content management.
5. **Chunk your content** — 200-800 char passages work best for retrieval.

→ Next: `05_tools_and_functions.ipynb` — custom tools and function calling.
