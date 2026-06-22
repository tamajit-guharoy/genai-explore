# Chapter 03 — Conversation History

## What You'll Learn

- How to turn a one-shot model call into a multi-turn conversation
- The message array as your harness's memory
- Role alternation: why user/assistant ordering matters
- How to trim conversation history when it gets too long
- A working 5-turn conversation example

---

## The Problem with Chapter 02

Our Chapter 02 harness works like a goldfish:

```
User: "What's quantum computing?"
Model: "Quantum computing is..."
User: "Can you simplify that?"       ← Model has NO IDEA what "that" refers to
Model: "Simplify what?"               ← Because it sees only the last message
```

Every call is stateless. The model sees exactly one message and responds. This isn't a conversation — it's a series of independent questions.

---

## The Solution: A Growing Message Array

The Anthropic API (and every other LLM API) accepts an array of messages. Each message has a `role` and `content`. The model reads the entire array in order — it sees the full conversation history.

Here's the mental model shift:

```
Chapter 02:                   Chapter 03:
                                
messages = [                  messages = [
  {role: "user",              {role: "user",
   content: latest_msg}        content: "What's QC?"},
]                              {role: "assistant",
                                content: "QC is..."},
                               {role: "user",
                                content: "Simplify?"},
                               {role: "assistant",
                                content: "Sure! Think..."}
                             ]
```

The harness maintains a **running transcript** and appends every new user message and model response to it.

---

## The Code

```python
# ═══════════════════════════════════════════════════
# CHAPTER 03 — Multi-Turn Conversation Harness
# ═══════════════════════════════════════════════════
import anthropic

# ═══ STEP 1: Create the client (same as Chapter 02) ═══
client = anthropic.Anthropic(
    api_key="sk-ant-..."  # Replace with your key
)

# ═══ STEP 2: Initialize the conversation history ═══
# This is the KEY CHANGE from Chapter 02. Instead of building a fresh
# messages array for each call, we maintain ONE array that grows over time.
# 
# Why start as an empty list? Because we haven't said anything yet.
# Every turn of the conversation, we append the user's message AND the
# model's response to this list. It's a living transcript.
messages = []

# ═══ STEP 3: Add a system message (optional but recommended) ═══
# System messages set the ground rules. They're NOT part of the conversation
# history — they sit ABOVE it and influence every response. We'll go deep
# on system prompts in Chapter 04, but adding one now makes the demo better.
# 
# The system parameter is separate from the messages array. It doesn't
# have a "role" — it's always "system" implicitly.
system_prompt = "You are a helpful assistant. Keep answers concise."

# ═══ STEP 4: The conversation loop ═══
# We'll simulate a 5-turn conversation by pre-defining user inputs.
# In a real app, this would be input() or a UI callback.
user_inputs = [
    "What's quantum computing?",
    "Can you explain it like I'm 5?",
    "What's superposition?",
    "How is this different from a regular computer?",
    "Thanks! Summarize everything we discussed."
]

for i, user_input in enumerate(user_inputs, start=1):
    # ── 4a: Add user message to history ──
    # Every user input gets appended to the transcript before we call the model.
    # This is how the model "remembers" what the user said earlier.
    # We use a dict with "role" and "content" — the API's required format.
    messages.append({
        "role": "user",
        "content": user_input
    })

    # ── 4b: Call the model with the FULL history ──
    # Notice: we pass the ENTIRE messages list, not just the latest message.
    # The model reads all previous turns to understand context.
    # This is why the model can respond to "Simplify that?" — "that" is in
    # the earlier messages the model can see.
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,   # System prompt injected here (not in messages)
        messages=messages        # Full conversation transcript
    )

    # ── 4c: Extract the model's answer ──
    # Same as Chapter 02 — first content block, .text attribute.
    # In later chapters, this might be a tool_use block instead of text.
    answer = response.content[0].text

    # ── 4d: Add the model's response to history ──
    # CRITICAL: We MUST append the model's response to the messages list.
    # If we don't, the next call will show the user asking two questions
    # in a row with no assistant response between them — the model gets
    # confused and the API might reject it (roles must alternate).
    messages.append({
        "role": "assistant",
        "content": answer
    })

    # ── 4e: Print the turn ──
    # In a real chat UI, you'd stream this (Chapter 08) and format it nicely.
    print(f"\n{'='*60}")
    print(f"TURN {i}")
    print(f"{'='*60}")
    print(f"User: {user_input}")
    print(f"Assistant: {answer}")

# ═══ STEP 5: Inspect the final messages array ═══
# This shows you the full transcript — 10 messages (5 user + 5 assistant).
# Understanding this structure is how you debug harness behavior.
print(f"\n{'='*60}")
print(f"FINAL STATE: {len(messages)} messages in history")
print(f"{'='*60}")
for msg in messages:
    # Truncate long messages for display
    content_preview = msg["content"][:80] + ("..." if len(msg["content"]) > 80 else "")
    print(f"  [{msg['role']}] {content_preview}")
```

