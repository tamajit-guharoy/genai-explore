// Codebase Security Audit — Dynamic Workflow
//
// PURPOSE: Systematically find security vulnerabilities using a multi-modal
// sweep (4 independent scanners, each blind to the others), then adversarially
// verify each unique finding with perspective-diverse lenses.
//
// PHASES:
//   1. Discover  — 4 parallel scanners, each owns a distinct vulnerability class
//   2. Verify    — 3 perspective-diverse lens agents per unique finding (haiku)
//   3. Report    — single agent writes the final markdown report
//
// WHY parallel() BARRIER BEFORE DEDUP?
//   The deduplication step must see ALL findings from ALL 4 scanners before it
//   can compare (file, line) pairs across agents. If dedup ran inside any single
//   scanner it would only see that scanner's output. The barrier is therefore
//   *justified* — it is the earliest point at which cross-finder dedup becomes
//   possible, and no work downstream of it can start until every scanner has
//   committed its findings.
//
// MULTI-MODAL SWEEP (Discover):
//   Each agent attacks the codebase from a completely different vulnerability
//   angle with no shared context. This maximises recall because blind-spot
//   patterns for one angle are often obvious to another. The four angles are:
//   injection (taint/data-flow), auth (trust-boundary/privilege), crypto
//   (entropy/secrets), and exposure (information-disclosure/path-traversal).
//
// PERSPECTIVE-DIVERSE vs ADVERSARIAL (Verify):
//   "Adversarial" implies one agent trying to break another's output. Here we
//   use three lenses whose incentives pull in different directions:
//   - exploitability: tries to confirm a practical attack chain exists
//   - false-positive-check: tries to find a credible benign explanation
//   - severity-calibration: asks whether the severity rating is proportionate
//   Requiring majority agreement (2/3) before confirming a finding sharply
//   reduces both false positives and severity inflation without requiring any
//   agent to directly attack another's reasoning.

export const meta = {
  name: 'security-audit',
  description: 'Multi-modal vulnerability scan with adversarial verification',
  phases: [
    { title: 'Discover' },
    { title: 'Verify' },
    { title: 'Report' },
  ],
};

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const FINDING_SCHEMA = {
  type: 'object',
  properties: {
    title:       { type: 'string' },
    file:        { type: 'string' },
    line:        { type: 'number' },
    vulnClass:   { type: 'string' },
    severity:    { type: 'string', enum: ['critical', 'high', 'medium', 'low'] },
    description: { type: 'string' },
  },
  required: ['title', 'file', 'line', 'vulnClass', 'severity', 'description'],
};

const FINDINGS_SCHEMA = {
  type: 'object',
  properties: {
    findings: { type: 'array', items: FINDING_SCHEMA },
  },
  required: ['findings'],
};

const VERDICT_SCHEMA = {
  type: 'object',
  properties: {
    confirmed: { type: 'boolean' },
    lens:      { type: 'string' },
    notes:     { type: 'string' },
  },
  required: ['confirmed', 'lens', 'notes'],
};

// ---------------------------------------------------------------------------
// Scanner prompts — each agent has a narrow, exclusive mandate so scanners
// remain truly blind to each other's concerns (multi-modal sweep).
// ---------------------------------------------------------------------------

