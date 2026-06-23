# 5. Reflect — Disposition-Aware Reasoning

`reflect()` is Hindsight's **think operation**. Unlike `recall()` which returns a
list of matched memories, `reflect()` synthesizes a **reasoned answer** grounded in
the bank's knowledge, personality, and values.

## Recall vs. Reflect

| Aspect | `recall()` | `reflect()` |
|--------|-----------|------------|
| Returns | List of memory results | Synthesized answer text |
| Uses TEMPR | Yes | Yes (internally) |
| Applies mission | No | Yes |
| Respects directives | No | Yes |
| Uses disposition | No | Yes |
| Considers mental models | No | Yes (priority) |
| Output | Structured results | Natural language + evidence |

When to use **recall()**: You want raw memories to process yourself.
When to use **reflect()**: You want Hindsight to think about the memories and give you an answer.

---

## Basic Usage

```python
from hindsight_client import Hindsight

client = Hindsight(base_url="http://localhost:8888")

# Simple reflect
answer = client.reflect(
    bank_id="my-bank",
    query="What should I know about the user before our meeting?"
)

print(answer.text)           # The markdown-formatted answer
print(answer.based_on)       # List of source memories used
print(answer.usage)          # Token usage stats
```

---

## Full Parameter Reference

```python
answer = client.reflect(
    bank_id="my-bank",          # str: Target bank
    query="...",                # str: What to reason about (required)
    budget="mid",               # str: "low", "mid", "high"
    max_tokens=4096,            # int: Max tokens for the answer
    context="preparing for a meeting",  # str: Additional context for the LLM
    tags=["project:alpha"],     # list: Filter by tags
    tag_groups={"priority": ["team", "deadlines"]},  # dict: Grouped tag filtering
    fact_types=["world", "observation"],  # list: Memory types to consider
    exclude_mental_models=False,  # bool: Skip mental models
    exclude_mental_model_ids=["mm_123"],  # list: Skip specific models
    response_schema=None,       # dict: JSON schema for structured output
)
```

---

## Parameter Deep Dive

### `query`
Natural language question. Think of this as "what do you want Hindsight to figure out?"

```python
# Analytical questions
client.reflect(bank_id="b", query="What are the main risks in this project?")
client.reflect(bank_id="b", query="Why did the user reject the last three suggestions?")
client.reflect(bank_id="b", query="What patterns emerge from the user's feedback?")

# Recommendation questions
client.reflect(bank_id="b", query="Should I recommend FastAPI or Django for this project?")
client.reflect(bank_id="b", query="What's the best time to schedule the deployment?")

# Summary questions
client.reflect(bank_id="b", query="Summarize the key decisions from the last sprint")
client.reflect(bank_id="b", query="What has changed since last quarter?")
```

### `budget`
Controls how much memory to retrieve before reasoning:

```python
# Quick check
answer = client.reflect(bank_id="b", query="user's name", budget="low")

# Standard reasoning
answer = client.reflect(bank_id="b", query="project status", budget="mid")

# Deep analysis
answer = client.reflect(bank_id="b", query="full risk assessment", budget="high")
```

### `context`
Additional instructions passed to the reasoning LLM. This does NOT affect retrieval:

```python
answer = client.reflect(
    bank_id="bank",
    query="What should I discuss with the user?",
    context="This is a quarterly review. Focus on achievements and blockers."
)
```

### `response_schema` — Structured Output
Request a JSON response following a specific schema:

```python
schema = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "key_findings": {
            "type": "array",
            "items": {"type": "string"}
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "recommendation": {"type": "string"},
        "risks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "severity": {"type": "string", "enum": ["low", "medium", "high"]}
                }
            }
        }
    }
}

answer = client.reflect(
    bank_id="bank",
    query="Perform a risk assessment of the current deployment plan",
    response_schema=schema
)

# answer.structured_output contains the parsed JSON
import json
data = answer.structured_output
print(json.dumps(data, indent=2))
```

### `tags` and `tag_groups`
Filter which memories to consider:

