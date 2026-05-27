# MCP Developer & Technical Guide — Build Apps, Use APIs, Create AI Workflows

**Companion to the [MCP Bible](mcp.md).** This guide focuses on the *how* — patterns, code, deployment, and production practices for developers building with MCP. If you need the protocol reference (JSON-RPC format, lifecycle, capability negotiation), see `mcp.md`. If you want practical recipes and patterns, you're in the right place.

---

## Table of Contents

### Part I: Building MCP Servers
1. [Zero to MCP Server — 10-Minute Walkthrough](#1-zero-to-mcp-server--10-minute-walkthrough)
2. [Choosing stdio vs HTTP Transport](#2-choosing-stdio-vs-http-transport)
3. [Designing Tool Signatures](#3-designing-tool-signatures)
4. [Resources vs Tools vs Prompts — Decision Framework](#4-resources-vs-tools-vs-prompts--decision-framework)
5. [Implementing Sampling — Server-Initiated LLM Chains](#5-implementing-sampling--server-initiated-llm-chains)
6. [Elicitation Patterns](#6-elicitation-patterns)
7. [Completions — Smart Autocomplete for Tool Args](#7-completions--smart-autocomplete-for-tool-args)
8. [Progress Reporting & Long-Running Operations](#8-progress-reporting--long-running-operations)
9. [Error Handling & Structured Error Responses](#9-error-handling--structured-error-responses)
10. [Testing MCP Servers](#10-testing-mcp-servers)
11. [Packaging for Distribution](#11-packaging-for-distribution)
12. [Multi-Client State in HTTP Servers](#12-multi-client-state-in-http-servers)

### Part II: API Integration Patterns
13. [Wrapping REST APIs as MCP Tools](#13-wrapping-rest-apis-as-mcp-tools)
14. [Streaming APIs to MCP](#14-streaming-apis-to-mcp)
15. [Rate Limiting, Retries & Resilience](#15-rate-limiting-retries--resilience)
16. [Authentication Passthrough](#16-authentication-passthrough)
17. [Webhook Ingestion via MCP Resources](#17-webhook-ingestion-via-mcp-resources)
18. [GraphQL as MCP Tools](#18-graphql-as-mcp-tools)
19. [Database-Backed MCP Servers](#19-database-backed-mcp-servers)
20. [File System Tools — Safe Path Sandboxing](#20-file-system-tools--safe-path-sandboxing)

### Part III: AI Workflows & Agents
21. [Chaining MCP Tools — Multi-Step Agent Workflows](#21-chaining-mcp-tools--multi-step-agent-workflows)
22. [Using Sampling for Self-Critique & Iterative Refinement](#22-using-sampling-for-self-critique--iterative-refinement)
23. [Multi-Agent Patterns with Shared MCP Servers](#23-multi-agent-patterns-with-shared-mcp-servers)
24. [RAG with MCP — Embedding Search as a Tool/Resource](#24-rag-with-mcp--embedding-search-as-a-toolresource)
25. [Human-in-the-Loop Workflows with Elicitation](#25-human-in-the-loop-workflows-with-elicitation)
26. [Prompt Engineering MCP Tool Descriptions](#26-prompt-engineering-mcp-tool-descriptions)
27. [Structured Output Extraction via Sampling](#27-structured-output-extraction-via-sampling)
28. [Building a Code Review Agent](#28-building-a-code-review-agent)

### Part IV: Production & DevOps
29. [Deploying HTTP MCP Servers Behind a Reverse Proxy](#29-deploying-http-mcp-servers-behind-a-reverse-proxy)
30. [Observability — Logging, Metrics & Tracing](#30-observability--logging-metrics--tracing)
31. [Securing MCP HTTP Endpoints](#31-securing-mcp-http-endpoints)
32. [CI/CD Pipelines for MCP Server Projects](#32-cicd-pipelines-for-mcp-server-projects)
33. [Health Checks & Graceful Shutdown](#33-health-checks--graceful-shutdown)
34. [Load Testing & Capacity Planning](#34-load-testing--capacity-planning)

### Part V: Advanced Patterns
35. [Dynamic Tool Registration](#35-dynamic-tool-registration)
36. [Resource Subscriptions — Pushing Live Updates](#36-resource-subscriptions--pushing-live-updates)
37. [Cross-Server Composition](#37-cross-server-composition)
38. [Versioning MCP Server APIs](#38-versioning-mcp-server-apis)
39. [Feature Flags & Staged Rollout](#39-feature-flags--staged-rollout)
40. [Building Custom MCP Clients](#40-building-custom-mcp-clients)

---

## Part I: Building MCP Servers

### 1. Zero to MCP Server — 10-Minute Walkthrough

**Goal:** Build a working MCP server from scratch, configure it in Claude Code, and call a tool.

#### Step 1: Project Setup (1 min)

```bash
mkdir my_mcp && cd my_mcp
python -m venv venv && source venv/bin/activate   # or venv\Scripts\activate on Windows
pip install mcp
```

#### Step 2: Write the Server (5 min)

Create `server.py`:

```python
#!/usr/bin/env python3
import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("my-first-server")

@server.tool()
async def hello(name: str, language: str = "en") -> list[TextContent]:
    """Greet someone in their preferred language.

    Args:
        name: Who to greet
        language: "en" for English, "es" for Spanish, "fr" for French
    """
    greetings = {"en": f"Hello, {name}!", "es": f"¡Hola, {name}!", "fr": f"Bonjour, {name}!"}
    msg = greetings.get(language, greetings["en"])
    return [TextContent(type="text", text=msg)]

@server.tool()
async def add(a: float, b: float) -> list[TextContent]:
    """Add two numbers together.

    Args:
        a: First number
        b: Second number
    """
    return [TextContent(type="text", text=str(a + b))]

@server.resource("hello://stats")
async def stats() -> str:
    return json.dumps({"server": "my-first-server", "version": "0.1.0"})

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
```

**What just happened:**
- `Server("my-first-server")` — creates the MCP server with a name
- `@server.tool()` — registers a callable tool; the docstring becomes the tool description
- `@server.resource("uri")` — exposes read-only data at a URI
- `StdioServerTransport()` — uses stdin/stdout as the communication channel
- `server.run(transport)` — starts the JSON-RPC loop

#### Step 3: Configure Claude Code (1 min)

Add to `.claude/settings.local.json`:

```json
{
  "mcpServers": {
    "my-first": {
      "type": "stdio",
      "command": "python",
      "args": ["server.py"]
    }
  }
}
```

#### Step 4: Test It (3 min)

Restart Claude Code, then ask:

> "Say hello to Maria in Spanish using the my-first server"

Or use the `/mcp` command to check server status:

> `/mcp list`

#### The Full Tool Signature Breakdown

```python
@server.tool()
async def my_tool(
    required_str: str,             # Required string
    optional_int: int = 42,        # Optional with default
    optional_float: float = 3.14,  # Float default
    flag: bool = False,            # Boolean flag
    choices: str = "option_a",     # Will show as enum if you list options in docstring
) -> list[TextContent]:
    """Short description of what the tool does.  ← Claude reads this!

    Args:
        required_str: Description shown to Claude for argument selection
        optional_int: Claude uses these descriptions to match args to user intent
        optional_float: Be specific — "Timeout in seconds (0.5-30.0)"
        flag: Describe what happens when True
        choices: Valid values: "option_a", "option_b", "option_c"
    """
    ...
```

**Key rules:**
1. The docstring **is** the tool description — Claude reads it to decide when to call the tool
2. `Args:` section is parsed for per-parameter descriptions
3. Type hints determine the JSON Schema sent to the client
4. Return type is always `list[TextContent]` (or `list[TextContent | ImageContent | AudioContent]`)
5. Function name becomes the tool name (use `snake_case`)

#### Common First-Server Mistakes

| Mistake | Fix |
|---------|-----|
| Forgetting `async` | All tool functions must be `async def` |
| Returning a plain string | Must return `[TextContent(type="text", text=...)]` |
| No docstring | Claude won't know when to use your tool |
| Missing type hints | Arguments won't have proper JSON Schema |
| Wrong Python path in config | Use absolute path or path relative to project root |

---

### 2. Choosing stdio vs HTTP Transport

See `mcp.md` Section 5 for the protocol details. This section focuses on the *decision*.

#### Decision Matrix

| Factor | stdio | HTTP/SSE |
|--------|-------|----------|
| **Setup complexity** | Minimal — one config entry | Need to run a server process + configure URL |
| **Network access** | Local only | Remote, any machine that can reach the URL |
| **Multi-client** | No — one Claude per process | Yes — many Claude instances share one server |
| **State sharing** | Process-local | Shared across all connected clients |
| **Persistence** | Dies with Claude Code | Survives independently |
| **Latency** | Zero network overhead | Network round-trip per call |
| **Debugging** | `print()` to stderr | Standard HTTP tooling (curl, Postman, logs) |
| **Deployment** | Nothing to deploy | Need to host a long-running service |
| **Auth** | Not needed (local trust boundary) | TLS, OAuth, API keys |
| **Scaling** | N/A (1:1) | Load balancer, multiple replicas |

#### When to Use stdio

- The server only needs local resources (files, OS, local DB)
- One user, one Claude instance
- The server is simple and stateless
- You don't want to manage infrastructure
- Examples: file conversion, local code analysis, desktop notifications

#### When to Use HTTP

- Multiple team members share the server
- The server wraps a shared service (deploy pipeline, feature flags, on-call schedule)
- State must persist across Claude sessions
- You need independent scaling
- You want standard HTTP observability (logs, metrics, tracing)
- Examples: team dashboard, shared secret vault, deployment coordinator

#### Template: stdio Server

```python
from mcp.server import Server
from mcp.server.stdio import StdioServerTransport

server = Server("my-server")

@server.tool()
async def my_tool(x: str) -> list[TextContent]:
    ...

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
```

#### Template: HTTP/SSE Server

```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

server = Server("my-server")

@server.tool()
async def my_tool(x: str) -> list[TextContent]:
    ...

async def handle_sse(request):
    transport = SseServerTransport("/messages")
    async with transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(streams[0], streams[1],
                         server.create_initialization_options())

app = Starlette(routes=[
    Route("/sse", handle_sse, methods=["GET"]),
])

# Run: uvicorn server:app --port 9020
```

#### Hybrid: stdio in Dev, HTTP in Prod

```python
async def main():
    if os.environ.get("MCP_TRANSPORT") == "http":
        import uvicorn
        app = build_starlette_app(server)
        uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "9020")))
    else:
        transport = StdioServerTransport()
        await server.run(transport)
```

---

### 3. Designing Tool Signatures

The tool signature is how Claude understands your tool. A well-designed signature makes the difference between Claude calling your tool correctly 90% of the time vs 30%.

#### The Anatomy of a Great Tool

```python
@server.tool()
async def search_logs(
    query: str,
    service: str = "all",
    severity: str = "error",
    since_minutes: int = 60,
    max_results: int = 100,
) -> list[TextContent]:
    """Search application logs across services with filtering.

    Use this when the user wants to find specific log entries, debug errors,
    or investigate recent activity. Supports full-text search and filtering
    by service name, severity level, and time window.

    Args:
        query: Search term or Lucene query syntax. Use * for wildcard.
              Examples: "timeout", "status:500", "user_id:12345"
        service: Service name to filter by, or "all" for every service.
                 Valid: "api", "worker", "frontend", "db", "cache", "all"
        severity: Minimum log level. "debug" < "info" < "warn" < "error" < "fatal"
        since_minutes: Look back this many minutes from now. Max 1440 (24 hours).
        max_results: Cap on results returned. 10-500. Higher = slower.
    """
```

**Why this works:**
1. **The first line** says exactly what it does and when to use it
2. **"Use this when..."** guides Claude on tool selection
3. **Per-arg examples** show valid values and syntax
4. **Constraints are explicit** — "Max 1440", "10-500"
5. **Ordering hint** for enum-like strings — "debug < info < warn..."

#### Naming Conventions

| Style | Example | When |
|-------|---------|------|
| `verb_noun` | `search_logs`, `create_ticket`, `delete_user` | Default — action-oriented |
| `noun_action` | `log_search`, `ticket_create` | When grouping by domain matters |
| `get_*` | `get_status`, `get_config` | Read-only fetchers |
| `list_*` | `list_users`, `list_deployments` | Collections, supports pagination |
| `set_*` | `set_feature_flag`, `set_config` | Single-value writers |
| `check_*` | `check_health`, `check_port` | Boolean or status queries |

#### The Docstring Matters Most

Claude uses the tool description (docstring first paragraph) for **tool selection** (which tool to call) and the `Args:` section for **argument filling** (what values to pass). Write both for Claude, not for a human reading docs.

**Bad:**
```python
"""Process data.

Args:
    data: The data
    mode: Processing mode
"""
```

**Good:**
```python
"""Parse and validate a CSV file, returning row counts and schema info.

Use when the user has a CSV file and wants to understand its structure,
check for errors, or get summary statistics before processing.

Args:
    file_path: Absolute path to the CSV file. Must exist and be readable.
    mode: "schema" returns column names and types; "stats" returns row count,
          null counts, and min/max values per column; "validate" checks
          every row against expected schema and returns errors.
    delimiter: Column separator. Usually "," — use "\t" for TSV files.
    has_header: Whether the first row contains column names. Default True.
"""
```

#### Argument Types & What Claude Understands

| Python Type | JSON Schema | Claude Sees |
|-------------|-------------|-------------|
| `str` | `{"type": "string"}` | Free text — provide examples in docstring |
| `int` | `{"type": "integer"}` | Whole number — give range in docstring |
| `float` | `{"type": "number"}` | Decimal number — specify precision |
| `bool` | `{"type": "boolean"}` | True/False toggle |
| `list[str]` | `{"type": "array", "items": {"type": "string"}}` | List of strings |
| `Literal["a", "b"]` | `{"type": "string", "enum": ["a", "b"]}` | Constrained choice — BEST for fixed options |
| `Optional[str]` | `{"type": "string"}` with no default | Can be omitted |

**Always prefer `Literal["a", "b", "c"]` over `str` with "Valid: a, b, c" in the docstring.** The JSON Schema enum is machine-readable, so Claude can validate before calling.

```python
from typing import Literal

@server.tool()
async def set_brightness(
    level: Literal["off", "low", "medium", "high", "max"],
) -> list[TextContent]:
    """Set display brightness to a preset level."""
    ...
```

#### Tool Annotations

```python
from mcp.types import Tool

@server.tool(
    annotations={
        "readOnlyHint": False,
        "destructiveHint": True,
        "idempotentHint": False,
        "openWorldHint": True,
    }
)
async def delete_user(user_id: str) -> list[TextContent]:
    """Permanently delete a user and all their data."""
    ...
```

| Annotation | Meaning | When to Set True |
|------------|---------|-----------------|
| `readOnlyHint` | Tool doesn't modify anything | Search, query, read operations |
| `destructiveHint` | Tool may destroy data | Delete, drop, truncate, overwrite |
| `idempotentHint` | Same call = same result | Set, update, upsert |
| `openWorldHint` | Interacts with external world | API calls, network, external services |

---

### 4. Resources vs Tools vs Prompts — Decision Framework

#### When to Use Each Primitive

```
"Is this something Claude should DO?"
  ├── YES → Tool
  │         (actions, side effects, computation, external calls)
  │
  └── NO → "Is this data Claude should READ?"
            ├── YES → Resource
            │         (files, configs, dashboards, live state)
            │
            └── NO → "Is this a reusable CONVERSATION STARTER?"
                      ├── YES → Prompt
                      │         (templates, guided workflows)
                      │
                      └── NO → You don't need MCP for this
```

#### Decision Table

| What You Want | Use This | Why |
|---------------|----------|-----|
| Run a command, make a change | **Tool** | Tools are actions |
| Query a database | **Tool** | Queries are parameterized actions |
| Send an email | **Tool** | Side effect = tool |
| Expose a config file | **Resource** | It's data to read |
| Show a dashboard | **Resource** | Read-only state snapshot |
| Live system metrics | **Resource** | Subscribe for updates |
| Code review workflow | **Prompt** | Guided multi-step process |
| Meeting agenda template | **Prompt** | Reusable template |
| Generate a report | **Tool** | Computation + output |
| Read a file's contents | **Resource** | It's existing data |
| Search across sources | **Tool** | Parameterized retrieval |
| Pomodoro timer setup | **Prompt** | Templates a multi-tool workflow |

#### Pattern: Expose the Same Data as Both

```python
# Tool — parameterized, computational
@server.tool()
async def get_user(user_id: str) -> list[TextContent]:
    """Fetch a user by ID from the database."""
    user = db.query("SELECT * FROM users WHERE id = ?", user_id)
    return [TextContent(type="text", text=json.dumps(user))]

# Resource — for the "current" or "all" case
@server.resource("users://all")
async def all_users() -> str:
    """All users as a read-only resource."""
    return json.dumps(db.query("SELECT * FROM users"))

# Resource — parameterized for direct URI access
@server.resource("users://{user_id}")
async def user_resource(user_id: str) -> str:
    """Get a specific user by URI: users://abc-123"""
    return json.dumps(db.query("SELECT * FROM users WHERE id = ?", user_id))
```

#### Prompt Anatomy

```python
@server.prompt(
    name="bug-report",
    description="Template for filing a structured bug report",
    arguments={
        "component": {
            "type": "string",
            "description": "Which component has the bug?",
            "required": True,
        },
        "severity": {
            "type": "string",
            "enum": ["critical", "major", "minor", "cosmetic"],
            "description": "How severe is the issue?",
            "required": False,
        },
    },
)
async def bug_report_prompt(component: str, severity: str = "minor") -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""File a bug report for {component} (severity: {severity}).

Please gather:
1. Steps to reproduce
2. Expected behavior
3. Actual behavior
4. Screenshots or logs if relevant
5. Environment details (browser, OS, version)

Then use create_issue to file it in GitHub with labels: bug, {severity}, {component}."""
            },
        }],
    }
```

---

### 5. Implementing Sampling — Server-Initiated LLM Chains

Sampling is the most powerful MCP primitive: your server can ask Claude to generate text during tool execution. This enables multi-step reasoning, extraction, and quality loops.

**Reference:** `mcp_servers/sampling_demo_server.py` — 5 complete patterns.

#### The Core Pattern

```python
from mcp.types import CreateMessageRequestParams, ContentBlock

@server.tool()
async def analyze_with_llm(text: str) -> list[TextContent]:
    # Step 1: Ask Claude to do something
    response = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[
                ContentBlock(type="text", text=f"Analyze this text:\n\n{text}"),
            ],
            maxTokens=500,
            systemPrompt="You are a text analyst. Extract key themes and sentiment.",
        )
    )

    # Step 2: Use the response
    result = response.content[0].text if response.content else ""

    return [TextContent(type="text", text=result)]
```

#### Pattern 1: Multi-Step Chain

```python
@server.tool()
async def analyze_logs_with_sampling(log_text: str) -> list[TextContent]:
    # Step 1: Classify errors
    classify_resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Classify each log line as ERROR, WARN, or INFO. "
                f"Return JSON: [{{\"line\": N, \"level\": \"...\", \"summary\": \"...\"}}]\n\n{log_text}"
            ))],
            maxTokens=1000,
            systemPrompt="You are a log classifier. Return only valid JSON.",
        )
    )

    # Step 2: Synthesize remediation from classifications
    remediate_resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Based on these classified errors, suggest remediation steps:\n\n"
                f"{classify_resp.content[0].text}"
            ))],
            maxTokens=500,
            systemPrompt="You are an SRE. Suggest concrete fixes for each error.",
        )
    )

    return [
        TextContent(type="text", text=json.dumps({
            "classification": classify_resp.content[0].text,
            "remediation": remediate_resp.content[0].text,
        }, indent=2))
    ]
```

#### Pattern 2: Structured Extraction

```python
@server.tool()
async def extract_and_structure(raw_text: str) -> list[TextContent]:
    # Pre-process (deterministic, no LLM needed)
    cleaned = raw_text.strip().replace("\r\n", "\n")

    # LLM for understanding
    resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Extract the following as JSON:\n"
                f"- people: list of {{name, title, company}}\n"
                f"- dates: list of {{description, iso_date}}\n"
                f"- decisions: list of {{what, who, status}}\n\n"
                f"{cleaned}"
            ))],
            maxTokens=1500,
            systemPrompt="Extract structured data from meeting notes. Return valid JSON only.",
        )
    )

    return [TextContent(type="text", text=resp.content[0].text)]
```

#### Pattern 3: Generate → Review → Revise Loop

```python
@server.tool()
async def generate_with_review(topic: str, iterations: int = 2) -> list[TextContent]:
    # Initial generation
    gen_resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=f"Write a short article about: {topic}")],
            maxTokens=1000,
        )
    )
    current = gen_resp.content[0].text

    for i in range(iterations):
        # Review
        review_resp = await server.request_sampling(
            CreateMessageRequestParams(
                messages=[ContentBlock(type="text", text=(
                    f"Review this article and list 3 specific improvements:\n\n{current}"
                ))],
                maxTokens=300,
                systemPrompt="You are a critical editor. Be specific and actionable.",
            )
        )
        feedback = review_resp.content[0].text

        # Revise
        revise_resp = await server.request_sampling(
            CreateMessageRequestParams(
                messages=[ContentBlock(type="text", text=(
                    f"Original article:\n{current}\n\n"
                    f"Improvement suggestions:\n{feedback}\n\n"
                    f"Rewrite the article incorporating these improvements."
                ))],
                maxTokens=1000,
            )
        )
        current = revise_resp.content[0].text

    return [TextContent(type="text", text=current)]
```

#### Pattern 4: Decision Matrix

```python
@server.tool()
async def decision_matrix(options: list[str], criteria: list[str]) -> list[TextContent]:
    # Step 1: Score each option against each criterion
    score_resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Score each option against each criterion (0-10).\n"
                f"Options: {json.dumps(options)}\n"
                f"Criteria: {json.dumps(criteria)}\n\n"
                f"Return JSON: {{option: {{criterion: score}}}}"
            ))],
            maxTokens=500,
        )
    )

    # Step 2: Weight criteria and rank
    rank_resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Weight each criterion by importance (0-1, sum to 1) and compute "
                f"weighted scores. Rank options best to worst.\n\nScores:\n{score_resp.content[0].text}"
            ))],
            maxTokens=500,
        )
    )

    return [TextContent(type="text", text=rank_resp.content[0].text)]
```

#### Pattern 5: Batch Classification

```python
@server.tool()
async def batch_classify(items: list[str], labels: list[str]) -> list[TextContent]:
    """Classify a batch of items into predefined labels using sampling."""
    resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Classify each item into exactly one label.\n"
                f"Labels: {json.dumps(labels)}\n"
                f"Items: {json.dumps(items)}\n\n"
                f"Return JSON: {{item: label}}"
            ))],
            maxTokens=500,
        )
    )

    return [TextContent(type="text", text=resp.content[0].text)]
```

#### Sampling Capability Check

Not all clients support sampling. Your server can check:

```python
# During initialization, check if the client declared sampling capability
def __init__(self):
    self._sampling_supported = False

# After handshake:
# self._sampling_supported = "sampling" in client_capabilities

@server.tool()
async def smart_tool(x: str) -> list[TextContent]:
    if not self._sampling_supported:
        # Fallback: deterministic processing
        return [TextContent(type="text", text=f"Processed (no LLM): {x.upper()}")]

    # Full path: use sampling
    resp = await server.request_sampling(...)
    return [TextContent(type="text", text=resp.content[0].text)]
```

#### Sampling Best Practices

1. **Always constrain `maxTokens`** — don't let the LLM generate unbounded text
2. **Use `systemPrompt`** to set role and output format
3. **Request structured output** — "Return JSON", "Return only the answer"
4. **Validate the response** — parse JSON, check fields, retry on failure
5. **Have a fallback** — what happens if sampling is not supported or fails?
6. **Mind the cost** — every `request_sampling` call costs tokens
7. **Don't loop forever** — always have a maximum iteration count

---

### 6. Elicitation Patterns

Elicitation pauses tool execution to ask the user a question. Use it when the tool needs a decision only the user can make.

```python
from mcp.types import ElicitRequestParams

@server.tool()
async def deploy_service(service: str, version: str) -> list[TextContent]:
    # Check if production — ask for confirmation
    if service in ("api", "frontend", "database"):
        response = await ctx.elicit(
            message=f"Deploy {service} version {version}?",
            options=[
                {"label": "Deploy to staging first", "value": "staging"},
                {"label": "Deploy directly to production", "value": "production"},
                {"label": "Cancel deployment", "value": "cancel"},
            ],
        )

        if response == "cancel":
            return [TextContent(type="text", text="Deployment cancelled.")]
        if response == "staging":
            environment = "staging"
        else:
            environment = "production"
    else:
        environment = "production"

    # Proceed with deployment
    result = do_deploy(service, version, environment)
    return [TextContent(type="text", text=json.dumps(result))]
```

#### Elicitation Patterns

**Confirmation Gate:**
```python
resp = await ctx.elicit(
    message=f"Are you sure you want to delete {count} records?",
    options=[
        {"label": "Yes, delete them", "value": "confirm"},
        {"label": "No, keep them", "value": "cancel"},
    ],
)
```

**Disambiguation:**
```python
resp = await ctx.elicit(
    message=f"Multiple services match '{query}'. Which one?",
    options=[
        {"label": f"{s['name']} ({s['env']})", "value": s['id']}
        for s in matches[:5]
    ],
)
```

**Parameter Collection:**
```python
resp = await ctx.elicit(
    message="Which notification channels should be enabled?",
    options=[
        {"label": "Email only", "value": "email"},
        {"label": "Slack only", "value": "slack"},
        {"label": "Both", "value": "both"},
        {"label": "Neither (silent mode)", "value": "none"},
    ],
)
```

---

### 7. Completions — Smart Autocomplete for Tool Args

Completions let Claude suggest values for tool arguments as the user types.

```python
@server.completion()
async def complete_service(current: str, context: dict) -> list[str]:
    """Suggest service names based on what's in the deployment registry."""
    all_services = ["api-server", "frontend", "worker", "database", "cache", "queue"]
    return [s for s in all_services if s.startswith(current)]

@server.completion()
async def complete_environment(current: str, context: dict) -> list[str]:
    """Suggest environments."""
    envs = ["staging", "production", "development", "testing"]
    return [e for e in envs if e.startswith(current)]
```

#### Context-Aware Completions

```python
@server.completion()
async def complete_flag_name(current: str, context: dict) -> list[str]:
    """Complete feature flag names. context contains other arg values."""
    # context might contain {"action": "toggle"} from the parent tool
    flags = list(_feature_flags.keys())
    return [f for f in flags if f.startswith(current)]
```

---

### 8. Progress Reporting & Long-Running Operations

For operations that take more than a few seconds, report progress so the user isn't left wondering.

```python
@server.tool()
async def batch_process(files: list[str]) -> list[TextContent]:
    """Process a batch of files with progress reporting."""
    total = len(files)
    results = []

    for i, file in enumerate(files):
        # Report progress: current step, total steps
        await ctx.report_progress(progress=i, total=total)

        result = process_one_file(file)
        results.append(result)

    # Mark complete
    await ctx.report_progress(progress=total, total=total)

    return [TextContent(type="text", text=json.dumps(results))]
```

#### Progress with Percentage

```python
@server.tool()
async def long_running_task(steps: int = 10) -> list[TextContent]:
    """Demonstrate progress for a multi-step operation."""
    for i in range(steps):
        await asyncio.sleep(0.5)  # Simulate work
        await ctx.report_progress(
            progress=i + 1,
            total=steps,
            message=f"Step {i + 1}/{steps}: Processing chunk..."
        )

    return [TextContent(type="text", text=f"Completed {steps} steps")]
```

#### Handling Cancellation

```python
@server.tool()
async def cancellable_task(duration: int = 30) -> list[TextContent]:
    """A task that can be cancelled mid-execution."""
    for i in range(duration):
        if ctx.cancelled:
            return [TextContent(type="text", text=f"Cancelled after {i} seconds")]

        await asyncio.sleep(1)
        await ctx.report_progress(progress=i, total=duration)

    return [TextContent(type="text", text=f"Completed {duration} seconds")]
```

---

### 9. Error Handling & Structured Error Responses

#### The Error Hierarchy

```python
from mcp.types import ErrorCode

# Standard MCP error codes
# -32600: Invalid Request
# -32601: Method Not Found
# -32602: Invalid Params
# -32603: Internal Error
# -32000: Server Error (custom, with data field)
```

#### Pattern: Structured Error Responses

Don't just raise exceptions — return error information as structured content so Claude can understand and possibly self-correct.

```python
@server.tool()
async def safe_api_call(endpoint: str, params: dict = {}) -> list[TextContent]:
    """Make an API call with structured error reporting."""
    try:
        result = await api_client.call(endpoint, params)
        return [TextContent(type="text", text=json.dumps({
            "ok": True,
            "data": result,
        }, indent=2))]

    except APIAuthError as e:
        return [TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": "authentication_failed",
            "message": "API key expired or invalid. Run: /mcp configure-auth",
            "detail": str(e),
        }, indent=2))]

    except APIRateLimitError as e:
        retry_after = e.headers.get("Retry-After", "unknown")
        return [TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": "rate_limited",
            "retry_after_seconds": retry_after,
            "message": f"Rate limited. Retry after {retry_after}s.",
        }, indent=2))]

    except APITimeoutError:
        return [TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": "timeout",
            "message": "API timed out. The service may be degraded.",
            "suggestion": "Try again with a smaller request or check status page.",
        }, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": "unknown",
            "message": str(e),
            "suggestion": "Report this to the MCP server maintainer.",
        }, indent=2))]
```

#### Validation Pattern

```python
@server.tool()
async def create_user(name: str, email: str, age: int) -> list[TextContent]:
    """Create a user with input validation."""
    errors = []

    if not name or len(name) < 2:
        errors.append({"field": "name", "error": "must be at least 2 characters"})
    if "@" not in email or "." not in email.split("@")[-1]:
        errors.append({"field": "email", "error": "invalid email format"})
    if age < 0 or age > 150:
        errors.append({"field": "age", "error": "must be between 0 and 150"})

    if errors:
        return [TextContent(type="text", text=json.dumps({
            "ok": False,
            "error": "validation_failed",
            "fields": errors,
        }, indent=2))]

    user = db.insert_user(name, email, age)
    return [TextContent(type="text", text=json.dumps({"ok": True, "user": user}, indent=2))]
```

#### Error Recovery Hints

When returning errors, always include a `suggestion` or `next_step` field. Claude reads these and can offer the user a path forward:

```python
ERROR_RECOVERY = {
    "auth_failed": "Run the /mcp auth command to re-authenticate",
    "not_found": "Check the resource ID or name for typos",
    "rate_limited": "Wait {retry_after}s and try again",
    "validation": "Fix the listed field errors and retry",
    "timeout": "The operation is taking too long. Try with a smaller input.",
    "permission_denied": "You don't have access. Contact the admin.",
}
```

---

### 10. Testing MCP Servers

#### Unit Testing Tools

```python
import pytest
import asyncio
import json
from my_server import server

@pytest.mark.asyncio
async def test_hello_tool():
    """Test a tool directly — no transport needed."""
    # Tools are async functions; call them directly
    result = await server._tools["hello"](name="World", language="en")

    assert len(result) == 1
    assert result[0].type == "text"
    assert "Hello, World" in result[0].text

@pytest.mark.asyncio
async def test_add_tool():
    result = await server._tools["add"](a=3, b=4)
    assert result[0].text == "7"
```

#### Integration Testing with stdio Transport

```python
import subprocess
import json
import time

def test_via_stdio():
    """Test by talking to the server as a subprocess."""
    proc = subprocess.Popen(
        ["python", "server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Send initialize request
    init_req = json.dumps({
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test", "version": "1.0"},
        },
    })
    proc.stdin.write(init_req + "\n")
    proc.stdin.flush()

    response = json.loads(proc.stdout.readline())
    assert "id" in response
    assert "result" in response

    # Send initialized notification
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0", "method": "notifications/initialized",
    }) + "\n")
    proc.stdin.flush()

    # Call a tool
    call_req = json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "add", "arguments": {"a": 3, "b": 4}},
    })
    proc.stdin.write(call_req + "\n")
    proc.stdin.flush()

    result = json.loads(proc.stdout.readline())
    assert result["result"]["content"][0]["text"] == "7"

    proc.terminate()
```

#### Integration Testing with HTTP Transport

```python
import httpx
import pytest

@pytest.mark.asyncio
async def test_http_server():
    """Test an HTTP MCP server."""
    async with httpx.AsyncClient(base_url="http://localhost:9020") as client:
        # Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # SSE connection (simplified — real tests use MCP client SDK)
        # For full integration, use the MCP Python client library
```

#### Testing with the MCP Client SDK

```python
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

@pytest.mark.asyncio
async def test_with_mcp_client():
    """Use the official MCP client to test end-to-end."""
    params = StdioServerParameters(
        command="python",
        args=["server.py"],
    )

    async with Client(params) as client:
        # Get tools
        tools = await client.list_tools()
        assert any(t.name == "hello" for t in tools)

        # Call a tool
        result = await client.call_tool("hello", {"name": "Test"})
        assert "Hello, Test" in result.content[0].text

        # Get resources
        resources = await client.list_resources()
        assert any(r.uri == "hello://stats" for r in resources)
```

#### Fixtures for Testable Servers

```python
import pytest
from mcp.server import Server

@pytest.fixture
def server_with_fake_db():
    """Create a server with a fake database for testing."""
    server = Server("test-server")
    fake_data = {"users": {}}

    @server.tool()
    async def get_user(user_id: str) -> list[TextContent]:
        user = fake_data["users"].get(user_id)
        if not user:
            return [TextContent(type="text", text=json.dumps({"error": "not_found"}))]
        return [TextContent(type="text", text=json.dumps(user))]

    @server.tool()
    async def create_user(name: str) -> list[TextContent]:
        import uuid
        uid = str(uuid.uuid4())
        fake_data["users"][uid] = {"id": uid, "name": name}
        return [TextContent(type="text", text=json.dumps({"id": uid}))]

    return server, fake_data

@pytest.mark.asyncio
async def test_create_and_get(server_with_fake_db):
    server, data = server_with_fake_db

    # Create
    result = await server._tools["create_user"](name="Alice")
    user_id = json.loads(result[0].text)["id"]

    # Get
    result = await server._tools["get_user"](user_id=user_id)
    assert "Alice" in result[0].text
```

---

### 11. Packaging for Distribution

#### PyPI Package Structure

```
my-mcp-server/
├── pyproject.toml
├── README.md
├── LICENSE
├── src/
│   └── my_mcp_server/
│       ├── __init__.py
│       ├── server.py          # MCP server definition
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── search.py
│       │   └── export.py
│       └── resources/
│           └── dashboard.py
└── tests/
    ├── test_tools.py
    └── test_resources.py
```

#### pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "my-mcp-server"
version = "0.1.0"
description = "MCP server for searching and exporting data"
requires-python = ">=3.10"
dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
]

[project.scripts]
my-mcp-server = "my_mcp_server.server:main"

[project.entry-points.claude_mcp]
my-server = "my_mcp_server.server:entry"
```

#### Docker Deployment

```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir .

# For HTTP servers:
EXPOSE 9020
CMD ["python", "-m", "my_mcp_server.server"]

# For stdio servers (used as sidecar):
# ENTRYPOINT ["python", "-m", "my_mcp_server.server"]
```

#### Claude Code Config After PyPI Install

```json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "my-mcp-server"
    }
  }
}
```

No `python` prefix, no path — just the entry point name.

---

### 12. Multi-Client State in HTTP Servers

When multiple Claude Code instances connect to the same HTTP MCP server, state management becomes critical.

**Reference:** `mcp_servers/http_team_server.py` — full implementation.

#### Shared State with Thread Safety

```python
import asyncio
from datetime import datetime

# Use asyncio.Lock for async-safe mutations
_state_lock = asyncio.Lock()
_shared_state: dict = {
    "notifications": [],
    "clients_connected": 0,
    "last_activity": None,
}

async def safe_append(key: str, item: dict):
    async with _state_lock:
        _shared_state[key].append(item)
        _shared_state["last_activity"] = datetime.now().isoformat()
        # Prune old entries
        if len(_shared_state[key]) > 200:
            _shared_state[key] = _shared_state[key][-200:]
```

#### Client-Specific vs Global State

```python
# Global — all clients see the same thing
_global_flags = {"maintenance_mode": False}

# Per-session — each client gets their own
_sessions: dict[str, dict] = {}  # session_id → state

@server.tool()
async def set_preference(key: str, value: str) -> list[TextContent]:
    """Set a personal preference (per-client)."""
    session_id = ctx.session_id
    if session_id not in _sessions:
        _sessions[session_id] = {}
    _sessions[session_id][key] = value
    return [TextContent(type="text", text=json.dumps({"ok": True}))]

@server.tool()
async def get_preferences() -> list[TextContent]:
    """Get your personal preferences."""
    prefs = _sessions.get(ctx.session_id, {})
    return [TextContent(type="text", text=json.dumps(prefs))]
```

#### Broadcasting to All Connected Clients

```python
# Track active SSE transports
_active_connections: dict[str, SseServerTransport] = {}

async def broadcast_event(event_type: str, data: dict):
    """Send an event to every connected client."""
    for session_id, transport in list(_active_connections.items()):
        try:
            await transport.send_event(event_type, data)
        except Exception:
            # Client disconnected — remove
            _active_connections.pop(session_id, None)

@server.tool()
async def team_announce(message: str) -> list[TextContent]:
    """Post an announcement that all clients see."""
    await broadcast_event("team_announcement", {"message": message})
    return [TextContent(type="text", text="Announcement sent to all clients")]
```

---

## Part II: API Integration Patterns

### 13. Wrapping REST APIs as MCP Tools

**Reference:** `mcp_servers/weather_server.py` — external API with caching.

#### The Basic Wrapper

```python
import httpx
from datetime import datetime, timedelta

# Cache for API responses
_cache: dict[str, tuple[dict, datetime]] = {}
CACHE_TTL = timedelta(minutes=5)

async def _cached_api_call(url: str, params: dict = {}) -> dict:
    """Make a cached API call with TTL."""
    cache_key = f"{url}:{json.dumps(params, sort_keys=True)}"

    # Check cache
    if cache_key in _cache:
        data, timestamp = _cache[cache_key]
        if datetime.now() - timestamp < CACHE_TTL:
            return data

    # Fetch
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    # Store
    _cache[cache_key] = (data, datetime.now())
    return data

@server.tool()
async def get_weather(city: str, units: str = "metric") -> list[TextContent]:
    """Get current weather for a city.

    Args:
        city: City name (e.g. "London", "Tokyo", "San Francisco")
        units: "metric" for Celsius, "imperial" for Fahrenheit
    """
    api_key = os.environ["WEATHER_API_KEY"]
    data = await _cached_api_call(
        f"https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "units": units, "appid": api_key},
    )

    return [TextContent(type="text", text=json.dumps({
        "city": data["name"],
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity": data["main"]["humidity"],
        "conditions": data["weather"][0]["description"],
        "wind_speed": data["wind"]["speed"],
    }, indent=2))]
```

#### Parallel API Calls

```python
@server.tool()
async def compare_weather(cities: list[str]) -> list[TextContent]:
    """Get weather for multiple cities simultaneously."""
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"https://api.weather.com/v1/{city}")
            for city in cities
        ]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

    results = {}
    for city, resp in zip(cities, responses):
        if isinstance(resp, Exception):
            results[city] = {"error": str(resp)}
        else:
            results[city] = resp.json()

    return [TextContent(type="text", text=json.dumps(results, indent=2))]
```

#### API Wrapper Anti-Patterns

| Anti-Pattern | Why It's Bad | Fix |
|--------------|--------------|-----|
| One tool per endpoint | Too many tools, hard to discover | Group related endpoints into fewer tools with an `action` parameter |
| Hardcoded API keys | Can't change for different users | Use `os.environ` or MCP auth |
| No caching | Rate limits hit quickly | TTL cache for GET requests |
| No timeout | Hung tool blocks Claude | Always set `httpx.Timeout` |
| Raw error passthrough | Claude can't self-correct | Catch and structure errors |

---

### 14. Streaming APIs to MCP

For APIs that return streaming responses (Server-Sent Events, chunked transfer), buffer chunks and return the full result.

```python
@server.tool()
async def stream_completion(prompt: str) -> list[TextContent]:
    """Call a streaming LLM API and return the full response."""
    async with httpx.AsyncClient() as client:
        full_text = []
        async with client.stream(
            "POST",
            "https://api.llm.example.com/v1/completions",
            json={"prompt": prompt, "stream": True},
            headers={"Authorization": f"Bearer {os.environ['LLM_API_KEY']}"},
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    chunk = json.loads(line[6:])
                    full_text.append(chunk.get("text", ""))
                if line == "data: [DONE]":
                    break

    return [TextContent(type="text", text="".join(full_text))]
```

#### With Progress Reporting

```python
@server.tool()
async def stream_with_progress(prompt: str) -> list[TextContent]:
    """Stream with real-time progress updates."""
    full_text = []
    chunk_count = 0

    async with httpx.AsyncClient() as client:
        async with client.stream("POST", "...", json={"prompt": prompt}) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    chunk = json.loads(line[6:])
                    full_text.append(chunk.get("text", ""))
                    chunk_count += 1
                    await ctx.report_progress(progress=chunk_count, total=0)  # 0 = indeterminate

    return [TextContent(type="text", text="".join(full_text))]
```

---

### 15. Rate Limiting, Retries & Resilience

#### Exponential Backoff with Retry

```python
import random

async def _api_call_with_retry(
    url: str,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> dict:
    """Make an API call with exponential backoff and jitter."""
    last_error = None

    for attempt in range(max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                return resp.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429:  # Rate limited
                retry_after = int(e.response.headers.get("Retry-After", base_delay * (2 ** attempt)))
                await asyncio.sleep(retry_after + random.uniform(0, 1))
            elif e.response.status_code >= 500:  # Server error, retryable
                delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
            else:
                raise  # Client error (4xx), don't retry

        except httpx.TimeoutException:
            delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)

        last_error = e

    raise last_error
```

#### Rate Limiter Class

```python
import time
from collections import deque

class RateLimiter:
    """Token bucket rate limiter."""

    def __init__(self, max_calls: int, period_seconds: float):
        self.max_calls = max_calls
        self.period = period_seconds
        self.calls: deque[float] = deque()

    async def acquire(self):
        """Wait until a call can be made."""
        now = time.time()

        # Remove expired entries
        while self.calls and self.calls[0] < now - self.period:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            # Calculate wait time
            wait = self.calls[0] + self.period - now
            if wait > 0:
                await asyncio.sleep(wait)

        self.calls.append(time.time())

_rate_limiter = RateLimiter(max_calls=10, period_seconds=1.0)

@server.tool()
async def rate_limited_api_call(query: str) -> list[TextContent]:
    """An API call protected by rate limiting."""
    await _rate_limiter.acquire()
    data = await _api_call_with_retry(f"https://api.example.com/search?q={query}")
    return [TextContent(type="text", text=json.dumps(data))]
```

#### Circuit Breaker

```python
class CircuitBreaker:
    """Fail-fast when a downstream service is unhealthy."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.threshold = failure_threshold
        self.recovery = recovery_timeout
        self.failures = 0
        self.last_failure = 0.0
        self.state = "closed"  # closed, open, half_open

    async def call(self, fn, *args, **kwargs):
        now = time.time()

        if self.state == "open":
            if now - self.last_failure > self.recovery:
                self.state = "half_open"
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await fn(*args, **kwargs)
            if self.state == "half_open":
                self.state = "closed"
                self.failures = 0
            return result
        except Exception:
            self.failures += 1
            self.last_failure = time.time()
            if self.failures >= self.threshold:
                self.state = "open"
            raise
```

---

### 16. Authentication Passthrough

#### Environment Variable Injection

```python
# Simplest: read from environment
@server.tool()
async def api_call(query: str) -> list[TextContent]:
    api_key = os.environ.get("MY_API_KEY")
    if not api_key:
        return [TextContent(type="text", text=json.dumps({
            "error": "auth_missing",
            "message": "Set MY_API_KEY environment variable",
        }))]
    ...
```

#### OAuth Passthrough Pattern

See `mcp.md` Section 8 for OAuth setup. In a tool:

```python
@server.tool()
async def protected_api_call(query: str) -> list[TextContent]:
    """Make an API call using the user's OAuth token."""
    # The MCP client passes auth headers automatically when OAuth is configured
    # Access them if your server acts as a proxy:
    headers = {}
    if hasattr(ctx, "auth_headers"):
        headers["Authorization"] = ctx.auth_headers.get("Authorization", "")

    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(f"https://api.example.com/search", params={"q": query})
        return [TextContent(type="text", text=resp.text)]
```

#### Multiple Auth Methods

```python
@server.tool()
async def multi_auth_api(service: str, query: str) -> list[TextContent]:
    """Call different services with different auth strategies."""
    auth_config = {
        "github": {"header": "Authorization", "value": f"Bearer {os.environ['GITHUB_TOKEN']}"},
        "slack": {"header": "Authorization", "value": f"Bearer {os.environ['SLACK_TOKEN']}"},
        "datadog": {"header": "DD-API-KEY", "value": os.environ['DD_API_KEY']},
        "internal": {"header": "X-API-Key", "value": os.environ['INTERNAL_KEY']},
    }

    if service not in auth_config:
        return [TextContent(type="text", text=json.dumps({
            "error": "unknown_service",
            "valid_services": list(auth_config.keys()),
        }))]

    cfg = auth_config[service]
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"https://{service}.example.com/api/search",
            params={"q": query},
            headers={cfg["header"]: cfg["value"]},
        )
        return [TextContent(type="text", text=resp.text)]
```

---

### 17. Webhook Ingestion via MCP Resources

HTTP servers can receive webhooks and expose them as resources.

```python
from starlette.requests import Request
from starlette.responses import JSONResponse

_webhook_events: list[dict] = []
MAX_EVENTS = 500

# Webhook receiver (exposed as a POST endpoint, not MCP)
async def webhook_receiver(request: Request):
    """Receive webhook events from external services."""
    body = await request.json()
    event = {
        "id": str(uuid.uuid4()),
        "source": request.headers.get("X-Webhook-Source", "unknown"),
        "event_type": request.headers.get("X-Event-Type", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "payload": body,
    }

    _webhook_events.append(event)
    if len(_webhook_events) > MAX_EVENTS:
        _webhook_events.pop(0)

    return JSONResponse({"received": True, "id": event["id"]})

# Resource: read recent webhooks
@server.resource("webhooks://recent")
async def recent_webhooks() -> str:
    return json.dumps(_webhook_events[-50:], indent=2)

# Tool: filter webhooks
@server.tool()
async def search_webhooks(source: str = "", event_type: str = "") -> list[TextContent]:
    """Search recent webhook events."""
    results = _webhook_events
    if source:
        results = [e for e in results if e["source"] == source]
    if event_type:
        results = [e for e in results if e["event_type"] == event_type]
    return [TextContent(type="text", text=json.dumps(results[-50:], indent=2))]
```

---

### 18. GraphQL as MCP Tools

```python
@server.tool()
async def graphql_query(
    query: str,
    variables: dict = {},
    operation_name: str = "",
) -> list[TextContent]:
    """Execute a GraphQL query against the configured endpoint.

    Args:
        query: GraphQL query string
        variables: Query variables as a JSON object
        operation_name: Optional operation name for multi-operation documents
    """
    endpoint = os.environ.get("GRAPHQL_ENDPOINT", "https://api.example.com/graphql")
    api_key = os.environ.get("GRAPHQL_API_KEY", "")

    payload = {"query": query, "variables": variables}
    if operation_name:
        payload["operationName"] = operation_name

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            endpoint,
            json=payload,
            headers={"Authorization": f"Bearer {api_key}"} if api_key else {},
        )
        data = resp.json()

    if "errors" in data:
        return [TextContent(type="text", text=json.dumps({
            "ok": False,
            "errors": data["errors"],
        }, indent=2))]

    return [TextContent(type="text", text=json.dumps({
        "ok": True,
        "data": data["data"],
    }, indent=2))]
```

#### Higher-Level GraphQL Tools

```python
@server.tool()
async def list_users_graphql(
    status: str = "active",
    limit: int = 10,
    cursor: str = "",
) -> list[TextContent]:
    """List users (wraps a specific GraphQL query).

    Args:
        status: "active", "inactive", or "all"
        limit: Page size (max 50)
        cursor: Pagination cursor from previous response
    """
    query = """
    query ListUsers($status: String, $limit: Int, $cursor: String) {
        users(status: $status, first: $limit, after: $cursor) {
            edges {
                node {
                    id
                    name
                    email
                    createdAt
                }
                cursor
            }
            pageInfo {
                hasNextPage
                endCursor
            }
        }
    }
    """
    variables = {"status": status, "limit": min(limit, 50)}
    if cursor:
        variables["cursor"] = cursor

    result = await graphql_query(query, variables)
    return result
```

---

### 19. Database-Backed MCP Servers

#### SQLite Pattern

```python
import sqlite3
import os

DB_PATH = os.environ.get("MCP_DB_PATH", "mcp_data.db")

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def _init_db():
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                data TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)

_init_db()

@server.tool()
async def db_create(name: str, data: str = "{}") -> list[TextContent]:
    """Create a new item in the database.

    Args:
        name: Item name (unique)
        data: JSON data to store
    """
    import uuid
    item_id = str(uuid.uuid4())

    with _get_db() as conn:
        try:
            conn.execute(
                "INSERT INTO items (id, name, data) VALUES (?, ?, ?)",
                (item_id, name, data),
            )
        except sqlite3.IntegrityError:
            return [TextContent(type="text", text=json.dumps({
                "error": "duplicate_name", "message": f"Item '{name}' already exists",
            }))]

    return [TextContent(type="text", text=json.dumps({"id": item_id, "name": name}))]

@server.tool()
async def db_search(query: str, limit: int = 20) -> list[TextContent]:
    """Search items by name (LIKE match).

    Args:
        query: Search term (partial name match)
        limit: Max results (1-100)
    """
    with _get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE name LIKE ? LIMIT ?",
            (f"%{query}%", min(limit, 100)),
        ).fetchall()

    return [TextContent(type="text", text=json.dumps(
        [dict(r) for r in rows], indent=2
    ))]

@server.resource("db://items")
async def all_items() -> str:
    """All items as a resource."""
    with _get_db() as conn:
        rows = conn.execute("SELECT * FROM items ORDER BY created_at DESC LIMIT 100").fetchall()
    return json.dumps([dict(r) for r in rows], indent=2)
```

#### PostgreSQL with Connection Pooling

```python
import asyncpg

_pool: asyncpg.Pool | None = None

async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            dsn=os.environ.get("DATABASE_URL", "postgresql://localhost/mcp"),
            min_size=2,
            max_size=10,
        )
    return _pool

@server.tool()
async def pg_query(query: str) -> list[TextContent]:
    """Execute a read-only SQL query (SELECT only).

    Args:
        query: SQL SELECT statement
    """
    query = query.strip()
    if not query.upper().startswith("SELECT"):
        return [TextContent(type="text", text=json.dumps({
            "error": "Only SELECT queries are allowed via this tool",
        }))]

    pool = await _get_pool()
    async with pool.acquire() as conn:
        try:
            rows = await conn.fetch(query)
        except Exception as e:
            return [TextContent(type="text", text=json.dumps({
                "error": str(e),
            }))]

    return [TextContent(type="text", text=json.dumps(
        [dict(r) for r in rows], indent=2, default=str
    ))]
```

---

### 20. File System Tools — Safe Path Sandboxing

**Reference:** `mcp_servers/devops_server.py` — `_is_path_allowed()` + `_is_command_safe()`.

#### Path Allowlisting

```python
from pathlib import Path

# Allowlisted directories — tools can only read/write within these
ALLOWED_PATHS = [
    Path.home() / "projects",
    Path.home() / "downloads",
    Path("/tmp/mcp_workspace"),
]

def is_path_allowed(target: str | Path) -> bool:
    """Check if a path is within an allowed directory."""
    target = Path(target).resolve()

    for allowed in ALLOWED_PATHS:
        allowed = allowed.resolve()
        try:
            target.relative_to(allowed)
            return True
        except ValueError:
            continue

    return False

@server.tool()
async def read_file(file_path: str, max_lines: int = 1000) -> list[TextContent]:
    """Read a file, with path safety checks.

    Args:
        file_path: Path to the file (must be within allowed directories)
        max_lines: Maximum lines to read (1-5000)
    """
    path = Path(file_path).resolve()

    # Safety checks
    if not path.exists():
        return [TextContent(type="text", text=json.dumps({"error": "File not found"}))]
    if not is_path_allowed(path):
        return [TextContent(type="text", text=json.dumps({
            "error": "path_not_allowed",
            "message": f"Access denied: {file_path}",
            "allowed_paths": [str(p) for p in ALLOWED_PATHS],
        }))]
    if path.is_symlink():
        return [TextContent(type="text", text=json.dumps({"error": "Symlinks not allowed"}))]

    content = path.read_text(encoding="utf-8", errors="replace")
    lines = content.splitlines()[:max_lines]

    return [TextContent(type="text", text="\n".join(lines))]

@server.tool()
async def write_file(file_path: str, content: str) -> list[TextContent]:
    """Write to a file, with path safety checks.

    Args:
        file_path: Path to write (must be within allowed directories)
        content: Text content to write
    """
    path = Path(file_path).resolve()

    if not is_path_allowed(path):
        return [TextContent(type="text", text=json.dumps({
            "error": "path_not_allowed",
        }))]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    return [TextContent(type="text", text=json.dumps({
        "written": str(path),
        "size_bytes": path.stat().st_size,
    }))]
```

#### Safe Shell Execution

```python
BLOCKED_COMMANDS = {"rm", "sudo", "chmod", "chown", "dd", "mkfs", "shutdown", "reboot",
                    "kill", "pkill", "wget", "curl", "nc", "telnet", "ssh"}

ALLOWED_COMMANDS = {"ls", "cat", "head", "tail", "wc", "grep", "find", "du", "df",
                    "echo", "date", "whoami", "pwd", "env", "which", "git", "docker", "ps"}

@server.tool()
async def safe_shell(command: str) -> list[TextContent]:
    """Run a safe shell command. Only allowlisted commands are permitted.

    Args:
        command: Shell command to run (e.g. "ls -la", "df -h", "git status")
    """
    cmd_parts = command.strip().split()
    base_cmd = cmd_parts[0]

    if base_cmd in BLOCKED_COMMANDS:
        return [TextContent(type="text", text=json.dumps({
            "error": "blocked_command",
            "command": base_cmd,
        }))]

    if base_cmd not in ALLOWED_COMMANDS:
        return [TextContent(type="text", text=json.dumps({
            "error": "command_not_allowed",
            "allowed_commands": sorted(ALLOWED_COMMANDS),
        }))]

    try:
        result = subprocess.run(
            cmd_parts,
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,  # No shell injection!
        )
        return [TextContent(type="text", text=json.dumps({
            "stdout": result.stdout[-10000:],  # Truncate
            "stderr": result.stderr[-5000:],
            "returncode": result.returncode,
        }))]
    except subprocess.TimeoutExpired:
        return [TextContent(type="text", text=json.dumps({"error": "Command timed out"}))]
```

---

## Part III: AI Workflows & Agents

### 21. Chaining MCP Tools — Multi-Step Agent Workflows

Claude can chain multiple tool calls. Your tools should be designed to compose well.

#### Pattern: Data Flow Between Tools

```
Tool A (extract) → returns structured JSON
    ↓
Tool B (transform) → takes JSON, returns transformed JSON
    ↓
Tool C (load) → takes JSON, writes to destination
```

```python
# Each tool produces clean JSON that the next tool can consume
@server.tool()
async def extract(source: str) -> list[TextContent]:
    """Extract data from source. Returns JSON with schema."""
    data = {"rows": [...], "schema": {...}, "count": N}
    return [TextContent(type="text", text=json.dumps(data))]

@server.tool()
async def transform(data_json: str, operation: str) -> list[TextContent]:
    """Transform JSON data. Takes the output of extract or another transform.

    Args:
        data_json: JSON data to transform (from extract tool output)
        operation: "filter", "aggregate", "join", "pivot"
    """
    data = json.loads(data_json)
    ...
```

#### Pattern: Workflow Orchestrator Tool

```python
@server.tool()
async def run_etl_pipeline(
    source: str,
    destination: str,
    transformations: list[str],
) -> list[TextContent]:
    """Run a complete ETL pipeline end-to-end.

    Args:
        source: Data source path or URL
        destination: Where to write results
        transformations: List of operations: "clean", "dedupe", "enrich", "validate"
    """
    log = []
    current = source

    for step in transformations:
        # Each step calls another tool internally
        if step == "clean":
            result = await clean_data(current)
        elif step == "dedupe":
            result = await deduplicate(current)
        elif step == "enrich":
            result = await enrich(current)
        elif step == "validate":
            result = await validate_data(current)
        else:
            return [TextContent(type="text", text=json.dumps({
                "error": f"Unknown step: {step}"
            }))]

        log.append({"step": step, "result": json.loads(result[0].text)})
        current = step  # Pass to next

    return [TextContent(type="text", text=json.dumps({
        "pipeline_complete": True,
        "steps": log,
        "output": destination,
    }, indent=2))]
```

#### Pattern: Tool That Returns Next Steps

```python
@server.tool()
async def analyze_and_suggest(file_path: str) -> list[TextContent]:
    """Analyze a file and suggest which tools to use next."""
    path = Path(file_path)

    suggestions = []
    if path.suffix == ".csv":
        suggestions.append({"tool": "parse_csv", "reason": "CSV detected — parse and explore schema"})
        suggestions.append({"tool": "generate_chart", "reason": "Create visualizations from CSV data"})
    elif path.suffix == ".log":
        suggestions.append({"tool": "search_logs", "reason": "Search for errors in log file"})
        suggestions.append({"tool": "analyze_logs_with_sampling", "reason": "Use AI to classify log entries"})
    elif path.suffix in (".py", ".js", ".ts"):
        suggestions.append({"tool": "analyze_code", "reason": "AST analysis and complexity metrics"})
        suggestions.append({"tool": "generate_tests", "reason": "Create test file"})

    return [TextContent(type="text", text=json.dumps({
        "file": str(path),
        "suggested_next_steps": suggestions,
    }, indent=2))]
```

---

### 22. Using Sampling for Self-Critique & Iterative Refinement

**Reference:** `mcp_servers/sampling_demo_server.py` — `generate_with_review` pattern.

#### The Generate-Review-Revise Loop

```python
@server.tool()
async def polished_writing(
    topic: str,
    style: str = "blog",
    review_rounds: int = 2,
) -> list[TextContent]:
    """Generate polished content with iterative AI review and revision.

    Args:
        topic: What to write about
        style: "blog", "documentation", "tweet", "email"
        review_rounds: How many review-revise cycles (1-5)
    """
    review_rounds = min(review_rounds, 5)

    # Generate initial draft
    gen = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Write a {style} about: {topic}"
            ))],
            maxTokens=1500,
            systemPrompt=f"You are a {style} writer. Be engaging and clear.",
        )
    )
    draft = gen.content[0].text

    for round_num in range(review_rounds):
        # Get critique
        review = await server.request_sampling(
            CreateMessageRequestParams(
                messages=[ContentBlock(type="text", text=(
                    f"Review this {style}. Identify 3 specific weaknesses and suggest fixes:\n\n{draft}"
                ))],
                maxTokens=500,
                systemPrompt="You are a critical editor. Be specific. Point to exact sentences.",
            )
        )
        feedback = review.content[0].text

        # Revise
        revise = await server.request_sampling(
            CreateMessageRequestParams(
                messages=[ContentBlock(type="text", text=(
                    f"Draft:\n{draft}\n\nFeedback:\n{feedback}\n\n"
                    f"Rewrite incorporating all feedback. Return the full revised text."
                ))],
                maxTokens=1500,
                systemPrompt=f"You are a {style} writer incorporating editor feedback.",
            )
        )
        draft = revise.content[0].text

    return [TextContent(type="text", text=json.dumps({
        "final": draft,
        "rounds": review_rounds,
    }, indent=2))]
```

#### Self-Critique Pattern

```python
@server.tool()
async def code_with_review(code: str, language: str = "python") -> list[TextContent]:
    """Review code and suggest improvements via sampling."""
    # Analyze
    analysis = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Review this {language} code for bugs, style issues, and improvements:\n\n```{language}\n{code}\n```"
            ))],
            maxTokens=800,
            systemPrompt="You are a senior code reviewer. Find bugs, security issues, and style problems.",
        )
    )

    # Suggest fixes
    fixes = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Code:\n```{language}\n{code}\n```\n\n"
                f"Review:\n{analysis.content[0].text}\n\n"
                f"For each issue found, provide the exact fix. Output as JSON: "
                f'[{{"line": N, "issue": "...", "fix": "..."}}]'
            ))],
            maxTokens=800,
        )
    )

    return [TextContent(type="text", text=json.dumps({
        "review": analysis.content[0].text,
        "fixes": fixes.content[0].text,
    }, indent=2))]
```

---

### 23. Multi-Agent Patterns with Shared MCP Servers

When multiple Claude instances connect via HTTP, you get multi-agent behavior "for free."

#### Pattern: Coordinator-Worker via Shared State

```python
# Shared job queue in the HTTP server
_job_queue: asyncio.Queue = asyncio.Queue()
_job_results: dict[str, dict] = {}

@server.tool()
async def submit_job(job_type: str, payload: dict) -> list[TextContent]:
    """Submit a job to the shared queue. Any connected Claude can pick it up."""
    job_id = str(uuid.uuid4())
    await _job_queue.put({"id": job_id, "type": job_type, "payload": payload})

    return [TextContent(type="text", text=json.dumps({
        "job_id": job_id,
        "message": "Job submitted. A worker will pick it up.",
    }))]

@server.tool()
async def claim_job() -> list[TextContent]:
    """Claim the next available job from the queue."""
    try:
        job = _job_queue.get_nowait()
    except asyncio.QueueEmpty:
        return [TextContent(type="text", text=json.dumps({"status": "no_jobs_available"}))]

    return [TextContent(type="text", text=json.dumps({"job": job}))]

@server.tool()
async def complete_job(job_id: str, result: dict) -> list[TextContent]:
    """Submit results for a completed job."""
    _job_results[job_id] = result
    return [TextContent(type="text", text=json.dumps({"completed": job_id}))]
```

#### Pattern: Broadcast Coordination

```python
@server.tool()
async def coordinate_deploy(service: str, version: str) -> list[TextContent]:
    """Announce a deployment. Other Claude instances can react."""
    await broadcast_event("deploy_starting", {
        "service": service,
        "version": version,
        "initiator": ctx.session_id,
        "timestamp": datetime.now().isoformat(),
    })

    # Each Claude instance that sees this can run health checks, update dashboards, etc.
    return [TextContent(type="text", text="Deployment coordination broadcast sent")]
```

---

### 24. RAG with MCP — Embedding Search as a Tool/Resource

#### Vector Search Tool

```python
@server.tool()
async def search_docs(
    query: str,
    top_k: int = 5,
    collection: str = "default",
) -> list[TextContent]:
    """Search documentation using semantic (vector) search.

    Args:
        query: Natural language search query
        top_k: Number of results (1-20)
        collection: Document collection to search
    """
    # Generate embedding for the query
    embedding = await _get_embedding(query)

    # Search vector store
    results = vector_store.search(
        collection=collection,
        vector=embedding,
        top_k=min(top_k, 20),
    )

    # Format results with context
    return [TextContent(type="text", text=json.dumps({
        "query": query,
        "results": [
            {
                "score": r.score,
                "title": r.metadata.get("title", "Untitled"),
                "source": r.metadata.get("source", "unknown"),
                "text": r.text[:2000],  # Truncate for context window
            }
            for r in results
        ],
    }, indent=2))]
```

#### RAG Resource

```python
@server.resource("rag://index-stats")
async def rag_stats() -> str:
    """Statistics about the RAG index."""
    return json.dumps({
        "total_documents": vector_store.count(),
        "collections": vector_store.list_collections(),
        "embedding_model": os.environ.get("EMBEDDING_MODEL", "text-embedding-3-small"),
        "last_indexed": vector_store.last_indexed(),
    }, indent=2)
```

#### Full RAG Pipeline Tool

```python
@server.tool()
async def rag_qa(question: str, collection: str = "default") -> list[TextContent]:
    """Full RAG pipeline: search → retrieve → answer.

    Args:
        question: The question to answer
        collection: Knowledge base to search
    """
    # 1. Search
    embedding = await _get_embedding(question)
    results = vector_store.search(collection, embedding, top_k=5)

    # 2. Build context
    context = "\n\n---\n\n".join(r.text for r in results)

    # 3. Answer with sampling
    answer = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Answer the question using only the provided context.\n\n"
                f"CONTEXT:\n{context}\n\n"
                f"QUESTION: {question}\n\n"
                f"If the context doesn't contain the answer, say so."
            ))],
            maxTokens=500,
            systemPrompt="You are a helpful assistant. Answer from context only.",
        )
    )

    return [TextContent(type="text", text=json.dumps({
        "answer": answer.content[0].text,
        "sources": [r.metadata.get("source") for r in results],
    }, indent=2))]
```

---

### 25. Human-in-the-Loop Workflows with Elicitation

#### Decision Gate

```python
@server.tool()
async def risky_operation(action: str, target: str) -> list[TextContent]:
    """Perform a risky operation with human approval gating.

    Args:
        action: "delete", "restart", "scale", "migrate"
        target: What to act on (service name, resource ID)
    """
    RISKY_ACTIONS = ["delete", "restart", "scale", "migrate"]

    if action in RISKY_ACTIONS:
        confirmation = await ctx.elicit(
            message=f"Confirm {action} on {target}? This cannot be undone.",
            options=[
                {"label": f"Yes, {action} {target}", "value": "confirm"},
                {"label": "No, cancel this operation", "value": "cancel"},
                {"label": f"Dry-run first (see what would happen)", "value": "dry_run"},
            ],
        )

        if confirmation == "cancel":
            return [TextContent(type="text", text=f"{action} cancelled.")]
        if confirmation == "dry_run":
            preview = dry_run(action, target)
            # Ask again after preview
            proceed = await ctx.elicit(
                message=f"Dry-run result:\n{json.dumps(preview, indent=2)}\n\nProceed?",
                options=[
                    {"label": "Yes, proceed", "value": "confirm"},
                    {"label": "No, cancel", "value": "cancel"},
                ],
            )
            if proceed == "cancel":
                return [TextContent(type="text", text="Operation cancelled.")]

    result = execute_operation(action, target)
    return [TextContent(type="text", text=json.dumps(result))]
```

#### Interactive Data Exploration

```python
@server.tool()
async def explore_data(source: str) -> list[TextContent]:
    """Explore a dataset interactively, asking the user what to look at next."""
    data = load_data(source)
    summary = get_summary(data)

    # Show summary and ask what to explore
    focus = await ctx.elicit(
        message=f"Data loaded: {summary['rows']} rows, {summary['cols']} columns.\n"
                f"Columns: {', '.join(summary['columns'])}\n\nWhat should we explore?",
        options=[
            {"label": "Show distributions", "value": "distributions"},
            {"label": "Find correlations", "value": "correlations"},
            {"label": "Detect outliers", "value": "outliers"},
            {"label": "Generate visualizations", "value": "charts"},
            {"label": "Export cleaned data", "value": "export"},
        ],
    )

    if focus == "distributions":
        column = await ctx.elicit(
            message="Which column?",
            options=[{"label": c, "value": c} for c in summary["columns"][:10]],
        )
        result = compute_distribution(data, column)
    elif focus == "correlations":
        result = compute_correlations(data)
    # ... etc

    return [TextContent(type="text", text=json.dumps(result, indent=2))]
```

---

### 26. Prompt Engineering MCP Tool Descriptions

The tool description (docstring) is the most important text you write. It's a prompt for Claude.

#### Before & After

**Before (bad):**
```python
@server.tool()
async def search(q: str, t: str = "all", l: int = 10) -> list[TextContent]:
    """Search stuff."""
    ...
```

**After (good):**
```python
@server.tool()
async def search_knowledge_base(query: str, type_filter: str = "all", limit: int = 10) -> list[TextContent]:
    """Search the internal knowledge base for articles, docs, and runbooks.

    Use this when the user asks about internal processes, needs documentation,
    or wants to find how-to guides. NOT for code search — use search_code instead.

    Args:
        query: Search terms. Supports exact phrases in "double quotes" and
               -excluded_terms with a minus prefix.
        type_filter: What kind of content to search.
                     "all" — everything
                     "article" — long-form knowledge articles
                     "runbook" — operational runbooks and incident guides
                     "policy" — company policies and standards
        limit: How many results to return. 5 is fast; 20 is thorough. Max 50.
    """
```

#### The Formula

```
[One-line summary of what it does]

Use this when [specific scenarios]. [If applicable: NOT for X — use Y instead.]

Args:
    [arg_name]: [What it is. Examples of valid values. Constraints.]
```

#### Testing Tool Descriptions

Ask Claude to use your tools in different scenarios and see if it:
1. Selects the right tool for the job
2. Fills arguments correctly
3. Handles edge cases appropriately

If Claude consistently picks the wrong tool or passes bad arguments, your docstring needs improvement.

---

### 27. Structured Output Extraction via Sampling

#### JSON Schema Extraction

```python
@server.tool()
async def extract_entities(text: str) -> list[TextContent]:
    """Extract named entities as structured JSON."""
    resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Extract named entities from this text. Return valid JSON only.\n\n"
                f"Schema:\n"
                f'{{"people": [{{"name": "...", "role": "..."}}],\n'
                f' "organizations": [{{"name": "...", "type": "..."}}],\n'
                f' "dates": [{{"description": "...", "iso_date": "YYYY-MM-DD"}}],\n'
                f' "locations": [{{"name": "...", "type": "city/country/address"}}]}}\n\n'
                f"Text:\n{text}"
            ))],
            maxTokens=1000,
            systemPrompt="Extract entities as JSON. Return only the JSON object, no explanation.",
        )
    )

    # Validate the extracted JSON
    try:
        entities = json.loads(resp.content[0].text)
        return [TextContent(type="text", text=json.dumps(entities, indent=2))]
    except json.JSONDecodeError:
        # Retry with stronger prompt
        retry = await server.request_sampling(
            CreateMessageRequestParams(
                messages=[ContentBlock(type="text", text=(
                    f"The previous response was not valid JSON. Try again.\n"
                    f"Return ONLY a JSON object matching the schema. No markdown, no explanation.\n\n"
                    f"Previous response: {resp.content[0].text[:500]}"
                ))],
                maxTokens=1000,
                systemPrompt="You are a JSON-only API. Return only valid JSON.",
            )
        )
        entities = json.loads(retry.content[0].text)
        return [TextContent(type="text", text=json.dumps(entities, indent=2))]
```

#### Pydantic Model Extraction

```python
from pydantic import BaseModel, Field
from typing import Optional

class BugReport(BaseModel):
    title: str = Field(description="Concise bug title")
    severity: str = Field(description="critical, major, minor, or cosmetic")
    steps_to_reproduce: list[str]
    expected_behavior: str
    actual_behavior: str
    environment: Optional[str] = None

@server.tool()
async def extract_bug_report(description: str) -> list[TextContent]:
    """Extract a structured bug report from a user's description."""
    schema_json = BugReport.schema_json(indent=2)

    resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Extract a bug report from this description as JSON matching this schema:\n\n"
                f"{schema_json}\n\n"
                f"Description:\n{description}"
            ))],
            maxTokens=800,
            systemPrompt="Extract bug reports as JSON. Return only the JSON object.",
        )
    )

    # Parse and validate with Pydantic
    data = json.loads(resp.content[0].text)
    bug = BugReport(**data)

    return [TextContent(type="text", text=bug.json(indent=2))]
```

---

### 28. Building a Code Review Agent

**Reference:** `mcp_servers/code_analyzer_server.py` — AST analysis tools.

#### Multi-Tool Code Review

```python
@server.prompt(
    name="code-review",
    description="Perform a comprehensive code review using all analysis tools",
    arguments={
        "file_path": {"type": "string", "description": "File to review", "required": True},
        "focus": {
            "type": "string",
            "enum": ["security", "performance", "style", "architecture", "all"],
            "description": "Review focus area",
            "required": False,
        },
    },
)
async def code_review_prompt(file_path: str, focus: str = "all") -> dict:
    focus_tasks = {
        "security": "- Check for SQL injection, XSS, hardcoded secrets, unsafe eval/exec\n- Validate input handling\n- Check auth/authz patterns",
        "performance": "- Identify N+1 queries, unnecessary allocations, blocking calls\n- Check caching opportunities\n- Review algorithmic complexity",
        "style": "- Check naming conventions, function length, docstrings\n- Verify type hints\n- Review error handling patterns",
        "architecture": "- Check coupling/cohesion\n- Review dependency direction\n- Identify God objects and leaky abstractions",
        "all": "- Complete review covering security, performance, style, and architecture",
    }

    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Review {file_path} with focus on {focus}.

Use these tools:
1. analyze_complexity — cyclomatic complexity and maintainability metrics
2. analyze_imports — dependency graph and unused imports
3. security_scan — hardcoded secrets, unsafe patterns
4. token_count — file size and complexity stats

{focus_tasks.get(focus, focus_tasks['all'])}

After analysis, produce a review with:
1. SUMMARY: 2-3 sentence overview
2. CRITICAL: Must-fix issues (security, bugs)
3. WARNINGS: Should-fix issues (performance, style)
4. SUGGESTIONS: Nice-to-have improvements
5. METRICS: Complexity score, functions, imports count""",
            },
        }],
    }
```

#### Automated Fix Generation

```python
@server.tool()
async def suggest_fix(file_path: str, issue_description: str) -> list[TextContent]:
    """Generate a specific code fix for an identified issue.

    Args:
        file_path: Path to the file with the issue
        issue_description: What the issue is (from code review output)
    """
    code = Path(file_path).read_text()

    resp = await server.request_sampling(
        CreateMessageRequestParams(
            messages=[ContentBlock(type="text", text=(
                f"Fix this code issue. Return ONLY the corrected code, no explanation.\n\n"
                f"FILE: {file_path}\n"
                f"ISSUE: {issue_description}\n\n"
                f"```\n{code}\n```"
            ))],
            maxTokens=2000,
            systemPrompt="You are a code fixer. Return only the fixed code.",
        )
    )

    return [TextContent(type="text", text=resp.content[0].text)]
```

---

## Part IV: Production & DevOps

### 29. Deploying HTTP MCP Servers Behind a Reverse Proxy

#### Nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name mcp.internal.company.com;

    ssl_certificate     /etc/ssl/certs/mcp.crt;
    ssl_certificate_key /etc/ssl/private/mcp.key;

    # MCP SSE endpoint (long-lived connections)
    location /mcp {
        proxy_pass http://127.0.0.1:9020;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Critical for SSE: disable buffering
        proxy_buffering off;
        proxy_cache off;

        # SSE connections can be long-lived
        proxy_read_timeout 86400s;
        proxy_send_timeout 86400s;
    }

    # MCP message endpoint
    location /mcp/messages {
        proxy_pass http://127.0.0.1:9020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Health check (no auth required)
    location /health {
        proxy_pass http://127.0.0.1:9020;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }
}
```

#### Docker Compose

```yaml
version: "3.8"

services:
  mcp-server:
    build: .
    ports:
      - "9020:9020"
    environment:
      - PORT=9020
      - MCP_TRANSPORT=http
      - DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@db:5432/mcp
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9020/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=mcp
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

#### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
        - name: mcp-server
          image: registry.company.com/mcp-server:v1.2.0
          ports:
            - containerPort: 9020
          env:
            - name: PORT
              value: "9020"
            - name: MCP_TRANSPORT
              value: "http"
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          readinessProbe:
            httpGet:
              path: /health
              port: 9020
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: 9020
            initialDelaySeconds: 15
            periodSeconds: 20
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
spec:
  selector:
    app: mcp-server
  ports:
    - port: 443
      targetPort: 9020
  type: ClusterIP
```

---

### 30. Observability — Logging, Metrics & Tracing

#### Structured Logging

```python
import logging
import sys

# Configure structured logging
logger = logging.getLogger("mcp-server")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stderr)
handler.setFormatter(logging.Formatter(
    '{"time": "%(asctime)s", "level": "%(levelname)s", "server": "my-server", '
    '"message": %(message)s}'
))
logger.addHandler(handler)

@server.tool()
async def audited_tool(action: str) -> list[TextContent]:
    """A tool with structured logging."""
    logger.info(json.dumps({"event": "tool_called", "tool": "audited_tool", "action": action}))

    try:
        result = perform_action(action)
        logger.info(json.dumps({"event": "tool_success", "tool": "audited_tool", "action": action}))
        return [TextContent(type="text", text=json.dumps(result))]
    except Exception as e:
        logger.error(json.dumps({"event": "tool_error", "tool": "audited_tool", "error": str(e)}))
        raise
```

#### Metrics with Prometheus

```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest

# Define metrics
tool_calls = Counter("mcp_tool_calls_total", "Total tool calls", ["tool_name"])
tool_duration = Histogram("mcp_tool_duration_seconds", "Tool execution time", ["tool_name"])
active_connections = Gauge("mcp_active_connections", "Active SSE connections")
tool_errors = Counter("mcp_tool_errors_total", "Tool errors", ["tool_name", "error_type"])

@server.tool()
async def monitored_tool(query: str) -> list[TextContent]:
    """A tool with Prometheus metrics."""
    tool_calls.labels(tool_name="monitored_tool").inc()

    with tool_duration.labels(tool_name="monitored_tool").time():
        try:
            result = perform_query(query)
            return [TextContent(type="text", text=json.dumps(result))]
        except Exception as e:
            tool_errors.labels(
                tool_name="monitored_tool",
                error_type=type(e).__name__,
            ).inc()
            raise

# Metrics endpoint (in HTTP servers)
async def metrics_endpoint(request):
    return PlainTextResponse(generate_latest())
```

#### MCP-Level Logging

```python
@server.tool()
async def logged_operation(data: str) -> list[TextContent]:
    """A tool that sends log messages to the MCP client."""
    await ctx.log(
        level="info",
        logger="my-server",
        data={"event": "processing_started", "data_size": len(data)},
    )

    result = process(data)

    await ctx.log(
        level="info",
        logger="my-server",
        data={"event": "processing_complete", "result_size": len(result)},
    )

    return [TextContent(type="text", text=result)]
```

---

### 31. Securing MCP HTTP Endpoints

#### API Key Authentication

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

class APIKeyMiddleware(BaseHTTPMiddleware):
    """Validate API key on every request."""

    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key

    async def dispatch(self, request, call_next):
        # Skip health check
        if request.url.path == "/health":
            return await call_next(request)

        # Validate API key
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return JSONResponse({"error": "Missing API key"}, status_code=401)

        if auth.removeprefix("Bearer ") != self.api_key:
            return JSONResponse({"error": "Invalid API key"}, status_code=403)

        return await call_next(request)

app = Starlette(routes=[...])
app.add_middleware(APIKeyMiddleware, api_key=os.environ["MCP_API_KEY"])
```

#### Input Validation

```python
import re

# Validate all string inputs against injection patterns
DANGEROUS_PATTERNS = [
    (re.compile(r'[;&|`$]'), "shell metacharacters"),
    (re.compile(r'\.\./'), "path traversal"),
    (re.compile(r'<script'), "XSS attempt"),
]

def validate_input(value: str, field_name: str) -> str | None:
    """Validate a string input. Returns error message or None."""
    if len(value) > 10000:
        return f"{field_name}: exceeds maximum length (10000)"

    for pattern, attack_type in DANGEROUS_PATTERNS:
        if pattern.search(value):
            return f"{field_name}: contains potentially dangerous content ({attack_type})"

    return None

@server.tool()
async def safe_tool(user_input: str, file_name: str) -> list[TextContent]:
    """A tool with input validation."""
    # Validate all inputs
    for name, value in [("user_input", user_input), ("file_name", file_name)]:
        error = validate_input(value, name)
        if error:
            return [TextContent(type="text", text=json.dumps({"error": error}))]

    # Proceed safely
    ...
```

#### TLS Configuration

```python
# uvicorn with TLS
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=443,
        ssl_keyfile="/etc/ssl/private/mcp.key",
        ssl_certfile="/etc/ssl/certs/mcp.crt",
        ssl_ca_certs="/etc/ssl/certs/ca-bundle.crt",
    )
```

---

### 32. CI/CD Pipelines for MCP Server Projects

#### GitHub Actions

```yaml
name: MCP Server CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install pytest pytest-asyncio pytest-cov

      - name: Run tests
        run: pytest --cov=src --cov-report=xml -v

      - name: Type check
        run: pip install mypy && mypy src/

      - name: Lint MCP tool descriptions
        run: |
          python -c "
          import ast, sys
          # Verify every @server.tool() has a docstring with Args:
          # (Custom check script)
          "

  build-and-push:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -t registry.company.com/mcp-server:${{ github.sha }} .

      - name: Push to registry
        run: |
          echo "${{ secrets.REGISTRY_PASSWORD }}" | docker login registry.company.com -u ${{ secrets.REGISTRY_USER }} --password-stdin
          docker push registry.company.com/mcp-server:${{ github.sha }}
          docker tag registry.company.com/mcp-server:${{ github.sha }} registry.company.com/mcp-server:latest
          docker push registry.company.com/mcp-server:latest

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest

    steps:
      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/mcp-server \
            mcp-server=registry.company.com/mcp-server:${{ github.sha }} \
            --namespace=mcp
          kubectl rollout status deployment/mcp-server --namespace=mcp
```

---

### 33. Health Checks & Graceful Shutdown

#### Health Check Endpoint

```python
async def health_endpoint(request):
    """Comprehensive health check."""
    checks = {}

    # Database check
    try:
        pool = await _get_pool()
        async with pool.acquire() as conn:
            await conn.execute("SELECT 1")
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {e}"

    # External API check
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("https://api.external.com/health")
        checks["external_api"] = "healthy" if resp.status_code == 200 else f"status_{resp.status_code}"
    except Exception as e:
        checks["external_api"] = f"unhealthy: {e}"

    # Overall status
    all_healthy = all(v == "healthy" for v in checks.values())

    return JSONResponse({
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "connected_clients": len(_active_transports),
        "uptime_seconds": time.time() - server_start_time,
    }, status_code=200 if all_healthy else 503)
```

#### Graceful Shutdown

```python
import signal

async def shutdown():
    """Gracefully shut down the server."""
    logger.info("Shutting down...")

    # Stop accepting new connections
    # (uvicorn handles this via signal handlers)

    # Notify connected clients
    for session_id, transport in list(_active_connections.items()):
        try:
            await transport.send_event("server_shutdown", {
                "message": "Server is shutting down. Please reconnect in a moment.",
                "timestamp": datetime.now().isoformat(),
            })
        except Exception:
            pass

    # Close database pool
    if _pool:
        await _pool.close()

    # Flush pending writes
    _save_tasks()

    logger.info("Shutdown complete")

# Register signal handlers
loop = asyncio.get_event_loop()
for sig in (signal.SIGTERM, signal.SIGINT):
    loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
```

---

### 34. Load Testing & Capacity Planning

#### Locust Load Test

```python
# locustfile.py
from locust import HttpUser, task, between

class MCPUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def health_check(self):
        self.client.get("/health")

    @task(3)
    def call_tool(self):
        """Simulate a tool call through the message endpoint."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_logs",
                "arguments": {"query": "error", "since_minutes": 60},
            },
        }
        self.client.post("/mcp/messages?session_id=test", json=payload)

    @task(5)
    def sse_connect(self):
        """Simulate an SSE connection."""
        self.client.get("/mcp", stream=True)
