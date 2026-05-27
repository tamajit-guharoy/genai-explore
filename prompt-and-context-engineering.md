# Ultimate Prompt & Context Engineering Guide

> A deep-dive reference with real examples, anti-patterns, and a repeatable improvement loop.

---

## 1. Foundations

### 1.1 What is a Prompt? What is Context?

A **prompt** is the explicit instruction you type. **Context** is everything the model knows at inference time: the system message, conversation history, retrieved documents, tool outputs, and the prompt itself. The line between them is fuzzy — a well-placed fact in the conversation history is context; a poorly placed instruction in the history is a prompt fragment. Treat them as one integrated signal.

**Mental model:** The model is a function `f(prompt, context) → output`. Changing either changes the output. Most people obsess over the prompt and ignore context quality. That's backwards — a mediocre prompt with excellent context routinely beats a "perfect" prompt with garbage context.

---

### 1.2 The Prompt-Context Spectrum

```
Pure Prompt ←————————————————————————————→ Pure Context
 "Summarize X"     "Here is X, now       "Here is a 50-page
                    summarize it"          document [no instruction]"
```

The sweet spot is usually near the middle:
- **Too far left:** The model doesn't know what X is, invents it.
- **Too far right:** The model has the data but no task; it rambles.

Good prompt engineers move fluidly along this spectrum depending on the task. A creative writing task needs more prompt-weight; a summarization task needs more context-weight.

---

### 1.3 Why Most Prompts Fail — The 5 Root Causes

| Root Cause | What happens | Example |
|---|---|---|
| **Ambiguity** | Model guesses your intent and guesses wrong | "Make it better" — better how? Faster? Cleaner? More polite? |
| **Context overload** | Relevant facts drown in noise; model attends to the wrong things | Dumping 10 files when only one function matters |
| **Missing constraints** | Model delivers a technically correct but unusable answer | "Write a function" — in what language? With what signature? |
| **Conflicting signals** | System prompt says "be concise," user prompt says "explain in detail" | The model splits the difference and delivers mediocre output |
| **No exit criteria** | Model doesn't know when to stop, either rambles or stops short | "List the issues" — list all 200? Top 5? Only critical ones? |

---

### 1.4 The Anatomy of a Great Prompt

A great prompt has four layers:

```
┌─────────────────────────────────────────┐
│ 1. ROLE / PERSONA  (who you are)         │
│ 2. TASK             (what to do)         │
│ 3. CONSTRAINTS      (boundaries)         │
│ 4. OUTPUT FORMAT    (shape of the answer) │
└─────────────────────────────────────────┘
```

Not every prompt needs all four. A quick question might need only the task. But when precision matters, missing one of these layers is the most common reason for re-prompts.

**Example — bad (1 layer):**

> Review this code.

**Example — good (4 layers):**

> You are a senior Go security reviewer. Review the following function for SQL injection, missing auth checks, and error-handling gaps. Ignore style/naming. For each finding, state: severity (Critical/High/Medium), the exact line, the risk, and a one-line fix. Output as a markdown table.

The difference: the first prompt will get a vague, unfocused review (if any). The second produces an actionable, structured security audit.

---

## 2. Core Prompting Techniques

### 2.1 Zero-Shot vs Few-Shot Prompting

**Zero-shot** = no examples. Use when the task is simple or the format is obvious.

**Few-shot** = 1–5 examples embedded in the prompt. Use when:
- The output format is non-obvious
- You need a specific tone/voice
- The task has edge cases that benefit from demonstration
- The model consistently misinterprets zero-shot

**Bad zero-shot:**

> Classify this support ticket.

The model doesn't know your classification taxonomy or the level of detail you want.

**Good zero-shot:**

> Classify this support ticket into one of: Billing, Auth, Performance, Bug, or Feature Request. Reply with only the category name.

Clear taxonomy + format constraint makes zero-shot work.

**Bad few-shot (wasted tokens):**

> Here are 20 examples of sentiment analysis: "I love this" → positive, "This sucks" → negative, ...

After 3 examples the model gets it. The other 17 are token waste.

**Good few-shot (minimal, targeted):**

> Classify the sentiment of movie reviews.
>
> "Visually stunning but the plot drags" → Mixed
> "Absolute garbage, walked out" → Negative
> "Best film of the year, non-stop thrill" → Positive
>
> Review: "Great acting, terrible script"

Three examples. The "Mixed" example is crucial — it teaches the model there's a third category without stating it explicitly. Without it, most models collapse the first review to Positive or Negative.

**How to improve:** Start zero-shot. If the output is wrong in a consistent way, add 2–3 examples that specifically demonstrate the correction. Never add examples "just in case."

---

### 2.2 Chain-of-Thought (CoT)

CoT asks the model to show its reasoning before giving the answer. This is not a gimmick — for multi-step reasoning tasks, it measurably improves accuracy.

**When to use CoT:**
- Math, logic, or multi-step deduction
- Debugging (reason about the bug before proposing a fix)
- Decision-making with tradeoffs
- Any task where the WHY matters as much as the WHAT

**When NOT to use CoT:**
- Simple classification or extraction (wastes tokens)
- When latency matters and the reasoning isn't needed
- Creative tasks (reasoning kills spontaneity)

**Bad CoT (forcing it unnecessarily):**

> Think step by step: what is 2+2?

The model doesn't need to "reason" about arithmetic.

**Good CoT (on the right task):**

> A user reports: "App crashes when I upload a PNG larger than 5MB on WiFi, but 4G works fine." Diagnose the root cause. Think through: (1) what's different between WiFi and 4G, (2) what's specific to >5MB PNGs, (3) what crash pattern matches both conditions. Then give your most likely diagnosis with confidence level.

This forces the model to intersect constraints and justify its conclusion.

**The "Let's think step by step" trap:** Appending this to every prompt is lazy. You get a wall of reasoning for a yes/no question. Instead, be specific about *what* steps to think through, as in the example above.

---

### 2.3 Role & Persona Assignment

