# Claude Code — Harness, Compaction & JSONL Reference

---

## The Harness

### What it is

The harness is the **Claude Code runtime** — the infrastructure layer that sits between you and Claude. You never talk to Claude directly. The harness mediates everything.

```
You (user)
    │
    ▼
┌─────────────────────────────────────────┐
│              HARNESS                    │
│         (Claude Code runtime)           │
│                                         │
│  - assembles the system prompt          │
│  - injects CLAUDE.md, listings          │
│  - executes tools on Claude's behalf    │
│  - spawns and manages sub-agents        │
│  - sends task notifications             │
│  - triggers compaction                  │
│  - writes session JSONL files           │
│  - executes hooks                       │
│  - connects MCP servers                 │
│  - manages permission prompts           │
└─────────────────┬───────────────────────┘
                  │
                  ▼
              Claude (LLM)
```

### What the harness does

| Responsibility | Detail |
|---|---|
| System prompt assembly | Combines tool defs + skill listing + command listing + CLAUDE.md → sends to Claude |
| Tool execution | When Claude calls `Bash`, harness actually runs the shell command and returns result |
| Sub-agent spawning | Creates isolated Claude instances, assigns agent IDs, manages lifecycle |
| Task notifications | Injects `<task-notification>` into Claude's context when agents complete |
| Compaction | Monitors context size, triggers summarization automatically or on demand |
| Session tracking | Writes every message as JSONL entries in real time |
| Hook execution | Runs shell commands on events (pre-tool, post-tool, session-start, etc.) |
| MCP management | Starts MCP servers, registers their tools into Claude's context |
| Permission prompts | Intercepts tool calls, prompts user to approve/deny |

### Key distinction

```
Claude knows:     what is currently in its context
Harness controls: what gets INTO that context and when
You control:      CLAUDE.md, skills, commands, settings, hooks
```

### Concrete example — tool execution

```
What you see:  Claude ran `git log`

Reality:
  Claude  → "I want to call Bash({ command: 'git log' })"
  Harness → checks permissions (prompts user if needed)
  Harness → actually executes git log in your shell
  Harness → sends stdout result back to Claude
  Claude  → reads result, formulates response
```

### Concrete example — task notification

```
What you see:  notification "Agent X done"

Reality:
  Sub-agent completes its task
  Harness → writes empty marker to .output file
  Harness → injects <task-notification> XML into Claude's context
  Claude  → reads notification content, reports to user
```

---

## Compaction

### What compaction is

Compaction is the process of **compressing conversation history** to free up context space. It replaces raw message history with a summarized version so the session can continue without hitting the context limit.

### The three context zones

```
┌─────────────────────────────────────────────────────┐
│  ZONE 1 — SYSTEM PROMPT (always intact)             │
│  Harness discards nothing here — re-injects fresh   │
├─────────────────────────────────────────────────────┤
│  ZONE 2 — CONVERSATION HISTORY (summarized)         │
│  Claude summarizes this into a compressed block     │
├─────────────────────────────────────────────────────┤
│  ZONE 3 — RECENT MESSAGES (preserved as-is)         │
│  Last N messages kept raw to maintain continuity    │
└─────────────────────────────────────────────────────┘
```

### What happens to each component during compaction

| Component | Zone | Survives? | Detail |
|---|---|---|---|
| Harness instructions | 1 | Yes — intact | Re-injected fresh |
| Tool definitions | 1 | Yes — intact | Re-injected fresh |
| Skill listing (names) | 1 | Yes — intact | Re-injected fresh |
| Command listing (names) | 1 | Yes — intact | Re-injected fresh |
| CLAUDE.md (all loaded) | 1 | Yes — intact | Re-injected fresh |
| MCP tool definitions | 1 | Yes — intact | Re-injected fresh |
| Skill content (injected) | 2 | Summarized | Detail lost |
| Command content (injected) | 2 | Summarized | Detail lost |
| Tool results (Bash, Read) | 2 | Summarized | Detail lost |
| Sub-agent results | 2 | Summarized | Detail lost |
| Earlier conversation | 2 | Summarized | Key points kept |
| Intermediate reasoning | 2 | Likely lost | Not deemed important |
| Long verbose outputs | 2 | Heavily compressed | Raw detail gone |
| Recent messages | 3 | Yes — intact | Last N kept raw |

