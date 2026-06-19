---
source_url: https://example.com/gpt4-technical-report-excerpt
ingested: 2026-06-19
sha256: placeholder
---

# GPT-4 Technical Report — Excerpt

*OpenAI, March 2023*

## Model Architecture (Section 2)

GPT-4 is a Transformer-based model pre-trained to predict the next token in a document. The training data is a mixture of publicly available text data and data licensed from third-party providers. Post-training uses reinforcement learning from human feedback (RLHF) to align the model with human intent.

Key architectural details:
- **Transformer-based** — follows the decoder-only architecture of the GPT family
- **Scale** — significantly larger than GPT-3.5, though exact parameter count is not disclosed
- **Context window** — 8,192 tokens (standard) and 32,768 tokens (extended)
- **Multimodal** — accepts both text and image inputs (though image generation is not supported)

## Capabilities (Section 3)

GPT-4 demonstrates human-level performance on many professional and academic benchmarks:

- **Bar Exam:** 90th percentile (vs. GPT-3.5 at 10th percentile)
- **SAT Math:** 89th percentile
- **GRE Verbal:** 99th percentile
- **AP exams:** 5 on most subjects

### Tool Use and Agentic Behavior

The report notes GPT-4's improved ability to use tools and follow complex, multi-step instructions. When equipped with tool access and given an objective, GPT-4 can:
- Browse the web to gather information
- Write and execute code
- Analyze data and generate reports
- Maintain coherent multi-turn task execution

This capability has been productized as Codex (OpenAI's coding agent, 2025) and forms the foundation for OpenAI's agent strategy.

## Limitations and Risks (Section 4)

- **Hallucination:** GPT-4 still confidently generates false information
- **Bias:** Reflects biases present in training data
- **Safety:** Can be jailbroken to produce harmful content despite alignment efforts
- **Cost:** Inference is computationally expensive, limiting real-time applications
- **Context limits:** Long-running agent tasks can exceed the context window

## Comparison with Claude

While OpenAI and Anthropic share a common Transformer heritage, they diverge on:
- **Alignment approach:** RLHF (OpenAI) vs. Constitutional AI (Anthropic)
- **Transparency:** OpenAI discloses less architectural detail than Anthropic
- **Pricing:** GPT-4 is generally more expensive per token than Claude equivalents
- **Safety posture:** Anthropic takes a more conservative approach to capability deployment

## Significance for AI Agents

GPT-4 proved that a single large model could handle diverse tool-use tasks without task-specific fine-tuning. This "generalist agent" paradigm — one model, many tools — is now the dominant approach, used by Claude Code, Codex, Hermes Agent, and most other agent platforms.
