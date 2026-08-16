# PART 10 — THE WORLD

The industry is a character. It has institutions, geography, and technology, and all three change underneath you.

## 10.0 The background industry — what's happening whether or not you're in it *(v9, new)*

Three things this document already promises and never actually builds the engine for:

- §9.3's genre-cycle formula reads `GenreHeat[g] += 30 for every film in g that returned ROI > 2.5` — which presumes a whole population of films is being resolved every quarter. Nothing before this section says where they come from if the player isn't in them.
- §4.12 states, as a design goal for the Rolodex: *"your rival wins the award you wanted and then flames out. The producer who blacklisted you at 30 gets fired at 45 and the door reopens."* That requires NPCs to have careers that run on their own, not scripted beats — §4.12 asserts it; this section is the mechanism.
- §5.17 tracks "the films you wanted to make," and §11.8's obituary promises to reveal "who took them, what they won" for every role you declined. Without this section, that line has nothing to compute — it's an assertion with no mechanism behind it.

This section is the mechanism. It's one idea: **a role you don't take isn't removed from the game. It's cast with someone else, and that film gets made.**

### The board is a slice, not the whole industry

§4.4 generates the roles that reach *your* board — filtered by your Standing, your Persona, your agent's reach. That was always a filter, not a generator. Underneath it, every quarter, the world is casting, shooting, and releasing far more films than any single actor ever sees a listing for: dozens of productions moving through the pipeline, of which your board shows you somewhere between 2 and 7 (§4.4's `reach`). Everything else on this section is about what happens to the rest of them.

### What happens to a role you don't take

You decline it, or the offer window closes, or your Persona and Standing never put it on your board in the first place. The production doesn't vanish:

```
CastingResolution(role, you-not-cast):
    candidate = weightedPick(Rolodex members ∪ generated background actors,
                              weight = Utility(candidate, role))   // §4.4's own formula,
                                                                    // run for someone else
    role.filledBy = candidate
```

No new casting math — the exact `Utility` formula from §4.4 runs again, with a different actor as the input. That's deliberate: the world doesn't get a simplified, fake version of casting for everyone who isn't the player. It gets the real one.

### The film still gets made, through the same formulas

The candidate who filled the role gets a real Performance (§4.7's formula, their Craft/Instinct/Presence/Fit/Prep/Chemistry standing in for yours), the film gets a real reception (§4.10 — `ProjectQuality`, `FilmCriticScore`, `AudienceScore`, box office, all of it), and it resolves to real Notices, a real ROI, real awards eligibility. Nothing about a background film is faked or abstracted at the level of the individual production — it is exactly as real as one of yours, computed the same way, and simply happened to someone else.

### Where it feeds back in

Every system that already reads an aggregate industry number was quietly depending on this existing:

| System | What background films feed it |
|---|---|
| **Genre cycles (§9.3)** | `GenreHeat` accumulates from every resolved film, yours and everyone else's — your own choices are a small perturbation on a self-sustaining cycle, not the cycle itself |
| **Landmarks (§5.4)** | An NPC director's own Craft + Vision can independently roll a landmark. Their invention enters the world's coherence set exactly like yours would, gets copied, and becomes a cliché you have to consciously avoid a decade later — a shape you never chose, that now shapes what "coherent" means for everyone shooting after it |
| **Awards (§4.11)** | Background films are entered into the same buzz/nomination pool yours are. A rival beating you for Best Supporting Actor is a real number losing to a real number, not a scripted outcome — which is the only way §4.12's "your rival wins the award you wanted" can be true instead of asserted |
| **Franchises (§6.4, §6.5, §9.5, §9.6)** | A property can run its entire installment curve off-screen — greenlit, cast, sequeled, rebooted-without-someone — and you find out from the trades, the same way a real actor finds out a franchise they auditioned for once became a five-picture deal for somebody else. Shared universes (§9.6) inherit this too: interlock, fatigue, and collapse can all happen to a universe you were never cast into. |

### NPCs have careers, not appearances

A director you haven't worked with in fifteen years has not been standing still. Their `DirectorSkill`, their Prestige, their Signature (§7.8) — all evolving off-screen from the films *they* made, the overwhelming majority of which you were never cast in, computed by the same formulas as your own career. When you finally work with them again, the person you're working with is not the person you remember; they're whoever fifteen years of a real, simulated career actually made them.

**Rivals** are this same mechanism given a name. Nothing new — §8.8 already runs 3–5 rival studios on the full simulation; a rival *actor or director* is the same idea one layer down, and doesn't need its own system either (§7.3 makes the director side explicit). A rival isn't declared at character creation. It's whichever Rolodex member (§4.12) the game has been quietly tracking because your careers keep intersecting — same category at the same ceremony twice, up for the same part three times, one franchise between you, or (for a director) the same financiers picking their slate over yours. The Rolodex already tracks the eight people who matter most by weighted contact, grudge, and stakes (§4.12); a rival simply falls out of that ranking on its own, the way it does in an actual career, rather than being assigned.

### Surfacing it: the trades

None of this is worth building if the player has to go looking through a production database to feel it. **The trades** are a once-a-year digest — pull, never pushed (§0.3 Rule 2b), always available, costing nothing against the decision budget — of what the background industry just did: which genre is hot and for how much longer, whose film everyone's discussing, a landmark getting copied, a rival's rise, a scandal, a retirement, a box-office record. Built and read in phase 0 as exactly this shape — five lines, once a year, entirely optional — and it's the cheapest, highest-return piece of this whole section: the world doesn't need the player to track it, it needs the player to be *able* to check in on it and find something has genuinely moved.

### This is what makes the declined-offer payoff real

§5.17 tracks the films you passed on. §11.8's obituary promises to show what became of them. Before this section, that promise had nothing behind it — a declined role was simply gone. Now it isn't: every declined or lost role enters exactly the pipeline above, gets cast, gets made, gets reviewed, and its outcome is sitting in the world's own history waiting for the obituary to read it back to you.

> You passed on a two-block indie at 26 because the dates conflicted with a franchise sequel that paid four times as much. The indie got made anyway, with someone else, on a schedule that worked for them. Five years later you are at home, not nominated, watching it win Best Picture. The sequel you took instead is fine. Nobody talks about it much. Both of those facts are computed, not written, and the obituary will put them next to each other without comment.

### Scope: simulated in full only where it will ever be seen

Full-detail simulation — a real Performance roll, a real reception, a tracked career — is worth running for the Rolodex's tracked members, rivals, franchise principals, and anyone the player has ever shared a set with. Nobody will ever ask what happened to the other four hundred background productions filled entirely by generated names in a given year, and running full formulas for all of them buys nothing: those resolve as an aggregate contribution to `GenreHeat`/`GenreDemand` only, per §9.3's existing math, exactly the way §9.3 already implies a population feeds it without ever specifying one. Same principle as §10.5's "four industries built well beats eight sketched" — detail goes where a player can actually walk into it.

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

*(v9 — this used to be introduced as "the era system sketched in §4.14," which no longer holds: §4.14 explicitly removed its own stub content in favour of this section, so it has nothing left to sketch. The dependency runs one way — this is the only place the era system lives.)* Each transition rewrites `GenreDemand`, the gatekeeper weight table, and **at least one rule of the game.**

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

