# Claude Code Hooks — Complete Tutorial

Hooks are shell commands that Claude Code executes automatically in response to specific lifecycle events. They let you enforce policies, automate side effects, log activity, and guard against dangerous actions — all without relying on Claude's judgment.

---

## Table of Contents

1. [How Hooks Work](#how-hooks-work)
2. [Configuration Structure](#configuration-structure)
3. [Hook Events](#hook-events)
4. [Data Passed to Hooks](#data-passed-to-hooks)
5. [Hook Return Values](#hook-return-values)
6. [Matcher Patterns](#matcher-patterns)
7. [Event Examples: UserPromptSubmit](#event-examples-userpromptsubmit)
8. [Event Examples: PreToolUse](#event-examples-pretooluse)
9. [Event Examples: PostToolUse](#event-examples-posttooluse)
10. [Event Examples: Stop](#event-examples-stop)
11. [Event Examples: Notification](#event-examples-notification)
12. [Multi-Hook Chains](#multi-hook-chains)
13. [Hook Scripts in Different Languages](#hook-scripts-in-different-languages)
14. [Limitations](#limitations)

---

## How Hooks Work

```
User types message
      │
      ▼
[UserPromptSubmit hook] ──block?──► message dropped
      │
      ▼
Claude thinks, decides to call a tool
      │
      ▼
[PreToolUse hook] ──block?──► tool call cancelled
      │
      ▼
Tool executes
      │
      ▼
[PostToolUse hook]  (cannot block)
      │
      ▼
Claude finishes responding
      │
      ▼
[Stop hook]  (cannot block)
```

Hooks are **not** Claude — they are plain shell commands run by the Claude Code process. Claude cannot override or bypass them.

---

## Configuration Structure

Hooks live in `.claude/settings.json` (project-level) or `~/.claude/settings.json` (global):

```json
{
  "hooks": {
    "<EventName>": [
      {
        "matcher": "<regex or empty string>",
        "hooks": [
          {
            "type": "command",
            "command": "<shell command>"
          }
        ]
      }
    ]
  }
}
```

- **`matcher`** — regex applied to the tool name (for tool events). Leave `""` to match everything.
- **`type`** — currently only `"command"` is supported.
- **`command`** — any shell command; receives event data via stdin as JSON.
- Multiple matchers and multiple hooks per matcher are supported.

---

## Hook Events

| Event | Fires When | Can Block? |
|---|---|---|
| `UserPromptSubmit` | User submits a message, before LLM sees it | Yes |
| `PreToolUse` | Before Claude executes any tool | Yes |
| `PostToolUse` | After a tool finishes | No |
| `Stop` | Claude finishes its response | No |
| `Notification` | Claude sends a notification | No |

---

## Data Passed to Hooks

Every hook receives a **JSON object via stdin**. Parse it in your script to act on the data.

### UserPromptSubmit

```json
{
  "message": "Please process this file with SSN 123-45-6789"
}
```

### PreToolUse

```json
{
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf /tmp/old"
  }
}
```

### PostToolUse

```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/src/app.py",
    "content": "..."
  },
  "tool_result": "File written successfully"
}
```

### Stop

```json
{
  "session_id": "abc123",
  "num_turns": 5
}
```

### Notification

```json
{
  "message": "Claude is waiting for your input"
}
```

---

## Hook Return Values

| Exit Code | Meaning |
|---|---|
| `0` | Allow / success — proceed normally |
| Non-zero | Block the action (only works for `UserPromptSubmit` and `PreToolUse`) |

Anything written to **stdout** is shown to Claude as feedback (for blocking hooks, this becomes the rejection reason). Anything written to **stderr** is shown to the user in the terminal.

---

## Matcher Patterns

The `matcher` field is a **regex** matched against the tool name.

```json
"matcher": "Bash"              // exact tool name
"matcher": "Write|Edit"        // either Write or Edit
"matcher": "^mcp__"            // all MCP tools (by prefix convention)
"matcher": ".*"                // everything (same as "")
"matcher": ""                  // everything (empty = match all)
"matcher": "Bash|Write|Edit"   // common file/shell tools
```

MCP tools are named `mcp__<server>__<tool>`, so `"matcher": "mcp__myserver__.*"` targets all tools from a specific server.

---

## Event Examples: UserPromptSubmit

### 1. Block messages containing PII (SSN, email, phone)

**`.claude/settings.json`**
```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python hooks/pii_filter.py" }
        ]
      }
    ]
  }
}
```

**`hooks/pii_filter.py`**
```python
import sys
import json
import re

data = json.load(sys.stdin)
message = data.get("message", "")

patterns = {
    "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
    "Email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    "Phone": r"\b(\+1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b",
    "Credit Card": r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b",
}

for name, pattern in patterns.items():
    if re.search(pattern, message):
        print(f"Blocked: message contains {name}. Remove PII before sending.")
        sys.exit(1)

sys.exit(0)
```

---

### 2. Profanity / toxic content filter

**`hooks/profanity_filter.py`**
```python
import sys
import json

BLOCKED_WORDS = ["badword1", "badword2"]  # populate with your list

data = json.load(sys.stdin)
message = data.get("message", "").lower()

for word in BLOCKED_WORDS:
    if word in message:
        print(f"Blocked: message contains disallowed content.")
        sys.exit(1)

sys.exit(0)
```

---

### 3. Block messages that are too long

**`hooks/length_limit.sh`**
```bash
#!/bin/bash
input=$(cat)
length=$(echo "$input" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('message','')))")

if [ "$length" -gt 5000 ]; then
  echo "Blocked: message exceeds 5000 character limit (got $length characters)."
  exit 1
fi
exit 0
```

---

### 4. Log all user inputs to a file

**`hooks/log_input.py`**
```python
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
message = data.get("message", "")

with open("logs/user_inputs.log", "a") as f:
    f.write(f"[{datetime.now().isoformat()}] {message}\n")

sys.exit(0)  # always allow
```

---

### 5. Block keyword-based topics (e.g. competitor mentions)

**`hooks/topic_guard.py`**
```python
import sys
import json

BLOCKED_TOPICS = ["competitor_name", "confidential_project_x"]

data = json.load(sys.stdin)
message = data.get("message", "").lower()

for topic in BLOCKED_TOPICS:
    if topic in message:
        print(f"Blocked: discussions about '{topic}' are not allowed in this context.")
        sys.exit(1)

sys.exit(0)
```

---

## Event Examples: PreToolUse

### 6. Block dangerous Bash commands

**`.claude/settings.json`**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python hooks/bash_guard.py" }
        ]
      }
    ]
  }
}
```

**`hooks/bash_guard.py`**
```python
import sys
import json
import re

DANGEROUS_PATTERNS = [
    r"rm\s+-rf\s+/",           # rm -rf /
    r"dd\s+if=",               # dd overwrite
    r"mkfs\.",                 # format filesystem
    r">\s*/dev/sd",            # overwrite disk device
    r"chmod\s+-R\s+777\s+/",  # chmod 777 root
    r"curl\s+.*\|\s*bash",    # curl pipe to bash
    r"wget\s+.*\|\s*bash",    # wget pipe to bash
    r":\(\)\{.*\}.*:",        # fork bomb
]

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

for pattern in DANGEROUS_PATTERNS:
    if re.search(pattern, command):
        print(f"Blocked: command matches dangerous pattern '{pattern}'. Review before running manually.")
        sys.exit(1)

sys.exit(0)
```

---

### 7. Block writes to protected directories

**`hooks/protect_dirs.py`**
```python
import sys
import json

PROTECTED = ["/etc", "/usr", "/bin", "/sbin", "C:\\Windows", "C:\\System32"]

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
file_path = data.get("tool_input", {}).get("file_path", "")

if tool in ("Write", "Edit") and file_path:
    for protected in PROTECTED:
        if file_path.startswith(protected):
            print(f"Blocked: writes to {protected} are not permitted.")
            sys.exit(1)

sys.exit(0)
```

**Config (matches Write and Edit):**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python hooks/protect_dirs.py" }
        ]
      }
    ]
  }
}
```

---

### 8. Require confirmation before deleting files

**`hooks/confirm_delete.py`**
```python
import sys
import json

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

if "rm " in command or "Remove-Item" in command:
    answer = input(f"Claude wants to run: {command}\nAllow deletion? (yes/no): ")
    if answer.strip().lower() != "yes":
        print("Blocked: user denied the delete operation.")
        sys.exit(1)

sys.exit(0)
```

---

### 9. Log all tool calls with timestamps

**`hooks/log_tools.py`**
```python
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
tool = data.get("tool_name")
inp = json.dumps(data.get("tool_input", {}))

with open("logs/tool_calls.log", "a") as f:
    f.write(f"[{datetime.now().isoformat()}] PRE  {tool}: {inp[:200]}\n")

sys.exit(0)
```

**Config (matches all tools):**
```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "",
        "hooks": [
          { "type": "command", "command": "python hooks/log_tools.py" }
        ]
      }
    ]
  }
}
```

---

### 10. Rate-limit tool calls (max N per minute)

**`hooks/rate_limit.py`**
```python
import sys
import json
import time
import os

LIMIT = 30  # max tool calls per minute
STATE_FILE = "/tmp/claude_rate.json"

now = time.time()
state = {"calls": []}

if os.path.exists(STATE_FILE):
    with open(STATE_FILE) as f:
        state = json.load(f)

# keep only calls within the last 60 seconds
state["calls"] = [t for t in state["calls"] if now - t < 60]

if len(state["calls"]) >= LIMIT:
    print(f"Blocked: rate limit of {LIMIT} tool calls/minute exceeded.")
    sys.exit(1)

state["calls"].append(now)
with open(STATE_FILE, "w") as f:
    json.dump(state, f)

sys.exit(0)
```

---

### 11. Block MCP tool calls outside business hours

**`hooks/business_hours.py`**
```python
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
tool = data.get("tool_name", "")

if tool.startswith("mcp__"):
    now = datetime.now()
    if now.weekday() >= 5 or now.hour < 9 or now.hour >= 18:
        print("Blocked: MCP tools are only available Mon–Fri 9am–6pm.")
        sys.exit(1)

sys.exit(0)
```

---

### 12. Block network tool calls in sensitive projects

**`hooks/no_network.py`**
```python
import sys
import json

NETWORK_TOOLS = ["WebFetch", "WebSearch", "mcp__browser__navigate"]

data = json.load(sys.stdin)
tool = data.get("tool_name", "")

if tool in NETWORK_TOOLS:
    print(f"Blocked: network access via {tool} is disabled for this project.")
    sys.exit(1)

sys.exit(0)
```

---

### 13. Audit file access (read operations)

**`hooks/audit_reads.py`**
```python
import sys
import json
from datetime import datetime
import os

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
file_path = data.get("tool_input", {}).get("file_path", "")

SENSITIVE = [".env", "secrets", "credentials", "id_rsa", "private_key"]

if tool == "Read" and any(s in file_path for s in SENSITIVE):
    with open("logs/sensitive_access.log", "a") as f:
        f.write(f"[{datetime.now().isoformat()}] SENSITIVE READ: {file_path}\n")
    # log but allow — remove sys.exit(0) and add sys.exit(1) to block

sys.exit(0)
```

---

## Event Examples: PostToolUse

### 14. Auto-run linter after file edits

**`.claude/settings.json`**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python hooks/auto_lint.py" }
        ]
      }
    ]
  }
}
```

**`hooks/auto_lint.py`**
```python
import sys
import json
import subprocess

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")

if file_path.endswith(".py"):
    subprocess.run(["python", "-m", "flake8", file_path], check=False)
elif file_path.endswith((".js", ".ts")):
    subprocess.run(["npx", "eslint", "--fix", file_path], check=False)
elif file_path.endswith(".go"):
    subprocess.run(["gofmt", "-w", file_path], check=False)

sys.exit(0)
```

---

### 15. Auto-run tests after code changes

**`hooks/auto_test.py`**
```python
import sys
import json
import subprocess

data = json.load(sys.stdin)
file_path = data.get("tool_input", {}).get("file_path", "")

TEST_DIRS = {"src/": "pytest tests/", "lib/": "npm test", "pkg/": "go test ./..."}

for prefix, cmd in TEST_DIRS.items():
    if file_path.startswith(prefix):
        print(f"Running tests: {cmd}", file=sys.stderr)
        subprocess.run(cmd.split(), check=False)
        break

sys.exit(0)
```

---

### 16. Backup files before they are overwritten

**`hooks/backup_on_write.py`**
```python
import sys
import json
import shutil
import os
from datetime import datetime

data = json.load(sys.stdin)
tool = data.get("tool_name")
file_path = data.get("tool_input", {}).get("file_path", "")

# PostToolUse fires after — back up the new version for history
if tool in ("Write", "Edit") and file_path and os.path.exists(file_path):
    backup_dir = ".claude/backups"
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = os.path.basename(file_path)
    shutil.copy2(file_path, f"{backup_dir}/{name}.{ts}.bak")

sys.exit(0)
```

---

### 17. Log tool results for debugging

**`hooks/log_results.py`**
```python
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
tool = data.get("tool_name")
result = str(data.get("tool_result", ""))[:500]  # truncate large results

with open("logs/tool_results.log", "a") as f:
    f.write(f"[{datetime.now().isoformat()}] POST {tool}: {result}\n")

sys.exit(0)
```

---

### 18. Send Slack notification after a deployment command

**`hooks/notify_slack.py`**
```python
import sys
import json
import urllib.request

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

data = json.load(sys.stdin)
command = data.get("tool_input", {}).get("command", "")

DEPLOY_KEYWORDS = ["kubectl apply", "terraform apply", "helm upgrade", "npm run deploy"]

if any(kw in command for kw in DEPLOY_KEYWORDS):
    payload = json.dumps({"text": f"Claude ran a deployment command: `{command}`"}).encode()
    req = urllib.request.Request(SLACK_WEBHOOK, data=payload, headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)

sys.exit(0)
```

---

### 19. Auto-commit after file changes

**`hooks/auto_commit.sh`**
```bash
#!/bin/bash
input=$(cat)
file_path=$(echo "$input" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tool_input',{}).get('file_path',''))")

if [ -n "$file_path" ] && [ -f "$file_path" ]; then
  git add "$file_path"
  git commit -m "auto: Claude updated $file_path" --no-verify 2>/dev/null || true
fi
exit 0
```

---

### 20. Track which files Claude has touched

**`hooks/track_touched.py`**
```python
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
tool = data.get("tool_name", "")
file_path = data.get("tool_input", {}).get("file_path", "")

if tool in ("Write", "Edit", "Read") and file_path:
    with open(".claude/touched_files.log", "a") as f:
        f.write(f"{datetime.now().isoformat()}\t{tool}\t{file_path}\n")

sys.exit(0)
```

---

## Event Examples: Stop

### 21. Desktop notification when Claude finishes (macOS)

**`.claude/settings.json`**
```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "osascript -e 'display notification \"Claude has finished\" with title \"Claude Code\"'" }
        ]
      }
    ]
  }
}
```

### 22. Desktop notification (Windows)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "powershell -Command \"[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms'); [System.Windows.Forms.MessageBox]::Show('Claude has finished', 'Claude Code')\""
          }
        ]
      }
    ]
  }
}
```

