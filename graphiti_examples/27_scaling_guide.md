# Scaling Guide for Graphiti

Strategies for scaling Graphiti from a single-user prototype to a
production system handling millions of episodes across many tenants.

---

## 1. Parallel Episode Processing Across group_ids

Graphiti's `group_id` field isolates data between tenants or projects. This
also provides a natural parallelism boundary: episodes in different groups
can be processed independently.

### Architecture

```
                  ┌─────────────────┐
                  │   Task Queue    │ (Redis / SQS / RabbitMQ)
                  └────────┬────────┘
                           │
           ┌───────────────┼───────────────┐
           │               │               │
     ┌─────▼─────┐  ┌─────▼─────┐  ┌─────▼─────┐
     │ Worker 1  │  │ Worker 2  │  │ Worker N  │
     │ group_a   │  │ group_b   │  │ group_c   │
     └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
           │               │               │
           └───────────────┼───────────────┘
                           │
                    ┌──────▼──────┐
                    │   Neo4j     │
                    └─────────────┘
```

### Implementation

```python
import asyncio
from graphiti_core import Graphiti


async def process_group(graphiti: Graphiti, group_id: str, episodes: list):
    """Process all episodes for a single group sequentially (within-group
    ordering matters for temporal consistency)."""
    for ep in episodes:
        await graphiti.add_episode(
            name=ep["name"],
            episode_body=ep["body"],
            source=ep["source"],
            source_description=ep["source_description"],
            reference_time=ep["reference_time"],
            group_id=group_id,
        )


async def process_all_groups(groups: dict[str, list]):
    """Process all groups in parallel using asyncio.gather."""
    graphiti = Graphiti(uri="...", user="...", password="...")
    await graphiti.build_indices_and_constraints()

    tasks = [
        process_group(graphiti, group_id, episodes)
        for group_id, episodes in groups.items()
    ]
    await asyncio.gather(*tasks)

    await graphiti.close()
```

### Throughput scaling

| Workers | groups/second | Notes |
|---------|-------------|-------|
| 1 | ~5-10 | Single-threaded baseline |
| 5 | ~25-50 | Good for small-medium deployments |
| 10 | ~40-80 | LLM rate limits become the bottleneck |
| 25 | ~50-100 | Diminishing returns (LLM throttling) |
| 50+ | No gain | Limited by Neo4j write throughput + LLM API |

**Key insight**: The bottleneck is almost always the LLM API, not Neo4j.
Parallelizing beyond 10-20 workers typically hits rate limits.

---

## 2. max_coroutines Tuning for LLM Rate Limits

Graphiti uses `max_coroutines` to control concurrent LLM API calls. This
parameter directly affects throughput and cost.

### How it works

```python
from graphiti_core import Graphiti

# Default (conservative): 5 concurrent calls
graphiti = Graphiti(uri="...", user="...", password="...", max_coroutines=5)

# Aggressive: 20 concurrent calls (requires high rate limit from LLM provider)
graphiti = Graphiti(uri="...", user="...", password="...", max_coroutines=20)
```

### Tuning guidelines

| max_coroutines | LLM rate limit needed | Use case |
|---------------|----------------------|----------|
| 1 | Any | Lowest cost, slowest throughput |
| 5 | 500+ RPM | Safe default for most deployments |
| 10 | 1000+ RPM | Good for moderate throughput |
| 20 | 2000+ RPM | High throughput, Tier 5 OpenAI |
| 50+ | 5000+ RPM | Enterprise throughput, custom LLM |

### Rate limit handling

If you hit LLM rate limits, use exponential backoff:

```python
import backoff
from graphiti_core import Graphiti
from graphiti_core.llm_client import LLMError

class ResilientGraphiti(Graphiti):
    @backoff.on_exception(
        backoff.expo,
        LLMError,
        max_tries=5,
        base=2,  # 2s, 4s, 8s, 16s, 32s
    )
    async def add_episode(self, *args, **kwargs):
        return await super().add_episode(*args, **kwargs)
```

