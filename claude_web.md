# Claude Code — Web & GitHub Commands: Complete Tutorial

A practical reference for every Claude Code command that touches **claude.ai** (web, mobile, remote) and **GitHub** (PRs, CI, Actions). Each command includes what it does, how to invoke it, and a real-life scenario.

---

## Table of Contents

1. [Claude Web Commands](#1-claude-web-commands)
   - [/teleport](#11-teleport)
   - [/remote-control](#12-remote-control)
   - [/remote-env](#13-remote-env)
   - [/autofix-pr](#14-autofix-pr)
   - [/ultraplan](#15-ultraplan)
   - [/ultrareview](#16-ultrareview--code-review-ultra)
   - [/desktop](#17-desktop)
   - [/schedule](#18-schedule)
   - [/mobile](#19-mobile)
   - [/voice](#110-voice)
   - [/team-onboarding](#111-team-onboarding)
   - [/workflows](#112-workflows)
   - [/color](#113-color)
   - [--remote flag](#114---remote-cli-flag)
   - [--channels flag](#115---channels-cli-flag)

2. [GitHub Commands](#2-github-commands)
   - [/install-github-app](#21-install-github-app)
   - [/web-setup](#22-web-setup)
   - [/review](#23-review-pr)
   - [/code-review --comment](#24-code-review---comment)
   - [/security-review](#25-security-review)
   - [/batch](#26-batch)
   - [--from-pr flag](#27---from-pr-cli-flag)
   - [--worktree with PR](#28---worktree--w-with-pr)
   - [claude ultrareview](#29-claude-ultrareview-cli-command)

3. [Cross-cutting: /autofix-pr (Web + GitHub)](#3-cross-cutting-autofix-pr)

4. [Real-Life Workflows](#4-real-life-workflows)

---

## 1. Claude Web Commands

These commands connect your local Claude Code terminal to the **claude.ai** ecosystem: web sessions, mobile app, remote control, and Anthropic-managed cloud infrastructure.

---

### 1.1 `/teleport`

**Aliases:** `/tp`  
**CLI flag:** `claude --teleport`  
**Direction:** Cloud → Local (pull a web session down to your terminal)

#### What it does
If you or a teammate started a task on **claude.ai/code** (the web UI), `/teleport` pulls that session — its full conversation history and the working branch — into your local terminal. The cloud session ends; you continue locally.

#### Prerequisites
- Clean git working tree (no uncommitted changes)
- You are in a local checkout of the same repository
- The branch created in the web session is pushed to the remote
- You are authenticated as the same claude.ai user

#### How to invoke

```bash
# From inside an active Claude Code terminal session:
/teleport

# OR from the shell before starting a session:
claude --teleport

# Pick from a list, or pass a specific session ID:
claude --teleport <session-id>
```

#### Real-life scenario

> You started a bug fix on claude.ai during your lunch break using only your phone/browser. Now you're back at your desk and need to run tests, edit config files, and use terminal tools.

```
1. Open your terminal in the project repo
2. Run: claude --teleport
3. A picker shows your active cloud sessions
4. Select the bug-fix session
5. Claude fetches the branch, checks it out, and resumes the conversation
   — you're now in full terminal mode with all local tools available
```

---

### 1.2 `/remote-control`

**Aliases:** `/rc`  
**CLI flags:** `--remote-control`, `--rc`  
**CLI command:** `claude remote-control` (server mode, no local interactive session)  
**Direction:** Local → Cloud (push your local session up so it's accessible from claude.ai or mobile)

#### What it does
Exposes your currently running **local** Claude Code session to claude.ai and the Claude mobile app. The session keeps running on your machine; you just get a URL/QR code to control it from any device. If your machine sleeps or the network drops, the session reconnects automatically when your machine comes back.

**Important:** Only one remote connection at a time. Close your terminal and the session ends.

#### How to invoke

```bash
# Inside an active session — enable remote control mid-session:
/remote-control

# At startup — start a session with remote control already enabled:
claude --remote-control "My Project"
claude --rc "My Project"

# Server mode — expose a session with no local interactive terminal:
claude remote-control --name "API Dev Server"
```

#### Enable for all sessions automatically

Open `/config` in Claude Code and toggle **"Enable Remote Control for all sessions"** — you'll never need to type `/remote-control` again.

#### Real-life scenario

> You started a long refactor at your desk. You need to step away but want to monitor progress and send occasional instructions from your phone.

```
1. In your terminal session, type: /remote-control
2. Claude prints a session URL and shows a QR code (press Space)
3. Scan the QR code with your phone — opens directly in the Claude iOS/Android app
4. From your phone you can:
   - Read Claude's progress updates
   - Send new instructions ("focus on the auth module next")
   - Approve or deny tool permission prompts
5. Your laptop keeps running the full session; phone is just a remote window
```

#### Server-mode scenario (headless EC2)

```bash
# On your EC2 instance (no interactive terminal needed):
claude remote-control --name "prod-hotfix" --remote-control-session-name-prefix ec2-box

# Now control it from claude.ai in your browser
# Session persists as long as EC2 is running
```

---

### 1.3 `/remote-env`

#### What it does
Lets you choose the **default environment configuration** that Anthropic-managed cloud agents use when you start a web session. This controls which VM preset (language runtimes, pre-installed tools, setup scripts) cloud sessions get by default.

#### How to invoke

```bash
/remote-env
```

Opens an interactive picker. You select the environment, and all subsequent cloud agent sessions use it as their default.

#### Real-life scenario

> Your project is a Java Spring Boot app. By default, cloud VMs set up a Node.js environment. You want Java 21 + Maven as the default so you don't have to configure it each time.

```
1. Type: /remote-env
2. Pick your pre-configured Java environment from the list
3. Future web sessions for this project start with Java 21 + Maven ready
```

---

### 1.4 `/autofix-pr`

> See [Section 3](#3-cross-cutting-autofix-pr) — this command spans both Web and GitHub.

---

### 1.5 `/ultraplan`

**Form:** `/ultraplan <prompt>`

#### What it does
Drafts a detailed implementation plan in a **cloud planning session**, shows it in your browser for review, and then lets you either:
- **Execute it remotely** — Anthropic-managed cloud runs the plan
- **Send it back to your terminal** — continue locally with the plan loaded

It's designed for large, multi-step tasks where you want to think before you code.

#### How to invoke

```bash
/ultraplan Refactor the payment module to support multiple currencies
/ultraplan Add OAuth2 login with Google and GitHub providers
/ultraplan Migrate all database queries from raw SQL to TypeORM
```

#### Real-life scenario

> You need to add a feature that touches 15 files across 4 layers of the stack. You want to see a full plan before any code changes.

```
1. Type: /ultraplan Add real-time notifications using WebSockets to the dashboard
2. Claude opens a browser tab showing a detailed plan:
   - Files to modify
   - New files to create
   - Order of changes
   - Risk areas
3. You review and edit the plan in the browser
4. Click "Execute Remotely" to run it as a cloud session
   — OR — click "Send to Terminal" to execute it locally
```

---

### 1.6 `/ultrareview` / `/code-review ultra`

**Aliases:** `/ultrareview` is an alias for `/code-review ultra`  
**CLI command:** `claude ultrareview [target] [--json] [--timeout <minutes>]`

#### What it does
Runs a **deep, multi-agent code review in Anthropic's cloud sandbox**. Multiple specialized agents examine your diff in parallel — correctness, security, performance, style — and synthesize findings. Results appear in your terminal and can be posted as inline GitHub PR comments.

Includes 3 free runs on Pro/Max plans; subsequent runs require usage credits.

#### How to invoke

```bash
# Review the current branch diff (web UI):
/code-review ultra
/ultrareview

# Review a specific PR:
/code-review ultra 1234
/ultrareview 1234

# Post findings as inline GitHub PR comments:
/code-review ultra --comment

# From the shell (non-interactive, CI-friendly):
claude ultrareview 1234 --json
claude ultrareview 1234 --timeout 45
```

#### Real-life scenario

> You've implemented a new authentication flow touching session management, JWT tokens, and middleware. You want a thorough security-aware review before merging.

```bash
# Inside Claude Code:
/code-review ultra --comment

# Claude spins up a cloud sandbox, fans out agents:
#   → Agent 1: correctness & logic bugs
#   → Agent 2: security vulnerabilities (injection, token exposure)
#   → Agent 3: performance & efficiency
#   → Agent 4: simplification & cleanup
# Findings are synthesized and posted as inline comments on your GitHub PR
# You see a summary in the terminal and review full details on GitHub
```

---

### 1.7 `/desktop`

**Aliases:** `/app`  
**Availability:** macOS and Windows with a Claude subscription

#### What it does
Continues your current terminal session in the **Claude Code Desktop app**, preserving the full conversation. Useful when you want the desktop app's embedded browser preview, visual diff tools, or richer UI.

#### How to invoke

```bash
/desktop
# or
/app
```

#### Real-life scenario

> You started a frontend styling task in the terminal but want to use the Desktop app's built-in browser preview to visually verify CSS changes.

```
1. In terminal Claude Code, type: /desktop
2. The Claude Code Desktop app opens with your conversation intact
3. Desktop app auto-launches your dev server and takes screenshots
4. You can see visual before/after of your CSS changes without leaving Claude
```

---

### 1.8 `/schedule`

**Aliases:** `/routines`

#### What it does
Creates and manages **routines** — recurring tasks that run on Anthropic-managed cloud infrastructure on a cron schedule or triggered by GitHub events (like a new commit or PR). Claude walks you through setup conversationally: you describe what you want and when, and it handles the scheduling.

#### How to invoke

```bash
/schedule
# Claude asks: "What should I do, and when?"

/schedule Run the full test suite every morning at 8am and open an issue if anything fails
/schedule Check for outdated dependencies every Monday and open a PR with updates
```

#### Real-life scenario

> You want Claude to automatically check your repo for security vulnerabilities every night and open a GitHub issue if it finds any.

```
1. Type: /schedule
2. Claude: "What task should I run, and on what schedule?"
3. You: "Every night at midnight, scan for npm audit vulnerabilities.
         If any critical ones are found, open a GitHub issue with details."
4. Claude sets up the routine on Anthropic cloud infrastructure
5. You can list/manage routines with /schedule again at any time
```

---

### 1.9 `/mobile`

**Aliases:** `/ios`, `/android`

#### What it does
Shows a **QR code** to download the Claude mobile app. When `/remote-control` is active, scanning the QR code opens the app directly connected to your session.

#### How to invoke

```bash
/mobile
/ios
/android
```

#### Real-life scenario

> A colleague wants to try monitoring their Claude Code sessions from their phone but doesn't have the app installed.

```
1. Type: /mobile
2. QR code appears in terminal
3. Colleague scans it, downloads the Claude app
4. You then run /remote-control
5. Press Space for the session QR code
6. Colleague scans again — now directly connected to your live session
```

---

### 1.10 `/voice`

**Form:** `/voice [hold|tap|off]`  
**Requires:** Claude.ai account

#### What it does
Enables **voice dictation** for sending prompts to Claude. Instead of typing, you speak your instructions.

- `hold` — hold a key to record, release to send
- `tap` — tap to start/stop recording
- `off` — disable voice

#### How to invoke

```bash
/voice          # Toggle voice on/off
/voice hold     # Hold-to-talk mode
/voice tap      # Tap-to-talk mode
/voice off      # Disable
```

#### Real-life scenario

> You're doing a code walkthrough and want to ask Claude questions hands-free while reading through files.

```
1. Type: /voice tap
2. Tap the designated key to start recording
3. Say: "Explain what the processPayment function does and identify any edge cases"
4. Tap again to send
5. Claude responds in text as usual
```

---

### 1.11 `/team-onboarding`

#### What it does
Generates a **team onboarding guide** from your own Claude Code usage history. Claude analyzes your sessions, commands, and MCP servers from the past 30 days and writes a markdown guide a new teammate can paste as their first message to get set up quickly.

For claude.ai subscribers (Pro, Max, Team, Enterprise) it also returns a **share link** teammates can open directly in Claude Code.

#### How to invoke

```bash
/team-onboarding
```

#### Real-life scenario

> A new engineer is joining your team. You want to share how your team uses Claude Code — which MCP servers, which custom skills, which workflows.

```
1. Type: /team-onboarding
2. Claude analyzes 30 days of your usage patterns
3. Generates a guide like:
   "Welcome! Here's how we use Claude Code on this project:
    - MCP Servers: github, postgres, linear
    - Key skills: /deploy-staging, /check-coverage
    - Typical workflow: /plan → implement → /code-review → /autofix-pr"
4. On Pro/Max/Team/Enterprise: a share link is generated
5. New engineer opens the link — Claude Code starts with full context
```

---

### 1.12 `/workflows`

#### What it does
Opens the **workflow progress view** to watch, pause, resume, or save running and completed workflows (such as `/batch`, `/ultrareview`, `/deep-research`). Shows a live tree of which agents are running, which are done, and what they produced.

#### How to invoke

```bash
/workflows
```

#### Real-life scenario

> You kicked off `/batch migrate all controllers to use the new service layer` which spawned 12 parallel agents. You want to check progress.

```
1. Type: /workflows
2. See a live progress tree:
   ✓ Agent 1: UserController — done, PR opened
   ✓ Agent 2: AuthController — done, PR opened
   ⟳ Agent 3: PaymentController — running (step 3/5)
   ○ Agent 4: ReportController — queued
   ...
3. Press P to pause any running agent
4. Press S to save the workflow state and resume later
```

---

### 1.13 `/color`

**Form:** `/color [color|default]`

#### What it does
Sets the **prompt bar color** for the current session. When `/remote-control` is active, the color syncs to claude.ai/code — useful for distinguishing multiple sessions on your screen.

Available colors: `red`, `blue`, `green`, `yellow`, `purple`, `orange`, `pink`, `cyan`

#### How to invoke

```bash
/color green        # Set to green
/color default      # Reset to default
/color              # Pick a random color
```

#### Real-life scenario

> You're running two remote-control sessions simultaneously on claude.ai: one for frontend work and one for backend. You color-code them to tell them apart.

```
Session 1 (frontend): /color blue
Session 2 (backend):  /color orange

Both sessions appear in claude.ai/code with their respective colors
making it easy to click the right one without reading the name
```

---

### 1.14 `--remote` CLI Flag

**Form:** `claude --remote "<task description>"`

#### What it does
Creates a **new cloud session on claude.ai** directly from the terminal — no need to open a browser. Claude receives the task and begins working in an Anthropic-managed VM with your repository cloned. Results come back as a branch/PR.

#### How to invoke

```bash
claude --remote "Fix all TypeScript type errors in the src/api directory"
claude --remote "Add pagination to the /users endpoint"
claude --remote "Write unit tests for the payment module"
```

#### Real-life scenario

> You're at the terminal and want to delegate a self-contained task to a cloud agent while you work on something else locally.

```bash
# Kick off a cloud task, then continue your local work:
claude --remote "Upgrade all deprecated React class components to hooks in src/components"

# A web session starts on Anthropic's cloud
# You stay in your local terminal doing other work
# When done, Claude opens a PR you can review on GitHub
```

---

### 1.15 `--channels` CLI Flag

**Form:** `claude --channels plugin:<name>@<marketplace>`  
**Status:** Research preview — requires claude.ai authentication

#### What it does
Subscribes your session to **MCP server channel notifications** from claude.ai. A channel is a push-notification stream from an MCP server — for example, a Slack bot, a CI webhook, or a GitHub event feed. Claude listens passively and acts when a relevant notification arrives.

#### How to invoke

```bash
claude --channels plugin:my-notifier@my-marketplace
```

#### Real-life scenario

> You want Claude to automatically respond when a GitHub webhook fires (e.g., a new PR is opened) and run a preliminary review.

```bash
claude --channels plugin:github-webhooks@my-marketplace \
       "When a new PR is opened, run /code-review and post a summary comment"

# Claude listens passively
# When a PR is opened on GitHub, the channel fires
# Claude wakes up, reviews the PR, posts a comment
# Then goes back to listening
```

---

## 2. GitHub Commands

These commands interact with GitHub repositories, pull requests, CI pipelines, and the Claude GitHub Actions integration.

---

### 2.1 `/install-github-app`

#### What it does
Interactive wizard that sets up the **Claude GitHub Actions integration** for a repository. After setup, Claude can be triggered directly from GitHub Actions workflows (e.g., on PR open, on CI failure, on comment).

#### How to invoke

```bash
/install-github-app
```

Claude walks you through:
1. Selecting the GitHub organization/repo
2. Installing the Claude GitHub App
3. Configuring which events trigger Claude

#### Real-life scenario

> You want Claude to automatically review every PR and respond to `@claude` mentions in PR comments.

```
1. Type: /install-github-app
2. Select your repo from the picker
3. Authorize the GitHub App installation
4. Choose triggers: "PR opened", "PR comment mentioning @claude"
5. Done — now every new PR gets a Claude review, and @claude responds to comments
```

---

### 2.2 `/web-setup`

#### What it does
Connects your **GitHub account to Claude Code on the web** using your local `gh` CLI credentials. Required before you can use cloud sessions that need GitHub access (push branches, open PRs, read private repos).

`/schedule` prompts for this automatically if GitHub isn't connected yet.

#### How to invoke

```bash
/web-setup
```

#### Real-life scenario

> You want to use `/autofix-pr` or `--remote` but get an error that GitHub isn't connected.

```
1. Ensure you're logged into GitHub locally: gh auth status
2. Type: /web-setup
3. Claude transfers your local gh credentials to Anthropic's cloud infrastructure
4. Cloud sessions can now clone private repos, push branches, and open PRs on your behalf
```

---

### 2.3 `/review [PR]`

#### What it does
Reviews a **pull request locally** in your current Claude Code session. Claude reads the PR diff, checks out the branch if needed, and provides a thorough review — code correctness, logic, style, potential bugs.

For a deeper cloud-based review, use `/code-review ultra` instead.

#### How to invoke

```bash
/review               # Detects the open PR for your current branch
/review 1234          # Review a specific PR by number
/review https://github.com/owner/repo/pull/1234   # Review by URL
```

#### Real-life scenario

> A teammate opened a PR for a database migration. You want Claude to review it for correctness and potential data-loss risks before you approve.

```
1. Check out the PR branch (or stay on your current branch)
2. Type: /review 1234
3. Claude reads the migration files and says:
   - "Line 45: The DROP COLUMN is irreversible with no rollback plan"
   - "Line 78: No index added for the new foreign key — will cause slow queries"
   - "Overall: 2 blocking issues, 3 suggestions"
4. You share Claude's feedback with the PR author
```

---

### 2.4 `/code-review [--comment]`

**Form:** `/code-review [low|medium|high|ultra] [--fix] [--comment] [target]`

#### What it does
Reviews the **current git diff** (or a specific PR) for correctness bugs and code quality issues.

Key flags:
- `--comment` — posts findings as **inline GitHub PR comments** (requires `gh` CLI)
- `--fix` — applies the fixes directly to your working tree
- `ultra` — runs the deep multi-agent cloud review (same as `/ultrareview`)

#### How to invoke

```bash
/code-review                    # Review current diff, low/medium effort
/code-review high               # Higher effort review
/code-review --fix              # Review and auto-apply fixes
/code-review --comment          # Review and post findings as PR comments
/code-review ultra --comment    # Deep cloud review + post PR comments
/code-review 1234               # Review PR #1234
/code-review high --comment 1234  # High-effort review of PR #1234 with comments
```

#### Real-life scenario

> You've finished a feature and want Claude to review your changes, then automatically post findings to your PR so reviewers see them.

```bash
# You're on your feature branch with changes staged:
git add -p   # stage your changes

# Inside Claude Code:
/code-review high --comment

# Claude reviews the diff at high effort
# Findings are posted as inline comments on the GitHub PR:
#   Line 34: "Null not handled — will throw if user is unauthenticated"
#   Line 89: "This query runs N+1 times in a loop — use a single JOIN"
# Your PR now shows Claude's review for human reviewers to see
```

---

### 2.5 `/security-review`

#### What it does
Analyzes the **pending changes on the current branch** specifically for security vulnerabilities: injection risks, authentication issues, data exposure, insecure defaults, and more.

#### How to invoke

```bash
/security-review
```

#### Real-life scenario

> You added file upload support to your API. Before merging, you want a security-focused review to check for path traversal, MIME type validation, and storage security.

```
1. Make sure your changes are committed/staged
2. Type: /security-review
3. Claude reports:
   - "File extension not validated — attackers can upload .php files"
   - "Upload path uses user-controlled input — path traversal risk"
   - "No file size limit — denial of service possible"
4. Fix each issue before merging
```

---

### 2.6 `/batch`

**Form:** `/batch <instruction>`

#### What it does
Orchestrates **large-scale changes across the entire codebase in parallel**. Claude:
1. Researches the codebase and decomposes the work into 5–30 independent units
2. Shows you a plan for approval
3. Spawns one background subagent per unit in an isolated git worktree
4. Each subagent implements its unit, runs tests, and **opens a pull request**

The result: many targeted PRs, one per unit of work, all running simultaneously.

Requires a git repository.

#### How to invoke

```bash
/batch migrate all class components in src/ to React functional components
/batch add JSDoc comments to every exported function in src/api/
/batch replace all console.log calls with the structured logger
/batch update all API calls to use the new v2 SDK
```

#### Real-life scenario

> You need to rename a method used in 40 files across your codebase, and update tests in each file too.

```
1. Type: /batch rename processOrder() to fulfillOrder() across the entire codebase, update all call sites and tests
2. Claude analyzes the codebase and presents a plan:
   "I'll split this into 8 units by directory. Each unit updates ~5 files and their tests."
3. You approve the plan
4. 8 agents run in parallel, each in their own git worktree
5. 8 PRs appear on GitHub, one per directory
6. You review and merge each PR — or merge them all at once
```

---

### 2.7 `--from-pr` CLI Flag

**Form:** `claude --from-pr <PR>`

#### What it does
Resumes **Claude Code sessions linked to a specific pull request**. Sessions are linked automatically when Claude creates a PR. Supports GitHub PR numbers/URLs, GitLab MR URLs, and Bitbucket PR URLs.

#### How to invoke

```bash
claude --from-pr 1234                                        # GitHub PR number
claude --from-pr https://github.com/owner/repo/pull/1234    # GitHub PR URL
claude --from-pr https://gitlab.com/owner/repo/-/merge_requests/56  # GitLab MR
```

#### Real-life scenario

> Claude opened PR #1234 as part of a `/batch` run. CI failed and you want to resume the agent that created it to fix the failure.

```bash
# Resume the agent session that opened PR #1234:
claude --from-pr 1234

# The session resumes with the same context and branch checked out
# You can now: fix the CI failure, push updates, or give new instructions
```

---

### 2.8 `--worktree` / `-w` with PR

**Form:** `claude --worktree <PR-number-or-URL>` or `claude -w #<PR-number>`

#### What it does
Starts Claude Code in an **isolated git worktree** checked out from a specific PR branch. The worktree is created at `<repo>/.claude/worktrees/<name>`. You can work on the PR without affecting your main working tree.

#### How to invoke

```bash
# Start a worktree for PR #42:
claude -w #42
claude --worktree #42
claude --worktree https://github.com/owner/repo/pull/42

# Combine with tmux for a split-pane experience:
claude -w #42 --tmux
```

#### Real-life scenario

> A colleague's PR #89 has a bug and you want to investigate and fix it without touching your own branch.

```bash
# In your project directory:
claude -w #89

# Claude:
# 1. Fetches PR #89's branch from origin
# 2. Creates a worktree at .claude/worktrees/fix-login-bug
# 3. Checks out the PR branch there
# 4. Starts a Claude session in that worktree

# You investigate the bug, Claude makes fixes
# When done, push the changes — they go to the PR branch
```

---

### 2.9 `claude ultrareview` CLI Command

**Form:** `claude ultrareview [target] [--json] [--timeout <minutes>]`

#### What it does
Runs `/code-review ultra` **non-interactively from the shell** — useful in CI pipelines or pre-merge scripts. Prints findings to stdout, exits with code 0 on success or 1 on failure.

#### How to invoke

```bash
# Review current branch:
claude ultrareview

# Review a specific PR:
claude ultrareview 1234

# Output raw JSON (for CI parsing):
claude ultrareview 1234 --json

# Set a longer timeout (default: 30 minutes):
claude ultrareview 1234 --timeout 45
```

#### Real-life scenario

> You want ultra review to run automatically in your CI pipeline as a required check before merging.

```yaml
# .github/workflows/claude-review.yml
name: Claude Ultra Review
on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install Claude Code
        run: npm install -g @anthropic-ai/claude-code
      - name: Run Ultra Review
        run: claude ultrareview ${{ github.event.number }} --json
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

---

## 3. Cross-cutting: `/autofix-pr`

**Form:** `/autofix-pr [prompt]`  
**Requires:** `gh` CLI + access to Claude Code on the web

#### What it does
Spawns a **cloud session on claude.ai** that watches your current branch's PR and automatically pushes fixes when:
- **CI fails** — Claude reads the failure logs and fixes the code
- **Reviewers leave comments** — Claude reads the comments and addresses them

By default it fixes everything; pass a prompt to constrain what it fixes.

#### How to invoke

```bash
/autofix-pr                              # Fix all CI failures and review comments
/autofix-pr only fix lint and type errors
/autofix-pr address review comments but don't change test files
/autofix-pr fix failing unit tests only, don't touch integration tests
```

To watch a different PR than the one on your current branch, check out that branch first.

#### Real-life scenario 1: CI keeps failing

> Your PR has a flaky lint error and a failing test. You're tired of push → wait → fix → push cycles.

```
1. Make sure your PR is open on GitHub
2. Be on the PR's branch locally
3. Type: /autofix-pr only fix lint errors and the failing unit tests

4. A cloud session spawns:
   - Reads CI failure logs
   - Fixes the lint error
   - Fixes the failing test
   - Pushes a commit to your branch
   - CI runs again

5. You get notified when CI is green — you didn't do anything
```

#### Real-life scenario 2: Addressing review comments automatically

> Your PR has 12 reviewer comments, mostly about naming conventions and missing error handling.

```
1. On the PR branch, type: /autofix-pr address all reviewer comments

2. Cloud session reads every comment on the PR
3. Addresses each one with a code change
4. Pushes commits to the branch
5. Replies to each comment: "Fixed in commit abc123"

6. You just review Claude's changes and approve
```

---

## 4. Real-Life Workflows

### Workflow A: Mobile-first development

Start at your desk → monitor from your phone → finish at your desk.

```
1. Terminal:     /remote-control          ← expose session to mobile
2. Phone:        Scan QR code, open Claude app
3. Terminal:     Start a long task ("Refactor the payments module")
4. Walk away:    Monitor progress on phone, send occasional instructions
5. Return:       Continue in terminal — session never dropped
```

---

### Workflow B: Delegate to cloud, work locally

Parallelize your work by running tasks in Anthropic's cloud while you work locally.

```bash
# Kick off cloud task:
claude --remote "Write comprehensive unit tests for src/services/"

# Continue local work in your own terminal:
claude   # normal session, different task

# When cloud task finishes, a PR appears on GitHub
# Review it without interrupting your local session
```

---

### Workflow C: Full automated PR lifecycle

Let Claude write, review, and fix a PR with minimal manual effort.

```
1. /batch add input validation to all API endpoints
   → 6 PRs opened in parallel

2. /autofix-pr
   → Cloud session watches all PRs, fixes CI failures as they come in

3. /code-review ultra --comment on each PR
   → Multi-agent review posts inline comments

4. You review only the summary and merge
```

---

### Workflow D: Remote EC2 development

Use a persistent cloud server instead of ephemeral VMs.

```bash
# On EC2 (SSH'd in):
claude remote-control --name "feature-auth" \
  --remote-control-session-name-prefix ec2-prod

# In your browser:
# → Open claude.ai/code
# → Find "ec2-prod-feature-auth" session
# → Full terminal control from browser, session persists 24/7

# From your phone later:
# → Same session, same context
# → EC2 handles all compute, your phone is just a window
```

---

### Workflow E: Nightly automated maintenance

Set up a routine that keeps your repo healthy without manual effort.

```
/schedule

Claude: "What should I do, and when?"

You: "Every weekday night at 11pm:
  1. Run npm audit and fix any vulnerabilities with a PR
  2. Check for packages more than 2 major versions behind and open an issue
  3. Run the full test suite; if any tests fail, open an issue with the log"

Claude sets up the routine → runs every weekday night → you wake up to PRs/issues
```

---

## Quick Reference Card

### Web Commands
| Command | Alias | What it does |
|---|---|---|
| `/teleport` | `/tp` | Pull cloud session into terminal |
| `/remote-control` | `/rc` | Expose local session to claude.ai/mobile |
| `/remote-env` | — | Set cloud agent default environment |
| `/ultraplan <task>` | — | Plan in browser, execute remotely |
| `/ultrareview [PR]` | `/code-review ultra` | Deep multi-agent cloud review |
| `/desktop` | `/app` | Continue in Desktop app |
| `/schedule` | `/routines` | Create recurring cloud routines |
| `/mobile` | `/ios`, `/android` | Show QR for mobile app |
| `/voice [hold\|tap\|off]` | — | Voice dictation |
| `/team-onboarding` | — | Generate onboarding guide + share link |
| `/workflows` | — | Watch running cloud workflows |
| `/color <color>` | — | Color-code session (syncs to claude.ai) |

### Web CLI Flags
| Flag | What it does |
|---|---|
| `claude --remote "<task>"` | Create new cloud session with task |
| `claude --teleport` | Resume cloud session in terminal |
| `claude --remote-control` | Start session with Remote Control on |
| `claude --channels plugin:x@y` | Subscribe to MCP channel notifications |

### GitHub Commands
| Command | What it does |
|---|---|
| `/install-github-app` | Set up Claude GitHub Actions integration |
| `/web-setup` | Connect GitHub account to Claude cloud |
| `/review [PR]` | Review PR locally |
| `/code-review --comment` | Review + post inline GitHub PR comments |
| `/code-review ultra --comment` | Deep cloud review + inline PR comments |
| `/security-review` | Security-focused review of current diff |
| `/autofix-pr [prompt]` | Cloud session that watches PR + auto-fixes CI/review |
| `/batch <instruction>` | Codebase-wide change → parallel PRs |

### GitHub CLI Flags
| Flag | What it does |
|---|---|
| `claude --from-pr <PR>` | Resume session linked to a specific PR |
| `claude -w #<PR>` | Start Claude in a worktree checked out from PR branch |
| `claude ultrareview <PR>` | Run cloud review non-interactively (CI-friendly) |