```

#### Capacity Planning

```
Benchmark assumptions (per replica):
  - 2 vCPU, 512MB RAM
  - avg tool call: 200ms
  - avg SSE keepalive: negligible CPU

Capacity calculator:
  concurrent_connections = memory_per_replica / memory_per_connection
  requests_per_second = vcpus * (1000ms / avg_tool_ms)

Example:
  - 50 concurrent SSE connections (~10MB each = 500MB, fits in 512MB)
  - 2 vCPU * (1000 / 200) = 10 requests/second per replica
  - 3 replicas = 30 req/s, 150 concurrent connections

For higher throughput:
  - Scale horizontally (more replicas)
  - Add Redis for shared state (stateless replicas)
  - Use async database drivers (asyncpg, aioredis)
```

#### Scaling Architecture

```
                    ┌─────────────┐
                    │  LB / NGINX │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         ┌────▼───┐   ┌───▼────┐  ┌───▼────┐
         │Replica 1│   │Replica2│  │Replica3│
         └────┬────┘   └───┬────┘  └───┬────┘
              │            │            │
              └────────────┼────────────┘
                           │
              ┌────────────▼────────────┐
              │    Redis (shared state) │
              │    Postgres (persistence)│
              └─────────────────────────┘
```

---

## Part V: Advanced Patterns

### 35. Dynamic Tool Registration

Tools that create, modify, or remove other tools at runtime.

```python
_dynamic_tools: dict[str, callable] = {}

