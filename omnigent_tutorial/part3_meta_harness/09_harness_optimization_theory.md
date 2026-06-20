# Chapter 09: Harness Optimization Theory

## The Problem: Harness Engineering is Manual

Most AI engineering effort goes into prompt tuning, model selection, and tool wiring. But the **harness** — the control code that decides what context to build, what to store in memory, when to retrieve, and how to assemble prompts — is often treated as an afterthought.

Research shows this is backwards. The 2026 Harness Engineering review found that **harness quality is the primary differentiator** between AI systems using similar base models. LangChain jumped from Top 30 to Top 5 on TerminalBench 2.0 with pure harness changes — same model.

The question Stanford's Meta-Harness asks: **can we automate harness improvement?**

## Formal Problem Definition

Given:
- A **frozen base model** M (weights never change)
- A **task distribution** X (e.g., classify 1,000 streaming documents)
- A **harness class** H (executable Python code with a defined interface)
- A **reward function** r(τ, x) that scores a trajectory τ on task x

Find:
```
H* = arg max_H  E[x~X, τ~p_M(H,x)] [r(τ, x)]
```

### What Makes This Hard

Unlike prompt optimization (searching over strings), harness optimization searches over **executable code**. Harnesses are stateful:

```python
class Harness:
    def process(self, task):
        # Step 1: Retrieve relevant memory
        memory = self._retrieve(task.query)
        # Step 2: Build context for model
        context = self._assemble(task, memory)
        # Step 3: Call model
        output = self._call_model(context)
        # Step 4: Update memory for future
        self._store(task, output)
        return output
```

A suboptimal choice at Step 2 (e.g., including too much or too little memory) cascades into errors at later steps — and those errors may only surface 50 steps later.

**Compressed feedback fails:** A scalar score ("0.42 accuracy") or a summary ("model couldn't find relevant examples") doesn't tell you *which* memory retrieval decision was wrong.

## The Core Innovation: Uncompressed Search History

Meta-Harness gives the proposer agent **a full, browsable filesystem** of prior harness candidates, their scores, and their **complete execution traces**:

```
search_history/
├── candidate_001/
│   ├── harness.py           # The actual harness code
│   ├── score.json           # {accuracy: 0.42, latency_ms: 340, cost_usd: 0.03}
│   └── traces/
│       ├── task_001.json    # FULL trace: every step, every tool call,
│       ├── task_002.json    # every model output, every memory state change
│       └── ...
├── candidate_002/
│   └── ...
└── ...
```

The proposer uses `grep`, `cat`, `ls` to explore this filesystem. When it finds a failure pattern, it can trace it to the exact line of harness code that caused it.

### Why Full Traces Beat Summaries

From the paper:

> "A failure at step 50 of a task might be caused by a suboptimal storage decision at step 2. A scalar score ('0/1') or a high-level summary ('model failed to find information') is insufficient to diagnose that the specific data point was never stored in the harness's state."

**Ablation confirmation:** Providing only scores or human-written summaries resulted in *significantly lower* final performance. The agent's ability to "deep-dive" into specific traces is what enables effective search.

## The Optimization Loop

```
Initialize:
  D ← {H₀, s₀, τ₀}          # seed harness + its score + traces

For iteration 1..N:
  1. Proposer reads D        # browses filesystem: grep, cat, ls
  2. Proposer analyzes failures
     - Finds: step 2 stored wrong key
     - Finds: retrieval missed edge case X
     - Finds: context exceeded limit on long tasks
  3. Proposer writes H_new   # generates new harness code
  4. Evaluate H_new on X_train → s_new, τ_new
  5. D ← D ∪ {H_new, s_new, τ_new}

Return: best H in D by held-out score
```

### What the Proposer Actually Does

```python
# Proposer explores:
$ grep -r "retrieve" candidate_*/harness.py
candidate_001/harness.py:  results = self.retrieve(query=task.topic)
candidate_003/harness.py:  results = self.retrieve(query=task.entity_name)

# Compares traces:
$ cat candidate_001/traces/task_007.json | jq '.steps[1]'
{
  "action": "retrieve(query='politics')",
  "result": [],
  "error": null
}
# ...50 steps later...
{
  "final_output": "neutral",
  "correct_label": "negative",
  "score": 0
}

$ cat candidate_003/traces/task_007.json | jq '.steps[1]'
{
  "action": "retrieve(query='NewPolicy')",
  "result": [similar_example_1, similar_example_2],
  "error": null
}
# ...50 steps later...
{
  "final_output": "negative",
  "correct_label": "negative",
  "score": 1
}

# Proposer learns: retrieval_key='topic' bad, retrieval_key='entity_name' good
```

## Why Code-Space Search?

Searching over Python code (rather than prompt strings or model weights) has unique advantages:

| Property | Why it matters |
|---|---|
| **Natural regularization** | Valid Python programs are coherent and algorithmic; random mutations usually produce syntax errors, not subtle bugs |
| **Human readability** | Results are readable Python — inspectable, debuggable, version-controllable |
| **Composability** | Harnesses can import shared utilities, reducing search space |
| **Deployability** | Output is a `.py` file — `import` and run, no special runtime |
| **Algorithmic bias** | LLM proposers naturally produce structured, named-variable, function-based code |

## When Meta-Harness Works

From the ONBOARDING.md — properties that make a domain a good fit:

| Property | Signal strength |
|---|---|
| Long-horizon or multi-step tasks | Strong — harness choices compound |
| Repeated tasks or episodes | Strong — needs many evaluation runs |
| Fixed base model | Required — all gain must come from harness |
| Measurable success metric | Required — optimizer needs a clear signal |
| Recurring error patterns | Strong — something systematic to fix |
| Offline traces available | Moderate — warm-starts search |
| Meaningful held-out test set | Strong — verifies generalization |

### Poor Fit

- Most gain would come from model improvement (fine-tuning, scaling)
- No stable, repeatable evaluation loop
- One-off bespoke tasks (not enough search signal)
- Sub-second latency requirements (search takes time)

## Practical Considerations

### Cost

- Proposer: 120B parameter model (in the paper)
- 20-50 evaluation tasks per candidate
- N iterations (10-50 in paper experiments)
- **Research-scale** — not a quick `pip install && run` script

### Code Maturity

The repo README states:

> "This is a cleaned up version of the code we used for the paper. It has not been tested beyond verifying that it runs. Please let us know if anything goes wrong."

This is research code. Expect to adapt it for your domain.

### Proposer Flexibility

The reference examples use Claude Code as proposer, wrapped via `claude_wrapper.py`. You can swap to any coding agent by adapting the wrapper — the framework only needs a proposer that can read files and write harness code.

## Summary

Stanford Meta-Harness shows that **harness optimization is automatable**. The key insight: give a coding agent full execution traces (not compressed summaries) and it can diagnose multi-step failures and improve harness code systematically.

The results — +7.7 points on text classification, +4.7 on math reasoning, Top-2 on TerminalBench 2.0 — demonstrate that automated harness search can outperform expert human engineering, without touching model weights.

---

**Previous:** [Chapter 08 — Stanford Meta-Harness: The Research](../part1_theory/08_meta_harness_research.md)
**Next:** [Chapter 10 — Text Classification Walkthrough](./10_text_classification_walkthrough.md)