### Before vs after compaction

```
BEFORE:
  [system prompt — 20k tokens]
  [message 1: user question]
  [message 2: claude reads 500 lines of code → full content]
  [message 3: skill content → full SKILL.md body]
  [message 4: agent result → full JSON blob]
  [message 5: claude response with reasoning]
  ... 50 more messages ...
  [message 55: current exchange]

AFTER:
  [system prompt — 20k tokens]        ← identical, re-injected fresh
  [SUMMARY: "Earlier in this session  ← replaces messages 1-52 (lossy)
    Claude read auth.ts and found X.
    release-notes skill was invoked.
    Agent returned 3 features, 2 fixes.
    Decision made to use format Y..."]
  [message 53: recent raw]            ← last few kept intact
  [message 54: recent raw]
  [message 55: current exchange]
```

### What the summary preserves vs loses

| Likely preserved | Likely lost |
|---|---|
| Key decisions made | Raw file contents that were read |
| Important findings | Full tool output details |
| Current task goal | Intermediate reasoning steps |
| Errors encountered | Skill/command full instructions |
| Current state of work | Verbose agent result details |

---

## Auto-Compaction

### How it triggers

```
Context usage grows during session
        │
        ▼
Approaches the autocompact buffer threshold
        │
        ▼
Harness automatically summarizes conversation history
        │
        ▼
Summary replaces raw history, system prompt re-injected
        │
        ▼
Context usage drops — session continues
```

### The autocompact buffer

From `/context` output:
```
Tokens:             20.7k / 200k  (10%)
Free space:         146.3k        (73.1%)
Autocompact buffer:   33k         (16.5%)   ← compaction zone
```

When conversation history fills enough to push into the 33k buffer, auto-compaction triggers. The buffer is reserved headroom the harness uses to perform the compaction itself.

### Auto-compaction characteristics

- Triggers automatically — no user input
- No custom instructions possible
- Harness decides what to summarize
- You cannot influence what gets kept or discarded
- Happens mid-session, potentially mid-workflow

### Mitigation for auto-compaction

Write critical data to files instead of holding it in context:

```
# Risky — lives in conversation history, lost to compaction
result = Agent({ prompt: "parse commits" })
# result only exists in context now

# Safe — written to disk, survives any compaction
result = Agent({ prompt: "parse commits, write results to commits.json" })
# compaction can't lose it
```

In your supervisor prompt, instruct sub-agents to write intermediate results to files immediately after completing their task.

---

## Manual Compaction

### Basic usage

```
/compact
```

Default behavior — harness decides what to summarize.

### With custom instructions

```
/compact <your instructions here>
```

Instructions guide Claude on **how** to compact — what to retain, summarize, or discard entirely.

### Influencing compaction — examples

**Discard skill/command content entirely:**
```
/compact discard all skill and command content that was injected, do not summarize it
```

**Retain only structured data:**
```
/compact retain only the final JSON results from each agent, discard all intermediate tool outputs and skill content
```

**Keep decisions, drop everything else:**
```
/compact keep only key decisions made and current task state, discard all file contents, tool outputs, and skill injections
```

**Task-focused:**
```
/compact we are generating release notes for v2.1.0, retain only commit data and version info, discard everything else
```

**Retain data, drop instructions:**
```
/compact retain all JSON results from sub-agents, discard skill content, command content, and raw tool outputs
```

### What you can and cannot influence

| Instruction | Effect |
|---|---|
| `discard skill content` | Skill injections dropped, not summarized |
| `discard tool outputs` | Raw Bash/Read results dropped |
| `retain only JSON results` | Sub-agent outputs kept, rest dropped |
| `retain current task state` | Context of what you're doing preserved |
| `focus on X` | Summary biased toward topic X |
| `discard everything before step N` | Earlier work dropped entirely |