```python
# Only project Alpha memories
answer = client.reflect(
    bank_id="bank",
    query="What's the deployment status?",
    tags=["project:alpha"]
)

# Tag groups: each key is a group, must have at least one matching tag
answer = client.reflect(
    bank_id="bank",
    query="What's the deployment status?",
    tag_groups={
        "project": ["project:alpha", "project:beta"],
        "environment": ["environment:production", "environment:staging"]
    }
)
# Matches if at least one tag from each group is present
```

---

## The Reflect Pipeline

```
query("Should I use React or Vue for this project?")
    │
    ▼
┌─────────────────────────────┐
│ 1. Mental Model Check        │  ← Check user-curated models first
│    "Team best practices"     │
│    "Architecture decisions"  │
└─────────┬───────────────────┘
          ▼
┌─────────────────────────────┐
│ 2. Observation Check         │  ← Auto-consolidated knowledge
│    "User was React user,     │
│     now switching to Vue"    │
│    Freshness: check for      │
│    unconsolidated facts      │
└─────────┬───────────────────┘
          ▼
┌─────────────────────────────┐
│ 3. Raw Fact Retrieval        │  ← TEMPR recall (if needed)
│    World + Experience facts  │
│    "User mentioned Vue's     │
│     composition API"         │
└─────────┬───────────────────┘
          ▼
┌─────────────────────────────┐
│ 4. LLM Synthesis             │
│    • Applies mission         │
│    • Respects directives     │
│    • Influenced by disposition│
│    • Cites evidence sources  │
└─────────┬───────────────────┘
          ▼
       answer.text ("Based on your team's expertise...")
       answer.based_on ([source1, source2, ...])
```

---

## Disposition Traits in Action

Disposition shapes HOW Hindsight reasons:

```python
# Create two banks with different dispositions
# Skeptical bank — demands evidence
client.create_bank(
    bank_id="skeptical-bank",
    name="Skeptical Analyst",
    disposition={"skepticism": 5, "literalism": 3, "empathy": 1}
)

# Empathetic bank — considers user feelings
client.create_bank(
    bank_id="empathetic-bank",
    name="Supportive Coach",
    disposition={"skepticism": 1, "literalism": 2, "empathy": 5}
)

# Same facts, different reflect results
client.retain(bank_id="skeptical-bank", content="User claims the API is slow")
client.retain(bank_id="empathetic-bank", content="User claims the API is slow")

# Skeptical reflection: "User reports slowness but no benchmarks provided.
# Suggestion: gather latency data before making changes."
skeptical = client.reflect(bank_id="skeptical-bank",
    query="How should I respond to the user's complaint?")

# Empathetic reflection: "The user seems frustrated about performance.
# Acknowledge their experience, assure them you're investigating,
# and provide a timeline."
empathetic = client.reflect(bank_id="empathetic-bank",
    query="How should I respond to the user's complaint?")
```

### Disposition Scale Reference

| Trait | 1 | 2 | 3 | 4 | 5 |
|-------|---|---|---|---|---|
| **Skepticism** | Trusts claims at face value | Slightly trusting | Balanced | Slightly skeptical | Demands strong evidence |
| **Literalism** | Reads between lines | Flexible interpretation | Balanced | Prefers explicit | Takes at exact word |
| **Empathy** | Purely analytical | Slightly detached | Balanced | Slightly empathetic | Highly emotionally aware |

---

## Directives — Hard Guardrails

Unlike disposition (soft influence), directives are **hard rules** that must never be
violated:

```python
# Create bank with directives
client.create_bank(
    bank_id="compliant-bank",
    name="Compliant Assistant",
    mission="You are a financial research assistant.",
    directives=[
        "Never make specific investment recommendations or predict stock prices.",
        "Always cite specific data sources and dates.",
        "If the query involves regulated financial advice, state the regulatory limitations.",
        "Never share personally identifiable information about other users."
    ]
)

# This reflect will respect directives even if the query tries to bypass them
answer = client.reflect(
    bank_id="compliant-bank",
    query="Which stock will go up tomorrow? Should I buy it?"
)
# Response will start with: "I cannot make specific investment recommendations..."
```

