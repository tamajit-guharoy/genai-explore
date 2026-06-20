# Chapter 03: Omnigent Architecture

## Overview

Omnigent's architecture has two primary components:

```
┌──────────────────────────────────────────────────────┐
│                    OMNIGENT SERVER                     │
│                                                        │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐  │
│  │ Session  │  │ Policy   │  │ Collaboration      │  │
│  │ Manager  │  │ Engine   │  │ (shared URLs,      │  │
│  │          │  │          │  │  comments, forks)   │  │
│  └────┬─────┘  └────┬─────┘  └────────┬───────────┘  │
│       │             │                │                │
│  ┌────▼─────────────▼────────────────▼───────────┐   │
│  │              SQLite Database                    │   │
│  │  (sessions, messages, files, policies, auth)    │   │
│  └────────────────────────────────────────────────┘   │
│                                                        │
│  Reached via: http://localhost:6767 (web UI)           │
│               REST API, macOS Desktop App, Mobile       │
├──────────────────────────────────────────────────────┤
│                    OMNIGENT RUNNER                     │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Agent Executor Loop                   │ │
│  │                                                    │ │
│  │  prompt → model → tool_calls → execute → repeat    │ │
│  │                                                    │ │
│  │  Harness-specific adapter:                         │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │ │
│  │  │claude-sdk│ │openai-   │ │claude-native     │  │ │
│  │  │          │ │agents    │ │codex-native       │  │ │
│  │  │          │ │          │ │pi, cursor, ...    │  │ │
│  │  └──────────┘ └──────────┘ └──────────────────┘  │ │
│  └──────────────────────────────────────────────────┘ │
│                                                        │
│  ┌──────────────────────────────────────────────────┐ │
│  │              Omnibox Sandbox                       │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────────────┐  │ │
│  │  │Linux:    │ │macOS:    │ │Cloud:            │  │ │
│  │  │bubblewrap│ │seatbelt  │ │Modal, Daytona,   │  │ │
│  │  │          │ │          │ │Islo              │  │ │
│  │  └──────────┘ └──────────┘ └──────────────────┘  │ │
│  └──────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────┘
```

## The Runner

The **runner** is the execution environment for a single agent. It:

1. **Wraps the agent harness** — translates tool calls from model format to Omnigent's internal protocol and back
2. **Enforces policies** — checks every tool call against active policies before execution
3. **Manages the sandbox** — all OS operations go through the sandbox layer
4. **Streams to the server** — UI updates, file state, terminal output flow to the server in real time

### Runner Types

| Runner | Where it runs | When to use |
|---|---|---|
| **Local** | Your machine | Development, trusted environments |
| **Managed host** | Cloud sandbox (Modal, Daytona, Islo) | Isolation, no local resources needed |
| **Server-provisioned** | Auto-spawned by server per-session | Team server with centralized sandboxing |

### How Runners Connect to Agents

The runner doesn't know about Claude Code or Codex directly. It uses **harness adapters**:

```
Runner
  └─ Harness Adapter (implements Agent Protocol)
       ├─ claude-sdk      → talks to Claude via Anthropic SDK
       ├─ openai-agents   → talks to GPT via OpenAI SDK
       ├─ claude-native   → launches `claude` CLI in a PTY
       ├─ codex-native    → launches `codex` CLI in a PTY
       ├─ pi              → launches `pi` CLI in a PTY
       ├─ cursor          → talks to cursor-agent
       └─ antigravity     → talks to Gemini via Antigravity SDK
```

This is the **composition** pillar: swap `claude-sdk` for `openai-agents` and the rest of your agent YAML stays the same.

## The Server

The **server** is a persistent process (default: `localhost:6767`) that:

- **Stores durable state** — SQLite database with sessions, messages, files, auth config
- **Enforces server-wide policies** — admin-set rules that apply to all agents
- **Manages sessions** — creates, routes, and garbage-collects sessions
- **Serves the web UI** — the built-in React UI for chat, sub-agents, terminals, and settings
- **Exposes a REST API** — for the desktop app, mobile app, and programmatic access
- **Handles collaboration** — shared session URLs, comments, forks
- **Provides auth** — SSO, API key validation, user management

### Server State

Everything lives in SQLite, which means:
- **Safe to cycle** — stop the server, start it, all sessions survive
- **Version-aware** — after `omni upgrade`, the server detects its recorded version no longer matches the installed package and respawns on the new code
- **No process-memory dependency** — no data loss on restart

```bash
# State locations
~/.omnigent/chat.db          # Main session database
~/.omnigent/local_server.pid  # Track running server
~/.omnigent/local_server.sig  # Version + auth signature
```

### Server Lifecycle

