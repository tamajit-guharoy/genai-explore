# Chapter 20: Persistent Sessions

> **Previous:** [Chapter 19: Human-in-the-Loop](19_human_in_the_loop.md)  
> **Next:** [Chapter 21: Architecture Deep-Dive — Pi](../part6_real_world/21_architecture_pi.md)

---

## What You'll Learn

- How to serialize and deserialize an entire agent conversation state
- SQLite-backed session persistence: messages, tools, metadata
- Session resumption: load by ID, reconstruct harness, continue where you left off
- Cross-device continuity: save on one machine, load on another
- The exact schema you need to make sessions survivable

---

## Why Persistent Sessions Matter

> **Analogy:** You're watching a movie. The power goes out. When it comes back, Netflix remembers exactly where you were — 42 minutes and 17 seconds in. Persistent sessions are that "Resume" button for AI conversations.

Without persistence:
- Every conversation starts from scratch
- A crash destroys all context
- You can't share sessions between devices
- There's no audit trail

With persistence:
- Pause and resume any conversation
- Load history to provide context for new interactions
- Show users their past conversations
- Keep cost/usage records

---

## The Session Data Model

Before we write code, let's design the schema. A session has:

```
┌────────────────────────────────────────────────────────────┐
│                    SESSIONS TABLE                          │
├──────────────┬─────────────────────────────────────────────┤
│ id           │ TEXT PRIMARY KEY — UUID                     │
│ created_at   │ TEXT — ISO 8601 timestamp                   │
│ updated_at   │ TEXT — ISO 8601 timestamp                   │
│ status       │ TEXT — "active", "paused", "completed"      │
│ system_prompt│ TEXT — The system prompt used                │
│ model        │ TEXT — Which model (claude-sonnet-4, etc.)  │
│ total_tokens │ INTEGER — Running total                     │
│ total_cost   │ REAL — Running cost in USD                  │
│ metadata     │ TEXT — JSON blob for extensible metadata    │
└──────────────┴─────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    MESSAGES TABLE                          │
├──────────────┬─────────────────────────────────────────────┤
│ id           │ INTEGER PRIMARY KEY AUTOINCREMENT           │
│ session_id   │ TEXT — FK → sessions.id                     │
│ turn_number  │ INTEGER — Which turn of the loop            │
│ role         │ TEXT — "system", "user", "assistant", "tool"│
│ content      │ TEXT — Message content (or JSON for blocks) │
│ tool_call_id │ TEXT — For tool result messages (nullable)  │
│ tool_name    │ TEXT — Which tool (nullable)                │
│ created_at   │ TEXT — ISO 8601                             │
└──────────────┴─────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────┐
│                    TOOLS TABLE                             │
├──────────────┬─────────────────────────────────────────────┤
│ session_id   │ TEXT — FK → sessions.id                     │
│ tool_name    │ TEXT — Tool name                            │
│ tool_def     │ TEXT — JSON of the ToolDefinition           │
│ PRIMARY KEY  │ (session_id, tool_name)                     │
└──────────────┴─────────────────────────────────────────────┘
```

---

## The SessionStore Implementation

