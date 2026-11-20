# The Living World — World Simulation Plan

Status: proposal. **Supersedes** `npc-autonomy-and-world-state-plan.md` §3.1, §4 phases 1–3 and 5,
§5.1b and §5.5 (see §0.2 for what carries forward and what does not). This plan builds on Part 10
§10.0 ("a role you don't take isn't removed from the game"), §3.3's one-spine rule, and the
simplified decision flow in `gameplay-simplification-review.md` §4.

## 0. Summary

Today one person in Callback has a career. The 40 background and 8 tracked Rolodex NPCs
(`rolodex/rolodex.py`: `BACKGROUND_SIZE = 40`, `TRACKED_SIZE = 8`) don't work, age, earn or die,
and their `StandingModel` is rolled once in `rolodex/npc.py::generate_npc` and never advanced. A
declined role is resolved by `rolodex/casting.py::resolve_declined_role` against a weighted pick
of ~10 candidates with sampled inputs, and nobody else's career moves because of it.

This plan turns the world into a population of about **12,000 people with real careers**: 10,000
actors, about 1,000 directors and producers, and about 1,000 agents, casting directors, critics
and executives. They work at **100 studios** that release **about 600 films a year**.

**Every NPC can take every action the player can.** No verb is player-only (§4.1). What differs
is data:

- NPCs **store less**: quantized meters, a 12-byte row per credit, no per-scene or per-week
  detail.
- NPCs **resolve at a coarser grain** wherever the finer grain would only produce detail nobody
  keeps, through the *same formula functions* with coarser inputs.

Fidelity levels (§3) are storage and resolution levels, not capability levels. An NPC promoted
next to the player **rehydrates** from its compact state without visible discontinuity (§3.5).

### 0.1 Measured baselines (this repo, CPython 3, one core)

| Operation | Measured | Source |
|---|---|---|
| One full-fidelity career-year through `Session` (8 archetype policies) | ~2.7 ms | `simulation/_archetype_policies.py` |
| `actor/offers.utility()` | 4.4 µs | micro-benchmark, 20k calls |
| `actor/offers.sample_role()` | 8.3 µs | 5k calls |
| `actor/reception.resolve_reception()` | 2.8 µs | 20k calls |
| `simulation/career.simulate_project()` (shoot → quality → release → standing, scene grain) | 99 µs | 2k calls |

So `simulate_project` is only ~4% of a Session year. Most of the rest is offer-board generation
(20–30 `sample_role` + `utility` calls, repeated by "keep looking") and façade bookkeeping. In the
world sim the market replaces that board (§5.2), so the costs below are built up from the formula
costs, not from 2.7 ms × N. Rust estimates assume a **60–100× speedup** over CPython for scalar
f64 code. Milestone M1 (§9) measures this factor before any later estimate is trusted.

### 0.2 Relation to the NPC-autonomy plan

| npc-autonomy plan | Status here | Why |
|---|---|---|
| §3.1 statistical career step for the 8 tracked; decay-only for the 40 | **Superseded** | Everyone has a career. At Rust speed the real formulas cost less than the budget (§5.9) |
| §3.2 Agenda-biased project selection | **Kept, generalized** | Agendas become terms in the utility model (§4.3) |
| §3.3 one relationship record per pair, studios included | **Kept** | The edge table holds person↔person and studio↔person edges (§2.6) |
| §5.1b awards as "a single weighted roll" outside the player's races | **Superseded** | Full BuzzScore for every entrant costs about 0.3 ms per year |
| §5.3 ephemeral tier for crew; Part 16 Team exception | **Kept** | Level E (§3.2) |
| §5.4 one promotion rule | **Kept, reframed** | Promotion changes storage and resolution grain, never permissions |
| §5.4a relevance floor and regeneration | **Kept as archival and debuts** | Level A (§3.2) plus debuts from the market (§5.2) |
| §5.5 locality-gated contention | **Superseded** | Every role is contested by real people. A shortlisted matching is cheap enough (§5.2) |

## 1. Goals and non-goals

**Goals**

