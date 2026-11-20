# PART 7 — THE DIRECTOR

A full parallel career, not an epilogue. You can start the game as a director, switch either direction, or run both at once. Actor and director share one world model — every formula below plugs into the equations in Part 4, from the other side of the camera.

## 7.1 The design argument: three inversions

Directing is worth building because it *inverts three things the actor cannot control.* That's what makes it a different game rather than a reskin.

| As an actor | As a director |
|---|---|
| `PostLuck ~ N(52, 14)` — a blind roll that can bury your best work | **The edit is a decision you make.** You roll it, and you can steer the mean. |
| Casting is a gate you try to pass | **You operate the gate.** You run the utility function in §4.4 from the other side. |
| Performance is something you produce | **Performance is something you elicit.** Your Command raises everyone's roll. |

Every actor who has been wrecked by a bad edit has a mechanical, in-fiction reason to want the chair. That's the pull, and the game should let players feel it arrive naturally rather than announcing it.

## 7.2 Director attributes (0–100)

| Attribute | What it does | What you'd actually hear *(v9)* |
|---|---|---|
| **Vision** | Originality and ambition. Sets the ceiling on `ProjectQuality` and drives Signature strength. High Vision + low Efficiency is the classic overreaching auteur. | "She has real ideas, even the ones that don't work." |
| **Command** | Leading actors and crew. **This is the single most important attribute** — it feeds `DirectionMult` and directly raises every cast member's Performance roll. | "Actors do their best work for him — everyone says so." |
| **Craft** | Blocking, coverage, camera, composition — how well you actually make the thing. Lowers `chaos`, raises `PostLuck`, feeds `FilmCriticScore` and festival fit. | "Every frame looks exactly like it's supposed to." |
| **Taste** | Script judgment. See below — this one is unusual. | "She can spot a good script from a stack of forty." |
| **Efficiency** | Schedule and budget adherence. Determines overage, which determines whether you keep final cut. | "Always over schedule. Always over budget." |

*v3 had seven. **TechCraft** and **Eye** did the same job under two names — merged into Craft. **Nerve** was barely referenced; holding your vision under pressure is what Vision means.*

