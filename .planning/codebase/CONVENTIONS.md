# Coding Conventions

**Analysis Date:** 2026-08-19

## Naming Patterns

**Files:**
- `snake_case.py`, named after the domain concept they model (`persona.py`, `obituary.py`, `catalogue.py`), not after a generic layer name (no `utils.py` sprawl — shared math lives in `core/util.py` specifically).
- Private/internal orchestration modules inside `simulation/` are prefixed with a leading underscore (`simulation/_director.py`, `simulation/_adaptations.py`, `simulation/_franchises.py`, `simulation/_relationships.py`) to distinguish "internal orchestration helpers" from the public modules in the same package (`career.py`, `session.py`, `cli.py`, `full_career.py`).
- Test files: `tests/test_<subject>.py`, one file per feature/system, not strictly one per source module (e.g. `test_director_mode.py`, `test_typecasting_depth.py`, `test_role_budget_split.py` group by *behavior* under test).

**Functions:**
- `snake_case`, verb-first for actions (`apply_year`, `resolve_declined_role`, `advance`, `generate_obituary`), noun/adjective for pure queries (`condition`, `reception_factor`, `legibility_band`).
- Private module-internal helpers prefixed `_` (e.g. `_resolve_directed_film` in `simulation/_director.py`).

**Variables:**
- `snake_case` throughout. Domain vocabulary from the design docs is used verbatim in code (`gross_income_millions`, `lifestyle_floor`, `consecutive_same_lane`, `char_age`, `type_strictness`) — variable names mirror the design doc's formula language rather than being abbreviated.
- Constants are `UPPER_SNAKE_CASE` module-level values, frequently tied directly to a design-doc section number in the docstring/comment above them (`AFFINITY_GAIN`, `STALENESS_COEF`, `LEGIBILITY_LOW_MAX`).

**Types:**
- `PascalCase` for classes/dataclasses (`Persona`, `MoneyState`, `AddictionState`, `HealthState`, `Role`, `FamilyState`).
- State-holding value objects are consistently suffixed `State` (`MoneyState`, `AddictionState`, `HealthState`, `FamilyState`) — this is the project's convention for "immutable snapshot of one subsystem's data."
- String-literal "enums" (stage names, dial labels) are plain `str` constants grouped near the top of the module (e.g. `CRISIS`, `RECOVERY`, `USE` in `life/addiction.py`) rather than `enum.Enum` classes — kept consistent with `dataclass` fields typed as `str`.

## Code Style

