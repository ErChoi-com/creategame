#!/usr/bin/env node
// MCP server for the creategame Three.js world.
//
// One process does three things:
//   1. Speaks MCP over stdio, so Claude (or any MCP client) can inspect and edit the world.
//   2. Serves the game's static files over HTTP (replaces `python -m http.server 8000`).
//   3. Pushes every world change to open browser tabs over WebSocket (/ws), and asks a tab
//      for a screenshot when the `screenshot` tool is called.
//
// The world is persisted to ../world.json, so the game also loads it under a plain static server.
//
// NOTE: stdout is the MCP channel. Log only with console.error.

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { WebSocketServer } from 'ws';
import { z } from 'zod';
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const GAME_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const WORLD_FILE = process.env.WORLD_FILE ? path.resolve(process.env.WORLD_FILE) : path.join(GAME_ROOT, 'world.json');
const PORT = Number(process.env.GAME_PORT || 8000);
const MAX_GRID = 64;

// ---------------------------------------------------------------- world state

const DEFAULT_WORLD = {
  grid: { width: 10, depth: 10, tileSize: 10, gap: 1, tileHeight: 10, color: '#ffffff', tiles: {} },
  entities: [{ id: 'player', type: 'box', x: 0, z: 0, color: '#4287f5', size: 4 }],
  camera: 'orbit',
};

const clone = (o) => JSON.parse(JSON.stringify(o));

function loadWorld() {
  try {
    return { ...clone(DEFAULT_WORLD), ...JSON.parse(fs.readFileSync(WORLD_FILE, 'utf8')) };
  } catch {
    return clone(DEFAULT_WORLD);
  }
}

let world = loadWorld();

function commit() {
  const tmp = WORLD_FILE + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(world, null, 2) + '\n');
  fs.renameSync(tmp, WORLD_FILE);
  broadcast({ type: 'world', world });
}

const tileKey = (x, z) => `${x},${z}`;

function assertInGrid(x, z) {
  const { width, depth } = world.grid;
  if (x < 0 || z < 0 || x >= width || z >= depth) {
    throw new Error(`(${x}, ${z}) is outside the ${width}x${depth} grid (valid x 0-${width - 1}, z 0-${depth - 1})`);
  }
}

function findEntity(id) {
  const e = world.entities.find((en) => en.id === id);
  if (!e) throw new Error(`No entity "${id}". Existing: ${world.entities.map((en) => en.id).join(', ') || 'none'}`);
  return e;
}

// ---------------------------------------------------------------- http + websocket

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.json': 'application/json',
  '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml', '.glb': 'model/gltf-binary',
};

const httpServer = http.createServer((req, res) => {
  const urlPath = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  if (urlPath === '/world.json') {
    res.writeHead(200, { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' });
    return res.end(JSON.stringify(world));
  }
  const file = path.join(GAME_ROOT, urlPath === '/' ? 'index.html' : urlPath);
  const rel = path.relative(GAME_ROOT, file);
  if (rel.startsWith('..') || path.isAbsolute(rel) || rel.split(path.sep).some((p) => p.startsWith('.') || p === 'node_modules' || p === 'mcp-server')) {
    res.writeHead(403);
    return res.end('Forbidden');
  }
  fs.readFile(file, (err, data) => {
    if (err) {
      res.writeHead(404);
      return res.end('Not found');
    }
    res.writeHead(200, { 'Content-Type': MIME[path.extname(file)] || 'application/octet-stream', 'Cache-Control': 'no-store' });
    res.end(data);
  });
});

const wss = new WebSocketServer({ server: httpServer, path: '/ws' });
const pendingShots = new Map(); // requestId -> {resolve, reject, timer}
let nextShotId = 1;

wss.on('connection', (ws) => {
  ws.send(JSON.stringify({ type: 'world', world }));
  ws.on('message', (raw) => {
    let msg;
    try { msg = JSON.parse(raw); } catch { return; }
    if (msg.type === 'screenshot' && pendingShots.has(msg.id)) {
      const p = pendingShots.get(msg.id);
      pendingShots.delete(msg.id);
      clearTimeout(p.timer);
      msg.error ? p.reject(new Error(msg.error)) : p.resolve(msg.data);
    }
  });
});

function broadcast(msg) {
  const data = JSON.stringify(msg);
  for (const c of wss.clients) if (c.readyState === 1) c.send(data);
}

function requestScreenshot() {
  const client = [...wss.clients].find((c) => c.readyState === 1);
  if (!client) {
    return Promise.reject(new Error(`No browser is connected. Open http://localhost:${PORT}/ and try again.`));
  }
  const id = nextShotId++;
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      pendingShots.delete(id);
      reject(new Error('Browser did not return a screenshot within 5s (is the tab in the background?)'));
    }, 5000);
    pendingShots.set(id, { resolve, reject, timer });
    client.send(JSON.stringify({ type: 'screenshot', id }));
  });
}

