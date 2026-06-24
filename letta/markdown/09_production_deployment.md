# Production Deployment — Self-Hosting, Docker & Best Practices

> **Goal**: Deploy Letta in production — self-hosted servers, Docker, security
> hardening, monitoring, and patterns for production-grade agent systems.

---

## 1. Deployment Architecture Options

```
┌──────────────────────────────────────────────────────────┐
│                 DEPLOYMENT ARCHITECTURES                  │
├──────────────┬──────────────────┬────────────────────────┤
│ LETTA CLOUD  │ SELF-HOSTED      │ HYBRID                 │
│ (Managed)    │ (Docker/VPS)     │ (Cloud + Local)        │
├──────────────┼──────────────────┼────────────────────────┤
│ ✓ Zero ops   │ ✓ Full control   │ ✓ Cloud for dev        │
│ ✓ Auto-scale │ ✓ Data locality  │ ✓ Self-host for prod   │
│ ✓ Managed DB │ ✓ No API limits  │ ✓ Gradual migration    │
│ ✗ API limits │ ✗ You manage it  │ ✗ More complex         │
│ ✗ Data on    │ ✗ Scaling on you │ ✗ Two systems to       │
│   Letta infra│                  │    monitor              │
└──────────────┴──────────────────┴────────────────────────┘
```

**When to self-host**: Data residency requirements, custom model backends,
air-gapped environments, cost optimization at scale.

## 2. Self-Hosting with Docker Compose

The recommended way to run Letta server on your own infrastructure.

```yaml
version: "3.8"

services:
  letta:
    image: letta/letta:latest
    container_name: letta-server
    restart: unless-stopped
    ports:
      - "8283:8283"          # Letta API
    environment:
      # ── Required: Model provider credentials ──────────────────
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}    # Optional
      
      # ── Database ──────────────────────────────────────────────
      # SQLite (default, simpler)
      - LETTA_DB_TYPE=sqlite
      - LETTA_DB_PATH=/data/letta.db
      
      # PostgreSQL (production)
      # - LETTA_DB_TYPE=postgres
      # - LETTA_DB_URI=postgresql://letta:password@postgres:5432/letta
      
      # ── Server config ─────────────────────────────────────────
      - LETTA_HOST=0.0.0.0
      - LETTA_PORT=8283
      - LETTA_LOG_LEVEL=info
      
      # ── Archival memory backend ───────────────────────────────
      # LanceDB (default, embedded)
      # - LETTA_ARCHIVAL_BACKEND=lance
      
      # Pinecone (production, managed vector DB)
      # - LETTA_ARCHIVAL_BACKEND=pinecone
      # - PINECONE_API_KEY=${PINECONE_API_KEY}
      # - PINECONE_ENVIRONMENT=us-east-1-aws
      
      # Redis (for Recall Memory in production)
      # - LETTA_RECALL_BACKEND=redis
      # - REDIS_URI=redis://redis:6379
      
    volumes:
      - letta_data:/data       # Persistent storage
      - ./config.yaml:/root/.letta/config.yaml:ro  # Custom config
    
    # ── Health check ────────────────────────────────────────────
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8283/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
  
  # ── Optional: PostgreSQL ──────────────────────────────────────
  # postgres:
  #   image: postgres:17-alpine
  #   container_name: letta-postgres
  #   restart: unless-stopped
  #   environment:
  #     - POSTGRES_DB=letta
  #     - POSTGRES_USER=letta
  #     - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data
  #   healthcheck:
  #     test: ["CMD-SHELL", "pg_isready -U letta"]
  #     interval: 10s
  #     timeout: 5s
  #     retries: 5
  
  # ── Optional: Redis ───────────────────────────────────────────
  # redis:
  #   image: redis:7-alpine
  #   container_name: letta-redis
  #   restart: unless-stopped
  #   volumes:
  #     - redis_data:/data

volumes:
  letta_data:
  # postgres_data:
  # redis_data:
```