@server.tool()
async def create_tool(
    name: str,
    description: str,
    code: str,
) -> list[TextContent]:
    """Create a new tool dynamically from Python code.

    USE WITH EXTREME CAUTION. The code is executed with full server privileges.

    Args:
        name: Tool name (snake_case). Must be unique.
        description: What the tool does (becomes the docstring)
        code: Python async function body that returns list[TextContent].
              Has access to: json, httpx, asyncio, os.environ
    """
    if name in server._tools:
        return [TextContent(type="text", text=json.dumps({"error": f"Tool '{name}' already exists"}))]

    # Build the function dynamically
    func_code = f"""
async def {name}(**kwargs):
    \"\"\"{description}\"\"\"
    {code}
"""
    namespace = {
        "json": json,
        "httpx": httpx,
        "asyncio": asyncio,
        "os": os,
        "TextContent": TextContent,
    }
    exec(func_code, namespace)
    func = namespace[name]

    # Register it
    server._tools[name] = func

    return [TextContent(type="text", text=json.dumps({"created": name}))]

@server.tool()
async def list_dynamic_tools() -> list[TextContent]:
    """List all dynamically created tools."""
    return [TextContent(type="text", text=json.dumps({
        "dynamic_tools": list(_dynamic_tools.keys()),
        "static_tools": [t for t in server._tools if t not in _dynamic_tools],
    }, indent=2))]

