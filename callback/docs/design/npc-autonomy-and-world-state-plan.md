# World State & NPC Autonomy — Implementation Plan

Status: proposal. Companion to `creative-revamp-plan.md` and `part-16-the-team.md` — this one targets
the world simulation layer (Part 10) rather than scene grammar or delegation.

## 1. Where things stand today

- **Rolodex (`rolodex/`)**: 40 background NPCs + 8 dynamically tracked, each with `affinity`,
  `grudge`, `shared_projects`, `last_contact_year`, a hidden `Agenda`, and a named relationship
  state (Stranger→Familiar→Ally/Rival→Loyal/Estranged→Legacy/Severed). Tracked NPCs (director,
  costar, producer types) also carry a `StandingModel` (Heat/Prestige/Affection/Notoriety) —
  but **nothing ever advances it**. It's initialized once from a gaussian roll and then only
  changes if the player directly vouches for them. NPCs don't work, age, or have careers.
- **Studio/director trust (`simulation/_relationships.py`)**: separate trust ledger keyed by
  studio/director id, updated from P&L asymmetrically. Lives outside Rolodex entirely — a studio
  you've made films with and a producer NPC in your Rolodex are two disconnected records even
  when they're the same relationship in fiction.
- **Genre cycle (`world/genre_cycle.py`)**: one global heat dict per genre, fed by resolved films
  (yours and, per the docstring, "every resolved film in the background industry" — but nothing
  in `world/` actually resolves background films; only the player's own ROI calls
  `accumulate_heat`). So "the background industry" is currently aspirational, not simulated.
- **Guild/strikes/trades (`world/guild.py`, `strikes.py`, `trades.py`)**: eligibility, strike
  triggers, and a trade digest — these react to the player's career, not to a simulated industry.
- **Franchises, adaptations (`simulation/_franchises.py`, `_adaptations.py`)**: per-project rolls,
  not persistent state carried by an NPC or a franchise-as-entity.

Net gap: there is no tick that makes the world move on its own. Every NPC's Standing, every
studio's slate, every genre's heat is either static or a pure function of the player's actions.
"Autonomy" doesn't exist yet — the pieces to build it (StandingModel reuse, Meters, pipeline
Stage protocol, band rendering) already do.

## 2. Goal

Two outcomes, one substrate:

1. **NPC autonomy**: tracked (and eventually background) NPCs run their own lightweight careers
   year over year — they take roles, get reception, their Standing moves, their Agenda pulls them
   toward or away from you, they age out or break through — independent of whether the player
   ever interacts with them.
2. **Perfected studio-actor-director interactions**: one relationship record per (player, entity)
   pair, whether the entity is a studio, a director NPC, or a producer NPC, feeding casting,
   negotiation, and reception consistently — no more split-brain between `_relationships.py` trust
   and `rolodex` affinity.

## 3. Design

### 3.1 A `WorldTick` stage, run once per year alongside the player's own year

New module: `world/npc_sim.py`. Not a full per-scene resolution (too expensive for 40+ NPCs ×
15+ years) — a **statistical career step** reusing existing formulas at a coarser grain:

- For each active NPC with a career-relevant type (`director`, `costar`, `producer`), roll
  whether they book work this year (probability from their current Standing, same shape as
  `actor/offers.py`'s utility curve, no need for a new formula — call the existing one with a
  synthetic "self" state).
- If booked: sample a project tier from `studio/slate.py`, resolve a reception score via
  `actor/reception.py`'s existing quality/critic/audience blend (cheap: skip the scene-by-scene
  path, just roll craft/luck once), and apply the resulting Standing deltas through
  `core/meters.py`'s `StandingModel.add` — the exact mechanism already driving the player and
  already partially wired for NPCs.
- Feed the *aggregate* of these resolutions into `world/genre_cycle.accumulate_heat` per genre,
  finally making the "fed by every resolved film in the background industry" docstring true.
