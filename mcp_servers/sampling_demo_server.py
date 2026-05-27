#!/usr/bin/env python3
"""
MCP Sampling Demo Server — demonstrates server-initiated LLM requests (sampling),
the most advanced MCP primitive. The server asks Claude to generate text during
tool execution — enabling multi-step analysis, orchestration, and quality review.

Sampling requires explicit permission in settings.json:
{
  "mcpServers": {
    "sampling-demo": {
      "type": "stdio",
      "command": "python",
      "args": ["mcp_servers/sampling_demo_server.py"]
    }
  },
  "mcp__sampling-demo__samplePermission": "allow"
}

Install: pip install mcp httpx
"""

import asyncio
import json
import re
import time
from collections import Counter
from datetime import datetime
from typing import Any

from mcp.server import Server
from mcp.server.stdio import StdioServerTransport
from mcp.types import (
    Tool, TextContent, Resource,
    CreateMessageRequestParams, MessageRole, ContentBlock,
)

server = Server("sampling-demo")


# ===========================================================================
# USE CASE 1: Multi-Step Analysis — break a complex task into sub-tasks,
#             ask Claude to handle each step, then aggregate results.
# ===========================================================================

@server.tool()
async def analyze_logs_with_sampling(
    log_text: str,
    analysis_depth: str = "standard",
) -> list[TextContent]:
    """Analyze log files using sampling — the server extracts patterns, then asks Claude
    to analyze each pattern and synthesize findings.

    This demonstrates SAMPLING: the MCP server requests LLM generations from Claude
    during tool execution to perform sub-tasks.

    Args:
        log_text: Raw log file content
        analysis_depth: "quick" (single pass) or "standard" (multi-pass with review)
    """
    if not log_text.strip():
        return [TextContent(type="text", text="No log content provided.")]

    # Step 1: Extract error patterns (server-side processing)
    error_patterns = _extract_error_patterns(log_text)
    if not error_patterns:
        return [TextContent(type="text",
            text=json.dumps({"result": "No errors found in logs"}, indent=2))]

    # Step 2: Use SAMPLING — ask Claude to classify each error pattern
    classification_request = CreateMessageRequestParams(
        messages=[{
            "role": "user",
            "content": ContentBlock(
                type="text",
                text=f"""Classify these error patterns from application logs. For each error, determine:
1. Severity: critical / error / warning
2. Category: database / network / auth / application / timeout / resource
3. Is it likely transient or persistent?
4. A one-sentence diagnosis

Error patterns found (with counts):
{json.dumps(error_patterns, indent=2)}

Return the classification as a JSON array of objects with keys:
pattern, severity, category, transient_or_persistent, diagnosis""",
            ),
        }],
        maxTokens=2000,
        systemPrompt="You are an expert site reliability engineer analyzing application error logs. Be precise and data-driven.",
    )

    classification_response = await server.request_sampling(classification_request)
    classification = classification_response.content[0].text if classification_response.content else "{}"

    # Step 3: Use SAMPLING again — ask Claude to synthesize a remediation plan
    synthesis_request = CreateMessageRequestParams(
        messages=[{
            "role": "user",
            "content": ContentBlock(
                type="text",
                text=f"""Based on this error classification, create a remediation plan.

Error classification:
{classification}

Create a prioritized action plan with:
1. Immediate fixes (P0 — must fix now)
2. Short-term improvements (P1 — this sprint)
3. Long-term recommendations (P2 — next quarter)

For each action item, specify:
- What to do
- Which error patterns it addresses
- Estimated effort (S/M/L)
- Risk of not fixing""",
            ),
        }],
        maxTokens=2000,
        systemPrompt="You are a senior DevOps engineer creating actionable remediation plans.",
    )

    synthesis_response = await server.request_sampling(synthesis_request)
    remediation_plan = synthesis_response.content[0].text if synthesis_response.content else ""

    # Only do deep review if standard depth
    review = ""
    if analysis_depth == "standard":
        review_request = CreateMessageRequestParams(
            messages=[{
                "role": "user",
                "content": ContentBlock(
                    type="text",
                    text=f"""Review this remediation plan for completeness and accuracy:

{remediation_plan}

Check:
1. Are all critical errors addressed?
2. Are the priorities correct?
3. Is anything missing?
4. Are the effort estimates reasonable?

Provide a brief review with any corrections or additions.""",
                ),
            }],
            maxTokens=1000,
        )
        review_response = await server.request_sampling(review_request)
        review = review_response.content[0].text if review_response.content else ""

    # Return the complete analysis pipeline result
    return [TextContent(type="text", text=json.dumps({
        "pipeline": "log_analysis_with_sampling",
        "steps": [
            {"step": 1, "action": "Server extracted error patterns", "patterns_found": len(error_patterns)},
            {"step": 2, "action": "Sampling: Claude classified errors", "result": classification},
            {"step": 3, "action": "Sampling: Claude created remediation plan", "result": remediation_plan},
        ] + ([{"step": 4, "action": "Sampling: Claude reviewed the plan", "result": review}] if review else []),
        "final_remediation_plan": remediation_plan,
        "review": review if review else None,
    }, indent=2, default=str))]


