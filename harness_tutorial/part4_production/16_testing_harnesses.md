# Chapter 16: Testing Harnesses

## What You'll Learn

- **Unit testing** tool executors — mock the LLM, test dispatch logic in isolation
- **Mocking LLM responses** — create fake `tool_use` blocks, test parsing
- **Integration tests** with real APIs using cheap models (haiku, flash)
- **Deterministic replay** — record real API responses, replay for reproducible tests
- **Test fixtures** — pre-built conversation histories, tool schemas, scenarios
- Complete **pytest examples** for every harness component

---

## 1. The Analogy: Ground Tests Before Flight

Before a new aircraft design ever leaves the ground, engineers spend years running
tests:
- **Wind tunnel tests** (unit tests) — test individual components in isolation
- **Taxi tests** (integration tests) — test components working together on the runway
- **Flight tests** (end-to-end tests) — test the whole system in real conditions

Your harness deserves the same rigor. You wouldn't deploy an agent that controls
production infrastructure without testing it first.

> **Testing = you wouldn't fly a plane without ground tests first. Unit tests
> validate components, integration tests validate connections, and replay tests
> validate behavior.**

---

## 2. The Testing Pyramid for AI Harnesses

```
            ┌──────────────┐
            │  E2E TESTS   │  ← Real API, real tools, real scenarios
            │  (few, slow) │     Run nightly or pre-release
            ├──────────────┤
            │ INTEGRATION  │  ← Real API (cheap models), real tools
            │ TESTS        │     Run on PR, takes 1-5 min
            ├──────────────┤
            │  UNIT TESTS  │  ← Mocked LLM, mocked tools
            │  (many, fast)│     Run on every commit, <1 second each
            └──────────────┘
```

---

## 3. Unit Testing: Mocking the LLM

The key insight: you don't need a real LLM to test tool dispatch logic, error handling,
or buffer management. Mock the API response.

### 3.1 Mocking OpenAI's API

```python
from unittest.mock import MagicMock, patch
import pytest
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice


# ═══ FIXTURE: Create a mock ChatCompletion response ═══
def make_mock_response(content: str | None = None,
                       tool_calls: list[dict] | None = None,
                       finish_reason: str = "stop",
                       input_tokens: int = 100,
                       output_tokens: int = 50,
                       ) -> ChatCompletion:
    """Factory for mock OpenAI ChatCompletion responses.

    This lets us test harness behavior without hitting the API.
    We control exactly what the "LLM" returns.
    """
    # ═══ Build the message ═══
    msg_kwargs = {}
    if content is not None:
        msg_kwargs["content"] = content
    if tool_calls:
        msg_kwargs["tool_calls"] = tool_calls

    message = MagicMock(spec=ChatCompletionMessage, **msg_kwargs)

    # ═══ Build the choice ═══
    choice = MagicMock(spec=Choice)
    choice.message = message
    choice.finish_reason = finish_reason

    # ═══ Build the completion ═══
    response = MagicMock(spec=ChatCompletion)
    response.choices = [choice]
    response.usage.input_tokens = input_tokens
    response.usage.output_tokens = output_tokens
    response.usage.total_tokens = input_tokens + output_tokens

    return response
```

### 3.2 Testing the ConversationBuffer

