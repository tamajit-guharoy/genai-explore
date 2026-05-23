# Claude Code — RAG, Multi-Agent Architecture & State Management Reference

---

## Part 1 — RAG in Claude

### The problem

Claude's context window (200k tokens) is large but finite. Loading entire codebases, knowledge bases, or document collections into context is wasteful and often impossible. RAG (Retrieval Augmented Generation) solves this by fetching only relevant chunks on demand.

### What Claude offers natively

**1. Prompt Caching (Anthropic API)**

Not RAG, but reduces cost of large repeated contexts:

```python
client.messages.create(
    model="claude-sonnet-4-6",
    system=[{
        "type": "text",
        "text": "huge knowledge base here...",
        "cache_control": {"type": "ephemeral"}   # cached for 5 min
    }],
    messages=[...]
)
```

- Caches up to 200k tokens
- Reuse across requests without re-sending
- Still limited by context window size
- Not semantic search — full content always loaded

**2. Files API (Anthropic API)**

Upload files once, reference across sessions:

```python
# Upload once
file = client.beta.files.upload(
    file=("knowledge.pdf", open("knowledge.pdf", "rb"))
)

# Reference in any future message
client.messages.create(
    messages=[{
        "role": "user",
        "content": [
            {"type": "document", "source": {"type": "file", "file_id": file.id}},
            {"type": "text", "text": "answer from this document"}
        ]
    }]
)
```

- Good for static documents
- Not vector search — no semantic retrieval
- File stored on Anthropic servers

**3. On-demand file reading (Claude Code)**

Agents read files only when needed — approximates retrieval:

```
Explore agent → Glob + Grep to find relevant files
             → Read only matching files into context
             → discard after task
```

- Keyword search only — not semantic
- Free, no setup
- Works well for code search

### RAG via MCP — the proper pattern

MCP servers can connect Claude to any vector database. Seen in Claude Code's plugin directory:

**Context7** — documentation retrieval
```json
{ "command": "npx", "args": ["@context7/mcp-server"] }
```
Retrieves up-to-date library documentation on demand — semantic lookup.

**Greptile** — code-aware semantic search
Searches large codebases semantically, returns only relevant snippets.

**Custom MCP RAG server:**
```typescript
server.tool("search_knowledge_base", async ({ query }) => {
    const results = await pinecone.query({
        vector: await embed(query),
        topK: 5
    })
    return { chunks: results.matches.map(m => m.metadata.text) }
})
```

Claude calls `search_knowledge_base("auth flow")` → gets back 5 relevant chunks → context stays minimal.

### RAG patterns comparison

| Approach | Semantic search | Context efficient | Persistent | Setup |
|---|---|---|---|---|
| Full context load | No | No — blows context | N/A | None |
| Prompt caching | No | Partial — still large | 5 min TTL | API param |
| Files API | No | Partial | Yes | Upload files |
| On-demand Read (Explore agent) | No — keyword only | Yes | N/A | None |
| Context7 / Greptile MCP | Yes | Yes — snippets only | Yes | Install MCP |
| Custom MCP + vector DB | Yes | Yes | Yes | Build server |

### Recommended RAG pattern

```
User question
      │
      ▼
Supervisor agent
      │
      ├── calls search_knowledge_base("relevant query")  ← MCP tool
      │         ↓
      │     vector DB returns top 5 relevant chunks only
      │         ↓
      │     context gets small relevant snippets, not full docs
      │
      └── answers based on retrieved chunks
```

---

## Part 2 — Multi-Agent DAG Architecture

### The core pattern

One main agent (supervisor) orchestrates multiple sub-agents. Sub-agents execute isolated tasks, return structured results, and are discarded. Supervisor synthesizes results.

```
Supervisor Agent (persistent session)
│
├── Creates DAG of tasks upfront
├── Spawns parallel workers for independent tasks
├── Collects structured results (JSON)
├── Spawns sequential workers for dependent tasks
└── Synthesizes final output
```

### DAG execution model

```
T1 (parse commits)     ─┐
T2 (read pkg.json)     ─┼──► T4 (group commits) ──► T5 (write file) ──► T6 (validate)
T3 (read changelog)    ─┘

T1, T2, T3 — no dependencies — run in parallel
T4 — blocked until T1 + T2 + T3 complete
T5 — blocked until T4 completes
T6 — blocked until T5 completes
```

### Sub-agent context isolation

Every sub-agent invocation gets a **fresh isolated context**:

```
Sub-agent context (per invocation):
  [agent template as system prompt]
  [skill_listing]
  [your prompt + any data you pass]
  [tool calls + results]
  ─────────────────────────────────
  discarded when agent completes

Parent receives: final text result only
```