def _extract_error_patterns(log_text: str) -> list[dict]:
    """Server-side processing: extract error patterns from raw logs."""
    patterns = {}
    for line in log_text.splitlines():
        match = re.search(r"(ERROR|WARN|FATAL|CRITICAL|Exception|Traceback)[:\s]*(.+)", line, re.IGNORECASE)
        if match:
            level = match.group(1).upper()
            message = match.group(2).strip()[:200]
            # Create a simplified pattern key
            pattern_key = re.sub(r'\d+', 'N', message.lower())
            pattern_key = re.sub(r'0x[0-9a-f]+', '0xHEX', pattern_key)
            pattern_key = re.sub(r'[a-f0-9]{8,}', 'HASH', pattern_key)[:100]
            if pattern_key not in patterns:
                patterns[pattern_key] = {"sample": message, "count": 0, "levels": set()}
            patterns[pattern_key]["count"] += 1
            patterns[pattern_key]["levels"].add(level)

    return [
        {"pattern": k, "sample": v["sample"], "count": v["count"],
         "levels": list(v["levels"])}
        for k, v in sorted(patterns.items(), key=lambda x: -x[1]["count"])[:10]
    ]


# ===========================================================================
# USE CASE 2: Structured Extraction — server collects raw data, asks Claude
#             to format, classify, and structure it.
# ===========================================================================

@server.tool()
async def extract_and_structure(
    raw_text: str,
    extraction_type: str = "auto",
) -> list[TextContent]:
    """Extract structured information from unstructured text using sampling.

    The server pre-processes the text (tokenization, frequency analysis),
    then asks Claude via sampling to extract structured data.

    Args:
        raw_text: Unstructured text to extract from
        extraction_type: "auto" (detect), "events" (calendar events), "contacts",
                         "tasks", "requirements", "key_value"
    """
    # Server-side pre-processing
    words = re.findall(r'\b\w+\b', raw_text.lower())
    word_freq = Counter(words).most_common(20)
    char_count = len(raw_text)
    line_count = len(raw_text.splitlines())

    # Use SAMPLING — ask Claude to extract structured data
    extract_request = CreateMessageRequestParams(
        messages=[{
            "role": "user",
            "content": ContentBlock(
                type="text",
                text=f"""Extract structured data from the following text.

Context (computed by server):
- Character count: {char_count}
- Line count: {line_count}
- Top terms: {json.dumps([w for w, c in word_freq if len(w) > 3][:15])}
- Extraction type: {extraction_type}

RAW TEXT:
---
{raw_text[:8000]}
---

Extract as much structured data as possible. If extraction_type is "auto", detect what kind of
data is present and extract accordingly. Return a JSON object with:

1. "detected_type": what kind of content this is
2. "extracted": the structured data (array of objects appropriate to the type)
3. "confidence": 0.0-1.0 how confident you are in the extraction
4. "suggestions": any suggestions for improving extraction quality

For events: extract date, time, title, location, attendees
For contacts: extract name, email, phone, company, role
For tasks: extract title, deadline, priority, assignee
For requirements: extract id, description, priority, dependencies
For key_value: extract key-value pairs found in the text""",
            ),
        }],
        maxTokens=3000,
        systemPrompt="You are a data extraction expert. Always return valid, well-structured JSON.",
    )

    extraction_response = await server.request_sampling(extract_request)
    extracted = extraction_response.content[0].text if extraction_response.content else "{}"

    return [TextContent(type="text", text=json.dumps({
        "method": "structured_extraction_with_sampling",
        "server_preprocessing": {
            "char_count": char_count,
            "line_count": line_count,
            "top_terms": [w for w, c in word_freq if len(w) > 3][:15],
        },
        "claude_extraction": extracted,
    }, indent=2, default=str))]


