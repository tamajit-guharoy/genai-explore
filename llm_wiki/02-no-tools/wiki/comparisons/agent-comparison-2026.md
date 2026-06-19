---
title: AI Agent Comparison — 2026
created: 2026-06-19
updated: 2026-06-19
type: comparison
tags: [comparison]
sources:
  - raw/articles/ai-agent-landscape-2026.md
  - raw/articles/gpt4-technical-report.md
  - raw/transcripts/karpathy-lex-fridman.md
confidence: medium
---

# AI Agent Comparison — Mid 2026

## What's Being Compared
Four major AI coding/automation agents as of June 2026. Purpose: help users choose the right agent for their workflow.

## Feature Matrix

| Feature | Claude Code | Codex | Hermes Agent | Manus |
|---|---|---|---|---|
| **Creator** | [[anthropic]] | [[openai]] | [[nous-research]] | Manus AI |
| **License** | Proprietary | Proprietary | Open-source (MIT) | Proprietary |
| **Hosting** | Managed | Managed | Self-hosted | Managed |
| **Price** | ~$20–200/mo (token-based) | ~$20–200/mo (token-based) | Free (bring your own API key) | ~$30/mo |
| **Terminal** | ✓ | ✓ | ✓ | Limited |
| **File Ops** | ✓ | ✓ | ✓ | Limited |
| **Web Search** | ✓ | ✓ | ✓ | ✓ |
| **Browser** | Limited | Limited | Limited | ✓ (primary) |
| **Memory** | Per-project | Per-session | **Cross-session** | None |
| **Skills** | Via agentskills.io | No | **Self-improving** | No |
| **Messaging** | No | No | **20+ platforms** | No |
| **Cron** | No | No | **Built-in** | No |
| **Subagents** | Via delegate | Limited | **Built-in** | No |
| **Model Providers** | Anthropic only | OpenAI only | **30+ providers** | Proprietary |
| **Voice** | No | No | Voice memo transcription | No |

## Strengths by Use Case

| Use Case | Best Agent | Why |
|---|---|---|
| Complex code reasoning | Claude Code | Deepest reasoning, best error recovery |
| GitHub workflow | Codex | Native GitHub + CI integration |
| Personal automation | Hermes Agent | Memory, cron, messaging gateway |
| Long-term knowledge work | Hermes Agent | Persistent memory, wiki-building skill |
| Web research / scraping | Manus | Browser-automation-first design |
| Budget-conscious | Hermes Agent | Free, use any model provider |
| Privacy-critical | Hermes Agent | Self-hosted, data never leaves your machine |

## Weaknesses

| Agent | Notable Weakness |
|---|---|
| Claude Code | Expensive per token; Anthropic-only models |
| Codex | Session-bound (no persistent memory); less transparent reasoning |
| Hermes Agent | Self-hosting overhead; model quality depends on your backend |
| Manus | Narrow scope (browser-first); less capable at code generation |

## Karpathy's Take
From Lex Fridman interview: ^[raw/transcripts/karpathy-lex-fridman.md]

- Uses **Claude Code** for heavy coding sessions
- Uses **Hermes Agent** for long-running personal automation and knowledge base maintenance
- Advocates a **portfolio approach** — different agents for different tasks, like using different programming languages

## Recommendation

| If You... | Try... |
|---|---|
| Write complex code daily, budget not an issue | Claude Code |
| Work heavily with GitHub, want polished UX | Codex |
| Want an agent that improves with use, care about privacy | Hermes Agent |
| Mostly do web research and data extraction | Manus |
| Want to experiment without spending money | Hermes Agent + free/cheap model |

## See Also
- [[ai-agents]] — the broader concept
- [[tool-use]] — the underlying capability
- [[llm-wiki-pattern]] — a use case well-suited to agents with memory
