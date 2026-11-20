# creategame

A three.js grid world that an AI agent can build and inspect live over MCP.

## Run the game

Without the MCP server (static files only, loads `world.json` once):

```bash
python -m http.server 8000
```

Then open http://localhost:8000/. Camera presets: `1` orbit, `2` isometric, `3` top-down. The mouse orbits, pans and zooms.

## MCP server

`mcp-server/server.js` speaks MCP over stdio. It also serves the game on http://localhost:8000/ (set `GAME_PORT` to change the port) and pushes every world change to open browser tabs over WebSocket. Every change is saved to `world.json`.

Setup (once):

```bash
cd mcp-server && npm install
```

**Claude Code** picks up the server automatically from `.mcp.json` when you open this folder. For other clients (Claude Desktop, Cursor and so on), add:

```json
{ "mcpServers": { "creategame": { "command": "node", "args": ["<path-to-repo>/mcp-server/server.js"] } } }
```

Then open http://localhost:8000/ so changes show up live and `screenshot` has a tab to capture.

| Tool | What it does |
|---|---|
| `get_world` | Full world JSON |
| `set_grid` | Width, depth, tile size, gap, default height and color |
| `set_tile` / `fill_tiles` | Color, height or hole for one tile or a rectangle; `reset` clears it |
| `spawn_entity` / `move_entity` / `update_entity` / `remove_entity` | Boxes, spheres and cones placed on grid tiles |
| `set_camera` | `orbit`, `isometric` or `top` in every open tab |
| `load_world` / `reset_world` | Replace the whole world in one call |
| `screenshot` | PNG of the open browser tab, returned to the agent |

Try asking: *"Make an 8x8 level with a wall down the middle, a pit, and a goal cone in the far corner, then screenshot it."*

Test: `cd mcp-server && npm test` (uses a temp world file and port).

## Design

See [docs/DESIGN_REVIEW.md](docs/DESIGN_REVIEW.md) for a breakdown of the prototype and the proposed core loop, an ice-slide grid puzzle.
