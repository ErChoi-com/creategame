# CALLBACK — DESIGN REVIEW
### v8, 2,659 lines, 15 parts, 7 "verified" subsystems
*Two independent reviews: a hostile read by a designer who didn't write it, and the first end-to-end career simulation ever run against the document.*

---

## VERDICT

**The document is a well-tuned collection of subsystems that has never been run as a game, and when you run it as a game it does not work.**

I simulated 4,000 complete careers wiring together §4.4 (casting), §4.7 (performance), §4.10 (reception), §4.3 (standing) and §11.6 (money) exactly as specified. Against the doc's own targets in §14.9:

| §14.9 target | Stated | Measured |
|---|---|---|
| Median career length | 26 yrs | **12** |
| Careers reaching Heat > 80 | ~18% | **0%** |
| Careers with zero award nominations | ~55% | **98%** |
| Award wins per 100 careers | 21 | **0** |
| Median lifetime earnings | $6–11M | **$0.3M** |
| Top-decile lifetime earnings | $90M+ | **$0M** |
| Lead role after 42 | ~30% | **4%** |

Not one target is met. **80% of careers never play a lead.** There is no upper tail — nobody becomes a star, ever, in four thousand attempts.

This is not a tuning problem. It is a structural one, and it was invisible because every previous verification tested one subsystem in isolation. §14.9 — the only section that would have caught it — was the one section marked *"to be verified in phase 0."*

---

## 1. THE LADDER HAS NO BOTTOM RUNG

The single most important finding.

**Standing gains are billing-weighted. Standing decay is not.**

```
ΔHeat = billingWeight × (…)        billingWeight: lead 1.0, supporting 0.55, bit 0.2
Heat decay = −9/yr, applied in full regardless of what you played
```

A beginner's realistic tier is bit parts. They therefore accrue Standing at **one fifth the rate** while paying decay at the full rate. The maths:

```
bit-part actor, 91% annual Heat retention → converges to Standing 9.1
bit-part actor, 94% annual Heat retention → converges to Standing 14.1
```

Neither ever reaches 25, and supporting roles don't open until roughly 47. **The tier you can reach cannot outrun the decay on that tier**, so there is no path from zero to a career. The offer probabilities themselves are fine — a beginner's 1.7% shot at a lead is correct and good. The problem is that nothing they *can* get lets them climb.

### And the gain terms are centred on zero

Separately and compounding: over 200,000 role resolutions,

```
median ROI = 1.11        → 9 × clamp(ROI − 1) is centred at +0.11
mean AudienceScore = 55.0 → 0.16 × (AUD − 55) is centred at −0.01
```

Both gain terms in `ΔHeat` sit almost exactly at zero by construction, so only an ROI > 2 hit moves anything. **A flat decay against gain terms centred on zero can only ever integrate to negative.**

### The correction

Structural, not cosmetic. Decay must be proportional (self-limiting, creating an equilibrium), gains must be re-centred below the median outcome, and **simply working must be worth something**:

```
ΔHeat = billingWeight × (3.0 + 9·clamp(ROI − 0.90, −0.6, 2.2) + 0.16·(AUD − 52))
Heat  ×= 0.91 per year                    // proportional, not flat −9
```

| Parameters | Equilibrium Heat, working lead |
|---|---|
| As written | **15** (p10 4, p90 27) |
| base 3, c₁ 0.90, c₂ 52, keep 0.91 | **58** (p10 48, p90 71) |
| base 4, c₁ 0.88, c₂ 50, keep 0.88 | 53 (p10 45, p90 64) |

That fixes the equilibrium for someone already working. **It does not fix the bootstrap** — I applied it and re-ran, and 77% still never play a lead. The on-ramp needs designing, not tuning: either decay scales with billing too, or early credits carry a "discovery" multiplier, or the bit→supporting gap needs a bridge that isn't Standing.

---

## 2. THE DECLARED CORE LOOP IS NOT CONNECTED TO ANYTHING

Part 5 is called "the core loop, build it first." It has no defined interface to Part 4.

