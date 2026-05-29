# Security, Multi-Tenancy, and Compliance Guide for Graphiti

This guide covers security best practices for deploying Graphiti in
production, with a focus on multi-tenant isolation, data protection,
compliance frameworks, and operational security.

---

## 1. group_id for Data Isolation Between Tenants

Graphiti's `group_id` is the primary mechanism for multi-tenant data isolation.
Every episode, entity, and edge is tagged with a `group_id`.

### Tenant isolation model

```
                        ┌──────────────────────┐
                        │    Application        │
                        └──┬───┬───┬───┬───┬───┘
                           │   │   │   │   │
                     ┌─────┘   │   │   │   └─────┐
                     │         │   │   │         │
               ┌─────▼──┐ ┌───▼───▼───▼───┐ ┌───▼────┐
               │Tenant A │ │  Tenant B     │ │Tenant C│
               │group_a  │ │  group_b      │ │group_c │
               └─────────┘ └───────────────┘ └────────┘
                           │
                    ┌──────▼──────┐
                    │   Neo4j     │
                    └─────────────┘
```

### Enforcing tenant isolation

```python
import os
from graphiti_core import Graphiti


class TenantAwareGraphiti:
    """Ensures each tenant can only access their own data."""

    def __init__(self, neo4j_uri: str, neo4j_user: str, neo4j_password: str):
        self.graphiti = Graphiti(
            uri=neo4j_uri,
            user=neo4j_user,
            password=neo4j_password,
        )

    async def add_episode(self, tenant_id: str, episode_body: str, **kwargs):
        """Add an episode scoped to a specific tenant."""
        return await self.graphiti.add_episode(
            episode_body=episode_body,
            group_id=tenant_id,  # Tenant isolation via group_id
            **kwargs,
        )

    async def search(self, tenant_id: str, query: str, **kwargs):
        """Search only within a specific tenant's data."""
        return await self.graphiti.search(
            query=query,
            group_ids=[tenant_id],  # Critical: scoped to tenant
            **kwargs,
        )

    async def delete_tenant_data(self, tenant_id: str):
        """GDPR right-to-erasure: delete all data for a tenant."""
        # This deletes all episodes, entities, and edges for this group
        await self.graphiti.delete_group(group_id=tenant_id)
```

### group_id naming conventions

| Pattern | Example | Use case |
|---------|---------|----------|
| `tenant:{id}` | `tenant:abc123` | SaaS multi-tenant |
| `project:{id}` | `project:quantumcart` | Project-based isolation |
| `user:{id}` | `user:user_42` | Per-user knowledge base |
| `org:{id}:dept:{dept}` | `org:acme:dept:eng` | Hierarchical isolation |

### Critical warning: never allow cross-tenant querying

```python
# ❌ DANGEROUS: Allows cross-tenant data leaks
async def search_across_tenants(graphiti, tenant_ids: list[str], query: str):
    return await graphiti.search(query=query, group_ids=tenant_ids)

# ✅ SAFE: Only query within the authenticated tenant
async def search_safe(graphiti, authenticated_tenant: str, query: str):
    return await graphiti.search(query=query, group_ids=[authenticated_tenant])
```

### Application-level authorization check

```python
from fastapi import FastAPI, Depends, HTTPException

app = FastAPI()


async def get_current_tenant(request) -> str:
    """Extract tenant ID from auth token (JWT, API key, etc.)."""

    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # Validate token and extract tenant_id
    tenant_id = decode_jwt(token).get("tenant_id")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return tenant_id


@app.post("/episodes")
async def add_episode(
    body: str,
    tenant_id: str = Depends(get_current_tenant),
):
    """Only the authenticated tenant can add episodes to their group."""
    tg = TenantAwareGraphiti("bolt://...", "neo4j", os.getenv("NEO4J_PASSWORD"))
    return await tg.add_episode(tenant_id=tenant_id, episode_body=body)


@app.get("/search")
async def search(
    query: str,
    tenant_id: str = Depends(get_current_tenant),
):
    """Only search within the authenticated tenant's data."""
    tg = TenantAwareGraphiti("bolt://...", "neo4j", os.getenv("NEO4J_PASSWORD"))

    # ❗ CRITICAL: tenant_id comes from auth, NOT from user input
    return await tg.search(tenant_id=tenant_id, query=query)
```

