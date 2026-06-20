#!/usr/bin/env python3
"""Generate notebook 07 — Graph Workflows (deep theory + multiple examples)."""
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
from google.adk import Workflow
print("Core imports + Workflow ready")'''

nb07 = [
    ("markdown", r'''# 07 — ADK 2.0 Graph Workflows: Deterministic Execution Flows

## What You'll Learn

1. **Workflow vs Agent** — two execution models, when to use which
2. **Graph theory basics** — nodes, edges, topological execution
3. **Simple linear workflows** — START -> A -> B -> END
4. **Fan-out / Fan-in** — parallel branches and result merging
5. **Conditional routing** — edge dicts that branch based on state
6. **Custom callable nodes** — any Python function as a workflow node
7. **Retry configuration** — per-node retry with exponential backoff
8. **Human-in-the-loop (HITL)** — pause for human approval
9. **Nested workflows** — workflows within workflows
10. **State flow** — how data propagates through graph nodes

> **Prerequisites:** Notebooks 02 (Agent), 04 (Multi-agent patterns)

---

## 7.1 Workflow vs Agent — Two Execution Models

ADK provides two fundamentally different ways to orchestrate work:

### Agent (LLM-Driven, Non-Deterministic)

```
User: "Analyze this data"
  -> LLM decides: "I should use the chart tool first"
  -> LLM decides: "Now I'll use the summary tool"
  -> LLM decides: "Now I'll write the report"
  -> Done

The LLM decides the order of operations at runtime.
Same input may produce different execution paths.
```

### Workflow (Graph-Driven, Deterministic)

```
START -> [fetch_data] -> [clean_data] -> [analyze] -> [report] -> END

You define the exact sequence of operations.
Same input ALWAYS produces the same execution path.
Each node can still be an Agent (with LLM inside), but the FLOW is fixed.
```

### Comparison Table

| Feature | Agent (LLM-driven) | Workflow (Graph-based) |
|---------|-------------------|----------------------|
| **Control flow** | LLM decides next step | You define graph edges |
| **Determinism** | Non-deterministic | Deterministic |
| **Best for** | Open-ended reasoning | Predictable pipelines |
| **Parallelism** | Only via ParallelAgent | Fan-out to N nodes |
| **Conditional branching** | LLM decides | Edge dicts with conditions |
| **Retry** | Manual | Per-node retry_config |
| **Human approval** | Manual | Pause nodes |
| **Error handling** | on_model_error callback | Per-node retry + fallback |
| **Composability** | sub_agents | Nested workflows |

### Rule of Thumb

```
Use WORKFLOW when:
  - The execution path is known and fixed
  - You need determinism (same input = same path)
  - You need parallel branches or conditional routing
  - You need retry or human-in-the-loop
  - Compliance requires auditable execution paths

Use AGENT when:
  - The LLM should decide what to do
  - The task is open-ended or exploratory
  - You want flexibility over predictability
```

---

## 7.2 Graph Theory Basics — How ADK Executes Workflows

### The Mental Model

A workflow is a **directed graph** where:
- **Nodes** are things that execute (Agents, tools, Python functions)
- **Edges** define what executes next
- **START** is a special entry-point node

### Node Types

| Node Type | What It Is | Example |
|-----------|-----------|---------|
| `Agent` | An ADK Agent (LLM + tools + instruction) | `Agent(name="analyzer", ...)` |
| `BaseTool` | A tool instance | `google_search`, custom tool |
| Callable | Any Python function | `def validate(data): ...` |
| `"START"` | Special keyword for entry point | `"START"` |

### Edge Types

| Edge Format | Meaning | Example |
|------------|---------|---------|
| `(A, B)` | After A, run B | `("START", agent_a)` |
| `(A, [B, C])` | After A, run B AND C in parallel | Fan-out |
| `([B, C], D)` | After B AND C complete, run D | Fan-in |
| `(A, {cond1: B, cond2: C})` | After A, evaluate condition dict | Conditional routing |

### Execution Model

```
1. ADK topologically sorts the graph
2. Starts at "START" node
3. For each node:
   a. Execute the node (run Agent, call function, run tool)
   b. Look at outgoing edges
   c. If multiple edges -> execute in parallel
   d. If conditional dict -> evaluate conditions, pick branch
   e. If no outgoing edges -> node is terminal (implicit END)
4. Workflow completes when all paths reach terminal nodes
```

### Visual: Topological Execution

