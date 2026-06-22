# Chapter 10: Long-Term Memory — Vector Stores & Summarization

## What You'll Learn

- Why short-term memory isn't enough for multi-session agents
- Setting up **ChromaDB** (lightweight vector database, no server required)
- The **embed → store → retrieve** pipeline for semantic memory
- Summarization-based compression of old conversation segments
- Building a `MemoryStore` class and integrating it into the harness loop

---

## 1. The Analogy: Your Notes and Journal

Your **short-term memory** (Chapter 9) is like holding a conversation at a party — you
remember the last few exchanges. But what about that important detail from 20 minutes ago?
Or the user's goal from the start of the session?

That's **long-term memory**: your notebook, your journal, your sticky notes. You don't
keep everything in your head — you **write things down** and **look them up** when needed.

> **Long-term memory = your notes/journal. You can look things up, but retrieval takes
> effort — the agent must actively decide what to store and when to search.**

```
┌─────────────────────────────────────────────────────────┐
│                   AGENT MEMORY SYSTEM                    │
│                                                         │
│  ┌──────────────┐    ┌──────────────────────────────┐  │
│  │ SHORT-TERM   │    │ LONG-TERM (this chapter)       │  │
│  │ (Ch 9)       │    │                              │  │
│  │              │    │  ┌──────────┐ ┌───────────┐  │  │
│  │ Recent turns │◄──►│  │ Vector   │ │ Summary   │  │  │
│  │ in buffer    │    │  │ Store    │ │ Compressor│  │  │
│  │              │    │  │ (Chroma) │ │ (periodic)│  │  │
│  └──────────────┘    │  └──────────┘ └───────────┘  │  │
│                      └──────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Two Approaches to Long-Term Memory

| Approach | Mechanism | Best For | Weakness |
|----------|-----------|----------|----------|
| **Vector Store** | Embed text → store embedding → search by similarity | Factual recall, find "that thing we discussed earlier" | May miss semantically distant but relevant info |
| **Summarization** | Periodically compress old turns into a summary paragraph | Maintaining narrative thread, session continuity | Loses detail; can't answer "what was that exact number?" |
| **Hybrid** (we'll build this) | Vector store + periodic summaries + keyword search | Best of both worlds | More complex to implement |

We'll build a **hybrid** system. The vector store handles precise lookups, and
summarization maintains a compressed "story so far."

---

## 3. Setting Up ChromaDB

ChromaDB is ideal for this: no server, no Docker, just `pip install` and it works
with SQLite locally.

```bash
pip install chromadb openai  # openai for embeddings
```

```python
import chromadb
from chromadb.config import Settings

# ═══ Create a persistent client — data survives restarts ═══
# Chroma stores everything in a local directory (./chroma_data)
client = chromadb.PersistentClient(
    path="./chroma_data",  # where the database lives on disk
    settings=Settings(anonymized_telemetry=False),
)

# ═══ Get or create a collection — like a table in SQL ═══
# Each agent session gets its own collection (or one per user)
collection = client.get_or_create_collection(
    name="agent_memory",
    metadata={"hnsw:space": "cosine"},  # cosine similarity for semantic search
)
```

---

## 4. The Embedding + Retrieval Pipeline

```
INSERT:                          QUERY:
┌──────────┐                    ┌──────────┐
│ Raw text │                    │ "What    │
│ "User    │                    │  was the │
│  wants   │                    │  user's  │
│  dark    │                    │  color   │
│  mode"   │                    │  pref?"  │
└────┬─────┘                    └────┬─────┘
     │                               │
     ▼                               ▼
┌──────────┐                    ┌──────────┐
│ Embedding│                    │ Embedding│
│ Model    │                    │ Model    │
│ [0.12,   │                    │ [0.11,   │
│  -0.34,  │                    │  -0.31,  │
│  0.78...]│                    │  0.75...]│
└────┬─────┘                    └────┬─────┘
     │                               │
     ▼                               ▼
┌──────────┐                    ┌──────────┐
│ Store in │                    │ Cosine   │
│ ChromaDB │                    │ Similarity│
│          │                    │ Search   │
└──────────┘                    └────┬─────┘
                                     │
                                     ▼
                              ┌──────────┐
                              │ Top-K    │
                              │ Results  │
                              │ "User    │
                              │  prefers │
                              │  dark    │
                              │  mode"   │
                              └──────────┘
```

---

## 5. Building the `MemoryStore` Class

```python
from dataclasses import dataclass, field
from datetime import datetime
import json
import chromadb
from openai import OpenAI


