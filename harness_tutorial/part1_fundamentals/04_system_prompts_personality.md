# Chapter 04 — System Prompts & Personality

## What You'll Learn

- What a system prompt is and how it differs from user messages
- How to separate "personality" from "logic" in your harness
- Dynamic system prompts: injecting variables with f-strings and Jinja2
- Building a harness with swappable personalities
- The art of prompt engineering for agent harnesses

---

## The System Prompt: Your Harness's Constitution

In Chapter 03, we used a simple system prompt:

```python
system_prompt = "You are a helpful assistant. Keep answers concise."
```

Let's understand what's actually happening.

The system prompt is **not a message** — it doesn't appear in the `messages` array. It's passed as a separate `system` parameter to the API. Anthropic's documentation describes it this way:

> *"The system prompt is a set of instructions that provides context and guidance to Claude before the conversation begins. It is the most impactful way to shape Claude's behavior."*

Think of it as the **Constitution** for your AI agent:

```
┌──────────────────────────────────────────┐
│           SYSTEM PROMPT                   │
│  "You are X. Your job is Y.              │
│   Rules: 1. Always do Z. 2. Never do W." │
│  (Sets the foundation — affects EVERY     │
│   message that follows)                   │
├──────────────────────────────────────────┤
│              MESSAGES                     │
│  User: "Hello"                            │
│  Assistant: "Hi! How can I..."            │
│  User: "What's 2+2?"                      │
│  Assistant: "4"                           │
│  (The actual conversation, guided by      │
│   the constitution above)                 │
└──────────────────────────────────────────┘
```

---

## Personality ≠ Logic

One of the most important design decisions in harness engineering is keeping **personality** separate from **logic**. Here's what I mean:

| Layer | What It Controls | Example |
|---|---|---|
| **System Prompt** | Personality, tone, role, high-level rules | "You are a patient mentor." |
| **Harness Logic** | Tool execution, loop control, error handling | `if response.stop_reason == "tool_use":` |
| **User Messages** | The actual task | "Explain recursion." |

Your Python code should never contain personality-specific strings like `"You are a cheerful assistant"`. That belongs in configuration. The harness is generic; the personality is a parameter.

---

## The Code: Swappable Personalities

Let's build a harness where the personality is a configuration object, not hard-coded:

```python
# ═══════════════════════════════════════════════════
# CHAPTER 04 — System Prompts & Swappable Personalities
# ═══════════════════════════════════════════════════
import anthropic

# ═══ STEP 1: Define personalities as configuration ═══
# Each personality is a dict with a name and a system prompt template.
# The {name} placeholder will be filled in at runtime.
# 
# WHY dicts and not classes? Personalities are pure data — no behavior.
# They're config, not code. You could load these from a YAML file or
# database, letting non-engineers define personalities without touching Python.
PERSONALITIES = {
    "terse": {
        "name": "Terse Terry",
        "system_prompt": (
            "You are {name}. You give the shortest possible answers. "
            "No greetings, no explanations, no pleasantries. "
            "Just the answer. If the question is 'What is 2+2?', respond '4.' "
            "If you don't know, respond 'Unknown.' Never use more than one sentence."
        )
    },
    "mentor": {
        "name": "Mentor Maria",
        "system_prompt": (
            "You are {name}, a patient and encouraging teacher. "
            "Explain concepts step by step, as if teaching someone new to the topic. "
            "Use analogies. Ask follow-up questions to check understanding. "
            "Never just give the answer — explain the reasoning behind it."
        )
    },
    "creative": {
        "name": "Creative Casey",
        "system_prompt": (
            "You are {name}, a wildly creative thinker. "
            "Answer every question with unexpected metaphors and vivid imagery. "
            "Connect ideas across completely different domains. "
            "Start every response with a surprising analogy."
        )
    },
}

# ═══ STEP 2: The personality-aware harness function ═══
def ask(personality_key: str, user_message: str, conversation_history: list = None) -> dict:
    """
    Send a message to the model with a specific personality.
    
    Args:
        personality_key: Which personality to use ("terse", "mentor", "creative")
        user_message: The user's question
        conversation_history: Previous messages (if continuing a conversation)
    
    Returns:
        dict with 'answer' and updated 'history'
    """
    # ── 2a: Load the personality config ──
    # This is the key separation: personality lives in data, not code.
    # You can add new personalities without changing this function at all.
    if personality_key not in PERSONALITIES:
        raise ValueError(f"Unknown personality: {personality_key}. "
                         f"Choose from: {list(PERSONALITIES.keys())}")
    
    personality = PERSONALITIES[personality_key]
    
    # ── 2b: Build the system prompt by filling in the template ──
    # .format() substitutes {name} with the actual name.
    # Why .format() and not f-strings? Because the template string lives
    # in a data structure (PERSONALITIES), not inline code. .format() lets
    # us defer substitution until runtime.
    # 
    # For more complex templating (conditionals, loops, external data),
    # use Jinja2 (see the "Advanced Templating" section below).
    system_prompt = personality["system_prompt"].format(name=personality["name"])
    
    # ── 2c: Initialize or copy conversation history ──
    # We copy the list to avoid mutating the caller's reference.
    # If no history is provided, start fresh.
    if conversation_history is None:
        messages = []
    else:
        messages = list(conversation_history)  # Shallow copy
    
    # ── 2d: Append the user's message ──
    messages.append({
        "role": "user",
        "content": user_message
    })
    
    # ── 2e: Call the model ──
    client = anthropic.Anthropic(
        api_key="sk-ant-..."  # Replace with your key
    )
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1024,
        system=system_prompt,  # The personality comes from config, not code!
        messages=messages
    )
    
    # ── 2f: Extract the answer ──
    answer = response.content[0].text
    
    # ── 2g: Append the response to history and return ──
    messages.append({
        "role": "assistant",
        "content": answer
    })
    
    return {
        "answer": answer,
        "history": messages,  # Caller saves this for the next turn
        "personality_used": personality["name"]
    }


# ═══ STEP 3: Demo — Same question, different personalities ═══
# This is the "aha!" moment: the SAME harness code, the SAME question,
# but three completely different responses because of the system prompt.

question = "What is recursion?"

for key in ["terse", "mentor", "creative"]:
    result = ask(key, question)
    print(f"\n{'='*60}")
    print(f"[{result['personality_used']}]")
    print(f"{'='*60}")
    print(f"Q: {question}")
    print(f"A: {result['answer']}")

# ═══ STEP 4: Demo — Multi-turn conversation with personality ═══
# The personality persists across turns because we pass history back.
print(f"\n\n{'#'*60}")
print("MULTI-TURN DEMO (Mentor Maria)")
print(f"{'#'*60}")

history = None
questions = [
    "What's a variable?",
    "How is that different from a constant?",
    "Can you give me an example in Python?"
]

for q in questions:
    result = ask("mentor", q, conversation_history=history)
    history = result["history"]  # Save for next turn
    print(f"\nQ: {q}")
    print(f"A: {result['answer'][:200]}...")  # Truncate for display
```

