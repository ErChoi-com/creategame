# Codebase Structure

**Analysis Date:** 2026-08-19

## Directory Layout

```
callbackgame/                          # repo root
├── callback/                          # the Python package — everything below is `callback.*`
│   ├── __init__.py
│   ├── README.md                      # top-level README (design-doc index pointer)
│   ├── docs/
│   │   ├── callback-career-sim.py     # legacy/reference standalone script (pre-package)
│   │   ├── callback-sim.py            # legacy/reference standalone script (pre-package)
│   │   ├── callback-design-review.md
│   │   ├── design/                    # the game design spec — Parts 0-15, one .md per part
│   │   │   ├── 00-index.md
│   │   │   ├── creative-revamp-plan.md
│   │   │   ├── part-00-design-rules-and-cut-list.md
│   │   │   ├── part-03-design-overview.md   # §3.3 "one spine" rule, §3.4 core loop
│   │   │   ├── part-04-the-actor.md         # actor/ formulas
│   │   │   ├── part-05-the-work.md          # the shoot/prep/positions
│   │   │   ├── part-06-leverage.md          # leverage/
│   │   │   ├── part-07-the-director.md      # director/
│   │   │   ├── part-08-the-studio.md        # studio/
│   │   │   ├── part-09-genres-franchises-and-tie-ins.md  # genre/
│   │   │   ├── part-10-the-world.md         # world/
│   │   │   ├── part-11-the-life.md          # life/
│   │   │   ├── part-12-data-schemas.md
│   │   │   ├── part-13-build-plan.md
│   │   │   ├── part-14-tuning-targets.md    # verify.py's own checked targets
│   │   │   └── part-15-risks.md
│   │   └── ux/                        # screen-flow specs (01 character creation .. 04 pull systems)
│   │
│   └── engine/                        # the implementation — `callback.engine.*`
│       ├── __init__.py
│       ├── README.md                  # authoritative architecture/behavior narrative — read first
│       ├── core/                      # career-agnostic primitives (dependency root)
│       │   ├── meters.py              # Meter, StandingModel
│       │   ├── pipeline.py            # Stage protocol
│       │   ├── script_notes.py        # shared actor/director script-note mechanic
│       │   └── util.py                # clamp() and other generic helpers
│       ├── actor/                     # the actor career's formulas
│       │   ├── offers.py, prep.py, positions.py, shape.py, performance.py,
│       │   │   reception.py, release.py, studios.py, standing.py, persona.py,
│       │   │   palette.py, rating.py, series.py, aging.py, attributes.py
│       ├── director/                  # the second playable career
│       │   ├── attributes.py, casting.py, development.py, edit.py,
│       │   │   shoot_style.py, skill.py
│       ├── rolodex/                   # relationships/NPC layer
│       │   ├── rolodex.py, casting.py, interactions.py, npc.py
│       ├── leverage/                  # favours/approvals/indispensability
│       │   ├── approvals.py, catalogue.py, favours.py, indispensability.py,
│       │   │   merchandising.py, multi_picture_deal.py
│       ├── life/                      # health/addiction/family/money/obituary
│       │   ├── addiction.py, family.py, health.py, money.py, obituary.py, state.py
│       ├── world/                     # guilds/strikes/background industry
│       │   ├── genre_cycle.py, guild.py, strikes.py, trades.py
│       ├── genre/                     # franchise sequel curve, adaptation bonus
│       │   ├── adaptation.py, franchise.py
│       ├── studio/                    # slate-tier economics, Marketing curve
│       │   └── slate.py
│       ├── awards/                    # BuzzScore, category strategy
│       │   └── awards.py
│       ├── simulation/                # orchestration + player-facing façade + CLI
│       │   ├── career.py              # minimal single-career loop (ActorState/simulate_project)
│       │   ├── full_career.py         # full integrated loop (FullState)
│       │   ├── session.py             # Session — the ONLY engine surface a UI may import
│       │   ├── cli.py                 # terminal UI (imports only Session)
│       │   ├── verify.py              # statistical verification vs design/part-14
│       │   ├── bands.py               # ROI/critic/audience score → label bands
│       │   ├── _director.py, _franchises.py, _adaptations.py, _relationships.py
│       │   │   # private glue modules composing subsystems into FullState
│       │   └── _director_report.py, _full_data_report.py, _quality_report.py,
│       │       _report_sim.py, _smart_report.py, _sim_policy_shared.py,
│       │       _backgrounds.py, _release_labels.py
│       │       # analysis/reporting scripts, not part of the playable game
│       └── tests/                     # unit tests, one test_<package>.py per system
│           └── test_*.py
│
├── .planning/                         # GSD planning artifacts (this document lives here)
├── .claude/                           # Claude Code project config/skills
├── .vscode/                           # editor config
├── index.html, main.js                # UNRELATED — a standalone Three.js scaffold, not wired
│                                       # into the Python engine or CLI at all
├── logs.txt
└── .gitignore
```

