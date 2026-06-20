# Chapter 05: Policies & Governance

## The Control Pillar

Omnigent's policy system is what separates it from running agent CLIs directly. Policies are **declarative guardrails** that evaluate agent actions and return verdicts — no prompt engineering, no "please don't do X" begging. They're code, enforced at the meta-harness layer.

## Policy Verdicts

Every policy returns exactly one of:

| Verdict | Effect | Agent sees |
|---|---|---|
| **ALLOW** | Action proceeds normally | Nothing — transparent |
| **DENY** | Action blocked | Error message: "Action denied by policy: <reason>" |
| **ASK** | Action paused, user prompted | Waiting for approval message |

## Policy Composition

Multiple policies can be active at once. They're evaluated in **declaration order**, and **a DENY from any policy short-circuits the rest**:

```
Policy 1 (session):  ALLOW  → continue to next
Policy 2 (session):  ALLOW  → continue to next
Policy 3 (agent):    ASK    → user approves → continue
Policy 4 (server):   DENY   → BLOCKED (short-circuit)
```

## Three Evaluation Levels

Policies stack across three levels:

| Level | Who sets it | How | Evaluated |
|---|---|---|---|
| **Session** | End user | UI settings panel | **First** (can short-circuit everything) |
| **Agent** | Agent developer | `policies:` in agent YAML | Middle |
| **Server** | Admin | Server config YAML or REST API | Last |

**Why this order?** Session policies evaluate first so the user can always add restrictions (e.g., "cap my spend at $2 for this chat"). Agent policies define what the agent developer considers safe defaults. Server policies are the admin's floor — the minimum safety bar that no session or agent can lower.

## Policy Declaration Syntax

Every policy uses the same schema:

```yaml
policy_name:
  type: function              # always "function" currently
  handler: dotted.path.to.handler   # Python import path
  factory_params:             # optional: pass to factory at build time
    key: value
```

### Direct Callable (no params)

```yaml
approve_file_ops:
  type: function
  handler: omnigent.policies.builtins.safety.ask_on_os_tools
```

### Factory (with params)

```yaml
rate_limit:
  type: function
  handler: omnigent.policies.builtins.safety.max_tool_calls_per_session
  factory_params:
    limit: 50
```

## Built-in Policies — Complete Catalog

### Safety

#### `max_tool_calls_per_session`
Limits total tool calls. DENY after limit reached.

| Param | Type | Default | Description |
|---|---|---|---|
| `limit` | int | 100 | Max tool calls allowed |

```yaml
rate_limit:
  type: function
  handler: omnigent.policies.builtins.safety.max_tool_calls_per_session
  factory_params:
    limit: 50
```

#### `ask_on_os_tools`
Requires user approval before any `sys_os_read`, `sys_os_write`, `sys_os_edit`, or `sys_os_shell` call.

```yaml
approve_all_os:
  type: function
  handler: omnigent.policies.builtins.safety.ask_on_os_tools
```

No parameters. Every OS tool call pauses for approval.

#### `block_skills`
Prevents the agent from loading specific skills.

| Param | Type | Default | Description |
|---|---|---|---|
| `blocked` | string[] | (required) | Skill names to block (case-insensitive) |

```yaml
no_deploy_skill:
  type: function
  handler: omnigent.policies.builtins.safety.block_skills
  factory_params:
    blocked: [deploy, rollback, destroy]
```

#### `enforce_sandbox`
Forces a specific sandbox configuration on agent start.

| Param | Type | Default | Description |
|---|---|---|---|
| `sandbox_type` | string | (required) | `linux_bwrap`, `darwin_seatbelt`, or `none` |
| `write_paths` | string[] | `[]` | Allowed write paths |
| `allow_network` | bool | `false` | Allow network access? |

```yaml
force_sandbox:
  type: function
  handler: omnigent.policies.builtins.safety.enforce_sandbox
  factory_params:
    sandbox_type: linux_bwrap
    write_paths: [./output]
    allow_network: false
```

### Cost Control

#### `cost_budget`
Hard spend cap with soft warning thresholds.

| Param | Type | Default | Description |
|---|---|---|---|
| `max_cost_usd` | float | (required) | Hard cap — DENY when exceeded |
| `ask_thresholds_usd` | float[] | `[]` | Soft warnings — ASK at each threshold |

```yaml
budget:
  type: function
  handler: omnigent.policies.builtins.cost.cost_budget
  factory_params:
    max_cost_usd: 10.00
    ask_thresholds_usd: [5.00, 8.00]   # ask at $5 and $8
```

**Behavior:**
- Below first threshold: silent ALLOW
- At each threshold: ASK ("You've spent $5.00. Continue?")
- At max: DENY ("Budget of $10.00 exceeded. Session blocked.")

#### `cost_per_turn`
Limits the cost of a single model turn.

| Param | Type | Default | Description |
|---|---|---|---|
| `max_cost_usd` | float | (required) | Max cost per turn |

### Service-Specific

#### `github_policy`

| Param | Type | Default | Description |
|---|---|---|---|
| `read_repos` | string[] | `[]` | Repos agent may read |
| `write_repos` | string[] | `[]` | Repos agent may write to |
| `write_branches` | string[] | `["*"]` | Branch patterns for writes |

```yaml
github_guard:
  type: function
  handler: omnigent.policies.builtins.github.github_policy
  factory_params:
    read_repos: [myorg/*]
    write_repos: [myorg/my-repo]
    write_branches: ["feature/*", "fix/*"]
```

