"""Playtest policy archetypes exercising every decision point catalogued in
docs/design/decision-map.md (POLICY-01/POLICY-02) — extends `_full_data_report.py`'s
parametrized-tendency pattern into one function per archetype rather than one dispatcher, per this
phase's CONTEXT.md decision. Eight archetypes total across Plans 01-05: `prestige_chaser`,
`franchise_maximizer` (this file, Plan 01), `indie_purist`, `risk_averse`, `gambler`,
`director_track`, `family_first`, `burnout_avoider` (added by later plans).

Every function takes `seed: int`, constructs its own `Session(seed=seed)`, and accepts an optional
`visited: Counter | None = None` kwarg it increments at each decision call site against
decision-map.md's own ID vocabulary — coverage tracking lives entirely here in the caller, per
CLAUDE.md's "no new logging framework" rule and `simulation/_decision_coverage.py`'s own docstring.
Reads only `Session`'s public methods and their returned plain-data dicts — never `Role`,
`ActorState`, `ReceptionResult`, or `StandingModel` (the one legal engine seam, per this project's
CLAUDE.md and every existing `_*_report.py` script).
"""
from __future__ import annotations

from collections import Counter

from callback.engine.director import casting, development as director_development, shoot_style
from callback.engine.simulation._franchises import REBOOT_MIN_DORMANT_YEARS, SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS
from callback.engine.simulation._release_labels import RELEASE_LABELS
from callback.engine.simulation._sim_policy_shared import CONTRAST_SCENE_POSITIONS, SCENE_POSITIONS
from callback.engine.simulation.session import Session
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand

MOMENTUM_RANK = {"dead": 0, "fading": 1, "building": 2, "real heat": 3, "can't-miss": 4}


def _prefer_self_release(bids):
    """indie_purist's festival bid selector — creative control over the payout, matching a real
    "keep it and release it ourselves" indie strategy rather than chasing the biggest guarantee."""
    for b in bids:
        if getattr(b, "self_release", False):
            return b
    return max(bids, key=lambda b: b.payout_millions)


def _prefer_self_distribute(bids):
    """indie_purist's streaming bid selector — the analogous self-distribute choice."""
    for b in bids:
        if getattr(b, "self_distribute", False):
            return b
    return max(bids, key=lambda b: b.payout_millions)

BUZZ_RANK = {"nothing you've heard": 0, "quiet": 1, "some heat": 2, "real buzz": 3, "the talk of the town": 4}
GENRES = ["drama", "thriller", "horror", "comedy", "scifi", "action", "period", "romance", "musical", "family"]

# choose_release()'s return dict only reports the resolved release as its player-facing label
# (result["release_label"]), not the internal strategy key — this reverses _release_labels.py's
# own RELEASE_LABELS to recover the canonical key ("wide"/"limited"/...) for coverage tallying,
# so a resolved-outcome ID always matches one of decision-map.md's five concrete
# release.actor.resolved.* rows rather than a mangled copy of the display string.
_RELEASE_LABEL_TO_STRATEGY = {label: strategy for strategy, label in RELEASE_LABELS.items()}

# How many extra generate_more_listings() batches franchise_maximizer is willing to burn on a year
# with no continuing-franchise offer on the board, matching _full_data_report.py's "opportunist"
# tendency's OPPORTUNIST_SCAN_BATCHES precedent (Session.generate_more_listings() has no cap of its
# own — this is purely how hard this one policy is willing to look, not an engine limit).
FRANCHISE_SCAN_BATCHES = 10


