# Phase 1: Decision Space & Playtest Policy Coverage - Pattern Map

**Mapped:** 2026-08-20
**Files analyzed:** 5
**Analogs found:** 5 / 5

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `callback/docs/design/decision-map.md` | config/reference-doc | batch (static catalog) | `callback/docs/design/part-07-the-director.md` (doc structure) + `01-RESEARCH.md`'s "Full Decision-Point Inventory" tables (row content) | role-match (doc convention), exact (content source) |
| `callback/engine/simulation/_archetype_policies.py` | service (headless policy runner) | batch / event-driven (year-by-year loop over `Session`) | `callback/engine/simulation/_full_data_report.py` | exact |
| `callback/engine/simulation/_decision_coverage.py` | utility (stats/reporting tool) | transform (tally + report) | `callback/engine/simulation/verify.py` (stats-harness shape) + `_full_data_report.py`'s `Counter`-adjacent call-order (instrumentation target) | role-match |
| `callback/engine/tests/test_archetype_policies.py` | test | batch (smoke tests) | `callback/engine/tests/test_full_career.py` / `callback/engine/tests/test_session.py` | exact |
| `callback/engine/tests/test_decision_coverage.py` | test | batch (assertion over aggregate report) | `callback/engine/tests/test_full_career.py` (integration-style, drives the loop then asserts on the resulting state) | role-match |

## Pattern Assignments

### `callback/docs/design/decision-map.md` (config/reference-doc, batch)

**Analog:** `callback/docs/design/part-07-the-director.md` (structural/tone convention) — content comes from `01-RESEARCH.md`'s inventory tables, not from re-deriving anything.