#### `gdrive_policy`
Controls Google Drive access.

| Param | Type | Default | Description |
|---|---|---|---|
| `read_all` | bool | `false` | Can read any file? |
| `allow_create` | bool | `false` | Can create files? |
| `allow_delete` | bool | `false` | Can delete files? |

## Guardrails (Runner-Level Enforcement)

Guardrails are like policies but enforced at the **runner** level — before the policy engine:

```yaml
guardrails:
  ask_timeout: 86400    # ASK approvals valid for 24 hours

  policies:
    blast_radius:
      type: function
      function:
        path: omnigent.inner.nessie.policies.blast_radius
        arguments:
          gate_pushes: false    # don't ASK on git push
                                # (but still DENY force-push, rm -rf /, hard-reset)

    spawn_bounds:
      type: function
      function:
        path: omnigent.inner.nessie.policies.spawn_bounds
        arguments:
          max_dispatches_per_turn: 5
          dispatch_tools: [sys_session_send, sys_session_create]

    headless_subagent_purpose_guard:
      type: function
      function:
        path: omnigent.inner.nessie.policies.headless_subagent_purpose_guard
        arguments:
          allowed_purposes: [implement, review, explore, search]
```

### Blast Radius Policy

The blast radius policy protects against catastrophic operations:

| Operation | Default | Customizable |
|---|---|---|
| `rm -rf /` | DENY | No |
| `git push --force` | DENY | No |
| `git reset --hard <remote-ref>` | DENY | No |
| Regular `git push` | ASK (if `gate_pushes: true`) | Yes |
| Regular `git merge` | ASK (if `gate_pushes: true`) | Yes |

## Real-World Examples

### Example 1: Tight Budget for a Coding Session

```yaml
# In agent.yaml
policies:
  budget:
    type: function
    handler: omnigent.policies.builtins.cost.cost_budget
    factory_params:
      max_cost_usd: 2.00
      ask_thresholds_usd: [1.00]

  safe_ops:
    type: function
    handler: omnigent.policies.builtins.safety.ask_on_os_tools

  no_deploy:
    type: function
    handler: omnigent.policies.builtins.safety.block_skills
    factory_params:
      blocked: [deploy, provision, destroy]
```

**Effect:** Agent can still code, but every file/shell operation pauses for approval, costs are capped at $2, and deploy skills are blocked.

### Example 2: Server-Wide Floor for a Team

```yaml
# In server_config.yaml (set by admin)
policies:
  team_budget:
    type: function
    handler: omnigent.policies.builtins.cost.cost_budget
    factory_params:
      max_cost_usd: 50.00
      ask_thresholds_usd: [25.00, 40.00]

  team_rate_limit:
    type: function
    handler: omnigent.policies.builtins.safety.max_tool_calls_per_session
    factory_params:
      limit: 200

  team_sandbox:
    type: function
    handler: omnigent.policies.builtins.safety.enforce_sandbox
    factory_params:
      sandbox_type: linux_bwrap
      write_paths: [./output, /tmp]
      allow_network: true
```

**Effect:** No agent on this server can exceed $50/session, 200 tool calls, or run unsandboxed. Individual agents can add *stricter* limits but not *looser* ones.

### Example 3: Session-Level Override (User)

Via the web UI or chat:
```
you: add a policy that caps my spend at $3 and asks me before any shell command
```

The agent calls `sys_add_policy` to add session-level policies:
```yaml
user_cap:
  type: function
  handler: omnigent.policies.builtins.cost.cost_budget
  factory_params:
    max_cost_usd: 3.00
    ask_thresholds_usd: [1.50]

user_approve_shell:
  type: function
  handler: omnigent.policies.builtins.safety.ask_on_os_tools
```

**Effect:** Even if the agent and server allow higher limits, the session policies evaluate first and enforce the user's tighter caps.

## Adding Custom Policies

Custom policies are Python modules that Omnigent imports:

```python
# my_policies.py
from omnigent.policies.base import Policy, PolicyVerdict

class CustomPolicy(Policy):
    """My custom guardrail."""

    def __init__(self, blocked_domains: list[str]):
        self.blocked_domains = set(blocked_domains)

    async def evaluate(self, action, context):
        if action.type == "sys_os_shell":
            # Check if the command tries to access blocked domains
            cmd = action.data.get("command", "")
            for domain in self.blocked_domains:
                if domain in cmd:
                    return PolicyVerdict.DENY(
                        reason=f"Command references blocked domain: {domain}"
                    )
        return PolicyVerdict.ALLOW()
```

Register in server config:
```yaml
# server_config.yaml
policy_modules:
  - my_policies

policies:
  domain_guard:
    type: function
    handler: my_policies.CustomPolicy
    factory_params:
      blocked_domains: [production.internal, staging.secrets]
```

## Summary

Omnigent's policy system gives you governance that:
- **Composes** — multiple policies stack, DENY short-circuits
- **Scales** — session → agent → server, each more permissive layer can only tighten
- **Is declarative** — no prompt-based begging, no "system prompt jailbreaking"
- **Is extensible** — custom Python policies for any domain

The key pattern: **server sets the floor, agent sets safe defaults, user tightens further.**

---

**Previous:** [Chapter 04 — Agent YAML Specification](./04_agent_yaml_spec.md)
**Next:** [Chapter 06 — Sandbox & Security Model](./06_sandbox_and_security.md)
