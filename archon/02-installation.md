# 02 — Installation & Setup

**Goal:** Get Archon installed and configured on your machine.

---

## 2.1 Prerequisites

| Requirement | Why | Install |
|---|---|---|
| **Bun** 1.x+ | JavaScript runtime + package manager | `curl -fsSL https://bun.sh/install \| bash` |
| **Claude Code** | The AI agent runtime | `curl -fsSL https://claude.ai/install.sh \| bash` |
| **GitHub CLI** (`gh`) | PR creation, issue fetching | `brew install gh` (macOS) / `winget install GitHub.cli` (Windows) / `sudo apt install gh` (Linux) |
| **Git** 2.30+ | Worktree support required | Usually pre-installed |
| **Anthropic API Key** | Required for Claude | Get from console.anthropic.com |

## 2.2 Full Setup (from scratch)

```bash
# Step 1: Install prerequisites
curl -fsSL https://bun.sh/install | bash
curl -fsSL https://claude.ai/install.sh | bash
# Install GitHub CLI for your OS (see above)

# Step 2: Authenticate GitHub CLI
gh auth login

# Step 3: Clone and set up Archon
git clone https://github.com/coleam00/Archon
cd Archon
bun install

# Step 4: Run the setup wizard
claude
# Say: "Set up Archon"
```

The wizard will:
1. Install the Archon CLI binary
2. Configure API credentials (Anthropic key)
3. Set up platform integrations (GitHub, Slack, Telegram — optional)
4. Create `~/.archon/config.yaml`
5. Copy the Archon skill into your target project

> **Important:** Always run Claude Code from YOUR PROJECT, not the Archon repo directory.

## 2.3 Quick Install (30 seconds)

For users who already have Claude Code installed:

```bash
# macOS / Linux
curl -fsSL https://archon.diy/install | bash

# Windows (PowerShell)
irm https://archon.diy/install.ps1 | iex

# Homebrew
brew install coleam00/archon/archon
```

## 2.4 CLAUDE_BIN_PATH Configuration

Compiled binaries need to know where Claude Code lives.

**Option A: Environment variable**
```bash
export CLAUDE_BIN_PATH="$HOME/.local/bin/claude"     # macOS/Linux
$env:CLAUDE_BIN_PATH = "$env:USERPROFILE\.local\bin\claude.exe"  # Windows
```

**Option B: Config file** (`~/.archon/config.yaml`)
```yaml
assistants:
  claude:
    claudeBinaryPath: /home/user/.local/bin/claude
```

## 2.5 Docker Deployment

```bash
git clone https://github.com/coleam00/Archon
cd Archon

# Copy and edit override file with your API keys
cp docker-compose.override.example.yml docker-compose.override.yml
# Edit docker-compose.override.yml

docker compose up -d
```

The Docker image ships with Claude Code pre-installed.

## 2.6 Configuration Files

| File | Purpose |
|---|---|
| `~/.archon/config.yaml` | Provider, model, platform tokens, assistant paths |
| `.archon/workflows/` | Your custom YAML workflow files (committed to repo) |
| `.archon/commands/` | Custom `.md` command files referenced by workflows |
| `.archon/scripts/` | TypeScript/Python scripts for script nodes |
| `~/.archon/workflows/` | Global workflows — apply to ALL projects |
| `~/.archon/archon.db` | SQLite database (sessions, runs, conversations) — auto-created |

## 2.7 Example `~/.archon/config.yaml`

```yaml
provider: anthropic
model: claude-sonnet-4

assistants:
  claude:
    claudeBinaryPath: /home/user/.local/bin/claude

platforms:
  github:
    token: ghp_xxxxxxxxxxxx
  slack:
    botToken: xoxb-xxxxxxxxxxxx
    signingSecret: xxxxxxxxxxxx
  telegram:
    botToken: "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"

database:
  url: sqlite://~/.archon/archon.db
```

## 2.8 Verifying Your Installation

```bash
# Check CLI version
archon --version

# Start Web UI
archon serve
# Or from source: cd Archon && bun run dev

# In your project
cd /path/to/your/project
claude
> What archon workflows do I have?
> Use archon to list the project structure and explain what it does
```

## 2.9 Common Setup Issues

| Symptom | Fix |
|---|---|
| "Claude Code not found" | Set `CLAUDE_BIN_PATH` or configure in `~/.archon/config.yaml` |
| `gh` not authenticated | Run `gh auth login` |
| `bun install` fails | Check Node.js version (needs 18+) with `node --version` |
| Workflow not found | Ensure file is in `.archon/workflows/` (not directly in `.archon/`) |
| Web UI won't start | Check port 3000 is free. Try `archon serve --port 3001` |

---

**Next:** [03 — Workflow Basics](./03-workflow-basics.md)
