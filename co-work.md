# Claude Cowork: The Complete Tutorial

> **What you will learn:** Every feature of Claude Cowork — New Task, Projects, Scheduled Tasks, Live Artifacts, Dispatch, and Customize — explained through real-world examples with exact prompts you can adapt immediately.

---

## Table of Contents

1. [What Is Claude Cowork?](#1-what-is-claude-cowork)
2. [Setup and First Launch](#2-setup-and-first-launch)
3. [Understanding the Interface](#3-understanding-the-interface)
4. [New Task — Getting Work Done](#4-new-task--getting-work-done)
5. [Projects — Organizing Ongoing Work](#5-projects--organizing-ongoing-work)
6. [Scheduled Tasks — Automating Recurring Work](#6-scheduled-tasks--automating-recurring-work)
7. [Live Artifacts — Always-Current Dashboards](#7-live-artifacts--always-current-dashboards)
8. [Dispatch — Working From Anywhere](#8-dispatch--working-from-anywhere)
9. [Customize — Making Cowork Yours](#9-customize--making-cowork-yours)
10. [MCP Connectors — Connecting to Your Apps](#10-mcp-connectors--connecting-to-your-apps)
11. [Writing Good Prompts for Cowork](#11-writing-good-prompts-for-cowork)
12. [Advanced Patterns — Combining Features](#12-advanced-patterns--combining-features)
13. [Personas: Cowork for Different Roles](#13-personas-cowork-for-different-roles)
14. [Troubleshooting](#14-troubleshooting)
15. [Decision Guide](#15-decision-guide)
16. [Quick Reference](#16-quick-reference)

---

## 1. What Is Claude Cowork?

Claude Cowork is the agentic workspace inside Claude Desktop. Unlike Claude Chat — where you ask a question and Claude replies in a single turn — Cowork lets you describe an *outcome*, and Claude plans, executes, and delivers that outcome autonomously. It can read and write files on your machine, run code in an isolated virtual machine, call connected apps through MCP, coordinate parallel workstreams, and run tasks on a schedule — all without you staying in the conversation.

### How It Differs From Claude Chat and Claude Code

| Dimension | Claude Chat | Claude Cowork | Claude Code |
|-----------|-------------|---------------|-------------|
| Where it runs | Browser or Desktop | Desktop only | Terminal (CLI) |
| Task length | Single turn | Minutes to hours | Minutes to hours |
| File access | Upload/download | Direct local read/write | Direct local read/write |
| Scheduling | No | Yes | No (use cron externally) |
| Best for | Q&A, drafting | Knowledge work, automation | Software engineering |
| Runs while you're away | No | Yes (Dispatch + Scheduled) | No |

### When Should You Use Cowork?

Use Cowork when:
- The task takes more than one step and involves your local files or apps
- You want it to run while you're in a meeting, asleep, or on a plane
- You do the same thing every week and want it automated
- You want a dashboard that's always current without manual refresh

Stick with Chat when you just need a quick answer, a draft, or an explanation.

---

## 2. Setup and First Launch

### Requirements

- **Claude Desktop** for macOS or Windows (latest version — update if prompted)
- **Paid plan:** Pro, Max, Team, or Enterprise
- **Machine must stay awake** while tasks, Dispatch, and Scheduled tasks run

### Installation Steps

1. Download Claude Desktop from claude.ai/download
2. Sign in with your Anthropic account
3. Click the **Cowork** tab at the top of the sidebar (between Chat and Code)
4. On first launch, Claude Desktop may ask permission to access your file system — grant it
5. Optionally, authorize your first MCP connector (Gmail, Slack, Google Calendar, etc.) under **Customize → Connectors**

### Your First Task (5-Minute Test)

Before diving into features, run this to confirm everything works:

```
Create a file called ~/Desktop/cowork_test.txt.
Write today's date, the current time, and the sentence "Cowork is running." into it.
```

If a file appears on your desktop with that content, your setup is complete.

---

## 3. Understanding the Interface

When you click the **Cowork** tab in Claude Desktop, you see a sidebar with these items:

```
+ New task
  Projects
  Scheduled
  Live artifacts
  Dispatch       [Beta]
  Customize

Recents
  ○ Model distillation in Claude
  ○ Semantic search
```

| Item | What It Does |
|------|-------------|
| **+ New task** | Start a one-off task right now |
| **Projects** | Workspaces with memory, instructions, and context |
| **Scheduled** | View and manage all recurring tasks |
| **Live artifacts** | Your saved, always-current dashboards |
| **Dispatch** | Send tasks from your phone to your desktop |
| **Customize** | Global settings, plugins, connectors, preferences |
| **Recents** | Your last few tasks for quick re-access |

---

## 4. New Task — Getting Work Done

### What It Is

New Task is the entry point for all immediate, one-off work. You describe what you want done — Claude plans it, executes it, and delivers the output to your file system.

### How Claude Executes a Task (Under the Hood)

1. **Reads your prompt** and identifies what files, apps, or data it needs
2. **Builds a plan** — shown to you before execution begins
3. **Breaks work into subtasks** — some run in parallel, some sequentially
4. **Runs code** in an isolated virtual machine on your machine
5. **Reads and writes** your local file system directly
6. **Shows progress** — you can steer, correct, or stop mid-task
7. **Delivers outputs** to specified paths and notifies you when done

### Writing a Good New Task Prompt

A strong task prompt includes:
- **What** to do (the goal)
- **Where** the input files are (exact paths)
- **Where** to save output (exact paths and format)
- **Any constraints** (tone, length, structure, do-not-touch rules)

**Weak prompt:**
```
Summarize my documents
```

**Strong prompt:**
```
Read every PDF in ~/Documents/Client_Reports/Q2/.
For each document: extract the title, key recommendations (max 5 bullets), and any stated risks.
Compile into a single summary table saved as ~/Documents/Q2_summary.xlsx.
Sort rows by date of report, newest first.
```

---

### Example 1 — Morning Board Brief

**Situation:** You have a board meeting at 9 AM. It is 7:30. You need a one-page brief covering open action items, revenue numbers, and urgent emails.

**Prompt:**
```
Read ~/Desktop/board_meeting_notes_Q1.docx and extract all open action items.
Check my Gmail (via MCP) for messages flagged as urgent in the last 24 hours.
Pull Q2 revenue total from ~/Documents/finance/q2_actuals.xlsx, cell B42.
Combine into a one-page briefing document:
- Section 1: Open action items (owner, due date)
- Section 2: Urgent emails (sender, subject, one-line summary)
- Section 3: Q2 revenue vs Q1 target
Save as ~/Desktop/board_brief_today.docx.
```

**Time:** ~4 minutes. **Output:** A formatted Word doc on your desktop.

---

### Example 2 — Customer Support Triage Report

**Situation:** Your inbox has 40 unresolved complaint threads exported to CSV. You need a grouped analysis before a product sync at 2 PM.

**Prompt:**
```
Read ~/Downloads/support_tickets_export.csv.
Group tickets by issue category: billing, login issues, performance, feature requests, other.
For each category:
- Count of tickets
- One-paragraph description of the pattern
- Recommended fix or owner team
Save as ~/Documents/support_analysis_June2026.pdf with a summary table at the top.
```

---

### Example 3 — Research Paper Backlog

**Situation:** 15 PDFs have been sitting unread in a folder for three weeks.

**Prompt:**
```
Read every PDF in ~/Papers/unread/.
For each paper write:
- Title and authors
- 3-sentence plain-language summary
- Key finding
- Relevance score (1–10) to "machine learning in medical imaging"
- One question it leaves unanswered

Compile into ~/Papers/reading_digest.md, sorted by relevance score descending.
Move each processed PDF to ~/Papers/read/ when done.
```

---

### Example 4 — Turning a Spreadsheet Into a Slide Deck

**Situation:** You have a Q2 sales data spreadsheet and need a 6-slide executive summary for tomorrow.

**Prompt:**
```
Read ~/Sales/Q2_actuals.xlsx.
Build a 6-slide PowerPoint presentation:
Slide 1: Title — "Q2 Sales Performance — Executive Summary"
Slide 2: Total revenue vs target (use a bar chart)
Slide 3: Top 5 accounts by deal size (table)
Slide 4: Regional breakdown (pie chart)
Slide 5: 3 wins and 3 risks (two-column layout)
Slide 6: Forecast for Q3 based on pipeline column in the spreadsheet
Save as ~/Presentations/Q2_exec_summary.pptx.
Use a clean, professional theme. Font: Calibri. Colors: dark blue and white.
```

---

### Example 5 — Legal Contract Review

**Situation:** You received a vendor contract. You want a plain-English risk summary before sending it to a lawyer.

**Prompt:**
```
Read ~/Documents/Contracts/VendorAgreement_Draft.pdf.
Identify and summarize:
1. Liability clauses — what are we on the hook for?
2. Termination terms — how and when can either party exit?
3. IP ownership — who owns work product?
4. Any unusual or one-sided clauses that should be flagged
5. Payment terms and penalties for late payment

Write a 1-page plain-English risk summary. 
Append a table: "Clause | Risk Level (Low/Medium/High) | Recommended Action"
Save as ~/Documents/Contracts/VendorAgreement_RiskSummary.docx.
Note at the top: "DRAFT — For internal review only. Not legal advice."
```

---

### Example 6 — Reconciling Expense Reports

**Situation:** You have 30 expense receipt images in a folder and an Excel expense template to fill.

**Prompt:**
```
Read all image files in ~/Expenses/June2026_receipts/.
For each receipt, extract: date, vendor, amount, currency, category (meals/travel/software/other).
Fill in ~/Expenses/june2026_template.xlsx, one row per receipt.
Sum totals by category.
Flag any receipt over $200 for manager approval in column F.
Save the completed file as ~/Expenses/june2026_completed.xlsx.
```

---

### Steering a Task Mid-Run

You can type in the task chat at any point while Claude is working:
- *"Stop — don't send the email yet, just save the draft"*
- *"Actually use the Q3 data instead of Q2"*
- *"Skip the PDF export, just save as Word"*

Claude reads mid-task messages and adjusts without restarting.

---

## 5. Projects — Organizing Ongoing Work

### What It Is

Projects are dedicated workspaces that group related tasks under a shared folder, memory, and instructions. Every task you run inside a project:
- Has access to the project's context files and linked folders
- Follows the project's custom instructions automatically
- Builds on memory from all previous tasks in that project
- Scopes its outputs to the project folder by default

### Three Ways to Create a Project

**Option A — Start from scratch:**
1. Cowork → Projects → + → Start from scratch
2. Name the project, choose a local folder to create
3. Add instructions (see examples below)
4. Attach any context files or folders

**Option B — Use an existing folder:**
1. Cowork → Projects → + → Use existing folder
2. Browse to a folder you already have (e.g., `~/Clients/AcmeCorp/`)
3. Add instructions scoped to that work
4. Claude will read anything in that folder as context

**Option C — Import from Claude Project:**
1. Cowork → Projects → + → Import from Claude Project
2. Select an existing web-based Claude Project
3. Files and instructions transfer over (one at a time, not bulk)

### What Lives in a Project

| Component | What It Does |
|-----------|-------------|
| **Instructions** | Tone, format rules, domain context applied to every task |
| **Context** | Local folders, URLs, or imported files Claude references |
| **Scheduled tasks** | Recurring automations scoped to this project |
| **Memory** | Claude remembers every task and applies learning forward |

> Memory is project-scoped. What Claude learns in Project A does not carry into Project B.

---

### Example 7 — Client Consulting Workspace

**Situation:** You're a consultant on a 3-month retail engagement. Everything — research, reports, decks, emails — needs to be consistent and organized.

**Setup:**
1. Cowork → Projects → + → Use existing folder → `~/Clients/RetailCo/`
2. Instructions:
```
Client: RetailCo (retail chain, 200 stores in UK).
Tone: professional, concise, no jargon.
Every report must have an executive summary on page 1 (max 200 words).
Brand colors: primary #E63946 (red), secondary #457B9D (blue).
Never include financial figures outside the /reports subfolder.
Date format: DD MMM YYYY.
Deliverable naming: RetailCo_{type}_{YYYYMMDD}
```
3. Context: attach `brand_guidelines.pdf`, `contract_scope.docx`, `stakeholder_list.xlsx`

**Tasks you then run (no need to re-explain context each time):**
- *"Draft the week 4 progress report covering milestones achieved and risks"*
- *"Turn the interview notes in /research/interviews/ into a theme analysis"*
- *"Build a 10-slide deck summarizing the operational findings"*

Because memory is on, by week 6 Claude knows your stakeholders by name, knows which recommendations were already made, and knows the client's sensitivities — without you repeating any of it.

---

### Example 8 — Job Search Workspace

**Situation:** You're applying for Senior Product Manager roles in fintech. You want tailored CVs, cover letters, and interview prep — all consistent with your personal positioning.

**Setup:**
- Project folder: `~/JobSearch/`
- Instructions:
```
Target role: Senior Product Manager in fintech (payments preferred).
My name: [Your Name]. Years experience: 8.
CV is in base_cv.docx. Always tailor to the company's stated values.
Cover letters: 300 words max, first paragraph must reference a specific company product.
Do not use the phrase "I am passionate about".
Interview prep: use the STAR method. Ground answers in my actual experience from the CV.
```
- Context: attach `base_cv.docx`, a folder `~/JobSearch/jds/` with saved job descriptions

**Tasks:**
- *"Tailor my CV for the Stripe Head of Payments PM role (JD in ~/JobSearch/jds/stripe_pm.pdf)"*
- *"Write a cover letter for the Revolut Senior PM role"*
- *"Create 10 interview questions for a fintech PM role at Monzo with STAR answers based on my CV"*
- *"Compare all 5 JDs in ~/JobSearch/jds/ — which role best matches my background? Score each 1–10 with reasoning."*

---

### Example 9 — Newsletter Content Studio

**Situation:** You publish a weekly B2B technology newsletter. Writing, research, social media posts, and scheduling all happen in one project.

**Instructions:**
```
Newsletter: The Signal. Audience: senior tech leaders (CTOs, VPs Eng).
Tone: sharp, opinionated, no filler. No bullet points in prose sections.
Article length: 800 words. LinkedIn post: 100 words. Twitter/X thread: 5 tweets.
Always include one contrarian take per issue.
Sources: prefer primary sources over aggregators. Cite inline.
Output folder: ~/Newsletter/issues/
Naming: signal_issue_{number}_{YYYYMMDD}
```

**Weekly workflow (one task per step):**
1. *"Research this week's topic: AI in procurement. Pull from my saved articles in ~/Newsletter/research/week25/ and web search for latest developments."*
2. *"Draft the article based on the research notes"*
3. *"Write the LinkedIn post, Twitter thread, and subject line variants for A/B testing"*
4. *"Create the send-ready HTML email version formatted for ConvertKit"*

---

### Example 10 — Personal Finance Tracker Project

**Situation:** You want a single workspace to track spending, model scenarios, and prepare for tax season.

**Instructions:**
```
All financial data lives in ~/Finances/.
Never share data outside this project folder.
Currency: GBP. Tax year: April–March.
When categorizing transactions: use HMRC expense categories for self-assessment.
Expense categories: office, travel, equipment, professional services, marketing, other.
Always add a column for "business vs personal" flag.
```

**Tasks throughout the year:**
- *"Process ~/Finances/bank_statement_may.csv — categorize each transaction"*
- *"What did I spend on travel Jan–May vs same period last year?"*
- *"Prepare a draft self-assessment summary for the 2025–26 tax year"*

---

### Project Best Practices

- **One project per engagement or domain.** Mixing unrelated work blurs the memory.
- **Write instructions before you run any tasks.** Instructions set the context from the first task.
- **Be specific about what NOT to do.** Prohibitions ("never send emails without my approval") are as useful as positive instructions.
- **Link your reference folder as context.** Instead of uploading files one by one, point the project at a folder — Claude can read everything in it.
- **Review memory occasionally.** If Claude starts making wrong assumptions, open the project and check what it has learned.

---

## 6. Scheduled Tasks — Automating Recurring Work

### What It Is

Scheduled Tasks run automatically on a cadence you define. You set them up once; they run without you. Claude Desktop must be open and the machine must be awake at the scheduled time.

### How to Set Up a Scheduled Task

In any task, type `/schedule` followed by the timing:

```
/schedule every Monday at 08:00
[your task prompt here]
```

Or use natural language:
```
/schedule every weekday at 07:30
/schedule every month on the 1st at 09:00
/schedule every Friday at 17:00
/schedule every 3 months on the 15th at 10:00
```

You can view, pause, or delete all scheduled tasks under **Cowork → Scheduled**.

### When to Use Scheduled Tasks

Use Scheduled Tasks when:
- You do the same thing on a predictable cadence
- The work requires no judgment call about whether to run
- The inputs refresh automatically (a CSV that updates overnight, email, a calendar)

Do NOT use Scheduled Tasks for work that requires your input or approval before running.

---

### Example 11 — Weekly Manager Status Report

**Situation:** Every Monday at 8 AM your manager expects a written status update.

**Setup:**
```
/schedule every Monday at 08:00

Read all files modified in the last 7 days in ~/Work/ProjectAlpha/.
Check my Google Calendar (via MCP) for meetings I attended last week and any noted outcomes.
Draft a status report with three sections:
1. Completed this week (bullet list, max 5 items)
2. Blockers (if none, write "None")
3. Plan for this week (bullet list, max 5 items)
Tone: concise, factual, no padding.
Save as ~/Work/reports/status_{YYYYMMDD}.docx.
Email it to manager@company.com with subject: "Weekly Status — {date}".
```

---

### Example 12 — Daily Sales Metrics Digest

**Situation:** Your sales team needs yesterday's key numbers in Slack every morning before 8 AM.

**Setup:**
```
/schedule every weekday at 07:30

Read ~/CRM_exports/daily_leads.csv (updated overnight by CRM export sync).
Calculate:
- New leads yesterday vs 7-day average
- Pipeline value added yesterday
- Deals closed this week (running total)
- Conversion rate this week vs last week

Post to Slack channel #sales-morning with this exact format:
📊 Sales Morning Update — {date}
New leads: X (7-day avg: Y)
Pipeline added: £X
Deals closed this week: X
Conversion: X% (last week: Y%)
```

---

### Example 13 — Monthly Invoice Chase

**Situation:** You're a freelancer. Every month on the 25th, check outstanding invoices and prepare chaser drafts.

**Setup:**
```
/schedule every month on the 25th at 09:00

Read ~/Finances/invoices/ for all invoice files.
Parse each for: client name, amount, due date, paid status.
Filter for any invoice unpaid and due within 35 days of today.
For each overdue invoice, write a polite payment reminder email:
- Friendly opener
- Reference invoice number and amount
- Due date
- Payment details from ~/Finances/payment_details.txt
- Offer to answer questions

Save each draft as ~/Finances/chasers/{client}_{date}.txt.
Also create a summary: ~/Finances/outstanding_summary_{date}.txt listing all unpaid invoices with days overdue.
```

---

### Example 14 — Weekly Competitor Intelligence Digest

**Situation:** As a product manager, you want a digest of competitor activity every Friday afternoon.

**Setup:**
```
/schedule every Friday at 16:00

Search the web for news about [CompanyA], [CompanyB], [CompanyC] from the last 7 days.
Also check their product blogs and release notes pages.
For each competitor, summarize:
- Any product launches or feature updates
- Pricing changes
- Press mentions or funding news
- Any negative news (outages, complaints, regulatory issues)

Save as ~/Research/competitor_digest_{date}.md.
Send a Slack message to #product-team with a 3-bullet summary per competitor.
```

---

### Example 15 — Daily Personal Morning Brief

**Situation:** You want a personal briefing waiting for you every morning when you wake up.

**Setup:**
```
/schedule every day at 06:30

Check my Gmail (via MCP) for unread emails from the last 12 hours.
Check my Google Calendar for today's meetings (time, title, attendees).
Check the weather for [your city] via web.
Check any Slack DMs marked urgent.

Create ~/Desktop/morning_brief_{date}.txt with:
- Today's weather (2 lines)
- Today's meetings (time, title)
- Email summary: count by priority, top 3 subjects to read first
- Any Slack urgent messages
- One sentence: "Today's focus should be: [infer from calendar and emails]"
```

---

### Example 16 — Quarterly Promotion Dossier Update (Academic)

**Situation:** You're building a promotion dossier over time. Every quarter, update it automatically.

**Setup:**
```
/schedule every 3 months on the 1st at 10:00

Check ~/Research/publications/ for any PDFs added since the last dossier update.
Check ~/Talks/ for any new presentations added.
Check ~/Grants/ for any new awards or rejections.
Update ~/CV/cv_master.docx:
- Add new publications to Publications section (APA format)
- Add new talks to Invited Talks section
- Update grant funding table

Regenerate ~/Bio/short_bio_150w.txt to reflect current stats.
Save a changelog entry in ~/CV/update_log.txt: date, what changed.
```

---

### Managing Scheduled Tasks

- View all scheduled tasks: **Cowork → Scheduled**
- Pause a task: click the task → toggle pause
- Delete a task: click the task → Delete
- Edit timing: delete and recreate (or click Edit if available)
- Check run history: each task shows its last run time and status

### Troubleshooting Scheduled Tasks

| Problem | Cause | Fix |
|---------|-------|-----|
| Task didn't run | Machine was asleep or app was closed | Check power settings; set machine to never sleep |
| Task ran but failed | Connector expired (password changed) | Re-authorize the connector in Customize |
| Task ran but output is wrong | Input data format changed | Update the task prompt to match new format |

---

## 7. Live Artifacts — Always-Current Dashboards

### What It Is

A Live Artifact is a persistent, interactive HTML dashboard that Claude builds for you. It:
- Connects to your apps and local files through MCP connectors
- Refreshes with current data every time you open it
- Lives in its own dedicated **Live artifacts** tab — independent of any conversation
- Is versioned (you can restore earlier versions)
- Can be updated or iterated over time

Unlike a one-time chat artifact (which is static and lives in a conversation), a Live Artifact is a permanent fixture of your workspace.

**Available on:** Pro, Max, Team, Enterprise — Claude Desktop only (macOS and Windows).

### How to Create a Live Artifact

**Method 1 — From a Cowork task:**
```
Build a live artifact: [describe what you want].
Pull from: [list your connectors and local paths].
Layout: [describe panels, charts, or sections].
```

**Method 2 — From the Live Artifacts tab:**
1. Cowork → Live artifacts
2. Click **New artifact** (top right)
3. Select **Chat with Claude**
4. Describe what you want built

### What Makes a Good Live Artifact

Good candidates:
- Information you check at unpredictable times throughout the day
- Data that changes frequently (not on a fixed schedule)
- Multiple data sources you currently check separately
- A view you'd keep open in a browser tab if it existed

Poor candidates:
- One-time reports (use New Task instead)
- Data that only changes on a schedule (use Scheduled Task to generate a report)
- Anything requiring your judgment before displaying

---

### Example 17 — Developer Pre-Standup Command Center

**Situation:** Every morning before standup you check Slack, GitHub, Linear, and Google Calendar separately. This consolidates them.

**Prompt:**
```
Build a live artifact: Developer Morning Dashboard.

Pull from:
- Slack: mentions of @me and DMs from the last 24 hours
- GitHub: open PRs assigned to me + PRs awaiting my review
- Linear: my tickets in "In Progress" or "In Review" status
- Google Calendar: today's meetings (time, title, video link if present)

Layout:
- Top row: 4 stat cards (unread Slack mentions, PRs to review, in-progress tickets, meetings today)
- Left panel: Slack threads (sender, preview, time)
- Middle panel: GitHub PRs (title, author, staleness)
- Right panel: Linear tickets (title, status, due date)
- Bottom: today's calendar timeline

Refresh all data when I open the artifact.
Show red badge on any item more than 48 hours old with no update.
```

---

### Example 18 — Freelance Business Dashboard

**Situation:** You have 5 active clients. You want a single view of deliverables, time, and money.

**Prompt:**
```
Build a live artifact: Freelance Business Dashboard.

Pull from:
- ~/Freelance/projects/ — one folder per client with project brief and deliverable list
- ~/Freelance/time_logs.csv — columns: date, client, task, hours
- ~/Finances/invoices/ — filter for unpaid invoices

Sections:
1. Client Cards (one per client): status, next deadline, hours this week, outstanding invoice amount
2. This Month: total hours billed, total revenue invoiced, total outstanding
3. Upcoming Deadlines: sorted by date, next 30 days
4. Overdue Invoices: client, amount, days overdue — shown in red

Refresh from files when opened.
```

---

### Example 19 — Founder's Operational Command Center

**Situation:** You're a startup founder. Before every call or standup, you want a full operational snapshot.

**Prompt:**
```
Build a live artifact: Founder Dashboard.

Pull from:
- Gmail: unread emails from investors, key customers (filter by contact list in ~/Contacts/priority.txt)
- Slack: #alerts, #customers, #team channels — last 24 hours
- Linear: all bugs labelled "critical" or "urgent"
- Google Sheets: ~/Metrics/kpi_tracker.csv — revenue, DAU, churn (last 30 days)
- HubSpot (via MCP): deals in "Proposal Sent" or "Negotiation" stage

Layout:
- Top: 5 KPI cards (MRR, DAU, Churn, Open deals value, Critical bugs)
- Middle left: Priority emails (unread, from priority contacts)
- Middle centre: Critical Slack alerts
- Middle right: Open deals pipeline
- Bottom: Critical and urgent bugs list

Auto-refresh on open.
```

---

### Example 20 — HR Hiring Pipeline Tracker

**Situation:** You're a hiring manager tracking 8 open roles across different stages.

**Prompt:**
```
Build a live artifact: Hiring Pipeline Dashboard.

Pull from:
- ~/Hiring/pipeline.csv — columns: role, candidate, stage, last_activity, interviewer, notes
- Google Calendar (via MCP): any events with "interview" in the title for this week
- Gmail: any emails with subject containing "application" or "interview" from last 48 hours

Sections:
1. Pipeline Overview: kanban-style columns (Applied, Phone Screen, Technical, Final, Offer, Rejected)
2. This Week's Interviews: from calendar — role, candidate, time, interviewer
3. Stale Candidates: anyone with no stage change in 7+ days, flagged amber
4. Roles by Stage Count: bar chart, one bar per open role

Refresh on open.
```

---

### Example 21 — Academic Grant Deadline Monitor

**Situation:** You're tracking 12 funding opportunities. Missing a deadline costs a year.

**Prompt:**
```
Build a live artifact: Grant Deadline Monitor.

Pull from:
- ~/Grants/tracked_opportunities.csv — columns: grant_name, funder, deadline, status, draft_file
- ~/Grants/drafts/ — check for existence of a draft file per grant

Display:
- Red: deadlines within 30 days AND no draft file found
- Amber: deadlines within 30 days WITH a draft in progress
- Green: deadlines 31–90 days away
- Grey: deadlines beyond 90 days or already submitted

Also show: a timeline view of all deadlines for the next 6 months.
Refresh when opened.
```

---

### Iterating on a Live Artifact

Every time you open a Live Artifact you can ask Claude to change it:
- *"Add a fourth panel showing my Notion tasks due this week"*
- *"Make the overdue items blink in red instead of just turning red"*
- *"Replace the table with a bar chart"*

Each change is versioned. To restore an earlier version: open the artifact → Version history → Restore.

---

## 8. Dispatch — Working From Anywhere

### What It Is

Dispatch is a remote trigger for your desktop. You type a task prompt from your phone (or any browser), and it fires that task into a full Cowork session running on your desktop machine. Your desktop does the actual work — reading your files, calling your connected apps, running code — while you're away.

Think of it as: *you have a capable colleague sitting at your desk, waiting for instructions you can send from anywhere.*

**Available on:** Pro and Max plans.

**Critical requirement:** Your desktop must stay awake, plugged in, and Claude Desktop must be running. Sleep mode stops execution.

### When to Use Dispatch vs Other Features

| Situation | Use |
|-----------|-----|
| One-off big task, you'll be away | **Dispatch** |
| Same task every week | **Scheduled Task** |
| You're at your desk | **New Task** |
| You need live data on demand | **Live Artifact** |

### Setting Up Dispatch

1. Open Claude Desktop
2. Cowork → Dispatch
3. Enable Dispatch and note your Dispatch address or open the mobile companion app
4. On your phone: open the Claude app → Dispatch tab → type your task

---

### Example 22 — Report Before a Long Flight

**Situation:** You're about to board a 4-hour flight. You want a full competitive analysis ready when you land.

**Dispatch from phone (gate lounge):**
```
Research our top 3 competitors — [CompanyA], [CompanyB], [CompanyC] — for Q2 2026 product updates.
Search the web and check ~/Research/competitor_notes/ on my desktop for existing notes.
Write a 1,500-word analysis: one section per competitor covering new features, pricing changes, market moves.
End with a 1-page comparison table.
Save to ~/Reports/competitive_analysis_June2026.docx.
```

You land. Open your laptop in the cab. The document is there.

---

### Example 23 — Build a Deck During Back-to-Back Meetings

**Situation:** You have meetings from 9 AM to 4 PM. At 1 PM you have 90 seconds between sessions.

**Dispatch from phone (hallway):**
```
Read ~/Projects/ProductRoadmap/Q3_roadmap.xlsx and the design mockups in ~/Design/mockups/Q3/.
Build a 12-slide PowerPoint for the all-hands presentation tomorrow:
Slide 1: Title
Slide 2: Q2 Recap (key metrics from roadmap file)
Slides 3–7: Q3 Feature Highlights (one slide per major feature, use mockup images)
Slide 8: Engineering milestones
Slide 9: Risks and mitigations
Slide 10: Success metrics
Slide 11: Team shoutouts (pull names from ~/Team/q2_contributors.txt)
Slide 12: Q&A slide
Save as ~/Presentations/allhands_June2026.pptx.
```

At 4 PM the deck is done.

---

### Example 24 — Overnight Literature Review

**Situation:** You're a researcher. Before bed, you want Claude to process a folder of papers overnight.

**Dispatch from phone (11 PM):**
```
Read every PDF in ~/Papers/to_review/ (there are about 20).
For each paper extract:
- Full citation (APA)
- Hypothesis
- Methodology (2 sentences)
- Key results (3 bullets)
- Limitations
- Relevance to my thesis topic: "Neural interfaces in motor rehabilitation"

Build a master comparison table across all papers.
Identify 3 themes that emerge across multiple papers.
Save complete review to ~/Papers/lit_review_draft_{date}.docx.
Move processed PDFs to ~/Papers/reviewed/.
```

Wake up to a complete literature review draft.

---

### Example 25 — Inbox Triage After a Day Offline

**Situation:** You were travelling with no connectivity. 47 emails landed. You want them sorted before you open your inbox.

**Dispatch (from airport arrivals hall):**
```
Check my Gmail (via MCP). I have been offline for 24 hours.
Triage ALL unread emails from the last 24 hours:

Priority 1 — Urgent (action required today):
- Emails from my manager or direct reports
- Customer escalations
- Time-sensitive requests

Priority 2 — Needs reply (within 48 hours):
- Client emails
- Partner/vendor requests

Priority 3 — FYI (read but no reply needed)
Priority 4 — Newsletter/automated (can archive)

For every Priority 1 email, write a draft reply.
Save all drafts to ~/Drafts/inbox_triage_{date}/.
Create a summary file: ~/Drafts/inbox_summary_{date}.txt listing Priority 1 items with sender, subject, and 1-line action.
```

---

### Example 26 — Pre-Meeting Prep While Commuting

**Situation:** You're on a 45-minute train. You have a sales call with a new prospect in 2 hours and you haven't done any prep.

**Dispatch from phone (on train):**
```
Research [ProspectCompany] — a B2B SaaS company in logistics.
From the web find: company size, recent news, products, pricing (if public), key executives, known pain points in their industry.
Read any existing notes in ~/Sales/prospects/[ProspectCompany]/ if the folder exists.

Build a 1-page call prep brief:
- Company overview (5 bullets)
- Key stakeholders (names, titles, LinkedIn if found)
- Likely pain points (ranked by relevance to our product)
- Our relevant case studies to mention
- 5 discovery questions tailored to their context
- Red flags or risks to watch for

Save as ~/Sales/call_prep_[ProspectCompany]_{date}.docx.
```

---

### Dispatch Tips

- **Be specific about output paths.** Dispatch runs unattended — if you don't specify where to save, Claude will try to infer, and you may spend time finding the output.
- **Front-load the most important instruction.** Dispatch prompts are read top-to-bottom. Put the core deliverable first.
- **Pre-authorize your connectors.** If Claude needs Gmail or Slack mid-task, the connector must already be authorized in Customize. Dispatch can't prompt you for a login.
- **Keep the machine plugged in.** Sleep or battery death kills the task silently.
- **Check notification settings.** Configure Cowork to notify you (Slack, email, or push) when a Dispatch task completes.

---

## 9. Customize — Making Cowork Yours

### What It Is

Customize is where you configure how Cowork behaves globally — across all tasks, all projects. It includes:
- **Instructions** — rules Claude follows in every session
- **Connectors** — authorizing apps Claude can call (Gmail, Slack, GitHub, etc.)
- **Plugins** — bundled skill+connector packages for specific roles or teams
- **Notifications** — how and when Cowork alerts you
- **Default folder** — where outputs go unless specified otherwise

Customize is also where project-level overrides are set (inside each project's settings).

---

### Example 27 — Personal Developer Setup

**Situation:** You're a software engineer who uses Cowork daily for code tasks, PR prep, and documentation.

**Global instructions:**
```
I am a senior software engineer. Primary languages: TypeScript and Go.
Code style: follow project .eslintrc and golangci.yml configs if present.
Always use the existing error handling pattern in the file — don't introduce new patterns.
Never create console.log debugging unless I ask.
When writing tests, prefer integration tests over mocks.
Output to the correct project folder; never create files at root level.
When suggesting shell commands, use bash syntax.
Notify me on Slack (#me) when any task over 5 minutes completes.
```

---

### Example 28 — Marketing Team Setup

**Situation:** A marketing lead sets up Cowork for a 6-person team. Everyone needs consistent brand voice and access to brand assets.

**Team-level global instructions:**
```
Company: [CompanyName]. Industry: B2B SaaS, HR Tech.
Brand voice: warm, direct, human. Avoid corporate buzzwords.
Never use: "leverage", "synergy", "revolutionize", "game-changing".
All external-facing copy must be reviewed before sending — save as DRAFT.
Brand color codes: #2D3748 (dark), #4299E1 (blue), #48BB78 (green).
Logo and asset folder: ~/Marketing/brand_assets/
Legal disclaimer required on all advertising copy: save in ~/Legal/disclaimer.txt
Output folder default: ~/Marketing/outputs/
```

**Connectors authorized for the whole team:**
- HubSpot (campaign data, contact lists)
- Google Analytics (traffic data)
- Slack (for posting finished work to #marketing-review)
- Google Drive (for reading research documents)

---

### Example 29 — Legal Team Compliance Setup

**Situation:** A compliance officer at a financial firm sets Cowork up for the legal department.

**Instructions:**
```
Department: Legal & Compliance.
All outputs must be saved only to ~/Legal/approved_outputs/ — no exceptions.
Do not access any external URLs not in the approved domain list at ~/Legal/approved_domains.txt.
Append to every document: "DRAFT — FOR INTERNAL REVIEW ONLY. NOT LEGAL ADVICE."
All documents must include: date created, author (use "Legal Team"), version number.
Do not summarize or paraphrase regulatory text — quote it directly with citation.
Flag any instruction that may conflict with GDPR, FCA regulations, or internal policy.
```

**Plugin installed:** Internal document classification plugin (tags every output with sensitivity: RESTRICTED / INTERNAL / PUBLIC)

---

### Example 30 — Research Lab Setup

**Situation:** A PI sets up Cowork for their research lab — 4 postdocs and PhD students.

**Instructions:**
```
Lab: [Lab Name], focus: computational neuroscience.
All data analysis should use Python (pandas, numpy, scipy, matplotlib unless otherwise specified).
Statistical significance threshold: p < 0.05. Always report effect sizes alongside p-values.
Output plots: save as both .png (300 dpi) and .svg.
Citation format: APA 7th edition.
IRB protocol number: [number] — include in any output involving participant data.
Never include raw participant data in reports — use de-identified summaries only.
```

### Plugins

Plugins are installable packages that bundle skills, connectors, and sub-agents for a specific workflow. Examples:

| Plugin Type | What It Includes |
|-------------|-----------------|
| Salesforce CRM plugin | CRM connector + deal query skills + outreach templates |
| GitHub Developer plugin | GitHub connector + PR review skills + commit message generation |
| HR Recruiting plugin | ATS connector + JD writing skills + interview scoring rubrics |
| Analytics plugin | Google Analytics + Mixpanel connectors + reporting templates |

To install: **Customize → Plugins → Browse / Install**

---

## 10. MCP Connectors — Connecting to Your Apps

### What Are MCP Connectors?

MCP (Model Context Protocol) connectors give Claude authorized access to your external apps — Gmail, Slack, Google Calendar, GitHub, Notion, HubSpot, and many others. Without connectors, Claude can only read and write your local file system. With connectors, it can pull live data from and push outputs to your entire tool stack.

### Authorizing a Connector

1. Cowork → Customize → Connectors
2. Find the app you want (or browse the marketplace)
3. Click **Connect** → complete the OAuth flow in your browser
4. Select which permissions to grant (read-only vs read+write)
5. The connector is now available in any task, scheduled task, or live artifact

### What Connectors Enable

| Connector | What Claude Can Do |
|-----------|-------------------|
| **Gmail** | Read emails, search by sender/subject/date, send drafts, move to folders |
| **Google Calendar** | Read events, check availability, create events |
| **Slack** | Read channels and DMs, post messages, search history |
| **GitHub** | Read repos, PRs, issues; create branches, open PRs |
| **Notion** | Read and write pages and databases |
| **HubSpot** | Read/update contacts, deals, and pipeline data |
| **Linear** | Read and update tickets, create new issues |
| **Google Drive** | Read files, create documents, organize folders |
| **Jira** | Read and update tickets, transitions |

### Connector Best Practices

- **Grant only the permissions you need.** Read-only is safer for data sources; read+write for tools you want Claude to update.
- **Re-authorize after password changes.** Connectors break silently if the underlying credentials expire.
- **Scope connectors per project.** In a project's settings, you can restrict which connectors are available — useful for sensitive projects.
- **Test before scheduling.** Run a one-off task using a connector before relying on it in a scheduled task.

---

## 11. Writing Good Prompts for Cowork

### The Anatomy of a Strong Cowork Prompt

```
[GOAL] — what you want delivered
[INPUT] — where the data/files are (exact paths)
[PROCESS] — any rules, logic, or calculations
[OUTPUT] — what format, where to save, what to name it
[CONSTRAINTS] — what not to do, what to check first
```

### Examples of Weak vs Strong Prompts

**Weak:**
```
Summarize my emails
```

**Strong:**
```
Check my Gmail. Find all unread emails from the last 48 hours.
Ignore newsletters (Substack, MailChimp, automated notifications).
For the remaining emails: group by sender domain. 
For each sender, write a 1-line summary of what they need from me.
Rank by urgency (infer from subject and content).
Save as ~/Desktop/email_summary_{date}.md.
```

---

**Weak:**
```
Make a presentation about Q3
```

**Strong:**
```
Read ~/Finance/Q3_results.xlsx and ~/Sales/Q3_pipeline.xlsx.
Build a 10-slide PowerPoint for the Q3 board review:
- Slide 1: Title — "Q3 2026 Business Review"
- Slide 2: Executive summary (3 bullets, under 30 words each)
- Slides 3–5: Financial performance (revenue, gross margin, burn) — use charts from the Finance file
- Slide 6: Sales pipeline (from pipeline file) — deals by stage
- Slide 7: Top 3 wins (from pipeline — deals with status "Closed Won" in Q3)
- Slide 8: Top 3 risks (infer from pipeline — deals stalled >30 days)
- Slide 9: Q4 outlook
- Slide 10: Appendix data table
Font: Inter. Colors: #1A202C (dark) and #3182CE (blue).
Save as ~/Presentations/Q3_board_review.pptx.
```

### Common Prompt Mistakes

| Mistake | Why It's a Problem | Fix |
|---------|-------------------|-----|
| Vague goal ("analyze this") | Claude has to guess what you want | State the specific deliverable |
| No output path | Claude saves somewhere you can't find | Always specify `save as ~/path/filename.ext` |
| No format specified | Claude chooses — may not be what you need | Specify: `.docx`, `.pdf`, `.xlsx`, `.md`, `.pptx` |
| Too many goals in one task | Claude may deprioritize some | For complex multi-output work, use Projects with multiple tasks |
| Forgetting permissions | Claude can't access a connector you haven't authorized | Pre-authorize in Customize |

### Steering Mid-Task

You can interrupt and redirect any running task:
- **Pause:** Type "pause" or click the pause button
- **Redirect:** Type the correction (e.g., "Use the March data instead of April")
- **Stop:** Type "stop" — Claude will stop and preserve work done so far
- **Clarify:** Ask a question — Claude will answer and then continue

---

## 12. Advanced Patterns — Combining Features

### Pattern 1 — The Automated Weekly Briefing Package

Combine Scheduled Tasks + Live Artifact for a manager who needs both a recurring report AND a live dashboard.

**Scheduled task (every Monday 7 AM):**
```
/schedule every Monday at 07:00
Read ~/Work/team_updates/ for any files updated last week.
Pull sprint data from Linear (via MCP).
Generate ~/Reports/team_brief_{date}.docx — team status, blockers, completed items.
Post summary to #team-leads on Slack.
```

**Live artifact (built once, always current):**
```
Build a live artifact: Team Lead Dashboard.
Pull from Linear (sprint progress), GitHub (open PRs), Slack (#team-updates last 48hrs).
Refresh on open. Show: sprint burndown, PR review backlog, blockers flagged by the team.
```

The scheduled task generates the weekly narrative; the live artifact gives you the live pulse at any moment.

---

### Pattern 2 — The Client Delivery Pipeline

For consultants or agencies: Project + Scheduled Tasks + Dispatch.

1. **Project** for each client — instructions, brand rules, memory
2. **Scheduled task** inside the project — weekly data pull from client systems
3. **Dispatch** when you're travelling — kick off specific deliverables from your phone while on the move

---

### Pattern 3 — The Research Production Line

For researchers or analysts:

1. **New Task** — pull and organize raw data into a clean CSV
2. **New Task** — run analysis on the clean data, generate charts
3. **New Task** — write the report narrative using the analysis
4. **Scheduled Task** — run the whole pipeline monthly with fresh data

Each step is a separate task so you can review and approve outputs before the next step runs.

---

### Pattern 4 — The Inbox-Zero Automation

Daily Scheduled Task + Dispatch combo:

**Scheduled task (every morning 7 AM):**
```
Triage overnight emails. Flag Priority 1, archive newsletters.
Save a triage summary to ~/Desktop/inbox_summary_today.txt.
```

**Dispatch (from phone if you're out):**
```
Draft replies for all Priority 1 items from today's inbox summary.
Save drafts to ~/Drafts/replies_{date}/ for my review.
```

---

## 13. Personas: Cowork for Different Roles

### For the Consultant

| Feature | How You Use It |
|---------|---------------|
| Projects | One project per client engagement, full memory and instructions |
| New Task | Draft reports, build decks, analyze data |
| Dispatch | Kick off deliverables from client site or train |
| Scheduled | Weekly status reports, monthly data pulls |
| Live Artifact | Client health dashboard — deliverables, milestones, open items |

**Most-used prompt pattern:**
```
[Client] — [deliverable type] — [input source] — [output format and path]
```

---

### For the Knowledge Worker / Manager

| Feature | How You Use It |
|---------|---------------|
| Scheduled | Daily brief, weekly status, meeting prep auto-runs |
| Live Artifact | Team dashboard — who's blocked, what's overdue |
| Dispatch | Send tasks from phone between meetings |
| New Task | Synthesize notes, prepare talking points, analyze data |

---

### For the Freelancer / Solo Operator

| Feature | How You Use It |
|---------|---------------|
| Projects | One per client, with instructions per client tone |
| Scheduled | Monthly invoice chase, weekly pipeline review |
| Live Artifact | Freelance tracker — hours, money, deadlines in one view |
| Dispatch | Kick off work while travelling to client meetings |
| Customize | Personal preferences: preferred file formats, output folders |

---

### For the Researcher / Academic

| Feature | How You Use It |
|---------|---------------|
| Projects | One per research project — papers, notes, drafts all in one place |
| New Task | Paper digests, literature reviews, data analysis, report writing |
| Scheduled | Quarterly CV updates, weekly literature scans |
| Live Artifact | Grant deadline monitor, paper backlog tracker |
| Dispatch | Queue overnight processing of paper batches |

---

### For the Developer

| Feature | How You Use It |
|---------|---------------|
| New Task | Code review, documentation, test generation, PR summaries |
| Projects | One per repository — Claude knows the codebase rules |
| Live Artifact | Pre-standup dashboard — PRs, Linear tickets, CI status |
| Scheduled | Weekly tech debt audit, dependency update reports |
| Customize | Code style instructions, language preferences, notification settings |

---

## 14. Troubleshooting

### Task Stopped Mid-Way

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| Task stopped, no output | Machine went to sleep | Disable sleep mode while tasks run |
| Task stopped with error | Connector expired | Re-authorize connector in Customize |
| Task stopped with error | File not found | Check the path in your prompt (exact case, correct subfolder) |
| Task running very slowly | Large number of files | Break into smaller tasks; process one folder at a time |

### Scheduled Task Didn't Run

1. Was Claude Desktop open at the scheduled time? (Check Recents for last activity)
2. Was the machine awake? (Check power/sleep settings)
3. Did a connector expire? (Check Customize → Connectors for expired authorizations)
4. Is there a task error? (Click the scheduled task in Cowork → Scheduled to see last run status)

### Live Artifact Not Refreshing

1. Open the artifact and click **Refresh** manually
2. Check that the connected MCP connectors are still authorized
3. Check that local files the artifact reads still exist at the expected paths
4. If a connector was re-authorized, rebuild the artifact (ask Claude to regenerate it)

### Dispatch Not Working

1. Is Claude Desktop open on the desktop machine?
2. Is the machine awake and plugged in?
3. Is Dispatch enabled in Customize?
4. Is the desktop on the same account as your phone?

### Claude Doesn't Remember Previous Work

- Check that you're running the task inside a **Project** (memory is only active in Projects, not standalone tasks)
- Check that memory is enabled for the project: Project settings → Memory → On
- Note: standalone tasks (outside a project) have no memory across sessions

---

## 15. Decision Guide

### Which Feature Should I Use?

```
Is this a one-off task I need done now?
  → Yes, I'm at my desk → New Task
  → Yes, but I'm about to go offline → Dispatch

Is this work I'll do repeatedly on a schedule?
  → Scheduled Task

Is this work that belongs to a longer engagement or ongoing project?
  → Projects (and use New Task within it)

Do I need a live view I can check anytime, that's always current?
  → Live Artifact

Do I want Claude to always behave a certain way, use my preferences, or connect to my apps?
  → Customize
```

### Which Feature for Each Work Type

| Work Type | Feature |
|-----------|---------|
| One-off analysis, report, document | New Task |
| Ongoing client work | Project + New Task |
| Weekly/monthly reporting | Scheduled Task |
| Morning briefing | Scheduled Task |
| Status dashboard | Live Artifact |
| Work while travelling | Dispatch |
| Global preferences, brand rules | Customize |
| Team standards, compliance rules | Customize (Team/Enterprise) |
| Cross-app live data view | Live Artifact + MCP connectors |

---

## 16. Quick Reference

### Key Paths and Commands

| Action | How |
|--------|-----|
| New task | Cowork → + New task |
| New project | Cowork → Projects → + |
| Schedule a task | Type `/schedule` in any task |
| View all scheduled tasks | Cowork → Scheduled |
| New live artifact | Cowork → Live artifacts → New artifact |
| Send Dispatch from phone | Claude mobile app → Dispatch |
| Add global instructions | Cowork → Customize → Instructions |
| Add a connector | Cowork → Customize → Connectors |
| Pause a running task | Type "pause" in the task chat |
| Stop a running task | Type "stop" in the task chat |

### Plan Requirements

| Feature | Pro | Max | Team | Enterprise |
|---------|-----|-----|------|-----------|
| New Task | ✓ | ✓ | ✓ | ✓ |
| Projects | ✓ | ✓ | ✓ | ✓ |
| Scheduled Tasks | ✓ | ✓ | ✓ | ✓ |
| Live Artifacts | ✓ | ✓ | ✓ | ✓ |
| Dispatch (mobile) | ✓ | ✓ | — | — |
| Customize / Plugins | ✓ | ✓ | ✓ | ✓ |

### Constraints to Know

| Constraint | Detail |
|-----------|--------|
| Desktop must stay open | Tasks, Dispatch, and Scheduled Tasks pause if Claude Desktop closes or machine sleeps |
| Local storage only | Projects and Live Artifacts live on your machine — no cloud sync |
| No team sharing | Team/Enterprise members cannot share Cowork projects with each other (as of June 2026) |
| Token usage | Cowork tasks consume significantly more tokens than Chat |
| Dispatch machine requirement | Desktop must be awake, plugged in, and running Claude Desktop |
| Live Artifact connectors | Must be pre-authorized — artifacts can't prompt for login at refresh time |

---

## Sources

- [Get started with Claude Cowork — Claude Help Center](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork)
- [Use live artifacts in Claude Cowork — Claude Help Center](https://support.claude.com/en/articles/14729249-use-live-artifacts-in-claude-cowork)
- [Organize your tasks with projects in Claude Cowork — Claude Help Center](https://support.claude.com/en/articles/14116274-organize-your-tasks-with-projects-in-claude-cowork)
- [The Three Modes of Claude Cowork: Dispatch, Scheduled Tasks, and Live Artifacts](https://techysurgeon.substack.com/p/the-three-modes-of-claude-cowork)
- [Claude Cowork Live Artifacts: From Static Report to Living Dashboard — Medium](https://medium.com/@richardhightower/claude-cowork-live-artifacts-from-static-report-to-living-dashboard-544561169d2a)
- [Claude Cowork vs Managed Agents — FindSkill.ai](https://findskill.ai/blog/claude-cowork-guide/)
- [Zero to Pro: The Ultimate Claude Cowork 2026 Setup Tutorial — Geeky Gadgets](https://www.geeky-gadgets.com/claude-cowork-beginner-tutorial-2026/)
