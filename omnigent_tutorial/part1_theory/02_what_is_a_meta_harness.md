# Chapter 02: What Is a Meta-Harness?

## Definitions First

### Harness

A **harness** is the code around a model that decides:

- What context to include in each prompt
- What to store in memory across turns
- What to retrieve from external sources
- How to structure multi-step reasoning
- Which tools to make available and how to call them

Every AI agent has a harness, whether it's explicit (a Python class) or implicit (hardcoded logic in a CLI binary).

### Meta-Harness

A **meta-harness** operates one layer above. It wraps one or more harnesses in a common runtime that adds:

- **Orchestration** — dispatch tasks to different underlying agents, collect results
- **Governance** — enforce policies (spend caps, tool limits, approval gates) across all wrapped agents
- **Sandboxing** — isolate agents at the OS level, broker secrets
- **Collaboration** — share sessions, co-drive agents, synchronize across devices

## The Layer Cake

```
┌──────────────────────────────────────────────────┐
│                  HUMAN USER                       │
│         (terminal, web UI, mobile, desktop)        │
├──────────────────────────────────────────────────┤
│              META-HARNESS (Omnigent)               │
│                                                    │
│  Policies │ Sandbox │ Session │ Collaboration      │
│                                                    │
│  ┌──────────────┐ ┌──────────┐ ┌──────────────┐  │
│  │  Claude Code  │ │  Codex   │ │  Custom Agent │  │
│  │  (claude-sdk) │ │ (codex)  │ │  (your YAML)  │  │
│  └──────┬───────┘ └────┬─────┘ └──────┬───────┘  │
├─────────┼──────────────┼──────────────┼───────────┤
│         │              │              │            │
│    ┌────▼────┐    ┌────▼────┐   ┌─────▼─────┐     │
│    │ Claude  │    │  GPT    │   │  Gemini   │     │
│    │  API    │    │  API    │   │   API     │     │
│    └─────────┘    └─────────┘   └───────────┘     │
│                                                    │
│               MODEL PROVIDERS                      │
└──────────────────────────────────────────────────┘
```

### Key Insight: The Harness Is Stateful

A harness isn't just a prompt template. It maintains state across turns:

```python
class MyHarness:
    def __init__(self):
        self.memory = {}          # what to remember
        self.conversation = []    # message history
        self.tool_results = []    # prior tool outputs
        self.scratchpad = ""      # working notes

    def step(self, user_input):
        # 1. Retrieve relevant memory
        # 2. Build context (memory + history + scratchpad)
        # 3. Call model with tools
        # 4. Process tool calls
        # 5. Update memory, scratchpad
        # 6. Return response
        pass
```

A decision at step 2 ("should I store this fact in memory?") can cascade to affect performance at step 50. This is why harness optimization is hard, and why Stanford's Meta-Harness treats harness search as a *code-space* search problem.

## Two Flavors of Meta-Harness

### Runtime Meta-Harness (Omnigent)

**What it solves:** "I have five different agent CLIs and want them to work together under consistent rules."

**Key properties:**
- Wraps existing agent tools (Claude Code, Codex, Pi, Cursor)
- Adds governance, sandboxing, and collaboration as a layer above them
- Agents defined in YAML — swap without rewriting code
- You use it *to run* agents

### Optimization Meta-Harness (Stanford)

**What it solves:** "I have a fixed base model and want to find the best harness code for my task."

**Key properties:**
- Treats harness code as the search space
- Uses a proposer agent (LLM) that reads full execution traces
- Iteratively improves harness candidates
- You use it *to find* the best harness

## Why Not Just Use the Agent CLI Directly?

A fair question: if you already have Claude Code installed, why add Omnigent?

### Without a meta-harness:

```bash
# Terminal 1
claude "refactor the auth module"  # runs in isolation

# Terminal 2
codex exec "review the refactored auth"  # no shared context, no shared session

# Problem: How do you enforce that codex doesn't push before review?
# Problem: How do you cap spending across both?
# Problem: How do you share this with a teammate?
```

### With a meta-harness:

```bash
omni polly  # Polly orchestrates Claude Code as implementer,
            # Codex as reviewer, enforces policies,
            # runs in a sandbox, shareable via URL
```

The difference is that Omnigent adds **runtime governance** — the agents run inside a managed environment rather than as raw shell processes.

## The Harness Engineering Revolution

The 2026 research landscape shows a clear trend:

| Pre-2025 | 2025-2026 | Future |
|---|---|---|
| Manual prompt engineering | Harness engineering as a discipline | Automated harness optimization |
| Each agent in its own silo | Meta-harnesses for composition | Self-optimizing meta-harnesses |
| Model quality as primary differentiator | Harness quality as competitive moat | Harness search as standard practice |

The findings from the 2026 Harness Engineering report:

1. **Context management is the highest-leverage intervention.** Better context scaffolding improved results more than switching models, at lower cost.
2. **Models cannot reliably evaluate their own work.** Every experiment trying single-agent self-evaluation found systematic over-leniency. Solution: separate generation from evaluation (cross-vendor review).
3. **Harness complexity should increase incrementally.** Each increment in complexity was justified by observable failure modes, not anticipation.
4. **The harness is now a competitive moat.** LangChain's Top 30 → Top 5 jump on TerminalBench 2.0, model unchanged.
5. **Automated harness optimization is viable.** Stanford's Meta-Harness paper: a coding agent with full execution history access discovered harness improvements exceeding those from expert human engineers.

## Summary

- A **harness** is the control code around a model (context, memory, tools)
- A **meta-harness** wraps harnesses with orchestration, governance, sandboxing, and collaboration
- **Runtime meta-harnesses** (Omnigent) help you run agents together
- **Optimization meta-harnesses** (Stanford) help you find the best harness code
- The harness layer is now as important as the model layer for system performance

---

**Previous:** [Chapter 01 — Introduction](./01_introduction.md)
**Next:** [Chapter 03 — Omnigent Architecture](./03_omnigent_architecture.md)
