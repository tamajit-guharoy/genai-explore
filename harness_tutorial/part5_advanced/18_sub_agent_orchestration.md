# Chapter 18: Sub-Agent Orchestration

> **Previous:** [Chapter 17: Multi-Provider Abstraction](17_multi_provider_abstraction.md)  
> **Next:** [Chapter 19: Human-in-the-Loop](19_human_in_the_loop.md)

---

## What You'll Learn

- The orchestrator-worker pattern: spawn agents AS tools
- How to run sub-agents in parallel and aggregate their results
- Context isolation: why each sub-agent gets a clean slate
- Building a code-review orchestrator that writes, reviews, and tests code
- The difference between sub-agents and regular tool calls

---

## The Orchestrator-Worker Pattern

> **Analogy:** A project manager (orchestrator) delegates tasks to specialists: a frontend developer, a backend developer, and a QA tester. The PM doesn't write code — they coordinate, collect results, and make decisions based on the aggregated output.

```
┌─────────────────────────────────────────────────────────────────┐
│                     ORCHESTRATOR AGENT                           │
│                                                                 │
│  "Here's a feature request. I'll split the work..."             │
│                                                                 │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐              │
│    │ Sub-Agent│     │ Sub-Agent│     │ Sub-Agent│              │
│    │ WRITER   │     │ REVIEWER │     │ TESTER   │              │
│    │          │     │          │     │          │              │
│    │ "Write   │     │ "Review  │     │ "Write   │              │
│    │  the     │     │  the     │     │  tests   │              │
│    │  code"   │     │  code"   │     │  for it" │              │
│    └────┬─────┘     └────┬─────┘     └────┬─────┘              │
│         │                │                │                     │
│         ▼                ▼                ▼                     │
│    source_code      review_notes      test_suite                │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          ▼                                       │
│                 AGGREGATED RESULT                                │
│                                                                 │
│  Orchestrator decides: "Code has bugs — send back to writer"    │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concept: A Sub-Agent IS a Tool

From the orchestrator's perspective, spawning a sub-agent is just another tool call. The orchestrator doesn't know (or care) that the tool implementation runs an entire agentic loop.

```python
# ═══════════════════════════════════════════════════════════════════
# Conceptual: a sub-agent tool from the orchestrator's view
# ═══════════════════════════════════════════════════════════════════

# The orchestrator sees this just like search_web or read_file:
ToolDefinition(
    name="code_writer",
    description="Write Python code for a given specification. "
                "Returns the complete source code.",
    parameters={
        "type": "object",
        "properties": {
            "specification": {
                "type": "string",
                "description": "Detailed specification of what to build"
            }
        },
        "required": ["specification"],
    },
)
```

---

## The Sub-Agent Runner

Here's the core engine. Each sub-agent gets its own provider, its own message history, and its own set of tools.

```python
# ═══════════════════════════════════════════════════════════════════
# sub_agent.py — A mini-harness that runs as a tool
# ═══════════════════════════════════════════════════════════════════

import asyncio
from dataclasses import dataclass, field
from typing import Any, Callable

from .base_provider import LLMProvider, Message, ToolDefinition
from .tool_translator import ToolSchemaTranslator


@dataclass
class SubAgentResult:
    """The result returned by a sub-agent after completing its task."""
    agent_name: str                                              # Which agent produced this
    final_answer: str                                            # The sub-agent's conclusion
    tool_calls_made: int                                         # How many tools it used
    total_tokens: int                                            # Token budget consumed
    duration_seconds: float                                      # How long it took