---

## Sample Output

```
============================================================
[Terse Terry]
============================================================
Q: What is recursion?
A: Recursion is a function that calls itself.

============================================================
[Mentor Maria]
============================================================
Q: What is recursion?
A: Great question! Let me break this down step by step.

Think of recursion like Russian nesting dolls (matryoshka). You open 
one doll, and inside there's another, slightly smaller doll. You keep 
opening them until you reach the tiniest doll that can't be opened — 
that's your "base case."

In programming, recursion is when a function calls itself to solve a 
smaller version of the same problem...

============================================================
[Creative Casey]
============================================================
Q: What is recursion?
A: Imagine you're standing between two mirrors, holding a candle. 
The flame reflects infinitely, each reflection containing another 
reflection — that's recursion! It's the programming equivalent of a 
snake eating its own tail, a function that dares to whisper its own 
name, shrinking the problem with each self-invocation until it reaches 
the atomic, indivisible base case...

============================================================
```

---

## Advanced: Jinja2 for Dynamic System Prompts

For production harnesses, f-strings and `.format()` hit limits fast. What if your system prompt needs:

- Conditional sections based on user tier
- Loops over tool descriptions
- Date/time injection
- External data (user profile, project context)

Enter **Jinja2** — Python's most popular templating engine:

```python
# ═══ ADVANCED: Jinja2 System Prompt Templating ═══
from jinja2 import Template
from datetime import datetime

# Define a rich template with conditionals, loops, and variables
template = Template("""
You are {{ name }}, an AI assistant.

Today is {{ current_date }}.
The user's timezone is {{ user_timezone }}.

Your capabilities:
{% for capability in capabilities %}
- {{ capability }}
{% endfor %}

{% if user_tier == "pro" %}
You have access to advanced features: {{ advanced_features | join(", ") }}.
Provide thorough, detailed responses.
{% else %}
You are on the basic tier. Keep responses under 100 words.
{% endif %}

Always be {{ tone }}.
""")

# Render with context
system_prompt = template.render(
    name="TechHelper 9000",
    current_date=datetime.now().strftime("%A, %B %d, %Y"),
    user_timezone="America/New_York",
    capabilities=["Code generation", "Debugging", "Documentation"],
    user_tier="pro",
    advanced_features=["Custom fine-tuned models", "Priority latency", "Long context"],
    tone="professional and helpful"
)

print(system_prompt)
```

Output:
```
You are TechHelper 9000, an AI assistant.

Today is Sunday, June 21, 2026.
The user's timezone is America/New_York.

Your capabilities:
- Code generation
- Debugging
- Documentation

You have access to advanced features: Custom fine-tuned models, Priority latency, Long context.
Provide thorough, detailed responses.

Always be professional and helpful.
```

**When to use which:**

| Approach | Use When |
|---|---|
| **f-string** | Simple, single-variable injection; the template is in code |
| **.format()** | Template stored in a config dict (like our PERSONALITIES dict) |
| **Jinja2** | Conditionals, loops, external data, template stored in a file |

---

## System Prompt Rules of Thumb

Through building dozens of agent harnesses, here's what I've learned:

1. **Be specific about output format.** "Answer concisely" is vague. "Respond in exactly one sentence, no more than 30 words" is specific and the model follows it.

2. **Define stop conditions.** "If you don't know the answer, say 'I don't know' — do not guess." Without this, models confabulate.

3. **Separate "who you are" from "what to do."** Start with identity ("You are a data analyst"), then instructions ("When given a dataset, first describe its shape, then identify outliers").

4. **Test your prompt across models.** A prompt that works perfectly on Claude Sonnet might produce different behavior on GPT-4 or Gemini. Test across providers if you plan to swap models.

5. **Keep it under 500 words.** The system prompt consumes context window tokens. Every word in your system prompt is a word the model can't use for conversation history.

---

## What We Built

| Feature | State |
|---|---|
| Static system prompt | ✅ (Chapter 03) |
| Swappable personalities from config | ✅ |
| Personality persistence across turns | ✅ |
| Jinja2 dynamic templates | ✅ |
| Personality as pure data | ✅ (key design pattern) |

---

**Previous:** [03 — Conversation History](03_conversation_history.md)  
**Next:** [05 — Tool Calling: The Big Idea](05_tool_calling_big_idea.md)
