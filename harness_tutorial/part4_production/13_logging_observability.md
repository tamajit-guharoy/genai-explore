# Chapter 13: Logging & Observability

## What You'll Learn

- **Structured logging** with JSON format — why `print()` doesn't cut it
- What to log: every model call, every tool call, every error, every token spent
- **OpenTelemetry** traces for distributed debugging across multiple services
- Token counting at each step and **latency breakdowns** to find bottlenecks
- Building a `HarnessLogger` that wraps the harness with full observability
- A **tool-call chain visualizer** — ASCII tree of every tool invocation

---

## 1. The Analogy: The Black Box Flight Recorder

Every commercial aircraft has a flight recorder — the "black box" (which is actually
orange). It records hundreds of parameters: altitude, speed, control inputs, engine
performance. When something goes wrong, investigators **replay the tape** to understand
exactly what happened, second by second.

Your harness needs the same thing.

> **Logging = the black box flight recorder. When something goes wrong at 3 AM,
> you replay the tape instead of guessing.**

---

## 2. Why `print()` Is Not Enough

```python
# ❌ The naive approach — debugging with print()
print("Calling API...")
print(f"Response: {response.choices[0].message.content[:100]}...")
print("Done!")
```

Problems:
- No timestamps — when did each event happen?
- No structure — can't query "show me all 429 errors in the last hour"
- No correlation — which user session does this log belong to?
- No levels — can't filter DEBUG vs ERROR
- No machine readability — can't pipe to monitoring tools

---

## 3. Structured Logging with `structlog`

```bash
pip install structlog python-json-logger
```

```python
import structlog
import logging

# ═══ Configure structlog for JSON output ═══
# JSON logs can be parsed by ELK, Datadog, Grafana, etc.
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,      # filter by log level
        structlog.stdlib.add_logger_name,      # which logger?
        structlog.stdlib.add_log_level,        # INFO, WARN, ERROR, etc.
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),  # timestamps!
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,  # pretty tracebacks
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),   # output as JSON
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

log = structlog.get_logger()
```

---

## 4. What to Log — The Complete Checklist

### 4.1 Every Model Call

```python
# ═══ Before the API call ═══
log.info("llm.call.start",
    model="gpt-4o",
    messages_count=len(messages),
    estimated_tokens=buffer.token_count(),
    tools_count=len(tools) if tools else 0,
)

# ═══ After the API call ═══
log.info("llm.call.complete",
    model="gpt-4o",
    latency_ms=duration_ms,
    input_tokens=response.usage.input_tokens,
    output_tokens=response.usage.output_tokens,
    total_tokens=response.usage.total_tokens,
    cost_usd=calculate_cost(model, response.usage),
    finish_reason=response.choices[0].finish_reason,
)
```

### 4.2 Every Tool Call

```python
log.info("tool.call.start",
    tool_name="read_file",
    tool_args={"path": "/app/config.yaml"},
    call_id=tool_call.id,
)

# ... execute tool ...

log.info("tool.call.complete",
    tool_name="read_file",
    duration_ms=duration_ms,
    result_length=len(result),
    success=True,
    truncated=len(result) > 4000,  # was result truncated?
)
```

### 4.3 Every Error

```python
log.error("llm.call.error",
    error_type="rate_limit",
    status_code=429,
    retry_attempt=attempt,
    backoff_delay=delay,
    model="gpt-4o",
    exc_info=True,  # include full traceback
)
```

---

## 5. Building the `HarnessLogger` Class

