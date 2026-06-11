# Claude Console Tutorial

A practical guide to every section of [console.anthropic.com](https://console.anthropic.com) — covers both the **browser UI** (with ASCII mockups) and equivalent **Python SDK** code.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Workbench](#2-workbench)
3. [Files API](#3-files-api)
4. [Skills (Tool Use)](#4-skills-tool-use)
5. [Batch Processing](#5-batch-processing)
6. [Managed Agents](#6-managed-agents)
7. [Sessions](#7-sessions)
8. [Putting It All Together](#8-putting-it-all-together)
9. [Multi-Agent Architecture](#9-multi-agent-architecture)

---

## 1. Introduction

### What is Claude Console?

Claude Console is Anthropic's web dashboard at [console.anthropic.com](https://console.anthropic.com). It lets you:

- Manage API keys
- Prototype prompts in the Workbench
- Upload files for use in conversations
- Define reusable tools (Skills)
- Submit large batch jobs
- Create and monitor Managed Agents

### Browser: Sidebar Overview

When you log in, the left sidebar looks like this:

```
┌─────────────────────────────┐
│  ☁  Claude Console          │
│  ▾ Default  (org switcher)  │
├─────────────────────────────┤
│  🏠 Dashboard               │
│  🔑 API Keys                │
├─────────────────────────────┤
│  🔧 Build              ▾    │
│      Workbench              │
│      Files                  │
│      Skills                 │
│      Batches                │
├─────────────────────────────┤
│  🤖 Managed Agents     ▾    │
│      Quickstart             │
│      Agents                 │
│      Sessions               │
└─────────────────────────────┘
```

### Browser: Creating an API Key

1. Click **API Keys** in the sidebar
2. Click **+ Create Key**
3. Name it (e.g. `tutorial-key`) and click **Create**
4. Copy the key — it is shown **only once**

```
┌──────────────────────────────────────────────────────┐
│  API Keys                              [+ Create Key] │
├──────────────────────────────────────────────────────┤
│  Name            Created       Last Used    Actions   │
│  ─────────────────────────────────────────────────── │
│  tutorial-key    2026-05-31    Never        [Delete]  │
│  prod-key        2026-04-10    2026-05-30   [Delete]  │
└──────────────────────────────────────────────────────┘
```

### SDK Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env
```

---

## 2. Workbench

The Workbench is a zero-code playground. Every setting you change there maps 1-to-1 to an API parameter.

### 2.1 Running Your First Prompt

**In the browser:**

1. Go to **Build → Workbench**
2. Type in the message box and click **Run**

```
┌─────────────────────────────────────────────────────────────────┐
│  Workbench                                    [Model: Sonnet ▾] │
├────────────────────────┬────────────────────────────────────────┤
│  System  (optional)    │  Response                              │
│  ┌──────────────────┐  │  ┌──────────────────────────────────┐ │
│  │                  │  │  │ Paris is the capital of France.  │ │
│  └──────────────────┘  │  └──────────────────────────────────┘ │
│                        │                                        │
│  User message          │                                        │
│  ┌──────────────────┐  │                                        │
│  │ What is the      │  │                                        │
│  │ capital of       │  │                                        │
│  │ France?          │  │                                        │
│  └──────────────────┘  │                                        │
│              [Run ▶]   │                                        │
└────────────────────────┴────────────────────────────────────────┘
```

**SDK equivalent:**

```python
import anthropic

client = anthropic.Anthropic()

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(message.content[0].text)
# Paris is the capital of France.
```

---

### 2.2 Setting a System Prompt

**In the browser:** Click the **System** panel at the top of the Workbench and type your instructions.

```
┌─────────────────────────────────────────────────────────────────┐
│  Workbench                                    [Model: Sonnet ▾] │
├─────────────────────────────────────────────────────────────────┤
│  System                                                          │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ You are a pirate. Answer every question like a pirate.    │  │
│  └───────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  User: What is the capital of France?                [Run ▶]    │
├─────────────────────────────────────────────────────────────────┤
│  Assistant: Arrr, it be Paris, matey!                           │
└─────────────────────────────────────────────────────────────────┘
```

**SDK equivalent:**

```python
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    system="You are a pirate. Answer every question like a pirate.",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(message.content[0].text)
# Arrr, it be Paris, matey!
```

---

### 2.3 Switching Models

**In the browser:** Click the model dropdown in the top-right of the Workbench.

```
┌─────────────────────────────────────────────────────────────────┐
│  Workbench                             [Model: claude-sonnet ▾] │
│                                        ┌───────────────────────┐│
│                                        │ ● claude-opus-4-8     ││
│                                        │ ● claude-sonnet-4-6   ││
│                                        │ ● claude-haiku-4-5    ││
│                                        └───────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**SDK equivalent:**

```python
# Haiku — fastest, cheapest
msg_fast = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=128,
    messages=[{"role": "user", "content": "Summarize the water cycle in one sentence."}]
)

# Opus — most capable
msg_smart = client.messages.create(
    model="claude-opus-4-8",
    max_tokens=512,
    messages=[{"role": "user", "content": "Explain quantum entanglement to a 10-year-old."}]
)

print(msg_fast.content[0].text)
print(msg_smart.content[0].text)
```

---

### 2.4 Adjusting Temperature and Max Tokens

**In the browser:** Click the **⚙ Parameters** panel (right side or bottom of Workbench).

```
┌──────────────────────────────────────┐
│  Parameters                      ⚙  │
├──────────────────────────────────────┤
│  Max tokens                          │
│  [────────────●──────────]  1024     │
│                                      │
│  Temperature                         │
│  [●─────────────────────]  0.0       │
│   └ deterministic          creative  │
│                                      │
│  Top P                               │
│  [─────────────────────●]  1.0       │
└──────────────────────────────────────┘
```

**SDK equivalent:**

```python
# Deterministic — good for structured tasks
deterministic = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=64,
    temperature=0,
    messages=[{"role": "user", "content": "List the planets in order from the sun."}]
)

# Creative — good for brainstorming
creative = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    temperature=1,
    messages=[{"role": "user", "content": "Invent a name for a coffee shop on Mars."}]
)

print(deterministic.content[0].text)
print(creative.content[0].text)
```

---

### 2.5 Testing Tool Use Interactively

**In the browser:** Click **+ Add Tool** in the Workbench toolbar, fill in the JSON schema, then run a prompt. Claude highlights when it decides to call the tool.

```
┌─────────────────────────────────────────────────────────────────┐
│  Tools                                           [+ Add Tool]   │
├─────────────────────────────────────────────────────────────────┤
│  Tool name:   calculate                                         │
│  Description: Perform basic arithmetic                          │
│  Schema:                                                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ {                                                         │  │
│  │   "type": "object",                                       │  │
│  │   "properties": {                                         │  │
│  │     "expression": { "type": "string" }                   │  │
│  │   },                                                      │  │
│  │   "required": ["expression"]                             │  │
│  │ }                                                         │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                              [Save]  [Cancel]   │
└─────────────────────────────────────────────────────────────────┘
```

After adding the tool, Claude's response shows a tool-call block:

```
┌─────────────────────────────────────────────────────────────────┐
│  Assistant                                                       │
│  ┌─────────────────────────────────┐                            │
│  │ 🔧 Tool call: calculate         │                            │
│  │    expression: "144 / 12"       │                            │
│  └─────────────────────────────────┘                            │
│  The answer is 12.                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. Files API

The Files API lets you upload a file once and reference it by `file_id` across multiple API calls.

### 3.1 Uploading a File via the Console UI

**In the browser:**

1. Go to **Build → Files**
2. Click **Upload File**, pick a PDF or image
3. The file appears in the list with its `file_id`

```
┌──────────────────────────────────────────────────────────────────┐
│  Files                                          [Upload File ↑]  │
├──────────────────────────────────────────────────────────────────┤
│  Name                    Size     Created        ID              │
│  ──────────────────────────────────────────────────────────────  │
│  report.pdf              1.2 MB   2026-05-31     file_011CNm...  │
│  logo.png                84 KB    2026-05-30     file_08XyZa...  │
│                                                  [Copy] [Delete] │
└──────────────────────────────────────────────────────────────────┘
```

Click **Copy** next to any file to copy its `file_id` to the clipboard.

---

### 3.2 Uploading a File via SDK

```python
import anthropic

client = anthropic.Anthropic()

with open("report.pdf", "rb") as f:
    response = client.beta.files.upload(
        file=("report.pdf", f, "application/pdf"),
    )

file_id = response.id
print(f"Uploaded file ID: {file_id}")
# file_011CNmFnG39KMhPMku2YZBR8
```

---

### 3.3 Referencing a File in a Message

**In the browser:** In the Workbench, click the **📎 Attach** icon → choose **Existing file** → pick by `file_id`.

```
┌──────────────────────────────────────────────────────┐
│  Attach content                                      │
│  ○ Upload new file                                   │
│  ● Use existing file                                 │
│    ┌──────────────────────────────────────────────┐  │
│    │ file_011CNmFnG39KMhPMku2YZBR8  report.pdf   │  │
│    │ file_08XyZaBcDeFgH             logo.png      │  │
│    └──────────────────────────────────────────────┘  │
│                               [Attach]  [Cancel]     │
└──────────────────────────────────────────────────────┘
```

**SDK equivalent:**

```python
message = client.beta.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Summarize the key findings in this report."
                },
                {
                    "type": "document",
                    "source": {
                        "type": "file",
                        "file_id": file_id   # reference — no re-upload
                    }
                }
            ]
        }
    ],
    betas=["files-api-2025-04-14"],
)

print(message.content[0].text)
```

---

### 3.4 Listing and Deleting Files

**In the browser:** All files are visible in **Build → Files**. Click **Delete** (trash icon) to remove one.

**SDK equivalent:**

```python
# List all uploaded files
files = client.beta.files.list()
for f in files.data:
    print(f.id, f.filename, f.created_at)

# Delete a file when no longer needed
client.beta.files.delete(file_id)
print("File deleted.")
```

---

## 4. Skills (Tool Use)

Skills are tools defined with JSON Schema that Claude can call during a conversation.

### 4.1 Defining a Tool in the Workbench

**In the browser:** In the Workbench toolbar click **+ Add Tool**.

```
┌──────────────────────────────────────────────────────────────────┐
│  Add Tool                                                        │
├──────────────────────────────────────────────────────────────────┤
│  Name *          │  calculate                                    │
│  Description *   │  Perform basic arithmetic                     │
│  Input schema *  │                                               │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ {                                                          │  │
│  │   "type": "object",                                        │  │
│  │   "properties": {                                          │  │
│  │     "expression": {                                        │  │
│  │       "type": "string",                                    │  │
│  │       "description": "e.g. '12 * 7'"                      │  │
│  │     }                                                      │  │
│  │   },                                                       │  │
│  │   "required": ["expression"]                              │  │
│  │ }                                                          │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                              [Add]  [Cancel]     │
└──────────────────────────────────────────────────────────────────┘
```

After adding, run any math prompt — the Workbench shows the tool call inline:

```
┌──────────────────────────────────────────────────────────────────┐
│  User:  What is 144 divided by 12?                               │
├──────────────────────────────────────────────────────────────────┤
│  Assistant:                                                       │
│  ┌──────────────────────────────┐                                │
│  │ 🔧 calculate                 │                                │
│  │    { "expression": "144/12" }│                                │
│  └──────────────────────────────┘                                │
│  → Tool result: 12                                               │
│  144 divided by 12 is 12.                                        │
└──────────────────────────────────────────────────────────────────┘
```

---

### 4.2 Defining a Tool via SDK

```python
import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "calculate",
        "description": "Perform basic arithmetic. Use this for any math question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "A math expression like '12 * 7' or '100 / 4'"
                }
            },
            "required": ["expression"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    tools=tools,
    messages=[{"role": "user", "content": "What is 144 divided by 12?"}]
)

print(response.stop_reason)          # tool_use
print(response.content[1].name)      # calculate
print(response.content[1].input)     # {'expression': '144 / 12'}
```

---

### 4.3 Handling the Tool Result

```python
def run_tool(name, inputs):
    if name == "calculate":
        return str(eval(inputs["expression"]))  # noqa: S307

tool_use_block = next(b for b in response.content if b.type == "tool_use")
result = run_tool(tool_use_block.name, tool_use_block.input)

follow_up = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    tools=tools,
    messages=[
        {"role": "user", "content": "What is 144 divided by 12?"},
        {"role": "assistant", "content": response.content},
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_block.id,
                    "content": result
                }
            ]
        }
    ]
)