---

## Sample Output (Abbreviated)

```
============================================================
TURN 1
============================================================
User: What's quantum computing?
Assistant: Quantum computing is a type of computation that uses quantum
bits (qubits) instead of classical bits. Unlike classical bits that are
either 0 or 1, qubits can exist in multiple states simultaneously...

============================================================
TURN 2
============================================================
User: Can you explain it like I'm 5?
Assistant: Imagine you have a coin. A regular computer thinks of the coin
as either heads OR tails — one at a time. A quantum computer thinks of
the coin as spinning in the air — it's kind of heads AND tails at the
same time! This lets it try many answers at once...

============================================================
TURN 3
============================================================
User: What's superposition?
Assistant: Superposition is exactly that "spinning coin" idea! It means a
qubit can be in multiple states at once — not just 0 or 1, but a blend of
both. It's like being in two places at the same time...

============================================================
TURN 4
============================================================
User: How is this different from a regular computer?
Assistant: A regular computer processes one thing at a time — it's like
solving a maze by trying every path one by one. A quantum computer uses
superposition to try ALL paths simultaneously. For certain problems...

============================================================
TURN 5
============================================================
User: Thanks! Summarize everything we discussed.
Assistant: Here's a summary:
1. Quantum computing uses qubits that can be 0, 1, or both (superposition)
2. It's like a spinning coin vs. a coin showing heads/tails
3. Regular computers try one path at a time; quantum computers try all at once
4. It's great for specific problems like factoring, simulation, and search

============================================================
FINAL STATE: 10 messages in history
============================================================
  [user] What's quantum computing?
  [assistant] Quantum computing is a type of computation that uses quantum bits (qubits) in...
  [user] Can you explain it like I'm 5?
  [assistant] Imagine you have a coin. A regular computer thinks of the coin as either head...
  [user] What's superposition?
  [assistant] Superposition is exactly that "spinning coin" idea! It means a qubit can be in...
  [user] How is this different from a regular computer?
  [assistant] A regular computer processes one thing at a time — it's like solving a maze by...
  [user] Thanks! Summarize everything we discussed.
  [assistant] Here's a summary:...
```

---

## The Golden Rule: Role Alternation

The LLM API requires messages to strictly alternate between `user` and `assistant` roles. You can never have:

```
❌ [user, user, assistant]     ← Two users in a row — API error!
❌ [assistant, assistant, user] ← Two assistants in a row — API error!
✅ [user, assistant, user, assistant, user]  ← Always alternates
```

This is why **you must always append the model's response back to the messages array** before the next call. If you forget, the next call sends two user messages in a row and the API rejects it.

---

## The Window Problem: When Conversations Get Too Long

Our harness has a hidden bug. After 100 turns, the messages array is 200 messages long and likely exceeds the model's context window (200K tokens for Claude). When that happens, the API either:

1. Rejects the request (too many tokens)
2. Silently drops the oldest messages (model loses context)

To solve this, we need **window trimming** — removing old messages when the total gets too large:

```python
# ═══ WINDOW TRIMMING (add before the model call) ═══
# This is a SIMPLE trimmer — it keeps only the last N messages.
# Production harnesses use smarter strategies (keep system-level
# context, summarize old turns, use sliding windows). But this
# naive approach prevents crashes and is easy to understand.

MAX_HISTORY_MESSAGES = 20  # Keep last 20 messages (10 turns)

if len(messages) > MAX_HISTORY_MESSAGES:
    # Keep the most recent messages. Always trim from the FRONT (oldest).
    # Trimming from the back would delete the user's latest question!
    messages = messages[-MAX_HISTORY_MESSAGES:]
    print(f"[Trimmed history to last {MAX_HISTORY_MESSAGES} messages]")
```

Better strategies (for later chapters):
- **Summarization**: Before dropping old messages, ask the model to summarize them
- **Sliding window with overlap**: Keep the last N messages plus the first system-level context
- **Token counting**: Use `client.count_tokens()` to trim based on actual token count, not message count

---

## What We Built vs. What's Missing

| Feature | State |
|---|---|
| Multi-turn conversation | ✅ Working |
| Message array management | ✅ Working |
| Simple window trimming | ✅ Added |
| Persistent storage (database) | ❌ Not yet — messages live in memory |
| Smart context management | ❌ Not yet — naive trimming |
| Persona / system prompt depth | ❌ Not yet — next chapter! |

---

## Try It Yourself

1. Remove the `messages.append({"role": "assistant", ...})` line and run — watch the API error
2. Set `MAX_HISTORY_MESSAGES = 4` and add more turns — see how the model loses context
3. Add a `"role": "user"` message without adding the assistant response — see the role alternation error
4. Print `response.usage.input_tokens` at each turn — watch it grow

---

**Previous:** [02 — The Simplest Harness](02_simplest_harness.md)  
**Next:** [04 — System Prompts & Personality](04_system_prompts_personality.md)
