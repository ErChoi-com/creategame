# Decision Map — Every Mechanically-Branching Choice in the Engine

*Reference doc, deliberately outside the `part-00`..`part-16` series — like `creative-revamp-plan.md`, this is a catalog other work cites back to, not a design chapter with its own argument. Built for Phase 1 of the Playtest & Balance Pass (MAP-01): every discrete, mechanically-branching decision point reachable through `simulation/session.py`'s `Session` class, one row per discrete option value, each citing the module/function that implements it and (where the implementing module carries one) the design-doc section it traces back to.*

*Only choices that affect simulated state/outcomes are cataloged. Purely cosmetic/flavor text with no mechanical branch is excluded — see the Character Creation section's callout on `ambition` below for the one field this specifically rules out.*

## How to read this catalog

Every row's `ID` is the vocabulary `callback/engine/simulation/_decision_coverage.py` reads to check playtest coverage — `_decision_coverage.py`'s `load_expected_ids()` parses this file's own ID column at call time (never a hardcoded duplicate list), so an ID present here and absent from a policy's tally is what a coverage gap looks like.

Two things worth knowing before reading "covered" off a coverage report:

- **Requested vs. resolved (studio overrule).** For any decision with a studio/engine-resolved outcome that can differ from what the player asked for — release strategy is the clear case (`Session.choose_release(strategy)` treats `strategy` as a *request*; the studio's actual decision, reported back as `result["release_label"]`, can differ) — this catalog's row represents the *requested* decision, the player-facing choice. That's what `_decision_coverage.py` counts as "covered." The resolved outcome is a secondary, informative signal a policy may also want to tally, but it is never the coverage gate itself.
- **Series projects skip the whole release/box-office branch.** Whenever `project_type == "series"`, `Session.choose_release()` dispatches to `_choose_release_series()` instead of the film-shaped release/box-office-bonus path — by design, a season isn't sold to theaters or shopped for streaming rights the way a film is. A run-year that happens to land a series role and so contributes zero release-strategy/box-office-bonus tallies that year is not itself a coverage failure; the tool only requires each ID to be visited at least once across a whole sampled run, not in every year it could theoretically apply.

---

## Character creation

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `character_creation.background.conservatory` | Starting background | Conservatory — trained, broke, unknown | `simulation/_backgrounds.py` (`BACKGROUND_TABLE`) via `Session.background_options()`/`start()` | design/ux/01-principles-and-first-session.md |
| `character_creation.background.discovered` | Starting background | Discovered — a manager, momentum, no technique yet | `simulation/_backgrounds.py` (`BACKGROUND_TABLE`) via `Session.start()` | design/ux/01-principles-and-first-session.md |
| `character_creation.background.regional_stage` | Starting background | Regional stage — years of range, no union credits, an older start age (`REGIONAL_STAGE_START_AGE = 33`) | `simulation/_backgrounds.py` (`BACKGROUND_TABLE`) via `Session.start()` | design/ux/01-principles-and-first-session.md |
| `character_creation.background.family_money` | Starting background | Family money — the rent's solved, starting `MoneyState(net_worth=2.0)` | `simulation/_backgrounds.py` (`BACKGROUND_TABLE`) via `Session.start()` | design/ux/01-principles-and-first-session.md |

**Ambition is intentionally NOT cataloged as a decision point.** `Session.ambition_options()`/`start()` (`session.py:302-318`) writes `self.ambition` once and reads it nowhere else in the codebase besides the one greeting string returned by `start()` itself — confirmed by a full-file grep of `self.ambition` in `session.py` this phase's research session. It has zero mechanical effect on any formula in the engine as currently implemented. This is documented here as "investigated and confirmed cosmetic-only," not forgotten — per this phase's own CONTEXT.md exclusion rule ("purely cosmetic/flavor text with no mechanical branch is excluded"). Fixing this (if the design intent was for ambition to actually branch something) is out of Phase 1's scope.

## Offer board / casting

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `offer_board.accept` | Accept a listing | `accept(index)` | `actor/offers.py` (`resolve_casting_path`) via `Session.accept()` (`session.py:545-583`) | design/part-04-the-actor.md §4.4 |
| `offer_board.decline` | Decline the whole board | `decline_board()` | `Session.decline_board()` (`session.py:591-604`) | design/part-04-the-actor.md §4.4 |
| `offer_board.generate_more_listings` | Scan deeper than the initial board | `generate_more_listings(count)` | `Session.generate_more_listings()` (`session.py:355-359`) | design/part-04-the-actor.md §4.4 |

## The Deal

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `deal.approvals` | Request script + costar approvals | `want_approvals: bool` | `leverage/approvals.py` via `Session.choose_deal()` (`session.py:913-945`) | design/part-06-leverage.md §6.3 |
| `deal.box_office_bonus.net_points` | Box-office bonus type | Net points — real share of profit, only once the studio's recouped its break-even | `leverage/approvals.py` via `Session.choose_deal(bonus_type="net_points")` (`session.py:888-902,913-945`) | design/part-06-leverage.md §6.3/§6.5 |
| `deal.box_office_bonus.first_dollar_gross` | Box-office bonus type | First-dollar gross — paid from dollar one, rarer ask, needs far higher Standing | `leverage/approvals.py` via `Session.choose_deal(bonus_type="first_dollar_gross")` (`session.py:888-902,913-945`) | design/part-06-leverage.md §6.3/§6.5 |
| `deal.merchandising` | Negotiate a merchandising royalty | `want_merchandising: bool` (animated franchise role + Standing gate) | `leverage/merchandising.py` via `Session.choose_deal(want_merchandising=True)` (`session.py:904-945`) | new mechanic — not adapted from an existing design/ section per `leverage/merchandising.py`'s own docstring; a direct extension of §6's leverage-play family |

## Script notes

**Actor-side script notes (`clarity`, `ambiguity`, `your_part`, `whole_film`) are intentionally NOT cataloged as required coverage IDs — see the Flagged Balance Finding after the Awards section below.** All four route through the identical `Session.script_notes_available()` gate (`"script" in self._approvals`, `session.py:949-950`), which is only ever true when `deal.approvals`' `want_approvals` request was actually *granted* — gated on `APPROVAL_STANDING_THRESHOLD = 65.0` weighted Standing, a bar this phase's research found effectively unreachable through simulated play. Per this phase's CONTEXT.md exclusion rule and the `ambition` precedent above: investigated and confirmed currently-unreachable, not forgotten. `core/script_notes.py` via `Session.choose_script_note(key)` (`session.py:952-962`), design/part-05-the-work.md §5.15, for reference if a future phase reopens this gate.

## Rating stance

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `rating.actor.cut` | Rating stance (only when `rating_cut_available()`) | Cut for the friendlier rating — the compromise shows on screen | `actor/rating.py` via `Session.choose_rating_stance(RATING_CUT)` (`session.py:972-983`) | design/part-05-the-work.md §5.19 |
| `rating.actor.release_as_shot` | Rating stance | Release as shot — the harder rating, the film you made | `actor/rating.py` via `Session.choose_rating_stance(RATING_RELEASE_AS_SHOT)` (`session.py:972-983`) | design/part-05-the-work.md §5.19 |

## Costar orientation

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `costar.orientation.neutral` | How you play toward your scene partner | Play it straight | `actor/positions.py` via `Session.choose_orientation(npc_id, "neutral")` (`session.py:1037-1052`) | design/part-05-the-work.md §5.5,§5.7 |
| `costar.orientation.generous` | Costar orientation | Be generous — let them have the moment (`generosity()`) | `actor/positions.py` via `Session.choose_orientation(npc_id, "generous")` (`session.py:1037-1052`) | design/part-05-the-work.md §5.5,§5.7 |
| `costar.orientation.upstage` | Costar orientation | Take the moment — upstage them (`upstaging()`) | `actor/positions.py` via `Session.choose_orientation(npc_id, "upstage")` (`session.py:1037-1052`) | design/part-05-the-work.md §5.5,§5.7 |

## Prep

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `prep.table_work` | Prep choice (one per project) | Table work | `actor/prep.py` (`PREP_OPTIONS`) via `Session.choose_prep("table_work")` (`session.py:1056-1061`) | design/part-04-the-actor.md §4.6 |
| `prep.research` | Prep choice | Research | `actor/prep.py` via `Session.choose_prep("research")` (`session.py:1056-1061`) | design/part-04-the-actor.md §4.6 |
| `prep.dialect` | Prep choice | Dialect | `actor/prep.py` via `Session.choose_prep("dialect")` (`session.py:1056-1061`) | design/part-04-the-actor.md §4.6 |
| `prep.physical_transformation` | Prep choice | Physical transformation | `actor/prep.py` via `Session.choose_prep("physical_transformation")` (`session.py:1056-1061`) | design/part-04-the-actor.md §4.6 |
| `prep.live_it` | Prep choice | Live it | `actor/prep.py` via `Session.choose_prep("live_it")` (`session.py:1056-1061`) | design/part-04-the-actor.md §4.6 |

`wing_it` (`PREP_OPTIONS[5]`) exists in the engine but is deliberately excluded from `Session.prep_options()`'s player-facing menu (`session.py:1057-1058`) — not a reachable player decision, so not a row here.

## The shoot — scene positions

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `scene_position.with` | Per-dial scene position (4 dials × up to 3 scenes/episode) | With | `actor/positions.py` (`POSITIONS`) via `Session.play_scene({dial: "with", ...})` (`session.py:1074-1088`) | design/part-05-the-work.md §5.5,§5.7 |
| `scene_position.beneath` | Per-dial scene position | Beneath | `actor/positions.py` via `Session.play_scene({dial: "beneath", ...})` (`session.py:1074-1088`) | design/part-05-the-work.md §5.5,§5.7 |
| `scene_position.beyond` | Per-dial scene position | Beyond | `actor/positions.py` via `Session.play_scene({dial: "beyond", ...})` (`session.py:1074-1088`) | design/part-05-the-work.md §5.5,§5.7 |
| `scene_position.against` | Per-dial scene position | Against | `actor/positions.py` via `Session.play_scene({dial: "against", ...})` (`session.py:1074-1088`) | design/part-05-the-work.md §5.5,§5.7 |

## Release

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `release.actor.request.wide` | Release strategy request | Wide | `actor/release.py` (`RELEASE_STRATEGIES`) via `Session.choose_release("wide")` (`session.py:1092-1268`) | design/part-03-design-overview.md §3.4 |
| `release.actor.request.limited` | Release strategy request | Limited | `actor/release.py` via `Session.choose_release("limited")` (`session.py:1092-1268`) | design/part-03-design-overview.md §3.4 |
| `release.actor.request.festival` | Release strategy request | Festival | `actor/release.py` via `Session.choose_release("festival")` (`session.py:1092-1268`) | design/part-03-design-overview.md §3.4 |
| `release.actor.request.streaming` | Release strategy request | Streaming | `actor/release.py` via `Session.choose_release("streaming")` (`session.py:1092-1268`) | design/part-03-design-overview.md §3.4 |
| `release.actor.request.shelved` | Release strategy request | Shelved — no studio's `preferred_release` is ever `"shelved"` (`actor/studios.py`'s `STUDIOS` table), so this option is unreachable except by a deliberate player request that also wins the influence roll | `actor/release.py` via `Session.choose_release("shelved")` (`session.py:1092-1268`) | design/part-03-design-overview.md §3.4 |
| `release.actor.resolved.wide` | Resolved (actual) release outcome — informative secondary tally, not the coverage gate (see "How to read this catalog" above) | Wide, whether requested or arrived at via `studio_overruled` | `actor/studios.py` (`decide_release_strategy`) via `Session.choose_release()`'s return dict (`session.py:1184-1185,1237-1253`) | design/part-03-design-overview.md §3.4 |
| `release.actor.resolved.limited` | Resolved release outcome | Limited | `actor/studios.py` via `Session.choose_release()`'s return dict | design/part-03-design-overview.md §3.4 |
| `release.actor.resolved.festival` | Resolved release outcome | Festival | `actor/studios.py` via `Session.choose_release()`'s return dict | design/part-03-design-overview.md §3.4 |
| `release.actor.resolved.streaming` | Resolved release outcome | Streaming | `actor/studios.py` via `Session.choose_release()`'s return dict | design/part-03-design-overview.md §3.4 |
| `release.actor.resolved.shelved` | Resolved release outcome | Shelved | `actor/studios.py` via `Session.choose_release()`'s return dict | design/part-03-design-overview.md §3.4 |
| `release.actor.streaming_bid_selector` | Custom streaming-bid picker | Any `Callable[[list[StreamingBid]], StreamingBid]` — default auto-accepts best payout | `actor/studios.py` via `Session.choose_release(streaming_bid_selector=...)` (`session.py:1145-1219`) | design/part-08-the-studio.md §8.2 |
| `release.actor.festival_bid_selector` | Custom festival-bid picker | Any `Callable[[list[FestivalBid]], FestivalBid]` — default auto-accepts best payout | `actor/studios.py` via `Session.choose_release(festival_bid_selector=...)` (`session.py:1125-1219`) | design/part-08-the-studio.md §8.2 |

