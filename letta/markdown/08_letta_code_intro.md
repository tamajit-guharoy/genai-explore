# Letta Code — CLI, MemFS, Skills & the Agent SDK V2

> **Goal**: Understand the new Letta ecosystem — the Letta Code CLI, MemFS
> (git-tracked memory), skills, subagents, and the V2 Agent SDK (TypeScript).

---

## 1. The Two Letta Ecosystems (2026)

```
LETTA ECOSYSTEM
├── Letta Agent SDK (V2 — Beta)
│   ├── TypeScript only
│   ├── MemFS (git-tracked memory filesystem)
│   ├── Skills (reusable agent extensions)
│   ├── Subagents (parallel agent delegation)
│   ├── Channels (Slack, Telegram, Discord, etc.)
│   ├── Deployment: Cloud (Constellation) OR Self-hosted
│   └── Based on Letta Code harness (bash tools, file editing)
│
└── Letta V1 SDK (Stable — Python + TS)
    ├── Python (`letta-client`) + TypeScript (`letta-client`)
    ├── Memory blocks + Archival memory (vector DB)
    ├── Server-side tools
    ├── Deployment: Letta Cloud only
    └── REST API (OpenAI-compatible responses format)
```

**This notebook** covers the V2 ecosystem — what's new and how it differs.

## 2. Letta Code CLI — Your Personal Agent

Letta Code is the end-user agent. Install globally and chat from your terminal:

```bash
# Start a new session
letta

# Resume last session
letta --continue

# Use a specific model
letta --model anthropic/claude-sonnet-4

# Run in headless mode (automation)
letta --prompt "Summarize the git diff" --headless

# Memory management
letta memory ls           # List memory files
letta memory show human   # Show human memory
letta memory edit human   # Edit memory directly
letta memory log          # git log for memory changes

# Skills management
letta skills ls           # List installed skills
letta skills install <name>  # Install from registry
```

## 3. MemFS — Git-Tracked Memory Filesystem

MemFS is the V2 memory system — a **git repository** where agent memory
lives as markdown files. This is the biggest architectural change from V1.

```
~/ .letta/agents/<agent-id>/memory/
├── system/
│   ├── persona.md         ← "I am a helpful assistant..."
│   ├── human.md           ← "Name: Alex, Role: Engineer..."
│   └── instructions.md    ← System instructions
├── knowledge/
│   ├── tech-stack.md      ← Company tech stack
│   └── processes.md       ← On-call rotation, deploy process
├── projects/
│   ├── q3-migration.md    ← Project-specific knowledge
│   └── auth-service.md
└── .git/                  ← Git repo with full version history
```

### Key MemFS Concepts:

| Concept | Description |
|---------|-------------|
| **system/ files** | Always loaded in full into context (like memory blocks) |
| **Other files** | Agent sees filenames + descriptions, NOT full contents |
| **git commits** | Every memory change is a commit — full version history |
| **Branching** | Experiment with different memory states, merge back |
| **Dreaming** | Background subagents reflect on and reorganize memory files |

```bash
# View memory file tree
letta memory tree

# Read a memory file
letta memory show human

# Edit memory file directly
letta memory edit human

# View git history
letta memory log

# Show diff between versions
letta memory diff HEAD~1

# Rollback to previous version
letta memory rollback HEAD~1

# Create a new memory file
letta memory create knowledge/api-endpoints.md

# Enable MemFS on an existing agent
letta memfs enable

# Push memory to Letta Cloud (backup + sync)
letta memory push
```

### MemFS vs V1 Memory Blocks

| | V1 Memory Blocks | V2 MemFS |
|---|---|---|
| **Storage** | Database fields | Git repo (markdown files) |
| **Version control** | No (overwrite only) | Full git history |
| **Branching** | No | Yes (experimental memory states) |
| **Human-editable** | Via API only | Via any text editor |
| **Sharing** | Block-level attach | File-level (any git remote) |
| **Context loading** | All blocks always in context | Only system/ files are always loaded |
| **Backup** | Letta Cloud | Git push to any remote |
| **Agent tools** | core_memory_append/replace | bash + file editing tools |

## 4. Skills — Reusable Agent Extensions

Skills are the V2 equivalent of "custom instructions + tools" bundles.
They're portable, versioned, and shareable.