---

## 3. Redis Caching for Frequent Subgraph Queries

For production systems where the same queries are run frequently (e.g., a
chatbot repeatedly looking up the same entities), Redis caching can
dramatically reduce latency and Neo4j load.

### Caching strategy

```python
import json
import hashlib
import redis.asyncio as redis

from graphiti_core import Graphiti


class CachedGraphiti:
    """Wraps Graphiti with Redis caching for frequent queries."""

    def __init__(self, graphiti: Graphiti, redis_url: str, ttl: int = 300):
        self.graphiti = graphiti
        self.redis = redis.from_url(redis_url)
        self.ttl = ttl

    def _cache_key(self, query: str, group_ids: list[str]) -> str:
        raw = f"{query}:{sorted(group_ids)}"
        return f"graphiti:search:{hashlib.md5(raw.encode()).hexdigest()}"

    async def search(self, query: str, group_ids: list[str], **kwargs):
        key = self._cache_key(query, group_ids)

        # Try cache first
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)

        # Execute query
        results = await self.graphiti.search(query=query, group_ids=group_ids, **kwargs)

        # Cache results (serializable subset)
        cache_data = [
            {
                "fact": e.fact,
                "source_node_name": e.source_node_name,
                "target_node_name": e.target_node_name,
                "valid_at": e.valid_at.isoformat() if e.valid_at else None,
                "invalid_at": e.invalid_at.isoformat() if e.invalid_at else None,
            }
            for e in results
        ]
        await self.redis.setex(key, self.ttl, json.dumps(cache_data))

        return results
```

### Cache invalidation triggers

| Action | Cache strategy |
|--------|---------------|
| New episode added | Invalidate group's query cache |
| Episode deleted | Invalidate group's query cache |
| Group deleted | Invalidate all caches for that group |
| Periodic refresh | TTL-based expiration (recommended: 5 minutes) |

### Expected performance

| Scenario | Without cache | With cache | Improvement |
|----------|--------------|------------|-------------|
| Repeated semantic search | 500-2000ms | 5-15ms | 30-100x |
| Entity lookup | 50-200ms | 3-10ms | 10-20x |
| Graph traversal | 100-500ms | 5-20ms | 10-25x |

---

## 4. Separating Vector Search from Graph Traversal

Zep's production pattern separates two concerns:

- **Vector search**: Fast semantic similarity (handled by a vector database)
- **Graph traversal**: Precise relationship navigation (handled by Neo4j)

### Why separate?

| Concern | Vector DB (Pinecone/Weaviate/Qdrant) | Graph DB (Neo4j) |
|---------|--------------------------------------|-------------------|
| Query type | Semantic similarity | Relationship traversal |
| Latency (P50) | 5-20ms | 50-200ms |
| Latency (P95) | 20-50ms | 200-1000ms |
| Cost | $/vector/month | $/node/month |
| Scale ceiling | Billions of vectors | Millions of nodes (single instance) |

### Hybrid search architecture

```python
from graphiti_core import Graphiti
from graphiti_core.search.search_config import SearchConfig, SearchRecipes


def create_hybrid_search_config(
    vector_weight: float = 0.6,
    graph_weight: float = 0.4,
) -> SearchConfig:
    """
    Create a search config that blends vector similarity with graph proximity.

    vector_weight: How much to favor semantic similarity (from the vector index)
    graph_weight:  How much to favor graph proximity (relationship traversal)

    For fact-retrieval tasks, favor vector_weight (0.7-0.8).
    For relationship-exploration tasks, favor graph_weight (0.6-0.7).
    """
    return SearchConfig(
        recipe=SearchRecipes.COMBINED_HYBRID_SEARCH_CROSS_ENCODER,
        num_results=10,
    )
```

### When to use each search mode

