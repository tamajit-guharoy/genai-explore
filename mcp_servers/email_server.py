#!/usr/bin/env python3
"""
MCP Email Server — demonstrates email composition with templates, SMTP sending,
attachment handling, and email validation.

Install: pip install mcp
Configure in .claude/settings.json:
{
  "mcpServers": {
    "email": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/email_server.py"],
      "env": {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": "587",
        "SMTP_USER": "you@gmail.com",
        "SMTP_PASS": "your-app-password"
      }
    }
  }
}
"""

import asyncio
import email.utils
import json
import os
import re
import smtplib
import time
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("email")

# ---------------------------------------------------------------------------
# Template store
# ---------------------------------------------------------------------------
TEMPLATES_FILE = Path(os.environ.get("EMAIL_TEMPLATES_FILE", ".email_templates.json"))
_templates: dict[str, dict] = {}

def _load_templates():
    global _templates
    if TEMPLATES_FILE.exists():
        _templates = json.loads(TEMPLATES_FILE.read_text())

def _save_templates():
    TEMPLATES_FILE.write_text(json.dumps(_templates, indent=2))

_load_templates()

# ---------------------------------------------------------------------------
# Email validation
# ---------------------------------------------------------------------------

def _validate_email(email_addr: str) -> bool:
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email_addr))

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def validate_email_address(email_addr: str) -> list[TextContent]:
    """Validate an email address format and check for common issues.

    Args:
        email_addr: Email address to validate
    """
    checks = {
        "format_valid": bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email_addr)),
        "has_domain": "@" in email_addr,
        "no_spaces": " " not in email_addr,
        "length_ok": len(email_addr) <= 254,
        "local_part": email_addr.split("@")[0] if "@" in email_addr else "",
        "domain": email_addr.split("@")[1] if "@" in email_addr else "",
    }

    # Check for disposable domains
    disposable = ["mailinator.com", "guerrillamail.com", "10minutemail.com", "tempmail.com"]
    domain = email_addr.split("@")[-1].lower() if "@" in email_addr else ""
    checks["disposable_domain"] = domain in disposable

    return [TextContent(type="text", text=json.dumps(checks, indent=2))]

@server.tool()
async def compose_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    body_type: str = "plain",
) -> list[TextContent]:
    """Compose an email and return it as a formatted string. Use send_email to actually send.

    Args:
        to: Recipient email address(es), comma-separated
        subject: Email subject line
        body: Email body content (plain text or HTML)
        cc: CC recipients, comma-separated
        bcc: BCC recipients, comma-separated
        body_type: "plain" or "html"
    """
    # Validate recipients
    invalid = []
    for addr in to.split(","):
        addr = addr.strip()
        if addr and not _validate_email(addr):
            invalid.append(addr)
    if invalid:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Invalid email(s): {', '.join(invalid)}"}, indent=2))]

    msg = MIMEMultipart()
    msg["From"] = os.environ.get("SMTP_USER", "user@example.com")
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    if cc:
        msg["Cc"] = cc

    msg.attach(MIMEText(body, body_type if body_type == "html" else "plain"))

    # Return the composed email for preview
    preview = {
        "from": msg["From"],
        "to": to,
        "cc": cc or None,
        "bcc": bcc or None,
        "subject": subject,
        "body_type": body_type,
        "body_preview": body[:500] + ("..." if len(body) > 500 else ""),
        "total_size_chars": len(body),
        "raw_message": msg.as_string()[:2000] + ("..." if len(msg.as_string()) > 2000 else ""),
    }
    return [TextContent(type="text", text=json.dumps(preview, indent=2))]

@server.tool()
async def send_email(
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    bcc: str = "",
    body_type: str = "plain",
    dry_run: bool = True,
) -> list[TextContent]:
    """Send an email via SMTP.

    Args:
        to: Recipient email address(es), comma-separated
        subject: Email subject line
        body: Email body content
        cc: CC recipients, comma-separated
        bcc: BCC recipients, comma-separated
        body_type: "plain" or "html"
        dry_run: If True, compose without sending (preview only). Set to False to actually send.
    """
    smtp_host = os.environ.get("SMTP_HOST", "")
    if not smtp_host and not dry_run:
        return [TextContent(type="text",
            text=json.dumps({"error": "SMTP not configured. Set SMTP_HOST env var."}, indent=2))]

    # Compose
    msg = MIMEMultipart()
    msg["From"] = os.environ.get("SMTP_USER", "user@example.com")
    msg["To"] = to
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    if cc:
        msg["Cc"] = cc

    msg.attach(MIMEText(body, body_type if body_type == "html" else "plain"))

    if dry_run:
        return [TextContent(type="text", text=json.dumps({
            "status": "dry_run",
            "message": "Email composed but not sent. Set dry_run=False to send.",
            "to": to,
            "subject": subject,
        }, indent=2))]

    # Send
    try:
        smtp_port = int(os.environ.get("SMTP_PORT", "587"))
        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")

        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.starttls()
            if smtp_user and smtp_pass:
                server.login(smtp_user, smtp_pass)
            recipients = [a.strip() for a in to.split(",") if a.strip()]
            if cc:
                recipients += [a.strip() for a in cc.split(",") if a.strip()]
            if bcc:
                recipients += [a.strip() for a in bcc.split(",") if a.strip()]
            server.sendmail(msg["From"], recipients, msg.as_string())

        return [TextContent(type="text", text=json.dumps({
            "status": "sent",
            "to": to,
            "subject": subject,
            "timestamp": datetime.now().isoformat(),
        }, indent=2))]
    except Exception as e:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Failed to send: {e}"}, indent=2))]

