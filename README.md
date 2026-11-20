# Callback

A Hollywood career sim: one life, 22 to 82. You do not control whether the film is good. You control what you say yes to.

- `callback/engine/` holds the game, a dependency-free Python engine. See [`callback/engine/README.md`](callback/engine/README.md).
- `callback/docs/` holds the design spec (`design/`) and the UX spec (`ux/`).
- `web/` is the TypeScript web frontend (Vite + React).

Every UI talks to the engine through one seam, `simulation/session.py`'s `Session`:

| Interface | Run from the repo root |
|---|---|
| Terminal | `python3 -m callback.engine.simulation.cli` (add `--auto --seed=7` to watch it play itself) |
| Web | `python3 -m callback.engine.simulation.web_server`, then open http://127.0.0.1:8765 (build `web/` first, see below) |
| MCP (AI agents) | `python3 -m callback.engine.simulation.mcp_server`. Claude Code picks it up from `.mcp.json`. |

## Web frontend

```bash
cd web && npm install && npm run build      # one-time build, served by web_server.py
```

For development with hot reload, run the engine API, then Vite (it proxies `/api` to port 8765):

```bash
python3 -m callback.engine.simulation.web_server
```

```bash
cd web && npm run dev                         # http://localhost:5173
```

The frontend is built from a small component library (`web/src/components/`). The year's decisions are declared as data-driven flow steps (`web/src/flows/`), and every option list comes from the engine via `/api/options`. The look is "Cinematic Noir" (`web/src/styles.css` tokens).

## MCP server

`.mcp.json` registers it as `callback`. Its tools:

- `new_game`, `game_status`, `call_session` (any public `Session` method) and `list_methods`: play turn by turn.
- `auto_play`: fast-forward years with the CLI's defaults.
- `run_archetype`: one of the 8 scripted playtest policies, for a full career.
- `run_verify`: the statistical checks against `design/part-14`.

## Tests

```bash
python3 -m unittest discover callback/engine/tests
```

```bash
cd web && npm run typecheck
```
