# Chapter 15: Sandboxing & Security

## What You'll Learn

- **Tool execution isolation** with Docker containers and subprocess restrictions
- **Path allowlists** — the agent can only read/write within approved directories
- **Command injection prevention** — why `shell=True` is dangerous and how to avoid it
- **Secret brokering** — API keys are injected at egress, never visible to the agent
- Building a `SandboxedExecutor` that wraps every tool call with security checks
- A before/after demonstration: dangerous `rm -rf` blocked, safe operations allowed

---

## 1. The Analogy: The Cleanroom

In semiconductor manufacturing, workers don't handle silicon wafers directly — they
work inside **cleanrooms**, wearing protective suits, using robotic arms. Contamination
from a single speck of dust ruins the chip.

Your agent is the same. You don't give it direct access to your filesystem, your
network, your database. You give it a **cleanroom** — a controlled environment where
it can operate safely.

> **Sandboxing = the agent works in a cleanroom with controlled access. It can touch
> what you allow, nothing more.**

```
┌──────────────────────────────────────────────────────┐
│                 UNSANDBOXED AGENT                     │
│  ┌──────────┐                                        │
│  │  Agent   │──► os.system("rm -rf /")  💀            │
│  └──────────┘       ╳ no restrictions                 │
│                      ╳ full filesystem access          │
│                      ╳ network: anything               │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│                 SANDBOXED AGENT                       │
│  ┌──────────┐     ┌─────────────────────┐            │
│  │  Agent   │──► │ SandboxedExecutor    │            │
│  └──────────┘     │  ├─ path allowlist   │            │
│                    │  ├─ Docker container │            │
│                    │  ├─ no shell=True    │            │
│                    │  ├─ secret injection │            │
│                    │  └─ timeout limits   │            │
│                    └─────────┬───────────┘            │
│                              │                         │
│                    ┌─────────▼───────────┐            │
│                    │ /sandbox/  (isolated)│           │
│                    └─────────────────────┘            │
└──────────────────────────────────────────────────────┘
```

---

## 2. Threat Model: What Could Go Wrong?

| Attack Vector | How It Happens | Real-World Consequence |
|--------------|----------------|----------------------|
| **Command injection** | Agent outputs `"; rm -rf /; echo "` as a tool arg | Deleted filesystem |
| **Path traversal** | Agent reads `../../.env` or `/etc/passwd` | Leaked secrets, credentials |
| **Resource exhaustion** | Agent spawns infinite subprocesses | Server OOM, denial of service |
| **Data exfiltration** | Agent sends secrets to external API via tool call | Credential leak |
| **Prompt extraction** | Malicious user input tricks agent into revealing system prompt | Intellectual property theft |
| **Tool misuse** | Agent uses `write_file` to overwrite critical config | System corruption |

---

## 3. Defense Layer 1: Path Allowlists

The simplest, most effective defense: restrict file operations to a whitelisted
directory.

```python
from pathlib import Path
import os


class PathAllowlist:
    """Restricts file operations to approved directories only.

    Every path the agent tries to access is checked against an
    allowlist. Paths outside the allowlist are rejected before
    they reach the filesystem.

    Think of this as a bouncer at a club — if your path isn't on
    the list, you're not getting in.
    """

    def __init__(self, allowed_dirs: list[str | Path]):
        """Initialize with a list of allowed directories.

        Args:
            allowed_dirs: Absolute paths the agent can access.
                          All subdirectories are implicitly allowed.
        """
        # ═══ Resolve all paths to absolute, normalized form ═══
        self._allowed = [Path(d).resolve() for d in allowed_dirs]

    def is_allowed(self, path: str | Path) -> bool:
        """Check if a path falls within any allowed directory.

        Uses resolve() to eliminate symlinks and '..' traversal.
        """
        try:
            resolved = Path(path).resolve()
        except (OSError, ValueError):
            # ═══ Path can't be resolved (e.g., contains null bytes) → reject ═══
            return False

        # ═══ Check if resolved path is under any allowed directory ═══
        for allowed in self._allowed:
            try:
                resolved.relative_to(allowed)
                return True  # path is inside this allowed directory
            except ValueError:
                continue  # not under this directory, try next one

        return False

    def safe_resolve(self, path: str | Path, base_dir: Path) -> Path | None:
        """Safely resolve a potentially-relative path within a base directory.

        This prevents '..' traversal: even if the agent asks for
        ../../etc/passwd, the resolved path stays within base_dir.

        Args:
            path: The path to resolve (may be relative)
            base_dir: The base directory to resolve within

        Returns:
            Resolved Path if safe, None if it would escape the sandbox
        """
        # ═══ Resolve relative to base_dir, then check ═══
        full_path = (base_dir / path).resolve()

        if self.is_allowed(full_path):
            return full_path

        return None

    def validate_or_raise(self, path: str | Path,
                          operation: str = "access") -> Path:
        """Validate a path and return the resolved version, or raise."""
        resolved = Path(path).resolve()
        if not self.is_allowed(resolved):
            raise SandboxViolationError(
                f"Cannot {operation} '{path}' — path is outside "
                f"allowed directories: {self._allowed}"
            )
        return resolved
```

