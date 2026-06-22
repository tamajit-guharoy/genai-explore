# Chapter 08 — Streaming Tool Calls

## What You'll Learn

- Why streaming matters for user experience in agentic applications
- The challenge: tool_use content blocks arrive as deltas (fragments)
- The buffering strategy: accumulate partial JSON until a tool call is complete
- How to stream text output while buffering tool calls simultaneously
- UX considerations: streaming "thinking" text while tools execute

---

## Why Streaming Matters

In Chapter 07, our agentic loop works — but it's a black box to the user. They send a message, wait 5–30 seconds, and eventually get a response. During that time, they see... nothing.

This is terrible UX. It's like calling a plumber who disappears under your sink for an hour with no communication. You have no idea if they're making progress, stuck, or taking a nap.

**Good streaming gives the user visibility into what the agent is doing:**

```
User: "Research quantum computing and save notes."

[STREAMING]
Assistant: Let me search for information about quantum computing...
           [🔧 Calling: search_web("quantum computing")]
           [📋 Result: Quantum computing uses qubits...]
           Now let me save that as a note...
           [🔧 Calling: save_note(...)]
           [📋 Note saved!]
           I've researched quantum computing and saved the key
           findings as a note. The main points are...
```

Every step is visible. The user has confidence the agent is working correctly.

---

## The Challenge: Tool Calls Arrive as Deltas

When you stream Anthropic responses (using `stream=True`), you don't get complete messages — you get **events**:

```
Event: message_start        → Metadata about the message
Event: content_block_start  → A new content block is starting (text or tool_use)
Event: content_block_delta  → A chunk of content (text delta or partial JSON)
Event: content_block_delta  → Another chunk...
Event: content_block_delta  → Another chunk...
Event: content_block_stop   → Content block is complete
...
Event: message_delta        → stop_reason, usage info
Event: message_stop         → Message is done
```

For text blocks, streaming is easy: accumulate deltas and print them as they arrive.

For tool_use blocks, the deltas contain **partial JSON** — fragments of the `input` object:

```
Delta 1: '{"ci'
Delta 2: 'ty": "To'
Delta 3: 'kyo"}'
```

You can't execute the tool until you have the **complete** JSON. So you must **buffer** it.

---

## The Buffering Strategy

```
┌─────────────────────────────────────────────────────┐
│                 STREAM HANDLER                       │
│                                                      │
│  ┌──────────────────┐   ┌─────────────────────────┐ │
│  │ TEXT BLOCK       │   │ TOOL_USE BLOCK          │ │
│  │                  │   │                         │ │
│  │ Delta: "Let me"  │   │ Delta: '{"ci'           │ │
│  │ → Print it now!  │   │ → ACCUMULATE (buffer)  │ │
│  │                  │   │                         │ │
│  │ Delta: " check"  │   │ Delta: 'ty":'          │ │
│  │ → Print it now!  │   │ → ACCUMULATE           │ │
│  │                  │   │                         │ │
│  │ Delta: " the..." │   │ Delta: '"Tokyo"}'      │ │
│  │ → Print it now!  │   │ → ACCUMULATE           │ │
│  │                  │   │                         │ │
│  │ BLOCK STOP       │   │ BLOCK STOP              │ │
│  │ → Done, nothing  │   │ → PARSE complete JSON   │ │
│  │   to finalize    │   │ → EXECUTE tool          │ │
│  └──────────────────┘   └─────────────────────────┘ │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## The Code: Streaming Agentic Loop

```python
# ═══════════════════════════════════════════════════
# CHAPTER 08 — Streaming Tool Calls
# ═══════════════════════════════════════════════════
import anthropic
import json
import datetime

# ═══ STEP 1: Create the client ═══
client = anthropic.Anthropic(
    api_key="sk-ant-..."  # Replace with your key
)

# ═══════════════════════════════════════════════════
# STEP 2: Tool definitions (from Chapter 07, condensed)
# ═══════════════════════════════════════════════════

KNOWLEDGE_BASE = {
    "python": "Python is a high-level, interpreted programming language created in 1991.",
    "ai": "AI is the simulation of human intelligence by machines.",
    "quantum": "Quantum computing uses qubits that can exist in superposition.",
}

def search_web(query: str) -> str:
    """Search the knowledge base."""
    query_lower = query.lower()
    results = []
    for topic, content in KNOWLEDGE_BASE.items():
        if topic in query_lower:
            results.append(f"[{topic}] {content}")
    return "\n\n".join(results) if results else f"No results for '{query}'"


def calculate(expression: str) -> str:
    """Safely evaluate math."""
    import math
    safe_ns = {"sqrt": math.sqrt, "pi": math.pi, "e": math.e, "pow": pow, "abs": abs}
    try:
        return f"Result: {eval(expression, {'__builtins__': {}}, safe_ns)}"
    except Exception as e:
        return f"Error: {e}"


def save_note(title: str, content: str) -> str:
    """Save a note."""
    return f"Note '{title}' saved."


