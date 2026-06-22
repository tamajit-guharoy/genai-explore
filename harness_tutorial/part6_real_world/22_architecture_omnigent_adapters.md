# Chapter 22: Architecture Deep-Dive — Omnigent Adapters

> **Previous:** [Chapter 21: Architecture Deep-Dive — Pi](21_architecture_pi.md)  
> **Next:** [Chapter 23: Full Build — Production Harness](23_full_build_production_harness.md)

---

## What You'll Learn

- How Omnigent unifies Claude SDK, Claude Native, Codex, and others under one interface
- The Agent Protocol: the uniform contract every adapter implements
- Claude SDK adapter walkthrough: translating Omnigent tool schemas to Anthropic format
- Native harness adapters: PTY/tmux wrapping for CLI-based agents
- The policy evaluation pipeline: where Omnigent checks policies
- The pattern for wrapping ANY agent CLI/SDK under a common interface

---

## The Problem Omnigent Solves

> **Analogy:** You're a contractor who works with electricians, plumbers, and carpenters. Each speaks a different trade language and uses different tools. Omnigent is the general contractor who speaks all their languages, so you only need to talk to ONE person.

```
                    ┌─────────────────────────┐
                    │      OMNIGENT           │
                    │   (The General Contractor)│
                    │                         │
                    │  ┌───────────────────┐  │
                    │  │  AGENT PROTOCOL   │  │  ← One interface to rule them all
                    │  └───────┬───────────┘  │
                    │          │               │
                    │  ┌───────┼───────────┐  │
                    │  │       │           │  │
                    │  ▼       ▼           ▼  │
                    │ SDK   Native       CLI  │
                    │ Type  PTY          Wrapper
                    └─────────────────────────┘
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
  ┌──────▼──────┐   ┌────────▼────────┐   ┌───────▼──────┐
  │ claude-sdk  │   │  claude-native  │   │  codex-cli   │
  │ (API calls) │   │  (tmux + PTY)   │   │  (pty spawn) │
  └─────────────┘   └─────────────────┘   └──────────────┘
```

Omnigent's core insight: **every AI agent has the same shape** — it takes instructions, responds with text or tool calls, and maintains a conversation. The differences are in HOW you communicate with it (API, CLI, PTY), not WHAT it fundamentally does.

---

## The Agent Protocol

Every harness adapter in Omnigent implements this protocol:

```python
# ═══════════════════════════════════════════════════════════════════
# agent_protocol.py — The universal contract for all adapters
# ═══════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator


@dataclass
class AgentResponse:
    """Normalized response from any agent backend."""
    text: str                                                  # Plain text content
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    # tool_calls: [{"name": "search", "args": {"query": "..."}}]
    finish_reason: str = "stop"                                # "stop", "tool_use", "error"
    usage: dict[str, int] = field(default_factory=dict)        # {"input": N, "output": N}


class AgentAdapter(ABC):
    """The universal protocol all Omnigent adapters implement.

    This is the translation layer between Omnigent's internal representation
    and whatever the underlying agent expects (API calls, CLI commands, PTY input).
    """

    @abstractmethod
    async def initialize(self, config: dict[str, Any]) -> None:
        """Set up the adapter with configuration.

        config includes: model, auth, sandbox, policies, skills, etc.
        Called once before any chat() calls.
        """
        ...

    @abstractmethod
    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AgentResponse:
        """Send a conversation turn and get a response.

        messages: [{"role": "user", "content": "..."}, ...]
        tools: Omnigent-format tool definitions
        """
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str | dict]:
        """Stream a response, yielding text chunks or tool call dicts."""
        ...

    @abstractmethod
    async def execute_tool(self, tool_name: str, args: dict[str, Any]) -> str:
        """Execute a tool and return the result string.

        This is called by the Omnigent engine after the adapter reports
        a tool call. The adapter passes through to the sandbox/executor.
        """
        ...

    @abstractmethod
    async def shutdown(self) -> None:
        """Clean up resources (close PTY, disconnect, etc.)."""
        ...
```

