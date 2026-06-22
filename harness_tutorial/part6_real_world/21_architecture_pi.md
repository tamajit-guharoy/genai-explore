# Chapter 21: Architecture Deep-Dive — Pi

> **Previous:** [Chapter 20: Persistent Sessions](../part5_advanced/20_persistent_sessions.md)  
> **Next:** [Chapter 22: Architecture Deep-Dive — Omnigent Adapters](22_architecture_omnigent_adapters.md)

---

## What You'll Learn

- How Pi.ai's agent harness is architected under the hood
- Multi-model routing: different models for different subtasks
- Pi's session model: maintaining empathetic context across long conversations
- Pi's tool dispatch: web search, code execution, file operations
- What makes Pi different: emotional intelligence + tool use in one system
- Concrete lessons you can steal for your own harness

---

## Why Study Pi's Architecture?

> **Analogy:** Studying Pi's architecture is like reading the blueprints of a Formula 1 car. You're not going to build an F1 car, but the lessons about aerodynamics, weight distribution, and engine design make your daily driver better.

Pi (pi.ai, by Inflection AI) is unique among AI agents: it's designed to be **emotionally intelligent AND practically capable**. Most agents optimize for one or the other. Pi does both, and its harness architecture shows how.

```
┌─────────────────────────────────────────────────────────────────┐
│                      PI'S HARNESS ARCHITECTURE                   │
│                                                                 │
│  ┌─────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │ Conversation │───►│  Multi-Model    │───►│  Tool Dispatch │  │
│  │    State     │    │    Router       │    │     Layer      │  │
│  └─────────────┘    └─────────────────┘    └────────────────┘  │
│         │                    │                       │          │
│         ▼                    ▼                       ▼          │
│  ┌─────────────┐    ┌─────────────────┐    ┌────────────────┐  │
│  │  Emotional   │    │  Inflection-2.5 │    │  Web Search    │  │
│  │   Context    │    │  (Primary)      │    │  Code Exec     │  │
│  │   Manager    │    │  + Specialty    │    │  File Ops      │  │
│  │             │    │    Models       │    │  Memory R/W    │  │
│  └─────────────┘    └─────────────────┘    └────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. Pi's Multi-Model Routing

Pi doesn't use a single model for everything. Instead, it routes requests to different models based on the task:

```
                            ┌─────────────────┐
                            │   REQUEST IN     │
                            └────────┬────────┘
                                     │
                            ┌────────▼────────┐
                            │  TASK CLASSIFIER │  ← Lightweight model
                            │  (fast, cheap)   │     classifies intent
                            └────────┬────────┘
                                     │
              ┌──────────────────────┼──────────────────────┐
              │                      │                      │
     ┌────────▼────────┐   ┌────────▼────────┐   ┌────────▼────────┐
     │ CONVERSATION    │   │ REASONING       │   │ TOOL USE        │
     │ MODEL           │   │ MODEL           │   │ MODEL           │
     │                 │   │                 │   │                 │
     │ Inflection-2.5  │   │ Inflection-2.5  │   │ Inflection-2.5  │
     │ (empathetic)    │   │ (analytical)    │   │ (function-call) │
     │                 │   │                 │   │                 │
     │ For: chitchat,  │   │ For: math,      │   │ For: search,    │
     │ emotional       │   │ logic, planning │   │ code, files     │
     │ support, small  │   │                 │   │                 │
     │ talk            │   │                 │   │                 │
     └─────────────────┘   └─────────────────┘   └─────────────────┘
```

### How to Steal This: Task Router in Your Harness

```python
# ═══════════════════════════════════════════════════════════════════
# task_router.py — Pi-inspired multi-model routing
# ═══════════════════════════════════════════════════════════════════

from enum import Enum
from dataclasses import dataclass


class TaskCategory(Enum):
    """Categories Pi uses to route requests."""
    CONVERSATION = "conversation"      # Chitchat, emotional support, personal
    REASONING = "reasoning"            # Math, logic, planning, analysis
    TOOL_USE = "tool_use"              # Search, code, file operations
    CREATIVE = "creative"              # Writing, brainstorming, ideation


