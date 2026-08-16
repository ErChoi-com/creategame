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
other — fixed with a cross-reference in both directions. Parts 1–3, 7–13, and 15 are the original
v8 text; none of that was built yet, and this pass didn't touch it.

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