---

## 2. Neo4j Authentication and Access Control

### Creating dedicated Neo4j users

Never use the `neo4j` admin user for application access. Create
role-specific users:

```cypher
-- Create a read-only user for search queries
CREATE USER graphiti_reader
  SET PASSWORD 'strong-reader-password'
  CHANGE NOT REQUIRED;

GRANT ROLE reader TO graphiti_reader;

-- Create a read-write user for ingestion
CREATE USER graphiti_writer
  SET PASSWORD 'strong-writer-password'
  CHANGE NOT REQUIRED;

GRANT ROLE publisher TO graphiti_writer;

-- Create an admin user for operations (backup, monitoring)
CREATE USER graphiti_ops
  SET PASSWORD 'strong-ops-password'
  CHANGE NOT REQUIRED;

GRANT ROLE admin TO graphiti_ops;
```

### Database-level permissions

```cypher
-- Fine-grained access control

-- Reader can only query graph data
GRANT MATCH {*} ON GRAPH neo4j TO graphiti_reader;
GRANT READ {*} ON GRAPH neo4j TO graphiti_reader;

-- Writer can create and update nodes/edges
GRANT MATCH {*} ON GRAPH neo4j TO graphiti_writer;
GRANT READ {*} ON GRAPH neo4j TO graphiti_writer;
GRANT WRITE {*} ON GRAPH neo4j TO graphiti_writer;

-- Prevent writer from modifying schema
DENY CREATE ON INDEX TO graphiti_writer;
DENY CREATE ON CONSTRAINT TO graphiti_writer;
DENY DROP ON INDEX TO graphiti_writer;
DENY DROP ON CONSTRAINT TO graphiti_writer;

-- Ops user can manage database
GRANT ACCESS ON DATABASE neo4j TO graphiti_ops;
GRANT START ON DATABASE neo4j TO graphiti_ops;
GRANT STOP ON DATABASE neo4j TO graphiti_ops;
```

### Password policies

```cypher
-- Enforce strong passwords for all Neo4j users
CALL dbms.security.config.set(
  'dbms.security.auth_minimum_password_length', '16'
);

-- Enable password expiry (90 days)
CALL dbms.security.config.set(
  'dbms.security.auth_password_expiration_days', '90'
);

-- Account lockout after failed attempts
CALL dbms.security.config.set(
  'dbms.security.auth_lock_threshold', '5'
);
CALL dbms.security.config.set(
  'dbms.security.auth_lock_duration_seconds', '900'
); -- 15 minutes
```

### Application connection with limited user

```python
import os
from graphiti_core import Graphiti

# Use limited-privilege credentials, NOT the admin user
graphiti = Graphiti(
    uri=os.getenv("NEO4J_URI"),
    user=os.getenv("NEO4J_WRITER_USER", "graphiti_writer"),
    password=os.getenv("NEO4J_WRITER_PASSWORD"),
)
```

---

## 3. Network Security

### TLS configuration for Neo4j

Production deployments MUST use TLS for all Bolt connections.

#### Server-side TLS (Neo4j configuration)

```ini
# neo4j.conf
dbms.connector.bolt.tls_level=REQUIRED
dbms.connector.bolt.ssl_cert=/path/to/neo4j.crt
dbms.connector.bolt.ssl_key=/path/to/neo4j.key
```

#### Client-side TLS (Python)

```python
from graphiti_core import Graphiti

# Use bolt+s (TLS required)
graphiti = Graphiti(
    uri="bolt+s://neo4j.example.com:7687",
    user="graphiti_writer",
    password=os.getenv("NEO4J_PASSWORD"),
    # For self-signed certs in dev:
    # trust="TRUST_ALL_CERTIFICATES",  # NEVER use in production
)
```

### Network segmentation

