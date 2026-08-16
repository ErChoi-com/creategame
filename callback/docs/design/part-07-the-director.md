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

| Attribute | What it does |
|---|---|
| **Vision** | Originality and ambition. Sets the ceiling on `ProjectQuality` and drives Signature strength. High Vision + low Efficiency is the classic overreaching auteur. |
| **Command** | Leading actors and crew. **This is the single most important attribute** — it feeds `DirectionMult` and directly raises every cast member's Performance roll. |
| **Craft** | Blocking, coverage, camera, composition — how well you actually make the thing. Lowers `chaos`, raises `PostLuck`, feeds `FilmCriticScore` and festival fit. |
| **Taste** | Script judgment. See below — this one is unusual. |
| **Efficiency** | Schedule and budget adherence. Determines overage, which determines whether you keep final cut. |

*v3 had seven. **TechCraft** and **Eye** did the same job under two names — merged into Craft. **Nerve** was barely referenced; holding your vision under pressure is what Vision means.*

### Taste is information, not power

Every other attribute makes you better at something. **Taste makes you see clearly.** When you read a script, the game shows you an *estimate*:

```
PerceivedScriptQuality = TrueScriptQuality + N(0, 26 − 0.22·Taste)
```

At Taste 20 you're reading scripts through a fog of ±21. At Taste 95 your error band is ±5. A low-Taste director with excellent Command will shoot the hell out of a bad screenplay, over and over, and never understand why the reviews don't come. **That is a real and specific kind of career**, and it emerges from one line of noise.

Taste is also the hardest attribute to raise: +1/yr from watching films, reading, and — most effectively — *being wrong and finding out.*

## 7.3 DirectorSkill — the bridge to the actor model

Everything in Part 4 that reads `DirectorSkill` and `DirectorPrestige` now resolves against a real character, whether NPC or player.

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

**And Command reaches into the cast's performance roll directly.** Amend §4.7:

```
Base = 0.28·Craft + 0.18·Instinct + 0.16·Presence
     + 0.16·Fit + 0.12·Prep + 0.10·Chemistry
     + 0.06·(DirectorCommand − 50)          // ← NEW

DirectionMult = 0.86 + 0.0028·DirectorSkill
```

A Command-90 director adds ~+2.4 to Base *and* lifts the multiplier — worth **+4.3 Performance to every actor on the call sheet** (simulation-verified: 62.7 → 67.1 for an identical cast member). Actors notice. This is how you earn a loyalty roster from the other side: be the director who makes people better, and the best actors take pay cuts to work with you.

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

**Development actions — one per project per year.** You are not tending a garden every quarter. You get one meaningful intervention per project per year, and it costs money, a favour, or a calendar block.

*v3 had you making momentum decisions quarterly across three projects: twelve prompts a year for one half of one career. The pipeline maths below is unchanged — only how often you're asked.*

Each costs a quarter, money, or a favour:

| Action | Momentum | Other effect |
|---|---|---|
| Rewrite (hire a writer) | +0.20 | ScriptQuality ±, costs money |
| Attach a star | +0.35 | Costs a Rolodex favor; huge PackageStrength swing |
| Cut the budget | +0.15 | **Lowers Difficulty** — often the real answer |
| New financier | +0.25 | May cost final cut |
| Take it to the market (§10.4) | +0.30 | Presales; requires a market window |
| Self-finance | instant greenlight | Your own money at full risk |
| Put it in a drawer | freezes decay | Can revive later; era may have moved on |

**Verified pipeline output** — 1,200 careers × 30 years, at `base 0.16 / decay 0.96`:

| Director standing | Films per 30 yrs | Median dev time | Projects that died in dev |
|---|---|---|---|
| **Newcomer (18)** | 2 (p90: 6) | 2.8 yr | 6 |
| **Working (45)** | 9 | 2.0 yr | 4 |
| **A-list (75)** | 15 | 1.5 yr | 1 |

A-list pace of one film per two years matches the real working rhythm of a top director. A newcomer making two films in thirty years is bleak and correct — and it's why the game must make the *climb out of that* the early-career arc rather than a grind.

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

## 7.7 The edit — the inversion, precisely

This is the payoff of the whole career. In §4.10 an actor eats `PostLuck ~ N(52, 14)` blind. As a director:

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

---

