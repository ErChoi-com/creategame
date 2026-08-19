# External Integrations

**Analysis Date:** 2026-08-19

## APIs & External Services

None. `callback/engine/` (the Python game engine — the actual "callback" life-sim) makes zero outbound network calls and integrates no third-party API or SDK; it is a pure, self-contained simulation over the standard library, played through a local terminal CLI (`callback/engine/simulation/cli.py`).

**3D prototype (unrelated project, repo root):**
- Three.js - `index.html` loads `three@0.152.2` and `es-module-shims@1.6.3` from the `unpkg.com` CDN via an import map. This is the only outbound network dependency anywhere in the repository, and it is purely a static asset load (no API calls, no data exchange) for the standalone `main.js` scene.

## Data Storage

**Databases:**
- None. No database client, connection string, ORM, or migration tooling anywhere in the codebase.

**File Storage:**
- Local filesystem only, and only incidentally: `logs.txt` at the repo root is a manually-maintained developer changelog for the JS prototype (not written to programmatically). The Python engine has no save/load or persistence layer — `Session` (`callback/engine/simulation/session.py`) and `FullState` are in-memory only; a game run's state exists for the lifetime of the Python process.

**Caching:**
- None.

## Authentication & Identity

**Auth Provider:**
- None. No auth of any kind — the engine is a single-player local process, the CLI has no login/user concept.

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry/error-reporting SDK, no telemetry.

**Logs:**
- None in the Python engine (no logging framework, no `print`-based logging layer beyond the CLI's own player-facing terminal output). `logs.txt` at the repo root is a hand-written developer diary for the JS prototype only (e.g. "08-05-2025 Switched back to three.js from WebAssembly with C++").

## CI/CD & Deployment

**Hosting:**
- None. No deployment target, no Dockerfile, no hosting config for either the Python engine or the JS prototype.

**CI Pipeline:**
- None. No `.github/workflows/`, no other CI config found anywhere in the repo. Tests (`python3 -m unittest discover callback/engine/tests`, or `pytest`, per `callback/engine/README.md`) are run manually.

## Environment Configuration

**Required env vars:**
- None. No `.env` file, no `os.environ` reads found in the engine.

**Secrets location:**
- Not applicable — no secrets, credentials, or API keys used anywhere in this repository.

## Webhooks & Callbacks

**Incoming:**
- None.

**Outgoing:**
- None.

---

*Integration audit: 2026-08-19*
