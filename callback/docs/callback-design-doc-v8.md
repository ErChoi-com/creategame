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
simulation actually measured. Parts 1–3, 7–13, and 15 are the original v8 text; none of that was
built yet, and this pass didn't touch it.

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

# PART 1 — HOW BITLIFE'S ACTOR PACK ACTUALLY WORKS

## 1.1 Access and framing

The acting career is not part of the base BitLife loop. It sits behind a paywall as a **Special Career**, sold either as the standalone **Actor Pack** or inside the **Jobs Pack** bundle (originally gated behind Boss Mode / legacy Bitizen). It shipped as the **Movie Star Update** on **March 10, 2022**.

Structurally it's an *overlay* on the standard BitLife life loop: you still age one year per tap, you still have Happiness / Health / Smarts / Looks, and the acting content is a new menu branch under `Occupation → Special Careers → Actor` plus a **Fame** panel that appears once you land your first credited role.

## 1.2 The prerequisite phase (ages 0–18)

Before you can meaningfully audition, the game asks you to farm two numbers:

| Input | How it's raised | Notes |
|---|---|---|
| **Looks** | Born value, then walks, healthy eating, gym, spa, plastic surgery | Community consensus: you want **80+**. This is the hardest gate for a random-start character. |
| **Acting skill** | *Acting Lessons* under `Activities → Mind & Body`, from **age 8**; parents pay until 18, then ~**$3,000/session** | Practice **~4×/year**; target **90%+** before serious auditions. |
| **Acting special talent** | Character-creation option, requires God Mode | Starts you with a large innate bonus. |
| **Drama club** | School extracurricular | Small contribution, mostly flavor. |

That's the whole preparation model: two sliders, both raised by repeating one button.

## 1.3 The casting layer

After high school you unlock the Actor special career. The casting screen is a **list of job postings** — a rolling set of open roles, each with a short description stating the production, the medium, the genre, and the character being cast.

**Role tiers** (ascending):

1. **Extra** — uncredited, no lines, a few hundred dollars, no skill requirement. The intended on-ramp.
2. **Bit part** — small credited role.
3. **Supporting role**
4. **Lead role**
5. **TV recurring role** — paid *per episode*, renews across seasons, the reliable-income option.

**Mediums and genres:** television (crime, drama, action, sitcom) and film (comedy, drama, thriller, horror), plus regional flavors added at launch — **Bollywood films** and **telenovelas**.

**Two-stage RNG.** Applying does not get you an audition; landing an audition does not get you the part. Guides describe this explicitly as "another layer of luck." The role description carries soft requirements — most importantly **age fit** (a 25-year-old auditioning for a 57-year-old character is near-hopeless) and appearance — and your acting skill weights the roll.

**Talent agent.** Hireable for roughly **$1,500** (some guides cite ~$20,000 for a good one). The agent surfaces better roles and **negotiates pay**; their **commission percentage** is shown on their profile. This is the one genuinely interesting economic decision in the pack.

**Pay display.** TV contracts show **per-episode** compensation; film contracts show a **flat fee**.

## 1.4 The on-set layer

Once cast, each year of the role gives you a menu of actions:

- **Practice / rehearse lines**
- **Develop your character**
- **Co-star interactions** — befriend, compliment, gift, rehearse with, date, hook up. Some co-stars are written as conceited and will rebuff you.
- **On-set situations** — scripted events you resolve by choice. Some are director requests, including illicit ones (drugs), which move **reputation** hard.
- **Perform stunts**
- **Eat exotic foods** (flavor event)
- **Publicity stunts** to promote the project

## 1.5 The output layer

- **Fame** — a percentage stat that unlocks on your first role. Maintained by social-media posting, commercials, photo shoots and talk shows (the latter two gate at ~50% fame), and book writing. It **decays if neglected**. The influencer path tags you as famous around **300,000 followers**.
- **Reputation** — a parallel stat, separate from fame. Bad on-set behavior tanks it; awards raise it. Gates access to better roles.
- **Bitcademy Awards** — Best Picture / Best TV Show and Best Actor / Best Actress (plus supporting categories). **Best Actor is reserved for leading roles.** Nominations follow from several completed projects with good performance, critical reception, and box-office success. Winning gives a large fame + reputation boost and an acceptance-speech beat.
- **Achievements** — a set of acting-specific unlockables.

## 1.6 The loop, compressed

```
raise Looks + Acting skill  →  scroll a job list  →  RNG audition  →
tap 3-5 on-set buttons  →  age up  →  Fame/Reputation tick  →  maybe an award
```

---

# PART 2 — WHAT'S MISSING

The pack is charming and it is *thin*. Six specific structural gaps, and each one is a design opportunity:

**1. Skill is a single scalar.** "Acting: 92%" collapses technique, screen presence, physicality, voice, and instinct into one bar you raise by tapping the same button. There is no such thing as being *wrong for a part* in an interesting way.

**2. Your performance and the project's success are the same event.** In BitLife, a good roll means a good movie. In reality — and in any interesting simulation — you can give the performance of your life in a film that a director ruins in the edit, or coast through a franchise blockbuster. **Decoupling these two is the single highest-value change.**

**3. Nobody remembers anything.** Directors, casting directors, co-stars and critics are disposable text. There is no persistent industry that knows who you are, owes you a favor, or holds a grudge.

**4. There is no opportunity cost.** One role per year, roles are offered or not. You never have to turn down the prestige indie because it shoots during the franchise sequel.

**5. Fame is one number and it only goes up or decays.** No distinction between "beloved," "respected," "bankable," and "notorious" — four things that trade off constantly and that different gatekeepers weight differently.

**6. The industry is static.** Genres don't rise and fall. There's no era shift, no streaming disruption, no moment where the persona you spent twenty years building stops being what the market wants.

---

# PART 3 — CALLBACK: DESIGN OVERVIEW

## 3.1 Pitch

> A career simulator where you play one actor from their first student film to their last. You do not control whether the movie is good. You control what you say yes to, how you prepare, who you keep in the room, and what you're willing to trade. The industry remembers everything, and it changes shape underneath you.

## 3.2 The five pillars

| Pillar | What it replaces in BitLife | One-line statement |
|---|---|---|
| **1. The Performance / Project split** | fused success roll | Your work and the film's fate are separate rolls that only partially correlate. |
| **2. The Persona** | acting skill % | You are not "good at acting," you are *a particular kind of presence* the market prices. |
| **3. The Rolodex** | anonymous NPCs | A persistent graph of ~40 industry figures with memory, careers, and agendas. |
| **4. The Calendar** | one role per year | Time is the scarce resource. Every yes is a no. |
| **5. The Era** | static world | The industry mutates on a 10–15 year cycle and can obsolete you. |

## 3.3 One spine, many careers

Actor, director, and studio executive are three games. They are playable in the same run,
simultaneously or in sequence, and they are only worth building because **they share one
spine** rather than being three parallel systems bolted together:

| Shared system | Actor | Director | Studio |
|---|---|---|---|
| **Standing** (Heat / Prestige / Affection / Notoriety) | your market value | your financing power | your board's patience |
| **Legibility** (the typecasting engine) | Persona — what roles you get | Signature — whether studios will hire you | Brand — what films you're expected to make |
| **The Rolodex** | who casts you | who finances you | who sells to you |
| **The Calendar** | which role you take | which film gets made | which slot on the release grid |
| **Leverage** (Part 6) | favours, indispensability, approvals | favours, final cut, packaging | capital, release dates, talent deals |
| **The Work** (Part 5) | performance dials, contrast, signature | the palette, coherence, the edit | which films get to be difficult |

Career switching is therefore not a mode change: your Rolodex transfers at **100%**,
Prestige at 60%, Heat at 35%. The relationships you built as an actor are the reason
you can get a first feature financed as a director. That is the single design decision
that makes a multi-career game cohere instead of fragment.

**If a newly added career needs its own version of any of those systems, the design is wrong.**
That rule is the whole scope defence.

And because the spine is shared, **there is no career ladder.** You can start as any of them, add
any of them at any age, hold all of them at once, or drop one for a decade and come back. The only
things gating content are Standing, Favours, Indispensability and money — resources, not
permissions. See §6.7.

## 3.4 The core loop

```
        ┌─────────────────────────────────────────────────────┐
        │  SEASON (one in-game year = 4 quarters)             │
        └─────────────────────────────────────────────────────┘
              │
   ┌──────────▼──────────┐
   │ 1. THE OFFER BOARD  │  Roles surface based on Persona fit,
   │                     │  Rolodex relationships, Standing, Quote
   └──────────┬──────────┘
              │  audition / negotiate / decline
   ┌──────────▼──────────┐
   │ 2. THE DEAL         │  Fee vs. backend, billing, options,
   │                     │  schedule blocks consumed
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │ 3. PREP             │  Allocate weeks: coach, research,
   │                     │  physical transformation, dialect
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │ 4. THE SHOOT        │  Event chain. Chemistry, director
   │                     │  conflict, injury, weather, rewrites
   └──────────┬──────────┘
              │  → PERFORMANCE SCORE (yours, private)
   ┌──────────▼──────────┐
   │ 5. POST & RELEASE   │  Edit can help or hurt you. Festival
   │                     │  vs wide vs dumped vs shelved
   └──────────┬──────────┘
              │  → CRITIC SCORE, AUDIENCE SCORE, GROSS
   ┌──────────▼──────────┐
   │ 6. THE SEASON       │  Awards campaign, press, scandal
   │                     │  management, Rolodex maintenance
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │ 7. RECKONING        │  Standing recalculated. Quote reset.
   │                     │  Persona drift. Body & life costs.
   └──────────┬──────────┘
              └──────────► next season
```

---

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
- a **Fit** penalty in the performance roll
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

