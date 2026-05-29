"""
Example 22: Research Knowledge Management -- Tracking AI/ML Papers Over Time

This example simulates tracking AI/ML research papers across three years
(2023-2025). It demonstrates how Graphiti can:

  1. Model research entities: Paper, Method, Author, Dataset, Finding
  2. Capture temporal provenance of research claims
  3. Handle contradictions when new findings challenge established beliefs
  4. Trace how research evolves: builds_on and contradicts relationships
  5. Use community detection to discover research clusters
  6. Query across time to understand the evolution of ideas

The data is realistic but fictional, representing a simplified research landscape
around efficient transformer architectures.
"""

import asyncio
import os
import sys

from datetime import datetime, timezone
from textwrap import dedent

# ---------------------------------------------------------------------------
# Environment / connectivity check
# ---------------------------------------------------------------------------
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

if not OPENAI_API_KEY:
    print(
        "WARNING: OPENAI_API_KEY is not set. Graphiti uses an LLM to extract "
        "entities and relationships. Without it, extraction will fail.\n"
        "Set it via:  export OPENAI_API_KEY='sk-...'  (Linux/Mac)\n"
        "or:          $env:OPENAI_API_KEY='sk-...'   (Windows PowerShell)\n"
    )


def check_neo4j_connection() -> bool:
    """Return True if Neo4j appears reachable at NEO4J_URI."""
    import socket

    host, _, port_str = NEO4J_URI.replace("bolt://", "").replace("neo4j://", "").partition(":")
    try:
        port = int(port_str) if port_str else 7687
    except ValueError:
        port = 7687
    try:
        with socket.create_connection((host, port), timeout=3):
            return True
    except (OSError, socket.timeout):
        return False


