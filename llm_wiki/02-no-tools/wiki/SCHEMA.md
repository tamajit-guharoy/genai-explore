# Wiki Schema

## Domain
AI/ML research and tools — architectures, training techniques, AI agents, companies, and key people.

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `transformer-architecture.md`)
- Every wiki page starts with YAML frontmatter (see format below)
- Use `[[wikilinks]]` to link between pages — minimum 1 outbound link per page (aim for 2+)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`
- **Provenance markers:** On pages synthesizing 3+ sources, use `^[raw/...]` markers

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
confidence: high | medium | low  # optional, recommended for opinion-heavy topics
contested: true                  # optional, set when page has unresolved contradictions
---
```

## Tag Taxonomy
- **People & Orgs:** company, person, open-source, lab
- **Technical:** architecture, training, inference, benchmark, technique, data
- **Meta:** concept, comparison, controversy, prediction, timeline

Every tag on a page must come from this taxonomy. Add new tags here first.

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create** for passing mentions or things outside the AI/ML domain
- **Split a page** when it exceeds ~200 lines
- **Archive** when content is fully superseded

## Entity Pages
Include: Overview, key facts, relationships to other entities (`[[wikilinks]]`), source references.

## Concept Pages
Include: Definition, current state of knowledge, open questions, related concepts.

## Comparison Pages
Include: What is being compared and why, dimensions (table format preferred), synthesis, sources.

## Update Policy
When new info conflicts with existing content:
1. Check dates — newer sources generally supersede older
2. If genuinely contradictory, note both positions with dates
3. Mark `contested: true` in frontmatter
4. Flag for review