@dataclass
class MemoryStore:
    """Long-term memory for an AI agent harness.

    Stores facts and conversation segments as vector embeddings
    in ChromaDB. Provides semantic search (find by meaning, not
    keywords) and periodic summarization of old conversation turns.

    Think of this as the agent's notebook — it writes down important
    things and can look them up later by "what they mean."

    Attributes:
        collection_name: Unique name for this memory space
        persist_dir: Where Chroma data lives on disk
        embedding_model: Which OpenAI model to use for embeddings
        llm_client: OpenAI client (also used for summarization)
    """

    collection_name: str = "agent_memory"
    persist_dir: str = "./chroma_data"
    embedding_model: str = "text-embedding-3-small"  # cheap, fast, good enough
    llm_client: OpenAI | None = None

    def __post_init__(self):
        """Wire up ChromaDB client and collection."""
        # ═══ ChromaDB with persistent storage — survives process restarts ═══
        self._chroma = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=chromadb.config.Settings(anonymized_telemetry=False),
        )
        self._collection = self._chroma.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},  # cosine distance = semantic similarity
        )
        self._embedding_cache: dict[str, list[float]] = {}  # avoid re-embedding identical text

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════

    def add_fact(self, fact: str, metadata: dict | None = None) -> str:
        """Store a fact with its embedding vector.

        Args:
            fact: The text to remember (e.g., "User prefers dark mode")
            metadata: Extra context (timestamp, source turn, importance)

        Returns:
            The ChromaDB document ID (you can use this to delete/update later)
        """
        # ═══ Generate embedding vector from the text ═══
        embedding = self._embed(fact)

        # ═══ Build metadata with timestamp ═══
        meta = metadata or {}
        meta.setdefault("timestamp", datetime.now().isoformat())
        meta.setdefault("type", "fact")

        # ═══ Store in ChromaDB ═══
        doc_id = f"fact_{datetime.now().timestamp()}_{hash(fact) % 10000}"
        self._collection.add(
            ids=[doc_id],
            documents=[fact],
            embeddings=[embedding],
            metadatas=[meta],
        )
        return doc_id

    def search(self, query: str, k: int = 5) -> list[dict]:
        """Search memory by semantic similarity.

        Args:
            query: Natural language query (e.g., "what color scheme does user want?")
            k: Number of top results to return

        Returns:
            List of {text, metadata, distance} dicts, sorted by relevance
        """
        # ═══ Embed the query in the same vector space ═══
        query_embedding = self._embed(query)

        # ═══ Cosine similarity search against all stored embeddings ═══
        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        # ═══ Normalize Chroma's response format ═══
        output = []
        if results["ids"] and results["ids"][0]:
            for i, doc_id in enumerate(results["ids"][0]):
                output.append({
                    "id": doc_id,
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i],  # lower = more similar
                })
        return output

    def summarize_session(self, messages: list[dict],
                          max_summary_tokens: int = 500) -> str:
        """Compress a conversation segment into a dense summary.

        This is the "journal entry" approach — periodically summarize
        old turns so the agent remembers the narrative without keeping
        every message.

        Args:
            messages: The conversation segment to summarize
            max_summary_tokens: Target length for the summary

        Returns:
            A single paragraph summarizing the conversation segment
        """
        if not self.llm_client:
            raise RuntimeError(
                "llm_client is required for summarization. "
                "Set MemoryStore.llm_client = OpenAI() before calling summarize_session."
            )

        # ═══ Build the summarization prompt ═══
        conversation_text = "\n".join(
            f"[{m['role']}]: {m.get('content', '')[:500]}"  # truncate per-message
            for m in messages
        )

        response = self.llm_client.chat.completions.create(
            model="gpt-4o-mini",  # cheap model for summarization
            messages=[{
                "role": "system",
                "content": (
                    "You are a conversation summarizer. Create a dense, factual "
                    "summary of this conversation segment. Include: key decisions, "
                    "user preferences, important facts, and action items. "
                    "Write in third person past tense. Be specific — include "
                    "numbers, names, and exact details."
                ),
            }, {
                "role": "user",
                "content": f"Summarize this conversation segment:\n\n{conversation_text}",
            }],
            max_tokens=max_summary_tokens,
        )
        summary = response.choices[0].message.content

        # ═══ Store the summary as a memory fact for future retrieval ═══
        self.add_fact(summary, metadata={
            "type": "summary",
            "message_count": len(messages),
            "timestamp": datetime.now().isoformat(),
        })

        return summary

    def clear(self) -> None:
        """Delete all memories (danger zone)."""
        self._chroma.delete_collection(self.collection_name)
        self._collection = self._chroma.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════

    def _embed(self, text: str) -> list[float]:
        """Generate an embedding vector using OpenAI's API.

        Uses a simple in-memory cache so identical strings aren't
        re-embedded (saves API calls when the same fact is stored twice).
        """
        if text in self._embedding_cache:
            return self._embedding_cache[text]

        client = self.llm_client or OpenAI()  # create client if not provided
        response = client.embeddings.create(
            model=self.embedding_model,
            input=text,
        )
        embedding = response.data[0].embedding

        # ═══ Cache it — embeddings are deterministic for the same text ═══
        self._embedding_cache[text] = embedding
        return embedding