```
START
  |
  v
[fetch_data]          Step 1: fetch data
  |
  +----> [clean]      Step 2a: clean data (parallel)
  |
  +----> [validate]   Step 2b: validate data (parallel)
  |        |
  v        |
[analyze]  |          Step 3: analyze (waits for clean)
  |        |
  v        v
[merge_results]       Step 4: merge (fan-in, waits for both)
  |
  v
[generate_report]     Step 5: report
  |
 (no outgoing edge -> END)
```'''),

    ("code", IMP_CELL),
    ("code", ENV_CELL),

    # ── 7.3 Simple Linear Workflow ──
    ("markdown", r'''## 7.3 Example 1: Simple Linear Workflow

The simplest workflow: START -> one agent -> done.

### Key Concepts
- `"START"` is a reserved keyword — always the entry point
- No explicit `"END"` — nodes with no outgoing edges are terminal
- The Runner API is identical for Workflows and Agents'''),

    ("code", r'''# ====================================================================
# EXAMPLE 1: Linear workflow — START -> greeter -> (done)
# ====================================================================

# Step 1: Define the agent that will be a workflow node
greeter = Agent(
    name="greeter",
    model="gemini-2.5-flash",
    instruction="Greet the user warmly and ask what topic they want to explore.",
)

# Step 2: Build the graph
# Edge format: (from_node, to_node)
# "START" is the special entry point keyword
# No outgoing edge from greeter -> implicit END
wf_simple = Workflow(
    name="simple_greeting",
    edges=[
        ("START", greeter),   # Entry point -> run greeter
        # greeter has no outgoing edge -> it's terminal (END)
    ],
)
print(f"Workflow created: {wf_simple.name}")
print("Graph: START -> greeter -> END")

# Step 3: Run it — same Runner API as Agent!
async def run_simple():
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="wf1")
    r = Runner(agent=wf_simple, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(text="I'm interested in black holes.")])
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"[{e.author}]: {p.text[:300]}")

# await run_simple()  # Uncomment to execute
print("Linear workflow ready — uncomment 'await run_simple()' to execute")'''),

    # ── 7.4 Multi-Node Pipeline ──
    ("markdown", r'''## 7.4 Example 2: Multi-Node Pipeline (Brainstorm -> Outline -> Draft)

A three-stage writing pipeline. Each stage builds on the previous one
via session state (output_key).

### How Data Flows Between Nodes

```
START -> [brainstorm] -> [outline] -> [draft] -> END
              |              |          |
              v              v          v
         state["..."]   state["..."]  final output
```

Each agent's output_key saves its result to session.state.
The next agent can read previous outputs from state in its instruction.

### Why This Is Better Than SequentialAgent

| Feature | SequentialAgent | Workflow |
|---------|----------------|----------|
| Linear pipelines | Yes | Yes |
| Conditional routing | No | Yes (edge dicts) |
| Parallel branches | No | Yes (fan-out) |
| Per-node retry | No | Yes (retry_config) |
| Human-in-the-loop | No | Yes (pause nodes) |
| Custom callable nodes | No | Yes (any Python function) |'''),

    ("code", r'''# ====================================================================
# EXAMPLE 2: Multi-node pipeline — Brainstorm -> Outline -> Draft
# ====================================================================

# --- Stage 1: Brainstorm ideas ---
brainstorm = Agent(
    name="brainstorm",
    model="gemini-2.5-flash",
    instruction="Brainstorm 3-5 interesting angles on the topic. Be creative and specific.",
    output_key="brainstorm_ideas",  # Saves to session.state["brainstorm_ideas"]
)

# --- Stage 2: Create outline from brainstorm ---
# This agent reads session.state["brainstorm_ideas"] from the previous stage
outline = Agent(
    name="outline",
    model="gemini-2.5-flash",
    instruction="""Read the brainstorm ideas from session state.
Create a structured outline using markdown headings.
Organize ideas into 3-5 sections.""",
    output_key="outline_result",
)

# --- Stage 3: Draft the content ---
draft = Agent(
    name="draft",
    model="gemini-2.5-flash",
    instruction="""Read the outline from session state.
Expand each section into 2-3 sentences. Professional tone.
Return the complete draft as markdown.""",
)

# --- Build the pipeline graph ---
pipeline = Workflow(
    name="writing_pipeline",
    edges=[
        ("START", brainstorm),      # Entry -> brainstorm
        (brainstorm, outline),       # brainstorm -> outline
        (outline, draft),            # outline -> draft
        # draft has no outgoing edge -> implicit END
    ],
)
print("Pipeline: START -> brainstorm -> outline -> draft -> END")