```bash
# .env — store alongside docker-compose.yaml
# NEVER commit this file to git!

OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
# POSTGRES_PASSWORD=your-strong-password-here
# PINECONE_API_KEY=...
```

## 3. Connecting Python Client to Self-Hosted Server

```python
# ── Connecting to a self-hosted Letta server ────────────────────

from letta_client import Letta

# No API key needed for self-hosted!
client = Letta(base_url="http://localhost:8283")

# Or with authentication (if configured on server)
# client = Letta(
#     base_url="http://localhost:8283",
#     api_key="your-custom-auth-token"
# )

# Everything works the same as cloud — same API, same code
# agent = client.agents.create(
#     model="openai/gpt-4o-mini",
#     memory_blocks=[...]
# )

print("Self-hosted client: no Letta API key needed!")
print("You still need model provider keys (OpenAI, Anthropic, etc.)")
print("Those go in the server's .env, not the client.")
```

## 4. Database Backend Selection

| Backend | Best For | Scaling Limit |
|---------|----------|---------------|
| **SQLite** | Development, single-server, <100 agents | ~1M messages, single writer |
| **PostgreSQL** | Production, multi-server, >100 agents | Millions of messages, concurrent reads/writes |
| **LanceDB** (archival) | Default, embedded | Good for <1M passages |
| **Pinecone** (archival) | Production, high scale | Billions of vectors, managed |
| **Redis** (recall) | Production, low-latency recall | Sub-millisecond message retrieval |

```bash
# Environment variables for production PostgreSQL setup:

LETTA_DB_TYPE=postgres
LETTA_DB_URI=postgresql://letta:STRONG_PASSWORD@postgres-primary.internal:5432/letta?sslmode=require

# For high availability: connection pooling
LETTA_DB_POOL_SIZE=20        # Max connections in pool
LETTA_DB_POOL_OVERFLOW=10    # Extra connections on spike

# Archival memory: Pinecone for scale
LETTA_ARCHIVAL_BACKEND=pinecone
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws
PINECONE_INDEX_NAME=letta-archival

# Recall memory: Redis for speed
LETTA_RECALL_BACKEND=redis
REDIS_URI=redis://:PASSWORD@redis.internal:6379/0
REDIS_MAX_CONNECTIONS=50
```

## 5. Security Hardening

Production agent systems have unique security concerns:

```text
SECURITY HARDENING CHECKLIST:

┌─ NETWORK ──────────────────────────────────────────────┐
│ ☐ Run behind reverse proxy (nginx/Caddy/Traefik)        │
│ ☐ Enable TLS (Let's Encrypt auto-renew)                 │
│ ☐ Restrict API access to internal network (VPC only)    │
│ ☐ Use WireGuard/VPN for admin access                    │
│ ☐ Rate limit API endpoints                              │
└─────────────────────────────────────────────────────────┘

┌─ AUTHENTICATION ───────────────────────────────────────┐
│ ☐ NEVER expose admin API without auth                   │
│ ☐ Use scoped access tokens (not master API key)        │
│ ☐ Rotate API keys regularly (every 90 days)             │
│ ☐ Audit token usage via logs                            │
│ ☐ Separate tokens per environment/microservice          │
└─────────────────────────────────────────────────────────┘

┌─ DATA ─────────────────────────────────────────────────┐
│ ☐ Encrypt database at rest (LUKS/cloud KMS)             │
│ ☐ Encrypt backups                                       │
│ ☐ Don't log message content (PII risk)                   │
│ ☐ Set data retention policies (auto-delete old data)    │
│ ☐ Regular backup schedule + test restores               │
└─────────────────────────────────────────────────────────┘

┌─ MODEL ACCESS ─────────────────────────────────────────┐
│ ☐ Use separate API keys per agent (cost tracking)       │
│ ☐ Set spending limits on provider accounts              │
│ ☐ Monitor for anomalous token usage (abuse detection)   │
│ ☐ Restrict which models agents can use                  │
└─────────────────────────────────────────────────────────┘

┌─ AGENT-SPECIFIC ───────────────────────────────────────┐
│ ☐ Tool allowlisting — only enable tools agents NEED     │
│ ☐ Rate limit per-agent message frequency                │
│ ☐ Set max tokens per response (prevent runaway loops)   │
│ ☐ Monitor agent memory usage (anomaly detection)        │
│ ☐ Isolate agents (no cross-agent data leakage)          │
└─────────────────────────────────────────────────────────┘
```

