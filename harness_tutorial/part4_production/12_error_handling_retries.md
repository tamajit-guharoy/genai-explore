# Chapter 12: Error Handling & Retries

## What You'll Learn

- Every failure mode of LLM APIs: rate limits, server errors, timeouts, connection drops
- **Exponential backoff with jitter** — the formula, the code, and why naively retrying
  causes thundering herds
- The **circuit breaker pattern** — stop trying after N consecutive failures
- **Graceful degradation** — fall back to cheaper/faster models when primary fails
- Building a complete `ErrorHandler` class with retry, circuit breaker, and fallback logic

---

## 1. The Analogy: Airbags and Seatbelts

Your car has an engine (the LLM), a steering wheel (the harness loop), and a destination
(the user's goal). Error handling is the **airbags and seatbelts** — you hope you never
need them, but when something goes wrong at 60mph, they're the difference between a
minor inconvenience and a total wreck.

> **Error handling = the airbags and seatbelts of your harness. You don't design for
> the happy path — you design for when everything goes wrong.**

---

## 2. The Failure Taxonomy

LLM APIs can fail in surprisingly many ways. Here's every failure mode you'll encounter:

```
┌────────────────────────────────────────────────────────────────┐
│                     API FAILURE TAXONOMY                        │
├──────────┬─────────────────────┬───────────┬───────────────────┤
│ STATUS   │ MEANING             │ RETRY?    │ TYPICAL CAUSE     │
├──────────┼─────────────────────┼───────────┼───────────────────┤
│ 429      │ Rate limited        │ YES (wait)│ Too many requests │
│ 500      │ Internal server err │ YES       │ Provider outage   │
│ 502      │ Bad gateway         │ YES       │ Proxy issue       │
│ 503      │ Service unavailable │ YES       │ Overloaded        │
│ 504      │ Gateway timeout     │ YES       │ Model slow        │
│ Timeout  │ Request timed out   │ YES       │ Network/model     │
│ ConnErr  │ Connection refused  │ YES       │ DNS/network       │
│ 400      │ Bad request         │ NO        │ Your bug          │
│ 401      │ Unauthorized        │ NO        │ Bad API key       │
│ 402      │ Payment required    │ NO        │ Billing issue     │
│ 403      │ Forbidden           │ NO        │ Access denied     │
│ Context  │ Context too long    │ NO        │ Trim messages     │
└──────────┴─────────────────────┴───────────┴───────────────────┘
```

**The golden rule:** 4xx errors are YOUR fault (don't retry). 5xx, 429, timeouts, and
connection errors are THEIR fault (retry with backoff).

---

## 3. Exponential Backoff with Jitter

### 3.1 The Formula

```
delay = min(base_delay × 2^attempt, max_delay) + random_jitter

Where:
  base_delay = 1 second (starting wait)
  attempt    = 0, 1, 2, 3, ... (how many retries so far)
  max_delay  = 60 seconds (never wait longer than this)
  jitter     = random(0, delay × 0.1)  (adds ±10% randomness)
```

Without jitter, 100 agents hitting the same rate limit all retry at the exact same
moment — a **thundering herd** that re-triggers the limit. Jitter spreads them out.

### 3.2 Visual Timeline

```
Attempt 0: FAIL ─────► wait 1.0s (+ ~0.1s jitter)
Attempt 1: FAIL ─────► wait 2.0s (+ ~0.2s jitter)
Attempt 2: FAIL ─────► wait 4.0s (+ ~0.4s jitter)
Attempt 3: FAIL ─────► wait 8.0s (+ ~0.8s jitter)
Attempt 4: FAIL ─────► wait 16.0s (+ ~1.6s jitter)
Attempt 5: FAIL ─────► wait 32.0s (+ ~3.2s jitter) — GIVE UP
```

---

## 4. The Circuit Breaker Pattern

After **N consecutive failures**, the circuit breaker "opens" — it stops even trying
for a cooldown period. This prevents your harness from hammering a degraded service
and making things worse.

```
     ┌──────────┐
     │  CLOSED  │  Normal operation — requests flow through
     └────┬─────┘
          │ N consecutive failures
          ▼
     ┌──────────┐
     │   OPEN   │  All requests immediately rejected for cooldown period
     └────┬─────┘
          │ Cooldown expires
          ▼
     ┌──────────┐
     │ HALF-OPEN│  One trial request allowed — if it succeeds, close circuit
     └────┬─────┘  If it fails, reopen circuit
          │
     ┌────▼─────┐
     │  CLOSED  │  Back to normal
     └──────────┘
```

---

## 5. Building the `ErrorHandler` Class

```python
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import random
import time
from typing import Callable, Any
from enum import Enum


class CircuitState(Enum):
    CLOSED = "closed"        # normal operation
    OPEN = "open"            # rejecting all requests
    HALF_OPEN = "half_open"  # testing the waters


@dataclass
class ErrorHandler:
    """Production-grade error handler with backoff, circuit breaker, and fallback.

    Think of this as the harness's immune system — it detects failures,
    backs off when overwhelmed, breaks circuits to prevent cascading
    failures, and falls back to alternative models when the primary is down.

    Attributes:
        max_retries: Maximum total retry attempts before giving up
        base_delay: Starting delay in seconds (doubles each attempt)
        max_delay: Cap on the exponential delay
        circuit_threshold: Consecutive failures before opening circuit
        circuit_cooldown: How long the circuit stays open (seconds)
        fallback_models: Ordered list of backup models to try
    """

    max_retries: int = 5
    base_delay: float = 1.0
    max_delay: float = 60.0
    circuit_threshold: int = 5
    circuit_cooldown: float = 30.0
    fallback_models: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize circuit breaker state."""
        self._circuit_state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._circuit_opened_at: datetime | None = None
        self._failure_history: list[dict] = field(default_factory=list)

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════

    def call_with_retry(self, fn: Callable, *args, **kwargs) -> Any:
        """Execute a function with retry, backoff, and circuit breaker.

        Args:
            fn: The callable to execute (typically an API call)
            *args, **kwargs: Passed through to fn

        Returns:
            The return value of fn on success

        Raises:
            RuntimeError: If all retries + fallbacks are exhausted
        """
        # ═══ Check circuit breaker before attempting ═══
        if not self._circuit_allows():
            raise RuntimeError(
                f"Circuit breaker OPEN — {self._circuit_cooldown}s "
                f"cooldown, opened at {self._circuit_opened_at}"
            )

        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # ═══ Attempt the call ═══
                result = fn(*args, **kwargs)

                # ═══ Success! Reset failure counter ═══
                self._on_success()
                return result

            except Exception as e:
                last_error = e
                error_type = self._classify_error(e)

                # ═══ Non-retryable errors — fail immediately ═══
                if not self._is_retryable(error_type):
                    self._record_failure(e, attempt)
                    raise  # re-raise immediately — not our problem to fix

                # ═══ Record the failure ═══
                self._record_failure(e, attempt)

                # ═══ Check if circuit should open ═══
                self._consecutive_failures += 1
                if self._consecutive_failures >= self.circuit_threshold:
                    self._open_circuit()
                    # Try fallback before giving up entirely
                    if self.fallback_models and attempt == self.max_retries:
                        return self._try_fallback(*args, **kwargs)
                    raise RuntimeError(
                        f"Circuit breaker OPEN after {self._consecutive_failures} "
                        f"consecutive failures. Last error: {e}"
                    )

                # ═══ Calculate backoff delay with jitter ═══
                if attempt < self.max_retries:
                    delay = self._backoff_delay(attempt)
                    print(f"[RETRY] Attempt {attempt + 1}/{self.max_retries} "
                          f"failed with {error_type}. Waiting {delay:.1f}s...")
                    time.sleep(delay)

        # ═══ All retries exhausted — try fallback ═══
        if self.fallback_models:
            return self._try_fallback(*args, **kwargs)

        raise RuntimeError(
            f"All {self.max_retries} retries exhausted. "
            f"Last error: {last_error}"
        )

    def retry(self, fn: Callable, *args, **kwargs) -> Any:
        """Alias for call_with_retry — shorter name for common use."""
        return self.call_with_retry(fn, *args, **kwargs)

    def circuit_breaker(self) -> dict:
        """Return current circuit breaker status for monitoring."""
        return {
            "state": self._circuit_state.value,
            "consecutive_failures": self._consecutive_failures,
            "opened_at": self._circuit_opened_at.isoformat()
                         if self._circuit_opened_at else None,
            "failure_history": self._failure_history[-10:],  # last 10 failures
        }

    def reset(self) -> None:
        """Force-reset the circuit breaker (e.g., after deploying a fix)."""
        self._circuit_state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._circuit_opened_at = None

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════

    def _backoff_delay(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter.

        delay = min(base × 2^attempt, max_delay) × (1 + random_jitter)
        """
        raw_delay = min(
            self.base_delay * (2 ** attempt),
            self.max_delay,
        )
        # ═══ Add ±25% jitter to prevent thundering herds ═══
        jitter = raw_delay * 0.25 * (random.random() * 2 - 1)
        return raw_delay + jitter

    def _classify_error(self, error: Exception) -> str:
        """Classify an exception into a retryable/non-retryable category.

        We inspect the error type, status code, and message to determine
        whether retrying makes sense.
        """
        error_str = str(error).lower()

        # ═══ Rate limiting — always retryable, respect Retry-After if present ═══
        if "429" in error_str or "rate limit" in error_str:
            return "rate_limit"

        # ═══ Server errors (5xx) — retryable, usually transient ═══
        for code in ["500", "502", "503", "504"]:
            if code in error_str:
                return f"server_error_{code}"

        # ═══ Network issues — retryable ═══
        if "timeout" in error_str or "timed out" in error_str:
            return "timeout"
        if "connection" in error_str or "connect" in error_str:
            return "connection_error"

        # ═══ Context length — NOT retryable (our bug, trim messages) ═══
        if "context" in error_str and "length" in error_str:
            return "context_length"

        # ═══ Auth/billing — NOT retryable ═══
        if any(code in error_str for code in ["401", "402", "403"]):
            return "auth_error"

        return "unknown"

    def _is_retryable(self, error_type: str) -> bool:
        """Determine if an error type warrants a retry."""
        non_retryable = {"context_length", "auth_error", "bad_request"}
        return error_type not in non_retryable

    def _record_failure(self, error: Exception, attempt: int) -> None:
        """Log failure for debugging and monitoring."""
        self._failure_history.append({
            "timestamp": datetime.now().isoformat(),
            "attempt": attempt,
            "error_type": self._classify_error(error),
            "error_message": str(error)[:200],
        })

    def _circuit_allows(self) -> bool:
        """Check if the circuit breaker allows a request through."""
        if self._circuit_state == CircuitState.CLOSED:
            return True
        if self._circuit_state == CircuitState.OPEN:
            # ═══ Check if cooldown has expired ═══
            elapsed = (datetime.now() - self._circuit_opened_at).total_seconds()
            if elapsed >= self.circuit_cooldown:
                self._circuit_state = CircuitState.HALF_OPEN
                return True  # allow one trial request
            return False
        # HALF_OPEN: allow the trial request
        return True

    def _open_circuit(self) -> None:
        """Open the circuit breaker — reject all requests until cooldown."""
        self._circuit_state = CircuitState.OPEN
        self._circuit_opened_at = datetime.now()
        print(f"[CIRCUIT BREAKER] OPEN — {self._consecutive_failures} "
              f"consecutive failures. Cooling down for {self.circuit_cooldown}s.")

    def _on_success(self) -> None:
        """Handle a successful call — reset failure state."""
        if self._circuit_state == CircuitState.HALF_OPEN:
            print("[CIRCUIT BREAKER] CLOSED — trial request succeeded.")
        self._circuit_state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._circuit_opened_at = None

    def _try_fallback(self, *args, **kwargs) -> Any:
        """Attempt the call with each fallback model in order.

        This implements graceful degradation: if GPT-4o is down,
        try Claude, then GPT-4o-mini, then give up.
        """
        original_model = kwargs.get("model", "unknown")

        for fallback in self.fallback_models:
            print(f"[FALLBACK] Primary model '{original_model}' failed. "
                  f"Trying fallback '{fallback}'...")
            try:
                kwargs["model"] = fallback
                # ═══ Use a fresh handler for the fallback (no retries) ═══
                # We don't want to cascade failures across models
                import openai
                client = kwargs.pop("_client", None)
                if client is None:
                    raise ValueError("Fallback requires _client kwarg")
                response = client.chat.completions.create(**kwargs)
                print(f"[FALLBACK] Success with '{fallback}'!")
                return response
            except Exception as e:
                print(f"[FALLBACK] '{fallback}' also failed: {e}")
                continue

        raise RuntimeError(
            f"All models exhausted: primary '{original_model}' "
            f"and fallbacks {self.fallback_models} all failed."
        )
```

---

## 6. Using ErrorHandler in Your Harness

```python
def production_harness_with_error_handling(user_input: str):
    """A harness that survives API failures gracefully."""
    from openai import OpenAI

    client = OpenAI()

    # ═══ Initialize error handler with fallbacks ═══
    error_handler = ErrorHandler(
        max_retries=3,
        base_delay=1.0,
        circuit_threshold=5,
        circuit_cooldown=30.0,
        fallback_models=["gpt-4o-mini", "gpt-3.5-turbo"],  # cheaper fallbacks
    )

    messages = [{"role": "user", "content": user_input}]

    # ═══ Wrap the API call in error handling ═══
    def api_call():
        return client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            max_tokens=1000,
        )

    try:
        # ═══ call_with_retry handles backoff, circuit breaker, and fallback ═══
        response = error_handler.call_with_retry(api_call)
        return response.choices[0].message.content

    except RuntimeError as e:
        # ═══ Total failure — log it, alert the user, don't crash ═══
        print(f"[FATAL] Harness failed: {e}")
        print(f"[DIAGNOSTIC] Circuit state: {error_handler.circuit_breaker()}")
        return "I'm sorry, the AI service is currently unavailable. Please try again later."

    except Exception as e:
        # ═══ Unexpected errors (bugs in our code) — log and surface ═══
        print(f"[BUG] Unexpected error: {type(e).__name__}: {e}")
        raise
```

---

## 7. Handling 429 Rate Limits Specifically

Rate limits need special treatment — the API often tells you how long to wait:

```python
def handle_rate_limit(response_headers: dict, error_handler: ErrorHandler) -> float:
    """Extract retry-after delay from rate limit headers.

    OpenAI and Anthropic both return headers like:
        x-ratelimit-reset-tokens: 5s
        retry-after: 3
    """
    # ═══ Check for Retry-After header (seconds) ═══
    retry_after = response_headers.get("retry-after")
    if retry_after:
        return float(retry_after)

    # ═══ Check for x-ratelimit-reset-requests ═══
    reset = response_headers.get("x-ratelimit-reset-requests")
    if reset:
        # Parse "5s" → 5.0 or "1m30s" → 90.0
        return _parse_duration(reset)

    # ═══ Fall back to exponential backoff ═══
    return error_handler._backoff_delay(0)


def _parse_duration(dur_str: str) -> float:
    """Parse '5s', '1m30s', etc. into seconds."""
    import re
    total = 0.0
    for match in re.finditer(r"(\d+)(ms|s|m|h)", dur_str):
        value = int(match.group(1))
        unit = match.group(2)
        multipliers = {"ms": 0.001, "s": 1, "m": 60, "h": 3600}
        total += value * multipliers.get(unit, 1)
    return total
```

---

## 8. When to Use Each Pattern

| Pattern | When to Use | Don't Use When |
|---------|------------|----------------|
| **Exponential backoff** | Always — it's the default retry strategy | Non-retryable errors (4xx) |
| **Jitter** | When multiple agents share a rate limit | Single-agent, no contention |
| **Circuit breaker** | Production services with >10 req/min | One-off scripts, low volume |
| **Fallback models** | Critical workloads where downtime costs money | Cost-sensitive applications |
| **Retry-After parsing** | 429 responses with headers | Rate limits without headers (use backoff) |

---

## Key Takeaways

1. **4xx = your fault (don't retry), 5xx/429/timeout = their fault (retry with backoff).**
2. **Exponential backoff without jitter causes thundering herds** — always add randomness.
3. **Circuit breakers prevent cascading failures** — stop trying when the service is clearly down.
4. **Graceful degradation > hard failure** — fall back to a cheaper model rather than returning an error.
5. **The ErrorHandler is middleware** — wrap every API call, every tool execution, every network operation.

---

> **Previous:** [11 — Context Window Management](../part3_memory_context/11_context_window_management.md)
> **Next:** [13 — Logging & Observability](13_logging_observability.md)
