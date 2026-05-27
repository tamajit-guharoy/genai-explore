#!/usr/bin/env python3
"""
MCP DevOps Server — demonstrates shell command execution with security sandboxing,
process management, and environment-aware operations.

Install: pip install mcp
Configure in .claude/settings.json:
{
  "mcpServers": {
    "devops": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/devops_server.py"],
      "env": {
        "DEVOPS_ALLOWED_DIRS": "/home/user/projects,/var/log",
        "DEVOPS_BLOCKED_COMMANDS": "rm,shutdown,reboot,mkfs,dd"
      }
    }
  }
}
"""

import asyncio
import json
import os
import platform
import re
import shlex
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("devops")

# ---------------------------------------------------------------------------
# Security configuration
# ---------------------------------------------------------------------------
ALLOWED_DIRS = [
    Path(d.strip()) for d in
    os.environ.get("DEVOPS_ALLOWED_DIRS", str(Path.home())).split(",")
    if d.strip()
]
BLOCKED_COMMANDS = set(
    c.strip() for c in
    os.environ.get("DEVOPS_BLOCKED_COMMANDS", "rm,shutdown,reboot,mkfs,dd,chmod").split(",")
    if c.strip()
)

def _is_path_allowed(target: str) -> bool:
    """Check if a path is within allowed directories."""
    p = Path(target).resolve()
    return any(
        str(p).startswith(str(allowed.resolve()))
        for allowed in ALLOWED_DIRS
    )

def _is_command_safe(cmd: str) -> tuple[bool, str]:
    """Check a command string against blocked patterns."""
    tokens = shlex.split(cmd)
    if not tokens:
        return False, "Empty command"
    base = os.path.basename(tokens[0])
    if base in BLOCKED_COMMANDS:
        return False, f"Blocked command: {base}"
    # Check for path traversal
    if ".." in cmd:
        return False, "Path traversal detected"
    return True, "ok"

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def run_command(
    command: str,
    cwd: str = "",
    timeout_seconds: int = 30,
    capture_stderr: bool = True,
) -> list[TextContent]:
    """Run a shell command securely within allowed directories.

    Args:
        command: The shell command to execute
        cwd: Working directory (must be within allowed dirs). Defaults to current dir.
        timeout_seconds: Maximum runtime in seconds. Defaults to 30.
        capture_stderr: Whether to capture stderr. Defaults to True.
    """
    safe, reason = _is_command_safe(command)
    if not safe:
        return [TextContent(type="text", text=json.dumps({"error": reason}, indent=2))]

    work_dir = Path(cwd).resolve() if cwd else Path.cwd()
    if not _is_path_allowed(str(work_dir)):
        return [TextContent(type="text",
            text=json.dumps({"error": f"Directory not allowed: {work_dir}"}, indent=2))]

    try:
        proc = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE if capture_stderr else None,
            cwd=str(work_dir),
            executable="/bin/bash" if sys.platform != "win32" else None,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=timeout_seconds
        )
        result = {
            "command": command,
            "exit_code": proc.returncode,
            "stdout": stdout.decode("utf-8", errors="replace") if stdout else "",
        }
        if stderr:
            result["stderr"] = stderr.decode("utf-8", errors="replace")
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    except asyncio.TimeoutError:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Command timed out after {timeout_seconds}s", "command": command}, indent=2))]
    except Exception as e:
        return [TextContent(type="text",
            text=json.dumps({"error": str(e), "command": command}, indent=2))]

@server.tool()
async def list_processes(filter_name: str = "") -> list[TextContent]:
    """List running processes, optionally filtered by name.

    Args:
        filter_name: Optional substring to filter process names
    """
    procs = []
    try:
        if sys.platform == "win32":
            output = subprocess.check_output(
                ["tasklist", "/FO", "CSV", "/NH"], text=True, timeout=10
            )
            for line in output.strip().splitlines():
                parts = line.replace('"', '').split(",")
                if len(parts) >= 5:
                    name, pid = parts[0], parts[1]
                    if filter_name.lower() in name.lower():
                        procs.append({
                            "name": name,
                            "pid": int(pid),
                            "memory_kb": parts[4].replace(" K", "").strip(),
                        })
        else:
            output = subprocess.check_output(
                ["ps", "aux", "--no-headers"], text=True, timeout=10
            )
            for line in output.strip().splitlines():
                if filter_name.lower() in line.lower():
                    parts = line.split()
                    if len(parts) >= 11:
                        procs.append({
                            "user": parts[0],
                            "pid": int(parts[1]),
                            "cpu_pct": parts[2],
                            "mem_pct": parts[3],
                            "command": " ".join(parts[10:]),
                        })
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

    return [TextContent(type="text", text=json.dumps(procs, indent=2))]