| Thing | Can you influence? | Why |
|---|---|---|
| Zone 1 (system prompt) | No | Harness re-injects regardless |
| Skill/command listings | No | Always re-injected fresh |
| CLAUDE.md | No | Always re-injected fresh |
| Conversation history | Yes | This is what compaction operates on |

---

## JSONL Logs

### Every agent has its own JSONL log

| Agent | Log location |
|---|---|
| Main agent | `~/.claude/projects/<project>/<session-uuid>.jsonl` |
| Sub-agent | `~/.claude/projects/<project>/<session-uuid>/subagents/agent-<id>.jsonl` |
| Global history | `~/.claude/history.jsonl` |

### Entry chain structure

Each line is a JSON object. Entries form a **linked list** via `parentUuid` → `uuid`:

```
Line 1: uuid=A, parentUuid=null      ← first entry
Line 2: uuid=B, parentUuid=A
Line 3: uuid=C, parentUuid=B
Line 4: uuid=D, parentUuid=C
```

### Entry types

| `type` | When it appears |
|---|---|
| `user` | Your message OR tool result returned (both use user role) |
| `assistant` | Claude's response — text output or tool call |
| `attachment` | System injections — skill_listing, deferred_tools_delta |
| `ai-title` | Session title generated by Claude |
| `last-prompt` | Marker for the last user message |
| `summary` / `compaction` | Appears after compaction event |

### Detailed entry breakdown

#### Line 1 — `type: user` (the prompt)

```json
{
  "type": "user",
  "parentUuid": null,
  "uuid": "e2691ba0-6218-4e0e-8a18-3cc81fd5f999",
  "agentId": "a24a6d75d2dc760f4",
  "isSidechain": true,
  "promptId": "9ae89daa-179b-43a5-aa67-97861dc1ff25",
  "sessionId": "f5e1fe45-fc4a-4469-9f1a-da823cd1819b",
  "message": {
    "role": "user",
    "content": "You are simulating a database migration task..."
  },
  "timestamp": "2026-05-16T05:20:48.688Z",
  "userType": "external",
  "entrypoint": "cli",
  "cwd": "C:\\Users\\guhar",
  "version": "2.1.143",
  "gitBranch": "HEAD",
  "slug": "peppy-orbiting-puppy"
}
```

#### Line 2 — `type: attachment` / `deferred_tools_delta` (tools injected)

```json
{
  "type": "attachment",
  "attachment": {
    "type": "deferred_tools_delta",
    "addedNames": [
      "EnterWorktree", "ExitWorktree", "Monitor",
      "NotebookEdit", "TaskStop", "WebFetch", "WebSearch"
    ],
    "removedNames": [],
    "readdedNames": []
  }
}
```

#### Line 3 — `type: attachment` / `skill_listing` (skills injected)

```json
{
  "type": "attachment",
  "attachment": {
    "type": "skill_listing",
    "skillCount": 10,
    "isInitial": true,
    "content": "- update-config: Use this skill...\n- review: Review a pull request..."
  }
}
```

