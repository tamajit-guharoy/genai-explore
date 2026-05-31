/**
 * Parallel Code Migration Workflow
 *
 * PURPOSE: Discover all files using a deprecated API, migrate each in an isolated
 * git worktree (no conflicts), verify each migration compiled, and report results.
 *
 * WHY WORKTREE ISOLATION IS ESSENTIAL:
 *   When migrating multiple files in parallel, each agent modifies the filesystem.
 *   Without isolation, concurrent writes to the same working tree cause race conditions,
 *   merge conflicts, and corrupted intermediate states. By setting isolation:'worktree',
 *   each migration agent gets its own git worktree — a separate checked-out copy of
 *   the repo — so all edits are fully independent. Results are merged back cleanly
 *   after each agent completes. This is the only safe way to parallelize file edits.
 *
 * PIPELINE STAGE SIGNATURE: (prevResult, originalItem, index)
 *   Each stage in a pipeline() call receives three arguments:
 *     - prevResult  : the structured output returned by the preceding stage
 *     - originalItem: the original element from the input array — always the
 *                     raw source value regardless of how many stages have run.
 *                     This is the key pipeline feature: later stages (like verify)
 *                     can always refer back to the original file path for labeling
 *                     even after prevResult has been transformed into an object.
 *     - index       : zero-based position in the array, useful for logging.
 *
 * DRY RUN PATTERN:
 *   When args.dryRun is true the migration agent is instructed to plan its
 *   changes and describe what it would do without actually writing any files.
 *   The verify stage still runs so the plan can be reviewed before committing
 *   to a real run.
 */

// ---------------------------------------------------------------------------
// Schemas
// ---------------------------------------------------------------------------

const FILES_SCHEMA = {
  type: 'object',
  properties: {
    files: { type: 'array', items: { type: 'string' } },
    count: { type: 'number' }
  },
  required: ['files', 'count']
}

const MIGRATION_SCHEMA = {
  type: 'object',
  properties: {
    file:         { type: 'string' },
    success:      { type: 'boolean' },
    changesCount: { type: 'number' },
    diff:         { type: 'string' },
    error:        { type: 'string' }
  },
  required: ['file', 'success', 'changesCount']
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    file:   { type: 'string' },
    passed: { type: 'boolean' },
    errors: { type: 'array', items: { type: 'string' } }
  },
  required: ['file', 'passed', 'errors']
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export const meta = {
  name: 'parallel-migration',
  description: 'Parallel file migration with worktree isolation — zero merge conflicts',
  phases: [
    { title: 'Discover' },
    { title: 'Migrate' },
    { title: 'Report' }
  ]
}

// ---------------------------------------------------------------------------
// Workflow
// ---------------------------------------------------------------------------

