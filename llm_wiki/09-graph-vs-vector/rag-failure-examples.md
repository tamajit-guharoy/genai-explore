# RAG Failure Examples — Concrete Demos

> Four worked examples where vector-based RAG breaks down and graph-based wiki retrieval succeeds.
> Each example includes the raw documents, the RAG failure, the wiki solution, and the analysis.

---

## Example 1: The Acquisition Story (Causal Chain)

### The Raw Documents

**doc-acquisition.md:**
```markdown
SAN FRANCISCO — Tech giant MegaCorp announced today the acquisition of startup
NanoAI for $2.3 billion in an all-cash deal. The acquisition, expected to close
in Q3 2024, gives MegaCorp control of NanoAI's flagship natural language
processing platform, LinguaX. NanoAI CEO Sarah Chen will join MegaCorp as VP of AI.
```

**doc-layoffs.md:**
```markdown
MegaCorp confirmed Tuesday that it will lay off the entire 85-person NanoAI team,
reversing earlier statements that the startup would operate independently.
"We determined that integrating NanoAI's technology into our existing platform
required a different team structure," a MegaCorp spokesperson said. Former
NanoAI employees were given 30 days' notice.
```

**doc-product-killed.md:**
```markdown
MegaCorp will discontinue LinguaX, the natural language platform it acquired
for $2.3 billion just eight months ago, according to an internal memo leaked
Thursday. The memo states that LinguaX's technology has been "fully absorbed"
into MegaCorp's existing AI suite and that "maintaining a separate product is
no longer cost-effective." Current LinguaX customers have until December 2025
to migrate.
```

**doc-writedown.md:**
```markdown
MegaCorp disclosed a $1.9 billion goodwill impairment charge in its Q2 2025
earnings, citing "lower than expected commercial returns" from last year's
acquisition of NanoAI. The writedown erases 83% of the $2.3 billion purchase
price. CFO James Morrison told analysts that "the technology acquisition was
successful, but the revenue expectations attached to the standalone product
did not materialize."
```

### RAG Query & Result

**Query:** *"What happened with MegaCorp's acquisition of NanoAI?"*

**RAG Process:**
- Embed query → "MegaCorp acquisition NanoAI"
- Top-3 cosine similarity results:
  1. doc-acquisition.md (score: 0.94) — "MegaCorp acquired NanoAI for $2.3B"
  2. doc-writedown.md (score: 0.71) — "writedown... NanoAI"
  3. doc-acquisition.md (score: 0.68) — duplicate chunk from same doc

**RAG Answer:**
> MegaCorp acquired NanoAI for $2.3 billion in an all-cash deal in 2024. The
> acquisition gave MegaCorp control of the LinguaX NLP platform. MegaCorp later
> disclosed a $1.9 billion goodwill impairment charge related to the acquisition.

**What RAG MISSED:**
- ❌ The entire NanoAI team was laid off (doc-layoffs.md — never retrieved; "layoffs" ≠ "acquisition" in embedding space)
- ❌ The LinguaX product was killed (doc-product-killed.md — never retrieved; "discontinued" ≠ "acquisition")
- ❌ Customers forced to migrate (doc-product-killed.md — buried in the missing document)
- ❌ The CFO's spin: "technology acquisition was successful" (doc-writedown.md — chunk was too far down for K=3)

**RAG told ~40% of the story.** The most human-interesting parts (layoffs, product killed, customer impact) were invisible.

### Wiki Solution

**Agent ingests all 4 documents.** Builds/updates:

**entities/megacorp.md:**
```markdown
---
title: MegaCorp
created: 2025-07-15
updated: 2025-07-15
type: entity
tags: [company]
sources:
  - raw/articles/doc-acquisition.md
  - raw/articles/doc-layoffs.md
  - raw/articles/doc-product-killed.md
  - raw/articles/doc-writedown.md
confidence: high
---

# MegaCorp

## NanoAI Acquisition (2024–2025)

### Timeline
1. **Q3 2024** — Acquired [[nanoai]] for $2.3B all-cash. LinguaX NLP platform included.
   CEO Sarah Chen joined as VP of AI. ^[raw/articles/doc-acquisition.md]
2. **Q4 2024** — Laid off entire 85-person NanoAI team, reversing "independent operation"
   promise. ^[raw/articles/doc-layoffs.md]
3. **Q2 2025** — Discontinued [[linguax]] product. Technology "fully absorbed" into
   MegaCorp's AI suite. Customers given until Dec 2025 to migrate. ^[raw/articles/doc-product-killed.md]
4. **Q2 2025** — $1.9B goodwill impairment (83% of purchase price). CFO cited "lower
   than expected commercial returns" but called the technology acquisition "successful."
   ^[raw/articles/doc-writedown.md]

### Synthesis
The NanoAI acquisition followed a pattern common in Big Tech M&A: buy for technology,
discard the team, kill the product, absorb the tech, write down the price tag.
$2.3B spent → $1.9B written off → 85 people laid off → 1 product discontinued.
The technology survived. Nothing else did.
```

