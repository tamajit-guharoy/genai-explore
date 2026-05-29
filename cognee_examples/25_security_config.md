# 25 — Security Hardening Guide

## Authentication Configuration

### API Key Authentication (Internal Services)
```python
cognee.config.set({
    "auth_provider": "api_key",
    "api_keys": [
        "cognee_sk_prod_abc123...",
        "cognee_sk_prod_def456...",
    ],
})
```
Clients include the key in the `X-Api-Key` header.

### JWT Authentication (User-Facing)
```python
cognee.config.set({
    "auth_provider": "auth0",
    "auth_domain": "your-tenant.auth0.com",
    "auth_audience": "https://api.cognee.ai",
})
```

### Single Sign-On
```python
cognee.config.set({
    "auth_provider": "cognito",  # AWS Cognito
    "auth_domain": "your-pool.auth.us-east-1.amazoncognito.com",
    "auth_client_id": "your-client-id",
})
```

## Network Security

### TLS/HTTPS
In production, always place Cognee behind a reverse proxy that terminates TLS:
```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name cognee.internal;

    ssl_certificate /etc/ssl/certs/cognee.crt;
    ssl_certificate_key /etc/ssl/private/cognee.key;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### MCP Server Security
The MCP server runs on local stdio by default (no network exposure):
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
If using HTTP/SSE transport, use TLS and authentication.

### CORS Configuration
```bash
# Restrict CORS to your domains
export CORS_ALLOWED_ORIGINS="https://app.example.com,https://admin.example.com"
```

## Data Privacy

### PII Handling
Cognee does not auto-redact PII (as of v0.5.7). Best practices:
1. **Pre-process**: Scan and redact PII before calling `cognee.add()`
2. **Access control**: Use dataset-level RBAC to limit PII exposure
3. **Audit**: Enable OTEL tracing to monitor all data access
4. **Minimize**: Only ingest the fields needed for extraction

Example pre-processing pipeline:
```python
import re

def redact_pii(text: str) -> str:
    """Basic PII redaction — use a proper library in production."""
    # Emails
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[REDACTED_EMAIL]', text)
    # SSNs
    text = re.sub(r'\d{3}-\d{2}-\d{4}', '[REDACTED_SSN]', text)
    # Credit cards
    text = re.sub(r'\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}', '[REDACTED_CC]', text)
    return text

# Pre-process before ingestion
safe_text = redact_pii(original_text)
await cognee.add(safe_text)
```

### Right to Erasure (GDPR)
```python
# Delete a specific user's data
await cognee.forget(user_id="user_123")

# Delete a specific dataset
await cognee.forget(dataset="marketing_campaigns")

# Delete data older than a date
from datetime import datetime
await cognee.forget(older_than=datetime(2024, 1, 1))
```

## Audit Trail

Enable OpenTelemetry tracing for complete audit trails:
```python
cognee.enable_tracing()
cognee.config.set({
    "otel_exporter_endpoint": "https://your-collector:4318/v1/traces",
})
```
Each traced operation records: who, what data, when, and the result.

## Key Rotation

Rotate API keys regularly:
```python
# Add a new key
cognee.config.update({"api_keys": [
    "cognee_sk_prod_OLD_KEY",    # Old key (keep during rotation)
    "cognee_sk_prod_NEW_KEY",    # New key
]})

# After confirming all clients have migrated, remove old key
cognee.config.update({"api_keys": [
    "cognee_sk_prod_NEW_KEY",
]})
```

## Database Security

### PostgreSQL
```bash
# Use SSL connections
export RELATIONAL_DB_URL=postgresql://user:pass@host:5432/cognee?sslmode=require

# Use certificate-based auth
export RELATIONAL_DB_URL=postgresql://user@host:5432/cognee?sslmode=verify-full&sslcert=/path/to/client.crt&sslkey=/path/to/client.key&sslrootcert=/path/to/ca.crt
```

### Neo4j
```bash
# Use encrypted Bolt connections
export GRAPH_DB_URL=bolt+s://neo4j-host:7687
export GRAPH_DB_USERNAME=neo4j
export GRAPH_DB_PASSWORD=your-secure-password
```

### Network Isolation
For production, place all database services on an internal network not exposed to the public internet:
```yaml
# In docker-compose.yml:
networks:
  backend:
    internal: true  # No external access
```

The Cognee API server is the only service with an exposed port.

## Compliance Checklist

| Requirement | Implementation |
|---|---|
| Encryption at rest | Use encrypted volumes; enable DB-level encryption |
| Encryption in transit | TLS/HTTPS for all connections; bolt+s for Neo4j |
| Access control | RBAC via dataset permissions + user_id scoping |
| Audit logging | OpenTelemetry tracing with export to SIEM |
| Data deletion | `cognee.forget()` with user/dataset/time scoping |
| Authentication | JWT or API key; SSO for enterprise |
| Network segmentation | Internal network for databases; API-only exposure |
| Key rotation | Regular API key rotation with overlap period |
| PII minimization | Pre-process data; limit ingestion to necessary fields |
