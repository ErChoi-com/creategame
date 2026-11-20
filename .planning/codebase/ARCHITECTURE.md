<!-- refreshed: 2026-08-19 -->
# Architecture

**Analysis Date:** 2026-08-19

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    Terminal UI — `callback/engine/simulation/cli.py`     │
│  imports exactly one engine symbol: `Session`. Every screen is built     │
│  from plain strings/numbers/dicts that Session methods return.           │
└───────────────────────────────┬────────────────────────────────────────┘
                                 │  method calls in, plain data out
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              Player-facing façade — `simulation/session.py` (Session)    │
│  offer_board/accept/choose_deal/choose_prep/play_scene/choose_release/   │
│  run_awards_campaign/trades/rolodex_summary/leverage_status/             │
│  franchise_status/become_director/advance_directing/end_year/...         │
└───────────────────────────────┬────────────────────────────────────────┘
                                 │  composes public functions of orchestration layer
                                 ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           Orchestration — `simulation/full_career.py` (FullState)        │
│  integrates actor loop + Rolodex + Leverage + Life + Guild + Strikes +   │
│  world genre-cycle + franchises + director career into one advancing     │
│  state; `simulation/career.py` (ActorState) is the tested, minimal       │
│  single-career loop full_career.py composes rather than reimplements.    │
└───┬─────────────┬─────────────┬─────────────┬─────────────┬────────────┘
    │              │             │             │              │
    ▼              ▼             ▼             ▼              ▼
┌────────┐   ┌──────────┐  ┌──────────┐  ┌─────────┐   ┌────────────┐
│ actor/ │   │ rolodex/ │  │leverage/ │  │  life/   │   │  world/    │
│ (Stage │   │(relation-│  │(favours, │  │(health,  │   │(guild,     │
│ funcs, │   │ ships)   │  │approvals,│  │addiction,│   │strikes,    │
│one-way │   │          │  │indispens-│  │family,   │   │genre_cycle)│
│on core)│   │          │  │ ability) │  │ money)   │   │            │
└────────┘   └──────────┘  └──────────┘  └─────────┘   └────────────┘
    │                                                          │
    ▼                                                          ▼
┌─────────────────────────────────────────────────────────────────────────┐
│    core/ — career-agnostic primitives: Meter/StandingModel (meters.py),  │
│    the Stage protocol (pipeline.py), script-note mechanics, clamp/util.  │
│    Imports nothing from the rest of the package (the dependency root).   │
└─────────────────────────────────────────────────────────────────────────┘

  Parallel second career, reusing core/actor rather than reimplementing:
  director/ (attributes, casting, development, edit, shoot_style, skill)
  — built on core/'s StandingModel and actor/'s Utility formula, composed
  into FullState via simulation/_director.py (DirectorState).

  Supporting/derived systems layered on the same spine:
  genre/ (sequel-value curve, adaptation bonus) · studio/ (slate-tier
  economics, Marketing curve) · awards/ (BuzzScore, category strategy)
  — all consumed through simulation/_*.py glue modules
  (_franchises.py, _adaptations.py, _relationships.py, _director.py)
  before FullState ever sees them.
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

**Overall:** Layered, one-way-dependency, functional-core game engine behind a single façade class (`Session`). No web/GUI framework, no database, no network layer — a pure-Python simulation engine consumed by a terminal CLI. Formulas and state transitions are pure functions over immutable (`frozen=True`) dataclasses; `random.Random` is threaded explicitly rather than using global RNG state, so runs are reproducible by seed.

