# Getting Started — Installation, Setup & First Agent

> **Goal**: Install the Letta SDK, configure credentials, and create your first
> stateful agent that remembers you across conversations.

---

## 1. Installation

Letta provides two Python packages. We'll use `letta-client` (the current V1 SDK name):

```python
Install the Letta Python client
!pip install letta-client

For self-hosted server support:
!pip install letta-client[server]

For all extras (postgres, redis, pinecone, etc.):
!pip install letta-client[server,postgres,redis,pinecone]
```

## 2. API Key Setup

Get your API key from https://app.letta.com → API Keys.

**Option A**: Environment variable (recommended for development):

```python
import os

# Set your API key (do this once per session)
# os.environ["LETTA_API_KEY"] = "sk-..."  # Replace with your actual key

# Or read from a .env file:
# from dotenv import load_dotenv
# load_dotenv()  # loads LETTA_API_KEY from .env file

print(f"API key configured: {'LETTA_API_KEY' in os.environ}")
```

**Option B**: Pass directly to the client (use with caution — never commit to git):

```python
from letta_client import Letta
client = Letta(api_key="sk-...")  # Not recommended — use env vars instead
```

## 3. Creating the Client

The `Letta` client is your entry point for all API operations.

```python
from letta_client import Letta
import os

# Connect to Letta Cloud
client = Letta(api_key=os.environ["LETTA_API_KEY"])

# For self-hosted servers (covered in notebook 09):
# client = Letta(base_url="http://localhost:8283")

print(f"Client connected: {client}")
```

## 4. Your First Agent — Hello, Stateful World

Create an agent with two standard memory blocks (`human` and `persona`).
This is the minimum viable agent.

```python
# Create an agent — the agent PERSISTS in Letta's database
# You can reuse this agent across sessions, notebooks, and applications

agent_state = client.agents.create(
    # ── Model selection ───────────────────────────────────────────
    # Format: "provider/model-name"
    # Supported providers: openai, anthropic, google, together, fireworks,
    #                      groq, deepseek, xai, openrouter, and more
    model="openai/gpt-4o-mini",
    
    # ── Embedding model for archival memory ───────────────────────
    embedding="openai/text-embedding-3-small",
    
    # ── Memory blocks — what the agent knows ──────────────────────
    memory_blocks=[
        {
            "label": "human",
            "value": (
                "Name: Alex\n"
                "Role: Data Engineer at PipelineCo\n"
                "Tech stack: Python, dbt, Snowflake, Airflow\n"
                "Preferences: Prefers code over configurations, "
                "uses VS Code, runs on macOS"
            ),
            "limit": 5000  # Max chars for this block
        },
        {
            "label": "persona",
            "value": (
                "I am Scout, a data engineering assistant.\n"
                "I specialize in dbt models, Airflow DAGs, and SQL optimization.\n"
                "I respond with working code, not just explanations.\n"
                "I proactively suggest improvements and catch edge cases."
            ),
            "limit": 5000
        }
    ],
    
    # ── Optional: system prompt override ──────────────────────────
    # system="You are a helpful data engineering assistant.",
    
    # ── Optional: compaction settings ─────────────────────────────
    # compaction_settings={
    #     "mode": "self_compact_sliding_window",
    #     "clip_chars": 2000
    # }
)

print(f"Agent ID:      {agent_state.id}")
print(f"Model:         {agent_state.model}")
print(f"Embedding:     {agent_state.embedding}")
print(f"Created at:    {agent_state.created_at}")
print(f"Memory blocks: {len(agent_state.memory_blocks)} blocks")
```

## 5. Sending a Message — The Key Difference from Stateless APIs

With Letta, you send **only the new message** — the server manages all conversation
history and memory. You never send the full chat history yourself.

```python
# Send a message to your agent
# Notice: we send ONLY the new user message, NOT the full history!

response = client.agents.messages.create(
    agent_state.id,           # The agent ID from creation
    input="Hi! What do you know about me, and can you suggest a dbt model pattern for our Snowflake pipeline?"
)

# The response contains ALL messages generated in this turn
# (assistant response + any intermediate tool calls/memory updates)
print(f"Number of messages in response: {len(response.messages)}")
print("\n" + "="*60)

for i, msg in enumerate(response.messages):
    msg_type = getattr(msg, 'message_type', getattr(msg, 'role', 'unknown'))
    print(f"\n--- Message {i+1} (type: {msg_type}) ---")
    
    if hasattr(msg, 'content') and msg.content:
        # Print first 500 chars to keep notebook tidy
        content = msg.content if isinstance(msg.content, str) else str(msg.content)
        if len(content) > 500:
            print(content[:500] + "...")
        else:
            print(content)
    
    # Show tool calls if any
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"  → Tool: {tc.function.name}")
            print(f"    Args: {tc.function.arguments[:200]}")
```

