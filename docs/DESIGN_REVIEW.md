# Design Review: creategame prototype

Reviewed: `index.html`, `main.js`, `logs.txt`, `.vscode/` as of commit `fa6a494`. Reviewer only; no code changed.

> **Status after the MCP server change:** these items are already fixed. The player now sits on top of its tile. The grid is centered on the origin. The shadow frustum fits the grid. Rendering is data-driven: `setWorld(world)` rebuilds from `world.json` or a WebSocket push and disposes the old meshes. `panelAnimate`, the light helper, the commented-out plane, the `a` key and `es-module-shims` are gone, and camera presets are on keys 1/2/3. **Still open:** the slab scale (the defaults are still 10-unit cubes; change them with `set_grid`), the fixed play camera, `rules.js`, `rev` and `level`, `result` messages, `validate_level`, and the `.vscode/` cleanup. The server stores tile overrides as a `grid.tiles` map keyed `"x,z"` and `camera` as a preset string, not the list and object shapes in the level JSON below.

## 1. What it is today

A static three.js 0.152.2 scene (CDN importmap, `python -m http.server 8000`). Nothing reacts to the player and nothing can be won or lost.

| System | Where | Verdict |
|---|---|---|
| Renderer, PCF soft shadows, resize handler | `_Initialize`, `_OnWindowResize` | Keep (real foundation) |
| 10x10 grid of 10x10x10 white cubes, 11-unit pitch | `panelAnimate()` | Keep the idea, rewrite it (hardcoded, wrong proportions) |
| 2x2x2 blue box at origin | `_Initialize` | The future player. Today it is invisible (see Problems) |
| Directional light (100,100,100) + ambient 0x404040 @ 0.5 | `_Initialize` | Keep, retune |
| `DirectionalLightHelper` | line 84 | Debug leftover |
| OrbitControls, free orbit/pan/zoom | line 90 | Debug camera, not game camera |
| `a` key snaps camera to (40,40,40) | `snapToIsometricPerspective` | Debug shortcut |
| Commented-out 100x100 plane | lines 10-19 | Dead code |
| Recursive `requestAnimationFrame` render loop | `_RAF` | Keep, but it has no clock/delta |
| `.vscode/` C/C++ Runner, gdb launch, IntelliSense config | `.vscode/*.json` | Leftover from the abandoned WASM/C++ attempt |
| `logs.txt` run notes | root | Should become a README |

## 2. Problems

**Game-breaking for a foundation**
- **The player box is buried inside a tile.** Tile (0,0) is a 10-unit cube centered at the origin, so it spans y -5..5. The box spans y 0..2. It is fully inside tile (0,0) and never renders. The only "game object" is not on screen.
- **Scale is wrong.** Tiles are 10x10x10 cubes, not floor slabs. Even lifted to y=6, the box covers 1/5 of a tile's width. Per-tile height overrides on 10-unit cubes produce huge towers. Use world units = tile units: `tileSize: 1`, slab height ~0.2, player ~0.7.
- **The grid is not centered.** Tiles run from -5 to 104 on x and z, centered at (49.5, 49.5). Both the start camera (75,20,0) and the `a` preset look at (0,0,0), a corner. From (40,40,40) most of the grid is behind the camera.
- **Shadows only cover about one tile.** The directional light's shadow camera keeps the default ±5 frustum, so only the area around the origin gets shadows. 100 meshes still cast and receive, and the 2048 map is wasted. Either fit `light.shadow.camera` to the grid bounds or turn shadows off until later.
- **Nothing is data-driven.** Tile count, size, gap (`+ 1` literal), colors and the box are all hardcoded in the constructor path. The MCP server pushes JSON, and the code has no `build(state)` function that can run twice, or any disposal of old meshes.

**Code and naming**
- `panelAnimate()` builds static tiles once. It animates nothing, and the "panel" name matches nothing else in the code. Call it `buildGrid(grid)`.
- `snapToIsometricPerspective` uses a perspective camera, so the view is not isometric. Call it `applyCameraPreset()`.
- The `a` key will clash with WASD movement. `e.key === 'a'` also misses `A` when Caps Lock or Shift is on, and the listener has no `preventDefault`.
- Free OrbitControls and grid movement don't mix: once the camera rotates, "W" stops meaning screen-up. A grid game needs a fixed camera, or at least locked rotation.
- One class (`baseWorld`, lower-case) owns renderer, input, camera, lights, world building and the loop. `_threejs` is the renderer. The tile loop calls its depth axis `y`, which will collide with the data model's `x/z`. `let app` is unused.
- In `_Initialize` the box is created, then the grid is built, then the box is positioned. The order is accidental.
- With `metalness: 0.5` and an ambient light that is almost black, the box's unlit faces render near-black.
- `.vscode/launch.json` points at an absolute Windows path in a Downloads folder and a C++ binary that does not exist. It misleads tooling and readers. `es-module-shims` is unnecessary in current browsers.

## 3. Simplified core loop: "Slide" (ice-slide grid puzzle)

**Proposal:** the box is on ice. Pick a direction and it slides tile by tile until a raised tile stops it. If it slides off the edge or into a hole, it falls. Stop exactly on the goal tile to win.

