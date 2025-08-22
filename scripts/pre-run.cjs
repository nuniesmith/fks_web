#!/usr/bin/env node
/**
 * Safe pre-run script for web service.
 * Attempts to execute the repo-level sync-docs.js if present; otherwise no-ops.
 * This prevents container restarts when only the web subfolder is bind-mounted.
 */
// eslint-disable-next-line @typescript-eslint/no-var-requires
const fs = require('fs');
// eslint-disable-next-line @typescript-eslint/no-var-requires
const path = require('path');

const cwd = process.cwd();
// Resolve to repo root assuming CWD is src/web/react
const repoRoot = path.resolve(cwd, '../../../');
const syncScript = path.join(repoRoot, 'scripts', 'sync-docs.js');

try {
  if (fs.existsSync(syncScript)) {
    // Execute the real sync script
    require(syncScript);
  } else {
    // Optional: fallback to copy docs if available under /app/src/docs
    const srcDocs = path.join(repoRoot, 'src', 'docs');
    const destDocs = path.join(cwd, 'public', 'docs');
    if (fs.existsSync(srcDocs)) {
      const ensureDir = (p) => fs.existsSync(p) || fs.mkdirSync(p, { recursive: true });
      const copyHtml = (from, to) => {
        ensureDir(to);
        const entries = fs.readdirSync(from, { withFileTypes: true });
        for (const e of entries) {
          const s = path.join(from, e.name);
          const d = path.join(to, e.name);
          if (e.isDirectory()) copyHtml(s, d);
          else if (e.isFile() && e.name.toLowerCase().endsWith('.html')) fs.copyFileSync(s, d);
        }
      };
      copyHtml(srcDocs, destDocs);
      console.log('[docs] fallback copy complete');
    } else {
      console.log('[docs] skip: sync-docs.js not found and no src/docs directory present');
    }
  }
} catch (err) {
  console.log('[docs] skip due to error:', err && err.message ? err.message : err);
}
