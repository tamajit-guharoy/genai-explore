#!/usr/bin/env python3
"""
Example 22: Error Handling, Retry Logic & Idempotency Keys

Demonstrates comprehensive error handling patterns for the Anthropic API,
including exponential backoff with jitter, idempotency keys, and a
safe_call() wrapper that handles all common error types.

Key concepts:
- RateLimitError (429) — retry with backoff
- OverloadedError (529) — retry with backoff
- BadRequestError (400) — do NOT retry
- AuthenticationError (401) — do NOT retry
- PermissionDeniedError (403) — do NOT retry
- NotFoundError (404) — do NOT retry
- APIStatusError (500+) — retry selectively
- APITimeoutError — retry
- APIConnectionError — retry
- Exponential backoff with jitter
- Idempotency-Key header for safe retries
- A safe_call() wrapper that encapsulates all retry logic
"""

import os
import time
import random
import uuid
import json
from typing import Any, Callable, Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from anthropic import (
    Anthropic,
    RateLimitError,
    BadRequestError,
    AuthenticationError,
    PermissionDeniedError,
    NotFoundError,
    APIStatusError,
    APITimeoutError,
    APIConnectionError,
)

load_dotenv()


# ── Configuration ──────────────────────────────────────────────────────────

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_retries: int = 5
    base_delay: float = 1.0      # Initial backoff in seconds
    max_delay: float = 60.0      # Cap for backoff
    jitter_factor: float = 0.1   # +/- 10% jitter

    def get_delay(self, attempt: int) -> float:
        """Calculate delay with exponential backoff and jitter."""
        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
        jitter = delay * self.jitter_factor * random.uniform(-1.0, 1.0)
        return max(0, delay + jitter)


# ── Error classification ───────────────────────────────────────────────────

def is_retryable(error: Exception) -> bool:
    """Determine if an error should be retried."""
    if isinstance(error, RateLimitError):
        return True     # 429 — too many requests, back off
    if isinstance(error, APITimeoutError):
        return True     # Request timed out, safe to retry
    if isinstance(error, APIConnectionError):
        return True     # Connection issue, safe to retry

    # OverloadedError (529) is a subclass of APIStatusError
    if isinstance(error, APIStatusError):
        if error.status_code == 529:
            return True  # Overloaded — retry
        if error.status_code >= 500:
            return True  # Server errors — retry
        return False

    return False


def is_non_retryable(error: Exception) -> bool:
    """Determine if an error should NOT be retried (client errors)."""
    if isinstance(error, BadRequestError):       # 400
        return True
    if isinstance(error, AuthenticationError):    # 401
        return True
    if isinstance(error, PermissionDeniedError):  # 403
        return True
    if isinstance(error, NotFoundError):          # 404
        return True
    # 422 Validation errors (in APIStatusError)
    if isinstance(error, APIStatusError) and error.status_code == 422:
        return True
    return False


# ── The safe_call wrapper ──────────────────────────────────────────────────

def safe_call(
    api_call: Callable[..., Any],
    *args,
    retry_config: Optional[RetryConfig] = None,
    **kwargs,
) -> Any:
    """
    Execute an API call with retry logic, exponential backoff with jitter,
    and idempotency keys for safe retries.

    Args:
        api_call: A callable (e.g., client.messages.create)
        *args: Positional arguments for api_call
        retry_config: RetryConfig instance (defaults to RetryConfig())
        **kwargs: Keyword arguments for api_call

    Returns:
        The API response.

    Raises:
        Exception: The last error encountered if all retries are exhausted
                   or a non-retryable error occurs.
    """
    if retry_config is None:
        retry_config = RetryConfig()

    # Generate a single idempotency key for the entire operation
    idempotency_key = str(uuid.uuid4())
    kwargs["extra_headers"] = kwargs.get("extra_headers", {})
    kwargs["extra_headers"]["Idempotency-Key"] = idempotency_key

    last_error = None

    for attempt in range(retry_config.max_retries + 1):
        try:
            return api_call(*args, **kwargs)

        except Exception as e:
            last_error = e

            if is_non_retryable(e):
                print(f"  [NON-RETRYABLE] {type(e).__name__}: {e}")
                print(f"    This error indicates a problem with the request itself.")
                print(f"    Idempotency-Key used: {idempotency_key}")
                raise

            if is_retryable(e):
                if attempt < retry_config.max_retries:
                    delay = retry_config.get_delay(attempt)
                    print(
                        f"  [RETRY {attempt + 1}/{retry_config.max_retries}] "
                        f"{type(e).__name__}: {short_error(e)}"
                    )
                    print(f"    Backing off {delay:.1f}s (key={idempotency_key[:8]}...)")
                    time.sleep(delay)
                else:
                    print(
                        f"  [EXHAUSTED] All {retry_config.max_retries} retries used. "
                        f"Last error: {type(e).__name__}"
                    )
                    raise
            else:
                # Unknown error type — do not retry
                print(f"  [UNKNOWN] {type(e).__name__}: {e}")
                raise

    raise last_error  # Shouldn't reach here, but satisfies type checker


def short_error(e: Exception) -> str:
    """Return a short string representation of an exception."""
    s = str(e)
    return s[:120] + "..." if len(s) > 120 else s


# ── Demonstration ──────────────────────────────────────────────────────────

