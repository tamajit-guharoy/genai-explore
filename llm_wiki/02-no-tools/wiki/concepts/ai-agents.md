---
title: AI Agents
created: 2026-06-19
updated: 2026-06-19
type: concept
tags: [concept, technique]
sources:
  - raw/articles/ai-agent-landscape-2026.md
  - raw/transcripts/karpathy-lex-fridman.md
confidence: high
---

# AI Agents

## Definition
An AI agent is an LLM-powered system that can use tools, maintain state, and take multi-step actions autonomously to achieve a goal. Unlike chatbots (single-turn Q&A without tools), agents plan, execute, observe results, and adapt.

## Core Capabilities

| Capability | Description |
|---|---|
| **Tool use** | Invoke external tools: terminal, browser, API calls, file operations |
| **Memory** | Maintain state across turns within a session; increasingly across sessions |
| **Planning** | Break complex tasks into steps, execute sequentially with branching |
| **Self-correction** | Observe tool output, detect errors, retry with adjusted approach |
| **Delegation** | Spawn sub-agents for parallel workstreams |

## Major Agents (Mid-2026)

| Agent | Creator | Type | Key Differentiator |
|---|---|---|---|
| [[claude-code]] | [[anthropic]] | Proprietary CLI | Deep reasoning, security-first posture |
| [[codex]] | [[openai]] | Proprietary CLI/Desktop | GitHub integration, fast execution |
| [[hermes-agent]] | [[nous-research]] | Open-source | Persistent memory, self-improving skills |
| Manus | Manus AI | Proprietary | Browser automation focus |

## The Memory Question
[[andrej-karpathy]] frames this as the critical differentiator for agents: ^[raw/transcripts/karpathy-lex-fridman.md]

> "The thing most people don't appreciate about current AI is how stateless it is. Every conversation starts from zero. The model doesn't remember you."

Most agents (Claude Code, Codex) are session-bound. [[hermes-agent]] is the notable exception with persistent, cross-session memory. Karpathy's view: "The agent that remembers you will always beat the one that doesn't."

## Portfolio Approach
Karpathy advocates using multiple agents — not betting on one winner:
- **Claude Code** for heavy coding sessions needing best reasoning
- **Hermes Agent** for long-running personal automation, scheduled tasks, knowledge base maintenance

This is analogous to using different programming languages for different jobs.

## The Skills Standard
The [[agentskills.io]] open standard enables portable skills across agent platforms. Both [[hermes-agent]] and [[claude-code]] support it, reducing lock-in and enabling skill sharing.

## Open Questions
- Will agents converge on a common tool-calling protocol, or will fragmentation continue?
- Can persistent memory be done well enough that agents become genuine long-term collaborators?
- Will open-source agents (Hermes) keep pace with well-funded proprietary ones (Claude, Codex)?

## See Also
- [[tool-use]] — the underlying capability
- [[agent-comparison-2026]] — detailed feature matrix
- [[llm-wiki-pattern]] — using agents to build knowledge bases