```python
from dataclasses import dataclass, field
from datetime import datetime, timezone
import time
import json
import structlog
from typing import Any


@dataclass
class HarnessLogger:
    """Observability wrapper for an AI agent harness.

    Records structured logs for every LLM call, tool execution,
    and error. Produces JSON-formatted logs suitable for ingestion
    by monitoring platforms (Datadog, Grafana, ELK, etc.).

    Think of this as the harness's flight recorder — every significant
    event is timestamped and structured for post-mortem analysis.

    Attributes:
        session_id: Unique ID for this conversation session
        agent_name: Name of the agent (for multi-agent setups)
        log_level: Minimum log level to emit
        cost_per_1k: Model pricing for cost tracking
    """

    session_id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d-%H%M%S"))
    agent_name: str = "default"
    log_level: str = "INFO"

    # ═══ Pricing table ($ per 1K tokens) — update periodically ═══
    # These are mid-2026 approximate prices
    cost_per_1k: dict[str, tuple[float, float]] = field(default_factory=lambda: {
        "gpt-4o":          (0.00250, 0.01000),   # (input, output) per 1K tokens
        "gpt-4o-mini":     (0.00015, 0.00060),
        "gpt-4-turbo":     (0.01000, 0.03000),
        "claude-3-opus":   (0.01500, 0.07500),
        "claude-3-sonnet": (0.00300, 0.01500),
        "claude-3-haiku":  (0.00025, 0.00125),
        "gemini-1.5-pro":  (0.00350, 0.01050),
        "gemini-1.5-flash":(0.00008, 0.00030),
    })

    def __post_init__(self):
        """Set up the structured logger with session context."""
        self._log = structlog.get_logger().bind(
            session_id=self.session_id,
            agent=self.agent_name,
        )
        self._turn_counter = 0
        self._total_cost = 0.0
        self._timers: dict[str, float] = {}  # for latency tracking

    # ═══════════════════════════════════════════════════════════════
    # LLM CALL LOGGING
    # ═══════════════════════════════════════════════════════════════

    def log_llm_start(self, model: str, messages: list[dict],
                      tools: list[dict] | None = None,
                      estimated_tokens: int = 0) -> str:
        """Log the start of an LLM API call. Returns a call_id for correlation."""
        self._turn_counter += 1
        call_id = f"{self.session_id}-turn{self._turn_counter}"

        self._log.info("llm.call.start",
            call_id=call_id,
            model=model,
            turn=self._turn_counter,
            messages_count=len(messages),
            estimated_input_tokens=estimated_tokens,
            tools_count=len(tools) if tools else 0,
        )

        # ═══ Start the latency timer ═══
        self._timers[call_id] = time.monotonic()
        return call_id

    def log_llm_complete(self, call_id: str, model: str,
                         usage: Any, finish_reason: str,
                         has_tool_calls: bool = False) -> dict:
        """Log the completion of an LLM API call. Returns cost breakdown."""
        # ═══ Calculate latency ═══
        start = self._timers.pop(call_id, time.monotonic())
        latency_ms = (time.monotonic() - start) * 1000

        # ═══ Calculate cost ═══
        input_tokens = getattr(usage, "input_tokens", 0)
        output_tokens = getattr(usage, "output_tokens", 0)
        cost = self._calculate_cost(model, input_tokens, output_tokens)
        self._total_cost += cost

        # ═══ Log structured event ═══
        self._log.info("llm.call.complete",
            call_id=call_id,
            model=model,
            latency_ms=round(latency_ms, 1),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            cost_usd=round(cost, 6),
            total_cost_usd=round(self._total_cost, 6),
            finish_reason=finish_reason,
            has_tool_calls=has_tool_calls,
            tokens_per_second=round(output_tokens / (latency_ms / 1000), 1)
                              if latency_ms > 0 else 0,
        )

        return {
            "latency_ms": latency_ms,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": cost,
        }

    # ═══════════════════════════════════════════════════════════════
    # TOOL CALL LOGGING
    # ═══════════════════════════════════════════════════════════════

    def log_tool_start(self, tool_name: str, tool_args: dict,
                       call_id_parent: str, tool_call_id: str) -> str:
        """Log the start of a tool execution. Returns a tool_call_key."""
        tool_key = f"{call_id_parent}-tool-{tool_call_id}"

        # ═══ Sanitize args: redact secrets, truncate long values ═══
        safe_args = self._sanitize_args(tool_args)

        self._log.info("tool.call.start",
            tool_key=tool_key,
            tool_name=tool_name,
            args=safe_args,
            parent_call_id=call_id_parent,
        )

        self._timers[tool_key] = time.monotonic()
        return tool_key

    def log_tool_complete(self, tool_key: str, tool_name: str,
                          result: str, success: bool = True,
                          error: str | None = None) -> None:
        """Log the completion of a tool execution."""
        start = self._timers.pop(tool_key, time.monotonic())
        duration_ms = (time.monotonic() - start) * 1000

        if success:
            self._log.info("tool.call.complete",
                tool_key=tool_key,
                tool_name=tool_name,
                duration_ms=round(duration_ms, 1),
                result_length=len(result),
                result_preview=result[:200] if result else "",
                truncated=len(result) > 4000,
            )
        else:
            self._log.error("tool.call.failed",
                tool_key=tool_key,
                tool_name=tool_name,
                duration_ms=round(duration_ms, 1),
                error=error,
            )

    # ═══════════════════════════════════════════════════════════════
    # ERROR LOGGING
    # ═══════════════════════════════════════════════════════════════

    def log_error(self, error: Exception, context: dict | None = None,
                  retry_attempt: int = 0, exc_info: bool = True) -> None:
        """Log an error with full context for debugging."""
        error_context = {
            "error_type": type(error).__name__,
            "error_message": str(error)[:500],
            "retry_attempt": retry_attempt,
            "turn": self._turn_counter,
        }
        if context:
            error_context.update(context)

        self._log.error("harness.error", **error_context, exc_info=exc_info)

    # ═══════════════════════════════════════════════════════════════
    # SUMMARY & DIAGNOSTICS
    # ═══════════════════════════════════════════════════════════════

    def session_summary(self) -> dict:
        """Return a summary of the entire session."""
        return {
            "session_id": self.session_id,
            "agent": self.agent_name,
            "total_turns": self._turn_counter,
            "total_cost_usd": round(self._total_cost, 6),
            "logged_at": datetime.now(timezone.utc).isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════

    def _calculate_cost(self, model: str, input_tokens: int,
                        output_tokens: int) -> float:
        """Calculate cost from token counts and model pricing."""
        prices = self.cost_per_1k.get(model, (0, 0))
        input_cost = (input_tokens / 1000) * prices[0]
        output_cost = (output_tokens / 1000) * prices[1]
        return input_cost + output_cost

    def _sanitize_args(self, args: dict) -> dict:
        """Redact sensitive keys (api_key, token, secret, password) from tool args."""
        safe = {}
        sensitive_keys = {"api_key", "token", "secret", "password", "authorization"}
        for key, value in args.items():
            if key.lower() in sensitive_keys:
                safe[key] = "***REDACTED***"
            elif isinstance(value, str) and len(value) > 200:
                safe[key] = value[:200] + "..."
            else:
                safe[key] = value
        return safe
```

