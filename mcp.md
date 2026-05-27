# MCP (Model Context Protocol) with Claude Code — The Complete Bible

MCP is an open protocol that lets Claude connect to external tools, data sources, and services through a standard server interface. Think of it as a "USB-C port for AI" — one protocol, any data source.

**This is the ultimate reference.** Covers every MCP feature, primitive, transport, pattern, server, and edge case. Includes 15 production-grade custom MCP servers you can install and use immediately.

---

## Table of Contents

### Part I: Foundations
1. [What is MCP?](#what-is-mcp)
2. [MCP Architecture](#mcp-architecture)
3. [The Four MCP Primitives](#the-four-mcp-primitives)
4. [MCP Protocol Deep Dive](#mcp-protocol-deep-dive)
   - [JSON-RPC Message Format](#json-rpc-message-format)
   - [Protocol Lifecycle](#protocol-lifecycle)
   - [Capability Negotiation](#capability-negotiation)
   - [Error Handling](#error-handling)
   - [Progress Notifications](#progress-notifications)
   - [Request Cancellation](#request-cancellation)
   - [Pagination](#pagination)
5. [Transport Types](#transport-types)
   - [stdio — Local Process](#1-stdio-local-process)
   - [SSE / Streamable HTTP — Remote Service](#2-sse--streamable-http--remote-service)
   - [Hybrid with OAuth](#3-hybrid-with-oauth)
   - [Transport Comparison & Troubleshooting](#transport-comparison--troubleshooting)

### Part II: Configuration & Management
6. [Configuring MCP Servers](#configuring-mcp-servers)
7. [Using the `/mcp` Command](#using-the-mcp-command)
8. [OAuth Authentication for MCP](#oauth-authentication)

### Part III: Primitives in Depth
9. [MCP Tools — Full Feature Walkthrough](#mcp-tools)
   - [How Tools Work](#how-tools-work)
   - [Tool Naming Convention](#tool-naming-convention)
   - [Tool Annotations](#tool-annotations)
   - [Structured Content in Tool Responses](#structured-content-in-tool-responses)
   - [Tool Execution Progress](#tool-execution-progress)
10. [MCP Resources — Exposing Data](#mcp-resources)
    - [Resource Templates](#resource-templates)
    - [Resource Subscriptions](#resource-subscriptions)
    - [Resource Metadata](#resource-metadata)
11. [MCP Prompts — Reusable Templates](#mcp-prompts)
12. [MCP Sampling — LLM Callbacks from Servers](#mcp-sampling)

### Part IV: Advanced Features
13. [Elicitation — Asking the User During Tool Execution](#elicitation)
14. [Roots — Telling Servers About Relevant Files](#roots)
15. [Logging — Server-to-Client Log Messages](#logging)
16. [Completions — Argument Autocomplete](#completions)
17. [MCP Hooks — Guarding MCP Tool Calls](#mcp-hooks)
18. [MCP Dynamic Slash Commands](#mcp-dynamic-slash-commands)

### Part V: Popular MCP Servers
19. [Popular MCP Servers — In-Depth Examples](#popular-mcp-servers)
    - [Context7 — Documentation at Your Fingertips](#context7)
    - [Playwright — Browser Automation](#playwright-mcp)
    - [Filesystem — Secure File Operations](#filesystem-mcp)
    - [GitHub — Repository Management](#github-mcp)
    - [Postgres / SQLite — Database Access](#database-mcp-servers)
    - [Brave Search — Web Search](#brave-search-mcp)
    - [Puppeteer — Headless Chrome](#puppeteer-mcp)
    - [Memory — Persistent Knowledge Graph](#memory-mcp)
    - [Sequential Thinking — Structured Reasoning](#sequential-thinking-mcp)
    - [Fetch — Web Content Retrieval](#fetch-mcp)

### Part VI: Custom MCP Server Library
20. [Custom MCP Server Library](#custom-mcp-server-library)
    - [Weather Server](#1-weather-server--external-api-integration)
    - [File Converter Server](#2-file-converter-server--binary-data--image-processing)
    - [DevOps Server](#3-devops-server--shell-commands--system-management)
    - [Data ETL Server](#4-data-etl-server--data-transformation-pipelines)
    - [Notification Server](#5-notification-server--desktop-notifications--scheduling)
    - [Code Analyzer Server](#6-code-analyzer-server--code-metrics--static-analysis)
    - [Search Aggregator Server](#7-search-aggregator-server--multi-source-search)
    - [Secret Manager Server](#8-secret-manager-server--encryption--credential-management)
    - [Monitoring Server](#9-monitoring-server--metrics--health-checks--alerting)
    - [Document Processor Server](#10-document-processor-server--document-parsing--text-analysis)
    - [Image Processor Server](#11-image-processor-server--image-manipulation--ocr)
    - [Email Server](#12-email-server--email-composition--templates)
    - [Crypto Server](#13-crypto-server--cryptographic-operations)
    - [Project Scaffolder Server](#14-project-scaffolder-server--project-generation)
    - [Calendar Server](#15-calendar-server--datetime-operations)

### Part VII: Building MCP Servers
21. [Building Your Own MCP Server](#building-your-own-mcp-server)
    - [Minimal TypeScript MCP Server](#minimal-typescript-mcp-server)
    - [Adding Resources](#adding-a-resource-to-your-server)
    - [Adding Prompts](#adding-a-prompt-to-your-server)
    - [Minimal Python MCP Server](#minimal-python-mcp-server)
    - [Adding Logging to Your Server](#adding-logging-to-your-server)
    - [Adding Progress Reporting](#adding-progress-reporting)
    - [Adding Completions](#adding-completions)
    - [Adding Elicitation](#adding-elicitation)

### Part VIII: Production
22. [Debugging MCP Servers](#debugging-mcp-servers)
23. [MCP Server Best Practices](#mcp-server-best-practices)
24. [Testing MCP Servers](#testing-mcp-servers)
25. [Security Considerations](#security-considerations)
26. [Performance Optimization](#performance-optimization)
27. [Deployment Strategies](#deployment-strategies)

### Part IX: Reference
28. [Quick Reference](#quick-reference)

---

## What is MCP?

MCP (Model Context Protocol) is an **open standard** created by Anthropic that defines how AI models like Claude connect to external tools and data sources. It replaces the old pattern of each AI tool having its own custom integration with a single, unified protocol.

```
Before MCP (N × M integrations):            With MCP (N + M integrations):

  Claude ──── custom ──── Postgres            Claude ────┐
  Claude ──── custom ──── GitHub               Claude ────┤
  Claude ──── custom ──── Filesystem           Claude ────┤── MCP ─── Postgres
  ChatGPT ─── custom ──── Postgres             ChatGPT ───┤          ├── GitHub
  ChatGPT ─── custom ──── GitHub               Gemini ────┘          ├── Filesystem
  ...                                                                 └── ...
```

**Key benefits:**
- **Write once, use everywhere:** Any MCP-compatible client (Claude Code, Claude Desktop, VS Code, Cursor, Continue.dev) can use any MCP server.
- **Standardized capability discovery:** Clients auto-discover what tools, resources, and prompts a server provides.
- **Security boundaries:** Servers run as separate processes; permissions are explicit and auditable.
- **Language-agnostic:** Servers can be written in Python, TypeScript, Go, Rust, or any language that speaks JSON-RPC over stdio or HTTP.

**MCP is not:**
- A model-serving protocol (it doesn't run LLMs)
- A replacement for REST APIs (it's for AI-to-tool communication)
- A data format (it uses JSON-RPC, not a custom wire format)

---

## MCP Architecture

```
┌─────────────────────┐         Transport          ┌─────────────────────┐
│                     │  ◄══════════════════════►  │                     │
│   Claude Code       │    stdio / SSE / HTTP      │   MCP Server        │
│   (MCP Client)      │                            │   (your data/tool)  │
│                     │    JSON-RPC messages        │                     │
└─────────────────────┘                            └─────────────────────┘
```

MCP uses **JSON-RPC 2.0** as its message format. The client (Claude Code) and server exchange messages over one of three transport mechanisms:

- **stdio** — the server runs as a child process, communication via stdin/stdout
- **SSE (Server-Sent Events)** — the server runs as a remote HTTP service
- **Streamable HTTP** — newer variant of SSE with better connection handling

Every interaction follows a request/response or request/notification pattern, all encoded as JSON-RPC messages.

### Protocol Layers

```
┌──────────────────────────────┐
│   MCP Application Layer      │  ← Tools, Resources, Prompts, Sampling
├──────────────────────────────┤
│   MCP Protocol Layer         │  ← Lifecycle, Capabilities, Negotiation
├──────────────────────────────┤
│   JSON-RPC 2.0               │  ← Request/Response/Notification
├──────────────────────────────┤
│   Transport (stdio/HTTP)     │  ← Byte stream / HTTP messages
└──────────────────────────────┘
```

---

## The Four MCP Primitives

MCP servers expose four kinds of capabilities. Claude Code supports all of them:

| Primitive | Direction | Purpose | Example |
|-----------|-----------|---------|---------|
| **Tools** | Client → Server | Let Claude perform actions | Run a SQL query, click a button, search the web |
| **Resources** | Server → Client | Expose read-only data to Claude | File contents, DB schemas, API docs |
| **Prompts** | Server → Client | Reusable prompt templates | "Review this PR", "Summarize this schema" |
| **Sampling** | Server → Client | Server asks Claude to generate text | Server needs Claude to summarize something mid-task |

```
┌──────────────┐                              ┌──────────────┐
│              │ ── Tools (action requests) ──► │              │
│ Claude Code  │ ◄── Resources (data) ───────── │ MCP Server   │
│  (Client)    │ ◄── Prompts (templates) ────── │              │
│              │ ◄── Sampling (LLM requests) ── │              │
└──────────────┘                              └──────────────┘
```

---

## MCP Protocol Deep Dive

### JSON-RPC Message Format

All MCP messages are JSON-RPC 2.0 objects. There are four message types:

**1. Request** (client → server or server → client):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "query",
    "arguments": { "sql": "SELECT * FROM users" }
  }
}
```

**2. Response** (reply to a request):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      { "type": "text", "text": "id,name\n1,Alice\n2,Bob" }
    ]
  }
}
```

**3. Error Response** (when a request fails):
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "Missing required parameter: sql"
  }
}
```

**4. Notification** (one-way message, no `id`):
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "progressToken": "task-1",
    "progress": 50,
    "total": 100
  }
}
```

### Protocol Lifecycle

Every MCP connection goes through a defined lifecycle:

```
  ┌──────────┐
  │  Created  │  Transport established (process spawned / HTTP connected)
  └────┬─────┘
       │ Client sends: initialize request
       ▼
  ┌──────────┐
  │ Initializing│  Client and server exchange capabilities
  └────┬─────┘
       │ Server responds: initialize result
       │ Client sends: initialized notification
       ▼
  ┌──────────┐
  │  Running  │  Normal operation — tools, resources, prompts
  └────┬─────┘
       │ Client sends: shutdown request (or process exits)
       ▼
  ┌──────────┐
  │  Shutdown │  Server cleans up, client sends exit notification
  └──────────┘
```

**Initialize request** (client → server):
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "method": "initialize",
  "params": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": {},
      "resources": { "subscribe": true },
      "prompts": {},
      "sampling": {}
    },
    "clientInfo": {
      "name": "Claude Code",
      "version": "2.0.0"
    }
  }
}
```

**Initialize response** (server → client):
```json
{
  "jsonrpc": "2.0",
  "id": 0,
  "result": {
    "protocolVersion": "2025-03-26",
    "capabilities": {
      "tools": { "listChanged": true },
      "resources": { "subscribe": true, "listChanged": true },
      "prompts": { "listChanged": true },
      "logging": {}
    },
    "serverInfo": {
      "name": "my-postgres-server",
      "version": "2.1.0"
    }
  }
}
```

**Initialized notification** (client → server):
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}
```

After this notification, the server can begin sending its own requests (logging, sampling, etc.).

**Ping** (either direction — heartbeats for connection health):
```json
{ "jsonrpc": "2.0", "id": 99, "method": "ping" }
```

Response:
```json
{ "jsonrpc": "2.0", "id": 99, "result": {} }
```

**Shutdown** (client → server):
```json
{ "jsonrpc": "2.0", "id": 100, "method": "shutdown" }
```

After the server responds, the client sends an exit notification and closes the transport.

### Capability Negotiation

Both client and server declare what they support during initialization. This ensures forward compatibility.

**Client capabilities** (what the client can do):
| Capability | Meaning |
|------------|---------|
| `tools` | Client can call tools |
| `resources.subscribe` | Client supports resource subscriptions |
| `resources.listChanged` | Client watches for resource list changes |
| `prompts` | Client can use prompt templates |
| `sampling` | Client allows server-initiated LLM requests |
| `elicitation` | Client can ask user during tool execution |
| `roots.listChanged` | Client notifies when roots change |
| `experimental` | Object with experimental feature flags |

**Server capabilities** (what the server provides):
| Capability | Meaning |
|------------|---------|
| `tools.listChanged` | Server notifies when tool list changes |
| `resources.subscribe` | Server supports resource subscriptions |
| `resources.listChanged` | Server notifies when resource list changes |
| `prompts.listChanged` | Server notifies when prompt list changes |
| `logging` | Server can send log messages to client |
| `completions` | Server provides argument autocomplete |
| `experimental` | Object with experimental feature flags |

### Error Handling

MCP uses standard JSON-RPC error codes plus MCP-specific ones:

**Standard JSON-RPC errors:**
| Code | Name | Meaning |
|------|------|---------|
| `-32700` | Parse error | Invalid JSON received |
| `-32600` | Invalid Request | Not a valid JSON-RPC request |
| `-32601` | Method not found | Unknown method name |
| `-32602` | Invalid params | Wrong parameter types or missing required params |
| `-32603` | Internal error | Server-side error |

**MCP-specific errors:**
| Code | Name | Meaning |
|------|------|---------|
| `-32000` | Server not initialized | Request sent before `initialized` notification |
| `-32001` | Unknown capability | Server doesn't support requested capability |
| `-32002` | Request cancelled | Request was cancelled by client |

**Best practice for server errors:** Return structured error data so Claude can understand and recover:
```python
# Good error response
raise McpError(
    code=-32602,
    message="Invalid SQL query",
    data={
        "sql": "SELECT * FORM users",  # echoed input
        "error_detail": "Syntax error at 'FORM' — did you mean 'FROM'?",
        "position": 14,
    }
)
```

### Progress Notifications

Long-running tool calls can report progress via notifications:

**Server → Client progress notification:**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/progress",
  "params": {
    "progressToken": "batch-export-1",
    "progress": 45,
    "total": 100
  }
}
```

The `progressToken` is set by the client in the original request params. The server can send multiple progress updates.

**Python example:**
```python
@server.tool()
async def export_data(format: str, ctx: Context) -> list[TextContent]:
    rows = fetch_all_rows()
    total = len(rows)
    for i, row in enumerate(rows):
        if i % 100 == 0:
            await ctx.report_progress(
                progress=i,
                total=total,
                message=f"Exporting row {i}/{total}",
            )
    return [TextContent(type="text", text=format_output(rows))]
```

### Request Cancellation

Clients can cancel in-progress tool calls:

**Client → Server cancel notification:**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/cancelled",
  "params": {
    "requestId": 42,
    "reason": "User requested cancellation"
  }
}
```

Servers should check for cancellation during long operations and raise `McpError` with code `-32002`.

**Python example of cancellation-aware server:**
```python
@server.tool()
async def long_running_task(ctx: Context) -> list[TextContent]:
    for i in range(100):
        if ctx.cancelled:
            raise McpError(code=-32002, message="Request cancelled")
        await asyncio.sleep(0.5)
    return [TextContent(type="text", text="Done")]
```

### Pagination

For `resources/list`, `resources/templates/list`, `tools/list`, and `prompts/list`, servers can paginate results using cursors:

**Request with cursor:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "method": "resources/list",
  "params": { "cursor": "page-2-cursor" }
}
```

**Response with nextCursor:**
```json
{
  "jsonrpc": "2.0",
  "id": 10,
  "result": {
    "resources": [ /* ... */ ],
    "nextCursor": "page-3-cursor"
  }
}
```

When `nextCursor` is omitted, the client knows it has all results.

---

## Transport Types

### 1. stdio (Local Process)

The simplest and most common pattern. The MCP server runs as a local child process. Claude Code starts it, communicates via stdin/stdout.

```json
{
  "mcpServers": {
    "sqlite": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "myapp.db"],
      "env": {
        "SQLITE_READONLY": "false"
      }
    }
  }
}
```

**Pros:** Fastest latency, no network overhead, process isolation, simple setup.
**Cons:** Only local, must install runtime (node/python/etc.), server per client instance.

### 2. SSE / Streamable HTTP (Remote Service)

The MCP server runs as a standalone HTTP service — possibly on another machine. Claude Code connects via HTTP and receives server-to-client messages through an event stream.

```json
{
  "mcpServers": {
    "context7": {
      "type": "url",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

**Pros:** Shared across team/clients, centralized auth, cloud-friendly.
**Cons:** Network latency, requires hosting infrastructure, needs auth management.

### 3. Hybrid with OAuth

Some remote servers require authentication. Claude Code supports the full MCP OAuth flow:

```json
{
  "mcpServers": {
    "github": {
      "type": "url",
      "url": "https://api.github.com/mcp",
      "auth": "oauth"
    }
  }
}
```

### Transport Comparison & Troubleshooting

```
Is the tool...
  ├── A local program/script that runs on your machine?
  │     → stdio  (fastest, simplest)
  │
  ├── A shared team service running on internal infrastructure?
  │     → url (SSE/HTTP)
  │
  ├── A SaaS/cloud MCP service?
  │     → url + OAuth
  │
  └── Something only you use, with filesystem access needed?
        → stdio  (no network overhead)
```

**Troubleshooting transport issues:**

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| stdio server won't start | Wrong binary path | Test the `command` manually in terminal |
| stdio server exits immediately | Missing dependency | Run with same args manually to see error |
| URL server "connection refused" | Wrong URL or server down | Verify URL with `curl` |
| SSE connection drops | Network instability | Check server logs; consider retry logic |
| OAuth loop never completes | Redirect URI mismatch | Verify OAuth configuration in `/mcp` |

---

## Configuring MCP Servers

MCP servers are configured in `.claude/settings.json` (project-level) or `~/.claude/settings.json` (user/global). Both files use the same `mcpServers` block:

```jsonc
// .claude/settings.json — project-level MCP servers
{
  "mcpServers": {
    // stdio server — local process
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-filesystem", "/path/to/allowed/dir"]
    },
    // URL-based server — remote HTTP service
    "context7": {
      "type": "url",
      "url": "https://mcp.context7.com/mcp"
    },
    // Server with custom environment variables
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-postgres", "postgresql://user:pass@localhost:5432/mydb"],
      "env": {
        "PGSSLMODE": "require"
      }
    }
  }
}
```

**Scope rules:**

| Location | Scope | Priority |
|----------|-------|----------|
| `~/.claude/settings.json` | All your projects (global) | Lower |
| `.claude/settings.json` | Current project only | Higher |
| `.claude/settings.local.json` | Current project, local-only (gitignored) | Highest |

Project-level servers override global ones with the same name. `settings.local.json` is for secrets and machine-specific paths — it's automatically gitignored.

### Security Notes on Environment Variables

Environment variables in `env` blocks are passed **only** to that specific server process. They are not available to other servers or to the main Claude Code process. This provides process-level isolation for secrets.

```jsonc
{
  "mcpServers": {
    "brave-search": {
      "env": {
        // This is ONLY available to brave-search. Other servers cannot read it.
        "BRAVE_API_KEY": "BSA-xxxxx"
      }
    }
  }
}
```

---

## Using the `/mcp` Command

The `/mcp` slash command provides an interactive interface for managing all MCP server connections:

```
/mcp                           # Open the MCP management UI
/mcp add <server-name>         # Add a new server
/mcp remove <server-name>      # Remove a server
/mcp list                      # List all connected servers
/mcp enable <server-name>      # Enable a previously disabled server
/mcp disable <server-name>     # Temporarily disable a server
```

**Interactive UI tabs:**
- **Connected** — shows active servers and their status (connected, error, disconnected)
- **Available** — browse installable MCP servers from registries
- **OAuth** — manage authentication tokens for remote servers

### Checking Server Health

```
/doctor
```

`/doctor` performs a comprehensive check of all MCP servers and reports connectivity, permission, and configuration issues.

---

## MCP Tools

Tools are the most important MCP primitive. They let Claude **perform actions** through the MCP server — run queries, navigate browsers, search the web, modify files, etc.

### How Tools Work

```
Claude decides to use a tool
         │
         ▼
Claude Code → MCP Server:  tools/call { name: "query", arguments: { sql: "SELECT ..." } }
         │
         ▼
MCP Server executes the tool (runs query, clicks button, reads file, etc.)
         │
         ▼
MCP Server → Claude Code:  { result: { content: [{ type: "text", text: "..." }] } }
         │
         ▼
Claude sees the result and continues the conversation
```

### Tool Naming Convention

In Claude Code, MCP tools appear with the naming pattern:

```
mcp__<server-name>__<tool-name>
```

For example:
- `mcp__postgres__query` — run a SQL query via the Postgres server
- `mcp__playwright__navigate` — navigate to a URL via Playwright
- `mcp__filesystem__read_file` — read a file via the Filesystem server

### Tool Annotations

Servers can provide annotations to help clients understand tool behavior:

| Annotation | Type | Meaning |
|-----------|------|---------|
| `readOnlyHint` | boolean | Tool does not modify state |
| `destructiveHint` | boolean | Tool may perform destructive operations |
| `idempotentHint` | boolean | Calling the tool multiple times with same args has same effect |
| `openWorldHint` | boolean | Tool interacts with external/"open world" entities |

```python
@server.tool(
    annotations={
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
async def get_weather(city: str) -> list[TextContent]:
    ...
```

Claude Code uses these hints for permission decisions — a destructive tool may require additional user confirmation.

### Structured Content in Tool Responses

Tools can return multiple content types in a single response:

```python
return [
    TextContent(type="text", text="Here's the screenshot:"),
    ImageContent(type="image", data=screenshot_b64, mimeType="image/png"),
    EmbeddedResource(type="resource", resource={
        "uri": "file:///project/output.json",
        "mimeType": "application/json",
        "text": json.dumps(result),
    }),
]
```

| Content Type | Use Case |
|-------------|----------|
| `TextContent` | Text output, JSON results, logs |
| `ImageContent` | Screenshots, charts, diagrams (base64) |
| `AudioContent` | Audio recordings, voice output (base64) |
| `EmbeddedResource` | Reference to a resource URI, inline data |

### Tool Execution Progress

For long operations, use the `report_progress` capability:

```python
@server.tool()
async def batch_process(items: list[str], ctx: Context) -> list[TextContent]:
    total = len(items)
    results = []
    for i, item in enumerate(items):
        result = await process_item(item)
        results.append(result)
        await ctx.report_progress(i + 1, total)
    return [TextContent(type="text", text=json.dumps(results))]
```

---

## MCP Resources

Resources are **read-only data** that MCP servers expose to Claude. Unlike tools (which Claude calls to perform actions), resources represent data the server makes available for Claude to read.

### What Resources Look Like

A resource is identified by a URI and has a MIME type:

```
file:///project/schema.sql          → text/plain
postgres://mydb/employees/table     → application/json
docs://api-reference/v2/users       → text/markdown
```

### Resource Templates

MCP servers can define **parameterized resource templates** using URI templates (RFC 6570):

```
postgres://{host}/{database}/{table}
file:///{path}
docs://{project}/{version}/{page}
```

This lets Claude discover what URI patterns are available and construct valid resource URIs on the fly.

```python
# Python SDK — resource template
@server.resource("config://app/{section}")
async def get_config_section(section: str) -> str:
    config = {
        "database": {"host": "localhost", "port": 5432},
        "cache": {"provider": "redis", "ttl": 3600},
    }
    return json.dumps(config.get(section, {}), indent=2)
```

### Resource Subscriptions

Some MCP servers support **resource subscriptions** — the server notifies the client when a resource changes:

```
Claude subscribes to: file:///var/log/app.log
Server sends: "updated" notification when new lines are appended
Claude re-reads the resource to get fresh content
```

**Server advertising subscription support:**
```json
{
  "capabilities": {
    "resources": {
      "subscribe": true,
      "listChanged": true
    }
  }
}
```

**Client subscribing to a resource:**
```json
{
  "jsonrpc": "2.0",
  "id": 20,
  "method": "resources/subscribe",
  "params": { "uri": "file:///var/log/app.log" }
}
```

**Server notification when resource changes:**
```json
{
  "jsonrpc": "2.0",
  "method": "notifications/resources/updated",
  "params": { "uri": "file:///var/log/app.log" }
}
```

### Resource Metadata

Servers describe each resource with metadata. Claude uses this to decide when a resource is relevant:

```jsonc
{
  "uri": "file:///project/docs/api.md",
  "name": "API Documentation",
  "description": "Complete REST API reference for the project",
  "mimeType": "text/markdown",
  "size": 24500  // bytes (optional)
}
```

---

## MCP Prompts

Prompts are **reusable templates** defined by MCP servers. They appear in Claude Code as:

1. **Slash commands** — `/mcp__<server>__<prompt-name>`
2. **Discoverable options** when you type `/` in the prompt

### How Prompt Templates Work

A prompt is defined by the server with arguments and default values:

```jsonc
// Server defines a prompt called "review-pr":
{
  "name": "review-pr",
  "description": "Review a GitHub pull request",
  "arguments": [
    {
      "name": "pr_number",
      "description": "The PR number to review",
      "required": true
    },
    {
      "name": "focus",
      "description": "What to focus on (security, performance, style)",
      "required": false
    }
  ]
}
```

When Claude invokes this prompt, the server returns the full prompt text with argument values substituted in.

### Prompts Can Include Embedded Resources

Prompts can include embedded resources for additional context:

```python
@server.prompt("review-with-schema")
async def review_with_schema(pr_number: str, table_name: str) -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"Review PR #{pr_number} considering this table schema:",
            },
        }],
        "resources": {
            "uri": f"postgres://mydb/public/{table_name}",
            "mimeType": "application/json",
        },
    }
```

### Why Use Prompts vs. Just Asking?

| Direct question | MCP prompt |
|----------------|------------|
| "Describe the users table" | `/mcp__postgres__describe-schema users` |
| Generic prompt, Claude guesses intent | Server provides structured, domain-specific instructions |
| No guarantee the right context is included | Server ensures schema details, conventions, and constraints are in the prompt |
| Works once | Reusable across team members and sessions |

---

## MCP Sampling

Sampling is the most advanced MCP primitive. It lets an MCP server **ask Claude to generate text** during a tool execution — essentially, a server-initiated LLM request.

### The Flow

```
Claude calls: mcp__myagent__analyze { file: "logs.txt" }
  │
  ▼
MCP Server processes the logs...
  │
  ├──► Server: "I need a summary of these 5 error patterns"
  │    Server calls: sampling/createMessage { messages: [...], maxTokens: 500 }
  │
  ▼
Claude (the model) generates: "The 5 errors are: 1) Connection timeout on DB..."
  │
  ▼
Server receives the LLM response, continues processing...
  │
  ├──► Server: "Now classify severity for each error"
  │    Server calls: sampling/createMessage again
  │
  ▼
Claude classifies...
  │
  ▼
Server finishes, returns final result to Claude Code
```

### Configuration

Sampling requires explicit permission because it allows MCP servers to consume your LLM tokens:

```jsonc
// .claude/settings.json
{
  "mcpServers": {
    "myagent": {
      "type": "stdio",
      "command": "node",
      "args": ["./my-agent-server.js"]
    }
  },
  "mcp__myagent__samplePermission": "allow"   // auto-allow sampling from this server
}
```

Without this permission, Claude Code will prompt you to approve each sampling request.

### Use Cases for Sampling

| Scenario | How sampling helps |
|----------|-------------------|
| **Multi-step analysis** | Server breaks a task into sub-tasks, asks Claude to handle each one |
| **Structured extraction** | Server extracts raw data, asks Claude to format/classify it |
| **Quality checks** | Server generates output, asks Claude to review and suggest improvements |
| **Agentic workflows** | Server acts as an orchestrator, delegating reasoning steps to Claude |

---

## Elicitation

Elicitation lets an MCP server **ask the user a question** during tool execution. Unlike sampling (which asks Claude), elicitation prompts the human user for input.

### The Flow

```
Claude calls: mcp__myapp__deploy { environment: "staging" }
  │
  ▼
MCP Server: "Need confirmation: deploy to staging with build #456?"
  │    Server requests elicitation
  ▼
User sees: "MCP 'myapp' asks: Proceed with staging deploy?"
  User responds: "Yes, but skip the migration step"
  │
  ▼
Server receives user's answer, continues deployment
  │
  ▼
Server finishes, returns result to Claude
```

### When Elicitation Makes Sense

- Confirmation before destructive operations (deploy, delete, charge)
- Clarifying ambiguous input mid-tool-execution
- Selecting from a list of options the server discovers at runtime

### Security Note

Elicitation is a powerful feature. Because it interrupts the user mid-task, it should be used sparingly and only when the user's input is genuinely required to proceed safely.

---

## Roots

Roots let MCP servers know **which directories and files are relevant** to the current project. The client (Claude Code) sends the list of project root directories to the server.

### The Flow

```
Client (Claude Code) → Server: "Here are your roots: /home/user/projects/myapp"
Server acknowledges roots
Server can now scope file operations to these directories
```

Roots are particularly useful for:
- **Filesystem MCP servers** — scope operations to project directories
- **Code analysis servers** — know which directories contain source code
- **Build tool servers** — find project configuration files

### Roots Changed Notification

When roots change (e.g., user switches projects), the client notifies all servers:

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/roots/list_changed"
}
```

The server then re-reads the roots list.

---

## Logging

MCP servers can send structured log messages to the client. This is the standard way for servers to report diagnostic information.

### Log Levels

| Level | Use Case |
|-------|----------|
| `debug` | Detailed diagnostic info |
| `info` | General operational messages |
| `notice` | Normal but significant events |
| `warning` | Potential issues that don't prevent operation |
| `error` | Errors that affect a specific operation |
| `critical` | Severe errors that may affect server health |
| `alert` | Immediate action required |
| `emergency` | System is unusable |

### Server → Client Log Notification

```json
{
  "jsonrpc": "2.0",
  "method": "notifications/message",
  "params": {
    "level": "warning",
    "logger": "postgres-connection",
    "data": "Connection pool at 90% capacity (45/50 connections)"
  }
}
```

### Python SDK Logging

```python
from mcp.server import Server

server = Server("my-server")

@server.tool()
async def my_tool(ctx: Context) -> list[TextContent]:
    await ctx.log(level="info", logger="my-tool", data="Starting processing...")
    # ... do work ...
    await ctx.log(level="info", logger="my-tool", data="Processing complete")
    return [TextContent(type="text", text="Done")]
```

Claude Code displays log messages in its debug output and writes them to `~/.claude/debug/<session>/mcp__<server>.log`.

---

## Completions

Completions let MCP servers provide **argument autocomplete suggestions** when Claude is filling in tool arguments.

### How It Works

```
Claude starts typing: mcp__postgres__query { "sql": "SELECT * FROM |
                                                              │
MCP Server suggests:      ← completions/complete request       │
  "users"                                                     │
  "orders"            (table names from the database)          │
  "products"                                                  │
```

### Server-Side Definition

```python
@server.tool()
async def query(sql: str) -> list[TextContent]:
    """Run a SQL query."""
    ...

@server.completion()
async def query_completions(
    ref: str,           # The argument name ("sql")
    argument: str,      # What the user has typed so far
    context: dict,      # Other argument values filled in so far
) -> list[str]:
    # Suggest table names after "FROM" or "JOIN"
    if "FROM" in argument.upper() or "JOIN" in argument.upper():
        tables = await get_table_names()
        return [
            table for table in tables
            if table.startswith(argument.split()[-1].strip("`\"'"))
        ]
    return []
```

Completions help Claude construct correct tool calls faster and reduce errors.

---

## MCP Hooks

Just like regular tool hooks, you can guard MCP tool calls with hooks in `.claude/settings.json`. MCP tools follow the naming pattern `mcp__<server>__<tool>` and hooks' matcher patterns apply to these names.

### Example: Block destructive database operations

```jsonc
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "mcp__postgres__query",
        "hooks": [
          {
            "type": "command",
            "command": "python hooks/block_destructive_sql.py"
          }
        ]
      }
    ]
  }
}
```

**`hooks/block_destructive_sql.py`:**

```python
import sys, json, re

data = json.load(sys.stdin)
sql = data.get("tool_input", {}).get("sql", "").upper()

# Block if the query modifies data without a WHERE clause
dangerous = [
    (r"DELETE\s+FROM\s+\w+\s*$", "DELETE without WHERE"),
    (r"UPDATE\s+\w+\s+SET\s+.*$", "UPDATE without WHERE — update a whole table?"),
    (r"DROP\s+TABLE", "DROP TABLE"),
    (r"TRUNCATE", "TRUNCATE"),
    (r"ALTER\s+TABLE.*DROP", "ALTER TABLE DROP"),
]

for pattern, reason in dangerous:
    if re.search(pattern, sql, re.IGNORECASE):
        print(f"Blocked: {reason}. Add a WHERE clause or review manually.")
        sys.exit(1)

sys.exit(0)
```

### Example: Rate-limit all MCP tool calls

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^mcp__",     // matches ALL MCP tools from any server
        "hooks": [
          {
            "type": "command",
            "command": "python hooks/mcp_rate_limit.py"
          }
        ]
      }
    ]
  }
}
```

### Example: Target a specific MCP server's tools

```jsonc
{
  "hooks": {
    "PreToolUse": [
      {
        // Only match GitHub MCP tools
        "matcher": "mcp__github__.*",
        "hooks": [
          {
            "type": "command",
            "command": "python hooks/github_audit.py"
          }
        ]
      }
    ]
  }
}
```

### Hook Context Variables

When a hook fires for an MCP tool, the following context is available:
- `tool_name` — full name like `mcp__postgres__query`
- `tool_input` — the arguments being passed to the tool
- `server_name` — derived from tool name, e.g. `postgres`

---

## MCP Dynamic Slash Commands

MCP servers that define **prompts** automatically expose them as slash commands in Claude Code. The naming pattern is:

```
/mcp__<server-name>__<prompt-name>
```

### How to Discover Available Commands

Type `/` alone at the prompt — Claude Code lists all available slash commands, including MCP dynamic ones:

```
/                          # shows all commands
/mcp                       # filters to MCP-related commands
/mcp__                     # shows all MCP server prompts
```

### Example: Postgres MCP prompts as slash commands

If the Postgres MCP server defines these prompts:
- `describe-schema` (with optional `table` argument)
- `explain-query` (with `sql` argument)
- `suggest-indexes` (with `table` argument)

They appear as:

```
/mcp__postgres__describe-schema users
/mcp__postgres__explain-query "SELECT * FROM orders WHERE status = 'pending'"
/mcp__postgres__suggest-indexes orders
```

---

## Popular MCP Servers

### Context7

**Purpose:** Provides up-to-date library documentation directly in Claude Code.

**Configuration:**
```jsonc
{
  "mcpServers": {
    "context7": {
      "type": "url",
      "url": "https://mcp.context7.com/mcp"
    }
  }
}
```

**Tools exposed:**
- `mcp__context7__resolve-library-id` — search for a library by name
- `mcp__context7__get-library-docs` — fetch documentation for a library

**Supported libraries:** React, Next.js, Tailwind, Vue, Svelte, Express, Prisma, Drizzle, Supabase, and thousands more across npm, PyPI, Maven, Go, and Rust.

### Playwright MCP

**Purpose:** Full browser automation — navigate pages, click buttons, fill forms, take screenshots.

**Configuration:**
```jsonc
{
  "mcpServers": {
    "playwright": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-playwright"]
    }
  }
}
```

**Tools:** `navigate`, `click`, `type`, `screenshot`, `evaluate`, `fill`, `select`, `hover`, `press`, `wait_for`

### Filesystem MCP

**Purpose:** Secure, scoped file system access within allowed directories.

```jsonc
{
  "mcpServers": {
    "filesystem": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-filesystem", "/home/user/projects"]
    }
  }
}
```

**Security model:** Only files within explicitly allowed directories are accessible. Path traversal is blocked.

### GitHub MCP

**Purpose:** Full GitHub API access — issues, PRs, repos, branches, files, search.

```jsonc
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxx" }
    }
  }
}
```

**Tools:** `create_issue`, `get_pr`, `list_issues`, `create_pr`, `merge_pr`, `search_code`, etc.

### Database MCP Servers

**Postgres:**
```jsonc
{
  "mcpServers": {
    "postgres": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-postgres",
               "postgresql://user:password@localhost:5432/myapp_db"]
    }
  }
}
```

**SQLite:**
```jsonc
{
  "mcpServers": {
    "sqlite": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-server-sqlite", "--db-path", "myapp.db"]
    }
  }
}
```

**Tools:** `query`, `list_tables`, `describe_table`, `explain`

### Brave Search MCP

**Purpose:** Web search capability via Brave Search API.

```jsonc
{
  "mcpServers": {
    "brave-search": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-brave-search"],
      "env": { "BRAVE_API_KEY": "BSA-xxxx" }
    }
  }
}
```

### Puppeteer MCP

**Purpose:** Chrome-specific browser automation. Similar to Playwright but Chrome-only.

### Memory MCP

**Purpose:** Persistent knowledge graph across Claude sessions.

```jsonc
{
  "mcpServers": {
    "memory": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-memory"]
    }
  }
}
```

**Tools:** `create_entities`, `create_relations`, `add_observations`, `read_graph`, `search_nodes`, `open_nodes`

### Sequential Thinking MCP

**Purpose:** Structured, multi-step reasoning for complex problems. Enables branching, revision, and hypothesis tracking.

### Fetch MCP

**Purpose:** Retrieve web page content as structured markdown text.

---

## Custom MCP Server Library

This section documents 15 production-ready MCP servers available in the `mcp_servers/` directory. Each server covers different MCP features, patterns, and use cases. **Every server can be installed and used directly in Claude Code.**

All servers files are located at: `mcp_servers/<name>.py`

### 1. Weather Server — External API Integration

**File:** `mcp_servers/weather_server.py`
**Demonstrates:** External API calls, response caching with TTL, structured error handling, parallel API requests
**Install:** `pip install mcp httpx`
**Env vars:** `OPENWEATHERMAP_API_KEY`

**Tools:**
| Tool | Description |
|------|-------------|
| `get_current_weather` | Current conditions by city name |
| `get_forecast` | 5-day forecast with daily summaries |
| `get_air_pollution` | Air quality index by city |
| `compare_cities` | Side-by-side weather comparison (parallel requests) |

**Configuration:**
```jsonc
{
  "mcpServers": {
    "weather": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/weather_server.py"],
      "env": { "OPENWEATHERMAP_API_KEY": "your-key-here" }
    }
  }
}
```

**Example usage:**
```
Claude calls: mcp__weather__compare_cities { "city_a": "Tokyo", "city_b": "London" }
→ returns side-by-side temperature, humidity, wind, and conditions for both cities
```

**Key pattern — response caching:**
```python
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 300  # seconds

def cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is None: return None
    ts, val = entry
    if time.time() - ts > CACHE_TTL:
        del _cache[key]; return None
    return val
```

### 2. File Converter Server — Binary Data & Image Processing

**File:** `mcp_servers/file_converter_server.py`
**Demonstrates:** Binary data handling (base64), image conversion between formats, EXIF extraction, batch processing, resource exposure of output files
**Install:** `pip install mcp pillow`
**Env vars:** `CONVERTER_OUTPUT_DIR`

**Tools:**
| Tool | Description |
|------|-------------|
| `image_convert` | Convert images between PNG/JPEG/WebP/BMP/GIF/TIFF |
| `image_resize` | Resize by dimensions or scale factor |
| `image_rotate` | Rotate images with expand option |
| `image_get_info` | Extract metadata, EXIF, color mode |
| `text_encode_decode` | Base64/Base32/Hex/URL/ROT13 encode or decode |
| `batch_process` | Process multiple images — thumbnails, dominant colors, grayscale |

**Key pattern — binary data with data URIs:**
```python
def _b64_to_bytes(b64: str) -> bytes:
    if "," in b64 and b64.startswith("data:"):
        b64 = b64.split(",", 1)[1]
    return base64.b64decode(b64)

def _bytes_to_b64(data: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(data).decode()
```

### 3. DevOps Server — Shell Commands & System Management

**File:** `mcp_servers/devops_server.py`
**Demonstrates:** Sandboxed shell command execution, path allowlisting, command blocking, process management, port scanning, log tailing
**Install:** `pip install mcp psutil`
**Env vars:** `DEVOPS_ALLOWED_DIRS`, `DEVOPS_BLOCKED_COMMANDS`

**Tools:**
| Tool | Description |
|------|-------------|
| `run_command` | Execute shell commands within allowed directories |
| `list_processes` | List running processes with optional name filter |
| `disk_usage` | Show disk usage for a directory |
| `system_info` | Comprehensive system information |
| `port_scan` | Scan TCP ports on a host |
| `log_tail` | Read last N lines of a log file with grep filter |
| `env_manager` | Get/set/list/delete environment variables |

**Key pattern — security sandboxing:**
```python
BLOCKED_COMMANDS = {"rm", "shutdown", "reboot", "mkfs", "dd", "chmod"}

def _is_command_safe(cmd: str) -> tuple[bool, str]:
    tokens = shlex.split(cmd)
    base = os.path.basename(tokens[0])
    if base in BLOCKED_COMMANDS:
        return False, f"Blocked command: {base}"
    if ".." in cmd:
        return False, "Path traversal detected"
    return True, "ok"
```

### 4. Data ETL Server — Data Transformation Pipelines

**File:** `mcp_servers/data_etl_server.py`
**Demonstrates:** Multi-format parsing (JSON, CSV, XML, YAML), data conversion, JSON Schema validation, JMESPath queries, data aggregation with multiple metrics, join/merge operations, mock data generation with templating
**Install:** `pip install mcp pyyaml jsonschema jmespath`

**Tools:**
| Tool | Description |
|------|-------------|
| `convert` | Convert between JSON, CSV, XML, YAML with auto-detection |
| `validate_schema` | Validate data against JSON Schema |
| `filter_transform` | Query data with JMESPath (like jq for JSON) |
| `aggregate` | Group-by with sum/avg/min/max/median/stdev metrics |
| `merge` | Join two datasets on a key (inner/left/right/outer) |
| `generate_mock_data` | Generate mock data from templates |
| `diff_data` | Compute set difference between two datasets |

**Key pattern — format auto-detection:**
```python
def _detect_format(text: str) -> str:
    text = text.strip()
    if text.startswith("{") or text.startswith("["): return "json"
    if text.startswith("<"): return "xml"
    if text.count(",") > 0 and text.count("\n") > 0: return "csv"
    if ":" in text.split("\n")[0]: return "yaml"
    return "unknown"
```

### 5. Notification Server — Desktop Notifications & Scheduling

**File:** `mcp_servers/notification_server.py`
**Demonstrates:** OS-level desktop notifications (Windows/Mac/Linux), scheduled and recurring notifications, countdown timers, background task scheduling with asyncio
**Install:** `pip install mcp`

**Tools:**
| Tool | Description |
|------|-------------|
| `send_notification` | Send immediate desktop notification |
| `schedule_notification` | Schedule a notification with optional recurring |
| `list_scheduled` | List all scheduled notifications |
| `cancel_notification` | Cancel a scheduled notification |
| `countdown_timer` | Run a countdown with progress and final alert |
| `remind_at` | Schedule a reminder at a specific ISO datetime |

**Key pattern — background scheduler:**
```python
async def _scheduler_loop():
    while True:
        await asyncio.sleep(5)
        now = datetime.now()
        for task_id, task in list(_tasks.items()):
            if now >= datetime.fromisoformat(task["fire_at"]):
                _send_os_notification(task["title"], task.get("body", ""))
                if task.get("recurring"):
                    task["fire_at"] = (now + timedelta(seconds=task["interval"])).isoformat()
                else:
                    del _tasks[task_id]
```

### 6. Code Analyzer Server — Code Metrics & Static Analysis

**File:** `mcp_servers/code_analyzer_server.py`
**Demonstrates:** AST parsing, cyclomatic complexity analysis, code pattern detection (security issues, TODOs, bare excepts), token counting, diff statistics, docstring generation
**Install:** `pip install mcp radon`

**Tools:**
| Tool | Description |
|------|-------------|
| `analyze_python` | Full analysis: functions, classes, complexity, imports |
| `analyze_complexity` | Cyclomatic complexity per function (radon) |
| `find_patterns` | Find security issues, TODOs, bare excepts, debug prints |
| `count_tokens` | Estimate token count for Claude or GPT models |
| `diff_stats` | Parse unified diffs for statistics |
| `generate_docstring` | Generate docstring templates (Google/NumPy/Sphinx) |

**Key pattern — AST visitor:**
```python
class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity: dict[str, int] = {}
        self.current_func: str | None = None

    def visit_FunctionDef(self, node):
        self.current_func = node.name
        self.complexity[node.name] = 1
        self.generic_visit(node)
        self.current_func = None

    def visit_If(self, node): self.complexity[self.current_func] += 1; self.generic_visit(node)
    def visit_While(self, node): self.complexity[self.current_func] += 1; self.generic_visit(node)
    def visit_For(self, node): self.complexity[self.current_func] += 1; self.generic_visit(node)
```

### 7. Search Aggregator Server — Multi-Source Search

**File:** `mcp_servers/search_aggregator_server.py`
**Demonstrates:** Multi-source parallel search (DuckDuckGo, Brave, SerpAPI), result deduplication, merge strategies (interleave/ranked), HTML content extraction, link scraping
**Install:** `pip install mcp httpx`
**Env vars:** `BRAVE_API_KEY`, `SERPAPI_KEY`

**Tools:**
| Tool | Description |
|------|-------------|
| `multi_search` | Parallel search across multiple engines |
| `fetch_page_content` | Fetch and extract readable text from a URL |
| `extract_links` | Extract all links from HTML |
| `summarize_results` | Search and create a synthesized summary |

**Key pattern — parallel with asyncio.gather:**
```python
tasks = [BACKENDS[src](query, count) for src in source_list]
all_results = await asyncio.gather(*tasks)
```

### 8. Secret Manager Server — Encryption & Credential Management

**File:** `mcp_servers/secret_manager_server.py`
**Demonstrates:** Encrypted vault storage, password generation, bcrypt hashing, key generation (Fernet/AES/RSA), TOTP code generation, encryption/decryption (Fernet/AES-GCM), checksums
**Install:** `pip install mcp cryptography`

**Tools:**
| Tool | Description |
|------|-------------|
| `generate_password` | Generate secure random passwords |
| `hash_password` | Hash with bcrypt/SHA-256/PBKDF2 |
| `generate_key` | Generate Fernet, AES, RSA, HMAC, or API keys |
| `vault_store` / `vault_get` / `vault_list` / `vault_delete` | Encrypted vault CRUD |
| `generate_totp` | TOTP code generation (RFC 6238) |
| `encrypt_decrypt` | Symmetric encrypt/decrypt (Fernet or AES-GCM) |
| `hash_checksum` | File or text checksums (MD5 through BLAKE2b) |

**Key pattern — TOTP implementation:**
```python
def _totp(secret_b32: str, interval: int = 30, digits: int = 6) -> str:
    key = base64.b32decode(secret_b32.upper())
    counter = int(time.time() // interval)
    counter_bytes = counter.to_bytes(8, "big")
    hmac_hash = hmac.new(key, counter_bytes, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0F
    code = (int.from_bytes(hmac_hash[offset:offset + 4], "big") & 0x7FFFFFFF) % (10 ** digits)
    return str(code).zfill(digits)
```

### 9. Monitoring Server — Metrics, Health Checks & Alerting

**File:** `mcp_servers/monitoring_server.py`
**Demonstrates:** System metrics collection (CPU, memory, disk, network), process monitoring, HTTP health checks, alert rule engine, port checking, metric snapshots over time
**Install:** `pip install mcp psutil`

**Tools:**
| Tool | Description |
|------|-------------|
| `system_metrics` | CPU, memory, disk, network, uptime |
| `process_top` | Top N processes by CPU or memory |
| `health_check` | HTTP health check with response time |
| `create_alert_rule` | Create alert with threshold and operator |
| `list_alerts` | Active rules and recent alert history |
| `check_port` | TCP port connectivity test |
| `monitor_snapshot` | Multiple metric snapshots over a time window |

### 10. Document Processor Server — Document Parsing & Text Analysis

**File:** `mcp_servers/document_processor_server.py`
**Demonstrates:** Multi-format document parsing (PDF, DOCX, HTML, Markdown), metadata extraction, text analysis (word frequency, readability scores, entity extraction), document comparison, chunking/splitting
**Install:** `pip install mcp PyPDF2 python-docx beautifulsoup4`

**Tools:**
| Tool | Description |
|------|-------------|
| `parse_document` | Parse and extract text from any supported format |
| `extract_metadata` | Extract author, dates, title, page count |
| `text_analysis` | Word frequency, readability, emails/URLs/names extraction |
| `markdown_convert` | Convert between HTML, Markdown, and plain text |
| `split_document` | Split into chunks by paragraph/sentence/header/size |
| `compare_documents` | Jaccard similarity and unified diff |

### 11. Image Processor Server — Image Manipulation & OCR

**File:** `mcp_servers/image_processor_server.py`
**Demonstrates:** Image info extraction, cropping, filters (grayscale/sepia/invert/blur/sharpen/emboss), dominant color extraction, placeholder generation, OCR text extraction, image collage creation
**Install:** `pip install mcp pillow pytesseract`

**Tools:**
| Tool | Description |
|------|-------------|
| `image_info` | Format, size, EXIF, color stats, transparency |
| `image_crop` | Crop to bounding box |
| `image_filters` | Apply 7 different visual filters |
| `extract_colors` | Dominant colors via histogram analysis |
| `create_placeholder` | Generate placeholder image with text overlay |
| `ocr_extract` | Tesseract OCR text extraction with word-level data |
| `create_collage` | Grid collage from multiple images |

### 12. Email Server — Email Composition & Templates

**File:** `mcp_servers/email_server.py`
**Demonstrates:** Email composition (MIME multipart), SMTP sending, email validation (format + disposable domain check), template system with variable substitution, dry-run mode for safety
**Install:** `pip install mcp`
**Env vars:** `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASS`

**Tools:**
| Tool | Description |
|------|-------------|
| `validate_email_address` | Format validation with disposable domain detection |
| `compose_email` | Compose MIME email for preview |
| `send_email` | Send via SMTP (with dry-run mode) |
| `create_template` | Create reusable template with `{{placeholders}}` |
| `render_template` | Fill template with values for preview |
| `list_templates` | List all saved templates |

### 13. Crypto Server — Cryptographic Operations

**File:** `mcp_servers/crypto_server.py`
**Demonstrates:** 10 hash algorithms, HMAC signing, symmetric encryption (Fernet/AES-GCM/ChaCha20), asymmetric key generation (RSA/Ed25519), digital signatures, JWT creation/verification, secure random generation
**Install:** `pip install mcp cryptography`

**Tools:**
| Tool | Description |
|------|-------------|
| `hash_text` | Hash with 10 algorithms (SHA256 through SHAKE-256) |
| `hmac_sign` | Generate HMAC with auto-keygen |
| `symmetric_encrypt` | Encrypt with Fernet, AES-GCM, or ChaCha20 |
| `symmetric_decrypt` | Decrypt with same algorithm |
| `asymmetric_keygen` | Generate RSA or Ed25519 key pairs |
| `sign_verify` | Sign messages or verify signatures |
| `jwt_token` | Create or verify JWTs (HS256/HS384/HS512) |
| `random_bytes` | Generate cryptographically secure random bytes |

### 14. Project Scaffolder Server — Project Generation

**File:** `mcp_servers/project_scaffolder_server.py`
**Demonstrates:** Template-based project generation, variable substitution with `{{placeholders}}`, multi-file tree creation, template preview without writing, custom template registration, MCP prompts for guided scaffolding, resource templates
**Install:** `pip install mcp`
**Env vars:** `SCAFFOLD_OUTPUT_DIR`

**Built-in templates:**
| Template | Language | Features |
|----------|----------|----------|
| `python-cli` | Python | argparse, pytest, setuptools, logging |
| `python-web` | Python/FastAPI | Routers, CORS middleware, health endpoint, httpx tests |
| `node-ts` | TypeScript | ESM, Vitest, ESLint, tsconfig |
| `docker-compose` | Docker | Multi-service stack, health checks, PostgreSQL, Redis |

**Tools:**
| Tool | Description |
|------|-------------|
| `list_project_templates` | Show all available templates |
| `generate_project` | Write all template files to disk |
| `preview_project` | Preview files without writing |
| `add_custom_template` | Register user-defined templates |

### 15. Calendar Server — Date/Time Operations

**File:** `mcp_servers/calendar_server.py`
**Demonstrates:** Date arithmetic (add/subtract days/weeks/months/years), recurring event generation with 15+ rule types, timezone conversion (zoneinfo), holiday lookup by country, calendar month generation, countdown calculation, ISO week numbers
**Install:** `pip install mcp python-dateutil holidays`

**Tools:**
| Tool | Description |
|------|-------------|
| `date_calc` | Date arithmetic with 9 operations |
| `date_diff` | Difference in days/weeks/months/years |
| `recurring_events` | Generate 15+ recurrence patterns |
| `timezone_convert` | Convert between any IANA timezone |
| `list_timezones` | List all available timezones |
| `holidays_lookup` | Public holidays by country/year |
| `calendar_month` | Structured calendar month view |
| `countdown` | Countdown with d/h/m/s breakdown |
| `week_number` | ISO week info for any date |

**Prompts:**
- `/mcp__calendar__schedule-meeting` — find optimal times across timezones
- `/mcp__calendar__event-planner` — plan recurring events with weekend detection

### 16. Sampling Demo Server — Server-Initiated LLM Requests

**File:** `mcp_servers/sampling_demo_server.py`
**Demonstrates:** The SAMPLING primitive — server-initiated LLM requests to Claude during tool execution. This is the most advanced MCP feature.
**Install:** `pip install mcp httpx`
**Config requires:** `"mcp__sampling-demo__samplePermission": "allow"` in settings.json

**Sampling use cases demonstrated:**

| # | Tool | Sampling Pattern | How Many Sampling Calls |
|---|------|-----------------|------------------------|
| 1 | `analyze_logs_with_sampling` | Multi-step: extract → classify → remediate → review | 3 (classification, synthesis, review) |
| 2 | `extract_and_structure` | Structured extraction: pre-process → extract → format | 1 (extraction) |
| 3 | `generate_with_review` | Quality loop: generate → review → revise (iterative) | 2N+1 (generate + N review cycles) |
| 4 | `decision_matrix` | Orchestration: score → weight → rank | 2 (scoring, ranking) |
| 5 | `batch_classify` | Classification: validate → classify | 1 (classification) |

**Key pattern — server.request_sampling():**
```python
# The server initiates an LLM request to Claude during tool execution
from mcp.types import CreateMessageRequestParams, ContentBlock

classification_request = CreateMessageRequestParams(
    messages=[{
        "role": "user",
        "content": ContentBlock(
            type="text",
            text="Classify these error patterns: ...",
        ),
    }],
    maxTokens=2000,
    systemPrompt="You are an expert SRE analyzing error logs.",
)

# This pauses the tool, Claude generates a response, then the tool continues
response = await server.request_sampling(classification_request)
claude_answer = response.content[0].text
```

**Prompts:**
- `/mcp__sampling-demo__sampling-explorer` — interactive guide to all 5 sampling patterns

### 17. HTTP Team Dashboard Server — Remote/HTTP Transport

**File:** `mcp_servers/http_team_server.py`
**Demonstrates:** HTTP/SSE transport (NOT stdio) — the server runs as a standalone HTTP service accessible by multiple Claude Code instances simultaneously. This is the **remote server** pattern.
**Install:** `pip install mcp uvicorn starlette`
**Run:** `python mcp_servers/http_team_server.py --port 9020`

**Key difference from stdio servers:**

| Aspect | stdio (all other servers) | HTTP (this server) |
|--------|--------------------------|---------------------|
| **Transport** | stdin/stdout pipe | HTTP + SSE (Server-Sent Events) |
| **Process** | Child process of Claude Code | Standalone daemon/service |
| **Access** | Local only, one client | Remote, multiple clients concurrently |
| **Config** | `"type": "stdio"` | `"type": "url"` |
| **Startup** | Automatic (Claude Code spawns it) | Manual (you run it separately) |
| **Shared state** | Per-process (isolated) | Shared across all connections |

**Configuration:**
```jsonc
{
  "mcpServers": {
    "team-dashboard": {
      "type": "url",
      "url": "http://localhost:9020/mcp"
    }
  }
}
```

**For team deployment:**
```jsonc
{
  "mcpServers": {
    "team-dashboard": {
      "type": "url",
      "url": "https://mcp.internal.company.com/mcp",
      "auth": "oauth"
    }
  }
}
```

**Tools:**
| Tool | Description |
|------|-------------|
| `team_announce` | Post announcement visible to all connected Claude instances |
| `get_team_activity` | Read recent team activity, deployments, and client count |
| `record_deployment` | Record a deployment event (started/completed/failed/rolled_back) |
| `manage_feature_flags` | CRUD + toggle shared feature flags |
| `oncall_status` | Check/set on-call schedule by week |

**Prompts:**
- `/mcp__team-dashboard__standup-report` — generate standup from team activity
- `/mcp__team-dashboard__deploy-coordination` — coordinate a production deployment

### Coverage Summary

| Primitive | Servers with it | Highlights |
|-----------|----------------|------------|
| **Tools** | 17/17 servers | ~120 tools total across all servers |
| **Resources** | 17/17 servers | 26 resources: static, parameterized templates (`{id}`, `{name}`, `{path}`), subscription-ready |
| **Prompts** | 14/17 servers | 17 prompts: code review, travel planning, meeting scheduler, data pipeline design, security checklist, email campaigns, image editing workflows, standup reports, deployment coordination, and more |
| **Sampling** | 1 dedicated server | 5 distinct patterns: multi-step analysis, structured extraction, quality review loop, decision matrix, batch classification |
| **HTTP transport** | 1 dedicated server | SSE-based remote server with multi-client shared state |

---

## Building Your Own MCP Server

MCP servers can be written in any language. The Python and TypeScript SDKs are the most mature.

### Minimal TypeScript MCP Server

```typescript
// server.ts — a minimal MCP server that exposes one tool
import { McpServer } from "@anthropic/mcp";
import { StdioServerTransport } from "@anthropic/mcp/stdio";

// 1. Create the server with metadata
const server = new McpServer({
  name: "my-first-server",
  version: "1.0.0",
});

// 2. Register a tool
server.tool(
  "greet",                              // tool name
  "Greets a person by name",            // description (Claude reads this to decide when to use)
  {
    // parameter schema (JSON Schema)
    name: { type: "string", description: "The name of the person to greet" },
    language: {
      type: "string",
      enum: ["en", "es", "fr", "de"],
      description: "Language for the greeting",
      default: "en",
    },
  },
  async ({ name, language }) => {
    // The tool implementation
    const greetings: Record<string, string> = {
      en: `Hello, ${name}!`,
      es: `Hola, ${name}!`,
      fr: `Bonjour, ${name}!`,
      de: `Hallo, ${name}!`,
    };

    return {
      content: [{ type: "text", text: greetings[language] }],
    };
  }
);

// 3. Connect and start listening
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Adding Resources

```typescript
// Static resource
server.resource(
  "config://app",
  "Application Config",
  "text/json",
  async () => ({
    contents: [{
      uri: "config://app",
      mimeType: "text/json",
      text: JSON.stringify({ version: "2.3.0", debug: false }, null, 2),
    }],
  })
);

// Parameterized resource template
server.resource(
  "config://app/{section}",
  "Config Section",
  "text/json",
  async ({ section }) => {
    const config: Record<string, any> = {
      database: { host: "localhost", port: 5432 },
      cache: { provider: "redis", ttl: 3600 },
    };
    return {
      contents: [{
        uri: `config://app/${section}`,
        mimeType: "text/json",
        text: JSON.stringify(config[section] || {}, null, 2),
      }],
    };
  }
);
```

### Adding Prompts

```typescript
server.prompt(
  "code-review",
  "Review code with a specific focus area",
  {
    language: { type: "string", description: "Programming language", required: true },
    focus: {
      type: "string",
      enum: ["security", "performance", "style", "architecture"],
      default: "style",
    },
  },
  ({ language, focus }) => ({
    messages: [{
      role: "user",
      content: {
        type: "text",
        text: `You are a code reviewer specializing in ${language} ${focus}.
Please review the following code carefully.`,
      },
    }],
  })
);
```

### Minimal Python MCP Server

```python
# server.py — a minimal MCP server in Python
from mcp.server import Server, StdioServerTransport
from mcp.types import Tool, TextContent

# 1. Create the server
server = Server("my-python-server")

# 2. Register a tool using a decorator
@server.tool()
async def add(a: float, b: float) -> list[TextContent]:
    """Add two numbers together and return the result."""
    result = a + b
    return [TextContent(type="text", text=f"{a} + {b} = {result}")]

# 3. Register a resource
@server.resource("stats://server")
async def get_stats() -> str:
    """Return current server statistics."""
    return json.dumps({
        "uptime_seconds": 86400,
        "requests_handled": 1543,
    })

# 4. Start listening
if __name__ == "__main__":
    transport = StdioServerTransport()
    asyncio.run(server.run(transport))
```

### Adding Logging to Your Server

```python
@server.tool()
async def my_tool(path: str, ctx: Context) -> list[TextContent]:
    await ctx.log(level="info", logger="my-tool", data=f"Processing {path}")
    try:
        result = process(path)
    except Exception as e:
        await ctx.log(level="error", logger="my-tool", data=str(e))
        raise
    await ctx.log(level="info", logger="my-tool", data="Done")
    return [TextContent(type="text", text=result)]
```

### Adding Progress Reporting

```python
@server.tool()
async def export_data(format: str, ctx: Context) -> list[TextContent]:
    rows = fetch_all_rows()
    total = len(rows)
    for i, row in enumerate(rows):
        if i % 50 == 0:
            await ctx.report_progress(
                progress=i,
                total=total,
                message=f"Processing row {i}/{total}",
            )
    return [TextContent(type="text", text=format_output(rows))]
```

### Adding Completions

```python
@server.completion()
async def format_completion(
    ref: str,
    argument: str,
    context: dict,
) -> list[str]:
    """Suggest completions for the 'format' argument."""
    formats = ["json", "csv", "yaml", "xml", "parquet"]
    return [f for f in formats if f.startswith(argument.lower())]
```

### Adding Elicitation

```python
@server.tool()
async def deploy(environment: str, ctx: Context) -> list[TextContent]:
    # Ask the user for confirmation
    response = await ctx.elicit(
        message=f"Deploy to {environment}?",
        options=["Yes, deploy now", "No, abort", "Preview changes first"],
    )
    if response == "No, abort":
        return [TextContent(type="text", text="Deployment cancelled")]
    if response == "Preview changes first":
        diff = get_deployment_diff(environment)
        return [TextContent(type="text", text=f"Preview:\n{diff}")]

    # Proceed with deployment
    result = perform_deploy(environment)
    return [TextContent(type="text", text=f"Deployed: {result}")]
```

### Choosing Transport: stdio vs HTTP

When building a server, your first decision is the transport. Here's how to choose:

```
┌──────────────────────────────────────────────────────────────┐
│                    MCP Transport Decision                      │
├──────────────┬─────────────────────┬─────────────────────────┤
│              │       stdio          │      HTTP / SSE         │
├──────────────┼─────────────────────┼─────────────────────────┤
│ How it works │ Child process,      │ Standalone HTTP server  │
│              │ stdin/stdout pipe   │ SSE for server→client   │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Startup      │ Automatic (Claude   │ Manual (you start it)   │
│              │ Code spawns it)     │                          │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Clients      │ 1:1 (one per Claude │ 1:N (multiple Claude     │
│              │ Code instance)      │ instances can connect)   │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Sharing      │ Isolated per user   │ Shared across team       │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Latency      │ ~0ms (no network)   │ ~1-50ms (network)       │
├──────────────┼─────────────────────┼─────────────────────────┤
│ State        │ Per-process, fresh  │ Shared, persists across  │
│              │ each startup        │ restarts if designed so  │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Auth         │ Process isolation   │ OAuth, API keys, mTLS   │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Use when...  │ Personal tools,     │ Team dashboards, shared │
│              │ local operations,   │ services, deployments,  │
│              │ no sharing needed   │ multi-user coordination │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Config       │ "type": "stdio",    │ "type": "url",          │
│              │ "command": "python" │ "url": "http://..."    │
├──────────────┼─────────────────────┼─────────────────────────┤
│ Example      │ weather_server.py,  │ http_team_server.py     │
│ servers      │ crypto_server.py... │                         │
└──────────────┴─────────────────────┴─────────────────────────┘
```

**stdio server template (Python):**
```python
from mcp.server import Server
from mcp.server.stdio import StdioServerTransport

server = Server("my-server")

@server.tool()
async def my_tool(arg: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"Result: {arg}")]

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
```

**HTTP/SSE server template (Python):**
```python
from mcp.server import Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

server = Server("my-server")

@server.tool()
async def my_tool(arg: str) -> list[TextContent]:
    return [TextContent(type="text", text=f"Result: {arg}")]

async def handle_mcp(request):
    transport = SseServerTransport("/mcp/messages")
    async with transport.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(streams[0], streams[1],
                         server.create_initialization_options())

app = Starlette(routes=[
    Route("/mcp", handle_mcp, methods=["GET"]),
])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9020)
```

---

## Debugging MCP Servers

### 1. Check Server Status with `/doctor`

```
/doctor
```

`/doctor` checks all configured MCP servers and reports:
- Whether the server process is running
- Whether the connection succeeded
- Any configuration errors (wrong command path, missing env vars, etc.)

### 2. Check Server Logs

MCP server logs are stored alongside Claude Code's debug logs:

```
~/.claude/debug/<session-id>/
  ├── mcp__postgres.log        ← Postgres server stdout/stderr
  ├── mcp__playwright.log      ← Playwright server stdout/stderr
  └── ...
```

Enable debug mode first:

```
/debug MCP server connection issues
```

### 3. Common Issues and Fixes

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Server shows "disconnected" in `/mcp` | Wrong binary path or server not installed | Run the `command` manually in terminal to test |
| Tools don't appear in autocomplete | Server started but handshake failed | Check server logs for JSON-RPC errors |
| "Permission denied" on tool calls | Permission mode blocks MCP tools | `/permissions` → allow `mcp__<server>__*` |
| OAuth loop never completes | Redirect URI mismatch | Check server OAuth config; use `/mcp` → OAuth tab |
| Server exits immediately | Missing dependency or bad args | Run the exact command from settings.json manually |
| High latency on remote server | Network or server overload | Use stdio servers when possible; set timeouts |

### 4. Verify a Server Connection Manually

For stdio servers, test the server process directly:

```bash
# Test if the command runs at all
npx -y @anthropic/mcp-server-filesystem --help

# Test JSON-RPC communication (send initialize request)
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | \
  npx -y @anthropic/mcp-server-filesystem /tmp
```

For Python servers:

```bash
# Test Python server
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python mcp_servers/weather_server.py
```

### 5. Environment Variable Debugging

To verify env vars are being passed correctly:
1. Enable debug mode with `/debug MCP`
2. Check the server log file for startup messages that show env var values
3. You can also use the `env_manager` tool from the devops server to verify

---

## MCP Server Best Practices

### 1. Tool Description Quality

Write tool descriptions that help Claude decide **when** to use them. Be specific about the tool's purpose:

```python
# Good — Claude knows exactly when to use this
@server.tool()
async def get_weather_forecast(city: str, days: int = 5) -> list[TextContent]:
    """Get a multi-day weather forecast for a city by name.

    Use this to answer questions about upcoming weather, plan outdoor
    activities, or compare weather across dates. Returns temperature
    highs/lows, humidity, and conditions for each day.

    Args:
        city: City name, e.g. "San Francisco" or "Tokyo"
        days: Number of days 1-5. Default 5.
    """

# Bad — vague, no context
@server.tool()
async def f(c: str) -> list[TextContent]:
    """Get forecast."""
```

### 2. Parameter Design

- **Use clear names:** `city` not `c`, `timeout_seconds` not `ts`
- **Provide defaults** for optional parameters
- **Use enums** when only specific values are valid
- **Add description to every parameter**

```python
@server.tool()
async def search(
    query: str,                              # Required — no default
    limit: int = 10,                         # Optional with sensible default
    sort: str = "relevance",                 # Will use enum
    include_preview: bool = True,            # Boolean flags
) -> list[TextContent]:
    """Search with parameters that are self-documenting."""
```

### 3. Error Messages

Make errors **actionable** for Claude:

```python
# Good — Claude can fix the problem
raise ValueError(
    f"Unknown format: '{format}'. Supported formats: json, csv, yaml, xml"
)

# Bad — Claude doesn't know how to recover
raise ValueError("Invalid format")
```

### 4. Idempotency

Design tools to be safe when called multiple times:
- Read-only tools (`readOnlyHint: true`) can be retried safely
- Destructive tools should check state before acting (e.g., "delete if exists")
- Idempotent tools (`idempotentHint: true`) produce the same result when called again

### 5. Response Size

Keep tool responses focused:
- Return summaries for large datasets; offer detailed tools for drill-down
- Truncate very long text (10K-50K chars) with a note about how to get more
- For binary data, use base64 in manageable chunks

### 6. Startup & Validation

Validate configuration at startup:

```python
async def main():
    # Validate env vars
    if not os.environ.get("API_KEY"):
        print("WARNING: API_KEY not set — some tools will fail", file=sys.stderr)

    # Validate dependencies
    try:
        import optional_dependency
    except ImportError:
        print("WARNING: optional_dependency not installed", file=sys.stderr)

    transport = StdioServerTransport()
    await server.run(transport)
```

---

## Testing MCP Servers

### Unit Testing Tools

```python
# test_weather_server.py
import pytest
import json
import asyncio
from weather_server import server

@pytest.mark.asyncio
async def test_get_current_weather():
    """Test that the tool returns valid JSON with expected fields."""
    result = await server.call_tool(
        "get_current_weather",
        {"city": "London", "units": "metric"}
    )
    assert len(result) == 1
    data = json.loads(result[0].text)
    assert "temperature" in data
    assert "humidity_pct" in data
    assert "city" in data
```

### Testing with JSON-RPC over stdio

```bash
# Test tools/list
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | \
  python mcp_servers/weather_server.py

# Test a specific tool call
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"hash_text","arguments":{"text":"hello","algorithm":"sha256"}}}' | \
  python mcp_servers/crypto_server.py
```

### Testing the Full Lifecycle

```bash
# Full lifecycle test script
#!/bin/bash
# Send initialize
echo '{"jsonrpc":"2.0","id":0,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
sleep 0.1
# Send initialized
echo '{"jsonrpc":"2.0","method":"notifications/initialized"}'
sleep 0.1
# List tools
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
sleep 0.1
# Call a tool
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"hash_text","arguments":{"text":"test","algorithm":"sha256"}}}'
sleep 0.1
# Shutdown
echo '{"jsonrpc":"2.0","id":3,"method":"shutdown","params":{}}'
```

---

## Security Considerations

### 1. stdio Server Security

- **Process isolation:** Each stdio server runs as a separate process with its own memory space
- **Environment isolation:** `env` vars in config are only available to that server
- **No network exposure:** stdio servers have no network interface — they only talk to the MCP client

### 2. Path Traversal Prevention

Always validate paths against an allowlist:

```python
def _is_path_allowed(target: str, allowed_dirs: list[Path]) -> bool:
    p = Path(target).resolve()
    return any(
        str(p).startswith(str(allowed.resolve()))
        for allowed in allowed_dirs
    )
```

### 3. Command Injection Prevention

- Use `shlex.split()` to parse commands safely
- Maintain a blocklist of dangerous commands
- Never pass unsanitized user input directly to shell

### 4. Secret Handling

- Store secrets in environment variables, never in source code
- Use `.claude/settings.local.json` (gitignored) for API keys
- Use encrypted vaults for at-rest secret storage (see Secret Manager server)
- Rotate credentials regularly

### 5. Rate Limiting

Protect external APIs by implementing:
- In-memory caches with TTL
- Request deduplication
- Exponential backoff for retries

```python
@server.tool()
async def rate_limited_tool(query: str) -> list[TextContent]:
    cache_key = f"rl:{hashlib.md5(query.encode()).hexdigest()}"
    if cache_key in _rate_limit_cache:
        last_call = _rate_limit_cache[cache_key]
        if time.time() - last_call < 1.0:  # 1 second minimum interval
            raise ValueError("Rate limited. Please wait before retrying.")
    _rate_limit_cache[cache_key] = time.time()
    # ... proceed with call
```

### 6. Authentication & Authorization

- Use OAuth for remote MCP servers (see OAuth section)
- For custom servers, validate API keys at startup
- Consider read-only database users for MCP connections (see Database MCP Servers section)
- Use hooks to add authorization layers for sensitive tool calls

---

## Performance Optimization

### 1. Caching Strategies

| Strategy | When to use | Example |
|----------|------------|---------|
| **In-memory TTL cache** | External API calls, DB queries that change infrequently | Weather server's `_cache` dict |
| **Result deduplication** | Multi-source queries with overlapping results | Search aggregator's `_deduplicate()` |
| **Connection pooling** | Database servers | Use connection pool libraries |

### 2. Parallelism

```python
# Good: parallel independent requests
results = await asyncio.gather(
    _search_source_a(query),
    _search_source_b(query),
    _search_source_c(query),
)

# Bad: sequential
a = await _search_source_a(query)
b = await _search_source_b(query)
c = await _search_source_c(query)
```

### 3. Response Optimization

- Compress large text responses (summarize, truncate with cursor)
- For images, use appropriate compression (JPEG quality 80-85, PNG for sharp edges)
- Batch multiple operations into single tool calls when possible

### 4. Tool List Size

Servers with many tools (>20) should consider:
- Grouping related operations into single tools with an `operation` parameter
- Using resource templates instead of individual resources
- Providing clear, searchable tool descriptions

---

## Deployment Strategies

### 1. Personal Development Server

```jsonc
// .claude/settings.local.json
{
  "mcpServers": {
    "my-server": {
      "type": "stdio",
      "command": "python",
      "args": ["./mcp_servers/my_server.py"]
    }
  }
}
```

### 2. Team Shared Server (Internal HTTP)

```jsonc
// .claude/settings.json (committed to repo)
{
  "mcpServers": {
    "team-tools": {
      "type": "url",
      "url": "https://mcp.internal.company.com/api"
    }
  }
}
```

### 3. Published npm/PyPI Package

```jsonc
{
  "mcpServers": {
    "published-server": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@scope/mcp-server-name", "--config", "./config.json"]
    }
  }
}
```

### 4. Docker Container

```jsonc
{
  "mcpServers": {
    "containerized": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "-i", "--rm", "my-mcp-server:latest"]
    }
  }
}
```

### 5. Custom uvx/Python Package

```jsonc
{
  "mcpServers": {
    "python-server": {
      "type": "stdio",
      "command": "uvx",
      "args": ["my-published-mcp-server", "--option", "value"]
    }
  }
}
```

### Deployment Checklist

| Step | Detail |
|------|--------|
| **Test locally** | Verify with `/doctor` and manual tool calls |
| **Validate startup** | Server should start in <5s |
| **Check permissions** | Tools should respect `readOnlyHint`/`destructiveHint` |
| **Error gracefully** | Missing env vars should produce clear error messages |
| **Log to stderr** | stdout is for JSON-RPC only |
| **Version your server** | Use semantic versioning; include version in initialize response |
| **Document tools** | Include clear descriptions for every tool and parameter |

---

## Quick Reference

### MCP Primitive Cheat Sheet

```
┌──────────┬──────────────────┬────────────────────────────────┐
│ Primitive│ Direction        │ Claude Code integration         │
├──────────┼──────────────────┼────────────────────────────────┤
│ Tools    │ Client → Server  │ mcp__<server>__<tool>          │
│ Resources│ Server → Client  │ Auto-read when relevant          │
│ Prompts  │ Server → Client  │ /mcp__<server>__<prompt>       │
│ Sampling │ Server → Client  │ Permission-controlled LLM calls │
└──────────┴──────────────────┴────────────────────────────────┘
```

### All MCP Methods (JSON-RPC)

**Client → Server:**
| Method | Purpose |
|--------|---------|
| `initialize` | Start connection, exchange capabilities |
| `ping` | Heartbeat / connection check |
| `tools/list` | Discover available tools |
| `tools/call` | Execute a tool |
| `resources/list` | List available resources |
| `resources/read` | Read a resource by URI |
| `resources/templates/list` | List parameterized resource templates |
| `resources/subscribe` | Subscribe to resource updates |
| `resources/unsubscribe` | Unsubscribe from resource updates |
| `prompts/list` | List available prompts |
| `prompts/get` | Get a rendered prompt |
| `completion/complete` | Request argument autocomplete |
| `shutdown` | Graceful shutdown |

**Server → Client:**
| Method | Purpose |
|--------|---------|
| `notifications/initialized` | Sent by client to complete handshake |
| `notifications/progress` | Tool execution progress |
| `notifications/cancelled` | Cancel an in-progress request |
| `notifications/message` | Log message from server |
| `notifications/resources/updated` | Resource content changed |
| `notifications/resources/list_changed` | Resource list changed |
| `notifications/tools/list_changed` | Tool list changed |
| `notifications/prompts/list_changed` | Prompt list changed |
| `notifications/roots/list_changed` | Project roots changed |
| `sampling/createMessage` | Server asks Claude to generate text |
| `elicitation/create` | Server asks user a question |

### Popular MCP Servers at a Glance

| Server | Command | Key Use Case |
|--------|---------|-------------|
| **Context7** | URL-based | Up-to-date library documentation |
| **Playwright** | `npx @anthropic/mcp-server-playwright` | Browser automation & testing |
| **Puppeteer** | `npx @anthropic/mcp-server-puppeteer` | Chrome-specific automation |
| **Filesystem** | `npx @anthropic/mcp-server-filesystem <path>` | Scoped file operations |
| **GitHub** | `npx @anthropic/mcp-server-github` | PRs, issues, repo management |
| **Postgres** | `npx @anthropic/mcp-server-postgres <url>` | Database queries & schema exploration |
| **SQLite** | `uvx mcp-server-sqlite --db-path <path>` | Local database access |
| **Brave Search** | `npx @anthropic/mcp-server-brave-search` | Web search with API key |
| **Memory** | `npx @anthropic/mcp-server-memory` | Cross-session knowledge graph |
| **Sequential Thinking** | `npx @anthropic/mcp-server-sequential-thinking` | Structured multi-step reasoning |
| **Fetch** | `uvx mcp-server-fetch` | Retrieve web page content |

### Custom MCP Servers (Python Library)

| Server | File | Transport | Key Features Demonstrated |
|--------|------|-----------|--------------------------|
| **Weather** | `weather_server.py` | stdio | External APIs, TTL caching, parallel requests, prompt |
| **File Converter** | `file_converter_server.py` | stdio | Binary data, image formats, batch processing |
| **DevOps** | `devops_server.py` | stdio | Shell sandboxing, process mgmt, port scanning |
| **Data ETL** | `data_etl_server.py` | stdio | Multi-format, schema validation, aggregation, parameterized resources, prompt |
| **Notification** | `notification_server.py` | stdio | Desktop alerts, scheduling, background tasks, prompt |
| **Code Analyzer** | `code_analyzer_server.py` | stdio | AST parsing, complexity, pattern detection, code review prompt |
| **Search Aggregator** | `search_aggregator_server.py` | stdio | Multi-source search, dedup, merge strategies |
| **Secret Manager** | `secret_manager_server.py` | stdio | Encryption, vault, TOTP, key generation, prompt |
| **Monitoring** | `monitoring_server.py` | stdio | System metrics, health checks, alerting, 2 prompts, subscription-ready resource |
| **Document Processor** | `document_processor_server.py` | stdio | PDF/DOCX/HTML parsing, text analysis, parameterized resource, prompt |
| **Image Processor** | `image_processor_server.py` | stdio | Image filters, OCR, color extraction, editing workflow prompt |
| **Email** | `email_server.py` | stdio | MIME composition, SMTP, templates, parameterized resource, prompt |
| **Crypto** | `crypto_server.py` | stdio | Hashing, encryption, JWT, signatures, security checklist prompt |
| **Project Scaffolder** | `project_scaffolder_server.py` | stdio | Template generation, multi-file output, parameterized resources, prompt |
| **Calendar** | `calendar_server.py` | stdio | Date arithmetic, recurrence, timezones, 2 prompts, parameterized resource |
| **Sampling Demo** | `sampling_demo_server.py` | stdio | **SAMPLING** — 5 patterns for server→Claude LLM requests, prompt |
| **HTTP Team Dashboard** | `http_team_server.py` | **HTTP/SSE** | **HTTP transport** — remote, multi-client, shared state, 2 prompts |

### Configuration Quick Reference

```jsonc
// All configuration lives in .claude/settings.json or ~/.claude/settings.json
{
  "mcpServers": {
    // Local stdio server with args and env
    "my-server": {
      "type": "stdio",
      "command": "npx",                              // or node, python, uvx, /path/to/binary
      "args": ["-y", "@scope/mcp-server-name", "--flag", "value"],
      "env": { "API_KEY": "xxx" }                    // env vars for the server process
    },
    // Remote HTTP server
    "remote-server": {
      "type": "url",
      "url": "https://mcp.example.com/api"
    },
    // Remote server with OAuth
    "auth-server": {
      "type": "url",
      "url": "https://mcp.example.com/api",
      "auth": "oauth"
    }
  },
  // Auto-allow sampling from a server
  "mcp__myagent__samplePermission": "allow"
}
```

### Essential Commands

```
/mcp                        # Open MCP management UI
/mcp add <name>             # Add and configure a new server
/mcp remove <name>          # Remove a server
/mcp list                   # List all connected servers
/mcp enable <name>          # Enable a disabled server
/mcp disable <name>         # Temporarily disable without removing
/doctor                     # Check MCP server health
/debug MCP issues           # Enable debug logging for MCP
```

### Transport Decision Guide

```
Is the tool...
  ├── A local program/script that runs on your machine?
  │     → stdio  (fastest, simplest)
  │
  ├── A shared team service running on internal infrastructure?
  │     → url (SSE/HTTP)
  │
  ├── A SaaS/cloud MCP service?
  │     → url + OAuth
  │
  └── Something only you use, with filesystem access needed?
        → stdio  (no network overhead)
```

### MCP Server Development Checklist

| Step | Detail |
|------|--------|
| **Name & version** | Use semantic versioning; name clearly describes what the server does |
| **Tool descriptions** | Write descriptions Claude can understand — be specific about when to use each tool |
| **Parameter schemas** | Use JSON Schema with clear `description` fields — Claude reads these to construct correct arguments |
| **Tool annotations** | Set `readOnlyHint`, `destructiveHint`, `idempotentHint` accurately |
| **Error handling** | Return structured, actionable errors. Claude reads error messages and may retry |
| **Logging** | Write to stderr (it goes to debug logs). stdout is for JSON-RPC only |
| **Startup validation** | Check env vars and dependencies at startup. Log warnings, don't crash silently |
| **Testing** | Test with `echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' \| your-server` |
| **Packaging** | Publish as an npm/PyPI package so others can use it with `npx` or `uvx` |
| **Documentation** | Document each tool, required env vars, and configuration example |
| **Caching** | Add TTL caches for external API calls to reduce latency and stay within rate limits |
| **Security** | Validate paths against allowlists, use shlex for commands, never trust user input |

---

> **Start here:** Read the [Quick Reference](#quick-reference), configure one MCP server from the [Popular servers](#popular-mcp-servers) section, verify with `/doctor`, and try using it in a conversation. Then explore the [Custom MCP Server Library](#custom-mcp-server-library) for patterns you can adapt for your own servers.
