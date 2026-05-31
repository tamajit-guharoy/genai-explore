/**
 * Documentation Generator — Parameterized Workflow
 *
 * Demonstrates:
 *   - args global: workflow inputs passed in at invocation time
 *   - parallel() for concurrent file analysis
 *   - pipeline() for multi-stage doc generation and writing
 *   - workflow() composition (one-level child workflow call)
 *   - scriptPath iteration for fast re-runs with result caching
 *
 * Invoke example:
 *   Workflow({ scriptPath: "workflow-examples/06-parameterized-workflow.js",
 *              args: { files: ["src/index.js", "src/utils.js"],
 *                      style: "jsdoc",
 *                      outputDir: "docs" } })
 *
 * args global
 * -----------
 * The `args` object is injected automatically by the workflow runtime before
 * the script executes.  It contains whatever the caller passed in the `args`
 * field of the Workflow() invocation.  Access it directly — no import needed.
 */

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const ANALYSIS_SCHEMA = {
  type: 'object',
  properties: {
    file:        { type: 'string' },
    exports:     { type: 'array', items: { type: 'string' } },
    description: { type: 'string' },
    complexity:  { type: 'string', enum: ['simple', 'moderate', 'complex'] },
  },
  required: ['file', 'exports', 'description', 'complexity'],
}

const DOC_SCHEMA = {
  type: 'object',
  properties: {
    title:    { type: 'string' },
    content:  { type: 'string' },
    coverage: { type: 'number' },
  },
  required: ['title', 'content', 'coverage'],
}

// ---------------------------------------------------------------------------
// Workflow metadata
// ---------------------------------------------------------------------------

export const meta = {
  name: 'doc-generator',
  description: 'Generate documentation with quality-check via child workflow',
  phases: [
    { title: 'Analyze' },
    { title: 'Generate' },
    { title: 'Quality Check' },
    { title: 'Write' },
  ],
}

// ---------------------------------------------------------------------------
// Input validation and defaults
//
// `args` is the global injected by the runtime.  We normalise it here so the
// rest of the workflow can rely on well-typed, validated values.
//
// All defaults are provided explicitly — the workflow is self-contained and
// can be invoked without any args at all.
// ---------------------------------------------------------------------------

const VALID_STYLES = ['jsdoc', 'markdown']

// Default: ['src/index.js'] — must be an array; if caller passed a non-array
// we fall back rather than crash so the workflow degrades gracefully.
const files = Array.isArray(args?.files) ? args.files : ['src/index.js']

// Default: 'markdown'.  Silently correct unrecognised values so the workflow
// does not abort on a typo in the caller's args.
const style = VALID_STYLES.includes(args?.style) ? args.style : 'markdown'

// Default: 'docs'.  Must be a non-empty string.
const outputDir =
  typeof args?.outputDir === 'string' && args.outputDir.length > 0
    ? args.outputDir
    : 'docs'

// Log a warning when an explicitly supplied style value was not recognised
// so the caller knows it was corrected.
if (args?.style !== undefined && !VALID_STYLES.includes(args.style)) {
  log(
    `[doc-generator] Warning: unknown style "${args.style}" — ` +
    'falling back to "markdown". Valid values: jsdoc | markdown'
  )
}

// ---------------------------------------------------------------------------
// Phase "Analyze" — parallel() over args.files
//
// parallel() fans out all agent descriptors at once and collects results in
// input order.  Each file is analysed independently with agentType 'Explore'
// so the runtime can grant it filesystem read permissions.
// ---------------------------------------------------------------------------

const analyses = await parallel(
  files.map((file) => ({
    label:     'analyze:' + file,
    phase:     'Analyze',
    agentType: 'Explore',
    schema:    ANALYSIS_SCHEMA,
    prompt:
      `Analyze the source file "${file}". ` +
      'Return a JSON object matching the schema:\n' +
      '- file: the file path exactly as provided\n' +
      '- exports: list of exported function, class, and variable names\n' +
      '- description: one-sentence summary of what this module does\n' +
      '- complexity: one of "simple" | "moderate" | "complex"',
  }))
)

