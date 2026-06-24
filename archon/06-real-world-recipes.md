# 06 — Real-World Recipes

**Goal:** Production-ready workflow recipes you can copy and adapt.

**Companion examples:** `examples/workflows/05-review-swarm.yaml`, `06-dependency-update.yaml`, `07-bug-fix.yaml`, `08-migration.yaml`

---

## Recipe 1: End-to-End Bug Fix

Fetch a bug report → reproduce → fix → add regression test → verify → create PR.

```yaml
# .archon/workflows/fix-bug.yaml
name: fix-bug-end-to-end
description: Fetch bug, reproduce, fix, test, create PR

nodes:
  - id: fetch-bug
    bash: |
      num=$(echo "$ARGUMENTS" | grep -oE '[0-9]+' | head -1)
      gh issue view "$num" --json title,body,labels,comments
    timeout: 15000

  - id: analyze
    depends_on: [fetch-bug]
    prompt: |
      Analyze: $fetch-bug.output
      Identify expected vs actual behavior, steps to reproduce, likely code paths.
      Save findings to $ARTIFACTS_DIR/analysis.md
    model: sonnet

  - id: reproduce
    depends_on: [analyze]
    loop:
      prompt: |
        Read $ARTIFACTS_DIR/analysis.md
        Try to reproduce the bug. Write a minimal reproduction script.
        When confirmed: <promise>CONFIRMED</promise>
      until: CONFIRMED
      max_iterations: 3

  - id: implement-fix
    depends_on: [reproduce]
    loop:
      prompt: |
        Implement the fix. After each change: run repro script + test suite.
        When fix complete and tests pass: <promise>DONE</promise>
      until: DONE
      max_iterations: 5

  - id: add-regression-test
    depends_on: [implement-fix]
    prompt: |
      Add a regression test that FAILS without the fix and PASSES with it.

  - id: verify
    depends_on: [add-regression-test]
    bash: "npm test 2>&1"
    timeout: 300000

  - id: create-pr
    depends_on: [verify]
    prompt: |
      Create a PR with: bug fix, regression test, root cause analysis.
      Reference the original issue. Use `gh pr create`.
```

**Design notes:**
- Two separate loop nodes: one for reproduction, one for implementation
- Explicit verification step (bash) before PR — no AI hallucination
- Regression test as separate node (not buried in implementation)

---

## Recipe 2: Multi-Agent PR Review Swarm

5 specialized reviewers run in PARALLEL, then findings are synthesized.

```yaml
# .archon/workflows/pr-review-swarm.yaml
name: comprehensive-pr-review
description: 5 parallel specialized reviewers → synthesize → report

nodes:
  - id: security
    prompt: |
      SECURITY review. Check: injection, auth issues, data leaks,
      unsafe deps, secret exposure.
    model: sonnet

  - id: performance
    prompt: |
      PERFORMANCE review. Check: N+1 queries, blocking I/O, missing
      indexes, memory leaks.
    model: sonnet

  - id: style
    prompt: |
      STYLE review. Check: naming, formatting, docs, dead code, patterns.
    model: haiku

  - id: logic
    prompt: |
      LOGIC review. Check: edge cases, error handling, state management,
      race conditions.
    model: sonnet

  - id: tests
    prompt: |
      TEST review. Check: missing cases, brittle tests, coverage gaps,
      mock appropriateness.
    model: haiku

  - id: synthesize
    depends_on: [security, performance, style, logic, tests]
    prompt: |
      Synthesize all reviews:

      Security: $security.output
      Performance: $performance.output
      Style: $style.output
      Logic: $logic.output
      Tests: $tests.output

      Format as:
      # PR Review Report
      ## Critical Issues (must fix)
      ## Warnings (should fix)
      ## Suggestions (nice to have)
    model: sonnet
```

**Design notes:**
- 5 reviewers run concurrently → ~5x speed vs sequential
- Mixed models: sonnet for security/perf/logic, haiku for style/coverage
- Single synthesis → user gets one report

---

## Recipe 3: Feature Scaffolding

Idea → plan → scaffold (structure) → implement (logic) → validate → approve → PR.

```yaml
# .archon/workflows/feature-scaffold.yaml
name: idea-to-pr
description: Feature idea → plan → scaffold → implement → test → approve → PR

nodes:
  - id: plan
    prompt: |
      I need to implement: $ARGUMENTS
      1. Explore the codebase
      2. Identify files needing changes
      3. Create detailed implementation plan
      Save to $ARTIFACTS_DIR/plan.md
    model: sonnet

  - id: scaffold
    depends_on: [plan]
    prompt: |
      Read $ARTIFACTS_DIR/plan.md
      Create the scaffolding: new files, interfaces, stubs, route declarations.
      Do NOT implement logic yet — just the skeleton.
    model: sonnet
    context: fresh

  - id: implement
    depends_on: [scaffold]
    loop:
      prompt: |
        Read $ARTIFACTS_DIR/plan.md
        Implement next task. After each: type-check + test.
        When ALL tasks complete: <promise>DONE</promise>
      until: DONE
      max_iterations: 10

  - id: validate
    depends_on: [implement]
    bash: "npx tsc --noEmit && npm test && npm run lint"
    timeout: 300000

  - id: approve
    depends_on: [validate]
    loop:
      prompt: |
        Present changes for review. Address any feedback.
        When approved: <promise>APPROVED</promise>
      until: APPROVED
      interactive: true

  - id: create-pr
    depends_on: [approve]
    prompt: "Create PR with feature description, testing instructions. Use `gh pr create`"
```