## 6. Monitoring & Observability

```text
# ── Key metrics to monitor ──────────────────────────────────────

# 1. LATENCY
#    - P50/P95/P99 response time per agent
#    - LLM API call latency (is the model provider slow?)
#    - Database query latency

# 2. THROUGHPUT
#    - Messages per second
#    - Active agents count
#    - Tool calls per turn

# 3. ERRORS
#    - 4xx/5xx rate
#    - Model API failures (rate limits, timeouts)
#    - Database connection errors

# 4. COST
#    - Tokens per agent per day
#    - Cost per message
#    - Total daily spend

# 5. MEMORY HEALTH
#    - Blocks approaching limit
#    - Archival passage count growth
#    - Compaction frequency per agent

# ── Monitoring stack recommendations ────────────────────────────

# Option A: Prometheus + Grafana (self-hosted)
#   - Export Letta metrics to Prometheus endpoint
#   - Grafana dashboard for visualization
#   - AlertManager for alerts

# Option B: Datadog / New Relic (SaaS)
#   - Built-in dashboards
#   - Anomaly detection
#   - Cost tracking integrations

# Option C: Letta Cloud Dashboard (for Cloud users)
#   - Built-in analytics
#   - Usage graphs
#   - Cost breakdowns
```

## 7. Production Code Patterns

Here's a production-ready agent service wrapper:

```python
import time
import logging
from typing import Optional
from contextlib import contextmanager
from letta_client import Letta, LettaError

class LettaAgentService:
    """
    Production-ready wrapper for Letta agents.
    
    Features:
    - Connection pooling (via client reuse)
    - Automatic retry with exponential backoff
    - Structured logging
    - Health checks
    - Cost tracking
    """
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self.base_url = base_url
        self.client = Letta(
            base_url=base_url,
            api_key=api_key
        )
        self.logger = logging.getLogger(__name__)
    
    def create_agent(self, agent_config: dict):
        """Create an agent with error handling."""
        try:
            agent = self.client.agents.create(**agent_config)
            self.logger.info(f"Agent created: {agent.id}")
            return agent
        except LettaError as e:
            self.logger.error(f"Failed to create agent: {e}")
            raise
    
    def send_message(self, agent_id: str, message: str, 
                     max_retries: int = 3) -> dict:
        """
        Send a message with exponential backoff.
        
        Returns: {messages, cost_estimate, latency_ms}
        """
        start = time.time()
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.agents.messages.create(
                    agent_id,
                    input=message
                )
                
                latency_ms = (time.time() - start) * 1000
                self.logger.info(
                    f"Message sent to {agent_id}: "
                    f"{len(response.messages)} messages, "
                    f"{latency_ms:.0f}ms"
                )
                
                return {
                    "messages": response.messages,
                    "latency_ms": latency_ms,
                    "status": "success"
                }
            
            except LettaError as e:
                last_error = e
                if "429" in str(e):
                    # Rate limit — back off
                    wait = 2 ** attempt
                    self.logger.warning(
                        f"Rate limited (attempt {attempt}). "
                        f"Waiting {wait}s..."
                    )
                    time.sleep(wait)
                    continue
                # Non-retryable
                raise
            
            except Exception as e:
                last_error = e
                self.logger.error(f"Unexpected error: {e}")
                if attempt == max_retries:
                    raise
                time.sleep(1)
        
        raise RuntimeError(
            f"Failed after {max_retries} retries. "
            f"Last error: {last_error}"
        )
    
    def health_check(self) -> bool:
        """Check if the Letta service is healthy."""
        try:
            # Simple API call to verify connectivity
            self.client.agents.list(limit=1)
            return True
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    def delete_agent_safely(self, agent_id: str):
        """Delete an agent with confirmation logging."""
        try:
            self.client.agents.delete(agent_id)
            self.logger.info(f"Agent deleted: {agent_id}")
        except LettaError as e:
            if "not found" in str(e).lower():
                self.logger.warning(f"Agent already deleted: {agent_id}")
            else:
                raise

# ── Usage example ───────────────────────────────────────────────

# Initialize service
# service = LettaAgentService(base_url="http://localhost:8283")

# Health check before use
# if not service.health_check():
#     raise RuntimeError("Letta service is unhealthy!")

# Create agent
# agent = service.create_agent({
#     "model": "openai/gpt-4o-mini",
#     "memory_blocks": [
#         {"label": "human", "value": "User: Alex", "limit": 2000},
#         {"label": "persona", "value": "I am a helpful assistant.", "limit": 2000}
#     ]
# })

# Send message
# result = service.send_message(agent.id, "Hello!")
# print(f"Response in {result['latency_ms']:.0f}ms")

print("LettaAgentService — production-ready wrapper pattern")
```

