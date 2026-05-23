# Claude Code — Context Reference Guide

## The Core Mental Model

There is always **one main agent** — Claude itself — running in the main conversation. Everything else (skills, commands, tools, sub-agents, MCP) is invoked from it. Sub-agents can further invoke skills, commands, tools, and spawn their own sub-agents.

```
Claude (main agent — persistent session)
│
├── Skills        → injected into current context
├── Commands      → injected into current context
├── Tools         → results land in current context
├── MCP Tools     → results land in current context
│
└── Sub-agents    → isolated fresh context, discarded after
        │
        ├── Skills
        ├── Commands
        ├── Tools / MCP Tools
        └── Sub-sub-agents → isolated fresh context
```

---

## Constructs

### Main Agent
- Claude itself, running in the main conversation
- Only entity with **persistent session state**
- Accumulates context across the entire session
- Has CLAUDE.md, skill_listing, command_listing always in context
- Spawns sub-agents, invokes skills, commands, tools

### Sub-agents
- Separate isolated Claude instances spawned via the `Agent` tool
- **Fresh context on every invocation** — no memory of previous invocations
- Context is **discarded** after the agent completes
- Parent receives only the final text result (not sub-agent's internal context)
- Can invoke skills, commands, tools, and spawn further sub-agents
- Each invocation gets a unique agent ID and its own JSONL transcript file
- Can run in parallel (single message, multiple Agent calls) or sequentially

### Agent Templates
- Markdown files stored in `agents/` directories
- Define the sub-agent's system prompt, model, and description
- `description:` field — Claude reads this to auto-select the right agent
- `model:` field — specify sonnet/opus/haiku per agent
- Content becomes the sub-agent's **system prompt** — parent never sees it
- No `agent_listing` is pre-loaded into parent context (unlike skills)

```markdown
---
name: release-notes-generator
description: Use this agent to generate release notes from git history
model: sonnet
---

You are a release notes generator...
```

**Locations:**
```
~/.claude/agents/          ← global
.claude/agents/            ← project-specific
```

### Skills
- Prompt templates stored as `SKILL.md` files
- Invoked via `/skill-name` or automatically by Claude based on trigger conditions
- **Listing** (names + descriptions) always pre-loaded in context as `skill_listing`
- **Content** (SKILL.md body) loaded on demand when invoked — never pre-loaded
- Once loaded, content stays in context for the session (never explicitly unloaded)
- Content lives in **conversation history** — subject to compaction
- After compaction, content is gone but listing survives — re-invoking reloads it
- Sub-agents also receive `skill_listing` and can invoke skills

**Locations:**
```
~/.claude/skills/<name>/SKILL.md    ← global
.claude/skills/<name>/SKILL.md      ← project (via plugins)
```

### Commands
- Markdown files invoked via `/command-name`
- Support `$ARGUMENTS` placeholder for passing parameters
- Behave **identically to skills** in terms of context:
  - Listing always pre-loaded (`command_listing`)
  - Content loaded on demand when invoked
  - Content stays once loaded, subject to compaction
- More project-focused than skills; committed to git and shared with team

**Locations:**
```
~/.claude/commands/name.md          ← global
.claude/commands/name.md            ← project-specific
.claude/commands/group/name.md      ← subdirectory → /group:name
```

### Tools (Built-in)
- Native capabilities: `Read`, `Write`, `Edit`, `Bash`, `Glob`, `Grep`, `Agent`, `WebSearch`, `WebFetch`, `TaskCreate`, `TaskUpdate`, etc.
- Always available — no listing overhead, no on-demand loading
- Tool **results** land in current context (main agent or sub-agent, wherever called)
- Results are conversation history — subject to compaction
- Available to main agent, sub-agents, and skills/commands (when executed)

### MCP (Model Context Protocol)
- External servers that register **custom tools** into Claude
- Once registered, MCP tools behave identically to built-in tools
- Results land in current context wherever called
- Extends the tool layer without changing Claude itself
- Available to main agent and sub-agents

**Registration (`.claude/settings.json`):**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "npx",
      "args": ["ts-node", "my-server.ts"]
    }
  }
}
```

### CLAUDE.md
- Injected into the **system prompt** — not conversation history
- **Root CLAUDE.md** — loaded at session start, always in context, survives compaction
- **Parent directory CLAUDE.md files** — loaded at session start (up to home/root)
- **Subdirectory CLAUDE.md files** — lazy loaded when Claude first accesses a file in that directory
- Once loaded, all CLAUDE.md files stay for the entire session (never unloaded)
- Survives compaction — re-injected fresh as system prompt
- Multiple files accumulate in context as more directories are accessed
- Sub-agents do NOT automatically inherit parent's CLAUDE.md — they use agent templates

**Locations:**
```
project/
├── CLAUDE.md              ← always loaded
├── src/
│   └── CLAUDE.md          ← loaded when src/ files accessed
└── tests/
    └── CLAUDE.md          ← loaded when tests/ files accessed