```

---

## 6. Integrating MemoryStore with the Harness Loop

Here's how to auto-save important facts after every turn and inject
relevant memories before each API call:

```python
def harness_with_memory(user_prompt: str, max_turns: int = 15):
    """A harness that remembers across turns using MemoryStore."""
    from openai import OpenAI

    client = OpenAI()
    memory = MemoryStore(llm_client=client)

    # ═══ Import our ConversationBuffer from Chapter 9 ═══
    buffer = ConversationBuffer(
        max_tokens=6000,
        model="gpt-4o",
        system_prompt="You are a helpful coding assistant. Be thorough.",
    )

    for turn in range(max_turns):
        # ═══ STEP 1: Search long-term memory for relevant context ═══
        # The query IS the user's current message — "what do we know about this?"
        relevant_memories = memory.search(user_prompt, k=3)

        # ═══ STEP 2: Inject memories into the system prompt or as context ═══
        if relevant_memories:
            memory_context = "Relevant context from earlier:\n" + "\n".join(
                f"- {m['text']}" for m in relevant_memories
            )
            # Prepend to user message so the model sees it
            enhanced_prompt = f"{memory_context}\n\n---\nCurrent message: {user_prompt}"
        else:
            enhanced_prompt = user_prompt

        buffer.add("user", enhanced_prompt)

        # ═══ STEP 3: Call the LLM with augmented context ═══
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=buffer.get_messages(),
            max_tokens=1000,
        )
        reply = response.choices[0].message.content
        buffer.add("assistant", reply)

        # ═══ STEP 4: Auto-save important exchanges to long-term memory ═══
        # Only save if the reply is substantial (not just "OK" or "Sure")
        if len(reply) > 50:
            memory.add_fact(
                f"User asked: {user_prompt[:200]}\nAssistant replied: {reply[:200]}",
                metadata={"turn": turn, "type": "exchange"},
            )

        # ═══ STEP 5: Every 5 turns, summarize older segments ═══
        if turn > 0 and turn % 5 == 0 and len(buffer.messages) > 8:
            # Summarize the first half of the buffer (older turns)
            midpoint = len(buffer.messages) // 2
            old_segment = buffer.messages[:midpoint]
            summary = memory.summarize_session(old_segment)
            print(f"[Turn {turn}] Generated summary: {summary[:100]}...")

        print(f"[Turn {turn}] Tokens: {buffer.token_count()}, "
              f"Memories: {len(relevant_memories)} retrieved")

    return buffer
```

---

## 7. When to Store vs When to Retrieve

Decision logic for your harness:

```
                           ┌──────────────┐
                           │ New message  │
                           │ received     │
                           └──────┬───────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │ Is it a "sticky" fact?    │
                    │ (preference, decision,     │
                    │  constraint, goal)          │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │ YES: store in MemoryStore  │
                    │ NO:  just keep in buffer   │
                    └─────────────┬─────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │ Before next LLM call:      │
                    │ search(query, k=3)          │
                    │ inject results into context │
                    └────────────────────────────┘
```

---

## 8. MemoryStore vs ConversationBuffer

| Feature | ConversationBuffer (Ch 9) | MemoryStore (this chapter) |
|---------|--------------------------|---------------------------|
| **Scope** | Current session only | Cross-session, persistent |
| **Storage** | In-memory list | ChromaDB on disk |
| **Retrieval** | Sequential (order matters) | Semantic (meaning matters) |
| **Size limit** | Token budget (~8K) | Millions of documents |
| **Latency** | Zero | ~50ms for embedding + query |
| **Cost** | Free | ~$0.02 per 1M tokens embedded (text-embedding-3-small) |

---

## 9. Production Considerations

1. **Embedding cost**: `text-embedding-3-small` costs $0.02/1M tokens. A typical
   session with 50 stored facts costs fractions of a cent.
2. **Deduplication**: Before storing, check if a nearly identical fact already
   exists (search with `k=1`, check distance). Skip if distance < 0.05.
3. **Staleness**: Timestamp metadata lets you filter out memories older than N days.
4. **Persistence**: ChromaDB stores data in `./chroma_data`. Back this up.
5. **Embedding model lock-in**: Switching models invalidates the vector space.
   Choose one and stick with it, or re-index everything if you change.

---

## Key Takeaways

1. **Short-term memory (buffer) handles the NOW; long-term memory (vector store) handles the PAST.**
2. **ChromaDB is a zero-config vector DB** — perfect for agent memory.
3. **Store facts, search by meaning** — embeddings let you retrieve "color scheme" when the user asks "visual theme."
4. **Summarization compresses narrative** — great for multi-turn coherence.
5. **The best systems use both** — we'll combine them in Chapter 11.

---

> **Previous:** [09 — Short-Term Memory: Conversation Buffers](09_short_term_memory.md)
> **Next:** [11 — Context Window Management: The Hybrid Approach](11_context_window_management.md)
