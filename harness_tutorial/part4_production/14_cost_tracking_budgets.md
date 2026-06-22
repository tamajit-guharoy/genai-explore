# Chapter 14: Cost Tracking & Budgets

## What You'll Learn

- Per-session cost accumulation: tracking every token against real model pricing
- **Budget enforcement** at three levels: hard cap, soft cap with warning, per-task budgets
- **Model-tier fallback**: automatically downgrade from opus → sonnet → haiku when budget is tight
- A pricing table for major models (Claude, GPT, Gemini) as of mid-2026
- Building a `CostTracker` with `add_usage()`, `remaining_budget()`, and `would_exceed()`

---

## 1. The Analogy: Your Agent Has a Company Credit Card

Imagine you give an employee a company credit card. You don't say "spend whatever you
want." You set a limit: **$50 per day for lunches, $500 for client dinners, $5,000 for
software licenses.** If they approach the limit, they get a warning. If they exceed it,
the card is declined.

Your AI agent is that employee. Every API call costs money. Every tool call might cost
money (APIs, cloud resources). Without a budget, costs spiral silently.

> **Cost tracking = your agent has a company credit card with limits. You define
> what "expensive" means, and the agent respects those boundaries.**

---

## 2. The Economics of AI Agents

A single API call costs fractions of a cent. But agents make **many** calls:

```
Typical agent session costs (mid-2026):
────────────────────────────────────────────────────────
Simple Q&A (2 turns):                     $0.002
Code review (10 turns + tools):           $0.05
Research agent (30 turns + search):       $0.25
Complex multi-step (50+ turns):           $0.80
Autonomous coding agent (100+ turns):     $3.50+
────────────────────────────────────────────────────────
```

Without tracking, a runaway agent loop can burn $50+ in an hour. With tracking, you
set a $5 budget and the agent stops or downgrades when it's close.

---

## 3. Model Pricing Table (Mid-2026)

Pricing changes frequently — always check the provider's website. This table gives
you a rough order of magnitude:

```
┌─────────────────────────┬──────────────────┬──────────────────┬──────────────┐
│ MODEL                   │ INPUT ($/1M tok) │ OUTPUT ($/1M tok)│ RELATIVE COST│
├─────────────────────────┼──────────────────┼──────────────────┼──────────────┤
│ OpenAI GPT-4o           │       $2.50      │      $10.00      │   $$$$$      │
│ OpenAI GPT-4o-mini      │       $0.15      │       $0.60      │   $          │
│ OpenAI GPT-4.1          │       $2.00      │       $8.00      │   $$$$       │
│ OpenAI GPT-4.1-mini     │       $0.15      │       $0.60      │   $          │
│ OpenAI GPT-4.1-nano     │       $0.05      │       $0.20      │   ¢          │
├─────────────────────────┼──────────────────┼──────────────────┼──────────────┤
│ Anthropic Claude Opus 4 │      $15.00      │      $75.00      │   $$$$$$$$$  │
│ Anthropic Claude Sonnet4│       $3.00      │      $15.00      │   $$$$$      │
│ Anthropic Claude Haiku 4│       $0.25      │       $1.25      │   $          │
├─────────────────────────┼──────────────────┼──────────────────┼──────────────┤
│ Google Gemini 2.5 Pro   │       $3.50      │      $10.50      │   $$$$       │
│ Google Gemini 2.5 Flash │       $0.08      │       $0.30      │   ¢          │
├─────────────────────────┼──────────────────┼──────────────────┼──────────────┤
│ DeepSeek V3             │       $0.27      │       $1.10      │   $          │
│ DeepSeek R1             │       $0.55      │       $2.20      │   $$         │
└─────────────────────────┴──────────────────┴──────────────────┴──────────────┘

$ = cheap (<$1/1M combined)
$$$$$ = expensive (>$10/1M combined)
```

> **Rule of thumb:** Claude Opus is ~6× more expensive than GPT-4o, and ~60× more
> than GPT-4o-mini. Choose your default model wisely.

---

## 4. Cost Accumulation

Every API response includes a `usage` object. Track it cumulatively:

```python
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class UsageRecord:
    """A single usage event — one API call."""
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: float  # time.time()

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens
```

---

## 5. Building the `CostTracker` Class