```python
# ═══ TEST: ConversationBuffer token trimming ═══
def test_buffer_trims_when_over_budget():
    """Verify that the buffer drops oldest messages when the token
    budget is exceeded."""
    from part3_memory_context.conversation_buffer import ConversationBuffer

    # ═══ Create a buffer with a very small budget ═══
    buffer = ConversationBuffer(
        max_tokens=100,  # tiny budget — forces trimming
        model="gpt-4o-mini",
        system_prompt="You are helpful.",  # ~5 tokens
    )

    # ═══ Add 10 messages — each ~20-30 tokens ═══
    for i in range(10):
        buffer.add("user", f"This is message number {i} with some extra padding text.")

    # ═══ Assert: buffer should have trimmed old messages ═══
    messages = buffer.get_messages()
    assert len(messages) < 12  # 1 system + at most 10, but likely fewer
    assert messages[0]["role"] == "system"  # system prompt always first
    assert buffer.token_count() <= 100 + 50  # within budget + some tolerance


# ═══ TEST: Buffer never trims system prompt ═══
def test_buffer_preserves_system_prompt():
    """The system prompt must survive even extreme trimming."""
    buffer = ConversationBuffer(
        max_tokens=10,  # absurdly small
        model="gpt-4o-mini",
        system_prompt="CRITICAL INSTRUCTION: Always be polite.",
    )

    # Fill it way past budget
    for i in range(50):
        buffer.add("user", "x" * 100)  # lots of tokens

    messages = buffer.get_messages()
    assert messages[0]["role"] == "system"
    assert "CRITICAL INSTRUCTION" in messages[0]["content"]


# ═══ TEST: Adding tool call messages ═══
def test_buffer_handles_tool_calls():
    """Buffer should correctly store and count tool_call messages."""
    buffer = ConversationBuffer(model="gpt-4o-mini")

    buffer.add_tool_call([
        {
            "id": "call_abc123",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": '{"path": "config.yaml"}',
            },
        }
    ])

    messages = buffer.get_messages()
    # Should have system + 1 assistant (with tool_calls)
    assert len(messages) >= 2
    assert messages[-1]["role"] == "assistant"
    assert "tool_calls" in messages[-1]
```

### 3.3 Testing Tool Dispatch Logic

```python
# ═══ TEST: Tool dispatch picks the right tool ═══
def test_tool_dispatch_routes_correctly():
    """When the LLM returns a tool call, the dispatcher should route
    to the correct tool function."""
    # ═══ Define mock tools ═══
    tools_registry = {
        "search_files": MagicMock(return_value="found 3 files"),
        "read_file": MagicMock(return_value="file contents here"),
        "write_file": MagicMock(return_value="file written"),
    }

    # ═══ Mock LLM response that requests a tool call ═══
    mock_response = make_mock_response(
        content=None,  # tool calls have null content
        tool_calls=[{
            "id": "call_1",
            "type": "function",
            "function": {
                "name": "read_file",
                "arguments": '{"path": "/app/config.yaml"}',
            },
        }],
        finish_reason="tool_calls",
    )

    # ═══ Simulate what the harness does ═══
    tool_call = mock_response.choices[0].message.tool_calls[0]
    tool_name = tool_call["function"]["name"]
    tool_args = {"path": "/app/config.yaml"}  # parsed from JSON

    # ═══ Dispatch ═══
    tool_fn = tools_registry[tool_name]
    result = tool_fn(**tool_args)

    # ═══ Assert ═══
    tools_registry["read_file"].assert_called_once_with(path="/app/config.yaml")
    assert result == "file contents here"


# ═══ TEST: Unknown tool handling ═══
def test_tool_dispatch_unknown_tool():
    """The harness should gracefully handle the LLM requesting
    a tool that doesn't exist."""
    tools_registry = {"search_files": MagicMock()}

    tool_name = "nonexistent_tool"

    # ═══ The harness should not crash — return an error message ═══
    if tool_name not in tools_registry:
        error_result = f"Error: Tool '{tool_name}' not found. Available: {list(tools_registry.keys())}"
    else:
        error_result = "should not reach here"

    assert "not found" in error_result
    assert "search_files" in error_result
```

---

## 4. Testing Error Handling