print(follow_up.content[0].text)
# 144 divided by 12 is 12.
```

---

### 4.4 Multi-Tool Example — Search + Format

```python
tools = [
    {
        "name": "search_web",
        "description": "Search the web for current information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "format_table",
        "description": "Format a list of items as a markdown table.",
        "input_schema": {
            "type": "object",
            "properties": {
                "headers": {"type": "array", "items": {"type": "string"}},
                "rows": {
                    "type": "array",
                    "items": {"type": "array", "items": {"type": "string"}}
                }
            },
            "required": ["headers", "rows"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=512,
    tools=tools,
    messages=[{"role": "user", "content": "Show me the top 3 programming languages in a table."}]
)

for block in response.content:
    if block.type == "tool_use":
        print(f"Tool called: {block.name}")
        print(f"Input: {block.input}")
```

---

### 4.5 Forcing Tool Use with `tool_choice`

```python
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=256,
    tools=tools[:1],
    tool_choice={"type": "tool", "name": "calculate"},
    messages=[{"role": "user", "content": "What is 7 times 8?"}]
)

print(response.stop_reason)       # tool_use — guaranteed
print(response.content[0].input)  # {'expression': '7 * 8'}
```

---

## 5. Batch Processing

Batch processes up to 10,000 requests asynchronously at 50% cost savings.

### 5.1 Viewing Batches in the Browser

Go to **Build → Batches** to see all jobs and their status.

```
┌──────────────────────────────────────────────────────────────────────────┐
│  Batches                                                                  │
├──────────────────────────────────────────────────────────────────────────┤
│  ID                  Requests   Status        Created       Results       │
│  ────────────────────────────────────────────────────────────────────── │
│  batch_01AbCd...     3          ended ✓       2026-05-31    [Download]   │
│  batch_01XyZw...     1000       in_progress   2026-05-31    —            │
│  batch_01MnOp...     500        ended ✓       2026-05-30    [Download]   │
└──────────────────────────────────────────────────────────────────────────┘
```

Click **Download** to get a `.jsonl` results file for any completed batch.

Each row also shows counts:

```
┌─────────────────────────────────────────────────────┐
│  batch_01AbCd...  ▸ Details                          │
│  ─────────────────────────────────────────────────  │
│  Succeeded   3                                       │
│  Errored     0                                       │
│  Expired     0                                       │
│  Canceled    0                                       │
│  Created     2026-05-31T10:22:00Z                    │
│  Ended       2026-05-31T10:23:47Z                    │
└─────────────────────────────────────────────────────┘
```

---

### 5.2 Creating a Batch via SDK

```python
import anthropic

client = anthropic.Anthropic()

batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": "q1",
            "params": {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 64,
                "messages": [{"role": "user", "content": "Capital of Japan?"}]
            }
        },
        {
            "custom_id": "q2",
            "params": {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 64,
                "messages": [{"role": "user", "content": "Capital of Brazil?"}]
            }
        },
        {
            "custom_id": "q3",
            "params": {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 64,
                "messages": [{"role": "user", "content": "Capital of Australia?"}]
            }
        },
    ]
)

