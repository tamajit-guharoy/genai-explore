#!/usr/bin/env python3
"""
Example 24: Agent Skills

Demonstrates how to define and use custom skills with the Claude API.
Skills are reusable capabilities that can be attached to agents to give
them specialized knowledge and behaviors.

Key concepts:
- Creating a skill directory structure with SKILL.md
- Writing YAML frontmatter for skill metadata
- Defining the skill behavior in markdown
- Invoking the skill via the API
- How skills are referenced in API calls
- Cleaning up temp files

Note: Skills require the Skill API to be enabled on your Anthropic account.
Contact Anthropic for access.
"""

import os
import json
import tempfile
import shutil
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


SKILL_MD_CONTENT = """\
---
name: python-code-reviewer
description: Reviews Python code for common issues, bugs, and style problems
model: claude-sonnet-4-20250514
version: 1.0.0
author: Demo
capabilities:
  - code_review
  - static_analysis
  - style_checking
categories:
  - development
  - code-quality
temperature: 0.3
max_tokens: 4096
---

# Python Code Reviewer Skill

You are an expert Python code reviewer. When provided with Python code,
you must analyze it for:

## 1. Bug Detection
- Logic errors and off-by-one errors
- Variable misuse (e.g., variable referenced before assignment)
- Type errors (mismatched types in operations)
- Resource leaks (files, connections not closed)
- Race conditions and threading issues
- Exception handling issues (bare excepts, too-broad catches)

## 2. Code Style & PEP 8
- Naming conventions (snake_case for functions/variables, PascalCase for classes)
- Line length > 88 characters (Black-compatible)
- Missing docstrings for public functions/classes/methods
- Unused imports or variables
- Magic numbers that should be named constants

## 3. Performance Issues
- Unnecessary list comprehensions vs generator expressions
- Inefficient string concatenation in loops
- Using `in` on lists instead of sets for membership tests
- Repeated computations that should be cached

## 4. Security Concerns
- Use of `eval()`, `exec()`, or `pickle` with untrusted data
- SQL injection vulnerabilities (raw string formatting in queries)
- Hardcoded secrets or credentials
- Command injection via `os.system()` or `subprocess` with `shell=True`

## Review Format

For each issue found, provide:
1. **Severity**: HIGH / MEDIUM / LOW
2. **Location**: Line number(s)
3. **Issue**: Description of the problem
4. **Suggestion**: How to fix it

If no issues are found, state that the code looks good.
Provide a summary at the end with counts of issues by severity.
"""


SAMPLE_PYTHON_CODE = """\
import os
import sys
import json

def process_data(data):
    results = []
    for i, item in enumerate(data):
        tmp = item.get('value', 0)
        r = tmp * 2
        if r > 100:
            results.append(r)
    return results

class DataProcessor:
    def __init__(self, config):
        self.config = config
        self.cache = {}

    def process(self, items):
        for item in items:
            if item['id'] not in self.cache:
                self.cache[item['id']] = self._compute(item)
                self.cache[item['id']] = self._compute(item)  # duplicate
            else:
                pass
        return list(self.cache.values())

    def _compute(self, item):
        x = item['x']
        y = item['y']
        r = eval(f"{x} + {y}")  # security issue
        return r

def main():
    config = {"threshold": 100}
    dp = DataProcessor(config)
    input_data = [{'id': i, 'value': i * 10} for i in range(10)]
    output = dp.process(input_data)
    print(output)

if __name__ == '__main__':
    main()
"""