- NPC career arcs: age tracked per NPC (reuse `actor/aging.py`'s curve), retirement/death rolls
  above a threshold age flip `active=False` and `relationship_state="legacy"` — this already
  exists as a state, just nothing sets it from a career event yet.

Cost control: only tracked NPCs (8) get the full roll every year. Background NPCs (40) get a
cheap decay-only pass (Standing drifts toward genre-cycle baseline) and are promoted into a full
roll only if `recompute_tracked` picks them up. This keeps the yearly cost O(8), not O(40).

### 3.2 Agenda-driven autonomy, not just stat drift

An NPC's `Agenda` (Ascent/Legacy/Loyalty/Redemption/Vindication/Mentorship) should bias their
career roll, not just their reaction to player interactions:

- Ascent NPCs preferentially take higher-billing swings even at reception risk.
- Legacy NPCs bias toward director/producer credits over pure acting.
- Redemption NPCs are more likely to accept a comeback-shaped project after a Standing trough.

This reuses `AGENDA_COMMON_TYPES` and the existing multiplier constants in `rolodex/npc.py` —
just applies them to the NPC's own project selection instead of only to how they respond to the
player's gestures.

### 3.3 Unify studio/director/producer relationship into one record

Fold `simulation/_relationships.py`'s trust ledger into `rolodex/npc.py`'s NPC model:

- Give studios an `NPC`-shaped record too (new `npc_type="studio"`, or a parallel
  `StudioRelationship` dataclass reusing the same `StandingModel`/trust fields — prefer reusing
  `NPC` directly since `core/meters.py` was already built type-agnostic for exactly this).
- Replace `_relationships.py`'s standalone trust float with the NPC's own `affinity` field, so a
  studio relationship decays/grows through the *same* asymmetric P&L-driven update it already
  uses, but the number becomes visible in the Rolodex/relationship-state machinery instead of a
  side ledger only `full_career.py` reads.
- Casting (`director/casting.py`), approvals (`leverage/approvals.py`), and offer utility
  (`actor/offers.py`) all currently take a bare `trust: float` or `standing` parameter in various
  shapes — converge them on reading `NPC.affinity` / `NPC.standing.weighted_score()` so a single
  source of truth drives fit, price, and greenlight odds everywhere.

This is the "perfected" part of the ask: today a director's trust in you and a director's Rolodex
affinity in you can silently disagree. After this, they're the same field.

### 3.4 Wire it into the yearly loop

`simulation/full_career.py::advance_between_years()` already runs Life, Leverage, Guild, strikes,
and genre-cycle updates once a year. Add the `WorldTick` call in the same place, after the
player's own reception resolves (so genre heat reflects this year's full slate, player included)
and before `recompute_tracked` re-ranks the Rolodex (so a breakout NPC's shared_projects/Standing
bump can actually promote them into the tracked eight the same year it happens).

### 3.5 Surface it to the player

Nothing here needs new UI mechanics — `simulation/bands.py` already renders every hidden score as
qualitative bands. Add:
- A yearly "industry digest" line (reuses `world/trades.py`'s existing trade-digest shape) noting
  NPC breakouts/flops: "Marcus Reyes just had his first hit" — cheap narrative payoff for a system
  that's otherwise invisible.
- Rolodex NPC cards show their current Standing band, same renderer as the player's own.

## 4. Phased implementation

1. **NPC career step (no unification yet)** — `world/npc_sim.py` with the yearly roll for the 8
   tracked NPCs, wired into `full_career.advance_between_years`. Verify: Standing on tracked NPCs
   changes across a 15-year run without any player interaction; `test_world.py` gets a new case
   asserting non-static NPC standing.
2. **Genre cycle from the background industry** — feed NPC resolutions into
   `accumulate_heat`, confirm booms/busts emerge without player-only data. Verify: run
   `_full_data_report.py`-style headless sim, assert genre heat variance is measurably higher than
   player-only baseline.
3. **Agenda-biased project selection** — apply Agenda weighting to the NPC career roll from 3.2.
   Verify: statistical test that Ascent-agenda NPCs' average billing trends up over N years vs.
   Loyalty-agenda NPCs.
4. **Relationship unification** — migrate `_relationships.py` trust into `NPC.affinity`/`standing`,
   update all call sites in `casting.py`, `approvals.py`, `offers.py`. This is the riskiest step
   (touches the most call sites) — do it behind the existing test suite, one call site at a time,
   running `pytest` after each migration.
5. **Background-NPC promotion pass + player-facing digest** — cheap decay-only pass for the other
   32, trade-digest lines, Rolodex Standing bands in the UI-facing `Session` output.

Each phase is independently shippable and testable; nothing in 1–3 requires 4, and 4 can land
whenever call-site migration is convenient — the two tracks (autonomy, unification) don't block
each other except at the final digest step.

## 5. Scaling architecture — how far this can grow without dying

§3–4 sizes everything to the current pool (40 background / 8 tracked). This section is the
design for growing that pool — more NPCs, richer studio/franchise/awards detail, deeper
cross-entity interaction — without the cost shape changing from "linear and cheap" to something
that doesn't finish.

**Read this section in two halves.** 5.1, 5.1a, and 5.1b are *theory* — reasoning about cost
shapes and worst cases to justify the design, not something the current build needs to act on.
At today's scale (40/8) none of it is measurable; it exists to show *why* the architecture below
is shaped the way it is, and to have an answer ready if pool sizes ever grow far enough to matter.
Nothing in 5.1–5.1b should gate or block any phase in §4.

5.2 onward (tiering, the ephemeral tier, the promotion/demotion rule, locality-gated contention)
is the *actually important* part — real architecture to build, specifically because §5.6 folds
its cheapest piece (a generic `Tier` field + one promotion function) into Phase 1 now, on the
theory that writing it generically costs nothing extra today and avoids a rewrite later. Everything
past 5.2 that isn't called out in §5.6 as Phase-1 work (locality-gating in 5.5, the wider knobs in
5.4b, individual studio entities in 5.2) is a later, optional deepening — worth knowing the shape
of, not worth building until the pool sizes in 5.2's table are real.