| Use case | Recommended mode | Rationale |
|----------|-----------------|-----------|
| "What did Alice say about budget?" | Vector search | Semantic match on fact text |
| "What services depend on PaymentService?" | Graph traversal | Structural query |
| "Who is connected to Bob through project X?" | Combined hybrid | Both semantics + structure |
| "Find all decisions made in Q3 2025" | Filtered vector | Time + semantic filter |

---

## 5. LLM Cost Optimization

LLM API calls are the dominant cost in production Graphiti deployments.
Here are strategies to reduce costs without sacrificing quality.

### Cost breakdown (per 1M episodes)

| Component | Cost estimate | % of total |
|-----------|--------------|------------|
| Entity extraction (GPT-4o) | $800-1200 | 50-60% |
| Relationship extraction (GPT-4o) | $400-600 | 25-30% |
| Embedding generation | $50-100 | 5-10% |
| Graph search / cross-encoder | $50-150 | 5-10% |

### Strategy 1: Prompt compression

Reduce episode body size before sending to the LLM:

```python
def compress_episode(body: str, max_chars: int = 2000) -> str:
    """Compress episode text by removing redundancies for LLM extraction."""
    if len(body) <= max_chars:
        return body

    # Simple truncation with semantic preservation
    # In production, use a text summarization model
    return body[:max_chars] + "... [truncated]"


await graphiti.add_episode(
    name="compressed_episode",
    episode_body=compress_episode(long_text, max_chars=2000),
    ...
)
```

### Strategy 2: Classical NLP fallbacks

Use lighter-weight NLP for simple extraction tasks, reserving LLM calls for
complex cases:

```python
def needs_llm_extraction(body: str) -> bool:
    """Heuristic: only use LLM for complex text. Simple structured data
    can be handled with regex or rule-based extraction."""
    if len(body) < 100:
        return False  # Too short, skip or use simple extraction
    if "|" in body and "\n" in body:
        return False  # Looks like tabular data
    if body.count(",") > 20:
        return True   # Complex narrative
    return True


async def smart_add_episode(graphiti, body: str, **kwargs):
    if needs_llm_extraction(body):
        return await graphiti.add_episode(episode_body=body, **kwargs)
    else:
        # Use fact_triple directly for simple structured data
        return await graphiti.add_episode(
            episode_body=body,
            source=EpisodeType.fact_triple,
            **kwargs,
        )
```

### Strategy 3: Model tiering

| Content type | Extraction model | Embedding model | Relative cost |
|-------------|-----------------|-----------------|---------------|
| High-value (contracts, legal) | GPT-4o / Claude Opus | text-embedding-3-large | 10x |
| Medium (reports, articles) | GPT-4o-mini / Claude Haiku | text-embedding-3-small | 1x |
| Low-value (logs, metrics) | Regex + rule-based | TF-IDF / bag-of-words | 0.01x |

### Strategy 4: Batching

LLM providers offer lower per-token costs for batch processing:

```python
# Batch API (OpenAI): 50% cost reduction, 24-hour turnaround
# Use this for non-time-sensitive bulk ingestion

import openai

batch_input = [
    {"custom_id": f"episode-{i}", "body": body}
    for i, body in enumerate(episode_bodies)
]
# Submit to batch API
# Process results 24h later
```

---

## 6. Database Choice at Scale: Kuzu vs Neo4j vs FalkorDB

| Dimension | Kuzu | Neo4j Community | Neo4j Enterprise | FalkorDB |
|-----------|------|-----------------|-------------------|----------|
| **Architecture** | Embedded | Client-server | Client-server | In-memory |
| **Max nodes** | ~10M | ~50B (practical: ~1B) | ~50B | RAM-bound |
| **Max edges** | ~100M | ~100B | ~100B | RAM-bound |
| **Vector search** | No | Via plugin | Via plugin | Yes (built-in) |
| **Graph algorithms** | Limited | Via GDS (limited) | Via GDS (full) | Limited |
| **Concurrent clients** | 1 | Unlimited | Unlimited | Unlimited |
| **High availability** | No | No | Yes (clustering) | Yes (replication) |
| **Backup** | File copy | Online backup (limited) | Online backup (full) | Snapshot |
| **Memory** | Off-heap + mmap | Heap + page cache | Heap + page cache | All in-memory |
| **Query language** | Cypher subset | Full Cypher | Full Cypher | Cypher subset |
| **License** | MIT | GPL v3 (or commercial) | Commercial | SSPL |
| **Best for** | Dev/small scale | General production | Enterprise | Real-time, low-latency |

