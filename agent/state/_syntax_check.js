const fs = require('fs');
const AsyncFunction = Object.getPrototypeOf(async function () {}).constructor;
for (const f of process.argv.slice(2)) {
  let src = fs.readFileSync(f, 'utf8').replace(/^export const meta = /m, 'const meta = ');
  try { new AsyncFunction('args', 'agent', 'parallel', 'pipeline', 'phase', 'log', 'workflow', 'budget', src); console.log(f + ': syntax ok'); }
  catch (e) { console.log(f + ': SYNTAX ERROR: ' + e.message); }
}