### 5.1 What's free and what isn't *(theory — justifies the design, not a build item)*

Per-entity, independent state (an NPC's own career roll, Standing decay, aging) is **O(1) per
entity per year** — nothing about resolving one NPC's year depends on any other NPC's. That means
raw pool size is close to free: 40 → 10,000 NPCs is a constant-factor increase on a baseline so
cheap it doesn't matter (sub-second even at that scale, for one playthrough).

What isn't free, and scales badly if built naively:

- **Dense cross-entity relationships.** If every NPC tracked a relationship with every other NPC,
  that's O(N²) storage and update — millions of edges at N in the thousands. The Rolodex already
  avoids this by construction (each NPC's *tracked* relationships are bounded to a small constant,
  not all-pairs) — that pattern has to hold as the pool grows, not get relaxed.
- **Simultaneous resource contention.** Casting, awards categories, and studio budgets are shared
  pools multiple entities compete for in the same year. Resolving that contention *exactly* (a
  true global assignment/auction) reintroduces non-parallel, non-independent cost. A greedy
  approximation (rank by fit/bid, assign highest first) stays cheap and is indistinguishable from
  outside the simulation.
- **Full scene-level fidelity applied to background entities.** The player's own films get
  scene-by-scene resolution (dials, positions, three-beat structure); background films get one
  aggregate reception roll (§3.1). Extending full fidelity to the whole background industry is a
  10–20× multiplier per film for detail nobody observes — deliberately not done.

### 5.1a Complexity by axis, and where the actual bottleneck lives *(theory)*

| Axis | Cost shape | Notes |
|---|---|---|
| More NPCs (N), independent yearly rolls | O(N) per year, O(N·Y) over a career | The default case; linear and small-constant |
| Dense NPC↔NPC relationship graph | O(N²) | The one true asymptotic trap — avoided by bounding tracked relationships per entity (5.1) |
| Casting/awards contention resolved exactly | O(N·M) naive scoring, worse if solved as a true simultaneous assignment | Greedy rank-and-assign keeps this ~O(N log N) |
| Full scene-level resolution vs. aggregate roll | ×S multiplier (S = scenes/film, ~10–20) | Constant-factor tax, not a complexity-class change — still not worth paying for unwatched films |

At current scale (40/8) none of this is measurable — a full 15-year career is on the order of
thousands of cheap operations, sub-millisecond. It only becomes relevant at two points: pool
sizes growing into the thousands (5.2's actor tier), or **running the simulation many times over**
for balance-tuning. A single richer-world playthrough (say N≈10,000, all independent) is still
low seconds at worst. 100,000 such playthroughs for statistical tuning is a different problem —
on the order of days of single-core compute — and the fix there is standard (multiprocess across
cores, ~10–30×) plus reducing per-update allocation cost (below), not an algorithmic change.

**The practical bottleneck at Python-implementation scale isn't big-O, it's allocation.** Every
`NPC`/`Meter` update here goes through a `@dataclass(frozen=True)` + `replace()`, i.e.
copy-on-write — each yearly tick allocates a new object rather than mutating in place. The
complexity class stays linear, but at N in the thousands with yearly updates, GC/allocation
overhead is the first thing to profile before assuming a bigger N needs an algorithmic fix. Worth
knowing before "just track more NPCs" gets blamed on the wrong layer if it ever gets slow.

### 5.1b Systems that are already depreciated, by construction *(theory, mostly — confirms no work needed)*

Not every subsystem needs new tiering work — several already resolve at the cheapest possible
grain and should stay that way rather than being "improved" toward more detail:

- **Genre cycle** (`world/genre_cycle.py`) — one float per genre. Already the minimum viable
  representation; there's no finer-grained version worth building.
- **Guild/strikes/trades** (`world/guild.py`, `strikes.py`, `trades.py`) — aggregate
  industry-level state, not per-entity. Cost is independent of pool size already.
- **Life systems** (`life/`) — inherently N=1 (the player's own state); scaling doesn't apply.
- **Awards** (`awards/awards.py`) — the full BuzzScore/narrative-bonus/category-fraud machinery is
  only worth running for a race the player or a tracked NPC is actually nominated in; every other
  category resolves as a single weighted roll for "who won," not a simulated campaign.
- **Leverage/catalogue** — scoped to relationships already; inherits whatever tier the underlying
  NPC/studio/director entity sits at rather than needing separate treatment.

### 5.2 Entity-type-specific tiering (studios / directors / actors) *(real architecture — build this)*

Rather than one flat "tracked vs. background" split across every entity, tier by type, sized to
each type's real-world count — the tripartite structure of a film (one studio × one director ×
several actors) means interactions are naturally mediated through shared films, not a dense graph,
so this is cheaper than uniform tracking, not more expensive:

| Entity type | Realistic pool size | Tracking depth |
|---|---|---|
| Studios | ~10–30 | Near-exhaustive — track all of them in real detail (replaces the current 5 fixed archetype-*types* with individual studio entities) |
| Directors | Low hundreds | Medium tier — the existing tracked-N mechanism, widened from 8 |
| Actors/costars | Thousands+ | Full three-tier ladder (tracked / background / dormant) — this is the pool numerous enough to need it |
| Composers & ancillary crew (line producer, cinematographer, one-off collaborators) | Effectively unbounded | **Ephemeral** — see 5.3 |

A single film can mix tiers freely (a tracked studio, an untracked director, three tracked and two
background actors) — detail is per-entity, not per-film, and a film touching a tracked entity is
the trigger that can promote an otherwise-background entity (5.4), not a reason to flatten
everyone else's detail down to match.

### 5.3 A fourth tier below "dormant": ephemeral, no persistent identity by default *(real architecture — build this)*

Composers (`director/composer.py`) and similar low-stakes, high-frequency roles don't need a
standing record at all in the common case — roll them fresh at the moment they're needed (skill,
cost, genre fit) and let them evaporate. Zero ongoing state, zero contribution to pool size,
O(1) per call with nothing carried between calls. This is the cheapest tier because it isn't
persistent state being *tiered down* — it's state that was never created.

**Exception, by design, not oversight:** Part 16's Team roles (agent, manager, publicist, line
producer, development exec) are persistent from first contact regardless of interaction
frequency, because the delegation mechanic needs a nameable, attributable character
("your agent took the pilot because...") — the ephemeral default is overridden explicitly for
roles a specific mechanic depends on, everything else falls through to ephemeral.