class SubAgent:
    """A self-contained mini-harness that acts as a tool.

    Each SubAgent has:
    - Its own system prompt (its "personality" / role)
    - Its own set of tools (relevant to its task)
    - A fresh context (no contamination from the parent)
    - A turn limit to prevent infinite loops
    """

    def __init__(
        self,
        name: str,
        system_prompt: str,
        provider: LLMProvider,
        max_turns: int = 5,                                      # Safety: limit agentic loops
    ):
        self.name = name
        self.system_prompt = system_prompt
        self.provider = provider
        self.max_turns = max_turns
        self.tools: dict[str, Callable] = {}                     # Tool registry for THIS sub-agent
        self.tool_defs: list[ToolDefinition] = []

    def register_tool(self, tool_def: ToolDefinition, handler: Callable):
        """Register a tool available to this sub-agent."""
        self.tools[tool_def.name] = handler
        self.tool_defs.append(tool_def)

    async def run(self, task: str) -> SubAgentResult:
        """Execute the sub-agent's task and return the result.

        This is the method the orchestrator calls — it runs a full
        agentic loop internally."""
        import time
        start_time = time.time()

        messages: list[Message] = [
            Message(role="system", content=self.system_prompt),
            Message(role="user", content=task),
        ]
        total_tokens = 0
        tools_used = 0

        for turn in range(self.max_turns):
            response = await self.provider.chat(
                messages=messages,
                tools=self.tool_defs,
                system=self.system_prompt,
            )
            total_tokens += response.usage.get("input_tokens", 0)
            total_tokens += response.usage.get("output_tokens", 0)

            # If the sub-agent is done (no tool calls), return its answer
            if not response.tool_calls:
                return SubAgentResult(
                    agent_name=self.name,
                    final_answer=response.content,
                    tool_calls_made=tools_used,
                    total_tokens=total_tokens,
                    duration_seconds=time.time() - start_time,
                )

            # ═══ Execute tools (sequential — sub-agents are simpler) ═══
            # Add the assistant's tool-use message
            tool_use_content = []
            for tc in response.tool_calls:
                tool_use_content.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.arguments,
                })
            messages.append(Message(role="assistant", content=tool_use_content))

            # Execute each tool and add results
            for tc in response.tool_calls:
                tools_used += 1
                handler = self.tools.get(tc.name)
                if handler:
                    try:
                        result = await handler(**tc.arguments) if asyncio.iscoroutinefunction(handler) \
                                 else handler(**tc.arguments)
                    except Exception as e:
                        result = f"Error executing {tc.name}: {e}"
                else:
                    result = f"Tool '{tc.name}' not found"

                messages.append(Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tc.id,
                    name=tc.name,
                ))

        # Max turns exceeded
        return SubAgentResult(
            agent_name=self.name,
            final_answer=f"[Max turns ({self.max_turns}) exceeded]",
            tool_calls_made=tools_used,
            total_tokens=total_tokens,
            duration_seconds=time.time() - start_time,
        )
```

---

## The Orchestrator: Parallel Execution

The real power comes from running sub-agents concurrently. This is the orchestrator that manages them.

```python
# ═══════════════════════════════════════════════════════════════════
# orchestrator.py — Coordinates sub-agents
# ═══════════════════════════════════════════════════════════════════

import asyncio
from typing import Any

from .base_provider import LLMProvider, LLMResponse, Message, ToolCall, ToolDefinition
from .sub_agent import SubAgent, SubAgentResult


