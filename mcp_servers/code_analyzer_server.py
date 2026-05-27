#!/usr/bin/env python3
"""
MCP Code Analyzer Server — demonstrates AST parsing, code metrics,
static analysis, and resource templates for individual file analysis.

Install: pip install mcp radon
Configure in .claude/settings.json:
{
  "mcpServers": {
    "code-analyzer": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/code_analyzer_server.py"]
    }
  }
}
"""

import asyncio
import ast
import json
import os
import re
import tokenize
from collections import Counter
from io import StringIO
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("code-analyzer")

# ---------------------------------------------------------------------------
# AST visitor for complexity analysis
# ---------------------------------------------------------------------------

class ComplexityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.complexity: dict[str, int] = {}
        self.current_func: str | None = None
        self.funcs: list[dict] = []

    def visit_FunctionDef(self, node):
        name = node.name
        self.current_func = name
        self.complexity[name] = 1  # Base complexity
        self.generic_visit(node)
        self.funcs.append({
            "name": name,
            "line": node.lineno,
            "args": [a.arg for a in node.args.args],
            "complexity": self.complexity[name],
            "decorators": [
                d.id if isinstance(d, ast.Name) else ast.dump(d)[:50]
                for d in node.decorator_list
            ],
        })
        self.current_func = None

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def _inc_complexity(self):
        if self.current_func:
            self.complexity[self.current_func] += 1

    def visit_If(self, node): self._inc_complexity(); self.generic_visit(node)
    def visit_While(self, node): self._inc_complexity(); self.generic_visit(node)
    def visit_For(self, node): self._inc_complexity(); self.generic_visit(node)
    def visit_ExceptHandler(self, node): self._inc_complexity(); self.generic_visit(node)
    def visit_And(self, node): self._inc_complexity(); self.generic_visit(node)
    def visit_Or(self, node): self._inc_complexity(); self.generic_visit(node)
    def visit_Try(self, node): self._inc_complexity(); self.generic_visit(node)

class ImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports: list[str] = []
        self.from_imports: list[dict] = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.from_imports.append({
                "module": node.module or "",
                "name": alias.name,
                "alias": alias.asname,
            })
        self.generic_visit(node)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def analyze_python(source_code: str) -> list[TextContent]:
    """Analyze Python source code: functions, classes, complexity, imports, lines.

    Args:
        source_code: Python source code as a string
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Syntax error: {e}"}, indent=2))]

    # Complexity
    cv = ComplexityVisitor()
    cv.visit(tree)

    # Imports
    iv = ImportVisitor()
    iv.visit(tree)

    # Classes
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in ast.walk(node)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            bases = [ast.dump(b) if not isinstance(b, ast.Name) else b.id for b in node.bases]
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "bases": bases,
                "method_count": len(methods),
                "methods": methods,
            })

    # Lines of code
    lines = source_code.splitlines()
    code_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    comment_lines = [l for l in lines if l.strip().startswith("#")]
    blank_lines = [l for l in lines if not l.strip()]

    result = {
        "total_lines": len(lines),
        "code_lines": len(code_lines),
        "comment_lines": len(comment_lines),
        "blank_lines": len(blank_lines),
        "comment_ratio": round(len(comment_lines) / max(len(lines), 1) * 100, 1),
        "classes": classes,
        "functions": cv.funcs,
        "imports": {"modules": iv.imports, "from_imports": iv.from_imports},
        "total_imports": len(iv.imports) + len(iv.from_imports),
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def analyze_complexity(source_code: str) -> list[TextContent]:
    """Compute cyclomatic complexity for each function using radon.

    Args:
        source_code: Python source code
    """
    try:
        from radon.complexity import cc_visit
        from radon.raw import analyze
    except ImportError:
        # Fallback to AST-based complexity
        tree = ast.parse(source_code)
        cv = ComplexityVisitor()
        cv.visit(tree)
        results = [{
            "name": f["name"],
            "line": f["line"],
            "complexity": f["complexity"],
            "risk": "low" if f["complexity"] <= 5
                    else "moderate" if f["complexity"] <= 10
                    else "high" if f["complexity"] <= 20
                    else "very high",
        } for f in cv.funcs]
        return [TextContent(type="text", text=json.dumps({
            "functions": results,
            "method": "ast-fallback",
        }, indent=2))]

    blocks = cc_visit(source_code)
    results = []
    for block in blocks:
        results.append({
            "name": block.name,
            "line": block.lineno,
            "complexity": block.complexity,
            "type": block.type,
            "risk": "A (low)" if block.complexity <= 5
                    else "B (moderate)" if block.complexity <= 10
                    else "C (high)" if block.complexity <= 20
                    else "D (very high)" if block.complexity <= 30
                    else "E (extreme)" if block.complexity <= 50
                    else "F (refactor immediately)",
        })

    total = sum(r["complexity"] for r in results)
    avg = total / len(results) if results else 0

    return [TextContent(type="text", text=json.dumps({
        "functions": results,
        "summary": {
            "total_functions": len(results),
            "total_complexity": total,
            "average_complexity": round(avg, 1),
            "most_complex": max(results, key=lambda r: r["complexity"]) if results else None,
        },
    }, indent=2))]

@server.tool()
async def find_patterns(
    source_code: str,
    pattern_type: str = "all",
) -> list[TextContent]:
    """Find common code patterns and potential issues in Python code.

    Args:
        source_code: Python source code
        pattern_type: Type of patterns to find —
          "all", "security" (exec/eval), "todo", "exception" (bare except),
          "print" (debug prints), "deprecated"
    """
    lines = source_code.splitlines()
    patterns: dict[str, list] = {
        "security": [],
        "todo": [],
        "exception": [],
        "print": [],
        "deprecated": [],
    }

    security_patterns = [
        (r"\beval\s*\(", "eval() call — potential code injection"),
        (r"\bexec\s*\(", "exec() call — potential code injection"),
        (r"\bos\.system\s*\(", "os.system() — use subprocess instead"),
        (r"\b__import__\s*\(", "__import__() with dynamic name"),
        (r"\bpickle\.loads?\s*\(", "pickle.load(s) — unsafe deserialization"),
    ]

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        for regex, desc in security_patterns:
            if re.search(regex, stripped):
                patterns["security"].append({"line": i, "code": stripped[:120], "issue": desc})

        if re.search(r"TODO|FIXME|HACK|XXX|BUG", stripped, re.IGNORECASE):
            patterns["todo"].append({"line": i, "code": stripped[:120]})

        if re.search(r"except\s*:", stripped) and "except Exception" not in stripped:
            patterns["exception"].append({"line": i, "code": stripped[:120],
                "issue": "Bare except clause — catch specific exceptions"})

        if re.search(r"\bprint\s*\(", stripped):
            patterns["print"].append({"line": i, "code": stripped[:120]})

        # Deprecated patterns
        if re.search(r"\butilities\.iteritems\b", stripped):
            patterns["deprecated"].append({"line": i, "code": stripped[:120],
                "issue": "iteritems() is deprecated in Python 3"})

    if pattern_type != "all":
        result = {pattern_type: patterns.get(pattern_type, [])}
    else:
        result = patterns

    result["summary"] = {
        k: len(v) for k, v in patterns.items()
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def count_tokens(text: str, model: str = "claude") -> list[TextContent]:
    """Estimate token count for a given text.

    Args:
        text: The text to count tokens for
        model: "claude", "gpt4", "gpt3", or "simple"
    """
    # Approximate tokenizers
    if model == "simple":
        # Rough: ~4 chars per token for English
        count = len(text) // 4
    elif model == "claude":
        # Claude tokenizer approximation
        words = len(re.findall(r"\w+", text))
        non_words = len(re.findall(r"[^\w\s]", text))
        spaces = len(re.findall(r"\s+", text))
        count = words + non_words + spaces // 2
    else:
        # GPT-family approximation: ~4 chars per token
        count = len(text) // 4

    return [TextContent(type="text", text=json.dumps({
        "estimated_tokens": count,
        "characters": len(text),
        "words": len(text.split()),
        "model": model,
        "note": "This is an estimate. Actual token count depends on the specific tokenizer.",
    }, indent=2))]

@server.tool()
async def diff_stats(diff_text: str) -> list[TextContent]:
    """Analyze a unified diff or git diff for statistics.

    Args:
        diff_text: Unified diff text (e.g., output of `git diff`)
    """
    files_changed = 0
    additions = 0
    deletions = 0
    changed_files: list[dict] = []

    current_file = None
    for line in diff_text.splitlines():
        if line.startswith("diff --git") or line.startswith("--- a/") or line.startswith("+++ b/"):
            if line.startswith("+++ b/"):
                current_file = line[6:]
                files_changed += 1
                changed_files.append({"file": current_file, "additions": 0, "deletions": 0})
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
            if changed_files:
                changed_files[-1]["additions"] += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
            if changed_files:
                changed_files[-1]["deletions"] += 1

    return [TextContent(type="text", text=json.dumps({
        "files_changed": files_changed,
        "total_additions": additions,
        "total_deletions": deletions,
        "net_change": additions - deletions,
        "per_file": changed_files,
    }, indent=2))]

@server.tool()
async def generate_docstring(
    source_code: str,
    style: str = "google",
) -> list[TextContent]:
    """Generate docstring templates for undocumented Python functions.

    Args:
        source_code: Python source code
        style: Docstring style — "google", "numpy", or "sphinx"
    """
    try:
        tree = ast.parse(source_code)
    except SyntaxError as e:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Syntax error: {e}"}, indent=2))]

    suggestions = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check if function already has a docstring
            has_docstring = (
                ast.get_docstring(node) is not None
            )
            if has_docstring:
                continue

            args = [a.arg for a in node.args.args]
            returns = None
            # Simple heuristic: check if there's a return statement
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Return) and subnode.value is not None:
                    returns = "Any"
                    break

            if style == "google":
                ds = [f'    """[Brief description]']
                if args:
                    ds.append("")
                    ds.append("    Args:")
                    for arg in args:
                        if arg == "self":
                            continue
                        ds.append(f"        {arg}: [Description]")
                if returns:
                    ds.append("")
                    ds.append("    Returns:")
                    ds.append(f"        {returns}: [Description]")
                ds.append('    """')
            elif style == "numpy":
                ds = [f'    """[Brief description]']
                if args:
                    ds.append("")
                    ds.append("    Parameters")
                    ds.append("    ----------")
                    for arg in args:
                        if arg == "self":
                            continue
                        ds.append(f"    {arg} : type")
                        ds.append(f"        [Description]")
                if returns:
                    ds.append("")
                    ds.append("    Returns")
                    ds.append("    -------")
                    ds.append(f"    {returns}")
                    ds.append(f"        [Description]")
                ds.append('    """')
            else:  # sphinx
                ds = [f'    """[Brief description]']
                for arg in args:
                    if arg == "self":
                        continue
                    ds.append(f"    :param {arg}: [Description]")
                    ds.append(f"    :type {arg}: [type]")
                if returns:
                    ds.append(f"    :returns: [Description]")
                    ds.append(f"    :rtype: {returns}")
                ds.append('    """')

            suggestions.append({
                "function": node.name,
                "line": node.lineno,
                "docstring": "\n".join(ds),
            })

    return [TextContent(type="text", text=json.dumps(suggestions, indent=2))]

