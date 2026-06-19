---
title: Tool Use
created: 2026-06-19
updated: 2026-06-19
type: concept
tags: [technique, concept]
sources:
  - raw/articles/ai-agent-landscape-2026.md
  - raw/articles/gpt4-technical-report.md
confidence: high
---

# Tool Use

## Definition
The capability of an LLM to invoke external tools — terminal commands, API calls, file operations, web searches, browser actions — as part of its reasoning and execution loop. Tool use is what distinguishes an [[ai-agents|AI agent]] from a chatbot.

## How It Works

1. **Model emits a tool call** — Instead of generating text, the model outputs a structured function call (typically JSON following OpenAI's function-calling format)
2. **Runtime executes the tool** — The agent platform runs the command/call and captures output
3. **Output is fed back** — Tool output is inserted into the model's context
4. **Model continues reasoning** — Using the tool output, the model decides the next action

This loop repeats until the task is complete.

## Common Tools

| Tool | What It Does | Example Agents |
|---|---|---|
| **Terminal** | Execute shell commands | All coding agents |
| **File I/O** | Read, write, edit files | All coding agents |
| **Web Search** | Search the internet | All agents |
| **Browser** | Navigate and interact with web pages | Manus, Hermes Agent |
| **API Calls** | Interact with external services | Hermes Agent |
| **Memory** | Store and recall persistent facts | Hermes Agent |
| **Subagents** | Delegate to parallel workers | Hermes Agent, Claude Code |

## Tool-Calling Protocols
OpenAI's function-calling format has become the de facto standard. Most model providers (Anthropic, Google, DeepSeek) support it, with minor variations. This convergence is reducing the integration burden across agent platforms.

## Security Considerations
Agents with terminal access are powerful and potentially dangerous. Mitigations:
- **Docker sandboxing** — Run commands inside containers (supported by Hermes Agent)
- **Tool allowlists** — Restrict which tools an agent can use
- **API key scoping** — Minimal permissions, short-lived tokens
- **User confirmation** — Require approval for destructive operations

The 2024–2025 period saw several high-profile agent vulnerabilities that drove the adoption of more conservative security defaults. ^[raw/articles/ai-agent-landscape-2026.md]

## Tool Use and Agent Quality
The quality of tool use varies significantly across models:
- **Strong:** Claude 4, GPT-5 — reliable multi-step tool chains, good error recovery
- **Adequate:** DeepSeek V3, Qwen 3 — correct most of the time but can struggle with complex chains
- **Weak:** Smaller/older models — frequent incorrect tool calls, poor recovery

This is one reason Karpathy recommends using frontier models for agent tasks and cheaper models for simpler queries.

## See Also
- [[ai-agents]] — the systems that use tools
- [[agentskills.io]] — the portable skills standard
- [[hermes-agent]] — agent with 30+ tool integrations