**Doc header convention** (part-07, lines 1-3):
```markdown
# PART 7 — THE DIRECTOR

A full parallel career, not an epilogue. ...
```
New doc should open the same way: a short framing paragraph, no YAML frontmatter, `#`/`##` heading hierarchy matching other `part-NN-*.md` files (`callback/docs/design/00-index.md` lists the numbering convention — check it before assigning a "part number"; per CONTEXT.md this file is **not** numbered `part-NN`, it's a standalone `decision-map.md` cited *by* other parts).

**Table convention** (part-07, lines 9-13, and used pervasively in RESEARCH.md's own inventory):
```markdown
| As an actor | As a director |
|---|---|
| `PostLuck ~ N(52, 14)` — a blind roll that can bury your best work | **The edit is a decision you make.** You roll it, and you can steer the mean. |
```
Use the same `| Decision point | Options | Source | Design § |` row shape RESEARCH.md's "Full Decision-Point Inventory" tables already use (§200-326 of `01-RESEARCH.md`) — that section is directly transcribable into the catalog with a `Design §` column added per CONTEXT.md's citation requirement (design-doc section AND module/function).

**Per-entry citation convention** (module docstring pattern, e.g. `actor/positions.py`, `director/development.py`): every module cited already opens with `"""design/part-NN-....md §X.Y — ..."""`. Cross-reference each decision-map row's "Source" column against the actual module docstring to pull the exact `§` citation rather than guessing it.

**Exclusion callout convention:** Document the `ambition` field's zero-mechanical-effect status as an explicit one-line note (per RESEARCH.md Open Question 1) — do not silently omit it, and do not attempt to fix it this phase.

---

### `callback/engine/simulation/_archetype_policies.py` (service, batch/event-driven)

**Analog:** `callback/engine/simulation/_full_data_report.py` (full file read this session — 278 lines)

**Module docstring pattern** (lines 1-17):
```python
"""One-off reporting script: runs a director/actor career under a named policy "tendency" and
dumps every field available on each film's result ...
"""
from __future__ import annotations

import json
from dataclasses import replace as dc_replace

from callback.engine.actor.attributes import Attributes
from callback.engine.director import casting, shoot_style
from callback.engine.director.attributes import DirectorAttributes
from callback.engine.simulation.session import Session
from callback.engine.simulation._sim_policy_shared import SCENE_POSITIONS
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand
```
New module should follow the same import block shape: `Session` from `simulation.session`, shared scene defaults from `simulation._sim_policy_shared`, engine constant modules (`director.casting`, `director.shoot_style`) imported for their string constants — never re-derive the option strings as fresh literals.

**Per-archetype function shape** (`run(seed, tendency, years=60, ...) -> dict`, lines 41-56):
```python
def run(seed: int, tendency: str, years: int = 60, max_stats: bool = False) -> dict:
    session = Session(seed=seed)
    session.start("conservatory", "work")
    session.become_director()
    ...
    for year in range(years):
        board = session.offer_board()
        ...
```
Per CONTEXT.md's "one-function-per-archetype" decision, split this into 8 top-level functions (`prestige_chaser(seed, years=60) -> dict`, etc.) rather than one `run(tendency=...)` dispatcher — each function owns its own scoring closures, background/deal/prep/scene/release choices, following this file's per-branch style (`if tendency == "gambler": ... elif tendency == "prestige": ...` becomes each archetype's own straight-line body).

**Full decision-chain call order (acting)** (lines 109-158) — copy this sequence exactly, varying only the scoring/selection logic per archetype:
```python
session.accept(best["index"])
bonus_type = "first_dollar_gross" if session.box_office_bonus_available("first_dollar_gross") else "net_points"
want_merch = session.merchandising_available()
session.choose_deal(want_approvals=..., want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
session.choose_prep(...)
for episode in session.episode_labels():
    for scene_choice in SCENE_POSITIONS:
        session.play_scene(scene_choice)
if session.rating_cut_available():
    session.choose_rating_stance("release_as_shot")
session.request_marketing_push()
result = session.choose_release(strategy)
```
**Coverage-critical deviation required:** per RESEARCH.md's gap list, at least one archetype must deliberately vary each currently-uncovered branch (background other than `"conservatory"`, prep `"research"`/`"dialect"`, rating stance `"cut"`, costar orientation `"upstage"`, scene positions `"beyond"`/`"against"`, release `"festival"`/`"streaming"`/`"shelved"`, script note `"clarity"`/`"ambiguity"`/`"your_part"`).

**Full decision-chain call order (directing)** (lines 185-236) — same pattern for `start_directing_project`/`advance_directing`/`attach_star`; **must fix Pitfall 3** — any awards-campaign call needs an explicit `category` argument:
```python
session.run_awards_campaign(category=session.available_award_categories()[0], spend_millions=2.0)
```

**Attach-star ordering gotcha** (RESEARCH.md, `session.py:1918-1936`, cross-referenced against `_full_data_report.py:229-232`):
```python
if action == "attach_star":
    opts = session.attach_star_target_options()
    session.choose_attach_star_target(opts[i]["id"], atype)   # must be called first
result = session.advance_directing(project_index, action)      # reads the attach target set above
```

**"Both tracks" director-mode pattern to mirror for `director_track` archetype's dual-track variant:** `_full_data_report.py` itself already runs both actor and director loops every year (this whole file IS the "both tracks" pattern CONTEXT.md references as mirroring `_smart_report.py`) — no separate read of `_smart_report.py` needed; treat this file as the canonical "both tracks" template directly.

**Franchise-continuity deviation (for `franchise-maximizer`):** none of the 5 existing scripts track `franchise_id`/`installment_number` continuity across years (RESEARCH.md, Gated Decision Points section) — `franchise-maximizer`'s scoring function must be new logic, not copied from any existing `best = max(available, key=...)` closure: it needs to scan `offer_board()` results for a `franchise_id` matching one already held, re-accept it across multiple years, and after building indispensability, call `holdout_available()`/`request_holdout()` (threshold 30.0) and `spinoff_options()`/`launch_spinoff()` (threshold 55.0).

**Entirely-uncalled `Session` methods that at least one archetype must invoke** (0% coverage per RESEARCH.md's Coverage Gap Inventory — none of these appear anywhere in `_full_data_report.py` or any of the 4 superseded scripts, so there is no existing call-site pattern to copy; call them per their own docstrings/signatures in `session.py`):
`sign_multi_picture_deal`, `break_multi_picture_deal` (`session.py:826-880`), `request_holdout` (`session.py:740-795`), `launch_spinoff` (`session.py:799-822`), `disappear` (`session.py:1584-1594`), `push_director_deal_for_backend` (`session.py:1818-1840`), `choose_adaptation_source_type`/`set_adaptation_licensing_fraction` (`session.py:1763-1794`), `directing_franchise_options`/pitch a sequel, `directing_reboot_options`/`pitch_reboot`, `directing_spinoff_options`/`launch_directing_spinoff` (`session.py:631-720`), `interact(..., "show_up")`/`"read_agenda"`/`"vouch"` (only `"check_in"` is ever called today, at `_full_data_report.py:172`), `run_awards_campaign` for the director track (`session.py:1452-1489`).

---

### `callback/engine/simulation/_decision_coverage.py` (utility, transform)

**Analog:** `callback/engine/simulation/verify.py` (stats-harness structural shape — module docstring, plain functions, no classes) + the `Counter`-based tallying convention already used across `_smart_report.py`/`_director_report.py`/`_report_sim.py` (cited but not itself copied verbatim, per RESEARCH.md Pattern 2).

**Module docstring / no-class, plain-function shape** (`verify.py`, lines 1-17):
```python
"""CLI verification harness — reproduces design/part-14-tuning-targets.md's §14.1 (reception
model) and §14.6 (creative decisions) checks against this engine ...
    python3 -m callback.engine.simulation.verify reception
"""
from __future__ import annotations

import math
import random
import statistics as st
import sys

from callback.engine.actor.attributes import Attributes
...
```
`_decision_coverage.py` should mirror: module docstring citing what it checks against (the decision-map catalog), plain top-level functions (no class), a `__main__` CLI entry point in the same shape as `verify.py`'s `reception()`/`creative_decisions()`/`if __name__ == "__main__":` dispatch, and `_full_data_report.py`'s `if __name__ == "__main__": ... print(json.dumps(...))` tail (lines 271-278) as the alternate CLI-output style if JSON output is preferred over `verify.py`'s printed OK/`<<<` table.

**Coverage tally shape (recommended by RESEARCH.md Pattern 2, not existing code — this is new but must follow the `Counter`-in-the-caller convention already established)**:
```python
from collections import Counter

def run_with_coverage(policy_fn, seed: int) -> tuple[dict, Counter]:
    visited = Counter()
    summary = policy_fn(seed, visited=visited)
    return summary, visited
```
Each archetype function in `_archetype_policies.py` should accept an optional `visited: Counter | None = None` kwarg and increment it at each decision call site — this keeps instrumentation inside the caller (per CLAUDE.md's "no new logging framework" rule) rather than inside `Session`.

**Two required tally axes per Pitfall 4** (requested vs. resolved) — tally BOTH:
```python
result = session.choose_release(strategy)
if visited is not None:
    visited[f"release_requested:{strategy}"] += 1
    visited[f"release_resolved:{result['release_label']}"] += 1
```

**Series-project exclusion per Pitfall 5:** the coverage report must special-case `project_type == "series"` — do not flag "release strategy never requested" for a series year; treat series renewal as its own tracked outcome instead.

**Report output shape (model on `verify.py`'s OK/`<<<` table, lines 92-94):**
```python
for label, value, (lo, hi) in checks:
    ok = "OK " if lo <= value <= hi else "<<<"
    print(f"{ok} corr({label:26s}) = {value:5.2f}   target {lo:.2f}-{hi:.2f}")
```
Adapt to: `for decision_id, count in sorted(gaps): print(f"<<< UNVISITED  {decision_id}")` — the coverage report's core output per POLICY-02 is a gap list, ideally empty.

---

### `callback/engine/tests/test_archetype_policies.py` (test, batch)

**Analog:** `callback/engine/tests/test_full_career.py` (unittest, drives a multi-year loop then asserts on resulting state) and `callback/engine/tests/test_session.py` (unittest against `Session` directly, one `TestCase` class per feature area).

**Import + unittest class shape** (`test_full_career.py`, lines 1-20, 37-41):
```python
"""simulation/full_career.py — the integrated loop wiring actor/rolodex/leverage/life/world."""
from __future__ import annotations

import random
import unittest

from callback.engine.simulation.full_career import (
    accept_and_play, advance_between_years, decline_and_resolve, new_full_state, obituary,
    offer_this_year, utility_for,
)


class TestFullCareerIntegration(unittest.TestCase):
    def test_age_advances_every_year(self):
        state = _run_years(random.Random(1), 20)
        self.assertEqual(state.actor.age, 42)
```
`test_archetype_policies.py` should follow: one `TestCase` class per archetype (or one shared `TestArchetypeSmoke` class parametrized by archetype name), each test calling `run(seed=<fixed>, years=<short 10-15>)` and asserting no exception + a sane summary shape (dict keys present, `age` advanced, `acting_credits`/`director_credits` are ints) — per RESEARCH.md's Validation Architecture section, this is the exact required shape for POLICY-01's test map entry.

**`Session`-direct assertion style** (`test_session.py`, lines 37-56):
```python
class TestCharacterCreation(unittest.TestCase):
    def test_background_and_ambition_options_are_plain_data(self):
        session = Session(seed=1)
```
Use plain-data assertions on `_archetype_policies.run(...)`'s returned dict, never assert on engine dataclasses — matches the project's `Session`-boundary rule.

---

### `callback/engine/tests/test_decision_coverage.py` (test, batch)

**Analog:** `callback/engine/tests/test_full_career.py` (integration test that runs a loop across years and asserts an aggregate property of the resulting state, rather than one-call-per-assertion).

**Pattern:** Run the full 8-archetype set at a fixed seed set (per RESEARCH.md's Validation Architecture: "runs the full 8-archetype set at a fixed seed set and asserts the coverage tool's gap list is empty"):
```python
class TestDecisionCoverage(unittest.TestCase):
    def test_zero_gaps_across_full_archetype_set(self):
        gaps = run_full_coverage_check(seeds=[1, 2, 3], years=60)
        self.assertEqual(gaps, [], f"uncovered decision points: {gaps}")
```
This is the phase-gate test per POLICY-02 — must be green before `/gsd-verify-work`.

---

## Shared Patterns

### `Session` as the only legal seam
**Source:** `callback/engine/simulation/session.py` (2235 lines) — every new file's only import into "the engine" beyond plain constant modules.
**Apply to:** `_archetype_policies.py`, `_decision_coverage.py`, both test files.
```python
from callback.engine.simulation.session import Session
```
No new file may import `Role`, `ActorState`, `ReceptionResult`, or `StandingModel` — reads limited to `Session`'s own return dicts, mirroring `_full_data_report.py`'s scoring closures (e.g. `o["buzz_band"]`, `o["genre"]`) and the one documented precedent for reaching `session.state.genre_heat` read-only (`_quality_report.py:58-66`, `_report_sim.py:6-8`).

### Shared scene-position default
**Source:** `callback/engine/simulation/_sim_policy_shared.py`
**Apply to:** `_archetype_policies.py` — every archetype where scene choice isn't the differentiator.
```python
from callback.engine.simulation._sim_policy_shared import SCENE_POSITIONS
```
Archetypes that DO differentiate on scene choice (gambler: extreme contrast; indie-purist: craft-safe) should add new named position tuples to `_sim_policy_shared.py` itself (following its existing docstring convention citing the specific formula reasoning), not inline dicts inside `_archetype_policies.py`.

### `rng`/seed threading
**Source:** project-wide convention, `Session(seed=seed)` (`_full_data_report.py:42`).
**Apply to:** all new files — every archetype function takes `seed: int`, constructs its own `Session(seed=seed)`; no global `random` state anywhere.

### Design-doc citation in module docstrings
**Source:** every existing engine module (e.g. `actor/positions.py`, `director/development.py`).
**Apply to:** `_archetype_policies.py`, `_decision_coverage.py` module docstrings should cite `decision-map.md` itself as their reference doc (a new pattern, since these are catalogue-consumers, not spec-implementers) — e.g. `"""Exercises every decision point catalogued in docs/design/decision-map.md ..."""`.

## No Analog Found

None — all 5 files have a strong existing analog; this phase is explicitly additive/extending existing infrastructure per CONTEXT.md, not novel architecture.

## Metadata

**Analog search scope:** `callback/engine/simulation/` (all `_*.py` report scripts, `session.py`, `verify.py`), `callback/engine/tests/` (`test_full_career.py`, `test_session.py`), `callback/docs/design/` (`part-07-the-director.md`, `00-index.md`).
**Files scanned:** `_full_data_report.py` (full), `_sim_policy_shared.py` (full), `verify.py` (partial, lines 1-120), `test_full_career.py` (partial, lines 1-60), `test_session.py` (grep for class/def), `part-07-the-director.md` (partial, lines 1-40), plus full re-read of `01-CONTEXT.md` and `01-RESEARCH.md`.
**Pattern extraction date:** 2026-08-20
