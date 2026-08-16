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