def demonstrate_errors():
    """Demonstrate various error handling scenarios."""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = "claude-sonnet-4-20250514"

    print("=" * 72)
    print("ERROR HANDLING, RETRY & IDEMPOTENCY DEMO")
    print("=" * 72)
    print()

    # ── Scenario 1: Successful call ────────────────────────────────────

    print(">>> Scenario 1: Successful API call (baseline)")
    print()

    try:
        response = safe_call(
            client.messages.create,
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": "Say 'hello' in one word."}],
        )
        text = response.content[0].text
        print(f"  Success! Response: {text}")
    except Exception as e:
        print(f"  Unexpected error: {e}")
    print()

    # ── Scenario 2: Intentional bad request (non-retryable) ────────────

    print(">>> Scenario 2: BadRequestError (400 — intentionally triggered)")
    print()

    try:
        # Invalid model name to trigger a 400
        safe_call(
            client.messages.create,
            model="claude-nonexistent-model-9999",
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )
    except BadRequestError as e:
        print(f"  Correctly raised BadRequestError (not retried):")
        print(f"  {short_error(e)}")
    except Exception as e:
        print(f"  Got different error than expected: {type(e).__name__}: {e}")
    print()

    # ── Scenario 3: Missing API key (AuthenticationError) ──────────────

    print(">>> Scenario 3: AuthenticationError pattern (401)")
    print()

    bad_client = Anthropic(api_key="sk-bad-key-for-demo")
    try:
        safe_call(
            bad_client.messages.create,
            model=model,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}],
        )
    except AuthenticationError as e:
        print(f"  Correctly raised AuthenticationError (not retried)")
    except Exception as e:
        # Some SDK versions may raise APIStatusError for non-retryable errors
        print(f"  Error: {type(e).__name__} (expected if API keys are validated)")
    print()

    # ── Scenario 4: Timeout (retryable) ───────────────────────────────

    print(">>> Scenario 4: Timeout pattern (retryable)")
    print()

    try:
        # Set a very short timeout to force a timeout error
        timeout_client = Anthropic(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            timeout=0.001,  # 1ms — will almost certainly time out
        )
        safe_call(
            timeout_client.messages.create,
            model=model,
            max_tokens=100,
            messages=[{"role": "user", "content": "Write a long essay about AI."}],
            retry_config=RetryConfig(max_retries=2, base_delay=0.5),
        )
    except APITimeoutError as e:
        print(f"  Timed out after retries (expected): {type(e).__name__}")
    except Exception as e:
        print(f"  Error: {type(e).__name__}: {short_error(e)}")
    print()

    # ── Scenario 5: Rate limit simulation ──────────────────────────────

    print(">>> Scenario 5: Rate limit handling pattern")
    print()

    # Make several rapid calls to potentially trigger rate limits
    for i in range(5):
        try:
            response = safe_call(
                client.messages.create,
                model=model,
                max_tokens=50,
                messages=[{"role": "user", "content": f"Count to {i}."}],
                retry_config=RetryConfig(max_retries=3, base_delay=0.5),
            )
            text = response.content[0].text
            print(f"  Request {i + 1}: OK — \"{text.strip()}\"")
        except Exception as e:
            print(f"  Request {i + 1}: {type(e).__name__} (after retries)")
    print()

    # ── Scenario 6: Idempotency key demonstration ──────────────────────

    print(">>> Scenario 6: Idempotency key demonstration")
    print()

    # Send the same request twice with the same idempotency key
    idempotent_key = str(uuid.uuid4())
    print(f"  Using idempotency key: {idempotent_key}")
    print()

    for i in range(2):
        try:
            response = client.messages.create(
                model=model,
                max_tokens=100,
                messages=[{"role": "user", "content": "What is 2 + 2?"}],
                extra_headers={"Idempotency-Key": idempotent_key},
            )
            text = response.content[0].text
            print(f"  Request {i + 1}: \"{text.strip()}\" ")
            print(f"    Request ID: {response.id}")
            if i == 0:
                print(f"    (First request — sent to API)")
            else:
                print(f"    (Second request — may return cached result due to idempotency key)")
        except Exception as e:
            print(f"  Request {i + 1}: {type(e).__name__}: {e}")
    print()

    # ── Scenario 7: Overloaded (529) handling pattern ──────────────────

    print(">>> Scenario 7: Overloaded (529 error) handling pattern")
    print()

    print("""
  The overloaded_error (529) occurs when the API is temporarily unable to
  handle requests due to capacity. The correct handling pattern is:

    1. Detect APIStatusError with status_code == 529
    2. Wait with exponential backoff + jitter
    3. Retry with the same idempotency key
    4. If the overload persists after max retries, surface the error
       to the caller with a clear message about API capacity

  The safe_call() wrapper above handles this automatically:
    - 529 is classified as retryable (see is_retryable())
    - Backoff is applied with jitter
    - The same Idempotency-Key is used across all retries
  """)


def main():
    demonstrate_errors()

    print()
    print("=" * 72)
    print("SUMMARY: Error handling patterns")
    print("=" * 72)
    print("""
  Error Type               Code  Retry?  Strategy
  ───────────────────────  ────  ──────  ─────────────────────────
  BadRequestError          400   No      Fix the request
  AuthenticationError      401   No      Check API key
  PermissionDeniedError    403   No      Check permissions
  NotFoundError            404   No      Check resource ID
  RateLimitError           429   Yes     Backoff + jitter
  APIStatusError (5xx)     500+  Yes     Backoff + jitter
  OverloadedError          529   Yes     Backoff + jitter
  APITimeoutError          N/A   Yes     Backoff + longer timeout
  APIConnectionError       N/A   Yes     Backoff + retry

  Idempotency-Key header: Ensures safe retries — the same request
  is processed at most once, preventing duplicate charges.
  """)


if __name__ == "__main__":
    main()
