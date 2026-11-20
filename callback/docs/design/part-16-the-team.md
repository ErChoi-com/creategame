# PART 16 — THE TEAM: DELEGATED DECISIONS

## 16.0 The problem this fixes

Part 0 got the push budget down to ~15–20 decisions a year by cutting chores, not by cutting choices — every decision left in that budget is one the design fought to keep. Part 6 then added forty-odd pull verbs on top, free against the budget because engaging with them is optional (§0.3, Rule 2b).

That's the right shape for a player who wants the whole game. It is a lot of surface for a player who wants *some* of the game — someone who loves the Shoot and the Reckoning and finds the leverage menu, the catalogue, and the fee-negotiation stance genuinely tedious. Right now that player's only option is to ignore those systems, which quietly forfeits the money and access they unlock. There's no way to *want* the outcomes of a system without doing the system.

This Part is the fix, and it isn't a settings menu. It's making a fact of the fiction mechanical: **you are not alone.** An actor has an agent, a manager, sometimes a publicist. A director has a line producer, a development exec keeping the slate moving. §6.6 already has an agent who can be signed, promoted, and asked to package a deal. This Part gives every one of those people a voice and lets the player hand them the wheel on specific, named categories of decision — never all of them, and never for free.

## 16.1 The rule this has to pass

Delegation is a new system, so §0.1's Decision Test applies to it directly: **handing something to your team has to be a real trade, not a strictly-better button.** If "delegate everything" is always the correct answer, delegation is a difficulty slider wearing a costume, and §0.1's own corollary — *if you can write the optimal play in one sentence, it isn't a mechanic* — kills it on sight.

So delegation costs something real, on both ends:

- **It costs access.** Your team can only be as good as the team you've earned. A Regional Stage start with an unrepresented actor has nobody to hand anything to — §16.3 gates delegation categories behind the same agent tiers §4.5 and §6.6 already built, so early career is hands-on by construction, not by a tutorial telling you so.
- **It costs ceiling.** A team member plays it safe, because their incentive is *not looking bad*, not *your transcendent scene*. §16.5 makes this literal: delegated choices are drawn from the same formulas as yours, but with the tail cut off.

That's a real choice between a smaller, steadier career and a bigger, riskier one, made once per category instead of once per instance — which is exactly what a decision budget is supposed to protect.

## 16.2 Who's on the team

Every delegation category is voiced by someone the engine already generates. The Rolodex (§10.0) already types its NPCs — `npc_type` includes `agent`, `producer`, and `casting_director` alongside `director`, `costar`, and `critic` — so this Part invents no new roles. It gives three of those existing types a second job: instead of only being someone you have a relationship with, they're someone whose judgment you can borrow. One is persistent across the whole career; two are scoped to whichever project is currently in motion — which matters, because it's also what keeps a single voice from being stretched over unrelated domains (§16.6).

