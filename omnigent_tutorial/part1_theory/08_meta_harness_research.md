# Chapter 08: Stanford Meta-Harness — The Research

## What Problem Does It Solve?

Omnigent wraps harnesses at runtime. **Stanford Meta-Harness searches for the best harness code at design time.**

The insight: harness engineering is tedious, manual, and error-prone. What if an AI agent could search the space of possible harnesses and find the best one automatically?

## The Problem Statement

Given:
- A **fixed base model** M (weights frozen)
- A **task distribution** X (e.g., text classification, math reasoning, coding)
- A **harness class** H (Python code that manages context, memory, tool use)

Find:

```
H* = arg max_H  E[x~X, τ~p_M(H,x)] [r(τ, x)]
```

In English: find the harness H that maximizes expected reward r over tasks x.

The harness H is **executable code** — it controls what information the model sees, what gets stored in memory, how retrieval works, and how prompts are assembled.

## Why Is This Hard?

Traditional optimizers (like DSPy, TextGrad, OpenEvolve) search over prompt strings or limited templates. Meta-Harness searches over **executable Python code**. This is harder because:

1. **Stateful consequences** — A decision at step 2 (e.g., what to store in memory) affects performance at step 50
2. **Long-horizon failures** — A wrong retrieval decision cascades through the entire task
3. **Compressed feedback is insufficient** — A scalar score ("0/1") or summary ("model couldn't find the right info") doesn't tell you *why* step 2's storage decision was wrong

## The Core Innovation: Uncompressed History

Meta-Harness gives the proposer agent **full, uncompressed access to prior execution traces**:

```
┌─────────────────────────────────────────────┐
│           SEARCH HISTORY (Filesystem D)       │
│                                               │
│  candidate_001/                               │
│    harness.py        ← the actual code        │
│    score.json        ← {accuracy: 0.42}       │
│    traces/                                    │
│      task_01.json    ← FULL execution trace   │
│      task_02.json    ← every tool call,       │
│      ...              ← every model output,   │
│                       ← every memory state    │
│  candidate_002/                               │
│    harness.py                                 │
│    ...                                        │
└─────────────────────────────────────────────┘
                    │
                    │ proposer browses with grep, cat, ls
                    ▼
┌─────────────────────────────────────────────┐
│           PROPOSER AGENT (LLM)                │
│                                               │
│  1. Inspects prior failure traces             │
│  2. Identifies root cause:                    │
│     "Step 2 stored the wrong key —             │
│      it used 'topic' but the task needed       │
│      'entity_name'"                           │
│  3. Proposes new harness code with fix         │
└─────────────────────────────────────────────┘
```

**Ablation finding:** Providing only scores or human-written summaries resulted in *significantly lower* final performance. The agent's ability to selectively "deep-dive" into specific traces is what enables it to navigate the code-space search.

## The Optimization Loop

```
ITERATION 0:
  Seed: human-written baseline harness H0
  Evaluate H0 on search set → score s0, traces τ0
  Store to filesystem D: H0, s0, τ0

ITERATION 1:
  Proposer reads D (prior candidates, scores, traces)
  Proposer identifies failure modes in H0's traces
  Proposer writes H1 (patch: fix storage key)
  Evaluate H1 on search set → score s1, traces τ1
  Store to D: H1, s1, τ1

ITERATION 2:
  Proposer reads D (both H0 and H1 now visible)
  Proposer identifies new failure in H1
  Proposer writes H2 (patch: add deduplication)
  ...

After N iterations:
  Return best H* from D
```

### What the Proposer Sees

```python
# The proposer agent uses terminal tools to explore D:
$ ls candidate_003/traces/
task_01.json  task_02.json  ...  task_20.json

$ cat candidate_003/traces/task_07.json | head -100
{
  "task_id": "classify_07",
  "input": "The new policy was met with...",
  "harness_version": "candidate_003",
  "steps": [
    {
      "step": 1,
      "harness_action": "retrieve_memory(query='topic:politics')",
      "retrieved": []
    },
    {
      "step": 2,
      "harness_action": "store_memory(key='topic', value='politics')",
      "stored": true
    },
    ...
    {
      "step": 50,
      "model_output": "neutral",
      "correct_label": "negative",
      "reason": "earlier retrieval missed the relevant example"
    }
  ],
  "score": 0.0
}

# Proposer identifies: step 1 retrieved by 'topic' but needed 'entity_name'
# Proposer writes H4: fix retrieval key from 'topic' to 'entity_name'
```

