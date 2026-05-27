#!/usr/bin/env python3
"""
MCP Search Aggregator Server — demonstrates multi-source parallel requests,
result merging, deduplication, and ranked aggregation.

Install: pip install mcp httpx
Configure in .claude/settings.json:
{
  "mcpServers": {
    "search-agg": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/search_aggregator_server.py"],
      "env": {
        "BRAVE_API_KEY": "your-brave-key",
        "SERPAPI_KEY": "your-serpapi-key"
      }
    }
  }
}
"""

import asyncio
import hashlib
import json
import os
import re
import time
from collections import OrderedDict
from typing import Any
from urllib.parse import quote_plus

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("search-agg")

# ---------------------------------------------------------------------------
# In-memory result cache
# ---------------------------------------------------------------------------
_cache: OrderedDict = OrderedDict()
MAX_CACHE_SIZE = 100

def _cache_key(query: str, sources: tuple) -> str:
    return hashlib.md5(f"{query}:{','.join(sorted(sources))}".encode()).hexdigest()

# ---------------------------------------------------------------------------
# Search backends
# ---------------------------------------------------------------------------

async def _search_duckduckgo(query: str, count: int = 10) -> list[dict]:
    """Search DuckDuckGo (no API key needed). Uses their HTML endpoint."""
    import httpx
    results = []
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (compatible; MCPBot/1.0)"},
            )
            # Parse the HTML results (simple regex-based extraction)
            html = r.text
            # Extract result blocks
            for match in re.finditer(
                r'<a rel="nofollow" class="result__a" href="([^"]+)".*?>(.*?)</a>.*?<a class="result__snippet".*?>(.*?)</a>',
                html, re.DOTALL,
            ):
                url, title, snippet = match.groups()
                results.append({
                    "title": re.sub(r"<[^>]+>", "", title).strip(),
                    "url": url.strip(),
                    "snippet": re.sub(r"<[^>]+>", "", snippet).strip()[:300],
                    "source": "duckduckgo",
                })
            return results[:count]
    except Exception as e:
        return [{"error": f"DuckDuckGo search failed: {e}", "source": "duckduckgo"}]

async def _search_brave(query: str, count: int = 10) -> list[dict]:
    """Search using Brave Search API."""
    api_key = os.environ.get("BRAVE_API_KEY", "")
    if not api_key:
        return []
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": query, "count": min(count, 20)},
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": api_key,
                },
            )
            data = r.json()
            results = []
            for item in data.get("web", {}).get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "snippet": item.get("description", "")[:300],
                    "source": "brave",
                })
            return results[:count]
    except Exception as e:
        return [{"error": f"Brave search failed: {e}", "source": "brave"}]

async def _search_serpapi(query: str, count: int = 10) -> list[dict]:
    """Search using SerpAPI (Google results)."""
    api_key = os.environ.get("SERPAPI_KEY", "")
    if not api_key:
        return []
    import httpx
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                "https://serpapi.com/search",
                params={"q": query, "api_key": api_key, "num": min(count, 20)},
            )
            data = r.json()
            results = []
            for item in data.get("organic_results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "snippet": item.get("snippet", "")[:300],
                    "source": "serpapi",
                })
            return results[:count]
    except Exception as e:
        return [{"error": f"SerpAPI search failed: {e}", "source": "serpapi"}]

# All available backends
BACKENDS = {
    "duckduckgo": _search_duckduckgo,
    "brave": _search_brave,
    "serpapi": _search_serpapi,
}

# ---------------------------------------------------------------------------
# Result processing
# ---------------------------------------------------------------------------

def _deduplicate(results: list[dict]) -> list[dict]:
    """Remove duplicate URLs, keeping the first occurrence (highest ranked)."""
    seen: set[str] = set()
    unique = []
    for r in results:
        url = r.get("url", "")
        normalized = url.rstrip("/").lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(r)
    return unique

