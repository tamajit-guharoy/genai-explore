# Chapter 12: Onboarding a New Domain

## Overview

This chapter is a practical guide to applying Stanford Meta-Harness to your own domain. It's based on the `ONBOARDING.md` from the repo and the paper's methodology.

**Important:** This is an **onboarding process** — defining the problem and designing the harness interface. It happens *before* any code is written.

## Step 1: Is Your Domain a Good Fit?

Before investing time, verify your domain has the right properties:

| Property | Requirement | Your domain? |
|---|---|---|
| **Long-horizon or multi-step** | Harness choices compound over many steps | ☐ |
| **Repeated tasks/episodes** | Need enough data for search (20-50 tasks minimum) | ☐ |
| **Fixed base model** | All improvement must come from harness, not weights | ☐ |
| **Measurable success metric** | Clear, automatable scoring function | ☐ |
| **Recurring error patterns** | Something systematic for the proposer to fix | ☐ |
| **Meaningful held-out test set** | Or a way to create one | ☐ |
| **Offline traces (bonus)** | Existing data to warm-start search | ☐ |
| **Cost budget (tokens/$)** | Enough for N iterations × K tasks per evaluation | ☐ |

**Skip Meta-Harness if:**
- Most gains would come from fine-tuning or a bigger model
- Your task is one-off and unrepeatable
- You need sub-second decisions (search takes time)

## Step 2: The Onboarding Conversation

The ONBOARDING.md provides a structured conversation loop for domain definition. Here's how to run it:

### 2a. Start with a One-Paragraph Description

Write down what you want to improve:

```markdown
Domain: [e.g., "Code review automation"]
Base model: [e.g., Claude Sonnet 4]
What I want to improve: [e.g., "Review quality — currently catches
40% of real bugs; I want 60%+"]
Current harness: [e.g., "A simple prompt that includes the diff and says
'find bugs'"]
```

### 2b. Fill In Required Fields

Work through the ONBOARDING.md checklist. Here's a completed example:

#### 1. Problem Framing

| Question | Answer |
|---|---|
| What is the user trying to improve? | Code review bug-detection rate |
| Unit of evaluation | One PR review (one diff → list of bugs found) |
| What is fixed? | Base model (Claude Sonnet 4, frozen weights) |
| What is allowed to change? | Harness code: diff chunking, context assembly, review checklist injection, past-review memory |
| Frozen base model | claude-sonnet-4-6 |
| Optimization budget | $200 in API credits, 50 iterations |

#### 2. Harness Definition

```python
# Harness interface
class ReviewHarness:
    def __init__(self, model):
        self.model = model
        self.memory = []  # past reviews for context

    def review(self, pr_diff: str, pr_description: str,
               repo_context: str) -> list[dict]:
        """
        Returns a list of bugs found.
        Each bug: {
            'file': str,
            'line': int,
            'severity': 'critical'|'high'|'medium'|'low',
            'description': str,
            'suggestion': str
        }
        """
        raise NotImplementedError
```

#### 3. Evaluation

| Question | Answer |
|---|---|
| Search-set evaluation | 50 PRs with known bugs (from bug tracker) |
| Held-out test set | 20 PRs from a different repo |
| Primary metric | Precision@10 (bugs found in top 10 flagged) |
| Secondary metrics | Recall, false-positive rate, tokens per review |
| Noise level | Moderate — bugs can be subjective |
| Evaluation time | ~30s per PR |

#### 4. Baselines

| Baseline | Description |
|---|---|
| `review_naive.py` | Send full diff + "find bugs" |
| `review_chunked.py` | Split diff by file, review each independently |
| `review_checklist.py` | Inject a bug-checklist prompt before review |

#### 5. Offline Experience

- Existing code review comments (500+ PRs) → can extract bug examples
- Bug tracker with labeled severities → can use for ground truth

#### 6. Online Experience

```
search_history/
└── candidate_N/
    ├── harness.py
    ├── score.json
    └── traces/
        ├── pr_001.json   # Full trace: chunking decisions,
        ├── pr_002.json   # model calls, bugs found/missed,
        └── ...           # false positives
```

## Step 3: Generate domain_spec.md

Using the template from ONBOARDING.md:

```markdown
# Domain Spec: Code Review Automation

## Domain Summary
Automated bug detection in pull requests. The harness
controls how a PR diff is chunked, what context is
assembled, what review checklist is injected, and how
past review outcomes influence future reviews. Base
model: claude-sonnet-4-6 (frozen). Budget: $200, 50
iterations.

## Harness Interface
[Include the Python class definition from Step 2b]

## Evaluation
- Search set: 50 PRs from repo A (known bugs tracked)
- Test set: 20 PRs from repo B (held out, different team)
- Metric: Precision@10 (bugs in top 10 flagged findings)
- Secondary: Recall, FPR, cost per review

## Baselines
1. review_naive.py — full diff, "find bugs"
2. review_chunked.py — per-file chunking
3. review_checklist.py — checklist injection

## Offline Resources
- 500+ PRs with reviewer comments in bug tracker
- Bug severity labels available
- Codebase structure docs

## Trace Schema
Each trace records:
- How diff was chunked (per file? per hunk? fixed-size?)
- Context assembled for each chunk
- Model call and raw response
- Bugs flagged vs. ground truth
- False positives (flagged but not bugs)
```

## Step 4: Implementation Plan

Once `domain_spec.md` is complete, the implementation follows the reference examples:

### Directory Structure

```
my_domain/
├── domain_spec.md
├── meta_harness.py           # Search loop (adapt from reference)
├── proposer_wrapper.py       # Proposer agent (Claude Code or other)
├── harness_interface.py      # Base class from domain_spec
├── baseline_harnesses/       # Human-written starting points
│   ├── naive.py
│   ├── chunked.py
│   └── checklist.py
├── evaluation.py             # Implements evaluation from domain_spec
├── tasks/
│   ├── search_set.jsonl      # 50 tasks
│   └── test_set.jsonl        # 20 tasks (held out)
└── search_history/           # Created during search
```

### Implementation Checklist

- [ ] `harness_interface.py` — base class matching domain_spec
- [ ] `evaluation.py` — run a harness on N tasks, compute metrics
- [ ] `baseline_harnesses/naive.py` — simplest possible harness
- [ ] Verify baseline evaluation works (`python evaluation.py baseline_harnesses/naive.py`)
- [ ] `proposer_wrapper.py` — adapt Claude Code wrapper from reference
- [ ] `meta_harness.py` — search loop, filesystem management
- [ ] Dry run: 1 iteration, verify proposer can read traces and write harness code
- [ ] Small search: 5 iterations, verify scores improve
- [ ] Full search: N iterations (budget permitting)

## Step 5: Common Pitfalls

### 1. Evaluation Leakage

**Problem:** Your "held-out" test set shares patterns with the search set.

**Fix:** Use different repos, different time periods, or different task sources.

### 2. Too Small Search Set

**Problem:** 10 tasks isn't enough for the proposer to find systematic patterns.

**Fix:** Aim for 50+ tasks in the search set.

### 3. Non-Executable Harness Code

**Problem:** Proposer generates Python with syntax errors or missing imports.

**Fix:** Add a syntax check + basic import check in the evaluation step; reject and re-propose on failure.

### 4. Proposer Gets Stuck

**Problem:** After a few iterations, scores plateau and the proposer keeps generating similar harnesses.

**Fix:** Increase proposer temperature, add diversity prompts ("try a completely different approach"), or seed with a random harness.

### 5. Trace Size Explosion

**Problem:** Full traces for 50 tasks × 100+ steps each = gigabytes of JSON.

**Fix:** Implement selective trace pruning — keep only steps where the harness made a decision (store, retrieve, route), not every model token.

## Summary

Applying Meta-Harness to a new domain is a structured process:

1. **Validate fit** — is your domain long-horizon, repeatable, and harness-dominated?
2. **Define the problem** — use the ONBOARDING.md conversation loop to fill in every field
3. **Write `domain_spec.md`** — the complete specification before any code
4. **Implement** — adapt reference examples; start with smoke tests, scale up
5. **Avoid pitfalls** — evaluation leakage, small search sets, trace explosion

The ONBOARDING.md in the repo is the authoritative guide — this chapter is a practical companion.

---

**Previous:** [Chapter 11 — TerminalBench 2.0 Walkthrough](./11_terminalbench_walkthrough.md)
**Next:** [Appendix A — Omnigent vs. Meta-Harness Comparison](../part4_appendix/A_omnigent_vs_meta_harness.md)