**Design notes:**
- Separate `scaffold` step before `implement` — AI creates structure first, then fills logic
- Easier to review, less likely to go off track

---

## Recipe 4: Dependency Update Pipeline

Check outdated → parse → update (if needed) → test → PR.

```yaml
# .archon/workflows/update-deps.yaml
name: update-dependencies
description: Check outdated deps, update minor/patch, test, create PR

nodes:
  - id: check-outdated
    bash: "npm outdated --json 2>/dev/null || echo '{}'"
    timeout: 30000

  - id: parse-outdated
    script: |
      try {
        const data = $check-outdated.output;
        const updates = Object.entries(data).map(([name, info]) => ({
          name, current: info.current, latest: info.latest, type: info.type
        }));
        const minor = updates.filter(u => u.type === 'minor' || u.type === 'patch');
        console.log(JSON.stringify({ total: updates.length, count: minor.length }));
      } catch {
        console.log(JSON.stringify({ total: 0, count: 0 }));
      }
    runtime: bun
    depends_on: [check-outdated]
    timeout: 10000

  - id: abort-if-none
    depends_on: [parse-outdated]
    when: "$parse-outdated.output.count == 0"
    cancel: "All dependencies up to date"

  - id: update
    depends_on: [parse-outdated]
    when: "$parse-outdated.output.count > 0"
    bash: "npm update"
    timeout: 120000

  - id: test
    depends_on: [update]
    bash: "npm test 2>&1"
    timeout: 300000

  - id: create-pr
    depends_on: [test]
    prompt: |
      Create PR for dependency updates.
      Updated: $parse-outdated.output
      Use `gh pr create`
```

**Design notes:**
- `cancel` node as guard clause — terminates cleanly when nothing to do
- Script node parses JSON deterministically (cheaper than LLM)
- Only runs `npm update` + tests when there are actual outdated packages

---

## Recipe 5: Code Migration

Structured approach with validation at every step.

```yaml
# .archon/workflows/migrate.yaml
name: migrate-framework
description: Structured migration with validation at each step

nodes:
  - id: analyze
    prompt: |
      Analyze the code at: $ARGUMENTS
      Document every endpoint, middleware, schema, dependency.
    model: sonnet

  - id: plan
    depends_on: [analyze]
    prompt: |
      Create migration plan. Map old patterns → new patterns.
      Identify breaking changes. Save to $ARTIFACTS_DIR/migration-plan.md
    model: sonnet
    context: fresh

  - id: migrate
    depends_on: [plan]
    loop:
      prompt: |
        Implement migration one step at a time.
        After each step: type-check + test.
        When complete: <promise>DONE</promise>
      until: DONE
      max_iterations: 8

  - id: verify
    depends_on: [migrate]
    bash: "npx tsc --noEmit && npm test && npm run lint"
    timeout: 300000

  - id: create-pr
    depends_on: [verify]
    prompt: |
      Create PR for migration. List: what was migrated, breaking changes.
```

**Adapt for:** React class → hooks, JS → TS, REST → GraphQL, MySQL → PostgreSQL.

---

## Recipe 6: CI Wait-and-Merge

Create PR → poll CI → merge when green.

```yaml
# .archon/workflows/wait-ci-merge.yaml
name: wait-ci-then-merge
description: Create PR, poll CI, merge when green

nodes:
  - id: create-pr
    prompt: "Push changes and create PR with `gh pr create`"

  - id: wait-ci
    depends_on: [create-pr]
    bash: |
      pr_url=$(echo "$create-pr.output" | grep -oE 'https://github.com/[^ ]*/pull/[0-9]*')
      pr_num=$(echo "$pr_url" | grep -oE '[0-9]*$')
      max_wait=30
      waited=0
      while [ $waited -lt $max_wait ]; do
        status=$(gh pr view "$pr_num" --json statusCheckRollup 2>/dev/null | jq -r '.statusCheckRollup[0].conclusion // "PENDING"')
        echo "[$waited/$max_wait] Status: $status"
        case "$status" in
          SUCCESS) echo "CI PASSED"; exit 0;;
          FAILURE) echo "CI FAILED"; exit 1;;
          *) sleep 30; waited=$((waited + 1));;
        esac
      done
      echo "Timeout"; exit 1
    timeout: 1800000        # 30 min
    retry:
      attempts: 1            # No retry on CI failure

  - id: merge
    depends_on: [wait-ci]
    prompt: "CI passed. Merge PR with `gh pr merge --squash`"
```

> **Warning:** Auto-merge is risky. Consider adding an `approval` node before `merge`.

---

**Next:** [07 — Appendix & Reference](./07-appendix.md)

**Try all recipes:** Copy from `examples/workflows/` to your `.archon/workflows/`
