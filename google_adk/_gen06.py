#!/usr/bin/env python3
"""Generate notebooks 06, 07, 08 with deep theory + multiple examples (no execution)."""
import json, os

BASE = r"C:\Users\guhar\ws\calude_tutorial\google_adk"
ENV_PATH = BASE + r"\.env"

def build(cells):
    out = []
    for ct, raw in cells:
        src = raw.split('\n')
        src = [s + '\n' for s in src[:-1]] + [src[-1]] if src else [""]
        entry = {"cell_type": ct, "metadata": {}, "source": src}
        if ct == "code":
            entry["outputs"] = []
            entry["execution_count"] = None
        out.append(entry)
    return {
        "cells": out,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12.0"}
        },
        "nbformat": 4, "nbformat_minor": 4
    }

def save(name, cells):
    path = os.path.join(BASE, name)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(build(cells), f, indent=1, ensure_ascii=False)
    print(f"  wrote {name} ({os.path.getsize(path)} bytes)")

ENV_CELL = '''# --- Load API key from .env ---
import os
_env = r"''' + ENV_PATH + '''"
if os.path.exists(_env):
    for line in open(_env):
        line = line.strip()
        if line and "=" in line and not line.startswith("#"):
            k, v = line.split("=", 1)
            os.environ[k] = v.strip().strip('"').strip("'")
print(f'API key: {"OK" if os.environ.get("GOOGLE_API_KEY") else "NOT FOUND"}')'''

IMP_CELL = '''# --- Core ADK imports ---
import asyncio
from google.adk import Agent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai.types import Content, Part
print("Core imports ready")'''

# =====================================================================
# NOTEBOOK 06 — A2A PROTOCOL
# =====================================================================

