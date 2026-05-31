export const meta = {
  name: 'parallel-hello-world',
  description: 'Hello World demo of parallel() — barrier between each stage, all items must finish before next stage starts',
  whenToUse: 'Run to see how parallel() works: all items complete Stage 1 before any item starts Stage 2 (barrier between stages).',
  phases: [
    { title: 'Greet', detail: 'All 3 names get greeted in parallel — barrier until all done' },
    { title: 'Shout', detail: 'All 3 greetings made enthusiastic in parallel — barrier until all done' },
    { title: 'Wrap', detail: 'All 3 results wrapped in parallel' },
  ],
}

const NAMES = ['Alice', 'Bob', 'Charlie']

// Stage 1 — Greet: ALL items run in parallel, then BARRIER
const greetings = await parallel(
  NAMES.map(name => () => agent(
    `Write a single short greeting for someone named ${name}. One sentence only.`,
    { label: `greet:${name}`, phase: 'Greet' }
  ))
)
log(`All greetings done: ${greetings.filter(Boolean).length}/3`)

// Stage 2 — Shout: ALL items run in parallel, then BARRIER
const shouts = await parallel(
  greetings.filter(Boolean).map((greeting, i) => () => agent(
    `Make this greeting more enthusiastic by adding exclamation marks and energy: "${greeting}"`,
    { label: `shout:${NAMES[i]}`, phase: 'Shout' }
  ))
)
log(`All shouts done: ${shouts.filter(Boolean).length}/3`)

// Stage 3 — Wrap: ALL items run in parallel
const wrapped = await parallel(
  shouts.filter(Boolean).map((shout, i) => () => agent(
    `Format this as a final welcome announcement for ${NAMES[i]}: "${shout}". One line only.`,
    { label: `wrap:${NAMES[i]}`, phase: 'Wrap' }
  ))
)

const valid = wrapped.filter(Boolean)

log('=== Parallel Results ===')
valid.forEach((r, i) => log(`${i + 1}. ${r}`))

return { results: valid }