#### Line 4 — `type: assistant` (Claude calls a tool)

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "model": "claude-sonnet-4-6",
    "content": [{
      "type": "tool_use",
      "id": "toolu_011tRC1aR6FkxsnapFNok53P",
      "name": "Bash",
      "input": {
        "command": "sleep 5 && echo \"DB migration complete\"",
        "description": "Run simulated database migration command"
      },
      "caller": { "type": "direct" }
    }],
    "stop_reason": null,
    "usage": {
      "input_tokens": 3,
      "cache_creation_input_tokens": 11250,
      "cache_read_input_tokens": 0,
      "output_tokens": 59
    }
  },
  "requestId": "req_011Cb5gigm6xgCr3HUTM8a7y"
}
```

#### Line 5 — `type: user` (tool result returned)

```json
{
  "type": "user",
  "message": {
    "role": "user",
    "content": [{
      "type": "tool_result",
      "tool_use_id": "toolu_011tRC1aR6FkxsnapFNok53P",
      "content": "DB migration complete: 42 tables migrated, 0 errors",
      "is_error": false
    }]
  },
  "sourceToolAssistantUUID": "2ad4e8d5-e27a-4ca5-a4f5-d122eccc3af6"
}
```

#### Line 6 — `type: assistant` (final response)

```json
{
  "type": "assistant",
  "message": {
    "role": "assistant",
    "content": [{
      "type": "text",
      "text": "The command completed successfully. Output:\n\nDB migration complete..."
    }],
    "stop_reason": "end_turn",
    "usage": {
      "input_tokens": 1,
      "cache_creation_input_tokens": 126,
      "cache_read_input_tokens": 11250,
      "output_tokens": 26
    }
  }
}
```

### Common fields in every entry

| Field | Meaning |
|---|---|
| `uuid` | Unique ID of this entry |
| `parentUuid` | Previous entry UUID — forms the linked chain |
| `type` | Entry type: `user`, `assistant`, `attachment` |
| `isSidechain` | `true` = sub-agent log, `false` = main agent log |
| `agentId` | Which sub-agent this entry belongs to |
| `sessionId` | Parent session UUID |
| `promptId` | Links sub-agent back to parent agent's originating prompt |
| `timestamp` | ISO 8601 timestamp when entry was written |
| `slug` | Human-readable session name (e.g. `peppy-orbiting-puppy`) |
| `version` | Claude Code version that wrote this entry |
| `cwd` | Working directory at time of entry |
| `entrypoint` | How Claude Code was launched (`cli`, `desktop`, etc.) |

### Token usage fields

| Field | Meaning |
|---|---|
| `input_tokens` | Fresh tokens sent in this API request |
| `cache_creation_input_tokens` | Tokens written to prompt cache (for reuse) |
| `cache_read_input_tokens` | Tokens read from cache — cheaper than fresh |
| `output_tokens` | Tokens Claude generated in response |

Cache hits (`cache_read_input_tokens > 0`) mean Claude reused a previously cached system prompt — significant cost saving on repeated agent calls.

---

## Searching JSONL Logs

### Session file paths

```powershell
# Windows — current session
$env:USERPROFILE\.claude\projects\C--Users-guhar\<session-uuid>.jsonl

# Windows — sub-agent logs
$env:USERPROFILE\.claude\projects\C--Users-guhar\<session-uuid>\subagents\agent-<id>.jsonl

# Linux/Mac — current session
~/.claude/projects/<project-slug>/<session-uuid>.jsonl

# Linux/Mac — sub-agent logs
~/.claude/projects/<project-slug>/<session-uuid>/subagents/agent-<id>.jsonl
```

---

### Zone 1 — System prompt components

**Windows (PowerShell):**
```powershell
# Skill listing injections
Select-String -Path "$env:USERPROFILE\.claude\projects\C--Users-guhar\*.jsonl" -Pattern '"type":"skill_listing"'

# Tool additions
Select-String -Path "$env:USERPROFILE\.claude\projects\C--Users-guhar\*.jsonl" -Pattern '"type":"deferred_tools_delta"'

# All system attachments
Select-String -Path "$env:USERPROFILE\.claude\projects\C--Users-guhar\*.jsonl" -Pattern '"type":"attachment"'
```

**Linux/Mac:**
```bash
# Skill listing injections
grep '"type":"skill_listing"' ~/.claude/projects/**/*.jsonl

# Tool additions
grep '"type":"deferred_tools_delta"' ~/.claude/projects/**/*.jsonl

