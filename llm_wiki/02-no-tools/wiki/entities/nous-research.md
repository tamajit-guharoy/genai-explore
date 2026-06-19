---
title: Nous Research
created: 2026-06-19
updated: 2026-06-19
type: entity
tags: [company, open-source]
sources:
  - raw/articles/ai-agent-landscape-2026.md
  - raw/transcripts/karpathy-lex-fridman.md
---

# Nous Research

## Overview
AI research company focused on open-source models and agent infrastructure. Based in the US. Tagline for their agent product: "the agent that grows with you."

## Key Products

### Hermes Models
Open-weight LLMs optimized for tool use and agentic behavior. The Hermes series is fine-tuned from base models (Llama, Qwen, DeepSeek) for instruction following, function calling, and structured output.

### Hermes Agent
Open-source, self-hosted autonomous AI agent platform. Key features:
- **Persistent memory** — SQLite + FTS5 with LLM summarization, survives across sessions
- **Self-improving skills** — Procedural knowledge captured as reusable documents, following the agentskills.io standard
- **Messaging gateway** — 20+ platforms: Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email
- **Built-in cron** — Scheduled unattended tasks (daily reports, backups, monitors)
- **30+ model providers** — Anthropic, OpenAI, OpenRouter, Gemini, Ollama, LM Studio, custom endpoints
- **Subagents** — Isolated parallel workers for large jobs
- **Cross-platform continuity** — Start on terminal, continue from Telegram

### Nous Portal
Hosted inference for Hermes models — a managed alternative to self-hosting.

## Role in the Agent Ecosystem
Hermes Agent is the leading open-source alternative to proprietary agents like [[claude-code]] and [[codex]]. Its differentiators are:
1. **Memory that compounds** — unlike session-bound agents, it remembers across sessions
2. **Skills that self-improve** — procedural knowledge that gets better with reuse
3. **Self-hosted, free forever** — no subscription, full data control

[[andrej-karpathy]] has mentioned using Hermes Agent for personal automation and knowledge base maintenance. ^[raw/transcripts/karpathy-lex-fridman.md]

## Relationship to LLM Wiki
Hermes Agent ships with an `llm-wiki` skill that implements Karpathy's [[llm-wiki-pattern]] directly — the agent can build and maintain a wiki following the same three-layer architecture Karpathy described. This makes Hermes one of the most natural platforms for running an LLM Wiki.

## See Also
- [[hermes-agent]] — detailed agent page
- [[ai-agents]] — broader agent landscape
- [[llm-wiki-pattern]] — the wiki pattern Hermes implements
- [[anthropic]] — creator of Claude Code (proprietary alternative)
- [[openai]] — creator of Codex (proprietary alternative)
