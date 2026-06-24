"""
02_file_editor_demo.py -- FileEditorTool programmatic usage
Based on Section 5.2 of openhands-tutorial.md

Shows how to use FileEditorTool directly (agents use it via actions,
but you can call it programmatically for testing or custom workflows).
"""

from pathlib import Path
import tempfile
from openhands.tools.file_editor import FileEditorTool
from openhands.tools.file_editor.actions import (
    FileWriteAction, FileReadAction, FileEditAction,
)

# Create workspace
workdir = Path(tempfile.mkdtemp(prefix="tool_demo_"))
editor = FileEditorTool(workspace_path=str(workdir))
print(f"Workspace: {workdir}")

# Write a file
write_action = FileWriteAction(
    path="hello.py",
    content='''"""
A simple Python module.
"""

def greet(name: str) -> str:
    """Return a greeting for the given name."""
    return f"Hello, {name}!"

if __name__ == "__main__":
    print(greet("World"))
'''
)
result = editor.execute(write_action)
print(f"Write result: {result.content}")

# Read the file back
read_action = FileReadAction(path="hello.py")
result = editor.execute(read_action)
print(f"\nRead result ({len(result.content)} chars):")
print(result.content[:200])

# Edit the file
edit_action = FileEditAction(
    path="hello.py",
    old_string='return f"Hello, {name}!"',
    new_string='return f"Hello, {name}! Welcome to OpenHands."',
)
result = editor.execute(edit_action)
print(f"\nEdit result: {result.content}")

# Verify the edit
final = (workdir / "hello.py").read_text()
print(f"\nFinal file content:\n{final}")