export default async function parallelMigration(args, { agent, pipeline, log }) {
  // ── 1. Validate args and apply defaults ────────────────────────────────────
  // Ensure args is always a plain object even when called with no arguments
  if (args === null || args === undefined || typeof args !== 'object' || Array.isArray(args)) {
    args = {}
  }

  const fromApi = typeof args.fromApi === 'string'  ? args.fromApi : 'oldMethod'
  const toApi   = typeof args.toApi   === 'string'  ? args.toApi   : 'newMethod'
  const dir     = typeof args.dir     === 'string'  ? args.dir     : 'src'
  const dryRun  = typeof args.dryRun  === 'boolean' ? args.dryRun  : false

  // ── 2. Phase "Discover" ────────────────────────────────────────────────────
  // One Explore agent scans the target directory for files using the deprecated API.

  const discovery = await agent(
    `Search the directory "${dir}" recursively for every source file that calls or ` +
    `references the deprecated API "${fromApi}". ` +
    `Return the list of relative file paths and the total count.`,
    {
      agentType: 'Explore',
      schema: FILES_SCHEMA
    }
  )

  const files = discovery.files ?? []
  log(`Discovered ${discovery.count ?? files.length} file(s) using "${fromApi}" in "${dir}"`)

  if (files.length === 0) {
    log('Nothing to migrate.')
    return { total: 0, migrated: 0, failed: 0, skipped: 0, dryRun }
  }

  // ── 3. Phase "Migrate" ─────────────────────────────────────────────────────
  // pipeline() fans out over the files array, running each item through the two
  // stages below in parallel. All pipeline stages run concurrently across items.

  const results = await pipeline(files, [

    // STAGE 1 — Migrate each file in an isolated worktree
    //
    // isolation:'worktree' is REQUIRED here. Because all items run in parallel,
    // without worktree isolation multiple agents would write to the same working
    // directory simultaneously, causing index lock conflicts and corrupted diffs.
    // Each worktree is an independent git checkout; the harness reconciles changes
    // after every agent finishes — zero merge conflicts regardless of parallelism.
    async (file) => {
      // DRY RUN PATTERN:
      //   When dryRun is true, instruct the agent to plan and describe its changes
      //   but NOT write any files. The schema still captures a planned diff and
      //   changesCount so the caller can review before committing to a real run.
      const dryRunNote = dryRun
        ? '\n\nDRY RUN: Do NOT write any files. Describe what you would change and produce a planned unified diff, but leave the filesystem untouched.'
        : ''

      return agent(
        `Migrate the file "${file}": replace every usage of the deprecated API ` +
        `"${fromApi}" with "${toApi}". Preserve all existing logic, formatting, ` +
        `and comments. Return the file path, whether the migration succeeded, ` +
        `how many occurrences were changed, and a unified diff of the changes.${dryRunNote}`,
        {
          label: 'migrate:' + file,
          phase: 'Migrate',
          // REQUIRED: worktree isolation prevents parallel write conflicts
          isolation: 'worktree',
          schema: MIGRATION_SCHEMA
        }
      )
    },

    // STAGE 2 — Verify the migration
    //
    // Stage signature: (prevResult, originalItem, index)
    //   - prevResult  = the MIGRATION_SCHEMA result object from stage 1
    //   - originalFile = the original file path string from the `files` input array.
    //                    This is the key pipeline feature: originalFile is always
    //                    the unchanged source value even after stage 1 returned an
    //                    object. We use it to label the verify task correctly.
    //   - index       = zero-based position (available for logging if needed)
    async (migrationResult, originalFile, _index) => {
      return agent(
        `Verify the migration of "${originalFile}": check that the file no longer ` +
        `contains any reference to "${fromApi}", that "${toApi}" call sites are ` +
        `syntactically correct, and that the file compiles without errors. ` +
        `Report the file path, whether verification passed, and list any errors found.`,
        {
          // Use originalFile (the raw input item) for the label — this is what
          // makes the (prevResult, originalItem, index) signature so valuable.
          label: 'verify:' + originalFile,
          // Haiku is sufficient for a lightweight verification / read-only check
          model: 'haiku',
          schema: VERIFY_SCHEMA
        }
      )
    }
  ])

  // ── 4. Phase "Report" ──────────────────────────────────────────────────────
  // Separate successes from failures. pipeline() yields null for failed items.

  const successes = results.filter(Boolean).filter(r => r.passed === true)
  const failures  = results.filter(Boolean).filter(r => r.passed === false)
  const skipped   = results.filter(r => !r).length

  const total    = files.length
  const migrated = successes.length
  const failed   = failures.length

  log('Migration complete.')
  log(`  Total files targeted : ${total}`)
  log(`  Successfully migrated: ${migrated}`)
  log(`  Failed               : ${failed}`)
  log(`  Skipped (errors)     : ${skipped}`)
  log(`  Dry run              : ${dryRun}`)

  if (failures.length > 0) {
    log('Failed files:')
    for (const r of failures) {
      log(`  - ${r.file}: ${(r.errors ?? []).join('; ') || 'unknown error'}`)
    }
  }

  return { total, migrated, failed, skipped, dryRun }
}
