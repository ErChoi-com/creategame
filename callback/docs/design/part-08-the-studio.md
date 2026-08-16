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

The box-office model behind those numbers is §4.10's — *v9: this section used to carry its own differently-tuned copy (a different opening coefficient, `Zeitgeist` defined here and nowhere else), which was exactly the two-box-office-models problem §4.10 says it fixed and, until this pass, hadn't actually fixed here. One model now; this section reads it.* The one piece worth restating is the marketing curve, which is genuinely studio-side (an actor never sees it) and doesn't live in §4.10 at all:

```
Marketing(b) = 0.35b if b<10 ; 0.48b if b<50 ; 0.55b if b<100 ; 0.80b otherwise
```

*(§4.10's `BreakEven` uses a flat 0.45 rather than this curve — deliberately: it's the number shown to an actor reading one release card, and a flat approximation is honest at that resolution, while a studio managing a slate needs the real budget-tiered curve above. The two are not meant to be forced into agreement; 0.45 sits inside the <$50M tier's 0.48, which is roughly where the flat figure was tuned to read correctly most often. If both figures ever need to move together, this is where that dependency lives.)*

`Zeitgeist` (§4.10) is what makes breakouts possible. It's deliberately *not* pure quality — a film catches on for reasons partly outside the film. Without it the model had no fat tail and every studio went bankrupt; with it, one film in twenty pays for the slate. That's the actual shape of the business.

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