```bash
# Skills are community-contributed agent capabilities
# Each skill is a directory with instructions + optional tools

# Browse available skills
letta skills browse                    # Interactive browser
letta skills search "pdf"             # Search by keyword

# Install skills
letta skills install pdf-extractor
letta skills install github-manager
letta skills install meeting-notes

# In-chat: ask agent to use a skill
# /skills                          # Show installed skills
# "Use the pdf-extractor skill on this file"

# Skills are stored locally
# ~/.letta/skills/
#   ├── pdf-extractor/
#   │   ├── SKILL.md               # Skill definition
#   │   └── scripts/               # Helper scripts
#   └── github-manager/
```

### Skills vs V1 Tools

| | V1 Tools | V2 Skills |
|---|---|---|
| **Scope** | Single function | Multi-step workflow + instructions |
| **Portability** | Per-agent configuration | Install once, use anywhere |
| **Community** | None | Public registry |
| **Versioning** | No | Yes (skill versions) |
| **Creation** | Manually define JSON schema | Agent learns and creates skills |
| **Example** | `get_weather(city)` | "PDF extractor" skill with parse→validate→export logic |

## 5. Subagents — Parallel Agent Delegation

The V2 Agent SDK supports subagents — isolated agents spawned for
parallel work, similar to Hermes' subagent system.

```python
// TypeScript V2: Spawning subagents for parallel work

import { LettaCodeClient } from "@letta-ai/letta-code-sdk";

const client = new LettaCodeClient({
  backend: "cloud",
  apiKey: process.env.LETTA_API_KEY,
});

const agentId = await client.createAgent({
  persona: "You are a project manager...",
});

const session = client.createSession(agentId);

// The agent can spawn subagents during conversation
await session.send(
  "Research 3 database options and compare them. " +
  "Spawn a subagent for each one and synthesize the results."
);

// Subagents:
// - Get isolated context windows (no parent clutter)
// - Run in parallel (faster than sequential)
// - Return only conclusions to parent
// - Have their own memory filesystem
```

## 6. Channels — Multi-Platform Agent Access

V2 agents can connect to messaging platforms natively:

```bash
# Letta Code supports native integrations:

# Slack
# letta channels connect slack
# → Paste Slack Bot Token
# → Agent appears as @letta in your workspace

# Telegram
# letta channels connect telegram
# → Paste BotFather token
# → Agent is reachable via Telegram bot

# Discord
# letta channels connect discord
# → Paste Discord Bot Token
# → Agent joins your server

# WhatsApp, Signal, Matrix, Email (via webhook/API)

# Cross-platform continuity:
# Start conversation in terminal → continue on Telegram
# Agent remembers across all platforms (same memory)
```

## 7. Agent SDK V2 — TypeScript Quickstart

The V2 SDK (`@letta-ai/letta-code-sdk`) is the programmatic interface
to Letta Code agents. Here's the architecture:

```typescript
import { LettaCodeClient } from "@letta-ai/letta-code-sdk";

// 1. CREATE CLIENT
const client = new LettaCodeClient({
  backend: "cloud",          // "cloud" | "local" | "remote"
  apiKey: process.env.LETTA_API_KEY,
  // backend: "local",       // Self-hosted (no API key needed)
  // backend: "remote",      // Remote self-hosted server
  // baseUrl: "http://my-server:8283",
});

// 2. CREATE AGENT
const agentId = await client.createAgent({
  persona: "You are a proactive chief of staff...",
  human: "The user prefers bullet points and async updates.",
  model: "anthropic/claude-sonnet-4",
  toolsets: ["bash", "file_edit", "web_search"],
  skills: ["meeting-notes", "github-manager"],
});

// 3. CREATE SESSION (like a conversation thread)
await using session = client.createSession(agentId);

// 4. SEND MESSAGE
await session.send(
  "Prepare a summary of what we discussed last week " +
  "and draft the Monday standup notes."
);

// 5. STREAM RESPONSES
for await (const message of session.stream()) {
  switch (message.type) {
    case "assistant":
      console.log(message.content);
      break;
    case "tool_call":
      console.log(`Tool: ${message.tool_name}`);
      break;
    case "error":
      console.error(message.error);
      break;
  }
}

// 6. CONTINUE CONVERSATION
await session.send("Now also include the Q3 roadmap items.");
for await (const message of session.stream()) {
  // ... same streaming loop
}

// Session auto-closes via 'await using'
```

