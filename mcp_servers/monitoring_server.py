#!/usr/bin/env python3
"""
MCP Monitoring / Observability Server — demonstrates system metrics collection,
health checks, alerting rules, and log streaming.

Install: pip install mcp psutil
Configure in .claude/settings.json:
{
  "mcpServers": {
    "monitor": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/monitoring_server.py"]
    }
  }
}
"""

import asyncio
import json
import os
import platform
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("monitor")

# ---------------------------------------------------------------------------
# Alert rule store
# ---------------------------------------------------------------------------
_alert_rules: list[dict] = []
_alert_history: list[dict] = []
MAX_ALERT_HISTORY = 200

def _check_alerts(metric_name: str, value: float) -> list[dict]:
    """Check metric value against all alert rules."""
    fired = []
    for rule in _alert_rules:
        if rule.get("metric") != metric_name:
            continue
        threshold = rule.get("threshold", 0)
        op = rule.get("operator", ">")
        triggered = False
        if op == ">":
            triggered = value > threshold
        elif op == "<":
            triggered = value < threshold
        elif op == ">=":
            triggered = value >= threshold
        elif op == "<=":
            triggered = value <= threshold
        elif op == "==":
            triggered = value == threshold

        if triggered:
            alert = {
                "rule": rule["name"],
                "metric": metric_name,
                "value": value,
                "threshold": threshold,
                "operator": op,
                "timestamp": datetime.now().isoformat(),
                "message": rule.get("message", f"{metric_name} {op} {threshold} (actual: {value})"),
            }
            fired.append(alert)
            _alert_history.append(alert)
            if len(_alert_history) > MAX_ALERT_HISTORY:
                _alert_history.pop(0)

    return fired

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def system_metrics() -> list[TextContent]:
    """Get current system metrics: CPU, memory, disk, network, uptime."""
    try:
        import psutil
    except ImportError:
        return [TextContent(type="text",
            text=json.dumps({"error": "psutil not installed. Run: pip install psutil"}, indent=2))]

    cpu = psutil.cpu_percent(interval=0.5, percpu=False)
    cpu_per_core = psutil.cpu_percent(interval=0.1, percpu=True)

    mem = psutil.virtual_memory()
    swap = psutil.swap_memory()

    disk_parts = []
    for part in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(part.mountpoint)
            disk_parts.append({
                "mount": part.mountpoint,
                "device": part.device,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "used_pct": usage.percent,
            })
        except PermissionError:
            continue

    net = psutil.net_io_counters()

    boot_time = datetime.fromtimestamp(psutil.boot_time())
    uptime = datetime.now() - boot_time

    metrics = {
        "timestamp": datetime.now().isoformat(),
        "hostname": platform.node(),
        "cpu": {
            "total_pct": cpu,
            "per_core": cpu_per_core,
            "logical_cores": psutil.cpu_count(logical=True),
            "physical_cores": psutil.cpu_count(logical=False),
        },
        "memory": {
            "total_gb": round(mem.total / (1024**3), 1),
            "available_gb": round(mem.available / (1024**3), 1),
            "used_pct": mem.percent,
            "swap_total_gb": round(swap.total / (1024**3), 1) if swap.total > 0 else 0,
            "swap_used_pct": swap.percent,
        },
        "disk": disk_parts,
        "network": {
            "sent_mb": round(net.bytes_sent / (1024**2), 1),
            "received_mb": round(net.bytes_recv / (1024**2), 1),
        },
        "uptime": str(uptime).split(".")[0],
    }

    # Check alert rules against current metrics
    alerts = _check_alerts("cpu_pct", cpu)
    alerts += _check_alerts("memory_pct", mem.percent)
    if alerts:
        metrics["alerts_fired"] = alerts

    return [TextContent(type="text", text=json.dumps(metrics, indent=2))]

