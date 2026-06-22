# Appendix D: Glossary

> Every term used in this tutorial, defined in 2-4 sentences with chapter cross-references.

---

## A

### Agent / AI Agent
An autonomous system that uses an LLM to reason about tasks, call tools, and produce results. The agent runs inside a **harness** that manages the conversation loop, tool execution, and state. *See: [Chapter 1: What is a Harness?](../part1_foundations/01_what_is_a_harness.md)*

### Agentic Loop
The core control flow of an agent harness: (1) send messages to the LLM, (2) receive response, (3) if the response contains tool calls, execute them and feed results back, (4) repeat until the LLM produces a final text response. The loop is bounded by a **turn limit** to prevent infinite execution. *See: [Chapter 2: The Agentic Loop](../part1_foundations/02_agentic_loop.md)*

### ALLOW / ASK / DENY
The three gate decisions in a **human-in-the-loop** policy engine. ALLOW executes immediately, ASK prompts the user for approval, DENY blocks execution entirely. *See: [Chapter 19: Human-in-the-Loop](../part5_advanced/19_human_in_the_loop.md)*

### Anthropic Messages API
Anthropic's stateless API for sending conversation messages to Claude models. Uses `system` as a top-level parameter (not a message), supports native **tool calling** via `tool_use` content blocks, and provides a `stream` context manager for token-by-token output. *See: [Chapter 17: Multi-Provider Abstraction](../part5_advanced/17_multi_provider_abstraction.md), [Appendix B](B_provider_api_cheatsheet.md)*

---

## C

### ChromaDB
An open-source vector database used for **long-term memory** in agent harnesses. Stores text as embeddings (vectors) and retrieves them via cosine similarity search. Runs embedded (no server needed) with persistent storage to disk. *See: [Chapter 15: Long-Term Memory with ChromaDB](../part3_memory/15_chromadb_memory.md)*

### Circuit Breaker
A fault-tolerance pattern that prevents cascading failures. After N consecutive errors, the breaker "opens" and rejects all requests immediately. After a timeout, it enters "half-open" to test if the service has recovered. *See: [Chapter 23: Full Build — Production Harness](../part6_real_world/23_full_build_production_harness.md)*

### Context Isolation
The practice of giving each **sub-agent** a fresh, independent context window — no shared message history, no cross-contamination of tool results. Only the sub-agent's final answer returns to the parent orchestrator. *See: [Chapter 18: Sub-Agent Orchestration](../part5_advanced/18_sub_agent_orchestration.md)*

### Context Window
The maximum number of tokens an LLM can process in a single request. Current limits: Claude 200K, GPT-4o 128K, Gemini 2.0 1M+. Messages exceeding the window must be trimmed or summarized. *See: [Chapter 12: Context Window Management](../part4_production/12_context_management.md)*

### Conversation Buffer
A sliding-window data structure that keeps the most recent N messages (or tokens) in the **context window**, dropping older messages to stay within limits. System messages are always preserved. *See: [Chapter 12: Context Window Management](../part4_production/12_context_management.md)*

### Cost Tracking
Recording the estimated dollar cost of every LLM call (input tokens × $/token + output tokens × $/token) and enforcing a per-session **budget**. Prevents runaway spending in autonomous agent loops. *See: [Chapter 19: Human-in-the-Loop](../part5_advanced/19_human_in_the_loop.md)*

---

## E

### Embedding
A numerical vector (typically 768–3072 dimensions) that represents the semantic meaning of text. Used in **RAG** and **long-term memory** to find text with similar meaning via vector similarity (cosine, dot product). *See: [Chapter 15: Long-Term Memory with ChromaDB](../part3_memory/15_chromadb_memory.md)*

---

## G

### Gemini (Google)
Google's LLM family, accessed via the `google-generativeai` Python SDK. Uses `generateContent` with a flat `contents` array, maps roles to "user" and "model", and wraps tools in a `functionDeclarations` container. *See: [Chapter 17: Multi-Provider Abstraction](../part5_advanced/17_multi_provider_abstraction.md)*

---

## H

### Harness
The software layer that wraps an LLM and manages the full lifecycle of an AI agent: the **agentic loop**, tool registration and dispatch, error handling, cost tracking, session persistence, and policy enforcement. The harness is to an AI agent what a web framework is to a web application. *See: [Chapter 1: What is a Harness?](../part1_foundations/01_what_is_a_harness.md)*

