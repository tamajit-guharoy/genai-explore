# Google ADK (Agent Development Kit) — Complete Tutorial

> **Comprehensive, from-scratch guide to Google's open-source agent framework.**
> Covers ADK v2.x: Agents, Tools, Multi-Agent Systems, Callbacks, Memory,
> A2A Protocol, Graph Workflows, Task API, Evaluation & Deployment.

## What is Google ADK?

**Agent Development Kit (ADK)** is an open-source, code-first Python framework
by Google for building, evaluating, and deploying AI agents. Released in April
2025 and now at v2.3+ (June 2026), it is model-agnostic (Gemini, Claude, GPT,
Ollama…) and deployment-agnostic (local, Cloud Run, Vertex AI Agent Engine, GKE).

### Key Features
- **Code-first**: define agents, tools, and orchestration in pure Python
- **Multi-agent**: Sequential, Parallel, Loop, and hierarchical composition
- **Rich tools**: Google Search, Code Executor, MCP, custom functions, OpenAPI
- **Graph Workflows** (ADK 2.0): deterministic execution with routing, fan-out,
  loops, retry, human-in-the-loop
- **Task API**: structured agent-to-agent delegation
- **A2A Protocol**: standardized inter-agent communication over HTTP
- **Built-in eval**: LLM-as-judge scoring with evalsets
- **One-command deploy**: `adk deploy cloud_run` or Vertex AI Agent Engine

## Tutorial Structure

| Notebook | Topics |
|----------|--------|
| `01_installation_setup.ipynb` | Installing ADK, venv, API keys, `adk create`, `adk run`, `adk web` |
| `02_first_agent.ipynb` | Agent class, Runner, Sessions, models, instructions, system prompt |
| `03_tools.ipynb` | Built-in tools (Google Search, Code Executor), custom function tools, MCP tools, tool configuration |
| `04_multi_agent.ipynb` | SequentialAgent, ParallelAgent, LoopAgent, sub_agents, agent routing/transfer |
| `05_callbacks_memory_state.ipynb` | 6 callback hooks, session state, memory service, streaming, artifacts |
| `06_a2a_protocol.ipynb` | A2A protocol: exposing agents, RemoteA2aAgent, agent cards, distributed systems |
| `07_workflow_task_api.ipynb` | ADK 2.0 graph workflows: nodes, edges, routing, fan-out, HITL, Task API |
| `08_evaluation_deployment.ipynb` | Eval framework, evalsets, LLM-as-judge, deploy to Cloud Run / Vertex AI |

## Prerequisites

- Python 3.10+
- A Google AI Studio API key (free) or Vertex AI setup
- Basic Python knowledge

## Quick Start

```bash
# 1. Clone / navigate to this directory
cd google_adk

# 2. Create and activate venv
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Install ADK
pip install google-adk

# 4. Set your API key
export GOOGLE_API_KEY="your-key-here"

# 5. Launch Jupyter
jupyter notebook

# 6. Open 01_installation_setup.ipynb and follow along!
```

## References

- Official docs: https://adk.dev
- GitHub: https://github.com/google/adk-python
- Samples: https://github.com/google/adk-samples
- A2A Protocol: https://a2aprotocol.ai

---

*Tutorial created: June 2026. ADK version targeted: v2.3.x.*