**Query resolution:**
1. Read index.md → find `entities/megacorp.md`
2. Read megacorp.md → full timeline with sources
3. Follow `[[nanoai]]` → read entities/nanoai.md (team details)
4. Follow `[[linguax]]` → read entities/linguax.md (customer impact)
5. Synthesize with citations

**Wiki Answer:**
> MegaCorp acquired NanoAI for $2.3B in Q3 2024. Over the next year: the entire
> 85-person NanoAI team was laid off (Q4 2024), the acquired LinguaX product was
> discontinued with customers forced to migrate (Q2 2025), and $1.9B — 83% of the
> purchase price — was written off as a goodwill impairment. The CFO characterized
> the technology acquisition as "successful" despite the writedown.
>
> In short: technology absorbed, team fired, product killed, $1.9B lost.

**Wiki captured 100% of the story.** All four documents contributed. The narrative arc is preserved.

---

## Example 2: The Contested Method (Citation Network)

### The Raw Documents

**paper-a-claims.md:**
```markdown
We present SparseFormer, a novel transformer variant that achieves 94.2% accuracy
on the GLUE benchmark while using 40% fewer parameters than a standard transformer
of equivalent depth. Our key innovation is dynamic head pruning during inference,
which selectively disables attention heads based on input complexity.
```

**paper-b-replication.md:**
```markdown
We attempted to replicate the 94.2% GLUE score reported for SparseFormer. Across
five independent training runs with the authors' published code and hyperparameters,
we achieved a mean accuracy of 89.1% (σ = 1.3%). We note that the original paper
used a custom GLUE preprocessing pipeline not described in the methods section.
```

**paper-c-contradiction.md:**
```markdown
Our experiments find that SparseFormer's dynamic head pruning introduces
significant latency on standard GPU hardware — 2.3x slower than a dense
transformer at inference, despite 40% fewer parameters. The "efficiency" gains
from parameter reduction are more than offset by the pruning overhead,
making SparseFormer a net-negative for practical deployment.
```

**paper-d-defense.md:**
```markdown
We address the replication concerns raised about SparseFormer. Our original
results (94.2%) used an unreleased version of the GLUE evaluation script that
included task-specific prompt tuning — a detail omitted from the original paper
by mistake. When evaluated with the standard GLUE script, SparseFormer achieves
91.7%. We acknowledge the oversight and have released the corrected evaluation
pipeline.
```

**paper-e-survey.md:**
```markdown
SparseFormer is the 3rd most-cited transformer efficiency paper of 2024 despite
well-documented replication issues. This paradox — high citations, contested
results — reflects a broader pattern in ML research where novel architectures
gain traction faster than the community can verify them.
```

### RAG Query & Result

**Query:** *"How well does SparseFormer perform?"*

**RAG Process:**
- Embed query → "SparseFormer perform"
- Top-3 results:
  1. paper-a-claims.md (score: 0.91) — "94.2% accuracy, 40% fewer params"
  2. paper-d-defense.md (score: 0.78) — "91.7% with standard eval"
  3. paper-a-claims.md (score: 0.72) — duplicate

Note: papers B (replication failure), C (latency problem), and E (citation paradox) all score <0.65 because they use words like "replicate," "latency," "paradox" — semantically distant from "perform."

**RAG Answer:**
> SparseFormer achieves 94.2% accuracy on GLUE with 40% fewer parameters than a
> standard transformer. A corrected evaluation pipeline reports 91.7% accuracy.

**What RAG MISSED:**
- ❌ Replication attempts only got 89.1% (paper-b — never retrieved)
- ❌ Dynamic head pruning makes it 2.3x SLOWER, not faster (paper-c — never retrieved; "latency" ≠ "performance")
- ❌ The original eval pipeline was non-standard (paper-d mentions it but the "mistake" framing was softened by RAG's lack of B's context)
- ❌ It's highly cited DESPITE replication issues (paper-e — never retrieved)
- ❌ The paper-d defense looks reasonable in isolation; with B and C, it looks like damage control