print(f"Batch ID: {batch.id}")
print(f"Status:   {batch.processing_status}")
# Status: in_progress
```

---

### 5.3 Checking Batch Status via SDK

```python
import time

batch_id = batch.id

while True:
    status = client.messages.batches.retrieve(batch_id)
    print(f"Status: {status.processing_status} | "
          f"Succeeded: {status.request_counts.succeeded} | "
          f"Processing: {status.request_counts.processing}")

    if status.processing_status == "ended":
        break
    time.sleep(5)
```

---

### 5.4 Retrieving Batch Results

```python
results = client.messages.batches.results(batch_id)

for result in results:
    if result.result.type == "succeeded":
        print(f"[{result.custom_id}] {result.result.message.content[0].text}")
    else:
        print(f"[{result.custom_id}] ERROR: {result.result.error}")

# [q1] The capital of Japan is Tokyo.
# [q2] The capital of Brazil is Brasília.
# [q3] The capital of Australia is Canberra.
```

---

### 5.5 Error Handling in Batches

```python
results = client.messages.batches.results(batch_id)

succeeded, failed = [], []
for result in results:
    if result.result.type == "succeeded":
        succeeded.append(result)
    else:
        failed.append(result)

print(f"Succeeded: {len(succeeded)}, Failed: {len(failed)}")

