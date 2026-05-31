export const meta = {
  name: 'dev-review-loop',
  description: 'Developer writes code, reviewer critiques it, loop until reviewer is satisfied',
  whenToUse: 'Run to see how a dev-review feedback loop works using while loop inside a workflow.',
  phases: [
    { title: 'Develop', detail: 'Developer agent writes or improves the code' },
    { title: 'Review', detail: 'Reviewer agent checks the code and decides if it is acceptable' },
  ],
}

const TASK = 'Write a JavaScript function that reverses a string'
const MAX_ITERATIONS = 5

const REVIEW_SCHEMA = {
  type: 'object',
  properties: {
    approved: { type: 'boolean' },
    feedback: { type: 'string' },
  },
  required: ['approved', 'feedback'],
}

let code = ''
let iteration = 0
let approved = false

while (!approved && iteration < MAX_ITERATIONS) {
  iteration++
  log(`--- Iteration ${iteration} ---`)

  // Developer agent: write or improve based on previous feedback
  phase('Develop')
  const developerPrompt = iteration === 1
    ? `You are a developer. Complete this task: "${TASK}". Write clean, well-structured code only.`
    : `You are a developer. Improve this code based on the reviewer's feedback.\n\nCurrent code:\n${code}\n\nReviewer feedback: ${feedback}\n\nReturn only the improved code.`

  code = await agent(developerPrompt, { label: `dev:iteration-${iteration}`, phase: 'Develop' })
  log(`Developer produced code (iteration ${iteration})`)

  // Reviewer agent: review the code and decide
  phase('Review')
  const review = await agent(
    `You are a strict code reviewer. Review this code for the task "${TASK}":\n\n${code}\n\nBe critical. Approve only if the code is clean, correct, and handles edge cases.`,
    { label: `review:iteration-${iteration}`, phase: 'Review', schema: REVIEW_SCHEMA }
  )

  approved = review.approved
  var feedback = review.feedback

  log(`Reviewer decision: ${approved ? 'APPROVED' : 'REJECTED'} — ${feedback}`)
}

log(approved
  ? `Approved after ${iteration} iteration(s)!`
  : `Max iterations (${MAX_ITERATIONS}) reached without approval.`
)

return { approved, iterations: iteration, finalCode: code }
