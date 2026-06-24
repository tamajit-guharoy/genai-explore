# 04 — Node Types Deep Dive

**Goal:** Master all 7 Archon node types.

**Companion examples:** `examples/workflows/04-smart-issue-fix.yaml` (uses all 7 types)

---

## 4.1 The 7 Node Types at a Glance

| # | Type | AI? | Description | Best For |
|---|------|-----|-------------|----------|
| 1 | `prompt` | Yes | Inline AI prompt string | Quick one-off AI tasks |
| 2 | `command` | Yes | Load from `.archon/commands/<name>.md` | Reusable team processes |
| 3 | `bash` | No | Shell script via `bash -c` | Tests, linting, git ops |
| 4 | `script` | No | TypeScript (bun) or Python (uv) | JSON parsing, data transforms |
| 5 | `loop` | Yes | Iterative AI until completion signal | Implementation with retry |
| 6 | `approval` | Yes | Human-in-the-loop gate | Pre-PR, pre-deploy gates |
| 7 | `cancel` | No | Early termination with reason | Guard clauses |

---

## 4.2 `prompt` — Inline AI Prompt

The simplest AI node. Send a string to Claude Code.

```yaml
- id: analyze
  prompt: |
    Analyze the codebase for:
    1. Security vulnerabilities
    2. Performance bottlenecks
    3. Code quality issues
```

With model override and restricted tools:
```yaml
- id: classify
  prompt: "Is this a bug or a feature?"
  model: haiku               # Cheap, fast model
  allowed_tools: []            # No tool calls needed for classification
```

With structured output (JSON Schema-enforced):
```yaml
- id: classify
  prompt: "Classify: $fetch-issue.output"
  model: haiku
  allowed_tools: []
  output_format:
    type: object
    properties:
      type:
        type: string
        enum: [bug, feature]
      severity:
        type: string
        enum: [low, medium, high, critical]
    required: [type]
```

---

## 4.3 `command` — Reusable .md Files

Loads a reusable command from `.archon/commands/<name>.md`. Prefer this over inline prompts for reusable steps.

```yaml
- id: investigate
  command: investigate-bug
```

**Command file** (`.archon/commands/investigate-bug.md`):
```markdown
---
description: Investigate a GitHub issue and identify root cause
argument-hint: "issue number or description"
---

# Investigate Bug: $ARGUMENTS

## Phase 1: Triage
1. Fetch the issue using `gh issue view`
2. Read linked PRs or commits

## Phase 2: Investigation
1. Search the codebase for relevant files
2. Trace the code path
3. Identify root cause

## Phase 3: Report
Write findings to $ARTIFACTS_DIR/investigation.md
```

Variables available in commands: `$ARGUMENTS`, `$ARTIFACTS_DIR`, `$BASE_BRANCH`, `$WORKFLOW_ID`.

---

## 4.4 `bash` — Deterministic Shell Script

Runs `bash -c`. No AI involved. Stdout captured as `$nodeId.output`. **Always set a timeout.**

```yaml
# Run tests
- id: run-tests
  bash: "npm test -- --coverage 2>&1"
  timeout: 300000     # 5 minutes (in ms, default: 120000)

# Fetch GitHub issue as JSON
- id: fetch-issue
  bash: |
    issue_num=$(echo "$ARGUMENTS" | grep -oE '[0-9]+' | head -1)
    gh issue view "$issue_num" --json title,body,labels
  timeout: 15000

# Guard: check if there are changes
- id: check-diff
  bash: |
    if git diff --quiet; then
      echo "No changes"
    else
      git diff --stat
    fi
  timeout: 10000
```

---

## 4.5 `script` — TypeScript or Python

Deterministic data transforms. More reliable and cheaper than LLM parsing.

**TypeScript (runtime: bun):**
```yaml
- id: parse-labels
  script: |
    try {
      const issue = $fetch-issue.output;   // Injected raw — JSON is valid JS
      const labels = (issue.labels ?? []).map((l) => l.name);
      console.log(JSON.stringify({
        labels,
        count: labels.length,
        hasBug: labels.includes("bug")
      }));
    } catch {
      console.log(JSON.stringify({ labels: [], count: 0, hasBug: false }));
    }
  runtime: bun
  depends_on: [fetch-issue]
  timeout: 10000
```

> **Critical:** `$nodeId.output` is injected RAW. If the upstream output is JSON, assign it directly — NO `String.raw` or `JSON.parse`. `String.raw` breaks if the output contains backticks (common in AI-generated markdown).