@dataclass
class RoutedRequest:
    """A request that has been classified and assigned to a model."""
    category: TaskCategory
    model: str                         # Which model to use
    system_prompt: str                 # Appropriate system prompt for this category
    original_message: str              # The user's original message (preserved)


class PiStyleRouter:
    """Routes requests to different models based on task classification.

    Pi uses Inflection's own models, but the pattern works with any provider.
    Map each category to the best model available.
    """

    def __init__(self, provider):
        self.provider = provider       # Multi-provider abstraction (Chapter 17!)
        self.model_map = {
            TaskCategory.CONVERSATION: "claude-sonnet-4-20250514",
            TaskCategory.REASONING:    "claude-opus-4-20250514",       # Strongest reasoning
            TaskCategory.TOOL_USE:     "claude-sonnet-4-20250514",     # Best tool calling
            TaskCategory.CREATIVE:     "claude-sonnet-4-20250514",
        }
        self.system_prompts = {
            TaskCategory.CONVERSATION: (
                "You are a warm, empathetic conversation partner. Be supportive, "
                "curious, and genuine. Listen actively and respond thoughtfully."
            ),
            TaskCategory.REASONING: (
                "You are an analytical reasoning engine. Think step by step, "
                "show your work, and prioritize correctness over brevity."
            ),
            TaskCategory.TOOL_USE: (
                "You are a capable assistant with tool access. Use tools "
                "proactively to provide accurate, up-to-date information."
            ),
            TaskCategory.CREATIVE: (
                "You are a creative collaborator. Generate novel ideas, explore "
                "possibilities, and help the user express themselves."
            ),
        }

    async def classify(self, message: str) -> TaskCategory:
        """Classify the user's message into a task category.

        Pi uses a lightweight classification model. Here we use the
        main provider with a classification prompt (or you can use
        a cheap/fast model like GPT-4o-mini for this).
        """
        response = await self.provider.chat(
            messages=[
                Message(role="user", content=(
                    f"Classify this message into EXACTLY ONE category. "
                    f"Respond with ONLY the category name.\n\n"
                    f"Categories: conversation, reasoning, tool_use, creative\n\n"
                    f"Message: \"{message}\"\n\nCategory:"
                )),
            ],
            system="You are a request classifier. Output only the category name.",
            max_tokens=10,
        )

        category_str = response.content.strip().lower()
        try:
            return TaskCategory(category_str)
        except ValueError:
            return TaskCategory.CONVERSATION                        # Default to conversation

    async def route(self, message: str) -> RoutedRequest:
        """Classify and route a message to the appropriate model + system prompt."""
        category = await self.classify(message)
        return RoutedRequest(
            category=category,
            model=self.model_map[category],
            system_prompt=self.system_prompts[category],
            original_message=message,
        )
```

---

## 2. Pi's Session Model: Emotional Continuity

Pi's killer feature is its ability to maintain **emotional context** across conversations. It remembers not just what you talked about, but how you felt about it.

```
┌─────────────────────────────────────────────────────────────────┐
│                  PI'S SESSION STATE                              │
│                                                                 │
│  SHORT-TERM (in context window):                                │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Last 20 messages (direct context)                         │  │
│  │ Current emotional tone: "user is anxious about job search" │  │
│  │ Active topics: ["career change", "machine learning"]      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  LONG-TERM (in vector DB):                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ User preferences: "prefers concise answers", "likes cats" │  │
│  │ Emotional history: "was stressed in March about layoffs"  │  │
│  │ Key life events: "got promoted April 2025", "moved to SF" │  │
│  │ Conversation summaries (last 50 sessions)                 │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  RETRIEVAL STRATEGY:                                            │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 1. Always inject "emotional summary" (100 tokens)         │  │
│  │ 2. Keyword-match relevant past conversations              │  │
│  │ 3. Semantic search for related topics                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### How to Steal This: Emotional Context in Your Harness

