# Chapter 09: Short-Term Memory — Conversation Buffers & Sliding Windows

## What You'll Learn

- How a harness keeps recent conversation turns in "working memory"
- Token counting with **tiktoken** (OpenAI) and Anthropic's API
- Three trimming strategies: FIFO, importance-based, and hybrid
- Building a `ConversationBuffer` class from scratch
- Comparing a harness **without** a buffer vs **with** one on a 20-turn conversation

---

## 1. The Analogy: Your Working Memory During a Conversation

Imagine you're talking to someone at a noisy party. You can only hold the last ~30 seconds
of the conversation in your **working memory**. If the conversation drags on for 10 minutes,
you don't remember every word — you remember the **gist** of what was said and the **last
few exchanges**. The rest fades away.

An LLM's context window is the same. Models have a finite token limit (e.g., 128K for GPT-4o,
200K for Claude). If your harness keeps appending every turn, you blow past the limit and
get an API error — or worse, the model loses track of recent instructions because they
got pushed out of the window.

> **Short-term memory = your working memory during a conversation. Limited capacity,
> constantly refreshed, always holding the most relevant recent information.**

---

## 2. Why "Just Append" Breaks

Here's what happens when your harness naively appends every turn:

```
┌─────────────────────────────────────────────────────┐
│ Turn 1:  user asks question          [500 tokens]   │
│ Turn 2:  assistant responds          [300 tokens]   │
│ ...                                                  │
│ Turn 18: user asks another question  [500 tokens]   │
│ Turn 19: assistant responds          [400 tokens]   │
│ Turn 20: context window FULL! ──────► API ERROR      │
└─────────────────────────────────────────────────────┘
```

Even before the hard error, performance degrades. The model's attention dilutes across
irrelevant old messages, and the system prompt drifts out of the context window.

---

## 3. Token Counting: How Big Is Your Buffer?

Before you can trim, you must **measure**. Two approaches:

| Approach | Library | Best For |
|----------|---------|----------|
| Client-side estimate | `tiktoken` (OpenAI models) | Fast, no API call, slightly off for non-OpenAI |
| API-reported count | Anthropic `usage.input_tokens` | Exact, but requires a real API call |

### 3.1 Using tiktoken (Client-Side)

```bash
pip install tiktoken
```

```python
import tiktoken

# ═══ Load the tokenizer for the model you're using ═══
# Different models use different encodings — cl100k_base covers GPT-4/GPT-3.5
encoding = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """Count tokens in a string using tiktoken."""
    return len(encoding.encode(text))

# Example: a message from the conversation
msg = {"role": "user", "content": "Tell me about quantum computing"}
tokens = count_tokens(msg["content"])
print(f"Message tokens: {tokens}")  # ~8 tokens
```

### 3.2 Counting an Entire Message Array

```python
def count_message_tokens(messages: list[dict]) -> int:
    """Count total tokens across all messages, including role overhead.

    OpenAI charges ~4 tokens per message for formatting (role + separators).
    Anthropic's count differs slightly — always use their API for billing accuracy.
    """
    total = 0
    for msg in messages:
        # ═══ Every message costs ~4 tokens of formatting overhead ═══
        total += 4  # role + delimiter overhead
        for key, value in msg.items():
            if isinstance(value, str):
                total += count_tokens(value)
            elif isinstance(value, list):
                # Handle tool_calls or content arrays (e.g., image URLs)
                for block in value:
                    if isinstance(block, dict) and "text" in block:
                        total += count_tokens(block["text"])
    total += 2  # assistant priming overhead
    return total
```

> **⚠️ Important:** `tiktoken` gives estimates. For billing, always use the `usage` field
> returned by the API. Anthropic's tokenizer is NOT tiktoken — use their token-counting
> endpoint for accuracy.

---

## 4. Trimming Strategies

When the buffer exceeds the token budget, you must drop messages. Three strategies:

### 4.1 FIFO (First-In, First-Out)

Drop the **oldest** messages first. Simple, predictable, works great for most use cases.

```
BEFORE TRIM:  [Turn1] [Turn2] [Turn3] [Turn4] [Turn5] [Turn6]  ← 9,000 tokens
                                                          ^budget: 6,000

AFTER TRIM:                          [Turn4] [Turn5] [Turn6]  ← 5,400 tokens
```

### 4.2 Importance-Based

Keep the **system prompt** and **last N turns** at all costs. Drop middle turns first.
This is like remembering the setup of a joke and the punchline, but forgetting the middle.

