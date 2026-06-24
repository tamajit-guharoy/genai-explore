# Memory Blocks — Core Memory in Depth

> **Goal**: Master memory blocks — the primary mechanism for persistent agent memory.
> Learn to create, read, update, and design blocks that agents can manage autonomously.

---

## 1. Anatomy of a Memory Block

Every memory block has four properties:

```
┌─────────────────────────────────────────┐
│  label: "human"                         │  ← Identifier (used in system prompt)
│  value: "Name: Alex\nRole: ..."         │  ← Actual content (editable by agent)
│  limit: 5000                            │  ← Max character count (backpressure)
│  description: "Key details about..."    │  ← Tells agent WHEN to use this block
│  read_only: false                       │  ← Can the agent modify this?
│  id: "block-abc123"                     │  ← Unique ID (auto-assigned)
└─────────────────────────────────────────┘
```

The **description** is crucial — it tells the agent what kind of information
belongs in this block. A well-written description dramatically improves
memory quality.

## 2. Setup — Reuse an Agent from Notebook 02

```python
from letta_client import Letta
import os

client = Letta(api_key=os.environ["LETTA_API_KEY"])

# Replace with YOUR agent ID from notebook 02
# AGENT_ID = "agent-your-id-here"

# Or list agents and pick one:
agents = client.agents.list()
if agents:
    AGENT_ID = agents[0].id
    print(f"Using agent: {AGENT_ID}")
else:
    print("No agents found. Run notebook 02 first!")
```

## 3. Reading Memory Blocks

Let's inspect what the agent currently has in its blocks:

```python
def print_memory_blocks(agent_id: str):
    """Pretty-print all memory blocks for an agent."""
    agent = client.agents.retrieve(agent_id)
    
    print(f"Agent: {agent.id}\n")
    print(f"{'Label':<20} {'Limit':<8} {'R/O':<6} {'Size':<8} Preview")
    print("=" * 80)
    
    for block in agent.memory_blocks:
        size = len(block.value)
        ro = "🔒" if block.read_only else "✏️"
        preview = block.value[:60].replace('\n', ' ¶ ')
        label = block.label[:18]
        print(f"{label:<20} {block.limit:<8} {ro:<6} {size:<8} {preview}...")
    
    print("\n✏️ = editable by agent  |  🔒 = read-only")

print_memory_blocks(AGENT_ID)
```

## 4. Creating Custom Memory Blocks

Beyond `human` and `persona`, you can create blocks for any purpose.
There are TWO ways:

### 4a. At Agent Creation Time (inline)

```python
# Create an agent with a CUSTOM memory block from the start

agent_with_custom = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "Name: Alex\nRole: Data Engineer\nPrefers concise responses.",
            "limit": 2000
        },
        {
            "label": "persona",
            "value": "I am a helpful data engineer assistant.",
            "limit": 2000
        },
        {
            # ── CUSTOM BLOCK ──────────────────────────────────
            "label": "sprint_backlog",
            "value": (
                "Current Sprint: Sprint 23 (June 16-30)\n"
                "Active tasks:\n"
                "  - [IN PROGRESS] Migrate customer_orders model to dbt 1.9\n"
                "  - [TODO] Add data quality tests for revenue pipeline\n"
                "  - [TODO] Optimize the daily_aggregates DAG (currently 45min)\n"
                "Blocked: None\n"
                "Next planning: June 30"
            ),
            "limit": 3000,
            "description": (
                "Current sprint backlog and task status. "
                "Update when tasks change status or new tasks are added. "
                "Reference this block when discussing work priorities."
            )
        }
    ]
)

print(f"Created agent {agent_with_custom.id} with 3 memory blocks")
print_memory_blocks(agent_with_custom.id)
```

### 4b. Post-Creation — Creating and Attaching Blocks

Create a block separately and attach it to an existing agent:

```python
# Method 1: Create a standalone block, then attach to agent

project_block = client.blocks.create(
    label="project_migration",
    value=(
        "Project: AWS → GCP Migration\n"
        "Phase: 2 of 4 (Data Warehouse)\n"
        "Completed: Networking, IAM, Compute Engine\n"
        "In Progress: BigQuery dataset migration (35/120 tables done)\n"
        "Risks: Schema incompatibilities in 3 legacy tables\n"
        "Deadline: September 15, 2026"
    ),
    limit=3000,
    description="Tracks the state of the AWS→GCP migration project. Update weekly."
)

print(f"Block created: {project_block.id}")

# Attach to agent
client.agents.blocks.attach(agent_with_custom.id, project_block.id)
print(f"Block {project_block.id} attached to agent {agent_with_custom.id}")

# Verify
print_memory_blocks(agent_with_custom.id)
```

## 5. Read-Only Blocks — Informing Without Risk

Read-only blocks let agents access information they must NOT modify:

```python
# Creating a read-only block for company policies

policy_block = client.blocks.create(
    label="company_policies",
    value=(
        "COMPANY POLICIES (read-only):\n"
        "1. All customer data must be handled per GDPR.\n"
        "2. Code changes require peer review before merge.\n"
        "3. Deployments to production require change management ticket.\n"
        "4. AWS prod access requires temporary credentials (max 4 hours).\n"
        "5. Security incidents must be reported within 1 hour to #security."
    ),
    limit=2000,
    description="Company policies and guidelines. Read-only — do not modify.",
    read_only=True  # Agent CANNOT edit this block
)

# Attach to agent
client.agents.blocks.attach(agent_with_custom.id, policy_block.id)
print(f"Read-only policy block attached to {agent_with_custom.id}")
print_memory_blocks(agent_with_custom.id)
```