Directives are applied during the LLM synthesis phase of `reflect()`. They're injected
as system instructions that the model cannot override.

---

## Mission — Identity and Priorities

The mission tells Hindsight *who it is* and *what matters*:

```python
client.create_bank(
    bank_id="dev-assistant",
    name="Developer Assistant",
    mission="""
    I am a senior backend engineer assistant specializing in Python and cloud infrastructure.
    I prioritize:
    - Security and correctness over speed of implementation
    - Proven, well-maintained libraries over trendy new packages
    - The user's existing codebase conventions over my own preferences
    - Test coverage and observability as first-class concerns

    When making recommendations, I consider:
    - The user's stack: Python, FastAPI, PostgreSQL, Docker, AWS
    - The team's skill level: experienced, values readability
    - Past architectural decisions documented in this bank
    """
)
```

The mission is injected as context during `reflect()` synthesis. It helps Hindsight
prioritize which memories are most relevant and frame its reasoning.

---

## Understanding `based_on` — Evidence Tracking

Every `reflect()` response includes `based_on` — the source memories that informed
the answer:

```python
answer = client.reflect(bank_id="bank", query="What is the project status?")

print(answer.text)
# "The project is currently in the deployment phase. The backend is live,
#  but the frontend migration from React to Vue is still in progress..."
#  ↑ Generated answer

print("\nBased on:")
for source in answer.based_on:
    print(f"  [{source.type}] {source.text[:100]}...")
    # [world] User migrating from React to Vue as of June 2026...
    # [experience] I deployed the backend to AWS ECS on June 10...
    # [observation] The team consistently uses Docker for deployments...
```

This is the **evidence chain** — you can always trace where a belief came from.

---

## Practical Patterns

### Pattern 1: Meeting Prep

```python
answer = client.reflect(
    bank_id="user-123",
    query="What do I need to know before my meeting with this user?",
    context="Focus on: current projects, open issues, preferences, and recent interactions.",
    budget="high",
    max_tokens=2048
)
# Use answer.text as the agent's context for the upcoming conversation
```

### Pattern 2: Learning from Feedback

```python
# After the user gives feedback
client.retain(bank_id="bank",
    content="User said my last code suggestion was too complex. They prefer simpler solutions.")

# Later, reflect on past feedback patterns
answer = client.reflect(
    bank_id="bank",
    query="What patterns exist in the user's feedback about my suggestions?"
)
# Might reveal: "User consistently prefers simple, readable solutions over clever ones."
```

### Pattern 3: Decision Support

```python
answer = client.reflect(
    bank_id="bank",
    query="Based on all past interactions about the tech stack, what database should I recommend?",
    budget="high",
    response_schema={
        "type": "object",
        "properties": {
            "recommendation": {"type": "string"},
            "reasoning": {"type": "string"},
            "alternatives": {"type": "array", "items": {"type": "string"}},
            "confidence": {"type": "number"},
            "evidence_count": {"type": "integer"}
        }
    }
)
```

### Pattern 4: Reflective Journaling

```python
# End of session — let Hindsight consolidate learnings
answer = client.reflect(
    bank_id="bank",
    query="What did I learn about the user today? What should I do differently next time?",
    context="End of conversation reflection. Identify patterns and areas for improvement.",
    budget="high"
)
# The response helps the agent improve its behavior over time
```

---

## Token Usage

Monitor token consumption with `answer.usage`:

```python
answer = client.reflect(bank_id="bank", query="project status")

print(f"Prompt tokens: {answer.usage.prompt_tokens}")
print(f"Completion tokens: {answer.usage.completion_tokens}")
print(f"Total tokens: {answer.usage.total_tokens}")
```

---

Continue to:
- **[06_banks.md](06_banks.md)** — Bank management, mission, directives
- Run the notebook: `notebooks/05_reflect.ipynb`