# All attachments — pretty print with jq
cat session.jsonl | jq 'select(.type == "attachment")'
```

---

### Zone 2 — Compaction / summary entries

**Windows (PowerShell):**
```powershell
# Find compaction events
Select-String -Path "$env:USERPROFILE\.claude\projects\C--Users-guhar\*.jsonl" -Pattern '"type":"summary"'
Select-String -Path "$env:USERPROFILE\.claude\projects\C--Users-guhar\*.jsonl" -Pattern '"type":"compaction"'

# Any compaction-related entry
Select-String -Path "$env:USERPROFILE\.claude\projects\C--Users-guhar\*.jsonl" -Pattern 'compaction|summary|compressed'
```

**Linux/Mac:**
```bash
# Find compaction events
grep '"type":"summary"' ~/.claude/projects/**/*.jsonl
grep '"type":"compaction"' ~/.claude/projects/**/*.jsonl

# Pretty print with jq
cat session.jsonl | jq 'select(.type == "summary" or .type == "compaction")'
```

---

### Zone 3 — Recent raw messages

**Windows (PowerShell):**
```powershell
# Last 10 entries
Get-Content "$env:USERPROFILE\.claude\projects\C--Users-guhar\<uuid>.jsonl" | Select-Object -Last 10

# Last 10 user messages
Select-String -Path "session.jsonl" -Pattern '"type":"user"' | Select-Object -Last 10

# Last 10 assistant messages
Select-String -Path "session.jsonl" -Pattern '"type":"assistant"' | Select-Object -Last 10
```

**Linux/Mac:**
```bash
# Last 10 entries
tail -10 session.jsonl

# Last 10 user messages
grep '"type":"user"' session.jsonl | tail -10

# Last 10 assistant messages — pretty print
grep '"type":"assistant"' session.jsonl | tail -5 | jq '{type, timestamp, stop_reason: .message.stop_reason}'
```

---

### Skill and command invocations

**Windows (PowerShell):**
```powershell
# Skill invocations
Select-String -Path "session.jsonl" -Pattern '"name":"Skill"'

# Command invocations
Select-String -Path "session.jsonl" -Pattern '"name":"Command"'
```

**Linux/Mac:**
```bash
# Skill invocations
grep '"name":"Skill"' session.jsonl

# Command invocations
grep '"name":"Command"' session.jsonl

# Pretty print skill calls with jq
cat session.jsonl | jq 'select(.message.content[]?.name == "Skill") | .message.content[]'
```

---

### Tool calls and results

**Windows (PowerShell):**
```powershell
# All tool calls
Select-String -Path "session.jsonl" -Pattern '"type":"tool_use"'

# Specific tool (e.g. Bash)
Select-String -Path "session.jsonl" -Pattern '"name":"Bash"'

# Failed tool calls
Select-String -Path "session.jsonl" -Pattern '"is_error":true'

# All tool results
Select-String -Path "session.jsonl" -Pattern '"type":"tool_result"'
```

**Linux/Mac:**
```bash
# All tool calls
grep '"type":"tool_use"' session.jsonl

# Specific tool
grep '"name":"Bash"' session.jsonl

# Failed tool calls
grep '"is_error":true' session.jsonl

