# Chapter 23: Full Build — Production Harness (The Capstone)

> **Previous:** [Chapter 22: Architecture Deep-Dive — Omnigent Adapters](22_architecture_omnigent_adapters.md)  
> **Next:** [Appendix A: Minimal Harness](../appendix/A_minimal_harness.py)

---

## What You'll Learn

- How to build a complete `Harness` class (~500 lines) that combines EVERYTHING from chapters 1-22
- Multi-provider support, tool calling, streaming, memory, error handling, logging, cost tracking, session persistence
- The entire class, method by method, with detailed inline comments
- How to run a complex multi-step task end-to-end

> **This is the chapter you bookmark.** It's the reference implementation — copy it, extend it, build on it.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION HARNESS                               │
│                                                                     │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────┐   │
│  │ Provider  │  │  Policy   │  │  Session  │  │    Memory     │   │
│  │  Layer    │  │  Engine   │  │   Store   │  │   (ChromaDB)  │   │
│  │           │  │           │  │           │  │               │   │
│  │ Anthropic │  │ Cost      │  │ SQLite    │  │ Long-term     │   │
│  │ OpenAI    │  │ Allowlist │  │ persistence│  │ vector        │   │
│  │ Gemini    │  │ Approval  │  │           │  │ storage       │   │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └───────┬───────┘   │
│        │              │              │                │            │
│        └──────────────┼──────────────┼────────────────┘            │
│                       │              │                              │
│              ┌────────▼──────────────▼────────┐                    │
│              │         AGENTIC LOOP           │                    │
│              │                                │                    │
│              │  • Streaming with buffering    │                    │
│              │  • Tool dispatch (parallel)    │                    │
│              │  • Error handling (retry/CB)   │                    │
│              │  • Structured logging          │                    │
│              │  • Cost tracking               │                    │
│              └────────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## The Complete Harness Class

