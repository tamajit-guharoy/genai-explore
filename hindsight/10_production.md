# 10. Production Deployment

Running Hindsight in production requires careful configuration of PostgreSQL,
vector extensions, connection pooling, monitoring, and security.

---

## Deployment Topology

```
                    ┌─────────────┐
                    │  Your Agent  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Load      │
                    │  Balancer   │
                    └──┬───┬───┬──┘
                       │   │   │
              ┌────────▼───▼───▼────────┐
              │   Hindsight API (×N)     │
              │   Workers (×N)           │
              └──────────┬──────────────┘
                         │
              ┌──────────▼──────────┐
              │  PostgreSQL Primary  │
              │  + pgvector/pgvs     │
              └──────────┬──────────┘
                         │
              ┌──────────▼──────────┐
              │  Read Replica(s)     │
              │  (recall offload)    │
              └─────────────────────┘
```

---

## Docker Production Setup

### Docker Compose with External PostgreSQL

```yaml
# docker-compose.prod.yml
version: "3.8"

services:
  hindsight-api:
    image: ghcr.io/vectorize-io/hindsight-api:latest
    restart: unless-stopped
    ports:
      - "8888:8888"
    environment:
      # Database
      HINDSIGHT_API_DATABASE_URL: postgresql://hindsight:${DB_PASSWORD}@postgres:5432/hindsight
      HINDSIGHT_API_READ_DATABASE_URL: postgresql://hindsight:${DB_PASSWORD}@postgres-read:5432/hindsight

      # LLM
      HINDSIGHT_API_LLM_PROVIDER: ${LLM_PROVIDER:-openai}
      HINDSIGHT_API_LLM_API_KEY: ${LLM_API_KEY}
      HINDSIGHT_API_LLM_MODEL: ${LLM_MODEL:-gpt-4o-mini}

      # Vector extension (pgvectorscale recommended for scale)
      HINDSIGHT_API_VECTOR_EXTENSION: pgvectorscale

      # Worker identity (STABLE — not container hostname!)
      HINDSIGHT_API_WORKER_ID: hindsight-api-prod

      # Pooling
      HINDSIGHT_API_DB_POOL_MIN_SIZE: 10
      HINDSIGHT_API_DB_POOL_MAX_SIZE: 50
      HINDSIGHT_API_LLM_MAX_CONCURRENT: 32

      # Logging
      HINDSIGHT_API_LOG_LEVEL: info
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8888/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 2G
          cpus: "2"
        reservations:
          memory: 1G
          cpus: "1"

  postgres:
    image: pgvector/pgvector:pg17
    restart: unless-stopped
    environment:
      POSTGRES_USER: hindsight
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: hindsight
    volumes:
      - pgdata:/var/lib/postgresql/data
    # PostgreSQL config for memory-heavy workloads
    command: |
      -c shared_buffers=2GB
      -c effective_cache_size=6GB
      -c maintenance_work_mem=512MB
      -c max_connections=200
      -c work_mem=64MB
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hindsight"]
      interval: 10s
      timeout: 5s
      retries: 5

  postgres-read:
    image: pgvector/pgvector:pg17
    # ... read replica configuration
    # Offloads recall queries from primary

volumes:
  pgdata:

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

---

## PostgreSQL Configuration

### Recommended extensions

```sql
-- On primary and replicas
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS vectorscale CASCADE;  -- For pgvectorscale (10M+ vectors)
CREATE EXTENSION IF NOT EXISTS pg_trgm;               -- For text search
```

### Tuning for Hindsight

```ini
# postgresql.conf optimizations for Hindsight

# Memory (adjust based on available RAM)
shared_buffers = 4GB          # 25% of system RAM
effective_cache_size = 12GB   # 75% of system RAM
maintenance_work_mem = 1GB
work_mem = 128MB              # Per-operation sort memory

# Connections
max_connections = 200
# Ensure pool_max + superuser_reserved < max_connections

# WAL (for write-heavy workloads)
wal_level = replica
max_wal_size = 10GB
min_wal_size = 2GB
checkpoint_timeout = 15min

# Query planning
random_page_cost = 1.1        # Lower if on SSD
effective_io_concurrency = 200

# Autovacuum (critical for Hindsight — many writes)
autovacuum_max_workers = 5
autovacuum_naptime = 30s
autovacuum_vacuum_scale_factor = 0.05
autovacuum_analyze_scale_factor = 0.025
```

---

## Vector Extension Selection

| Extension | Best for | Notes |
|-----------|----------|-------|
| `pgvector` (HNSW) | <10M vectors, simple setup | Default, good enough for most |
| `pgvectorscale` (DiskANN) | 10M+ vectors | 28× lower p95 latency, 16× higher throughput |
| `vchord` (vchordrq) | 3000+ dimensional vectors | Includes BM25 search |
| `scann` (AlloyDB) | Google AlloyDB users | Single global index |

Set via:
```bash
export HINDSIGHT_API_VECTOR_EXTENSION=pgvectorscale
```

**Switching extensions**: With existing data, you can only switch to `scann`.
Other switches require an empty database (recreated on startup).

---

## Monitoring

### Prometheus Metrics

Hindsight exposes Prometheus metrics at `GET /metrics`:

```yaml
# prometheus scrape config
scrape_configs:
  - job_name: "hindsight"
    scrape_interval: 15s
    static_configs:
      - targets: ["hindsight-api:8888"]
