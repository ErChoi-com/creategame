# Creative Mechanics Revamp — the Scene Grammar

*Plan doc, deliberately outside the part-00..15 series and its philosophy. Where this
disagrees with `part-05-the-work.md` (the 6-dial palette, the With/Beneath/Beyond/Against
"positions," the director's "note" as something you negotiate against), this plan wins for
anything it touches. Nothing here has been built yet. Supersedes two earlier drafts of this
file: v1 proposed a hand-authored setpiece list per genre (scrapped — a content-authoring
treadmill, doesn't generalize, privileges action's furniture over dialogue genres). v2
introduced the five-axis grammar but only worked it through 2-3 pilot genres and a 5-engine
table that quietly had no honest slot for a musical number or a quiet family scene. v3 closed
both gaps: the grammar covers all ten of `palette.py`'s existing genres from day one, and a
sixth Engine was added so a non-adversarial scene isn't forced into a fake contest shape it
doesn't have. v3 added eight more primary genres (war, western, crime/noir, fantasy, sports,
disaster, spy, biopic — §3.3), a real secondary-genre/hybrid mechanism so a film can genuinely
be two genres at once instead of picking one (§3.4), and a repeatable playbook for adding any
future genre or hybrid without re-deriving any of this (§10). (Genres 1-15 of the roster and a
first hybrid mechanism actually shipped in code this way — `actor/palette.py`'s 15-genre
`GENRE_DIAL_WEIGHTS`/`CANONICAL_ARCHETYPES` and `genre/hybrids.py` — ahead of this doc's own
grammar/BeatSheet build, on the existing, simpler palette pipeline; §11-§15 below are additive
to that shipped genre layer, not a redo of it.)

**v4 (this pass) is a correction, not just an addition.** Building on player feedback that the
whole point is to feel like you are actually making the movie: §2's grammar and §3's genre
tables are kept exactly as designed, but how a player interacts with them was wrong in an
earlier draft of this pass and is corrected here before any of it gets built. Three real
mistakes, caught and fixed in order:
1. First draft of v4 proposed camera coverage and the edit's cut as two independent per-scene
   picks. Wrong — they're the same decision in real production (nobody separately decides "how
   do I shoot this" and "how will this be cut" before the edit), and asking for both only
   doubles the clicks, not the expressive range. Fixed in §12: one merged per-scene axis.
2. Second draft proposed every one of a film's 8-20 scene-slots getting full manual five-axis
   treatment. Wrong — real directors pour attention into the handful of scenes that matter and
   let routine coverage handle the rest; forcing equal-weight manual decisions on every slot is
   decision fatigue dressed up as depth. Fixed in §11: auto-fill everything from the genre's own
   archetype weights, manual override only where the film's own structure already says a scene
   matters.
3. Third mistake, caught last: even the corrected manual-override interaction was still a stats
   menu — pick an enum, read a `(for_you, for_film, risk)` delta, optimize it. That's a
   spreadsheet wearing a costume, and it's the opposite of feeling like a filmmaker. Fixed in
   §11.4: the manual interaction is narrative-first — the player reads what the moment actually
   is and chooses in filmmaker language, the mechanical delta still happens but stays backstage,
   surfaced only later in how the film is received, never as a live number during the choice.

§14 also redoes `persona.py`'s `ARCHETYPES` list critically (cutting two, adding three,
rejecting several plausible-sounding additions as redundant with fields that already exist) and
adds a second, independent role-depth axis wired into production mechanics, not just reception.

## 1. The actual problem, restated

"Building the film" needs to feel like actually constructing scenes — not tuning four
abstract sliders (`With/Beneath/Beyond/Against`) across three generic, content-free slots
(setup/turn/resolution) that are identical whether the film is a heist or a divorce drama.
The fix isn't "write 40 setpieces per genre" — that's a wall of content that only ever covers
what got hand-written, doesn't generalize to a genre nobody's authored yet, and treats
dialogue-driven or non-adversarial genres (drama, romance, family, musical) as afterthought
reskins of action's chases-and-shootouts furniture.

The fix is a **grammar**: a small, fixed set of composable primitives that describe *any*
scene in *any* genre — the same way `palette.py`'s six dials already describe any *film* in
any genre. Build the scene the way you'd build a sentence: pick the pieces, and the
combination is what makes it specific. A courtroom cross-examination, a car chase, and a
wedding-day musical number are mechanically the same shape (something is happening, in a
defined setting, through a defined engine, with a defined tactic, and stakes attached) — they
read differently only because of what's in each slot, never because they need unrelated
systems.

## 2. The grammar

Every scene is built from five axes. This is the one thing every genre shares, and it's the
entire reusable pipeline: genres don't get their own mechanics, they get their own *weights
and labels* on top of one shared structure.

| Axis | What it answers | Options (fixed set, genre-agnostic) |
|---|---|---|
| **Engine** | What kind of scene is this actually running on? | `physical`, `verbal`, `psychological`, `technical`, `social`, `expressive` |
| **Setting** | What space/situation constrains it? | `confined`, `open`, `exposed` (public/no cover), `home_turf`, `away_turf` |
| **Approach** | The player's concrete tactic within that engine | `overpower`, `outmaneuver`, `endure`, `deceive`, `disarm` — five verbs that map onto every Engine (see §2.1) |
| **Stakes** | What's actually on the line, and does it grow? | `personal`, `mission`, `relationship`, `exposure` (being found out) — plus an `escalates: bool` flag |
| **Turn** | Does the scene flip on a revelation/reversal mid-way? | `none`, `reveal`, `betrayal`, `reversal_of_power` |

A scene is a tuple of `(Engine, Setting, Approach, Stakes, Turn)`. That's it — six small enums
across five axes, fully genre-agnostic. A car chase is `(physical, open, outmaneuver,
mission, none)`. A courtroom cross-exam is `(verbal, exposed, disarm, exposure, reveal)`. A
basement descent in a horror film is `(physical, confined, endure, personal,
reversal_of_power)`. A breakup dinner is `(verbal, home_turf, deceive→disarm, relationship,
betrayal)`. A wedding dance number is `(expressive, exposed, overpower, relationship, none)`.
**Nothing about the engine differs between genres — only which combinations a given genre
reaches for, and what you call the result.**