def print_edges(edges, heading: str = ""):
    """Pretty-print a list of edges with temporal metadata."""
    if heading:
        print(f"\n  --- {heading} ---")
    if not edges:
        print("  (no results)")
        return
    for i, e in enumerate(edges, 1):
        print(f"  [{i}] fact:     {e.fact}")
        print(f"      source:   {e.source_node_name} --> {e.target_node_name}")
        if e.valid_at:
            print(f"      valid at: {e.valid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        if e.invalid_at:
            print(f"      expired:  {e.invalid_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()


async def simulate_research_evolution():
    """
    Core simulation: add research papers in chronological order across
    2023, 2024, and 2025. Each year builds on (or contradicts) prior work.
    """
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType

    graphiti = Graphiti(uri=NEO4J_URI, user=NEO4J_USER, password=NEO4J_PASSWORD)
    await graphiti.build_indices_and_constraints()

    # Use a single group_id for the full research domain
    group_id = "ai_research_evolution"

    # ===================================================================
    # YEAR 1: 2023 -- Foundations
    # ===================================================================
    print("\n" + "=" * 72)
    print("YEAR 1: 2023 -- The Transformer Era")
    print("=" * 72)

    now_2023 = datetime(2023, 6, 15, tzinfo=timezone.utc)

    # Paper 1: TransformerXL
    await graphiti.add_episode(
        name="paper_transformerxl_2023",
        episode_body=dedent("""
            Paper: TransformerXL -- Beyond Fixed-Length Contexts
            Authors: Zihang Dai, Zhilin Yang, Yiming Yang
            Institution: Google Research & Carnegie Mellon University
            Year: 2023
            Venue: NeurIPS 2023

            Finding: TransformerXL introduces segment-level recurrence with a state
            reuse mechanism, enabling learning of dependencies beyond 80% longer
            than vanilla transformers while maintaining inference speed.

            Method: Segment-level recurrence with relative positional encoding.
            The recurrent mechanism caches hidden states from previous segments,
            reusing them as extended context for the current segment.

            Dataset: WikiText-103, enwik8, text8
            Achieves: Test perplexity 18.3 on WikiText-103, significantly
            outperforming the previous SOTA of 20.5.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2023,
        group_id=group_id,
    )
    print("  [2023] Added: TransformerXL -- segment-level recurrence")

    # Paper 2: Sparse Attention
    await graphiti.add_episode(
        name="paper_sparse_attention_2023",
        episode_body=dedent("""
            Paper: Sparse Attention Mechanisms for Efficient Transformers
            Authors: Rewon Child, Scott Gray, Alec Radford
            Institution: OpenAI
            Year: 2023
            Venue: ICML 2023

            Finding: Full attention matrices are computationally wasteful for
            long sequences. Sparse attention patterns (fixed, strided, and
            learned sparsity) reduce complexity from O(n^2) to O(n sqrt(n))
            with minimal accuracy loss.

            Method: Sparse attention patterns. Factorized attention combines
            strided and fixed attention patterns. Learned sparsity uses
            L0 regularization to discover task-specific patterns.

            Dataset: CIFAR-10, ImageNet, Enwik8
            Achieves: 99.1% accuracy on CIFAR-10 with 40% fewer FLOPs than
            dense attention baseline.

            Builds on: TransformerXL -- the relative positional encoding
            scheme from TransformerXL is adopted for sparse attention patterns.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2023,
        group_id=group_id,
    )
    print("  [2023] Added: Sparse Attention -- O(n sqrt(n)) complexity")

    # Paper 3: Linear Attention
    await graphiti.add_episode(
        name="paper_linear_attention_2023",
        episode_body=dedent("""
            Paper: Linear Transformers Are Secretly Fast Weight Programmers
            Authors: Imanol Schlag, Kazuki Irie, Jurgen Schmidhuber
            Institution: Swiss AI Lab, IDSIA
            Year: 2023
            Venue: ICML 2023

            Finding: Linear attention mechanisms can be reformulated as fast
            weight programmers, achieving O(n) complexity for sequence lengths
            up to 16K tokens while retaining competitive performance.

            Method: Linearized attention via kernel feature maps. The key-query
            product is replaced with a feature map dot product, enabling
            associative memory updates in O(n) time.

            Dataset: PG-19, WikiText-103, LAMBADA
            Achieves: Comparable perplexity to softmax attention on PG-19 with
            2x faster training and 3x faster inference.

            Builds on: Sparse Attention Mechanisms for Efficient Transformers --
            extends sparsity ideas to achieve fully linear complexity.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2023,
        group_id=group_id,
    )
    print("  [2023] Added: Linear Attention -- O(n) complexity achieved")

    # ===================================================================
    # YEAR 2: 2024 -- Building on Foundations
    # ===================================================================
    print("\n" + "=" * 72)
    print("YEAR 2: 2024 -- Mixture of Experts & Sparse Attention Advances")
    print("=" * 72)

    now_2024 = datetime(2024, 4, 10, tzinfo=timezone.utc)

    # Paper 4: Mixture of Experts
    await graphiti.add_episode(
        name="paper_moe_2024",
        episode_body=dedent("""
            Paper: Mixture of Experts with Dynamic Routing for Efficient LLMs
            Authors: William Fedus, Barret Zoph, Noam Shazeer
            Institution: Google DeepMind
            Year: 2024
            Venue: ICLR 2024

            Finding: Sparse Mixture of Experts (MoE) with top-k routing enables
            training models with 1 trillion parameters while using only 10% of
            parameters per forward pass, achieving 4x better compute efficiency
            than dense transformers.

            Method: Sparse MoE with top-2 routing. Each input token is routed
            to the top-2 most relevant expert networks (out of 64-2048 experts).
            Load balancing loss ensures uniform expert utilization.

            Dataset: C4, The Pile, GitHub Code
            Achieves: 1T parameter MoE model achieves 15% lower perplexity than
            a dense 500B parameter model at equivalent inference cost.

            Builds on: Linear Transformers Are Secretly Fast Weight Programmers --
            MoE routing mechanisms build on linear attention's per-token processing.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2024,
        group_id=group_id,
    )
    print("  [2024] Added: Mixture of Experts -- 1T parameter MoE")

    # Paper 5: Multi-Query Attention
    await graphiti.add_episode(
        name="paper_multi_query_2024",
        episode_body=dedent("""
            Paper: Fast Transformer Decoding via Multi-Query Attention
            Authors: Noam Shazeer
            Institution: Google Brain
            Year: 2024
            Venue: NeurIPS 2024

            Finding: Multi-Query Attention (MQA) uses multiple query heads but
            only a single key-value head, reducing memory bandwidth requirements
            by 50% during autoregressive decoding with negligible quality loss.

            Method: Single key-value head shared across all query heads.
            This reduces the size of the KV cache from n_heads * d_kv to
            1 * d_kv, dramatically cutting memory for long sequences.

            Dataset: WMT 2014 English-German, WMT 2014 English-French
            Achieves: BLEU score 28.4 on En-De (vs 28.5 for baseline) with
            2.3x faster decoding.

            Builds on: Sparse Attention Mechanisms for Efficient Transformers --
            MQA extends the efficiency principles of sparse attention to the
            decoding phase specifically.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2024,
        group_id=group_id,
    )
    print("  [2024] Added: Multi-Query Attention -- 50% less KV cache")

    # ===================================================================
    # YEAR 3: 2025 -- New Paradigms & Contradictions
    # ===================================================================
    print("\n" + "=" * 72)
    print("YEAR 3: 2025 -- State Space Models Challenge Attention")
    print("=" * 72)

    now_2025 = datetime(2025, 2, 20, tzinfo=timezone.utc)

    # Paper 6: State Space Models (SSMs)
    await graphiti.add_episode(
        name="paper_mamba_2025",
        episode_body=dedent("""
            Paper: Mamba -- Linear-Time Sequence Modeling with Selective State Spaces
            Authors: Albert Gu, Tri Dao
            Institution: Princeton University, Carnegie Mellon University
            Year: 2025
            Venue: ICLR 2025 (Oral)

            Finding: State Space Models (SSMs) with selective state transitions
            can match or exceed transformer performance on long-range tasks
            without requiring any attention mechanism. SSMs process sequences
            in O(n) time and O(1) memory during inference.

            Method: Selective State Space Model (Mamba). Unlike previous SSMs
            with time-invariant parameters, Mamba uses input-dependent state
            transitions, enabling content-aware reasoning. Hardware-aware
            parallel scan algorithm for efficient training.

            Dataset: The Pile, PG-19, Long Range Arena (LRA)
            Achieves: 5x higher throughput than Transformers on sequences of
            8K tokens. State-of-the-art on LRA benchmark with 86.5 average score.

            Contradicts: The central finding of the 2023-2024 efficient attention
            literature. Papers like Sparse Attention and Linear Attention claimed
            that attention (even if optimized) was essential for sequence modeling.
            Mamba shows that no attention at all is needed -- structured state
            spaces suffice and outperform attention on several long-range tasks.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2025,
        group_id=group_id,
    )
    print("  [2025] Added: Mamba SSM -- challenges attention necessity")

    # Paper 7: Hybrid SSM-Attention
    await graphiti.add_episode(
        name="paper_hybrid_ssm_2025",
        episode_body=dedent("""
            Paper: Jamba -- Hybrid SSM-Transformer for Efficient Language Models
            Authors: Opher Lieber, Barak Lenz, Hofit Bata, Gal Cohen, Jhonathan Osin
            Institution: AI21 Labs
            Year: 2025
            Venue: arXiv 2025

            Finding: A hybrid architecture combining Mamba SSM layers with
            traditional attention layers achieves the best of both worlds:
            SSMs handle long-range context efficiently while attention provides
            recall and lookup capabilities that SSMs struggle with.

            Method: Alternating Mamba layers (every 8th layer is a standard
            attention layer). Uses MoE for feed-forward expansion. Total 52B
            parameters with 12B active per token.

            Dataset: C4, The Pile, BooksCorpus
            Achieves: 8-bit perplexity 5.82 on C4, competitive with much larger
            dense transformers at 1/3 the inference cost.

            Builds on: Mamba -- adopts the selective SSM architecture.
            Builds on: Mixture of Experts -- uses MoE layers for FFN.
            Builds on: TransformerXL -- uses a modified relative positional encoding.

            Partially contradicts: Mamba's claim that pure SSMs are sufficient.
            Jamba finds that a small number of attention layers (1 in 8) is
            still needed for recall-intensive tasks like fact lookup.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2025,
        group_id=group_id,
    )
    print("  [2025] Added: Jamba Hybrid SSM-Attention")

    # Paper 8: Rejection of Full Attention
    await graphiti.add_episode(
        name="paper_no_attention_2025",
        episode_body=dedent("""
            Paper: Attention-Free Transformers Are All You Need (Maybe)
            Authors: Junxiong Wang, Yingbo Zhou, Caiming Xiong
            Institution: Salesforce Research
            Year: 2025
            Venue: ACL 2025

            Finding: A systematic study showing that across 25 diverse NLP
            benchmarks, pure SSM architectures match or exceed transformer
            performance on 21 of 25 benchmarks. The only cases where attention
            helps are tasks requiring associative recall (e.g., looking up a
            fact from earlier context).

            Method: Systematic benchmarking of Mamba, S4, Hyena, and other
            SSM variants against optimized transformers across 25 tasks
            spanning reasoning, summarization, classification, and generation.

            Dataset: 25 diverse NLP benchmarks including SuperGLUE,
            BigBench Hard, HELM, and LongBench
            Achieves: Average of 82.3% across all benchmarks vs 81.9% for
            transformers -- statistically equivalent.

            Contradicts: The 2023 efficient attention literature (Sparse
            Attention, Linear Attention) strongly suggested that attention
            mechanisms should be preserved but optimized. This paper shows
            that replacing attention entirely with SSMs is viable for most
            use cases.

            Builds on: Mamba -- uses Mamba as the primary SSM baseline.
        """),
        source=EpisodeType.text,
        source_description="Research paper abstract",
        reference_time=now_2025,
        group_id=group_id,
    )
    print("  [2025] Added: No-Attention Study -- SSMs match Transformers")

    return graphiti, group_id


# ===================================================================
# Main example
# ===================================================================
async def main():
    print("=" * 72)
    print("Example 22: Research Knowledge Management")
    print("Temporal tracking of AI/ML research papers (2023-2025)")
    print("=" * 72)

    if not check_neo4j_connection():
        print(
            f"\n[SKIP] Cannot reach Neo4j at {NEO4J_URI}\n"
            f"  Start Neo4j via Docker:\n"
            f"    docker run --rm -p 7687:7687 -p 7474:7474 "
            f"-e NEO4J_AUTH={NEO4J_USER}/password neo4j:5\n"
        )
        return

    graphiti, group_id = await simulate_research_evolution()

    # ===================================================================
    # Query 1: What methods exist for efficient attention?
    # ===================================================================
    print("\n" + "=" * 72)
    print("RESEARCH QUERIES")
    print("=" * 72)

    print('\n>>> Query 1: "What methods exist for efficient attention?"')
    print(
        "  This should surface all papers about efficient attention: Sparse Attention,\n"
        "  Linear Attention, Multi-Query Attention, and MoE routing.\n"
    )
    edges = await graphiti.search(
        query="What methods exist for efficient attention mechanisms in transformers?",
        group_ids=[group_id],
        num_results=10,
    )
    print_edges(edges, f"Found {len(edges)} relevant relationships")

    # ===================================================================
    # Query 2: How did attention efficiency research evolve?
    # ===================================================================
    print("\n>>> Query 2: How did research on attention efficiency evolve from 2023 to 2025?")
    print(
        "  This traces the evolution: full attention -> sparse attention -> linear attention\n"
        "  -> MoE -> MQA -> SSM (no attention) -> hybrid SSM-attention.\n"
    )
    edges = await graphiti.search(
        query=(
            "Trace the evolution of attention efficiency research from 2023 to 2025. "
            "How did ideas build on each other and what contradictions emerged?"
        ),
        group_ids=[group_id],
        num_results=10,
    )
    print_edges(edges, f"Found {len(edges)} relevant relationships")

    # ===================================================================
    # Query 3: Contradictions in the literature
    # ===================================================================
    print("\n>>> Query 3: What findings contradict earlier work?")
    print(
        "  This demonstrates contradiction handling. Earlier papers (2023-2024) claimed\n"
        "  attention optimization was the path forward. Later papers (2025) challenged\n"
        "  this by showing attention may not be needed at all.\n"
    )
    edges = await graphiti.search(
        query="What papers or findings contradict earlier research about attention being essential?",
        group_ids=[group_id],
        num_results=10,
    )
    print_edges(edges, f"Found {len(edges)} contradictory relationships")

    # ===================================================================
    # Query 4: What did Mamba build on and what does it challenge?
    # ===================================================================
    print("\n>>> Query 4: What is Mamba's position in the research landscape?")
    print(
        "  This shows both builds_on and contradicts relationships for Mamba,\n"
        "  illustrating how Graphiti captures the full context.\n"
    )
    edges = await graphiti.search(
        query="What papers did Mamba build on and what findings does it contradict?",
        group_ids=[group_id],
        num_results=10,
    )
    print_edges(edges, f"Found {len(edges)} relationships for Mamba")

    # ===================================================================
    # Query 5: Research clusters (community detection simulation)
    # ===================================================================
    print("\n" + "=" * 72)
    print("RESEARCH CLUSTERS (Community Detection)")
    print("=" * 72)
    print(
        "  Graphiti uses Leiden community detection on the entity graph. Below we query\n"
        "  for distinct research communities that emerge from the paper relationships.\n"
        "  \n"
        "  Expected clusters:\n"
        "    1. Attention Optimization Cluster: TransformerXL, Sparse Attention, Linear Attention, MQA\n"
        "       These papers all work on improving the transformer attention mechanism.\n"
        "    \n"
        "    2. Scaling & Architecture Cluster: MoE, Jamba\n"
        "       These focus on scaling and hybrid architectures.\n"
        "    \n"
        "    3. Post-Attention Cluster: Mamba, No-Attention Study\n"
        "       These challenge the attention paradigm itself.\n"
    )

    # Use a broad query to surface community structure
    edges = await graphiti.search(
        query=(
            "What are the main research communities or clusters in this literature? "
            "Group papers by their general approach to sequence modeling."
        ),
        group_ids=[group_id],
        num_results=15,
    )
    print_edges(edges, f"Found {len(edges)} relationships across research clusters")
    print(
        "  Note: In a production system, you'd also use Graphiti's community detection\n"
        "  directly via the Neo4j Graph Data Science library (Leiden algorithm) to\n"
        "  extract community membership for each entity node.\n"
    )

    # ===================================================================
    # Summary: Key takeaways
    # ===================================================================
    print("=" * 72)
    print("Key Takeaways")
    print("=" * 72)
    print("""
  1. Temporal research tracking
     Each paper's findings are timestamped with reference_time. Older findings
     remain in the graph even when superseded or contradicted.

  2. Contradiction handling
     Graphiti captures contradicts relationships alongside builds_on. Both
     conflicting viewpoints coexist in the graph with their temporal context.

  3. Provenance
     Every fact is linked back to its source episode (the paper abstract).
     You can trace which paper made which claim and when.

  4. Community detection
     Research clusters naturally emerge from the relationship graph.
     Leiden clustering groups papers by their intellectual lineage.

  5. Cross-time queries
     Semantic search across all timestamps reveals the full arc of research,
     from foundational work to paradigm shifts.
""")

    # Clean up
    print("\nCleaning up...")
    await graphiti.delete_group(group_id=group_id)
    await graphiti.close()
    print("Done. Graphiti connection closed.")


if __name__ == "__main__":
    asyncio.run(main())