# Pretty print all tool calls
cat session.jsonl | jq 'select(.message.content[]?.type == "tool_use") | .message.content[] | {name, input}'
```

---

### Agent-specific searches

**Windows (PowerShell):**
```powershell
# Count sub-agents spawned in session
(Get-ChildItem "$env:USERPROFILE\.claude\projects\C--Users-guhar\<uuid>\subagents\").Count

# List all sub-agent IDs and timestamps
Get-ChildItem "$env:USERPROFILE\.claude\projects\C--Users-guhar\<uuid>\subagents\" |
  Select-Object Name, LastWriteTime

# Find entries for a specific agent
Select-String -Path "session.jsonl" -Pattern '"agentId":"a24a6d75d2dc760f4"'

# Find all agent spawn calls (Agent tool use)
Select-String -Path "session.jsonl" -Pattern '"name":"Agent"'
```

**Linux/Mac:**
```bash
# Count sub-agents spawned
ls ~/.claude/projects/<slug>/<uuid>/subagents/ | wc -l

# List sub-agent IDs
ls -la ~/.claude/projects/<slug>/<uuid>/subagents/

# Find entries for a specific agent
grep '"agentId":"a24a6d75d2dc760f4"' session.jsonl

# Find all agent spawn calls
grep '"name":"Agent"' session.jsonl | jq '.message.content[] | select(.name == "Agent") | .input'
```

---

### Token usage analysis

**Windows (PowerShell):**
```powershell
# Find all cache hits (cache_read_input_tokens > 0)
Select-String -Path "session.jsonl" -Pattern '"cache_read_input_tokens":[^0]'

# Extract all usage blocks
Select-String -Path "session.jsonl" -Pattern '"usage"' | Select-Object -First 20
```

**Linux/Mac:**
```bash
# Extract token usage from all assistant messages
cat session.jsonl | jq 'select(.type == "assistant") | .message.usage'

# Total output tokens across session
cat session.jsonl | jq '[select(.type == "assistant") | .message.usage.output_tokens // 0] | add'

# Cache hit rate
cat session.jsonl | jq '[select(.type == "assistant") | .message.usage.cache_read_input_tokens // 0] | add'
```

---

### Full context audit — all zones at once

**Windows (PowerShell):**
```powershell
$file = "$env:USERPROFILE\.claude\projects\C--Users-guhar\<uuid>.jsonl"

Write-Host "=== ZONE 1: System prompt components ===" -ForegroundColor Cyan
Select-String -Path $file -Pattern '"skill_listing"|"deferred_tools_delta"' |
  Select-Object LineNumber, Line

Write-Host "=== ZONE 2: Compaction events ===" -ForegroundColor Yellow
Select-String -Path $file -Pattern '"summary"|"compaction"' |
  Select-Object LineNumber, Line

Write-Host "=== ZONE 3: Recent messages ===" -ForegroundColor Green
Get-Content $file | Select-Object -Last 5
```

**Linux/Mac:**
```bash
FILE=~/.claude/projects/<slug>/<uuid>.jsonl

echo "=== ZONE 1: System prompt components ==="
grep -n '"skill_listing"\|"deferred_tools_delta"' $FILE

echo "=== ZONE 2: Compaction events ==="
grep -n '"summary"\|"compaction"' $FILE

echo "=== ZONE 3: Recent messages ==="
tail -5 $FILE | jq '{type: .type, timestamp: .timestamp}'
```

---

### Monitor JSONL in real time

**Windows (PowerShell):**
```powershell
# Watch for new entries as session runs
Get-Content "session.jsonl" -Wait | Select-String "compaction|summary|tool_use"
```

**Linux/Mac:**
```bash
# Watch for compaction events
tail -f session.jsonl | grep -E '"compaction"|"summary"'

# Watch all new entries — pretty print
tail -f session.jsonl | jq '{type: .type, timestamp: .timestamp}'
```

---

## Quick Reference

### Compaction summary

```
Auto-compaction:
  triggers automatically at autocompact buffer threshold
  no influence possible
  mitigation: write data to files, don't rely on context

Manual compaction:
  /compact                          ← default summarization
  /compact <instructions>           ← guided summarization
  /compact discard skill content    ← example: drop injected skills
  /compact retain only JSON results ← example: keep structured data only
```

### JSONL entry types at a glance

```
user        → your prompt OR tool result returned
assistant   → Claude's text response OR tool call decision
attachment  → system injection (skill_listing, deferred_tools_delta)
ai-title    → session title
last-prompt → marker for last user message
summary     → appears after compaction
```

### File locations

```
Main session:   ~/.claude/projects/<project>/<uuid>.jsonl
Sub-agent:      ~/.claude/projects/<project>/<uuid>/subagents/agent-<id>.jsonl
Global history: ~/.claude/history.jsonl
Task markers:   $TEMP/claude/<project>/<uuid>/tasks/<agentId>.output  (always empty)
```
