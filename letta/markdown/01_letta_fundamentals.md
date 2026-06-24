# Letta Fundamentals — Memory Architecture & Core Concepts

> **Goal**: Understand the OS-inspired memory hierarchy that makes Letta unique.
> By the end of this notebook you'll know what every component does and when to use it.

---

## 1. The Problem Letta Solves

Traditional LLM APIs are **stateless** — every request stands alone. This creates three problems:

| Problem | Example |
|---------|---------|
| **Context Window Limits** | Can't fit a year of conversation into 128K tokens |
| **No Persistent Memory** | Agent forgets your name between sessions |
| **No Self-Managed Learning** | Agent can't decide what's worth remembering |

Letta solves all three by making the agent the **memory manager**: it decides what to keep,
what to summarize, and what to archive — all through normal tool-calling.

## 2. The OS-Inspired Memory Hierarchy

Letta models agent memory like a computer's storage hierarchy:

```
┌──────────────────────────────────────────────────────────────┐
│                  LETTA MEMORY ARCHITECTURE                    │
├──────────────┬───────────────────────┬───────────────────────┤
│  MAIN CONTEXT│   RECALL MEMORY       │   ARCHIVAL MEMORY     │
│  (≈ RAM)     │   (≈ Recent Disk)     │   (≈ Cold Storage)    │
├──────────────┼───────────────────────┼───────────────────────┤
│ Always in    │ Searchable on-demand  │ Searchable on-demand  │
│ context      │ (recent msg history)  │ (vector DB passages)  │
│              │                       │                       │
│ • System     │ • Recent messages     │ • Passages inserted   │
│   prompt     │ • Summaries of old    │   by agent or app     │
│ • Memory     │   conversations       │ • Semantic search     │
│   blocks     │ • Full-text search    │ • Vector embeddings   │
│ • Current    │                       │ • Unlimited storage   │
│   messages   │                       │                       │
├──────────────┼───────────────────────┼───────────────────────┤
│ SIZE: LLM    │ SIZE: Thousands of    │ SIZE: Unlimited       │
│ context      │ messages              │ (vector DB backed)    │
│ window       │                       │                       │
└──────────────┴───────────────────────┴───────────────────────┘
```

### The Key Insight

The **agent itself** moves data between tiers via tool calls:
- `core_memory_append` / `core_memory_replace` — edit main context blocks
- `conversation_search` — search recall memory
- `archival_memory_insert` / `archival_memory_search` — read/write long-term storage

## 3. Main Context — The Agent's Working Memory

Everything the model sees on every turn lives here. It's composed of:

### 3a. System Prompt
The instructions that define how the agent acts. Letta auto-generates this from memory blocks.

### 3b. Memory Blocks (Core Memory)
**Labeled, editable strings** that the agent can modify with tools. This is the most important
concept in Letta.

```python
# Conceptual illustration — not runnable yet
#
# Memory blocks are key-value pairs where:
#   - label: identifies the block ("human", "persona", "task_state", etc.)
#   - value: the actual content (modifiable by the agent)
#   - limit: max character count (acts as backpressure)
#   - description: tells the agent WHEN to use this block

memory_blocks = [
    {
        "label": "human",
        "value": (
            "Name: Sarah Chen\n"
            "Role: CTO at DataStack (Series B, 45 employees)\n"
            "Preferences: Prefers bullet points, async comms, no meetings before 10am\n"
            "Projects: Migration from AWS to GCP, hiring 3 senior engineers"
        ),
        "limit": 5000
    },
    {
        "label": "persona",
        "value": (
            "I am Scout, a proactive executive assistant.\n"
            "I prioritize: clarity > completeness, action items > summaries,\n"
            "  anticipating needs > waiting for requests.\n"
            "I speak in crisp, structured English with explicit next steps."
        ),
        "limit": 5000
    },
    {
        "label": "project_hermes",
        "value": (
            "Project: Hermes — internal developer portal\n"
            "Stack: React 19, Go 1.24, PostgreSQL 17\n"
            "Status: Alpha deployed to staging, 3 critical bugs open\n"
            "Deadline: Q3 launch, board demo July 15"
        ),
        "limit": 2000,
        "description": "Current state of the Hermes project. Update when milestones change."
    }
]
```

