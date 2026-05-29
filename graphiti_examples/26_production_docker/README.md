# Production Deployment Guide for Graphiti

This guide covers deploying Graphiti in a production environment, including
Neo4j Enterprise, Docker Compose, network security, backups, monitoring, and
scaling considerations.

---

## Production Docker Compose

Below is a production-grade `docker-compose.yml` for Neo4j Enterprise with
Graphiti. It includes health checks, restart policies, resource limits, and
network isolation.

### docker-compose.yml

```yaml
version: "3.9"

networks:
  graphiti-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

volumes:
  neo4j_data:
    driver: local
  neo4j_backups:
    driver: local
  neo4j_logs:
    driver: local

services:
  neo4j:
    image: neo4j:5-enterprise
    container_name: graphiti-neo4j
    networks:
      - graphiti-network
    ports:
      # Bolt protocol (encrypted in production)
      - "7687:7687"
      # HTTP for monitoring / health checks only
      # Restrict this port in your firewall
      - "7474:7474"
    environment:
      # Authentication
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?err}

      # Memory configuration
      - NEO4J_dbms_memory_pagecache_size=${NEO4J_PAGECACHE_SIZE:-2G}
      - NEO4J_dbms_memory_heap_initial__size=${NEO4J_HEAP_INITIAL:-1G}
      - NEO4J_dbms_memory_heap_max__size=${NEO4J_HEAP_MAX:-4G}

      # Enterprise features
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_dbms_backup_enabled=true

      # Security
      - NEO4J_dbms_security_auth__minimum__password__length=12
      - NEO4J_dbms_security_procedures_unrestricted=gds.*,apoc.*

      # Network
      - NEO4J_dbms_connector_bolt_advertised__address=${NEO4J_ADVERTISED_ADDRESS:-localhost:7687}
      - NEO4J_dbms_connector_bolt_tls__level=OPTIONAL

      # Logging
      - NEO4J_dbms_logs_debug_level=INFO
      - NEO4J_dbms_logs_query_enabled=true
      - NEO4J_dbms_logs_query_threshold=1000

      # Caches
      - NEO4J_dbms_memory_off__heap_max__size=${NEO4J_OFFHEAP_SIZE:-512M}
    volumes:
      - neo4j_data:/data
      - neo4j_backups:/backups
      - neo4j_logs:/logs
      - ./neo4j/plugins:/plugins
      - ./neo4j/conf:/conf
    healthcheck:
      test: ["CMD-SHELL",
        "cypher-shell -u neo4j -p '${NEO4J_PASSWORD}' 'RETURN 1;' || exit 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 60s
    deploy:
      resources:
        limits:
          cpus: "4"
          memory: ${NEO4J_MEMORY_LIMIT:-8G}
        reservations:
          cpus: "2"
          memory: ${NEO4J_MEMORY_RESERVE:-4G}
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"

  # Optional: Graphiti MCP server for programmatic access
  graphiti-mcp:
    image: ghcr.io/getzep/graphiti-mcp:latest
    container_name: graphiti-mcp
    networks:
      - graphiti-network
    ports:
      - "8000:8000"
    environment:
      - NEO4J_URI=bolt://neo4j:7687
      - NEO4J_USER=neo4j
      - NEO4J_PASSWORD=${NEO4J_PASSWORD:?err}
      - OPENAI_API_KEY=${OPENAI_API_KEY:?err}
      - GRAPHITI_MCP_HOST=0.0.0.0
      - GRAPHITI_MCP_PORT=8000
      - GRAPHITI_LOG_LEVEL=INFO
    depends_on:
      neo4j:
        condition: service_healthy
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 512M
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "3"
```

### .env.example

```bash
# =============================================================================
# Graphiti Production Configuration
# Copy to .env and fill in all values
# =============================================================================

# --- Neo4j ---
NEO4J_PASSWORD=CHANGE_ME_TO_A_STRONG_PASSWORD_AT_LEAST_24_CHARS
NEO4J_ADVERTISED_ADDRESS=neo4j.example.com:7687

# --- Memory ---
NEO4J_PAGECACHE_SIZE=2G
NEO4J_HEAP_INITIAL=1G
NEO4J_HEAP_MAX=4G
NEO4J_OFFHEAP_SIZE=512M
NEO4J_MEMORY_LIMIT=8G
NEO4J_MEMORY_RESERVE=4G

# --- LLM ---
OPENAI_API_KEY=sk-your-key-here

# --- Optional: Alternative LLM provider ---
# OPENAI_BASE_URL=https://your-proxy.example.com/v1
# GRAPHITI_LLM_MODEL=gpt-4o
# GRAPHITI_LLM_EMBEDDING_MODEL=text-embedding-3-small

# --- Graphiti MCP ---
# GRAPHITI_MCP_HOST=0.0.0.0
# GRAPHITI_MCP_PORT=8000
```

