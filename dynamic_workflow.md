# Claude Dynamic Workflows: Complete Tutorial

## Table of Contents

- [1. Introduction](#1-introduction)
- [2. Core Primitives](#2-core-primitives)
  - [2.1 agent()](#21-agent)
  - [2.2 label option](#22-label-option)
  - [2.3 phase()](#23-phase)
  - [2.4 log()](#24-log)
  - [2.5 parallel()](#25-parallel)
  - [2.6 pipeline()](#26-pipeline)
  - [2.7 workflow()](#27-workflow)
  - [2.8 args global](#28-args-global)
  - [2.9 Passing args from CLI and Slash Commands](#29-passing-args-from-cli-and-slash-commands)
- [3. Structured Output](#3-structured-output)
- [4. Resume and Caching](#4-resume-and-caching)
- [5. Advanced Features](#5-advanced-features)
  - [5.1 Worktree Isolation](#51-worktree-isolation)
  - [5.2 Model Overrides](#52-model-overrides)
  - [5.3 Custom Agent Types](#53-custom-agent-types)
  - [5.4 Token Budget Awareness](#54-token-budget-awareness)
  - [5.5 Concurrency Cap](#55-concurrency-cap)
  - [5.7 1000-Agent Total Cap](#57-1000-agent-total-cap)
  - [5.8 workflow() Nesting Limit](#58-workflow-nesting-limit)
  - [5.9 Dynamic Prompt Loading from Files](#59-dynamic-prompt-loading-from-files)
- [6. Control Flow Patterns](#6-control-flow-patterns)
  - [6.1 Loop-Until-Count](#61-loop-until-count)
  - [6.2 Loop-Until-Budget](#62-loop-until-budget)
  - [6.3 Loop-Until-Dry](#63-loop-until-dry)
  - [6.4 pipeline() vs parallel()](#64-pipeline-vs-parallel)
- [7. Quality Patterns](#7-quality-patterns)
  - [7.1 Adversarial Verification](#71-adversarial-verification)
  - [7.2 Perspective-Diverse Verification](#72-perspective-diverse-verification)
  - [7.3 Judge Panel](#73-judge-panel)
  - [7.4 Multi-Modal Sweep](#74-multi-modal-sweep)
  - [7.5 Completeness Critic](#75-completeness-critic)
  - [7.6 No Silent Caps](#76-no-silent-caps)
- [8. The meta Block](#8-the-meta-block)
- [9. Script Sandbox Constraints](#9-script-sandbox-constraints)
- [10. Real-World Examples](#10-real-world-examples)
- [11. Quick Reference](#11-quick-reference)

---

## 1. Introduction

### What are Dynamic Workflows?

Dynamic workflows are a **deterministic multi-agent orchestration** system built into Claude Code. Instead of one agent handling a complex task sequentially, you write a JavaScript script that fans work out across many parallel subagents — then synthesizes their results.

The key word is *deterministic*: unlike asking an agent to "figure it out," your script explicitly controls which agents run, in what order, with what prompts, and how results are combined. The agents are the workers; your script is the foreman.

### When to Use Workflows vs a Single Agent

| Situation | Use |
|-----------|-----|
| Simple question or task | Single agent |
| Task fits in one context window | Single agent |
| Task requires parallel research across many sources | Workflow |
| You need adversarial verification of findings | Workflow |
| Parallel file edits that would conflict | Workflow (with worktree isolation) |
| Scale beyond what one context can hold | Workflow |
| You need reproducible, resumable multi-step work | Workflow |

### How the Orchestration Model Works

```
You write a JS script
       ↓
Workflow tool executes it
       ↓
Script calls agent() → spawns subagents concurrently
       ↓
Subagents run (capped at ~10–16 at once, rest queue)
       ↓
Results flow back to the script
       ↓
Script synthesizes, decides next steps, calls more agents
```

### The /workflows Command

Run `/workflows` in Claude Code to open a live progress tree showing:
- Each named phase as a group
- Every active/completed agent with its label
- Real-time status (running, done, failed)

This lets you watch fan-out happen as your workflow executes.

### Motivating Example

**Without workflows** — sequential, slow:
```javascript
// One agent does everything — no parallelism, single context
const result = await agent("Research topic A, then B, then C, then synthesize")
```

**With a workflow** — parallel, fast:
```javascript
// Three agents run simultaneously
const [a, b, c] = await parallel([
  () => agent("Research topic A", { label: "research:A" }),
  () => agent("Research topic B", { label: "research:B" }),
  () => agent("Research topic C", { label: "research:C" }),
])
const synthesis = await agent(`Synthesize these findings: ${a} ${b} ${c}`)
```

The parallel version completes in the time of the slowest single research agent, not the sum of all three.

---

## 2. Core Primitives

### 2.1 `agent()`

**Signature:** `agent(prompt: string, opts?: AgentOptions): Promise<string | object | null>`

Spawns a single subagent. This is the fundamental building block of every workflow.

**Without `schema`** — returns the agent's final text as a string:
```javascript
const summary = await agent("Summarize the key points of this codebase")
console.log(typeof summary) // "string"
```

**With `schema`** — returns a validated JS object (the agent is forced to call a StructuredOutput tool; it cannot return free text):
```javascript
const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    title: { type: 'string' },
    severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
    file: { type: 'string' },
    line: { type: 'number' }
  },
  required: ['title', 'severity', 'file', 'line']
}

const finding = await agent("Find the most critical bug in auth.ts", {
  schema: FINDING_SCHEMA
})
console.log(finding.severity) // "critical" — typed, no JSON.parse needed
```

**Returns `null`** when the user skips the agent mid-run. Always filter:
```javascript
const results = await parallel([
  () => agent("Task A"),
  () => agent("Task B"),
  () => agent("Task C"),
])
const valid = results.filter(Boolean) // remove any nulls from skipped agents
```

### 2.2 `label` option

The `label` option overrides the display label shown in the `/workflows` progress tree.

Without a label, the tree shows a truncated version of the prompt — often ugly and unhelpful when many agents share the same prompt template.

```javascript
// Bad — all agents show the same truncated prompt
const results = await parallel(files.map(f => () =>
  agent(`Analyze the file ${f} for security issues`)
))

// Good — each agent has a clear, unique label
const results = await parallel(files.map(f => () =>
  agent(`Analyze the file ${f} for security issues`, {
    label: `audit:${f}`  // shows as "audit:src/auth.ts", "audit:src/db.ts", etc.
  })
))
```

Use short, descriptive labels with a colon-separated hierarchy: `"review:security"`, `"verify:claim-3"`, `"migrate:src/api.ts"`.

### 2.3 `phase()`

**Signature:** `phase(title: string): void`

Starts a new named phase. All subsequent `agent()` calls are grouped under this title in the `/workflows` progress tree, until the next `phase()` call.

```javascript
phase('Review')
// These agents appear under the "Review" group
const reviews = await parallel(files.map(f => () =>
  agent(`Review ${f}`, { label: `review:${f}` })
))

phase('Verify')
// These agents appear under the "Verify" group
const verifications = await parallel(reviews.map(r => () =>
  agent(`Verify: ${r}`, { label: `verify:${r}` })
))
```

**Important:** Inside `pipeline()` or `parallel()`, use `opts.phase` on each `agent()` call instead of calling `phase()` at the top level. Calling `phase()` inside concurrent stages causes a race condition where agents from different stages land in the wrong group.

```javascript
// Correct — use opts.phase inside pipeline/parallel
await pipeline(items,
  item => agent(`Stage 1: ${item}`, { label: `s1:${item}`, phase: 'Stage One' }),
  item => agent(`Stage 2: ${item}`, { label: `s2:${item}`, phase: 'Stage Two' })
)
```

### 2.4 `log()`

**Signature:** `log(message: string): void`

Emits a narrator message above the progress tree, visible to the user in real time. Unlike `phase()`, it doesn't create a group — just a timestamped status line.

Use it for meaningful progress updates, especially inside loops:

```javascript
const bugs = []
let iteration = 0
while (bugs.length < 10) {
  iteration++
  log(`Iteration ${iteration}: found ${bugs.length}/10 bugs so far...`)
  const batch = await agent("Find bugs", { schema: BUGS_SCHEMA })
  bugs.push(...batch.bugs)
}
log(`Done — found ${bugs.length} bugs in ${iteration} iterations`)
```

### 2.5 `parallel()`

**Signature:** `parallel(thunks: Array<() => Promise<any>>): Promise<any[]>`

Runs an array of thunk functions concurrently. **This is a BARRIER** — it waits for every thunk to resolve before returning.

```javascript
// All 5 agents start immediately; parallel() returns when the last one finishes
const results = await parallel([
  () => agent("Search angle: background context", { label: "search:background" }),
  () => agent("Search angle: recent news", { label: "search:news" }),
  () => agent("Search angle: technical details", { label: "search:technical" }),
  () => agent("Search angle: criticisms", { label: "search:criticisms" }),
  () => agent("Search angle: expert opinions", { label: "search:experts" }),
])

const valid = results.filter(Boolean)
```

Key behaviors:
- A thunk that throws resolves to `null` — `parallel()` itself never rejects
- Always `.filter(Boolean)` before using results
- Excess thunks queue automatically when the concurrency cap is hit — safe to pass 100 items

**Choose `parallel()` only when you need ALL results together** before the next step. For multi-stage processing, use `pipeline()` instead.

### 2.6 `pipeline()`

**Signature:** `pipeline(items: any[], ...stages: Function[]): Promise<any[]>`

Processes items through multiple stages with **no synchronization barrier** between stages. This is the most important primitive for efficient multi-stage workflows.

```
Item A: [Stage 1 ✓] → [Stage 2 ✓] → [Stage 3 running...]
Item B: [Stage 1 ✓] → [Stage 2 running...]
Item C: [Stage 1 running...]
```

All items progress independently. Wall-clock time = slowest single item chain, NOT sum of slowest-per-stage.

**Stage signature:** `(prevResult, originalItem, index) => Promise<any>`
- `prevResult`: output of the previous stage for this item
- `originalItem`: the original input item (use this for labels in later stages)
- `index`: the position in the items array

```javascript
const files = ['auth.ts', 'db.ts', 'api.ts']

const reports = await pipeline(
  files,
  // Stage 1: analyze each file
  file => agent(`Analyze ${file} for issues`, {
    label: `analyze:${file}`,
    phase: 'Analyze',
    schema: ANALYSIS_SCHEMA
  }),
  // Stage 2: generate report from analysis
  // Use originalItem (the file name) for the label — prevResult is the analysis object
  (analysis, file, index) => agent(
    `Write a report for ${file} based on: ${JSON.stringify(analysis)}`,
    { label: `report:${file}`, phase: 'Report', schema: REPORT_SCHEMA }
  )
)
// reports[0] is the report for auth.ts, etc.
```

A stage that throws drops that item to `null` and skips its remaining stages — the rest continue.

### 2.7 `workflow()`

**Signature:** `workflow(nameOrRef: string | {scriptPath: string}, args?: any): Promise<any>`

Run another registered workflow or a script file as a sub-step inline.

```javascript
// By name (saved/registered workflow)
const qualityReport = await workflow('doc-quality-check', {
  docs: generatedDocs,
  strict: true
})

// By script file path
const result = await workflow({ scriptPath: './scripts/scan.js' }, {
  targetDir: 'src'
})
```

The child workflow:
- Shares your concurrency cap, agent counter, abort signal, and token budget
- Appears as a collapsible `▸ name` group in `/workflows`
- Its agents count toward the shared budget and concurrency cap

**Always wrap in try/catch** — throws on unknown name, unreadable path, or child syntax error:
```javascript
let qualityReport
try {
  qualityReport = await workflow('doc-quality-check', { docs })
} catch (e) {
  log('Warning: doc-quality-check workflow not available, skipping quality gate')
  qualityReport = { passed: docs } // graceful degradation
}
```

### 2.8 `args` global

The `args` global holds whatever value was passed as the Workflow tool's `args` input. Use it to parameterize named or saved workflows.

```javascript
// args might be: { question: "What is...", depth: "thorough" }
const question = args && args.question ? args.question : "What are the main trends in AI?"
const depth = args && args.depth ? args.depth : "standard"

log(`Researching: ${question} at depth: ${depth}`)
```

**Critical:** Pass `args` as actual JSON values, not as a JSON-encoded string.

```javascript
// CORRECT — args is an actual array
Workflow({ script: "...", args: ["src/auth.ts", "src/db.ts"] })

// WRONG — args is a string; args.filter/args.map will throw
Workflow({ script: "...", args: '["src/auth.ts", "src/db.ts"]' })
```

Always validate and default args fields at the top of your script:
```javascript
const files = (args && Array.isArray(args.files)) ? args.files : ['src/index.js']
const style = (args && args.style === 'jsdoc') ? 'jsdoc' : 'markdown'
const outputDir = (args && args.outputDir) ? args.outputDir : 'docs'
```

### 2.9 Passing `args` from CLI and Slash Commands

How `args` reach a workflow depends on how the workflow is invoked.

#### From the Workflow tool (programmatic)

This is the canonical channel — pass `args` directly as a JSON value:

```javascript
// In a conversation or parent workflow
Workflow({ name: 'deep-research', args: { question: 'How does Raft work?', depth: 'thorough' } })
Workflow({ scriptPath: '.claude/workflows/my-script.js', args: { files: ['src/auth.ts'], dryRun: true } })
```

#### From the CLI with `-p` (one-shot)

Describe the args in natural language — Claude interprets them and calls the Workflow tool with the right `args` object:

```bash
claude -p "Run the deep-research workflow. Question: 'How does Raft consensus work?' Use thorough depth."
```

Or more explicitly:

```bash
claude -p "Run the workflow at .claude/workflows/deep-research.js with args {\"question\": \"How does Raft work?\", \"depth\": \"thorough\"}"
```

#### From a slash command (`/workflow-name`)

Workflows saved in `.claude/workflows/` are invokable as slash commands — `graph-workflow-demo.js` becomes `/graph-workflow-demo`. However, **slash commands have no built-in structured args syntax**. Any text after the command name is conversational context that Claude reads and interprets — it is not automatically parsed into `args`.

Practical options, in order of reliability:

**1. Natural language after the command (simplest, slightly fragile)**
```
/graph-workflow-demo with supervisor="planner" and max_iterations=5
```
Claude parses the trailing text and passes structured args. Works for simple cases but depends on Claude interpreting intent correctly.

**2. Sensible defaults in the script (most robust)**

Design the workflow to have working defaults for every arg. Invocation via slash command uses the defaults; programmatic invocation via the Workflow tool overrides them:

```javascript
// args are optional — slash command invocation uses defaults
const supervisor    = (args && args.supervisor)      ? args.supervisor     : 'planner'
const maxIterations = (args && args.max_iterations)  ? args.max_iterations : 5
const outputDir     = (args && args.outputDir)       ? args.outputDir      : 'output/'
```

**3. Wrap in a skill for reliable arg parsing**

Skills (`.claude/skills/`) support `$ARGUMENTS` — the trailing text after the slash command is substituted verbatim. If you need reliable structured input from a slash command, write a skill whose SKILL.md instructs Claude to parse `$ARGUMENTS` and call the Workflow tool with the right `args`:

```
# SKILL.md
Parse the following arguments and run the graph-workflow-demo workflow with them: $ARGUMENTS
```

Then `/graph-workflow-demo planner 5` is reliably parsed before the workflow runs.

#### Summary

| Invocation method | How to pass args |
|-------------------|-----------------|
| `Workflow({ args: {...} })` tool call | Direct JSON — the only fully typed channel |
| `claude -p "..."` CLI | Natural language description; Claude constructs the `args` object |
| `/workflow-name text` slash command | Natural language after the command; Claude interprets it |
| Slash command with reliable parsing | Wrap in a skill that uses `$ARGUMENTS` |

**General rule:** always code your workflow with explicit defaults for every `args` field. This makes slash-command invocation (which passes no structured args) work out of the box, while still allowing programmatic callers to override specific fields.

---

## 3. Structured Output

### Using the `schema` Option

Pass a JSON Schema object as `opts.schema` and the subagent is forced to call a `StructuredOutput` tool. The model cannot return free text — it must produce a valid object matching your schema. If it doesn't match, it retries automatically at the tool-call layer.

`agent()` returns the validated JS object directly — no `JSON.parse`, no string manipulation.

```javascript
const BUGS_SCHEMA = {
  type: 'object',
  properties: {
    bugs: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'number' },
          severity: { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
          description: { type: 'string' }
        },
        required: ['title', 'file', 'line', 'severity', 'description']
      }
    }
  },
  required: ['bugs']
}

const result = await agent("Find all bugs in the authentication module", {
  schema: BUGS_SCHEMA
})

// result is a typed JS object — no parsing needed
result.bugs.forEach(bug => {
  log(`${bug.severity.toUpperCase()}: ${bug.title} in ${bug.file}:${bug.line}`)
})
```

### JSON Schema Essentials for Workflows

```javascript
// Object with required fields
const PERSON_SCHEMA = {
  type: 'object',
  properties: {
    name: { type: 'string' },
    age: { type: 'number' },
    active: { type: 'boolean' }
  },
  required: ['name', 'age']
}

// Array of strings
const TAGS_SCHEMA = {
  type: 'object',
  properties: {
    tags: { type: 'array', items: { type: 'string' } }
  },
  required: ['tags']
}

// Enum constraint
const SEVERITY_SCHEMA = {
  type: 'object',
  properties: {
    level: { type: 'string', enum: ['critical', 'high', 'medium', 'low', 'info'] }
  },
  required: ['level']
}

// Nested objects
const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    finding: {
      type: 'object',
      properties: {
        title: { type: 'string' },
        location: {
          type: 'object',
          properties: {
            file: { type: 'string' },
            line: { type: 'number' }
          },
          required: ['file', 'line']
        }
      },
      required: ['title', 'location']
    }
  },
  required: ['finding']
}
```

**Design advice:** Keep schemas tight. Only include fields you will actually use. Smaller schemas produce fewer retries. Don't add optional fields "just in case."

### The `.filter(Boolean)` Pattern

`agent()` returns `null` when the user skips it mid-run. Always filter before working with results:

```javascript
const results = await parallel(items.map(item => () =>
  agent(`Process ${item}`, { schema: RESULT_SCHEMA })
))

// Without filter — crashes if any agent was skipped
results.forEach(r => log(r.title)) // TypeError if r is null

// With filter — safe
results.filter(Boolean).forEach(r => log(r.title))
```

This also applies to `pipeline()` results — items dropped by a throwing stage appear as `null`.

---

## 4. Resume and Caching

### How It Works

Every `Workflow` tool invocation automatically saves its script to a file under the session directory. The tool result includes the path. Each `agent()` call's result is cached by its `(prompt, opts)` pair.

### The runId

The tool result includes a `runId` (format: `wf_xxxxxxxx`). Keep this — you need it to resume.

### Resuming a Workflow

If a workflow is interrupted (user stops it, it crashes, or you want to iterate on the script):

1. Stop the running task first: `TaskStop({ task_id: "wxxx" })`
2. Resume: `Workflow({ scriptPath: "path/from/result", resumeFromRunId: "wf_xxx" })`

Completed `agent()` calls with **unchanged `(prompt, opts)`** return cached results instantly. Only edited or new agent calls re-run. Same script + same args = 100% cache hit.

```
First run (interrupted at agent 47 of 100):
  agents 1-46: completed ✓ (cached)
  agent 47: interrupted ✗

Resume:
  agents 1-46: instant cache hits ✓ (no API calls)
  agent 47: re-runs from where it left off
  agents 48-100: continue normally
```

### Why Certain Functions Are Banned

The following are unavailable in workflow scripts:
- `Date.now()` — the current timestamp
- `Math.random()` — random numbers
- `new Date()` with no arguments

**Why:** These functions produce different values on every run. If you use them in a prompt string, the prompt changes every time — the cache key never matches, so every resume re-runs everything from scratch, defeating the purpose of caching.

**Workarounds:**
```javascript
// WRONG — prompt changes every run, breaks caching
const result = await agent(`Analyze this at timestamp ${Date.now()}`)

// CORRECT — pass the timestamp via args before the workflow runs
const timestamp = args.runTimestamp || 'unknown'
const result = await agent(`Analyze this — run started at: ${timestamp}`)

// Vary agents by index, not random
const agents = items.map((item, index) =>
  () => agent(`Perspective ${index}: analyze ${item}`, { label: `p${index}:${item}` })
)
```

Stamp results with timestamps **after** the workflow returns — at the call site, not inside the script.

### scriptPath Iteration Pattern

Every Workflow invocation returns the script file path. To iterate:

1. Run your workflow → note the `scriptPath` in the result
2. Edit the script file with the `Edit` tool
3. Re-invoke: `Workflow({ scriptPath: "...", resumeFromRunId: "wf_xxx" })`
4. Unchanged agents return cached results; only your edits re-run

This is much faster than pasting the full script each time.

---

## 5. Advanced Features

### 5.1 Worktree Isolation

**Option:** `isolation: 'worktree'`

Runs the agent in a fresh git worktree — an isolated copy of the repository branched from the base ref (usually `origin/<default-branch>`).

#### How It Works

Each `agent({ isolation: 'worktree' })` call creates an independent git worktree under `.claude/worktrees/`:

```
Main repo (C:\...\project)
  └─ .claude/worktrees/
       ├─ agent-a/   ← isolated copy for agent A
       ├─ agent-b/   ← isolated copy for agent B
       └─ agent-c/   ← isolated copy for agent C
```

Every agent sees a **clean, private** working directory. Crucially: **no agent can see any other agent's worktree.** Each is a fresh branch from the same base ref.

**Cost:** ~200–500ms setup + disk I/O per agent. **Do not use casually.**

**Use ONLY when** multiple agents edit files in parallel and would otherwise clobber each other's changes. The primary use case is parallel code migrations.

**Auto-cleanup:** If the agent makes no changes, the worktree is deleted automatically. If changes were made, the worktree is kept on disk for inspection.

#### Critical Constraint: Worktrees Are Not Shared

A common misconception is that a "merge" agent with `isolation: 'worktree'` can discover and reconcile the changes made by earlier worktree-isolated agents. **This does NOT work:**

```javascript
// ❌ BROKEN — the "merge" agent gets a FRESH worktree from origin/main
// It sees NONE of the changes from agent A or agent B's worktrees

phase('Refactor')
const refactored = await parallel([
  () => agent('Refactor the auth module', { isolation: 'worktree', schema: CHANGES_SCHEMA }),
  () => agent('Refactor the payment module', { isolation: 'worktree', schema: CHANGES_SCHEMA }),
])

phase('Merge')
// WRONG: this agent runs in worktree-C — a fresh copy of origin/main
// It sees zero refactored changes from A or B
await agent('Reconcile all refactored modules', { isolation: 'worktree' })
```

```
Refactor agent A  →  worktree-A/  (edits auth module) ← seen only by A
Refactor agent B  →  worktree-B/  (edits payment module) ← seen only by B
Merge agent       →  worktree-C/  (FRESH copy of origin/main — sees NEITHER A nor B)
```

**The Merge agent deterministically skips ALL of them** — it's not a race condition or occasional bug; it's the architectural guarantee of isolation.

#### The Correct Pattern: Structured Output as the Bridge

Since file-system side effects don't cross worktree boundaries, the **only** way to pass results between agents is through their return values. Use the `schema` option so each refactor agent returns its changes as structured data. The merge agent then runs **without** isolation and applies all collected changes:

```javascript
export const meta = {
  name: 'parallel-refactor-with-merge',
  description: 'Refactor components in parallel, then merge deterministically',
  phases: [{ title: 'Refactor' }, { title: 'Merge' }],
}

const CHANGE_SCHEMA = {
  type: 'object',
  properties: {
    files: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          path: { type: 'string' },
          content: { type: 'string' },
          summary: { type: 'string' }
        },
        required: ['path', 'content', 'summary']
      }
    }
  },
  required: ['files']
}

phase('Refactor')
// Each agent returns its changes as structured data
const results = await parallel([
  () => agent('Refactor the auth module — return changed files with full content', {
    isolation: 'worktree',
    schema: CHANGE_SCHEMA,
    label: 'refactor:auth'
  }),
  () => agent('Refactor the payment module — return changed files with full content', {
    isolation: 'worktree',
    schema: CHANGE_SCHEMA,
    label: 'refactor:payment'
  }),
])

// results is a deterministic, index-stable array: [authChanges, paymentChanges]
// null fills any slot where an agent errored or was skipped
const allFiles = results.filter(Boolean).flatMap(r => r.files)
// Every file from every agent is accounted for. Nothing is silently skipped.

phase('Merge')
// Merge agent runs WITHOUT worktree isolation — it works in the real repo
// and applies all collected changes
await agent(
  `Apply these refactored files to the codebase, resolving any conflicts:
   ${JSON.stringify(allFiles, null, 2)}`,
  { label: 'merge:all-refactors' }
)
```

#### Deterministic Collection Guarantees

When collecting results from `parallel()` or `pipeline()`, the return arrays are **positionally indexed** and deterministic:

| Mechanism | Guarantee |
|-----------|-----------|
| `parallel([thunkA, thunkB, ...])` | Returns array where slot `i` maps to input thunk `i`. If thunk errors, slot `i` is `null` — you see the gap explicitly. |
| `pipeline(items, stages...)` | Same ordering. A stage that throws produces `null` for that item's remaining stages — visible, not silent. |
| File-system side effects between agents | **No agent sees another's worktree.** You MUST pass data through return values. |

With hundreds of refactor agents, `parallel()` returns an array of exactly N results — no silent drops. If agent #47 errors, slot 47 is `null`, and you know exactly which one failed.

#### Summary of Rules

1. **Worktree isolation = per-agent sandbox**, not a merge primitive. Agents share NO filesystem state.
2. **Structured output (`schema`)** is the deterministic bridge between worktree-isolated agents.
3. **No silent skipping** — `parallel()`/`pipeline()` return arrays are index-stable; gaps are explicit `null`s.
4. **Merge agents should NOT use `isolation: 'worktree'`** — run them in the main repo so they can apply collected changes.
5. **Skip worktree isolation entirely for read-only agents** — the overhead buys you nothing.

### 5.2 Model Overrides

**Option:** `model: 'haiku' | 'sonnet' | 'opus'`

Override the model for a specific agent. Default: the agent inherits the main-loop model.

```javascript
// Use haiku for high-volume simple tasks (much cheaper)
const extractions = await parallel(snippets.map(s => () =>
  agent(`Extract the function names from: ${s}`, {
    label: `extract:${s.slice(0, 20)}`,
    model: 'haiku',
    schema: NAMES_SCHEMA
  })
))

// Use opus for the final high-stakes synthesis
const report = await agent("Synthesize all findings into an executive report", {
  label: 'final-synthesis',
  model: 'opus'
})
```

**Per-phase override** in the `meta` block:
```javascript
export const meta = {
  name: 'my-workflow',
  description: 'Example with phase-level model override',
  phases: [
    { title: 'Extract', model: 'haiku' },   // all agents in Extract use haiku
    { title: 'Synthesize', model: 'opus' },  // all agents in Synthesize use opus
  ],
}
```

Only override when you're confident a different tier fits. Omit the option and inherit by default.

### 5.3 Custom Agent Types

**Option:** `agentType: string`

Uses a specialized subagent type instead of the default workflow subagent.

```javascript
// Explore agent — read-only code search, fast and safe
const analysis = await agent(
  `Find all usages of the deprecated API in src/`,
  {
    label: 'find:deprecated-api',
    agentType: 'Explore',
    schema: USAGES_SCHEMA
  }
)
```

Available types:

| agentType | Tools |
|---|---|
| `claude` (default) | Everything |
| `Explore` | Glob, Grep, Read, WebFetch, WebSearch — no writes |
| `general-purpose` | Everything |
| `Plan` | Everything except Agent, ExitPlanMode, Edit, Write |
| `code-reviewer` | Everything (code review specialist system prompt) |

The `agentType` composes with `schema` — the custom agent's system prompt gets a StructuredOutput instruction appended automatically.

### 5.4 Token Budget Awareness

The `budget` global is available in every workflow script.

| Property/Method | Description |
|----------------|-------------|
| `budget.total` | The user's `+Nk` token target, or `null` if none set |
| `budget.spent()` | Output tokens spent this turn (shared across main loop + all workflows) |
| `budget.remaining()` | `max(0, total - spent())`, or `Infinity` if no target |

```javascript
// Static scaling — fleet size based on budget
const FLEET_SIZE = budget.total ? Math.floor(budget.total / 100_000) : 5

// Dynamic loop — keep working while budget allows
while (budget.total && budget.remaining() > 50_000) {
  log(`Budget remaining: ${Math.round(budget.remaining() / 1000)}k tokens`)
  const batch = await agent("Find more issues", { schema: ISSUES_SCHEMA })
  allIssues.push(...batch.issues)
  if (batch.issues.length === 0) break
}

// Conditional depth
if (budget.total && budget.remaining() > 200_000) {
  log("Budget sufficient — running deep verification")
  await runDeepVerification(findings)
} else {
  log("Budget low — skipping deep verification")
}
```

**Critical:** Always guard on `budget.total` before using `budget.remaining()`. Without the guard, `remaining()` returns `Infinity` and an unbounded loop runs straight to the 1000-agent cap.

### 5.5 Concurrency Cap

The runtime caps concurrent agents at `min(16, cpu cores - 2)` per workflow. Excess `agent()` calls queue automatically — you never need to manage this yourself.

```javascript
// Safe to do — 100 items queue and run as slots open
const results = await parallel(
  Array.from({ length: 100 }, (_, i) => () =>
    agent(`Process item ${i}`, { label: `item:${i}` })
  )
)
// All 100 complete; only ~10-16 run at any moment
```

### 5.7 1000-Agent Total Cap

A hard backstop of 1000 total `agent()` calls per workflow lifetime. This is set far above any real workflow — it only triggers runaway loops.

If you hit this cap, your workflow has a logic bug. Design all loops with an explicit exit condition: a count threshold, a budget check, or a "dry rounds" counter.

### 5.8 `workflow()` Nesting Limit

Nesting is **exactly one level**. Calling `workflow()` inside a child workflow throws immediately.

```javascript
// TOP-LEVEL script — can call workflow()
const result = await workflow('child-workflow', { data: items })

// CHILD WORKFLOW (child-workflow) — CANNOT call workflow()
// This would throw:
// const nested = await workflow('grandchild', {})  // ERROR
```

Plan your orchestration so the top-level script is the only caller of `workflow()`. The child's agents still count toward the shared concurrency cap and token budget.

### 5.9 Dynamic Prompt Loading from Files

When agent prompts grow long — multi-paragraph instructions, domain-specific templates, or reusable review criteria — embedding them as string literals inside the workflow script becomes unwieldy. Since workflow scripts have no filesystem access (`fs`, `require`, `path` are all unavailable), there are three clean patterns for externalizing prompts.

#### Pattern 1: Pre-load via `args` (Zero Extra Agents)

Before calling `Workflow`, you (or a scout agent) read the prompt files and pass their contents as `args`. The workflow script stays thin — it only orchestrates:

```javascript
export const meta = {
  name: 'prompt-from-args',
  description: 'Runs agents whose prompts are loaded externally and passed via args',
  phases: [{ title: 'Analyze' }, { title: 'Report' }],
}

// args.prompts = { analyze: "<full contents of analyze.md>", report: "<full contents of report.md>" }
const analyzePrompt = (args && args.prompts && args.prompts.analyze)
  ? args.prompts.analyze
  : 'Analyze the codebase for issues.'

const reportPrompt = (args && args.prompts && args.prompts.report)
  ? args.prompts.report
  : 'Write a report of the findings.'

const findings = await agent(analyzePrompt, { label: 'analyze', phase: 'Analyze', schema: FINDINGS_SCHEMA })
const report   = await agent(reportPrompt + '\n\nFindings:\n' + JSON.stringify(findings), { label: 'report', phase: 'Report' })
return report
```

Before calling `Workflow`, Claude reads the files and passes them:
```
Workflow({
  script: "...",
  args: {
    prompts: {
      analyze: "<full text of prompts/analyze.md>",
      report:  "<full text of prompts/report.md>"
    }
  }
})
```

**When to use:** Prompts are stable (not changing between runs), reasonably sized, and you want zero extra agent calls. Most common choice.

**Cache behavior:** Because the prompt text is embedded in `args` and the `agent(prompt, opts)` cache key includes the prompt string, changing the prompt file and re-passing it via `args` correctly invalidates the cache for that agent only — unchanged agents still get cache hits on resume.

---

#### Pattern 2: Stage-0 Loader Agent (Reads at Runtime)

Spawn a dedicated loader agent whose only job is to read the prompt file and return its contents verbatim. Use the result as the prompt for the actual work agent:

```javascript
export const meta = {
  name: 'stage0-prompt-loader',
  description: 'Loads a prompt from a file at runtime, then runs the main task',
  phases: [{ title: 'Load' }, { title: 'Run' }],
}

// args.promptFile = absolute path to the prompt file
const promptFile = (args && args.promptFile) ? args.promptFile : 'prompts/default.md'

const loadedPrompt = await agent(
  `Read the file at ${promptFile} and return its full contents verbatim. Return only the file contents — no commentary, no formatting, no prefix.`,
  { label: 'load-prompt', phase: 'Load' }
)

const result = await agent(
  loadedPrompt + '\n\nTarget: ' + (args && args.target ? args.target : 'src/'),
  { label: 'main-task', phase: 'Run' }
)

return result
```

Call it with: `Workflow({ script: "...", args: { promptFile: "C:/path/to/prompts/security-review.md", target: "src/auth" } })`

**When to use:** Prompts are large, change frequently (you want to edit the file without touching the workflow), or are shared across multiple workflows and you want a single source of truth on disk.

**Tradeoff:** Costs one extra agent call per prompt file. On resume, the loader agent result is cached unless the file path changes.

---

#### Pattern 3: Pipeline with Per-Item Prompt Files

For fan-out workflows where each branch needs its own long prompt, use `pipeline()` to load each prompt in Stage 1 before doing the actual work in Stage 2:

```javascript
export const meta = {
  name: 'per-item-prompt-pipeline',
  description: 'Each review dimension loads its own prompt file, then runs its review',
  phases: [{ title: 'Load' }, { title: 'Review' }, { title: 'Verify' }],
}

const DIMENSIONS = [
  { label: 'security',     promptFile: 'prompts/review-security.md' },
  { label: 'performance',  promptFile: 'prompts/review-perf.md' },
  { label: 'test-coverage',promptFile: 'prompts/review-tests.md' },
]

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: { type: 'string' } },
    passed: { type: 'boolean' }
  },
  required: ['findings', 'passed']
}

const results = await pipeline(
  DIMENSIONS,

  // Stage 1: load each dimension's prompt from its file
  dim => agent(
    `Read the file at ${dim.promptFile} and return its full contents verbatim.`,
    { label: `load:${dim.label}`, phase: 'Load' }
  ),

  // Stage 2: run the review using the loaded prompt
  // Use originalItem (dim) for the label — prevResult (loadedPrompt) is just text
  (loadedPrompt, dim) => agent(
    loadedPrompt + '\n\nCode diff to review:\n' + (args && args.diff ? args.diff : ''),
    { label: `review:${dim.label}`, phase: 'Review', schema: VERDICT_SCHEMA }
  ),

  // Stage 3: verify each result independently (no barrier needed)
  (review, dim) => agent(
    `Verify this ${dim.label} review — are the findings actionable and specific?\nFindings: ${JSON.stringify(review.findings)}`,
    { label: `verify:${dim.label}`, phase: 'Verify', schema: VERDICT_SCHEMA }
  )
)

return results.filter(Boolean)
```

**When to use:** You have many review dimensions (or migration targets, or analysis tasks) each with distinct long prompts. The pipeline ensures prompt-A's review starts the moment prompt-A loads, without waiting for prompt-B to finish loading.

---

#### Comparison

| Pattern | Extra agent calls | Best for |
|---------|-------------------|----------|
| Pre-load via `args` | 0 | Stable prompts, passed once at call time |
| Stage-0 loader agent | 1 per prompt | Prompts that change often, shared across workflows |
| Pipeline Stage 1 loader | 1 per item | Fan-out where each item has its own prompt file |

**General rule:** start with `args` pre-loading. Upgrade to a loader agent only when the prompt changes frequently enough that re-pasting it into `args` becomes friction.

---

## 6. Control Flow Patterns

### 6.1 Loop-Until-Count

Accumulate results to a fixed target number.

```javascript
export const meta = {
  name: 'find-ten-bugs',
  description: 'Find exactly 10 bugs in the codebase',
  phases: [{ title: 'Find' }],
}

phase('Find')

const BUGS_SCHEMA = {
  type: 'object',
  properties: {
    bugs: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, file: { type: 'string' }, description: { type: 'string' } }, required: ['title', 'file', 'description'] } }
  },
  required: ['bugs']
}

const bugs = []
let iterations = 0
const MAX_ITERATIONS = 20 // safety exit

while (bugs.length < 10 && iterations < MAX_ITERATIONS) {
  iterations++
  log(`Iteration ${iterations}: ${bugs.length}/10 bugs found`)

  const result = await agent(
    `Find bugs in the codebase. Already found ${bugs.length} bugs. 
     Focus on areas not yet covered. Return new bugs only.`,
    { label: `find:iter-${iterations}`, phase: 'Find', schema: BUGS_SCHEMA }
  )

  if (result) {
    bugs.push(...result.bugs)
  }
}

log(`Complete: found ${bugs.length} bugs in ${iterations} iterations`)
return { bugs: bugs.slice(0, 10) }
```

### 6.2 Loop-Until-Budget

Scale work to the user's `+Nk` token directive.

```javascript
export const meta = {
  name: 'budget-driven-audit',
  description: 'Find security issues — scales depth to token budget',
  phases: [{ title: 'Audit' }],
}

phase('Audit')

const ISSUES_SCHEMA = {
  type: 'object',
  properties: {
    issues: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, severity: { type: 'string' }, file: { type: 'string' } }, required: ['title', 'severity', 'file'] } }
  },
  required: ['issues']
}

const allIssues = []
const MIN_BUDGET_PER_ROUND = 50_000 // realistic cost per iteration

// CRITICAL: guard on budget.total — without this, remaining() is Infinity
while (budget.total && budget.remaining() > MIN_BUDGET_PER_ROUND) {
  const remaining = Math.round(budget.remaining() / 1000)
  log(`${remaining}k tokens remaining — scanning...`)

  const result = await agent(
    `Find security issues. Already found ${allIssues.length}. 
     Focus on new areas. Be thorough.`,
    { label: `audit:${allIssues.length}`, phase: 'Audit', schema: ISSUES_SCHEMA }
  )

  if (!result || result.issues.length === 0) break
  allIssues.push(...result.issues)
}

if (!budget.total) {
  log("No budget target set — ran one pass only")
}

return { issues: allIssues, budgetUsed: budget.spent() }
```

### 6.3 Loop-Until-Dry

For discovery tasks where you don't know how many items exist. Loop until K consecutive rounds find nothing new.

```javascript
export const meta = {
  name: 'exhaustive-edge-cases',
  description: 'Find all edge cases — stops after 2 dry rounds',
  phases: [{ title: 'Find' }],
}

phase('Find')

const CASES_SCHEMA = {
  type: 'object',
  properties: {
    cases: { type: 'array', items: { type: 'object', properties: { input: { type: 'string' }, expectedBehavior: { type: 'string' } }, required: ['input', 'expectedBehavior'] } }
  },
  required: ['cases']
}

const seen = new Set()      // dedup vs ALL SEEN — not just confirmed
const confirmed = []
let dry = 0
const K = 2  // exit after 2 dry rounds

while (dry < K) {
  log(`Round ${confirmed.length + dry + 1}: ${dry} dry rounds so far`)

  const result = await agent(
    `Find edge cases for this function. Already know about ${seen.size} cases.
     Focus on unexplored scenarios. Return new cases only.`,
    { label: `find:round-${dry}`, phase: 'Find', schema: CASES_SCHEMA }
  )

  if (!result) { dry++; continue }

  // Dedup vs ALL SEEN (not just confirmed) — critical for convergence
  const fresh = result.cases.filter(c => !seen.has(c.input))

  if (fresh.length === 0) {
    dry++  // another dry round
    log(`Dry round ${dry}/${K} — no new cases found`)
  } else {
    dry = 0  // reset on any new finding
    fresh.forEach(c => seen.add(c.input))
    confirmed.push(...fresh)
    log(`Found ${fresh.length} new cases (${confirmed.length} total)`)
  }
}

log(`Exhausted — ${confirmed.length} unique cases found`)
return { cases: confirmed }
```

**Why dedup vs `seen` (not `confirmed`):** If you only dedup against confirmed cases, then cases your agent *found but rejected* will reappear in the next round. The loop never converges because the agent keeps re-discovering the same rejected cases and resets the dry counter each time.

### 6.4 `pipeline()` vs `parallel()`

This is the most important decision in workflow design.

**`pipeline()`** — no barrier, maximum parallelism:
```
Item A: [Stage 1 ✓] → [Stage 2 ✓] → [Stage 3 running]
Item B: [Stage 1 ✓] → [Stage 2 running]
Item C: [Stage 1 running]
```
Wall-clock = slowest single item. Default choice.

**`parallel()`** — barrier, waits for all:
```
Items A, B, C run Stage 1 concurrently
→ BARRIER: wait for all Stage 1s to finish
→ Items A, B, C run Stage 2 concurrently
→ BARRIER: wait for all Stage 2s to finish
```
Wall-clock = slowest item at EACH stage, summed. Only use when the barrier is genuinely needed.

#### When `parallel()` barrier is justified

1. **Cross-item dedup before expensive downstream work:**
```javascript
// Need ALL finder results to dedup before running expensive verification
const allFindings = await parallel(FINDERS.map(f => () => agent(f.prompt, { schema: FINDINGS_SCHEMA })))
const deduped = dedupeByFileAndLine(allFindings.filter(Boolean).flatMap(r => r.findings))
// Now run expensive verification only on unique findings
const verified = await parallel(deduped.map(f => () => agent(`Verify: ${f.title}`, { schema: VERDICT_SCHEMA })))
```

2. **Early exit if count is zero:**
```javascript
const findings = await parallel(SCANNERS.map(s => () => agent(s.prompt, { schema: FINDINGS_SCHEMA })))
const all = findings.filter(Boolean).flatMap(r => r.items)
if (all.length === 0) {
  log("No findings — skipping expensive verification phase")
  return { findings: [] }
}
// Only proceed if there's something to verify
```

3. **Later agent's prompt references the full set:**
```javascript
const allProfiles = await parallel(competitors.map(c => () => agent(`Profile ${c}`, { schema: PROFILE_SCHEMA })))
// The comparison agent NEEDS all profiles to compare them
const comparison = await agent(`Compare these competitor profiles: ${JSON.stringify(allProfiles.filter(Boolean))}`)
```

#### When `pipeline()` is correct (most of the time)

```javascript
// WRONG — barrier between stages even though there's no cross-item need
const stage1Results = await parallel(items.map(i => () => agent(`Stage 1: ${i}`, { schema: S1 })))
const stage2Inputs = stage1Results.filter(Boolean).map(r => r.data)  // transform — no cross-item logic
const stage2Results = await parallel(stage2Inputs.map(d => () => agent(`Stage 2: ${d}`, { schema: S2 })))

// CORRECT — no barrier, item A's Stage 2 starts while item B is still in Stage 1
const results = await pipeline(
  items,
  item => agent(`Stage 1: ${item}`, { schema: S1, phase: 'Stage 1' }),
  (s1Result, item) => agent(`Stage 2: ${s1Result.data}`, { schema: S2, phase: 'Stage 2' })
)
```

**Smell test:** If you wrote `parallel → transform → parallel` and the transform has no cross-item logic (just a map/filter/flatten), rewrite it as a `pipeline()` with the transform inside a stage.

---

## 7. Quality Patterns

### 7.1 Adversarial Verification

After a discovery phase, spawn N independent skeptic agents per finding. Each is prompted to *refute* the finding. A finding survives only if the majority say it's real.

```javascript
const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reason: { type: 'string' }
  },
  required: ['refuted', 'reason']
}

// Verify a single finding with 3 skeptics
async function adversarialVerify(finding) {
  const voters = await parallel([
    () => agent(
      `Try to REFUTE this finding: "${finding.title}" in ${finding.file}:${finding.line}.
       Description: ${finding.description}.
       Default to refuted:true if you are uncertain.`,
      { label: `skeptic-1:${finding.title}`, schema: VERDICT_SCHEMA }
    ),
    () => agent(
      `Try to REFUTE this finding: "${finding.title}" in ${finding.file}:${finding.line}.
       Description: ${finding.description}.
       Default to refuted:true if you are uncertain.`,
      { label: `skeptic-2:${finding.title}`, schema: VERDICT_SCHEMA }
    ),
    () => agent(
      `Try to REFUTE this finding: "${finding.title}" in ${finding.file}:${finding.line}.
       Description: ${finding.description}.
       Default to refuted:true if you are uncertain.`,
      { label: `skeptic-3:${finding.title}`, schema: VERDICT_SCHEMA }
    ),
  ])

  const validVoters = voters.filter(Boolean)
  const survivorVotes = validVoters.filter(v => !v.refuted).length
  // Survives if at least 2 of 3 say NOT refuted
  return survivorVotes >= 2
}

// Apply to a list of findings
const survivors = []
for (const finding of rawFindings) {
  const isReal = await adversarialVerify(finding)
  if (isReal) survivors.push(finding)
}
log(`${survivors.length} of ${rawFindings.length} findings survived adversarial verification`)
```

**Key instruction:** "Default to `refuted: true` if uncertain." This raises the bar — only findings that can withstand scrutiny survive.

### 7.2 Perspective-Diverse Verification

When a finding can fail in more than one way, give each verifier a **different lens** rather than N identical skeptics.

```javascript
const LENS_VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    confirmed: { type: 'boolean' },
    notes: { type: 'string' }
  },
  required: ['lens', 'confirmed', 'notes']
}

const LENSES = ['exploitability', 'reproducibility', 'false-positive-likelihood']

async function diverseVerify(finding) {
  const verdicts = await parallel(LENSES.map(lens => () =>
    agent(
      `Evaluate this finding through the ${lens} lens:
       Title: ${finding.title}
       File: ${finding.file}:${finding.line}
       Description: ${finding.description}
       
       Focus specifically on ${lens}. Is this finding valid?`,
      {
        label: `verify:${lens}:${finding.title.slice(0, 30)}`,
        schema: LENS_VERDICT_SCHEMA,
        model: 'haiku'
      }
    )
  ))

  const valid = verdicts.filter(Boolean)
  const confirmed = valid.filter(v => v.confirmed).length
  // Need at least 2 of 3 lenses to confirm
  return { finding, confirmed: confirmed >= 2, lensResults: valid }
}
```

**Why better than N identical skeptics:** Each lens catches a different failure mode. A security finding might be real (not a false positive) but non-exploitable. A performance claim might be reproducible but only in edge cases. Diverse lenses reveal these nuances; identical skeptics just vote on the same dimension repeatedly.

### 7.3 Judge Panel

Generate N independent solution attempts from different angles, score all with judges, synthesize from the winner while grafting the best ideas from runners-up.

```javascript
const FIX_SCHEMA = {
  type: 'object',
  properties: {
    approach: { type: 'string' },
    code: { type: 'string' },
    tradeoffs: { type: 'string' }
  },
  required: ['approach', 'code', 'tradeoffs']
}

const JUDGMENT_SCHEMA = {
  type: 'object',
  properties: {
    winner: { type: 'string' },
    score: { type: 'number' },
    rationale: { type: 'string' },
    grafts: { type: 'array', items: { type: 'string' } }
  },
  required: ['winner', 'score', 'rationale', 'grafts']
}

async function judgePanel(bug) {
  // Generate 3 independent fix approaches
  const approaches = ['minimal-patch', 'defensive-hardening', 'architectural-refactor']
  const fixes = await parallel(approaches.map(approach => () =>
    agent(
      `Fix this bug using a ${approach} approach:
       ${bug.title}: ${bug.description}
       File: ${bug.file}`,
      { label: `fix:${approach}:${bug.title.slice(0, 20)}`, schema: FIX_SCHEMA }
    )
  ))

  const validFixes = fixes.filter(Boolean)

  // Judge scores all approaches
  const judgment = await agent(
    `You are a code review judge. Evaluate these ${validFixes.length} fix approaches for:
     Bug: ${bug.title}
     
     Approaches:
     ${validFixes.map((f, i) => `${i + 1}. ${f.approach}\nCode: ${f.code}\nTradeoffs: ${f.tradeoffs}`).join('\n\n')}
     
     Pick the winner. Note any ideas from other approaches worth grafting in.`,
    { label: `judge:${bug.title.slice(0, 20)}`, schema: JUDGMENT_SCHEMA }
  )

  return { bug, fixes: validFixes, judgment }
}
```

### 7.4 Multi-Modal Sweep

Parallel agents each search using a **different method** — none knows what the others found. Combine with dedup.

```javascript
const SCAN_SCHEMA = {
  type: 'object',
  properties: {
    method: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: { file: { type: 'string' }, issue: { type: 'string' } }, required: ['file', 'issue'] } }
  },
  required: ['method', 'findings']
}

// Each agent uses a completely different search strategy
const sweepResults = await parallel([
  () => agent(
    "Scan the codebase for security issues by reviewing import statements and dependencies",
    { label: 'sweep:imports', schema: SCAN_SCHEMA }
  ),
  () => agent(
    "Scan the codebase for security issues by searching for hardcoded strings and secrets",
    { label: 'sweep:strings', schema: SCAN_SCHEMA }
  ),
  () => agent(
    "Scan the codebase for security issues by tracing user input through the request pipeline",
    { label: 'sweep:data-flow', schema: SCAN_SCHEMA }
  ),
  () => agent(
    "Scan the codebase for security issues by reviewing authentication and authorization logic",
    { label: 'sweep:auth-logic', schema: SCAN_SCHEMA }
  ),
])

// Combine and dedup
const allFindings = sweepResults
  .filter(Boolean)
  .flatMap(r => r.findings)

const seen = new Set()
const unique = allFindings.filter(f => {
  const key = `${f.file}:${f.issue}`
  if (seen.has(key)) return false
  seen.add(key)
  return true
})

log(`Multi-modal sweep: ${allFindings.length} total findings, ${unique.length} unique after dedup`)
```

### 7.5 Completeness Critic

A final agent whose job is to identify what was missed — modalities not run, claims not verified, sources not read. Its output drives the next round of work.

```javascript
const GAPS_SCHEMA = {
  type: 'object',
  properties: {
    gaps: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          description: { type: 'string' },
          suggestedAction: { type: 'string' }
        },
        required: ['description', 'suggestedAction']
      }
    }
  },
  required: ['gaps']
}

async function completenessCritic(workDone, context) {
  const critique = await agent(
    `You are a completeness critic. Review this work and identify what is missing.
     
     Work completed:
     ${workDone}
     
     Context: ${context}
     
     What important areas were not covered? What claims were not verified?
     What sources were not consulted? Be specific.`,
    { label: 'completeness-critic', schema: GAPS_SCHEMA }
  )

  return critique ? critique.gaps : []
}

// Use in a review workflow
let round = 0
let gaps = ['initial']  // seed to enter the loop

while (gaps.length > 0 && round < 3) {
  round++
  log(`Round ${round}: addressing ${gaps.length} identified gaps`)

  // Do the work...
  const workSummary = await doReviewWork(gaps)

  // Ask the critic what's still missing
  gaps = await completenessCritic(workSummary, "Security review of the authentication module")
  log(`Critic identified ${gaps.length} remaining gaps`)
}
```

### 7.6 No Silent Caps

**Rule:** If your workflow limits scope (top-N, sampling, skipping), always `log()` what was dropped and why. Silent truncation misleads the user into thinking everything was covered.

```javascript
const MAX_FILES = 50
const allFiles = await discoverFiles()

if (allFiles.length > MAX_FILES) {
  // No Silent Caps — explicitly log what was skipped
  log(`Scanning top ${MAX_FILES} of ${allFiles.length} files (${allFiles.length - MAX_FILES} skipped — sorted by churn, low-churn files excluded)`)
}

const filesToScan = allFiles.slice(0, MAX_FILES)
const results = await parallel(filesToScan.map(f => () =>
  agent(`Scan ${f}`, { label: `scan:${f}` })
))

// Also log filter stages
const confirmed = rawFindings.filter(f => f.confidence > 0.8)
log(`Verification complete: ${confirmed.length} confirmed, ${rawFindings.length - confirmed.length} dropped (confidence below 0.8)`)
```

Apply this everywhere you impose a ceiling, take a sample, or skip verification.

---

## 8. The `meta` Block

Every workflow script must begin with `export const meta = { ... }`. It is evaluated **statically** before the script runs.

### Required Fields

```javascript
export const meta = {
  name: 'my-workflow-name',        // kebab-case slug, shown in permission dialog
  description: 'What this does',   // one-line purpose, shown in workflow list
}
```

### Optional Fields

```javascript
export const meta = {
  name: 'comprehensive-audit',
  description: 'Security audit with adversarial verification',
  whenToUse: 'When you need a thorough security review of changed files',
  phases: [
    { title: 'Discover', detail: 'Multi-modal vulnerability scan' },
    { title: 'Verify', detail: 'Adversarial verification of findings', model: 'haiku' },
    { title: 'Report', detail: 'Synthesize confirmed findings' },
  ],
}
```

The `phases` array:
- `title`: must match the string passed to `phase()` calls exactly
- `detail`: shown as a subtitle in the progress tree
- `model`: overrides the model for all agents in this phase

### CRITICAL: Pure Literal Only

The `meta` object must be a **pure literal** — no variables, function calls, template literals, spreads, or any computed values. It's evaluated statically before execution.

```javascript
// VALID
export const meta = {
  name: 'my-workflow',
  description: 'Does something useful',
  phases: [{ title: 'Find' }, { title: 'Verify' }],
}

// INVALID — will fail with a parse/eval error
const workflowName = 'my-workflow'
export const meta = {
  name: workflowName,           // ERROR: variable reference
  description: `Does ${thing}`, // ERROR: template literal
  phases: [...sharedPhases],    // ERROR: spread
}
```

---

## 9. Script Sandbox Constraints

Workflow scripts run in a restricted JavaScript environment. Understanding these constraints prevents confusing errors.

### Plain JavaScript Only

TypeScript type annotations, interfaces, and generics cause immediate parse errors:

```javascript
// INVALID TypeScript — fails to parse
const SCHEMA: JSONSchema = { ... }
function process(items: string[]): Promise<Result[]> { ... }
interface Finding { title: string; severity: string }

// VALID JavaScript — works correctly
const SCHEMA = { ... }
async function process(items) { ... }
// Use schema objects instead of interfaces
```

### Implicit Async Context

The script body runs in an implicit `async` context. Use `await` directly at the top level — no need to wrap in an `async function`.

```javascript
// Works — top-level await
const results = await parallel([...])
const synthesis = await agent("Synthesize: " + results.join(", "))
return synthesis
```

### No Filesystem or Node.js APIs

The script body cannot access `fs`, `path`, `os`, `process`, or any Node.js built-in. Use agents with the Write/Read tools for file operations:

```javascript
// INVALID — throws ReferenceError
const fs = require('fs')
fs.writeFileSync('output.md', content)

// VALID — have an agent write the file
await agent(
  `Write this content to output.md: ${content}`,
  { label: 'write:output.md' }
)
```

### Banned Non-Deterministic Functions

The following are unavailable because they break resume/caching:

| Banned | Why | Workaround |
|--------|-----|-----------|
| Timestamp function (Date dot now) | Changes every run | Pass via `args.timestamp` |
| Date constructor with no args | Changes every run | Pass via `args.startTime` |
| Random number function (Math dot random) | Non-deterministic | Use `index` to vary agents |

```javascript
// WRONG — prompts change every run, cache never hits
const result = await agent(`Analyze as of ${timestampFunction()}`)

// CORRECT — timestamp passed in from outside the script
const ts = args && args.timestamp ? args.timestamp : 'unknown'
const result = await agent(`Analyze — run started at: ${ts}`)
```

### Available Standard Built-ins

`JSON`, `Math` (except random), `Array`, `Object`, `String`, `Number`, `Boolean`, `Promise`, `Set`, `Map` — all standard JS built-ins work normally.

---

## 10. Real-World Examples

All examples are in the `workflow-examples/` directory. Each is a complete, runnable workflow script.

### 10.1 Deep Research Report

**File:** `workflow-examples/01-deep-research.js`

Researches a question by fanning out 6 parallel web searches from different angles, pipelines each result to fetch the source URL for depth, adversarially verifies the top claims with 3 skeptic agents each, and synthesizes a cited report.

**Key patterns demonstrated:**
- `parallel()` for the 6 search angles (all start simultaneously)
- `pipeline()` for the fetch stage (each result fetched as soon as its search completes)
- Adversarial verification with 3-voter majority vote per claim
- `agentType: 'Explore'` for read-only URL fetching
- `model: 'haiku'` for high-volume search agents

**Usage:** Pass `args.question` with your research question.

---

### 10.2 Security Audit

**File:** `workflow-examples/02-security-audit.js`

Scans a codebase for vulnerabilities using 4 parallel agents each focused on a different vulnerability class (injection, auth, crypto, data-exposure). Deduplicates findings across all scanners, then runs perspective-diverse verification (3 lenses per finding). Writes a final security report.

**Key patterns demonstrated:**
- Multi-modal sweep (4 blind scanners, each using different techniques)
- `parallel()` barrier justified for cross-finder dedup
- Perspective-diverse verification (exploitability / false-positive / severity lenses)
- No Silent Caps — logs confirmed vs dropped findings

**Usage:** Pass `args.targetDir` (default: `'src'`) and `args.outputFile`.

---

### 10.3 Parallel Code Migration

**File:** `workflow-examples/03-parallel-migration.js`

Discovers all files using a deprecated API, migrates each file in an isolated git worktree (preventing conflicts), verifies each migration, and reports successes and failures.

**Key patterns demonstrated:**
- `isolation: 'worktree'` for conflict-free parallel file edits
- `pipeline()` with the `(prevResult, originalItem, index)` stage signature
- `agentType: 'Explore'` for the discovery stage
- Dry-run mode via `args.dryRun`

**Usage:** Pass `args.fromApi`, `args.toApi`, `args.dir`, `args.dryRun`.

---

### 10.4 PR Review Pipeline

**File:** `workflow-examples/04-pr-review.js`

Reviews a PR across 5 dimensions (bugs, security, performance, test-coverage, style) using `pipeline()` so each dimension's verification starts the moment that dimension's review completes — no waiting for other dimensions. Applies a judge panel to the top bugs: generates 3 fix approaches, scores them, synthesizes the winner.

**Key patterns demonstrated:**
- `pipeline()` for review → verify (dimension B's verification doesn't wait for dimension A's review)
- `parallel()` for the 3 fix approaches per bug (genuine barrier — judge needs all approaches)
- Judge panel pattern with rationale + grafted ideas
- No Silent Caps — logs findings dropped at each filter stage

**Usage:** Pass `args.prNumber` or omit to use the current branch diff.

---

### 10.5 Competitive Analysis

**File:** `workflow-examples/05-competitive-analysis.js`

For a product and competitor list, runs a 4-angle multi-modal sweep per competitor, applies a completeness critic to identify information gaps, fills gaps with budget-aware targeted agents, runs a 3-analyst judge panel for comparison, and produces a structured competitive analysis.

**Key patterns demonstrated:**
- Multi-modal sweep (4 blind angles per competitor: pricing, features, reviews, news)
- Completeness critic identifying missing information
- Budget-aware gap filling (`budget.total && budget.remaining() > threshold`)
- Judge panel with 3 analyst perspectives + synthesis
- No Silent Caps — logs skipped gaps when budget is low

**Usage:** Pass `args.product` and `args.competitors` (array of strings).

---

### 10.6 Parameterized Named Workflow

**File:** `workflow-examples/06-parameterized-workflow.js`

A documentation generator that takes a file list and style via `args`, analyzes each file with `agentType: 'Explore'`, generates docs in `pipeline()`, calls a child quality-check workflow, and writes approved docs. Also demonstrates the scriptPath iteration pattern.

**Key patterns demonstrated:**
- `args` global with explicit validation and defaults
- `workflow()` child composition with `try/catch` for graceful degradation
- `agentType: 'Explore'` for the analysis stage
- `pipeline()` with stage 2 accessing `originalItem` for context
- scriptPath iteration comments (how to edit and re-run without re-pasting the script)

**Usage:** Pass `args.files` (array), `args.style` (`'markdown'` or `'jsdoc'`), `args.outputDir`.

---

## 11. Quick Reference

### Primitives and Globals

| Name | Signature | Returns | Description |
|------|-----------|---------|-------------|
| `agent()` | `agent(prompt, opts?)` | `string \| object \| null` | Spawn a subagent. Returns text, structured object (with schema), or null if skipped |
| `parallel()` | `parallel(thunks[])` | `any[]` | Run thunks concurrently. BARRIER — waits for all. Throws → null |
| `pipeline()` | `pipeline(items, ...stages)` | `any[]` | Multi-stage processing, no barrier. Default choice |
| `workflow()` | `workflow(nameOrRef, args?)` | `any` | Run a child workflow inline. One-level nesting only |
| `phase()` | `phase(title)` | `void` | Start a named phase group in the progress tree |
| `log()` | `log(message)` | `void` | Emit a narrator status line visible in real time |
| `args` | global variable | `any` | Input passed to the workflow (must be actual JSON, not encoded string) |
| `budget` | global object | — | `budget.total`, `budget.spent()`, `budget.remaining()` |

### `agent()` Options

| Option | Type | Description |
|--------|------|-------------|
| `label` | `string` | Display label in `/workflows` tree. Use `"category:detail"` format |
| `phase` | `string` | Assign to a phase group (use inside `pipeline`/`parallel` instead of calling `phase()`) |
| `schema` | `object` | JSON Schema — forces structured output, returns validated JS object |
| `model` | `'haiku' \| 'sonnet' \| 'opus'` | Override model. Omit to inherit main-loop model |
| `isolation` | `'worktree'` | Run in isolated git worktree. Expensive — only for parallel file edits |
| `agentType` | `string` | Use specialized agent type: `'Explore'` (read-only), `'Plan'` (no writes), `'general-purpose'` (all tools), `'code-reviewer'` |

### Key Patterns

| Pattern | When to Use | Key Mechanism |
|---------|-------------|---------------|
| Adversarial verify | High false-positive risk; costly errors | N skeptics per finding, majority vote, default `refuted:true` |
| Perspective-diverse | Findings with multiple failure modes | Different lenses (correctness, security, reproducibility) |
| Judge panel | Wide solution space; first attempt may not be best | N independent approaches → parallel scoring → synthesize winner |
| Multi-modal sweep | Exhaustive discovery; one search angle has blind spots | N blind agents each using a different search strategy |
| Completeness critic | After research/audit; missing something is costly | Final agent asks "what's missing?" → next round of work |
| Loop-until-count | Known target quantity | `while (results.length < TARGET)` with safety max |
| Loop-until-budget | Scale to user's `+Nk` directive | `while (budget.total && budget.remaining() > MIN)` |
| Loop-until-dry | Unknown-size discovery | Dry counter; dedup vs ALL seen (not just confirmed) |
| No silent caps | Any time you limit scope | `log()` exactly what was dropped and why |
| `pipeline()` default | Multi-stage processing (most cases) | No barrier; item A stage 2 starts while item B is in stage 1 |
| `parallel()` barrier | Cross-item dedup; early-exit on zero; prompt needs full set | Waits for ALL thunks; justified only by genuine cross-item need |