@server.tool()
async def remove_tool(name: str) -> list[TextContent]:
    """Remove a dynamically created tool.

    Args:
        name: Tool to remove. Only dynamic tools can be removed.
    """
    if name not in _dynamic_tools:
        return [TextContent(type="text", text=json.dumps({
            "error": f"Cannot remove '{name}'. Not a dynamic tool or doesn't exist."
        }))]

    del server._tools[name]
    del _dynamic_tools[name]
    return [TextContent(type="text", text=json.dumps({"removed": name}))]
```

---

### 36. Resource Subscriptions — Pushing Live Updates

**Reference:** `mcp_servers/monitoring_server.py` — `monitor://live-metrics` resource.

#### Subscription-Ready Resource

```python
_subscriptions: dict[str, float] = {}  # uri → last_notified

@server.resource("live://scores")
async def live_scores() -> str:
    """Live sports scores. Clients can subscribe for updates."""
    current = fetch_scores()
    return json.dumps(current, indent=2)

# Background task to notify subscribers
async def _notify_loop():
    """Check for changes and notify subscribers every 30 seconds."""
    last_state = {}
    while True:
        await asyncio.sleep(30)

        current = fetch_scores()
        for uri, last_notified in list(_subscriptions.items()):
            if current != last_state.get(uri):
                # In a real implementation, this sends a
                # notifications/resources/updated message
                logger.info(f"Resource {uri} changed, notifying subscribers")
                # await server.notify_resource_updated(uri)

            last_state[uri] = current
```