# --- Run the pipeline ---
async def run_pipeline():
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="wf2")
    r = Runner(agent=pipeline, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(
        text="Write about the impact of AI on healthcare diagnostics."
    )])
    print("=== Writing Pipeline ===\n")
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"--- [{e.author}] ---\n{p.text[:400]}\n")

# await run_pipeline()  # Uncomment to execute
print("Pipeline ready — uncomment 'await run_pipeline()' to execute")'''),

    # ── 7.5 Fan-Out / Fan-In ──
    ("markdown", r'''## 7.5 Example 3: Fan-Out / Fan-In (Parallel Branches)

Fan-out: one node triggers multiple parallel branches.
Fan-in: multiple branches converge to a single node that waits for all.

### Architecture

```
                    START
                      |
                      v
               [research_topic]
                      |
            +---------+---------+
            |                   |        Fan-out: 3 parallel branches
            v                   v
     [research_AI]       [research_ethics]
            |                   |
            +---------+---------+
                      |                   Fan-in: merge waits for both
                      v
               [write_summary]
                      |
                   (END)
```

### When to Use Fan-Out/Fan-In

- **Multi-perspective analysis**: Analyze from tech, business, and legal angles
- **Parallel research**: Research multiple topics simultaneously
- **Distributed processing**: Process chunks in parallel, merge results
- **Redundancy**: Run 3 agents, take majority vote

### How Fan-In Works

The merge node does NOT start until ALL incoming branches complete.
ADK handles this synchronization automatically — you just define the edges.'''),

    ("code", r'''# ====================================================================
# EXAMPLE 3: Fan-out/Fan-in — parallel research + merge
# ====================================================================

# --- Node 1: Extract the topic (single entry node) ---
topic_extractor = Agent(
    name="topic_extractor",
    model="gemini-2.5-flash",
    instruction="Extract the main topic from the user request. Return just the topic name.",
    output_key="topic",
)

# --- Node 2a: Research AI perspective (parallel branch A) ---
ai_researcher = Agent(
    name="ai_researcher",
    model="gemini-2.5-flash",
    instruction="Research the AI/technical perspective on the topic from session state. 3 key points.",
    output_key="ai_perspective",
)

# --- Node 2b: Research ethics perspective (parallel branch B) ---
ethics_researcher = Agent(
    name="ethics_researcher",
    model="gemini-2.5-flash",
    instruction="Research the ethical/social perspective on the topic from session state. 3 key points.",
    output_key="ethics_perspective",
)

# --- Node 3: Merge results (fan-in — waits for both branches) ---
merger = Agent(
    name="merger",
    model="gemini-2.5-flash",
    instruction="""Read the AI perspective and ethics perspective from session state.
Write a balanced summary that includes both viewpoints.
Format: 'Technical View:' and 'Ethical View:' sections.""",
)

# --- Build the fan-out/fan-in graph ---
fan_workflow = Workflow(
    name="parallel_research",
    edges=[
        # Entry -> extract topic
        ("START", topic_extractor),

        # Fan-out: topic_extractor -> TWO branches in parallel
        (topic_extractor, ai_researcher),       # Branch A
        (topic_extractor, ethics_researcher),   # Branch B

        # Fan-in: both branches -> merger (merger waits for both)
        (ai_researcher, merger),       # Branch A -> merge
        (ethics_researcher, merger),   # Branch B -> merge
        # merger has no outgoing edge -> END
    ],
)
print("Fan-out/fan-in graph:")
print("  START -> topic_extractor")
print("  topic_extractor -> ai_researcher (parallel)")
print("  topic_extractor -> ethics_researcher (parallel)")
print("  ai_researcher -> merger (fan-in)")
print("  ethics_researcher -> merger (fan-in)")
print("  merger -> END")

# --- Run it ---
async def run_fan():
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="wf3")
    r = Runner(agent=fan_workflow, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(
        text="Analyze the use of facial recognition technology in public spaces."
    )])
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"[{e.author}]: {p.text[:300]}\n")

# await run_fan()  # Uncomment to execute
print("\nFan-out/fan-in ready — uncomment 'await run_fan()' to execute")'''),

    # ── 7.6 Conditional Routing ──
    ("markdown", r'''## 7.6 Example 4: Conditional Routing

Sometimes the path depends on the data. Use edge dicts to branch:

```python
# After router_node, evaluate conditions:
(router_node, {
    "condition_1": node_a,   # If condition_1 is true -> run node_a
    "condition_2": node_b,   # If condition_2 is true -> run node_b
})
```

### When to Use Conditional Routing