nb06 = [
    ("markdown", r'''# 06 — A2A Protocol: Distributed Agent Communication

## What You'll Learn

1. **What A2A is** — the open protocol for agent-to-agent communication
2. **The A2A specification** — JSON-RPC 2.0, Agent Cards, Task lifecycle
3. **Server side** — exposing any ADK agent as an HTTP service with `to_a2a()`
4. **Client side** — consuming remote agents with `RemoteA2aAgent`
5. **Multi-server orchestration** — coordinating agents across machines
6. **Agent Cards** — auto-discovery, metadata, capabilities, skills
7. **Security** — authentication, authorization, network considerations
8. **Comparison** — A2A vs MCP vs sub_agents: when to use which

> **Requires:** `pip install google-adk[a2a]` for full A2A support
> **Prerequisites:** Notebooks 02 (Agent), 04 (Multi-agent)

---

## 6.1 The Problem A2A Solves

### Without A2A: Monolithic Agent Systems

```
┌─────────────────────────────────────────┐
│  Single Process                         │
│  ┌──────────┐  ┌──────────┐           │
│  │ Weather   │  │ Math      │           │
│  │ Agent     │  │ Agent     │           │
│  └──────────┘  └──────────┘           │
│  ┌──────────┐  ┌──────────┐           │
│  │ Code      │  │ Research  │           │
│  │ Agent     │  │ Agent     │           │
│  └──────────┘  └──────────┘           │
│  All in one Python process, one machine │
└─────────────────────────────────────────┘
```

**Problems:**
- All agents must run in the same process/machine
- Cannot share agents across teams or organizations
- Cannot use agents built in different languages/frameworks
- Cannot scale individual agents independently
- No standard way to discover or communicate with external agents

### With A2A: Distributed Agent Networks

```
Team A's Server              Team B's Server
┌──────────────┐            ┌──────────────┐
│ Weather Agent │            │ Math Agent    │
│ (Python/ADK)  │            │ (Java/Spring) │
│ Port 8001     │            │ Port 8002     │
└──────┬───────┘            └──────┬───────┘
       │                           │
       │    A2A Protocol (HTTP)    │
       │                           │
┌──────┴───────────────────────────┴──────┐
│          Orchestrator Agent              │
│          (Python/ADK, any machine)       │
│          Uses RemoteA2aAgent to call     │
│          both remote agents              │
└──────────────────────────────────────────┘
```

**Benefits:**
- Agents can be on different machines, clouds, or organizations
- Agents can be built in different languages (Python, Java, Go, JS)
- Standard discovery via Agent Cards
- Independent scaling and deployment
- Location transparency — orchestrator code doesn't change

---

## 6.2 The A2A Specification

### Protocol Details

A2A (Agent-to-Agent) is an **open protocol** governed by the Linux Foundation.
It defines:

| Component | Description |
|-----------|-------------|
| **Transport** | HTTP/HTTPS with SSE (Server-Sent Events) for streaming |
| **Message Format** | JSON-RPC 2.0 |
| **Discovery** | Agent Card at `/.well-known/agent-card.json` |
| **Task Lifecycle** | submitted -> working -> input-required -> completed/failed |
| **Content Types** | TextPart, FilePart, DataPart |

### Agent Card Structure

Every A2A server exposes a JSON "business card" at a well-known URL.
This is how clients discover what an agent can do:

```json
{
  "name": "weather_agent",
  "description": "Provides weather forecasts for any city",
  "version": "1.0.0",
  "capabilities": {
    "streaming": true,
    "pushNotifications": false
  },
  "skills": [
    {
      "name": "get_weather",
      "description": "Get current weather for a city",
      "inputModes": ["text"],
      "outputModes": ["text", "data"]
    }
  ],
  "endpoints": {
    "tasks": "/tasks",
    "tasksSubscribe": "/tasks/subscribe"
  }
}
```

### Task Lifecycle

```
Client sends task
    |
    v
SUBMITTED ----> WORKING ----> COMPLETED
                   |               |
                   |               +-> Failed (error)
                   |
                   +-> INPUT_REQUIRED (needs human input)
                   |       |
                   |       v
                   |    Client provides input
                   |       |
                   |       v
                   +-- WORKING (continue processing)
```

**Key states:**
- `SUBMITTED`: Task received, not yet started
- `WORKING`: Agent is processing (may stream updates via SSE)
- `INPUT_REQUIRED`: Agent needs more input from the client (HITL)
- `COMPLETED`: Task done, result available
- `FAILED`: Task failed with error

### Message and Part Types

A2A messages contain parts, each of which can be:

| Part Type | Content | Use Case |
|-----------|---------|----------|
| `TextPart` | Plain text | Conversational responses |
| `FilePart` | File URI or base64 | Images, PDFs, documents |
| `DataPart` | Structured JSON | Tool results, structured data |

---

## 6.3 Server Side: Exposing an Agent with to_a2a()

### How to_a2a() Works

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

# 1. Create a normal ADK agent
agent = Agent(name="weather", model="gemini-2.5-flash", ...)

# 2. Convert it to an A2A-compatible Starlette app
a2a_app = to_a2a(agent)

# 3. Run with any ASGI server (uvicorn, hypercorn, etc.)
# uvicorn server_module:a2a_app --host 0.0.0.0 --port 8001
```

**What to_a2a() does internally:**
1. Wraps the agent in a Starlette/FastAPI application
2. Exposes `/.well-known/agent-card.json` (auto-generated from agent metadata)
3. Exposes `/tasks` endpoint for JSON-RPC task submission
4. Exposes `/tasks/subscribe` for SSE streaming
5. Handles task lifecycle management automatically'''),

    ("code", IMP_CELL),

    ("code", r'''# ====================================================================
# EXAMPLE 1: A2A Server — Expose an agent as an HTTP service
# ====================================================================
# This code would go in a file like weather_server.py
# Run it with: uvicorn weather_server:app --host 0.0.0.0 --port 8001

# --- Server-side code (reference) ---
# from google.adk.a2a.utils.agent_to_a2a import to_a2a
#
# # Define your agent normally
# weather_agent = Agent(
#     name="weather_service",
#     model="gemini-2.5-flash",
#     instruction="""You are a weather forecasting service.
#     Provide accurate weather information for any city.
#     Include temperature, conditions, and a 3-day forecast.""",
#     description="Weather forecasting agent for any city worldwide",
# )
#
# # Convert to A2A-compatible HTTP app
# app = to_a2a(weather_agent)
#
# # That's it! The app now exposes:
# #   GET  /.well-known/agent-card.json  -> Agent Card (discovery)
# #   POST /tasks                        -> Submit a task (JSON-RPC)
# #   POST /tasks/subscribe              -> Submit + stream via SSE
#
# # Run: uvicorn weather_server:app --host 0.0.0.0 --port 8001

print("A2A server pattern documented")
print("Key: to_a2a(agent) converts any ADK agent to an HTTP service")'''),

    ("markdown", r'''## 6.4 Client Side: Consuming Remote Agents

### RemoteA2aAgent — Looks Like a Local Agent

The magic of A2A: from the orchestrator's perspective, a remote agent
looks EXACTLY like a local sub-agent. You put it in `sub_agents=[]`
and the orchestrator delegates to it seamlessly.

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

remote_weather = RemoteA2aAgent(
    name="remote_weather",
    agent_card="http://weather-server:8001/.well-known/agent-card.json"
)

orchestrator = Agent(
    name="main",
    model="gemini-2.5-flash",
    instruction="Route weather questions to remote_weather",
    sub_agents=[remote_weather],  # Looks like a normal sub-agent!
)
```

### How RemoteA2aAgent Works Internally

```
1. RemoteA2aAgent fetches the Agent Card from the URL
2. ADK registers it as a sub-agent with transfer_to_agent capability
3. When orchestrator's LLM calls transfer_to_agent("remote_weather"):
   a. RemoteA2aAgent sends a JSON-RPC task to the remote server
   b. Remote server runs the agent and returns the result
   c. RemoteA2aAgent wraps the result as an Event
   d. Orchestrator sees the result like any other sub-agent response
```

### Location Transparency

The orchestrator code is IDENTICAL whether the sub-agent is local or remote:

```python
# LOCAL sub-agent (same process):
local_weather = Agent(name="weather", model="gemini-2.5-flash", ...)
orchestrator = Agent(name="main", ..., sub_agents=[local_weather])

# REMOTE sub-agent (different machine):
remote_weather = RemoteA2aAgent(name="weather", agent_card="http://...")
orchestrator = Agent(name="main", ..., sub_agents=[remote_weather])

# Same code! Just swap the agent definition.
```'''),

    ("code", r'''# ====================================================================
# EXAMPLE 2: A2A Client — Consume a remote agent
# ====================================================================
# This is the orchestrator that calls the remote weather server

# from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
#
# # Point to the remote server's agent card
# remote_weather = RemoteA2aAgent(
#     name="remote_weather",
#     agent_card="http://localhost:8001/.well-known/agent-card.json",
# )
#
# # Create orchestrator that delegates weather questions to the remote agent
# orchestrator = Agent(
#     name="orchestrator",
#     model="gemini-2.5-flash",
#     instruction="""You are a helpful assistant.
#     For weather questions, delegate to remote_weather.
#     Handle other questions yourself.""",
#     sub_agents=[remote_weather],
# )
#
# # Run normally — the orchestrator doesn't know weather is remote!
# svc = InMemorySessionService()
# s = await svc.create_session(app_name="t", user_id="u", session_id="a2a")
# r = Runner(agent=orchestrator, app_name="t", session_service=svc)
# m = Content(role="user", parts=[Part.from_text(text="What's the weather in Tokyo?")])
# for e in r.run(user_id="u", session_id=s.id, new_message=m):
#     if e.content and e.content.parts and e.author != "user":
#         for p in e.content.parts:
#             if p.text: print(f"[{e.author}]: {p.text}")

print("A2A client pattern documented")
print("Key: RemoteA2aAgent looks identical to a local Agent in orchestrator code")'''),

    ("markdown", r'''## 6.5 Multi-Server Orchestration

### Pattern: Orchestrator with Multiple Remote Agents

```
                    Orchestrator Agent
                   /                  \
                  /                    \
    RemoteA2aAgent          RemoteA2aAgent
    (weather server)        (math server)
    localhost:8001           localhost:8002
```

The orchestrator's LLM sees both remote agents as available specialists
and routes based on the user's question — exactly like local sub_agents.

### When to Use Multi-Server Architecture

| Scenario | Multi-Server? | Why |
|----------|--------------|-----|
| All agents in one app | No | Keep it simple, use sub_agents |
| Agents built by different teams | Yes | Independent deployment |
| Agents need different resources | Yes | GPU agent on GPU machine |
| Agents in different languages | Yes | A2A is language-agnostic |
| Agents shared across orgs | Yes | A2A provides standard API |
| Agents need independent scaling | Yes | Scale each independently |'''),

    ("code", r'''# ====================================================================
# EXAMPLE 3: Multi-server orchestration — 2 remote agents
# ====================================================================

# from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
#
# # --- Two remote agents on different servers ---
# remote_weather = RemoteA2aAgent(
#     name="weather_service",
#     agent_card="http://weather-host:8001/.well-known/agent-card.json",
# )
#
# remote_math = RemoteA2aAgent(
#     name="math_service",
#     agent_card="http://math-host:8002/.well-known/agent-card.json",
# )
#
# # --- Orchestrator with both remote agents as sub_agents ---
# orchestrator = Agent(
#     name="smart_router",
#     model="gemini-2.5-flash",
#     instruction="""You are a smart routing assistant.
#     - Weather questions -> delegate to weather_service
#     - Math questions -> delegate to math_service
#     - General questions -> answer yourself""",
#     sub_agents=[remote_weather, remote_math],
# )
#
# # --- Run it — same code as any multi-agent system ---
# svc = InMemorySessionService()
# s = await svc.create_session(app_name="multi", user_id="u", session_id="multi")
# r = Runner(agent=orchestrator, app_name="multi", session_service=svc)
#
# # Ask a weather question -> routes to remote_weather
# m1 = Content(role="user", parts=[Part.from_text(text="Weather in Paris?")])
# for e in r.run(user_id="u", session_id=s.id, new_message=m1):
#     if e.content and e.content.parts and e.author != "user":
#         for p in e.content.parts:
#             if p.text: print(f"[{e.author}]: {p.text[:200]}")
#
# # Ask a math question -> routes to remote_math
# m2 = Content(role="user", parts=[Part.from_text(text="Solve 2x^2 + 5x - 3 = 0")])
# for e in r.run(user_id="u", session_id=s.id, new_message=m2):
#     if e.content and e.content.parts and e.author != "user":
#         for p in e.content.parts:
#             if p.text: print(f"[{e.author}]: {p.text[:200]}")

print("Multi-server orchestration pattern documented")'''),

    ("markdown", r'''## 6.6 Agent Card Inspection & Health Checks

### Why Health Checks Matter

In a distributed system, remote agents can:
- Go offline (server crash, deployment)
- Be slow (high load, network latency)
- Have incompatible versions

Before delegating to a remote agent, verify it's alive and capable.

### Agent Card as a Health Endpoint

The Agent Card endpoint (`/.well-known/agent-card.json`) serves double duty:
1. **Discovery** — what can this agent do? what skills does it have?
2. **Health check** — if this endpoint responds, the server is alive'''),

    ("code", r'''# ====================================================================
# EXAMPLE 4: Agent Card inspection & health check
# ====================================================================
# This code works without the a2a extra — uses standard HTTP

import urllib.request
import json

def fetch_agent_card(agent_url: str) -> dict:
    """Fetch and parse an A2A agent card from a remote server.
    
    The agent card is always at: /.well-known/agent-card.json
    This is the standard discovery endpoint in the A2A protocol.
    
    Args:
        agent_url: Base URL of the A2A server (e.g., "http://localhost:8001")
    
    Returns:
        dict: Parsed agent card with name, description, skills, capabilities
    """
    # Build the well-known URL
    card_url = f"{agent_url.rstrip('/')}/.well-known/agent-card.json"
    try:
        with urllib.request.urlopen(card_url, timeout=5) as resp:
            card = json.loads(resp.read())
            return card
    except Exception as e:
        return {"error": str(e), "status": "unreachable"}

def display_agent_card(card: dict):
    """Pretty-print an agent card for human inspection."""
    if "error" in card:
        print(f"  ERROR: {card['error']}")
        return
    
    print(f"  Name: {card.get('name', 'unknown')}")
    print(f"  Description: {card.get('description', 'N/A')}")
    print(f"  Version: {card.get('version', 'N/A')}")
    
    # Show capabilities
    caps = card.get('capabilities', {})
    print(f"  Capabilities:")
    print(f"    Streaming: {caps.get('streaming', False)}")
    print(f"    Push Notifications: {caps.get('pushNotifications', False)}")
    
    # Show skills
    skills = card.get('skills', [])
    print(f"  Skills ({len(skills)}):")
    for skill in skills:
        print(f"    - {skill.get('name', 'unnamed')}: {skill.get('description', 'N/A')[:80]}")

# --- Example: check a hypothetical remote agent ---
# card = fetch_agent_card("http://localhost:8001")
# print("Agent Card:")
# display_agent_card(card)

print("Agent card inspection functions ready")
print("Use: card = fetch_agent_card('http://host:port')")
print("     display_agent_card(card)")'''),

    ("code", r'''# ====================================================================
# EXAMPLE 5: Health check with retry logic
# ====================================================================
import time

def check_a2a_health(agent_url: str, max_retries: int = 3, timeout: int = 5) -> dict:
    """Check if a remote A2A agent is healthy, with retry logic.
    
    In production, you'd call this before delegating to a remote agent
    to avoid timeouts and improve user experience.
    
    Args:
        agent_url: Base URL of the A2A server
        max_retries: Number of retry attempts
        timeout: Timeout per attempt in seconds
    
    Returns:
        dict with status: 'healthy' | 'unhealthy' and details
    """
    card_url = f"{agent_url.rstrip('/')}/.well-known/agent-card.json"
    
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(card_url, timeout=timeout) as resp:
                card = json.loads(resp.read())
                return {
                    "status": "healthy",
                    "name": card.get("name"),
                    "skills_count": len(card.get("skills", [])),
                    "attempts": attempt + 1,
                }
        except urllib.error.HTTPError as e:
            # Server responded but with error
            return {"status": "unhealthy", "error": f"HTTP {e.code}", "attempts": attempt + 1}
        except Exception as e:
            # Connection failed — retry after backoff
            if attempt < max_retries - 1:
                wait = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"  Retry {attempt+1}/{max_retries} in {wait}s... ({e})")
                time.sleep(wait)
            else:
                return {"status": "unhealthy", "error": str(e), "attempts": max_retries}

# --- Example usage ---
# result = check_a2a_health("http://localhost:8001")
# print(f"Health: {result}")

print("Health check with retry ready")
print("Implements exponential backoff: 1s -> 2s -> 4s between retries")'''),

    ("markdown", r'''## 6.7 A2A vs MCP vs sub_agents — When to Use Which

ADK supports three ways to connect agents to external capabilities.
They serve different purposes:

| Feature | sub_agents | MCP (Model Context Protocol) | A2A |
|---------|-----------|------------------------------|-----|
| **What it connects** | Agent to Agent (in-process) | Agent to Tool Server | Agent to Agent (cross-network) |
| **Transport** | Python function calls | stdio/SSE (local) | HTTP/HTTPS (network) |
| **Scope** | Same process | Same machine or local network | Any network location |
| **Discovery** | Hardcoded in code | MCP server URL | Agent Card auto-discovery |
| **Language agnostic** | No (Python only) | Yes (MCP protocol) | Yes (A2A protocol) |
| **Use case** | Simple delegation | External tools (DB, API, file) | Distributed agent systems |
| **Complexity** | Lowest | Medium | Highest |

### Decision Tree

```
Need to connect to an external capability?
├── Is it a TOOL (database, API, file system)?
│   └── Use MCP (Model Context Protocol)
├── Is it another AGENT in the same app?
│   └── Use sub_agents (in-process delegation)
└── Is it another AGENT on a different server/machine?
    └── Use A2A (Agent-to-Agent protocol)
```

### Hybrid Architecture Example

```
Orchestrator Agent
├── sub_agents (local, in-process)
│   ├── summarizer (local Agent)
│   └── translator (local Agent)
├── MCP tools (local tool servers)
│   ├── database_toolset (MCP, stdio)
│   └── file_toolset (MCP, SSE)
└── RemoteA2aAgent (remote, cross-network)
    ├── weather_service (A2A, HTTP:8001)
    └── analytics_service (A2A, HTTP:8002)
```

All three can coexist in a single orchestrator!'''),

    ("markdown", r'''## 6.8 Security Considerations

### A2A Security Layers

| Layer | Threat | Mitigation |
|-------|--------|------------|
| **Transport** | Eavesdropping | HTTPS/TLS encryption |
| **Authentication** | Unauthorized access | API keys, OAuth 2.0, mTLS |
| **Authorization** | Privilege escalation | Per-skill access control |
| **Input validation** | Injection attacks | Validate all inputs before processing |
| **Rate limiting** | DoS attacks | Rate limit per client/IP |
| **Audit** | Compliance | Log all task submissions and results |

### Authentication Patterns

**Pattern 1: Shared Secret (API Key)**
```python
# Server side: verify API key in header
# Client side: RemoteA2aAgent with headers
remote = RemoteA2aAgent(
    name="secure_agent",
    agent_card="https://secure-server/.well-known/agent-card.json",
    headers={"X-API-Key": "your-secret-key"},
)
```

**Pattern 2: OAuth 2.0 (Enterprise)**
```python
# Use OAuth tokens that expire and can be refreshed
remote = RemoteA2aAgent(
    name="enterprise_agent",
    agent_card="https://corp-server/.well-known/agent-card.json",
    headers={"Authorization": f"Bearer {oauth_token}"},
)
```

**Pattern 3: mTLS (Mutual TLS)**
```python
# Both server and client verify each other's certificates
# Configure at the transport level, not in ADK code
# Use HTTPS with client certificates
```

### Best Practices

1. **Always use HTTPS in production** — never expose A2A over plain HTTP
2. **Restrict who can access** — use authentication on every endpoint
3. **Validate inputs** — the remote agent should sanitize all inputs
4. **Rate limit** — prevent any single client from overwhelming the server
5. **Log everything** — audit trail of all task submissions and results
6. **Version your agent card** — include version field for compatibility checks

---

## Summary

| Concept | Key Point |
|---------|-----------|
| **A2A Protocol** | Open standard for agent-to-agent communication over HTTP |
| **to_a2a(agent)** | Converts any ADK agent into an HTTP service (server side) |
| **RemoteA2aAgent** | Wraps a remote A2A endpoint — looks like a local Agent (client side) |
| **Agent Card** | JSON metadata at `/.well-known/agent-card.json` for discovery |
| **Task Lifecycle** | submitted -> working -> completed/failed/input-required |
| **Location transparency** | Orchestrator code is identical for local vs remote agents |
| **Multi-server** | Orchestrator can mix local + remote agents seamlessly |
| **Security** | HTTPS + auth + rate limiting + input validation |

### A2A Cheat Sheet

```
SERVER SIDE:
  agent = Agent(name="svc", model="gemini-2.5-flash", ...)
  app = to_a2a(agent)
  # Run: uvicorn server:app --port 8001

CLIENT SIDE:
  remote = RemoteA2aAgent(name="svc", agent_card="http://host:8001/...")
  orchestrator = Agent(name="main", sub_agents=[remote])
  # Run normally — remote looks like a local sub-agent

HEALTH CHECK:
  GET http://host:8001/.well-known/agent-card.json
  # If 200 OK -> healthy. If error -> unhealthy.
```

**Next:** [07_workflow_task_api.ipynb](./07_workflow_task_api.ipynb) — deterministic graph workflows.'''),
]

save('06_a2a_protocol.ipynb', nb06)
print("Notebook 06 complete")
