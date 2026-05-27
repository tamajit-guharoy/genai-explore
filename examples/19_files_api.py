#!/usr/bin/env python3
"""
Example 19: Files API

Demonstrates the full lifecycle of the Anthropic Files API:
creating, listing, retrieving, using in a message, and deleting files.

Key concepts:
- client.files.create() — upload a file
- client.files.list() — list all uploaded files
- client.files.retrieve() — get metadata for a specific file
- Using a file_id in a message via the "document" content block type
- client.files.delete() — remove a file
- Full lifecycle: create -> list -> retrieve -> use -> delete
"""

import os
import tempfile
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = "claude-sonnet-4-20250514"

    print("=" * 72)
    print("FILES API — FULL LIFECYCLE")
    print("=" * 72)
    print()

    # ── Step 1: Create a sample text file ────────────────────────────────

    print(">>> Step 1: Creating a sample text file for upload...")

    sample_content = """\
# Project Overview

## Architecture
The system uses a microservices architecture with the following components:
- API Gateway (Kong)
- Auth Service (OAuth 2.0 / JWT)
- Data Pipeline (Apache Kafka + Flink)
- Storage Layer (PostgreSQL + Redis Cache)

## API Endpoints

### Public Endpoints
| Method | Path              | Description            |
|--------|-------------------|------------------------|
| GET    | /api/v1/health    | Health check           |
| GET    | /api/v1/docs      | API documentation      |

### Authenticated Endpoints
| Method | Path                   | Description            |
|--------|------------------------|------------------------|
| GET    | /api/v1/users/me       | Get current user       |
| PUT    | /api/v1/users/me       | Update profile         |
| GET    | /api/v1/data           | Get paginated data     |
| POST   | /api/v1/data           | Create new record      |

## Deployment
The application is deployed on Kubernetes (EKS) with Helm charts.
Monitoring is handled by Prometheus + Grafana.
"""

    # Write to a temp file for upload
    tmp_path = os.path.join(tempfile.gettempdir(), "project_overview.md")
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(sample_content)
    print(f"  Created temp file: {tmp_path}")
    print(f"  Size: {len(sample_content)} bytes")
    print()

    # ── Step 2: Upload the file ──────────────────────────────────────────

    print(">>> Step 2: Uploading file via client.files.create()...")

    uploaded_file = client.files.create(
        file_path=tmp_path,
        purpose="document",  # or "tool_output" for tool outputs
    )

    file_id = uploaded_file.id
    print(f"  File ID: {file_id}")
    print(f"  Type: {uploaded_file.type}")
    print(f"  Purpose: {uploaded_file.purpose}")
    print(f"  Size (bytes): {uploaded_file.size_bytes}")
    print(f"  Created at: {uploaded_file.created_at}")
    print()

    # ── Step 3: List all files ───────────────────────────────────────────

    print(">>> Step 3: Listing all uploaded files...")

    files_list = client.files.list()
    print(f"  Total files: {len(files_list.data)}")
    for f in files_list.data:
        print(f"    - {f.id} ({f.filename or 'unnamed'}, {f.size_bytes} bytes, status={getattr(f, 'status', 'N/A')})")
    print()

    # ── Step 4: Retrieve file metadata ───────────────────────────────────

    print(">>> Step 4: Retrieving file metadata...")

    retrieved = client.files.retrieve(file_id=file_id)
    print(f"  ID: {retrieved.id}")
    print(f"  Filename: {retrieved.filename}")
    print(f"  Purpose: {retrieved.purpose}")
    print(f"  Size: {retrieved.size_bytes} bytes")
    print(f"  Created at: {retrieved.created_at}")
    # The Files API response includes a status field while processing
    status = getattr(retrieved, "status", "N/A")
    print(f"  Status: {status}")
    print()

    # ── Step 5: Use the file in a message ────────────────────────────────

    print(">>> Step 5: Using the uploaded file in a message...")

    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "document",
                        "source": {
                            "type": "file_id",
                            "file_id": file_id,
                        },
                    },
                    {
                        "type": "text",
                        "text": "Summarize this project overview document. "
                                "List the main components and API endpoints.",
                    },
                ],
            },
        ],
    )

    print(f"  Claude's response:")
    for block in response.content:
        if block.type == "text":
            print(f"  {block.text}")
    print()

    # ── Step 6: Delete the file ──────────────────────────────────────────

    print(">>> Step 6: Deleting the file...")

    deleted = client.files.delete(file_id=file_id)
    print(f"  Delete result: {deleted}")
    print()

    # ── Verify deletion ──────────────────────────────────────────────────

    print(">>> Verification: Listing files after deletion...")
    files_after = client.files.list()
    still_present = any(f.id == file_id for f in files_after.data)
    print(f"  File still present: {still_present}")
    print(f"  Total files now: {len(files_after.data)}")

    # Clean up temporary file
    try:
        os.remove(tmp_path)
        print(f"  Cleaned up temp file: {tmp_path}")
    except OSError:
        pass

    print()
    print("=" * 72)
    print("FILES API LIFECYCLE COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
