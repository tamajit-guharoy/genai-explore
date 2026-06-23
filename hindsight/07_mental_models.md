# 7. Mental Models & Observations

Hindsight's two higher-order memory types — **observations** and **mental models** —
are what transform it from a "smart database" into a **learning system**.

## The Knowledge Hierarchy

```
Mental Models (highest priority, user-curated)
    │
    ▼
Observations (auto-consolidated from facts)
    │
    ▼
Raw Facts: World + Experience (base layer)
```

During `reflect()`, Hindsight checks in priority order:
1. Mental Models first — curated knowledge trumps everything
2. Observations second — consolidated understanding
3. Raw Facts last — only checked if neither model nor observation covers the query

---

## Observations: Automatic Knowledge Consolidation

Observations are Hindsight's most powerful learning mechanism. They emerge automatically
when multiple related facts accumulate.

### How Observations Form

```python
# Week 1: User shares preferences
client.retain(bank_id="b", content="User uses React for frontend")
client.retain(bank_id="b", content="User prefers TypeScript over JavaScript")
client.retain(bank_id="b", content="User uses Tailwind CSS for styling")

# Hindsight automatically consolidates:
# Observation: "User is a React developer who uses TypeScript and Tailwind CSS"
#   - Built from 3 source facts
#   - Proof count: 3
#   - Each source fact is cited

# Week 2: More evidence strengthens the observation
client.retain(bank_id="b", content="User chose Next.js for the new project")
# Observation updated: "...uses React ecosystem including Next.js..."
# Proof count: 4

# Week 3: Contradictory evidence updates (not overwrites)
client.retain(bank_id="b", content="User is evaluating Vue for a side project")
# Observation updated: "Primary React developer, exploring Vue"
# History preserved: can see evolution over time
```

### Observation Properties

- **Deduplicated**: Multiple facts saying the same thing merge into one observation
- **Evidence-grounded**: Each observation cites its source facts with exact quotes
- **Continuously refined**: New evidence updates the observation; history is preserved
- **Freshness-aware**: `reflect()` checks for unconsolidated facts and treats affected
  observations as "stale" until re-verified

### Configuring Observations

```python
client.create_bank(
    bank_id="learning-bank",
    name="Learning Bank",

    # Enable/disable auto-consolidation
    enable_observations=True,  # Default: True

    # Optional: guide consolidation behavior
    observations_mission="""
    When consolidating facts into observations:
    - Prioritize facts about user preferences and technical decisions
    - Note contradictions explicitly rather than resolving them
    - Track confidence trends over time
    - Flag observations that are based on a single source
    """
)
```

### Viewing Observation History

```python
# Get a memory and its observation history
history = client.get_memory_history(
    bank_id="my-bank",
    memory_id="mem_abc123"
)

for entry in history:
    print(f"Version: {entry.version}")
    print(f"Text: {entry.text}")
    print(f"Updated: {entry.updated_at}")
    print(f"Source facts: {len(entry.source_facts)}")
    print("---")
```

### Clearing and Regenerating Observations

```python
# Clear observations derived from a specific memory
# Triggers re-consolidation
client.clear_memory_observations(
    bank_id="my-bank",
    memory_id="mem_abc123"
)
```

---

## Mental Models: Curated Knowledge

Mental models are **user-curated** (or agent-curated) summaries. Unlike observations
which emerge automatically, mental models are explicitly created.

### When to Create Mental Models

1. **Stable knowledge**: Information that won't change frequently
2. **Onboarding context**: "Here's what you need to know about this project"
3. **Best practices**: "Team coding standards"
4. **Decisions**: "Architecture Decision Records (ADRs)"
5. **Important context**: "Key stakeholder preferences"

### Creating a Mental Model

```python
# Via the client
client.create_mental_model(
    bank_id="my-bank",
    name="Team Python Standards",
    content="""
    ## Team Python Coding Standards

    - Use type hints on all function signatures
    - Prefer dataclasses over plain dicts for data structures
    - Use pytest with pytest-asyncio for testing
    - Format with ruff (line length: 100)
    - Docstrings: Google style
    - Logging: structlog with JSON output
    - Async: use asyncio, not trio
    - Database: SQLAlchemy 2.0+ with async session

    ## Deployment
    - Docker multi-stage builds
    - AWS ECS Fargate
    - CI/CD: GitHub Actions
    - Staging before production, always

    ## Architecture Decisions
    - Monorepo with pnpm workspaces
    - Event-driven microservices via SQS
    - Read models in PostgreSQL, not Elasticsearch
    """,
    tags=["standards", "python", "team"]
)

# Update a mental model
client.update_mental_model(
    bank_id="my-bank",
    mental_model_id="mm_abc123",
    content="Updated standards reflecting new ruff config..."
)
```

