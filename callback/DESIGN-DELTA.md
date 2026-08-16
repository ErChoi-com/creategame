# CALLBACK — what changed between the document and the game

`docs/callback-design-doc-v8.md` is the design. `docs/callback-design-review.md` is the
adversarial read that found the design, run end to end, does not produce a career: not one of
the seven targets in §14.9 was met, 80% of simulated careers never played a lead, and nobody
became a star in four thousand attempts.

This directory is the implementation, and it works. Below is every place it departs from the
document, why, and which check holds it in place.

Run the checks:

```bash
node callback/sim/career-sim.mjs 3000     # §14.9 whole-career targets — 7/7
node callback/sim/subsystems.mjs          # §14.1, §5.3-5.6, §9.3 — 16/16
node callback/sim/agency.mjs              # the design rules in Part 0 — 4/4
node callback/sim/replay-test.mjs         # saves rebuild the same career — 25/25
```

---

## The review's ordered fix list (§10), and what was done

### 1. Fix the ladder — *"nothing else matters until a career can happen"*

The document's Standing gains were billing-weighted and its decay was not, so a beginner
accrued at one fifth the rate while paying full price. Four separate changes, all in
`engine/model.js`:

| | Document | Here |
|---|---|---|
| **FIX-1** | `ΔHeat = bw × (9·clamp(ROI−1) + 0.16·(AUD−55))`, flat `−9/yr` decay | Gains carry a base term (`K.heatBase`, working at all is worth something), are re-centred below the median outcome (`ROI−0.90`, `AUD−52`), and decay is **proportional** so the meter finds an equilibrium instead of integrating to zero |
| **FIX-1b** | decay identical at every tier | Decay is **billing-aware** (`heatKeepBit/Supporting/Lead`). The tier you can reach has to be able to outrun the decay on that tier, or there is no bottom rung |
| **FIX-1c** | — | **Discovery multiplier**: your first nine credits count for up to 2.4×. A new face is news; a known quantity is not |
| **FIX-1d** | — | **Recognition**, the bridge out of bit parts that is deliberately *not* Standing. Good notices in a small part are remembered by casting directors and enter Utility for supporting and bit roles only — a way in, not a way up |
| **FIX-1e** | — | **Reach**: Heat gains scale with the film's budget. A hit on a $4M film and a hit on a $140M film are the same ROI and nothing like the same career event. This is where the game's upper tail comes from, and why it is rare |

### 2. Define one Notices and one Ensemble

Part 4 and Part 5 defined both quantities differently and never reconciled them; the two
"verified" subsystems were verified in isolation and were mutually inconsistent.

There is now exactly one of each. `model.resolvePositions()` and `model.shapePerformance()`
produce `notices` and `ensembleValue` from the Part 5 position/shape system, and those values
are the terms `§4.10`'s `reception()` consumes — `yourNotices` inside the Notices equation,
`ensembleValue` inside the billing-weighted `EnsembleScore` that feeds `ProjectQuality`. Part 5
cannot drift from Part 4 again because there is only one code path.

The reception sweep was then re-run (`sim/subsystems.mjs reception`), which is what §14.1 asked
for and never got.

### 3. Define Standing-the-scalar

Parts 6 and 8 gate the entire leverage layer on "Standing 65 / 70 / 75 / 85", a quantity the
document never defines and the schema has no field for. `model.standing()` defines it once —
StarPower net of scandal — and every threshold in the game reads that function.

### 4. Write the first hour

The largest gap: 2,659 lines with no character creation, no starting conditions, no onboarding,
no interface, and not one line of the game's prose.

- **Four openings** (`career.js` `BACKGROUNDS`) that differ in what they are short of, not in
  how good they are: Conservatory, Discovered, Regional stage, Family money.
- **The union catch-22 is passable.** §10.1 locks you out of union productions until you have
  three union credits and never says how you get the first three. Non-union listings now appear
  on the board of anyone under three credits: they pay a third as much and are easier to get.
- **A playable interface** (`web/`): the offer board, prep, the film's palette, your four
  positions against it with a visible contrast budget, the three on-set moments, a reception
  card that always attributes the result, the year's decay, and the obituary.
- **Prose in the game's register** throughout, including the qualitative read after every shoot
  — you never see your Performance number, only what the room did.

---

## Other structural faults from review §6, fixed

