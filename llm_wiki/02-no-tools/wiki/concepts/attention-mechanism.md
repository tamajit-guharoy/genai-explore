---
title: Attention Mechanism
created: 2026-06-19
updated: 2026-06-19
type: concept
tags: [architecture, technique]
sources:
  - raw/papers/attention-is-all-you-need.md
confidence: high
---

# Attention Mechanism

## Definition
A neural network operation that computes weighted relevance scores between elements in a sequence. In the [[transformer-architecture]], self-attention allows every token to attend to every other token directly, capturing long-range dependencies without sequential processing. ^[raw/papers/attention-is-all-you-need.md]

## Scaled Dot-Product Attention
The core formula from Vaswani et al. (2017):

```
Attention(Q, K, V) = softmax(QK^T / √d_k)V
```

Where:
- **Q (Query):** What we're looking for
- **K (Key):** What we match against
- **V (Value):** What we retrieve
- **√d_k:** Scaling factor to prevent extreme softmax outputs

## Intuition
Think of attention as a differentiable dictionary lookup:
1. Query is compared against all Keys to produce relevance scores
2. Scores are normalized (softmax) into a probability distribution
3. Values are weighted by these probabilities and summed

The result: each position gets a context-aware representation that incorporates information from all other positions.

## Multi-Head Attention
Instead of one attention function with full-dimensional keys/values, multi-head attention projects Q, K, V into h lower-dimensional subspaces, computes attention in parallel, then concatenates and projects the results.

This lets the model attend to different representation subspaces simultaneously — e.g., one head for syntactic relationships, another for semantic ones, another for positional patterns.

## Self-Attention vs. Cross-Attention
- **Self-attention:** Q, K, V all come from the same sequence (used in encoder and decoder self-attention)
- **Cross-attention:** Q comes from decoder, K and V come from encoder output (used in encoder-decoder attention)

## Why It Replaced Recurrence

| Property | RNN/LSTM | Self-Attention |
|---|---|---|
| Path length between distant tokens | O(n) | O(1) |
| Parallelization | Sequential (per-step) | Full parallel |
| Computational complexity per layer | O(n · d²) | O(n² · d) |

The constant path length means attention can directly model relationships between tokens thousands of positions apart — something RNNs struggle with due to vanishing gradients.

## Broader Impact
The attention mechanism has expanded beyond NLP:
- **Vision Transformer (ViT):** Apply self-attention to image patches
- **Cross-modal attention:** Connect text and image representations
- **Sparse attention:** Reduce O(n²) complexity for very long sequences

## See Also
- [[transformer-architecture]] — the full architecture built on attention
- [[positional-encoding]] — how Transformers add sequence order
- [[multi-head-attention]] — the parallel attention variant