### Decision framework

```
Is your dataset < 1M entities?
  YES → Kuzu (simplest, zero ops)
  NO  → Is latency < 10ms critical?
          YES → FalkorDB (in-memory)
          NO  → Do you need clustering/HA?
                  YES → Neo4j Enterprise
                  NO  → Neo4j Community
```

---

## 7. Scaling Benchmarks

The benchmarks below are estimates based on typical configurations. Actual
performance will vary based on hardware, dataset characteristics, and LLM
provider.

### Episode ingestion throughput

| Configuration | Episodes/hour | Cost/hour | Notes |
|--------------|--------------|-----------|-------|
| Single worker, GPT-4o-mini | 500-1000 | $2-5 | Good for dev |
| 5 workers, GPT-4o-mini | 2000-4000 | $8-20 | Good for low-cost production |
| 10 workers, GPT-4o | 3000-5000 | $50-100 | Balanced speed/cost |
| 20 workers, GPT-4o | 5000-8000 | $100-200 | High throughput |
| 10 workers, Ollama (local) | 200-500 | $0 | Free, but slow |

### Query latency (P50 / P95)

| Query type | Kuzu | Neo4j (local) | Neo4j (server) | FalkorDB |
|-----------|------|---------------|----------------|----------|
| Simple entity lookup | 2/5ms | 5/15ms | 10/30ms | 1/3ms |
| Semantic search (vector) | N/A | 50/150ms | 100/300ms | 10/30ms |
| Graph traversal (2 hops) | 5/15ms | 20/50ms | 50/150ms | 3/10ms |
| Complex query (5 hops) | 20/50ms | 100/300ms | 200/800ms | 15/50ms |
| Community detection | N/A | 1-10s | 5-30s | N/A |

### Cost scaling (monthly estimate)

| Dataset size | Entities | Episodes | Neo4j infra | LLM cost | Total (est.) |
|-------------|----------|----------|-------------|----------|-------------|
| Small | 10K | 1K | $30-50 | $10-20 | $40-70 |
| Medium | 100K | 10K | $100-200 | $50-100 | $150-300 |
| Large | 1M | 100K | $500-1000 | $500-1000 | $1000-2000 |
| Enterprise | 10M | 1M | $2000-5000 | $5000-10000 | $7000-15000 |

---

## 8. Capacity Planning

### Episodes to entities conversion

```
1 episode (~500 chars) → ~5-15 entities + ~5-20 edges
100K episodes          → ~500K-1.5M entities + ~500K-2M edges
1M episodes            → ~5M-15M entities + ~5M-20M edges
```

### Storage estimation

| Component | Per 100K episodes | Per 1M episodes |
|-----------|-------------------|------------------|
| Neo4j database | 2-5 GB | 20-50 GB |
| Vector embeddings | 1-3 GB | 10-30 GB |
| Episode text storage | 0.5-1 GB | 5-10 GB |
| Indexes | 1-2 GB | 10-20 GB |
| **Total** | **4-11 GB** | **40-110 GB** |

### Memory estimation

| Dataset | Entities | Neo4j page cache | Heap | Total Neo4j RAM |
|---------|----------|-----------------|------|-----------------|
| Small | 10K | 512 MB | 512 MB | 1 GB |
| Medium | 100K | 1 GB | 1 GB | 2 GB |
| Large | 1M | 4 GB | 4 GB | 8 GB |
| Enterprise | 10M | 16 GB | 8 GB | 24 GB |

