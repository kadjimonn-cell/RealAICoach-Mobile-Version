/* eslint-env node */
/* RealAICoach web frontend server: serves the cross-platform UI bundle (Expo SSG layout: client/ + server/) on port 3000. */
const express = require('express');
const compression = require('compression');
const path = require('path');
const fs = require('fs');

const PORT = Number(process.env.PORT || 3000);

const CANDIDATE_DIRS = [
  path.join(__dirname, 'build'),
  path.join(__dirname, 'rnw_dist'),
  path.resolve(__dirname, '..', 'mobile', 'dist'),
];
const DIST_DIR = CANDIDATE_DIRS.find((d) => fs.existsSync(path.join(d, 'client')) || fs.existsSync(path.join(d, 'index.html')));

if (!DIST_DIR) {
  console.error('FATAL: no static UI bundle found in', CANDIDATE_DIRS);
  process.exit(1);
}

const CLIENT_DIR = fs.existsSync(path.join(DIST_DIR, 'client')) ? path.join(DIST_DIR, 'client') : DIST_DIR;
const SERVER_DIR = path.join(DIST_DIR, 'server');

const app = express();
app.disable('x-powered-by');
app.use(compression());

app.get('/healthz', (_req, res) => res.json({ ok: true, dist_dir: DIST_DIR }));

app.use(
  express.static(CLIENT_DIR, {
    index: false,
    maxAge: '1h',
    setHeaders: (res, filePath) => {
      if (filePath.endsWith('.html')) res.setHeader('Cache-Control', 'no-cache');
      if (/\.(js|css)$/.test(filePath) && /-[a-f0-9]{8,}\./.test(path.basename(filePath))) {
        res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
      }
    },
  })
);

function resolveRouteHtml(reqPath) {
  const clean = String(reqPath || '/').split('?')[0].replace(/\/+$/, '') || '/';
  const candidates = clean === '/'
    ? [path.join(SERVER_DIR, 'index.html')]
    : [
        path.join(SERVER_DIR, `${clean}.html`),
        path.join(SERVER_DIR, clean, 'index.html'),
        path.join(CLIENT_DIR, `${clean}.html`),
        path.join(CLIENT_DIR, clean, 'index.html'),
        path.join(SERVER_DIR, 'index.html'),
      ];
  candidates.push(path.join(CLIENT_DIR, 'index.html'));
  return candidates.find((c) => c.startsWith(DIST_DIR) && fs.existsSync(c));
}

app.get('*', (req, res, next) => {
  if (req.path.startsWith('/api')) return next();
  const html = resolveRouteHtml(req.path);
  if (!html) return res.status(404).send('Not found');
  res.setHeader('Cache-Control', 'no-cache');
  res.sendFile(html);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`RealAICoach web frontend serving ${DIST_DIR} on port ${PORT}`);
});
