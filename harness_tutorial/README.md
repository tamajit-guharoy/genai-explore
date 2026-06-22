# Harness Engineering — The Complete Guide to Building AI Agent Harnesses in Python

> **"The harness is now a competitive moat."** — Harness Engineering for AI Agents, Research Review 2026
>
> A comprehensive, code-heavy tutorial on building AI agent harnesses from scratch — from a 15-line model caller to a 500-line production-grade agent runtime.
>
> Written: June 2026 | Tested against: Anthropic SDK, OpenAI SDK, Gemini SDK, ChromaDB

---

## What This Tutorial Covers

Every AI agent has a **harness** — the control code around the model that manages context, calls tools, handles errors, and orchestrates work. A great harness on a mid-tier model can outperform a naive harness on a frontier model.

This tutorial teaches you to build harnesses from the ground up: why each component exists, when to add it, and exactly how to write it — with runnable Python on every page.

| Part | Chapters | What You'll Build |
|---|---|---|
| **1. Fundamentals** | 01–04 | A model caller → multi-turn conversation → personality system |
| **2. Tool Calling** | 05–08 | Tool definitions → single-step tools → full agentic loop → streaming |
| **3. Memory & Context** | 09–11 | Conversation buffers → vector memory (ChromaDB) → context assembly |
| **4. Production Hardening** | 12–16 | Retries + circuit breakers → logging → cost tracking → sandboxing → testing |
| **5. Advanced Patterns** | 17–20 | Multi-provider abstraction → sub-agent orchestration → human-in-the-loop → persistence |
| **6. Real-World Architectures** | 21–23 | Pi deep-dive → Omnigent adapters → full production harness build |
| **Appendices** | A–D | Minimal harness (single file) → provider cheatsheet → tool schema reference → glossary |

---

## How to Use This Tutorial

**Sequential read (recommended):** Each chapter builds on the previous one. Start at [Chapter 01](part1_fundamentals/01_what_is_a_harness.md) and work forward. By Chapter 23, you'll have written every component of a production harness.

**Jump in:** Each chapter is self-contained with its own "What You'll Learn" section. If you already know the basics, jump to [Chapter 07 — The Agentic Loop](part2_tool_calling/07_the_agentic_loop.md) for the core algorithm, or [Chapter 23 — Full Build](part6_real_world/23_full_build_production_harness.md) for the complete production class.

**Copy-paste:** Every code block is runnable. Install the dependencies (`pip install anthropic openai chromadb tiktoken structlog`) and paste the code into a `.py` file.

---

## Prerequisites

- **Python 3.10+** — type hints, structural pattern matching, asyncio
- **An API key** for at least one provider (Anthropic, OpenAI, or Gemini)
- **Basic familiarity** with LLM APIs and HTTP requests
- **pip installs:** `anthropic`, `openai`, `google-generativeai`, `chromadb`, `tiktoken`, `structlog`, `opentelemetry-api`

---

## Tutorial Structure

### Part 1: Fundamentals

| # | Chapter | Lines | What You'll Learn |
|---|---|---|---|
| 01 | [What Is a Harness?](part1_fundamentals/01_what_is_a_harness.md) | ~160 | The agent layer cake, harness anatomy, why harness quality > model quality |
| 02 | [The Simplest Possible Harness](part1_fundamentals/02_simplest_harness.md) | ~175 | ~15 lines of Python — call model, return response |
| 03 | [Adding Conversation History](part1_fundamentals/03_conversation_history.md) | ~285 | Multi-turn message management, role alternation |
| 04 | [System Prompts & Personality](part1_fundamentals/04_system_prompts_personality.md) | ~370 | Prompt templating, swappable personalities |

### Part 2: Tool Calling

| # | Chapter | Lines | What You'll Learn |
|---|---|---|---|
| 05 | [Tool Calling: The Big Idea](part2_tool_calling/05_tool_calling_big_idea.md) | ~245 | JSON schema + function dispatch, across providers |
| 06 | [Single-Step Tool Use](part2_tool_calling/06_single_step_tool_use.md) | ~375 | Define, register, parse, execute a tool |
| 07 | [The Agentic Loop](part2_tool_calling/07_the_agentic_loop.md) | ~610 | **THE critical chapter.** The full loop: input → model → tool → repeat |
| 08 | [Streaming Tool Calls](part2_tool_calling/08_streaming_tool_calls.md) | ~495 | Streaming with tool-use buffering, UX considerations |

### Part 3: Memory & Context

| # | Chapter | Lines | What You'll Learn |
|---|---|---|---|
| 09 | [Short-Term Memory](part3_memory_context/09_short_term_memory.md) | ~410 | `ConversationBuffer`, token counting, trimming strategies |
| 10 | [Long-Term Memory](part3_memory_context/10_long_term_memory.md) | ~465 | ChromaDB vector store, embedding + retrieval, summarization |
| 11 | [Context Window Management](part3_memory_context/11_context_window_management.md) | ~495 | Hybrid assembly: recent + summary + RAG, budget allocation |

### Part 4: Production Hardening