#### Client-Side Subscription (Conceptual)

```json
{
  "jsonrpc": "2.0",
  "id": 42,
  "method": "resources/subscribe",
  "params": {
    "uri": "live://scores"
  }
}
```

The server then sends `notifications/resources/updated` whenever the resource changes:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": {
    "uri": "live://scores"
  }
}
```

---

### 37. Cross-Server Composition

One MCP server calling another's tools.

#### Pattern: MCP Client Within a Server

```python
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

@server.tool()
async def composed_workflow(data: str) -> list[TextContent]:
    """A tool that calls another MCP server's tools internally."""
    # Connect to another MCP server
    params = StdioServerParameters(
        command="python",
        args=["mcp_servers/code_analyzer_server.py"],
    )

    async with Client(params) as client:
        # Step 1: Use the other server's tool
        analysis = await client.call_tool("analyze_complexity", {"file_path": data})
        complexity = json.loads(analysis.content[0].text)

        # Step 2: Use sampling
        resp = await server.request_sampling(
            CreateMessageRequestParams(
                messages=[ContentBlock(type="text", text=(
                    f"Based on this code analysis, suggest improvements:\n"
                    f"{json.dumps(complexity, indent=2)}"
                ))],
                maxTokens=500,
            )
        )

    return [TextContent(type="text", text=json.dumps({
        "analysis": complexity,
        "suggestions": resp.content[0].text,
    }, indent=2))]