```
┌─────────────────────────────────────────────────────────┐
│                     Production VPC                        │
│                                                          │
│  ┌──────────────┐          ┌────────────────────────┐   │
│  │  App Tier     │          │  Database Tier          │   │
│  │              │          │                         │   │
│  │  API Server  ├──────────►  Neo4j (private subnet) │   │
│  │  (public     │  bolt:   │  - Port 7687 from app   │   │
│  │   subnet)    │  7687    │    tier only             │   │
│  └──────────────┘          │  - Port 7474 from admin  │   │
│                             │    VPN only              │   │
│                             └────────────────────────┘   │
│                                        │                  │
│                                        │ s3:              │
│                                        ▼                  │
│                             ┌────────────────────────┐   │
│                             │  Backup Storage (S3)    │   │
│                             └────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Firewall rules (example for AWS security groups)

```hcl
# Database security group
resource "aws_security_group" "neo4j" {
  name = "neo4j-sg"

  # Bolt port -- only from app tier
  ingress {
    from_port   = 7687
    to_port     = 7687
    protocol    = "tcp"
    security_groups = [aws_security_group.app.id]
    description = "Neo4j Bolt from app tier"
  }

  # HTTP port -- only from admin VPN
  ingress {
    from_port   = 7474
    to_port     = 7474
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # VPN CIDR
    description = "Neo4j HTTP from admin VPN"
  }

  # Cluster communication (Enterprise)
  ingress {
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    self        = true
    description = "Neo4j cluster discovery"
  }

  # No public internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Application security group
resource "aws_security_group" "app" {
  name = "app-sg"

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }

  # No SSH from internet -- use bastion host or VPN
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]  # VPN CIDR
    description = "SSH from admin VPN"
  }
}
```

---

## 4. API Key Management for LLM Providers

### Environment variables (minimum)

```bash
# .env.production -- NEVER commit to version control
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Or use a different provider
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Secrets management

```python
import os

def get_llm_api_key() -> str:
    """Get the LLM API key from the most secure available source."""

    # Priority: secrets manager > env var > local file (dev only)

    # 1. Try AWS Secrets Manager
    try:
        import boto3
        from botocore.exceptions import ClientError

        client = boto3.client("secretsmanager")
        response = client.get_secret_value(SecretId="graphiti/llm-api-key")
        return response["SecretString"]
    except (ImportError, ClientError):
        pass

    # 2. Try environment variable
    key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key

    # 3. Fallback for local dev only
    raise RuntimeError(
        "LLM API key not found. Set OPENAI_API_KEY or ANTHROPIC_API_KEY."
    )
```

### Key rotation

```python
import os
from datetime import datetime, timedelta


class ApiKeyRotator:
    """Automatically rotate API keys before expiry."""

    def __init__(self, secret_id: str):
        self.secret_id = secret_id

    async def rotate_if_needed(self) -> bool:
        """Check if key is near expiry and rotate."""
        import boto3

        client = boto3.client("secretsmanager")
        secret = client.describe_secret(SecretId=self.secret_id)

        # Check if rotation is configured
        if "RotationEnabled" not in secret or not secret["RotationEnabled"]:
            return False

        # Check last rotation date
        last_rotated = secret.get("LastRotatedDate", datetime.min)
        days_since_rotation = (datetime.utcnow() - last_rotated).days

        if days_since_rotation > 60:
            # Trigger rotation
            client.rotate_secret(SecretId=self.secret_id)
            return True
        return False
```

---

## 5. PII Detection and Handling

### Identifying PII in episode text

