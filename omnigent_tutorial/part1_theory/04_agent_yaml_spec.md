# Chapter 04: Agent YAML Specification — Complete Reference

## Overview

Omnigent agents are defined in a single YAML file. The philosophy: **an agent is its config.** No separate "agent definition" vs "agent runtime" — the YAML file is the complete, self-contained specification.

```bash
omnigent run path/to/agent.yaml       # launch your agent
omnigent run agent.yaml --harness pi  # override harness
omnigent run agent.yaml --model gpt-5 # override model
```

## Minimal Agent

The shortest valid agent file:

```yaml
name: hello_agent
prompt: |
  You are a concise assistant. Answer directly and ask a follow-up
  question when the request is ambiguous.

executor:
  harness: claude-sdk
  model: claude-sonnet-4-6
```

That's it. `name`, `prompt`, and `executor` are all you need. Run it with `omnigent run hello.yaml`.

## Top-Level Fields — Complete Reference

| Field | Type | Required? | Purpose |
|---|---|---|---|
| `name` | string | Recommended | Stable identifier in sessions and logs |
| `prompt` | string | Usually | Inline system prompt |
| `instructions` | string | Optional | Inline instructions or path to file (e.g., `AGENTS.md`). Takes precedence over `prompt` |
| `executor` | object | Recommended | Harness, model, and auth settings |
| `tools` | object | Optional | MCP servers, Python functions, sub-agents, handoffs |
| `policies` | object | Optional | Agent-level guardrails |
| `params` | object | Optional | Typed user parameters available to tools/skills |
| `os_env` | object | Optional | Enables local OS tools (file read/write/edit/shell) |
| `terminals` | object | Optional | Named interactive terminal environments |
| `async` | bool | Optional | Expose async work tools? Default: `true` |
| `cancellable` | bool | Optional | Can the session be cancelled? Default: `true` |
| `timers` | bool | Optional | Expose timer tools? Default: `false` |
| `spawn` | bool | Optional | Allow agent to spawn child sessions? Default: `false` |

### `prompt` vs `instructions`

```yaml
# Option A: inline prompt
prompt: |
  You are a data analyst. Always cite sources.

# Option B: external file (resolved relative to YAML location)
instructions: ./AGENTS.md

# Option C: both — instructions wins
instructions: ./AGENTS.md
prompt: "This is ignored when instructions is present."
```

## Executor Configuration

The `executor` block selects the harness, model, and authentication.

### Basic

```yaml
executor:
  harness: claude-sdk
  model: claude-opus-4-8
```

### With Authentication

```yaml
executor:
  harness: claude-sdk
  model: claude-sonnet-4-6
  auth:
    type: databricks
    profile: oss
```

### Auth Types

| Auth Type | Use Case | Config |
|---|---|---|
| `databricks` | Databricks workspace model routing | `profile: oss` |
| `api_key` | Direct API key | `api_key: ${ANTHROPIC_API_KEY}` |
| `provider` | Reference a named provider from `~/.omnigent/config.yaml` | `name: my-openrouter` |
| (omitted) | Picks up from environment | `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` |

### Available Harnesses

| Harness ID | Underlying Agent | Transport | Notes |
|---|---|---|---|
| `claude-sdk` | Claude via Anthropic SDK | Python SDK | No CLI needed |
| `openai-agents` | GPT via OpenAI SDK | Python SDK | No CLI needed |
| `claude-native` | Claude Code CLI | PTY (tmux) | Needs `claude` on PATH |
| `codex-native` | Codex CLI | PTY (tmux) | Needs `codex` on PATH |
| `codex` | Codex via SDK | Python SDK | May also refer to Codex |
| `pi` | Pi CLI | PTY (tmux) | Needs `pi` on PATH |
| `cursor` | Cursor Agent | Proprietary | Needs `cursor-agent` + `CURSOR_API_KEY` |
| `antigravity` | Gemini via Antigravity SDK | Python SDK | Needs `google-antigravity` extra |
| `pi` (SDK) | Pi via SDK | Python SDK | — |