@server.tool()
async def create_template(
    name: str,
    subject_template: str,
    body_template: str,
    description: str = "",
) -> list[TextContent]:
    """Create a reusable email template with placeholders: {{name}}, {{date}}, etc.

    Args:
        name: Template name (unique identifier)
        subject_template: Subject line template (e.g. "Hello {{name}}, your order {{order_id}} is ready")
        body_template: Body template with placeholders
        description: Description of when to use this template
    """
    _templates[name] = {
        "subject": subject_template,
        "body": body_template,
        "description": description,
        "created_at": datetime.now().isoformat(),
        "placeholders": re.findall(r"\{\{(\w+)\}\}", subject_template + body_template),
    }
    _save_templates()

    return [TextContent(type="text", text=json.dumps({
        "created": name,
        "placeholders_detected": _templates[name]["placeholders"],
    }, indent=2))]

@server.tool()
async def render_template(
    template_name: str,
    values: str = "{}",
) -> list[TextContent]:
    """Fill an email template with values and preview the result.

    Args:
        template_name: Name of the template to use
        values: JSON object mapping placeholder names to values.
                e.g. '{"name": "Alice", "order_id": "ORD-1234"}'
    """
    if template_name not in _templates:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Template not found: {template_name}. Available: {list(_templates.keys())}"}, indent=2))]

    tpl = _templates[template_name]
    vals = json.loads(values)

    subject = tpl["subject"]
    body = tpl["body"]
    for key, val in vals.items():
        subject = subject.replace(f"{{{{{key}}}}}", str(val))
        body = body.replace(f"{{{{{key}}}}}", str(val))

    return [TextContent(type="text", text=json.dumps({
        "template": template_name,
        "rendered_subject": subject,
        "rendered_body": body,
        "unfilled_placeholders": re.findall(r"\{\{(\w+)\}\}", subject + body),
    }, indent=2))]

@server.tool()
async def list_templates() -> list[TextContent]:
    """List all saved email templates."""
    result = []
    for name, tpl in _templates.items():
        result.append({
            "name": name,
            "description": tpl.get("description", ""),
            "placeholders": tpl.get("placeholders", []),
            "created_at": tpl.get("created_at"),
        })
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("email://templates")
async def get_templates() -> str:
    return json.dumps(_templates, indent=2)

@server.resource("email://config")
async def get_config() -> str:
    return json.dumps({
        "smtp_configured": bool(os.environ.get("SMTP_HOST")),
        "smtp_host": os.environ.get("SMTP_HOST", "<not set>"),
        "smtp_user": os.environ.get("SMTP_USER", "<not set>"),
        "templates_loaded": len(_templates),
    }, indent=2)

@server.resource("email://template/{name}")
async def get_template_resource(name: str) -> str:
    """Parameterized resource — get a specific template's details."""
    if name not in _templates:
        return json.dumps({"error": f"Template not found: {name}"})
    return json.dumps(_templates[name], indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="compose-campaign",
    description="Design and compose an email campaign from a description",
    arguments={
        "campaign_goal": {
            "type": "string",
            "description": "What the email campaign should achieve",
            "required": True,
        },
        "audience": {
            "type": "string",
            "description": "Who the recipients are, e.g. 'existing customers', 'new signups'",
            "required": True,
        },
        "tone": {
            "type": "string",
            "enum": ["professional", "friendly", "urgent", "celebratory", "apologetic"],
            "description": "The tone of the email",
            "required": False,
        },
    },
)
async def compose_campaign_prompt(campaign_goal: str, audience: str, tone: str = "professional") -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Design an email campaign.

Goal: {campaign_goal}
Audience: {audience}
Tone: {tone}

Steps:
1. First, create a reusable template with create_template — use placeholders like {{{{recipient_name}}}}, {{{{date}}}}, and any others relevant to the campaign
2. Use render_template to preview the email with sample values
3. Use validate_email_address to verify any seed addresses
4. Compose the final email with compose_email (dry_run mode — this is just a design exercise)
5. List all templates with list_templates

The template should include:
- A compelling subject line
- Personalization with placeholders
- Clear call to action
- Unsubscribe note in footer

After composing, explain:
- Why you chose this structure
- A/B testing ideas (what variants to test)
- Optimal send time recommendations""",
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
