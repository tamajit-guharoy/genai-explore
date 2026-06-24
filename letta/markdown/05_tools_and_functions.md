# Tools & Function Calling — Extending Agent Capabilities

> **Goal**: Create custom tools that Letta agents can call. From simple
> calculator functions to API integrations — give your agents real-world abilities.

---

## 1. The Tool Model in Letta V1

In the V1 SDK, tools are **server-side functions** that Letta hosts and executes.
The agent calls them via standard function-calling, just like OpenAI/Anthropic tools.

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│  Agent   │────▶│ Letta Server │────▶│ Tool Runtime │
│ (LLM)    │     │ (Orchestrator)│     │ (Python VM)  │
└──────────┘     └──────────────┘     └──────────────┘
     │                                        │
     │  "call: get_weather(lat, lon)"          │
     │◀───────────────────────────────────────┘
     │              returns "72°F, sunny"
```

Available built-in tools: `web_search`, `fetch_webpage`, `run_code`,
and custom tools you define.

## 2. Setup

```python
from letta_client import Letta
import os

client = Letta(api_key=os.environ["LETTA_API_KEY"])
```

## 3. Creating an Agent with Built-In Tools

Letta includes built-in tools you can enable at creation time:

```python
# Create an agent with built-in web and code tools

agent_with_tools = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {"label": "human", "value": "Name: Alex\nRole: Developer", "limit": 2000},
        {"label": "persona", "value": "I am a helpful coding and research assistant.", "limit": 2000}
    ],
    # ── Enable built-in tools ──────────────────────────────────
    tools=[
        "web_search",      # Search the web via Tavily/Brave/etc.
        "fetch_webpage",   # Extract content from a URL
        "run_code"          # Execute Python code in a sandbox
    ]
)

AGENT_ID = agent_with_tools.id
print(f"Agent with tools: {AGENT_ID}")

# Check which tools are attached
agent = client.agents.retrieve(AGENT_ID)
if hasattr(agent, 'tools'):
    print(f"Tools enabled: {agent.tools}")
```

## 4. Using Built-In Tools — Web Search Example

Ask the agent something that requires web access:

```python
# The agent will call web_search on its own

response = client.agents.messages.create(
    AGENT_ID,
    input="What's the latest version of Python and what are the key new features?"
)

# Trace the tool calls
for msg in response.messages:
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"🔧 {tc.function.name}")
            args = tc.function.arguments[:200]
            print(f"   {args}")
    
    if hasattr(msg, 'content') and msg.content:
        text = msg.content if isinstance(msg.content, str) else str(msg.content)
        if text.strip():
            print(f"💬 {text[:500]}")
```

## 5. Custom Tools — Defining Your Own Functions

Custom tools are Python functions that run on Letta's server. Define them as:
1. A **JSON Schema** for the function signature
2. Python source code for the implementation

> Note: Custom tools are created via the Letta API/CLI, not inline in code.
> Here we show the pattern using the REST API concept.

```python
# ── DEFINING A CUSTOM TOOL ────────────────────────────────────
#
# Custom tools are defined with:
#   1. A name and description
#   2. A JSON Schema for parameters
#   3. Python source code
#
# This is the CONCEPTUAL pattern — actual creation is via REST API or CLI.
# See: https://docs.letta.com/guides/core-concepts/tools

custom_tool_definition = {
    "name": "calculate_mortgage",
    "description": (
        "Calculate monthly mortgage payment. "
        "Uses the standard amortization formula: M = P * r*(1+r)^n / ((1+r)^n - 1)"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "principal": {
                "type": "number",
                "description": "Loan principal amount in dollars"
            },
            "annual_rate": {
                "type": "number",
                "description": "Annual interest rate as percentage (e.g., 6.5 for 6.5%)"
            },
            "years": {
                "type": "integer",
                "description": "Loan term in years"
            }
        },
        "required": ["principal", "annual_rate", "years"]
    },
    "source_code": '''
def calculate_mortgage(principal: float, annual_rate: float, years: int) -> dict:
    """Calculate monthly mortgage payment."""
    monthly_rate = (annual_rate / 100) / 12
    num_payments = years * 12
    
    if monthly_rate == 0:
        monthly_payment = principal / num_payments
    else:
        monthly_payment = (
            principal
            * monthly_rate
            * (1 + monthly_rate) ** num_payments
        ) / ((1 + monthly_rate) ** num_payments - 1)
    
    total_paid = monthly_payment * num_payments
    total_interest = total_paid - principal
    
    return {
        "monthly_payment": round(monthly_payment, 2),
        "total_paid": round(total_paid, 2),
        "total_interest": round(total_interest, 2),
        "num_payments": num_payments
    }
'''
}

print("Custom tool definition ready.")
print(f"Tool name: {custom_tool_definition['name']}")
print(f"Parameters: {list(custom_tool_definition['parameters']['properties'].keys())}")
```

## 6. Tool Design Patterns

### Pattern 1: Calculator / Utility
```python
# Simple stateless computation
# Good for: math, date math, unit conversion, validation
def validate_email(email: str) -> dict:
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return {"valid": bool(re.match(pattern, email))}
```

### Pattern 2: API Client
```python
# Wrap external APIs
# Good for: weather, stocks, CRM, databases
def get_stock_price(symbol: str) -> dict:
    import requests  # Available in Letta's sandbox
    url = f"https://api.example.com/stocks/{symbol}"
    resp = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
    return resp.json()