- **Language detection**: If state["language"] == "es" -> spanish_agent
- **Complexity routing**: Simple questions -> fast agent, complex -> deep agent
- **Content type**: Text -> text_agent, image -> vision_agent
- **Approval flow**: If state["approved"] -> publish, else -> review

### How Conditions Work

ADK evaluates the condition dict by checking session state keys.
The first matching condition determines the branch taken.'''),

    ("code", r'''# ====================================================================
# EXAMPLE 4: Conditional routing — branch based on content type
# ====================================================================

# --- Router node: determines what type of request this is ---
classifier = Agent(
    name="classifier",
    model="gemini-2.5-flash",
    instruction="""Classify the user request as one of:
- 'technical': code, programming, technical questions
- 'creative': stories, poems, creative writing
- 'factual': facts, definitions, information

Return ONLY the classification word (technical, creative, or factual).""",
    output_key="classification",  # Saves result to session.state["classification"]
)

# --- Branch A: Technical questions ---
tech_agent = Agent(
    name="tech_responder",
    model="gemini-2.5-flash",
    instruction="You are a technical expert. Provide precise, detailed technical answers with code examples.",
)

# --- Branch B: Creative requests ---
creative_agent = Agent(
    name="creative_responder",
    model="gemini-2.5-flash",
    instruction="You are a creative writer. Be imaginative, vivid, and engaging.",
)

# --- Branch C: Factual questions ---
factual_agent = Agent(
    name="factual_responder",
    model="gemini-2.5-flash",
    instruction="You are a fact-based assistant. Provide accurate, well-sourced information.",
)

# --- Build conditional routing graph ---
# The edge dict tells ADK: after classifier, check session.state["classification"]
# and route to the matching agent
conditional_wf = Workflow(
    name="smart_router",
    edges=[
        # Entry -> classifier
        ("START", classifier),

        # Conditional routing: classifier -> one of three branches
        # The dict keys match the value saved in session.state["classification"]
        (classifier, {
            "technical": tech_agent,       # If state["classification"] == "technical"
            "creative": creative_agent,     # If state["classification"] == "creative"
            "factual": factual_agent,       # If state["classification"] == "factual"
        }),
        # Each branch agent has no outgoing edge -> END
    ],
)
print("Conditional routing graph:")
print("  START -> classifier")
print("  classifier -> {technical: tech_responder, creative: creative_responder, factual: factual_responder}")
print("  Each branch -> END")

# --- Run it ---
async def run_conditional():
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="wf4")
    r = Runner(agent=conditional_wf, app_name="t", session_service=svc)
    # Try different inputs to see different branches
    m = Content(role="user", parts=[Part.from_text(
        text="Write a Python function to sort a list using quicksort."
    )])
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"[{e.author}]: {p.text[:300]}\n")

# await run_conditional()  # Uncomment to execute
print("\nConditional routing ready — uncomment 'await run_conditional()' to execute")'''),

    # ── 7.7 Custom Callable Nodes ──
    ("markdown", r'''## 7.7 Example 5: Custom Callable Nodes (Non-Agent Nodes)

Not every node needs an LLM! You can use any Python function as a workflow
node. This is powerful for:

- **Data validation**: Check inputs before passing to agents
- **Data transformation**: Clean, filter, or transform data
- **Logging/monitoring**: Record state at specific points
- **Business logic**: Apply rules without LLM cost

### Callable Node Signature

```python
def my_function(ctx: Context) -> Optional[Content]:
    """A workflow callable node.
    
    Args:
        ctx: The workflow Context (access to state, session, etc.)
    
    Returns:
        Content to add to the conversation, or None
    """
    # Read/write session state
    data = ctx.state.get("input_data", "")
    
    # Do work
    cleaned = data.strip().lower()
    
    # Write result to state for next node
    ctx.state["cleaned_data"] = cleaned
    
    return None  # No content to add to conversation
```'''),

    ("code", r'''# ====================================================================
# EXAMPLE 5: Custom callable nodes — non-LLM processing in workflows
# ====================================================================

# --- Callable Node 1: Data validation (no LLM needed!) ---
def validate_input(ctx) -> None:
    """Validate user input before passing to expensive LLM agents.
    
    This node runs WITHOUT any LLM call — pure Python logic.
    Saves CPU/API costs by rejecting invalid input early.
    """
    # Access the last user message from session events
    # In a real app, you'd extract the text from the latest event
    user_input = ctx.state.get("raw_input", "")
    
    # Validation rules
    if not user_input or len(user_input.strip()) < 10:
        ctx.state["validation_error"] = "Input too short (minimum 10 characters)"
        print(f"  [VALIDATE] FAILED: input too short")
    else:
        ctx.state["validated_input"] = user_input.strip()
        ctx.state["validation_error"] = None
        print(f"  [VALIDATE] PASSED: {len(user_input)} chars")
    
    return None  # No content to add — just state updates

