
### `/mcp`
Manage MCP (Model Context Protocol) server connections and OAuth authentication.

**Example 1:** Add a Postgres MCP server for direct database access.
```
/mcp
```

---

### `/permissions`
Manage allow/ask/deny rules for tool permissions. Interactive dialog with rule management.

Each rule targets a tool (or tool pattern) and assigns one of three actions:
- **allow** — Claude runs the tool without prompting
- **ask** — Claude prompts you for approval before running
- **deny** — Claude is blocked from using the tool entirely

Rules live in settings files — project-level (`.claude/settings.json`) or user-level (`~/.claude/settings.json`) — and the more specific rule always wins.

**Example 1:** Permanently allow npm commands without prompting.
```
/permissions
```
Add a rule: `Tool: Bash | Pattern: npm * | Action: allow`

Result in `.claude/settings.json`:
```json
{
  "permissions": {
    "allow": ["Bash(npm *)"]
  }
}
```
Now Claude runs `npm install`, `npm run build`, etc. silently without prompting.

**Example 2:** Block a dangerous command (deny rule).
```json
{
  "permissions": {
    "deny": ["Bash(rm *)"]
  }
}
```
If Claude tries `rm -rf dist/`, it is hard-blocked — even if a global allow rule exists. `deny` is absolute.

**Example 3:** Require approval for git push (ask rule).
```json
{
  "permissions": {
    "ask": ["Bash(git push*)"]
  }
}
```
Claude drafts the command, pauses, shows what it will run, and waits for your yes/no before proceeding.

**Example 4 — Precedence: project overrides global.**
```
~/.claude/settings.json   (global)  → allow: ["Bash(*)"]
.claude/settings.json     (project) → deny:  ["Bash(psql*)"]
```
When Claude tries `psql -U admin`, the **project deny wins** even though global allows all Bash.

**Example 5 — Precedence: specific pattern beats wildcard.**
```json
{
  "permissions": {
    "allow": ["Bash(git *)"],
    "deny":  ["Bash(git push --force*)"]
  }
}
```
- `git status` → allowed
- `git push origin main` → allowed
- `git push --force origin main` → **denied** (more specific pattern wins)

**Precedence order:**
```
project deny  >  project allow  >  global deny  >  global allow
more specific pattern  >  less specific pattern (within same scope)
```

---

### `/hooks`
View hook configurations that execute on tool events.

**Example:**
```
/hooks
```

---

## Utilities & Tools

### `/copy`
Copy the last assistant response to clipboard. Pass a number to copy the Nth-latest response.

**Example 1:** Copy Claude's last code block to paste into your editor.
```
/copy
```

**Example 2:** Copy the second-to-last response.
```
/copy 2
```

---