```python
# ═══════════════════════════════════════════════════════════════════
# harness.py — THE CAPSTONE. Complete production agent harness.
# ═══════════════════════════════════════════════════════════════════
#
# This file combines EVERY concept from the tutorial into a single,
# coherent class. ~500 lines that you can copy, extend, and deploy.
#
# Features:
#   ✅ Multi-provider (Anthropic, OpenAI, Gemini)
#   ✅ Tool calling with parallel dispatch
#   ✅ Streaming with tool-use buffering
#   ✅ Conversation buffer with token management
#   ✅ Long-term memory via ChromaDB
#   ✅ Error handling with retry + circuit breaker
#   ✅ Structured logging
#   ✅ Cost tracking with budget enforcement
#   ✅ Session persistence with SQLite
#
# Dependencies:
#   pip install anthropic openai google-generativeai chromadb tiktoken

import asyncio
import json
import logging
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, AsyncIterator, Callable

# ═══════════════════════════════════════════════════════════════════
# LOGGING SETUP
# ═══════════════════════════════════════════════════════════════════

logger = logging.getLogger("harness")
logger.setLevel(logging.DEBUG)

# Structured JSON logging for production observability
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter(
    '{"timestamp":"%(asctime)s","level":"%(levelname)s","component":"%(name)s","message":%(message)s}',
    datefmt="%Y-%m-%dT%H:%M:%S",
))
logger.handlers = [handler]


# ═══════════════════════════════════════════════════════════════════
# DATA TYPES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class ToolCall:
    """Normalized tool call across all providers."""
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class LLMResponse:
    """Normalized LLM response."""
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "stop"
    usage: dict[str, int] = field(default_factory=dict)
    model: str = ""
    cost: float = 0.0                                      # Estimated USD cost


@dataclass
class Message:
    """Normalized conversation message."""
    role: str                                               # "system" | "user" | "assistant" | "tool"
    content: str | list[dict]
    tool_call_id: str | None = None
    tool_name: str | None = None


@dataclass
class ToolDefinition:
    """Unified tool definition — translate per-provider."""
    name: str
    description: str
    parameters: dict[str, Any]                              # JSON Schema


@dataclass
class HarnessConfig:
    """All configuration for the harness."""
    provider: str = "anthropic"                             # "anthropic" | "openai" | "gemini"
    model: str = "claude-sonnet-4-20250514"
    api_key: str | None = None
    max_turns: int = 20                                     # Safety: max agentic loop iterations
    max_tokens_per_turn: int = 4096
    temperature: float = 0.7
    system_prompt: str = "You are a helpful AI assistant."
    budget_usd: float = 10.0                                # Max $ to spend per session
    db_path: str = "harness_sessions.db"                    # SQLite persistence
    chroma_path: str = "harness_memory"                     # ChromaDB vector store
    enable_memory: bool = True                              # Long-term memory on/off
    enable_streaming: bool = True                           # Stream responses to user
    retry_attempts: int = 3                                 # Retry on transient errors
    circuit_breaker_threshold: int = 5                      # Failures before circuit opens


# ═══════════════════════════════════════════════════════════════════
# PROVIDER ABSTRACTION (Chapter 17)
# ═══════════════════════════════════════════════════════════════════

class LLMProvider(ABC):
    """Abstract provider interface."""

    @abstractmethod
    async def chat(
        self, messages: list[Message], tools: list[ToolDefinition] | None,
        model: str, max_tokens: int, temperature: float, system: str | None,
    ) -> LLMResponse: ...

    @abstractmethod
    async def stream(
        self, messages: list[Message], tools: list[ToolDefinition] | None,
        model: str, max_tokens: int, temperature: float, system: str | None,
    ) -> AsyncIterator[str | ToolCall]: ...

    @abstractmethod
    def count_tokens(self, text: str) -> int: ...


class AnthropicProvider(LLMProvider):
    """Anthropic Messages API adapter."""
    # (Full implementation from Chapter 17 — condensed here for the capstone)

    def __init__(self, api_key: str | None = None):
        import anthropic
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self._cost_per_1k_input = 0.003                       # $3/MTok for Sonnet
        self._cost_per_1k_output = 0.015                      # $15/MTok for Sonnet

    def _to_anthropic_messages(self, messages: list[Message]) -> list[dict]:
        return [
            {"role": m.role, "content": m.content if isinstance(m.content, str) else m.content}
            for m in messages if m.role != "system"
        ]

    def _to_anthropic_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        if not tools:
            return None
        return [{"name": t.name, "description": t.description, "input_schema": t.parameters} for t in tools]

    def _parse_response(self, response, model: str) -> LLMResponse:
        text = "".join(b.text for b in response.content if b.type == "text")
        tool_calls = [
            ToolCall(id=b.id, name=b.name, arguments=b.input)
            for b in response.content if b.type == "tool_use"
        ]
        input_tokens = response.usage.input_tokens if response.usage else 0
        output_tokens = response.usage.output_tokens if response.usage else 0
        cost = (input_tokens / 1000) * self._cost_per_1k_input + (output_tokens / 1000) * self._cost_per_1k_output
        return LLMResponse(
            content=text, tool_calls=tool_calls,
            stop_reason=response.stop_reason or "stop",
            usage={"input": input_tokens, "output": output_tokens},
            model=model, cost=cost,
        )

    async def chat(self, messages, tools, model, max_tokens, temperature, system):
        import anthropic
        response = await self.client.messages.create(
            model=model, max_tokens=max_tokens, temperature=temperature,
            system=system or anthropic.NOT_GIVEN,
            messages=self._to_anthropic_messages(messages),
            tools=self._to_anthropic_tools(tools) or anthropic.NOT_GIVEN,
        )
        return self._parse_response(response, model)

    async def stream(self, messages, tools, model, max_tokens, temperature, system):
        import anthropic
        async with self.client.messages.stream(
            model=model, max_tokens=max_tokens, temperature=temperature,
            system=system or anthropic.NOT_GIVEN,
            messages=self._to_anthropic_messages(messages),
            tools=self._to_anthropic_tools(tools) or anthropic.NOT_GIVEN,
        ) as stream:
            async for event in stream:
                if event.type == "text":
                    yield event.text
            final = await stream.get_final_message()
            for block in final.content:
                if block.type == "tool_use":
                    yield ToolCall(id=block.id, name=block.name, arguments=block.input)

    def count_tokens(self, text: str) -> int:
        return self.client.count_tokens(text)                         # Anthropic endpoint


class OpenAIProvider(LLMProvider):
    """OpenAI Chat Completions adapter."""
    # (Condensed from Chapter 17)

    def __init__(self, api_key: str | None = None):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self._cost_per_1k_input = 0.0025                          # GPT-4o pricing
        self._cost_per_1k_output = 0.01

    def _to_openai_messages(self, messages: list[Message]) -> list[dict]:
        result = []
        for m in messages:
            entry = {"role": m.role, "content": m.content}
            if m.role == "tool":
                entry["tool_call_id"] = m.tool_call_id
                if isinstance(entry["content"], list):
                    entry["content"] = json.dumps(entry["content"])
            result.append(entry)
        return result

    def _to_openai_tools(self, tools: list[ToolDefinition] | None) -> list[dict] | None:
        if not tools:
            return None
        return [{"type": "function", "function": {"name": t.name, "description": t.description, "parameters": t.parameters}} for t in tools]

    def _parse_response(self, response, model: str) -> LLMResponse:
        choice = response.choices[0]
        tool_calls = []
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
        input_tokens = response.usage.prompt_tokens if response.usage else 0
        output_tokens = response.usage.completion_tokens if response.usage else 0
        cost = (input_tokens / 1000) * self._cost_per_1k_input + (output_tokens / 1000) * self._cost_per_1k_output
        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=tool_calls,
            stop_reason=choice.finish_reason or "stop",
            usage={"input": input_tokens, "output": output_tokens},
            model=model, cost=cost,
        )

    async def chat(self, messages, tools, model, max_tokens, temperature, system):
        all_msgs = self._to_openai_messages(messages)
        if system and not any(m["role"] == "system" for m in all_msgs):
            all_msgs.insert(0, {"role": "system", "content": system})
        response = await self.client.chat.completions.create(
            model=model, messages=all_msgs, max_completion_tokens=max_tokens,
            temperature=temperature, tools=self._to_openai_tools(tools) or openai.NOT_GIVEN,
        )
        return self._parse_response(response, model)

    async def stream(self, messages, tools, model, max_tokens, temperature, system):
        # (Simplified — full streaming with tool buffering in Chapter 17)
        response = await self.chat(messages, tools, model, max_tokens, temperature, system)
        yield response.content
        for tc in response.tool_calls:
            yield tc

    def count_tokens(self, text: str) -> int:
        import tiktoken
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))


# ═══════════════════════════════════════════════════════════════════
# ERROR HANDLING: RETRY + CIRCUIT BREAKER
# ═══════════════════════════════════════════════════════════════════

class CircuitState(Enum):
    CLOSED = "closed"             # Normal operation
    OPEN = "open"                 # Failing — reject immediately
    HALF_OPEN = "half_open"       # Testing if recovered


class CircuitBreaker:
    """Prevents cascading failures by stopping calls after N consecutive errors."""

    def __init__(self, threshold: int = 5, recovery_timeout: float = 30.0):
        self.threshold = threshold
        self.recovery_timeout = recovery_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: float = 0.0
        self.last_success_time: float = 0.0

    def record_success(self):
        """Record a successful call — reset the breaker."""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_success_time = time.time()

    def record_failure(self):
        """Record a failure — potentially trip the breaker."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.threshold:
            self.state = CircuitState.OPEN
            logger.warning(json.dumps({
                "event": "circuit_opened",
                "failures": self.failure_count,
                "threshold": self.threshold,
            }))

    def allow_request(self) -> bool:
        """Should we allow this request through?"""
        if self.state == CircuitState.CLOSED:
            return True
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                logger.info(json.dumps({"event": "circuit_half_open"}))
                return True
            return False
        return True  # HALF_OPEN — allow one probe request


async def with_retry(
    fn: Callable,
    max_attempts: int = 3,
    circuit_breaker: CircuitBreaker | None = None,
    base_delay: float = 1.0,
) -> Any:
    """Execute fn with exponential backoff retry + circuit breaker.

    Retries on: RateLimitError, APITimeoutError, APIConnectionError
    Does NOT retry on: Validation errors, auth errors
    """
    last_exception = None

    for attempt in range(max_attempts):
        if circuit_breaker and not circuit_breaker.allow_request():
            raise Exception(f"Circuit breaker open — {circuit_breaker.failure_count} failures")

        try:
            result = await fn()
            if circuit_breaker:
                circuit_breaker.record_success()
            return result
        except Exception as e:
            last_exception = e
            error_type = type(e).__name__

            # Only retry on transient errors
            transient = any(kw in error_type.lower() for kw in [
                "rate", "timeout", "connection", "server", "overloaded", "capacity"
            ])

            if not transient or attempt == max_attempts - 1:
                if circuit_breaker:
                    circuit_breaker.record_failure()
                raise

            delay = base_delay * (2 ** attempt)                        # Exponential: 1, 2, 4, 8
            logger.warning(json.dumps({
                "event": "retry", "attempt": attempt + 1,
                "error": error_type, "delay": delay,
            }))
            await asyncio.sleep(delay)

    raise last_exception


# ═══════════════════════════════════════════════════════════════════
# LONG-TERM MEMORY (ChromaDB)
# ═══════════════════════════════════════════════════════════════════

class LongTermMemory:
    """Vector-based long-term memory using ChromaDB.

    Stores conversation summaries and retrieves relevant context
    for new conversations. (See Chapter 15 for the full implementation.)
    """

    def __init__(self, persist_path: str):
        import chromadb
        self.client = chromadb.PersistentClient(path=persist_path)
        self.collection = self.client.get_or_create_collection(
            name="harness_memory",
            metadata={"hnsw:space": "cosine"},
        )

    def store(self, session_id: str, text: str, metadata: dict | None = None):
        """Store a memory chunk."""
        mem_id = f"{session_id}-{uuid.uuid4().hex[:8]}"
        self.collection.add(
            documents=[text],
            ids=[mem_id],
            metadatas=[metadata or {}],
        )
        logger.debug(json.dumps({"event": "memory_stored", "id": mem_id, "chars": len(text)}))

    def recall(self, query: str, n_results: int = 5) -> list[str]:
        """Retrieve relevant memories."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results,
        )
        documents = results.get("documents", [[]])[0]
        logger.debug(json.dumps({
            "event": "memory_recall",
            "query": query[:50],
            "results": len(documents),
        }))
        return documents

    def summarize_and_store(self, session_id: str, messages: list[Message]):
        """Create a summary of the conversation and store it."""
        full_text = "\n".join([
            f"{m.role}: {m.content if isinstance(m.content, str) else '[content block]'}"
            for m in messages[-20:]                              # Last 20 messages
        ])
        # In production, use an LLM call to summarize. Here we store the raw text
        # (with a size cap to avoid massive embeddings).
        self.store(session_id, full_text[:2000], {"type": "conversation_summary"})


# ═══════════════════════════════════════════════════════════════════
# SESSION PERSISTENCE (SQLite — Chapter 20)
# ═══════════════════════════════════════════════════════════════════

class SessionStore:
    """SQLite-backed session persistence. (Condensed from Chapter 20.)"""

    def __init__(self, db_path: str):
        import sqlite3
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY, created_at TEXT, updated_at TEXT,
                status TEXT DEFAULT 'active', system_prompt TEXT,
                model TEXT, total_tokens INTEGER DEFAULT 0,
                total_cost REAL DEFAULT 0.0,
                messages_json TEXT DEFAULT '[]',
                tool_defs_json TEXT DEFAULT '[]'
            );
        """)

    def save_session(self, session_id: str, messages: list[Message],
                     system_prompt: str, model: str, total_tokens: int,
                     total_cost: float, tool_defs: list[ToolDefinition],
                     status: str = "active"):
        """Save full session state."""
        now = datetime.now(timezone.utc).isoformat()
        messages_data = [
            {"role": m.role, "content": m.content if isinstance(m.content, str) else json.dumps(m.content),
             "tool_call_id": m.tool_call_id, "tool_name": m.tool_name}
            for m in messages
        ]
        tool_data = [{"name": t.name, "description": t.description, "parameters": t.parameters} for t in tool_defs]

        self.conn.execute("""
            INSERT OR REPLACE INTO sessions
                (id, created_at, updated_at, status, system_prompt, model,
                 total_tokens, total_cost, messages_json, tool_defs_json)
            VALUES (?, COALESCE((SELECT created_at FROM sessions WHERE id=?), ?),
                    ?, ?, ?, ?, ?, ?, ?, ?)
        """, (session_id, session_id, now, now, status, system_prompt, model,
              total_tokens, total_cost, json.dumps(messages_data), json.dumps(tool_data)))
        self.conn.commit()

    def load_session(self, session_id: str) -> dict | None:
        """Load session state. Returns None if not found."""
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            return None

        messages_data = json.loads(row["messages_json"])
        messages = [
            Message(
                role=m["role"],
                content=(json.loads(m["content"]) if m["content"].startswith("[") else m["content"]),
                tool_call_id=m.get("tool_call_id"),
                tool_name=m.get("tool_name"),
            )
            for m in messages_data
        ]
        tool_data = json.loads(row["tool_defs_json"])
        tool_defs = [ToolDefinition(**t) for t in tool_data]

        return {
            "session_id": row["id"],
            "messages": messages,
            "tool_definitions": tool_defs,
            "system_prompt": row["system_prompt"],
            "model": row["model"],
            "total_tokens": row["total_tokens"],
            "total_cost": row["total_cost"],
            "status": row["status"],
        }


# ═══════════════════════════════════════════════════════════════════
# TOKEN MANAGEMENT (Conversation Buffer)
# ═══════════════════════════════════════════════════════════════════

class TokenBuffer:
    """Manages a sliding window of messages to stay within token limits.

    Keeps: system message + last N messages that fit within max_tokens.
    Drops: oldest non-system messages first.
    """

    def __init__(self, provider: LLMProvider, max_tokens: int = 100_000):
        self.provider = provider
        self.max_tokens = max_tokens

    def trim(self, messages: list[Message]) -> list[Message]:
        """Trim messages to fit within max_tokens, preserving system messages."""
        system_msgs = [m for m in messages if m.role == "system"]
        other_msgs = [m for m in messages if m.role != "system"]

        # Count tokens in system messages (always keep these)
        system_tokens = sum(
            self.provider.count_tokens(m.content if isinstance(m.content, str) else json.dumps(m.content))
            for m in system_msgs
        )

        available = self.max_tokens - system_tokens - 1000           # 1000 token buffer
        if available <= 0:
            logger.warning(json.dumps({
                "event": "token_buffer_full",
                "system_tokens": system_tokens,
                "max": self.max_tokens,
            }))
            return system_msgs + [other_msgs[-1]] if other_msgs else system_msgs

        # Keep messages from newest to oldest until we hit the token limit
        kept = []
        tokens_used = 0
        for msg in reversed(other_msgs):
            msg_text = msg.content if isinstance(msg.content, str) else json.dumps(msg.content)
            msg_tokens = self.provider.count_tokens(msg_text)
            if tokens_used + msg_tokens > available:
                break
            kept.insert(0, msg)                                     # Prepend to maintain order
            tokens_used += msg_tokens

        logger.debug(json.dumps({
            "event": "token_trim",
            "before": len(other_msgs),
            "after": len(kept),
            "tokens": tokens_used,
        }))
        return system_msgs + kept


# ═══════════════════════════════════════════════════════════════════
# THE PRODUCTION HARNESS — Where Everything Comes Together
# ═══════════════════════════════════════════════════════════════════

class Harness:
    """THE CAPSTONE. A complete, production-ready agent harness.

    Combines:
    - Multi-provider support (Ch 17)
    - Tool calling with parallel dispatch
    - Streaming with tool-use buffering
    - Token-aware conversation buffer
    - Long-term memory with ChromaDB (Ch 15)
    - Error handling with retry + circuit breaker
    - Structured logging
    - Cost tracking with budget enforcement
    - Session persistence with SQLite (Ch 20)

    Usage:
        harness = Harness(HarnessConfig(
            provider="anthropic",
            model="claude-sonnet-4-20250514",
            api_key="sk-ant-...",
        ))
        harness.register_tool(search_tool_def, search_handler)
        result = await harness.run("Search for latest Python release")
    """

    def __init__(self, config: HarnessConfig):
        self.config = config

        # ── Provider ──
        self.provider = self._create_provider()

        # ── Circuit breaker ──
        self.circuit_breaker = CircuitBreaker(
            threshold=config.circuit_breaker_threshold
        )

        # ── Session store ──
        self.session_store = SessionStore(config.db_path)

        # ── Long-term memory ──
        self.memory = LongTermMemory(config.chroma_path) if config.enable_memory else None

        # ── Token buffer ──
        self.token_buffer = TokenBuffer(self.provider)

        # ── Runtime state ──
        self.tools: dict[str, tuple[ToolDefinition, Callable]] = {}  # name → (def, handler)
        self.session_id: str = str(uuid.uuid4())
        self.messages: list[Message] = []
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.turn_count: int = 0

        logger.info(json.dumps({
            "event": "harness_initialized",
            "provider": config.provider,
            "model": config.model,
            "session_id": self.session_id,
        }))

    def _create_provider(self) -> LLMProvider:
        """Factory: create the right provider based on config."""
        if self.config.provider == "anthropic":
            return AnthropicProvider(api_key=self.config.api_key)
        elif self.config.provider == "openai":
            return OpenAIProvider(api_key=self.config.api_key)
        elif self.config.provider == "gemini":
            # Return GeminiProvider (Chapter 17) — omitted for brevity
            raise NotImplementedError("Gemini provider — see Chapter 17 for full implementation")
        else:
            raise ValueError(f"Unknown provider: {self.config.provider}")

    # ═══════════════════════════════════════════════════════════════
    # TOOL REGISTRATION
    # ═══════════════════════════════════════════════════════════════

    def register_tool(self, tool_def: ToolDefinition, handler: Callable):
        """Register a tool that the agent can use.

        Args:
            tool_def: ToolDefinition with name, description, parameters
            handler: async or sync function that executes the tool
        """
        self.tools[tool_def.name] = (tool_def, handler)
        logger.info(json.dumps({"event": "tool_registered", "tool": tool_def.name}))

    def _get_tool_defs(self) -> list[ToolDefinition]:
        """Get all registered tool definitions for the current turn."""
        return [td for td, _ in self.tools.values()]

    # ═══════════════════════════════════════════════════════════════
    # MEMORY INJECTION
    # ═══════════════════════════════════════════════════════════════

    def _inject_memories(self, user_message: str) -> str | None:
        """Search long-term memory and inject relevant context.

        Returns a memory context string to prepend to the system prompt,
        or None if no relevant memories found.
        """
        if not self.memory:
            return None

        memories = self.memory.recall(user_message, n_results=3)
        if not memories:
            return None

        context = "[RELEVANT MEMORY]\n" + "\n---\n".join(memories) + "\n[/RELEVANT MEMORY]"
        logger.debug(json.dumps({"event": "memory_injected", "chunks": len(memories)}))
        return context

    # ═══════════════════════════════════════════════════════════════
    # TOOL EXECUTION (Parallel)
    # ═══════════════════════════════════════════════════════════════

    async def _execute_tools(self, tool_calls: list[ToolCall]) -> list[dict]:
        """Execute multiple tool calls in parallel.

        Returns list of {"tool_call": ToolCall, "result": str}
        """
        async def execute_one(tc: ToolCall) -> dict:
            tool_info = self.tools.get(tc.name)
            if not tool_info:
                return {"tool_call": tc, "result": f"Tool '{tc.name}' not found"}

            _, handler = tool_info
            try:
                if asyncio.iscoroutinefunction(handler):
                    result = await handler(**tc.arguments)
                else:
                    result = handler(**tc.arguments)
                return {"tool_call": tc, "result": str(result)}
            except Exception as e:
                logger.error(json.dumps({
                    "event": "tool_error",
                    "tool": tc.name,
                    "error": str(e),
                }))
                return {"tool_call": tc, "result": f"Error executing {tc.name}: {e}"}

        tasks = [execute_one(tc) for tc in tool_calls]
        results = await asyncio.gather(*tasks)
        return list(results)

    # ═══════════════════════════════════════════════════════════════
    # THE AGENTIC LOOP
    # ═══════════════════════════════════════════════════════════════

    async def run(self, user_message: str) -> str:
        """Run the full agentic loop.

        This is the heart of the harness. It:
        1. Injects long-term memory context
        2. Builds the system prompt
        3. Calls the model (with streaming or batch)
        4. If tool calls: executes tools in parallel, feeds results back
        5. Repeats until the model stops calling tools or max turns reached
        6. Persists the session and stores conversation in memory
        """
        start_time = time.time()

        # ── Step 1: Memory injection ──
        memory_context = self._inject_memories(user_message)
        effective_system = self.config.system_prompt
        if memory_context:
            effective_system = memory_context + "\n\n" + effective_system

        # ── Step 2: Initialize conversation ──
        if not self.messages:
            self.messages = [Message(role="system", content=effective_system)]
        self.messages.append(Message(role="user", content=user_message))

        tool_defs = self._get_tool_defs()

        logger.info(json.dumps({
            "event": "run_started",
            "session_id": self.session_id,
            "message": user_message[:100],
            "tools_available": len(tool_defs),
        }))

        # ── Step 3: Agentic loop ──
        for turn in range(1, self.config.max_turns + 1):
            self.turn_count = turn

            # Trim context to fit token window
            trimmed = self.token_buffer.trim(self.messages)

            # Call the model (with circuit breaker + retry)
            try:
                response = await with_retry(
                    lambda: self.provider.chat(
                        messages=trimmed,
                        tools=tool_defs if tool_defs else None,
                        model=self.config.model,
                        max_tokens=self.config.max_tokens_per_turn,
                        temperature=self.config.temperature,
                        system=effective_system,
                    ),
                    max_attempts=self.config.retry_attempts,
                    circuit_breaker=self.circuit_breaker,
                )
            except Exception as e:
                logger.error(json.dumps({"event": "model_call_failed", "error": str(e)}))
                return f"Error: Model call failed after retries — {e}"

            # Track usage and cost
            self.total_tokens += response.usage.get("input", 0) + response.usage.get("output", 0)
            self.total_cost += response.cost

            logger.info(json.dumps({
                "event": "turn_completed",
                "turn": turn,
                "tokens": response.usage,
                "cost": round(response.cost, 6),
                "total_cost": round(self.total_cost, 4),
                "tool_calls": len(response.tool_calls),
            }))

            # ── Budget check ──
            if self.total_cost >= self.config.budget_usd:
                logger.warning(json.dumps({
                    "event": "budget_exceeded",
                    "cost": round(self.total_cost, 4),
                    "budget": self.config.budget_usd,
                }))
                self.messages.append(Message(role="assistant", content=(
                    f"I've reached the budget limit (${self.total_cost:.2f} of ${self.config.budget_usd:.2f}). "
                    f"Here's what I've found so far:\n\n{response.content}"
                )))
                self._persist("budget_exceeded")
                return response.content

            # ── No tool calls? We're done! ──
            if not response.tool_calls:
                self.messages.append(Message(role="assistant", content=response.content))
                self._persist("completed")
                elapsed = time.time() - start_time
                logger.info(json.dumps({
                    "event": "run_completed",
                    "turns": turn,
                    "total_tokens": self.total_tokens,
                    "total_cost": round(self.total_cost, 4),
                    "elapsed": round(elapsed, 2),
                }))
                return response.content

            # ── Execute tools in PARALLEL ──
            tool_results = await self._execute_tools(response.tool_calls)

            # Build assistant message with tool_use content blocks
            tool_use_blocks = []
            for tc in response.tool_calls:
                tool_use_blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })

            # If the model output text alongside tool calls, include it too
            for tc in response.tool_calls:
                self.messages.append(Message(
                    role="assistant",
                    content=response.content or tool_use_blocks,
                ))
                break  # One assistant message for all tool calls

            # Append tool results
            for tr in tool_results:
                tc = tr["tool_call"]
                self.messages.append(Message(
                    role="tool",
                    content=tr["result"],
                    tool_call_id=tc.id,
                    tool_name=tc.name,
                ))

            # ── Persist after each turn (crash recovery) ──
            self._persist("active")

        # Max turns reached
        logger.warning(json.dumps({"event": "max_turns_reached", "turns": self.config.max_turns}))
        self._persist("max_turns")
        return "I've reached the maximum number of steps. Here's what I have so far."

    # ═══════════════════════════════════════════════════════════════
    # STREAMING VERSION
    # ═══════════════════════════════════════════════════════════════

    async def run_streaming(self, user_message: str) -> AsyncIterator[str]:
        """Run the agentic loop, yielding text tokens as they arrive.

        This is the streaming version of run(). It yields:
        - Text tokens as they arrive from the model
        - Tool call notifications as "[🔧 Using tool: {name}]"
        - Final response text

        Only streams the FINAL model response (not intermediate tool-calling turns).
        """
        memory_context = self._inject_memories(user_message)
        effective_system = self.config.system_prompt
        if memory_context:
            effective_system = memory_context + "\n\n" + effective_system

        if not self.messages:
            self.messages = [Message(role="system", content=effective_system)]
        self.messages.append(Message(role="user", content=user_message))

        tool_defs = self._get_tool_defs()

        for turn in range(1, self.config.max_turns + 1):
            self.turn_count = turn
            trimmed = self.token_buffer.trim(self.messages)

            response = await with_retry(
                lambda: self.provider.chat(
                    messages=trimmed,
                    tools=tool_defs if tool_defs else None,
                    model=self.config.model,
                    max_tokens=self.config.max_tokens_per_turn,
                    temperature=self.config.temperature,
                    system=effective_system,
                ),
                max_attempts=self.config.retry_attempts,
                circuit_breaker=self.circuit_breaker,
            )

            self.total_tokens += response.usage.get("input", 0) + response.usage.get("output", 0)
            self.total_cost += response.cost

            if not response.tool_calls:
                # Stream the final response
                async for token in self.provider.stream(
                    messages=trimmed,
                    tools=tool_defs if tool_defs else None,
                    model=self.config.model,
                    max_tokens=self.config.max_tokens_per_turn,
                    temperature=self.config.temperature,
                    system=effective_system,
                ):
                    if isinstance(token, str):
                        yield token
                    elif isinstance(token, ToolCall):
                        yield f"\n[🔧 Tool: {token.name}]"
                return

            # Execute tools (non-streaming for intermediate turns)
            for tc in response.tool_calls:
                yield f"\n[🔧 Using tool: {tc.name}]"

            tool_results = await self._execute_tools(response.tool_calls)
            for tr in tool_results:
                self.messages.append(Message(
                    role="tool",
                    content=tr["result"],
                    tool_call_id=tr["tool_call"].id,
                    tool_name=tr["tool_call"].name,
                ))

            self._persist("active")

    # ═══════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════

    def _persist(self, status: str):
        """Save current state to SQLite."""
        self.session_store.save_session(
            session_id=self.session_id,
            messages=self.messages,
            system_prompt=self.config.system_prompt,
            model=self.config.model,
            total_tokens=self.total_tokens,
            total_cost=self.total_cost,
            tool_defs=self._get_tool_defs(),
            status=status,
        )

        # Also store in long-term memory
        if self.memory and status in ("completed", "budget_exceeded", "max_turns"):
            self.memory.summarize_and_store(self.session_id, self.messages)

    def load(self, session_id: str) -> bool:
        """Load a previous session by ID. Returns True if found."""
        data = self.session_store.load_session(session_id)
        if not data:
            return False

        self.session_id = data["session_id"]
        self.messages = data["messages"]
        self.total_tokens = data["total_tokens"]
        self.total_cost = data["total_cost"]

        logger.info(json.dumps({
            "event": "session_loaded",
            "session_id": session_id,
            "messages": len(self.messages),
            "total_cost": round(self.total_cost, 4),
        }))
        return True

    # ═══════════════════════════════════════════════════════════════
    # STATS
    # ═══════════════════════════════════════════════════════════════

    def stats(self) -> dict:
        """Return current session statistics."""
        return {
            "session_id": self.session_id,
            "provider": self.config.provider,
            "model": self.config.model,
            "turns": self.turn_count,
            "messages": len(self.messages),
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 6),
            "budget": self.config.budget_usd,
            "tools_registered": len(self.tools),
        }
```

