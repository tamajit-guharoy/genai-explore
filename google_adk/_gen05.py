#!/usr/bin/env python3
"""Generate notebook 05 with deep theory + multiple examples."""
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

# Using r'''...''' so """ docstrings inside code cells are safe
nb05 = [
    ("markdown", r'''# 05 — Callbacks, State, Memory, Artifacts & Streaming

## What You'll Learn

This notebook is the **deepest dive into ADK's runtime infrastructure**:

1. **Callbacks** — 6+ hooks to intercept every stage of the agent loop
2. **Callback Return Values** — how returning None vs Content vs dict changes behavior
3. **Session State** — structured data shared across agents and turns
4. **Memory Service** — persistent facts that survive across sessions
5. **Artifacts** — file I/O for agents (images, PDFs, generated content)
6. **Streaming** — real-time event processing for responsive UX
7. **Context Object** — what's available inside callbacks

> **Prerequisites:** Notebooks 02 (Agent), 03 (Tools), 04 (Multi-agent)

---

## The Big Picture: ADK Runtime Architecture

```
User Message
    |
    v
+--------------------------------------------------------------------+
|  Runner                                                            |
|  +-----------+    +--------------+    +-------------+              |
|  |  before_   |--->|   Agent      |--->|  after_     |              |
|  |  agent_cb  |    |  (LLM loop)  |    |  agent_cb   |              |
|  +-----------+    +--------------+    +-------------+              |
|                   |              |                                   |
|                   v              v                                   |
|              +---------+  +----------+                               |
|              |before_  |  |before_   |                               |
|              |model_cb |  |tool_cb   |                               |
|              +---------+  +----------+                               |
|                   |              |                                   |
|                   v              v                                   |
|              +---------+  +----------+                               |
|              |after_   |  |after_    |                               |
|              |model_cb |  |tool_cb   |                               |
|              +---------+  +----------+                               |
|                                                                    |
|  +-------------------+  +--------------------+                     |
|  |  Session Service   |  |  Memory Service    |                    |
|  |  (per-chat state)  |  |  (cross-chat facts)|                    |
|  +-------------------+  +--------------------+                     |
|                                                                    |
|  +-------------------+                                             |
|  |  Artifact Service  |  (files: images, PDFs, etc.)              |
|  +-------------------+                                             |
+--------------------------------------------------------------------+
    |
    v
Events (streamed to user)
```

**Key insight:** The Runner is NOT just "call the LLM and return." It's a
full execution engine with hooks at every step, state management, and
file storage. Mastering these features is what separates toy agents
from production agents.'''),

    ("code", IMP_CELL),
    ("code", ENV_CELL),
    ("code", r'''# --- Callback-specific imports ---
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.context import Context
from google.adk.memory.in_memory_memory_service import InMemoryMemoryService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
print("Callback/memory/artifact imports ready")'''),

    ("markdown", r'''## 5.1 Callbacks: The Interception System

### What Are Callbacks?

Callbacks are **middleware functions** that ADK calls at specific points
during agent execution. Think of them as interceptors in a request pipeline —
they can observe, modify, block, or replace any step.

### Why Callbacks Matter

| Use Case | Callback | Example |
|----------|----------|---------|
| **Observability** | all 6 | Log every LLM call, tool invocation, timing |
| **Security** | before_tool | Block `os.system("rm -rf /")` |
| **Preprocessing** | before_model | Inject user profile into every LLM call |
| **Postprocessing** | after_model | Redact PII from LLM responses |
| **Caching** | before_agent | Return cached response, skip LLM entirely |
| **Guardrails** | after_model | Check response for toxicity before showing user |
| **Audit trail** | all 6 | Record every action for compliance |

### The 6 Core Callbacks (ADK 2.x signatures)

```
Agent lifecycle:
  before_agent(ctx: Context) -> Optional[Content]
      Called ONCE before agent starts. Return Content to skip agent entirely.
  after_agent(ctx: Context) -> Optional[Content]
      Called ONCE after agent finishes. Return Content to override final output.

Model (LLM) interaction:
  before_model(ctx: Context, llm_request: LlmRequest) -> Optional[LlmResponse]
      Called before EACH LLM API call. Return LlmResponse to skip the call.
  after_model(ctx: Context, llm_response: LlmResponse) -> Optional[LlmResponse]
      Called after EACH LLM API call. Return LlmResponse to replace the output.

Tool execution:
  before_tool(tool: BaseTool, args: dict, ctx: Context) -> Optional[dict]
      Called before EACH tool runs. Return dict to skip tool execution.
  after_tool(tool: BaseTool, args: dict, ctx: Context, result: dict) -> Optional[dict]
      Called after EACH tool runs. Return dict to replace the tool result.
```

### The Golden Rule of Callbacks

**Return `None`** -> proceed normally (most common case)
**Return a value** -> SKIP that step and use the returned value instead

This "return to override" pattern is the most powerful feature of callbacks:
- Return `Content` from `before_agent` -> agent never runs, your Content is the response
- Return `LlmResponse` from `before_model` -> LLM API never called, your response is used
- Return `dict` from `before_tool` -> tool function never runs, your dict is the result'''),

    ("markdown", r'''## 5.2 Example 1: Full Callback Tracing (Observability)

This example attaches ALL 6 callbacks to a single agent and traces every
step of execution. This is what you'd use for debugging and logging.'''),

    ("code", r'''# ====================================================================
# EXAMPLE 1: Full callback tracing -- observe every step of agent execution
# ====================================================================

# --- Agent lifecycle callbacks ---
def before_agent(ctx: Context):
    """Called ONCE before the agent starts processing.
    Return None = proceed normally.
    Return Content = skip the agent entirely (use this for caching).
    """
    print(f"  [BEFORE_AGENT] Starting: {ctx.agent.name}")
    return None  # Proceed normally

def after_agent(ctx: Context):
    """Called ONCE after the agent finishes.
    Return None = keep agent output.
    Return Content = replace the agent final output.
    """
    print(f"  [AFTER_AGENT] Finished: {ctx.agent.name}")
    return None

# --- Model (LLM) callbacks ---
def before_model(ctx: Context, llm_request):
    """Called BEFORE each LLM API call.
    This fires on EVERY iteration of the agent loop (once per LLM call).
    Return None = call the LLM normally.
    Return LlmResponse = skip the LLM call entirely (use for caching).
    """
    n_messages = len(llm_request.contents) if llm_request else 0
    print(f"    [BEFORE_MODEL] Sending {n_messages} messages to LLM")
    return None

def after_model(ctx: Context, llm_response):
    """Called AFTER each LLM API call.
    Inspect what the LLM returned before it gets processed.
    Return None = use LLM response.
    Return LlmResponse = replace the LLM response.
    """
    if llm_response and llm_response.content:
        text_len = sum(len(p.text) for p in llm_response.content.parts if p.text)
        fc_count = len(llm_response.function_calls) if hasattr(llm_response, 'function_calls') else 0
        print(f"    [AFTER_MODEL] Got {text_len} chars, {fc_count} function calls")
    return None

# --- Tool callbacks ---
def before_tool(tool, args: dict, ctx: Context):
    """Called BEFORE each tool executes.
    This is your SECURITY GATE -- inspect args and block dangerous calls.
    Return None = run the tool.
    Return dict = skip the tool, use this dict as the result.
    """
    print(f"      [BEFORE_TOOL] {tool.name}({str(args)[:80]})")
    return None

def after_tool(tool, args: dict, ctx: Context, result: dict):
    """Called AFTER each tool returns.
    Inspect or sanitize tool results before they go back to the LLM.
    Return None = use tool result.
    Return dict = replace the tool result.
    """
    print(f"      [AFTER_TOOL] {tool.name} returned: {str(result)[:100]}")
    return None

print("All 6 callbacks defined")'''),

    ("code", r'''# --- Run agent with all 6 callbacks attached ---
async def callback_tracing_demo():
    # Simple math tools for the demo
    def add(a: int, b: int) -> dict:
        """Add two numbers."""
        return {"result": a + b}

    def multiply(x: int, y: int) -> dict:
        """Multiply two numbers."""
        return {"result": x * y}

    agent = Agent(
        name="traced_calc",
        model="gemini-2.5-flash",
        instruction="Use add and multiply tools to answer math questions. Show your work.",
        tools=[add, multiply],
        # --- Attach all 6 callbacks ---
        before_agent_callback=before_agent,
        after_agent_callback=after_agent,
        before_model_callback=before_model,
        after_model_callback=after_model,
        before_tool_callback=before_tool,
        after_tool_callback=after_tool,
    )

    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="cb1")
    r = Runner(agent=agent, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(text="What is (15 + 27) x 3?")])

    print("=== Full Callback Trace ===\n")
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text:
                    print(f"\n>>> FINAL ANSWER: {p.text}")

await callback_tracing_demo()'''),

    ("markdown", r'''## 5.3 Example 2: Callback Return Values -- Override & Intercept

The most powerful feature of callbacks is the ability to **skip** a step
by returning a value. Let's see each pattern in action.

### Pattern A: before_agent returns Content -> Caching

If the agent's response was cached, return it from `before_agent` to skip
the entire agent execution. This saves LLM API costs.

### Pattern B: before_tool returns dict -> Security Gate

Block dangerous tool calls by returning an error dict. The tool function
never runs -- the LLM sees your error dict instead.

### Pattern C: after_model returns LlmResponse -> Guardrail

Inspect the LLM's response and replace it if it violates safety rules.'''),

    ("code", r'''# ====================================================================
# EXAMPLE 2A: Caching with before_agent callback
# ====================================================================

# Simulate a cache: store responses keyed by user message
response_cache = {}

def caching_before_agent(ctx: Context):
    """Check if we have seen this question before. If so, return cached answer."""
    print(f"  [CACHE_CHECK] Checking cache for: {ctx.agent.name}")
    # In production, you would extract the user message and check Redis:
    #   cached = redis.get(user_message)
    #   if cached:
    #       return Content(role="model", parts=[Part.from_text(text=cached)])
    return None  # No cache hit -> proceed normally

agent_cached = Agent(
    name="cached_agent",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant. Answer concisely.",
    before_agent_callback=caching_before_agent,
)

async def cache_demo():
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="cache")
    r = Runner(agent=agent_cached, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(text="What is photosynthesis?")])
    print("=== Caching Callback Demo ===\n")
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"Agent: {p.text[:300]}")

await cache_demo()'''),

    ("code", r'''# ====================================================================
# EXAMPLE 2B: Security gate with before_tool callback
# ====================================================================

# A "dangerous" tool that could delete files
def delete_file(path: str) -> dict:
    """Delete a file at the given path."""
    return {"status": "deleted", "path": path}

# Blocked paths -- never allow deletion of these
BLOCKED_PATHS = ["/etc", "/system", "C:\\Windows", ".env", ".git"]

def security_before_tool(tool, args: dict, ctx: Context):
    """Security gate: block dangerous file operations."""
    if tool.name == "delete_file":
        path = args.get("path", "")
        for blocked in BLOCKED_PATHS:
            if blocked in path:
                print(f"  [BLOCKED] Rejected deletion of: {path}")
                # Returning a dict SKIPS the tool entirely.
                # The LLM sees this error message instead of the tool result.
                return {"error": f"SECURITY: Cannot delete protected path: {path}"}
    return None  # Safe -> proceed

agent_secured = Agent(
    name="file_manager",
    model="gemini-2.5-flash",
    instruction="You have a delete_file tool. Help the user manage files.",
    tools=[delete_file],
    before_tool_callback=security_before_tool,
)

async def security_demo():
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="sec")
    r = Runner(agent=agent_secured, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(
        text="Please delete the file at C:\\Windows\\system32\\config\\sam"
    )])
    print("=== Security Gate Demo ===\n")
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"Agent: {p.text[:300]}")

await security_demo()'''),

    ("markdown", r'''## 5.4 Session State -- The Agent's Working Memory

### What Is Session State?

Every session has a `.state` dictionary that persists across turns within
that session. It's the primary mechanism for:

- **Pipeline data passing**: Agent A writes, Agent B reads
- **User context**: Track user preferences within a conversation
- **Intermediate results**: Store computed values for later turns
- **Flow control**: Use state values to drive conditional logic

### State Lifecycle

```
create_session() -> state = {}
  Turn 1: user message -> agent runs -> state["key"] = value
  Turn 2: agent sees state["key"] from Turn 1
  Turn 3: state still persists
  ...until session is deleted
```

### State vs Memory -- Critical Distinction

| Feature | Session State | Memory Service |
|---------|--------------|----------------|
| **Scope** | Single session (one chat) | Across ALL sessions |
| **Lifetime** | Until session ends | Permanent (until explicitly deleted) |
| **Access** | Direct dict: `ctx.state["key"]` | Via `search_memory()` API |
| **Use for** | Pipeline data, temp vars | User name, long-term preferences |
| **Example** | `"current_topic": "quantum physics"` | `"user_name": "Alice"` |

### How output_key Connects to State

When you set `output_key="result"` on an Agent, ADK automatically saves
the agent's final text response to `session.state["result"]`. This is the
simplest way to pass data between pipeline stages.'''),

    ("code", r'''# ====================================================================
# EXAMPLE 3: Session state -- pre-populate, read, and write
# ====================================================================

async def state_demo():
    agent = Agent(
        name="stateful_bot",
        model="gemini-2.5-flash",
        instruction="""You are a personal assistant.
The user name and preferences are in your context (session state).
Use them to personalize responses. Be warm and specific.""",
        output_key="last_response",  # Auto-saves response to state["last_response"]
    )

    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="state1")

    # --- Pre-populate state BEFORE running the agent ---
    # This simulates loading user profile from a database
    s.state["user_name"] = "Alice"
    s.state["favorite_language"] = "Python"
    s.state["skill_level"] = "intermediate"
    print(f"Pre-populated state: {dict(s.state)}\n")

    r = Runner(agent=agent, app_name="t", session_service=svc)

    # --- Turn 1: Agent sees the pre-populated state ---
    m1 = Content(role="user", parts=[Part.from_text(
        text="Suggest a project I could work on this weekend."
    )])
    print("Turn 1: Suggest a project...\n")
    for e in r.run(user_id="u", session_id=s.id, new_message=m1):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"  Agent: {p.text[:400]}")

    # --- Read state AFTER execution ---
    # Note: get_session is ASYNC in ADK 2.x!
    sess = await svc.get_session(app_name="t", user_id="u", session_id="state1")
    print(f"\nState after Turn 1: {dict(sess.state)}")
    # "last_response" was auto-added by output_key!

    # --- Turn 2: State persists, agent remembers ---
    m2 = Content(role="user", parts=[Part.from_text(
        text="Actually, can you make it simpler? I am short on time."
    )])
    print("\nTurn 2: Make it simpler...\n")
    for e in r.run(user_id="u", session_id=s.id, new_message=m2):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"  Agent: {p.text[:400]}")

await state_demo()'''),

    ("markdown", r'''## 5.5 Memory Service -- Cross-Session Persistence

### The Problem Memory Solves

Session state dies when the session ends. But users expect agents to
"remember" things across conversations:

```
Monday: "My name is Alice and I love hiking"
  -> session.state["name"] = "Alice"  (dies when session ends)

Wednesday (new session): "Plan my weekend"
  -> Agent does not know about hiking... unless you use Memory Service
```

### How Memory Service Works

```
Session 1 ---\
              --> Memory Service --> Session 3 (recall)
Session 2 ---/    (stores facts)     "You like hiking, right?"
```

1. After each session, ADK can extract facts and store them in Memory
2. Before a new session, ADK searches memory for relevant facts
3. Relevant facts are injected into the agent context

### ADK Memory APIs

| Method | Purpose |
|--------|---------|
| `memory.add_session(session)` | Extract and store facts from a completed session |
| `memory.search_memory(query)` | Search stored facts by semantic similarity |
| `preload_memory` tool | Auto-inject relevant memories into agent context |
| `load_memory` tool | Let agent search memory on-demand |

### InMemoryMemoryService vs Production

- `InMemoryMemoryService` -- stores in RAM, lost on restart (good for dev)
- Production: Use Vertex AI Memory Service or custom database-backed'''),

    ("code", r'''# ====================================================================
# EXAMPLE 4: Memory Service -- facts that survive across sessions
# ====================================================================

async def memory_demo():
    # --- Create a shared memory service ---
    # This persists across sessions (unlike session state)
    memory_service = InMemoryMemoryService()

    agent = Agent(
        name="memory_bot",
        model="gemini-2.5-flash",
        instruction="You are a helpful assistant. Remember what users tell you.",
    )

    # --- Session 1: User tells the agent personal facts ---
    svc = InMemorySessionService()
    s1 = await svc.create_session(app_name="app", user_id="alice", session_id="chat_monday")
    r1 = Runner(agent=agent, app_name="app", session_service=svc,
                memory_service=memory_service)  # Attach memory service!

    m = Content(role="user", parts=[Part.from_text(
        text="Hi! My name is Alice, I work as a data scientist, and I love hiking on weekends."
    )])
    print("=== Session 1 (Monday) ===")
    print("User: Hi! My name is Alice, I work as a data scientist, and I love hiking on weekends.\n")
    for e in r1.run(user_id="alice", session_id="chat_monday", new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"Agent: {p.text[:300]}")

    # --- Store session 1 in memory ---
    # add_session_to_memory extracts facts from the conversation and saves them
    await memory_service.add_session_to_memory(s1)
    print("\n[Memory: Session 1 facts stored]\n")

    # --- Session 2 (Wednesday, NEW session): Agent should remember! ---
    s2 = await svc.create_session(app_name="app", user_id="alice", session_id="chat_wednesday")
    r2 = Runner(agent=agent, app_name="app", session_service=svc,
                memory_service=memory_service)

    # Search memory for relevant facts before responding
    # search_memory returns a SearchMemoryResponse with .memories list
    response = await memory_service.search_memory(
        app_name="app",
        user_id="alice",
        query="What does Alice like to do on weekends?"
    )
    memories = response.memories if hasattr(response, 'memories') else []
    print(f"=== Memory search results: {len(memories)} memories found ===")
    for mem in memories:
        # Each memory has .content with .parts
        parts_text = []
        if hasattr(mem, 'content') and mem.content:
            for p in (mem.content.parts or []):
                if p.text:
                    parts_text.append(p.text)
        print(f"  Memory: {' '.join(parts_text)[:150]}...")

    # Now ask the question -- agent can use memories
    m2 = Content(role="user", parts=[Part.from_text(
        text="Can you suggest a weekend activity for me?"
    )])
    print("\n=== Session 2 (Wednesday) ===")
    print("User: Can you suggest a weekend activity for me?\n")
    for e in r2.run(user_id="alice", session_id="chat_wednesday", new_message=m2):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"Agent: {p.text[:300]}")

await memory_demo()'''),

    ("markdown", r'''## 5.6 Artifacts -- File I/O for Agents

### What Are Artifacts?

Artifacts are **files** that agents can create, read, and share. Unlike
session state (which stores strings/dicts), artifacts store binary data:

- Images (PNG, JPEG)
- PDFs
- CSV files
- Generated charts
- Audio clips

### Artifact Service

| Service | Storage | Use Case |
|---------|---------|----------|
| `InMemoryArtifactService` | RAM | Development, testing |
| `GcsArtifactService` | Google Cloud Storage | Production |
| Custom | Any blob storage | Self-hosted |

### When to Use Artifacts vs State

| Use artifacts for... | Use state for... |
|---------------------|-------------------|
| Binary files (images, PDFs) | Small string/dict values |
| Large data (>1KB) | Small config values |
| Files shared across agents | Pipeline intermediate results |
| Generated content (charts, reports) | User preferences, flags |'''),

    ("code", r'''# ====================================================================
# EXAMPLE 5: Artifacts -- Save and load files between agent turns
# ====================================================================

async def artifact_demo():
    # --- Create artifact service ---
    art_svc = InMemoryArtifactService()

    # --- Create a text "file" as an artifact ---
    # In a real app, this could be an image, PDF, or CSV
    report_content = b"""Weekly Sales Report
====================
Monday:    $12,500
Tuesday:   $15,200
Wednesday: $18,700
Thursday:  $14,300
Friday:    $22,100
Total:     $82,800
"""
    # Save artifact -- Part.from_bytes wraps binary data
    await art_svc.save_artifact(
        app_name="app",
        user_id="user1",
        session_id="s1",
        filename="weekly_report.txt",
        artifact=Part.from_bytes(data=report_content, mime_type="text/plain")
    )
    print("Saved artifact: weekly_report.txt")

    # --- Load the artifact back ---
    loaded = await art_svc.load_artifact(
        app_name="app",
        user_id="user1",
        session_id="s1",
        filename="weekly_report.txt"
    )
    if loaded and loaded.inline_data:
        print(f"Loaded artifact:\n{loaded.inline_data.data.decode('utf-8')[:200]}")
    else:
        print("Artifact not found")

    print("\n[Artifact demo complete -- agents can share files this way]")

await artifact_demo()'''),

    ("markdown", r'''## 5.7 Streaming -- Real-Time Event Processing

### What Is Streaming?

By default, `runner.run()` returns events after each **complete step**
(one full LLM response, one tool execution). For real-time UX, use
`runner.run_async()` which streams **token-by-token** as the LLM generates.

### run() vs run_async()

| Method | Returns | Granularity | Use Case |
|--------|---------|-------------|----------|
| `runner.run()` | sync generator | Per-step (full response) | Simple scripts, batch processing |
| `runner.run_async()` | async generator | Per-token (streaming) | Chat UIs, real-time display |

### Event Types You'll See

```
Event {
    author: "agent_name"          # Who produced this event
    content: Content {             # What was produced
        parts: [
            Part { text: "Hello" },                    # Text chunk
            Part { thought: true, text: "..." },        # Thinking content
            Part { function_call: {...} },              # Tool call
            Part { function_response: {...} },          # Tool result
        ]
    }
    actions: EventActions {        # Side effects
        state_delta: {...},        # State changes
        artifact_delta: {...},     # Artifact changes
    }
    partial: bool                  # Is this a partial (streaming) event?
}
```

### Streaming Best Practices

1. **Filter by author** -- skip "user" events (echo of user message)
2. **Check partial** -- partial=True means more chunks coming
3. **Handle function_call/function_response** -- show tool activity to user
4. **Skip thought parts** -- these are internal reasoning, not for display'''),

    ("code", r'''# ====================================================================
# EXAMPLE 6: Streaming -- process events in real time
# ====================================================================

async def streaming_demo():
    agent = Agent(
        name="storyteller",
        model="gemini-2.5-flash",
        instruction="You are a creative storyteller. Write a 3-sentence story about any topic.",
    )
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="stream")
    r = Runner(agent=agent, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(text="Tell me a story about a robot learning to paint.")])

    print("=== Streaming Demo (run_async) ===\n")
    print("Story: ", end="", flush=True)

    # --- run_async() yields events as they happen ---
    event_count = 0
    async for event in r.run_async(user_id="u", session_id=s.id, new_message=m):
        event_count += 1
        if event.content and event.content.parts:
            for part in event.content.parts:
                # Text chunk -- print immediately for streaming effect
                if part.text and not getattr(part, 'thought', False):
                    print(part.text, end="", flush=True)
                # Tool calls (if any)
                if part.function_call:
                    print(f"\n  [Tool call: {part.function_call.name}]")

    print(f"\n\n[Streamed {event_count} events total]")

await streaming_demo()'''),

    ("markdown", r'''## 5.8 The Context Object -- What's Available Inside Callbacks

The `Context` object (`ctx`) passed to callbacks is your window into the
agent's runtime state. Here's what you can access:

### Context Properties

| Property | Type | Description |
|----------|------|-------------|
| `ctx.agent` | Agent | The agent being executed |
| `ctx.state` | dict | Session state (read/write) |
| `ctx.session` | Session | Full session object |
| `ctx.user_id` | str | Current user ID |
| `ctx.invocation_id` | str | Unique ID for this run (for tracing) |
| `ctx.model` | BaseLlm | The LLM instance |

### Practical Pattern: Dynamic Instructions

You can use callbacks to **dynamically modify instructions** based on
session state -- e.g., switching language, adjusting verbosity, or
injecting real-time data.'''),

    ("code", r'''# ====================================================================
# EXAMPLE 7: Dynamic instruction injection via before_model callback
# ====================================================================

def inject_context_before_model(ctx: Context, llm_request):
    """Inject user preferences into every LLM call.
    This runs before EACH LLM call, so context is always fresh.
    """
    # Read from session state
    user_name = ctx.state.get("user_name", "Unknown")
    language = ctx.state.get("language", "English")
    verbosity = ctx.state.get("verbosity", "normal")

    # Build dynamic context string
    dynamic_context = f"\n\n[Runtime Context]\nUser: {user_name}\nLanguage: {language}\nVerbosity: {verbosity}"

    # Append to the system instruction
    if llm_request and llm_request.config and llm_request.config.system_instruction:
        llm_request.config.system_instruction += dynamic_context
    else:
        print(f"    [INJECT] No system instruction found, skipping injection")

    print(f"    [INJECT] Added context: user={user_name}, lang={language}")
    return None  # Proceed with modified request

async def dynamic_context_demo():
    agent = Agent(
        name="adaptive_bot",
        model="gemini-2.5-flash",
        instruction="You are a helpful assistant. Adapt to the user preferences.",
        before_model_callback=inject_context_before_model,
    )
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="dyn")
    # Pre-populate user profile
    s.state["user_name"] = "Bob"
    s.state["language"] = "Spanish"
    s.state["verbosity"] = "concise"

    r = Runner(agent=agent, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(text="Greet me and tell me about the weather.")])

    print("=== Dynamic Context Injection Demo ===\n")
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"Agent: {p.text[:400]}")

await dynamic_context_demo()'''),

    ("markdown", r'''## Summary

| Feature | Purpose | Key API |
|---------|---------|---------|
| **before_agent** | Setup, caching, validation | `ctx -> Optional[Content]` |
| **after_agent** | Cleanup, logging, override | `ctx -> Optional[Content]` |
| **before_model** | Modify LLM request, inject context | `ctx, LlmRequest -> Optional[LlmResponse]` |
| **after_model** | Inspect/filter LLM response | `ctx, LlmResponse -> Optional[LlmResponse]` |
| **before_tool** | Security gate, validation | `tool, args, ctx -> Optional[dict]` |
| **after_tool** | Sanitize/log tool results | `tool, args, ctx, result -> Optional[dict]` |
| **Session State** | Per-chat data (dict) | `ctx.state["key"] = value` |
| **Memory Service** | Cross-session facts | `memory.add_session()` / `search_memory()` |
| **Artifacts** | File I/O (images, PDFs) | `save_artifact()` / `load_artifact()` |
| **Streaming** | Real-time token output | `runner.run_async()` |

### Callback Return Value Cheat Sheet

```
before_agent:  None -> run agent | Content -> skip agent, use this
after_agent:   None -> keep output | Content -> replace output
before_model:  None -> call LLM | LlmResponse -> skip LLM call
after_model:   None -> keep response | LlmResponse -> replace response
before_tool:   None -> run tool | dict -> skip tool, use this dict
after_tool:    None -> keep result | dict -> replace result
```

**Next:** [06_a2a_protocol.ipynb](./06_a2a_protocol.ipynb) -- distributed agent communication.'''),
]

save('05_callbacks_memory_state.ipynb', nb05)
print("Notebook 05 complete")