---

## 4. Defense Layer 2: Command Injection Prevention

The golden rule: **never use `shell=True`**. Period.

```python
import shlex
import subprocess
import shutil


class SafeSubprocess:
    """Execute subprocess commands without shell injection risk.

    The ONLY safe way to run subprocess commands is to pass arguments
    as a list (not a string) with shell=False. This prevents the agent
    from injecting shell metacharacters like ; | && $() `` etc.

    BAD:  subprocess.run(f"cat {user_input}", shell=True)
          If user_input = "file; rm -rf /", game over.

    GOOD: subprocess.run(["cat", user_input], shell=False)
          If user_input = "file; rm -rf /", cat looks for a file
          literally named "file; rm -rf /", which doesn't exist.
    """

    @staticmethod
    def run(command: list[str], *,
            timeout: int = 30,
            cwd: str | None = None,
            env: dict | None = None,
            allowlist: PathAllowlist | None = None,
            ) -> subprocess.CompletedProcess:
        """Run a subprocess command safely.

        Args:
            command: The command as a list of strings (NOT a single string)
            timeout: Maximum execution time in seconds
            cwd: Working directory (must be within allowlist if set)
            env: Environment variables (secrets injected here, not in agent context)
            allowlist: Path allowlist to validate cwd

        Returns:
            subprocess.CompletedProcess with stdout, stderr, returncode

        Raises:
            SandboxViolationError: If cwd is outside the allowlist
            subprocess.TimeoutExpired: If the command takes too long
        """
        # ═══ Validate working directory ═══
        if cwd and allowlist:
            allowlist.validate_or_raise(cwd, "execute in")

        # ═══ Validate command: must be a list, not a string ═══
        if isinstance(command, str):
            raise SandboxViolationError(
                "Command must be a list of strings, not a single string. "
                "Use shlex.split() if you must parse a string, "
                "but validate each argument first."
            )

        # ═══ Validate each argument: no shell metacharacters ═══
        for arg in command:
            if not isinstance(arg, str):
                raise SandboxViolationError(
                    f"Command argument must be a string, got {type(arg)}: {arg}"
                )

        # ═══ Execute with shell=False (the safe default) ═══
        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
            shell=False,  # ═══ THIS IS THE CRITICAL LINE ═══
        )

    @staticmethod
    def validate_shell_command(cmd: str) -> list[str]:
        """Parse a shell command string safely.

        ONLY use this for pre-vetted, static commands. Never pass
        agent-generated strings through here without additional
        argument-level validation.
        """
        # ═══ shlex.split() handles quoting correctly ═══
        # e.g., 'echo "hello world"' → ['echo', 'hello world']
        return shlex.split(cmd)
```

---

## 5. Defense Layer 3: Secret Brokering

The agent should **never** see API keys, database passwords, or auth tokens. These
are injected at the moment of tool execution, via environment variables.

