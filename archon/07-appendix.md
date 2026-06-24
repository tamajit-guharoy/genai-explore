# 07 — Appendix & Reference

**Goal:** Quick-reference sheets, CLI reference, built-in workflows, glossary.

---

## A.1 CLI Reference

### Setup & Config
```bash
archon --version                  # Show version
archon serve                      # Start Web UI (default port 3000)
archon serve --port 3001          # Custom port
```

### Workflows
```bash
archon workflow list                             # List all available workflows
archon workflow run <name>                       # Run a workflow
archon workflow run <name> --branch <branch>    # Run on specific branch
archon workflow run <name> 'arguments here'      # Run with arguments
```

### From Claude Code
```
claude → "Set up Archon"                             # First-time setup
claude → "Use archon to fix issue #42"               # Run a workflow
claude → "What archon workflows do I have?"          # List workflows
claude → "Use archon to run <workflow-name>"         # Run named workflow
```

### From Source
```bash
cd Archon && bun install      # Install dependencies
cd Archon && bun run dev      # Start dev server
cd Archon && bun test         # Run tests
```

---

## A.2 The 17 Built-in Workflows

Found in `.archon/workflows/defaults/`. Copy to your `.archon/workflows/` to customize.

| # | Workflow | Description |
|---|---|---|
| 1 | `archon-assist` | General Q&A, debugging, code exploration |
| 2 | `archon-fix-github-issue` | Classify → investigate → plan → implement → validate → PR → review → self-fix |
| 3 | `archon-idea-to-pr` | Feature idea → plan → implement → validate → PR → 5 parallel reviews → self-fix |
| 4 | `archon-plan-to-pr` | Execute existing plan → implement → validate → PR → review → self-fix |
| 5 | `archon-issue-review-full` | Fix + full multi-agent review pipeline for GitHub issues |
| 6 | `archon-smart-pr-review` | Classify PR complexity → targeted review agents → synthesize |
| 7 | `archon-comprehensive-pr-review` | 5 parallel reviewers with automatic fixes |
| 8 | `archon-create-issue` | Classify problem → gather context → investigate → create GitHub issue |
| 9 | `archon-validate-pr` | Validate PR testing both main and feature branches |
| 10 | `archon-resolve-conflicts` | Detect → analyze → resolve → validate merge conflicts |
| 11 | `archon-security-audit` | Dependency scan → code analysis → secret detection → report |
| 12 | `archon-documentation` | Generate/update docs from code changes |
| 13 | `archon-refactor` | Identify refactoring → plan → execute → validate |
| 14 | `archon-migrate` | Framework/API migration with validation at each step |
| 15 | `archon-generate-tests` | Analyze code → generate tests → validate coverage |
| 16 | `archon-code-review` | Single-agent focused code review |
| 17 | `archon-release` | Version bump → changelog → tag → release notes |

Override any default:
```bash
cp .archon/workflows/defaults/archon-fix-github-issue.yaml .archon/workflows/my-fix.yaml
```

---

## A.3 Node Type Cheat Sheet

| Type | AI? | Purpose | Minimal Example |
|---|---|---|---|
| `prompt` | Yes | Inline AI prompt | `prompt: "Do X"` |
| `command` | Yes | Load .md file | `command: cmd-name` |
| `bash` | No | Shell script | `bash: "npm test"` + `timeout: 300000` |
| `script` | No | TS/Python transform | `script: "..."` + `runtime: bun` |
| `loop` | Yes | Iterate until signal | `loop: { prompt: "...", until: DONE }` |
| `approval` | Yes | Human gate | `loop: { ..., until: APPROVED, interactive: true }` |
| `cancel` | No | Early termination | `cancel: "Reason"` |

---

## A.4 Trigger Rules

| Rule | Description | When to Use |
|---|---|---|
| `all_success` | ALL deps must succeed (default) | Merge parallel reviews |
| `one_success` | At least ONE dep succeeds | Divergent paths (bug OR feature) |
| `none_failed_min_one_success` | No failures + >=1 success | Fallback approaches |
| `all_done` | All complete regardless of result | Cleanup that MUST run |

---

## A.5 Variable Reference

| Variable | Scope | Description |
|---|---|---|
| `$ARGUMENTS` | All nodes | User's argument string |
| `$ARTIFACTS_DIR` | All nodes | Temp directory for this run |
| `$BASE_BRANCH` | All nodes | Target branch name |
| `$WORKFLOW_ID` | All nodes | Unique run ID |
| `$nodeId.output` | All nodes | Output of completed node |
| `$nodeId.output.field` | All nodes | Field access on structured output |