**RAG told a sanitized version of the story.** The most critical papers — the replication failure and the latency problem — were invisible.

### Wiki Solution

**Agent ingests all 5 papers.** Builds:

**concepts/sparseformer.md:**
```markdown
---
title: SparseFormer
created: 2025-07-15
updated: 2025-07-15
type: concept
tags: [architecture, training, controversy]
sources:
  - raw/papers/paper-a-claims.md
  - raw/papers/paper-b-replication.md
  - raw/papers/paper-c-contradiction.md
  - raw/papers/paper-d-defense.md
  - raw/papers/paper-e-survey.md
confidence: medium
contested: true
---

# SparseFormer

## Claims vs Reality

| Claim | Source | Year | Status | Notes |
|---|---|---|---|---|
| 94.2% GLUE, 40% fewer params | Paper A | 2024 | ❌ Not replicated | Used non-standard eval pipeline |
| 89.1% on replication | Paper B | 2024 | ✓ Independent | 5 runs, published code |
| 2.3x SLOWER than dense transformer | Paper C | 2024 | ✓ Measured | Pruning overhead negates param savings |
| 91.7% with standard eval | Paper D | 2024 | ⚠️ Author correction | Acknowledged original methods omission |
| 3rd most-cited despite issues | Paper E | 2025 | ✓ Survey finding | "Citation paradox" |

## Synthesis
SparseFormer's headline claim (94.2% GLUE) was not replicated. Independent
evaluation found 89.1% ± 1.3%. The original result used an undisclosed custom
eval pipeline. When corrected, authors reported 91.7%. Separately, the dynamic
head pruning that enables parameter reduction introduces 2.3x inference latency,
making SparseFormer a net-negative for deployment efficiency despite parameter
savings — the exact opposite of its stated goal. ^[raw/papers/paper-c-contradiction.md]

Despite these issues, the paper is the 3rd most-cited transformer efficiency
paper of 2024 — a "citation paradox" documented by Paper E. ^[raw/papers/paper-e-survey.md]

**Bottom line:** Novel architecture, unreplicated headline result, slower in
practice, highly cited anyway. Approach with caution.
```

**Query resolution:**
1. Read index.md → find `concepts/sparseformer.md`
2. Read the page → full claim matrix with statuses
3. Follow wikilinks to related pages (GLUE benchmark, dynamic pruning, transformer efficiency)
4. Synthesize with confidence levels

**Wiki Answer:**
> SparseFormer is contested. The headline claim of 94.2% GLUE accuracy was not
> replicated — independent evaluation found 89.1%. The authors later acknowledged
> using a non-standard eval pipeline and corrected to 91.7%. Additionally,
> despite claiming efficiency, SparseFormer is 2.3x slower than a dense transformer
> at inference because the dynamic pruning overhead exceeds the parameter savings.
> Despite these issues, it remains highly cited (3rd most-cited in its category).
> Verdict: approach with caution.

---

## Example 3: The Regulatory Web (Legal/Compliance)

### The Raw Documents

**regulation-a.md:**
```markdown
The Digital Services Act (DSA), effective January 2025, requires platforms with
over 45 million monthly active EU users to conduct annual risk assessments for
algorithmic amplification, illegal content, and electoral manipulation.
Non-compliance penalties: up to 6% of global annual revenue.
```

**regulation-b.md:**
```markdown
The EU AI Act, effective June 2025, classifies "general-purpose AI systems"
as high-risk if they are used in critical infrastructure, employment decisions,
or law enforcement. Providers must maintain technical documentation, implement
human oversight, and register with the EU AI Office.
```

**guidance-note.md:**
```markdown
EU Commission Guidance Note 2025/07 clarifies that a platform's recommendation
algorithm, if powered by a general-purpose AI system, is subject to BOTH the
DSA risk assessment requirements AND the AI Act high-risk classification.
Platforms must perform a joint assessment covering DSA systemic risk factors
AND AI Act safety requirements in a single integrated filing.
```

**enforcement-action.md:```markdown
The EU Commission fined SocialNet €400 million today for failing to conduct
a joint DSA/AI Act risk assessment of its recommendation algorithm. SocialNet
argued it had separately complied with each regulation, but the Commission
ruled that Guidance Note 2025/07 requires an integrated assessment. This is
the first enforcement action combining both regulations.
```