---

## Network Security

### TLS for Neo4j Bolt connections

For production, enable TLS on the Bolt protocol. You need a valid TLS
certificate (not self-signed for production).

Option 1: Use Neo4j's built-in SSL support

```yaml
# docker-compose.yml extra config
environment:
  - NEO4J_dbms_connector_bolt_tls__level=REQUIRED
  - NEO4J_dbms_connector_bolt_tls__cert__file=/ssl/neo4j.crt
  - NEO4J_dbms_connector_bolt_tls__key__file=/ssl/neo4j.key
volumes:
  - ./ssl:/ssl:ro
```

Option 2: Use a reverse proxy (NGINX / Traefik)

```nginx
# nginx.conf for TLS termination
stream {
    upstream neo4j_bolt {
        server neo4j:7687;
    }

    server {
        listen 7687 ssl;
        proxy_pass neo4j_bolt;

        ssl_certificate /etc/letsencrypt/live/neo4j.example.com/fullchain.pem;
        ssl_certificate_key /etc/letsencrypt/live/neo4j.example.com/privkey.pem;
    }
}
```

### Firewall rules

| Port | Protocol | Purpose | Restrict to |
|------|----------|---------|-------------|
| 7687 | TCP | Neo4j Bolt | Application servers only |
| 7474 | TCP | Neo4j HTTP | Admin VPN / internal network only |
| 8000 | TCP | Graphiti MCP | Application servers only |
| 22 | TCP | SSH | Admin VPN only |

### VPC / Private networking

- Deploy Neo4j in a private subnet with no public IP
- Place application servers in the same VPC
- Use VPC peering or VPN for admin access
- For cloud deployments:
  - AWS: Security groups + NACLs + VPC endpoints
  - GCP: VPC firewall rules + Private Service Connect
  - Azure: NSGs + Private Link

### API key management

Never hardcode API keys. Use a secrets manager:

```bash
# AWS Secrets Manager example
export OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id graphiti/openai-key --query SecretString --output text)

# HashiCorp Vault example
export OPENAI_API_KEY=$(vault kv get -field=key secret/graphiti/openai)

# Docker secrets (Docker Swarm)
echo "sk-your-key" | docker secret create openai_api_key -
```

---

## Backup Strategy

### Automated backup script

```bash
#!/bin/bash
# neo4j-backup.sh -- Run daily via cron or Kubernetes CronJob

set -euo pipefail

BACKUP_DIR="/backups/neo4j"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
NEO4J_CONTAINER="graphiti-neo4j"
NEO4J_PASSWORD="${NEO4J_PASSWORD:?}"

echo "Starting Neo4j backup at $(date)"

# Create backup directory
mkdir -p "${BACKUP_DIR}/${TIMESTAMP}"

# Use neo4j-admin dump (Enterprise feature)
docker exec "${NEO4J_CONTAINER}" \
  neo4j-admin database dump neo4j \
  --to-path="/backups/${TIMESTAMP}"

# Copy backup to host
docker cp "${NEO4J_CONTAINER}:/backups/${TIMESTAMP}" "${BACKUP_DIR}/"

# Compress backup
tar -czf "${BACKUP_DIR}/neo4j-backup-${TIMESTAMP}.tar.gz" \
  -C "${BACKUP_DIR}" "${TIMESTAMP}"
rm -rf "${BACKUP_DIR:?}/${TIMESTAMP}"

# Upload to remote storage (optional)
# aws s3 cp "${BACKUP_DIR}/neo4j-backup-${TIMESTAMP}.tar.gz" \
#   "s3://your-bucket/neo4j-backups/"

# Clean up old backups
find "${BACKUP_DIR}" -name "neo4j-backup-*.tar.gz" -mtime +"${RETENTION_DAYS}" -delete

echo "Backup complete: neo4j-backup-${TIMESTAMP}.tar.gz"
echo "Size: $(du -h "${BACKUP_DIR}/neo4j-backup-${TIMESTAMP}.tar.gz" | cut -f1)"
```

### Restore procedure

