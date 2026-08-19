# Testing Patterns

**Analysis Date:** 2026-08-19

## Test Framework

**Runner:**
- Python's built-in `unittest` (stdlib). No `pytest`, `nose`, or third-party runner config file exists anywhere under `callback/`.

**Assertion Library:**
- `unittest.TestCase` assertion methods (`assertEqual`, `assertGreater`, `assertLess`, `assertTrue`, `assertFalse`, `assertIn`, `assertGreaterEqual`). No `pytest`-style bare `assert` statements or third-party assertion libraries.

**Run Commands:**
```bash
python -m unittest discover -s callback/engine/tests   # Run all tests
python -m unittest callback.engine.tests.test_life      # Run one module
python -m callback.engine.tests.test_life                # Also runnable directly (each file has `if __name__ == "__main__": unittest.main()`)
```
(`pytest` also happens to work against `unittest.TestCase` files if installed, but the project is written and run against plain `unittest` — no `pytest.ini`/`pyproject.toml` test config exists.)

## Test File Organization

**Location:**
- Centralized, not co-located: all tests live under `callback/engine/tests/`, separate from the source packages they cover (`actor/`, `life/`, `director/`, etc.).

**Naming:**
- `tests/test_<subject>.py`, where `<subject>` is a feature or behavior area, not always a 1:1 mirror of a single source file. E.g. `test_life.py` covers `life/addiction.py`, `life/family.py`, `life/health.py`, `life/money.py`, and `life/obituary.py` together, because those modules compose one behavioral story (a life arc). Other files are narrower and map to one system: `test_rolodex.py`, `test_merchandising.py`, `test_series.py`.
- 26 test files, ~5,764 total lines — this is a substantial, actively maintained suite, not a token afterthought.

**Structure:**
```
callback/engine/tests/
├── __init__.py
├── test_core.py            # core/util.py, core/meters.py (Meter, StandingModel)
├── test_life.py            # life/ package (addiction, family, health, money, obituary)
├── test_director.py, test_director_mode.py, test_director_v10.py
├── test_franchises.py, test_adaptation.py, test_series.py
├── test_leverage.py, test_multi_picture_deal.py
├── test_formulas.py        # cross-cutting formula regression checks
├── test_full_career.py, test_session.py    # integration-level, exercise simulate_career/Session end-to-end
└── ...
```

## Test Structure

**Suite Organization:**
```python
class TestHealth(unittest.TestCase):
    def test_burnout_debt_lowers_condition(self):
        healthy = condition(HealthState(health=75, burnout_debt=0), resilience=50, substance_load=0)
        burnt_out = condition(HealthState(health=75, burnout_debt=20), resilience=50, substance_load=0)
        self.assertGreater(healthy, burnt_out)
```
- One `TestCase` subclass per sub-feature within a file (`TestHealth`, `TestAddiction`, `TestFamily`, `TestMoney`, `TestObituary` all inside `test_life.py`), named `Test<Subject>`.
- Test method names are full sentences describing the behavioral guarantee under test (`test_a_dry_spell_genuinely_corrects_the_floor_instead_of_oscillating`, `test_clean_usually_holds_but_can_begin_the_arc`) — names are written to be read as a spec, not abbreviated (`test_money_1`). Follow this style for new tests: the method name should state the guarantee, not the mechanism.

**Patterns:**
- No `setUp`/`tearDown` fixtures are typical; state is constructed inline per test via dataclass constructors (`MoneyState(net_worth=10.0, peak_annual_income=6.0, lifestyle_floor=3.3)`).
- Multi-step state evolution is tested by chaining reassignment against the immutable dataclasses: `state = apply_year(state, ...)` repeated in a loop, then asserting a trend across the resulting sequence (`test_a_dry_spell_genuinely_corrects_the_floor_instead_of_oscillating`).
- Randomness is always seeded explicitly and locally via `random.Random(<int>)` passed as the `rng` argument — never global `random` state. Distinct seeds are used per test to avoid coupling.
- Statistical/distributional behavior (e.g. rare-but-real state transitions) is tested by running many trials over a range of seeds and asserting on aggregate counts, not a single sample: `for seed in range(300): ... self.assertGreater(held, transitioned); self.assertGreater(transitioned, 0)` (`test_life.py::TestAddiction::test_clean_usually_holds_but_can_begin_the_arc`).