- **FIX-6 — one of three casting paths was unreachable.** `Utility − difficulty > 25` cannot be
  met without relationships, which makes path 2 and path 3 the same path. The offer threshold is
  now 14 over the role's own difficulty, so a star who is obvious casting for a small film gets
  offered it outright, and the Rolodex path stays distinct (`castingPath()`).
- **The 0.80 ensemble share.** Asserted in the doc and wrong for a real cast. Your share now
  depends on billing: a lead carries most of the ensemble (~0.56), a bit player is one voice in
  a room (~0.09). §14.1's signature correlations are consequently checked on the **lead subset**,
  which is the population the doc was describing.
- **Presence's verb never fired.** `NoticesFloor = 0.10 × Presence` could never bind against a
  Notices mean of 58. It is `0.42 × Presence` here, and it binds — a magnetic actor can afford
  to be still.
- **The average NPC director was worse than the blind roll.** §7.7's formula yields 49.4 at the
  stated population mean against a `N(52,14)` model. `world.postSkill()` is re-centred on 52.
- **FIX-7 — narrative beat merit ~2:1 in awards.** Campaign narratives are halved and capped at
  ±12, so a fiction tilts a close race instead of deciding an open one.
- **The overpricing term priced working actors off the board.** `−12 × (Quote/budget − 1)`
  uncapped ends careers the moment a quote moves; capped at 12, because an actor who wants a
  part takes less for it.
- **Two box office models.** §8.2's shape with §4.10's rights share, once, in `reception()`.
- **Palette effects swamped everything.** At the doc's stated weights the palette moves audience
  and critic scores by up to ±20 against a base sd of 7.6, and critics and crowds decorrelate
  completely. `K.paletteScale` holds them to the ±7–10 the doc says it intends.

---

## What was added after the model worked

The corrections above make a career happen. These make it a game you can sit
down and play, and each one came with a check that holds it.

### The pull layer (Part 6), and the audit that keeps it free

Some thirty verbs — get work you were not offered, change the project you are
on, change your own standing, change other people, change the market, change
the rules — none of them ever prompted. Favours are tokens attached to named
people; scarcity accrues while you are away; indispensability builds by doing
the same property again and pays in money and approvals; positions (guild
office, a jury seat, a production company, teaching, a board seat) grant levers
rather than obligations.

`sim/agency.mjs` holds the three claims that licence the breadth, and it found
real faults in all three:

| Claim | What it caught |
|---|---|
| A career that never opens the menu still meets §14.9 | — held from the start |
| No playstyle dominates the six Ambitions | The Author won all six until producing carried real risk; the producer share was dead code and the stake was never paid |
| Year 45 pushes no more prompts than year 15 | Prompts grew 7 → 11. Prep and stance asked about things a veteran has answered a hundred times, and the season interrupted when there was nothing to decide |

### Saves, as a journal

Every mutating call goes through `Game.call()` and lands in a list. The engine
is deterministic from its seed, so that list *is* the save file. Verified two
ways: `sim/replay-test.mjs` rebuilds 25 careers and compares fingerprints, and
`sim/save-test.mjs` reloads a real browser mid-career and checks the recorded
history survives. This is what caught the trades panel consuming the game's
randomness outside the journal — a bug no amount of reading the code would
have surfaced.

### Content, and the faults reading it exposed

Ten on-set moments drawn by what the production actually is, eight life events
fired by what is true about you, headlines drawn per outcome shape, eight ways
to be turned down, milestones for the turns a career has, and a trade paper
once a year so the world is legible as something moving on its own.

`sim/transcript.mjs` prints a whole career as prose. Reading one is how the
following were found, none of which the aggregate numbers showed:

- The lifestyle ratchet charged the annual floor on every payment *and* again
  at year end: a career could finish $865M in debt on $583M of earnings.
- Careers never faded, because offer counts were rounded — a rate of 1.2 a
  quarter meant exactly one offer, forever.
- The bit-to-supporting bridge was centred at 51 Notices against a population
  averaging 49, so ordinary good work never accumulated any. Recognition now
  fades as your own standing rises, which is what it was always for.
- Two films in one career could share a title, so the log read as though a
  picture was reviewed before it was cast.
- A life event could strand you in an open-ended hiatus with no way out.
- One scandal could be defended repeatedly, farming favours from a single story.

---

## What the genre's own literature changed

Three things came out of reading how comparable systems are built, and each
one found a fault:

**Storylets have named shapes, and one-shot events cannot express them.** The
quality-based narrative tradition (Failbetter's storylets, and the pattern
catalogue that grew from them) names the chain, the clock, the hourglass and
the gravity well. §11.2's "addiction as an arc, not a flag" is precisely a
clock driving a chain: a hidden level rises from how you are living, a
different scene plays each time it crosses a threshold, and the ending differs
by where you got off. `engine/arcs.js` implements that shape and uses it for
the drinking, a rival, and the body — including the gravity well, so a finished
arc leaves a mark rather than going quiet.

**Hidden ability needs a separately-modelled estimate of it.** Football
Manager's judging attributes and Total Extreme Wrestling's scouting levels —
which rise only while a worker is actually doing the thing being judged — both
separate the truth from the player's read of it. CALLBACK already hid
Performance; it did not model your ability to read the room, which was a flat
noise term. It now narrows with Craft and with having worked with that
director before, and the game tells you how much to trust the read.

**Hand-written playstyles cannot find the edges.** The automated-playtesting
literature bounds a design with agents rather than personas. Three were added,
and two of the five agency rules failed immediately:

- A random agent collapsed to two active years. The diagnosis needed a third
  agent — one who takes whatever comes but does the work properly — to
  separate "the offer economy is broken" from "playing badly is punished". It
  was neither: quitting keyed on *not working* when it should key on *not
  being offered anything*. Missing out is not the same as not being wanted.
- The greedy agent won 85 awards per 100 careers by campaigning every year
  forever. Campaign money now only moves a performance people are already
  arguing about, consecutive campaigns decay, and category fraud twice is a
  story about you.

## The box office, and the bug that showing it exposed

The model computed a gross from the start and the interface never printed it:
you saw ROI as a bare ratio and a headline that said "made a great deal of
money", and had to do the arithmetic yourself. The release card now carries the
figure, the opening, the multiple it played, and — the number that makes ROI
legible at all — what the picture had to take to break even, which is the budget
plus prints and advertising against the share of the gross that comes back. A
film can take twice what it cost and still be a disappointment, and that is now
readable rather than implied. Credits carry their gross afterwards, so the
filmography at the end is a filmography with money on it.

Printing the number is what caught the fault under it. `realBudget` — the film's
size in start-year dollars, which is what reception, reach and box office all
read — was **snapshotted when the role was generated**, and three paths rewrite
`role.budget` afterwards: the non-union downgrade (×0.35), the unknown-lead
franchise ticket (floor $90M) and a franchise installment (floor $120M). So the
model was simulating a different film from the one on the offer board, in both
directions: early non-union work was scored as a picture nearly three times its
stated size, and the two biggest paths in the game were scored as the small
films they were generated as before being promoted. `model.realBudget()` derives
it now and nothing stores it, so it cannot go stale again.

That correction removed a phantom subsidy the early ladder was quietly living
on: careers reaching Heat > 80 fell from 15% to 10% and the earnings tail from
$137M to $92M, because the first rung was being paid for by the bug.
`K.reachBase` 0.35 → 0.46 restores it honestly — 17% and $126M, closer to the
document's ~18% than the version with the fault. Swept at N=900, then confirmed
7/7 on 3,000 careers and on three independent seed populations of 1,500.

Two stray copies of the Enter-key handler were also removed from `web/app.js`,
where a careless replacement had pasted the block inside the save-recovery catch
and inside the obituary's "Again" button — every failed replay or restart
registered another global listener, so Enter eventually clicked the primary
button several times over.

## What is not built

Named honestly, because the review's complaint about this document was that it never was:

- **The director and the studio careers** (Parts 7 and 8). The actor spine is complete; the
  director exists only as an NPC with attributes, a temperament and an affinity toward you.
- **The rest of Part 6.** Approvals exist but only two of the four do anything;
  information is collected and can only be leaked; blacklisting and the
  reconciliation broker are implemented but thinly.
- **Festivals, territories, strikes, technology eras, likeness rights** (Part 10) and
  **health, addiction, family, politics** (Part 11) beyond the health/condition curve and the
  going-broke ratchet.
- **Deals as negotiation.** Fee, billing, gross points and the holdout resolve;
  options, pay-or-play and the fee-for-approvals trade do not.
- **Deals.** Fee, billing and gross points resolve; options, pay-or-play and approvals do not.

The scope estimate in review §8 (4–6 years, 15–25 people for the full document) stands. What is
here is the phase-0 slice the review asked for: a career that happens, verified end to end.

## The shoot, played as three scenes instead of one