# --- Callable Node 2: Data preprocessing ---
def preprocess_data(ctx) -> None:
    """Clean and normalize the validated input.
    Another pure-Python node — no LLM cost.
    """
    text = ctx.state.get("validated_input", "")
    if text:
        # Normalization: strip, lowercase, remove extra whitespace
        cleaned = " ".join(text.split())
        ctx.state["processed_input"] = cleaned
        print(f"  [PREPROCESS] Cleaned: {len(cleaned)} chars")
    return None

# --- Agent Node: The actual LLM processing ---
analyzer = Agent(
    name="analyzer",
    model="gemini-2.5-flash",
    instruction="Analyze the processed input from session state. Provide insights.",
)

# --- Build workflow with mixed node types ---
mixed_workflow = Workflow(
    name="validate_and_analyze",
    edges=[
        ("START", validate_input),     # START -> validate (Python function)
        (validate_input, preprocess_data),  # validate -> preprocess (Python function)
        (preprocess_data, analyzer),    # preprocess -> analyze (Agent)
        # analyzer -> END
    ],
)
print("Mixed workflow: START -> validate (Python) -> preprocess (Python) -> analyze (Agent) -> END")
print("Key insight: Not every node needs an LLM — pure Python functions work too!")

# --- Run it ---
async def run_mixed():
    svc = InMemorySessionService()
    s = await svc.create_session(app_name="t", user_id="u", session_id="wf5")
    # Pre-populate with test data
    s.state["raw_input"] = "The quick brown fox jumps over the lazy dog and runs away."
    r = Runner(agent=mixed_workflow, app_name="t", session_service=svc)
    m = Content(role="user", parts=[Part.from_text(text="Analyze the input data.")])
    for e in r.run(user_id="u", session_id=s.id, new_message=m):
        if e.content and e.content.parts and e.author != "user":
            for p in e.content.parts:
                if p.text: print(f"[{e.author}]: {p.text[:300]}")

# await run_mixed()  # Uncomment to execute
print("\nMixed workflow ready — uncomment 'await run_mixed()' to execute")'''),

    # ── 7.8 Retry Configuration ──
    ("markdown", r'''## 7.8 Example 6: Retry Configuration

Production agents fail. APIs timeout, models hit rate limits, network
glitches happen. Workflow nodes support per-node retry configuration.

### RetryConfig

```python
from google.adk.workflow import RetryConfig

retry = RetryConfig(
    max_retries=3,              # Maximum retry attempts
    initial_delay=1.0,          # First retry waits 1 second
    max_delay=30.0,             # Cap delay at 30 seconds
    backoff_multiplier=2.0,     # Each retry doubles the delay
    retryable_errors=[          # Which errors trigger retry
        ConnectionError,
        TimeoutError,
    ],
)
```

### Exponential Backoff Visualization

```
Attempt 1: FAIL -> wait 1s
Attempt 2: FAIL -> wait 2s
Attempt 3: FAIL -> wait 4s
Attempt 4: FAIL -> wait 8s (capped at max_delay)
...
Attempt N: FAIL -> give up, propagate error
```

### When to Use Retry

| Scenario | Retry? | Why |
|----------|--------|-----|
| API timeout | Yes | Transient — likely succeeds on retry |
| Rate limit (429) | Yes | Wait and retry |
| Invalid input error | No | Same input = same error |
| Authentication failure | No | Retrying won't fix bad credentials |
| Network connection refused | Yes | Server might restart |'''),

    ("code", r'''# ====================================================================
# EXAMPLE 6: Retry configuration — resilient workflow nodes
# ====================================================================

from google.adk.workflow import RetryConfig

# --- Define retry strategies ---

# Aggressive retry for flaky external APIs
aggressive_retry = RetryConfig(
    max_retries=5,              # Try up to 5 times
    initial_delay=1.0,          # Start with 1s delay
    max_delay=60.0,             # Cap at 60s
    backoff_multiplier=2.0,     # 1s, 2s, 4s, 8s, 16s
)

# Conservative retry for expensive LLM calls
conservative_retry = RetryConfig(
    max_retries=2,              # Only 2 retries (LLM calls are expensive)
    initial_delay=5.0,          # Start with 5s delay
    max_delay=30.0,             # Cap at 30s
    backoff_multiplier=3.0,     # 5s, 15s
)

