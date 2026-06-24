---
description: Fix a confirmed bug with implementation and validation
argument-hint: "bug description or investigation file path"
---

# Fix Bug: $ARGUMENTS

## Phase 1: Understand the Bug
1. Read the investigation from $ARTIFACTS_DIR/investigation.md (if available)
2. Review the reproduction steps
3. Understand the root cause before writing any code

## Phase 2: Implement Fix
1. Write the minimal fix for the root cause
2. Do NOT refactor unrelated code
3. Do NOT change APIs unless necessary for the fix
4. Follow existing code patterns and conventions

## Phase 3: Validate
1. Run the reproduction script — bug should NO LONGER occur
2. Run the full test suite — no regressions
3. Run type-check/lint — no new errors
4. If anything fails: fix it before declaring done

## Phase 4: Document
Write a summary to $ARTIFACTS_DIR/fix-summary.md:

```markdown
# Fix Summary: [Bug Title]

## Root Cause
[What was wrong]

## Fix Applied
[What changed and why]

## Files Modified
- `path/to/file.ts` — [what changed]

## Verification
- Reproduction test: PASS
- Test suite: PASS (N tests)
- Type-check: PASS
```