```

#### Pattern: HTTP Server as Proxy

```python
@server.tool()
async def proxy_to_other_server(server_url: str, tool_name: str, args: dict) -> list[TextContent]:
    """Call a tool on another MCP server via HTTP."""
    # This assumes the other server exposes a direct tool-call endpoint
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{server_url}/mcp/messages",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": args},
            },
        )
        return [TextContent(type="text", text=resp.text)]
```

---

### 38. Versioning MCP Server APIs

#### Semantic Versioning for MCP Servers

```
MAJOR.MINOR.PATCH

MAJOR — breaking changes:
  - Removing a tool
  - Renaming a tool
  - Changing a tool's required arguments
  - Removing a resource URI
  - Changing a resource URI pattern

MINOR — new features, backward-compatible:
  - Adding a new tool
  - Adding optional arguments to existing tools
  - Adding new resource URIs
  - Adding new prompts

PATCH — backward-compatible fixes:
  - Bug fixes
  - Docstring improvements
  - Performance improvements
  - Error message improvements
```

#### Deprecation Pattern

```python
import warnings
from functools import wraps

def deprecated(since: str, use_instead: str):
    """Mark a tool as deprecated."""
    def decorator(func):
        func.__doc__ = (
            f"[DEPRECATED since {since}. Use '{use_instead}' instead.]\n"
            + (func.__doc__ or "")
        )
        return func
    return decorator