def prestige_chaser(seed: int, years: int = 60, visited: Counter | None = None) -> dict:
    """Buzz-driven picks, both tracks (actor + director) — the "chase the acclaim" archetype.
    Follows `_full_data_report.py`'s `"prestige"` tendency call order almost exactly, but with two
    deliberate deviations that close real coverage gaps (RESEARCH.md Coverage Gap Inventory items
    2, 12, 13, 14): a `"your_part"` script note instead of `"whole_film"`, and a real
    awards-campaign loop (actor AND director side) that rotates through every eligible category
    and periodically attempts category fraud — both entirely unexercised by any existing report
    script."""
    if visited is None:
        visited = Counter()

    session = Session(seed=seed)
    session.start("conservatory", "work")
    visited["character_creation.background.conservatory"] += 1
    session.become_director()
    visited["director.become_director"] += 1

    award_campaign_count = 0
    films_acted = []
    films_directed = []
    genre_i = 0
    tick = 0

    for _year in range(years):
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        best = None
        if available:
            def score(o):
                buzz = BUZZ_RANK.get(o.get("buzz_band"), 0) * 30.0
                demand = world_genre_demand(session.state.genre_heat, o["genre"])
                billing_payoff = {"lead": 1.0, "supporting": 0.55, "bit": 0.2, "extra": 0.0}.get(o["billing"], 0.0)
                return (buzz + demand * 0.5) * billing_payoff
            candidate = max(available, key=score)
            if BUZZ_RANK.get(candidate.get("buzz_band"), 0) >= 2 and candidate["billing"] != "extra":
                best = candidate

        if best is not None:
            session.accept(best["index"])
            visited["offer_board.accept"] += 1
            bonus_type = "first_dollar_gross" if session.box_office_bonus_available("first_dollar_gross") else "net_points"
            visited[f"deal.box_office_bonus.{bonus_type}"] += 1
            want_merch = session.merchandising_available()
            if want_merch:
                visited["deal.merchandising"] += 1
            session.choose_deal(want_approvals=True, want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
            visited["deal.approvals"] += 1
            session.choose_prep("physical_transformation")
            visited["prep.physical_transformation"] += 1
            # Deviation 1 (Coverage Gap #2): push for your own part instead of the whole film —
            # closes the one script-note option no existing report script ever exercises.
            if session.script_notes_available():
                session.choose_script_note("your_part")
                visited["script_note.actor.your_part"] += 1
            for episode in session.episode_labels():
                for scene_choice in SCENE_POSITIONS:
                    session.play_scene(scene_choice)
                    for dial, position in scene_choice.items():
                        visited[f"scene_position.{position}"] += 1
            if session.rating_cut_available():
                session.choose_rating_stance("release_as_shot")
                visited["rating.actor.release_as_shot"] += 1
            session.request_marketing_push()
            visited["marketing_push.actor"] += 1
            # Pitfall 5 — a series project has no release-strategy/box-office-bonus branch at all
            # (_choose_release_series ignores `strategy` entirely); only tally the requested/
            # resolved release IDs for a real film-shaped project.
            is_series_year = session.is_series()
            strategy = "wide" if best["budget_millions"] >= 60.0 else "limited"
            result = session.choose_release(strategy)
            if not is_series_year:
                visited[f"release.actor.request.{strategy}"] += 1
                visited[f"release.actor.resolved.{_RELEASE_LABEL_TO_STRATEGY.get(result['release_label'], 'unknown')}"] += 1
            films_acted.append({
                "genre": best["genre"], "billing": best["billing"], "studio_tag": best["studio_name"],
                "is_animation": best.get("is_animation", False), **result,
            })
        else:
            session.decline_board()
            visited["offer_board.decline"] += 1

        # Deviation 2 (Coverage Gap #12/#13/#14): a real awards-campaign loop, both tracks. Every
        # existing script either never calls this at all or calls it with a missing `category`
        # argument (a documented pre-existing bug in _quality_report.py, see decision-map.md's
        # Awards callout) — always call with an explicit category here.
        if session.awards_campaign_available():
            categories = session.available_award_categories()
            if categories:
                category = categories[award_campaign_count % len(categories)]
                attempt_fraud = award_campaign_count % 3 == 0
                session.run_awards_campaign(category=category, spend_millions=2.0, attempt_category_fraud=attempt_fraud)
                visited[f"awards.actor.category.{category}"] += 1
                if attempt_fraud:
                    visited["awards.actor.category_fraud"] += 1
                award_campaign_count += 1
        if session.director_awards_campaign_available():
            session.run_director_awards_campaign(spend_millions=2.0)
            visited["awards.director.campaign"] += 1

        offer = session.check_for_hire_offer()
        if offer is not None:
            accept = session.director_status()["standing"] not in ("unknown",)
            if accept:
                session.accept_hire_offer()
                visited["director.hire_offer.accept"] += 1
            else:
                session.decline_hire_offer()
                visited["director.hire_offer.decline"] += 1

        while session.quarters_remaining_this_year() > 0:
            status = session.director_status()
            for s in status["projects"]:
                if s["momentum_band"] == "dead":
                    session.scrap_directing_project(s["index"])
                    visited["director.project.scrap"] += 1
                    status = session.director_status()
                    break
            if status["can_start_new_project"]:
                genre = GENRES[genre_i % len(GENRES)]
                genre_i += 1
                visited["director.project.genre"] += 1
                tier = "micro" if status["standing"] in ("unknown", "working") else "low"
                visited[f"director.project.budget_tier.{tier}"] += 1
                if session.start_directing_project(genre, tier):
                    new = session.director_status()["projects"][-1]
                    session.choose_director_casting_action(new["index"], casting.YOUR_ROSTER)
                    visited["director.casting.your_roster"] += 1
                    session.choose_director_shoot_style_action(new["index"], shoot_style.HEAVY_COVERAGE)
                    visited["director.shoot_style.heavy_coverage"] += 1
                    session.choose_director_script_note_action(new["index"], "whole_film")
                    visited["director.script_note.whole_film"] += 1
                    session.request_director_release_strategy(new["index"], "limited")
                    visited["director.release.request.limited"] += 1
                    session.request_director_marketing_push_action(new["index"])
                    visited["director.marketing_push"] += 1
                    status = session.director_status()
            if not status["projects"]:
                continue
            project_index = status["projects"][0]["index"]
            action = "rewrite" if tick % 3 != 0 else "attach_star"
            tick += 1
            if action == "attach_star":
                opts = session.attach_star_target_options()
                session.choose_attach_star_target(opts[tick % len(opts)]["id"], "bankable")
                visited["director.attach_star.target"] += 1
                visited["director.attach_star.type.bankable"] += 1
            session.advance_directing(project_index, action)
            visited[f"director.dev_action.{action}"] += 1
            if session.platform_expansion_available():
                session.request_platform_expansion()
                visited["director.platform_expansion.request"] += 1

        if session.state.life.money.net_worth < 0.0:
            session.cut_lifestyle_floor(session.state.life.money.lifestyle_floor * 0.5)
            visited["life.lifestyle_floor.cut"] += 1

        wrapped = session.end_year()
        for result in wrapped:
            films_directed.append({"genre": result["genre"], **result})
        if session.platform_expansion_available():
            session.request_platform_expansion()
            visited["director.platform_expansion.request"] += 1
        if session.is_over():
            break

    d = session.director_status()
    return {
        "seed": seed, "archetype": "prestige_chaser", "age": session.age(),
        "acting_credits": len(films_acted), "director_credits": d["credits"],
        "director_standing": d["standing"], "agent_tier": session.leverage_status()["agent_tier"],
        "net_worth": round(session.state.life.money.net_worth, 1),
        "actor_standing": {k: round(session.state.actor.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "films_acted": films_acted, "films_directed": films_directed,
        "franchise_status": session.franchise_status(),
    }


def franchise_maximizer(seed: int, years: int = 60, visited: Counter | None = None) -> dict:
    """Chases franchise continuity above all else — the one archetype whose offer-scoring is
    genuinely new logic (RESEARCH.md's Gated Decision Points section: no existing report script
    tracks `franchise_id`/`installment_number` continuity across years). Prefers re-accepting a
    franchise it already holds over any fresh, unrelated offer; once it builds real
    Indispensability in one, it signs a multi-picture deal, requests a holdout, launches a
    spin-off, and eventually breaks the deal — the entire multi-picture-deal/holdout/spin-off
    subsystem that RESEARCH.md documents as 0% covered by every existing script."""
    if visited is None:
        visited = Counter()

    session = Session(seed=seed)
    session.start("conservatory", "franchise")
    visited["character_creation.background.conservatory"] += 1

    held_franchise_ids: set[str] = set()
    signed_deal = False
    signed_year: int | None = None
    broke_deal = False
    films_acted = []

    for year in range(years):
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        continuing = next((o for o in available if o.get("franchise_id") in held_franchise_ids), None)
        if continuing is None:
            # No offer on the board continues a franchise already held — scan deeper (like
            # _full_data_report.py's "opportunist" tendency) rather than settle for the first
            # handful, both to find a real shot at continuity and, failing that, the best-buzz
            # lead/supporting role available: real Standing growth is what eventually unlocks
            # multi_picture_deal_available()'s MULTI_PICTURE_MIN_STANDING gate.
            for _ in range(FRANCHISE_SCAN_BATCHES):
                board = board + session.generate_more_listings()
                visited["offer_board.generate_more_listings"] += 1
                available = [o for o in board if o["available"]]
                continuing = next((o for o in available if o.get("franchise_id") in held_franchise_ids), None)
                if continuing is not None:
                    break
        best = None
        if available:
            if continuing is not None:
                best = continuing
            else:
                def fallback_score(o):
                    has_franchise = 1.0 if o.get("franchise_id") is not None else 0.0
                    buzz = BUZZ_RANK.get(o.get("buzz_band"), 0)
                    demand = world_genre_demand(session.state.genre_heat, o["genre"])
                    billing_payoff = {"lead": 1.0, "supporting": 0.6, "bit": 0.2, "extra": 0.0}.get(o["billing"], 0.0)
                    return has_franchise * 1000.0 + (buzz * 30.0 + demand * 0.5) * billing_payoff
                best = max(available, key=fallback_score)

        if best is not None:
            session.accept(best["index"])
            visited["offer_board.accept"] += 1
            newly_franchised = best.get("franchise_id") is not None
            if newly_franchised:
                held_franchise_ids.add(best["franchise_id"])

            if newly_franchised and not signed_deal and session.multi_picture_deal_available():
                session.multi_picture_deal_terms(3)
                visited["multi_picture_deal.terms_preview"] += 1
                session.sign_multi_picture_deal(3)
                visited["multi_picture_deal.sign"] += 1
                signed_deal = True
                signed_year = year

            if signed_deal and not broke_deal and signed_year is not None and (year - signed_year) >= 3:
                session.break_multi_picture_deal()
                visited["multi_picture_deal.break"] += 1
                broke_deal = True

            # A lost holdout (recast/write-out) sets Session._role to None — "no project this
            # year," the same real outcome a declined offer produces. Everything from choose_deal
            # onward assumes a live role, so a failed holdout must skip straight to end_year() the
            # same way the "no offer accepted" branch below does.
            proceeded = True
            if session.holdout_available():
                holdout_result = session.request_holdout()
                visited["franchise.holdout.request"] += 1
                proceeded = holdout_result["proceeds"]

            if proceeded:
                for f in session.spinoff_options():
                    session.launch_spinoff(f["franchise_id"])
                    visited["franchise.spinoff.actor_launch"] += 1
                    break

                bonus_type = "first_dollar_gross" if session.box_office_bonus_available("first_dollar_gross") else "net_points"
                visited[f"deal.box_office_bonus.{bonus_type}"] += 1
                want_merch = session.merchandising_available()
                if want_merch:
                    visited["deal.merchandising"] += 1
                session.choose_deal(want_approvals=True, want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
                visited["deal.approvals"] += 1
                # Coverage Gap Inventory item 5's "dialect" half — "research" is indie_purist's job
                # in a later plan; not duplicated here.
                session.choose_prep("dialect")
                visited["prep.dialect"] += 1
                for episode in session.episode_labels():
                    for scene_choice in SCENE_POSITIONS:
                        session.play_scene(scene_choice)
                        for dial, position in scene_choice.items():
                            visited[f"scene_position.{position}"] += 1
                if session.rating_cut_available():
                    session.choose_rating_stance("release_as_shot")
                    visited["rating.actor.release_as_shot"] += 1
                session.request_marketing_push()
                visited["marketing_push.actor"] += 1
                # Pitfall 5 — see prestige_chaser's identical guard above.
                is_series_year = session.is_series()
                strategy = "wide" if best["budget_millions"] >= 50.0 else "limited"
                result = session.choose_release(strategy)
                if not is_series_year:
                    visited[f"release.actor.request.{strategy}"] += 1
                    visited[f"release.actor.resolved.{_RELEASE_LABEL_TO_STRATEGY.get(result['release_label'], 'unknown')}"] += 1
                films_acted.append({
                    "genre": best["genre"], "billing": best["billing"], "studio_tag": best["studio_name"],
                    "franchise_id": best.get("franchise_id"), **result,
                })
        else:
            session.decline_board()
            visited["offer_board.decline"] += 1

        session.end_year()
        if session.state.life.money.net_worth < 0.0:
            session.cut_lifestyle_floor(session.state.life.money.lifestyle_floor * 0.5)
            visited["life.lifestyle_floor.cut"] += 1
        if session.is_over():
            break

    return {
        "seed": seed, "archetype": "franchise_maximizer", "age": session.age(),
        "acting_credits": len(films_acted),
        "agent_tier": session.leverage_status()["agent_tier"],
        "net_worth": round(session.state.life.money.net_worth, 1),
        "actor_standing": {k: round(session.state.actor.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "films_acted": films_acted,
        "franchise_status": session.franchise_status(),
        "held_franchise_ids": sorted(held_franchise_ids),
        "multi_picture_deal_signed": signed_deal,
    }


def indie_purist(seed: int, years: int = 60, visited: Counter | None = None) -> dict:
    """Craft-over-money, acting-only — chases buzz/genre-fit without a billing floor (indie roles
    are frequently supporting/bit), stays deliberately craft-safe on scene positions (the shared
    SCENE_POSITIONS default IS the differentiator, not indifference — see comment below), and
    exercises self-release/self-distribute control over festival/streaming money (Coverage Gap
    Inventory items 5's `research` half, 7's festival/streaming requests, 8's custom bid
    selectors)."""
    if visited is None:
        visited = Counter()

    session = Session(seed=seed)
    session.start("conservatory", "work")
    visited["character_creation.background.conservatory"] += 1

    films_acted = []
    prep_tick = 0

    for _year in range(years):
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        best = None
        if available:
            def score(o):
                buzz = BUZZ_RANK.get(o.get("buzz_band"), 0) * 20.0
                demand = world_genre_demand(session.state.genre_heat, o["genre"])
                return buzz + demand
            best = max(available, key=score)

        if best is not None:
            session.accept(best["index"])
            visited["offer_board.accept"] += 1
            session.choose_deal(want_approvals=False)
            visited["deal.approvals"] += 1
            # Alternates research/dialect — Coverage Gap Inventory item 5's `research` half.
            prep_choice = "research" if prep_tick % 2 == 0 else "dialect"
            prep_tick += 1
            session.choose_prep(prep_choice)
            visited[f"prep.{prep_choice}"] += 1
            if session.script_notes_available():
                session.choose_script_note("ambiguity")
                visited["script_note.actor.ambiguity"] += 1
            for episode in session.episode_labels():
                # Deliberate: reuse the shared craft-safe default rather than inventing a new
                # "sameness" tuple. indie_purist's differentiator IS staying craft-safe — a future
                # reader should not "fix" this into something else.
                for scene_choice in SCENE_POSITIONS:
                    session.play_scene(scene_choice)
                    for dial, position in scene_choice.items():
                        visited[f"scene_position.{position}"] += 1
            is_series_year = session.is_series()
            if not is_series_year:
                if best["budget_millions"] < 30.0:
                    strategy = "festival"
                    result = session.choose_release(strategy, festival_bid_selector=_prefer_self_release)
                    visited["release.actor.festival_bid_selector"] += 1
                else:
                    strategy = "streaming"
                    result = session.choose_release(strategy, streaming_bid_selector=_prefer_self_distribute)
                    visited["release.actor.streaming_bid_selector"] += 1
                visited[f"release.actor.request.{strategy}"] += 1
                visited[f"release.actor.resolved.{_RELEASE_LABEL_TO_STRATEGY.get(result['release_label'], 'unknown')}"] += 1
            else:
                result = session.choose_release("festival")
            films_acted.append({
                "genre": best["genre"], "billing": best["billing"], "studio_tag": best["studio_name"],
                **result,
            })
        else:
            session.decline_board()
            visited["offer_board.decline"] += 1

        session.end_year()
        if session.state.life.money.net_worth < 0.0:
            session.cut_lifestyle_floor(session.state.life.money.lifestyle_floor * 0.5)
            visited["life.lifestyle_floor.cut"] += 1
        if session.is_over():
            break

    return {
        "seed": seed, "archetype": "indie_purist", "age": session.age(),
        "acting_credits": len(films_acted),
        "agent_tier": session.leverage_status()["agent_tier"],
        "net_worth": round(session.state.life.money.net_worth, 1),
        "actor_standing": {k: round(session.state.actor.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "films_acted": films_acted,
    }


def risk_averse(seed: int, years: int = 60, visited: Counter | None = None) -> dict:
    """Safe, steady, in-demand moderate-budget roles — no approval fights, a net_points bonus
    (the less volatile of the two bonus types) when available, always the lower-variance `limited`
    release. Signature move: requests the rating cut whenever `rating_cut_available()` fires
    (Coverage Gap Inventory item 3 — the one deliberate-player-choice rating cut no existing
    report script ever exercises)."""
    if visited is None:
        visited = Counter()

    session = Session(seed=seed)
    session.start("conservatory", "work")
    visited["character_creation.background.conservatory"] += 1

    films_acted = []

    for _year in range(years):
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        best = None
        if available:
            def score(o):
                demand = world_genre_demand(session.state.genre_heat, o["genre"])
                billing_payoff = {"lead": 0.6, "supporting": 1.0, "bit": 0.4, "extra": 0.0}.get(o["billing"], 0.0)
                budget_fit = 1.0 - abs(o["budget_millions"] - 40.0) / 100.0
                return demand * billing_payoff + budget_fit
            candidate = max(available, key=score)
            if candidate["billing"] != "extra":
                best = candidate

        if best is not None:
            session.accept(best["index"])
            visited["offer_board.accept"] += 1
            bonus_type = "net_points"
            want_box_office = session.box_office_bonus_available(bonus_type)
            if want_box_office:
                visited[f"deal.box_office_bonus.{bonus_type}"] += 1
            session.choose_deal(want_approvals=False, want_box_office_bonus=want_box_office, bonus_type=bonus_type)
            visited["deal.approvals"] += 1
            session.choose_prep("table_work")
            visited["prep.table_work"] += 1
            # A risk-averse actor doesn't fight for approvals, so this rarely fires — but when it
            # does (e.g. a franchise/guaranteed-listing path), push for clarity, not ambiguity.
            if session.script_notes_available():
                session.choose_script_note("clarity")
                visited["script_note.actor.clarity"] += 1
            for episode in session.episode_labels():
                for scene_choice in SCENE_POSITIONS:
                    session.play_scene(scene_choice)
                    for dial, position in scene_choice.items():
                        visited[f"scene_position.{position}"] += 1
            if session.rating_cut_available():
                session.choose_rating_stance("cut")
                visited["rating.actor.cut"] += 1
            is_series_year = session.is_series()
            result = session.choose_release("limited")
            if not is_series_year:
                visited["release.actor.request.limited"] += 1
                visited[f"release.actor.resolved.{_RELEASE_LABEL_TO_STRATEGY.get(result['release_label'], 'unknown')}"] += 1
            films_acted.append({
                "genre": best["genre"], "billing": best["billing"], "studio_tag": best["studio_name"],
                **result,
            })
        else:
            session.decline_board()
            visited["offer_board.decline"] += 1

        session.end_year()
        if session.state.life.money.net_worth < 0.0:
            session.cut_lifestyle_floor(session.state.life.money.lifestyle_floor * 0.5)
            visited["life.lifestyle_floor.cut"] += 1
        if session.is_over():
            break

    return {
        "seed": seed, "archetype": "risk_averse", "age": session.age(),
        "acting_credits": len(films_acted),
        "agent_tier": session.leverage_status()["agent_tier"],
        "net_worth": round(session.state.life.money.net_worth, 1),
        "actor_standing": {k: round(session.state.actor.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "films_acted": films_acted,
    }


def gambler(seed: int, years: int = 60, visited: Counter | None = None) -> dict:
    """Extreme-swing scene positions (CONTRAST_SCENE_POSITIONS), the `discovered` background
    (Coverage Gap Inventory item 1), upstaging the costar (item 4), biggest-budget picks regardless
    of buzz (mirrors `_full_data_report.py`'s own gambler tendency), and one in four accepted
    projects requests `shelved` as a deliberate long-shot (item 7 — the request is what closes the
    coverage gate per decision-map.md's own requested-vs-resolved rule; no studio's
    preferred_release is ever `shelved`, so this rarely if ever actually resolves that way, which
    is the point)."""
    if visited is None:
        visited = Counter()

    session = Session(seed=seed)
    session.start("discovered", "run")
    visited["character_creation.background.discovered"] += 1

    films_acted = []
    tick = 0

    for _year in range(years):
        board = session.offer_board()
        available = [o for o in board if o["available"] and o["billing"] != "extra"]
        best = max(available, key=lambda o: o["budget_millions"]) if available else None

        if best is not None:
            session.accept(best["index"])
            visited["offer_board.accept"] += 1
            session.choose_deal(want_approvals=False)
            visited["deal.approvals"] += 1
            session.choose_prep("physical_transformation")
            visited["prep.physical_transformation"] += 1
            costars = session.costar_options()
            if costars:
                session.choose_orientation(costars[0]["id"], "upstage")
            else:
                session.choose_orientation(None, "upstage")
            visited["costar.orientation.upstage"] += 1
            for episode in session.episode_labels():
                for scene_choice in CONTRAST_SCENE_POSITIONS:
                    session.play_scene(scene_choice)
                    for dial, position in scene_choice.items():
                        visited[f"scene_position.{position}"] += 1
            is_series_year = session.is_series()
            tick += 1
            strategy = "shelved" if tick % 4 == 0 else "wide"
            result = session.choose_release(strategy)
            if not is_series_year:
                visited[f"release.actor.request.{strategy}"] += 1
                visited[f"release.actor.resolved.{_RELEASE_LABEL_TO_STRATEGY.get(result['release_label'], 'unknown')}"] += 1
            films_acted.append({
                "genre": best["genre"], "billing": best["billing"], "studio_tag": best["studio_name"],
                **result,
            })
        else:
            session.decline_board()
            visited["offer_board.decline"] += 1

        session.end_year()
        if session.state.life.money.net_worth < 0.0:
            session.cut_lifestyle_floor(session.state.life.money.lifestyle_floor * 0.5)
            visited["life.lifestyle_floor.cut"] += 1
        if session.is_over():
            break

    return {
        "seed": seed, "archetype": "gambler", "age": session.age(),
        "background": "discovered",
        "acting_credits": len(films_acted),
        "agent_tier": session.leverage_status()["agent_tier"],
        "net_worth": round(session.state.life.money.net_worth, 1),
        "actor_standing": {k: round(session.state.actor.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "films_acted": films_acted,
    }


_BUDGET_TIER_CYCLE = ("micro", "low", "mid", "upper", "tentpole")
_ADAPTATION_SOURCE_CYCLE = (
    "public_domain", "foreign_remake", "stage_play", "true_story", "comic", "video_game", "toy_line",
)


def director_track(seed: int, years: int = 60, visited: Counter | None = None) -> dict:
    """Director-only archetype (no acting-side calls at all) closing every remaining
    director-mode coverage gap: all 5 budget tiers, self-financed projects, franchise
    sequel/reboot/spinoff pitching, all 7 non-default adaptation source types, licensing
    fraction, backend deal pushes, director script notes, director release variety, and the
    two dev actions (self_finance, drawer) no existing report script ever exercises — closed
    with explicit condition-based firing per project rather than a diluted modulo cycle
    (Pitfall 2), matching CONTEXT.md's coverage rule."""
    if visited is None:
        visited = Counter()

    session = Session(seed=seed)
    session.start("conservatory", "work")
    visited["character_creation.background.conservatory"] += 1
    session.become_director()
    visited["director.become_director"] += 1

    genres = GENRES
    genre_i = 0
    project_count = 0
    tick = 0

    own_franchise_id: str | None = None
    own_franchise_index: int | None = None
    own_franchise_sequel_pitches = 0
    own_franchise_last_pitch_year: int | None = None
    reboot_pitched = False
    spinoff_pitched = False
    recast_done = False
    write_out_done = False

    self_finance_done = False
    drawer_done = False
    backend_push_done = False
    script_note_clarity_done = False
    script_note_ambiguity_done = False
    adaptation_licensing_done = False
    release_done = {"festival": False, "streaming": False, "shelved": False}

    casting_cycle = list(casting.CASTING_CHOICES)
    style_cycle = list(shoot_style.SHOOT_STYLES)

    def _set_casting_and_style():
        # Real quality signals (critic score -> director prestige) come from casting/shoot-style,
        # not just picking a genre and walking away — mirrors _director_report.py's own pitch().
        # Also cycles every casting/shoot_style option (Coverage Gap Inventory closure beyond
        # items 17-25's explicit list, since these rows are still uncovered after Plans 01-02).
        idx = session.director_status()["projects"][-1]["index"]
        cast_choice = casting_cycle[project_count % len(casting_cycle)]
        style_choice = style_cycle[project_count % len(style_cycle)]
        session.choose_director_casting_action(idx, cast_choice)
        visited[f"director.casting.{cast_choice}"] += 1
        session.choose_director_shoot_style_action(idx, style_choice)
        visited[f"director.shoot_style.{style_choice}"] += 1

    def pitch(status, year):
        nonlocal genre_i, project_count, own_franchise_id, own_franchise_index, own_franchise_last_pitch_year
        nonlocal own_franchise_sequel_pitches, recast_done, write_out_done, adaptation_licensing_done
        tier = _BUDGET_TIER_CYCLE[project_count % len(_BUDGET_TIER_CYCLE)]
        self_financed = project_count % 5 == 0 and project_count > 0

        # Own-franchise strategy: start it once, pitch a handful of sequels, then deliberately
        # stop and let it go dormant so decay_dormant_franchises can retire it into
        # retired_franchises — only then does pitch_reboot become reachable at all.
        if own_franchise_id is None and own_franchise_index is None:
            genre = genres[genre_i % len(genres)]
            genre_i += 1
            if session.start_directing_project(genre, tier, self_financed=self_financed, new_franchise=True):
                own_franchise_index = len(status["projects"])  # about-to-be-appended slot
                project_count += 1
                visited[f"director.budget_tier.{tier}"] += 1
                if self_financed:
                    visited["director.project.self_financed"] += 1
                visited["director.project.new_franchise"] += 1
                _set_casting_and_style()
            return

        if own_franchise_id is not None and own_franchise_sequel_pitches < SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS:
            options = session.directing_franchise_options()
            mine = next((o for o in options if o["id"] == own_franchise_id), None)
            if mine is not None:
                cast_decision = None
                if not recast_done:
                    cast_decision = "recast"
                elif not write_out_done:
                    cast_decision = "write_out"
                if session.start_directing_project(mine["genre"], tier, franchise_id=own_franchise_id, cast_decision=cast_decision):
                    project_count += 1
                    own_franchise_sequel_pitches += 1
                    own_franchise_last_pitch_year = year
                    visited[f"director.budget_tier.{tier}"] += 1
                    visited["director.project.franchise_sequel_pitch"] += 1
                    if cast_decision == "recast":
                        recast_done = True
                        visited["director.project.cast_decision.recast"] += 1
                    elif cast_decision == "write_out":
                        write_out_done = True
                        visited["director.project.cast_decision.write_out"] += 1
                    _set_casting_and_style()
                return

        # Original/adaptation project — cycle non-default adaptation source types and licensing
        # fraction on alternating projects (Coverage Gap Inventory items 20-21).
        genre = genres[genre_i % len(genres)]
        genre_i += 1
        if project_count % 2 == 1:
            source = _ADAPTATION_SOURCE_CYCLE[project_count % len(_ADAPTATION_SOURCE_CYCLE)]
            session.choose_adaptation_source_type(source)
            visited[f"director.adaptation.source_type.{source}"] += 1
            if not adaptation_licensing_done:
                session.choose_adaptation_licensing_fraction(0.8)
                visited["director.adaptation.licensing_fraction"] += 1
                adaptation_licensing_done = True
        if session.start_directing_project(genre, tier, self_financed=self_financed):
            project_count += 1
            visited[f"director.budget_tier.{tier}"] += 1
            if self_financed:
                visited["director.project.self_financed"] += 1
            _set_casting_and_style()

    for year in range(years):
        offer = session.check_for_hire_offer()
        if offer is not None:
            accept = session.director_status()["standing"] not in ("unknown",)
            if accept:
                session.accept_hire_offer()
                visited["director.hire_offer.accept"] += 1
            else:
                session.decline_hire_offer()
                visited["director.hire_offer.decline"] += 1

        # Own-franchise dormancy watch: once far enough past the last sequel pitch, keep checking
        # for the reboot opportunity every year until it lands or the run ends.
        if (
            own_franchise_id is not None and not reboot_pitched
            and own_franchise_last_pitch_year is not None
            and year - own_franchise_last_pitch_year >= REBOOT_MIN_DORMANT_YEARS
        ):
            reboot_options = session.directing_reboot_options()
            if any(o["franchise_id"] == own_franchise_id for o in reboot_options):
                if session.pitch_reboot(own_franchise_id):
                    reboot_pitched = True
                visited["director.franchise.reboot_pitch"] += 1

        if not spinoff_pitched:
            spinoff_options = session.directing_spinoff_options()
            if spinoff_options:
                target = spinoff_options[0]
                new_id = session.launch_directing_spinoff(target["franchise_id"])
                if new_id is not None:
                    spinoff_pitched = True
                    visited["director.franchise.spinoff_pitch"] += 1

        while session.quarters_remaining_this_year() > 0:
            status = session.director_status()

            # Fire "drawer" once on a genuinely dead project instead of scrapping it outright —
            # closes Coverage Gap Inventory item 25's other never-used dev action.
            dead_projects = [s for s in status["projects"] if s["momentum_band"] == "dead"]
            if dead_projects and not drawer_done:
                idx = dead_projects[0]["index"]
                session.advance_directing(idx, "drawer")
                visited["director.dev_action.drawer"] += 1
                drawer_done = True
                status = session.director_status()
            else:
                for s in status["projects"]:
                    if s["momentum_band"] == "dead":
                        session.scrap_directing_project(s["index"])
                        status = session.director_status()
                        break

            if status["can_start_new_project"]:
                pitch(status, year)
                status = session.director_status()

            if own_franchise_id is None and own_franchise_index is not None:
                # The franchise only registers in the shared pool once its first installment
                # resolves — re-check every quarter until it appears.
                for s in status["projects"]:
                    if s["franchise_id"] is not None:
                        own_franchise_id = s["franchise_id"]
                        break

            if not status["projects"]:
                break

            best = max(status["projects"], key=lambda s: MOMENTUM_RANK.get(s["momentum_band"], 0))
            project_index = best["index"]

            # Explicit, condition-based firing (not a diluted cycle) for the two dev actions no
            # existing script ever exercises (Coverage Gap Inventory item 25).
            action = None
            if not backend_push_done and session.director_deal_available(project_index):
                # Per decision-map.md's requested-vs-resolved rule: the ASK is what coverage
                # counts, not whether Standing clears BOX_OFFICE_BONUS_STANDING_THRESHOLD — a
                # real no-op (granted: False) is still a legitimate, tallied request, the same
                # semantics deal.approvals/release-strategy rows already use.
                session.push_director_deal_for_backend(project_index, "net_points")
                visited["director.deal.backend_push"] += 1
                backend_push_done = True
                action = "rewrite"
            elif not self_finance_done and best["momentum_band"] in ("fading", "dead") and not best["self_financed"]:
                action = "self_finance"
            elif not script_note_clarity_done:
                session.choose_director_script_note_action(project_index, "clarity")
                visited["director.script_note.clarity"] += 1
                script_note_clarity_done = True
                action = "rewrite"
            elif not script_note_ambiguity_done:
                session.choose_director_script_note_action(project_index, "ambiguity")
                visited["director.script_note.ambiguity"] += 1
                script_note_ambiguity_done = True
                action = "rewrite"
            else:
                cycle = ["rewrite", "cut_budget", "call_in_favour", "option_adaptation", "new_financier", "take_to_market"]
                action = cycle[tick % len(cycle)]
            tick += 1

            if action == "self_finance":
                visited["director.dev_action.self_finance"] += 1
                self_finance_done = True
            else:
                visited[f"director.dev_action.{action}"] += 1

            result = session.advance_directing(project_index, action)

            if result.get("greenlit"):
                remaining = [s for s in ("festival", "streaming", "shelved") if not release_done[s]]
                strategy = remaining[0] if remaining else "wide"
                session.request_director_release_strategy(project_index, strategy)
                visited[f"director.release.request.{strategy}"] += 1
                if strategy in release_done:
                    release_done[strategy] = True
                session.request_director_marketing_push_action(project_index)
                visited["director.marketing_push"] += 1

        if session.director_awards_campaign_available():
            session.run_director_awards_campaign(spend_millions=2.0)
            visited["awards.director.campaign"] += 1

        session.end_year()
        if session.is_over():
            break

    d = session.director_status()
    return {
        "seed": seed, "archetype": "director_track", "age": session.age(),
        "director_credits": d["credits"],
        "director_standing": {k: round(session.state.director.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "net_worth": round(session.state.life.money.net_worth, 1),
        "own_franchise_id": own_franchise_id,
        "reboot_pitched": reboot_pitched,
    }
