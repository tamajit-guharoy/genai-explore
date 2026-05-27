#!/usr/bin/env python3
"""
Example 25: Full Agentic Loop

A comprehensive end-to-end agent example combining multiple features:
- Custom tool definitions (list_files, read_file, search_code)
- Interleaved thinking (extended thinking)
- Built-in web_search tool
- Full agent loop handling: thinking blocks, tool_use blocks,
  tool_result blocks, server_tool_use blocks, text responses
- Multi-step task execution with trace logging

Task: "Investigate why the login endpoint is slow"

The agent will:
  1. Think about what to investigate
  2. Search the codebase for login-related code
  3. Read relevant files
  4. Potentially search the web for best practices
  5. Provide a final analysis

This uses mock implementations for file operations and web search
so it runs without external dependencies.
"""

import os
import json
import time
import sys
from typing import Any
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

# ── Mock file system ───────────────────────────────────────────────────────

MOCK_FILESYSTEM = {
    "src/auth/login.py": """\
import time
import hashlib
import jwt
from flask import request, jsonify
from database import db

def login():
    start = time.time()
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # BAD: N+1 query pattern
    user = db.query(f"SELECT * FROM users WHERE username = '{username}'")

    # BAD: Synchronous bcrypt with high cost factor
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), user.salt, 1000000)

    # BAD: Nested synchronous API call
    audit_response = requests.post(
        "https://audit.internal/events",
        json={"user": username, "event": "login"},
        timeout=5
    )

    token = jwt.encode({"user_id": user.id}, "secret-key", algorithm="HS256")
    elapsed = time.time() - start
    print(f"Login took {elapsed:.2f}s")
    return jsonify({"token": token, "elapsed": elapsed})
""",
    "src/auth/middleware.py": """\
import time
from functools import wraps
from flask import request, jsonify

def rate_limiter(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = f(*args, **kwargs)
        elapsed = time.time() - start
        if elapsed > 1.0:
            print(f"WARNING: {request.path} took {elapsed:.2f}s")
        return result
    return wrapper

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper
""",
    "src/auth/config.py": """\
# Login configuration
LOGIN_SETTINGS = {
    "bcrypt_rounds": 12,
    "session_timeout": 3600,
    "max_login_attempts": 5,
    "audit_logging": True,
    "audit_endpoint": "https://audit.internal/events",
    "rate_limit": "100/hour",
}
""",
    "src/database.py": """\
import time

class db:
    @staticmethod
    def query(sql):
        time.sleep(0.5)  # Simulate slow query
        return type('User', (), {
            'id': 1,
            'username': 'admin',
            'salt': b'fixed_salt',
            'email': 'admin@example.com'
        })()

    @staticmethod
    def find_all(sql):
        time.sleep(0.3)
        return []
""",
}


def mock_list_files(path: str = "/src") -> list[dict]:
    """Mock implementation of list_files."""
    all_files = list(MOCK_FILESYSTEM.keys())
    if path == "/":
        path = ""
    results = [
        {"path": p, "size": len(MOCK_FILESYSTEM[p]), "type": "file"}
        for p in all_files
        if p.startswith(path.lstrip("/"))
    ]
    return results


def mock_read_file(path: str) -> str:
    """Mock implementation of read_file."""
    key = path.lstrip("/")
    if key in MOCK_FILESYSTEM:
        return MOCK_FILESYSTEM[key]
    return f"Error: File not found: {path}"


def mock_search_code(pattern: str, path: str = "/src") -> list[dict]:
    """Mock implementation of search_code."""
    results = []
    for filepath, content in MOCK_FILESYSTEM.items():
        if path != "/" and not filepath.startswith(path.lstrip("/")):
            continue
        for i, line in enumerate(content.split("\\n"), 1):
            if pattern.lower() in line.lower():
                results.append({
                    "file": filepath,
                    "line": i,
                    "content": line.strip(),
                })
    return results


# ── Mock web search ────────────────────────────────────────────────────────

MOCK_WEB_RESULTS = {
    "flask login": [
        {
            "title": "Flask Login Performance Best Practices",
            "url": "https://example.com/flask-login-perf",
            "snippet": "Use connection pooling, async bcrypt, and query optimization.",
        },
    ],
    "flask slow login endpoint": [
        {
            "title": "Debugging Slow Flask Endpoints",
            "url": "https://example.com/debug-slow-flask",
            "snippet": "Common causes: N+1 queries, sync crypto, missing indexes.",
        },
    ],
}


