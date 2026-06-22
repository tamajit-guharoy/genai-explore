# Chapter 17: Multi-Provider Abstraction Layer

> **Previous:** [Chapter 16: Testing Harnesses](../part4_production/16_testing_harnesses.md)  
> **Next:** [Chapter 18: Sub-Agent Orchestration](18_sub_agent_orchestration.md)

---

## What You'll Learn

- Why vendor lock-in is the silent killer of AI agent projects
- The Adapter pattern applied to LLM providers
- How to build a unified interface over Anthropic, OpenAI, Gemini, and OpenRouter
- Tool schema translation: define once, convert everywhere
- Complete working code for all four providers

---

## The Problem: Every Provider Speaks a Different Language

Picture this: You've built a brilliant agent harness on top of Anthropic's Claude. Your users love it. Then your CTO says, "We need to support OpenAI too — some enterprise customers require it." You open the OpenAI docs and realize... *everything is different*.

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR HARNESS CODE                            │
│                                                                 │
│  if provider == "anthropic":                                    │
│      response = anthropic.messages.create(                      │
│          model="claude-sonnet-4-20250514",                      │
│          max_tokens=4096,        ← parameter name               │
│          system=system_prompt,   ← top-level field               │
│          messages=messages,      ← list of {"role","content"}    │
│          tools=tool_defs,        ← different format!             │
│      )                                                          │
│  elif provider == "openai":                                     │
│      response = openai.chat.completions.create(                  │
│          model="gpt-4o",                                        │
│          max_completion_tokens=4096, ← different name!           │
│          messages=[{"role":"system","content":...}, ...], ← diff! │
│          tools=tool_defs,        ← different format again!       │
│      )                                                          │
│  elif provider == "gemini":                                     │
│      ...yet another completely different API...                  │
└─────────────────────────────────────────────────────────────────┘
```

This is **vendor spaghetti**. Every new provider adds exponential complexity. The solution? The **Adapter Pattern**.

---

## The Solution: One Interface, Many Backends

> **Analogy:** A universal remote control. You press "Play" — the remote translates that into the specific infrared signal for your TV, Blu-Ray player, or soundbar. Your harness is the remote; each provider is a different device.

```
                          ┌───────────────────┐
                          │   LLMProvider     │  ← Abstract Base Class
                          │   (ABC)           │
                          │                   │
                          │ + chat()          │
                          │ + stream()        │
                          │ + count_tokens()  │
                          └───────┬───────────┘
                                  │
            ┌─────────────────────┼─────────────────────┐
            │                     │                     │
   ┌────────▼────────┐  ┌────────▼────────┐  ┌────────▼────────┐
   │ AnthropicProvider│  │ OpenAIProvider  │  │ GeminiProvider  │
   │                 │  │                 │  │                 │
   │ translates to   │  │ translates to   │  │ translates to   │
   │ Anthropic       │  │ OpenAI Chat     │  │ Gemini          │
   │ Messages API    │  │ Completions API │  │ generateContent │
   └─────────────────┘  └─────────────────┘  └─────────────────┘
```

---

## Step 1: The Abstract Base Class

Every provider adapter must implement these three methods. This is our contract.

```python
# ═══════════════════════════════════════════════════════════════════
# base_provider.py — The Abstract Base Class
# ═══════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Iterator, Literal


@dataclass
class ToolCall:                                         # Unified tool call representation
    """A tool call, normalized across all providers."""
    id: str                                             # Unique call ID (maps to Anthropic's tool_use id)
    name: str                                           # Function/tool name
    arguments: dict[str, Any]                           # Parsed JSON arguments


@dataclass
class LLMResponse:                                      # Unified response across all providers
    """Response from ANY provider, normalized."""
    content: str                                        # Text content (empty if tool call only)
    tool_calls: list[ToolCall] = field(default_factory=list)
    stop_reason: str = "end_turn"                       # "end_turn" | "tool_use" | "max_tokens" | "stop"
    usage: dict[str, int] = field(default_factory=dict) # {"input_tokens": N, "output_tokens": N}
    model: str = ""                                     # Which model generated this
    raw_response: Any = None                            # Original provider response for debugging


