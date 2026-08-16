# CALLBACK
### A design document for a deep film-industry life simulator
*v9 — the actor spine built, verified end to end, and folded back in*

**What's in it:** the Director as a full parallel career (Part 7), the Studio /
business layer (Part 8), genres as real economies plus the franchise and
merchandise business (Part 9), a simulated industry with guilds, strikes, festivals and
technology shifts (Part 10), and a life layer where careers end for reasons that have
nothing to do with talent (Part 11). All new economies are simulation-tuned, same as v1's
reception model — see Part 14 for verified numbers. *(v9 — the four "(Part 11)" cross-references
in this paragraph were a leftover placeholder in v8; corrected to the parts they actually name.)*

**What v9 changes:** Parts 0, 4, 5, and 6 — the actor spine — were built and played, not just
specified, and this revision folds back what that found. The headline fault, caught by the first
end-to-end career simulation ever run against this document (`callback-design-review.md`): Standing
gains were billing-weighted and decay wasn't, so a beginner accrued at a fifth the rate while paying
full price — no career could climb off the bottom rung, and none of §14.9's seven whole-career
targets were met. §4.3 has the fix. Alongside it: the offer-board threshold that made two of three
casting paths the same path (§4.4), the union catch-22 with no stated entry point (§4.0, new — v8 had
no character-creation design at all), Notices and Ensemble defined twice and never reconciled
(§4.10, §5.6), a Presence verb that could never fire (§4.1), two incompatible box-office models
(§4.10), a shoot's three beats existing only as a formula until this pass turned them into three
scenes actually played (§5.6), a fourth approval named after the director's Final Cut but never
built for the actor it was assigned to (§6.3), an agent tier nobody could ever change (§4.5, §6.6),
and an Indispensability decay that could freeze a franchise open forever instead of ever really
ending it (§6.4). §14.9 is no longer "to be verified" — it's a table of what a 3,000-career
simulation actually measured. A later pass went back over §5 specifically — the shoot itself —
and closed two more gaps the three-scene rework left open: the three on-set moments were a fixed
set asked every time until §5.12 turned them into a pool drawn from what the specific production
actually is, narrowing with experience the way §0.3 Rule 3 already requires everything else to;
and §5.14's account of the edit never acknowledged §6.3's new actor-side approval, so an actor who
earned a seat in the room and a director cutting the film were, on paper, still strangers to each
other — fixed with a cross-reference in both directions. A further pass gave the three scenes
themselves a narrative identity: §5.6 now names the three-act structure the `intro`/`turn`/`reso`
weighting was always a numeric description of (setup, set piece, resolution), and names what the
turn concretely *is* per genre — the first kill, the confrontation, the falling-out, the reveal —
and which of §5.5's four dials is most likely carrying it, without changing a single formula
either section already specified.

**A full connective pass then went across every Part**, not just the built ones, looking
specifically for §3.3's own rule — one Standing model, one Legibility engine, one Rolodex, one
calendar — stated as an intention but not actually honoured. It found, and fixed, real ones: §8.2
still carried its own box-office model with different constants from §4.10's, the exact
two-models problem §4.10 already claimed to have fixed and hadn't, in this section, actually
fixed; §7.3 said it was "amending" §4.7's performance formula with a Director Command term that
§4.7 never actually showed; §10.6 called its own era system "sketched in §4.14" after §4.14 had
explicitly said that content was removed; §13's build plan cited "the edit as three real choices"
at §5.8 (script register) instead of §5.14 (the actual edit); and half a dozen mechanics —
franchise backend as a retirement plan, the two career-switching Rolodex-transfer tables, the
declined-offers list tracked in §5.17 and paid off in §11.8, Animation's odd fit as a "genre" when
§4.2's own affinity vector has no such entry — were specified twice in different Parts with no
link between the two, or specified once with no pointer from where a reader would naturally look
for it. All fixed with cross-references or, where two versions had actually diverged, one
canonical formula that the other Part now reads instead of restating. Parts 1–3, 7–13, and 15 are
still substantially the original v8 text — none of that was built — but they no longer contradict
Part 4/5/6 or each other where they touch the same mechanic.

