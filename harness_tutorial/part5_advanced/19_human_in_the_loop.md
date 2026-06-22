# Chapter 19: Human-in-the-Loop

> **Previous:** [Chapter 18: Sub-Agent Orchestration](18_sub_agent_orchestration.md)  
> **Next:** [Chapter 20: Persistent Sessions](20_persistent_sessions.md)

---

## What You'll Learn

- The three gate decisions: ALLOW, ASK, DENY
- Building a policy engine with declarative rules
- Three-level governance: session → agent → server (the Omnigent model)
- Where exactly to insert policy checks in the agentic loop
- Cost budgets, tool allowlists, and approval requirements

---

## Why Human-in-the-Loop?

> **Analogy:** A senior engineer must approve before deploying to production. The junior engineer (AI agent) can do the work, but the senior signs off on high-risk actions. Human-in-the-loop is that senior engineer — present at critical decision points, invisible during routine work.

Without guardrails, an AI agent can:
- **Spend $500** on API calls in a runaway loop
- **Delete files** it shouldn't touch
- **Send emails** to the wrong recipients
- **Execute shell commands** that brick the system

The solution isn't to remove autonomy — it's to insert **approval gates** at the right places.

---

## The ALLOW / ASK / DENY Model

Every tool execution passes through a gate. The gate can return one of three decisions:

```
                        ┌─────────────────┐
                        │  POLICY ENGINE  │
                        │                 │
  Tool Call ──────────► │  Evaluate rules │ ───┬── ALLOW  ──► Execute immediately
  + Context             │                 │   │
                        └─────────────────┘   ├── ASK    ──► Pause, ask user for approval
                                              │
                                              └── DENY   ──► Block and report
```

```python
# ═══════════════════════════════════════════════════════════════════
# policy_types.py — Core types for policy enforcement
# ═══════════════════════════════════════════════════════════════════

from enum import Enum
from dataclasses import dataclass, field
from typing import Any


class GateDecision(Enum):
    """What the policy engine decides about a tool call."""
    ALLOW = "allow"                                              # Execute immediately
    ASK = "ask"                                                  # Pause, require human approval
    DENY = "deny"                                                # Block execution entirely


@dataclass
class PolicyResult:
    """Result of evaluating policies against a tool call."""
    decision: GateDecision
    reason: str                                                  # Why (for logging / user display)
    required_approvals: list[str] = field(default_factory=list)  # Who must approve (for ASK)
    cost_impact: float = 0.0                                     # Estimated cost of this call


@dataclass
class ToolCallContext:
    """Everything the policy engine needs to make a decision."""
    tool_name: str
    tool_args: dict[str, Any]
    turn_number: int                                             # Which turn of the loop
    total_cost_spent: float                                      # $ spent so far in this session
    total_tokens_used: int                                       # Total tokens consumed
    session_id: str                                              # Which session this belongs to
    agent_role: str                                              # "orchestrator", "code_writer", etc.
```

---

## The Policy Engine: Declarative Rules

A policy engine is a chain of rules. Each rule returns ALLOW, ASK, or DENY. Rules are evaluated in priority order — the first non-ALLOW result wins.