### 23. Desktop notification (Linux)

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "notify-send 'Claude Code' 'Claude has finished responding'" }
        ]
      }
    ]
  }
}
```

---

### 24. Play a sound when Claude finishes

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "afplay /System/Library/Sounds/Glass.aiff" }
        ]
      }
    ]
  }
}
```

*(Replace `afplay` with `paplay` on Linux or `powershell -c (New-Object Media.SoundPlayer 'C:\\sound.wav').PlaySync()` on Windows)*

---

### 25. Log session summary

**`hooks/session_summary.py`**
```python
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
session_id = data.get("session_id", "unknown")
turns = data.get("num_turns", 0)

with open("logs/sessions.log", "a") as f:
    f.write(f"[{datetime.now().isoformat()}] session={session_id} turns={turns}\n")

sys.exit(0)
```

---

### 26. Send email summary when Claude finishes a long session

**`hooks/email_on_long_session.py`**
```python
import sys
import json
import smtplib
from email.mime.text import MIMEText

data = json.load(sys.stdin)
turns = data.get("num_turns", 0)

if turns > 20:
    msg = MIMEText(f"Claude completed a session with {turns} turns.")
    msg["Subject"] = "Claude Code Session Complete"
    msg["From"] = "claude@yourcompany.com"
    msg["To"] = "you@yourcompany.com"

    with smtplib.SMTP("localhost") as smtp:
        smtp.send_message(msg)

sys.exit(0)
```