class OrchestratorHarness:
    """An agent harness that can spawn sub-agents as tools.

    The orchestrator itself uses a provider to reason about the overall task,
    then delegates work to specialized sub-agents via tool calls.
    """

    def __init__(self, provider: LLMProvider):
        self.provider = provider
        self.sub_agents: dict[str, SubAgent] = {}                    # Sub-agent registry
        self.regular_tools: dict[str, Any] = {}                      # Non-agent tools
        self.max_turns = 20

    def register_sub_agent(self, name: str, agent: SubAgent):
        """Register a sub-agent that the orchestrator can spawn."""
        self.sub_agents[name] = agent

    def register_tool(self, tool_def: ToolDefinition, handler):
        """Register a regular (non-agent) tool."""
        self.regular_tools[tool_def.name] = (tool_def, handler)

    def _build_tool_defs(self) -> list[ToolDefinition]:
        """Build the combined tool list: sub-agents + regular tools.

        Each sub-agent appears as a tool with its name, a description derived
        from its system prompt, and a 'task' parameter.
        """
        tool_defs: list[ToolDefinition] = []

        # ── Sub-agent tools ──
        for name, agent in self.sub_agents.items():
            # The system prompt's first line serves as the tool description
            description = agent.system_prompt.strip().split("\n")[0]
            tool_defs.append(ToolDefinition(
                name=name,
                description=f"[SUB-AGENT] {description}. This spawns an independent AI agent.",
                parameters={
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": f"Detailed instructions for the {name} sub-agent"
                        }
                    },
                    "required": ["task"],
                },
            ))

        # ── Regular tools ──
        for tool_def, _ in self.regular_tools.values():
            tool_defs.append(tool_def)

        return tool_defs

    async def run_parallel(self, sub_agent_tasks: dict[str, str]) -> dict[str, SubAgentResult]:
        """Run multiple sub-agents in parallel with different tasks.

        Args:
            sub_agent_tasks: {agent_name: task_description} — which agent does what

        Returns:
            {agent_name: SubAgentResult} — results keyed by agent name
        """
        async def _run_one(name: str, task: str) -> tuple[str, SubAgentResult]:
            agent = self.sub_agents.get(name)
            if not agent:
                return (name, SubAgentResult(
                    agent_name=name,
                    final_answer=f"Agent '{name}' not registered",
                    tool_calls_made=0,
                    total_tokens=0,
                    duration_seconds=0,
                ))
            result = await agent.run(task)
            return (name, result)

        # ═══ LAUNCH ALL IN PARALLEL ═══
        tasks = [_run_one(name, task) for name, task in sub_agent_tasks.items()]
        results = await asyncio.gather(*tasks)

        return dict(results)

    async def aggregate(self, results: dict[str, SubAgentResult]) -> str:
        """Ask the orchestrator's LLM to synthesize sub-agent results.

        This is where the orchestrator's own intelligence shines — it reads
        all sub-agent outputs and produces a coherent conclusion.
        """
        # Build a summary of all results
        summary_parts = []
        for name, result in results.items():
            summary_parts.append(
                f"### {name}\n{result.final_answer}\n"
                f"(tokens: {result.total_tokens}, tools: {result.tool_calls_made}, "
                f"time: {result.duration_seconds:.1f}s)"
            )

        summary_text = "\n\n".join(summary_parts)

        response = await self.provider.chat(
            messages=[
                Message(role="system", content=(
                    "You are an orchestrator. Synthesize sub-agent results into "
                    "one coherent answer. Identify conflicts, merge complementary "
                    "information, and present a final conclusion."
                )),
                Message(role="user", content=(
                    f"Sub-agent results:\n\n{summary_text}\n\n"
                    "Provide a synthesized final answer."
                )),
            ],
            system="You are an orchestrator synthesizing sub-agent results.",
        )
        return response.content

    async def run(self, user_message: str) -> str:
        """Full orchestrator loop: reason → delegate → aggregate → respond."""
        messages: list[Message] = [
            Message(role="system", content=(
                "You are an orchestrator agent. You have access to specialized "
                "sub-agents as tools. Decompose complex tasks, delegate work, "
                "and synthesize results."
            )),
            Message(role="user", content=user_message),
        ]

        tool_defs = self._build_tool_defs()

        for turn in range(self.max_turns):
            response = await self.provider.chat(
                messages=messages,
                tools=tool_defs,
            )

            if not response.tool_calls:
                return response.content                           # Done

            for tc in response.tool_calls:
                # Check if this tool call maps to a sub-agent
                if tc.name in self.sub_agents:
                    agent = self.sub_agents[tc.name]
                    task = tc.arguments.get("task", str(tc.arguments))
                    result = await agent.run(task)                # Run sub-agent SEQUENTIALLY

                    messages.append(Message(
                        role="assistant",
                        content=f"Spawned sub-agent {tc.name}"
                    ))
                    messages.append(Message(
                        role="tool",
                        content=(
                            f"Sub-agent {result.agent_name} completed.\n"
                            f"Tokens: {result.total_tokens}\n"
                            f"Tools used: {result.tool_calls_made}\n"
                            f"Duration: {result.duration_seconds:.1f}s\n\n"
                            f"Result:\n{result.final_answer}"
                        ),
                        tool_call_id=tc.id,
                        name=tc.name,
                    ))
                elif tc.name in self.regular_tools:
                    tool_def, handler = self.regular_tools[tc.name]
                    try:
                        tool_result = await handler(**tc.arguments) if asyncio.iscoroutinefunction(handler) \
                                      else handler(**tc.arguments)
                    except Exception as e:
                        tool_result = f"Error: {e}"

                    messages.append(Message(
                        role="assistant",
                        content=f"Used tool {tc.name}"
                    ))
                    messages.append(Message(
                        role="tool",
                        content=str(tool_result),
                        tool_call_id=tc.id,
                        name=tc.name,
                    ))

        return "Max turns exceeded"