Each quarter, generate role listings from active productions in the world sim, at a rate that rises with Standing and your agent's reach and falls hard with age past the mid-40s (§4.9) — offers are lumpy on purpose: some quarters nothing at all comes in, and that has to be possible or the calendar has no downside.

**Offer probability** for role *r* from gatekeeper *G*:

```
StandingScore = Σ (G.weight[m] × Standing[m])          // per 4.3 table

FitScore = 100
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

DirectionMult = 0.86 + 0.0028 · DirectorSkill              // 0.86 – 1.14
ConditionMult = 0.80 + 0.0020 · Condition                  // 0.80 – 1.00
                                                            // Condition from health,
                                                            // burnout, substances

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

The critical structural move — and the thing that makes the whole design work — is that **the film gets reviewed and you get reviewed separately.** BitLife has one number. Callback has `FilmCriticScore` (was the movie good) and `YourNotices` (were *you* good in it). Prestige and awards read `YourNotices`; Heat and money read the box office; the two only partly agree. Everything downstream depends on this split.

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

**Box office — v9: one model, not two.** The original spec carried this shape here *and* a differently-structured one in §8.2 for the studio layer, never reconciled — two box-office models computing different numbers for the same release. This is now the only one, and both actor and studio read it:

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
Legs        = clamp(1.7 + 0.048·(AudienceScore − 50)
                     + 0.032·max(0, z − 70)^1.5, 1.15, 8.0)     // z = AudienceScore + N(0,12);
                                                                 // the extra term is the
                                                                 // legitimate-hit tail — word of
                                                                 // mouth compounding past a
                                                                 // threshold, not just a wider
                                                                 // opening
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

**NPCs have their own arcs.** Directors decline. Your rival wins the award you wanted and then flames out. The producer who blacklisted you at 30 gets fired at 45 and the door reopens. The world should feel like it's running whether or not you're in it.

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
entirely, and two half-descriptions of one system is worse than one description. They're gone.

---

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

There is no meter and no penalty. It's not a morality system and the game never comments. It simply appears at the end, in the obituary, next to the filmography — and for some careers the two lists are the same, and for most they are not.

That's not a mechanic. It's the reason to build the rest of it.

---

# PART 6 — LEVERAGE: PLAYING THE INDUSTRY

## 6.0 The problem this fixes

Read Parts 3 and 4 back honestly and the player is a passenger. Offers arrive; you accept or decline. Even the director career is *develop a project and wait for someone to greenlight it.* Every system in the document so far is the industry acting on you.

That's only half of a career, and it's the less interesting half. The other half is **leverage** — the accumulated ability to make things happen that weren't going to happen. This Part is that half.

### Push and pull — why this doesn't break the decision budget

§0.2 caps the game at ~15 decisions per in-game year, and this Part adds forty-odd actions. Those are not in tension, because there are two different kinds of interaction:

| | | Budgeted? |
|---|---|---|
| **Push** | The game stops and asks you something | **Yes** — this is the ~15/year |
| **Pull** | You open a menu and do something because you want to | **No** |

Pull actions cost nothing in tedium because engaging with them is voluntary. A player who never opens the leverage menu plays a clean, uncluttered career and the game never nags them. A player who lives in it is playing a much richer game. **Breadth belongs in pull. Never in push.**

That principle is what lets this Part be as large as it is, and it should govern anything added later.

## 6.1 The five kinds of leverage

| Type | What it is | How you get it | What it buys |
|---|---|---|---|
| **Favours** | Countable debts specific people owe you | Doing things for them at a cost to yourself | Direct offers, introductions, someone hired |
| **Indispensability** | How badly a project or franchise needs *you specifically* | Being irreplaceable in a role over time | Money, approvals, the holdout |
| **Approvals** | Contractual rights over a production | Negotiated at high Standing, or traded for fee | Script, director, co-star, cut |
| **Public standing** | Affection weaponised in a dispute | A long clean career, or a well-chosen fight | Winning a public argument with a studio |
| **Information** | Things you know about specific people | Being in rooms; years of proximity | Silence has a price; so does speech |

These are deliberately *different resources* rather than one power stat, because they're won differently and spent differently. An actor with enormous Indispensability and no Favours is powerful on exactly one project. An actor with forty years of Favours and no Heat can still get almost anything made.

## 6.2 Favours — the currency

Favours are tokens attached to named people, not a pool.

```
You gain a favour from an NPC when you do something that costs you and helps them:
    take scale to be in their small film          +2
    do a day on their project as a favour         +1
    publicly defend them during a scandal         +3
    recommend them for a job they get             +2
    hold the picket line beside them (§10.2)       +2
    hire them when nobody else would              +3

Favours are spent, and they're gone:
    a direct offer with no audition               −2
    they attach to your project (financing!)      −3
    they hire someone you name                    −2
    an introduction to someone in their circle    −1
    they publicly back you in a dispute           −3
```

Favours decay slowly (one per five years of no contact) and die with people. A twenty-year friendship with a director who then dies is a real loss with real mechanical weight, which is roughly how it feels.

## 6.3 Approvals — the contractual levers

Negotiable terms that turn into gameplay verbs. Each is won at a Standing threshold or bought by cutting your fee.

| Approval | Threshold | What it lets you do |
|---|---|---|
| **Script approval** | Prestige 60 | Force a rewrite; block a change you hate |
| **Director approval** | Standing 65 | Veto a director; name one you want |
| **Co-star approval** | Standing 70 | Block casting; bring your own people in |
| **A seat in the edit** *(v9, actor-scoped)* | Your own production company, or Standing 58 | Shift a finished film's Notices and Ensemble by a small, bounded amount before release — real influence over the cut, well short of the authority below |
| **Final cut** (director) | Prestige 70 | §7.7 — the whole game for a director |
| **Pay-or-play** | Any, costs fee | Paid whether or not it happens |
| **Marketing consult** | Standing 75 | Change the campaign, the poster, the trailer |
| **Release approval** | Standing 85, rare | Block a dump; force a real release |

*(v9 note on the row above: phase 0's actor-only build needed a fourth approval alongside script/director/co-star and initially just called it "cut," informally borrowing the director's Final Cut language for something much smaller — an actor lobbying the edit, not controlling it. It's named and scoped properly here instead of left ambiguous between the two. Earned two ways: build a production company (§8), or be successful enough on your own that editors already expect you in the room.)*

Approvals are the reason to take less money, and the game should make that trade legible: a fee cut of 30% for script and co-star approval is often the highest-value decision available.

## 6.4 Indispensability — becoming irreplaceable

The number that makes a franchise need you.

```
Indispensability = 0.35 · CharacterIdentification
                 + 0.25 · min(100, 22 · installmentsStarred)
                 + 0.20 · clamp(50 · (yourStarPower / castAverage), 0, 100)
                 + 0.20 · contractualHold           // approvals + options you control

CharacterIdentification grows with installments, with your Notices in the role,
and with the character's memorability. It is how fused you are with the part
in the public's head.

RecastCost = 0.55 · Indispensability
    → an AudienceScore penalty the studio eats on the next installment if they replace you
```

**Verified across a franchise run:**

| Installment | CharacterID | Indispensability | Recast cost | How the studio sees you |
|---|---|---|---|---|
| 1 | 18 | 27 | 15.0 | Recasts freely |
| 2 | 33 | 40 | 22.2 | Reluctant |
| 3 | 48 | 54 | 29.5 | Expensive |
| 4 | 63 | 67 | 36.7 | Unthinkable |
| 5 | 78 | 77 | 42.6 | Unthinkable |
| 6 | 93 | 83 | 45.7 | Unthinkable |

You are replaceable for two films and irreplaceable by the fourth. **That gap is the whole arc of franchise power**, and it means the interesting decisions cluster around installments three and four — exactly where real contract disputes happen.

**v9 — Indispensability has to be able to fall all the way to zero, or the property never lets you go.** Every property has a natural ceiling (§9.5) — nobody makes eleven of them with the same person, and past the last one the studio reboots without you. Phase 0's implementation modelled that reasonably (a decay term, faster once you've been rebooted past) but gated the *entire* decay-and-release calculation behind "Indispensability still above 30," on the theory that only a genuinely high number needed tracking closely. It doesn't: a reboot's own decay routinely drops the number from comfortably above 30 into the 12–30 band in a single step, and once inside that band the gate that runs further decay never reopens — the number simply stops moving, forever, and a franchise that's supposed to be over stays open, silently blocking every franchise after it for the rest of the career. This is Part 15's own risk item — *"every hard system needs a real exit"* — failing in the one place it was actually implemented. The fix is structural, not numeric: decay (and the eventual release once it crosses a floor) must run at every level of Indispensability once a property is live, not only while it's still high. Only the *perks* of being indispensable — the floor under Heat, the recast cost — are correctly gated to a high number; the exit never should have been.

## 6.5 Franchise influence — fifteen ways in

The worked example, because it's the richest case. Every one of these is a pull action available to an actor inside a franchise.

### Getting more out of it

| Action | Requires | Effect |
|---|---|---|
| **Hold out** | Indispensability | See below — the marquee gamble |
| **Trade fee for gross points** | Standing 60 | Uncapped upside; you eat the risk |
| **Take merchandising points** | Any — nobody asks for them | On a toy-driven property this is the largest single payday in the game (§9.7) |
| **Get approvals written in** | Standing 65+ | Script, co-star, director |
| **Negotiate a shorter option** | Standing 55 | Frees calendar years — worth more than money if the material is good |
| **Negotiate your character's death** | Any | The exit. Cash, closure, and you never come back — unless they need you back |

### The holdout

Refuse to sign for the next installment. The marquee manipulation, and a genuine gamble.

```
P(they pay)   = 0.85 · sigmoid(0.085 · (Indispensability − 58))
                // capped at 0.85 — studios call bluffs, because caving to you
                // sets a precedent across their entire slate
Otherwise:  65% they recast or write you out, 35% they delay and you go again