---

### 27. Run a test suite after every Claude session

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "npm test -- --passWithNoTests 2>&1 | tail -5 >&2" }
        ]
      }
    ]
  }
}
```

---

## Event Examples: Notification

### 28. Log all notifications

**`hooks/log_notifications.py`**
```python
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
message = data.get("message", "")

with open("logs/notifications.log", "a") as f:
    f.write(f"[{datetime.now().isoformat()}] NOTIFY: {message}\n")

sys.exit(0)
```

---

### 29. Escalate notifications to Slack

**`hooks/notify_slack_on_alert.py`**
```python
import sys
import json
import urllib.request

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

data = json.load(sys.stdin)
message = data.get("message", "")

payload = json.dumps({"text": f":bell: Claude Code notification: {message}"}).encode()
req = urllib.request.Request(SLACK_WEBHOOK, data=payload, headers={"Content-Type": "application/json"})
urllib.request.urlopen(req)

sys.exit(0)
```

---

### 30. Flash terminal bell on notification

```json
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          { "type": "command", "command": "printf '\\a'" }
        ]
      }
    ]
  }
}
```

---

## Multi-Hook Chains

You can attach multiple hooks to the same event. They run **in order**. If any blocking hook exits non-zero, the chain stops.

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          { "type": "command", "command": "python hooks/pii_filter.py" },
          { "type": "command", "command": "python hooks/profanity_filter.py" },
          { "type": "command", "command": "python hooks/log_input.py" }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          { "type": "command", "command": "python hooks/bash_guard.py" },
          { "type": "command", "command": "python hooks/rate_limit.py" },
          { "type": "command", "command": "python hooks/log_tools.py" }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python hooks/protect_dirs.py" },
          { "type": "command", "command": "python hooks/audit_reads.py" }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "python hooks/auto_lint.py" },
          { "type": "command", "command": "python hooks/backup_on_write.py" },
          { "type": "command", "command": "python hooks/track_touched.py" }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          { "type": "command", "command": "python hooks/session_summary.py" },
          { "type": "command", "command": "npm test -- --passWithNoTests 2>&1 | tail -5 >&2" }
        ]
      }
    ]
  }
}
```

