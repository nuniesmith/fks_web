#!/usr/bin/env node
// Simple ESLint JSON reporter summarizer (CommonJS)
let input = ''
process.stdin.setEncoding('utf8')
process.stdin.on('data', chunk => (input += chunk))
process.stdin.on('end', () => {
  try {
    const results = JSON.parse(input)
    let warn = 0, err = 0
    const ruleCounts = {}
    for (const file of results) {
      for (const m of file.messages) {
        if (m.severity === 2) err++
        else warn++
        const id = m.ruleId || 'unknown'
        ruleCounts[id] = (ruleCounts[id] || 0) + 1
      }
    }
    const top = Object.entries(ruleCounts)
      .sort((a,b)=>b[1]-a[1])
      .slice(0,15)
      .map(([rule,count])=>({ rule, count }))
    console.log(JSON.stringify({ errors: err, warnings: warn, topRules: top }, null, 2))
  } catch (e) {
    console.error('Failed to parse ESLint JSON input', e)
    process.exit(1)
  }
})