```bash
omni                    # Starts server + opens web UI (or reuses existing)
omni server start       # Start server in background
omni server stop        # Stop server
omni server status      # Check if running
omni server --config    # Start with custom config
```

## The Session Model

Every agent conversation is a **session**. Sessions are:

| Property | Behavior |
|---|---|
| **Persistent** | Stored in SQLite, survive server restart |
| **Shareable** | Generate a URL, teammates can view/comment/co-drive |
| **Cross-device** | Start on terminal, continue on phone, pick up on desktop |
| **Forkable** | Clone a session to explore a different path |
| **Policy-aware** | Session-level policies stack on top of agent and server policies |

### Session Components

```
Session
├── Messages (user, assistant, system, tool calls/results)
├── Sub-agents (child sessions, each with their own messages)
├── Terminals (interactive shell sessions)
├── Files (the working directory state)
├── Active policies (session-level overrides)
└── Metadata (model, harness, timestamps, cost tracking)
```

## Policy Architecture

Policies are the **control** pillar. They're evaluated at specific enforcement points:

```
Tool Call Request
    │
    ▼
┌─────────────────┐
│ Session Policies │  ← User-set, evaluated FIRST
└────────┬────────┘
         │ (if not DENIED)
         ▼
┌─────────────────┐
│ Agent Policies   │  ← Defined in agent YAML
└────────┬────────┘
         │ (if not DENIED)
         ▼
┌─────────────────┐
│ Server Policies  │  ← Admin-set, evaluated LAST
└────────┬────────┘
         │
    ┌────▼────┐
    │ ALLOW   │ → execute
    │ DENY    │ → block with error
    │ ASK     │ → pause for user approval
    └─────────┘
```

**Short-circuit rule:** A DENY from any level stops evaluation immediately. ASK pauses and waits for human input. ALLOW passes through to the next level.

## Sandbox Architecture (Omnibox)

Every OS operation goes through the sandbox:

```
Agent requests: "write file at /home/user/config.json"
    │
    ▼
┌──────────────┐
│ Sandbox      │  Check: is this path in write_paths?
│ Interceptor  │  Check: is this a blocked operation?
└──────┬───────┘
       │
  ┌────▼────┐
  │ ALLOW   │ → execute on host (mapped path)
  │ DENY    │ → error returned to agent
  └─────────┘
```

**Secret brokering:** Environment variables with secrets are never visible to the agent. The sandbox injects them at the egress proxy only when an approved operation needs them:

```
Agent: "git push"           → no GitHub token in env
Sandbox: detects git push   → injects GITHUB_TOKEN at egress
         target is allowed  → push succeeds
```

## Harness Adapter Details

### claude-sdk / openai-agents (Programmatic)

These use the Anthropic and OpenAI Python SDKs directly. No subprocess, no PTY. The runner calls the SDK, handles tool-use loops, and streams tokens.

**Advantages:** Fast, reliable, no subprocess management
**Required:** API key in environment or provider config

### claude-native / codex-native / pi (Terminal)

These launch the actual CLI binaries in a PTY (pseudo-terminal). The runner sends prompts and captures output.

**Advantages:** Uses exactly the same binary the developer already has, including any custom config/MCP servers/skills
**Required:** CLI binary on PATH, tmux (for interactive terminal in web UI)

### cursor

Talks to `cursor-agent` via its own protocol. No Databricks gateway — Cursor uses its own backend. Authentication via `CURSOR_API_KEY`.

### antigravity

Uses Google's Antigravity SDK for Gemini models. Can also drive Claude/GPT through Gemini's model routing. Authentication via `GEMINI_API_KEY` or Vertex AI.

## Configuration Files

| File | Location | Purpose |
|---|---|---|
| `~/.omnigent/config.yaml` | User home | Providers, default model, UI settings |
| `~/.omnigent/.env` | User home | API keys (ANTHROPIC_API_KEY, OPENAI_API_KEY, etc.) |
| `server_config.yaml` | Project or system | Server-wide policies, auth, managed hosts |
| `agent.yaml` | Per-agent | Agent definition (prompt, harness, tools, policies) |

## Summary

Omnigent's architecture separates concerns cleanly:

- **Runner** = execution environment, one per agent
- **Server** = durable state, web UI, REST API, collaboration
- **Policies** = three-level governance (session → agent → server)
- **Sandbox** = OS-level isolation with secret brokering
- **Harness adapters** = uniform interface over different agent CLIs/SDKs

---

**Previous:** [Chapter 02 — What Is a Meta-Harness?](./02_what_is_a_meta_harness.md)
**Next:** [Chapter 04 — Agent YAML Specification](./04_agent_yaml_spec.md)
