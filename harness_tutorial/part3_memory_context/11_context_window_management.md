# Chapter 11: Context Window Management — The Hybrid Approach

## What You'll Learn

- Why the context window is the most **scarce and precious resource** in AI agents
- The **"mega-context" pattern**: what deserves a slot in the limited window
- Priority ordering: system > recent > retrieved > summaries > scratchpad
- Context **budget allocation** with percentage-based quotas
- Building a `ContextBuilder` that assembles the final messages array from all sources
- How different allocation strategies affect agent performance on long tasks

---

## 1. The Analogy: Packing a Suitcase

You're going on a week-long trip. Your suitcase has **fixed volume** (the context window).
You can't bring your entire wardrobe — you must **prioritize**:

- **Essentials** (system prompt): passport, wallet, phone charger. Always packed first.
- **Today's outfit** (recent messages): what you're wearing RIGHT NOW.
- **Weather-dependent items** (retrieved memories): umbrella if rain, sunscreen if sun.
- **Itinerary notes** (summaries): the compressed plan for the week.
- **Empty space** (scratchpad): room for souvenirs (the model's response).

> **Context window management = packing a suitcase with fixed volume. Every item
> competes for space. You need a system for deciding what makes the cut.**

---

## 2. The Five Zones of Context

```
┌──────────────────────────────────────────────────────────────────────┐
│                    128,000 TOKEN CONTEXT WINDOW                       │
│                                                                      │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ ZONE 1: SYSTEM PROMPT                   (~20% = 25,600 tokens)   │ │
│ │  • Agent's role, rules, constraints                               │ │
│ │  • Tool definitions (more on these in Part 2)                     │ │
│ │  • NEVER trimmed — the agent's constitution                        │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ ZONE 2: RECENT CONVERSATION              (~50% = 64,000 tokens)  │ │
│ │  • Last N turns from ConversationBuffer                           │ │
│ │  • Full fidelity — every word preserved                           │ │
│ │  • This is the "working surface" the agent operates on             │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ ZONE 3: RETRIEVED MEMORIES               (~20% = 25,600 tokens)  │ │
│ │  • Top-K search results from MemoryStore                           │ │
│ │  • Only injected when semantically relevant                        │ │
│ │  • Acts as "context boosters" for the current query                │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ ZONE 4: SUMMARIES                        (~5%  = 6,400 tokens)   │ │
│ │  • Compressed narrative of older turns                             │ │
│ │  • Provides "the story so far" without verbatim messages           │ │
│ └──────────────────────────────────────────────────────────────────┘ │
│ ┌──────────────────────────────────────────────────────────────────┐ │
│ │ ZONE 5: SCRATCHPAD                      (~5%  = 6,400 tokens)    │ │
│ │  • Reserved for the model's response                               │ │
│ │  • Also used for tool call results and chain-of-thought            │ │
│ └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. Priority Ordering — What Gets Cut First?

When the window is full, we drop items in this order:

```
PRIORITY (highest → lowest):
═══════════════════════════════════════════════════════════

1. SYSTEM PROMPT           ████████████████  NEVER cut
2. RECENT TURNS (last 3)   ████████████████  NEVER cut (the agent needs immediate context)
3. RECENT TURNS (older)    ████████████░░░░  Cut oldest first (FIFO)
4. RETRIEVED MEMORIES      ████████░░░░░░░░  Drop low-similarity results first
5. SUMMARIES               ████░░░░░░░░░░░░  Truncate to shorter version
6. SCRATCHPAD              ░░░░░░░░░░░░░░░░  Shrink response max_tokens
```

---

## 4. Building the `ContextBuilder` Class

This is the **orchestrator** that combines buffer, memory, and summaries into
one final message array — respecting the token budget at every layer.

```python
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class ContextBudget:
    """Token allocation percentages for each context zone.

    The percentages should sum to ~100% (excluding scratchpad,
    which is reserved headroom for the model's response).

    Example for a 128K context window:
        system:    0.20 →  25,600 tokens
        recent:    0.50 →  64,000 tokens
        memory:    0.20 →  25,600 tokens
        summaries: 0.05 →   6,400 tokens
        headroom:  0.05 →   6,400 tokens (scratchpad/response)
    """

    system: float = 0.20      # system prompt + tool definitions
    recent: float = 0.50      # conversation buffer (verbatim turns)
    memory: float = 0.20      # retrieved from vector store
    summaries: float = 0.05   # compressed older segments
    headroom: float = 0.05    # reserved for model response


@dataclass
class ContextBuilder:
    """Assembles the final messages array from all memory sources.

    This is the "packing algorithm" — it takes the system prompt,
    conversation buffer, vector store results, and summaries, then
    assembles them into a single messages array that fits within
    the model's context window.

    Think of it as a Tetris player, fitting blocks of context into
    a fixed-width container by dropping the least important pieces first.
    """

    model_context_limit: int = 128_000  # total tokens the model can handle
    budget: ContextBudget = field(default_factory=ContextBudget)

    def __post_init__(self):
        """Precompute token limits for each zone."""
        self._limits = {
            "system":    int(self.model_context_limit * self.budget.system),
            "recent":    int(self.model_context_limit * self.budget.recent),
            "memory":    int(self.model_context_limit * self.budget.memory),
            "summaries": int(self.model_context_limit * self.budget.summaries),
            "headroom":  int(self.model_context_limit * self.budget.headroom),
        }

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════

    def build(self,
              system_prompt: str,
              buffer: "ConversationBuffer",
              memory: "MemoryStore | None" = None,
              query: str = "",
              tool_definitions: list[dict] | None = None,
              ) -> list[dict]:
        """Assemble the complete messages array for an API call.

        Args:
            system_prompt: The agent's constitution (Zone 1)
            buffer: Current conversation buffer (Zone 2)
            memory: Optional long-term memory store (Zone 3)
            query: Current user query (for memory retrieval)
            tool_definitions: Tool schemas (counted in Zone 1 budget)

        Returns:
            List of message dicts ready for the API
        """
        messages = []

        # ═══ ZONE 1: System prompt — always first, always preserved ═══
        system_msg = self._build_system_message(system_prompt, tool_definitions)
        messages.append(system_msg)

        # ═══ ZONE 4: Summaries — compressed narrative (goes before recent for flow) ═══
        if memory:
            summary_text = self._get_latest_summary(memory)
            if summary_text:
                # Insert as a system-level context note
                messages.append({
                    "role": "system",
                    "content": f"[SESSION SUMMARY]\n{summary_text}",
                })

        # ═══ ZONE 3: Retrieved memories — injected before the user's query ═══
        if memory and query:
            retrieved = self._retrieve_and_rank(memory, query)
            if retrieved:
                memory_block = "Relevant context from previous exchanges:\n" + "\n".join(
                    f"- {r['text']}" for r in retrieved
                )
                # Inject as a system message so it doesn't look like user input
                messages.append({
                    "role": "system",
                    "content": f"[RETRIEVED MEMORY]\n{memory_block}",
                })

        # ═══ ZONE 2: Recent conversation — the working buffer ═══
        # Trim the buffer to fit within the 'recent' zone budget
        budget_messages = self._fit_buffer_to_budget(
            buffer.messages, self._limits["recent"]
        )
        messages.extend(budget_messages)

        # ═══ Final safety check: trim everything if still over budget ═══
        total_tokens = self._count_messages(messages)
        if total_tokens > self.model_context_limit - self._limits["headroom"]:
            # Emergency trim: cut from the middle of the conversation
            messages = self._emergency_trim(messages)

        return messages

    def get_allocation_report(self, messages: list[dict]) -> str:
        """Return a human-readable breakdown of token usage by zone.

        Useful for debugging why the agent seems to "forget" things —
        you can see exactly where tokens are going.
        """
        report = []
        zone_tokens = {"system": 0, "memory": 0, "summaries": 0, "recent": 0}
        current_zone = "system"

        for msg in messages:
            content = msg.get("content", "") or ""
            # Detect zone from message markers
            if "[RETRIEVED MEMORY]" in str(content):
                current_zone = "memory"
            elif "[SESSION SUMMARY]" in str(content):
                current_zone = "summaries"
            elif msg["role"] in ("user", "assistant", "tool"):
                current_zone = "recent"

            zone_tokens[current_zone] += self._count_tokens(str(msg))

        total = sum(zone_tokens.values())
        for zone, tokens in zone_tokens.items():
            pct = (tokens / total * 100) if total else 0
            limit = self._limits.get(zone, 0)
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            report.append(
                f"{zone:12s} {tokens:>6d} tokens ({pct:5.1f}%) [{bar}] "
                f"limit: {limit:,}"
            )

        report.append(f"{'TOTAL':12s} {total:>6d} tokens")
        report.append(f"{'HEADROOM':12s} {self.model_context_limit - total:>6d} tokens")
        return "\n".join(report)

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════

    def _build_system_message(self, prompt: str,
                              tools: list[dict] | None) -> dict:
        """Build the system message, optionally appending tool schemas."""
        content = prompt
        if tools:
            # ═══ Include tool names/descriptions in the system message ═══
            # The actual tool schemas go to the API separately, but including
            # descriptions here helps the model understand its capabilities
            tool_list = "\n".join(
                f"- {t['function']['name']}: {t['function'].get('description', '')}"
                for t in tools
            )
            content += f"\n\nAvailable tools:\n{tool_list}"
        return {"role": "system", "content": content}

    def _get_latest_summary(self, memory: "MemoryStore") -> str | None:
        """Retrieve the most recent session summary from the vector store."""
        results = memory.search("session summary conversation", k=1)
        for r in results:
            if r.get("metadata", {}).get("type") == "summary":
                return r["text"]
        return None

    def _retrieve_and_rank(self, memory: "MemoryStore",
                           query: str) -> list[dict]:
        """Search memory and filter by relevance threshold."""
        results = memory.search(query, k=10)

        # ═══ Only keep results within a distance threshold ═══
        # distance < 0.5 means "reasonably similar" (cosine distance)
        filtered = [r for r in results if r["distance"] < 0.5]

        # ═══ Truncate each result to stay within memory zone budget ═══
        max_per_result = self._limits["memory"] // max(len(filtered), 1)
        for r in filtered:
            r["text"] = self._truncate_text(r["text"], max_per_result)

        return filtered

    def _fit_buffer_to_budget(self, messages: list[dict],
                              token_limit: int) -> list[dict]:
        """Trim buffer messages to fit within the token limit.

        Strategy: Always keep the last 2 exchanges (4 messages),
        trim from the front (oldest) first.
        """
        result = list(messages)  # shallow copy
        while len(result) > 4 and self._count_messages(result) > token_limit:
            result.pop(0)  # remove oldest first
        return result

    def _emergency_trim(self, messages: list[dict]) -> list[dict]:
        """Last resort: aggressively drop non-system messages from the middle."""
        headroom = self._limits["headroom"]
        # Keep system prompt (index 0) and last 2 messages
        while len(messages) > 3:
            if self._count_messages(messages) <= self.model_context_limit - headroom:
                break
            # Remove from index 1 (after system, before last 2)
            del messages[1]
        return messages

    @staticmethod
    def _count_tokens(text: str) -> int:
        """Estimate tokens. Replace with tiktoken in production."""
        return len(text) // 4  # rough heuristic: ~4 chars per token

    @staticmethod
    def _count_messages(messages: list[dict]) -> int:
        """Count total estimated tokens across all messages."""
        return sum(ContextBuilder._count_tokens(str(m)) for m in messages)

    @staticmethod
    def _truncate_text(text: str, max_tokens: int) -> str:
        """Truncate text to roughly max_tokens."""
        chars = max_tokens * 4
        if len(text) <= chars:
            return text
        return text[:chars] + "..."
```

---

## 5. How Budget Allocations Affect Performance

Let's compare three strategies on a 30-turn coding task:

| Strategy | System | Recent | Memory | Summaries | Result |
|----------|--------|--------|--------|-----------|--------|
| **Recent-heavy** | 20% | 60% | 10% | 10% | Great immediate recall, forgets early decisions ❌ |
| **Memory-heavy** | 20% | 30% | 40% | 10% | Good fact retrieval, loses conversational coherence ❌ |
| **Balanced** (recommended) | 20% | 50% | 20% | 10% | Best of both worlds ✅ |

```python
# ═══ Testing different budgets ═══
def benchmark_budgets(task_description: str, turns: int = 30):
    """Compare different ContextBudget configurations."""
    budgets = {
        "recent-heavy": ContextBudget(recent=0.60, memory=0.10, summaries=0.10),
        "memory-heavy": ContextBudget(recent=0.30, memory=0.40, summaries=0.10),
        "balanced":     ContextBudget(recent=0.50, memory=0.20, summaries=0.10),
    }

    for name, budget in budgets.items():
        builder = ContextBuilder(budget=budget)
        # ... run harness with this builder ...
        # ... measure: task completion, fact recall, coherence ...
        print(f"{name:15s}: allocation={budget}")
```

---

## 6. The Complete Memory Pipeline

Bringing together Chapters 9, 10, and 11:

```python
def complete_harness_with_memory(user_input: str, system_prompt: str,
                                  tools: list[dict] | None = None):
    """A harness integrating ALL memory systems from Chapters 9-11.

    This is the full "memory stack":
        ContextBuilder (this chapter) ── orchestrator
          ├── ConversationBuffer (Ch 9) ── short-term
          └── MemoryStore (Ch 10) ── long-term
    """
    from openai import OpenAI

    client = OpenAI()

    # ═══ Initialize the three components ═══
    buffer = ConversationBuffer(
        max_tokens=64000,  # will be further trimmed by ContextBuilder
        model="gpt-4o",
        system_prompt=system_prompt,
    )
    memory = MemoryStore(llm_client=client)
    builder = ContextBuilder(
        model_context_limit=128_000,
        budget=ContextBudget(),  # default balanced allocation
    )

    # ═══ Add the user's message ═══
    buffer.add("user", user_input)

    # ═══ Build the context (orchestrates all memory sources) ═══
    messages = builder.build(
        system_prompt=system_prompt,
        buffer=buffer,
        memory=memory,
        query=user_input,
        tool_definitions=tools,
    )

    # ═══ Show allocation before the API call ═══
    print(builder.get_allocation_report(messages))
    print("\n" + "=" * 60 + "\n")

    # ═══ Call the API ═══
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools,
        max_tokens=builder._limits["headroom"],  # use headroom for response
    )

    reply = response.choices[0].message.content
    buffer.add("assistant", reply)

    # ═══ Auto-save to long-term memory ═══
    if len(reply) > 50:
        memory.add_fact(
            f"Q: {user_input[:200]}\nA: {reply[:200]}",
            metadata={"type": "exchange"},
        )

    return reply, buffer, memory
