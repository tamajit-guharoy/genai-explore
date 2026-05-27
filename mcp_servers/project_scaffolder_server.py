#!/usr/bin/env python3
"""
MCP Project Scaffolder Server — demonstrates project generation, template-based
scaffolding, interactive prompts via MCP prompts, and multi-file output.

Install: pip install mcp
Configure in .claude/settings.json:
{
  "mcpServers": {
    "scaffold": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/project_scaffolder_server.py"],
      "env": { "SCAFFOLD_OUTPUT_DIR": "./generated" }
    }
  }
}
"""

import asyncio
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import Tool, TextContent, Resource, ResourceTemplate

server = Server("scaffold")

OUTPUT_DIR = Path(os.environ.get("SCAFFOLD_OUTPUT_DIR", "./generated"))

# ---------------------------------------------------------------------------
# Template registry
# ---------------------------------------------------------------------------
PROJECT_TEMPLATES = {
    "python-cli": {
        "name": "Python CLI App",
        "description": "Python command-line application with argparse, logging, and tests",
        "files": {
            "{{project}}/README.md": '''# {{project}}

{{description}}

## Install

```bash
pip install -e .
```

## Usage

```bash
{{project}} --help
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
''',
            "{{project}}/pyproject.toml": '''[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "{{project}}"
version = "0.1.0"
description = "{{description}}"
readme = "README.md"
requires-python = ">=3.10"
dependencies = []

[project.optional-dependencies]
dev = ["pytest", "pytest-cov", "ruff", "mypy"]

[project.scripts]
{{project}} = "{{module_name}}.cli:main"
''',
            "{{project}}/src/{{module_name}}/__init__.py": '''"""{{project}} — {{description}}"""

__version__ = "0.1.0"
''',
            "{{project}}/src/{{module_name}}/cli.py": '''"""Command-line interface for {{project}}."""

import argparse
import logging
import sys

def main() -> None:
    parser = argparse.ArgumentParser(description="{{description}}")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    logging.info("{{project}} started")
    print("Hello from {{project}}!")

if __name__ == "__main__":
    main()
''',
            "{{project}}/tests/__init__.py": "",
            "{{project}}/tests/test_cli.py": '''"""Tests for {{project}} CLI."""

import subprocess
import sys

def test_cli_runs():
    result = subprocess.run(
        [sys.executable, "-m", "{{module_name}}.cli", "--version"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
''',
        },
    },
    "python-web": {
        "name": "Python Web API (FastAPI)",
        "description": "FastAPI web application with routers, middleware, and tests",
        "files": {
            "{{project}}/README.md": '''# {{project}}

{{description}}

## Quickstart

```bash
pip install -e .
uvicorn {{module_name}}.app:app --reload
```
''',
            "{{project}}/pyproject.toml": '''[project]
name = "{{project}}"
version = "0.1.0"
description = "{{description}}"
requires-python = ">=3.10"
dependencies = ["fastapi", "uvicorn[standard]", "pydantic"]

[project.optional-dependencies]
dev = ["pytest", "httpx"]
''',
            "{{project}}/src/{{module_name}}/__init__.py": "",
            "{{project}}/src/{{module_name}}/app.py": '''"""FastAPI application for {{project}}."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import health

app = FastAPI(
    title="{{project}}",
    description="{{description}}",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
''',
            "{{project}}/src/{{module_name}}/routers/__init__.py": "",
            "{{project}}/src/{{module_name}}/routers/health.py": '''"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "{{project}}"}
''',
            "{{project}}/tests/test_health.py": '''from fastapi.testclient import TestClient
from {{module_name}}.app import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
''',
        },
    },
    "node-ts": {
        "name": "Node.js TypeScript Package",
        "description": "Node.js TypeScript library with ESM, Vitest, and ESLint",
        "files": {
            "{{project}}/README.md": '''# {{project}}

{{description}}

## Install

```bash
npm install {{project}}
```

## Usage

```typescript
import { greet } from "{{project}}";
console.log(greet("World"));
```
''',
            "{{project}}/package.json": '''{
  "name": "{{project}}",
  "version": "0.1.0",
  "description": "{{description}}",
  "type": "module",
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  },
  "scripts": {
    "build": "tsc",
    "test": "vitest run",
    "lint": "eslint src/"
  },
  "devDependencies": {
    "@types/node": ">=20",
    "typescript": "^5.5",
    "vitest": "^1.6",
    "eslint": "^9"
  }
}
''',
            "{{project}}/tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "declaration": true,
    "outDir": "./dist",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist", "tests"]
}
''',
            "{{project}}/src/index.ts": '''/**
 * {{project}} — {{description}}
 */

export function greet(name: string): string {
  return `Hello, ${name}! Welcome to {{project}}.`;
}
''',
            "{{project}}/tests/index.test.ts": '''import { describe, it, expect } from "vitest";
import { greet } from "../src/index.js";

describe("greet", () => {
  it("returns a greeting", () => {
    expect(greet("World")).toBe("Hello, World! Welcome to {{project}}.");
  });
});
''',
        },
    },
    "docker-compose": {
        "name": "Docker Compose Stack",
        "description": "Multi-service Docker Compose setup with health checks",
        "files": {
            "{{project}}/README.md": '''# {{project}} Docker Stack

{{description}}

## Services

- **app**: Main application
- **db**: PostgreSQL database
- **cache**: Redis cache

## Usage

```bash
docker compose up -d
```
''',
            "{{project}}/docker-compose.yml": '''version: "3.9"

services:
  app:
    build: .
    ports:
      - "{{app_port}}:{{app_port}}"
    environment:
      - DATABASE_URL=postgresql://{{db_user}}:{{db_pass}}@db:5432/{{db_name}}
      - REDIS_URL=redis://cache:6379
    depends_on:
      db:
        condition: service_healthy
      cache:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER={{db_user}}
      - POSTGRES_PASSWORD={{db_pass}}
      - POSTGRES_DB={{db_name}}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U {{db_user}}"]
      interval: 5s
      timeout: 5s
      retries: 5

  cache:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
''',
            "{{project}}/Dockerfile": '''FROM python:3.12-slim

WORKDIR /app
COPY . .
RUN pip install -e .
EXPOSE {{app_port}}
CMD ["python", "-m", "{{module_name}}.app"]
''',
        },
    },
}

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@server.tool()
async def list_project_templates() -> list[TextContent]:
    """List all available project templates with descriptions."""
    templates = []
    for slug, tpl in PROJECT_TEMPLATES.items():
        templates.append({
            "slug": slug,
            "name": tpl["name"],
            "description": tpl["description"],
            "file_count": len(tpl["files"]),
            "files": list(tpl["files"].keys()),
        })
    return [TextContent(type="text", text=json.dumps(templates, indent=2))]

@server.tool()
async def generate_project(
    template_slug: str,
    project_name: str,
    description: str = "A new project",
    extra_vars: str = "{}",
    output_dir: str = "",
) -> list[TextContent]:
    """Generate a new project from a template, writing all files to disk.

    Args:
        template_slug: Template to use — "python-cli", "python-web", "node-ts", "docker-compose"
        project_name: Project name (use kebab-case, e.g. "my-cool-app")
        description: Project description
        extra_vars: JSON object with additional template variables, e.g. '{"app_port": "8000"}'
        output_dir: Output directory (defaults to SCAFFOLD_OUTPUT_DIR env var or ./generated)
    """
    if template_slug not in PROJECT_TEMPLATES:
        return [TextContent(type="text",
            text=json.dumps({
                "error": f"Unknown template: {template_slug}",
                "available": list(PROJECT_TEMPLATES.keys()),
            }, indent=2))]

    tpl = PROJECT_TEMPLATES[template_slug]
    base_dir = Path(output_dir) if output_dir else OUTPUT_DIR
    base_dir.mkdir(parents=True, exist_ok=True)

    # Build template variables
    module_name = re.sub(r"[^a-zA-Z0-9_]", "_", project_name)
    vars_dict: dict[str, str] = {
        "project": project_name,
        "module_name": module_name,
        "description": description,
        "year": str(datetime.now().year),
        "app_port": "8000",
        "db_user": "app",
        "db_pass": "changeme",
        "db_name": f"{module_name}_db",
    }
    vars_dict.update(json.loads(extra_vars))

    created_files = []
    for template_path, template_content in tpl["files"].items():
        # Substitute variables
        resolved_path = template_path
        resolved_content = template_content
        for key, val in vars_dict.items():
            resolved_path = resolved_path.replace(f"{{{{{key}}}}}", val)
            resolved_content = resolved_content.replace(f"{{{{{key}}}}}", val)

        full_path = base_dir / resolved_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(resolved_content)
        created_files.append(str(full_path))

    return [TextContent(type="text", text=json.dumps({
        "template": template_slug,
        "project_name": project_name,
        "output_directory": str(base_dir.resolve()),
        "files_created": len(created_files),
        "files": created_files,
    }, indent=2))]

@server.tool()
async def preview_project(
    template_slug: str,
    project_name: str,
    description: str = "A new project",
    extra_vars: str = "{}",
) -> list[TextContent]:
    """Preview all files that would be generated without writing to disk.

    Args:
        template_slug: Template slug
        project_name: Project name
        description: Project description
        extra_vars: Extra template variables as JSON
    """
    if template_slug not in PROJECT_TEMPLATES:
        return [TextContent(type="text",
            text=json.dumps({
                "error": f"Unknown template: {template_slug}",
                "available": list(PROJECT_TEMPLATES.keys()),
            }, indent=2))]

    tpl = PROJECT_TEMPLATES[template_slug]
    module_name = re.sub(r"[^a-zA-Z0-9_]", "_", project_name)
    vars_dict: dict[str, str] = {
        "project": project_name,
        "module_name": module_name,
        "description": description,
        "year": str(datetime.now().year),
        "app_port": "8000",
        "db_user": "app",
        "db_pass": "changeme",
        "db_name": f"{module_name}_db",
    }
    vars_dict.update(json.loads(extra_vars))

    files = {}
    for template_path, template_content in tpl["files"].items():
        resolved_path = template_path
        resolved_content = template_content
        for key, val in vars_dict.items():
            resolved_path = resolved_path.replace(f"{{{{{key}}}}}", val)
            resolved_content = resolved_content.replace(f"{{{{{key}}}}}", val)
        files[resolved_path] = resolved_content

    return [TextContent(type="text", text=json.dumps({
        "template": template_slug,
        "project_name": project_name,
        "total_files": len(files),
        "file_tree": list(files.keys()),
        "files": files,
    }, indent=2))]

@server.tool()
async def add_custom_template(
    name: str,
    slug: str,
    description: str,
    files_json: str,
) -> list[TextContent]:
    """Register a custom project template.

    Args:
        name: Human-readable template name
        slug: Unique template slug (used in generate_project)
        description: Template description
        files_json: JSON object mapping file paths to their content as strings.
                    Use {{variable}} placeholders for template variables.
    """
    files = json.loads(files_json)
    PROJECT_TEMPLATES[slug] = {
        "name": name,
        "description": description,
        "files": files,
    }
    return [TextContent(type="text", text=json.dumps({
        "registered": slug,
        "name": name,
        "file_count": len(files),
        "detected_placeholders": list(set(
            var for content in files.values()
            for var in re.findall(r"\{\{(\w+)\}\}", content)
        )),
    }, indent=2))]

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("scaffold://templates")
async def get_templates() -> str:
    return json.dumps({
        slug: {"name": t["name"], "description": t["description"], "files": list(t["files"].keys())}
        for slug, t in PROJECT_TEMPLATES.items()
    }, indent=2)

@server.resource("scaffold://output/{project_name}")
async def get_project_output(project_name: str) -> str:
    """View generated project files for a project."""
    project_dir = OUTPUT_DIR / project_name
    if not project_dir.exists():
        return json.dumps({"error": f"Project not found: {project_name}"})
    files = {}
    for f in project_dir.rglob("*"):
        if f.is_file():
            files[str(f.relative_to(project_dir))] = f.read_text()
    return json.dumps(files, indent=2)

# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@server.prompt(
    name="scaffold-guide",
    description="Interactive guide for scaffolding a new project",
    arguments={
        "project_type": {"type": "string", "description": "What kind of project?", "required": True},
    },
)
async def scaffold_guide(project_type: str) -> dict:
    available = ", ".join(f"'{s}' ({t['name']})" for s, t in PROJECT_TEMPLATES.items())
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Help me scaffold a new {project_type} project.

Available templates: {available}

Steps:
1. Choose the best template from the available options
2. Use preview_project to show what files will be created
3. Confirm with me before running generate_project
4. After generation, suggest next steps (git init, install deps, etc.)

Available template variables you can customize:
- project: kebab-case project name
- description: project description
- module_name: Python-safe module name
- app_port: port number for web services (default 8000)
- db_user, db_pass, db_name: for database templates""",
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