---

## Adapter Category 1: SDK-Based (Claude SDK, OpenAI SDK)

SDK adapters are the simplest — they translate Omnigent's format to the provider's SDK calls:

```
┌──────────────────────────────────────────────────────────────────┐
│                    SDK ADAPTER FLOW                              │
│                                                                  │
│  Omnigent Engine                    Adapter                      │
│  ┌─────────────┐                ┌──────────────┐                │
│  │ chat(        │                │ translate     │                │
│  │   messages,  │──────────────► │ messages to   │──── anthropic SDK
│  │   tools,     │                │ Anthropic fmt │                │
│  │   system     │                │               │                │
│  │ )            │◄────────────── │ translate     │                │
│  └─────────────┘   AgentResponse │ response back │                │
│                                   └──────────────┘                │
└──────────────────────────────────────────────────────────────────┘
```

### Claude SDK Adapter: Under the Hood

```python
# ═══════════════════════════════════════════════════════════════════
# claude_sdk_adapter.py — How claude-sdk adapter translates
# ═══════════════════════════════════════════════════════════════════

import anthropic
from anthropic.types import MessageParam, ToolParam


class ClaudeSDKAdapter(AgentAdapter):
    """Adapter that translates Omnigent protocol ↔ Anthropic SDK calls.

    This is the reference implementation — the cleanest adapter because
    both sides use structured data (no text parsing needed).
    """

    def __init__(self):
        self.client: anthropic.AsyncAnthropic | None = None
        self.model: str = "claude-sonnet-4-20250514"
        self.tool_schemas: list[dict] = []                         # Omnigent format tools

    async def initialize(self, config: dict[str, Any]) -> None:
        """Initialize the Anthropic client from Omnigent config."""
        auth = config.get("auth", {})
        self.model = config.get("model", "claude-sonnet-4-20250514")

        if auth.get("type") == "api_key":
            self.client = anthropic.AsyncAnthropic(api_key=auth["api_key"])
        elif auth.get("type") == "provider":
            # For subscription-based auth, the CLI handles it
            # SDK adapter uses API key mode — fall back to env var
            self.client = anthropic.AsyncAnthropic()
        else:
            raise ValueError(f"Unsupported auth type: {auth.get('type')}")

        # Convert Omnigent tool schemas to Anthropic format
        self.tool_schemas = self._translate_tools(
            config.get("skills", []) + config.get("tools", [])
        )

    # ── Tool Schema Translation ─────────────────────────────────
    def _translate_tools(self, omnigent_tools: list[dict]) -> list[dict]:
        """Convert Omnigent tool format → Anthropic tool format.

        Omnigent format:
            {"name": "search", "description": "...", "parameters": {...}}

        Anthropic format:
            {"name": "search", "description": "...", "input_schema": {...}}
        """
        translated = []
        for tool in omnigent_tools:
            translated.append({
                "name": tool["name"],
                "description": tool.get("description", tool["name"]),
                "input_schema": tool.get("parameters", {
                    "type": "object",
                    "properties": {},
                }),
            })
        return translated

    # ── Message Translation ─────────────────────────────────────
    def _translate_messages(
        self,
        messages: list[dict],
        system: str | None,
    ) -> tuple[str | None, list[MessageParam]]:
        """Separate system message from conversation messages.

        Anthropic API: system is a top-level parameter, NOT in messages array.
        """
        system_content = system
        conversation: list[MessageParam] = []

        for msg in messages:
            role = msg["role"]
            content = msg.get("content", "")

            if role == "system":
                system_content = content                           # Extract system
                continue

            # Handle tool results
            if role == "tool":
                conversation.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": str(content),
                    }],
                })
                continue

            conversation.append({"role": role, "content": str(content)})

        return system_content, conversation

    # ── Response Translation ────────────────────────────────────
    def _translate_response(self, response) -> AgentResponse:
        """Convert Anthropic response → AgentResponse."""
        text_parts = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "name": block.name,
                    "args": block.input,
                    "id": block.id,
                })

        return AgentResponse(
            text="".join(text_parts),
            tool_calls=tool_calls,
            finish_reason=response.stop_reason or "stop",
            usage={
                "input": response.usage.input_tokens,
                "output": response.usage.output_tokens,
            } if response.usage else {},
        )

    # ── Core Methods ─────────────────────────────────────────────
    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AgentResponse:
        system_content, anthropic_messages = self._translate_messages(messages, system)

        # Merge provided tools with configured tools
        all_tools = self.tool_schemas.copy()
        if tools:
            all_tools.extend(self._translate_tools(tools))

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system_content or anthropic.NOT_GIVEN,
            messages=anthropic_messages,
            tools=all_tools or anthropic.NOT_GIVEN,
        )

        return self._translate_response(response)

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str | dict]:
        system_content, anthropic_messages = self._translate_messages(messages, system)
        all_tools = self.tool_schemas.copy()
        if tools:
            all_tools.extend(self._translate_tools(tools))

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            system=system_content or anthropic.NOT_GIVEN,
            messages=anthropic_messages,
            tools=all_tools or anthropic.NOT_GIVEN,
        ) as stream:
            # Accumulate tool use as it streams in
            tool_use_buffer: dict[int, dict] = {}
            async for event in stream:
                if event.type == "text":
                    yield event.text
                elif event.type == "content_block_start":
                    if event.content_block.type == "tool_use":
                        idx = event.index
                        tool_use_buffer[idx] = {
                            "name": event.content_block.name,
                            "args": {},
                            "id": event.content_block.id,
                        }
                elif event.type == "content_block_delta":
                    if event.delta.type == "input_json_delta":
                        idx = event.index
                        if idx in tool_use_buffer:
                            # Accumulate partial JSON
                            tool_use_buffer[idx]["args"] = event.delta.partial_json

            # After stream ends, yield accumulated tool calls
            for tc in tool_use_buffer.values():
                yield {"name": tc["name"], "args": tc["args"], "id": tc["id"]}

    async def execute_tool(self, tool_name: str, args: dict[str, Any]) -> str:
        """Execute a tool. In production, this dispatches to the sandbox."""
        # The actual execution happens in Omnigent's tool executor,
        # which handles sandboxing, policies, etc.
        return f"Tool {tool_name} executed with args: {args}"

    async def shutdown(self) -> None:
        self.client = None
```

