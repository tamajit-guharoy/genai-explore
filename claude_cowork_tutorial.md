# Claude Cowork: A Practical Tutorial

Claude Cowork is the agentic workspace inside Claude Desktop. You describe an outcome, step away, and come back to finished work. It lives on your machine — reads and writes your local files directly, runs code in an isolated VM, coordinates parallel workstreams — and is distinct from Claude Chat (single-turn Q&A) and Claude Code (developer CLI). Cowork launched in research preview January 2026 and reached general availability on all paid plans in April 2026.

**Prerequisite:** Claude Desktop (macOS or Windows), paid plan (Pro, Max, Team, or Enterprise). Keep the desktop app open while tasks run.

---

## Feature 1: New Task

**What it is:** The entry point for everything. You type a goal in plain language, Claude plans the work, breaks it into subtasks, runs them — reading and writing your local files — and delivers the result. Unlike chat, tasks can run for minutes or hours without timing out.

**How Claude executes a task:**
1. Analyses your request and builds a plan
2. Breaks it into subtasks (can run in parallel)
3. Runs code in an isolated VM on your machine
4. Reads and writes your local file system
5. Shows progress so you can steer mid-task if needed

---

### Real-World Example 1 — Morning Briefing Before a Big Meeting

**Scenario:** You have a board meeting at 9 AM. It's 7:30. You want a single-page brief covering last quarter's revenue numbers, three open action items from the previous meeting (in a Word doc on your desktop), and any emails flagged as urgent in the last 24 hours.

**Task prompt:**
```
Read the file ~/Desktop/board_meeting_notes_Q1.docx and extract all open action items.
Then check my email (Gmail via MCP) for anything marked urgent in the last 24 hours.
Pull Q2 revenue from ~/Documents/finance/q2_actuals.xlsx.
Combine everything into a one-page brief saved to ~/Desktop/board_brief_today.docx.
```

**What happens:** Claude opens the Word doc, scans for action items, queries Gmail, reads the spreadsheet, and writes a formatted brief — all without you touching a single file.

---

### Real-World Example 2 — Turning 40 Customer Emails Into a Structured Report

**Scenario:** Your support inbox has 40 unresolved complaint threads. You need a summary report grouping them by issue type, with a recommended fix for each group, before a product sync at 2 PM.

**Task prompt:**
```
Export the last 40 unresolved support tickets from ~/Downloads/tickets_export.csv.
Group them by issue category (e.g., billing, login, performance).
For each category, write a one-paragraph summary and a recommended fix.
Save as ~/Documents/support_analysis_June2026.pdf.
```

**Outcome:** A structured PDF ready for the meeting, in about 4 minutes.

---

### Real-World Example 3 — Processing a Research Paper Backlog

**Scenario:** You have 15 PDFs in a `~/Papers/unread/` folder that have been sitting there for three weeks.

**Task prompt:**
```
Read every PDF in ~/Papers/unread/.
For each paper write: title, 3-sentence summary, key finding, and relevance to "AI in clinical diagnostics".
Compile into ~/Papers/reading_list_summary.md, sorted by relevance score (1–10).
```

---

## Feature 2: Projects

**What it is:** Projects are dedicated workspaces that group related tasks, files, instructions, and memory together. Each Project links to a local folder on your machine. Claude remembers context from every task you run inside a project and applies it to future tasks — but that memory is scoped strictly to that project.

**Three ways to create a project:**
- **From scratch** — new folder, custom instructions, attach files
- **Import from Claude Project** — bring over files and instructions from a chat project
- **Use existing folder** — point Cowork at a folder you already have

**What each project contains:**
- **Instructions** — tone, formatting rules, domain context that applies to every task
- **Context** — local folders, linked URLs, imported project files
- **Scheduled tasks** — recurring automations scoped to this project
- **Memory** — Claude learns from every task run and carries that forward

---

### Real-World Example 4 — A Client Project Workspace

**Scenario:** You're a consultant running a three-month engagement for a retail client. Research, reports, slide decks, and email drafts all need to live in one place with consistent formatting.

**Setup:**
1. Open Cowork → Projects → + → Use Existing Folder → select `~/Clients/RetailCo/`
2. Add instructions:
   ```
   Tone: professional, concise. Avoid jargon.
   Always include an executive summary on page 1 of every report.
   Client brand colors: #E63946 (red), #457B9D (blue).
   Never share financials outside of the reports subfolder.
   ```
3. Attach `~/Clients/RetailCo/brand_guidelines.pdf` as context.

Now every task you run in this project automatically inherits those rules. A week later you ask: *"Draft the mid-engagement progress report."* Claude remembers the work it did in week 1 and week 2 — no recap needed.

---

### Real-World Example 5 — A Personal Job Search Workspace

**Scenario:** You're job hunting. You want to track applications, tailor CVs, draft cover letters, and prep for interviews — all in one place.

