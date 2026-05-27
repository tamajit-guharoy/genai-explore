#!/usr/bin/env python3
"""
Example 11: Interleaved thinking with tool use.

Demonstrates how extended thinking blocks can be interleaved with tool-use
calls in a multi-step agent loop. This is useful for complex tasks that
require reasoning between tool invocations.

The scenario: Claude is tasked with analyzing a fictional project, reading
files, reasoning about dependencies, and writing a summary report -- all
while showing its internal reasoning between each step.

Uses claude-opus-4-7 with adaptive thinking, falling back to claude-sonnet-4-6.
"""

import json
import os
import sys
import time
from typing import Any

from dotenv import load_dotenv

load_dotenv()

import anthropic

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PREFERRED_MODEL = "claude-opus-4-20250514"
FALLBACK_MODEL = "claude-sonnet-4-6-20250515"
MAX_TOKENS = 8192

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def print_header(label: str) -> None:
    print(f"\n{'=' * 72}")
    print(f"  {label}")
    print(f"{'=' * 72}")


# ---------------------------------------------------------------------------
# Mock tool implementations (simulated file system)
# ---------------------------------------------------------------------------
_MOCK_FILES: dict[str, str] = {
    "project/main.py": (
        "import data_loader\nimport analyzer\nimport reporter\n\n"
        "def run_pipeline(source):\n"
        "    data = data_loader.load(source)\n"
        "    results = analyzer.process(data)\n"
        "    reporter.generate(results)\n"
        "    return results\n"
    ),
    "project/data_loader.py": (
        "import json\nimport csv\n\ndef load(source):\n"
        '    if source.endswith(".json"):\n'
        "        with open(source) as f:\n"
        "            return json.load(f)\n"
        '    elif source.endswith(".csv"):\n'
        "        with open(source) as f:\n"
        "            return list(csv.DictReader(f))\n"
        "    else:\n"
        '        raise ValueError(f"Unsupported format: {source}")\n'
    ),
    "project/analyzer.py": (
        "def process(data):\n"
        "    results = {'total': len(data)}\n"
        "    numeric_values = []\n"
        "    for item in data:\n"
        "        for key, val in item.items():\n"
        "            if isinstance(val, (int, float)):\n"
        "                numeric_values.append(val)\n"
        "    if numeric_values:\n"
        "        results['avg'] = sum(numeric_values) / len(numeric_values)\n"
        "        results['max'] = max(numeric_values)\n"
        "        results['min'] = min(numeric_values)\n"
        "    return results\n"
    ),
    "project/reporter.py": (
        "def generate(results):\n"
        "    print('Pipeline Results:')\n"
        "    for key, val in results.items():\n"
        "        print(f'  {key}: {val}')\n"
    ),
    "project/README.md": (
        "# Data Pipeline\n\n"
        "A simple data processing pipeline.\n\n"
        "## Files\n"
        "- main.py: Entry point\n"
        "- data_loader.py: Loads data from JSON/CSV\n"
        "- analyzer.py: Computes statistics\n"
        "- reporter.py: Prints results\n\n"
        "## Usage\n"
        "```python\nfrom main import run_pipeline\n"
        "result = run_pipeline('data.json')\n```\n"
    ),
}


def execute_tool(name: str, input_data: dict) -> dict:
    """Execute a mock tool and return its result."""
    if name == "read_file":
        path = input_data.get("path", "")
        if path in _MOCK_FILES:
            return {"success": True, "path": path, "content": _MOCK_FILES[path]}
        else:
            return {"success": False, "error": f"File not found: {path}"}

    elif name == "write_file":
        path = input_data.get("path", "")
        content = input_data.get("content", "")
        _MOCK_FILES[path] = content
        return {"success": True, "path": path, "size": len(content)}

    elif name == "execute_command":
        command = input_data.get("command", "")
        # Mock execution
        if "pylint" in command or "flake8" in command or "mypy" in command:
            return {
                "success": True,
                "stdout": "No issues found.",
                "stderr": "",
                "exit_code": 0,
            }
        elif "python" in command:
            return {
                "success": True,
                "stdout": "Pipeline executed successfully.",
                "stderr": "",
                "exit_code": 0,
            }
        else:
            return {
                "success": True,
                "stdout": f"Command '{command}' completed.",
                "stderr": "",
                "exit_code": 0,
            }

    return {"success": False, "error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Tool definitions
# ---------------------------------------------------------------------------
TOOLS: list[dict] = [
    {
        "name": "read_file",
        "description": "Read the contents of a file from the project directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the file (e.g. 'project/main.py').",
                }
            },
            "required": ["path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write content to a file in the project directory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to the file."},
                "content": {"type": "string", "description": "Content to write."},
            },
            "required": ["path", "content"],
        },
    },
    {
        "name": "execute_command",
        "description": "Run a command (simulated) to test the project.",
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Command to run."},
            },
            "required": ["command"],
        },
    },
]


