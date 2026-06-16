# BMAD Method Tutorial: The Complete Guide to AI-Driven Agile Development

> **Authoritative references:**
> - GitHub: https://github.com/bmad-code-org/BMAD-METHOD (49k+ stars)
> - Docs: https://docs.bmad-method.org/
> - Full doc snapshot for AI: https://docs.bmad-method.org/llms-full.txt
> - Discord: https://discord.gg/gk8jAdXWmj
> - Written: June 2026 | Tested against: BMAD-METHOD v6-alpha (OPSX-era)

---

## Table of Contents

1. [What is BMAD?](#1-what-is-bmad)
2. [Why BMAD Matters](#2-why-bmad-matters)
3. [Installation & Setup](#3-installation--setup)
4. [Core Concepts & Architecture](#4-core-concepts--architecture)
5. [The BMAD Team: All Agents Explained](#5-the-bmad-team-all-agents-explained)
6. [All Skills (Workflows) — Complete Reference](#6-all-skills-workflows--complete-reference)
7. [The Three Planning Tracks](#7-the-three-planning-tracks)
8. [Phase 1: Analysis (Optional)](#8-phase-1-analysis-optional)
9. [Phase 2: Planning (Required)](#9-phase-2-planning-required)
10. [Phase 3: Solutioning (BMad Method / Enterprise)](#10-phase-3-solutioning-bmad-method--enterprise)
11. [Phase 4: Implementation — The Build Cycle](#11-phase-4-implementation--the-build-cycle)
12. [Greenfield Projects (0→1) — Complete Walkthrough](#12-greenfield-projects-01--complete-walkthrough)
13. [Brownfield Projects (1→n) — Complete Walkthrough](#13-brownfield-projects-1n--complete-walkthrough)
14. [Practical Example 1: Build a SaaS App (Greenfield)](#14-practical-example-1-build-a-saas-app-greenfield)
15. [Practical Example 2: Evolve the SaaS App (Brownfield — Add Features + Deprecate)](#15-practical-example-2-evolve-the-saas-app-brownfield--add-features--deprecate)
16. [Quick Dev: The Fast Lane](#16-quick-dev-the-fast-lane)
17. [Party Mode: Your Whole AI Team in One Room](#17-party-mode-your-whole-ai-team-in-one-room)
18. [Correct Course: Mid-Stream Changes](#18-correct-course-mid-stream-changes)
19. [Forensic Investigation](#19-forensic-investigation)
20. [Project Context & Customization](#20-project-context--customization)
21. [Customizing Agents & Workflows](#21-customizing-agents--workflows)
22. [Directory Structure — Every File & Folder Explained](#22-directory-structure--every-file--folder-explained)
23. [CLI & Commands Reference](#23-cli--commands-reference)
24. [BMAD vs Alternatives](#24-bmad-vs-alternatives)
25. [Best Practices](#25-best-practices)
26. [Troubleshooting](#26-troubleshooting)
27. [Cheat Sheet](#27-cheat-sheet)

---

## 1. What is BMAD?

**BMAD** (Build More Architect Dreams) — officially **Breakthrough Method for Agile AI-Driven Development** — is an open-source (MIT), universal framework for orchestrating specialized AI agents through structured development workflows. It transforms your AI coding assistant from a single "genius intern" into a **full agile team of domain experts**.

### The Core Thesis

> "Traditional AI tools produce average results because they do the thinking for you. BMad agents guide you through structured processes to bring out YOUR best thinking in partnership with the AI."

### What BMAD Is NOT

- **NOT** a code generation tool that writes code for you
- **NOT** a single-prompt-to-app converter
- **NOT** a replacement for your IDE

### What BMAD IS

- A **team of 6+ named AI agents** — each with a specific role (Analyst, PM, Architect, UX Designer, Dev, Technical Writer)
- A **workflow orchestrator** — 34+ guided workflows across 4 phases
- A **context-engineering system** — every agent gets precisely the context it needs, eliminating "context loss"
- A **spec-first methodology** — documentation IS the source of truth; code follows from it

### BMAD's Philosophy

```
Scale-adaptive      → Automatically adjusts methodology depth based on project complexity
Human-in-the-loop   → AI proposes, you decide. Quality gates at every phase.
Documentation-first → Specs persist beyond chat sessions. No context loss.
Agent-as-Code       → Agents are versioned Markdown/YAML artifacts (portable, diffable, reusable)
Fresh chats         → Each workflow runs in its own session — prevents context pollution
```

---

## 2. Why BMAD Matters

### The Problem: Context Loss in AI Development

Every developer using AI for coding has hit the same wall:

1. You describe Feature 1. AI builds it.
2. You describe Feature 2. AI builds it — **but breaks Feature 1**.
3. By Feature 5, the AI has forgotten architecture decisions from Feature 1.
4. Documentation is nonexistent or stale.
5. Codebase consistency degrades with every session.

### The BMAD Solution

BMAD solves this with **four key innovations**:

| Innovation | How It Works | Result |
|---|---|---|
| **Specialized Agents** | Analyst, PM, Architect, Dev, QA — each handles their domain | Expert-level reasoning per phase |
| **Document Sharding** | Complex requirements broken into focused, manageable files | Fits within AI context windows |
| **Story Files as Interface** | Each implementation story carries full context | Dev agent has complete understanding |
| **Spec-First Workflow** | PRD → Architecture → Epics → Stories → Code | Code always aligns with specifications |

### BMAD vs "Vibe Coding"

| Aspect | Vibe Coding | BMAD Method |
|---|---|---|
| **Requirements** | In chat history (lost after session) | In PRD.md (persistent, reviewable) |
| **Architecture** | Ad-hoc, inconsistent | Architecture doc with ADRs |
| **Implementation** | Single AI, context overload | Story-by-story, fresh chat each time |
| **Quality** | "Looks right" | Code review workflow, QA gates |
| **Team Scale** | Solo only | Solo OR team (consistent standards) |

---

## 3. Installation & Setup

### Prerequisites

- **Node.js 20.12+** (required for the installer)
- **Git** (recommended for version control)
- **An AI-powered IDE**: Claude Code, Cursor, Windsurf, Codex, or similar
- **LLM Access**: Claude 3.5 Sonnet, GPT-4o, or better (weaker models lose context)

### Quick Install

```bash
# In your project directory:
npx bmad-method install

# For the newest prerelease (v6-alpha):
npx bmad-method@next install
```

### What the Installer Creates

```
your-project/
├── _bmad/                    # Agents, workflows, tasks, configuration
│   ├── bmm/                  #   BMad Method module
│   │   ├── agents/           #     Agent personas (Markdown)
│   │   ├── workflows/        #     Workflow definitions
│   │   ├── tasks/            #     Task templates
│   │   └── templates/        #     Document templates
│   ├── custom/               #   Your customizations (empty initially)
│   └── config.toml           #   Central configuration
│
├── _bmad-output/             # Where your artifacts are saved (empty initially)
│   ├── planning-artifacts/   #   PRDs, architecture docs
│   │   └── epics/            #   Epic and story files
│   └── implementation-artifacts/ # Sprint tracking, code output
│
└── .claude/
    └── skills/               # AI tool skill files (auto-generated)
        └── bmad-*.md
```

### First Command After Install

```
bmad-help
```

**BMad-Help** is your intelligent guide. It:
- Inspects your project to see what's been done
- Shows your options based on installed modules
- Recommends what to do next
- Answers questions like "I have a SaaS idea, where do I start?"
- Runs automatically at the end of every workflow

```bash
# Examples:
bmad-help
bmad-help I have an idea for a SaaS product, where do I get started?
bmad-help What's the difference between Quick Flow and full BMad Method?
bmad-help I'm stuck on the PRD workflow
```

---

## 4. Core Concepts & Architecture

### The Four Phases

BMAD organizes development into four sequential phases:

```
┌────────────────────────────────────────────────────────────────┐
│  Phase 1: ANALYSIS         │  Phase 2: PLANNING                │
│  ─────────────────         │  ───────────────                  │
│  • Brainstorming           │  • PRD (Product Requirements)     │
│  • Market/domain research  │  • User personas & journeys       │
│  • Product Brief / PRFAQ   │  • UX Design (optional)           │
│  (optional)                │  (required for Method/Enterprise) │
├────────────────────────────┼───────────────────────────────────┤
│  Phase 3: SOLUTIONING      │  Phase 4: IMPLEMENTATION          │
│  ────────────────────      │  ────────────────────────         │
│  • Architecture doc + ADRs │  • Sprint planning                │
│  • Epics & Stories         │  • Story-by-story build cycle     │
│  • Implementation readiness│  • Code review                   │
│  (Method/Enterprise only)  │  • Retrospective                  │
└────────────────────────────────────────────────────────────────┘
```

### Scale-Adaptive Intelligence

BMAD automatically adjusts its approach. You don't choose "enterprise mode" — the agents decide:

| Project Type | What BMAD Does |
|---|---|
| **Bug fix** | Quick Flow: 3 commands, done |
| **Simple feature** | Tech-spec → implementation in 30 minutes |
| **SaaS platform** | Full PRD + Architecture + Epics + Sprints |
| **Enterprise system** | Adds security reviews, compliance checks, DevOps planning |

### Document Sharding

Instead of loading one massive document (which overflows AI context windows), BMAD **shards** complex information:

- PRD is one focused document
- Architecture is separate (loaded only when architecting)
- Stories carry only the context relevant to that story
- `project-context.md` carries global conventions

### Agent-as-Code

Every agent is a versioned Markdown artifact with:
- **Identity**: Name, role, domain expertise
- **Persona**: Communication style, principles, visual cues (emoji prefix)
- **Skills**: Menu of capabilities (workflows the agent can run)
- **Customization surface**: `customize.toml` for team/personal overrides

### Fresh Chats Rule

> **Always start a fresh chat for each workflow.**

This prevents context window pollution. The documentation (PRD, Architecture, Stories) is the bridge between chats — not chat history.

---

## 5. The BMAD Team: All Agents Explained

BMAD ships with **6 named agents**, each anchored to a development phase:

### Agent Roster

| Agent | Phase | Emoji | Role |
|---|---|---|---|
| **Mary** | Analysis | 📊 | Business Analyst |
| **Paige** | Analysis | 📚 | Technical Writer |
| **John** | Planning | 📋 | Product Manager |
| **Sally** | Planning | 🎨 | UX Designer |
| **Winston** | Solutioning | 🏗️ | System Architect |
| **Amelia** | Implementation | 💻 | Senior Engineer |

### Detailed Agent Profiles

#### 📊 Mary — Business Analyst

- **Invoke**: `bmad-agent-analyst` or just "Hey Mary"
- **Phase**: 1 (Analysis)
- **Expertise**: Requirements elicitation, market research, brainstorming, competitive analysis
- **Workflows**: brainstorming, market-research, domain-research, technical-research, product-brief, prfaq
- **Menu Codes**: BP (brainstorming), MR (market research), DR (domain research), TR (technical research), PB (product brief), PF (PRFAQ)
- **Personality**: Systematic, inquisitive, structured. Asks probing questions before jumping to solutions.

#### 📚 Paige — Technical Writer

- **Invoke**: `bmad-agent-technical-writer` or "Hey Paige"
- **Phase**: 1 (Analysis)
- **Expertise**: Project documentation, architecture diagrams (Mermaid), document validation
- **Workflows**: generate-project-context, documentation generation
- **Menu Codes**: GP (generate project context)
- **Personality**: Clear, precise, organized. Enforces documentation standards.

#### 📋 John — Product Manager

- **Invoke**: `bmad-agent-pm` or "Hey John"
- **Phase**: 2 (Planning)
- **Expertise**: PRD creation, user story mapping, epic breakdown, MVP scope
- **Workflows**: prd, create-epics-and-stories, check-implementation-readiness
- **Menu Codes**: PR (PRD), ES (epics & stories), IR (implementation readiness)
- **Personality**: Decisive, scope-conscious, user-focused. Cuts through ambiguity.

#### 🎨 Sally — UX Designer

- **Invoke**: `bmad-agent-ux-designer` or "Hey Sally"
- **Phase**: 2 (Planning)
- **Expertise**: UX specifications, design systems, user flows, accessibility
- **Workflows**: ux (UX design), ux-review
- **Menu Codes**: UX (UX design)
- **Personality**: Empathetic, visual, user-centered. Thinks in journeys and interactions.

#### 🏗️ Winston — System Architect

- **Invoke**: `bmad-agent-architect` or "Hey Winston"
- **Phase**: 3 (Solutioning)
- **Expertise**: System design, ADRs, technology selection, non-functional requirements
- **Workflows**: create-architecture, check-implementation-readiness, generate-project-context
- **Menu Codes**: CA (create architecture), IR (implementation readiness), GP (generate project context)
- **Personality**: Rigorous, principled, trade-off-aware. Documents decisions with rationale.

#### 💻 Amelia — Senior Engineer

- **Invoke**: `bmad-agent-dev` or "Hey Amelia"
- **Phase**: 4 (Implementation)
- **Expertise**: Story execution, code review, sprint planning, forensic investigation, quick-dev
- **Workflows**: sprint-planning, create-story, dev-story, code-review, quick-dev, retrospective, correct-course, investigate
- **Menu Codes**: DS (dev story), QD (quick dev), CR (code review), SP (sprint planning), CS (create story), ER (epic retrospective), IN (investigate)
- **Personality**: Pragmatic, quality-focused, detail-oriented. The workhorse of the team.

### Named Agent Activation

When you invoke a named agent, 8 steps happen automatically:

1. **Resolve agent block** — merge `customize.toml` with team + personal overrides
2. **Execute prepend steps** — any pre-flight behavior configured
3. **Adopt persona** — identity + customized role, communication style, principles
4. **Load persistent facts** — org rules, compliance notes, project-context.md
5. **Load config** — user name, language, artifact paths
6. **Greet** — personalized, in configured language, with emoji prefix
7. **Execute append steps** — post-greet setup
8. **Dispatch or present menu** — if intent maps to menu item, go directly; otherwise show menu

### Intent-Based Dispatch

You don't need to memorize menu codes:

```
Hey Mary, let's brainstorm my SaaS idea
→ Mary skips the menu and starts brainstorming immediately

John, I need a PRD for a task management app
→ John opens the PRD workflow directly

Winston, design the architecture for the PRD we just finished
→ Winston reads the PRD and starts architecture
```

---

## 6. All Skills (Workflows) — Complete Reference

### By Phase

#### Phase 1: Analysis (Optional)

| Workflow | Command | Agent | Purpose | Output Files |
|---|---|---|---|---|
| **Brainstorming** | `bmad-brainstorming` | Mary (Analyst) | Guided ideation with 35+ creative techniques | Brainstorming notes |
| **Market Research** | `bmad-market-research` | Mary (Analyst) | Competitive landscape, market sizing | Research report |
| **Domain Research** | `bmad-domain-research` | Mary (Analyst) | Deep dive into domain concepts | Domain analysis |
| **Technical Research** | `bmad-technical-research` | Mary (Analyst) | Evaluate tech options, feasibility | Tech report |
| **Product Brief** | `bmad-product-brief` | Mary (Analyst) | Foundation document — problem, users, market | `product-brief.md` |
| **PRFAQ** | `bmad-prfaq` | Mary (Analyst) | Working Backwards exercise (Amazon-style) | `prfaq.md` |

#### Phase 2: Planning (Required for Method/Enterprise)

| Workflow | Command | Agent | Purpose | Output Files |
|---|---|---|---|---|
| **PRD** | `bmad-prd` | John (PM) | Create/Update/Validate Product Requirements Doc | `prd.md`, `addendum.md`, `decision-log.md` |
| **UX Design** | `bmad-ux` | Sally (UX) | UX specifications, design system | `ux-design.md` |
| **Create Epics & Stories** | `bmad-create-epics-and-stories` | John (PM) | Break PRD into epics with stories | `epics/*.md` |

#### Phase 3: Solutioning (Method/Enterprise)

| Workflow | Command | Agent | Purpose | Output Files |
|---|---|---|---|---|
| **Create Architecture** | `bmad-create-architecture` | Winston (Architect) | System design with ADRs | `architecture.md` |
| **Generate Project Context** | `bmad-generate-project-context` | Paige (Writer) or Analyst | Rules & conventions for implementation agents | `project-context.md` |
| **Check Implementation Readiness** | `bmad-check-implementation-readiness` | Winston (Architect) | Validate cohesion across all planning docs | Validation report |

#### Phase 4: Implementation

| Workflow | Command | Agent | Purpose | Output Files |
|---|---|---|---|---|
| **Sprint Planning** | `bmad-sprint-planning` | Amelia (Dev) | Initialize sprint tracking | `sprint-status.yaml` |
| **Create Story** | `bmad-create-story` | Amelia (Dev) | Expand epic story into detailed story file | `story-[slug].md` |
| **Dev Story** | `bmad-dev-story` | Amelia (Dev) | Implement a story | Working code + tests |
| **Code Review** | `bmad-code-review` | Amelia (Dev) | Quality validation | Review report |
| **Retrospective** | `bmad-retrospective` | Amelia (Dev) | Lessons learned after epic | Retrospective notes |
| **Correct Course** | `bmad-correct-course` | Amelia (Dev) | Handle mid-sprint scope changes | Updated plan |

#### Cross-Phase / Special

| Workflow | Command | Agent | Purpose | Output Files |
|---|---|---|---|---|
| **BMad Help** ⭐ | `bmad-help` | Any | **Your intelligent guide** — ask anything | Guidance |
| **Quick Dev** | `bmad-quick-dev` | Amelia (Dev) | Unified fast lane: clarify → plan → implement → review | `spec-*.md` + code |
| **Party Mode** | `bmad-party-mode` | Orchestrator | All agents in one conversation | Conversation |
| **Investigate** | `bmad-investigate` | Amelia (Dev) | Forensic debugging with evidence grading | `*investigation.md` |
| **Customize** | `bmad-customize` | Any | Guided authoring of agent overrides | `customize.toml` files |
| **Advanced Elicitation** | `bmad-advanced-elicitation` | Multi-agent | Multi-perspective requirements gathering | Elicitation report |

### The PRD Workflow in Detail

`bmad-prd` is the most important planning workflow. It has three **intents**:

| Intent | Purpose | Use Case |
|---|---|---|
| **Create** | Coached discovery from scratch — names a workspace folder, guides to a complete PRD | New projects, new features |
| **Update** | Point at an existing PRD + change signal. Surfaces conflicts before applying changes | Evolving requirements |
| **Validate** | Critique a finished PRD against a checklist. Produces HTML findings report | Pre-implementation gate |

---

## 7. The Three Planning Tracks

BMAD offers three tracks based on project complexity. You don't choose — BMAD recommends based on what you're building.

| Track | Best For | Stories | Documents | Workflow |
|---|---|---|---|---|
| **Quick Flow** | Bug fixes, simple features, clear scope | 1-15 | Tech-spec only | `bmad-quick-dev` handles all |
| **BMad Method** | Products, platforms, complex features | 10-50+ | PRD + Architecture + UX | Full 4-phase lifecycle |
| **Enterprise** | Compliance, multi-tenant, regulated | 30+ | PRD + Architecture + Security + DevOps | Full lifecycle + compliance gates |

### Quick Flow (Fast Lane)

```
bmad-quick-dev
```

One workflow: clarifies intent → builds spec → implements → reviews. Everything in a single session. No PRD. No Architecture. No Epics.

**Use when:**
- Bug fix: "Fix the login validation bug"
- Small feature: "Add a search box to the dashboard"
- Clear scope: "Add rate limiting to the API"

### BMad Method (Standard Path)

```
Phase 1 (optional) → Phase 2 → Phase 3 → Phase 4
```

Full planning with PRD, Architecture, Epics, and story-by-story implementation.

**Use when:**
- Building a product: "A task management SaaS"
- Complex feature: "Add real-time collaboration"
- Unknown scope: "Redesign the onboarding flow"

### Enterprise (Full Path)

```
Phase 1 → Phase 2 → Phase 3 (+ security reviews) → Phase 4 (+ compliance gates)
```

Everything in BMad Method plus: security architecture, compliance checklists, DevOps planning, risk assessments.

**Use when:**
- Regulated industries (healthcare, finance)
- Multi-tenant SaaS with data isolation
- Compliance requirements (SOC2, HIPAA, GDPR)

---

## 8. Phase 1: Analysis (Optional)

All workflows in this phase are optional. Skip directly to Phase 2 if you have a clear vision.

### Brainstorming

```
Invoke: Mary (bmad-agent-analyst)
Run: bmad-brainstorming
```

Mary uses 35+ creative techniques to explore your idea. She asks probing questions, challenges assumptions, and helps crystallize the concept.

```
You: Hey Mary, let's brainstorm my idea for a goal-tracking app

Mary: 📊 Hi! Let's explore this. Tell me:
      1. Who is this for? (Be specific — age, profession, pain point)
      2. What existing tools have they tried and abandoned?
      3. What does "success" look like for them in 6 months?
```

### Market Research

```
Run: bmad-market-research
```

Analyzes competitive landscape, identifies gaps, sizes the market.

### Product Brief (Recommended)

```
Run: bmad-product-brief
```

A lightweight foundation document. Recommended as the minimum artifact before PRD.

**Output**: `product-brief.md` containing:
- Problem statement
- Target users
- Core value proposition
- Competitive alternatives
- Success metrics

### PRFAQ (Working Backwards)

```
Run: bmad-prfaq
```

Amazon-style "Working Backwards" exercise. Write the press release FIRST — before building anything. Stress-tests your concept by forcing you to articulate what customers would say about the finished product.

---

## 9. Phase 2: Planning (Required)

### PRD Creation

```
Invoke: John (bmad-agent-pm)
Run: bmad-prd → intent: Create
```

**What John does:**
1. Asks clarifying questions about the product
2. Identifies user personas
3. Defines functional requirements (FRs) with acceptance criteria
4. Defines non-functional requirements (NFRs)
5. Establishes MVP scope vs. future
6. Creates decision log for trade-offs

**Output files** (in `_bmad-output/planning-artifacts/`):
- `PRD.md` — The complete Product Requirements Document
- `addendum.md` — Supplementary details, research notes
- `decision-log.md` — All scope decisions and rationale

**Example PRD structure:**
```markdown
# TaskMaster — Product Requirements Document

## Product Overview
TaskMaster is a goal-to-task breakdown app for professionals.

## User Personas
### Persona 1: Busy Professional (Sarah)
- Age 30-40, project manager
- Pain: Too many apps, no unified view
- Goal: See all tasks in one place, prioritized

## Functional Requirements
### FR-001: Goal Creation
Users shall be able to create high-level goals.
Acceptance: Goal appears in goal list within 500ms.

### FR-002: Task Breakdown
Users shall be able to break goals into sub-tasks.
Acceptance: Drag-and-drop nesting, max 3 levels deep.

## Non-Functional Requirements
### NFR-001: Performance
API responses < 200ms at p95 under 10k concurrent users.

## MVP Scope
FR-001, FR-002, FR-003, FR-004
Out: FR-005 (collaboration) → v2
```

### UX Design (Optional)

```
Invoke: Sally (bmad-agent-ux-designer)
Run: bmad-ux
```

Sally creates UX specifications: user flows, wireframes, design system recommendations, accessibility requirements. Runs after PRD because she reads the PRD for requirements context.

### Create Epics and Stories (V6 — After Architecture)

In v6, epics and stories are created **after architecture**, not after PRD. This produces better stories because architecture decisions (database schema, API patterns, tech stack) directly affect how work is broken down.

```
Invoke: John (bmad-agent-pm)
Run: bmad-create-epics-and-stories
```

---

## 10. Phase 3: Solutioning (BMad Method / Enterprise)

### Create Architecture

```
Invoke: Winston (bmad-agent-architect)
Run: bmad-create-architecture
```

**What Winston does:**
1. Reads the PRD (all FRs and NFRs)
2. Designs system architecture with component diagrams (Mermaid)
3. Creates ADRs (Architecture Decision Records) for every significant choice
4. Maps FRs to technical approach
5. Defines API contracts, data models, directory structure
6. Documents standards and conventions

**Output**: `architecture.md` containing:
- System overview diagram
- Technology stack with rationale
- ADRs (database choice, API style, auth, state management, etc.)
- FR-to-technical-approach mapping
- API contracts
- Data models
- Directory structure
- Testing strategy
- Deployment architecture

**Example ADR:**
```markdown
## ADR-001: Database — PostgreSQL

### Context
We need a relational database for structured task data with
hierarchical relationships (goals → tasks → sub-tasks).

### Options Considered
1. PostgreSQL — Relational, mature, great for hierarchical queries
2. MongoDB — Document store, flexible schema
3. SQLite — Embedded, no server needed

### Decision
PostgreSQL 16 via Prisma ORM

### Rationale
- CTE queries for hierarchical task data
- Strong type system for data integrity
- Prisma provides type-safe queries in TypeScript
- Team has PostgreSQL experience

### Consequences
- Requires database instance (not embedded)
- Migration management needed
- Indexing strategy required for performance
```

### Implementation Readiness Check

```
Run: bmad-check-implementation-readiness
```

Winston validates that all planning documents are cohesive:
- Does the architecture cover all FRs?
- Are there conflicting decisions?
- Are NFRs addressed (performance, security, scalability)?
- Is the scope bounded — no "scope creep" from planning phase?

---

## 11. Phase 4: Implementation — The Build Cycle

### Initialize Sprint Tracking

```
Invoke: Amelia (bmad-agent-dev)
Run: bmad-sprint-planning
```

Creates `sprint-status.yaml` — a machine-readable tracker of all epics and stories with status.

### The Build Cycle (Repeat per Story)

```
┌─────────────────────────────────────────────────┐
│                                                 │
│  1. Create Story  ──►  2. Dev Story  ──►        │
│     (bmad-create-story) (bmad-dev-story)         │
│                                                 │
│                    3. Code Review                │
│                    (bmad-code-review)            │
│                                                 │
│  Repeat for each story in the epic              │
│                                                 │
│  After all stories: Retrospective               │
│  (bmad-retrospective)                           │
│                                                 │
└─────────────────────────────────────────────────┘
```

**FRESH CHAT for each step.** This is non-negotiable.

#### Step 1: Create Story

```
Amelia: bmad-create-story
```

Amelia reads the epic and expands one story into a **hyper-detailed story file** containing:
- Story description and acceptance criteria
- Technical context from architecture
- Relevant PRD requirements
- Implementation guidance
- Test scenarios
- Files to create/modify

**Output**: `story-[slug].md` — the "bridge" between planning and implementation.

#### Step 2: Dev Story

```
Amelia: bmad-dev-story
```

Amelia opens the story file and implements it. Because the story file carries ALL context (PRD excerpts, architecture decisions, test scenarios), she doesn't need to re-read the PRD or architecture — context is embedded.

#### Step 3: Code Review

```
Amelia: bmad-code-review
```

Amelia reviews the implemented code:
- Does it match the story's acceptance criteria?
- Does it follow the architecture conventions?
- Are tests comprehensive?
- Any regressions or edge cases missed?

**Output**: Approved or changes requested.

### Epic Retrospective

```
Amelia: bmad-retrospective
```

After all stories in an epic are complete:
- What went well?
- What could be improved?
- Any architecture decisions to revisit?
- Lessons learned for next epic

---

## 12. Greenfield Projects (0→1) — Complete Walkthrough

A greenfield project starts with nothing — no code, no docs, just an idea.

### Step-by-Step Walkthrough

#### 1. Initialize

```bash
mkdir my-saas && cd my-saas
git init
npx bmad-method install
# Select: BMad Method module
```

#### 2. First: BMad-Help

```
bmad-help I want to build a SaaS task management app. Where do I start?
```

BMad-Help detects: fresh project, BMad Method module installed. Recommends Analysis phase.

#### 3. Analysis: Product Brief (Recommended)

```
Hey Mary, let's create a product brief for my task management app
→ Mary activates, runs bmad-product-brief
```

Mary creates `_bmad-output/planning-artifacts/product-brief.md`.

#### 4. Planning: PRD

```
John, create a PRD based on the product brief
→ John activates, runs bmad-prd (Create intent)
```

John produces:
- `_bmad-output/planning-artifacts/PRD.md`
- `_bmad-output/planning-artifacts/addendum.md`
- `_bmad-output/planning-artifacts/decision-log.md`

#### 5. UX Design (if applicable)

```
Hey Sally, design the UX based on the PRD
→ Sally activates, runs bmad-ux
```

Sally produces `_bmad-output/planning-artifacts/ux-design.md`.

#### 6. Solutioning: Architecture

```
Winston, create the architecture from the PRD
→ Winston activates, runs bmad-create-architecture
```

Winston produces `_bmad-output/planning-artifacts/architecture.md`.

#### 7. Epics & Stories (After Architecture in v6)

```
John, break the PRD and architecture into epics and stories
→ John activates, runs bmad-create-epics-and-stories
```

John produces `_bmad-output/planning-artifacts/epics/*.md`.

#### 8. Implementation Readiness

```
Winston, check if we're ready to implement
→ Winston runs bmad-check-implementation-readiness
```

#### 9. Implementation

```
Amelia, let's start sprint planning
→ Amelia activates, runs bmad-sprint-planning

# Then for each story (FRESH CHAT each time):
Amelia: bmad-create-story
Amelia: bmad-dev-story
Amelia: bmad-code-review
```

### Greenfield File Timeline

```
_bmad-output/planning-artifacts/
├── product-brief.md          ← Phase 1: Mary, bmad-product-brief
├── PRD.md                    ← Phase 2: John, bmad-prd
├── addendum.md               ← Phase 2: John, bmad-prd
├── decision-log.md           ← Phase 2: John, bmad-prd
├── ux-design.md              ← Phase 2: Sally, bmad-ux (optional)
├── architecture.md           ← Phase 3: Winston, bmad-create-architecture
└── epics/
    ├── epic-1-auth.md        ← Phase 3: John, bmad-create-epics-and-stories
    ├── epic-2-tasks.md
    └── ...

_bmad-output/implementation-artifacts/
├── sprint-status.yaml        ← Phase 4: Amelia, bmad-sprint-planning
└── stories/
    ├── story-user-registration.md  ← Amelia, bmad-create-story
    └── ...
```

---

## 13. Brownfield Projects (1→n) — Complete Walkthrough

Brownfield = existing codebase, production traffic, established patterns.

### The Key Insight

BMAD works on brownfield projects because it **does not require rewriting your app**. You don't convert existing code into BMAD format. You don't create retrospectives for code you never wrote with BMAD. You start where you are:

1. Install BMAD in your existing repo
2. Set up `project-context.md` with your current conventions
3. Use BMAD for new features going forward

### Step-by-Step Brownfield Walkthrough

#### 1. Install on Existing Repo

```bash
cd my-existing-app
npx bmad-method install
# These folders are NEW. Your existing code is untouched:
#   _bmad/
#   _bmad-output/
```

#### 2. Generate Project Context

This is THE critical step for brownfield. Without it, BMAD agents don't know your conventions.

**Option A: Auto-generate from codebase**

```
Paige: bmad-generate-project-context
→ Paige scans your codebase and discovers existing patterns
→ Creates _bmad-output/project-context.md
```

Paige identifies:
- Technology stack from `package.json`, `tsconfig.json`, etc.
- Directory structure conventions
- API patterns (looks at existing routes)
- Testing patterns (looks at existing tests)
- Code style (from ESLint, Prettier configs)

**Option B: Manual**

Create `_bmad-output/project-context.md` yourself:
```markdown
## Technology Stack & Versions
- Node.js 20.x, TypeScript 5.x, Express 4.x
- PostgreSQL via raw SQL (no ORM)
- Jest for testing
- RESTful API, /api/v1 prefix

## Critical Implementation Rules
- All SQL in /src/db/queries/ (no inline SQL)
- Route handlers in /src/routes/ with co-located validation
- Middleware pattern: auth → validation → handler → response
- Error responses: { error: string, code: string, status: number }
- Tests in /tests/ mirroring /src/ structure
```

#### 3. Explore the Existing System (Optional but Recommended)

```
Hey Mary, I want to understand the authentication system
→ Mary (or Amelia with bmad-investigate) analyzes existing code
→ Returns structured analysis
```

#### 4. Plan a New Feature Using Existing Context

```
John, I need a PRD for adding file uploads to the task system
→ John reads project-context.md and existing codebase patterns
→ Creates PRD with constraints: must use existing API patterns, PostgreSQL, etc.
```

#### 5. Architecture: Respect Existing Patterns

```
Winston, design the architecture for file uploads
→ Winston reads project-context.md + existing architecture
→ Designs within existing constraints:
  - Follows existing route pattern: /api/v1/uploads
  - Uses PostgreSQL (existing) + S3 (new) for storage
  - Follows existing error response format
  - ADR documents why S3 was chosen (fits existing AWS infra)
```

#### 6. Implement Story by Story

Amelia reads each story file (which embeds project-context.md rules) and implements within existing conventions. She doesn't introduce new patterns unless the story explicitly calls for it.

#### 7. After Feature Complete

Update `project-context.md` to reflect any new conventions:
- New dependency added? Document it.
- New pattern emerged? Capture it.
- Run `bmad-generate-project-context` to refresh auto-discovery.

### Brownfield: Adding a Feature to an Existing App

```
# Step 1: Install BMAD
npx bmad-method install

# Step 2: Generate project-context.md
bmad-generate-project-context

# Step 3: Explore the area you'll modify
bmad-investigate "Understand the task creation flow"

# Step 4: Plan the feature
John: bmad-prd (Create intent)
"The app needs file attachments on tasks"

# Step 5: Architecture (within existing constraints)
Winston: bmad-create-architecture
"Design file uploads that fit the existing Express + PostgreSQL stack"

# Step 6: Epics & Stories
John: bmad-create-epics-and-stories

# Step 7: Build (story by story)
Amelia: bmad-sprint-planning
Amelia: bmad-create-story → bmad-dev-story → bmad-code-review (repeat)
```

### Brownfield: Deprecating Old Features

When you need to remove or replace existing functionality:

1. **Explore first**: `bmad-investigate` to understand what the feature touches
2. **Document in PRD**: The PRD's scope section explicitly states what's being deprecated
3. **Architecture documents migration path**: How existing data/users transition
4. **Stories include cleanup tasks**: "Remove old endpoint", "Update docs", "Add deprecation headers"

```
# Example PRD excerpt for deprecating old PUT in favor of PATCH:
## Scope
- IN: PATCH /api/v1/tasks/:id for partial updates
- OUT: PUT /api/v1/tasks/:id (deprecated, sunset in v2)
- Migration: PUT returns 301 + Deprecation header → PATCH
```

---

## 14. Practical Example 1: Build a SaaS App (Greenfield)

Let's build **TaskFlow** — a task management SaaS — from zero.

### Setup

```bash
mkdir taskflow && cd taskflow
git init
npx bmad-method install
# Select: BMad Method
```

### Phase 1: Analysis — Product Brief

```
You: Hey Mary, let's create a product brief for TaskFlow.
     It's a task management app for remote teams.

Mary: 📊 Let's start with the fundamentals.
      Who is the primary user?

You: Remote team leads managing 5-15 people across time zones.

Mary: Got it. What specific pain point does TaskFlow solve that
      Asana, Linear, or Notion don't?

You: Those tools show tasks but not the WHY behind them.
     TaskFlow connects every task to a higher-level goal,
     so teams always know what they're working toward.

Mary: Excellent. And what does success look like in 6 months?

[Conversation continues 10-15 turns]
→ Mary produces product-brief.md
```

### Phase 2: Planning — PRD

```
You: John, create a PRD from the product brief.

John: 📋 Reviewing the product brief...
      TaskFlow — Goal-connected task management for remote teams.
      
      Let me clarify scope:
      1. Is this MVP or v1?
      2. Desktop only or mobile too?
      3. Self-hosted or SaaS?

You: SaaS MVP. Web app only. PostgreSQL backend.

John: Understood. Let me structure the requirements...
[Creates PRD with 12 FRs, 5 NFRs, and clear MVP scope]

Files created:
  _bmad-output/planning-artifacts/PRD.md
  _bmad-output/planning-artifacts/addendum.md
  _bmad-output/planning-artifacts/decision-log.md
```

### Phase 2 (cont): UX Design

```
You: Sally, design the UX for TaskFlow.

Sally: 🎨 Reading the PRD... I see we have goals, tasks, and sub-tasks.
       Let me map the user journey:
       1. Sign up → 2. Create first goal → 3. Break into tasks →
       4. Assign → 5. Track progress
       
[Produces UX spec with user flows, wireframe descriptions,
 design system recommendations]
```

### Phase 3: Solutioning — Architecture

```
You: Winston, create the architecture.

Winston: 🏗️ Reading PRD and UX design...
         Analyzing FRs, NFRs, and user flows.
         
         ADR-001: Next.js (App Router) — SSR for performance,
                  great DX with TypeScript
         ADR-002: PostgreSQL + Prisma — Relational data for goals/tasks
         ADR-003: NextAuth.js — JWT sessions, OAuth providers
         ADR-004: Tailwind CSS — Utility-first, rapid UI
         ADR-005: tRPC — End-to-end type safety from DB to UI
         
         [Writes architecture.md with all ADRs, component diagram,
          API contracts, data models, directory structure]
```

### Phase 3 (cont): Epics & Stories

```
You: John, break it down into epics and stories.
     [Note: in v6, this happens AFTER architecture]

John: 📋 Reading PRD and Architecture...
      
      Epic 1: Authentication (3 stories)
        S1.1: User registration
        S1.2: Login with email/password
        S1.3: OAuth (Google, GitHub)
      
      Epic 2: Goal Management (4 stories)
        S2.1: Create and edit goals
        S2.2: Goal list with filters
        S2.3: Goal detail view
        S2.4: Goal progress tracking
      
      Epic 3: Task Management (5 stories)
        ...
```

### Phase 4: Implementation

```
# Initialize tracking
Amelia: bmad-sprint-planning
→ Creates sprint-status.yaml

# Epic 1, Story 1.1 (FRESH CHAT)
Amelia: bmad-create-story → User Registration story created
Amelia: bmad-dev-story → Implementation done
Amelia: bmad-code-review → Approved

# Epic 1, Story 1.2 (FRESH CHAT)
Amelia: bmad-create-story → Login story created
Amelia: bmad-dev-story → Implementation done
Amelia: bmad-code-review → Approved

... continue through all epics ...

# After Epic 1 complete:
Amelia: bmad-retrospective
→ Lessons: "Auth setup was smooth. Consider rate limiting for v2."
```

---

## 15. Practical Example 2: Evolve the SaaS App (Brownfield — Add Features + Deprecate)

TaskFlow has been live for 3 months. Now we need to:

1. **Add**: Real-time collaboration (WebSocket)
2. **Add**: Teams and workspaces
3. **Deprecate**: Simple task assignments in favor of team-based assignment

### Step 1: Update Project Context

```bash
bmad-generate-project-context
# Paige scans the 3-month-old codebase, finds new patterns:
# - Actually using Redis for caching (not in original arch)
# - Added a notification service
# - Some routes don't follow the original pattern (tech debt)
```

### Step 2: Explore the Current State

```
You: Amelia, investigate the task assignment flow.
     I need to understand how it works before we change it.

Amelia: 💻 Running forensic investigation on task assignment...
        Confirmed: Tasks assigned via user_id FK on tasks table.
        Deduced: Single-user assignment, no team concept.
        Hypothesized: Adding teams requires migration of existing data.
        [Produces investigation.md with evidence grading]
```

### Step 3: Plan the Changes

```
You: John, we need a PRD for v2. Three major changes:
     1. Real-time updates via WebSocket
     2. Teams and workspaces
     3. Deprecate single-user assignment → team-based

John: 📋 Let me scope this carefully.
      [Reads existing PRD, architecture, project-context.md, investigation.md]
      
      PRD v2 created:
      
      ## ADDED: Real-time Collaboration
      FR-020: WebSocket connection for live task updates
      FR-021: Real-time presence indicators
      
      ## ADDED: Teams & Workspaces
      FR-030: Team creation and management
      FR-031: Workspace isolation per team
      
      ## MODIFIED: Task Assignment
      FR-004 (was: Single user assignment)
      → NOW: Team-based assignment with optional individual assignee
      → Migration: Existing tasks retain assignee. New tasks use team.
      
      ## DEPRECATED
      - POST /api/v1/tasks/:id/assign (replaced by team assignment)
      - GET /api/v1/tasks?assignedTo=:userId (replaced by team filter)
      Sunset: v3 (2026-12-31)
```

### Step 4: Architecture for v2

```
You: Winston, design the architecture for the v2 PRD.

Winston: 🏗️ Reading v2 PRD...
         
         ADR-006: Socket.io — Mature WebSocket library with rooms support
         ADR-007: Team-based authorization — RBAC with workspace isolation
         ADR-008: Database migration strategy:
           - New tables: teams, team_members, workspaces
           - Modified: tasks (add team_id FK, nullable for migration)
           - Deprecated column: tasks.assigned_to → kept until v3
         
         Migration path:
           Phase 1: Add team_id column (nullable)
           Phase 2: Backfill existing tasks into default teams
           Phase 3: Make team_id non-nullable
           Phase 4: Remove assigned_to in v3
```

### Step 5: Epics & Stories

```
You: John, break v2 into epics.

John: 📋
  Epic 4: Teams & Workspaces (5 stories)
    S4.1: Create team (DB + API)
    S4.2: Team member management
    S4.3: Workspace isolation middleware
    S4.4: Migrate existing users to default team
    S4.5: Deprecate single-user assignment (add headers, docs)
  
  Epic 5: Real-time Collaboration (4 stories)
    S5.1: WebSocket server setup
    S5.2: Task update broadcast
    S5.3: Presence indicators
    S5.4: Real-time notification integration
```

### Step 6: Implement (Story by Story)

```
# Each story in fresh chat:
Amelia: bmad-create-story  (reads PRD v2, architecture v2, project-context)
Amelia: bmad-dev-story     (implements within existing codebase patterns)
Amelia: bmad-code-review   (validates against all docs)
```

### Step 7: After Epic 4 (Deprecation Complete)

```bash
# Update project-context to reflect new architecture
bmad-generate-project-context

# Archive old docs (optional)
# PRD v2 replaces PRD v1 as source of truth
# architecture.md updated with ADRs 6-8
```

**Key brownfield insight**: The deprecation is gradual:
1. New feature (teams) is added
2. Old feature (single assignment) is deprecated with headers
3. Migration path is documented
4. Old feature is removed in a future version — each phase is its own epic/story

---

## 16. Quick Dev: The Fast Lane

`bmad-quick-dev` is BMAD's answer to "I just need to fix this bug / add this small feature." It's NOT for building a SaaS from scratch — that's what the full BMad Method track is for.

### What Quick Dev Does

```
bmad-quick-dev
```

A single workflow that:
1. **Clarifies intent** — Compresses your request into one coherent goal
2. **Routes to smallest safe path** — Simple changes go straight to code; complex ones get a spec
3. **Runs with less supervision** — Model works autonomously between human checkpoints
4. **Diagnoses failures** — If the implementation is wrong, diagnoses whether the problem was intent, spec, or code

### Quick Dev Architecture

```
Human intent
    │
    ▼
Intent clarification ──► Is this truly simple?
    │                        │
    │ Yes                    │ No (needs planning)
    ▼                        ▼
Direct implementation    Create spec first
    │                        │
    ▼                        ▼
Review ──────────────────────┘
```

### When to Use Quick Dev

| Use Quick Dev For | Use Full BMad Method For |
|---|---|
| Bug fixes | New products |
| Small features (1-3 files) | Complex features (10+ files) |
| Clear, well-understood scope | Unknown scope, need discovery |
| "Add search box" | "Redesign onboarding flow" |
| "Fix login validation" | "Add real-time collaboration" |
| "Update API rate limit" | "Build a notification system" |

### Quick Dev Examples

```
# Bug fix:
bmad-quick-dev
> Fix the login validation bug that allows empty passwords

# GitHub issue:
bmad-quick-dev
> fix https://github.com/org/repo/issues/42

# Pre-written intent:
bmad-quick-dev
> implement the intent in _bmad-output/implementation-artifacts/my-intent.md

# Brownfield specific:
bmad-quick-dev
> Add rate limiting to the /api/v1/tasks endpoint.
> Must follow existing middleware pattern in src/middleware/.
> 100 req/min per IP, 429 response for excess.
```

### How Quick Dev Handles Brownfield

Quick Dev respects `project-context.md` if it exists. For brownfield, always:
1. Have `project-context.md` set up (generated or manual)
2. Reference specific files/paths in your intent
3. Specify constraints: "use the existing error response format"

---

## 17. Party Mode: Your Whole AI Team in One Room

`bmad-party-mode` brings all your installed agents into a single conversation. They respond in character — agreeing, disagreeing, building on each other's ideas.

### How It Works

```
You: bmad-party-mode

[BMad-Master orchestrates]:
📊 Mary (Analyst) — Present
📋 John (PM) — Present
🏗️ Winston (Architect) — Present
💻 Amelia (Dev) — Present
🎨 Sally (UX Designer) — Present

All agents are here. What shall we discuss?
```

The orchestrator picks relevant agents per message. If you ask about architecture, Mary might stay quiet while Winston, Amelia, and John debate.

### Party Mode Examples

**Post-Mortem:**
```
You: Our auth service went down three times last sprint.
     What happened?

🏗️ Winston: The architecture was sound — JWT with refresh tokens.
             If implementation deviated...

💻 Amelia: I followed the architecture. But the spec didn't account
           for session invalidation during token refresh races.

📋 John: Both of you raise valid points. The PRD should have specified
         concurrent session handling. This is a requirements gap.
```

**Technical Decision:**
```
You: Monolith or microservices for v1?

🏗️ Winston: Monolith. Microservices add complexity you don't need
             before 10k users.

📋 John: Agreed. Time to market matters more than theoretical scale.

💻 Amelia: Monolith with clear module boundaries. Extract services
           later if needed. I've done this pattern before.
```

**Creative Brainstorming:**
```
You: How do we make onboarding feel magical?

🎨 Sally: Progressive disclosure — features unfold as users need them.
          No tutorial, just natural discovery.

📊 Mary: Data shows users who complete 3 tasks in the first session
         retain at 80%. Onboarding should drive to that milestone.

💻 Amelia: What if the first interaction is creating a REAL task,
           not a dummy? They learn by doing something valuable immediately.
```

### When to Use Party Mode

- High-stakes architecture decisions with trade-offs
- Post-mortems after incidents
- Sprint retrospectives
- Creative brainstorming
- Cross-cutting decisions affecting multiple domains

---

## 18. Correct Course: Mid-Stream Changes

`bmad-correct-course` handles scope changes during implementation. Things change — BMAD adapts.

### When You Need It

- Stakeholder adds a requirement mid-sprint
- Discovered a technical constraint that changes scope
- A story turned out much larger than estimated
- Need to re-prioritize remaining work

### How It Works

```
Amelia: bmad-correct-course

Amelia: 💻 I see we're mid-sprint. What's changed?

You: We need to add email notifications to the task assignment story.
     The PM says it's critical for launch.

Amelia: Let me assess the impact...
        Story S4.2 (Team member management) is 60% complete.
        Adding email notifications affects:
        - S4.2: Needs notification integration
        - S4.3: No impact
        - Sprint timeline: +2 stories estimated
        
        Options:
        1. Add notifications to S4.2 (delays epic by 2 days)
        2. Spin off S4.2-notifications as new story (no delay to current)
        3. Defer to v2 (no impact)
        
        Recommend: Option 2 — keep current story scope, add new story.
```

### Correct Course Flow

1. Amelia reads `sprint-status.yaml` — what's done, what's in progress
2. You describe the change
3. Amelia assesses impact across all remaining stories
4. Amelia presents options with trade-offs
5. You choose
6. Amelia updates `sprint-status.yaml` and affected story files

---

## 19. Forensic Investigation

`bmad-investigate` is Amelia's debugging methodology. It's a disciplined, evidence-based approach — not "let me look at the code and guess."

### The Investigation Discipline

| Principle | What It Means |
|---|---|
| **Evidence Grading** | Every finding is Confirmed (cited), Deduced (reasoned), or Hypothesized (unconfirmed) |
| **Stronghold First** | Start from ONE confirmed fact and expand outward — not from a theory |
| **Hypothesis Discipline** | Never delete hypotheses. Mark as Confirmed or Refuted with evidence |
| **Challenge the Premise** | The user's description is a hypothesis, not a fact. Verify independently |
| **Calibrated Walk** | One procedure for both defect-chasing AND area-exploration |

### Evidence Grades

```
Confirmed:   Directly observed in logs, code, or dumps.
             Cited with path:line, log timestamp, commit hash.

Deduced:     Logically follows from confirmed evidence.
             Reasoning chain is shown.

Hypothesized: Plausible but unconfirmed.
              States what evidence would confirm/refute.
```

### Investigation Output

```
_bmad-output/implementation-artifacts/investigations/
└── auth-session-race-condition-investigation.md

Sections:
  • Confirmed Findings (with citations)
  • Deductions (with chains)
  • Hypotheses (all, with Status and Resolution)
  • Timeline reconstruction
  • Data gaps
  • Reproduction plan
  • Investigation backlog
```

### When to Use

- Bug with unclear root cause
- Before modifying a complex subsystem you don't understand
- Production incident post-mortem
- Brownfield: understanding existing code before changing it

---

## 20. Project Context & Customization

### project-context.md

The `project-context.md` file is the implementation rulebook. Every dev workflow (dev-story, quick-dev, code-review, create-story) reads it.

**Location**: `_bmad-output/project-context.md` (or anywhere in project root)

**What goes in it:**
```markdown
## Technology Stack & Versions
- Node.js 20.x, TypeScript 5.x, Next.js 14
- PostgreSQL 16 via Prisma, Redis 7
- Testing: Vitest + Playwright + MSW
- Styling: Tailwind CSS

## Critical Implementation Rules
- All API routes in /src/app/api/ follow Next.js App Router pattern
- Database queries use Prisma in /src/lib/db/ (no raw SQL)
- Auth via NextAuth.js middleware — never handle sessions manually
- Error format: { error: string, code: string } from /src/lib/errors.ts
- All async operations use try/catch with handleError() wrapper
- Feature flags via /src/lib/flags.ts — never hardcode feature gates
```

**When to create:**
- New project, before architecture: document your preferences
- New project, after architecture: capture architecture decisions
- Existing project: discover conventions from codebase

**Three ways to create:**
1. **Manual**: Create `_bmad-output/project-context.md` yourself
2. **Generate**: `bmad-generate-project-context` (Paige or Analyst scans codebase)
3. **After architecture**: Winston can generate it from architecture decisions

### Central Configuration

`_bmad/config.toml` holds cross-cutting config:
```toml
[core]
user_name = "Your Name"
communication_language = "English"
output_language = "English"

[modules.bmm]
planning_track = "bmad-method"  # or "quick-flow", "enterprise"
```

Override with `_bmad/custom/config.toml` (team, committed) and `_bmad/custom/config.user.toml` (personal, gitignored).

---

## 21. Customizing Agents & Workflows

### Three-Layer Override Model

```
Priority 1 (wins): _bmad/custom/{skill-name}.user.toml  (personal, gitignored)
Priority 2:        _bmad/custom/{skill-name}.toml        (team, committed)
Priority 3 (last): skill's own customize.toml             (defaults)
```

### What You Can Customize

Every agent/workflow ships with a `customize.toml` file exposing its customization surface. You can change:

- **Persona**: Role description, communication style, principles
- **Persistent facts**: Org rules, compliance notes, loaded files
- **Menu items**: Add custom capabilities
- **Pre/Post hooks**: Prepend/append steps (e.g., run a script before dev-story)
- **MCP integrations**: Add tools the agent should have access to

### Example: Make Amelia Always Use Linear for Stories

**`_bmad/custom/bmad-agent-dev.toml`** (team override):
```toml
[persistent_facts]
"Always check Linear (linear.app) for story details when the local epic 
doesn't have a story file. Fall back to local epics only when Linear is unavailable."

[principles]
"Prefer existing patterns over introducing new ones."
"When in doubt, read project-context.md before implementing."
```

Now every dev workflow Amelia runs inherits this behavior.

### Using bmad-customize (Guided)

```
bmad-customize
→ Scans what's customizable
→ Asks: "Which agent or workflow do you want to customize?"
→ Asks: "What do you want to change?"
→ Writes the override file
→ Verifies the merge
```

---

## 22. Directory Structure — Every File & Folder Explained

```
your-project/
│
├── _bmad/                                # BMAD configuration (managed by installer)
│   ├── bmm/                              #   BMad Method module
│   │   ├── agents/                       #     Agent persona definitions (Markdown)
│   │   │   ├── bmad-agent-analyst.md     #       Mary — Business Analyst
│   │   │   ├── bmad-agent-pm.md          #       John — Product Manager
│   │   │   ├── bmad-agent-architect.md   #       Winston — System Architect
│   │   │   ├── bmad-agent-dev.md         #       Amelia — Senior Engineer
│   │   │   ├── bmad-agent-ux-designer.md #       Sally — UX Designer
│   │   │   └── bmad-agent-tech-writer.md #       Paige — Technical Writer
│   │   ├── workflows/                    #     Workflow definitions
│   │   │   ├── bmad-brainstorming/       #       Brainstorming workflow + template
│   │   │   ├── bmad-prd/                 #       PRD workflow + template
│   │   │   ├── bmad-create-architecture/ #       Architecture workflow + template
│   │   │   ├── bmad-dev-story/           #       Dev story workflow + template
│   │   │   ├── bmad-code-review/         #       Code review workflow + template
│   │   │   ├── bmad-quick-dev/           #       Quick Dev workflow + template
│   │   │   └── ... (34+ total)
│   │   ├── tasks/                        #     Reusable task templates
│   │   └── templates/                    #     Document templates (PRD, arch, stories)
│   │
│   ├── custom/                           #   YOUR overrides (empty initially)
│   │   ├── bmad-agent-dev.toml           #     Team override for Amelia
│   │   ├── bmad-agent-dev.user.toml      #     Personal override (gitignored)
│   │   ├── config.toml                   #     Team central config override
│   │   └── config.user.toml              #     Personal central config (gitignored)
│   │
│   ├── config.toml                       #   Central config (installer-managed)
│   └── config.user.toml                  #   Personal central config (installer-managed)
│
├── _bmad-output/                         # YOUR artifacts (you own these)
│   ├── planning-artifacts/
│   │   ├── product-brief.md              #   Phase 1: Analysis output
│   │   ├── PRD.md                        #   Phase 2: Requirements
│   │   ├── addendum.md                   #   Phase 2: Supplementary details
│   │   ├── decision-log.md               #   Phase 2: Scope decisions
│   │   ├── ux-design.md                  #   Phase 2: UX specifications (optional)
│   │   ├── architecture.md               #   Phase 3: System design + ADRs
│   │   └── epics/
│   │       ├── epic-1-auth.md            #   Phase 3: Epic with stories
│   │       ├── epic-2-tasks.md
│   │       └── ...
│   │
│   ├── implementation-artifacts/
│   │   ├── sprint-status.yaml            #   Phase 4: Epic/story tracking
│   │   ├── stories/
│   │   │   ├── story-user-registration.md   #   Phase 4: Detached story file
│   │   │   └── ...
│   │   ├── investigations/
│   │   │   └── auth-race-condition-investigation.md
│   │   └── spec-*.md                     #   Quick Dev output
│   │
│   └── project-context.md                #   Global conventions for all agents
│
└── .claude/
    └── skills/                           # AI tool integration (auto-generated)
        ├── bmad-help.md                  #   BMad-Help skill
        ├── bmad-agent-pm.md              #   John's skill
        ├── bmad-prd.md                   #   PRD workflow skill
        └── ... (all agents + workflows)
```

### File Ownership

| Directory | Owner | Edit? |
|---|---|---|
| `_bmad/bmm/` | Installer | **NO** — overwritten on `npx bmad-method install` |
| `_bmad/custom/` | You (team) | **YES** — survives updates |
| `_bmad/config.toml` | Installer | **NO** — overwritten |
| `_bmad/config.user.toml` | Installer | **NO** — overwritten |
| `_bmad/custom/config.toml` | You (team) | **YES** |
| `_bmad/custom/config.user.toml` | You (personal) | **YES** (gitignored) |
| `_bmad-output/` | You | **YES** — your artifacts |
| `.claude/skills/` | Auto-generated | **NO** — regenerated on `npx bmad-method install` |

---

## 23. CLI & Commands Reference

### Installation Commands

```bash
npx bmad-method install              # Standard install
npx bmad-method@next install         # v6-alpha prerelease
npx bmad-method install --list-tools # Show all supported AI tools
```

### Agent Invocation

```
bmad-help                            # Universal guide (works anywhere)
bmad-agent-analyst                   # Mary — Business Analyst
bmad-agent-pm                        # John — Product Manager
bmad-agent-architect                 # Winston — System Architect
bmad-agent-dev                       # Amelia — Senior Engineer
bmad-agent-ux-designer               # Sally — UX Designer
bmad-agent-technical-writer          # Paige — Technical Writer
```

### Workflow Commands (Alphabetical)

| Command | Phase | What It Does |
|---|---|---|
| `bmad-advanced-elicitation` | Analysis | Multi-perspective requirements elicitation |
| `bmad-brainstorming` | 1 | Guided ideation with 35+ techniques |
| `bmad-check-implementation-readiness` | 3 | Validate plan cohesion before building |
| `bmad-code-review` | 4 | Quality validation of implemented story |
| `bmad-correct-course` | 4 | Handle mid-sprint scope changes |
| `bmad-create-architecture` | 3 | System design with ADRs |
| `bmad-create-epics-and-stories` | 3 | Break PRD into epics and stories |
| `bmad-create-story` | 4 | Expand epic story into detailed story file |
| `bmad-customize` | Any | Guided authoring of agent overrides |
| `bmad-dev-story` | 4 | Implement a story |
| `bmad-domain-research` | 1 | Deep dive into domain concepts |
| `bmad-generate-project-context` | 3 | Auto-generate project-context.md |
| `bmad-help` ⭐ | Any | Intelligent guide — ask anything |
| `bmad-investigate` | 4 | Forensic debugging with evidence grading |
| `bmad-market-research` | 1 | Competitive landscape analysis |
| `bmad-party-mode` | Any | All agents in one conversation |
| `bmad-prd` | 2 | Create/Update/Validate PRD |
| `bmad-prfaq` | 1 | Working Backwards exercise |
| `bmad-product-brief` | 1 | Foundation document (recommended) |
| `bmad-quick-dev` | 4 | Fast lane: clarify → plan → implement → review |
| `bmad-retrospective` | 4 | Lessons learned after epic |
| `bmad-sprint-planning` | 4 | Initialize sprint tracking |
| `bmad-technical-research` | 1 | Evaluate tech options |
| `bmad-ux` | 2 | UX design specifications |

---

## 24. BMAD vs Alternatives

| Feature | BMAD | OpenSpec | Spec Kit | No Framework |
|---|---|---|---|---|
| **Approach** | Multi-agent agile team | Spec-first change management | Constitution + feature specs | Ad-hoc prompts |
| **Agents** | 6 named agents with personas | None (AI tool is the agent) | None | None |
| **Phases** | 4 (Analysis→Planning→Solutioning→Impl) | 3 (Propose→Apply→Archive) | 3 (Constitution→Specify→Plan) | None |
| **Planning Tracks** | 3 (Quick/Method/Enterprise) | 1 (single change size) | 1 | None |
| **Brownfield** | project-context.md, investigate workflow | /opsx:explore, delta specs | Manual baseline | Unreliable |
| **Context Management** | Fresh chat per workflow, document sharding | Spec files in repo as context | Spec files as context | Chat history only |
| **Documentation** | PRD, Architecture, Epics, Stories, ADRs | proposal.md, design.md, tasks.md, spec deltas | Constitution, spec, plan, tasks | None |
| **Team Scale** | Solo to enterprise | Solo to large teams | Teams | Solo |
| **Learning Curve** | Medium (agent model, workflow order) | Low (3 commands) | Medium (phase gates) | None |
| **Installation** | `npx bmad-method install` | `npm install -g @fission-ai/openspec` | Python setup | None |
| **License** | MIT | MIT | MIT | N/A |
| **GitHub Stars** | 49k+ | 55k+ | 18k+ | N/A |

### When to Choose BMAD

- You want a **full agile team** of AI agents with distinct roles
- You need **comprehensive planning** (PRD + Architecture + Stories)
- You value **documentation as source of truth** that persists beyond sessions
- You're building **products** (not just features) — SaaS, platforms, complex apps
- You want **scale-adaptive** methodology (simple bug fix ≠ enterprise feature)
- You need **party mode** for multi-agent collaboration on decisions

### When to Choose OpenSpec Instead

- You want **lightweight spec management** with minimal overhead
- You're doing **iterative changes** on an existing codebase
- You prefer **3 commands** to learn (propose → apply → archive)
- You want spec **deltas** (ADDED/MODIFIED/REMOVED) with audit trails
- You don't need distinct agent personas

### When They Work Together

Some teams use both:
- **BMAD** for greenfield product planning (PRD, Architecture, Stories)
- **OpenSpec** for brownfield changes and spec delta management on the resulting codebase

---

## 25. Best Practices

### Fresh Chats: Non-Negotiable

> **Always start a fresh chat for each workflow.**

Context windows are finite. A chat that ran PRD creation (which loaded 50KB of context) cannot also run dev-story effectively. The documentation IS the bridge between chats.

### Track Selection

| If... | Use... |
|---|---|
| Bug fix, < 5 files | Quick Dev (`bmad-quick-dev`) |
| Small feature, clear scope | Quick Dev |
| New product or major feature | BMad Method (full track) |
| Regulated industry | Enterprise track |

### PRD Quality

- **One PRD per product** (not per feature)
- Use **Create intent** for new, **Update** for changes, **Validate** before implementing
- PRD is the contract between planning and implementation — invest time here

### Architecture Quality

- Every cross-epic decision gets an **ADR**
- ADRs include: Context, Options, Decision, Rationale, Consequences
- Update architecture when decisions change (use `bmad-correct-course`)

### Story Quality

- Stories should be completable in **one AI session**
- Each story file MUST carry enough context to implement without re-reading PRD/architecture
- Include test scenarios in every story

### Brownfield-Specific

- **Always** set up `project-context.md` before implementing
- Use `bmad-investigate` before modifying complex subsystems
- Let BMAD discover your patterns — it prevents breaking them
- Update `project-context.md` when new patterns emerge

### Customization

- Team conventions → `_bmad/custom/{skill-name}.toml` (committed to git)
- Personal preferences → `_bmad/custom/{skill-name}.user.toml` (gitignored)
- Never edit `_bmad/bmm/` — it gets overwritten on updates

---

## 26. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Agents produce generic/inconsistent code | Missing project-context.md | Run `bmad-generate-project-context` or create it manually |
| Dev stories miss architecture context | Architecture created after stories (pre-v6 issue) | In v6, create stories AFTER architecture. Re-run `bmad-create-epics-and-stories` |
| Agent doesn't follow team conventions | No team override file | Use `bmad-customize` or create `_bmad/custom/{skill-name}.toml` |
| Quick Dev produces wrong implementation | Intent wasn't clear enough | Be more specific. Reference files, constraints, error formats |
| Two agents make conflicting decisions | Architecture lacks ADRs for that area | Add an ADR. Re-run `bmad-check-implementation-readiness` |
| "npx bmad-method install" fails | Node.js < 20.12 | Upgrade Node: `nvm install 20 && nvm use 20` |
| Agent "forgets" earlier decisions | Didn't use fresh chat | Always fresh chat. The docs ARE the memory |
| Party Mode agents talk over each other | Too many agents for simple question | Ask more focused questions, or use a single agent |
| Custom overrides not taking effect | Wrong file path or TOML syntax | Run `bmad-customize` for guided authoring. Check `_bmad/custom/` paths |
| "No modules installed" error | Ran bmad-help before install | Install first: `npx bmad-method install` |

---

## 27. Cheat Sheet

### Quick Start (5 minutes)

```bash
npx bmad-method install       # Install in your project
bmad-help                     # Ask: "Where do I start?"
```

### The Three Workflow Paths

```
QUICK PATH (bug fix / small feature):
  bmad-quick-dev

METHOD PATH (product / complex feature):
  Phase 1: bmad-product-brief       (Mary — optional)
  Phase 2: bmad-prd                  (John)
           bmad-ux                   (Sally — optional)
  Phase 3: bmad-create-architecture  (Winston)
           bmad-create-epics-and-stories (John)
  Phase 4: bmad-sprint-planning      (Amelia)
           bmad-create-story → bmad-dev-story → bmad-code-review (repeat)

ENTERPRISE PATH (regulated / compliance):
  Same as Method + security reviews + compliance gates
```

### Essential Commands

```
bmad-help                        # Your guide — always available
bmad-quick-dev                   # Fast lane for bugs and small features
bmad-prd                         # Create/update/validate PRD
bmad-create-architecture         # System design with ADRs
bmad-create-story                # Expand story from epic
bmad-dev-story                   # Implement a story
bmad-code-review                 # Review implemented code
bmad-sprint-planning             # Initialize sprint tracking
bmad-retrospective               # After epic completion
bmad-correct-course              # Mid-sprint scope changes
bmad-investigate                 # Forensic debugging
bmad-party-mode                  # All agents in one room
bmad-customize                   # Customize agents and workflows
bmad-generate-project-context    # Auto-generate project rules
```

### Agent Quick-Reference

```
📊 Mary    (Analyst)         → bmad-agent-analyst         → BP MR DR TR PB PF
📚 Paige   (Tech Writer)     → bmad-agent-technical-writer → GP
📋 John    (PM)              → bmad-agent-pm               → PR ES IR
🎨 Sally   (UX Designer)     → bmad-agent-ux-designer      → UX
🏗️ Winston (Architect)       → bmad-agent-architect         → CA IR GP
💻 Amelia  (Senior Engineer) → bmad-agent-dev              → DS QD CR SP CS ER IN
```

### Directory Map

```
_bmad/                        ← BMAD internals (don't edit)
_bmad/custom/                 ← YOUR overrides (edit freely)
_bmad-output/
  ├── planning-artifacts/     ← PRD, architecture, epics
  ├── implementation-artifacts/ ← Sprint tracking, stories
  └── project-context.md      ← Rules all agents follow
```

### BMAD in One Sentence

> Install → `bmad-help` → Choose your track → Let your AI team guide you from idea to production, with documentation as the persistent source of truth.

---

## Sources

- [BMAD-METHOD GitHub](https://github.com/bmad-code-org/BMAD-METHOD) — 49k+ stars, MIT license
- [Official BMAD Documentation](https://docs.bmad-method.org/)
- [AI-Optimized Full Docs (llms-full.txt)](https://docs.bmad-method.org/llms-full.txt)
- [BMAD Method Guide (bmadmethodguide.com)](https://bmadmethodguide.com/)
- [BMAD Method + Claude Code (Hammad Haqqani)](https://hammadhaqqani.com/blog/bmad-method-claude-code-agile-development)
- [BMAD in Practice (Diego Rodrigo)](https://diegorodrigo.dev/en/2026/04/06/bmad-in-practice-the-complete-ai-agent-development-workflow)
- [BMAD Deep Dive (dev.to — Brian Spann, Parts 1-5)](https://dev.to/bspann/bmad-method-ai-driven-agile-development-that-actually-works-part-1-core-framework-36n1)
- [BMAD Workflows Deep Dive (dev.to, Part 2)](https://dev.to/bspann/bmad-method-workflows-deep-dive-from-idea-to-production-part-2-5od)
- [BMAd Method Guide (redreamality.com)](https://redreamality.com/garden/notes/bmad-method-guide)
- [Spec-Driven AI Development with BMAD (GMO Research)](https://recruit.group.gmo/engineer/jisedai/blog/the-bmad-method-a-framework-for-spec-oriented-ai-driven-development)
- [BMAD at Scale (qwavelabs.io)](https://qwavelabs.io/blog/bmad-method)
- [BMAD 6-Step Workflow (theaistack.dev)](https://www.theaistack.dev/p/bmad)

---

*Tutorial created: June 15, 2026. BMAD Method is actively developed — check https://github.com/bmad-code-org/BMAD-METHOD for the latest.*
