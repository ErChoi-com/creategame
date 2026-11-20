// End-to-end check: start the server over stdio, call every tool, verify the persisted world.
// Uses a temp world file and port so it never touches your real world.json.
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const worldFile = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'creategame-')), 'world.json');
const transport = new StdioClientTransport({
  command: process.execPath,
  args: [new URL('./server.js', import.meta.url).pathname],
  env: { ...process.env, WORLD_FILE: worldFile, GAME_PORT: '18765' },
  stderr: 'ignore',
});
const client = new Client({ name: 'test', version: '0' });
await client.connect(transport);

const call = async (name, args = {}) => {
  const r = await client.callTool({ name, arguments: args });
  return { ...r, body: r.content[0].text };
};
const saved = () => JSON.parse(fs.readFileSync(worldFile, 'utf8'));

const { tools } = await client.listTools();
console.log('tools:', tools.map((t) => t.name).join(', '));

await call('reset_world');
await call('set_grid', { width: 6, depth: 5 });
assert.equal(saved().grid.width, 6);

await call('set_tile', { x: 2, z: 2, color: '#00ff00', height: 15 });
assert.deepEqual(saved().grid.tiles['2,2'], { color: '#00ff00', height: 15 });
await call('fill_tiles', { x1: 0, z1: 4, x2: 5, z2: 4, hidden: true });
assert.equal(Object.keys(saved().grid.tiles).length, 7);

await call('spawn_entity', { id: 'goal', type: 'cone', x: 5, z: 0, color: '#ffd400' });
await call('move_entity', { id: 'player', dx: 1, dz: 2 });
assert.deepEqual(saved().entities.find((e) => e.id === 'player'), { id: 'player', type: 'box', x: 1, z: 2, color: '#4287f5', size: 4 });

const oob = await call('move_entity', { id: 'player', x: 99, z: 0 });
assert.equal(oob.isError, true);
console.log('out-of-bounds error:', oob.body);

await call('update_entity', { id: 'goal', size: 6 });
await call('set_camera', { preset: 'isometric' });
await call('set_grid', { width: 4 }); // drops goal at x=5
assert.equal(saved().entities.some((e) => e.id === 'goal'), false);
await call('remove_entity', { id: 'player' });
assert.equal(saved().entities.length, 0);

await call('load_world', { world: { grid: { width: 3, depth: 3 }, entities: [{ id: 'a', type: 'sphere', x: 1, z: 1, color: '#ffffff', size: 3 }] } });
assert.equal(saved().grid.tileSize, 10); // defaults filled in
assert.equal(JSON.parse((await call('get_world')).body).entities[0].id, 'a');

const shot = await call('screenshot');
assert.equal(shot.isError, true); // no browser connected
console.log('screenshot without browser:', shot.body);

await client.close();
console.log('ok');
