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

**Second generation.** Retire and play your child: inherit the Rolodex at 70% — the same transfer mechanic §7.11 uses for switching careers mid-life (there, Rolodex moves at 100%, Prestige at 60%, Heat at 35%, Affection at 80%; a generation is a harder cut than a career change, which is why this figure sits below all four) — start with a large `Heat` advantage, and carry a permanent **−15 Prestige nepotism penalty that is only cleared by one genuinely great performance** (`YourNotices > 82`). Until then, every review mentions your parent.

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

The escape valves are real too: residuals from a deep filmography (§10.1), a franchise backend that pays for decades (§6.4's `RecastCost` and §6.5's holdout and gross-points leverage — Indispensability is, among other things, a retirement plan), selling your likeness (§10.6), commercial work in a territory where you're still huge (§10.4), or simply *cutting the floor* — which is available at any time, costs Affection with your own entourage, and is the correct move that almost nobody makes in time.

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
- **The roles you declined, and what became of them** — who took them, what they won. §5.17 names this list from the other end, quietly, the whole way through a career: the films you wanted to make against the films you made. §10.0 is the mechanism that makes this a real query instead of an assertion — a declined role is cast, made, and resolved through the same formulas as any of yours, and this is where that history gets read back.
- The people you kept, and the ones you didn't

That last section is the whole game's payoff, and the reason every declined offer is tracked from the first minute of play.

---