---

## Adapter Category 2: Native CLI Adapters (PTY/tmux)

For CLI-based agents (Claude Code, Codex CLI), Omnigent wraps them in a pseudo-terminal:

```
┌──────────────────────────────────────────────────────────────────┐
│                  NATIVE ADAPTER FLOW                             │
│                                                                  │
│  Omnigent Engine           Adapter              tmux/PTY         │
│  ┌─────────────┐       ┌──────────────┐    ┌──────────────┐     │
│  │ chat(        │       │ format as    │    │              │     │
│  │   messages   │──────►│ CLI prompts  │───►│  $ claude    │     │
│  │ )            │       │              │    │              │     │
│  │              │       │ parse output │    │  Claude      │     │
│  │              │◄──────│ from PTY     │◄───│  responds... │     │
│  └─────────────┘       └──────────────┘    └──────────────┘     │
│                                                                  │
│  THIS IS HARD because:                                           │
│  - You're parsing human-readable text, not structured data       │
│  - ANSI escape codes, progress bars, spinners                    │
│  - Tool calls appear as text blocks with special formatting      │
│  - The agent might ask questions back (disambiguation)           │
└──────────────────────────────────────────────────────────────────┘
```

### Native Adapter: The PTY Wrapper Pattern

```python
# ═══════════════════════════════════════════════════════════════════
# native_adapter.py — PTY/tmux-based adapter pattern
# ═══════════════════════════════════════════════════════════════════

import asyncio
import json
import os
import re
import signal


class NativeCLIAdapter(AgentAdapter):
    """Wraps a CLI-based agent (claude, codex) via PTY/tmux.

    This is an ORDER OF MAGNITUDE harder than SDK adapters because
    you're parsing text output instead of structured API responses.

    Key challenges:
    1. Starting/stopping the CLI process
    2. Sending prompts and detecting when the response is complete
    3. Parsing tool calls from text output
    4. Handling interactive prompts (the agent asks for clarification)
    5. Cleaning up tmux sessions on shutdown
    """

    def __init__(self):
        self.process: asyncio.subprocess.Process | None = None
        self.command: list[str] = []
        self.completion_marker = "___OMNIGENT_DONE___"          # Unique marker
        self.tool_call_regex = re.compile(
            r'<tool_call>\s*(\{.*?\})\s*</tool_call>',          # Match JSON in tags
            re.DOTALL,
        )

    async def initialize(self, config: dict[str, Any]) -> None:
        """Start the CLI agent in a PTY or tmux session."""
        harness_type = config.get("executor", {}).get("harness", "claude-native")
        model = config.get("executor", {}).get("model", "claude-sonnet-4-20250514")

        if harness_type == "claude-native":
            # Use tmux for Claude Code (it needs a real terminal)
            self._start_tmux_session("claude", model, config)
        elif harness_type == "codex-native":
            # Use PTY for Codex CLI
            self.command = ["codex", "exec", "--model", model]
            self.process = await self._spawn_process()
        else:
            raise ValueError(f"Unknown native harness: {harness_type}")

    async def _spawn_process(self) -> asyncio.subprocess.Process:
        """Spawn the CLI process with a PTY."""
        import pty
        master_fd, slave_fd = pty.openpty()

        process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            preexec_fn=os.setsid,                                # New process group
        )

        # Close slave fd in parent (child uses it)
        os.close(slave_fd)

        # Make master fd non-blocking
        os.set_blocking(master_fd, False)

        self._pty_fd = master_fd
        return process

    def _start_tmux_session(self, agent: str, model: str, config: dict):
        """Start the agent in a tmux session.

        tmux gives us a persistent terminal we can send commands to
        and capture output from — even across restarts.
        """
        session_name = f"omnigent-{agent}-{os.getpid()}"
        os.system(f"tmux new-session -d -s {session_name}")

        # Configure the agent inside tmux
        instructions = config.get("prompt", "")
        system_prompt_file = config.get("instructions_file", "")

        # Send initial setup commands to tmux
        if system_prompt_file:
            os.system(f"tmux send-keys -t {session_name} 'cat > /tmp/omnigent_instructions.txt << 'EOF'' Enter")
            os.system(f"tmux send-keys -t {session_name} '{instructions}' Enter")
            os.system(f"tmux send-keys -t {session_name} 'EOF' Enter")

        # Start the agent CLI
        start_cmd = f"{agent} --model {model}"
        if agent == "claude":
            start_cmd += " --dangerously-skip-permissions"       # Non-interactive mode
            if system_prompt_file:
                start_cmd += " --system-prompt-file /tmp/omnigent_instructions.txt"
            else:
                # Send system prompt via stdin
                start_cmd += f' --system-prompt "{instructions[:500]}"'  # Truncate for CLI

        os.system(f"tmux send-keys -t {session_name} '{start_cmd}' Enter")

        self.tmux_session = session_name

    async def _send_to_tmux(self, text: str):
        """Send text to the tmux session and wait for the completion marker."""
        session = self.tmux_session

        # Escape special characters for tmux
        escaped = text.replace('"', '\\"').replace('$', '\\$')
        os.system(f'tmux send-keys -t {session} "{escaped}" Enter')

        # Also send the completion marker command
        os.system(f'tmux send-keys -t {session} "echo {self.completion_marker}" Enter')

        # Poll until we see the completion marker in tmux output
        for _ in range(120):                                     # 2 minute timeout with 1s polls
            await asyncio.sleep(1)
            output = os.popen(f"tmux capture-pane -t {session} -p").read()
            if self.completion_marker in output:
                break

        # Capture final output
        output = os.popen(f"tmux capture-pane -t {session} -p -S -200").read()
        return output

    async def chat(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AgentResponse:
        """Send a message to the CLI agent and parse the response.

        For native CLI agents, we format the conversation as text prompts
        rather than structured API calls.
        """
        # ── Format the prompt for CLI input ──
        # Build a text representation of the conversation
        prompt_parts = []
        for msg in messages[-5:]:                                # Last 5 messages only
            role = msg["role"]
            content = msg.get("content", "")
            if role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        if tools:
            tool_descriptions = "\n".join([
                f"- {t['name']}: {t.get('description', '')}"
                for t in tools
            ])
            prompt_parts.append(f"\nAvailable tools:\n{tool_descriptions}")

        prompt_text = "\n\n".join(prompt_parts)

        # ── Send to CLI ──
        if hasattr(self, 'tmux_session'):
            raw_output = await self._send_to_tmux(prompt_text)
        else:
            # PTY-based: write to fd, read response
            os.write(self._pty_fd, (prompt_text + "\n").encode())
            await asyncio.sleep(0.5)
            raw_output = os.read(self._pty_fd, 65536).decode(errors="replace")

        # ── Parse the output ──
        return self._parse_cli_output(raw_output)

    def _parse_cli_output(self, raw: str) -> AgentResponse:
        """Parse CLI text output into AgentResponse.

        This is the hardest part of native adapters. Different CLIs
        format tool calls differently. Here's a generic pattern.
        """
        # Remove the completion marker
        clean = raw.replace(self.completion_marker, "")

        # Extract tool calls from <tool_call> tags (if the agent uses them)
        tool_calls = []
        for match in self.tool_call_regex.finditer(clean):
            try:
                tool_data = json.loads(match.group(1))
                tool_calls.append({
                    "name": tool_data.get("name", "unknown"),
                    "args": tool_data.get("arguments", tool_data.get("args", {})),
                    "id": tool_data.get("id", ""),
                })
            except json.JSONDecodeError:
                pass

        # Remove tool call tags from text
        text = self.tool_call_regex.sub("", clean).strip()

        return AgentResponse(
            text=text,
            tool_calls=tool_calls,
            finish_reason="tool_use" if tool_calls else "stop",
        )

    async def stream(
        self,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        system: str | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str | dict]:
        """Streaming for native adapters is line-by-line from PTY.

        Because we can't control how fast the CLI outputs, we yield
        each line as it appears in the PTY buffer.
        """
        # For simplicity, fall back to non-streaming and yield the whole result
        response = await self.chat(messages, tools=tools, system=system)
        yield response.text
        for tc in response.tool_calls:
            yield tc

    async def execute_tool(self, tool_name: str, args: dict[str, Any]) -> str:
        """Execute a tool and return the result to the CLI agent."""
        # In production, Omnigent routes this through the sandbox executor
        result = f"Tool '{tool_name}' executed successfully with args: {json.dumps(args)}"

        # Feed the result back to the CLI
        feedback = f"<tool_result>{result}</tool_result>"
        if hasattr(self, 'tmux_session'):
            os.system(f'tmux send-keys -t {self.tmux_session} "{feedback}" Enter')
        else:
            os.write(self._pty_fd, (feedback + "\n").encode())

        return result

    async def shutdown(self) -> None:
        """Clean up: kill process or tmux session."""
        if hasattr(self, 'tmux_session'):
            os.system(f"tmux kill-session -t {self.tmux_session}")
            self.tmux_session = None
        elif self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            self.process = None
```

