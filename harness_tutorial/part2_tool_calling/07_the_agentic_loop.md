# Chapter 07 — The Agentic Loop

## What You'll Learn

- The full agentic loop: how the model chains multiple tool calls to solve complex tasks
- Loop architecture: the `while True` pattern that powers every AI agent
- Termination conditions: when (and why) the loop should stop
- Parallel tool dispatch: handling multiple tool calls in one response
- A complete working example: a research assistant with search, calculate, and notes tools

---

## THIS Is the Critical Chapter

Everything before this was preparation. The agentic loop is **the defining pattern** of AI agent engineering. Every agent — from Claude Code to Cursor to Devin — runs some variant of this loop:

```
while not done:
    response = model(messages, tools)
    if response has tool_calls:
        for each tool_call:
            result = execute(tool_call)
            append result to messages
    else:
        done = True
        return response.text
```

It's simple in concept, but the details matter enormously. Let's build it right.

---

## The Loop Diagram

```
                    ┌──────────────────┐
                    │   START: user     │
                    │   sends message   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
               ┌───>│  CALL MODEL      │
               │    │  (with full      │
               │    │   message        │
               │    │   history +      │
               │    │   tools)          │
               │    └────────┬─────────┘
               │             │
               │             ▼
               │    ┌──────────────────┐
               │    │  CHECK RESPONSE  │
               │    └────────┬─────────┘
               │             │
               │     ┌───────┴───────┐
               │     │               │
               │     ▼               ▼
               │  ┌──────────┐  ┌──────────┐
               │  │ Has      │  │ Pure     │
               │  │ tool_use │  │ text     │
               │  │ blocks?  │  │ only?    │
               │  └────┬─────┘  └────┬─────┘
               │       │             │
               │       ▼             ▼
               │  ┌──────────┐  ┌──────────┐
               │  │ EXECUTE  │  │ RETURN   │
               │  │ all tool │  │ text to  │
               │  │ calls    │  │ user     │
               │  └────┬─────┘  └──────────┘
               │       │             ▲
               │       ▼             │
               │  ┌──────────┐       │
               │  │ APPEND   │       │
               │  │ tool     │       │
               │  │ results  │       │
               │  │ to msgs  │       │
               │  └────┬─────┘       │
               │       │             │
               └───────┘             │
                                     │
                            DONE ────┘
```

The loop has exactly two exit paths:
1. Model returns **text only** (no tool_use blocks) → we're done
2. We hit a **safety limit** (max iterations, timeout, etc.) → forced exit

---

## The Code: Research Assistant

Let's build a research assistant that can:
- **search the web** (simulated with a local "knowledge base")
- **calculate** math expressions
- **save notes** to a file