def _interleave(results_per_source: list[list[dict]]) -> list[dict]:
    """Round-robin interleave results from multiple sources for diversity."""
    merged = []
    max_len = max(len(r) for r in results_per_source)
    for i in range(max_len):
        for source_results in results_per_source:
            if i < len(source_results):
                merged.append(source_results[i])
    return merged

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def multi_search(
    query: str,
    sources: str = "duckduckgo",
    count: int = 10,
    merge_strategy: str = "interleave",
) -> list[TextContent]:
    """Search across multiple search engines in parallel and merge results.

    Args:
        query: The search query
        sources: Comma-separated list — "duckduckgo", "brave", "serpapi"
        count: Results per source (max 20)
        merge_strategy: "interleave" (round-robin), "ranked" (source order), or "dedup-only"
    """
    source_list = [s.strip() for s in sources.split(",") if s.strip() in BACKENDS]
    if not source_list:
        source_list = ["duckduckgo"]

    count = min(count, 20)

    # Check cache
    cache_key = _cache_key(query, tuple(source_list))
    if cache_key in _cache:
        return [TextContent(type="text", text=json.dumps(_cache[cache_key], indent=2))]

    # Parallel search
    tasks = [BACKENDS[src](query, count) for src in source_list]
    all_results = await asyncio.gather(*tasks)

    # Apply merge strategy
    if merge_strategy == "interleave":
        merged = _interleave(all_results)
    elif merge_strategy == "ranked":
        merged = []
        for r in all_results:
            merged.extend(r)
    else:
        merged = []
        for r in all_results:
            merged.extend(r)

    deduped = _deduplicate(merged)

    result = {
        "query": query,
        "sources_queried": source_list,
        "total_raw_results": sum(len(r) for r in all_results),
        "unique_results": len(deduped),
        "merge_strategy": merge_strategy,
        "results": deduped[:count],
        "errors": [r for batch in all_results for r in batch if "error" in r],
    }

    # Cache it
    if len(_cache) >= MAX_CACHE_SIZE:
        _cache.popitem(last=False)
    _cache[cache_key] = result

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def fetch_page_content(url: str, max_length: int = 5000) -> list[TextContent]:
    """Fetch and extract readable text content from a URL.

    Args:
        url: The URL to fetch
        max_length: Maximum characters to return. Defaults to 5000.
    """
    import httpx
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            r = await client.get(
                url,
                headers={"User-Agent": "Mozilla/5.0 (compatible; MCPBot/1.0)"},
            )
            r.raise_for_status()
            html = r.text

            # Simple HTML-to-text extraction
            # Strip scripts and styles
            html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
            html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
            # Strip tags
            text = re.sub(r"<[^>]+>", " ", html)
            # Normalize whitespace
            text = re.sub(r"\s+", " ", text).strip()
            # Truncate
            if len(text) > max_length:
                text = text[:max_length] + f"\n\n[... truncated at {max_length} chars]"

            return [TextContent(type="text", text=text)]
    except Exception as e:
        return [TextContent(type="text",
            text=json.dumps({"error": f"Failed to fetch {url}: {e}"}, indent=2))]

@server.tool()
async def extract_links(html: str, base_url: str = "") -> list[TextContent]:
    """Extract all links from HTML content.

    Args:
        html: Raw HTML string
        base_url: Base URL for resolving relative links
    """
    links = []
    for match in re.finditer(r'<a\s+[^>]*href=["\']([^"\']+)["\']([^>]*)>(.*?)</a>', html, re.DOTALL | re.IGNORECASE):
        href, attrs, text = match.groups()
        text = re.sub(r"<[^>]+>", "", text).strip()
        # Resolve relative URLs
        if base_url and not href.startswith(("http://", "https://", "#", "mailto:", "tel:")):
            from urllib.parse import urljoin
            href = urljoin(base_url, href)
        links.append({"url": href, "text": text[:200] if text else ""})

    return [TextContent(type="text", text=json.dumps({
        "total_links": len(links),
        "links": links[:200],
    }, indent=2))]

@server.tool()
async def summarize_results(
    query: str,
    sources: str = "duckduckgo",
    max_results: int = 5,
) -> list[TextContent]:
    """Search and create a synthesized summary from top results.

    Args:
        query: The search query
        sources: Comma-separated search sources
        max_results: Number of top results to summarize
    """
    source_list = [s.strip() for s in sources.split(",") if s.strip() in BACKENDS]
    if not source_list:
        source_list = ["duckduckgo"]

    tasks = [BACKENDS[src](query, max_results) for src in source_list]
    all_results = await asyncio.gather(*tasks)
    merged = []
    for r in all_results:
        merged.extend(r)
    deduped = _deduplicate(merged)[:max_results]

    return [TextContent(type="text", text=json.dumps({
        "query": query,
        "top_results": deduped,
        "instruction": "Use the above search results to provide a comprehensive, "
                       "synthesized answer to the query. Cite specific sources by URL.",
    }, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("search://stats")
async def search_stats() -> str:
    return json.dumps({
        "cached_queries": len(_cache),
        "available_backends": list(BACKENDS.keys()),
        "active_backends": [
            name for name in BACKENDS
            if name == "duckduckgo" or os.environ.get(f"{name.upper()}_API_KEY")
        ],
    }, indent=2)

# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
