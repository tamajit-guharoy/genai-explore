---
created: 2026-06-01
tags: [dashboard, projects]
---

# Project Dashboard

> Auto-generated project overview. Updates live as project notes change.

## Active Projects

```dataview
TABLE status, priority, due, owner, Completion
FROM "projects"
WHERE status = "active"
SORT priority ASC
```

## All Projects (by Status)

```dataview
TABLE status, priority, due, owner, Completion
FROM "projects"
SORT status ASC, priority ASC
```

## Overdue Tasks

```dataview
TASK
FROM "projects"
WHERE !completed AND due <= date(today)
SORT due ASC
```

## Summary

- **Active projects**: `$= dv.pages('"projects"').where(p => p.status == "active").length`
- **Completed this month**: `$= dv.pages('"projects"').where(p => p.completed_date && dv.date(p.completed_date).month == dv.date("now").month).length`
- **Total projects**: `$= dv.pages('"projects"').length`
