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

*(v9 — Animation sits oddly in this table, and it's worth saying why rather than leaving it unexplained: §4.2's `GenreAffinity` — the vector Persona and typecasting actually track — has ten entries, and animation isn't one of them, because it isn't a genre in that sense. You can make an animated comedy, an animated family film, an animated period piece. It's the production medium, and §10.5 treats it that way — "Voice / animation," a lane defined by what gate it removes (no Look, no age cliff), not by what story it tells. This table keeps its own Animation row because the economics genuinely are distinct — the merchandise multiplier and budget norms don't belong to any one of the ten genres — but a role's `archetype`/`genre` tags underneath an animated film are still whichever of the ten actually fit it, and Persona updates against those, not against "animation" as its own affinity.)*

### Why horror matters more than it looks

Horror's numbers are real and extreme, and they create the design's most important on-ramp: **it is the one genre where a nobody with no Standing can make a film that actually works.** Budgets are small enough to self-finance, the audience doesn't care about stars, and critical failure barely dents the returns.

So horror should be where struggling actors and first-time directors go, and it should genuinely work — while also being the hardest lane to leave. A horror star at 40 with high Legibility and low Prestige is a real, common, and interesting place to be stuck.

## 9.2 Subgenres and hybrids

Each genre holds 4–6 subgenres with their own demand cycles — horror splits into slasher, supernatural, folk, body, found-footage, elevated. Subgenres boom and die faster than genres do.

**Hybrids** average the demand of both parents, take a −8 marketing penalty (harder to sell in one sentence), and get a +6 critic bonus if `ProjectQuality > 70`. So a horror-comedy is harder to open and easier to love — which is why they're rare and why they become cult films (§9.9).

## 9.3 Genre cycles — the boom and the bust

The most important addition in this Part. Genres are not stable; they surge after a hit, flood with imitators, and crash. *(The formula below reads "every film in g that returned ROI > 2.5" as though a whole population of films is resolving every quarter whether or not the player is in any of them — because it is: §10.0 is where that population actually comes from.)*

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

*(v9 — "recast" in the Prequel row, and the recast that follows when Legacy sequel talent prices itself out, both resolve through §10.0's `CastingResolution` — the same `Utility`-weighted pipeline that fills any role you decline, not a separate unspecified process for franchise roles.)*

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

*(v9 — a shared universe you're not part of still runs on these rules. §10.0 resolves its off-screen entries the same way it resolves any background film, so interlock, fatigue, and collapse are things that can happen to a universe entirely outside your own casting history — and you find out from the trades.)*

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

That trade is the honest engine behind a lot of films, and putting it in the model explains a certain kind of movie better than any amount of commentary about creative bankruptcy. **Not implemented yet** — the built engine (see the note below §9.7) only has the fee-vs-points trade, not this financing-for-creative-control shape; a real, bounded follow-up.

### §9.7 build note — what's actually implemented, and what's still just this section

The fee-vs-merchandising-points trade this section always specified is built, in `leverage/merchandising.py` — deliberately its own small, self-contained module (no `Role`/`FranchiseEntry`/`Session` imports; every function takes plain numbers) rather than folded into the approvals/box-office-bonus deal code, so it can be reasoned about, tested, and extended on its own. It's the first genuinely *ongoing* income stream in the engine — every other deal (a fee, a box-office bonus, a director's cut) pays once, at resolution; a merchandising royalty pays every year afterward, read fresh off the character's own current Indispensability (`leverage/indispensability.py`) — so it fades as the franchise goes dormant and, new this pass, spikes back to life on a reboot, with no separate decay/revival logic needed at all.

**Gated to animation for now** (`actor/offers.py`'s `Role.is_animation`, itself new this pass — see Part 4/5's own note on why Animation stopped being modeled as a genre) — real merchandise-driven franchise money is dominantly a toy-shelf, animation-driven thing; a live-action franchise's own (rarer, differently-shaped) licensing deals are a real, separate follow-up, not this mechanic reused blind.

**The 8-year-dormancy "reboot lands harder" idea this section already named is built too** — `simulation._franchises.py`'s `resolve_reboots()`. A franchise that crosses the Indispensability release floor no longer just vanishes from tracking; it moves into a retired archive (`FullState.retired_franchises`) carrying its own career-best `peak_indispensability`, and rolls a small, real per-year chance of revival — higher for a franchise that peaked bigger, and never before `REBOOT_MIN_DORMANT_YEARS`. A revival re-seeds a real partial indispensability (not full peak — a genuine second life, not a free reset) and is immediately eligible for a real sequel offer next time a role is sampled, exactly the "they're bringing your old franchise back" moment the dormancy strategy above was always describing.

**Deliberately not built this pass — documented here instead**, in roughly the order they'd matter most:
- **A studio buyout on the royalty stream.** The same shape director development's own self-finance buyout already has, pointed at a merchandising deal instead of a project: the studio offers a lump sum to buy back your ongoing claim. The real tension is information asymmetry — you don't know if they're offering because the property's fading, or because they know a reboot's coming and want you out before it pays off.
- **Renegotiating a royalty share that's grown stale.** A share signed on installment 1, before anyone knew the character would carry a trilogy, stays locked at those terms even as `update_franchise_after_project` grows the real value of the property out from under it — the same quote-lock trap §9.6/§5.18 already name elsewhere. The natural fix is a holdout-shaped renegotiation attempt, a new target for the existing `resolve_holdout()` machinery, contested by the same `studio_protectiveness()` that already resists giving up value on a proven property — reusing the holdout, not inventing a second one.
- **A morals-clause suspension.** §9.8's own Endorsements-for-actors row already names a morals clause that terminates on a Notoriety spike; merchandising royalties currently have no equivalent, despite Notoriety/the addiction arc (§4.13, `life/addiction.py`) being a fully built, currently under-used system. Tying a bad enough spike to a frozen or cancelled royalty check would give that system a real financial consequence it doesn't have anywhere else yet.
- **A lifetime-royalty line in the obituary.** Low cost, real payoff — `life/obituary.py`'s retrospective already names declined roles and hidden performances as "the whole shape of a career, told at the end"; total lifetime merchandising income, and which characters kept paying decades later, belongs in exactly that list.

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

