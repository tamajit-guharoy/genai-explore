---
title: OpenAI
created: 2026-06-19
updated: 2026-06-19
type: entity
tags: [company]
sources:
  - raw/articles/ai-agent-landscape-2026.md
  - raw/articles/gpt4-technical-report.md
---

# OpenAI

## Overview
AI research and deployment company. Creator of the GPT model series (GPT-1 through GPT-5) and the Codex coding agent. Mission: "ensure that artificial general intelligence benefits all of humanity."

## Key Products

### GPT Models
- **GPT-3.5** (2022) — First widely deployed instruction-tuned LLM; basis for initial ChatGPT
- **GPT-4** (2023) — Multimodal (text + images), human-level on many professional benchmarks. Bar exam: 90th percentile. Architecture: decoder-only Transformer with RLHF post-training. ^[raw/articles/gpt4-technical-report.md]
- **GPT-5** (2025) — Increased reasoning depth, longer context, stronger agentic capabilities

### Codex
OpenAI's coding agent, launched 2025. Integrates with GitHub and VS Code. Strengths: fast execution, deep GitHub integration (PRs, issues, CI), large model family. Weaker on transparency of reasoning compared to [[claude-code]].

### ChatGPT
Consumer-facing chat interface. The product that brought LLMs to mainstream awareness (100M+ users in 2 months, 2023).

## Approach to Alignment
Uses RLHF (Reinforcement Learning from Human Feedback) for post-training alignment. This differs from [[anthropic]]'s Constitutional AI approach. OpenAI has been criticized for reducing transparency over time (e.g., not disclosing GPT-4 parameter count, limiting technical detail in reports).

## Role in Agent Ecosystem
Codex is one of the two dominant proprietary agents (alongside [[claude-code]]). OpenAI's function-calling format has become a de facto standard for tool-use APIs across the industry.

## Relationship to Other Entities
- [[andrej-karpathy]] was a co-founder (left in 2017, later returned briefly)
- [[anthropic]] was founded by former OpenAI employees (Dario Amodei, Daniela Amodei) over safety concerns
- [[nous-research]] represents the open-source alternative to OpenAI's closed approach

## See Also
- [[codex]] — OpenAI's agent product
- [[gpt-4]] — technical details
- [[transformer-architecture]] — the architecture behind GPT
- [[anthropic]] — primary competitor