```

**Sample allocation report:**

```
system        3,200 tokens ( 5.1%) [██░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] limit: 25,600
summaries         0 tokens ( 0.0%) [░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] limit: 6,400
memory        2,100 tokens ( 3.3%) [█░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░] limit: 25,600
recent       57,800 tokens (91.6%) [██████████████████████████████████████████████░░░░░] limit: 64,000
TOTAL        63,100 tokens
HEADROOM     64,900 tokens
```

---

## 7. Advanced: Dynamic Budget Rebalancing

Static budgets work for simple agents. For complex ones, rebalance dynamically
based on the task:

```python
def dynamic_budget(task_type: Literal["chat", "coding", "research", "multi_step"]
                   ) -> ContextBudget:
    """Choose budget allocation based on task type.

    - Chat: recent-heavy (conversational flow matters most)
    - Coding: memory-heavy (need to recall coding conventions, earlier decisions)
    - Research: balanced (mix of recent findings and retrieved knowledge)
    - Multi-step: summary-heavy (need compressed plan of completed steps)
    """
    budgets = {
        "chat":       ContextBudget(recent=0.60, memory=0.10, summaries=0.10),
        "coding":     ContextBudget(recent=0.40, memory=0.30, summaries=0.10),
        "research":   ContextBudget(recent=0.45, memory=0.25, summaries=0.10),
        "multi_step": ContextBudget(recent=0.40, memory=0.15, summaries=0.25),
    }
    return budgets.get(task_type, ContextBudget())
```

---

## 8. Debugging: Why Is My Agent "Forgetting"?

Common issues and their fixes:

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Agent forgets system prompt after 10 turns | System prompt pushed out by long conversation | Reduce `budget.recent`, or make system prompt shorter |
| Agent can't recall earlier decisions | Memory not being retrieved | Lower distance threshold in `_retrieve_and_rank` |
| Agent gives short, confused answers | Context too full, model overwhelmed | Increase `headroom`, reduce other zones |
| High API cost, slow responses | Sending too many tokens per call | Tighten all budget percentages |

---

## Key Takeaways

1. **The context window is finite — treat it as a budget, not a dump.**
2. **Percentages over absolute numbers** — budgets that scale with model context
   limits are portable across models.
3. **Priority order is non-negotiable**: system > recent > memory > summaries.
4. **The ContextBuilder is the single source of truth** for message assembly.
5. **Debug with allocation reports** — if something's missing, the report tells
   you why.

---

> **Previous:** [10 — Long-Term Memory: Vector Stores & Summarization](10_long_term_memory.md)
> **Next:** [12 — Error Handling & Retries](../part4_production/12_error_handling_retries.md)