```python
import re


def detect_pii(text: str) -> dict[str, list[str]]:
    """Detect potential PII in text before storing in Graphiti."""

    findings = {}

    # Email addresses
    emails = re.findall(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
    if emails:
        findings["emails"] = emails

    # Phone numbers (US format)
    phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phones:
        findings["phones"] = phones

    # Social Security Numbers (US)
    ssns = re.findall(r'\b\d{3}-\d{2}-\d{4}\b', text)
    if ssns:
        findings["ssns"] = ssns

    # Credit card numbers (basic Luhn check)
    cc_pattern = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
    potential_ccs = re.findall(cc_pattern, text)
    if potential_ccs:
        findings["credit_cards"] = potential_ccs

    # IP addresses
    ips = re.findall(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', text)
    if ips:
        # Filter out obviously non-PII IPs (local ranges)
        private_ips = [ip for ip in ips if ip.startswith(("10.", "192.168.", "172.16.", "127."))]
        if private_ips:
            findings["private_ips"] = private_ips

    return findings


def redact_pii(text: str) -> str:
    """Redact PII from episode text."""

    pii = detect_pii(text)

    if not pii:
        return text

    redacted = text
    for pii_type, values in pii.items():
        for value in values:
            # Replace with placeholder
            placeholder = f"[REDACTED_{pii_type.upper()}]"
            redacted = redacted.replace(value, placeholder)

    return redacted


async def add_episode_safe(graphiti, episode_body: str, **kwargs):
    """Add an episode after PII detection and redaction."""

    pii_found = detect_pii(episode_body)
    if pii_found:
        print(f"WARNING: PII detected in episode: {pii_found}")
        episode_body = redact_pii(episode_body)
        print(f"PII redacted before storage.")

    return await graphiti.add_episode(episode_body=episode_body, **kwargs)
```

### PII handling strategies

| Strategy | Description | Best for |
|----------|-------------|----------|
| **Redact** | Replace PII with placeholders | General purpose |
| **Hash** | Store irreversible hash of PII | Analytics without raw access |
| **Encrypt** | Store encrypted PII, decrypt on access | Regulated data |
| **Reject** | Block episodes containing PII | Strict compliance |
| **Tag** | Tag entities as PII, restrict query access | Fine-grained access control |

---

## 6. GDPR Compliance

### Right-to-erasure (Article 17)

Graphiti supports deleting all data for a specific tenant or episode:

```python
# Delete all data for a tenant (complete erasure)
await graphiti.delete_group(group_id="tenant:abc123")

# Delete a specific episode (single data point erasure)
await graphiti.delete_episode(episode_id="episode-uuid-here")
```

### Data retention

```python
import asyncio
from datetime import datetime, timedelta, timezone


async def enforce_retention_policy(
    graphiti,
    retention_days: int = 365,
):
    """Delete episodes older than the retention period."""

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    # Retrieve all groups
    # Check each episode's reference_time
    # Delete episodes older than the cutoff

    print(f"Retention policy: deleting episodes older than {cutoff_date.date()}")
    # Implementation depends on how you track episode timestamps
```

### GDPR data flow diagram

```
User request for erasure
        │
        ▼
Verify identity ──── Failed → Log + notify user
        │
        ▼  Success
Find all groups for user
        │
        ▼
Call delete_group(group_id) for each group
        │
        ▼
Confirm deletion in audit log
        │
        ▼
Notify user of completion (within 30 days)
```

### Data portability (Article 20)

```python
import json


async def export_user_data(graphiti, tenant_id: str) -> dict:
    """Export all data for a tenant in a portable format."""

    episodes = await graphiti.retrieve_episodes(group_ids=[tenant_id])

    export = {
        "exported_at": datetime.utcnow().isoformat(),
        "tenant_id": tenant_id,
        "episodes": [],
    }

    for ep in episodes:
        export["episodes"].append({
            "name": ep.name,
            "body": ep.body,
            "source": str(ep.source),
            "created_at": ep.created_at.isoformat(),
            "reference_time": ep.reference_time.isoformat(),
        })

    return export
```

---

## 7. Data Residency Considerations

### Region-based data isolation

```python
class RegionalGraphiti:
    """Route data to Neo4j instances in the appropriate region."""

    def __init__(self):
        self.instances = {
            "us-east": Graphiti(uri="bolt://neo4j-us.example.com:7687", ...),
            "eu-west": Graphiti(uri="bolt://neo4j-eu.example.com:7687", ...),
            "ap-southeast": Graphiti(uri="bolt://neo4j-ap.example.com:7687", ...),
        }

    def _select_instance(self, region: str) -> Graphiti:
        if region not in self.instances:
            raise ValueError(f"Unsupported region: {region}")
        return self.instances[region]

    async def add_episode(self, region: str, **kwargs):
        return await self._select_instance(region).add_episode(**kwargs)

    async def search(self, region: str, **kwargs):
        return await self._select_instance(region).search(**kwargs)
```