## 8. Cost Management

```text
COST MANAGEMENT STRATEGIES FOR PRODUCTION:

1. MODEL TIERING:
   ┌────────────────┬──────────────┬──────────────────┐
   │ Task           │ Model        │ Cost/turn (est.) │
   ├────────────────┼──────────────┼──────────────────┤
   │ Simple Q&A     │ gpt-4o-mini  │ ~$0.002          │
   │ Complex agent  │ gpt-4o       │ ~$0.05           │
   │ Code gen       │ claude-s-4   │ ~$0.03           │
   │ Compaction     │ gpt-4o-mini  │ ~$0.001          │
   │ Sleep-time     │ gpt-4o-mini  │ ~$0.005/cycle    │
   └────────────────┴──────────────┴──────────────────┘

2. TOKEN BUDGETING:
   - Set max_tokens per response (prevent runaway generations)
   - Limit memory block sizes (every char costs tokens)
   - Use compaction aggressively for long-running agents
   - Archive old passages instead of keeping in context

3. RATE LIMITING:
   - Free tier: 100 messages/day (good for dev)
   - Pro tier: 10,000 messages/day
   - Implement client-side rate limiting to stay within budget

4. CACHING:
   - Cache common responses (for deterministic queries)
   - Reuse embeddings for repeated archival searches
   - Batch archival inserts (fewer API calls)

5. MONITORING:
   - Set up daily spend alerts
   - Track cost per agent, per user, per endpoint
   - Review weekly: which agents are the most expensive?
```

## 9. Scalability Patterns

```text
SCALING LETTA IN PRODUCTION:

SCALE: 1-100 agents
  Architecture: Single server + SQLite
  Deployment: docker-compose on one VM (4 vCPU, 8GB RAM)
  Monitoring: Basic logging + health checks

SCALE: 100-1,000 agents
  Architecture: Load-balanced servers + PostgreSQL
  Deployment: Kubernetes (2-3 pods), separate DB instance
  Monitoring: Prometheus + Grafana
  Cache: Redis for recall memory
  Archival: Pinecone (managed vector DB)

SCALE: 1,000-10,000 agents
  Architecture: Microservices + read replicas + message queue
  Deployment: Kubernetes with HPA (auto-scaling)
  Database: PostgreSQL with read replicas + connection pooling
  Queue: Redis/Kafka for message processing
  Monitoring: Datadog / New Relic
  Cost: ~$0.50-$2.00 per agent per day (model-dependent)

SCALE: 10,000+ agents
  Architecture: Sharded by customer + global routing
  Consider: Letta Cloud Enterprise (managed scaling)
  Multi-region: Deploy close to users for lower latency
  Custom models: Fine-tuned models for specific use cases
```

## 10. Backup & Disaster Recovery