### Mental Model Priority

During `reflect()`, mental models take **highest priority**:

```python
# Even if there are 50 raw facts about Python preferences,
# a mental model titled "Team Python Standards" will be
# checked first and its content will dominate the response.

answer = client.reflect(
    bank_id="my-bank",
    query="Should I use asyncio or trio for this new service?"
)
# Response will reference the mental model:
# "The team standard is asyncio (from Team Python Standards mental model)..."
```

### Excluding Mental Models

For queries where you want fresh analysis from raw facts:

```python
# Exclude all mental models
answer = client.reflect(
    bank_id="bank",
    query="What's the current state of the codebase?",
    exclude_mental_models=True
)

# Exclude specific models
answer = client.reflect(
    bank_id="bank",
    query="...",
    exclude_mental_model_ids=["mm_abc123", "mm_def456"]
)
```

### Listing Mental Models

```python
models = client.list_mental_models(bank_id="my-bank")

for model in models:
    print(f"ID: {model.id}")
    print(f"Name: {model.name}")
    print(f"Tags: {model.tags}")
    print(f"Created: {model.created_at}")
    print("---")
```

---

## The Consolidation Pipeline

```
retain("User switched from React to Vue for the dashboard project")
    │
    ▼
┌─────────────────────────────┐
│ Extract facts                │
│ → "User uses Vue"            │
│ → "Context: dashboard project│
│ → "Date: June 2026"          │
└─────────┬───────────────────┘
          ▼
┌─────────────────────────────┐
│ Check for related facts      │
│ → "User uses React"          │
│ → "User prefers React"       │
│ → "User chose Next.js"       │
│ → "User evaluating Vue"      │
└─────────┬───────────────────┘
          ▼
┌─────────────────────────────┐
│ Reconcile                    │
│ Old observation:             │
│   "User is a React developer │
│    using TypeScript"         │
│                              │
│ New evidence: Vue adoption   │
│                              │
│ → Update observation:        │
│   "User is transitioning     │
│    from React to Vue"        │
│   (history preserved)        │
└─────────┬───────────────────┘
          ▼
┌─────────────────────────────┐
│ Update indexes               │
│ → Semantic: re-embed         │
│ → Graph: update entity links │
│ → Temporal: timestamp        │
└─────────────────────────────┘
```

---

## Observation Scopes

Observations can be organized by **scopes** — tag groupings that define different
perspectives on the same facts:

```python
# View distinct observation scopes
scopes = client.get_observation_scopes(bank_id="my-bank")

for scope in scopes:
    print(f"Scope tags: {scope.tags}")
    print(f"Observation count: {scope.count}")
```

---

## Practical Patterns

### Pattern 1: Agent Self-Improvement Loop

```python
# After each user interaction
def learn_from_interaction(user_message, agent_response, user_feedback=None):
    # Retain the exchange
    client.retain(bank_id="agent", content=f"User asked: {user_message}")
    client.retain(bank_id="agent", content=f"I responded: {agent_response}")

    if user_feedback:
        client.retain(
            bank_id="agent",
            content=f"User feedback: {user_feedback}",
            context="feedback"
        )

    # Periodically, reflect on patterns
    reflection = client.reflect(
        bank_id="agent",
        query="What patterns have emerged in user feedback? What should I do differently?"
    )
    # Use reflection to adjust agent behavior
```

### Pattern 2: Project Onboarding via Mental Models

```python
# When a new agent joins a project
def onboard_to_project(bank_id, project_context):
    client.create_mental_model(
        bank_id=bank_id,
        name=f"Project Context — {project_context['name']}",
        content=f"""
        ## Project: {project_context['name']}

        ### Tech Stack
        - Backend: {project_context['backend']}
        - Frontend: {project_context['frontend']}
        - Database: {project_context['database']}
        - Infrastructure: {project_context['infra']}

        ### Key Decisions
        {chr(10).join(f'- {d}' for d in project_context['decisions'])}

        ### Known Pitfalls
        {chr(10).join(f'- {p}' for p in project_context['pitfalls'])}
        """,
        tags=["onboarding", f"project:{project_context['name']}"]
    )
```

### Pattern 3: Evidence-Aware Responses

```python
def evidence_backed_response(bank_id, query):
    answer = client.reflect(
        bank_id=bank_id,
        query=query,
        budget="high"
    )

    # Build response with citations
    response = answer.text
    if answer.based_on:
        response += "\n\n---\n**Sources:**\n"
        for i, source in enumerate(answer.based_on, 1):
            response += f"{i}. [{source.type}] {source.text[:200]}...\n"

    return response
```

---

Continue to:
- **[08_async_batch.md](08_async_batch.md)** — High-throughput patterns
- Run the notebook: `notebooks/07_mental_models.ipynb`