```python
# ═══════════════════════════════════════════════════════════════════
# emotional_context.py — Pi-style emotional continuity
# ═══════════════════════════════════════════════════════════════════

@dataclass
class EmotionalState:
    """Pi tracks these dimensions per conversation."""
    primary_emotion: str         # "anxious", "excited", "curious", "frustrated"
    intensity: float            # 0.0 (neutral) → 1.0 (intense)
    topics: list[str]           # What the user is talking about
    relationship_stage: str     # "new", "established", "trusted"


class EmotionalContextManager:
    """Maintains emotional context across a conversation.

    Pi does this with a dedicated emotional-intelligence model.
    You can approximate it with periodic summaries injected into context.
    """

    def __init__(self, provider):
        self.provider = provider
        self.state = EmotionalState(
            primary_emotion="neutral",
            intensity=0.0,
            topics=[],
            relationship_stage="new",
        )
        self.update_frequency = 5                                  # Update every 5 messages

    async def analyze_emotion(self, messages: list[Message]) -> EmotionalState:
        """Analyze recent messages for emotional content."""
        recent = "\n".join([
            f"{m.role}: {m.content}" for m in messages[-10:]
            if isinstance(m.content, str)
        ])

        response = await self.provider.chat(
            messages=[Message(role="user", content=(
                f"Analyze the emotional content of this conversation. Output JSON:\n"
                f'{{"primary_emotion": "...", "intensity": 0.0-1.0, '
                f'"topics": [...], "relationship_stage": "new|established|trusted"}}\n\n'
                f"Conversation:\n{recent}\n\nJSON:"
            ))],
            system="You analyze emotional content. Output valid JSON only.",
            max_tokens=200,
        )

        try:
            data = json.loads(response.content)
            return EmotionalState(**data)
        except (json.JSONDecodeError, TypeError):
            return self.state                                      # Keep previous if parse fails

    def build_context_injection(self) -> str:
        """Build a short text to inject into the system prompt.

        This is how Pi keeps emotional context present without
        consuming the entire context window.
        """
        return (
            f"[EMOTIONAL CONTEXT] User appears {self.state.primary_emotion} "
            f"(intensity: {self.state.intensity:.1f}). "
            f"Topics: {', '.join(self.state.topics[:3])}. "
            f"Relationship: {self.state.relationship_stage}."
            f"[/EMOTIONAL CONTEXT]"
        )

    async def update(self, messages: list[Message]) -> str:
        """Update emotional state and return context injection string."""
        self.state = await self.analyze_emotion(messages)
        return self.build_context_injection()
```

---

## 3. Pi's Tool Dispatch

Pi handles tools differently from most agents — it surfaces tool results conversationally:

```
USER: "What's the weather in Tokyo?"
  │
  ▼
PI (internally): calls weather_api("Tokyo") → "24°C, partly cloudy"
  │
  ▼
PI (to user): "Tokyo's looking pleasant today! It's 24°C with partly
               cloudy skies. Perfect for exploring the city — have you
               been to the Meiji Shrine? The gardens are beautiful in
               this weather."
                ↑
                Not just the data — wrapped in conversation
```

### The Conversational Tool Result Pattern

```python
# ═══════════════════════════════════════════════════════════════════
# pi_style_tools.py — Conversational tool result wrapping
# ═══════════════════════════════════════════════════════════════════

class PiStyleToolDispatcher:
    """Pi wraps raw tool results in conversational framing.

    Instead of dumping JSON to the user, Pi:
    1. Executes the tool
    2. Passes the raw result + conversation context to a "narrator" pass
    3. The narrator weaves the data into a natural response
    """

    def __init__(self, provider):
        self.provider = provider
        self.tools: dict[str, callable] = {}

    def register(self, name: str, handler: callable):
        self.tools[name] = handler

    async def execute_and_narrate(
        self,
        tool_name: str,
        tool_args: dict,
        conversation_context: str,                                  # Recent messages summary
        user_emotion: EmotionalState | None = None,
    ) -> str:
        """Execute a tool and narrate the result conversationally."""
        # Step 1: Execute the tool
        handler = self.tools.get(tool_name)
        if not handler:
            return f"I'm sorry, I couldn't perform that action."

        raw_result = await handler(**tool_args) if asyncio.iscoroutinefunction(handler) \
                     else handler(**tool_args)

        # Step 2: Narrate the result
        emotion_hint = ""
        if user_emotion:
            emotion_hint = f"The user seems {user_emotion.primary_emotion}. "

        response = await self.provider.chat(
            messages=[Message(role="user", content=(
                f"Context: {conversation_context}\n"
                f"Tool: {tool_name}\n"
                f"Raw result: {raw_result}\n"
                f"{emotion_hint}"
                f"Weave this into a natural, conversational response. "
                f"Don't just state the facts — connect them to the user's context. "
                f"Be warm and helpful."
            ))],
            system="You are a warm, conversational narrator for tool results.",
            max_tokens=300,
        )
        return response.content
```

