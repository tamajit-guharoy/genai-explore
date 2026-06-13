# Cowork Tutorial — Sample Input Files

Sample input files for every example in `co-work.md`. Each folder maps to an example number.
All `.docx`, `.pdf`, `.xlsx`, and `.pptx` files are represented as `.txt` or `.csv` — Cowork handles real binary formats; these are readable stand-ins for demo purposes.

---

## Folder Map

| Folder | Example | Input Files |
|--------|---------|-------------|
| `example1/` | Ex 1: Morning Board Brief | `board_meeting_notes_Q1.txt`, `q2_actuals.csv` |
| `example2/` | Ex 2: Support Triage Report | `support_tickets_export.csv` (40 tickets) |
| `example3/` | Ex 3: Research Paper Backlog | `papers/unread/` — 5 papers (ML in medical imaging) |
| `example4/` | Ex 4: Spreadsheet → Slide Deck | `Q2_actuals.csv` (sales by region and account) |
| `example5/` | Ex 5: Legal Contract Review | `VendorAgreement_Draft.txt` (full vendor agreement) |
| `example6/` | Ex 6: Expense Reconciliation | `june2026_template.csv`, `receipts/` — 7 receipts |
| `example7/` | Ex 7: Client Consulting Workspace | `brand_guidelines.txt`, `contract_scope.txt`, `stakeholder_list.csv` |
| `example8/` | Ex 8: Job Search Workspace | `base_cv.txt`, `jds/` — 3 job descriptions (Stripe, Revolut, Monzo) |
| `example9/` | Ex 9: Newsletter Content Studio | `research/week25/` — 3 saved articles on AI in procurement |
| `example10/` | Ex 10: Personal Finance Tracker | `bank_statement_may.csv` (30 transactions) |
| `example11/` | Ex 11: Weekly Status Report | `ProjectAlpha/` — requirements doc, sprint notes, meeting notes |
| `example12/` | Ex 12: Daily Sales Metrics | `daily_leads.csv` (30 leads with pipeline stats) |
| `example13/` | Ex 13: Monthly Invoice Chase | `invoices/` — 4 invoices (2 unpaid, 1 overdue, 1 paid), `payment_details.txt` |
| `example16/` | Ex 16: Quarterly CV Update | `publications/` — 2 papers, `cv_master.txt`, `short_bio_150w.txt` |
| `example18/` | Ex 18: Freelance Dashboard | `projects/` — 3 client briefs, `time_logs.csv` |
| `example19/` | Ex 19: Founder Dashboard | `priority_contacts.txt`, `kpi_tracker.csv` (6 months of KPIs) |
| `example20/` | Ex 20: Hiring Pipeline | `pipeline.csv` (12 candidates across 6 roles) |
| `example21/` | Ex 21: Grant Deadline Monitor | `tracked_opportunities.csv` (12 grants), `drafts/` — 1 draft |
| `example22/` | Ex 22: Competitor Research (Dispatch) | `competitor_notes/` — 3 competitor files |
| `example23/` | Ex 23: Deck During Meetings (Dispatch) | `Q3_roadmap.csv`, `q2_contributors.txt` |
| `example24/` | Ex 24: Overnight Lit Review (Dispatch) | `papers/to_review/` — 3 papers |
| `example26/` | Ex 26: Pre-Meeting Prep (Dispatch) | `prospects/TechLogistics_notes.txt` |

---

## Notes

- Examples 14, 15, 17, 25 use only MCP connectors (Gmail, Slack, Google Calendar) — no local files needed.
- Examples 27–30 (Customize) are configuration examples — no input files required.
- Replace placeholder paths (e.g., `~/Papers/unread/`) with paths to these folders when running the tutorial prompts.

---

## Quick Start

To try Example 1 in Cowork:
1. Copy `example1/` to your Desktop or a known path
2. Update the prompt paths to match where you saved the files
3. Start a New Task in Cowork and paste the prompt from `co-work.md` Section 4, Example 1
