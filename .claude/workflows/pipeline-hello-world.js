export const meta = {
  name: 'pipeline-hello-world',
  description: 'Hello World demo of pipeline() — items flow through 3 stages sequentially',
  whenToUse: 'Run to see how pipeline() works: each item passes through Stage 1 → Stage 2 → Stage 3 independently.',
  phases: [
    { title: 'Greet', detail: 'Each name gets a greeting message' },
    { title: 'Shout', detail: 'Each greeting is made enthusiastic' },
    { title: 'Wrap', detail: 'Each result is wrapped in a final summary' },
  ],
}

// Items to process — each one flows through all 3 stages independently
const NAMES = ['Alice', 'Bob', 'Charlie']

const results = await pipeline(
  NAMES,

  // Stage 1 — Greet: turn a name into a greeting
  name => agent(
    `Write a single short greeting for someone named ${name}. One sentence only.`,
    { label: `greet:${name}`, phase: 'Greet' }
  ),

  // Stage 2 — Shout: make the greeting enthusiastic (receives stage 1 result)
  (greeting, originalName) => agent(
    `Make this greeting more enthusiastic by adding exclamation marks and energy: "${greeting}"`,
    { label: `shout:${originalName}`, phase: 'Shout' }
  ),

  // Stage 3 — Wrap: produce final summary line (receives stage 2 result)
  (shout, originalName) => agent(
    `Format this as a final welcome announcement for ${originalName}: "${shout}". One line only.`,
    { label: `wrap:${originalName}`, phase: 'Wrap' }
  )
)

const valid = results.filter(Boolean)

log('=== Pipeline Results ===')
valid.forEach((r, i) => log(`${i + 1}. ${r}`))

return { results: valid }
