export const meta = {
  name: 'world-capitals',
  description: 'Ask 3 subagents for capitals of France, Germany, and Japan, then consolidate',
  whenToUse: 'Run to fetch and consolidate the capitals of France, Germany, and Japan using parallel subagents.',
  phases: [
    { title: 'Ask', detail: 'Three parallel agents each ask for a country capital' },
    { title: 'Consolidate', detail: 'Merge results into a single response' },
  ],
}

phase('Ask')

const SCHEMA = {
  type: 'object',
  properties: {
    country: { type: 'string' },
    capital: { type: 'string' },
  },
  required: ['country', 'capital'],
}

const results = await parallel([
  () => agent('What is the capital of France? Return only the country name and its capital.', { label: 'France', phase: 'Ask', schema: SCHEMA }),
  () => agent('What is the capital of Germany? Return only the country name and its capital.', { label: 'Germany', phase: 'Ask', schema: SCHEMA }),
  () => agent('What is the capital of Japan? Return only the country name and its capital.', { label: 'Japan', phase: 'Ask', schema: SCHEMA }),
])

phase('Consolidate')

const valid = results.filter(Boolean)

const consolidated = await agent(
  `Summarize these country capitals into a clean list: ${JSON.stringify(valid)}`,
  { label: 'Summarize', phase: 'Consolidate' }
)

log('tamajit==============================')

log(consolidated)

return { capitals: valid, summary: consolidated }
