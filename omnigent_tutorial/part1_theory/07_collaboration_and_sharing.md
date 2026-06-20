# Chapter 07: Collaboration & Multi-Device Access

## The Collaboration Pillar

Omnigent's third pillar (after composition and control) is collaboration. The core idea: **agent sessions are shareable URLs.** Like Google Docs for AI agents.

## Session Sharing

### Share a Live Session

```bash
omni                    # start a session
# → http://localhost:6767/session/abc123
```

Share that URL with a teammate. They see:

- The full message history
- Sub-agents and their status
- Terminal output (if any)
- File state (the working directory)

They can:
- **View** — watch the agent work in real time
- **Comment** — leave inline comments on generated files
- **Co-drive** — send messages to the agent, steering it alongside you
- **Fork** — clone the session into their own for independent exploration

### Permission Model

| Role | View | Comment | Co-drive | Fork | Manage |
|---|---|---|---|---|---|
| **Owner** | ✓ | ✓ | ✓ | ✓ | ✓ |
| **Collaborator** | ✓ | ✓ | ✓ | ✓ | — |
| **Viewer** | ✓ | ✓ | — | ✓ | — |

### Sharing Flow

```
1. You start a session:
   omni run my_agent.yaml

2. Invite a collaborator:
   you: "share this session with alice@example.com"
   # or via UI: Share → Add collaborator

3. Alice gets the URL, opens it:
   → Sees your agent working on a task
   → She can comment: "consider using async here"
   → She can co-drive: sends a message to the agent
   → Agent sees both your messages and Alice's

4. When done, Alice can fork:
   → Her fork is a new session with full history
   → She can continue independently
```

## Cross-Device Continuity

One of Omnigent's distinctive claims: **sessions follow you across devices.**

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│ Terminal │     │  Web UI  │     │  Mobile  │
│ (CLI)    │     │ (:6767)  │     │ (phone)  │
└────┬─────┘     └────┬─────┘     └────┬─────┘
     │                │                │
     └────────────────┼────────────────┘
                      │
              ┌───────▼───────┐
              │  OMNIGENT     │
              │  SERVER       │
              │  (SQLite DB)  │
              └───────────────┘
```

**How it works:** All state is in the server's SQLite database. The terminal, web UI, and mobile app are all clients talking to the same server. No syncing, no "send to device" — there's one source of truth.

### Real-World Flow

```
09:00 — At your desk
  Terminal: omni claude
  "Analyze the performance regression in PR #342"

09:15 — On the train
  Phone: open omni.yourapp.com
  Same session is there. Read the agent's findings.
  Send: "Also check if it's related to the cache change last week"

09:45 — At the coffee shop
  Laptop web UI: http://localhost:6767
  Agent has finished analysis. Review the report.
  Comment on a specific finding, ask for clarification.
```

## Multi-Agent Collaboration

The real power of Omnigent's collaboration: agents that work together.

### Polly: Multi-Agent Coding Orchestrator

Polly (ships with Omnigent) is a concrete example of agent-agent collaboration:

```
POLY (orchestrator, claude-sdk)
  │
  ├── Sub-agent: CLAUDE_CODE (implements feature A)
  │     └── Opens PR #1 in its own worktree
  │
  ├── Sub-agent: CODEX (implements feature B)
  │     └── Opens PR #2 in its own worktree
  │
  └── After implementation:
       ├── Sub-agent: PI (reviews PR #1)  ← different vendor!
       └── Sub-agent: CODEX (reviews PR #2) ← different vendor!
```

**Key collaboration patterns in Polly:**

1. **Parallel work** — Sub-agents run concurrently in isolated worktrees
2. **Cross-vendor review** — Every PR reviewed by a different vendor's agent
3. **Inbox-driven wake** — Orchestrator sleeps until sub-agents complete; no polling
4. **Human-in-the-loop** — Human merges PRs; agent never merges

### Debby: Two-Headed Brainstorming

```
DEBBY (orchestrator, claude-sdk)
  │
  ├── Sub-agent: CLAUDE (responds to question)
  └── Sub-agent: GPT (responds to same question)

  Debby presents both answers side-by-side.
  With /debate: partners critique each other for N rounds.
```

## Shared Server (Team Deployment)

For teams, deploy a shared Omnigent server:

```bash
# Admin sets up
omni server start --host 0.0.0.0 --port 6767

# Team members connect
omni --server http://team-server:6767
```

### Server Configuration

```yaml
# server_config.yaml
auth:
  type: sso
  provider: google            # or: github, okta, saml
  allowed_domains:
    - mycompany.com

policies:
  team_budget:
    type: function
    handler: omnigent.policies.builtins.cost.cost_budget
    factory_params:
      max_cost_usd: 100.00

managed_hosts:
  - type: modal
    region: us-east
    max_concurrent: 10
```

### Database

The server uses a configurable database:

```yaml
# server_config.yaml
database:
  type: postgres              # or: sqlite (default)
  url: postgres://user:pass@host:5432/omnigent
```

Postgres enables multi-server deployments (multiple Omnigent servers share one DB). SQLite is fine for single-server teams.

## Mobile Access

Omnigent's web UI is responsive — it works on mobile browsers. The native mobile experience is being built.

Current mobile flow:
1. Deploy Omnigent server (your machine or cloud)
2. Expose it (tailscale, ngrok, or direct public IP)
3. Open the URL on your phone
4. Chat with your agents from anywhere

## REST API

For programmatic access:

```
GET    /api/sessions              List sessions
POST   /api/sessions              Create session
GET    /api/sessions/:id          Get session
POST   /api/sessions/:id/messages Send message
GET    /api/sessions/:id/messages Get messages
POST   /api/sessions/:id/fork     Fork session
DELETE /api/sessions/:id          Delete session

GET    /api/agents                List available agents
POST   /api/agents/run            Run an agent

GET    /api/policies              List active policies
POST   /api/policies              Add session policy
```

## Collaboration vs. Other Tools

| Feature | Omnigent | Claude Code (native) | Codex (native) | Cursor |
|---|---|---|---|---|
| Share live session | ✓ (URL) | — | — | — |
| Co-drive with teammates | ✓ | — | — | — |
| Inline comments | ✓ | — | — | — |
| Session fork | ✓ | — | — | — |
| Cross-device continuity | ✓ | — | — | — |
| Multi-agent in one session | ✓ | — | — | — |
| REST API | ✓ | — | — | — |

## Summary

Omnigent's collaboration story:

- **Shareable URLs** — Send a session link like a Google Doc
- **Roles** — Owner, collaborator, viewer
- **Co-driving** — Multiple humans steering one agent
- **Comments** — Inline feedback on generated files
- **Forks** — Branch a session for independent exploration
- **Cross-device** — Same session on terminal, web, mobile
- **Multi-agent** — Agents collaborating under an orchestrator
- **Team server** — Shared deployment with SSO and centralized policies

---

**Previous:** [Chapter 06 — Sandbox & Security Model](./06_sandbox_and_security.md)
**Next:** [Chapter 08 — Stanford Meta-Harness: The Research](./08_meta_harness_research.md)
