# OpenHands Tutorial — From Basics to Advanced

> **OpenHands** (formerly OpenDevin) is an open-source platform for building and running autonomous AI coding agents. It can write code, run shell commands, browse the web, and handle entire software tasks end-to-end — from a GitHub issue to a merged PR.
>
> - GitHub: <https://github.com/All-Hands-AI/OpenHands>
> - SDK: <https://github.com/OpenHands/software-agent-sdk>
> - Docs: <https://docs.openhands.dev>
> - PyPI: `openhands`
> - License: MIT

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Python** | 3.12+ |
| **uv** | 0.11.6+ (package manager, required for MCP servers) |
| **Docker** | Required for sandboxed execution and GUI server |
| **LLM API Key** | OpenAI, Anthropic, OpenRouter, or any litellm-compatible provider |
| **OS** | Linux, macOS, WSL2 (Windows via WSL) |

**Quick install:**
```bash
# Install uv (if not already)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install OpenHands CLI
uv tool install openhands --python 3.12

# Verify
openhands --version
```

---

## Notebook Index

Each notebook is self-contained and can be run independently. They progress from basic concepts to advanced workflows.

| # | Notebook | Topics | Runnability |
|---|---|---|---|
| 01 | `01_what_is_openhands.ipynb` | Architecture, event loop, agent loop, comparison to alternatives | [CONCEPT] Read-only — no API key needed |
| 02 | `02_installation_setup.ipynb` | uv install, Docker setup, config files, model providers | [SETUP] Terminal commands |
| 03 | `03_cli_modes.ipynb` | TUI, headless, web, ACP, cloud — all CLI modes | [DEMO] Needs API key for headless |
| 04 | `04_sdk_hello_world.ipynb` | LLM, Agent, Conversation, minimal working example | [DEMO] Needs API key |
| 05 | `05_tools_and_workspace.ipynb` | FileEditor, Terminal, TaskTracker, WebBrowser, MCP tools | [DEMO] Needs API key |
| 06 | `06_context_and_skills.ipynb` | Condensers, skills system, AGENTS.md, context files | [DEMO] Needs API key |
| 07 | `07_security_and_approval.ipynb` | Security analyzer, risk levels, approval modes, sandboxing | [CONCEPT] + [DEMO] |
| 08 | `08_agent_server.ipynb` | Remote execution, REST API, Docker/K8s sandboxes | [DEMO] Needs API key + Docker |
| 09 | `09_headless_automation.ipynb` | CI/CD pipelines, JSONL output, batch tasks, exit codes | [DEMO] Needs API key |
| 10 | `10_ide_integration.ipynb` | ACP protocol, JetBrains, VS Code, Zed, Toad setup | [CONCEPT] Config examples |
| 11 | `11_advanced_multi_agent.ipynb` | Orchestration, task decomposition, parallel agents | [DEMO] Needs API key |
| 12 | `12_real_world_recipes.ipynb` | Bug fix, refactor, dependency update, test generation | [RECIPE] Needs API key |
| 13 | `13_appendix_reference.ipynb` | Cheat sheet, CLI reference, comparison tables, glossary | [CONCEPT] Read-only |

**Legend:**
- **[CONCEPT]** — Theory and code patterns, no API key needed
- **[SETUP]** — Installation and configuration commands
- **[DEMO]** — Runnable examples that need an LLM API key
- **[RECIPE]** — Complete end-to-end workflows

---

## Quick Start (If You Just Want to Try One Thing)

```bash
# 1. Set your API key
export LLM_API_KEY="sk-..."

# 2. Run OpenHands in headless mode
openhands --headless -t "Write a Python script that prints 'Hello, OpenHands!'"

# 3. Or launch the interactive TUI
openhands
```

---

## Key Concepts at a Glance

| Concept | What It Is |
|---|---|
| **Agent** | The reasoning-action loop: query LLM → generate action → execute tool → observe result → repeat |
| **Conversation** | A session that holds event history and drives the agent loop |
| **Tool** | What the agent can do: edit files, run bash, browse web, track tasks |
| **Workspace** | Where the agent works: local directory, Docker container, or remote API |
| **Condenser** | Compresses conversation history to stay within token limits |
| **Skill** | Reusable prompt/instruction that activates on trigger conditions |
| **Security Analyzer** | Evaluates each action's risk before execution |
| **ACP** | Agent Client Protocol — JSON-RPC 2.0 protocol for IDE integration |
| **MCP** | Model Context Protocol — connects agents to external tools and data sources |

---

## Sources

- [OpenHands Documentation](https://docs.openhands.dev)
- [Software Agent SDK — GitHub](https://github.com/OpenHands/software-agent-sdk)
- [OpenHands CLI — PyPI](https://pypi.org/project/openhands)
- [OpenHands Paper (arXiv)](https://arxiv.org/abs/2407.16741)
- [SDK Paper (arXiv)](https://arxiv.org/abs/2511.03690)

*Tutorial written June 2026 against OpenHands CLI v1.x and SDK.*