**Why this one:** it needs only what the scene already has (a grid, one box, tile heights). Plain step-to-goal movement is just pathfinding with no puzzle in it. Sliding makes a 6x6 grid with six walls a real puzzle. A level is a few integers, so the AI agent can author levels live through MCP. A 10-line BFS can prove each level solvable and find par before it is pushed. One level is finishable in under a minute, which gives a tight loop: look, plan, move, fall or win, retry.

- **Verbs:** `move(N|S|E|W)` via WASD / arrow keys, plus `restart` (R). That is all. (Undo is deferred.)
- **Win:** the player comes to rest on the `goal` tile. Passing over the goal mid-slide does not count. Show the move count against par.
- **Lose:** the player leaves the grid or enters a hole. It drops, and the level auto-restarts after ~0.5 s. There is no move limit, so retrying is free.
- **Tile rules from existing fields (no new schema):** a tile is a *floor* at the default height, a *wall* (blocks, slider stops before it) when its `height` override is greater than the default, and a *hole* (fall) when `height` is `0`, which renders no mesh.
- **Axes:** `x` is +X (east) and `z` is +Z (south, toward the default camera). `W` means -z. The renderer centers the grid on the origin: `worldX = (x - (width-1)/2) * (tileSize + gap)`.

**Level 1 as data** (6x6; checked by BFS, unique solution `N W N E S`, par 5; every other first move falls):

```json
{
  "rev": 1,
  "level": { "id": "1-1", "rules": "slide", "par": 5 },
  "grid": {
    "width": 6, "depth": 6, "tileSize": 1, "gap": 0.05,
    "tileHeight": 0.2, "color": "#e8e8e8",
    "overrides": [
      { "x": 2, "z": 0, "height": 1, "color": "#8a8f98" },
      { "x": 3, "z": 0, "height": 1, "color": "#8a8f98" },
      { "x": 5, "z": 1, "height": 1, "color": "#8a8f98" },
      { "x": 2, "z": 2, "height": 1, "color": "#8a8f98" },
      { "x": 2, "z": 3, "height": 1, "color": "#8a8f98" },
      { "x": 4, "z": 4, "height": 1, "color": "#8a8f98" },
      { "x": 0, "z": 3, "height": 0 },
      { "x": 1, "z": 3, "height": 0 }
    ]
  },
  "entities": [
    { "id": "player", "type": "player", "x": 5, "z": 5, "color": "#4287f5" },
    { "id": "goal",   "type": "goal",   "x": 4, "z": 3, "color": "#f5c542" }
  ],
  "camera": { "preset": "iso", "target": "gridCenter", "distance": 9 }
}
```

**Small additions the MCP data model needs** (if the server stores overrides as a keyed map instead of a list, keep the semantics and change only the shape):
1. `grid.tileHeight`: the default slab height, which gives "raised" and "hole" a meaning.
2. Reserved entity types `player` (exactly one) and `goal` (exactly one). These are values, not new fields.
3. Optional `level: { id, rules, par }`, plus a top-level `rev` integer the server bumps on every push. The browser resets play state only when `rev` changes, so a cosmetic color push mid-level does not teleport the player.
4. Ownership rule: the server holds the **level definition** (the player's *start* position). The browser holds **runtime** state (current position, move count) and does not write each move back.
5. One browser-to-server message on the same WebSocket: `{ "type": "result", "levelId": "1-1", "outcome": "won" | "fell", "moves": 5 }`, so the agent can see playtest outcomes.
6. One server-side MCP tool, `validate_level`, which runs the BFS and returns `{ solvable, par, solution }`. Agent-built levels will otherwise be unsolvable much of the time.

## 4. Cut list

**Remove now:** the commented-out plane; `DirectionalLightHelper` (or show it only behind `?debug`); the `a` key handler; free OrbitControls in play mode (keep them behind `?debug`); the box's `metalness`; the `.vscode/` C++ files; `es-module-shims`; the hardcoded `tileCount`/`tileXYZ`/`+1` literals.

**Defer:** shadows (off, or fit the frustum to the grid later); undo; level select and save progress; move limits or timers; enemies, pushable blocks, keys and doors (the obvious second mechanic is pushable blocks, but not before level 1 is fun); sound; a physics engine; any WASM/C++ revival; client-side procedural generation (the agent plus `validate_level` covers that).

## 5. Build order

1. **Render from data.** Write `buildWorld(state)`: a centered grid of slabs, the override heights and colors, holes as gaps, the player and a flat goal marker, and a fixed camera framed on the grid center. Load it from local `world.json`. Also `clear()`, which disposes the previous meshes. Delete the debug items from the cut list. Done when level 1 above renders correctly and the box is visible.
2. **Rules as pure logic.** Add `rules.js`, with no three.js: `slide(level, pos, dir) -> { pos, fell }` and `isWin(level, pos)`. Wire WASD/arrows/R. Snap the position for now. Done when `N W N E S` wins and `W` from the start falls.
3. **Feedback and feel.** Tween the slide (~60 ms per tile) and lock input during it. Add a fall animation with auto-restart, a HUD showing `moves / par`, and a "Solved" overlay with a "Next" stub. Move timing into `renderer.setAnimationLoop` with a delta.
4. **Live link.** Connect to the MCP server's WebSocket and apply pushed state through the same `buildWorld`. Reset runtime state only on a new `rev`. Send `result` messages back.
5. **Content loop.** Add `validate_level` (BFS) to the MCP server, have the agent author 3-5 levels of rising par, and add a level sequence with "Next". This is the first shippable build: start to finish, winnable, with retries.