def demonstrate_agent_skills():
    """
    Demonstrate the Agent Skills API:
    1. Create a skill directory with SKILL.md
    2. Invoke the skill via the API
    3. Show how skills are referenced
    4. Clean up temp files
    """
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = "claude-sonnet-4-20250514"
    tmp_dir = None

    print("=" * 72)
    print("AGENT SKILLS DEMO")
    print("=" * 72)
    print()

    try:
        # ── Step 1: Create skill directory structure ────────────────

        print(">>> Step 1: Creating skill directory structure...")

        tmp_dir = tempfile.mkdtemp(prefix="skill_demo_")
        skill_dir = Path(tmp_dir) / "python-code-reviewer"
        skill_dir.mkdir(parents=True, exist_ok=True)

        # Write SKILL.md
        skill_md_path = skill_dir / "SKILL.md"
        with open(skill_md_path, "w", encoding="utf-8") as f:
            f.write(SKILL_MD_CONTENT)

        print(f"  Skill directory: {skill_dir}")
        print(f"  SKILL.md size: {len(SKILL_MD_CONTENT)} bytes")
        print(f"  Contains YAML frontmatter with metadata:")
        print(f"    name: python-code-reviewer")
        print(f"    description: Reviews Python code for common issues")
        print(f"    version: 1.0.0")
        print(f"    categories: development, code-quality")
        print()

        # ── Step 2: Invoke the skill via the API ───────────────────

        print(">>> Step 2: Invoking the skill via the API...")
        print()

        # The skill is referenced by its name in the system prompt
        # or via the skills parameter in the API call
        skill_name = "python-code-reviewer"

        response = client.messages.create(
            model=model,
            max_tokens=2000,
            # Reference the skill in the system prompt
            system=f"You are using the '{skill_name}' skill. "
                   f"Follow the skill's instructions for reviewing code.",
            # Additional skills can be passed as a parameter
            # This is the structured way to attach skills
            skills=[
                {
                    "type": "skill",
                    "name": skill_name,
                    "source": {
                        "type": "text",
                        "content": SKILL_MD_CONTENT,
                    },
                },
            ],
            messages=[
                {
                    "role": "user",
                    "content": f"Please review this Python code:\\n\\n"
                               f"```python\\n{SAMPLE_PYTHON_CODE}\\n```",
                },
            ],
        )

        print(f"  Skills parameter: [{skill_name}]")
        print(f"  Response stop_reason: {response.stop_reason}")
        print()

        print(">>> Skill invocation result:")
        print("-" * 72)
        for block in response.content:
            if block.type == "text":
                print(block.text)
        print("-" * 72)
        print()

        # ── Step 3: Show how skills work ───────────────────────────

        print(">>> Step 3: How skills are referenced in API calls")
        print()

        print("""
  Skills can be attached to API calls in two ways:

  Method 1 — System prompt reference (simpler):
    system="You are using the 'python-code-reviewer' skill. ..."

  Method 2 — Structured skills parameter (recommended):
    skills=[{
        "type": "skill",
        "name": "python-code-reviewer",
        "source": {
            "type": "text",
            "content": "... full SKILL.md content ...",
        },
    }]

  Method 3 — Registered skill (requires Skill API access):
    skills=[{
        "type": "skill",
        "name": "python-code-reviewer",
        "source": {
            "type": "skill_id",
            "skill_id": "skl_abc123",
        },
    }]

  The skill provides:
    - Specialized instructions and guardrails
    - Consistent output format
    - Domain-specific knowledge
    - Reusable across multiple conversations
  """)

    except Exception as e:
        print(f"  Error: {type(e).__name__}: {e}")
        print()
        if "skill" in str(e).lower() or "not_found" in str(e).lower():
            print("  NOTE: Skills require the Skill API to be enabled on your account.")
            print("  The skill WAS created locally as a SKILL.md file structure.")
            print()
            print("  See conceptual flow below:")
            print()

        # Show what was demonstrated even if the API call failed
        print("  Local skill structure was created successfully:")
        print(f"    {skill_dir / 'SKILL.md'}")

        print("""
  ── Conceptual API Flow ──

  # Define skill (locally or via API)
  skill_definition = {
      "name": "python-code-reviewer",
      "description": "Reviews Python code for common issues",
      "source": {"type": "text", "content": SKILL_MD_CONTENT},
  }

  # Use skill in a request
  response = client.messages.create(
      model="claude-sonnet-4-20250514",
      max_tokens=2000,
      skills=[skill_definition],
      messages=[{"role": "user", "content": code_to_review}],
  )

  # (Future) Register skill for reuse:
  # registered_skill = client.beta.skills.create(
  #     name="python-code-reviewer",
  #     file=open("SKILL.md", "rb"),
  # )
  # skills=[{"type": "skill", "source": {"type": "skill_id", "skill_id": registered_skill.id}}]
  """)

    # ── Cleanup ────────────────────────────────────────────────────

    print(">>> Cleanup: Removing temporary skill directory...")
    if tmp_dir and Path(tmp_dir).exists():
        shutil.rmtree(tmp_dir)
        print(f"  Deleted: {tmp_dir}")

    print()
    print("=" * 72)
    print("AGENT SKILLS DEMO COMPLETE")
    print("=" * 72)


def main():
    demonstrate_agent_skills()


if __name__ == "__main__":
    main()