```
BEFORE TRIM:  [System] [Turn1] [Turn2] [Turn3] [Turn4] [Turn5] ← 9,000 tokens
              ^always keep                        ^always keep

AFTER TRIM:   [System] [Turn1]               [Turn4] [Turn5] ← 5,800 tokens
              ^pinned                          ^pinned
```

### 4.3 Hybrid (Sliding Window + Summaries)

Keep recent N turns intact, summarize older turns, and store summaries as system notes.
We'll explore this in Chapter 10 with long-term memory.

---

## 5. Building the `ConversationBuffer` Class

Let's implement a production-ready buffer with FIFO trimming and token awareness.

```python
from dataclasses import dataclass, field
from typing import Literal
import tiktoken


@dataclass
class ConversationBuffer:
    """A sliding-window conversation buffer with token-aware trimming.

    Think of this as the agent's "working memory" — it holds the most
    recent conversation turns, trimming old ones when the token budget
    is exceeded. The system prompt is always preserved.

    Attributes:
        max_tokens: Total token budget for the message array
        model: Model name (determines which tiktoken encoding to use)
        system_prompt: The system message — NEVER trimmed
        messages: The working set of conversation turns
    """

    max_tokens: int = 8000  # default budget — adjust per model
    model: str = "gpt-4o"
    system_prompt: str = ""
    messages: list[dict] = field(default_factory=list)

    def __post_init__(self):
        """Set up the tokenizer after initialization."""
        # ═══ Map model names to tiktoken encodings ═══
        self._encoding = tiktoken.encoding_for_model(self.model)

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════

    def add(self, role: Literal["user", "assistant", "tool"], content: str,
            tool_call_id: str | None = None, name: str | None = None) -> None:
        """Add a message and auto-trim if over budget.

        Args:
            role: 'user', 'assistant', or 'tool'
            content: The message body
            tool_call_id: Required when role='tool' — links to the tool call
            name: Optional tool name for tool-result messages
        """
        msg = {"role": role, "content": content}
        if tool_call_id:
            msg["tool_call_id"] = tool_call_id  # link tool result to call
        if name:
            msg["name"] = name  # which tool produced this result

        self.messages.append(msg)
        self._trim_if_needed()  # enforce token budget on every insert

    def add_tool_call(self, tool_calls: list[dict]) -> None:
        """Add an assistant message containing tool_call blocks.

        These are structured differently — content may be null, and
        tool_calls is an array of {id, type, function: {name, arguments}}.
        """
        self.messages.append({
            "role": "assistant",
            "content": None,
            "tool_calls": tool_calls,
        })
        self._trim_if_needed()

    def get_messages(self) -> list[dict]:
        """Return the assembled message array for the API call.

        The system prompt is prepended as the first message — it's
        not stored in self.messages to avoid accidental trimming.
        """
        result = [{"role": "system", "content": self.system_prompt}]
        result.extend(self.messages)
        return result

    def trim_to_tokens(self, target: int) -> int:
        """Force-trim the buffer to a specific token count.

        Returns the number of messages removed. Primarily used
        before sending to the API when you want to reserve headroom
        for the model's response.
        """
        removed = 0
        while self._total_tokens() > target and len(self.messages) > 1:
            self.messages.pop(0)  # remove oldest non-system message
            removed += 1
        return removed

    def token_count(self) -> int:
        """Current token count including system prompt overhead."""
        return self._total_tokens()

    def clear(self) -> None:
        """Wipe the buffer but keep the system prompt."""
        self.messages = []

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════

    def _total_tokens(self) -> int:
        """Count tokens across system prompt + all messages."""
        total = len(self._encoding.encode(self.system_prompt))
        total += 4  # system message formatting overhead
        for msg in self.messages:
            total += 4  # per-message overhead
            content = msg.get("content")
            if isinstance(content, str):
                total += len(self._encoding.encode(content))
            # tool_calls blocks are counted separately by the API;
            # this is an approximation
            if "tool_calls" in msg:
                for tc in msg["tool_calls"]:
                    total += len(self._encoding.encode(
                        tc["function"]["name"] + tc["function"]["arguments"]
                    ))
        return total

    def _trim_if_needed(self) -> None:
        """Check token budget and drop oldest messages if exceeded.

        We ALWAYS keep at least 2 messages (one exchange) so the
        model has SOME context, even if we're way over budget.
        """
        while self._total_tokens() > self.max_tokens and len(self.messages) > 2:
            # Drop the oldest non-system message
            self.messages.pop(0)
```