for r in failed:
    print(f"  {r.custom_id}: {r.result.error.type} — {r.result.error.message}")
```

---

## 6. Managed Agents

Managed Agents are persistent, stateful agents you define once and call repeatedly.

### 6.1 Creating an Agent in the Browser

Go to **Managed Agents → Agents → Create Agent**.

```
┌──────────────────────────────────────────────────────────────────┐
│  Create Agent                                                    │
├──────────────────────────────────────────────────────────────────┤
│  Name *                                                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ customer-support                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Model *            [claude-sonnet-4-6              ▾]          │
│                                                                  │
│  System Prompt                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ You are a helpful customer support agent for Acme Corp.  │   │
│  │ Be polite, concise, and escalate complex issues.         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Tools                                    [+ Add Tool]          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ (none attached)                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                      [Cancel]  [Create Agent]   │
└──────────────────────────────────────────────────────────────────┘
```

After saving, you'll see the agent in the list:

```
┌────────────────────────────────────────────────────────────────────┐
│  Agents                                          [Create Agent +]  │
├────────────────────────────────────────────────────────────────────┤
│  Name                Model            ID             Actions       │
│  ────────────────────────────────────────────────────────────────  │
│  customer-support    sonnet-4-6       agt_01XyZ...   [Edit][Del]  │
│  sql-helper          sonnet-4-6       agt_02AbC...   [Edit][Del]  │
└────────────────────────────────────────────────────────────────────┘
```

---

### 6.2 Testing an Agent in the Browser (Quickstart)

Go to **Managed Agents → Quickstart** to chat with any agent directly in the browser without writing any code:

```
┌──────────────────────────────────────────────────────────────────┐
│  Quickstart                  Agent: [customer-support ▾]         │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│  🤖 Hi! I'm your customer support agent. How can I help today?   │
│                                                                   │
│  👤 I need to reset my password.                                  │
│                                                                   │
│  🤖 Sure! Go to login page → click "Forgot password" → enter     │
│     your email. You'll receive a reset link in 2 minutes.        │
│                                                                   │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────┐    │
│  │ Type a message...                              [Send ▶]  │    │
│  └──────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────┘
```

---

### 6.3 Calling an Agent via SDK

```python
import anthropic

client = anthropic.Anthropic()

AGENT_ID = "agt_01XyzAbcDef..."   # from the Console

session = client.beta.managed_agents.sessions.create(
    agent_id=AGENT_ID,
    messages=[
        {"role": "user", "content": "Hello! What can you help me with today?"}
    ]
)

print(session.id)                       # sess_... — save for follow-ups
print(session.messages[-1]["content"])  # agent's response
```

---

### 6.4 Passing Context Between Turns

```python
session_id = session.id

