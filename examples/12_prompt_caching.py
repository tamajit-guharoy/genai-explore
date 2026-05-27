#!/usr/bin/env python3
"""
Example 12: Prompt caching with the Anthropic API.

Demonstrates how to use prompt caching to reduce costs and latency:
  1. A long system prompt with cache_control breakpoints
  2. First request: creates the cache (cache_creation_input_tokens > 0)
  3. Second request: reads from the cache (cache_read_input_tokens > 0)
  4. Cache on user messages (large document in first turn)
  5. Cost savings calculation

Prompt caching is ideal for:
  - Large system prompts shared across many conversations
  - Reference documents that are consulted repeatedly
  - Few-shot examples that don't change between requests
"""

import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()

import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def print_header(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}")


def estimate_cost(usage: anthropic.types.Usage, label: str) -> dict:
    """
    Estimate cost based on Anthropic's Claude pricing (approximate).
    Sonnet 4: $3/M input tokens, $15/M output tokens.
    Cached input: $0.30/M tokens (90% discount on input).
    """
    input_cost_per_m = 3.00
    output_cost_per_m = 15.00
    cached_input_cost_per_m = 0.30  # 90% discount

    input_tokens = usage.input_tokens
    output_tokens = usage.output_tokens
    cache_creation = getattr(usage, "cache_creation_input_tokens", 0)
    cache_read = getattr(usage, "cache_read_input_tokens", 0)

    # Of the input tokens, some are cache creation and some are regular
    # The first input tokens may be cache creation, rest are regular
    # We'll do a simple estimate
    cost = (
        max(0, input_tokens - cache_creation - cache_read)
        / 1_000_000
        * input_cost_per_m
        + cache_creation / 1_000_000 * input_cost_per_m
        + cache_read / 1_000_000 * cached_input_cost_per_m
        + output_tokens / 1_000_000 * output_cost_per_m
    )

    print(f"  [{label}] Cost estimate: ${cost:.6f}")
    print(f"           Input: {input_tokens}, Output: {output_tokens}, "
          f"Cache creation: {cache_creation}, Cache read: {cache_read}")

    return {
        "cost": cost,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cache_creation": cache_creation,
        "cache_read": cache_read,
    }


# ---------------------------------------------------------------------------
# Build a large system prompt (long enough to trigger caching)
# ---------------------------------------------------------------------------
def build_large_system_prompt() -> str:
    """Create a system prompt large enough to benefit from caching (>1024 tokens)."""
    sections = [
        "You are an expert software architect and code reviewer.",
    ]

    # Add many rules to make the prompt long
    rules = []
    for i in range(1, 31):
        rules.append(
            f"{i}. Always follow best practices for {['security', 'performance', "
            f"'readability', 'testing', 'documentation', 'maintainability', "
            f"'scalability', 'error handling'][i % 8]}."
        )
    sections.append("\n".join(rules))

    sections.append(
        "\nWhen reviewing code, check for:\n"
        "- Proper error handling and edge cases\n"
        "- Memory leaks and resource management\n"
        "- Thread safety and concurrency issues\n"
        "- API design and backwards compatibility\n"
        "- Test coverage and quality\n"
        "- Documentation completeness\n"
        "- Performance bottlenecks\n"
        "- Security vulnerabilities including injection attacks\n"
        "- Authentication and authorization checks\n"
        "- Data validation and sanitization\n"
        "- Logging and monitoring\n"
        "- Configuration management\n"
        "- Dependency management\n"
        "- Build and deployment considerations\n"
        "- Compliance with coding standards\n"
    )

    sections.append(
        "\nCode style guidelines:\n"
        "- Follow PEP 8 for Python code\n"
        "- Use type hints for all function signatures\n"
        "- Write docstrings for all public APIs\n"
        "- Keep functions focused and under 50 lines\n"
        "- Use meaningful variable names\n"
        "- Avoid deep nesting (max 3 levels)\n"
        "- Prefer composition over inheritance\n"
        "- Use immutable data structures where possible\n"
        "- Write pure functions when feasible\n"
        "- Handle all exceptions explicitly\n"
    )

    sections.append(
        "\nArchitecture principles:\n"
        "- Follow SOLID principles\n"
        "- Use dependency injection\n"
        "- Separate concerns into layers\n"
        "- Design for testability\n"
        "- Favor loose coupling\n"
        "- Use interfaces/abstract base classes\n"
        "- Apply the single responsibility principle\n"
        "- Keep the codebase modular\n"
        "- Document architectural decisions\n"
        "- Plan for extensibility\n"
    )

    # Add repetitive text to ensure we exceed the caching threshold
    sections.append("\n" + "\n".join(
        f"Important reminder {j}: Always think carefully before writing code."
        for j in range(20)
    ))

    return "\n\n".join(sections)