Key implication: **parent must pass all needed context explicitly**. Sub-agents have no memory of previous invocations.

### Structured output from sub-agents

Sub-agents have no formal schema enforcement but can be prompted to return JSON:

```
Agent({
    prompt: """
        Run: git log --oneline ...

        Return ONLY valid JSON, no explanation:
        {
          "version": "<tag>",
          "features": ["..."],
          "bugfixes": ["..."]
        }
        First character must be { and last must be }
    """
})
```

Parent receives JSON string → parses → uses as typed data.

### Supervisor pattern

```
Supervisor
  │
  ├── Creates all tasks upfront (full DAG visibility)
  │
  ├── Spawns parallel agents for independent tasks
  │     each agent:
  │       1. Executes assigned task
  │       2. Returns structured JSON result
  │       3. Context discarded
  │
  ├── Collects all results
  │
  ├── Spawns sequential agents for dependent tasks
  │     passes upstream results explicitly in prompt
  │
  └── Synthesizes final output
```

---

## Part 3 — State Management Solutions

### The problem

In a large multi-agent workflow:
- Context gets compacted — intermediate results lost
- Sessions can crash — need to resume from checkpoint
- Parallel agents — need to coordinate without conflicts
- Debugging — need to know execution order and what each agent did

### Solution 1 — Claude Code Task Tools (built-in)

Six built-in tools for task tracking with dependency support:

| Tool | Purpose |
|---|---|
| `TaskCreate` | Create a task (starts as `pending`) |
| `TaskUpdate` | Change status, set owner, add dependencies, store metadata |
| `TaskGet` | Fetch full details of one task by ID |
| `TaskList` | List all tasks — status, owner, blockedBy |
| `TaskStop` | Stop a running background task |
| `TaskOutput` | Get output from a running/completed background task |

**DAG dependency wiring:**
```
TaskCreate({ subject: "Parse commits", id → T1 })
TaskCreate({ subject: "Read pkg.json", id → T2 })
TaskCreate({ subject: "Group commits", id → T3 })

TaskUpdate({ taskId: "T3", addBlockedBy: ["T1", "T2"] })
# T3 cannot move to in_progress until T1 and T2 are completed
```

**Agent claiming (prevents double-execution):**
```
TaskUpdate({ taskId: "T1", owner: "worker-1", status: "in_progress" })
```

**Storing output on task (survives compaction):**
```
TaskUpdate({
    taskId: "T1",
    status: "completed",
    metadata: { result: JSON.stringify({ features: [...] }) }
})
```

**Downstream agent reads upstream output:**
```
t1_output = TaskGet("T1").metadata.result   # not from context — from task store
```

**Important:** Task tools are **deferred** — sub-agents must call ToolSearch first:
```
ToolSearch({ query: "select:TaskCreate,TaskGet,TaskList,TaskUpdate" })
```

**Task tool limitations:**
- Session-scoped only — gone when session ends
- Cannot pause/resume across sessions
- No cross-session continuity

---

### Solution 2 — File-based State (user-proposed)

Two files maintained by supervisor:
1. `plan.md` — task dependencies and progress
2. `log.txt` — inter-agent communication and execution log

**Strengths:**
- Survives compaction — files persist, context doesn't
- Pause and resume — supervisor reads files to reconstruct state
- Human inspectable — open file to see current state
- Cross-session — works across session restarts
- Debuggable — log shows exact execution order

**Problems:**
- Race conditions — parallel agents writing same file simultaneously
- Format drift — LLMs don't write files byte-perfectly over many iterations
- Shared log grows huge — expensive to read back into context
- No atomicity — interrupted write leaves corrupt file

---

### Solution 3 — Refined File-based State (recommended)

Fix the problems while keeping the benefits:

**`plan.json` (strict schema, machine-readable):**
```json
{
    "run_id": "release-v2.1.0",
    "created_at": "2026-05-16T10:00:00Z",
    "tasks": {
        "T1": {
            "subject": "Parse git commits",
            "status": "completed",
            "depends_on": [],
            "assigned_to": "worker-1",
            "started_at": "2026-05-16T10:01:00Z",
            "completed_at": "2026-05-16T10:01:45Z",
            "output_file": "outputs/T1.json"
        },
        "T2": {
            "subject": "Read package.json",
            "status": "in_progress",
            "depends_on": [],
            "assigned_to": "worker-2",
            "started_at": "2026-05-16T10:01:00Z",
            "completed_at": null,
            "output_file": null
        },
        "T3": {
            "subject": "Group commits",
            "status": "pending",
            "depends_on": ["T1", "T2"],
            "assigned_to": null,
            "output_file": null
        }
    }
}
```

