---
created: <% tp.date.now("YYYY-MM-DD") %>
tags: [meeting]
attendees: []
date: <% tp.date.now("YYYY-MM-DD") %>
time: <% tp.date.now("HH:mm") %>
duration: 30 min
---

# <% tp.system.prompt("Meeting Title") %>

> **Attendees**: <% tp.system.prompt("Attendees (comma-separated)") %>
> **Date**: <% tp.date.now("YYYY-MM-DD") %> at <% tp.date.now("HH:mm") %>
> **Duration**: <% tp.system.prompt("Duration in minutes", "30") %> minutes

## Agenda

1. 
2. 
3. 

## Notes

## Decisions

> [!important] Decisions Made
> - 

## Action Items

- [ ] Action 1 (Owner: , Due: )
- [ ] Action 2 (Owner: , Due: )
- [ ] Action 3 (Owner: , Due: )

## Related

- 
