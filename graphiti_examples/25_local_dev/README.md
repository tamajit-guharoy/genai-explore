# Local Development Setup Guide for Graphiti

This guide covers four approaches to running Graphiti locally, from the
simplest (Neo4j Desktop) to the most self-contained (Kuzu embedded + Ollama).

---

## Option 1: Neo4j Desktop (Windows / Mac / Linux)

Neo4j Desktop provides a GUI for managing local Neo4j instances. This is the
easiest way to get started if you prefer a visual interface.

### Step-by-step

1. **Download Neo4j Desktop**
   - Go to https://neo4j.com/download/
   - Create a free account (required)
   - Download Neo4j Desktop for your OS

2. **Install Neo4j Desktop**
   - Run the installer
   - Launch Neo4j Desktop
   - (Windows) If you see a Windows Defender warning, click "Allow access"

3. **Create a local database**
   - Click "New" -> "Local DBMS"
   - Set a name (e.g., `graphiti-local`)
   - Set a password (e.g., `password` for local dev -- change for production)
   - Choose version: Neo4j 5.x (latest stable)
   - Click "Create"

4. **Start the database**
   - Click the "Start" button next to your database
   - Wait for the status to show "Started" (green)
   - Note the Bolt URL: `bolt://localhost:7687` and HTTP URL: `http://localhost:7474`

5. **Verify the connection**
   - Open your browser to `http://localhost:7474` (Neo4j Browser)
   - Connect with `neo4j` / `<your-password>`
   - Run `:play graphiti` or just `RETURN 1` to verify it works

6. **Configure environment variables**

   ```bash
   # Windows PowerShell
   $env:NEO4J_URI="bolt://localhost:7687"
   $env:NEO4J_USER="neo4j"
   $env:NEO4J_PASSWORD="password"
   $env:OPENAI_API_KEY="sk-your-key-here"

   # Linux / Mac
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_USER="neo4j"
   export NEO4J_PASSWORD="password"
   export OPENAI_API_KEY="sk-your-key-here"
   ```

7. **Run an example**

   ```bash
   cd graphiti_examples
   python 01_hello_graphiti.py
   ```

### Screenshot references

- Neo4j Desktop main screen: Shows your database with Start/Stop buttons
- Neo4j Browser (`http://localhost:7474`): Shows the Cypher query editor
- Bolt connection confirmation: Shows the "Connected to Neo4j" indicator

---

## Option 2: Docker Compose (Neo4j + Graphiti)

For a fully containerized local setup, use the `docker-compose.yml` below.

### Prerequisites

- Docker Desktop (Win/Mac) or Docker Engine (Linux)
- Docker Compose v2 (included with Docker Desktop)

### docker-compose.yml

```yaml
version: "3.9"

services:
  neo4j:
    image: neo4j:5-community
    container_name: graphiti-neo4j
    ports:
      - "7687:7687"   # Bolt protocol
      - "7474:7474"   # HTTP browser
    environment:
      - NEO4J_AUTH=neo4j/password
      - NEO4J_dbms_memory_pagecache_size=512M
      - NEO4J_dbms_memory_heap_initial__size=512M
      - NEO4J_dbms_memory_heap_max__size=1G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - neo4j_import:/var/lib/neo4j/import
      - neo4j_plugins:/plugins
    healthcheck:
      test: ["CMD", "cypher-shell", "-u", "neo4j", "-p", "password", "RETURN 1"]
      interval: 15s
      timeout: 10s
      retries: 10
      start_period: 30s
    restart: unless-stopped

volumes:
  neo4j_data:
  neo4j_logs:
  neo4j_import:
  neo4j_plugins:
```

### Setup steps

1. Save the file as `docker-compose.yml`
2. Start the service:
   ```bash
   docker compose up -d
   ```
3. Check health:
   ```bash
   docker compose ps
   # Should show "healthy" for neo4j
   ```
4. Follow logs:
   ```bash
   docker compose logs -f neo4j
   ```
5. Verify Neo4j is ready:
   ```bash
   docker exec graphiti-neo4j cypher-shell -u neo4j -p password "RETURN 1;"
   ```
6. Set environment variables (see Option 1, step 6)
7. Run an example:
   ```bash
   python graphiti_examples/01_hello_graphiti.py
   ```

### Shutting down

