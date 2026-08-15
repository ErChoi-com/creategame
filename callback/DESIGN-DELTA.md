# CALLBACK — what changed between the document and the game

`docs/callback-design-doc-v8.md` is the design. `docs/callback-design-review.md` is the
adversarial read that found the design, run end to end, does not produce a career: not one of
the seven targets in §14.9 was met, 80% of simulated careers never played a lead, and nobody
became a star in four thousand attempts.

This directory is the implementation, and it works. Below is every place it departs from the
document, why, and which check holds it in place.

Run the checks:

```bash
node callback/sim/career-sim.mjs 3000     # §14.9 — 7/7
node callback/sim/subsystems.mjs          # §14.1, §5.3-5.6, §9.3 — 16/16
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

## What is not built

Named honestly, because the review's complaint about this document was that it never was:

- **The director and the studio careers** (Parts 7 and 8). The actor spine is complete; the
  director exists only as an NPC with attributes, a temperament and an affinity toward you.
- **Leverage** (Part 6). Favours accrue from generosity on set and are spendable nowhere yet.
- **Festivals, territories, strikes, technology eras, likeness rights** (Part 10) and
  **health, addiction, family, politics** (Part 11) beyond the health/condition curve and the
  going-broke ratchet.
- **Awards as a campaign.** The season resolves, and `runAwardsSeason()` accepts campaign spend
  and category fraud, but the UI never offers either — it is a system without a screen.
- **Deals.** Fee, billing and gross points resolve; options, pay-or-play and approvals do not.

The scope estimate in review §8 (4–6 years, 15–25 people for the full document) stands. What is
here is the phase-0 slice the review asked for: a career that happens, verified end to end.