def mock_web_search(query: str) -> list[dict]:
    """Mock implementation of web_search."""
    results = []
    for key, value in MOCK_WEB_RESULTS.items():
        if key.lower() in query.lower() or query.lower() in key.lower():
            results.extend(value)
    if not results:
        results = [{"title": "(no mock results)", "url": "", "snippet": ""}]
    return results


# ── Tool definitions ───────────────────────────────────────────────────────

CUSTOM_TOOLS = [
    {
        "name": "list_files",
        "description": "List files in a directory within the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Directory path, e.g. '/src/auth'",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "read_file",
        "description": "Read the contents of a file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path, e.g. '/src/auth/login.py'",
                },
            },
            "required": ["path"],
        },
    },
    {
        "name": "search_code",
        "description": "Search for a pattern in the codebase.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Search pattern"},
                "path": {"type": "string", "description": "Directory scope"},
            },
            "required": ["pattern"],
        },
    },
]

BUILT_IN_TOOLS = [
    {
        "type": "web_search",
        "name": "web_search",
        "description": "Search the web for information.",
    },
]

ALL_TOOLS = CUSTOM_TOOLS + BUILT_IN_TOOLS


# ── Tool executor ──────────────────────────────────────────────────────────

TOOL_IMPLEMENTATIONS = {
    "list_files": lambda **kw: json.dumps(mock_list_files(**kw)),
    "read_file": lambda **kw: mock_read_file(**kw),
    "search_code": lambda **kw: json.dumps(mock_search_code(**kw)),
    "web_search": lambda **kw: json.dumps(mock_web_search(**kw)),
}


def execute_tool(name: str, tool_input: dict) -> str:
    """Execute a tool and return the result as a string."""
    impl = TOOL_IMPLEMENTATIONS.get(name)
    if not impl:
        return json.dumps({"error": f"Unknown tool: {name}"})
    try:
        return impl(**tool_input)
    except Exception as e:
        return json.dumps({"error": str(e)})


# ── Main agentic loop ──────────────────────────────────────────────────────