### 2.1 Why a sixth Engine — `expressive`

The first five Engines (physical/verbal/psychological/technical/social) all describe a
*contest* — someone against someone, or someone against a problem. That's the right shape
for action, thriller, horror, most of drama and comedy. It's the wrong shape for a musical
number, a training/montage sequence, a ceremony, a quiet character beat with no adversary in
the room — scenes that are about *display or feeling*, not conflict. Forcing "the number"
into `social`/`overpower` (win the crowd) is technically possible but reads as a lie about
what the scene is. `expressive` is the honest sixth option: the scene's contest, if it has
one at all, is with the performer's own nerve, technique, or vulnerability — "can I actually
pull this off in front of everyone" — not with another character. This is what makes musical,
much of family, and the quieter end of romance and period first-class instead of forced
reskins.

### 2.2 Approach reads differently per Engine, same five verbs throughout

This is what keeps the option count small instead of exploding into Engine×Approach special
cases. The five Approach verbs are the same five choices no matter the Engine — the *flavor
text* changes, the *mechanics* (which stat they read, what they trade off) stay in one small
table:

| Approach | Physical | Verbal | Psychological | Technical | Social | Expressive |
|---|---|---|---|---|---|---|
| `overpower` | Force your way through | Talk over them | Break their composure | Brute-force it | Call in your weight/status | Go bigger than the room can look away from |
| `outmaneuver` | Outrun/flank | Out-argue on their terms | Read and exploit their tell | Improvise around the obstacle | Work the room around them | Find the angle nobody else is playing |
| `endure` | Take the hit, keep going | Absorb the attack, don't break | Stay steady under pressure | Grind it out, no shortcuts | Weather the exposure | Hold the moment past where it's comfortable |
| `deceive` | Fake them out | Lie convincingly | Gaslight/misdirect | Fake competence/sabotage quietly | Play a part for the room | Perform confidence you don't have |
| `disarm` | De-escalate physically | Defuse with honesty/humor | Name what's really happening | Hand over the "solution" that isn't | Own the room's read on you | Let the moment be small and honest |

Mechanically each `(Engine, Approach)` pair reads one Attribute pairing (Craft/Instinct/
Presence for the actor; Vision/Command/Craft for the director) and produces the same
`(for_you, for_film, risk)` shape `positions.SceneRead` already produces today — this is a
**30-cell table** (6 Engines × 5 Approaches), authored once, reused by every genre and every
scene forever.

## 3. Genre is a weighting + a phrasebook, not new mechanics

This is the actual pipeline win. A genre needs exactly two small, cheap things — no new code
paths, no new content categories — and both are sized to cover **all ten existing genres from
day one**, not a pilot subset:

1. **Archetype weights** — which `(Engine, Approach, Setting)` combinations read as "on-genre"
   vs. "off-genre," reusing the exact shape `palette.py`'s `GENRE_DIAL_WEIGHTS`/
   `CANONICAL_ARCHETYPES` already have today (that table already lists all ten genres — this
   is the same-sized table, richer axes). Sketch, one dominant lean per genre:

   | Genre | Leans toward | Reads as off-genre |
   |---|---|---|
   | Action | `physical`/`outmaneuver`/`open` | `expressive`, `home_turf` |
   | Thriller | `psychological`/`technical`, `disarm`/`deceive`, `exposed` | `expressive` |
   | Horror | `physical`/`psychological`, `endure`, `confined` | `social`, `open` |
   | Drama | `verbal`/`psychological`, `disarm`/`endure`, `home_turf` | `technical` |
   | Comedy | `social`/`verbal`, `overpower`/`deceive`, `exposed` | `psychological` (played straight) |
   | Romance | `verbal`/`expressive`, `disarm`, `home_turf` | `technical` |
   | Sci-fi | `technical`/`physical`, `outmaneuver`, `away_turf` | `social` |
   | Period | `social`/`verbal`, `endure`, `exposed` (public consequence) | `technical` |
   | Musical | `expressive`, `overpower`/`outmaneuver`, `exposed` | `psychological` |
   | Family | `verbal`/`expressive`, `disarm`/`endure`, `home_turf` | `physical` |

   This is a coherence score exactly like the one `palette.coherence()` computes now — same
   math, richer input, and (per §6.4) it's a genuine extension of a table that already
   exists for all ten genres, not new ground.

