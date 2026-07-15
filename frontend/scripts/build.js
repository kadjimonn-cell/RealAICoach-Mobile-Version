/* eslint-env node */
/* Build: assemble a standard static-site layout into ./build
   (index.html at root, per-route HTML files at their paths, client assets at root). */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(ROOT, 'build');
const SOURCES = [path.join(ROOT, 'rnw_dist'), path.resolve(ROOT, '..', 'mobile', 'dist')];

const src = SOURCES.find((d) => fs.existsSync(path.join(d, 'client')) || fs.existsSync(path.join(d, 'index.html')));
if (!src) {
  console.error('FATAL: no UI bundle found. Run `yarn sync:rnw` after exporting the mobile web bundle.');
  process.exit(1);
}

const noPrecompressed = (p) => !p.endsWith('.br') && !p.endsWith('.gz');
fs.rmSync(OUT, { recursive: true, force: true });

const clientDir = path.join(src, 'client');
const serverDir = path.join(src, 'server');

if (fs.existsSync(clientDir)) {
  fs.cpSync(clientDir, OUT, { recursive: true, filter: noPrecompressed });
  if (fs.existsSync(serverDir)) {
    fs.cpSync(serverDir, OUT, { recursive: true, filter: noPrecompressed });
  }
} else {
  fs.cpSync(src, OUT, { recursive: true, filter: noPrecompressed });
}

if (!fs.existsSync(path.join(OUT, 'index.html'))) {
  console.error('FATAL: build output has no root index.html');
  process.exit(1);
}
console.log(`Web build assembled (static-site layout): ${src} -> ${OUT}`);