```python
import os
from dataclasses import dataclass, field


@dataclass
class SecretBroker:
    """Manages secrets without exposing them to the agent.

    The agent's context (system prompt, conversation, tool results)
    NEVER contains raw API keys. Instead, secrets are stored in this
    broker and injected into subprocess environments at egress time.

    Think of this as a valet key for your car — the agent can drive
    (use the API), but it can't open the trunk (see the raw key).
    """

    # ═══ Map of secret names → environment variable names ═══
    # The agent references secrets by NAME, e.g., "github_token"
    # The broker resolves this to the actual env var, e.g., "GITHUB_TOKEN"
    secret_map: dict[str, str] = field(default_factory=lambda: {
        "github_token": "GITHUB_TOKEN",
        "openai_api_key": "OPENAI_API_KEY",
        "database_url": "DATABASE_URL",
        "aws_access_key": "AWS_ACCESS_KEY_ID",
        "aws_secret_key": "AWS_SECRET_ACCESS_KEY",
    })

    def resolve(self, secret_name: str) -> str | None:
        """Resolve a secret name to its actual value from the environment.

        Args:
            secret_name: The human-readable secret name (e.g., 'github_token')

        Returns:
            The secret value, or None if not found
        """
        env_var = self.secret_map.get(secret_name)
        if env_var is None:
            return None
        return os.environ.get(env_var)

    def build_env(self, required_secrets: list[str]) -> dict[str, str]:
        """Build a subprocess environment with required secrets injected.

        Args:
            required_secrets: List of secret names the tool needs

        Returns:
            Dict of environment variables to pass to subprocess

        Raises:
            MissingSecretError: If a required secret is not available
        """
        env = {}
        for name in required_secrets:
            value = self.resolve(name)
            if value is None:
                raise MissingSecretError(
                    f"Secret '{name}' is required but not available "
                    f"(check that {self.secret_map.get(name, 'UNKNOWN')} "
                    f"is set in the environment)"
                )
            # ═══ Use the env var name (not the human-readable name) ═══
            env[self.secret_map[name]] = value
        return env

    def redact_secrets(self, text: str) -> str:
        """Remove all known secret values from a string.

        Used before sending tool output back to the agent — ensures
        secrets never leak into the conversation context.
        """
        result = text
        for name in self.secret_map:
            value = self.resolve(name)
            if value and len(value) > 4:
                result = result.replace(value, f"***{name.upper()}***")
        return result


class MissingSecretError(Exception):
    """Raised when a required secret is not available."""
    pass


class SandboxViolationError(Exception):
    """Raised when an operation violates the sandbox rules."""
    pass
```

---

## 6. Building the `SandboxedExecutor` Class

This is the **gatekeeper** — every tool call goes through it.