Raise on success = ×(1.35 + 0.013·(Indispensability − 50)), capped at ×2.40
Cost of failure  = the franchise income, Notoriety +15,
                   and every gatekeeper marks you difficult
Repeat holdouts get harder: −8 Indispensability effect per prior holdout
```

**Verified payoffs**, in units of your remaining franchise income:

| Indispensability | P(they pay) | P(you're out) | Raise | Expected value | Correct play |
|---|---|---|---|---|---|
| 40 | 0.15 | 0.55 | ×1.35 | 0.53 | Sign |
| 60 | 0.46 | 0.35 | ×1.48 | 0.89 | Sign |
| **70** | 0.62 | 0.24 | ×1.61 | **1.15** | **Hold out** |
| 80 | 0.74 | 0.17 | ×1.74 | 1.38 | Hold out |
| 90 | 0.80 | **0.13** | ×1.87 | 1.57 | Hold out |

You have to genuinely *be* the franchise before this is right — and even at 90 there's a **13% chance you lose the role entirely.** It never becomes free money, which is what keeps it a decision instead of a button.

### Taking it over

| Action | Requires | Effect |
|---|---|---|
| **Executive producer credit** | Indispensability 55 | A seat in the room. Small backend, real information. |
| **Producer** | Indispensability 70 + a favour | Casting input, script input, you're in the greenlight conversation |
| **Direct an installment** | Director Standing 45 + Indispensability 65 | The clean crossover. You know the property better than anyone they could hire. |
| **Creative custodian** | Producer + 4 installments | The studio consults you before anything happens to the property. Effectively a veto without a contract. |
| **Buy the rights** | Money, and a distressed studio | Late-career. It's yours. Do what you want. |

### Shaping it from inside

| Action | Cost | Effect |
|---|---|---|
| **Bring in your director** | 3 favours | Their DirectionMult on a tentpole budget — a rare combination |
| **Cast your roster** | Co-star approval | Chemistry bonuses, and you've made four people owe you |
| **Push for a spin-off** | Producer + audience test | Your character, your film (§9.5) |
| **Champion a newcomer** | 1 favour | Twenty years later they're a star who owes you |
| **Refuse to promote** | Notoriety +12 | Opening −15%. It hurts them more than you, and everyone knows why |
| **Publicly criticise the film** | Notoriety +20, Affection ±20 | Nuclear. Sometimes it's the only honest thing left |
| **Return for the legacy sequel** | Being alive and remembered | Decades later, you hold *every* card (§9.5) |

## 6.6 The action catalogue

Everything else you can initiate. All pull, none of it prompted.

### Get work that wasn't offered you

| Action | Cost | Effect |
|---|---|---|
| Publicly campaign for a role | Notoriety +6 if you don't get it | Forces an audition you weren't going to get |
| Screen-test for free | A block | Bypasses the Standing term in §4.4 entirely |
| Take scale to work with someone | The fee | +2 favours, big Rolodex affinity, a genuine Craft gain |
| Attach yourself and shop it | A block + money | *You* become the package. Financing follows you, not the script. |
| Option material yourself | Money | Develop a role that doesn't exist yet |
| Call in a roster favour | 2 favours | A direct offer, no audition |
| **Sign with a bigger agency** *(v9)* | Standing clears the next tier's bar | Moves you one agent tier up (§4.5) — the missing rung: nothing else in the original design ever moved this stat, which meant a Regional Stage start had no representation for an entire career and nobody, ever, could reach Powerhouse to use the row below |
| Ask your agency to package | Powerhouse agent | Guaranteed offer, no audition, 15% forever |

### Change a project you're on

| Action | Cost | Effect |
|---|---|---|
| Request a rewrite of your part | Goodwill | `Fit` +, or `ScriptQuality` − if you're wrong about your own part |
| Recommend a co-star | 1 favour | Chemistry +, they owe you |
| Block a co-star | Co-star approval | Avoids a chemistry disaster; makes an enemy |
| Get your crew hired | 1–2 favours | Unit bonuses on someone else's film |
| Push for a different director | Director approval | The single biggest swing available to an actor |
| Improvise against the script | Director's patience | High variance; rewards Instinct |
| Refuse a scene | Notoriety +5, director affinity − | You can always say no. It always costs. |
| Go over the director's head | Burns them permanently | Sometimes the film is worth it |

### Change your own standing

| Action | Cost | Effect |
|---|---|---|
| **Disappear** | Heat decay, no income | See below |
| A season of theatre | 2 blocks, no money | Prestige ++, Craft +, Heat − |
| Franchise paycheck to fund an indie | Your own money | The most common real strategy in the industry |
| Publicly turn down something famous | Burns that studio | Affection +, Prestige + |
| Start a feud | Notoriety both ways | Visibility for two. Sometimes both careers benefit. |
| Court a critic | Years of cultivation | One critic's noise term skews your way, permanently |
| Write a memoir | A block | Money, Affection, and you can burn someone in it |
| Change your name and reinvent | Everything you built | Persona reset. Occasionally the only move left. |

**Disappearing** deserves its own numbers, because it's a strategy real actors use and no game models:

```
After 4+ consecutive quarters not working:
    Heat decays normally (you are being forgotten)
    Scarcity += 6 per quarter, capped at 40
On return:
    offer QUALITY tier available     +0.4 · Scarcity
    first offer's fee                ×(1 + 0.010 · Scarcity)
```

Two years away costs you roughly 18 Heat and buys you materially better material when you come back. Whether that's a good trade depends entirely on whether the Heat was buying you anything worth having.

### Change other people

| Action | Cost | Effect |
|---|---|---|
| Mentor a newcomer | A block a year | In twenty years they may be the most powerful person you know |
| Recommend someone | Your credibility | They owe you 2 favours; it costs you if they're bad |
| Broker a reconciliation | 2 favours | Both parties owe you 3. The best trade in the game if you can spot it. |
| Publicly defend someone in a scandal | Notoriety +10 | +3 favours and a loyalty that outlives most careers |
| Poach a crew member | Money | Their old director never forgets |
| Blacklist someone | Requires real power | It works. It also tells everyone what you are. |
| Leak something | Information | Effective, deniable, and information spends only once |

### Change the market

| Action | Cost | Effect |
|---|---|---|
| Demand a release date change | Approval or leverage | Dodge a rival tentpole (§8.6) |
| Push for a festival premiere | Producer input | Trades opening weekend for a critic reveal (§10.3) |
| Fund your own awards campaign | $400K–$3M + a block | §4.11 |
| Buy back your own IP | Money | You own the thing you're famous for |
| Time your return to a genre boom | Reading the cycle | §9.3 — the payoff for paying attention |

### Change the rules

| Position | How you get it | What it lets you do |
|---|---|---|
| **Guild officer** | Elected; needs standing among peers | Set residual policy, call or settle a strike (§10.2). You are now on the other side of a decision that shaped your own career. |
| **Festival juror** | Prestige 70 + an invitation | You decide who wins. Every filmmaker in competition now has a relationship with you. |
| **Studio board seat** | Money or a favour from a mogul | Vote on greenlights. Fire an executive. |
| **Teacher / conservatory** | Late career | Your students become the next generation. In fifteen years, your Rolodex is the industry. |
| **Production company owner** | Prestige 45 | Develop anything, for anyone, including yourself |

Positions are not careers. They cost a fraction of a block and they grant levers, so a player can hold several at once alongside whatever they're actually doing.

## 6.7 No paths, no prerequisites

The document has been implying a progression — actor, then director, then studio. **Delete that idea.** There is no ladder.

- **Start as anything.** First run can begin as a 24-year-old director who has never acted, or a 30-year-old with family money starting a production company.
- **Add anything, any time.** Direct your first film at 58. Act for the first time at 61 after a producing career. There is no gate saying *you must first*.
- **Hold everything at once.** Act in someone else's film in Q1, direct your own in Q2–Q3, and sit on a festival jury in Q4. The calendar is the only limit, and that's the correct limit.
- **Drop anything.** Stop acting for a decade. The Rolodex doesn't expire, and re-entry is a real arc rather than a locked door.

The only things that gate content are **Standing, Favours, Indispensability, and money** — all of which are earned in many different ways, and none of which care how you got them. That's what makes the game open rather than branching: the requirements are resources, not permissions.

## 6.8 Three worked routes to the same power

The point of a wide verb set is that it produces different-shaped careers that arrive at comparable places. Sketches:

**The Indispensable One.** Take a franchise lead at 26. Sign a cheap five-picture deal because you have no leverage. Build CharacterIdentification for three films while your quote stays fixed and you quietly resent it. At installment four, Indispensability 67 — hold out. They pay. Take gross points and co-star approval instead of a bigger fee. Use approval to cast your roster. Direct installment six. By 40 you're the creative custodian of a property worth more than the studio that owns it.

**The Favour Bank.** Never get very famous. Work constantly, take scale for people you believe in, defend two friends through scandals nobody else would touch, mentor four newcomers in your thirties. Heat never passes 45. At 52, one of your mentees runs a studio and another is the most in-demand director alive, and you can get any film financed by making three phone calls. You have no power the game ever displayed as a number.

**The Disappearing Act.** Enormous at 29, typecast at 33, miserable. Vanish for three years. Heat collapses from 80 to 30; Scarcity hits 40. Come back into a prestige indie for scale with a director who owed you nothing and said yes anyway. Notices at 88. Persona Legibility drops from 84 to 51 — you're readable as something else now. Spend the rest of your career as an actor people describe as *interesting*, which is worth more at 50 than Heat ever was.

None of these is the intended path. That's the point.

---

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

# PART 8 — THE STUDIO

> **This is an optional mode, and it should be built last or shipped separately.**
> The studio layer is a strategy game wearing a life sim's clothes — slate portfolios, release-date
> warfare, quarterly board pressure. It's good, and it does not belong in the critical path of
> someone playing an actor. Reachable through the fiction (a vanity production company is a
> natural thing for a successful actor to start), never forced, and skippable forever without
> the rest of the game feeling incomplete.

The business layer. Playable as a third career, or as a light overlay you acquire while acting or directing.

## 8.1 Getting one

| Stage | How you get here | What you can do |
|---|---|---|
| **Vanity production company** | Any actor/director with Prestige > 45 | Produce your own projects, take producer credit and points |
| **First-look deal** | Standing > 60; a studio funds your overhead | They get right of first refusal; you get development money |
| **Independent producer** | 3+ produced films | Finance from outside; full slate control at small scale |
| **Mini-major** | $200M+ capital | 6–10 film slate, own distribution in some territories |
| **Studio** | $1B+ capital or acquisition | Full slate, global distribution, IP library, a board that can fire you |

## 8.2 The slate — verified economics

The single most important thing a studio does is choose a *portfolio*, and the numbers have to make that a real dilemma. Tuned across 15,000 films per tier:

| Tier | Budget | Median ROI | % profitable | P(>2× ROI) | Character |
|---|---|---|---|---|---|
| **Micro** | $4M | 1.24 | 80%\* | 7.6% | Cheap, safe per-dollar, trivial absolute upside |
| **Low** | $12M | 1.03 | 55% | 5.3% | The genre-film workhorse |
| **Mid** | $30M | 0.99 | 48% | 5.4% | The endangered middle |
| **Upper** | $60M | 0.95 | 42% | 6.2% | Worst risk-adjusted tier in the game |
| **Tentpole** | $170M | 0.95 | 44% | 12.9% | Low median, fat tail, enormous absolute dollars |

\* *Micro's 80% is before the distribution gate — see §10.3. Roughly 30% of micro-budget films never find a distributor and return zero, bringing effective profitability to ~56%.*

**Slate outcomes** (4,000 simulated studio-years):

| Strategy | Capital at risk | Median year | P(profitable year) | p10 | p90 |
|---|---|---|---|---|---|
| **Balanced** (1 tent, 2 upper, 3 mid, 4 low) | $428M | +$38M | 60% | −$103M | +$423M |
| **Blockbuster** (3 tent, 4 upper, 3 mid) | $840M | +$170M | 69% | −$171M | +$805M |
| **Indie** (2 mid, 4 low, 4 micro) | $124M | +$18M | 78% | −$9M | +$74M |

Read that carefully, because it's the studio game in one table: **the indie strategy is by far the safest and can never make you big. The blockbuster strategy has the best expected value and can lose $171M in a bad year — enough to get you fired.** Both are correct answers to different questions, which is what a good strategic choice looks like.

The updated box-office model behind those numbers:

```
Marketing(b) = 0.35b if b<10 ; 0.48b if b<50 ; 0.55b if b<100 ; 0.80b otherwise

