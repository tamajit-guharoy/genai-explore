"""
01_minimal_agent.py -- Your first OpenHands agent
Based on Section 4 of openhands-tutorial.md

Prerequisites:
    export LLM_API_KEY=sk-...
    export LLM_MODEL="gpt-5.5"  # or claude-sonnet-4-5, etc.
    uv tool install openhands --python 3.12
"""

import os
from pathlib import Path
from openhands.sdk import LLM, Agent, Conversation
from openhands.tools.file_editor import FileEditorTool

# Step 1: Create the LLM
llm = LLM(
    model=os.getenv("LLM_MODEL", "gpt-5.5"),
    api_key=os.getenv("LLM_API_KEY"),
)

# Step 2: Configure the agent
agent = Agent(
    llm=llm,
    tools=[FileEditorTool],
    system_prompt="You are a helpful coding assistant. Write clean, well-documented code.",
)

# Step 3: Create a workspace
workspace_dir = Path("./agent_workspace")
workspace_dir.mkdir(exist_ok=True)

# Step 4: Run the conversation
conversation = Conversation(
    agent=agent,
    workspace_path=str(workspace_dir),
    max_iterations=20,
)

# Step 5: Give it a task
result = conversation.run(
    "Create a file called 'project_info.py' that contains a function "
    "get_project_info() returning a dict with 'name', 'version', and 'description' keys."
)

# Step 6: Check the result
print(f"Status: {result.status}")
print(f"Iterations: {result.iterations}")
if result.status == "finished":
    info_file = workspace_dir / "project_info.py"
    if info_file.exists():
        print(f"\nGenerated file ({info_file.stat().st_size} bytes):")
        print(info_file.read_text())
else:
    print(f"Agent stopped: {result.message}")