```python
# ═══════════════════════════════════════════════════════════════════
# policy_engine.py — Declarative rule evaluation
# ═══════════════════════════════════════════════════════════════════

from abc import ABC, abstractmethod
from .policy_types import GateDecision, PolicyResult, ToolCallContext


class PolicyRule(ABC):
    """Base class for all policy rules.

    Each rule inspects a tool call + context and returns a PolicyResult.
    Rules are composable — chain them in a PolicyEngine.
    """

    @abstractmethod
    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        """Evaluate this rule against the tool call context.

        Return PolicyResult(ALLOW, ...) to let execution continue.
        Return anything else to block or pause.
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for logging."""
        ...


class PolicyEngine:
    """Evaluates a chain of policy rules.

    Rules are checked in order. The FIRST non-ALLOW result stops evaluation
    (DENY or ASK). If all rules return ALLOW, execution proceeds.
    """

    def __init__(self):
        self.rules: list[PolicyRule] = []

    def add_rule(self, rule: PolicyRule):
        """Add a rule to the end of the evaluation chain."""
        self.rules.append(rule)

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        """Evaluate all rules. First non-ALLOW wins. ALLOW if all pass."""
        for rule in self.rules:
            result = rule.evaluate(ctx)
            if result.decision != GateDecision.ALLOW:
                return result
        return PolicyResult(decision=GateDecision.ALLOW, reason="All rules passed")


# ═══════════════════════════════════════════════════════════════════
# Built-in Policy Rules
# ═══════════════════════════════════════════════════════════════════

class CostBudgetRule(PolicyRule):
    """DENY all tool calls when total cost exceeds the budget."""

    def __init__(self, max_budget_usd: float):
        self.max_budget = max_budget_usd
        self._name = "cost_budget"

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        if ctx.total_cost_spent >= self.max_budget:
            return PolicyResult(
                decision=GateDecision.DENY,
                reason=f"Budget exhausted: ${ctx.total_cost_spent:.4f} >= ${self.max_budget:.2f}",
            )
        return PolicyResult(decision=GateDecision.ALLOW, reason="Within budget")


class ToolAllowlistRule(PolicyRule):
    """Only allow tools that are in the explicit allowlist. Block everything else."""

    def __init__(self, allowed_tools: list[str]):
        self.allowed_tools = set(allowed_tools)
        self._name = "tool_allowlist"

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        if ctx.tool_name not in self.allowed_tools:
            return PolicyResult(
                decision=GateDecision.DENY,
                reason=f"Tool '{ctx.tool_name}' is not in the allowlist: {self.allowed_tools}",
            )
        return PolicyResult(decision=GateDecision.ALLOW, reason="Tool in allowlist")


class ToolBlocklistRule(PolicyRule):
    """Explicitly block dangerous tools."""

    DANGEROUS_TOOLS = {"delete_file", "execute_shell", "send_email", "sudo", "rm", "shutdown"}

    def __init__(self, blocked_tools: list[str] | None = None):
        self.blocked = set(blocked_tools) if blocked_tools else self.DANGEROUS_TOOLS
        self._name = "tool_blocklist"

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        if ctx.tool_name in self.blocked:
            return PolicyResult(
                decision=GateDecision.DENY,
                reason=f"Tool '{ctx.tool_name}' is blocked (dangerous operation)",
            )
        return PolicyResult(decision=GateDecision.ALLOW, reason="Tool not blocked")


class RequireApprovalRule(PolicyRule):
    """Require human approval for specific tools or above a cost threshold."""

    def __init__(
        self,
        tools_requiring_approval: list[str] | None = None,
        cost_threshold_per_call: float | None = None,
        cost_threshold_cumulative: float | None = None,
    ):
        self.approval_tools = set(tools_requiring_approval or [])
        self.cost_threshold_per_call = cost_threshold_per_call
        self.cost_threshold_cumulative = cost_threshold_cumulative
        self._name = "require_approval"

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        reasons = []

        if ctx.tool_name in self.approval_tools:
            reasons.append(f"Tool '{ctx.tool_name}' requires approval")

        if self.cost_threshold_per_call and ctx.cost_impact >= self.cost_threshold_per_call:
            reasons.append(
                f"Per-call cost ${ctx.cost_impact:.4f} >= threshold ${self.cost_threshold_per_call:.2f}"
            )

        if self.cost_threshold_cumulative and ctx.total_cost_spent >= self.cost_threshold_cumulative:
            reasons.append(
                f"Cumulative cost ${ctx.total_cost_spent:.4f} >= threshold ${self.cost_threshold_cumulative:.2f}"
            )

        if reasons:
            return PolicyResult(
                decision=GateDecision.ASK,
                reason="; ".join(reasons),
            )
        return PolicyResult(decision=GateDecision.ALLOW, reason="No approval required")


class TurnLimitRule(PolicyRule):
    """DENY after exceeding max turns (catches infinite loops)."""

    def __init__(self, max_turns: int = 50):
        self.max_turns = max_turns
        self._name = "turn_limit"

    @property
    def name(self) -> str:
        return self._name

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        if ctx.turn_number > self.max_turns:
            return PolicyResult(
                decision=GateDecision.DENY,
                reason=f"Turn limit exceeded: {ctx.turn_number} > {self.max_turns}",
            )
        return PolicyResult(decision=GateDecision.ALLOW, reason="Turn limit OK")
```