## Directory Purposes

**`callback/engine/core/`:**
- Purpose: Career-agnostic building blocks every other package depends on.
- Contains: `Meter`/`StandingModel` (meters.py), the `Stage` protocol (pipeline.py), shared script-note logic, generic `clamp()`/util helpers.
- Key files: `callback/engine/core/meters.py`, `callback/engine/core/pipeline.py`

**`callback/engine/actor/`:**
- Purpose: Every formula behind the actor career — casting, prep, the shoot, performance, reception (box office), release strategies, standing, persona, studios, ratings.
- Contains: One module per named subsystem (offers, prep, positions, shape, performance, reception, release, studios, standing, persona, palette, rating, series, aging, attributes).
- Key files: `callback/engine/actor/offers.py` (Role/Utility), `callback/engine/actor/reception.py`, `callback/engine/actor/release.py`

**`callback/engine/director/`:**
- Purpose: The second playable career (development hell, casting, shoot style, the edit), built on `core`/`actor` rather than reimplementing Standing or casting math.
- Key files: `callback/engine/director/development.py`, `callback/engine/director/casting.py`, `callback/engine/director/edit.py`

**`callback/engine/simulation/`:**
- Purpose: Orchestrates every package into one playable game and exposes the player-facing façade.
- Contains: `career.py` (tested minimal loop), `full_career.py` (full integrated `FullState`), `session.py` (the `Session` façade — the only import a UI should ever need), `cli.py` (terminal UI), `verify.py` (statistical checks against design targets), private `_*.py` glue/report modules.
- Key files: `callback/engine/simulation/session.py`, `callback/engine/simulation/career.py`, `callback/engine/simulation/cli.py`

**`callback/engine/tests/`:**
- Purpose: Unit tests for every package above, plus regression tests for two intentionally v9-fixed constants.
- Contains: One `test_<subject>.py` per system (`test_adaptation.py`, `test_director.py`, `test_leverage.py`, `test_life.py`, `test_full_career.py`, `test_session.py`, etc.).
- Key files: `callback/engine/tests/test_full_career.py`, `callback/engine/tests/test_session.py`

**`callback/docs/design/`:**
- Purpose: The authoritative, numbered design specification (Parts 0-15) that every formula in `engine/` implements and cites by section number in docstrings/comments.
- Contains: One `part-NN-*.md` file per topic area, an index, and a creative-revamp planning doc.
- Key files: `callback/docs/design/part-03-design-overview.md` (§3.3/§3.4 — the architecture's own rules), `callback/docs/design/part-14-tuning-targets.md` (verify.py's targets)

**`callback/docs/ux/`:**
- Purpose: Screen-flow specifications the CLI follows exactly (character creation, the hub, the season loop, the pull menu).

## Key File Locations

**Entry Points:**
- `callback/engine/simulation/cli.py`: Interactive/auto-play terminal game — `python3 -m callback.engine.simulation.cli`
- `callback/engine/simulation/verify.py`: Statistical verification — `python3 -m callback.engine.simulation.verify all`
- `callback/engine/simulation/session.py`: Library entry point (`Session` class) for any future UI

**Configuration:**
- None — no config files, environment variables, or build tooling detected; behavior is controlled entirely by an integer `seed` argument.

**Core Logic:**
- `callback/engine/simulation/career.py`: The season-loop pipeline (resolve_shoot/resolve_quality/resolve_release_schedule/resolve_standing_update)
- `callback/engine/simulation/full_career.py`: `FullState`, the full integrated game loop
- `callback/engine/core/meters.py`: The shared Standing/Meter machinery every career reuses

**Testing:**
- `callback/engine/tests/`: `python3 -m unittest discover callback/engine/tests` (117+ tests as of the engine README)