- §4.10: `YourNotices = 0.52·Performance + 0.25·FilmCritic + 0.13·visibility + N(0,7)`, mean 58.
- §5.5–5.6: `Notices` is an independent output of the position system, values 70–81, computed from a hardcoded `base = 62` and `+0.10·Presence`, **with no reference to the Performance roll at all.**
- §5.5 claims `Ensemble` "feeds ProjectQuality (§4.10)" — but §4.10's `EnsembleScore` is a billing-weighted mean of cast *Performance* values. Different quantity, different axis.
- §5.11's swing penalty is "Notices −8.5, Ensemble −5.1" — units unstated against either definition.

The harness proves it: `reception()` computes ensemble with zero palette, position, coherence or contrast terms; `palette()` computes Notices with zero reference to Performance. **The two flagship verified subsystems are verified in isolation and are mutually inconsistent.**

§14.1 even warns "if you change any constant in §4.10, re-run the sweep." Part 5 injects a whole new layer of terms into Performance, Ensemble, Notices, Audience and Critic scores. The sweep was never re-run. **Every number in §14.1 describes a game in which Part 5 does not exist.**

---

## 3. TWO INCOMPATIBLE BOX-OFFICE MODELS

§4.10 and §8.2 both define the box office, differently, and the harness runs one in `reception()` and the other in `studio()`.

| | §14.1 as published | Using §8.2's own newer model |
|---|---|---|
| corr(Performance, ROI) — *"the design's signature number"* | 0.23 ✅ | **0.13** |
| corr(FilmCritic, ROI) | 0.30 ✅ | **0.17** |

Two of the five headline correlations fall outside their stated targets when you use the document's own more recent economics. §9.5 explicitly supersedes Part 8's franchise curve; nobody applied the same discipline to the box office.

---

## 4. THE THING BEING AVOIDED: THERE IS NO PLAYER IN THIS DOCUMENT

2,659 lines. Search for character creation, starting conditions, onboarding, UI, screen layout, session length, or one line of the game's prose. Nothing. §15 mentions UI once, to say four meters are visible.

Missing entirely:

- **How a run starts.** §6.7 says "start as a 24-year-old director, or a 30-year-old with family money." With what attributes, money, Standing, Rolodex, agent, union status? Never specified. §1.2 demolishes BitLife's ages 0–18 grind and supplies no replacement.
- **The union catch-22.** §10.1 locks you out of union productions until you have three union credits. How you get the first three is never addressed.
- **The director on-ramp.** §7.4's own verified output is *2 films in 30 years* for a newcomer. The doc calls this "bleak and correct," says the climb out "must be the early-career arc," and then doesn't design it.
- **Any writing at all.** For a game whose nearest comparable is BitLife — a product whose entire appeal is voice and tone — there is not one sample event, one line of NPC dialogue, or one paragraph in the game's register.

Every verification in Part 14 measures the model's statistical properties. Not one measures a person's experience.

### The sharper version

The design's thesis may be anti-fun, and the doc files it under strengths. §4.7 hides your Performance number permanently. §4.10 correlates it 0.23 with box office. §5.14 lets a director destroy you in the cut and notes approvingly that "the actor may never find out." §11.8 reveals your true scores in the *obituary*.

That is a game which spends forty in-game years telling you, with a receipt, that your choices didn't determine the outcome — and hands you the answer key after the run is over. §15's mitigation is "always attribute," but **attribution is an explanation, not agency.** Being told forty times "you were good, the edit buried you" is not the same as it having mattered. This is the largest fun risk in the design and it appears in the risk table as a UI problem.

---

## 5. "ONE SPINE" IS ABOUT HALF REAL

§0.3 Rule 4 — *"if a new feature needs its own version of Standing, Legibility, Rolodex or Calendar, it doesn't go in"* — is the entire scope defence. Checking the studio against it:

| Spine system | Studio's version | Real? |
|---|---|---|
| Standing | §8.9's `ExecutiveStanding`, a separate scalar with its own update function | **No** |
| Legibility | §3.3 claims "Brand." **There is no studio Brand system anywhere in the document.** | **No** |
| Calendar | Player is 4 quarters/year; studio is a year+week release grid. Two granularities in one schema. | **No** |
| Rolodex | Genuinely shared | Yes |

