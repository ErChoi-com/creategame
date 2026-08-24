# Technology Stack

**Analysis Date:** 2026-08-19

## Languages

**Primary:**
- Python 3.13/3.14 - the entire `callback` game engine (`callback/engine/`), a text/terminal life-sim. No `pyproject.toml`/`setup.py`/`requirements.txt` exists anywhere in the repo — this is a plain, dependency-free Python package tree run via `python -m`, not an installable/packaged project.

**Secondary:**
- JavaScript (ES modules) - a separate, largely dormant 3D prototype at the repo root (`main.js`, `index.html`). Not connected to the Python engine in any way; different project living in the same repo.

## Runtime

**Environment:**
- Python 3.13.1 / 3.14.3 both present on the dev machine (`python --version` / `python3 --version`). No `.python-version` or version pin file — no enforced minimum version, though code uses `from __future__ import annotations` and dataclasses/typing features compatible with 3.9+.
- Browser (any evergreen browser with ES module + WebGL support) for the JS prototype — loaded via a plain `<script type="module">`, no bundler/dev server beyond `python -m http.server 8000` (per `logs.txt`).

**Package Manager:**
- None for Python — no `requirements.txt`, `Pipfile`, `pyproject.toml`, or virtualenv config found. All imports across `callback/engine/` are Python standard library only (`dataclasses`, `typing`, `enum`, `random`, `math`, `itertools`, `collections`, `statistics`, `functools`, `datetime`, `argparse`, `json`, `unittest`, `unittest.mock`).
- npm implied for the JS side (`.gitignore` excludes `node_modules/` and `package-lock.json`) but no `package.json` exists in the working tree — the JS dependency (`three`) is loaded entirely from a CDN import map in `index.html`, not installed locally.

## Frameworks

**Core:**
- None (Python) - `callback/engine` is built entirely on the standard library; no web framework, no ORM, no async framework. It is a simulation library plus a terminal CLI (`callback/engine/simulation/cli.py`).
- Three.js r0.152.2 (JS) - loaded via CDN (`https://unpkg.com/three@0.152.2/...`) through an import map in `index.html`; used only by the standalone `main.js` 3D scene prototype (a grid-tile world + `OrbitControls`), unrelated to the game's actual mechanics.

**Testing:**
- `unittest` (Python stdlib) - test suite lives in `callback/engine/tests/` (e.g. `test_adaptation.py`, `test_director_mode.py`, `test_formulas.py`, `test_franchises.py`, `test_full_career.py`, `test_leverage.py`, `test_life.py`, `test_session.py`, `test_studios.py`). Run via `python3 -m unittest discover callback/engine/tests` per `callback/engine/README.md`.
- `pytest` is also usable against the same suite — a `.pytest_cache/` directory is present at the repo root, indicating pytest has been run here even though there's no `pytest.ini`/`conftest.py`/`tox.ini` configuring it; it auto-discovers the `unittest`-style tests.

**Build/Dev:**
- None. No bundler, linter, formatter, or CI config found anywhere in the repo (no `.eslintrc`, `.prettierrc`, `webpack.config.*`, `vite.config.*`, `.github/workflows/`). The JS side runs unbundled straight from `index.html`'s import map; the Python side runs unbundled straight from module paths (`python3 -m callback.engine.simulation.cli`).

## Key Dependencies

**Critical:**
- None (zero third-party Python packages). The engine's own internal packages (`core`, `actor`, `rolodex`, `leverage`, `life`, `awards`, `director`, `world`, `genre`, `studio`, `simulation`) form a strict internal dependency graph documented in `callback/engine/README.md`: `core` imports nothing from the package; `actor` imports only `core`; every other package builds on `core`/`actor` (and `rolodex` where relationships matter); `simulation` composes only public functions from the rest.
- `three` (`three@0.152.2`) - only dependency for the unrelated JS prototype, resolved via CDN import map, not a local `node_modules` install.
- `es-module-shims@1.6.3` (CDN, `index.html`) - polyfills import maps for browsers lacking native support.

**Infrastructure:**
- None. No database client, no HTTP client/server framework, no message queue, no cache client anywhere in the codebase.

## Configuration

**Environment:**
- No environment-variable-based configuration found (no `.env`, no `os.environ` usage detected in the engine). All game tuning constants live as plain Python module-level constants inside the relevant engine files (e.g. `BOX_OFFICE_BONUS_STANDING_THRESHOLD` in `callback/engine/leverage/approvals.py`, `AFFECTION_DECAY`/`PRESTIGE_DECAY` in `callback/engine/actor/standing.py`).
- The Python simulation's only runtime configuration surface is CLI flags and constructor args: `Session(seed=...)` (`callback/engine/simulation/session.py`) and `cli.py --auto --seed=7`.

**Build:**
- None. `.vscode/settings.json` and `.vscode/launch.json` at the repo root are leftover C/C++ debugging config (`C_Cpp_Runner`, a `cppdbg` launch pointing at an unrelated `lab5/creategame` path) — not used by either the Python engine or the JS prototype; effectively stale editor config.

## Platform Requirements

**Development:**
- Windows 11 dev machine (per environment), Python 3.13+ interpreter on PATH, and (for the JS prototype only) any static file server (`python -m http.server 8000`, per `logs.txt`) plus a browser with WebGL/ES-module support.
- No OS-specific code paths detected in the Python engine — pure standard library, should run unmodified on macOS/Linux.

**Production:**
- No deployment target defined. The Python engine is a local terminal program (`python3 -m callback.engine.simulation.cli`), not a deployed service. The JS prototype is static files servable from any static host, but has no build step or production configuration.

---

*Stack analysis: 2026-08-19*