## Naming Conventions

**Files:**
- `snake_case.py`, one module per named subsystem/formula group (e.g. `reception.py`, `release.py`, `standing.py`) — matches the design doc's own section names where applicable.
- Private/internal orchestration glue inside `simulation/` is prefixed with an underscore (`_director.py`, `_franchises.py`, `_adaptations.py`, `_relationships.py`, `_director_report.py`, etc.) to signal "not part of the public composition surface, only used by full_career.py/session.py."
- Test files mirror the package/module they cover: `test_<subject>.py` (e.g. `test_director_mode.py`, `test_leverage.py`, `test_full_career.py`).

**Directories:**
- One directory per named design-doc "system" (`actor/`, `director/`, `rolodex/`, `leverage/`, `life/`, `world/`, `genre/`, `studio/`, `awards/`), plus `core/` (shared primitives) and `simulation/` (orchestration/UI).

**Classes/functions (Python, per engine README + observed code):**
- Dataclasses are `@dataclass(frozen=True)` and named `<Noun>State`/`<Noun>Result`/`<Noun>Terms`/`<Noun>Decision` (e.g. `ActorState`, `ProjectResult`, `DirectorTerms`, `MarketingDecision`).
- Stage functions follow `resolve_<thing>()` / `simulate_<thing>()` naming and the `(state, rng, ...) -> result` call shape (the `Stage` protocol).
- Module-level constants are `UPPER_SNAKE_CASE` and usually documented with the design-doc section they encode (e.g. `BOX_OFFICE_BONUS_STANDING_THRESHOLD`, `MULTI_PICTURE_MIN_STANDING`).

## Where to Add New Code

**New actor-career formula/mechanic:**
- Implementation: a new module in `callback/engine/actor/`, importing only from `callback/engine/core/`
- Wiring: consumed by `callback/engine/simulation/career.py`'s stage functions, then threaded through `callback/engine/simulation/full_career.py` if it needs Rolodex/Leverage/Life/World context, then exposed on `callback/engine/simulation/session.py` if the player needs to act on it
- UI: add the corresponding screen function to `callback/engine/simulation/cli.py`, calling only the new `Session` method
- Tests: `callback/engine/tests/test_<subject>.py`

**New director-career mechanic:**
- Implementation: `callback/engine/director/`, importing only from `core`/`actor` public functions
- Wiring: `callback/engine/simulation/_director.py` (DirectorState), then `Session`
- Tests: `callback/engine/tests/test_director*.py`

**New career-agnostic primitive (a stat, a shared decision curve):**
- Implementation: `callback/engine/core/` — never career-specific logic here
- Consumed by: whichever career package(s) configure it (e.g. `actor/standing.py`, `director/attributes.py` both configuring `core.meters.StandingModel`)

**New supporting system (relationships/economy/world event):**
- Implementation: its own directory under `callback/engine/` (`rolodex/`, `leverage/`, `life/`, `world/`, `genre/`, `studio/`, `awards/`) depending only on `core`/`actor`
- Wiring: a `simulation/_<system>.py` glue module composes it into `FullState`, never reaching into another package's internals directly
- Tests: `callback/engine/tests/test_<system>.py`

**Design-doc changes:**
- `callback/docs/design/part-NN-*.md` — update the relevant numbered section first; engine code cites section numbers in docstrings, so keep them aligned when either changes.

## Special Directories

**`callback/engine/tests/`:**
- Purpose: Unit + regression tests, one file per system under test.
- Generated: No.
- Committed: Yes.

**`callback/docs/design/` and `callback/docs/ux/`:**
- Purpose: The design specification the engine implements; engine docstrings/comments cite these by section number (`§4.3`, `§7.4`, etc.).
- Generated: No — hand-authored design documents.
- Committed: Yes.

**`index.html` / `main.js` (repo root):**
- Purpose: An unrelated, unconnected Three.js scaffold (a `baseWorld` class, tile-grid rendering). Not part of the Python game engine's architecture — do not extend the game through these files.
- Generated: No.
- Committed: Yes.

**`.planning/`:**
- Purpose: GSD workflow planning artifacts (phase plans, requirements, this codebase map).
- Generated: Yes (by GSD tooling).
- Committed: Yes.

---

*Structure analysis: 2026-08-19*