### 3c. Standard Block Labels

| Label | Purpose | Auto-generated description? |
|-------|---------|----------------------------|
| `human` | What the agent knows about the user | Yes |
| `persona` | The agent's self-description and behavior | Yes |
| `<custom>` | Anything you want: project state, preferences, goals | No (you provide it) |

### 3d. Read-Only Blocks

Blocks can be locked so the agent can't modify them:

```python
{
    "label": "company_policies",
    "value": "1. Never share customer data externally\n"
             "2. All code changes require review\n"
             "3. Escalate security issues within 1 hour",
    "read_only": True  # Agent can READ but not WRITE
}
```

## 4. Recall Memory — Recent Conversation History

Recall memory stores the agent's **message history** in a searchable database.
Unlike main context, it's NOT in the prompt — the agent must explicitly search it.

```
RECALL MEMORY (searchable, not in context)
├── Conversation #1: "Let's plan the Q3 roadmap"
│   ├── Message 1: user — "Here are the priorities..."
│   ├── Message 2: assistant — "Let me organize those..."
│   └── ... (50 messages)
├── Conversation #2: "Debug the auth service"
│   └── ... (30 messages)
└── Conversation #3: "Weekly standup notes"
    └── ... (15 messages)
```

The agent calls `conversation_search` to find relevant past discussions.
This is the "what did we say about X three weeks ago?" layer.

## 5. Archival Memory — Long-Term Knowledge Base

Archival memory is a **vector database** where the agent stores knowledge as
**passages** (text chunks with optional metadata).

```
ARCHIVAL MEMORY (vector DB, semantic search)
├── Passage: "AWS→GCP migration: Phase 1 complete (compute + networking)"
│   └── metadata: {source: "weekly_update", date: "2026-06-15"}
├── Passage: "New hire onboarding checklist: 1) SSO, 2) repo access, 3) IDE config"
│   └── metadata: {source: "process_doc", tags: ["onboarding", "checklist"]}
├── Passage: "Competitor analysis: DataBricks raised $500M at $10B valuation"
│   └── metadata: {source: "research", date: "2026-06-10"}
└── ... (thousands more passages)
```

**Default backend**: LanceDB (embedded) or Pinecone/Redis/Postgres for production.

### Archival vs Recall — When to Use Which

| Characteristic | Recall Memory | Archival Memory |
|---------------|---------------|-----------------|
| Content | Raw conversation messages | Curated knowledge passages |
| Who writes? | System (automatic) | Agent or application (explicit insert) |
| Search type | Keyword/full-text | Semantic (vector similarity) |
| Best for | "What did we discuss?" | "What do we know about X?" |
| Lifespan | Recent (older → summarized) | Permanent (until deleted) |

## 6. The Agent Loop — How Memory Management Works

Every turn, this cycle runs:

```
┌──────────────────────────────────────────────────┐
│  1. COMPILE CONTEXT                              │
│     System prompt + memory blocks + recent msgs   │
│     → Fits into model's context window            │
├──────────────────────────────────────────────────┤
│  2. LLM GENERATES RESPONSE                       │
│     May include tool calls (memory edits, search) │
├──────────────────────────────────────────────────┤
│  3. EXECUTE TOOL CALLS                           │
│     • core_memory_replace — update a block       │
│     • archival_memory_insert — save knowledge    │
│     • conversation_search — recall past chats    │
│     • send_message — reply to user               │
├──────────────────────────────────────────────────┤
│  4. UPDATE STATE                                 │
│     Messages saved, blocks updated, passages     │
│     inserted → agent state persists              │
├──────────────────────────────────────────────────┤
│  5. CHECK COMPACTION                             │
│     If context is near limit → summarize old     │
│     messages, move to recall memory              │
└──────────────────────────────────────────────────┘
```