follow_up = client.beta.managed_agents.sessions.continue_session(
    session_id=session_id,
    messages=[
        {"role": "user", "content": "Can you help me reset my password?"}
    ]
)

print(follow_up.messages[-1]["content"])
```

---

### 6.5 Creating an Agent via SDK

```python
agent = client.beta.managed_agents.agents.create(
    name="sql-helper",
    model="claude-sonnet-4-6",
    system_prompt=(
        "You are a SQL expert. "
        "When given a question, write a clean, commented SQL query. "
        "Always use CTEs for complex queries."
    ),
)

print(agent.id)    # agt_...
print(agent.name)  # sql-helper
```

---

### 6.6 Listing All Agents

```python
agents = client.beta.managed_agents.agents.list()

for a in agents.data:
    print(f"{a.id}  {a.name}  model={a.model}")
```

---

## 7. Sessions

Sessions store the complete message history of an agent conversation.

### 7.1 Viewing Sessions in the Browser

Go to **Managed Agents → Sessions** to see all conversations:

```
┌────────────────────────────────────────────────────────────────────────┐
│  Sessions                              Agent: [All agents ▾]  [Search] │
├────────────────────────────────────────────────────────────────────────┤
│  Session ID          Agent              Turns   Created        Status  │
│  ────────────────────────────────────────────────────────────────────  │
│  sess_01AbCd...      customer-support   4       2026-05-31     Active  │
│  sess_01XyZw...      sql-helper         2       2026-05-30     Ended   │
│  sess_01MnOp...      customer-support   6       2026-05-29     Ended   │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 7.2 Inspecting a Session in the Browser

Click any session ID to see the full message thread:

```
┌──────────────────────────────────────────────────────────────────┐
│  Session: sess_01AbCd...                                         │
│  Agent: customer-support   Model: sonnet-4-6   Turns: 4          │
├──────────────────────────────────────────────────────────────────┤
│  👤 USER  10:22:01                                                │
│  Hello! What can you help me with today?                         │
├──────────────────────────────────────────────────────────────────┤
│  🤖 ASSISTANT  10:22:02                                           │
│  Hi! I can help with account issues, billing, and general        │
│  product questions. What do you need?                            │
├──────────────────────────────────────────────────────────────────┤
│  👤 USER  10:23:10                                                │
│  I need to reset my password.                                    │
├──────────────────────────────────────────────────────────────────┤
│  🤖 ASSISTANT  10:23:11                                           │
│  Sure! Go to login page → Forgot password → enter email.        │
│                                                                  │
│  Tokens used: 312 input / 58 output                              │
└──────────────────────────────────────────────────────────────────┘
```

---

### 7.3 Listing Sessions via SDK

```python
sessions = client.beta.managed_agents.sessions.list(
    agent_id=AGENT_ID,
    limit=10
)

for s in sessions.data:
    print(f"{s.id}  created={s.created_at}  turns={len(s.messages)}")
```

---

### 7.4 Inspecting a Session via SDK

```python
session_detail = client.beta.managed_agents.sessions.retrieve(
    session_id="sess_01AbcDef..."
)

for msg in session_detail.messages:
    role = msg["role"].upper()
    content = msg["content"] if isinstance(msg["content"], str) else "[tool call]"
    print(f"[{role}] {content[:120]}")
```

---

### 7.5 Deleting a Session

**In the browser:** Click the **⋯** menu on any session row → **Delete**.

**SDK equivalent:**

```python
client.beta.managed_agents.sessions.delete(
    session_id="sess_01AbcDef..."
)
print("Session deleted.")
```

---

## 8. Putting It All Together

An end-to-end pipeline entirely in code: upload a file → create an agent → start a session with the document → batch follow-up questions.

### Browser Flow Summary

```
Build → Files          Upload quarterly_report.pdf  →  copy file_id
Managed Agents         Create "report-analyst" agent →  copy agent_id
Managed Agents →       Quickstart: verify agent works in browser
  Quickstart
(run script below)     Batch 4 questions, poll, print answers
Build → Batches        Verify batch status and download results
```

### Full Script

