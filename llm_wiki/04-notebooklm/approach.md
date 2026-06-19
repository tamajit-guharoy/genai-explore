# Approach 4: NotebookLM — What It Can and Can't Do

> Google's NotebookLM is a powerful RAG tool, but it's not an LLM Wiki builder. Here's an honest assessment of where it fits.

## What NotebookLM Is

NotebookLM is a Google product that lets you upload documents (PDFs, Google Docs, websites, YouTube links, pasted text) and then ask questions about them. It uses Gemini models under the hood with RAG (Retrieval-Augmented Generation) over your uploaded sources.

## What It Does Well

| Capability | How It Works |
|---|---|
| **Source upload** | Drag-and-drop PDFs, paste URLs, link Google Docs |
| **Question answering** | Ask natural language questions; gets answers grounded in your sources |
| **Citation** | Answers include clickable citations to the exact source passage |
| **Audio overviews** | Generates a podcast-style conversation about your sources (2 hosts discussing) |
| **Notebook organization** | Group sources into notebooks by topic |
| **Note-taking** | Save generated answers as notes within the notebook |
| **Suggested questions** | Auto-generates questions based on your sources |
| **Free** | Currently free (subject to change) |

## What It CANNOT Do (The Wiki Gap)

| Wiki Feature | NotebookLM's Limitation |
|---|---|
| **Persistent wiki pages** | No concept of interlinked wiki pages. Notes exist but they're flat — no `[[wikilinks]]`, no structured cross-referencing. |
| **Compound knowledge** | Every question is a fresh RAG query. It doesn't build on previous answers. No accumulation. |
| **Cross-referencing** | Citations are great (source → answer) but there's no entity-to-entity or concept-to-concept linking. |
| **Health checks** | No linting, no contradiction detection, no stale page detection, no orphan detection. |
| **Portability** | Your "knowledge base" lives in NotebookLM's proprietary cloud. Can't export as markdown files. |
| **Agent-driven maintenance** | No API for an agent to write pages. It's a human-in-the-loop Q&A tool. |
| **Custom schema** | No SCHEMA.md. No conventions. No tag taxonomy. The structure is whatever NotebookLM decides. |
| **Index/catalog** | No central index of what's been covered. You can't see "here's everything I know about X." |

## Where NotebookLM Fits in a Wiki Workflow

NotebookLM CAN serve as:

### 1. Discovery Layer (Feed into Wiki)

```
NotebookLM: "What are the main themes across these 10 papers on AI agents?"
           → Get a quick overview, identify key entities/concepts
           → Feed the papers into your LLM Wiki agent
           → Agent builds structured, persistent wiki pages
```

NotebookLM is good for **exploratory Q&A** — "what's in here?" — before committing to a full wiki ingestion.

### 2. Quick-Look Tool (Alongside Wiki)

```
LLM Wiki:      Persistent, structured knowledge that compounds
NotebookLM:    Quick Q&A over a specific document set you don't want to wiki-fy
```

Not every document set deserves a full wiki treatment. For a one-off project with 5 papers, NotebookLM is faster than setting up a wiki structure.

### 3. Audio Overview Generator

NotebookLM's most unique feature: the AI-generated podcast about your sources. You could:
1. Build your wiki with an agent
2. Export key wiki pages to a NotebookLM notebook
3. Generate an audio overview of your wiki's findings
4. Listen while commuting

This is genuinely useful — no other tool does this well.

## Concrete Comparison: 10 Papers on AI Agents

### Using NotebookLM
1. Upload 10 PDFs to a notebook (2 min)
2. Ask: "Compare the approaches to persistent memory across these papers" (30 sec)
3. Get a cited answer — grounded, but isolated. No wiki page is created.
4. Ask: "What does Karpathy say about agents?" (30 sec)
5. Get another cited answer — but no connection to the first answer.
6. **Result:** You have answers to specific questions. No persistent knowledge structure.

### Using LLM Wiki
1. Save 10 papers to `raw/papers/` (2 min)
2. Ask agent: "Ingest all 10 papers" (5–10 min of agent work)
3. Agent creates entity pages for every researcher, company, model mentioned
4. Agent creates concept pages for every technique, idea discussed
5. Agent cross-references everything with `[[wikilinks]]`
6. Agent flags contradictions between papers in frontmatter
7. **Result:** You have a navigable, interlinked wiki. Ask any question and the agent reads the relevant pages (not raw papers).

### Combined Approach
1. Upload to NotebookLM for quick exploration (10 min)
2. Identify the most valuable papers worth wiki-fying
3. Feed those into the LLM Wiki agent
4. Use NotebookLM for ad-hoc questions on the REST of the papers

## NotebookLM + Obsidian

Some users bridge the gap:
1. Use NotebookLM to explore a document set
2. Copy NotebookLM's cited answers into Obsidian as notes
3. Manually add `[[wikilinks]]` between notes
4. Maintain the Obsidian vault going forward

This is essentially the manual approach with NotebookLM as a research assistant. It's better than pure manual but still requires significant human effort to maintain structure.

## Pros and Cons

### Pros
- **Zero setup** — no config, no CLI, no API keys
- **Excellent citations** — every claim is traceable to source
- **Audio overviews** — genuinely unique and useful
- **Free** — at least for now
- **Great for exploration** — "what's in this document set?"

### Cons
- **No persistent structure** — answers are ephemeral; no wiki pages are built
- **No cross-referencing** — connections between concepts are lost between queries
- **No compounding** — 10th query is no better than 1st
- **Proprietary lock-in** — can't export your knowledge graph as files
- **No agent API** — can't automate ingestion or maintenance
- **Scaling ceiling** — uploading 100+ documents gets unwieldy; NotebookLM wasn't designed for that

## Verdict

NotebookLM is a **RAG tool with great UX**, not an LLM Wiki builder. It solves the "what's in these documents?" problem but not the "build me a knowledge base I can read and grow over months" problem.

Use it for:
- Quick exploration before committing to wiki
- Ad-hoc Q&A on document sets you won't return to
- Audio overviews (legitimately great)
- As a discovery layer feeding into your wiki

Don't use it as your primary knowledge base. It won't compound.

---

*Next: [05 — Agent-Driven Approaches](../05-agent-driven/approach.md)*