```

---

## Complete Example: Code Review Orchestrator

This is the "hello world" of sub-agent orchestration. Three agents: Writer, Reviewer, Tester.

```python
# ═══════════════════════════════════════════════════════════════════
# code_review_orchestrator.py — Full working example
# ═══════════════════════════════════════════════════════════════════

from .providers import AnthropicProvider
from .sub_agent import SubAgent
from .orchestrator import OrchestratorHarness

async def run_code_review_orchestrator():
    """Demonstrate a three-agent code review pipeline."""

    # ═══ Setup: 3 sub-agents, each with their own personality ═══
    provider = AnthropicProvider()  # All sub-agents share one provider (or use different ones)

    writer = SubAgent(
        name="code_writer",
        system_prompt=(
            "You are an expert Python developer. Write clean, well-documented, "
            "production-quality Python code. Include type hints, docstrings, "
            "and error handling. Output ONLY the complete source code."
        ),
        provider=provider,
        max_turns=3,
    )

    reviewer = SubAgent(
        name="code_reviewer",
        system_prompt=(
            "You are a senior code reviewer. Analyze the provided code for:\n"
            "1. Correctness — logic bugs, edge cases\n"
            "2. Style — PEP 8, naming, consistency\n"
            "3. Security — injection, credential exposure\n"
            "4. Performance — bottlenecks, unnecessary allocations\n"
            "Output a structured review with severity levels: CRITICAL, WARNING, INFO."
        ),
        provider=provider,
        max_turns=2,
    )

    tester = SubAgent(
        name="test_writer",
        system_prompt=(
            "You are a QA engineer. Write pytest test cases for the provided code. "
            "Cover: happy path, edge cases, error conditions, and boundary values. "
            "Use fixtures and parametrize where appropriate. Output ONLY the test file."
        ),
        provider=provider,
        max_turns=3,
    )

    # ═══ Setup: Orchestrator ═══
    orchestrator = OrchestratorHarness(provider)
    orchestrator.register_sub_agent("code_writer", writer)
    orchestrator.register_sub_agent("code_reviewer", reviewer)
    orchestrator.register_sub_agent("test_writer", tester)

    # ═══ Option A: Use the orchestrator loop (LLM decides what to delegate) ═══
    result_a = await orchestrator.run(
        "Build a function that validates email addresses according to RFC 5322. "
        "I need the implementation, a code review, and a test suite."
    )
    print("=== Orchestrator auto-delegation result ===")
    print(result_a)

    # ═══ Option B: Direct parallel execution (you decide the split) ═══
    # First, run the writer
    code_result = await writer.run(
        "Write a Python function validate_email(email: str) -> bool "
        "that implements RFC 5322 validation."
    )
    print(f"\nWriter output:\n{code_result.final_answer}")

    # Then run reviewer and tester in PARALLEL (both need the code)
    parallel_results = await orchestrator.run_parallel({
        "code_reviewer": f"Review this code:\n```python\n{code_result.final_answer}\n```",
        "test_writer": f"Write tests for this code:\n```python\n{code_result.final_answer}\n```",
    })

    for name, result in parallel_results.items():
        print(f"\n=== {name} ===")
        print(result.final_answer)

    # Finally, aggregate
    synthesis = await orchestrator.aggregate(parallel_results)
    print(f"\n=== Orchestrator Synthesis ===")
    print(synthesis)
