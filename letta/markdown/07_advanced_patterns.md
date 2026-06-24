# Advanced Patterns — Agent Types, Compaction, Templates & Sleep-Time

> **Goal**: Master the advanced features that make Letta agents production-ready:
> agent types, context compaction, reusable templates, and sleep-time compute.

---

## 1. Agent Types — Choosing the Right Architecture

Letta supports multiple agent types for different use cases:

| Agent Type | Description | Best For |
|-----------|-------------|----------|
| `memgpt_agent` | Classic MemGPT with memory blocks + archival | General chat, knowledge work |
| `memgpt_v2_agent` | V2 memory model (newer) | Modern deployments |
| `letta_v1_agent` | Latest Letta architecture | Recommended for new projects |
| `react_agent` | ReAct pattern (Reason + Act loop) | Task execution, tool-heavy workflows |
| `workflow_agent` | Multi-step workflow agent | Pipeline automation |
| `split_thread_agent` | Splits long conversations into threads | High-volume chat |
| `sleeptime_agent` | Background reflection agent | Memory consolidation |
| `voice_convo_agent` | Optimized for voice interactions | Voice assistants |

```python
from letta_client import Letta
import os

client = Letta(api_key=os.environ["LETTA_API_KEY"])

# Create agents of different types

# Type 1: Standard Letta agent (default for most use cases)
standard_agent = client.agents.create(
    model="openai/gpt-4o-mini",
    agent_type="letta_v1_agent",  # Latest architecture
    memory_blocks=[
        {"label": "human", "value": "User: Alex", "limit": 2000},
        {"label": "persona", "value": "I am a helpful assistant.", "limit": 2000}
    ]
)
print(f"Standard agent: {standard_agent.id}")

# Type 2: ReAct agent — explicit Reason→Act→Observe loop
# Better for tool-heavy tasks where explicit reasoning chains matter
react_agent = client.agents.create(
    model="openai/gpt-4o-mini",
    agent_type="react_agent",
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "I am a methodical problem-solver. "
                "I follow the ReAct pattern: "
                "1. Thought: Analyze the situation "
                "2. Action: Take a concrete step "
                "3. Observation: Evaluate the result "
                "4. Repeat until done"
            ),
            "limit": 3000
        }
    ]
)
print(f"ReAct agent: {react_agent.id}")

# Type 3: Workflow agent — designed for multi-step processes
# Best for: data pipelines, report generation, deployment workflows
workflow_agent = client.agents.create(
    model="openai/gpt-4o-mini",
    agent_type="workflow_agent",
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "I am a workflow executor. "
                "I break tasks into steps, execute them sequentially, "
                "track progress, and report results."
            ),
            "limit": 3000
        }
    ]
)
print(f"Workflow agent: {workflow_agent.id}")

print("\nCreated 3 agent types. Clean up when done!")

# Cleanup
# for aid in [standard_agent.id, react_agent.id, workflow_agent.id]:
#     client.agents.delete(aid)
```

## 2. Context Compaction — Managing the Context Window

As conversations grow, the context window fills up. Letta provides
several compaction strategies to handle this gracefully.

```python
# ── Compaction Mode Reference ────────────────────────────────────

compaction_modes = {
    "sliding_window": {
        "description": "Keep N most recent messages, drop older ones",
        "pros": "Simple, fast, predictable token usage",
        "cons": "Loses all context beyond the window",
        "best_for": "Short-lived agents, demos, simple chatbots"
    },
    "all": {
        "description": "Summarize ALL messages into one compressed message",
        "pros": "Preserves gist of everything",
        "cons": "Lossy — details get compressed away",
        "best_for": "Medium-length conversations with narrative arc"
    },
    "self_compact_sliding_window": {
        "description": "Agent itself summarizes older messages before dropping",
        "pros": "Smarter than raw sliding window — agent decides what's important",
        "cons": "Slower and more expensive (extra LLM calls for summarization)",
        "best_for": "Production agents that need to retain key context"
    },
    "self_compact_all": {
        "description": "Agent summarizes everything into a single passage",
        "pros": "Most thorough — agent preserves what matters",
        "cons": "Most expensive — extra LLM call on compaction",
        "best_for": "Long-running agents where quality > cost"
    }
}

for mode, info in compaction_modes.items():
    print(f"\n{mode}:")
    print(f"  {info['description']}")
    print(f"  Best for: {info['best_for']}")
```

```python
# ── Creating an agent with custom compaction ────────────────────

agent_compact = client.agents.create(
    model="openai/gpt-4o-mini",
    memory_blocks=[
        {"label": "human", "value": "Name: Alex", "limit": 2000},
        {"label": "persona", "value": "I am a helpful assistant.", "limit": 2000}
    ],
    # ── Compaction configuration ─────────────────────────────────
    compaction_settings={
        # Mode: how to compact old messages
        "mode": "self_compact_sliding_window",
        
        # clip_chars: max length of each summary in characters
        "clip_chars": 2000,
        
        # model: model to use FOR SUMMARIZATION (can be cheaper than main model!)
        # Use a cheaper model for compaction to save costs
        "model": "openai/gpt-4o-mini",  # $0.15/M input vs $2.50/M for gpt-4o
        
        # Optional: custom summarization prompt
        # "prompt": "Summarize this conversation, preserving key facts, decisions, and action items."
    }
)

print(f"Agent with self-compaction: {agent_compact.id}")
print(f"Compaction mode: {agent_compact.compaction_settings.mode}")
print(f"Compaction model: {agent_compact.compaction_settings.model}")
```