---

## Using the Production Harness

```python
# ═══════════════════════════════════════════════════════════════════
# example_usage.py — End-to-end demonstration
# ═══════════════════════════════════════════════════════════════════

async def main():
    """Run a complex multi-step task with the production harness."""

    # ═══ Configure ═══
    config = HarnessConfig(
        provider="anthropic",
        model="claude-sonnet-4-20250514",
        api_key="sk-ant-...",                                      # Or set ANTHROPIC_API_KEY env var
        system_prompt=(
            "You are an expert software developer. You have access to "
            "filesystem tools, web search, and code execution. Break down "
            "complex tasks, use tools methodically, and explain your reasoning."
        ),
        max_turns=15,
        budget_usd=1.00,                                           # Keep it cheap for demos
        enable_memory=True,
    )

    harness = Harness(config)

    # ═══ Register tools ═══
    # Tool 1: Read a file
    harness.register_tool(ToolDefinition(
        name="read_file",
        description="Read the contents of a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"],
        },
    ), handler=lambda path: Path(path).read_text()[:5000])         # Cap at 5KB

    # Tool 2: Write a file
    harness.register_tool(ToolDefinition(
        name="write_file",
        description="Write content to a file",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "content": {"type": "string", "description": "Content to write"},
            },
            "required": ["path", "content"],
        },
    ), handler=lambda path, content: (
        Path(path).parent.mkdir(parents=True, exist_ok=True),
        Path(path).write_text(content),
        f"Wrote {len(content)} bytes to {path}"
    )[2])

    # Tool 3: Execute Python code
    import subprocess
    harness.register_tool(ToolDefinition(
        name="run_python",
        description="Execute a Python script and return the output",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python code to execute"},
            },
            "required": ["code"],
        },
    ), handler=lambda code: subprocess.run(
        ["python", "-c", code], capture_output=True, text=True, timeout=10
    ).stdout[:2000])

    # ═══ Run a complex task ═══
    result = await harness.run(
        "Create a Python module called 'email_validator.py' that implements "
        "RFC 5322 email validation. Include comprehensive docstrings, type hints, "
        "and handle edge cases. Then write a test file that exercises it with "
        "valid and invalid emails. Finally, run the tests."
    )

    print("=" * 60)
    print("FINAL RESULT:")
    print("=" * 60)
    print(result)

    # ═══ Print stats ═══
    print("\n" + "=" * 60)
    print("SESSION STATS:")
    print("=" * 60)
    for key, value in harness.stats().items():
        print(f"  {key}: {value}")

    # ═══ Save and reload ═══
    session_id = harness.session_id
    print(f"\nSession saved as: {session_id}")

    # Later, in a different process...
    harness2 = Harness(config)
    harness2.register_tool(ToolDefinition(
        name="read_file", description="Read a file",
        parameters={"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    ), handler=lambda path: Path(path).read_text()[:5000])
    # ... re-register other tools ...

    if harness2.load(session_id):
        result2 = await harness2.run("Now optimize the validator for performance.")
        print(f"\nContinuation result: {result2[:200]}...")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Architecture Decision Record

| Decision | Choice | Rationale |
|---|---|---|
| Provider abstraction | ABC + per-provider adapter | Swap providers without changing harness logic |
| Error handling | Retry + circuit breaker | Transient errors recover; persistent failures fast-fail |
| Token management | Sliding window with token counting | Stay within context limits automatically |
| Tool execution | `asyncio.gather` parallel | Multiple independent tools run concurrently |
| Persistence | SQLite WAL mode | ACID, concurrent reads, zero setup |
| Long-term memory | ChromaDB | Open-source, persistent, cosine similarity |
| Logging | Structured JSON to stdout | Parseable by log aggregators, human-readable |
| State management | In-memory + periodic SQLite saves | Fast access + crash recovery |

---

## What This Harness Does NOT Do (Yet)

This is a production-grade foundation. Here's what you'd add for full production readiness:

| Missing Feature | Why It Matters | How to Add |
|---|---|---|
| Authentication middleware | Multi-tenant SaaS | Wrap `run()` in auth check |
| Rate limiting | Prevent abuse | Token bucket / sliding window |
| Async job queue | Long-running tasks | Celery / Redis Queue |
| Observability (traces) | Debug slow requests | OpenTelemetry spans |
| A/B model testing | Compare model performance | Route to different models, track metrics |
| WebSocket streaming | Real-time UI updates | Yield tokens over WebSocket |
| Sandboxing | Security isolation | Docker / Firecracker per session |

---

## Key Takeaways

1. **The harness is the product** — model APIs change; your harness shouldn't
2. **Parallel tool execution is underrated** — it's the biggest latency win
3. **Persistence is not optional** — save every turn, survive any crash
4. **Log everything in structured format** — you'll need it when debugging production issues
5. **Keep it under 500 lines** — if your harness is 2000+ lines, you're doing something wrong
6. **This chapter IS your reference** — bookmark it, copy the code, make it yours

---

> **Previous:** [Chapter 22: Architecture Deep-Dive — Omnigent Adapters](22_architecture_omnigent_adapters.md)  
> **Next:** [Appendix A: Minimal Harness](../appendix/A_minimal_harness.py)

---

*End of the main tutorial. Appendices follow with quick-reference material.*