@server.tool()
@deprecated(since="v2.0.0", use_instead="search_logs")
async def log_search(query: str) -> list[TextContent]:
    """Search logs. DEPRECATED — use search_logs instead."""
    # Forward to new implementation
    return await search_logs(query=query)
```

#### Version Resource

```python
@server.resource("server://version")
async def version_info() -> str:
    """Server version and API compatibility info."""
    return json.dumps({
        "server": "my-server",
        "version": "2.1.0",
        "mcp_protocol": "2024-11-05",
        "api_version": "2",
        "deprecated": [
            {"tool": "log_search", "since": "2.0.0", "use_instead": "search_logs"},
        ],
        "changelog_url": "https://github.com/company/mcp-server/blob/main/CHANGELOG.md",
    }, indent=2)
```

---

### 39. Feature Flags & Staged Rollout

**Reference:** `mcp_servers/http_team_server.py` — `manage_feature_flags` tool.

#### Feature Flag System for MCP Tools

```python
# Feature flags control tool availability and behavior
_feature_flags: dict[str, dict] = {
    "new_search_algorithm": {
        "enabled": False,
        "rollout_pct": 10,  # Enable for 10% of calls
        "description": "Use the new semantic search instead of keyword search",
    },
    "export_v2": {
        "enabled": True,
        "rollout_pct": 100,
        "description": "Export data in the new v2 format",
    },
}

