# Chapter 10: Text Classification Walkthrough

## The Domain: Online Text Classification

**Task:** Classify streaming text documents into categories (sentiment, topic, etc.). Documents arrive one at a time. The harness must decide what to keep in memory from past documents to help classify future ones.

**Why this is a harness problem:** The model is fixed. Performance depends entirely on **memory management** — which past examples to store, when to retrieve them, and how to use them in context.

## The Harness Interface

Every candidate harness must implement:

```python
class ClassificationHarness:
    def __init__(self, model, max_memory_size=100):
        self.model = model
        self.memory = []          # stored examples
        self.max_memory = max_memory_size

    def classify(self, document: str) -> str:
        """
        Given a document, return a class label.
        May use self.memory to retrieve relevant past examples.
        Updates self.memory after classification.
        """
        raise NotImplementedError
```

## Baseline (Human-Written)

The baseline harness stores every document with its label and retrieves the most recent K:

```python
class BaselineHarness(ClassificationHarness):
    def classify(self, document):
        # Retrieve: last 5 examples (simple recency)
        recent = self.memory[-5:] if self.memory else []

        # Build context
        context = f"Recent examples:\n"
        for ex in recent:
            context += f"  Text: {ex['text'][:100]}... → {ex['label']}\n"
        context += f"\nClassify: {document[:200]}"

        # Call model
        label = self.model.classify(context)

        # Store this example
        self.memory.append({"text": document, "label": label})
        if len(self.memory) > self.max_memory:
            self.memory.pop(0)    # FIFO eviction

        return label
```

**Performance:** ~40.9% accuracy (the ACE baseline from the paper).

## What Meta-Harness Discovered

### Iteration 1: The Proposer Reads Traces

```bash
$ grep "correct_label" baseline/traces/task_*.json | head -5
task_003.json:  "correct_label": "sports",   "predicted": "politics"
task_007.json:  "correct_label": "negative", "predicted": "neutral"
task_012.json:  "correct_label": "technology","predicted": "business"
```

The proposer sees: this isn't random error — it's systematic misclassification between related categories.

### Iteration 3: Diagnosis

```bash
$ cat baseline/traces/task_007.json | jq '.steps[0:3]'
[
  {"action": "retrieve", "query": "recency", "retrieved": [
    {"text": "The stock market rallied...", "label": "business"},
    {"text": "Senator proposes new...",    "label": "politics"},
    {"text": "Team wins championship...",  "label": "sports"}
  ]},
  {"action": "call_model", "context_preview": "Recent examples: [business, politics, sports]..."},
  {"action": "store", "key": "recency_queue", "value": {"text": "...", "label": "neutral"}}
]
```

Proposer notices: the recency-based retrieval is pulling **irrelevant** examples (sports, business for a sentiment classification task). The "topic" examples are polluting the context.

### Iteration 5: First Improvement

The proposer patches the retrieval to use **similarity-based** selection:

```python
class SimilarityHarness(ClassificationHarness):
    def classify(self, document):
        # Retrieve: most SIMILAR past examples, not most recent
        if self.memory:
            scored = []
            for ex in self.memory:
                # Count shared words
                doc_words = set(document.lower().split())
                ex_words = set(ex['text'].lower().split())
                overlap = len(doc_words & ex_words)
                scored.append((overlap, ex))
            scored.sort(reverse=True)
            relevant = [ex for _, ex in scored[:5]]
        else:
            relevant = []
        # ... rest similar to baseline
```

**Performance:** ~44.1% accuracy (+3.2 points).

### Iteration 8: The "Label-Primed Query"

The proposer discovers a two-step strategy by reading its own traces:

```bash
$ cat candidate_008/traces/task_015.json | jq '.steps[0:5]'
[
  # Step 1: Quick classification (no context)
  {"action": "quick_classify", "input": "The team's performance was...",
   "output": "sports", "confidence": 0.72},

  # Step 2: Retrieve examples matching the primed label
  {"action": "retrieve_by_label", "label": "sports", "retrieved": [
    {"text": "A thrilling match...", "label": "sports"},
    {"text": "Player scores hat-trick...", "label": "sports"}
  ]},

  # Step 3: Confirm or revise with label-matched context
  {"action": "confirm_classify",
   "context": "[two sports examples]",
   "output": "sports", "confidence": 0.94}
]
```

This is the **Label-Primed Query** strategy:

```python
class LabelPrimedHarness(ClassificationHarness):
    def classify(self, document):
        # Step 1: Quick first-pass (model alone, no context)
        candidate_label = self.model.classify(
            f"Quickly classify: {document[:200]}"
        )

        # Step 2: Retrieve examples of that candidate label
        label_matches = [ex for ex in self.memory
                        if ex['label'] == candidate_label]

        # Step 3: Confirm with label-matched context
        context = f"Examples labeled '{candidate_label}':\n"
        for ex in label_matches[:3]:
            context += f"  {ex['text'][:100]}...\n"
        context += f"\nRe-classify with context: {document[:200]}"

        final_label = self.model.classify(context)

        # Store
        self.memory.append({"text": document, "label": final_label})

        return final_label
```

**Performance:** **48.6% accuracy** (+7.7 vs baseline, beats ACE's 40.9% by +7.7).

**Efficiency:** Uses **4× fewer context tokens** than the baseline (only 3 label-matched examples vs. recency-based 12 that often included noise).

### The Pareto Frontier

Search naturally produced a range of harnesses trading accuracy vs. cost:

```
  Accuracy
  49% │                                   ● (Label-Primed, expensive)
      │                         ●
  46% │               ●
      │         ●
  43% │   ●
      │ ● (Baseline, cheap)
  40% │
      └──────────────────────────────────────────
          200    400    600    800   1000   1200
                  Context tokens per classification
```

Practitioners can pick based on their budget: deploy the expensive harness for high-stakes classifications, the cheap one for bulk processing.

## Running the Experiment

```bash
cd reference_examples/text_classification

# Install dependencies
uv sync

# Run 1 iteration (smoke test — ~2 minutes)
uv run python meta_harness.py --iterations 1

# Run full search (paper: 20+ iterations, hours)
uv run python meta_harness.py --iterations 20

# Inspect results
ls search_history/
cat search_history/candidate_*/score.json
```

### Key Files in the Experiment

```
reference_examples/text_classification/
├── meta_harness.py           # Main search loop
├── claude_wrapper.py         # Proposer agent wrapper
├── harness_interface.py      # Base harness class
├── baseline_harness.py       # Human-written starting point
├── evaluation.py             # Evaluates a harness on tasks
├── tasks/
│   ├── train.jsonl           # Search-set tasks
│   └── test.jsonl            # Held-out test set
└── search_history/           # Created during search
    └── ...
```

## Key Takeaways

1. **Recency-based memory is (often) wrong.** The proposer discovered that retrieving by topic similarity, then by label match, systematically outperformed simple recency.
2. **Two-step strategies emerge naturally.** The Label-Primed Query wasn't designed — the proposer invented it by noticing that a quick first-pass enables much better retrieval.
3. **Generalization happens.** Harnesses trained on 8 datasets generalized to 9 unseen ones, suggesting the discovered strategies capture real structure, not dataset-specific overfitting.
4. **Pareto optimization is a side effect.** Searching over code naturally produces candidates trading accuracy vs. cost — you don't need multi-objective optimization machinery.

---

**Previous:** [Chapter 09 — Harness Optimization Theory](./09_harness_optimization_theory.md)
**Next:** [Chapter 11 — TerminalBench 2.0 Walkthrough](./11_terminalbench_walkthrough.md)
