---
source_url: https://www.youtube.com/watch?v=example-karpathy-lex
ingested: 2026-06-19
sha256: placeholder
---

# Andrej Karpathy on Lex Fridman Podcast — Excerpt

*Transcript excerpt — topics: LLMs, knowledge management, AI agents*

## On How He Uses LLMs (00:12:30)

**Lex:** How has your personal workflow changed with these new models?

**Karpathy:** The biggest shift for me has been using LLMs not just as tools I query, but as agents that do sustained work. I'll give you a concrete example. I've been researching a topic — I won't say which — and I've collected maybe 50 papers, articles, transcripts. In the past, I'd read them, take notes, try to synthesize. It's months of work.

**Lex:** And now?

**Karpathy:** Now I drop them into a folder, point an agent at it, and say "build me a wiki." The agent reads everything, extracts all the entities and concepts, writes interlinked markdown pages, flags contradictions between papers, marks confidence levels. I come back in an hour and I have a navigable knowledge base. I didn't write a single word.

**Lex:** Does that feel like cheating?

**Karpathy:** (laughs) No, it feels like leverage. I'm still the one curating what goes in, I'm still the one verifying the important claims, I'm still the one asking the questions. But I'm not the one doing the mechanical work of summarization and cross-referencing. That's what machines are for.

## On Memory in AI Systems (00:24:15)

**Karpathy:** The thing most people don't appreciate about current AI is how stateless it is. Every conversation starts from zero. The model doesn't remember you. That's going to change.

**Lex:** What does persistent memory unlock?

**Karpathy:** Everything. Imagine an agent that has been working with you for a year. It knows your preferences, your projects, your writing style, your pet peeves. It knows what you've already discussed and doesn't repeat itself. It remembers what approaches failed and why. That's not a chatbot anymore — that's a colleague.

**Lex:** Are we close to that?

**Karpathy:** We're getting there. There are systems now — Hermes Agent, some people's custom setups — that have real persistent memory. SQLite-backed, searchable, summarized into context. It's early but the trajectory is clear. The agent that remembers you will always beat the one that doesn't.

## On the Agent Ecosystem (00:41:00)

**Karpathy:** I think we're going to see a split. There will be the managed agents — Claude Code, Codex — that are polished, fast, and expensive. And there will be the self-hosted agents — Hermes, Open Interpreter — that are more work to set up but give you total control and cost you nothing in API fees beyond the model.

**Lex:** Which do you use?

**Karpathy:** Both, honestly. Claude Code for heavy coding sessions where I want the best reasoning. Hermes Agent for long-running personal automation — daily reports, scheduled tasks, maintaining my knowledge bases. Different tools for different jobs.

**Lex:** Do you think one model will win?

**Karpathy:** No, I think we'll have a portfolio. Just like I use Python and C and JavaScript for different things, I'll use different agents for different tasks. The key is having a standard way to move between them — which is what the agentskills.io standard is trying to do.
