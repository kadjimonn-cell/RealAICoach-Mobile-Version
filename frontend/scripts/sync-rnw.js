/* eslint-env node */
/* Sync the latest mobile web export (../mobile/dist) into ./rnw_dist (pruning precompressed files). */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const SRC = path.resolve(ROOT, '..', 'mobile', 'dist');
const DEST = path.join(ROOT, 'rnw_dist');

if (!fs.existsSync(path.join(SRC, 'client')) && !fs.existsSync(path.join(SRC, 'index.html'))) {
  console.error('FATAL: ../mobile/dist not found or missing index.html. Run `yarn export:web` in /app/mobile first.');
  process.exit(1);
}

fs.rmSync(DEST, { recursive: true, force: true });
fs.cpSync(SRC, DEST, {
  recursive: true,
  filter: (p) => !p.endsWith('.br') && !p.endsWith('.gz'),
});
console.log(`Synced ${SRC} -> ${DEST}`);

const { execFileSync } = require('child_process');
execFileSync('node', [path.join(__dirname, 'seo.js'), DEST], { stdio: 'inherit' });
