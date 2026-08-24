# PART 0 — DESIGN RULES AND THE CUT LIST

Parts 4–11 describe a lot of systems. This Part is the filter they all have to pass, and the record of what didn't. It was written last and it changed the rest of the document.

## 0.1 The Decision Test

> **Every system must produce a choice where two options are both defensible.**
> If a system produces a *task* — something you should always do, or must remember to do — it is not a system. It is a chore with a stat attached. Cut it, or convert it into a choice.

BitLife fails this constantly, and the first three drafts of this document inherited the habit. Acting lessons four times a year is not a decision; it's a button you press because not pressing it is strictly worse. Posting on social media to stop your fame decaying is the same thing. Both are gone.

The test has a useful corollary: **if you can write down the optimal play in one sentence, it isn't a mechanic.** "Always take the recurring TV role" means the recurring TV role is mispriced.

## 0.2 The decision budget

A 40-year career at four quarters a year is 160 turns. How much should happen in each?

Counting v3 honestly, a working actor-director faced roughly **55 decisions per in-game year** — deal terms, prep allocation, on-set events, fame upkeep, relationship maintenance, development slate tending. Over a career that's about **2,200 decisions**, and the great majority were small, repetitive, and had a correct answer.

v4 targets **~15 per year**, or about **12 for an actor-only run**:

| | v3 / yr | v4 / yr |
|---|---|---|
| Accept / decline offers | 3 | 3 |
| Deal terms | 9 | **1** |
| Prep → **setting the palette** (§5.3, §5.5) | 9 | **2** |
| On-set events → **the three moments** (§5.6) | 12 | **4** |
| Fame maintenance | 4 | **0** |
| Rolodex upkeep | 4 | **1** |
| Season / campaign | 2 | 2 |
| *Actor-only subtotal* | *43* | ***13*** |
| Development slate (directing) | 12 | **3** |
| Thematic intent (directing, §5.7) | — | **1** |
| **The edit** (directing, §5.8) | — | **2** |
| **Total (pushed prompts)** | **55** | **19** |
| **Over a 40-year career** | **2,200** | **760** |

**The target moved from ≤15 to ≤20, deliberately.** Part 5 adds three pushed decisions per year and they are the three most valuable in the game — what the character is, what happens in the room, and what survives the cut. The budget was never about minimising prompts. It was about not spending them on deal paperwork and social-media upkeep. **What matters is the mix, not the count**, and the mix is now: nothing pushed at the player is administrative.

The swing (§5.4) is *not* in this table. Like everything in Part 6, it's pull — the player declares it.

Part 6's leverage actions are **not** in this table and never will be — they're pull, not push (Rule 2b below).

That's still a **65% reduction** against v3, and almost none of it comes from removing systems. It comes from removing the *repetitions inside* systems. Every mechanic named in Parts 4–11 is still there. You just touch each one when it matters instead of every time it exists.

## 0.3 The four rules

**1. No upkeep.** Nothing decays because you forgot to click. Standing decays because time passes and the industry moves on — that's systemic pressure, and it's fine. There is no maintenance button anywhere in this game.

**2. Always attribute.** Any time an outcome surprises the player, show the causal chain. After every release: *"Your performance: strong. The edit: buried you. Reviews: mixed. Opening: soft."* A simulation this decoupled is indistinguishable from a random number generator unless you show your work. This is not a nice-to-have — it's what makes the core idea legible instead of infuriating.

**2b. Push is budgeted; pull is free.** The ~15/year ceiling applies only to prompts *the game pushes at you*. Actions the player goes looking for cost nothing in tedium, because engaging with them is voluntary. This is what lets Part 6 add forty verbs without adding a single obligation — and it's the rule to apply to anything added later. **Breadth belongs in pull. Never in push.**

**3. Options should narrow, not multiply.** A 60-year career must not become 60 years of spreadsheet management. Late career should offer *fewer, heavier* decisions than early career. If year 45 has more choices on screen than year 15, the pacing is broken.

**4. One spine.** Actor, director and studio share one Standing model, one Legibility engine, one Rolodex, one calendar (§3.3). If a new feature needs its own version of any of those four, it doesn't go in.

