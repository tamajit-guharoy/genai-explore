"""
04_agent_server_client.py -- Connect to a remote Agent Server
Based on Section 8.3 of openhands-tutorial.md

Prerequisites:
    1. Start the Agent Server: openhands agent-server
    2. Or: docker-compose -f ../configs/docker-compose-server.yml up -d
    3. Verify: curl http://localhost:8000/api/alive
"""

import os
from openhands.sdk import LLM, Agent, Conversation
from openhands.workspace import RemoteWorkspace

# Configure the LLM
llm = LLM(
    model=os.getenv("LLM_MODEL", "gpt-5.5"),
    api_key=os.getenv("LLM_API_KEY"),
)

# Create the agent
agent = Agent(
    llm=llm,
    tools=[],  # Tools are managed by the server
    system_prompt="You are a helpful coding assistant.",
)

# Connect to the remote server
workspace = RemoteWorkspace(
    base_url="http://localhost:8000",
    # api_key="your-server-token",  # Uncomment if server requires auth
)

# Run the conversation remotely
conversation = Conversation(
    agent=agent,
    workspace=workspace,
    max_iterations=15,
)

print("Connected to Agent Server at http://localhost:8000")
print("Sending task...")

result = conversation.run(
    "List the files in the current directory and create a summary.txt "
    "file describing what you find."
)

print(f"\nResult: {result.status}")
print(f"Iterations: {result.iterations}")
if result.status == "finished":
    print("Task completed successfully!")
else:
    print(f"Task stopped: {result.message}")