### Human-in-the-Loop (HITL)
A governance pattern where certain agent actions require explicit human approval before execution. Implemented via a **policy engine** with **ALLOW/ASK/DENY** gates, typically applied at high-risk or high-cost operations. *See: [Chapter 19: Human-in-the-Loop](../part5_advanced/19_human_in_the_loop.md)*

---

## L

### Long-Term Memory
Persistent storage of conversation history and user context outside the **context window**, typically using a **vector database** like ChromaDB. Retrieved via semantic search when relevant to the current conversation. *See: [Chapter 15: Long-Term Memory with ChromaDB](../part3_memory/15_chromadb_memory.md)*

---

## M

### Multi-Provider Abstraction
A design pattern where a single **LLMProvider** abstract base class defines the interface (`chat()`, `stream()`, `count_tokens()`), and per-provider adapters (Anthropic, OpenAI, Gemini, OpenRouter) implement it. The harness code never imports provider-specific SDKs directly. *See: [Chapter 17: Multi-Provider Abstraction](../part5_advanced/17_multi_provider_abstraction.md)*

---

## O

### Omnigent
An open-source agent orchestration platform by Nous Research that provides a uniform interface (**Agent Protocol**) over multiple AI agent backends (Claude SDK, Claude Native, Codex, Cursor, etc.) with built-in policy enforcement, sandboxing, and sub-agent orchestration. *See: [Chapter 22: Architecture Deep-Dive — Omnigent Adapters](../part6_real_world/22_architecture_omnigent_adapters.md)*

### OpenAI Chat Completions API
OpenAI's API for chat-based LLM interactions. Uses a `messages` array where system messages are included inline, expects `max_completion_tokens`, and wraps tools in `{"type": "function", "function": {...}}` format. *See: [Chapter 17: Multi-Provider Abstraction](../part5_advanced/17_multi_provider_abstraction.md)*

### OpenRouter
An API gateway that provides a single OpenAI-compatible endpoint to access 200+ models from different providers. Uses the same SDK as OpenAI but with a different base URL and model names like `"anthropic/claude-sonnet-4-20250514"`. *See: [Chapter 17: Multi-Provider Abstraction](../part5_advanced/17_multi_provider_abstraction.md)*

### Orchestration / Orchestrator
The pattern of using a "manager" agent to decompose complex tasks, delegate them to specialized **sub-agents**, and synthesize their results. The orchestrator itself is an agent that treats sub-agents as tools. *See: [Chapter 18: Sub-Agent Orchestration](../part5_advanced/18_sub_agent_orchestration.md)*

---

## P

### Persistent Sessions
The ability to save an agent's entire conversation state (messages, tool registrations, cost, model) to disk and resume it later — even on a different machine. Typically implemented with **SQLite** for simplicity. *See: [Chapter 20: Persistent Sessions](../part5_advanced/20_persistent_sessions.md)*

### Pi (pi.ai)
Inflection AI's emotionally intelligent AI agent. Pi's harness uniquely combines **multi-model routing** (different models for conversation vs. reasoning vs. tool use), emotional context tracking, and conversational tool result narration. *See: [Chapter 21: Architecture Deep-Dive — Pi](../part6_real_world/21_architecture_pi.md)*

### Policy Engine
A chain of declarative rules evaluated against every tool call. Rules can check cost budgets, tool allowlists/blocklists, approval requirements, and turn limits. The first non-ALLOW result (ASK or DENY) wins. *See: [Chapter 19: Human-in-the-Loop](../part5_advanced/19_human_in_the_loop.md)*

### Prompt Injection
A security vulnerability where user-provided text contains instructions that override or manipulate the system prompt. Mitigations include: separating system instructions from user content, input sanitization, and policy-based tool restrictions. *See: [Chapter 11: Security Best Practices](../part4_production/11_security.md)*

### PTY (Pseudo-Terminal)
A virtual terminal device used to wrap CLI-based AI agents (like Claude Code or Codex CLI) so Omnigent can send prompts and capture output programmatically. PTY adapters are fragile compared to SDK adapters but work with any text-based CLI tool. *See: [Chapter 22: Architecture Deep-Dive — Omnigent Adapters](../part6_real_world/22_architecture_omnigent_adapters.md)*

---

## R

### RAG (Retrieval-Augmented Generation)
A technique where relevant documents are retrieved from a **vector database** and injected into the LLM's context before generation. Combines the LLM's reasoning with external knowledge without fine-tuning. *See: [Chapter 15: Long-Term Memory with ChromaDB](../part3_memory/15_chromadb_memory.md)*