@dataclass
class Message:                                          # Unified message format
    """A conversation message, normalized."""
    role: Literal["system", "user", "assistant", "tool"]
    content: str | list[dict[str, Any]]                 # String or multimodal content blocks
    tool_call_id: str | None = None                     # For tool result messages
    name: str | None = None                             # Tool name for tool result messages


@dataclass
class ToolDefinition:                                   # Unified tool definition
    """Define a tool once — translate to provider format on demand."""
    name: str                                           # Function name
    description: str                                    # What it does (REQUIRED for Anthropic)
    parameters: dict[str, Any]                          # JSON Schema for parameters
    # {
    #     "type": "object",
    #     "properties": {
    #         "query": {"type": "string", "description": "Search query"}
    #     },
    #     "required": ["query"]
    # }


class LLMProvider(ABC):                                 # The contract all providers must fulfill
    """Abstract base class for all LLM providers.

    Every provider adapter must implement chat(), stream(), and count_tokens().
    Your harness code ONLY depends on this interface — never on a specific SDK.
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> LLMResponse:
        """Send a chat completion request and return the normalized response."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> AsyncIterator[str | ToolCall]:
        """Stream a chat completion, yielding text chunks and ToolCall objects."""
        ...

    @abstractmethod
    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Count tokens for a given text string using the provider's tokenizer."""
        ...
```

---

## Step 2: Tool Schema Translation

This is the part that burns most people. Each provider formats tool definitions differently.

```python
# ═══════════════════════════════════════════════════════════════════
# tool_translator.py — Convert unified ToolDefinitions to provider format
# ═══════════════════════════════════════════════════════════════════

