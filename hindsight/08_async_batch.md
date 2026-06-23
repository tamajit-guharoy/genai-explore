# 8. Async & Batch Operations

For production use, Hindsight supports async operations and batch processing for
high-throughput scenarios.

---

## Async Client

All operations have async equivalents prefixed with `a`:

```python
import asyncio
from hindsight_client import Hindsight

async def main():
    client = Hindsight(base_url="http://localhost:8888")

    # Async retain
    await client.aretain(
        bank_id="my-bank",
        content="Alice works at Google"
    )

    # Async batch retain
    await client.aretain_batch(
        bank_id="my-bank",
        items=[
            {"content": "Bob works at Meta"},
            {"content": "Carol works at Amazon"},
        ]
    )

    # Async recall
    results = await client.arecall(
        bank_id="my-bank",
        query="Where do people work?"
    )
    for r in results.results:
        print(r.text)

    # Async reflect
    answer = await client.areflect(
        bank_id="my-bank",
        query="Summarize the team"
    )
    print(answer.text)

    # Always close
    await client.aclose()

asyncio.run(main())
```

---

## Async Context Manager

```python
async def main():
    async with Hindsight(base_url="http://localhost:8888") as client:
        await client.aretain(bank_id="b", content="Hello")
        results = await client.arecall(bank_id="b", query="Hello")
    # Auto-closed
```

---

## Concurrent Operations

### Parallel Retains

```python
async def retain_many(bank_id, items):
    client = Hindsight(base_url="http://localhost:8888")

    # Fire multiple retains in parallel
    tasks = [
        client.aretain(bank_id=bank_id, content=item)
        for item in items
    ]
    results = await asyncio.gather(*tasks)

    await client.aclose()
    return results

# Usage
items = [
    "User prefers Python",
    "Project uses FastAPI",
    "Deployed on AWS",
    "Database is PostgreSQL",
    "CI/CD with GitHub Actions",
]
asyncio.run(retain_many("my-bank", items))
```

### Parallel Recalls Across Banks

```python
async def search_all_banks(query, bank_ids):
    client = Hindsight(base_url="http://localhost:8888")

    tasks = [
        client.arecall(bank_id=bid, query=query, budget="low")
        for bid in bank_ids
    ]
    all_results = await asyncio.gather(*tasks)

    await client.aclose()

    # Merge results from all banks
    merged = []
    for bank_id, results in zip(bank_ids, all_results):
        for r in results.results:
            merged.append({
                "bank": bank_id,
                "text": r.text,
                "score": r.score
            })

    # Sort by score
    merged.sort(key=lambda x: x["score"], reverse=True)
    return merged

# Usage
results = asyncio.run(search_all_banks(
    "deployment",
    ["project-alpha", "project-beta", "project-gamma"]
))
```

---

## Async Retain (Background Processing)

When `retain_async=True`, the call returns immediately and processing happens in the
background. This is ideal for high-throughput ingestion pipelines.

```python
# Sync async retain — returns immediately
result = client.retain(
    bank_id="my-bank",
    content="Log entry: request processed in 23ms",
    retain_async=True
)
# Returns: {"success": True, "operation_id": "op_abc123"}

# Async version
result = await client.aretain(
    bank_id="my-bank",
    content="Log entry: request processed in 23ms",
    retain_async=True
)
```

### Checking Async Operation Status

```python
# Get bank stats to check pending operations
stats = client.get_bank_stats(bank_id="my-bank")
print(f"Pending operations: {stats.pending_operations}")
print(f"Failed operations: {stats.failed_operations}")
```

---

## Batch Retain

For bulk ingestion, `retain_batch()` is significantly faster than individual calls:

```python
# Load existing data in bulk
conversation_history = [
    {"content": "User: What's the best way to deploy FastAPI?", "context": "question"},
    {"content": "Assistant: Docker + AWS ECS is our standard approach.", "context": "answer"},
    {"content": "User: Can we use Kubernetes instead?", "context": "question"},
    {"content": "Assistant: Yes, but ECS is simpler for our scale.", "context": "answer"},
    {"content": "User: OK, let's go with ECS.", "context": "decision"},
]

result = client.retain_batch(
    bank_id="my-bank",
    items=conversation_history,
    document_id="conv_deployment_001",
    retain_async=False
)

print(f"Processed: {result.items_count} items")
```

### Batch with Different Timestamps

```python
from datetime import datetime, timezone

timeline_items = [
    {
        "content": "Project kickoff meeting",
        "timestamp": datetime(2026, 1, 15, tzinfo=timezone.utc).isoformat()
    },
    {
        "content": "Backend MVP completed",
        "timestamp": datetime(2026, 3, 1, tzinfo=timezone.utc).isoformat()
    },
    {
        "content": "First production deployment",
        "timestamp": datetime(2026, 5, 15, tzinfo=timezone.utc).isoformat()
    },
    {
        "content": "Reached 1000 daily active users",
        "timestamp": datetime(2026, 6, 1, tzinfo=timezone.utc).isoformat()
    },
]

client.retain_batch(
    bank_id="my-bank",
    items=timeline_items,
    document_id="project_timeline"
)
```

---

## High-Throughput Ingestion Pipeline