```

---

## Context Lifecycle

### What loads when

| Construct | When loaded | Trigger |
|---|---|---|
| Root CLAUDE.md | Session start | Always |
| Parent CLAUDE.md files | Session start | Always |
| Subdirectory CLAUDE.md | On demand | First file access in that directory |
| Skill listing | Session start | Always |
| Skill content | On demand | Skill invoked |
| Command listing | Session start | Always |
| Command content | On demand | Command invoked |
| Built-in tools | Always available | No loading needed |
| MCP tools | Session start | After MCP server connects |
| Agent template listing | Never pre-loaded | Not injected into parent |
| Agent template content | On demand | Becomes sub-agent system prompt |
| Sub-agent context | On demand | Agent spawned |

### What survives compaction

| Construct | Survives? | Reason |
|---|---|---|
| Root CLAUDE.md | Yes | System prompt |
| Subdirectory CLAUDE.md | Yes | System prompt |
| Skill listing | Yes | System prompt |
| Command listing | Yes | System prompt |
| Skill content | No | Conversation history |
| Command content | No | Conversation history |
| Tool results | No | Conversation history |
| Sub-agent results | No | Conversation history |
| Sub-agent internal context | N/A | Already discarded on completion |

### What never unloads (within a session)

- All CLAUDE.md files (once loaded)
- Skill listing
- Command listing
- Skill content (once invoked — until compaction)
- Command content (once invoked — until compaction)

---

## Context Isolation

### Main agent vs sub-agent context

```
Main agent context (persistent):
  [system prompt]
    ├── CLAUDE.md files
    ├── skill_listing
    └── command_listing
  [conversation history]
    ├── skill content (if invoked)
    ├── command content (if invoked)
    ├── tool results
    └── sub-agent final results (text only)

Sub-agent context (isolated, discarded after):
  [system prompt]
    ├── agent template content
    ├── skill_listing
    └── deferred_tools_delta
  [conversation]
    ├── your prompt
    ├── skill content (if sub-agent invokes skill)
    ├── tool results
    └── sub-sub-agent results
```

### State passing rules

Sub-agents have no memory across invocations. Parent must explicitly pass context:

```
# Wrong — invocation 2 has no memory of invocation 1
result1 = Agent({ prompt: "parse commits" })
result2 = Agent({ prompt: "format the commits you just parsed" })  ✗

# Correct — parent passes result1 explicitly
result1 = Agent({ prompt: "parse commits. return JSON." })
result2 = Agent({ prompt: f"format these commits: {result1}" })   ✓
```

---

## Recommended Patterns

### Supervisor pattern (context-efficient)

```
Main agent (supervisor)
  │  minimal context — just orchestration logic
  │
  ├── Sub-agent A (lean prompt)
  │     invokes Skill on demand → behavioral instructions
  │     uses MCP tool → structured data return
  │     returns JSON result
  │
  ├── Sub-agent B (lean prompt)
  │     invokes Skill on demand
  │     returns JSON result
  │
  └── Main agent synthesizes JSON results → writes output
```

**Why this works:**
- Sub-agent prompts stay minimal (no upfront bloat)
- Skills loaded only when needed, scoped to sub-agent context
- Sub-agent contexts discarded — never pollute parent
- Parent only accumulates lightweight text results

### Skills vs MCP tools in sub-agents

| Use | For |
|---|---|
| Skills | Behavioral instructions — how to reason, format, approach |
| MCP tools | Data in/out — structured return values, external system calls |

### CLAUDE.md structure

```
CLAUDE.md (root — always loaded, keep minimal)
  Universal rules, tech stack, repo overview only

src/CLAUDE.md (lazy — keep focused)
  Coding patterns, component structure

tests/CLAUDE.md (lazy — keep focused)
  Test framework, mocking patterns

infra/CLAUDE.md (lazy — keep focused)
  Deployment rules, env conventions
```

---

## Session Files

| File | Purpose |
|---|---|
| `~/.claude/projects/<project>/<session-uuid>.jsonl` | Full main session transcript |
| `~/.claude/projects/<project>/<session-uuid>/subagents/agent-<id>.jsonl` | Per sub-agent transcript |
| `~/.claude/history.jsonl` | Global session history |
| `$TEMP/claude/<project>/<session-uuid>/tasks/<agentId>.output` | Agent output marker (empty) |

### Useful queries on session JSONL

```powershell
# Find skill invocations
Select-String -Path "session.jsonl" -Pattern '"name":"Skill"'

# Find skill content injections
Select-String -Path "session.jsonl" -Pattern "skill_listing"

# Find command invocations
Select-String -Path "session.jsonl" -Pattern '"name":"Command"'

# Count sub-agents spawned
(Get-ChildItem "subagents/").Count
```

### Detecting context at runtime

| Method | What it shows |
|---|---|
| `/context` | Token usage by category |
| Session JSONL | Full context — every injection, tool call, result |
| Sub-agent JSONL | Exact context that agent had |
| Ask Claude directly | Skills/tools available, rough context state |

---

## Quick Reference

```
Always in context (session start):
  CLAUDE.md (root + parents)
  skill_listing (names only)
  command_listing (names only)
  built-in tools

Lazy loaded (on demand):
  subdirectory CLAUDE.md    → first file access in directory
  skill content             → skill invoked
  command content           → command invoked
  sub-agent context         → agent spawned (isolated)
  agent template            → becomes sub-agent system prompt

Never pre-loaded into parent:
  agent template listing
  agent template content

Survives compaction:
  everything in system prompt (CLAUDE.md, listings)

Lost to compaction:
  skill content, command content, tool results, sub-agent results

Always discarded:
  sub-agent internal context (on agent completion)
```