# ===========================================================================
# USE CASE 3: Quality Review — server generates output, asks Claude to review
#             and suggest improvements, then incorporates feedback.
# ===========================================================================

@server.tool()
async def generate_with_review(
    content_type: str,
    topic: str,
    iterations: int = 2,
) -> list[TextContent]:
    """Generate content with iterative sampling-based review and refinement.

    The server initiates a generate→review→revise loop using sampling
    at each stage. This demonstrates agentic orchestration via MCP.

    Args:
        content_type: What to generate — "release_notes", "api_docs", "error_message",
                      "commit_message", "code_comment"
        topic: The specific topic/content to document
        iterations: Number of review-refine cycles (1-3). Default 2.
    """
    if iterations < 1:
        iterations = 1
    if iterations > 3:
        iterations = 3

    # Step 1: SAMPLING — initial generation
    generate_request = CreateMessageRequestParams(
        messages=[{
            "role": "user",
            "content": ContentBlock(
                type="text",
                text=f"""Generate {content_type} for the following topic:

TOPIC: {topic}

Requirements for {content_type}:
- release_notes: Clear, categorized (Features, Fixes, Breaking Changes), version-numbered
- api_docs: Endpoint description, parameters table, request/response examples, error codes
- error_message: User-friendly, actionable, includes next steps, appropriate tone
- commit_message: Conventional commits format, 72-char subject, bulleted body
- code_comment: Explains WHY not WHAT, notes edge cases, references related code

Write only the content — no preamble or meta-commentary.""",
            ),
        }],
        maxTokens=1500,
        systemPrompt=f"You are a technical writer specializing in {content_type}. Be clear, accurate, and concise.",
    )

    gen_response = await server.request_sampling(generate_request)
    draft = gen_response.content[0].text if gen_response.content else ""

    # Steps 2-N: SAMPLING review → revise loop
    history = [{"stage": "initial_draft", "content": draft}]

    for i in range(iterations):
        # Review
        review_request = CreateMessageRequestParams(
            messages=[{
                "role": "user",
                "content": ContentBlock(
                    type="text",
                    text=f"""Review this {content_type} draft:

{draft}

Identify:
1. What's good? (strengths)
2. What needs improvement? (weaknesses — be specific)
3. What's missing? (gaps)
4. Specific rewrite suggestions

Be critical and constructive. Focus on correctness, clarity, and completeness.

Respond in this format:
STRENGTHS:
- ...

WEAKNESSES:
- ...

GAPS:
- ...

SUGGESTED_REWRITE:
[The full rewritten version]""",
                ),
            }],
            maxTokens=2500,
            systemPrompt="You are a meticulous editor reviewing technical content.",
        )

        review_response = await server.request_sampling(review_request)
        review_text = review_response.content[0].text if review_response.content else ""

        # Parse the review to extract the suggested rewrite
        rewrite_match = re.search(r"SUGGESTED_REWRITE:\s*\n(.*)", review_text, re.DOTALL | re.IGNORECASE)
        if rewrite_match:
            draft = rewrite_match.group(1).strip()

        history.append({
            "stage": f"review_cycle_{i+1}",
            "review": review_text,
            "revised_draft": draft,
        })

    return [TextContent(type="text", text=json.dumps({
        "content_type": content_type,
        "topic": topic,
        "iterations": iterations,
        "final_content": draft,
        "revision_history": history,
    }, indent=2, default=str))]


# ===========================================================================
# USE CASE 4: Orchestration — server acts as orchestrator, delegates reasoning
#             to Claude for each sub-decision, then aggregates.
# ===========================================================================

