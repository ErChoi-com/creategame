# PART 10 — THE WORLD

The industry is a character. It has institutions, geography, and technology, and all three change underneath you.

## 10.1 Guilds and unions

Union status is one of the most mechanically fertile and least-simulated facts about acting as a job.

| System | Mechanic |
|---|---|
| **Eligibility** | Join after 3 credited union jobs or a qualifying earnings threshold. Before that you're locked out of all union productions — which is most of them. |
| **Scale minimum** | A hard floor on pay. Protects new actors; also means low-Standing actors *can* survive. |
| **Residuals** | Back-end income from reruns, home video, and streaming. Formula changes by era (§10.6). **For a working actor, residuals are the difference between a career and a hobby.** |
| **Health plan** | Requires earnings above a threshold *each year* (say $28K in current-era dollars). |
| **Pension** | Vests over 10 qualifying years; pays from 65. |

### The health-plan cliff

This deserves its own callout because it's the truest thing in the entire design.

> A journeyman actor at 51 has $19K of qualifying earnings this year. The threshold is $28K. They have one quarter left and two offers: a two-block prestige indie paying scale ($6K), or a commercial paying $14K. Taking the commercial gets them insured for a year and costs them the role that might have relaunched them.

That is a *real decision that real actors make constantly*, it requires no fantasy, and it emerges from three numbers. No game has ever modeled it. It should be in this one.

## 10.2 Strikes

Every era generates grievances (residual formulas eroding, streaming transparency, AI likeness rights — §10.6). When accumulated grievance crosses a threshold, the guild strikes.

```
Strike duration: 1–4 quarters. ALL union production freezes.
```

**Player choices as talent:**

| Choice | Money | Rolodex | Long-term |
|---|---|---|---|
| **Hold the line** | Zero income for the duration | +8 affinity across all union NPCs | Solidarity credit; a `held_the_line` flag that some directors weight heavily forever |
| **Interim agreement / indie waiver** | Small income | Neutral | Legitimate, unglamorous |
| **Cross** | Full income, and the offers are unusually good | **−40 affinity across the entire graph**; 20% of NPCs set `grudge = permanent` | Some doors never reopen. Not most. Some. |

**As a studio:** negotiate early (costs margin forever), wait it out (costs a year of slate), or shift production abroad (works, and generates the *next* grievance).

Strikes should be genuinely painful and should hit at the worst possible time, because they do. A player mid-awards-campaign when the strike lands — press blocked, campaign frozen — is a story they'll remember.

## 10.3 Festivals

Festivals are the alternate distribution economy and the primary way small films become real.

| Festival | Taste profile | What winning gives you |
|---|---|---|
| **Riviera** (Cannes-like) | Auteur, international, formally daring, hostile to sentiment | Prestige ++, a global distribution auction, an instant Signature |
| **Alpine** (Sundance-like) | American indie, personal, discovery-hungry | The acquisition market; where careers *start* |
| **Lagoon** (Venice-like) | Prestige, awards-season launchpad | Awards momentum: `NarrativeBonus` seeded early |
| **Northern** (TIFF-like) | Audience-facing; its audience award predicts box office | An `AudienceScore` forecast before you're locked in |
| **Midnight** (genre) | Horror, transgressive, cult | Cult status, Notoriety +, a devoted permanent fanbase |

**The flow:** submit → selection (competitive, weighted by your Signature's fit to that festival's taste) → premiere → **all reviews land at once** (a single enormous `FilmCriticScore` reveal, which is terrifying and great) → acquisition auction if the film is unsold.

```
P(acquired) = sigmoid(0.08·(FilmCriticScore − 55) + 0.05·(CastStarPower − 40)
                      + festivalTierBonus + audienceAwardBonus)
```

**Unsold films return ROI = 0.** This is the distribution gate that corrects the micro-budget tier in §8.2 from 80% profitable down to a realistic ~56%, and it does it *diegetically* — the film didn't lose money, it just never came out. Every player who has a beautiful little film die in a festival market will understand the industry better for it.

## 10.4 The territory market

Twice a year, a film market opens. Sell distribution rights territory by territory before you shoot.

**Five blocs, not twelve territories.** v3 had a dozen, which is optimisation busywork with one right answer per film. Five is enough to make the interesting thing happen and few enough to hold in your head: North America, Europe, East Asia, Latin America, and the rest of the world.

Each bloc carries its own `GenreDemand` vector and its own **star affinity**, which creates one of the design's best emergent career states:

> **You are enormous in one territory and nobody anywhere else.** Your Quote in Hollywood is $400K. Your Quote for a film that presells to East Asia is $4M, because your face closes that territory by itself.

Actors can deliberately build territory-specific Standing. It's a real strategy, a real career, and a real trap — territory heat evaporates fast when a local star rises.

## 10.5 International industries

Standing is tracked **per region** with a `globalBleed` coefficient. Region choice is a genuine strategic axis, not a flavour selector.