---

## Three-Level Governance (The Omnigent Model)

Omnigent pioneered a three-level governance model that's worth adopting:

```
┌──────────────────────────────────────────────────────────────────┐
│                    THREE-LEVEL GOVERNANCE                         │
│                                                                  │
│  LEVEL 1: SESSION POLICIES (most permissive)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Set by the END USER per session.                           │ │
│  │ "Allow Claude to search the web this session"              │ │
│  │ "Budget: $5 for this conversation"                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          ↓  UNION (most restrictive wins)       │
│  LEVEL 2: AGENT POLICIES (defined by agent config)              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Set by the AGENT DEVELOPER.                                │ │
│  │ "This agent can read files but never delete them"          │ │
│  │ "Maximum 20 tool calls per task"                           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                          ↓  UNION (most restrictive wins)       │
│  LEVEL 3: SERVER POLICIES (most restrictive)                    │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Set by the SYSTEM ADMIN.                                   │ │
│  │ "No outbound network from sandbox"                         │ │
│  │ "Max 1GB disk, 512MB RAM per agent"                        │ │
│  │ "Blocked tools: execute_shell, send_email"                 │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  EFFECTIVE POLICY = session_policies ∩ agent_policies ∩ server_policies
└──────────────────────────────────────────────────────────────────┘
```

```python
# ═══════════════════════════════════════════════════════════════════
# three_level_governance.py
# ═══════════════════════════════════════════════════════════════════

class ThreeLevelPolicyEngine:
    """Combines session, agent, and server policies into one evaluation.

    The effective policy is the INTERSECTION: all three levels must ALLOW.
    If any level says DENY, the tool is blocked.
    If any level says ASK (and none say DENY), the user is prompted.
    """

    def __init__(self):
        self.session_engine = PolicyEngine()                     # User-configured per session
        self.agent_engine = PolicyEngine()                       # Agent developer-configured
        self.server_engine = PolicyEngine()                      # System administrator-configured

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        """Evaluate all three levels. Most restrictive wins.

        Priority: DENY > ASK > ALLOW
        If server says DENY, nothing else matters.
        """
        results = {
            "session": self.session_engine.evaluate(ctx),
            "agent": self.agent_engine.evaluate(ctx),
            "server": self.server_engine.evaluate(ctx),
        }

        # ═══ Priority: DENY at any level blocks everything ═══
        for level, result in results.items():
            if result.decision == GateDecision.DENY:
                return PolicyResult(
                    decision=GateDecision.DENY,
                    reason=f"[{level}] {result.reason}",
                )

        # ═══ ASK at any level means ASK overall ═══
        for level, result in results.items():
            if result.decision == GateDecision.ASK:
                return PolicyResult(
                    decision=GateDecision.ASK,
                    reason=f"[{level}] {result.reason}",
                    required_approvals=result.required_approvals,
                )

        # ═══ All clear ═══
        return PolicyResult(decision=GateDecision.ALLOW, reason="All governance levels: ALLOW")
```

---

## The Exact Point in the Agentic Loop Where Policies Are Checked

Here's the critical integration. Policies must be checked AFTER the model returns a tool call but BEFORE execution:

```python
# ═══════════════════════════════════════════════════════════════════
# harness_with_policies.py — WHERE policies plug in
# ═══════════════════════════════════════════════════════════════════

class PolicyAwareHarness:
    """Harness with policy enforcement at the right point in the loop."""

    def __init__(self, provider, policy_engine: ThreeLevelPolicyEngine):
        self.provider = provider
        self.policy_engine = policy_engine
        self.tools: dict[str, callable] = {}
        self.tool_defs: list = []
        self.total_cost = 0.0
        self.total_tokens = 0
        self.session_id = "session-001"
        self._approval_callback = None                             # Function to call for ASK decisions

    def set_approval_callback(self, callback):
        """Set a callback that prompts the user for approval.

        callback(tool_name, tool_args, reason) -> bool
        Returns True if approved, False if denied.
        """
        self._approval_callback = callback

    def register_tool(self, tool_def, handler, cost_per_call: float = 0.0):
        """Register a tool with its estimated cost."""
        self.tools[tool_def.name] = {
            "handler": handler,
            "definition": tool_def,
            "cost": cost_per_call,
        }
        self.tool_defs.append(tool_def)

    async def run(self, user_message: str, system_prompt: str = "") -> str:
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=user_message),
        ]

        for turn in range(1, 100):                                 # Turn counter for policy context
            # ── Step 1: Get model response ──
            response = await self.provider.chat(
                messages=messages,
                tools=self.tool_defs,
                system=system_prompt,
            )

            # Track cost
            self.total_tokens += response.usage.get("input_tokens", 0)
            self.total_tokens += response.usage.get("output_tokens", 0)
            # Assume $0.000003/token for input, $0.000015/token for output (approx GPT-4 pricing)
            turn_cost = (
                response.usage.get("input_tokens", 0) * 0.000003 +
                response.usage.get("output_tokens", 0) * 0.000015
            )
            self.total_cost += turn_cost

            if not response.tool_calls:
                return response.content                         # Done

            # ── Step 2: POLICY EVALUATION (THE CRITICAL POINT) ──
            for tc in response.tool_calls:
                tool_info = self.tools.get(tc.name, {})
                tool_cost = tool_info.get("cost", 0.0)

                ctx = ToolCallContext(
                    tool_name=tc.name,
                    tool_args=tc.arguments,
                    turn_number=turn,
                    total_cost_spent=self.total_cost,
                    total_tokens_used=self.total_tokens,
                    session_id=self.session_id,
                    agent_role="main",
                )

                policy_result = self.policy_engine.evaluate(ctx)

                # ═══ BRANCH on policy decision ═══
                if policy_result.decision == GateDecision.DENY:
                    # Return the DENY reason as the tool result
                    messages.append(Message(role="assistant", content=f"Attempted {tc.name}"))
                    messages.append(Message(
                        role="tool",
                        content=f"BLOCKED: {policy_result.reason}",
                        tool_call_id=tc.id,
                        name=tc.name,
                    ))
                    continue                                    # Skip to next tool call

                elif policy_result.decision == GateDecision.ASK:
                    if self._approval_callback:
                        approved = self._approval_callback(
                            tc.name, tc.arguments, policy_result.reason
                        )
                        if not approved:
                            messages.append(Message(
                                role="assistant",
                                content=f"Attempted {tc.name} (awaiting approval)"
                            ))
                            messages.append(Message(
                                role="tool",
                                content=f"DENIED by user: {policy_result.reason}",
                                tool_call_id=tc.id,
                                name=tc.name,
                            ))
                            continue                            # User said no
                    # User approved — fall through to execution

                # ── Step 3: Execute (ALLOW path or ASK-approved path) ──
                handler = self.tools.get(tc.name, {}).get("handler")
                if handler:
                    try:
                        result = await handler(**tc.arguments) if asyncio.iscoroutinefunction(handler) \
                                 else handler(**tc.arguments)
                    except Exception as e:
                        result = f"Error: {e}"
                else:
                    result = f"Tool '{tc.name}' not found"

                # ── Step 4: Feed result back to the model ──
                messages.append(Message(role="assistant", content=f"Called {tc.name}({tc.arguments})"))
                messages.append(Message(
                    role="tool",
                    content=str(result),
                    tool_call_id=tc.id,
                    name=tc.name,
                ))

        return "Max turns exceeded"
```

---

## Complete Example: Building a Guarded Harness