**Part 10 gained an engine it had only ever implied.** §9.3's genre-cycle formula reads ROI off
"every film in the genre" as if a whole population of films were being resolved every quarter, and
nothing said where they came from if you weren't in them; §4.12 promised a Rolodex where NPCs have
careers that run on their own — a rival flames out, a producer who blacklisted you gets fired and
the door reopens — as a design goal with no mechanism under it; §5.17 and §11.8's obituary promise
to name who took the role you declined and what they won, with nothing to query. **§10.0, new**, is
the mechanism for all three, and it's one idea: a role you don't take isn't removed from the game,
it's cast with someone else — through §4.4's own `Utility` formula, run for that candidate instead
of you — and that film is made and resolved through §4.7 and §4.10, the same formulas as any of
yours. It feeds the genre-cycle formula its population, gives the Rolodex's background NPCs real
(if mostly aggregate) careers, introduces actor/director rivals as the same idea §8.8 already runs
for studios, surfaces once a year as a pull-only trades digest under §0.3 Rule 2b, and is scoped
explicitly — full per-film simulation only for tracked Rolodex members, rivals, and franchise
principals; the rest resolved in aggregate, the same "simulate well what will be seen" principle
§10.5 already uses for its four built industries. Cross-referenced forward from §9.3, §4.4, §4.12,
§8.8, and §11.8.

**A short follow-up pass then carried §10.0 the rest of the way out**, into the parts a first sweep
naturally doesn't reach on its first pass through a new section: §3.2 and §3.3 now cite it as the
mechanism behind promises those sections already made (NPC "careers," and the one-spine rule
holding for background characters, not just player-controlled ones); §6.1 stops implying Public
standing and Information are free-standing leverage systems and points them at the substrate they
already have (§4.13's scandal table, §4.12's Rolodex edges); §6.5's holdout and §6.6's
"Recommend"/"Blacklist" verbs now name §10.0's `CastingResolution` as what they actually move,
instead of an unspecified outcome; §7.3 generalises Rivals to directors, and §7.4 explains what
`Difficulty` was always implicitly pricing in; §9.5's recast and §9.6's shared-universe rules now
resolve through the same mechanism as any declined role; Part 12's schema gained a
`resolvedProjectId` pointer on `declined` entries and a scoping flag on `rolodex` entries, so the
obituary and the full-sim-only rule both have somewhere real to read from; Part 13 lists §10.0 as
Phase 9 scope and notes the trades digest could ship as early as Phase 4; Part 14 adds the
"re-verify once the population is real" caveat §14.1 already models elsewhere; and Part 15 cites
§10.0 as the mitigation an existing risk row already described, plus one new row for a risk §10.0
itself introduces — an off-screen NPC career feeling arbitrary the day it resurfaces. Nothing here
is a new formula or a new stat; every addition names which existing mechanism a verb, a promise, or
a schema field was always supposed to be reading from.

**A language pass then closed out the gaps an audit found in the earlier plain-language cleanup.**
That cleanup (§4.1, §5.3, §5.5) never fully propagated: §4.2's and §5.15's **Fit** had no gloss
anywhere, unlike Legibility; `YourNotices` leaked back into plain prose in §4.10 and §5.14 even
though §5.6 had already settled on the clean "Notices"/"Ensemble"; **Indispensability** (§6.1,
§6.4) read as a raw stat name with no stated connection to §15's own rule that non-core numbers
are shown to the player as words, not values; and §7.2's director attribute table (Vision,
Command, Craft, Taste, Efficiency) looked like a raw stat block despite §15 explicitly saying the
director's five attributes get the same word-only treatment as the actor's. Fixed: Fit got the
same one-line, first-mention gloss Legibility already had; the stray `YourNotices` instances were
normalized to the plain term already established in §5.6; Indispensability's note in §6.1 now
states explicitly that the player only ever sees the qualitative band already in §6.4's table; and
§7.2 gained a "What you'd actually hear" column showing what each attribute sounds like in play,
plus a note citing §15's rule directly. No mechanic changed — every fix is a gloss, a cross-
reference, or a term swapped for one already defined elsewhere in the document.