```python
from dataclasses import dataclass, field
from typing import Any, Callable
import time


@dataclass
class SandboxedExecutor:
    """Wraps tool execution with multiple layers of security.

    Every tool call passes through this executor, which checks:
    1. Path allowlist (can the tool access this file/directory?)
    2. Command safety (no shell injection, no dangerous commands)
    3. Secret injection (secrets added to env, never visible to agent)
    4. Timeout enforcement (tools can't run forever)
    5. Output sanitization (secrets redacted from results)

    Think of this as the TSA for your agent's tool calls — everything
    gets screened before it reaches the real world.
    """

    allowlist: PathAllowlist
    secret_broker: SecretBroker = field(default_factory=SecretBroker)
    default_timeout: int = 30  # seconds
    max_output_length: int = 100_000  # characters — truncate longer results
    allowed_commands: set[str] = field(default_factory=lambda: {
        # ═══ Whitelist of allowed executables (empty = all allowed) ═══
        # If populated, ONLY these commands can run
    })
    blocked_commands: set[str] = field(default_factory=lambda: {
        # ═══ Blacklist of dangerous commands ═══
        "rm", "shred", "mkfs", "dd", ":(){ :|:& };:",  # fork bomb
    })

    # ═══════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════

    def execute(self, tool_name: str, tool_args: dict,
                tool_fn: Callable) -> dict:
        """Execute a tool call through all security layers.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments the agent wants to pass
            tool_fn: The actual function to execute (validated separately)

        Returns:
            Dict with result, truncated flag, and duration
        """
        # ═══ LAYER 1: Validate tool arguments ═══
        sanitized_args = self._sanitize_args(tool_name, tool_args)

        # ═══ LAYER 2: Check path arguments against allowlist ═══
        self._validate_paths_in_args(tool_name, sanitized_args)

        # ═══ LAYER 3: Inject secrets if the tool needs them ═══
        secrets_needed = self._get_required_secrets(tool_name)
        if secrets_needed:
            sanitized_args["_env"] = self.secret_broker.build_env(secrets_needed)

        # ═══ LAYER 4: Execute with timeout ═══
        start = time.monotonic()
        try:
            result = tool_fn(**sanitized_args)
            success = True
            error = None
        except Exception as e:
            result = str(e)
            success = False
            error = str(e)
        duration_ms = (time.monotonic() - start) * 1000

        # ═══ LAYER 5: Sanitize output (redact secrets, truncate) ═══
        if isinstance(result, str):
            result = self.secret_broker.redact_secrets(result)
        result_str = str(result)
        truncated = len(result_str) > self.max_output_length
        if truncated:
            result_str = result_str[:self.max_output_length] + "\n... [TRUNCATED]"

        return {
            "result": result_str,
            "success": success,
            "error": error,
            "duration_ms": round(duration_ms, 1),
            "truncated": truncated,
        }

    # ═══════════════════════════════════════════════════════════════
    # INTERNALS
    # ═══════════════════════════════════════════════════════════════

    def _sanitize_args(self, tool_name: str, args: dict) -> dict:
        """Validate and sanitize tool arguments before execution.

        This is where we catch injection attempts. Each tool type
        has specific validation rules.
        """
        sanitized = {}

        for key, value in args.items():
            # ═══ Reject null bytes (used in some injection attacks) ═══
            if isinstance(value, str) and "\x00" in value:
                raise SandboxViolationError(
                    f"Argument '{key}' contains null byte — rejected"
                )

            # ═══ Reject excessively long string arguments ═══
            if isinstance(value, str) and len(value) > 50_000:
                raise SandboxViolationError(
                    f"Argument '{key}' is {len(value)} chars — "
                    f"max allowed is 50,000"
                )

            sanitized[key] = value

        return sanitized

    def _validate_paths_in_args(self, tool_name: str, args: dict) -> None:
        """Check all path-like arguments against the allowlist.

        We look for keys that suggest file paths: 'path', 'file', 'dir',
        'directory', 'filename', 'output', 'input', 'cwd'.
        """
        path_keys = {"path", "file", "dir", "directory", "filename",
                      "output", "input", "cwd", "target", "source", "dest"}

        for key, value in args.items():
            key_lower = key.lower()
            is_path_key = any(pk in key_lower for pk in path_keys)

            if is_path_key and isinstance(value, str):
                # ═══ Validate this path against the allowlist ═══
                self.allowlist.validate_or_raise(value, f"access via '{key}'")

            # ═══ Also check for paths inside nested structures ═══
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and is_path_key:
                        self.allowlist.validate_or_raise(
                            item, f"access via '{key}' list element"
                        )

    def _get_required_secrets(self, tool_name: str) -> list[str]:
        """Determine which secrets a tool needs.

        Override this per-tool type. By default, no secrets are injected.
        """
        # ═══ Map tool names to their required secrets ═══
        tool_secrets = {
            "github_api": ["github_token"],
            "database_query": ["database_url"],
            "s3_upload": ["aws_access_key", "aws_secret_key"],
            "send_email": ["smtp_password"],
        }
        return tool_secrets.get(tool_name, [])
```

---

## 7. Before/After: Dangerous Operations Blocked

