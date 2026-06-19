# Shared Sample Raw Sources

> These are sample raw source files used across all approaches in this tutorial.
> Each file follows the raw source convention: YAML frontmatter with `source_url`, `ingested` date, and `sha256` hash.

## Contents

| File | Type | Content |
|---|---|---|
| [articles/ai-agent-landscape-2026.md](articles/ai-agent-landscape-2026.md) | Article | Survey of major AI agents (Claude Code, Codex, Hermes, Manus) |
| [articles/karpathy-llm-wiki-tweet.md](articles/karpathy-llm-wiki-tweet.md) | Article | Karpathy's original LLM Wiki tweet thread |
| [articles/gpt4-technical-report.md](articles/gpt4-technical-report.md) | Article | GPT-4 architecture, capabilities, and agent implications |
| [papers/attention-is-all-you-need.md](papers/attention-is-all-you-need.md) | Paper | The Transformer paper (Vaswani et al., 2017) |
| [transcripts/karpathy-lex-fridman.md](transcripts/karpathy-lex-fridman.md) | Transcript | Karpathy on Lex Fridman: agents, memory, LLM usage |

## Using These Samples

### For Manual Approach (Section 2)
Read these files, then manually create wiki pages following the pattern in [02-no-tools/approach.md](../02-no-tools/approach.md).

### For Agent-Driven (Section 5)
Point your agent at this directory:
```
Ingest all sources in raw/ into my wiki.
```

### For NotebookLM (Section 4)
Upload these files to a notebook and explore before building your wiki.

### For Obsidian (Section 3)
These stay in `raw/` — Obsidian displays them but the agent never edits them.
