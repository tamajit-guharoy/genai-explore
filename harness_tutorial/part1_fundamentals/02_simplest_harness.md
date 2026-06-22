# Chapter 02 — The Simplest Harness

## What You'll Learn

- How to build a working harness in ~15 lines of Python
- What every line does, why it's there, and what happens if you change it
- How to set up the Anthropic SDK and your API key
- The difference between `text` and `content` blocks in the API response

---

## The Goal

Before we add tools, memory, or streaming, we need to **call a model and get text back**. That's it. One message in, one message out. Everything we build later extends this foundation.

Here's the complete harness:

```python
# ═══════════════════════════════════════════════════
# CHAPTER 02 — The Simplest AI Agent Harness
# ═══════════════════════════════════════════════════
import anthropic  # The official Anthropic Python SDK — handles HTTP, auth, retries

# ═══ STEP 1: Create a client ═══
# The client is our connection to Claude. It holds the API key and base URL.
# You could also read ANTHROPIC_API_KEY from the environment, but explicit
# is better for learning — you can see exactly where auth happens.
client = anthropic.Anthropic(
    # NEVER hard-code API keys in production code!
    # In a real app, use: api_key=os.environ["ANTHROPIC_API_KEY"]
    api_key="sk-ant-..."  # Replace with your actual key
)

# ═══ STEP 2: Define the user's message ═══
# This is what the user typed. In a real app, this comes from input(),
# a chat UI, a Slack message, etc. We hard-code it here for the example.
user_message = "Explain quantum computing in one sentence."

# ═══ STEP 3: Call the model ═══
# This is the entire harness in one method call. Let's break it down:
response = client.messages.create(
    # ── Model selection ──
    # "claude-sonnet-4-20250514" is the model ID — this is a specific snapshot.
    # Using a dated snapshot (not "claude-sonnet-4" alias) means your harness
    # behavior won't silently change when Anthropic updates the model.
    model="claude-sonnet-4-20250514",

    # ── Max output tokens ──
    # Safety valve: the model can't burn through your budget with an infinite
    # response. 1024 tokens is ~750 words — generous for a single answer.
    max_tokens=1024,

    # ── Messages array ──
    # The API expects a list of message objects. Each message has a "role"
    # (either "user" or "assistant") and content. Right now we only have one
    # message — the user's question. In Chapter 03, this array grows.
    messages=[
        {
            "role": "user",
            "content": user_message
        }
    ]
)

# ═══ STEP 4: Extract and print the response ═══
# The response object has a .content attribute which is a LIST of content blocks.
# For simple text responses, there's one block of type "text".
# We grab the .text attribute of the first block.
# If you omit [0], you get the whole list — try it and see!
answer = response.content[0].text
print(answer)
```

---

## Running It

First, install the SDK and set your key:

```bash
# Install the Anthropic Python SDK
pip install anthropic

# Set your API key (get one at https://console.anthropic.com)
export ANTHROPIC_API_KEY="sk-ant-..."

# Run the script
python simplest_harness.py
```

Sample output:

```
Quantum computing harnesses the principles of quantum mechanics — 
superposition, entanglement, and interference — to process information 
in ways that classical computers cannot, potentially solving certain 
problems exponentially faster.
```

---

## Line-by-Line: Why Each Choice Matters

### `import anthropic`

Why not `import openai`? Both are valid. We use Anthropic because:
- Anthropic's tool-use content blocks are more structured (typed content blocks vs. JSON-in-string)
- The SDK has first-class streaming support for tool calls
- It's the most widely-used provider for agentic workloads in 2025-2026

### `client = anthropic.Anthropic(api_key=...)`

Creating a client once and reusing it is important. The client manages connection pooling — creating a new client per request is wasteful. In a real app, you'd create this at module level or pass it via dependency injection.

### `model="claude-sonnet-4-20250514"`

Always use **dated model snapshots** in production. The alias `claude-sonnet-4` points to the latest snapshot, which can change behavior under your feet. A dated snapshot is immutable — your harness behaves the same way every time.

### `max_tokens=1024`

This is your **budget control**. Every token costs money. Without `max_tokens`, the model could theoretically generate until it hits its context limit (200K tokens), which would be expensive and useless for a short answer.

### `messages=[{"role": "user", "content": user_message}]`

The messages array is the central data structure of every harness. It's a conversation transcript. Right now it has one entry, but it's already an array because every real conversation will have more. Always wrap your content in a list, even for a single message — the API contract requires it.

### `response.content[0].text`

Why `[0]`? Because `.content` is always a list. For simple text, there's one block. But when the model uses tools (Chapter 05+), `.content` can contain multiple blocks: a `text` block saying "Let me look that up..." followed by a `tool_use` block. Always treating `.content` as a list means our code works the same way whether there are tools or not.

---

## What This Harness Can't Do (Yet)

| Missing Feature | Why It Matters | Added In |
|---|---|---|
| **Conversation history** | Can't have a back-and-forth conversation | Chapter 03 |
| **System prompt** | Can't give the model a personality or instructions | Chapter 04 |
| **Tool calling** | Can't use external functions, APIs, or data | Chapters 05–07 |
| **Streaming** | User waits for the full response before seeing anything | Chapter 08 |
| **Error handling** | API failures crash the script | Exercise for reader |

---

## The Mental Model

Think of this harness as a **function**:

```python
def harness(user_input: str) -> str:
    return model(user_input)
```

That's it. Input: text. Output: text. Every chapter from here extends this function — adding state (Chapter 03), configuration (Chapter 04), and side effects (Chapters 05+).

But the core pattern never changes: **assemble context, call model, return response.** Everything else is decoration around that loop.

---

## Try It Yourself

Before moving on, run the script with:

1. A different model (try `claude-haiku-3-5-20241022` for speed)
2. A lower `max_tokens` (try 50 — watch what happens when the answer gets cut off)
3. Check `response.content` directly (print the whole list, not just `[0].text`)
4. Look at `response.usage` — this shows input and output token counts

Understanding the raw API response is crucial before we start wrapping it in abstractions.

---

**Previous:** [01 — What Is a Harness?](01_what_is_a_harness.md)  
**Next:** [03 — Conversation History](03_conversation_history.md)