## 6. Continuing a Conversation — Persistence in Action

Let's send a follow-up message to the SAME agent. The agent remembers
the previous turn automatically.

```python
# Send a follow-up — the agent remembers the first conversation!

response2 = client.agents.messages.create(
    agent_state.id,
    input="You mentioned a pattern earlier — can you write the actual dbt SQL for it?"
)

for msg in response2.messages:
    if hasattr(msg, 'content') and msg.content:
        print(msg.content[:800])
        print("---")
```

## 7. Retrieving an Existing Agent

You don't need to create a new agent every time. Retrieve an existing one by ID:

```python
# List all your agents
agents = client.agents.list()

print(f"You have {len(agents)} agent(s):")
for agent in agents:
    print(f"  • {agent.id} — {agent.model} (created {agent.created_at})")

# Retrieve a specific agent by ID
# my_agent = client.agents.retrieve(agent_id="agent-abc123")

# SAVE YOUR AGENT ID for reuse across notebooks!
print(f"\n💡 Save this ID for later: {agent_state.id}")
```

## 8. Listing Messages — Reading Conversation History

Access the full message history of an agent:

```python
# Get message history
messages = client.agents.messages.list(agent_state.id, limit=10)

print(f"Recent messages ({len(messages)} total):")
for msg in messages:
    role = getattr(msg, 'role', '?')[:10]
    content = getattr(msg, 'content', '') or ''
    preview = content[:80].replace('\n', ' ')
    print(f"  [{role}] {preview}..." if len(content) > 80 else f"  [{role}] {preview}")
```

## 9. Checking Memory Blocks

See what the agent has stored in its core memory:

```python
# Retrieve the agent's current memory blocks
agent = client.agents.retrieve(agent_state.id)

print("Current memory blocks:\n")
for block in agent.memory_blocks:
    print(f"  [{block.label}] (limit: {block.limit} chars)")
    print(f"  {'─' * 50}")
    print(f"  {block.value[:300]}")
    if len(block.value) > 300:
        print(f"  ... ({len(block.value)} total chars)")
    print()
```

## 10. Error Handling — Production Patterns

Proper error handling for Letta API calls:

```python
from letta_client import LettaError
import time

def send_message_safely(agent_id: str, message: str, max_retries: int = 3):
    """
    Send a message with retry logic for transient failures.
    
    Letta's API can occasionally return 429 (rate limit) or 5xx errors.
    This wrapper handles those gracefully.
    """
    for attempt in range(1, max_retries + 1):
        try:
            response = client.agents.messages.create(
                agent_id,
                input=message
            )
            return response
        
        except LettaError as e:
            # Rate limiting — back off and retry
            if "429" in str(e) or "rate" in str(e).lower():
                wait = 2 ** attempt  # Exponential backoff: 2, 4, 8 seconds
                print(f"Rate limited (attempt {attempt}/{max_retries}). "
                      f"Waiting {wait}s...")
                time.sleep(wait)
                continue
            # Non-retryable error
            print(f"Letta API error: {e}")
            raise
        
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise
    
    raise RuntimeError(f"Failed after {max_retries} retries")

# Example usage:
# response = send_message_safely(agent_state.id, "Hello!")
```

## 11. Streaming Responses (TypeScript V2 Only — Future Python Feature)

> Note: Streaming is currently available in the V2 Agent SDK (TypeScript).
> The Python V1 SDK returns complete responses. Check Letta's changelog for
> Python streaming support.

```typescript
// TypeScript V2 streaming example (for reference)
const session = client.createSession(agentId);
await session.send("What's the status?");

for await (const message of session.stream()) {
    if (message.type === "assistant") {
        console.log(message.content);
    }
}
```

## 12. Cleanup — Deleting Agents

When you're done testing, clean up your agents:

```python
Delete an agent (uncomment to use)
client.agents.delete(agent_state.id)
print(f"Agent {agent_state.id} deleted.")

Or delete ALL agents (use with caution!)
for agent in client.agents.list():
    client.agents.delete(agent.id)
    print(f"Deleted: {agent.id}")
```

## Key Takeaways

1. **Stateful by default** — agents persist between sessions. You create once, use many times.
2. **Memory blocks** — `human` and `persona` are the standard labels; the agent can edit them.
3. **Only send new messages** — never manage conversation history yourself.
4. **Save your agent ID** — you'll reuse it across notebooks and applications.

→ Next: `03_memory_blocks.ipynb` — deep dive into core memory management.
