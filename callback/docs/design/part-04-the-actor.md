# PART 4 — THE ACTOR

## 4.0 Character creation — the opening hour *(v9, new)*

Nothing in v8 specified how a run starts. Phase 0's build reached the end of every other system before noticing this gap, and it's the largest single omission the review flagged: no starting conditions, no onboarding, no first thing the player actually does.

**Four backgrounds**, deliberately not ranked against each other — each is short of something different, not simply worse:

| Background | Starts with | Short of |
|---|---|---|
| **Conservatory** | Craft 62, technique, a showcase nobody important came to | Money, connections, a recognisable face |
| **Discovered** | Presence 70, a manager, momentum | Craft 28 — has never had a lesson |
| **Regional stage** | Craft 70, years of range | Age (33 already) and a total absence of union credits |
| **Family money** | The rent solved, room to say no to bad work | Presence and Resilience — the room can tell, and it isn't automatically on your side |

The player also picks an **Ambition** (§0.4) here — gates nothing, decides what the obituary measures.

**The first three credits are a closed loop unless something opens it.** §10.1 requires three union credits to work union productions and never says how the first three happen. They happen non-union: a listing that would be union-only is offered non-union instead to anyone under three union credits (25% of the time), paying a third as much and easier to land. It is how a career starts, not a reward.

## 4.1 Attributes (0–100, slow-moving)

Replaces the single Acting bar. Each is raised differently, so builds diverge.

| Attribute | What it does | How it grows | Decay |
|---|---|---|---|
| **Craft** | Technique. Raises the floor of every performance and *reduces variance*. | Coaching, theatre work, repetition, working with great directors | none |
| **Instinct** | Raw talent. Raises the ceiling; source of transcendent takes. | Barely trainable (+1/yr max). Mostly innate. | none |
| **Presence** | How the camera reads you. Drives audience scores and star power. | Screen work, on-camera hours, some innate | −0.5/yr after 55 |
| **Voice** | Range, control, accent work. Gates certain roles entirely. | Dialect coach, voice work, theatre, animation gigs | −1/yr after 60 |
| **Physicality** | Movement, stunts, dance, combat. Gates action & period work. | Training, stunt work | −2/yr after 45 |
| **Look** | Conventional attractiveness. Aggressively curve-based (see 4.9). | Genetics, upkeep, surgery | curve |
| **Resilience** | Professionalism *and* buffer. Cuts bad on-set events, makes prep go further, and absorbs pressure and bad press. | Therapy, stable relationships, time off, choices under pressure | — |

**Four of these drive performance. Three of them decide what you're allowed to play.**

| | Attributes |
|---|---|
| **Core** — how good you are | Craft, Instinct, Presence, Resilience |
| **Gates** — what roles are open to you | Look, Voice, Physicality |

### Each attribute owns a verb, not a coefficient

A stat that only multiplies an outcome is a number. These each change *what you can do*:

| Attribute | Its verb |
|---|---|
| **Craft** | Sets your **contrast budget** (§5.5) — how many positions you can hold against the film before the performance stops holding together |
| **Instinct** | Lets you **re-set your palette mid-shoot** when the film changes underneath you: a rewrite, a new director, a co-star who gives you nothing |
| **Presence** | Your **Notices floor** = 0.42 × Presence *(v9 — was 0.10; at that weight the floor could never bind against a Notices mean of 58, so the verb never actually fired for anyone. At 0.42 it does: a magnetic actor genuinely can be still and be noticed for it.)*. At 90 you can hold the screen doing nothing. At 30 you must take positions to exist at all. |
| **Resilience** | How long a shoot before `Condition` erodes — and some forgiveness when you overspend your contrast budget |

The Presence one produces two genuinely different careers. **A magnetic actor can afford to be still. An unmagnetic one has to be interesting.** Neither is better and they play nothing alike.

### The gates open creative range, not just doors

They never appear in the performance roll (§4.7) — but they aren't a separate checklist either. Each governs how far a dial can travel:

| Gate | What it opens |
|---|---|
| **Voice** | Your range on **Volume** — how far you can go either way and still be heard doing it |
| **Physicality** | Your range on **Energy** and **Speed** |
| **Look** | What your *neutral* reads as. High: your "with" plays as charming. Low: it plays as ordinary, which is to say real. Different archetypes, neither strictly better. |

So improving your Voice doesn't make you a better actor — it widens the space of ideas you can execute. And when sound arrives (§10.6), that stops being a small difference.

*v3 had eight attributes including Discipline, which only ever modified prep and on-set rolls. Folded into Resilience.*

