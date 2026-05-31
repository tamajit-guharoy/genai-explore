// Competitive Analysis Workflow
// Patterns: multi-modal sweep (blind agents), completeness critic, budget-aware scaling, judge panel, no-silent-caps

export const meta = {
  name: 'competitive-analysis',
  description: 'Multi-modal sweep + completeness critic + budget-scaled analysis',
  phases: [
    { title: 'Sweep' },
    { title: 'Fill Gaps' },
    { title: 'Compare' },
    { title: 'Synthesize' },
  ],
};

// --- Schemas ---

const PROFILE_SCHEMA = {
  type: 'object',
  properties: {
    competitor: { type: 'string' },
    angle: { type: 'string' },
    findings: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
  },
  required: ['competitor', 'angle', 'findings', 'summary'],
};

const GAPS_SCHEMA = {
  type: 'object',
  properties: {
    competitor: { type: 'string' },
    missingInfo: { type: 'array', items: { type: 'string' } },
  },
  required: ['competitor', 'missingInfo'],
};

const COMPARISON_SCHEMA = {
  type: 'object',
  properties: {
    lens: { type: 'string' },
    rankings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          name: { type: 'string' },
          score: { type: 'number' },
        },
        required: ['name', 'score'],
      },
    },
    rationale: { type: 'string' },
  },
  required: ['lens', 'rankings', 'rationale'],
};

const SYNTHESIS_SCHEMA = {
  type: 'object',
  properties: {
    winner: { type: 'string' },
    keyInsights: { type: 'array', items: { type: 'string' } },
    recommendedActions: { type: 'array', items: { type: 'string' } },
  },
  required: ['winner', 'keyInsights', 'recommendedActions'],
};

// --- Workflow ---