### 5.4 One promotion rule across all four tiers *(real architecture — build this)*

`ephemeral → dormant → background → tracked`, and the same rule moves an entity up a tier at any
point in that chain: **repeated or high-stakes contact with something already tracked or visible
to the player.** This is the existing `register_collision` → `RIVAL` mechanism in
`rolodex/rolodex.py`, generalized past "same NPC, repeated collisions" to "any entity, contact
with the tracked set":

- A composer hired twice by the same tracked director → promoted out of ephemeral into a real
  background NPC.
- A background actor cast opposite a tracked NPC three times → promoted into the tracked set via
  the existing `recompute_tracked` ranking (their `shared_projects`/`tracking_score` genuinely
  rises from the contact, no special-casing needed).
- A background franchise that starts sharing cast or studio with the player's own franchise →
  promoted from an aggregate franchise-fatigue signal into full `_franchises.py` tracking.
- A dormant NPC referenced again by the player (a callback, a collision) → reconstructed from
  their last frozen state rather than treated as gone.

Writing this as one rule (not a special case per subsystem) keeps the tiering logic itself from
becoming N bespoke promotion paths to maintain as more entity types get tiered.

### 5.4a Demotion: bounding N over a long simulation, not just at one snapshot *(real architecture — build this)*

5.2's pool sizes are only cheap if they stay roughly constant *over time* — a world that keeps
generating new NPCs every year (debuts) without ever retiring anyone has N grow unboundedly across
a multi-decade simulation, which eventually reintroduces real cost even though each individual
tick is O(1). `NPC.active: bool` already exists for exactly this ("False once retired/dead —
becomes legacy and stops taking interactions") — nothing currently sets it from relevance, only
(presumably) from career-end events.

The missing piece is a **relevance floor**, reusing `rolodex.py`'s existing `_tracking_score()`
(shared_projects + recency + grudge + stakes) rather than inventing a new formula: below the
floor for N consecutive years with no player contact, an entity leaves the simulated pool
entirely — no more yearly compute, state frozen at its last value. Two ways back in, both cheap:

- **Regenerated** — a fresh entity takes the freed slot (a debut), keeping pool size roughly
  constant rather than accumulating.
- **Reconstructed on demand** — if the player references the dormant entity again (a callback, a
  collision), rebuild from their frozen last-known state rather than having silently kept ticking
  them the whole time they were irrelevant.

This is what makes the "more NPCs is free" claim hold across an entire multi-decade playthrough,
not just at one fixed-N snapshot — churning pool membership instead of accumulating it.

### 5.4b Further knobs, all cheap because they widen a bound rather than remove one *(theory / later optional deepening, not Phase 1)*

Once 5.2–5.4's tiering exists, "more detail" is a set of dial-turns on the same architecture, not
new complexity classes:

- **Widen k** — raise the tracked-set size per entity type (e.g. 8 → 20–30 tracked NPCs). Still
  O(k), just a bigger constant.
- **Second-degree visibility** — extend promotion triggers one hop out: a tracked NPC's own
  tracked relationships (their rivals, frequent collaborators) get pulled into real resolution
  even before the player meets them directly. Still bounded (k × k′, both small), and it's a large
  share of "living world" texture — hearing about a falling-out secondhand before it's personal.
- **Lower the promotion threshold** — the collision/contact count that triggers tier promotion
  (5.4) is a tunable number, not an architecture decision. Lowering it promotes more background
  entities to real detail; cost scales with how often it fires, which is directly controllable.
- **Richer aggregate fallback** — give the background tier a bit more shape (a coarse trajectory
  or career-phase tag, not just a decaying float) without promoting it to full tracking, so
  entities that never cross the visibility boundary still don't feel like pure noise if looked at.

The one move that is *not* a free dial-turn is dropping the visibility gate and detail-simulating
regardless of contact with the player — that reopens 5.1's traps.

### 5.5 Locality of detail for cross-entity interactions *(real architecture, but deferred — see §5.6)*

Contention resolution (who else is up for this role, who else is nominated in this category) only
needs to be *real* when it touches the tracked/visible set — two background actors competing for
a background film's supporting role resolve statistically, since neither outcome is ever
perceived. When the player or a tracked entity is one of the competitors, pull in a small sampled
pool of plausible rivals (drawn preferentially from the tracked set) and resolve that contention
for real. Cost scales with *how many interactions cross the visibility boundary in a given year*,
not with N or N² — the same "resolve what's observed, not what's possible" principle as 5.4's
promotion rule.

### 5.6 What this changes about the phased plan in §4

Phase 1 (§4.1) should build the tiering/promotion machinery (5.2–5.4) generically from the start
— even though the current pool (40/8) doesn't strictly need it yet — rather than hardcoding
`TRACKED_SIZE = 8` as a magic constant to revisit later. A generic `Tier` field and one
promotion function that reads a per-type tracked-size table costs nothing extra to write now and
avoids a rewrite when the pool sizes in 5.2's table become real. Locality-gated contention (5.5)
is lower priority — it only matters once background entities are numerous and detailed enough
that naive full contention would be noticeable, which isn't true at the current scale — and can
land as a later phase once 5.2's pool sizes actually grow.
