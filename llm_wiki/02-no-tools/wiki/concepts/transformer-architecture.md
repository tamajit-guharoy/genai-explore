---
title: Transformer Architecture
created: 2026-06-19
updated: 2026-06-19
type: concept
tags: [architecture, training]
sources:
  - raw/papers/attention-is-all-you-need.md
  - raw/articles/gpt4-technical-report.md
confidence: high
---

# Transformer Architecture

## Definition
A neural network architecture introduced by Vaswani et al. (2017) that relies entirely on [[attention-mechanism|attention mechanisms]], dispensing with recurrence and convolutions. It is the foundation of all modern large language models. ^[raw/papers/attention-is-all-you-need.md]

## Key Components

### Self-Attention
Computes relevance scores between every pair of tokens in parallel. The core operation:

```
Attention(Q, K, V) = softmax(QK^T / √d_k)V
```

This allows the model to capture long-range dependencies directly — unlike RNNs, which process tokens sequentially and struggle with distant relationships.

### Multi-Head Attention
Multiple attention "heads" operate in parallel, each attending to different representation subspaces. This lets the model focus on different aspects of the input simultaneously (e.g., one head for syntax, another for semantics).

### Positional Encoding
Since there's no recurrence, the model has no inherent sense of token order. Sine/cosine functions of different frequencies are added to input embeddings to encode position.

### Architecture Structure
- **Encoder:** 6 identical layers (multi-head self-attention → feed-forward network), with residual connections and layer normalization
- **Decoder:** 6 identical layers (masked self-attention → encoder-decoder attention → feed-forward)

## Variants

| Variant | Description | Example |
|---|---|---|
| **Encoder-only** | Bidirectional attention; good for understanding | BERT |
| **Decoder-only** | Unidirectional (causal) attention; good for generation | GPT series, Claude |
| **Encoder-decoder** | Full architecture; good for transduction | Original Transformer, T5 |

## Modern LLMs as Transformers
All major LLMs use decoder-only Transformer variants:
- **GPT-4** ([[openai]]) — Decoder-only with RLHF post-training ^[raw/articles/gpt4-technical-report.md]
- **Claude** ([[anthropic]]) — Decoder-only with Constitutional AI alignment
- **Hermes** ([[nous-research]]) — Fine-tuned from decoder-only base models for tool use

## Impact
The Transformer displaced RNNs/LSTMs across virtually all of NLP. It is now expanding into computer vision (Vision Transformer / ViT), audio processing, and multimodal models. "Attention Is All You Need" turned out to be prophetic.

## See Also
- [[attention-mechanism]] — the core operation
- [[gpt-4]] — a prominent Transformer implementation
- [[positional-encoding]] — how Transformers handle sequence order
