# Appendix C: Glossary

## Core Concepts

**Agent**
A prompt + tools + harness that performs tasks. In Omnigent, defined as a single YAML file. In Stanford Meta-Harness, the entity being optimized.

**Harness**
The control code around a model that decides what context to include, what to store in memory, when to retrieve, and how to structure multi-step reasoning. Also called "scaffold" or "agent framework."

**Meta-Harness**
A harness that wraps other harnesses. Provides orchestration, governance, sandboxing, and collaboration as a layer above individual agent CLIs.

**Orchestrator**
An agent that dispatches work to sub-agents rather than doing it itself. Example: Polly decomposes tasks, delegates to Claude Code/Codex/Pi, and reviews results.

**Sub-agent**
An agent launched by an orchestrator to perform a specific task. Runs in its own session with its own context, tools, and (optionally) sandbox.

**Session**
A single conversation between a user and an agent. In Omnigent, sessions are persistent (stored in SQLite), shareable (via URL), and cross-device (same session on terminal, web, mobile).

## Omnigent-Specific Terms

**Omnibox**
Omnigent's OS-level sandbox system. Provides filesystem and network isolation using bubblewrap (Linux), seatbelt (macOS), or cloud sandboxes (Modal/Daytona/Islo).

**Policy**
A declarative guardrail that returns ALLOW, DENY, or ASK for agent actions. Evaluated at three levels: session, agent, and server.

**Guardrail**
Runner-level enforcement that operates before the policy engine. Used for catastrophic-operation prevention (blast radius) and dispatch bounding.

**Runner**
The execution environment for a single agent. Wraps the harness adapter, enforces policies, and manages the sandbox.

**Server**
The persistent backend (default: `localhost:6767`) that stores sessions, enforces server-wide policies, serves the web UI, and handles collaboration.

**Harness Adapter**
The translation layer between Omnigent's internal protocol and a specific agent backend (e.g., `claude-sdk` adapter talks to Anthropic's Python SDK).

**Polly**
Omnigent's built-in multi-agent coding orchestrator. Decomposes tasks, delegates to Claude Code/Codex/Pi in parallel worktrees, enforces cross-vendor review.

**Debby**
Omnigent's built-in two-headed brainstorming agent. Fans every question to both Claude and GPT, presents both perspectives, and (with `/debate`) has them critique each other.

**Secret Brokering**
Omnigent's mechanism for hiding credentials from agents: secrets are injected at the network egress point only when an approved operation needs them, never visible in the agent's environment.

**Blast Radius Policy**
A guardrail that always denies catastrophic operations (`rm -rf /`, `git push --force`, fork bombs) and optionally asks for approval on pushes/merges.

## Stanford Meta-Harness Terms

**Proposer Agent**
The LLM-based coding agent that reads prior harness code and execution traces, then proposes new harness candidates.

**Search History (D)**
The filesystem containing all prior harness candidates, their scores, and their full execution traces. The proposer browses this with `grep`, `cat`, `ls`.

**Uncompressed Trace**
A complete, verbatim record of every step in a harness evaluation: every tool call, model output, memory state change. The key innovation of Stanford Meta-Harness — contrast with compressed feedback (scalar scores, summaries).

**Harness Candidate (H)**
One proposed implementation of the harness interface. Evaluated on a subset of tasks, scored, and stored in the search history.

**Label-Primed Query**
A harness strategy discovered by Meta-Harness: first do a quick classification to guess the label, then retrieve examples matching that label, then confirm or revise. Achieved 48.6% accuracy vs. 40.9% baseline.

**Environment Bootstrapping**
A harness strategy discovered by Meta-Harness: snapshot the sandbox environment before the agent starts, inject it into the initial prompt, saving 2-3 exploratory turns.

**Structured Observation**
A harness strategy: parse tool outputs into structured summaries instead of raw text, reducing context usage by ~35%.

**Error Recovery Hints**
A harness strategy: after tool failures, inject context-specific hints suggesting common fixes, improving recovery rate by ~15%.

## Cross-Cutting Terms

**Harness Engineering**
The discipline of designing, testing, and optimizing the control code around AI models. Recognized in 2026 as a distinct engineering practice, separate from prompt engineering or fine-tuning.

**Cross-Vendor Review**
The pattern of having one vendor's agent review another vendor's agent's work. Example: Claude Code implements, Codex reviews. Key to catching vendor-specific blindspots.

**Worktree**
A `git worktree` — an isolated checkout of a repository where a sub-agent can work without interfering with the main checkout or other sub-agents.

**Inbox-Driven Wake**
The pattern where an orchestrator dispatches sub-agents, then sleeps until the sub-agent completes (notification via inbox). Contrast with polling (`while not done: check()`).

**Context Scaffolding**
The structure around a model's prompt: what goes before the user message, what comes after, how history is included, how tool results are formatted.

**Policy Composition**
The stacking of multiple policies, evaluated in declaration order. A DENY from any policy short-circuits all subsequent evaluations.

## Abbreviations

| Abbreviation | Meaning |
|---|---|
| **YAML** | Yet Another Markup Language — Omnigent's agent definition format |
| **MCP** | Model Context Protocol — Anthropic's standard for tool servers |
| **PTY** | Pseudo-terminal — used for interactive CLI harnesses (tmux) |
| **SDK** | Software Development Kit — programmatic harnesses (Python) |
| **FTS5** | Full-Text Search (SQLite) — used for session search |
| **TUI** | Terminal User Interface — Omnigent's modern terminal mode |
| **SSO** | Single Sign-On — team server authentication |
