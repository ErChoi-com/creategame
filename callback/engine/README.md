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
Session.offer_board() / accept() / decline_board()             the Offer Board
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
board = session.offer_board()
available = [o for o in board if o["available"]]
if available:
    session.accept(available[0]["index"])
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

**Movie-making has real, in-project choices now, not just prep/shoot/release.** Three more
dormant-or-missing systems got wired into `Session` and the CLI, all scoped to the film you're
actually making rather than life/politics side systems:

- **Script notes** (`actor/script_notes.py`, design §5.15) — if the Deal secured script approval,
  you get a real say before the shoot: push for clarity (audience up, critics down), ambiguity
  (critics up, audience down, a shot at a cult-classic bonus), your part (you read better, the
  script reads worse), or the whole film (no personal upside, but the film itself gets better).
  `Session.script_notes_available()` / `script_note_options()` / `choose_script_note()`.
- **Scene-partner orientation** — `actor/positions.py`'s `generosity()`/`upstaging()` formulas
  existed but were never called from anywhere; picking a tracked Rolodex co-star and choosing to
  play generous or upstage them now actually shifts notices, ensemble, and the relationship, and
  generosity credits that NPC a Leverage favour. `Session.costar_options()` /
  `orientation_options()` / `choose_orientation()`.
- **Requesting your director** — spend a Leverage favour to pull a specific tracked Rolodex
  director onto the project instead of the usual random NPC sample. Their own Standing (read via
  `full_career.director_terms_for()`, not a second stat block) sets the project's director terms —
  the same "one spine" reuse the Standing model already establishes elsewhere.
  `Session.available_directors()` / `request_director()`.

**Different studios finance and market your film differently** (`actor/studios.py`, reading
design §8.2's Marketing(b) curve down onto a single project). Every offer is now attached to a
producing studio — indie house, mid-major, prestige awards house, blockbuster machine, or
streamer-backed — each with its own marketing share of budget, backend split, festival pull, and
streaming buyout terms:

- **Indie house** — thin marketing (20% of budget), but the best backend split and a real
  festival-acquisition edge.
- **Mid-major** — the old flat baseline (45% marketing, standard backend), unchanged for anyone
  not passing a studio through.
- **Prestige awards house** — spends more on campaigns than trailers (50% marketing skewed toward
  festival pull), a slightly better backend, worse streaming terms.
- **Blockbuster machine** — marketing scales with budget on §8.2's own tiered curve (35% under
  $10M up to 80% over $100M), the worst backend split, weak festival pull.
- **Streamer-backed** — almost no theatrical marketing (8%), but the biggest streaming-buyout
  bonus if you pick that release strategy.

This changes real numbers, not just flavor text: `reception.py`'s `resolve_reception()` takes
optional `marketing_share`/`rights_share`/`opening_marketing_coef` params (a studio spending more
than baseline buys a bigger opening weekend — visibility, never quality; the film's actual
Project Quality/Critic/Audience scores are untouched), and `release.py`'s
`apply_release_strategy()` takes the matching `marketing_share`/`rights_share`/
`streaming_multiplier` so a chosen release strategy (Wide/Limited/Festival/Streaming/Shelved)
plays out through *that* studio's money, not a flat constant. `offers.sample_role()` now assigns
a studio weighted by the film's own budget (`studios.pick_studio()` — a $4M film never lands at
the blockbuster machine, a $200M one never lands at the indie house), and the CLI/`Session`
surface the studio's name and pitch on the Offer Board and again at Post & Release.

## Known gaps and simplifications (documented inline at each site too)

- **`actor/offers.sample_role()`** is still a placeholder role generator — it doesn't scale a
  role's difficulty to the actor's own Standing the way the real offer board's Rolodex/agent-reach
  filtering would. This is the reason a headless career still lands relatively few credits per
  offer seen: most individual rolls are simply too hard for a fresh actor. The fix is a real
  Standing-aware listing generator, not a new formula — everything downstream of "you got the
  part" is already correct. Its budget draw (`sample_budget_millions()`) got the same
  not-yet-Standing-aware treatment: a log-normal spread from $1.5M to a real $300M tentpole
  ceiling, median ~$12M, replacing the old fixed five-tier list — every value in range is
  reachable, not just five discrete stops, but which budget you personally get offered still
  isn't scaled to your own career yet.
- **`Session.offer_board()`** mitigates the same gap from the other direction: instead of one
  role rolled per year, it procedurally generates 3-6 listings (`OFFER_BOARD_MIN/MAX_LISTINGS`),
  each independently run through `utility()`/`offer_probability()` against your real Standing —
  more looks at the dice each year, not a smarter die. Accepting one listing quietly resolves
  every other listing on that board through the background industry (§10.0), the same as a single
  declined offer always has; declining the whole board (`decline_board()`) does the same for all
  of them and advances the year once. Still 0-1 projects per year — more choice about *which*
  film, not more films at once.
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