Opening = Budget × (0.80 + 0.004·CastStarPower + 0.005·GenreDemand)
                 × (Budget/30)^−0.10        // small films punch above their weight

Zeitgeist = AudienceScore + 0.5·(GenreDemand − 50) + N(0, 12)   // "did it catch on"
Legs      = clamp(1.7 + 0.048·(AudienceScore − 50)
                      + 0.032·max(0, Zeitgeist − 70)^1.5, 1.15, 8.0)

Gross = Opening × Legs
```

The `Zeitgeist` term is what makes breakouts possible. It's deliberately *not* pure quality — a film catches on for reasons partly outside the film. Without it the model had no fat tail and every studio went bankrupt; with it, one film in twenty pays for the slate. That's the actual shape of the business.

Studios also greenlight *on purpose*: budget correlates with the demand and star power you buy with it (`CastStarPower ~ N(35 + 0.19·Budget, 16)`, `GenreDemand ~ N(52 + 0.10·Budget, 13)`) and, pointedly, **with worse scripts** (`ScriptQuality ~ N(62 − 0.020·Budget, 14)`). Tentpole screenplays are compromised by committee. That single negative coefficient generates most of the texture in the tier table.

## 8.3 The financing stack

**Three presets, one meaningful override.** Assembling six funding sources per film is an accountancy minigame; you'd do it forty times and it would have a right answer by the fifth.

| Preset | What you trade |
|---|---|
| **Studio-financed** | Full budget, no personal risk, they own it and can recut you |
| **Independent** | You assemble it, you keep final cut and the upside, and it may collapse before a frame is shot |
| **Streamer buyout** | Budget plus 20% guaranteed, no backend, no theatrical, no box-office story to tell |

Then **one override that actually matters** — almost always the tax-credit location trade: shoot somewhere cheaper for a 25–40% rebate and eat a `ProductionValue` penalty plus a `chaos` bump, or pay for the real place.

The full stack still exists underneath, and a player who wants to see it can:

| Source | Cost | Notes |
|---|---|---|
| **Equity** | Full risk, first loss | Your money or an investor's |
| **Territory presales** | Discount to face value | Sell Japan and Germany before you shoot (§10.4) |
| **Tax credits** | Free money | **Tied to shooting location** — 25–40% rebate, but the location changes `chaos`, crew quality, and cast willingness |
| **Gap debt** | Interest | Borrowed against unsold territories |
| **Completion bond** | 2–4% of budget | Guarantees delivery. **Refuses to cover uninsurable talent** (§11.2) |
| **Streamer buyout** | Full budget + 20% | No backend, no theatrical, no box-office glory. The devil's bargain of the Streaming era. |

Location-for-tax-credit is a lovely decision: shoot the New York story in a cheaper city for a 35% rebate, and eat a `ProductionValue` penalty plus a `chaos` bump — or pay for authenticity.

## 8.4 The script market

A rolling pool of available screenplays with `TrueQuality` hidden behind your **Taste** (§7.2 — the same noise formula applies to studio executives). Specs go to auction; rivals bid. Buying a great script cheap because you read it right is the purest expression of taste-as-skill in the game.

Options expire. Scripts rot in turnaround. Another studio's abandoned project can be picked up for pennies and become your best film of the decade.

## 8.5 IP and franchises

> **Superseded by Part 9**, which replaces the v1 sequel curve with one fitted to real box-office
> data, and adds source material, shared universes, merchandising and tie-ins. Keep this section
> only as the studio's balance-sheet view: rights are assets. They can be bought, sold, lost in a
> bankruptcy, or frozen for years in a rights dispute — and a studio's library is often worth more
> than its slate.

## 8.6 Release date warfare

Every studio claims release dates on a shared calendar, visible to everyone, a year or more ahead.

```
If two films with GenreDemand overlap > 60 open within 2 weeks:
    both take Opening × 0.78 and Legs −0.3
```

You can **stake a date early** to scare rivals off, **blink** and move (costing marketing already spent and signaling weakness), or **play chicken.** Counter-programming — deliberately opening a small drama opposite a tentpole — gets `Opening × 1.12` if genre overlap is under 25%. Real, legible, and the kind of thing players will talk about.

## 8.7 Talent deals

| Deal | Cost | Effect |
|---|---|---|
| **First-look** | Overhead, ~$1–4M/yr | Right of first refusal on their projects |
| **Holding deal** | Retainer | An actor can't work elsewhere; you may never use them |
| **Output deal** | Guaranteed slots | A director owes you N films; guarantees supply, forfeits selectivity |
| **Pay-or-play offer** | Full fee at risk | Locks a star before financing closes — aggressive and sometimes ruinous |

## 8.8 Rivals

3–5 rival studios run the same simulation you do, with distinct strategies (blockbuster machine, prestige boutique, volume streamer, distressed legacy studio). They bid against you at auctions, poach your first-look talent, claim your release dates, and can be acquired or can acquire you.

## 8.9 The corporate layer

If you run a studio, you have a **board**, and the board has a memory shorter than a film's development cycle. This is the studio game's version of the actor's age cliff — the structural pressure you cannot solve, only manage.

```
ExecutiveStanding += f(trailing 3-year slate ROI, prestige wins, franchise health)
If ExecutiveStanding < 25 for 2 consecutive years → fired.
```

Getting fired isn't game over: you land at another studio, or go independent with your relationships intact — and your greenlit slate stays behind for your successor to take credit for. Which happens constantly and is very funny.

Also here: conglomerate parents with priorities unrelated to film, hostile takeovers, library sell-offs to cover a bad year, and the quarterly-earnings pressure that makes a studio cancel a finished film for a tax write-off. That last one should be available as an event, and it should feel exactly as bad as it does in reality.

---

# PART 9 — GENRES, FRANCHISES, AND THE TIE-IN ECONOMY

Everything in this Part is about one idea: **a film is not the product. A film is the thing that creates the product.** Star Wars has taken $10.3B at the box office and $32B in merchandise — the movies are 22% of the franchise. Any simulation that stops at the box office is missing three quarters of the business.

## 9.1 Genres are economies, not labels

Right now the doc treats genre as a modifier on a critic score. It should be a different game per genre. Each one has its own budget norms, profit shape, award ceiling, and effect on your career.

| Genre | Typical budget | Profit shape | Critics | Award ceiling | What it does to a career |
|---|---|---|---|---|---|
| **Horror** | $3–20M | **Best in the game.** ~173% average ROI; 16 of the 50 most profitable films ever | −5 | Very low | Builds a fanbase that never leaves. Hard to escape. |
| **Comedy** | $20–50M | Reliable, rarely huge | −4 | Low | Highest Affection gains; critics never respect you |
| **Drama** | $10–40M | Poor | +4 | **Highest** | Prestige-dense, money-poor |
| **Action** | $80–200M | High variance | −3 | Low | Physicality gate; ages out hardest |
| **Thriller** | $20–60M | Solid middle | +1 | Medium | The safest lane for a working actor |
| **Sci-fi** | $60–200M | Very high variance | 0 | Medium | Big merchandise upside |
| **Romance** | $15–40M | Moderate | −2 | Low | Affection engine; brutal age curve |
| **Animation** | $80–180M | Good, and **the biggest merchandise multiplier in the game** | +2 | Separate category | Voice work — no Look gate, no age cliff |
| **Musical** | $50–150M | Boom and bust | +3 | High | Hard Voice gate; era-dependent |
| **Period / war** | $40–120M | Poor to moderate | +5 | High | Prestige machine, expensive to make |
| **Family** | $50–150M | Good | −2 | Low | Merchandise engine; content restrictions |

### Why horror matters more than it looks

Horror's numbers are real and extreme, and they create the design's most important on-ramp: **it is the one genre where a nobody with no Standing can make a film that actually works.** Budgets are small enough to self-finance, the audience doesn't care about stars, and critical failure barely dents the returns.

So horror should be where struggling actors and first-time directors go, and it should genuinely work — while also being the hardest lane to leave. A horror star at 40 with high Legibility and low Prestige is a real, common, and interesting place to be stuck.

## 9.2 Subgenres and hybrids

Each genre holds 4–6 subgenres with their own demand cycles — horror splits into slasher, supernatural, folk, body, found-footage, elevated. Subgenres boom and die faster than genres do.

**Hybrids** average the demand of both parents, take a −8 marketing penalty (harder to sell in one sentence), and get a +6 critic bonus if `ProjectQuality > 70`. So a horror-comedy is harder to open and easier to love — which is why they're rare and why they become cult films (§9.9).

## 9.3 Genre cycles — the boom and the bust

The most important addition in this Part. Genres are not stable; they surge after a hit, flood with imitators, and crash.

```
Every quarter, for each genre g:

    GenreHeat[g] ×= 0.88
    GenreHeat[g] += 30   for every film in g that returned ROI > 2.5

    greenlit[g] = 1.0 + 1.2 × (GenreHeat[g] / 25)
        → those films release 8 QUARTERS LATER        ← the lag is the mechanic

    GenreDemand[g] += 0.30 × GenreHeat[g] / 4        // appetite grows
                    − 2.00 × (released[g] − 1.0)     // saturation
                    + 0.045 × (58 − GenreDemand[g])  // appetite recovers in absence
    GenreDemand[g] clamped to [15, 95]
