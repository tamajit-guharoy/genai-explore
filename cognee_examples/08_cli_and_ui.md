# 08 — CLI & UI Workflows

This is a reference document, not a runnable script. It covers common CLI
workflows and UI features.

## Starting the Cognee Server

```bash
# Launch with UI (backend + frontend + MCP server)
cognee-cli -ui

# API server only (no UI)
python -m cognee.api

# Custom port
cognee-cli -ui --port 9000
```

The UI opens at `http://localhost:8000` by default. It provides:
- A chat interface for querying your knowledge graph
- Data upload (drag-and-drop files)
- Dataset management (create, list, delete)
- Search with configurable parameters
- Graph visualization preview

## CLI Commands Reference

### Data Ingestion
```bash
# Add text directly
cognee-cli add "Artificial intelligence is transforming industries."

# Add a file
cognee-cli add path/to/document.pdf

# Add multiple files
cognee-cli add docs/*.pdf

# Add from URL
cognee-cli add "https://docs.example.com/api-reference"

# Add with dataset name
cognee-cli add report.pdf --dataset quarterly_reports
```

### Knowledge Graph Construction
```bash
# Process all unprocessed data
cognee-cli cognify

# Process specific datasets
cognee-cli cognify --datasets quarterly_reports,product_docs

# Force reprocessing (ignore incremental cache)
cognee-cli cognify --force
```

### Search
```bash
# Default graph completion search
cognee-cli search "What is our refund policy?"

# Chunk-level semantic search
cognee-cli search "Find exact text about SLA terms" --type CHUNKS

# Scoped to a dataset
cognee-cli search "Q4 revenue" --dataset quarterly_reports

# With result limit
cognee-cli search "microservices architecture" --top-k 5
```

### Dataset Management
```bash
# List all datasets
cognee-cli datasets list

# Delete a dataset
cognee-cli datasets delete --name experimental_data

# Export a dataset
cognee-cli datasets export --name product_docs --format json
```

### Skills Management (v0.5.4rc1+)
```bash
# Ingest a skill definition
cognee-cli skills ingest --path ./my_skill/

# List available skills
cognee-cli skills list

# Execute a skill
cognee-cli skills execute --name legal_summarizer

# Get skill execution history
cognee-cli skills history --name legal_summarizer
```

## Environment Setup

```bash
# Required: LLM API key
export LLM_API_KEY=sk-...

# Optional: Override defaults
export LLM_PROVIDER=openai           # openai, anthropic, ollama, google
export LLM_MODEL=gpt-4o
export GRAPH_DB_PROVIDER=kuzu        # kuzu, neo4j, falkordb
export VECTOR_DB_PROVIDER=lancedb    # lancedb, qdrant, chroma, pinecone
export RELATIONAL_DB_PROVIDER=sqlite # sqlite, postgresql
export COGNEE_CONCURRENCY=10         # Max concurrent LLM calls
```

## Common Workflows

### Workflow 1: Build a knowledge base from documents
```bash
cognee-cli add docs/*.pdf --dataset company_kb
cognee-cli cognify --datasets company_kb
cognee-cli search "What is our remote work policy?"
```

### Workflow 2: Incremental update
```bash
# Add new document to existing dataset
cognee-cli add new_report.pdf --dataset company_kb
# Cognify (only processes the new file)
cognee-cli cognify
```

### Workflow 3: Exploratory analysis with visualization
```bash
cognee-cli add research_papers/*.pdf --dataset literature_review
cognee-cli cognify
cognee-cli -ui  # Open UI to explore the graph visually
```

## Troubleshooting CLI

| Issue | Solution |
|---|---|
| `cognee-cli: command not found` | `pip install cognee` or add Python scripts to PATH |
| `Connection refused` on UI | Server not started; run `cognee-cli -ui` |
| Search returns empty | Check dataset name; verify `cognee-cli cognify` completed |
| Cognify hangs | Check LLM_API_KEY; reduce COGNEE_CONCURRENCY if rate limited |
| Port already in use | `cognee-cli -ui --port 9000` |
