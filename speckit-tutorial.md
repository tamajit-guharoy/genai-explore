# Spec Kit Tutorial: The Complete Guide to Spec-Driven Development with GitHub Spec Kit

> **Authoritative references:**
> - GitHub: https://github.com/github/spec-kit (28k+ stars, MIT)
> - Docs: https://github.github.io/spec-kit/
> - Package: `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git`
> - Written: June 2026 | Tested against: Spec Kit latest release

---

## Table of Contents

1. [What is Spec Kit?](#1-what-is-spec-kit)
2. [Why Spec-Driven Development (SDD)?](#2-why-spec-driven-development-sdd)
3. [Installation & Setup](#3-installation--setup)
4. [Core Concepts & Philosophy](#4-core-concepts--philosophy)
5. [All Commands — Complete Reference](#5-all-commands--complete-reference)
6. [Directory Structure — Every File & Folder Explained](#6-directory-structure--every-file--folder-explained)
7. [The Spec Kit Workflow: Constitution → Implement](#7-the-spec-kit-workflow-constitution--implement)
8. [The Constitution: Nine Articles of Development](#8-the-constitution-nine-articles-of-development)
9. [Specify: Writing the Spec (Phase 1)](#9-specify-writing-the-spec-phase-1)
10. [Clarify: Resolving Ambiguity (Phase 1.5)](#10-clarify-resolving-ambiguity-phase-15)
11. [Checklist: Validating Requirements (Phase 1.6)](#11-checklist-validating-requirements-phase-16)
12. [Plan: Creating the Implementation Plan (Phase 2)](#12-plan-creating-the-implementation-plan-phase-2)
13. [Tasks: Breaking Down into Executable Steps (Phase 3)](#13-tasks-breaking-down-into-executable-steps-phase-3)
14. [Analyze: Cross-Artifact Consistency (Phase 3.5)](#14-analyze-cross-artifact-consistency-phase-35)
15. [Implement: Code Generation (Phase 4)](#15-implement-code-generation-phase-4)
16. [Greenfield Projects (0→1) — Complete Walkthrough](#16-greenfield-projects-01--complete-walkthrough)
17. [Brownfield Projects (1→n) — Complete Walkthrough](#17-brownfield-projects-1n--complete-walkthrough)
18. [Practical Example 1: Build a Photo Album App (Greenfield)](#18-practical-example-1-build-a-photo-album-app-greenfield)
19. [Practical Example 2: Add Features + Deprecate (Brownfield)](#19-practical-example-2-add-features--deprecate-brownfield)
20. [Template-Driven Quality: How Constraints = Better Code](#20-template-driven-quality-how-constraints--better-code)
21. [Extensions & Presets: Customizing Spec Kit](#21-extensions--presets-customizing-spec-kit)
22. [CLI Reference](#22-cli-reference)
23. [Supported AI Agents](#23-supported-ai-agents)
24. [Spec Kit vs Alternatives](#24-spec-kit-vs-alternatives)
25. [Best Practices](#25-best-practices)
26. [Troubleshooting](#26-troubleshooting)
27. [Cheat Sheet](#27-cheat-sheet)

---

## 1. What is Spec Kit?

**Spec Kit** is an open-source (MIT) toolkit from GitHub for **Spec-Driven Development (SDD)**. It provides a structured, command-driven workflow that transforms natural language specifications into working code through AI coding agents.

### The Core Idea

> "Specifications don't serve code — code serves specifications."

In traditional development, specs are scaffolding you build and discard once "real work" begins. In Spec Kit, the spec IS the source of truth. Code is a generated artifact derived from it. You write WHAT you want and WHY. The AI figures out HOW.

### What Spec Kit Is

- A **CLI tool** (`specify`) that bootstraps project structure for SDD
- A set of **9 slash commands** that guide AI through Constitution → Specify → Plan → Tasks → Implement
- A **template system** that enforces quality through structured constraints
- A **constitutional framework** that bakes architectural principles into every feature
- An **extension & preset system** for deep customization

### What Spec Kit Is NOT

- A code generator that runs standalone (you need an AI coding agent)
- A replacement for your IDE
- A "one-prompt-to-app" tool
- A full project management suite (though it integrates with GitHub Issues)

### Philosophy

```
Focus on WHAT        → Describe the product, not the tech stack
Constitutional       → Immutable principles guide all development
Template-Driven      → Structured templates constrain AI to quality output
Branch-Centric       → Each feature is a branch with isolated specs
Spec-First           → Specs exist before code, generate code, outlast code
Intent-Driven        → Natural language drives everything; code is "last mile"
```

---

## 2. Why Spec-Driven Development (SDD)?

### The Problem: Vibe Coding at Scale

```
You:    "Add pagination to the users API"
AI:     [guesses offset-based, page=1, limit=20, returns total_count]
You:    "No, cursor-based, not offset"
AI:     [rewrites everything]
You:    "And don't change the schema"
AI:     [rewrites again]
Total:  3 rounds, 45 minutes, frustration
```

Vibe coding works for prototypes. It breaks at scale because:
- "Truth" lives in chat history that resets when context windows fill up
- No traceability between requirements and code
- Agents make plausible but wrong assumptions
- Each iteration loses context from previous ones

### The Solution: Spec-First

```
You:    [Write 15-line spec in 5 minutes:
         - Cursor-based pagination on created_at
         - Default 50, max 200
         - Returns next_cursor (opaque base64) and has_more
         - Backward compatible (no cursor = page 1)]

AI:     [Reads spec, implements exactly once]
Total:  1 round, 15 minutes, done
```

### Prompts vs Specs

| Dimension | Prompt | Spec |
|---|---|---|
| **Ambiguity** | High — agent fills gaps with guesses | Low — requirements and constraints explicit |
| **Reviewability** | Subjective — "does this look right?" | Objective — "do acceptance criteria pass?" |
| **Reusability** | One-shot, conversation-specific | Checked into git, reusable across sessions |
| **Autonomous work** | Requires human in the loop | Agent works independently against criteria |
| **Debugging** | "Why did it do that?" | "Spec was incomplete" or "agent didn't follow spec" |
| **Team scale** | Solo only | Team: specs are reviewable, diffable, version-controlled |

### The Three Questions SDD Answers

1. **WHAT are we building?** → Spec (`/speckit.specify`)
2. **HOW will we build it?** → Plan (`/speckit.plan`)
3. **In WHAT ORDER?** → Tasks (`/speckit.tasks`)

---

## 3. Installation & Setup

### Prerequisites

- **Python 3.11+**
- **`uv`** (recommended) or `pipx` (for persistent install)
- **Git**
- **An AI coding agent**: Claude Code, GitHub Copilot, Cursor, Gemini CLI, Codex, Windsurf, etc. (30+ supported)
- **Linux / macOS / Windows** (Bash and PowerShell scripts provided)

### Method 1: One-shot with `uvx` (Recommended for Quick Start)

```bash
# Create a new project:
uvx --from git+https://github.com/github/spec-kit.git specify init my-project

# Or initialize in current directory:
cd existing-project
uvx --from git+https://github.com/github/spec-kit.git specify init .
```

### Method 2: Persistent Install with `uv tool`

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git

# Then use directly:
specify init my-project
specify init .
```

### Method 3: Persistent Install with `pipx`

```bash
pipx install git+https://github.com/github/spec-kit.git

specify init my-project
```

### Choosing Your AI Agent

```bash
# With integration flag:
specify init my-project --integration claude      # Claude Code
specify init my-project --integration copilot     # GitHub Copilot
specify init my-project --integration cursor-agent # Cursor
specify init my-project --integration codex       # Codex CLI
specify init my-project --integration gemini      # Gemini CLI
specify init my-project --integration hermes      # Hermes Agent

# Skills mode (for agents that support it):
specify init my-project --integration codex --integration-options="--skills"

# List all available integrations:
specify integration list
```

### What `specify init` Creates

```
my-project/
├── .specify/
│   ├── memory/
│   │   └── constitution.md           # Project principles (template, filled by /speckit.constitution)
│   ├── scripts/
│   │   └── bash/
│   │       ├── check-prerequisites.sh
│   │       ├── common.sh
│   │       ├── create-new-feature.sh  # Creates feature branch + spec scaffold
│   │       ├── setup-plan.sh          # Prepares plan artifacts
│   │       └── setup-tasks.sh         # Prepares tasks artifacts
│   └── templates/
│       ├── spec-template.md           # Template for feature specifications
│       ├── plan-template.md           # Template for implementation plans
│       ├── tasks-template.md          # Template for task breakdowns
│       └── CLAUDE-template.md         # Project-level AI instructions
│
├── specs/                             # Feature specifications live here (empty initially)
│
├── .claude/
│   └── commands/                      # Slash commands (for Claude Code integration)
│       ├── speckit.constitution.md
│       ├── speckit.specify.md
│       ├── speckit.clarify.md
│       ├── speckit.checklist.md
│       ├── speckit.plan.md
│       ├── speckit.tasks.md
│       ├── speckit.analyze.md
│       └── speckit.implement.md
│
└── CLAUDE.md                          # Project context file (generated)
```

### Verifying Installation

```bash
specify --version    # Check version
specify self check   # Check for updates
specify self upgrade # Upgrade to latest
```

---

## 4. Core Concepts & Philosophy

### The Power Inversion

```
Traditional:  Code is King. Specs serve code. Code drifts from intent.

SDD:          Spec is King. Code serves specs. Intent IS the source of truth.
```

### The Four-Phase Lifecycle

```
┌───────────────────────────────────────────────────────────────┐
│  Phase 1: SPECIFY          │  Phase 2: PLAN                   │
│  ─────────────────         │  ───────────────                 │
│  /speckit.specify           │  /speckit.plan                   │
│  WHAT and WHY               │  HOW — tech stack, architecture  │
│  User stories, FRs, NFRs   │  API contracts, data models      │
│  Acceptance criteria        │  Research, quickstart guide      │
│                             │                                  │
│  Quality Gates:             │  Quality Gates:                  │
│  /speckit.clarify (before)  │  /speckit.checklist (before)     │
│                             │                                  │
├─────────────────────────────┼──────────────────────────────────┤
│  Phase 3: TASKS             │  Phase 4: IMPLEMENT              │
│  ──────────────             │  ──────────────────              │
│  /speckit.tasks             │  /speckit.implement               │
│  Executable task list       │  Code generation                 │
│  Dependencies, order        │  TDD execution                   │
│  Parallel [P] markers       │  Progress tracking               │
│                             │                                  │
│  Quality Gate:              │  Quality Gate:                   │
│  /speckit.analyze (before)  │  /speckit.analyze (after, opt.)  │
└───────────────────────────────────────────────────────────────┘
```

### Two Workflow Paths

**Lean Path** (quick experiments, simple features):
```
/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

**Production Path** (anything with meaningful ambiguity):
```
/speckit.constitution
    → /speckit.specify
    → /speckit.clarify      ← de-risk before planning
    → /speckit.checklist    ← validate before planning
    → /speckit.plan
    → /speckit.tasks
    → /speckit.analyze      ← catch gaps before implementation
    → /speckit.implement
    → /speckit.analyze      ← optional post-implement review
```

### Branch-Centric Design

Every feature lives on its own branch:

```
main
├── 001-create-taskify/       # Feature 1: spec + plan + tasks
├── 002-photo-albums/         # Feature 2: spec + plan + tasks
├── 003-dark-mode/            # Feature 3: spec + plan + tasks
└── ...
```

Spec Kit commands auto-detect the active feature from your Git branch name. Switch branches to work on different specs. This isolates documentation and prevents cross-feature context pollution.

---

## 5. All Commands — Complete Reference

### Core Commands (Required)

| Command | Agent Skill | Phase | Purpose | Input | Output Files |
|---|---|---|---|---|---|
| `/speckit.constitution` | `speckit-constitution` | 0 | Define governing principles | Project principles as arguments | `.specify/memory/constitution.md` |
| `/speckit.specify` | `speckit-specify` | 1 | Create feature specification | Feature description (WHAT + WHY) | `specs/<branch>/spec.md` + new branch |
| `/speckit.plan` | `speckit-plan` | 2 | Create technical implementation plan | Tech stack + architecture choices | `specs/<branch>/plan.md`, `data-model.md`, `research.md`, `contracts/`, `quickstart.md` |
| `/speckit.tasks` | `speckit-tasks` | 3 | Generate executable task list | (reads plan.md) | `specs/<branch>/tasks.md` |
| `/speckit.implement` | `speckit-implement` | 4 | Execute implementation | (reads tasks.md) | Working code + tests |
| `/speckit.taskstoissues` | `speckit-taskstoissues` | 3.5 | Convert tasks to GitHub Issues | (reads tasks.md) | GitHub Issues |

### Optional Quality Gate Commands

| Command | Agent Skill | When to Run | Purpose | Output |
|---|---|---|---|---|
| `/speckit.clarify` | `speckit-clarify` | After specify, before plan | Resolve ambiguities via structured Q&A | Updated `spec.md` with Clarifications section |
| `/speckit.checklist` | `speckit-checklist` | After specify/clarify, before plan | Generate quality checklist for requirements | Custom checklist; validated `spec.md` |
| `/speckit.analyze` | `speckit-analyze` | After tasks, before implement | Cross-artifact consistency check | Analysis report flagging gaps |

### Command Placement Rules

```
MUST run after:        /speckit.constitution before /speckit.specify
                       /speckit.specify before /speckit.plan
                       /speckit.plan before /speckit.tasks
                       /speckit.tasks before /speckit.implement

MUST NOT skip:         /speckit.clarify before /speckit.plan (for production)
                       /speckit.analyze before /speckit.implement (for production)

CAN skip:              /speckit.clarify (explicitly state if skipping)
                       /speckit.checklist (for quick experiments)
                       /speckit.analyze (for quick experiments)
```

### Detailed Command Behavior

#### `/speckit.constitution`

**What it does:**
1. Reads the constitution template at `.specify/templates/constitution-template.md`
2. Identifies all `[PLACEHOLDER_TOKENS]` in the template
3. Fills tokens from your provided principles, or infers from project context
4. Creates/updates `.specify/memory/constitution.md`
5. Propagates changes to dependent templates

**Example:**
```
/speckit.constitution This project follows a "Library-First" approach.
All features must be implemented as standalone libraries first.
We use TDD strictly. We prefer functional programming patterns.
```

**Constitutional principles typically include:**
- Code quality standards
- Testing requirements (TDD, coverage thresholds)
- Architecture rules (max projects, no premature abstraction)
- Performance requirements
- Security/privacy rules
- UX consistency principles

#### `/speckit.specify`

**What it does:**
1. Scans existing specs to determine next feature number (001, 002, 003...)
2. Generates a semantic branch name from your description
3. Creates and switches to the feature branch
4. Copies the spec template and customizes it with your requirements
5. Generates user stories, functional requirements, success criteria, edge cases

**Key constraint:** Focus on WHAT and WHY. The template explicitly instructs:
```
✅ Focus on WHAT users need and WHY
❌ Avoid HOW to implement (no tech stack, APIs, code structure)
```

**Example:**
```
/speckit.specify Build an application that can help me organize my photos
in separate photo albums. Albums are grouped by date and can be re-organized
by dragging and dropping on the main page. Albums are never in other nested
albums. Within each album, photos are previewed in a tile-like interface.
```

#### `/speckit.clarify`

**What it does:**
1. Reads the spec.md for `[NEEDS CLARIFICATION]` markers
2. Conducts structured, sequential, coverage-based questioning
3. Records all answers in a Clarifications section in spec.md
4. Resolves ambiguity BEFORE planning (reduces downstream rework)

**Example:**
```
/speckit.clarify Focus on security and performance requirements
```

#### `/speckit.checklist`

**What it does:**
1. Reads the spec.md
2. Generates a custom quality checklist ("unit tests for English")
3. Validates requirements completeness, clarity, consistency
4. Identifies missing edge cases, contradictions, untestable claims

**Example checklist items:**
```
### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
- [ ] Edge cases identified
- [ ] Non-functional requirements covered
```

#### `/speckit.plan`

**What it does:**
1. Reads the specification (`spec.md`)
2. Reads the constitution for architectural principles
3. Translates business requirements into technical architecture
4. Generates supporting documents:
   - `plan.md` — Implementation plan with phases, gates, file creation order
   - `research.md` — Technology comparisons, rationale for choices
   - `data-model.md` — Database schema, entity relationships
   - `contracts/` — API specifications (OpenAPI), WebSocket events
   - `quickstart.md` — Key validation scenarios
5. Runs constitutional compliance gates (Phase -1 checks)

**Example:**
```
/speckit.plan The application uses Vite with minimal number of libraries.
Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not
uploaded anywhere and metadata is stored in a local SQLite database.
```

#### `/speckit.tasks`

**What it does:**
1. Reads `plan.md` (required) and optionally `data-model.md`, `contracts/`, `research.md`
2. Converts contracts, entities, and scenarios into specific tasks
3. Orders tasks by dependency
4. Marks independent tasks with `[P]` (parallelizable)
5. Organizes tasks by user story (each story = implementation phase)
6. Includes TDD ordering: test tasks BEFORE implementation tasks
7. Includes checkpoint validation after each user story

**Output structure:**
```markdown
## Phase 1: User Story 1 — Create Album
- [ ] T001 [P] Write contract tests for POST /albums
- [ ] T002 [P] Write unit tests for Album model
- [ ] T003 Create Album model at src/models/album.js
- [ ] T004 Create albums API endpoint at src/routes/albums.js
- [ ] T005 Integration test for album creation flow

**Checkpoint**: Albums can be created and retrieved
```

#### `/speckit.analyze`

**What it does:**
1. Validates prerequisites: constitution, spec, plan, tasks must exist
2. Cross-references all artifacts for consistency:
   - Does the plan cover every spec requirement?
   - Do tasks trace back to plan decisions and spec requirements?
   - Are there gaps, contradictions, or orphaned tasks?
3. Produces an analysis report with findings

**Run before** `/speckit.implement` so gaps can be fixed while plan/tasks are still adjustable. Optionally re-run after implementation as an extra review.

#### `/speckit.implement`

**What it does:**
1. Validates all prerequisites are in place
2. Parses the task breakdown from `tasks.md`
3. Executes tasks in order, respecting dependencies
4. Follows TDD: tests first, then implementation
5. Runs parallel tasks `[P]` concurrently where possible
6. Provides progress updates
7. Handles errors and continues where possible

#### `/speckit.taskstoissues`

**What it does:**
1. Reads `tasks.md`
2. Creates GitHub Issues for each task
3. Preserves dependency structure via issue references
4. Links back to the spec branch

---

## 6. Directory Structure — Every File & Folder Explained

### At Init-Time (after `specify init`)

```
my-project/
├── .specify/                              # Spec Kit scaffolding (managed by CLI)
│   ├── memory/
│   │   └── constitution.md                #   TEMPLATE with [PLACEHOLDER_TOKENS]
│   │                                      #   Filled by /speckit.constitution
│   │                                      #   Read by every command for principles
│   │
│   ├── scripts/bash/                      #   Automation scripts (Bash + PS)
│   │   ├── common.sh                      #     Shared functions
│   │   ├── check-prerequisites.sh         #     Validates env before commands
│   │   ├── create-new-feature.sh          #     Creates branch + spec scaffold
│   │   ├── setup-plan.sh                  #     Prepares plan template
│   │   └── setup-tasks.sh                 #     Prepares tasks template
│   │
│   └── templates/                         #   Document templates
│       ├── spec-template.md               #     Feature specification template
│       ├── plan-template.md               #     Implementation plan template
│       ├── tasks-template.md              #     Task breakdown template
│       └── CLAUDE-template.md             #     Project-level AI instruction template
│
├── specs/                                 # Feature specifications (per-branch)
│   └── (empty initially)
│
├── .claude/commands/                      # Slash commands for Claude Code
│   ├── speckit.constitution.md
│   ├── speckit.specify.md
│   ├── speckit.clarify.md
│   ├── speckit.checklist.md
│   ├── speckit.plan.md
│   ├── speckit.tasks.md
│   ├── speckit.analyze.md
│   └── speckit.implement.md
│
└── CLAUDE.md                              # Project context for AI agent
```

### Per-Feature (after running through the workflow)

```
specs/001-photo-albums/
├── spec.md                # Phase 1: Feature specification (user stories, FRs, NFRs)
├── plan.md                # Phase 2: Implementation plan (architecture, phases)
├── research.md            # Phase 2: Technology research (library comparsons, benchmarks)
├── data-model.md          # Phase 2: Database schema, entity relationships
├── quickstart.md          # Phase 2: Key validation scenarios, setup instructions
├── tasks.md               # Phase 3: Executable task breakdown (ordered, parallel markers)
│
└── contracts/             # Phase 2: API and event contracts
    ├── api-spec.json      #   REST API specification (OpenAPI format)
    └── signalr-spec.md    #   Real-time event specifications (if applicable)
```

### After Extensions/Presets

```
.specify/
├── extensions/            # Installed extensions (new capabilities)
│   └── templates/         #   Extension-specific templates
├── presets/               # Installed presets (existing workflow overrides)
│   └── templates/         #   Preset-specific template overrides
└── templates/
    └── overrides/         # Project-local one-off overrides (highest priority)
```

### File Purpose Summary

| File | Phase | Created By | Purpose | Editable? |
|---|---|---|---|---|
| `.specify/memory/constitution.md` | 0 | `/speckit.constitution` | Immutable project principles | Yes — via `/speckit.constitution` |
| `specs/<feature>/spec.md` | 1 | `/speckit.specify` | WHAT: user stories, requirements, acceptance criteria | Yes — refine with agent |
| `specs/<feature>/plan.md` | 2 | `/speckit.plan` | HOW: architecture, tech decisions, phase gates | Yes — refine with agent |
| `specs/<feature>/research.md` | 2 | `/speckit.plan` | Technology evaluation, rationale, benchmarks | Yes |
| `specs/<feature>/data-model.md` | 2 | `/speckit.plan` | Database schema, entity diagrams | Yes |
| `specs/<feature>/contracts/` | 2 | `/speckit.plan` | API specs, event contracts | Yes |
| `specs/<feature>/quickstart.md` | 2 | `/speckit.plan` | Validation scenarios, setup guide | Yes |
| `specs/<feature>/tasks.md` | 3 | `/speckit.tasks` | Executable, ordered task list | Yes — regenerate with `/speckit.tasks` |
| `CLAUDE.md` | Any | `specify init` | Project-level AI instructions | Yes |

---

## 7. The Spec Kit Workflow: Constitution → Implement

### Production Path (Complete)

```
Step 1:  /speckit.constitution    → Define immutable project principles
Step 2:  /speckit.specify         → Create feature spec (WHAT + WHY)
Step 3:  /speckit.clarify         → Resolve ambiguities via structured Q&A
Step 4:  /speckit.checklist       → Validate requirements quality
Step 5:  /speckit.plan            → Create technical implementation plan (HOW)
Step 6:  Review + Audit           → Manually audit plan for gaps, over-engineering
Step 7:  /speckit.tasks           → Generate executable task list
Step 8:  /speckit.analyze         → Cross-artifact consistency check
Step 9:  /speckit.implement       → Execute: code generation, TDD, progress
Step 10: Manual test + iterate    → Test, fix runtime errors, iterate
```

### Lean Path (Quick Experiments)

```
Step 1: /speckit.specify   → Feature spec
Step 2: /speckit.plan      → Implementation plan
Step 3: /speckit.tasks     → Task list
Step 4: /speckit.implement → Execute
```

### Key Workflow Rules

1. **Review at every step**: The AI's first attempt is NOT final. Read outputs. Refine. Ask for clarification.
2. **Do NOT treat the AI's output as final**: Challenge it. Ask "why did you choose X over Y?" Force rationale.
3. **Constitution is immutable**: Every `/speckit.plan` and `/speckit.implement` references it. Changes require documented rationale.
4. **Branch per feature**: Each `/speckit.specify` creates a branch. Context is isolated.
5. **Audit the plan**: Before implementation, ask the agent: "Read the plan as a critic. What's over-engineered? What's missing?"
6. **Cross-check with checklist**: Ask the agent: "Check off each item in the review checklist that passes. Leave empty if not."

---

## 8. The Constitution: Nine Articles of Development

The constitution (`.specify/memory/constitution.md`) is Spec Kit's most powerful concept. It's **immutable** — it doesn't change per feature. Every plan and every implementation must pass constitutional gates. This ensures ALL generated code follows the same principles, regardless of which AI agent or which session generated it.

### The Full Nine Articles

#### Article I: Library-First Principle

> Every feature MUST begin as a standalone library. No feature shall be implemented directly within application code without first being abstracted into a reusable library component.

**Enforces:** Modular design. Clear boundaries. Minimal dependencies.

#### Article II: CLI Interface Mandate

> All CLI interfaces MUST accept text as input (stdin, args, or files) and produce text as output (stdout). Must support JSON for structured data exchange.

**Enforces:** Observability. Testability. Everything is inspectable.

#### Article III: Test-First Imperative (NON-NEGOTIABLE)

> All implementation MUST follow strict TDD. No implementation code shall be written before:
> 1. Unit tests are written
> 2. Tests are validated and approved
> 3. Tests are confirmed to FAIL (Red phase)

**Enforces:** Tests exist before code. AI generates tests first, gets approval, THEN implements.

#### Article IV: Code Quality Standards

> Defines linting, formatting, complexity limits, documentation requirements.

#### Article V: Testing Standards

> Coverage thresholds, test types (unit, integration, contract, e2e), test data policies.

#### Article VI: UX Consistency

> Design system adherence, accessibility standards, responsive design requirements.

#### Article VII: Simplicity Principle

> Maximum 3 projects for initial implementation. Additional projects require documented justification. No future-proofing. No speculative features.

**Enforces:** Anti-over-engineering. Justify every layer of complexity.

#### Article VIII: Anti-Abstraction Principle

> Use framework features directly rather than wrapping them. Single model representation. No premature generalization.

**Enforces:** Don't wrap what the framework already gives you. Don't abstract until you have 3+ use cases.

#### Article IX: Integration-First Testing

> Use realistic environments. Prefer real databases over mocks. Use actual service instances over stubs. Contract tests mandatory before implementation.

**Enforces:** Tests that actually validate production behavior.

### Constitutional Enforcement: The Phase -1 Gates

Every `/speckit.plan` includes pre-implementation gates that check constitutional compliance:

```markdown
### Phase -1: Pre-Implementation Gates

#### Simplicity Gate (Article VII)
- [ ] Using ≤3 projects?
- [ ] No future-proofing?
- [ ] No speculative features?

#### Anti-Abstraction Gate (Article VIII)
- [ ] Using framework directly (no wrappers)?
- [ ] Single model representation?
- [ ] No premature abstractions?

#### Integration-First Gate (Article IX)
- [ ] Contracts defined?
- [ ] Contract tests written?
- [ ] Real database used (not mocks)?

#### Library-First Gate (Article I)
- [ ] Feature isolated as library?
- [ ] Minimal dependencies?
- [ ] CLI interface exposed?
```

If a gate fails, the agent must document justification in a "Complexity Tracking" section. No silent violations allowed.

### Constitutional Evolution (Section 4.2)

The constitution can be amended — but only with:
1. Explicit documentation of rationale
2. Review and approval by project maintainers
3. Backwards compatibility assessment

Amendments are versioned and dated. This allows the methodology to learn while maintaining stability.

---

## 9. Specify: Writing the Spec (Phase 1)

### What Happens When You Run `/speckit.specify`

```
Input:  "Build a photo album app where albums are grouped by date and
         photos show in a tile interface."

Behind the scenes:
1. CLI scans specs/ → finds 000, so this is 001
2. Generates branch: 001-photo-album-app
3. Creates branch + switches to it
4. Copies spec-template.md → specs/001-photo-album-app/spec.md
5. Agent fills template with structured spec:
   - User stories (As a... I want... So that...)
   - Functional requirements (with acceptance criteria)
   - Non-functional requirements
   - Success criteria (measurable)
   - Edge cases
   - [NEEDS CLARIFICATION] markers for ambiguities
```

### What a Good Spec Contains

```markdown
# Feature Specification: Photo Album Organizer

## User Stories
### US-001: Create Album
As a user, I want to create a new photo album so that I can organize my photos.

**Acceptance Criteria:**
- Album name is required (1-100 chars)
- Album is grouped by creation date on the main page
- Albums cannot be nested (flat structure only)

### US-002: Upload Photos
As a user, I want to upload photos into an album so that I can view them later.

**Acceptance Criteria:**
- Supports JPEG, PNG, WebP formats
- Max file size: 10MB per photo
- Photos appear as tiles in the album view
- Upload progress indicator shown

## Functional Requirements
### FR-001: Album Management
The system SHALL allow users to create, rename, and delete albums.
- Creation: POST /albums { name }
- Rename: PATCH /albums/:id { name }
- Delete: DELETE /albums/:id (soft delete, photos preserved for 30 days)

## Non-Functional Requirements
### NFR-001: Performance
- Album list renders < 500ms with 100 albums
- Photo tiles lazy-load (virtual scrolling)
- Search returns results < 300ms

## Success Criteria
- [ ] User can create an album in under 3 clicks
- [ ] Photo upload completes within 5 seconds for images under 5MB
- [ ] App functions without network connection for browsing (offline-first)

## Edge Cases
- [ ] Album with 0 photos — show "Empty album" placeholder
- [ ] Album with 500+ photos — paginate tiles
- [ ] Concurrent upload to same album
- [ ] Uploading a file that isn't an image — show error
- [ ] Album name with special characters — sanitize but preserve intent
```

### Key Rules for Spec Writing

1. **WHAT, not HOW**: Don't mention React, PostgreSQL, or Docker. That's for `/speckit.plan`.
2. **Mark ALL ambiguities**: Use `[NEEDS CLARIFICATION: specific question]`. Don't guess.
3. **Acceptance criteria must be testable**: "The UI should look good" → BAD. "Album card renders with name, date, and photo count" → GOOD.
4. **Success criteria must be measurable**: "Fast" → BAD. "Renders < 500ms" → GOOD.
5. **Think edge cases**: Empty state, error state, concurrent operations, limits.

---

## 10. Clarify: Resolving Ambiguity (Phase 1.5)

### Why Clarify?

The spec you get from `/speckit.specify` WILL have `[NEEDS CLARIFICATION]` markers. This is by design — the template forces the AI to mark ambiguities instead of guessing. `/speckit.clarify` resolves them systematically.

### How It Works

```
/speckit.clarify Focus on security and performance requirements.
```

The agent:
1. Reads the entire spec.md
2. Finds all `[NEEDS CLARIFICATION]` markers
3. Conducts structured, sequential questioning
4. Asks ONE question at a time (not a wall of 20)
5. Records all answers in a Clarifications section
6. Updates the spec to remove resolved markers

### Example Clarification Session

```
Agent: I found 3 ambiguities. Let's resolve them one at a time.

Question 1/3: The spec mentions "user authentication" but doesn't
specify the method. Options:
  A) Email + password
  B) OAuth (Google, GitHub)
  C) Both
  D) No auth needed (local-only app)

You: A — email + password only for v1

Agent: Recorded. Question 2/3: Photo storage — local filesystem
or cloud? [NEEDS CLARIFICATION: storage backend not specified]

You: Local filesystem for v1. Add cloud option in v2.

Agent: Recorded. Question 3/3: Should deleted photos be recoverable?
[NEEDS CLARIFICATION: soft delete vs permanent delete]

You: Soft delete — 30-day recovery window.

Agent: All ambiguities resolved. Updated spec.md with Clarifications section.
```

### Clarifications Section Output

```markdown
## Clarifications

### Session 2026-06-15
1. **Auth method**: Email + password only. OAuth deferred to v2.
2. **Storage backend**: Local filesystem. Cloud option in v2.
3. **Delete behavior**: Soft delete with 30-day recovery window.
4. **Max albums per user**: 100 (clarified during review).
```

---

## 11. Checklist: Validating Requirements (Phase 1.6)

### What It Does

```
/speckit.checklist
```

Generates a QUALITY checklist (not a TODOs list). Think of it as "unit tests for English." It validates:

- **Completeness**: Every user story has acceptance criteria? Every FR has measurable success?
- **Clarity**: No vague language ("fast," "good," "user-friendly")?
- **Consistency**: No contradictory requirements? (e.g., "no login" + "user-specific data")
- **Edge cases**: Empty states, error states, limits, concurrent operations?
- **NFR coverage**: Performance, security, accessibility, scalability?

### Example Checklist Output

```markdown
## Requirements Quality Checklist

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [ ] Success criteria are measurable — NFR-001 uses "fast" (vague)
- [x] Edge cases identified for all user stories

### User Story Quality
- [x] Every story has acceptance criteria
- [ ] US-003 (Delete Album) missing edge case: what happens to photos?
- [x] Stories are independent and can be implemented in any order

### Non-Functional Requirements
- [x] Performance requirements specified
- [ ] Security: No authentication method specified beyond "login"
- [ ] Accessibility: No WCAG compliance mentioned
- [ ] Offline behavior: Not specified for photo viewing

### Consistency
- [ ] FR-001 says albums "cannot be nested" but US-004 references "sub-albums"
- [x] Terminology consistent across stories
```

### How to Use the Checklist

```
You: Read the review and acceptance checklist, and check off each item
     if the feature spec meets the criteria. Leave it empty if it does not.

Agent: [Reviews spec against checklist, checks off passing items, leaves
        empty items flagged for attention]

You: Address the unchecked items. For the US-004/sub-albums contradiction,
     resolve it — should albums be nestable or not?

Agent: [Fixes spec, updates checklist]
```

---

## 12. Plan: Creating the Implementation Plan (Phase 2)

### What `/speckit.plan` Does

```
/speckit.plan We are going to use React with Vite, TypeScript, and
PostgreSQL via Prisma. The frontend should use Tailwind CSS.
Images are stored locally in the /uploads directory.
```

This is WHERE you specify the tech stack. Everything before this was WHAT.

### Generated Artifacts

| File | What It Contains |
|---|---|
| `plan.md` | Implementation plan with phases, pre-implementation gates, file creation order, developer notes |
| `research.md` | Technology comparisons (e.g., "Why Vite over CRA?"), version pinning, benchmark results |
| `data-model.md` | Entity relationship diagrams, table schemas, column types, indexes, migrations |
| `contracts/api-spec.json` | OpenAPI 3.0 specification for REST endpoints |
| `contracts/signalr-spec.md` | WebSocket/real-time event specifications (if applicable) |
| `quickstart.md` | How to set up dev environment, key validation scenarios, smoke tests |

### Plan Structure

```markdown
# Implementation Plan: Photo Album Organizer

## Phase -1: Pre-Implementation Gates
### Simplicity Gate (Article VII)
- [x] Using ≤3 projects? (Frontend + Backend = 2)
- [x] No future-proofing? (Cloud storage deferred to v2)
- [x] No speculative features? (Only specified features)

### Library-First Gate (Article I)
- [x] Album CRUD isolated as library? (src/lib/albums/)
- [x] CLI interface exposed? (Album CLI: create, list, delete)

## Phase 0: Project Setup
1. Initialize Vite React TypeScript project
2. Configure Tailwind CSS
3. Set up Prisma with SQLite
4. Configure ESLint + Prettier per Article IV

## Phase 1: Album Management (User Story 1)
### File Creation Order:
1. Create contracts/api-spec.json (Album endpoints)
2. Write contract tests (validate against spec)
3. Write integration tests for album creation
4. Write unit tests for Album model
5. Create Prisma schema (Album table)
6. Implement Album model (src/lib/albums/model.ts)
7. Implement Album CLI (src/lib/albums/cli.ts)
8. Implement Album API routes
9. Run tests → all pass

## Phase 2: Photo Management (User Story 2)
...

## Complexity Tracking
(None — all gates passed)
```

### Why the Plan Matters

Without a plan, the AI codes from a prompt. It guesses. It adds things you didn't ask for. With a plan:
- Every decision is documented with rationale
- Constitutional gates catch over-engineering
- File creation order enforces TDD
- You can audit BEFORE any code is written
- The plan is reviewable — share it, discuss it, change it

### Auditing the Plan

```
You: Now I want you to audit the implementation plan. Read through it
     as a critic. Are there missing pieces? Over-engineered components?
     Does every technical decision trace back to a spec requirement?

Agent: [Reviews plan critically]
       - Phase 2 includes a Redis caching layer that isn't in the spec. Remove.
       - The data model doesn't handle album reordering. Add migration.
       - The quickstart.md assumes Docker. Add non-Docker setup alternative.
```

---

## 13. Tasks: Breaking Down into Executable Steps (Phase 3)

### What `/speckit.tasks` Does

```
/speckit.tasks
```

Reads `plan.md` (required) and optionally `data-model.md`, `contracts/`, `research.md`. Converts the plan into a granular, ordered task list.

### Task Structure

```markdown
# Tasks: Photo Album Organizer

## Phase 1: Album Management (US-001, US-002)
### Dependency: None (starts here)

- [ ] T001 [P] Create Prisma schema for Album model (src/lib/albums/schema.prisma)
- [ ] T002 [P] Write contract tests for Album API (tests/contracts/albums.test.ts)
- [ ] T003 [P] Write unit tests for AlbumService (tests/unit/album-service.test.ts)
- [ ] T004 Create AlbumService with CRUD operations (src/lib/albums/service.ts)
- [ ] T005 Create Album CLI interface (src/lib/albums/cli.ts)
- [ ] T006 Create Album API routes (src/routes/albums.ts)
- [ ] T007 Integration test: Create album → view in list → rename → delete
- [ ] T008 Create Album UI components (AlbumList, AlbumCard, AlbumForm)

**Checkpoint**: Albums can be created, renamed, deleted via API and UI

## Phase 2: Photo Management (US-003, US-004)
### Dependency: Phase 1 complete

- [ ] T009 [P] Write contract tests for Photo API (tests/contracts/photos.test.ts)
- [ ] T010 [P] Write unit tests for PhotoService (tests/unit/photo-service.test.ts)
- [ ] T011 [P] Create file upload middleware (src/middleware/upload.ts)
- [ ] T012 Create Prisma schema for Photo model
- [ ] T013 Create PhotoService (src/lib/photos/service.ts)
...
```

### Key Features of Tasks

| Feature | What It Means |
|---|---|
| `[P]` marker | Task can run in parallel with other `[P]` tasks in the same phase |
| **Ordered by dependency** | T001 before T004. Dependencies are explicit |
| **TDD ordering** | Tests listed BEFORE implementation that makes them pass |
| **Checkpoints** | Validation gate after each user story phase |
| **File paths** | Every task specifies WHERE to create/modify files |
| **Organized by user story** | Each story = one phase. Phases can be delivered incrementally |

### After Tasks: Optionally Convert to GitHub Issues

```
/speckit.taskstoissues
```

Creates one GitHub Issue per task, with dependencies linked. Useful for team coordination and tracking.

---

## 14. Analyze: Cross-Artifact Consistency (Phase 3.5)

### What `/speckit.analyze` Does

```
/speckit.analyze
```

This is the LAST quality gate before implementation. It answers: "Do spec, plan, and tasks actually agree with each other?"

### What It Checks

1. **Coverage**: Does every spec requirement have at least one task?
2. **Orphaned tasks**: Any tasks without a corresponding spec requirement? (scope creep!)
3. **Consistency**: Does the plan's tech stack match the tasks' file paths?
4. **Constitutional compliance**: Are all Phase -1 gates resolved?
5. **Dependency integrity**: Are task dependencies valid (no circular refs)?

### Example Analysis Output

```
Cross-Artifact Analysis Report
==============================

✅ Coverage:
   All 12 functional requirements have corresponding tasks.

⚠️ Gaps Found:
   FR-008 (Photo search) has no tasks in Phase 3.
   → Add search tasks or explicitly defer to v2.

✅ Orphaned Tasks:
   No orphaned tasks found.

❌ Constitutional Violation:
   Plan Phase 3 introduces 4th project (notification-service).
   Article VII limits: 3 projects.
   → Merge into existing backend OR document justification.

✅ Dependency Integrity:
   All task dependencies valid. No circular references.

⚠️ Terminology Drift:
   Spec uses "album" consistently. Tasks use "collection" in T015-T018.
   → Standardize to "album."
```

### Why Analyze BEFORE Implementing

Catching gaps here costs minutes. Catching them during implementation costs hours. Catching them in production... don't.

---

## 15. Implement: Code Generation (Phase 4)

### What `/speckit.implement` Does

```
/speckit.implement
```

1. Validates prerequisites (constitution, spec, plan, tasks all present)
2. Parses `tasks.md`
3. Executes tasks sequentially within each phase
4. Runs `[P]` tasks in parallel where possible
5. Follows TDD ordering: tests → fail → implementation → pass
6. Reports progress and handles errors

### Implementation Flow

```
Phase 1: Album Management
  ├── T001 [P] Create Prisma schema        ─┐
  ├── T002 [P] Write contract tests         ├─ PARALLEL (no dependencies)
  ├── T003 [P] Write unit tests            ─┘
  ├── T004 Create AlbumService              ← waits for T001
  ├── T005 Create Album CLI                 ← waits for T004
  ├── T006 Create Album API routes          ← waits for T004
  ├── T007 Integration test                 ← waits for T004-T006
  ├── T008 Create Album UI components       ← waits for T006
  └── CHECKPOINT: Albums CRUD complete ✓

Phase 2: Photo Management
  ...
```

### Error Handling

If a task fails:
- Non-parallel tasks: Implementation pauses, error is reported
- Parallel tasks: Other parallel tasks continue; failed task is flagged
- You can fix the issue and resume

### Post-Implementation

```
You: Test the application. Are there any browser console errors
     or runtime issues?

Agent: [Runs app, checks console]
       No console errors. Photo upload works but the tile preview
       doesn't refresh after upload. Adding auto-refresh...

You: Good. Update the plan and tasks to reflect this fix.
```

---

## 16. Greenfield Projects (0→1) — Complete Walkthrough

Greenfield = new project, no existing code.

### Step-by-Step

#### 1. Create Project

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init photo-albums --integration claude
cd photo-albums
```

#### 2. Constitution

```
/speckit.constitution Photo Albums is a "User-First" application.
All features must be usable without documentation. We follow TDD
strictly (Article III). We use React + TypeScript + Tailwind.
Maximum 3 top-level directories. No premature optimization.
All UI must pass WCAG 2.1 AA accessibility standards.
```

#### 3. Specify

```
/speckit.specify Build a photo album organizer. Users can create albums,
add photos, drag-and-drop to reorder, and view photos in a tile grid.
Albums are flat (no nesting). Photos support JPEG, PNG, WebP up to 10MB.
No login required — single-user local app. Photos stored locally.
Albums grouped by creation date on the main page.
```

Creates: branch `001-photo-album-organizer`, `specs/001-photo-album-organizer/spec.md`

#### 4. Clarify

```
/speckit.clarify
```

Resolves ambiguities the agent marked (e.g., "How should we handle duplicate photos?" "What's the max albums limit?").

#### 5. Checklist

```
/speckit.checklist
```

Validates requirements quality. Fix issues found.

#### 6. Plan

```
/speckit.plan We use Vite + React + TypeScript. Tailwind CSS for styling.
SQLite via better-sqlite3 for metadata. Photos stored in /photos directory.
Vitest for testing. Playwright for E2E. No API server — everything runs
in-browser with Node.js filesystem access via Tauri (desktop app).
```

Creates: `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

#### 7. Audit Plan

```
You: Audit the plan. What's over-engineered? What's missing?

Agent: The plan includes a WebSocket server for "real-time" updates,
       but this is a single-user desktop app. Removing.
       Missing: Photo thumbnail generation. Adding.
       Research.md references Electron but we chose Tauri. Updating.
```

#### 8. Tasks

```
/speckit.tasks
```

Creates: `tasks.md` with ordered, parallel-marked tasks.

#### 9. Analyze

```
/speckit.analyze
```

Checks consistency. Fix gaps.

#### 10. Implement

```
/speckit.implement
```

Code is generated. TDD is followed.

#### 11. Test & Iterate

```
You: Run the app and tell me what runtime errors you find.

Agent: [Tests app] The album creation form doesn't clear after submit.
       The drag-and-drop reorder doesn't persist on page refresh.
       Fixing...

You: Good. Update the spec and plan to reflect what actually shipped
     vs what was deferred.
```

---

## 17. Brownfield Projects (1→n) — Complete Walkthrough

Brownfield = existing codebase with production traffic.

### The Brownfield Difference

Spec Kit works in brownfield because:

1. **`specify init .`** doesn't touch your existing code — it only adds `.specify/`
2. Each feature is on its own branch — existing code on `main` is safe
3. The constitution can reference your existing patterns
4. The plan's research phase reads your existing codebase to understand conventions

### Step-by-Step

#### 1. Initialize on Existing Repo

```bash
cd my-existing-app
uvx --from git+https://github.com/github/spec-kit.git specify init . --force --integration claude
# --force: allow initialization in non-empty directory
```

Your existing code is untouched. Only `.specify/` and `.claude/commands/` are added.

#### 2. Constitution: Match Your Existing Patterns

```
/speckit.constitution This project already uses Express + PostgreSQL +
EJS templates. All new features must follow existing patterns:
- RESTful API at /api/v1/
- PostgreSQL via pg (raw SQL, no ORM)
- EJS server-side rendering (no SPA)
- Jest for testing
- Error format: { error: string, details?: any }
- Middleware pattern: auth → validate → handler → respond
```

This is CRITICAL. Without this, the agent might propose React SPA for a server-rendered app.

#### 3. Explore Existing Code

```
You: Before we add the feature, read the existing codebase structure.
     Understand: directory layout, API patterns, database schema,
     testing conventions, error handling.

Agent: [Reads existing code]
       I see the app follows:
       - /src/routes/ — route handlers
       - /src/models/ — database queries (raw SQL)
       - /src/middleware/ — auth, validation, error handling
       - /tests/ mirroring /src/ structure
       - PostgreSQL schema in /migrations/
```

#### 4. Specify the New Feature

```
/speckit.specify Add file upload support to the existing task manager.
Users should be able to attach files to tasks. Files are stored in S3
(reuse existing AWS config). Max 25MB per file. Max 5 files per task.
Supported: PDF, DOCX, XLSX, PNG, JPEG, TXT. New API: POST /api/v1/tasks/:id/attachments,
GET /api/v1/tasks/:id/attachments, DELETE /api/v1/tasks/:id/attachments/:fileId.
Must follow existing error response format and middleware pattern.
```

#### 5. Clarify + Checklist + Plan

```
/speckit.clarify Focus on how file uploads interact with existing task permissions
/speckit.checklist
/speckit.plan Reuse existing S3 client from /src/lib/s3.js. Follow existing
route pattern. Use existing auth middleware. Add new migration for
attachments table (follow existing migration naming convention).
```

#### 6. Tasks + Analyze + Implement

```
/speckit.tasks
/speckit.analyze  ← CRITICAL in brownfield: ensures new code fits existing patterns
/speckit.implement
```

### Brownfield: Deprecating Old Features

When adding a feature that replaces existing functionality:

```
/speckit.specify Replace task assignment with team-based assignment.
Teams are groups of users managed by team leads.

DEPRECATED:
- POST /api/v1/tasks/:id/assign (replaced by team assignment)
- tasks.assigned_to column (replaced by tasks.team_id FK)
- GET /api/v1/tasks?assignedTo=:id (replaced by ?team=:id)

MIGRATION PATH:
1. Add teams table + tasks.team_id (nullable)
2. Add team-based assignment API
3. Mark old endpoints with Deprecation: true header
4. Backfill existing tasks into "Default" team
5. Make tasks.team_id NOT NULL
6. Remove old endpoints in v3 (2027-01-01)

SUNSET SCHEDULE:
- v2: Old endpoints return 301 + Deprecation header
- v3: Old endpoints removed
```

The plan handles the migration:
```markdown
### Phase 3: Deprecation (v2)
- T020 Add deprecation headers to old assign endpoints
- T021 Add deprecation warnings to old assign UI
- T022 Backfill script: assign all existing users to "Default" team
- T023 Documentation: migration guide for API consumers

### Phase 4: Sunset (v3 — future branch)
- T024 Remove POST /api/v1/tasks/:id/assign
- T025 Drop tasks.assigned_to column
- T026 Remove deprecation headers
```

---

## 18. Practical Example 1: Build a Photo Album App (Greenfield)

Let's build **PixVault** — a photo album organizer — from zero.

### 1. Init

```bash
uvx --from git+https://github.com/github/spec-kit.git specify init pixvault --integration claude
cd pixvault
```

### 2. Constitution

```
/speckit.constitution PixVault principles:
- Library-First: every feature is a standalone library with CLI
- TDD: no implementation without failing tests first
- Simplicity: max 3 top-level directories. No frameworks we don't need.
- CLI: every library must have a command-line interface
- Real testing: use real SQLite, not mocks
- Accessibility: all UI passes WCAG AA
- No premature optimization: make it work, then make it fast
```

### 3. Specify

```
/speckit.specify PixVault is a desktop photo album organizer.
Users create albums (flat, no nesting). Albums show on main page grouped
by month. Drag-and-drop to reorder albums. Inside an album: photo tiles
(3 columns, responsive). Click photo to view full-size. Upload via
drag-and-drop or button. Supported: JPEG, PNG, WebP, max 15MB.
Photos stored locally (no cloud). Album metadata in SQLite.
No login (single-user). Search photos by filename. Delete album
moves photos to Trash (30-day recovery).
```

Agent creates branch `001-pixvault`, writes `spec.md` with 8 user stories, 15 FRs, 5 NFRs.

### 4. Clarify

```
/speckit.clarify

Agent: Question 1/8: Should Trash be user-visible or system-only?
You: User-visible. A "Trash" section in the sidebar.

Agent: Question 2/8: What happens to album order after closing/reopening?
You: Persist order. Save order as position integer in SQLite.

... resolves all 8 ambiguities
```

### 5. Checklist

```
/speckit.checklist

Output: 3 issues found
- Missing: "Max albums limit" not specified → Add: 500 albums max
- Missing: "What happens with corrupted image files" → Skip with error toast
- Vague: "Responsive" → Specify breakpoints: 3 cols desktop, 2 tablet, 1 mobile
```

### 6. Plan

```
/speckit.plan Use Electron + React + TypeScript. Vite for bundling.
SQLite via better-sqlite3. Tailwind CSS. Photos in OS user data directory.
IPC for main↔renderer communication. Vitest + Playwright. electron-builder
for packaging. Follow constitutional library-first pattern:
each feature (albums, photos, search, trash) is a standalone library
with its own CLI.
```

Agent generates `plan.md`, `research.md` (compares Electron vs Tauri, explains Electron choice for filesystem access), `data-model.md` (5 tables), `contracts/ipc-events.md` (IPC events instead of REST since it's desktop).

### 7. Audit

```
You: Read the plan as a critic. Flag over-engineering.

Agent: Found: plan includes a thumbnail generation service as a separate
       process. Over-engineered for v1. Thumbnails can be generated
       on-import synchronously. Also: the IPC contract defines 27 events
       but the spec has only 8 user stories. Reducing to 12 events.
```

### 8. Tasks

```
/speckit.tasks

Output: tasks.md with 42 tasks across 8 phases.
Phase 1 (Albums): T001-T008. 3 parallel [P] tasks.
Phase 2 (Photos): T009-T018. 5 parallel [P] tasks.
...
Phase 8 (Trash): T038-T042. 1 parallel [P] task.
```

### 9. Analyze

```
/speckit.analyze

✅ All spec requirements covered
⚠️ Contract IPC-EVENT-014 (album-share) has no corresponding task
   → Removed: sharing deferred to v2
✅ Constitutional compliance: all gates passing
✅ Dependency integrity: no circular references
```

### 10. Implement

```
/speckit.implement

Phase 1/8: Album Management [T001-T008]
  T001 [P] SQLite schema ✓
  T002 [P] Contract tests ✓
  T003 [P] Unit tests ✓
  T004 AlbumService ✓
  ... 
  CHECKPOINT: Albums CRUD working ✓

Phase 2/8: Photo Management [T009-T018]
  ...
```

### Result After 8 Phases

```
pixvault/
├── src/
│   ├── lib/
│   │   ├── albums/       # Library per Article I
│   │   │   ├── cli.ts
│   │   │   ├── service.ts
│   │   │   └── service.test.ts
│   │   ├── photos/
│   │   ├── search/
│   │   └── trash/
│   ├── main/             # Electron main process
│   └── renderer/         # React UI
├── tests/
├── specs/001-pixvault/   # Full spec, plan, tasks (source of truth)
└── .specify/memory/constitution.md
```

---

## 19. Practical Example 2: Add Features + Deprecate (Brownfield)

PixVault has been live for 6 months. Now we need to:

1. **ADD**: Cloud backup to Google Drive
2. **ADD**: Shared albums (read-only links)
3. **DEPRECATE**: Local Trash (replace with cloud trash)

### 1. Initialize on Existing Repo

```bash
cd pixvault
# Already has .specify/ from original init
# No need to re-init
```

### 2. Explore Current State

```
You: Read the plan, spec, and data-model from the original implementation.
     Then read the actual code in src/lib/. Identify any drift between
     the spec and what actually shipped.

Agent: Drift found:
       - Original plan specified Electron. We actually shipped Tauri (migrated in v1.1).
       - The Trash library has a purge-expired.ts that isn't in the original spec.
       - Photo search uses a different approach (FUSE.js) than planned (SQL LIKE).
       
       Updating spec and plan to reflect actual state before adding features.
```

### 3. Specify v2 Features

```
/speckit.specify PixVault v2 adds:
1. Cloud backup: user can connect Google Drive. Albums auto-sync on change.
   Manual "Backup Now" button. Conflict resolution: newer wins.
2. Shared albums: generate read-only share link. Viewer sees photos but
   can't modify. Link expires after configurable duration (default 7 days).
3. DEPRECATE local Trash: replaced by cloud trash (30 days in cloud).
   Local Trash removed. Existing trash items migrated to cloud on upgrade.

V2 SPECIFIC NOTES:
- Must reuse existing Tauri patterns (no Electron regression)
- Must follow existing IPC event naming: domain:action (e.g., albums:create)
- Must use existing error format: { error: string, code: string, details?: any }
- Google Drive OAuth: use existing auth flow pattern from v1 (system browser)

SUNSET: Local Trash
- v2.0: Local Trash hidden, cloud trash shown instead
- v2.1: Local trash data migrated to cloud
- v3.0: Local trash code removed
```

Agent creates branch `002-pixvault-v2`, writes spec.

### 4. Plan

```
/speckit.plan Cloud backup uses Google Drive API v3 via googleapis npm.
OAuth via Tauri's shell.open for auth URL. Token stored in OS keychain
(use existing keychain module). Sync uses FileObserver from Tauri.
Shared albums generate UUID links, stored in new shared_links table.
Validation: link UUID + expiry check per request.
```

### 5. Deprecation Handling in Tasks

```markdown
### Phase 4: Trash Migration (Deprecation)
- [ ] T025 [P] Add cloud-trash library (follow library-first)
- [ ] T026 [P] Add migration script: export local trash → cloud
- [ ] T027 Hide local Trash UI, show cloud trash
- [ ] T028 Add deprecation notice to local Trash IPC events
- [ ] T029 Update spec: mark local Trash as DEPRECATED with sunset date
- [ ] T030 Migration guide for existing users

CHECKPOINT: Users see cloud trash. Local trash hidden but not deleted.
```

### 6. After v2 Ships

```bash
# Archive the v2 spec as delivered
git tag v2.0.0

# The spec/plan/tasks in specs/002-pixvault-v2/ are the permanent record
# of what was built, why, and how. No drift between docs and code.
```

---

## 20. Template-Driven Quality: How Constraints = Better Code

Spec Kit's templates are NOT just empty scaffolds. They are **sophisticated prompt engineering** that constraints AI behavior toward quality.

### Constraint 1: Preventing Premature Implementation

The spec template explicitly BLOCKS tech thinking:

```markdown
✅ Focus on WHAT users need and WHY
❌ Avoid HOW to implement (no tech stack, APIs, code structure)
```

Without this, AI naturally jumps to "use React with Redux" instead of "users need real-time updates."

### Constraint 2: Forced Uncertainty Markers

```markdown
1. Mark ALL ambiguities: Use [NEEDS CLARIFICATION: specific question]
2. Don't guess: If the prompt doesn't specify something, mark it
```

Without this, AI makes plausible but wrong assumptions. "Login" becomes "email+password" when you meant OAuth.

### Constraint 3: Checklists as "Unit Tests for English"

```markdown
### Requirement Completeness
- [ ] No [NEEDS CLARIFICATION] markers remain
- [ ] Requirements are testable and unambiguous
- [ ] Success criteria are measurable
```

These force the AI to self-review systematically, catching gaps before they become code.

### Constraint 4: Constitutional Phase Gates

```markdown
### Phase -1: Pre-Implementation Gates
#### Simplicity Gate (Article VII)
- [ ] Using ≤3 projects?
- [ ] No future-proofing?
```

Gates force the AI to explicitly justify complexity. If a gate fails, it must document why in "Complexity Tracking."

### Constraint 5: Hierarchical Detail Management

```markdown
IMPORTANT: This plan should remain high-level and readable.
Code samples and detailed algorithms → implementation-details/ files.
```

Prevents plans from becoming unreadable code dumps. Main doc stays navigable.

### Constraint 6: TDD Ordering

```markdown
### File Creation Order
1. Create contracts/ with API specifications
2. Create test files: contract → integration → e2e → unit
3. Create source files to make tests pass
```

This ordering constraint ensures the AI thinks about testability before implementation.

### Constraint 7: No Speculative Features

```markdown
- [ ] No speculative or "might need" features
- [ ] All phases have clear prerequisites and deliverables
```

Stops AI from adding "nice to haves" that add complexity without current value.

### The Compound Effect

These 7 constraints work together:

```
Without constraints:  AI = creative writer
With constraints:     AI = disciplined specification engineer

Result:
  Complete specs     → Checklists ensure nothing is forgotten
  Unambiguous specs  → Forced clarification markers
  Testable specs     → TDD thinking baked in
  Maintainable code  → Gates prevent over-engineering
  Traceable code     → Every implementation traces to a spec requirement
```

---

## 21. Extensions & Presets: Customizing Spec Kit

### The Customization Stack (Priority: Top Wins)

```
1. Project-Local Overrides   ← .specify/templates/overrides/
2. Presets                    ← .specify/presets/templates/
3. Extensions                 ← .specify/extensions/templates/
4. Spec Kit Core              ← .specify/templates/
```

### Extensions: Add NEW Capabilities

Use when you need functionality beyond the core 9 commands.

```bash
# Search:
specify extension search

# Install:
specify extension add <extension-name>

# List installed:
specify extension list
```

**Example extensions (community):**
- **Ralph Loop**: Autonomous implementation — runs `/speckit.implement` in a loop until all tasks done, no human intervention needed between tasks
- **Jira Integration**: Converts tasks to Jira tickets
- **Post-Implementation Review**: Adds a code review phase after implementation
- **V-Model Traceability**: Adds test-to-requirement traceability matrix
- **Project Health**: Diagnostics and metrics on spec coverage

### Presets: Customize EXISTING Workflows

Use when you want to change HOW Spec Kit works, not WHAT it does.

```bash
# Search:
specify preset search

# Install:
specify preset add <preset-name>
```

**What presets can change:**
- Spec template structure (add regulatory traceability sections)
- Terminology (rename "tasks" to "crew assignments" for game dev)
- Phase ordering (add security review gate)
- Checklist content (add domain-specific validation)
- Language (localize entire workflow — pirate-speak demo shows full terminology override)

### Preset Stacking

```
specify preset add compliance   # 1st: adds regulatory traceability
specify preset add agile        # 2nd: renames phases to sprints
specify preset add dark-mode    # 3rd: adds accessibility checklist items
```

Higher priority presets can override lower.

### When to Use Which

| Goal | Use |
|---|---|
| Add a brand-new command or workflow | Extension |
| Customize the format of specs, plans, or tasks | Preset |
| Integrate an external tool or service | Extension |
| Enforce organizational or regulatory standards | Preset |
| One-off change for a single project | Project-local override |
| Ship reusable domain-specific templates | Either (presets for overrides, extensions for new commands) |

---

## 22. CLI Reference

### Core Commands

```bash
# Initialize
specify init <project-name>                   # New project
specify init .                                # Current directory
specify init . --force                        # Non-empty directory
specify init <name> --integration claude      # Choose agent
specify init <name> --integration codex --integration-options="--skills"  # Skills mode
specify init <name> --ignore-agent-tools      # Skip agent detection
specify init <name> --no-git                  # Don't init git
specify init <name> --script ps               # Force PowerShell scripts

# Self-management
specify --version
specify self check                            # Check for updates
specify self upgrade                          # Upgrade to latest
specify self upgrade --tag v1.2.3             # Pin version
specify self upgrade --dry-run                # Preview

# Integration management
specify integration list                      # List available integrations
specify integration add <name>               # Add integration
specify integration remove <name>            # Remove integration

# Extension management
specify extension search [query]             # Search extensions
specify extension add <name>                 # Install extension
specify extension list                       # List installed
specify extension remove <name>              # Remove extension
specify extension info <name>                # Extension details

# Preset management
specify preset search [query]                # Search presets
specify preset add <name>                    # Install preset
specify preset list                          # List installed
specify preset remove <name>                 # Remove preset
specify preset info <name>                   # Preset details
```

### Agent Integration Flags

| Flag | Agent |
|---|---|
| `--integration claude` | Claude Code |
| `--integration copilot` | GitHub Copilot |
| `--integration cursor-agent` | Cursor |
| `--integration codex` | Codex CLI |
| `--integration gemini` | Gemini CLI |
| `--integration windsurf` | Windsurf |
| `--integration hermes` | Hermes Agent |
| `--integration kiro-cli` | Kiro CLI |
| `--integration opencode` | OpenCode |
| `--integration qoder` | Qoder CLI |
| `--integration bob` | IBM Bob |
| `--integration junie` | JetBrains Junie |
| ... and 20+ more |

---

## 23. Supported AI Agents

Spec Kit supports **30+ AI coding agents**:

| Agent | Mode | Notes |
|---|---|---|
| **Claude Code** | Slash commands | `.claude/commands/` — recommended |
| **GitHub Copilot** | Slash commands | VS Code / CLI |
| **Cursor** | Slash commands | `.cursor/commands/` |
| **Codex CLI** | Skills / Slash | `.agents/skills/` for skills mode |
| **Gemini CLI** | Slash commands | Google's agent |
| **Windsurf** | Slash commands | AI-first IDE |
| **Hermes Agent** | Skills | `~/.hermes/skills/` — global install |
| **Kiro CLI** | Slash commands | AWS's agent |
| **OpenCode** | Slash commands | Terminal agent |
| **Amp** | Slash commands | |
| **Cline** | Slash commands | IDE agent |
| **CodeBuddy** | Slash commands | |
| **Devin** | Skills | `.devin/skills/` |
| **Forge** | Slash commands | |
| **Goose** | YAML recipes | `.goose/recipes/` |
| **IBM Bob** | Slash commands | IDE agent |
| **iFlow** | Slash commands | |
| **Junie** | Slash commands | JetBrains |
| **Kilo Code** | Slash commands | |
| **Kimi Code** | Skills | |
| **Lingma** | Skills | Alibaba |
| **Mistral Vibe** | Slash commands | |
| **Pi** | Slash commands | |
| **Qoder** | Slash commands | |
| **Tabnine** | Slash commands | |
| ... and more | | |

---

## 24. Spec Kit vs Alternatives

| Feature | Spec Kit | OpenSpec | BMAD Method |
|---|---|---|---|
| **Approach** | Spec-first with constitution | Spec-first with change deltas | Multi-agent agile team |
| **Commands** | 9 slash commands | 3+ slash commands | 27+ skill commands |
| **Structure** | Spec → Plan → Tasks → Implement | Propose → Apply → Archive | Analysis → Planning → Solutioning → Impl |
| **Constitution** | 9 Articles, immutable, Phase -1 gates | None | None (customization via TOML) |
| **Quality Gates** | clarify, checklist, analyze | validate (--strict) | code-review, check-implementation-readiness |
| **Brownfield** | Specify on existing repo; plan researches codebase | /opsx:explore; delta specs against existing | project-context.md; investigate workflow |
| **TDD** | Built-in (Article III: MUST write tests first) | Optional (depends on agent) | Optional (depends on agent) |
| **Customization** | Extensions + Presets system | Custom schemas + OPSX | customize.toml overlay model |
| **Agents** | Works with 30+ AI coding agents | Works with 20+ AI assistants | 6 named AI agents with personas |
| **Branching** | Per-feature branches (auto-created) | Per-change folders (not branches) | No auto-branching |
| **CI/Issues** | taskstoissues → GitHub Issues | None built-in | None built-in |
| **Installation** | `uvx/uv tool install specify-cli` | `npm install -g @fission-ai/openspec` | `npx bmad-method install` |
| **Language** | Python (CLI), Markdown+Shell (templates) | Node.js (CLI), Markdown | Node.js (installer), Markdown |
| **License** | MIT | MIT | MIT |
| **GitHub Stars** | 28k+ | 55k+ | 49k+ |

### When to Choose Spec Kit

- You want **constitutional enforcement** of TDD, simplicity, library-first
- You want **branch-per-feature** isolation
- You value **template-constrained quality** over free-form AI generation
- You need **analyze** for cross-artifact consistency before code is written
- You want **GitHub Issues integration** (taskstoissues)
- You work with **30+ agent choices** (not locked into one tool)

### When to Choose OpenSpec Instead

- You want **change deltas** (ADDED/MODIFIED/REMOVED diffs)
- You need **lightweight workflow** (3 commands)
- You want **audit trails** for every change
- You prefer **change folders** over per-feature branches

### When to Choose BMAD Instead

- You want **named AI agent personas** with distinct voices
- You need **party mode** for multi-agent collaboration
- You want **scale-adaptive intelligence** (auto-detects project complexity)
- You value **document sharding** for context management

---

## 25. Best Practices

### Workflow Discipline

1. **Always use the production path for production features.** Skipping clarify/checklist/analyze is for quick experiments only. The quality gates catch things AI misses.

2. **Review at every step.** The AI's first output is NOT final. Read it. Question it. "Why did you choose X?" "What's the rationale for Y?" "What alternatives did you consider?"

3. **Constitution first, then features.** Without a constitution, the plan has no constraints. With one, every plan respects the same principles.

4. **Branch per feature.** Let Spec Kit create branches. Don't manually name them. The auto-detection depends on branch naming conventions.

### Spec Quality

5. **Be exhaustively specific.** "Users can create albums" is too vague. "Users can create albums with a name (1-100 chars, required). Albums appear grouped by creation month. Max 500 albums per user. Albums cannot contain other albums (flat structure)."

6. **Acceptance criteria are tests.** Write them so a computer could verify them. "The UI should look good" → bad. "Album card renders with name, creation date, and photo count badge" → good.

7. **Edge cases are mandatory.** What happens with 0 photos? 10,000 photos? An album named with emojis? Concurrent operations?

### Plan Quality

8. **Research is not optional.** Always check `research.md` to verify the right tech versions were chosen. Ask for parallel research on rapidly-changing libraries.

9. **Audit the plan.** Always ask: "Read the plan as a critic. What's over-engineered? What's missing? Are there tasks not traceable to requirements?"

10. **Gate compliance is binary.** If a Phase -1 gate can't be checked, it means the plan isn't ready. All gates must pass OR have justified exceptions.

### Implementation Quality

11. **Don't trust the first implementation.** Test it. Run it. Find runtime errors. Copy browser console errors back to the agent.

12. **Update spec and plan after implementation.** What actually shipped may differ from the original plan. The docs are the permanent record. Keep them truthful.

### Brownfield-Specific

13. **Read the existing codebase FIRST.** Before `/speckit.specify`, have the agent explore your current architecture, patterns, and conventions.

14. **Constitution must match reality.** If your app uses Express + raw SQL, the constitution should say so. Don't let the AI propose React SPA for a server-rendered app.

15. **Deprecate in phases.** Old features should be deprecated first (headers, warnings, docs), migrated second (data), removed third (future version). Each phase is a task.

---

## 26. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| AI adds features you didn't ask for | No constitution or weak spec | Strengthen constitution's simplicity article. Add "no speculative features" to checklist. |
| Plan uses wrong tech stack | Didn't specify stack in `/speckit.plan` | Re-run with explicit tech: "We use Express, PostgreSQL, EJS. No React." |
| Tasks don't cover all requirements | Skipped `/speckit.analyze` | Run `/speckit.analyze` before implementation. Add missing tasks. |
| Implementation breaks existing features | Brownfield: no exploration of existing code | Have agent read existing codebase before implementing. Reference in plan. |
| AI generates tests after code (not TDD) | Constitution Article III not enforced | Check constitution. Ensure Phase -1 TDD gate is checked. |
| Plan is too long/complex to read | Agent dumped code into plan.md | Remind agent: "Keep plan high-level. Code to implementation-details/." |
| `specify init` fails | `uv` not installed, or Python < 3.11 | Install `uv`: `pip install uv`. Upgrade Python to 3.11+. |
| AI gets stuck researching wrong thing | Research too broad | Tell agent: "Identify specific unknowns, then parallel research each one." |
| Spec has too many `[NEEDS CLARIFICATION]` | You were too vague in `/speckit.specify` | Be more specific upfront, or run `/speckit.clarify` to resolve. |
| Lost track of which feature is active | Multiple branches | Check `git branch`. Switch to the feature branch you want to work on. |
| Constitution changes not taking effect | Amended constitution but plan already created | Re-run `/speckit.plan` to re-apply constitutional gates. |
| Extensions/presets not working | Priority collision | Check resolution order: overrides > presets > extensions > core. |

---

## 27. Cheat Sheet

### Quick Start (3 steps)

```bash
# 1. Install
uvx --from git+https://github.com/github/spec-kit.git specify init my-project --integration claude
cd my-project

# 2. Define principles
/speckit.constitution We use TDD, library-first, max 3 projects. All code tested.

# 3. Start building
/speckit.specify <describe what you want to build>
```

### Production Path

```
/speckit.constitution → /speckit.specify → /speckit.clarify → /speckit.checklist
→ /speckit.plan → /speckit.tasks → /speckit.analyze → /speckit.implement
```

### Lean Path

```
/speckit.specify → /speckit.plan → /speckit.tasks → /speckit.implement
```

### All Commands

```
/speckit.constitution    # Define immutable project principles (once)
/speckit.specify         # Create feature spec — WHAT and WHY
/speckit.clarify         # Resolve ambiguities (before plan)
/speckit.checklist       # Validate requirements quality (before plan)
/speckit.plan            # Create technical plan — HOW (tech stack)
/speckit.tasks           # Generate executable task list
/speckit.analyze         # Cross-artifact consistency (before implement)
/speckit.implement       # Execute: code generation with TDD
/speckit.taskstoissues   # Convert tasks to GitHub Issues
```

### Per-Feature Artifacts

```
specs/001-feature-name/
├── spec.md           ← WHAT: user stories, FRs, NFRs, acceptance criteria
├── plan.md           ← HOW: architecture, phases, file creation order
├── research.md       ← Technology comparisons, rationale
├── data-model.md     ← Database schema, entities
├── quickstart.md     ← Validation scenarios, setup
├── tasks.md          ← Executable, ordered task list
└── contracts/        ← API specs, IPC events
```

### Directory Map

```
.specify/                       ← Spec Kit internals (extensions/presets safe)
  ├── memory/constitution.md    ← YOUR principles (edit via /speckit.constitution)
  ├── scripts/                  ← Automation (don't edit)
  └── templates/                ← Templates (override via presets/extensions)

specs/<feature>/                ← YOUR artifacts (edit freely, commit to git)
```

### The Nine Constitutional Articles

```
I.   Library-First         → Every feature is a standalone library
II.  CLI Interface         → Everything inspectable via command line
III. Test-First (TDD)      → NON-NEGOTIABLE: tests before code
IV.  Code Quality          → Linting, formatting, complexity limits
V.   Testing Standards     → Coverage, test types, data policies
VI.  UX Consistency        → Design system, accessibility
VII. Simplicity            → ≤3 projects, no future-proofing
VIII. Anti-Abstraction     → Use framework directly, don't wrap
IX.  Integration-First     → Test in real environments, not mocks
```

### Spec Kit in One Sentence

> Install → Constitution → Specify WHAT → Clarify → Plan HOW → Tasks → Analyze → Implement → Code that traces to requirements, respects immutable principles, and survives context loss.

---

## Sources

- [Spec Kit GitHub](https://github.com/github/spec-kit) — 28k+ stars, MIT license
- [Spec Kit Documentation](https://github.github.io/spec-kit/)
- [Spec Kit Quickstart](https://github.github.io/spec-kit/quickstart.html)
- [SDD Methodology (spec-driven.md)](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [Spec Kit Community Walkthroughs](https://github.github.io/spec-kit/community/walkthroughs.html)
- [Greenfield Spring Boot + React Demo](https://github.com/mnriem/spec-kit-spring-react-demo)
- [Brownfield ASP.NET CMS Extension Demo](https://github.com/mnriem/spec-kit-aspnet-brownfield-demo)
- [Brownfield Java Runtime Extension Demo](https://github.com/mnriem/spec-kit-java-brownfield-demo)
- [Brownfield Go + React Dashboard Demo](https://github.com/mnriem/spec-kit-go-brownfield-demo)
- [Pirate-Speak Preset Demo](https://github.com/mnriem/spec-kit-pirate-speak-preset-demo)
- [Spec Kit Extensions (hiddedesmet.com)](https://hiddedesmet.com/speckit-extensions)
- [Deep Dive into SpecKit (LPains)](https://blog.lpains.net/posts/2025-12-07-deep-dive-into-speckit)
- [GitHub Spec Kit Tutorial Series (CodeStandUp)](https://codestandup.com/posts/2025/github-spec-kit-tutorial-plan-tasks-commands)
- [Spec-Driven Development Guide (Fundesk)](https://www.fundesk.io/spec-driven-development-github-spec-kit-guide)
- [speckit.org](https://speckit.org/)

---

*Tutorial created: June 15, 2026. Spec Kit is actively developed — check https://github.com/github/spec-kit for the latest.*