```

### Pattern 3: Data Processing
```python
# Process data and return results
# Good for: analytics, summarization, formatting
def analyze_sentiment(text: str) -> dict:
    from textblob import TextBlob  # Available in sandbox
    blob = TextBlob(text)
    return {
        "polarity": blob.sentiment.polarity,
        "subjectivity": blob.sentiment.subjectivity
    }
```

### Pattern 4: Database Query
```python
# Read from databases
# Good for: SQL queries, vector searches, key-value lookups
def query_database(sql: str) -> dict:
    import sqlite3
    conn = sqlite3.connect("/data/app.db")
    cursor = conn.cursor()
    cursor.execute(sql)
    rows = cursor.fetchall()
    columns = [d[0] for d in cursor.description]
    return {"columns": columns, "rows": rows}
```

## 7. Tool Security Best Practices

Tools run in a sandboxed Python VM on Letta's server, but you should still:

| Practice | Why |
|----------|-----|
| Validate all inputs | Prevent injection, out-of-range errors |
| Set timeouts | Avoid runaway computations |
| Limit return size | Keep context window efficient |
| Use environment variables for secrets | Never hardcode API keys |
| Return structured JSON | Easier for the agent to parse |
| Handle errors gracefully | Return error messages, don't crash |

```python
# Example: Secure tool template

SECURE_TOOL_TEMPLATE = '''
def my_secure_tool(param1: str, param2: int) -> dict:
    """
    A secure, production-ready tool.
    """
    import os
    
    # 1. Validate inputs
    if not isinstance(param1, str) or len(param1) == 0:
        return {"error": "param1 must be a non-empty string"}
    if not isinstance(param2, int) or param2 < 0:
        return {"error": "param2 must be a positive integer"}
    
    # 2. Use env vars for secrets
    api_key = os.environ.get("MY_API_KEY")
    if not api_key:
        return {"error": "API key not configured"}
    
    # 3. Core logic with error handling
    try:
        result = {"processed": True, "input": param1, "count": param2}
        return {"status": "success", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
'''

print("Secure tool template ready.")
print(f"Template length: {len(SECURE_TOOL_TEMPLATE)} chars")
```

## 8. Managing Tools — List, Attach, Detach

Tools are managed at the server level, then attached to agents:

```python
# List available tools (built-in + custom)
# Note: The Python SDK may not expose a direct tools.list() endpoint.
# Tools are typically managed via the REST API or CLI.
#
# REST API concept:
# GET /v1/tools/ — list all tools
# POST /v1/tools/ — create a custom tool
# POST /v1/agents/{id}/tools/{tool_name} — attach tool to agent
# DELETE /v1/agents/{id}/tools/{tool_name} — detach tool from agent

print("""
Tool management via REST API:

  # List all tools
  curl https://api.letta.com/v1/tools/ \\
    -H "Authorization: Bearer $LETTA_API_KEY"

  # Create a custom tool
  curl -X POST https://api.letta.com/v1/tools/ \\
    -H "Authorization: Bearer $LETTA_API_KEY" \\
    -H "Content-Type: application/json" \\
    -d @my_tool.json

  # Attach tool to agent
  curl -X POST https://api.letta.com/v1/agents/{agent_id}/tools/my_tool \\
    -H "Authorization: Bearer $LETTA_API_KEY"
""")
```

## 9. Advanced: Run Code Tool

The `run_code` built-in lets the agent execute Python at runtime:

```python
# Ask the agent to write and run code

response = client.agents.messages.create(
    AGENT_ID,
    input=(
        "Calculate the compound annual growth rate (CAGR) for an investment "
        "that grew from $10,000 to $25,000 over 5.5 years. "
        "Use the run_code tool to compute this."
    )
)

# Show the tool interaction
for msg in response.messages:
    msg_type = getattr(msg, 'message_type', getattr(msg, 'role', '?'))
    
    if hasattr(msg, 'tool_calls') and msg.tool_calls:
        for tc in msg.tool_calls:
            print(f"🔧 {tc.function.name}")
            # Show the code it wrote (truncated)
            args = tc.function.arguments
            print(f"   {args[:300]}")
    
    if msg_type == 'tool' or hasattr(msg, 'name'):
        content = getattr(msg, 'content', str(msg))
        print(f"📦 Tool result: {str(content)[:200]}")
    
    if hasattr(msg, 'content') and msg.content:
        text = msg.content if isinstance(msg.content, str) else str(msg.content)
        if text.strip() and msg_type != 'tool':
            print(f"💬 {text[:400]}")
```

## 10. Tool Execution Flow — Step by Step

```
User: "What's the weather in San Francisco?"
    │
    ▼
LLM decides: "I need to call get_weather"
    │
    ▼
Tool Call: get_weather(lat=37.7749, lon=-122.4194)
    │
    ▼
Letta Server: executes tool in sandbox
    │
    ▼
Tool Result: {"temp": 65, "condition": "partly cloudy"}
    │
    ▼
LLM: "It's 65°F and partly cloudy in San Francisco right now."
    │
    ▼
User receives: final answer
```

The agent can call **multiple tools in sequence** — search the web, then
run code on the results, then save to archival memory — all in one turn.

## 11. Cleanup

```python
client.agents.delete(AGENT_ID)
print(f"Cleaned up agent: {AGENT_ID}")
```

## Key Takeaways

1. **Tools = agent superpowers** — web search, code execution, custom APIs.
2. **Built-in tools**: `web_search`, `fetch_webpage`, `run_code`.
3. **Custom tools**: Python functions with JSON Schema, run in sandbox.
4. **Security**: validate inputs, use env vars, return structured results.
5. **Multi-tool chains**: agents combine tools in one turn for complex tasks.

→ Next: `06_multi_agent_systems.ipynb` — orchestrating multiple agents.