def _is_enabled(flag_name: str, session_id: str = "") -> bool:
    """Check if a feature flag is enabled for this call."""
    flag = _feature_flags.get(flag_name)
    if not flag:
        return False

    if flag["enabled"] and flag["rollout_pct"] >= 100:
        return True

    if flag["enabled"] and flag["rollout_pct"] > 0:
        # Deterministic rollout based on session ID
        hash_val = hash(session_id + flag_name) % 100
        return hash_val < flag["rollout_pct"]

    return False

@server.tool()
async def search(query: str) -> list[TextContent]:
    """Search with feature-flagged algorithm selection."""
    if _is_enabled("new_search_algorithm", ctx.session_id):
        # Use the new semantic search
        results = semantic_search(query)
        return [TextContent(type="text", text=json.dumps({
            "method": "semantic",
            "results": results,
        }))]

    # Use the original keyword search
    results = keyword_search(query)
    return [TextContent(type="text", text=json.dumps({
        "method": "keyword",
        "results": results,
    }))]
```

#### Staged Rollout Tool

```python
@server.tool()
async def manage_rollout(
    flag_name: str,
    action: str,
    rollout_pct: int = 0,
) -> list[TextContent]:
    """Manage feature flag rollout percentage.

    Args:
        flag_name: Feature flag to manage
        action: "get", "enable", "disable", "set_pct"
        rollout_pct: Rollout percentage 0-100 (for "set_pct")
    """
    if action == "get":
        return [TextContent(type="text", text=json.dumps(_feature_flags.get(flag_name, {})))]
    elif action == "enable":
        _feature_flags[flag_name]["enabled"] = True
        _feature_flags[flag_name]["rollout_pct"] = 100
    elif action == "disable":
        _feature_flags[flag_name]["enabled"] = False
        _feature_flags[flag_name]["rollout_pct"] = 0
    elif action == "set_pct":
        _feature_flags[flag_name]["enabled"] = rollout_pct > 0
        _feature_flags[flag_name]["rollout_pct"] = max(0, min(100, rollout_pct))

    return [TextContent(type="text", text=json.dumps({
        "flag": flag_name,
        "status": _feature_flags[flag_name],
    }, indent=2))]
```

---

### 40. Building Custom MCP Clients

While Claude Code is the primary client, you can build your own MCP clients.

#### Minimal Python Client

```python
import asyncio
import json
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

async def main():
    # Connect to a server
    params = StdioServerParameters(
        command="python",
        args=["mcp_servers/weather_server.py"],
    )

    async with Client(params) as client:
        # List available tools
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools]}")

        # Call a tool
        result = await client.call_tool("get_weather", {"city": "London"})
        print(f"Result: {result.content[0].text}")

        # List resources
        resources = await client.list_resources()
        print(f"Resources: {[r.uri for r in resources]}")

        # Read a resource
        data = await client.read_resource("weather://cache-stats")
        print(f"Resource: {data.contents[0].text}")

if __name__ == "__main__":
    asyncio.run(main())
```

#### HTTP Client

```python
import asyncio
import httpx
import json

class MCPHTTPClient:
    """Minimal MCP HTTP client."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_id = None
        self.id_counter = 0

    async def connect(self):
        """Establish SSE connection and get session ID."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/mcp", stream=True)
            # Session ID typically comes from first SSE event or headers
            self.session_id = resp.headers.get("X-Session-ID", "default")

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Call a tool on the server."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/mcp/messages?session_id={self.session_id}",
                json={
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                },
            )
            return resp.json()

    def _next_id(self) -> int:
        self.id_counter += 1
        return self.id_counter

async def main():
    client = MCPHTTPClient("http://localhost:9020")
    await client.connect()

    result = await client.call_tool("team_announce", {
        "message": "Hello from custom client!",
        "priority": "high",
    })
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
```

#### Headless Agent Loop

```python
class MCPAgent:
    """A simple agent that uses MCP tools to accomplish goals."""

    def __init__(self, mcp_client: Client):
        self.client = mcp_client
        self.tools = []
        self.history = []

    async def setup(self):
        """Load available tools."""
        self.tools = await self.client.list_tools()

    async def run(self, goal: str):
        """Execute a goal using available tools."""
        self.history.append({"role": "user", "content": goal})

        # Determine which tool to call (in a real agent, use an LLM here)
        tool = self._select_tool(goal)
        if not tool:
            return "No suitable tool found for this goal."

        # Call the tool
        result = await self.client.call_tool(tool.name, self._extract_args(goal, tool))
        self.history.append({"role": "assistant", "content": result.content[0].text})

        return result.content[0].text

    def _select_tool(self, goal: str):
        """Select the best tool for a goal. In production, use an LLM for this."""
        # Simplified: keyword matching
        for tool in self.tools:
            if any(word in goal.lower() for word in tool.name.lower().split("_")):
                return tool
        return self.tools[0] if self.tools else None

    def _extract_args(self, goal: str, tool) -> dict:
        """Extract arguments from the goal. In production, use an LLM."""
        # Simplified: return empty dict for no-arg tools
        return {}
```

#### CLI Wrapper

```python
#!/usr/bin/env python3
"""A CLI tool that wraps any MCP server as a command-line interface."""

import asyncio
import argparse
import json

async def main():
    parser = argparse.ArgumentParser(description="MCP CLI Client")
    parser.add_argument("--server", required=True, help="Python MCP server file")
    parser.add_argument("--tool", required=True, help="Tool name")
    parser.add_argument("--args", default="{}", help="Tool arguments as JSON")
    args = parser.parse_args()

    params = StdioServerParameters(
        command="python",
        args=[args.server],
    )

    async with Client(params) as client:
        result = await client.call_tool(args.tool, json.loads(args.args))
        print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(main())
```

Usage:
```bash
./mcp_cli.py --server mcp_servers/weather_server.py --tool get_weather --args '{"city": "Tokyo"}'
```

---

## Appendices

### A. Quick Reference: All MCP Methods

| Method | Type | Description |
|--------|------|-------------|
| `initialize` | Request | Client → Server: start session |
| `notifications/initialized` | Notification | Client → Server: handshake done |
| `tools/list` | Request | Get available tools |
| `tools/call` | Request | Execute a tool |
| `resources/list` | Request | Get available resources |
| `resources/read` | Request | Read a resource by URI |
| `resources/subscribe` | Request | Subscribe to resource updates |
| `prompts/list` | Request | Get available prompts |
| `prompts/get` | Request | Get a prompt template |
| `sampling/createMessage` | Request | Server → Client: request LLM generation |
| `elicitation/create` | Request | Server → Client: ask user a question |
| `logging/setLevel` | Request | Client → Server: set log level |
| `notifications/cancelled` | Notification | Cancel in-progress request |
| `notifications/progress` | Notification | Progress update for long operation |
| `completion/complete` | Request | Get autocomplete suggestions |
| `roots/list` | Request | Server → Client: get root directories |

### B. Cross-Reference: Guide ↔ Existing Servers

| Topic | Reference Server | File |
|-------|-----------------|------|
| API wrapping + caching | Weather Server | `mcp_servers/weather_server.py` |
| File operations + binary data | File Converter | `mcp_servers/file_converter_server.py` |
| Shell sandboxing + path safety | DevOps Server | `mcp_servers/devops_server.py` |
| Data transformation + validation | Data ETL Server | `mcp_servers/data_etl_server.py` |
| OS notifications + scheduling | Notification Server | `mcp_servers/notification_server.py` |
| AST analysis + code metrics | Code Analyzer | `mcp_servers/code_analyzer_server.py` |
| Multi-source search + dedup | Search Aggregator | `mcp_servers/search_aggregator_server.py` |
| Encryption + vault + TOTP | Secret Manager | `mcp_servers/secret_manager_server.py` |
| System metrics + alerting | Monitoring Server | `mcp_servers/monitoring_server.py` |
| Document parsing + text analysis | Document Processor | `mcp_servers/document_processor_server.py` |
| Image processing + OCR | Image Processor | `mcp_servers/image_processor_server.py` |
| Email composition + sending | Email Server | `mcp_servers/email_server.py` |
| Cryptography + JWT | Crypto Server | `mcp_servers/crypto_server.py` |
| Project scaffolding | Project Scaffolder | `mcp_servers/project_scaffolder_server.py` |
| Calendar + scheduling | Calendar Server | `mcp_servers/calendar_server.py` |
| Sampling (5 patterns) | Sampling Demo | `mcp_servers/sampling_demo_server.py` |
| HTTP/SSE transport + multi-client | HTTP Team Server | `mcp_servers/http_team_server.py` |

### C. Decision Cheat Sheet

```
I want to...                              → Use this section
─────────────────────────────────────────────────────────────
Build my first MCP server                 → §1 (Walkthrough)
Decide stdio vs HTTP transport            → §2 (Decision Matrix)
Design a good tool interface              → §3 (Tool Signatures)
Decide Tool vs Resource vs Prompt         → §4 (Decision Framework)
Do server-initiated LLM calls             → §5 (Sampling)
Pause for user input during a tool        → §6 (Elicitation)
Add autocomplete to tool arguments        → §7 (Completions)
Handle long-running operations            → §8 (Progress Reporting)
Return good error messages                → §9 (Error Handling)
Test my server                            → §10 (Testing)
Package for PyPI or Docker                → §11 (Packaging)
Handle multiple clients on one server     → §12 (Multi-Client State)
Wrap a REST API                           → §13 (API Wrappers)
Handle streaming APIs                     → §14 (Streaming)
Add retries and rate limiting             → §15 (Resilience)
Pass auth tokens through                  → §16 (Auth Passthrough)
Receive webhooks in an MCP server         → §17 (Webhooks)
Work with GraphQL                         → §18 (GraphQL)
Connect to a database                     → §19 (Databases)
Safely access the filesystem              → §20 (File System)
Build multi-step agent workflows          → §21 (Chaining)
Use AI for self-review loops              → §22 (Self-Critique)
Coordinate multiple Claude instances      → §23 (Multi-Agent)
Build a RAG system                        → §24 (RAG)
Add human approval gates                  → §25 (Human-in-Loop)
Write better tool descriptions            → §26 (Prompt Engineering)
Extract structured data with LLMs         → §27 (Structured Extraction)
Build a code review agent                 → §28 (Code Review)
Deploy to production                      → §29 (Deployment)
Add logging, metrics, tracing             → §30 (Observability)
Secure the server                         → §31 (Security)
Set up CI/CD                              → §32 (CI/CD)
Add health checks and graceful shutdown   → §33 (Health Checks)
Load test and plan capacity               → §34 (Load Testing)
Create tools at runtime                   → §35 (Dynamic Tools)
Push live updates to clients              → §36 (Subscriptions)
Call other MCP servers from a server      → §37 (Cross-Server)
Version the API without breaking clients  → §38 (Versioning)
Roll out features gradually               → §39 (Feature Flags)
Build a custom MCP client                 → §40 (Custom Clients)
```

---

*See also: [mcp.md](mcp.md) for the protocol reference, message format, lifecycle, and all 17 reference MCP server implementations.*
