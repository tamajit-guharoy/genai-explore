#!/usr/bin/env python3
"""
MCP Weather Server — demonstrates external API integration, response caching,
structured error handling, and multiple coordinated tools.

Install: pip install mcp httpx
Configure in .claude/settings.json:
{
  "mcpServers": {
    "weather": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/weather_server.py"],
      "env": { "OPENWEATHERMAP_API_KEY": "your-key-here" }
    }
  }
}
"""

import asyncio
import json
import os
import time
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server, NotificationOptions
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent, Resource, ResourceTemplate

# ---------------------------------------------------------------------------
# In-memory cache (TTL-based). Demonstrates caching best practices for MCP tools.
# ---------------------------------------------------------------------------
_cache: dict[str, tuple[float, Any]] = {}
CACHE_TTL = 300  # seconds

def cache_get(key: str) -> Any | None:
    entry = _cache.get(key)
    if entry is None:
        return None
    ts, val = entry
    if time.time() - ts > CACHE_TTL:
        del _cache[key]
        return None
    return val

def cache_set(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)

# ---------------------------------------------------------------------------
# Server setup
# ---------------------------------------------------------------------------
server = Server("weather")

# ---------------------------------------------------------------------------
# Helper: call OpenWeatherMap API
# ---------------------------------------------------------------------------
async def _owm_request(endpoint: str, params: dict[str, str]) -> dict:
    api_key = os.environ.get("OPENWEATHERMAP_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENWEATHERMAP_API_KEY env var not set")
    params["appid"] = api_key

    import httpx
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(
            f"https://api.openweathermap.org/data/2.5/{endpoint}",
            params=params,
        )
        if r.status_code == 404:
            raise ValueError(f"Location not found: {params}")
        r.raise_for_status()
        return r.json()

def _kelvin_to_celsius(k: float) -> float:
    return round(k - 273.15, 1)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def get_current_weather(
    city: str,
    units: str = "metric",
) -> list[TextContent]:
    """Get current weather conditions for a city by name.

    Args:
        city: City name (e.g. "London", "Tokyo", "San Francisco")
        units: "metric" (Celsius), "imperial" (Fahrenheit), or "kelvin"
    """
    cache_key = f"current:{city}:{units}"
    cached = cache_get(cache_key)
    if cached:
        return [TextContent(type="text", text=json.dumps(cached, indent=2))]

    data = await _owm_request("weather", {"q": city, "units": units})
    result = {
        "city": data["name"],
        "country": data.get("sys", {}).get("country", ""),
        "temperature": data["main"]["temp"],
        "feels_like": data["main"]["feels_like"],
        "humidity_pct": data["main"]["humidity"],
        "pressure_hpa": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "conditions": data["weather"][0]["description"],
        "icon_code": data["weather"][0]["icon"],
        "visibility_m": data.get("visibility", 0),
    }
    cache_set(cache_key, result)
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def get_forecast(city: str, days: int = 5) -> list[TextContent]:
    """Get multi-day weather forecast for a city.

    Args:
        city: City name
        days: Number of days to forecast (1-5). Defaults to 5.
    """
    if days < 1 or days > 5:
        raise ValueError("days must be between 1 and 5")

    cache_key = f"forecast:{city}:{days}"
    cached = cache_get(cache_key)
    if cached:
        return [TextContent(type="text", text=json.dumps(cached, indent=2))]

    data = await _owm_request("forecast", {"q": city, "units": "metric"})
    # Group 3-hourly entries by day
    by_day: dict[str, list[dict]] = {}
    for entry in data["list"]:
        day = entry["dt_txt"][:10]
        by_day.setdefault(day, []).append(entry)

    forecast = {}
    for i, (day, entries) in enumerate(by_day.items()):
        if i >= days:
            break
        temps = [e["main"]["temp"] for e in entries]
        humidity = [e["main"]["humidity"] for e in entries]
        conditions = [e["weather"][0]["description"] for e in entries]
        forecast[day] = {
            "high_c": round(max(temps), 1),
            "low_c": round(min(temps), 1),
            "avg_humidity": round(sum(humidity) / len(humidity)),
            "dominant_condition": max(set(conditions), key=conditions.count),
            "data_points": len(entries),
        }

    cache_set(cache_key, forecast)
    return [TextContent(type="text", text=json.dumps(forecast, indent=2))]