**Setup:**
- Project folder: `~/JobSearch/`
- Instructions: *"My target role is Senior Product Manager in fintech. My CV is in base_cv.docx. Always tailor cover letters to the company's stated values."*
- Context: link your base CV, a folder of job descriptions you've saved

**Tasks you then run:**
- *"Tailor my CV for the attached JD from Stripe and save as cv_stripe.docx"*
- *"Write a cover letter for the Revolut PM role using their values from ~/JobSearch/revolut_jd.pdf"*
- *"Create an interview prep sheet for a fintech PM role: 10 likely questions with model answers based on my CV"*

Because memory is on, Claude knows your base CV and previous tailoring decisions without you repeating them every time.

---

### Real-World Example 6 — A Content Studio Project

**Scenario:** You run a newsletter. Every week you research a topic, write a draft, create social posts, and schedule sends.

**Project instructions:**
```
Newsletter name: The Signal. Audience: senior tech leaders. 
Tone: sharp, no filler, no bullet-point overload.
Word count target: 800 words for main article, 100 words for LinkedIn post.
Always include one contrarian take per issue.
```

One command per week: *"Research and draft this week's issue on AI in supply chain. Pull from my saved articles in ~/Newsletter/research/week24/"*

---

## Feature 3: Scheduled Tasks

**What it is:** Recurring tasks that run automatically on a cadence you set. Type `/schedule` in any task to configure timing. The machine must be awake and Claude Desktop must be running at the scheduled time.

**Best for:** Predictable, repeating work you currently do manually — weekly reports, daily digests, monthly data pulls, quarterly document updates.

**Decision rule:** If it happens on a fixed schedule and you always do the same thing → Scheduled Task.

---

### Real-World Example 7 — Weekly Team Status Report

**Scenario:** Every Monday at 8 AM your manager expects a status update covering tasks completed, blockers, and plan for the week.

**Setup:**
```
/schedule every Monday at 08:00

Read all files modified last week in ~/Work/ProjectAlpha/.
Check my calendar (via MCP) for meetings and outcomes from last week.
Draft a status report covering: (1) completed work, (2) blockers, (3) this week's plan.
Save to ~/Work/reports/status_week_{date}.docx and email it to manager@company.com.
```

You never write another status report manually.

---

### Real-World Example 8 — Daily Sales Dashboard Refresh

**Scenario:** Your sales team checks a summary dashboard every morning. The underlying data is a CSV export from your CRM that updates nightly.

**Setup:**
```
/schedule every day at 07:00

Read ~/CRM_exports/daily_leads.csv (updated overnight by CRM sync).
Calculate: new leads today, pipeline value, conversion rate vs last 7 days.
Update ~/Dashboards/sales_summary.xlsx with today's row.
Send a Slack message to #sales-team with the three key numbers.
```

---

### Real-World Example 9 — Monthly Invoice Chase

**Scenario:** You freelance. Every month on the 25th you want to check which invoices are outstanding and send polite chasers.

**Setup:**
```
/schedule every month on the 25th at 09:00

Read ~/Finances/invoices/ for any invoice marked unpaid and due within 30 days.
Draft a polite payment reminder email for each.
Save drafts to ~/Finances/chasers/{client}_{date}.txt for my review.
```

---

### Real-World Example 10 — Quarterly CV and Bio Update

**Scenario:** You're an academic. Every quarter you want your CV and short bio updated to reflect new publications, talks, and grants.

**Setup:**
```
/schedule every 3 months on the 1st at 10:00

Check ~/Research/publications/ for any new PDFs added since last update.
Update ~/CV/cv_master.docx with new entries in the Publications section.
Regenerate ~/Bio/short_bio_150w.txt to reflect the latest additions.
```

---

## Feature 4: Live Artifacts

**What it is:** Live artifacts are persistent, interactive HTML dashboards that Claude builds for you inside Cowork. They connect to your apps and files through MCP connectors and refresh with current data every time you open them. Unlike a one-time chat artifact, they live in their own dedicated tab, are versioned (you can restore earlier versions), and stay current automatically.

**Available on:** Pro, Max, Team, Enterprise — Claude Desktop only (macOS and Windows).

**Best for:** Information you check repeatedly at unpredictable times — a command center you glance at before meetings, a tracker that's always up to date.

**Decision rule:** If you need a glanceable view that updates whenever you open it → Live Artifact.

---

### Real-World Example 11 — Pre-Standup Command Center

**Scenario:** Every morning before standup you check: Slack threads mentioning your name, open PRs awaiting your review, Linear tickets in progress, and today's calendar.

**Prompt to build it:**
```
Build a live artifact: my pre-standup command center.
Pull from: Slack (mentions of @me in the last 24 hrs), GitHub (open PRs assigned to me),
Linear (my in-progress tickets), Google Calendar (today's meetings).
Layout: 4 panels, one per source. Refresh each time I open it.
```