# ===================================================================
def main() -> None:
    """Run the interleaved thinking demonstration."""
    print_header("INTERLEAVED THINKING WITH TOOL USE")
    print("Claude will reason between each tool call, showing its thinking.\n")

    # Determine which model to use
    model = PREFERRED_MODEL
    print(f"Attempting model: {model}")
    print(f"Fallback model:   {FALLBACK_MODEL}")
    print()

    system_prompt = (
        "You are a code reviewer analyzing a small data pipeline project. "
        "Use the available tools to read files, understand the code, and write "
        "a summary report. Think carefully between each step about what you've "
        "learned and what to do next."
    )

    user_message = (
        "Please analyze the project in the 'project/' directory:\n"
        "1. Read main.py, data_loader.py, analyzer.py, reporter.py, and README.md\n"
        "2. For each file, think about its purpose and quality\n"
        "3. Test the project by running 'python project/main.py'\n"
        "4. Write a summary to 'project/review_summary.md' with:\n"
        "   - Overview of the architecture\n"
        "   - Key observations about each module\n"
        "   - Suggestions for improvement\n"
    )

    print(f"System prompt: {system_prompt}\n")
    print(f"User message: {user_message}\n")

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_message}]
    step = 0

    # Retry with fallback model if first choice fails
    for attempt_model in [model, FALLBACK_MODEL]:
        if attempt_model != model:
            print(f"\nRetrying with fallback model: {attempt_model}")

        try:
            while True:
                step += 1
                print_header(f"STEP {step} -- Request to {attempt_model}")

                with client.messages.stream(
                    model=attempt_model,
                    max_tokens=MAX_TOKENS,
                    system=system_prompt,
                    tools=TOOLS,
                    thinking={"type": "enabled", "budget_tokens": 2000},
                    messages=messages,
                ) as stream:
                    response = stream.get_final_message()

                # Print thinking blocks as they appear
                thinking_blocks = [b for b in response.content if b.type == "thinking"]
                for i, tb in enumerate(thinking_blocks):
                    print_header(f"THINKING BLOCK {i + 1}")
                    print(tb.thinking[:600])
                    if len(tb.thinking) > 600:
                        print(f"... (truncated, {len(tb.thinking)} total chars)")

                # Print text content
                text_blocks = [b for b in response.content if b.type == "text"]
                for tb in text_blocks:
                    print_header("TEXT OUTPUT")
                    print(tb.text)

                # Check for tool use
                tool_blocks = [b for b in response.content if b.type == "tool_use"]
                if not tool_blocks:
                    print_header("DONE -- No more tool calls")
                    break

                # Add assistant response to history
                messages.append({"role": "assistant", "content": response.content})

                for tb in tool_blocks:
                    print_header(f"TOOL CALL: {tb.name}")
                    print(json.dumps(tb.input, indent=2))

                    result = execute_tool(tb.name, tb.input)
                    print_header(f"TOOL RESULT: {tb.name}")
                    print(json.dumps(result, indent=2)[:1000])

                    messages.append(
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tb.id,
                                    "content": json.dumps(result),
                                }
                            ],
                        }
                    )

            # Success -- exit the retry loop
            break

        except anthropic.NotFoundError as e:
            print(f"\nModel {attempt_model} not available: {e}")
            if attempt_model == FALLBACK_MODEL:
                print("Both models failed. Exiting.")
                return
            # Otherwise, retry with fallback
        except Exception as e:
            print(f"\nError with {attempt_model}: {type(e).__name__}: {e}")
            if attempt_model == FALLBACK_MODEL:
                print("Both models failed. Exiting.")
                return

    print_header("INTERLEAVED THINKING DEMONSTRATION COMPLETE")
    print("Key takeaway: Thinking blocks can appear before, between, or after")
    print("tool_use blocks, allowing Claude to reason through multi-step tasks.")


if __name__ == "__main__":
    main()