@server.tool()
async def get_air_pollution(city: str) -> list[TextContent]:
    """Get current air quality index for a city.

    Args:
        city: City name
    """
    # First geocode the city to get lat/lon
    geo_data = await _owm_request("weather", {"q": city, "units": "metric"})
    lat = geo_data["coord"]["lat"]
    lon = geo_data["coord"]["lon"]

    aqi_data = await _owm_request("air_pollution", {"lat": str(lat), "lon": str(lon)})
    aqi = aqi_data["list"][0]
    components = aqi["components"]

    aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
    result = {
        "city": city,
        "aqi": aqi["main"]["aqi"],
        "aqi_label": aqi_labels.get(aqi["main"]["aqi"], "Unknown"),
        "components": {
            "co_μg/m³": components["co"],
            "no_μg/m³": components["no"],
            "no2_μg/m³": components["no2"],
            "o3_μg/m³": components["o3"],
            "so2_μg/m³": components["so2"],
            "pm2_5_μg/m³": components["pm2_5"],
            "pm10_μg/m³": components["pm10"],
            "nh3_μg/m³": components["nh3"],
        },
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def compare_cities(city_a: str, city_b: str) -> list[TextContent]:
    """Compare current weather between two cities side by side.

    Args:
        city_a: First city name
        city_b: Second city name
    """
    results = await asyncio.gather(
        _owm_request("weather", {"q": city_a, "units": "metric"}),
        _owm_request("weather", {"q": city_b, "units": "metric"}),
    )
    comparison = {}
    for label, data in [(city_a, results[0]), (city_b, results[1])]:
        comparison[label] = {
            "temp_c": data["main"]["temp"],
            "humidity_pct": data["main"]["humidity"],
            "wind_ms": data["wind"]["speed"],
            "conditions": data["weather"][0]["description"],
        }
    return [TextContent(type="text", text=json.dumps(comparison, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("weather://cache-stats")
async def cache_stats() -> str:
    """Return current cache statistics."""
    entries = []
    for key, (ts, val) in _cache.items():
        entries.append({
            "key": key,
            "age_seconds": round(time.time() - ts, 1),
            "expires_in_seconds": round(CACHE_TTL - (time.time() - ts), 1),
        })
    return json.dumps({
        "total_entries": len(_cache),
        "ttl_seconds": CACHE_TTL,
        "entries": entries,
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts — reusable templates that appear as slash commands
# ---------------------------------------------------------------------------

@server.prompt(
    name="travel-advisory",
    description="Get a full travel weather advisory comparing multiple destinations",
    arguments={
        "destinations": {
            "type": "string",
            "description": "Comma-separated city names, e.g. 'Tokyo, London, Sydney'",
            "required": True,
        },
        "travel_dates": {
            "type": "string",
            "description": "Travel date range, e.g. '2026-06-15 to 2026-06-30'",
            "required": False,
        },
    },
)
async def travel_advisory_prompt(destinations: str, travel_dates: str = "") -> dict:
    cities = [c.strip() for c in destinations.split(",")]
    date_hint = f"\nTravel dates: {travel_dates}" if travel_dates else ""
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""You are a travel weather advisor. Analyze and compare weather for: {', '.join(cities)}.{date_hint}

For each city, use the get_current_weather, get_forecast, and get_air_pollution tools to gather:
1. Current conditions (temperature, humidity, wind)
2. 5-day forecast trends
3. Air quality index

Then provide:
1. A comparison table of all cities
2. A "best to visit now" ranking with reasoning
3. Packing recommendations for each city
4. Air quality warnings if AQI is 3 or above

Format as a clear, actionable travel advisory.""",
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