---

## 6. The Tool-Call Chain Visualizer

When your agent makes nested tool calls, understanding the flow is hard. This
visualizer draws an ASCII tree:

```python
@dataclass
class ToolCallNode:
    """A node in the tool-call tree for visualization."""
    name: str
    args: dict
    result_preview: str = ""
    duration_ms: float = 0
    children: list["ToolCallNode"] = field(default_factory=list)
    success: bool = True


def visualize_tool_chain(root: ToolCallNode, indent: int = 0) -> str:
    """Render a tree of tool calls as ASCII art.

    Example output:
        └── search_files("config*.yaml") [45ms] ✓
            └── read_file("config.yaml") [12ms] ✓
                ├── parse_yaml(...) [3ms] ✓
                └── validate_schema(...) [8ms] ✗ ERROR: invalid port
    """
    lines = []

    def _render(node: ToolCallNode, prefix: str, is_last: bool):
        # ═══ Choose the connector character ═══
        connector = "└── " if is_last else "├── "

        # ═══ Format the node line ═══
        status = "✓" if node.success else "✗"
        args_str = json.dumps(node.args, default=str)[:60]
        node_line = (
            f"{prefix}{connector}"
            f"{node.name}({args_str}) "
            f"[{node.duration_ms:.0f}ms] {status}"
        )
        if not node.success and node.result_preview:
            node_line += f" ERROR: {node.result_preview[:80]}"
        lines.append(node_line)

        # ═══ Render children ═══
        child_prefix = prefix + ("    " if is_last else "│   ")
        for i, child in enumerate(node.children):
            _render(child, child_prefix, i == len(node.children) - 1)

    _render(root, "", True)
    return "\n".join(lines)


# ═══ Usage: collect tool calls during harness execution ═══
def harness_with_visualization():
    """Example: collect tool call nodes and render after execution."""
    hlogger = HarnessLogger()
    root = ToolCallNode(name="harness_run", args={})

    # During execution, append child nodes:
    search_node = ToolCallNode(
        name="search_files",
        args={"pattern": "config*"},
        duration_ms=45,
        result_preview="Found 3 files",
    )
    root.children.append(search_node)

    read_node = ToolCallNode(
        name="read_file",
        args={"path": "config.yaml"},
        duration_ms=12,
    )
    search_node.children.append(read_node)

    # ═══ Render the tree ═══
    print(visualize_tool_chain(root))

    # Output:
    # └── harness_run() [0ms] ✓
    #     └── search_files("config*") [45ms] ✓
    #         └── read_file("config.yaml") [12ms] ✓
```

