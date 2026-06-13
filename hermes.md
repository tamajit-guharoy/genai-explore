# Hermes Agent Tutorial

> **Hermes Agent** is an open-source, self-hosted autonomous AI agent by [Nous Research](https://nousresearch.com), released in February 2026. Its tagline — *"the agent that grows with you"* — captures its core idea: a **single persistent agent** with memory and skills that improve the longer you use it, reachable from your terminal and 20+ messaging platforms.
>
> - GitHub: <https://github.com/nousresearch/hermes-agent>
> - Docs: <https://hermes-agent.nousresearch.com/docs/>
> - Website: <https://hermes-agent.org/>

---

## Table of Contents

1. [What Makes Hermes Different](#1-what-makes-hermes-different)
2. [Installation](#2-installation)
3. [First-Time Setup](#3-first-time-setup)
4. [Basic Usage: CLI and TUI](#4-basic-usage-cli-and-tui)
5. [Slash Commands](#5-slash-commands)
6. [Persistent Memory](#6-persistent-memory)
7. [Skills: The Learning Loop](#7-skills-the-learning-loop)
8. [Built-in Tools](#8-built-in-tools)
9. [Messaging Gateway (Telegram, Discord, Slack, WhatsApp…)](#9-messaging-gateway)
10. [Scheduled Automations (Cron)](#10-scheduled-automations-cron)
11. [Subagents and Parallel Work](#11-subagents-and-parallel-work)
12. [Personalities](#12-personalities)
13. [Configuration Reference](#13-configuration-reference)
14. [Model Providers](#14-model-providers)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. What Makes Hermes Different

Most AI assistants are **session-bound**: close the window and everything is forgotten. Hermes is built around three persistence mechanisms:

| Mechanism | What it stores | How it grows |
|---|---|---|
| **Memory** | Your preferences, projects, environment, facts about you | Agent-curated after conversations; recalled across sessions |
| **Skills** | *Procedural* knowledge — "how to do X" documents | Auto-created after the agent solves a hard problem; self-improve with reuse |
| **User model** | A long-term picture of who you are (via Honcho integration) | Refined continuously across every session |

The result: ask Hermes to "do the weekly report" in month three, and it already knows your data sources, your formatting preferences, and the three edge cases that broke it in month one.

**Key features at a glance:**

- 🧠 Persistent, inspectable memory across sessions (SQLite + FTS5 full-text search with LLM summarization)
- 📚 Self-improving skills, compatible with the [agentskills.io](https://agentskills.io) open standard
- 💬 One gateway → Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and more — with voice-memo transcription and cross-platform conversation continuity
- ⏰ Built-in cron scheduler for unattended tasks (daily reports, backups, monitors)
- 🔀 Isolated subagents for parallel workstreams
- 🔌 30+ model providers (Anthropic, OpenAI, OpenRouter, Gemini, Bedrock, Ollama, LM Studio, custom endpoints…)
- 🖥️ Two terminal UIs: a classic CLI and a modern TUI with mouse support and streaming tool output
- 🆓 Self-hosted, open source, free forever

---

## 2. Installation

**Requirements:** Linux, macOS, WSL2, or Android (Termux); native Windows via PowerShell or the Desktop app. Your chosen model must support **at least 64,000 tokens of context** — smaller windows can't sustain multi-step tool-calling. Claude, GPT, Gemini, Qwen, and DeepSeek hosted models all qualify.

### Linux / macOS / WSL2 / Termux

```bash
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
source ~/.bashrc   # or: source ~/.zshrc
```

The installer handles all prerequisites automatically — no Python/venv juggling required.

### Windows (native PowerShell)

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

### Desktop App (macOS / Windows)

Download the installer from <https://hermes-agent.nousresearch.com/desktop> — the recommended route for non-terminal users.

### Verify and update

```bash
hermes doctor    # diagnose configuration issues
hermes update    # upgrade to the latest version
```

---

## 3. First-Time Setup

Run the setup wizard once:

```bash
hermes setup
```

It walks you through choosing a model provider, entering API keys, and configuring tool access.

**Example: quick setup with Anthropic**

```bash
hermes model                                          # interactive provider picker
# — or set it directly:
hermes config set model anthropic/claude-opus-4.6
hermes config set ANTHROPIC_API_KEY sk-ant-...
```

**Example: quick setup with Nous Portal** (Nous Research's hosted models)

```bash
hermes setup --portal
```

**Example: free/local setup with Ollama**

```bash
hermes config set model ollama/qwen3:32b   # any local model with ≥64k context
```

Configuration lands in two files:

| File | Contents |
|---|---|
| `~/.hermes/.env` | Secrets — API keys, bot tokens |
| `~/.hermes/config.yaml` | Everything else — model, tools, gateway settings |

---

## 4. Basic Usage: CLI and TUI

```bash
hermes              # classic CLI (prompt_toolkit)
hermes --tui        # modern TUI — modal overlays, mouse selection, streaming tool output (recommended)
hermes --continue   # resume your last session
hermes -c           # short form of --continue
```

Both interfaces share the same sessions, slash commands, and config — pick whichever you prefer.

**A first conversation:**

```
you › What's in my ~/projects directory, and which repos have uncommitted changes?

hermes › [tool: terminal] ls ~/projects
         [tool: terminal] for d in ~/projects/*/; do git -C "$d" status --porcelain ...
         You have 6 projects. Two have uncommitted changes:
         • blog-engine — 3 modified files
         • data-pipeline — 1 untracked file
```

**Useful input tricks:**

- **Multi-line input:** `Alt+Enter`, `Ctrl+J`, or `Shift+Enter`
- **Interrupt a running task:** just type a new message
- **Slash-command autocomplete:** type `/` to get a dropdown

---

## 5. Slash Commands

| Command | What it does |
|---|---|
| `/new` | Start a fresh conversation (memory persists; context resets) |
| `/model [provider:model]` | Switch models mid-conversation, e.g. `/model openrouter:deepseek/deepseek-v3` |
| `/personality [name]` | Switch the agent's persona |
| `/retry` | Undo and regenerate the last turn |
| `/skills` | Browse installed skills |
| `/compress` | Compress conversation context when it gets long |

**Example — switching models mid-task:**

```
you › /model anthropic:claude-opus-4-8
hermes › Switched to claude-opus-4-8. Continuing where we left off.
```

---

## 6. Persistent Memory

Hermes maintains **agent-curated memory**: after meaningful exchanges, the agent itself decides what's worth remembering and files it away. Periodic "nudges" prompt it to consolidate. Cross-session recall is powered by SQLite **FTS5 full-text search plus LLM summarization** — Hermes searches past sessions and summarizes the relevant bits into the current context.

**Example — memory in action across sessions:**

```
# Monday
you › I prefer TypeScript over JavaScript, always use pnpm, and my staging
      server is deploy@staging.example.com.
hermes › Noted — saved to memory.

# Thursday (new session, /new)
you › Scaffold a small web API and deploy it to staging.
hermes › Creating a TypeScript project with pnpm... deploying to
         deploy@staging.example.com via SSH...
```

You never re-explained anything — recall is automatic.

**Tips:**

- Ask directly: *"What do you remember about my deployment setup?"*
- Correct it: *"Forget the old staging server, the new one is deploy@stage2.example.com."*
- Memory survives `/new` — a fresh conversation does not mean a fresh brain.

> **Trade-off to know:** Hermes stores episodic memory in SQLite, which is convenient but not as directly human-editable as plain-file approaches (e.g. OpenClaw's markdown memory files). You interact with memory primarily *through the agent*.

---

## 7. Skills: The Learning Loop

Skills are Hermes' signature feature — **procedural memory**. When Hermes solves a hard, multi-step problem, it writes a reusable *skill document* describing how, so it never has to rediscover the solution. Skills then **self-improve during use**: if a step fails on reuse, the agent amends the skill.

Skills follow the **[agentskills.io](https://agentskills.io) open standard**, so they're portable and shareable (the same standard used by Claude Code skills).

### Browsing and installing skills

```bash
hermes skills browse        # browse the community Skills Hub from your terminal
```

Or in-chat:

```
you › /skills
hermes › Installed skills:
         • pdf-invoice-extractor — pull line items from PDF invoices
         • weekly-metrics-report — compile the Monday metrics email
         • hetzner-deploy — deploy a Docker app to my Hetzner box
```

### Example — watching a skill get born

```
# Week 1: the hard way
you › Pull last week's Stripe payouts, reconcile against the invoices
      folder, and flag mismatches.
hermes › [20 minutes of tool calls, two failed approaches, finally success]
         Done — 2 mismatches flagged. This took several non-obvious steps,
         so I've saved a skill: "stripe-invoice-reconciliation".

# Week 2: the easy way
you › Reconcile this week's payouts.
hermes › [uses skill: stripe-invoice-reconciliation]
         Done in 2 minutes — no mismatches this week.
```

### Why this matters

Repeated workflows — daily reports, content pipelines, research loops, data hygiene — get *faster and more reliable over time*. This is the main reason to pick Hermes for long-lived personal automation rather than a stateless assistant.

---

## 8. Built-in Tools

Hermes ships with batteries included:

| Tool | Capability |
|---|---|
| **Terminal** | Run shell commands (sandboxable — see below) |
| **File operations** | Read, write, edit files |
| **Web search** | Search and read the web |
| **Memory** | Store and recall persistent facts |
| **Skills** | Create, search, and execute skills |

Configure what the agent may touch:

```bash
hermes tools                                    # interactive tool-access configuration
hermes config set terminal.backend docker       # run shell commands inside Docker instead of your host
```

> **Security note:** Hermes was designed conservatively after high-profile vulnerabilities in earlier agent runtimes — it documents a **seven-layer security model**. Still, an agent with terminal access is powerful: prefer the Docker terminal backend, scope API keys minimally, and review tool permissions with `hermes tools` before connecting public-facing messaging channels.

---

## 9. Messaging Gateway

One gateway process connects Hermes to **20+ platforms**: Telegram, Discord, Slack, WhatsApp, Signal, Matrix, Email, and more. Highlights:

- **Voice memo transcription** — send a voice note on WhatsApp, get a transcribed-and-answered reply
- **Cross-platform continuity** — start a conversation in the terminal, continue it from Telegram on the train

### Setup

```bash
hermes gateway setup
```

The wizard walks you through per-platform bot creation (e.g. a Telegram bot token from @BotFather) and stores tokens in `~/.hermes/.env`.

**Example — Telegram flow:**

```bash
hermes gateway setup
# › Select platform: Telegram
# › Paste bot token: 7123456789:AAH...
# › Allowed user IDs: 123456789      ← restrict who can talk to your agent!
# Gateway running. Message your bot on Telegram.
```

Then from your phone:

```
you (Telegram) › 🎤 [voice memo: "remind me what we decided about the
                 pricing page yesterday"]
hermes › Yesterday in the terminal session you decided: three tiers,
         annual discount at 20%, and to drop the enterprise "Contact us"
         tier. Want me to draft the copy?
```

> ⚠️ Always restrict allowed users/chat IDs. A publicly reachable bot with terminal access is a remote shell for strangers.

---

## 10. Scheduled Automations (Cron)

Hermes has a **built-in cron scheduler** with delivery to any connected platform — no system crontab needed. Schedule tasks conversationally:

```
you › Every weekday at 8:30, check my calendar and the team's GitHub
      activity from yesterday, and send me a morning briefing on Telegram.
hermes › Scheduled: "morning-briefing" — Mon–Fri 08:30, delivery: Telegram.
```

**Typical unattended-task patterns:**

- 📊 *Daily report:* compile metrics, deliver to Slack every morning
- 💾 *Backups:* nightly database dump + upload, message you only on failure
- 👀 *Monitors:* check a URL/price/RSS feed hourly, alert on change
- 🧹 *Hygiene:* weekly cleanup of downloads folder, summarize what was moved

Because the scheduler is internal, scheduled runs have full access to memory and skills — your morning briefing improves over time like everything else.

---

## 11. Subagents and Parallel Work

For large jobs, Hermes can **spawn isolated subagents** that work concurrently, each with its own context:

```
you › Research the top 5 vector databases — pricing, performance
      benchmarks, and operational complexity — and give me a comparison.
hermes › Spawning 5 subagents, one per database...
         [parallel: qdrant ✓] [weaviate ✓] [milvus ✓] [pgvector ✓] [pinecone ✓]
         Consolidated comparison: ...
```

Subagents keep the main conversation's context clean: only their conclusions return, not their tool-call noise.

---

## 12. Personalities

Switch how Hermes communicates without losing memory or skills:

```
you › /personality terse
hermes › Done.

you › /personality mentor
hermes › Switched. I'll explain my reasoning as we go and flag learning
         opportunities.
```

Useful when the same agent serves different contexts — terse for ops work in Slack, explanatory when you're learning something new.

---

## 13. Configuration Reference

Everything is driven by two files plus a CLI:

```bash
# General pattern
hermes config set <key> <value>

# Examples
hermes config set model anthropic/claude-opus-4.6     # default model
hermes config set terminal.backend docker             # sandbox shell commands
hermes config set OPENROUTER_API_KEY sk-or-...        # secrets go to ~/.hermes/.env automatically
```

| Path | Purpose |
|---|---|
| `~/.hermes/config.yaml` | Model, tools, gateway, scheduler — non-secret settings |
| `~/.hermes/.env` | API keys and bot tokens |
| `hermes doctor` | Validates the whole setup and pinpoints misconfiguration |

---

## 14. Model Providers

Hermes works with **30+ providers** — it's model-agnostic as long as the model handles function calling and ≥64k context:

- **Hosted:** Nous Portal, Anthropic, OpenAI, OpenRouter (200+ models), Google Gemini, AWS Bedrock, Azure Foundry, xAI, DeepSeek, Hugging Face, GitHub Copilot
- **Local:** Ollama, LM Studio, any OpenAI-compatible custom endpoint

Switch any time with `hermes model`, `hermes config set model ...`, or in-chat `/model`. A common pattern: a cheap model for scheduled background tasks, a frontier model for interactive work.

---

## 15. Troubleshooting

| Symptom | Fix |
|---|---|
| Agent loses track mid-task, truncates context | Your model's context window is too small — use a ≥64k model |
| Anything misbehaving after install/update | `hermes doctor` |
| Conversation got huge and slow | `/compress`, or `/new` (memory persists) |
| Want yesterday's session back | `hermes --continue` |
| Messaging bot doesn't respond | Re-run `hermes gateway setup`; check tokens in `~/.hermes/.env` |
| Worried about shell access | `hermes config set terminal.backend docker` and audit `hermes tools` |

---

## Quick-Start Cheat Sheet

```bash
# Install (Linux/macOS/WSL2)
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash && source ~/.bashrc

# Configure
hermes setup                 # wizard: provider, keys, tools
hermes doctor                # verify

# Use
hermes --tui                 # chat (modern TUI)
hermes -c                    # resume last session
hermes skills browse         # explore the Skills Hub
hermes gateway setup         # connect Telegram/Discord/Slack/...
hermes update                # stay current
```

---

## Sources

- [Hermes Agent — GitHub (NousResearch/hermes-agent)](https://github.com/nousresearch/hermes-agent)
- [Official Documentation](https://hermes-agent.nousresearch.com/docs/)
- [Quickstart Guide](https://hermes-agent.nousresearch.com/docs/getting-started/quickstart)
- [Hermes Agent website](https://hermes-agent.org/)

*Note: in-chat dialogue examples in this tutorial are illustrative of documented features; exact agent output will vary by model and version. Tutorial written 2026-06-12 against Hermes Agent v0.2.x docs.*