**Formatting:**
- No formatter config detected (no `.prettierrc`/`black` config file found in `callback/engine`). Code is manually kept to a consistent style: 4-space indents, double-quoted strings predominating, ~100–110 char line length in practice (some formula lines run long to keep an expression on one line, matching the design doc's math).
- `from __future__ import annotations` is present at the top of essentially every module — postponed evaluation of annotations is a project-wide standard, always the first non-docstring line.

**Linting:**
- No `.eslintrc`/`ruff`/`flake8` config file detected. Style discipline is enforced by convention and by the test suite (see TESTING.md), not by a linter.

## Import Organization

**Order (observed in `simulation/session.py` and others):**
1. `from __future__ import annotations` (always first)
2. Standard library imports (`random`, `dataclasses`, `types`)
3. `callback.engine.*` absolute imports, ordered roughly by dependency layer: `core` → `actor` → `leverage` → `life`/`director`/`genre`/`world` → `rolodex` → same-package siblings last.

**Absolute imports only:**
- All internal imports use the fully-qualified `callback.engine.<package>.<module>` path (e.g. `from callback.engine.actor.offers import Role`). No relative imports (`from . import`) are used anywhere in the codebase, including within a package's own submodules.

**Path Aliases:**
- None. No bundler/tsconfig-style path aliasing; this is a Python package tree, imported by its full dotted path.

## Error Handling

**Patterns:**
- `ValueError` is raised for invalid/unknown domain inputs at API boundaries, with an f-string identifying the bad value: `raise ValueError(f"unknown casting choice: {choice}")` (`director/casting.py:82`).
- `SystemExit` is used only at the true CLI entry point to propagate a process exit code: `raise SystemExit(main(sys.argv))` (`simulation/verify.py:170`).
- Domain code otherwise favors **defensive math over exceptions** — invariants are enforced by clamping (`core/util.py:clamp`) and guard branches rather than raising. E.g. `sigmoid()` clamps its output at the extremes instead of raising on overflow; `Persona.legibility()`'s `concentration()` helper returns `0.0` when `peak <= 0` instead of dividing by zero.
- No custom exception hierarchy exists (no `exceptions.py` per package) — built-in exception types are used directly and sparingly.

## Logging

**Framework:** None. No `logging` module usage detected in engine code.

**Patterns:**
- Player-facing output goes through `simulation/cli.py`'s print/format layer, not a logger. There is no diagnostic logging layer to follow — do not introduce one without a stated need.

## Comments

**When to Comment:**
- Every module carries a docstring that cites the exact design-doc section it implements, e.g. `"""design/part-04-the-actor.md §4.2 — the Persona (the typecasting engine)."""`. New modules should follow this pattern: cite the design doc and section at the top of the file.
- Inline comments explain *why a formula is shaped the way it is*, frequently referencing a bug that was once caused by the naive version (e.g. `life/money.py`'s comment on `peak_annual_income` decay, `persona.py`'s note on `STALENESS_COEF` being "a magnitude, not a pre-negated value"). Comments document formula intent and historical gotchas, not restating the obvious code.
- Regression-locking test comments explicitly say what bug they guard against (see TESTING.md).

**Docstrings:**
- Module-level docstrings are mandatory and always reference the design doc section.
- Function docstrings frequently restate the exact formula from the design doc in prose/math notation (e.g. `"""100 × (max(v) − mean(v)) / max(v), averaged across both vectors."""`), so a reader can verify the code against the spec without opening the doc.

## Function Design

**Size:** Small, single-formula functions are the norm — most functions in `actor/`, `life/`, `core/` are under 15 lines and implement exactly one named formula from the design docs. Larger orchestration functions live in `simulation/` (`career.py`, `session.py`) where multiple subsystems are composed.

**Parameters:** Keyword-explicit calls dominate for anything beyond 1–2 args (e.g. `apply_year(state, gross_income_millions=6.0, rng=rng)`), improving readability against the design doc's named formula inputs. `rng: random.Random` is threaded explicitly as a parameter everywhere randomness is needed — no global random state or seeding side effects.

**Return Values:** Pure functions return new values; stateful updates return a **new** immutable dataclass instance rather than mutating in place (see Module Design below).

## Module Design

**Immutability:**
- State dataclasses are declared `@dataclass(frozen=True)` (e.g. `Persona`). Updates use `dataclasses.replace(...)` rather than field mutation — 41+ `@dataclass` usages across the codebase, and the frozen+`replace` pattern is the standard way to "update" simulation state.
- This immutability discipline is what makes the test suite's approach of chaining `state = apply_year(state, ...)` safe and predictable.

**Exports:**
- No `__all__` lists detected; modules export via plain top-level `def`/`class`/constant definitions. Consumers import specific names explicitly (no wildcard imports observed).

**Barrel Files:** Not used. `__init__.py` files exist per package but are not used to re-export a curated public surface — callers import from the specific submodule directly (`from callback.engine.actor.offers import Role`).

**Player-facing boundary:**
- `simulation/session.py`'s `Session` class is the single sanctioned seam between "engine" and "UI." Its contract is described in `callback/engine/README.md`: only plain data (strings, numbers, small dicts/tuples) crosses that boundary — no engine dataclass (`Role`, `ActorState`, `ReceptionResult`, `StandingModel`, etc.) may leak into `simulation/cli.py`. When adding a new player-facing feature, add a `Session` method rather than importing an engine type into `cli.py`.
- Dependency direction is one-way and enforced by convention: `core` imports nothing from the rest of the package; `actor` imports only `core`; other packages build on `core`/`actor` (and `rolodex` where relevant) without reaching into another module's internals; `simulation` composes public functions only.

---

*Convention analysis: 2026-08-19*