class ToolSchemaTranslator:
    """Translate our unified ToolDefinition into each provider's format."""

    @staticmethod
    def to_anthropic(tools: list[ToolDefinition]) -> list[dict]:
        """Anthropic format: {"name":..., "description":..., "input_schema":{...}}"""
        return [
            {
                "name": tool.name,
                "description": tool.description,            # REQUIRED — Anthropic rejects without it
                "input_schema": tool.parameters,            # JSON Schema directly
            }
            for tool in tools
        ]

    @staticmethod
    def to_openai(tools: list[ToolDefinition]) -> list[dict]:
        """OpenAI format: {"type":"function","function":{"name":...,"description":...,"parameters":...}}"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,        # Optional but strongly recommended
                    "parameters": tool.parameters,          # JSON Schema
                    "strict": True,                         # GPT-4o+ structured output mode
                },
            }
            for tool in tools
        ]

    @staticmethod
    def to_gemini(tools: list[ToolDefinition]) -> list[dict]:
        """Gemini format: {"functionDeclarations": [{"name":..., "description":..., "parameters":...}]}"""
        # Gemini wraps ALL tools in a single function_declarations block
        declarations = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            }
            for tool in tools
        ]
        return [{"function_declarations": declarations}]

    @staticmethod
    def to_openrouter(tools: list[ToolDefinition]) -> list[dict]:
        """OpenRouter uses OpenAI-compatible format."""
        return ToolSchemaTranslator.to_openai(tools)
```

### Translation Table: Field-by-Field Mapping

| Our Field | Anthropic | OpenAI | Gemini |
|---|---|---|---|
| `name` | `name` (top-level) | `function.name` (nested) | `name` in `functionDeclarations[]` |
| `description` | `description` (**required**) | `function.description` (optional) | `description` in `functionDeclarations[]` |
| `parameters` | `input_schema` | `function.parameters` | `parameters` in `functionDeclarations[]` |
| Container | Array of tool objects | Array of `{type, function}` | One object with `functionDeclarations` array |

---

## Step 3: The Anthropic Provider

```python
# ═══════════════════════════════════════════════════════════════════
# anthropic_provider.py
# ═══════════════════════════════════════════════════════════════════

import anthropic                                                      # pip install anthropic
from anthropic.types import Message as AnthropicMessage
from .base_provider import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition
from .tool_translator import ToolSchemaTranslator


class AnthropicProvider(LLMProvider):
    """Adapter for Anthropic's Messages API."""

    def __init__(self, api_key: str | None = None):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)       # Use async client
        self._default_model = "claude-sonnet-4-20250514"

    # ── Message conversion ────────────────────────────────────
    def _to_anthropic_messages(self, messages: list[Message]) -> list[dict]:
        """Convert our normalized Messages to Anthropic's format.

        Anthropic format (no system in messages array):
            {"role": "user", "content": "..."}
            {"role": "assistant", "content": [...]}          ← content blocks for tool use
            {"role": "user", "content": [{"type": "tool_result", ...}]}
        """
        converted = []
        for msg in messages:
            if msg.role == "system":
                continue  # System messages go in the system= parameter, not the array

            if isinstance(msg.content, str):
                converted.append({"role": msg.role, "content": msg.content})
            else:
                # Already a content block list (images, tool results, etc.)
                converted.append({"role": msg.role, "content": msg.content})

        return converted

    def _extract_system(self, messages: list[Message]) -> str | None:
        """Extract system prompt from messages."""
        for msg in messages:
            if msg.role == "system":
                return msg.content if isinstance(msg.content, str) else str(msg.content)
        return None

    # ── Tool extraction from Anthropic response ───────────────
    def _extract_tool_calls(self, content_blocks: list) -> list[ToolCall]:
        """Pull tool_use blocks out of Anthropic's content array."""
        tool_calls = []
        for block in content_blocks:
            if block.type == "tool_use":
                tool_calls.append(ToolCall(
                    id=block.id,
                    name=block.name,
                    arguments=block.input,                          # Anthropic already parses JSON
                ))
        return tool_calls

    # ── Main methods ──────────────────────────────────────────
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> LLMResponse:
        """Send a chat request to Anthropic."""
        system_prompt = system or self._extract_system(messages)
        anthropic_messages = self._to_anthropic_messages(messages)
        anthropic_tools = ToolSchemaTranslator.to_anthropic(tools) if tools else None

        response: AnthropicMessage = await self.client.messages.create(
            model=model or self._default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or anthropic.NOT_GIVEN,           # Must use NOT_GIVEN, not None
            messages=anthropic_messages,
            tools=anthropic_tools or anthropic.NOT_GIVEN,
        )

        # Normalize response
        text_content = ""
        for block in response.content:
            if block.type == "text":
                text_content += block.text

        return LLMResponse(
            content=text_content,
            tool_calls=self._extract_tool_calls(response.content),
            stop_reason=response.stop_reason or "end_turn",
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            model=response.model,
            raw_response=response,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> AsyncIterator[str | ToolCall]:
        """Stream from Anthropic."""
        system_prompt = system or self._extract_system(messages)
        anthropic_messages = self._to_anthropic_messages(messages)
        anthropic_tools = ToolSchemaTranslator.to_anthropic(tools) if tools else None

        async with self.client.messages.stream(
            model=model or self._default_model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or anthropic.NOT_GIVEN,
            messages=anthropic_messages,
            tools=anthropic_tools or anthropic.NOT_GIVEN,
        ) as stream:
            async for event in stream:
                if event.type == "text":
                    yield event.text                                   # Text delta
                elif event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        pass  # Tool use starting — we collect arguments via deltas
                # Anthropic's SDK stream manager handles tool_use accumulation internally
                # For full streaming tool support, use stream.text_stream or the message event

            # After stream ends, get the final message for tool calls
            final_message = await stream.get_final_message()
            for block in final_message.content:
                if block.type == "tool_use":
                    yield ToolCall(id=block.id, name=block.name, arguments=block.input)

    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Use Anthropic's token counting endpoint."""
        return self.client.count_tokens(text)                           # Returns int directly
```

---

## Step 4: The OpenAI Provider

```python
# ═══════════════════════════════════════════════════════════════════
# openai_provider.py
# ═══════════════════════════════════════════════════════════════════

import json                                                          # For parsing tool call arguments
from openai import AsyncOpenAI                                        # pip install openai
from .base_provider import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition
from .tool_translator import ToolSchemaTranslator


class OpenAIProvider(LLMProvider):
    """Adapter for OpenAI's Chat Completions API."""

    def __init__(self, api_key: str | None = None):
        self.client = AsyncOpenAI(api_key=api_key)                   # Use async client
        self._default_model = "gpt-4o"

    # ── Message conversion ────────────────────────────────────
    def _to_openai_messages(self, messages: list[Message]) -> list[dict]:
        """Convert to OpenAI format — system is part of the messages array."""
        converted = []
        for msg in messages:
            entry: dict[str, Any] = {"role": msg.role, "content": msg.content}

            if msg.role == "tool":                                   # Tool result message
                entry["tool_call_id"] = msg.tool_call_id
                # OpenAI expects tool result content as a string
                if isinstance(entry["content"], list):
                    entry["content"] = json.dumps(entry["content"])

            if msg.name and msg.role == "assistant":                 # Assistant with tool_calls
                pass  # tool_calls are in content blocks

            converted.append(entry)
        return converted

    # ── Handling assistant messages with tool_calls ───────────
    def _build_assistant_message(self, response) -> dict:
        """Build an assistant message dict that includes any tool_calls."""
        msg: dict[str, Any] = {
            "role": "assistant",
            "content": response.choices[0].message.content or "",
        }
        tc = response.choices[0].message.tool_calls
        if tc:
            msg["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,       # Stringified JSON
                    },
                }
                for call in tc
            ]
            msg["content"] = msg["content"] or None                 # OpenAI wants null, not ""
        return msg

    # ── Tool call extraction ─────────────────────────────────
    def _extract_tool_calls(self, response) -> list[ToolCall]:
        """Extract normalized ToolCalls from OpenAI response."""
        tool_calls = []
        choice = response.choices[0]
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_calls.append(ToolCall(
                    id=tc.id,
                    name=tc.function.name,
                    arguments=json.loads(tc.function.arguments),     # Parse JSON string
                ))
        return tool_calls

    # ── Main methods ──────────────────────────────────────────
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> LLMResponse:
        """Send a chat request to OpenAI."""
        all_messages = self._to_openai_messages(messages)

        # If a system string is provided that's not already a message, prepend it
        if system and not any(m["role"] == "system" for m in all_messages):
            all_messages.insert(0, {"role": "system", "content": system})

        openai_tools = ToolSchemaTranslator.to_openai(tools) if tools else None

        response = await self.client.chat.completions.create(
            model=model or self._default_model,
            messages=all_messages,
            max_completion_tokens=max_tokens,                        # NOTE: different param name
            temperature=temperature,
            tools=openai_tools or openai.NOT_GIVEN,
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            tool_calls=self._extract_tool_calls(response),
            stop_reason=choice.finish_reason or "stop",
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            model=response.model,
            raw_response=response,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> AsyncIterator[str | ToolCall]:
        """Stream from OpenAI with tool-call accumulation."""
        all_messages = self._to_openai_messages(messages)
        if system and not any(m["role"] == "system" for m in all_messages):
            all_messages.insert(0, {"role": "system", "content": system})

        openai_tools = ToolSchemaTranslator.to_openai(tools) if tools else None

        stream = await self.client.chat.completions.create(
            model=model or self._default_model,
            messages=all_messages,
            max_completion_tokens=max_tokens,
            temperature=temperature,
            tools=openai_tools or openai.NOT_GIVEN,
            stream=True,
        )

        # OpenAI streams tool calls as deltas — accumulate them
        tool_call_buffer: dict[int, dict] = {}                       # index → {id, name, arguments}
        async for chunk in stream:
            delta = chunk.choices[0].delta

            if delta.content:
                yield delta.content                                   # Text delta

            if delta.tool_calls:
                for tc_delta in delta.tool_calls:
                    idx = tc_delta.index
                    if idx not in tool_call_buffer:
                        tool_call_buffer[idx] = {"id": "", "name": "", "arguments": ""}

                    buf = tool_call_buffer[idx]
                    if tc_delta.id:
                        buf["id"] = tc_delta.id
                    if tc_delta.function:
                        if tc_delta.function.name:
                            buf["name"] += tc_delta.function.name
                        if tc_delta.function.arguments:
                            buf["arguments"] += tc_delta.function.arguments

        # After streaming ends, yield accumulated tool calls
        for tc in tool_call_buffer.values():
            if tc["name"]:
                yield ToolCall(
                    id=tc["id"],
                    name=tc["name"],
                    arguments=json.loads(tc["arguments"]),
                )

    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Estimate tokens using tiktoken."""
        import tiktoken                                                # pip install tiktoken
        enc = tiktoken.encoding_for_model(model or self._default_model)
        return len(enc.encode(text))
```

---

## Step 5: The Gemini Provider

```python
# ═══════════════════════════════════════════════════════════════════
# gemini_provider.py
# ═══════════════════════════════════════════════════════════════════

import google.generativeai as genai                                   # pip install google-generativeai
from google.generativeai.types import content_types
from .base_provider import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition
from .tool_translator import ToolSchemaTranslator


class GeminiProvider(LLMProvider):
    """Adapter for Google's Gemini API (generateContent)."""

    def __init__(self, api_key: str | None = None):
        genai.configure(api_key=api_key)
        self._default_model = "gemini-2.0-flash"

    # ── Message conversion ────────────────────────────────────
    def _to_gemini_contents(self, messages: list[Message], system: str | None) -> list:
        """Gemini uses a flat 'contents' list. System prompt goes via system_instruction.

        Gemini roles: "user" or "model" (not "assistant").
        """
        contents = []
        for msg in messages:
            if msg.role == "system":
                continue  # Handled via system_instruction

            role = "model" if msg.role == "assistant" else "user"     # Map roles

            # Handle text content
            if isinstance(msg.content, str):
                parts = [{"text": msg.content}]
            else:
                parts = msg.content  # Multimodal blocks

            # Handle tool calls baked into assistant messages
            if msg.role == "assistant" and hasattr(msg, "_gemini_tool_calls"):
                # Gemini represents tool calls as functionCall parts
                for tc in msg._gemini_tool_calls:
                    parts.append({
                        "functionCall": {
                            "name": tc.name,
                            "args": tc.arguments,
                        }
                    })

            # Handle tool results
            if msg.role == "tool":
                parts = [{
                    "functionResponse": {
                        "name": msg.name,
                        "response": {"result": msg.content},
                    }
                }]

            contents.append({"role": role, "parts": parts})
        return contents

    # ── Gemini tool config conversion ─────────────────────────
    def _to_gemini_tools(self, tools: list[ToolDefinition] | None):
        """Gemini expects a 'tools' list with function_declarations."""
        if not tools:
            return None
        return ToolSchemaTranslator.to_gemini(tools)

    # ── Response parsing ──────────────────────────────────────
    def _parse_response(self, response, model: str) -> LLMResponse:
        """Parse Gemini's GenerateContentResponse."""
        text_content = ""
        tool_calls: list[ToolCall] = []

        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.text:
                        text_content += part.text
                    if hasattr(part, "function_call") and part.function_call:
                        tool_calls.append(ToolCall(
                            id=f"gemini-{len(tool_calls)}",            # Gemini has no call IDs
                            name=part.function_call.name,
                            arguments=dict(part.function_call.args),
                        ))

            finish_reason = str(candidate.finish_reason.name) if candidate.finish_reason else "STOP"
        else:
            finish_reason = "SAFETY"  # Blocked by safety filters

        # Token counts
        usage = {}
        if hasattr(response, "usage_metadata"):
            usage = {
                "input_tokens": response.usage_metadata.prompt_token_count,
                "output_tokens": response.usage_metadata.candidates_token_count,
            }

        return LLMResponse(
            content=text_content,
            tool_calls=tool_calls,
            stop_reason=finish_reason,
            usage=usage,
            model=model,
            raw_response=response,
        )

    # ── Main methods ──────────────────────────────────────────
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> LLMResponse:
        """Send a chat request to Gemini."""
        selected_model = model or self._default_model
        gemini_model = genai.GenerativeModel(
            model_name=selected_model,
            system_instruction=system,
            tools=self._to_gemini_tools(tools),
        )

        contents = self._to_gemini_contents(messages, system)

        response = await gemini_model.generate_content_async(
            contents,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
        )

        return self._parse_response(response, selected_model)

    async def stream(
        self,
        messages: list[Message],
        tools: list[ToolDefinition] | None = None,
        *,
        model: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> AsyncIterator[str | ToolCall]:
        """Stream from Gemini."""
        selected_model = model or self._default_model
        gemini_model = genai.GenerativeModel(
            model_name=selected_model,
            system_instruction=system,
            tools=self._to_gemini_tools(tools),
        )

        contents = self._to_gemini_contents(messages, system)

        response = await gemini_model.generate_content_async(
            contents,
            generation_config={
                "max_output_tokens": max_tokens,
                "temperature": temperature,
            },
            stream=True,
        )

        async for chunk in response:
            if chunk.candidates and chunk.candidates[0].content:
                for part in chunk.candidates[0].content.parts:
                    if part.text:
                        yield part.text
                    if hasattr(part, "function_call") and part.function_call:
                        yield ToolCall(
                            id=f"gemini-stream-{part.function_call.name}",
                            name=part.function_call.name,
                            arguments=dict(part.function_call.args),
                        )

    def count_tokens(self, text: str, model: str | None = None) -> int:
        """Gemini token counting: use the model's count_tokens method."""
        selected_model = model or self._default_model
        gemini_model = genai.GenerativeModel(selected_model)
        result = gemini_model.count_tokens(text)
        return result.total_tokens
```

---

## Step 6: The OpenRouter Provider (Bonus)

```python
# ═══════════════════════════════════════════════════════════════════
# openrouter_provider.py
# ═══════════════════════════════════════════════════════════════════
# OpenRouter is an API gateway that proxies 200+ models through
# an OpenAI-compatible interface. We extend OpenAIProvider and
# just change the base URL and add OpenRouter-specific headers.

from openai import AsyncOpenAI
from .openai_provider import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter adapter — OpenAI-compatible API with different base URL.

    OpenRouter gives you ONE API key that works with models from
    Anthropic, OpenAI, Google, Meta, Mistral, and many more.
    """

    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key: str | None = None, app_name: str = "my-harness"):
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.OPENROUTER_BASE_URL,                       # Route to OpenRouter
            default_headers={
                "HTTP-Referer": "https://github.com/myorg/myharness", # Optional: for rankings
                "X-Title": app_name,                                  # Optional: for rankings
            },
        )
        # OpenRouter model names: "anthropic/claude-sonnet-4-20250514"
        #                       "openai/gpt-4o"
        #                       "google/gemini-2.0-flash-001"
        self._default_model = "openai/gpt-4o"

    # chat(), stream(), and count_tokens() are inherited from OpenAIProvider
    # because OpenRouter uses the same API format!
```

---

## Step 7: Using the Abstraction in Your Harness

Now the payoff — your harness code doesn't care which provider it's using:

```python
# ═══════════════════════════════════════════════════════════════════
# harness.py — Provider-agnostic agent loop
# ═══════════════════════════════════════════════════════════════════

class AgentHarness:
    """A harness that can swap providers without changing agent logic."""

    def __init__(self, provider: LLMProvider):
        self.provider = provider                                     # ANY LLMProvider subclass
        self.tools: dict[str, callable] = {}                         # Tool registry

    def register_tool(self, tool_def: ToolDefinition, handler: callable):
        """Register a tool with its definition and handler."""
        self.tools[tool_def.name] = handler
        self._tool_defs = getattr(self, "_tool_defs", [])
        self._tool_defs.append(tool_def)

    async def run(self, user_message: str, system_prompt: str = "") -> str:
        """The agentic loop — INDEPENDENT of provider."""
        messages: list[Message] = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_message),
        ]

        for _ in range(10):                                          # Max 10 turns
            response = await self.provider.chat(
                messages=messages,
                tools=getattr(self, "_tool_defs", None),
                system=system_prompt,
            )

            if not response.tool_calls:
                return response.content                              # Done — no tools requested

            # Execute tools
            for tool_call in response.tool_calls:
                handler = self.tools.get(tool_call.name)
                result = await handler(**tool_call.arguments) if handler else "Tool not found"

                # Append assistant message with tool use + tool result
                messages.append(Message(
                    role="assistant",
                    content=f"Called {tool_call.name}({tool_call.arguments})"
                ))
                messages.append(Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                ))

        return "Max turns exceeded"


# ═══════════════════════════════════════════════════════════════════
# Usage: Swap providers with ONE LINE
# ═══════════════════════════════════════════════════════════════════

async def main():
    # Choose your provider:
    provider = AnthropicProvider(api_key="sk-ant-...")                # ← ONE LINE TO SWAP
    # provider = OpenAIProvider(api_key="sk-...")
    # provider = GeminiProvider(api_key="AIza...")
    # provider = OpenRouterProvider(api_key="sk-or-...")

    harness = AgentHarness(provider)

    # Register tools (same definitions work everywhere!)
    harness.register_tool(
        ToolDefinition(
            name="search_web",
            description="Search the web for current information",
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"}
                },
                "required": ["query"],
            },
        ),
        handler=lambda query: f"Results for: {query}",
    )

    result = await harness.run("What's the weather in Tokyo?")
    print(result)
```

---

## Provider Capability Matrix

| Feature | Anthropic | OpenAI | Gemini | OpenRouter |
|---|---|---|---|---|
| `chat()` | ✅ | ✅ | ✅ | ✅ |
| `stream()` | ✅ | ✅ | ✅ | ✅ |
| `count_tokens()` | ✅ API endpoint | ✅ tiktoken | ✅ API method | ✅ (via OpenAI underlying model) |
| Tool calling | ✅ Native | ✅ Native | ✅ Native | ✅ Model-dependent |
| Multimodal (images) | ✅ | ✅ | ✅ | ✅ Model-dependent |
| Caching | ✅ Prompt caching | ❌ (separate API) | ✅ Context caching | ❌ |
| Extended thinking | ✅ (Opus 4) | ❌ | ✅ (Gemini 2.5) | ❌ |
| Max context | 200K | 128K | 1M+ (Gemini 2.0) | Model-dependent |

---

## Key Takeaways

1. **Define your interface first** — `LLMProvider` is the contract; everything else implements it
2. **Normalize at the boundary** — Each adapter translates FROM provider format TO your unified types
3. **Tool schemas are the hard part** — Pay extra attention to the translation table
4. **OpenRouter gives you 200+ models for free** — One API key, OpenAI-compatible format
5. **The harness should never import `anthropic` or `openai` directly** — Only via the adapter

---

> **Previous:** [Chapter 16: Testing Harnesses](../part4_production/16_testing_harnesses.md)  
> **Next:** [Chapter 18: Sub-Agent Orchestration](18_sub_agent_orchestration.md)
