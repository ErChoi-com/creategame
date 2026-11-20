# Gameplay Simplification Review: Complexity and Player-Facing Clarity

*A teardown of the game as it is actually played through `simulation/session.py` (`Session`) and `simulation/cli.py`. This review is about complexity: how many systems, verbs and decisions per year the player faces, and which of them they can read and enjoy. It assumes the balance work and does not repeat it: `callback-design-review.md` (v8 structural review), `part-00-design-rules-and-cut-list.md` (§0.1 Decision Test, §0.2 decision budget, §0.5 cut list), `decision-map.md` (115 option IDs), and `.planning/phases/03–05` (Standing ceiling, net-worth clustering, the five unreachable gates). Where a finding here is downstream of one of those, it is cited rather than re-argued.*

## Method

- **Auto runs.** `python3 -m callback.engine.simulation.cli --auto --seed=N` for seeds 1, 2, 3, 4, 5, 7, 11 and 42. **Every run crashed within 1 to 6 in-game years** (see §3.7), so the auto flow cannot complete a career.
- **Instrumented driver** (`/tmp/cb_drive.py`). It mirrors `cli.py`'s exact prompt sequence through `Session` (`offer_board` → `accept` → deal → prep → `play_scene` ×N → `choose_release` → awards → directing → `end_year`). It works around both CLI crashes and counts every prompt the CLI would show, plus its option count. It ran 8 seeds × 30 years with a random but legal policy, acting-only and acting+directing (directing from age 24), across all four backgrounds.
- **Choice-sensitivity probes** (`/tmp/cb_sens.py`, `/tmp/cb_scene_search.py`, `/tmp/cb_rating.py`, `/tmp/cb_dev.py`). Each one `copy.deepcopy`s a `Session` right after `accept()` (common random numbers), varies one decision, resolves, and compares what the Post & Release screen shows. The probes ran over about 30 projects, at career year 1 and year 9.
- **Hand-driven run** (`/tmp/cb_manual.py`, seed 21, Discovered / The Prize). Ten years of acting, plus directing from year 3, reading the actual strings the player gets back.

---

## 1. Breakdown: every player-facing decision, in the order a year meets it

Frequencies are measured per player-year (acting-only, 240 player-years) unless marked otherwise.

