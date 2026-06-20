# Appendix B: Reference Tables

## Omnigent Harnesses — Complete Reference

| Harness ID | Transport | Requires CLI? | Model Resolution | Notes |
|---|---|---|---|---|
| `claude-sdk` | Anthropic Python SDK | No | `ANTHROPIC_API_KEY` or Databricks | Recommended for Claude |
| `openai-agents` | OpenAI Python SDK | No | `OPENAI_API_KEY` | For GPT-native workflows |
| `claude-native` | PTY (tmux) | Yes (`claude`) | Claude subscription or API key | Full Claude Code experience |
| `codex-native` | PTY (tmux) | Yes (`codex`) | Codex subscription or API key | Full Codex CLI experience |
| `codex` | OpenAI Python SDK | No | `OPENAI_API_KEY` | SDK-based Codex (may also refer to Codex CLI) |
| `cursor` | Proprietary | Yes (`cursor-agent`) | `CURSOR_API_KEY` | No Databricks gateway support |
| `antigravity` | Google Antigravity SDK | No (`pip install omnigent[antigravity]`) | `GEMINI_API_KEY` or Vertex AI | For Gemini models |
| `pi` | PTY (tmux) or SDK | Yes (`pi` for native) | Multi-model | Exploration-focused |

## Omnigent Agent YAML — Top-Level Fields

| Field | Type | Required? | Default | Description |
|---|---|---|---|---|
| `name` | string | Recommended | — | Stable identifier |
| `description` | string | No | — | Human-readable description |
| `spec_version` | int | No | — | Schema version (currently 1) |
| `prompt` | string | Usually | — | Inline system prompt |
| `instructions` | string | No | — | Path to external instructions (wins over `prompt`) |
| `executor` | object | Recommended | — | Harness, model, auth |
| `tools` | object | No | — | MCP servers, functions, sub-agents |
| `policies` | object | No | — | Agent-level guardrails |
| `params` | object | No | — | Typed user parameters |
| `os_env` | object | No | — | OS tools + sandbox config |
| `terminals` | object | No | — | Named interactive shells |
| `async` | bool | No | `true` | Async work tools |
| `cancellable` | bool | No | `true` | Session cancellation |
| `timers` | bool | No | `false` | Timer tools |
| `spawn` | bool | No | `false` | Spawn child sessions |
| `guardrails` | object | No | — | Runner-level enforcement |

## Omnigent Built-in Policies — Quick Reference

| Policy | Handler | Params | Verdict |
|---|---|---|---|
| **Cost budget** | `omnigent.policies.builtins.cost.cost_budget` | `max_cost_usd`, `ask_thresholds_usd` | ALLOW below threshold, ASK at threshold, DENY at cap |
| **Cost per turn** | `omnigent.policies.builtins.cost.cost_per_turn` | `max_cost_usd` | DENY if single turn exceeds limit |
| **Tool call limit** | `omnigent.policies.builtins.safety.max_tool_calls_per_session` | `limit` (default: 100) | DENY after limit reached |
| **Shell approval** | `omnigent.policies.builtins.safety.ask_on_os_tools` | None | ASK on every `sys_os_*` call |
| **Block skills** | `omnigent.policies.builtins.safety.block_skills` | `blocked` (string[]) | DENY loading blocked skills |
| **Enforce sandbox** | `omnigent.policies.builtins.safety.enforce_sandbox` | `sandbox_type`, `write_paths`, `allow_network` | DENY if agent sandbox doesn't match |
| **GitHub guard** | `omnigent.policies.builtins.github.github_policy` | `read_repos`, `write_repos`, `write_branches` | DENY unauthorized GitHub ops |
| **Google Drive** | `omnigent.policies.builtins.google.gdrive_policy` | `read_all`, `allow_create`, `allow_delete` | DENY unauthorized Drive ops |

## Omnigent Guardrails

| Guardrail | Path | Purpose |
|---|---|---|
| **Blast radius** | `omnigent.inner.nessie.policies.blast_radius` | Always DENY: force-push, `rm -rf /`, hard-reset. Configurable ASK: push, merge, publish |
| **Spawn bounds** | `omnigent.inner.nessie.policies.spawn_bounds` | Limit sub-agent dispatches per turn |
| **Purpose guard** | `omnigent.inner.nessie.policies.headless_subagent_purpose_guard` | Restrict sub-agent purposes to allowlist |

