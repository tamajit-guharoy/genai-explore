# 9. Integrations — Hindsight with Agent Frameworks

Hindsight offers **54 integrations** (48 official + 5 community) that plug persistent memory
into virtually every AI agent framework and tool. This section covers the most popular ones.

---

## Integration Architecture Patterns

Hindsight integrations follow three patterns:

| Pattern | How it works | Example integrations |
|---------|-------------|---------------------|
| **MCP Server** | Hindsight exposed as MCP tools | Claude Code, Cursor, Continue, Gemini Spark |
| **Framework Plugin** | Native SDK adapter for the framework | LangChain, CrewAI, Pydantic AI, Google ADK |
| **LLM Wrapper** | Transparent middleware intercepting LLM calls | LiteLLM, OpenAI Agents SDK |
| **Context Provider** | Automatic recall/retain on each agent turn | Microsoft Agent Framework, AG2 |

---

## MCP Server Integration

The MCP (Model Context Protocol) server is the most universal integration.
Any MCP-compatible client can use Hindsight.

### Starting the MCP Server

```bash
# Standalone MCP server (no full API needed)
hindsight-local-mcp
```

Or it's already available at `http://localhost:8888/mcp` when running the full server.

### Claude Code Configuration

Add to your Claude Code MCP config (`~/.claude/claude_desktop_config.json` or project `.mcp.json`):

```json
{
  "mcpServers": {
    "hindsight": {
      "command": "hindsight-local-mcp",
      "env": {
        "HINDSIGHT_API_LLM_PROVIDER": "openai",
        "HINDSIGHT_API_LLM_API_KEY": "***"
      }
    }
  }
}
```

Or connect to a running server:

```json
{
  "mcpServers": {
    "hindsight": {
      "type": "http",
      "url": "http://localhost:8888/mcp"
    }
  }
}
```

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `hindsight_retain` | Store a memory |
| `hindsight_recall` | Search memories |
| `hindsight_reflect` | Reason over memories |
| `hindsight_create_mental_model` | Create curated knowledge |
| `hindsight_list_mental_models` | List mental models |
| `hindsight_search_memories` | Raw memory search |

---

## LangChain / LangGraph Integration

```bash
pip install hindsight-langchain
```

### As Tools

```python
from hindsight_langchain import HindsightToolSpec

tools = HindsightToolSpec(
    bank_id="my-agent",
    api_url="http://localhost:8888"
).to_tool_list()

# Use in your LangChain agent
from langchain.agents import create_react_agent

agent = create_react_agent(llm, tools, prompt)
```

### As Memory Store

```python
from hindsight_langchain import HindsightMemoryStore

store = HindsightMemoryStore(
    bank_id="my-agent",
    api_url="http://localhost:8888"
)

# Use as LangChain BaseStore
store.mset([("user:prefs", "Python over JavaScript")])
value = store.mget(["user:prefs"])
```

### LangGraph Checkpointer

```python
from hindsight_langgraph import HindsightCheckpointer

checkpointer = HindsightCheckpointer(
    bank_id="my-graph",
    api_url="http://localhost:8888"
)

graph = create_graph().compile(checkpointer=checkpointer)
```

---

## CrewAI Integration

```bash
pip install hindsight-crewai
```

```python
from crewai import Agent, Task, Crew
from hindsight_crewai import HindsightMemory

# Create memory instance
memory = HindsightMemory(
    bank_id="my-crew",
    api_url="http://localhost:8888"
)

# Create agents with memory
researcher = Agent(
    role="Research Analyst",
    goal="Research market trends",
    memory=memory,     # ← Hindsight as memory
    llm=llm
)

writer = Agent(
    role="Content Writer",
    goal="Write market report",
    memory=memory,     # ← Same bank, shared memory
    llm=llm
)

# Run crew — agents share and learn from memories
crew = Crew(agents=[researcher, writer], tasks=[...])
result = crew.kickoff()
```

---

## Pydantic AI Integration

```bash
pip install hindsight-pydantic-ai
```

```python
from pydantic_ai import Agent
from hindsight_pydantic_ai import HindsightMemoryProvider

# Create provider
memory = HindsightMemoryProvider(
    bank_id="pydantic-agent",
    api_url="http://localhost:8888"
)

# Attach to agent
agent = Agent(
    "openai:gpt-4o",
    memory_provider=memory
)

# Memories auto-retained and auto-recalled
result = await agent.run("Remember my favorite color is blue")
result = await agent.run("What's my favorite color?")  # Recalls: blue
```

---

## Google ADK Integration

```bash
pip install hindsight-google-adk
```

```python
from google.adk import Agent
from hindsight_google_adk import HindsightMemoryService

# Create memory service
memory_service = HindsightMemoryService(
    bank_id="adk-agent",
    api_url="http://localhost:8888"
)

# Create agent with memory
agent = Agent(
    model="gemini-2.5-flash",
    memory_service=memory_service
)

# Memory persists across sessions automatically
```