# --- An agent that might fail (simulating a flaky API) ---
import random

flaky_agent = Agent(
    name="flaky_api_caller",
    model="gemini-2.5-flash",
    instruction="Call the external API and return the result.",
    retry_config=conservative_retry,  # Attach retry config to this node
    timeout=30.0,                     # Per-node timeout in seconds
)

# --- A robust agent with aggressive retry ---
robust_agent = Agent(
    name="robust_fetcher",
    model="gemini-2.5-flash",
    instruction="Fetch data from the external service.",
    retry_config=aggressive_retry,
    timeout=60.0,
)

# --- Build a workflow with different retry strategies per node ---
resilient_wf = Workflow(
    name="resilient_pipeline",
    edges=[
        ("START", robust_fetcher := robust_agent),    # Entry: robust fetch
        (robust_fetcher, flaky_agent := flaky_agent), # Then: flaky API call
        # flaky_agent -> END
    ],
)

print("Retry strategies configured:")
print(f"  robust_fetcher: {conservative_retry}")
print(f"  flaky_agent: aggressive (5 retries, 1-60s backoff)")
print("\nKey: Each node can have its OWN retry strategy")'''),

    # ── 7.9 Human-in-the-Loop ──
    ("markdown", r'''## 7.9 Example 7: Human-in-the-Loop (HITL)

Some workflows need human approval before proceeding — sending emails,
publishing content, making payments, executing irreversible actions.

### HITL Pattern in ADK Workflows

```
START -> [draft_email] -> [await_approval] -> [send_email] -> END
                              ^
                              |
                    Human reviews and approves/rejects
```

### How HITL Works in ADK

ADK provides the `request_input` tool for pausing workflow execution:

1. A node calls `request_input` to pause and ask for human input
2. The workflow enters `INPUT_REQUIRED` state
3. Human reviews the content and provides input (approve/reject/edit)
4. Workflow resumes based on human input

### When to Use HITL

| Scenario | HITL? | Why |
|----------|-------|-----|
| Send customer email | Yes | Email is irreversible |
| Generate report | No | Report can be regenerated |
| Process payment | Yes | Financial transaction |
| Delete database records | Yes | Irreversible data loss |
| Draft blog post | No | Can always edit later |
| Deploy to production | Yes | High-impact action |'''),

    ("code", r'''# ====================================================================
# EXAMPLE 7: Human-in-the-loop — email approval workflow
# ====================================================================

from google.adk.tools import request_input

# --- Node 1: Draft the email ---
email_drafter = Agent(
    name="email_drafter",
    model="gemini-2.5-flash",
    instruction="""Draft a professional email based on the user request.
    Include subject line and body. Save to session.state["email_draft"].""",
    output_key="email_draft",
)

# --- Node 2: Request human approval ---
def request_approval(ctx) -> None:
    """Pause the workflow and ask a human to review the email draft.
    
    This is a HITL (Human-in-the-Loop) checkpoint.
    The workflow pauses until the human provides input.
    """
    draft = ctx.state.get("email_draft", "")
    print(f"  [HITL] Email draft ready for review:")
    print(f"  {draft[:200]}...")
    print(f"  [HITL] Waiting for human approval...")
    
    # In ADK, you'd use the request_input tool:
    # approval = request_input(
    #     prompt="Do you approve this email? (yes/no/edit)",
    #     ctx=ctx,
    # )
    # ctx.state["approved"] = (approval.lower() == "yes")
    
    # For this example, we simulate approval
    ctx.state["approved"] = True
    print(f"  [HITL] Approved!")
    return None

# --- Node 3: Send the email (only if approved) ---
email_sender = Agent(
    name="email_sender",
    model="gemini-2.5-flash",
    instruction="""Check session.state["approved"]. 
    If True, confirm the email was sent.
    If False, explain that the email was not approved.""",
)

# --- Build HITL workflow ---
hitl_workflow = Workflow(
    name="email_approval",
    edges=[
        ("START", email_drafter),
        (email_drafter, request_approval),    # Agent -> HITL checkpoint
        (request_approval, email_sender),      # After approval -> send
        # email_sender -> END
    ],
)

print("HITL Workflow: START -> draft_email -> [HUMAN APPROVAL] -> send_email -> END")
print("Key: request_input pauses execution until human responds")
print("\nTo run: await with a real human-in-the-loop system")'''),

    # ── 7.10 Nested Workflows ──
    ("markdown", r'''## 7.10 Example 8: Nested Workflows

Workflows can contain other workflows! This is how you build complex
multi-stage systems while keeping each layer manageable.

### Architecture Example