**Design intent:** a high-Craft/low-Instinct actor is *reliable* — narrow outcome band, works forever, rarely transcendent. A high-Instinct/low-Craft actor is a lottery ticket — occasional 95s, frequent 40s, and directors learn to fear them. Both are viable careers with different shapes.

## 4.2 The Persona (the typecasting engine)

This is the headline system. Rather than "you're a good actor," the game tracks **what the industry thinks you are.**

**Persona = two vectors plus a scalar.**

```
GenreAffinity  = { drama, comedy, action, horror, thriller,
                   romance, scifi, period, musical, family }   each 0–100
ArchetypeAffinity = { leading_hero, romantic_lead, villain,
                      everyman, character_actor, ingenue,
                      authority, comic_relief, wildcard }      each 0–100
Legibility = 0–100   // how sharply defined you are
```

**Update rule after each project:**

```
For the project's genre g and your role's archetype a:
    GenreAffinity[g]     += 6 × billingWeight × receptionFactor
    ArchetypeAffinity[a] += 6 × billingWeight × receptionFactor
    all others           -= 0.8 × billingWeight        (slow bleed)

receptionFactor = clamp(0.4 + (AudienceScore / 100), 0.4, 1.6)
billingWeight   = { lead 1.0, supporting 0.55, bit 0.2, extra 0.0 }

Legibility = normalized concentration of the two vectors
           = 100 × (max(v) − mean(v)) / max(v)      averaged across both
```

**Why Legibility matters — the central tension:**

| Legibility | Effect |
|---|---|
| **Low (0–35)** | Few offers. Casting directors "don't know what to do with you." But no ceiling — any role is castable. |
| **Mid (36–70)** | Healthy offer volume across two or three lanes. The sweet spot. |
| **High (71–100)** | Flood of offers *in your lane*, at a premium quote. But **strongly reduced offer probability outside it**, and critics apply a staleness penalty for repetition. |

**Breaking type.** You can take a role that fights your Persona. It carries:
- an audition penalty (see 4.4)
- a **Fit** penalty in the performance roll *(v9 — Fit is how well you read for the part on paper: age, genre, archetype, the hard gates. It's not how well you act it — that's Performance, §4.7. A role can fit you badly and still be the best work of your career.)*
- but on success: a large **Prestige** bonus, a Legibility reset toward the middle, and an award-narrative flag (`transformation`)

This is the actual dramatic arc of most real careers, and BitLife has no version of it.

**Staleness.** Track `consecutiveSameLane`. Critic score penalty of `−2 × (consecutiveSameLane − 2)`, floored at −12. Audience score is *unaffected* — the public likes what it likes. This is a deliberate wedge between the two reception numbers.

## 4.3 Standing (replaces "Fame")

Four meters, each doing a different job. Different gatekeepers weight them differently — that's the whole point.

| Meter | Range | Meaning | Baseline decay/yr |
|---|---|---|---|
| **Heat** | 0–100 | Current market demand. "Who's hot right now." | proportional, billing-aware — see below |
| **Prestige** | 0–100 | Industry respect. Directors and critics. | ×0.985 (very sticky) |
| **Affection** | 0–100 | Public warmth. Drives audience turnout & endorsements. | ×0.96 |
| **Notoriety** | 0–100 | Scandal heat. Sometimes an asset. | ×0.84 |

**These decay on their own, and there is no maintenance button.** BitLife wants you to post on social media every year or watch your fame drain — a chore, not a decision (§0.1). Here Heat falls because the industry moves on. The only thing that raises it is work, and choosing work is the game.

**v9 — the ladder had no bottom rung, and phase 0's end-to-end simulation caught it before a single line of interface got built.** The original spec here made gains billing-weighted (`bw`: lead 1.0, supporting 0.55, bit 0.2) and decay flat and identical at every tier — a beginner therefore accrued Heat at a fifth the rate a lead does, while paying full decay regardless. Run 4,000 careers against that and 80% never play a lead and nobody ever becomes a star; see `callback-design-review.md` §1. Four changes fix it, all load-bearing, and all four have to move together — they were swept and re-verified as a set, not tuned individually:

