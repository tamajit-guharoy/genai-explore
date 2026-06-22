# Omnigent Compatibility Matrix

> **Key insight:** Omnigent has two harness layers — SDK harnesses that route through Omnigent's own tool system, and native/CLI harnesses that bring their own tool systems. `os_env` sandboxing and tool-level policies only apply where Omnigent controls the tool execution path. The `tools:` block (custom functions, MCP, sub-agents) is translated by Omnigent for each harness and works everywhere.

---

## 1. os_env / Omnibox Sandbox

`os_env` controls Omnigent's built-in `sys_os_*` tools (`sys_os_read`, `sys_os_write`, `sys_os_edit`, `sys_os_shell`) and terminals declared in the `terminals:` config block. It does **NOT** control harness-native tool systems.

| Harness | Tool system | `os_env` applies? |
|---|---|---|
| `claude-sdk` | Omnigent `sys_os_*` | **YES** |
| `openai-agents` | Omnigent `sys_os_*` | **YES** |
| `codex` (SDK) | Omnigent `sys_os_*` | **YES** |
| `antigravity` | Gemini native function calling | **NO** |
| `claude-native` | Claude Code CLI tools (Bash, Read, Write, Edit) | **NO** |
| `codex-native` | Codex CLI tools | **NO** |
| `pi` | Pi CLI tools | **NO** |
| `cursor` | Cursor CLI tools | **NO** |

**In practice:**
- Omitting `os_env` with `claude-sdk` → agent has **zero** filesystem/shell access
- Omitting `os_env` with `antigravity`/`claude-native`/etc. → agent **can still** read/write files via its native tools

---

## 2. Policies / Guardrails

Three categories based on what they intercept:

### Omnigent-layer — **ALL harnesses**

Intercept at Omnigent's own abstraction layer (token gateway, skill registry). Harness type is irrelevant.

| YAML key | Handler | Coverage |
|---|---|---|
| `budget` | `omnigent.policies.builtins.cost.cost_budget` | **ALL 8 harnesses** |
| `no_destructive` | `omnigent.policies.builtins.safety.block_skills` | **ALL 8 harnesses** |

### Tool-level (under `policies:`) — **SDK harnesses only**

Intercept individual `sys_os_*` tool calls. Harness-native tools bypass this path.

| YAML key | Handler | SDK (3) | Native (5) |
|---|---|---|---|
| `approve_ops` | `omnigent.policies.builtins.safety.ask_on_os_tools` | **YES** | **NO** |
| `rate_limit` | `omnigent.policies.builtins.safety.max_tool_calls_per_session` | **YES** | **NO** |

### Runner-level (under `guardrails:`) — **SDK harnesses only**

Enforced below the policy stack. Cannot be bypassed. Same `sys_os_*` interception path.

| YAML key | Handler | SDK (3) | Native (5) |
|---|---|---|---|
| `blast_radius` | `omnigent.inner.nessie.policies.blast_radius` | **YES** | **NO** |

> **Note:** `blast_radius` lives under `guardrails:` (not `policies:`) — see example 26. It's runner-level, always-on, and still gates `sys_os_*` calls only.

---

## 3. Tools (`tools:` block)

The `tools:` block declares custom tools — Python functions, MCP servers, sub-agents, containers. Omnigent translates these into the appropriate format for each harness, making `tools:` **genuinely harness-agnostic**.

> *"Tools, policies, and other config stay the same across harnesses. Just change the `harness` value."* — Omnigent harnesses doc

| Tool type | SDK harnesses | Native/PTY harnesses | antigravity |
|---|---|---|---|
| `function` (Python) | Omnigent executes callable, returns result | Omnigent executes, pipes result back to CLI | Registered as Gemini function declaration |
| `mcp` (local stdio) | Omnigent spawns server, proxies to model | Omnigent spawns, registers with CLI's MCP config | Registered as Gemini tool |
| `mcp` (remote HTTP/SSE) | Proxied | Proxied | Proxied |
| `agent` (sub-agent) | Omnigent-managed sub-session | Omnigent-managed sub-session | Omnigent-managed sub-session |
| `container` | Docker container tool | Docker container tool | Docker container tool |

