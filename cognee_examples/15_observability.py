"""
15_observability.py — Trace a pipeline run and analyze performance.

Demonstrates OpenTelemetry tracing for Cognee pipelines, including:
- Enabling tracing
- Tracking LLM calls, entity counts, and timing
- Exporting traces to observability platforms

Prerequisites:
    pip install cognee
"""

import asyncio
import time
import json

import cognee


class SimpleTracer:
    """Lightweight tracer for environments without full OTEL setup.

    In production with cognee.enable_tracing(), this is handled by
    OpenTelemetry with automatic span creation, context propagation,
    and export to Jaeger/Honeycomb/Datadog.
    """

    def __init__(self):
        self.spans: list[dict] = []
        self.current_trace: dict | None = None

    def start_trace(self, name: str) -> dict:
        self.current_trace = {
            "name": name,
            "start_time": time.time(),
            "spans": [],
            "metrics": {},
        }
        return self.current_trace

    def add_span(self, name: str, **kwargs):
        span = {
            "name": name,
            "timestamp": time.time(),
            **kwargs,
        }
        if self.current_trace:
            self.current_trace["spans"].append(span)
        return span

    def end_trace(self):
        if self.current_trace:
            self.current_trace["end_time"] = time.time()
            self.current_trace["duration_ms"] = (
                self.current_trace["end_time"]
                - self.current_trace["start_time"]
            ) * 1000
        trace = self.current_trace
        self.spans.append(trace)
        self.current_trace = None
        return trace

    def summary(self) -> str:
        if not self.spans:
            return "No traces recorded"
        trace = self.spans[-1]
        return json.dumps({
            "pipeline": trace["name"],
            "duration_ms": round(trace["duration_ms"]),
            "span_count": len(trace["spans"]),
            "spans": [s["name"] for s in trace["spans"]],
        }, indent=2)


async def main():
    # ── Initialize tracer ──────────────────────────────────────────────
    tracer = SimpleTracer()

    # In production, use Cognee's built-in OTEL:
    # cognee.enable_tracing()
    # This automatically instruments all pipeline operations.

    print("Running instrumented Cognee pipeline...")

    # ── Phase 1: Data Ingestion ────────────────────────────────────────
    tracer.start_trace("full_pipeline")

    t0 = time.time()
    tracer.add_span("ingestion_start")

    await cognee.add(
        "Machine learning operations (MLOps) is the practice of deploying, "
        "monitoring, and maintaining ML models in production. Key MLOps tools "
        "include MLflow for experiment tracking, Kubeflow for pipeline "
        "orchestration on Kubernetes, and Weights & Biases for experiment "
        "visualization. Feature stores like Feast and Tecton manage feature "
        "engineering pipelines. Model serving platforms include Seldon Core, "
        "BentoML, and TorchServe. The MLOps landscape is fragmented with "
        "over 200 tools across the model lifecycle.",
        dataset_name="mlops",
    )

    tracer.add_span("ingestion_complete", docs_added=1, size_chars=550)
    ingestion_time = (time.time() - t0) * 1000

    # ── Phase 2: Cognify ───────────────────────────────────────────────
    tracer.add_span("cognify_start")
    t0 = time.time()
    await cognee.cognify()
    cognify_time = (time.time() - t0) * 1000
    tracer.add_span("cognify_complete")

    # ── Phase 3: Search ────────────────────────────────────────────────
    tracer.add_span("search_start")
    t0 = time.time()

    queries = [
        "What tools are used for experiment tracking in MLOps?",
        "How do feature stores relate to model serving?",
    ]

    for query in queries:
        tracer.add_span("llm_search_call", query=query[:60])
        results = await cognee.search(query)
        tracer.add_span(
            "llm_search_response",
            result_count=len(list(results)) if results else 0,
        )

    search_time = (time.time() - t0) * 1000

    # ── End trace ──────────────────────────────────────────────────────
    trace = tracer.end_trace()
    trace["metrics"] = {
        "ingestion_time_ms": round(ingestion_time),
        "cognify_time_ms": round(cognify_time),
        "search_time_ms": round(search_time),
        "total_llm_calls": sum(
            1 for s in trace["spans"] if s["name"].startswith("llm_")
        ),
    }

    # ── Display trace summary ──────────────────────────────────────────
    print("\n" + "=" * 60)
    print("PIPELINE TRACE SUMMARY")
    print("=" * 60)

    print(f"\nPipeline: {trace['name']}")
    print(f"Total duration: {trace['duration_ms']:.0f}ms")

    print(f"\nPhase timings:")
    print(f"  Ingestion: {ingestion_time:.0f}ms")
    print(f"  Cognify:   {cognify_time:.0f}ms")
    print(f"  Search:    {search_time:.0f}ms")

    print(f"\nSpans ({len(trace['spans'])}):")
    for span in trace["spans"]:
        extras = ""
        for k, v in span.items():
            if k not in ("name", "timestamp"):
                extras += f", {k}={v}"
        print(f"  [{span['name']}]{extras}")

    print(f"\nMetrics:")
    for k, v in trace["metrics"].items():
        print(f"  {k}: {v}")

    print(f"\nFull trace JSON:")
    print(tracer.summary())

    print("\n" + "=" * 60)
    print("In production with OpenTelemetry:")
    print("  cognee.enable_tracing()")
    print("  # Configure exporter:")
    print("  cognee.config.set({")
    print("      'otel_exporter_endpoint': 'https://api.honeycomb.io/v1/traces',")
    print("      'otel_exporter_headers': {'x-honeycomb-team': 'your-key'},")
    print("  })")
    print("  # All pipeline operations are now auto-instrumented.")


if __name__ == "__main__":
    asyncio.run(main())