**Build four properly.** Hollywood, Bollywood, Korean serial TV and European art cinema cover the four genuinely distinct economies — biggest-market, star-system-extreme, serial-television, and subsidy-and-festival. The rest of the table below stays as places you can go and work, with their flavour and their gates, but without bespoke systems. Four built well beats eight sketched, and these four are the ones that *play* differently rather than the ones that sound different.

| Industry | Defining mechanics |
|---|---|
| **Hollywood** | Biggest budgets, hardest entry, global reach, highest ceiling |
| **Bollywood** | Musical numbers are a hard gate (Voice + Physicality); star system extreme — `Affection` weighted ~2× in every gatekeeper; family-audience content limits |
| **Korean film/TV** | Serial TV economy; intense fan management (a `fandom` sub-meter with its own volatility); mandatory military service interrupts male careers for 2 blocks — a real and brutal scheduling event |
| **Nollywood** | Enormous volume, ultra-fast schedules (0.5 blocks/film), tiny budgets; you can build a 40-film filmography in a decade and a fanbase that Hollywood can't see |
| **Telenovela** | Year-long serial contracts consuming *all four blocks*; enormous `Affection` gains, `Prestige` ceiling around 45 |
| **European art cinema** | Subsidy-funded, festival-routed, `Prestige`-dense, money-poor; the reliable path to critical immortality and a small apartment |
| **Hong Kong action** | `Physicality` dominant, injury probability ~3× baseline, own stunt-performer stardom track |
| **Voice / animation** | `Voice` only. **No `Look` gate and no age curve** — the one lane where the §4.9 cliff doesn't exist. A refuge, and the game should let players find it. |

```
CrossoverStanding(from A to B) = Standing_A × globalBleed[A][B]
// Hollywood → elsewhere ≈ 0.55        elsewhere → Hollywood ≈ 0.18–0.30
```

Making it in Hollywood after Bollywood stardom is a fresh climb *with a head start* — which is precisely, uncomfortably accurate.

## 10.6 Technology eras and obsolescence events

The era system sketched in §4.14, made structural. Each transition rewrites `GenreDemand`, the gatekeeper weight table, and **at least one rule of the game.**

| Shift | What it obsoletes | Mechanic |
|---|---|---|
| **Sound** | `Voice` becomes a hard gate overnight | Every established actor with Voice < 45 is career-ended in two years. The canonical obsolescence event. |
| **Color** | Faces are re-evaluated | `Look` re-rolled ±12; some careers made, some ended, for no reason anyone can articulate |
| **Television** | Theatrical vs. TV caste split | TV is first a career death, then, an era later, a career *refuge* — and the actors who took it early get vindicated |
| **New Wave** | Studio contracts collapse | Auteur power spikes; `Prestige` worth ~2×; budgets shrink; director becomes the strongest career in the game for one era |
| **Home video** | — | **Residuals are invented.** Back catalogue starts paying. Actors with deep filmographies get a passive income they didn't plan for. |
| **Digital** | Shooting cost collapses | Volume up ~40%; micro-budget tier explodes; DP craft shifts |
| **Streaming** | Theatrical grosses shrink | Backend points become nearly worthless; volume explodes; `Affection` rises in weight; the mid-budget tier is gutted |
| **Virtual production** | Location work | `Physicality` devalued; `chaos` drops; location tax-credit strategy dies |
| **Synthetic performers** | **You** | See below |

### The likeness economy

The last shift deserves its own system, because it's the one modern development that genuinely changes what it means to have a career.

```
License your likeness:  immediate payment ≈ 3.5 × current annual income
Thereafter:
    Synthetic performances appear in projects you did not choose.
    They generate Affection and Notoriety you do not control.
    Your Quote decays by 6%/yr (why hire you at scale when the license is cheap?)
    Your Persona drifts toward whatever the licensees cast you as.
    Revocation requires litigation: 2 blocks, large money, uncertain outcome.
```

An aging actor with declining offers and a mortgage is offered a very large check to stop being the author of their own image. That's not a gimmick — it's the age cliff (§4.9) and the going-broke ratchet (§11.6) arriving at the same time with a solution attached, and it should feel awful to accept and awful to refuse.

## 10.7 Censorship, codes, and blacklists

Some eras run a **content code**: certain themes cap `ScriptQuality`, certain genres are unavailable, and violating the code kills distribution outright. Working around a code — implication, subtext, the thing you can't show — grants a `craft_under_constraint` bonus to `FilmCriticScore` that a permissive era doesn't offer. Constraint makes better films, and the game should be able to demonstrate that rather than assert it.

**Blacklists.** In certain eras, a political affiliation (§11.5) or a public position flags you. Offers collapse to near zero across every mainstream gatekeeper. Available responses: work under a pseudonym at a fraction of your quote (a `front` NPC takes the credit and possibly the award), go abroad (§10.5), name others (money and career restored, `Rolodex` catastrophically and permanently damaged, and the obituary will say so), or wait — rehabilitation becomes possible after 8–15 years and carries a very large `NarrativeBonus`.

---

