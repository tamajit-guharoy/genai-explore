#!/usr/bin/env python3
"""
MCP Notification Server — demonstrates desktop notifications, event scheduling,
and persistent state management.

Install: pip install mcp schedule
Windows: No extra deps needed (uses win10toast or fallback)
macOS: No extra deps needed (uses osascript)
Linux: pip install notify2

Configure in .claude/settings.json:
{
  "mcpServers": {
    "notify": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/notification_server.py"]
    }
  }
}
"""

import asyncio
import json
import os
import platform
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("notify")

# ---------------------------------------------------------------------------
# In-memory scheduled task store (persisted to JSON for demo)
# ---------------------------------------------------------------------------
SCHEDULE_FILE = Path(os.environ.get("NOTIFY_SCHEDULE_FILE", ".notify_schedule.json"))
_tasks: dict[str, dict] = {}

def _load_tasks():
    global _tasks
    if SCHEDULE_FILE.exists():
        _tasks = json.loads(SCHEDULE_FILE.read_text())

def _save_tasks():
    SCHEDULE_FILE.write_text(json.dumps(_tasks, indent=2))

_load_tasks()

# ---------------------------------------------------------------------------
# OS-level notification
# ---------------------------------------------------------------------------

def _send_os_notification(title: str, body: str = "", urgency: str = "normal") -> bool:
    """Send a native desktop notification."""
    system = platform.system()
    try:
        if system == "Windows":
            # Using PowerShell toast notification
            ps_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
                [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{body}")) > $null
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude MCP").Show($toast)
            '''
            # Fallback: use simple message box approach
            subprocess.run(
                ["powershell", "-Command",
                 f'[System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms");'
                 f'[System.Windows.Forms.MessageBox]::Show("{body}", "{title}")'],
                capture_output=True, timeout=5,
            )
        elif system == "Darwin":
            subprocess.run([
                "osascript", "-e",
                f'display notification "{body}" with title "{title}"',
            ], capture_output=True, timeout=5)
        else:
            # Linux — try notify-send
            subprocess.run([
                "notify-send", "-u", urgency, title, body,
            ], capture_output=True, timeout=5)
        return True
    except Exception:
        return False

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def send_notification(
    title: str,
    body: str = "",
    urgency: str = "normal",
) -> list[TextContent]:
    """Send a desktop notification immediately.

    Args:
        title: Notification title
        body: Notification body text
        urgency: "low", "normal", or "critical"
    """
    ok = _send_os_notification(title, body, urgency)
    result = {
        "sent": ok,
        "title": title,
        "body": body,
        "timestamp": datetime.now().isoformat(),
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def schedule_notification(
    title: str,
    body: str,
    delay_seconds: int = 60,
    recurring: bool = False,
    interval_seconds: int = 0,
) -> list[TextContent]:
    """Schedule a notification to be sent after a delay, optionally recurring.

    Note: The schedule is stored in memory; notifications fire only while
    this server process is running.

    Args:
        title: Notification title
        body: Notification body text
        delay_seconds: Seconds to wait before first notification (min 5)
        interval_seconds: Seconds between repeats (if recurring). Default 0 = no repeat.
        recurring: Whether to repeat the notification
    """
    if delay_seconds < 5:
        delay_seconds = 5

    task_id = f"task_{int(time.time() * 1000)}"
    fire_at = (datetime.now() + timedelta(seconds=delay_seconds)).isoformat()

    _tasks[task_id] = {
        "id": task_id,
        "title": title,
        "body": body,
        "delay_seconds": delay_seconds,
        "recurring": recurring,
        "interval_seconds": interval_seconds if recurring else 0,
        "fire_at": fire_at,
        "created_at": datetime.now().isoformat(),
        "fired_count": 0,
    }
    _save_tasks()

    return [TextContent(type="text", text=json.dumps({
        "task_id": task_id,
        "message": f"Notification scheduled to fire at {fire_at}",
        "recurring": recurring,
    }, indent=2))]

@server.tool()
async def list_scheduled() -> list[TextContent]:
    """List all scheduled notifications (pending and recurring)."""
    return [TextContent(type="text", text=json.dumps(list(_tasks.values()), indent=2))]

@server.tool()
async def cancel_notification(task_id: str) -> list[TextContent]:
    """Cancel a scheduled notification by its task ID.

    Args:
        task_id: The task ID from schedule_notification
    """
    if task_id in _tasks:
        del _tasks[task_id]
        _save_tasks()
        return [TextContent(type="text", text=json.dumps({"cancelled": task_id}, indent=2))]
    return [TextContent(type="text", text=json.dumps({"error": f"Task not found: {task_id}"}, indent=2))]

@server.tool()
async def countdown_timer(
    label: str,
    duration_seconds: int,
    interval: int = 1,
) -> list[TextContent]:
    """Run a countdown timer and notify at completion.

    Args:
        label: What this timer is for (e.g. "Pizza in oven", "Build complete")
        duration_seconds: Total timer duration in seconds (max 3600)
        interval: Log progress every N seconds. Default 1.
    """
    if duration_seconds > 3600:
        duration_seconds = 3600
    if duration_seconds < 1:
        duration_seconds = 1

    start = time.time()
    end = start + duration_seconds
    log = [f"Timer started: {label} ({duration_seconds}s)"]

    while time.time() < end:
        await asyncio.sleep(interval)
        remaining = int(end - time.time())
        if remaining <= 0:
            break
        log.append(f"[{label}] Remaining: {remaining}s")

    elapsed = time.time() - start
    _send_os_notification(f"Timer Done: {label}", f"Completed in {elapsed:.0f}s")
    log.append(f"Timer finished: {label} — elapsed {elapsed:.0f}s")

    return [TextContent(type="text", text="\n".join(log))]

@server.tool()
async def remind_at(
    message: str,
    iso_time: str,
) -> list[TextContent]:
    """Schedule a one-time reminder at a specific ISO datetime.

    Args:
        message: Reminder message text
        iso_time: ISO datetime string, e.g. "2026-05-26T14:30:00"
    """
    try:
        target = datetime.fromisoformat(iso_time)
    except ValueError:
        return [TextContent(type="text",
            text=json.dumps({"error": "Invalid ISO datetime. Use format: 2026-05-26T14:30:00"}, indent=2))]

    now = datetime.now()
    if target <= now:
        return [TextContent(type="text",
            text=json.dumps({"error": "Target time is in the past"}, indent=2))]

    delay = int((target - now).total_seconds())
    task_id = f"remind_{int(time.time() * 1000)}"
    _tasks[task_id] = {
        "id": task_id,
        "title": f"Reminder: {message[:50]}",
        "body": message,
        "type": "reminder",
        "fire_at": iso_time,
        "delay_seconds": delay,
        "created_at": now.isoformat(),
    }
    _save_tasks()

    return [TextContent(type="text", text=json.dumps({
        "task_id": task_id,
        "message": f"Reminder scheduled for {iso_time}",
    }, indent=2))]

# ---------------------------------------------------------------------------
# Background scheduler
# ---------------------------------------------------------------------------

async def _scheduler_loop():
    """Check scheduled tasks and fire notifications."""
    while True:
        await asyncio.sleep(5)
        now = datetime.now()
        to_fire = []
        for task_id, task in list(_tasks.items()):
            fire_at = datetime.fromisoformat(task["fire_at"])
            if now >= fire_at:
                to_fire.append(task)
                if not task.get("recurring"):
                    del _tasks[task_id]
                else:
                    # Reschedule for next interval
                    task["fired_count"] = task.get("fired_count", 0) + 1
                    next_fire = now + timedelta(seconds=task.get("interval_seconds", 60))
                    task["fire_at"] = next_fire.isoformat()
        if to_fire:
            _save_tasks()
            for task in to_fire:
                _send_os_notification(task["title"], task.get("body", ""))

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("notify://scheduled-tasks")
async def scheduled_tasks() -> str:
    return json.dumps(list(_tasks.values()), indent=2, default=str)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="pomodoro-session",
    description="Set up a Pomodoro-style work session with notifications",
    arguments={
        "task_name": {
            "type": "string",
            "description": "What you're working on",
            "required": True,
        },
        "num_sessions": {
            "type": "number",
            "description": "How many 25-min focus sessions? Default 4.",
            "required": False,
        },
    },
)
async def pomodoro_prompt(task_name: str, num_sessions: int = 4) -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Set up a Pomodoro work session for: {task_name} ({num_sessions} sessions).

Use the notification tools to:
1. Schedule a notification for each 25-minute work session end
2. Schedule a 5-minute break notification between each session
3. After the 4th session, schedule a 15-minute long-break notification
4. Use countdown_timer for the first session (so user sees live progress)
5. Display all scheduled notifications with list_scheduled

The user wants to start now. First session: 25 minutes from now.""",
            },
        }],
    }

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    # Start background scheduler
    asyncio.create_task(_scheduler_loop())
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
