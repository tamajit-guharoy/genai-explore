# Archon — The Complete Tutorial

> **Archon** (coleam00/Archon) is the first open-source harness builder for AI coding — a workflow engine that makes AI-driven development deterministic and repeatable. Define your dev process as a YAML DAG once, and run it identically from CLI, Web, Slack, Telegram, or GitHub.
>
> - **Repo:** <https://github.com/coleam00/Archon>
> - **Docs:** <https://archon.diy/docs/>
> - **Stars:** 22.5k+ | **License:** MIT | **Stack:** TypeScript + Bun

---

## Table of Contents

1. [What Is Archon?](#1-what-is-archon)
2. [Why Archon Exists](#2-why-archon-exists)
3. [Architecture Deep Dive](#3-architecture-deep-dive)
4. [Installation & Setup](#4-installation--setup)
5. [Your First Workflow](#5-your-first-workflow)
6. [Node Types — Complete Reference](#6-node-types--complete-reference)
7. [Commands — The Building Blocks](#7-commands--the-building-blocks)
8. [Variable Substitution System](#8-variable-substitution-system)
9. [Conditional Branching](#9-conditional-branching)
10. [Script Nodes — TypeScript & Python](#10-script-nodes--typescript--python)
11. [Loop Nodes & Approval Gates](#11-loop-nodes--approval-gates)
12. [Structured Output](#12-structured-output)
13. [Isolation System — Git Worktrees](#13-isolation-system--git-worktrees)
14. [Web UI & Dashboard](#14-web-ui--dashboard)
15. [Multi-Platform Access](#15-multi-platform-access)
16. [The 17 Built-in Workflows](#16-the-17-built-in-workflows)
17. [Configuration Reference](#17-configuration-reference)
18. [Advanced Workflow Patterns](#18-advanced-workflow-patterns)
19. [Real-World Recipe Book](#19-real-world-recipe-book)
20. [Archon vs OpenHands vs Hermes](#20-archon-vs-openhands-vs-hermes)
21. [Troubleshooting & Tips](#21-troubleshooting--tips)

---

## 1. What Is Archon?

Archon is a **workflow engine for AI coding agents**. It doesn't replace Claude Code — it *harnesses* it.

The core metaphor: **Dockerfiles for AI coding.** Just as a Dockerfile defines exactly how a container is built (every time, identically), an Archon workflow defines exactly how an AI agent should approach a development task — plan, implement, validate, review, ship — every time, identically.

### The Harness Builder Concept

A "harness" in software testing wraps and controls a component's execution. Archon applies this to AI agents:

- **You** define the phases, gates, and artifacts
- **The AI** fills in the intelligence at each step
- **Archon** handles routing, context passing, isolation, and error recovery

Without Archon, asking an AI to "fix this bug" is a coin toss — it might skip tests, forget your PR template, or wander off exploring unrelated code. With Archon, the sequence is deterministic: classify → investigate → implement → validate → review → PR. Every time.

### Key Numbers

- **22.5k+ GitHub stars**, 3.4k forks
- **TypeScript monorepo** on Bun with SQLite/PostgreSQL persistence
- **7 node types** for composing workflows
- **17 built-in workflows** covering bug fixes, PR reviews, feature scaffolding, and more
- **4 access surfaces:** CLI, Web UI, Slack/Telegram/Discord, GitHub integration

---

## 2. Why Archon Exists

### The Problem It Solves

```text
Without Archon:
You: "Fix issue #42"
AI:  *writes code* "Done!" (didn't run tests, skipped the PR template, missed edge case)

With Archon:
You: "Use archon to fix issue #42"
Archon → classify → investigate → plan → implement (loop until tests pass) → validate → review → create PR
Result: A properly formatted PR with passing tests and review comments
```

The gap between "an AI that can code" and "an AI coding workflow you can trust" is where Archon lives.

### The Five Pillars

| Pillar | What it means |
|---|---|
| **Repeatable** | Same workflow, same sequence, every time. Plan → Implement → Validate → Review → PR. |
| **Isolated** | Every workflow run gets its own git worktree. Run 5 fixes in parallel with zero conflicts. |
| **Fire and forget** | Kick off a workflow, go do other work. Come back to a finished PR with review comments. |
| **Composable** | Mix deterministic nodes (bash scripts, tests, git ops) with AI nodes (planning, coding, review). AI only runs where it adds value. |
| **Portable** | Workflows live in `.archon/workflows/`, committed to your repo. They work identically from CLI, Web UI, Slack, Telegram, or GitHub. |

---

## 3. Architecture Deep Dive

### System Overview

```text
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│   CLI    │  │  Web UI  │  │  Slack   │  │ Telegram │
└────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
     └──────────────┴────────────┴──────────────┘
                         │
              ┌──────────▼──────────┐
              │   @archon/core      │
              │   (Orchestrator)     │
              └──────────┬──────────┘
                         │
     ┌───────────────────┼───────────────────┐
     │                   │                   │
┌────▼─────┐    ┌────────▼────────┐   ┌──────▼──────┐
│Workflows │    │   AI Clients    │   │  Isolation  │
│  Engine  │    │ (Claude, Codex) │   │ (Worktrees) │
└──────────┘    └─────────────────┘   └─────────────┘
                         │
              ┌──────────▼──────────┐
              │  SQLite / PostgreSQL │
              │      (7 tables)     │
              └─────────────────────┘
```

### Monorepo Package Structure

| Package | Responsibility |
|---|---|
| `@archon/core` | Central orchestrator, database adapters, command handling |
| `@archon/workflows` | YAML parsing, DAG execution engine, node type definitions |
| `@archon/isolation` | Git worktree management for isolated execution |
| `@archon/adapters` | GitHub, Slack, Discord, Telegram platform integrations |
| `@archon/paths` | Path resolution utilities and logging (zero dependencies) |

### The DAG Execution Model

Workflows are **Directed Acyclic Graphs**. The engine:

1. Parses the YAML into a node graph
2. Resolves `depends_on` to determine execution order
3. Runs independent nodes concurrently (`Promise.allSettled`)
4. Passes outputs from upstream nodes to downstream nodes via variable substitution
5. Handles loops, conditionals, retries, and timeouts

**Example — a 3-node DAG with parallelism:**

```text
       ┌──────────┐
       │  plan    │
       └────┬─────┘
            │
    ┌───────┼───────┐
    │       │       │
┌───▼───┐ ┌▼────┐ ┌▼────┐
│ impl  │ │test │ │docs │    ← all three run in parallel after plan
└───┬───┘ └──┬──┘ └──┬──┘
    └───────┼───────┘
            │
       ┌────▼─────┐
       │ review   │
       └──────────┘
```

---

## 4. Installation & Setup

### Full Setup (5 minutes)

**Prerequisites:** Bun, Claude Code, GitHub CLI

```bash
# Install Bun
curl -fsSL https://bun.sh/install | bash

# Install GitHub CLI
brew install gh          # macOS
winget install GitHub.cli  # Windows
sudo apt install gh      # Debian/Ubuntu

# Install Claude Code
curl -fsSL https://claude.ai/install.sh | bash

# Clone and set up Archon
git clone https://github.com/coleam00/Archon
cd Archon
bun install
claude
# Then say: "Set up Archon"
```

The wizard installs the CLI, configures credentials and platforms, and copies the Archon skill into your target project.

### Quick Install (30 seconds)

For users who already have Claude Code:

```bash
# macOS / Linux
curl -fsSL https://archon.diy/install | bash

# Windows (PowerShell)
irm https://archon.diy/install.ps1 | iex

# Homebrew
brew install coleam00/archon/archon
```

**Important:** Set `CLAUDE_BIN_PATH` for compiled binaries:
```bash
export CLAUDE_BIN_PATH="$HOME/.local/bin/claude"    # macOS/Linux
$env:CLAUDE_BIN_PATH = "$env:USERPROFILE\.local\bin\claude.exe"  # Windows
```

Or configure in `~/.archon/config.yaml`:
```yaml
assistants:
  claude:
    claudeBinaryPath: /home/user/.local/bin/claude
```

### Docker Deployment

```bash
git clone https://github.com/coleam00/Archon
cd Archon
cp docker-compose.override.example.yml docker-compose.override.yml
# Edit docker-compose.override.yml with your API keys
docker compose up -d
```

### Verify Installation

```bash
archon --version

# Start Web UI
archon serve

# Or from source
cd Archon && bun run dev
```

### Configuration Files

| File | Purpose |
|---|---|
| `~/.archon/config.yaml` | Provider, model, platform tokens, assistant paths |
| `.archon/workflows/` | Your custom workflow YAML files (committed to repo) |
| `.archon/commands/` | Custom command `.md` files |
| `.archon/scripts/` | TypeScript/Python scripts for script nodes |
| `~/.archon/workflows/` | Global workflows (apply to all projects) |

---

## 5. Your First Workflow

### The Simplest Possible Workflow

Create `.archon/workflows/hello.yaml` in your project:

```yaml
name: hello-world
description: My first Archon workflow

nodes:
  - id: greet
    prompt: "Say hello and list the files in the current directory."
```

Run it:
```text
You: Use archon to run the hello-world workflow
```

### A Two-Node Sequential Workflow

```yaml
name: two-step
description: Plan then implement

nodes:
  - id: plan
    prompt: "Explore the codebase and create an implementation plan."

  - id: implement
    depends_on: [plan]
    prompt: "Read the plan from the previous step and implement it."
    context: fresh
```

Key concepts demonstrated:
- **`depends_on`**: `implement` waits for `plan` to complete
- **`context: fresh`**: Gives `implement` a clean session (doesn't see `plan`'s tool calls, only its output)
- **Default behavior**: Without `depends_on`, both nodes run in parallel

### A Complete Feature-Build Workflow

This is the canonical Archon example — plan, implement with a loop, run tests, get human approval, create PR:

```yaml
name: build-feature
description: Full feature development pipeline

nodes:
  - id: plan
    prompt: "Explore the codebase and create an implementation plan"

  - id: implement
    depends_on: [plan]
    loop:
      prompt: "Read the plan. Implement the next task. Run validation."
      until: ALL_TASKS_COMPLETE
      fresh_context: true

  - id: run-tests
    depends_on: [implement]
    bash: "bun run validate"

  - id: review
    depends_on: [run-tests]
    prompt: "Review all changes against the plan. Fix any issues."

  - id: approve
    depends_on: [review]
    loop:
      prompt: "Present the changes for review. Address any feedback."
      until: APPROVED
      interactive: true

  - id: create-pr
    depends_on: [approve]
    prompt: "Push changes and create a pull request"
```

**What happens when you run this:**
```text
You: Use archon to add dark mode to the settings page

Agent: Creating isolated worktree on branch archon/task-abc123...
       [plan] Exploring codebase... done (3 files identified)
       [implement] Task 1/4: CSS variables... ✓
       [implement] Task 2/4: Theme toggle... validation failed - fixing...
       [implement] Task 2/4: Theme toggle... ✓
       [implement] Task 3/4: Component updates... ✓
       [implement] Task 4/4: E2E tests... ✓
       [run-tests] bun run validate → PASS ✓
       [review] 0 issues found
       [approve] Changes presented. Awaiting your approval...
       → You: Approve
       [create-pr] PR created: https://github.com/you/project/pull/47
```

---

## 6. Node Types — Complete Reference

Archon supports exactly 7 node types. Each node has exactly ONE type.

### 6.1 `prompt` — Inline AI Prompt

The simplest AI node. The prompt string is sent to Claude Code directly.

```yaml
- id: my-node
  prompt: |
    Analyze the codebase and identify performance bottlenecks.
    Focus on database queries and N+1 patterns.
```

**When to use:** Quick AI tasks that don't need reusable command files.

### 6.2 `command` — Load from .archon/commands/

Loads a reusable command `.md` file. Prefer this over inline prompts for reusable steps.

```yaml
- id: investigate
  command: investigate-bug    # Loads .archon/commands/investigate-bug.md
```

**Command file format** (`.archon/commands/investigate-bug.md`):
```markdown
---
description: Investigate a bug report and identify root cause
argument-hint: "issue number or description"
---

# Investigate Bug

You are investigating bug: $ARGUMENTS

## Phase 1: Reproduction
1. Read the bug description
2. Reproduce the issue if possible
3. Document the exact steps to reproduce

## Phase 2: Root Cause
1. Trace the code path
2. Identify the root cause
3. Write your findings to $ARTIFACTS_DIR/root-cause.md
```

**When to use:** Reusable steps used across multiple workflows. Team-shared processes.

### 6.3 `bash` — Deterministic Shell Script

Runs a shell script via `bash -c`. No AI involved. Stdout is captured as `$nodeId.output`.

```yaml
- id: run-tests
  bash: |
    echo "Running test suite..."
    npm test -- --coverage
  timeout: 300000    # 5 minutes (in ms, default 120000)
```

**When to use:** Tests, linting, git operations, any deterministic task where AI is unnecessary waste.

### 6.4 `script` — TypeScript or Python

Deterministic data transformation. TypeScript runs via `bun`, Python via `uv`.

**TypeScript example:**
```yaml
- id: parse-issue
  script: |
    try {
      const issue = $fetch-issue.output;
      const labels = (issue.labels ?? []).map((l) => l.name);
      console.log(JSON.stringify({ labels, count: labels.length }));
    } catch {
      console.log(JSON.stringify({ labels: [], count: 0 }));
    }
  runtime: bun
  timeout: 10000
```

**Python example:**
```yaml
- id: analyze-metrics
  script: |
    import json, sys

    data = $test-results.output
    results = json.loads(data) if isinstance(data, str) else data

    passed = results.get("numPassedTests", 0)
    failed = results.get("numFailedTests", 0)
    total = passed + failed

    print(json.dumps({
        "pass_rate": round(passed / total * 100, 2) if total else 0,
        "passed": passed,
        "failed": failed,
        "total": total
    }))
  runtime: uv
  deps:
    - "numpy>=2.0"
  timeout: 30000
```

**When to use:** Parsing JSON output, transforming data, calculations — anything where an LLM would be overkill or unreliable.

### 6.5 `loop` — Iterative AI Until Signal

Repeats an AI prompt until a completion signal is received.

```yaml
- id: implement
  depends_on: [plan]
  loop:
    prompt: |
      Read the implementation plan.
      Implement the next task.
      Run validation after each change.
      When ALL tasks are complete: <promise>DONE</promise>
    until: DONE
    max_iterations: 10
    fresh_context: true
```

**Loop options:**

| Field | Default | Description |
|---|---|---|
| `until` | required | Signal string (e.g., `DONE`, `APPROVED`, `ALL_TASKS_COMPLETE`) |
| `max_iterations` | 5 | Hard limit to prevent infinite loops |
| `fresh_context` | false | New session each iteration (prevents context bloat) |

**When to use:** Implementation with test-fix cycles, any task that may need multiple attempts.

### 6.6 `approval` — Human-in-the-Loop Gate

Pauses workflow execution until a human approves or rejects.

```yaml
- id: approve
  depends_on: [review]
  loop:
    prompt: "Present the changes for review. Address any feedback."
    until: APPROVED
    interactive: true
```

**When to use:** Gates before deployment, before PR creation, before any irreversible action.

### 6.7 `cancel` — Early Termination

Terminates the workflow with a reason. Workflow status becomes `cancelled`.

```yaml
- id: skip-if-no-changes
  depends_on: [check-diff]
  when: "$check-diff.output == ''"
  cancel: "No changes detected — nothing to do"
```

**When to use:** Guard clauses that should abort the workflow.

---

### Common Node Fields (All Node Types)

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | string | **required** | Unique identifier for dependency refs, conditions, output substitution |
| `depends_on` | string[] | `[]` | Node IDs that must complete before this node runs |
| `when` | string | — | Condition expression; node skipped if false |
| `trigger_rule` | string | `all_success` | How to handle multiple dependencies: `all_success`, `one_success`, `none_failed_min_one_success`, `all_done` |
| `context` | `fresh` / `shared` | inherited | `fresh` = new session; `shared` = inherit prior session |
| `idle_timeout` | number | — | Kill node if idle for this many ms |
| `retry` | object | 2 retries | Auto-retry config: `{ attempts: 3, backoff: 3000 }` |
| `always_run` | boolean | false | Re-run on resume even if prior run completed |
| `output_type` | string | — | Semantic label (`plan`, `findings`) — writes typed sidecar to `$ARTIFACTS_DIR/nodes/<id>.md` |

### AI Node Options (`prompt` and `command` nodes only)

| Field | Type | Default | Description |
|---|---|---|---|
| `provider` | string | inherited | Per-node provider override (e.g., `openai`) |
| `model` | string | inherited | Per-node model override (e.g., `haiku` for cheap classification) |
| `output_format` | object | — | JSON Schema for structured output (SDK-enforced) |
| `allowed_tools` | string[] | all | Restrict which tools this node can use. `[]` = no tools |
| `modelReasoningEffort` | string | — | Codex-only: reasoning effort level |
| `webSearchMode` | string | — | Codex-only: `live` for web search enabled |

---

## 7. Commands — The Building Blocks

Commands are reusable Markdown files that combine a YAML frontmatter header with a detailed prompt body. They're the atomic building blocks of Archon workflows.

### File Format

```markdown
---
description: Investigate a GitHub issue and identify root cause
argument-hint: "issue number or URL"
---

# Investigate Bug: $ARGUMENTS

## Phase 1: Triage
1. Fetch the issue details using `gh issue view`
2. Read any linked PRs or commits
3. Classify severity: low / medium / high / critical

## Phase 2: Investigation
1. Search the codebase for relevant files
2. Trace the code path involved
3. Identify potential root causes

## Phase 3: Report
Write findings to $ARTIFACTS_DIR/investigation.md with:
- Root cause analysis
- Affected files
- Suggested fix approach
- Estimated complexity
```

### Location & Discovery

- **Repo commands:** `.archon/commands/` (scanned recursively)
- **Global commands:** `~/.archon/commands/`
- **Default commands:** `.archon/commands/defaults/` (bundled with Archon)

### Frontmatter Fields

| Field | Required | Description |
|---|---|---|
| `description` | Yes | Used by the AI router to select this command |
| `argument-hint` | No | Shown to users in UI/CLI |
| `model` | No | Model override for this command |

### Variables Available in Commands

| Variable | Description |
|---|---|
| `$ARGUMENTS` | Full string of arguments passed to the workflow or command |
| `$ARTIFACTS_DIR` | Absolute path to run-specific temp directory |
| `$BASE_BRANCH` | Target branch (e.g., `main`, `dev`) |
| `$WORKFLOW_ID` | Unique ID for the current execution run |

### Best Practices for Commands

1. **Phased execution:** Break tasks into logical phases (Triage → Investigate → Report)
2. **Artifact-driven:** Write intermediate results to `$ARTIFACTS_DIR/` so downstream nodes can read them
3. **Concrete instructions:** "Run `npm test`" not "run the tests"
4. **Error handling:** "If the build fails, read the error output and fix before proceeding"

---

## 8. Variable Substitution System

Archon injects variables at runtime into commands, prompts, bash scripts, and script nodes.

### Two Syntaxes

```yaml
# 1. $nodeId.output — output from a previous node
prompt: "Based on the plan: $plan.output, implement the changes."

# 2. $VARIABLE — runtime context variables
prompt: "Arguments: $ARGUMENTS"
bash: "cp $ARTIFACTS_DIR/report.md ./docs/report.md"
```

### Available Runtime Variables

| Variable | Scope | Description |
|---|---|---|
| `$ARGUMENTS` | All nodes | User's full argument string |
| `$ARTIFACTS_DIR` | All nodes | Temp directory for this run |
| `$BASE_BRANCH` | All nodes | Target branch name |
| `$WORKFLOW_ID` | All nodes | Unique execution run ID |
| `$nodeId.output` | prompt, command, bash, script | Output from node with given ID |

### Scoping Rules

- **`$nodeId.output`** is substituted *raw* into the target (no shell quoting). For JSON output, this means it's valid JS expression syntax — assign directly in script nodes without `String.raw` or `JSON.parse`.
- **Variables resolve in order of node execution**, so only upstream nodes are available.
- **Bash nodes:** Variables are shell-expanded. Use `"$ARGUMENTS"` (quoted) to handle spaces.
- **Script nodes:** Variables are injected as JavaScript/Python literals. JSON from `$nodeId.output` can be used directly.

### Example: Chaining Outputs

```yaml
nodes:
  - id: fetch-issue
    bash: "gh issue view 42 --json title,body,labels"

  - id: classify
    prompt: |
      Classify this issue:
      $fetch-issue.output
    output_format:
      type: object
      properties:
        issue_type: { type: string, enum: [bug, feature] }
        severity: { type: string, enum: [low, medium, high, critical] }

  - id: handle-bug
    command: fix-bug
    when: "$classify.output.issue_type == 'bug'"

  - id: handle-feature
    command: build-feature
    when: "$classify.output.issue_type == 'feature'"
```

Here, `$classify.output` is structured JSON, and `$classify.output.issue_type` accesses a specific field in the `when:` condition.

---

## 9. Conditional Branching

The `when:` field enables conditional execution. If the condition evaluates to `false`, the node is skipped (status: `skipped`).

### Condition Syntax

```yaml
# Simple equality
when: "$classify.output.issue_type == 'bug'"

# Negation
when: "$classify.output.issue_type != 'feature'"

# Check for empty
when: "$fetch-pr-template.output != ''"

# Numeric comparisons
when: "$extract-labels.output.count > 3"
```

### Common Patterns

**Pattern 1: Route based on classification**
```yaml
- id: classify
  prompt: "Is this a bug or a feature?"
  output_format:
    type: object
    properties:
      type: { type: string, enum: [bug, feature] }

- id: fix-bug
  command: fix-bug
  depends_on: [classify]
  when: "$classify.output.type == 'bug'"

- id: build-feature
  command: build-feature
  depends_on: [classify]
  when: "$classify.output.type == 'feature'"
```

**Pattern 2: Skip on empty result**
```yaml
- id: fetch-template
  bash: |
    if [ -f .github/PULL_REQUEST_TEMPLATE.md ]; then
      cat .github/PULL_REQUEST_TEMPLATE.md
    fi

- id: use-template
  prompt: "Use this PR template: $fetch-template.output"
  depends_on: [fetch-template]
  when: "$fetch-template.output != ''"

- id: use-default
  prompt: "Create a PR with a standard description"
  depends_on: [fetch-template]
  when: "$fetch-template.output == ''"
```

**Pattern 3: Guard clause with cancel**
```yaml
- id: abort-if-no-changes
  depends_on: [check-diff]
  when: "$check-diff.output == 'No changes'"
  cancel: "No changes detected — nothing to commit"
```

### Trigger Rules (for multiple dependencies)

When a node has multiple `depends_on`, use `trigger_rule` to control join semantics:

| Rule | Behavior |
|---|---|
| `all_success` (default) | All dependencies must succeed |
| `one_success` | At least one dependency must succeed |
| `none_failed_min_one_success` | No failures AND at least one success |
| `all_done` | All dependencies must complete (regardless of success/failure) |

```yaml
- id: merge-results
  depends_on: [investigate, plan]
  trigger_rule: one_success    # Runs if either path completes successfully
```

---

## 10. Script Nodes — TypeScript & Python

Script nodes run deterministic code without invoking an LLM. They're for data transforms, parsing, calculations — things where AI is unnecessary and expensive.

### TypeScript (bun runtime)

```yaml
- id: parse-labels
  script: |
    try {
      const issue = $fetch-issue.output;
      const labels = (issue.labels ?? []).map((l) => l.name);
      console.log(JSON.stringify({
        labels,
        count: labels.length,
        hasBug: labels.includes("bug"),
        hasUrgent: labels.includes("urgent")
      }));
    } catch {
      console.log(JSON.stringify({
        labels: [], count: 0, hasBug: false, hasUrgent: false
      }));
    }
  runtime: bun
  depends_on: [fetch-issue]
  timeout: 10000
```

**Important:** `$fetch-issue.output` is injected *raw*. If it's JSON, assign it directly — no `String.raw` or `JSON.parse` needed. `String.raw` breaks if the output contains backticks (common in markdown AI output).

### Python (uv runtime)

```yaml
- id: calculate-metrics
  script: |
    import json

    test_data = $run-tests.output

    passed = test_data.get("numPassedTests", 0)
    failed = test_data.get("numFailedTests", 0)
    skipped = test_data.get("numSkippedTests", 0)
    total = passed + failed + skipped

    result = {
        "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
        "passed": passed,
        "failed": failed,
        "skipped": skipped,
        "total": total,
        "verdict": "PASS" if failed == 0 else "FAIL"
    }
    print(json.dumps(result))
  runtime: uv
  deps:
    - "numpy>=2.0"
    - "pandas>=2.0"
  depends_on: [run-tests]
  timeout: 30000
```

### Named Script References

Instead of inline code, reference a file in `.archon/scripts/`:

```yaml
- id: analyze
  script: metrics-analyzer    # Loads .archon/scripts/metrics-analyzer.ts or .py
  runtime: bun
```

### Script Node Options

| Field | Required | Description |
|---|---|---|
| `script` | Yes* | Inline code string OR named reference to `.archon/scripts/<name>.(ts|py)` |
| `runtime` | Yes | `bun` for TypeScript/JS, `uv` for Python |
| `deps` | No | Python dependencies for `uv` (PEP 508 format) |
| `timeout` | No | Max execution time in ms (default: 120000) |

---

## 11. Loop Nodes & Approval Gates

### Loop Nodes — Iterate Until Done

Loop nodes run an AI prompt repeatedly until a completion signal is detected in the output.

```yaml
- id: implement
  depends_on: [plan]
  loop:
    prompt: |
      You are implementing: $ARGUMENTS

      Read the plan from $ARTIFACTS_DIR/plan.md.
      Implement one task at a time.
      After each task, run the relevant tests.
      When ALL tasks are complete and ALL tests pass:
      <promise>DONE</promise>
    until: DONE
    max_iterations: 10
    fresh_context: false
    idle_timeout: 600000
```

**How it works:**
1. The prompt is sent to Claude Code
2. Claude does work and responds
3. Archon checks if the response contains the `until` signal (e.g., `DONE`)
4. If found → loop ends, output = Claude's final response
5. If not found → increment iteration counter, loop again
6. If `max_iterations` reached → loop fails

**`fresh_context: true` vs `false`:**
- `true` — Each iteration gets a brand new session. Prevents context from growing unboundedly. Best for multi-task implementation where each task is independent.
- `false` — Session persists across iterations. The AI remembers what it did before. Best when later iterations need context from earlier ones.

### Approval Nodes — Human-in-the-Loop

Approval nodes pause the workflow and wait for a human decision.

```yaml
- id: approve
  depends_on: [review]
  loop:
    prompt: |
      Present the changes for review:

      Summary: $review.output
      Diff: run `git diff` to show changes

      Wait for feedback or approval.
      If feedback is given, address it.
      When approved: <promise>APPROVED</promise>
    until: APPROVED
    interactive: true
```

**When `interactive: true`:**
- The workflow pauses
- The user sees the agent's output
- The user can approve, reject, or give feedback
- The agent addresses feedback and loops back
- Only `APPROVED` (or the configured `until` signal) exits the loop

---

## 12. Structured Output

Force AI nodes to produce typed JSON output using JSON Schema.

### Basic Structured Output

```yaml
- id: classify
  prompt: |
    Classify this GitHub issue:

    $fetch-issue.output

    Determine if this is a bug fix or a new feature.
  model: haiku
  allowed_tools: []
  output_format:
    type: object
    properties:
      issue_type:
        type: string
        enum: [bug, feature]
      title:
        type: string
      severity:
        type: string
        enum: [low, medium, high, critical]
      affected_components:
        type: array
        items:
          type: string
    required: [issue_type, title]
```

**When to use:**
- Classification/routing decisions (so downstream `when:` conditions are reliable)
- Extracting structured data from unstructured text
- Any time a downstream node depends on specific fields

**Key benefit:** The output is guaranteed to match the schema (SDK-enforced), so `$classify.output.issue_type` is always a valid `"bug"` or `"feature"` — never an unexpected value.

### Important: Disable Tools for Classification

When using structured output for pure classification, set `allowed_tools: []`. This prevents the AI from running unnecessary bash commands or file reads, making classification fast and cheap.

---

## 13. Isolation System — Git Worktrees

Every workflow run gets its own **git worktree** — a separate working directory linked to the same repository.

### How It Works

```text
Main repo:     /home/user/project          (on branch main)
Worktree 1:    /home/user/.archon/worktrees/abc123  (on branch archon/task-abc123)
Worktree 2:    /home/user/.archon/worktrees/def456  (on branch archon/task-def456)
```

- Each worktree is a full copy of the working tree
- Share the same `.git` directory (no duplication of git history)
- Each has its own branch, so changes don't conflict
- Worktrees are cleaned up after the workflow completes

### Why This Matters

Without isolation:
```text
Run 1: Fix issue #42 → creates branch fix/42, modifies 3 files
Run 2: Fix issue #43 → also modifies file X → CONFLICT
```

With isolation:
```text
Run 1: Worktree on archon/task-abc → modifies 3 files → PR created → cleaned up
Run 2: Worktree on archon/task-def → modifies file X independently → PR created → cleaned up
No conflicts. Both run in parallel.
```

### Worktree Configuration

```yaml
# Per-workflow worktree control
worktree:
  enabled: false    # false = always live checkout (for read-only workflows like review)
```

---

## 14. Web UI & Dashboard

Start the Web UI:
```bash
archon serve          # Compiled binary
bun run dev           # From source
```

### Key Pages

| Page | Purpose |
|---|---|
| **Chat** | Real-time streaming conversation with tool call visualization |
| **Dashboard** | Mission Control — monitor all running workflows, filterable by project, status, date |
| **Workflow Builder** | Visual drag-and-drop editor for DAG workflows with loop nodes |
| **Workflow Execution** | Step-by-step progress view for active workflow runs |

### Sidebar Features

The sidebar shows conversations from **all platforms** (CLI, Slack, Telegram, GitHub) — not just the web. It's a unified monitoring hub.

### Project Registration

Click **+** next to "Project" and enter a GitHub URL or local path. Projects are auto-registered on first use from CLI too.

---

## 15. Multi-Platform Access

Archon workflows run identically from any access surface:

```text
┌──────────────────────────────────────────────────────┐
│                  Archon Core                          │
│                                                       │
│  ┌──────┐  ┌─────────┐  ┌───────┐  ┌──────────┐     │
│  │ CLI  │  │ Web UI  │  │ Slack │  │ Telegram │     │
│  │      │  │         │  │       │  │          │     │
│  │"use   │  │[Chat]   │  │@archon│  │/workflow │     │
│  │archon"│  │[Builder]│  │fix #42│  │fix #42   │     │
│  └──┬───┘  └────┬────┘  └───┬───┘  └────┬─────┘     │
│     └───────────┴────────────┴────────────┘           │
│                     │                                 │
│            Same workflow engine                       │
│            Same isolation                             │
│            Same output                                │
└──────────────────────────────────────────────────────┘
```

### Platform Setup

During `"Set up Archon"`, the wizard walks you through connecting:

- **GitHub:** OAuth or token for PR creation, issue fetching
- **Slack:** Bot token + signing secret
- **Telegram:** Bot token from @BotFather
- **Discord:** Bot token + application ID

Tokens are stored in `~/.archon/config.yaml`.

### Usage by Platform

| Platform | Trigger |
|---|---|
| CLI | `claude` → "Use archon to fix issue #42" |
| Web | Chat box → "Fix issue #42" |
| Slack | `@archon fix issue #42` |
| Telegram | `/workflow fix issue #42` |
| GitHub | Issue comment: `/archon fix` |

---

## 16. The 17 Built-in Workflows

Archon ships with 17 workflows covering the most common development tasks. Find them in `.archon/workflows/defaults/`.

| # | Workflow | Description |
|---|---|---|
| 1 | `archon-assist` | General Q&A, debugging, and code exploration |
| 2 | `archon-fix-github-issue` | Classify → investigate → plan → implement → validate → PR → review → self-fix |
| 3 | `archon-idea-to-pr` | Feature idea → plan → implement → validate → PR → 5 parallel reviews → self-fix |
| 4 | `archon-plan-to-pr` | Execute an existing plan → implement → validate → PR → review → self-fix |
| 5 | `archon-issue-review-full` | Fix + full multi-agent review pipeline for GitHub issues |
| 6 | `archon-smart-pr-review` | Classify PR complexity → targeted review agents → synthesize findings |
| 7 | `archon-comprehensive-pr-review` | Multi-agent PR review (5 parallel reviewers) with automatic fixes |
| 8 | `archon-create-issue` | Classify problem → gather context → investigate → create GitHub issue |
| 9 | `archon-validate-pr` | Thorough PR validation testing both main and feature branches |
| 10 | `archon-resolve-conflicts` | Detect merge conflicts → analyze → resolve → validate |
| 11 | `archon-security-audit` | Dependency scan → code analysis → secret detection → report |
| 12 | `archon-documentation` | Generate/update docs from code changes |
| 13 | `archon-refactor` | Identify refactoring opportunities → plan → execute → validate |
| 14 | `archon-migrate` | Framework/API migration with validation at each step |
| 15 | `archon-generate-tests` | Analyze code → generate unit/integration/e2e tests → validate coverage |
| 16 | `archon-code-review` | Single-agent focused code review |
| 17 | `archon-release` | Version bump → changelog → tag → release notes |

### Overriding Defaults

Copy a default workflow to customize it:
```bash
cp .archon/workflows/defaults/archon-fix-github-issue.yaml .archon/workflows/my-fix-issue.yaml
# Edit my-fix-issue.yaml with your customizations
```

Same-named files in your `.archon/workflows/` override the bundled defaults.

---

## 17. Configuration Reference

### `~/.archon/config.yaml`

```yaml
# Provider configuration
provider: anthropic
model: claude-sonnet-4

# Assistant paths
assistants:
  claude:
    claudeBinaryPath: /home/user/.local/bin/claude

# Platform tokens
platforms:
  github:
    token: ghp_...
  slack:
    botToken: xoxb-...
    signingSecret: ...
  telegram:
    botToken: "1234567890:ABC..."
  discord:
    botToken: "..."
    applicationId: "..."

# Database
database:
  url: sqlite://~/.archon/archon.db   # or postgres://...

# Server
server:
  port: 3000
  host: localhost
```

### Workflow Top-Level Schema

```yaml
name: workflow-name              # Required. Unique identifier
description: |                   # Optional. Shown in UI/CLI listings
  What this workflow does.

provider: claude                 # Optional. Default provider for all nodes
model: sonnet                    # Optional. Default model for all nodes
interactive: true                # Optional. Web only: run in foreground
requires: [github]               # Optional. Block if user hasn't connected GitHub
tags: [Review, GitLab]           # Optional. UI filter tags
persist_sessions: true           # Optional. Persist AI node sessions across runs

worktree:                        # Optional. Isolation config
  enabled: true                  # Default: true. false for live checkout workflows

nodes:                           # Required. Array of node definitions
  - id: node-id
    # ... one of: prompt, command, bash, script, loop, approval, cancel
```

---

## 18. Advanced Workflow Patterns

### Pattern 1: Smart Issue Routing

Classify an issue, then branch based on type:

```yaml
name: smart-issue-fix
description: Classify a GitHub issue, route to appropriate handler

nodes:
  - id: fetch-issue
    bash: |
      issue_num=$(echo "$ARGUMENTS" | grep -oE '[0-9]+' | head -1)
      gh issue view "$issue_num" --json title,body,labels,comments

  - id: classify
    prompt: "Classify this issue: $fetch-issue.output"
    depends_on: [fetch-issue]
    model: haiku
    allowed_tools: []
    output_format:
      type: object
      properties:
        type: { type: string, enum: [bug, feature, docs, question] }
        severity: { type: string, enum: [low, medium, high, critical] }
      required: [type]

  - id: fix-bug
    command: investigate-bug
    depends_on: [classify]
    when: "$classify.output.type == 'bug'"
    context: fresh

  - id: build-feature
    command: plan-feature
    depends_on: [classify]
    when: "$classify.output.type == 'feature'"
    context: fresh

  - id: write-docs
    command: update-docs
    depends_on: [classify]
    when: "$classify.output.type == 'docs'"
    context: fresh

  - id: answer-question
    command: answer-question
    depends_on: [classify]
    when: "$classify.output.type == 'question'"
    context: fresh

  - id: implement
    depends_on: [fix-bug, build-feature, write-docs, answer-question]
    trigger_rule: one_success
    loop:
      prompt: |
        Read the investigation/plan from $ARTIFACTS_DIR.
        Implement the changes. Validate. When done: <promise>DONE</promise>
      until: DONE
      max_iterations: 5

  - id: create-pr
    depends_on: [implement]
    prompt: "Push changes and create a PR summarizing what was done"
```

### Pattern 2: Parallel Review Swarm

Run multiple specialized reviews in parallel, then merge findings:

```yaml
name: comprehensive-review

nodes:
  - id: security-review
    prompt: "Perform a security-focused code review. Check for: injection, auth issues, data leaks, unsafe dependencies."

  - id: performance-review
    prompt: "Perform a performance review. Check for: N+1 queries, unnecessary allocations, blocking operations, missing indexes."

  - id: style-review
    prompt: "Review code style and consistency. Check naming, formatting, patterns, documentation."

  - id: logic-review
    prompt: "Review business logic correctness. Check edge cases, error handling, state management, race conditions."

  - id: test-review
    prompt: "Review test coverage and quality. Check for missing test cases, brittle tests, slow tests."

  - id: synthesize
    depends_on: [security-review, performance-review, style-review, logic-review, test-review]
    prompt: |
      Synthesize all review findings:

      Security: $security-review.output
      Performance: $performance-review.output
      Style: $style-review.output
      Logic: $logic-review.output
      Tests: $test-review.output

      Create a unified review report. Highlight critical issues first.
      Suggest concrete fixes for each issue.
```

### Pattern 3: Wait for CI then Merge

```yaml
name: wait-ci-then-merge
description: Create PR, wait for CI to pass, then merge

nodes:
  - id: create-pr
    prompt: "Push changes and create a pull request"

  - id: wait-ci
    depends_on: [create-pr]
    bash: |
      pr_url=$(echo "$create-pr.output" | grep -o 'https://github.com/[^ ]*/pull/[0-9]*')
      pr_num=$(echo "$pr_url" | grep -o '[0-9]*$')
      echo "Waiting for CI on PR #$pr_num..."
      while true; do
        status=$(gh pr view "$pr_num" --json state,statusCheckRollup | jq -r '.statusCheckRollup[0].conclusion // "PENDING"')
        echo "Status: $status"
        if [ "$status" = "SUCCESS" ]; then
          echo "CI passed!"
          break
        elif [ "$status" = "FAILURE" ]; then
          echo "CI failed!"
          exit 1
        fi
        sleep 30
      done
    timeout: 1800000    # 30 minutes

  - id: merge
    depends_on: [wait-ci]
    prompt: "CI has passed. Merge the pull request."
```

---

## 19. Real-World Recipe Book

### Recipe 1: End-to-End Bug Fix

```yaml
name: fix-bug-end-to-end
description: Fetch bug report, reproduce, fix, test, review, ship

nodes:
  - id: fetch-bug
    bash: |
      issue_num=$(echo "$ARGUMENTS" | grep -oE '[0-9]+' | head -1)
      gh issue view "$issue_num" --json title,body,labels
    timeout: 15000

  - id: analyze
    prompt: |
      Analyze this bug report:
      $fetch-bug.output

      Identify:
      1. Expected behavior vs actual behavior
      2. Steps to reproduce
      3. Likely affected code paths
    model: sonnet
    depends_on: [fetch-bug]

  - id: reproduce
    depends_on: [analyze]
    loop:
      prompt: |
        Try to reproduce the bug based on the analysis.
        Write a minimal reproduction script.
        When you've confirmed the bug exists: <promise>CONFIRMED</promise>
        If you cannot reproduce: <promise>CANNOT_REPRODUCE</promise>
      until: CONFIRMED
      max_iterations: 3

  - id: implement-fix
    depends_on: [reproduce]
    loop:
      prompt: |
        Implement a fix for the bug.
        After each change:
        1. Run the reproduction script to verify the bug is fixed
        2. Run the existing test suite to check for regressions
        When fix is complete and all tests pass: <promise>DONE</promise>
      until: DONE
      max_iterations: 5

  - id: add-tests
    depends_on: [implement-fix]
    prompt: |
      Add a regression test that specifically covers this bug.
      The test should fail without the fix and pass with it.

  - id: create-pr
    depends_on: [add-tests]
    prompt: |
      Create a pull request with:
      1. The bug fix
      2. The regression test
      3. A clear description referencing the original issue
      4. A summary of the root cause
```

### Recipe 2: Dependency Update Pipeline

```yaml
name: update-dependencies
description: Update deps, run tests, create PR

nodes:
  - id: check-outdated
    bash: |
      npm outdated --json
    timeout: 30000

  - id: parse-outdated
    script: |
      try {
        const outdated = $check-outdated.output;
        const updates = Object.entries(outdated).map(([name, info]) => ({
          name,
          current: info.current,
          wanted: info.wanted,
          latest: info.latest,
          type: info.type
        }));
        const minor = updates.filter(u => u.type === "minor" || u.type === "patch");
        const major = updates.filter(u => u.type === "major");
        console.log(JSON.stringify({ total: updates.length, minor, major }));
      } catch {
        console.log(JSON.stringify({ total: 0, minor: [], major: [] }));
      }
    runtime: bun
    depends_on: [check-outdated]
    timeout: 10000

  - id: abort-if-none
    depends_on: [parse-outdated]
    when: "$parse-outdated.output.total == 0"
    cancel: "All dependencies are up to date"

  - id: update-minor
    depends_on: [parse-outdated]
    when: "$parse-outdated.output.minor.length > 0"
    bash: |
      npm update
    timeout: 120000

  - id: run-tests
    depends_on: [update-minor]
    bash: |
      npm test
    timeout: 300000

  - id: create-pr
    depends_on: [run-tests]
    prompt: |
      Create a PR for the dependency updates.

      Outdated packages: $parse-outdated.output

      Include a summary of what was updated.
```

### Recipe 3: Code Migration (Express → Fastify)

```yaml
name: migrate-express-to-fastify
description: Migrate an Express.js route to Fastify

nodes:
  - id: analyze-route
    prompt: |
      Analyze the Express route at src/routes/$ARGUMENTS.ts
      Document:
      1. All endpoints (method + path)
      2. Middleware used
      3. Request/response schemas
      4. Dependencies (other modules, DB queries)

  - id: plan-migration
    depends_on: [analyze-route]
    prompt: |
      Create a migration plan for converting this Express route to Fastify.
      Consider:
      1. Fastify plugin structure
      2. Schema validation (use TypeBox or JSON Schema)
      3. Middleware → Fastify hooks (onRequest, preHandler)
      4. Error handling patterns

  - id: migrate
    depends_on: [plan-migration]
    loop:
      prompt: |
        Implement the migration one step at a time.
        After each step, verify:
        1. TypeScript compiles without errors
        2. Existing tests still pass
        When migration is complete: <promise>DONE</promise>
      until: DONE
      max_iterations: 8

  - id: verify
    depends_on: [migrate]
    bash: |
      npx tsc --noEmit && npm test
    timeout: 180000

  - id: create-pr
    depends_on: [verify]
    prompt: |
      Create a PR for the Express → Fastify migration.
      Include:
      1. What was migrated
      2. Breaking changes (if any)
      3. Performance improvements (if measurable)
```

---

## 20. Archon vs OpenHands vs Hermes

| Dimension | Archon | OpenHands | Hermes |
|---|---|---|---|
| **Category** | Workflow engine | Coding agent platform | Personal agent |
| **Scope** | Software dev only | Software dev only | General purpose |
| **Core idea** | YAML-defined DAG harnesses for AI coding | Autonomous agents that resolve dev tasks | Persistent agent that grows with you |
| **Persistence** | Stateless per run | Session-level | Cross-session memory + skills |
| **Isolation** | Git worktrees | Docker sandboxes | N/A (user's machine) |
| **Primary I/O** | Claude Code + YAML workflows | Web GUI / CLI / SDK / Cloud | Terminal + TUI + 20 messaging platforms |
| **Multi-agent** | Yes (DAG nodes in parallel) | Yes (sub-agents, orchestrators) | Yes (subagents + delegation) |
| **Scheduling** | Manual trigger / CI hook | Automation service | Built-in cron scheduler |
| **Messaging** | GitHub, Slack, Telegram (triggers) | Slack, GitHub | Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email |
| **Learning** | Static workflows (update YAML) | Static configuration | Self-improving skills |
| **Enterprise** | No | Yes (control plane, RBAC, SSO, audit logs) | No |
| **Stars** | 22.5k | 77.9k | N/A (newer) |
| **Stack** | TypeScript + Bun | Python | Python |
| **License** | MIT | MIT | Open source |
| **Setup complexity** | Medium (Bun + Claude Code + gh CLI) | Medium (Python + Docker) | Low (single install script) |
| **Best for** | Teams wanting repeatable, deterministic AI coding pipelines | Engineering teams offloading real backlog work to autonomous agents | Individuals wanting one persistent agent for everything |

### When to Choose What

- **Pick Archon** when you want to encode your team's dev process into repeatable YAML and run it identically from CLI, Slack, or CI.
- **Pick OpenHands** when you want autonomous agents that resolve GitHub issues end-to-end with enterprise governance.
- **Pick Hermes** when you want one agent that knows you, remembers everything, and follows you everywhere.

They're complementary, not competitive. You could use Archon workflows inside OpenHands, or trigger Hermes cron jobs that call Archon workflows.

---

## 21. Troubleshooting & Tips

### Common Issues

| Symptom | Fix |
|---|---|
| "Claude Code not found" | Set `CLAUDE_BIN_PATH` or configure in `~/.archon/config.yaml` |
| Workflow hangs | Check `idle_timeout` settings; add timeouts to `bash` nodes |
| Loop never exits | Verify the `until` signal appears verbatim in the LLM response; increase `max_iterations` |
| Bash node output empty | Check that stdout is where output goes (not stderr); use `2>&1` if needed |
| Variable substitution not working | Variables only resolve for upstream (completed) nodes; check `depends_on` ordering |
| Script node runtime error | `bun` nodes: avoid `String.raw` and `JSON.parse` on injected JSON — assign directly |
| Worktree conflict | Clean up stale worktrees: `git worktree prune` |
| Server doesn't see local workflow changes | Server reads from workspace clone, not local filesystem. Push changes first, or use CLI. |

### Pro Tips

1. **Use `model: haiku` for classification nodes** — fast, cheap, and accurate enough for routing decisions
2. **Set `allowed_tools: []` on classification nodes** — prevents unnecessary tool calls
3. **Use `context: fresh` on loop nodes** running multi-task implementations — prevents context explosion
4. **Always add `timeout` to bash nodes** — defaults to 120s, which may be too short for installs or builds
5. **Write intermediate artifacts to `$ARTIFACTS_DIR`** — makes debugging easier (you can inspect what each node produced)
6. **Use script nodes for parsing** — more reliable and cheaper than having the LLM parse JSON
7. **Commit your `.archon/workflows/` to the repo** — they're part of your team's dev process
8. **Copy and customize default workflows** — don't modify defaults directly (updates will override)

---

## Quick-Start Cheat Sheet

```bash
# Install
curl -fsSL https://archon.diy/install | bash

# Set up
cd Archon && bun install && claude
# Say: "Set up Archon"

# Use in your project
cd /path/to/your/project
claude
# Say: "Use archon to fix issue #42"
# Say: "What archon workflows do I have?"

# Web UI
archon serve                    # or: bun run dev

# CLI commands
archon workflow list             # List available workflows
archon workflow run <name>       # Run a workflow
archon --version                 # Check version
```

---

## Sources

- [Archon GitHub Repository](https://github.com/coleam00/Archon) — primary source for code, README, workflows
- [Archon Documentation](https://archon.diy/docs/) — official docs
- [The Book of Archon](https://archon.diy/book/) — 10-chapter narrative tutorial
- [DeepWiki: coleam00/Archon](https://deepwiki.com/coleam00/Archon) — auto-generated detailed wiki
- [Archon DAG Workflow Example](https://github.com/coleam00/Archon/blob/dev/.claude/skills/archon/examples/dag-workflow.yaml) — reference workflow
- [Authoring Workflows Guide](https://github.com/coleam00/Archon/blob/dev/packages/docs-web/src/content/docs/guides/authoring-workflows.md) — workflow authoring docs
- [Script Nodes Guide](https://archon.diy/guides/script-nodes/) — script node documentation

*Tutorial written June 2026 against Archon (coleam00/Archon). Example workflows are illustrative of documented features; exact behavior depends on your Claude Code version and model.*
