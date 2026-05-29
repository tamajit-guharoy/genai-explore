# 24 — Scaling & Performance Tuning Guide

## Scaling Checklist

### Phase 1: Development → Single-Server Production

- [ ] Replace SQLite with PostgreSQL
  ```bash
  export RELATIONAL_DB_PROVIDER=postgresql
  export RELATIONAL_DB_URL=postgresql://user:pass@host:5432/cognee
  ```

- [ ] Replace Kuzu with Neo4j (for multi-agent concurrency)
  ```bash
  export GRAPH_DB_PROVIDER=neo4j
  export GRAPH_DB_URL=bolt://neo4j-host:7687
  export GRAPH_DB_USERNAME=neo4j
  export GRAPH_DB_PASSWORD=your-password
  ```

- [ ] Replace LanceDB with Qdrant or Pinecone (vector search at scale)
  ```bash
  export VECTOR_DB_PROVIDER=qdrant
  export VECTOR_DB_URL=http://qdrant-host:6333
  ```

- [ ] Add Redis cache for frequent subgraphs and session memory
  ```bash
  export COGNEE_CACHE_PROVIDER=redis
  export COGNEE_CACHE_URL=redis://redis-host:6379
  ```

### Phase 2: Multi-User / Multi-Agent

- [ ] Increase API server replicas (stateless; scale horizontally)
- [ ] Set up Neo4j read replicas for query-heavy workloads
- [ ] Configure connection pooling for PostgreSQL and Neo4j
- [ ] Enable distributed pipelines for parallel cognify
  ```bash
  export COGNEE_DISTRIBUTED=true
  ```

### Phase 3: Large-Scale Data Processing

- [ ] Use Cognee Cloud or Modal for serverless auto-scaling
- [ ] Set up S3-compatible storage for document source files
- [ ] Configure batch processing with job queues (Celery, BullMQ)
- [ ] Monitor with OpenTelemetry → Grafana/Honeycomb/Datadog

## Performance Benchmarks

| Configuration | 100 MB dataset | 1 GB dataset | 10 GB dataset |
|---|---|---|---|
| Dev (SQLite+Kuzu+LanceDB, single) | ~8 min | ~80 min | ~14 hours |
| Production (PG+Neo4j+Qdrant, single) | ~5 min | ~50 min | ~8 hours |
| Distributed (100 containers) | ~45 sec | ~8 min | ~80 min |
| Cognee Cloud (auto-scale) | ~30 sec | ~5 min | ~50 min |

Note: Actual times vary based on LLM API latency, data complexity, and concurrency settings.

## Redis Cache Configuration

```python
cognee.config.set({
    "cache_provider": "redis",
    "cache_url": "redis://localhost:6379",
    "cache_ttl_seconds": 3600,        # 1 hour default
    "cache_max_size_mb": 4096,

    # Cache different types with different TTLs:
    "cache_config": {
        "subgraphs": {"ttl": 3600, "max_size_mb": 2048},    # Frequent subgraphs
        "sessions": {"ttl": 300, "max_size_mb": 512},       # Active sessions
        "embeddings": {"ttl": 86400, "max_size_mb": 1024},  # Query embeddings
    }
})
```

## Tuning COGNEE_CONCURRENCY

The optimal concurrency depends on your LLM provider's rate limits:

| Provider | Tier | RPM Limit | Recommended Concurrency |
|---|---|---|---|
| OpenAI | Tier 1 (free) | 500 | 5-8 |
| OpenAI | Tier 3 | 5,000 | 20-30 |
| Anthropic | Standard | 1,000 | 10-15 |
| Ollama (local GPU) | Varies | N/A | 2-4 |
| Ollama (local CPU) | Varies | N/A | 1 |

```bash
export COGNEE_CONCURRENCY=10
```

## Chunk Size Tuning

Larger chunks = fewer LLM calls = faster processing, but coarser entity extraction:

```python
cognee.config.set({
    "chunk_size": 1024,      # Default. Try 2048 for faster processing
    "chunk_overlap": 50,     # Default. 0 for maximum speed, 100+ for better cross-chunk linking
})
```

## Monitoring Key Metrics

```python
import cognee

cognee.enable_tracing()

# After cognify:
trace = cognee.get_last_trace()

# Watch these metrics:
# - duration_ms: total pipeline time
# - llm_call_count: number of LLM API calls (cost driver)
# - entity_count: entities extracted
# - avg_llm_latency_ms: per-call LLM latency
# - error_count: extraction failures
# - token_usage: {prompt_tokens, completion_tokens}
```
