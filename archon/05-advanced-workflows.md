# 05 — Advanced Workflows

**Goal:** Master conditional branching, structured output, variable substitution, retry logic, and isolation.

**Companion examples:** `examples/workflows/04-smart-issue-fix.yaml`

---

## 5.1 Conditional Branching with `when:`

Route execution based on upstream node output. If the condition is false, the node is **skipped** (not failed).

### Syntax

```yaml
# Simple equality
when: "$classify.output.type == 'bug'"

# Negation / inequality
when: "$classify.output.type != 'feature'"

# Check for empty output
when: "$fetch-pr-template.output != ''"

# Numeric comparison
when: "$parse-labels.output.count > 3"
```

### Routing Pattern: Classify → Branch

```yaml
- id: classify
  prompt: "Is this a bug or a feature?"
  model: haiku
  allowed_tools: []
  output_format:
    type: object
    properties:
      type: { type: string, enum: [bug, feature] }
    required: [type]

- id: fix-bug
  command: fix-bug
  depends_on: [classify]
  when: "$classify.output.type == 'bug'"
  context: fresh

- id: build-feature
  command: build-feature
  depends_on: [classify]
  when: "$classify.output.type == 'feature'"
  context: fresh

- id: finalize
  depends_on: [fix-bug, build-feature]
  trigger_rule: one_success          # Only one path ran — that's OK
  prompt: "Create a summary of what was done"
```

### Guard Clause Pattern

```yaml
- id: check-diff
  bash: |
    if git diff --quiet; then echo "No changes"; fi
  timeout: 10000

- id: abort-if-clean
  depends_on: [check-diff]
  when: "$check-diff.output == 'No changes'"
  cancel: "No changes detected — nothing to commit"
```

---

## 5.2 Structured Output

Force AI nodes to produce typed JSON. Essential for reliable `when:` conditions.

```yaml
- id: classify
  prompt: "Classify: $fetch-issue.output"
  model: haiku
  allowed_tools: []
  output_format:
    type: object
    properties:
      issue_type:
        type: string
        enum: [bug, feature, docs, question]
      severity:
        type: string
        enum: [low, medium, high, critical]
      affected_components:
        type: array
        items:
          type: string
    required: [issue_type]
```

**Then use fields in downstream nodes:**
```yaml
when: "$classify.output.issue_type == 'bug'"
when: "$classify.output.severity == 'critical'"
```

**Best practices:**
- Use `model: haiku` for classification (cheap, fast)
- Set `allowed_tools: []` (pure classification, no tool calls)
- Only require fields you actually use downstream

---

## 5.3 Variable Substitution System

### Runtime Variables (available in ALL nodes)

| Variable | Description |
|---|---|
| `$ARGUMENTS` | Full argument string from user |
| `$ARTIFACTS_DIR` | Temp directory for this workflow run |
| `$BASE_BRANCH` | Target branch (e.g., `main`) |
| `$WORKFLOW_ID` | Unique execution run ID |

### Node Output Variables

| Syntax | Description |
|---|---|
| `$nodeId.output` | Full output of node |
| `$nodeId.output.fieldName` | Nested field (structured output) |
| `$nodeId.output.items[0]` | Array element |

### Scoping Rules

- Only UPSTREAM (completed) nodes are available
- In **bash nodes**: shell-expanded — use quotes: `"$ARGUMENTS"`
- In **TypeScript script nodes (bun)**: injected RAW — assign directly, no `JSON.parse` needed
- In **Python script nodes (uv)**: injected as Python literal

```yaml
# Bash: shell expansion works naturally
bash: "cp $ARTIFACTS_DIR/plan.md ./docs/plan.md"

# Prompt: use output from previous node
prompt: "Based on the plan: $plan.output, implement the changes"

# TypeScript script: assign directly (NO String.raw or JSON.parse)
script: |
  const issue = $fetch-issue.output;
  console.log(JSON.stringify({ labels: issue.labels ?? [] }));
```

---

## 5.4 Retry Configuration

Nodes auto-retry on failure. Default: 2 retries (3 total attempts), 3-second backoff.

```yaml
# Custom retry: 5 total attempts, 10s backoff
- id: flaky-build
  bash: "npm run build"
  retry:
    attempts: 5
    backoff: 10000
  timeout: 120000

# No retries — fail on first attempt
- id: one-shot-deploy
  bash: "./deploy.sh"
  retry:
    attempts: 1
  timeout: 300000
```

**When to increase retries:** Network-dependent operations, flaky external services, rate-limited APIs.

**When to disable retries:** Destructive operations (deploy, database writes), idempotency-critical tasks.

---

## 5.5 Worktree Isolation

```yaml
# Default: each run gets its own worktree
name: build-feature
worktree:
  enabled: true

# Disable for read-only workflows
name: code-review
worktree:
  enabled: false     # Runs directly in the repo — can see uncommitted changes
```

**Keep enabled for:** Any workflow that modifies code, parallel execution, production use.

**Disable for:** Read-only workflows (review, audit, analysis), quick exploratory tasks where you want the AI to see local changes.

---

## 5.6 Complete Example: Smart Issue Fix

See `examples/workflows/04-smart-issue-fix.yaml` for the full workflow demonstrating:

- `bash` node to fetch GitHub issue
- `script` node (TypeScript) to parse labels
- `prompt` node with structured output for classification
- `command` nodes with `when:` for branching
- `loop` node for implementation
- `trigger_rule: one_success` to merge paths
- `context: fresh` for isolated sessions
- `model: haiku` for cheap classification

---

## 5.7 Pipeline Design Principles

1. **Separate deterministic steps from AI steps** — bash/script for parsing and validation, AI for reasoning and code generation
2. **Classify first, then branch** — structured output enables reliable routing
3. **Use script nodes for data transforms** — cheaper and more reliable than having the LLM parse JSON
4. **Always add timeouts** — defaults may be wrong for your use case
5. **Write intermediate artifacts** — use `$ARTIFACTS_DIR` so downstream nodes can pick up structured data
6. **Version your workflows** — commit `.archon/workflows/` to your repo

---

**Next:** [06 — Real-World Recipes](./06-real-world-recipes.md)