```python
from dataclasses import dataclass, field
from datetime import datetime
import time
from typing import Callable


@dataclass
class CostTracker:
    """Tracks cumulative AI spending and enforces budget limits.

    Think of this as the agent's finance department — it approves
    every spend, warns when the budget is tight, and cuts off
    spending when limits are hit.

    Attributes:
        budget_total: Hard cap for the entire session ($)
        budget_warning: Soft cap — warn at this threshold ($)
        budget_per_task: Optional per-subtask limit ($)
        model_tiers: Ordered list of models from cheapest to most expensive
                     (used for automatic downgrade)
    """

    budget_total: float = 5.0         # $5 hard cap per session
    budget_warning: float = 4.0       # warn at $4 (80% of budget)
    budget_per_task: float | None = None  # optional per-task limit
    model_tiers: list[str] = field(default_factory=lambda: [
        "gpt-4o-mini",     # cheapest — use when budget is tight
        "gpt-4o",          # mid-tier — default
        "claude-sonnet-4", # expensive — use only when needed
    ])

    def __post_init__(self):
        """Initialize tracking state."""
        self._records: list[UsageRecord] = []
        self._session_start = time.time()
        self._warnings_issued = 0
        self._budget_exhausted = False
        self._task_spends: dict[str, float] = {}  # per-task tracking
        self._current_model_index = 1  # default to mid-tier (gpt-4o)

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════

    def add_usage(self, model: str, input_tokens: int,
                  output_tokens: int, task_id: str | None = None) -> UsageRecord:
        """Record a usage event and check budget.

        Args:
            model: Which model was used
            input_tokens: Tokens sent to the model
            output_tokens: Tokens received from the model
            task_id: Optional task identifier for per-task budget tracking

        Returns:
            The UsageRecord that was created

        Raises:
            BudgetExceededError: If the hard cap would be exceeded
        """
        cost = self._calculate_cost(model, input_tokens, output_tokens)

        # ═══ Check if this would exceed the hard cap ═══
        current_total = self.total_cost()
        if current_total + cost > self.budget_total:
            self._budget_exhausted = True
            raise BudgetExceededError(
                f"Cannot spend ${cost:.4f} — would exceed "
                f"budget of ${self.budget_total:.2f} "
                f"(current: ${current_total:.4f})"
            )

        # ═══ Check per-task budget ═══
        if task_id and self.budget_per_task is not None:
            task_spend = self._task_spends.get(task_id, 0.0)
            if task_spend + cost > self.budget_per_task:
                raise BudgetExceededError(
                    f"Task '{task_id}' would exceed its "
                    f"${self.budget_per_task:.2f} budget"
                )

        # ═══ Record the usage ═══
        record = UsageRecord(
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost,
            timestamp=time.time(),
        )
        self._records.append(record)

        # ═══ Update per-task spend ═══
        if task_id:
            self._task_spends[task_id] = self._task_spends.get(task_id, 0.0) + cost

        # ═══ Check warning threshold ═══
        new_total = current_total + cost
        if new_total >= self.budget_warning and self._warnings_issued == 0:
            self._warnings_issued += 1
            print(
                f"[BUDGET WARNING] ${new_total:.4f} spent of "
                f"${self.budget_total:.2f} budget "
                f"({new_total/self.budget_total*100:.0f}%)"
            )

        return record

    def remaining_budget(self) -> float:
        """How much budget is left?"""
        return max(0.0, self.budget_total - self.total_cost())

    def would_exceed(self, estimated_cost: float) -> bool:
        """Would spending this much exceed the budget?"""
        return self.total_cost() + estimated_cost > self.budget_total

    def total_cost(self) -> float:
        """Total spent so far."""
        return sum(r.cost_usd for r in self._records)

    def total_tokens(self) -> dict[str, int]:
        """Token breakdown by type."""
        return {
            "input_tokens": sum(r.input_tokens for r in self._records),
            "output_tokens": sum(r.output_tokens for r in self._records),
            "total_tokens": sum(r.total_tokens for r in self._records),
        }

    def recommend_model(self, estimated_tokens: int) -> str:
        """Recommend which model tier to use based on remaining budget.

        If the budget is tight, downgrade to a cheaper model.
        If there's plenty of budget, you can afford the expensive one.

        Args:
            estimated_tokens: Rough estimate of tokens for the next call

        Returns:
            The recommended model name
        """
        # ═══ Calculate how much budget is left as a fraction ═══
        budget_remaining_pct = self.remaining_budget() / self.budget_total

        # ═══ Estimate cost of each tier for this call ═══
        for i, model in enumerate(self.model_tiers):
            est_cost = self._estimate_call_cost(model, estimated_tokens)
            if est_cost <= self.remaining_budget() * 0.5:  # use at most 50% per call
                # Found an affordable tier — but don't downgrade
                # below the cheapest model in the list
                return model

        # ═══ Even the cheapest model is tight — return it anyway ═══
        return self.model_tiers[0]

    def auto_downgrade(self) -> str:
        """Switch to the next cheaper model tier.

        Called when the budget is running low. Moves down the model_tiers
        list (index 0 = cheapest). Returns the new model name.
        """
        if self._current_model_index > 0:
            self._current_model_index -= 1
            new_model = self.model_tiers[self._current_model_index]
            print(f"[BUDGET] Auto-downgrading to cheaper model: {new_model}")
            return new_model
        return self.model_tiers[0]  # already at cheapest

    def auto_upgrade(self) -> str:
        """Switch to the next more capable model tier.

        Called when budget is plentiful and the task is complex.
        """
        if self._current_model_index < len(self.model_tiers) - 1:
            self._current_model_index += 1
            return self.model_tiers[self._current_model_index]
        return self.model_tiers[-1]  # already at most expensive

    def summary(self) -> str:
        """Human-readable cost summary."""
        tokens = self.total_tokens()
        elapsed = time.time() - self._session_start
        total = self.total_cost()
        return (
            f"Session Cost Summary\n"
            f"{'='*50}\n"
            f"  Duration:      {elapsed:.0f}s\n"
            f"  API Calls:     {len(self._records)}\n"
            f"  Input Tokens:  {tokens['input_tokens']:,}\n"
            f"  Output Tokens: {tokens['output_tokens']:,}\n"
            f"  Total Cost:    ${total:.4f}\n"
            f"  Budget:        ${self.budget_total:.2f}\n"
            f"  Remaining:     ${self.remaining_budget():.4f}\n"
            f"  Cost/Turn:     ${total/max(len(self._records), 1):.4f}\n"
            f"{'='*50}"
        )

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════

    # ═══ Pricing table: ($ per 1M input tokens, $ per 1M output tokens) ═══
    PRICING: dict[str, tuple[float, float]] = {
        "gpt-4o":              (2.50,  10.00),
        "gpt-4o-mini":         (0.15,   0.60),
        "gpt-4.1":             (2.00,   8.00),
        "gpt-4.1-mini":        (0.15,   0.60),
        "gpt-4.1-nano":        (0.05,   0.20),
        "claude-opus-4":       (15.00, 75.00),
        "claude-sonnet-4":     (3.00,  15.00),
        "claude-haiku-4":      (0.25,   1.25),
        "gemini-2.5-pro":      (3.50,  10.50),
        "gemini-2.5-flash":    (0.08,   0.30),
        "deepseek-v3":         (0.27,   1.10),
        "deepseek-r1":         (0.55,   2.20),
    }

    def _calculate_cost(self, model: str,
                        input_tokens: int, output_tokens: int) -> float:
        """Calculate USD cost from token counts."""
        # ═══ Normalize model name for lookup (strip provider prefix) ═══
        lookup = model
        for prefix in ["openai/", "anthropic/", "google/", "deepseek/"]:
            if model.startswith(prefix):
                lookup = model[len(prefix):]
                break

        prices = self.PRICING.get(lookup)
        if prices is None:
            # ═══ Unknown model — log warning and estimate conservatively ═══
            print(f"[COST] WARNING: Unknown model '{model}', using $5/$15 estimate")
            prices = (5.0, 15.0)  # conservative estimate

        input_cost = (input_tokens / 1_000_000) * prices[0]
        output_cost = (output_tokens / 1_000_000) * prices[1]
        return round(input_cost + output_cost, 8)

    def _estimate_call_cost(self, model: str,
                            estimated_tokens: int) -> float:
        """Estimate cost of a future call (assumes 50/50 input/output split)."""
        half = estimated_tokens // 2
        return self._calculate_cost(model, half, half)


class BudgetExceededError(Exception):
    """Raised when an operation would exceed the budget."""
    pass
```