## 6. Letting the Agent Edit Memory — The Magic

This is where Letta shines. The agent will **decide for itself** what to add,
update, or remove from memory blocks as it converses.

```python
# Tell the agent about yourself and watch it update the 'human' block

response = client.agents.messages.create(
    agent_with_custom.id,
    input=(
        "Here are some things about me you should remember:\n"
        "- I'm allergic to shellfish\n"
        "- My timezone is Pacific (UTC-8)\n"
        "- I prefer Python type hints to be strict (use mypy strict mode)\n"
        "- My daughter's name is Maya and she's 4 years old\n"
        "- I hate meetings before 10am"
    )
)

# Examine tool calls — the agent should have called core_memory_replace or core_memory_append
for msg in response.messages:
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            if 'memory' in tc.function.name.lower():
                print(f"🔧 Tool: {tc.function.name}")
                print(f"   Args: {tc.function.arguments[:300]}")
                print()
    if hasattr(msg, 'content') and msg.content:
        text = msg.content if isinstance(msg.content, str) else str(msg.content)
        print(f"💬 Agent: {text[:300]}")
        print()

# Check — did the human block get updated?
print("\n" + "="*60)
print("Checking human block after conversation...")
agent = client.agents.retrieve(agent_with_custom.id)
human_block = [b for b in agent.memory_blocks if b.label == "human"][0]
print(f"\nHuman block now contains:\n{human_block.value}")
```

## 7. Programmatic Block Manipulation

Sometimes YOU want to update blocks directly (bypassing the agent):

```python
# Directly update a block's content

# Get the sprint_backlog block
agent = client.agents.retrieve(agent_with_custom.id)
sprint_block = [b for b in agent.memory_blocks if b.label == "sprint_backlog"][0]

# Update its value
updated_block = client.blocks.update(
    sprint_block.id,
    value=(
        "Current Sprint: Sprint 24 (July 1-14)\n"
        "Active tasks:\n"
        "  - [COMPLETED] Migrate customer_orders model to dbt 1.9\n"
        "  - [IN PROGRESS] Add data quality tests for revenue pipeline\n"
        "  - [IN PROGRESS] Optimize the daily_aggregates DAG\n"
        "  - [NEW] Set up CI/CD for dbt tests in GitHub Actions\n"
        "Blocked: None\n"
        "Next planning: July 14"
    )
)

print(f"Updated sprint_backlog block")
print(f"New value:\n{updated_block.value}")
```

## 8. Block Design Patterns — What Works

Good block design makes the difference between an agent that remembers
effectively and one that drifts:

### Pattern 1: Structured Key-Value
```
Name: Alex
Role: Data Engineer
Timezone: Pacific (UTC-8)
Preferences: strict mypy, before-10am no-meetings
Family: daughter Maya (4)
```
Best for: `human` block, user profiles

### Pattern 2: Task Tracker
```
[IN PROGRESS] Task A — details
[TODO] Task B — details
[BLOCKED] Task C — details + blocker
```
Best for: Sprint backlogs, project state

### Pattern 3: Decision Log
```
2026-06-15: Chose PostgreSQL over MySQL — better JSON support, team experience
2026-06-20: Decided to use dbt Cloud over dbt Core — managed scheduling worth cost
```
Best for: Architecture decisions, rationale tracking

### Pattern 4: State Machine
```
Phase: DEPLOY_STAGING
Last action: docker build completed (2026-06-22 14:30)
Next: Run integration tests
```
Best for: Multi-step workflows, deployment pipelines

## 9. Block Limits — Understanding Backpressure

The `limit` parameter caps the character count. When a block approaches
its limit, the agent MUST summarize/condense — it can't just append forever.

```python
# Blocks with different limits for different purposes

memory_blocks = [
    {"label": "human", "limit": 2000},     # User facts: key-value, short
    {"label": "persona", "limit": 3000},   # Agent identity: moderately sized
    {"label": "decision_log", "limit": 5000},  # Can grow over time
    {"label": "task_state", "limit": 1000},    # Only current state needed
]
```

**Rule of thumb**: Set limits so all blocks combined use <25% of the
model's context window, leaving room for conversation history.

## 10. Detaching and Cleaning Up Blocks

```python
# Detach a block from an agent (doesn't delete the block)
# client.agents.blocks.detach(agent_id, block_id)

# List all standalone blocks
all_blocks = client.blocks.list()
print(f"Total blocks in your account: {len(all_blocks)}")
for b in all_blocks:
    print(f"  • {b.id} — [{b.label}] (limit: {b.limit})")

# Delete a block entirely
# client.blocks.delete(block_id)

# Clean up the agent we created in this notebook
client.agents.delete(agent_with_custom.id)
print(f"\nCleaned up agent: {agent_with_custom.id}")
```

## Key Takeaways

1. **Memory blocks are the core of Letta** — labeled, editable strings the agent manages.
2. **Standard labels**: `human` (user info) and `persona` (agent identity).
3. **Custom blocks** for task state, project tracking, decision logs — anything.
4. **Read-only blocks** for policies, reference data the agent shouldn't change.
5. **Limits enforce backpressure** — agents must summarize, not just append forever.
6. **Good descriptions** tell the agent WHEN and HOW to use each block.

→ Next: `04_archival_memory.ipynb` — long-term knowledge storage with passages.
