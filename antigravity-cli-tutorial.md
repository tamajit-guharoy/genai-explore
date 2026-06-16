# Antigravity CLI (agy) — The Complete Guide

> **Author:** Compiled from official docs + independent community resources  
> **Version:** Antigravity CLI 1.0+  
> **Updated:** June 2026  
> **Binary:** `agy` (Go-based, replaces Gemini CLI)

---

## Table of Contents

1. [What Is Antigravity CLI?](#1-what-is-antigravity-cli)
2. [The Four-Surface Platform](#2-the-four-surface-platform)
3. [Installation](#3-installation)
4. [First Launch Walkthrough](#4-first-launch-walkthrough)
5. [TUI Anatomy & Navigation](#5-tui-anatomy--navigation)
6. [Shell Wrapper Commands](#6-shell-wrapper-commands)
7. [Prompting & Interaction](#7-prompting--interaction)
8. [Complete Slash Command Reference](#8-complete-slash-command-reference)
9. [Managing Conversations](#9-managing-conversations)
10. [Artifacts & Code Review](#10-artifacts--code-review)
11. [Settings Deep Dive](#11-settings-deep-dive)
12. [Keybindings Configuration](#12-keybindings-configuration)
13. [Permissions & Security](#13-permissions--security)
14. [Terminal Sandbox](#14-terminal-sandbox)
15. [Models & AI Credits](#15-models--ai-credits)
16. [Subagents & Parallel Work](#16-subagents--parallel-work)
17. [Plugins](#17-plugins)
18. [Skills](#18-skills)
19. [MCP Servers](#19-mcp-servers)
20. [Workspace Context Files](#20-workspace-context-files)
21. [Migrating from Gemini CLI](#21-migrating-from-gemini-cli)
22. [Scripting & Automation](#22-scripting--automation)
23. [Customizing Status Line & Terminal Title](#23-customizing-status-line--terminal-title)
24. [Best Practices](#24-best-practices)
25. [Troubleshooting](#25-troubleshooting)
26. [Core Paths & File Layout](#26-core-paths--file-layout)
27. [Platform Comparison — CLI vs 2.0 vs IDE](#27-platform-comparison--cli-vs-20-vs-ide)

**Appendices**

- [Appendix A: Quick Reference Card](#appendix-a-quick-reference-card)
- [Appendix B: Complete Example Workflows](#appendix-b-complete-example-workflows)

---

## 1. What Is Antigravity CLI?

Antigravity CLI (`agy`) is Google's **terminal-first AI agent interface** — a lightweight, keyboard-driven Terminal User Interface (TUI) that brings autonomous AI agents directly into your shell. Announced at Google I/O 2026 (May 19, 2026), it replaces the older **Gemini CLI** for individual-tier users and is written entirely in **Go** (a ground-up rewrite from the TypeScript-based Gemini CLI).

### Key Facts

| Property | Detail |
|---|---|
| **Binary** | `agy` |
| **Language** | Go (statically compiled) |
| **License** | Apache 2.0 |
| **Repo** | `github.com/google-antigravity/antigravity-cli` |
| **Replaces** | Gemini CLI (sunset: June 18, 2026 for individual accounts) |
| **Platforms** | macOS, Linux, Windows |
| **Auth** | OS keyring + Google Sign-In (browser OAuth) |
| **Models** | Gemini 3.x, Claude Sonnet 4.6, Claude Opus 4.6, GPT-OSS 120B |
| **Key features** | Subagents, plugins, skills, MCP, sandbox, slash commands |

### What It Can Do

- **Edit code** — multi-file edits with diff review before applying
- **Run terminal commands** — with sandboxed or approved execution
- **Orchestrate subagents** — spawn parallel background agents for tests, builds, research
- **Reason about codebases** — reads your entire workspace, understands context files
- **Manage plugins** — import Gemini CLI extensions, install community plugins
- **Web search** — the agent can search and extract web content
- **Work in natural language** — describe what you want; the agent plans and executes

### Comparison to Other Tools

| Feature | Antigravity CLI | Gemini CLI | Claude Code | Codex CLI |
|---|---|---|---|---|
| **Interface** | TUI (terminal) | TUI (terminal) | TUI (terminal) | TUI (terminal) |
| **Language** | Go | TypeScript | TypeScript | Python |
| **Subagents** | Yes (background) | Limited | Yes (delegate) | No |
| **Sandbox** | Yes (nsjail/sandbox-exec) | No | No | No |
| **Plugins** | Yes (bundles) | Extensions | No | No |
| **Models** | Gemini + Claude + GPT | Gemini only | Claude only | OpenAI only |
| **Cross-surface sync** | Yes (2.0/IDE) | No | No | No |

---

## 2. The Four-Surface Platform

Antigravity CLI is one of four surfaces in Google's unified Antigravity platform. All four share the **same core agent harness** — improvements to the engine benefit every surface simultaneously.

### The Four Surfaces

| Surface | Description | Best For |
|---|---|---|
| **Antigravity 2.0** | Desktop GUI "mission control" | Visual orchestration, multiple parallel agents, artifacts preview, voice |
| **Antigravity CLI** | Terminal TUI (`agy`) | SSH/remote, keyboard-first, low-overhead, terminal-native workflows |
| **Antigravity SDK** | Programmatic API | Embedding agent capabilities into your own applications |
| **Antigravity IDE** | Editor-centric IDE | Full-featured code editing with integrated agent assistance |

### CLI vs Antigravity 2.0 — Detailed Comparison

| Feature | Antigravity CLI | Antigravity 2.0 |
|---|---|---|
| **Primary interface** | Keyboard-driven TUI | Visual desktop editor |
| **Performance overhead** | Near-zero, extremely lightweight | Standard desktop IDE footprint |
| **Workflow focus** | Fast local iterations, SSH, headless | Complete project management, visual workspace |
| **Navigation** | Universal keyboard shortcuts | Mouse and multi-panel layout |
| **Remote usability** | Native SSH, tmux, terminal multiplexers | Local workspace or remote dev containers |
| **Settings sync** | Bidirectional — permissions, allowlists sync | Bidirectional |
| **Conversation export** | Export CLI conversations to 2.0 via @conversation | Import 2.0 conversations into CLI via /resume |

### When to Use CLI vs 2.0

Use **CLI** when:
- You're on a remote server via SSH
- You work in tmux/screen sessions
- You want minimal resource overhead
- You prefer keyboard-only workflows
- You need to script agent interactions

Use **Antigravity 2.0** when:
- You need visual artifact previews and diffs
- You want to orchestrate multiple agents side-by-side
- You need voice interaction or scheduled tasks
- You prefer mouse-driven navigation

---

## 3. Installation

### Prerequisites

- macOS 12+ (Apple Silicon), Linux (glibc >= 2.28), or Windows 10/11 (64-bit)
- A Google AI Pro or Ultra subscription (or enterprise GCP project)
- Terminal emulator (iTerm2, Ghostty, WezTerm, Windows Terminal, or standard terminal)

### Fast-Path Installation

**macOS / Linux:**

```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash
```

**Windows (PowerShell):**

```powershell
irm https://antigravity.google/cli/install.ps1 | iex
```

**Windows (CMD):**

```cmd
curl -fsSL https://antigravity.google/cli/install.cmd -o install.cmd && install.cmd && del install.cmd
```

### Binary Location After Install

| Platform | Default Binary Path |
|---|---|
| macOS / Linux | `~/.local/bin/agy` |
| Windows | `C:\Users\<Username>\AppData\Local\agy\bin\agy.exe` |

### Verifying the Installation

```bash
agy --version
# Antigravity CLI 1.0.2
```

```bash
command -v agy
# /home/user/.local/bin/agy
```

### PATH Configuration

If `agy: command not found`, add the binary directory to your PATH:

**macOS / Linux** — add to `~/.bashrc` or `~/.zshrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then reload:

```bash
source ~/.bashrc   # or source ~/.zshrc
```

**Windows (PowerShell)** — Run as Administrator:

```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:LocalAppData\agy\bin", "User")
```

Restart your terminal after.

### Inspecting the Installer (Security-Conscious)

On shared or sensitive infrastructure, download and inspect the script before piping:

```bash
curl -fsSL https://antigravity.google/cli/install.sh -o /tmp/install.sh
less /tmp/install.sh      # Review the script
bash /tmp/install.sh       # Run after review
```

### `agy install` Flags

The `agy install` command (run from an already-installed binary) supports additional flags:

```bash
agy install --help
```

| Flag | Description |
|---|---|
| `--dir <path>` | Custom installation directory |
| `--skip-aliases` | Don't create shell aliases |
| `--skip-path` | Don't modify PATH |

### Updating

```bash
agy update
```

The CLI includes a built-in self-updater that checks for new versions. It uses a 15-minute debounce between checks and an advisory lock (`~/.gemini/antigravity-cli/updater/update.lock`).

To disable auto-updates:

```bash
export AGY_NO_AUTO_UPDATE=1   # Add to ~/.bashrc or ~/.zshrc
```

---

## 4. First Launch Walkthrough

### Launch the TUI

Navigate to your project directory and run:

```bash
cd /path/to/your/project
agy
```

### Step 1: Color Scheme

On first launch, you're prompted to select a color scheme:

- **Solarized** — Warm, low-contrast palette
- **Dark** — High-contrast dark theme
- **Solarized Light** — Light variant of Solarized
- **Terminal Colors** — Inherits your terminal's native colors

Use arrow keys to navigate and press `Enter` to select.

### Step 2: Rendering Mode

Choose how the TUI renders its output:

| Mode | Behavior | Best For |
|---|---|---|
| **Alt-Screen** | Opens a dedicated alternate buffer with integrated scrollback, mouse-wheel scrolling, and clean state restoration | Local development with advanced terminals (iTerm2, Ghostty, WezTerm) |
| **Inline** | Renders output sequentially in standard stdout, preserving full session in terminal's native scrollback | SSH sessions, tmux/screen, low-bandwidth connections |

You can change this later via `/config` or `settings.json`.

### Step 3: Workspace Trust

The agent asks you to confirm you trust the current workspace directory. Once confirmed, it indexes the files and stands ready.

### Step 4: Authentication

**Local (first launch):** The CLI opens your default browser for Google Sign-In. Complete the OAuth flow; the token is stored in your OS keyring.

**Remote SSH:** The CLI prints an authorization URL:

```
Open this URL to authenticate:
https://antigravity.google/cli/auth?code=XXXX-XXXX
```

Complete the flow on your local machine, then paste the confirmation code back into the SSH terminal.

### Step 5: First Task

Type your first instruction and press `Enter`:

```
Write a simple Python script to fetch web page text
```

The agent reads the workspace, reasons about the task, and proposes a plan. It may ask for permission before writing files or running commands.

### Post-Setup Verification Commands

```bash
# Check your current configuration
/config

# See available models
/model

# Review permission level
/permissions

# Open help
/usage
```

---

## 5. TUI Anatomy & Navigation

### Layout

The TUI has three main zones:

```
┌─────────────────────────────────────────────┐
│  Status Bar: [model] [credits] [CWD] [time] │
├─────────────────────────────────────────────┤
│                                             │
│         Conversation / Output Area           │
│  (agent responses, diffs, plans, logs)      │
│                                             │
├─────────────────────────────────────────────┤
│  Prompt Box:  > _                           │
└─────────────────────────────────────────────┘
```

### Global Controls

| Key | Action |
|---|---|
| `Esc` | **Universal escape** — cancels active agent turn, closes overlays, returns focus to prompt |
| `Ctrl+C` | Exit CLI (prompts for confirmation if agent is working) |
| `Ctrl+L` | Clear/refresh the terminal buffer |

### Interrupting the Agent

If the agent is executing an undesired task or looping:

1. Press `Esc` — immediately halts the current turn
2. The prompt box regains focus
3. You can now redirect with a new instruction or `/rewind`

### Status Bar

The status bar displays real-time information:

- **Active model** — e.g., "Gemini 3.5 Flash (High)"
- **AI credits** remaining / usage
- **Current working directory**
- **Background task count** — shows if subagents are running
- **Artifact review count** — shows "2 to review" when artifacts need attention

---

## 6. Shell Wrapper Commands

These commands run **outside** the TUI — from your regular shell prompt. They control the binary itself, not the interactive agent session.

### Command Reference

```bash
# Display version information
agy --version
# Antigravity CLI 1.0.2

# Show shell wrapper help (NOT in-session slash commands!)
agy help

# View changelog
agy changelog

# Install/reinstall the binary
agy install
agy install --dir /custom/path

# Update to the latest version
agy update

# Plugin management (from shell)
agy plugin list
agy plugin import gemini
agy plugin install <plugin-name>
agy plugin uninstall <plugin-name>
agy plugin enable <plugin-name>
agy plugin disable <plugin-name>
agy plugin validate <path>
agy plugin link <mp> <target>
agy plugin help
```

### Useful Launch Flags

```bash
# Non-interactive one-shot mode
agy --print "Summarize this repo in 3 bullets"
agy -p "Fix all lint errors in src/"

# Continue the most recent conversation
agy --continue
agy -c

# Resume a specific conversation by UUID
agy --conversation "86603edc-f09c-45c1-93ba-3143c49e9035"

# Add a directory to the workspace
agy --add-dir /path/to/other/project

# Enable sandbox for this session
agy --sandbox

# Skip all permission prompts (DANGEROUS)
agy --dangerously-skip-permissions

# Non-interactive with custom timeout (seconds)
agy --print "Run the test suite" --print-timeout 300

# Launch with a pre-filled prompt (starts in interactive mode)
agy --prompt "Add a new REST endpoint for user profiles"

# Interactive mode with prompt
agy --prompt-interactive "Refactor the auth module"
agy -i "Refactor the auth module"

# Write session log to a file
agy --log-file /tmp/agy-session.log
```

### Full Flag Reference

| Flag | Short | Description |
|---|---|---|
| `--add-dir <path>` | — | Add directory to workspace |
| `--continue` | `-c` | Resume most recent conversation |
| `--conversation <uuid>` | — | Resume specific conversation by UUID |
| `--dangerously-skip-permissions` | — | Skip all permission prompts |
| `--log-file <path>` | — | Write session log to file |
| `--print "<prompt>"` | `-p` | Non-interactive one-shot mode |
| `--print-timeout <seconds>` | — | Timeout for --print mode |
| `--prompt "<text>"` | — | Pre-fill prompt in interactive mode |
| `--prompt-interactive` | `-i` | Interactive mode with pre-filled prompt |
| `--sandbox` | — | Enable sandbox for this session |
| `--version` | — | Print version and exit |

---

## 7. Prompting & Interaction

### The Prompt Box

The prompt box sits at the bottom of the TUI. Type your instruction and press `Enter` to submit it to the agent.

### Multiline Composition

For complex directives, use these methods to write multi-line prompts:

**Method 1: `Shift+Enter` or `Ctrl+J`**

```
> Write a Python class for:
  Shift+Enter
  - connecting to PostgreSQL
  Shift+Enter
  - with connection pooling
  Shift+Enter
  - and async support
  Enter (to submit)
```

**Method 2: Backslash Escape**

Type `\` at the end of a line, then press `Enter`:

```
> Write a Python class for: \
connecting to PostgreSQL \
with connection pooling
```

The backslash is automatically removed and a newline is inserted.

**Method 3: macOS Terminal Fallback**

If using Apple Terminal (which doesn't forward `Shift+Enter` by default):

- Press `Option+Enter` instead
- Ensure **Use Option as Meta key** is checked in Terminal Preferences → Profiles

### External Editor (Ctrl+G)

For extensive prompts, draft in your preferred editor:

1. Press `Ctrl+G` in the empty prompt box
2. Your `$EDITOR` (vim, nano, code, etc.) opens with a temporary buffer
3. Write your multi-line instruction
4. Save and exit — the content is imported into the prompt box

### Path Autocomplete (@)

Type `@` in the prompt box to trigger interactive path suggestions:

```
> Fix the bug in @
  ┌─────────────────────────────┐
  │ src/utils/helper.py         │
  │ src/models/user.py          │
  │ src/api/endpoints.py        │
  │ tests/test_auth.py          │
  └─────────────────────────────┘
```

Use `↑`/`↓` to navigate and `Enter` to select. The absolute workspace path is inserted directly into your prompt.

### Attaching Media (Ctrl+V)

Paste screenshots, mockups, or videos directly into the prompt:

```bash
# Copy an image to clipboard, then press Ctrl+V in the prompt box
Ctrl+V
```

**Supported formats:**

| Category | Formats |
|---|---|
| Images | PNG, JPEG, GIF, WebP, BMP, TIFF, SVG |
| Videos | MP4, MOV, WebM, AVI |

The agent analyzes the attached media and incorporates it into its reasoning. This is especially useful for:
- UI bug reports (paste a screenshot of the visual glitch)
- Design mockups (paste a Figma export)
- Error screenshots (paste an error dialog)

### `!` — Run Terminal Commands Directly

Type `!` followed by a shell command to execute it directly:

```
> !git status
> !pytest tests/ -x
> !npm run build
```

The command output is displayed inline without involving the agent.

### `?` — Quick Help

Type `?` in the prompt to open context-sensitive help:

```
> ?
```

---

## 8. Complete Slash Command Reference

Type `/` in the prompt box to open the typeahead command selection menu. Below is every slash command with its category, aliases, and usage.

### Conversation Control

| Command | Alias(es) | Description |
|---|---|---|
| `/resume` | `/switch`, `/conversation` | Open conversation picker to resume or switch sessions |
| `/rewind` | `/undo` | Roll back conversation history to a previous checkpoint |
| `/rename <name>` | — | Rename the current session thread |
| `/fork` | `/branch` | Clone current conversation into a new parallel session |
| `/clear` | — | Clear terminal and reset conversation context |
| `/new` | — | Start a fresh conversation |

**Examples:**

```
/resume
# Opens interactive conversation picker — filter by keyword, navigate with ↑/↓, Enter to select

/rewind
# Opens checkpoint list — select a previous turn to roll back to

/rename "Implement user auth"
# Renames the current conversation thread

/fork
# Creates a duplicate session with full history up to this point
```

### Configuration

| Command | Alias(es) | Description |
|---|---|---|
| `/config` | `/settings` | Open interactive Settings Editor overlay |
| `/model` | — | Select default reasoning model (persists across sessions) |
| `/permissions` | — | Switch global permission presets |
| `/keybindings` | — | Open interactive keyboard shortcut editor |
| `/statusline` | — | Open status bar customization overlay |
| `/title [on/off]` | — | Toggle terminal window title updates |
| `/planning` | — | Enable multi-turn plan generation mode |
| `/fast` | — | Enable fast mode (bypass reasoning plans) |

**Examples:**

```
/config
# Opens full-screen settings editor — navigate with ↑/↓, Enter to toggle/edit, Esc to save

/model
# Opens model picker: Gemini 3.5 Flash, Gemini 3.5 Pro, Claude Sonnet 4.6, etc.

/permissions
# Cycle through: request-review → always-proceed → strict → proceed-in-sandbox

/keybindings
# Interactive keybinding editor — remap any shortcut

/planning
# Agent will produce a detailed plan before executing — good for complex tasks
```

### Tools & Monitoring

| Command | Description |
|---|---|
| `/agents` | Open Agent Manager Panel — monitor background subagents |
| `/tasks` | Open Task Manager Panel — view background shell execution logs |
| `/skills` | Browse loaded local and global agent skills |
| `/mcp` | Open MCP (Model Context Protocol) server manager |
| `/hooks` | Browse active pre-flight and post-format script hooks |

**Examples:**

```
/agents
# Shows all active/completed subagents with status (running, done, killed) and current step
# Select a subagent to open full detail view (conversation, steps, tool logs)

/tasks
# Monitor background shell tasks, view logs, terminate hung processes

/skills
# Browse available skills — local (project) and global (~/.gemini/)

/mcp
# Configure MCP servers — add, remove, enable, disable
```

### Utilities

| Command | Description |
|---|---|
| `/diff` | Show unified diff of all modified workspace files |
| `/open <path>` | Open a file in your default system editor |
| `/usage` | Launch offline developer help manual |
| `/add-dir <path>` | Add a directory to the active workspace |
| `/btw <query>` | Ask a side question in background without interrupting main conversation |
| `/exit` | Close the TUI session and restore host shell |

**Examples:**

```
/diff
# Shows git-style unified diff of all files the agent has modified

/open src/main.py
# Opens src/main.py in $EDITOR

/add-dir /home/user/another-project
# Adds another project directory to the workspace for cross-repo context

/btw "What does the .gitignore pattern '*.log' do?"
# Asks a quick question in a background thread — answer appears without interrupting

/exit
# Clean exit — saves session state and restores your shell
```

### Account

| Command | Description |
|---|---|
| `/logout` | Disconnect profile and purge authentication tokens from keyring |

```
/logout
# Removes cached credentials — next launch will re-prompt for auth
```

---

## 9. Managing Conversations

### Workspace Scoping

Antigravity CLI scopes conversations to your current working directory. When you launch `agy` from `/home/user/project-a`, you only see conversations associated with that directory. This prevents context pollution across projects.

### Resuming Sessions

#### Via the TUI Picker

```
/resume
```

1. Interactive Conversation Picker overlay opens
2. Type keywords to filter by description or ID
3. Use `↑`/`↓` to navigate, `←`/`→` to page through older records
4. Press `Enter` to resume; `Esc` to cancel

#### Importing from Antigravity 2.0

1. Type `/resume` and press `Enter`
2. Press `Tab` to cycle between **CLI** tab (local TUI conversations) and **Antigravity** tab (2.0 desktop conversations)
3. Select a desktop conversation and press `Enter`
4. Confirm the import — the conversation history, context, and trajectories are duplicated into your CLI session

#### Quick Resume from Command Line

```bash
# Resume most recent session in this workspace
agy --continue
agy -c

# Resume specific conversation by UUID
agy --conversation "86603edc-f09c-45c1-93ba-3143c49e9035"
```

### Branching with `/fork`

`/fork` (alias: `/branch`) clones your entire conversation history up to the current turn into a new independent session. This enables safe, parallel experimentation:

1. Reach a stable baseline in your conversation
2. Type `/fork` — a new session with a unique UUID is created
3. Your terminal switches to the new branch
4. Experiment freely — if the approach fails, use `/resume` to return to the original branch

**Important:** `/fork` clones the **conversation thread**, not your Git checkout. To fully isolate files during parallel experiments, use Git branches or stash changes first.

### Rewinding with `/rewind`

If successive changes introduce errors:

```
/rewind
```

1. A list of conversation checkpoints appears
2. Select the point to roll back to
3. The conversation thread is restored to that state

Alias: `/undo`

### Renaming Sessions

```
/rename "User authentication feature"
```

Renames the current conversation thread for easier identification in the picker.

### Clearing Sessions

```
/clear
```

Clears the terminal display and resets the active conversation context. Useful when the conversation has accumulated too much irrelevant context.

---

## 10. Artifacts & Code Review

An **Artifact** is a structured deliverable the agent creates: implementation plans, code diffs, architecture diagrams, visual media. Artifacts enable asynchronous collaboration — you review high-level deliverables instead of monitoring every tool execution.

### The Artifact Review Flow

1. Agent completes work and produces artifacts
2. Status bar shows: `/artifact to review (3)` — indicating 3 items need attention
3. You review, comment, approve, or reject each artifact
4. Approved artifacts are applied; rejected ones are discarded

### Artifact Picker Panel

Press `Ctrl+R` inside the prompt box to open the full-screen **Artifact Picker Panel**.

#### Picker Keybindings

| Key | Command | Action |
|---|---|---|
| `↑` / `↓` | `nav.scroll_line` | Scroll through file list |
| `h` / `l` (or `←`/`→`) | `nav.switch_button` | Toggle between **open**, **approve**, **reject** buttons |
| `p` | `confirm.preview` | Toggle 12-line inline code preview |
| `y` | `confirm.approve` | Approve file → `✓ approved` |
| `n` | `confirm.reject` | Reject file → `✗ rejected` |
| `Shift+A` | `confirm.approve_all` | Bulk-approve all pending files |
| `Shift+R` | `confirm.reject_all` | Bulk-reject all pending files |
| `Enter` | `nav.confirm` | Execute focused button; if `open`, launch Detail Viewer |
| `Esc` | `nav.escape` | Save review state, submit, return to prompt |

#### Code Files vs Visual Media

- **Actionable Code Files** — require explicit approval before being written to disk
- **Collapsible Media Drawer** — groups visual assets (PNG, JPG, WebP, SVG, MP4, WebM) under a **Media** header
  - Highlight **Media** and press `Enter` to expand/collapse
  - Highlight a media item and press `Enter` to open in system's native viewer

### Artifact Detail Viewer

Press `Enter` on a code row (with `open` focused) to launch the full-screen detail viewer.

#### Viewer Navigation

| Key | Action |
|---|---|
| `j` / `k` (or `↑`/`↓`) | Scroll line by line |
| `Ctrl+D` / `Ctrl+U` | Scroll page by page |
| `g` | Jump to top |
| `Shift+G` | Jump to bottom |
| `l` | Toggle line number gutter |
| `Esc` | Close viewer, return to picker |

#### Inline Commenting

1. Position cursor on the target line
2. Press `c` — opens multi-line comment editor attached to that line
3. Write feedback, press `Esc` to save — line shows `💬` indicator
4. To delete a comment, press `d` on a commented line

#### Mermaid Diagram Rendering

Press `m` to cycle through render modes:

| Mode | Description |
|---|---|
| **ASCII Box Art** (default) | Text-based rendering — works in any shell |
| **Kitty Graphics Image** | Native graphics in Kitty-compatible terminals (zoom with `Ctrl+=`/`Ctrl+-`) |
| **Raw Code** | Shows original Mermaid markdown fences |

---

## 11. Settings Deep Dive

### Configuration File

Settings are stored in a JSON file with **sparse persistence** — only values that differ from defaults are written, keeping the config clean and forward-compatible.

**Location:** `~/.gemini/antigravity-cli/settings.json`

### Complete settings.json — Every Known Key

```json
{
  "colorScheme": "dark",
  "renderingMode": "alt-screen",
  "enableTerminalSandbox": false,
  "allowNonWorkspaceAccess": false,
  "trustedWorkspaces": [
    "/home/user/project-a",
    "/home/user/project-b"
  ],
  "permissions": {
    "mode": "request-review",
    "allowed": [
      "ls",
      "cat",
      "git status",
      "git diff",
      "npm test",
      "pytest",
      "go test"
    ],
    "denied": [
      "rm -rf",
      "sudo",
      "chmod 777",
      "git push --force"
    ]
  },
  "model": "gemini-3.5-flash",
  "aiCredits": {
    "fallbackEnabled": true,
    "fallbackModel": "gemini-3.5-flash"
  },
  "editor": "code",
  "statusLine": {
    "enabled": true,
    "script": "~/.gemini/antigravity-cli/scripts/status.sh"
  },
  "terminalTitle": {
    "enabled": true,
    "format": "agy: {project} — {model}"
  }
}
```

### Key Reference

| Key | Type | Default | Description |
|---|---|---|---|
| `colorScheme` | string | `"dark"` | Visual theme: `"solarized"`, `"dark"`, `"solarized-light"`, `"terminal"` |
| `renderingMode` | string | `"default"` | `"alt-screen"`, `"inline"`, or `"default"` (auto-detect) |
| `enableTerminalSandbox` | boolean | `false` | Enable OS-level sandbox for all agent terminal commands |
| `allowNonWorkspaceAccess` | boolean | `false` | Allow agent to read files outside the workspace |
| `trustedWorkspaces` | array | `[]` | List of workspace paths that skip the trust prompt |
| `permissions.mode` | string | `"request-review"` | Global permission level |
| `permissions.allowed` | array | `[]` | Commands always allowed regardless of mode |
| `permissions.denied` | array | `[]` | Commands always denied regardless of mode |
| `model` | string | — | Default model (set via `/model`) |
| `aiCredits.fallbackEnabled` | boolean | `true` | Fall back to lower-tier model when credits exhausted |
| `aiCredits.fallbackModel` | string | — | Fallback model when credits exhausted |
| `editor` | string | `$EDITOR` | External editor for Ctrl+G |
| `statusLine.enabled` | boolean | `true` | Show/hide status bar |
| `statusLine.script` | string | `""` | Custom shell script for status line content |
| `terminalTitle.enabled` | boolean | `false` | Update terminal window title |
| `terminalTitle.format` | string | `"agy: {project}"` | Template for terminal title |

### Interactive Settings Editor (`/config`)

```
/config
```

- Opens a full-screen **Settings Editor Overlay**
- Navigate with `↑`/`↓`
- Press `Enter` on a parameter to toggle its state or open a text field
- Press `Esc` to save and close

### Command-Line Overrides

Temporarily override persistent settings for a single session:

```bash
agy --sandbox                         # Enable sandbox for this session only
agy --dangerously-skip-permissions    # Skip all permission prompts
```

When an override is active, the `/config` menu displays:

```
⚠ This setting is overridden by a command-line flag
```

The persistent value can still be edited, but the flag takes precedence until the session ends.

### Visual Rendering Modes

| Mode | Behavior | Best For |
|---|---|---|
| `alt-screen` | Dedicated alternate buffer, integrated scrollback, mouse-wheel scrolling | Local dev with iTerm2, Ghostty, WezTerm |
| `inline` | Sequential stdout output, native terminal scrollback | SSH, tmux, screen, low-bandwidth |
| `default` | Auto-detect: alt-screen locally, inline over SSH | General use |

---

## 12. Keybindings Configuration

### Keybindings File

**Location:** `~/.gemini/antigravity-cli/keybindings.json`

The JSON file maps TUI commands to keyboard shortcut arrays. Empty arrays disable a shortcut.

### Example keybindings.json

```json
{
  "cli.escape": ["Esc"],
  "cli.exit": ["Ctrl+C", "Ctrl+D"],
  "cli.clear_screen": ["Ctrl+L"],
  "prompt.submit": ["Enter"],
  "prompt.newline": ["Shift+Enter", "Ctrl+J"],
  "prompt.paste": ["Ctrl+V"],
  "prompt.external_editor": ["Ctrl+G"],
  "prompt.open_review": ["Ctrl+R"],
  "prompt.toggle_trajectory": ["Ctrl+O"],
  "prompt.fast_approve": ["Ctrl+K"],
  "prompt.teleport_agent": ["Alt+J"],
  "prompt.cursor_start": ["Ctrl+A"],
  "prompt.cursor_end": ["Ctrl+E"],
  "prompt.undo_text": ["Ctrl+Z"],
  "prompt.redo_text": ["Ctrl+Shift+Z"],
  "nav.scroll_up": ["Up", "k"],
  "nav.scroll_down": ["Down", "j"],
  "nav.page_up": ["Ctrl+U", "PageUp"],
  "nav.page_down": ["Ctrl+D", "PageDown"],
  "nav.scroll_top": ["g", "Home"],
  "nav.scroll_bottom": ["Shift+G", "End"]
}
```

### Customizing Keybindings

Use the interactive editor:

```
/keybindings
```

Or edit the JSON file directly. To disable a shortcut, set its action to an empty array:

```json
{
  "prompt.external_editor": []
}
```

### Protected Keys (Cannot Be Disabled)

| Command | Default Key |
|---|---|
| `cli.exit` | `Ctrl+D` / `Ctrl+C` |
| `prompt.submit` | `Enter` |

These are mandatory for basic TUI operation.

### Restoring Defaults

Delete the keybindings file to revert all keys to system defaults:

```bash
rm ~/.gemini/antigravity-cli/keybindings.json
```

If the JSON is malformed, the CLI falls back to system defaults for invalid actions and loads the rest.

### Default Keybinding Reference

#### Global Controls (Always Active)

| Key | Command | Action |
|---|---|---|
| `Esc` | `cli.escape` | Close panels, halt streams, clear prompts |
| `Ctrl+C` | `cli.exit` | Terminate CLI session |
| `Ctrl+L` | `cli.clear_screen` | Refresh terminal buffer |

#### Prompt Focus Keys

| Key | Command | Action |
|---|---|---|
| `Enter` | `prompt.submit` | Submit prompt to agent |
| `Shift+Enter` / `Ctrl+J` | `prompt.newline` | Insert newline |
| `Ctrl+V` | `prompt.paste` | Paste media/clipboard |
| `Ctrl+G` | `prompt.external_editor` | Open $EDITOR |
| `Ctrl+R` | `prompt.open_review` | Open artifact review panel |
| `Ctrl+O` | `prompt.toggle_trajectory` | Expand/collapse tool reasoning |
| `Ctrl+K` | `prompt.fast_approve` | Instantly approve pending subagent action |
| `Alt+J` | `prompt.teleport_agent` | Switch focus to next subagent needing approval |
| `Ctrl+A` | `prompt.cursor_start` | Move cursor to line start |
| `Ctrl+E` | `prompt.cursor_end` | Move cursor to line end |
| `Ctrl+Z` | `prompt.undo_text` | Undo last text edit |
| `Ctrl+Shift+Z` | `prompt.redo_text` | Redo last undone edit |

#### Navigation Keys

| Key | Command | Action |
|---|---|---|
| `↑` / `k` | `nav.scroll_up` | Scroll up one line |
| `↓` / `j` | `nav.scroll_down` | Scroll down one line |
| `PageUp` / `Ctrl+U` | `nav.page_up` | Scroll up one page |
| `PageDown` / `Ctrl+D` | `nav.page_down` | Scroll down one page |
| `Home` / `g` | `nav.scroll_top` | Jump to top |
| `End` / `Shift+G` | `nav.scroll_bottom` | Jump to bottom |

---

## 13. Permissions & Security

### Permission Modes

Set via `/permissions` slash command or `settings.json`:

| Mode | Behavior | Use Case |
|---|---|---|
| `request-review` | **Default.** Prompts before writes, bash commands, and network calls. | Daily development — safety with convenience |
| `always-proceed` | Agent executes all operations without prompting. | Trusted projects, experienced users |
| `strict` | Always prompts for all non-read operations. | High-security environments, code review |
| `proceed-in-sandbox` | Safe commands run autonomously in sandbox; risky ones prompt. | Balanced security with reduced friction |

### Cycling Permission Modes

```
/permissions
```

Each invocation of `/permissions` cycles to the next mode. The current mode is shown in the status bar.

### Fine-Grained Permissions

Override the global mode with explicit lists in `settings.json`:

```json
{
  "permissions": {
    "mode": "request-review",
    "allowed": [
      "ls",
      "cat",
      "head",
      "tail",
      "git status",
      "git diff",
      "git log",
      "npm test",
      "npm run lint",
      "pytest",
      "go test",
      "cargo test",
      "make",
      "echo"
    ],
    "denied": [
      "rm -rf",
      "sudo",
      "chmod 777",
      "chown",
      "git push --force",
      "git reset --hard",
      "shutdown",
      "reboot",
      "docker rm -f",
      "kubectl delete"
    ]
  }
}
```

**Priority:** Explicit `denied` entries trump `allowed` entries, which trump the `mode` setting.

### Workspace Trust

On first launch in a new directory, the agent asks you to confirm trust. Once confirmed, the path is added to `trustedWorkspaces`:

```json
{
  "trustedWorkspaces": [
    "/home/user/project-a",
    "/home/user/project-b"
  ]
}
```

Trusted workspaces skip the confirmation prompt on subsequent launches.

### Non-Workspace Access

By default, the agent can only read files within the current workspace. To allow access outside:

```json
{
  "allowNonWorkspaceAccess": true
}
```

Use with caution — this lets the agent read arbitrary files on your system.

### `--dangerously-skip-permissions`

```bash
agy --dangerously-skip-permissions
```

This flag disables ALL permission prompts for the session. Equivalent to `always-proceed` mode, but clearly marked as dangerous. Use only in isolated environments.

---

## 14. Terminal Sandbox

The terminal sandbox is a lightweight OS-level security boundary that isolates agent shell commands from your host system — without the overhead of VMs or containers.

### How It Works

| Platform | Technology | Mechanism |
|---|---|---|
| Linux | `nsjail` | Namespace isolation + seccomp filters |
| macOS | `sandbox-exec` | Apple Sandbox with Seatbelt profiles |
| Windows | `AppContainer` | Windows app container isolation |

**Key property:** Zero startup overhead — no container spin-up, no VM boot.

### Enabling the Sandbox

**Persistent** — in `settings.json`:

```json
{
  "enableTerminalSandbox": true
}
```

**Per-session** — via command-line flag:

```bash
agy --sandbox
```

### Interactive Approval Toggle

The sandbox adds a dynamic option to the approval prompt:

**When sandbox is enabled:**
```
Allow this command?
  [y] Yes, and run without sandbox restrictions  ← temporarily bypass
  [n] No
```

**When sandbox is disabled:**
```
Allow this command?
  [y] Yes
  [s] Yes, and run in sandbox  ← force into sandbox for this command
  [n] No
```

### What the Sandbox Blocks

- File writes outside the workspace directory
- Network connections to non-whitelisted hosts
- Execution of binaries outside approved paths
- Modification of system configuration files
- Access to sensitive device files (`/dev/mem`, etc.)

---

## 15. Models & AI Credits

### Available Models

Antigravity CLI exposes models from multiple providers through a single subscription:

| Model | Provider | Best For |
|---|---|---|
| Gemini 3.5 Flash | Google | Fast, cost-effective — daily tasks, quick edits |
| Gemini 3.5 Flash (High) | Google | Higher reasoning at moderate cost |
| Gemini 3.5 Pro | Google | Complex reasoning, large codebases |
| Claude Sonnet 4.6 | Anthropic | Balanced speed and depth |
| Claude Opus 4.6 | Anthropic | Deepest reasoning, complex architecture |
| GPT-OSS 120B | OpenAI | Open-source model option |

### Selecting a Model

```
/model
```

Opens an interactive model picker. Use `↑`/`↓` to navigate, `Enter` to select. The choice persists across sessions.

The selected model is displayed in the status bar:

```
▄▀▀▄ Antigravity CLI 1.0.2
 ▀▀▀▀▀▀ user@gmail.com
▀▀▀▀▀▀▀▀ Gemini 3.5 Flash (High)
```

### AI Credits

Google AI Pro and Ultra subscriptions include monthly AI credits. When credits run low:

```json
{
  "aiCredits": {
    "fallbackEnabled": true,
    "fallbackModel": "gemini-3.5-flash"
  }
}
```

- `fallbackEnabled: true` — automatically switch to a lower-tier model when credits are exhausted
- `fallbackModel` — which model to use as fallback

The status bar shows remaining credits. When credits are low, a warning appears.

### Credit Monitoring

```
/usage
```

Opens the offline help manual, which includes credit tracking information.

---

## 16. Subagents & Parallel Work

Subagents are **independent, concurrent agent sessions** that the main agent spawns for background work. They let you tackle large tasks faster by running multiple workstreams in parallel.

### How Subagents Work

1. You give the main agent a complex task
2. The agent identifies parallelizable sub-tasks
3. It spawns subagents — each gets its own context, tools, and workspace access
4. Subagents run in the background while you continue working
5. Results are collected and presented when ready

### Subagent Capabilities

Subagents have access to:
- Code search and file reading
- File editing (with permission)
- Terminal command execution (with permission)
- Web search
- MCP tools (if delegated)

### The `/agents` Panel

```
/agents
```

Opens the **Agent Manager Panel** — an interactive TUI for subagent oversight.

**Panel shows:**
- Active subagents with status: `running`, `done`, `killed`
- Completed subagents with result summaries
- Current step each subagent is executing

**Detail View:**
Select a subagent to open a full-screen view showing:
- Complete conversation history
- Step-by-step reasoning
- Tool execution logs
- Pending approvals

### Tool Confirmations & Fast Approvals

When a subagent needs permission for an action, you have two approval methods:

**Method 1: Detail View Approvals**
- Open the subagent's detail view
- Navigate to the **Interaction** section
- Approve or reject pending actions

**Method 2: Fast Path Alerts**
- An alert appears directly above the main prompt
- Press `Ctrl+K` to instantly approve without switching contexts

### Keyboard Shortcuts for Subagents

| Key | Action |
|---|---|
| `Ctrl+K` | Instantly approve pending subagent action from alert |
| `Alt+J` | Teleport focus to next subagent needing approval |
| `Ctrl+J` | Teleport from main conversation to subagent detail view |

### Best Practices

- **Delegate independent work** — tests, documentation lookups, builds, validations
- **Avoid over-delegation** — each subagent costs context; don't spawn 10 for trivial tasks
- **Use fast approvals** — `Ctrl+K` for repetitive safe operations
- **Monitor with `/agents`** — check subagent progress periodically

---

## 17. Plugins

Plugins are **namespaced bundles** containing skills, agents, rules, MCP servers, and hooks — all deployable as a single unit. They replace Gemini CLI's "Extensions" model.

### Plugin Anatomy

A plugin bundle can contain:

| Component | Description |
|---|---|
| **Skills** | Encapsulated agent workflows (slash commands) |
| **Agents** | Custom agent configurations |
| **Rules** | Workspace rules and conventions |
| **MCP Servers** | Model Context Protocol server definitions |
| **Hooks** | Pre-flight and post-format script hooks |

### Plugin Storage

Plugins are staged under:

```
~/.gemini/antigravity-cli/plugins/
├── conductor/
│   ├── skills/
│   ├── agents/
│   ├── mcpServers/
│   └── hooks/
├── google-workspace/
│   └── skills/
└── custom-plugin/
    └── ...
```

### Shell Wrapper Plugin Commands

```bash
# List installed plugins
agy plugin list

# Import from Gemini CLI extensions
agy plugin import gemini

# Install a plugin from a source (URL, path, or registry)
agy plugin install <target>

# Uninstall a plugin
agy plugin uninstall <plugin-name>

# Enable a disabled plugin
agy plugin enable <plugin-name>

# Disable a plugin without uninstalling
agy plugin disable <plugin-name>

# Validate a plugin manifest at a path
agy plugin validate /path/to/plugin/

# Link an MCP server to a target
agy plugin link <mp> <target>

# Plugin subcommand help
agy plugin help
```

### Importing Gemini CLI Extensions

```bash
agy plugin import gemini
```

Sample output:

```
[ok]    conductor
          - skills      : skipped (not found)
          - agents      : skipped (not found)
          ✔ commands    : 6 processed (converted to skills)
          - mcpServers  : skipped (not found)
          - hooks       : skipped (not found)
[ok]    google-workspace
          ✔ skills      : 6 processed
          - agents      : skipped (not found)
          ✔ commands    : 4 processed (converted to skills)
          ✔ mcpServers  : 2 processed
          - hooks       : skipped (not found)
```

**What migrates:**
- Gemini CLI commands → Antigravity skills (automatic conversion)
- MCP server configurations
- Skills definitions
- Hook scripts

**What doesn't migrate:**
- Custom agent definitions (different format)
- Some extension-specific metadata

### In-Session Plugin Access

Once loaded, plugin components are accessed via slash commands:

```
/skills          # Browse plugin-provided skills
/mcp             # Manage plugin-provided MCP servers
/hooks           # View plugin-provided hooks
```

---

## 18. Skills

Skills are **encapsulated agent workflows** — reusable procedures that teach the agent how to handle specific task types. They're the primary extensibility mechanism inside the TUI.

### Browsing Skills

```
/skills
```

Opens an interactive browser showing:
- **Local skills** — defined in your current project
- **Global skills** — installed in `~/.gemini/` (including plugin-provided skills)

### Skill Types

| Type | Scope | Example |
|---|---|---|
| **Local** | Current workspace only | Project-specific build/deploy procedures |
| **Global** | All workspaces | General-purpose workflows (git, docker, etc.) |
| **Plugin-provided** | All workspaces (when enabled) | Community workflows from installed plugins |

### Creating Skills

Skills can be created:
- **By the agent itself** — after successfully completing a complex task, the agent may offer to save the approach as a skill
- **Manually** — by placing skill definitions in the appropriate directory
- **Via plugins** — plugin bundles can include pre-built skills

### Skill Features

Skills can include:
- **Trigger conditions** — when should the agent load this skill?
- **Step-by-step procedures** — numbered actions with exact commands
- **Pitfalls and edge cases** — known issues and workarounds
- **Verification steps** — how to confirm the task succeeded
- **Reference files** — templates, configs, scripts bundled with the skill
- **Environment requirements** — required commands, env vars, credential files

---

## 19. MCP Servers

MCP (Model Context Protocol) servers extend agent capabilities by providing additional tools and context sources.

### Managing MCP Servers

```
/mcp
```

Opens the **MCP Server Manager** — an interactive panel for configuring MCP connections.

### MCP Server Configuration

MCP servers can be configured to connect via:

| Transport | Description |
|---|---|
| **stdio** | Launch a local process and communicate over stdin/stdout |
| **HTTP** | Connect to a remote MCP server over HTTP |
| **OAuth** | Authenticated HTTP connection with token-based auth |

### Adding an MCP Server

From the `/mcp` panel, you can:
- **Add new servers** — specify name, transport type, and connection details
- **Enable/disable** — toggle servers on and off
- **Test connections** — verify the server is reachable
- **View tools** — inspect what tools a server provides

### MCP OAuth Handling

For OAuth-based MCP servers:

1. Configure the server URL and OAuth endpoints
2. The CLI initiates the OAuth flow
3. A browser window opens for authentication (or an auth URL is printed for SSH)
4. Tokens are stored and automatically refreshed

---

## 20. Workspace Context Files

Antigravity CLI reads context files to understand your project's conventions and constraints before making changes.

### Supported Files

| File | Location | Purpose |
|---|---|---|
| `GEMINI.md` | Project root | Project-specific rules, conventions, commands |
| `AGENTS.md` | Project root | Alternative filename for project rules |
| `~/.gemini/GEMINI.md` | User home | Global rules applied to all projects |

### Example GEMINI.md

```markdown
# Project Rules

## Build Commands
- Build: `npm run build`
- Test: `npm test -- --coverage`
- Lint: `npm run lint`
- Format: `npm run format`

## Code Style
- TypeScript strict mode: always
- Prettier for formatting (single quotes, no semicolons)
- Jest for testing, React Testing Library for components

## Architecture
- `src/components/` — React components
- `src/services/` — API calls and business logic
- `src/utils/` — pure utility functions
- No default exports — always use named exports

## Conventions
- Error messages should be user-facing (not technical)
- API responses must include a `requestId` field
- Database queries go through `src/services/db.ts` only
```

### How Context Files Are Used

1. On launch, the agent parses all context files
2. On each turn, the agent consults these rules before proposing changes
3. Rules can specify:
   - Build and test commands
   - Code style preferences
   - Architecture constraints
   - Naming conventions
   - Deprecation warnings
   - Security policies

### Best Practices

- **Be specific** — write exact test commands the agent should run
- **Include architecture notes** — file structure, module boundaries
- **Document anti-patterns** — things the agent should avoid
- **Keep it current** — stale rules cause agent confusion
- **Use both levels** — project-specific in `GEMINI.md`, global defaults in `~/.gemini/GEMINI.md`

---

## 21. Migrating from Gemini CLI

### Timeline

| Date | Event |
|---|---|
| May 19, 2026 | Antigravity CLI announced; migration command available |
| June 18, 2026 | Gemini CLI stops serving requests for individual-tier accounts |

**Enterprise carveout:** Gemini CLI continues for Google Cloud Code Assist Standard/Enterprise and paid API key users.

### Migration Command

The migration is a one-time import:

```bash
agy plugin import gemini
```

### What Migrates

| Gemini CLI Component | Antigravity CLI Equivalent | Notes |
|---|---|---|
| Extensions | Plugins | Namespace and format changed |
| Commands | Skills | Automatic conversion |
| MCP Servers | MCP Servers | Direct migration |
| Hooks | Hooks | Direct migration |
| Skills | Skills | Direct migration |
| Settings | Settings | Some manual adjustment needed |

### What Does NOT Migrate

- Custom agent definitions — different format in Antigravity
- Extension-specific metadata
- Session/conversation history — start fresh in Antigravity CLI
- Some permission configurations — review `/permissions` after migration

### Post-Migration Checklist

1. **Verify plugins loaded:** `agy plugin list`
2. **Test skills:** `/skills` — browse and verify all skills appear
3. **Check MCP servers:** `/mcp` — confirm connections work
4. **Review permissions:** `/permissions` — set your preferred mode
5. **Test a simple task:** Run a small prompt to confirm the agent works
6. **Update context files:** Ensure `GEMINI.md` or `AGENTS.md` is in place
7. **Test in a disposable directory first** — before migrating production workflows

### Migration Pitfalls

- `agy plugin import gemini` returning "no plugins found" — check that Gemini CLI extensions directory exists at the expected path
- Skills not appearing — some Gemini CLI commands may not convert cleanly; expect manual fixes
- MCP auth tokens — OAuth tokens may need re-authorization after migration
- Plugin conflicts — if a plugin name collides with an existing one, rename before importing

---

## 22. Scripting & Automation

### Non-Interactive Mode (`--print` / `-p`)

The `--print` flag runs the agent in one-shot mode — it executes the prompt and returns output without entering the TUI. Ideal for scripting, CI/CD, and git hooks.

```bash
# Simple one-shot query
agy --print "Summarize this repo in 3 bullets"

# Code fixes
agy -p "Fix all ESLint errors in src/"

# Generate documentation
agy -p "Generate JSDoc comments for all exported functions"

# Run tests and fix failures
agy -p "Run the test suite and fix any failing tests"
```

### With Timeout

```bash
# Allow up to 5 minutes for a complex task
agy --print "Refactor the authentication module" --print-timeout 300
```

### Scripting Patterns

**Git pre-commit hook:**

```bash
#!/bin/bash
# .git/hooks/pre-commit
agy -p "Check all staged files for lint errors and fix them" --print-timeout 120
```

**CI pipeline step:**

```yaml
# .github/workflows/ci.yml
- name: AI Code Review
  run: |
    agy -p "Review the diff from the last commit and suggest improvements" --print-timeout 180
```

**Automated PR description:**

```bash
agy -p "Read the git diff and generate a comprehensive PR description" --print-timeout 60
```

### Combining with Other Tools

```bash
# Pipe output to a file
agy -p "Generate a README.md for this project" > README.md

# Use with jq for structured output
agy -p "List all API endpoints in this project as JSON" | jq .

# Chain with other commands
agy -p "Find all TODO comments" && git add -A && git commit -m "Resolved TODOs"
```

### Limitations of `--print` Mode

- No interactive approval — the agent runs with your configured permission mode
- No subagent spawning — single-threaded execution
- No artifact review — diffs are applied directly (or not, depending on permissions)
- Output is plain text (not TUI-rendered)

---

## 23. Customizing Status Line & Terminal Title

### Status Line

The status bar at the top of the TUI shows real-time agent metadata. You can customize it via `/statusline` or `settings.json`.

#### Built-in Status Bar Information

By default, the status line shows:
- CLI version
- Authenticated user
- Active model
- Current workspace
- Conversation UUID

#### Custom Status Line Script

Create a shell script that receives live agent metadata as JSON via stdin:

```bash
# ~/.gemini/antigravity-cli/scripts/status.sh
#!/bin/bash
# The agent pipes JSON to this script: {"cwd":"...","model":"...","tokens":1234,"state":"thinking",...}
read -r metadata
cwd=$(echo "$metadata" | jq -r '.cwd')
model=$(echo "$metadata" | jq -r '.model')
state=$(echo "$metadata" | jq -r '.state')
tokens=$(echo "$metadata" | jq -r '.tokens')

printf "📍 %s | 🧠 %s | %s | %s tokens" "$cwd" "$model" "$state" "$tokens"
```

Make it executable:

```bash
chmod +x ~/.gemini/antigravity-cli/scripts/status.sh
```

Configure in `settings.json`:

```json
{
  "statusLine": {
    "enabled": true,
    "script": "~/.gemini/antigravity-cli/scripts/status.sh"
  }
}
```

#### Available Metadata Fields

| Field | Type | Description |
|---|---|---|
| `cwd` | string | Current working directory |
| `model` | string | Active model name |
| `tokens` | number | Tokens used in current turn |
| `state` | string | Agent state: `thinking`, `executing`, `idle` |
| `project` | string | Project/workspace name |
| `conversation` | string | Conversation UUID |
| `subagents` | number | Count of active subagents |

### Terminal Title

Toggle terminal window title updates:

```
/title on
/title off
```

Configure in `settings.json`:

```json
{
  "terminalTitle": {
    "enabled": true,
    "format": "agy: {project} — {model}"
  }
}
```

**Available template variables:**
- `{project}` — workspace name
- `{model}` — active model
- `{cwd}` — current working directory
- `{state}` — agent state

---

## 24. Best Practices

### 1. Establish Verification Loops

The single most effective way to ensure reliable agent output:

1. **Ensure a test suite exists** in your workspace
2. If none, **direct the agent to write tests first**
3. After the agent proposes code, **instruct it to run the tests**
4. The agent will iterate on test output automatically

```
> Write unit tests for the UserService class, then run them to verify
```

### 2. Explore, Plan, Then Execute

Break complex changes into three phases:

**Phase 1 — Exploration:**
```
> Explain how authentication works in this codebase
```

**Phase 2 — Planning:**
```
> Create an implementation plan for adding OAuth support
```

The agent produces an artifact listing targeted files, dependencies, and logic overrides. Review and approve the plan.

**Phase 3 — Execution:**
```
> Implement the approved OAuth support plan
```

### 3. Enrich Your Prompt Context

- Use `@` path autocomplete to target specific files
- Paste screenshots (`Ctrl+V`) for visual issues
- Be specific about success criteria
- Reference existing patterns in the codebase

### 4. Write Good Context Files

A well-crafted `GEMINI.md` dramatically improves agent accuracy:

- **Build commands** — exact test, lint, format, and build commands
- **Architecture notes** — module structure, boundaries, patterns
- **Anti-patterns** — things the agent should never do
- **Naming conventions** — file, variable, function naming rules
- **Security policies** — what the agent is never allowed to access

### 5. Manage Sessions Proactively

- **Press `Esc` early** — interrupt the agent the moment it goes off-track
- **Use `/rewind`** — roll back to a checkpoint instead of starting over
- **Use `/fork`** — branch for speculative experiments without losing progress
- **Use `/clear`** — reset context when it gets cluttered with irrelevant history

### 6. Tune Permissions for Your Workflow

| Workflow | Recommended Mode |
|---|---|
| Learning/exploring a codebase | `strict` — review everything |
| Daily development | `request-review` — approve writes and commands |
| CI/CD or scripting (`-p`) | `always-proceed` or `proceed-in-sandbox` |
| High-security environments | `strict` + `enableTerminalSandbox` |

### 7. Leverage Subagents

```
> Run the test suite, lint the code, and check for security vulnerabilities — all in parallel
```

The agent spawns three subagents simultaneously. Use `/agents` to monitor.

### 8. Use `--print` for Automation

```bash
# Pre-commit hook
agy -p "Format all staged files and fix lint errors" --print-timeout 120

# Daily standup summary
agy -p "Summarize yesterday's git commits in bullet points" --print-timeout 30
```

---

## 25. Troubleshooting

### Quick Symptom Table

| Symptom | Cause | Resolution |
|---|---|---|
| `agy: command not found` | Binary not in PATH | Add `~/.local/bin` (or Windows equivalent) to PATH |
| Keyring / DBUS errors | Keyring daemon not running | Start keyring daemon; unlock keychain |
| SSH clipboard paste fails | Protocol doesn't forward clipboard | Use iTerm2/Ghostty; configure OSC 52 |
| Update hangs / fails | Advisory lock stuck | Remove `~/.gemini/antigravity-cli/updater/update.lock` |
| Auth loops / fails | Keyring permission issue | Re-authorize keyring access; try `/logout` then re-launch |
| WSL auth opens wrong browser | WSL browser routing | Use SSH auth flow: copy URL, open on Windows host |
| Rate limit errors | Credits exhausted or tier limit | Check `/usage`; configure fallback model |
| Plugin import fails | Gemini CLI extensions not found | Verify extensions directory exists; check path |
| MCP connection fails | Server unreachable or auth expired | Test server independently; re-auth OAuth tokens |

### Configure Your Shell PATH

**Symptom:** `agy: command not found`

**macOS / Linux:**

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"

# Reload
source ~/.bashrc
```

**Windows (PowerShell — as Administrator):**

```powershell
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";$env:LocalAppData\agy\bin", "User")
```

Restart your terminal after.

### Authorize Keyring Permissions

**Symptom:** CLI hangs, prints DBUS warnings, or throws keyring exceptions.

**macOS:**
1. Open **Keychain Access**
2. Search for "Antigravity CLI"
3. Right-click → **Get Info** → **Access Control**
4. Verify `agy` is on the allowed applications list
5. For headless SSH: `security unlock-keychain ~/Library/Keychains/login.keychain-db`

**Linux:**
- Ensure GNOME Keyring or KWallet is running and unlocked
- For headless/SSH, initialize a D-Bus session:

```bash
export $(dbus-launch)
gnome-keyring-daemon --start --components=secrets
```

### Enable Clipboard Forwarding (SSH)

**Symptom:** `Ctrl+V` paste fails in SSH sessions.

1. Use iTerm2 or Ghostty (support advanced clipboard channels)
2. **iTerm2:** Preferences → General → Selection → Check "Applications in terminal may access clipboard"
3. **tmux:** Ensure OSC 52 is configured:

```bash
# ~/.tmux.conf
set -g allow-passthrough on
set -g set-clipboard on
```

### Resolve Self-Updater Locks

**Symptom:** Launch hangs with advisory lock warning.

```bash
# Release the lock
rm ~/.gemini/antigravity-cli/updater/update.lock
```

To disable auto-updates permanently:

```bash
# Add to ~/.bashrc or ~/.zshrc
export AGY_NO_AUTO_UPDATE=1
```

### WSL Auth Issues

On WSL, token storage is file-based (no system keyring). Auth issues are usually local-file or session-state problems:

1. Try `/logout` then re-launch
2. Use the SSH auth flow: when the URL is printed, open it on your Windows host browser
3. Check write permissions on `~/.gemini/antigravity-cli/`

### Rate Limits

Separate limits exist at multiple levels:

| Level | What Counts |
|---|---|
| **Account** | Your Google AI Pro/Ultra subscription tier |
| **Plan** | Daily/monthly credit allocation |
| **Model** | Per-model rate limits (Claude models have separate limits) |
| **CLI Session** | Concurrent request limits per session |

Check current usage with `/usage`.

---

## 26. Core Paths & File Layout

### Complete Filesystem Reference

```
~/.gemini/antigravity-cli/
├── settings.json              # User preferences and permissions
├── keybindings.json           # Keyboard shortcut mappings
├── history.jsonl              # Prompt history (JSON lines)
├── conversations/             # Saved conversation threads
│   ├── <uuid-1>.json
│   ├── <uuid-2>.json
│   └── ...
├── brain/                     # Agent's learned patterns and artifacts
│   └── ...
├── plugins/                   # Installed plugins
│   ├── <plugin-name>/
│   │   ├── skills/
│   │   ├── agents/
│   │   ├── rules/
│   │   ├── mcpServers/
│   │   └── hooks/
│   └── ...
├── log/                       # Session logs
│   ├── cli-2026-06-01.log
│   ├── cli-2026-06-02.log
│   └── ...
├── updater/                   # Self-updater state
│   ├── update.lock
│   └── last_check.timestamp
└── scripts/                   # Custom scripts (status line, etc.)
    └── status.sh
```

### Key Files

| File | Format | Purpose |
|---|---|---|
| `settings.json` | JSON | All user preferences, permissions, model selection |
| `keybindings.json` | JSON | Custom keyboard shortcuts |
| `history.jsonl` | JSON Lines | Prompt history for search and recall |
| `conversations/*.json` | JSON | Full conversation threads (one per UUID) |
| `brain/*` | Various | Agent's learned information and cache |
| `log/cli-*.log` | Text | Session logs for debugging |
| `updater/update.lock` | Lock file | Prevents concurrent updates |
| `updater/last_check.timestamp` | Timestamp | Debounce marker (15-min TTL) |

### Global Context File

```
~/.gemini/GEMINI.md            # Global workspace rules (applied to all projects)
```

### Binary Location

| Platform | Path |
|---|---|
| macOS / Linux | `~/.local/bin/agy` |
| Windows | `C:\Users\<Username>\AppData\Local\agy\bin\agy.exe` |

---

## 27. Platform Comparison — CLI vs 2.0 vs IDE

### Comparison Table

| Feature | Antigravity CLI | Antigravity 2.0 | Antigravity IDE |
|---|---|---|---|
| **Type** | Terminal TUI | Desktop GUI | Editor-centric IDE |
| **Interface** | Keyboard-driven | Mouse + keyboard | Code editor |
| **Install size** | ~15 MB (single Go binary) | ~200 MB | ~300 MB |
| **Resource usage** | Near-zero | Moderate | Higher |
| **SSH support** | Native | Via remote containers | No |
| **tmux/screen** | Full support | No | No |
| **Subagents** | Yes (background) | Yes (visual panel) | Yes |
| **Artifacts review** | TUI picker + detail viewer | Visual diff viewer | In-editor |
| **Voice** | No | Yes | No |
| **Scheduled tasks** | No | Yes | No |
| **Multi-project** | Via `/add-dir` | Full workspace management | Single project |
| **Plugin system** | Yes | Yes | Limited |
| **MCP support** | Yes | Yes | Yes |
| **Settings sync** | Bidirectional with 2.0 | Bidirectional with CLI | Separate |
| **Conversation export** | To 2.0 | To CLI | To 2.0 |
| **Browser interaction** | Limited (`/browser` in 2.0) | Full Chrome DevTools | Through agent |
| **Scripting** | `--print` flag | SDK | SDK |

### Decision Matrix

**Choose Antigravity CLI when:**
- You work primarily in the terminal
- You SSH into remote machines frequently
- You want minimal resource overhead
- You prefer keyboard-only workflows
- You need to script agent interactions (`--print`)

**Choose Antigravity 2.0 when:**
- You want visual diff review and artifact previews
- You need to orchestrate multiple agents side-by-side
- You use scheduled/recurring agent tasks
- You want voice interaction
- You prefer visual navigation

**Choose Antigravity IDE when:**
- You want a full IDE experience with integrated agent assistance
- You need deep codebase analysis within an editor
- You prefer traditional editor workflows (file tree, tabs, etc.)

### Using Them Together

The surfaces are designed to complement each other:

1. **Start in CLI** for quick tasks and SSH work
2. **Export to 2.0** when tasks grow complex and need visual orchestration
3. **Use IDE** for deep, editor-centric development sessions
4. **Settings sync automatically** — preferences and permissions follow you

---

## Appendix A: Quick Reference Card

### Essential Shell Commands

```bash
agy                                    # Launch interactive TUI
agy --version                          # Print version
agy --print "prompt"                   # Non-interactive one-shot
agy -c                                 # Resume most recent conversation
agy --sandbox                          # Launch with sandbox enabled
agy update                             # Update to latest version
agy plugin list                        # List installed plugins
agy plugin import gemini               # Migrate from Gemini CLI
```

### All Slash Commands

```
/resume, /switch, /conversation     Conversation picker
/rewind, /undo                      Roll back history
/rename <name>                      Rename session
/fork, /branch                      Clone session
/clear                              Clear terminal
/new                                New conversation
/config, /settings                  Settings editor
/model                              Model selection
/permissions                        Permission mode
/keybindings                        Shortcut editor
/statusline                         Status bar config
/title [on|off]                     Terminal title toggle
/planning                           Plan-before-execute mode
/fast                               Skip reasoning plans
/agents                             Subagent manager
/tasks                              Task manager
/skills                             Skills browser
/mcp                                MCP server manager
/hooks                              Hooks browser
/diff                               Show file diffs
/open <path>                        Open in editor
/usage                              Help manual
/add-dir <path>                     Add workspace directory
/btw <query>                        Background question
/logout                             Sign out
/exit                               Quit
```

### Permission Modes

```
request-review    Default — prompt before writes and commands
always-proceed    No prompts — full autonomy
strict            Always prompt for non-read operations
proceed-in-sandbox  Safe commands auto-run in sandbox
```

### Key Paths

```
~/.gemini/antigravity-cli/settings.json       Settings
~/.gemini/antigravity-cli/keybindings.json    Keybindings
~/.gemini/antigravity-cli/conversations/      Saved conversations
~/.gemini/antigravity-cli/plugins/            Installed plugins
~/.gemini/antigravity-cli/log/                Session logs
~/.gemini/antigravity-cli/brain/              Agent brain
~/.gemini/antigravity-cli/history.jsonl       Prompt history
~/.gemini/GEMINI.md                           Global context rules
~/.local/bin/agy                              Binary (macOS/Linux)
```

### Essential Keyboard Shortcuts

```
Esc              Cancel / close / interrupt
Enter            Submit prompt
Ctrl+C           Exit CLI
Ctrl+L           Clear screen
Shift+Enter      Newline in prompt
Ctrl+J           Newline in prompt
Ctrl+G           Open $EDITOR for prompt
Ctrl+R           Open artifact review
Ctrl+V           Paste media/clipboard
Ctrl+K           Fast-approve subagent action
Alt+J            Teleport to subagent
Ctrl+A           Cursor to line start
Ctrl+E           Cursor to line end
Ctrl+Z           Undo text
Ctrl+Shift+Z     Redo text
Ctrl+O           Toggle tool reasoning output
```

---

## Appendix B: Complete Example Workflows

### Workflow 1: New Project Setup

```bash
# 1. Create a new project directory
mkdir my-api && cd my-api

# 2. Create a GEMINI.md context file
cat > GEMINI.md << 'EOF'
# Project Rules
## Build & Test
- Install: `npm install`
- Test: `npm test`
- Lint: `npm run lint`
- Start: `npm start`

## Tech Stack
- Node.js + Express
- TypeScript (strict mode)
- Jest for testing
- PostgreSQL with Prisma ORM

## Conventions
- RESTful API design
- Error responses: { error: string, details?: any }
- All endpoints require input validation
- Database access only through Prisma service layer
EOF

# 3. Launch Antigravity CLI
agy

# 4. In the TUI:
# > Initialize a Node.js Express TypeScript project with Prisma, Jest, and ESLint
#
# Agent creates package.json, tsconfig.json, jest.config.js, .eslintrc.js
# Agent installs dependencies
# Review artifacts with Ctrl+R, approve
#
# > Create a basic Express server with health check endpoint
# > Add a User model in Prisma schema and generate the migration
# > Create CRUD endpoints for users with input validation

# 5. Verify everything works:
# > Run the test suite and fix any failures
```

### Workflow 2: Bug Fix with Parallel Subagents

```bash
# 1. Launch and resume
agy --continue

# 2. Describe the bug
# > The login endpoint returns 500 when email has a '+' character.
# > Find the root cause and fix it.
#
# Agent explores the codebase, finds the issue in email validation regex.
# Agent proposes a fix.

# 3. Run verification in parallel
# > Run the full test suite, check for similar regex issues in other validators,
# > and verify the fix handles edge cases — all in parallel
#
# Agent spawns 3 subagents:
#   - Subagent 1: Runs test suite
#   - Subagent 2: Searches for similar regex patterns
#   - Subagent 3: Tests edge cases (unicode, special chars, long emails)

# 4. Monitor progress
/agents
# Review subagent results

# 5. Approve and apply
Ctrl+R  # Open artifact review
# Review the diff
y       # Approve
Esc     # Submit
```

### Workflow 3: Code Review with Fork

```bash
# 1. Start a review
agy

# > Review the auth module for security vulnerabilities
#
# Agent analyzes the code and reports findings

# 2. Experiment safely with a fork
/fork

# > Implement JWT token refresh with rotation, ignoring the current session approach
#
# Agent works on the forked session — original session is preserved

# 3. If the experiment works:
# Note the changes, switch back
/resume  # Return to original session
# > Apply the JWT token refresh approach from the fork

# 4. If the experiment fails:
/resume  # Return to original session
# Original work is untouched
```

### Workflow 4: CI/CD Integration

```bash
# .github/workflows/ai-review.yml
name: AI Code Review
on: [pull_request]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: AI Code Review
        run: |
          agy -p "Review the changes in this PR. Focus on:
            1. Security vulnerabilities
            2. Performance regressions
            3. Breaking API changes
            4. Missing test coverage
            Provide a structured report." --print-timeout 300 > review.md

      - name: Post Review
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const review = fs.readFileSync('review.md', 'utf8');
            github.rest.issues.createComment({
              ...context.repo,
              issue_number: context.issue.number,
              body: review
            });
```

### Workflow 5: Migrating from Gemini CLI

```bash
# 1. Install Antigravity CLI
curl -fsSL https://antigravity.google/cli/install.sh | bash

# 2. Verify installation
agy --version

# 3. Import Gemini CLI extensions
agy plugin import gemini

# Sample output:
# [ok]    conductor
#           ✔ commands    : 6 processed (converted to skills)
# [ok]    google-workspace
#           ✔ skills      : 6 processed
#           ✔ commands    : 4 processed (converted to skills)
#           ✔ mcpServers  : 2 processed

# 4. Verify the import
agy plugin list

# 5. Launch and check settings
agy
/config        # Review settings
/permissions   # Set permission mode
/skills        # Verify skills are available
/mcp           # Check MCP server connections

# 6. Test with a simple task
# > List all the available skills and their descriptions

# 7. Update context files
# Ensure GEMINI.md or AGENTS.md exists in your projects
```

---

*End of Antigravity CLI Complete Guide*