```python
import anthropic
import time

client = anthropic.Anthropic()

# ── Step 1: Upload a document ──────────────────────────────────────────────
with open("quarterly_report.pdf", "rb") as f:
    uploaded = client.beta.files.upload(
        file=("quarterly_report.pdf", f, "application/pdf"),
    )
file_id = uploaded.id
print(f"[1] File uploaded: {file_id}")

# ── Step 2: Create an agent ────────────────────────────────────────────────
agent = client.beta.managed_agents.agents.create(
    name="report-analyst",
    model="claude-sonnet-4-6",
    system_prompt=(
        "You are a financial analyst. "
        "Answer questions based only on the provided report. "
        "Be concise and cite specific figures when possible."
    ),
)
print(f"[2] Agent created: {agent.id}")

# ── Step 3: Start a session with the document ──────────────────────────────
session = client.beta.managed_agents.sessions.create(
    agent_id=agent.id,
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Here is our quarterly report. Please acknowledge you received it."
                },
                {
                    "type": "document",
                    "source": {"type": "file", "file_id": file_id}
                }
            ]
        }
    ],
    betas=["files-api-2025-04-14"],
)
session_id = session.id
print(f"[3] Session started: {session_id}")
print(f"    Agent: {session.messages[-1]['content'][:80]}...")

# ── Step 4: Batch follow-up questions ─────────────────────────────────────
questions = [
    "What was total revenue this quarter?",
    "Which product line grew the fastest?",
    "What are the top 3 risks mentioned?",
    "What is the guidance for next quarter?",
]

batch = client.messages.batches.create(
    requests=[
        {
            "custom_id": f"q{i}",
            "params": {
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 128,
                "messages": [{"role": "user", "content": q}]
            }
        }
        for i, q in enumerate(questions)
    ]
)
print(f"[4] Batch submitted: {batch.id}")

# ── Step 5: Poll for batch completion ─────────────────────────────────────
while True:
    status = client.messages.batches.retrieve(batch.id)
    if status.processing_status == "ended":
        break
    print(f"    Waiting... ({status.request_counts.processing} remaining)")
    time.sleep(5)

# ── Step 6: Print results ──────────────────────────────────────────────────
print("\n[5] Batch Results:")
for result in client.messages.batches.results(batch.id):
    idx = int(result.custom_id[1:])
    answer = (
        result.result.message.content[0].text
        if result.result.type == "succeeded"
        else "ERROR"
    )
    print(f"  Q: {questions[idx]}")
    print(f"  A: {answer}\n")

# ── Cleanup ────────────────────────────────────────────────────────────────
client.beta.files.delete(file_id)
print("[6] File cleaned up.")
```

---

## 9. Multi-Agent Architecture

Managed Agents don't have a built-in "spawn sub-agent" button, but you can compose them into
supervisor/sub-agent trees using **agent-as-tool**: the supervisor agent has tools whose names
match your sub-agents. Your orchestration layer (Python) intercepts each tool call and dispatches
it to the right sub-agent session.

### 9.1 Architecture Overview

```
                        ┌─────────────────────────────┐
          User ────────▶│     Supervisor Agent         │
                        │  system: "You are a router.  │
                        │   Delegate tasks to the      │
                        │   right specialist."         │
                        │                              │
                        │  tools:                      │
                        │    call_researcher           │
                        │    call_writer               │
                        │    call_sql_expert           │
                        └──────┬──────────┬────────────┘
                               │          │
               ┌───────────────┘          └─────────────────┐
               ▼                                             ▼
  ┌────────────────────────┐               ┌────────────────────────┐
  │   Researcher Agent     │               │    Writer Agent        │
  │  system: "Search and   │               │  system: "Turn facts   │
  │   summarise topics."   │               │   into clear prose."   │
  └────────────────────────┘               └────────────────────────┘
                                                        │
                               ┌────────────────────────┘
                               ▼
                  ┌────────────────────────┐
                  │    SQL Expert Agent    │
                  │  system: "Write SQL    │
                  │   queries from plain   │
                  │   English."            │
                  └────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────┐
  │  Your Python code = the orchestration layer                     │
  │  It intercepts supervisor tool calls → routes to sub-agents     │
  │  → feeds results back to supervisor → loops until done          │
  └─────────────────────────────────────────────────────────────────┘
```

---

### 9.2 Browser: Setting Up the Agents

**Step 1 — Create each sub-agent** in **Managed Agents → Agents → Create Agent**:

```
┌──────────────────────────────────────────────────────────────────┐
│  Agents                                          [Create Agent]  │
├──────────────────────────────────────────────────────────────────┤
│  Name              Model          ID              Role           │
│  ────────────────────────────────────────────────────────────    │
│  researcher        haiku-4-5      agt_res_01...   Sub-agent      │
│  writer            haiku-4-5      agt_wri_01...   Sub-agent      │
│  sql-expert        sonnet-4-6     agt_sql_01...   Sub-agent      │
│  supervisor        sonnet-4-6     agt_sup_01...   Orchestrator   │
└──────────────────────────────────────────────────────────────────┘
```

**Step 2 — On the supervisor agent, add one tool per sub-agent** via **Edit → + Add Tool**:

```
┌──────────────────────────────────────────────────────────────────┐
│  Edit Agent: supervisor                                          │
│  Tools                                           [+ Add Tool]   │
├──────────────────────────────────────────────────────────────────┤
│  call_researcher  — "Delegate a research task"     [Edit][Del]  │
│  call_writer      — "Delegate a writing task"      [Edit][Del]  │
│  call_sql_expert  — "Delegate a SQL query task"    [Edit][Del]  │
└──────────────────────────────────────────────────────────────────┘
```

Tool schema for each (same pattern, change the name/description):

