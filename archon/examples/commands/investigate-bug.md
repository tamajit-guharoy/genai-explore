---
description: Investigate a GitHub issue and identify the root cause
argument-hint: "issue number or description"
---

# Investigate Bug: $ARGUMENTS

## Phase 1: Triage
1. Fetch the issue details using `gh issue view`
2. Read any linked PRs or commits
3. Classify severity: low / medium / high / critical
4. Check if there are reproduction steps

## Phase 2: Investigation
1. Search the codebase for relevant files using grep/ripgrep
2. Trace the code path involved in the bug
3. Identify potential root causes
4. Look for similar patterns that might have the same bug

## Phase 3: Root Cause Analysis
Determine the root cause and document:
- What the bug is
- Why it happens
- What code path triggers it
- Whether it's a logic error, missing validation, race condition, etc.

## Phase 4: Report
Write findings to $ARTIFACTS_DIR/investigation.md with:

```markdown
# Bug Investigation: [Title]

## Root Cause
[Detailed explanation]

## Affected Files
- `path/to/file1.ts` — [what's wrong]
- `path/to/file2.ts` — [what's wrong]

## Suggested Fix
[High-level approach]

## Estimated Complexity
[low / medium / high] — [rationale]

## Reproduction
[Steps to reproduce]
```