### Harness-Specific Notes

**Cursor:**
```yaml
executor:
  harness: cursor
  model: auto            # or: gpt-5, claude-sonnet-4-6
  auth:
    type: api_key
    api_key: ${CURSOR_API_KEY}
```
- No Databricks gateway support
- Model IDs are Cursor-specific, not Databricks-prefixed

**Antigravity (Gemini):**
```yaml
executor:
  harness: antigravity
  model: gemini-3.5-flash
  auth:
    type: api_key
    api_key: ${GEMINI_API_KEY}
```
- Install extra: `pip install "omnigent[antigravity]"`
- Can also use Vertex AI: `auth: {type: vertex_ai, project: ..., location: ...}`

## OS Environment (`os_env`)

When declared, the agent gets `sys_os_read`, `sys_os_write`, `sys_os_edit`, and `sys_os_shell` tools.

### Unsandboxed (trusted local development)

```yaml
os_env:
  type: caller_process
  cwd: .
  sandbox:
    type: none
```

### Sandboxed (recommended for untrusted or shared agents)

```yaml
os_env:
  type: caller_process
  cwd: .
  sandbox:
    type: linux_bwrap        # Linux: bubblewrap
    # type: darwin_seatbelt  # macOS: seatbelt
    write_paths:
      - ./output
      - /tmp/omnigent
    read_paths:
      - ./
    allow_network: false
```

### Platform-Agnostic (omit sandbox.type)

```yaml
os_env:
  type: caller_process
  cwd: .
  # sandbox.type omitted → Omnigent picks platform default
  # Linux → linux_bwrap, macOS → darwin_seatbelt
  sandbox:
    write_paths: [./output]
    allow_network: true
```

## Terminals

Named interactive shells for long-running processes (servers, watchers):

```yaml
terminals:
  shell:
    command: bash
    allow_cwd_override: true
    os_env:
      type: caller_process
      cwd: .
      sandbox:
        type: none

  python_repl:
    command: python
    allow_cwd_override: false
```

The agent uses `sys_terminal_launch` to open a named terminal.

## Tools

### Sub-Agents (declared)

```yaml
tools:
  coder:
    type: agent
    harness: claude-sdk
    model: claude-sonnet-4-6
    prompt: You are a coding specialist. Write clean, tested code.
    os_env:
      type: caller_process
      cwd: .
      sandbox: {type: none}

  reviewer:
    type: agent
    harness: openai-agents
    model: gpt-5
    prompt: You review code for correctness and style.
```

The orchestrator dispatches to sub-agents via `sys_session_send`.

### Pre-defined Agent Refs

```yaml
tools:
  agents:
    - claude_code     # references examples/polly/agents/claude_code/
    - codex           # references examples/polly/agents/codex/
    - pi              # references examples/polly/agents/pi/
```

### MCP Servers

```yaml
tools:
  github:
    type: mcp
    command: uv
    args:
      - run
      - python
      - -m
      - my_package.github_mcp
    tools:                    # restrict to specific tools
      - search_issues
      - get_pull_request

  docs:
    type: mcp
    url: https://example.com/mcp
    headers:
      Authorization: Bearer ${TOKEN}
```

### Python Function Tools

```yaml
tools:
  summarize_file:
    type: function
    description: Summarize a local text file.
    callable: my_package.tools.summarize_file
    parameters:
      type: object
      properties:
        path:
          type: string
          description: Path to the file
      required: [path]
```

### Tool Inheritance

```yaml
tools:
  researcher:
    type: agent
    prompt: Search and summarize.
    tools:
      my_tool: inherit        # inherits parent's my_tool
      new_tool:               # adds a new tool
        type: function
        callable: mymod.new_tool
```

## Policies (Agent-Level)