## Marketing push

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `marketing_push.actor` | Request a bigger marketing campaign | boolean call | `actor/studios.py` via `Session.request_marketing_push()` (`session.py:585-589`) | design/part-08-the-studio.md §8.2 |

## Multi-picture deals

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `multi_picture_deal.terms_preview` | Preview multi-picture deal terms | `multi_picture_deal_terms(film_count: int)` — preview, not a commitment | `leverage/multi_picture_deal.py` via `Session.multi_picture_deal_terms()` (`session.py:833-844`) | new mechanic — no design/ section (module's own docstring: "a direct mechanical extension of the same risk/reward shape" as the Indispensability holdout and Disappear, §6.4-6.6) |
| `multi_picture_deal.sign` | Sign a multi-picture deal | `sign_multi_picture_deal(film_count: int)`, 2-5 films (`MULTI_PICTURE_MIN_FILMS`/`MAX_FILMS`), gated on `MULTI_PICTURE_MIN_STANDING = 40.0` | `leverage/multi_picture_deal.py` via `Session.sign_multi_picture_deal()` (`session.py:826-859`) | new mechanic — no design/ section |
| `multi_picture_deal.break` | Break a signed multi-picture deal early | boolean call, real Notoriety cost | `leverage/multi_picture_deal.py` via `Session.break_multi_picture_deal()` (`session.py:871-880`) | new mechanic — no design/ section |

## Franchise holdout

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `franchise.holdout.request` | Request a holdout on a sequel (installment 2+, `FRANCHISE_INDISPENSABILITY_HOLDOUT_THRESHOLD = 30.0`) | boolean call — outcome: they pay a raise, recast you out, or call your bluff | `leverage/indispensability.py` (`resolve_holdout`) via `Session.request_holdout()` (`session.py:740-795`) | design/part-06-leverage.md §6.4-6.5 |

## Spin-offs — actor track

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `franchise.spinoff.actor_launch` | Launch a spin-off (franchise indispensability ≥ `SPINOFF_INDISPENSABILITY_THRESHOLD = 55.0`, and `you_are_current_lead`) | `launch_spinoff(franchise_id)` | `simulation/_franchises.py` (`create_spinoff_entry`) via `Session.launch_spinoff()` (`session.py:799-822`) | design/part-09-genres-franchises-and-tie-ins.md §9.5 |

## Awards

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `awards.actor.category.lead_drama` | Actor awards campaign category (only when `awards_campaign_available()`, `AWARDS_SPOTLIGHT_THRESHOLD = 68.0`) | Lead Drama | `awards/awards.py` (`eligible_performance_categories`) via `Session.run_awards_campaign(category="lead_drama")` (`session.py:1359-1447`) | design/part-04-the-actor.md §4.11 |
| `awards.actor.category.lead_comedy` | Actor awards campaign category | Lead Comedy/Musical | `awards/awards.py` via `Session.run_awards_campaign(category="lead_comedy")` (`session.py:1359-1447`) | design/part-04-the-actor.md §4.11 |
| `awards.actor.category.supporting` | Actor awards campaign category | Supporting | `awards/awards.py` via `Session.run_awards_campaign(category="supporting")` (`session.py:1359-1447`) | design/part-04-the-actor.md §4.11 |
| `awards.actor.category.ensemble` | Actor awards campaign category | Ensemble — always eligible, judges the film not the performance | `awards/awards.py` via `Session.run_awards_campaign(category="ensemble")` (`session.py:1359-1447`) | design/part-04-the-actor.md §4.11 |
| `awards.actor.category.breakthrough` | Actor awards campaign category | Breakthrough — early-career only (`credits <= BREAKTHROUGH_CREDITS_MAX`) | `awards/awards.py` via `Session.run_awards_campaign(category="breakthrough")` (`session.py:1359-1447`) | design/part-04-the-actor.md §4.11 |
| `awards.actor.category.voice_performance` | Actor awards campaign category | Voice Performance — animated lead/supporting only | `awards/awards.py` via `Session.run_awards_campaign(category="voice_performance")` (`session.py:1359-1447`) | design/part-04-the-actor.md §4.11 |
| `awards.actor.category.genre_excellence` | Actor awards campaign category | Genre Excellence — horror/scifi/fantasy/superhero/action lead/supporting only | `awards/awards.py` via `Session.run_awards_campaign(category="genre_excellence")` (`session.py:1359-1447`) | design/part-04-the-actor.md §4.11 |
| `awards.actor.category_fraud` | Category fraud attempt (§4.11's lead-in-supporting play) | `attempt_category_fraud: bool` — +18 advantage against a 35% chance of getting caught and paying a Notoriety cost | `awards/awards.py` (`category_fraud`) via `Session.run_awards_campaign(attempt_category_fraud=True)` (`session.py:1373,1401-1407`) | design/part-04-the-actor.md §4.11 |
| `awards.director.campaign` | Director awards campaign (DIRECTOR is the only category — reuses the actor track's BuzzScore formulas on director inputs) | boolean call, gated on `director_awards_campaign_available()` | `awards/awards.py` via `Session.run_director_awards_campaign()` (`session.py:1452-1489`) | design/part-04-the-actor.md §4.11 (reused for the director track, per `run_director_awards_campaign`'s own docstring) |

**Known pre-existing bug, not fixed by this phase:** `simulation/_quality_report.py:213` calls `session.run_awards_campaign(spend_millions=2.0)` without the required `category` argument — `Session.run_awards_campaign`'s signature (`session.py:1373`) has no default for `category`, so this call would raise `TypeError` the first time `awards_campaign_available()` returns `True` in a `_quality_report.py` run. This is a bug in a script this phase does not modify (`_quality_report.py` is a superseded, one-off report script per its own docstring). Every new archetype in this phase calls `run_awards_campaign` with an explicit `category` argument to avoid repeating it.

**Flagged balance finding — Approvals threshold, not fixed by this phase:** `APPROVAL_STANDING_THRESHOLD = 65.0` (`leverage/approvals.py:14`) gates script/costar approval negotiation on a weighted Standing score (`0.4·heat + 0.3·prestige + 0.3·affection`). A 59-seed × 60-year sweep of `prestige_chaser` — an archetype built specifically to chase Standing — never crossed a weighted score of ~18, roughly a quarter of the threshold (see `test_archetype_policies.py::TestPrestigeChaser::test_script_note_your_part_is_currently_unreachable_finding`, a passing test that documents the finding rather than force-passing it with a lucky-seed search). This is why the four actor-side script-note IDs are excluded from the catalog above rather than listed as required coverage. Phase 3's balance analysis should treat "elite Standing tiers are effectively unreachable through normal play" as a first-class candidate finding; Phase 4 decides whether `APPROVAL_STANDING_THRESHOLD`, or the Standing gain/decay curve feeding it (`actor/standing.py`), is the correct lever.

## Leverage — agent tier / scarcity

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `leverage.agent_tier.advance` | Advance agent tier | Automatic-if-eligible, `unrepresented → regional → boutique → major → powerhouse` | `leverage/catalogue.py` via `Session.try_advance_agent_tier()` (`session.py:1571-1582`) | design/part-06-leverage.md §6.6 |
| `leverage.disappear` | Disappear — bank Scarcity for a better return | boolean call, spends the rest of the year's actor quarters | `leverage/catalogue.py` via `Session.disappear()` (`session.py:1584-1594`) | design/part-06-leverage.md §6.6 |

## Rolodex pulls

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `rolodex.interact.check_in` | Interact with a tracked NPC | Check in | `rolodex/interactions.py` (`check_in`) via `Session.interact(npc_id, "check_in")` (`session.py:1503-1538`) | design/ux/04-pull-systems.md |
| `rolodex.interact.show_up` | Rolodex pull | Show up for them | `rolodex/interactions.py` (`show_up_for_them`) via `Session.interact(npc_id, "show_up")` (`session.py:1503-1538`) | design/ux/04-pull-systems.md |
| `rolodex.interact.read_agenda` | Rolodex pull | Read their agenda and act | `rolodex/interactions.py` (`read_agenda_and_act`) via `Session.interact(npc_id, "read_agenda")` (`session.py:1503-1538`) | design/ux/04-pull-systems.md |
| `rolodex.interact.vouch` | Rolodex pull | Vouch for them | `rolodex/interactions.py` (`vouch_for_them`) via `Session.interact(npc_id, "vouch")` (`session.py:1503-1538`) | design/ux/04-pull-systems.md |

## Life

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `life.lifestyle_floor.cut` | Cut lifestyle floor | `new_floor_millions: float` — real Affection cost | `life/money.py` (`cut_the_floor`) via `Session.cut_lifestyle_floor()` (`session.py:2109-2126`) | design/part-11-the-life.md §11.6 |

Health/addiction/family state (`life/health.py`, `life/addiction.py`, `life/family.py`) have no player-facing `Session` decision anywhere (confirmed by grepping `Session` for `def choose_/request_/try_` and finding zero references to health/addiction/family) — automatic background state, correctly out of this catalog's scope per the "only mechanical choices count" rule.

## Director mode — becoming a director, projects, franchise pitches

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.become_director` | Unlock directing | one-time unlock | `Session.become_director()` (`session.py:1611-1615`) | design/part-07-the-director.md §7.1 |
| `director.project.genre` | Start a directing project — genre | any of 10 `GENRES` | `director/development.py` (`start_development`) via `Session.start_directing_project(genre, ...)` (`session.py:1684-1730`) | design/part-07-the-director.md §7.4 |
| `director.project.budget_tier.micro` | Start a directing project — budget tier | Micro (~$4M) | `studio/slate.py` (`TIER_BUDGETS`) via `Session.start_directing_project(budget_tier="micro")` (`session.py:1684-1730`) | design/part-08-the-studio.md §8.2 |
| `director.project.budget_tier.low` | Budget tier | Low (~$12M) | `studio/slate.py` via `Session.start_directing_project(budget_tier="low")` (`session.py:1684-1730`) | design/part-08-the-studio.md §8.2 |
| `director.project.budget_tier.mid` | Budget tier | Mid (~$30M) | `studio/slate.py` via `Session.start_directing_project(budget_tier="mid")` (`session.py:1684-1730`) | design/part-08-the-studio.md §8.2 |
| `director.project.budget_tier.upper` | Budget tier | Upper (~$60M) | `studio/slate.py` via `Session.start_directing_project(budget_tier="upper")` (`session.py:1684-1730`) | design/part-08-the-studio.md §8.2 |
| `director.project.budget_tier.tentpole` | Budget tier | Tentpole (~$170M) | `studio/slate.py` via `Session.start_directing_project(budget_tier="tentpole")` (`session.py:1684-1730`) | design/part-08-the-studio.md §8.2 |
| `director.project.self_financed` | Self-finance a project | `self_financed: bool` — no studio ever attached, whole budget comes out of your own net worth | `director/development.py` via `Session.start_directing_project(self_financed=True)` (`session.py:1684-1730`) | design/part-07-the-director.md §7.4 |
| `director.project.franchise_sequel_pitch` | Pitch the next installment of an active franchise | `franchise_id` from `directing_franchise_options()` (`SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS = 4`) | `simulation/_franchises.py` via `Session.start_directing_project(franchise_id=...)` (`session.py:631-648,1684-1730`) | design/part-09-genres-franchises-and-tie-ins.md §9.5 |
| `director.project.new_franchise` | Register a brand-new property as a franchise on first resolve | `new_franchise: bool` | `director/development.py` via `Session.start_directing_project(new_franchise=True)` (`session.py:1684-1730`) | design/part-09-genres-franchises-and-tie-ins.md §9.5 |
| `director.project.cast_decision.recast` | Cast decision on a directed sequel | `"recast"` — same two real outcomes an actor holdout loss resolves through, director-initiated | `director/development.py` via `Session.start_directing_project(franchise_id=..., cast_decision="recast")` (`session.py:1684-1730`) | design/part-06-leverage.md §6.4-6.5 |
| `director.project.cast_decision.write_out` | Cast decision on a directed sequel | `"write_out"` | `director/development.py` via `Session.start_directing_project(franchise_id=..., cast_decision="write_out")` (`session.py:1684-1730`) | design/part-06-leverage.md §6.4-6.5 |
| `director.project.scrap` | Scrap a directing project | `scrap_directing_project(project_index)` — no cost, no roll | `director/development.py` (`scrap_project`) via `Session.scrap_directing_project()` (`session.py:1732-1734`) | design/part-07-the-director.md §7.4 |
| `director.franchise.reboot_pitch` | Pitch reviving a retired franchise (`REBOOT_MIN_DORMANT_YEARS = 5`) | `pitch_reboot(franchise_id)` from `directing_reboot_options()` | `simulation/_franchises.py` (also `Session.pitch_reboot()`, `session.py:653-693`) | design/part-09-genres-franchises-and-tie-ins.md §9.5 |
| `director.franchise.spinoff_pitch` | Pitch a director-side spin-off (`SPINOFF_INDISPENSABILITY_THRESHOLD = 55.0`, no `you_are_current_lead` gate) | `launch_directing_spinoff(franchise_id)` from `directing_spinoff_options()` | `simulation/_franchises.py` via `Session.launch_directing_spinoff()` (`session.py:698-720`) | design/part-09-genres-franchises-and-tie-ins.md §9.5 |

## Director mode — attaching a star

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.attach_star.target` | Attach-star target | Any tracked Rolodex NPC id, or `None` for a cold approach | `Session.attach_star_target_options()`/`choose_attach_star_target()` (`session.py:1738-1761`) | design/part-07-the-director.md §7.4 |
| `director.attach_star.type.bankable` | Attach-star type | Bankable — real fame, real PackageStrength, the fee to match | `director/development.py` (`ATTACHMENT_BANKABLE`) via `Session.choose_attach_star_target(..., "bankable")` (`session.py:1751-1761`) | design/part-07-the-director.md §7.4 |
| `director.attach_star.type.genre_fit` | Attach-star type | Good fit — not famous, but right for it | `director/development.py` (`ATTACHMENT_GENRE_FIT`) via `Session.choose_attach_star_target(..., "genre_fit")` (`session.py:1751-1761`) | design/part-07-the-director.md §7.4 |
| `director.attach_star.type.studio_favorite` | Attach-star type | A studio favourite — reliable, modest, not fame-scaled | `director/development.py` (`ATTACHMENT_STUDIO_FAVORITE`) via `Session.choose_attach_star_target(..., "studio_favorite")` (`session.py:1751-1761`) | design/part-07-the-director.md §7.4 |

## Director mode — adaptations

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.adaptation.source_type.public_domain` | Adaptation source type (feeds the `"option_adaptation"` dev action) | Public domain | `director/development.py` (`ADAPTATION_SOURCE_TYPES`) via `Session.choose_adaptation_source_type("public_domain")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.source_type.foreign_remake` | Adaptation source type | Foreign remake | `director/development.py` via `Session.choose_adaptation_source_type("foreign_remake")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.source_type.novel` | Adaptation source type | Novel (engine default) | `director/development.py` via `Session.choose_adaptation_source_type("novel")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.source_type.stage_play` | Adaptation source type | Stage play | `director/development.py` via `Session.choose_adaptation_source_type("stage_play")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.source_type.true_story` | Adaptation source type | True story | `director/development.py` via `Session.choose_adaptation_source_type("true_story")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.source_type.comic` | Adaptation source type | Comic / graphic novel | `director/development.py` via `Session.choose_adaptation_source_type("comic")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.source_type.video_game` | Adaptation source type | Video game | `director/development.py` via `Session.choose_adaptation_source_type("video_game")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.source_type.toy_line` | Adaptation source type | Toy line / brand | `director/development.py` via `Session.choose_adaptation_source_type("toy_line")` (`session.py:1763-1783`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |
| `director.adaptation.licensing_fraction` | Adaptation licensing fraction offered | `float 0.0-1.0` of the source's option-cost ceiling | `director/development.py` via `Session.choose_adaptation_licensing_fraction()` (`session.py:1785-1794`) | design/part-09-genres-franchises-and-tie-ins.md §9.4 |

## Director mode — casting

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.casting.bankable_wrong_fit` | Director casting choice | The bankable star, wrong for it | `director/casting.py` (`BANKABLE_WRONG_FIT`) via `Session.choose_director_casting_action()` (`session.py:1798-1810`) | design/part-07-the-director.md §7.1,§7.5 |
| `director.casting.right_actor_no_heat` | Director casting choice | The right actor, no heat | `director/casting.py` (`RIGHT_ACTOR_NO_HEAT`) via `Session.choose_director_casting_action()` (`session.py:1798-1810`) | design/part-07-the-director.md §7.1,§7.5 |
| `director.casting.discovery` | Director casting choice | The discovery — enormous variance | `director/casting.py` (`DISCOVERY`) via `Session.choose_director_casting_action()` (`session.py:1798-1810`) | design/part-07-the-director.md §7.1,§7.5 |
| `director.casting.your_roster` | Director casting choice | Your roster — reliable, Chemistry bonus, below quote | `director/casting.py` (`YOUR_ROSTER`) via `Session.choose_director_casting_action()` (`session.py:1798-1810`) | design/part-07-the-director.md §7.1,§7.5 |
| `director.casting.difficult_genius` | Director casting choice | The difficult genius — highest ceiling, real chaos risk | `director/casting.py` (`DIFFICULT_GENIUS`) via `Session.choose_director_casting_action()` (`session.py:1798-1810`) | design/part-07-the-director.md §7.1,§7.5 |

## Director mode — the director's own deal (backend push)

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.deal.backend_push` | Push the director's own deal for backend (trades fee down for a box-office bonus shot) | `push_director_deal_for_backend(project_index, bonus_type)` | `director/development.py` (`negotiate_director_backend_deal`) via `Session.push_director_deal_for_backend()` (`session.py:1818-1840`) | design/part-06-leverage.md §6.3/§6.5 (mirrored onto directing) |

## Director mode — shoot style

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.shoot_style.heavy_coverage` | Director shoot style | Heavy coverage — safer, fixable in the edit | `director/shoot_style.py` (`HEAVY_COVERAGE`) via `Session.choose_director_shoot_style_action()` (`session.py:1842-1854`) | design/part-07-the-director.md §7.6 |
| `director.shoot_style.long_takes` | Director shoot style | Long takes — higher ceiling, real risk | `director/shoot_style.py` (`LONG_TAKES`) via `Session.choose_director_shoot_style_action()` (`session.py:1842-1854`) | design/part-07-the-director.md §7.6 |
| `director.shoot_style.many_takes` | Director shoot style | Many takes — rewards real Craft | `director/shoot_style.py` (`MANY_TAKES`) via `Session.choose_director_shoot_style_action()` (`session.py:1842-1854`) | design/part-07-the-director.md §7.6 |
| `director.shoot_style.improvisation` | Director shoot style | Improvisation — rewards Instinct | `director/shoot_style.py` (`IMPROVISATION`) via `Session.choose_director_shoot_style_action()` (`session.py:1842-1854`) | design/part-07-the-director.md §7.6 |
| `director.shoot_style.lean_and_fast` | Director shoot style | Lean and fast — lower ceiling, real Efficiency reputation | `director/shoot_style.py` (`LEAN_AND_FAST`) via `Session.choose_director_shoot_style_action()` (`session.py:1842-1854`) | design/part-07-the-director.md §7.6 |

## Director mode — script note, release, marketing

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.script_note.clarity` | Director's own script note (the film's primary note, full strength) | Push for clarity | `core/script_notes.py` via `Session.choose_director_script_note_action(..., "clarity")` (`session.py:1865-1875`) | design/part-05-the-work.md §5.15 |
| `director.script_note.ambiguity` | Director's script note | Push for ambiguity | `core/script_notes.py` via `Session.choose_director_script_note_action(..., "ambiguity")` (`session.py:1865-1875`) | design/part-05-the-work.md §5.15 |
| `director.script_note.whole_film` | Director's script note | Push for the whole film — no angle, it just gets better | `core/script_notes.py` via `Session.choose_director_script_note_action(..., "whole_film")` (`session.py:1865-1875`) | design/part-05-the-work.md §5.15 |
| `director.release.request.wide` | Director release strategy request | Wide | `actor/release.py` (shared `RELEASE_STRATEGIES`) via `Session.request_director_release_strategy(..., "wide")` (`session.py:1877-1882`) | design/part-03-design-overview.md §3.4 |
| `director.release.request.limited` | Director release strategy request | Limited | `actor/release.py` via `Session.request_director_release_strategy(..., "limited")` (`session.py:1877-1882`) | design/part-03-design-overview.md §3.4 |
| `director.release.request.festival` | Director release strategy request | Festival | `actor/release.py` via `Session.request_director_release_strategy(..., "festival")` (`session.py:1877-1882`) | design/part-03-design-overview.md §3.4 |
| `director.release.request.streaming` | Director release strategy request | Streaming | `actor/release.py` via `Session.request_director_release_strategy(..., "streaming")` (`session.py:1877-1882`) | design/part-03-design-overview.md §3.4 |
| `director.release.request.shelved` | Director release strategy request | Shelved | `actor/release.py` via `Session.request_director_release_strategy(..., "shelved")` (`session.py:1877-1882`) | design/part-03-design-overview.md §3.4 |
| `director.marketing_push` | Director marketing push | boolean call | `actor/studios.py` (shared marketing curve) via `Session.request_director_marketing_push_action()` (`session.py:1884-1885`) | design/part-08-the-studio.md §8.2 |

## Director mode — development actions

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.dev_action.rewrite` | Director development action (one per quarter, per project) | Rewrite — improve the script | `director/development.py` (`DEV_ACTIONS`) via `Session.advance_directing(index, "rewrite")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.attach_star` | Dev action | Attach a star — real bankability, real momentum | `director/development.py` via `Session.advance_directing(index, "attach_star")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.cut_budget` | Dev action | Cut the budget — easier to greenlight, less to work with | `director/development.py` via `Session.advance_directing(index, "cut_budget")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.new_financier` | Dev action | Find a new financier | `director/development.py` via `Session.advance_directing(index, "new_financier")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.take_to_market` | Dev action | Take it to market | `director/development.py` via `Session.advance_directing(index, "take_to_market")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.self_finance` | Dev action | Self-finance — buy the project out from the studio and make it entirely your own | `director/development.py` via `Session.advance_directing(index, "self_finance")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.drawer` | Dev action | Put it in the drawer — walk away for now | `director/development.py` via `Session.advance_directing(index, "drawer")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.call_in_favour` | Dev action | Call in a favour — a Rolodex financier owes you one | `director/development.py` via `Session.advance_directing(index, "call_in_favour")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4 |
| `director.dev_action.option_adaptation` | Dev action | Option an adaptation — pivot onto existing IP | `director/development.py` via `Session.advance_directing(index, "option_adaptation")` (`session.py:1888-2007`) | design/part-07-the-director.md §7.4/§9.4 |

**Coverage note (Pitfall 2):** a cycle list *containing* an option string (e.g. `"self_finance"` appearing in a policy's own `dev_action_cycle` constant) is not proof the option ever actually fires — modulo-cycling against a shared `tick` that also advances on higher-priority actions can leave low-frequency entries permanently unreached. Coverage here is measured off the tally the archetype actually increments when `advance_directing(index, action)` is *called* with that action, not off whether the action string appears in source.

## Director mode — hire offers, platform expansion

| ID | Decision Point | Options | Source (module/function) | Design section |
|---|---|---|---|---|
| `director.hire_offer.accept` | Accept a director-for-hire offer | boolean | `Session.accept_hire_offer()` (`session.py:2168-2178`) | design/part-07-the-director.md §7.13 |
| `director.hire_offer.decline` | Decline a director-for-hire offer | boolean | `Session.decline_hire_offer()` (`session.py:2180-2181`) | design/part-07-the-director.md §7.13 |
| `director.platform_expansion.request` | Request platform expansion on a Limited/Festival hit | boolean, gated on `platform_expansion_available()` | `Session.request_platform_expansion()` (`session.py:2130-2147`) | design/part-07-the-director.md §7.12 |