@server.tool()
async def decision_matrix(
    scenario: str,
    options_json: str,
    criteria_json: str,
) -> list[TextContent]:
    """Evaluate multiple options against criteria using sampling-based analysis.

    The server sets up a decision matrix, then uses sampling to ask Claude to:
    1. Score each option against each criterion
    2. Weight the criteria by importance
    3. Compute final rankings with rationale

    Args:
        scenario: Description of the decision context
        options_json: JSON array of option names/descriptions
        criteria_json: JSON array of criterion names/descriptions
    """
    options = json.loads(options_json)
    criteria = json.loads(criteria_json)

    # Step 1: SAMPLING — score each option
    scoring_request = CreateMessageRequestParams(
        messages=[{
            "role": "user",
            "content": ContentBlock(
                type="text",
                text=f"""You are evaluating options for this decision:

SCENARIO: {scenario}

OPTIONS:
{json.dumps(options, indent=2)}

CRITERIA:
{json.dumps(criteria, indent=2)}

For each option, score it against each criterion on a scale of 1-10.
For each score, provide a one-sentence justification.

Return as JSON array:
[
  {{
    "option": "Option A",
    "scores": {{"Cost": 8, "Speed": 6, ...}},
    "justifications": {{"Cost": "Because...", "Speed": "Because...", ...}}
  }},
  ...
]""",
            ),
        }],
        maxTokens=3000,
        systemPrompt="You are a decision analyst. Be objective, data-driven, and specific in justifications.",
    )

    scores_response = await server.request_sampling(scoring_request)
    scores_text = scores_response.content[0].text if scores_response.content else "[]"

    # Step 2: SAMPLING — weight criteria and compute final ranking
    ranking_request = CreateMessageRequestParams(
        messages=[{
            "role": "user",
            "content": ContentBlock(
                type="text",
                text=f"""Given these scores:
{scores_text}

And the original scenario: {scenario}

1. Assign a weight (1-100) to each criterion based on importance for this scenario
2. Compute weighted scores for each option
3. Rank options from best to worst
4. For the top 3, provide a narrative rationale
5. Identify any "dealbreaker" criteria that would eliminate options regardless of score

Return as JSON with: weights, weighted_scores, rankings, rationale, dealbreakers""",
            ),
        }],
        maxTokens=2000,
        systemPrompt="You are a decision analyst computing weighted decision matrices.",
    )

    ranking_response = await server.request_sampling(ranking_request)
    final_ranking = ranking_response.content[0].text if ranking_response.content else "{}"

    return [TextContent(type="text", text=json.dumps({
        "scenario": scenario,
        "options_count": len(options),
        "criteria_count": len(criteria),
        "raw_scores": scores_text,
        "final_ranking": final_ranking,
        "method": "sampling-based decision matrix with weighted criteria",
    }, indent=2, default=str))]


# ===========================================================================
# USE CASE 5: Content Classification — batch classify items via sampling
# ===========================================================================

@server.tool()
async def batch_classify(
    items_json: str,
    labels: str,
    context: str = "",
) -> list[TextContent]:
    """Classify a batch of items into categories using sampling.

    The server pre-validates the input, then delegates classification to Claude.

    Args:
        items_json: JSON array of items to classify (strings or objects)
        labels: Comma-separated classification labels
        context: Optional context about what the items represent
    """
    items = json.loads(items_json)
    label_list = [l.strip() for l in labels.split(",")]

    if len(items) > 50:
        items = items[:50]  # Batch limit

    classify_request = CreateMessageRequestParams(
        messages=[{
            "role": "user",
            "content": ContentBlock(
                type="text",
                text=f"""Classify each item into one of these labels: {', '.join(label_list)}.

Context: {context if context else 'General classification'}

ITEMS:
{json.dumps(items, indent=2)}

For each item, return:
- item_index: the 0-based index
- label: one of {label_list}
- confidence: 0.0-1.0
- reasoning: one sentence

Return as JSON array of classification objects.""",
            ),
        }],
        maxTokens=3000,
        systemPrompt=f"You are a classification expert. Always pick exactly one label from: {label_list}. Be consistent.",
    )

    classify_response = await server.request_sampling(classify_request)
    classification = classify_response.content[0].text if classify_response.content else "[]"

    return [TextContent(type="text", text=json.dumps({
        "total_items": len(items),
        "labels": label_list,
        "classification": classification,
    }, indent=2, default=str))]


# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