### Regional compliance matrix

| Region | Regulation | Requirements |
|--------|-----------|--------------|
| EU | GDPR | Right to erasure, data portability, 72h breach notification |
| US (California) | CCPA | Right to know, right to delete, opt-out of sale |
| US (Healthcare) | HIPAA | BAA required, audit logs, encryption at rest |
| Brazil | LGPD | Similar to GDPR, consent requirements |
| Japan | APPI | Cross-border transfer restrictions |
| India | DPDP Act | Data localization, consent management |

---

## 8. Audit Logging

### Application-level audit logging

```python
import json
import logging
from datetime import datetime, timezone

audit_logger = logging.getLogger("graphiti_audit")
audit_logger.setLevel(logging.INFO)

# Add a secure handler (write to a separate, append-only log)
handler = logging.FileHandler("/var/log/graphiti/audit.log")
handler.setFormatter(logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
))
audit_logger.addHandler(handler)


async def audit_log(
    action: str,
    actor: str,
    tenant_id: str,
    resource: str,
    details: dict = None,
):
    """Log an auditable event."""

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "tenant_id": tenant_id,
        "resource": resource,
        "details": details or {},
    }

    audit_logger.info(json.dumps(event))
```

### Events to audit

| Event type | Action | Data to log |
|-----------|--------|-------------|
| **Authentication** | User login | actor, IP, timestamp, success/failure |
| **Data access** | Search query | actor, tenant, query text (redacted), result count |
| **Data modification** | Episode added | actor, tenant, episode name, size |
| **Data deletion** | Episode/group deleted | actor, tenant, resource deleted |
| **Admin action** | Config change | actor, setting changed, old/new values |
| **Security event** | Rate limit hit | actor, IP, endpoint |
| **LLM API call** | External API | actor, model, tokens used, cost |

### Example: query audit middleware

```python
from fastapi import FastAPI, Request
import time

app = FastAPI()


@app.middleware("http")
async def audit_middleware(request: Request, call_next):
    """Log all requests for audit purposes."""

    start = time.time()
    response = await call_next(request)
    duration = time.time() - start

    # Extract actor from auth context
    actor = request.headers.get("X-User-Id", "anonymous")
    tenant = request.headers.get("X-Tenant-Id", "unknown")

    await audit_log(
        action=f"{request.method} {request.url.path}",
        actor=actor,
        tenant_id=tenant,
        resource=request.url.path,
        details={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000),
            "ip": request.client.host,
        },
    )

    return response
```

---

## 9. SOC 2 and HIPAA: Zep Cloud vs Self-Hosted

### SOC 2

| Requirement | Zep Cloud | Self-Hosted |
|-------------|-----------|-------------|
| Encryption at rest | Yes (managed) | Your responsibility |
| Encryption in transit | Yes (TLS 1.2+) | Your responsibility |
| Access controls | SSO + RBAC | Neo4j auth + your app layer |
| Audit logging | Built-in | You implement |
| Penetration testing | Annual (SOC 2 report) | Your responsibility |
| Vendor management | N/A | You manage all vendors |
| Incident response | Zep handles | You handle |

### HIPAA

| Requirement | Zep Cloud | Self-Hosted |
|-------------|-----------|-------------|
| BAA (Business Associate Agreement) | Available (enterprise) | Not needed (you are covered entity) |
| ePHI encryption | Yes | Your responsibility |
| Access control | Yes (SSO, MFA) | Neo4j auth + your app |
| Audit controls | Built-in | You implement |
| Integrity controls | Managed backups | Your backup strategy |
| Person/entity authentication | SSO + MFA | Your identity system |
| Transmission security | TLS 1.2+ | TLS 1.2+ |

### Decision matrix for compliance