| # | System | Session methods | Choices | Mandatory? | How often | Notes |
|---|---|---|---|---|---|---|
| 0 | Character creation | `background_options`, `ambition_options`, `start` | 4, then 6 | Once per run | Once | Ambition is cosmetic (`decision-map.md` §Character creation). But `cli.py:47` tells the player it "decides what your obituary measures you against". `obituary_summary()` never reads it. |
| 1 | Year menu | `directing_unlocked` | 2–3 (act / direct / done) | Yes | 1.00 | Asked even of a player who never directs. |
| 2 | Pull gate | `rolodex_summary`, `interact`, `leverage_status`, `try_advance_agent_tier`, `franchise_status`, `spinoff_options`, `multi_picture_deal_status`, `studio_relations_status`, `director_relationship_status` | "[Enter] or [p]", then up to 5 sub-prompts | Optional | 1.00 (interactive only) | Only `check_in` of the 4 `interact` verbs is reachable. `disappear` and `cut_lifestyle_floor` are not in the CLI at all. |
| 3 | Offer board | `offer_board`, `generate_more_listings`, `director_info`, `accept`, `decline_board` | Pick 1 of the available listings, keep looking, pass, or look up a director | Yes | **8.81 prompts per year** | 20–30 listings per board (`session.py:198-199`), **about 100 rows read per year**, 0.87 available on average. 41% of years have none, 46% have exactly one, and **12% have a real choice between 2 or more roles**. |
| 4 | Franchise holdout | `holdout_available`, `request_holdout` | 2 | Gated | 0.013–0.017 | |
| 5 | Deal: bonus type | `box_office_bonus_available` ×2, `choose_deal` | 2–3 | Gated | **0** | The gate is unreachable (05-REPORT #5). |
| 6 | Deal: approvals | `approvals_available`, `choose_deal` | 2 | Gated | **0** | Unreachable (05-REPORT #4). Every year prints "standard terms". |
| 7 | Multi-picture deal | `multi_picture_deal_available`, `multi_picture_deal_terms`, `sign_multi_picture_deal` | 2, then 2 | Gated | 0.008–0.033 | |
| 8 | Marketing push | `request_marketing_push` | 2 | Asked on every role | 0.65 | The studio honours it 5–9% of the time. |
| 9 | Script notes | `script_notes_available`, `choose_script_note` | 4 | Gated | **0** | Behind approvals. |
| 10 | Request a director | `available_directors`, `request_director` | 1 + N | Gated (tracked directors) | 0.15 | It costs 2 favours, and a new actor holds 0. |
| 11 | Scene partner + orientation | `costar_options`, `choose_orientation` | 1 + N, then 3 | Gated (tracked costars) | 0.65 (2 prompts) | |
| 12 | Prep | `prep_options`, `choose_prep` | 5 | Yes, per role | 0.65 | |
| 13 | The shoot | `episode_labels`, `scene_names`, `dial_options`, `position_options`, `play_scene` | 4 per dial | Yes, per role | **8.55 prompts per year** | 3 scenes × 4 dials = **12 prompts per film, 24 per series**. |
| 14 | Rating stance | `rating_preview`, `choose_rating_stance` | 2 | Gated (borderline films) | 0.27 | Also asked on series. |
| 15 | Release request | `release_options`, `choose_release` | 5 | Yes, per film | 0.59 | The studio overrules it **74%** of the time. |
| 16 | Streaming or festival bids | `choose_release(…_bid_selector=)` | Number of bids | Gated | 0.25 | |
| 17 | Awards campaign | `awards_campaign_available`, `available_award_categories`, `run_awards_campaign` | 2, then category, then fraud (2) | Gated | **0 in 240 player-years** | |
| 18 | Directing (when on) | `become_director`, `director_status`, `start_directing_project`, `choose_director_*_action` ×4, `request_director_*`, `scrap_directing_project`, `advance_directing` (9 actions), `attach_star_*`, `check_for_hire_offer`, `accept_hire_offer`, `decline_hire_offer`, `run_director_awards_campaign` | 9 prompts per pitch; 4 per quarter; +2 to attach a star | Optional career | **+19.7 prompts per year** | The quarter loop (scrap, which project, dev action, another quarter?) costs 14.9 prompts per year. Under a random-but-legal policy it took **874 development quarters to produce 22 films**, about 160 prompts per directed film. |
| 19 | Reckoning and trades | `end_year`, `standing_summary`, `trades` | 0 | — | 1.00 | `end_year()` returns the directed films that wrapped, and `cli.py:794` throws that return value away. |
| 20 | Obituary | `obituary_summary` | 0 | — | End of run | The strongest payoff in the game: the roles you declined, and "your best hidden performance". |

**Total measured load:** **22.2 prompts per year for an acting-only career** (range 19–42; all four backgrounds land between 22.2 and 22.8). An actor-director faces **42.0 per year** (range 19–65). The targets in `part-00` §0.2 are **13 actor-only and 19 total**. Acting-only play runs at 1.7× budget and actor-director play at 2.2×.

**How many of those are real decisions?** A real decision has two defensible options and a consequence the player can read. By that test (evidence in §3), **fewer than 3 of the 22 qualify in a typical year**: which role to take (live in 12% of years), prep (weak), and occasionally the rating. About 17 of the 22 prompts are navigation, a dominated choice, or a request the engine ignores.

The public API compounds this. `Session` has **110 public methods**. **22 of them are unreachable from `cli.py`**, including `disappear`, `cut_lifestyle_floor`, `pitch_reboot`, `push_director_deal_for_backend`, the adaptation pickers, and three of the four `interact` verbs. Those players can't reach at all. Others are asked every year with no consequence.

## 2. The core loop in one sentence

> **Each year you choose one role from what the industry actually offers you, decide how to play it, and watch reception move your Standing — which decides what you're offered next — until age, money or the calendar ends the career and the obituary reads back what you took and what you turned down.**

The 3–5 systems that carry that sentence:

1. **The offer board and the calendar** (`offer_board` / `accept` / `decline_board`, with `quarters_for_role`). This is the "what you say yes to" from §3.1.
2. **The performance**: prep and the three scenes (`choose_prep`, `play_scene`). This is the player's only hands-on creative act.
3. **Reception with attribution** (`choose_release`'s summary, the Post & Release screen). Rule 2, "always attribute", lives or dies here.
4. **Standing and Persona at the Reckoning** (`end_year`, `standing_summary`, `persona_status`). This closes the feedback loop into the next offer board.
5. **The obituary and declined roles** (`obituary_summary`, §10.0 / §11.8). This is the career-level payoff.

The rest is supporting texture that should surface when it matters: the Rolodex, leverage, franchises, life, directing and awards.

## 3. Complexity problems (with evidence from the runs)

### 3.1 Decisions whose consequence the player cannot read

| Decision | Evidence | Why |
|---|---|---|
| **Release request** (`choose_release(strategy)`) | Year 1: 0 of 29 projects changed outcome across all four requests. Year 9: 1 of 29. Overruled 74% of the time overall. In the hand-driven run: asked for Limited on 5 films and was overruled on all 5. | `actor_influence_on_studio_decision` (`actor/studios.py:124`) is a power-4 curve on Standing. Nobody gets near the top of it (05-REPORT #3). |
| **Marketing push** | Honoured 5–9%. When it's honoured, mean ROI falls (0.76 → 0.64). | Same curve. When the push works, it buys spend the film can't recoup. |
| **Orientation** (generous / upstage) | Mean critic-score range 0.7 points. The shown band changes in 3% of projects. | Its real payoff is relationships and the §5.7 trust chain, and that payoff is never attributed on screen. |
| **Prep** | Critic range 1.5 points. The "Your work" band changes 31–38% of the time, with no line saying why. | It moves Performance, but Post & Release never names prep as a cause. |
| **The shoot vs. "Your work"** | Across all-With, all-Beneath, all-Beyond and all-Against, Performance was **identical (50.56)**, while the critic score moved by 22.8 points. | What you played shows up on the "Critics" line, not the "Your work" line. The attribution chain the UX promises (ux/03 §5) is inverted. |
| **Ambition** | No mechanical effect (`decision-map.md`). | The CLI copy promises an effect that doesn't exist. |
| **Director momentum** | In the hand-driven run, "momentum: can't-miss" held for 16 consecutive quarters before the greenlight. | `momentum_band` describes momentum. It doesn't describe greenlight odds, but it reads as if it does. |
| **Your own directed film's reception** | Visible only in the `end_year()` return value, which `cli.py` discards. | The director never sees how the film did. |

### 3.2 Near-duplicate verbs (the parallel actor and director surfaces)

`Session` has two copies of most project verbs, with different names, signatures and option lists:

- `request_marketing_push()` ↔ `request_director_marketing_push_action(i)`
- `release_options()` / `choose_release()` ↔ `director_release_options()` / `request_director_release_strategy(i, s)` (the same `RELEASE_STRATEGIES` list)
- `script_note_options()` (4) / `choose_script_note()` ↔ `director_script_note_options()` (3) / `choose_director_script_note_action()`
- `run_awards_campaign()` ↔ `run_director_awards_campaign()`
- `box_office_bonus_available()` / `choose_deal(want_box_office_bonus=)` ↔ `director_box_office_bonus_available()` / `push_director_deal_for_backend()`
- `spinoff_options()` / `launch_spinoff()` ↔ `directing_spinoff_options()` / `launch_directing_spinoff()`
- `actor_quarters_remaining_this_year()` ↔ `quarters_remaining_this_year()`
- `available_directors()` / `request_director()` ↔ `attach_star_target_options()` / `choose_attach_star_target()` (both mean "pull a Rolodex NPC onto my project")
- `director_casting_options()` (5) ↔ `attach_star_type_options()` (3). Both mean "who's in my film", answered twice per directed project.
- Self-financing appears twice: `start_directing_project(self_financed=True)` and the `self_finance` dev action.
- Relationships have four read-outs: `rolodex_summary`, `studio_relations_status`, `director_relationship_status`, `director_info`.
- Money has three finders: the `new_financier`, `call_in_favour` and `take_to_market` dev actions overlap with no stated difference.

§3.3's "one spine" rule is honoured in the engine (`core/meters.py`, the shared release and marketing curves) and broken at the façade. The player learns every verb twice.

### 3.3 Choices with an obviously dominant option

- **Scene positions.** "Match it" on all 12 dials beat **all 150 random combinations** on critic score. The "shaped read" (`part-05` §5.6, line 249: one *against* at the turn, everything else restrained) **lost** to all-With in all 12 placements, by 0.3–2.8 critic points. All-Against cost 25 critic points and 0.34 ROI. This is the most repeated interaction in the game (12 prompts per film), and its optimal play is to press `1` twelve times, which is also the CLI default. It fails both halves of §0.1.
- **Rating.** Release as shot beats the cut on critic score (58.3 vs 54.8) and on ROI in 77% of borderline films.
- **"Shelved"** as a release request is never correct (`decision-map.md` notes that no studio prefers it).
- **Agent tier.** `decision-map.md` itself labels it "Automatic-if-eligible". It's a button you press whenever it lights up.
- **Keep looking.** When nothing on the board is available, it costs nothing to press, so you always press it (7.8 presses per year). It quietly raises application fatigue ("overexposed" in the hand-driven run), and the player can't see that cost.
- **Development actions.** On a first low-budget drama, `attach_star` greenlit 38 of 60 seeds within 4 years. `option_adaptation` managed 2 of 60, and `drawer` / `self_finance` managed 0 of 60. Of the 9 options, 3 are traps for a new director and the menu gives no hint which.

### 3.4 Systems that rarely or never trigger, but still own screens and prose

- **Never in 240 player-years:** approvals, script notes, both bonus types, merchandising, both spin-offs (all confirmed unreachable in `decision-map.md` §Flagged and 05-REPORT #4–7), and the **awards campaign**. That last one means a player who picks **The Prize** never sees an awards prompt.
- **1–3% of years:** holdout, multi-picture deal, hire offer, platform expansion, director awards.
- **Seven of `cli.py`'s roughly 25 screen functions** (`franchise_screen`, `_negotiate_bonus_type`, `multi_picture_deal_screen`, `script_notes_screen`, `awards_screen`, `director_awards_screen`, `hire_offer_screen`), plus the spin-off, expansion and deal-break blocks in `pull_menu`, serve systems that fire in under 3% of years. `deal_screen` adds an eighth that, in practice, only ever prints "standard terms". They aren't harmful, but nothing tells the player they exist until, decades in, one fires with no context.

### 3.5 Jargon and raw internals on screen

These are all seen in real output, and all break ux/01 Rule 3 ("numbers are for the game"):

- `director: n_002 (someone you haven't really met)` and "Whose id? (see 'director: <id>' on a listing)". The player is asked to type an internal NPC id.
- `indispensability 31.2, recast cost $X M`, `scarcity: 0.0`, `agent tier: unrepresented`, `net P&L $-1.2M`, `Critics: cold (43/100)`, `ROI 0.72x`, `Wk1 $… Wk2 $…`
- `demand: steady` on **99.8% of listings**: 5,782 of 5,794 across 29 seeds × 8 years. It carries no information.
- `typecasting_note` is always `None`. `in_your_lane`, `breaking_type` and `quarters_required` are computed but never shown, even though ux/03 says the calendar cost is one of the five things every card shows. `in_your_lane` and `breaking_type` were both true on 496 listings, which contradicts itself.
- The Energy / Size / Warmth / Tempo dials, each with "Match it / Hold back / Go big / Play against it", where "Match" refers to a film palette the CLI never displays (ux/03 §3a's palette screen doesn't exist).
- The `PREMIERE` / `FINALE` headers for a series, with no explanation.
- A truncated option label: "Net points — … only once the studio's whole".

### 3.6 The offer board is a slot machine, not a board

`Session.offer_board()`'s own docstring admits it: "more looks at the dice, not a smarter die." In practice the player sees 20–30 rows. About 97% of them read "(an audition — but it doesn't come through this year)", and then comes "Keep looking" up to 18 times. ux/03 §1 specifies 2–7 cards, each explaining *why this role reached you*. The real decision the pitch is built on, "every yes is a no" (§3.2 pillar 4), is live in about one year in eight.

### 3.7 The playable flow can't finish a career

Two crashes kill every auto run:

- **`KeyError: 'studio_overruled'`** (`cli.py:343`). `acting_block` sends series roles through the film `release_screen`, but `choose_release()` hands series to `_choose_release_series()`, which has no such key. Series are 6–10% of accepted roles, and each one also costs 24 dial prompts.
- **`KeyError: 'budget_millions'`** (`cli.py:623`). Since v12, `greenlit` means "cameras rolling" (`session.py:1976`), and the resolved film only comes back from `end_year()`.

On every seed tested, the auto flow dies before age 29. That alone explains how an 8.8-prompt "keep looking" grind and a 12-prompt dial sheet survived design review.

## 4. Simplified design

**Principles.** These are part-00's rules, applied to the façade:

1. **One push per beat.** Each stop in §3.4's loop asks at most one question.
2. **Auto unless opened.** Every sub-choice gets a sensible default and a visible "change this". This is `creative-revamp-plan.md` §11.1's auto-fill/override principle, applied to today's systems instead of waiting for the scene grammar.
3. **Don't ask what the engine will ignore.** Requests the studio overrules become events ("The studio's taking it to Toronto"). The ask comes back once the player has the standing for it to matter. Being overruled is very Hollywood; being *asked* and then ignored every time is not.
4. **Reveal by relevance.** A tab, verb or prompt appears the first time it can fire (Rule 3 run in reverse, as ux/01 already argues). It never appears greyed out before that.

### The year, after

| Stop | After | Prompts |
|---|---|---|
| Year menu | Gone for an actor-only player. "Step behind the camera" becomes a one-time pushed card, offered after 3 credits or a director Ally, and always available in pull afterwards. | 0 |
| **Offers** | Only listings that came through, capped at 4, plus up to 2 "long shots" marked as auditions. "Keep looking" becomes one pull verb, "Have your agent push harder" (once a year, cost stated in words; it reuses `application_fatigue_tax`). Each card shows billing, genre, fee, **quarters**, and one "why it reached you" line. Demand shows only when it isn't "steady". Directors appear by name. | 1 |
| **The deal** | One card with at most 2 options. Session picks the live axis: holdout, multi-picture, approvals, points or merch, in that order (ux/03 §2 already says this). When nothing's live, nothing is asked. Requesting a director moves to the Leverage tab, since it spends a favour. | ~0.1 |
| Scene partner | Asked only when a tracked costar is **Familiar or closer**. Otherwise it defaults to "play it straight". The relationship consequence is named at the Reckoning ("Priya noticed you gave her the scene"). | ~0.3 |
| **Prep** | Kept: one of five. It's the actor's ritual and reads like the job. Post & Release gains a cause line ("The dialect work showed"). | 1 |
| **The shoot** | **One read per scene**: Match it / Hold back / Go big / Play against it, applied to that scene's carrying dial from §5.6's per-genre table. The other three dials auto-fill. "Work it dial by dial" stays as an opt-in override. A series asks for the premiere turn and the finale turn only. | 3 (series: 2) |
| Rating | Auto "release as shot", asked only when `rating_studio_pressure` is real (a fight with the studio, not a form). | ~0.1 |
| **Release** | Not asked while `actor_influence_on_studio_decision` is below a threshold; the studio's choice is shown as an event instead. Never offer "Shelved". Streaming bids auto-take the best. A **festival bidding war** (2 or more bids, including self-release) stays as a prompt, because it's the Sundance moment. Marketing push merges into this ask ("…and push for a real campaign"). | ~0.3 |
| Awards | When it fires: one prompt, "Campaign for X?", with the best category chosen automatically. Category fraud is the only sub-choice, offered when it applies. | ~0.05 |
| Reckoning | Shows wrapped directed films, any agency signing (automatic, as a toast), and the year's one relationship moment. | 0 |
| **Directing** | A pitch is 3 prompts: genre, budget tier, and **"how you'll make it"**. That last one is a stance that bundles casting, shoot style and script note into one choice (e.g. *Studio-safe*, *Auteur*, *Guerrilla*, or *Custom*). Release and marketing are asked once the film wraps. Development is **one standing order per project per year** (Push it / Rewrite / Attach someone / Drawer), and Session spends the quarters. This restores part-00 §0.5's own cut ("one action per project per year"), which §7.4 v16 undid. | ~3 |

**Before and after decisions per year.** "Before" is measured; "after" is projected from the trigger rates above.

| | Before (measured) | After | part-00 §0.2 target |
|---|---|---|---|
| Acting year with a role | ~23 | **~6** | — |
| Acting year without a role | ~9 (board navigation only) | **1** | — |
| **Acting-only, average** | **22.2** | **~4.5** | 13 |
| Directing on top | +19.7 | **+~3** | +6 |
| **Actor-director, average** | **42.0** (max 65) | **~8** (max ~12) | 19 |

This deliberately comes in under budget. The freed room of about 8–10 prompts a year is reserved for the content the design says is the game and that is completely unbuilt: **§5.12's three on-set moments** ("the scene that isn't working", "the adjustment you disagree with", "the discovery"). These are the most *Hollywood* decisions in the design documents. Today their slot is held by a dial spreadsheet.

**What this protects.** The calendar cost of a role, the studio overruling you (now shown as an event rather than a fake choice), the holdout, the festival bidding war, category fraud, the call from a studio (hire offer), the trades, declined roles resolving into other people's careers, and the obituary. Nothing about the Hollywood feel depends on the player clicking Energy / Size / Warmth / Tempo four times per scene.

## 5. Cut / defer list

**CLI** means presentation only. **Session** means façade logic in `session.py`, with no engine change. **Engine** means it touches `actor/`, `director/`, `life/` and so on, and must follow CLAUDE.md's conventions (frozen dataclasses, `replace`, docstrings citing design sections, one-way imports).

| Item | Action | Reason | Layer |
|---|---|---|---|
| Per-dial scene prompts (12 per film) | Collapse to 1 per scene plus an override | All-With is dominant; this is the biggest single prompt sink | Session + CLI |
| "Keep looking" / `generate_more_listings` spam | Collapse into one yearly agent push | Navigation, not a decision; its hidden cost is fatigue | Session + CLI |
| Release request below star level | Hide; show the studio's decision | 0 of 29 outcomes changed at year 1 | Session + CLI |
| "Shelved" as a request | Cut from `release_options()` | Never correct | Session |
| Marketing push as its own y/n | Merge into the release ask | Honoured 5–9%, and lowers ROI when it is | CLI |
| Streaming bid picker | Auto-take the best, report the buyer | The CLI already defaults to the best; the prompt is redundant | CLI |
| Rating prompt on every borderline film | Ask only under studio pressure | Release as shot dominates | Session + CLI |
| Bonus type sub-choice (net vs. first-dollar gross) | Fold into one Deal card | Unreachable today (05-REPORT #5) | CLI |
| Actor script notes, merchandising, actor spin-off, director spin-off | **Defer**: hide until reachable | Unreachable gates (`decision-map.md` §Flagged); a fix belongs to the balance track | CLI (engine later) |
| Agent tier as a verb | Automate at `end_year()` with a toast | "Automatic-if-eligible" is not a choice | Session |
| Year menu (act / direct / done) | Hide until the player opts into directing | One wasted prompt per year for most players | CLI |
| Director request | Move to the Leverage tab | A favour spend, which is pull by §0.3 Rule 2b | CLI |
| Director 9-prompt pitch | Collapse to genre, tier and stance | Pre-committing casting and style before development reads as a form | Session + CLI |
| Quarterly development loop | One order per project per year | §0.5 already cut this; 160 prompts per film | Session + CLI |
| Self-financing as both a pitch flag and a dev action | Merge into one | Duplicate verb | Session |
| Adaptation source type and licensing fraction | **Defer** (not in the CLI today) | Two sliders on top of a dev action that greenlit 2 of 60 | — |
| Raw ids and numbers on screen (`n_002`, indispensability, scarcity, ROI, critic /100) | Replace with names and bands | ux/01 Rule 3 | Session (add display names) + CLI |
| `demand_band` while "steady" | Hide | 99.8% "steady" | CLI |
| Ambition copy | Fix the copy now; wire it into the obituary later | The CLI makes a false promise | CLI now, Engine later (`life/obituary.py`) |
| `disappear`, `cut_lifestyle_floor`, `show_up` / `read_agenda` / `vouch` | **Surface** in pull (these are the reverse of a cut) | Designed, built and unreachable | CLI |
| Duplicate actor/director façade methods | Unify behind one verb per concept; keep the old names as thin aliases | Halves the API a UI must learn | Session |

## 6. Ordered implementation plan

Each step ships on its own and leaves `python3 -m unittest discover -s callback/engine/tests` green. Steps 1–7 never touch engine packages. Step 8 is the only engine work, and it follows CLAUDE.md.

1. **Make a career finishable.** In `acting_block`, skip `release_screen` when `session.is_series()` and print the series summary (its `license_value_millions` and renewal fields). In `_print_directing_result`, print "cameras roll" on greenlight instead of reading the resolved-only fields. In `run()`, print `session.end_year()`'s wrapped films at the Reckoning. Add an auto-mode smoke test over about 10 seeds × 40 years. *Files:* `simulation/cli.py`, new `tests/test_cli_auto_smoke.py` (coordinate the name with the in-flight `mcp_server` test).
2. **An honest offer board.** Have the CLI show only `available` listings, plus at most 2 long shots, and replace the keep-looking loop with one yearly "agent push" (`Session.agent_push()` wrapping `generate_more_listings` with a fixed batch). Show `quarters_required`, and hide `demand_band` when it's "steady". Add a `display_name` to `_director_tag` / `director_info` so no id is ever typed. *Files:* `session.py` (`_listing_extra_fields`, `director_info`, new `agent_push`), `cli.py` (`offer_board_screen`, `_print_listings`).
3. **One read per scene.** Add `Session.carrying_dial(scene_index)` from §5.6's genre table and `Session.play_scene_read(position, overrides=None)`, which fills the non-carrying dials with `"with"` and calls `play_scene`. The CLI asks 3 prompts (2 for a series), with "dial by dial" as an opt-in. File the all-With dominance as a balance finding for the `.planning` pipeline; don't tune it here. *Files:* `session.py`, `cli.py` (`shoot_screen`). *Cites:* `part-05` §5.6, `creative-revamp-plan.md` §11.1.
4. **Stop asking what the engine ignores.** Add `Session.release_request_matters()`, which compares `actor_influence_on_studio_decision(trust, importance)` against a threshold. Filter "shelved" out of `release_options()`. Fold the marketing push into the release prompt. Auto-take the best streaming bid. Ask the rating question only when the studio is pressuring. Fix the ambition copy. *Files:* `session.py`, `cli.py` (`release_screen`, `marketing_push_screen`, `rating_screen`, `character_creation`).
5. **One Deal card.** Add `Session.deal_options()`, which returns at most 2 plain-language options from {holdout, multi-picture, approvals, points, merch}, plus `choose_deal_option(key)`, which routes to the existing `request_holdout`, `sign_multi_picture_deal` and `choose_deal`. The CLI's five deal screens collapse into one. *Files:* `session.py`, `cli.py` (`franchise_screen`, `deal_screen`, `multi_picture_deal_screen`, `script_notes_screen`).
6. **Directing at human cadence.** Add `Session.director_approach_options()` and `choose_director_approach(i, key)`, which bundle the casting, shoot-style and script-note setters into presets. Add `Session.plan_directing_year(i, order)`, which loops `advance_directing` over the remaining quarters and stops on greenlight, death or limbo. Ask release and marketing at wrap time. Unify the duplicated actor/director verbs behind one `request_release(...)`, `request_marketing_push(...)` and `run_awards_campaign(...)`, keeping the old names as aliases. *Files:* `session.py`, `cli.py` (`_maybe_pitch_new_project`, `_directing_quarter`, `directing_block`). *Cites:* `part-00` §0.5, `part-07` §7.4.
7. **Reveal by relevance and automate chores.** Auto-advance the agent tier inside `end_year()` and report it. Show the year menu only after the player opts into directing. Make Rolodex, Leverage and Franchise appear in the pull menu on first relevance, and surface `disappear`, `cut_lifestyle_floor` and all four `interact` verbs there. Move director requests to Leverage. *Files:* `session.py` (`end_year`), `cli.py` (`year_screen`, `pull_menu`, `director_screen`).
8. **Engine, later, and convention-bound.** (a) Make contrast positions pay on the "Your work" line, so that the three reads are a real choice (`actor/positions.py`, citing §5.5 and §5.6; this goes through the `.planning` sweep). (b) Wire ambition into `life/obituary.py` (§0.4). (c) Build §5.12's on-set moment pool into the freed prompt budget, as a new `actor/` module citing §5.12 and exposed through one `Session.on_set_moment()` / `choose_on_set_response()` pair. *Files:* `actor/positions.py`, `life/obituary.py`, a new `actor/` module, `session.py`, `cli.py`, and tests.