**Per-agent logs (no race conditions):**
```
logs/
  supervisor.log      ← supervisor writes only here
  worker-T1.log       ← T1 agent writes only here
  worker-T2.log       ← T2 agent writes only here
  worker-T3.log       ← T3 agent writes only here
```

**Per-task output files:**
```
outputs/
  T1.json    ← T1 result (written by T1 agent only)
  T2.json    ← T2 result (written by T2 agent only)
  T3.json    ← T3 reads T1.json + T2.json, writes T3.json
```

**Strict file ownership (eliminates race conditions):**
```
Only supervisor writes:   plan.json
Each agent writes:        logs/worker-{task-id}.log
Each agent writes:        outputs/{task-id}.json
```

**Pause and resume flow:**
```
# Session 1 — runs T1, T2, crashes mid-T3
plan.json: T1=completed, T2=completed, T3=in_progress

# Session 2 — supervisor reads plan.json on startup
"T3 was in_progress but incomplete → reset to pending, re-run"
"T1, T2 already completed → skip, read from outputs/"
```

**JSONL format for logs (structured, appendable):**
```jsonl
{"timestamp":"2026-05-16T10:01:00Z","agent":"worker-T1","event":"started","task":"T1"}
{"timestamp":"2026-05-16T10:01:30Z","agent":"worker-T1","event":"tool_call","tool":"Bash","input":"git log..."}
{"timestamp":"2026-05-16T10:01:45Z","agent":"worker-T1","event":"completed","task":"T1","output_file":"outputs/T1.json"}
```

---

### Solution 4 — Hybrid (Task Tools + Files)

Best of both worlds:

```
┌─────────────────────────────────────────┐
│  plan.json          ← DAG + status      │  files
│  outputs/T*.json    ← task outputs      │  (persist across
│  logs/worker-*.log  ← per-agent logs    │   sessions)
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│  Task tools         ← runtime tracking  │  in-session
│  (TaskCreate etc.)  ← dependency gating │  (fast, atomic,
│                     ← agent claiming    │   built-in)
└─────────────────────────────────────────┘
```

- Task tools enforce dependency ordering at runtime
- Files provide persistence, debuggability, and cross-session state
- Supervisor syncs task tool state to plan.json periodically

---

### Solution 5 — SQLite via MCP

For production-grade multi-agent applications:

```typescript
// MCP server exposing SQLite as tools
server.tool("update_task_status", async ({ task_id, status, output }) => {
    db.run("UPDATE tasks SET status=?, output=? WHERE id=?",
           [status, output, task_id])
})

server.tool("get_available_tasks", async () => {
    return db.all(`
        SELECT * FROM tasks
        WHERE status='pending'
        AND id NOT IN (
            SELECT blocked_task FROM dependencies
            WHERE blocking_task IN (
                SELECT id FROM tasks WHERE status != 'completed'
            )
        )
    `)
})
```

- ACID transactions — no race conditions
- Query-based retrieval — efficient at scale
- Persists across sessions
- But requires MCP server setup and maintenance

---

## Part 4 — Making Flow Deterministic and Predictable

### Problem sources

| Problem | Symptom |
|---|---|
| LLM non-determinism | Same prompt produces different execution paths |
| Context loss (compaction) | Agent forgets earlier decisions |
| No dependency enforcement | Agent starts task before dependency completes |
| Unstructured outputs | Downstream agent can't parse upstream result |
| No ownership tracking | Two agents execute same task simultaneously |
| No checkpointing | Crash requires full restart |

### Solutions

**1. Structured JSON outputs — enforce format**
```
"Return ONLY raw JSON. No markdown, no explanation.
 First character must be { and last must be }.
 Schema: { 'features': [...], 'fixes': [...] }"
```

**2. Explicit dependency gates**
```
# Agent prompt pattern
"Call TaskList. Only claim tasks where:
 - status = pending
 - blockedBy list is empty
 - owner is unset
 Do NOT proceed if blockedBy has any entries."
```

**3. Idempotent tasks**
```
# Each task checks if already done before executing
"Check if outputs/T1.json exists.
 If yes: read it and return contents — do not re-execute.
 If no: execute and write result to outputs/T1.json"
```

**4. Single writer per resource**
```
plan.json     → supervisor only
outputs/T1.*  → T1 agent only
logs/T1.log   → T1 agent only
```

