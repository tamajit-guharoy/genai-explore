/**
 * PR Review Pipeline
 *
 * Orchestrates a multi-dimension code review with adversarial verification
 * and a judge panel for the top bugs.
 *
 * WHY pipeline() NOT parallel() for review->verify:
 *   parallel() would force a barrier — all dimension reviews would have to finish
 *   before any verification could start. pipeline() processes each item through
 *   its stages independently: the moment 'security' review finishes, security
 *   verification starts immediately — without waiting for 'bugs', 'performance',
 *   or any other dimension. This is the "no barrier" property: total latency is
 *   bounded by the slowest single dimension, not by the sum of all reviews.
 *
 * WHY parallel() for 3 fix approaches:
 *   The three fix strategies (minimal, defensive, refactor) are fully independent
 *   of each other — none needs the output of another. Running them in parallel
 *   cuts wall-clock time by ~3x versus sequential generation, and all three results
 *   are available simultaneously when the judge agent needs to compare them.
 *
 * JUDGE PANEL PATTERN:
 *   For each top bug we fan out to N independent generator agents (one per fix
 *   approach) and then collapse with a single judge agent that scores all outputs.
 *   Separating generation from evaluation avoids anchoring bias: generator agents
 *   explore their approach freely; the judge applies a consistent scoring rubric.
 *   The 'grafts' field lets the judge cherry-pick valuable ideas from losing
 *   approaches into the winning recommendation.
 */

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    title:       { type: 'string' },
    file:        { type: 'string' },
    line:        { type: 'number' },
    severity:    { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
    description: { type: 'string' },
  },
  required: ['title', 'file', 'line', 'severity', 'description'],
};

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    items: { type: 'array', items: FINDING_SCHEMA },
  },
  required: ['items'],
};

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    refuted:    { type: 'boolean' },
    confidence: { type: 'number' },
    reason:     { type: 'string' },
  },
  required: ['refuted', 'confidence', 'reason'],
};

const FIX_SCHEMA = {
  type: 'object',
  properties: {
    approach:  { type: 'string' },
    code:      { type: 'string' },
    tradeoffs: { type: 'string' },
  },
  required: ['approach', 'code', 'tradeoffs'],
};

const JUDGE_SCHEMA = {
  type: 'object',
  properties: {
    winner:    { type: 'string' },
    rationale: { type: 'string' },
    grafts:    { type: 'array', items: { type: 'string' } },
  },
  required: ['winner', 'rationale', 'grafts'],
};

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export const meta = {
  name: 'pr-review-pipeline',
  description: 'Multi-dimension review with adversarial verification and judge panel',
  phases: [
    { title: 'Review' },
    { title: 'Verify' },
    { title: 'Judge' },
    { title: 'Comment' },
  ],
};

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const DIMENSIONS = ['bugs', 'security', 'performance', 'test-coverage', 'style'];

const FIX_APPROACHES = ['minimal', 'defensive', 'refactor'];

const SEVERITY_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

// ---------------------------------------------------------------------------
// Workflow entry point
// ---------------------------------------------------------------------------

