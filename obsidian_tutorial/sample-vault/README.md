# Sample Obsidian Vault

This is a sample vault demonstrating Obsidian concepts from the `OBSIDIAN_TUTORIAL.md` tutorial.

## How to Use

1. Open Obsidian
2. Click "Open folder as vault"
3. Navigate to this folder (`obsidian_tutorial/sample-vault/`)
4. Explore the files!

## What's Inside

### Projects (with frontmatter + Dataview)
- `projects/project-alpha.md` — Active project with full Properties, inline fields, wikilinks
- `projects/project-beta.md` — Completed project for comparison
- `projects/project-dashboard.md` — Dataview-powered dashboard (requires Dataview plugin)

### Daily Notes & Templates
- `daily-notes/2026-06-18.md` — Example daily note with tasks, meetings, reflection
- `templates/daily-note.md` — Templater template (requires Templater plugin)
- `templates/meeting-note.md` — Meeting template with prompts

### Books (knowledge tracking)
- `books/atomic-habits.md` — Book note with rating, status, key ideas, action items
- `books/deep-work.md` — Completed book with four philosophies

### Meetings (with embeds)
- `meetings/2026-06-18-standup.md` — Demonstrates `![[embeds]]` to project sections

### Concepts (linked thinking)
- `concepts/linked-thinking.md` — Concept note with extensive wikilinks
- `concepts/zettelkasten.md` — Methodology note linking to Atomic Habits

### Canvas
- `project-canvas.canvas` — Visual Q3 planning with notes, connections, groups

## Demonstrates

| Feature | Where |
|---|---|
| Wikilinks (`[[link]]`) | Every file |
| Properties / Frontmatter | `project-alpha.md`, `atomic-habits.md` |
| Embeds (`![[embed]]`) | `2026-06-18-standup.md` |
| Callouts (`> [!type]`) | `project-alpha.md`, `2026-06-18-standup.md` |
| Tags (`#tag`) | Frontmatter in every file |
| Dataview Queries | `project-dashboard.md`, `daily-note.md` (template) |
| Block References (`^id`) | `project-alpha.md` (key-metric) |
| Canvas | `project-canvas.canvas` |
| Inline Fields (`Key:: Value`) | `atomic-habits.md`, `project-alpha.md` |
| Templates (Templater) | `templates/daily-note.md`, `templates/meeting-note.md` |

## Recommended Plugins

To fully experience this vault, install:
- **Dataview** — powers the dashboard and meeting queries
- **Templater** — powers the dynamic templates
- **Calendar** — visual navigation for daily notes