**Coverage: ALL 8 harnesses** — Omnigent owns the translation layer.

---

## 4. Full Compatibility Matrix

```
                     os_env    budget   no_       approve_  rate_    blast_    tools:
                     sandbox            destr     ops       limit    radius    block
                     ───────   ──────   ───────   ────────  ──────   ──────    ─────
claude-sdk           ✓ YES     ✓ YES    ✓ YES     ✓ YES     ✓ YES    ✓ YES     ✓ YES
openai-agents        ✓ YES     ✓ YES    ✓ YES     ✓ YES     ✓ YES    ✓ YES     ✓ YES
codex (SDK)          ✓ YES     ✓ YES    ✓ YES     ✓ YES     ✓ YES    ✓ YES     ✓ YES
antigravity          ✗ NO      ✓ YES    ✓ YES     ✗ NO      ✗ NO     ✗ NO      ✓ YES
claude-native        ✗ NO      ✓ YES    ✓ YES     ✗ NO      ✗ NO     ✗ NO      ✓ YES
codex-native         ✗ NO      ✓ YES    ✓ YES     ✗ NO      ✗ NO     ✗ NO      ✓ YES
pi                   ✗ NO      ✓ YES    ✓ YES     ✗ NO      ✗ NO     ✗ NO      ✓ YES
cursor               ✗ NO      ✓ YES    ✓ YES     ✗ NO      ✗ NO     ✗ NO      ✓ YES
```

---

## 5. Summary: What works where?

| YAML block | SDK harnesses (3) | Native harnesses (5) | Why the difference? |
|---|---|---|---|
| `os_env` / sandbox | ✓ Full control | ✗ No effect | Only gates `sys_os_*` tools |
| `tools:` block | ✓ Full support | ✓ Full support | Omnigent translates per-harness |
| Omnigent-layer policies | ✓ Full support | ✓ Full support | Skill registry + token gateway sit above harness |
| Tool-level policies (`policies:`) | ✓ Full support | ✗ No effect | Intercept `sys_os_*` calls only |
| Runner-level guardrails (`guardrails:`) | ✓ Full support | ✗ No effect | Intercept `sys_os_*` calls only |
| `terminals:` block | ✓ Full support | ✓ Full support | Omnigent-managed PTY sessions |

---

## 6. How to Lock Down Native Harnesses

Since `os_env`, tool-level policies, and runner-level guardrails don't apply to native harnesses, use harness-side controls:

| Harness | Lockdown options |
|---|---|
| `antigravity` | Gemini safety settings, Google AI Studio content filters |
| `claude-native` | Claude Code permissions (`/permissions`), `.claude/settings.json` |
| `codex-native` | Codex sandbox (Seatbelt/Bubblewrap), `/permissions` |
| `pi` | Pi's own tool restrictions |
| `cursor` | Cursor agent permissions, `CURSOR_API_KEY` scoping |

Or switch to an SDK harness (`claude-sdk`, `openai-agents`, `codex`) for full Omnigent guardrail + sandbox coverage.

---

## 7. Source References

- **Omnigent OS Sandbox docs:** "The OS sandbox applies to the built-in OS tools (`sys_os_read`, `sys_os_write`, `sys_os_edit`, `sys_os_shell`) and any terminals you declare in the agent config."
- **Omnigent Tools docs:** Documents `function`, `mcp`, `agent` tool types with no harness restrictions stated
- **Omnigent Harnesses doc:** "Tools, policies, and other config stay the same across harnesses."
- **GitHub README:** Same `tools:` block shown with comment `# or: codex, codex-native, claude-native, cursor, openai-agents, pi, antigravity`
- **Example 13 (`13_os_no_access.yaml`):** "Omitting `os_env:` entirely → no OS tools" (specific to `claude-sdk`)
- **Example 24 (`24_policy_shell_approval.yaml`):** Uses `approve_file_ops` key, gates `sys_os_*` tools
- **Example 26 (`26_policies_combined_governance.yaml`):** Uses canonical short names `approve_ops` and `no_destructive`; separates `policies:` from `guardrails:` (blast_radius)

---

*Generated from analysis of Omnigent v0.2.0 docs, standalone examples (41 files), OS sandbox documentation, and tools documentation.*
