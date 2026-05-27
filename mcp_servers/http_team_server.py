#!/usr/bin/env python3
"""
MCP HTTP Team Server — demonstrates HTTP/SSE-based MCP transport for remote,
team-shared servers. Unlike the stdio servers (which run as local child processes),
this server runs as a standalone HTTP service that multiple Claude Code instances
can connect to simultaneously.

This demonstrates the OTHER transport mode: HTTP with Server-Sent Events (SSE).

Install: pip install mcp uvicorn starlette
Run:    python mcp_servers/http_team_server.py --port 9020
Configure in .claude/settings.json:
{
  "mcpServers": {
    "team-dashboard": {
      "type": "url",
      "url": "http://localhost:9020/mcp"
    }
  }
}

For team-wide deployment, host on internal infrastructure and use:
{
  "mcpServers": {
    "team-dashboard": {
      "type": "url",
      "url": "https://mcp.internal.company.com/mcp",
      "auth": "oauth"
    }
  }
}

Architecture:
  Claude Code ──HTTP──► Starlette/ASGI server ──► MCP Server (SSE transport)
  Multiple Claude Code instances can connect to the same server process.
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.sse import SseServerTransport
from mcp.types import Tool, TextContent, Resource
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.requests import Request
from starlette.responses import JSONResponse


# ===========================================================================
# Server setup — note: using SSE transport, NOT stdio
# ===========================================================================
server = Server("team-dashboard")

# Shared state (persists across all connected clients)
_shared_state: dict[str, Any] = {
    "team_notes": [],
    "deployments": [],
    "oncall_schedule": {},
    "feature_flags": {},
    "started_at": datetime.now().isoformat(),
    "connected_clients": 0,
    "total_requests": 0,
}


# ===========================================================================
# Tools
# ===========================================================================

@server.tool()
async def team_announce(
    message: str,
    author: str = "Claude",
    priority: str = "normal",
) -> list[TextContent]:
    """Post an announcement to the team dashboard. All connected Claude instances can see it.

    Args:
        message: The announcement text (supports markdown)
        author: Who is posting. Defaults to "Claude".
        priority: "low", "normal", "high", or "urgent"
    """
    entry = {
        "id": f"announce-{int(time.time() * 1000)}",
        "message": message,
        "author": author,
        "priority": priority,
        "timestamp": datetime.now().isoformat(),
        "type": "announcement",
    }
    _shared_state["team_notes"].append(entry)
    # Keep last 200
    if len(_shared_state["team_notes"]) > 200:
        _shared_state["team_notes"] = _shared_state["team_notes"][-200:]

    return [TextContent(type="text", text=json.dumps({
        "posted": True,
        "announcement": entry,
        "total_announcements": len(_shared_state["team_notes"]),
    }, indent=2))]


@server.tool()
async def get_team_activity(limit: int = 20) -> list[TextContent]:
    """Read recent team activity from the shared dashboard.

    Args:
        limit: Max entries to return. Defaults to 20.
    """
    recent = _shared_state["team_notes"][-limit:]
    deploys = _shared_state["deployments"][-5:]
    return [TextContent(type="text", text=json.dumps({
        "recent_announcements": recent,
        "recent_deployments": deploys,
        "connected_clients": _shared_state["connected_clients"],
        "server_uptime_minutes": round(
            (datetime.now() - datetime.fromisoformat(_shared_state["started_at"])).total_seconds() / 60, 1
        ),
        "total_requests_handled": _shared_state["total_requests"],
    }, indent=2, default=str))]


@server.tool()
async def record_deployment(
    service: str,
    version: str,
    environment: str = "staging",
    status: str = "started",
    changelog: str = "",
) -> list[TextContent]:
    """Record a deployment event visible to the whole team.

    Args:
        service: Service name (e.g. "api-server", "frontend")
        version: Version tag or commit SHA being deployed
        environment: "staging" or "production"
        status: "started", "completed", "failed", "rolled_back"
        changelog: Brief description of changes
    """
    deploy = {
        "id": f"deploy-{int(time.time() * 1000)}",
        "service": service,
        "version": version,
        "environment": environment,
        "status": status,
        "changelog": changelog,
        "timestamp": datetime.now().isoformat(),
    }
    _shared_state["deployments"].append(deploy)
    if len(_shared_state["deployments"]) > 100:
        _shared_state["deployments"] = _shared_state["deployments"][-100:]

    return [TextContent(type="text", text=json.dumps({
        "recorded": True,
        "deployment": deploy,
        "active_deployments": len([
            d for d in _shared_state["deployments"]
            if d["status"] == "started"
        ]),
    }, indent=2))]


@server.tool()
async def manage_feature_flags(
    action: str,
    flag_name: str = "",
    flag_value: str = "",
) -> list[TextContent]:
    """Manage shared feature flags visible to all team members.

    Args:
        action: "list", "set", "get", "delete", "toggle"
        flag_name: Feature flag name (for set/get/delete/toggle)
        flag_value: Value to set ("true", "false", or JSON). For toggle, this is ignored.
    """
    if action == "list":
        return [TextContent(type="text", text=json.dumps({
            "flags": _shared_state["feature_flags"],
            "count": len(_shared_state["feature_flags"]),
        }, indent=2))]

    if action == "set":
        if not flag_name:
            raise ValueError("flag_name is required for 'set'")
        _shared_state["feature_flags"][flag_name] = {
            "value": flag_value,
            "updated_at": datetime.now().isoformat(),
            "updated_by": "Claude (MCP HTTP)",
        }
        return [TextContent(type="text", text=json.dumps({
            "set": flag_name,
            "value": flag_value,
        }, indent=2))]

    if action == "get":
        flag = _shared_state["feature_flags"].get(flag_name)
        return [TextContent(type="text",
            text=json.dumps({flag_name: flag} if flag else {"error": f"Flag not found: {flag_name}"}, indent=2))]

    if action == "delete":
        if flag_name in _shared_state["feature_flags"]:
            del _shared_state["feature_flags"][flag_name]
            return [TextContent(type="text", text=json.dumps({"deleted": flag_name}, indent=2))]
        return [TextContent(type="text",
            text=json.dumps({"error": f"Flag not found: {flag_name}"}, indent=2))]

    if action == "toggle":
        current = _shared_state["feature_flags"].get(flag_name, {}).get("value", "false")
        new_value = "false" if current.lower() == "true" else "true"
        _shared_state["feature_flags"][flag_name] = {
            "value": new_value,
            "updated_at": datetime.now().isoformat(),
            "updated_by": "Claude (MCP HTTP) — toggled",
        }
        return [TextContent(type="text",
            text=json.dumps({"toggled": flag_name, "new_value": new_value}, indent=2))]

    raise ValueError(f"Unknown action: {action}")


@server.tool()
async def oncall_status(week_of: str = "") -> list[TextContent]:
    """Check who is on call. Team members can update the schedule.

    Args:
        week_of: ISO date of the Monday of the week. Defaults to current week.
    """
    if not week_of:
        today = datetime.now().date()
        week_of = (today - timedelta(days=today.weekday())).isoformat()

    schedule = _shared_state.get("oncall_schedule", {})
    return [TextContent(type="text", text=json.dumps({
        "week_of": week_of,
        "oncall": schedule.get(week_of, "No one scheduled — use record_deployment to suggest"),
        "full_schedule": schedule,
    }, indent=2))]


# ===========================================================================
# Resources
# ===========================================================================

@server.resource("team://dashboard")
async def full_dashboard() -> str:
    """The complete team dashboard as a resource."""
    return json.dumps({
        "server_started": _shared_state["started_at"],
        "uptime_minutes": round(
            (datetime.now() - datetime.fromisoformat(_shared_state["started_at"])).total_seconds() / 60, 1
        ),
        "connected_clients": _shared_state["connected_clients"],
        "total_requests": _shared_state["total_requests"],
        "active_deployments": [d for d in _shared_state["deployments"][-10:]],
        "feature_flags": _shared_state["feature_flags"],
        "recent_announcements": _shared_state["team_notes"][-10:],
    }, indent=2, default=str)


@server.resource("team://deployment/{deploy_id}")
async def get_deployment(deploy_id: str) -> str:
    """Parameterized resource — get a specific deployment by ID."""
    for d in _shared_state["deployments"]:
        if d.get("id") == deploy_id:
            return json.dumps(d, indent=2, default=str)
    return json.dumps({"error": f"Deployment not found: {deploy_id}"})


# ===========================================================================
# Prompts
# ===========================================================================

@server.prompt(
    name="standup-report",
    description="Generate a daily standup report from team activity",
    arguments={
        "team_member": {
            "type": "string",
            "description": "Your name for the standup",
            "required": True,
        },
    },
)
async def standup_report_prompt(team_member: str) -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Generate a standup report for {team_member} using the team dashboard data.

Use get_team_activity and oncall_status to gather:
1. Recent announcements relevant to {team_member}
2. Active deployments and their status
3. Feature flag changes
4. Who's on call

Then produce a standup report in this format:

YESTERDAY:
- [What was done — inferred from deployment records and announcements]

TODAY:
- [What's planned — based on active work]

BLOCKERS:
- [Any issues — from failed deployments or announcements]

ONCALL NOTES:
- [Current oncall and any relevant alerts]""",
            },
        }],
    }