```

Key metrics:
- `hindsight_retain_requests_total` — Retain call count
- `hindsight_retain_duration_seconds` — Retain latency histogram
- `hindsight_recall_requests_total` — Recall call count
- `hindsight_recall_duration_seconds` — Recall latency histogram
- `hindsight_llm_requests_total` — LLM call count
- `hindsight_db_pool_connections` — DB connection pool status
- `hindsight_pending_operations` — Pending background operations
- `hindsight_failed_operations_total` — Failed background operations

### Health Endpoints

```bash
# Basic health
curl http://localhost:8888/health
# → {"status": "ok"}

# Version + feature flags
curl http://localhost:8888/version
# → {"api_version": "0.8.3", "features": {...}}

# Bank-level LLM health
curl -X POST http://localhost:8888/v1/default/banks/my-bank/health/llm
# → {"retain": "ok", "consolidation": "ok", "reflect": "ok"}
```

---

## Scaling

### Horizontal Scaling

Hindsight API servers are stateless — scale horizontally:

```bash
# Run multiple API instances behind a load balancer
docker compose up --scale hindsight-api=4
```

### Read Replicas

Offload `recall()` queries to replicas:

```bash
export HINDSIGHT_API_READ_DATABASE_URL=postgresql://user:***@read-replica:5432/hindsight
```

### Worker Identity

**Critical**: Set a stable `HINDSIGHT_API_WORKER_ID` per instance (not the container
hostname). On restart, tasks claimed under the old ID become orphaned:

```bash
export HINDSIGHT_API_WORKER_ID=hindsight-worker-1  # Stable identity
```

---

## Recovering Stuck Operations

If operations become stuck (e.g., from worker crash during async retain):

```bash
# Admin CLI
hindsight-admin list-stuck-operations --bank-id my-bank
hindsight-admin retry-stuck-operation --bank-id my-bank --operation-id op_abc123
hindsight-admin retry-all-stuck --bank-id my-bank
```

---

## Security

### API Authentication

```bash
# Set an API key
export HINDSIGHT_API_KEY=your-secret-key

# Clients must send:
# Authorization: Bearer your-secret-key
```

Client:
```python
client = Hindsight(
    base_url="http://localhost:8888",
    api_key="your-secret-key"
)
```

### Network Isolation

```bash
# Bind to localhost only
export HINDSIGHT_API_HOST=127.0.0.1

# Or use a reverse proxy (nginx, Caddy, Traefik) with TLS
```

### Database Security

```bash
# Use SSL for PostgreSQL connections
export HINDSIGHT_API_DATABASE_URL=postgresql://user:***@host:5432/hindsight?sslmode=require
```

---

## Backup & Recovery

### PostgreSQL Backup

```bash
# pg_dump
pg_dump -h localhost -U hindsight hindsight > backup.sql

# Or continuous backup with WAL archiving
# (configure archive_command in postgresql.conf)
```

### Hindsight Export

Hindsight supports document export if the feature flag is enabled:

```bash
# Check if export is available
curl http://localhost:8888/version | jq '.features.document_export_api'
```

---

## Cost Optimization

### LLM Model Selection

| Use Case | Recommended Model | Why |
|----------|-------------------|-----|
| Retain (fact extraction) | `gpt-4o-mini` or `claude-haiku` | Many small calls, cheap model works well |
| Consolidation | `gpt-4o-mini` or `gemini-flash` | Batch processing |
| Reflect (reasoning) | `gpt-4o` or `claude-sonnet` | Complex reasoning benefits from better models |

Set per-operation models:
```bash
export HINDSIGHT_API_LLM_MODEL=gpt-4o-mini       # Default for retain/consolidation
# Reflect uses the same model by default; for budget optimization,
# use LiteLLM router to direct different operations to different models
```

### Slim Image

For lower memory footprint, use the slim image (500MB vs 9GB):

```bash
docker pull ghcr.io/vectorize-io/hindsight-api:latest-slim
```

Requires external embedding/reranker providers:

```bash
export HINDSIGHT_API_EMBEDDING_PROVIDER=openai
export HINDSIGHT_API_RERANKER_PROVIDER=cohere
export COHERE_API_KEY=***```

---

## Enterprise: Oracle AI Database

For Oracle shops, Hindsight supports Oracle AI Database 23ai with feature parity:

```bash
export HINDSIGHT_API_DATABASE_BACKEND=oracle
export HINDSIGHT_API_DATABASE_URL=oracle://user:***@host:1521/service
```

Supported features are identical to PostgreSQL backend.

---

## Quick-Start Production Checklist

- [ ] External PostgreSQL 14+ with pgvector/pgvectorscale
- [ ] Stable `HINDSIGHT_API_WORKER_ID` per instance
- [ ] Read replica configured for recall offload
- [ ] Connection pooling tuned (`DB_POOL_MIN_SIZE`, `DB_POOL_MAX_SIZE`)
- [ ] LLM provider with API key and appropriate model
- [ ] Prometheus metrics endpoint accessible
- [ ] Health checks configured (Docker or K8s)
- [ ] API key set for authentication
- [ ] PostgreSQL tuned (shared_buffers, work_mem, autovacuum)
- [ ] Backup strategy in place (pg_dump or WAL archiving)
- [ ] Vector extension selected based on scale
- [ ] Autovacuum properly configured for write-heavy workload

---

Continue to:
- **[appendix.md](appendix.md)** — Full API reference, cookbook links, glossary