@server.tool()
async def disk_usage(path: str = ".") -> list[TextContent]:
    """Show disk usage for a directory or file.

    Args:
        path: Directory path to analyze (must be within allowed dirs)
    """
    if not _is_path_allowed(path):
        return [TextContent(type="text",
            text=json.dumps({"error": f"Path not allowed: {path}"}, indent=2))]

    p = Path(path).resolve()
    cmd = ["du", "-sh", str(p)] if sys.platform != "win32" else ["powershell", "-Command",
        f"(Get-ChildItem -Path '{p}' -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB"]

    try:
        output = subprocess.check_output(cmd, text=True, timeout=30, stderr=subprocess.STDOUT)
        return [TextContent(type="text", text=output.strip())]
    except Exception as e:
        return [TextContent(type="text", text=json.dumps({"error": str(e)}, indent=2))]

@server.tool()
async def system_info() -> list[TextContent]:
    """Get comprehensive system information."""
    info = {
        "hostname": platform.node(),
        "os": platform.system(),
        "os_release": platform.release(),
        "os_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "python_version": sys.version,
        "cpu_count_logical": os.cpu_count(),
        "current_time_utc": datetime.now(timezone.utc).isoformat(),
        "current_timezone": str(time.tzname),
    }

    # Memory info
    try:
        import psutil
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total_gb": round(mem.total / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "used_pct": mem.percent,
        }
        disk = psutil.disk_usage("/")
        info["disk"] = {
            "total_gb": round(disk.total / (1024**3), 1),
            "free_gb": round(disk.free / (1024**3), 1),
            "used_pct": disk.percent,
        }
    except ImportError:
        info["memory"] = "psutil not installed — pip install psutil for memory info"

    return [TextContent(type="text", text=json.dumps(info, indent=2))]

@server.tool()
async def port_scan(host: str = "localhost", start_port: int = 1, end_port: int = 1024) -> list[TextContent]:
    """Scan TCP ports on a host to find open ones.

    Args:
        host: Hostname or IP to scan. Defaults to localhost.
        start_port: First port to check. Defaults to 1.
        end_port: Last port to check. Defaults to 1024.
    """
    import socket

    if end_port - start_port > 1024:
        raise ValueError("Port range too large (max 1024 ports per scan)")

    open_ports = []
    for port in range(start_port, end_port + 1):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex((host, port))
            if result == 0:
                try:
                    svc = socket.getservbyport(port)
                except OSError:
                    svc = "unknown"
                open_ports.append({"port": port, "service": svc})
            sock.close()
        except Exception:
            continue

    return [TextContent(type="text", text=json.dumps({
        "host": host,
        "scanned_range": f"{start_port}-{end_port}",
        "open_ports": open_ports,
    }, indent=2))]

@server.tool()
async def log_tail(
    log_file: str,
    lines: int = 50,
    grep_filter: str = "",
) -> list[TextContent]:
    """Read the last N lines of a log file, optionally filtering by pattern.

    Args:
        log_file: Path to the log file (must be within allowed dirs)
        lines: Number of lines to return. Defaults to 50.
        grep_filter: Only return lines containing this text. Optional.
    """
    if not _is_path_allowed(log_file):
        return [TextContent(type="text",
            text=json.dumps({"error": f"File not allowed: {log_file}"}, indent=2))]

    log_path = Path(log_file)
    if not log_path.exists():
        return [TextContent(type="text",
            text=json.dumps({"error": f"File not found: {log_file}"}, indent=2))]

    content = log_path.read_text(errors="replace")
    log_lines = content.splitlines()[-lines:]
    if grep_filter:
        log_lines = [l for l in log_lines if grep_filter.lower() in l.lower()]

    return [TextContent(type="text", text="\n".join(log_lines))]

@server.tool()
async def env_manager(action: str, key: str = "", value: str = "") -> list[TextContent]:
    """Manage environment variables for this server session.

    Args:
        action: "get", "set", "list", or "delete"
        key: Environment variable name (for get/set/delete)
        value: Value to set (for set only)
    """
    if action == "list":
        envs = {k: v for k, v in sorted(os.environ.items()) if not k.startswith("_")}
        return [TextContent(type="text", text=json.dumps(envs, indent=2))]
    elif action == "get":
        val = os.environ.get(key, "")
        return [TextContent(type="text", text=f"{key}={val}" if val else f"{key} is not set")]
    elif action == "set":
        os.environ[key] = value
        return [TextContent(type="text", text=f"Set {key}={value}")]
    elif action == "delete":
        os.environ.pop(key, None)
        return [TextContent(type="text", text=f"Deleted {key}")]
    else:
        raise ValueError(f"Unknown action: {action}")

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("devops://allowed-dirs")
async def get_allowed_dirs() -> str:
    return json.dumps([str(d) for d in ALLOWED_DIRS], indent=2)

@server.resource("devops://blocked-commands")
async def get_blocked_commands() -> str:
    return json.dumps(sorted(BLOCKED_COMMANDS), indent=2)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
