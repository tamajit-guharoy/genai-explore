---
title: Andrej Karpathy
created: 2026-06-19
updated: 2026-06-19
type: entity
tags: [person]
sources:
  - raw/articles/karpathy-llm-wiki-tweet.md
  - raw/articles/ai-agent-landscape-2026.md
  - raw/transcripts/karpathy-lex-fridman.md
---

# Andrej Karpathy

## Overview
AI researcher and engineer. Former senior director of AI at Tesla (Autopilot), co-founder of [[openai]], and one of the most influential voices in applied AI. Known for his educational content (Zero to Hero series, CS231n) and for popularizing practical AI workflows.

## Key Contributions
- **CS231n** — Stanford's influential course on CNNs for visual recognition
- **Tesla Autopilot** — Led the AI/computer vision team for autonomous driving
- **Zero to Hero** — YouTube series teaching neural networks from scratch
- **[[llm-wiki-pattern]]** — Popularized the agent-built personal knowledge base approach (April 2026)
- **Auto-research loop** — Pattern for LLMs improving their own skills over time

## LLM Wiki Pattern
In April 2026, Karpathy described a shift in how he uses LLMs: spending tokens on "knowledge manipulation" rather than code generation. His [[llm-wiki-pattern]] uses an LLM agent to build and maintain a personal wiki of interlinked markdown files, growing one research topic to ~100 pages and ~400K words without writing a single word himself. ^[raw/articles/karpathy-llm-wiki-tweet.md]

## Views on AI Agents
From Lex Fridman interview (2026): ^[raw/transcripts/karpathy-lex-fridman.md]
- Uses **both managed and self-hosted agents** — Claude Code for heavy coding, Hermes Agent for personal automation
- Believes **persistent memory** is the key unlock for agents ("the agent that remembers you will always beat the one that doesn't")
- Expects a **portfolio approach** — different agents for different tasks, not one winner
- Supports the [[agentskills.io]] standard for portable agent skills

## Philosophy
- Strong advocate for **open-source AI** and educational accessibility
- Favors **practical leverage** over theoretical purity — "That's what machines are for"
- Believes **curation is the human's role** — we choose what goes in and verify important claims, but shouldn't do mechanical summarization

## See Also
- [[openai]] — co-founder, early employee
- [[llm-wiki-pattern]] — his knowledge management pattern
- [[ai-agents]] — the broader agent landscape he comments on
- [[nous-research]] — creator of Hermes Agent (which implements his wiki pattern as a skill)
