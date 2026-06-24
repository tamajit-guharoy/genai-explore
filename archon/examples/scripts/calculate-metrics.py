# .archon/scripts/calculate-metrics.py
# Python script node (runtime: uv)
# Parses test output and calculates pass/fail metrics.
#
# Usage in workflow:
#   - id: metrics
#     script: calculate-metrics   # Named reference to this file
#     runtime: uv
#     depends_on: [run-tests]
#     timeout: 30000
#
# Or inline with dependencies:
#   - id: metrics
#     script: |
#       import numpy as np
#       ...
#     runtime: uv
#     deps:
#       - "numpy>=2.0"

import json

# "$run-tests.output" is injected as a Python literal at runtime by Archon.
# In this file, it's a placeholder that Archon substitutes at execution time.
data = {"numPassedTests": 0, "numFailedTests": 0}  # $run-tests.output (substituted at runtime)

# Handle both string and already-parsed input
if isinstance(data, str):
    try:
        data = json.loads(data)
    except json.JSONDecodeError:
        print(json.dumps({
            "pass_rate": 0,
            "passed": 0,
            "failed": 0,
            "total": 0,
            "verdict": "ERROR",
            "error": "Could not parse test output"
        }))
        exit(1)

passed = data.get("numPassedTests", 0)
failed = data.get("numFailedTests", 0)
skipped = data.get("numSkippedTests", 0)
total = passed + failed + skipped

pass_rate = round(passed / total * 100, 2) if total > 0 else 0

result = {
    "pass_rate": pass_rate,
    "passed": passed,
    "failed": failed,
    "skipped": skipped,
    "total": total,
    "verdict": "PASS" if failed == 0 else "FAIL",
    "summary": f"{passed}/{total} passed ({pass_rate}%)"
}

print(json.dumps(result))