// ---------------------------------------------------------------------------
// Phase "Generate" — pipeline() over analyses
//
// pipeline() chains stages left-to-right for each item:
//   Stage 1 — agent call that produces structured doc content (DOC_SCHEMA)
//   Stage 2 — pure transform that shapes the result and attaches the original
//              file path so downstream phases always have it available
//
// Using pipeline() (rather than two parallel() calls) keeps per-file data
// flowing together: stage 2 receives both the agent output AND the original
// analysis object via its second argument.
// ---------------------------------------------------------------------------

const generatedDocs = await pipeline(
  analyses,

  // Stage 1: Generate documentation content
  (analysis) => ({
    label:  'gen:' + analysis.file,
    phase:  'Generate',
    schema: DOC_SCHEMA,
    prompt:
      `Generate ${style} documentation for the module described below.\n\n` +
      `Analysis:\n` +
      `  File:        ${analysis.file}\n` +
      `  Exports:     ${analysis.exports.join(', ')}\n` +
      `  Description: ${analysis.description}\n` +
      `  Complexity:  ${analysis.complexity}\n\n` +
      'Return a JSON object with:\n' +
      '- title:    the document heading\n' +
      `- content:  full ${style} documentation text\n` +
      '- coverage: estimated documentation coverage as a number between 0 and 1',
  }),

  // Stage 2: Transform — attach original file path to the agent result
  (docResult, originalAnalysis) => ({
    file:     originalAnalysis.file,
    content:  docResult.content,
    title:    docResult.title,
    coverage: docResult.coverage,
  })
)

// ---------------------------------------------------------------------------
// Phase "Quality Check" — workflow() composition
//
// workflow() delegates to another registered workflow by name.
// This is one-level nesting: the parent pauses while the child runs to
// completion, then receives the child's return value.
//
// One-level rule: child workflows should NOT themselves call workflow() to
// avoid deep chains that are hard to debug and whose caches do not compose.
//
// try/catch provides graceful degradation: if "doc-quality-check" is not
// registered in the current environment, the Write phase proceeds with all
// docs rather than failing the entire run.
// ---------------------------------------------------------------------------

let qualityReport

try {
  // workflow(name, inputArgs) — inputArgs becomes `args` inside the child.
  qualityReport = await workflow('doc-quality-check', { docs: generatedDocs })
} catch (err) {
  log(
    `[doc-generator] Warning: child workflow "doc-quality-check" is not available ` +
    `(${err.message}). Treating all generated docs as passing quality check.`
  )

  // Graceful degradation — mark every doc as passing so Write can proceed.
  qualityReport = {
    results: generatedDocs.map((doc) => ({
      file:   doc.file,
      passed: true,
      issues: [],
    })),
  }
}

// Partition docs into passing / failing using the quality report results.
const passingDocs = generatedDocs.filter((doc) => {
  const result = (qualityReport.results ?? []).find((r) => r.file === doc.file)
  return result ? result.passed : true
})

const failingDocs = generatedDocs.filter((doc) => {
  const result = (qualityReport.results ?? []).find((r) => r.file === doc.file)
  return result ? !result.passed : false
})

if (failingDocs.length > 0) {
  log(
    `[doc-generator] ${failingDocs.length} doc(s) failed quality check and will not be written:`
  )
  failingDocs.forEach((d) => log(`  - ${d.file}`))
}

// ---------------------------------------------------------------------------
// Phase "Write" — pipeline() each passing doc to disk
//
// Only docs that passed the quality check reach this phase.
// Stage 1 issues a write agent call; stage 2 normalises the confirmation.
// ---------------------------------------------------------------------------

const writeResults =
  passingDocs.length > 0
    ? await pipeline(
        passingDocs,

        // Stage 1: Write the documentation file
        (doc) => ({
          label:  'write:' + doc.file,
          phase:  'Write',
          prompt:
            `Write the following documentation to the file system.\n\n` +
            `Target directory : ${outputDir}\n` +
            `Source file      : ${doc.file}\n` +
            `Title            : ${doc.title}\n\n` +
            `Content:\n${doc.content}\n\n` +
            'Confirm by returning a brief success message that includes the full output path.',
        }),

        // Stage 2: Normalise the write confirmation
        (writeConfirmation, doc) => ({
          file:    doc.file,
          written: true,
          summary:
            typeof writeConfirmation === 'string'
              ? writeConfirmation
              : JSON.stringify(writeConfirmation),
        })
      )
    : []

// ---------------------------------------------------------------------------
// Return summary
// ---------------------------------------------------------------------------

