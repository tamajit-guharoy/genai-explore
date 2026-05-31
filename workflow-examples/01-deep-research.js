// Deep Research Report Workflow
// Fan-out parallel web searches from 6 angles, fetch source URLs,
// adversarially verify top claims, and synthesize a cited report.

export const meta = {
  name: 'deep-research-report',
  description: 'Fan-out web research with adversarial claim verification',
  phases: [
    { title: 'Search' },
    { title: 'Fetch' },
    { title: 'Verify' },
    { title: 'Synthesize' }
  ]
}

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const SEARCH_SCHEMA = {
  type: 'object',
  properties: {
    angle:    { type: 'string' },
    findings: { type: 'array', items: { type: 'string' } },
    topUrl:   { type: 'string' },
    summary:  { type: 'string' }
  },
  required: ['angle', 'findings', 'topUrl', 'summary']
}

const CLAIMS_SCHEMA = {
  type: 'object',
  properties: {
    claims: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          claim:  { type: 'string' },
          source: { type: 'string' }
        },
        required: ['claim', 'source']
      }
    }
  },
  required: ['claims']
}

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted: { type: 'boolean' },
    reason:  { type: 'string' }
  },
  required: ['refuted', 'reason']
}

// ---------------------------------------------------------------------------
// Workflow entry point
// ---------------------------------------------------------------------------