httpServer.on('error', (err) => {
  // A second instance (or python http.server) may already hold the port. MCP tools still work;
  // changes are saved to world.json and picked up on reload.
  console.error(`[creategame-mcp] HTTP server not started on :${PORT}: ${err.message}`);
});
httpServer.listen(PORT, () => console.error(`[creategame-mcp] game at http://localhost:${PORT}/`));

// ---------------------------------------------------------------- MCP tools

const mcp = new McpServer({ name: 'creategame', version: '0.1.0' });

const text = (t) => ({ content: [{ type: 'text', text: typeof t === 'string' ? t : JSON.stringify(t, null, 2) }] });

// Run a mutation; on success persist + broadcast, on failure report the error to the model.
function tool(name, description, inputSchema, fn) {
  mcp.registerTool(name, { description, inputSchema }, async (args) => {
    try {
      return await fn(args);
    } catch (err) {
      return { isError: true, content: [{ type: 'text', text: err.message }] };
    }
  });
}

const color = z.string().regex(/^#[0-9a-fA-F]{6}$/).describe('Hex color like #ff8800');
const gx = z.number().int().min(0).describe('Grid column (0 = first)');
const gz = z.number().int().min(0).describe('Grid row (0 = first)');

tool('get_world', 'Return the full world state: grid, per-tile overrides, entities and camera.', {}, () => text(world));

tool(
  'set_grid',
  'Change grid settings. Shrinking the grid drops tile overrides and entities outside the new bounds.',
  {
    width: z.number().int().min(1).max(MAX_GRID).optional(),
    depth: z.number().int().min(1).max(MAX_GRID).optional(),
    tileSize: z.number().positive().max(100).optional().describe('Tile footprint in world units'),
    gap: z.number().min(0).max(20).optional().describe('Space between tiles'),
    tileHeight: z.number().positive().max(100).optional().describe('Default tile height'),
    color: color.optional().describe('Default tile color'),
  },
  (args) => {
    Object.assign(world.grid, Object.fromEntries(Object.entries(args).filter(([, v]) => v !== undefined)));
    const { width, depth } = world.grid;
    for (const k of Object.keys(world.grid.tiles)) {
      const [x, z] = k.split(',').map(Number);
      if (x >= width || z >= depth) delete world.grid.tiles[k];
    }
    const dropped = world.entities.filter((e) => e.x >= width || e.z >= depth).map((e) => e.id);
    world.entities = world.entities.filter((e) => e.x < width && e.z < depth);
    commit();
    return text(`Grid is now ${width}x${depth}.${dropped.length ? ` Removed out-of-bounds entities: ${dropped.join(', ')}` : ''}`);
  },
);

tool(
  'set_tile',
  'Override one tile\'s color and/or height, or hide it (a hole). Pass reset=true to restore the default.',
  {
    x: gx, z: gz,
    color: color.optional(),
    height: z.number().min(0).max(100).optional().describe('Tile height; 0 hides the tile'),
    hidden: z.boolean().optional().describe('Remove the tile (a hole)'),
    reset: z.boolean().optional().describe('Clear all overrides on this tile'),
  },
  ({ x, z: zz, reset, ...over }) => {
    assertInGrid(x, zz);
    const k = tileKey(x, zz);
    if (reset) delete world.grid.tiles[k];
    else {
      const t = { ...world.grid.tiles[k] };
      for (const [key, v] of Object.entries(over)) if (v !== undefined) t[key] = v;
      world.grid.tiles[k] = t;
    }
    commit();
    return text(`Tile ${k}: ${JSON.stringify(world.grid.tiles[k] || 'default')}`);
  },
);

tool(
  'fill_tiles',
  'Apply the same override to a rectangle of tiles (inclusive bounds). Handy for walls, paths and pits.',
  {
    x1: gx, z1: gz, x2: gx, z2: gz,
    color: color.optional(),
    height: z.number().min(0).max(100).optional(),
    hidden: z.boolean().optional(),
    reset: z.boolean().optional(),
  },
  ({ x1, z1, x2, z2, reset, ...over }) => {
    assertInGrid(x1, z1);
    assertInGrid(x2, z2);
    let n = 0;
    for (let x = Math.min(x1, x2); x <= Math.max(x1, x2); x++) {
      for (let zz = Math.min(z1, z2); zz <= Math.max(z1, z2); zz++, n++) {
        const k = tileKey(x, zz);
        if (reset) delete world.grid.tiles[k];
        else {
          const t = { ...world.grid.tiles[k] };
          for (const [key, v] of Object.entries(over)) if (v !== undefined) t[key] = v;
          world.grid.tiles[k] = t;
        }
      }
    }
    commit();
    return text(`Updated ${n} tiles.`);
  },
);

tool(
  'spawn_entity',
  'Place a new entity on a tile. It sits on top of the tile.',
  {
    id: z.string().min(1).optional().describe('Unique id; generated if omitted'),
    type: z.enum(['box', 'sphere', 'cone']).default('box'),
    x: gx, z: gz,
    color: color.default('#e94f37'),
    size: z.number().positive().max(100).default(4),
  },
  ({ id, ...e }) => {
    assertInGrid(e.x, e.z);
    id ??= `${e.type}-${Date.now().toString(36)}`;
    if (world.entities.some((en) => en.id === id)) throw new Error(`Entity "${id}" already exists`);
    world.entities.push({ id, ...e });
    commit();
    return text(`Spawned ${id} at (${e.x}, ${e.z}).`);
  },
);

tool(
  'move_entity',
  'Move an entity to a tile (x/z), or by an offset (dx/dz).',
  {
    id: z.string(),
    x: gx.optional(), z: gz.optional(),
    dx: z.number().int().optional(), dz: z.number().int().optional(),
  },
  ({ id, x, z: zz, dx = 0, dz = 0 }) => {
    const e = findEntity(id);
    const nx = (x ?? e.x) + dx;
    const nz = (zz ?? e.z) + dz;
    assertInGrid(nx, nz);
    e.x = nx;
    e.z = nz;
    commit();
    return text(`${id} is at (${nx}, ${nz}).`);
  },
);

tool(
  'update_entity',
  'Change an entity\'s color, size or type.',
  { id: z.string(), color: color.optional(), size: z.number().positive().max(100).optional(), type: z.enum(['box', 'sphere', 'cone']).optional() },
  ({ id, ...changes }) => {
    const e = findEntity(id);
    for (const [k, v] of Object.entries(changes)) if (v !== undefined) e[k] = v;
    commit();
    return text(e);
  },
);

tool('remove_entity', 'Delete an entity by id.', { id: z.string() }, ({ id }) => {
  findEntity(id);
  world.entities = world.entities.filter((e) => e.id !== id);
  commit();
  return text(`Removed ${id}.`);
});

tool(
  'set_camera',
  'Switch the camera preset in every open browser tab.',
  { preset: z.enum(['orbit', 'isometric', 'top']) },
  ({ preset }) => {
    world.camera = preset;
    commit();
    return text(`Camera: ${preset}`);
  },
);

tool(
  'load_world',
  'Replace the whole world with the given JSON (same shape as get_world returns). Use for building a level in one call.',
  { world: z.object({ grid: z.object({}).passthrough(), entities: z.array(z.object({}).passthrough()), camera: z.string().optional() }).passthrough() },
  ({ world: next }) => {
    const merged = clone(DEFAULT_WORLD);
    merged.grid = { ...merged.grid, ...next.grid, tiles: next.grid.tiles || {} };
    merged.entities = next.entities;
    merged.camera = next.camera || 'orbit';
    if (merged.grid.width > MAX_GRID || merged.grid.depth > MAX_GRID) throw new Error(`Grid max is ${MAX_GRID}x${MAX_GRID}`);
    world = merged;
    commit();
    return text(`Loaded world: ${world.grid.width}x${world.grid.depth}, ${world.entities.length} entities.`);
  },
);

tool('reset_world', 'Restore the default 10x10 world with a single player box.', {}, () => {
  world = clone(DEFAULT_WORLD);
  commit();
  return text('World reset.');
});

tool(
  'screenshot',
  `Capture what the game currently looks like, from an open browser tab (http://localhost:${PORT}/).`,
  {},
  async () => {
    const dataUrl = await requestScreenshot();
    return { content: [{ type: 'image', data: dataUrl.split(',')[1], mimeType: 'image/png' }] };
  },
);

await mcp.connect(new StdioServerTransport());