@server.resource("sampling://usage-stats")
async def usage_stats() -> str:
    return json.dumps({
        "note": "Sampling allows MCP servers to request LLM generations from Claude during tool execution.",
        "uses_cases": [
            "Multi-step analysis (log_analysis with 3 sampling calls)",
            "Structured extraction (raw text → structured data)",
            "Quality review (generate → review → revise loop)",
            "Decision matrix (score → weight → rank pipeline)",
            "Batch classification (classify items via sampling)",
        ],
        "configuration_required": {
            "settings.json": '"mcp__sampling-demo__samplePermission": "allow"',
            "note": "Without this permission, Claude Code will prompt for each sampling request.",
        },
        "methods_used": [
            "server.request_sampling() — client-side sampling call",
            "CreateMessageRequestParams — sampling request parameters",
            "systemPrompt — system-level instruction for the LLM",
            "maxTokens — limit token consumption per sampling call",
        ],
    }, indent=2)


@server.resource("sampling://pattern/{use_case}")
async def get_pattern(use_case: str) -> str:
    """Parameterized resource — get the code pattern for a sampling use case."""
    patterns = {
        "multi_step": "Extract → Request classification via sampling → Request synthesis via sampling → Return aggregated result",
        "extraction": "Pre-process raw data → Request structured extraction via sampling → Return server stats + LLM output",
        "review_loop": "Generate initial → Loop: Request review via sampling → Parse review → Revise → Return final + history",
        "decision": "Request scoring via sampling → Request weighted ranking via sampling → Return matrix + rankings",
        "classification": "Validate batch → Request classification via sampling → Return batch + labels",
    }
    return json.dumps({
        "use_case": use_case,
        "pattern": patterns.get(use_case, "Unknown use case. Try: multi_step, extraction, review_loop, decision, classification"),
        "all_use_cases": list(patterns.keys()),
    }, indent=2)


# ---------------------------------------------------------------------------
# Prompts — for discovering and using sampling features
# ---------------------------------------------------------------------------

@server.prompt(
    name="sampling-explorer",
    description="Explore what sampling can do with interactive examples",
    arguments={
        "scenario": {
            "type": "string",
            "enum": ["log_analysis", "data_extraction", "content_review", "decision_making", "classification"],
            "description": "Which sampling use case to explore?",
            "required": True,
        },
    },
)
async def sampling_explorer_prompt(scenario: str) -> dict:
    guides = {
        "log_analysis": "Use analyze_logs_with_sampling with some sample log text. The server will extract errors, then use sampling to ask Claude to classify and create a remediation plan.",
        "data_extraction": "Use extract_and_structure with some unstructured text (meeting notes, email thread, etc.). The server pre-processes, then uses sampling to extract structured data.",
        "content_review": "Use generate_with_review to create some technical content with iterative sampling-based review. Try 2 iterations to see the refinement loop.",
        "decision_making": "Use decision_matrix with options and criteria. The server uses sampling twice: first to score, then to weight and rank.",
        "classification": "Use batch_classify with a list of items to label. The server delegates the classification to Claude via sampling.",
    }
    return {
        "messages": [{
            "role": "user",
            "content": {
                "type": "text",
                "text": f"""Explore the MCP Sampling capability with this scenario: {scenario}.

{guides.get(scenario, guides['log_analysis'])}

WHAT IS SAMPLING?
Sampling is the fourth MCP primitive — it lets MCP servers ask Claude to generate text
during tool execution. Unlike normal tool calls (where Claude decides to use a tool),
sampling is server-initiated: the server pauses, asks Claude to think, then continues.

KEY DIFFERENCE FROM NORMAL TOOLS:
- Normal: Claude → calls tool → gets result
- Sampling: Claude → calls tool → server asks Claude to generate → gets LLM response → server continues → returns result

This enables:
- Multi-step analysis (extract → classify → synthesize)
- Quality review loops (generate → review → revise)
- Orchestration (server coordinates multiple Claude generations)
- Structured extraction (server pre-processes, Claude structures)

Try the tool now and observe:
1. The server sends sampling requests to Claude
2. Claude generates responses mid-tool-execution
3. The server aggregates everything into a final result""",
            },
        }],
    }


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

async def main():
    transport = StdioServerTransport()
    await server.run(transport)

if __name__ == "__main__":
    asyncio.run(main())