```python
# ═══════════════════════════════════════════════════════════════════
# session_store.py — SQLite-backed session persistence
# ═══════════════════════════════════════════════════════════════════

import json
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base_provider import Message, ToolDefinition


@dataclass
class Session:
    """A full session that can be saved and restored."""
    id: str
    messages: list[Message]
    tool_definitions: list[ToolDefinition]
    system_prompt: str
    model: str
    total_tokens: int = 0
    total_cost: float = 0.0
    status: str = "active"
    created_at: str = ""
    updated_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "system_prompt": self.system_prompt,
            "model": self.model,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "metadata": self.metadata,
        }


class SessionStore:
    """SQLite-backed session persistence.

    Usage:
        store = SessionStore("sessions.db")
        store.initialize()

        # Save
        session = Session(id="abc-123", messages=[...], ...)
        store.save(session)

        # Load
        session = store.load("abc-123")

        # List all
        all_sessions = store.list_sessions()

        # Delete
        store.delete("abc-123")
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        """Lazy connection with WAL mode for concurrent reads."""
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path))
            self._conn.execute("PRAGMA journal_mode=WAL")         # Better concurrency
            self._conn.execute("PRAGMA foreign_keys=ON")           # Enforce FK constraints
            self._conn.row_factory = sqlite3.Row                   # Access columns by name
        return self._conn

    def initialize(self):
        """Create tables if they don't exist. Idempotent — safe to call every startup."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                system_prompt TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                total_tokens INTEGER NOT NULL DEFAULT 0,
                total_cost REAL NOT NULL DEFAULT 0.0,
                metadata TEXT NOT NULL DEFAULT '{}'
            );

            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                turn_number INTEGER NOT NULL DEFAULT 0,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                tool_call_id TEXT,
                tool_name TEXT,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_messages_session
                ON messages(session_id, turn_number);

            CREATE TABLE IF NOT EXISTS session_tools (
                session_id TEXT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                tool_name TEXT NOT NULL,
                tool_def_json TEXT NOT NULL,
                PRIMARY KEY (session_id, tool_name)
            );
        """)
        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════
    # SAVE
    # ═══════════════════════════════════════════════════════════════

    def save(self, session: Session):
        """Save (insert or update) a full session, including messages and tools.

        Uses INSERT OR REPLACE for the session row, then deletes and re-inserts
        messages and tools for simplicity. For large sessions, use incremental updates.
        """
        now = datetime.now(timezone.utc).isoformat()
        session.updated_at = now
        if not session.created_at:
            session.created_at = now

        # ── Session row ──
        self.conn.execute("""
            INSERT OR REPLACE INTO sessions
                (id, created_at, updated_at, status, system_prompt,
                 model, total_tokens, total_cost, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session.id,
            session.created_at,
            session.updated_at,
            session.status,
            session.system_prompt,
            session.model,
            session.total_tokens,
            session.total_cost,
            json.dumps(session.metadata),
        ))

        # ── Messages (delete + re-insert) ──
        self.conn.execute("DELETE FROM messages WHERE session_id = ?", (session.id,))

        for i, msg in enumerate(session.messages):
            content = msg.content
            if not isinstance(content, str):
                content = json.dumps(content)                    # Content blocks → JSON string
            self.conn.execute("""
                INSERT INTO messages
                    (session_id, turn_number, role, content,
                     tool_call_id, tool_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                session.id,
                i // 2,  # Every user/assistant pair = one "turn"
                msg.role,
                content,
                msg.tool_call_id,
                msg.name,
                now,
            ))

        # ── Tools (delete + re-insert) ──
        self.conn.execute("DELETE FROM session_tools WHERE session_id = ?", (session.id,))

        for tool_def in session.tool_definitions:
            self.conn.execute("""
                INSERT INTO session_tools (session_id, tool_name, tool_def_json)
                VALUES (?, ?, ?)
            """, (
                session.id,
                tool_def.name,
                json.dumps({
                    "name": tool_def.name,
                    "description": tool_def.description,
                    "parameters": tool_def.parameters,
                }),
            ))

        self.conn.commit()

    # ═══════════════════════════════════════════════════════════════
    # LOAD
    # ═══════════════════════════════════════════════════════════════

    def load(self, session_id: str) -> Session | None:
        """Load a full session by ID. Returns None if not found."""
        # ── Load session row ──
        row = self.conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()

        if not row:
            return None

        # ── Load messages ──
        msg_rows = self.conn.execute(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY id",
            (session_id,)
        ).fetchall()

        messages: list[Message] = []
        for mr in msg_rows:
            content = mr["content"]
            # Try to parse JSON content blocks
            try:
                content = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass  # Keep as plain string

            messages.append(Message(
                role=mr["role"],
                content=content,
                tool_call_id=mr["tool_call_id"],
                name=mr["tool_name"],
            ))

        # ── Load tools ──
        tool_rows = self.conn.execute(
            "SELECT * FROM session_tools WHERE session_id = ?",
            (session_id,)
        ).fetchall()

        tool_defs: list[ToolDefinition] = []
        for tr in tool_rows:
            td = json.loads(tr["tool_def_json"])
            tool_defs.append(ToolDefinition(
                name=td["name"],
                description=td["description"],
                parameters=td["parameters"],
            ))

        # ── Reconstruct session ──
        metadata = json.loads(row["metadata"]) if row["metadata"] else {}
        return Session(
            id=row["id"],
            messages=messages,
            tool_definitions=tool_defs,
            system_prompt=row["system_prompt"],
            model=row["model"],
            total_tokens=row["total_tokens"],
            total_cost=row["total_cost"],
            status=row["status"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            metadata=metadata,
        )

    # ═══════════════════════════════════════════════════════════════
    # LIST
    # ═══════════════════════════════════════════════════════════════

    def list_sessions(
        self,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict]:
        """List session summaries (without messages — lightweight)."""
        query = "SELECT id, created_at, updated_at, status, model, total_tokens, total_cost FROM sessions"
        params: list = []

        if status:
            query += " WHERE status = ?"
            params.append(status)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    # ═══════════════════════════════════════════════════════════════
    # DELETE
    # ═══════════════════════════════════════════════════════════════

    def delete(self, session_id: str) -> bool:
        """Delete a session and all its messages/tools (CASCADE handles this)."""
        cursor = self.conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # ═══════════════════════════════════════════════════════════════
    # UPDATE STATUS / METADATA (lightweight, no full re-save)
    # ═══════════════════════════════════════════════════════════════

    def update_status(self, session_id: str, status: str):
        """Update just the status field."""
        now = datetime.now(timezone.utc).isoformat()
        self.conn.execute(
            "UPDATE sessions SET status = ?, updated_at = ? WHERE id = ?",
            (status, now, session_id),
        )
        self.conn.commit()

    def update_usage(self, session_id: str, tokens: int, cost: float):
        """Increment token and cost counters."""
        self.conn.execute(
            "UPDATE sessions SET total_tokens = total_tokens + ?, total_cost = total_cost + ?, updated_at = ? WHERE id = ?",
            (tokens, cost, datetime.now(timezone.utc).isoformat(), session_id),
        )
        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
```