```
Do you need SOC 2 or HIPAA?
│
├── YES, and you want the easiest path
│   → Zep Cloud Enterprise
│     Pros: Compliance built-in, no audit burden
│     Cons: Data must be in Zep's cloud, higher cost
│
├── YES, and you need on-premises
│   → Self-hosted with compliance program
│     Pros: Full control, data stays on-prem
│     Cons: You own the compliance burden
│     Required:
│       - Encryption at rest (AES-256)
│       - Encryption in transit (TLS 1.2+)
│       - Audit logging (all access logged)
│       - Access controls (RBAC, MFA)
│       - Backup and disaster recovery
│       - Incident response plan
│       - Vendor risk assessments
│
└── NO
    → Either Zep Cloud or self-hosted, compliance optional
```

---

## 10. Security Checklist for Production Deployment

### Pre-deployment

- [ ] Neo4j admin password is changed from default and stored in a secrets manager
- [ ] Dedicated Neo4j users created (reader, writer, ops) -- never use `neo4j` admin
- [ ] TLS enabled for all Bolt connections (certificate from a trusted CA)
- [ ] Network security groups restrict access to Neo4j ports
- [ ] LLM API keys are in a secrets manager, not in code or .env
- [ ] Database is not exposed to the public internet
- [ ] Container images are scanned for vulnerabilities
- [ ] All dependencies (Python packages, Neo4j plugins) are up to date
- [ ] Backups are configured and tested (restore drill completed)
- [ ] Audit logging is enabled and logs are sent to a central location
- [ ] Monitoring and alerting are configured for security events

### Ongoing

- [ ] Neo4j password rotated every 90 days
- [ ] LLM API keys rotated before expiry
- [ ] TLS certificates renewed before expiry
- [ ] Security patches applied within 30 days
- [ ] Backup restore tested quarterly
- [ ] Access logs reviewed monthly for unusual activity
- [ ] User access reviewed quarterly (terminate stale accounts)
- [ ] Penetration testing performed annually
- [ ] Incident response plan reviewed and updated annually
- [ ] Compliance documentation updated as regulations change

### Incident response

- [ ] Runbook for data breach scenarios
- [ ] Contact information for Neo4j support / cloud provider
- [ ] Procedure for emergency tenant data deletion
- [ ] Procedure for revoking compromised API keys
- [ ] Communication template for breach notification (72h for GDPR)

---

## 11. Threat Model

### Assets

| Asset | Sensitivity | Description |
|-------|-------------|-------------|
| Episode text | Medium-High | Contains facts, may include PII |
| Entity graph | Medium | Relationships between entities |
| LLM API keys | Critical | Used for all LLM extraction calls |
| Neo4j credentials | Critical | Full database access |
| Neo4j database | Critical | All stored knowledge |
| Query logs | Medium | May reveal query patterns and interests |

### Threat scenarios and mitigations

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Cross-tenant data access | Medium | High | group_id enforcement, auth middleware |
| LLM API key leak | Medium | High | Secrets manager, key rotation, audit logging |
| Neo4j credential leak | Low | Critical | Dedicated users, least privilege, TLS |
| SQL/Cypher injection | Low | High | Parameterized queries (built into Graphiti SDK) |
| Insecure direct object reference | Medium | High | Server-side tenant validation, never trust user input |
| Data exfiltration via search | Medium | Medium | Query logging, rate limiting, PII detection |
| Ransomware / data destruction | Low | Critical | Immutable backups, least privilege access |
| Insider threat | Low | High | Audit logging, access reviews, separation of duties |
| Supply chain attack (dependency) | Low | High | Dependency scanning, lock files, minimal dependencies |
| Denial of service | Medium | Medium | Rate limiting, connection pooling, resource limits |

### Trust boundaries

```
[Internet]
    │
    ▼
[Load Balancer / API Gateway]
    │  TLS termination, rate limiting, WAF
    ▼
[Application Server]
    │  Tenant auth, PII redaction, audit logging
    ▼
[Neo4j Database]
    │  TLS, RBAC, network isolation
    ▼
[Backup Storage (S3/Blob)]
    │  Encryption at rest, access control
    ▼
[LLM API (external)]
```

**Trust boundaries are between every layer.** Never assume that a request
reaching the application server is authentic -- validate at every layer.