| Voice | Existing `npc_type` | Scope | Speaks for |
|---|---|---|---|
| **Your agent** | `agent` | Persistent — one NPC, tied to `agent_tier` (§16.8) | Offer Board curation, fee negotiation stance |
| **The director** *(this project's)* | `director` | Per-project, but not memoryless — draws on `director_relations`/`director_continuity_bonus` (`simulation/full_career.py`), the same machinery that already lets a Rolodex-tracked director return to a project instead of a random one | Approvals selection — script/director/co-star approval is fundamentally about how much this specific director trusts you in the room, not a career-wide policy |
| **The producer** *(this project's)* | `producer` | Per-project, a named NPC — but its tone is a *read-through* of `studio_relations`, not its own ledger (§16.8) | Release-strategy calls when the numbers aren't close, development-slate triage, overage tolerance (director track) — the money-and-logistics side |

That's three voices, deliberately: enough that the game isn't routing every delegated decision through one all-purpose "your team" abstraction (which would make the personality mechanism in §16.6 do more work than the data supports), not so many that this Part starts feeling like its own cast list. All three voices are built to *recur* rather than reset to Stranger every time — a director you keep working with should sound like it, and a producer should read as one person fronting for a studio that's learned to trust you, not a fresh stranger generated every film. `casting_director` and `costar` stay relationship-only — see below for why casting was cut, and `costar` was never a candidate (co-stars don't decide things about your career).

*Cut from this list: a casting-director voice for director-track casting.* The only casting decision the engine actually exposes (`choose_director_casting_action()`) isn't administrative filler — it's the five-way trade-off between a bankable-wrong-fit star, the right actor with no heat, a discovery, your own roster, or a difficult genius, which is exactly the kind of two-defensible-options choice §0.1's Decision Test exists to protect. There's no minor-role busywork sitting underneath it to hand off; delegating it would mean automating the one real decision in that system, not the chore around it. It moves to §16.3.

Two categories stay unvoiced on purpose:

- **Setup & Resolution scene positions** default to the safe, on-book choice with no team member attached — this is the one delegable category that's about *you*, not your team, and "played it safe" is honest enough attribution on its own (§16.6).
- **Public standing pull actions** (the publicist instinct) were already folded into §4.13's scandal table and §6.1's Public-standing leverage in Part 6 — this Part adds nothing new there, it just means the trades digest can now say *"your producer thinks this is worth a statement"* instead of surfacing silently.

Nobody new is hired, and no new NPC subsystem is built. This Part is what lets the player talk to relationships the game already models, instead of only benefiting from them off-screen.

## 16.3 What's never on the table

The following stay player-only, always, at every agent tier. This list is deliberately the same handful of decisions §0.2's table fought to protect — automating them wouldn't simplify the game, it would hollow it out:

- **Accept / decline / hold an offer.** The one decision the whole game is downstream of.
- **The Deal fork** (§5.4) — money vs. control. Cut from 9 decisions to 1 specifically because it's the one that matters; it doesn't get cut to 0.
- **The Turn** — the middle scene's position choice (§5.6). The setup and resolution can be delegated (§16.4); the turn is where Instinct's transcendence roll lives, and it's the single decision the UX docs call "the peak." Handing it away would mean nobody ever plays the best moment in the game.
- **Season / campaign** and any Ambition-adjacent choice (§0.4) — what you're playing for is not a thing your team gets an opinion on.
- **Holdouts** (§6.5) and any leverage play that spends a relationship, not just money — these are pull, already free, and they're personal by definition.
- **Director-track casting** (`choose_director_casting_action()`, §16.2) — the bankable-wrong-fit / no-heat / discovery / roster / difficult-genius trade-off, the director-side equivalent of the Deal fork.

If a future system wants to add to this list, that's the test: does automating it remove a chore, or does it remove the reason to be playing.

## 16.4 What's delegable, and how it surfaces

Everything not in §16.3, gated by §16.5's tiers:

| Category | Voice | Manual version | Delegated version |
|---|---|---|---|
| Offer Board curation | Agent | See all offers, judge Fit yourself | Pre-filters to what clears your Standing/Fit bar; you still see and choose from what's left — this narrows the board, it never removes the accept/decline choice |
| Fee negotiation stance | Agent | Set your own ask against Standing | Negotiates within a stated floor ("never below scale," "always chase approvals over cash") |
| Setup & Resolution scene positions | *(unvoiced — §16.2)* | Choose With/Beneath/Beyond/Against yourself | Picks the safe, on-budget position (§16.5); the Turn is never included, per §16.3 |
| Approvals selection | This project's director | Pick which right to buy with your fee cut | Buys the approval this director is actually inclined to grant — a Loyal/Ally director yields script or co-star approval readily; a Stranger only ever offers pay-or-play |
| Release strategy | Producer | Choose wide/limited/festival/streaming/shelve | Takes it only when two options are within a small, defined margin of each other — a real toss-up, not a studio override |
| Development slate triage | Producer | Choose which project gets this year's action | Applies momentum to whichever project is closest to greenlight |

Delegation is set per category from the Rolodex/Leverage tab — a pull surface already, so changing it costs nothing against the push budget (§0.3, Rule 2b). Each category has three states, and setting one is itself a pull action:

**Ask me** (default until unlocked otherwise) → **Suggest, then I decide** → **Handle it**

"Suggest, then I decide" is the training wheel: the team's pick appears pre-selected with its one-line reason attached, and confirming costs the same single tap accepting normally would. Nothing is lost by trying it.

## 16.5 Trust, tiers, and the safety/ceiling trade

Two things are true about a team pick, and both are load-bearing:

**It's gated by what you can afford.** Delegation categories unlock the same way §6.6's agent tiers already do — the five tiers (`unrepresented → regional → boutique → major → powerhouse`, cleared at Standing 15/35/55/75) already carry different application-fatigue rates and offer-boost ranges, so a Powerhouse agent is mechanically more capable than a Regional one *before this Part adds anything.* Delegation just extends that existing curve one step further: `unrepresented` has nobody to hand the Offer Board to, `regional` can be trusted with the safe version of it, and only `major`/`powerhouse` can be trusted with the categories closer to money (approvals, release calls). This means the choice to go hands-off is never available on day one, which is correct: nobody starts a career with a team good enough to trust blindly, and the game shouldn't pretend otherwise.

**It plays it safe.** A delegated pick is computed from the exact same formula a manual one would use — §4.4's `Utility`, §5.6's shape math, whatever the category calls for — with the tail trimmed:

```
Manual pick:   sampled normally, including Instinct's transcendence roll (§4.7)
               and the full Coherence/Landmark range (§5.9)

Delegated pick: the same formula, biased toward the option closest to the
               *expected* outcome — never the swing for a Landmark, never
               the highest-variance position, never the fee ask that risks
               the offer to chase 5% more
```

This is not a worse formula bolted on for balance. It's the honest version of what a real team does: protects the floor, never reaches for the ceiling, because reaching is the client's call, not theirs. A player who stays hands-on keeps access to the transcendent scene, the landmark film, the holdout that pays off huge. A player who delegates trades that away for a steadier, lower-variance career and gets time and attention back. Neither is the correct answer — that's the point.

## 16.6 Attribution — the one rule that isn't optional

§0.3's Rule 2 already governs every outcome in the game: *always show the causal chain.* A delegated decision is not exempt — if anything it needs it more, because the player wasn't in the room.

Every delegated pick produces one line, in the team member's voice, visible the moment it happens and recapped in that year's Reckoning:

> *"Your agent took the Fox pilot — steady paycheck, keeps your calendar clear for awards season."*
> *"The director passed on offering script approval this time — you're barely past Familiar, and this film's too small to bet trust on."*
> *"Your producer held for a wide release — the numbers weren't close enough to call it a toss-up."*
> *"You played the resolution close to the vest — no reason to spend contrast budget you might need next year."*

If a player can't tell *why* their team did something, delegation reads as the random-number generator §0.3 already warns against — worse, here, because the player didn't even make the roll. This line is not optional polish; it's the mechanism that keeps delegation legible enough to trust.

**The voice should vary with the specific person, not just the category — and the game already has what that needs.** Every NPC (§10.0) carries an `agenda` (`ascent | legacy | loyalty | redemption | vindication | mentorship`) and a `relationship_state` (`stranger → familiar → (ally|rival) → (loyal|estranged) → (legacy|severed)`), both already tracked for reasons that have nothing to do with this Part. `narrator.py` reads them as a phrasing table instead of inventing a separate personality system: an `ascent`-agenda agent who's still only `familiar` reaches for the offer that raises *their* profile too ("this gets you both in the room"); a `loyal`, `mentorship`-agenda director explains a granted approval in terms of your growth, not the film's ("you've earned the room, use it").

This isn't hypothetical variation — it's earned. §16.2 already establishes that the director voice recurs through the engine's own `director_relations`/`director_continuity_bonus`, so the *same* director can be Familiar in year 3 and Loyal by year 9, and the line should visibly change as that happens — a career-long collaboration actually sounding like one is the whole payoff.

The producer voice recurs too, but through a narrower mechanism, deliberately: it's a real, named `npc_type="producer"` NPC — someone the player can watch turn up on more than one project at a studio they keep working with — but that NPC carries no `affinity`/`grudge` of its own. Its `agenda` and displayed `relationship_state` are read straight off that project's `studio_relations` entry instead of an independent ledger. This gives the line a face without asking the game to track two parallel trust scores that would, in practice, only ever move together — a producer's tone should reflect the studio's opinion of you, not a private opinion of their own, because in the fiction they're speaking for the studio's money, not their own. Same line-generation mechanism either way, same inputs the relationship system already computes — this is a lookup table, not a new mechanic, and it's the reason a twenty-year agent should never sound like the director you just met.

## 16.7 Risks

| Risk | Mitigation |
|---|---|
| Delegation becomes strictly optimal, failing §0.1's own test | §16.5's safety/ceiling trade — delegated picks are provably worse in expectation for anyone chasing the tail (Landmark, transcendence, a holdout win) |
| Reads as a settings menu instead of part of the fiction | Every category is voiced by an existing role (§16.2); every action produces attributed dialogue (§16.6), never a silent toggle |
| Players feel babysat into automation they didn't ask for | Default state is **Ask me** for every category, always; nothing unlocks a *worse* manual option, only an additional one |
| Core dramatic choices get quietly automated by scope creep later | §16.3 is an explicit, closed list, with the test for adding to it stated inline |
| Team picks feel arbitrary the one time they go wrong | Same fix as §10.0's background-industry risk: the attribution line is generated from the same inputs that produced the outcome, not decorative flavor text bolted on after |

## 16.8 Where this lives in the engine

Nothing here needs a new subsystem — it needs a thin layer in front of decision points that already exist, reusing the recommendation math those systems already compute.

**Two gaps have to close first, both small and both in the same shape.**

`leverage/catalogue.py`'s `agent_tier` is currently just a string on `LeverageState` (`unrepresented | regional | boutique | major | powerhouse`, advanced by `try_advance_agent_tier()`), with no link to any actual NPC — while `rolodex/npc.py` already generates NPCs of `npc_type == "agent"`. §16.6's personality mechanism needs those to be the same entity. Fix: the first successful `try_advance_agent_tier()` call (past `unrepresented`) generates or promotes one tracked `npc_type="agent"` NPC to represent the tier from then on.

The producer voice needs the mirror-image fix: a `producer` NPC generated per project already gets a `name` and an `agenda` from `generate_npc()`, but §16.6 deliberately wants it to carry *no independent* `affinity`/`grudge` — those fields should read through to `studio_relations[role.studio]` instead of being set on the NPC itself. Concretely: `narrator.py`'s producer branch never reads `npc.affinity`/`npc.relationship_state` directly, it computes a `relationship_state`-shaped value from the studio trust score using the same banding `state_after_update()` already uses, and displays the producer NPC's name against it. No new field on `NPC`, no second score to keep in sync — the studio-trust number the game already has just gets a face put on it per project.

Both are genuine improvements to the existing systems, not scope added for this Part — right now the agent tier is powerful and nameless, and studio trust is exactly as real as a relationship but has never been allowed to talk.

- **`engine/team/policy.py`** — per-player `DelegationPolicy`: one of the three §16.4 states per category, read against `leverage_status()` at read-time so a policy can't be set above what's earned.
- **`engine/team/decide.py`** — one function per delegable category, each a thin wrapper around the *existing* formula (`actor/offers.py:utility()`, `actor/shape.py`, etc.) that samples the safe end of the distribution instead of the full one, per §16.5.
- **`engine/team/narrator.py`** — turns a `(category, choice, inputs, source)` tuple into the one attributed line from §16.6. For the agent and director voices, `source` is the deciding NPC and its `agenda`/`relationship_state`; for the producer voice, `source` is the current project's `studio_relations` entry, read the same way.
- **`Session`** — every method that currently blocks on player input for a delegable category gains a policy check at the top, against its real signature:
  - `offer_board()` / `accept()` / `decline_board()` → agent category, resolved against the one persistent agent NPC
  - `play_scene()` (Setup and Resolution calls only — never the Turn, per §16.3) → unvoiced, safe-default category, no NPC lookup
  - `choose_deal()`'s approvals flags → director category, resolved against whichever `npc_type="director"` NPC is attached to the current project, preferring a `requested_director_npc_id` match when one exists so a recurring director's own trust (`director_relations`) governs the pick
  - `choose_release()`, and `choose_deal()`'s bonus/dev-slate-adjacent flags → producer category, resolved against the current project's `role.studio` entry in `studio_relations`

  `choose_director_casting_action()` gets no policy check — it stays a plain, always-manual call, per §16.3.

  `Ask me` behaves exactly as today; `Suggest, then I decide` returns the recommendation alongside the normal options; `Handle it` calls `team/decide.py`, applies the result, and queues the `team/narrator.py` line for the next screen that shows attribution (in-the-moment for anything dramatic enough to warrant it, batched into the Reckoning recap otherwise).

This should land late in the build plan (§13) — after Phase 5b (leverage) and the director phases, since every category it wraps has to exist and be tuned first. It touches no formula anyone else depends on; it only decides, sometimes, not to ask.