```bash
docker compose down          # stops containers
docker compose down -v       # stops and deletes volumes (wipes data)
```

---

## Option 3: Kuzu Embedded (Zero Dependency, Single Process)

[Kuzu](https://kuzudb.com/) is an embedded property graph database that runs
in-process with no server needed. This is useful for:

- Development environments where Docker is unavailable
- CI/CD pipelines
- Simple testing without infrastructure

### Installation

```bash
pip install kuzu  # or add to requirements.txt
```

### Usage with Graphiti

As of Graphiti v0.4+, Kuzu can be used as a backend:

```python
from graphiti_core import Graphiti

# Graphiti auto-detects Kuzu when using a file path
graphiti = Graphiti(
    uri="./graphiti_kuzu_db",   # Local file path for Kuzu
    user="",                     # No auth needed
    password="",
    use_kuzu=True,               # Enable Kuzu backend
)
```

### Limitations of Kuzu

| Feature | Kuzu | Neo4j |
|---------|------|-------|
| Server mode | No (embedded only) | Yes |
| Concurrent access | Single process | Multi-client |
| Graph algorithm libraries | Limited | Rich (GDS library) |
| Vector search | No | Yes (via plugins) |
| Persistence | File-based | Server-managed |
| Maximum dataset | <10M nodes | Enterprise-scale |

**When to choose Kuzu:**
- You need a zero-dependency setup for development
- Your dataset is small (<1M entities)
- You don't need vector search or graph algorithms
- You want fast startup without infrastructure

**When to choose Neo4j:**
- You need vector search on entity embeddings
- You need community detection (Leiden, Louvain)
- Your dataset is large
- You need concurrent access from multiple processes

---

## Option 4: Ollama for Fully Local LLM (No API Keys Needed)

If you want to avoid sending data to external LLM providers, you can run a
local model with [Ollama](https://ollama.ai/).

### Setup

1. **Install Ollama**

   ```bash
   # Linux / Mac
   curl -fsSL https://ollama.ai/install.sh | sh

   # Windows: Download from https://ollama.ai/download
   ```

2. **Pull a model**

   ```bash
   # For entity extraction, a model with good instruction following:
   ollama pull llama3.2:8b

   # Or for better results (requires more RAM):
   ollama pull llama3.3:70b
   ```

3. **Set environment variables**

   ```bash
   export OPENAI_API_KEY="ollama"                                # Placeholder value
   export OPENAI_BASE_URL="http://localhost:11434/v1"            # Ollama's OpenAI-compatible endpoint
   export GRAPHITI_LLM_MODEL="ollama/llama3.2:8b"               # Model to use
   export GRAPHITI_LLM_EMBEDDING_MODEL="ollama/nomic-embed-text" # Embedding model
   ```

   Or in Python:

   ```python
   import os
   os.environ["OPENAI_API_KEY"] = "ollama"
   os.environ["OPENAI_BASE_URL"] = "http://localhost:11434/v1"
   os.environ["GRAPHITI_LLM_MODEL"] = "ollama/llama3.2:8b"
   os.environ["GRAPHITI_LLM_EMBEDDING_MODEL"] = "ollama/nomic-embed-text"
   ```

4. **Verify Ollama is working**

   ```bash
   curl http://localhost:11434/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "llama3.2:8b", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

### Performance considerations

- **llama3.2:8b**: ~8GB RAM needed. Good quality, reasonable speed on modern CPUs.
- **nomic-embed-text**: ~2GB RAM. Good quality embeddings.
- For production-quality entity extraction, consider using a cloud LLM provider.
- Local models may produce lower-quality entity/relationship extraction than
  GPT-4 or Claude.

---

## Verifying Your Setup Works

Run this quick check script to verify everything is configured correctly:

```python
# check_setup.py
import os
import sys
import socket


def check_env():
    """Verify required environment variables."""

    checks = {
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", ""),
        "NEO4J_URI": os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        "NEO4J_USER": os.getenv("NEO4J_USER", "neo4j"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD", "password"),
    }

    print("Environment variables:")
    for name, value in checks.items():
        status = "SET" if value else "NOT SET"
        print(f"  {name}: {status}")

    if not checks["OPENAI_API_KEY"]:
        print("  WARNING: OPENAI_API_KEY is not set. LLM extraction will fail.")


def check_neo4j():
    """Check if Neo4j is reachable."""

    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    host, _, port_str = uri.replace("bolt://", "").replace("neo4j://", "").partition(":")
    port = int(port_str) if port_str else 7687

    try:
        sock = socket.create_connection((host, port), timeout=3)
        sock.close()
        print(f"  Neo4j: REACHABLE at {host}:{port}")
        return True
    except (OSError, socket.timeout) as e:
        print(f"  Neo4j: UNREACHABLE at {host}:{port} ({e})")
        return False


def try_import():
    """Check if graphiti_core is installed."""

    try:
        import graphiti_core
        print(f"  graphiti_core: INSTALLED (version: {graphiti_core.__version__})")
        return True
    except ImportError:
        print("  graphiti_core: NOT INSTALLED")
        print("  Run: pip install graphiti-core")
        return False


if __name__ == "__main__":
    print("Graphiti Setup Check")
    print("=" * 40)
    check_env()
    print()
    check_neo4j()
    print()
    try_import()
    print()
    if check_neo4j() and try_import():
        print("Setup looks good! Ready to run examples.")
    else:
        print("Some checks failed. See guidance above.")
```

Save this as `check_setup.py` and run:

```bash
python check_setup.py
```

---

## Troubleshooting Common Local Dev Issues

### Neo4j won't start

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| Container exits immediately | Port conflict | Change host port mapping (e.g., `7688:7687`) |
| "insufficient memory" | Docker memory limit | Increase Docker Desktop memory to 4GB+ |
| Java heap errors | Neo4j memory config | Reduce heap: `NEO4J_dbms_memory_heap_max__size=512M` |
| "database already exists" | Corrupt volume | `docker compose down -v && docker compose up -d` |

### Connection refused

```
Could not connect to Neo4j at bolt://localhost:7687
```

- Is Neo4j Desktop running? Click "Start" on the database.
- Is Docker container running? `docker ps | grep neo4j`
- Check the host: some Docker setups need `bolt://host.docker.internal:7687`
  instead of `bolt://localhost:7687`
- Windows WSL2: use `bolt://localhost:7687` from WSL, or the WSL IP from Windows

### LLM extraction fails

```
graphiti_core.llm_client.errors.LLMError: API call failed
```

- Is `OPENAI_API_KEY` set correctly?
  - Run `echo $env:OPENAI_API_KEY` (PowerShell) to verify
  - Run `echo $OPENAI_API_KEY` (bash) to verify
- Check for trailing whitespace in the env var
- If using Ollama, is the server running?
  - `curl http://localhost:11434/api/tags`
- Rate limited? Add delays between episodes in your script

### Embedding dimension mismatch

```
ValueError: Embedding dimension 1536 does not match existing index dimension 384
```

This happens when switching between embedding models. Solution:

1. Delete the Neo4j database and recreate it
2. Or use `graphiti.delete_group()` to clear data and let it regenerate

For Docker: `docker compose down -v && docker compose up -d`

For Neo4j Desktop: Stop the database, click "..." -> "Delete", create a new one.

### Slow performance on first run

The first `add_episode()` call builds Neo4j indices and constraints. This can
take 10-30 seconds. Subsequent calls will be faster.

### "graphiti_core" module not found

```bash
pip install graphiti-core

# If that fails, try:
pip install git+https://github.com/getzep/graphiti.git
```

### Windows-specific issues

1. **Long path errors**: Enable long paths in Windows:
   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" `
     -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

2. **WSL2 file system performance**: Keep your project on the Linux filesystem
   (`/home/user/...`) not on `/mnt/c/...` for better I/O.

3. **Docker Desktop WSL2 backend**: Make sure WSL2 is enabled in Docker Desktop
   Settings -> General -> "Use WSL 2 based engine".

---

## Quick Reference: Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEO4J_URI` | `bolt://localhost:7687` | Neo4j connection URI |
| `NEO4J_USER` | `neo4j` | Neo4j username |
| `NEO4J_PASSWORD` | `password` | Neo4j password |
| `OPENAI_API_KEY` | (none) | OpenAI API key for LLM extraction |
| `OPENAI_BASE_URL` | (none) | Custom LLM endpoint (e.g., Ollama) |
| `GRAPHITI_LLM_MODEL` | (auto) | Override the LLM model |
| `GRAPHITI_LLM_EMBEDDING_MODEL` | (auto) | Override the embedding model |