2. **A phrasebook** — a lookup from `(genre, Engine, Approach, Setting)` to the label and one
   line of flavor text the player actually sees. One worked example per genre, to prove the
   grammar reaches every one honestly, not just the obviously-action-shaped ones:

   | Genre | Example tuple | Label |
   |---|---|---|
   | Action | `physical, outmaneuver, open` | "Car Chase" |
   | Thriller | `psychological, disarm, exposed` | "The Interrogation" |
   | Horror | `physical, endure, confined` | "The Basement" |
   | Drama | `verbal, disarm, home_turf` | "The Blow-Up Dinner" |
   | Comedy | `social, deceive, exposed` | "The Wedding Toast Gone Wrong" |
   | Romance | `expressive, disarm, home_turf` | "The Quiet Confession" |
   | Sci-fi | `technical, outmaneuver, away_turf` | "The System Override" |
   | Period | `social, endure, exposed` | "The Public Reckoning" |
   | Musical | `expressive, overpower, exposed` | "The Number" |
   | Family | `verbal, endure, home_turf` | "The Scene Remembered at 40" |

   When no exact phrasebook entry exists for a given tuple, fall back to a generic but
   still-specific label built from the axes themselves ("A tense physical confrontation,
   cornered") — never a blank or a raw enum name. **Every genre is usable the moment its
   weights table exists** (all ten, from phase 2 — see §8); the phrasebook is presentation
   polish that fills in incrementally, forever, without blocking anything, genre by genre or
   even tuple by tuple.

This is the "generally applicable to all genres" property directly: the mechanical pipeline
(§2) never grows per genre, and per §3's two tables, no genre is structurally second-class —
musical and family get the same weights-table-plus-phrasebook treatment action does, not a
smaller or bolted-on version of it.

### 3.3 Eight more primary genres

`palette.py`'s existing ten genres aren't the ceiling — they're just what the current dial
system happens to already have tables for. The grammar doesn't care how many genres exist;
it costs the same two small tables (§3, items 1-2) per genre regardless of how many there
already are. Eight more, sized and shaped exactly like the original ten:

   | Genre | Leans toward | Reads as off-genre |
   |---|---|---|
   | War | `physical`/`psychological`, `endure`, `away_turf` | `expressive` |
   | Western | `physical`/`social`, `overpower`/`endure`, `open`/`exposed` | `technical` |
   | Crime / Noir | `psychological`/`social`, `deceive`/`disarm`, `exposed`/`confined` | `expressive` |
   | Fantasy | `physical`/`technical` (magic-as-technical), `outmaneuver`, `away_turf` | `social` |
   | Sports | `physical`/`expressive`, `endure`/`overpower`, `exposed` | `psychological` (played straight) |
   | Disaster / Survival | `physical`, `endure`, `open`/`away_turf` | `social` |
   | Spy / Espionage | `technical`/`psychological`, `deceive`, `away_turf`/`exposed` | `expressive` |
   | Biopic / Docudrama | `verbal`/`social`, `endure`/`disarm`, `exposed` (public life) | `technical` |

   Phrasebook seed, one worked example each, chosen the same way as §3's original ten — proof
   the tuple lands somewhere honest, not a strained reskin:

   | Genre | Example tuple | Label |
   |---|---|---|
   | War | `physical, endure, away_turf` | "Holding the Line" |
   | Western | `social, overpower, exposed` | "The Showdown" |
   | Crime / Noir | `social, disarm, exposed` | "Working the Informant" |
   | Fantasy | `technical, outmaneuver, away_turf` | "Breaking the Ward" |
   | Sports | `expressive, endure, exposed` | "The Final Play" |
   | Disaster / Survival | `physical, endure, open` | "The Evacuation" |
   | Spy / Espionage | `technical, deceive, exposed` | "The Dead Drop" |
   | Biopic / Docudrama | `verbal, disarm, exposed` | "The Confession to the Camera" |

   Eighteen genres total, all structurally identical citizens of the same two tables. Nothing
   in §2's grammar or §6's resolution changes to fit them in — see §10 for the actual
   step-by-step of adding these (or any future genre) to the live tables.

### 3.4 Secondary genres and hybrids — a film can genuinely be two genres at once

A film with only ever one genre can't express "action-comedy," "sci-fi horror," "war drama,"
"rom-com" — real, common combinations design/part-09's own genre-cycle text already assumes
exist. The grammar makes this a blend, not a new mechanic:

```
GenreProfile(
    primary: str
    secondary: str | None = None
    blend: float = 0.0   # 0.0-0.5 — how much of `secondary` folds into archetype weights.
                          # 0.0 is a pure single-genre film (today's default, unchanged).
                          # Capped at 0.5 so `secondary` never outweighs `primary` — a hybrid
                          # has a lead genre, not two co-equal ones.
)
```

- **Archetype weights** (§3.1/§3.3's tables): `effective_weights = (1 - blend) * primary_weights
  + blend * secondary_weights` — a straight linear blend, same shape `palette.py`'s existing
  per-dial weights already are, just computed once at profile-build time instead of hardcoded
  per genre. Coherence (§6.4) scores the beat sheet against this blended vector, so an
  action-horror film genuinely reads as coherent when it leans `physical`/`endure`/`confined`
  in a way neither pure genre's own archetype would fully reward alone.
- **Phrasebook resolution order**: try `(primary, tuple)` → try `(secondary, tuple)` → try a
  hand-tuned hybrid-specific entry keyed on `(primary, secondary, tuple)` for well-known pairs
  (see below) → the generic axis-built fallback (§3, item 2) that already exists for any
  ungrouped tuple. A hybrid is never less playable than a single genre — worst case it falls
  through to the same generic label every other genre already falls back to.
- **Known hybrid pairings worth hand-tuning first** — not exhaustive, not blocking (any two
  genres can blend via the formula above with zero prep), just where a hand-written phrasebook
  entry pays off fastest because the combination is common enough for players to hit it often:
  Action-Comedy, Rom-Com (Romance+Comedy), Sci-Fi Horror, Crime-Drama, War-Drama,
  Western-Horror, Fantasy-Romance, Sports-Drama.

## 4. Building the film: the beat sheet

A film is `N` ordered scene slots (`N` scales with budget tier — bigger films afford more
real scenes), each slot populated by picking the five-axis tuple, with an `emphasis` share
(0-1, sums to a per-tier total) marking which slot is the film's peak. Populating a slot
never requires new content: the player (director, or actor requesting via script-approval
leverage) picks five small enums per slot from a fixed, genre-agnostic option set — same
five axes every time, every genre, every slot — and the phrasebook (or its generic fallback)
renders it back as something that reads like a real scene.

```
BeatSheetSlot(
    engine, setting, approach, stakes, turn: <enum>   # the five axes, §2
    emphasis: float                                  # 0-1 share of the film's total weight
    performer_approach: <enum> | None                # the ACTOR's own Approach in this
                                                       # scene, independent of the director's
                                                       # Approach — see §5
)
```

## 5. Two independent Approach picks, one grammar, both careers reuse it

The same five-axis grammar serves both careers without forking into two systems:

- **Director** picks `Engine`/`Setting`/`Stakes`/`Turn` for the slot (what scene this even is)
  and their own `Approach` — how it's *directed/executed* (an `overpower` execution reads as
  coverage-heavy/forceful shooting; `outmaneuver` reads as clever blocking/oners). This
  directly subsumes `shoot_style.py`'s five styles as one Engine-agnostic Approach axis
  instead of a separate system, and it now applies identically to an `expressive` musical
  number as to a `physical` shootout.
- **Actor** (if their character is in that slot) picks their own `Approach` on the *same
  scene* — their character's tactic, independent of how it's shot. A `physical` scene shot
  `outmaneuver` (clever direction) can still be *played* `endure` (the character just takes
  the beating); an `expressive` number shot `overpower` (go bigger) can be *played* `disarm`
  (an intentionally small, honest performance against a huge staging — a real, legible
  choice). The resonance or clash between director-Approach and actor-Approach is exactly
  `positions.py`'s old Generosity/Upstaging idea, kept, just generalized from a 4-dial grid
  to this richer but still-small grammar.

One 30-cell Engine×Approach table (§2.2), read twice per slot with two different subjects
(director and actor), replaces both `shoot_style.py`'s film-wide toggle and `positions.py`'s
per-dial grid with one shared, reusable mechanism — and it's the same mechanism whether the
slot is a car chase or a first dance.

## 6. Resolution — unchanged contract with the rest of the engine

Exactly as before, and this is still the load-bearing promise: **nothing downstream of
`Palette` and `SceneRead`-shaped objects changes.**

1. **Palette**: sum each slot's genre-weighted axis contribution (§3.1) times `emphasis`,
   replacing `generate_palette`'s blind noise sample with a deterministic function of what
   was actually built.
2. **Scene reads**: each slot with a `performer_approach` becomes one `SceneRead` via the
   30-cell table (§2.2), scaled by `emphasis` — same fields (`for_you`, `for_film`, `cost`,
   `overspend`) `shape.py` already consumes.
3. **Shape**: generalize `resolve_shape` from a fixed 3-tuple to N scene reads; the
   highest-`emphasis` slot stands in for the old hardcoded `TURN` beat-weighting.
4. **Coherence**: `palette.coherence()`'s distance-to-archetype math extends to score the
   whole beat sheet's axis distribution against the genre's archetype weights (§3.1), same
   formula shape, richer input, still all ten genres — landmark-probability and
   outcome-variance stay wired exactly as they are today.
5. **Director execution deltas** (craft_contribution/chaos/critic_bonus/overage): sum across
   slots via the same 30-cell table read for the director's own Approach — a direct
   generalization of `shoot_style.resolve_shoot_style`'s single film-wide delta to
   per-slot deltas.

`resolve_shoot`, `resolve_quality`, `resolve_reception`, `standing.py`, box office — all
untouched. Only the code producing a `Palette` + `SceneRead`s from thin air is replaced.

## 7. What's kept from the current system

- **Generosity/Upstaging** — reframed as director-Approach vs. actor-Approach resonance
  (§5), same payoff shape, no longer a bolt-on modifier — now structurally part of every
  scene that has a performer in it, in every genre.
- **Contrast budget** (craft + director command) — still gates how much `emphasis` a
  player can safely put on a single slot before `overspend_penalty` bites; same formula.
- **`palette.coherence()`/landmark math** — extended, not replaced (§6.4).

What's cut: the four position labels as *the* vocabulary, the fixed three-generic-scene
structure, blind noise-sampled palettes, and `shoot_style.py`/`development.py`'s
film-wide-only toggles (both become per-slot instances of the same grammar instead of
separate systems).

## 8. Build phases

1. **Grammar core** — `engine/creative/grammar.py`: the five axis enums (six Engines), the
   30-cell Engine×Approach table (§2.2) with its `(for_you, for_film, risk)` outputs, pure
   and genre-agnostic. Fully testable with zero genre content.
2. **Genre weighting, original ten at once** — extend `palette.py`'s `GENRE_DIAL_WEIGHTS`/
   `CANONICAL_ARCHETYPES` shape to the five axes (§3.1) for **all ten of `palette.py`'s
   existing genres in one pass** — this is the cheap, mechanical part (it's numbers, not
   prose), and doing all ten together is what makes the system actually genre-complete from
   the start rather than pilot-then-backfill.
3. **Phrasebook, one worked entry per genre plus fallback** — `engine/creative/
   phrasebook.py`: seed with the ten entries in §3's table (one per genre, chosen to prove
   the grammar reaches non-adversarial genres honestly, not just action) plus the
   generic axis-built fallback for every unlisted tuple. Expandable indefinitely, per genre,
   without ever touching mechanics or blocking a genre from being playable.
4. **BeatSheet + resolution** — `engine/creative/beatsheet.py` implementing §4 and §6:
   slot assembly, emphasis-budget validation by tier, Palette/SceneRead generation.
   Generalize `shape.resolve_shape` to N slots.
5. **Actor flow** — replace `career.simulate_project`'s `scene_choices` tuple with a
   BeatSheet + the player's per-slot `performer_approach` picks.
6. **Director flow** — wire BeatSheet assembly into `development.py`/`casting.py` in place
   of `rewrite`/global shoot style; `edit.py` unchanged, downstream as before.
7. **UI** — `session.py`/`cli.py`: five-dropdown scene builder + phrasebook-rendered label
   preview, emphasis allocator, `bands.py`-style words-not-numbers everywhere a raw float
   would otherwise leak through.
8. **Tuning pass** — same methodology as `simulation/verify.py`: confirm the beat-sheet path
   reproduces roughly the same reception correlations §14 already verified, across **all ten
   original genres**, before calling this done.
9. **Eight new genres + hybrid blending** — add War/Western/Crime-Noir/Fantasy/Sports/
   Disaster/Spy/Biopic (§3.3) using the playbook (§10), and implement `GenreProfile`'s
   primary/secondary blend (§3.4) plus its phrasebook resolution order. Seed the
   known-hybrid-pairings list (§3.4) with hand-tuned entries once the blend math itself is
   verified against the original ten.
10. **Phrasebook depth pass** — go back through every genre and hybrid and hand-polish the
    highest-traffic tuples (the ones players actually pick most, read from playtesting/
    telemetry) past the generic fallback — ongoing content work, never blocking, never
    mechanical.
11. **Retire the old path** — delete `generate_palette`'s noise sampling, the 4-position
    grid, and `shoot_style.py`'s film-wide-only toggle once the grammar covers everything
    they did, for every genre and hybrid.

## 9. Open questions before implementation starts

- **Slot count vs. budget tier** — needs a real curve; likely also genre-sensitive (a
  musical's number-driven structure may want fewer, higher-emphasis slots than an action
  film's more evenly-distributed setpiece run — worth checking against real data before
  assuming one curve fits all ten genres).
- **NPC-director default policy** — how an off-screen/world-sim film (§10.0) picks its own
  five-axis tuples per slot without a human; likely: sample from the genre's archetype
  weights directly, which the grammar makes trivial (it's already a weighted distribution),
  and this works identically for all ten genres with no special-casing.
- **Script-approval veto scope** — one axis on one slot, or a full slot's worth?
- **Emphasis-budget curve** — flat per film, or scales with slot count/tier independently?
- **Does `expressive` need its own resolution term downstream**, or does it fully launder
  through the existing `craft_contribution`/`for_film` numbers the other five Engines use?
  Recommend: no new term for v1 — prove the six-Engine table works through the existing
  pipeline before considering a musical-specific box-office/critic term (§9.7's already-real
  distinct animation/merch economy is the closer analogy if one turns out to be needed).
- **Turn axis timing** — does a `reveal`/`betrayal`/`reversal_of_power` need to resolve at a
  specific point in the slot (must it land last), or is it just another coherence-scored tag?
  Recommend: just a tag for v1, add timing semantics only if playtesting shows it's needed.
- **Hybrid blend curve** — is a flat 0-0.5 `blend` scalar (§3.4) expressive enough, or do some
  genre pairs need an asymmetric curve (e.g. a "horror-tinged thriller" reading very
  differently from a "thriller-tinged horror" at the same nominal blend value)? Recommend:
  ship the flat scalar first — asymmetry can be checked for empirically in phase 9 tuning by
  comparing a pair blended both ways, and only gets its own curve if the difference actually
  shows up in reception correlations.

Recommend resolving all of these empirically during phases 8-9, same as the rest of this
design's own convention — build placeholder numbers first, tune against real simulated
careers, don't decide analytically up front.

## 10. The genre extensibility playbook

The actual answer to "how do we add more genres": every genre, forever, past this plan's
initial eighteen, follows the same seven steps. None of them touch the grammar (§2) or the
resolution pipeline (§6) — a new genre is purely two small tables and a validation check.

1. **Name it and find its lean.** Pick 2-3 dominant `(Engine, Approach, Setting)` tendencies
   and 1-2 combinations that would read as obviously off-genre if a film leaned on them
   instead. This is a design call, not a numeric one — write it as a sentence first (§3.1/
   §3.3's "Leans toward"/"Reads as off-genre" columns) before it becomes a table row.
2. **Write the archetype-weights row.** Same numeric shape as every existing row in §3.1/
   §3.3 — small, fixed-size, no new fields. This is the only thing that makes a genre
   mechanically live.
3. **Check it's actually a new genre, not a hybrid in disguise.** Run the new archetype
   vector's distance against every existing genre's vector, the same
   `distance_to_nearest_archetype` math `palette.coherence()` already uses today. If it lands
   suspiciously close to an existing genre, it's very likely a secondary/hybrid variant of
   that genre (§3.4) — express it as a `GenreProfile(primary=existing, secondary=new_idea,
   blend=...)` instead of a thin, redundant thirteenth (or twenty-fifth) primary-genre row.
   This check is what keeps the genre list from silently bloating with near-duplicates.
4. **Write one worked phrasebook entry.** Prove the grammar reaches the genre honestly (§3,
   item 2) — pick the tuple that most clearly is that genre, not a strained edge case.
   Everything else falls back to the generic axis-built label (§3, item 2) until someone
   chooses to hand-polish it; that's fine, it's never blocking.
5. **If it's likely to pair often, seed 2-4 hybrid candidates.** Same as §3.4's known-pairings
   list — name the genres this one commonly blends with in real film culture and a rough
   starting `blend` (0.2-0.4 is typical), so the first hand-tuned phrasebook entries for that
   hybrid have somewhere to go. Not required — the blend formula (§3.4) works with zero prep
   for any pair — just cheap to seed while the genre's design is already fresh.
6. **Run the phase-8/9 tuning pass on it.** Simulate careers/films using the new genre (and
   its seeded hybrids) through `simulation/verify.py`'s existing methodology; confirm
   reception correlations land in a plausible range, the same bar every genre already in the
   engine has cleared, before it ships live.
7. **Ship.** A genre is playable the moment step 2's table exists — steps 4-5's phrasebook
   entries are incremental content, never a blocker, exactly as §3 already establishes for the
   original eighteen.

This is the whole answer to "make a plan to add them": adding genre nineteen, or forty, costs
the same seven steps as genre eleven did here. Nothing about the pipeline gets more expensive
or more special-cased as the roster grows.

---

## v4 — making a film feel like making a film

The sections above (§1-§10) are unchanged: the five-axis grammar, the eighteen-genre roster, the
extensibility playbook. Everything below is new, additive, and answers a question the sections
above never asked: once a player is looking at a BeatSheet of 8-20 scene-slots, what do they
actually *do*, moment to moment, and does it feel like directing a movie or like filling out a
form? §11 is the interaction model. §12 folds camera and cut into one axis instead of two. §13
covers the two remaining film-wide creative identities plus the needle-drop token. §14 redoes
`persona.py`'s role-archetype list critically and adds a role-depth axis wired into production,
not just reception. §15 is the revised build order.

## 11. Auto-fill, manual override, and a narrative-first interaction

### 11.1 The principle: manual depth scales with stakes, not with scene count

A film's BeatSheet has 8-20 slots (§4, scaled by budget tier). Asking a player to hand-pick all
five axes for every single one is decision fatigue, not immersion — and it's actually *less*
realistic to the craft than the alternative, because real directors don't spend equal creative
energy on every scene. They pour it into the handful that matter and trust competent routine
coverage for the rest.

So: **the instant a BeatSheet is generated, every slot is auto-filled**, sampled from the genre's
(or, for a hybrid, the blended §3.4) archetype weights — the same distribution
§9's "NPC-director default policy" open question already proposed using for a no-human background
film, now reused for the player's own routine scenes too. A player can accept the whole auto-built
film and move straight to shooting it — that's a complete, valid way to play, the same way
accepting the offer board's default terms already is elsewhere in this engine.

**Manual override is then offered, never forced, at exactly the moments the film's own structure
already flags as load-bearing:**
- Every slot whose `emphasis` clears a threshold (the film's own designated peaks — §4 already
  has this field, it's just unused for this purpose today).
- Any slot that is a showcase-depth role's (§14.2) main scene — the character's one real chance
  to matter, and the actor should get to say how it's played (§5's existing "two independent
  Approach picks" already supports this, it just needs a trigger).

That's realistically 2-4 scenes a player actually sits down and builds by hand per film. Everything
else is the auto-fill, silently doing competent, on-genre work exactly the way a good crew would.

### 11.2 Why this isn't just "fewer choices" — it's *targeted* choices

This is the same shape §9.1 (design/part-09) already uses for horror as an actor's on-ramp: not
every decision in this game is meant to carry equal weight, and pretending otherwise dilutes the
ones that should. A player who wants a light, mostly-auto-piloted film can have one. A player who
wants to hand-direct their Oscar showcase scene gets a real, rich interaction there instead of the
same interaction spread thin across fifteen scenes nobody will remember.

### 11.3 What auto-fill actually removes: two false axes from the earlier draft

Two drafts of this pass got corrected before reaching this doc (see the changelog note at the top
of this file) — both were attempts to add *more* per-scene mechanical surface, and both were wrong
for the same reason: more independent per-scene picks was mistaken for more depth.
- **Camera coverage and the edit's cut were briefly proposed as two separate per-scene axes.**
  Folded into one — §12.
- **Every scene was briefly proposed to get full manual treatment.** Replaced by §11.1's
  auto-fill/override split above.

### 11.4 The manual interaction itself is narrative-first, not a stats menu

This is the actual correction that matters most, and it changes what "manual override" means
concretely. It is **not**: an enum picker showing `Approach: outmaneuver (+4 for_film, +2 risk)`.
That's the grammar's own internal representation leaking into the UI raw, and reading it live
while making the choice turns creative direction into expected-value optimization — the opposite
of the goal.

Instead, when a slot is opened for manual override, the player is shown:
- **What the moment is**, in plain filmmaker language, built from the phrasebook (§3, item 2) the
  same way an auto-filled scene would already render — genre, setting, who's in it, what's at
  stake. ("The two of you are alone in the greenhouse. She just found out. This is the scene
  where it either breaks her or she holds.")
- **A small number of real, described options**, phrased as directing choices, not axis labels —
  each one *is* a real `(Engine, Approach, Setting, Stakes, Turn)` tuple or a coverage-style pick
  underneath, but the player reads "Let her hold it together, filmed close, and make the audience
  wait" — not "psychological / endure / confined."
- **No visible number.** The mechanical delta (§6's existing resolution math — craft_contribution,
  a nudge to critic/audience score) still computes and still matters, but it stays backstage. The
  player finds out how it landed the way a real director does: in the dailies, in the cut, in the
  reviews — never as a live readout while they're making the call.

**This means the phrasebook (§3, item 2; §3.3's eighteen worked entries) stops being "presentation
polish, fills in incrementally, never blocking" and becomes load-bearing infrastructure for v4.**
§3/§3.3 already say a missing phrasebook entry falls back to a generic axis-built label
("A tense physical confrontation, cornered") — that fallback is fine for an auto-filled scene a
player never opens, but a manual-override scene is exactly a phrasebook cache-miss made visible to
the player, so **phrasebook depth for the tuples most likely to appear at emphasis peaks is now a
phase-2/3 priority, not indefinitely-deferred content work** (§15 reorders this from the original
§8 build phases).

### 11.5 Contract with the rest of the engine: unchanged

§6's resolution pipeline is untouched by any of this — auto-fill and manual override both produce
the exact same BeatSheet-of-tuples shape §4 already specifies; §11 only changes *how a tuple gets
chosen* for a given slot (sampled vs. hand-picked through a narrative interface), never what a
tuple *is* or how it resolves.

## 12. Coverage style — camera and cut, one merged axis

An earlier draft of this pass proposed camera coverage and the edit's cut-into-next-scene as two
independent per-scene picks. Wrong: in real production these aren't two decisions, they're one —
nobody separately plans "how do I shoot this" and "how will this be cut" before the edit even
starts; the coverage choice mostly *determines* the cut (a oner doesn't get chopped up afterward;
heavy coverage all but demands a busier edit). Asking for both doubled the clicks without
doubling the real expressive range — the illusion of depth, not depth.

**One per-scene axis instead:** `Coverage` — `heavy_coverage` (safe, many options in the edit,
costs some Craft, §7's existing shoot-style numbers are the starting point for the deltas),
`long_takes` (a oner — high Craft ceiling, real risk, no safety net if a performance in it goes
wrong), `many_takes` (grinds toward the best version, pays off only past a Craft threshold, same
shape as `director/shoot_style.py`'s existing `MANY_TAKES` logic), `lean_and_fast` (cheap, fast,
a real schedule/quality trade). This is a **direct generalization of `director/shoot_style.py`'s
existing five film-wide styles down to per-scene granularity** — not a new system bolted on next
to it; §15 retires the film-wide-only version the same way §7/§8 (original) already planned to
retire the 4-position grid.

Surfaced only on manually-opened slots (§11.1), and per §11.4, presented narratively — "shoot it
in one unbroken take, no safety net" — not as a labeled enum with a number attached.

## 13. Film-wide identities and the needle drop

Two real creative decisions genuinely are film-wide, because that's how those departments
actually work — nobody rehires their DP or their composer mid-shoot (confirmed against real
production process: the director and DP set the visual language together before the shoot; the
director and composer set the film's sound identity as its own dedicated pass, distinct from
picture editing). These stay single, one-time, low-frequency, high-weight picks — not diluted
into the per-scene loop.

- **Visual signature** (once per film): `naturalistic`, `stylized`, `high_contrast`,
  `handheld_intimate`, `classical_composed`. Genre-weighted the same shape as §3.1/§3.3 — horror
  leans `high_contrast`/`handheld_intimate`, musical leans `stylized`/`classical_composed`.
- **Score genre** (once per film): a single, plain, conventional pick — `orchestral`, `pop`,
  `electronic`, `country`, `rock`, `hip_hop`. This replaces v4's first draft (`orchestral_
  traditional`/`electronic_modern`/`source_music_driven`/`minimal_sparse`/`hybrid_experimental`)
  — that list was abstract descriptors nobody actually talks about a film's music in; real,
  nameable genres are the "conventional and simplistic" film-wide pick this section wants, and
  they're what actually determines who you'd plausibly hire (§13.1). Same genre-weight shape as
  §3.1/§3.3 — western leans `country`/`orchestral`, musical leans `pop`/`orchestral`, horror leans
  `electronic`. This is genuinely the whole film-wide decision: simple, one pick, done. Who
  delivers on it is a separate question — §13.1.

### 13.1 Hiring the composer

A visual-signature pick is a director's own aesthetic call — no one to negotiate with. A score
genre is different in real production: picking "country" doesn't write the score, hiring a
country composer does, and that's a real casting-shaped decision. This reuses three patterns
already built elsewhere in this engine rather than inventing a fourth: `director/casting.py`'s
tiered choice-of-candidate shape, `actor/offers.py`'s `negotiated_fee_share` fee-negotiation
math, and `simulation/session.py`'s Rolodex-style NPC tracking (`director_npc_id`/
`_director_tag`) for a recurring collaborator you can work with again.

A composer candidate carries exactly three things, deliberately no more:
- **Skill** — one scalar, 0-100, same shape as `DirectorAttributes.craft`. Read straight into the
  score's mechanical delta (§13's palette-effect folding) as a multiplier — a skilled composer
  gets more out of whatever genre you hired them for; an unskilled one gets less, or even inverts
  a critic bonus into a penalty, the same way `director/shoot_style.py`'s `MANY_TAKES` already
  flips sign below a Craft threshold.
- **Background** — a real, nameable *combination*, not a single tag off the film's own genre list:
  a scene/stature half (`indie`, `mainstream`, `superstar`, `legacy`) crossed with a style half
  (the same six genres §13 just picked from). "Indie Pop," "Superstar Country," "Legacy
  Orchestral," "Mainstream Electronic" — a composer is a real person with both a scene they came
  up in and a style they play, and those mix and match independently (an indie composer can play
  orchestral; a superstar can work in electronic) rather than being one flat descriptor. 4 scenes
  × 6 styles = 24 real, distinct backgrounds from two small lists, the same combinatorial trick
  §2.2's Engine×Approach table already uses to get real variety out of small fixed pieces instead
  of a long hand-authored enum.
- **Fit** — not stored, computed off style alone: does the composer's style half match the
  film's §13 score genre? — the same `distance_to_nearest_archetype` shape `palette.coherence()`
  already uses. This is the only thing that touches the creative delta. Scene/stature is
  deliberately **not** a fit input — it shows up next to Fit purely as information (who this
  person is, what tier they're known at) so the player can read the hire before committing, but
  mechanically it does exactly one thing, below. A mismatched style is a real creative problem; a
  mismatched scene tier is not a separate problem to model, it's just a price tag.

**Salary demands** — the composer's *only* other mechanical lever. Scales with the scene half
(a superstar costs dramatically more than an indie composer, regardless of style match — the
same star-power-drives-cost logic `actor/offers.py` already applies to cast) and with Skill, run
through the exact same `negotiated_fee_share`-shaped formula `actor/offers.py` already has for an
actor's own fee — no new negotiation mechanic, the existing one applied to a new role — with a
Rolodex relationship-tier discount (`Loyal/Ally/Familiar/Stranger/Rival`, same scale
`director/development.py`'s attachments already use) for a composer you've worked with before. No
separate buzz/marketing bonus on top of this: one cost dial, cleanly separated from the one
creative-fit dial, is the whole point of splitting Background into two halves — giving stature a
second payoff on top of salary would just be double-counting the same signal.

**Once Skill, style Fit, and Salary are resolved, that's the whole composer mechanic —
deliberately.** No separate "composer relationship" arc, no per-scene composer involvement, no
second axis. The hire is one decision, made once, folding into the same modest, backstage-
magnitude `palette_aud_effect`/`palette_crit_effect` delta §13 already produces — in keeping with
§11.4/§13's "underlying, minor effect" principle, not a system that grows a second game inside
itself.

**Needle drops — a scarce token, not a menu.** design/part-09 §9.7 already states "a hit song
raises AudienceScore for the whole film" with no mechanism behind it; this closes that gap. A
film gets 1-2 needle-drop tokens (scaling with budget tier and whether `score_genre in
(pop, hip_hop, rock, country)` — the genres a real needle-drop moment plausibly comes from), and
the player spends one by dragging it onto a scene — a single, weighty,
binary call ("spend it here, or save it"), never a dropdown of song genres to optimize. Both
identities and the token are presented the same narrative-first way as §11.4: "you have one needle
drop left — is this the moment?"

Both identities' mechanical effect folds into `palette_aud_effect`/`palette_crit_effect` the same
additive way `hybrid`/`franchise`/`adaptation`/`rating_outcome` bonuses already stack in
`simulation/career.resolve_quality` — each a small, optional, default-off term; magnitudes stay
modest by design (§11.4's "underlying, minor effect" principle applies here too, not just to
per-scene choices) so none of this becomes a min-maxing target that crowds out the narrative
framing.

## 14. Roles, redone — a critical pass, not an addition

`actor/persona.py`'s `ARCHETYPES` (nine entries: `leading_hero, romantic_lead, villain, everyman,
character_actor, ingenue, authority, comic_relief, wildcard`) is redone here critically — cutting
what doesn't belong, adding only what's genuinely missing, and explicitly rejecting several
plausible-sounding additions as redundant with fields the engine already has, so the list doesn't
bloat.

### 14.1 The archetype list

**Cut, with reasons:**
- `character_actor` — a category error. It's not a story function a role has; it's a reputation
  an actor *earns* over a career for range across many archetypes. Keeping it as a castable
  archetype means it can never actually be earned through play, just statically assigned. Replace
  with an emergent read: low `Persona.Legibility` (already tracked) spread across many archetypes
  in the filmography *is* being a character actor — no new field.
- `wildcard` — an undefined grab-bag. Replaced by a properly-defined `ensemble` (below), which has
  an actual meaning instead of "none of the above."

**Kept as-is:** `leading_hero, romantic_lead, villain, everyman, ingenue, authority, comic_relief`
— seven real, distinct, non-overlapping story functions.

**Added, with reasons:**
- `mentor` — a real, distinct function with its own franchise behavior worth modeling: mentors
  are written out or killed off across a franchise's sequels at a markedly higher rate than any
  other archetype (§14.3).
- `narrator` — the framing-device/retrospective voice (noir, period, drama), mechanically distinct
  because it interacts with the story from outside the plot rather than inside it.
- `ensemble` — the honest replacement for `wildcard`: a defined bucket for genuine multi-hander
  films (disaster, war, family — genres already in the §3.3 roster) where no single archetype
  fits, instead of a meaningless catch-all.

**Rejected candidates, and why** (kept here so nobody re-proposes them without re-deriving the
same conclusion — same spirit as §10's playbook step 3 for genres):
- *Deuteragonist / second lead* — redundant with `leading_hero` + `billing=supporting`; billing
  already answers "how prominent."
- *Henchman / villain's second* — redundant with `villain` + `billing=supporting`, same reasoning.
- *Tragic figure* — not a function, a quality of how the story treats a character. That's exactly
  what §14.2's depth axis is for; any archetype can be tragic.
- *Breakout scene-stealer* — not something cast, an outcome. Already handled after the fact by the
  existing spin-off mechanic (design/part-09 §9.5).
- *Foil* — a relationship between two characters, not a property of one role; better served by
  existing relationship/chemistry mechanics than a new archetype label.

**Result: ten archetypes** — `leading_hero, romantic_lead, villain, everyman, ingenue, authority,
comic_relief, mentor, narrator, ensemble` — a net addition of one over the original nine, with
every entry earning its place instead of padding the list.

### 14.2 Role depth — a second, independent axis

Archetype alone answers "what kind of role" but never "how good a role" — two leads in the same
genre can be a career-making showcase or a paycheck part, and nothing today distinguishes them.
New, independent axis: `underwritten → standard → rich → showcase`. Independent of both archetype
(a mentor can be underwritten or a showcase) and billing (a supporting role can be a showcase, a
lead can be underwritten).

### 14.3 Depth and archetype wired into production, not just reception

The actual point of this section, per the "more input over how the film is actually made"
direction: role should touch the *making* of the film, not just its final score.

- **Casting** (`actor/casting`/`director/casting.py`): showcase and mentor/narrator roles raise
  effective competition/`type_strictness`; the existing "difficult genius" casting path reads as a
  better fit for villain/showcase roles than for ingenue roles.
- **Development hell** (`director/development.py`): today only a billed lead can really anchor a
  project's momentum via its `Attachment` types. A showcase-depth supporting role should be able
  to anchor on its own — a new `prestige` attachment type, distinct from `bankable`/`genre_fit`/
  `studio_favorite`.
- **Awards**: depth sets the actual per-role award ceiling, as a second gate alongside (not
  replacing) design/part-09 §9.1's existing genre-level award-ceiling column — a showcase role in
  a low-ceiling genre is still a real nomination shot; an underwritten role in a high-ceiling
  genre still isn't.
- **Franchise mechanics** (`simulation/_franchises.py`): archetype drives sequel behavior —
  `leading_hero` anchors, `mentor` has an elevated departure/death rate, `ensemble`/`narrator`
  rarely anchor a franchise alone.
- **Merchandising** (`leverage/merchandising.py`): toyability reads off archetype (`villain`/
  `leading_hero` high, `mentor`/`narrator` low) as a real input alongside the existing
  animation-gated multiplier, not a genre-only signal.

Each of these is one optional, default-off parameter threaded into an existing function, the same
proven contract `is_hybrid`/`is_animation`/`director_spectacle_bonus` already use elsewhere in this
codebase — no existing caller or test changes behavior by default.

## 15. Revised build phases (supersedes §8's ordering for the parts §11-§14 touch)

§8's original eleven phases still apply for the grammar/genre core (phases 1-3, 8-9, 11
unchanged). Phases 4-7 and 10 are reordered/amended:

4. **BeatSheet + auto-fill** (§4, §11.1): slot assembly, emphasis-budget validation by tier, AND
   the genre-weighted auto-fill sampler from day one — not added later. A BeatSheet that can only
   be hand-built isn't shippable under this plan; auto-fill is core, not polish.
5. **Phrasebook depth for likely-manual tuples** (§11.4): pulled forward from "incremental content,
   never blocking" (original §8 phase 3/10) to a real phase — the emphasis-peak and showcase-role
   tuples most likely to actually reach a player need real prose before manual override ships,
   since the fallback generic label is acceptable for auto-fill but not for the interaction §11.4
   describes.
6. **Coverage style** (§12): generalize `director/shoot_style.py` to per-scene, reusing its
   existing five-style deltas as the starting numbers.
7. **Roles** (§14): archetype list migration (nine to ten, with the emergent character-actor read
   replacing the static field) + depth axis + the five production wiring points in §14.3.
8. **Film-wide identities + composer hire + needle drop** (§13, §13.1).
9. **Actor/director flow + UI**: session.py/cli.py's beat-sheet builder, narrative-first per
   §11.4 — not a five-dropdown enum picker (this corrects original §8 phase 7's own description,
   written before §11.4's correction).
10. **Tuning pass**, same methodology as original §8 phase 8, extended to cover auto-fill
    distributions matching genre archetype weights and confirming manual-override magnitudes stay
    "minor, underlying" per §11.4/§13's own stated principle — not just reception correlations.
11. **Retire the old paths**: `generate_palette`'s noise sampling, the 4-position grid, and
    `shoot_style.py`'s film-wide-only toggle (superseded by §12) — unchanged from original §8
    phase 11.
