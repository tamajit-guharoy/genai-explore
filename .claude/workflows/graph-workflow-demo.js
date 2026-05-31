export const meta = {
  name: 'graph-workflow-demo',
  description: 'State-machine graph: Supervisor → Developer ⟷ Validator → Executor ⟷ Developer',
  whenToUse: 'Demonstrates a complex graph workflow with two conditional loops: dev↔validator and dev↔executor.',
  phases: [
    { title: 'Supervise', detail: 'Supervisor parses the user request into a clear task' },
    { title: 'Develop', detail: 'Developer writes or fixes code' },
    { title: 'Validate', detail: 'Validator reviews and approves or rejects' },
    { title: 'Execute', detail: 'Executor runs the code and reports success or failure' },
  ],
}

const USER_REQUEST = 'Write a JavaScript function that finds the longest word in a sentence.'
const MAX_DEV_LOOPS = 3
const MAX_EXEC_LOOPS = 3

const BOOL_SCHEMA = {
  type: 'object',
  properties: {
    approved: { type: 'boolean' },
    feedback: { type: 'string' },
  },
  required: ['approved', 'feedback'],
}

// ── State machine ──────────────────────────────────────────────
// Nodes: SUPERVISE → DEVELOP → VALIDATE → EXECUTE → DONE
// Edges:
//   VALIDATE rejected  → DEVELOP  (loop 1)
//   EXECUTE  failed    → DEVELOP  (loop 2)
//   EXECUTE  succeeded → DONE

let state = 'SUPERVISE'
let task = ''
let code = ''
let validatorFeedback = ''
let executorFeedback = ''
let devIteration = 0
let execIteration = 0

while (state !== 'DONE') {

  // ── Node: SUPERVISE ──────────────────────────────────────────
  if (state === 'SUPERVISE') {
    phase('Supervise')
    task = await agent(
      `You are a supervisor. The user said: "${USER_REQUEST}". Rewrite this as a precise, unambiguous technical task for a developer. One paragraph.`,
      { label: 'supervisor', phase: 'Supervise' }
    )
    log(`Supervisor defined task: ${task}`)
    state = 'DEVELOP'

  // ── Node: DEVELOP ────────────────────────────────────────────
  } else if (state === 'DEVELOP') {
    devIteration++
    if (devIteration > MAX_DEV_LOOPS) {
      log(`Max dev iterations (${MAX_DEV_LOOPS}) reached — stopping.`)
      break
    }
    phase('Develop')
    const devPrompt = executorFeedback
      ? `Task: ${task}\n\nYour previous code failed execution:\n${code}\n\nExecution error: ${executorFeedback}\n\nFix the code.`
      : validatorFeedback
        ? `Task: ${task}\n\nYour previous code was rejected by the validator:\n${code}\n\nFeedback: ${validatorFeedback}\n\nImprove the code.`
        : `Task: ${task}\n\nWrite clean JavaScript code. Return only the code, no explanation.`

    code = await agent(devPrompt, { label: `developer:v${devIteration}`, phase: 'Develop' })
    validatorFeedback = ''
    executorFeedback = ''
    log(`Developer wrote code (v${devIteration})`)
    state = 'VALIDATE'

  // ── Node: VALIDATE ───────────────────────────────────────────
  } else if (state === 'VALIDATE') {
    phase('Validate')
    const review = await agent(
      `You are a strict code reviewer. Task: "${task}"\n\nCode to review:\n${code}\n\nApprove only if it is correct, clean, and handles edge cases. Be critical.`,
      { label: `validator:v${devIteration}`, phase: 'Validate', schema: BOOL_SCHEMA }
    )
    log(`Validator: ${review.approved ? 'APPROVED' : 'REJECTED'} — ${review.feedback}`)
    if (review.approved) {
      state = 'EXECUTE'
    } else {
      validatorFeedback = review.feedback
      state = 'DEVELOP'
    }

  // ── Node: EXECUTE ────────────────────────────────────────────
  } else if (state === 'EXECUTE') {
    execIteration++
    if (execIteration > MAX_EXEC_LOOPS) {
      log(`Max exec iterations (${MAX_EXEC_LOOPS}) reached — stopping.`)
      break
    }
    phase('Execute')
    const execResult = await agent(
      `You are a code executor. Mentally run this JavaScript code and check for runtime errors, wrong output, or edge case failures:\n\n${code}\n\nReport whether it succeeds or fails with a specific reason.`,
      { label: `executor:run${execIteration}`, phase: 'Execute', schema: BOOL_SCHEMA }
    )
    log(`Executor: ${execResult.approved ? 'SUCCESS' : 'FAILED'} — ${execResult.feedback}`)
    if (execResult.approved) {
      state = 'DONE'
    } else {
      executorFeedback = execResult.feedback
      state = 'DEVELOP'
    }
  }
}

log(state === 'DONE'
  ? `Graph completed successfully in ${devIteration} dev iteration(s) and ${execIteration} execution(s).`
  : `Graph stopped early after ${devIteration} dev iteration(s).`
)

return { finalCode: code, devIterations: devIteration, execIterations: execIteration, completed: state === 'DONE' }