```

---

## Context Isolation: Why It Matters

```
┌───────────────────────────────────────────────────────────────────┐
│                     CONTEXT ISOLATION                              │
│                                                                   │
│   PARENT (Orchestrator)         SUB-AGENT A        SUB-AGENT B    │
│   ┌──────────────────┐     ┌───────────────┐  ┌───────────────┐  │
│   │ Messages: 4500    │     │ Messages: 3    │  │ Messages: 3    │  │
│   │ tokens            │     │ tokens (fresh) │  │ tokens (fresh) │  │
│   │                    │     │                │  │                │  │
│   │ "Here's the task"  │     │ System prompt  │  │ System prompt  │  │
│   │ "Let me delegate"  │     │ + User task    │  │ + User task    │  │
│   │ ...                │     │                │  │                │  │
│   └──────────────────┘     │ Tools: 2        │  │ Tools: 3        │  │
│                             └────────────────┘  └─────────────────┘  │
│   Only the SUB-AGENT'S       Each sub-agent       Each sub-agent     │
│   FINAL ANSWER returns       starts with a        cannot see the     │
│   to the parent.             CLEAN context.       other's context.   │
└───────────────────────────────────────────────────────────────────┘
```

**Without isolation:** Sub-agent A's tool results would leak into Sub-agent B's context, causing confusion, hallucinations, and prompt-injection vectors.

**With isolation:** Each sub-agent operates in a clean bubble. Only the orchestrator sees the whole picture.

---

## When to Use Sub-Agents vs Regular Tools

| Scenario | Use | Reason |
|---|---|---|
| Simple data lookup (API call, DB query) | Regular tool | No reasoning needed |
| Single code generation | Regular tool | One-shot, no iteration |
| Complex multi-step task requiring reasoning | Sub-agent | Needs agentic loop |
| Task requiring different "persona" | Sub-agent | System prompt isolation |
| Parallel independent work | Sub-agent (parallel) | Context isolation prevents interference |
| Sequential dependent work | Orchestrator loop | LLM decides ordering |

---

## Cost Management for Sub-Agents

Sub-agents multiply costs. Three sub-agents × 5 turns = 15 LLM calls. Mitigations:

```python
class BudgetAwareOrchestrator(OrchestratorHarness):
    """Orchestrator that enforces a total token budget across sub-agents."""

    def __init__(self, provider: LLMProvider, max_total_tokens: int = 100_000):
        super().__init__(provider)
        self.max_total_tokens = max_total_tokens
        self.total_tokens_spent = 0

    async def run(self, user_message: str) -> str:
        # Wrap sub-agent runs to track and enforce budget
        original_run = SubAgent.run

        async def budgeted_run(agent_self, task):
            result = await original_run(agent_self, task)
            self.total_tokens_spent += result.total_tokens
            if self.total_tokens_spent > self.max_total_tokens:
                raise BudgetExceededError(
                    f"Budget exceeded: {self.total_tokens_spent} > {self.max_total_tokens}"
                )
            return result

        # Patch sub-agents (in production, use a proper decorator)
        for agent in self.sub_agents.values():
            agent.run = budgeted_run.__get__(agent, SubAgent)

        return await super().run(user_message)
```

---

## Key Takeaways

1. **A sub-agent IS a tool** — the orchestrator doesn't need to know it's spawning another agent loop
2. **Context isolation is the killer feature** — each sub-agent gets a clean slate, no cross-contamination
3. **Parallel execution is where sub-agents shine** — run reviewer + tester simultaneously
4. **The orchestrator adds value through synthesis** — it reads all results and produces a coherent answer
5. **Budget enforcement is critical** — three sub-agents × five turns = real money

---

> **Previous:** [Chapter 17: Multi-Provider Abstraction](17_multi_provider_abstraction.md)  
> **Next:** [Chapter 19: Human-in-the-Loop](19_human_in_the_loop.md)