export async function run(args, { agent, parallel, log, budget }) {
  // 1. Accept args with defaults
  const product = args?.product ?? 'Our Product';

  // 2. Validate args.competitors is an array; default if missing or invalid
  let competitors = args?.competitors;
  if (!Array.isArray(competitors)) {
    competitors = ['Competitor A', 'Competitor B', 'Competitor C'];
  }

  // Multi-modal sweep angles — each agent is blind to the others
  const angles = [
    'pricing-and-packaging',
    'features-and-capabilities',
    'user-reviews-and-sentiment',
    'recent-news-and-roadmap',
  ];

  // -----------------------------------------------------------------------
  // Phase "Sweep": for each competitor, run 4 parallel blind sweep agents
  // -----------------------------------------------------------------------
  log(`Phase Sweep: sweeping ${competitors.length} competitors across ${angles.length} angles`);

  const sweepResults = [];

  for (const competitor of competitors) {
    // parallel() over 4 angles per competitor — each agent is blind to the others (multi-modal sweep)
    const profiles = await parallel(
      angles.map((angle) => ({
        label: competitor + ':' + angle,
        phase: 'Sweep',
        schema: PROFILE_SCHEMA,
        model: 'haiku',
        prompt:
          `You are a competitive intelligence analyst. Your focus is strictly the "${angle}" angle. ` +
          `Research "${competitor}" from ONLY this perspective — do NOT consider other angles. ` +
          `Product context: comparing against "${product}". ` +
          `Return structured findings covering the "${angle}" angle specifically. Be factual and specific.`,
      }))
    );

    sweepResults.push({ competitor, profiles });
  }

  log('Swept ' + competitors.length + ' competitors across 4 angles');

  // -----------------------------------------------------------------------
  // Completeness Critic: one critic agent per competitor profile
  // -----------------------------------------------------------------------
  log('Running completeness critic for each competitor');

  const gapResults = await parallel(
    sweepResults.map(({ competitor, profiles }) => ({
      label: 'critic:' + competitor,
      phase: 'Fill Gaps',
      schema: GAPS_SCHEMA,
      prompt:
        `You are a completeness critic. Given this profile for "${competitor}", ` +
        `what important information is missing that would be needed for a thorough ` +
        `competitive analysis against "${product}"?\n\n` +
        `Profile:\n${JSON.stringify(profiles, null, 2)}\n\n` +
        `List each specific gap concisely in missingInfo.`,
    }))
  );

  // -----------------------------------------------------------------------
  // Phase "Fill Gaps": budget-aware gap filling — no silent caps
  // -----------------------------------------------------------------------
  log('Phase Fill Gaps: evaluating budget for gap filling');

  const filledGaps = [];
  let gapsSkipped = 0;

  if (budget?.total && budget.remaining() > 100_000) {
    const maxGapsToFill = Math.floor(budget.remaining() / 30_000);
    log(`Budget allows up to ${maxGapsToFill} gap fills (remaining: ${budget.remaining()} tokens)`);

    // Flatten all identified gaps across competitors
    const allGapItems = gapResults.flatMap((g) =>
      (g.missingInfo ?? []).map((info) => ({ competitor: g.competitor, info }))
    );

    const gapsToFill = allGapItems.slice(0, maxGapsToFill);
    gapsSkipped = allGapItems.length - gapsToFill.length;

    // No-silent-caps: always log how many gaps were skipped
    if (gapsSkipped > 0) {
      log(`Skipping ${gapsSkipped} of ${allGapItems.length} identified gaps — budget cap reached (max: ${maxGapsToFill})`);
    }

    if (gapsToFill.length > 0) {
      const filled = await parallel(
        gapsToFill.map(({ competitor, info }) => ({
          label: 'gap-fill:' + competitor + ':' + info.slice(0, 40),
          phase: 'Fill Gaps',
          schema: PROFILE_SCHEMA,
          model: 'haiku',
          prompt:
            `Research the following specific information gap about "${competitor}" ` +
            `for a competitive analysis against "${product}": "${info}". ` +
            `Provide focused, factual findings to fill this gap.`,
        }))
      );
      filledGaps.push(...filled);
      log(`Filled ${filledGaps.length} gap(s)`);
    }
  } else {
    // No silent caps — explicitly log why and how many gaps were skipped
    gapsSkipped = gapResults.reduce((sum, g) => sum + (g.missingInfo?.length ?? 0), 0);
    log(
      `Skipping gap fill — budget below threshold or not set ` +
      `(remaining: ${budget?.remaining ? budget.remaining() : 'N/A'}, threshold: 100,000). ` +
      `${gapsSkipped} identified gap(s) will not be filled.`
    );
  }

  // -----------------------------------------------------------------------
  // Phase "Compare": 3 independent analyst agents with different perspectives
  // -----------------------------------------------------------------------
  log('Phase Compare: running 3 independent analyst agents');

  const analysts = ['technical-depth', 'business-value', 'user-experience'];

  const fullProfileContext = JSON.stringify(
    { product, sweepResults, filledGaps },
    null,
    2
  );

  // 3 independent analysts — each uses a different lens
  const analystReports = await parallel(
    analysts.map((perspective) => ({
      label: 'analyst:' + perspective,
      phase: 'Compare',
      schema: COMPARISON_SCHEMA,
      prompt:
        `You are a competitive analyst specializing in the "${perspective}" lens. ` +
        `Evaluate and rank all competitors (including "${product}") using ONLY your lens. ` +
        `Assign a score 0–10 to each. Provide a clear rationale grounded in the data. ` +
        `Intelligence data:\n${fullProfileContext}`,
    }))
  );

  log('3 analyst perspectives complete — running judge synthesis');

  // One judge synthesizes all 3 analyst reports
  const judgeVerdict = await agent({
    label: 'judge:synthesis',
    phase: 'Compare',
    schema: SYNTHESIS_SCHEMA,
    prompt:
      `You are a senior strategy judge. Three independent analysts have evaluated competitors ` +
      `from different lenses. Synthesize their findings into a final verdict. ` +
      `Product under evaluation: "${product}". Competitors: ${competitors.join(', ')}.\n\n` +
      `Analyst reports:\n${JSON.stringify(analystReports, null, 2)}\n\n` +
      `Identify the overall winner, the most important cross-lens insights, ` +
      `and concrete recommended actions for "${product}".`,
  });

  // -----------------------------------------------------------------------
  // Phase "Synthesize": final agent writes the competitive analysis report
  // -----------------------------------------------------------------------
  log('Phase Synthesize: writing final competitive analysis report');

  const report = await agent({
    label: 'final-report',
    phase: 'Synthesize',
    prompt:
      `Write a comprehensive, executive-ready competitive analysis report for "${product}". ` +
      `Competitors evaluated: ${competitors.join(', ')}.\n\n` +
      `Include: executive summary, per-competitor profiles, gap analysis, ` +
      `comparative rankings, key strategic insights, and recommended actions. ` +
      `Use clear markdown formatting.\n\n` +
      `Sweep profiles:\n${JSON.stringify(sweepResults, null, 2)}\n\n` +
      `Filled gaps:\n${JSON.stringify(filledGaps, null, 2)}\n\n` +
      `Analyst perspectives:\n${JSON.stringify(analystReports, null, 2)}\n\n` +
      `Judge synthesis:\n${JSON.stringify(judgeVerdict, null, 2)}`,
  });

  log(`Competitive analysis complete. Gaps skipped: ${gapsSkipped}`);

  // 8. Return structured result
  return {
    competitors,
    report,
    gapsSkipped,
  };
}
