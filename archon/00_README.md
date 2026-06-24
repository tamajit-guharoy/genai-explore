# Archon Tutorial — From Basics to Advanced

> **Archon** is the first open-source harness builder for AI coding — a workflow engine that makes AI-driven development deterministic and repeatable. Define your dev process as a YAML DAG once, and run it identically from CLI, Web, Slack, Telegram, or GitHub.
>
> - GitHub: <https://github.com/coleam00/Archon>
> - Docs: <https://archon.diy/docs/>
> - License: MIT | Stars: 22.5k+

---

## Prerequisites

| Requirement | Details |
|---|---|
| **Bun** | 1.x+ (JavaScript runtime) |
| **Claude Code** | CLI installed + Anthropic API key |
| **GitHub CLI** | `gh` authenticated for PRs and issues |
| **Git** | 2.30+ (worktree support) |

---

## Tutorial Index

Each file is self-contained. Start at 01 and work through sequentially, or jump to any topic.

| # | File | Topics |
|---|---|---|
| 01 | `01-getting-started.md` | Architecture, DAG engine, isolation, five pillars, comparison to OpenHands/Hermes |
| 02 | `02-installation.md` | Setup: Bun, Claude Code, gh CLI, config files, Docker, troubleshooting |
| 03 | `03-workflow-basics.md` | YAML structure, depends_on, DAG execution, trigger rules, context modes |
| 04 | `04-node-types.md` | Complete reference: prompt, command, bash, script, loop, approval, cancel + all fields |
| 05 | `05-advanced-workflows.md` | Conditional branching, structured output, variable substitution, retry, isolation |
| 06 | `06-real-world-recipes.md` | 6 production recipes: bug fix, review swarm, feature scaffold, dep update, migration, CI merge |
| 07 | `07-appendix.md` | Cheat sheets, CLI reference, 17 built-in workflows, glossary, YAML/command templates |

**Comprehensive version:** `ARCHON_TUTORIAL.md` — 21 sections covering everything in one file.

---

## Example Files

Standalone, runnable examples — copy into your project and use immediately.

### Workflows (`examples/workflows/`)

| # | File | Demonstrates |
|---|---|---|
| 01 | `01-hello-world.yaml` | Simplest possible workflow |
| 02 | `02-two-step.yaml` | `depends_on`, `context: fresh` |
| 03 | `03-build-feature.yaml` | prompt, loop, bash, approval — canonical example |
| 04 | `04-smart-issue-fix.yaml` | **All 7 node types**: bash, script, prompt, command, loop, cancel + structured output, `when:`, `trigger_rule` |
| 05 | `05-review-swarm.yaml` | 5 parallel specialized reviewers → synthesize |
| 06 | `06-dependency-update.yaml` | script node, cancel guard, conditional execution |
| 07 | `07-bug-fix.yaml` | Complete bug fix pipeline: fetch → reproduce → fix → test → PR |
| 08 | `08-migration.yaml` | Code migration with validation at every step |

### Commands (`examples/commands/`)

| File | Purpose |
|---|---|
| `investigate-bug.md` | Phased bug investigation command |
| `plan-feature.md` | Feature planning with task breakdown |
| `fix-bug.md` | Bug fix with validation steps |

### Scripts (`examples/scripts/`)

| File | Runtime | Purpose |
|---|---|---|
| `parse-labels.ts` | bun | Parse GitHub issue labels from JSON |
| `calculate-metrics.py` | uv | Calculate pass/fail metrics from test output |

### Setup Script

```bash
# Copy all examples into your project
bash examples/setup.sh /path/to/your/project
```

---

## Quick Start

```bash
# Install Archon
curl -fsSL https://archon.diy/install | bash

# Full setup
git clone https://github.com/coleam00/Archon
cd Archon && bun install && claude
# Say: "Set up Archon"

# Use in your project
cd /path/to/your/project
claude
> Use archon to fix issue #42
> What archon workflows do I have?

# Bootstrap examples
bash /path/to/archon-tutorial/examples/setup.sh .
```

---

## Key Concepts at a Glance

| Concept | What It Is |
|---|---|
| **Workflow** | A YAML file defining a DAG of nodes that orchestrate AI coding tasks |
| **Node** | A single execution step — AI-driven (prompt, command) or deterministic (bash, script) |
| **DAG** | Directed Acyclic Graph — nodes with dependencies, executed concurrently where possible |
| **Isolation** | Every run gets its own git worktree; parallel runs don't conflict |
| **Command** | A `.md` file in `.archon/commands/` with YAML frontmatter + prompt body |
| **Script Node** | TypeScript (via `bun`) or Python (via `uv`) for deterministic data transforms |
| **Loop Node** | Iterative AI execution until a completion signal |
| **Approval Node** | Human-in-the-loop gate that pauses for review |
| **Variable Substitution** | `$nodeId.output`, `$ARGUMENTS`, `$ARTIFACTS_DIR` injected at runtime |

---

## Sources

- [Archon GitHub Repository](https://github.com/coleam00/Archon)
- [Archon Documentation](https://archon.diy/docs/)
- [The Book of Archon](https://archon.diy/book/)
- [DeepWiki: coleam00/Archon](https://deepwiki.com/coleam00/Archon)
- [Authoring Workflows Guide](https://github.com/coleam00/Archon/blob/dev/packages/docs-web/src/content/docs/guides/authoring-workflows.md)

*Tutorial written June 2026 against Archon (coleam00/Archon).*
