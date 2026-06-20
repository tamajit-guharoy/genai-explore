# Omnigent & Meta-Harness — In-Depth Tutorial

> **A comprehensive guide to AI agent meta-harness frameworks: Omnigent (runtime orchestration) and Stanford Meta-Harness (harness optimization research).**
>
> Written: June 2026 | Tested against: Omnigent v0.x (alpha), Meta-Harness (arXiv 2603.28052)

---

## What This Tutorial Covers

This tutorial covers **two distinct but related concepts** in AI agent engineering:

| Tool | What it is | Layer |
|---|---|---|
| **Omnigent** | Open-source meta-harness framework for running AI agents | Runtime — orchestration, sandboxing, policies, collaboration |
| **Meta-Harness** (Stanford IRIS Lab) | Research framework for automated *search* over harness code | Optimization — finds the best harness for a given model/task |

The word "meta-harness" appears in both because Omnigent *is* a meta-harness (a harness that wraps other harnesses), while Stanford's Meta-Harness *optimizes* harnesses. This tutorial covers both in depth, with a dedicated comparison chapter.

---

## Prerequisites

- Python 3.12+ and `uv` (for Omnigent)
- Node.js 22 LTS and npm (for Claude Code / Codex harnesses)
- Basic familiarity with YAML and Python
- Agent coding experience helpful but not required

---

## Tutorial Structure

### Part 1: Theory (Markdown)
Read these chapters in order for conceptual understanding.

| # | Chapter | Description |
|---|---|---|
| 01 | [Introduction](./part1_theory/01_introduction.md) | What is a meta-harness, and why does it matter? |
| 02 | [What Is a Meta-Harness?](./part1_theory/02_what_is_a_meta_harness.md) | Deep dive: harness vs. meta-harness, the layer cake |
| 03 | [Omnigent Architecture](./part1_theory/03_omnigent_architecture.md) | Runner, server, policies, sessions — how it all fits |
| 04 | [Agent YAML Specification](./part1_theory/04_agent_yaml_spec.md) | Complete reference for defining agents in YAML |
| 05 | [Policies & Governance](./part1_theory/05_policies_and_governance.md) | Declarative guardrails: spend caps, tool limits, approval gates |
| 06 | [Sandbox & Security Model](./part1_theory/06_sandbox_and_security.md) | Omnibox OS sandboxing, secret brokering, trust model |
| 07 | [Collaboration & Multi-Device](./part1_theory/07_collaboration_and_sharing.md) | Shared sessions, co-driving, cross-platform continuity |
| 08 | [Stanford Meta-Harness: The Research](./part1_theory/08_meta_harness_research.md) | How automated harness search works |

### Part 2: Omnigent Examples (Jupyter Notebooks)
Hands-on, runnable examples. Open in VS Code, JupyterLab, or any .ipynb viewer.

| # | Notebook | What you'll do |
|---|---|---|
| Example 01 | [Hello, Omnigent](./part2_omnigent_examples/example_01_hello_world.ipynb) | Install, setup, launch first agent |
| Example 02 | [Custom Agents](./part2_omnigent_examples/example_02_custom_agent.ipynb) | Write your own agent YAML from scratch |
| Example 03 | [Policies in Practice](./part2_omnigent_examples/example_03_policies.ipynb) | Configure spend caps, tool limits, approval gates |
| Example 04 | [Multi-Agent Orchestration](./part2_omnigent_examples/example_04_multi_agent.ipynb) | Build Polly-style orchestrators with sub-agents |
| Example 05 | [Sandboxing & Security](./part2_omnigent_examples/example_05_sandbox.ipynb) | Configure OS sandboxes, restrict filesystem/network |

### Part 3: Stanford Meta-Harness (Markdown + Code)
Theory and walkthroughs for harness optimization research.

| # | Chapter | Description |
|---|---|---|
| 09 | [Harness Optimization Theory](./part3_meta_harness/09_harness_optimization_theory.md) | Problem formulation, search loop, uncompressed history |
| 10 | [Text Classification Walkthrough](./part3_meta_harness/10_text_classification_walkthrough.md) | Step-by-step through the reference experiment |
| 11 | [TerminalBench 2.0 Walkthrough](./part3_meta_harness/11_terminalbench_walkthrough.md) | Scaffold evolution for agentic coding |
| 12 | [Onboarding a New Domain](./part3_meta_harness/12_onboarding_new_domain.md) | How to apply Meta-Harness to your own task |

### Part 4: Appendix

| # | File | Description |
|---|---|---|
| A | [Omnigent vs. Meta-Harness Comparison](./part4_appendix/A_omnigent_vs_meta_harness.md) | Side-by-side: when to use which |
| B | [Reference Tables](./part4_appendix/B_reference_tables.md) | All harnesses, policies, config knobs at a glance |
| C | [Glossary](./part4_appendix/C_glossary.md) | Terms defined |

---

## Quick Start

```bash
# Install Omnigent
uv tool install omnigent

# Verify
omni --version

# Launch your first agent (walks you through model setup)
omni

# Or read the theory first — start with Part 1, Chapter 01
cat part1_theory/01_introduction.md
```

---

## Environment Notes

This tutorial was written and tested on Windows (WSL/git-bash) with:
- Python 3.12.6, uv 0.6.7
- Node.js 22.12.0, npm 11.6

**Omnigent on Windows:** The installer works via `uv tool install`. tmux is not available on native Windows — the `omnigent claude` / `omnigent codex` wrappers won't launch interactive terminals, but programmatic harnesses (claude-sdk, openai-agents) and the web UI work fine. For full functionality, use WSL2 or a Linux/macOS host.

**Stanford Meta-Harness:** Requires a 120B+ parameter open-source model for the proposer agent. The reference experiments use Claude Code as proposer. These are **research code**, not a polished product — expect to adapt.

---

## Sources

- [Omnigent — GitHub (omnigent-ai/omnigent)](https://github.com/omnigent-ai/omnigent)
- [Omnigent — Official Docs](https://omnigent.ai/docs)
- [Stanford Meta-Harness — GitHub](https://github.com/stanford-iris-lab/meta-harness)
- [Meta-Harness Paper — arXiv 2603.28052](https://arxiv.org/abs/2603.28052)
- [Harness Engineering for AI Agents — Research Review & Roadmap 2026](https://www.adaptivereasoning.ai/research/pdf/Harness%20Engineering.pdf)