```python
# ═══════════════════════════════════════════════════
# CHAPTER 07 — The Agentic Loop: Research Assistant
# ═══════════════════════════════════════════════════
import anthropic
import math
import datetime
import json
import re

# ═══ STEP 1: Create the client ═══
client = anthropic.Anthropic(
    api_key="sk-ant-..."  # Replace with your key
)

# ═══════════════════════════════════════════════════
# STEP 2: Define tools — FUNCTIONS + SCHEMAS
# ═══════════════════════════════════════════════════
# Each tool has two parts: the Python function that runs, and the
# JSON schema that tells the model how to call it.

# ── Tool 1: Search ──
# Simulates a web search with a local knowledge base.
# In production, replace with a real search API (Brave, Tavily, SerpAPI).
KNOWLEDGE_BASE = {
    "python": "Python is a high-level, interpreted programming language "
              "created by Guido van Rossum in 1991. Known for readability.",
    "ai": "Artificial Intelligence (AI) is the simulation of human "
          "intelligence by machines. Key subfields: machine learning, "
          "NLP, computer vision, robotics.",
    "quantum": "Quantum computing uses quantum bits (qubits) that can "
               "exist in superposition. Potential to solve certain problems "
               "exponentially faster than classical computers.",
    "anthropic": "Anthropic is an AI safety company founded in 2021. "
                 "Creators of Claude. Focus on constitutional AI.",
    "harness": "In AI engineering, a harness is the control loop that "
               "manages the interaction between a user, an LLM, and tools. "
               "It orchestrates context, tool execution, and response handling.",
}

def search_web(query: str) -> str:
    """
    Search a simulated knowledge base for information.
    
    Args:
        query: The search query string
    
    Returns:
        Matching information or 'No results found'
    """
    # Simple keyword matching — in production, use embeddings + vector search
    query_lower = query.lower()
    results = []
    
    for topic, content in KNOWLEDGE_BASE.items():
        if topic in query_lower or any(word in content.lower() for word in query_lower.split()):
            results.append(f"[{topic}] {content}")
    
    if not results:
        return f"No results found for '{query}'. Try a different search term."
    
    return "\n\n".join(results)


def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.
    
    Args:
        expression: A math expression like "2 + 2 * 3" or "sqrt(16)"
    
    Returns:
        The calculated result as a string
    """
    # ⚠️ SECURITY: Never use eval() on arbitrary input in production!
    # We restrict to math operations only by using a whitelist of allowed
    # functions and operators. For a real app, use a proper expression parser.
    try:
        # Build a safe namespace with only math functions
        safe_namespace = {
            "abs": abs, "round": round, "min": min, "max": max,
            "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos,
            "pi": math.pi, "e": math.e, "pow": pow, "log": math.log,
        }
        # Use eval with restricted globals — the expression can only use
        # the functions we explicitly allowed above
        result = eval(expression, {"__builtins__": {}}, safe_namespace)
        return f"Result: {result}"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


# In-memory notes store (in production, use a database or file)
_notes_store: dict[str, str] = {}

def save_note(title: str, content: str) -> str:
    """
    Save a note with a title and content.
    
    Args:
        title: The note title
        content: The note content to save
    
    Returns:
        Confirmation message
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _notes_store[title] = f"[{timestamp}] {content}"
    return f"Note '{title}' saved successfully at {timestamp}."


def read_notes() -> str:
    """
    Read all saved notes.
    
    Returns:
        All notes formatted as text, or a message if no notes exist
    """
    if not _notes_store:
        return "No notes saved yet."
    
    lines = []
    for title, content in _notes_store.items():
        lines.append(f"## {title}\n{content}")
    return "\n\n".join(lines)


# ── Tool schemas (what the model sees) ──
# Each schema follows the Anthropic tool format.
# The 'description' is CRITICAL — it's how the model decides WHICH tool to use.
# Be specific about what each tool does and when to use it.
TOOL_SCHEMAS = [
    {
        "name": "search_web",
        "description": (
            "Search for information about a topic in the knowledge base. "
            "Use this when you need facts, definitions, or explanations "
            "that you don't already know. The query should be keywords, "
            "not a full sentence."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (keywords, e.g., 'python programming language')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate",
        "description": (
            "Evaluate a mathematical expression. Use this for calculations, "
            "conversions, or any math that requires precise computation. "
            "Supports: +, -, *, /, sqrt(), sin(), cos(), log(), pi, e, pow()."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression, e.g., '2 + 2 * 3' or 'sqrt(144)'"
                }
            },
            "required": ["expression"]
        }
    },
    {
        "name": "save_note",
        "description": (
            "Save a note for later reference. Use this when the user asks "
            "you to remember something or save information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "A short title for the note"
                },
                "content": {
                    "type": "string",
                    "description": "The content to save in the note"
                }
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "read_notes",
        "description": (
            "Read all previously saved notes. Use this when the user asks "
            "what notes exist or wants to review saved information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
]

# ── Tool registry: maps tool name → Python function ──
# This pattern (dict of callables) is the simplest and most common
# approach. In larger systems, you might use decorator-based registration
# or a plugin system.
TOOL_REGISTRY = {
    "search_web": search_web,
    "calculate": calculate,
    "save_note": save_note,
    "read_notes": read_notes,
}


# ═══════════════════════════════════════════════════
# STEP 3: The Agentic Loop
# ═══════════════════════════════════════════════════
def agentic_loop(
    user_message: str,
    max_iterations: int = 10,
    verbose: bool = True
) -> str:
    """
    Run the full agentic loop: user input → model → tools → model → ... → final answer.
    
    Args:
        user_message: The user's initial request
        max_iterations: Safety limit — maximum tool-calling rounds
        verbose: Print tool calls and results for debugging
    
    Returns:
        The model's final text response
    """
    
    # ── 3a: Initialize the message history ──
    # The messages list is the "transcript" of the entire interaction.
    # We start with just the user's message, then grow it as the model
    # calls tools and receives results.
    messages = [
        {"role": "user", "content": user_message}
    ]
    
    # ── 3b: THE LOOP ──
    # This is the heart of every AI agent. We iterate until either:
    #   - The model returns a text-only response (no more tools needed)
    #   - We exceed max_iterations (safety valve)
    for iteration in range(1, max_iterations + 1):
        if verbose:
            print(f"\n{'─'*40}\n[ITERATION {iteration}/{max_iterations}]\n{'─'*40}")
        
        # ── Call the model with current messages + available tools ──
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=(
                "You are a research assistant. Use tools to gather information "
                "before answering. Always cite sources from search results. "
                "If you save a note, confirm what was saved."
            ),
            tools=TOOL_SCHEMAS,
            messages=messages
        )
        
        # ── 3c: Check stop reason ──
        # "end_turn" = model is done talking, no tools needed
        # "tool_use" = model wants to use one or more tools
        if verbose:
            print(f"  stop_reason: {response.stop_reason}")
        
        if response.stop_reason == "end_turn":
            # 🎉 EXIT PATH 1: Model produced a final text answer
            # Return the text content directly
            final_text = response.content[0].text if response.content else ""
            if verbose:
                print(f"\n{'='*60}\nFINAL ANSWER:\n{'='*60}")
            return final_text
        
        # ── 3d: Collect all tool_use blocks from the response ──
        # A single response can contain MULTIPLE tool_use blocks.
        # The model might say "I need both the weather AND a calculation."
        # We handle all of them before the next model call.
        tool_use_blocks = [
            block for block in response.content
            if block.type == "tool_use"
        ]
        
        if not tool_use_blocks:
            # Guard: stop_reason said "tool_use" but no tool blocks found
            # This can happen on edge cases; return whatever text we have
            return response.content[0].text if response.content else "No response"
        
        # ── 3e: Execute ALL tool calls (parallel dispatch) ──
        # First, save the model's response (with tool_use blocks) to history.
        # We MUST do this before adding results — the conversation order is:
        #   user → assistant(tool_use) → user(tool_results) → assistant(final)
        messages.append({
            "role": "assistant",
            "content": response.content  # Keep ALL content blocks
        })
        
        # Now execute each tool and build the tool_result content blocks
        tool_result_blocks = []
        
        for block in tool_use_blocks:
            tool_name = block.name
            tool_id = block.id
            tool_input = block.input
            
            if verbose:
                print(f"  🔧 {tool_name}({json.dumps(tool_input)})")
            
            # Look up and execute the function
            if tool_name not in TOOL_REGISTRY:
                result = f"Error: unknown tool '{tool_name}'"
            else:
                try:
                    func = TOOL_REGISTRY[tool_name]
                    # **tool_input unpacks dict as keyword args
                    result = func(**tool_input)
                except Exception as e:
                    # CRITICAL: Catch all exceptions so a broken tool
                    # doesn't crash the entire loop. The model can handle
                    # error strings and adjust its approach.
                    result = f"Error executing {tool_name}: {str(e)}"
            
            if verbose:
                # Truncate long results for display
                result_preview = result[:150] + ("..." if len(result) > 150 else "")
                print(f"  📋 → {result_preview}")
            
            # Build the tool_result content block
            # The structure MUST be exactly: type="tool_result", tool_use_id, content
            tool_result_blocks.append({
                "type": "tool_result",
                "tool_use_id": tool_id,
                "content": result
            })
        
        # ── 3f: Append tool results to messages as a USER message ──
        # Even though these are tool results, the role is "user".
        # This is Anthropic's convention — tool results are "injected"
        # into the conversation from the user side.
        messages.append({
            "role": "user",
            "content": tool_result_blocks
        })
        
        # ── Loop continues: next iteration calls model with results ──
    
    # ── 3g: EXIT PATH 2 — Max iterations reached ──
    # If we get here, the model is still trying to use tools after
    # max_iterations rounds. This usually means:
    #   - The model is stuck in a loop (calling the same tool repeatedly)
    #   - The task is genuinely complex and needs more iterations
    #   - A tool is returning results the model can't use
    return (
        f"I've reached the maximum number of tool-calling rounds "
        f"({max_iterations}). Here's what I know so far, but the task "
        f"may be incomplete. Please try a more specific request."
    )


# ═══════════════════════════════════════════════════
# STEP 4: Demo — Multi-step research task
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    # This request requires MULTIPLE tools across MULTIPLE iterations:
    #   1. search_web("python") — research Python
    #   2. search_web("ai") — research AI
    #   3. calculate — compute something
    #   4. save_note — save findings
    # The model autonomously decides the sequence!
    
    task = (
        "Research Python and AI for me. Find information about both topics, "
        "calculate how many years Python has existed (from 1991 to now), "
        "and save the key findings as notes."
    )
    
    print(f"{'='*60}")
    print("RESEARCH ASSISTANT DEMO")
    print(f"{'='*60}")
    print(f"\nUSER REQUEST: {task}")
    
    final_answer = agentic_loop(task, max_iterations=10)
    
    print(final_answer)
    print(f"\n{'='*60}")
    print("SAVED NOTES:")
    print(f"{'='*60}")
    print(read_notes())
```