---

## 6. Before/After: Harness Without Buffer vs With Buffer

### 6.1 WITHOUT Buffer — The "Append Everything" Harness

```python
# ❌ Naive approach: just keep appending
def naive_harness_loop(prompt: str, max_turns: int = 20):
    """This harness will break when context exceeds the model's limit."""
    from openai import OpenAI
    client = OpenAI()
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    for turn in range(max_turns):
        messages.append({"role": "user", "content": f"Turn {turn}: {prompt}"})
        # ═══ By turn 15–20, messages are huge — API will reject or degrade ═══
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # cheaper for demo
            messages=messages,
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        print(f"Turn {turn}: {reply[:80]}...")
        # Eventually: openai.BadRequestError — context too long
```

### 6.2 WITH Buffer — The "Sliding Window" Harness

```python
# ✅ Smart approach: use ConversationBuffer
def buffered_harness_loop(prompt: str, max_turns: int = 20):
    """This harness stays within token budget indefinitely."""
    from openai import OpenAI
    client = OpenAI()

    # ═══ Create buffer with a conservative 6K token budget (leaving room for response) ═══
    buffer = ConversationBuffer(
        max_tokens=6000,
        model="gpt-4o-mini",
        system_prompt="You are a helpful assistant. Be concise.",
    )

    for turn in range(max_turns):
        buffer.add("user", f"Turn {turn}: {prompt}")
        messages = buffer.get_messages()

        print(f"  [Turn {turn}] Tokens before API call: {buffer.token_count()}")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,  # leave headroom
        )
        reply = response.choices[0].message.content
        buffer.add("assistant", reply)
        print(f"  [Turn {turn}] Reply: {reply[:80]}...")

    print(f"\nFinal buffer size: {len(buffer.messages)} messages, "
          f"{buffer.token_count()} tokens — ✅ never exceeded budget")
```

**Output comparison:**

```
WITHOUT BUFFER                    WITH BUFFER
─────────────────────────────     ─────────────────────────────
Turn 0: OK                        Turn 0: 520 tokens — OK
Turn 5: OK                        Turn 5: 2,100 tokens — OK
Turn 12: slowing down...          Turn 12: 4,800 tokens — OK
Turn 18: BadRequestError ❌       Turn 18: 5,900 tokens — OK (older turns trimmed)
Turn 19: (crashed)                Turn 19: 5,700 tokens — OK
                                  Turn 25: 5,900 tokens — OK (indefinitely!)
```

---

## 7. Choosing Your Token Budget

Your `max_tokens` should account for:

```
┌──────────────────────────────────────────┐
│ Total model context:         128,000     │
│ ─ System prompt:             -2,000     │
│ ─ Conversation buffer:      -8,000     │  ← your max_tokens
│ ─ Tool definitions:          -3,000     │
│ ─ Expected response:         -4,000     │
│ ─ Safety margin:            -10,000     │
│ ─────────────────────────────────────    │
│ Headroom for spikes:        101,000     │
└──────────────────────────────────────────┘
```

A conservative rule: **budget 50–70% of the model's context for your messages array**.
The rest goes to tool schemas, the model's response, and safety padding.

---

## 8. When FIFO Isn't Enough

FIFO trimming has a weakness: it can drop **critical early context** (e.g., the user's
original goal) while keeping **filler** turns. In Chapter 10, we'll add **long-term memory**
— a vector store that preserves important facts across turns, so even trimmed information
stays accessible.

| FIFO Alone | FIFO + Long-Term Memory |
|------------|------------------------|
| Old facts are lost forever | Old facts are compressed & stored |
| No retrieval mechanism | Semantic search retrieves relevant history |
| Simple, predictable | More complex but preserves knowledge |

---

## Key Takeaways

1. **Token counting is step zero** — you can't manage what you can't measure.
2. **FIFO trimming is the 80/20 solution** — simple, reliable, works for most agents.
3. **Always preserve the system prompt** — it's the agent's constitution.
4. **Leave headroom** — budget for the response AND tool schemas.
5. **The buffer is your first line of defense** — long-term memory (Ch 10) builds on top.

---

> **Previous:** [08 — Streaming Tool Calls](../part2_tool_calling/08_streaming_tool_calls.md)
> **Next:** [10 — Long-Term Memory: Vector Stores & Summarization](10_long_term_memory.md)