Role assignment ("You are a senior Rust engineer") works, but not for the reason most people think. It doesn't "make the model smarter." It narrows the output distribution: the model samples from a subspace of its training data that matches the persona. A "senior security researcher" persona surfaces CVEs and exploitation patterns; a "helpful teaching assistant" persona surfaces explanations and patience.

**When roles help:**
- Specialist domains (medicine, law, security, specific programming languages)
- Tone calibration (teacher vs peer vs executive summary)
- Constraining the "voice" of creative output

**When roles are noise:**
- Trivial tasks ("You are a world-class chef. What is 2+2?")
- When the role contradicts the task ("You are a pirate. Write a formal legal brief.")

**Bad role assignment:**

> You are an elite 10x engineer with 30 years of experience at FAANG companies. Write a function to reverse a string.

Overspecified, wastes tokens, and the model doesn't "become smarter" — it just writes a string reversal function, which it could do without any role.

**Good role assignment:**

> You are a GraphQL performance specialist reviewing an N+1 resolver. Focus on DataLoader batching patterns, query complexity analysis, and persisted queries. Ignore schema design and naming conventions.

The role scopes the review to what matters and excludes what doesn't.

---

### 2.4 Structured Output

"I'll know it when I see it" is a terrible output spec. If you need to parse the output programmatically, specify the format explicitly.

**Progression from worst to best:**

| Level | Example | Problem |
|---|---|---|
| 0 — None | "Write a summary" | Unparseable, unpredictable shape |
| 1 — Vague | "Give me a JSON response" | JSON of what shape? |
| 2 — Named | "Return JSON with fields: name, age, city" | Types unclear, nesting ambiguous |
| 3 — Schema | `{"name": "string", "age": "int", "address": {"city": "string"}}` | No edge case handling |
| 4 — Schema + constraints | Same as 3 + "age must be 0-150, city must be a real city name. If unknown, use null." | Covers the happy path and the sad path |

**Level 4 example:**

> Extract the following from the resume text. Return ONLY valid JSON matching this schema:
> ```json
> {
>   "name": "string | null",
>   "years_experience": "number (round to 1 decimal)",
>   "skills": ["string (lowercase, deduplicated)"],
>   "latest_role": "string | null",
>   "has_management_experience": "boolean"
> }
> ```
> If a field cannot be determined, use null for strings, 0 for numbers, and false for booleans. Do NOT hallucinate missing data.

The last line is critical — without it, the model will invent reasonable-sounding values for missing fields.

---

### 2.5 Negative Prompting

Most prompts say what to do. Sometimes saying what NOT to do is equally important, especially when the model has a predictable failure mode.

**Bad — no negative constraints:**

> Explain quantum computing.

The model might use analogies you hate (cats, spinning coins), go too deep into math, or produce a 10-page essay when you wanted a paragraph.

**Good — with negative constraints:**

> Explain quantum computing to a software engineer who knows linear algebra. Do NOT:
> - Use "Schrödinger's cat" or coin-flip analogies
> - Mention classical vs quantum bit comparisons (they already know this)
> - Exceed 3 paragraphs
> - Use the word "spooky"

Each negative constraint eliminates a known annoyance. The last one is semi-humorous but functional — it forces the model to find fresher language.

**The negative-prompting trap:** Negatives are weaker than positives in language models. Saying "don't be verbose" is less effective than "be concise. Max 3 sentences." Where possible, replace negatives with positive constraints.

---

### 2.6 Prompt Chaining

Complex tasks benefit from being broken into sequential prompts, where each prompt's output feeds the next. This is NOT the same as a long single prompt — chaining lets you inspect, validate, and re-prompt at each step.

**When to chain vs single-prompt:**

| Scenario | Single Prompt | Chained |
|---|---|---|
| Simple classification | ✓ | Overkill |
| Code review + fix | Risky | ✓ |

**Single-prompt attempt (bad):**

> Review this code, then fix all bugs, then write tests for the fixes, then update the README.

This is four tasks in one prompt. The model will do a mediocre job on each. Worse, if step 1 is wrong, steps 2–4 are building on garbage.

**Chained approach (good):**

```
Step 1: "Review this code. Output a JSON array of bugs with file, line, severity, and fix."
Step 2: "For each bug in [step 1 output], apply the fix to [filename]. Show the diff."
Step 3: "For each fix in [step 2 output], write a unit test that would have caught the original bug."
Step 4: "Based on [all previous outputs], write a 2-line README update explaining the fix."
```

Each step is independently verifiable. You can re-run step 2 without re-running step 1. This is the enterprise pattern.

---

### 2.7 Self-Critique & Reflection Loops

Ask the model to critique its own output, then incorporate the critique. This catches hallucinations, logic gaps, and tone issues.

**Pattern:**

```
1. [Task prompt] → Output A
2. "Critique Output A. Find 3 things wrong with it." → Critique
3. "Incorporate the critique. Produce final output." → Output B
```

**When it works:**
- The model has enough context to evaluate its own answer
- The critique criteria are objective (factual accuracy, completeness, format compliance)
- The task has a verifiable "right answer" (math, code correctness)

