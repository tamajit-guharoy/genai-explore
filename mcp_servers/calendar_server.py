#!/usr/bin/env python3
"""
MCP Calendar Server — demonstrates date/time operations, scheduling,
recurring event calculation, timezone conversion, and holiday detection.

Install: pip install mcp python-dateutil holidays
Configure in .claude/settings.json:
{
  "mcpServers": {
    "calendar": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/calendar_server.py"]
    }
  }
}
"""

import asyncio
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("calendar")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(d: str) -> date:
    """Parse a date string in various formats."""
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y%m%d", "%d-%b-%Y", "%B %d, %Y"):
        try:
            return datetime.strptime(d, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: {d}. Use YYYY-MM-DD format.")

def _parse_datetime(dt: str) -> datetime:
    """Parse a datetime string in various formats."""
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(dt, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse datetime: {dt}")

def _ordinal(n: int) -> str:
    if 10 <= n % 100 <= 20:
        return f"{n}th"
    return f"{n}{{1:'st',2:'nd',3:'rd'}.get(n%10,'th')}"

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def date_calc(
    date_str: str,
    operation: str,
    value: int = 0,
) -> list[TextContent]:
    """Perform date arithmetic: add/subtract days, weeks, months, or years.

    Args:
        date_str: Date in YYYY-MM-DD format
        operation: "add_days", "sub_days", "add_weeks", "add_months", "add_years",
                   "start_of_week", "start_of_month", "end_of_month", "start_of_year"
        value: Number of units (for add/subtract operations)
    """
    from dateutil.relativedelta import relativedelta

    d = _parse_date(date_str)
    original = d.isoformat()

    if operation == "add_days":
        d = d + timedelta(days=value)
    elif operation == "sub_days":
        d = d - timedelta(days=value)
    elif operation == "add_weeks":
        d = d + timedelta(weeks=value)
    elif operation == "add_months":
        d = d + relativedelta(months=value)
    elif operation == "add_years":
        d = d + relativedelta(years=value)
    elif operation == "start_of_week":
        d = d - timedelta(days=d.weekday())
    elif operation == "start_of_month":
        d = d.replace(day=1)
    elif operation == "end_of_month":
        d = d.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
    elif operation == "start_of_year":
        d = d.replace(month=1, day=1)
    else:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Unknown operation: {operation}"}, indent=2))]

    return [TextContent(type="text", text=json.dumps({
        "original": original,
        "operation": operation,
        "value": value,
        "result": d.isoformat(),
        "day_of_week": d.strftime("%A"),
        "day_of_year": d.timetuple().tm_yday,
        "week_number": d.isocalendar()[1],
        "days_from_today": (d - date.today()).days,
    }, indent=2))]

@server.tool()
async def date_diff(
    date_a: str,
    date_b: str,
    unit: str = "days",
) -> list[TextContent]:
    """Calculate the difference between two dates.

    Args:
        date_a: First date (YYYY-MM-DD)
        date_b: Second date (YYYY-MM-DD)
        unit: "days", "weeks", "months", "years", or "all"
    """
    from dateutil.relativedelta import relativedelta

    a = _parse_date(date_a)
    b = _parse_date(date_b)

    delta_days = (b - a).days
    delta = relativedelta(b, a)

    result: dict[str, Any] = {
        "date_a": date_a,
        "date_b": date_b,
    }

    if unit in ("days", "all"):
        result["days"] = delta_days
        result["weeks"] = round(delta_days / 7, 1)
    if unit in ("months", "all"):
        result["months"] = delta.months + delta.years * 12
    if unit in ("years", "all"):
        result["years"] = round(delta_days / 365.25, 2)
    if unit == "all":
        result["human"] = f"{delta.years}y {delta.months}m {delta.days}d"

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def recurring_events(
    start_date: str,
    rule: str,
    count: int = 10,
    end_date: str = "",
) -> list[TextContent]:
    """Generate dates for recurring events using simple rules.

    Args:
        start_date: First occurrence (YYYY-MM-DD)
        rule: Recurrence rule —
          "daily", "weekly", "biweekly", "monthly", "quarterly", "yearly",
          "weekdays" (Mon-Fri), "weekly:mon" (Monday), "monthly:15" (15th of month),
          "monthly:last" (last day), "monthly:2nd_tue" (2nd Tuesday)
        count: Max number of occurrences to return
        end_date: Stop after this date (optional, YYYY-MM-DD)
    """
    from dateutil.relativedelta import relativedelta, MO, TU, WE, TH, FR, SA, SU

    d = _parse_date(start_date)
    end = _parse_date(end_date) if end_date else date(2099, 12, 31)

    weekday_map = {"mon": MO, "tue": TU, "wed": WE, "thu": TH, "fri": FR, "sat": SA, "sun": SU}

    occurrences = []
    current = d

    while len(occurrences) < count and current <= end:
        occurrences.append(current.isoformat())

        if rule == "daily":
            current = current + timedelta(days=1)
        elif rule == "weekly":
            current = current + timedelta(weeks=1)
        elif rule == "biweekly":
            current = current + timedelta(weeks=2)
        elif rule == "monthly":
            current = current + relativedelta(months=1)
        elif rule == "quarterly":
            current = current + relativedelta(months=3)
        elif rule == "yearly":
            current = current + relativedelta(years=1)
        elif rule == "weekdays":
            current = current + timedelta(days=1)
            while current.weekday() >= 5:  # Skip weekends
                current = current + timedelta(days=1)
        elif rule.startswith("weekly:"):
            target_day = rule.split(":")[1].lower()
            target_wkday = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}[target_day]
            days_ahead = target_wkday - current.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            current = current + timedelta(days=days_ahead)
        elif rule.startswith("monthly:"):
            spec = rule.split(":")[1]
            if spec == "last":
                current = current.replace(day=1) + relativedelta(months=1) - timedelta(days=1)
            elif spec.isdigit():
                day_num = int(spec)
                current = current.replace(day=1) + relativedelta(months=1)
                max_day = (current - timedelta(days=1)).day
                current = current.replace(day=min(day_num, max_day))
            elif "_" in spec:
                # e.g. "2nd_tue"
                parts = spec.split("_")
                ordinal_str = parts[0].rstrip("ndrdthst")
                wkday = parts[1][:3].lower()
                n = {"1": 1, "2": 2, "3": 3, "4": 4, "5": 5}.get(ordinal_str, 1)
                wd = weekday_map.get(wkday, MO)
                current = current.replace(day=1) + relativedelta(months=1, weekday=wd(n))
            await asyncio.sleep(0)  # Yield control
        else:
            return [TextContent(type="text",
                text=json.dumps({"error": f"Unknown rule: {rule}"}, indent=2))]

    return [TextContent(type="text", text=json.dumps({
        "rule": rule,
        "start_date": start_date,
        "count": count,
        "occurrences": occurrences,
    }, indent=2))]

@server.tool()
async def timezone_convert(
    datetime_str: str,
    from_tz: str = "UTC",
    to_tz: str = "America/New_York",
) -> list[TextContent]:
    """Convert a datetime between timezones.

    Args:
        datetime_str: ISO datetime string (e.g. "2026-05-26T14:30:00")
        from_tz: Source timezone name (e.g. "UTC", "America/Los_Angeles", "Europe/London")
        to_tz: Target timezone name
    """
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        return [TextContent(type="text",
            text=json.dumps({"error": "zoneinfo requires Python 3.9+"}, indent=2))]

    try:
        from_zone = ZoneInfo(from_tz)
        to_zone = ZoneInfo(to_tz)

        dt = _parse_datetime(datetime_str)
        dt = dt.replace(tzinfo=from_zone)
        converted = dt.astimezone(to_zone)

        return [TextContent(type="text", text=json.dumps({
            "original": datetime_str,
            "from_tz": from_tz,
            "to_tz": to_tz,
            "converted": converted.strftime("%Y-%m-%dT%H:%M:%S %Z"),
            "utc_offset": str(converted.utcoffset()),
            "is_dst": bool(converted.dst()),
        }, indent=2, default=str))]
    except Exception as e:
        return [TextContent(type="text",
            text=json.dumps({"error": str(e)}, indent=2))]

@server.tool()
async def list_timezones(region: str = "") -> list[TextContent]:
    """List available timezone names, optionally filtered by region.

    Args:
        region: Filter by region prefix — "America", "Europe", "Asia", "Pacific", "UTC"
    """
    try:
        from zoneinfo import available_timezones
        zones = sorted(available_timezones())
        if region:
            zones = [z for z in zones if z.startswith(region)]
        return [TextContent(type="text", text=json.dumps({
            "count": len(zones),
            "timezones": zones[:500],
        }, indent=2))]
    except ImportError:
        # Fallback to common timezones
        common = [
            "UTC", "US/Eastern", "US/Central", "US/Mountain", "US/Pacific",
            "America/New_York", "America/Chicago", "America/Denver", "America/Los_Angeles",
            "Europe/London", "Europe/Paris", "Europe/Berlin", "Europe/Moscow",
            "Asia/Tokyo", "Asia/Shanghai", "Asia/Kolkata", "Asia/Dubai",
            "Australia/Sydney", "Pacific/Auckland",
        ]
        if region:
            common = [z for z in common if z.lower().startswith(region.lower())]
        return [TextContent(type="text", text=json.dumps({"count": len(common), "timezones": common}, indent=2))]

@server.tool()
async def holidays_lookup(
    country: str = "US",
    year: int = 2026,
) -> list[TextContent]:
    """List public holidays for a country and year.

    Args:
        country: ISO 3166-1 alpha-2 country code (e.g. "US", "GB", "DE", "IN", "JP", "AU")
        year: Year to look up
    """
    try:
        import holidays
        country_holidays = holidays.country_holidays(country, years=year)
        result = []
        for d, name in sorted(country_holidays.items()):
            result.append({
                "date": d.isoformat(),
                "name": name,
                "day_of_week": d.strftime("%A"),
            })
        return [TextContent(type="text", text=json.dumps({
            "country": country,
            "year": year,
            "total_holidays": len(result),
            "holidays": result,
        }, indent=2))]
    except ImportError:
        return [TextContent(type="text",
            text=json.dumps({
                "error": "Package 'holidays' not installed. Run: pip install holidays",
                "manual": "Cannot look up holidays without the package.",
            }, indent=2))]
    except Exception as e:
        return [TextContent(type="text",
            text=json.dumps({"error": str(e)}, indent=2))]

@server.tool()
async def calendar_month(year: int, month: int) -> list[TextContent]:
    """Generate a formatted calendar month view.

    Args:
        year: Year (e.g. 2026)
        month: Month (1-12)
    """
    import calendar

    cal = calendar.TextCalendar(calendar.SUNDAY)
    month_str = cal.formatmonth(year, month)

    # Also generate a structured version
    weeks = cal.monthdayscalendar(year, month)
    today = date.today()

    structured = []
    for week in weeks:
        week_data = []
        for day_num in week:
            if day_num == 0:
                week_data.append(None)
            else:
                d = date(year, month, day_num)
                week_data.append({
                    "day": day_num,
                    "date": d.isoformat(),
                    "weekday": d.strftime("%A")[:3],
                    "is_today": d == today,
                    "is_weekend": d.weekday() >= 5,
                })
        structured.append(week_data)

    return [TextContent(type="text", text=json.dumps({
        "year": year,
        "month": month,
        "month_name": calendar.month_name[month],
        "text_calendar": month_str,
        "structured_weeks": structured,
    }, indent=2))]

@server.tool()
async def countdown(target_date: str, label: str = "") -> list[TextContent]:
    """Calculate a countdown to a target date, returning days/hours/minutes.

    Args:
        target_date: Target date (YYYY-MM-DD) or datetime (YYYY-MM-DDTHH:MM:SS)
        label: Label for the countdown (e.g. "Project Deadline")
    """
    try:
        target = _parse_datetime(target_date)
    except ValueError:
        target = datetime.combine(_parse_date(target_date), datetime.min.time())

    now = datetime.now()
    delta = target - now
    total_seconds = int(delta.total_seconds())

    if total_seconds < 0:
        return [TextContent(type="text", text=json.dumps({
            "label": label,
            "target": target_date,
            "status": "passed",
            "elapsed_days": abs(delta.days),
        }, indent=2))]

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return [TextContent(type="text", text=json.dumps({
        "label": label,
        "target": target_date,
        "status": "upcoming",
        "total_days": round(total_seconds / 86400, 1),
        "countdown": f"{days}d {hours}h {minutes}m {seconds}s",
        "breakdown": {"days": days, "hours": hours, "minutes": minutes, "seconds": seconds},
        "target_weekday": target.strftime("%A"),
    }, indent=2))]

@server.tool()
async def week_number(date_str: str = "today") -> list[TextContent]:
    """Get the ISO week number and related info for a date.

    Args:
        date_str: Date in YYYY-MM-DD format, or "today"
    """
    if date_str == "today":
        d = date.today()
    else:
        d = _parse_date(date_str)

    iso = d.isocalendar()
    return [TextContent(type="text", text=json.dumps({
        "date": d.isoformat(),
        "iso_year": iso[0],
        "iso_week": iso[1],
        "iso_weekday": iso[2],
        "weekday_name": d.strftime("%A"),
        "quarter": (d.month - 1) // 3 + 1,
        "ordinal_date": _ordinal(d.day) + " " + d.strftime("%B %Y"),
        "days_in_month": (date(d.year, d.month % 12 + 1, 1) - timedelta(days=1)).day
                         if d.month < 12 else 31,
    }, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("calendar://today")
async def today_info() -> str:
    today = date.today()
    return json.dumps({
        "date": today.isoformat(),
        "iso": {"year": today.isocalendar()[0], "week": today.isocalendar()[1], "day": today.isocalendar()[2]},
        "weekday": today.strftime("%A"),
        "year_progress_pct": round(today.timetuple().tm_yday / 365 * 100, 1),
    }, indent=2)

@server.resource("calendar://month/{year}/{month}")
async def get_month_resource(year: str, month: str) -> str:
    """Parameterized resource — get a calendar month as a resource."""
    import calendar as cal
    y, m = int(year), int(month)
    return json.dumps({
        "year": y,
        "month": m,
        "name": cal.month_name[m],
        "weeks": cal.monthcalendar(y, m),
        "first_weekday": cal.month_name[cal.monthrange(y, m)[0] + 1],
        "num_days": cal.monthrange(y, m)[1],
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="schedule-meeting",
    description="Find optimal meeting times across timezones",
    arguments={
        "attendees": {
            "type": "string",
            "description": "Attendee timezones, e.g. 'America/New_York, Europe/London, Asia/Tokyo'",
            "required": True,
        },
        "meeting_duration_minutes": {
            "type": "number",
            "description": "How long the meeting should be (minutes)",
            "required": False,
        },
    },
)
async def schedule_meeting_prompt(attendees: str, meeting_duration_minutes: int = 30) -> dict:
    tzs = [t.strip() for t in attendees.split(",")]
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Find optimal meeting times for attendees in these timezones: {', '.join(tzs)}.

Meeting duration: {meeting_duration_minutes} minutes

Use the available tools to:
1. Convert current time to each timezone with timezone_convert
2. Suggest 3 time slots that work across all zones (during business hours 9am-5pm in each zone)
3. For each slot, show the local time in every attendee's timezone
4. Check if any slot falls on a weekend or public holiday (use holidays_lookup for each relevant country)
5. Calculate a countdown to each proposed slot with the countdown tool

Present as a clear, timezone-aware meeting proposal.""",
            },
        }],
    }

@server.prompt(
    name="event-planner",
    description="Plan a recurring event schedule",
    arguments={
        "event_name": {
            "type": "string",
            "description": "Name of the event",
            "required": True,
        },
        "cadence": {
            "type": "string",
            "enum": ["daily", "weekly", "biweekly", "monthly", "quarterly", "weekdays"],
            "description": "How often the event repeats",
            "required": False,
        },
    },
)
async def event_planner_prompt(event_name: str, cadence: str = "weekly") -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Plan a recurring event schedule for: "{event_name}" (cadence: {cadence}).

Use the calendar tools to:
1. Generate the next 12 occurrences using recurring_events with rule="{cadence}"
2. For each occurrence, show the day of week and week number (use week_number)
3. Count the days between now and the first occurrence
4. Check which occurrences fall on weekends
5. If this is a work event, suggest alternative dates for any weekend occurrences

Present as a clean schedule listing with dates, day names, and week numbers.""",
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
