# Chapter 11: TerminalBench 2.0 Walkthrough

## The Domain: Agentic Coding

**Task:** Autonomous coding on TerminalBench 2.0 — a benchmark where agents must solve real-world terminal tasks (extract archives, configure servers, debug scripts, write code) inside a sandboxed Linux environment.

**Why this is a harness problem:** The base model is fixed. Performance depends on the **scaffold** — how the harness manages the environment, constructs prompts, handles tool outputs, and recovers from errors.

## The Starting Point

The baseline is a strong **human-written harness** (BaselineKira):

```python
class AgentHarness:
    def __init__(self, model, sandbox):
        self.model = model
        self.sandbox = sandbox
        self.history = []
        self.scratchpad = ""

    def step(self, task: str) -> str:
        prompt = f"""
        Task: {task}

        Previous actions:
        {self._format_history()}

        Scratchpad:
        {self.scratchpad}

        What should I do next?
        """

        response = self.model.generate(prompt)

        # Parse tool calls from response
        tool_calls = self._parse_tool_calls(response)

        for call in tool_calls:
            result = self.sandbox.execute(call)
            self.history.append((call, result))
            self.scratchpad += f"\n{call} → {result[:200]}"

        return response
```

This baseline was already competitive — Top 30 on TerminalBench 2.0. But Meta-Harness found improvements the human authors missed.

## What Meta-Harness Discovered

### Finding 1: "Environment Bootstrapping"

The proposer noticed agents wasted 2-3 initial turns exploring the sandbox:

```bash
$ cat candidate_003/traces/task_extract_elf.json | jq '.steps[0:6]'
[
  {"step": 1, "action": "ls",         "output": "README.md  data/ src/"},
  {"step": 2, "action": "ls data/",   "output": "archive.tar.gz input.csv"},
  {"step": 3, "action": "file data/archive.tar.gz",
   "output": "gzip compressed data"},
  {"step": 4, "action": "which python", "output": "/usr/bin/python3"},
  {"step": 5, "action": "python --version",
   "output": "Python 3.11.2"},
  # Only at step 6 does actual work begin
  {"step": 6, "action": "tar xzf data/archive.tar.gz", ...}
]
```

**Fix — Environment Bootstrapping:** Snapshot the sandbox environment before the agent starts, and inject it into the initial prompt:

```python
class BootstrappedHarness(AgentHarness):
    def step(self, task):
        # Snapshot environment once (first turn only)
        if not hasattr(self, '_env_snapshot'):
            self._env_snapshot = self._snapshot_environment()

        prompt = f"""
        Task: {task}

        Environment:
        {self._env_snapshot}        # ← pre-populated!

        Previous actions:
        {self._format_history()}

        What should I do next?
        """
        # ...
```

**Effect:** Agent skips 2-3 exploration turns, starts actual work immediately. Pass rate improved.

### Finding 2: Structured Observation

The baseline's `_format_history()` just concatenated raw tool outputs:

```
Tool: ls
Output: README.md
data/
src/

Tool: cat data/input.csv
Output: id,name,value
1,alpha,100
2,beta,200
...
```

Long outputs overwhelmed the context window. The proposer noticed that ~40% of failures involved the agent losing track of important information buried in verbose outputs.

**Fix — Structured Observation:** Parse tool outputs and extract only the structurally relevant parts:

```python
class StructuredHarness(AgentHarness):
    def _format_observation(self, call, result):
        if call.command.startswith('ls'):
            # Summarize: count + first 5 items
            items = result.strip().split('\n')
            return f"Directory: {len(items)} items (showing 5): {', '.join(items[:5])}"

        elif call.command.startswith('cat ') and '.csv' in call.command:
            # Extract: header + row count
            lines = result.strip().split('\n')
            header = lines[0]
            return f"CSV: header={header}, rows={len(lines)-1}"

        elif call.command.startswith('file '):
            # Keep: just the file type
            return f"File type: {result.split(':')[1].strip() if ':' in result else result}"

        else:
            # Default: truncate to 500 chars
            return result[:500]
```

**Effect:** Context usage dropped ~35%, agent could track longer task histories, pass rate improved.

### Finding 3: Error Recovery Patterns

The proposer identified that ~25% of failures were recoverable — the agent made a correctable mistake (wrong flag, missing dependency, typo in filename) but had no structured recovery mechanism:

```bash
# From traces: agent typo, then gives up
{"step": 7, "action": "pip instal pandas", "output": "ERROR: Unknown command 'instal'"}
{"step": 8, "action": "DONE", "output": "I couldn't install the dependencies"}
```

