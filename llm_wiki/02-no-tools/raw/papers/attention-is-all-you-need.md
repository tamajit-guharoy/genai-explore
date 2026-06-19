---
source_url: https://arxiv.org/abs/1706.03762
ingested: 2026-06-19
sha256: placeholder
---

# Attention Is All You Need

*Vaswani et al., 2017 — the paper that introduced the Transformer architecture.*

## Abstract (Excerpt)

The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.

## Key Contributions

### 1. Self-Attention Mechanism
Instead of processing tokens sequentially (like RNNs), the Transformer computes attention scores between every pair of tokens in parallel. This allows the model to capture long-range dependencies directly.

The core operation: `Attention(Q, K, V) = softmax(QK^T / √d_k)V`

### 2. Multi-Head Attention
Rather than a single attention function, the Transformer uses multiple "heads" that attend to different representation subspaces. This lets the model focus on different aspects of the input simultaneously.

### 3. Positional Encoding
Since there's no recurrence or convolution, the model has no inherent notion of token order. Positional encodings (sine/cosine functions of different frequencies) are added to the input embeddings.

### 4. Architecture
- **Encoder:** N=6 identical layers, each with multi-head self-attention and a feed-forward network
- **Decoder:** N=6 identical layers, with masked self-attention, encoder-decoder attention, and feed-forward
- **Residual connections** and **layer normalization** throughout

## Results

The Transformer achieved state-of-the-art BLEU scores on WMT 2014 English-to-German (28.4) and English-to-French (41.0) translation tasks, while being significantly faster to train than recurrent or convolutional alternatives.

## Impact

This paper is arguably the most influential in modern AI. The Transformer architecture is the foundation of:
- BERT (Devlin et al., 2018)
- GPT series (Radford et al., 2018–2024)
- Claude (Anthropic)
- Gemini (Google)
- Every major LLM since 2018

The "Attention Is All You Need" title turned out to be prophetic — attention mechanisms displaced recurrence across virtually all of NLP and are now expanding into computer vision (ViT) and other domains.

## Key Figures
- Figure 1: The Transformer architecture diagram (encoder-decoder stack)
- Figure 2: Scaled Dot-Product Attention and Multi-Head Attention diagrams
- Table 1: Maximum path lengths, per-layer complexity, and minimum sequential operations comparison

## Citation
Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, L., & Polosukhin, I. (2017). Attention Is All You Need. *Advances in Neural Information Processing Systems 30*.
