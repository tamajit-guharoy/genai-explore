#!/usr/bin/env python3
"""
MCP Data ETL Server — demonstrates data transformation pipelines, schema validation,
multi-format support (JSON, CSV, XML, YAML, TOML), and streaming transformations.

Install: pip install mcp pyyaml
Configure in .claude/settings.json:
{
  "mcpServers": {
    "etl": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/data_etl_server.py"]
    }
  }
}
"""

import asyncio
import csv
import io
import json
import re
import statistics
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent

server = Server("etl")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_csv(text: str) -> list[dict]:
    reader = csv.DictReader(io.StringIO(text))
    return list(reader)

def _to_csv(rows: list[dict]) -> str:
    if not rows:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()

def _parse_xml(text: str) -> dict:
    import xml.etree.ElementTree as ET
    root = ET.fromstring(text)

    def _elem_to_dict(elem):
        result: dict[str, Any] = {}
        for child in elem:
            tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
            child_dict = _elem_to_dict(child)
            if tag in result:
                if not isinstance(result[tag], list):
                    result[tag] = [result[tag]]
                result[tag].append(child_dict)
            else:
                result[tag] = child_dict
        if elem.text and elem.text.strip():
            result["#text"] = elem.text.strip()
        if elem.attrib:
            result["@attrs"] = elem.attrib
        return result

    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag
    return {tag: _elem_to_dict(root)}

def _detect_format(text: str) -> str:
    text = text.strip()
    if text.startswith("{") or text.startswith("["):
        return "json"
    if text.startswith("<"):
        return "xml"
    if text.count(",") > 0 and text.count("\n") > 0:
        # Heuristic: looks like CSV
        return "csv"
    if ":" in text.split("\n")[0]:
        return "yaml"
    return "unknown"

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def convert(
    input_data: str,
    from_format: str = "auto",
    to_format: str = "json",
) -> list[TextContent]:
    """Convert data between formats: JSON, CSV, XML, YAML.

    Args:
        input_data: The input data as a string
        from_format: Input format — "auto", "json", "csv", "xml", "yaml"
        to_format: Output format — "json", "csv", "yaml", "xml"
    """
    if from_format == "auto":
        from_format = _detect_format(input_data)

    # Parse
    parsers = {
        "json": json.loads,
        "csv": _parse_csv,
        "yaml": lambda t: __import__("yaml").safe_load(t),
    }
    if from_format == "xml":
        parsed = _parse_xml(input_data)
    elif from_format in parsers:
        parsed = parsers[from_format](input_data)
    else:
        raise ValueError(f"Unsupported input format: {from_format}")

    # Serialize
    serializers = {
        "json": lambda d: json.dumps(d, indent=2, default=str),
        "csv": _to_csv,
        "yaml": lambda d: __import__("yaml").safe_dump(d, allow_unicode=True, sort_keys=False),
    }
    if to_format in serializers:
        result = serializers[to_format](parsed)
    else:
        raise ValueError(f"Unsupported output format: {to_format}")

    return [TextContent(type="text", text=result)]