---

## 4. What Makes Pi Different: The Synthesis

Most AI agents are either:
- **Utility-focused** (search, code, files) — cold and transactional
- **Conversation-focused** (chatbot) — warm but useless for real tasks

Pi synthesizes both:

```
┌─────────────────────────────────────────────────────────────────┐
│                  PI'S SYNTHESIS LAYER                            │
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │ TOOL RESULTS  │         │  EMOTIONAL    │                     │
│  │ (raw data)    │         │  CONTEXT      │                    │
│  └──────┬────────┘         └──────┬────────┘                    │
│         │                         │                              │
│         └─────────┬───────────────┘                              │
│                   │                                              │
│          ┌────────▼────────┐                                     │
│          │  CONVERSATIONAL │  ← The secret sauce                 │
│          │  SYNTHESIZER    │                                     │
│          │                 │                                     │
│          │ "Tokyo is 24°C. │                                     │
│          │  Knowing you're │                                     │
│          │  planning a     │                                     │
│          │  trip, I'd      │                                     │
│          │  recommend..."  │                                     │
│          └─────────────────┘                                     │
└─────────────────────────────────────────────────────────────────┘
```

This is the pattern to steal: **separate tool execution from tool presentation**. Execute cold, present warm.

---

## 5. Lessons for Your Own Harness

### Lesson 1: Classify Before You Respond

```python
# Don't use one prompt for everything. Route.
category = await router.classify(user_message)
if category == TaskCategory.TOOL_USE:
    return await tool_harness.run(user_message)
elif category == TaskCategory.CONVERSATION:
    return await conversation_harness.run(user_message)
```

### Lesson 2: Emotional Context is a Feature, Not Overhead

```python
# A 100-token emotional summary injected into the system prompt
# dramatically improves user satisfaction. It's the cheapest
# "personality upgrade" you can make.
system_prompt = base_prompt + "\n\n" + emotional_manager.build_context_injection()
```

### Lesson 3: Narration Layer for Tools

```python
# Raw tool results → conversation → user
# NOT: raw tool results → user
raw = await execute_tool(name, args)
narrated = await narrate(raw, context, emotion)
return narrated
```

### Lesson 4: Persistent Emotional Memory

```python
# Store emotional summaries in your session DB (Chapter 20):
session.metadata["emotional_summary"] = {
    "mood_trajectory": ["neutral", "anxious", "relieved"],
    "key_concerns": ["job search", "relocation"],
}
```

---

## Pi Architecture Summary

| Component | Pi's Approach | Your Takeaway |
|---|---|---|
| Model routing | Classifier → specialized models | Route based on task category |
| Session model | Short-term + long-term emotional state | Store emotional summaries in metadata |
| Tool dispatch | Execute → narrate conversationally | Add narration pass after tool execution |
| Personality | Consistent warm tone across all interactions | System prompt injection with emotional context |
| Memory | Semantic + emotional retrieval | Vector DB with emotion-tagged embeddings |

---

> **Previous:** [Chapter 20: Persistent Sessions](../part5_advanced/20_persistent_sessions.md)  
> **Next:** [Chapter 22: Architecture Deep-Dive — Omnigent Adapters](22_architecture_omnigent_adapters.md)