TOOL_SCHEMAS = [
    {
        "name": "search_web",
        "description": "Search for information about a topic.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query keywords"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "calculate",
        "description": "Evaluate a mathematical expression.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string", "description": "Math expression"}
            },
            "required": ["expression"]
        }
    },
    {
        "name": "save_note",
        "description": "Save a note with title and content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Note title"},
                "content": {"type": "string", "description": "Note content"}
            },
            "required": ["title", "content"]
        }
    },
]

TOOL_REGISTRY = {
    "search_web": search_web,
    "calculate": calculate,
    "save_note": save_note,
}


# ═══════════════════════════════════════════════════
# STEP 3: The Streaming Agentic Loop
# ═══════════════════════════════════════════════════

def streaming_agentic_loop(user_message: str, max_iterations: int = 10) -> str:
    """
    Run the agentic loop with STREAMING output.
    
    Text from the model is printed in real-time.
    Tool calls are buffered until complete, then executed.
    Tool results are displayed as they arrive.
    """
    
    messages = [{"role": "user", "content": user_message}]
    
    for iteration in range(1, max_iterations + 1):
        print(f"\n{'─'*40}\n[ITERATION {iteration}]")
        
        # ── 3a: Start streaming from the model ──
        # We use a context manager (with statement) because the streaming
        # client needs to properly close the HTTP connection when done.
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system="You are a research assistant. Use tools when needed.",
            tools=TOOL_SCHEMAS,
            messages=messages
        ) as stream:
            
            # ── 3b: Initialize buffers for this message ──
            # text_buffer: accumulates ALL text content for history
            # tool_use_blocks: accumulates complete tool_use blocks
            # current_block_type: which block type is currently streaming
            # current_tool_name/id/input_buffer: for the current tool_use block
            
            text_buffer = ""
            tool_use_blocks = []  # Completed tool_use blocks
            
            # State for the block currently being streamed
            current_block_type = None  # "text" or "tool_use"
            current_tool_name = None
            current_tool_id = None
            current_input_buffer = ""  # Accumulated partial JSON
            
            # ── 3c: Process stream events ──
            # The stream yields events one by one. We need to handle:
            #   content_block_start → new block starting
            #   content_block_delta → content fragment
            #   content_block_stop  → block complete
            #   message_delta       → stop_reason, usage
            
            for event in stream:
                # ── New content block starting ──
                if event.type == "content_block_start":
                    block = event.content_block
                    
                    if block.type == "text":
                        # Starting a text block — reset text state
                        current_block_type = "text"
                        # No need to track text block name/id
                    
                    elif block.type == "tool_use":
                        # Starting a tool_use block — capture its metadata
                        current_block_type = "tool_use"
                        current_tool_name = block.name      # e.g., "search_web"
                        current_tool_id = block.id           # e.g., "toolu_01..."
                        current_input_buffer = ""            # Reset JSON buffer
                        
                        # Announce the tool call to the user
                        print(f"\n🔧 Calling: {current_tool_name}...")
                
                # ── Content fragment arriving ──
                elif event.type == "content_block_delta":
                    delta = event.delta
                    
                    if current_block_type == "text":
                        # TEXT DELTA: print directly to user
                        # This is the "streaming" part — the user sees
                        # the model's thinking in real time
                        text = delta.text
                        text_buffer += text
                        # Print without newline (end="") for smooth streaming
                        # flush=True forces immediate output (no buffering)
                        print(text, end="", flush=True)
                    
                    elif current_block_type == "tool_use":
                        # TOOL_USE DELTA: accumulate partial JSON
                        # We CANNOT execute the tool yet — the JSON isn't complete
                        # We just silently buffer the fragments
                        current_input_buffer += delta.partial_json
                
                # ── Content block complete ──
                elif event.type == "content_block_stop":
                    if current_block_type == "text":
                        # Text block done — nothing special, just reset state
                        current_block_type = None
                    
                    elif current_block_type == "tool_use":
                        # Tool_use block complete — parse and record it
                        # Now the JSON buffer is complete, so we can parse it
                        try:
                            tool_input = json.loads(current_input_buffer)
                        except json.JSONDecodeError:
                            # Malformed JSON — the model produced invalid output
                            # This should be rare with modern models but we guard
                            tool_input = {"error": "Failed to parse tool input"}
                        
                        # Record the complete tool_use block
                        tool_use_blocks.append({
                            "name": current_tool_name,
                            "id": current_tool_id,
                            "input": tool_input
                        })
                        
                        # Reset tool-specific state
                        current_block_type = None
                        current_tool_name = None
                        current_tool_id = None
                        current_input_buffer = ""
                
                # ── Message-level metadata ──
                elif event.type == "message_delta":
                    # stop_reason tells us if model is done or wants tools
                    stop_reason = event.delta.stop_reason
                    # usage = event.usage  # Token counts if needed
            
            # ── 3d: Get the final message (accumulated by the SDK) ──
            # After the stream finishes, stream.get_final_message() returns
            # the complete message with properly structured content blocks.
            # This is the cleanest way to get formatted content for history.
            final_message = stream.get_final_message()
            
            # ── 3e: Check if model is done or wants tools ──
            # We need the stop_reason. It's either from the final_message
            # or we captured it from message_delta events.
            stop_reason = final_message.stop_reason
            
            if stop_reason == "end_turn":
                # 🎉 Done! Return accumulated text
                print()  # Final newline
                return text_buffer
            
            # ── 3f: Model wants tools — execute them ──
            if not tool_use_blocks:
                # Edge case: stop_reason is tool_use but no blocks collected
                print("\n[WARNING: tool_use stop but no blocks found]")
                return text_buffer
            
            # Add model's response to history
            # We use final_message.content because it's already properly formatted
            messages.append({
                "role": "assistant",
                "content": final_message.content
            })
            
            # Execute each tool and build result blocks
            tool_result_blocks = []
            
            for tool in tool_use_blocks:
                tool_name = tool["name"]
                tool_id = tool["id"]
                tool_input = tool["input"]
                
                # Execute the tool
                if tool_name in TOOL_REGISTRY:
                    try:
                        result = TOOL_REGISTRY[tool_name](**tool_input)
                    except Exception as e:
                        result = f"Error: {str(e)}"
                else:
                    result = f"Error: unknown tool '{tool_name}'"
                
                # Display the result to the user
                result_preview = result[:120] + ("..." if len(result) > 120 else "")
                print(f"\n📋 Result: {result_preview}")
                
                # Build the tool_result block for the API
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": result
                })
            
            # Add tool results to message history
            messages.append({
                "role": "user",
                "content": tool_result_blocks
            })
            
            # ── Loop continues to next iteration ──
            # The model will now "see" the tool results in its next call
    
    # Max iterations reached
    return "\n\n[Max iterations reached. Task may be incomplete.]"