```python
import asyncio
from asyncio import Queue
from hindsight_client import Hindsight

class MemoryIngestor:
    """Buffered, batched memory ingestion pipeline."""

    def __init__(self, bank_id, batch_size=50, flush_interval=5.0):
        self.bank_id = bank_id
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.queue = Queue()
        self.client = Hindsight(base_url="http://localhost:8888")

    async def ingest(self, content, **kwargs):
        """Add an item to the ingestion queue."""
        item = {"content": content, **kwargs}
        await self.queue.put(item)

    async def _flush(self):
        """Flush the queue in batches."""
        batch = []
        while not self.queue.empty():
            try:
                item = self.queue.get_nowait()
                batch.append(item)
                if len(batch) >= self.batch_size:
                    await self._send_batch(batch)
                    batch = []
            except asyncio.QueueEmpty:
                break

        if batch:
            await self._send_batch(batch)

    async def _send_batch(self, batch):
        """Send a batch to Hindsight."""
        try:
            result = await self.client.aretain_batch(
                bank_id=self.bank_id,
                items=batch,
                retain_async=True  # Fire and forget
            )
            return result
        except Exception as e:
            print(f"Batch failed: {e}")
            # Could implement retry logic here

    async def run(self):
        """Main loop — flush periodically."""
        while True:
            await asyncio.sleep(self.flush_interval)
            await self._flush()

    async def shutdown(self):
        """Final flush and cleanup."""
        await self._flush()
        await self.client.aclose()

# Usage
async def main():
    ingestor = MemoryIngestor("high-volume-bank", batch_size=50)

    # Start background flush loop
    loop_task = asyncio.create_task(ingestor.run())

    # Simulate high-volume ingestion
    for i in range(1000):
        await ingestor.ingest(
            content=f"Event #{i}: processed in {i%100}ms",
            context="metrics",
            metadata={"source": "pipeline"}
        )

    # Let the flush loop catch up
    await asyncio.sleep(6)

    # Shutdown
    loop_task.cancel()
    await ingestor.shutdown()

asyncio.run(main())
```

---

## Connection Pooling & Timeouts

### Configuring the Client

```python
client = Hindsight(
    base_url="http://localhost:8888",
    timeout=60.0,  # Request timeout in seconds (default: 30)
    # Uses httpx under the hood with connection pooling
)
```

### Server-Side Pooling

Hindsight server uses connection pooling for PostgreSQL. Configure via environment:

```bash
# Database connection pool
export HINDSIGHT_API_DB_POOL_MIN_SIZE=5
export HINDSIGHT_API_DB_POOL_MAX_SIZE=100
export HINDSIGHT_API_DB_COMMAND_TIMEOUT=60
export HINDSIGHT_API_DB_ACQUIRE_TIMEOUT=30

# LLM concurrency
export HINDSIGHT_API_LLM_MAX_CONCURRENT=32

# Read replica (offloads recall queries)
export HINDSIGHT_API_READ_DATABASE_URL=postgresql://user:pass@read-replica:5432/hindsight
```

---

## Error Handling & Retries

```python
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10)
)
async def robust_retain(client, bank_id, content):
    """Retain with automatic retries on failure."""
    try:
        result = await client.aretain(
            bank_id=bank_id,
            content=content
        )
        return result
    except Exception as e:
        print(f"Retain failed (will retry): {e}")
        raise

# Usage
async def main():
    client = Hindsight(base_url="http://localhost:8888")

    try:
        result = await robust_retain(
            client, "my-bank", "Critical fact that must be stored"
        )
    except Exception:
        print("All retries exhausted — investigate server health")

    await client.aclose()
```

---

## Monitoring Throughput

```python
import time
from collections import defaultdict

class ThroughputMonitor:
    def __init__(self):
        self.stats = defaultdict(lambda: {"count": 0, "total_ms": 0, "errors": 0})

    async def timed_retain(self, client, bank_id, content):
        start = time.monotonic()
        try:
            result = await client.aretain(bank_id=bank_id, content=content)
            elapsed_ms = (time.monotonic() - start) * 1000
            self.stats["retain"]["count"] += 1
            self.stats["retain"]["total_ms"] += elapsed_ms
            return result
        except Exception:
            self.stats["retain"]["errors"] += 1
            raise

    async def timed_recall(self, client, bank_id, query):
        start = time.monotonic()
        try:
            result = await client.arecall(bank_id=bank_id, query=query)
            elapsed_ms = (time.monotonic() - start) * 1000
            self.stats["recall"]["count"] += 1
            self.stats["recall"]["total_ms"] += elapsed_ms
            return result
        except Exception:
            self.stats["recall"]["errors"] += 1
            raise

    def report(self):
        for op, data in self.stats.items():
            avg = data["total_ms"] / data["count"] if data["count"] > 0 else 0
            print(f"{op}: {data['count']} calls, "
                  f"avg {avg:.1f}ms, "
                  f"{data['errors']} errors")
```

---

## Rate Limiting

```python
import asyncio

class RateLimiter:
    def __init__(self, max_per_second):
        self.max_per_second = max_per_second
        self.tokens = max_per_second
        self.last_refill = time.monotonic()

    async def acquire(self):
        while True:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.max_per_second,
                            self.tokens + elapsed * self.max_per_second)
            self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return
            else:
                await asyncio.sleep(1.0 / self.max_per_second)

# Usage
rate_limiter = RateLimiter(max_per_second=10)

async def rate_limited_retain(client, bank_id, content):
    await rate_limiter.acquire()
    return await client.aretain(bank_id=bank_id, content=content)
```

---

Continue to:
- **[09_integrations.md](09_integrations.md)** — Integrate with agent frameworks
- Run the notebook: `notebooks/08_async_batch.ipynb`