export default async function deepResearch({ args, agent, parallel, pipeline, log }) {

  // Default to a sample question when none is supplied
  const question = args.question || 'What are the latest breakthroughs in nuclear fusion energy and their practical implications?'

  // The six search angles provide orthogonal coverage so no single framing
  // dominates the evidence gathered.
  const angles = [
    'background',
    'recent-developments',
    'technical-details',
    'criticisms',
    'expert-opinions',
    'real-world-applications'
  ]

  // ===========================================================================
  // Phase 1 — Search
  // parallel() fans out all 6 angle searches simultaneously. Because no search
  // depends on another, concurrent execution is safe and reduces total wall-clock
  // time to that of the slowest single search rather than the sum of all six.
  // ===========================================================================
  log(`[Search] Launching ${angles.length} parallel searches for: "${question}"`)

  const searchResults = await parallel(
    angles.map(angle => ({
      label: 'search:' + angle,
      phase: 'Search',
      schema: SEARCH_SCHEMA,
      model: 'haiku',
      prompt: `You are a research assistant. Search for information about the following question from the "${angle}" angle.

Question: ${question}

Perform a thorough web search focusing on the "${angle}" perspective.
Return:
- angle: the angle name ("${angle}")
- findings: array of 3-5 key facts or data points discovered
- topUrl: the single most authoritative or informative URL you found
- summary: a 2-3 sentence synthesis of what you found from this angle`
    }))
  )

  log(`[Search] Completed ${searchResults.length} searches`)

  // ===========================================================================
  // Phase 2 — Fetch
  // pipeline() is used because each fetch step depends on the topUrl that was
  // only determined after its paired search completed. pipeline() chains the
  // upstream result into the downstream fetch agent, preserving the data flow
  // without requiring manual await loops.
  // agentType: 'Explore' signals that this agent should browse and extract
  // content from a live URL rather than perform a generation-only task.
  // ===========================================================================
  log(`[Fetch] Fetching top URLs from ${searchResults.length} search results`)

  const fetchResults = await pipeline(
    searchResults.map((result, i) => ({
      label: 'fetch:' + angles[i],
      phase: 'Fetch',
      agentType: 'Explore',
      prompt: `Fetch and extract the most important content from this URL for research purposes.

URL: ${result.topUrl}
Research question: ${question}
Search angle: ${angles[i]}

Extract:
- The main claims or findings on the page
- Supporting evidence, statistics, or citations
- Author/publication credibility signals
- Date of publication if available

Summarize the key content that is relevant to the research question.`
    }))
  )

  log(`[Fetch] Completed ${fetchResults.length} URL fetches`)

  // ===========================================================================
  // Claim Extraction
  // One agent synthesizes ALL search and fetch findings into the top 5 claims
  // that will be subjected to adversarial verification.
  // ===========================================================================
  log('[Verify] Extracting top 5 claims from all gathered findings')

  const allFindings = searchResults
    .map((r, i) => [
      `=== Angle: ${angles[i]} ===`,
      `Summary: ${r.summary}`,
      `Findings:\n${r.findings.join('\n')}`,
      `Fetched content:\n${typeof fetchResults[i] === 'string' ? fetchResults[i] : JSON.stringify(fetchResults[i])}`
    ].join('\n'))
    .join('\n\n')

  const claimsResult = await agent({
    label: 'extract-claims',
    schema: CLAIMS_SCHEMA,
    prompt: `You are a critical analyst. Given the following research findings about "${question}", extract the 5 most significant, specific, and verifiable claims.

For each claim:
- Make it a concrete, falsifiable statement (not vague)
- Attribute it to the most credible source URL found in the research
- Focus on claims that are central to answering the research question

Research findings:
${allFindings}

Return exactly 5 claims with their sources.`
  })

  const claims = claimsResult.claims || []
  log(`[Verify] Running adversarial verification on ${claims.length} claims`)

  // ===========================================================================
  // Phase 3 — Verify
  // Adversarial verification pattern: for each claim, 3 independent "skeptic"
  // agents are tasked to REFUTE the claim. Assuming a claim is false until it
  // survives scrutiny counteracts the confirmation bias of asking "is this true?"
  //
  // parallel() is used for the 3 voters because:
  // 1. Each voter evaluates the same claim independently — no output dependency.
  // 2. Running them concurrently prevents anchoring: voter N cannot influence
  //    voter N+1 since they never see each other's reasoning.
  // 3. Wall-clock time per claim equals one agent call, not three sequential ones.
  //
  // A claim survives if at least 2 of 3 skeptics return refuted: false.
  // ===========================================================================
  const verifiedClaims = []
  const droppedClaims = []

  for (const claim of claims) {
    // Three independent skeptics attempt to disprove the same claim in parallel.
    const voters = await parallel(
      [0, 1, 2].map(i => ({
        label: `skeptic-${i}:${claim.source}`,
        phase: 'Verify',
        schema: VERDICT_SCHEMA,
        model: 'haiku',
        prompt: `You are a rigorous fact-checker and skeptic (instance ${i + 1} of 3). Your job is to ATTEMPT TO REFUTE the following claim.

Claim: "${claim.claim}"
Source: ${claim.source}
Research context: ${question}

Search for counter-evidence, methodological flaws, outdated information, misrepresentation, or alternative interpretations that would undermine this claim.

Return:
- refuted: true if you found credible evidence or reasoning that refutes or seriously undermines the claim, false if the claim holds up under scrutiny
- reason: your specific reasoning or the counter-evidence found (or why you could not refute it)`
      }))
    )

    // .filter(Boolean) removes null/undefined results from any failed agents
    // before counting votes, preventing crashes on partial failures.
    const validVoters = voters.filter(Boolean)
    const survivedCount = validVoters.filter(v => v.refuted === false).length
    const refutedCount  = validVoters.filter(v => v.refuted === true).length

    // Claim survives if at least 2 of 3 skeptics failed to refute it.
    if (survivedCount >= 2) {
      verifiedClaims.push({
        ...claim,
        verificationScore: `${survivedCount}/3 skeptics failed to refute`
      })
    } else {
      droppedClaims.push({
        ...claim,
        refutedBy: refutedCount,
        reasons: validVoters.filter(v => v.refuted).map(v => v.reason)
      })
    }
  }

  log(`[Verify] ${verifiedClaims.length} claims verified, ${droppedClaims.length} dropped`)

  // ===========================================================================
  // Phase 4 — Synthesize
  // One agent writes the final report using ONLY verified claims, ensuring the
  // output is grounded in evidence that survived adversarial review.
  // ===========================================================================
  log('[Synthesize] Writing final report from verified claims')

  const report = await agent({
    label: 'synthesize-report',
    phase: 'Synthesize',
    prompt: `You are an expert research writer. Write a comprehensive, well-structured research report answering the following question.

IMPORTANT: Base your report ONLY on the verified claims listed below. Do not introduce information not supported by these claims.

Research question: ${question}

Verified claims (each survived adversarial review by 3 skeptics):
${verifiedClaims.map((c, i) => `${i + 1}. "${c.claim}" [Source: ${c.source}] (${c.verificationScore})`).join('\n')}

${droppedClaims.length > 0
  ? `NOTE: The following ${droppedClaims.length} claims were dropped due to insufficient evidence and must NOT appear in the report:\n${droppedClaims.map(c => `- "${c.claim}"`).join('\n')}`
  : ''}

Write a report with:
1. Executive Summary (2-3 sentences)
2. Key Findings (one section per verified claim, with inline citation)
3. Analysis and Implications
4. Limitations and Caveats (acknowledge what we do NOT know)
5. References (list all cited source URLs)

Use clear, authoritative language appropriate for an informed general audience.`
  })

  log('[Synthesize] Report complete')

  // Return the structured result for the caller.
  return {
    question,
    verifiedClaims,
    droppedClaims,
    report
  }
}