---

## A.6 YAML Template

```yaml
# .archon/workflows/<name>.yaml
name: my-workflow
description: |
  What this workflow does.

provider: claude
# model: sonnet                # Optional default model
# tags: [Review]               # Optional UI filter tags

nodes:
  - id: step-1
    prompt: "Do something"
    # OR: command: my-command
    # OR: bash: "some command"
    #   timeout: 300000
    # OR: script: "console.log('hello')"
    #   runtime: bun

  - id: step-2
    depends_on: [step-1]
    prompt: "Use: $step-1.output"
    # context: fresh            # Optional: clean session
    # model: haiku              # Optional: different model
    # when: "$step-1.output != ''"  # Optional: conditional

  - id: step-3                    # Parallel to step-2 (no depends_on)
    bash: "npm test"
    timeout: 300000

  - id: step-4
    depends_on: [step-2, step-3]
    prompt: "Synthesize"
```

---

## A.7 Command File Template

```markdown
---
description: Brief description
argument-hint: "what arguments this expects"
---

# Command Title

Task: $ARGUMENTS

## Phase 1: Setup
1. First step with concrete instructions
2. Use specific commands when possible

## Phase 2: Main Work
1. Do the main task
2. Write results to $ARTIFACTS_DIR/<name>.md

## Phase 3: Validation
1. Verify the work
2. Run relevant tests
3. Report findings
```

Save to `.archon/commands/<name>.md`. Reference in workflow: `command: <name>`.

---

## A.8 Comparison Matrix

| Feature | Archon | OpenHands | Hermes | Claude Code | Aider |
|---|---|---|---|---|---|
| **Category** | Workflow Engine | Agent Platform | Personal Agent | AI Coding CLI | AI Coding CLI |
| **Workflow Def** | YAML DAG | Agent-driven | Agent-driven | Ad-hoc | Ad-hoc |
| **Isolation** | Git worktrees | Docker containers | None | None | Git branches |
| **Multi-Agent** | DAG nodes | Sub-agents | Subagents | Sub-agents | No |
| **Persistence** | None (stateless) | Session-level | Memory + skills | Session only | Session only |
| **Enterprise** | No | Yes (RBAC, SSO) | No | No | No |
| **Stars** | 22.5k | 77.9k | N/A | N/A | 30k+ |

---

## A.9 Glossary

| Term | Definition |
|---|---|
| **Workflow** | A YAML file defining a DAG of nodes that orchestrate AI coding tasks |
| **Node** | A single execution step — can be AI-driven or deterministic |
| **DAG** | Directed Acyclic Graph — nodes with dependencies, no cycles at the graph level |
| **Harness** | Infrastructure that controls execution of components |
| **Worktree** | Git worktree — separate working directory linked to same repo |
| **Command** | A `.md` file in `.archon/commands/` — reusable prompt with YAML frontmatter |
| **Script Node** | TypeScript (bun) or Python (uv) code for deterministic data transforms |
| **Loop Node** | Iterative AI execution until a completion signal |
| **Approval Node** | Human-in-the-loop gate that pauses for review |
| **Cancel Node** | Early termination with a reason string |
| **Trigger Rule** | Join semantics when a node has multiple dependencies |
| **Structured Output** | JSON Schema-enforced output from AI nodes |
| **Artifact** | Intermediate file written to `$ARTIFACTS_DIR` for cross-node communication |
| **CLAUDE_BIN_PATH** | Environment variable pointing to Claude Code binary |

---

## A.10 Quick-Start Cheat Sheet

```bash
# Install (30 seconds)
curl -fsSL https://archon.diy/install | bash

# Full setup
git clone https://github.com/coleam00/Archon
cd Archon && bun install && claude
# Say: "Set up Archon"

# Use in your project
cd /path/to/your/project && claude
> Use archon to fix issue #42
> What archon workflows do I have?

# Web UI
archon serve

# Create custom workflow
cp .archon/workflows/defaults/archon-fix-github-issue.yaml \
   .archon/workflows/my-custom-fix.yaml

# Docs
# https://archon.diy/docs/
# https://github.com/coleam00/Archon
```

---

**Sources:**
- [Archon GitHub](https://github.com/coleam00/Archon)
- [Archon Docs](https://archon.diy/docs/)
- [The Book of Archon](https://archon.diy/book/)
- [DeepWiki: coleam00/Archon](https://deepwiki.com/coleam00/Archon)
- [Authoring Workflows Guide](https://github.com/coleam00/Archon/blob/dev/packages/docs-web/src/content/docs/guides/authoring-workflows.md)
