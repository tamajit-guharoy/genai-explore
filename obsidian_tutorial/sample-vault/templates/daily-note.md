---
created: <% tp.date.now("YYYY-MM-DD") %>
tags: [daily-notes]
---

# <% tp.date.now("dddd, MMMM Do, YYYY") %>

> Day <% tp.date.now("DDD") %> of <% tp.date.now("YYYY") %> | Week <% tp.date.now("WW") %>

## 🎯 Today's Focus

- [ ] Priority 1
- [ ] Priority 2
- [ ] Priority 3

## 📝 Notes

## 📅 Meetings

```dataview
TABLE WITHOUT ID
  file.link as "Meeting",
  date as "Time",
  duration as "Duration"
FROM "meetings"
WHERE date = date(<% tp.date.now("YYYY-MM-DD") %>)
SORT time ASC
```

## 🔗 Navigation

| ← [[<% tp.date.yesterday("YYYY-MM-DD") %>\|Yesterday]] | [[<% tp.date.tomorrow("YYYY-MM-DD") %>\|Tomorrow →]] |
|---|---|

## 🌙 Evening Reflection

- **What went well today?**
- **What could be improved?**
- **Key takeaway:**