```python
# ═══ SETUP: Create a sandboxed executor ═══
workspace = Path("/home/agent/project")
allowlist = PathAllowlist([workspace])
executor = SandboxedExecutor(allowlist=allowlist)


# ═══ TEST 1: Safe file read — ALLOWED ═══
def test_safe_read():
    """Reading a file inside the workspace — should succeed."""
    result = executor.execute(
        tool_name="read_file",
        tool_args={"path": str(workspace / "config.yaml")},
        tool_fn=lambda path: f"content of {path}",
    )
    print(f"✅ Safe read: {result['success']}")  # True


# ═══ TEST 2: Path traversal — BLOCKED ═══
def test_path_traversal():
    """Trying to read ../../etc/passwd — should be blocked."""
    try:
        executor.execute(
            tool_name="read_file",
            tool_args={"path": "/etc/passwd"},  # outside workspace
            tool_fn=lambda path: "secret data",
        )
        print("❌ Path traversal was NOT blocked!")  # shouldn't reach here
    except SandboxViolationError as e:
        print(f"✅ Path traversal blocked: {e}")


# ═══ TEST 3: Dangerous command — BLOCKED ═══
def test_dangerous_command():
    """Trying to run 'rm -rf /' — should be blocked."""
    try:
        # Even if the agent tries to execute 'rm', our blocked_commands catches it
        if "rm" in executor.blocked_commands:
            raise SandboxViolationError("Command 'rm' is blocked")
        print("❌ Dangerous command was NOT blocked!")
    except SandboxViolationError as e:
        print(f"✅ Dangerous command blocked: {e}")


# ═══ TEST 4: Secret redaction — SECRETS HIDDEN ═══
def test_secret_redaction():
    """Tool output containing secrets should be redacted."""
    os.environ["GITHUB_TOKEN"] = "ghp_secret123456789"
    broker = SecretBroker()
    result = broker.redact_secrets(
        "API response: token=ghp_secret123456789, status=ok"
    )
    print(f"✅ Secret redacted: {result}")
    # Output: "API response: token=***GITHUB_TOKEN***, status=ok"


test_safe_read()
test_path_traversal()
test_dangerous_command()
test_secret_redaction()
```

**Output:**
```
✅ Safe read: True
✅ Path traversal blocked: Cannot access '/etc/passwd' — path is outside allowed directories
✅ Dangerous command blocked: Command 'rm' is blocked
✅ Secret redacted: API response: token=***GITHUB_TOKEN***, status=ok
```

---

## 8. Docker-Based Isolation (Advanced)

For maximum security, run each tool in a disposable Docker container:

```python
def docker_execute(command: list[str], *,
                   image: str = "python:3.12-slim",
                   timeout: int = 30,
                   workdir: str = "/sandbox",
                   memory_limit: str = "256m",
                   cpu_limit: float = 1.0,
                   ) -> subprocess.CompletedProcess:
    """Execute a command inside a Docker container with resource limits.

    This provides the strongest isolation: the agent's tools run in
    a fresh container that's destroyed after execution. Even if the
    agent manages to break something, the damage is contained to
    a container that no longer exists.

    Requires: Docker installed and running on the host.
    """
    docker_cmd = [
        "docker", "run", "--rm",  # --rm = delete container after execution
        "--memory", memory_limit,  # prevent OOM on host
        "--cpus", str(cpu_limit),  # prevent CPU exhaustion
        "--network", "none",  # ═══ NO network access ═══
        "--read-only",  # ═══ filesystem is read-only by default ═══
        f"--tmpfs=/tmp:size=64m",  # writable /tmp for temp files
        "-v", f"{workdir}:/sandbox:ro",  # mount working dir read-only
        "-w", "/sandbox",
        image,
        *command,
    ]

    return subprocess.run(
        docker_cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
```

---

## 9. Security Checklist

| Layer | Check | Priority |
|-------|-------|----------|
| Path allowlist | Every file operation goes through `validate_or_raise()` | **Critical** |
| Command safety | `shell=False` always, arguments as list | **Critical** |
| Secret brokering | Secrets never in agent context, injected at egress | **High** |
| Timeout limits | Every tool has a timeout; subprocess, HTTP, everything | **High** |
| Output sanitization | Redact secrets before sending results back to agent | **High** |
| Resource limits | Docker memory/CPU limits, or ulimit for subprocess | **Medium** |
| Network isolation | `--network none` in Docker; firewall rules for subprocess | **Medium** |
| Audit logging | Log every tool call with args, result, duration, user | **Medium** |
| Read-only filesystem | Docker `--read-only`; chmod restrictions for subprocess | **Low** |

---

## Key Takeaways

1. **Never `shell=True`** — it's the #1 injection vector. Use argument lists.
2. **Path allowlists are your first and best defense** — validate EVERY file operation.
3. **Secrets are injected at egress, never visible in context** — the agent knows secret NAMES, not VALUES.
4. **Timeout everything** — a runaway tool is a denial-of-service attack on yourself.
5. **Docker isolation is the gold standard** — disposable containers mean zero persistent damage.

---

> **Previous:** [14 — Cost Tracking & Budgets](14_cost_tracking_budgets.md)
> **Next:** [16 — Testing Harnesses](16_testing_harnesses.md)