# ---------------------------------------------------------------------------
# Resource templates
# ---------------------------------------------------------------------------

@server.resource("analyzer://function/{function_name}")
async def get_function_info(function_name: str) -> str:
    """Dynamically resolved resource for a named function."""
    return json.dumps({
        "function": function_name,
        "note": "This is a dynamic resource. Use analyze_python to populate function details.",
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="code-review",
    description="Perform a thorough code review with static analysis",
    arguments={
        "focus": {
            "type": "string",
            "enum": ["all", "security", "performance", "complexity", "style"],
            "description": "What aspect of the code to focus on",
            "required": False,
        },
    },
)
async def code_review_prompt(focus: str = "all") -> dict:
    focus_instructions = {
        "all": "Check everything: security issues, complexity hotspots, code patterns, and missing docstrings.",
        "security": "Focus on security: look for eval/exec, os.system, pickle.loads, hardcoded secrets, and unsafe deserialization. Use find_patterns with pattern_type='security'.",
        "performance": "Focus on performance: check complexity with analyze_complexity, look for O(n²) patterns, excessive allocations, and blocking calls.",
        "complexity": "Focus on cyclomatic complexity: use analyze_complexity on every function. Flag anything above 10.",
        "style": "Focus on style: check for missing docstrings with generate_docstring, bare excepts, debug prints, and TODO/FIXME comments.",
    }
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""You are a senior code reviewer. Review the provided code.

FOCUS: {focus}
{focus_instructions.get(focus, focus_instructions['all'])}

Use the available tools (analyze_python, analyze_complexity, find_patterns, generate_docstring) to:
1. First, analyze the full structure with analyze_python
2. Check complexity with analyze_complexity
3. Find patterns/issues with find_patterns (matching the focus area)
4. Generate missing docstrings with generate_docstring

For each finding:
- Quote the exact line number
- Explain WHY it's a problem
- Show the corrected version
- Rate severity: 🔴 critical / 🟡 warning / 🔵 info

End with a summary: total findings by severity and an overall assessment.""",
            },
        }],
    }

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