## 0.4 Ambitions — what "winning" means

A life sim with no goal is drift, and this one is long enough for drift to be fatal. At the start of a run the player picks an **Ambition**. It doesn't restrict anything — no content is gated by it, and Part 6's rule stands: requirements are resources, never permissions. It decides what the obituary measures you against, and it gives the mid-game a shape.

| Ambition | Measured by |
|---|---|
| **The Work** | Lifetime average of `YourNotices` across credited roles |
| **The Prize** | Awards won, weighted by category |
| **The Fortune** | Peak net worth and what survived to the end |
| **The Run** | Years spent working at lead or director level |
| **The Franchise** | Peak franchise strength of a property you're identified with |
| **The Voice** | Auteur Legibility sustained above 70, with critics on your side |

The interesting part is that these conflict in exactly the ways the systems already model. The Fortune wants tentpoles and merchandising points; the Prize wants prestige drama and a campaign block every year; the Run wants you to leave the ingenue lane at 35 and never chase Heat. You can change Ambition once, at any point, and the game notes when you did — because people do.

## 0.5 The cut list

What came out of v3, and why.

| Cut | Reason |
|---|---|
| **Acting lessons as a repeated yearly action** | Fails the Decision Test — no reason not to. Craft now grows from *work itself* and from coaching choices that cost a calendar block. |
| **Fame maintenance / social posting** | Pure chore treadmill inherited from BitLife. Standing decays systemically instead. |
| **Actor attributes: Discipline** | Only modified prep efficiency and on-set event rolls. Folded into Resilience. |
| **Director attributes: Nerve** | Barely referenced. Holding your vision under pressure *is* Vision. |
| **Director attributes: TechCraft + Eye** | Two attributes that did the same job — feed PostLuck and critic score. Merged into **Craft**. |
| **Prep as a week-allocation puzzle** | An optimisation you solve once and then repeat 20 times. Now one choice from six, each with a real cost. |
| **On-set events, 6–10 per shoot** | Most were flavour. Cut to **3 per shoot**, each consequential. |
| **Rolodex of 40 tracked NPCs** | Too many relationships to hold in your head. Now **8 named and tracked**; the rest are background who surface when they matter. |
| **12 sales territories** | Optimisation busywork. Cut to **5 blocs**, one decision: who you presell to and what you give up. |
| **8 international industries** | Four built well beats eight sketched. Kept: Hollywood, Bollywood, Korean serial TV, European art cinema. The others become flavour destinations. |
| **6-source financing stack, assembled per film** | Now **three presets** (studio-financed, independent, streamer buyout) with one meaningful override — usually the tax-credit location trade. |
| **Development momentum tended quarterly** | 3 projects × 4 quarters = 12 decisions a year for one career. Now **one action per project per year**. |
| **Politics as a faction-standing matrix** | Mechanically thin and it risked turning editorial. Kept as *events with costs and constituencies*; the matrix is gone. |
| **The studio career, as a core mode** | It's a strategy game wearing a life sim's clothes. Now an explicit **optional late-game mode** (Part 8), reachable but never forced. |
| **The old era-and-life summary stubs in Part 4** | Vestigial — Parts 10 and 11 replaced them. |

## 0.6 What is deliberately *not* cut

Every one of these is expensive, and every one earns it:

- **The Performance / Project split** and the separate `YourNotices` score. This is the game.
- **The calendar.** Opportunity cost is the single best mechanic in the design.
- **Persona and Legibility.** Typecasting is the actor's real problem and nothing else models it.
- **Director loyalty rosters.** Being handed a part by someone who trusts you is the best feeling available.
- **Taste as information.** One line of noise that produces a whole kind of career.
- **The age cliff.** Softening it would be a lie.
- **The health-plan threshold, uninsurability, and the lifestyle ratchet.** Three pieces of arithmetic that end careers for reasons that have nothing to do with talent.
- **Genre boom and bust.** The industry has to move on its own or none of the strategy means anything.
- **The obituary, and the roles you turned down.** The payoff for everything else.

---