---

## 6. Integrating CostTracker with the Harness

```python
def harness_with_cost_tracking(user_input: str):
    """A harness that tracks and enforces spending."""
    from openai import OpenAI

    client = OpenAI()
    tracker = CostTracker(
        budget_total=2.00,      # $2 hard cap for this session
        budget_warning=1.50,    # warn at $1.50
        model_tiers=[           # cheapest → most expensive
            "gpt-4o-mini",
            "gpt-4o",
        ],
    )

    messages = [{"role": "user", "content": user_input}]
    current_model = "gpt-4o"  # start with the good model

    while True:
        # ═══ Check if we can afford the call ═══
        if tracker.budget_exhausted:
            print("[BUDGET] Budget exhausted. Stopping.")
            break

        # ═══ Maybe downgrade if budget is tight ═══
        if tracker.remaining_budget() < tracker.budget_total * 0.2:
            current_model = tracker.auto_downgrade()

        try:
            response = client.chat.completions.create(
                model=current_model,
                messages=messages,
                max_tokens=500,
            )
        except Exception as e:
            print(f"[ERROR] API call failed: {e}")
            break

        # ═══ Record the cost ═══
        usage = response.usage
        tracker.add_usage(
            model=current_model,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )

        # ═══ Check remaining budget ═══
        print(f"[COST] Spent: ${tracker.total_cost():.4f}, "
              f"Remaining: ${tracker.remaining_budget():.4f}")

        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})

        # ═══ Stop if the model says it's done (no tool calls, finish_reason=stop) ═══
        if response.choices[0].finish_reason == "stop":
            break

        # ═══ For demo, limit to 5 turns ═══
        if len(messages) > 10:
            break

    # ═══ Print final summary ═══
    print("\n" + tracker.summary())
    return messages
```