**5. Validation gates in the DAG**
```
T5 (write file) ──► T6 (validate output)
                          │
                    pass ─┤─ fail → reset T5 to pending
                          │         create T5-fix task
                          ▼
                    T7 (next step)
```

**6. Supervisor reads state, never assumes**
```
# Supervisor prompt pattern
"Before spawning any agent:
 1. Read plan.json to see current state
 2. Find tasks where status=pending and all depends_on are completed
 3. Spawn agents only for those tasks
 Never assume a task is done — always verify from plan.json"
```

---

## Part 5 — Full Solution Comparison

| | Task Tools | plan.md + log.txt | plan.json + per-agent logs | Hybrid | SQLite MCP |
|---|---|---|---|---|---|
| Dependency enforcement | Yes — built-in | Manual | Manual | Yes | Yes |
| Agent ownership | Yes — owner field | Manual | Manual | Yes | Yes |
| Survives compaction | Yes — metadata | Yes | Yes | Yes | Yes |
| Cross-session resume | No | Yes | Yes | Yes | Yes |
| Race condition safe | Yes | No | Yes (single writer) | Yes | Yes (ACID) |
| Human inspectable | Via /tasks | Yes | Yes | Yes | Via SQL |
| Debuggable execution log | No | Partial | Yes — JSONL logs | Yes | Yes |
| Format consistency | Yes | No — LLM drift | Yes — strict schema | Yes | Yes |
| Setup complexity | None | None | Low | Low | High |
| Production ready | Partial | No | Yes | Yes | Yes |

---

## Part 6 — Recommended Architecture for Large Multi-Agent Apps

```
project/
├── plan.json                  ← DAG state (supervisor owned)
├── outputs/
│   ├── T1.json                ← T1 result (T1 agent owned)
│   ├── T2.json                ← T2 result (T2 agent owned)
│   └── T3.json                ← T3 result (T3 agent owned)
└── logs/
    ├── supervisor.jsonl       ← supervisor decisions
    ├── worker-T1.jsonl        ← T1 execution trace
    ├── worker-T2.jsonl        ← T2 execution trace
    └── worker-T3.jsonl        ← T3 execution trace
```

**Supervisor agent prompt pattern:**
```
You are a supervisor agent managing a DAG workflow.

On every invocation:
1. Read plan.json to get current state
2. Find tasks where status=pending AND all depends_on tasks are completed
3. Spawn parallel agents for all available tasks
4. Each agent must:
   a. Check if output file already exists (idempotency)
   b. Read input from outputs/{upstream-task}.json
   c. Write result to outputs/{this-task}.json
   d. Append execution log to logs/worker-{task-id}.jsonl
   e. Update plan.json: set status=completed, output_file=outputs/{id}.json
5. After all agents complete, check plan.json for next available tasks
6. Repeat until all tasks are completed or a task fails
7. On failure: log to supervisor.jsonl, reset task to pending, report to user
```

**Worker agent prompt pattern:**
```
You are a worker agent assigned to Task {task_id}: {subject}

Steps (in order):
1. Check if outputs/{task_id}.json exists
   If yes: task already completed — read and return contents, stop
   If no: continue

2. Read inputs from: {list of upstream output files}

3. Execute: {task-specific instructions}

4. Write result to outputs/{task_id}.json as valid JSON

5. Append to logs/worker-{task_id}.jsonl:
   {"timestamp": "...", "event": "completed", "output": "outputs/{task_id}.json"}

6. Update plan.json: set tasks.{task_id}.status = "completed"

Return the contents of outputs/{task_id}.json
```

---

## Quick Reference

### When to use what

| Scenario | Recommendation |
|---|---|
| Simple session workflow | Task tools only |
| Needs pause/resume | plan.json + per-agent logs |
| Large parallel DAG | Hybrid (Task tools + files) |
| Production app | SQLite MCP or hybrid |
| Debugging needed | Per-agent JSONL logs always |
| Cross-session continuity | Files always (Task tools won't work) |

### The non-negotiables for determinism

```
1. Structured JSON outputs from every agent
2. Single writer per file (no shared mutable state)
3. Idempotent tasks (check before execute)
4. Explicit dependency gates (never assume order)
5. State on disk (not in context)
6. Supervisor reads state — never assumes
```

### What big frameworks do under the hood

| Framework | State store | Pattern |
|---|---|---|
| LangGraph | In-memory graph + checkpoint | State graph with persistence |
| CrewAI | Task-based with memory | Sequential/hierarchical agents |
| AutoGen | Conversation history | Message-passing agents |
| Claude Code | Task tools + files | DAG with file persistence |

All converge on the same fundamentals: persistent state, dependency ordering, structured outputs, and single-writer ownership.