### `/export`
Export the current conversation as plain text. Useful for sharing session context with a teammate as a read-only reference — they get the full history but cannot resume it as a live session. See [Sharing Sessions with Teammates](#sharing-sessions-with-teammates-cross-machine) for other sharing options.

**Example 1:** Save the session as a reference doc.
```
/export refactor-session-2026-05-17.txt
```

---

### `/btw`
Ask a quick side question without polluting conversation history.

**Example 1:** Check a fact without derailing the current task.
```
/btw what's the current git commit SHA?
```

**Example 2:** Quick syntax lookup.
```
/btw what's the PowerShell equivalent of grep -r?
```

---

### `/recap`
Generate a one-line summary of the current session.

**Example:**
```
/recap
```

---

## Help & Diagnostics

### `/help`
Show available commands and usage information.

**Example:**
```
/help
```

---

### `/doctor`
Diagnose and verify your Claude Code installation and settings. Press `f` to auto-fix issues.

**Example 1:** Something feels off after an update — run a health check.
```
/doctor
```

---

### `/status`
Open the Settings interface showing version, model, account, and connectivity status.

**Example:**
```
/status
```

---

### `/usage`
Show session cost, plan usage limits, and activity statistics. Aliases: `/cost`, `/stats`.

**Example 1:** Check how much of your monthly quota you've used.
```
/usage
```

---

### `/debug`
Enable debug logging and troubleshoot issues. Optionally describe the problem.

**Example 1:** Session keeps freezing — enable debug logging to investigate.
```
/debug session freezing after large file reads
```

---

### `/feedback`
Submit feedback or a bug report. Alias: `/bug`.

**Example:**
```
/feedback /compact seems to lose important context when used mid-task
```

---

### `/heapdump`
Write a JavaScript heap snapshot to your Desktop for diagnosing high memory usage.

**Example:**
```
/heapdump
```

---

### `/insights`
Generate a report analyzing your Claude Code usage patterns, friction points, and project areas.

**Example:**
```
/insights
```

---

### `/release-notes`
View the changelog with an interactive version picker.

**Example:**
```
/release-notes
```

---

## Settings & Configuration

### `/config`
Open the Settings interface to adjust theme, model, output style, and preferences. Alias: `/settings`.

**Example:**
```
/config
```

---

### `/theme`
Change the color theme: auto, light, dark, colorblind/daltonized, ANSI, or custom.

**Example 1:** Switch to dark theme for a night session.
```
/theme
```

---

### `/keybindings`
Open or create the keybindings configuration file.

**Example:**
```
/keybindings
```

---

### `/tui`
Set the terminal UI renderer. `fullscreen` gives flicker-free alt-screen rendering.

**Example 1:** Eliminate terminal flickering.
```
/tui fullscreen
```

---

### `/focus`
Toggle focus view — shows only the last prompt, a tool-call summary, and the final response.

**Example:**
```
/focus
```

---

### `/statusline`
Configure Claude Code's status line in your shell prompt.

**Example 1:** Show git branch and token usage in the status line.
```
/statusline show git branch and token usage
```

---

## IDE & Platform Integration

### `/ide`
Manage IDE integrations and show status (VS Code, JetBrains, Cursor, etc.).

**Example:**
```
/ide
```

---

### `/terminal-setup`
Configure terminal keybindings for Shift+Enter and other shortcuts for your specific terminal/IDE.

**Example 1:** First time setting up Claude Code in VS Code's integrated terminal.
```
/terminal-setup
```

---

### `/desktop`
Continue the current session in the Claude Code Desktop app. Alias: `/app`.

**Example:**
```
/desktop
```

---

### `/voice`
Toggle voice dictation or set the mode (`hold`, `tap`, `off`). Requires a Claude.ai account.

**Example 1:** Dictate prompts hands-free while reading code.
```
/voice tap
```

---

### `/remote-control`
Make your session available for remote control from claude.ai. Alias: `/rc`. This is the easiest way to share a live session with a teammate on a different machine — they can observe and take over from their browser. See [Sharing Sessions with Teammates](#sharing-sessions-with-teammates-cross-machine) for other sharing options.

**Example 1:** Let a teammate observe and take over your session.
```
/remote-control
```

---

## Account & Authentication

### `/login`
Sign in to your Anthropic account.

**Example:**
```
/login
```

---

### `/logout`
Sign out from your Anthropic account.

**Example:**
```
/logout
```

---

### `/upgrade`
Open the upgrade page to switch to a higher plan tier.

**Example:**
```
/upgrade
```

---

### `/setup-bedrock`
Configure Amazon Bedrock authentication (interactive wizard). Only visible when `CLAUDE_CODE_USE_BEDROCK=1` is set.

**Example:**
```
/setup-bedrock
```

---

### `/setup-vertex`
Configure Google Vertex AI authentication (interactive wizard). Only visible when `CLAUDE_CODE_USE_VERTEX=1` is set.

**Example:**
```
/setup-vertex
```

---

## Cloud & Remote

### `/ultraplan`
Draft a plan in an ultraplan session, review it in the browser, then execute remotely or send back to your terminal.

**Example 1:** Plan a large schema migration interactively in the browser before running it.
```
/ultraplan migrate the database schema to support multi-tenancy
```

---

### `/web-setup`
Connect your GitHub account to Claude Code on the web using local `gh` CLI credentials.

**Example:**
```
/web-setup
```

---

### `/teleport`
Pull a Claude Code web session into your terminal. Opens a picker, fetches branch and conversation. Requires a Claude.ai subscription.

**Example 1:** Continue in your terminal a session you started on claude.ai.
```
/teleport
```

---

## Miscellaneous

### `/exit`
Exit the Claude Code CLI. In an attached background session, detaches without stopping it. Alias: `/quit`.

**Example:**
```
/exit
```

---

### `/powerup`
Discover Claude Code features through interactive lessons with animated demos.

**Example 1:** Onboarding to Claude Code for the first time.
```
/powerup
```

---

### `/skills`
List available skills and manage which ones are active. Press `t` to sort by token count.

**Example:**
```
/skills
```

---

### `/plugin`
Manage Claude Code plugins (install, uninstall, configure).

**Example:**
```
/plugin
```

---

### `/reload-plugins`
Reload active plugins to apply changes without restarting the session.

**Example:**
```
/reload-plugins
```

---

### `/team-onboarding`
Generate a team onboarding guide from the last 30 days of usage history. Returns a shareable link.

**Example 1:** Onboard a new engineer to your Claude Code workflows.
```
/team-onboarding
```

---

### `/privacy-settings`
View and update your privacy settings (Pro and Max plans only).

**Example:**
```
/privacy-settings
```

---

### `/extra-usage`
Configure extra usage to keep working when plan rate limits are hit.

**Example:**
```
/extra-usage
```

---

### `/radio`
Open Claude FM lo-fi radio in the browser while you code.

**Example:**
```
/radio
```

---

### `/mobile`
Show a QR code to download the Claude mobile app. Aliases: `/ios`, `/android`.

**Example:**
```
/mobile
```

---

### `/stickers`
Order Claude Code stickers.

**Example:**
```
/stickers
```

---

## Quick Reference by Use Case

| Scenario | Commands to Use |
|----------|----------------|
| **New project setup** | `/init` → `/memory` → `/mcp` → `/permissions` |
| **Active development** | `/plan` → `/model` → `/effort` → `/context` → `/compact` |
| **Before committing** | `/diff` → `/review` → `/security-review` → `/simplify` |
| **Large-scale refactor** | `/ultraplan` → `/batch` |
| **Long running task** | `/goal` or `/background` |
| **Debugging problems** | `/doctor` → `/debug` → `/heapdump` |
| **Context running low** | `/context` → `/compact` |
| **CI automation** | `/autofix-pr` or `/loop` |
| **Session management** | `/rename` → `/branch` → `/resume` |
| **Check costs** | `/usage` |

---

## MCP Dynamic Commands

MCP servers can expose prompts that appear as slash commands:

```
/mcp__<server-name>__<prompt-name>
```

**Example:** If you connect a Postgres MCP server, it might expose:
```
/mcp__postgres__describe-schema
```

These are auto-discovered from connected MCP servers via `/mcp`.

---

> **Tip:** Type `/` alone at the prompt to see all commands filtered for your current platform, plan, and environment.
