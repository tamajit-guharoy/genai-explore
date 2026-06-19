# Wiki Schema

## Domain
AI/ML research and tools — architectures, training techniques, AI agents, companies, and key people.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter
- Use `[[wikilinks]]` to link between pages — minimum 1 outbound link (aim for 2+)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- On pages synthesizing 3+ sources, use `^[raw/...]` provenance markers

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low
contested: true  # optional
---
```

## Tag Taxonomy
- **People & Orgs:** company, person, open-source, lab
- **Technical:** architecture, training, inference, benchmark, technique, data
- **Meta:** concept, comparison, controversy, prediction, timeline

## Page Thresholds
- Create a page when an entity/concept appears in 2+ sources OR is central to one source
- Add to existing page when already covered
- DON'T create for passing mentions
- Split pages over ~200 lines
- Archive when fully superseded

## Update Policy
When new info conflicts: check dates, note both positions, mark `contested: true`, flag for review.
