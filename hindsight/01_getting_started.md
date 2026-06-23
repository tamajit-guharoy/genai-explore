# 1. Getting Started with Hindsight

## What is Hindsight?

Hindsight is an **open-source memory system for AI agents** that enables agents to
*learn over time*, not just recall conversation history. Most agent memory systems
focus on recalling chat logs. Hindsight structures memory the way humans do:
**facts, experiences, and mental models** that evolve.

### The Problem It Solves

AI agents are amnesiac by design. Every session starts blank:
- No memory of what happened last Tuesday
- No recall of user preferences shared last month
- No knowledge of approaches that failed in prior attempts

Hindsight gives agents:
- **Persistent memory** across sessions
- **Learning from experience** (not just retrieving past chats)
- **Temporal reasoning** ("what happened last spring?")
- **Dedup and consolidation** (facts merge, don't repeat)
- **Evidence-grounded beliefs** with confidence scores

### State of the Art

Hindsight achieved **91.4% on LongMemEval** (the first system to cross 90%), independently
reproduced by Virginia Tech's Sanghani Center and The Washington Post.

---

## Installation

### Option A: Docker (Recommended for Quick Start)

```bash
export OPENAI_API_KEY=sk-xxx

docker run -d --name hindsight --restart unless-stopped \
  -p 8888:8888 -p 9999:9999 \
  -e HINDSIGHT_API_LLM_API_KEY=$OPENAI_API_KEY \
  -e HINDSIGHT_API_WORKER_ID=hindsight-prod \
  -v hindsight-data:/home/hindsight/.pg0 \
  ghcr.io/vectorize-io/hindsight:latest
```

After startup:
- **API Server**: http://localhost:8888
- **Control Plane (Web UI)**: http://localhost:9999
- **Health check**: `curl http://localhost:8888/health`

### Option B: Pip Install (Self-Hosted)

```bash
# Install the full package (includes embedded PostgreSQL)
pip install hindsight-all

# Set your LLM provider
export HINDSIGHT_API_LLM_PROVIDER=openai
export HINDSIGHT_API_LLM_API_KEY=sk-xxx

# Start the server
hindsight-api
```

### Option C: Hindsight Cloud (Managed)

Sign up at https://ui.hindsight.vectorize.io/signup for a free managed instance.
No self-hosting needed.

---

## Install the Python Client

```bash
pip install hindsight-client
```

---

## Verify Your Setup

```python
from hindsight_client import Hindsight

# Connect to your server
client = Hindsight(base_url="http://localhost:8888")

# Check health
import requests
resp = requests.get("http://localhost:8888/health")
print(resp.json())  # Should return {"status": "ok"}

# Check version
resp = requests.get("http://localhost:8888/version")
print(resp.json())  # {"api_version": "0.8.x", "features": {...}}
```

---

## Your First Memory Bank

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Create a memory bank — the container for all memories
client.create_bank(
    bank_id="my-first-bank",
    name="My First Bank",
    mission="You are a helpful assistant. Remember user preferences and project details."
)

# Store a memory
client.retain(
    bank_id="my-first-bank",
    content="The user's name is Alice and she works at Google in Mountain View."
)

# Recall it
results = client.recall(
    bank_id="my-first-bank",
    query="Where does Alice work?"
)

for r in results.results:
    print(f"Type: {r.type}")
    print(f"Text: {r.text}")
    print("---")
```

---

## The Three Core Operations

| Operation | What it does | When to use |
|-----------|-------------|-------------|
| **retain()** | Store new information | After every conversation turn, user feedback, or tool result |
| **recall()** | Search existing memories | Before responding — find relevant past context |
| **reflect()** | Reason over memories | When you need analysis, recommendations, or consolidated answers |

---

## Supported LLM Providers

Hindsight uses LiteLLM under the hood. Set via `HINDSIGHT_API_LLM_PROVIDER`:

| Provider | env value |
|----------|-----------|
| OpenAI | `openai` |
| Anthropic | `anthropic` |
| Google Gemini | `gemini` |
| Groq | `groq` |
| Ollama (local) | `ollama` |
| LM Studio (local) | `lmstudio` |
| OpenRouter | `openrouter` |
| DeepSeek | `deepseek` |
| xAI | `xai` |
| AWS Bedrock | `bedrock` |
| Custom endpoint | Any LiteLLM-supported provider |

Example with Groq:
```bash
export HINDSIGHT_API_LLM_PROVIDER=groq
export HINDSIGHT_API_LLM_API_KEY=gsk_xxx
export HINDSIGHT_API_LLM_MODEL=llama-4-maverick
hindsight-api
```

---

## Next Steps

Now that you have Hindsight running, continue to:
- **[02_core_concepts.md](02_core_concepts.md)** — Understand the architecture: memory types, TEMPR retrieval, biomimetic design
- **[03_retain.md](03_retain.md)** — Deep dive into storing memories
- Run the notebook: `notebooks/01_getting_started.ipynb`