```
ΔHeat = bw · discovery(credits) · reach(budget) ·
        ( heatBase                                        // 7.9 — working at all is worth something
          + heatRoiCoef · clamp(ROI − heatRoiCentre, −0.6, 2.2)   // 9.0, centred at 0.90 — below the median outcome
          + heatAudCoef · (Audience − heatAudCentre) )     // 0.20, centred at 52

Heat *= heatKeep[billing this year]     // proportional decay, so it finds an equilibrium instead of
                                         // integrating to zero: idle 0.80, bit 0.865, supporting 0.888, lead 0.925 —
                                         // the tier you can reach has to be able to outrun the decay on that tier

discovery(credits) = up to 2.4× across your first 9 credits, tapering to 1× — a new face is news;
                     a known quantity is not

reach(budget) = clamp(0.46 + 0.50 · log10(budget), 0.3, 1.7)   // a hit on a $4M film and a hit on a
                     // $140M film are the same ROI and nothing like the same career event — this is
                     // where the upper tail comes from, and why it is rare

Recognition — the bridge out of bit parts, and deliberately NOT Standing:
  ΔRecognition = 0.42 · max(0, YourNotices − 51)     // good work in a small part, remembered
  Recognition *= 0.90/yr, faster once Standing clears 45 (it has done its job by then)
  feeds Utility (§4.4) only for supporting/bit roles — a way in, not a way up
```

`ΔPrestige` and `ΔAffection` keep the same billing-and-discovery structure (`ΔPrestige = bw·discovery·(0.11·(FilmCritic−57) + 0.26·(YourNotices−54))`; `ΔAffection = bw·discovery·reach·0.10·(Audience−55)`) — only Heat needed the `reach` term, since Prestige and Affection aren't primarily about how many people saw you.

**Derived values:**

```
StarPower  = 0.45·Heat + 0.30·Affection + 0.25·Prestige
Standing   = clamp(StarPower − 0.20·max(0, Notoriety − 55), 0, 100)   // StarPower net of scandal —
             the scalar Parts 6 and 8 gate on, defined once, here, so it can't drift
Bankability = 0.60·Heat + 0.25·(recent box-office ROI, normalized)
            + 0.15·Affection − 0.20·max(0, Notoriety − 55)

Quote (your asking price, in $M) =
    0.05 · exp(0.070 · Bankability) · eraMultiplier
```

That quote curve is deliberately exponential — the top of the market pays wildly more than the middle, which is true, and which makes the climb feel like a climb.

*(This section describes one Standing — the single-region form the actor spine was built and verified against. §10.5's fuller design tracks all four meters per region, with a `globalBleed` coefficient governing how much of one region's Standing carries into another; Part 12's schema shows the shape of it. Nothing here contradicts that — it's the same four numbers and the same formulas, just not yet split by region. If regions are ever built, this is the section that gains a subscript, not one that gets replaced.)*

**Gatekeeper weightings** (used in 4.4):

| Gatekeeper | Heat | Prestige | Affection | Notoriety |
|---|---|---|---|---|
| Studio tentpole | **0.55** | 0.05 | 0.30 | −0.40 |
| Prestige auteur | 0.10 | **0.65** | 0.05 | +0.05 |
| Indie / first-timer | 0.15 | 0.40 | 0.10 | 0.00 |
| Streamer volume play | 0.35 | 0.15 | 0.30 | +0.15 |
| Network TV | 0.30 | 0.10 | **0.45** | −0.55 |
| Franchise reboot | 0.45 | 0.10 | 0.35 | −0.30 |

Note that a prestige auteur *slightly rewards* notoriety and network TV punishes it severely. A scandal doesn't end your career — it **reroutes** it. That is a far better game than a single reputation bar.

## 4.4 The Offer Board & casting

Each quarter, generate role listings from active productions in the world sim, at a rate that rises with Standing and your agent's reach and falls hard with age past the mid-40s (§4.9) — offers are lumpy on purpose: some quarters nothing at all comes in, and that has to be possible or the calendar has no downside. This board was always a filtered slice of something bigger, never the whole industry — §10.0 specifies the much larger set of productions moving through the pipeline underneath it, most of which you'll never see a listing for at all.

**Offer probability** for role *r* from gatekeeper *G*:

```
StandingScore = Σ (G.weight[m] × Standing[m])          // per 4.3 table

FitScore = 100                                          // how well you match the part on paper
         − ageMismatchPenalty(|charAge − yourAge|)      // see below
         − 0.45 × (100 − GenreAffinity[r.genre])        × r.typeStrictness
         − 0.45 × (100 − ArchetypeAffinity[r.archetype]) × r.typeStrictness
         − hardGatePenalty(Voice, Physicality, Look vs r.requirements)

ageMismatchPenalty(d) = 0 if d ≤ 4
                      = 2.2 × (d − 4)^1.35     capped at 70
                      (asymmetric: playing younger costs 1.6× more than older)

RelationshipBonus = Σ over Rolodex members attached to this production:
                    0.30 × affinity − 0.55 × grudge

Utility = 0.40·StandingScore + 0.35·FitScore
        + 0.15·(0.6·Craft + 0.4·Instinct)
        + RelationshipBonus
        − 12 × min(Quote / r.budgetForRole − 1, 1)⁺     // you're too expensive — v9: capped,
                                                          // because an actor who wants a part takes
                                                          // less for it; uncapped, this term priced
                                                          // working actors off the board entirely
                                                          // the moment their quote moved

P(offer) = 1 / (1 + e^(−0.11 · (Utility − r.difficulty)))
```

