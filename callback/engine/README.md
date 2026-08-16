# CALLBACK engine

The primary system and mechanics — the actor career's core loop — implemented from
`../docs/design/`. See that document for what each formula means; this package is where they run.

## Layout

```
core/        generic, career-agnostic abstractions (Meter, StandingModel, the Stage protocol)
actor/       the actor career's formulas (design/part-04-the-actor.md, part-05-the-work.md)
simulation/  orchestration (career.py) and verification (verify.py) against design/part-14
tests/       unit tests, including regression tests for the two v9-fixed constants
```

Dependency direction is one-way: `core` imports nothing from this package; `actor` imports only
`core`; `simulation` imports only `actor`'s public functions. A future director or studio engine
reuses `core` the same way `actor` does, rather than reimplementing Standing/decay/weighted-score
reduction a second time — that reuse is what `design/part-03-design-overview.md` §3.3's "one
spine" rule requires.

## Running it

From the repository root:

```bash
python3 -m unittest discover callback/engine/tests
python3 -m callback.engine.simulation.verify reception   # design/part-14 §14.1 checks
python3 -m callback.engine.simulation.verify creative     # design/part-14 §14.6 checks
python3 -m callback.engine.simulation.verify all
```

```python
import random
from callback.engine.simulation.career import simulate_career

state, results = simulate_career(start_age=22, years=40, rng=random.Random(42))
```

## Scope of this pass

Implements design/part-13-build-plan.md's Phase 0b + 1 + 1b: attributes, Persona, Standing, the
offer board, prep, the Performance roll, the six-dial palette, the four positions and contrast
budget, the three-scene shape resolution, and reception (critic/audience/box office).

**Not in this pass** — deferred in the build plan's own order: awards campaigns (§4.11), the
Rolodex and Leverage (§4.12, Part 6), the full calendar/deal-negotiation UI, director/studio/
world/life layers, and any UI (`../ux/` is the target once this engine is further along).

**Known simplifications, documented inline where they occur:**
- `actor/offers.sample_role()` is a placeholder role generator — it doesn't scale a role's
  difficulty to the actor's own Standing the way the real offer board's Rolodex/agent-reach
  filtering would, so a headless multi-year `simulate_career()` run currently lands very few
  credits per career. The individual formulas are the point of this pass; realistic career-length
  tuning is a follow-up once the Rolodex (§4.12) and a real offer-board content model exist.
- `actor/palette.GENRE_DIAL_WEIGHTS` and `CANONICAL_ARCHETYPES` are this pass's own documented
  readings, not a transcription of undisclosed exact design/ constants (§5.3 publishes the
  *target* correlations, not the underlying weight table). `verify.py creative`'s per-genre
  correlation check reports honestly against that gap — see its output and palette.py's docstring.
- Director, Condition (§11.1), and Rolodex (§4.12) inputs are sampled placeholders (documented at
  each call site) until those layers exist.
