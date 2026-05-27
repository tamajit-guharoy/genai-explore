#!/usr/bin/env python3
"""
Example 09: Using the built-in text_editor and bash tools.

Demonstrates how to use Anthropic's text_editor_20250728 and bash_20250124
tools in a multi-step agentic workflow:
  1. Create a Python file using the text editor tool
  2. Run the file using the bash tool
  3. View the file contents using the text editor tool
  4. Stream the response to show real-time progress

This is a self-contained example that uses the anthropic Python SDK.
"""

import json
import os
import sys
from typing import Any

from dotenv import load_dotenv

load_dotenv()

import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
MODEL = "claude-sonnet-4-20250514"  # or "claude-opus-4-20250514"
MAX_TOKENS = 4096

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def print_step(label: str, content: str = "") -> None:
    """Print a clearly visible step header."""
    print(f"\n{'=' * 70}")
    print(f"  {label}")
    print(f"{'=' * 70}")
    if content:
        print(content)


def run_agent_loop(system_prompt: str, user_message: str, tools: list[dict]) -> list[dict]:
    """
    Run a streaming agent loop that handles tool_use blocks automatically.

    Returns the full list of content blocks from the final response.
    """
    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    final_content: list[dict] | None = None

    while True:
        print_step("Sending request to Claude (streaming)...")
        with client.messages.stream(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=tools,
            messages=messages,
        ) as stream:
            # We accumulate the full response for inspection.
            response = stream.get_final_message()

        print_step("Response received", f"Stop reason: {response.stop_reason}")
        final_content = response.content

        # Check whether Claude wants to use a tool
        tool_blocks = [b for b in response.content if b.type == "tool_use"]
        if not tool_blocks:
            # No tools -- conversation is done
            break

        # Add assistant message with tool_use blocks
        messages.append({"role": "assistant", "content": response.content})

        for tool_block in tool_blocks:
            name = tool_block.name
            tool_input = tool_block.input  # already a dict
            tool_use_id = tool_block.id

            print_step(f"Tool called: {name}", json.dumps(tool_input, indent=2))

            # Execute the tool
            if name == "text_editor":
                result = execute_text_editor(tool_input)
            elif name == "bash":
                result = execute_bash(tool_input)
            else:
                result = {"error": f"Unknown tool: {name}"}

            print_step(f"Tool result for {name}", json.dumps(result, indent=2)[:2000])

            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": tool_use_id,
                            "content": json.dumps(result),
                        }
                    ],
                }
            )

    return final_content


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------
def execute_text_editor(input_data: dict) -> dict:
    """
    Simulate the text_editor_20250728 tool.
    Commands: create, view, edit, etc.
    """
    command = input_data.get("command", "")
    file_path = input_data.get("file_path", "")
    file_text = input_data.get("file_text", "")

    result: dict[str, Any] = {"success": True}

    if command == "create":
        try:
            os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_text)
            result["message"] = f"Created file: {file_path} ({len(file_text)} bytes)"
        except Exception as e:
            result = {"success": False, "error": str(e)}

    elif command == "view":
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            result["content"] = content
            result["message"] = f"Viewed file: {file_path} ({len(content)} bytes)"
        except FileNotFoundError:
            result = {"success": False, "error": f"File not found: {file_path}"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

    elif command == "edit":
        try:
            old = input_data.get("old_string", "")
            new = input_data.get("new_string", "")
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            if old in content:
                content = content.replace(old, new, 1)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                result["message"] = f"Edited file: {file_path}"
            else:
                result = {"success": False, "error": "old_string not found"}
        except Exception as e:
            result = {"success": False, "error": str(e)}

    else:
        result = {"success": False, "error": f"Unknown command: {command}"}

    return result


def execute_bash(input_data: dict) -> dict:
    """
    Execute a bash command locally and return the output.
    WARNING: This runs arbitrary commands -- use with caution.
    """
    import subprocess  # noqa: S404

    command = input_data.get("command", "")
    try:
        completed = subprocess.run(  # noqa: S603
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "exit_code": completed.returncode,
            "success": completed.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Command timed out (30s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ---------------------------------------------------------------------------
# Tool definitions (sent to Claude)
# ---------------------------------------------------------------------------
TEXT_EDITOR_TOOL: dict = {
    "name": "text_editor",
    "description": "Create, view, and edit text files using the Text Editor tool.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "enum": ["create", "view", "edit"],
                "description": "The action to perform.",
            },
            "file_path": {
                "type": "string",
                "description": "Absolute path to the file.",
            },
            "file_text": {
                "type": "string",
                "description": "Content for the create command.",
            },
            "old_string": {
                "type": "string",
                "description": "Text to replace (for edit command).",
            },
            "new_string": {
                "type": "string",
                "description": "Replacement text (for edit command).",
            },
            "insert_line": {
                "type": "integer",
                "description": "Line number to insert at (for edit command).",
            },
            "new_str": {
                "type": "string",
                "description": "Text to insert (for edit command, alternative).",
            },
        },
        "required": ["command", "file_path"],
    },
}

BASH_TOOL: dict = {
    "name": "bash",
    "description": "Run a bash command on the local system.",
    "input_schema": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The bash command to execute.",
            },
        },
        "required": ["command"],
    },
}


# ===================================================================
def main() -> None:
    """Run the text_editor + bash tool demonstration."""
    print_step(
        "ANTHROPIC CLAUDE SDK -- text_editor + bash tool demonstration",
        f"Model: {MODEL}",
    )

    system_prompt = (
        "You are a helpful assistant with access to a text editor and a bash shell. "
        "When asked to create a file, use the text_editor tool with command='create'. "
        "When asked to run code, use the bash tool. "
        "When asked to view a file, use the text_editor tool with command='view'."
    )

    user_message = (
        "Please do the following steps IN ORDER:\n"
        "1. Create a file called 'greeting.py' in the current directory with a Python function "
        "called `greet(name)` that prints 'Hello, {name}! Nice to meet you.'\n"
        "2. Run the file with: python greeting.py\n"
        "   (The file won't output anything on its own since greet() just defines a function -- "
        "   that is expected. Just report what happened.)\n"
        "3. View the file contents using the text_editor tool so I can see what was written.\n"
    )

    print_step("USER MESSAGE", user_message)
    print_step("Starting agent loop -- Claude will use tools as needed...")

    tools = [TEXT_EDITOR_TOOL, BASH_TOOL]
    final_content = run_agent_loop(system_prompt, user_message, tools)

    print_step("FINAL RESPONSE")
    if final_content:
        for block in final_content:
            if block.type == "text":
                print(block.text)
    else:
        print("(No response content)")


if __name__ == "__main__":
    main()