const SCANNER_PROMPTS = {
  injection: (targetDir) => `You are a security researcher specialising exclusively in injection vulnerabilities.
Recursively examine every source file under the directory: ${targetDir}

Look ONLY for:
  - SQL injection (raw queries, string concatenation into queries, ORM misuse)
  - OS / shell command injection (exec, spawn, eval, system calls with user input)
  - Template injection (server-side template engines, expression language injection)
  - LDAP / XPath / NoSQL injection

For each vulnerability found, record the exact file path, the nearest line number,
a concise title, a severity (critical/high/medium/low), and a clear description of
why this is exploitable. Do NOT report authentication, crypto, or data-exposure issues
— those are handled by other scanners.

Return your findings as structured JSON matching the required schema.`,

  auth: (targetDir) => `You are a security researcher specialising exclusively in authentication and
authorisation vulnerabilities.
Recursively examine every source file under the directory: ${targetDir}

Look ONLY for:
  - Missing or bypassable authentication checks
  - Broken access control / privilege escalation paths
  - Insecure session management (weak tokens, missing expiry, fixation)
  - JWT misuse (alg:none, weak signing keys, missing verification)
  - OAuth / OIDC misconfigurations
  - CSRF vulnerabilities

For each vulnerability found, record the exact file path, the nearest line number,
a concise title, a severity (critical/high/medium/low), and a clear description of
why this is exploitable. Do NOT report injection, crypto, or data-exposure issues.

Return your findings as structured JSON matching the required schema.`,

  crypto: (targetDir) => `You are a security researcher specialising exclusively in cryptography weaknesses
and secret management.
Recursively examine every source file under the directory: ${targetDir}

Look ONLY for:
  - Hardcoded secrets, API keys, passwords, tokens, private keys
  - Weak or deprecated algorithms (MD5, SHA1, DES, RC4, ECB mode)
  - Insufficient key lengths or weak random number generation
  - Insecure TLS configuration (SSLv3, TLS 1.0/1.1, weak cipher suites)
  - Improper certificate validation (hostname verification disabled, pinning bypass)
  - Secrets leaked via environment variable defaults or config file templates

For each vulnerability found, record the exact file path, the nearest line number,
a concise title, a severity (critical/high/medium/low), and a clear description.
Do NOT report injection, auth, or data-exposure issues.

Return your findings as structured JSON matching the required schema.`,

  exposure: (targetDir) => `You are a security researcher specialising exclusively in sensitive data exposure
and path traversal vulnerabilities.
Recursively examine every source file under the directory: ${targetDir}

Look ONLY for:
  - Path traversal / directory traversal (../../ in user-controlled paths)
  - Sensitive data written to logs, error messages, or HTTP responses
  - PII / financial data stored without encryption at rest
  - Insecure file upload handling (missing type/size validation, unsafe destinations)
  - Open redirects exposing internal services
  - Debug endpoints or verbose error pages left in production code
  - Missing security headers (CSP, HSTS, X-Frame-Options)

For each vulnerability found, record the exact file path, the nearest line number,
a concise title, a severity (critical/high/medium/low), and a clear description.
Do NOT report injection, auth, or crypto issues.

Return your findings as structured JSON matching the required schema.`,
};

// ---------------------------------------------------------------------------
// Lens prompts — perspective-diverse: one maximises threat (exploitability),
// one challenges it (false-positive-check), one calibrates it
// (severity-calibration). Majority (2/3) vote determines confirmation.
// ---------------------------------------------------------------------------

const LENS_PROMPTS = {
  exploitability: (f) => `You are a red-team attacker. Determine whether this reported finding is
genuinely exploitable in a real-world attack scenario.

Finding:
  Title:       ${f.title}
  File:        ${f.file}
  Line:        ${f.line}
  Vuln Class:  ${f.vulnClass}
  Severity:    ${f.severity}
  Description: ${f.description}

Assume a motivated, skilled attacker with read access to the source code.
Assess whether a practical exploit chain exists. Set confirmed: true only if
exploitation is feasible without extraordinary access or luck.
Set lens to "exploitability". Include specific attack steps or why exploitation fails.`,

  'false-positive-check': (f) => `You are a sceptical security engineer whose job is to eliminate false positives.

Finding:
  Title:       ${f.title}
  File:        ${f.file}
  Line:        ${f.line}
  Vuln Class:  ${f.vulnClass}
  Severity:    ${f.severity}
  Description: ${f.description}

Look for reasons this finding may NOT be a real vulnerability:
  - Is user input actually sanitised upstream?
  - Is the code path unreachable in production?
  - Is there a framework or middleware that already mitigates the risk?
  - Is this a test file, mock, or dead code?

Set confirmed: false if you find a credible mitigating factor; true only if you
cannot dismiss the finding. Set lens to "false-positive-check".`,

  'severity-calibration': (f) => `You are a senior security architect responsible for risk prioritisation.
Assess whether the reported severity is correctly calibrated.

Finding:
  Title:       ${f.title}
  File:        ${f.file}
  Line:        ${f.line}
  Vuln Class:  ${f.vulnClass}
  Severity:    ${f.severity}
  Description: ${f.description}

Consider: data sensitivity, blast radius, likelihood of exploitation, and
compensating controls. Set confirmed: true if the severity is reasonable (within
one level of your own assessment). Set confirmed: false if the finding is so
mis-calibrated that it should be re-evaluated or dropped.
Set lens to "severity-calibration". Include your recommended severity in notes.`,
};