**Key Characteristics:**
- Strict one-way dependency direction: `core` → `actor`/`director`(built on `core`) → `rolodex`/`leverage`/`life`/`world`/`genre`/`studio`/`awards` (built on `core`/`actor`) → `simulation` (composes public functions only, never reaches into another package's internals).
- Career-agnostic abstractions live in `core/` (`Meter`, `StandingModel`, the `Stage` protocol) so a second career (`director/`) reuses the exact same Standing/Utility machinery instead of re-implementing it — enforced as "the one spine" rule (`design/part-03` §3.3).
- A project's resolution is a straight-line pipeline of independently callable, independently testable stages (`resolve_shoot` → `resolve_quality` → `resolve_release_schedule` → `resolve_standing_update`), not a class hierarchy or dynamic dispatch — see `simulation/career.py`.
- The player-facing boundary is a single class (`Session`) whose entire contract is plain method calls in, plain data out (strings/numbers/small dicts/tuples) — no engine dataclass (`Role`, `ActorState`, `ReceptionResult`, `StandingModel`) ever crosses it. `cli.py` importing only `Session` is the proof the boundary holds; a future GUI/web frontend would sit at the same seam.

## Layers

**`core/` (career-agnostic primitives):**
- Purpose: Shared, career-agnostic abstractions used by every other package.
- Location: `callback/engine/core/`
- Contains: `Meter`/`StandingModel` (`meters.py`), the `Stage` protocol (`pipeline.py`), script-note mechanics shared by actor and director paths (`script_notes.py`), `clamp`/generic helpers (`util.py`).
- Depends on: nothing in this package (the dependency root).
- Used by: every other package.

**`actor/` (the actor career's formulas):**
- Purpose: Casting economics, prep, the shoot (palette/positions/shape), performance, reception (critic/audience/box office), release strategies, studios, standing (Heat/Prestige/Affection/Notoriety), persona, ratings, aging, series.
- Location: `callback/engine/actor/`
- Contains: `offers.py` (Role, Utility, casting path), `prep.py`, `positions.py`/`shape.py` (the three-scene shoot), `performance.py`, `reception.py` (box office resolution), `release.py` (wide/limited/festival/streaming/shelved), `standing.py`, `persona.py`, `palette.py`, `studios.py`, `rating.py`, `series.py`, `aging.py`.
- Depends on: `core` only.
- Used by: `simulation/career.py`, `director/` (reuses `offers.utility`), `simulation/full_career.py`.

**`director/` (second playable career):**
- Purpose: Development hell, casting, the shoot's style, the edit, director attributes/skill — a parallel career built on `core` and reusing `actor`'s Utility function rather than reimplementing casting math.
- Location: `callback/engine/director/`
- Contains: `attributes.py`, `casting.py`, `development.py`, `edit.py`, `shoot_style.py`, `skill.py`.
- Depends on: `core`, `actor` (public functions only).
- Used by: `simulation/_director.py`, `simulation/full_career.py`, `Session`.

**`rolodex/` / `leverage/` / `life/` / `world/` / `genre/` / `studio/` / `awards/` (supporting systems):**
- Purpose: Relationships (`rolodex`), favours/approvals/indispensability (`leverage`), health/family/money/obituary (`life`), guilds/strikes/genre cycle (`world`), franchise sequel-value/adaptation curves (`genre`), slate-tier economics (`studio`), BuzzScore/awards campaigns (`awards`).
- Location: `callback/engine/{rolodex,leverage,life,world,genre,studio,awards}/`
- Depends on: `core`/`actor` only, never each other's internals directly (composed instead through `simulation/_*.py` glue).
- Used by: `simulation/full_career.py`, `Session`.

**`simulation/` (orchestration):**
- Purpose: Wires every package above into one playable game, exposes the player-facing façade, verifies formulas against design targets, drives the terminal UI.
- Location: `callback/engine/simulation/`
- Contains: `career.py` (minimal single-career loop, `ActorState`/`ProjectResult`/`simulate_project`), `full_career.py` (`FullState`, the full integrated loop), `session.py` (`Session`, the façade — 2000 lines), `cli.py` (terminal UI), `verify.py` (statistical checks against `design/part-14`), private glue modules prefixed `_` (`_director.py`, `_franchises.py`, `_adaptations.py`, `_relationships.py`, plus report generators `_director_report.py`, `_full_data_report.py`, `_quality_report.py`, `_report_sim.py`, `_smart_report.py`, `_sim_policy_shared.py`, `_backgrounds.py`, `_release_labels.py`).
- Depends on: every package above, through public functions only.
- Used by: `Session` is consumed by `cli.py` and is the intended integration point for any future UI.

## Data Flow

### Primary Season Loop (one year, acting path)

1. `Session.offer_board()` procedurally generates 20+ listings, each scored through `actor.offers.utility()`/`offer_probability()` against the actor's real Standing (`session.py`).
2. `Session.accept(index)` → `career.simulate_project()` orchestrates the stage pipeline:
   - `resolve_shoot()` — prep/fit/chemistry/Performance roll, the three-scene shape (`career.py:218`)
   - `resolve_quality()` — critic/audience score and baseline box office, resolved once and never touched again (`career.py:321`)
   - `resolve_release_schedule()` — how the finished film reaches an audience, including the streaming bid pool (`career.py:418`)
   - `resolve_standing_update()` — Standing/Persona/Attributes/Recognition deltas (`career.py:483`)
3. `full_career.py` layers Rolodex costar draws, Leverage favours, Life state, Guild residuals, world genre-heat accumulation, and franchise/adaptation glue around the same `simulate_project()` call.
4. `Session.end_year()` is the single call that actually advances the shared calendar — every other action (release choice, holdout, marketing push, `advance_directing()`) applies its own deltas immediately but never touches the calendar itself.

### Directing Path (parallel career, same calendar)

1. `Session.become_director()` unlocks the directing track — reachable from year one, not gated behind acting Prestige.
2. `Session.start_directing_project()` shelves a project onto a capacity-gated slate (`DirectorState.slate`); `advance_directing()` spends one quarter's action on casting/shoot-style/edit/development-hell choices via `director/` modules.
3. On greenlight, `simulation._director._resolve_directed_film()` reuses the same `studios.pick_studio()`/`resolve_reception()`/`apply_release_strategy()` money math the actor path uses — one box-office model, not two.
4. The directed project's own `StandingModel` reuses `core.meters.StandingModel` with a director-specific billing weight (always 1.0), not a second Standing implementation.

**State Management:**
- Fully immutable, functional-update state: `ActorState`, `FullState`, `DirectorState`, `Rolodex`, `LeverageState`, etc. are all `@dataclass(frozen=True)`; every transition returns a new state via `dataclasses.replace()` rather than mutating in place. `Meter`/`StandingModel` are the one mutable exception (`.add()`/`.decay()` mutate in place) but are always operated on through an explicit `.copy()` first when a functional update is needed.
- All randomness flows through an explicitly passed `random.Random` instance (never global `random` state), making every run byte-for-byte reproducible by seed.

## Key Abstractions

**`StandingModel`/`Meter` (core.meters):**
- Purpose: Career-agnostic bounded stat + weighted-score reduction, shared by every career.
- Examples: `callback/engine/core/meters.py`, configured for the actor in `actor/standing.py`, for the director in `director/attributes.py` (via `simulation/_director.py`).
- Pattern: A concrete career configures meter names/bounds/gatekeeper weights; the reduction logic (`weighted_score`) is shared, never duplicated.

**`Stage` protocol (core.pipeline):**
- Purpose: Structural typing convention — every season-loop step is `(state, rng) -> result`.
- Examples: `resolve_shoot`, `resolve_quality`, `resolve_release_schedule`, `resolve_standing_update` in `callback/engine/simulation/career.py`.
- Pattern: `simulation/career.py` depends only on that call shape; stages don't inherit from or import `core.pipeline` to satisfy it.

**`Session` façade (simulation.session):**
- Purpose: The one class meant to be handed to a UI; every other module is engine, not UI-facing.
- Examples: `callback/engine/simulation/session.py` (2000 lines).
- Pattern: Method-call-in/plain-data-out only — no `Role`/`ActorState`/`ReceptionResult`/`StandingModel` ever returned or accepted.

**`ProjectResult` / `ReceptionResult` (frozen dataclasses):**
- Purpose: Immutable records of one resolved project's every output (quality, box office, standing deltas, rating outcome, marketing).
- Examples: `callback/engine/simulation/career.py:117` (`ProjectResult`), `callback/engine/actor/reception.py` (`ReceptionResult`).
- Pattern: Constructed once per resolution, never mutated; every downstream consumer (Session, CLI, tests) reads fields off it directly.

## Entry Points

**`callback/engine/simulation/cli.py` (`python3 -m callback.engine.simulation.cli`):**
- Location: `callback/engine/simulation/cli.py`
- Triggers: Run directly as a module (interactive) or with `--auto --seed=N` (self-playing demo).
- Responsibilities: Terminal screen flow only; imports exactly `Session` from the engine.

**`callback/engine/simulation/verify.py` (`python3 -m callback.engine.simulation.verify [reception|creative|all]`):**
- Location: `callback/engine/simulation/verify.py`
- Triggers: Run directly for statistical verification against `design/part-14` tuning targets.
- Responsibilities: Runs many simulated careers/projects and checks aggregate stats against documented targets.

**`callback/engine/simulation/session.py` (`Session` class, library entry point):**
- Location: `callback/engine/simulation/session.py`
- Triggers: Instantiated by any consumer (`Session(seed=42)`) — the intended integration point for a future GUI/web frontend.
- Responsibilities: The entire player-facing API surface.

**`callback/engine/tests/` (`python3 -m unittest discover callback/engine/tests`):**
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

**What happens:** A caller imports a module-level constant or private helper from another package instead of its documented public function.
**Why it's wrong:** Breaks the one-way dependency contract (`design/part-03` §3.3's "one spine" rule) and makes it impossible to swap or test a stage in isolation.
**Do this instead:** Import only public functions/classes documented at the top of each module (e.g., `simulation/career.py`'s own docstring: "Depends only on each actor/ module's public functions — never imports simulation/ from actor/, and never reaches past a stage's public entry point into its internals").

### A second, parallel implementation of Standing/Utility for a new career

**What happens:** Building a bespoke stat-tracking class for a new career instead of configuring `core.meters.StandingModel`.
**Why it's wrong:** Duplicates clamping/decay/weighted-score logic that already exists, and was explicitly called out as "the design is wrong" in `design/part-03` §3.3.
**Do this instead:** Instantiate `StandingModel` with career-specific meter names/weights (see `director/attributes.py`'s reuse pattern) and reuse `actor.offers.utility()` where casting math applies (`director/casting.py`'s `evaluate_candidate()`).

### Letting a UI type see an engine dataclass

**What happens:** A UI-layer function accepts or returns `Role`, `ActorState`, `ReceptionResult`, `StandingModel`, or any other engine type directly.
**Why it's wrong:** Breaks the `Session` boundary that `cli.py` is built to prove holds — a future GUI/web frontend would then need to import engine internals instead of sitting at the same seam `cli.py` does.
**Do this instead:** Add or extend a `Session` method that shapes the data into plain strings/numbers/small dicts/tuples before it ever reaches UI code.

## Error Handling

**Strategy:** Defensive clamping and bounded sampling rather than exceptions for expected out-of-range values; genuine programming errors (missing keys, wrong types) are allowed to raise naturally (no broad `except` swallowing observed).

**Patterns:**
- `core.util.clamp()` is used pervasively to keep every meter/score inside its documented `[lo, hi]` bounds after arithmetic.
- CLI input parsing defaults to a safe index (`auto_default_index`) whenever input is missing, non-numeric, or out of range (`cli.py`'s `choose()`/`prompt()`), rather than raising on bad terminal input.

## Cross-Cutting Concerns

**Logging:** None — the engine communicates entirely through return values (`Session` methods, `ProjectResult`/summary dicts) and the CLI's own `print()` calls; no logging framework is used.
**Validation:** Enforced through dataclass field types plus `clamp()`-based range enforcement inside formulas, not a separate validation layer or schema library.
**Authentication:** Not applicable — single-process, offline, no network layer.

---

*Architecture analysis: 2026-08-19*