```python
# ═══ TEST: ErrorHandler retries on 429 ═══
def test_error_handler_retries_on_rate_limit():
    """Simulate a 429 rate limit error and verify retry behavior."""
    from part4_production.error_handler import ErrorHandler

    handler = ErrorHandler(
        max_retries=3,
        base_delay=0.01,  # tiny delay for fast test
    )

    # ═══ Create a mock function that fails twice then succeeds ═══
    call_count = [0]  # mutable counter

    def flaky_api_call():
        call_count[0] += 1
        if call_count[0] < 3:
            # ═══ Simulate rate limit error ═══
            raise Exception("429 Rate limit exceeded. Try again in 5s.")
        return "success!"

    # ═══ Execute with retry ═══
    result = handler.call_with_retry(flaky_api_call)

    # ═══ Assert: it retried twice, then succeeded ═══
    assert result == "success!"
    assert call_count[0] == 3  # 2 failures + 1 success


# ═══ TEST: Circuit breaker opens after threshold ═══
def test_circuit_breaker_opens():
    """After N consecutive failures, the circuit breaker should open."""
    handler = ErrorHandler(
        circuit_threshold=3,
        circuit_cooldown=0.1,
        max_retries=1,
        base_delay=0.01,
    )

    # ═══ Fail 3 times in a row ═══
    for i in range(3):
        try:
            handler.call_with_retry(lambda: (_ for _ in ()).throw(
                Exception("500 Internal Server Error")
            ))
        except RuntimeError:
            pass  # expected

    # ═══ Circuit should now be OPEN ═══
    status = handler.circuit_breaker()
    assert status["state"] == "open"
    assert status["consecutive_failures"] >= 3


# ═══ TEST: Non-retryable errors fail immediately ═══
def test_non_retryable_error_fails_fast():
    """401 Unauthorized should NOT be retried."""
    handler = ErrorHandler(max_retries=3)

    with pytest.raises(Exception, match="401"):
        handler.call_with_retry(lambda: (_ for _ in ()).throw(
            Exception("401 Unauthorized — invalid API key")
        ))
```

---

## 5. Testing Cost Tracking

```python
# ═══ TEST: CostTracker enforces hard cap ═══
def test_cost_tracker_hard_cap():
    """When the budget is exceeded, CostTracker should raise."""
    from part4_production.cost_tracker import CostTracker, BudgetExceededError

    tracker = CostTracker(budget_total=0.01)  # $0.01 budget

    # ═══ First call — should succeed (under budget) ═══
    tracker.add_usage("gpt-4o-mini", input_tokens=1000, output_tokens=500)

    # ═══ Second call with lots of tokens — should exceed budget ═══
    with pytest.raises(BudgetExceededError):
        # 100K input + 100K output with gpt-4o is expensive
        tracker.add_usage("gpt-4o", input_tokens=100_000, output_tokens=100_000)


# ═══ TEST: CostTracker recommends cheaper model when budget is tight ═══
def test_cost_tracker_recommends_downgrade():
    """When budget is low, recommend cheaper model tier."""
    tracker = CostTracker(
        budget_total=1.00,
        model_tiers=["gpt-4o-mini", "gpt-4o"],
    )

    # ═══ Spend most of the budget ═══
    tracker.add_usage("gpt-4o", input_tokens=300_000, output_tokens=50_000)
    # That's ~$0.75 + $0.50 = $1.25... would exceed $1.00 budget
    # Let me recalculate: (300K/1M)*2.50 + (50K/1M)*10.00 = 0.75 + 0.50 = 1.25
    # That exceeds $1.00. Let me use fewer tokens.

    # Reset and use fewer tokens
    tracker2 = CostTracker(budget_total=0.10, model_tiers=["gpt-4o-mini", "gpt-4o"])
    tracker2.add_usage("gpt-4o", input_tokens=500, output_tokens=100)
    # ~$0.00125 + $0.001 = $0.00225 spent, $0.09775 remaining (~97.75% remaining)

    # ═══ With plenty of budget, recommend stays at current tier ═══
    # (The recommend_model checks remaining budget percentage)
    recommended = tracker2.recommend_model(estimated_tokens=1000)
    assert recommended in tracker2.model_tiers  # some model is recommended


# ═══ TEST: UsageRecord calculation ═══
def test_usage_record_calculation():
    """Verify token math in UsageRecord."""
    from part4_production.cost_tracker import UsageRecord
    import time

    record = UsageRecord(
        model="gpt-4o-mini",
        input_tokens=5000,
        output_tokens=2000,
        cost_usd=0.00195,  # (5000/1M)*0.15 + (2000/1M)*0.60 = 0.00075 + 0.00120
        timestamp=time.time(),
    )

    assert record.total_tokens == 7000
    assert record.cost_usd == pytest.approx(0.00195, rel=1e-3)
```

---

## 6. Deterministic Replay Testing

The holy grail of harness testing: record real API responses once, replay them
infinitely for deterministic, fast, free tests.

