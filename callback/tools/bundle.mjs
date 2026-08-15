// Bundle the game into one self-contained HTML file.
//
//   node callback/tools/bundle.mjs [out.html]
//
// The played version loads engine/*.js as ES modules from a server. That is the
// right shape for the source and the wrong shape for handing someone a game, so
// this flattens the modules into a single <script> with no imports, inlines the
// stylesheet, and emits one file that runs from a double-click or a URL.
//
// It is deliberately dumb: it strips import/export syntax, builds the one
// namespace object the code expects, and refuses to guess when two modules
// declare the same top-level name.

import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '..');
const out = process.argv[2] || resolve(root, 'dist/callback.html');
// Hosted artifact pages are wrapped in their own document skeleton, so that
// build emits content only — same game, no <html>/<head>/<body> of its own.
const forArtifact = process.argv.includes('--artifact');

// Dependency order. Anything that reads a name must come after the file that
// declares it, since the bundle is one flat scope.
const MODULES = [
  'engine/rng.js',
  'engine/data.js',
  'engine/model.js',
  'engine/rolodex.js',
  'engine/ambition.js',
  'engine/events.js',
  'engine/arcs.js',
  'engine/world.js',
  'engine/leverage.js',
  'engine/career.js',
  'web/app.js',
];

const read = (rel) => readFileSync(resolve(root, rel), 'utf8');

// --- strip module syntax ----------------------------------------------------
function flatten(src) {
  return src
    // import { a, b } from './x.js';   /   import * as M from './x.js';
    .replace(/^\s*import\s+[\s\S]*?from\s+['"][^'"]+['"];?\s*$/gm, '')
    .replace(/^\s*import\s+['"][^'"]+['"];?\s*$/gm, '')
    // export const / function / class  ->  const / function / class
    .replace(/^export\s+(const|let|function|class|async)\b/gm, '$1')
    // export { a, b };  ->  dropped entirely (re-exports mean nothing here)
    .replace(/^export\s*\{[^}]*\}\s*;?\s*$/gm, '');
}

// Top-level declarations, for collision detection.
function declarations(src) {
  const names = new Set();
  const re = /^(?:const|let|var|function|class)\s+([A-Za-z_$][\w$]*)/gm;
  let m;
  while ((m = re.exec(src))) names.add(m[1]);
  return names;
}

// The engine is written against `M.something` for the model's namespace import;
// rebuild that object from what model.js actually exports.
function modelNamespace(modelSrc) {
  const names = [...modelSrc.matchAll(/^export\s+(?:const|function)\s+([A-Za-z_$][\w$]*)/gm)]
    .map((m) => m[1]);
  return `\n// namespace shim for what was \`import * as M from './model.js'\`\nconst M = { ${names.join(', ')} };\n`;
}

const pieces = [];
const seen = new Map();
let collisions = 0;

for (const rel of MODULES) {
  const raw = read(rel);
  for (const name of declarations(flatten(raw))) {
    if (seen.has(name)) {
      console.error(`collision: ${name} declared in both ${seen.get(name)} and ${rel}`);
      collisions += 1;
    } else seen.set(name, rel);
  }
  pieces.push(`\n/* ===== ${rel} ===== */\n${flatten(raw)}`);
  if (rel === 'engine/model.js') pieces.push(modelNamespace(raw));
}

if (collisions) {
  console.error(`\n${collisions} name collision(s). Rename in the source, not here.`);
  process.exit(1);
}

// --- assemble ---------------------------------------------------------------
const css = read('web/style.css');
const html = read('web/index.html');

// Take the body markup from the real page so the two never drift.
const body = html.slice(html.indexOf('<body>') + 6, html.indexOf('</body>')).trim();

const script = `<script>
"use strict";
(function () {
${pieces.join('\n')}
}());
</${'script'}>`;

const page = forArtifact
  ? `<title>Callback</title>
<style>
${css}
</style>
${body}
${script}
`
  : `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Callback</title>
<style>
${css}
</style>
</head>
<body>
${body}
${script}
</body>
</html>
`;

mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, page);
console.log('%s — %d KB, %d modules, no external requests',
  out, Math.round(page.length / 1024), MODULES.length);
