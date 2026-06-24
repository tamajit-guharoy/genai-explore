# Multi-Agent Systems — Collaboration & Shared Memory

> **Goal**: Build systems of multiple Letta agents that collaborate, share
> knowledge, and divide work — from simple pairs to complex hierarchies.

---

## 1. Why Multi-Agent?

Single agents hit limits:
- **Context saturation** — one agent can't know everything
- **Role confusion** — hard to be both creative AND rigorous
- **Sequential bottlenecks** — one agent does one thing at a time

Multi-agent patterns solve these by **dividing responsibilities** across
specialized agents that communicate.

## 2. Pattern 1 — Writer/Reviewer Pair

The simplest multi-agent pattern: one agent creates, the other critiques.

```python
from letta_client import Letta
import os

client = Letta(api_key=os.environ["LETTA_API_KEY"])

# ── Create the Writer agent ──────────────────────────────────────
writer = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "You are working for a tech startup that needs content.",
            "limit": 2000
        },
        {
            "label": "persona",
            "value": (
                "I am Draft, a content writer. "
                "I write first drafts — blogs, emails, docs, social posts. "
                "My style: clear, engaging, technically accurate. "
                "I don't self-critique heavily — that's the reviewer's job."
            ),
            "limit": 3000
        }
    ]
)

# ── Create the Reviewer agent ────────────────────────────────────
reviewer = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "human",
            "value": "You are reviewing content for a tech startup.",
            "limit": 2000
        },
        {
            "label": "persona",
            "value": (
                "I am Review, a critical editor. "
                "I find issues others miss: factual errors, unclear writing, "
                "bad structure, missing edge cases. "
                "I provide SPECIFIC, ACTIONABLE feedback. "
                "I maintain a checklist: accuracy, clarity, completeness, tone."
            ),
            "limit": 3000
        }
    ]
)

print(f"Writer:   {writer.id}")
print(f"Reviewer: {reviewer.id}")
```

```python
# ── The workflow pipeline ────────────────────────────────────────

def writer_reviewer_workflow(topic: str) -> dict:
    """
    Writer creates content → Reviewer critiques → Writer revises.
    
    Returns: {draft, review, final}
    """
    
    # Step 1: Writer creates first draft
    print("✍️  Writer creating draft...")
    draft_response = client.agents.messages.create(
        writer.id,
        input=f"Write a 3-paragraph blog post about: {topic}. "
              f"Target audience: technical founders."
    )
    
    draft = ""
    for msg in draft_response.messages:
        if hasattr(msg, 'content') and msg.content:
            draft += (msg.content if isinstance(msg.content, str) else str(msg.content))
    
    print(f"   Draft: {len(draft)} chars")
    
    # Step 2: Reviewer critiques
    print("🔍 Reviewer analyzing...")
    review_response = client.agents.messages.create(
        reviewer.id,
        input=(
            f"Review this blog post draft. Check for: factual accuracy, "
            f"clarity, structure, tone (is it right for technical founders?), "
            f"and completeness. Provide specific, numbered feedback.\n\n"
            f"DRAFT:\n{draft}"
        )
    )
    
    review = ""
    for msg in review_response.messages:
        if hasattr(msg, 'content') and msg.content:
            review += (msg.content if isinstance(msg.content, str) else str(msg.content))
    
    print(f"   Review: {len(review)} chars")
    
    # Step 3: Writer revises based on feedback
    print("✍️  Writer revising...")
    revision_response = client.agents.messages.create(
        writer.id,
        input=(
            f"Here is reviewer feedback on your draft. "
            f"Revise the draft addressing ALL feedback points.\n\n"
            f"FEEDBACK:\n{review}\n\n"
            f"ORIGINAL DRAFT:\n{draft}"
        )
    )
    
    final = ""
    for msg in revision_response.messages:
        if hasattr(msg, 'content') and msg.content:
            final += (msg.content if isinstance(msg.content, str) else str(msg.content))
    
    print(f"   Final: {len(final)} chars")
    
    return {"draft": draft, "review": review, "final": final}

# Run the workflow
result = writer_reviewer_workflow(
    "Why developer experience (DX) is the next competitive moat for SaaS companies"
)

print("\n" + "="*60)
print("FINAL BLOG POST:")
print("="*60)
print(result["final"][:800])
```