**legal-analysis.md:**
```markdown
The SocialNet fine establishes a troubling precedent: the integrated assessment
requirement was only published 3 months before the enforcement action. Platforms
are now expected to continuously monitor Commission guidance notes — which have
no legislative status — or face penalties. Legal scholars warn this blurs the
line between binding regulation and non-binding guidance.
```

### RAG Query & Result

**Query:** *"What are the DSA and AI Act requirements for recommendation algorithms?"*

**RAG Process:**
- Top-3 results:
  1. regulation-a.md — DSA requirements
  2. regulation-b.md — AI Act requirements
  3. guidance-note.md — joint assessment requirement

**RAG Answer:**
> Recommendation algorithms on large platforms must comply with DSA risk
> assessments (for platforms with 45M+ EU users) and may be classified as
> high-risk under the AI Act if powered by general-purpose AI. A joint
> assessment is required per Guidance Note 2025/07.

**What RAG MISSED:**
- ❌ The €400M fine for getting it wrong (enforcement-action.md — "fine" doesn't match "requirements")
- ❌ The legal controversy: guidance notes now act as binding regulation (legal-analysis.md — too meta)
- ❌ The timeline: only 3 months between guidance and enforcement
- ❌ The precedent: "first enforcement action combining both regulations"

**RAG returned correct but INCOMPLETE advice.** It told you the rules but not the risk.

### Wiki Solution

**Agent ingests all 5.** Builds:

**concepts/dsa-ai-act-recommendation-compliance.md:**
```markdown
---
title: DSA & AI Act — Recommendation Algorithm Compliance
created: 2025-07-15
updated: 2025-07-15
type: concept
tags: [regulation, compliance, controversy]
sources:
  - raw/regulations/regulation-a.md
  - raw/regulations/regulation-b.md
  - raw/regulations/guidance-note.md
  - raw/regulations/enforcement-action.md
  - raw/regulations/legal-analysis.md
confidence: high
---

## Requirements
Platforms with 45M+ EU users using AI-powered recommendation:
1. DSA annual risk assessment (algorithmic amplification, illegal content, electoral) ^[raw/regulations/regulation-a.md]
2. AI Act high-risk classification (if general-purpose AI) with technical docs, human oversight, registration ^[raw/regulations/regulation-b.md]
3. JOINT integrated assessment combining both per Guidance Note 2025/07 ^[raw/regulations/guidance-note.md]
4. Penalty: up to 6% global annual revenue per regulation (potentially cumulative)

## Enforcement Risk (HIGH)
SocialNet fined €400M — first combined DSA + AI Act enforcement. ^[raw/regulations/enforcement-action.md]
- Argued separate compliance was sufficient → rejected
- Guidance Note published only 3 months before enforcement
- Precedent: guidance notes treated as binding regulation

## Legal Controversy
Scholars warn this blurs binding regulation vs. non-binding guidance. ^[raw/regulations/legal-analysis.md]
Platforms must now monitor ALL guidance notes — not just legislation — or risk fines.
```

---

## Example 4: The Dependency Web (Software Documentation)

(*Abbreviated — see [approach.md](approach.md) Part 2, Failure Mode 4 for the full version*)

---

## Pattern Analysis: What All Four Failures Share

| Failure | Root Cause | Why RAG Can't Fix It | Why Wiki Does |
|---|---|---|---|
| Acquisition story | Causal chain across 4 docs | Chunks in different embedding regions | Entity page preserves timeline |
| Contested method | Citation network; critique docs use different vocabulary | "Replication" ≠ "performance" in embedding space | Concept page with claim matrix |
| Regulatory web | Interdependent regulations + enforcement | "Fine" doesn't match "requirement" query | Cross-referenced compliance page |
| Dependency graph | Technical prerequisites spread across files | Sparse keyword matches | Dependency section with versions + bugs |

**The common thread:** All four involve documents that are **related by structure** (causality, citation, regulation, dependency), not by **semantic similarity**. RAG assumes semantic similarity captures relevance. In these cases, it doesn't.

The wiki pattern captures structure explicitly — through `[[wikilinks]]`, timelines, claim matrices, dependency sections. That structure is what makes retrieval complete.

---

*Back to [approach.md](approach.md) for the architecture and fine-tuning discussion.*