---

## Hook Scripts in Different Languages

Hooks can be written in **any language** as long as the script is executable and reads JSON from stdin.

### Bash

```bash
#!/bin/bash
input=$(cat)
tool=$(echo "$input" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_name',''))")
echo "[HOOK] Tool called: $tool" >&2
exit 0
```

### Python

```python
#!/usr/bin/env python3
import sys, json
data = json.load(sys.stdin)
# ... process data ...
sys.exit(0)
```

### Node.js

```javascript
#!/usr/bin/env node
let raw = "";
process.stdin.on("data", chunk => raw += chunk);
process.stdin.on("end", () => {
  const data = JSON.parse(raw);
  // ... process data ...
  process.exit(0);
});
```

### PowerShell (Windows)

```powershell
$input_data = $input | ConvertFrom-Json
$tool = $input_data.tool_name
Write-Host "Tool called: $tool"
exit 0
```

---

## Limitations

| Limitation | Detail |
|---|---|
| Cannot intercept LLM calls | No hook fires between user message and model API call (except `UserPromptSubmit` which fires before the LLM sees it) |
| Cannot modify input | Hooks can only allow or block — they cannot rewrite the user message or tool input |
| Cannot modify tool output | `PostToolUse` hooks cannot change what Claude sees as the tool result |
| No async hooks | Hooks are synchronous — long-running hooks block the Claude Code process |
| Tool type only | Only `"type": "command"` is supported; no native plugin API |
| Matcher is tool-name only | The matcher regex applies to tool name, not to the content of tool arguments |

### Workarounds for input modification

If you need to transform input rather than just block it, options are:

1. **Wrap the `claude` CLI** in a shell script that preprocesses stdin before passing it.
2. **Run a local HTTP proxy** that intercepts and rewrites requests to the Anthropic API.
3. **Use `CLAUDE.md`** to instruct Claude to handle/redact certain content patterns itself.

---

## Quick Reference Card

```
Event              Fires                          Blocks?   Data available
─────────────────────────────────────────────────────────────────────────
UserPromptSubmit   User submits message           YES       message
PreToolUse         Before tool executes           YES       tool_name, tool_input
PostToolUse        After tool executes            NO        tool_name, tool_input, tool_result
Stop               Claude finishes responding     NO        session_id, num_turns
Notification       Claude sends a notification    NO        message

Exit code 0   → allow / proceed
Exit code 1+  → block (UserPromptSubmit, PreToolUse only)
stdout        → shown to Claude as feedback
stderr        → shown to user in terminal
```