## 8. Deployment Options (V2)

V2 supports three deployment modes:

```text
DEPLOYMENT OPTIONS (Letta Agent SDK V2):

┌─────────────────┬────────────────┬───────────────────────┐
│ Mode            │ Where agent    │ API Key needed?       │
│                 │ runs           │                       │
├─────────────────┼────────────────┼───────────────────────┤
│ Cloud           │ Letta's        │ YES                   │
│ (Constellation) │ infrastructure │ (letta.com/api-keys)  │
├─────────────────┼────────────────┼───────────────────────┤
│ Local           │ Your laptop    │ NO                    │
│                 │ (same process) │ (model API key only)  │
├─────────────────┼────────────────┼───────────────────────┤
│ Remote Server   │ Your server    │ NO (or custom auth)   │
│                 │ (Docker/VPS)   │                       │
└─────────────────┴────────────────┴───────────────────────┘

TYPE SCRIPT CONFIGURATION:

// Cloud
const client = new LettaCodeClient({
  backend: "cloud",
  apiKey: process.env.LETTA_API_KEY
});

// Local
const client = new LettaCodeClient({
  backend: "local",
  // Uses local models (Ollama, LM Studio, etc.)
});

// Remote self-hosted
const client = new LettaCodeClient({
  backend: "remote",
  baseUrl: "http://10.0.1.50:8283"
});
```

## 9. Migration Path — V1 → V2

If you're on the V1 SDK and want to migrate:

```text
MIGRATING FROM V1 SDK TO V2 AGENT SDK:

1. ASSESS IF YOU NEED TO MIGRATE:
   Stay on V1 if:
     - You need Python (V2 is TypeScript-only currently)
     - You rely on server-side tools
     - Your app is stable and doesn't need new features
   
   Migrate to V2 if:
     - You want skills, subagents, or channels
     - You need self-hosting
     - You want git-tracked memory (MemFS)
     - You're building a new project

2. CONCEPTUAL MAPPING:
   V1 memory_blocks → V2 files in system/ directory
   V1 archival_memory → V2 files in knowledge/ directory  
   V1 agents.messages.create() → V2 session.send() + stream()
   V1 client.agents → V2 client.createAgent() + createSession()

3. CODE CHANGES:
   pip install letta-client      → npm install @letta-ai/letta-code-sdk
   from letta_client import Letta  → import { LettaCodeClient } from "..."
   client.agents.create({...})     → client.createAgent({...})
   client.agents.messages.create()  → session.send()
   response.messages                → for await (msg of session.stream())

4. PYTHON USERS:
   Python SDK for V2 is NOT yet available.
   Options:
     a) Stay on V1 SDK (stable, Python, good for most use cases)
     b) Use TypeScript for V2 features
     c) Call Letta Code CLI from Python (subprocess)
     d) Wait for Python V2 SDK (watch letta.com changelog)
```

## 10. When to Use V1 vs V2

```
Use V1 SDK (Python):
  ✓ You work in Python
  ✓ You need memory blocks + archival memory
  ✓ You want server-side tools
  ✓ Your app is a chatbot/knowledge assistant
  ✓ You want stable, documented APIs

Use V2 Agent SDK (TypeScript):
  ✓ You want the latest features (skills, subagents)
  ✓ You need self-hosting
  ✓ You want git-tracked memory
  ✓ You need multi-platform channels (Slack, Telegram, etc.)
  ✓ You're building a coding agent with bash tools

Use Letta Code CLI (end-user):
  ✓ You want a personal coding agent
  ✓ You want a persistent digital assistant
  ✓ You need a memory-first alternative to Claude Code/Codex
```

## Key Takeaways

1. **Letta Code** is the end-user agent — install with npm, run `letta`.
2. **MemFS** replaces memory blocks with git-tracked markdown files.
3. **Skills** are reusable, versioned agent extensions (community registry).
4. **Subagents** enable parallel agent delegation in V2.
5. **V2 is TypeScript-only** — Python users should stay on V1 or wait.
6. **Three deployment modes** — Cloud (easy), Local (free), Remote (custom).

→ Next: `09_production_deployment.ipynb` — self-hosting, Docker, and best practices.