---

## The Policy Evaluation Pipeline

Where Omnigent checks policies is exactly where Chapter 19's `PolicyAwareHarness` does it — but with the adapter abstraction:

```
┌──────────────────────────────────────────────────────────────────┐
│            OMNIGENT POLICY EVALUATION PIPELINE                    │
│                                                                  │
│  1. Model returns response (via adapter.chat())                  │
│                          │                                       │
│                          ▼                                       │
│  2. Response contains tool_call? ─── NO ──► Return text to user │
│                          │                                       │
│                          ▼ YES                                   │
│  3. POLICY CHECK: evaluate(tool_name, args, context)             │
│     ┌──────────────────────────────────────────────────────┐     │
│     │  ALLOW  ──► Continue to step 4                       │     │
│     │  ASK    ──► Present to user → wait for response      │     │
│     │  DENY   ──► Return denial reason to model            │     │
│     └──────────────────────────────────────────────────────┘     │
│                          │                                       │
│                          ▼ (if ALLOW or ASK-approved)             │
│  4. SANDBOX CHECK: can this tool run in current sandbox?         │
│     ┌──────────────────────────────────────────────────────┐     │
│     │  ALLOW  ──► Continue to step 5                       │     │
│     │  DENY   ──► "This tool requires --allow-dangerous"   │     │
│     └──────────────────────────────────────────────────────┘     │
│                          │                                       │
│                          ▼ (if allowed)                           │
│  5. EXECUTE: adapter.execute_tool(name, args)                    │
│                          │                                       │
│                          ▼                                       │
│  6. FEED RESULT back to model via adapter.chat()                 │
└──────────────────────────────────────────────────────────────────┘
```