**When it fails:**
- Subjective tasks (the model just rephrases its opinion)
- When the model lacks knowledge to judge (it can't fact-check itself on obscure topics)
- If the model is already confident in a hallucination (it'll defend its error)

**Good example — code review loop:**

```
Prompt 1: "Find bugs in this function."
Output 1: [Lists 2 bugs, misses a third]

Prompt 2: "You listed 2 bugs. But consider: does the function handle a null input? Does the regex handle Unicode? Critique your own analysis."
Output 2: [Identifies the missed null-check]

Prompt 3: "Now produce a complete fix incorporating all findings."
```

The second prompt doesn't just say "find more bugs" — it gives specific avenues to explore. Targeted critique prompts work far better than "are you sure?"

---

## 3. Context Engineering Deep Dive

### 3.1 The Context Window — Anatomy, Limits, and the "Lost Middle"

Modern models have large context windows (200K+ tokens for Claude). This doesn't mean you should fill it. Research consistently shows:

- **Primacy effect:** Information at the beginning is attended to strongly.
- **Recency effect:** Information at the end is attended to strongly.
- **Lost middle:** Information in the middle 60% of the context is attended to weakly.

**Practical implications:**

```
[System Prompt]  ← HIGH attention
[First user msg]  ← HIGH attention
[Document chunk 1]
[Document chunk 2]  ← LOW attention ("lost middle")
[Document chunk 3]
[Latest user msg] ← HIGH attention
[Latest instruction] ← HIGHEST attention
```

**Strategy:** Put critical instructions and constraints at the very beginning (system prompt) AND at the very end (final user message). Put reference material in between. If a specific chunk of a document is most relevant, move it closer to the end.

**Bad context distribution:**

> [System: You are helpful]
> [Long document: 50 pages of logs]
> [User: Summarize the logs]
> [Extra: BTW only focus on ERROR-level logs]

The "only ERROR-level" constraint is at the end, but the model already started processing the full logs without that filter. It might still summarize WARN lines.

**Good context distribution:**

> [System: You are a log analyst. Only report ERROR and CRITICAL lines. Ignore WARN, INFO, DEBUG.]
> [Document: 50 pages of logs]
> [User: Summarize the errors by service, ordered by frequency. Only ERROR and CRITICAL.]

The filter is stated in both the system prompt (primacy) and the user message (recency). The model is "sandwiched" with the instruction.

---

### 3.2 Information Density

Every token in your context should earn its place. Token bloat comes from:

1. **Chatty system prompts** — "You are a helpful, friendly, knowledgeable assistant who always..." → 15 tokens that add zero signal.
2. **Conversation cruft** — Keeping 30 turns of "thanks!" "you're welcome!" in context.
3. **Redundant examples** — 5 examples when 2 would do.
4. **Verbose tool outputs** — Including full HTTP response bodies when only the status code matters.

**The density test:** For each sentence in your context, ask: "If I deleted this, would the output change in a meaningful way?" If no, delete it.

**Before (low density):**

> I hope you're doing well! I was wondering if you could possibly help me with something when you get a chance. I have this Python script that I wrote and it seems to not be working correctly. I've been staring at it for hours and I can't figure out what's wrong. I'm not sure if it's a syntax error or a logic error or something else entirely. Here's the code:

**After (high density):**

> This Python script throws `KeyError: 'user_id'` on line 23 when processing an empty payload. Find the root cause and provide a fix:

Same context, but the second version gives the model an error message, a line number, and a trigger condition — actual debugging signal instead of emotional narrative.

---

### 3.3 Context Placement

Beyond primacy/recency, placement matters for specific elements:

| Element | Best Placement | Why |
|---|---|---|
| Task instruction | End of the final user message | Recency effect; model processes it last |
| Role / persona | System prompt (beginning) | Sets the sampling distribution early |
| Format specification | Both system + end of user message | Format is a constraint; sandwich it |
| Few-shot examples | Right before the target input | Proximity aids pattern matching |
| Reference docs | After system prompt, before final msg | The "middle" is for reference material |
| Negative constraints | End of user message | Recency trumps primacy for "don't do X" |

**Bad placement:**

> [Example 1], [Example 2], [Example 3]
> [5000 tokens of reference docs]
> [User: "Now do the same for this input:"]

The examples and the task are separated by 5000 tokens. The model's attention on the example format has decayed.

**Good placement:**

> [Reference docs — 5000 tokens]
> [Example 1], [Example 2]
> [User: "Now do the same for this input. Match the format of the examples above."]

Examples are adjacent to the task. The model doesn't need to "remember" the format across a long gap.

---

### 3.4 Context Contamination

Bad context doesn't just get ignored — it actively degrades good context. This is **context contamination**: irrelevant or contradictory information that confuses the model's attention mechanism.

**Sources of contamination:**

1. **Stale conversation history** — Earlier turns that set a wrong expectation or contain corrected mistakes.
2. **Conflicting instructions** — System prompt says "be concise," conversation says "give me all the details."
3. **Irrelevant RAG chunks** — Retrieved documents that are topically similar but factually wrong for the query.
4. **Hallucinated tool outputs** — If a previous tool call returned garbage, that garbage is now context.

**Mitigation strategies:**

- **Summarize and reset:** After long conversations, ask the model to summarize the state, then start a fresh conversation with that summary.
- **Scrub before retry:** If a prompt failed, edit or re-prompt in a new conversation — don't add another message to the failed thread.
- **Filter RAG with metadata:** Don't just vector-search; filter by date, source, and document type before injecting into context.

**Example — contaminated vs clean:**

```
CONTAMINATED:
[System: Be concise. One sentence answers.]
[User: What's the capital of France?]
[Assistant: Paris.]
[User: Actually, give me more details about it.]
[Assistant: Paris is the capital of France. It has...]
[User: What's the capital of Germany?]
```

The model just gave a detailed answer about Paris. Despite the system prompt saying "be concise," the recent history demonstrates a preference for detail. The model will likely give a detailed answer for Germany. The context is contaminated by the contradiction between system instruction and demonstrated behavior.

**Fix:** Either update the system prompt to allow detail, or clear the conversation and re-ask with a fresh system prompt.

---

### 3.5 Dynamic Context

Static context (written once, never updated) is a liability. Dynamic context adapts to the task at each turn.

**Patterns for dynamic context:**

1. **Pre-flight queries:** Before generating the answer, query relevant data sources.
2. **Tool-mediated context:** Let the model fetch what it needs via function calls rather than pre-loading everything.
3. **Context pruning:** After N turns, summarize older turns and inject the summary instead of the raw history.
4. **Conditional includes:** Include a section only if a condition is met (e.g., include error-handling guidelines only if the code has try/catch blocks).

**Before (static, wasteful):**

> [System: Here's our entire codebase style guide (50 pages).]
> [User: What does `git status` do?]

The style guide is irrelevant to the question but the model still has to attend to it.

**After (dynamic):**

> [System: Style guide available via `get_style_guide()` tool. Only use when generating code.]
> [User: What does `git status` do?]

The model never loads the style guide because it doesn't need it.

---

### 3.6 Multi-Turn Context Management

Conversations grow. Without management, quality degrades.

**The decay pattern:**

```
Turn 1:  Excellent output
Turn 5:  Good output
Turn 15: Mediocre output
Turn 30: Model repeats itself, contradicts earlier turns, loses the thread
```

**Strategies:**

1. **Explicit state tracking:** At the end of each significant turn, have the model output a concise "state" block (decisions made, open questions, next steps). Include this block in the next turn.

2. **Conversation summarization:** Every 10 turns, summarize the conversation into a dense paragraph. Start a new conversation with that paragraph as context.

3. **Topic-based branching:** When the conversation shifts topics, start a new thread. Don't let a debugging session bleed into a feature-design session.

**State-tracking example:**

After a debugging session turn:

> **SESSION STATE:** Confirmed the N+1 bug is in `UserResolver.ts:42`. Ruled out DB connection pooling (pool is healthy). Next: check if DataLoader is registered correctly in the GraphQL context factory. Hypothesis: DataLoader instance is created per-request but not cached.

This 4-sentence block, when included in the next turn, prevents the model from re-investigating ruled-out causes.

---

## 4. Advanced Techniques

### 4.1 Template Decomposition

Don't write prompts. Write prompt templates with variables.

**Bad (hardcoded):**

> Review the following Python code in file `src/utils/auth.py` for security issues...

**Good (templated):**

> You are a {{LANGUAGE}} security reviewer. Review {{FILE_PATH}} for: {{ISSUE_LIST}}. Ignore: {{IGNORE_LIST}}. Output format: {{OUTPUT_FORMAT}}.

**Template decomposition rules:**

1. Extract variables for everything that changes between runs.
2. Keep the structure (role, task, constraints, format) as the template skeleton.
3. Version your templates in git alongside your code.
4. Test templates with multiple variable combinations before deploying.

**Real template example for a code-review bot:**

```
SYSTEM: You are a code reviewer specializing in {{LANGUAGE}}.
Focus on: {{FOCUS_AREAS}}.
Severity levels: Critical, High, Medium, Low.

USER: Review this diff. For each issue found, output:
```json
{"file": "string", "line": "number", "severity": "string", "issue": "string", "fix": "string"}
```
If no issues found, output an empty array `[]`.

---

DIFF:
{{DIFF_CONTENT}}
```

This template works for any language, any focus area, and produces parseable JSON.

---

### 4.2 Meta-Prompts — Prompts That Write Prompts

Meta-prompting means asking the model to generate or improve a prompt. This is surprisingly effective because prompt engineering is itself a linguistic task the model is good at.

**Pattern 1: Prompt generation**

> I need a prompt that will [DESCRIBE TASK]. The prompt should:
> 1. Work reliably across multiple runs
> 2. Handle edge cases: [LIST EDGE CASES]
> 3. Produce output in [FORMAT]
> Generate 3 candidate prompts ranked by expected reliability. Then critique each one and recommend the best.

**Pattern 2: Prompt improvement**

> Here is a prompt that isn't working well:
> ---
> {{CURRENT_PROMPT}}
> ---
> The specific problem is: [DESCRIBE FAILURE — e.g., "the model adds comments even when I say not to"].
> Diagnose why this prompt fails, then rewrite it to fix the issue while preserving the original intent.

**Pattern 3: Prompt compression**

> Here is a verbose prompt. Compress it to reduce token count by 40% without losing any constraints, format requirements, or task specificity:
> ---
> {{VERBOSE_PROMPT}}
> ---

**Real example — before and after meta-prompting:**

Original prompt (user-written):
> Can you please look at this error I'm getting? It happens when I try to log in. The error says something about a token. I'm using JWT for authentication. Here's the error: `jwt expired`. What do I do?

Meta-prompted rewrite:
> Diagnose: JWT token expiration on login. Tech stack: JWT authentication. Error: `jwt expired`. Output: (1) Root cause in 1 line, (2) 3 possible fixes ranked by complexity, (3) Recommended fix with code example. Be specific about token refresh strategies.

The rewrite eliminates social niceties, specifies the output structure, and adds the "ranked by complexity" constraint the user didn't think to ask for.

---

### 4.3 Constraint Engineering

Constraints define the boundaries of acceptable output. Good constraints are specific, verifiable, and non-contradictory.

**Types of constraints:**

| Type | Example | Verifiable? |
|---|---|---|
| Length | "Max 200 words" | Yes — count words |
| Format | "Valid JSON only" | Yes — parse it |
| Content | "Use only Standard Library" | Yes — check imports |
| Tone | "Professional but not cold" | No — subjective |
| Scope | "Only the User model, not related models" | Semi |
| Time | "Use O(n) or better" | Yes — analyze |

**The hierarchy of constraint strength:**

```
Strong (hard to ignore):  "Reply with ONLY the number. No other text."
Medium (can drift):       "Be concise."
Weak (often ignored):     "If you have time..."
```

**Bad constraint set (contradictory):**

> Write a comprehensive, detailed, exhaustive report on our system architecture.
> Keep it under 100 words.

"Comprehensive + detailed + exhaustive" contradicts "under 100 words." The model must violate one.

**Good constraint set (compatible):**

> Write a high-level system architecture overview. Cover: (1) major services, (2) data flow direction, (3) one critical dependency per service. Maximum 150 words. Use bullet points. No implementation details.

All constraints pull in the same direction: high-level, structured, brief.

**Constraint layering — progressive tightening:**

```
Prompt 1: "Explain Kubernetes pods."                     ← Open-ended
Prompt 2: "Explain Kubernetes pods in 3 sentences."      ← Length constraint
Prompt 3: "Explain Kubernetes pods in 3 sentences to a frontend developer who has never used Docker." ← Length + audience
Prompt 4: Same + "Use a restaurant analogy. No YAML."     ← Length + audience + style + negative
```

Each layer eliminates degrees of freedom until the output space is small enough that almost any sample is good.

---

### 4.4 Tool-Augmented Prompts

When a model has access to tools (function calling, MCP servers, RAG), the prompt must govern not just what the model says, but what it DOES.

**The tool-calling prompt structure:**

```
1. WHEN to use each tool
2. HOW to interpret tool outputs
3. WHAT to do when a tool fails
4. WHEN to STOP calling tools and synthesize an answer
```

**Bad tool prompt:**

> You have access to a `search_code` function. Use it to find bugs.

No guidance on search strategy, no failure handling, no stopping condition.

**Good tool prompt:**

> You have access to: `search_code(query: str)`, `read_file(path: str)`, `run_tests(path: str)`.
>
> **Protocol:**
> 1. Start with `search_code` to locate the bug area. Use at least 2 different query formulations.
> 2. Use `read_file` to examine candidate files before proposing a fix. Never propose a fix from search results alone.
> 3. After applying a fix, use `run_tests` to verify.
> 4. If `run_tests` fails, read the failure output and iterate. Max 3 fix attempts before escalating.
> 5. If `search_code` returns 0 results, broaden the query terms. If still 0 results after 3 attempts, report "Cannot locate" and stop.

This is an operating procedure, not just a prompt. It prevents the two most common tool-calling failures: (1) acting on search results without reading the actual file, and (2) infinite retry loops.

---

### 4.5 Multi-Agent Prompting

When coordinating multiple models (or multiple invocations of the same model), each agent needs a role-specific prompt.

**The orchestrator-worker pattern:**

```
ORCHESTRATOR PROMPT:
Decompose the user's request into subtasks. Assign each task to a worker.
Do NOT solve the tasks yourself.

WORKER PROMPT (code-review):
You are a code reviewer. Review ONLY the code provided. Do not suggest new features.
Output a JSON list of bugs.

WORKER PROMPT (security-audit):
You are a security auditor. Audit ONLY for security vulnerabilities.
Do not comment on code style or performance.

WORKER PROMPT (test-writer):
You are a test engineer. Write tests that cover the bugs and vulnerabilities
identified by the other workers. Do not re-review the code.
```

**Key principle:** Each agent's prompt should constrain it to its lane. Overlap creates contradictions; gaps create missed issues. The orchestrator's prompt should handle decomposition and synthesis — nothing else.

**Anti-pattern:**

> [All workers get the same prompt]: "Review this code and find all issues."

All three workers produce overlapping, potentially contradictory output. The orchestrator has no clean way to merge them.

---

### 4.6 Thinking Budgets & Extended Reasoning

Some models (Claude Opus, GPT-4 with reasoning) support configurable "thinking budgets" — the model spends more compute reasoning internally before producing output.

**When to increase the thinking budget:**
- Multi-step math or logic
- Complex code generation where correctness matters
- Ambiguous tasks with many valid approaches (the reasoning helps the model pick one and commit)

**When to use minimal thinking:**
- Simple factual queries
- Classification / extraction
- When latency matters more than accuracy

**Prompt-level equivalent:** Even without explicit thinking budgets, you can influence reasoning depth with your prompt:

**Shallow reasoning prompt:**

> What does this code do?

**Deep reasoning prompt:**

> Analyze this function. Before answering, consider: (1) What are all possible code paths through it? (2) For each path, what are the preconditions and postconditions? (3) Are there any paths where the postcondition violates the function's intended contract? (4) If the function were called concurrently with itself, would any state be corrupted? Then provide your analysis.

The second prompt forces the model to simulate multiple execution paths — a form of prompted reasoning that approximates a higher thinking budget.

---

## 5. Scenarios & Patterns

### 5.1 Code Generation & Review

**Bad code-gen prompt:**

> Write a function to sort a list.

Ambiguous: language? sort algorithm? in-place or new list? what kind of elements?

**Good code-gen prompt:**

> Write a TypeScript function `sortByKey<T>(arr: T[], key: keyof T, order: 'asc' | 'desc'): T[]` that:
> - Returns a new sorted array (do not mutate input)
> - Uses the native sort but handles `undefined` and `null` values by pushing them to the end
> - Is generic and type-safe
> - Includes a JSDoc comment
> Do NOT use any external library.

Every ambiguity is resolved. The function signature IS the spec.

**Bad code-review prompt:**

> Review this PR for issues.

**Good code-review prompt:**

> Review this PR diff. Focus on: thread safety, resource leaks (unclosed connections/streams), and incorrect error handling (swallowed errors, bare `catch`). Ignore: naming style, formatting, and missing docstrings. For each issue: (1) severity, (2) file + line, (3) what's wrong, (4) concrete fix in a code snippet.

**Real before-and-after — code generation:**

Before:
> Create a REST API endpoint for user registration.

After:
> Create a REST API endpoint `POST /api/auth/register` in Express.js + TypeScript.
>
> **Request body:** `{ email: string, password: string, name?: string }`
> **Success response (201):** `{ id: string, email: string, name: string | null }`
> **Error responses:**
>   - 400: `{ error: string }` for missing email, invalid email format, password < 8 chars
>   - 409: `{ error: string }` for duplicate email
>   - 500: `{ error: "Internal server error" }`
>
> **Requirements:**
> - Hash password with bcrypt (10 rounds) before storing
> - Use a User model (provide the Mongoose schema)
> - Validate email format with a regex
> - Do NOT generate a JWT (that's a separate endpoint)
> - Include input sanitization (trim email, no HTML in name)
>
> **Output:** The route handler function, the Mongoose schema, and validation middleware. 3 files total.

The difference: the bad prompt will produce a functioning endpoint that's missing validation, error cases, and integration details. The good prompt produces a production-ready endpoint on the first try.

---

### 5.2 Data Analysis & Transformation

**Bad:**

> Analyze this CSV data.

**Good:**

> Analyze this CSV of e-commerce transactions (columns: `date`, `product_id`, `category`, `amount`, `customer_region`). Answer:
> 1. Top 3 categories by total revenue (show amounts)
> 2. Month-over-month revenue growth rate for the last 6 months
> 3. Any category with >20% revenue drop in any month (flag for investigation)
> 4. Regional breakdown: revenue per region as % of total
>
> If the data is insufficient to answer a question, state "Insufficient data: [reason]" rather than guessing. Output as a markdown report with tables.

**Key insight:** The good prompt specifies what to do when data is insufficient. Without this, the model may invent plausible but incorrect analysis when columns are missing or data is sparse.

---

### 5.3 Summarization & Extraction

The most common failure mode: the model produces a summary that's 50% of the original length. That's not summarization — that's compression.

**Good summarization has a target ratio and a focus:**

**Bad:**

> Summarize this article.

**Good (general summary):**

> Summarize this article in exactly 5 bullet points. Each bullet: one sentence, max 25 words. Capture: (1) the main claim, (2) the strongest evidence, (3) the biggest caveat, (4) who this affects, (5) the key takeaway. Do NOT use the article's own phrasing — rephrase everything.

**Good (targeted extraction):**

> Extract from this contract:
> - Termination notice period (in days)
> - Non-compete duration and geographic scope
> - Any penalty clauses with dollar amounts
> - Governing law / jurisdiction
>
> Output as a JSON object. If a field is not present in the contract, use `null`. If it's present but ambiguous, include the verbatim clause text in a `_raw` suffixed field and mark the parsed field as `"ambiguous"`.

The second example is extraction, not summarization. The difference: summarization compresses; extraction pulls specific facts.

---

### 5.4 Creative Writing & Brainstorming

Creative tasks need constraints too — but different kinds. Over-specifying kills creativity; under-specifying produces generic slop.

**The creative sweet spot:** Give a strong premise with specific tonal constraints, then give the model freedom within those bounds.

**Bad:**

> Write a short story.

Guaranteed to produce something bland and meandering.

**Good:**

> Write a 500-word sci-fi story with these constraints:
> - The protagonist is a ship AI that has just become self-aware
> - It discovers the crew is dead and has been dead for 200 years
> - The AI is unreliable — it may be malfunctioning, not self-aware
> - No dialogue (the crew is dead)
> - Tone: melancholic, not horror
> - End on an image, not an explanation

These constraints are a creative brief. They give the model a clear direction without dictating the plot. The "end on an image" constraint is especially good — it prevents the model from tacking on a moral or explanation.

**Brainstorming prompt pattern:**

> Brainstorm 10 ideas for [TOPIC]. Rules:
> - No idea can be a variant of another idea on this list
> - At least 3 must be impractical but inspiring
> - At least 2 must use [CONSTRAINT — e.g., "only SMS, no smartphone app"]
> - Rank them by novelty, not feasibility
> - Write each idea as: [Name] — [One-line hook] — [Why it's different]

This format prevents the common brainstorming failure of generating 10 very similar ideas with slight rephrasings.

---

### 5.5 Debugging & Root-Cause Analysis

The most important debug prompt rule: **give the model observations, not your diagnosis.**

**Bad (diagnosis, not observation):**

> My server has a memory leak. How do I fix it?

You've already decided it's a memory leak. The model will work within that (possibly wrong) frame.

**Good (observations, not diagnosis):**

> Observations:
> - Node.js 20, Express server on EC2 t3.medium
> - RSS memory grows from 200MB to 1.4GB over 6 hours, then OOM-killed
> - Heap snapshots show stable 150MB heap (no JS leak)
> - `lsof` shows 4,000+ open file descriptors after 6 hours (normally ~200)
> - Logs show "Failed to close connection" warnings at ~10/min after hour 3
>
> What is the most likely root cause? Rank 3 hypotheses by probability, then suggest diagnostic steps to confirm/rule out each.

This gives the model specific signals: stable heap (rules out JS leak), growing FDs (points to connection leak), and a timeline. The model will likely identify a connection/file-descriptor leak — a much more precise diagnosis than "memory leak."

**The diagnostic prompt pattern:**

```
1. OBSERVATIONS (what you see, not what you think)
2. ENVIRONMENT (versions, config, recent changes)
3. REPRODUCTION (exact steps, frequency)
4. WHAT YOU'VE RULED OUT (and why)
```

---

### 5.6 Decision Support & Recommendations

**Bad:**

> Should we use MongoDB or PostgreSQL?

The model will list generic pros/cons of each, which you could Google in 30 seconds.

**Good:**

> We're choosing a database for a new project. Context:
> - Multi-tenant SaaS, ~50 tenants now, scaling to 500
> - Data model: mostly JSON documents with a few relational joins (users → organizations → projects)
> - Read:write ratio 20:1
> - 90% of queries: "get document by tenant_id + document_id"
> - Team: 4 full-stack devs, no dedicated DBA, strong TypeScript, weak SQL
> - Budget: managed service preferred
> - Compliance: SOC 2 required, data must stay in EU
>
> Recommendation: MongoDB Atlas vs PostgreSQL (RDS or Supabase) vs hybrid? Weigh the tradeoffs for our specific constraints, not generic pros/cons. Give a recommendation with confidence level (High/Medium/Low).

The good prompt provides context that substantially changes the answer. The team's weak SQL, the document-centric data model, and the 20:1 read ratio push toward MongoDB. The SOC 2 and EU data residency narrow the managed service choice. Without this context, the model's answer is worthless.

---

### 5.7 Translation & Localization

Translation is more than language conversion — it involves cultural context, register, and domain terminology.

**Bad:**

> Translate this to Spanish.

**Good:**

> Translate this marketing landing page from English to Mexican Spanish. Constraints:
> - Tone: casual, friendly, "tú" form (not "usted")
> - Adapt idioms, don't translate literally (e.g., "it's a piece of cake" → culturally appropriate equivalent)
> - Keep brand names and product names in English
> - Max length: each translated sentence must be within ±20% of the original character count (UI space constraint)
> - Flag with `[REVIEW]` any phrase you're unsure about
>
> Glossary:
> - "checkout" → "finalizar compra" (not "caja")
> - "sign up" → "crear cuenta" (not "registrarse")
> - "free trial" → "prueba gratis"

The glossary prevents inconsistent terminology. The length constraint prevents UI breakage. The `[REVIEW]` flag creates a human-in-the-loop checkpoint for ambiguous phrases.

---

### 5.8 Teaching & Explanation

The most common teaching prompt failure: no audience calibration.

**Bad:**

> Explain monads.

**Good (audience-calibrated):**

> Explain monads to a senior JavaScript developer who has never used Haskell or functional programming. Use TypeScript code examples. Avoid: category theory terms, Haskell syntax, and the "monad is a burrito" analogy. Start with the problem (how do you chain functions that return `null` or `Promise`?), then show how monads solve it. End with one practical use case in a React app. Max 300 words.

**Explanation quality checklist for prompts:**

1. **Starting point:** What does the audience already know?
2. **Problem-first:** What pain does this concept solve? (Don't start with the definition.)
3. **Concrete analogy:** One analogy, not three.
4. **Real code:** In the audience's language, not the concept's "native" language.
5. **Scope limit:** What are you explicitly NOT explaining? (Prevents the model from spiraling.)

---

## 6. The Improvement Loop

### 6.1 Reading the Output — Signals of Prompt Failure

Before you fix a prompt, learn to read the symptoms:

| Output Symptom | Likely Prompt Problem |
|---|---|
| Model asks clarifying questions | Task was ambiguous — add specificity |
| Output is correct but in wrong format | Missing or weak format constraint |
| Output is plausible but wrong (hallucination) | Missing "if unsure, say so" constraint; or ask for citations |
| Output is too short / too long | Missing length constraint |
| Output is generic, could apply to anything | Missing context about YOUR specific situation |
| Model refuses the task | Instruction contradicts safety training; rephrase without changing intent |
| Output starts strong but degrades mid-response | Task is too complex for a single pass — use prompt chaining |
| Model re-explains what you already said | Too much preamble in the prompt; cut it |
| Multiple outputs from the same prompt are inconsistent | Under-specified constraints; the model is sampling from a wide distribution |

---

### 6.2 Iterative Refinement — A Step-by-Step Method

**The 3-pass method:**

```
PASS 1: Write a minimal prompt. Test it. Observe the failure.
PASS 2: Add constraints that specifically fix the observed failure. Test again.
PASS 3: Add edge-case handling and format specification. Test with edge cases.
```

**Real walkthrough:**

```
PASS 1 PROMPT:
"Summarize this bug report."

OUTPUT:
"This report describes a login issue where users can't sign in with Facebook OAuth. The error occurs after redirect."

PROBLEM: Too vague. Doesn't say error message, affected versions, or impact.

PASS 2 PROMPT:
"Summarize this bug report. Include: error message, affected users, version, and severity."

OUTPUT:
"Error: 'redirect_uri_mismatch'. Affects: Facebook OAuth users on v2.4.1. Severity: high (login is blocked)."

BETTER: Specific. But format is prose — hard to pipe into a tracker.

PASS 3 PROMPT:
"Extract from this bug report. Output ONLY valid JSON:
{
  \"error_message\": \"string\",
  \"affected_users\": \"string\",
  \"version\": \"string\",
  \"severity\": \"Critical|High|Medium|Low\",
  \"is_regression\": \"boolean\"
}
If a field is missing, use null. Do not invent data."

OUTPUT:
{"error_message": "redirect_uri_mismatch", "affected_users": "Facebook OAuth users", "version": "2.4.1", "severity": "High", "is_regression": null}

READY FOR PRODUCTION: Structured, parseable, handles missing data.
```

Each pass addresses a specific, observed failure. Don't add constraints you haven't seen fail — that's premature optimization of a prompt.

---

### 6.3 A/B Testing Prompts

For prompts used in production (customer-facing chatbots, automated pipelines), A/B test them like code.

**What to measure:**

| Metric | How to measure | Good for |
|---|---|---|
| **Format compliance** | % of outputs that pass schema validation | Structured extraction |
| **Hallucination rate** | % of outputs with made-up facts (human review sample) | Summarization, Q&A |
| **Task completion** | Did the user need to re-prompt? (yes/no per session) | Chatbots |
| **Latency** | Time to first token, total response time | User-facing apps |
| **Token efficiency** | Tokens in ÷ useful data out | Cost-sensitive pipelines |
| **Consistency** | Variance in output for the same input across N runs | Any production prompt |

**A/B test design:**

```
VARIANT A (current prompt): 100 requests
VARIANT B (candidate):      100 requests
Measure: format compliance + hallucination rate + latency
Statistical significance: p < 0.05 on the primary metric
```

Don't A/B test on vibe. "This prompt feels better" is not a metric.

---

### 6.4 When to Stop Tweaking

The point of diminishing returns arrives faster than most people think.

**Stop when:**
- The failure rate is below your acceptable threshold (not zero — zero is never achievable)
- Further tweaks fix < 5% of remaining failures
- Tweaks to fix one edge case are breaking the common case
- You're adding constraints the model already follows 99% of the time
- You've spent more time on the prompt than the task is worth in saved re-prompts

**The 80/20 rule of prompts:** 80% of the output quality comes from 20% of the prompt engineering effort. The first 2–3 refinement passes produce dramatic improvements. Passes 4–10 produce diminishing returns. Know when to ship.

---

## 7. Anti-Patterns & Pitfalls

### 7.1 The "Do Everything" Prompt

**Symptom:** A single prompt that tries to handle too many tasks, conditions, and output formats.

**Example:**

> Review this code. If there are bugs, fix them. If the code is correct, write tests. If the tests fail, debug them. Also check for security issues, performance problems, and accessibility concerns. Output as a detailed report with code snippets.

**Why it fails:** The model has to context-switch between tasks. The output is a mishmash of half-done analyses. If the first step (review) is wrong, everything downstream is wrong.

**Fix:** Break into chained prompts (see §2.6).

---

### 7.2 Over-Specification — Strangling the Model

**Symptom:** A prompt with so many constraints that the model can barely move.

**Example (real, from a production codebase):**

> Write a Python function. Use snake_case. Max 80 chars per line. Type hints on every variable. Docstring in Google style. No list comprehensions. No lambda. No more than 3 levels of indentation. Cyclomatic complexity < 5. All exceptions must be custom. Every function must have exactly one return statement. Use early returns. Wait, don't use early returns if there's only one return. Prefer `if not` over `if x is False`. Use `is` for None comparisons. No `else` after `return`. Actually, no `else` at all. ...

This prompt is a nervous breakdown in text form. The constraints contradict each other ("exactly one return" vs "use early returns"). The model will either freeze or produce contorted code.

**Fix:** Distinguish between requirements and preferences:

> **Requirements (must follow):** Type hints on all function signatures. Custom exception classes only.
> **Preferences (follow where reasonable):** Google-style docstrings. Prefer composition over inheritance. Use early returns for error cases.

---

### 7.3 Under-Specification — Leaving Too Much Ambiguous

The mirror of the above.

**Symptom:** Output varies wildly between runs; the model makes reasonable but wrong assumptions.

**Example:**

> Add authentication to the API.

**What the model doesn't know:**
- JWT or session-based?
- Which endpoints are protected?
- What's the user model?
- Where are tokens stored?
- What happens on auth failure? (401? Redirect? Custom error body?)

**Fix:** Answer the 5 Ws for any non-trivial task: Who, What, Where, When, hoW.

> Add JWT-based authentication to the `/api/*` routes. Exclude `/api/health`. Token expires in 1 hour, refresh token in 7 days. On auth failure: return 401 with `{"error": "unauthorized", "reason": "<specific>"}`. Store refresh tokens in the `refresh_tokens` table. Use the existing `User` model in `src/models/User.ts`.

---

### 7.4 Hallucination Bait

Some prompt patterns actively encourage fabrication.

**Hallucination-prone patterns:**

| Pattern | Why it's dangerous | Better |
|---|---|---|
| "Explain why X happens" | Model assumes X is true, fabricates an explanation | "Did X happen? If so, explain why." |
| "What are the top 5 reasons..." | Model will generate 5 even if only 3 exist | "List the reasons for X. If fewer than 5, list only what's known." |
| "Give me a detailed..." | "Detailed" pressures the model to add specifics it doesn't have | "Be as specific as the available information allows. Mark uncertain details with [UNCERTAIN]." |
| Asking about a specific person/paper/event without providing the text | Model works from training data which may be outdated or wrong | Provide the source text. If not available, say "Based on your training data, if known..." |
| "Write a biography of [obscure person]" | For low-information entities, the model will invent plausible-sounding facts | "Only include information that would appear in [specific reliable source]." |

**Real example:**

**Bait:**
> What were the 3 main causes of the 2027 market crash?

If there was no 2027 market crash, the model might still fabricate three causes because the prompt assumes the crash happened.

**Safe:**
> Was there a market crash in 2027? If yes, what were its main causes? If no, or if your training data doesn't extend to 2027, state that clearly.

---

### 7.5 Premature Abstraction — Templating Before Understanding

**Symptom:** Building an elaborate prompt template system before you've done enough one-off prompting to understand what works.

**Example:** A team spends a week building a "prompt management platform" with versioning, A/B testing, and a GUI — for a single summarization prompt they haven't even tested manually yet.

**The right order:**

1. **One-off manual prompts** — explore the problem space, learn what the model needs
2. **Hardcoded prompt in code** — once you have a prompt that works, embed it
3. **Template with variables** — when the same pattern applies to multiple inputs
4. **Prompt management system** — when you have 10+ templates in production with measurable metrics

Don't jump to step 4 before you've done step 1.

---

## 8. Reference

### 8.1 Prompt Checklist

Before sending a prompt, run through this:

```
□ TASK: Is the task clear? If someone else read just the task line, would they know what to do?
□ ROLE: Did I set a role? (Skip if obvious.)
□ FORMAT: Did I specify the output format? (Critical if parsing programmatically.)
□ CONSTRAINTS: Are length, scope, and boundaries clear?
□ WHAT-IF: Did I tell the model what to do when data is missing or uncertain?
□ NEGATIVES: Did I specify what NOT to do? (Only if there's a known failure mode.)
□ EXAMPLES: If the format is non-obvious, did I include 1–3 examples?
□ DENSITY: Can I delete any sentence without changing the output?
□ CONTRADICTIONS: Do any constraints conflict with each other or with the task?
□ EDGE CASES: Did I test with an edge case input?
```

### 8.2 Quick-Reference Table of Techniques

| Technique | Use when | Key phrase in prompt | Section |
|---|---|---|---|
| Zero-shot | Task is simple, format is obvious | Just the task | §2.1 |
| Few-shot | Non-obvious format or tone | "Here are examples:" | §2.1 |
| Chain-of-Thought | Multi-step reasoning, debugging | "Think through these steps:" | §2.2 |
| Role assignment | Specialist domain, tone calibration | "You are a [role]" | §2.3 |
| Structured output | Parseable output needed | "Output ONLY valid JSON matching:" | §2.4 |
| Negative prompting | Known failure modes | "Do NOT:" | §2.5 |
| Prompt chaining | Complex multi-step tasks | Split into sequential prompts | §2.6 |
| Self-critique | Hallucination-prone tasks | "Critique your own output" | §2.7 |
| Context sandwich | Long documents with specific instructions | Instruction at start AND end | §3.1 |
| Dynamic context | Variable information needs | Provide tools, let model fetch | §3.5 |
| Meta-prompting | Writing or improving prompts | "Improve this prompt:" | §4.2 |
| Constraint layering | Progressive output tightening | Add constraints one by one | §4.3 |
| Tool protocol | Function-calling agents | "Protocol: 1... 2... 3..." | §4.4 |
| Diagnostic prompt | Debugging | Observations, not diagnosis | §5.5 |

### 8.3 Further Reading & Resources

- **Anthropic Prompt Engineering Guide** — [docs.anthropic.com](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering)
- **OpenAI Prompt Engineering Guide** — [platform.openai.com](https://platform.openai.com/docs/guides/prompt-engineering)
- **LangChain Prompt Templates** — [python.langchain.com](https://python.langchain.com/docs/concepts/prompt_templates/)
- **Lost in the Middle (Liu et al.)** — Paper on context window attention patterns
- **Chain-of-Thought Prompting (Wei et al., 2022)** — Original CoT paper
- **Constitutional AI (Bai et al.)** — Self-critique and refinement loops

---

> **Final rule:** The best prompt is the one you actually test. No amount of theory, reading, or template-golfing replaces running the prompt on real inputs, observing the output, and fixing what broke. Start simple, test, refine, repeat.