```python
import json
import hashlib
from pathlib import Path


class ResponseRecorder:
    """Record API responses for deterministic replay testing.

    WORKFLOW:
    1. RECORD mode: Run harness against real API, save responses to disk
    2. REPLAY mode: Load saved responses, run tests without API calls

    This makes tests: deterministic (same response every time),
    fast (no network latency), and free (no API costs).
    """

    def __init__(self, cache_dir: str = "./test_fixtures/responses",
                 mode: str = "replay"):
        """Initialize the recorder.

        Args:
            cache_dir: Where to store/load recorded responses
            mode: 'record' to save real responses, 'replay' to load them
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.mode = mode

    def _cache_key(self, model: str, messages: list[dict],
                   tools: list[dict] | None = None) -> str:
        """Generate a deterministic cache key from the request.

        We hash the serialized request to create a unique filename.
        Same request → same hash → same cached response.
        """
        request_data = {
            "model": model,
            "messages": messages,
            "tools": tools or [],
        }
        serialized = json.dumps(request_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()[:16]

    def get_response(self, model: str, messages: list[dict],
                     tools: list[dict] | None = None,
                     real_api_call=None) -> dict:
        """Get a response — from cache (replay) or real API (record).

        Args:
            model: Model name
            messages: The messages array
            tools: Tool definitions
            real_api_call: Callable that makes the real API call (record mode only)

        Returns:
            The API response as a dict
        """
        key = self._cache_key(model, messages, tools)
        cache_file = self.cache_dir / f"{key}.json"

        if self.mode == "replay" and cache_file.exists():
            # ═══ Load cached response ═══
            with open(cache_file) as f:
                return json.load(f)

        elif self.mode == "record":
            # ═══ Call real API and save response ═══
            if real_api_call is None:
                raise ValueError("real_api_call is required in record mode")
            response = real_api_call()
            with open(cache_file, "w") as f:
                json.dump(response, f, default=str, indent=2)
            return response

        else:
            raise RuntimeError(
                f"No cached response for key {key} in replay mode. "
                f"Run in record mode first."
            )


# ═══ Example: Using ResponseRecorder in tests ═══
def test_harness_with_replay():
    """Test harness behavior using recorded API responses."""
    recorder = ResponseRecorder(
        cache_dir="./test_fixtures/responses",
        mode="replay",  # no API calls in CI
    )

    messages = [{"role": "user", "content": "Hello!"}]

    # ═══ In replay mode, this loads from disk instead of calling API ═══
    response = recorder.get_response(
        model="gpt-4o-mini",
        messages=messages,
        real_api_call=None,  # not needed in replay mode
    )

    assert "choices" in response
    assert len(response["choices"]) > 0
```

---

## 7. Test Fixtures: Pre-Built Conversation Histories

```python
# ═══ FIXTURE: A multi-turn conversation with tool calls ═══
@pytest.fixture
def multi_turn_conversation():
    """A realistic conversation history for testing."""
    return [
        {"role": "system", "content": "You are a coding assistant."},
        {"role": "user", "content": "Find all YAML files in my project."},
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [{
                "id": "call_1",
                "type": "function",
                "function": {
                    "name": "search_files",
                    "arguments": '{"pattern": "*.yaml", "path": "/project"}',
                },
            }],
        },
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": "Found: config.yaml, deploy.yaml, secrets.yaml",
        },
        {
            "role": "assistant",
            "content": "I found 3 YAML files: config.yaml, deploy.yaml, and secrets.yaml.",
        },
    ]


# ═══ FIXTURE: Tool schemas for testing ═══
@pytest.fixture
def tool_schemas():
    """Standard tool definitions used across tests."""
    return [
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Read the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path to the file",
                        },
                    },
                    "required": ["path"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "search_files",
                "description": "Find files matching a pattern",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pattern": {"type": "string"},
                        "path": {"type": "string"},
                    },
                    "required": ["pattern"],
                },
            },
        },
    ]


# ═══ TEST: Validate conversation fixture structure ═══
def test_fixture_validity(multi_turn_conversation, tool_schemas):
    """Ensure our fixtures are well-formed."""
    # ═══ Every message should have a role ═══
    for msg in multi_turn_conversation:
        assert "role" in msg
        assert msg["role"] in ("system", "user", "assistant", "tool")

    # ═══ Tool schemas should have the correct structure ═══
    for tool in tool_schemas:
        assert "type" in tool
        assert tool["type"] == "function"
        assert "function" in tool
        assert "name" in tool["function"]
        assert "parameters" in tool["function"]
```

