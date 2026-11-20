# Callback — Playtest & Balance Pass

## What This Is

Callback is a Hollywood career-simulation game: an actor navigates decades of roles, franchises, relationships, leverage, and life events, built as a Python engine (`callback/engine/`) driven by an extensive design-doc spec (`callback/docs/design/part-00` through `part-16`). The engine and its CLI prototype already exist and are covered by a large test suite. This project is not about adding a new feature — it's a systematic playtesting and balance-tuning pass: exhaustively exercise every gameplay option the engine currently offers, discover where builds/paths are weak, boring, dominant, or dead-ended, and tune the underlying values/formulas until a wide range of playstyles produce varied, fun, non-repetitive outcomes.

## Core Value

Every meaningfully different way to play — background, ambition, genre lane, franchise chasing, leverage plays, life choices — should lead to a distinct, engaging career arc with real ups and downs. No path should be strictly best, and no path should be a dead end.

## Requirements

### Validated

- ✓ Core actor career loop (offers, prep, scene shoot, reception, standing) — existing engine (`actor/`, `simulation/career.py`)
- ✓ Franchise/adaptation systems (sequels, reboots, franchise fatigue) — existing engine (`genre/franchise.py`, `genre/adaptation.py`, `simulation/_franchises.py`, `simulation/_adaptations.py`)
- ✓ Leverage/catalogue/indispensability systems — existing engine (`leverage/`)
- ✓ Life simulation (money, family, health, obituary) — existing engine (`life/`)
- ✓ Director mode (casting, development, editing) — existing engine (`director/`)
- ✓ Awards system — existing engine (`awards/awards.py`)
- ✓ Studio/slate and Rolodex/relationship systems — existing engine (`studio/slate.py`, `simulation/_relationships.py`)
- ✓ Headless simulation/report harness (`simulation/full_career.py`, `_full_data_report.py`, `_quality_report.py`, `_smart_report.py`, `verify.py`) with scripted decision policies for automated playthroughs
- ✓ Interactive CLI prototype exposing the full loop (`simulation/cli.py`) via the `Session` boundary
- ✓ Formula-verification harness reproducing design-doc §14 tuning targets (`simulation/verify.py`)

### Active

- [ ] Catalog every distinct gameplay option/decision point a player can reach (background, ambition, offer choices, prep, scene positions, leverage plays, franchise/adaptation decisions, director-mode choices, life/relationship choices) as a reference map of the full decision space
- [ ] Extend/build scripted playtest policies covering a wide variety of goals and archetypes (e.g. prestige-chaser, franchise-maximizer, indie-purist, risk-averse, gambler, director-track, family-first, burnout-avoider) so automated runs exercise the full decision space, not just the existing few policies
- [ ] Run automated playthroughs at volume across policies/seeds and collect outcome statistics (career length, income, prestige/heat/affection trajectories, obituary quality, franchise outcomes, dead-end/stuck-state frequency)
- [ ] Identify dominant strategies (a build objectively outperforming all others), dead ends (choices leading to boring/stuck/unrecoverable states), and low-variance outcomes (different choices converging on similar results)
- [ ] Tune the responsible constants/formulas in the engine to fix identified issues, always tracing each change back to the specific design-doc section it implements
- [ ] Update existing tests to reflect intentionally changed tuning values (tests encode current behavior, not sacred targets)
- [ ] Re-run the playtest sweep after each round of changes to verify fixes worked and didn't introduce new imbalances (discover → tune → verify loop)
- [ ] Research comparable career/Hollywood/RPG progression sim games for how they solve build-variety and immersiveness problems, and apply relevant patterns
- [ ] Produce a findings/changes report summarizing what was broken, what changed, and why, referencing design-doc sections

### Out of Scope

- New gameplay systems or content (new career paths, genres, event types) — this pass tunes what exists; gaps found may be flagged but only filled if a build path is otherwise dead-ended, not added speculatively
- CLI/UI text and presentation polish — engine values and formulas only; `simulation/cli.py` already exposes whatever the engine provides
- Anything outside `callback/engine/` (e.g. non-engine tooling, unrelated docs) unless directly needed to document a tuning decision

## Context

- **Codebase map already exists** at `.planning/codebase/` (STACK, ARCHITECTURE, STRUCTURE, CONVENTIONS, TESTING, INTEGRATIONS, CONCERNS) — read before deep work.
- **Design docs are the source of truth.** Every module cites the design-doc section it implements; formulas in code should match `callback/docs/design/part-XX-*.md`. Tuning changes should update the relevant design-doc section alongside the code, not just the code.
- **Immutable state discipline.** State is `@dataclass(frozen=True)`; updates go through `dataclasses.replace(...)`. Tuning code must follow this pattern, not mutate in place.
- **`Session` is the only engine↔CLI boundary** (`simulation/session.py`). Since this pass is engine-only, no new `Session` methods should be needed — but if a report script needs new engine-facing capability, it goes through existing public module functions, not by reaching into internals.
- **Existing headless report scripts already form the seed of a playtest harness**: `simulation/full_career.py` composes the full loop; `_full_data_report.py`, `_quality_report.py`, `_smart_report.py`, `_report_sim.py`, `_director_report.py` are one-off policy runners; `_sim_policy_shared.py` holds shared scene-position defaults; `verify.py` reproduces design-doc §14 statistical targets. Extend this infrastructure rather than building a parallel one.
- **Test suite is extensive** (`callback/engine/tests/test_*.py`, one file per feature/behavior) and currently encodes today's tuning values — expect to touch many of these as values change.

## Constraints

- **Convention adherence**: All engine changes must match the existing codebase conventions (naming, docstrings citing design-doc sections, frozen dataclasses, `core → actor → other packages → simulation` one-way dependency direction, no new logging/exception frameworks) — this was called out as the single most important constraint for this project.
- **Design-doc traceability**: Every tuning change should be traceable to a design-doc section — either it already exists and the code drifted, or the design doc gets updated to match the new intended target.
- **No engine dataclasses in CLI**: `Role`, `ActorState`, `ReceptionResult`, `StandingModel`, etc. must never leak past `Session` into `cli.py`.
- **Immersiveness over pure stats**: The measurable balance goals (no dominant strategy, no dead ends, meaningful variance, emotional highs/lows) matter, but the guiding priority when tuning is preserving the sense of an immersive, believable Hollywood career — not just flattening a stat curve.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Scope: tune + fill genuine gaps only, no new systems | User wants exhaustive balance across existing options, not scope creep into new content | — Pending |
| Discover weak spots via playtesting rather than a pre-made list | No known issues yet — data/play should surface them | — Pending |
| Playtest method: scripted automated playthroughs with varied decision policies | Engine already has a report/policy harness (`full_career.py`, `_*_report.py`) to extend rather than manual-only play | — Pending |
| "Done" = full sweep across all major systems + fixes + report, not indefinite tuning | Gives this milestone a concrete finish line despite tuning being open-ended | — Pending |
| Existing tests get updated to match intentional tuning changes | Tests encode current behavior, not fixed design targets | — Pending |
| Research comparable games, prioritizing immersiveness over stat-balance metrics alone | User's stated top priority is that the game feels immersive, not just mathematically balanced | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-08-20 after initialization*