---

## Microsoft Agent Framework Integration

```bash
pip install hindsight-agent-framework
```

```python
from agent_framework.openai import OpenAIChatClient
from hindsight_agent_framework import HindsightProvider

agent = OpenAIChatClient().as_agent(
    name="assistant",
    instructions="You are a helpful assistant.",
    context_providers=[
        HindsightProvider(bank_id="user-123")
    ]
)

# Automatic recall before each run, retain after
session = agent.create_session()
await agent.run("Remember that I prefer vegetarian food.", session=session)
await agent.run("Suggest a recipe.", session=session)  # Recalls vegetarian preference
```

---

## LiteLLM Integration (Zero Code Changes)

```bash
pip install hindsight-litellm
```

Configure via LiteLLM proxy config:

```yaml
# litellm_config.yaml
model_list:
  - model_name: gpt-4o
    litellm_params:
      model: openai/gpt-4o

litellm_settings:
  callbacks: ["hindsight_litellm"]
  hindsight:
    bank_id: "litellm-agent"
    api_url: "http://localhost:8888"
    auto_retain: true       # Automatically store every call
    auto_recall: true       # Inject memories into context
```

Then use any LLM normally — Hindsight handles memory transparently:

```python
import openai

client = openai.OpenAI(base_url="http://localhost:4000")  # LiteLLM proxy

# Memories are auto-stored and auto-recalled
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "My name is Alice and I work at Google"}
    ]
)

# Later — memories automatically injected
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Where do I work?"}
    ]
)
# Response: "You work at Google." ← recalled from Hindsight
```

---

## OpenClaw / Hermes Agent Integration

Hindsight can serve as a long-term memory backend for Hermes Agent and OpenClaw:

```bash
# In Hermes, add Hindsight as an MCP server
hermes mcp add hindsight --command hindsight-local-mcp
```

---

## OpenAI Agents SDK Integration

```bash
pip install hindsight-openai-agents
```

```python
from agents import Agent, Runner
from hindsight_openai_agents import HindsightTools

tools = HindsightTools(
    bank_id="openai-agent",
    api_url="http://localhost:8888"
)

agent = Agent(
    name="MemoryAgent",
    instructions="You have persistent memory via Hindsight tools.",
    tools=tools.as_tools()
)

result = await Runner.run(agent, "Remember this conversation")
```

---

## n8n Integration

Hindsight has a community node for n8n workflows:

1. Install the community node in n8n
2. Add Hindsight nodes to any workflow
3. Use Retain, Recall, and Reflect actions in your automation

---

## Integration Decision Tree

```
What's your agent framework?
│
├─ Claude Code / Cursor / Continue
│   → MCP Server (hindsight-local-mcp)
│
├─ LangChain / LangGraph
│   → hindsight-langchain (tools + BaseStore + checkpointer)
│
├─ CrewAI
│   → hindsight-crewai (Agent.memory)
│
├─ Pydantic AI
│   → hindsight-pydantic-ai (memory_provider)
│
├─ Google ADK
│   → hindsight-google-adk (memory_service)
│
├─ Microsoft Agent Framework
│   → hindsight-agent-framework (context_provider)
│
├─ OpenAI Agents SDK
│   → hindsight-openai-agents (tools)
│
├─ Anything using LiteLLM
│   → hindsight-litellm (zero code changes)
│
├─ Any MCP-compatible client
│   → MCP Server (universal)
│
└─ Custom / no framework
    → hindsight-client (direct API)
```

---

## Writing a Custom Integration

For frameworks not listed, use the HTTP API directly:

```python
import httpx

class CustomHindsightIntegration:
    def __init__(self, base_url, bank_id):
        self.base_url = base_url
        self.bank_id = bank_id
        self.client = httpx.AsyncClient(timeout=30)

    async def retain(self, content, **kwargs):
        resp = await self.client.post(
            f"{self.base_url}/v1/default/banks/{self.bank_id}/memories",
            json={"items": [{"content": content, **kwargs}]}
        )
        return resp.json()

    async def recall(self, query, **kwargs):
        resp = await self.client.post(
            f"{self.base_url}/v1/default/banks/{self.bank_id}/memories/recall",
            json={"query": query, **kwargs}
        )
        return resp.json()

    async def reflect(self, query, **kwargs):
        resp = await self.client.post(
            f"{self.base_url}/v1/default/banks/{self.bank_id}/reflect",
            json={"query": query, **kwargs}
        )
        return resp.json()

    async def close(self):
        await self.client.aclose()
```

---

Continue to:
- **[10_production.md](10_production.md)** — Production deployment
- Run the notebook: `notebooks/09_mcp_integration.ipynb`