The studio needs its own version of three of four. The doc's response was to quietly mark Part 8 optional without ever admitting the rule broke — which means **the rule doing all the scope-defence work has already been suspended once, silently.** The Actor/Director spine is real and well-argued; the claim should be scoped to two careers.

---

## 6. OTHER STRUCTURAL FAULTS

**One of the three paths to a role is unreachable.** §4.4's "Offer — triggered when Utility − difficulty > 25." Ceiling analysis: max Utility ≈ 86 without relationships, lead difficulty is 68 in the doc's own schema. A maxed star with a perfect-fit role reaches `U − d ≤ 18`. The only way over is `RelationshipBonus` — which is path 3. **Paths 2 and 3 are the same path.**

**The 0.80 ensemble share is asserted and wrong for a normal cast.** With the doc's own billing weights: a lead plus one bit player gives 0.83, but two leads plus three supporting plus four bits gives **0.22**. Sensitivity: at share 0.48, corr(Performance, FilmCritic) drops to 0.26 against a 0.40–0.48 target. On a realistically cast film your work barely touches whether the film is good.

**Legibility bands contradict the update rule that produces them.** Running §4.2's rule over a career: an actor who plays five different lanes across forty films reaches Legibility 35 — never leaving the band §4.2 describes as "casting directors don't know what to do with you." Break-type, which §4.2 calls "the actual dramatic arc of most real careers," is mathematically hardest exactly when the fiction says it should be the move.

**"Standing" is used as both a four-vector and an undefined scalar.** §6.3, §6.5 and §8.1 gate the entire leverage layer on "Standing 65 / 70 / 75 / 85." No such scalar is defined anywhere and the schema has no field for it. Part 6 — pitched as the answer to "the player is a passenger" — is gated on a quantity that doesn't exist.

**Rule 3 contradicts Part 6 directly.** Rule 3: "if year 45 has more choices on screen than year 15, the pacing is broken." Part 6 accumulates leverage permanently, stacks positions, and gives a franchise actor fifteen simultaneous verbs. §15 names no mechanic that sheds anything.

**"Pull is free" is an accounting trick.** §6.8's three worked careers are all built on leverage play, so not opening the menu is strictly worse, which by §0.1's own Decision Test makes it compulsory. Then §15's mitigation for discoverability is to surface it "as a conversation with your agent" — a push prompt, back in the budget the exemption existed to protect.

**The average NPC director is worse than the blind roll.** §4.10 gives actors `PostLuck ~ N(52,14)`. §7.7 gives directors `45 + 0.30(Craft−50) + 0.25(Taste−50)`, which at the stated population mean of 58 yields **49.4**. Once directors are real characters, every film in the world gets a worse edit than the model was tuned against.

**Presence's "verb" never fires.** §4.1 builds a "two genuinely different careers" claim on `NoticesFloor = 0.10 × Presence`. A floor of 9 against a Notices mean of 58 and sd 11.5 is never binding.

**Rule 1 is violated four times.** "Nothing decays because you forgot to click" — then favours decay from no contact (§6.2), critics need "years of cultivation" and mentoring costs "a block a year" (§6.6), and the health plan requires clearing a threshold every year (§10.1). §0.2's own budget table contains a line item literally called "Rolodex upkeep."

**The three on-set moments are nine table cells repeated ~180 times per career**, with no content plan, variant count, or authoring budget. It's the most-repeated interaction in the game and it's solved by hour three.

**§4.10 contains a duplicated block whose second copy misstates its own formula** — claiming `ΔPrestige` reads `YourPerformance` directly, which it does not.

**Version drift is visible in the first fifteen lines**, including unresolved `(Part 11)_TMP` placeholders pointing at wrong parts, and column headers labelled v3/v4 in a v8 document.

---

## 7. THE VERIFICATION IS THINNER THAN IT LOOKS

Of seven "verified" subsystems, **three are real simulations of emergent behaviour** (reception, studio slates, genre cycles) and one more is a real sim (director pipeline). The rest:

- The **palette check** is a property test of hand-authored weight tables — it verifies the tables the author wrote have the properties the author wanted. Close to a tautology.
- **Leverage** and **decision budget** are arithmetic printed at four points, not simulation.

Meanwhile §14.1 is headed "verified ✅" while containing a check the harness itself fails and prints as `<<<` (corr(FilmCritic, Audience) = 0.39 against a 0.40–0.50 target, softened to "⚠️ boundary" inside a section titled *verified*). The front matter claims "all new economies are simulation-tuned"; §14.5 is a hand-fit curve and §14.9 is explicitly unverified.

**Load-bearing and unsimulated**, ranked: Standing dynamics and the Quote curve (broken, §1 above) · the offer board (dead branch) · Persona/Legibility (bands contradict the rule) · Part 5's integration into §4.10 (doesn't exist) · the calendar, called "the single best mechanic in the design," which is also *excluded from the phase-1 slice* · the age cliff · awards (a +20 posthumous narrative bonus against N(0,9) noise means narrative dominates merit ~2:1) · the money ratchet and health-plan cliff · nine technology eras each of which "rewrites a rule of the game."

---

## 8. SCOPE

No dates, headcount, budget, engine, platform, business model, content budget, or market sizing anywhere in 2,659 lines.

Counting honestly: roughly **65 distinct simulation subsystems**, plus a persistent NPC graph where each NPC runs their own career, plus a world sim (11 genres with boom/bust, 5 festivals, 5 territory blocs, 4 international industries, 9 technology eras, 3–5 rival studios each running the full slate simulation), plus Rule 2's requirement that *every outcome ships with an attribution UI*.

"Phases 0–5 are a complete, shippable game" doesn't survive contact with its own contents — those phases include the reception model, all of Part 5, the calendar, deals and agents, Persona/Legibility, the full Rolodex graph *with NPC arcs*, the entire awards season, and all of Part 6. That's ~25 subsystems including the hardest one.

And the phase-1 slice explicitly excludes the calendar — **so phase 1 cannot test the mechanic the design is proudest of.**

Realistic full scope at ship quality: **4–6 years, 15–25 people.** Nothing in the document acknowledges a number remotely like that.

---

## 9. WHAT'S ACTUALLY GOOD

Briefly, because it's real:

- **The Performance/Project decoupling (§4.10)** is a genuine, novel idea, correctly implemented, and the tuning discipline behind it is above the norm for a design doc.
- **Taste as noise rather than power** (§7.2, §5.9) — attributes determine how clearly you forecast, not whether you're right — is the best single idea in the document and generalises well.
- **The landmark → archetype → genre-boom → cliché loop (§5.4)** is elegant: player authorship permanently mutating the world model, then being consumed by it.
- **The health-plan cliff (§10.1)** and the **lifestyle ratchet (§11.6)** are specific, true, unmodelled anywhere else, and emerge from three numbers each.
- **The generosity → trust → contrast budget chain (§5.7)** is the one place a long social loop terminates in a concrete capability rather than a bonus.
- **Genre cycles (§9.3)** — the 8-quarter greenlight lag as the source of overshoot is correct, well-tuned, and the note about the two failure modes hit while tuning is the most credible paragraph in Part 14.

---

## 10. WHAT I'D DO NEXT, IN ORDER

1. **Fix the ladder.** Make decay billing-aware, or add an early-career discovery multiplier, or build a bridge from bit to supporting that isn't Standing. Then re-run the career sim until §14.9's targets are met. **Nothing else matters until a career can happen.**
2. **Define one Notices and one Ensemble.** Write Part 5's outputs as terms inside §4.10's equations, then re-run the reception sweep. Delete whichever box-office model loses.
3. **Define Standing-the-scalar**, or rewrite every Part 6 threshold in terms of the four meters.
4. **Write the first hour.** Character creation, the first offer, the first shoot, twenty lines of actual game prose. This is the real gap and eight versions have avoided it.
5. **Then** go back to features.

The honest summary: **the simulation is more defensible than any design doc needs to be, and the game is less designed than a prototype needs it to be.** The eight iterations went into making the model rigorous. Not one went into the thing a person touches — and the model, when finally run end to end, doesn't produce a career.