```

**Verified over 400 genre-histories of 60 years each:**

| Metric | Result |
|---|---|
| Time spent in boom (demand > 70) | **5%** |
| Boom years per 60 | median 3 |
| Bust years per 60 (demand < 48) | median 14 |
| Demand standard deviation | 10.0 |
| Genres booming at any given moment (of 11) | **~0.5** |

So a genre boom is a notable event that happens every few years somewhere in the industry, and a *bust* is the ordinary condition — most genres spend most of their time below their own baseline, recovering. Sample 60-year traces:

```
++++++++++++***+========++*#*+==--======++*++***+=-----=+==-
++++++++++++***#**+=------=++==++====+==-=+++**+---==------=
++++++++++++***++++===========++++++++**++=======+**+**##%#+
```

**Two failure modes to avoid**, both of which I hit while tuning. A weak saturation term sends demand into a death spiral — it collapses to the floor and never recovers, because nothing restores appetite. A weak greenlight response makes demand ratchet upward forever and never crash. **You only get real busts when the imitator flood genuinely overshoots**, which needs both a strong saturation coefficient and a strong greenlight response. The recovery term is what stops the spiral.

**The lag is the mechanic.** A film takes roughly two years from greenlight to release. So the imitators that a hit inspires arrive exactly when the audience has moved on. Chasing a boom is almost always wrong and always tempting — and the studios who read the cycle correctly buy in *during* the bust, when the genre is cheap and nobody wants it.

This is not theoretical. In 2000, one of the top ten films was a franchise sequel. By 2022 it was all eleven of the top eleven. Then the same trend reversed. A player should be able to live through a full cycle and feel it.

## 9.4 Where scripts come from — the adaptation market

Original screenplays are one source among many, and the others come with an audience attached.

| Source | Rights cost | Built-in audience | Catch |
|---|---|---|---|
| **Original screenplay** | Cheap | None | You're selling an idea, not a name |
| **Novel** | Moderate | Small, loyal | Author has opinions and sometimes approval |
| **Comic / graphic novel** | High | Large, vocal | Fidelity pressure is severe |
| **Video game** | High | Large, young | Historically a graveyard; the market is currently reversing |
| **True story** | Life rights (see below) | Moderate | The real person is an NPC |
| **Stage play** | Moderate | Prestige audience | "Stagey" critic risk |
| **Foreign remake** | Low–moderate | None domestically | The original's fans will compare, loudly |
| **Toy line / brand** | Very high, or free with strings | Enormous | See §9.7 — the toy company gets creative input |
| **Public domain** | Free | Everyone knows it | So does every rival studio |

### Fidelity: pick your approach

```
faithful      → +12 fan goodwill, −4 critic ("inert", "reverent")
loose         → +6 critic upside, 40% chance of fan backlash
in-name-only  → no fan bonus, no backlash, and you paid for a title
```

**Fan backlash** is its own event: `Notoriety +10`, and a review-bombing effect that knocks `AudienceScore` down by 6–14 *without any relationship to how good the film is.* That's a useful wedge — it lets a genuinely good film be publicly hated for reasons outside quality, which happens constantly and which no reception model usually captures.

### Life rights

For true stories you must acquire rights from the real person or their estate. They're an NPC with opinions about their own portrayal, approval over the script, and the ability to walk mid-production and take the rights with them. Playing a living person who is watching you play them is a great source of scenes and a real production risk.

## 9.5 The shapes a franchise can take

The v1 sequel curve was wrong. Real data shows the **first two installments usually out-earn the third**, and audience reception bottoms out around the fifth or sixth. Corrected:

```
SequelBonus(n) = base[n] × (priorAudienceScore / 65)

base = { 1st sequel: +32,  2nd: +30,  3rd: +20,
         4th: +12,  5th: +6,  6th: +2,  7th+: 0 }
```

So the first sequel is usually the most profitable film in a franchise, the well runs dry around six, and quality-of-the-last-one gates everything.

| Type | How it works |
|---|---|
| **Straight sequel** | The curve above |
| **Prequel** | Younger cast — either recast (fan risk) or de-age (only in later tech eras, expensive) |
| **Legacy sequel** | Bring the original cast back decades later. Large nostalgia bonus (+25), **but you need those actors**, and they now know exactly what they're worth |
| **Reboot** | After 8+ years dormant, restores the counter at 60% |
| **Spin-off** | A supporting character gets their own film |
| **Crossover** | Two franchises meet. Demand adds, then both decay faster afterward |
| **Anthology** | Same world, new cast each time. No actor leverage — which is precisely why studios love it |

### The spin-off is the supporting actor's lottery ticket

If your supporting character tests well with audiences, the studio may spin them off. For a supporting player this is the single best thing that can happen: your billing jumps to lead, your Quote roughly triples, and you skip the entire climb.

```
P(spin-off) = sigmoid(0.09·(YourNotices − 70) + 0.06·(AudienceScore − 60)
                      + characterMemorability)
```

It also traps you. The character becomes most of your Persona, and Legibility spikes.

## 9.6 Shared universes

Several franchises sharing continuity. Distinct enough from a normal franchise to need its own rules.

- **Interlock.** Entries reference each other. A bad entry damages demand for *every* film in the universe, not just its own sequels.
- **Multi-picture deals.** Actors sign for 3–7 films at once. This is the actor's version of a trap: you signed at your year-one Quote, and by film three you're worth six times that with no way to renegotiate — except publicly, expensively, and at the cost of every relationship on the project. Some of the most famous contract disputes in film history are exactly this, and it's a good decision to hand a player.
- **Scheduling.** Universe films lock calendar blocks *years* ahead. Your best years get pre-spent.
- **Fatigue.** Each additional entry raises the universe's demand decay rate by 4%.
- **Collapse.** Two consecutive entries below ROI 0.7 halves universe demand. Recovery takes a decade or a reboot.

## 9.7 Merchandise — where the money actually is

The headline: **Star Wars has grossed $10.3B in theatres and $32B in merchandise.** Films are 22% of franchise revenue. Lucas famously traded his $500K directing fee for the merchandising rights, which is arguably the best financial decision anyone has made in the industry.

```
MerchRevenue = Gross × MerchMultiplier × BrandStrength

MerchMultiplier by property type:
    Toy-driven family / animation      1.5 – 3.2 ×
    Sci-fi / superhero                 0.4 – 1.1 ×
    Action                             0.2 – 0.5 ×
    Horror (apparel, collectibles)     0.05 – 0.2 ×  but a very long tail
    Drama / romance                    ~0
