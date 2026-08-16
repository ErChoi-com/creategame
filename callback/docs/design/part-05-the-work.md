# PART 5 — THE WORK: CREATIVE DECISIONS

## 5.0 The gap this fills

Read the document so far and notice what you never do: **a decision about the work itself.**

You choose roles, deals, schedules, franchises, favours and fights. You never choose *how to play the part.* Performance is a formula with `Prep` and `Fit` as inputs, and `Prep` is picking one of six preparation methods. Nothing in Parts 3–4 asks what you think the character is.

That's the wrong hole to have in a game about acting. This Part is the work.

## 5.1 The perception principle

The organising idea, and it applies everywhere:

> **Your character's perception determines your interface.**
> Attributes don't decide whether you're right. They decide how clearly you can see what your
> choices will do. (Revised in §5.7 — an earlier version of this made it a guessing game.)

A director with low Taste reads scripts through noise (§7.2). An actor with low Instinct sees a blurred version of what a role needs. As those attributes grow, **the game literally becomes clearer to play** — the estimates tighten, the previews get honest, the fog lifts.

This is the most satisfying kind of progression available, because the improvement happens in the player's understanding rather than in a number. A veteran isn't just stronger; they can *see*.

## 5.2 Why the first version of this was wrong

An earlier draft of this Part had a system called *interpretation*: every role carried a hidden **TrueReading**, you guessed at it, and your Instinct determined how clearly you could see it. Alignment with the hidden answer fed your performance.

**That is a skill check wearing a costume.** There's a right answer, you're rolling to find it, and the fiction of creativity is painted on top. Everything interesting about making something — that there *isn't* a right answer, that two good versions can be completely different, that your choices produce a thing with a texture — was missing.

It's replaced by what follows. **No hidden answer. You set the dials, and the dials make the film what it is.**

## 5.3 The palette — six dials that describe a film

A film is described by six settings, each running −50 to +50. The director sets them; the budget and schedule constrain them; the results follow from what you chose. **The player never sets these — this is the film's shape, read and reacted to, not chosen.**

| Dial | −50 | +50 | Costs |
|---|---|---|---|
| **Pace** | Slow-burn | Fast-paced | Schedule at the extremes |
| **Colour** | Muted | Vivid | Post budget to push either way |
| **Scale** | Intimate | Epic | **Money.** A $5M film cannot be epic |
| **Intensity** | Gentle | Intense | Effects budget, stunt risk (§4.9) |
| **Clarity** | Subtle | On-the-nose | Free — and the sharpest choice you make |
| **Texture** | Steady | Frantic | Schedule; more setups per day |