*(v9 — like the actor's own core attributes, these five numbers are never shown to the player as raw 0–100 values; §15's rule for player-facing UI covers the director exactly as it covers the actor. The third column above is what that sounds like in practice — the same qualitative-read pattern §4.7 already uses for the actor's own hidden Performance, not a new UI element.)*

### Taste is information, not power

Every other attribute makes you better at something. **Taste makes you see clearly.** When you read a script, the game shows you an *estimate*:

```
PerceivedScriptQuality = TrueScriptQuality + N(0, 26 − 0.22·Taste)
```

At Taste 20 you're reading scripts through a fog of ±21. At Taste 95 your error band is ±5. A low-Taste director with excellent Command will shoot the hell out of a bad screenplay, over and over, and never understand why the reviews don't come. **That is a real and specific kind of career**, and it emerges from one line of noise.

Taste is also the hardest attribute to raise: +1/yr from watching films, reading, and — most effectively — *being wrong and finding out.*

## 7.3 DirectorSkill — the bridge to the actor model

Everything in Part 4 that reads `DirectorSkill` and `DirectorPrestige` now resolves against a real character, whether NPC or player. `DirectorPrestige` is not a parallel stat invented for this Part — it's the same `Prestige` meter from §4.3's shared Standing model, read for whoever is directing instead of whoever is acting. `DirectorStanding` (§7.4's `PackageStrength`, §8.1's stage thresholds) is the same composite `Standing` scalar, same formula, same source. One Standing model (§3.3's own rule) means literally one: nothing in this Part computes it a second way.

```
DirectorSkill = 0.34·Vision + 0.28·Command + 0.38·Craft
              + engagementModifier          // passion project +6, paycheck −8
              + N(0, 11)                    // this project, this year

// Merging two correlated attributes into one RAISES variance, so the project-noise
// term drops from 12 to 11 to hold the distribution steady.
// Verified: attributes ~ N(58,20) gives mean 58, sd 16.0 — the distribution §4.10's
// constants were tuned against. Re-running the reception sweep across DirectorSkill
// sd from 15.0 to 16.7 moves every correlation by at most 0.01, so the merge is safe.
```

**And Command reaches into the cast's performance roll directly** — §4.7's `Base` already carries `+0.06·(DirectorCommand − 50)` as part of its baseline, not a patch bolted on from over here, because every shoot has a director whether or not the player is one:

```
Base = 0.28·Craft + 0.18·Instinct + 0.16·Presence
     + 0.16·Fit + 0.12·Prep + 0.10·Chemistry
     + 0.06·(DirectorCommand − 50)

DirectionMult = 0.86 + 0.0028·DirectorSkill
```

A Command-90 director adds ~+2.4 to Base *and* lifts the multiplier — worth **+4.3 Performance to every actor on the call sheet** (simulation-verified: 62.7 → 67.1 for an identical cast member). Actors notice. This is how you earn a loyalty roster from the other side: be the director who makes people better, and the best actors take pay cuts to work with you.

*(v9 — a rival director is nothing director-specific either: §10.0's Rivals concept falls out of the Rolodex ranking the same way for a director as it does for an actor — the person you keep losing festival slots to, or whose slate the same financiers keep choosing over yours.)*

## 7.4 Development hell

You maintain a **development slate** of up to 3 (5 with a production company). Each project has `momentum`, and momentum is the resource the whole phase is about.

```
PackageStrength = 0.40·AttachedStarBankability
                + 0.30·ScriptQuality
                + 0.30·YourDirectorStanding

Difficulty(budget) = 30 + 22·log₁₀(budget + 1)
        // micro $4M → 45   mid $30M → 63   tentpole $170M → 79

P(greenlight this quarter) = 0.16 · sigmoid(0.10·(PackageStrength − Difficulty)) · momentum

momentum ×= 0.96 each quarter it sits.  Below 0.22 the project dies permanently.
```

*(v10, fix — `momentum` is a raw internal number, and §15's own rule (row 2: player-facing UI shows only the four Standing meters as numbers, everything else as words) applies to it exactly as it applies to Indispensability and the director's five attributes. What reaches the player is a band, not the float:*

```
momentum < 0.22        "dead"           (already the death floor — this band is just naming it)
0.22 – 0.40             "fading"
0.40 – 0.70             "building"
0.70 – 1.00             "real heat"
> 1.00                  "can't-miss"     (a fresh greenlight resets momentum to 1.0 — this band is
                                          only ever seen mid-quarter, right after a big swing)
```

*Same convention §6.4's Indispensability table and §7.2's attribute read already use — the number drives the math, the band is what the producer's tone in the room actually sounds like.)*

**Development actions — one per project per year.** You are not tending a garden every quarter. You get one meaningful intervention per project per year, and it costs money, a favour, or a calendar block.

*v3 had you making momentum decisions quarterly across three projects: twelve prompts a year for one half of one career. The pipeline maths below is unchanged — only how often you're asked.*

Each costs a quarter, money, or a favour. *(v10, fix — the five original rows below still carry their v8 flat numbers; the three v10 rows carry ranges. Left as-is rather than silently rewritten: those five are already simulation-verified against §14's pipeline table at their flat values, and re-deriving them as ranges is a real re-tuning pass this document hasn't run, not a two-line edit. The inconsistency is real and visible on purpose — better than quietly implying five untested numbers just got the same treatment as the tested ones.)*

| Action | Momentum | Other effect |
|---|---|---|
| Rewrite (hire a writer) | +0.20 | ScriptQuality ±, costs money |
| Attach a star | +0.35 (variable — see below) | Costs a Rolodex favor; huge PackageStrength swing |
| Cut the budget | +0.15 | **Lowers Difficulty** — often the real answer |
| New financier | +0.25 | May cost final cut |
| Take it to the market (§10.4) | +0.30 | Presales; requires a market window |
| Self-finance | instant greenlight | Your own money at full risk |
| Put it in a drawer | freezes decay | Can revive later; era may have moved on |
| **Call in a favour** *(v10, new)* | +0.20 to +0.35, no money cost | Spends a Leverage favour — the size of the favour you spend (a Rolodex balance, not a flat toggle) sets where in the range you land; a financier who owes you one big ask gives more than one who owes you a small one |
| **Option an adaptation** *(v10, new)* | +0.08 to +0.22 | Pivots the project onto existing IP (§9.4's `SourceMaterialType`), for a real licensing cost against the budget ask: `ScriptQuality` reads the same familiarity term §9.4's own adaptation-audience-bonus already applies to an actor's role. Where in the range you land reads how much of the licensing cost you actually paid — a cut-rate option on obscure source material barely moves the needle, a real prestige property costs more and pulls harder. Centred below Cut the budget's flat +0.15, because the real payoff here isn't this quarter's roll, it's the finished film's own numbers |

**"Attach a star" isn't one flat action — who you're actually attaching changes what it means.** *(v10, revised — replaces an earlier draft's separate "Poach a rival's attachment" row, which duplicated this action instead of extending it.)* You name a target — any tracked Rolodex NPC, or a cold, untracked name — and the real outcome reads their actual relationship state (§10.0's own `Stranger → Familiar → Ally/Rival → Loyal/Estranged → Legacy/Severed` arc), the same states the Rolodex already tracks for everything else:

| Their relationship to you | Momentum | What it actually costs |
|---|---|---|
| **Loyal / Ally** | +0.25 to +0.40, scaled by *their* AttachedStarBankability | Favour cost scaled down by relationship depth — Loyal costs less than Ally, both less than market rate |
| **Familiar / Stranger** | +0.25 to +0.40, same Bankability scaling | The base case — a full favour or real money, no relationship stake either way |
| **Rival** | +0.35 to +0.60, scaled by *their* AttachedStarBankability | The poach — the range sits above the other two because it's taking something already spoken for, but a poach off a minor Rival attachment is still a modest swing, not an automatic jackpot. Real cost, also scaled: `Notoriety +2` to `+8` off how established the rivalry already is (§10.0's relationship-state depth, not a flat number), and their Agenda shifts one step against you regardless of size |
| **Estranged / Severed** | — | Unavailable — you burned that bridge, and this action can't reopen it |

Every tier reads off the same one input — the target's own AttachedStarBankability — rather than three separate factors per row: a bigger name is a bigger swing and a bigger ask no matter who they are to you; *who* they are to you only moves the price and, for a Rival, the social cost.

**What this means for Casting (§7.5), resolved explicitly rather than left as two unconnected stages.** *(v10, fix)* If development ever attached someone, that person **is** the lead — they occupy the "Your roster"/bankable-star slot at Casting automatically, not a second, independent pick. §7.5's five-way choice becomes a live decision specifically on the path where development never attached anyone: `rewrite`/`cut the budget`/`new financier`/`take it to market` alone, all the way to greenlight, arrives at Casting with a genuinely open lead role — the pure-craft, no-stars-attached route this section's own opening already makes a legitimate, harder-climb strategy rather than a dead end. One real seam, one real rule closing it, not a new mechanic.

One action, one row, a real range of outcomes depending on who you actually go after — not a second, situational menu entry that only ever matters if a Rival happens to exist.

**Attaching someone isn't only ever "the star," and it isn't a one-time pick.** *(v11, revised)* Three real reasons to attach, three real mechanical effects — not the same formula wearing three labels:

| Why attach them | Momentum | What it actually is |
|---|---|---|
| **Bankable** | as above (0.25–0.60, tier-scaled) | Fame — the original case, real weight on `PackageStrength` |
| **Good fit, not famous** | +0.10 to +0.20 | Doesn't move `PackageStrength`'s star term at all — eases the package itself, the same real lever Cut the Budget already uses (a smaller `Difficulty(budget)` read), just tied to a person instead of a one-time cut |
| **A studio favourite** | +0.15 to +0.25, flat | Reliable specifically *because* it isn't fame-scaled — the studio already trusts them, full stop. The one type where a total unknown is exactly as useful as a star |

And it's a real roster, not a lead-plus-one: attach as many people as you want before greenlight, each one aging quarter to quarter. **The risk is real, and it grows.** The longer a project sits without shooting, the more likely someone with other options has moved on:

```
P(drop this quarter) = clamp(0.03 + 0.02·quartersAttached, 0, 0.55)
```

A loss reports plainly (who, and that it happened) and, if it was your bankable lead, `attached_star_bankability` recomputes off whoever's left — the same read-off-the-roster logic that already applies when someone new joins. An ensemble of three doesn't just raise `chaos` at the Shoot (§7.6's own ensemble-chaos idea, now summed across the whole roster instead of capped at one "second attachment") — it's also three independent clocks that can each run out.

**Attaching someone was a guaranteed yes, which quietly skipped the actual decision.** *(v12, fix)* The only input this ever needs is the offer itself — but whether they take it is now a real question, reading numbers already in play rather than a fourth roll bolted on:

```
bankable:       base 0.75 − 0.30·(their Bankability/100) + 0.20·(projectMomentum/2) + 0.20·(YourStanding/100)
genre_fit:      flat 0.75 — they want this kind of project, full stop
studio_favorite: flat 0.80 — reliable by construction, that's the whole point
                + tierBonus:  Loyal +0.15, Ally +0.08, Familiar 0, Stranger −0.05, Rival −0.10
                floor 0.15 — even the hardest ask is never a near-certain no
```

*(v13, retune — the first pass's 0.50 resistance coefficient and 0.05 floor were checked empirically, not just asserted: 10 seeded careers averaged 4.1 films/68-year career before this whole mechanic existed, 2.7 after — worse than this section's own "bleak newcomer" 30-year baseline, under a policy actively working every year. Retuned to 0.30/0.15; a follow-up check landed at 3.0, a real improvement but not a full recovery. Still short of the simulation-verification pass §7.4's own pipeline table went through — flagged, not hidden.)*

A bankable target resists more the bigger they already are (more offers competing for their time) — the same "harder to land, bigger swing if you land it" tension casting's own bankable-star choice carries, read from the offer side instead of the outcome side. But that resistance is real, not fixed: a project with real momentum, or a director with real Standing, is its own genuine pull — which makes *when* you make the offer a real decision too, not just *who*. A cold pitch on a project that's barely moving is a different bet than the same name approached once the package already has heat. A decline costs nothing beyond the year already spent making the ask — the same real opportunity cost a passed-on pitch already carries everywhere else in this design.

*(v10, new — two more actions were deliberately **not** added as new rows either, on §0.1's own Decision Test: a "hire a different writer" distinct from Rewrite, and a "co-financier" distinct from New financier, are not new choices, they're the same choice with different numbers behind it depending on what's already true of the project. `Rewrite` on a project a director has real money behind can pull in an outside voice for a bigger, riskier ScriptQuality swing than their own pass. `New financier` sometimes resolves as a co-financing split instead of a full replacement, when the studio's own risk profile calls for it. The table stays at nine rows, not thirteen.)*

**Development isn't silent between actions.** *(v10, new — and this is the one place this section has to be explicit about its own cadence, sitting right next to the v3→v4 lesson above it: these are four internal rolls per year, not four more prompts. They resolve silently across the year's quarters and land in the same single yearly report the one dev-action already produces — "the market cooled on you this year, but a rival's own attachment fell through in June" reads as one sentence in a result the player already gets, never a fifth interruption. Reintroducing v3's mistake by accident, in the name of dynamism, would be the one genuinely bad outcome of this whole addition.)* Every quarter, independent of whichever action you took, one event roll:

```
P(event this quarter) = 0.06 to 0.18, off this genre's own GenreHeat        // a hot, crowded genre
                                                                             // means more competing
                                                                             // productions drawing on
                                                                             // the same financiers —
                                                                             // more news, not weather
                                                                             // manufactured from nothing
event magnitude ~ U(0.10, 0.18) momentum, sign by type   // bounded inside [CUT_BUDGET_MOMENTUM,
                                                          // REWRITE_MOMENTUM] regardless of how the
                                                          // odds moved — felt, never dominant, and
                                                          // never close to ATTACH_STAR_MOMENTUM's ceiling
```

Which event fires reads §10.0's own background-industry state instead of a fresh roll with no reference: a **financier cold-feet** event (momentum down) draws its odds from that studio's own `trust`/genre exposure the same way `studios.decide_marketing_spend()` already reads trust; a **market window** event (momentum up, `take_to_market`'s next use gets `+0.10` on top) fires only when the real `GenreHeat` for this project's genre is already above its own median, not a coin flip disconnected from the world; a **rival attachment scare** (momentum down, one-time) only fires if a tracked Rolodex Rival exists and shares this genre. No Rival, no rival event that quarter — the event pool itself is state-gated, not just its odds. This is the same "the industry runs in the background" mechanism §9.3's `GenreHeat` already surfaces, not a second event system invented for this Part. The point isn't more prompts; it's that two years at identical momentum shouldn't feel identical, and *why* they differed should always be traceable to something real in the world, never unexplained noise (§15's own "always show why" rule, cited directly).

**Verified pipeline output** — 1,200 careers × 30 years, at `base 0.16 / decay 0.96`:

| Director standing | Films per 30 yrs | Median dev time | Projects that died in dev |
|---|---|---|---|
| **Newcomer (18)** | 2 (p90: 6) | 2.8 yr | 6 |
| **Working (45)** | 9 | 2.0 yr | 4 |
| **A-list (75)** | 15 | 1.5 yr | 1 |

A-list pace of one film per two years matches the real working rhythm of a top director. A newcomer making two films in thirty years is bleak and correct — and it's why the game must make the *climb out of that* the early-career arc rather than a grind.

*(v9 — `Difficulty` and financier attention already implicitly price in competition; §10.0 is what that competition actually is. Every quarter, dozens of background productions are chasing the same financiers you are, and §9.3's `GenreHeat` is the visible symptom: a hot genre means more of those background directors are drawing on the same money, tightening the deals you can get even though nothing in the formula above changed. This doesn't move the verified constants — it's why they were tuned where they are.)*

## 7.5 Casting — now you're the gatekeeper

You run §4.4's utility function as `G`. The offer board fills with actors instead of roles, and every entry shows their Standing, Persona fit, Quote, and — if you've worked together — your private notes.

**The core director decision, every single film:**

> The star gets you the budget. The right actor gets you the film.

```
Attaching an actor with Bankability B unlocks budget tier:
    maxBudget = 3 · exp(0.041 · B)         // B=30 → $10M, B=60 → $35M,
                                            // B=85 → $98M, B=100 → $180M
```

So casting is *literally* how films get financed, which ties the two careers together at the economic level rather than the cosmetic one.

| Casting choice | Trade |
|---|---|
| **The bankable star, wrong for it** | Budget unlocked, `Fit` penalty on their Performance, possible ego events |
| **The right actor, no heat** | Best Performance, but Difficulty stays high and the film may never get made |
| **The discovery** (unknown, no Standing) | Enormous Performance variance. If they break out: permanent Prestige, a `discovered_by` edge, and a loyalty roster for life. |
| **Your roster** | Reliable Performance, Chemistry bonus, they'll work under quote for you |
| **The difficult genius** | Highest Performance ceiling in the game, +0.15 `chaos`, on-set conflict events, may cost you the schedule |

*(v10, new — Casting, the Shoot (§7.6), and the Edit (§7.7) all resolve within the same turn a greenlight actually lands, not a new calendar block each. A greenlight is already rare by construction — §7.4's own verified table puts a newcomer at ~2 films in 30 years — so these three real decisions arrive together, once, on an event that's already earned, the same way Part 5's three pushed on-set moments only arrive when a role is actually landed. §0.2's decision budget already prices directing's dev slate at 3/year; this doesn't add to that average, it makes what happens on the rare year a greenlight lands worth the wait instead of one silent dice roll.)*

## 7.6 The shoot — style as a real choice

Pick a shooting approach before principal photography. Each is a genuine trade, none dominates.

| Style | Performance | Schedule | Other |
|---|---|---|---|
| **Heavy coverage** | ceiling −6 | −1 block equiv. | Raises `PostLuck` floor by 8 — you can fix it in the edit |
| **Long takes** | ceiling +10, sd +5 | −2 | +5 `Craft` critic bonus; disaster if the cast is weak |
| **Many takes (20+)** | +8 for Craft>70, −5 otherwise | −2 | Cast `Condition` −10, grudge risk |
| **Improvisation** | rewards Instinct: +0.10·(Instinct−50) | 0 | `ScriptQuality` weight drops to 0.22, ensemble weight rises to 0.38 |
| **Lean and fast** | ceiling −8 | +1 | Budget under; `Efficiency` reputation ++ |

```
Overage% = clamp( 0.35·ambition + 0.40·chaos − 0.006·Efficiency·100 + N(0,0.08), −0.20, 1.20 )
```

Going more than 25% over budget: the studio takes final cut, *or* your next project's `Difficulty` rises by 12. Coming in under: `Efficiency` reputation rises and financiers seek you out — a quiet, real, and rarely-modeled kind of power.

*(v10, new — an ensemble package from §7.4's "attach a star" (a second name attached to a project that already has one) adds `chaos +0.04` to `+0.13` here, scaled by that second name's own Bankability — an ensemble of two mid-tier names barely registers, two real stars is a real risk, and the range is deliberately capped below "the difficult genius" cast choice's own flat `+0.15`, since a packaging-stage decision made before you know anyone's temperament is a smaller bet than knowingly casting a difficult one. The two stack if you did both: an ensemble of difficult geniuses is exactly as combustible as it sounds, and the `Overage%` formula above reads their sum, not the larger of the two.)*

**The marketing budget is set here, not before and not after §7.7.** *(v10, new)* The studio's campaign spend (§8.2's Marketing curve) is decided once the film is actually in the can — after the Shoot, before the Edit reveals what the film actually is — the same point in the sequence the actor path already resolves it at (§4.5's Deal terms are locked earlier, but the *spend* itself waits for a finished film). No one, including the studio, gets to price a campaign off a quality score that doesn't exist yet.

## 7.7 The edit — the inversion, precisely

This is the payoff of the whole career. In §4.10 an actor eats `PostLuck ~ N(52, 14)` blind. As a director, `PostLuck` stops being a blind roll and becomes yours to steer with the attributes below — and §5.14 is where that steering becomes three concrete decisions (runtime, whose film it is, the ending), not just a better-tuned formula. As a director:

```
PostLuck = 45 + 0.30·(Craft − 50) + 0.25·(Taste − 50)
         + editorLoyaltyBonus                 // up to +5
         + N(0, 9)                            // sd 14 → 9

// A Craft-80 / Taste-80 director with a loyal editor: mean ≈ 66.5, sd 9.
// A Craft-35 / Taste-40 director: mean ≈ 38. The edit is where films die.
```

**Final cut** decides who rolls:

| Who has it | Resolution |
|---|---|
| **You** | Your formula above. You also own the blame. |
| **The studio** | `PostLuck = 0.45·(your roll) + 0.55·(studio roll)`, where the studio roll is biased toward `AudienceScore` (+6) and against `FilmCriticScore` (−7). Commercial and worse. |
| **Contested** | Test screenings. Bad scores trigger forced reshoots: −money, −schedule, `PostLuck` re-rolled with the studio's bias. |

**Final cut is earned, not bought:** granted at `DirectorPrestige > 70`, or after two consecutive profitable films, or by taking a large fee cut. It is the single most valuable contractual term in the game.

**A contested cut reshoots at most once.** *(v10, new)* A second bad test score locks in the worse `PostLuck` rather than triggering another round — §0.1's Decision Test again: a reshoot loop with no cap isn't a decision, it's a slot machine you keep feeding. One real reshoot, with a real cost, is the mechanic; a second one is just delay.

**Disowning a film.** If the studio recut you badly, take the pseudonym (the game's Alan Smithee). Your `Prestige` is shielded from the result entirely, you forfeit backend and most of the fee, and the studio Rolodex takes a −25 hit. Sometimes it's right.

## 7.8 Signature — the auteur's Legibility problem

Same engine as the actor's Persona (§4.2), different vectors:

```
VisualSignature   = { naturalist, expressionist, formalist, kinetic,
                      static, maximalist, minimalist }
TonalSignature    = { bleak, ironic, sincere, comic, operatic, cool }
ThematicObsession = { family, violence, faith, class, memory, obsession,
                      institutions, the west, the city }
```

**Auteur Legibility behaves differently from actor Legibility, in a specific and important way:**

| | Actor | Director |
|---|---|---|
| Critics reward high Legibility? | **No** — staleness penalty | **Yes** — a recognizable voice is the point. `+0.08·Legibility` to `FilmCriticScore` |
| Studio board at high Legibility | narrows | **narrows much harder** — studios fear auteurs |
| Festival access at high Legibility | n/a | opens dramatically |

So the director's version of the typecasting dilemma isn't "am I stale," it's **"am I employable."** A Legibility-90 auteur is beloved by Cannes and unhireable by a studio. The way through is the same as the actor's: a deliberate register change, at a cost.

**Late style.** After 25+ years at Legibility > 70, unlock the *late style* flag: `FilmCriticScore` variance doubles. Critics either declare it a masterpiece or a self-parody, with little middle. Fitting, and mechanically spicy.

## 7.9 The Unit — crew loyalty

Directors don't work alone, and the recurring-collaborator relationship is one of the truest things about the job. Your **Unit** is five persistent crew NPCs with their own loyalty tracks.

| Crew role | Bonus at loyalty 80 | Loss if they leave |
|---|---|---|
| **Cinematographer** | +6 to `Craft` contribution, `chaos` −0.08 | Visual signature weakens for 2 films |
| **Editor** | `PostLuck` +5, sd −3 | The edit gets scary again |
| **Composer** | `AudienceScore` +3 | — |
| **Production designer** | `ProductionValue` +5 | — |
| **First AD** | `Efficiency` +12 effective | Overage rises sharply |

Crew are poached by richer directors, retire, die, or graduate to their own directing careers — your brilliant DP leaving to direct is a genuine loss dressed as good news for them. Loyalty is built by hiring them repeatedly, defending them to producers, and sharing credit in interviews.

## 7.10 The director's career shape

```
student film → short → micro-budget indie → FESTIVAL BREAKOUT
    ↓                                              ↓
  never gets out                          ┌────────┴────────┐
                                    studio job-for-hire   stay indie
                                     (THE SELLOUT CHOICE)      ↓
                                          ↓              festival auteur
                                    franchise offer        (low money,
                                          ↓                high Prestige)
                                ┌─────────┴─────────┐          ↓
                          become a machine    take the money   late style
                          (Heat, no Prestige)  and run back
                                                to the indie
```

**The sellout decision** is the director's version of the actor's typecasting problem, and it should arrive at the moment of maximum temptation: right after your festival breakout, when you have Prestige and no money, and a studio offers you a $90M franchise entry. Taking it is *not* wrong — it buys final cut leverage and a Rolodex you can't otherwise get. Taking it twice in a row is usually fatal to the auteur path.

## 7.11 Playing both — the actor-director

Directing yourself is available and deliberately dangerous.

```
Condition −18 while directing yourself      // split attention
Your Performance uses your own Command      // you can't give yourself notes
PostLuck is yours AND Performance is yours  // variance compounds:
                                            // sd_total ≈ 17 vs 11 for either alone
Vanity penalty: if DirectorStanding > 65 and ROI < 0.8,
    FilmCriticScore −6 and Notoriety +8     // "an act of hubris"
```

**Switching careers** — this is where the Rolodex earns everything:

```
Prestige transfers at 60%      // respect is partly portable
Heat transfers at 35%          // nobody buys a ticket for a director
Affection transfers at 80%     // the public still likes you
Rolodex transfers at 100%      // ← the entire point
```

An actor with twenty years of director relationships can get a first feature financed almost immediately. An actor who burned every bridge cannot. The Rolodex stops being a nice bonus system and becomes the load-bearing wall of the whole design.

## 7.12 Platform expansion — earning a wider release *(v10, new)*

A film that opened Limited or Festival (and, for Festival, actually sold — an unsold submission has nothing to expand) can be pushed for a wider release afterward. **Once, not a ladder.** An earlier draft of this section had a three-tier Festival → Expanded Limited → Wide climb with its own fatigue-decay curve; cut on §0.1's own Decision Test — the tier that actually matters is the first one, and a second and third ask past it were retries dressed as depth, not real choices.

**The ask has to be earned before it's even offered** — availability itself is the first gate, off the film's own already-resolved reception:

```
available  ⇔  reception is at least "warm"/"a real draw" (§4.10's own bands) — a cold or soft
              opening has nothing to point to, and there's no request worth making
```

Past that gate, one negotiation, reusing what's already built rather than a new formula stack:

```
P(expansion granted) = influence_fn(trust, importance) × ratingDampener(ContentRating, studio)

ratingDampener:  G/PG → 1.00
                 PG-13 → 0.85 – 0.95
                 R → 0.65 – 0.85
                 NC-17 → 0.45 – 0.65
```

`influence_fn` is `director_influence_on_studio_decision` on a directed film, the same fame-gated curve already deciding a release-strategy request or a marketing push — not a fourth copy of that shape. `ratingDampener`'s range isn't rng noise, it reads which studio is financing the expansion the same way `effective_rating_ceiling` (the studio pressure mechanic §5.19 introduced) already does: a prestige house's own identity sits at the top of each band's range, a blockbuster machine's at the bottom — a specialty distributor is genuinely more willing to go wide with an R than a four-quadrant one is, and that's the same studio-identity number this design already computes, not a second read of it. Even at its floor it only cuts the odds by roughly half; it can never zero them out the way the availability gate above already can.

**Deliberately left out**, named rather than silently dropped: genre heat and awards `BuzzScore` were both real candidates — a hot genre or a mid-campaign film both have an honest case for expanding — but adding them would mean explaining a denial across four separate numbers instead of one. §15's own "the player never sees the raw math" rule already implies this: a factor that doesn't change the *legible* story the player gets back ("it did well enough, and they believed in you enough") isn't worth the opacity it costs to include. Worth revisiting if a later pass finds the two-factor version reads as thin in play — cut for now, not forbidden.

*(v10, fix — this isn't inconsistent with §7.4's dev-events reading `GenreHeat` a few sections earlier, even though both are "should GenreHeat be a factor here" calls that landed differently. They're answering different questions: §7.4's events explain **whether something happens at all** — background-industry texture, the same "always show why" attribution row 1 of §15 already demands for any real-world event. This section's `GenreHeat` would only ever have modulated **a number already in play**, stacked on top of `influence_fn` and `ratingDampener` — a third multiplier on a formula that was already trimmed once this pass specifically to stay legible. Texture earns inclusion more easily than a third stacked term does.)*

**What a grant actually does:** extends the film's own `weekly_gross_curve()` (§4.10) forward from the point of the request with a larger screen count, and re-runs the marketing decision once more for the expansion push specifically — a genuine second cost, not a free upgrade tacked onto the first release.

## 7.13 Director-for-hire — the offer comes to you *(v10, new)*

Not every project starts in your own development slate. §7.10's own career-shape diagram has always named the moment a studio walks up with a franchise entry as *the sellout decision* — this section is that beat, mechanized, not just narrated.

```
P(hire offer this year) = base × standing_term(DirectorStanding) × genreFitTerm(Legibility, requested genre) × GenreHeat(genre)
```

`standing_term` and `GenreHeat` read exactly like every other real number in this design — the shared Standing model, §9.3's genre cycle. `genreFitTerm` is the one that needed real care: §7.8 already states high Legibility *narrows* general studio access even as it *sharpens* how well you fit one specific genre — so this is not a monotonic "more Legibility, more offers" term. It peaks at moderate Legibility (broad, generic hireability) and only stays high past that peak for the one genre your Signature actually matches; every other genre's offer odds fall off a cliff past that same point. A famous minimalist doesn't get horror offers just for being famous.

**Terms are structurally different from a self-driven greenlight — that's the entire point of taking one:**
- Skips development hell outright. No momentum, no `Difficulty` check — the offer either exists or it doesn't, and accepting routes straight into Casting (§7.5) exactly like a self-financed project does. No second pipeline.
- Final cut starts with the studio by default, not earned the normal way (§7.7's bar still governs any film after this one) — the real trade §7.10 already names.
- `delta_prestige` reads lower than a self-driven film's own (commercial work, not your vision); `delta_heat` reads higher (real visibility) — the same billing-weight-shaped split the Standing formulas already use elsewhere, not a new one.
- If Signature/Legibility (§7.8) is built, each hire film nudges Legibility down slightly — direct, mechanical support for §7.10's own "become a machine (Heat, no Prestige)" branch, not just a diagram label.

**Declining costs nothing the first time.** Repeated declines from the same studio cost trust the same asymmetric way `studio_relations` already reads elsewhere (a big loss costing more than an equivalent gain earns back) — reused, not reinvented. A declined offer resolves through §10.0's background industry exactly like a declined acting role: someone else directs it, and the obituary can query what happened to it.

*(v10, note — this event fires probabilistically and rarely by construction (§0.2's decision budget), a pushed notification only when the roll actually lands, the same restraint the Casting/Shoot/Edit sequence already earns from being gated on a rare greenlight. `base`/`standing_term`'s exact shape are unverified against simulation, same caveat as the rest of this pass — see the note at the end of this Part.)*

**v10 verification status.** *(v10, note)* Every number introduced in this pass — the Bankability-scaled ranges in §7.4, the event-probability formula, the rating dampener in §7.12, `director_hire`'s own probability terms in §7.13 — is a designed judgment call, not a simulation-verified constant. That's a real, deliberate difference from the rest of this Part: `greenlight_probability`, the pipeline table, and `PostLuck`'s own constants all carry a "verified against N simulated careers" citation; nothing added this pass has been run through that same check yet. Flagged here rather than left to look equally load-bearing — the next real step for all of v10 is the same 1,200-careers-×-30-years pass §7.4's own table already went through once.

## 7.14 The slate — working more than one project at once *(v15, new)*

**Why this exists.** §7.4's own pipeline table already names the newcomer's bleak baseline — 2 films (p90: 6) in 30 years — as intentional, correctly-bleak design. But instrumenting a real director's career (`PackageStrength` vs `Difficulty` at every budget tier, every year) turned up a second, structural problem sitting on top of that intentional bleakness: a project stuck at low `PackageStrength` doesn't just greenlight slowly, it occupies the director's *entire* yearly action for however many years — sometimes 20+ — with nothing else able to happen in parallel. A career isn't just gated by Difficulty; it's gated by having only ever one shot in the chamber at a time. Real directors, even early-career ones, are rarely working on strictly one thing — they take a general meeting on a second project while the first one sits with a financier who hasn't called back.

**The mechanic.** A director can have more than one project in development at once — a real slate, not just the one active pursuit — but the yearly action (§0.2's decision budget) still only spends on *one* project a year. The real new decision isn't "do more work," it's **triage: which project gets this year's attention, and which gets left to sit.**

```
SlateCapacity(DirectorStanding) = 1   if StandingScore < 25
                                   2   if StandingScore ∈ [25, 55)
                                   3   if StandingScore ∈ [55, 80)
                                   4   if StandingScore ≥ 80
```

A brand-new director gets exactly today's one-track experience — the second slot only opens once there's a real reputation behind it, the same Standing-gated pattern already used for agent tiers and hire-offer odds (§6, §7.13). This also gives Standing a second, structural payoff beyond `PackageStrength`'s own 30% weight: growing it doesn't just make each project easier to greenlight, it means fewer years spent with your whole career blocked on one stalled deal.

**What a shelved project does while it's not active:**
- Its momentum sits frozen — no event roll, no `Difficulty` check, no cooling. Setting a project aside costs it nothing on its own.
- Anyone already attached to it keeps aging and risks walking (the same attrition §7.4's Attach-a-star roster already models) — real people don't wait around forever just because you're not calling this year. A shelved passion project can still quietly lose its cast.
- It never competes with the active project for genre demand, studio attention, or anything else world-side — it's genuinely paused, not secretly still rolling in the background.

**Switching focus is free** — no action cost, no roll, a between-years choice like checking the Rolodex. The outgoing active project goes back into the slate exactly as it stood, including its own pending casting/shoot/release/marketing choices; nothing is lost by looking away.

**Scrapping is also free**, and distinct from "put it in the drawer" (§7.4's existing freeze action): drawer keeps a project shelved-but-yours, still occupying a slate slot, in case a stalled deal is worth reviving later. Scrap permanently drops it and frees the slot outright — real, no-cost permission to cut a dead-weight project loose rather than let it squat on capacity you could use for something with better odds.

**A director-for-hire offer (§7.13) displaces the active project the same way a free focus-switch does** — accepting one shelves whatever was active rather than discarding it, since the hire resolves the same year it's taken.

*(v15, note — unverified against simulation like the rest of v10/v13; the intended empirical question is whether real slate use — a genuinely triaging policy, not blind round-robin — meaningfully raises films-per-career relative to §7.4's single-track baseline, or whether the underlying `PackageStrength`/`Difficulty` gap dominates regardless of how many shots are in the chamber.)*

---