---

## Integrating Session Persistence into the Harness

```python
# ═══════════════════════════════════════════════════════════════════
# persistent_harness.py — Harness with auto-save
# ═══════════════════════════════════════════════════════════════════

class PersistentHarness:
    """A harness that automatically persists every turn to SQLite.

    Call save() after each tool execution to checkpoint progress.
    If the process crashes, reload with load(session_id) and call resume().
    """

    def __init__(self, provider, session_store: SessionStore):
        self.provider = provider
        self.store = session_store
        self.session: Session | None = None
        self.tools: dict[str, callable] = {}

    def register_tool(self, tool_def: ToolDefinition, handler: callable):
        """Register a tool. Note: tool handlers are NOT persisted —
        you must re-register them after loading a session."""
        self.tools[tool_def.name] = handler

    def new_session(self, system_prompt: str = "", model: str = "") -> Session:
        """Create a fresh session."""
        session = Session(
            id=str(uuid.uuid4()),
            messages=[
                Message(role="system", content=system_prompt),
            ] if system_prompt else [],
            tool_definitions=[],                                 # Populated on first save
            system_prompt=system_prompt,
            model=model,
        )
        self.session = session
        self.store.save(session)                                 # Persist immediately
        return session

    def load_session(self, session_id: str) -> Session | None:
        """Load a session from the store. Returns None if not found."""
        self.session = self.store.load(session_id)
        return self.session

    def _get_tool_defs(self) -> list[ToolDefinition]:
        """Get tool definitions from registered handlers."""
        return [
            ToolDefinition(
                name=name,
                description=getattr(handler, "__doc__", "") or name,
                parameters=getattr(handler, "__tool_params__", {
                    "type": "object",
                    "properties": {},
                }),
            )
            for name, handler in self.tools.items()
        ]

    async def run(self, user_message: str) -> str:
        """Run the agentic loop with auto-persistence after every turn."""
        if not self.session:
            self.new_session()                                    # Auto-create if needed

        # Append user message
        self.session.messages.append(Message(role="user", content=user_message))
        self.store.save(self.session)                             # Checkpoint

        tool_defs = self._get_tool_defs()

        for turn in range(1, 100):
            response = await self.provider.chat(
                messages=self.session.messages,
                tools=tool_defs,
                system=self.session.system_prompt,
                model=self.session.model,
            )

            # Track usage
            self.session.total_tokens += response.usage.get("input_tokens", 0)
            self.session.total_tokens += response.usage.get("output_tokens", 0)

            if not response.tool_calls:
                # Final response
                self.session.messages.append(
                    Message(role="assistant", content=response.content)
                )
                self.session.status = "completed"
                self.store.save(self.session)
                return response.content

            # Execute tools
            for tc in response.tool_calls:
                handler = self.tools.get(tc.name)
                result = str(await handler(**tc.arguments)) if handler else f"Tool '{tc.name}' not found"

                self.session.messages.append(
                    Message(role="assistant", content=f"Called {tc.name}({tc.arguments})")
                )
                self.session.messages.append(Message(
                    role="tool",
                    content=result,
                    tool_call_id=tc.id,
                    name=tc.name,
                ))

            # ── PERSIST AFTER EVERY TURN ──
            self.session.tool_definitions = tool_defs
            self.store.save(self.session)

        self.session.status = "completed"
        self.store.save(self.session)
        return "Max turns exceeded"

    async def resume(self, new_user_message: str | None = None) -> str:
        """Resume a loaded session.

        If new_user_message is provided, it's added before continuing.
        Otherwise, the agent picks up where it left off (reacts to the last
        tool result in context).
        """
        if not self.session:
            raise ValueError("No session loaded. Call load_session() first.")

        if new_user_message:
            return await self.run(new_user_message)

        # The agent picks up from the last assistant message + tool results
        # This is useful if the session was paused mid-task
        return await self.run("Continue from where you left off.")
```

