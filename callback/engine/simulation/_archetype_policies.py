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
from callback.engine.simulation._release_labels import RELEASE_LABELS
from callback.engine.simulation._sim_policy_shared import CONTRAST_SCENE_POSITIONS, SCENE_POSITIONS
from callback.engine.simulation.session import Session
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand


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
