#!/usr/bin/env python3
"""
Example 21: Batch Processing

Demonstrates the Anthropic Batch API for processing multiple requests
asynchronously at 50% lower cost than synchronous API calls.

Key concepts:
- Creating JSONL request data for batch processing
- Creating a batch with client.messages.batches.create()
- Polling for completion with client.messages.batches.retrieve()
- Retrieving results with client.messages.batches.results()
- Checking processing status and per-request results
- 50% cost savings compared to synchronous calls

Note: The batch file must be uploaded. Since the API expects a file path
or file-like object, we use io.BytesIO to create an in-memory file.
"""

import os
import io
import json
import time
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()


def main():
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    model = "claude-sonnet-4-20250514"

    print("=" * 72)
    print("BATCH PROCESSING DEMO")
    print("=" * 72)
    print()
    print("The Batch API offers 50% cost reduction vs. synchronous calls.")
    print("Requests are processed asynchronously within 1-2 hours.")
    print()

    # ── Step 1: Create JSONL request data ──────────────────────────────

    print(">>> Step 1: Creating 10 batch requests as JSONL data...")

    # Each line is a JSON object with custom_id, params, and model
    requests = []
    for i in range(10):
        requests.append({
            "custom_id": f"req-{i + 1:03d}",
            "params": {
                "model": model,
                "max_tokens": 200,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Write a one-sentence fun fact about the number {i + 1}."
                        ),
                    },
                ],
            },
        })

    # Convert to JSONL (newline-delimited JSON)
    jsonl_lines = "\\n".join(json.dumps(req) for req in requests)
    jsonl_bytes = jsonl_lines.encode("utf-8")

    print(f"  Created {len(requests)} requests")
    print(f"  Total JSONL size: {len(jsonl_bytes)} bytes")
    print(f"  Model: {model}")
    print()

    # ── Step 2: Upload JSONL and create batch ─────────────────────────

    print(">>> Step 2: Uploading batch file and creating batch...")

    # Create an in-memory file-like object
    file_obj = io.BytesIO(jsonl_bytes)
    file_obj.name = "batch_requests.jsonl"

    batch_file = client.files.create(
        file_path=file_obj,
        purpose="batch_results",  # required for batch input
    )
    print(f"  Uploaded file ID: {batch_file.id}")
    print(f"  File size: {batch_file.size_bytes} bytes")

    batch = client.messages.batches.create(
        input_file_id=batch_file.id,
    )
    batch_id = batch.id
    print(f"  Batch ID: {batch_id}")
    print(f"  Initial status: {batch.processing_status}")
    print()

    # ── Step 3: Poll for completion ───────────────────────────────────

    print(">>> Step 3: Polling for batch completion...")
    print("  (In a real scenario, this can take minutes to hours.)")
    print()

    max_polls = 30       # Max polling attempts
    poll_interval = 2    # Seconds between polls

    for attempt in range(1, max_polls + 1):
        time.sleep(poll_interval)
        batch_status = client.messages.batches.retrieve(batch_id=batch_id)

        status = batch_status.processing_status
        counts = {
            "succeeded": getattr(batch_status, "request_counts", {}).get("succeeded", 0)
            if hasattr(batch_status, "request_counts")
            else 0,
            "errored": getattr(batch_status, "request_counts", {}).get("errored", 0)
            if hasattr(batch_status, "request_counts")
            else 0,
            "processing": getattr(batch_status, "request_counts", {}).get("processing", 0)
            if hasattr(batch_status, "request_counts")
            else 0,
        }

        print(
            f"  Poll {attempt:2d}: status={status:<12} "
            f"succeeded={counts['succeeded']}  errored={counts['errored']}  "
            f"processing={counts['processing']}"
        )

        if status == "ended":
            print()
            print(f">>> Batch processing complete!")
            break
        if attempt >= max_polls:
            print()
            print(">>> Max polls reached. Batch may still be processing.")
            print("    In production, use webhook notifications instead of polling.")
            break
    else:
        print("  Batch did not complete in the allotted polling time.")

    print()

    # ── Step 4: Retrieve results ──────────────────────────────────────

    print(">>> Step 4: Retrieving batch results...")

    try:
        # The results() method returns a paginated list of batch results
        results = client.messages.batches.results(batch_id=batch_id)
        results_list = list(results)

        print(f"  Retrieved {len(results_list)} result(s)")
        print()

        for result in results_list:
            custom_id = result.custom_id
            status_code = getattr(result, "status_code", "N/A")

            if status_code == 200 and result.result:
                # Success — print the response content
                msg_type = getattr(result.result, "type", "unknown")
                if msg_type == "message" and hasattr(result.result, "content"):
                    text_content = " ".join(
                        block.text
                        for block in result.result.content
                        if hasattr(block, "text")
                    )
                    print(f"  [{custom_id}] OK | {text_content[:120]}...")
                else:
                    print(f"  [{custom_id}] OK | type={msg_type}")
            else:
                # Error — print the error details
                error_info = getattr(result, "error", "unknown error")
                print(f"  [{custom_id}] ERR | {error_info}")
    except Exception as e:
        print(f"  Could not retrieve results: {e}")
        print()
        print("  NOTE: Results are only available after the batch has completed")
        print("  processing (status='ended'). The polling loop above may have")
        print("  timed out before completion.")
    print()

    # ── Step 5: Cost comparison ───────────────────────────────────────

    print(">>> Step 5: Cost comparison (synchronous vs batch)")
    print()

    # Example pricing: batch is 50% cheaper
    sync_input_cost_per_mtok = 3.00    # Sonnet input
    sync_output_cost_per_mtok = 15.00  # Sonnet output
    batch_input_cost_per_mtok = 1.50   # 50% less
    batch_output_cost_per_mtok = 7.50  # 50% less

    estimated_input_tokens = 50   # ~50 tokens per request
    estimated_output_tokens = 40  # ~40 tokens per response
    total_requests = 10

    sync_cost = (
        (estimated_input_tokens * total_requests * sync_input_cost_per_mtok)
        + (estimated_output_tokens * total_requests * sync_output_cost_per_mtok)
    ) / 1_000_000

    batch_cost = (
        (estimated_input_tokens * total_requests * batch_input_cost_per_mtok)
        + (estimated_output_tokens * total_requests * batch_output_cost_per_mtok)
    ) / 1_000_000

    savings = sync_cost - batch_cost
    savings_pct = (savings / sync_cost) * 100 if sync_cost > 0 else 0

    print(f"  {'':<25} {'Synchronous':<16} {'Batch':<16}")
    print(f"  {'-'*25} {'-'*16} {'-'*16}")
    print(f"  {'Per-M input token':<25} ${sync_input_cost_per_mtok:<13.2f} ${batch_input_cost_per_mtok:<13.2f}")
    print(f"  {'Per-M output token':<25} ${sync_output_cost_per_mtok:<13.2f} ${batch_output_cost_per_mtok:<13.2f}")
    print(f"  {'Estimated cost':<25} ${sync_cost:<14.6f} ${batch_cost:<14.6f}")
    print(f"  {'Savings':<25} {'':<16} {savings_pct:.0f}% less")
    print()

    # ── Cleanup ───────────────────────────────────────────────────────

    print(">>> Cleanup: Deleting uploaded batch file...")
    try:
        client.files.delete(file_id=batch_file.id)
        print(f"  Deleted batch input file: {batch_file.id}")
    except Exception as e:
        print(f"  Could not delete file: {e}")

    print()
    print("=" * 72)
    print("BATCH API DEMO COMPLETE")
    print("=" * 72)
    print()
    print("Key benefits of Batch API:")
    print("  - 50% cost reduction vs synchronous API calls")
    print("  - Process up to 10,000 requests per batch")
    print("  - Results available within 1-2 hours (usually faster)")
    print("  - Ideal for: evals, content generation, data enrichment")
    print()
    print("See: https://docs.anthropic.com/en/docs/build-with-claude/batch-processing")


if __name__ == "__main__":
    main()