**Fix — Error Recovery Hints:** After tool failures, inject a hint suggesting common fixes:

```python
class RecoveryHarness(AgentHarness):
    COMMON_FIXES = {
        'Unknown command': 'Did you mean "install"?',
        'No such file': 'Check filename spelling. Try: ls to see files.',
        'Permission denied': 'Try with sudo, or check file permissions.',
        'ModuleNotFoundError': 'Try: pip install <module>',
        'command not found': 'Try: apt-get install <package> or which <command>',
    }

    def _process_result(self, call, result):
        for error_pattern, hint in self.COMMON_FIXES.items():
            if error_pattern.lower() in result.lower():
                return f"{result}\n[HINT: {hint}]"
        return result
```

**Effect:** Recovery rate improved ~15%, agents no longer abandoned tasks after one failure.

## Full Results

| Configuration | Pass Rate | Rank |
|---|---|---|
| Baseline (hand-written) | — | Top 30 |
| Claude Haiku 4.5 + Meta-Harness | **37.6%** | **#1** Haiku-based |
| Claude Opus 4.6 + Meta-Harness | **76.4%** | **#2** overall |
| Opus 4.6 baseline (no harness optimization) | ~65% | Lower |

The discovered harness added ~11 percentage points to Opus 4.6 without changing the model.

## The Optimized Harness

After 30+ iterations, the final harness combined all three discoveries:

```python
class OptimizedHarness(AgentHarness):
    def __init__(self, model, sandbox):
        super().__init__(model, sandbox)
        self.env_snapshot = None
        self.error_history = []

    def step(self, task):
        # Discovery 1: Environment bootstrapping
        if self.env_snapshot is None:
            self.env_snapshot = self._snapshot_environment()

        prompt = self._build_prompt(task)

        for attempt in range(3):  # max 3 retries per step
            response = self.model.generate(prompt)
            tool_calls = self._parse_tool_calls(response)

            for call in tool_calls:
                result = self.sandbox.execute(call)

                # Discovery 3: Error recovery hints
                if self._is_error(result):
                    hint = self._get_hint(result)
                    result = f"{result}\n[HINT: {hint}]"
                    self.error_history.append((call, result))

                # Discovery 2: Structured observation
                obs = self._format_observation(call, result)
                self.history.append(obs)

                # If error, retry with hint in prompt
                if self._is_error(result) and attempt < 2:
                    prompt = f"{prompt}\n\nError on {call}: {obs}\nTry again."
                    break
            else:
                break  # no errors, continue

        return response
```

## Running the Experiment

```bash
cd reference_examples/terminal_bench_2

# Install dependencies
uv sync

# Smoke test: 1 task, 1 trial
uv run bash scripts/run_eval.sh \
    agents.baseline_kira:AgentHarness full 1 1 \
    -i extract-elf

# Full search (paper scale — hours to days)
uv run python meta_harness.py --iterations 30
```

### Key Files

```
reference_examples/terminal_bench_2/
├── meta_harness.py             # Search loop adapted for TerminalBench
├── claude_wrapper.py           # Proposer agent (Claude Code)
├── agents/
│   └── baseline_kira/
│       └── AgentHarness.py     # Starting harness
├── scripts/
│   └── run_eval.sh             # Evaluation runner
├── tasks/                      # TerminalBench tasks
├── sandbox/                    # Sandbox configuration
└── search_history/             # Results accumulate here
```

### The Artifact Repo

The optimized harness from the paper lives in a separate repo:

```bash
git clone https://github.com/stanford-iris-lab/meta-harness-tbench2-artifact
```

This contains the final, optimized `AgentHarness.py` that achieved the paper's results — useful for studying what the search converged to without running the full search yourself.

## Key Takeaways

1. **Scaffold matters enormously.** Pure harness changes (environment bootstrapping, structured observation, error recovery) added ~11 percentage points to Opus 4.6 without touching model weights.
2. **Discovery 1 — Environment bootstrapping** saved 2-3 exploratory turns per task by pre-populating environment info.
3. **Discovery 2 — Structured observation** cut context usage by 35%, letting agents track longer task histories.
4. **Discovery 3 — Error recovery hints** improved recovery rate by ~15%, preventing agents from giving up after one mistake.
5. **Search is viable.** A coding agent with full trace access found improvements that expert human engineers missed — and did it systematically.

---

**Previous:** [Chapter 10 — Text Classification Walkthrough](./10_text_classification_walkthrough.md)
**Next:** [Chapter 12 — Onboarding a New Domain](./12_onboarding_new_domain.md)