## Mocking

**Framework:** `unittest.mock.patch`, used sparingly.

**Patterns:**
```python
with patch("callback.engine.simulation._director._resolve_directed_film",
           return_value=(fake_reception, "wide", False, 30.0, 0.0, None)):
    ...
```
(`tests/test_director_mode.py:106`) — patches target the fully-qualified import path of the function being stubbed, matching the absolute-import convention project-wide.

**What to Mock:**
- Only the specific internal orchestration call that would otherwise pull in unrelated randomness/behavior when isolating one code path in an integration-style test (e.g. patching `_resolve_directed_film` to control its return tuple while testing the surrounding director-mode flow).

**What NOT to Mock:**
- Pure domain/formula functions (`apply_year`, `condition`, `advance`, etc.) are called for real, with seeded `random.Random` instances, rather than mocked — the suite's philosophy is to exercise real formulas with controlled randomness, not to stub them out. Mocking is the exception, reserved for integration tests around large orchestration functions (`simulate_career`, director mode), not for unit-level formula tests.

## Fixtures and Factories

**Test Data:**
- No separate fixtures/factories module or JSON fixture files. Test data is built directly via dataclass constructors and small locally-defined helper objects (e.g. constructing a `Role(...)` inline in `test_life.py::TestObituary`).
- Cross-system integration tests build a real mini-scenario using the actual engine functions rather than pre-baked fixtures, e.g. `simulate_career(start_age=22, years=20, rng=rng)` followed by `new_rolodex(...)` and `register_contact(...)` to produce a realistic `results`/`rolodex` pair before testing `generate_obituary`.

**Location:**
- N/A — no fixtures directory exists.

## Coverage

**Requirements:** No coverage tool config (`coverage.cfg`, `.coveragerc`) detected. No enforced numeric target.

**View Coverage:**
```bash
# Not configured in-repo; if needed, run manually:
python -m coverage run -m unittest discover -s callback/engine/tests
python -m coverage report
```

## Test Types

**Unit Tests:**
- The bulk of the suite: one formula/state-transition function exercised directly per test, per package (`test_core.py` for `core/util.py` and `core/meters.py`; `test_life.py`, `test_leverage.py`, etc. per package).

**Integration Tests:**
- `test_full_career.py` and `test_session.py` exercise `simulate_career` and `Session` end-to-end across many simulated years, validating that composed subsystems behave sensibly together (not just each formula in isolation).
- `test_formulas.py` performs cross-cutting regression checks tied to specific numeric constants called out in the README as "regression tests for the two v9-fixed constants" — i.e. tests exist specifically to lock in previously-buggy values so they can't silently regress.

**E2E Tests:** Not used. There is a terminal `simulation/cli.py`, but no automated end-to-end/CLI-driving test harness — `simulation/verify.py` instead does a scripted verification pass against `docs/design/part-14` (a design-spec conformance check, run as its own entry point, not part of the `unittest` suite).

## Common Patterns

**Regression-locking comments:**
```python
# Regression: peak_annual_income used to never decay, which pinned target_floor at the old
# ceiling forever — the floor would decay one year then instantly ratchet back up the next,
# alternating between two fixed values rather than ever actually falling.
```
When fixing a bug that a test would have caught, add both the assertion and a comment describing the previously-broken behavior — this is the established style across `test_life.py`, `test_formulas.py`, and others, and makes the test suite double as a changelog of subtle bugs.

**Seeded randomness:**
```python
rng = random.Random(5)
_, results = simulate_career(start_age=22, years=20, rng=rng)
```
Always instantiate a local `random.Random(seed)` and pass it explicitly; never rely on module-global `random` state in tests or production code.

**Trend assertions over sequences:**
```python
for earlier, later in zip(floors, floors[1:]):
    self.assertLess(later, earlier)
```
Used to assert monotonic behavior across a simulated sequence of years, rather than checking only start/end values.

---

*Testing analysis: 2026-08-19*