// ---------------------------------------------------------------------------
// Main workflow export
// ---------------------------------------------------------------------------

export default async function securityAudit(args, { agent, parallel, pipeline, log }) {
  const targetDir  = args.targetDir  ?? 'src';
  const outputFile = args.outputFile ?? 'security-report.md';

  // =========================================================================
  // PHASE 1 — DISCOVER
  // Multi-modal sweep: 4 independent scanners, each with a distinct mandate,
  // each blind to the others. parallel() is the right primitive: scanners are
  // independent and IO-intensive. The barrier after parallel() is JUSTIFIED —
  // genuine cross-finder dedup requires all 4 result sets simultaneously.
  // =========================================================================

  log(`Starting multi-modal vulnerability sweep across: ${targetDir}`);

  const vulnClasses = ['injection', 'auth', 'crypto', 'exposure'];

  // Each agent label prefixed with 'scan:' per spec
  const scanResults = await parallel(
    vulnClasses.map((vulnClass) => ({
      label:  `scan:${vulnClass}`,
      phase:  'Discover',
      schema: FINDINGS_SCHEMA,
      prompt: SCANNER_PROMPTS[vulnClass](targetDir),
    }))
  );

  // -------------------------------------------------------------------------
  // Pure-JS deduplication — no agent needed; this is deterministic data work.
  // A finding is considered duplicate if it shares the same (file, line) pair.
  // When duplicates exist, keep the highest-severity report so we never
  // under-report the risk of a given code location.
  // -------------------------------------------------------------------------

  const SEVERITY_ORDER = { critical: 4, high: 3, medium: 2, low: 1 };

  const allFindings = scanResults.flatMap((result) => result.findings ?? []);
  const totalRaw    = allFindings.length;

  const deduped = new Map(); // key: "file:line"

  for (const finding of allFindings) {
    const key      = `${finding.file}:${finding.line}`;
    const existing = deduped.get(key);

    if (!existing) {
      deduped.set(key, finding);
    } else {
      // Keep the higher-severity entry so we never under-report
      const existingScore = SEVERITY_ORDER[existing.severity] ?? 0;
      const incomingScore = SEVERITY_ORDER[finding.severity]  ?? 0;
      if (incomingScore > existingScore) {
        deduped.set(key, finding);
      }
    }
  }

  const uniqueFindings = Array.from(deduped.values());
  const totalUnique    = uniqueFindings.length;

  // No Silent Caps — always log the dedup result
  log(`Deduped ${totalRaw} findings to ${totalUnique} unique across 4 scanners`);

  if (totalUnique === 0) {
    log('No findings to verify — writing clean report.');
    await agent({
      label:  'report:clean',
      phase:  'Report',
      prompt: `Write a security audit report to the file "${outputFile}" using the Write tool.
The audit found zero vulnerabilities in directory: ${targetDir}
Include: audit date, scanned directory, scanners used (injection, auth, crypto, exposure),
and a conclusion that no issues were detected.`,
    });
    return { total: 0, confirmed: 0, dropped: 0, outputFile };
  }

  // =========================================================================
  // PHASE 2 — VERIFY
  // Perspective-diverse verification: for each unique finding, 3 lens agents
  // each approach the finding from a different direction (exploitability,
  // false-positive-check, severity-calibration). pipeline() processes each
  // finding as a sequential unit; within each finding the 3 lenses run in
  // parallel (blind to each other — perspective-diverse, not antagonistic).
  // Confirmed if at least 2 of 3 lenses return confirmed: true.
  // =========================================================================

  log(`Verifying ${totalUnique} unique findings with 3 perspective-diverse lenses each...`);

  const lenses = ['exploitability', 'false-positive-check', 'severity-calibration'];

  const verifiedFindings = await pipeline(
    uniqueFindings,
    async (finding) => {
      // Run all 3 lenses in parallel for this finding — each lens is blind to
      // the others' verdicts, preserving perspective diversity.
      const verdicts = await parallel(
        lenses.map((lens) => ({
          label:  `verify:${finding.title}:${lens}`,
          phase:  'Verify',
          schema: VERDICT_SCHEMA,
          model:  'haiku',
          prompt: LENS_PROMPTS[lens](finding),
        }))
      );

      const confirmedCount = verdicts.filter((v) => v.confirmed === true).length;

      return {
        finding,
        verdicts,
        confirmed:      confirmedCount >= 2,
        confirmedCount,
      };
    }
  );

  const confirmedFindings = verifiedFindings.filter((r) => r.confirmed);
  const droppedFindings   = verifiedFindings.filter((r) => !r.confirmed);

  // No Silent Caps — always surface the verification counts
  log(
    `Confirmed ${confirmedFindings.length} of ${totalUnique} findings; ` +
    `${droppedFindings.length} dropped as false positives`
  );

  // =========================================================================
  // PHASE 3 — REPORT
  // Single agent synthesises all confirmed findings into a structured Markdown
  // security report and writes it to disk using the Write tool.
  // =========================================================================

  const confirmedSummary = confirmedFindings
    .map(({ finding, verdicts, confirmedCount }) => {
      const verdictNotes = verdicts
        .map((v) => `  - [${v.lens}] confirmed=${v.confirmed}: ${v.notes}`)
        .join('\n');
      return (
        `### [${finding.severity.toUpperCase()}] ${finding.title}\n` +
        `- **File:** ${finding.file} (line ${finding.line})\n` +
        `- **Class:** ${finding.vulnClass}\n` +
        `- **Description:** ${finding.description}\n` +
        `- **Lens verdicts (${confirmedCount}/3 confirmed):**\n${verdictNotes}`
      );
    })
    .join('\n\n');

  const droppedSummary = droppedFindings.length > 0
    ? droppedFindings
        .map(({ finding }) =>
          `- ${finding.title} (${finding.file}:${finding.line}) — dropped as likely false positive`
        )
        .join('\n')
    : '_None_';

  await agent({
    label:  'report:write',
    phase:  'Report',
    prompt: `Write a comprehensive security audit report to the file "${outputFile}" using the Write tool.

Structure the report exactly as follows:

# Security Audit Report

**Target directory:** ${targetDir}
**Audit date:** (today's date)
**Scanners:** injection, auth, crypto, exposure (multi-modal sweep — each blind to others)
**Verification:** exploitability + false-positive-check + severity-calibration (2/3 majority)

## Summary

| Metric | Count |
|--------|-------|
| Raw findings (pre-dedup) | ${totalRaw} |
| Unique findings (post-dedup) | ${totalUnique} |
| Confirmed vulnerabilities | ${confirmedFindings.length} |
| Dropped (false positives) | ${droppedFindings.length} |

## Confirmed Vulnerabilities

${confirmedSummary || '_No confirmed vulnerabilities._'}

## Dropped Findings (False Positives)

${droppedSummary}

## Methodology

Explain: (1) the multi-modal sweep — 4 independent scanners each blind to the others,
maximising recall by covering orthogonal vulnerability classes; (2) the parallel() barrier
which is justified because dedup requires all 4 scanner outputs simultaneously;
(3) perspective-diverse verification — 3 lenses with different incentives, majority vote
to reduce false positives and severity inflation.

Write this content verbatim to "${outputFile}" using the Write tool.`,
  });

  // =========================================================================
  // Return summary
  // =========================================================================

  return {
    total:      totalUnique,
    confirmed:  confirmedFindings.length,
    dropped:    droppedFindings.length,
    outputFile,
  };
}