export default async function run(args, { agent, parallel, pipeline, log }) {
  // ------------------------------------------------------------------
  // 1. Resolve the diff source
  // ------------------------------------------------------------------
  const prNumber = args?.prNumber;

  const diffContext = prNumber
    ? `PR #${prNumber}`
    : 'current branch diff (no prNumber provided)';

  const diffInstruction = prNumber
    ? `You are reviewing GitHub PR #${prNumber}. Obtain the diff using the GitHub API or available tools.`
    : `You are reviewing the diff of the current branch against its base. Use \`git diff origin/HEAD...HEAD\` or equivalent to obtain the diff.`;

  log(`Starting PR review pipeline for: ${diffContext}`);

  // ------------------------------------------------------------------
  // 2. pipeline() over DIMENSIONS — NO barrier between review and verify.
  //
  //    pipeline(items, ...stageFns) runs each item through all stages in
  //    order, but items are processed concurrently with each other.
  //    As soon as 'security' finishes Stage 1 it enters Stage 2 —
  //    it does NOT wait for 'bugs' or any other dimension to finish Stage 1.
  // ------------------------------------------------------------------

  const results = await pipeline(
    DIMENSIONS,

    // Stage 1: Review one dimension
    async (dim) => {
      const findings = await agent(
        `${diffInstruction}

You are a ${dim} specialist performing a focused code review.
Identify every ${dim} issue present in the diff.
Only report issues that are clearly evidenced — do not speculate.
For each issue provide: title, file path, line number, severity (critical/high/medium/low), and a concise description.`,
        {
          label: 'review:' + dim,
          phase: 'Review',
          schema: FINDINGS_SCHEMA,
        },
      );

      log(`[${dim}] review complete — ${findings?.items?.length ?? 0} raw findings`);
      return { findings, dim };
    },

    // Stage 2: Adversarially verify each finding from this dimension.
    // Starts immediately when Stage 1 for THIS dimension completes —
    // no cross-dimension barrier.
    async ({ findings, dim }) => {
      const items = findings?.items ?? [];

      if (items.length === 0) {
        log(`[${dim}] no findings to verify`);
        return [];
      }

      const verified = await parallel(
        items.map((f) => async () => {
          const verdict = await agent(
            `${diffInstruction}

You are an adversarial reviewer. Your job is to REFUTE the following finding if you can.
Be skeptical: look for false positives, misread context, already-handled edge cases, or scope creep.

Finding title: ${f.title}
File: ${f.file}
Line: ${f.line}
Severity: ${f.severity}
Description: ${f.description}

Attempt to refute this finding with solid evidence. If you cannot, mark refuted=false.
Set confidence (0.0–1.0) to reflect how certain you are of your verdict.`,
            {
              label: 'verify:' + f.title,
              phase: 'Verify',
              schema: VERDICT_SCHEMA,
            },
          );

          const isReal = verdict != null && !verdict.refuted;
          return { ...f, dimension: dim, isReal, verdict };
        }),
      );

      const confirmedCount = verified.filter((r) => r?.isReal).length;
      log(`[${dim}] verified ${confirmedCount}/${items.length} findings confirmed`);
      return verified;
    },
  );

  // ------------------------------------------------------------------
  // 3. Collect confirmed findings — No Silent Caps
  // ------------------------------------------------------------------

  const allResults = results.flat().filter(Boolean);
  const confirmed  = allResults.filter((r) => r.isReal);
  const dropped    = allResults.length - confirmed.length;

  // Always log the counts so no findings vanish silently.
  log(`Confirmed ${confirmed.length} of ${allResults.length} total findings; ${dropped} dropped`);

  // ------------------------------------------------------------------
  // 4. Phase "Judge" — judge panel for top 3 confirmed bugs by severity
  // ------------------------------------------------------------------

  const topBugs = confirmed
    .filter((f) => f.dimension === 'bugs')
    .sort((a, b) => (SEVERITY_ORDER[a.severity] ?? 99) - (SEVERITY_ORDER[b.severity] ?? 99))
    .slice(0, 3);

  log(`Running judge panel on ${topBugs.length} top bug(s)`);

  // parallel() over top bugs — each bug's judge pipeline is independent
  const fixes = await parallel(
    topBugs.map((bug) => async () => {
      // Fan out: 3 fix approaches in parallel (they are independent of each other)
      const approaches = await parallel(
        FIX_APPROACHES.map((approach) => async () =>
          agent(
            `${diffInstruction}

You are proposing a ${approach} fix for the following confirmed bug.

Bug: ${bug.title}
File: ${bug.file}
Line: ${bug.line}
Severity: ${bug.severity}
Description: ${bug.description}

- minimal: smallest safe change that eliminates the bug
- defensive: adds guards, assertions, or extra safety beyond the minimal fix
- refactor: restructures the affected code for long-term correctness

Provide:
- approach: exactly "${approach}"
- code: the concrete fix (diff or replacement snippet)
- tradeoffs: concise pros and cons of this approach`,
            {
              label: `fix:${approach}:${bug.title}`,
              phase: 'Judge',
              schema: FIX_SCHEMA,
            },
          ),
        ),
      );

      // Collapse: one judge scores all 3 and picks a winner
      const approachesSummary = approaches
        .map(
          (a, i) =>
            `[${FIX_APPROACHES[i].toUpperCase()}]\n` +
            `Approach: ${a?.approach}\n` +
            `Code:\n${a?.code}\n` +
            `Tradeoffs: ${a?.tradeoffs}`,
        )
        .join('\n\n---\n\n');

      const judgment = await agent(
        `You are a senior engineer acting as a judge.
Three fix approaches have been proposed for the bug below. Score them and pick the best.

Bug: ${bug.title}
File: ${bug.file}
Line: ${bug.line}
Severity: ${bug.severity}
Description: ${bug.description}

${approachesSummary}

Evaluate on: correctness, safety, and maintainability.
Select the winner by its approach name (minimal, defensive, or refactor).
Provide a rationale.
If any losing approach contains ideas worth incorporating into the winner, list them in grafts.`,
        {
          label: `judge:${bug.title}`,
          phase: 'Judge',
          schema: JUDGE_SCHEMA,
        },
      );

      return { bug, approaches, judgment };
    }),
  );

  // ------------------------------------------------------------------
  // 5. Phase "Comment" — synthesise into a PR review markdown comment
  // ------------------------------------------------------------------

  const findingLines = confirmed
    .map(
      (f) =>
        `- [${f.severity.toUpperCase()}] ${f.dimension}: ${f.title} — ${f.file}:${f.line}\n  ${f.description}`,
    )
    .join('\n');

  const fixLines = fixes
    .map(({ bug, approaches, judgment }) => {
      const winnerIdx = FIX_APPROACHES.indexOf(judgment?.winner);
      const winnerCode = winnerIdx >= 0 ? approaches[winnerIdx]?.code : '(see rationale)';
      return (
        `### ${bug.title}\n` +
        `**Winner:** ${judgment?.winner} — ${judgment?.rationale}\n` +
        (judgment?.grafts?.length ? `**Grafts:** ${judgment.grafts.join('; ')}\n` : '') +
        '```\n' + (winnerCode ?? '') + '\n```'
      );
    })
    .join('\n\n');

  const reviewComment = await agent(
    `You are writing a GitHub PR review comment for ${diffContext}.
Format the output as polished Markdown suitable for posting directly as a PR review.

CONFIRMED FINDINGS (${confirmed.length} total):
${findingLines || '(none)'}

RECOMMENDED FIXES FOR TOP BUGS:
${fixLines || '(none)'}

Structure the comment with:
1. Short executive summary (2–3 sentences)
2. Critical and High findings section
3. Medium and Low findings section
4. Recommended Fixes section (include winning code inline)
5. Closing note on overall code quality

Be concise and actionable. Use GitHub Markdown formatting.`,
    {
      label: 'comment:synthesis',
      phase: 'Comment',
    },
  );

  log('PR review pipeline complete.');

  return {
    confirmed,
    fixes,
    reviewComment,
  };
}