**Result:** A single HTML page. Every morning you click "Live Artifacts" → open your dashboard → everything is current. No switching between four apps.

---

### Real-World Example 12 — Freelance Project Tracker

**Scenario:** You have five active clients. You want a live view of: open deliverables per client, hours logged this week, unpaid invoices, and next deadline.

**Prompt:**
```
Build a live artifact: freelance project tracker.
Pull from: ~/Freelance/projects/ (project files), ~/Freelance/time_logs.csv,
~/Finances/invoices/ (filter unpaid).
Show: per-client status card, a timeline of deadlines this month, unpaid invoice total.
```

---

### Real-World Example 13 — Competitive Intelligence Radar

**Scenario:** You're a product manager. You want a live dashboard of competitor news, new feature launches, and pricing changes — scanned from RSS feeds and saved articles.

**Prompt:**
```
Build a live artifact: competitor radar for [CompanyA], [CompanyB], [CompanyC].
Pull from: RSS feeds for each company's blog, ~/Research/competitor_notes/,
and search news for each company name.
Show: latest news by company, any pricing page changes (compare to last snapshot),
new feature mentions flagged in red.
Refresh each time I open it.
```

---

### Real-World Example 14 — Grant Deadline Monitor (Academic/Nonprofit)

**Scenario:** You track 12 funding opportunities with rolling deadlines. Missing one costs a year.

**Prompt:**
```
Build a live artifact: grant deadline monitor.
Pull from: ~/Grants/tracked_opportunities.csv and NIH/AHRQ grant calendar (via web).
Show: grants due in next 30 days (red), 60 days (amber), 90 days (green).
Flag any where I haven't started a draft (no file in ~/Grants/drafts/ matching the grant name).
```

---

## Feature 5: Dispatch (Beta)

**What it is:** Dispatch is a remote trigger. You send a task prompt from your phone (or any browser), and it fires into a full Cowork session running on your desktop — with access to all your local files, connected apps, and full Claude capabilities. Your desktop does the work; your phone issued the order.

**Available on:** Pro and Max plans (mobile access).

**Requirement:** Your desktop must stay awake and plugged in. Sleep mode stops Dispatch execution.

**Best for:** One-time, substantial tasks you want running while you're away — on a flight, in a meeting, at the gym.

**Decision rule:** One-off task + you'll be unavailable while it runs → Dispatch.

---

### Real-World Example 15 — Kick Off a Report From Your Phone Before a Flight

**Scenario:** You board a 4-hour flight. Before takeoff you want Claude to compile a full competitive analysis while you're in the air, ready when you land.

**From your phone (Dispatch):**
```
Research our top 3 competitors' Q2 2026 product updates using web search.
Cross-reference with ~/Research/competitor_notes/ on my desktop.
Write a 1,500-word analysis with a summary table.
Save to ~/Reports/competitor_analysis_June2026.docx.
```

You land. The report is done. You review it in the cab.

---

### Real-World Example 16 — Prep a Presentation While You're in a Meeting

**Scenario:** You have back-to-back meetings until 4 PM. At 1 PM between sessions you have 90 seconds on your phone.

**Dispatch prompt:**
```
Using ~/Projects/ProductRoadmap/roadmap_Q3.xlsx and the design files in ~/Design/mockups/,
build a 12-slide presentation deck for the all-hands tomorrow.
Slide structure: problem, solution, roadmap, metrics, next steps.
Save as ~/Presentations/allhands_June2026.pptx.
```

At 4 PM when your meetings end, the deck is on your desktop.

---

### Real-World Example 17 — Overnight Literature Review

**Scenario:** You're a researcher. Before bed you want Claude to work through a list of 20 papers.

**Dispatch prompt (from phone at 11 PM):**
```
Read every PDF in ~/Papers/to_review/.
For each: extract hypothesis, methodology, key results, limitations.
Build a comparison table across all 20 papers.
Save to ~/Papers/literature_review_draft.docx.
```

Wake up to a complete literature review.

---

### Real-World Example 18 — Triage and Draft Replies to a Full Inbox

**Scenario:** You were offline for a day. 47 emails landed. You want them triaged and draft replies ready before you open your inbox.

**Dispatch prompt:**
```
Check my Gmail (via MCP). Triage the last 47 unread emails:
- Flag urgent (response needed today) in red
- Categorize the rest: FYI, needs reply later, newsletters
Draft replies for every urgent email, saved to ~/Drafts/email_replies_{date}/.
Give me a summary of what's waiting.
```

---

## Feature 6: Customize

**What it is:** Customize lets you configure how Cowork behaves — globally or per-project. This includes plugins (bundles of skills, connectors, and sub-agents for specific roles or teams), default instructions, connector permissions, and notification preferences.