---

## Sample Output (Abbreviated)

```
============================================================
RESEARCH ASSISTANT DEMO
============================================================

USER REQUEST: Research Python and AI for me. Find information about both 
topics, calculate how many years Python has existed (from 1991 to now), 
and save the key findings as notes.

────────────────────────────────────────
[ITERATION 1/10]
────────────────────────────────────────
  stop_reason: tool_use
  🔧 search_web({"query": "python programming language"})
  📋 → [python] Python is a high-level, interpreted programming language...
  🔧 search_web({"query": "AI artificial intelligence"})
  📋 → [ai] Artificial Intelligence (AI) is the simulation of human intell...

────────────────────────────────────────
[ITERATION 2/10]
────────────────────────────────────────
  stop_reason: tool_use
  🔧 calculate({"expression": "2026 - 1991"})
  📋 → Result: 35

────────────────────────────────────────
[ITERATION 3/10]
────────────────────────────────────────
  stop_reason: tool_use
  🔧 save_note({"title": "Python Overview", "content": "Python is a..."})
  📋 → Note 'Python Overview' saved successfully at 2026-06-21 14:30:00.
  🔧 save_note({"title": "AI Overview", "content": "AI is the..."})
  📋 → Note 'AI Overview' saved successfully at 2026-06-21 14:30:01.

────────────────────────────────────────
[ITERATION 4/10]
────────────────────────────────────────
  stop_reason: end_turn

============================================================
FINAL ANSWER:
============================================================
Here's a summary of my research:

**Python**: Created by Guido van Rossum in 1991, Python is now 35 years old...

**AI**: Artificial Intelligence simulates human intelligence...

I've saved detailed notes for both topics. Is there anything specific 
about Python or AI you'd like to explore further?

============================================================
SAVED NOTES:
============================================================
## Python Overview
[2026-06-21 14:30:00] Python is a...

## AI Overview
[2026-06-21 14:30:01] AI is the simulation of...
```

