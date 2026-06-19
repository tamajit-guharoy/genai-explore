---
source_url: https://arxiv.org/abs/1706.03762
ingested: 2026-06-19
sha256: placeholder
---

# Attention Is All You Need

*Vaswani et al., 2017 — the paper that introduced the Transformer architecture.*

## Abstract

The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

## Key Contributions

### 1. Self-Attention Mechanism
Instead of processing tokens sequentially (like RNNs), the Transformer computes attention scores between every pair of tokens in parallel. The core operation:

`Attention(Q, K, V) = softmax(QK^T / √d_k)V`

### 2. Multi-Head Attention
Multiple "heads" attend to different representation subspaces, allowing the model to focus on different aspects of the input simultaneously.

### 3. Positional Encoding
Since there's no recurrence, positional encodings (sine/cosine functions) are added to input embeddings to encode token order.

### 4. Architecture
- **Encoder:** 6 identical layers (multi-head self-attention + feed-forward)
- **Decoder:** 6 identical layers (masked self-attention + encoder-decoder attention + feed-forward)
- Residual connections and layer normalization throughout

## Results

State-of-the-art BLEU scores on WMT 2014 translation tasks while being significantly faster to train than recurrent or convolutional alternatives.

## Impact

The Transformer is the foundation of every major LLM since 2018: BERT, GPT series, Claude, Gemini, and all modern language models.

## Citation
Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., & Polosukhin, I. (2017). Attention Is All You Need. NeurIPS 30.
