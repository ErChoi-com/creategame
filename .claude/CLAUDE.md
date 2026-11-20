<!-- GSD:project-start source:PROJECT.md -->

## Project

**Callback — Playtest & Balance Pass**

Callback is a Hollywood career-simulation game: an actor navigates decades of roles, franchises, relationships, leverage, and life events, built as a Python engine (`callback/engine/`) driven by an extensive design-doc spec (`callback/docs/design/part-00` through `part-16`). The engine and its CLI prototype already exist and are covered by a large test suite. This project is not about adding a new feature — it's a systematic playtesting and balance-tuning pass: exhaustively exercise every gameplay option the engine currently offers, discover where builds/paths are weak, boring, dominant, or dead-ended, and tune the underlying values/formulas until a wide range of playstyles produce varied, fun, non-repetitive outcomes.

**Core Value:** Every meaningfully different way to play — background, ambition, genre lane, franchise chasing, leverage plays, life choices — should lead to a distinct, engaging career arc with real ups and downs. No path should be strictly best, and no path should be a dead end.

### Constraints

- **Convention adherence**: All engine changes must match the existing codebase conventions (naming, docstrings citing design-doc sections, frozen dataclasses, `core → actor → other packages → simulation` one-way dependency direction, no new logging/exception frameworks) — this was called out as the single most important constraint for this project.
- **Design-doc traceability**: Every tuning change should be traceable to a design-doc section — either it already exists and the code drifted, or the design doc gets updated to match the new intended target.
- **No engine dataclasses in CLI**: `Role`, `ActorState`, `ReceptionResult`, `StandingModel`, etc. must never leak past `Session` into `cli.py`.
- **Immersiveness over pure stats**: The measurable balance goals (no dominant strategy, no dead ends, meaningful variance, emotional highs/lows) matter, but the guiding priority when tuning is preserving the sense of an immersive, believable Hollywood career — not just flattening a stat curve.

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.13/3.14 - the entire `callback` game engine (`callback/engine/`), a text/terminal life-sim. No `pyproject.toml`/`setup.py`/`requirements.txt` exists anywhere in the repo — this is a plain, dependency-free Python package tree run via `python -m`, not an installable/packaged project.
- JavaScript (ES modules) - a separate, largely dormant 3D prototype at the repo root (`main.js`, `index.html`). Not connected to the Python engine in any way; different project living in the same repo.

## Runtime

- Python 3.13.1 / 3.14.3 both present on the dev machine (`python --version` / `python3 --version`). No `.python-version` or version pin file — no enforced minimum version, though code uses `from __future__ import annotations` and dataclasses/typing features compatible with 3.9+.
- Browser (any evergreen browser with ES module + WebGL support) for the JS prototype — loaded via a plain `<script type="module">`, no bundler/dev server beyond `python -m http.server 8000` (per `logs.txt`).
- None for Python — no `requirements.txt`, `Pipfile`, `pyproject.toml`, or virtualenv config found. All imports across `callback/engine/` are Python standard library only (`dataclasses`, `typing`, `enum`, `random`, `math`, `itertools`, `collections`, `statistics`, `functools`, `datetime`, `argparse`, `json`, `unittest`, `unittest.mock`).
- npm implied for the JS side (`.gitignore` excludes `node_modules/` and `package-lock.json`) but no `package.json` exists in the working tree — the JS dependency (`three`) is loaded entirely from a CDN import map in `index.html`, not installed locally.

## Frameworks