export default {
  generated:     generatedDocs.length,
  qualityPassed: passingDocs.length,
  qualityFailed: failingDocs.length,
  outputDir,
  writtenFiles:  writeResults.map((r) => r.file),
}

// ---------------------------------------------------------------------------
// scriptPath iteration workflow
// ---------------------------------------------------------------------------
//
// To iterate on this script:
// 1. The Workflow tool returns the saved script path in its result
// 2. Edit the saved file using the Edit tool
// 3. Re-invoke: Workflow({ scriptPath: "path/from/result", resumeFromRunId: "wf_xxx" })
// 4. Completed agent() calls with unchanged prompts return cached results instantly
// 5. Only new or changed agent() calls re-run — fast iteration on large workflows
//
// Example iteration session:
//
//   // First run — full execution, saves script to runtime path
//   const run1 = await Workflow({
//     scriptPath: "workflow-examples/06-parameterized-workflow.js",
//     args: { files: ["src/index.js", "src/utils.js"], style: "markdown" },
//   })
//   // run1.scriptPath => "/saved/runtime/path/06-parameterized-workflow.js"
//   // run1.runId      => "wf_abc123"
//
//   // Edit the Generate prompt to improve output quality
//   await Edit({
//     file_path: run1.scriptPath,
//     old_string: "full ${style} documentation text",
//     new_string: "comprehensive ${style} documentation with examples",
//   })
//
//   // Resume — Analyze phase hits cache (unchanged); Generate and Write re-run
//   const run2 = await Workflow({
//     scriptPath:      run1.scriptPath,
//     resumeFromRunId: run1.runId,
//     args: { files: ["src/index.js", "src/utils.js"], style: "markdown" },
//   })

// ---------------------------------------------------------------------------
// Child workflow reference — doc-quality-check (commented-out example)
// ---------------------------------------------------------------------------
//
// The workflow() call above expects "doc-quality-check" to be registered in
// the runtime.  Save the code below as a separate file and register it to
// enable real quality checking.
//
// The child receives args.docs (array of { file, title, content, coverage })
// from the parent workflow() call and returns { results, totalChecked,
// totalPassed, totalFailed }.
//
// One-level nesting rule: this child does NOT call workflow() itself.
//
// ─────────────────────────────────────────────────────────────────────────────
//
// // FILE: 07-doc-quality-check.js
//
// export const meta = {
//   name: 'doc-quality-check',
//   description: 'Quality-check generated documentation for completeness and style',
//   phases: [
//     { title: 'Check' },
//   ],
// }
//
// const QUALITY_SCHEMA = {
//   type: 'object',
//   properties: {
//     file:   { type: 'string' },
//     passed: { type: 'boolean' },
//     issues: { type: 'array', items: { type: 'string' } },
//     score:  { type: 'number' },
//   },
//   required: ['file', 'passed', 'issues', 'score'],
// }
//
// // args.docs is injected from the parent's workflow('doc-quality-check', { docs }) call
// const docs = Array.isArray(args?.docs) ? args.docs : []
//
// // Check every doc concurrently — no ordering dependency between files
// const checkResults = await parallel(
//   docs.map((doc) => ({
//     label:  'check:' + doc.file,
//     phase:  'Check',
//     schema: QUALITY_SCHEMA,
//     prompt:
//       `Quality-check the following documentation for "${doc.file}".\n\n` +
//       `Title    : ${doc.title}\n` +
//       `Coverage : ${doc.coverage}\n\n` +
//       `Content:\n${doc.content}\n\n` +
//       'Evaluate for:\n' +
//       '- Completeness: are all exports documented?\n' +
//       '- Clarity: is the content easy to understand?\n' +
//       '- Style consistency\n' +
//       '- Accuracy of the coverage score\n\n' +
//       'Return a JSON object with:\n' +
//       '- file:   the file path\n' +
//       '- passed: true if overall quality score >= 0.7, false otherwise\n' +
//       '- issues: specific problems found (empty array if none)\n' +
//       '- score:  overall quality score between 0 and 1',
//   }))
// )
//
// export default {
//   results:      checkResults,
//   totalChecked: checkResults.length,
//   totalPassed:  checkResults.filter((r) => r.passed).length,
//   totalFailed:  checkResults.filter((r) => !r.passed).length,
// }
//
// ─────────────────────────────────────────────────────────────────────────────
