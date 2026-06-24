# 01 — What Is Archon?

**Goal:** Understand what Archon is, its architecture, how it compares to alternatives, and when to use it.

---

## 1.1 The Problem Archon Solves

When you ask an AI agent to "fix this bug", what happens depends on the model's mood. It might skip planning, forget to run tests, or write a PR description that ignores your template. Every run is different.

**Archon fixes this by wrapping the AI in a harness.** A harness controls and monitors how a component executes. In Archon:

- **You** define the phases, validation gates, and artifacts (as YAML)
- **The AI** fills in the intelligence at each step
- **Archon** handles routing, context passing, isolation, and error recovery

The result: plan → implement → validate → review → PR. Every. Single. Time.

## 1.2 The Core Metaphor

| Tool | What it standardized | How |
|---|---|---|
| **Dockerfiles** | Infrastructure builds | Declarative instructions for container creation |
| **GitHub Actions** | CI/CD pipelines | YAML workflows for build/test/deploy |
| **Archon** | AI coding workflows | YAML DAGs for plan/implement/review/ship |

Just as a Dockerfile guarantees the same container is built every time, an Archon workflow guarantees the same development process is followed every time.

## 1.3 Architecture Overview

Archon is a **TypeScript monorepo** using **Bun** for execution with **SQLite/PostgreSQL** for persistence.

```
┌──────────────────────────────────────────────────────────┐
│                   ACCESS SURFACES                         │
│   CLI ("use archon") │ Web UI │ Slack │ Telegram │ GitHub │
├──────────────────────────────────────────────────────────┤
│                   ORCHESTRATION                           │
│   @archon/core — routing, session management, config      │
├──────────────┬───────────────────┬───────────────────────┤
│  WORKFLOWS   │    AI CLIENTS     │     ISOLATION          │
│  Engine      │  Claude / Codex   │  Git Worktrees         │
│  YAML→DAG    │  SDK integration  │  Per-run environments  │
├──────────────┴───────────────────┴───────────────────────┤
│                   PERSISTENCE                             │
│     SQLite (local) / PostgreSQL (production)              │
│     7 tables: codebases, conversations, sessions,        │
│     workflow_runs, isolation_environments, messages,      │
│     workflow_events                                       │
└──────────────────────────────────────────────────────────┘
```

### Monorepo Package Structure

| Package | Responsibility | Dependencies |
|---|---|---|
| `@archon/paths` | Path resolution, logging | None (foundation) |
| `@archon/core` | Orchestrator, DB adapters, command handling | paths |
| `@archon/workflows` | YAML parser, DAG engine, node type definitions | core |
| `@archon/isolation` | Git worktree lifecycle management | core |
| `@archon/adapters` | GitHub, Slack, Discord, Telegram integrations | core |

## 1.4 The DAG Execution Model

Workflows are **Directed Acyclic Graphs**. This is the heart of Archon.

Key properties:
- **Nodes** are execution steps — prompts, shell commands, scripts, loops, approvals
- **Edges** are dependencies — `depends_on: [node_a, node_b]`
- **No cycles** — infinite loops only possible inside `loop` nodes, not at the graph level
- **Parallel by default** — nodes without dependencies run concurrently
- **Deterministic ordering** — same graph → same execution order, every time

### Example: 5-Node Review Swarm

```
       ┌──────────┐
       │ fetch-pr │
       └────┬─────┘
            │
   ┌────────┼────────┬────────┬────────┐
   │        │        │        │        │
┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐ ┌──▼──┐
│sec  │ │perf │ │style│ │logic│ │tests│   ← 5 reviewers IN PARALLEL
└──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘ └──┬──┘
   │        │        │        │        │
   └────────┴────────┴────────┴────────┘
                     │
              ┌──────▼──────┐
              │ synthesize  │
              └─────────────┘
```

## 1.5 The Isolation System — Git Worktrees

Every workflow run gets its own **git worktree** — a separate working directory linked to the same repository.

```
Main repo:     /home/user/project                    (branch: main)
Worktree 1:    ~/.archon/worktrees/abc123/          (branch: archon/task-abc123)
Worktree 2:    ~/.archon/worktrees/def456/          (branch: archon/task-def456)
```

**Why it matters:** Run 5 fixes in parallel with zero conflicts. Each worktree has its own branch and working tree but shares one `.git` directory — no file conflicts, no branch collisions.

## 1.6 The Five Pillars

| Pillar | What it means |
|---|---|
| **Repeatable** | Same workflow, same sequence, every time |
| **Isolated** | Every run gets its own git worktree — zero conflicts |
| **Fire and forget** | Kick off a workflow, come back to a finished PR |
| **Composable** | Mix deterministic nodes (bash) with AI nodes (prompts). AI only where it adds value. |
| **Portable** | Workflows in `.archon/workflows/` committed to repo. Same behavior from CLI, Web, Slack, Telegram, GitHub. |

## 1.7 Archon vs OpenHands vs Hermes

| Dimension | Archon | OpenHands | Hermes |
|---|---|---|---|
| **Category** | Workflow Engine | Agent Platform | Personal Agent |
| **Scope** | SDLC pipelines | Dev task resolution | General purpose |
| **Core idea** | YAML DAG harness for AI coding | Autonomous coding agents in sandboxes | Persistent agent that grows with you |
| **Isolation** | Git worktrees | Docker containers | N/A (user's machine) |
| **Persistence** | Stateless per run | Session-level | Cross-session memory + skills |
| **Multi-agent** | DAG nodes in parallel | Sub-agents + orchestrators | Subagents + delegation |
| **Learning** | Static YAML workflows | Static configuration | Self-improving skills |
| **Stack** | TypeScript + Bun | Python | Python |
| **Stars** | 22.5k | 77.9k | N/A (newer) |

**When to pick Archon:** You want to encode your team's dev process into repeatable YAML and run it identically from CLI, Slack, or CI. You value deterministic process over agent autonomy.

---

**Next:** [02 — Installation & Setup](./02-installation.md)