```python
BACKUP STRATEGY:

1. DATABASE BACKUPS:
   # PostgreSQL continuous backup
   pg_dump -Fc letta > backup_$(date +%Y%m%d).dump
   
   # Or Point-in-Time Recovery (PITR)
   # Configure WAL archiving to S3/GCS

2. MEMORY BACKUPS (MemFS / V2):
   # Git auto-pushes memory to remote
   letta memory push  # Push to GitHub/GitLab
   
   # Or: nightly cron job
   0 2 * * * cd ~/.letta/agents/*/memory && git push origin main

3. RESTORE PROCEDURE:
   1. Stop Letta server
   2. Restore database from backup
   3. For V2: git clone memory repos
   4. Verify with health check
   5. Resume traffic

4. DISASTER RECOVERY TIMELINE:
   - RPO (Recovery Point Objective): 1 hour (hourly backups)
   - RTO (Recovery Time Objective): 30 minutes (automated restore)
   - Test restore: Monthly (don't wait for an incident!)
```

## 11. Production Checklist

Before going live with Letta in production:

```text
PRODUCTION READINESS CHECKLIST:

INFRASTRUCTURE:
☐ Database: PostgreSQL (not SQLite) for production
☐ Backups: Automated daily backups with tested restore
☐ Monitoring: Metrics + alerts for latency, errors, cost
☐ Logging: Structured logs with correlation IDs
☐ TLS: HTTPS everywhere, even internal services

APPLICATION:
☐ Error handling: All API calls wrapped with retry logic
☐ Timeouts: Set on all external calls (LLM, DB, cache)
☐ Rate limiting: Protect against abuse and runaway costs
☐ Idempotency: Duplicate messages shouldn't duplicate effects
☐ Circuit breakers: Degrade gracefully when downstream fails

SECURITY:
☐ Auth: All endpoints require authentication
☐ Scoped tokens: Per-service, minimal permissions
☐ Secrets: Never in code, use vault/secret manager
☐ Audit log: Who accessed what, when
☐ Data retention: Purging policy for old conversations

AGENT-SPECIFIC:
☐ Cost caps: Per-agent spending limits
☐ Content filtering: Block inappropriate agent responses
☐ Memory limits: Prevent unbounded memory growth
☐ Versioning: Track agent configs in git
☐ Testing: Integration tests for agent behavior

OPERATIONS:
☐ Runbook: Documented procedures for common incidents
☐ On-call: Who gets paged when the agent service is down?
☐ Capacity planning: When do you need to scale?
☐ SLA: What uptime do you promise? (Target: 99.9%+)
☐ Cost tracking: Monthly cost review process
```

## Key Takeaways

1. **Start with Letta Cloud**, graduate to self-hosted when needed.
2. **Docker Compose** is the easiest self-hosting path.
3. **PostgreSQL + Pinecone/Redis** for production scale (>100 agents).
4. **Security is critical** — agents with tool access are powerful, lock them down.
5. **Monitor everything** — latency, errors, cost, memory health.
6. **Backup and test restore** — agent memory is valuable data.
7. **Cost compounds** — 1,000 agents × $0.05/turn × 100 turns/day = $5,000/day.

---

## End of Tutorial

You've completed the Letta comprehensive tutorial. You now understand:

- **Fundamentals**: Memory hierarchy, OS-inspired architecture
- **Getting started**: Installation, API keys, first agent
- **Memory blocks**: Core memory management, labels, custom blocks
- **Archival memory**: Passages, semantic search, knowledge bases
- **Tools**: Custom functions, server-side tools, tool patterns
- **Multi-agent**: Writer/reviewer, shared knowledge, hierarchies, debates
- **Advanced**: Agent types, compaction, templates, sleep-time
- **Letta Code**: CLI, MemFS, skills, subagents, V2 Agent SDK
- **Production**: Self-hosting, Docker, security, monitoring, scaling

**Next steps**:
1. Get an API key: https://app.letta.com
2. Run the code examples in these notebooks
3. Join the Letta Discord: https://discord.gg/letta
4. Read the docs: https://docs.letta.com
5. Star the repo: https://github.com/letta-ai/letta
