# Appendix A: Omnigent vs. Meta-Harness — Side-by-Side Comparison

## At a Glance

| Dimension | Omnigent | Stanford Meta-Harness |
|---|---|---|
| **What it is** | Runtime meta-harness framework | Research framework for harness optimization |
| **Layer** | Runtime — runs agents | Design-time — finds best harness code |
| **Core problem** | "I have 5 agent CLIs and want them to work together" | "I have a fixed model and want the best harness for my task" |
| **Input** | Agent YAML definitions | Task distribution + base model + harness interface |
| **Output** | Running agent sessions | Optimized harness code (Python file) |
| **Who builds it** | Databricks AI + Neon | Stanford IRIS Lab (Yoonho Lee et al.) |
| **License** | Apache 2.0 | Code available, paper on arXiv |
| **Status** | Alpha (actively developed) | Research release (cleaned paper code) |
| **GitHub stars** | ~4,100 | ~1,100 |
| **Python** | 3.12+ | Not specified (uv-based) |

## Detailed Comparison

### Purpose

**Omnigent** is for **running** agents. You use it when:
- You juggle multiple agent CLIs (Claude Code, Codex, Pi, Cursor)
- You want consistent policies across all agents
- You need sandboxing and secret brokering
- You want collaboration (shared sessions, co-driving)
- You're building a team workflow around AI agents

**Stanford Meta-Harness** is for **designing** agents. You use it when:
- You have a fixed base model and want to maximize its performance
- You have a repetitive task with a measurable success metric
- You suspect harness improvements would help more than prompt tweaking
- You're doing ML research on agent architectures
- You want to discover harness strategies you wouldn't think of manually

### Architecture

```
OMNIGENT:                          STANFORD META-HARNESS:

┌──────────────┐                   ┌───────────────────┐
│   SERVER     │                   │  SEARCH LOOP       │
│  (policies,  │                   │                    │
│   sessions,  │                   │  Proposer → Files  │
│   sharing)   │                   │  Evaluate → Score  │
└──────┬───────┘                   │  Repeat N times    │
       │                           └───────────────────┘
┌──────▼───────┐
│   RUNNER     │                   Unlike Omnigent, Meta-Harness
│  (harness    │                   doesn't run agents for users —
│   adapter,   │                   it finds the best harness,
│   sandbox)   │                   then you deploy it.
└──────────────┘
```

### Harness Model

| Aspect | Omnigent | Stanford Meta-Harness |
|---|---|---|
| Harness = | The agent CLI wrapper (claude-sdk, codex, etc.) | Python code around a model (context, memory, retrieval) |
| Harness selection | User picks from dropdown (or YAML `executor.harness`) | Proposer writes Python code from scratch |
| Harness change | One-line YAML edit | Proposer generates entirely new implementations |
| Multiple harnesses | Yes — simultaneous (Polly: Claude + Codex + Pi) | No — searches for one optimal harness |

### Agents

| Aspect | Omnigent | Stanford Meta-Harness |
|---|---|---|
| Agent definition | YAML file (prompt, harness, tools, policies) | Python class (harness interface implementation) |
| Agent creation | Human authors YAML (or agent builds agent) | Proposer LLM generates Python |
| Agent composition | Orchestrator + sub-agents (hierarchical) | Single harness (no sub-agents in search) |
| Agent scope | Any task (coding, research, data, chat) | Domain-specific (text, math, coding — paper domains) |

### Policies & Governance

| Aspect | Omnigent | Stanford Meta-Harness |
|---|---|---|
| Policies? | Yes — core feature | No — research framework, not a runtime |
| Three levels | Session → Agent → Server | N/A |
| Built-in policies | Spend cap, tool limit, shell approval, skill block, sandbox enforce, service-specific | N/A |
| Custom policies | Yes — Python modules | N/A |
| Policy enforcement | Runtime (every tool call checked) | N/A — it's an optimizer, not an executor |

### Sandboxing

| Aspect | Omnigent | Stanford Meta-Harness |
|---|---|---|
| Sandboxing? | Yes — Omnibox, core feature | Yes — but only for evaluation (TerminalBench sandbox) |
| Backends | bubblewrap (Linux), seatbelt (macOS), Modal/Daytona/Islo (cloud) | Docker or local (varies by experiment) |
| Secret brokering | Yes — egress proxy injection | No — not a runtime |
| Config | Per-agent: write_paths, read_paths, allow_network | Per-evaluation: whatever sandbox the task needs |

### Collaboration

| Aspect | Omnigent | Stanford Meta-Harness |
|---|---|---|
| Session sharing | Yes — shareable URLs, roles | No |
| Co-driving | Yes — multiple users steering one agent | No |
| Comments | Yes — inline on generated files | No |
| Forks | Yes — clone a session | No |
| Cross-device | Yes — terminal, web, mobile, desktop | No |
| Team server | Yes — SSO, managed hosts | No |

### Model Support

| Aspect | Omnigent | Stanford Meta-Harness |
|---|---|---|
| Models supported | 30+ providers (Anthropic, OpenAI, Gemini, OpenRouter, Ollama, etc.) | Any (proposer uses Claude Code by default; base model is experiment-specific) |
| Model switching | Mid-session via `/model` or CLI flag | N/A — proposer model is fixed; base model is the optimization target |
| Multi-model | Yes — different sub-agents can use different models | No — searches for one harness around one base model |

## When to Use Which

### Use Omnigent when...

- You need to **run** agents today
- You have multiple agent tools and want a common layer
- You want governance (spend caps, approval gates, sandboxing)
- You collaborate with teammates on agent sessions
- You want your agents to work together (orchestration)

### Use Stanford Meta-Harness when...

- You have a **fixed model** and want to maximize its performance
- You have a **repetitive, measurable task** with clear success criteria
- You're willing to invest **compute budget** in harness search
- You're doing **ML research** on agent architectures
- You want to **discover** harness strategies rather than design them

### Use Both when...

- You use Omnigent to run agents
- You identify a bottleneck task that's harness-dominated
- You use Meta-Harness to find a better harness for that task
- You deploy the optimized harness back into Omnigent

```
┌──────────────────────────────────────┐
│  1. Run agents with Omnigent          │
│     ↓                                 │
│  2. Identify harness bottleneck       │
│     ↓                                 │
│  3. Search with Meta-Harness          │
│     ↓                                 │
│  4. Deploy optimized harness          │
│     back into Omnigent                │
└──────────────────────────────────────┘
```

## Summary Table

| | Omnigent | Stanford Meta-Harness |
|---|---|---|
| **Type** | Runtime framework | Research optimizer |
| **User** | Developer, team lead | ML researcher, engineer |
| **Maturity** | Alpha product | Research code |
| **Install** | `uv tool install omnigent` | `git clone` + `uv sync` |
| **Learning curve** | Moderate (YAML + concepts) | Steep (ML research + harness design) |
| **Time to value** | Minutes (install, setup, run) | Days to weeks (domain setup, search, analysis) |
| **Maintenance** | Active (533+ commits, frequent releases) | Minimal (paper artifact, not actively developed) |

---

**Back to:** [Part 3 — Stanford Meta-Harness](../part3_meta_harness/12_onboarding_new_domain.md)
**Next:** [Appendix B — Reference Tables](./B_reference_tables.md)