## Experimental Results

### 1. Online Text Classification

**Setup:** Classify streaming text documents. Harness manages memory: which past examples to keep in context.

**Search:** 120B parameter open-source model as proposer.

**Results:**
- Meta-Harness-discovered strategies outperformed **Agentic Context Engineering (ACE)** (hand-engineered baseline)
- Harnesses **generalized to 9 unseen datasets**

**Discovered Strategy — "Label-Primed Query":**
1. Model first identifies the most likely label for a document
2. Then retrieves examples specifically matching that label
3. Uses those to confirm or revise the initial guess

```
Accuracy:  48.6% (Meta-Harness) vs 40.9% (ACE)
Context:   4× fewer tokens than ACE
```

**Additional discovery — Pareto frontier:**
The search naturally produced a range of harnesses trading accuracy vs. context cost, letting practitioners pick based on their budget.

### 2. Math Reasoning (IMO-Level)

**Setup:** Retrieval-augmented math reasoning. Harness manages a corpus of 500,000 examples.

**Results:**
- **+4.7 points** average improvement across **5 different held-out base models**
- Discovered harness: compact program routing queries to subject-specific retrieval policies based on problem text, with deduplication and difficulty-based reranking

### 3. Agentic Coding (TerminalBench 2.0)

**Setup:** Scaffold evolution for coding agents on TerminalBench 2.0.

**Results:**

| Model | Pass Rate | Leaderboard Rank |
|---|---|---|
| Claude Haiku 4.5 + Meta-Harness | **37.6%** | **#1** among Haiku-based agents |
| Claude Opus 4.6 + Meta-Harness | **76.4%** | **#2** overall |

**Key Discovery — "Environment Bootstrapping":**
- Proposer noticed agents wasted initial turns exploring the sandbox environment
- Solution: automatically snapshot the sandbox and inject environment info into the initial prompt
- Effect: saved 2-3 exploratory turns per task, improving success rates

## Why Code-Space Search Works

Meta-Harness searches over Python code, not prompt strings. This provides:

1. **Natural regularization** — Valid Python programs are coherent and algorithmic; random string mutations aren't
2. **Human readability** — Resulting harnesses are readable Python, not opaque embeddings
3. **Composability** — Harnesses can import each other, share utilities, be version-controlled
4. **Real-world deployability** — The output is a Python file you can `import` and run

## When Meta-Harness Is Promising

From the ONBOARDING.md:

| Property | Why it helps |
|---|---|
| **Long-horizon task** | Harness choices compound over many steps |
| **Repeated episodes** | Search needs many evaluation runs |
| **Fixed base model** | All gain comes from harness improvement |
| **Measurable success metric** | The optimizer needs a clear signal |
| **Recurring error patterns** | Something systematic for the proposer to fix |
| **Offline traces available** | Warm-start the search with existing data |
| **Meaningful held-out test set** | Verify generalization |

## When It's Not a Good Fit

- Most gain would come from changing the base model (fine-tuning, bigger model)
- No stable, repeatable evaluation loop
- One-off bespoke tasks (not enough search signal)
- Sub-second latency requirements (search takes time)

## Practical Details

### Cost

The paper used a 120B proposer model. Search took multiple iterations with 20-50 tasks evaluated per candidate. This is **research-scale compute**, not a quick script.

### Code Quality

The repo README is honest: *"This is a cleaned up version of the code we used for the paper. It has not been tested beyond verifying that it runs."*

### Reproducibility

```bash
# Text classification
cd reference_examples/text_classification
uv sync
uv run python meta_harness.py --iterations 1

# Terminal-Bench 2 (smoke test)
cd reference_examples/terminal_bench_2
uv sync
uv run bash scripts/run_eval.sh agents.baseline_kira:AgentHarness full 1 1 -i extract-elf
```

## Summary

Stanford Meta-Harness demonstrates that **harness optimization is automatable**. The key insight — giving the proposer full execution traces instead of compressed scores — enables an LLM to diagnose multi-step failures and fix harness code systematically.

The results are striking: +7.7 points on text classification, +4.7 on math reasoning, Top-2 on TerminalBench 2.0 — all without changing model weights.

The research points toward a future where "harness search" is as routine as hyperparameter tuning is today.

---

**Previous:** [Chapter 07 — Collaboration & Multi-Device](./07_collaboration_and_sharing.md)
**Next:** [Part 2 — Omnigent Examples (Notebooks)](../part2_omnigent_examples/example_01_hello_world.ipynb)