### Retry with Exponential Backoff
An error-handling strategy where failed API calls are retried with increasing delays (1s, 2s, 4s, 8s...). Only applied to transient errors (rate limits, timeouts, connection failures), not to permanent errors (auth, validation). Often combined with a **circuit breaker**. *See: [Chapter 23: Full Build — Production Harness](../part6_real_world/23_full_build_production_harness.md)*

---

## S

### Sandbox
An isolated execution environment that restricts what an AI agent can do — typically using Docker, Firecracker, macOS Seatbelt, or Linux bubblewrap. Prevents agents from accessing the host filesystem, network, or system resources. *See: [Chapter 14: Sandboxing & Execution](../part4_production/14_sandboxing.md)*

### Session Store
A persistence layer (typically SQLite) that saves and loads agent conversation state: messages, tool definitions, system prompt, model, token usage, and cost. Enables **persistent sessions** and crash recovery. *See: [Chapter 20: Persistent Sessions](../part5_advanced/20_persistent_sessions.md)*

### Streaming
Sending tokens from the LLM to the user one at a time as they're generated, rather than waiting for the complete response. Improves perceived latency and enables real-time UI updates. Requires buffering for **tool calls** (which arrive as deltas). *See: [Chapter 8: Streaming Responses](../part2_tools/08_streaming.md)*

### Sub-Agent
A self-contained mini-agent that runs as a tool within a larger **orchestrator**. Each sub-agent has its own system prompt, tool set, and **context isolation** — only its final answer returns to the parent. *See: [Chapter 18: Sub-Agent Orchestration](../part5_advanced/18_sub_agent_orchestration.md)*

### System Prompt
The initial instruction given to the LLM that defines its role, behavior, constraints, and personality. Some APIs (Anthropic) treat it as a special top-level parameter; others (OpenAI) include it as a `role="system"` message. *See: [Chapter 1: What is a Harness?](../part1_foundations/01_what_is_a_harness.md)*

---

## T

### Three-Level Governance
Omnigent's policy model with three cascading levels: **session policies** (set by the user), **agent policies** (set by the developer), and **server policies** (set by the system administrator). The effective policy is the intersection (most restrictive combination) of all three. *See: [Chapter 19: Human-in-the-Loop](../part5_advanced/19_human_in_the_loop.md)*

### tiktoken
OpenAI's open-source tokenizer library. Used for **token counting** in OpenAI models (`tiktoken.encoding_for_model("gpt-4o")`). Different models use different encodings (cl100k_base for GPT-4/3.5, o200k_base for GPT-4o). *See: [Appendix B: Provider API Cheat Sheet](B_provider_api_cheatsheet.md)*

### Token
The fundamental unit of text that LLMs process — roughly 0.75 words in English. Both input (prompt) and output (completion) are measured in tokens. Pricing is per 1,000 or 1,000,000 tokens. Token limits constrain the **context window**. *See: [Chapter 12: Context Window Management](../part4_production/12_context_management.md)*

### Tool Calling
The mechanism by which an LLM requests to execute an external function. The model returns a structured object (tool name + parameters) instead of plain text. The harness executes the requested function and feeds the result back into the conversation. Also called "function calling" by OpenAI. *See: [Chapter 4: Your First Tool](../part2_tools/04_first_tool.md)*

### Tool Definition / Tool Schema
A JSON Schema object that describes a tool's interface: its name, description, and the parameters it accepts (with types, descriptions, and which are required). Provider formats differ — Anthropic uses `input_schema`, OpenAI uses `function.parameters`, Gemini uses `functionDeclarations`. *See: [Appendix C: Tool Schema Reference](C_tool_schema_reference.md)*

### Turn
One iteration of the **agentic loop**: model call → response → (optional) tool execution → tool results fed back. A session may have 1–50 turns. The **turn limit** is a safety mechanism to prevent infinite loops. *See: [Chapter 2: The Agentic Loop](../part1_foundations/02_agentic_loop.md)*

---

## V

### Vector Database
A database optimized for storing and querying high-dimensional vectors (**embeddings**). Used for semantic search — finding text with similar meaning, not just keyword matches. ChromaDB, Pinecone, Weaviate, and Milvus are common choices. *See: [Chapter 15: Long-Term Memory with ChromaDB](../part3_memory/15_chromadb_memory.md)*

---

> **See also:** The full tutorial table of contents for chapter-by-chapter deep dives into each concept.