## 3. Pattern 2 — Shared Archival Memory (Knowledge Base)

Multiple agents share the SAME archival memory — one agent's
discoveries become available to all others.

```python
# ── Create a shared knowledge base ───────────────────────────────
# In Letta V1, archival memory is per-agent. To share, we create a
# "librarian" agent that owns the knowledge base, and other agents
# can query it through the librarian.

librarian = client.agents.create(
    model="openai/gpt-4o-mini",
    embedding="openai/text-embedding-3-small",
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "I am the Knowledge Librarian. "
                "I maintain the shared knowledge base. "
                "Other agents can ask me to store or retrieve information. "
                "I always search archival memory before answering."
            ),
            "limit": 3000
        }
    ]
)

print(f"Librarian agent: {librarian.id}")

# Seed the shared knowledge base
shared_knowledge = [
    {
        "text": "Company PTO policy: 25 days/year, accrues monthly, "
                "max carryover 5 days. Unlimited sick days. "
                "Remote-work eligible with manager approval.",
        "metadata": {"category": "HR", "topic": "PTO"}
    },
    {
        "text": "Tech stack: Frontend (React 19 + TypeScript), "
                "Backend (Go 1.24 + gRPC), DB (PostgreSQL 17 + Redis), "
                "Infra (Kubernetes on GKE, Terraform, GitHub Actions CI/CD).",
        "metadata": {"category": "Engineering", "topic": "tech_stack"}
    },
    {
        "text": "Q3 OKRs: (1) Launch EU region (deadline Aug 15), "
                "(2) Reduce p99 latency by 40% (target: <200ms), "
                "(3) Achieve SOC 2 Type II certification (audit Oct 1).",
        "metadata": {"category": "Strategy", "topic": "OKRs"}
    },
    {
        "text": "On-call rotation: Week 1 Alice (primary) / Bob (secondary), "
                "Week 2 Charlie / Diana, Week 3 Eve / Frank. "
                "Escalation: page → Slack #oncall → call CTO if no response in 15min.",
        "metadata": {"category": "Engineering", "topic": "oncall"}
    },
]

for item in shared_knowledge:
    client.agents.passages.create(
        librarian.id,
        text=item["text"],
        metadata=item["metadata"]
    )

print(f"Seeded shared knowledge base with {len(shared_knowledge)} passages")
```

```python
def query_shared_knowledge(question: str) -> str:
    """
    Query the shared knowledge base via the librarian agent.
    
    The librarian searches archival memory and returns relevant information.
    """
    response = client.agents.messages.create(
        librarian.id,
        input=(
            f"Question from another agent: {question}\n\n"
            f"Search the knowledge base and provide the most relevant information. "
            f"Be concise — just give the facts."
        )
    )
    
    answer = ""
    for msg in response.messages:
        if hasattr(msg, 'content') and msg.content:
            answer += (msg.content if isinstance(msg.content, str) else str(msg.content))
    
    return answer

# Another agent queries the shared knowledge
questions = [
    "What's our Q3 OKRs?",
    "Who's on call this week?",
    "What's our tech stack?",
]

for q in questions:
    print(f"\n❓ {q}")
    answer = query_shared_knowledge(q)
    print(f"📚 {answer[:300]}")
```

## 4. Pattern 3 — Parallel Research Agents

Spawn multiple agents to research different aspects simultaneously:

```python
import concurrent.futures

def create_researcher(name: str, focus: str):
    """Create a specialized research agent."""
    return client.agents.create(
        model="openai/gpt-4o-mini",
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "persona",
                "value": (
                    f"I am {name}, researching {focus}. "
                    f"I provide structured, evidence-backed analysis. "
                    f"I note sources and confidence levels."
                ),
                "limit": 3000
            }
        ]
    )

def research_topic(agent_id: str, topic: str) -> str:
    """Ask a researcher agent to analyze a topic."""
    response = client.agents.messages.create(
        agent_id,
        input=(
            f"Research and analyze: {topic}\n\n"
            f"Provide a structured analysis with:\n"
            f"1. Key findings (3-5 bullet points)\n"
            f"2. Market numbers if applicable\n"
            f"3. Key players/competitors\n"
            f"4. Risks and opportunities\n"
            f"5. Recommendation"
        )
    )
    
    result = ""
    for msg in response.messages:
        if hasattr(msg, 'content') and msg.content:
            result += (msg.content if isinstance(msg.content, str) else str(msg.content))
    return result

# Parallel research — 3 agents, 3 topics, simultaneously
print("Spawning 3 research agents in parallel...")

research_tasks = [
    ("Vector Databases Market", "market size and trends for vector databases in 2026"),
    ("AI Coding Assistants", "competitive landscape of AI coding tools (Copilot, Cursor, Codex, etc.)"),
    ("LLM Inference Costs", "trends in LLM inference pricing and self-hosting economics"),
]

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    # Create researchers
    researcher_futures = {
        executor.submit(create_researcher, name, focus): (name, focus)
        for name, focus in research_tasks
    }
    
    researchers = {}
    for future in concurrent.futures.as_completed(researcher_futures):
        name, focus = researcher_futures[future]
        agent = future.result()
        researchers[name] = agent.id
        print(f"  ✓ Created: {name} ({agent.id})")
    
    # Research in parallel
    research_futures = {
        executor.submit(research_topic, researchers[name], topic): name
        for name, topic in research_tasks
    }
    
    results = {}
    for future in concurrent.futures.as_completed(research_futures):
        name = research_futures[future]
        results[name] = future.result()
        print(f"  ✓ Completed: {name}")

print(f"\nAll research complete! {len(results)} reports generated.")

# Show a snippet from each
for name, report in results.items():
    print(f"\n{'='*60}")
    print(f"RESEARCH: {name}")
    print(f"{'='*60}")
    print(report[:400])
```

## 5. Pattern 4 — Supervisor/Worker Hierarchy

A supervisor agent delegates tasks to specialized workers and
synthesizes their results.

```python
# ── Create specialist workers ────────────────────────────────────

analyst = client.agents.create(
    model="openai/gpt-4o-mini",
    memory_blocks=[{
        "label": "persona",
        "value": "I am a Data Analyst. I extract insights from data, find trends, and quantify findings. I think in numbers.",
        "limit": 2000
    }]
)

engineer = client.agents.create(
    model="openai/gpt-4o-mini",
    memory_blocks=[{
        "label": "persona",
        "value": "I am a Software Engineer. I assess technical feasibility, estimate effort, and identify architectural risks.",
        "limit": 2000
    }]
)

writer_agent = client.agents.create(
    model="openai/gpt-4o-mini",
    memory_blocks=[{
        "label": "persona",
        "value": "I am a Technical Writer. I turn complex analysis into clear, actionable documents with executive summaries and detailed appendices.",
        "limit": 2000
    }]
)

# ── Supervisor ───────────────────────────────────────────────────
supervisor = client.agents.create(
    model="openai/gpt-4o-mini",
    memory_blocks=[
        {
            "label": "persona",
            "value": (
                "I am a Project Supervisor. I coordinate specialists "
                "to produce comprehensive deliverables. I do NOT do "
                "the work myself — I delegate and synthesize. "
                f"My team IDs: Analyst={analyst.id}, Engineer={engineer.id}, "
                f"Writer={writer_agent.id}"
            ),
            "limit": 4000
        },
        {
            "label": "worker_outputs",
            "value": "",
            "limit": 10000,
            "description": "Outputs from specialist workers. Append each worker's output here for synthesis."
        }
    ]
)

specialists = {
    "analyst": analyst.id,
    "engineer": engineer.id,
    "writer": writer_agent.id
}

print("Team assembled!")
print(f"  Supervisor: {supervisor.id}")
for role, agent_id in specialists.items():
    print(f"  {role}: {agent_id}")
```