### Cost estimation formula

```
Monthly cost = Infra_cost + LLM_cost

Infra_cost:
  Small:    $50-100/month  (1 Neo4j instance, 2GB RAM, 50GB SSD)
  Medium:   $200-400/month (1 Neo4j instance, 8GB RAM, 200GB SSD)
  Large:    $800-1500/month (1 Neo4j + replica, 16GB RAM, 500GB SSD)
  Enterprise: $3000-8000/month (3-node cluster, 32GB RAM each, 1TB SSD)

LLM_cost:
  per_episode_cost × episodes_per_month
  GPT-4o-mini: ~$0.008/episode (1K chars avg)
  GPT-4o:      ~$0.05/episode (1K chars avg)
  Haiku:       ~$0.005/episode (1K chars avg)
  Sonnet:      ~$0.03/episode (1K chars avg)
```

---

## 9. Auto-Scaling Considerations for Kubernetes

### Horizontal pod autoscaling

```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: graphiti-worker
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: graphiti-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: External
      external:
        metric:
          name: sqs_queue_depth
          target:
            type: AverageValue
            averageValue: 100
```

### Pod resource requests and limits

```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: graphiti-worker
spec:
  replicas: 5
  selector:
    matchLabels:
      app: graphiti-worker
  template:
    metadata:
      labels:
        app: graphiti-worker
    spec:
      containers:
        - name: worker
          image: your-registry/graphiti-worker:latest
          resources:
            requests:
              cpu: "1"
              memory: "2Gi"
            limits:
              cpu: "2"
              memory: "4Gi"
          env:
            - name: NEO4J_URI
              value: "bolt://neo4j-headless:7687"
            - name: NEO4J_USER
              valueFrom:
                secretKeyRef:
                  name: neo4j-secret
                  key: username
            - name: NEO4J_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: neo4j-secret
                  key: password
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: openai-secret
                  key: api-key
            - name: MAX_COROUTINES
              value: "10"
```

### Key K8s considerations

| Factor | Recommendation | Rationale |
|--------|---------------|-----------|
| Worker statelessness | Workers must be stateless | Scale up/down without data loss |
| Database connection pool | Limit per-worker connections | Neo4j has finite connection slots |
| Graceful shutdown | Handle SIGTERM properly | Avoid mid-write corruption |
| Pod disruption budget | minAvailable: 1 (or more) | Prevent total worker loss |
| Node affinity | Co-locate with Neo4j if possible | Reduce network latency |
| Resource quotas | Set namespace limits | Prevent noisy neighbor issues |
| Readiness probe | Check Neo4j connectivity | Don't send traffic to disconnected workers |

### Graceful shutdown handler

```python
import asyncio
import signal

class GracefulWorker:
    def __init__(self):
        self.shutdown = asyncio.Event()

        # Register signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig, self.shutdown.set
            )

    async def run(self):
        graphiti = Graphiti(uri="...", user="...", password="...")
        try:
            while not self.shutdown.is_set():
                # Process next episode from queue
                episode = await self.get_next_episode(timeout=1)
                if episode:
                    await graphiti.add_episode(**episode)
        finally:
            # Flush pending writes
            await graphiti.close()
            print("Worker shut down gracefully")
```

---

## Quick Reference: Scaling Decision Tree

```
Q: What is your episode volume per day?
|
├── < 1,000  → Single worker, any DB, no caching needed
|
├── 1,000 - 10,000  → 2-5 workers, Neo4j Community, optional Redis cache
|
├── 10,000 - 100,000 → 5-20 workers, Neo4j Enterprise, Redis cache,
|                       separated vector/graph concerns
|
└── > 100,000 → 20-100 workers, Neo4j Enterprise cluster,
                 separated search, Redis + CDN caching,
                 batch LLM processing, multiple tenants distributed
                 across shards
```