*(v9 — the pole words above are the interface's; the original draft used the more literary-photographic Languid/Relentless, Desaturated/Saturated, Restrained/Visceral, Ambiguous/Explicit, Observational/Kinetic. Same six numbers, plainer language — a player reading a shoot's palette for the first time shouldn't need a film-studies vocabulary to know what a dial means. `Pace`/`Colour`/`Scale`/`Intensity`/`Clarity`/`Texture` stay as the internal names; only the poles shown to a player changed.)*

There is no correct setting. There are settings that produce different films.

```
AudienceScore += Σ  audWeight[genre][dial] × setting / 100
FilmCritic    += Σ  critWeight[genre][dial] × setting / 100
```

### The weights differ by genre, which is what stops this being one slider

The obvious failure mode is a single commercial-to-artistic axis: push everything one way for money, the other for reviews. That's not a choice, it's a dial with your name on it. So the weights are **per genre**, and every genre has at least one dial that helps both and one that hurts both.

**Verified** — correlation between a palette's audience effect and its critic effect, over 8,000 random palettes per genre:

| Genre | corr(audience, critic) | What that means at the table |
|---|---|---|
| **Horror** | **+0.52** | Restraint pleases critics *and* works on audiences. Choices that help, help twice. |
| **Comedy** | +0.19 | Mostly aligned. Pace is nearly free money. |
| **Sci-fi** | +0.01 | Fully orthogonal. You can find settings that do both, or neither. |
| **Action** | −0.10 | Near-orthogonal; clarity is the one real trade |
| **Drama** | −0.58 | The genuine tension. Ambiguity is critic gold and audience poison. |

So the same dial means different things in different films, and "what's the smart palette" has no general answer — only a per-project one. Palette effects run about ±7–10 on `AudienceScore`, against a base standard deviation of 7.6. **A major factor, never the only one.**

## 5.4 Coherence — the actual skill

If there's no right answer, what is the skill? **Making the settings agree with each other.**

Seven archetypal shapes exist in the world at any time — blockbuster, art film, horror, chamber piece, epic, vérité, neon. Coherence is how close your palette sits to the nearest one. *(v9 — below coherence 40, "nearest shape" stops being a meaningful description, since nothing is genuinely close to anything; the interface stops naming one at that point and says the film hasn't settled into a shape yet, rather than reporting a misleadingly specific answer.)*

```
Coherence = clamp(100 − 2.2 × distanceToNearestArchetype, 0, 100)
outcomeVariance ×= 1 + 0.014 × (100 − Coherence)
```

**Verified over 20,000 random palettes:** mean coherence 43, with 18% below 30. A languid, saturated, epic, ambiguous film scores 32 and carries **1.95× the normal outcome variance.**

| | |
|---|---|
| **High coherence** | Predictable. Narrow outcomes. You made a recognisable thing well. |
| **Low coherence** | Wide open. It's a mess, or it's a landmark, and you won't know until it's cut. |

Incoherence is **not** a mistake. It's a risk position, and it's the only route to the thing below.

### Landmarks — inventing a shape

```
If Coherence < 60 and (Craft + Vision)/2 > 70:
    P(landmark) = clamp(0.02 + 0.00022 × (60 − Coherence) × (skill − 70), 0, 0.20)
```

| Coherence | Skill 72 | Skill 85 | Skill 95 |
|---|---|---|---|
| 55 | 2% | 4% | 5% |
| 45 | 3% | 7% | 10% |
| 35 | 3% | 10% | 16% |
| 25 | 4% | 14% | **20%** |

A genuinely great filmmaker making a genuinely strange film has about a one-in-five shot. Most strange films are just strange — which is true, and it's what keeps the swing honest.

**A landmark creates a new archetype.** Your palette enters the world's coherence set permanently. Other directors can now be *coherent within it*, so they copy it, and the copies feed the genre boom in §10.3 — which saturates, and turns your invention into a cliché in about eight years. You get to watch that happen.

That loop is the best thing in the document. You don't just make a good film; you change what films are, and then the industry uses it up.

## 5.5 The performance — relationships, not distance

An earlier version of this section measured **contrast** as a single distance between your palette and the film's, and published a table of optimum values. That was the same mistake as §5.2 in a new costume: one number with a solvable best answer, which a player computes once and then plays forever.

Here is what replaced it. **Your four dials each take a *position relative to the film*, and the positions are named, not numeric.**

| Position | Meaning | Player-facing label *(v9)* | Cost |
|---|---|---|---|
| **With** | You move as the film moves. Part of its texture. | *Match it* | 0 |
| **Beneath** | Same direction, less of it. The calm inside it. | *Hold back* | 1 |
| **Beyond** | Same direction, more of it. The most X thing on screen. | *Go big* | 2 |
| **Against** | The opposite. Counterpoint. | *Play against it* | 3 |

*(v9 — With/Beneath/Beyond/Against stay the internal vocabulary this whole Part reasons in; the labels above are what a player actually clicks. The original interface printed the internal keys straight to the screen — literally `with (0)` as a button label — and the running total was reported as "contrast budget 4.6 · spending 4," which reads like a spreadsheet rather than an acting choice. Same mechanic; the words changed, not the numbers.)*

Four dials — **Energy, Volume, Warmth, Speed**, shown to the player as **Energy, Size, Warmth, Tempo** — each taking one of four positions. Sixteen atoms, 256 combinations, and no distance metric anywhere.

### The contrast budget

You cannot hold every position. Sustaining a performance that fights the film is *work*, and how much you can do depends on your technique and on whether the camera is with you.

```
ContrastBudget = (Craft + DirectorCommand) / 28

If total cost > budget:
    Notices  −= 5 × overspend
    Ensemble −= 3 × overspend
    Critics reach for: "mannered", "showy", "indicating"
```

| Who you are | Budget | What that actually buys |
|---|---|---|
| Limited actor, no support | 3.2 | **1 against** |
| Skilled, neutral director | 4.3 | 1 against + 1 beneath |
| Skilled, director with them | 5.5 | 1 against + 1 beyond |
| Great actor, director with them | 6.2 | **2 against** |

This is the whole reason to build Craft and to build relationships, and it's now the *same* reason: both buy you room to take positions. An actor with neither can hold exactly one idea about a character. An actor with both can hold two contradictory ones, which is what great performances are made of.

### Positions read differently on different dials

The four positions are **not** interchangeable. Going *beyond* on Volume in a loud film is shouting in a shouting match, and critics dismiss it. Going *against* on Energy in a kinetic film makes you the still centre, which is the most reliable way to be remembered.

```
READ[dial][position] = (whatItDoesForYou, whatItDoesForTheFilm)

energy   with (0.5, 1.5)  beneath (2.5, 1.0)  beyond (1.0, −0.5)  against (4.5,  0.5)
volume   with (0.5, 1.5)  beneath (3.0, 1.5)  beyond (0.5, −1.5)  against (3.5,  0.0)
warmth   with (0.5, 1.5)  beneath (1.5, 0.5)  beyond (2.0,  0.5)  against (4.0, −0.5)
speed    with (0.5, 1.5)  beneath (2.0, 1.0)  beyond (2.5,  0.0)  against (3.0,  0.5)
```

And genre reweights which dials pay. Stillness is worth 1.5× in horror and 0.7× in action. Speed is worth 1.6× in comedy and 0.8× in drama.

**Verified: no dominant allocation.** Across sixteen build-and-genre combinations, the optimal choice was one of **eight different allocations**, and the most common won only 6 of 16. There is no line to memorise.

### The two currencies

Every position produces two numbers, and they pull apart:

```
Notices   = what the reviews say about YOU
Ensemble  = what your work does for the FILM   → feeds ProjectQuality (§4.10)
```

Look at the read table again: *beyond* on Volume is **+0.5 for you and −1.5 for the film.** Some of the most attention-getting things an actor can do actively damage the thing they're in.

## 5.6 Shape — a performance is not one number, and not one scene

A performance resolves across **three beats**: the introduction, the turn, and the resolution. The turn is the scene it's remembered for.

**v9 — the three beats are three scenes now, actually played, not a formula spread across an imagined shape.** The original design was right that a performance has three beats and wrong about how a player touches them: one contrast-budget decision (§5.5) got made once, per film, and then distributed across `intro`/`turn`/`reso` by a fixed curve (`intro = base − 0.65·lift`, `turn = base + 1.30·lift`, `reso = base − 0.65·lift`) that the player never saw or influenced directly. The beats existed in the math and nowhere else.

They're real now. **The shoot is three scenes, played in order, each its own full position choice** (§5.5 — all four dials, a fresh look at the contrast budget) rather than one choice imagined to cover all three:

```
For each of the three scenes:
    resolved[i] = resolvePositions(yourChoiceThisScene, filmContext)   // §5.5's read table,
                                                                        // unchanged

resolved = mean(resolved[0], resolved[1], resolved[2])   // averaged, not summed — a player who
           // makes the identical choice in all three scenes gets exactly the number the old
           // single-choice version always gave; three real, differing choices land in the same
           // range a single choice always could, just distributed across an actual shape instead
           // of a formula's guess at one

Notices  = 0.55 × peak(scene) + 0.45 × YourPerformanceShape + resolved.forYou
Ensemble = YourPerformanceShape − 4.0 × spikiness + resolved.forFilm
```

*(The `peak`/beat construction below this line — `lift = 9·spikiness`, `intro`/`turn`/`reso` — is unchanged and still describes the shape those three real scenes produce; what changed is that `resolved` now comes from three genuine decisions instead of one decision smeared across a curve. `Notices` also now explicitly carries the `resolved.forYou` term the original formula dropped — the very thing §5.5 spends the whole contrast budget describing has to actually reach the number it's supposedly driving.)*

A short **dailies read** follows each of the first two scenes — the room's reaction, in a line, before the next one — and it is not idle flavour: a scene played past what the day can hold measurably costs you with the director going forward (a small, bounded ding to the working relationship, the same order of magnitude as one of §5.12's on-set moments), because the read a player is given has to be true somewhere or it's decoration, not information (§0.3 Rule 2).

**The three on-set moments (§5.12) now interleave with the three scenes** rather than landing in a block once shooting wraps — one between scene one and two, one between two and three, whatever's left after the third, following the same per-actor frequency §5.12 already specifies. Same pool, same count; only the pacing changed, so a shoot reads as a schedule with things happening between setups rather than a decision screen followed by a debrief.

### v9, new — what the three scenes actually are

A real film has dozens of scenes scattered across a shooting schedule that runs weeks or months. The three you play are not a sample of them — they're the three the finished film's own three-act structure hangs its weight on, and everything shot around them is exactly the "ordinary days" §5.12 already describes: real, resolved, and not worth a decision, because the picture doesn't turn on them. That's the answer to the obvious question — *why three, when a shoot is fifty scenes* — and it should be said to the player once, plainly, the first time they're asked to play one: **you're not playing the whole film. You're playing the three scenes that decide what it is.**

Each scene has a fixed dramatic job, and the `intro`/`turn`/`reso` weighting (§5.6's own beat construction, above) is that job made numeric — not an arbitrary curve, a description of what a three-act structure actually does with its weight:

| Scene | Act | Job | Weight |
|---|---|---|---|
| **The first scene** | Setup | Establishes the baseline everything after it is measured against. Low stakes on purpose — its job is legibility, not memorability. | `−0.65·lift` |
| **The turn** | The set piece | The scene the film is *for*. Whatever this genre's version of "the thing people describe when they describe the movie" is, this is where it happens. | `+1.30·lift` |
| **The last scene** | Resolution | Pays off what the first scene set up, or refuses to. Symmetric weight to the first, opposite function: one opens the account, the other settles it. | `−0.65·lift` |

**The turn is where genre stops being a bias term and becomes a concrete scene**, and it's worth naming what it actually is, because it changes which of §5.5's four dials is doing the real work that day — the same way §5.5 already reweights the dials themselves by genre, this reweights which *scene* you're in when you use them:

| Genre | The turn, concretely | The dial most likely carrying it |
|---|---|---|
| **Horror** | The first kill, or the moment the threat is confirmed real | Energy — stillness against it is the reliable read (§5.5) |
| **Action** | The set piece — the chase, the fight, the thing the trailer is cut around | Speed |
| **Drama** | The confrontation — the thing that's been unsaid finally gets said | Warmth |
| **Comedy** | The set-piece farce, or the joke the whole film has been loading | Speed |
| **Romance** | The falling-out — the moment the intimacy the film built actually breaks | Warmth |
| **Thriller** | The reveal — what you thought was true turns out not to be | Energy |
| **Sci-fi** | The reveal — the rule of the world made visible, not just stated | Energy |
| **Musical** | The number — the scene where the singing is the point, not an interruption | Speed |
| **Period** | The moment the era's weight becomes personal, not just production design | Warmth |
| **Family** | The scene the child in the audience will remember at 40 | Warmth |

None of this changes what you're actually deciding — still four dials, still the same contrast budget, still §5.5's read table untouched. It changes what the choice *means* going in: playing *against* on Warmth in the turn of a romance isn't an abstract counterpoint, it's playing the character *not* breaking when the scene needs them to. The mechanic was always this specific. Naming it is what makes a player feel it instead of just computing it.

**This gives Coherence (§5.4) a face a player can feel, not just compute.** §5.4's Coherence is strictly the six palette dials' distance to the nearest archetype — that formula doesn't read scene content, and this section doesn't change it. But a film can score perfectly consistent on all six dials and still hand you a turn that doesn't structurally belong to the genre it's dressed as — a horror film whose "first kill" plays like a drama confrontation. A player won't see that in the coherence number; they'll see it in the scene in front of them not matching the table above. Reading that gap — is this actually the genre's own set piece, or something dressed as one — is the kind of judgment §5.9's forecast is meant to sharpen with Taste, in prose alongside the number rather than inside it.

**Verified:**

| Allocation | Spikiness | Notices | Ensemble |
|---|---|---|---|
| All *with* | 0.00 | 70.3 | **68.0** |
| Two *beneath* (steady) | 0.07 | 76.9 | 67.2 |
| One *against* (shaped) | 0.29 | **80.9** | 65.8 |
| *Against* + *beyond* (showy) | 0.46 | 78.5 | 62.1 |

Two things fall out of this, and both are true of acting.

**Critics reward the peak; the film needs the mean.** You can build a performance that is extraordinary in the one scene everyone quotes and thin everywhere else, and it will review better than a performance that is quietly excellent for ninety minutes. That's the choice: *play for the moment, or play for the film.*

**Maximum showiness isn't optimal.** The shaped read (one *against*, everything else restrained) beats the showy one on Notices as well as on Ensemble, because *beyond* positions read badly on the dials where they're loudest. The best performances are mostly restraint with one strong idea — which the numbers produce on their own rather than being asserted.

### And if everyone does it

| Cast | Ensemble | Effect on the film |
|---|---|---|
| Four generous leads | 67.2 | ProjectQuality +1.5 |
| Four showy leads | 62.1 | ProjectQuality +0.0 |

A cast of stars all playing for their own reviews makes a measurably worse film than a cast of the same actors playing for each other. That's emergent from the two currencies, not scripted, and it means a director's casting job includes reading who plays well with others.

## 5.7 Generosity and upstaging

The scene-partner layer, and the best long loop in the actor's game.

```
GENEROSITY — play beneath on a dial where your partner plays against or beyond
    you       −1.5 Notices
    them      +2.5 Notices
    the film  +1.5 Ensemble
    and       +1 favour, + their affinity

UPSTAGING — play beyond in their moment
    you       +2.0 Notices
    them      −2.0
    the film  −1.5
    and       − affinity, and the director may simply cut you out of it
```

Generosity costs you about 1.5 Notices a film. Over thirty films that's 45 points of reviews you gave away — and **30 favours banked**, which buys roughly fifteen direct offers with no audition, or ten star attachments to films you want made (§6.2).

More than that: generosity raises director trust, trust raises `DirectorCommand` on your projects, and Command feeds directly into your **contrast budget**.

> **Being generous early literally buys you the ability to take bigger risks later.**

That is the actor's long game, it's mechanically exact, and it's what actually happens. The performer who spends their twenties making other people better is, at fifty, the one who can hold two contradictory ideas at once and have a director shoot it that way.

## 5.8 Serve it, bend it, or fight it

Scripts still have a natural register — the film they want to be. **It is shown to the player, plainly.** No guessing.

The decision isn't what the material wants. It's what you're going to do about it.

| | Effect |
|---|---|
| **Serve it** | Palette drifts toward the script's register. High coherence, reliable, ceiling capped. |
| **Bend it** | Your palette, its bones. Moderate coherence, moderate variance. Most good films. |
| **Fight it** | A war between what it is and what you're making it. Coherence collapses; landmark odds open; so do the odds it's incoherent rubbish. |

Fighting a script that's already great is usually vandalism. Fighting a mediocre one is how mediocre scripts become interesting films. **Reading which is which is what Taste is for** (§7.2) — and Taste now earns its keep by telling you how good the material *actually* is before you decide whether to respect it.

## 5.9 Perception, revised

The perception principle survives, but it does a different job. Attributes no longer determine how well you *guess an answer*. They determine **how accurately the game forecasts the consequences of your choices.**

```
Before you commit a palette, the game shows a forecast of the likely
audience and critic response.
    Forecast error = N(0, 22 − 0.18 × relevantAttribute)
```

At Taste 25 the forecast is nearly useless and you're working on feel. At Taste 90 it's close to honest and you can plan. Growing the attribute makes the game *legible* rather than making you *right* — you can still choose to make the unpopular film, and now it's a decision rather than an accident.

Era fashion is part of the forecast, and it moves. A palette that read as bold in one decade reads as dated in the next (§10.6), which is how a director with a fixed style ages out without ever getting worse at their job.

## 5.10 Signature — what you keep doing

Repeat a palette and it becomes recognisably yours. Your dials drift toward your habits unless you push against them.

```
SignatureStrength rises when your palettes cluster.
At strength > 70, critics name it.
    Recent work strong  →  "a style"      Prestige +
    Recent work weak    →  "a tic"        Prestige −, staleness +
```

Breaking your signature deliberately — a project set well outside your usual dials — costs coherence and resets the counter. It's how mid-career directors and actors escape becoming a parody of themselves, and it's the same move as §6.2's break-type role, one layer down.

## 5.11 The swing, restated

The swing needs no separate system at all: **a swing is deliberately overspending your contrast budget.**

Take two *against* positions on a 4.3 budget and you're 1.7 over. The penalty is known in advance — `Notices −8.5`, `Ensemble −5.1`, and critics reaching for *mannered*. You take it anyway, because the read you want needs both ideas and you'd rather fail at the real thing than succeed at the safe one.

No hidden roll, no gamble on information you don't have. You can see the cost and you choose it. Which means **the way to make swinging affordable is to raise your budget** — through craft, and through working with people who are with you. Relationships don't make you better. They make you able to risk more, which at the end of a career amounts to the same thing.

## 5.12 The three moments on set

§4.7 cut on-set events to three. Here is what those three should be. Not weather and catering — **the actual moments where the work is decided.**

**v9 — three slots, not three fixed events.** Built and played, this needed one more layer than the original draft specified: a fixed pool of exactly these three categories, asked every time, reads as a form after the second shoot of a career. What actually holds up is a **pool drawn from what the production specifically is**, with the three below as the baseline that can always fire and a wider set of situational moments layered on top of it — a stunt on an action picture, a night-shoot schedule that's not survivable, a co-star who's late and everyone's pretending not to notice, pages rewritten and pushed under the trailer door an hour before call, a director's doubt you can't read because you've never worked with them before, a press visit that turns into a story. Which of these are even *possible* depends on the production's own chaos level, its genre, and whether this director is a stranger or someone you have history with — a calm, familiar set simply doesn't generate half of them.

The count stays three (§0.2's budget), but **which three** is drawn fresh each time from whatever the production can actually produce, so thirty shoots don't feel like the same three questions thirty times. And per §0.3 Rule 3, the pool itself narrows with experience: a newcomer gets asked about nearly everything a chaotic set can throw up; twenty years and forty pictures in, most of it resolves on its own — not because the moments stop happening, but because an experienced actor has a standing answer for the ones they've already answered a hundred times, and the game stops asking about only those. The moments below are the ones that never stop being asked, on any set, at any age — the actual center the situational pool surrounds.

### 1. The scene that isn't working

| Choice | Effect |
|---|---|
| Play it as written | Safe. Nothing gained, nothing lost. |
| Propose a change | `ScriptQuality` ± depending on your Taste; director affinity ± depending on whether you're right |
| Do it your way and say nothing | A private swing. If it lands, they keep it and never ask. If it doesn't, you've burned trust you didn't have to spend. |

### 2. The adjustment you disagree with

| Choice | Effect |
|---|---|
| Take it | Your performance dials move toward the director's; contrast drops, safety rises |
| Take it and quietly do yours anyway | You get both takes in the can. **The edit decides**, and you won't be in the room. |
| Argue for yours | Resolves on Craft and standing. Win: they adjust. Lose: affinity −, and now they're watching you. |

### 3. The discovery

Something in rehearsal that isn't in the script.

| Choice | Effect |
|---|---|
| Offer it to the director | Shared credit; affinity + if it's good |
| Keep it for the take | Surprise on camera — high variance, real chemistry effects on scene partners |
| Rebuild the performance around it | A full swing, mid-shoot, with everything already committed |

## 5.13 The director's creative decisions

### What the film is about

Before shooting, commit to a **thematic intent**. It's not decoration — it sets what critics respond to, what festivals want (§9.3), and which axis of your Signature grows.

Committing hard narrows the film: `FilmCriticScore` variance rises, `AudienceScore` falls slightly, festival fit improves markedly. Refusing to commit makes a competent film nobody argues about.

### Casting for the reading

Actors carry their own palette habits (§5.5, §5.8). Casting is now a composition decision rather than a shopping trip: a committed stillness-and-restraint actor in a relentless, saturated film is either your best contrast or a hole in the middle of the picture, and which one it is depends on whether you frame them for it.

> The scene where you realise the biggest name available is wrong for the part, and the unknown is right, is the best scene in the director's game. §6.5's budget maths makes it expensive to be right.

### How much to say

| Approach | Effect |
|---|---|
| **Over-direct** | Pulls every performance toward the film's palette. Coherent, safe, nobody surprises you. |
| **Leave room** | Actors keep their own dials. Higher contrast, higher variance — glorious with a strong cast, a shambles with a weak one. |
| **Direct only the ones who need it** | Requires reading your cast correctly. This is what `Command` is actually for. |

### Shoot the alternative ending?

Insurance costs money and schedule, and it hands the studio something to use against you in post (§7.7). Committing to one ending is braver and sometimes stupider.

## 5.14 The edit as authorship

The flagship creative system, and the one that closes the loop on the whole design.

§7.7 made `PostLuck` a formula the director steers. It should also be **three real decisions**:

```
RUNTIME
    tight     AudienceScore +5, FilmCritic −3, Legs +0.2
    as shot   neutral
    long      FilmCritic +4 if ProjectQuality > 70 else −5; AudienceScore −6

WHOSE FILM IS IT — favour one performance in the cut
    chosen actor:  YourNotices +8
    every other lead: −4

THE ENDING
    as shot        neutral
    test-optimised AudienceScore +6, FilmCritic −5
    ambiguous      FilmCritic +5, AudienceScore −7, cult chance ×2  (§8.9)
```

### The interlock that makes this matter

**A director can make or destroy an actor in the cut, and the actor may never find out.**

If the player is the actor, they get a `YourNotices` number that doesn't match the work they know they did — and no explanation. If the player is the director, they hold someone's year in their hands while that person is at home waiting.

It should be discoverable, but late: at a retrospective, in a memoir, from a crew member decades on, in the obituary. **The film you thought failed you was a choice somebody made in a room you weren't in.** That's the most human thing this simulation can do, and it costs three lines of code.

**v9 — this is no longer strictly true, and the exception is the whole reason §6.3 exists.** An actor holding **a seat in the edit** (§6.3 — earned through a production company, or through being successful enough that editors expect you there, well short of the director's Final Cut above) is no longer purely at the mercy of the three decisions in this section: they get one bounded push of their own on the finished cut, small enough that it never overrides what the director actually decided, real enough that "the room you weren't in" stops being categorically true for the actors who worked for the right to be in it. Most careers never clear that bar, and for them everything above still holds exactly as written — the seat is earned, not given, and it moves the needle, not the outcome.

## 5.15 Script notes

Anyone holding script approval (§6.3) gets notes. What you push for is a real choice with real costs:

| Push for | Effect |
|---|---|
| **Clarity** | `AudienceScore` +, `FilmCritic` − |
| **Ambiguity** | `FilmCritic` +, `AudienceScore` −, cult chance up |
| **Your part** | Your `Fit` and screen time up; `ScriptQuality` down; the whole crew notices |
| **The whole film** | `ScriptQuality` +, nothing for you, and the writer will work with you again for life |

That last row should be the quietly correct answer often enough that players discover it themselves.

## 5.16 Creative levers differ by genre

Different work asks different questions. A short list, because it changes what the three on-set moments even offer:

| Genre | The creative question |
|---|---|
| **Horror** | Commit or restrain? A full-throated scream, or the thing you don't show |
| **Comedy** | Timing, and generosity — do you take the laugh or feed it to the other actor |
| **Drama** | How much to withhold |
| **Action** | Do it yourself or use the double (§4.9's injury maths says the double; ego says otherwise) |
| **Period** | How much of the era to play, and how much to ignore |
| **Musical** | Sing it live on set, or to playback |

## 5.17 The gap

Track, quietly, two lists: **the films you wanted to make, and the films you made.**

Every project you seriously considered and passed on for money, schedule, or fear goes in the first list. Every swing you didn't take. Every script you loved that died in development.

There is no meter and no penalty. It's not a morality system and the game never comments. It simply appears at the end, in the obituary (§11.8 — "the roles you declined, and what became of them," the same tracked list named here from the other end), next to the filmography — and for some careers the two lists are the same, and for most they are not.

That's not a mechanic. It's the reason to build the rest of it.

---