- None (Python) - `callback/engine` is built entirely on the standard library; no web framework, no ORM, no async framework. It is a simulation library plus a terminal CLI (`callback/engine/simulation/cli.py`).
- Three.js r0.152.2 (JS) - loaded via CDN (`https://unpkg.com/three@0.152.2/...`) through an import map in `index.html`; used only by the standalone `main.js` 3D scene prototype (a grid-tile world + `OrbitControls`), unrelated to the game's actual mechanics.
- `unittest` (Python stdlib) - test suite lives in `callback/engine/tests/` (e.g. `test_adaptation.py`, `test_director_mode.py`, `test_formulas.py`, `test_franchises.py`, `test_full_career.py`, `test_leverage.py`, `test_life.py`, `test_session.py`, `test_studios.py`). Run via `python3 -m unittest discover callback/engine/tests` per `callback/engine/README.md`.
- `pytest` is also usable against the same suite — a `.pytest_cache/` directory is present at the repo root, indicating pytest has been run here even though there's no `pytest.ini`/`conftest.py`/`tox.ini` configuring it; it auto-discovers the `unittest`-style tests.
- None. No bundler, linter, formatter, or CI config found anywhere in the repo (no `.eslintrc`, `.prettierrc`, `webpack.config.*`, `vite.config.*`, `.github/workflows/`). The JS side runs unbundled straight from `index.html`'s import map; the Python side runs unbundled straight from module paths (`python3 -m callback.engine.simulation.cli`).

## Key Dependencies

- None (zero third-party Python packages). The engine's own internal packages (`core`, `actor`, `rolodex`, `leverage`, `life`, `awards`, `director`, `world`, `genre`, `studio`, `simulation`) form a strict internal dependency graph documented in `callback/engine/README.md`: `core` imports nothing from the package; `actor` imports only `core`; every other package builds on `core`/`actor` (and `rolodex` where relationships matter); `simulation` composes only public functions from the rest.
- `three` (`three@0.152.2`) - only dependency for the unrelated JS prototype, resolved via CDN import map, not a local `node_modules` install.
- `es-module-shims@1.6.3` (CDN, `index.html`) - polyfills import maps for browsers lacking native support.
- None. No database client, no HTTP client/server framework, no message queue, no cache client anywhere in the codebase.

## Configuration

- No environment-variable-based configuration found (no `.env`, no `os.environ` usage detected in the engine). All game tuning constants live as plain Python module-level constants inside the relevant engine files (e.g. `BOX_OFFICE_BONUS_STANDING_THRESHOLD` in `callback/engine/leverage/approvals.py`, `AFFECTION_DECAY`/`PRESTIGE_DECAY` in `callback/engine/actor/standing.py`).
- The Python simulation's only runtime configuration surface is CLI flags and constructor args: `Session(seed=...)` (`callback/engine/simulation/session.py`) and `cli.py --auto --seed=7`.
- None. `.vscode/settings.json` and `.vscode/launch.json` at the repo root are leftover C/C++ debugging config (`C_Cpp_Runner`, a `cppdbg` launch pointing at an unrelated `lab5/creategame` path) — not used by either the Python engine or the JS prototype; effectively stale editor config.

## Platform Requirements

- Windows 11 dev machine (per environment), Python 3.13+ interpreter on PATH, and (for the JS prototype only) any static file server (`python -m http.server 8000`, per `logs.txt`) plus a browser with WebGL/ES-module support.
- No OS-specific code paths detected in the Python engine — pure standard library, should run unmodified on macOS/Linux.
- No deployment target defined. The Python engine is a local terminal program (`python3 -m callback.engine.simulation.cli`), not a deployed service. The JS prototype is static files servable from any static host, but has no build step or production configuration.

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- `snake_case.py`, named after the domain concept they model (`persona.py`, `obituary.py`, `catalogue.py`), not after a generic layer name (no `utils.py` sprawl — shared math lives in `core/util.py` specifically).
- Private/internal orchestration modules inside `simulation/` are prefixed with a leading underscore (`simulation/_director.py`, `simulation/_adaptations.py`, `simulation/_franchises.py`, `simulation/_relationships.py`) to distinguish "internal orchestration helpers" from the public modules in the same package (`career.py`, `session.py`, `cli.py`, `full_career.py`).
- Test files: `tests/test_<subject>.py`, one file per feature/system, not strictly one per source module (e.g. `test_director_mode.py`, `test_typecasting_depth.py`, `test_role_budget_split.py` group by *behavior* under test).
- `snake_case`, verb-first for actions (`apply_year`, `resolve_declined_role`, `advance`, `generate_obituary`), noun/adjective for pure queries (`condition`, `reception_factor`, `legibility_band`).
- Private module-internal helpers prefixed `_` (e.g. `_resolve_directed_film` in `simulation/_director.py`).
- `snake_case` throughout. Domain vocabulary from the design docs is used verbatim in code (`gross_income_millions`, `lifestyle_floor`, `consecutive_same_lane`, `char_age`, `type_strictness`) — variable names mirror the design doc's formula language rather than being abbreviated.
- Constants are `UPPER_SNAKE_CASE` module-level values, frequently tied directly to a design-doc section number in the docstring/comment above them (`AFFINITY_GAIN`, `STALENESS_COEF`, `LEGIBILITY_LOW_MAX`).
- `PascalCase` for classes/dataclasses (`Persona`, `MoneyState`, `AddictionState`, `HealthState`, `Role`, `FamilyState`).
- State-holding value objects are consistently suffixed `State` (`MoneyState`, `AddictionState`, `HealthState`, `FamilyState`) — this is the project's convention for "immutable snapshot of one subsystem's data."
- String-literal "enums" (stage names, dial labels) are plain `str` constants grouped near the top of the module (e.g. `CRISIS`, `RECOVERY`, `USE` in `life/addiction.py`) rather than `enum.Enum` classes — kept consistent with `dataclass` fields typed as `str`.