**Key difference from other frameworks**: The LLM *itself* decides what to remember
and what to forget. There's no separate summarization pipeline — it's all in-band
through tool calls during normal conversation.

## 7. Sleep-Time Compute — Learning While Idle

Letta introduced "sleep-time compute" (2025) — the agent continues to *think* between
user interactions:

```
ACTIVE PHASE                    SLEEP PHASE
──────┬──────────────────       ────┬──────────────────
      │ user: "plan Q3"             │ Agent auto-runs:
      │ agent: <plans>              │ • Consolidate today's memories
      │                             │ • Re-organize archival passages
      │ user: "add budget"          │ • Reflect on contradictions
      │ agent: <updates>            │ • Prepare context for tomorrow
──────┴──────────────────       ────┴──────────────────
```

Configured via `enable_sleeptime=True` on agent creation. The agent runs
a reflection loop during idle periods, consolidating and improving its memory
without consuming the user's time or tokens during active conversation.

## 8. Compaction — When Context Gets Full

When the main context approaches the model's limit, Letta **compacts** old messages:

| Compaction Mode | Behavior |
|-----------------|----------|
| `sliding_window` | Drop oldest messages, keep N most recent |
| `all` | Summarize everything into a single compressed message |
| `self_compact_sliding_window` | Agent itself summarizes older messages (LLM-driven) |
| `self_compact_all` | Agent summarizes everything (LLM-driven) |

```python
# Configuring compaction when creating an agent
compaction_settings = {
    "mode": "self_compact_sliding_window",  # Agent-driven summarization
    "clip_chars": 2000,                      # Max length of each summary
    "model": "openai/gpt-4o-mini"            # Cheaper model for summarization
}
```

## 9. The Two SDKs — V1 vs V2 (Agent SDK)

Letta currently offers TWO developer interfaces:

| | V1 SDK (`letta-client`) | V2 Agent SDK (`letta-code-sdk`) |
|---|---|---|
| **Language** | Python + TypeScript | TypeScript only |
| **Memory** | Memory blocks + Archival | MemFS (git-tracked filesystem) |
| **Tools** | Server-side tools | Client-side bash toolsets |
| **Skills** | No | Yes (reusable agent extensions) |
| **Subagents** | No | Yes (parallel agent delegation) |
| **Deployment** | Letta Cloud only | Cloud + Self-hosted |
| **Channels** | No | Yes (Slack, Telegram, etc.) |
| **Dreaming** | Via sleeptime setting | Via MemFS + dream subagents |
| **Status** | Stable (legacy) | Beta (recommended for new projects) |

This tutorial covers **both**, with emphasis on the V1 SDK for Python
and V2 Agent SDK for advanced features.

## 10. Quick Comparison — Letta vs Alternatives

| Framework | Memory Model | Self-Managing? | Python SDK | Best For |
|-----------|-------------|---------------|------------|----------|
| **Letta** | OS-inspired hierarchy | Yes (agent-driven) | Yes | Agents that must remember across sessions |
| **LangGraph** | Checkpoint-based state | No (developer-managed) | Yes | Complex workflow orchestration |
| **CrewAI** | In-session only | No | Yes | Multi-agent task decomposition |
| **Mem0** | Vector-store profiles | Auto-extraction | Yes | User profile memory for chatbots |
| **OpenAI Assistants** | Threads + vector stores | No (API-managed) | Yes | Simple RAG chatbots |

**Letta's niche**: When the agent needs to *decide for itself* what's worth remembering
and actively manage its own context across hundreds of interactions.

## Next Steps

→ Continue to `02_getting_started.ipynb` to install the SDK and create your first agent.