```
┌──────────────────────────────────────────────────────────────────┐
│  Tool: call_researcher                                           │
│  Description: Delegate a research or information-lookup task     │
│  Schema:                                                         │
│  {                                                               │
│    "type": "object",                                             │
│    "properties": {                                               │
│      "task": {                                                   │
│        "type": "string",                                         │
│        "description": "The research question or task"           │
│      }                                                           │
│    },                                                            │
│    "required": ["task"]                                          │
│  }                                                               │
└──────────────────────────────────────────────────────────────────┘
```

**Step 3 — Test in Quickstart** by talking to the supervisor. You'll see it decide which tool to call:

```
┌──────────────────────────────────────────────────────────────────┐
│  Quickstart                    Agent: [supervisor ▾]             │
├──────────────────────────────────────────────────────────────────┤
│  👤 Write me a short blog post about electric cars.              │
│                                                                   │
│  🤖 ┌──────────────────────────────────────┐                    │
│     │ 🔧 call_researcher                   │                    │
│     │    { "task": "key facts about        │                    │
│     │       electric cars in 2026" }       │                    │
│     └──────────────────────────────────────┘                    │
│     [Your orchestration layer routes this to researcher-agent]  │
└──────────────────────────────────────────────────────────────────┘
```

---

### 9.3 Example 1 — Supervisor with Two Sub-Agents (Researcher + Writer)

```python
import anthropic

client = anthropic.Anthropic()

# ── Agent IDs (paste from the Console after creating them) ────────────────
SUPERVISOR_ID  = "agt_sup_01..."
RESEARCHER_ID  = "agt_res_01..."
WRITER_ID      = "agt_wri_01..."

# ── Tool definitions the supervisor knows about ───────────────────────────
SUPERVISOR_TOOLS = [
    {
        "name": "call_researcher",
        "description": "Delegate a research or fact-finding task to the researcher agent.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "The research question"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "call_writer",
        "description": "Delegate a writing task. Pass research notes to turn into prose.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Writing instructions + any notes"}
            },
            "required": ["task"]
        }
    }
]

# ── Dispatch: route a tool call to the matching sub-agent ─────────────────
def call_sub_agent(agent_id: str, task: str) -> str:
    session = client.beta.managed_agents.sessions.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": task}]
    )
    return session.messages[-1]["content"]

TOOL_ROUTING = {
    "call_researcher": RESEARCHER_ID,
    "call_writer":     WRITER_ID,
}

# ── Orchestration loop ────────────────────────────────────────────────────
def run_supervisor(user_request: str) -> str:
    messages = [{"role": "user", "content": user_request}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=(
                "You are a supervisor. Break the user's request into subtasks. "
                "Use call_researcher for facts and call_writer to produce the final text. "
                "Return the final answer once writing is complete."
            ),
            tools=SUPERVISOR_TOOLS,
            messages=messages,
        )

        # Collect tool calls
        tool_calls = [b for b in response.content if b.type == "tool_use"]

        if not tool_calls:
            # No more tool calls — final answer
            final = next(b for b in response.content if b.type == "text")
            return final.text

        # Append supervisor's response turn
        messages.append({"role": "assistant", "content": response.content})

        # Execute each tool call → feed results back
        tool_results = []
        for tc in tool_calls:
            agent_id = TOOL_ROUTING[tc.name]
            print(f"  → Routing to {tc.name} (task: {tc.input['task'][:60]}...)")
            result = call_sub_agent(agent_id, tc.input["task"])
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result
            })

        messages.append({"role": "user", "content": tool_results})


# ── Run it ────────────────────────────────────────────────────────────────
answer = run_supervisor("Write a short blog post about electric cars in 2026.")
print(answer)
```

**What happens step by step:**

```
User: "Write a short blog post about electric cars in 2026."

Supervisor → call_researcher("key facts and stats about EVs in 2026")
  Researcher agent responds: "Global EV sales hit 22M in 2026, 35% market share..."

Supervisor → call_writer("Write a 200-word blog post using these facts: ...")
  Writer agent responds: "Electric cars are no longer the future — they're the now..."

Supervisor returns final text to user.
```

---

### 9.4 Example 2 — Three Specialist Sub-Agents (SQL + Search + Formatter)

