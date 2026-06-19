---
title: Anthropic
created: 2026-06-19
updated: 2026-06-19
type: entity
tags: [company]
sources:
  - raw/articles/ai-agent-landscape-2026.md
  - raw/articles/gpt4-technical-report.md
---

# Anthropic

## Overview
AI safety company founded in 2021 by former [[openai]] employees Dario Amodei and Daniela Amodei. Creator of the Claude model family and Claude Code agent. Known for a strong emphasis on AI safety and "Constitutional AI" alignment.

## Key Products

### Claude Models
- **Claude 3 series** (2024) — Haiku (fast), Sonnet (balanced), Opus (powerful)
- **Claude 4 series** (2025–2026) — Improved reasoning, longer context, stronger agentic behavior
- All models share a focus on safety, helpfulness, and honesty (the "HHH" framework)

### Claude Code
Anthropic's coding agent, deeply integrated with Claude models. Strengths:
- Exceptional reasoning on complex codebases
- Strong security posture with a "think before you act" philosophy
- VS Code extension and CLI available
- Supports the [[agentskills.io]] skills standard

Weakness: relatively expensive per-token compared to open-source alternatives. ^[raw/articles/ai-agent-landscape-2026.md]

## Approach to Alignment
Uses **Constitutional AI** — models are trained to follow a "constitution" of principles rather than relying solely on human feedback (RLHF, as [[openai]] does). This is designed to be more scalable and transparent than pure human-feedback approaches.

## Role in Agent Ecosystem
Claude Code is one of the two dominant proprietary coding agents (alongside Codex). It's preferred by users who prioritize reasoning depth, safety, and transparency over raw speed or price.

## Relationship to Other Entities
- Founded by ex-[[openai]] employees who left over safety concerns
- Competes with [[openai]] (Codex) and [[nous-research]] (Hermes Agent)
- [[andrej-karpathy]] has mentioned using Claude Code for "heavy coding sessions where I want the best reasoning" ^[raw/transcripts/karpathy-lex-fridman.md]

## See Also
- [[claude-code]] — detailed agent page
- [[openai]] — primary competitor
- [[constitutional-ai]] — alignment approach
- [[agent-comparison-2026]] — feature comparison