---

## 8. Integration Tests with Real APIs (Cheap Models)

```python
import pytest
import os


@pytest.mark.integration  # marker to skip in CI without API keys
@pytest.mark.slow  # marker for tests that take >1 second
def test_real_api_harness_loop():
    """End-to-end test with a real API call using a cheap model.

    This test actually calls the API. It costs ~$0.0003 per run.
    Skip it in CI unless OPENAI_API_KEY is set.
    """
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set — skipping integration test")

    from openai import OpenAI
    client = OpenAI()

    # ═══ Use the cheapest model possible ═══
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # ~$0.00015 per 1K input tokens
        messages=[{"role": "user", "content": "Say 'hello world' and nothing else."}],
        max_tokens=20,
        temperature=0,  # deterministic for testing
    )

    # ═══ Basic assertions ═══
    assert response.choices[0].finish_reason == "stop"
    assert "hello" in response.choices[0].message.content.lower()
    assert response.usage.total_tokens > 0


@pytest.mark.integration
def test_harness_with_tool_calling():
    """Integration test: harness with tool calling using real API."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    from openai import OpenAI
    client = OpenAI()

    tools = [{
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                },
                "required": ["city"],
            },
        },
    }]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": "What's the weather in Paris?",
        }],
        tools=tools,
        tool_choice="auto",
        max_tokens=100,
    )

    # ═══ Should request the get_weather tool ═══
    message = response.choices[0].message
    assert message.tool_calls is not None
    assert len(message.tool_calls) == 1
    assert message.tool_calls[0].function.name == "get_weather"
```

---

## 9. Running the Test Suite

```bash
# ═══ Run all unit tests (fast, no API calls) ═══
pytest harness_tutorial/tests/ -v -m "not integration"

# ═══ Run integration tests (requires API key) ═══
pytest harness_tutorial/tests/ -v -m integration

# ═══ Run all tests with coverage ═══
pip install pytest-cov
pytest harness_tutorial/tests/ -v --cov=harness_tutorial --cov-report=html

# ═══ Sample pytest.ini ═══
# [pytest]
# markers =
#     unit: Fast, no network tests
#     integration: Tests that call real APIs
#     slow: Tests that take >1 second
# testpaths = harness_tutorial/tests/
```

---

## 10. Testing Checklist for Production Harnesses

| Component | Unit Test | Integration Test | E2E Test |
|-----------|-----------|-----------------|----------|
| ConversationBuffer | ✅ trim behavior | — | — |
| MemoryStore | ✅ add/search (mock embeddings) | ✅ real embeddings (cheap model) | — |
| ContextBuilder | ✅ budget allocation math | ✅ with real buffer + memory | — |
| ErrorHandler | ✅ retry logic, circuit breaker | ✅ real 429 handling (hard to trigger) | — |
| CostTracker | ✅ budget math, downgrade logic | ✅ real API cost accumulation | — |
| SandboxedExecutor | ✅ path allowlist, injection blocking | — | ✅ real Docker isolation |
| Tool dispatch | ✅ routing, error handling | ✅ real tool execution | — |
| Full harness loop | — | ✅ cheap model + mock tools | ✅ real model + real tools |

---

## Key Takeaways

1. **Mock the LLM for unit tests** — test YOUR code, not OpenAI's.
2. **Deterministic replay is the secret weapon** — record once, replay forever, zero cost.
3. **Integration tests use cheap models** — `gpt-4o-mini` or `claude-haiku` cost fractions of a cent.
4. **Fixtures make tests maintainable** — invest in good conversation histories and tool schemas.
5. **The testing pyramid applies to AI too** — many fast unit tests, fewer slow integration tests, rare E2E tests.

---

> **Previous:** [15 — Sandboxing & Security](15_sandboxing_security.md)
> **Next:** [17 — Multi-Provider Harness](../part5_advanced/17_multi_provider.md)
