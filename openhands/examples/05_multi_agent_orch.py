"""
05_multi_agent_orch.py -- Multi-agent orchestration example
Based on Section 11 of openhands-tutorial.md

Demonstrates task decomposition and parallel agent coordination pattern.
Note: This is a structural example -- actual agent execution requires API keys.
"""

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class SubTask:
    """A single agent-sized work unit."""
    id: str
    description: str
    dependencies: list[str]  # IDs of tasks that must complete first
    status: str = "pending"
    result: Optional[str] = None


def decompose_task(large_task: str) -> list[SubTask]:
    """
    Break a large task into parallelizable, single-commit chunks.

    Properties of a good sub-task:
    - One-shottable: agent can complete in one focused session
    - Single-commit: changes fit in one git commit
    - Parallelizable: doesn't depend on other sub-tasks
    - Verifiable: human can judge correct/incorrect quickly
    """
    if "migrate" in large_task.lower() and "redux" in large_task.lower():
        return [
            SubTask("A", "Migrate store module: src/store/*.ts", []),
            SubTask("B", "Migrate components using useSelector: 12 files", []),
            SubTask("C", "Migrate components using useDispatch: 8 files", []),
            SubTask("D", "Update tests for migrated modules", ["A"]),
            SubTask("E", "Update tests for migrated components", ["B", "C"]),
            SubTask("F", "Remove Redux dependencies, update package.json",
                    ["A", "B", "C"]),
        ]
    return [
        SubTask("1", f"Part 1 of: {large_task}", []),
        SubTask("2", f"Part 2 of: {large_task}", []),
    ]


def schedule_tasks(tasks: list[SubTask]) -> list[list[SubTask]]:
    """Schedule tasks in dependency-respecting parallel batches."""
    completed: set[str] = set()
    batches = []
    remaining = list(tasks)

    while remaining:
        batch = [
            t for t in remaining
            if all(dep in completed for dep in t.dependencies)
        ]
        if not batch:
            raise RuntimeError(
                f"Circular dependency: {remaining}"
            )
        batches.append(batch)
        for t in batch:
            completed.add(t.id)
            remaining.remove(t)

    return batches


# Example usage
big_task = "Migrate the entire frontend from Redux to Zustand"
subtasks = decompose_task(big_task)
batches = schedule_tasks(subtasks)

print(f"Task: {big_task}")
print(f"Decomposed into {len(subtasks)} sub-tasks "
      f"across {len(batches)} batches:")
for i, batch in enumerate(batches):
    print(f"\n  Batch {i+1} (parallel):")
    for t in batch:
        deps = (f" [depends on: {', '.join(t.dependencies)}]"
                if t.dependencies else "")
        print(f"    {t.id}: {t.description}{deps}")

print(f"\nEstimated wall-clock time: {len(batches)} agent-sessions "
      f"(vs 1 very long session)")
print(f"Parallelism gain: {len(subtasks) / len(batches):.1f}x")