# ═══════════════════════════════════════════════════
# STEP 4: Demo
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    print("=" * 60)
    print("STREAMING AGENTIC LOOP DEMO")
    print("=" * 60)
    print("\nUser: Research Python and calculate 2 + 2 * 10\n")
    
    final = streaming_agentic_loop(
        "Research Python and calculate 2 + 2 * 10"
    )
    
    print(f"\n\n{'='*60}")
    print("SESSION COMPLETE")
    print(f"{'='*60}")
```

---

## Sample Output

```
============================================================
STREAMING AGENTIC LOOP DEMO
============================================================

User: Research Python and calculate 2 + 2 * 10


────────────────────────────────────────
[ITERATION 1]
Let me research Python and do that calculation for you.
🔧 Calling: search_web...
🔧 Calling: calculate...

📋 Result: [python] Python is a high-level, interpreted programming language created in 1991.

📋 Result: Result: 22

────────────────────────────────────────
[ITERATION 2]
Python was created in 1991 and is known as a high-level, interpreted 
programming language. As for your calculation: 2 + 2 × 10 = 22 
(multiplication takes precedence: 2 × 10 = 20, then 20 + 2 = 22).

============================================================
SESSION COMPLETE
============================================================
```

---

## Key Streaming Events Reference

For quick reference, here are the Anthropic streaming events you'll encounter:

| Event Type | When It Fires | Key Fields |
|---|---|---|
| `message_start` | Once, at the very beginning | `message.id`, `message.model` |
| `content_block_start` | When a new content block begins | `content_block.type`, `content_block.name` (for tool_use) |
| `content_block_delta` | Repeatedly, for each token/JSON fragment | `delta.text` or `delta.partial_json` |
| `content_block_stop` | When a content block finishes | (none — just a signal) |
| `message_delta` | Once, near the end | `delta.stop_reason`, `usage` |
| `message_stop` | Once, at the very end | (none — stream is done) |

---

## UX Consideration: Streaming "Thinking" While Tools Execute

The best agent UX shows **three kinds of output**:

```
┌─────────────────────────────────────────────────────┐
│  🤖 THINKING TEXT (streamed in real-time)           │
│  "Let me look that up... I'll also calculate..."    │
├─────────────────────────────────────────────────────┤
│  🔧 TOOL CALLS (announced when buffered & complete) │
│  [search_web("python")]                             │
│  [calculate("2+2*10")]                              │
├─────────────────────────────────────────────────────┤
│  📋 TOOL RESULTS (shown when execution finishes)    │
│  [python] Python is a...                            │
│  Result: 22                                         │
├─────────────────────────────────────────────────────┤
│  💬 FINAL RESPONSE (streamed, incorporates results) │
│  "Python was created in 1991. 2+2*10 = 22..."       │
└─────────────────────────────────────────────────────┘
```

Our code above already does this. The key insight: text is streamed immediately, but tool calls are **deferred** until the JSON buffer is complete. The user sees the model's thinking process unfold naturally.

---

## What We Built

| Feature | State |
|---|---|
| Real-time text streaming | ✅ |
| Tool call buffering | ✅ |
| Parallel tool calls with streaming | ✅ |
| Proper history management | ✅ |
| UX: thinking text + tool indicators + results | ✅ |

---

**Previous:** [07 — The Agentic Loop](07_the_agentic_loop.md)  
**Next:** [09 — (coming in Part 3)](../part3_advanced/09_error_handling_retries.md)
