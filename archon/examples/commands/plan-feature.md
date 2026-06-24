---
description: Create a detailed implementation plan for a new feature
argument-hint: "feature description"
---

# Plan Feature: $ARGUMENTS

## Phase 1: Research
1. Explore the codebase to understand the current architecture
2. Identify all files that will need changes
3. Note any existing patterns to follow
4. Check for tests that cover related functionality

## Phase 2: Design
1. Define the new interfaces/types
2. Map out the component/file structure
3. Identify data flow and state management
4. Consider edge cases and error states

## Phase 3: Task Breakdown
Create a prioritized task list. Each task should be:
- **Discrete** — one clear deliverable
- **Testable** — has a clear "done" condition
- **Ordered** — dependencies between tasks noted

## Phase 4: Plan Document
Write the plan to $ARTIFACTS_DIR/plan.md:

```markdown
# Feature Plan: [Title]

## Overview
[Brief description of what we're building]

## Architecture
[How it fits into the existing codebase]

## Files to Create/Modify
### New Files
- `path/to/new-file.ts` — [purpose]
### Modified Files
- `path/to/existing.ts` — [what changes]

## Implementation Tasks
1. [Task 1] — [depends on: none]
2. [Task 2] — [depends on: task 1]
3. ...

## Testing Strategy
- Unit tests for [X]
- Integration tests for [Y]
- E2E tests for [Z]

## Risks & Mitigations
- [Risk] → [How we handle it]
```