```yaml
policies:
  rate_limit:
    type: function
    handler: omnigent.policies.builtins.safety.max_tool_calls_per_session
    factory_params:
      limit: 100

  ask_shell:
    type: function
    handler: omnigent.policies.builtins.safety.ask_on_os_tools

  github_guard:
    type: function
    handler: omnigent.policies.builtins.github.github_policy
    factory_params:
      write_repos: [myorg/my-repo]
      write_branches: ["feature/*"]
```

## Guardrails

Guardrails are policy-like but enforced at the runner level (before reaching the policy engine):

```yaml
guardrails:
  ask_timeout: 86400          # ASK approvals valid for 24 hours
  policies:
    blast_radius:
      type: function
      function:
        path: omnigent.inner.nessie.policies.blast_radius
        arguments:
          gate_pushes: false   # don't ASK on git push

    spawn_bounds:
      type: function
      function:
        path: omnigent.inner.nessie.policies.spawn_bounds
        arguments:
          max_dispatches_per_turn: 5
          dispatch_tools: [sys_session_send, sys_session_create]
```

## Complete Example: A Custom Coding Agent

```yaml
spec_version: 1
name: my_coding_agent
description: A coding assistant with GitHub access and review capability.

# System prompt
prompt: |
  You are a coding assistant. Write clear, tested code.
  Always explain your reasoning before making changes.
  Ask clarifying questions when the request is ambiguous.

# Executor: run on Claude via Databricks
executor:
  harness: claude-sdk
  model: databricks-claude-sonnet-4-6
  auth:
    type: databricks
    profile: oss

# OS access: sandboxed
os_env:
  type: caller_process
  cwd: .
  sandbox:
    write_paths:
      - ./src
      - ./tests
    read_paths:
      - ./
    allow_network: true

# Interactive shell for long-running tasks
terminals:
  shell:
    command: bash
    allow_cwd_override: true

# Tools
tools:
  github:
    type: mcp
    command: npx
    args:
      - -y
      - "@anthropic/mcp-server-github"
    tools:
      - create_pull_request
      - get_issue
      - search_code

  reviewer:
    type: agent
    prompt: |
      You are a code reviewer. Check for:
      1. Correctness — does the code do what it claims?
      2. Style — does it follow project conventions?
      3. Tests — are edge cases covered?
      4. Security — any obvious vulnerabilities?
      Report issues; never make edits yourself.
    harness: openai-agents
    model: gpt-5

# Agent-level policies
policies:
  cost_cap:
    type: function
    handler: omnigent.policies.builtins.cost.cost_budget
    factory_params:
      max_cost_usd: 5.00
      ask_thresholds_usd: [3.00]

  safe_shell:
    type: function
    handler: omnigent.policies.builtins.safety.ask_on_os_tools

# Guardrails
guardrails:
  ask_timeout: 3600
  policies:
    blast_radius:
      type: function
      function:
        path: omnigent.inner.nessie.policies.blast_radius
        arguments:
          gate_pushes: true

# Misc
async: true
cancellable: true
```

## CLI Overrides

The YAML is the source of truth, but CLI flags can override for one-off runs:

```bash
omnigent run agent.yaml --harness pi              # switch harness
omnigent run agent.yaml --model gpt-5             # switch model
omnigent run agent.yaml --harness pi --model ...  # both
```

## Summary

The Agent YAML spec is the heart of Omnigent's composition story. A single file defines:
- **What** the agent does (prompt/instructions)
- **How** it runs (executor: harness, model, auth)
- **What it can touch** (os_env, sandbox)
- **What tools it has** (sub-agents, MCP, Python functions)
- **What rules it follows** (policies, guardrails)

Swap the harness, swap the model, or clone the file for a variant — no code rewrites needed.

---

**Previous:** [Chapter 03 — Omnigent Architecture](./03_omnigent_architecture.md)
**Next:** [Chapter 05 — Policies & Governance](./05_policies_and_governance.md)