```python
def ask_specialist(role: str, question: str) -> str:
    """Delegate a question to a specialist and return their answer."""
    agent_id = specialists[role]
    response = client.agents.messages.create(agent_id, input=question)
    
    answer = ""
    for msg in response.messages:
        if hasattr(msg, 'content') and msg.content:
            answer += (msg.content if isinstance(msg.content, str) else str(msg.content))
    return answer

def supervisor_synthesis(task: str) -> str:
    """
    Full supervisor workflow:
    1. Decompose task into specialist questions
    2. Query each specialist
    3. Synthesize into final deliverable
    """
    print(f"📋 Task: {task}\n")
    
    # Step 1: Supervisor decomposes the task
    print("🧠 Supervisor decomposing task...")
    decomposition = client.agents.messages.create(
        supervisor.id,
        input=(
            f"Decompose this task into specific questions for each specialist:\n"
            f"TASK: {task}\n\n"
            f"Output format:\n"
            f"ANALYST: <question about data, metrics, trends>\n"
            f"ENGINEER: <question about feasibility, architecture, risks>\n"
            f"WRITER: <question about structure, audience, narrative>"
        )
    )
    
    # Extract decomposed questions
    decomp_text = ""
    for msg in decomposition.messages:
        if hasattr(msg, 'content') and msg.content:
            decomp_text += (msg.content if isinstance(msg.content, str) else str(msg.content))
    
    # Step 2: Query specialists (simplified — extract questions via LLM)
    print("🔍 Querying specialists...")
    analyst_q = f"Analyze the business impact of: {task}. Focus on market size, timelines, and ROI."
    engineer_q = f"Assess the technical feasibility of: {task}. Focus on architecture, risks, and effort."
    writer_q = f"Outline the narrative structure for a report about: {task}. Consider audience and key messages."
    
    analyst_report = ask_specialist("analyst", analyst_q)
    print(f"  ✓ Analyst done ({len(analyst_report)} chars)")
    
    engineer_report = ask_specialist("engineer", engineer_q)
    print(f"  ✓ Engineer done ({len(engineer_report)} chars)")
    
    writer_report = ask_specialist("writer", writer_q)
    print(f"  ✓ Writer done ({len(writer_report)} chars)")
    
    # Step 3: Synthesize
    print("🔄 Supervisor synthesizing...")
    synthesis = client.agents.messages.create(
        supervisor.id,
        input=(
            f"Synthesize these specialist reports into one executive summary:\n\n"
            f"=== ANALYST REPORT ===\n{analyst_report[:1000]}\n\n"
            f"=== ENGINEER REPORT ===\n{engineer_report[:1000]}\n\n"
            f"=== WRITER REPORT ===\n{writer_report[:1000]}\n\n"
            f"SYNTHESIS REQUIREMENTS:\n"
            f"1. One-paragraph executive summary\n"
            f"2. Key numbers and timelines\n"
            f"3. Top 3 risks\n"
            f"4. Recommended next steps"
        )
    )
    
    final = ""
    for msg in synthesis.messages:
        if hasattr(msg, 'content') and msg.content:
            final += (msg.content if isinstance(msg.content, str) else str(msg.content))
    
    return final

# Run the full workflow
final_report = supervisor_synthesis(
    "Evaluate whether we should migrate our PostgreSQL database from AWS RDS to Google Cloud SQL to align with the rest of our GCP infrastructure"
)

print("\n" + "="*60)
print("FINAL EXECUTIVE SUMMARY:")
print("="*60)
print(final_report[:1000])
```

## 6. Pattern 5 — Debate/Tournament (LLM-as-Judge)

Two agents argue opposing positions, a third judges:

```python
def create_debate_agent(position: str, stance: str) -> str:
    """Create an agent with a specific debate stance."""
    agent = client.agents.create(
        model="openai/gpt-4o-mini",
        memory_blocks=[{
            "label": "persona",
            "value": (
                f"I am arguing {position}. My stance: {stance}. "
                f"I present the STRONGEST possible case for my position. "
                f"I use evidence, logic, and compelling examples. "
                f"I acknowledge valid counterpoints but refute them."
            ),
            "limit": 3000
        }]
    )
    return agent.id

# The debate topic
topic = "Should software engineers learn to write prompts as a core skill, or rely on AI tools becoming more intuitive?"

# Create debaters
pro_id = create_debate_agent("FOR", "Learning prompt engineering is essential — it's the new 'learning to code'")
con_id = create_debate_agent("AGAINST", "Tools will abstract prompting away — focus on domain expertise and system design")
judge_id = create_debate_agent("JUDGE", "I evaluate arguments objectively and declare a winner with reasoning")

def debate_round(round_num: int, topic: str) -> dict:
    """Run one round of debate."""
    print(f"\n═══ ROUND {round_num} ═══")
    
    # Pro argues
    pro_response = client.agents.messages.create(
        pro_id,
        input=f"Round {round_num}: Make your strongest argument for: {topic}"
    )
    pro_arg = ""
    for msg in pro_response.messages:
        if hasattr(msg, 'content') and msg.content:
            pro_arg += (msg.content if isinstance(msg.content, str) else str(msg.content))
    print(f"  👍 FOR: {pro_arg[:200]}...")
    
    # Con argues (and sees pro's argument)
    con_response = client.agents.messages.create(
        con_id,
        input=(f"Round {round_num}: Rebut this argument against {topic}:\n"
               f"{pro_arg[:500]}")
    )
    con_arg = ""
    for msg in con_response.messages:
        if hasattr(msg, 'content') and msg.content:
            con_arg += (msg.content if isinstance(msg.content, str) else str(msg.content))
    print(f"  👎 AGAINST: {con_arg[:200]}...")
    
    return {"pro": pro_arg, "con": con_arg}

# Run 2 rounds
rounds = [debate_round(i, topic) for i in range(1, 3)]

# Judge decides
print("\n═══ JUDGMENT ═══")
debate_transcript = "\n\n".join([
    f"ROUND {i+1}:\nFOR: {r['pro'][:500]}\nAGAINST: {r['con'][:500]}"
    for i, r in enumerate(rounds)
])

judgment_response = client.agents.messages.create(
    judge_id,
    input=(f"Judge this debate on: {topic}\n\n{debate_transcript}\n\n"
           f"DECLARE A WINNER with specific reasoning. Score each side on: "
           f"evidence quality, logical consistency, persuasiveness.")
)

verdict = ""
for msg in judgment_response.messages:
    if hasattr(msg, 'content') and msg.content:
        verdict += (msg.content if isinstance(msg.content, str) else str(msg.content))

print(f"🏆 VERDICT:\n{verdict[:800]}")

# Cleanup debaters
# for agent_id in [pro_id, con_id, judge_id]:
#     client.agents.delete(agent_id)
```

## 7. Multi-Agent Best Practices

| Do | Don't |
|----|-------|
| Give each agent a CLEAR, NARROW role | Create one "do everything" agent |
| Use shared archival for knowledge | Copy-paste context between agents |
| Explicitly define communication format | Assume agents will coordinate naturally |
| Have a supervisor synthesis step | Let workers talk directly (noise) |
| Use concurrency for parallel work | Run sequential when parallel is possible |
| Clean up agents after use | Leave abandoned agents accumulating cost |

### When NOT to use multi-agent:
- Simple Q&A (single agent is faster and cheaper)
- Tasks requiring tight consistency (agents can diverge)
- Real-time/low-latency requirements (orchestration adds overhead)
- Budget-constrained projects (N agents = N × cost)

## Key Takeaways

1. **Writer/Reviewer** is the simplest effective multi-agent pattern.
2. **Shared archival memory** via a librarian agent enables knowledge sharing.
3. **Parallel research** with ThreadPoolExecutor speeds up multi-topic analysis.
4. **Supervisor/Worker** hierarchy is the most flexible pattern for complex tasks.
5. **Clean up agents** — they persist and consume resources until deleted.

→ Next: `07_advanced_patterns.ipynb` — agent types, compaction, templates, sleep-time.