**Then the Rolodex's relationship layer got built out**, inside §10.0, at the user's specific
request to keep it in the world doc rather than scatter it. §4.12 already stored `affinity`,
`grudge`, `sharedProjects`, and `lastContact` per NPC, but those four numbers only ever fed one
thing — the casting `Utility` term — which fails §0.1's own Decision Test: a relationship that's
only ever a hidden multiplier on offers isn't a decision. §10.0 now has the rest of it: hidden
**Agendas** (six types — Ascent, Legacy, Loyalty, Redemption, Vindication, Mentorship) that bias
both an NPC's own §10.0 career choices and how much a player's actions land, never shown as a
number; a named **relationship arc** (`STRANGER → FAMILIAR → (ALLY|RIVAL) → (LOYAL|ESTRANGED) →
(LEGACY|SEVERED)`) with transition thresholds read off fields §4.12 already tracks; pull actions
that build a relationship instead of spending one (Check in, Show up for them, Read their Agenda,
Vouch for them); a small, explicitly budget-capped set of NPC-initiated pushes (a Loyal NPC's own
crisis, an Estranged NPC's arc resolving, a Rival's flameout) so the new depth doesn't blow §0.2's
decision cap; a payoff table connecting relationship state to concrete effects (financing access,
softened scandal noise, an early private read on the trades); and a Legacy/loss mechanic extending
§6.2's "favours die with people" into something with real, bounded weight when a Loyal or Ally
NPC's own simulated career ends. Cross-referenced back from §4.12.

**Part 0 is the editing pass.** It states the rules every system has to pass and lists what came
out: the decision load per in-game year drops from ~55 to ~15 without removing a mechanic. Read it first.

**Part 5 is the work itself** — six dials that decide what a film *is* (pace, colour, scale,
intensity, clarity, texture), performance dials that play with or against them, coherence,
landmarks, and the edit as authorship. The actor plays it through **four dials taking named
positions against the film** — with, beneath, beyond, against — paid for from a contrast budget set
by craft and by who's behind the camera. §5.2 and §5.5 each document a system cut for being a
solvable stat check. This is the core loop and it should be built first — it now includes the
three-scene rework in §5.6.

**Part 6 is the answer to "the player is a passenger."** Leverage — favours, approvals,
indispensability, and forty ways to act on the industry rather than wait for it. It costs nothing
against the decision budget because none of it is ever pushed at you (§0.3, Rule 2b). It also
removes the career ladder: start as anything, add anything at any age, hold everything at once.

---


## Contents

0. [PART 0 — DESIGN RULES AND THE CUT LIST](part-00-design-rules-and-cut-list.md)
1. [PART 1 — HOW BITLIFE'S ACTOR PACK ACTUALLY WORKS](part-01-bitlife-teardown.md)
2. [PART 2 — WHAT'S MISSING](part-02-whats-missing.md)
3. [PART 3 — CALLBACK: DESIGN OVERVIEW](part-03-design-overview.md)
4. [PART 4 — THE ACTOR](part-04-the-actor.md)
5. [PART 5 — THE WORK: CREATIVE DECISIONS](part-05-the-work.md)
6. [PART 6 — LEVERAGE: PLAYING THE INDUSTRY](part-06-leverage.md)
7. [PART 7 — THE DIRECTOR](part-07-the-director.md)
8. [PART 8 — THE STUDIO](part-08-the-studio.md)
9. [PART 9 — GENRES, FRANCHISES, AND THE TIE-IN ECONOMY](part-09-genres-franchises-and-tie-ins.md)
10. [PART 10 — THE WORLD](part-10-the-world.md)
11. [PART 11 — THE LIFE](part-11-the-life.md)
12. [PART 12 — DATA SCHEMAS](part-12-data-schemas.md)
13. [PART 13 — BUILD PLAN](part-13-build-plan.md)
14. [PART 14 — TUNING TARGETS](part-14-tuning-targets.md)
15. [PART 15 — RISKS](part-15-risks.md)
