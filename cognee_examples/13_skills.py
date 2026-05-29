"""
13_skills.py — Create and demonstrate a custom Cognee skill.

The Cognee skills system (v0.5.4rc1+) enables self-improving capabilities
that observe their own performance and auto-correct. This example shows the
skill pattern and lifecycle, even though the full cognee-skills package
may require additional dependencies.

A skill has six lifecycle phases:
  1. Ingest  — parse skill definition
  2. Route   — match requests to skills
  3. Execute — run the skill
  4. Observe — record outputs
  5. Evaluate — score performance
  6. Amend   — auto-correct if score below threshold

Prerequisites:
    pip install cognee
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum


# ── Skill framework (illustrative — uses core patterns) ────────────────


class SkillStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    AMENDING = "amending"


@dataclass
class SkillResult:
    """Output of a skill execution with evaluation metrics."""
    success: bool
    output: dict
    metrics: dict = field(default_factory=dict)
    needs_amendment: bool = False
    amendment_suggestions: list[str] = field(default_factory=list)


class Skill:
    """Base class for Cognee skills.

    In production, skills are packaged as microservice containers and
    registered with the skill orchestration engine via REST or MCP.
    """

    def __init__(self, name: str, description: str, metrics: list[str] | None = None):
        self.name = name
        self.description = description
        self.target_metrics = metrics or ["accuracy", "completeness"]
        self.auto_amend_threshold = 0.75
        self.status = SkillStatus.IDLE
        self.run_history: list[SkillResult] = []

    async def execute(self, input_data: dict) -> SkillResult:
        """Override this with skill-specific logic."""
        raise NotImplementedError

    async def evaluate(self, result: SkillResult) -> SkillResult:
        """Score the output against target metrics."""
        # In production, this uses an LLM to score outputs.
        # Here we use simple heuristics for demonstration.
        metrics = {}
        for metric in self.target_metrics:
            if metric == "accuracy":
                metrics["accuracy"] = self._score_accuracy(result)
            elif metric == "completeness":
                metrics["completeness"] = self._score_completeness(result)
            else:
                metrics[metric] = 0.8  # Placeholder

        result.metrics = metrics
        avg_score = sum(metrics.values()) / len(metrics) if metrics else 0
        result.needs_amendment = avg_score < self.auto_amend_threshold
        return result

    async def amend(self, result: SkillResult, input_data: dict) -> SkillResult:
        """Auto-correct the output if quality is below threshold."""
        self.status = SkillStatus.AMENDING
        # In production, this triggers an LLM-based correction pipeline.
        result.amendment_suggestions = [
            f"Re-extract entities with higher temperature",
            f"Validate output against {self.name} schema",
        ]
        return result

    def _score_accuracy(self, result: SkillResult) -> float:
        """Simplified accuracy scoring — replace with LLM-based eval in production."""
        output = result.output
        score = 1.0
        # Penalize empty outputs
        if not output:
            score -= 0.5
        # Penalize very short outputs (likely incomplete)
        if isinstance(output.get("summary", ""), str):
            if len(output["summary"]) < 50:
                score -= 0.2
        return max(score, 0.0)

    def _score_completeness(self, result: SkillResult) -> float:
        """Simplified completeness scoring."""
        output = result.output
        if not output:
            return 0.0
        # More fields = more complete (simplified)
        filled_fields = sum(1 for v in output.values() if v)
        total_fields = len(output) if output else 1
        return min(filled_fields / total_fields, 1.0)


# ── Custom skill implementation ────────────────────────────────────────


class ContractAnalyzerSkill(Skill):
    """Extracts key information from contract text."""

    def __init__(self):
        super().__init__(
            name="contract_analyzer",
            description="Extracts parties, dates, obligations, and key terms "
                        "from legal contracts with high accuracy.",
            metrics=["accuracy", "completeness", "entity_citation"],
        )
        self.auto_amend_threshold = 0.70

    async def execute(self, input_data: dict) -> SkillResult:
        """Extract contract entities."""
        text = input_data.get("text", "")
        if not text:
            return SkillResult(
                success=False,
                output={},
                metrics={"accuracy": 0.0, "completeness": 0.0},
            )

        # In production, this uses Cognee's entity extraction pipeline.
        # For this example, we simulate extraction.
        extracted = {
            "parties": ["Acme Corp", "Beta Industries"],
            "effective_date": "2026-01-15",
            "termination_date": "2028-01-15",
            "governing_law": "Delaware",
            "payment_terms": "Net 30",
            "liability_cap": "$5,000,000",
            "key_obligations": [
                "Acme Corp shall deliver quarterly reports",
                "Beta Industries shall provide technical support 24/7",
            ],
            "summary": "Two-year service agreement between Acme Corp and "
                       "Beta Industries for quarterly reporting and "
                       "technical support services.",
        }

        return SkillResult(success=True, output=extracted)

    async def run_with_lifecycle(self, input_data: dict) -> SkillResult:
        """Execute the full skill lifecycle."""
        # Phase 1-2: Ingest & Route (handled by orchestration engine)

        # Phase 3: Execute
        self.status = SkillStatus.RUNNING
        result = await self.execute(input_data)

        # Phase 4-5: Observe & Evaluate
        result = await self.evaluate(result)

        # Phase 6: Amend if needed
        if result.needs_amendment:
            result = await self.amend(result, input_data)

        self.status = SkillStatus.COMPLETED
        self.run_history.append(result)
        return result


async def main():
    print("Demonstrating the Cognee Skills pattern")
    print("=" * 60)

    # ── Create and run the skill ───────────────────────────────────────
    skill = ContractAnalyzerSkill()

    sample_contract = """
    MASTER SERVICES AGREEMENT between Acme Corp and Beta Industries.
    Effective Date: January 15, 2026. Term: 2 years.
    Governing Law: State of Delaware.
    Payment: Net 30 days.
    Liability Cap: $5,000,000.
    Acme Corp shall deliver quarterly performance reports.
    Beta Industries shall provide 24/7 technical support.
    """

    print(f"\nSkill: {skill.name}")
    print(f"Description: {skill.description}")
    print(f"Target metrics: {skill.target_metrics}")
    print(f"Auto-amend threshold: {skill.auto_amend_threshold}")

    print("\n" + "-" * 40)
    print("Running skill lifecycle...")
    result = await skill.run_with_lifecycle({"text": sample_contract})

    # ── Display results ────────────────────────────────────────────────
    print(f"\nStatus: {skill.status.value}")
    print(f"Success: {result.success}")
    print(f"\nExtracted data:")
    for key, value in result.output.items():
        if key != "summary":
            print(f"  {key}: {value}")
    print(f"\n  Summary: {result.output.get('summary', 'N/A')}")

    print(f"\nEvaluation metrics:")
    for metric, score in result.metrics.items():
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"  {metric}: {bar} {score:.0%}")

    print(f"\nNeeds amendment: {result.needs_amendment}")
    if result.amendment_suggestions:
        print("Amendment suggestions:")
        for s in result.amendment_suggestions:
            print(f"  • {s}")

    print(f"\nRun history length: {len(skill.run_history)}")
    print("\nIn production, skills are auto-deployed as microservices")
    print("and the orchestration engine composes them for complex tasks.")


if __name__ == "__main__":
    asyncio.run(main())