### Compaction Strategy Decision Tree

```
Is the agent long-running (100+ turns)?
├── NO → Use 'sliding_window'
└── YES
    └── Is quality critical (missing context hurts)?
        ├── NO → Use 'sliding_window' with a larger window
        └── YES
            └── Is budget tight?
                ├── YES → Use 'self_compact_sliding_window' + cheap model
                └── NO → Use 'self_compact_all'
```

## 3. Templates — Reusable Agent Blueprints

Templates let you define an agent configuration once and reuse it
across many instances. Great for SaaS apps that create per-user agents.

```python
# ── Create a reusable template ───────────────────────────────────

template = client.templates.create(
    name="customer_support_agent",
    description="Customer support agent template with standard SOPs",
    
    # Agent configuration (same fields as agents.create)
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "I am SupportBot, a customer support agent for Acme Corp.\n"
                "Tone: Empathetic, solution-oriented, professional.\n"
                "Escalation: Issues unresolved in 3 turns → transfer to human.\n"
                "Products: Acme Cloud, Acme Analytics, Acme Connect.\n"
                "I always: (1) Acknowledge the issue, (2) Provide solution, "
                "(3) Verify resolution, (4) Offer additional resources."
            ),
            "limit": 4000
        },
        {
            "label": "human",
            "value": "Customer information will be populated at agent creation time.",
            "limit": 3000
        }
    ],
    
    compaction_settings={
        "mode": "self_compact_sliding_window",
        "clip_chars": 2000
    }
)

print(f"Template created: {template.id}")
print(f"Name: {template.name}")
```

```python
# ── Spawn agents from the template ───────────────────────────────

def create_customer_agent(customer_name: str, customer_tier: str, 
                          company: str = "Acme Corp"):
    """
    Create a customer-specific agent from the support template.
    
    Each agent gets the same persona but personalized human block.
    """
    agent = client.templates.agents.create(
        template.id,
        # Override the human block with customer-specific info
        memory_blocks_override=[
            {
                "label": "human",
                "value": (
                    f"Customer: {customer_name}\n"
                    f"Tier: {customer_tier}\n"
                    f"Company: {company}\n"
                    f"Join date: 2026-06-22"
                ),
                "limit": 3000
            }
        ]
    )
    return agent

# Spawn agents for 3 customers
customers = [
    ("Sarah (TechNova)", "enterprise"),
    ("Marcus (DataFlow)", "pro"),
    ("Priya (CloudStart)", "starter"),
]

customer_agents = {}
for name, tier in customers:
    agent = create_customer_agent(name, tier)
    customer_agents[name] = agent.id
    print(f"  ✓ {name} ({tier}) → {agent.id}")

print(f"\nCreated {len(customer_agents)} agents from template")

# Each agent now has the same persona but different customer context
# They can be used independently — perfect for SaaS multi-tenant apps
```

```python
# ── Manage templates ─────────────────────────────────────────────

# List all templates
templates = client.templates.list()
print(f"You have {len(templates)} templates:")
for t in templates:
    print(f"  • {t.name} — {t.description[:60]}")

# Update a template
# client.templates.update(template.id, model="openai/gpt-4o")  # Upgrade model

# Save a snapshot / version
# client.templates.save(template.id)  # Creates a version snapshot

# Rollback to previous version
# client.templates.rollback(template.id, version=1)

# Delete template
# client.templates.delete(template.id)
```

## 4. Sleep-Time Compute — Background Reflection

Sleep-time compute lets agents continue to *think* between user
interactions — consolidating memories, reorganizing knowledge,
and preparing for future interactions.

```python
# ── Enabling sleep-time on an agent ──────────────────────────────

sleeptime_agent = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    
    memory_blocks=[
        {
            "label": "human",
            "value": (
                "Name: Alex\n"
                "Role: Engineering Manager\n"
                "Current focus: Q3 planning, team growth, architecture review"
            ),
            "limit": 3000
        },
        {
            "label": "persona",
            "value": (
                "I am a proactive engineering assistant. "
                "During sleep-time, I consolidate what I've learned "
                "about Alex's projects, preferences, and decisions. "
                "I identify patterns across conversations and "
                "prepare relevant context for future interactions."
            ),
            "limit": 3000
        }
    ],
    
    # ── Enable sleep-time compute ────────────────────────────────
    enable_sleeptime=True,
    
    # Optional: sleep-time configuration
    # sleeptime_settings={
    #     "model": "openai/gpt-4o-mini",  # Model for sleep-time reflection
    #     "frequency": "after_turn",       # When to trigger sleep-time
    #     "max_steps": 10                  # Max reflection steps per sleep cycle
    # }
)

print(f"Sleep-time agent: {sleeptime_agent.id}")
print(f"Sleep-time: {sleeptime_agent.enable_sleeptime}")
```

