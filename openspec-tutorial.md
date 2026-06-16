# OpenSpec Tutorial: The Complete Guide to Spec-Driven Development

> **Authoritative references:**
> - GitHub: https://github.com/Fission-AI/OpenSpec
> - Docs: https://openspec.dev/ | https://thedocs.io/openspec
> - npm: https://www.npmjs.com/package/@fission-ai/openspec
> - Written: June 2026 | Tested against: OpenSpec v1.2+ (OPSX workflow)

---

## Table of Contents

1. [What is OpenSpec?](#1-what-is-openspec)
2. [Why OpenSpec Matters](#2-why-openspec-matters)
3. [Installation & Setup](#3-installation--setup)
4. [Directory Structure — Every File Explained](#4-directory-structure--every-file-explained)
5. [Skills (Slash Commands) — Complete Reference](#5-skills-slash-commands--complete-reference)
6. [Core Workflow: The Four-Stage Lifecycle](#6-core-workflow-the-four-stage-lifecycle)
7. [Greenfield Projects (0→1) — Complete Walkthrough](#7-greenfield-projects-01--complete-walkthrough)
8. [Brownfield Projects (1→n) — Complete Walkthrough](#8-brownfield-projects-1n--complete-walkthrough)
9. [Practical Example 1: Build a Task API (Greenfield)](#9-practical-example-1-build-a-task-api-greenfield)
10. [Practical Example 2: Evolve the Task API (Brownfield — Add Features + Deprecate Old)](#10-practical-example-2-evolve-the-task-api-brownfield--add-features--deprecate-old)
11. [Spec Delta Format — Deep Dive](#11-spec-delta-format--deep-dive)
12. [Project Configuration (config.yaml)](#12-project-configuration-configyaml)
13. [Custom Schemas & OPSX Customization](#13-custom-schemas--opsx-customization)
14. [CLI Reference](#14-cli-reference)
15. [Best Practices](#15-best-practices)
16. [Troubleshooting](#16-troubleshooting)
17. [OpenSpec vs Alternatives](#17-openspec-vs-alternatives)
18. [Cheat Sheet](#18-cheat-sheet)

---

## 1. What is OpenSpec?

**OpenSpec** is an open-source (MIT), tool-agnostic framework for **Spec-Driven Development (SDD)**. Created by Fission AI (Y Combinator), it sits between you and your AI coding assistant (Claude Code, Cursor, Copilot, Windsurf, Codex, and 20+ others) and ensures that *intent is agreed upon before code is written*.

### The Core Thesis

> **"Generating code is now cheap. Correctness is still expensive."**

OpenSpec solves the problem of AI coding assistants producing unpredictable, hallucinated, or unmaintainable code by enforcing a lightweight specification layer. You define *what* the system should do in structured Markdown — the AI implements *how*.

### OpenSpec's Philosophy

```
fluid not rigid     → No phase gates. Edit any artifact, anytime.
iterative not waterfall → Build in small, reviewable deltas.
easy not complex    → Markdown files in your repo. No databases. No SaaS.
built for brownfield not just greenfield → Designed for existing codebases.
scalable            → From solo devs to enterprise teams.
```

### Key Differentiators

| Concept | What It Means |
|---|---|
| **Specs as Source of Truth** | `openspec/specs/` contains the *current* system behavior, organized by capability. Always up-to-date via archive flow. |
| **Changes as Proposals** | `openspec/changes/` isolates proposed modifications. Each change is a self-contained, reviewable folder. |
| **Spec Deltas** | Changes describe what's ADDED, MODIFIED, or REMOVED relative to current specs — not a full rewrite. |
| **Auditable History** | Archived changes preserve *why* every modification was made. Full lineage of every spec. |
| **No Lock-In** | Works with any AI coding tool. Slash commands integrate directly. No API keys. No MCP servers. |

---

## 2. Why OpenSpec Matters

### The Problem: "Vibe Coding" at Scale

AI coding assistants are powerful but chaotic when requirements live only in chat history:

- **Context loss**: AI "forgets" requirements as conversations grow long
- **Hallucinations**: Vague prompts produce plausible but incorrect code
- **Regression**: No way to know what changed and why
- **Review hell**: Reviewers must reverse-engineer intent from code diffs

Research shows that when AI context usage exceeds 40%, performance degrades significantly — previous requirement details are forgotten or tampered with.

### The Solution: Spec-First Development

OpenSpec transforms AI from a black-box code generator into an intelligent collaborator that:

1. **Reads existing specs** to understand the system
2. **Proposes spec changes** before touching code
3. **Implements against approved specs** with bounded scope
4. **Merges deltas** into living documentation on completion

The result: deterministic, reviewable, auditable AI-driven development.

---

## 3. Installation & Setup

### Prerequisites

- **Node.js >= 20.19.0** (check with `node --version`)
- An AI coding assistant (Claude Code, Cursor, Copilot, Windsurf, etc.)

### Install

```bash
# Global install (recommended)
npm install -g @fission-ai/openspec@latest

# Or use without installing
npx @fission-ai/openspec@latest init

# Also works with: pnpm, yarn, bun, nix
```

### Initialize a Project

```bash
cd your-project
openspec init
```

**What `openspec init` does:**
1. Prompts you to select your AI tool (Claude Code, Cursor, Copilot, Windsurf, etc.)
2. Creates the `openspec/` directory structure
3. Generates `AGENTS.md` with AI instructions
4. Creates `project.md` for project-wide context
5. Sets up slash commands for your chosen AI tool
6. Generates skill files in `.claude/skills/` (or equivalent)

### Verify

```bash
openspec list              # list all active changes
openspec list --specs      # list all specs
openspec validate --all    # validate everything
```

### Update After Upgrading the CLI

```bash
npm install -g @fission-ai/openspec@latest
openspec update            # regenerates tool configs in each project
```

---

## 4. Directory Structure — Every File Explained

After `openspec init`, your project looks like this:

```
project_root/
├── openspec/
│   ├── AGENTS.md                  # AI agent instruction set (managed by OpenSpec)
│   ├── project.md                 # Global project context, tech stack, conventions
│   ├── config.yaml                # Project configuration (optional, you create this)
│   │
│   ├── specs/                     # SOURCE OF TRUTH — current system behavior
│   │   ├── auth-login/            #   Organized by capability/domain
│   │   │   └── spec.md            #   One spec file per capability
│   │   ├── auth-session/
│   │   │   └── spec.md
│   │   ├── checkout-cart/
│   │   │   └── spec.md
│   │   └── checkout-payment/
│   │       └── spec.md
│   │
│   ├── changes/                   # ACTIVE CHANGE PROPOSALS (workspace)
│   │   └── add-dark-mode/         #   One folder per change (kebab-case, verb-led)
│   │       ├── .openspec.yaml     #   Change metadata (schema, timestamps)
│   │       ├── proposal.md        #   Why + What: intent, scope, approach
│   │       ├── design.md          #   How: technical decisions, architecture
│   │       ├── tasks.md           #   Implementation checklist (mark checkboxes)
│   │       └── specs/             #   DELTA SPECS — what's changing
│   │           └── ui/
│   │               └── spec.md    #   ADDED/MODIFIED/REMOVED requirements
│   │
│   └── changes/archive/           # COMPLETED CHANGES (audit trail)
│       └── 2026-06-15-add-dark-mode/   # Date-prefixed for ordering
│           └── ... (same structure as active change)
│
└── .claude/
    └── skills/                    # AI tool skill files (Claude Code example)
        └── openspec-*.md          # Auto-generated by openspec init/update
```

### File-By-File Explanation

#### `openspec/AGENTS.md`
- **What**: Auto-generated instructions for AI coding assistants.
- **Who reads it**: Your AI agent reads this automatically when loaded into the project.
- **Do not edit manually**: Regenerated by `openspec update`. Customize via `config.yaml` instead.

#### `openspec/project.md`
- **What**: High-level project context. Tech stack, coding conventions, architecture notes.
- **Who reads it**: AI agents during `/opsx:propose` and `/opsx:explore`.
- **You maintain it**: Update when your tech stack or conventions change.

#### `openspec/config.yaml` (optional, you create)
- **What**: Per-project customization — default schema, context injection, per-artifact rules.
- **Example**:
```yaml
schema: spec-driven
context: |
  Tech stack: TypeScript, React, Node.js, PostgreSQL
  Testing: Vitest (unit), Playwright (e2e)
  API style: RESTful, JSON responses
rules:
  proposal:
    - Include a rollback plan
    - Identify affected teams/services
  specs:
    - Use GIVEN/WHEN/THEN format for all scenarios
    - Each requirement MUST have at least one scenario
  design:
    - Include sequence diagrams for complex flows
    - Document database migrations
```

#### `openspec/specs/<capability>/spec.md`
- **What**: The *current* system behavior for a capability. The Source of Truth.
- **Format**: Markdown with structured `## Requirements`, `### Requirement:`, `#### Scenario:` sections.
- **Example**:
```markdown
# auth-session Specification

## Purpose
Manage user session lifecycle including creation, validation, and expiration.

## Requirements

### Requirement: Session Creation
The system SHALL create a session token upon successful authentication.

#### Scenario: Successful login
- GIVEN a user with valid credentials
- WHEN the user submits the login form
- THEN a session token is issued
- AND the user is redirected to the dashboard

#### Scenario: Failed login
- GIVEN a user with invalid credentials
- WHEN the user submits the login form
- THEN no session token is issued
- AND an error message is displayed

### Requirement: Session Expiration
The system SHALL expire sessions after a configured duration of inactivity.

#### Scenario: Default session timeout
- GIVEN a user has authenticated
- WHEN 24 hours pass without activity
- THEN invalidate the session token
- AND require re-authentication
```

#### `openspec/changes/<change-id>/proposal.md`
- **What**: The "Why" and "What" of the change.
- **Generated by**: `/opsx:propose` or `/opsx:ff`
- **Template structure**:
  - **Motivation**: Why this change is needed
  - **Scope**: What is and isn't changing
  - **Approach**: High-level strategy
  - **Impact**: Affected specs, services, teams
  - **Risks**: Known risks and mitigation
  - **Rollback**: How to undo if needed

#### `openspec/changes/<change-id>/design.md`
- **What**: Technical decisions, architecture, trade-offs.
- **Generated by**: `/opsx:propose` or `/opsx:ff` or `/opsx:continue`
- **Template structure**:
  - **Architecture**: Component diagram, data flow
  - **Database Changes**: Migrations, new tables/columns
  - **API Changes**: New/modified endpoints
  - **Security Considerations**
  - **Performance Considerations**
  - **Trade-offs**: What was considered and rejected

#### `openspec/changes/<change-id>/tasks.md`
- **What**: Ordered implementation checklist.
- **Generated by**: `/opsx:propose` or `/opsx:ff` or `/opsx:continue`
- **Template structure**:
```markdown
## Phase 1: Database
- [ ] 1.1 Create migration for new columns
- [ ] 1.2 Update seed data

## Phase 2: Backend
- [ ] 2.1 Add new endpoint POST /api/sessions
- [ ] 2.2 Update session middleware
- [ ] 2.3 Add unit tests for session logic

## Phase 3: Frontend
- [ ] 3.1 Add "Remember Me" checkbox to login form
- [ ] 3.2 Update session handling in API client
- [ ] 3.3 Add e2e test for extended session
```

#### `openspec/changes/<change-id>/specs/<capability>/spec.md`
- **What**: DELTA SPEC — what's changing in this capability's spec.
- **Format**: Uses `## ADDED Requirements`, `## MODIFIED Requirements`, `## REMOVED Requirements` sections.
- **Detailed coverage in Section 11**.

#### `openspec/changes/<change-id>/.openspec.yaml`
- **What**: Machine-readable metadata for the change.
- **Example**:
```yaml
schema: spec-driven
created: 2026-06-15T10:30:00Z
updated: 2026-06-15T14:20:00Z
```

---

## 5. Skills (Slash Commands) — Complete Reference

OpenSpec commands are **slash commands** invoked inside your AI coding assistant's chat interface. They are NOT terminal commands — they are AI-level instructions.

### 5.1 Choosing Your Workflow Profile

OpenSpec has two workflow profiles:

| Profile | Commands Available | Best For |
|---|---|---|
| **`core` (default)** | `propose`, `explore`, `apply`, `sync`, `archive` | Quick path: create → implement → archive |
| **`expanded` (opt-in)** | All core + `new`, `continue`, `ff`, `verify`, `bulk-archive`, `onboard` | Step-by-step control, teams, complex changes |

To enable expanded commands:
```bash
openspec config profile     # interactive: select "workflows"
openspec update             # apply to current project
```

### 5.2 Core Commands (Default Profile)

#### `/opsx:propose` — Create Change + Generate All Planning Artifacts

The primary entry point. One command creates the entire change scaffold.

```
Syntax:  /opsx:propose [change-name-or-description]
```

**What it does:**
1. Runs `openspec list` to see active changes
2. Runs `openspec list --specs` to see existing capabilities
3. Creates `openspec/changes/<change-name>/`
4. Generates `proposal.md`, `specs/<capability>/spec.md` (deltas), `design.md`, `tasks.md`
5. Returns summary: "Ready for `/opsx:apply`"

**Files created:**
- `openspec/changes/<change-name>/.openspec.yaml` (metadata)
- `openspec/changes/<change-name>/proposal.md`
- `openspec/changes/<change-name>/design.md`
- `openspec/changes/<change-name>/tasks.md`
- `openspec/changes/<change-name>/specs/<capability>/spec.md` (delta)

**Example:**
```
You: /opsx:propose add-dark-mode

AI:  Created openspec/changes/add-dark-mode/
     ✓ proposal.md    — Motivation: users want reduced eye strain
     ✓ specs/ui/spec.md — ADDED: 2 requirements for dark mode
     ✓ design.md      — CSS variables approach, no new dependencies
     ✓ tasks.md       — 6 tasks across 2 phases
     Ready for review. Run /opsx:apply to implement.
```

---

#### `/opsx:explore` — Investigate Before Committing

Think through ideas, analyze the codebase, compare approaches — no artifacts created.

```
Syntax:  /opsx:explore [topic]
```

**What it does:**
- Opens an unstructured exploratory conversation
- Searches codebase, reads existing specs
- Compares approaches, surfaces trade-offs
- Does NOT create any files
- Can transition to `/opsx:propose` when insights crystallize

**When to use:**
- Requirements are unclear
- You want to compare multiple approaches
- You're in a brownfield codebase and need to understand what exists

**No files created.**

**Example:**
```
You: /opsx:explore How to add file uploads

AI: Let me investigate the codebase...
    Current state: No existing upload infrastructure.
    3 approaches:
    1. S3 presigned URLs (simplest, requires AWS)
    2. Multipart upload via API (flexible, more code)
    3. Third-party service (Uploadthing, Cloudinary)
    
    Given your AWS infra from project.md, I'd recommend #1.
    Want me to create a change proposal?
```

---

#### `/opsx:apply` — Implement the Change

Execute tasks from the change's `tasks.md` checklist.

```
Syntax:  /opsx:apply [change-name]
```

**What it does:**
1. Reads `proposal.md`, `design.md`, `specs/`, `tasks.md`
2. Implements tasks sequentially, marking `- [x]` as complete
3. Updates artifacts if implementation reveals issues
4. Returns: "All tasks complete" or "N/M tasks done"

**When to use:**
- After reviewing and approving the proposal
- After `/opsx:propose` or `/opsx:ff`

**No new files created** (modifies existing code and marks tasks complete).

**Example:**
```
You: /opsx:apply

AI: Implementing add-dark-mode...
    [x] 1.1 Add CSS custom properties for color scheme     ✓
    [x] 1.2 Create ThemeContext provider                    ✓
    [x] 1.3 Add theme toggle component                      ✓
    [x] 2.1 Update existing components to use theme vars    ✓
    [x] 2.2 Add localStorage persistence                    ✓
    [x] 2.3 Add system preference detection                 ✓
    All 6 tasks complete. Ready for /opsx:archive.
```

---

#### `/opsx:sync` — Merge Delta Specs to Source of Truth

Applies the delta specs from a change into the main `openspec/specs/` tree.

```
Syntax:  /opsx:sync [change-name]
```

**What it does:**
- Reads delta specs from `changes/<name>/specs/`
- Merges ADDED/MODIFIED/REMOVED into `openspec/specs/<capability>/spec.md`
- Does NOT archive the change (that's `/opsx:archive`)

**When to use:**
- You want to update specs mid-implementation (e.g., after a design change)
- Rarely needed if using `/opsx:archive` (which does sync + archive)

**Example output:**
```
Syncing specs for add-dark-mode...
  ui: + 2 added, ~ 0 modified, - 0 removed
Specs updated. Change is still active.
```

---

#### `/opsx:archive` — Complete and Archive

Finalize a change: merge deltas into source of truth + move to archive.

```
Syntax:  /opsx:archive [change-name]
```

**What it does:**
1. Validates the change: `openspec validate <change-name>`
2. Merges delta specs from `changes/<name>/specs/` into `openspec/specs/`
3. Moves the change folder to `openspec/changes/archive/<YYYY-MM-DD>-<name>/`
4. Reports: "Change archived successfully"

**Example output:**
```
Archiving add-dark-mode...
Specs to update:
  ui: update (+ 2 added)
Totals: + 2, ~ 0, - 0
Change 'add-dark-mode' archived as '2026-06-15-add-dark-mode'.
```

---

### 5.3 Expanded Commands (opt-in via `openspec config profile`)

#### `/opsx:new` — Scaffold a New Change

Create just the change directory and metadata — no artifacts yet.

```
Syntax:  /opsx:new [change-name] [--schema <schema-name>]
```

**What it does:**
- Creates `openspec/changes/<change-name>/` and `.openspec.yaml`
- Shows which artifact is ready to create next
- Must follow with `/opsx:continue` or `/opsx:ff`

**Files created:**
- `openspec/changes/<change-name>/.openspec.yaml`

**Example:**
```
You: /opsx:new add-dark-mode

AI: Created openspec/changes/add-dark-mode/
    Schema: spec-driven
    Ready to create: proposal
    Use /opsx:continue or /opsx:ff.
```

---

#### `/opsx:continue` — Create Next Artifact (One at a Time)

Step-by-step artifact creation, following the dependency chain.

```
Syntax:  /opsx:continue [change-name]
```

**What it does:**
1. Checks `openspec status --change <name> --json`
2. Shows artifact status (done/ready/blocked)
3. Creates the next ready artifact
4. Reads dependencies for context

**Artifact dependency chain:**
```
proposal → specs → design → tasks → (implementation)
```

**Files created** (one per call): proposal.md → specs/ → design.md → tasks.md

**Example:**
```
You: /opsx:continue

AI: Change: add-dark-mode
    Artifact status:
    ✓ proposal   (done)
    ◆ specs      (ready)
    ◆ design     (ready)
    ○ tasks      (blocked — needs: specs)
    Creating specs...
    ✓ Created specs/ui/spec.md
    Next: tasks is now available.
```

---

#### `/opsx:ff` — Fast-Forward: All Planning Artifacts at Once

Equivalent to `/opsx:propose` in the core profile — create everything.

```
Syntax:  /opsx:ff [change-name]
```

**Files created** (same as `/opsx:propose`): proposal.md, specs/, design.md, tasks.md

**Use when:** You already understand the problem and want to skip step-by-step review.

---

#### `/opsx:verify` — Validate Implementation Against Artifacts

Check that the implemented code matches the specs and design.

```
Syntax:  /opsx:verify [change-name]
```

**What it does:**
- Reads specs and verifies each requirement is implemented
- Checks for missing features, extra features, behavioral mismatches
- Reports: "All verified" or lists gaps

**No files created.**

**Example:**
```
You: /opsx:verify add-dark-mode

AI: Verifying add-dark-mode...
    ✓ Dark mode toggle renders in settings
    ✓ CSS variables switch on theme change
    ✓ localStorage persists preference
    ✗ System preference detection not found (req 2.3)
    3/4 requirements verified. 1 gap found.
```

---

#### `/opsx:bulk-archive` — Archive Multiple Changes

Archive several completed changes at once.

```
Syntax:  /opsx:bulk-archive [change-name-1] [change-name-2] ...
```

**What it does:** Sequentially archives each change. Resolves merge conflicts if two changes touch the same spec.

---

#### `/opsx:onboard` — Guided Tutorial

Interactive walkthrough of the complete OpenSpec workflow.

```
Syntax:  /opsx:onboard
```

**What it does:** Teaches the user by walking through a mock change — propose, review, apply, archive.

---

### 5.4 Skill-to-File Mapping (Quick Reference)

| Command | Files Created |
|---|---|
| `/opsx:propose` | `.openspec.yaml`, `proposal.md`, `design.md`, `tasks.md`, `specs/<cap>/spec.md` (delta) |
| `/opsx:explore` | *None* |
| `/opsx:apply` | *None* (modifies existing source code) |
| `/opsx:sync` | *None* (modifies `openspec/specs/`) |
| `/opsx:archive` | *None* (modifies `openspec/specs/`, moves change to `archive/`) |
| `/opsx:new` | `.openspec.yaml` only |
| `/opsx:continue` | One artifact at a time (proposal → specs → design → tasks) |
| `/opsx:ff` | Same as `/opsx:propose` |
| `/opsx:verify` | *None* |
| `/opsx:bulk-archive` | *None* (same effect as multiple `/opsx:archive`) |
| `/opsx:onboard` | *Temporary demo change files* |

---

## 6. Core Workflow: The Four-Stage Lifecycle

Every change moves through four stages:

```
 EXPLORE ──────► CREATE ──────► APPLY ──────► ARCHIVE
   │                │               │              │
 understand      proposal        implement      merge specs
 the problem     specs           the tasks      into source
                 design                         of truth
                 tasks
```

### Stage 1: EXPLORE (Optional but Recommended)

- **Command**: `/opsx:explore [topic]`
- **Goal**: Understand the problem before committing.
- **Output**: Analysis, options, recommendations. No files.
- **Brownfield tip**: This is where you baseline existing behavior.

### Stage 2: CREATE

- **Command**: `/opsx:propose <name>` (core) or `/opsx:ff <name>` (expanded)
- **Goal**: Define the change via artifacts.
- **Output**: proposal.md, specs/, design.md, tasks.md
- **Review gate**: Review the artifacts. Do NOT proceed until satisfied.

### Stage 3: APPLY

- **Command**: `/opsx:apply [change-name]`
- **Goal**: Implement the code.
- **Output**: Actual code changes. Tasks marked complete.
- **Iterate**: If implementation reveals issues, update artifacts and re-apply.

### Stage 4: ARCHIVE

- **Command**: `/opsx:archive [change-name]`
- **Goal**: Merge deltas into source of truth; preserve audit trail.
- **Output**: Updated `openspec/specs/`. Change moved to `archive/`.
- **Prerequisite**: Validate first (`openspec validate <name>`).

### The Complete Flow (Diagram)

```
You: /opsx:explore "How to add file uploads"
AI:  [Analyzes codebase, compares 3 approaches, recommends S3 presigned URLs]
---
You: /opsx:propose add-file-uploads
AI:  [Creates change folder with proposal, specs, design, tasks]
---
You: [Reviews artifacts, approves]
You: /opsx:apply
AI:  [Implements tasks, checks them off]
You: [Tests manually, all good]
---
You: /opsx:archive add-file-uploads
AI:  [Validates, merges deltas into specs/file-upload/spec.md,
      moves change to archive/2026-06-15-add-file-uploads/]
```

---

## 7. Greenfield Projects (0→1) — Complete Walkthrough

A greenfield project starts from zero — no existing code, no existing specs. OpenSpec helps you define the system incrementally.

### Phase 1: Initialize

```bash
mkdir my-task-api && cd my-task-api
npm init -y
openspec init        # select your AI tool
```

This creates the `openspec/` directory with empty `specs/` and `changes/`.

### Phase 2: Define Project Context

Edit `openspec/project.md`:
```markdown
# Task API — Project Context

## Tech Stack
- Runtime: Node.js 22 + TypeScript 5.x
- Framework: Express.js
- Database: PostgreSQL 16 via Prisma ORM
- Testing: Vitest (unit), Supertest (integration)
- Auth: JWT-based

## Conventions
- RESTful API design
- All endpoints prefixed with /api/v1
- Standard error response: { error: string, code: string }
- Input validation via Zod
```

### Phase 3: Create Your First Feature

```
You: /opsx:propose add-task-crud

AI:  Created openspec/changes/add-task-crud/
     ✓ proposal.md
     ✓ specs/task-crud/spec.md  (ADDED: 4 requirements)
     ✓ design.md
     ✓ tasks.md                 (8 tasks across 3 phases)
```

**What gets generated:**

- `proposal.md`: Motivation ("Core task management is the foundation"), scope ("CRUD operations only, no filtering/sorting yet"), approach ("Express routes → Prisma → PostgreSQL")
- `specs/task-crud/spec.md`: Delta spec with `## ADDED Requirements`:
  - Requirement: Create Task (with 3 scenarios)
  - Requirement: List Tasks (with 2 scenarios)
  - Requirement: Get Task by ID (with 3 scenarios)
  - Requirement: Update Task (with 3 scenarios)
  - Requirement: Delete Task (with 2 scenarios)
- `design.md`: Route structure, Prisma schema, error handling patterns
- `tasks.md`: Phase 1: Prisma setup, Phase 2: Routes + controllers, Phase 3: Tests

### Phase 4: Review & Implement

```bash
# Terminal
openspec list                  # see: add-task-crud (active)
openspec show add-task-crud    # review artifacts
openspec validate add-task-crud --strict
```

```
You: /opsx:apply

AI:  [Creates Prisma schema, migrations, Express routes, tests]
     [Marks all 8 tasks complete]
```

### Phase 5: Archive

```
You: /opsx:archive add-task-crud

AI:  Archiving add-task-crud...
     Specs to update:
       task-crud: create (+ 5 reqs, 13 scenarios)
     Change archived as 2026-06-15-add-task-crud.
```

**Now `openspec/specs/task-crud/spec.md` exists** — the permanent source of truth for task CRUD.

### Phase 6: Add More Features (Iterate)

```
You: /opsx:propose add-task-filtering-and-sorting

AI:  [Reads existing specs/task-crud/spec.md]
     [Creates change with MODIFIED requirements for List Tasks,
      ADDED requirements for filtering and sorting]
     ...
```

Each new feature builds on existing specs by creating **delta specs** (ADDED/MODIFIED/REMOVED), not rewriting the entire spec from scratch.

---

## 8. Brownfield Projects (1→n) — Complete Walkthrough

Brownfield = existing codebase with production traffic. OpenSpec is *designed* for this.

### Phase 1: Initialize on Existing Codebase

```bash
cd my-existing-api
openspec init       # does NOT touch your code
```

### Phase 2: Baseline Existing Specs

The key challenge in brownfield: OpenSpec's `specs/` directory starts empty, but your codebase already has behavior that should be documented.

**Two approaches:**

#### Approach A: Explore-First (Recommended)

Use `/opsx:explore` to investigate the existing system before creating specs:

```
You: /opsx:explore "What auth functionality exists?"

AI:  [Searches codebase]
     Found: JWT-based login, session management, password reset.
     Current routes: POST /api/v1/auth/login, POST /api/v1/auth/register,
                     POST /api/v1/auth/reset-password
     Let me create a baseline...
```

Then create a change to document existing behavior:

```
You: /opsx:propose document-auth-baseline

AI:  Creates change with ADDED specs that describe the
     EXISTING behavior (not new behavior).
     This is a "documentation change" — no code changes.
```

#### Approach B: Gradual Baseline

Add specs incrementally — only for the parts you're about to change:

```
# You're about to add "Remember Me". First baseline the session spec.
You: /opsx:propose baseline-session-spec

AI:  Reads session code, creates specs/auth-session/spec.md
     describing current behavior. No code changes.
     Archive immediately: /opsx:archive baseline-session-spec

# Now propose the actual change
You: /opsx:propose add-remember-me

AI:  Reads specs/auth-session/spec.md (the baseline we just created!)
     Creates delta with MODIFIED requirement: Session Expiration
     Adds "Remember Me" scenario with 30-day timeout
```

### Phase 3: The Brownfield Change Lifecycle

```
1. EXPLORE    /opsx:explore "How does <area> work?"
              → AI reads source code, returns analysis

2. BASELINE   /opsx:propose document-<area>-baseline
   (if needed) → Creates ADDED specs for existing behavior
              → Archive immediately (no code changes)

3. PROPOSE    /opsx:propose <your-change>
              → AI reads existing specs (the baseline!)
              → Creates delta specs (ADDED/MODIFIED/REMOVED)

4. APPLY      /opsx:apply
              → Implements against baselined spec understanding

5. ARCHIVE    /opsx:archive <your-change>
              → Merges deltas into the now-live spec tree
```

### Key Brownfield Insight

OpenSpec separates **Source Specs** (`specs/`) from **Proposed Changes** (`changes/`). This means:

- Existing code behavior = what's in `specs/` (once baselined)
- Proposed modifications = what's in `changes/<name>/specs/`
- The delta between them = exactly what the agent will change

Without this separation, AI agents "hallucinate" what exists. With it, they read the spec, understand the system, and propose precise deltas.

---

## 9. Practical Example 1: Build a Task API (Greenfield)

Let's walk through building a complete Task Management API from scratch with OpenSpec.

### Setup

```bash
mkdir task-api && cd task-api
npm init -y
npm install express typescript prisma @prisma/client zod
npx tsc --init
openspec init
```

Edit `openspec/project.md`:
```markdown
# Task API

## Tech Stack
- Node.js 22, TypeScript 5.x, Express.js
- PostgreSQL + Prisma ORM
- Zod for validation, Vitest for testing

## Conventions
- RESTful: /api/v1/tasks
- GET /api/v1/health for health check
- Standard errors: { error: string, details?: any }
```

### Step 1: Propose — Create Task CRUD

```
You: /opsx:propose add-task-crud
```

**What the AI does:**
1. Reads `openspec/project.md` for tech stack context
2. Sees `openspec/specs/` is empty (greenfield)
3. Creates `openspec/changes/add-task-crud/` with:

**proposal.md** (generated by AI):
```markdown
# Add Task CRUD Operations

## Motivation
The Task API needs core CRUD operations as its foundation.
Without this, no other features (filtering, comments, labels) can be built.

## Scope
- POST /api/v1/tasks — Create a task
- GET /api/v1/tasks — List all tasks
- GET /api/v1/tasks/:id — Get a single task
- PUT /api/v1/tasks/:id — Update a task
- DELETE /api/v1/tasks/:id — Delete a task

## Out of Scope
- Filtering, searching, sorting (separate change)
- User authentication (separate change)
- Task assignment (separate change)

## Approach
1. Define Prisma schema for Task model
2. Create Express router with Zod validation
3. Write integration tests with Supertest

## Impact
- New spec: task-crud
- New DB table: tasks
- No existing specs affected
```

**specs/task-crud/spec.md** (delta — generated by AI):
```markdown
# Delta for Task CRUD

## ADDED Requirements

### Requirement: Create Task
The system SHALL allow creating a new task with a title and optional description.

#### Scenario: Create task with title only
- GIVEN no tasks exist
- WHEN a POST request is sent to /api/v1/tasks with { "title": "Buy groceries" }
- THEN a new task is created with status "pending"
- AND the response status is 201
- AND the response body contains an id, title, and createdAt timestamp

#### Scenario: Create task with title and description
- GIVEN no tasks exist
- WHEN a POST request is sent with { "title": "Report", "description": "Q4 report" }
- THEN a new task is created with the provided title and description
- AND the response status is 201

#### Scenario: Create task with empty title
- GIVEN no tasks exist
- WHEN a POST request is sent with { "title": "" }
- THEN the response status is 400
- AND the response body contains an error message about invalid title

### Requirement: List Tasks
The system SHALL return all tasks ordered by creation date (newest first).

#### Scenario: List empty tasks
- GIVEN no tasks exist
- WHEN a GET request is sent to /api/v1/tasks
- THEN the response status is 200
- AND the response body is an empty array

#### Scenario: List multiple tasks
- GIVEN 3 tasks exist
- WHEN a GET request is sent to /api/v1/tasks
- THEN the response status is 200
- AND the response body contains all 3 tasks
- AND tasks are ordered by createdAt descending

### Requirement: Get Task by ID
The system SHALL return a single task by its unique identifier.

#### Scenario: Get existing task
- GIVEN a task with id "abc-123" exists
- WHEN a GET request is sent to /api/v1/tasks/abc-123
- THEN the response status is 200
- AND the response body contains the task's title, description, status

#### Scenario: Get non-existent task
- GIVEN no task with id "nonexistent" exists
- WHEN a GET request is sent to /api/v1/tasks/nonexistent
- THEN the response status is 404

#### Scenario: Get task with invalid ID format
- GIVEN the ID format is UUID
- WHEN a GET request is sent to /api/v1/tasks/not-a-uuid
- THEN the response status is 400

### Requirement: Update Task
The system SHALL allow updating a task's title, description, and status.

#### Scenario: Update task title
- GIVEN a task with id "abc-123" and title "Old title"
- WHEN a PUT request is sent with { "title": "New title" }
- THEN the task's title is updated
- AND the response status is 200

#### Scenario: Update task to completed
- GIVEN a task with status "pending"
- WHEN a PUT request is sent with { "status": "completed" }
- THEN the task's status is updated
- AND the response status is 200

#### Scenario: Update non-existent task
- GIVEN no task with id "nonexistent"
- WHEN a PUT request is sent with { "title": "Test" }
- THEN the response status is 404

### Requirement: Delete Task
The system SHALL allow deleting a task by its ID.

#### Scenario: Delete existing task
- GIVEN a task with id "abc-123" exists
- WHEN a DELETE request is sent to /api/v1/tasks/abc-123
- THEN the task is removed
- AND the response status is 204

#### Scenario: Delete non-existent task
- GIVEN no task with id "nonexistent"
- WHEN a DELETE request is sent to /api/v1/tasks/nonexistent
- THEN the response status is 404
```

**design.md** (generated by AI):
```markdown
# Task CRUD — Technical Design

## Architecture
- Single Express router mounted at /api/v1/tasks
- Prisma ORM for database access
- Zod schemas for input validation
- Standardized error middleware

## Database
```prisma
model Task {
  id          String   @id @default(uuid())
  title       String
  description String?
  status      String   @default("pending") // pending | completed
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}
```

## API Routes
| Method | Path | Handler | Validation |
|--------|------|---------|------------|
| POST | /api/v1/tasks | createTask | title: string.min(1) |
| GET | /api/v1/tasks | listTasks | none |
| GET | /api/v1/tasks/:id | getTask | id: uuid |
| PUT | /api/v1/tasks/:id | updateTask | id: uuid, body: partial task |
| DELETE | /api/v1/tasks/:id | deleteTask | id: uuid |

## Error Patterns
```typescript
{ error: "Task not found" }           // 404
{ error: "Validation failed",         // 400
  details: [{ field: "title",
              message: "Required" }] }
```
```

**tasks.md** (generated by AI):
```markdown
# Task CRUD — Implementation Checklist

## Phase 1: Database Setup
- [ ] 1.1 Initialize Prisma and define Task schema
- [ ] 1.2 Generate Prisma client and run migration

## Phase 2: Backend Routes
- [ ] 2.1 Create Zod validation schemas for Task
- [ ] 2.2 Implement POST /api/v1/tasks (create)
- [ ] 2.3 Implement GET /api/v1/tasks (list)
- [ ] 2.4 Implement GET /api/v1/tasks/:id (get by ID)
- [ ] 2.5 Implement PUT /api/v1/tasks/:id (update)
- [ ] 2.6 Implement DELETE /api/v1/tasks/:id (delete)
- [ ] 2.7 Add error handling middleware

## Phase 3: Testing
- [ ] 3.1 Write integration tests for create task (3 scenarios)
- [ ] 3.2 Write integration tests for list tasks (2 scenarios)
- [ ] 3.3 Write integration tests for get task (3 scenarios)
- [ ] 3.4 Write integration tests for update task (3 scenarios)
- [ ] 3.5 Write integration tests for delete task (2 scenarios)
```

### Step 2: Review & Validate

```bash
openspec validate add-task-crud --strict
# Output: Change 'add-task-crud' is valid.
```

### Step 3: Apply — AI Implements

```
You: /opsx:apply
```

The AI systematically implements each task, marking checkboxes:
```
[x] 1.1 Initialize Prisma and define Task schema
[x] 1.2 Generate Prisma client and run migration
[x] 2.1 Create Zod validation schemas for Task
[x] 2.2 Implement POST /api/v1/tasks (create)
...
[x] 3.5 Write integration tests for delete task (2 scenarios)

All 13 tasks complete. 37 tests passing.
Ready for /opsx:archive.
```

### Step 4: Archive

```
You: /opsx:archive add-task-crud

AI:  Archiving...
     task-crud: create (+ 5 reqs, 13 scenarios)
     Archived as 2026-06-15-add-task-crud.
```

Now `openspec/specs/task-crud/spec.md` contains the complete task CRUD spec — the source of truth.

---

## 10. Practical Example 2: Evolve the Task API (Brownfield — Add Features + Deprecate Old)

Now let's evolve the Task API we built in Example 1. We'll:

1. Add **filtering, searching, and sorting** to task listing
2. Add **task labels** (tags)
3. **Deprecate** the simple `PUT /api/v1/tasks/:id` in favor of `PATCH` with partial updates

### Current State (Source of Truth)

After Example 1, `openspec/specs/task-crud/spec.md` has:
- Create Task (3 scenarios)
- List Tasks (2 scenarios — simple list, no filtering)
- Get Task by ID (3 scenarios)
- Update Task (3 scenarios — full PUT)
- Delete Task (2 scenarios)

### Change 1: Add Filtering, Searching, and Sorting

```
You: /opsx:propose add-task-filtering-search-sort
```

The AI reads `openspec/specs/task-crud/spec.md` and sees the existing List Tasks requirement. It creates a **delta spec** that MODIFIES the existing behavior.

**specs/task-crud/spec.md** (delta — generated by AI):
```markdown
# Delta for Task CRUD — Filtering, Search, Sort

## MODIFIED Requirements

### Requirement: List Tasks
The system SHALL return tasks with optional filtering, search, and sorting.
All query parameters are optional. Default: all tasks, newest first.

#### Scenario: List empty tasks (unchanged)
- GIVEN no tasks exist
- WHEN a GET request is sent to /api/v1/tasks
- THEN the response status is 200
- AND the response body is an empty array

#### Scenario: List multiple tasks (unchanged)
- GIVEN 3 tasks exist
- WHEN a GET request is sent to /api/v1/tasks
- THEN the response status is 200
- AND the response body contains all 3 tasks
- AND tasks are ordered by createdAt descending

#### Scenario: Filter by status
- GIVEN tasks with statuses "pending" and "completed" exist
- WHEN a GET request is sent to /api/v1/tasks?status=pending
- THEN only pending tasks are returned

#### Scenario: Search by title
- GIVEN tasks titled "Buy groceries", "Write report", "Buy milk"
- WHEN a GET request is sent to /api/v1/tasks?search=Buy
- THEN only tasks whose title contains "Buy" are returned

#### Scenario: Sort by title ascending
- GIVEN tasks titled "Zebra", "Apple", "Mango"
- WHEN a GET request is sent to /api/v1/tasks?sort=title&order=asc
- THEN tasks are returned in alphabetical order

## ADDED Requirements

### Requirement: Pagination
The system SHALL support cursor-based pagination for task listing.

#### Scenario: First page with 10 items
- GIVEN 25 tasks exist
- WHEN a GET request is sent to /api/v1/tasks?limit=10
- THEN 10 tasks are returned
- AND the response includes a nextCursor for the next page

#### Scenario: Last page
- GIVEN 25 tasks exist
- WHEN a GET request is sent with cursor pointing to the 21st task and limit=10
- THEN 5 tasks are returned
- AND no nextCursor is present
```

**What's happening:**
- `## MODIFIED Requirements` — the List Tasks requirement now supports query params. Original scenarios preserved, new ones added.
- `## ADDED Requirements` — Pagination is a brand-new requirement.
- The delta makes it crystal clear: "We're changing List Tasks AND adding Pagination."

### Change 1: Apply & Archive

```
You: /opsx:apply
You: /opsx:archive add-task-filtering-search-sort
```

After archive, `openspec/specs/task-crud/spec.md` now shows the merged result:
- List Tasks has 5 scenarios (was 2)
- Pagination has 2 scenarios (new)

### Change 2: Add Task Labels

```
You: /opsx:propose add-task-labels
```

AI creates delta specs that ADD the Labels requirement (no MODIFIED or REMOVED).

**specs/task-crud/spec.md** (delta):
```markdown
# Delta for Task CRUD — Labels

## ADDED Requirements

### Requirement: Task Labels
The system SHALL support attaching labels/tags to tasks.

#### Scenario: Create task with labels
- GIVEN the labels "urgent" and "backend" exist
- WHEN a POST request includes { "labels": ["urgent", "backend"] }
- THEN the task is created with both labels attached

#### Scenario: Add label to existing task
- GIVEN a task exists with no labels
- WHEN a PUT request adds labels ["frontend"]
- THEN the task has label "frontend"

#### Scenario: Filter tasks by label
- GIVEN tasks with labels "urgent" and "normal"
- WHEN a GET request is sent to /api/v1/tasks?label=urgent
- THEN only urgent tasks are returned

#### Scenario: Remove label from task
- GIVEN a task has label "frontend"
- WHEN the label "frontend" is removed via update
- THEN the task has zero labels
```

### Change 3: Deprecate Full PUT in Favor of PATCH

This is the important one — **deprecating old behavior**.

```
You: /opsx:propose replace-put-with-patch
```

**specs/task-crud/spec.md** (delta — generated by AI):
```markdown
# Delta for Task CRUD — Replace PUT with PATCH

## MODIFIED Requirements

### Requirement: Update Task
The system SHALL support partial updates via PATCH.
The PUT endpoint is deprecated and will be removed in v2.

#### Scenario: Partial update via PATCH (new)
- GIVEN a task with title "Old" and description "Desc"
- WHEN a PATCH request is sent with { "title": "New" }
- THEN only the title is updated
- AND the description remains "Desc"
- AND the response status is 200

#### Scenario: Update status via PATCH (new)
- GIVEN a task with status "pending"
- WHEN a PATCH request is sent with { "status": "completed" }
- THEN only the status is updated
- AND completedAt is set to the current timestamp

#### Scenario: Full update via deprecated PUT (unchanged, deprecated)
- GIVEN a task with id "abc-123"
- WHEN a PUT request is sent with { "title": "Updated" }
- THEN the task is updated (current behavior preserved)
- AND the response includes a Deprecation header
- AND the response includes a Warning header with sunset date

## REMOVED Requirements

None directly removed — PUT is soft-deprecated with headers until v2.

## ADDED Requirements

### Requirement: Deprecation Headers
The system SHALL include standard deprecation headers on deprecated endpoints.

#### Scenario: PUT returns deprecation warning
- GIVEN the PUT endpoint is deprecated
- WHEN any PUT request is made
- THEN the response includes: Deprecation: true
- AND the response includes: Sunset: Sat, 01 Aug 2026 00:00:00 GMT
- AND the response includes: Link: rel="alternate"; /api/v1/tasks/:id (PATCH)
```

**What's happening here:**
- `## MODIFIED Requirements` — Update Task now supports PATCH. PUT behavior preserved but flagged as deprecated.
- `## REMOVED Requirements` — Nothing removed yet (soft deprecation).
- `## ADDED Requirements` — Deprecation Headers is a new requirement for the deprecation mechanism.
- The delta communicates: "We're transitioning from PUT to PATCH. PUT still works but emits warnings. Full removal planned for v2."

### Change 3: Apply & Archive

```
You: /opsx:apply
You: /opsx:archive replace-put-with-patch
```

After archive, `openspec/specs/task-crud/spec.md` now reflects:
- Update Task has 5 scenarios: 2 PATCH (new), 1 PUT-deprecated, 2 original PUT
- Deprecation Headers is a separate requirement in the spec

### Full Spec After Three Changes

After archiving all three changes, the merged `openspec/specs/task-crud/spec.md` contains:

```
Requirements:
  ✓ Create Task         (3 scenarios)  [from Example 1]
  ✓ List Tasks          (5 scenarios)  [2 original + 3 from Change 1]
  ✓ Get Task by ID      (3 scenarios)  [from Example 1]
  ✓ Update Task         (5 scenarios)  [3 original + 2 PATCH from Change 3]
  ✓ Delete Task         (2 scenarios)  [from Example 1]
  ✓ Pagination          (2 scenarios)  [from Change 1]
  ✓ Task Labels         (4 scenarios)  [from Change 2]
  ✓ Deprecation Headers (1 scenario)   [from Change 3]

Total: 8 requirements, 25 scenarios — all auditable by change history.
```

---

## 11. Spec Delta Format — Deep Dive

Delta specs are the heart of OpenSpec's change management. They describe **what's changing** relative to the current spec, not a rewrite of the entire specification.

### Structure

```markdown
# Delta for <Capability Name>

## ADDED Requirements

### Requirement: <New Requirement Name>
<Description of the new requirement>

#### Scenario: <Scenario Name>
- GIVEN <precondition>
- WHEN <action>
- THEN <expected outcome>
- AND <additional outcome>

## MODIFIED Requirements

### Requirement: <Existing Requirement Name>
<Updated description — reflects the new behavior>

#### Scenario: <Scenario Name> (unchanged)
- ... (original scenario preserved)

#### Scenario: <New Scenario Name>
- ... (new scenario added)

## REMOVED Requirements

### Requirement: <Deprecated Requirement>
**Reason**: <Why this is being removed>
**Migration**: <How users should adapt>
```

### Merge Rules (What Happens on Archive)

When `/opsx:archive` runs, it merges delta specs into the main spec:

| Delta Section | Merge Behavior |
|---|---|
| `## ADDED Requirements` | Appended to the main spec's Requirements section |
| `## MODIFIED Requirements` | Replaces the matching requirement in the main spec (matched by name) |
| `## REMOVED Requirements` | Removed from the main spec's Requirements section |
| Scenarios within MODIFIED | If the scenario name matches exactly, it replaces the old scenario. If new, it's added. |

### Example: Before and After a MODIFIED Merge

**Before (main spec):**
```markdown
### Requirement: Session Expiration
The system SHALL expire sessions after a configured duration.

#### Scenario: Default session timeout
- GIVEN a user has authenticated
- WHEN 24 hours pass without activity
- THEN invalidate the session token
```

**Delta spec (from change):**
```markdown
## MODIFIED Requirements

### Requirement: Session Expiration
The system SHALL support configurable session expiration periods.

#### Scenario: Default session timeout
- GIVEN a user has authenticated
- WHEN 24 hours pass without "Remember Me"
- THEN invalidate the session token

#### Scenario: Extended session with remember me
- GIVEN user checks "Remember Me" at login
- WHEN 30 days have passed
- THEN invalidate the session token
- AND clear the persistent cookie
```

**After merge (main spec becomes):**
```markdown
### Requirement: Session Expiration
The system SHALL support configurable session expiration periods.

#### Scenario: Default session timeout
- GIVEN a user has authenticated
- WHEN 24 hours pass without "Remember Me"
- THEN invalidate the session token

#### Scenario: Extended session with remember me
- GIVEN user checks "Remember Me" at login
- WHEN 30 days have passed
- THEN invalidate the session token
- AND clear the persistent cookie
```

### The "No Delta" Anti-Pattern

**WRONG:** Rewriting the entire spec as a delta with everything in ADDED.
```markdown
# Bad: this rewrites the entire spec
## ADDED Requirements
### Requirement: Create Task
... (all 8 requirements from the main spec)
```
This defeats the purpose — reviewers can't see what actually changed.

**RIGHT:** Only ADDED/MODIFIED/REMOVED sections for what's actually changing.
```markdown
# Good: only what's changing
## MODIFIED Requirements
### Requirement: List Tasks
... (the modiffied requirement with new scenarios)

## ADDED Requirements
### Requirement: Pagination
... (the brand-new requirement)
```

---

## 12. Project Configuration (config.yaml)

`openspec/config.yaml` customizes how OpenSpec behaves in your project.

### Full Reference

```yaml
# openspec/config.yaml

# Default schema for new changes (default: "spec-driven")
schema: spec-driven

# Injected into EVERY artifact's AI instructions
# Max 50KB. Use for tech stack, conventions, testing frameworks.
context: |
  Tech stack: TypeScript 5.x, React 18, Node.js 22, PostgreSQL 16
  Testing: Vitest (unit/integration), Playwright (e2e)
  API style: RESTful with JSON responses, /api/v1 prefix
  Database: Prisma ORM with migrations
  CI/CD: GitHub Actions, deploy to Vercel
  Code style: Prettier with default config, ESLint strict

# Per-artifact rules injected into AI instructions
# Valid artifact IDs for spec-driven: proposal, specs, design, tasks
rules:
  proposal:
    - Always include a rollback plan
    - Identify affected services and teams
    - Link to relevant Slack channels for review
    - Include estimated timeline (S/M/L)

  specs:
    - Use GIVEN/WHEN/THEN format for ALL scenarios
    - Each requirement MUST have at least 2 scenarios
    - Include both happy-path and error scenarios
    - Use RFC 2119 keywords: SHALL, SHOULD, MAY

  design:
    - Include sequence diagrams for complex flows (Mermaid)
    - Document all database migrations
    - List all new npm dependencies with justification
    - Include security considerations section

  tasks:
    - Group tasks into numbered phases
    - Mark parallelizable tasks with [P]
    - Include testing tasks in each phase
    - Each task should be completable in < 2 hours
```

### How Config Is Applied

1. **Schema precedence** (highest to lowest): CLI flag → change metadata → project config → default (`spec-driven`)
2. **Context injection**: Prepended to every artifact, wrapped in `<context>...</context>`
3. **Rules injection**: Injected for matching artifacts, wrapped in `<rules>...</rules>`, after context, before template

### Troubleshooting Config

| Problem | Solution |
|---|---|
| "Unknown artifact ID in rules: X" | Check against valid IDs: proposal, specs, design, tasks |
| Config not applied | Ensure file is at `openspec/config.yaml` (NOT `.yml`). Validate YAML. |
| Context too large (>50KB) | Summarize. Link external docs instead. |
| Rules not appearing | Use correct artifact IDs. Check for YAML indentation errors. |

---

## 13. Custom Schemas & OPSX Customization

### What is OPSX?

OPSX is OpenSpec's **customizable workflow engine**. Unlike the legacy hardcoded workflow, OPSX lets you define your own schemas, artifacts, dependencies, and templates.

### Default `spec-driven` Schema Artifacts

```
proposal ──→ specs ──→ design ──→ tasks ──→ (implementation)
```

Each artifact depends on the previous one. Dependencies are **enablers**, not phase gates — you can go back and edit any artifact anytime.

### Creating a Custom Schema

You can define custom schemas in `openspec/schemas/`:

```
openspec/
└── schemas/
    └── my-workflow/
        ├── schema.yaml        # artifact definitions + dependencies
        └── templates/
            ├── proposal.md    # template for the proposal artifact
            ├── specs.md
            ├── design.md
            └── tasks.md
```

**schema.yaml example:**
```yaml
name: spec-driven-with-adr
description: Standard spec-driven workflow with Architecture Decision Records

artifacts:
  - id: proposal
    description: Why and what
    template: templates/proposal.md
    requires: []

  - id: specs
    description: Requirements and scenarios
    template: templates/specs.md
    requires: [proposal]

  - id: design
    description: Technical decisions
    template: templates/design.md
    requires: [proposal]     # can start after proposal (parallel with specs)

  - id: tasks
    description: Implementation checklist
    template: templates/tasks.md
    requires: [specs, design] # needs both before tasks

  - id: adr                    # CUSTOM artifact!
    description: Architecture Decision Record
    template: templates/adr.md
    requires: [design]        # created after design
```

### Using a Custom Schema

```bash
# Set as default in config
# openspec/config.yaml:
#   schema: spec-driven-with-adr

# Or per-change:
/opsx:new my-change --schema spec-driven-with-adr
```

---

## 14. CLI Reference

All `openspec` terminal commands (not slash commands):

| Command | Description |
|---|---|
| `openspec init` | Initialize OpenSpec in a project |
| `openspec update` | Regenerate AI tool configs after CLI upgrade |
| `openspec list` | List all active and archived changes |
| `openspec list --specs` | List all current specifications |
| `openspec list --json` | Machine-readable output |
| `openspec show <change-id>` | Display details of a specific change |
| `openspec show <spec-name> --spec` | Display a specific spec |
| `openspec validate <change-id>` | Validate a change for structural issues |
| `openspec validate <change-id> --strict` | Strict validation (no warnings tolerated) |
| `openspec validate --all` | Validate all active changes |
| `openspec validate --all --json` | JSON output for CI pipelines |
| `openspec status --change <name>` | Show artifact completion status |
| `openspec status --change <name> --json` | Machine-readable artifact status |
| `openspec archive <change-id>` | Archive a completed change (with confirmation) |
| `openspec archive <change-id> --yes` | Archive without confirmation prompt |
| `openspec config profile` | Interactive: choose workflow profile (core vs expanded) |
| `openspec schemas` | List available schemas |
| `openspec schemas --json` | Machine-readable schema list |

### Common Patterns

```bash
# Before starting work: what's active?
openspec list
openspec list --specs

# Validate before archiving
openspec validate add-dark-mode --strict

# Check progress on a change
openspec status --change add-dark-mode

# See all specs after archiving several changes
openspec list --specs
```

---

## 15. Best Practices

### Naming Changes

- Use **verb-led kebab-case**: `add-dark-mode`, `fix-login-redirect`, `refactor-payment-service`, `deprecate-v1-endpoints`
- Avoid generic names: `update`, `changes`, `wip`, `test`
- Names become audit trail entries — make them descriptive

### Spec Quality

- Every requirement needs **at least one scenario**
- Scenarios use **GIVEN/WHEN/THEN** format
- Include **error scenarios** (not just happy paths)
- Requirements use **RFC 2119 keywords**: SHALL (mandatory), SHOULD (recommended), MAY (optional)

### Change Size

| Size | Tasks | Example |
|---|---|---|
| **Small** (recommended) | 1-3 tasks | Add a single endpoint, fix a bug |
| **Medium** | 4-8 tasks | Add filtering + pagination, refactor a module |
| **Large** (split if possible) | 9+ tasks | Full authentication system, database migration |

**Prefer small changes.** They're easier to review, faster to implement, and simpler to roll back.

### Workflow

1. **Always explore first** in brownfield: `/opsx:explore` before `/opsx:propose`
2. **Review artifacts before applying**: Catch misalignment early
3. **Validate before archiving**: `openspec validate <name> --strict`
4. **Archive promptly**: Don't let changes accumulate
5. **Keep project.md updated**: Tech stack changes? Update it.

### Teams & Code Review

- **Review proposals before code**: Reviewers read `proposal.md` + spec deltas, not just code diffs
- **Use artifact gates**: Require proposal approval before `/opsx:apply`
- **Archive before merging PR**: Merge spec changes into `openspec/specs/` as part of the PR

### Model Selection

OpenSpec works best with **high-reasoning models** (Claude Opus 4.7+, Codex 5.5+, GPT-5). Planning artifacts require deep codebase understanding — weaker models may produce shallow specs.

---

## 16. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| AI generates shallow/generic specs | Model too weak | Use a higher-reasoning model (Opus, Codex, GPT-5) |
| `/opsx:propose` creates wrong artifacts | project.md is outdated | Update `openspec/project.md` with current tech stack |
| `openspec validate` fails | Structural issues in artifacts | Read error messages carefully; fix the offending file |
| Two changes touch same spec; merge conflict | Parallel changes to same domain | Archive in chronological order. Use `bulk-archive` for automatic resolution |
| Delta specs not applied after archive | Validation failed silently | Always validate before archiving (`--strict`) |
| Config not taking effect | Wrong filename or YAML | Ensure `config.yaml` (not `.yml`). Validate YAML syntax |
| Node.js version too old | Pre-v20.19.0 | Upgrade: `nvm install 20 && nvm use 20` |
| AI skips tasks during `/opsx:apply` | Context overload | Tell AI: "Please execute tasks in order. Task X is not finished." |
| Custom schema fails | schema.yaml syntax error | Run schema validation. Check for circular dependencies in `requires` |

---

## 17. OpenSpec vs Alternatives

| Feature | OpenSpec | Spec Kit (GitHub) | Kiro (AWS) | No Specs (Vibe Coding) |
|---|---|---|---|---|
| **Philosophy** | Fluid, iterative | Structured, phase-gated | IDE-locked | Ad-hoc |
| **Setup** | `npm install` + `openspec init` | Python setup + configuration | Must use their IDE | None |
| **Brownfield** | First-class support | Possible but ceremony-heavy | Limited | Unpredictable |
| **Spec Format** | Markdown deltas (ADDED/MODIFIED/REMOVED) | Full spec documents | Visual spec builder | None |
| **Tool Support** | 20+ AI assistants | Cursor, Copilot, Claude | AWS IDE only | Any |
| **Auditability** | Per-change folders + archive | Constitution + feature specs | Cloud-hosted | None |
| **Lock-in** | None (MIT, Markdown files) | None (MIT) | High (AWS IDE) | None |
| **Learning Curve** | Low (3 commands) | Medium (phase gates) | Low (visual UI) | None |
| **Best For** | Iterative changes, brownfield | Large teams, strict process | AWS ecosystem | Quick prototypes |

### When to Choose OpenSpec

- You have an **existing codebase** (brownfield) and need incremental spec adoption
- You want **lightweight process** — no phase gates, no ceremonies
- You use **any AI coding tool** — no lock-in
- You care about **auditability** — every change has a proposal + spec delta preserved in Git

### When to Choose Spec Kit

- You're doing **greenfield development** and want a full system spec from scratch
- Your team needs **strict phase gates** and formal approval workflows
- You want **constitution-driven development** with explicit principles

---

## 18. Cheat Sheet

### Quick Start (2 minutes)

```bash
npm install -g @fission-ai/openspec@latest
cd your-project
openspec init
# Edit openspec/project.md with your tech stack
```

### The Three Essential Commands

```
/opsx:propose <name>    # Plan: create proposal + specs + design + tasks
/opsx:apply             # Build: implement the tasks
/opsx:archive           # Ship: merge specs, archive change
```

### Optional but Powerful

```
/opsx:explore <topic>   # Understand before you commit
/opsx:verify            # Validate implementation against specs
/opsx:bulk-archive      # Archive multiple changes
```

### CLI Essentials

```bash
openspec list                  # what's active?
openspec list --specs          # what specs exist?
openspec validate --all        # everything clean?
openspec status --change <id>  # progress on a change?
```

### Directory Map

```
openspec/
├── project.md          ← you maintain (tech stack, conventions)
├── config.yaml         ← you maintain (rules, context injection)
├── specs/              ← SOURCE OF TRUTH (auto-managed via archive)
├── changes/            ← ACTIVE WORK (created by /opsx:propose)
└── changes/archive/    ← AUDIT TRAIL (moved by /opsx:archive)
```

### Spec Format in One Glance

```
## ADDED Requirements       → New behavior
## MODIFIED Requirements    → Changed behavior
## REMOVED Requirements     → Deprecated behavior

### Requirement: <Name>
#### Scenario: <Name>
- GIVEN ...
- WHEN ...
- THEN ...
```

---

## Sources

- [OpenSpec GitHub (Fission-AI/OpenSpec)](https://github.com/Fission-AI/OpenSpec) — 55k+ stars
- [OpenSpec Official Docs](https://openspec.dev/)
- [OpenSpec Docs (thedocs.io)](https://thedocs.io/openspec)
- [OpenSpec npm package](https://www.npmjs.com/package/@fission-ai/openspec)
- [OPSX Workflow Documentation](https://lzw.me/docs/openspec/en/opsx.html)
- [SparkFabrik Playbook — OpenSpec Reference](https://playbook.sparkfabrik.com/ai-development/openspec-reference)
- [OpenSpec Deep Dive (azanello.com)](https://azanello.com/blog/openspec-deep-dive)
- [Dan Clarke's OpenSpec Overview](https://www.danclarke.com/openspec)
- [Redreamality OpenSpec Architecture Guide](https://redreamality.com/garden/notes/openspec-guide/)
- [OpenSpec Cheatsheet (rushis.com)](https://www.rushis.com/openspec-cheatsheet)
- [QubitTool OpenSpec Tutorial](https://qubittool.com/blog/openspec-sdd-tutorial)
- [Spec-Driven.com — OpenSpec Analysis](https://specdriven.com/landscape/openspec)

---

*Tutorial created: June 15, 2026. OpenSpec is actively developed — check https://github.com/Fission-AI/OpenSpec for the latest.*