@server.tool()
async def process_top(count: int = 10, sort_by: str = "cpu") -> list[TextContent]:
    """Show top processes by CPU or memory usage.

    Args:
        count: Number of processes to show
        sort_by: "cpu" or "memory"
    """
    import psutil

    procs = []
    for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent", "status"]):
        try:
            info = proc.info
            procs.append({
                "pid": info["pid"],
                "name": info["name"],
                "cpu_pct": info["cpu_percent"] or 0,
                "memory_pct": round(info["memory_percent"] or 0, 1),
                "status": info["status"],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "cpu_pct" if sort_by == "cpu" else "memory_pct"
    procs.sort(key=lambda p: p[key], reverse=True)

    return [TextContent(type="text", text=json.dumps(procs[:count], indent=2))]

@server.tool()
async def health_check(url: str, method: str = "GET", timeout: int = 10) -> list[TextContent]:
    """Perform an HTTP health check against a URL.

    Args:
        url: The URL to check
        method: HTTP method (GET, HEAD, POST)
        timeout: Timeout in seconds
    """
    import urllib.request
    import urllib.error

    start = time.time()
    try:
        req = urllib.request.Request(url, method=method)
        resp = urllib.request.urlopen(req, timeout=timeout)
        elapsed = time.time() - start
        result = {
            "url": url,
            "status": "healthy",
            "http_status": resp.status,
            "response_time_ms": round(elapsed * 1000, 1),
            "content_length": int(resp.headers.get("content-length", 0)),
        }
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start
        result = {
            "url": url,
            "status": "unhealthy",
            "http_status": e.code,
            "response_time_ms": round(elapsed * 1000, 1),
            "error": str(e),
        }
    except Exception as e:
        elapsed = time.time() - start
        result = {
            "url": url,
            "status": "down",
            "response_time_ms": round(elapsed * 1000, 1),
            "error": str(e),
        }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def create_alert_rule(
    name: str,
    metric: str,
    operator: str = ">",
    threshold: float = 80,
    message: str = "",
) -> list[TextContent]:
    """Create an alerting rule that fires when a metric crosses a threshold.

    Args:
        name: Rule name (unique identifier)
        metric: Metric to watch — "cpu_pct", "memory_pct", "disk_pct"
        operator: Comparison — ">", "<", ">=", "<=", "=="
        threshold: Threshold value
        message: Alert message template
    """
    # Remove existing rule with same name
    global _alert_rules
    _alert_rules = [r for r in _alert_rules if r["name"] != name]

    rule = {
        "name": name,
        "metric": metric,
        "operator": operator,
        "threshold": threshold,
        "message": message or f"{metric} {operator} {threshold}",
        "created_at": datetime.now().isoformat(),
    }
    _alert_rules.append(rule)

    return [TextContent(type="text", text=json.dumps({
        "created": rule,
        "total_rules": len(_alert_rules),
    }, indent=2))]

@server.tool()
async def list_alerts(limit: int = 20) -> list[TextContent]:
    """List active alert rules and recent alert history.

    Args:
        limit: Max number of historical alerts to return
    """
    return [TextContent(type="text", text=json.dumps({
        "rules": _alert_rules,
        "recent_alerts": _alert_history[-limit:],
    }, indent=2))]

@server.tool()
async def check_port(host: str, port: int, timeout: int = 5) -> list[TextContent]:
    """Check if a TCP port is open on a remote host.

    Args:
        host: Hostname or IP
        port: Port number
        timeout: Connection timeout in seconds
    """
    import socket

    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        elapsed = time.time() - start
        result = {
            "host": host,
            "port": port,
            "status": "open",
            "response_time_ms": round(elapsed * 1000, 1),
        }
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        elapsed = time.time() - start
        result = {
            "host": host,
            "port": port,
            "status": "closed",
            "response_time_ms": round(elapsed * 1000, 1),
            "error": str(e),
        }

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def monitor_snapshot(duration_seconds: int = 10, interval: int = 2) -> list[TextContent]:
    """Take multiple system metric snapshots over a time window.

    Args:
        duration_seconds: Total monitoring window (max 60)
        interval: Seconds between snapshots
    """
    import psutil

    duration_seconds = min(duration_seconds, 60)
    snapshots = []
    start = time.time()
    end = start + duration_seconds

    while time.time() < end:
        snapshots.append({
            "time": datetime.now().isoformat(),
            "cpu_pct": psutil.cpu_percent(interval=0.1),
            "memory_pct": psutil.virtual_memory().percent,
        })
        remaining = end - time.time()
        if remaining > interval:
            await asyncio.sleep(interval)
        elif remaining > 0:
            await asyncio.sleep(remaining)
        else:
            break

    cpu_values = [s["cpu_pct"] for s in snapshots]
    mem_values = [s["memory_pct"] for s in snapshots]

    return [TextContent(type="text", text=json.dumps({
        "duration_seconds": duration_seconds,
        "snapshots": snapshots,
        "summary": {
            "cpu_avg": round(sum(cpu_values) / len(cpu_values), 1) if cpu_values else 0,
            "cpu_max": max(cpu_values) if cpu_values else 0,
            "cpu_min": min(cpu_values) if cpu_values else 0,
            "memory_avg": round(sum(mem_values) / len(mem_values), 1) if mem_values else 0,
            "memory_max": max(mem_values) if mem_values else 0,
        },
    }, indent=2))]

# ---------------------------------------------------------------------------
# Resources (with subscription support)
# ---------------------------------------------------------------------------

# Track resource subscriptions for live-update simulation
_subscriptions: dict[str, float] = {}  # uri → last_notified_timestamp

@server.resource("monitor://alert-rules")
async def alert_rules() -> str:
    return json.dumps(_alert_rules, indent=2)

@server.resource("monitor://alert-history")
async def alert_history() -> str:
    return json.dumps(_alert_history[-50:], indent=2)

@server.resource("monitor://live-metrics")
async def live_metrics() -> str:
    """A resource that changes frequently — ideal for subscriptions.
    Clients can subscribe to be notified when metrics change."""
    import psutil
    cpu = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory().percent
    timestamp = datetime.now().isoformat()
    return json.dumps({
        "timestamp": timestamp,
        "cpu_pct": cpu,
        "memory_pct": mem,
        "subscriptions_active": len(_subscriptions),
        "note": "This resource supports subscriptions. Subscribe to get notifications when metrics change.",
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="diagnose-issue",
    description="Diagnose a system issue using monitoring data",
    arguments={
        "symptom": {"type": "string", "description": "What symptom are you seeing?", "required": True},
    },
)
async def diagnose_prompt(symptom: str) -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Diagnose the following system issue using the monitoring tools available.

Reported symptom: {symptom}

Use the tools (system_metrics, process_top, check_port, health_check, etc.) to investigate.
Provide:
1. Likely root cause
2. Evidence from monitoring data
3. Recommended fix
4. Prevention steps""",
            },
        }],
    }

@server.prompt(
    name="system-audit",
    description="Complete system health audit and report",
    arguments={
        "report_format": {
            "type": "string",
            "enum": ["executive", "technical", "compliance"],
            "description": "Who is the audience for this audit report?",
            "required": False,
        },
    },
)
async def system_audit_prompt(report_format: str = "technical") -> dict:
    style_guides = {
        "executive": "Use business language, focus on risk and ROI, use traffic-light indicators (🟢🟡🔴), keep under 1 page.",
        "technical": "Include exact metrics, thresholds, and commands. Use tables for data. Be detailed and precise.",
        "compliance": "Map findings to compliance frameworks (SOC2, HIPAA, PCI). Include remediation timelines and ownership.",
    }
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Perform a complete system health audit.

Report format: {report_format}
{style_guides.get(report_format, style_guides['technical'])}

Use ALL monitoring tools:
1. system_metrics — CPU, memory, disk, network, uptime
2. process_top — check for resource-hungry processes
3. check_port — verify critical ports are accessible
4. health_check — test any HTTP endpoints
5. monitor_snapshot — take a 10-second window of metrics for trend analysis

Also:
- Create alert rules for any metrics approaching thresholds (create_alert_rule)
- Review existing alert history (list_alerts)

AUDIT REPORT SECTIONS:
1. Executive Summary
2. Resource Utilization (CPU/Memory/Disk)
3. Process Health
4. Network & Port Status
5. Alerts & Thresholds
6. Recommendations (prioritized)""",
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