## Omnigent Sandbox Backends

| Backend | Platform | Install | Features |
|---|---|---|---|
| `none` | All | None | Unsandboxed; agent has full user permissions |
| `linux_bwrap` | Linux | `apt install bubblewrap` | Linux namespaces; write_paths, read_paths, network toggle |
| `darwin_seatbelt` | macOS | Built-in | macOS Seatbelt sandbox; write_paths, read_paths, network toggle |
| Managed: `modal` | Cloud | Provisioned by Omnigent | Ephemeral VM; max isolation |
| Managed: `daytona` | Cloud | Provisioned by Omnigent | Ephemeral VM; max isolation |
| Managed: `islo` | Cloud | Provisioned by Omnigent | Ephemeral VM; max isolation |

## Omnigent Auth Types

| Auth Type | Use Case | Config |
|---|---|---|
| `databricks` | Databricks workspace routing | `profile: oss` |
| `api_key` | Direct API key | `api_key: ${VAR}` |
| `provider` | Named provider from config | `name: my-provider` |
| (omitted) | Environment auto-detect | Picks up `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc. |

## Stanford Meta-Harness — Reference Experiments

| Experiment | Domain | Harness Controls | Key Discovery | Improvement |
|---|---|---|---|---|
| **Text Classification** | Online classification with memory | Retrieval strategy, memory eviction, context assembly | Label-Primed Query (two-step) | +7.7 pts (48.6% vs 40.9%) |
| **TerminalBench 2.0** | Agentic coding | Environment bootstrapping, observation formatting, error recovery | Environment bootstrapping, structured observation, error hints | +11 pts (Opus 4.6), #1 Haiku-based, #2 overall |
| **Math Reasoning** | IMO-level with retrieval | Retrieval routing, deduplication, reranking | Subject-specific retrieval policies | +4.7 pts avg across 5 models |

## Stanford Meta-Harness — Proposer Details

| Aspect | Paper Value |
|---|---|
| Proposer model | 120B open-source model |
| Proposer wrapper | `claude_wrapper.py` (Claude Code) |
| Search iterations | 10-50 (varies by experiment) |
| Tasks per evaluation | 20-50 |
| History format | Filesystem: `candidate_N/harness.py`, `score.json`, `traces/*.json` |
| Proposer tools | `grep`, `cat`, `ls` — terminal tools on the search history filesystem |

## Omnigent CLI Commands

| Command | Purpose |
|---|---|
| `omni` | Start Omnigent (TUI + web UI) |
| `omni --tui` | Force TUI mode |
| `omni setup` | Interactive credential + model setup |
| `omni claude` | Launch Claude Code in Omnigent session |
| `omni codex` | Launch Codex in Omnigent session |
| `omni run agent.yaml` | Run custom agent |
| `omni debby` | Launch Debby (two-headed brainstorming) |
| `omni polly` | Launch Polly (multi-agent coding orchestrator) |
| `omni server start` | Start server in background |
| `omni server stop` | Stop server |
| `omni server status` | Check server status |
| `omni upgrade` | Upgrade Omnigent |
| `omni upgrade --check` | Check for newer version |
| `omni doctor` | (planned) Diagnose configuration issues |

## Omnigent Configuration Files

| File | Location | Contents |
|---|---|---|
| `config.yaml` | `~/.omnigent/` | Providers, default model, UI settings |
| `.env` | `~/.omnigent/` | API keys and secrets |
| `chat.db` | `~/.omnigent/` | SQLite database: sessions, messages, files |
| `local_server.pid` | `~/.omnigent/` | Running server PID |
| `local_server.sig` | `~/.omnigent/` | Version + auth signature (for upgrade detection) |

---

**Previous:** [Appendix A — Omnigent vs. Meta-Harness](./A_omnigent_vs_meta_harness.md)
**Next:** [Appendix C — Glossary](./C_glossary.md)
