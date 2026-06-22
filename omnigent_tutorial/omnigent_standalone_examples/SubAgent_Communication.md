# Sub-Agent Communication in Omnigent

## Overview

Omnigent orchestrators coordinate work across multiple sub-agents using an **inbox-driven messaging model**. The orchestrator delegates tasks, sleeps while sub-agents work, and wakes up when results arrive — no polling needed.

```
Orchestrator                          Sub-Agent
    │                                      │
    ├── sys_session_send(task) ───────────►│
    │                                      ├── works...
    │                                      ├── works...
    │                                      ├── done
    │◄── sys_read_inbox returns result ────│
    │                                      │
    ├── review, loop, or present           │
```

---

## Core Tools

| Tool | Purpose | Used By |
|---|---|---|
| `sys_session_send(name, task)` | Dispatch work to a named sub-agent | Orchestrator |
| `sys_read_inbox()` | Block until a sub-agent completes and retrieve its result | Orchestrator |

---

## Configuration Requirements

For an agent to act as an orchestrator with sub-agents, these top-level flags are required:

```yaml
spawn: true      # Allow spawning child sessions
async: true      # Enable async work tools (wait for results)
cancellable: true # Allow cancellation of in-flight sub-agents
```

Sub-agents are declared in the `tools:` section with `type: agent`:

```yaml
tools:
  coder:
    type: agent                    # Declares this as a sub-agent
    description: Writes the code.  # Visible to the orchestrator
    harness: claude-sdk            # Can use different harness than orchestrator
    model: claude-sonnet-4-6       # Can use different model
    prompt: |
      # Your sub-agent system prompt here
    os_env:                        # Sub-agents can have their own OS access
      type: caller_process
      cwd: .
      sandbox: { type: none }
```

---

## Communication Patterns

### 1. Sequential — Single Sub-Agent

Orchestrator delegates to one sub-agent, waits, then presents:

```
1. PLAN the work
2. DISPATCH to `coder` via sys_session_send
3. WAIT via sys_read_inbox
4. REVIEW the result
5. PRESENT to user
```

**Example:** `27_orchestrator_single_subagent.yaml`

### 2. Sequential — Pipeline (Cross-Vendor Review)

Orchestrator chains sub-agents in sequence: code first, then review:

```
1. PLAN the implementation
2. DISPATCH to `coder` (Claude) via sys_session_send
3. WAIT via sys_read_inbox
4. DISPATCH to `reviewer` (GPT) for code review
5. WAIT via sys_read_inbox
6. If APPROVED → present; if NEEDS WORK → loop back to coder
```

**Key principle:** The reviewer is always a **different vendor** than the coder, catching vendor-specific blind spots.

**Example:** `29_orchestrator_cross_vendor_review.yaml`

### 3. Parallel — Multiple Sub-Agents

Orchestrator dispatches to multiple sub-agents simultaneously, then collects all results:

```
1. PLAN the feature
2. DISPATCH to `coder` AND `writer` simultaneously (both via sys_session_send)
3. WAIT for BOTH to complete (sys_read_inbox × 2)
4. SYNTHESIZE results
5. PRESENT to user
```

**Example:** `28_orchestrator_two_subagents.yaml`

---

## Inbox-Driven Wake (No Polling)

The orchestrator's LLM call is **suspended** after calling `sys_session_send`. When the sub-agent finishes, the runtime places the result in the orchestrator's inbox and **resumes** the orchestrator's LLM call. The orchestrator then calls `sys_read_inbox` to retrieve the result.

This is fundamentally different from polling (`while not done: check()`):

| Approach | Mechanism | Cost |
|---|---|---|
| **Polling** | LLM repeatedly asks "are you done yet?" | Wastes tokens, slow |
| **Inbox-driven** | LLM suspended until notification | Zero waste, instant wake |

---

## Sub-Agent Isolation

Each sub-agent runs in its own isolated session with:

- **Independent tool access** — each sub-agent can have its own `os_env`, `tools`, and `policies`
- **Different harness/model** — a sub-agent can use a completely different provider than the orchestrator
- **Own worktree** — `git worktree` isolation prevents file conflicts between parallel sub-agents

```yaml
tools:
  # Orchestrator: Claude
  coder:
    type: agent
    harness: claude-sdk          # ← different from reviewer
    model: claude-sonnet-4-6
    os_env:
      type: caller_process
      cwd: .
      sandbox: { type: none }

  # Reviewer: GPT (different vendor)
  reviewer:
    type: agent
    harness: openai-agents       # ← different from coder
    model: gpt-5
    # No os_env — reviewer is read-only, never touches the filesystem
```

---

## Summary

| Pattern | Sub-Agents | Dispatch | Collection | Use Case |
|---|---|---|---|---|
| Single | 1 | Sequential | 1× read | Simple delegation |
| Pipeline | 2+ | Sequential | N× read | Code → Review → ... |
| Parallel | 2+ | Simultaneous | N× read (any order) | Code + Docs + Tests |

All patterns rely on `sys_session_send` + `sys_read_inbox` with inbox-driven wake for efficient, polling-free coordination.