**Plugins explained:** A plugin packages everything Claude needs for a specific workflow — tools it can call, connectors it's authorized to use, sub-agents it can spin up — into one installable unit. Your IT team or Anthropic's marketplace provides them.

---

### Real-World Example 19 — Setting Up a Sales Team Plugin

**Scenario:** A sales operations manager sets up Cowork for their 12-person team. Every rep needs Claude to access Salesforce, draft outreach from templates, and follow legal-approved language.

**Customize setup:**
- Install the Salesforce plugin (connector + CRM query skills)
- Add global instructions: *"Always use approved legal language from ~/Templates/legal_approved.txt. Never promise delivery dates not confirmed in Salesforce."*
- Set default output folder: `~/CRM_outputs/`

Every rep on the team gets the same guardrails without configuring anything individually.

---

### Real-World Example 20 — A Researcher's Personal Cowork Setup

**Scenario:** A data scientist customizes Cowork for their personal workflow.

**Customize setup:**
- **Instructions:** *"I work in Python and R. Prefer pandas over raw CSV parsing. Output data files as .parquet unless I say otherwise. Explain statistical choices briefly when you make them."*
- **Connectors authorized:** Google Scholar (via MCP), local Python environment, GitHub
- **Notifications:** Ping Slack when any task over 10 minutes completes

Now every task Claude runs respects those preferences without being told each time.

---

### Real-World Example 21 — Enterprise Compliance Guardrails

**Scenario:** A compliance officer at a financial firm sets Cowork up for their legal team.

**Customize:**
- **Instructions:** *"Never write to any folder outside ~/Legal/approved_outputs/. Do not access external URLs not on the approved domain list. Always append 'DRAFT — NOT LEGAL ADVICE' to every document."*
- **Restricted connectors:** Only internal Confluence and approved document repositories
- **Plugin:** Internal document classification plugin that tags every output with data sensitivity level

---

## Putting It All Together: An End-to-End Workflow

**Scenario:** You're a solo consultant preparing a monthly client report package.

| Step | Feature Used | What Happens |
|------|-------------|--------------|
| 1 | **Project** | Open the "ClientCo" project — instructions and memory already loaded |
| 2 | **Scheduled Task** | Runs every 1st of month at 7 AM — pulls raw data from CRM, analytics, and finance folder |
| 3 | **Live Artifact** | Your "ClientCo Dashboard" is already current — open it for a quick status check |
| 4 | **Dispatch** | From your phone on the train: *"Draft the monthly report narrative using last month's data"* — desktop runs it while you commute |
| 5 | **New Task** | Back at your desk: *"Review the draft, add a risks section, export as PDF and PowerPoint"* |
| 6 | **Customize** | Client-specific formatting rules apply automatically throughout — no reminders needed |

---

## Decision Guide: Which Feature to Reach For

| Situation | Feature |
|-----------|---------|
| You have a one-off task, you're here at your desk | **New Task** |
| The work belongs to a longer-running engagement | **Projects** |
| You do the same thing every week/month | **Scheduled Tasks** |
| You need a live view you'll check repeatedly | **Live Artifacts** |
| You're about to go offline but want work running | **Dispatch** |
| You want Claude to always behave a certain way | **Customize** |

---

## Quick Reference: Constraints to Know

| Constraint | Detail |
|-----------|--------|
| Desktop must stay open | Tasks, Dispatch, and Scheduled Tasks pause if the app closes or the machine sleeps |
| Storage is local only | Projects and Live Artifacts live on your machine — no cloud sync, no sharing between teammates (Team/Enterprise) |
| Token usage | Cowork tasks consume more tokens than chat — complex multi-hour tasks use significantly more |
| Plans required | All Cowork features need Pro, Max, Team, or Enterprise |
| Dispatch mobile access | Pro and Max plans only |
| Live Artifacts | Available on Pro, Max, Team, Enterprise via Claude Desktop |

---

Sources:
- [Get started with Claude Cowork — Claude Help Center](https://support.claude.com/en/articles/13345190-get-started-with-claude-cowork)
- [Use live artifacts in Claude Cowork — Claude Help Center](https://support.claude.com/en/articles/14729249-use-live-artifacts-in-claude-cowork)
- [Organize your tasks with projects in Claude Cowork — Claude Help Center](https://support.claude.com/en/articles/14116274-organize-your-tasks-with-projects-in-claude-cowork)
- [The Three Modes of Claude Cowork: Dispatch, Scheduled Tasks, and Live Artifacts](https://techysurgeon.substack.com/p/the-three-modes-of-claude-cowork)
- [Claude Cowork Live Artifacts: From Static Report to Living Dashboard](https://medium.com/@richardhightower/claude-cowork-live-artifacts-from-static-report-to-living-dashboard-544561169d2a)