§5.6 always modelled a performance as three beats — intro, turn, resolution — but the game only
ever asked for one contrast-budget decision and spread it across the three formulaically. A
shoot is now three real scenes (`SCENE_LABELS` in `engine/career.js`), each with its own dailies
read, and the beats the model already computed are the beats the player actually plays.

The engine change is additive, not a rewrite: `shoot()` takes an optional `scenePositions`
(three position objects) alongside the original single `positions`, averages the three resolved
outcomes into the exact same shape `shapePerformance()` has always consumed, and every existing
caller — every sim policy, every save recorded before this change — never sets `scenePositions`
and hits the original code path unchanged. `sim/production.mjs` holds three claims: three
identical scene choices resolve to the same numbers a single choice always did (within float
rounding); a career played entirely through three real, varying scene choices still meets every
§14.9 target on its own; and the fourth approval below is reachable and bounded. The web
interface (`web/app.js` `screenScene`) is the only thing that changed behaviour for a player —
the calibrated harnesses are unaffected because they never ask for the new path.

## The cut, the approval that did nothing

Part 6 names four approvals — script, costar, director, cut — and only two of them were ever
granted by anything (noted honestly above, in "What is not built"). `cut` is now real: it is
granted by having your own production company or by being successful enough that editors expect
you in the room (`M.standing > 58`, re-derived from the actual population distribution under
`sim/production.mjs`, not asserted), and `fight_for_the_cut` (`engine/leverage.js`) spends it, or
two favours with the director, to shift a pending film's Notices and Ensemble by a small, bounded
amount (±5, the same order of magnitude as an on-set moment). It follows the pull-layer's own
rules exactly: never prompted, gated by a resource rather than a permission, and it operates on
`g.pending`/`c.project` the same way `festival_premiere` already did.

## The language pass

Two mechanics were renamed without touching a single tuned number. The positions grid printed
its internal keys straight to the player (`with (0)`, `beyond (2)`) and called the leftover
contrast a "budget" it "spent" against; `PERF_DIAL_LABELS`/`POSITION_LABELS`/`POSITION_HINTS`
in `engine/data.js` are the plain-language surface now (`Match it`, `Go big`, `Room to push it
this scene: 3 of 5 points used`) and `READ`/`POSITION_COST` — every calibrated number — are
untouched underneath them.

The ledger had the same fault the other way round: `Approvals` and `Positions` printed
`[...g.approvals].join(', ')` — the raw Set of internal keys — and `Standing`, a composite of
the four HUD meters net of scandal, sat next to them as a bare number with no context at all,
the fifth stat in a four-stat display. `APPROVAL_LABELS`/`CAREER_POSITION_LABELS` (`engine/
data.js`) replace the key dumps, and `Standing`/`Legibility` now carry the same "number — what
that number means" pattern the ledger already used successfully in one place and nowhere else.

## The moments, interleaved with the scenes instead of stacked after them

Two faults, one fix. First, a UI-only correctness bug that predates the three-scene rework:
`web/app.js` called `game.momentsFor(role)` once to build the on-set cards it showed the player,
then `shoot()` called `this.momentsFor(role)` *again* internally when `choices.momentSet` was
never passed — a second, later draw from the same RNG stream. Nothing crashed, because every
answer is keyed by moment id and any mismatch just falls back to `defaultMomentChoice()` for that
id — but a player's specific answer could silently stop mattering if the two draws did not agree,
and there was no check that would ever have noticed. `screenFilm()` now calls `momentsFor()`
exactly once, keeps the result in `choice.momentSet`, and `finishShoot()` passes that same array
back into `shoot()` — which already accepted `choices.momentSet` for exactly this purpose and had
simply never been given one.

Second, with a real set now in hand, `web/app.js` distributes it across scene boundaries instead
of showing every card in one block after the third scene — `nextScene()` shows the next moment,
if one is still owed, before advancing, and `resolveShoot()` clears anything left over the same
way it always has. The pool a shoot draws from, and how many of it a given actor gets asked about,
are completely unchanged (§0.3 rule 3 still holds — nothing new is prompted, nothing prompted more
often); only where in the shoot each one lands changed, which is what makes three scenes read as
a schedule with things happening between setups rather than a form followed by a debrief.

The dailies line shown between scenes is purely a client-side preview (no RNG, nothing journaled)
and now carries a small, real consequence to match: a scene played past its room nudges the
director's affinity down a point, the same bounded scale a moment's own effect already uses —
`sim/production.mjs`'s legacy-equivalence check confirms this only ever fires on the new
scene-by-scene path, never retroactively changing a number the calibrated harnesses check.