**Three paths to a role**, and the game should make you feel the difference:

1. **Open audition** — full RNG, low utility floor, always available. This is the grind.
2. **Offer** — no audition; triggered when `Utility − difficulty > 14`. *(v9 — originally 25, which required a relationship bonus to ever clear and made this path and path 3 the same path in practice; phase 0's simulation flagged it as unreachable. At 14, a star who is obvious casting for a small film gets it outright, and the Rolodex path below stays genuinely distinct.)*
3. **Direct offer via Rolodex** — a director who trusts you (`affinity > 70`) hands you the part regardless of Standing. **The single most valuable asset in the game.** It bypasses the casting system entirely, which is exactly how the relationship graph earns its keep.

**Auditions are not a slot machine.** You bring a performance palette into the room (§5.5) — *play the anger / play the grief under the anger / play it flat and let them come to you* — and then choose whether to take the adjustment they give you. The room has visible preferences you learn by working with these people, and the casting director's own taste decides whether your contrast reads as bold or as wrong. This converts "another layer of luck" into a decision you can reason about.

**The union catch-22, made passable.** §10.1 locks an actor out of union productions until they have three union credits, and never specifies how the first three happen — a closed loop with no entry point. v9: non-union listings appear on the board of anyone under three union credits (a union role has a 25% chance of being offered non-union to a newcomer instead, paying roughly a third as much and pulling easier). It is a worse deal every time, and it is how a career starts.

**Typecasting, on the offer side.** The board itself is shaped by Persona (§4.2): roughly a fifth of the time a listing is drawn "in your lane" — weighted toward the genre and archetype you're already legible as — and the rest of the time from whatever the market currently wants. A highly legible actor's board fills with more of the same; an illegible one keeps seeing a genuinely varied mix. This is the offer-side half of typecasting the original spec never modelled at all — Persona existed but never touched what you were actually shown.

## 4.5 The Deal

The negotiation layer BitLife gestures at with its agent and then drops. Every offer exposes:

| Term | Effect |
|---|---|
| **Fee** | Cash now. Anchored to Quote; agent negotiates ±25%. |
| **Backend points** | % of net or gross. Trade fee for upside. Gross points are the real prize and only high-Bankability actors get them. |
| **Billing** | Above/below title, credit order. Affects Persona weight, award eligibility, and ego events. |
| **Options** | Sequel/season options. Locks *future* calendar blocks — the trap. |
| **Pay-or-play** | You get paid even if the film collapses. |
| **Approvals** | Director approval, script approval, co-star approval. Prestige currency, unlocks at high Standing. |

**Agents.** Tiered, with real differences beyond commission:

| Tier | Commission | Effect |
|---|---|---|
| None | 0% | Open auditions only. Small roles. |
| Boutique | 10% | +1 offer/quarter, small negotiation bonus |
| Mid-tier | 12% | +2 offers, ±18% fee negotiation, some access |
| Powerhouse | 15% | +4 offers, ±25% fee, packaging (see below), buries small scandals |

**Packaging** is the powerhouse-only move: your agency also reps the director and the writer and bundles you into a project before it's cast. Mechanically it's a guaranteed offer once every N years with no audition — enormously strong, and it costs you 15% of everything forever. That's a real decision.

**v9 — tier has to be climbable, or it isn't a decision, it's a starting condition.** The original spec set agent tier once, at character creation, with nothing anywhere that ever moved it — which meant an actor who started with no representation had none for the entire game, and *nobody, ever, on any path,* could reach Powerhouse, making the packaging move above permanently unreachable content regardless of how well the game was played. Fixed with an explicit pull action (§6.6, "get work"): **Sign with a bigger agency**, available whenever there's a tier above your current one and Standing clears that tier's bar (0 / 28 / 60), costing exactly the higher commission the new tier already implies. One step at a time, player-initiated, never pushed.

## 4.6 Prep

**Pick one approach.** v3 made this a week-allocation puzzle across six options — an optimisation you solve once and then repeat twenty times. It's now a single choice, and each option costs something real.

| Prep option | Cost | Effect |
|---|---|---|
| **Table work / coach** | 2 wk | +Prep, +Craft (tiny, permanent) |
| **Research the world** | 3 wk | +Prep, large bonus if role is `biographical` or `period` |
| **Dialect** | 4 wk | Removes Voice hard-gate penalty; +Prep |
| **Physical transformation** | 6–12 wk | Removes Physicality/Look gate; **Health cost**, small permanent Resilience hit |
| **Live it** (method) | 8 wk | Big Prep and a `transformation` award flag; **Resilience −8**, relationship strain events, risk of on-set conflict |
| **Wing it** | 0 wk | Prep = 20. Instinct-heavy builds can genuinely survive this. |

```
Prep = clamp(base[choice] × (0.8 + 0.004 × Resilience), 0, 100)
```

You can also set a **default approach** your character reaches for, and only be asked when the role makes it interesting — a biopic where research matters, an accent you don't have. Most films shouldn't ask at all.

## 4.7 The Shoot, and the Performance roll

The shoot resolves as **three events**, drawn from a pool weighted by the production's `chaos` value (budget pressure, director temperament, location). Each adjusts Chemistry, Condition, Prep, Rolodex affinity, or Health.

*v3 specified 6–10 events per shoot. At one and a half films a year that's a dozen prompts annually, most of them flavour, and it turns every production into a clicking exercise. Three events that matter beat nine that don't — and each one can then carry real weight instead of being ±2 to a hidden number.*

Then:

```
Base = 0.28·Craft + 0.18·Instinct + 0.16·Presence
     + 0.16·Fit + 0.12·Prep + 0.10·Chemistry
     + 0.06·(DirectorCommand − 50)          // v9 — §7.3 called this an amendment to this
                                             // formula and never landed it here; every shoot has
                                             // a director, NPC or player, so it isn't optional and
                                             // belongs in the baseline, not a patch applied
                                             // elsewhere. §7.2 defines Command; §7.3 shows what a
                                             // Command-90 director is worth to a cast member who
                                             // never picks up a camera themselves.

DirectionMult = 0.86 + 0.0028 · DirectorSkill              // 0.86 – 1.14  — DirectorSkill itself
                                                            // is §7.3's formula; a role's director
                                                            // is always a real character, NPC or
                                                            // player, never a bare parameter
ConditionMult = 0.80 + 0.0020 · Condition                  // 0.80 – 1.00 — Condition is §11.1's
                                                            // formula (health, burnout debt,
                                                            // substance load, Resilience)

σ = 16 − 0.09 · Craft                                       // craft = consistency
Roll = Normal(0, σ)

Performance = clamp( Base · DirectionMult · ConditionMult + Roll , 0, 100 )

// Transcendence: the reason Instinct exists
if random() < Instinct / 320:
    Performance += Uniform(9, 26)                          // "something happened
                                                            //  in take 14"
```

**Performance is private.** You see a qualitative read from the director, and your own uncertain sense of it. You do not see the number. This matters enormously for how the awards season plays — you should be able to walk away from a shoot convinced you were brilliant and be wrong.

**v9 — your own read of the room is itself a modelled estimate, not the truth.** Hidden Performance existed from the start; what was missing was a separately-tracked *estimate* of it, the pattern sports-management sims that do this well share (Football Manager's judging attributes, Total Extreme Wrestling's scouting levels — both rise only while you're actually doing the thing being judged, never passively). The read you're given narrows — states its own confidence, in words — as Craft rises and as you work with a given director again; a veteran with a trusted collaborator reads the room accurately, a newcomer on a first job with a stranger genuinely cannot tell.

*(`Base`'s `Fit` term and `Performance` itself feed directly into §5.6's shape — that section defines the single reconciled Notices/Ensemble split this Performance number resolves into; see the note there. §14.9's whole-career simulation is what caught the original spec's Standing formula failing to convert any of this into a career at all — see §4.3.)*

## 4.8 The Calendar — opportunity cost

The year is **4 quarters**; each project consumes a contiguous block:

| Project type | Blocks |
|---|---|
| Indie feature | 1 |
| Studio feature | 2 |
| Tentpole / franchise | 3 (plus 1 reshoot block, 35% chance) |
| TV season (network) | 3 |
| TV season (streaming, 8–10 ep) | 2 |
| Limited series | 2 |
| Theatre run | 2 |
| Voice work / cameo | 0.5 |
| Awards campaign | 1 (see 4.11) |
| Rest / recovery | 1 |

Offers arrive with **shoot windows**. Two great scripts overlapping in Q2–Q3 is the most common and most interesting decision in the game. This one change — a schedule instead of a role-per-year — creates more meaningful choice than every other addition combined.

**Burnout:** working 4/4 blocks for consecutive years drives `Condition` down and triggers a burnout arc. Rest blocks cost you Heat (−6). The tension is permanent and unresolvable, which is correct.

## 4.9 The Body & the ageism curve

`Look` follows a curve modified by upkeep, and — critically — **role availability is a separate curve from Look.**

```
LookCurve(age) = peaks 22–32, −0.9/yr to 45, −1.6/yr to 60, −2.2/yr after
Upkeep (gym, diet, dermatology, surgery) shifts the curve up but
  surgery carries a Presence risk: 12% chance of −6 Presence permanently
  ("something's off about the face now")
```

**Role Volume by age** — this is the honest part of the design and should be surfaced to the player as an in-fiction chart the *agent* shows them:

| Age band | Ingenue/romantic lead offers | Character/authority offers | Lead offers overall |
|---|---|---|---|
| 18–27 | ●●●●● | ○ | ●●● |
| 28–38 | ●●●● | ●● | ●●●●● |
| 39–48 | ●● | ●●●● | ●●●● |
| 49–60 | ○ | ●●●●● | ●●● |
| 61+ | — | ●●●● | ●● |

The design response is not to remove the cliff, it's to make **the transition a playable arc**: pivoting Archetype from `ingenue` toward `character_actor` or `authority` before the cliff arrives is one of the game's real strategic problems. Players who don't plan for it hit 42 and watch the board go empty. Players who spent their thirties banking Prestige and building a Rolodex land the late-career renaissance.

**Injury.** Stunt work rolls against Physicality; failures cost Health and can permanently cap Physicality, which retroactively closes an entire lane of roles. Stunt doubles are available and cost Prestige with certain directors.

## 4.10 Reception — the decoupling

This is the mechanical heart of the redesign. **Four separate numbers**, computed from overlapping but non-identical inputs.

The critical structural move — and the thing that makes the whole design work — is that **the film gets reviewed and you get reviewed separately.** BitLife has one number. Callback has `FilmCriticScore` (was the movie good) and **Notices** — `YourNotices` in the formulas below, fully defined in §5.6 — (were *you* good in it). Prestige and awards read Notices; Heat and money read the box office; the two only partly agree. Everything downstream depends on this split.

**v9 — Part 5 defined `YourNotices` and `EnsembleScore` again, differently, and the two were never reconciled; each was "verified" in isolation against a different definition of itself.** There is now exactly one of each, produced by §5.6's shape resolution and consumed here as `yourNotices`/`ensembleScore` — this section cannot drift from Part 5 again because there is only one code path between them. The reception sweep below was re-run against the unified definition.

```
EnsembleScore = ( YourPerformanceShape · yourBillingWeight
                 + Σ restOfCast(billing-weighted) )
               / (yourBillingWeight + Σ restOfCastWeights)
              // v9: the doc's flat "≈0.80·yours + 0.20·rest" is wrong for a real cast and was
              // never checked against one — a lead actually carries about 0.56 of it, a bit
              // player about 0.09. Modelled per-billing now, not as one constant for every part.

ProjectQuality = 0.31·ScriptQuality
               + 0.22·DirectorSkill
               + 0.29·EnsembleScore
               + 0.08·ProductionValue(budget)
               + 0.10·PostLuck ~ N(52, 14)          // the edit

FilmCriticScore = ProjectQuality
                + genreBias[g]                      // drama +4, horror −5,
                                                    // comedy −4, action −3
                + 0.10·(DirectorPrestige − 50)      // auteur halo
                − stalenessPenalty                  // your repetition, 4.2
                − clicheePenalty                    // v9 — §5.4's landmarks: the shape you
                                                    // invented eventually reads as tired to
                                                    // critics too, once enough films copy it
                + palette effect(genre)             // §5.3, scaled — see note there
                + N(0, 4.6)

YourNotices     = 0.52·YourPerformanceShape
                + 0.25·FilmCriticScore
                + 0.13·(50 + 30·billingWeight)      // visibility: you can't be
                                                    // praised for what nobody saw
                + N(0, 7)

AudienceScore   = 0.62·ProjectQuality
                + 0.17·GenreDemand[g, era]
                + 0.11·CastStarPower
                + 0.06·(100 − ProjectQuality)       // anti-elitism term:
                                                    // difficult films
                                                    // underperform with crowds
                + palette effect(genre)
                + N(0, 4.5)
```

**Box office — v9: one model, not two.** The original spec carried this shape here *and* a differently-structured one in §8.2 for the studio layer, never reconciled — two box-office models computing different numbers for the same release, down to different opening-weekend coefficients (0.92 here, 0.80 there) and one carrying a `GenreDemand` nudge on legs the other didn't. This is now the only one; §8.2 reads it rather than restating it, and this version keeps the better piece of each — the actor-side derivation discipline below, and the studio-side model's named `Zeitgeist` term for what legs actually measure:

```
Budget      = role.budget / eraMultiplier            // v9 — derived at resolution time, never
                                                       // stored: three paths (a non-union
                                                       // downgrade, an unknown-lead franchise
                                                       // ticket, a franchise installment) rewrite
                                                       // the nominal budget after a role is
                                                       // generated, and a value snapshotted at
                                                       // generation was quietly scoring a
                                                       // different film from the one on the offer
                                                       // board — in both directions
BreakEven   = Budget × (1 + 0.45) / 0.62              // marketing share, and the rights share
                                                       // that ever comes back — the figure a
                                                       // player is shown so ROI reads as more
                                                       // than a bare ratio
Opening     = Budget × (0.92 + 0.005·CastStarPower + 0.005·GenreDemand) × (Budget/30)^−0.10
Zeitgeist   = AudienceScore + 0.5·(GenreDemand − 50) + N(0, 12)     // "did it catch on" — legs
                                                                     // measure something partly
                                                                     // outside the film itself, and
                                                                     // naming it is what makes the
                                                                     // fat tail in §8.2's slate
                                                                     // outcomes legible instead of
                                                                     // asserted
Legs        = clamp(1.7 + 0.048·(AudienceScore − 50)
                     + 0.032·max(0, Zeitgeist − 70)^1.5, 1.15, 8.0)
Gross       = Opening × Legs
ROI         = (0.62 × Gross) / (Budget + Marketing)
```

**And now the payoff — your Standing gains are computed from these, per §4.3's corrected formula.** (The original draft of this section duplicated the Standing math here, with the pre-fix constants — see §4.3 for the one live definition and why the version that used to live here was wrong.)

**These constants are tuned, not guessed.** Running 40,000 project resolutions against them yields:

| Output | Mean | SD |
|---|---|---|
| Performance | 63.6 | 14.6 |
| FilmCriticScore | 58.1 | 9.7 |
| YourNotices | 58.0 | 11.5 |
| AudienceScore | 55.0 | 7.6 |
| ROI | median 0.97 | 46% of films profitable |

| Correlation | Value | Reading |
|---|---|---|
| Performance ↔ YourNotices | **0.76** | Your work mostly determines how *you're* reviewed. Agency preserved. |
| Performance ↔ FilmCriticScore | **0.42** | You're one input of several into whether the film is good. |
| Performance ↔ ROI | **0.23** | Your performance barely moves the box office. |
| FilmCriticScore ↔ ROI | **0.30** | Good films make somewhat more money. Somewhat. |
| FilmCriticScore ↔ AudienceScore | **0.39** | Critics and crowds agree less than half the time. |

**Read what that produces:**

- A **flop with great reviews and a great performance** → Prestige way up, Heat down. You become "an actor's actor" — the auteur board opens, the tentpole board closes.
- A **hit you were bad in** → Heat and Affection up, Prestige flat or down. Your quote soars and critics stop taking you seriously.
- A **great performance in a film ruined in post** (`PostLuck` rolls 18) → `YourNotices` weights `YourPerformanceShape` at 0.52 against `FilmCriticScore` at 0.25, so most of your Notices — and therefore most of your Prestige gain, since Prestige reads Notices, not the film's score directly — survives a wrecked edit. The industry knows. The public never finds out.

That last case is *precisely* the thing BitLife cannot express, and it's the emotional core of the whole design.

## 4.11 Awards as a campaign

Not a die roll at the end of the year — a **strategic mini-season occupying one calendar block.**

```
BuzzScore = 0.34·YourNotices     + 0.20·FilmCriticScore
          + 0.14·CampaignSpend   + 0.12·Prestige
          + 0.10·NarrativeBonus  + 0.10·CategoryAdvantage
          + N(0, 9)
```

Note it reads `YourNotices`, not `YourPerformance`. **Awards do not reward being good; they reward being *seen* to be good.** A brilliant turn in a film nobody reviewed scores badly here — which is both true and a good reason to care about release strategy.

**NarrativeBonus** — the campaign fictions that actually decide awards:

| Narrative | Bonus | Trigger |
|---|---|---|
| *"She's due"* | +14 | 3+ prior nominations, zero wins |
| *"The transformation"* | +12 | physical transformation or method prep flag |
| *"The comeback"* | +11 | Heat was < 25 for 4+ consecutive years |
| *"The final bow"* | +10 | age 70+, or announced retirement |
| *"The newcomer"* | +8 | first-ever nomination, age < 28 |
| *"They were overdue and now they're dead"* | +20 | posthumous |
| *"Too commercial"* | −10 | 2+ tentpoles in the last 3 years |
| *"Overexposed"* | −7 | 4+ credits released this season |

**CategoryAdvantage — category fraud, playable.** A lead performance can be campaigned in Supporting. It's a weaker field, so `CategoryAdvantage +18`, but it carries a `Notoriety +6` risk if the press calls it out (35% chance, scaling with your Notoriety). This is a genuinely real industry practice and it makes a great decision.

**Vote splitting:** if two performances from the same film are nominated in one category, both take −9. Studios lobby you to switch categories. Sometimes you should refuse.

**Campaign cost:** money and a calendar block. A serious campaign runs $400K–$3M of your own money if the studio won't fund it, and you spend a quarter at luncheons instead of working — which costs a role. Prestige actors who campaign relentlessly are making a real trade.

## 4.12 The Rolodex

**Eight named people you actually track**, drawn from a wider background cast of ~40 who exist, age, and have their own careers, but who only surface when they intersect with yours.

*v3 asked you to hold forty relationships in your head. You can't, and trying turns the Rolodex into a chore list. The eight are chosen dynamically — whoever you've worked with most, plus anyone currently holding a grudge or owing a favour. The rest are real but quiet.*

| Type | Count | What they track | What they do |
|---|---|---|---|
| **Directors** | 10 | Skill, Prestige, temperament, genre lane, *loyalty roster* | Direct offers; DirectionMult; auteur halo |
| **Casting directors** | 6 | Preference profile, memory of every audition | Gate the offer board; readable preferences |
| **Producers/studio heads** | 5 | Risk appetite, budget authority, grudges | Greenlight, blacklist, franchise access |
| **Agents/managers** | 5 | Tier, client roster, hustle | Offer volume, negotiation, scandal burial |
| **Co-stars/rivals** | 10 | Full attribute sets, own careers, ego | Chemistry, ensemble score, award competition |
| **Critics/press** | 4 | Taste vector, grudges | CriticScore noise skew, scandal amplification |

**Each edge stores `affinity (−100..100)`, `grudge`, `sharedProjects`, and `lastContact`.**

**The loyalty roster is the key mechanic.** Directors keep a stable of actors they cast repeatedly. Getting onto a great director's roster (`affinity > 70`, achieved through 2+ good collaborations) means recurring direct offers on prestige projects for the rest of their career. This is how real careers actually work — Scorsese/De Niro, Anderson/Murray, Burton/Depp — and it's an enormous, earnable, losable asset.

**NPCs have their own arcs.** Directors decline. Your rival wins the award you wanted and then flames out. The producer who blacklisted you at 30 gets fired at 45 and the door reopens. The world should feel like it's running whether or not you're in it — §10.0 is the mechanism, not just the promise: NPCs' Standing, Skill, and Signature move because of films they made that you were never in, computed by the same formulas as your own career.

*(v9 — `affinity`, `grudge`, `sharedProjects`, and `lastContact` above are the raw fields; §10.0 builds the rest of the system on top of them — hidden Agendas, named relationship states, pull actions that build a relationship rather than spend one, and what losing someone actually costs.)*

## 4.13 Scandal & press

Notoriety is generated by on-set behavior, relationships, substance arcs, political statements, and rival leaks. **Crucially it is not purely negative** — see the gatekeeper table in 4.3.

**Scandal resolution mini-game** — four postures, each with a payoff profile:

| Posture | Notoriety | Affection | Prestige | Risk |
|---|---|---|---|---|
| **Deny** | −5 | +3 | 0 | If evidence surfaces later: ×2.5 blowback |
| **Apologize** | −14 | −6 | +2 | Signals guilt; opens follow-up stories |
| **Silence** | −2/yr slow bleed | −10 | +4 | Story runs unopposed for 2 quarters |
| **Lean in** | +12 | +8 or −18 (splits on Affection) | −5 | High variance; can *create* a persona |

"Lean in" splitting the audience is the interesting one — it can convert a scandal into a brand.

## 4.14 Era and life — see Parts 10 and 11

v3 carried summary stubs here for the era system and the life layer. Parts 10 and 11 replaced them
entirely, and two half-descriptions of one system is worse than one description. They're gone —
this section is a pointer, not a summary: §10.6 for eras, §11 for the life layer, and neither of
those sections has anything left here to sketch or reconcile against.

---