```python
import anthropic

client = anthropic.Anthropic()

SUPERVISOR_ID  = "agt_sup_01..."
SQL_ID         = "agt_sql_01..."
SEARCH_ID      = "agt_srch_01..."
FORMATTER_ID   = "agt_fmt_01..."

SUPERVISOR_TOOLS = [
    {
        "name": "call_sql_expert",
        "description": "Generate or explain a SQL query from plain English.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "call_search",
        "description": "Search for documentation or external information.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"}
            },
            "required": ["query"]
        }
    },
    {
        "name": "call_formatter",
        "description": "Format raw text or data into clean markdown or HTML.",
        "input_schema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "format":  {"type": "string", "enum": ["markdown", "html", "plain"]}
            },
            "required": ["content", "format"]
        }
    }
]

TOOL_ROUTING = {
    "call_sql_expert": SQL_ID,
    "call_search":     SEARCH_ID,
    "call_formatter":  FORMATTER_ID,
}

def call_sub_agent(agent_id: str, task: str) -> str:
    session = client.beta.managed_agents.sessions.create(
        agent_id=agent_id,
        messages=[{"role": "user", "content": task}]
    )
    return session.messages[-1]["content"]

def run_supervisor(user_request: str) -> str:
    messages = [{"role": "user", "content": user_request}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=(
                "You are a data assistant supervisor. "
                "Use call_sql_expert for queries, call_search for docs, "
                "call_formatter to clean up output. Return the final result."
            ),
            tools=SUPERVISOR_TOOLS,
            messages=messages,
        )

        tool_calls = [b for b in response.content if b.type == "tool_use"]

        if not tool_calls:
            return next(b for b in response.content if b.type == "text").text

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tc in tool_calls:
            agent_id = TOOL_ROUTING[tc.name]
            task = tc.input.get("task") or tc.input.get("query") or tc.input.get("content", "")
            print(f"  → {tc.name}: {task[:60]}")
            result = call_sub_agent(agent_id, task)
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tc.id,
                "content": result
            })

        messages.append({"role": "user", "content": tool_results})


answer = run_supervisor(
    "Show me a SQL query to get monthly revenue for 2025, "
    "then format the result as a markdown table."
)
print(answer)
```

---

### 9.5 Parallel Sub-Agent Calls

When the supervisor issues **multiple tool calls in one turn**, you can dispatch them in parallel:

```python
import concurrent.futures

def dispatch_parallel(tool_calls: list) -> list:
    def execute(tc):
        agent_id = TOOL_ROUTING[tc.name]
        task = next(iter(tc.input.values()))   # first input value
        result = call_sub_agent(agent_id, task)
        return {"type": "tool_result", "tool_use_id": tc.id, "content": result}

    with concurrent.futures.ThreadPoolExecutor() as pool:
        futures = [pool.submit(execute, tc) for tc in tool_calls]
        return [f.result() for f in concurrent.futures.as_completed(futures)]
```

Replace the serial loop in the orchestrator with:

```python
tool_results = dispatch_parallel(tool_calls)
messages.append({"role": "user", "content": tool_results})
```

Supervisor turn with two simultaneous sub-agent calls completes in the time of the slowest one,
not the sum.

---

### 9.6 Passing Results Between Sub-Agents (Chain Mode)

Sometimes sub-agent B needs the output of sub-agent A directly:

```python
# Researcher produces notes, Writer receives them as context
research_notes = call_sub_agent(RESEARCHER_ID, "Key EV stats for 2026")

blog_post = call_sub_agent(
    WRITER_ID,
    f"Write a 200-word blog post using ONLY these facts:\n\n{research_notes}"
)

print(blog_post)
```

This is useful when the supervisor doesn't need to reason between steps — just pipe outputs.

---

### 9.7 Architecture Patterns Summary

| Pattern | When to use | How |
|---|---|---|
| Supervisor routes to one agent | Task needs a specialist | Single tool call per turn |
| Supervisor fans out | Multiple independent subtasks | Multiple tool calls in one turn → `dispatch_parallel` |
| Chained pipeline | B depends on A's output | Pass A's result as input to B |
| Supervisor loops | Multi-step reasoning needed | Keep the `while True` loop running until no tool calls |
| Flat multi-agent | No hierarchy needed | Call agents directly from your app code, no supervisor |

---



| Task | Browser path | SDK method |
|---|---|---|
| Create API key | API Keys → Create Key | — |
| Run a prompt | Workbench → Run | `client.messages.create()` |
| Set system prompt | Workbench → System panel | `system=` param |
| Change model | Workbench → model dropdown | `model=` param |
| Set temperature | Workbench → Parameters ⚙ | `temperature=` param |
| Upload file | Files → Upload File | `client.beta.files.upload()` |
| Reference file | Workbench → Attach → Existing | `{"type":"file","file_id":"..."}` |
| Delete file | Files → Delete icon | `client.beta.files.delete()` |
| Define tool | Workbench → Add Tool | `tools=[...]` param |
| Force tool call | — | `tool_choice={"type":"tool",...}` |
| View batches | Batches → list | `client.messages.batches.list()` |
| Create batch | — | `client.messages.batches.create()` |
| Create agent | Managed Agents → Agents → Create | `client.beta.managed_agents.agents.create()` |
| Test agent | Managed Agents → Quickstart | `client.beta.managed_agents.sessions.create()` |
| View sessions | Managed Agents → Sessions | `client.beta.managed_agents.sessions.list()` |
| Inspect session | Sessions → click row | `client.beta.managed_agents.sessions.retrieve()` |
| Build supervisor | Agents → add tool per sub-agent | `tools=[call_researcher, ...]` on supervisor |
| Route tool call | — | `TOOL_ROUTING[tc.name]` → `call_sub_agent()` |
| Parallel sub-agents | — | `ThreadPoolExecutor` over tool calls |

---

*All SDK examples use the `anthropic` Python SDK. Install with `pip install anthropic`.*
