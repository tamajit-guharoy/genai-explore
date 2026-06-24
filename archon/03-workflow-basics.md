# 03 — Workflow Basics

**Goal:** Master the YAML structure, DAG execution order, and core workflow concepts.

**Companion examples:** `examples/workflows/01-hello-world.yaml`, `02-two-step.yaml`, `03-build-feature.yaml`

---

## 3.1 Anatomy of a Workflow YAML

Every Archon workflow is a YAML file in `.archon/workflows/`. The simplest possible workflow:

```yaml
# .archon/workflows/hello-world.yaml
name: hello-world
description: My first Archon workflow

nodes:
  - id: greet
    prompt: "Say hello and list the files in the current directory."
```

Run it:
```
$ cd /path/to/your/project
$ claude
> Use archon to run the hello-world workflow
```

## 3.2 The Top-Level Schema

```yaml
name: workflow-name              # Required. Unique identifier
description: |                   # Optional but recommended
  What this workflow does.

provider: claude                 # Optional. Default provider for all nodes
model: sonnet                    # Optional. Default model
tags: [Review]                   # Optional. UI filter tags

worktree:                        # Optional. Isolation config
  enabled: true                  # Default: true. false = live checkout

nodes:                           # Required. The DAG array
  - id: step-1
    # ... node definition
  - id: step-2
    depends_on: [step-1]
    # ... node definition
```

## 3.3 Sequential vs Parallel Execution

The key insight: nodes WITHOUT `depends_on` run in **parallel**. Nodes WITH `depends_on` wait for their dependencies.

### Fully Sequential (4 nodes, 4 layers)

```yaml
nodes:
  - id: plan
    prompt: "Create a plan"

  - id: implement
    depends_on: [plan]
    prompt: "Write the code"

  - id: test
    depends_on: [implement]
    bash: "npm test"

  - id: ship
    depends_on: [test]
    prompt: "Create PR"
```

Execution: `plan` → `implement` → `test` → `ship` (one at a time)

### Fan-Out / Fan-In (parallel middle layer)

```yaml
nodes:
  - id: plan
    prompt: "Create a plan"

  - id: module-a
    depends_on: [plan]
    prompt: "Implement module A"

  - id: module-b
    depends_on: [plan]
    prompt: "Implement module B"

  - id: module-c
    depends_on: [plan]
    prompt: "Implement module C"

  - id: merge
    depends_on: [module-a, module-b, module-c]
    prompt: "Merge all modules"
```

Execution: `plan` → `[module-a, module-b, module-c]` (all 3 in parallel) → `merge`

### Full Review Swarm (5 parallel reviewers, then synthesize)

```yaml
nodes:
  - id: fetch-pr
    prompt: "Fetch the PR details"

  - id: security
    depends_on: [fetch-pr]
    prompt: "Security review"

  - id: performance
    depends_on: [fetch-pr]
    prompt: "Performance review"

  - id: style
    depends_on: [fetch-pr]
    prompt: "Style review"

  - id: logic
    depends_on: [fetch-pr]
    prompt: "Logic review"

  - id: tests
    depends_on: [fetch-pr]
    prompt: "Test review"

  - id: synthesize
    depends_on: [security, performance, style, logic, tests]
    prompt: "Synthesize all reviews into a report"
```

## 3.4 `trigger_rule` — Controlling Join Semantics

When a node depends on MULTIPLE upstream nodes, `trigger_rule` controls when it's allowed to run.

| Rule | Behavior | When to Use |
|---|---|---|
| `all_success` (default) | ALL dependencies must succeed | Merge after parallel reviews — need every finding |
| `one_success` | At least ONE must succeed | Branching paths: either bug-fix OR feature-path completes |
| `none_failed_min_one_success` | No failures + at least one success | Multiple fallback approaches — use first that works |
| `all_done` | All complete (regardless of success/failure) | Cleanup step that MUST run no matter what |

```yaml
# Example: merge divergent paths
- id: implement
  depends_on: [fix-bug, build-feature]
  trigger_rule: one_success
  loop:
    prompt: "Implement from whichever path completed..."
    until: DONE
```

## 3.5 `context: fresh` vs `context: shared`

Controls whether an AI node gets a brand-new session or inherits from the previous node.

| Mode | Behavior | Default For |
|---|---|---|
| `fresh` | Clean Claude Code session. Sees upstream OUTPUT (via `$nodeId.output`) but NOT prior tool calls or conversation | Parallel DAG layers |
| `shared` | Inherits the same Claude Code session. Sees all prior conversation and tool calls | Sequential DAG chains |

**Rule of thumb:** Use `fresh` when each node has independent work. Use `shared` when later nodes need to build on the context of earlier ones.

```yaml
- id: plan
  prompt: "Explore and plan"

- id: implement
  depends_on: [plan]
  prompt: "Implement based on the plan: $plan.output"
  context: fresh         # Clean session — only sees $plan.output text
```

## 3.6 The Canonical `build-feature` Workflow

This is the reference example used in Archon's README. See `examples/workflows/03-build-feature.yaml` for the full file.

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

## 3.7 Workflow File Discovery

| Location | Precedence | Scope |
|---|---|---|
| `.archon/workflows/` | **Highest** | This repo only |
| `~/.archon/workflows/` | Medium | All projects (overridden by repo workflows) |
| `.archon/workflows/defaults/` | Lowest | 17 built-in workflows shipped with Archon |

Same-named files in higher-precedence locations override lower ones.

**Override a default:**
```bash
cp .archon/workflows/defaults/archon-fix-github-issue.yaml .archon/workflows/my-fix-issue.yaml
# Edit my-fix-issue.yaml with your customizations
```

---

**Try it:** Copy the examples from `examples/workflows/` to your project's `.archon/workflows/` and run them.

```bash
cp examples/workflows/01-hello-world.yaml /path/to/project/.archon/workflows/
cd /path/to/project
claude
> Use archon to run the hello-world workflow
```

**Next:** [04 — Node Types Deep Dive](./04-node-types.md)