@server.prompt(
    name="deploy-coordination",
    description="Coordinate a production deployment across the team",
    arguments={
        "service": {
            "type": "string",
            "description": "Which service is being deployed",
            "required": True,
        },
        "version": {
            "type": "string",
            "description": "Version or commit being deployed",
            "required": True,
        },
    },
)
async def deploy_coordination_prompt(service: str, version: str) -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Coordinate a deployment of {service} version {version}.

Steps:
1. Use team_announce to notify the team: "Deploying {service} {version} to production"
2. Use record_deployment to log the deployment start
3. After deployment, update the deployment status with record_deployment
4. If anything goes wrong, announce it with priority="urgent"
5. Use oncall_status to check who to escalate to if needed
6. After completion, post a summary announcement

Use the deployment checklist:
- [ ] Pre-deploy announcement posted
- [ ] Deployment recorded (status: started)
- [ ] Health check passed
- [ ] Deployment recorded (status: completed)
- [ ] Post-deploy summary posted""",
            },
        }],
    }


# ===========================================================================
# HTTP Server with SSE transport (the key difference from stdio servers!)
# ===========================================================================

# Track connected clients for the dashboard
_active_transports: list[SseServerTransport] = []


async def handle_mcp_connection(request: Request):
    """Handle an incoming SSE connection from a Claude Code client.

    This is where the HTTP transport is established. Each Claude Code instance
    that connects gets its own SSE stream. The server can handle multiple
    concurrent connections.
    """
    # Create SSE transport for this connection
    transport = SseServerTransport("/mcp/messages")

    # Track the connection
    _active_transports.append(transport)
    _shared_state["connected_clients"] = len(_active_transports)

    try:
        # Run the MCP server with this transport
        async with transport.connect_sse(
            request.scope, request.receive, request._send
        ) as streams:
            await server.run(streams[0], streams[1],
                             server.create_initialization_options())
    finally:
        # Cleanup on disconnect
        if transport in _active_transports:
            _active_transports.remove(transport)
        _shared_state["connected_clients"] = len(_active_transports)


async def handle_messages(request: Request):
    """Handle incoming MCP messages from clients (the POST endpoint)."""
    _shared_state["total_requests"] += 1

    # Find the transport that matches this session
    session_id = request.query_params.get("session_id", "")
    for transport in _active_transports:
        if hasattr(transport, "_session_id") and transport._session_id == session_id:
            await transport.handle_post_message(request.scope, request.receive, request._send)
            return

    return JSONResponse({"error": "Session not found"}, status_code=404)


async def health_endpoint(request: Request):
    """Health check — useful for load balancers and monitoring."""
    return JSONResponse({
        "status": "healthy",
        "server": "team-dashboard-mcp",
        "transport": "SSE (HTTP)",
        "connected_clients": _shared_state["connected_clients"],
        "uptime_minutes": round(
            (datetime.now() - datetime.fromisoformat(_shared_state["started_at"])).total_seconds() / 60, 1
        ),
    })


# ===========================================================================
# Startup — run as HTTP server (NOT stdio!)
# ===========================================================================

def main():
    import uvicorn

    port = int(os.environ.get("PORT", "9020"))

    app = Starlette(
        routes=[
            Route("/mcp", handle_mcp_connection, methods=["GET"]),    # SSE endpoint
            Route("/mcp/messages", handle_messages, methods=["POST"]), # Message endpoint
            Route("/health", health_endpoint, methods=["GET"]),        # Health check
        ],
    )

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  MCP HTTP Team Dashboard Server                          ║
║  Transport: SSE (Server-Sent Events) over HTTP           ║
║  Listening on: http://0.0.0.0:{port}/mcp                   ║
║  Health check: http://localhost:{port}/health               ║
║                                                          ║
║  Configure Claude Code with:                             ║
║  {{"mcpServers": {{                                         ║
║    "team-dashboard": {{                                   ║
║      "type": "url",                                      ║
║      "url": "http://localhost:{port}/mcp"                  ║
║    }}                                                    ║
║  }}}}                                                     ║
║                                                          ║
║  Multiple Claude Code instances can connect!             ║
╚══════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()