---

## 7. Budget Strategies Compared

| Strategy | How It Works | Best For | Risk |
|----------|-------------|----------|------|
| **Hard cap** | Stop immediately when budget is hit | Prototypes, demos | Task left incomplete |
| **Soft cap + warning** | Warn at 80%, stop at 100% | Most production use cases | Still leaves tasks incomplete |
| **Per-task budget** | Each subtask gets its own limit | Multi-goal agents | Complex to configure |
| **Model-tier fallback** | Downgrade models as budget tightens | Long-running agents | Quality degrades but tasks finish |
| **Unlimited + alert** | No cap, but alert if cost exceeds threshold | Internal tools, R&D | Cost can spiral |

---

## 8. Per-Request Cost Comparison (Real Numbers)

For a typical 10-turn conversation with 2K input tokens and 500 output tokens per turn:

```
MODEL               INPUT COST    OUTPUT COST    TOTAL (10 TURNS)
─────────────────────────────────────────────────────────────────
gpt-4.1-nano        $0.0001       $0.0001        $0.0020
gemini-2.5-flash    $0.0002       $0.0002        $0.0035
gpt-4o-mini         $0.0003       $0.0003        $0.0060
deepseek-v3         $0.0005       $0.0006        $0.0110
gpt-4o              $0.0050       $0.0050        $0.1000
claude-sonnet-4     $0.0060       $0.0075        $0.1350
gemini-2.5-pro      $0.0070       $0.0053        $0.1230
claude-opus-4       $0.0300       $0.0375        $0.6750
```

The difference between cheapest and most expensive is **337×**. Choose deliberately.

---

## Key Takeaways

1. **Track every token from day one** — costs that seem trivial at 2 turns become painful at 200.
2. **Model-tier fallback is the best budget strategy** — tasks complete, just with cheaper models.
3. **Hard caps are for safety, soft caps are for UX** — use both.
4. **The pricing table changes monthly** — don't hardcode, use a configurable lookup.
5. **Cost tracking pays for itself** — a single runaway loop can cost more than a month of careful tracking.

---

> **Previous:** [13 — Logging & Observability](13_logging_observability.md)
> **Next:** [15 — Sandboxing & Security](15_sandboxing_security.md)