| # | Chapter | Lines | What You'll Learn |
|---|---|---|---|
| 12 | [Error Handling & Retries](part4_production/12_error_handling_retries.md) | ~495 | Exponential backoff + jitter, circuit breaker, graceful degradation |
| 13 | [Logging & Observability](part4_production/13_logging_observability.md) | ~570 | Structured JSON logging, OpenTelemetry, tool-call chain visualizer |
| 14 | [Cost Tracking & Budgets](part4_production/14_cost_tracking_budgets.md) | ~475 | Per-session cost, hard/soft caps, model-tier auto-downgrade |
| 15 | [Sandboxing & Security](part4_production/15_sandboxing_security.md) | ~655 | `SandboxedExecutor`, path allowlists, secret brokering, Docker isolation |
| 16 | [Testing Harnesses](part4_production/16_testing_harnesses.md) | ~695 | Unit tests, mocked LLMs, integration tests, deterministic replay |

### Part 5: Advanced Patterns

| # | Chapter | Lines | What You'll Learn |
|---|---|---|---|
| 17 | [Multi-Provider Abstraction](part5_advanced/17_multi_provider_abstraction.md) | ~1,100 | `LLMProvider` ABC, adapters for Anthropic/OpenAI/Gemini/OpenRouter |
| 18 | [Sub-Agent Orchestration](part5_advanced/18_sub_agent_orchestration.md) | ~700 | Orchestrator-worker pattern, parallel execution, context isolation |
| 19 | [Human-in-the-Loop](part5_advanced/19_human_in_the_loop.md) | ~700 | ALLOW/ASK/DENY gates, `PolicyEngine`, three-level governance |
| 20 | [Persistent Sessions](part5_advanced/20_persistent_sessions.md) | ~700 | SQLite-backed `SessionStore`, save/load/resume, cross-device export |

### Part 6: Real-World Architectures

| # | Chapter | Lines | What You'll Learn |
|---|---|---|---|
| 21 | [Architecture: Pi Agent](part6_real_world/21_architecture_pi.md) | ~550 | Pi's multi-model routing, emotional context, conversational tool narration |
| 22 | [Architecture: Omnigent Adapters](part6_real_world/22_architecture_omnigent_adapters.md) | ~750 | Agent Protocol, Claude SDK adapter, native CLI adapter, policy pipeline |
| 23 | [Full Build: Production Harness](part6_real_world/23_full_build_production_harness.md) | ~1,250 | **CAPSTONE.** Complete ~500-line `Harness` class combining everything |

### Appendices

| # | File | Lines | What It Is |
|---|---|---|---|
| A | [Minimal Harness](appendix/A_minimal_harness.py) | ~80 | Self-contained 30-line harness, single `pip install`, copy-paste ready |
| B | [Provider API Cheatsheet](appendix/B_provider_api_cheatsheet.md) | ~200 | Anthropic vs OpenAI vs Gemini — auth, request/response, tools, streaming |
| C | [Tool Schema Reference](appendix/C_tool_schema_reference.md) | ~250 | `ToolSchemaTranslator` class, field-by-field mapping, 6 common gotchas |
| D | [Glossary](appendix/D_glossary.md) | ~350 | 30+ terms defined with chapter cross-references |

---

## Key Themes Across the Tutorial

**1. The harness is as important as the model.**
LangChain jumped from Top 30 to Top 5 on TerminalBench 2.0 without changing its model — only its harness improved. Every chapter reinforces this.

**2. Progressive complexity.**
Chapter 02's 15-line script grows organically through 23 chapters into a 500-line production harness. You understand every line because you watched it get added.

**3. Analogies everywhere.**
Technical concepts are mapped to everyday objects: harness = car chassis, the agentic loop = a manager delegating to specialists, context management = packing a suitcase with limited space.

**4. 50/50 theory-to-code.**
Every concept is explained in prose first, then demonstrated in commented Python. No code appears without explanation; no concept is described without code.

**5. Provider-agnostic.**
While examples use Anthropic SDK by default, Chapters 17 and Appendices B-C provide complete multi-provider support including OpenAI, Gemini, and OpenRouter.

---

## Quick Start

```bash
# Install dependencies
pip install anthropic openai google-generativeai chromadb tiktoken structlog

# Set your API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Read from the beginning
cat part1_fundamentals/01_what_is_a_harness.md

# Or jump to the capstone
cat part6_real_world/23_full_build_production_harness.md

# Or grab the minimal harness and run it
python appendix/A_minimal_harness.py
```

---

## Environment Notes

This tutorial was written and tested on Windows (git-bash/MSYS2) with:
- Python 3.12.6
- anthropic 0.45+
- openai 1.60+
- chromadb 0.5+
- tiktoken 0.7+

All code uses POSIX-compatible patterns that work on Linux, macOS, and Windows (via WSL/git-bash).

---

## Sources

- [Anthropic Messages API Documentation](https://docs.anthropic.com/en/api/messages)
- [OpenAI Chat Completions Documentation](https://platform.openai.com/docs/api-reference/chat)
- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Stanford Meta-Harness Paper — arXiv 2603.28052](https://arxiv.org/abs/2603.28052)
- [Harness Engineering for AI Agents — Research Review 2026](https://www.adaptivereasoning.ai/research/pdf/Harness%20Engineering.pdf)
- [Pi Agent — inflection.ai](https://pi.ai)
- [Omnigent — GitHub (omnigent-ai/omnigent)](https://github.com/omnigent-ai/omnigent)
- [ChromaDB Documentation](https://docs.trychroma.com/)

---

**Total:** 27 files, ~13,100 lines of markdown + Python, covering every aspect of harness engineering from first principles to production deployment.
