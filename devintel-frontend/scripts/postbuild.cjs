/**
 * Post-build script: copies index.html to all client-side route paths.
 *
 * When a static host (Vercel, Netlify, etc.) receives a request for
 * /oauth/callback, it looks for a physical file at that path.  If
 * none exists and no rewrite rule is configured, it returns 404.
 *
 * This script creates dist/<route>/index.html for every SPA route
 * so the host always finds a file to serve — React Router then
 * handles the routing client-side.
 *
 * This is the most reliable SPA fallback strategy because it works
 * regardless of hosting provider configuration.
 */

const fs = require('fs');
const path = require('path');

const DIST = path.join(__dirname, '..', 'dist');
const INDEX = path.join(DIST, 'index.html');

// All client-side routes that might be hit via direct navigation or redirects.
// Add new routes here as they are created.
const SPA_ROUTES = [
  'oauth/callback',
  'login',
  'signup',
  'dashboard',
];

if (!fs.existsSync(INDEX)) {
  console.error('ERROR: dist/index.html not found — run vite build first.');
  process.exit(1);
}

const html = fs.readFileSync(INDEX, 'utf-8');

for (const route of SPA_ROUTES) {
  const dir = path.join(DIST, route);
  const file = path.join(dir, 'index.html');

  // Skip if the file already exists (avoid overwriting real pages)
  if (fs.existsSync(file)) {
    console.log(`  [skip] ${route}/index.html (already exists)`);
    continue;
  }

  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(file, html);
  console.log(`  [copy] ${route}/index.html`);
}

console.log('SPA route files created successfully.');