### What Happens During Sleep-Time?

```
1. TRIGGER: After N user turns, or after compaction event
   ↓
2. REFLECTION: Agent reviews recent conversation
   - "What did I learn about the user?"
   - "Are there contradictions in my memory?"
   - "What should I consolidate/archive?"
   ↓
3. CONSOLIDATION: Agent updates its memory
   - Updates 'human' block with new facts
   - Moves important info to archival memory
   - Summarizes recent conversations
   - Identifies action items for follow-up
   ↓
4. PREPARE: Agent is ready for next interaction
   with improved context
```

**Cost implication**: Sleep-time runs cost tokens, but they make the agent
more efficient in future turns (less searching, better recall).

## 5. Agent Tags — Organizing Your Agent Fleet

As your agent count grows, use tags to organize them:

```python
# Tags help organize agents by purpose, environment, team, etc.

# Create tags
tags_to_create = ["production", "staging", "dev", "customer-facing", "internal"]

for tag_name in tags_to_create:
    try:
        tag = client.tags.create(name=tag_name)
        print(f"  ✓ Tag: {tag.name}")
    except Exception:
        print(f"  - Tag '{tag_name}' may already exist")

# List tags
tags = client.tags.list()
print(f"\nAll tags: {[t.name for t in tags]}")

# Attach tags to agents
# client.agents.tags.attach(agent_id, tag_id)

# Filter agents by tag
# prod_agents = client.agents.list(tags=["production"])
```

## 6. Agent Environments — Multi-Tenant Isolation

Environments provide logical isolation between groups of agents
(e.g., different customers, teams, or projects).

```python
# Environments are a paid-tier feature, but understanding them helps
# plan multi-tenant architectures:

# env = client.environments.create(
#     name="customer_acme",
#     description="Isolated environment for Acme Corp customer agents"
# )

# # Create agents inside a specific environment
# agent = client.agents.create(
#     model="openai/gpt-4o-mini",
#     environment_id=env.id,
#     ...
# )

# # List agents in an environment
# agents = client.environments.agents.list(env.id)

print("Environments: Available on Letta Cloud paid plans.")
print("Use them for strict multi-tenant isolation.")
```

## 7. Access Tokens — Scoped API Access

For production, create scoped access tokens instead of using your
main API key:

```python
# Create a scoped token (e.g., read-only access for a dashboard)
#
# token = client.access_tokens.create(
#     name="readonly-dashboard",
#     scopes=["agents:read", "messages:read"],
#     expires_in_days=90
# )
# print(f"Token: {token.token}")  # Save this — shown only once!
#
# # List tokens
# tokens = client.access_tokens.list()
#
# # Revoke a token
# client.access_tokens.delete(token.id)

print("Access tokens: Use scoped tokens in production!")
print("Never embed your master API key in client-side code.")
```

## 8. Feedback — Training Your Agent

Provide explicit feedback to improve agent behavior:

```python
# After a response, provide feedback that the agent can learn from
#
# client.agents.feedback.create(
#     agent_id,
#     message_id="msg-abc123",
#     rating="thumbs_up",      # or "thumbs_down"
#     comment="Great answer, but next time include code examples",
#     tags=["code_quality", "improvement_idea"]
# )

print("Feedback helps agents learn preferences over time.")
print("Thumbs up/down + comments → agent adjusts future responses.")
```

## 9. Cost Optimization Strategies

| Strategy | Savings | Trade-off |
|----------|---------|-----------|
| Use cheaper model for compaction | 80-90% on summarization | Summaries may be less nuanced |
| Set tight memory block limits | Less context tokens | Agent must compress more |
| Use `sliding_window` compaction | No extra LLM calls | Loses context beyond window |
| Share blocks across agents | Reuse instead of duplicate | Less customization |
| Archive aggressively | Smaller main context | More archival searches needed |
| Batch archival inserts | Fewer API calls | Slightly delayed availability |

### Cost Calculator (rough):

```
Per-turn cost =
    (system_prompt_tokens + memory_block_tokens + message_tokens) × input_price
  + response_tokens × output_price
  + tool_call_overhead (~200-500 tokens per call)
  + compaction_cost (if self_compact mode)

Example: gpt-4o-mini, 5K context, 1K response, 2 tool calls
  → ~$0.003 per turn (literally fractions of a cent)

Example: gpt-4o, 20K context, 2K response, 5 tool calls
  → ~$0.12 per turn
```

## Key Takeaways

1. **Choose agent types wisely** — `letta_v1_agent` for general, `react_agent` for tool-heavy, `workflow_agent` for pipelines.
2. **Self-compaction is worth the cost** — agents summarize smarter than naive sliding windows.
3. **Use templates for scale** — define once, spawn many agents with consistent behavior.
4. **Sleep-time = proactive learning** — agents improve between interactions.
5. **Tags and environments** keep multi-agent systems manageable.

→ Next: `08_letta_code_intro.ipynb` — Letta Code CLI and the Agent SDK V2.