---

## Loop Termination: Getting It Right

The agentic loop MUST have robust termination. Here are the exit conditions ranked by priority:

| Condition | Priority | Action |
|---|---|---|
| **Model returns text, no tool_use** | 1 (normal) | Return text to user |
| **Max iterations reached** | 2 (safety) | Return partial results with warning |
| **Model calls same tool with same args** | 3 (loop detection) | Break and warn about loop |
| **User interrupt / timeout** | 4 (external) | Clean up and return partial state |

Here's loop detection you can add:

```python
# ═══ LOOP DETECTION (add inside the for loop) ═══
# Track recent tool calls to detect infinite loops
# e.g., if the model calls search_web("python") → gets results →
# calls search_web("python") again with the same query

recent_calls = []  # List of (tool_name, frozenset of input items)

# Inside the loop, before calling the model:
for block in tool_use_blocks:
    call_signature = (block.name, frozenset(block.input.items()))
    recent_calls.append(call_signature)
    
    # Keep only last 5 calls
    recent_calls = recent_calls[-5:]
    
    # If same call appears 3+ times in last 5, it's a loop
    if recent_calls.count(call_signature) >= 3:
        return (
            "I seem to be stuck in a loop calling the same tool repeatedly. "
            "Let me provide what I have so far instead."
        )
```

---

## What We Built

| Feature | State |
|---|---|
| Multi-step tool reasoning | ✅ |
| Parallel tool dispatch (multiple tools per response) | ✅ |
| Tool registry with error handling | ✅ |
| Safety limits (max_iterations) | ✅ |
| Loop detection (optional, code provided) | ✅ |
| Real streaming output | ❌ — Next chapter! |

---

**Previous:** [06 — Single-Step Tool Use](06_single_step_tool_use.md)  
**Next:** [08 — Streaming Tool Calls](08_streaming_tool_calls.md)
