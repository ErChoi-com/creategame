# CALLBACK engine

Every system in `../docs/design/` and `../docs/ux/`, implemented and wired into one playable
terminal prototype behind a single player-facing API. See the design doc for what each formula
means; this package is where they run.

## Layout

```
core/         generic, career-agnostic abstractions (Meter, StandingModel, the Stage protocol)
actor/        the actor career's formulas (part-04-the-actor.md, part-05-the-work.md), plus
              release.py — release strategies (wide/limited/festival/streaming/shelved) and the
              weekly box-office trajectory
rolodex/      the Rolodex + relationship layer (§4.12, §10.0, ux/04-pull-systems.md)
leverage/     favours, approvals, indispensability + the holdout, a verb-catalogue subset (Part 6)
life/         health, addiction, family, money, the obituary (Part 11)
awards/       BuzzScore, narrative bonuses, category strategy, vote splitting (§4.11)
director/     a second playable career, built on core/ and reusing actor/'s Utility (Part 7)
world/        guilds, strikes, genre cycles, the background industry + trades digest (§10.0, Part 9)
genre/        the franchise sequel-value curve (§9.5)
studio/       slate-tier economics and the Marketing curve (§8.2)
simulation/   career.py + full_career.py (orchestration), verify.py (verification against
              design/part-14), session.py (the player-facing façade), cli.py (the terminal game)
tests/        unit tests for every package above, including regression tests for the two
              v9-fixed constants
```

Dependency direction is one-way: `core` imports nothing from this package; `actor` imports only
`core`; every other package builds on `core`/`actor` (and `rolodex` where relationships matter)
without reaching into another module's internals; `simulation` composes public functions only.
`director/` reusing `core.meters.StandingModel` and `actor.offers.utility` instead of
reimplementing Standing or casting math is `design/part-03` §3.3's "one spine" rule, held as
architecture rather than a promise in prose.

## The player-facing boundary: `simulation.session.Session`

Every package above is engine — built to be composed and tested, not handed to a UI. `Session` is
the one class meant to be. Its entire contract is plain method calls in, plain data out (strings,
numbers, small dicts/tuples) — no `Role`, `ActorState`, `ReceptionResult`, `StandingModel`, or any
other engine type ever crosses that boundary. `simulation/cli.py` proves the boundary holds: it
imports exactly one thing from the engine, `Session`, and nothing else — every screen is built
from what `Session`'s methods return, already shaped for printing. A future GUI or web frontend
would sit at exactly the same seam, importing only `Session`.

```
Session.background_options() / ambition_options() / start()   character creation
Session.roll_offer() / accept() / decline()                    the Offer Board
Session.approvals_available() / choose_deal()                  the Deal
Session.prep_options() / choose_prep()                         Prep
Session.dial_options() / position_options() / play_scene()     the Shoot
Session.release_options() / choose_release()                   Post & Release
Session.awards_campaign_available() / run_awards_campaign()    a real BuzzScore campaign
Session.trades() / rolodex_summary() / interact()               the pull menu: Trades, Rolodex
Session.leverage_status() / try_advance_agent_tier() / disappear()   the pull menu: Leverage
Session.obituary_summary()                                      the closing obituary
```

## Running it

From the repository root:

```bash
python3 -m unittest discover callback/engine/tests      # 117 tests
python3 -m callback.engine.simulation.verify reception    # design/part-14 §14.1 checks
python3 -m callback.engine.simulation.verify creative       # design/part-14 §14.6 checks
python3 -m callback.engine.simulation.verify all

python3 -m callback.engine.simulation.cli                    # play it — interactive
python3 -m callback.engine.simulation.cli --auto --seed=7      # self-playing demo run
```

```python
from callback.engine.simulation.session import Session

session = Session(seed=42)
session.start("conservatory", "work")
offer = session.roll_offer()
if offer["available"]:
    session.accept()
    session.choose_deal(want_approvals=False)
    session.choose_prep("table_work")
    for _ in range(3):
        session.play_scene({d: "with" for d, _ in session.dial_options()})
    print(session.choose_release("wide"))
```

Anything below `Session` (`full_career.py`, `career.py`, every `actor/`/`rolodex/`/`leverage/`
module) is still directly importable for testing, scripting, or a future engine consumer that
genuinely needs lower-level access — the façade doesn't hide the engine, it just means a UI never
has to reach past it.

## What's here now

Every system named in `design/`'s Parts 0/3–11 has a real, tested implementation. Two audit passes
went into confirming that, not just building it:

**Every package is exercised, not just present.** An earlier check found several systems that were
fully built and tested but had no path a player could ever actually reach: `rolodex/interactions.py`
(check in / show up / read their agenda / vouch), `leverage/catalogue.py`'s agent-tier progression
and Disappear/Scarcity, and all of `awards/awards.py` were sitting unimported outside their own
packages and test files. `Session` is where that got fixed — see the method table above.

**The box office model is a real mechanic, not just a final ROI number.** §3.4's core loop names
"festival vs wide vs dumped vs shelved" as its own step; `actor/release.py` builds it: **Wide** (the
original model, untouched), **Limited** (a smaller opening that leans on legs instead of
marketing), **Festival** (§10.3's own published acquisition formula — an unsold film returns ROI
0), **Streaming** (§8.3's flat buyout, no upside), and **Shelved** (a total loss). `weekly_gross_curve()`
turns the single "Gross" number into a real week-by-week trajectory, and §9.3's `GenreHeat` —
accumulated from every resolved film, including the background industry's — now feeds real
`GenreDemand` into box-office math instead of each site sampling its own random value.

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
- **`leverage/indispensability.py`'s holdout** has no player-facing entry point — it needs a
  tracked "this is installment N of a franchise" concept (a multi-project identity spanning years)
  that no part of `simulation/` builds yet. The formula is real and tested; nothing calls it.
- **`director/`** is a complete second career (DirectorSkill, development-hell greenlighting, the
  steerable edit, casting from the other side) with no `Session` of its own yet — it's reachable
  directly as a library, not through the CLI. A `DirectorSession` alongside the actor one is the
  natural next step, not a rebuild.
- **The full multi-offer calendar/deal-negotiation UI** isn't built — one project a year, not
  overlapping offers or the full fee/billing/options/pay-or-play deal space (only the
  approvals-for-fee trade is wired up).
- **Studio mode** is numeric primitives only (slate tiers, the Marketing curve) — no financing
  stack, release-date warfare, or board/executive layer, matching `design/`'s own "build it last"
  framing for that layer.
- **`world.guild.is_eligible()`** isn't literally wired into `actor.offers`' own (consistent, but
  separately-implemented) union-credit check — noted at the import site in `full_career.py`.
- **Politics (§11.5), festivals-as-submission (§10.3 beyond the release-strategy acquisition
  formula), international industries (§10.5), tech eras (§10.6), censorship (§10.7), and
  merchandise/tie-ins (§9.7–9.9)** are not implemented — genuinely out of scope for this pass
  rather than simplified.