# ===================================================================
def main() -> None:
    """Run the prompt caching demonstration."""
    print_header("PROMPT CACHING DEMONSTRATION")
    print(f"Model: {MODEL}")
    print()

    system_prompt = build_large_system_prompt()
    system_len = len(system_prompt)
    print(f"System prompt size: {system_len} characters "
          f"(~{system_len // 4} estimated tokens)")
    print()

    # ------------------------------------------------------------------
    # Part 1: First request -- creates the cache
    # ------------------------------------------------------------------
    print_header("PART 1: First request (cache creation)")

    message_1 = (
        "Briefly explain what a REST API is and its key principles. "
        "Keep it to 2-3 sentences."
    )

    response_1 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": message_1}],
    )

    print(f"Response 1: {response_1.content[0].text[:200]}...")
    usage_1 = response_1.usage
    cost_1 = estimate_cost(usage_1, "Request 1")

    if getattr(usage_1, "cache_creation_input_tokens", 0) > 0:
        print("\n  ** Cache was CREATED on this request. **")
    else:
        print("\n  Note: cache_creation_input_tokens = 0. "
              "The prompt may not be long enough.")
        print("  (This can happen if the API version doesn't report this field.)")

    # ------------------------------------------------------------------
    # Part 2: Second request -- reads from cache
    # ------------------------------------------------------------------
    print_header("PART 2: Second request (cache read)")

    message_2 = (
        "What are the differences between SQL and NoSQL databases? "
        "Keep it to 2-3 sentences."
    )

    response_2 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": message_2}],
    )

    print(f"Response 2: {response_2.content[0].text[:200]}...")
    usage_2 = response_2.usage
    cost_2 = estimate_cost(usage_2, "Request 2")

    if getattr(usage_2, "cache_read_input_tokens", 0) > 0:
        print("\n  ** Cache was READ on this request. **")
    else:
        print("\n  Note: cache_read_input_tokens = 0. "
              "Cache may have expired or not been created.")

    # ------------------------------------------------------------------
    # Part 3: Cost savings
    # ------------------------------------------------------------------
    print_header("PART 3: COST SAVINGS CALCULATION")

    total_without_caching = cost_1["cost"] + cost_2["cost"]
    # Recompute cost_2 as if cache_read was regular input
    cost_2_without_cache = (
        cost_2["input_tokens"] / 1_000_000 * 3.00
        + cost_2["output_tokens"] / 1_000_000 * 15.00
    )
    total_with_caching = cost_1["cost"] + cost_2_without_cache
    savings = cost_2_without_cache - cost_2["cost"]

    print(f"Request 1 cost:  ${cost_1['cost']:.6f}")
    print(f"Request 2 cost:  ${cost_2['cost']:.6f}")
    print(f"Total cost:      ${total_with_caching:.6f}")
    print(f"Saved on req 2:  ${savings:.6f} ({(savings / max(cost_2_without_cache, 0.0001)) * 100:.1f}%)")
    print()

    # ------------------------------------------------------------------
    # Part 4: Caching on user messages (large document)
    # ------------------------------------------------------------------
    print_header("PART 4: Caching on user messages (large document)")

    large_document = "\n".join(
        f"This is paragraph {i} of a very long reference document that Claude "
        f"needs to analyze. It contains various data points and information "
        f"that is important for answering user questions accurately."
        for i in range(50)
    )

    print(f"Large document size: {len(large_document)} chars "
          f"(~{len(large_document) // 4} estimated tokens)\n")

    # First turn: document + short question
    response_3 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system="You are a helpful assistant.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": large_document,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": "What is the main topic of this document? "
                                "Answer in one sentence.",
                    },
                ],
            }
        ],
    )

    usage_3 = response_3.usage
    print(f"Response 3: {response_3.content[0].text[:200]}...")
    cost_3 = estimate_cost(usage_3, "Request 3 (with doc cache)")

    if getattr(usage_3, "cache_creation_input_tokens", 0) > 0:
        print("  ** Document cache was CREATED. **")

    # Second turn: same document cached, different question
    response_4 = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system="You are a helpful assistant.",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": large_document,
                        "cache_control": {"type": "ephemeral"},
                    },
                    {
                        "type": "text",
                        "text": "Summarize this document in 2-3 sentences.",
                    },
                ],
            }
        ],
    )

    usage_4 = response_4.usage
    print(f"Response 4: {response_4.content[0].text[:200]}...")
    cost_4 = estimate_cost(usage_4, "Request 4 (cache read)")

    if getattr(usage_4, "cache_read_input_tokens", 0) > 0:
        print("  ** Document cache was READ. **")

    print_header("DEMONSTRATION COMPLETE")
    print("Prompt caching reduces costs by ~90% on cached input tokens.")
    print("Use cache_control on system prompts, messages, or content blocks.")
    print("Cache TTL is 5 minutes with an 'ephemeral' duration.")


if __name__ == "__main__":
    main()