def run_agentic_loop():
    """Run the full agentic loop for the login investigation task."""
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = "claude-sonnet-4-20250514"

    print("=" * 72)
    print("FULL AGENTIC LOOP")
    print("=" * 72)
    print()
    print(f"  Model: {model}")
    print(f"  Tools: {[t['name'] for t in ALL_TOOLS]}")
    print()
    print("  Task: Investigate why the login endpoint is slow")
    print()

    # ── System prompt ────────────────────────────────────────────────

    system_prompt = """\
You are a senior software engineer investigating a performance issue.
You have access to a codebase and the web. Follow these steps:

1. FIRST think about what could cause slowness in a login endpoint.
2. Search the codebase for relevant files and code.
3. Read suspicious files to understand the implementation.
4. Use web search to validate your findings against best practices.
5. Provide a final analysis with specific recommendations.

Be thorough. The codebase is in /src.
"""

    messages = [
        {
            "role": "user",
            "content": (
                "Our login endpoint at POST /api/auth/login is slow — it takes "
                "over 3 seconds. Investigate the codebase and figure out why. "
                "Look at /src/auth/login.py and related files. Search the web "
                "for best practices too.\n\n"
                "Provide a detailed report with:\n"
                "- Root causes found\n"
                "- Specific line numbers and code snippets\n"
                "- Performance impact of each issue\n"
                - Concrete fixes with code examples"
            ),
        },
    ]

    # ── Agent loop ───────────────────────────────────────────────────

    max_iterations = 15
    action_log = []

    for iteration in range(1, max_iterations + 1):
        print(f"{'=' * 72}")
        print(f"  ITERATION {iteration}")
        print(f"{'=' * 72}")
        print()

        response = client.messages.create(
            model=model,
            max_tokens=4096,
            system=system_prompt,
            tools=ALL_TOOLS,
            messages=messages,
            # Enable extended thinking
            thinking={"type": "enabled", "budget_tokens": 2048},
        )

        # Process response blocks
        has_tool_calls = False
        assistant_content = []

        for block in response.content:
            if block.type == "text":
                print(f"  [TEXT]")
                print(f"  {block.text[:500]}")
                print()
                assistant_content.append({"type": "text", "text": block.text})
                action_log.append(("text", block.text[:100] + "..."))

            elif block.type == "thinking":
                print(f"  [THINKING] ({len(block.thinking)} chars)")
                print(f"  {block.thinking[:400]}...")
                print()
                assistant_content.append({"type": "thinking", "thinking": block.thinking})
                action_log.append(("thinking", f"{len(block.thinking)} chars"))

            elif block.type == "tool_use":
                has_tool_calls = True
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                print(f"  [TOOL_USE] {tool_name}")
                print(f"    id:    {tool_id}")
                print(f"    input: {json.dumps(tool_input, indent=6)}")

                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_id,
                    "name": tool_name,
                    "input": tool_input,
                })

                # Execute the tool
                print(f"    → executing...")
                result = execute_tool(tool_name, tool_input)
                print(f"    → result ({len(result)} chars): {result[:200]}...")
                print()

                action_log.append(("tool_use", f"{tool_name}({json.dumps(tool_input)})"))

                # Append tool result
                messages.append({
                    "role": "assistant",
                    "content": assistant_content,
                })
                messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_id,
                            "content": result,
                        },
                    ],
                })

                # Reset for next iteration
                assistant_content = []

            elif block.type == "tool_use_block":
                # For built-in tools that return results inline
                has_tool_calls = True
                print(f"  [SERVER_TOOL_USE] {block.name}")
                tool_name = block.name

                action_log.append(("server_tool_use", f"{tool_name}"))

                assistant_content.append({
                    "type": "tool_use",
                    "id": getattr(block, "id", "builtin"),
                    "name": tool_name,
                    "input": getattr(block, "input", {}),
                })

        # If no tool calls were made, this is the final answer
        if assistant_content and not has_tool_calls:
            messages.append({
                "role": "assistant",
                "content": assistant_content,
            })
            print(f"  >>> No more tool calls — agent is done.")
            print()
            break

        if iteration >= max_iterations:
            print(f"  >>> Reached max iterations ({max_iterations}). Stopping.")
            print()

    # ── Summary ──────────────────────────────────────────────────────

    print()
    print("=" * 72)
    print("AGENTIC LOOP SUMMARY")
    print("=" * 72)
    print()
    print(f"Iterations: {iteration}")
    print(f"Actions taken:")
    print()

    for i, (action_type, detail) in enumerate(action_log, 1):
        icon = {
            "text": "[TEXT]",
            "thinking": "[THINK]",
            "tool_use": "[TOOL]",
            "server_tool_use": "[WEB]",
        }.get(action_type, f"[{action_type.upper()}]")
        print(f"  {i:2d}. {icon} {detail[:120]}")

    print()

    # Extract the final answer
    print("=" * 72)
    print("FINAL ANSWER")
    print("=" * 72)
    print()

    for msg in reversed(messages):
        if msg["role"] == "assistant":
            content = msg.get("content", "")
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        print(block["text"])
            elif isinstance(content, str):
                print(content)
            break

    print()
    print("=" * 72)
    print("AGENTIC LOOP COMPLETE")
    print("=" * 72)
    print()
    print("Key features demonstrated:")
    print("  - Custom tool definitions and execution")
    print("  - Extended thinking (thinking blocks)")
    print("  - Built-in web_search tool")
    print("  - Full tool_use + tool_result round-trip")
    print("  - Multi-step reasoning with state tracking")
    print("  - Mock implementations for zero-dependency running")


def main():
    try:
        run_agentic_loop()
    except Exception as e:
        print(f"Error during agentic loop: {type(e).__name__}: {e}")
        print()
        print("TIP: If this is a rate limit or authentication error,")
        print("check your ANTHROPIC_API_KEY environment variable.")
        print()

        # Fallback: Show what the code does conceptually
        print("=" * 72)
        print("FALLBACK: Conceptual flow")
        print("=" * 72)
        print("""
  The agentic loop works as follows:

  1. User provides a task
  2. Claude thinks about the problem (thinking block)
  3. Claude decides which tool(s) to call
  4. We execute the tool and return the result
  5. Claude thinks again and plans next steps
  6. Repeat until Claude provides a final answer

  Tools used in this demo:
    - list_files   → explore the codebase structure
    - read_file    → read specific files
    - search_code  → find patterns across files
    - web_search   → find best practices online

  The loop tracks every action and prints a summary at the end.
  """)


if __name__ == "__main__":
    main()