@server.tool()
async def validate_schema(
    data: str,
    schema_json: str,
    data_format: str = "json",
) -> list[TextContent]:
    """Validate data against a JSON Schema definition.

    Args:
        data: The data string to validate
        schema_json: JSON Schema definition
        data_format: Format of the data — "json" or "yaml"
    """
    import jsonschema

    schema = json.loads(schema_json)
    if data_format == "yaml":
        import yaml
        instance = yaml.safe_load(data)
    else:
        instance = json.loads(data)

    errors = []
    for err in jsonschema.Draft202012Validator(schema).iter_errors(instance):
        errors.append({
            "path": ".".join(str(p) for p in err.absolute_path),
            "message": err.message,
            "schema_path": ".".join(str(p) for p in err.schema_path),
        })

    result = {
        "valid": len(errors) == 0,
        "error_count": len(errors),
        "errors": errors,
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def filter_transform(
    data: str,
    jmespath_query: str,
    data_format: str = "json",
) -> list[TextContent]:
    """Query and transform data using JMESPath expressions.

    JMESPath is a query language for JSON (like jq). Examples:
      - "users[*].name" — extract all user names
      - "users[?age > `30`]" — filter users over 30
      - "length(users)" — count users

    Args:
        data: JSON or YAML data string
        jmespath_query: JMESPath query expression
        data_format: "json" or "yaml"
    """
    import jmespath

    if data_format == "yaml":
        import yaml
        parsed = yaml.safe_load(data)
    else:
        parsed = json.loads(data)

    result = jmespath.search(jmespath_query, parsed)
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

@server.tool()
async def aggregate(
    data: str,
    group_by: str,
    metrics: str = "count",
    data_format: str = "json",
) -> list[TextContent]:
    """Aggregate data by grouping and computing metrics.

    Args:
        data: JSON array of objects
        group_by: Field name to group by
        metrics: Comma-separated metric specs, e.g. "count,sum:salary,avg:age,max:score"
        data_format: "json" or "csv"
    """
    if data_format == "csv":
        rows = _parse_csv(data)
    else:
        rows = json.loads(data)

    if not rows:
        return [TextContent(type="text", text=json.dumps({"error": "No data"}, indent=2))]

    # Group
    groups: dict[str, list[dict]] = {}
    for row in rows:
        key = str(row.get(group_by, "null"))
        groups.setdefault(key, []).append(row)

    # Compute metrics
    metric_specs = [m.strip() for m in metrics.split(",")]
    result = {}
    for key, group_rows in groups.items():
        result[key] = {"count": len(group_rows)}
        for spec in metric_specs:
            if ":" in spec:
                op, field = spec.split(":", 1)
                values = []
                for r in group_rows:
                    try:
                        values.append(float(r.get(field, 0)))
                    except (ValueError, TypeError):
                        pass
                if not values:
                    continue
                if op == "sum":
                    result[key][f"sum_{field}"] = round(sum(values), 2)
                elif op == "avg":
                    result[key][f"avg_{field}"] = round(statistics.mean(values), 2)
                elif op == "min":
                    result[key][f"min_{field}"] = min(values)
                elif op == "max":
                    result[key][f"max_{field}"] = max(values)
                elif op == "median":
                    result[key][f"median_{field}"] = round(statistics.median(values), 2)
                elif op == "stdev":
                    result[key][f"stdev_{field}"] = round(statistics.stdev(values), 2) if len(values) > 1 else 0

    return [TextContent(type="text", text=json.dumps(result, indent=2))]

@server.tool()
async def merge(
    left_data: str,
    right_data: str,
    on: str,
    how: str = "inner",
) -> list[TextContent]:
    """Merge two JSON arrays of objects by a common key field.

    Args:
        left_data: JSON array (left side)
        right_data: JSON array (right side)
        on: Key field to join on
        how: Join type — "inner", "left", "right", "outer"
    """
    left = json.loads(left_data)
    right = json.loads(right_data)

    right_index: dict[str, dict] = {str(r.get(on, "")): r for r in right}

    merged = []
    matched_keys = set()
    for l_item in left:
        key = str(l_item.get(on, ""))
        if key in right_index:
            merged.append({**l_item, **{f"right_{k}": v for k, v in right_index[key].items() if k != on}})
            matched_keys.add(key)
        elif how in ("left", "outer"):
            merged.append({**l_item})

    if how in ("right", "outer"):
        for r_item in right:
            key = str(r_item.get(on, ""))
            if key not in matched_keys:
                merged.append({**r_item})

    return [TextContent(type="text", text=json.dumps(merged, indent=2, default=str))]

@server.tool()
async def generate_mock_data(
    template_json: str,
    count: int = 10,
) -> list[TextContent]:
    """Generate mock data from a JSON template with placeholders.

    Placeholders:
      {{uuid}} — random UUID
      {{int:min:max}} — random integer
      {{float:min:max}} — random float
      {{name}} — random full name
      {{email}} — random email
      {{city}} — random city name
      {{date:start:end}} — random date in range (YYYY-MM-DD)
      {{choice:a,b,c}} — random choice from list
      {{word:N}} — N random words
      {{bool}} — random true/false

    Args:
        template_json: JSON template string with placeholders
        count: Number of records to generate
    """
    import random as rand
    import uuid
    from datetime import datetime, timedelta

    first_names = ["Alice", "Bob", "Carol", "Dave", "Eve", "Frank", "Grace", "Heidi", "Ivan", "Judy"]
    last_names = ["Smith", "Jones", "Lee", "Patel", "Kim", "Garcia", "Muller", "Chen", "Brown", "Davis"]
    cities = ["New York", "London", "Tokyo", "Paris", "Berlin", "Sydney", "Toronto", "Mumbai", "Seoul", "Dubai"]

    def _resolve_placeholder(placeholder: str) -> str:
        name = placeholder.split(":")[0]
        args = placeholder.split(":")[1:] if ":" in placeholder else []

        if name == "uuid":
            return str(uuid.uuid4())[:8]
        elif name == "int":
            lo, hi = int(args[0]) if args else 0, int(args[1]) if len(args) > 1 else 100
            return str(rand.randint(lo, hi))
        elif name == "float":
            lo, hi = float(args[0]) if args else 0, float(args[1]) if len(args) > 1 else 100
            return str(round(rand.uniform(lo, hi), 2))
        elif name == "name":
            return f"{rand.choice(first_names)} {rand.choice(last_names)}"
        elif name == "email":
            return f"{rand.choice(first_names).lower()}.{rand.choice(last_names).lower()}@example.com"
        elif name == "city":
            return rand.choice(cities)
        elif name == "date":
            start = datetime(2020, 1, 1)
            end = datetime(2026, 12, 31)
            if args:
                start = datetime.strptime(args[0], "%Y-%m-%d")
                if len(args) > 1:
                    end = datetime.strptime(args[1], "%Y-%m-%d")
            delta = (end - start).days
            return (start + timedelta(days=rand.randint(0, delta))).strftime("%Y-%m-%d")
        elif name == "choice":
            return rand.choice(args) if args else ""
        elif name == "word":
            n = int(args[0]) if args else 2
            words = ["lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit"]
            return " ".join(rand.choices(words, k=n))
        elif name == "bool":
            return str(rand.choice([True, False])).lower()
        return f"{{{{{placeholder}}}}}"

    template = template_json
    results = []
    for _ in range(count):
        filled = template
        for match in re.finditer(r"\{\{(.+?)\}\}", filled):
            filled = filled.replace(match.group(0), _resolve_placeholder(match.group(1)), 1)
        results.append(json.loads(filled))

    return [TextContent(type="text", text=json.dumps(results, indent=2))]

@server.tool()
async def diff_data(left_data: str, right_data: str) -> list[TextContent]:
    """Compute the difference between two JSON datasets.

    Args:
        left_data: First JSON array
        right_data: Second JSON array
    """
    left = json.loads(left_data) if isinstance(left_data, str) else left_data
    right = json.loads(right_data) if isinstance(right_data, str) else right_data

    left_strs = {json.dumps(item, sort_keys=True) for item in left}
    right_strs = {json.dumps(item, sort_keys=True) for item in right}

    only_left = [json.loads(s) for s in left_strs - right_strs]
    only_right = [json.loads(s) for s in right_strs - left_strs]
    in_both = [json.loads(s) for s in left_strs & right_strs]

    result = {
        "total_left": len(left),
        "total_right": len(right),
        "in_both": len(in_both),
        "only_in_left": len(only_left),
        "only_in_right": len(only_right),
        "only_in_left_items": only_left[:100],
        "only_in_right_items": only_right[:100],
    }
    return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("etl://supported-formats")
async def supported_formats() -> str:
    return json.dumps({
        "input_formats": ["json", "csv", "xml", "yaml", "auto"],
        "output_formats": ["json", "csv", "yaml"],
        "operations": ["convert", "filter_transform", "aggregate", "merge", "validate_schema", "diff_data", "generate_mock_data"],
    }, indent=2)

@server.resource("etl://pipeline/{pipeline_id}")
async def get_pipeline_status(pipeline_id: str) -> str:
    """Parameterized resource — returns the state of a named data pipeline."""
    return json.dumps({
        "pipeline": pipeline_id,
        "status": "idle",
        "last_run": None,
        "records_processed": 0,
        "note": "This is a parameterized resource template. Real implementations would fetch live pipeline state.",
    }, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="data-pipeline-design",
    description="Design a data transformation pipeline from requirements",
    arguments={
        "data_description": {
            "type": "string",
            "description": "Describe the source data: format, fields, volume, etc.",
            "required": True,
        },
        "target_description": {
            "type": "string",
            "description": "Describe the desired output: format, structure, constraints",
            "required": True,
        },
    },
)
async def pipeline_design_prompt(data_description: str, target_description: str) -> dict:
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Design a data transformation pipeline.

SOURCE DATA:
{data_description}

TARGET OUTPUT:
{target_description}

Use the available ETL tools (convert, filter_transform, aggregate, merge, validate_schema) to:
1. Break down the transformation into steps
2. Specify which tool to use for each step
3. Write the exact tool call parameters needed
4. Describe any edge cases or data quality issues to watch for
5. If mock data would help validate the pipeline, generate a sample using generate_mock_data

Be precise about tool parameters — they should be directly executable.""",
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
