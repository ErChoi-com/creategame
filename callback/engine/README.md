# CALLBACK engine

Every system in `../docs/design/` and `../docs/ux/`, implemented and wired into one playable
terminal prototype. See the design doc for what each formula means; this package is where they run.

## Layout

```
core/         generic, career-agnostic abstractions (Meter, StandingModel, the Stage protocol)
actor/        the actor career's formulas (part-04-the-actor.md, part-05-the-work.md), plus
              release.py — release strategies (wide/limited/festival/streaming/shelved) and the
              weekly box-office trajectory (§3.4's "festival vs wide vs dumped vs shelved," never
              built out until now)
rolodex/      the Rolodex + relationship layer (§4.12, §10.0, ux/04-pull-systems.md)
leverage/     favours, approvals, indispensability + the holdout, a verb-catalogue subset (Part 6)
life/         health, addiction, family, money, the obituary (Part 11)
awards/       BuzzScore, narrative bonuses, category strategy, vote splitting (§4.11)
director/     a second playable career, built on core/ and reusing actor/'s Utility (Part 7)
world/        guilds, strikes, genre cycles, the background industry + trades digest (§10.0, Part 9)
genre/        the franchise sequel-value curve (§9.5)
studio/       slate-tier economics and the Marketing curve (§8.2)
simulation/   orchestration (career.py, full_career.py), verification (verify.py), and the
              playable CLI (cli.py)
tests/        unit tests for every package above, including regression tests for the two
              v9-fixed constants
```

Dependency direction is one-way: `core` imports nothing from this package; `actor` imports only
`core`; every other package builds on `core`/`actor` (and `rolodex` where relationships matter)
without reaching into another module's internals; `simulation` composes public functions only.
`director/` reusing `core.meters.StandingModel` and `actor.offers.utility` instead of
reimplementing Standing or casting math is `design/part-03` §3.3's "one spine" rule, held as
architecture rather than a promise in prose.

## Running it

From the repository root:

```bash
python3 -m unittest discover callback/engine/tests      # 94 tests
python3 -m callback.engine.simulation.verify reception    # design/part-14 §14.1 checks
python3 -m callback.engine.simulation.verify creative       # design/part-14 §14.6 checks
python3 -m callback.engine.simulation.verify all

python3 -m callback.engine.simulation.cli                    # play it — interactive
python3 -m callback.engine.simulation.cli --auto --seed=7      # self-playing demo run
```

```python
import random
from callback.engine.simulation.full_career import (
    new_full_state, offer_this_year, utility_for, accept_and_play,
    decline_and_resolve, advance_between_years, obituary,
)
from callback.engine.actor.offers import resolve_casting_path, offer_probability
from callback.engine.simulation.career import default_scene_policy

rng = random.Random(42)
state = new_full_state(rng, start_age=22)
role = offer_this_year(state, rng)
# ... accept_and_play / decline_and_resolve / advance_between_years each year;
# see simulation/cli.py for the full loop, or engine/tests/test_full_career.py.
```

## What's here now

Every system named in `design/`'s Parts 0/3–11 (the actor spine, the Rolodex, Leverage, the life
layer, awards, the director career, and a working subset of the world/genre/studio layers) has a
real, tested implementation — not a stub. `simulation/full_career.py` composes all of it into one
playable state, and `simulation/cli.py` is a real terminal game following `../ux/`'s exact screen
flow (character creation, the Offer Board, the Deal, Prep, the three-scene Shoot, Post & Release,
the Reckoning, the trades digest, the closing obituary) with every hidden score rendered through
`simulation/bands.py`'s words-not-numbers pass, never a raw number.

**The box office model is a real mechanic now, not just a final ROI number.** §3.4's core loop
names "festival vs wide vs dumped vs shelved" as its own step; `actor/release.py` builds it:
**Wide** (the original model, untouched), **Limited** (a smaller opening that leans on legs
instead of marketing), **Festival** (§10.3's own published acquisition formula — an unsold film
returns ROI 0), **Streaming** (§8.3's flat buyout, no backend, no upside), and **Shelved** (a total
loss). `simulation/cli.py` asks after every shoot. On top of that, `weekly_gross_curve()` turns the
single "Gross" number into a real week-by-week trajectory for display, and §9.3's `GenreHeat` —
accumulated from every resolved film, yours and the background industry's — now feeds real
`GenreDemand` into both `simulation/career.py`'s and `rolodex/casting.py`'s box-office math instead
of each independently sampling a random value; a hot genre visibly changes what your film earns.

## Known gaps and simplifications (documented inline at each site too)

- **`actor/offers.sample_role()`** is still a placeholder role generator — it doesn't scale a
  role's difficulty to the actor's own Standing the way the real offer board's Rolodex/agent-reach
  filtering would. This is the reason a headless career currently lands few credits: most rolls
  are simply too hard for a fresh actor. The fix is a real Standing-aware listing generator, not a
  new formula — everything downstream of "you got the part" is already correct.
- **`actor/palette.GENRE_DIAL_WEIGHTS`** and **`CANONICAL_ARCHETYPES`** are this pass's own
  documented readings, not undisclosed exact `design/` constants (§5.3 publishes target
  correlations, not the weight table itself). `verify.py creative` reports honestly against that
  gap rather than faking a pass.
- **The full multi-offer calendar/deal-negotiation UI** isn't built — `simulate_year`/`cli.py`
  handle "0 or 1 project this year," not overlapping offers, scheduling conflicts, or the full
  fee/billing/options/pay-or-play deal space (only the approvals-for-fee trade is wired up).
- **Studio mode** is numeric primitives only (slate tiers, the Marketing curve) — no financing
  stack, release-date warfare, or board/executive layer, matching `design/`'s own "build it last"
  framing for that layer.
- **`world.guild.is_eligible()`** isn't literally wired into `actor.offers`' own (consistent, but
  separately-implemented) union-credit check — noted at the import site in `full_career.py`.
- **Politics (§11.5), festivals (§10.3), international industries (§10.5), tech eras (§10.6),
  censorship (§10.7), and merchandise/tie-ins (§9.7–9.9)** are not implemented — genuinely out of
  scope for this pass rather than simplified.
