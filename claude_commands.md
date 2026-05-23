# Claude Code Slash Commands — Complete Reference

A comprehensive tutorial of all `/` commands available in Claude Code, with descriptions and real-world examples.

---

## Table of Contents

1. [Session & Context Management](#session--context-management)
2. [Code Changes & Review](#code-changes--review)
3. [Custom Review Practices via CLAUDE.md](#custom-review-practices-via-claudemd)
4. [Planning & Execution](#planning--execution)
5. [Model & Performance](#model--performance)
6. [Parallel Work & Agents](#parallel-work--agents)
7. [Automation & Integration](#automation--integration)
8. [Project Configuration](#project-configuration)
9. [Utilities & Tools](#utilities--tools)
10. [Help & Diagnostics](#help--diagnostics)
11. [Settings & Configuration](#settings--configuration)
12. [IDE & Platform Integration](#ide--platform-integration)
13. [Account & Authentication](#account--authentication)
14. [Cloud & Remote](#cloud--remote)
15. [Miscellaneous](#miscellaneous)

---

## Session & Context Management

### `/clear`
Start a fresh conversation with empty context. Optionally label the previous session for later retrieval.

**How sessions are stored:**
Internally, Claude Code saves the current session to a `.jsonl` file named with a UUID, then opens a new session with its own UUID. Each session = one `.jsonl` file in:
```
~/.claude/projects/<project-hash>/
```

**What the label does:**

Without a label, the old session is saved only by its UUID (e.g. `3f8a2c1d-...`), making it hard to find later.

```
/clear
# → session saved as 3f8a2c1d-.... hard to rediscover
```

With a label, the session is tagged with a human-readable name you choose. You can then jump back to it by name using `/resume`:

```
/clear setup-phase
# → session saved and tagged as "setup-phase"

/resume setup-phase
# → reopens that exact conversation with all its history
```

Think of it like `git tag` — without a tag, a commit exists but is hard to find; with a tag, it's instantly addressable.

**Memory vs. disk after `/clear`:**

Once `/clear` runs, the old session is **only on disk** — it is no longer in active memory. Claude has zero awareness of that conversation in the new session.

```
/clear setup-phase
# → old session flushed to disk as a .jsonl file
# → new empty session starts in memory
# → Claude has NO memory of the previous conversation
```

When you `/resume` later, Claude Code reads the `.jsonl` back from disk and loads it into the context window:

```
/resume setup-phase
# → .jsonl read from disk → loaded into context window → Claude can "see" it again
```

Think of it like closing a browser tab — the page data persists on the server (disk), but it's gone from RAM until you reopen it.

**Concrete workflow:**
```
# Day 1 — you finish project setup: CLAUDE.md, MCP servers, permissions
# Context is long. Coding work is about to begin.

/clear setup-phase
# → Saves current session as "setup-phase", opens a fresh one

# ... a week of coding work ...

# Need to recall what was decided during setup?
/resume setup-phase
# → Reopens the old setup conversation intact
```

**Example 1:** You finished onboarding setup and want to start the actual coding session clean.
```
/clear setup-phase
```

**Example 2:** After a long debugging session, start fresh for a new feature.
```
/clear
```

---

### `/compact`
Summarize the conversation to free up context window space. Optionally pass focus instructions so the summary retains what matters most.

**Example 1:** Your session is getting long and you just want to slim it down.
```
/compact
```

**Example 2:** You're deep in a debugging loop and want the summary to focus on errors found.
```
/compact focus on the errors we found and the fixes we tried
```

---

### `/resume`
Resume a previous named session by ID or open an interactive picker.

**Example 1:** Continue yesterday's auth refactor session.
```
/resume auth-refactor
```

**Example 2:** Open the picker to choose from all available sessions.
```
/resume
```

---

### `/rename`
Rename the current session for easy identification later. Without arguments, auto-generates a name from history.

**Example 1:** You're about to hand off the session to a teammate and want a clear name.
```
/rename payment-api-bugfix
```

**Example 2:** Auto-generate a meaningful name from conversation history.
```
/rename
```

**`/resume` works with `/rename` too:**

`/rename` and `/clear <label>` are just two different ways to name a session — `/resume` works with both.

```
/rename payment-api-bugfix
/resume payment-api-bugfix   ✓ works
```

```
/clear setup-phase
/resume setup-phase          ✓ also works
```

The name is the name, regardless of how it was set. `/resume` just looks up a session by its human-readable name, whether that name came from `/rename` or `/clear <label>`.

**Difference between `/rename` and `/clear <label>`:**

| Command | What it does |
|---|---|
| `/rename payment-api-bugfix` | Labels the **current** session, stays in it |
| `/clear setup-phase` | Labels the **old** session, then starts a **fresh** one |

Use `/rename` when you want to name the session you're currently working in (e.g. for handoff). Use `/clear <label>` when you're done with a session and want to start fresh.

---

### `/branch`
Fork the current conversation at this point, preserving the original. Useful for exploring an alternative approach without losing your current path.

**What the label refers to:**

The label (e.g. `explore-quicksort-alt`) is the name of the **new forked session**, not the original. Think of it exactly like `git branch`:

- **Original session** → stays intact, keeps its existing name/UUID, untouched
- **New forked session** → named `explore-quicksort-alt`, starts at the same point in history — this is where you land after the command

So after running `/branch explore-quicksort-alt` you are now **inside the fork**. If the alternative approach doesn't work out, simply abandon it and resume the original:

```
/branch explore-quicksort-alt
# → you are now in the fork, trying the alternative

# ... experiment fails ...

/resume <original-session-name>
# → back to where you were before the fork, history untouched
```

**Which session does `/resume explore-quicksort-alt` open?**

It resumes the **fork** — because that's the name you gave the fork. The original keeps whatever name/UUID it had before `/branch` was run.

```
/resume explore-quicksort-alt    # → opens the FORK
/resume main-quicksort-solution  # → opens the ORIGINAL
```

If you hadn't named the original beforehand, run `/resume` with no arguments to open the interactive picker and find it by UUID.

**Tip — name your original before branching:**

```
/rename main-quicksort-solution
/branch explore-quicksort-alt
# now you can always get back cleanly:
/resume main-quicksort-solution
```

**Example 1:** You want to try a different algorithm without losing your current solution.
```
/branch explore-quicksort-alt
```

---

### `/rewind`
Revert the conversation (and any code changes) to a previous point. Aliases: `/checkpoint`, `/undo`.

**How it works:**

- Reverts both the **conversation history** and any **code changes** made in that turn
- Works **one step at a time** (like Ctrl+Z) — run it multiple times to go back multiple steps:
```
/rewind   # undo last turn
/rewind   # undo one more turn
/rewind   # undo one more turn
```

**Before rewinding — use `/diff` to see what you're about to undo:**
```
/diff     # shows per-turn diffs so you know exactly where rewind will take you
/rewind   # then rewind if confirmed
```

**Mental model:** Think of it like Ctrl+Z in an editor — one undo per invocation, use `/diff` first to see what you're about to undo.

**Example 1:** Claude just made a large refactor you didn't want — roll it back.
```
/rewind
```

**Example 2:** Go back several turns to before a series of bad changes.
```
/rewind
/rewind
/rewind
```

---

### `/color`
Set the prompt bar color to visually distinguish sessions (useful when running multiple terminal windows).

**`/color` vs `/theme`:**

`/color` only changes the **prompt bar color**, not the full UI theme. For full theme changes use `/theme` — but note that `/theme` is a **global setting** that applies to all sessions, not per-session.

| Command | Scope | What it changes |
|---|---|---|
| `/color red` | Per-session | Prompt bar color only |
| `/theme dark` | Global (all sessions) | Full UI theme |

There is no built-in way to set a different full theme per session. `/color` is the closest thing to per-session visual distinction, but it is limited to the prompt bar color.

**Example 1:** Color the production hotfix session red so you don't accidentally type in the wrong window.
```
/color red
```

**Example 2:** Reset to default.
```
/color default
```

---

### Sharing Sessions with Teammates (Cross-Machine)

There are three ways to share your session context with another user on a different machine:

**Option 1: `/remote-control` — live sharing**
```
/remote-control
```
Makes your session available via claude.ai. Your teammate can observe it live and take over control from their browser. Best for real-time handoff.

**Option 2: `/export` — read-only text share**
```
/export payment-session.txt
```
Exports the full conversation as plain text. Send the file to anyone — they can read all the context but cannot resume it as a live session.

**Option 3: Copy the `.jsonl` file manually — full resume on another machine**

Every session is stored as a `.jsonl` file in:
```
~/.claude/projects/<project-hash>/
```
Copy that file to the same path on your teammate's machine. They can then run `/resume <session-name>` and get the full interactive session with complete history.

**Comparison:**

| Method | Interactive? | Easy? | Use when... |
|---|---|---|---|
| `/remote-control` | Yes, live | Yes | Real-time handoff or observation |
| `/export` | No (read-only) | Yes | Teammate just needs to read the history |
| Copy `.jsonl` manually | Yes, full resume | Manual effort | Teammate needs to continue the session independently |

---

## Code Changes & Review

### `/diff`
Open an interactive diff viewer showing uncommitted changes and per-turn diffs. Navigate with arrow keys.

**What `/diff` shows:**

1. **Uncommitted changes** — all file changes since the last git commit (not just the last turn)
2. **Per-turn diffs** — diffs broken down by each conversation turn, navigate with arrow keys

**What `/diff` can't do:**

It is scoped to the current Claude Code session's changes. It is not a general-purpose git diff tool — for comparing arbitrary things use `git diff` in the terminal:

| What you want | Use |
|---|---|
| See all uncommitted changes | `/diff` |
| See what each Claude turn changed | `/diff` (navigate with arrow keys) |
| Compare branches / commits / files | `git diff` in terminal |

**How to see current vs 2 turns ago:**

There is no single built-in command for a cumulative multi-turn diff. Your options:

- **`/diff`** — navigate turn by turn with arrow keys (shows each turn separately, not combined)
- **`git diff`** — most reliable for cumulative diffs if you commit at meaningful checkpoints:
```
git diff HEAD~2              # current vs 2 commits ago
git diff HEAD~2 -- auth.py   # scoped to one file
```
- **`/rewind` twice + `/diff`** — rewind 2 turns then inspect state, but this is destructive so use carefully (branch first)

For precise multi-turn cumulative diffs, `git diff` with regular commits is the most reliable approach.

**Example 1:** Before committing, visually inspect every change Claude made across the session.
```
/diff
```

---

### `/review`
Review a pull request. Auto-detects the current branch's PR or accepts a PR number/URL.

**Example 1:** Review your own PR before requesting a teammate's review.
```
/review
```

**Example 2:** Review a specific PR by URL.
```
/review https://github.com/myorg/myrepo/pull/42
```

**When to use it:**
- Before requesting a teammate's review — catch issues yourself first
- As a quick sanity check on your own changes before merging

**Related commands:**
- `/security-review` — focused specifically on security vulnerabilities (injection, auth, data exposure)
- `/ultrareview` — deeper multi-agent review in a cloud sandbox, more thorough but heavier
- `/diff` — inspect the raw changes before reviewing

**Typical pre-merge workflow:**
```
/diff → /review → /security-review → /simplify
```

---

### `/security-review`
Analyze pending changes on the current branch for security vulnerabilities (injection, auth issues, data exposure, etc.).

**Example 1:** Run before merging a PR that touches authentication logic.
```
/security-review
```

---

### `/simplify`
Review recently changed code for reuse, quality, and efficiency, then fix issues found. Spawns parallel review agents.

**Example 1:** After implementing a feature, clean up the code quality.
```
/simplify
```

**Example 2:** Focus the review on memory efficiency specifically.
```
/simplify focus on memory efficiency
```

---

### `/ultrareview`
Run a deep multi-agent code review in a cloud sandbox. More thorough than `/review`.

**Example 1:** Deep review of your current branch before a major release.
```
/ultrareview
```

**Example 2:** Deep review of a specific PR number.
```
/ultrareview 87
```

---

## Custom Review Practices via CLAUDE.md

All review-related commands (`/review`, `/security-review`, `/simplify`, `/ultrareview`) read your project's `CLAUDE.md` before running. Any coding standards, forbidden patterns, or security rules you define there will be applied during every review.

**Setup:**

```
/init      # creates CLAUDE.md if you don't have one
/memory    # opens it for editing
```

**Example `CLAUDE.md` review guidelines:**

```markdown
## Code Review Guidelines

### Good Practices
- All public functions must have a docstring
- No raw SQL strings — always use parameterized queries
- API responses must never expose internal stack traces
- Prefer early returns over deeply nested if/else

### Forbidden Patterns
- No `console.log` left in production code
- No hardcoded credentials or API keys
- No `any` type in TypeScript except at external boundaries

### Security Requirements
- All user input must be validated before use
- Auth checks must happen at the route level, not inside handlers
```

**Which commands pick up CLAUDE.md:**

| Command | Reads CLAUDE.md? |
|---|---|
| `/review` | Yes |
| `/security-review` | Yes |
| `/simplify` | Yes |
| `/ultrareview` | Yes |
| `/plan` | Yes |

> **Note:** These rules apply to the whole session, not just review commands — Claude will also follow them while writing and editing code.

---

## Planning & Execution

### `/plan`
Enter plan mode and interactively draft an implementation strategy before writing any code. Claude proposes steps; you approve before execution.

**Example 1:** Plan a database migration before touching any files.
```
/plan migrate users table to add soft-delete support
```

**Example 2:** Plan how to refactor a module.
```
/plan refactor the auth module to use JWT instead of sessions
```

**How it behaves:**

If your prompt is ambiguous, Claude asks clarifying questions before drafting. Once ready, it presents a numbered plan and waits for your response — it never touches files until you approve.

```
/plan migrate users table to add soft-delete support
  │
  ├─ (if unclear) → asks clarifying questions
  │
  ├─ drafts the plan with numbered steps
  │
  ├─ presents it to you for review
  │
  └─ waits for your response:
       ├─ approve  → executes the plan
       ├─ feedback → revises and re-presents
       └─ cancel   → discards, no files touched
```

**Tip — more specific prompts skip the clarifying questions:**
```
# Vague → more questions
/plan improve the database

# Specific → fewer questions, faster to plan
/plan add soft-delete (deleted_at column) to users table, update all queries to filter it out
```

---

### Plan Mode via `Shift+Tab` — How it differs from `/plan`

`Shift+Tab` toggles a **global plan-only mode** on your session. It is different from the `/plan` command in a few key ways:

| | `/plan <task>` | `Shift+Tab` plan mode |
|---|---|---|
| **Scope** | One specific task | Every prompt until toggled off |
| **Flow** | Plan → approve → execute | Describe only, never executes |
| **File changes** | Executes after approval | Never touches files while active |
| **Use case** | "Plan this task carefully before doing it" | "Stop doing anything, just describe what you would do" |

**`/plan <task>`** is task-scoped and interactive — Claude drafts a plan for that one task, waits for your approval, then executes it.

**`Shift+Tab` plan mode** is a global safety toggle — while active, Claude will describe what it *would* do for any prompt, but will not execute any tool calls or file edits at all. Toggle it off when you're ready to act.

```
# Shift+Tab ON  → Claude only describes actions, nothing happens
# Shift+Tab OFF → Claude executes normally again
```

Use `Shift+Tab` when you want to explore or sanity-check a series of prompts without risk, then flip it off to execute.

---

### `/goal`
Set a goal condition. Claude keeps working autonomously until the condition is met. Clear with `stop`, `off`, or `none`.

**Example 1:** Have Claude keep running tests and fixing failures until the suite is green.
```
/goal until all tests pass
```

**Example 2:** Stop the current goal.
```
/goal stop
```

**Same agent or background?**

`/goal` runs in the **same session, in the foreground**. It is not a separate background agent — Claude loops autonomously in your current session. The UI is not fully blocked (you can interrupt with `Ctrl+C` or `/goal stop`), but it occupies your active session.

For true background execution use `/background` instead:
```
/background keep running tests and fixing failures until they pass
```

**Is there a max retry limit?**

There is no built-in `--max-tries` parameter. You can express a soft limit in natural language and Claude will follow it:
```
/goal until all tests pass, abort after 5 attempts
/goal until the build is green, give up if not resolved in 10 tries
```

This is not a hard system-level abort — it relies on Claude interpreting the instruction.

**Quick reference:**

| Question | Answer |
|---|---|
| Same agent? | Yes, foreground session |
| Blocks UI? | Yes (but interruptible) |
| Background alternative | `/background` |
| Hard max-tries limit | No built-in parameter |
| Soft limit workaround | Natural language: `abort after N attempts` |

---

### `/batch`
Orchestrate large-scale changes across the codebase. Decomposes the task into units and runs each in an isolated git worktree.

**Example 1:** Migrate all React class components to functional components across `src/`.
```
/batch migrate src/ from class components to functional components with hooks
```

**Example 2:** Add TypeScript types to an entire JavaScript project.
```
/batch add TypeScript types to all files in src/
```

---

### What is a Git Worktree?

Normally git gives you one working directory per repo. A **worktree** lets you check out multiple branches into separate directories simultaneously — all sharing the same git history.

```
# Normal setup — one working directory
my-project/         ← main branch checked out here

# With worktrees — multiple directories, same repo
my-project/         ← main branch
my-project-wt-1/    ← worktree 1, isolated copy
my-project-wt-2/    ← worktree 2, isolated copy
my-project-wt-3/    ← worktree 3, isolated copy
```

Each worktree is a full working directory but they all share the same `.git` folder. Changes in one worktree don't affect another — which is exactly why `/batch` uses them: it spins up N worktrees, runs one agent per worktree in parallel, then merges results back.

---

### Internal Phases of `/batch`

`/batch` follows three internal phases:

```
/batch migrate @Autowired to constructor injection in src/
  │
  ├─ DECOMPOSE  → identifies all units of work (e.g. each affected file)
  │               and determines what change to apply to each
  │
  ├─ EDIT       → applies the change to each unit in parallel worktrees
  │
  └─ MERGE      → brings worktree changes back, reports results
```

The decompose phase is implicit — there is no approval step like `/plan`. It determines the units and proceeds immediately.

---

### Same Agent or Separate Agents?

**Separate agents, each in an isolated git worktree, running in parallel.**

Your current session acts as the **orchestrator** — it spawns the subtask agents and collects results. It does not do the editing itself.

```
/batch (orchestrator — current session)
   ├─ worktree-1 → agent A edits OrderService.java
   ├─ worktree-2 → agent B edits PaymentService.java
   ├─ worktree-3 → agent C edits UserService.java
   └─ ... all in parallel
```

---

### Does `/batch` Test and Fix After Editing?

**No — not by default.** `/batch` applies the transformation and reports results. It does not automatically run your test suite, detect failures, or loop to fix them.

For that behaviour, chain it with `/goal`:

```
/batch migrate @Autowired to constructor injection in src/
# once batch completes...
/goal until mvn test passes, fix any compilation or test failures
```

---

### Spring Application Examples

**1. Migrate field injection to constructor injection**
```
/batch migrate all @Autowired field injection to constructor injection in src/main/java
```
Before:
```java
@Service
public class OrderService {
    @Autowired
    private PaymentService paymentService;
}
```
After:
```java
@Service
public class OrderService {
    private final PaymentService paymentService;

    public OrderService(PaymentService paymentService) {
        this.paymentService = paymentService;
    }
}
```

**2. Spring Boot 2 → 3 migration (`javax` → `jakarta`)**
```
/batch replace all javax.persistence imports with jakarta.persistence, javax.servlet with jakarta.servlet across src/
```

**3. Add OpenAPI annotations to all REST controllers**
```
/batch add @Operation and @ApiResponse Swagger annotations to all @RestController classes in src/
```

**4. Replace `RestTemplate` with `WebClient`**
```
/batch migrate all RestTemplate usages to WebClient in src/main/java
```

---

### Apache Spark Examples

**1. Migrate RDD API to DataFrame API**
```
/batch migrate all RDD-based transformations to DataFrame API across src/main/scala/jobs
```
Before:
```scala
val counts = rdd.map(line => (line.split(",")(0), 1)).reduceByKey(_ + _)
```
After:
```scala
val counts = df.groupBy("id").count()
```

**2. Spark 2 → 3 deprecation fixes**
```
/batch replace deprecated SQLContext usages with SparkSession across all job files in src/
```

**3. Add schema enforcement to all `spark.read` calls**
```
/batch add explicit schema definitions to all spark.read.csv and spark.read.json calls in src/main/scala
```
Before:
```scala
val df = spark.read.option("inferSchema", "true").csv("data/input.csv")
```
After:
```scala
val schema = StructType(Seq(StructField("id", StringType), StructField("amount", DoubleType)))
val df = spark.read.schema(schema).csv("data/input.csv")
```

**4. Replace unsafe `collect()` with bounded alternatives**
```
/batch replace unbounded collect() calls with take(1000) or limit() where safe across all Spark jobs
```

---

### When to Use `/batch` vs Manually

| Situation | Use `/batch`? |
|---|---|
| Same change in 3–5 files | No — just do it manually |
| Same change in 20+ files | Yes |
| Pattern is consistent and mechanical | Yes |
| Each file needs custom judgment | No — use `/plan` instead |
| Refactor touches interconnected logic | No — too risky for parallel worktrees |

---

### Using `/plan` and `/batch` Together

There is **no native pipe** between `/plan` and `/batch`. Worktree agents start fresh and don't inherit your session's conversation history. Here are the recommended approaches to connect them:

**Approach 1 — Save the pattern to `CLAUDE.md` (most reliable)**

Worktree agents read `CLAUDE.md` before starting, so anything saved there is available to every subtask agent.

```
# Step 1: validate the pattern on one file
/plan migrate @Autowired field injection to constructor injection in OrderService.java

# Step 2: save the approved pattern to CLAUDE.md
/memory  → add transformation rules as a section

# Step 3: batch picks up the pattern from CLAUDE.md automatically
/batch migrate @Autowired field injection to constructor injection in src/
```

**Approach 2 — Be explicit in the `/batch` prompt**

Encode what you learned from `/plan` directly in the batch instruction:
```
/batch in src/main/java, for every class annotated with @Service or @Component:
  - remove @Autowired from all fields
  - make those fields private final
  - generate a constructor injecting all of them
  - skip classes already using @RequiredArgsConstructor
```

**Approach 3 — `/ultraplan` → `/batch` (purpose-built for this)**

`/ultraplan` opens in your browser, lets you review and edit the plan, then sends it back for execution:
```
/ultraplan design the Spring Boot 2 to 3 migration strategy across the codebase
# → review and approve in browser
# → send back to terminal

/batch replace javax.* with jakarta.* imports across src/
```

**Approach 4 — Export the plan to a file**
```
/plan migrate RDD jobs to DataFrame API in WordCountJob.scala
/export spark-migration-plan.txt

/batch following the pattern in spark-migration-plan.txt, migrate all RDD jobs in src/main/scala/jobs/
```

| Approach | Effort | Reliability | Best for |
|---|---|---|---|
| Save to `CLAUDE.md` | Medium | High | Reusable patterns, team projects |
| Explicit batch prompt | Low | Medium | One-off migrations |
| `/ultraplan` → `/batch` | Low | High | Large, complex migrations |
| Export to file | High | Low | Audit trail needed |

---

### Full Recommended Workflow for a Risky Migration

```
# 1. Plan on one representative file — validate the pattern
/plan migrate WordCountJob.scala from RDD API to DataFrame API

# 2. Save approved pattern to CLAUDE.md
/memory  → add transformation rules

# 3. Batch a small package first — smoke test
/batch migrate src/main/scala/jobs/wordcount/ from RDD to DataFrame API

# 4. Review the diff
git diff

# 5. Happy? Run on full codebase
/batch migrate all jobs in src/main/scala/jobs/ from RDD to DataFrame API

# 6. Fix compilation/test failures in a loop
/goal until sbt test passes, fix any type or API errors
```

---

## Model & Performance

### `/model`
Switch the AI model mid-session. Opens a picker interactively or accepts a model ID directly.

**Default model:**

If you don't set a model explicitly, Claude Code uses **Claude Sonnet** as the default. The exact version (e.g. `claude-sonnet-4-6`) reflects Anthropic's current recommended baseline and may change as newer models are released — it is not permanently fixed.

To set a persistent default so you don't have to use `/model` every session, run `/config`.

**Example 1:** Switch to Opus for a complex architecture task.
```
/model claude-opus-4-7
```

**Example 2:** Open the interactive picker.
```
/model
```

**Example 3:** Set a persistent default model via config.
```
/config
```

---

### `/effort`
Set the model's effort/thinking level: `low`, `medium`, `high`, `xhigh`, `max`. Use `auto` to reset. Opens a slider without arguments.

**Important:** The effort level is session-persistent — it applies to every response until you change it, not just the next prompt. If you forget to reset after a complex task, trivial follow-up questions will still run at the elevated effort level and burn extra tokens unnecessarily.

**Recommended pattern for a specific task:**
```
/effort high          # 1. elevate for the task
<your prompt here>    # 2. run the task
/effort auto          # 3. reset to default immediately after
```

**Example 1:** Boost effort for a tricky concurrency bug.
```
/effort high
```

**Example 2:** Drop to low effort for a quick rename task.
```
/effort low
```

**Example 3:** Reset to default after a high-effort task.
```
/effort auto
```

---

### `/fast`
Toggle fast mode on/off (uses Claude Opus with faster output).

**`/fast` vs `/effort` — separate axes:**

- **`/effort`** controls **thinking depth** — how many reasoning tokens the model uses internally before responding.
- **`/fast`** controls **output speed** — how quickly tokens are streamed to you. It does not change reasoning depth.

They operate on different phases: thinking happens *before* the first token appears, streaming happens *after*. So they don't conflict and can be combined independently:

| Combination | Effect |
|---|---|
| `/fast on` + `/effort high` | Fast output, deep thinking |
| `/fast off` + `/effort low` | Normal output, minimal thinking |
| `/fast on` + `/effort auto` | Fast output, default thinking |

**Why not always use fast + deep thinking?**

It's technically possible but rarely the right default:

| Reason | Detail |
|---|---|
| **Cost** | `/effort high` burns significantly more reasoning tokens — expensive for trivial tasks |
| **Latency** | Deep thinking still adds wall-clock time before the first token appears, even if streaming is fast after |
| **Overkill** | Most tasks (renaming a variable, formatting code) don't benefit from deep reasoning at all |

`/fast` doesn't make deep thinking free — it only speeds up the output phase after thinking finishes. The real trade-off is **cost vs. quality**, not speed.

**Does `/fast on` increase cost?**

Potentially yes. `/fast` uses Claude Opus under the hood. If you're on the default Sonnet model, turning on `/fast` upgrades you to Opus, which costs more per token. If you're already on Opus, the cost difference is less clear.

**Recommended pattern for urgent tasks:**
```
/fast on      # 1. switch to faster Opus output
<urgent task> # 2. get the response quickly
/fast off     # 3. switch back to default
```

The reset step matters — like `/effort`, fast mode persists for the whole session until changed. Forgetting to reset means all subsequent prompts (including trivial ones) continue running on the more expensive Opus.

**When to use it:**

Use `/fast` when turnaround time matters more than cost — e.g., unblocked on something urgent, live debugging session, or need a quick answer mid-meeting. For normal work where speed isn't critical, staying on the default Sonnet is cheaper.

**Example 1:** Speed up a long code generation session.
```
/fast on
```

---

### `/compact`
*(Also listed under Session Management)* — Free up context by summarizing.

**Example:**
```
/compact focus on the API design decisions we made
```

---

### `/context`
Visualize current context usage as a colored grid. Shows optimization suggestions. Pass `all` for fullscreen detail.

**What `/context` does NOT do:**

`/context` is a usage metrics tool, not a content inspection tool. It shows *how much* of the context window is consumed, not *what's in it*. It cannot be used to check whether a specific file, section, or content is available in the current context.

**To check if something is in context:**

| Goal | How |
|---|---|
| Is a file in context? | Ask: *"Do you have access to X file?"* |
| Is specific content available? | Ask: *"What do you know about X?"* |
| What was summarized away? | Run `/compact` — it tells you what it's condensing |
| See raw session history | Parse the `.jsonl` file (see below) |

**Inspecting context via the `.jsonl` file:**

Every session is stored as a `.jsonl` file (one JSON object per line — user messages, assistant responses, tool calls, file reads, etc.) at:
```
# Windows
C:\Users\<user>\.claude\projects\<project-hash>\<session-uuid>.jsonl
```

Parse it in PowerShell to audit session history:
```powershell
# List all message roles/types
Get-Content <session>.jsonl | ForEach-Object { $_ | ConvertFrom-Json } | Select-Object type, role

# Extract user message content
Get-Content <session>.jsonl | ForEach-Object { ($_ | ConvertFrom-Json) } | Where-Object { $_.role -eq "user" } | Select-Object -ExpandProperty content
```

**Important caveat — session history ≠ active context window:**

The `.jsonl` is the complete session record. The active context window is a subset — the most recent turns that fit within the token limit. After `/compact` runs, the original turns are replaced by a summary in the active context, even though the raw turns remain in the `.jsonl`. So parsing the file is useful for auditing what happened, but not for knowing exactly what Claude can see right now — for that, just ask Claude directly.

**Example 1:** Check how much context you've used before starting a large task.
```
/context
```

**Example 2:** Full breakdown of context consumption.
```
/context all
```

---

## Parallel Work & Agents

### `/agents`
Manage subagent configurations for delegating side tasks. Opens a **tabbed interactive interface** with two panels:

- **Running** — shows live subagents currently active in your session (open or stop them)
- **Library** — lists all available subagents (built-in, user, project, plugin); create, edit, or delete them here

**Example 1:** Set up a subagent to handle running tests while you focus on implementation.
```
/agents
```

---

### Built-in Subagents

Claude Code ships with these pre-configured agents out of the box:

| Subagent | Model | Purpose |
|---|---|---|
| Explore | Haiku | Fast, read-only codebase search |
| Plan | Inherits | Research before editing |
| General-purpose | Inherits | Complex multi-step tasks |
| claude-code-guide | Haiku | Answers Claude Code questions |
| statusline-setup | Sonnet | Used by `/statusline` |

---

### Creating a Custom Subagent

**Method 1: Via `/agents` UI (Recommended)**

1. Type `/agents` → go to **Library** tab → press **Create**
2. Fill in:
   - **Name** — unique identifier (e.g. `test-runner`)
   - **Description** — Claude reads this to decide when to auto-delegate
   - **Tools** — which tools it can access
   - **Model** — Haiku (fast/cheap), Sonnet, Opus, or inherit from main
3. Press `s` to save (or `e` to save and open in editor)

**Method 2: Manual Markdown File**

Create a `.md` file in one of these locations:
- **Project-level:** `.claude/agents/test-runner.md`
- **User-level (all projects):** `~/.claude/agents/test-runner.md`

Minimal example:
```markdown
---
name: test-runner
description: Runs the test suite and returns a pass/fail summary with error details
tools: Bash, Read
model: haiku
---

You are a test runner. Execute the test command, capture output, and return a concise summary: total tests, passed, failed, and the first 3 error messages if any failed.
```

Full frontmatter options:
```yaml
---
name: test-runner
description: Runs tests and summarizes results   # Claude uses this to auto-delegate
tools: Bash, Read, Glob                          # Tools it can use
disallowedTools: Write, Edit                     # Tools explicitly blocked
model: haiku                                     # haiku / sonnet / opus / inherit
maxTurns: 10                                     # Max agentic turns
permissionMode: auto                             # default / auto / plan
background: false                                # true = runs concurrently
effort: low                                      # low / medium / high / max
color: green                                     # visual ID in UI
---
```

**The description field is the most important part** — Claude decides whether to auto-delegate based on it. Be specific:
```yaml
# Too vague — Claude won't know when to use it
description: helps with code

# Good — Claude knows exactly when to delegate
description: Runs pytest, captures output, and returns a structured pass/fail summary with failing test names and error messages
```

---

### Subagent Scope & Priority

| Location | Scope | Priority |
|---|---|---|
| Managed settings | Organization-wide | 1 (highest) |
| `.claude/agents/` | Current project | 2 |
| `~/.claude/agents/` | All your projects | 3 |
| Plugin `agents/` dir | Where plugin enabled | 4 (lowest) |

If duplicates exist across scopes, higher priority wins.

---

### How Results Come Back

- **Foreground subagents** — block until done, return a summary to your main conversation. Verbose output stays in the subagent's own context, keeping your main context window clean.
- **Background subagents** (`background: true` in frontmatter) — run concurrently; results arrive asynchronously while you continue working.

---

### `/agents` vs `claude agents` (CLI)

| | `/agents` (slash command) | `claude agents` (CLI) |
|---|---|---|
| **What it manages** | Subagents *inside* your session | Independent background sessions across your system |
| **Results** | Returned to your conversation | Monitored separately, attach/detach as needed |
| **Use case** | Delegate a side task | Hand off many independent tasks in parallel |

---

### Invoking a Subagent

Claude may auto-delegate based on the task description, or you can be explicit:
```
@test-runner verify my changes didn't break anything
@explore find all usages of AuthService
Use the test-runner subagent to check the build
```

---

### `/tasks`
List and manage **background bash processes** running within the current session — long-running commands like dev servers, test runners, and build watchers that Claude has started asynchronously.

**Example 1:** Check the status of a background build task.
```
/tasks
```

Alias: `/bashes`

---

### What `/tasks` Shows

`/tasks` shows **currently running tasks only** — not completed ones. Completed tasks are cleaned up automatically when the session ends.

Per task, it displays:
- **Task ID** — unique identifier
- **Status** — running / stopped
- **Command** — what's being executed
- **Output** — readable by attaching to the task

**Toggle the task list in the status bar:** `Ctrl+T` (shows up to 5 tasks at a time)

---

### Interacting with Tasks

| Action | How |
|---|---|
| View all running tasks | `/tasks` |
| Attach to a task and see live output | Select it in the `/tasks` view |
| Stop a task | Stop option within `/tasks` |
| Toggle status bar task list | `Ctrl+T` |

---

### How Background Tasks Are Created

| Method | How |
|---|---|
| Claude starts automatically | Claude sets `run_in_background: true` on long-running commands |
| You background a running command | Press `Ctrl+B` while a command is executing |
| Monitor tool | Claude watches something (logs, CI, file changes) and reacts when it changes |

**Common use cases:** webpack, vite, npm, jest, pytest, docker, dev servers, log tailing.

---

### Giving Permissions to Background Tasks

Background tasks **inherit the session's permission mode** — the same rules apply to foreground and background work. There is no separate per-task permission system.

**What happens when a task needs a permission:**

| Mode | Behaviour |
|---|---|
| `default` | Task **pauses and prompts you** — blocks until you respond |
| `acceptEdits` | File edits and common FS commands (mkdir, mv, cp, rm) **auto-approve** |
| `auto` | Classifier decides — auto-approves safe actions, blocks risky ones |
| `dontAsk` | Unpermitted actions **fail silently** with no prompt |
| `bypassPermissions` | Everything executes immediately (only for isolated VMs) |

**Switch mode mid-session:** `Shift+Tab` cycles through modes.

**Pre-grant permissions in `.claude/settings.json`:**
```json
{
  "permissions": {
    "allow": [
      "Bash(npm run *)",
      "Bash(npm test *)",
      "Bash(git commit *)",
      "Bash(make *)"
    ],
    "deny": [
      "Bash(rm -rf *)",
      "Bash(git push -f *)"
    ]
  }
}
```

**Rule precedence (first match wins):** `deny → ask → allow`

Deny always overrides allow — even if both match, the deny rule wins.

**Set `acceptEdits` as your default** to auto-approve file and FS operations without a long allow list:
```json
{
  "permissions": {
    "defaultMode": "acceptEdits"
  }
}
```

**When a task hits a denied permission:**
- Action is blocked and logged under `/permissions` → "Recently denied"
- Task stops — no automatic retry
- Open `/permissions`, review the denial, adjust the rule, then re-run

---

### `/tasks` vs `/agents` vs `/background`

| Command | What it manages | Scope |
|---|---|---|
| `/tasks` | Background bash processes in the current session | Current session only |
| `/agents` | Subagent configurations (specialized AI workers) | User or project level |
| `/background` | Detaches the **entire session** as a background agent | Cross-session (managed via `claude agents` CLI) |
| `/goal` | Autonomous looping toward a condition | Foreground, same session |

**Key point:** `/tasks` is about **shell processes**, not subagents. A backgrounded `npm run dev` shows in `/tasks`; a subagent spawned via `@explore` does not.

---

### Session Scope

`/tasks` is **scoped to the current session only**. All background tasks terminate when you exit. To share task lists across sessions, set `CLAUDE_CODE_TASK_LIST_ID` to a named directory in `~/.claude/tasks/`.

---

### `/background`
Detach the **current session** to run autonomously as a background agent, freeing your terminal. Alias: `/bg`.

**Example 1:** Start a long migration and free your terminal.
```
/background continue with the database migration
```

**Example 2:** Pass a prompt before detaching.
```
/bg run the full test suite and fix any failures
```

---

### `/background` — How It Works (Transfer, Not Fork)

`/background` is a **transfer**, not a fork. The current session moves from being terminal-attached to being hosted by a background supervisor process. No new session or `.jsonl` file is created.

```
Before /background:
  terminal → session (abc123.jsonl)   ← you're attached

After /background:
  supervisor → session (abc123.jsonl) ← same file, still running
  terminal → freed                    ← no session here
```

The same `.jsonl` continues to grow as the background session runs. The terminal does not get a continuing foreground session — Claude Code exits from it. If you want to work in the foreground after backgrounding, open a new `claude` session, which creates a brand new `.jsonl` with a new UUID:

```
supervisor → abc123.jsonl  ← background, running autonomously
terminal   → def456.jsonl  ← new foreground session, new file
```

---

### `.jsonl` and Per-Agent Logs

**Each subagent gets its own `.jsonl` transcript**, stored in a `subagents/` subdirectory under the parent session:

```
~/.claude/projects/<project>/<session>/
  abc123.jsonl                          ← parent session (summary result only)
  subagents/
    agent-abc.jsonl                     ← subagent 1 full transcript
    agent-def.jsonl                     ← subagent 2 full transcript
```

The parent session's `.jsonl` records only the **summary result** returned by the subagent. The full verbose transcript — all the subagent's tool calls, reasoning, and intermediate steps — lives in its own `agent-{agentId}.jsonl` file.

```
parent session (abc123.jsonl)
  └─ spawns @explore subagent
       → runs with full isolated context
       → full transcript saved to subagents/agent-abc.jsonl
       → summary result only appended to abc123.jsonl
```

**`.jsonl` behaviour by situation:**

| Situation | `.jsonl` behaviour |
|---|---|
| New `claude` session in terminal | New UUID, new top-level `.jsonl` |
| `/background` detaches current session | **Same `.jsonl`** continues in background |
| New session dispatched from Agent View | New UUID, new top-level `.jsonl` |
| `/branch` forks a session | New UUID, new `.jsonl` (copy of parent up to fork point) |
| Subagent spawned within a session | **Own `.jsonl`** in `subagents/` subdirectory |

To read a subagent's full transcript:
```bash
cat ~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl
```

---

### Per-Agent Persistent Memory

Subagents with memory enabled store their memory separately from the main session auto-memory:

| Path | Scope |
|---|---|
| `.claude/agent-memory/<agent-name>/MEMORY.md` | Project-scoped |
| `~/.claude/agent-memory/<agent-name>/MEMORY.md` | User-scoped (all projects) |
| `.claude/agent-memory-local/<agent-name>/MEMORY.md` | Local only (not committed) |

These are separate from main session auto-memory at `~/.claude/projects/<project>/memory/`.

---

### Debug Logs

When `/debug` is active, logs are written to `~/.claude/debug/` per session. There is no separate debug file per subagent, but **subagent lifecycle events** (SubagentStart, SubagentStop) are logged within the parent session's debug output.

---

### Monitoring — `claude agents` (Agent View)

Run `claude agents` to open **Agent View** — the dashboard for all background sessions. Sessions are grouped by state:

| Group | Meaning |
|---|---|
| Pinned | Sessions you marked important |
| Needs input | Waiting for your reply or a permission decision |
| Working | Actively executing |
| Ready for review | Session opened a PR |
| Completed / Failed / Stopped | Done |

Per row it shows: animated state icon, one-line progress summary, PR status if applicable.

**Shell commands:**
```bash
claude agents              # open Agent View
claude logs <id>           # print recent output from a session
claude attach <id>         # attach directly from shell
```

---

### Attaching Back to a Background Session

From Agent View, press `Enter` or `→` on a session row to attach. You see a recap of what happened while detached. All interactive commands and shortcuts work normally while attached.

**To detach without stopping the session:**
- Press `←` on an empty prompt
- Run `/exit`
- Press `Ctrl+Z`

None of these stop the session — they only detach you from it.

---

### Multiple Background Sessions

You can run many simultaneously. Dispatch multiple tasks from Agent View and they all run in parallel, each consuming quota independently.

---

### Survival Across Terminal/Machine Events

| Event | Background session |
|---|---|
| Close terminal window | Keeps running |
| SSH disconnect | Keeps running |
| Machine sleep / shutdown | **Stops** |

When the machine wakes, stopped sessions show as "failed" in Agent View. Restart them with:
```bash
claude respawn <session-id>    # restart one
claude respawn --all           # restart all stopped sessions
```
The transcript and context are preserved on disk — restarting resumes from where it left off.

---

### Permissions in Background Sessions

Background sessions inherit the permission mode active when they were backgrounded. When a session needs input (including a permission decision), it moves to the **"Needs input"** group in Agent View — it does not auto-deny. You can reply from Agent View without fully attaching.

`auto` and `bypassPermissions` modes must be accepted interactively first before they apply to background sessions (a safety requirement for unattended execution).

---

### Stopping a Background Session

| Method | Effect |
|---|---|
| `Ctrl+X` in Agent View | Stops the session |
| `Ctrl+X` again within 2s | Deletes it and cleans up worktree |
| `claude stop <id>` | Stops from shell |
| `/stop` inside attached session | Stops the session |
| `/exit` or `←` while attached | **Detaches only** — session keeps running |

---

### `/background` vs `Ctrl+B`

| | `/background` | `Ctrl+B` |
|---|---|---|
| What moves | Entire session (same `.jsonl`) | Single bash command |
| Terminal | Freed completely | Stays open, Claude still interactive |
| Monitored via | `claude agents` (Agent View) | `/tasks` |
| Use case | Long multi-step autonomous task | Long build/test while you keep chatting |

---

### State Storage

```
# Session files
~/.claude/projects/<project>/<session>.jsonl          ← session transcript
~/.claude/projects/<project>/<session>/subagents/
  agent-{id}.jsonl                                    ← per-subagent full transcript

# Agent memory (per named subagent)
.claude/agent-memory/<name>/MEMORY.md                 ← project-scoped
~/.claude/agent-memory/<name>/MEMORY.md               ← user-scoped

# Background session state (Agent View)
~/.claude/daemon.log                                  ← supervisor log
~/.claude/daemon/roster.json                          ← list of running background sessions
~/.claude/jobs/<id>/state.json                        ← per-background-session state
~/.claude/worktrees/                                  ← isolated git worktrees

# Debug logs (when /debug is active)
~/.claude/debug/                                      ← per-session debug output
```

---

### `/stop`
Terminates the current background session permanently. Unlike `/exit` (which only detaches you from the session while it keeps running), `/stop` ends the session entirely.

**Critical distinction:**

| Command | What it does | Session fate |
|---------|-------------|--------------|
| `/stop` | Terminate the background session | Ends permanently → moves to Completed/Stopped in Agent View |
| `/exit` or `/quit` | Detach from the background session | Keeps running in background — you can re-attach later |

**All ways to stop a background session:**

| Method | Where | Effect |
|--------|-------|--------|
| `/stop` | Inside attached background session | Terminates session immediately |
| `Ctrl+X` | Agent View (`claude agents`) | Sends stop signal to selected session |
| `Ctrl+X` again within 2 seconds | Agent View | Deletes the session record entirely |
| `claude stop <session-id>` | Any shell | Terminates session by ID |

**After stopping:**
- Session moves to the **Completed / Stopped** group in Agent View
- The `.jsonl` transcript on disk is **preserved** — you can still read the full history
- Any in-progress tool calls are abandoned; no partial results are committed

**Scope:** `/stop` only applies to background sessions. For a foreground session:
- Use `Ctrl+C` to interrupt the current operation
- Use `/exit` to close the session

**Example:**
```
/stop
```

---

## Automation & Integration

### `/loop`
Run a prompt repeatedly on a timer while the session stays open. Omit interval for self-pacing.

**Example 1:** Poll every 5 minutes to check if a CI deploy finished.
```
/loop 5m check if the deployment to staging finished
```

**Example 2:** Self-paced loop running a maintenance check continuously.
```
/loop run linting and fix any new issues
```

**Does `/loop` run in the foreground or background?**

`/loop` runs in the **foreground** of your current session — the same as `/goal`. Your terminal is occupied while it runs.

| Command | Where it runs |
|---|---|
| `/loop` | Foreground, current session |
| `/goal` | Foreground, current session |
| `/background` | Detaches entire session to background supervisor |

To run a loop in the background while keeping your terminal free:
```
/loop 5m check deployment status
/background   # detach the whole session — loop keeps running
```

The session (including the active loop) moves to the background supervisor. Monitor it via `claude agents`.

---

### `/schedule`
Create recurring remote agents that run on a cron schedule. Claude walks you through setup conversationally.

**Example 1:** Schedule a weekly dependency audit.
```
/schedule run npm audit every Monday at 8am
```

**Example 2:** One-time scheduled task.
```
/schedule run the database backup script tomorrow at 2am
```

**Does each execution create a session?**

**Yes.** Each scheduled run spins up its own independent remote agent session with its own `.jsonl` transcript. Think of it like a cron job that boots a fresh Claude Code instance each time.

**Foreground or background?**

**Neither — it's remote.** `/schedule` creates agents that run on **Anthropic's cloud infrastructure**, not on your machine. Your terminal is completely free once the schedule is set up.

| Command | Where it runs | Terminal |
|---|---|---|
| `/loop` | Local, foreground | Occupied |
| `/goal` | Local, foreground | Occupied |
| `/background` | Local, background supervisor | Freed |
| `/schedule` | Remote (Anthropic cloud) | Completely free |

**What if the machine is shut down?**

**Nothing happens — it still runs.** Since agents execute remotely, your machine's state is irrelevant. Whether your laptop is off, asleep, or disconnected, scheduled runs fire on time.

This is the key advantage over `/loop + /background` — a background local session **stops if your machine shuts down**, but a scheduled remote agent does not.

---

### `/autofix-pr`
Spawn a web session that watches your branch's PR and automatically pushes fixes for CI failures or review comments.

**Example 1:** Auto-fix all CI lint failures on a PR.
```
/autofix-pr only fix lint errors, don't touch logic
```

**What is a "web session"?**

A **web session** is a Claude Code session that runs in the browser at claude.ai, not in your terminal. It is an Anthropic-hosted environment — a cloud Claude Code instance with a browser UI instead of a terminal UI.

**Where does it run?**

**Remotely on Anthropic's cloud**, same as `/schedule`. Your terminal is completely free once launched.

| Command | Where it runs | Terminal |
|---|---|---|
| `/autofix-pr` | Remote web session (Anthropic cloud) | Freed |
| `/schedule` | Remote agent (Anthropic cloud) | Freed |
| `/background` | Local background supervisor | Freed |

**How does it read CI errors?**

It connects to your GitHub repository via the **GitHub integration** (the app installed via `/install-github-app`). Through this it:
- Watches the PR's CI status checks
- Reads the full CI log output when a check fails
- Identifies what needs fixing (lint failure, test failure, type error, etc.)

This is why `/install-github-app` is a prerequisite — without it, the web session has no way to observe CI state or push changes back.

**Does it create commits and push to GitHub?**

**Yes — both.** The full automated loop is:

```
CI fails on your PR
  → web session reads the CI error log
  → identifies the fix needed
  → edits the code
  → creates a commit
  → pushes to your PR branch on GitHub
  → CI reruns automatically
  → repeats until CI passes (or review comments are resolved)
```

You can constrain what it is allowed to touch:
```
/autofix-pr only fix lint errors, don't touch logic
```
Without constraints it may fix anything CI flags, including test failures and type errors.

**Prerequisites:**
```
/install-github-app   # must be done first — connects Claude to your repo
/autofix-pr           # then launch the watcher on the current branch's PR
```

**Does `/autofix-pr` read CLAUDE.md?**

Almost certainly **yes**. The docs don't explicitly confirm this for `/autofix-pr` specifically, but two things make it very likely:

1. The docs state: *"These rules apply to the whole session, not just review commands — Claude will also follow them while writing and editing code."* — `/autofix-pr` is a Claude Code session and the same loading behavior applies.
2. Since the web session already has full repo access via the GitHub integration (to read CI logs and push commits), it naturally reads `CLAUDE.md` from the repo root before making any edits.

**Practical use — put autofix constraints in CLAUDE.md:**

```markdown
## Autofix Rules
- Never change test assertions to make tests pass — fix the implementation instead
- Do not auto-format files that weren't part of the original PR diff
- Prefer fixing the root cause, not suppressing lint warnings with inline comments
```

This is more reliable than cramming everything into the `/autofix-pr` prompt each time — it persists across all sessions and all commands. Worth verifying on first real use since this is inferred, not explicitly documented.

**`/autofix-pr` vs `/goal until tests pass`:**

| | `/autofix-pr` | `/goal until tests pass` |
|---|---|---|
| Runs on | Anthropic cloud (web session) | Local, foreground |
| Watches GitHub CI | Yes | No — runs tests locally |
| Pushes commits to GitHub | Yes | No |
| Machine must stay on | No | Yes |
| Reads CLAUDE.md | Very likely yes | Yes |

---

### `/install-github-app`
Set up the Claude GitHub Actions app for a repository — walks through selection and configuration.

**Example:**
```
/install-github-app
```

**What it does:**

Installs the **Claude GitHub App** on your repository — a one-time setup that grants Claude's cloud infrastructure permission to interact with your GitHub repo on your behalf. Without this, remote commands like `/autofix-pr` have no way to read CI logs, watch PR status, or push commits.

**What the app gets permission to do:**

| Permission | Why needed |
|---|---|
| Read repository code | To understand what to fix |
| Read pull requests & review comments | To know what needs addressing |
| Read CI check runs & logs | To see what failed and why |
| Write to repository (push commits) | To push the fixes it makes |

**Setup flow:**

```
/install-github-app
  │
  ├─ Opens GitHub OAuth flow in browser
  ├─ You select which repo(s) to install on
  │    (one repo, multiple repos, or entire org)
  ├─ GitHub asks you to approve the permissions
  └─ App is installed — Claude's cloud can now access the repo
```

This is a **one-time setup per repo**. You don't need to repeat it each time you use `/autofix-pr`.

**Scope — repo vs. org:**

| Level | Effect |
|---|---|
| Single repo | Only that repo gets Claude access |
| Organization | All repos in the org get Claude access |

Start with a single repo to test, then expand to the org if you want it everywhere.

**Which commands depend on it:**

| Command | Needs GitHub App? |
|---|---|
| `/autofix-pr` | **Yes** — can't watch CI or push fixes without it |
| `/review` (local PR) | No |
| `/schedule` (if touching GitHub) | Depends on the task |

**`/install-github-app` vs `/web-setup`:**

These are often confused but serve different purposes:

| Command | What it connects | Used for |
|---|---|---|
| `/install-github-app` | GitHub App → your repo | Gives Claude cloud permission to read/write your repo |
| `/web-setup` | Your local `gh` CLI → claude.ai | Lets the claude.ai web UI know your GitHub identity |

`/install-github-app` is the one that matters for `/autofix-pr`.

---

## Project Configuration

### `/init`
Initialize a new `CLAUDE.md` file with codebase documentation to guide Claude in future sessions.

**Example 1:** First time setting up Claude in a new project.
```
/init
```

**What `/init` actually does:**

`/init` is not a blank-template generator. It **scans your codebase** and auto-generates a populated `CLAUDE.md` with real information derived from your project. The result is a working file, not a skeleton to fill in manually.

What it reads from your project and writes into `CLAUDE.md`:

| What it detects | Example output in CLAUDE.md |
|---|---|
| Build tool and commands | `Build: mvn clean package` / `npm run build` |
| Test runner and commands | `Test: mvn test` / `pytest tests/` / `npm test` |
| Project structure summary | Main packages, entry points, key directories |
| Architecture overview | MVC layout, microservices structure, layering |
| Coding conventions in use | Naming patterns, import style, annotation usage |

**Internal flow:**

```
/init
  │
  ├─ SCAN    → reads project files, build configs, source structure
  │
  ├─ GENERATE → writes CLAUDE.md with detected commands and conventions
  │
  └─ OPEN    → opens the generated file for you to review and edit
```

After `/init`, use `/memory` to open and edit it further — add team rules, forbidden patterns, or anything project-specific that `/init` couldn't infer automatically.

**Can `/init` create CLAUDE.md in subdirectories?**

**Yes.** Run `/init` from inside the subdirectory and it generates a `CLAUDE.md` scoped to that location.

For a monorepo, run it once per package or service:

```
my-monorepo/
  CLAUDE.md                      ← /init from root — repo-wide conventions
  services/
    auth-service/
      CLAUDE.md                  ← /init from here — auth-service specific
    payment-service/
      CLAUDE.md                  ← /init from here — payment-service specific
```

Each subdirectory CLAUDE.md can contain conventions specific to that package — different test commands, different build flags, different code patterns — without polluting the root file.

**How Claude reads CLAUDE.md files (hierarchical merging):**

Claude reads and merges **all** CLAUDE.md files it finds, from outermost to innermost:

```
~/.claude/CLAUDE.md              ← 1st — your personal user-level rules (all projects)
my-monorepo/CLAUDE.md            ← 2nd — project root rules
my-monorepo/services/auth/CLAUDE.md ← 3rd — subdirectory rules (most specific)
```

All three are merged. Deeper files **add to** the root, they don't override or replace it. Claude sees all of them at once.

This means:
- Put repo-wide conventions in the root `CLAUDE.md`
- Put package-specific exceptions or additions in subdirectory `CLAUDE.md` files
- Put personal rules that apply to all your projects in `~/.claude/CLAUDE.md`

**After `/init` — edit with `/memory`:**

```
/init      # generate the CLAUDE.md
/memory    # open it to add team rules, constraints, forbidden patterns
```

---

### `/memory`
Edit `CLAUDE.md` memory files, enable/disable auto-memory, and view auto-memory entries.

**Example 1:** Update project conventions Claude should follow.
```
/memory
```

**What it opens:**

Running `/memory` opens an **interactive editor** that gives you access to multiple CLAUDE.md files at once:

```
/memory
  │
  ├─ ~/.claude/CLAUDE.md              ← user-level (all your projects)
  ├─ <project-root>/CLAUDE.md         ← project-level (this repo)
  └─ <subdirectory>/CLAUDE.md         ← subdirectory-level (if you're in one)
```

You navigate between them with tabs. Edits take effect immediately — the next prompt in this session or any future session will follow the updated rules.

**What to put in CLAUDE.md:**

CLAUDE.md is free-form markdown. Common sections:

```markdown
## Build & Test Commands
- Build: mvn clean package -DskipTests
- Test: mvn test
- Lint: npm run lint

## Architecture
- Services communicate via Kafka, not direct HTTP
- All DB access goes through the repository layer, never from controllers

## Code Conventions
- Java: constructor injection only, never @Autowired on fields
- No raw SQL strings — always parameterized queries
- All public methods need a Javadoc summary

## Forbidden Patterns
- Never use System.out.println — use the logger
- No Thread.sleep() in production code
- Never commit .env files

## Review Rules
- Never change test assertions to make tests pass — fix the implementation
- Do not auto-format files outside the PR diff
```

**Auto-memory vs. manual memory:**

`/memory` also controls **auto-memory** — Claude's ability to save observations on its own without you asking.

| Type | What it is | How to edit |
|---|---|---|
| Manual memory | Rules you write directly in CLAUDE.md | `/memory` → edit the file |
| Auto-memory | Facts Claude inferred and saved itself | `/memory` → view and delete auto-memory entries |

Auto-memory entries look like:
```
[auto] User prefers constructor injection over field injection
[auto] Build command is: mvn clean package
[auto] Tests run with: pytest tests/ -v
```

From the `/memory` interface you can delete any auto-memory entry you don't want Claude carrying forward.

**User-level vs. project-level:**

| File | Scope | Use for |
|---|---|---|
| `~/.claude/CLAUDE.md` | All your projects | Personal preferences, tools you always use, style rules |
| `<project>/CLAUDE.md` | This project only | Team conventions, build commands, architecture rules |
| `<subdir>/CLAUDE.md` | This package/service | Package-specific commands or exceptions |

A rule in `~/.claude/CLAUDE.md` applies everywhere. A rule in the project root applies only to that repo. Both are active at the same time — Claude merges all of them.

**Practical workflow:**

```
/init      # generates CLAUDE.md from codebase scan — good starting point
/memory    # open to refine: add team rules, delete wrong auto-inferences
```

For a rule you want to persist across all future sessions:
```
# Instead of repeating "always use constructor injection" every session:
/memory    # add it once → applies to all future sessions automatically
```

**Key distinction — `/memory` vs. session context:**

`/memory` edits **persistent files on disk** — rules that survive across sessions. The session context (what Claude remembers from the current conversation) is separate and controlled by `/compact`, `/clear`, and `/resume`. They don't overlap.

**Do you need `/memory` to edit CLAUDE.md — can't you just ask Claude?**

You can just say "add this rule to CLAUDE.md" and Claude will edit the file directly. `/memory` is not required. It adds three things over asking Claude directly:

1. **Tabbed view of all levels at once** — rather than asking Claude to open each level separately, `/memory` shows `~/.claude/CLAUDE.md`, project root, and subdirectory all in one interface with tabs. Useful when deciding which level a rule belongs at.
2. **Auto-memory management** — auto-memory entries are stored separately from CLAUDE.md and cannot be edited by asking Claude to "open CLAUDE.md." `/memory` is the only way to see and delete them.
3. **Direct editor control** — `/memory` opens the file in your editor so you have full manual control without Claude as an intermediary.

For simple edits, asking Claude directly is fine and often faster. Use `/memory` when you need to manage auto-memory entries or want the multi-level tabbed view.

**What to consider for auto-memory:**

Auto-memory fires when Claude notices something during a session worth persisting — but it uses judgment, and that judgment can be wrong.

Things Claude auto-saves correctly:
- Build and test commands it discovered: `mvn clean package`, `pytest tests/ -v`
- Style corrections you gave mid-session: "don't use `var` in Java"
- Factual project structure: "main entry point is `Application.java`"

Things Claude sometimes auto-saves badly:
- **Overly specific one-off decisions**: "for this PR, use the legacy API" — now saved as a permanent rule
- **Temporarily true context**: "we're on a feature freeze this week"
- **Wrong inferences**: guessing your test command incorrectly from a config file scan

What to do: after any long session where Claude was doing significant work, open `/memory` and scan the `[auto]` entries. Ask yourself — is this still true? Was this task-specific, not a permanent rule? Is it accurate? Delete anything that doesn't apply universally. Takes 30 seconds and prevents compounding confusion across future sessions.

---

### `/add-dir`
Add an additional working directory for file access in the current session.

**Example 1:** Access a shared library repo while working on your main app.
```
/add-dir ../shared-utils
```

**The problem it solves:**

By default, Claude Code can only read and write files within the directory you launched it from. If your app imports from a sibling library, Claude can see the import statement but not the library's source files.

```
repos/
  my-app/          ← Claude launched here, can see this
  shared-utils/    ← Claude CANNOT see this by default
```

After `/add-dir ../shared-utils`:
```
repos/
  my-app/          ← Claude can see this
  shared-utils/    ← Claude can now also see this
```

**What it changes and what it doesn't:**

Changes: the set of files Claude can read and edit.

Does NOT change:
- The **working directory** — where shell commands run and where `git` operates
- Which **CLAUDE.md files** are loaded (those are based on working directory, not added dirs)
- **Session persistence** — added directories are forgotten when the session ends

**Common use cases:**

```
# Working across a monorepo from one service
/add-dir ../../packages/api-types

# Referencing a shared config library while editing an app
/add-dir ../company-eslint-config

# Two related repos side by side
/add-dir ../backend-repo   # frontend session can now read backend types
```

**Multiple directories:** You can add more than one, each call expands access further:
```
/add-dir ../shared-utils
/add-dir ../api-contracts
/add-dir ../../platform/core
```

**Persistence:** `/add-dir` is session-only. When the session ends, the added directories are gone. There is no way to make them permanent — if you always need access to a sibling directory, either start Claude Code from a common parent directory, or note the `/add-dir` command in your CLAUDE.md as a reminder to run at session start.

**`/add-dir` vs. launching from a parent directory:**

| Approach | Working dir | Git scope | CLAUDE.md loaded |
|---|---|---|---|
| Launch from `my-app/`, `/add-dir ../shared-utils` | `my-app/` | `my-app/` git | `my-app/CLAUDE.md` |
| Launch from `repos/` (parent) | `repos/` | `repos/` git | `repos/CLAUDE.md` |

If the two directories are separate git repos, launching from the parent is usually wrong — git commands would operate at the wrong level. `/add-dir` keeps the correct working directory while expanding read/write access.

---

### `/mcp`
Manage MCP (Model Context Protocol) server connections and OAuth authentication.

**Example 1:** Add a Postgres MCP server for direct database access.
```
/mcp
```

---

### `/permissions`
Manage allow/ask/deny rules for tool permissions. Interactive dialog with rule management.

**Example 1:** Permanently allow npm commands without prompting.
```
/permissions
```

---

### `/hooks`
View hook configurations that execute on tool events.

**Example:**
```
/hooks
```

---

## Utilities & Tools

### `/copy`
Copy the last assistant response to clipboard. Pass a number to copy the Nth-latest response.

**Example 1:** Copy Claude's last code block to paste into your editor.
```
/copy
```

**Example 2:** Copy the second-to-last response.
```
/copy 2
```

---

### `/export`
Export the current conversation as plain text. Useful for sharing session context with a teammate as a read-only reference — they get the full history but cannot resume it as a live session. See [Sharing Sessions with Teammates](#sharing-sessions-with-teammates-cross-machine) for other sharing options.

**Example 1:** Save the session as a reference doc.
```
/export refactor-session-2026-05-17.txt
```

---

### `/btw`
Ask a quick side question without polluting conversation history.

**Example 1:** Check a fact without derailing the current task.
```
/btw what's the current git commit SHA?
```

**Example 2:** Quick syntax lookup.
```
/btw what's the PowerShell equivalent of grep -r?
```

---

### `/recap`
Generate a one-line summary of the current session.

**Example:**
```
/recap
```

---

## Help & Diagnostics

### `/help`
Show available commands and usage information.

**Example:**
```
/help
```

---

### `/doctor`
Diagnose and verify your Claude Code installation and settings. Press `f` to auto-fix issues.

**Example 1:** Something feels off after an update — run a health check.
```
/doctor
```

---

### `/status`
Open the Settings interface showing version, model, account, and connectivity status.

**Example:**
```
/status
```

---

### `/usage`
Show session cost, plan usage limits, and activity statistics. Aliases: `/cost`, `/stats`.

**Example 1:** Check how much of your monthly quota you've used.
```
/usage
```

---

### `/debug`
Enable debug logging and troubleshoot issues. Optionally describe the problem.

**Example 1:** Session keeps freezing — enable debug logging to investigate.
```
/debug session freezing after large file reads
```

---

### `/feedback`
Submit feedback or a bug report. Alias: `/bug`.

**Example:**
```
/feedback /compact seems to lose important context when used mid-task
```

---

### `/heapdump`
Write a JavaScript heap snapshot to your Desktop for diagnosing high memory usage.

**Example:**
```
/heapdump
```

---

### `/insights`
Generate a report analyzing your Claude Code usage patterns, friction points, and project areas.

**Example:**
```
/insights
```

---

### `/release-notes`
View the changelog with an interactive version picker.

**Example:**
```
/release-notes
```

---

## Settings & Configuration

### `/config`
Open the Settings interface to adjust theme, model, output style, and preferences. Alias: `/settings`.

**Example:**
```
/config
```

---

### `/theme`
Change the color theme: auto, light, dark, colorblind/daltonized, ANSI, or custom.

**Example 1:** Switch to dark theme for a night session.
```
/theme
```

---

### `/keybindings`
Open or create the keybindings configuration file.

**Example:**
```
/keybindings
```

---

### `/tui`
Set the terminal UI renderer. `fullscreen` gives flicker-free alt-screen rendering.

**Example 1:** Eliminate terminal flickering.
```
/tui fullscreen
```

---

### `/focus`
Toggle focus view — shows only the last prompt, a tool-call summary, and the final response.

**Example:**
```
/focus
```

---

### `/statusline`
Configure Claude Code's status line in your shell prompt.

**Example 1:** Show git branch and token usage in the status line.
```
/statusline show git branch and token usage
```

---

## IDE & Platform Integration

### `/ide`
Manage IDE integrations and show status (VS Code, JetBrains, Cursor, etc.).

**Example:**
```
/ide
```

---

### `/terminal-setup`
Configure terminal keybindings for Shift+Enter and other shortcuts for your specific terminal/IDE.

**Example 1:** First time setting up Claude Code in VS Code's integrated terminal.
```
/terminal-setup
```

---

### `/desktop`
Continue the current session in the Claude Code Desktop app. Alias: `/app`.

**Example:**
```
/desktop
```

---

### `/voice`
Toggle voice dictation or set the mode (`hold`, `tap`, `off`). Requires a Claude.ai account.

**Example 1:** Dictate prompts hands-free while reading code.
```
/voice tap
```

---

### `/remote-control`
Make your session available for remote control from claude.ai. Alias: `/rc`. This is the easiest way to share a live session with a teammate on a different machine — they can observe and take over from their browser. See [Sharing Sessions with Teammates](#sharing-sessions-with-teammates-cross-machine) for other sharing options.

**Example 1:** Let a teammate observe and take over your session.
```
/remote-control
```

---

## Account & Authentication

### `/login`
Sign in to your Anthropic account.

**Example:**
```
/login
```

---

### `/logout`
Sign out from your Anthropic account.

**Example:**
```
/logout
```

---

### `/upgrade`
Open the upgrade page to switch to a higher plan tier.

**Example:**
```
/upgrade
```

---

### `/setup-bedrock`
Configure Amazon Bedrock authentication (interactive wizard). Only visible when `CLAUDE_CODE_USE_BEDROCK=1` is set.

**Example:**
```
/setup-bedrock
```

---

### `/setup-vertex`
Configure Google Vertex AI authentication (interactive wizard). Only visible when `CLAUDE_CODE_USE_VERTEX=1` is set.

**Example:**
```
/setup-vertex
```

---

## Cloud & Remote

### `/ultraplan`
Draft a plan in an ultraplan session, review it in the browser, then execute remotely or send back to your terminal.

**Example 1:** Plan a large schema migration interactively in the browser before running it.
```
/ultraplan migrate the database schema to support multi-tenancy
```

---

### `/web-setup`
Connect your GitHub account to Claude Code on the web using local `gh` CLI credentials.

**Example:**
```
/web-setup
```

---

### `/teleport`
Pull a Claude Code web session into your terminal. Opens a picker, fetches branch and conversation. Requires a Claude.ai subscription.

**Example 1:** Continue in your terminal a session you started on claude.ai.
```
/teleport
```

---

## Miscellaneous

### `/exit`
Exit the Claude Code CLI. In an attached background session, detaches without stopping it. Alias: `/quit`.

**Example:**
```
/exit
```

---

### `/powerup`
Discover Claude Code features through interactive lessons with animated demos.

**Example 1:** Onboarding to Claude Code for the first time.
```
/powerup
```

---

### `/skills`
List available skills and manage which ones are active. Press `t` to sort by token count.

**Example:**
```
/skills
```

---

### `/plugin`
Manage Claude Code plugins (install, uninstall, configure).

**Example:**
```
/plugin
```

---

### `/reload-plugins`
Reload active plugins to apply changes without restarting the session.

**Example:**
```
/reload-plugins
```

---

### `/team-onboarding`
Generate a team onboarding guide from the last 30 days of usage history. Returns a shareable link.

**Example 1:** Onboard a new engineer to your Claude Code workflows.
```
/team-onboarding
```

---

### `/privacy-settings`
View and update your privacy settings (Pro and Max plans only).

**Example:**
```
/privacy-settings
```

---

### `/extra-usage`
Configure extra usage to keep working when plan rate limits are hit.

**Example:**
```
/extra-usage
```

---

### `/radio`
Open Claude FM lo-fi radio in the browser while you code.

**Example:**
```
/radio
```

---

### `/mobile`
Show a QR code to download the Claude mobile app. Aliases: `/ios`, `/android`.

**Example:**
```
/mobile
```

---

### `/stickers`
Order Claude Code stickers.

**Example:**
```
/stickers
```

---

## Quick Reference by Use Case

| Scenario | Commands to Use |
|----------|----------------|
| **New project setup** | `/init` → `/memory` → `/mcp` → `/permissions` |
| **Active development** | `/plan` → `/model` → `/effort` → `/context` → `/compact` |
| **Before committing** | `/diff` → `/review` → `/security-review` → `/simplify` |
| **Large-scale refactor** | `/ultraplan` → `/batch` |
| **Long running task** | `/goal` or `/background` |
| **Debugging problems** | `/doctor` → `/debug` → `/heapdump` |
| **Context running low** | `/context` → `/compact` |
| **CI automation** | `/autofix-pr` or `/loop` |
| **Session management** | `/rename` → `/branch` → `/resume` |
| **Check costs** | `/usage` |

---

## MCP Dynamic Commands

MCP servers can expose prompts that appear as slash commands:

```
/mcp__<server-name>__<prompt-name>
```

**Example:** If you connect a Postgres MCP server, it might expose:
```
/mcp__postgres__describe-schema
```

These are auto-discovered from connected MCP servers via `/mcp`.

---

> **Tip:** Type `/` alone at the prompt to see all commands filtered for your current platform, plan, and environment.