```

**Who owns the merchandising is a negotiable deal term**, and it should sit in §4.5 next to backend points. Trading fee for merchandising points is available to any actor or director on any film. Almost nobody takes it, because it looks like giving up certain money for a lottery ticket. On a toy-driven family film it is not a lottery ticket.

### The tie-in stack

| Tie-in | Effect |
|---|---|
| **Toys** | The big one. Requires toyable characters — which shapes the film itself |
| **Apparel / collectibles** | Small but permanent; horror over-indexes here |
| **Video game** | A rushed licensed game damages the brand (−8 demand). A good one made by a real studio *raises* it (+10) |
| **Novelizations / comics** | Cheap, and **they extend a franchise's life without burning a sequel slot** |
| **Soundtrack** | Modest income; a hit song raises AudienceScore for the whole film |
| **Theme park attraction** | Unlocked at high franchise strength. An enormous permanent annuity that changes what the studio will greenlight forever |

The novelization line deserves attention: **you can keep a franchise culturally alive in comics and books during its 8-year dormancy so the reboot lands harder.** That's a real strategy, it's cheap, and it rewards long-term thinking in a system that otherwise punishes it.

### Toy-driven development

A toy company offers to finance your film. The catch is creative input: mandatory characters designed to be sold as toys, a vehicle in act two, a colour-coded team.

```
Financing: up to 60% of budget, free
ScriptQuality: −12
MerchMultiplier: +1.4
```

That trade is the honest engine behind a lot of films, and putting it in the model explains a certain kind of movie better than any amount of commentary about creative bankruptcy.

## 9.8 Brands, placement, and co-promotion

Real figures: a comprehensive placement program runs **$60K–$250K** for a brand; international brands competing for slots in blockbusters pay **high six to low seven figures**; and studios prioritise partners bringing **co-promotions worth $5M+**.

```
PlacementIncome = f(budget tier, genre fit, audience demographics)
ScriptQuality penalty scales with how intrusive the integration is (−1 to −9)
Brands refuse: violent, sexual, politically charged, or downbeat content
```

**Co-promotion is the important one.** A fast-food chain spends $20M advertising your film for you. That's free marketing budget — but they need a film their customers' children can see.

So brand money mechanically pushes films toward the middle. This is the actual force that makes tentpoles bland, and having it in the model means the game can *show* that rather than assert it.

### Endorsements, for actors

Your Affection converts directly into income. But an endorsement contract carries a morals clause: cross a Notoriety threshold and it terminates, sometimes with a public statement. Some brands also bar you from certain roles for the contract's duration — a soft drink company would rather you didn't play the villain in something ugly.

A high-Affection, low-Prestige actor can out-earn a prestige star by a wide margin without ever being in a good film. That should be a viable, slightly hollow way to play.

## 9.9 The long tail, and the cult film

Films don't stop earning. Theatrical → premium home → streaming → broadcast → library, with each window's value set by the technology era (§10.6). Residuals flow to actors from all of them, which is what makes a deep filmography an income source in old age.

**A film that flopped theatrically can become profitable in the library**, and the actor keeps getting cheques for something everyone agreed was a disaster.

### Cult status

```
If AudienceScore < 45 at release AND FilmCriticScore > 62 (or a strong genre signature),
    accrue cultScore over the following 10–25 years.
At cultScore > 70:
    the film is reappraised. Everyone attached gains Prestige, retroactively.
```

The film that damaged your career at 31 makes you a legend at 58. It's real, it happens constantly, and it gives long careers a shape that short ones can't have.

## 9.10 What each genre buys you

The summary a player actually needs — and the reason genre choice is a career strategy rather than a flavour preference.

| Genre | Money | Prestige | Affection | Career longevity |
|---|---|---|---|---|
| Horror | ●●●● (per dollar) | ○ | ●●● (devoted) | ●●●● |
| Comedy | ●●● | ○ | ●●●●● | ●● |
| Drama | ● | ●●●●● | ●● | ●●●● |
| Action | ●●●● | ● | ●●● | ● |
| Sci-fi | ●●●● | ●● | ●●● | ●●● |
| Animation / voice | ●●● | ●● | ●● | ●●●●● |
| Period / war | ●● | ●●●●● | ● | ●●●● |
| Family | ●●●●● (merch) | ○ | ●●●● | ●●● |

Note the two outliers. **Animation and voice work has the best longevity in the game** because there's no Look gate and no age cliff. **Action has the worst** because Physicality declines from 45 and injuries are permanent. An actor who reads that table at 25 and plans accordingly will have a very different life from one who doesn't — which is exactly the kind of decision this game should be made of.

---

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

# PART 11 — THE LIFE

The half of the simulation that isn't the career, and that determines the career.

## 11.1 Health

Health is not a single bar. It's a set of conditions with onset probabilities driven by age, behavior, work intensity, and luck. Chronic conditions apply permanent modifiers; acute events consume calendar blocks.

`Condition` (the multiplier in §4.7's Performance roll) is derived:

```
Condition = 70 + 0.20·(Health − 50) − burnoutDebt − substanceLoad
          + 0.10·(Resilience − 50)
```

Injuries from stunt work can permanently cap `Physicality`, which retroactively closes an entire lane of roles — an injury at 34 can end the action career and force the pivot to character work a decade early.

## 11.2 Addiction as an arc, not a flag

Stages, each with its own event pool and its own exit:

```
USE → DEPENDENCE → TOLERANCE → CRISIS → { RECOVERY | DECLINE }
```

| Stage | Effect |
|---|---|
| **Use** | `Condition +8` short-term, `−2` accumulating. Social lubricant: small Rolodex bonus at parties. Genuinely works, at first. |
| **Dependence** | `Resilience` −3/yr. Missed call times. First on-set incidents. |
| **Tolerance** | `Condition` net negative. `Notoriety` +6/yr. Directors start noting it. |
| **Crisis** | Public incident. `Notoriety` +25, `Affection` −15, and the mechanic below. |

### Uninsurability

```
At Crisis stage, the completion bond company refuses to cover you.
No financed production can legally cast you.
Only self-financed and micro-budget work remains available.
```

This is the mechanically exact expression of "the industry stopped hiring them," and it is *precisely* how it works in reality — not moral disapproval, an insurance underwriter. It's specific, it's true, it's brutal, and it has a clear path out: **stay clean and insurable for two years and coverage returns.**

**Recovery** costs 2 blocks and money, introduces a sponsor NPC (a strong Resilience anchor, and a relationship you can damage), and carries a relapse probability that decays over years but never reaches zero. It also unlocks the *comeback* narrative bonus (+11) in awards — the industry loves a recovery story, which is its own uncomfortable truth worth modeling.

## 11.3 Therapy, and one deliberate anti-myth

Therapy and medication raise `Resilience`, reduce crisis event frequency, and improve the outcome distribution of scandal responses.

**In-game, several NPCs will tell you that treatment dulls your Instinct — that the pain is where the work comes from. The code applies no such penalty. It is simply false.** Some directors believe it and will say so. A player who avoids therapy for thirty years to protect their gift will have protected nothing.

It's a small thing. It's also the sort of thing a game about this profession should be willing to say plainly.

## 11.4 Family, and the caretaking block

| Relationship | Mechanic |
|---|---|
| **Partner outside the industry** | Conflict events during long shoots and location work; **+Resilience floor**; doesn't understand the ask |
| **Partner inside the industry** | Rolodex access, chemistry bonuses if you work together, **2× scandal exposure**, competing calendars |
| **Children** | Consume blocks; set a Resilience floor; unlock the second-generation start |
| **Aging parents** | **Caretaking consumes 1–2 blocks/yr for years.** Refusing costs Resilience and generates guilt events. |
| **Friends outside the business** | The strongest Resilience anchor available — and the easiest to lose through neglect, silently, with no event to warn you |

The caretaking block is another under-modeled career killer: a 47-year-old actor whose mother needs care loses half their availability for four years, right at the pivot point where they most need to be working. No villain, no scandal, just arithmetic.

**Second generation.** Retire and play your child: inherit the Rolodex at 70%, start with a large `Heat` advantage — and carry a permanent **−15 Prestige nepotism penalty that is only cleared by one genuinely great performance** (`YourNotices > 82`). Until then, every review mentions your parent.

## 11.5 Politics and activism

Take public positions. Each maps to audience factions and to Rolodex members who hold their own views.

*v3 modelled this as a faction-standing matrix. It was mechanically thin — a table of numbers that mostly summed to zero — and a matrix of political positions with scores attached is the fastest way for a game to start sounding like it has opinions. It's now **events with costs and constituencies**, not a standings screen.*

Taking a position costs you specific people and wins you specific people, and the game names who and how much. It does not keep score.

```
Affection shifts within the audience segments the position speaks to
Named Rolodex members react according to their own established views
Era risk multiplier: blacklist eras × 4.0 ; permissive eras × 0.7
```

**Silence is also a position**, and in later eras younger audience factions penalize it. There's no neutral square on the board — which is the honest version of this, and lets the game explore it without telling the player what to think. Positions should be modeled as *factions and costs*, never as correct or incorrect.

## 11.6 Money and the going-broke ratchet

The most requested "how does a person who made $40M end up bankrupt" mechanic, which turns out to be pure arithmetic.

```
Off the top, every year:
    Agent 10%  +  Manager 5%  +  Lawyer 5%  +  Publicist ~$70K/yr   ≈ 22%
    Business manager 3% (and a small annual chance of embezzlement)
    Taxes: era-dependent, 35–70%+

LifestyleFloor:
    ratchets UP to 0.55 × your peak annual income
    falls only 8% per year afterward
```

Work the numbers. A $6M peak year sets a lifestyle floor of $3.3M. Income stops. Five years later the floor is still $2.17M/yr against no income. **The floor is stickier than the career.** Houses, staff, the plane you leased, the family you support, the manager who put everything in one bad development deal.

The escape valves are real too: residuals from a deep filmography (§10.1), a franchise backend that pays for decades, selling your likeness (§10.6), commercial work in a territory where you're still huge (§10.4), or simply *cutting the floor* — which is available at any time, costs Affection with your own entourage, and is the correct move that almost nobody makes in time.

## 11.7 Aging, mortality, legacy

Health curves bend. Insurance gets harder. The late-career renaissance is available but conditional: it requires banked `Prestige`, a live `Rolodex`, and an `Archetype` pivot made in advance (§4.9).

Death can arrive mid-project. The film gets completed with a double, a rewrite, or — in the synthetic era — your licensed likeness. Posthumous awards carry the largest `NarrativeBonus` in the game (+20), which is bleak and accurate.

## 11.8 The obituary

The run ends with a generated retrospective covering every career you had:

- The filmography, with your private Performance scores finally revealed next to the public reception — **including every film where you were brilliant and nobody knew**
- Films directed; the company you built and what happened to it after you left
- Awards won, lost, and campaigned for
- Your collaborators, with the number of films you made together
- The strikes you held and the ones you crossed
- **The roles you declined, and what became of them** — who took them, what they won
- The people you kept, and the ones you didn't

That last section is the whole game's payoff, and the reason every declined offer is tracked from the first minute of play.

---

# PART 12 — DATA SCHEMAS

```jsonc
// ── ROLE listing on the offer board ──────────────────────────────
{
  "id": "r_8812", "projectId": "p_2201",
  "characterName": "Marisol Vega",
  "billing": "lead",              // lead | supporting | bit | extra | recurring
  "archetype": "authority",
  "charAge": 47,
  "typeStrictness": 0.8,
  "difficulty": 68,
  "requirements": { "voice": 60, "physicality": 30, "look": 45 },
  "shootWindow": { "startQuarter": 2, "blocks": 2 },
  "flags": ["biographical", "period", "accent_required"]
}