---

## Cross-Device Continuity

The session is just a SQLite file. Copy it, sync it, back it up.

```python
# ═══════════════════════════════════════════════════════════════════
# cross_device.py — Sharing sessions between machines
# ═══════════════════════════════════════════════════════════════════

import shutil

def export_session(store: SessionStore, session_id: str, output_path: str):
    """Export a single session to a standalone SQLite file.

    This file can be copied to another machine and loaded with import_session().
    """
    # Create a new database with just this session
    export_db = SessionStore(output_path)
    export_db.initialize()

    session = store.load(session_id)
    if session:
        export_db.save(session)

    export_db.close()
    print(f"Session '{session_id}' exported to {output_path}")


def import_session(source_path: str, target_store: SessionStore) -> str | None:
    """Import a session from an exported SQLite file into the main store."""
    source = SessionStore(source_path)
    source.initialize()

    sessions = source.list_sessions(limit=1)
    if not sessions:
        source.close()
        return None

    session = source.load(sessions[0]["id"])
    if session:
        target_store.save(session)                               # Write into target store

    source.close()
    return session.id if session else None
```

---

## Practical Usage: End-to-End

```python
# ═══════════════════════════════════════════════════════════════════
# example_persistent.py
# ═══════════════════════════════════════════════════════════════════

async def persistent_session_demo():
    """Full demo: create → save → crash → resume → complete."""

    store = SessionStore("my_sessions.db")
    store.initialize()

    harness = PersistentHarness(
        provider=AnthropicProvider(),
        session_store=store,
    )

    # Register tools (must do this every time — handlers aren't persisted)
    harness.register_tool(
        ToolDefinition(
            name="search",
            description="Search the web",
            parameters={
                "type": "object",
                "properties": {"q": {"type": "string"}},
                "required": ["q"],
            },
        ),
        handler=lambda q: f"Results for '{q}': ...",
    )

    # ── Day 1: Start a conversation ──
    session_id = harness.new_session(
        system_prompt="You are a research assistant.",
        model="claude-sonnet-4-20250514",
    ).id

    result = await harness.run("Research quantum computing breakthroughs in 2025.")
    print(f"Day 1 result: {result[:200]}...")

    # At this point the session is auto-saved to SQLite.
    # The process crashes or the user closes the app.

    # ── Day 2: Resume the conversation ──
    # (New process, new harness instance)
    store2 = SessionStore("my_sessions.db")                      # Same DB file
    store2.initialize()

    harness2 = PersistentHarness(AnthropicProvider(), store2)
    harness2.register_tool(ToolDefinition(
        name="search", description="Search the web",
        parameters={"type": "object", "properties": {"q": {"type": "string"}}, "required": ["q"]},
    ), handler=lambda q: f"Results for '{q}': ...")

    harness2.load_session(session_id)                            # ← RESUME
    result2 = await harness2.run("Now summarize the key findings in 3 bullet points.")
    print(f"Day 2 result: {result2}")

    # ── List all sessions ──
    all_sessions = store2.list_sessions()
    print(f"\nAll sessions ({len(all_sessions)}):")
    for s in all_sessions:
        print(f"  {s['id'][:8]}... | {s['status']:10} | {s['model']:30} | {s['total_tokens']:6} tokens")
```

---

## Performance Considerations

| Approach | Use Case | Pros | Cons |
|---|---|---|---|
| SQLite (this chapter) | Single-user, local | Zero setup, ACID, fast | Not multi-user |
| PostgreSQL | Multi-user, server | Concurrent writes, replication | Requires DB server |
| File-based (JSON) | Debugging, export | Human-readable, portable | Slow for large sessions |
| Redis | High-frequency, ephemeral | Ultra-fast, TTL support | No persistence by default |

For most agent harnesses, SQLite is the right default. It's embedded, requires no server, and handles millions of messages without breaking a sweat.

---

## Key Takeaways

1. **SQLite is your friend** — zero-config, ACID-compliant, battle-tested
2. **Save after every turn** — losses between turns mean lost context
3. **Tool handlers are NOT persisted** — re-register them after loading
4. **Export/import for cross-device** — sessions are just data, not stateful objects
5. **Three tables is all you need** — sessions, messages, session_tools

---

> **Previous:** [Chapter 19: Human-in-the-Loop](19_human_in_the_loop.md)  
> **Next:** [Chapter 21: Architecture Deep-Dive — Pi](../part6_real_world/21_architecture_pi.md)