```
Outer Workflow
├── [research_phase] (inner Workflow)
│   ├── START -> [search] -> [extract] -> [summarize] -> END
│
├── [analysis_phase] (inner Workflow)
│   ├── START -> [analyze] -> [validate] -> END
│
└── [report_phase] (inner Workflow)
    ├── START -> [draft] -> [review] -> [publish] -> END
```

### Why Nest Workflows?

| Benefit | Explanation |
|---------|-------------|
| **Modularity** | Each phase is a self-contained, testable workflow |
| **Reusability** | Share the research workflow across projects |
| **Clarity** | Each workflow has a focused graph (not 20 nodes in one) |
| **Independent retry** | Each inner workflow can have its own retry config |'''),

    ("code", r'''# ====================================================================
# EXAMPLE 8: Nested workflows — workflow within a workflow
# ====================================================================

# --- Inner Workflow 1: Research phase ---
search_agent = Agent(name="searcher", model="gemini-2.5-flash",
    instruction="Search for information on the topic.", output_key="search_results")

extract_agent = Agent(name="extractor", model="gemini-2.5-flash",
    instruction="Extract key facts from search results.", output_key="extracted_facts")

research_workflow = Workflow(
    name="research_phase",
    edges=[
        ("START", search_agent),
        (search_agent, extract_agent),
        # extract_agent -> END (inner workflow completes)
    ],
)

# --- Inner Workflow 2: Analysis phase ---
analyze_agent = Agent(name="analyzer", model="gemini-2.5-flash",
    instruction="Analyze the extracted facts. Identify trends and patterns.", output_key="analysis")

validate_agent = Agent(name="validator", model="gemini-2.5-flash",
    instruction="Validate the analysis for accuracy and completeness.", output_key="validated_analysis")

analysis_workflow = Workflow(
    name="analysis_phase",
    edges=[
        ("START", analyze_agent),
        (analyze_agent, validate_agent),
        # validate_agent -> END
    ],
)

# --- Inner Workflow 3: Report phase ---
draft_agent = Agent(name="drafter", model="gemini-2.5-flash",
    instruction="Draft the final report from validated analysis.", output_key="report_draft")

review_agent = Agent(name="reviewer", model="gemini-2.5-flash",
    instruction="Review and polish the report draft. Fix any issues.")

report_workflow = Workflow(
    name="report_phase",
    edges=[
        ("START", draft_agent),
        (draft_agent, review_agent),
        # review_agent -> END
    ],
)

# --- Outer Workflow: Combines all three inner workflows ---
# Inner workflows are used as nodes in the outer workflow!
outer_workflow = Workflow(
    name="full_pipeline",
    edges=[
        ("START", research_workflow),         # Phase 1: Research
        (research_workflow, analysis_workflow), # Phase 2: Analysis
        (analysis_workflow, report_workflow),   # Phase 3: Report
        # report_workflow -> END
    ],
)

print("Nested Workflow Architecture:")
print("  Outer: START -> research_phase -> analysis_phase -> report_phase -> END")
print("  research_phase:  START -> searcher -> extractor -> END")
print("  analysis_phase:  START -> analyzer -> validator -> END")
print("  report_phase:    START -> drafter -> reviewer -> END")
print("\nKey: Inner workflows are used as nodes in the outer workflow")'''),

    # ── 7.11 State Flow ──
    ("markdown", r'''## 7.11 State Flow in Workflows — How Data Propagates

### The Single Shared State

All nodes in a workflow share ONE session state dictionary. This is how
data flows from node to node:

```
Node A:  ctx.state["result_a"] = "some value"
             |
             v
Node B:  value = ctx.state.get("result_a")  # Reads what A wrote
         ctx.state["result_b"] = process(value)
             |
             v
Node C:  value = ctx.state.get("result_b")  # Reads what B wrote
```

### output_key: The Shortcut

Setting `output_key="key"` on an Agent automatically saves its final
text response to `ctx.state["key"]`. This is the easiest way to pass
data between Agent nodes.

### Best Practices for State in Workflows

1. **Use descriptive keys**: `"research_results"` not `"rr"`
2. **Use output_key for agents**: Let ADK auto-save agent responses
3. **Use ctx.state for callables**: Manually set state in Python function nodes
4. **Don't overwrite keys**: Each node should write to its OWN key
5. **Read defensively**: Use `ctx.state.get("key", "default")` not `ctx.state["key"]`

### State Flow Diagram