1. **One population, one rulebook.** Every person runs the same formulas as the player
   (§3.3, and §10.0's "the world doesn't get a simplified, fake version of casting"). The player
   is row 0 of the Person table plus a richer storage record.
2. **Full verb parity.** Every public `Session` verb has an NPC equivalent driven by a policy
   (§4.1).
3. **Real contention.** Roles, award categories, financing and release slots are contested by
   real entities. Declined roles cascade to real people, and §11.8's obituary reads real outcomes.
4. **Bounded storage.** Hot state is under 8 MB at target scale. A 60-year save is under 20 MB
   raw (about 6 MB compressed).
5. **Deterministic from a seed.** The same seed and the same player choices give byte-identical
   worlds on 1 or N threads, native or WASM.
6. **The JSON contract survives.** `web_server.py` routes and `Session` method names and
   argument shapes are unchanged. Response shapes only gain fields.
7. **Python stays the oracle.** Every pure formula function in Python is the reference the Rust
   port is tested against (§7.5). The Python world tick is the design lab.

**Performance budget**

| Measure | Target | Hard limit |
|---|---|---|
| One world-year, native Rust, 1 thread, target scale | ≤ 250 ms | **< 1 s** |
| One world-year, native Rust, 8 threads | ≤ 60 ms | — |
| One world-year, WASM in a Web Worker (single-threaded) | ≤ 400 ms | < 1 s |
| One world-year, Python reference, target scale | ≤ 5 s | 10 s |
| `Session.end_year()` latency the player feels (Rust) | ≤ 100 ms | 1 s |
| Monte-Carlo balance sweep: 1,000 worlds × 60 years, 16 cores | ≤ 30 min | — |
| Hot memory at target scale | ≤ 8 MB | 32 MB |

The estimate in §5.9 is about 52 ms single-threaded, roughly 5× under the 250 ms target. That
headroom is reserved for regions (§10.5 ×4 Standing), landmarks (§5.4) and release-date warfare
(§8.6).

**Non-goals**

- Scene-grain or week-grain detail for films nobody involved with the player will ever open.
  §10.0's scope rule changes from "simulate in full only where seen" to **"everyone has a career;
  keep detail only where it will be seen"**.
- Dense all-pairs relationships. Edges are capped per person (§2.6).
- New player-facing numbers (§8 keeps ux/05's words-not-numbers rule).
- Real-time or multiplayer. One player, one world, synchronous turns.
- Regions, eras, censorship (§10.5–10.7). The store reserves room for them, but they are not
  built here.

## 2. Entity model

### 2.1 Identity

Every entity has one `EntityId(u32)`: a 2-bit kind (Person, Studio, Franchise, Film) and a 30-bit
index. Ids are never reused, so history rows stay valid after death or bankruptcy. Hot tables are
indexed by a slot (`slot_of[id]`). Archived entities give up their hot slot and keep their cold
record.

Fixed-point convention: every 0–100 meter is stored as **Q8.8 `u16`** (value × 256, resolution
0.004). This is precise enough for §4.3's ×0.985 Prestige decay and §4.2's −0.16/yr persona
bleed, both of which would vanish under `u8`. Money is `f32` in $M. Full-level state uses `f64`.

### 2.2 Person (one shared type)

A Person has a **role bitset**: actor, director, producer, agent, casting director, critic,
writer or exec. Any combination is allowed, and the player is a Person. This replaces
`rolodex/npc.py`'s single `npc_type` string. An actor who becomes a director gains the Director
component and keeps every Person field (§3.3's "Rolodex transfers at 100%").

**Hot fields, touched every tick (all persons):**

| Group | Fields | Bytes |
|---|---|---|
| Header | role bits u8, level u8, flags u8 (alive, retired, union, insurable, disappeared, …), birth_year u16 | 5 |
| Standing (§4.3) | heat, prestige, affection, notoriety: 4×Q8.8 | 8 |
| Recognition (§4.3) | Q8.8 | 2 |
| Attributes (§4.1) | craft, instinct, presence, voice, physicality, look, resilience: 7×Q8.8 | 14 |
| Persona (§4.2) | 10 genre + 9 archetype affinities as Q8.8, consecutive_same_lane u8 | 39 |
| Career counters | credits u16, union_credits u8, award noms u8, wins u8, years_heat_below_25 u8 (§4.11 "comeback") | 6 |
| ROI memory | EWMA Q8.8 + last three u8 | 5 |
| Leverage (§6) | agent_tier u4 + scarcity u4 | 1 |
| Calendar (§4.8) | quarters_busy bitmask u8, two committed FilmIds | 9 |
| Health (§11.1–11.2) | health u8, burnout u8, conditions bitset u16, addiction stage u4 + clean_years u4 | 5 |
| Family (§11.4) | partner PersonId u32, children u8, caretaking u8, family flags u8 | 7 |
| Money (§11.6) | net_worth, peak_income, lifestyle_floor, last_income: 4×f32 | 16 |
| Guild (§10.1) | pension_years u8, residual_stream f32, qualifying_ytd f32 | 9 |
| Policy (§4.3) | agenda u8, temperament u8 (§4.12), 7 personality weights u8 | 9 |
| Links | edge-slot offset u32 + count u8, cold-record pointer u32 | 9 |
| **Total** | | **144 B** |

**Sparse components**, side tables keyed by PersonId:

| Component | Holders | Fields | Bytes |
|---|---|---|---|
| Director (§7.2–7.4) | ~1,000 | 5 attributes Q8.8; director Standing 4×Q8.8 (`DirectorState.standing`); credits; consecutive_profitable; trailing ROI and overage f32; Signature reserve (§7.8); ≤3 `DevCompact` (26 B: script id, genre, true and perceived script quality, momentum, budget_ask, quarters_in_dev, flags, attached star, financing studio, franchise and installment) | ~128 |
| Producer (§8.3) | ~300 | studio affiliation, risk appetite, budget authority f32 | 8 |
| Critic (§4.12) | ~100 | taste vector, 10×u8 | 10 |
| Contracts (§6.5, §9.7) | ~5% | multi-picture deal or merch row: studio, kind, remaining, share, locked floor | 12 each |
| Favours (§6.2) | owed ledgers | top 4 (PersonId, i8) | 20 |

**Cold fields** (history and summaries, appended at phase barriers and never read by formulas):

| Record | Fields | Bytes |
|---|---|---|
| Career summary | first and last credit year; peak Standing ×4 + peak year; genre histogram 10×u8; best hidden performance (FilmId, u8); lifetime earnings f32; career-phase tag; up to 6 notable EventIds | ~64 |
| Credit row (per credit) | FilmId u32, billing u8, archetype u8, Performance u8, Notices u8, flags u8 (transformation, breaking type, via Rolodex), fee code u8, quarters u8 | 12 each |
| Declines ring | last 8 notable declines (FilmId u32, year u16, reason u8, flags u8) | 64 |

An average career of 25 credits costs about 430 B cold.

### 2.3 Studio

There are 100 studios. Each takes one of the five `actor/studios.py` profiles (indie house,
mid-major, prestige house, blockbuster machine, streamer) as its *type*. Individual parameters are
jittered off that type, and there are 3–5 named strategic rivals per §8.8.

| | Fields | Bytes |
|---|---|---|
| Hot | type u8, strategy u8 (§8.2 Balanced, Blockbuster or Indie), capital f32, executive Standing 4×Q8.8 (§3.3 "board's patience"), boardPatience u8, slate ≤12 FilmIds, held release weeks ≤12, talent deals ≤8 × (PersonId, kind, cost) | ~260 |
| Cold | trailing 3-year slate ROI, library FranchiseIds, exec history (who ran it and when), P&L per year (60 × f32) | ~400 |

### 2.4 Film (Project, part-12's PROJECT schema)

About 1,800 films are live at once: in development, in production, or released less than a
quarter ago. §9.3's 8-quarter lag means three cohorts overlap.

| | Fields | Bytes |
|---|---|---|
| Hot (live) | studio, director, producer; genre + secondary; medium; budget, marketing f32; true script quality u8; chaos u8; franchise + installment; adaptation source; release strategy, week; stage u8; level u8 (§3); ≤8 cast slots × (PersonId, billing, archetype, char_age, fee f16) | ~150 |
| Cold (resolved) | project quality, critic, audience, zeitgeist u8; opening, gross f32; legs Q8.8; ROI f16; acquired; festival u8; awards bitset u16; runner-up PersonIds for the lead roles (§5.7) | ~40 |
| L0 only | weekly gross curve (16×f32), the player's scene shapes, the bid menu | ~200 |

### 2.5 Franchise

| | Fields | Bytes |
|---|---|---|
| Hot | genre, studio, installments, last year, prior audience, prior holdouts, last director, ≤4 principals × (PersonId, character id, indispensability f32, peak) | ~96 |
| Cold | exit records (type, year, audience at exit), reboot history | ~32 |

This is `simulation/_franchises.py::FranchiseEntry` lifted from "the player's franchises" to world
entities. `you_are_current_lead` becomes "principal[0] == player". About 300 are live.

### 2.6 Relationship edge

There is one record per unordered pair: person↔person or studio↔person. Directed fields hold
each side's view.

| Fields | Bytes |
|---|---|
| a, b EntityId; affinity a→b and b→a (i16, ×100); grudge a→b and b→a (u8); shared_projects u8; state nibble per side (§10.0 arc); last_contact u16; flags u8 (loyalty roster, held the line together, mentored); collisions u8 | 20 |

There are **at most 24 edge slots per NPC**, kept by `rolodex.py::_tracking_score` and evicted
lowest-first. The player's edges are uncapped. The current Rolodex becomes *the player's edge
list*. "The eight" (§4.12) become a UI lens, the top 8 of that list by `_tracking_score`, and no
longer a simulation tier. `_relationships.py`'s trust ledger folds into studio↔person edges, per
npc-autonomy §3.3.

### 2.7 Totals at target scale

| Table | Count | Bytes each | Total |
|---|---|---|---|
| Person hot | 12,000 | 144 | 1.7 MB |
| Sparse components | ~1,800 | ~60 avg | 0.1 MB |
| Edges (mean degree 14) + slots | 84k + 12k×24 | 20 + 4 | 2.9 MB |
| Films live | 1,800 | 150 | 0.3 MB |
| Studios, franchises | 100 + 300 | — | 0.05 MB |
| **Hot total** | | | **≈ 5 MB** |
| Cold after 60 years: ~51k persons ever, 216k credits, 36k films, ~120k notable events (16 B) | | | ≈ 13 MB |

## 3. Fidelity model: resolution and storage levels

### 3.1 The principle

A level never decides *what a person may do*. It decides two things:

- **Resolution grain**: how finely a verb's outcome is computed (scene, project or year).
- **Retention**: what is kept afterwards (the full record, a compact row, or a frozen record).

Both grains call the **same formula functions**. The coarse grain feeds them coarser inputs: one
performance read instead of twelve dials, the closed-form Gross instead of the weekly curve, an
on-set event resolved by its default response instead of a prompt.

The coarse inputs are the ones `gameplay-simplification-review.md` §4 already defines for the
player's "auto unless opened" flow. So an L1 NPC resolves exactly as a player who left every
default alone would. That is the parity guarantee: **NPC grain = player grain with defaults
accepted.**

### 3.2 Levels

| Level | Who (per year) | Resolution grain | Retention | Count |
|---|---|---|---|---|
| **L0 Full** | The player; every principal on the player's current project(s) (cast, director, producer, the financing studio); anyone in a live negotiation with the player (holdout, hire offer, attachment) | **Scene and week**: per-scene dial reads (§5.6), on-set moment chains (§5.12), generosity and upstaging (§5.7), weekly gross curve, bid menus | The player keeps everything (`ProjectResult`, `DeclinedRoleRecord`, …). L0 NPCs keep compact rows only; their scene detail lives in the *player's* film record | 1 + ~6–15 |
| **L1 Project** | Anyone with a project stage this year: shooting, developing, releasing, campaigning | **Project**: one read per role, the event pool rolled with default responses, closed-form box office, bids auto-picked by the producer's policy | Compact rows (§2) | ~4,000–5,000 |
| **L2 Year** | Everyone else alive | **Year**: life, money, guild, ageing, decay, yearly verbs (agent tier, disappear, cut the floor, become a director, interactions, retirement). These are already year-grain for the player | Compact rows | ~7,000 |
| **A Archived** | Dead, or retired ≥5 years with no edge to an L0 or L1 person | None. Read only by history queries | Frozen cold record | grows ~250/yr |
| **E Ephemeral** | Unnamed extras and one-off crew (npc-autonomy §5.3) | Rolled at use (`director/composer.py` pattern) | None, unless promoted to Person | 0 stored |

Levels are recomputed per person **at the year barrier**, and again at the one mid-year point
where the player can pull someone in: casting acceptance (§3.5). Being L1 or L2 is a fact about
*this year's workload*, not a rank. A star with no project this year is L2, and a bit player in
production is L1.

Rust CPU alone does not force tiers. Running 12,000 Session-years at about 2.7 ms ÷ 70 would take
roughly 0.5 s. What forces them is everything around the CPU:

- **Storage.** Full records are about 0.6 KB per credit plus per-year Session transients: roughly
  250 MB over 60 years against 18 MB.
- **The Python lab.** At full grain the reference would need about 30 s per world-year instead of
  about 3.5 s.
- **Balance-sweep throughput.**
- **Push-budget hygiene.** NPC scene prompts have nobody to answer them.

### 3.3 Stage × level matrix

| Engine stage (existing function) | L0 | L1 | L2 |
|---|---|---|---|
| Casting market: `offers.utility`, `offer_probability`, `resolve_casting_path` | full | full | full (candidate) |
| Deal: `leverage/approvals.py`, `multi_picture_deal.py`, `merchandising.py`, `indispensability.resolve_holdout` | full, player chooses | full, policy chooses | — |
| Prep: `actor/prep.py` | full | full, policy chooses | — |
| Shoot: `career.resolve_shoot` → `positions`, `shape` | per-scene reads; §5.12 moments prompted | one read per role auto-filled (simplification §4 "one read per scene" applied to all 3); moments rolled with the default response | — |
| Quality: `career.resolve_quality` / `resolve_reception` | **once per film**, real cast performances feed `EnsembleScore` | same | — |
| Release: `studios.decide_release_strategy`, `decide_marketing_spend`, `decide_rating_cut`, `quality_adjusted_bids`, festival acquisition (§10.3) | full, with menu and weekly curve | full, auto-pick, Gross only | — |
| Standing: `standing.delta_*`, persona update (§4.2) | f64 | f64 internally, Q8.8 at barrier | decay only |
| Awards: `awards.buzz_score`, `narrative_bonus`, `apply_vote_splitting`, `resolve_category` | full, player campaigns | full, policy campaigns | — |
| Directing: `director/development.py`, `skill.py`, `edit.py`, `shoot_style.py` | quarter loop, as today | one order per project per year (simplification §4, restoring part-00 §0.5) | — |
| Life: `life/state.advance_year`, health, addiction, family, money | full | full | full |
| Guild: `world/guild.advance_year`, residuals | full | full | full |
| Ageing: `Attributes.age_decay`, `aging.apply_look_curve` | full | full | full |
| Relationships: `rolodex` state machine, interactions (§10.0) | full | full | full |

The only coarsenings are the **shoot**, the **development loop**, the **weekly curve** and
**menus**. Each of them already has an "auto" path in the simplification review. Everything that
moves Standing, money, health or relationships runs the identical function at every level.

### 3.4 Player vs NPC stored state, per subsystem

Player bytes are the Rust Full representation (f64, full history). Python objects are roughly
8–15× larger.

| Subsystem | Player (L0) stores | NPC stores | Player B | NPC B |
|---|---|---|---|---|
| Standing | `StandingModel`, 4 `Meter` f64 + bounds | 4×Q8.8 | 32 | 8 |
| Attributes | 7×f64 | 7×Q8.8 | 56 | 14 |
| Persona | 19×f64 + i32 | 19×Q8.8 + u8 | 156 | 39 |
| Career counters | recognition, credits, union credits, full `roi_history`, nominations and wins lists | counters, ROI EWMA + last 3 | 40 + 8/credit | 13 |
| Filmography | `ProjectResult` (32 fields) + `Role` (26 fields) + scene shapes + weekly curve | credit row; the film's own cold record is shared | ~650/credit | 12/credit |
| Declined roles | every `DeclinedRoleRecord` with its full reception | ring of 8 notable declines | ~300/decline | 64 |
| Rolodex | uncapped edges + favour ledger + collision counts | ≤24 edges + top-4 favours | 20/edge | ≤500 |
| Leverage | agent tier, scarcity f64, blacklist set, recommend map, favours | tier and scarcity nibbles, ≤2 blacklist ids | ~200 | 9 |
| Life | `HealthState` (conditions as strings), `AddictionState`, `FamilyState`, `MoneyState` | §2.2 health, family and money groups | ~160 | 28 |
| Guild | `GuildState`, 6 fields | 9 B | 48 | 9 |
| Directing | `DirectorState` with `ProjectSlot` + `DevProject` (25 fields each), pending choices, `DirectedReleaseSnapshot` | Director component | ~1,200 | ~128 |
| Franchises | per-franchise `FranchiseEntry` | nothing personal; principal rows live on the Franchise entity | ~140 each | 0 |
| Deals | `MultiPictureDeal`, merch tuple, approvals, bonus terms | Contracts row while active | ~120 | 12 |
| This-year transients | board (20–30 `Role`s), palette, scene dicts, pending note, bids | none; market proposals live in a phase arena freed at the barrier | ~6,000 | 0 |
| **Per entity, 60-year career** | | | **≈ 25–40 KB** | **≈ 0.6 KB** |

### 3.5 Promotion (rehydration) and demotion (compaction)

**Promotion to L0** fires when an NPC is attached to the player's project (cast, director,
producer, star attachment), opens a live negotiation with the player, or becomes the player: the
second-generation start (§11.4), or a future "continue as" mode. Rehydration is a pure function
`rehydrate(compact, history) -> FullPersonView`:

1. **Dequantize.** Each Q8.8 value becomes the f64 `v/256`, exactly. Bands rendered before and
   after promotion read identical values, so no band can flip at the moment of promotion.
2. **Rebuild the engine dataclasses.**
   - `ActorState` from the hot row (`age = year − birth_year`).
   - `roi_history` and award lists from the credit rows joined to film cold records. ROI is stored
     per film, so this is lossless for every field a formula reads.
   - `DirectorState` from the Director component, with `DevCompact` expanded to `DevProject` and
     untracked fields at their defaults.
   - The Rolodex view from the edge table.
   - Life states from bitsets: condition bits map to `life/health.py` condition names.
3. **Derive, never invent.** Detail that was never stored (past scene shapes, old offer boards,
   weekly grosses of their old films) is *not regenerated as fact*. If a screen wants "what were
   they like in X", it phrases the stored Performance and Notices bands ("She was the best thing
   in it"). **Formula-closure invariant:** the compact state contains every input any formula will
   ever read for that person. A test asserts that every input of every resolution call at L0 is
   either read from the compact state or produced during the current project.
4. **Bind streams.** The person's RNG streams are derived from (seed, id, year, phase) (§6), so
   promotion changes no future draw except those the finer grain itself consumes.

**Demotion** happens only at the year barrier:

- f64 values are re-quantized with **band-preserving rounding**: of floor and ceiling at 1/256,
  pick the one that keeps the current band (`simulation/bands.py`), and otherwise round half to
  even. The error is at most 0.004 per meter.
- The player-film detail stays with the player's film record.
- The NPC keeps its 12-byte credit row and its updated edge with the player.

**No statistical discontinuity.** L1 uses the player's own default flow, so the L0 and L1 output
distributions differ only by the policy's choices, not by the formulas. **Tier-invariance tests**
(§7.5) resolve 10,000 sampled (person, role) pairs at both grains with the same policy. They
require two-sample KS p > 0.01 on Performance, Notices, ΔHeat and ΔPrestige, and mean differences
under 0.5 points. A promote → demote round trip must return the original compact row within
quantization error.

## 4. NPC decision-making

### 4.1 Verb parity: every public Session verb has an NPC path

Groups follow `_session_bridge.METHOD_GROUPS`. Pure queries (`*_options`, `*_available`,
`*_status`, `director_info`, `rating_preview`, `trades`, …) become **feature reads** inside the
policy, so they need no separate verb.

| Session verb(s) | NPC equivalent (engine path) | Policy decides | Grain |
|---|---|---|---|
| `start(background, ambition)` | `debut()`: a Person created from one of §4.0's four backgrounds; ambition seeds the policy weights | — (sampled) | — |
| `offer_board`, `accept`, `decline_board` | Casting-market proposals (§5.2); the actor side holds or declines | accept/decline over fee, fit, lane, quarters, agenda, money pressure | L1/L2 |
| `generate_more_listings` | "Agent push": extra applications this round, taxed by `catalogue.application_fatigue_tax` | how hard to push (0–3) given hunger and tier | L1/L2 |
| `holdout_available` / `request_holdout` | Franchise principal over `indispensability` threshold → `resolve_holdout` | hold out vs sign, by greed and risk | L1 |
| `spinoff_options` / `launch_spinoff` | `_franchises.create_spinoff_entry` for any principal over `SPINOFF_INDISPENSABILITY_THRESHOLD` | pitch or not, by ambition and Ascent | L1 |
| `choose_deal` (approvals, bonus type, merch) | Same `leverage/approvals.py` and `merchandising.py` resolution | fee vs points vs approvals: risk appetite, vanity, Legacy | L1 |
| `multi_picture_deal_*` / `sign_multi_picture_deal` | `leverage/multi_picture_deal.py`; guaranteed future proposals in the market | security vs freedom: risk-averse weight | L1 |
| `request_marketing_push` | Same `decide_marketing_spend(requested_push=…)` | push if star power and ambition, cost-aware | L1 |
| `script_note_options` / `choose_script_note` | `core/script_notes.py` when approvals were won | Legacy: whole film; Ascent: your part; gambler: ambiguity | L1 |
| `available_directors` / `request_director` | Spend 2 favours (`ROSTER_FAVOUR_COST`) to pull an edge-linked director | when a Loyal director is free and favours ≥2 | L1 |
| `costar_options` / `choose_orientation` | `positions.generosity` / `upstaging` against a castmate | temperament/ego (§4.12) vs Loyalty and Mentorship | L0/L1 |
| `choose_prep` | `actor/prep.py` | §4.6 "default approach", overridden by role flags (biographical → research; accent → dialect) | L1 |
| `play_scene` | `resolve_shoot` | L0: per-scene read; L1: one read (Match, Hold back, Go big, Against) by risk appetite | L0/L1 |
| `choose_rating_stance` | `decide_rating_cut` | release as shot vs cut, under studio pressure | L1 |
| `choose_release` (+ bid policy) | `decide_release_strategy` with the NPC's request, `quality_adjusted_bids` | request only when influence matters (simplification §4); bids "best" or "self" | L1 |
| `run_awards_campaign` (category, fraud) | `awards.buzz_score` with `CampaignSpend`, `category_fraud` | campaign if expected nomination rank ≤ 7 and money/quarter affordable; fraud by risk appetite and Notoriety tolerance | L1 |
| `interact` (check in, show up, read agenda, vouch) | `rolodex/interactions.py` on the NPC's own edges | ≤2 per year, aimed by agenda (Loyalty: check in; Ascent: show up for the hottest edge; Redemption: vouch) | L2 |
| `try_advance_agent_tier` | `catalogue.advance_agent_tier` | automatic if eligible (as the simplification review proposes for the player) | L2 |
| `disappear` | `catalogue.accumulate_scarcity` | Legacy or prestige weight, high Heat, money cushion | L2 |
| `cut_lifestyle_floor` | `life/money.py` floor cut | money stress × prudence; a denial bias makes it late, as §11.6 says | L2 |
| `become_director` | Director component created | Legacy agenda, credits ≥ 3, vision proxy, age | L2 |
| `start_directing_project` | `DevCompact` created (genre, budget tier, self-financed) | genre from Persona lane and heat; tier from Standing | L1 |
| `advance_directing` (9 dev actions) / `scrap_directing_project` | `director/development.py` actions; attachments use `attachment_offer_probability`, *and the target star's own policy accepts or refuses* | one order per project per year: push, rewrite, attach, financier, drawer, scrap | L1 |
| `check_for_hire_offer` / `accept_hire_offer` / `decline_hire_offer` | Studio slate phase issues `HireOffer`s to directors (§5.1) | fee vs passion (§7.3 engagement ±) | L1 |
| `run_director_awards_campaign` | Same as the actor campaign, director categories | as above | L1 |
| Strike response (`world/strikes.py`: hold, interim, cross) | Every union person decides when a strike fires | money stress vs loyalty and held-the-line flags | L2 |
| `blacklist` / `recommend` (`leverage/catalogue.py`, §6.6) | Producers and directors adjust market weights | grudge ≥ 40 → blacklist; Mentorship → recommend | L1/L2 |
| Life choices (`family.refuse_caretaking`, therapy, partner) | Same `life/` functions | family weight vs career heat | L2 |
| `end_year` | The world tick (§5) | — | — |
| `obituary_summary` | `generate_obituary` for any Person (NPC obituaries feed the trades, §8) | — | — |
| *(new, both sides)* retire | Flag set, Legacy transition on edges (§10.0 "Losing them") | age, Standing, money, health; the player gets the same verb as an explicit "hang it up" | L2 |

### 4.2 The utility model

Each decision is a choice among options `o` from the same option set the player sees:

```
U(o | p) = Σ_k  w_k(p) · f_k(o, p)  +  τ(p) · G_o          // G_o ~ Gumbel(0,1), from p's stream
choice   = argmax_o U(o | p)                                // Gumbel-max ≡ softmax sampling
```

Shared features `f_k`, each computed with existing formulas on *perceived* inputs:

| Feature | Formula source |
|---|---|
| money: fee and expected backend vs the lifestyle-floor gap | `offers.negotiated_fee_share`, `life/money.py` floor |
| expected ΔHeat / ΔPrestige / ΔAffection | `standing.delta_*` at the film's expected ROI (§8.2 tier median) and the person's expected Notices |
| fit and lane: in lane, breaking type, staleness | `offers.fit_score`, `in_lane`, `is_breaking_type`, §4.2 staleness |
| calendar cost: quarters, conflicts, burnout | `quarters_for_role`, §4.8 burnout |
| risk: outcome variance (tier P(>2×), σ = 16 − 0.09·Craft) | §8.2, §4.7 |
| relationships: affinity with attached people, agenda served (×1.6, ×1.0 or ×0.6) | `rolodex/npc.agenda_multiplier` |
| franchise and indispensability | `_franchises`, `leverage/indispensability.py` |
| life load: health, caretaking, children, addiction stage | `life/` |

**Information parity.** NPCs read the inputs the player would see, including Taste-noised
perceived script quality (`ProjectSlot.perceived_script_quality`) and never `latent_quality` or
true script quality. An NPC can misjudge a script exactly as the player can.

### 4.3 Personality = archetype mixture + agenda + temperament + age drift

- **Archetype prior.** The eight scripted policies in `_archetype_policies.py` become eight weight
  vectors over the features above:

  | Policy | Weights it leans on |
  |---|---|
  | `prestige_chaser` | prestige and awards high |
  | `franchise_maximizer` | franchise, holdout, money |
  | `indie_purist` | low budget, self-release, prestige |
  | `risk_averse` | variance strongly negative, multi-picture deals |
  | `gambler` | variance positive, high τ |
  | `director_track` | directing and Legacy |
  | `family_first` | life load, fewer quarters |
  | `burnout_avoider` | burnout, rest blocks |

  Each NPC draws mixture weights from a Dirichlet(α = 0.6), so most people are one or two types.
  Weights are stored as the 7 personality bytes (§2.2) after projection.
- **Agenda** (§10.0, `rolodex/npc.AGENDAS`) multiplies terms:

  | Agenda | Effect |
  |---|---|
  | Ascent | ×1.5 on Heat and billing |
  | Legacy | ×1.5 on Prestige; directing bias; §10.0's "devSlate weights ScriptQuality over Difficulty" |
  | Loyalty | ×2 on relationship |
  | Redemption | bonus for comeback-shaped roles after a Standing trough |
  | Vindication | bonus when a rival edge is in the same race |
  | Mentorship | ×2 on recommend and champion verbs |

- **Temperament.** `N(50, 22)`, rolled once (§4.12). It feeds chaos, upstaging and τ.
- **Age drift.** Risk weight × (1 − 0.01·(age − 30)⁺), and Legacy weight rises after 50,
  matching §4.9's "the transition is a playable arc".

### 4.4 Calibration

1. **Archetype equivalence.** Run each scripted archetype through `Session` (today's code) and run
   the matching pure-archetype NPC policy through the world tick at the same scale. Distributions
   of credits per year, billing mix, net worth at 60 and award nominations must match (KS
   p > 0.01). Weights are fitted by CMA-ES in the Python lab.
2. **Population targets.** The mixed population must reproduce §14.9's seven career-shape targets
   (median career 26 years, ~18% reaching Heat > 80, ~55% with zero nominations, median earnings
   $6–11M, …). It must also reproduce §14.2 slate economics and §14.4 genre-cycle statistics
   *with the population as the actual input*, closing the open caveat in §14.4.

## 5. The yearly tick

### 5.0 Phase order and the player's turn

```
 Y.1  Slate & development     studios greenlight; directors' dev orders; hire offers
 Y.2  Casting market          proposals → [PLAYER: offer_board / accept / decline] → cascade
 Y.3  Deal, prep, production  [PLAYER: deal, prep, play_scene] ; L1 resolve ; per-film quality
 Y.4  Release & market        release decisions, festivals, bids, box office; GenreHeat ×4 quarters
 Y.5  Awards                  BuzzScore for all entrants → [PLAYER: campaign] → ceremonies
 Y.6  Life events             health, addiction, family, money, guild, mortality, retirement
 Y.7  Relationships & ageing  edges from co-work, decay, arcs, interactions, Standing decay, ageing
 Y.8  Trades, news, levels    events → salience → digest; compaction; level recompute; debuts
```

`Session` keeps its method names. Each player verb advances the world state machine to the next
phase that needs the player's input (`world.run_until(PlayerInput)`), so `offer_board()` runs Y.1
and the first market pass, and `end_year()` runs Y.4–Y.8. The player's directing order (Y.1) is
the one verb that comes *before* the board. In world mode it is queued and applied at Y.1 of the
next year if the player skips it, and `advance_directing()` called before `offer_board()` applies
it immediately.

### 5.1 Slate and development (§8.2, §7.4, §7.13, §9.3)

- **Studios.** Each studio picks its slate size and tier mix from its strategy (§8.2 Balanced,
  Blockbuster or Indie) and capital. Tier counts are scaled by §9.3's
  `greenlit[g] = 1.0 + 1.2 × GenreHeat[g]/25`.
- **Supply.** Projects come from three sources: directors' `DevCompact`s seeking finance, studio
  IP (`_franchises.sequel_probability`), and adaptations (§9.4).
- **Greenlight.** `package_strength` → `greenlight_probability`, evaluated against the studios
  whose `budget_range` fits. That is about 20 per project, via `pick_studio`'s band.
- **Crew.** Studio-originated films issue `HireOffer`s to directors, chosen by director Utility
  over Director-component holders. Producers attach from studio affiliation.
- **Complexity.** O(D·S_b) with D ≈ 1,500 dev projects and S_b ≈ 20 → ~30k evaluations.

### 5.2 The casting market (§4.4, §10.0)

About **3,600 named role slots a year**: 600 films × ~6 (1–2 leads, 2–3 supporting, 2–3 bit).
Extras are level E.

1. **Candidate shortlist.** Actors are bucketed by (age band of 5 years × top-2 archetypes ×
   Standing band of 5); the index is rebuilt each year in O(N).
   - A cheap prefilter (gatekeeper-weighted StandingScore plus the lane test, about 5 ns) scans
     ≤256 bucket members around each role.
   - Exact casting-side `offers.utility()` (§4.4) runs on the top **K = 48**.
   - Forced inclusions: the attached director's edges with affinity > 70 (the Rolodex direct-offer
     path), §6.6 recommended people, and multi-picture or spin-off guarantees. Blacklisted people
     are removed.
2. **Paths, unchanged from §4.4.** Each shortlisted candidate gets a path:
   - direct offer: the director's affinity > 70;
   - offer: `Utility − difficulty > 14`;
   - audition: a Bernoulli draw of `P(offer)` from the *candidate's* stream, only if the
     candidate applies. Applications are bounded by agent tier reach (§4.5) and taxed by fatigue.
3. **Matching: role-proposing deferred acceptance over up to 8 rounds.**
   - Each unfilled role proposes to its best remaining eligible candidate (direct offers first,
     then offers, then audition passes, by casting Utility).
   - Each actor holds the proposals with the highest *actor-side* policy utility (§4.2), subject to
     a non-overlapping `quarters_busy` capacity (≤4 quarters, ≤2 concurrent holds) and rejects the
     rest.
   - Ties break on (utility, EntityId), so the result is deterministic.
   - Each role proposes to each candidate at most once, so at most R·K = 173k proposal events, each
     O(log h) at the holder. Quarter capacity makes this a greedy approximation of a stable
     many-to-one match: no cycling, not guaranteed stable. Nobody outside can tell.
4. **The player.** The player is an actor row whose actor-side choice comes from the UI.
   - Proposals reaching the player are reserved, capped at ux/03 §1's 2–7 cards, plus at most 2
     long-shot auditions. `offer_board()` returns them in today's listing shape.
   - After `accept`/`decline_board`, released roles re-enter the market. A second, small pass
     cascades them to the next candidates. This is §10.0's `CastingResolution` made literal, and
     it replaces `rolodex/casting.resolve_declined_role`.
   - Five roles are tied up for one round out of 3,600, which makes no measurable difference.
5. **Debuts.** A role still unfilled after round 8 goes to a generated newcomer (one of §4.0's
   backgrounds, age 18–30), *created as a Person*. This is how the pool replenishes, about 650 a
   year against about 250 deaths and retirements and about 400 people drifting out of work for
   good.
6. **Runner-ups.** For each lead role, the best loser is stored on the film record. Same role
   lost three times → `register_collision` → RIVAL (§10.0), now from real contention.

Cost: prefilter 3,600 × 256 ≈ 0.9M cheap ops; exact utility 3,600 × 48 × 2 sides ≈ 345k; matching
≈ 173k heap operations.

### 5.3 Production resolution (§4.7, §4.10, §5.6, §5.12)

Per film, the level is the max level of anyone attached, so the player's films are L0. Each cast
member's Performance is resolved at their grain (§3.3). Then **one** `resolve_reception` runs per
film with `EnsembleScore` built from the *real* cast's billing-weighted performances, instead of
the sampled `restOfCast` used today. Shoot events read chaos from the real director's
temperament.

A person on two films in one year reads the pre-phase snapshot for both. Their Standing and
Persona deltas are emitted as messages and applied in film-id order at the barrier.

Cost: about 3,600 project-grain shoots plus 600 receptions, plus ~10 L0 scene-grain shoots.

### 5.4 Release and the market (§4.10, §8.2, §9.3, §10.3)

- **Per film:** `decide_release_strategy` (with the lead's and director's requests weighted by
  `actor_influence_on_studio_decision`), `decide_marketing_spend`, `decide_rating_cut`, festival
  submission and §10.3's `P(acquired)`, then `quality_adjusted_bids` / `festival_bidders` over
  studios in the budget band (~20), and the box office closed form. The weekly curve is computed
  for L0 films only.
- **GenreHeat and GenreDemand.** These advance **quarterly** per §9.3 (today's code is yearly).
  `released[g]` is the real count of films releasing that quarter. Release weeks come from the
  slate.
- **Reserved hook.** §8.6 release-date crowding is a multiplier on Opening, defaulting to 1.0. It
  is not built here.

### 5.5 Awards (§4.11)

- **Entrants:** every eligible performance and film (`eligible_performance_categories`), about
  4,000 entries.
- **Order:**
  1. A pre-campaign BuzzScore.
  2. NPC campaign decisions (§4.1).
  3. The player's `run_awards_campaign`.
  4. The final BuzzScore with `NarrativeBonus`. `NarrativeContext` is built from compact fields:
     prior noms and wins, the transformation credit flag, `years_heat_below_25`, age, retirement.
  5. `apply_vote_splitting`, then `resolve_category`.
- **Collisions:** nominees in the same category as the player record collisions.
- **Complexity:** O(E log 5) per category, with E entries.

### 5.6 Life events (Part 11)

For every live person:

- `life/state.advance_year`: health, burnout, addiction stages and the uninsurability gate
  (§11.2), family and caretaking (§11.4), money with the ~22% team take, tax and the floor ratchet
  (§11.6). Income is summed from this year's credits.
- `guild.advance_year`.
- **Partnering:** singles pick partners from their edges, which gives partner-in-industry, or
  from an off-industry draw.
- **Retirement** decision (§4.1).
- **Mortality.** A new Gompertz hazard
  `h(age) = 0.00004·e^(0.093·age) × health × addiction multipliers`: ~1%/yr at 60, ~5% at 80.

> Design-doc change needed: §11.7 says "death can arrive mid-project" but gives no hazard, and
> `life/health.py` has none. Whether the *player* can die before `MAX_AGE = 90` is a separate
> design call. NPCs need the hazard regardless.

### 5.7 Relationships and ageing (§4.12, §10.0)

- **New contact:** every film creates or bumps edges among its principals: about 45 pairs per film
  across cast, director, producer and casting director, so about 27k edge touches a year. The
  studio↔person trust edge is updated by `_relationships.update_relationship`'s asymmetric P&L
  rule.
- **Upkeep:** affinity and contact decay on all edges; §10.0 state transitions; each person's ≤2
  agenda-aimed interactions; loyalty roster updates; Legacy conversion when a person retires or
  dies.
- **Rivals:** collisions from §5.2 and §5.5 promote rivals.
- **Ageing:** `Attributes.age_decay`, `apply_look_curve`, Standing decay with `HEAT_KEEP[billing]`
  (§4.3), Recognition decay, Director standing decay (`decay_director_standing`).

### 5.8 Trades and news from real events (§10.0 "the trades")

Every phase emits typed 16-byte events: breakout, flop, record, casting news, recast, holdout,
award, scandal, death, retirement, studio exec fired (§8.9), franchise greenlit, genre boom or
bust, and others. The trades rank them:

```
salience = magnitude × proximity(player) × novelty
proximity: self 1.0 · tracked lens 0.8 · any edge 0.5 · shared franchise/studio 0.3 · anyone 0.1
```

The top 5 become the digest (pull only, §0.3 Rule 2b), rendered through `simulation/bands.py`.
Ally and Loyal edges get the private early read from §10.0's table. "Notable" events above a
threshold are kept, about 2k a year, and the rest are dropped at Y.8.

### 5.9 Cost per phase at target scale

| Phase | Complexity | Python ref (est.) | Rust 1 thread (est.) | Parallel? |
|---|---|---|---|---|
| Y.1 Slate & dev | O(D·S_b + S·P) | 0.1 s | 0.5 ms | per studio |
| Y.2 Casting market | O(N) index + O(R·B) prefilter + O(R·K) utility + O(R·K log h) match | 2.1 s | 29 ms | scoring per role; matching serial |
| Y.3 Production | O(Σ cast) + O(F) | 0.25 s | 6 ms | per film |
| Y.4 Release & market | O(F·S_b) + O(G·4) | 0.05 s | 1 ms | per film; heat reduction serial |
| Y.5 Awards | O(E log 5) | 0.02 s | 0.3 ms | per category |
| Y.6 Life | O(N) | 0.3 s | 5 ms | per person |
| Y.7 Relationships & ageing | O(F·c² + E_edges + N) | 0.45 s | 5 ms | per edge partition, per person |
| Y.6/7 Yearly verbs (policy) | O(N·V) with V ≈ 8 | 0.3 s | 4 ms | per person |
| Y.8 Trades, compaction, levels | O(Ev log 5 + N) | 0.05 s | 2 ms | serial |
| **Total** | **≈ O(N + R·K log K + edges)** | **≈ 3.6 s** | **≈ 52 ms** | **≈ 15 ms on 8 threads** |

Symbols: N = 12,000 persons, R = 3,600 roles, K = 48, B = 256, F = 600 films, D = 1,500 dev
projects, S_b ≈ 20 budget-band studios, E ≈ 4,000 award entries, c ≈ 10 principals per film.

## 6. Determinism and parallelism

- **Counter-based RNG streams.** Every draw comes from
  `stream(world_seed, phase, entity, year, sub)`: SplitMix64 hashes the key into a xoshiro256++
  state, and draws advance only that stream. The same generator and the same Box–Muller Gaussian
  are implemented in Rust and in a new `core/rng.py`.
  - No stream is shared between entities. Who else exists, or what order threads run in, never
    changes a person's draws.
  - Player verbs get sub-streams keyed by verb kind and per-year call index. The player's results
    depend on *their choices*, not on how often they opened unrelated screens, and retrying the
    same choice reproduces the same result.
  - Legacy `Session(seed)` without a world keeps `random.Random`, so today's byte-for-byte tests
    stay valid until M5 (§9).
- **Phase barriers.** Within a phase, tasks read the **pre-barrier snapshot** (double-buffered hot
  column groups) and write only their own rows. Cross-entity effects (credits to cast, edge bumps,
  income) go out as messages `(target, source, seq, payload)`. These are sorted by that key and
  applied at the barrier, so the result is independent of thread count.
- **Floats.**
  - Reductions (GenreHeat sums, studio P&L) run over fixed 1,024-entity chunks and are combined in
    chunk order.
  - No fast-math. Rust does not auto-fuse FMA.
  - Transcendentals come from the pure-Rust `libm` crate, so native and WASM are bit-identical.
  - Python's platform libm can differ by an ulp, so cross-language parity uses a tolerance with
    per-barrier resync (§7.5).
- **What runs in parallel.** Y.1 per studio, then greenlight conflicts resolved by priority
  (studio type, id). Y.2 scoring per role, then matching serially or by independent billing and
  medium segments. Y.3 and Y.4 per film. Y.5 per category. Y.6 per person. Y.7 per edge partition
  (by min id) and per person. Y.8 serial.
- **World hash.** A world hash (xxh3 over hot columns) is taken after every phase. CI asserts
  equality across 1/2/8 threads and native/WASM for 20 seeds × 60 years.

## 7. Rust architecture

### 7.1 Crate layout

| Crate | Contents | Depends on |
|---|---|---|
| `callback-core` | Q8.8 types, meter configs, counter RNG, band tables (generated from `bands.py`) | — |
| `callback-formulas` | Pure functions mirroring Python modules 1:1: `offers`, `standing`, `persona`, `reception`, `release`, `studios`, `aging`, `life`, `guild`, `genre_cycle`, `franchise`, `indispensability`, `awards`, `director/{skill,development,edit,shoot_style}`. f64 in, f64 out, RNG as a trait | core |
| `callback-world` | SoA store, entity tables, edges, credits, events, phases, scheduler, compaction, rehydration | core, formulas |
| `callback-policy` | Utility model, personality, archetype weight sets (data files fitted in Python) | core, formulas, world (read views) |
| `callback-session` | Port of `Session`: player Full state, method registry with the same names and arguments, serde response structs, `describe_methods` | world, policy |
| `callback-server` | HTTP server reproducing `web_server.py`'s routes | session |
| `callback-wasm` | `wasm-bindgen` exports: `new_game`, `call(method, args_json)`, `status`, `auto_play` | session |
| `callback-py` | `pyo3` bindings: formulas plus the world tick for fast sweeps from the Python lab | formulas, world |

The dependency direction mirrors the Python rule (`core` → formulas → world → session).

### 7.2 Data-oriented store: grouped SoA, not an ECS

Columns are grouped by phase access ("hybrid SoA"):

- `CastingView` {standing, attrs, persona, birth_year, calendar, agent} is read together by Y.2.
- `LifeView` {health, family, money, guild} is read by Y.6.
- Sparse components are sparse sets keyed by PersonId.

Why not an ECS (bevy_ecs, hecs):

- There are four fixed entity kinds. Components are mostly dense (every person has Standing and
  Life) and the few sparse ones are known up front. ECS archetype churn would buy nothing.
- Phases are a fixed, ordered batch pipeline, so a dynamic system scheduler only adds
  nondeterminism risk.
- Index-order iteration is the determinism story. Serialization is "dump the columns", and
  compaction is a column copy.
- There is no ECS dependency to carry into WASM.

Cache budget: Y.2 streams about 12,000 × 72 B ≈ 0.9 MB of `CastingView`, which fits in L2/L3.

### 7.3 Serving the Session and JSON API

- **Native server (drop-in).** `callback-server` uses axum on tokio, behind a `Mutex<Session>`
  per game.
  - Same routes: `POST /api/games`, `GET /api/options`, `GET /api/games/<id>/status`,
    `POST /api/games/<id>/call {method, args}`, `POST /api/games/<id>/auto_play`.
  - Same status codes: 400 `GameError`, 404, 500.
  - Same `STATUS_QUERIES` dashboard and the `bid_policy` convention. It serves `web/dist`
    statically.
  - The frontend changes only its base URL.
- **WASM in the browser.** The world runs in a Web Worker (about 5 MB of memory).
  - A transport implementing the same `call(method, args)` interface as today's HTTP client
    replaces `fetch`. That is a later `web/` change and is not part of this plan's edits.
  - Single-threaded (rayon off), so expect about 1.5–2× the native single-thread time: about
    100 ms per year.
  - Saves are column snapshots plus the event log in IndexedDB (zstd, about 6 MB at 60 years).
- **Contract rule.** Response dicts only *gain* keys, for example `why_it_reached_you`,
  `up_against` or `career_band` on Rolodex cards. Keys are never renamed or retyped.

### 7.4 Python's role

- **Reference.** New modules follow CLAUDE.md (frozen dataclasses, design-section docstrings,
  one-way imports):
  - `core/rng.py`;
  - a `population/` package on `core`/`actor` holding compact Person, Studio and Film records,
    quantization and `rehydrate`;
  - `simulation/_world_tick.py`, `_market.py` and `_npc_policy.py`, keeping composition in
    `simulation/`.
  - At 12,000 entities × ~10 phases, `replace()` costs about 0.25 s a year, which fits the 5 s
    budget. No convention exception is needed.
- **Design lab.** Policy fitting (CMA-ES), tuning sweeps, and `verify.py` extended with
  population checks. Sweeps can call the Rust tick through `callback-py`.

### 7.5 Parity testing (Python is the oracle)

| Layer | Method | Pass criterion |
|---|---|---|
| **Formula parity** | `simulation/_parity_vectors.py` (new) samples 10k inputs per pure function. Stochastic functions run with a **recording RNG** that logs each call (`random`, `gauss`, `uniform`, `choices`, `randint`) and its return value; Rust replays the values and asserts the same call sequence. JSONL golden files are checked in | \|Δ\| ≤ 1e-9 relative; identical call sequence |
| **Stage parity** | Python and Rust world ticks in "parity mode" (shared counter RNG); per-phase hash and field diff; Rust resyncs from Python at each barrier so ulp drift can't compound | integer fields equal; floats within 1e-7; ≤0.1% Q8.8 cells differing by 1 LSB |
| **Tier invariance** | §3.5: L0 vs L1 on the same (person, role) pairs; promote/demote round trip | KS p > 0.01; mean Δ < 0.5; round-trip within quantization |
| **Statistical parity** | 1,000 seeds × 60 years in both: §14.1, §14.2, §14.4 and §14.9 targets, and archetype equivalence (§4.4) | KS p > 0.01 per metric; targets within the documented bands |
| **Contract parity** | Recorded transcripts of scripted sessions (the 8 archetypes) against Python `web_server.py` and the Rust server, diffed structurally | identical key sets and JSON types for every method |

## 8. Player-facing payoff

All of it goes through ux/05's three-step words-not-numbers pass. Names and bands, never figures;
Heat and the other three render only as a bar and a word.

- **Rivals with real careers.** "The part went to Dana Okafor. Third time this year it's been
  her." A rival comes from real lost roles and shared categories (§10.0's ranking, now fed by
  real contention), and you can watch them peak, flame out, or outlast you.
- **The declined-role ledger, true at last.** "You passed on *Low Tide*. Marisol Vega took it, and
  it made her." §11.8's line is a database lookup, not an assertion.
- **Offer cards with a reason and a field.** "Reached you because Kessler asked for you." "You're
  up against someone hotter." The board shows real proposals (2–7 cards, ux/03 §1), which fixes
  the slot-machine board of simplification §3.6.
- **Trades about real people.** "Prestige house Halcyon fires its chief after a third bad summer."
  "Ravi Shah's directing debut is the one everyone's talking about." "In memoriam: Ines Calder,
  who directed you three times." Every line comes from an event.
- **A Rolodex that has moved.** A director you haven't seen in 15 years is whoever 15 simulated
  years made them (§10.0, "NPCs have careers, not appearances"). Cards show a career band: "on a
  run", "cooling off", "out of the business".
- **Awards nights with real fields.** The nominee list is named people with real films. "Vote
  splitting cost you both." "The fraud campaign worked — for her."
- **Franchises that live without you.** A recast names the actor who replaced you, and the trades
  follow their installments.
- **The obituary among peers.** "Of the people who started out the year you did, almost none were
  still working at fifty. You were." "The director who gave you your first lead died at 71; you
  outlived most of that set." NPC obituaries make the industry's memory real, and a
  second-generation child (§11.4) can *become* the player through rehydration (§3.5).

## 9. Migration plan

Each milestone ships on its own, keeps `python3 -m unittest discover callback/engine/tests`
green, and records a benchmark in `callback/docs/design/world-sim-bench.md` (to be created at M1).

| # | Milestone | Ships | Benchmark gate | Exit criteria |
|---|---|---|---|---|
| **M1** | **Rust prototype: the L2 (Ambient) tick at full scale** | `callback-core`, a `callback-formulas` subset (standing decay, ageing and look curve, life and money ratchet, guild, mortality draft), SoA Person table of 12,000, counter RNG, CLI population report | 60 world-years L2-only < 1 s total; measures the Python→Rust factor on these formulas | formula parity green for the subset; world hash equal on 1 vs 8 threads |
| **M2** | Python reference population | `core/rng.py`, `population/`, `simulation/_world_tick.py` (L2 phases), quantization and rehydration | Python L2 year ≤ 0.5 s at 12k | stage parity with M1 per barrier; round-trip test |
| **M3** | Studios, market and project-grain production (L1) | Y.1–Y.4 in both languages: slate (§8.2), casting market (§5.2), production, release, quarterly genre cycle (§9.3) | Rust ≤ 150 ms per year (1 thread); Python ≤ 4 s | §14.1, §14.2 and §14.4 reproduced *from the population*; debuts keep N within ±5% over 60 years |
| **M4** | NPC policy, full verb set | `_npc_policy.py` and `callback-policy`; every row of §4.1; awards for all (Y.5); life, relationships and trades (Y.6–Y.8) | Rust ≤ 250 ms per year; Python ≤ 5 s | archetype equivalence (§4.4); §14.9 targets on the NPC population; verb-coverage test (every §4.1 verb fires ≥ 100× per 1,000 world-years) |
| **M5** | The player joins the world (Python first) | `Session(seed, world=True)`: board from the market, cascade on decline, L0 promotion of castmates, Rolodex as edges, trades from events, additive JSON fields; legacy mode kept | `end_year()` ≤ 5 s in Python | tier-invariance tests; all existing tests green in legacy mode; contract snapshots recorded |
| **M6** | Rust Session and server | `callback-session` and `callback-server` as a drop-in for `web_server.py` | `end_year()` ≤ 100 ms; p99 `call` ≤ 5 ms | contract parity on the 8 archetype transcripts; frontend runs unchanged against it |
| **M7** | WASM, saves, parallel phases, balance harness | `callback-wasm` in a Worker; save and load; rayon phases; `verify`-equivalent Monte-Carlo in Rust | WASM year ≤ 400 ms; 1,000×60 sweep ≤ 30 min on 16 cores | native/WASM/threads hash equality; save → load → continue is byte-identical |
| M8 *(optional)* | Depth on the same store | §8.6 release-date crowding, §8.9 exec firing, §5.4 landmarks, §10.5 regions | stays ≤ 250 ms per year | each behind a flag, verified per Part 14 |

**Design-doc follow-ups this plan creates** (owner: design, before M4/M5):

- §11.7 mortality hazard.
- §10.0's scope paragraph, rewritten per §1.
- §4.12's "~40 background" becomes "the world population; the eight are a lens".
- part-12's `simulatedInFull` becomes `level`.
- A player-side "retire" verb (§4.1).
- §9.3's quarterly cadence, confirmed against today's yearly `world/genre_cycle.py`.
