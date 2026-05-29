"""
19_research_assistant.py — Research & Literature Review Assistant.

Simulates ingesting research paper abstracts and building a research knowledge
graph connecting papers, methods, datasets, findings, and contradictions.

Prerequisites:
    pip install cognee
"""

import asyncio

import cognee


async def main():
    print("Building Research Paper Knowledge Graph...")
    print("=" * 60)

    # ── Paper 1 ────────────────────────────────────────────────────────
    await cognee.add("""
    TITLE: "Attention Is All You Need"
    AUTHORS: Vaswani, Shazeer, Parmar, Uszkoreit, Jones, Gomez, Kaiser, Polosukhin
    YEAR: 2017
    VENUE: NeurIPS
    ABSTRACT: We propose the Transformer, a novel neural network architecture
    based solely on attention mechanisms, dispensing with recurrence and
    convolutions entirely. On the WMT 2014 English-to-German translation task,
    the Transformer achieves 28.4 BLEU, outperforming the previous best model
    by over 2 BLEU. The model also achieves state-of-the-art results on
    English-to-French translation (41.0 BLEU). Key innovation: self-attention
    enables parallel processing of sequential data, reducing training time from
    days to hours compared to RNN-based models.
    METHOD: Transformer with multi-head self-attention
    DATASETS: WMT 2014 English-German, WMT 2014 English-French
    RESULTS: 28.4 BLEU (EN-DE), 41.0 BLEU (EN-FR)
    CITATIONS: 120,000+
    """, dataset_name="research")

    # ── Paper 2 ────────────────────────────────────────────────────────
    await cognee.add("""
    TITLE: "BERT: Pre-training of Deep Bidirectional Transformers"
    AUTHORS: Devlin, Chang, Lee, Toutanova
    YEAR: 2018
    VENUE: NAACL
    ABSTRACT: We introduce BERT, a language representation model based on the
    Transformer architecture. Unlike previous Transformer models, BERT uses
    bidirectional attention — conditioning on both left and right context in
    all layers. BERT achieves state-of-the-art results on 11 NLP tasks
    including GLUE (80.5%), MultiNLI (86.7%), SQuAD v1.1 (93.2 F1), and
    SQuAD v2.0 (83.1 F1). BERT demonstrates that large-scale pre-training
    followed by fine-tuning on specific tasks is a highly effective paradigm.
    METHOD: Bidirectional Transformer with masked language modeling
    DATASETS: BooksCorpus (800M words), English Wikipedia (2,500M words)
    RESULTS: GLUE 80.5%, SQuAD v1.1 F1 93.2, SQuAD v2.0 F1 83.1
    CITATIONS: 100,000+
    """, dataset_name="research")

    # ── Paper 3 ────────────────────────────────────────────────────────
    await cognee.add("""
    TITLE: "RoBERTa: A Robustly Optimized BERT Pretraining Approach"
    AUTHORS: Liu, Ott, Goyal, Du, Joshi, Chen, Levy, Lewis, Zettlemoyer, Stoyanov
    YEAR: 2019
    VENUE: arXiv
    ABSTRACT: We replicate and systematically study the BERT pretraining
    procedure. We find that BERT was significantly undertrained and propose
    RoBERTa, which matches or exceeds all post-BERT methods. Key changes:
    training longer with bigger batches over more data, removing the next
    sentence prediction objective, training on longer sequences, and
    dynamically changing the masking pattern. RoBERTa achieves state-of-the-art
    on GLUE (88.9%), SQuAD (94.6 F1), and RACE (90.2%).
    METHOD: Optimized BERT — longer training, more data, dynamic masking
    DATASETS: BookCorpus + Wikipedia + CC-News + OpenWebText + Stories
    RESULTS: GLUE 88.9%, SQuAD F1 94.6, RACE 90.2%
    CITATIONS: 25,000+
    """, dataset_name="research")

    # ── Paper 4 ────────────────────────────────────────────────────────
    await cognee.add("""
    TITLE: "LoRA: Low-Rank Adaptation of Large Language Models"
    AUTHORS: Hu, Shen, Wallis, Allen-Zhu, Li, Wang, Wang, Chen
    YEAR: 2021
    VENUE: ICLR 2022
    ABSTRACT: We propose Low-Rank Adaptation (LoRA), which freezes pretrained
    model weights and injects trainable rank decomposition matrices into each
    layer of the Transformer architecture. LoRA reduces the number of trainable
    parameters for downstream tasks by 10,000x compared to full fine-tuning
    while maintaining or improving performance. On GPT-3 175B, LoRA reduces
    VRAM usage from 1.2TB to 350GB during fine-tuning. Key insight: the weight
    updates during adaptation have a low "intrinsic rank."
    METHOD: Low-rank matrix decomposition for parameter-efficient fine-tuning
    DATASETS: E2E NLG, DART, WebNLG, GLUE
    RESULTS: Comparable to full fine-tuning with 10,000x fewer parameters
    CITATIONS: 15,000+
    """, dataset_name="research")

    # ── Paper 5 (contrasting) ──────────────────────────────────────────
    await cognee.add("""
    TITLE: "On the Limitations of Fine-Tuning: A Critical Analysis of PEFT"
    AUTHORS: Chen, Zhang, Wang, Liu
    YEAR: 2023
    VENUE: ACL 2023
    ABSTRACT: We perform a large-scale empirical study of parameter-efficient
    fine-tuning (PEFT) methods including LoRA, adapters, and prompt tuning
    across 20 diverse NLP tasks. We find that while PEFT methods approach
    full fine-tuning performance on in-distribution data, they consistently
    underperform (by 5-15%) on out-of-distribution generalization and
    few-shot learning scenarios. We also find that LoRA's performance degrades
    significantly when the rank is below 8 and that different tasks require
    substantially different optimal ranks. This challenges the narrative that
    PEFT methods are a universal replacement for full fine-tuning.
    METHOD: Empirical comparison of PEFT methods (LoRA, adapters, prompt tuning)
    DATASETS: 20 NLP tasks across GLUE, SuperGLUE, and domain-specific benchmarks
    RESULTS: PEFT underperforms by 5-15% on OOD tasks; LoRA needs rank >= 8
    CITATIONS: 500+
    """, dataset_name="research")

    await cognee.cognify()

    # ── Research queries ───────────────────────────────────────────────
    print("\n── Research Literature Queries ──\n")

    queries = [
        # Method evolution
        "Trace the evolution from the original Transformer to BERT to LoRA. "
        "What did each paper contribute?",

        # Performance comparison
        "Compare the GLUE and SQuAD scores across BERT, RoBERTa, and other "
        "approaches mentioned in the papers.",

        # Contradiction detection
        "The 2023 paper by Chen et al. challenges claims made about LoRA. "
        "What specific claims are disputed and what evidence does each side "
        "present?",

        # Method finding
        "What methods exist for reducing the cost of fine-tuning large "
        "language models, and how do they compare?",
    ]

    for query in queries:
        print(f" Q: {query}")
        print("-" * 60)
        results = await cognee.search(query)
        for r in results:
            print(f"  → {r}")
        print()

    print("Done! The research KG connects papers through methods, citations,")
    print("and contradictions — enabling scientific literature analysis at scale.")


if __name__ == "__main__":
    asyncio.run(main())