// ── PROJECT ──────────────────────────────────────────────────────
{
  "id": "p_2201", "title": "The Quiet Hours",
  "medium": "film",               // film | tv | limited | theatre | voice
  "genre": "drama", "region": "hollywood",
  "budget": 24, "marketing": 11.5,
  "scriptQuality": 81,            // TRUE value; players see it through Taste noise
  "directorId": "d_04", "studioId": "s_02",
  "gatekeeperProfile": "prestige_auteur",
  "chaos": 0.35,
  "finalCut": "director",         // director | studio | contested
  "shootingStyle": "long_takes",
  "financing": { "equity": 9, "presales": 8, "taxCredit": 5, "gapDebt": 2,
                 "bondCompany": "bc_1", "shootLocation": "budapest" },
  "unit": { "dp": "c_11", "editor": "c_23", "composer": "c_31" },
  "castIds": [], "releaseStrategy": "festival_platform",
  "franchise": { "id": "f_03", "installment": 2 },
  "releaseDate": { "year": 2041, "week": 46 },
  "resolved": { "projectQuality": null, "filmCritic": null, "audience": null,
                "zeitgeist": null, "gross": null, "acquired": null }
}

// ── PLAYER: shared spine across all careers ──────────────────────
{
  "activeCareers": ["actor", "director"],
  "standing": {                    // per region
    "hollywood": { "heat": 58, "prestige": 71, "affection": 63, "notoriety": 22 },
    "europe":    { "heat": 12, "prestige": 44, "affection": 18, "notoriety": 4 }
  },
  "quote": 2.9,
  "calendar": [ { "year": 2041, "q": ["p_2201","p_2201","campaign","caretaking"] } ],
  "rolodex": [ { "npcId": "d_04", "affinity": 78, "grudge": 0,
                 "sharedProjects": 2, "onLoyaltyRoster": true,
                 "flags": ["held_the_line_together"] } ],
  "declined": [ { "roleId": "r_7734", "year": 2039, "outcome": "won Best Actor" } ],

  "actor": {
    "core":  { "craft": 74, "instinct": 61, "presence": 80, "resilience": 49 },
    "gates": { "look": 68, "voice": 55, "physicality": 42 },
    "persona": { "genre": { "drama": 84, "thriller": 52, "comedy": 11 },
                 "archetype": { "authority": 77, "character_actor": 61 },
                 "legibility": 64, "consecutiveSameLane": 3 }
  },

  "director": {
    "attributes": { "vision": 71, "command": 83, "craft": 62,
                    "taste": 44, "efficiency": 39 },
    "signature": { "visual": { "naturalist": 72 }, "tonal": { "bleak": 68 },
                   "thematic": { "family": 81 }, "legibility": 58,
                   "lateStyle": false },
    "devSlate": [ { "scriptId": "sc_88", "momentum": 0.71, "budgetAsk": 30,
                    "attachedStarId": null, "quartersInDev": 6 } ],
    "unit": { "dp": { "id": "c_11", "loyalty": 84 },
              "editor": { "id": "c_23", "loyalty": 91 } },
    "finalCutEarned": true
  },

  "studio": {
    "tier": "independent_producer", "capital": 180,
    "slate": ["p_2201","p_2209"], "library": ["f_03"],
    "executiveStanding": 54, "boardPatience": 2,
    "releaseDatesHeld": [ { "year": 2042, "week": 27, "projectId": "p_2209" } ],
    "talentDeals": [ { "npcId": "a_17", "type": "first_look", "cost": 2.5 } ]
  },

  "life": {
    "health": 71, "conditions": ["knee_reconstruction"],
    "substance": { "stage": "dependence", "insurable": true, "cleanYears": 0 },
    "therapy": true, "burnoutDebt": 14,
    "family": { "partnerId": "n_09", "partnerInIndustry": false,
                "childIds": ["n_44"], "caretakingLoad": 1 },
    "politics": { "positions": ["labor"], "factionStanding": {} },
    "finance": { "netWorth": 12.4, "lifestyleFloor": 3.3, "peakIncome": 6.0,
                 "residualStreams": 0.42, "teamTakePct": 0.22 },
    "guild": { "member": true, "qualifyingEarningsYTD": 19000,
               "healthPlanThreshold": 28000, "pensionYears": 14,
               "strikeRecord": { "held": 2, "crossed": 0 } }
  }
}
```

---

# PART 13 — BUILD PLAN

| Phase | Scope | Ship criterion |
|---|---|---|
| **0a. Cut list** | Apply Part 0 before writing any code. The Decision Test kills features cheaply on paper and expensively in an engine. | For every system, the optimal play takes more than one sentence to state. |
| **0b. Spreadsheet** | Every formula in Parts 4–11 in a sheet. Simulate headless: 200 acting careers, 200 directing careers, 500 studio-years. | Distributions match Part 14. **Do this before any UI.** The v1 formulas failed this check badly and had to be re-derived — assume yours will too. |
| **1. Actor vertical slice** | One era, one region, 15 NPCs, 6 genres. No scandal, no calendar. | A playtester independently says *"the movie was bad but I was good"* without being told that's possible. If they don't, stop and fix it. |
| **1b. The Work** | The six film dials, coherence, performance contrast, the three on-set moments | Two playtesters given the identical script produce films that are recognisably different and both defensible. Build before the calendar — it's the core loop. |
| **2. Calendar + Deal** | Quarters, overlapping offers, deal terms, agents, packaging | Playtesters visibly agonize over a scheduling conflict. |
| **3. Persona + typecasting** | Affinity vectors, Legibility, break-type arc, the age cliff | Two players describe their actors in different words without prompting. |
| **4. Rolodex** | Full graph, loyalty rosters, NPC arcs | A player names a specific director as their favorite thing in the game. |
| **5. Awards season** | Campaign block, narratives, category fraud, vote splitting | Losing an award feels like a story, not a bad roll. |
| **5b. Leverage** | Favours, approvals, Indispensability, the holdout, the pull-action menu | A player describes a career win that the game never prompted them to attempt. |
| **6. Director career** | Attributes, Taste-as-noise, dev hell, casting from the other side, **the edit as three real choices (§5.8)**, final cut, the Unit | An actor player *chooses* to direct because they got burned in post — not because a menu appeared. |
| **7. Life layer** | Health, addiction + uninsurability, family, caretaking, the money ratchet | A career ends for a reason that has nothing to do with talent, and the player agrees it was fair. |
| **8. Genre & IP layer** | Genre economies, boom/bust cycles, adaptation market, franchise shapes, merchandising, tie-ins, brand money | A player deliberately makes a horror film because it's the only thing they can get financed — and it works. |
| **9. World layer** | Guilds, health-plan cliff, strikes, festivals, territories | A player turns down a good role to hit their health-plan threshold. |
| **10. Studio** | Slate, financing stack, script market, IP decay, date warfare, the board | A player gets fired from a studio and immediately wants to run another one. |
| **11. Eras + regions + legacy** | Tech shifts, obsolescence events, international industries, likeness economy, obituary, second generation | A 60-year run has three distinct acts and the obituary makes someone quiet. |

**Scope reality check.** Phases 0–5 are a complete, shippable game — that's the actor sim, and it's enough. Phase 6 roughly doubles the design surface. Phase 10 doubles it again and is closer to a strategy game than a life sim; it deserves to be evaluated on its own merits and possibly shipped as a separate mode or an expansion.

**The dependency that matters:** the Rolodex (phase 4) must exist before the director career (phase 6), because career-switching is only interesting if relationships carry over. Building the director first produces two disconnected games sharing a menu.

---

# PART 14 — TUNING TARGETS

All values below were fit by simulation, not chosen by feel. The harness is included alongside this document — run `python3 callback-sim.py all` to reproduce every number in this Part.

## 14.1 Reception model — verified ✅

| Correlation | Target | Measured |
|---|---|---|
| Performance ↔ YourNotices | 0.70–0.80 | **0.76** ✅ |
| Performance ↔ FilmCriticScore | 0.40–0.48 | **0.42** ✅ |
| Performance ↔ Box-office ROI | 0.20–0.30 | **0.23** ✅ — the design's signature number |
| FilmCriticScore ↔ ROI | 0.20–0.30 | **0.30** ✅ |
| FilmCriticScore ↔ AudienceScore | 0.40–0.50 | **0.39** ⚠️ boundary |

These five trade off sharply against each other. **If you change any constant in §4.10, re-run the sweep** — raising the ensemble weight to make performance matter more to critics also collapses the critic/audience divergence the design depends on.

## 14.2 Studio economics — verified ✅

Per-tier medians and slate outcomes are in §8.2. Headline checks:

| Metric | Target | Measured |
|---|---|---|
| Share of all films profitable | 45–55% | **48%** (mid tier) ✅ |
| Micro-budget effective profitability (after distribution gate) | ~55% | **56%** ✅ |
| Balanced slate: P(profitable year) | 55–65% | **60%** ✅ |
| Blockbuster slate: p10 outcome | catastrophic | **−$171M** ✅ |
| Tentpole P(>2× ROI) | ≥8% | **12.9%** ✅ |

## 14.3 Director pipeline — verified ✅

| Standing | Films / 30 yrs | Median dev time | Died in dev |
|---|---|---|---|
| Newcomer (18) | 2 | 2.8 yr | 6 |
| Working (45) | 9 | 2.0 yr | 4 |
| A-list (75) | 15 | 1.5 yr | 1 |

A-list pace of one film per two years matches the real working rhythm of a top director.

## 14.4 Genre cycles — verified ✅

| Metric | Target | Measured |
|---|---|---|
| Share of time a genre is booming | 4–8% | **5%** ✅ |
| Bust years per 60-year history | 10–20 | **14** ✅ |
| Demand standard deviation | 8–12 | **10.0** ✅ |
| Genres booming simultaneously (of 11) | <1 | **0.5** ✅ |

## 14.5 Franchise curve — fitted to real data

The v1 sequel curve declined monotonically from the first sequel. Box-office data shows the **first two installments usually out-earn the third**, with reception bottoming around the fifth or sixth. The v3 curve (§9.5) is fitted to that shape rather than assumed.

## 14.6 Creative decisions — verified ✅

The design goal was *authorship*, not skill checks. These numbers are how you tell the difference.

| Metric | Target | Measured |
|---|---|---|
| corr(audience effect, critic effect) — **must not be one axis** | −0.7 to +0.6, varying by genre | **−0.58 (drama) to +0.52 (horror)** ✅ |
| Genres where the palette is near-orthogonal | ≥2 | **3** (action −0.10, comedy +0.19, sci-fi +0.01) ✅ |
| Palette effect size vs `AudienceScore` sd (7.6) | comparable, not dominant | **±7–10** ✅ |
| Mean coherence of a random palette | 35–50 | **43** ✅ |
| Share of random palettes below coherence 30 | 10–25% | **18%** ✅ |
| Variance multiplier at coherence 32 | 1.7–2.2× | **1.95×** ✅ |
| P(landmark), great director + strange film | 15–25% | **20%** ✅ |
| **Distinct optimal allocations across 16 build×genre pairs** | ≥6 | **8** ✅ |
| Most common allocation's share of those 16 | ≤50% | **6/16 = 38%** ✅ |
| Contrast budget spread, worst build to best | must change *what you can afford* | **3.2 → 6.2** (1 against → 2 against) ✅ |
| Ensemble cost of a showy read vs a steady one | must be real | **−5.1** ✅ |
| Showiest allocation must NOT maximise Notices | required | **shaped 80.9 > showy 78.5** ✅ |

**Two failure conditions to keep testing for.**

If `corr(audience, critic)` goes strongly negative in every genre, the film palette has collapsed into a single commercial-versus-artistic slider and the system has failed. Three genres are deliberately near zero to prevent that.

If the actor's optimal allocation is the *same* across most build-and-genre pairs, the performance system has collapsed into a stat check — which is exactly what happened to an earlier draft that measured contrast as a single distance and produced a publishable *"optimum contrast: 63."* Positions being **named and asymmetric** rather than numeric is the fix; the 8-of-16 spread is how you check it held.

## 14.7 Leverage — verified ✅

| Metric | Target | Measured |
|---|---|---|
| Installments before recasting becomes "unthinkable" | 3–5 | **4** ✅ |
| Break-even Indispensability for a holdout | 65–75 | **70** ✅ |
| P(losing the role) on a holdout at Indispensability 90 | ≥10% | **13%** ✅ |
| Max holdout raise | ≤×2.5 | **×2.40** ✅ |

The holdout must never become free money — a leverage move with no downside is a button, not a decision. The 0.85 cap on `P(they pay)` is what enforces that: studios call bluffs because caving to you sets a precedent across their whole slate.

## 14.8 Decision budget — verified ✅

| Metric | v3 | v4 | Target |
|---|---|---|---|
| Decisions per in-game year (actor + director) | 55 | **19** | ≤20 |
| Decisions per year (actor only) | 43 | **13** | ≤15 |
| Decisions over a 40-year career | 2,200 | **760** | <900 |
| Share of pushed prompts that are administrative | most | **0%** | 0% |

Measured by counting prompts per system per year, not estimated. Full breakdown in §0.2.

## 14.9 Career-shape targets — v9: the first seven are verified, phase 0 built the actor spine only

Phase 0 was scoped to the actor career alone (§0.6, §3.3's spine, minus the director and studio layers). The seven targets below all read off systems phase 0 actually built, and were the test the original v8 draft never ran — §1's finding (this section marked *"to be verified"* while §4.3's Standing formula, the one thing that gates every target here, shipped unverified) is what produced the 0%-of-targets-met result in `callback-design-review.md`. After the §4.3/§4.4/§4.10 fixes above, and again after this session's production rework (§5.6, §6.3–6.4), a 3,000-career simulation hits all seven, every time it's re-run:

| Metric | Target | Measured (n=3,000) |
|---|---|---|
| Median acting career length | 26 years active | 32 |
| Careers reaching Heat > 80 at any point | ~18% | 17% |
| Careers with zero award nominations | ~55% | 50% |
| Award wins per 100 careers | 21 | 12 |
| Median lifetime earnings | $6–11M | $10.0M |
| Top-decile lifetime earnings | $90M+ | $120M |
| Careers surviving the age-42 cliff at lead level | ~30% | 39% |

Three further claims, verified alongside the table above, that don't come from the design doc's own §14.9 list but that the review's method — *simulate the whole career, not the subsystem* — turned out to demand once leverage (Part 6) and the reworked shoot (§5.6) existed: a career that never opens the moves menu at all still meets every target above (Part 6 is genuinely optional, not secretly load-bearing); no single playstyle dominates the six Ambitions (§0.4); and a career played entirely through three real, varying scenes per shoot (§5.6) meets the same seven targets a single-choice shoot always did, confirming the rework changed the interface, not the odds.

**The remaining four targets are still unverified** — they read off systems phase 0 didn't build: the health-plan threshold and addiction/uninsurability beyond a basic health curve (Part 11, mostly unbuilt), the director career to switch into (Part 7, doesn't exist as a playable mode), and the obituary's declined-offer regret count (the obituary exists; this specific figure was never instrumented). They stay targets, not results, until those parts are built.

---

# PART 15 — RISKS

| Risk | Mitigation |
|---|---|
| **Decoupling reads as "the game is random"** | Always show *why*. A post-release breakdown card: "Your performance: strong. The edit: buried you. Reviews: mixed. Opening: soft." Attribution is the entire fix. |
| **Too many meters** | Player-facing UI shows **Heat / Prestige / Affection / Notoriety** and nothing else numeric. Attributes are shown as words ("technically excellent, physically limited"). Everything else stays internal. The v4 pass cut the actor to 4 core attributes + 3 gates and the director to 5. |
| **Persona feels like punishment** | Surface it as an *agent conversation*, not a stat screen. "They see you as the guy who plays cops. That's money. It's also a wall." |
| **The age cliff feels unfair** | Telegraph it hard from age 30, in fiction, through your agent. Fairness comes from *warning*, not from removing it. |
| **Three careers = three shallow games** | They share one spine (§3.3): one Standing model, one Legibility engine, one Rolodex, one calendar. Build the spine first. If a new career needs its own version of any of those four, the design is wrong. |
| **The studio layer is a different genre** | It is. Gate it behind real in-fiction progression, or ship it as a separate mode. Do not force a life-sim player into slate management. |
| **The life layer becomes misery tourism** | Every hard system needs a real exit: uninsurability clears after two clean years, blacklists end, the lifestyle floor can be cut, the late-career renaissance is reachable. Consequences must be survivable or players stop caring. |
| **Politics content becomes editorial** | Model positions strictly as factions with costs and constituencies. The game states outcomes, never verdicts. |
| **The likeness economy dates instantly** | Treat it as one era's rules among many, not the game's thesis. It sits in the same list as sound killing the silent stars. |
| **60-year careers become spreadsheet management** | Late career should *shed* options, not add them. Fewer, heavier decisions. This is Rule 3 in §0.3, and the decision budget in §14.6 is how you check it. |
| **The tie-in layer turns the game cynical** | It should feel that way *sometimes* — brand money genuinely does push films toward the middle, and the model showing that is the point. Counterweight it: the cult-film system (§9.9) and the prestige lanes have to stay genuinely viable, and the merchandising fortune must remain a real, reachable prize rather than a trap. |
| **Genre cycles feel like weather the player can't affect** | Surface the cycle in fiction — trades reporting a boom, your agent saying every studio wants a horror script this year. A player who reads a cycle correctly and buys in during the bust should visibly win. |
| **The palette collapses into one slider** | The genre-specific weights are the defence, and §14.6 is how you check it. If a playtester ever says "just push everything left for reviews," the weights are wrong. |
| **Coherence punishes experimentation** | It doesn't reduce the mean, only widens the spread — and it's the sole route to a landmark. Say this to the player in the forecast: *"nobody knows what this is, including us."* |
| **Forty verbs is paralysis, not freedom** | They're all pull, so the game never presents them at once. Surface them contextually — the holdout appears as a conversation with your agent when your option is up, not as a menu item you might miss. A player who ignores the whole system should still have a good career. |
| **Leverage makes the player too strong** | Every lever costs a different currency, and the currencies are hard to convert. Favours die with people. Indispensability is per-property. Information spends once. Approvals cost fee. There is no accumulating power stat. |
| **Scope** | Phases 0–5 ship a complete game. Everything after that is an expansion and should be planned as one. |

---

# THE ONE-LINE SUMMARY

BitLife asks: *did the roll succeed?*

Callback asks: **were you good, was it good, did anyone notice, and was it worth what it cost you?**

Those are four different questions. Every system in this document exists to keep them apart — and the director, studio, world, and life layers exist so that the answer to the fourth one has somewhere real to come from.