```python
# ═══════════════════════════════════════════════════════════════════
# example_guarded_harness.py
# ═══════════════════════════════════════════════════════════════════

async def build_guarded_harness():
    """Build a harness with full three-level governance."""

    # ═══ Server-level policies (sysadmin — most restrictive) ═══
    server_policies = PolicyEngine()
    server_policies.add_rule(ToolBlocklistRule([
        "execute_shell", "rm", "sudo", "shutdown", "delete_file"
    ]))
    server_policies.add_rule(TurnLimitRule(max_turns=50))

    # ═══ Agent-level policies (developer) ═══
    agent_policies = PolicyEngine()
    agent_policies.add_rule(CostBudgetRule(max_budget_usd=5.00))
    agent_policies.add_rule(ToolAllowlistRule([
        "search_web", "read_file", "write_file",
        "code_writer", "code_reviewer"               # Sub-agents are allowed
    ]))
    agent_policies.add_rule(RequireApprovalRule(
        tools_requiring_approval=["write_file"],     # Writing files requires approval
        cost_threshold_cumulative=2.00,              # Ask before spending > $2
    ))

    # ═══ Session-level policies (user) ═══
    session_policies = PolicyEngine()
    session_policies.add_rule(CostBudgetRule(max_budget_usd=3.00))  # User sets $3 limit

    # ═══ Combine all three levels ═══
    governance = ThreeLevelPolicyEngine()
    governance.server_engine = server_policies
    governance.agent_engine = agent_policies
    governance.session_engine = session_policies

    # ═══ Approval callback (in real app, this would be a CLI prompt or web UI) ═══
    def cli_approval(tool_name, tool_args, reason):
        print(f"\n{'='*60}")
        print(f"⚠️  APPROVAL REQUIRED")
        print(f"   Tool: {tool_name}")
        print(f"   Args: {tool_args}")
        print(f"   Reason: {reason}")
        print(f"{'='*60}")
        response = input("Approve? [y/N]: ").strip().lower()
        return response == "y"

    harness = PolicyAwareHarness(
        provider=AnthropicProvider(),
        policy_engine=governance,
    )
    harness.set_approval_callback(cli_approval)

    # Register tools
    harness.register_tool(
        ToolDefinition(
            name="search_web",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
        handler=lambda query: f"Results for: {query}",
        cost_per_call=0.0,
    )

    harness.register_tool(
        ToolDefinition(
            name="write_file",
            description="Write content to a file",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        ),
        handler=lambda path, content: f"Wrote {len(content)} bytes to {path}",
        cost_per_call=0.0,
    )

    # ═══ Run ═══
    result = await harness.run(
        "Search for the latest Python release and save the version number to a file.",
        system_prompt="You are a helpful assistant with file and search tools.",
    )
    print(f"\nFinal result: {result}")
```

---

## Policy Debugging: Why Was This Blocked?

When a tool call is denied, you need to know WHY. Add a trace mode:

```python
class TraceablePolicyEngine(PolicyEngine):
    """Policy engine that records every rule evaluation for debugging."""

    def __init__(self):
        super().__init__()
        self.trace: list[dict] = []                                # Full evaluation trace

    def evaluate(self, ctx: ToolCallContext) -> PolicyResult:
        self.trace = []
        for rule in self.rules:
            result = rule.evaluate(ctx)
            self.trace.append({
                "rule": rule.name,
                "decision": result.decision.value,
                "reason": result.reason,
            })
            if result.decision != GateDecision.ALLOW:
                return result
        return PolicyResult(decision=GateDecision.ALLOW, reason="All rules passed")

    def explain_last_decision(self) -> str:
        """Return a human-readable explanation of the last evaluation."""
        lines = []
        for entry in self.trace:
            icon = {"allow": "✅", "ask": "⚠️", "deny": "🚫"}[entry["decision"]]
            lines.append(f"  {icon} {entry['rule']}: {entry['reason']}")
        return "\n".join(lines)
```

---

## Key Takeaways

1. **Check policies AFTER the model responds, BEFORE tool execution** — this is the single critical insertion point
2. **ALLOW/ASK/DENY is simpler than numeric scores** — three outcomes are enough
3. **Three-level governance prevents gaps** — server locks down the OS, agent locks down capabilities, session lets the user customize
4. **Always provide a reason** — the user needs to know WHY something was blocked
5. **Approval callbacks should be pluggable** — CLI prompt today, web UI tomorrow, Slack integration next week

---

> **Previous:** [Chapter 18: Sub-Agent Orchestration](18_sub_agent_orchestration.md)  
> **Next:** [Chapter 20: Persistent Sessions](20_persistent_sessions.md)