The key insight: **the adapter doesn't do policy checks** — the Omnigent engine sits between the adapter and tool execution. The adapter only handles communication with the agent; the engine handles governance.

---

## Lessons for Your Own Harness

### Lesson 1: The Adapter Pattern is Universal

```python
# Your harness should have ONE adapter interface.
# Every agent backend (SDK, CLI, API) implements it.
# Your agent loop code NEVER imports anthropic or openai directly.
```

### Lesson 2: SDK Adapters Are 10x Easier Than CLI Adapters

```python
# SDK: structured data in → structured data out
# CLI: text in → parse → hope → text out
#
# Always prefer an SDK adapter when available.
# Only use CLI adapters when the CLI has features the SDK doesn't
# (like Claude Code's interactive permission model).
```

### Lesson 3: Policy Checks Belong in the Engine, Not the Adapter

```python
# WRONG: adapter checks policies internally
# RIGHT: engine checks policies, adapter just translates communication
#
# This separation means swapping adapters doesn't change your security posture.
```

### Lesson 4: PTY/tmux is the Universal Escape Hatch

```python
# When no SDK exists, PTY/tmux wrapping works for ANY CLI tool.
# It's fragile, hard to parse, and slow — but it ALWAYS works.
# This is how Omnigent supports claude-native, codex-native, cursor, etc.
```

---

## Omnigent Adapter Comparison

| Adapter | Setup Complexity | Reliability | Tool Parsing | Latency |
|---|---|---|---|---|
| claude-sdk | Low (API key) | High (structured API) | Easy (JSON) | Low |
| claude-native | High (Node, tmux) | Medium (text parsing) | Hard (regex) | High |
| codex-cli | Medium (PTY) | Medium (text parsing) | Hard (regex) | High |
| openai-agents | Low (API key) | High (structured API) | Easy (JSON) | Low |

---

> **Previous:** [Chapter 21: Architecture Deep-Dive — Pi](21_architecture_pi.md)  
> **Next:** [Chapter 23: Full Build — Production Harness](23_full_build_production_harness.md)
