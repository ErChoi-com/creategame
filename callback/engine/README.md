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
Session.franchise_status() / holdout_available() / request_holdout() the pull menu: Franchises
Session.directing_unlocked() / become_director() / advance_directing()   a second career, fused in
Session.end_year()                                              advances the shared calendar once
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
session.end_year()  # advances the shared calendar once — call after resolving whatever you did this year
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
  play generous or upstage them now actually shifts Spotlight, Craft Contribution, and the relationship, and
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
plays out through *that* studio's money, not a flat constant.

**Marketing is tracked as its own real figure, never folded silently into the production
budget.** `ReceptionResult`/`ProjectResult` both carry a `marketing` field distinct from `budget` —
Post & Release and a greenlit directed film both show them separately (e.g. "$0.9M production ·
$0.2M marketing"). It's still computed as a share of budget (`marketing_share × budget`, per the
studio financing it), but the two numbers stay visibly separate rather than becoming one blended
"cost" — and the split is real, not cosmetic: Streaming (§8.3's own "no theatrical" framing),
Shelved, and an unsold Festival submission all zero out `marketing` (no distributor ever spent it),
while the production `budget` itself is untouched in every strategy.

**Fixed a real scale bug in Streaming's ROI.** Every release path's `roi` is a multiple where 1.0
means exact break-even (`simulation/bands.ROI_BANDS`' own scale: 0.9 "close to even", 1.3
"profitable", ...) — Streaming's used to compute `(payout − budget) / budget`, a *gain fraction*
where 0.0 means break-even instead. A guaranteed-profitable `streaming_multiplier > 1.0` deal (the
whole point of the flat §8.3 buyout) was landing well under the 0.9 "close to even" threshold on
that scale and banding as **"a loss"** every single time, despite always paying out more than the
budget. Now `roi = payout / budget`, on the same scale as everything else.

`offers.sample_role()` now assigns
a studio weighted by the film's own budget (`studios.pick_studio()` — a $4M film never lands at
the blockbuster machine, a $200M one never lands at the indie house), and the CLI/`Session`
surface the studio's name and pitch on the Offer Board and again at Post & Release.

**Streaming rights are a real bidding pool, not one flat buyout.** `studios.streaming_bidders()`
gathers every studio whose money credibly plays at this budget (a wider band than who could have
*financed* it — buying rights is a smaller commitment than making it), each offering its own
`STREAMING_BUYOUT_MULTIPLIER + streaming_multiplier_delta` terms — deterministic, so it's a stable
menu to compare rather than a fresh roll every time you look. The pool always includes the film's
own financing studio, who can either bid their normal terms *or* — `SELF_DISTRIBUTE_MULTIPLIER`
— just put it up on their own service for nothing: you get exactly your budget back, no more, no
less, the literal "for nothing" option. `Session.streaming_bid_options()` surfaces a budget-only
*preview* pool before the film is made — nobody's seen it yet, so it can't reflect quality.

**The real sale happens after the movie is made, and quality decides who shows up.**
`studios.quality_adjusted_bids()` is resolved inside `choose_release("streaming")` itself, once
`resolve_reception()` has already produced the film's actual `film_critic_score`/`audience_score`
(`career.py` never reorders this — the quality terms are computed before any release strategy is
ever applied). Each outside bidder reads that quality with its own noise
(`QUALITY_PERCEPTION_SPREAD`, "perception can differ and vary within a certain range"), and a buyer
whose perceived read falls below `QUALITY_BID_FLOOR` simply doesn't bid — an awful film, especially
one that never got a wide release, can draw a thin outside pool or none at all. `choose_release`
takes an optional `streaming_bid_selector(bids) -> StreamingBid` callback (the CLI's
`release_screen()` uses it to show the real, quality-shaped offers and let you pick); with no
selector it auto-accepts the best offer. The financing studio's own terms and the
`SELF_DISTRIBUTE_MULTIPLIER` "for nothing" option are always on the table regardless of quality —
they already own the film either way.

**Franchises and directors are now real, interacting systems, not just data sitting in `genre/`
and `director/` unreached** (`simulation/_franchises.py`). Two previously-dormant systems —
§9.5's sequel-value curve (`genre/franchise.py`) and §6.4-6.5's Indispensability holdout
(`leverage/indispensability.py`) — are composed together and wired into the regular game loop,
not bolted on as a side mode:

- **Offers can be franchise entries.** `offer_this_year()` sometimes turns a freshly sampled role
  into either the first installment of a brand-new franchise, or — if you already have an open one
  — its next sequel, matching that franchise's genre and staying with the studio that financed the
  original (continuity, not a fresh random studio each time). The Offer Board tags these
  `[NEW FRANCHISE]` / `[SEQUEL — Part N]`.
- **A real box-office bonus, not flavor text.** `franchise_audience_bonus()` reuses
  `genre/franchise.py`'s `sequel_bonus()` exactly as designed — scaled by how well the *previous*
  installment's audience actually responded, added straight onto AudienceScore alongside every
  other reception input. A sequel to a poorly-received film earns far less than one following a
  hit, the same asymmetry real franchises show.
- **A returning director gets a mechanical bonus, not just a line of dialogue.** If you spend a
  Leverage favour to request the *same* director who helmed the franchise's last installment
  (`Session.request_director()`), `director_continuity_bonus()` applies `director/skill.py`'s own
  passion-project engagement bump to their skill term — continuity is rewarded the same way the
  formula already rewards a director who cares about the project.
- **Indispensability is a real, playable holdout, not a stat that just sits there.** Every sequel
  updates `character_identification()`/`indispensability()` off your real Spotlight, the audience's
  response, and your own Standing's `star_power()`. Once it crosses a threshold,
  `Session.holdout_available()` opens up `Session.request_holdout()` — the studio either pays a
  real fee increase, calls your bluff and proceeds at the original terms, or recasts the part
  entirely (voiding the project for that year and hitting your Standing's notoriety meter), per
  `leverage/indispensability.resolve_holdout()`. A franchise left dormant too long decays
  (`decay_dormant_franchises()`, honoring §6.4's v9 fix: decay always runs, and a property that
  crosses the release floor drops out of tracking rather than sticking around forever) and stops
  offering you sequels.
- **Reachable everywhere a player already looks.** `Session.franchise_status()` shows in the pull
  menu next to Rolodex/Leverage; Post & Release tags which installment you just played; the whole
  system interacts with Studios (financing continuity), the Rolodex (the requested director),
  Leverage (favours spent, the holdout itself), and Standing (notoriety on a failed holdout,
  star_power feeding indispensability) rather than living in its own silo.

**Directing is a real second career now, fused into this same `Session`/`FullState` rather than a
separate one** (`simulation/_director.py`). A sufficiently prestigious actor
(`directing_unlocked()`: real Prestige and enough credits, not a rubber stamp) can cross into
directing (`become_director()`) — the CLI's "This year: act, or direct?" choice is a genuinely
distinct menu, not the acting screens repurposed:

- **Development hell is real**, not a single roll: `director/development.py`'s `DevProject`
  (momentum, budget ask, an attached star) advances one action a year — rewrite, attach a star,
  cut the budget, find a new financier, take it to market, self-finance, or shelve it — through
  the same `package_strength()`/`greenlight_probability()` formulas, until it either greenlights,
  dies in development, or keeps going.
- **A director's own Craft and Efficiency steer the edit**, not just luck: `director/edit.py`'s
  `steered_post_luck()` shifts PostLuck's mean before the roll — reception.py grew an optional
  `post_luck_override` param specifically so a director's film isn't subject to the actor path's
  blind `N(52, 14)` sample.
- **The same money, marketing, and box-office math the actor's films use** — a directed film is
  cast through `studios.pick_studio()`/`marketing_share_for()` exactly like an acting role,
  resolved through the same `resolve_reception()`, and feeds the same `world.genre_cycle` heat and
  Guild residuals afterward. One box-office model, not two.
- **One shared calendar, one Standing philosophy — and acting and directing no longer compete for
  it.** A directed project's own `StandingModel` is the same `core.meters.StandingModel`
  actor/standing.py configures (§3.3's "one Standing model" rule, made literal again) — grown off
  the same `delta_heat`/`delta_prestige`/`delta_affection` formulas, just with a director's own
  billing weight (always 1.0 — you're the whole show). Every action that resolves an outcome
  (`choose_release()`, `decline_board()`, `request_holdout()`, `advance_directing()`,
  `disappear()`) applies its own Standing/money/state deltas immediately but no longer touches the
  calendar itself — `Session.end_year()` is the one call that actually advances it.
- **Each block is a clean either/or, but you can work both blocks in the same year.** The CLI's
  `year_screen()` presents one menu — "Work on acting" / "Work on directing" / "That's it for this
  year" — and loops after each pick, so choosing acting doesn't remove directing from the menu; it
  removes *itself*, letting you circle back for the other before the calendar moves. `Session`
  itself has no "which mode" flag to keep in sync — `year_screen()` is UI-layer sequencing over
  two already-independent Session tracks, not a new engine concept.

**A box-office bonus is a real, higher-bar Deal option** (`leverage/approvals.py`'s
`BOX_OFFICE_BONUS_STANDING_THRESHOLD`, deliberately set well above the 65-Standing bar approvals
already use — a real backend point is a rarer get than script/co-star approval). Negotiating it
(`Session.box_office_bonus_available()` / `choose_deal(..., want_box_office_bonus=True)`) pays out
3% of the film's Gross, but only if it actually clears break-even (`box_office_bonus_earned()`
returns 0 on anything that lost money — a real gross-points deal, not a guaranteed top-up). The
payout flows straight into `life/money.py` as real income (`advance_between_years()`'s new
`bonus_income` param), same as your quote already does.

**Studios and directors remember profit and loss** (`simulation/_relationships.py`). Every
resolved project updates a `Relationship` (project count, running net P&L, a 0-100 trust score)
keyed to that film's financing studio, and — if you spent a Leverage favour to request them — to
that specific director. Trust moves asymmetrically off ROI, the same loss-averse read every other
risk-facing formula in this engine already uses: a big loss costs more trust than an equivalent
win earns back. That trust then changes real numbers, not just a ledger:

- **A studio's trust in you shifts how easily they cast you.** `Session.offer_board()` adds
  `utility_bonus_from_trust()` straight onto that listing's Utility before the casting-path/offer-
  probability roll — a studio you've made money for offers more readily, one you've burned goes
  measurably cold (an instrumented check: distrust dropped one studio's own offer-availability
  rate from ~12% to ~5% against otherwise-identical listings).
- **A director's trust in you sharpens their own skill reading**, stacking with (not replacing)
  the franchise-specific continuity bonus a *returning* director on the same franchise already
  earns — two different, real reasons a repeat collaborator reads better.
- **Reachable everywhere a player already looks**: `Session.studio_relations_status()` /
  `director_relationship_status()` show in the pull menu next to Rolodex/Franchises/Leverage, and
  `available_directors()` now shows trust alongside the existing relationship/favour-balance read.

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
  role rolled per year, it procedurally generates at least 20 listings (`OFFER_BOARD_MIN_LISTINGS`,
  up to `OFFER_BOARD_MAX_LISTINGS`), each independently run through `utility()`/
  `offer_probability()` against your real Standing — more looks at the dice each year, not a
  smarter die. If that still isn't enough, `generate_more_listings()` appends another batch on
  demand (the CLI's "keep looking" option, capped at `OFFER_BOARD_HARD_CAP` as a safety valve, not
  a design limit) rather than resetting the board — nothing about the board size is hard-stopped.
  Accepting one listing quietly resolves every other listing on that board through the background
  industry (§10.0), the same as a single declined offer always has; declining the whole board
  (`decline_board()`) does the same for all of them and advances the year once. Still 0-1 projects
  per year — more choice about *which* film, not more films at once. This is the only offer-board
  implementation in the playable game — `simulation/cli.py` reaches it exclusively through
  `Session`, never a second, parallel code path; `simulation/career.py`'s single-role-per-year
  `simulate_year()` is a separate, intentionally minimal harness used only by `verify.py`'s
  statistical checks, not part of the player-facing game.
- **`actor/palette.GENRE_DIAL_WEIGHTS`** and **`CANONICAL_ARCHETYPES`** are this pass's own
  documented readings, not undisclosed exact `design/` constants (§5.3 publishes target
  correlations, not the weight table itself). `verify.py creative` reports honestly against that
  gap rather than faking a pass.
- **Directing doesn't touch franchises or release strategy yet.** A directed film is always a
  Wide release and never participates in the sequel system (`simulation/_franchises.py`) — real,
  bounded follow-ups, not attempted in this pass (see "What's here now" for what directing does
  cover).
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