```bash
#!/bin/bash
# neo4j-restore.sh -- Restore a specific backup

BACKUP_FILE="$1"
if [ -z "${BACKUP_FILE}" ]; then
  echo "Usage: $0 <backup-file.tar.gz>"
  exit 1
fi

set -euo pipefail

echo "=== NEO4J RESTORE ==="
echo "WARNING: This will overwrite the current database!"
echo "Backup file: ${BACKUP_FILE}"
echo ""

# 1. Stop the Neo4j container
docker compose down neo4j

# 2. Extract backup
RESTORE_DIR="/tmp/neo4j-restore-$(date +%s)"
mkdir -p "${RESTORE_DIR}"
tar -xzf "${BACKUP_FILE}" -C "${RESTORE_DIR}"

# 3. Remove old data
docker compose run --rm neo4j bash -c "rm -rf /data/*"

# 4. Load backup
docker compose run --rm \
  -v "${RESTORE_DIR}:/restore" \
  neo4j bash -c "
    neo4j-admin database load neo4j --from-path=/restore/\$(ls /restore)
  "

# 5. Clean up
rm -rf "${RESTORE_DIR}"

# 6. Restart
docker compose up -d neo4j
echo "Restore complete. Neo4j is starting..."
```

### Backup retention policy

| Retention tier | Duration | Frequency | Storage |
|---------------|----------|-----------|---------|
| Hourly | 24 hours | Every hour | Local volume |
| Daily | 30 days | Once daily | Local + S3/Blob |
| Weekly | 12 weeks | Once weekly | S3/Blob |
| Monthly | 12 months | Once monthly | S3/Blob + cold archive |

---

## Monitoring

### Health check endpoint

Graphiti MCP exposes a health endpoint:

```bash
curl http://localhost:8000/health
# Expected: {"status": "ok", "neo4j": "connected", "version": "0.4.0"}
```

### Prometheus metrics (via Neo4j Exporter)

```yaml
# docker-compose addition
neo4j-exporter:
  image: bitnami/neo4j-exporter:latest
  container_name: neo4j-exporter
  networks:
    - graphiti-network
  environment:
    - NEO4J_URI=http://neo4j:7474
    - NEO4J_USER=neo4j
    - NEO4J_PASSWORD=${NEO4J_PASSWORD:?err}
  ports:
    - "9474:9474"
  restart: unless-stopped
```

### Key metrics to monitor

| Metric | What it tells you | Warning threshold | Critical threshold |
|--------|-------------------|-------------------|-------------------|
| `neo4j_db_episodes` | Total episodes ingested | - | - |
| `neo4j_db_entities` | Total entity nodes | - | - |
| `neo4j_db_edges` | Total relationship edges | - | - |
| `neo4j_query_execution_time` | Graph query latency | >500ms | >2s |
| `neo4j_bolt_connections` | Active connections | >100 | >200 |
| `neo4j_heap_usage` | JVM heap utilization | >70% | >90% |
| `neo4j_page_cache_hit_ratio` | Cache efficiency | <90% | <80% |
| `neo4j_store_size` | Database size on disk | - | - |
| `graphiti_llm_calls_total` | LLM API call count | - | - |
| `graphiti_llm_latency` | LLM API latency | >5s | >10s |

### Grafana dashboard

A basic Grafana dashboard for Neo4j should include:

1. **Database Overview**: Store size, node/edge counts, page cache hit ratio
2. **Query Performance**: P50/P95/P99 query latency, slow queries
3. **Connection Pool**: Active connections, wait time
4. **System Health**: CPU, memory, disk, JVM GC activity
5. **LLM Usage**: API calls, latency, cost, token usage (if using cloud LLM)

---

## Scaling Considerations

### Read replicas

Neo4j Enterprise supports read replicas for scaling read queries:

```yaml
# docker-compose addition for a read replica
neo4j-reader:
  image: neo4j:5-enterprise
  container_name: graphiti-neo4j-reader
  networks:
    - graphiti-network
  environment:
    - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:?err}
    - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
    - NEO4J_dbms_mode=READ_REPLICA
    - NEO4J_dbms_cluster_discovery_endpoints=neo4j:5000
    - NEO4J_initial_server_mode__constraint=true
  volumes:
    - neo4j_data_reader:/data
  deploy:
    resources:
      limits:
        cpus: "4"
        memory: ${NEO4J_MEMORY_LIMIT:-8G}
  restart: unless-stopped
```

Update your application to route read queries to the replica:

```python
# Separate read and write connections
write_client = Graphiti(uri="bolt://neo4j:7687", user="neo4j", password="...")
read_client = Graphiti(uri="bolt://neo4j-reader:7687", user="neo4j", password="...")

# Writes go to primary
await write_client.add_episode(...)

# Reads can go to replica
results = await read_client.search(...)
```

### Separating vector search from graph traversal

For high-throughput production systems, consider separating the vector search
and graph traversal concerns:

```
                  ┌───────────────┐
                  │  Application  │
                  └───┬───────┬───┘
                      │       │
              ┌───────▼──┐ ┌──▼────────┐
              │ Vector DB │ │ Graph DB  │
              │ (for      │ │ (for      │
              │  semantic │ │  traversal)│
              │  search)  │ │           │
              └───────────┘ └───────────┘
```

This is Zep's production pattern. The vector store handles the initial semantic
search (fast, approximate), and the graph handles the relationship traversal
(precise, structured).

---

## Zep Cloud vs Self-Hosted Decision Matrix

| Capability | Zep Cloud | Self-Hosted (Neo4j) |
|------------|-----------|---------------------|
| **Setup time** | Minutes (API key only) | Hours to days |
| **Maintenance** | Zero (managed) | Full ops responsibility |
| **Scaling** | Automatic | Manual (Docker/K8s) |
| **Vector search** | Built-in, managed | Requires plugin setup |
| **Community detection** | Built-in | Requires GDS plugin |
| **Backup/recovery** | Automatic | Manual setup required |
| **SLA** | 99.9%+ (varies by tier) | Depends on your infrastructure |
| **Data residency** | US/EU regions | Full control |
| **HIPAA/SOC 2** | Available on enterprise | You own compliance |
| **Cost model** | Usage-based (per entity) | Fixed infra + ops cost |
| **LLM integration** | Built-in, managed | You manage API keys + billing |
| **On-premises option** | No | Yes |

**Choose Zep Cloud when:**
- You want to get started in minutes, not days
- You don't want to manage infrastructure
- Your data residency requirements allow cloud hosting
- You need HIPAA/SOC 2 compliance without building it yourself
- Your workload is variable (benefits from usage-based pricing)

**Choose Self-Hosted when:**
- You need on-premises deployment for regulatory reasons
- You have existing Neo4j infrastructure and expertise
- Your workload is predictable and large enough to justify fixed costs
- You need full control over the deployment and configuration
- You are running in air-gapped environments

---

## Migration Path: Local Dev to Production

```
Local Dev                         Staging                        Production
──────────                        ───────                        ──────────
Neo4j Desktop or Docker Compose   Docker Compose (closer to prod) Neo4j Enterprise Cluster
Kuzu (for testing)                Single Neo4j instance           Read replicas + backups
.env file with local creds        .env + secrets manager          Secrets manager + vault
No TLS                            TLS with self-signed cert       TLS with valid cert
No backups                        Manual backups                  Automated backups w/ retention
No monitoring                     Basic health checks             Full Grafana + alerts
Local LLM (Ollama) or OpenAI      OpenAI / Anthropic              Dedicated LLM endpoint
```

### Migration steps

1. **Export data from local Neo4j**: `docker exec ... neo4j-admin dump`
2. **Set up production Neo4j** (cloud VM, AuraDB, or your own infra)
3. **Import data**: `neo4j-admin load`
4. **Update connection URIs**: Point your app to the production URI
5. **Switch secrets**: Move from `.env` to a secrets manager
6. **Enable TLS**: Configure certificates for production Bolt connections
7. **Configure backups**: Set up automated backups with retention
8. **Set up monitoring**: Deploy Prometheus + Grafana
9. **Gradually shift traffic**: Use a blue-green or canary deployment

---

## Security Checklist for Production

- [ ] Neo4j password is at least 24 characters, generated by a password manager
- [ ] TLS is enabled for all Bolt connections
- [ ] Port 7474 (HTTP) is restricted to admin VPN / internal network
- [ ] API keys are stored in a secrets manager, never in code or .env files
- [ ] Neo4j Enterprise license is active (if using Enterprise features)
- [ ] Automated backups are configured with offsite storage
- [ ] Monitoring and alerting are configured for key metrics
- [ ] Container resource limits are set (prevent OOM / CPU starvation)
- [ ] Logs are collected centrally (ELK, Loki, DataDog, etc.)
- [ ] Regular security updates are applied to Neo4j and dependencies
- [ ] Network access is restricted via firewall / security groups
- [ ] Read replicas are in separate availability zones (if applicable)