---

## 7. OpenTelemetry Integration

For distributed tracing across multiple services, OpenTelemetry is the standard:

```bash
pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp
```

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# ═══ Set up OpenTelemetry ═══
# In production, point the exporter at your observability backend
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)


def traced_llm_call(model: str, messages: list[dict]):
    """An LLM call wrapped in an OpenTelemetry span."""
    with tracer.start_as_current_span("llm.call") as span:
        # ═══ Set span attributes for filtering in your observability tool ═══
        span.set_attribute("model", model)
        span.set_attribute("messages.count", len(messages))
        span.set_attribute("gen_ai.system", "openai")

        # ... make the API call ...

        # ═══ Record results as span attributes ═══
        span.set_attribute("gen_ai.usage.input_tokens", response.usage.input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", response.usage.output_tokens)
        span.set_attribute("gen_ai.response.finish_reason",
                          response.choices[0].finish_reason)
```

---

## 8. Latency Breakdown

How to instrument your harness to find bottlenecks:

```python
def instrumented_harness_turn():
    """A harness turn with detailed latency instrumentation."""
    timings = {}

    # ═══ Phase 1: Memory retrieval ═══
    t0 = time.monotonic()
    memories = memory.search(query, k=5)
    timings["memory_search"] = (time.monotonic() - t0) * 1000

    # ═══ Phase 2: Context assembly ═══
    t0 = time.monotonic()
    messages = builder.build(system_prompt, buffer, memory, query)
    timings["context_build"] = (time.monotonic() - t0) * 1000

    # ═══ Phase 3: LLM API call ═══
    t0 = time.monotonic()
    response = client.chat.completions.create(model=model, messages=messages)
    timings["llm_api"] = (time.monotonic() - t0) * 1000

    # ═══ Phase 4: Tool execution (if needed) ═══
    t0 = time.monotonic()
    if response.choices[0].message.tool_calls:
        results = execute_tools(response.choices[0].message.tool_calls)
    timings["tool_exec"] = (time.monotonic() - t0) * 1000

    # ═══ Log the breakdown ═══
    log.info("harness.turn.latency",
        **{k: round(v, 1) for k, v in timings.items()},
        total_ms=round(sum(timings.values()), 1),
    )
```

**Example latency breakdown:**

```
memory_search:     45ms  ████░░░░░░░░░░░░░░   (4%)
context_build:     12ms  █░░░░░░░░░░░░░░░░░   (1%)
llm_api:          980ms  ████████████████████  (91%)
tool_exec:         45ms  ████░░░░░░░░░░░░░░   (4%)
─────────────────────────────────────────
TOTAL:           1082ms
```

This immediately tells you: the LLM is the bottleneck (91%). Optimizing memory or
context assembly won't move the needle — focus on streaming, model selection, or
request batching.

---

## 9. Production Logging Checklist

| What | Why | Format |
|------|-----|--------|
| Session ID | Correlate all events for one user session | UUID or timestamp-based |
| Timestamps (ISO 8601) | Sort events chronologically | `2026-06-21T14:30:00Z` |
| Model + provider | Know which model handled which request | String |
| Token counts (in/out) | Cost tracking, usage trends | Integer |
| Latency (ms) | Performance monitoring, SLA compliance | Float |
| Tool name + args | Reproduce tool executions | String (sanitized) |
| Error type + traceback | Debug failures | String |
| Finish reason | Stop, length, tool_calls, content_filter | Enum string |
| Cost per call | Billing, budget enforcement | Float (USD) |

---

## Key Takeaways

1. **`print()` is for prototyping; structured JSON logging is for production.**
2. **Log every API call with tokens + latency + cost** — you'll need it for debugging AND billing.
3. **The tool-call chain visualizer** lets you see the agent's decision tree at a glance.
4. **Latency breakdowns identify the real bottleneck** — spoiler: it's almost always the LLM.
5. **OpenTelemetry is the industry standard** — adopt it early, integrate with Datadog/Grafana later.

---

> **Previous:** [12 — Error Handling & Retries](12_error_handling_retries.md)
> **Next:** [14 — Cost Tracking & Budgets](14_cost_tracking_budgets.md)