```
                   session.state = {}
                        |
    +-------------------+-------------------+
    |                   |                   |
    v                   v                   v
 [Node A]           [Node B]           [Node C]
 writes              writes              writes
 state["a"]         state["b"]         state["c"]
    |                   |                   |
    +-------------------+-------------------+
                        |
                        v
              [Merge Node]
         reads state["a"], state["b"], state["c"]
         writes state["merged_result"]
                        |
                        v
              session.state = {
                  "a": "...",
                  "b": "...",
                  "c": "...",
                  "merged_result": "..."
              }
```'''),

    ("code", r'''# ====================================================================
# EXAMPLE 9: State flow — track data through every workflow node
# ====================================================================

# This example shows how state accumulates as each node executes

data_collector = Agent(
    name="collector",
    model="gemini-2.5-flash",
    instruction="Collect key information about the topic. Return 3 bullet points.",
    output_key="collected_data",  # -> state["collected_data"]
)

data_processor = Agent(
    name="processor",
    model="gemini-2.5-flash",
    instruction="Read collected_data from state. Transform into a structured summary.",
    output_key="processed_data",  # -> state["processed_data"]
)

# Custom callable that inspects ALL state
def state_inspector(ctx) -> None:
    """Log the current state at this point in the workflow.
    Useful for debugging and auditing.
    """
    print(f"  [STATE INSPECTOR] Current state keys: {list(ctx.state.keys())}")
    for key, value in ctx.state.items():
        if isinstance(value, str):
            print(f"    {key}: {value[:100]}...")
        else:
            print(f"    {key}: {type(value).__name__}")
    return None

final_reporter = Agent(
    name="reporter",
    model="gemini-2.5-flash",
    instruction="Read processed_data from state. Write a final executive summary.",
    output_key="final_report",  # -> state["final_report"]
)

state_flow_wf = Workflow(
    name="state_tracked_pipeline",
    edges=[
        ("START", data_collector),
        (data_collector, data_processor),
        (data_processor, state_inspector),   # Inspect state mid-workflow
        (state_inspector, final_reporter),
        # final_reporter -> END
    ],
)

print("State Flow Workflow:")
print("  START -> collector (state['collected_data'])")
print("  -> processor (state['processed_data'])")
print("  -> state_inspector (logs all state keys)")
print("  -> reporter (state['final_report'])")
print("  -> END")
print("\nFinal state will contain: collected_data, processed_data, final_report")'''),

    # ── Summary ──
    ("markdown", r'''## Summary

### Workflow Concepts Cheat Sheet

| Concept | Key API | Purpose |
|---------|---------|---------|
| **Workflow** | `Workflow(name=..., edges=[...])` | Graph-based execution |
| **Edge (simple)** | `(A, B)` | After A, run B |
| **Edge (fan-out)** | `(A, [B, C])` | After A, run B AND C in parallel |
| **Edge (fan-in)** | `([A, B], C)` | After A AND B, run C |
| **Edge (conditional)** | `(A, {cond1: B, cond2: C})` | Branch based on state |
| **START** | `"START"` | Special entry-point keyword |
| **Agent node** | `Agent(...)` | LLM-powered node |
| **Callable node** | `def fn(ctx): ...` | Pure Python node (no LLM) |
| **RetryConfig** | `RetryConfig(max_retries=...)` | Per-node retry |
| **output_key** | `Agent(output_key="key")` | Auto-save to state |
| **Nested workflow** | Inner `Workflow` as outer node | Modularity |

### When to Use Workflow vs Agent

```
WORKFLOW when:
  + Execution path is known and fixed
  + Need determinism (compliance, auditing)
  + Need parallel branches or conditional routing
  + Need retry or human-in-the-loop
  + Mix LLM and non-LLM processing

AGENT when:
  + LLM should decide what to do
  + Task is open-ended or exploratory
  + Want flexibility over predictability
  + Simple delegation (sub_agents is easier)
```

### Edge Type Quick Reference

```python
# Linear: A then B
edges = [("START", A), (A, B)]

# Fan-out: A then B AND C in parallel
edges = [("START", A), (A, B), (A, C)]

# Fan-in: A AND B, then C (C waits for both)
edges = [("START", A), ("START", B), (A, C), (B, C)]

# Conditional: A, then B or C based on state
edges = [("START", A), (A, {"condition_b": B, "condition_c": C})]

# Mixed callable + agent:
edges = [("START", validate_fn), (validate_fn, agent), (agent, postprocess_fn)]
```

**Next:** [08_evaluation_deployment.ipynb](./08_evaluation_deployment.ipynb) — testing and deploying agents.'''),
]

save('07_workflow_task_api.ipynb', nb07)
print("Notebook 07 complete")
