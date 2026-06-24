// .archon/scripts/parse-labels.ts
// TypeScript script node (runtime: bun)
// Parses GitHub issue JSON and extracts label information.
//
// Usage in workflow:
//   - id: parse-labels
//     script: parse-labels        # Named reference to this file
//     runtime: bun
//     depends_on: [fetch-issue]
//     timeout: 10000
//
// Or inline:
//   - id: parse-labels
//     script: |
//       try {
//         const issue = $fetch-issue.output;
//         ...
//

try {
  // "$fetch-issue.output" is injected RAW at runtime by Archon.
  // JSON is valid JS — assign directly. Do NOT use String.raw or JSON.parse.
  // In this file, it's a placeholder that Archon substitutes at execution time.
  const issue = {"labels": [], "title": "", "body": ""}; // $fetch-issue.output (substituted at runtime)

  const labels = (issue.labels ?? []).map((l: any) => l.name);
  const hasBug = labels.includes("bug");
  const hasUrgent = labels.includes("urgent");
  const hasEnhancement = labels.includes("enhancement");

  console.log(JSON.stringify({
    labels,
    count: labels.length,
    hasBug,
    hasUrgent,
    hasEnhancement,
    priority: hasUrgent ? "urgent" : hasBug ? "high" : "normal"
  }));
} catch {
  // If parsing fails (e.g., empty or malformed input), return safe defaults
  console.log(JSON.stringify({
    labels: [],
    count: 0,
    hasBug: false,
    hasUrgent: false,
    hasEnhancement: false,
    priority: "unknown"
  }));
}
