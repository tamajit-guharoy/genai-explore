# Graphiti MCP Server

A comprehensive guide to setting up and using the Graphiti Model Context Protocol (MCP) server. This server exposes Graphiti's temporal knowledge graph capabilities as MCP tools, allowing Claude Desktop and other MCP-compatible clients to interact with your knowledge graph.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Claude Desktop Configuration](#claude-desktop-configuration)
- [Available MCP Tools](#available-mcp-tools)
- [Transport Options](#transport-options)
- [Example Workflow](#example-workflow)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python      | 3.10+   | Tested with 3.10--3.12 |
| Neo4j       | 5.x     | Community or Enterprise edition |
| OpenAI API  | --      | API key with access to GPT-4 or GPT-4o |
| Claude Desktop | Latest | Or any MCP-compatible client |

---

## Installation

### 1. Install graphiti-core

```bash
pip install graphiti-core
```

This installs the core library along with the MCP server entry point.

### 2. Verify installation

```bash
python -c "from graphiti_core import Graphiti; print('OK')"
```

### 3. Start Neo4j (if not already running)

Using Docker:

```bash
docker run --rm -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

Neo4j Aura (cloud) users can skip this step and use their Aura connection URI.

---

## Environment Variables

Set these before starting the MCP server:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEO4J_URI` | Yes | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | Yes | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | Yes | `password` | Neo4j password |
| `OPENAI_API_KEY` | Yes | -- | OpenAI API key for LLM extraction |
| `GRAPHITI_GROUP_ID` | No | `default` | Default group ID for episodes |

**Windows PowerShell:**

```powershell
$env:NEO4J_URI = "bolt://localhost:7687"
$env:NEO4J_USER = "neo4j"
$env:NEO4J_PASSWORD = "your_password"
$env:OPENAI_API_KEY = "sk-..."
```

**Linux / macOS:**

```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="your_password"
export OPENAI_API_KEY="sk-..."
```

---

## Claude Desktop Configuration

Add the Graphiti MCP server to your Claude Desktop configuration file.

### Configuration file location

- **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Linux:** `~/.config/Claude/claude_desktop_config.json`

### Minimal configuration

```json
{
  "mcpServers": {
    "graphiti": {
      "command": "uvx",
      "args": ["graphiti-core"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Configuration with pip (if uvx is unavailable)

```json
{
  "mcpServers": {
    "graphiti": {
      "command": "python",
      "args": ["-m", "graphiti_core.mcp.server"],
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Configuration with SSE transport

```json
{
  "mcpServers": {
    "graphiti": {
      "url": "http://localhost:8000/mcp",
      "env": {
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

After editing the configuration file, restart Claude Desktop.

---

## Available MCP Tools

The Graphiti MCP server exposes the following tools:

### Episode Management

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `add_episode` | Ingest text and extract entities/relationships | `name`, `episode_body`, `group_id` (optional), `source` (optional) |
| `get_episodes` | Retrieve stored episodes | `group_ids` (optional), `limit` (optional) |

### Search and Retrieval

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `search_nodes` | Search for entity nodes by query | `query`, `group_ids`, `num_results` (default: 10) |
| `search_facts` | Search for relationship edges by query | `query`, `group_ids`, `num_results` (default: 10) |
| `get_entity` | Get a specific entity by UUID | `uuid` |
| `get_entity_edges` | Get all edges connected to an entity | `uuid` |

### Graph Management

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `build_communities` | Run community detection on the graph | (none) |
| `get_communities` | List detected communities | `group_ids` (optional) |
| `delete_group` | Remove all data for a group | `group_id` |
| `get_statistics` | Get graph statistics | `group_ids` (optional) |

### Metadata

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `list_tools` | List all available MCP tools | (none) |
| `get_server_info` | Server version and status | (none) |

---

## Transport Options

### stdio (Default)

The server communicates over standard input/output. This is the default mode and works well with Claude Desktop when configured as a subprocess.

```
uvx graphiti-core
```

### SSE (Server-Sent Events)

For remote or containerized deployments:

```bash
# Start the SSE server
python -m graphiti_core.mcp.server --transport sse --port 8000
```

The server listens on `http://localhost:8000/mcp`. Configure your client to connect via SSE URL.

### When to use which

| Transport | Pros | Cons | Best For |
|-----------|------|------|----------|
| stdio | Simple, low latency, no ports | Tied to parent process | Local Claude Desktop integration |
| SSE | Remote access, container-friendly | Network overhead, port management | Multi-user setups, Docker deployment |

---

## Example Workflow

### Step 1: Start Neo4j

```bash
docker run --rm -p 7687:7687 -p 7474:7474 \
  -e NEO4J_AUTH=neo4j/password \
  neo4j:5
```

### Step 2: Configure Claude Desktop

Add the configuration JSON (from the [Claude Desktop Configuration](#claude-desktop-configuration) section above) and restart Claude Desktop.

### Step 3: Add episodes via MCP

In Claude Desktop, use the Graphiti tools to add knowledge:

```
Add an episode about Acme Corp:
"Acme Corp was founded in 2019 by Dr. Sarah Chen in San Francisco.
Sarah is the CEO and holds a PhD in Computer Science from Stanford.
Acme builds AI-powered supply chain optimization software.
Their flagship product, RouteOptimizer Pro, was launched in 2021."
```

Claude will call the `add_episode` tool, which extracts entities and relationships.

### Step 4: Search the graph

```
Search for facts about Acme Corp funding
```

This calls `search_facts` and returns matching relationships.

### Step 5: Build communities

```
Build communities to understand the graph structure
```

This calls `build_communities` and detects entity clusters.

---

## Troubleshooting

### "Connection refused" when connecting to Neo4j

**Cause:** Neo4j is not running or not reachable.

**Solutions:**
- Verify Neo4j is running: `docker ps` (check the neo4j container)
- Check the URI: `bolt://localhost:7687` is the default; if using Neo4j Aura, use your Aura URI
- Ensure the port is not firewalled: `telnet localhost 7687`

### "Invalid API key" error

**Cause:** `OPENAI_API_KEY` is missing or incorrect.

**Solutions:**
- Verify the key is set in the environment or Claude Desktop config
- Ensure the key has access to GPT-4 / GPT-4o models
- Check for typos or extra whitespace in the key

### No tools appear in Claude Desktop

**Cause:** The MCP server failed to start.

**Solutions:**
- Check Claude Desktop logs: Look at the session logs in the Claude Desktop menu (Help > View Logs)
- Run the server manually to see errors:
  ```bash
  python -m graphiti_core.mcp.server
  ```
- Verify all environment variables are set correctly in the config JSON

### "uvx: command not found"

**Cause:** `uvx` is not installed.

**Solutions:**
- Install uv: `pip install uv`
- Or use the pip configuration option instead of uvx
- Or run directly: `python -m graphiti_core.mcp.server`

### Community detection returns no communities

**Cause:** Not enough entities or relationships in the graph yet.

**Solutions:**
- Add more episodes (at least 5--10 with diverse entities)
- Ensure episodes have connected entities (shared people, companies, etc.)
- Run `build_communities` again after adding more data

### Slow search performance

**Cause:** Missing vector index or large graph.

**Solutions:**
- Run `build_indices_and_constraints` to ensure vector indexes exist
- Use `num_results` to limit return size
- Consider using `HNSW_KNN` recipe for faster (but less accurate) searches

---

## Additional Resources

- [Graphiti GitHub Repository](https://github.com/getzep/graphiti)
- [Neo4j Download](https://neo4j.com/download/)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Claude Desktop MCP Documentation](https://docs.anthropic.com/en/docs/claude-desktop-mcp)