## Code Style

- No formatter config detected (no `.prettierrc`/`black` config file found in `callback/engine`). Code is manually kept to a consistent style: 4-space indents, double-quoted strings predominating, ~100–110 char line length in practice (some formula lines run long to keep an expression on one line, matching the design doc's math).
- `from __future__ import annotations` is present at the top of essentially every module — postponed evaluation of annotations is a project-wide standard, always the first non-docstring line.
- No `.eslintrc`/`ruff`/`flake8` config file detected. Style discipline is enforced by convention and by the test suite (see TESTING.md), not by a linter.

## Import Organization

- All internal imports use the fully-qualified `callback.engine.<package>.<module>` path (e.g. `from callback.engine.actor.offers import Role`). No relative imports (`from . import`) are used anywhere in the codebase, including within a package's own submodules.
- None. No bundler/tsconfig-style path aliasing; this is a Python package tree, imported by its full dotted path.

## Error Handling

- `ValueError` is raised for invalid/unknown domain inputs at API boundaries, with an f-string identifying the bad value: `raise ValueError(f"unknown casting choice: {choice}")` (`director/casting.py:82`).
- `SystemExit` is used only at the true CLI entry point to propagate a process exit code: `raise SystemExit(main(sys.argv))` (`simulation/verify.py:170`).
- Domain code otherwise favors **defensive math over exceptions** — invariants are enforced by clamping (`core/util.py:clamp`) and guard branches rather than raising. E.g. `sigmoid()` clamps its output at the extremes instead of raising on overflow; `Persona.legibility()`'s `concentration()` helper returns `0.0` when `peak <= 0` instead of dividing by zero.
- No custom exception hierarchy exists (no `exceptions.py` per package) — built-in exception types are used directly and sparingly.

## Logging

- Player-facing output goes through `simulation/cli.py`'s print/format layer, not a logger. There is no diagnostic logging layer to follow — do not introduce one without a stated need.

## Comments

- Every module carries a docstring that cites the exact design-doc section it implements, e.g. `"""design/part-04-the-actor.md §4.2 — the Persona (the typecasting engine)."""`. New modules should follow this pattern: cite the design doc and section at the top of the file.
- Inline comments explain *why a formula is shaped the way it is*, frequently referencing a bug that was once caused by the naive version (e.g. `life/money.py`'s comment on `peak_annual_income` decay, `persona.py`'s note on `STALENESS_COEF` being "a magnitude, not a pre-negated value"). Comments document formula intent and historical gotchas, not restating the obvious code.
- Regression-locking test comments explicitly say what bug they guard against (see TESTING.md).
- Module-level docstrings are mandatory and always reference the design doc section.
- Function docstrings frequently restate the exact formula from the design doc in prose/math notation (e.g. `"""100 × (max(v) − mean(v)) / max(v), averaged across both vectors."""`), so a reader can verify the code against the spec without opening the doc.

## Function Design

## Module Design

- State dataclasses are declared `@dataclass(frozen=True)` (e.g. `Persona`). Updates use `dataclasses.replace(...)` rather than field mutation — 41+ `@dataclass` usages across the codebase, and the frozen+`replace` pattern is the standard way to "update" simulation state.
- This immutability discipline is what makes the test suite's approach of chaining `state = apply_year(state, ...)` safe and predictable.
- No `__all__` lists detected; modules export via plain top-level `def`/`class`/constant definitions. Consumers import specific names explicitly (no wildcard imports observed).
- `simulation/session.py`'s `Session` class is the single sanctioned seam between "engine" and "UI." Its contract is described in `callback/engine/README.md`: only plain data (strings, numbers, small dicts/tuples) crosses that boundary — no engine dataclass (`Role`, `ActorState`, `ReceptionResult`, `StandingModel`, etc.) may leak into `simulation/cli.py`. When adding a new player-facing feature, add a `Session` method rather than importing an engine type into `cli.py`.
- Dependency direction is one-way and enforced by convention: `core` imports nothing from the rest of the package; `actor` imports only `core`; other packages build on `core`/`actor` (and `rolodex` where relevant) without reaching into another module's internals; `simulation` composes public functions only.

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| `Session` | Player-facing façade; only engine surface the UI may import | `callback/engine/simulation/session.py` |
| `cli.py` | Terminal UI, screen flow, printing | `callback/engine/simulation/cli.py` |
| `FullState` / full_career.py | Integrates every subsystem into one advancing game state | `callback/engine/simulation/full_career.py` |
| `ActorState` / career.py | Minimal, tested single-career actor loop (casting→prep→shoot→reception→standing) | `callback/engine/simulation/career.py` |
| `core.meters.StandingModel` | Career-agnostic Meter/Standing reduction shared by actor and director | `callback/engine/core/meters.py` |
| `core.pipeline.Stage` | Structural `(state, rng) -> result` protocol every actor/ stage conforms to | `callback/engine/core/pipeline.py` |
| `actor/` | Casting, prep, shoot (palette/positions/shape), performance, reception, release, standing, studios | `callback/engine/actor/*.py` |
| `director/` | Second playable career: casting, development, edit, shoot style, attributes, skill | `callback/engine/director/*.py` |
| `rolodex/` | NPC relationships, interactions, casting reads off relationships | `callback/engine/rolodex/*.py` |
| `leverage/` | Favours, approvals, indispensability/holdout, agent tiers, multi-picture deals, merchandising | `callback/engine/leverage/*.py` |
| `life/` | Health, addiction, family, money, the closing obituary | `callback/engine/life/*.py` |
| `world/` | Guilds, strikes, genre cycle (background industry heat/demand) | `callback/engine/world/*.py` |
| `genre/` | Franchise sequel-value curve, adaptation bonus/risk | `callback/engine/genre/*.py` |
| `studio/` | Slate-tier economics, Marketing curve | `callback/engine/studio/*.py` |
| `awards/` | BuzzScore, narrative bonuses, category strategy, vote splitting | `callback/engine/awards/*.py` |
| `simulation/_*.py` glue | Composes franchises/adaptations/relationships/director into `FullState` | `callback/engine/simulation/_franchises.py`, `_adaptations.py`, `_relationships.py`, `_director.py` |
| `simulation/verify.py` | Statistical verification against `design/part-14` tuning targets | `callback/engine/simulation/verify.py` |
| `tests/` | Unit tests for every package, plus v9-fixed-constant regressions | `callback/engine/tests/*.py` |

## Pattern Overview

- Strict one-way dependency direction: `core` → `actor`/`director`(built on `core`) → `rolodex`/`leverage`/`life`/`world`/`genre`/`studio`/`awards` (built on `core`/`actor`) → `simulation` (composes public functions only, never reaches into another package's internals).
- Career-agnostic abstractions live in `core/` (`Meter`, `StandingModel`, the `Stage` protocol) so a second career (`director/`) reuses the exact same Standing/Utility machinery instead of re-implementing it — enforced as "the one spine" rule (`design/part-03` §3.3).
- A project's resolution is a straight-line pipeline of independently callable, independently testable stages (`resolve_shoot` → `resolve_quality` → `resolve_release_schedule` → `resolve_standing_update`), not a class hierarchy or dynamic dispatch — see `simulation/career.py`.
- The player-facing boundary is a single class (`Session`) whose entire contract is plain method calls in, plain data out (strings/numbers/small dicts/tuples) — no engine dataclass (`Role`, `ActorState`, `ReceptionResult`, `StandingModel`) ever crosses it. `cli.py` importing only `Session` is the proof the boundary holds; a future GUI/web frontend would sit at the same seam.

## Layers

- Purpose: Shared, career-agnostic abstractions used by every other package.
- Location: `callback/engine/core/`
- Contains: `Meter`/`StandingModel` (`meters.py`), the `Stage` protocol (`pipeline.py`), script-note mechanics shared by actor and director paths (`script_notes.py`), `clamp`/generic helpers (`util.py`).
- Depends on: nothing in this package (the dependency root).
- Used by: every other package.
- Purpose: Casting economics, prep, the shoot (palette/positions/shape), performance, reception (critic/audience/box office), release strategies, studios, standing (Heat/Prestige/Affection/Notoriety), persona, ratings, aging, series.
- Location: `callback/engine/actor/`
- Contains: `offers.py` (Role, Utility, casting path), `prep.py`, `positions.py`/`shape.py` (the three-scene shoot), `performance.py`, `reception.py` (box office resolution), `release.py` (wide/limited/festival/streaming/shelved), `standing.py`, `persona.py`, `palette.py`, `studios.py`, `rating.py`, `series.py`, `aging.py`.
- Depends on: `core` only.
- Used by: `simulation/career.py`, `director/` (reuses `offers.utility`), `simulation/full_career.py`.
- Purpose: Development hell, casting, the shoot's style, the edit, director attributes/skill — a parallel career built on `core` and reusing `actor`'s Utility function rather than reimplementing casting math.
- Location: `callback/engine/director/`
- Contains: `attributes.py`, `casting.py`, `development.py`, `edit.py`, `shoot_style.py`, `skill.py`.
- Depends on: `core`, `actor` (public functions only).
- Used by: `simulation/_director.py`, `simulation/full_career.py`, `Session`.
- Purpose: Relationships (`rolodex`), favours/approvals/indispensability (`leverage`), health/family/money/obituary (`life`), guilds/strikes/genre cycle (`world`), franchise sequel-value/adaptation curves (`genre`), slate-tier economics (`studio`), BuzzScore/awards campaigns (`awards`).
- Location: `callback/engine/{rolodex,leverage,life,world,genre,studio,awards}/`
- Depends on: `core`/`actor` only, never each other's internals directly (composed instead through `simulation/_*.py` glue).
- Used by: `simulation/full_career.py`, `Session`.
- Purpose: Wires every package above into one playable game, exposes the player-facing façade, verifies formulas against design targets, drives the terminal UI.
- Location: `callback/engine/simulation/`
- Contains: `career.py` (minimal single-career loop, `ActorState`/`ProjectResult`/`simulate_project`), `full_career.py` (`FullState`, the full integrated loop), `session.py` (`Session`, the façade — 2000 lines), `cli.py` (terminal UI), `verify.py` (statistical checks against `design/part-14`), private glue modules prefixed `_` (`_director.py`, `_franchises.py`, `_adaptations.py`, `_relationships.py`, plus report generators `_director_report.py`, `_full_data_report.py`, `_quality_report.py`, `_report_sim.py`, `_smart_report.py`, `_sim_policy_shared.py`, `_backgrounds.py`, `_release_labels.py`).
- Depends on: every package above, through public functions only.
- Used by: `Session` is consumed by `cli.py` and is the intended integration point for any future UI.

## Data Flow

### Primary Season Loop (one year, acting path)

### Directing Path (parallel career, same calendar)

- Fully immutable, functional-update state: `ActorState`, `FullState`, `DirectorState`, `Rolodex`, `LeverageState`, etc. are all `@dataclass(frozen=True)`; every transition returns a new state via `dataclasses.replace()` rather than mutating in place. `Meter`/`StandingModel` are the one mutable exception (`.add()`/`.decay()` mutate in place) but are always operated on through an explicit `.copy()` first when a functional update is needed.
- All randomness flows through an explicitly passed `random.Random` instance (never global `random` state), making every run byte-for-byte reproducible by seed.

## Key Abstractions

- Purpose: Career-agnostic bounded stat + weighted-score reduction, shared by every career.
- Examples: `callback/engine/core/meters.py`, configured for the actor in `actor/standing.py`, for the director in `director/attributes.py` (via `simulation/_director.py`).
- Pattern: A concrete career configures meter names/bounds/gatekeeper weights; the reduction logic (`weighted_score`) is shared, never duplicated.
- Purpose: Structural typing convention — every season-loop step is `(state, rng) -> result`.
- Examples: `resolve_shoot`, `resolve_quality`, `resolve_release_schedule`, `resolve_standing_update` in `callback/engine/simulation/career.py`.
- Pattern: `simulation/career.py` depends only on that call shape; stages don't inherit from or import `core.pipeline` to satisfy it.
- Purpose: The one class meant to be handed to a UI; every other module is engine, not UI-facing.
- Examples: `callback/engine/simulation/session.py` (2000 lines).
- Pattern: Method-call-in/plain-data-out only — no `Role`/`ActorState`/`ReceptionResult`/`StandingModel` ever returned or accepted.
- Purpose: Immutable records of one resolved project's every output (quality, box office, standing deltas, rating outcome, marketing).
- Examples: `callback/engine/simulation/career.py:117` (`ProjectResult`), `callback/engine/actor/reception.py` (`ReceptionResult`).
- Pattern: Constructed once per resolution, never mutated; every downstream consumer (Session, CLI, tests) reads fields off it directly.

## Entry Points

- Location: `callback/engine/simulation/cli.py`
- Triggers: Run directly as a module (interactive) or with `--auto --seed=N` (self-playing demo).
- Responsibilities: Terminal screen flow only; imports exactly `Session` from the engine.
- Location: `callback/engine/simulation/verify.py`
- Triggers: Run directly for statistical verification against `design/part-14` tuning targets.
- Responsibilities: Runs many simulated careers/projects and checks aggregate stats against documented targets.
- Location: `callback/engine/simulation/session.py`
- Triggers: Instantiated by any consumer (`Session(seed=42)`) — the intended integration point for a future GUI/web frontend.
- Responsibilities: The entire player-facing API surface.
- Location: `callback/engine/tests/`
- Triggers: Run via unittest discovery from the repository root.
- Responsibilities: Unit tests for every package, including regression tests for v9-fixed constants.

## Architectural Constraints

- **Threading:** Single-threaded, synchronous. No async, no worker threads, no concurrency anywhere in the engine.
- **Global state:** None — no module-level singletons or shared mutable state; all state is threaded explicitly through function parameters/dataclasses. `random.Random` instances are always passed in, never module-global.
- **Circular imports:** None by design — the one-way dependency direction (`core` → `actor`/`director` → other packages → `simulation`) is a documented, enforced rule (`callback/engine/README.md`), not just an observation.
- **Unrelated root-level files:** `main.js`/`index.html` at the repository root are an unconnected Three.js scaffold (a `baseWorld` class rendering a tile grid) — not wired into the Python engine or CLI in any way. Do not treat them as part of this system's architecture.

## Anti-Patterns

### Reaching past a package's public entry point

### A second, parallel implementation of Standing/Utility for a new career

### Letting a UI type see an engine dataclass

## Error Handling

- `core.util.clamp()` is used pervasively to keep every meter/score inside its documented `[lo, hi]` bounds after arithmetic.
- CLI input parsing defaults to a safe index (`auto_default_index`) whenever input is missing, non-numeric, or out of range (`cli.py`'s `choose()`/`prompt()`), rather than raising on bad terminal input.

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:

- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