**Python (runtime: uv):**
```yaml
- id: calculate-metrics
  script: |
    import json

    data = $run-tests.output
    passed = data.get("numPassedTests", 0)
    failed = data.get("numFailedTests", 0)
    total = passed + failed

    print(json.dumps({
        "pass_rate": round(passed / total * 100, 2) if total else 0,
        "verdict": "PASS" if failed == 0 else "FAIL"
    }))
  runtime: uv
  deps:
    - "numpy>=2.0"
  depends_on: [run-tests]
  timeout: 30000
```

**Named script reference** (file in `.archon/scripts/`):
```yaml
- id: analyze
  script: metrics-analyzer    # Loads .archon/scripts/metrics-analyzer.ts
  runtime: bun
```

---

## 4.6 `loop` — Iterative AI Until Signal

Repeats an AI prompt until a completion signal is detected in the output.

```yaml
- id: implement
  depends_on: [plan]
  loop:
    prompt: |
      Read the plan. Implement the next task. Validate.
      When all tasks complete: <promise>DONE</promise>
    until: DONE
    max_iterations: 10          # Hard stop (default: 5)
    fresh_context: true         # New session each iteration
    idle_timeout: 600000        # Kill if idle for 10 min
```

**How it works:**
1. Prompt sent to Claude Code
2. Claude responds
3. Archon checks: does response contain `DONE`?
4. If NO → increment counter, loop again
5. If YES → loop ends, output = final response
6. If counter > max_iterations → loop FAILS

**`fresh_context: true` vs `false`:**
- `true` — new session each iteration (prevents context explosion, best for independent tasks)
- `false` — session persists (AI remembers previous iterations, context grows)

---

## 4.7 `approval` — Human-in-the-Loop Gate

Pauses the workflow for human review. Technically a loop node with `interactive: true`.

```yaml
- id: approve
  depends_on: [review]
  loop:
    prompt: |
      Present the changes for review.
      Address any feedback from the human reviewer.
      When approved: <promise>APPROVED</promise>
    until: APPROVED
    interactive: true
```

**What happens:**
1. Claude presents changes and waits
2. Workflow PAUSES
3. User sees output and can: APPROVE, REJECT, or give FEEDBACK
4. If FEEDBACK: Claude addresses it, loops back
5. If APPROVED: loop exits, workflow continues

**Common approval gates:** Before PR creation, before deployment, after security-sensitive changes.

---

## 4.8 `cancel` — Early Termination

Terminates the workflow. Status becomes `cancelled`.

```yaml
# Guard clause: no changes → nothing to do
- id: abort-if-none
  depends_on: [check-diff]
  when: "$check-diff.output == 'No changes'"
  cancel: "No changes detected — nothing to commit"

# Precondition check: all deps up to date
- id: abort-if-clean
  depends_on: [check-deps]
  when: "$check-deps.output == '0'"
  cancel: "All dependencies are up to date"
```

---

## 4.9 Common Fields (All Node Types)

| Field | Type | Default | Description |
|---|---|---|---|
| `id` | string | **required** | Unique identifier |
| `depends_on` | string[] | `[]` | Node IDs to wait for |
| `when` | string | — | Condition; skip if false |
| `trigger_rule` | string | `all_success` | Join semantics |
| `context` | `fresh` / `shared` | inherited | Session isolation |
| `idle_timeout` | number | — | Kill if idle (ms) |
| `retry` | object | 2 retries | `{ attempts: 3, backoff: 3000 }` |
| `always_run` | boolean | false | Re-run on resume |
| `output_type` | string | — | Writes typed sidecar |

## 4.10 AI-Only Fields (`prompt` and `command`)

| Field | Type | Default | Description |
|---|---|---|---|
| `provider` | string | inherited | Per-node provider override |
| `model` | string | inherited | Per-node model override |
| `output_format` | object | — | JSON Schema for structured output |
| `allowed_tools` | string[] | all | Restrict tools; `[]` = no tools |

---

## 4.11 Pro Tips

1. **Use `model: haiku` for classification nodes** — fast, cheap, accurate enough for routing
2. **Set `allowed_tools: []` on classification** — no tool calls = instant response
3. **Use `context: fresh` on loop nodes** — prevents context explosion
4. **Always set `timeout` on bash nodes** — default 120s may be too short or too long
5. **Use script nodes for parsing JSON** — deterministic, cheaper than LLM
6. **Separate plan and implement** — two AI nodes with `context: fresh` between them

---

**Try it:** See `examples/workflows/04-smart-issue-fix.yaml` for a workflow using all 7 node types.

**Next:** [05 — Advanced Workflows](./05-advanced-workflows.md)
