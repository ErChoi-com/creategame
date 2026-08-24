"""One-off reporting script: runs a director/actor career under a named policy "tendency" and
dumps every field available on each film's result — including the obscure ones (legs, opening,
weekly gross curve, box office bonus, rating stance/forced cut, streaming buyer, marketing push
honored, requested-vs-actual release, franchise installment) — to a JSON file for full-detail
inspection. Four tendencies: "gambler" (big swings — high budget, bankable attachments,
self-finance, wide releases, momentum over quality), "prestige" (buzz-driven picks, rewrite-heavy
directing, limited/festival releases — the policy already built in _quality_report.py, reused
here), and "workhorse" (neither — takes whatever reasonably fits rather than chasing buzz or
budget, never passes on the whole board the way prestige's own buzz threshold can, table-work
prep, lean-and-fast directing, a steady mid-budget tier every time rather than swinging between
tiers — the "just keeps working" career, the real median outcome for most people in the industry
this design models), and "opportunist" (no fixed lane at all — exhaustively scans the whole board
every year via generate_more_listings(), as many times as it takes, rather than settling for the
first handful like every other tendency, then picks whichever real listing actually scores best
this year on a blended demand/billing/buzz/fee read; deal/prep/release choices adapt per-listing
too, rather than following one fixed style year to year).
"""
from __future__ import annotations

import json
from dataclasses import replace as dc_replace

from callback.engine.actor.attributes import Attributes
from callback.engine.director import casting, shoot_style
from callback.engine.director.attributes import DirectorAttributes
from callback.engine.simulation.session import Session
from callback.engine.simulation._sim_policy_shared import SCENE_POSITIONS
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand

MOMENTUM_RANK = {"dead": 0, "fading": 1, "building": 2, "real heat": 3, "can't-miss": 4}
BILLING_RANK = {"lead": 3, "supporting": 2, "bit": 1, "extra": 0}
BUZZ_RANK = {"nothing you've heard": 0, "quiet": 1, "some heat": 2, "real buzz": 3, "the talk of the town": 4}
GENRES = ["drama", "thriller", "horror", "comedy", "scifi", "action", "period", "romance", "musical", "family"]

# "as many as he needs" — Session.generate_more_listings() has no real cap of its own (see its own
# docstring: "the offer board isn't capped"); this is just how many extra batches this one policy
# is willing to burn on the same year's board before picking, not an engine limit.
OPPORTUNIST_SCAN_BATCHES = 25


def run(seed: int, tendency: str, years: int = 60, max_stats: bool = False) -> dict:
    session = Session(seed=seed)
    session.start("conservatory", "work")
    session.become_director()
    if max_stats:
        # Every real power stat maxed on both tracks — Attributes (craft/instinct/presence/voice/
        # physicality/look/resilience) and DirectorAttributes (vision/command/craft/taste/
        # efficiency). Nothing about the policy itself changes — same scene-position logic, same
        # offer/dev-action choices — only the character's own ceiling moves.
        session.state = dc_replace(session.state, actor=dc_replace(session.state.actor, attrs=Attributes(
            craft=100.0, instinct=100.0, presence=100.0, voice=100.0, physicality=100.0, look=100.0, resilience=100.0,
        )))
        session.state = dc_replace(session.state, director=dc_replace(session.state.director, attrs=DirectorAttributes(
            vision=100.0, command=100.0, craft=100.0, taste=100.0, efficiency=100.0,
        )))

    films_acted = []
    films_directed = []
    genre_i = 0
    tick = 0
    casting_cycle = [casting.YOUR_ROSTER, casting.DIFFICULT_GENIUS, casting.DISCOVERY, casting.BANKABLE_WRONG_FIT, casting.RIGHT_ACTOR_NO_HEAT]
    style_cycle = [shoot_style.LONG_TAKES, shoot_style.LEAN_AND_FAST, shoot_style.MANY_TAKES, shoot_style.IMPROVISATION, shoot_style.HEAVY_COVERAGE]
    dev_action_cycle = ["attach_star", "attach_star", "rewrite", "cut_budget", "call_in_favour", "option_adaptation", "new_financier", "take_to_market"]
    attach_type_cycle = ["bankable", "genre_fit", "studio_favorite"]

    for year in range(years):
        board = session.offer_board()
        if tendency == "opportunist":
            # No fixed lane, no fixed number of looks — the whole point of this policy is refusing
            # to settle for the first handful of listings the way every other tendency does.
            for _ in range(OPPORTUNIST_SCAN_BATCHES):
                board = board + session.generate_more_listings()
        available = [o for o in board if o["available"]]
        best = None
        if available:
            if tendency == "gambler":
                # biggest swing available: chase the highest-budget lead/supporting role regardless
                # of buzz — a real "go big or go home" policy.
                best = max(available, key=lambda o: (BILLING_RANK.get(o["billing"], 0), o["budget_millions"]))
            elif tendency == "opportunist":
                # "whatever works best for him" — a blended read across demand, billing, buzz, AND
                # the fee itself (the other tendencies never weigh raw pay at all): no genre/
                # archetype loyalty, no buzz gate that can leave the year empty — just whichever
                # real listing, out of everything actually scanned this year, scores highest.
                def opportunist_score(o):
                    demand = world_genre_demand(session.state.genre_heat, o["genre"])
                    billing_payoff = {"lead": 1.0, "supporting": 0.75, "bit": 0.4, "extra": 0.05}.get(o["billing"], 0.0)
                    buzz = BUZZ_RANK.get(o.get("buzz_band"), 0) * 15.0
                    return (demand * 0.6 + buzz) * billing_payoff + o["fee_millions"] * 0.5
                best = max(available, key=opportunist_score)
            elif tendency == "prestige":
                def score(o):
                    buzz = BUZZ_RANK.get(o.get("buzz_band"), 0) * 30.0
                    demand = world_genre_demand(session.state.genre_heat, o["genre"])
                    billing_payoff = {"lead": 1.0, "supporting": 0.55, "bit": 0.2, "extra": 0.0}.get(o["billing"], 0.0)
                    return (buzz + demand * 0.5) * billing_payoff
                candidate = max(available, key=score)
                if BUZZ_RANK.get(candidate.get("buzz_band"), 0) >= 3 and candidate["billing"] != "extra":
                    best = candidate
            else:  # workhorse — no buzz gate at all, just the best-fitting real job on offer this
                # year. Genre demand still matters (nobody works entirely blind to what's hot), but
                # there's no minimum bar that can leave the whole year empty the way prestige's does.
                def steady_score(o):
                    demand = world_genre_demand(session.state.genre_heat, o["genre"])
                    billing_payoff = {"lead": 1.0, "supporting": 0.8, "bit": 0.5, "extra": 0.1}.get(o["billing"], 0.0)
                    return demand * billing_payoff
                best = max(available, key=steady_score)

        if best is not None:
            session.accept(best["index"])
            # §6.5 v21 — always reach for the rarer, better-paying first-dollar gross deal first;
            # fall back to net points when Standing hasn't cleared that higher bar yet.
            bonus_type = "first_dollar_gross" if session.box_office_bonus_available("first_dollar_gross") else "net_points"
            # leverage/merchandising.py — take the ongoing royalty whenever it's actually on the
            # table (an animated franchise role at real Standing); costs nothing else to ask.
            want_merch = session.merchandising_available()
            if tendency == "gambler":
                session.choose_deal(want_approvals=False, want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
                session.choose_prep("live_it")
            elif tendency == "opportunist":
                # Adaptive per listing rather than one fixed style all career: only asks for real
                # script/costar approval when this particular project is actually worth protecting
                # (real buzz, real billing) — every other ask (bonus, merch) is free either way, so
                # always taken.
                buzz_rank = BUZZ_RANK.get(best.get("buzz_band"), 0)
                want_approvals = buzz_rank >= 3 and best["billing"] in ("lead", "supporting")
                session.choose_deal(want_approvals=want_approvals, want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
                session.choose_prep("live_it" if buzz_rank >= 2 else "table_work")
                if want_approvals and session.script_notes_available():
                    session.choose_script_note("whole_film")
            elif tendency == "prestige":
                session.choose_deal(want_approvals=True, want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
                session.choose_prep("physical_transformation")
                if session.script_notes_available():
                    session.choose_script_note("whole_film")
            else:  # workhorse — takes the ordinary deal on the table, no special asks beyond the
                # box-office bonus (free to request, costs nothing to ask for), plain table-work prep.
                session.choose_deal(want_approvals=False, want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
                session.choose_prep("table_work")
            for episode in session.episode_labels():
                for scene_choice in SCENE_POSITIONS:
                    session.play_scene(scene_choice)
            if session.rating_cut_available():
                session.choose_rating_stance("release_as_shot")
            session.request_marketing_push()
            if tendency == "gambler":
                strategy = "wide"
            elif tendency == "prestige":
                strategy = "wide" if best["budget_millions"] >= 60.0 else "limited"
            elif tendency == "opportunist":
                strategy = "wide" if best["budget_millions"] >= 45.0 else "limited"
            else:
                strategy = "wide" if best["budget_millions"] >= 40.0 else "limited"
            result = session.choose_release(strategy)
            films_acted.append({
                "genre": best["genre"], "billing": best["billing"], "studio_tag": best["studio_name"],
                "is_animation": best.get("is_animation", False), **result,
            })
        else:
            session.decline_board()
            while session.actor_quarters_remaining_this_year() > 0:
                lev = session.leverage_status()
                if lev["next_tier"]:
                    msg = session.try_advance_agent_tier()
                    if "Signed" in msg:
                        continue
                roster = session.rolodex_summary()
                target = next((n for n in roster if n["relationship"] not in ("loyal", "legacy")), None)
                if target is None:
                    break
                before = session.actor_quarters_remaining_this_year()
                session.interact(target["id"], "check_in")
                if session.actor_quarters_remaining_this_year() == before:
                    break

        offer = session.check_for_hire_offer()
        if offer is not None:
            accept = tendency != "prestige" or session.director_status()["standing"] not in ("unknown",)
            if accept:
                session.accept_hire_offer()  # v12 — only starts the shoot now; the real result
                # (if any) shows up in end_year()'s own returned list once it actually wraps.
            else:
                session.decline_hire_offer()

        while session.quarters_remaining_this_year() > 0:
            status = session.director_status()
            for s in status["projects"]:
                if s["momentum_band"] == "dead":
                    session.scrap_directing_project(s["index"])
                    status = session.director_status()
                    break
            if status["can_start_new_project"]:
                genre = GENRES[genre_i % len(GENRES)]
                genre_i += 1
                if tendency == "gambler":
                    tier = "upper"
                elif tendency == "prestige":
                    tier = "micro" if status["standing"] in ("unknown", "working") else "low"
                else:  # workhorse — a steady mid tier every time, never chasing the top and never
                    # staying stuck at micro once there's a real track record
                    tier = "micro" if status["standing"] == "unknown" else "low"
                if session.start_directing_project(genre, tier):
                    new = session.director_status()["projects"][-1]
                    if tendency == "gambler":
                        session.choose_director_casting_action(new["index"], casting.BANKABLE_WRONG_FIT)
                        session.choose_director_shoot_style_action(new["index"], shoot_style.LONG_TAKES)
                    elif tendency == "prestige":
                        session.choose_director_casting_action(new["index"], casting.YOUR_ROSTER)
                        session.choose_director_shoot_style_action(new["index"], shoot_style.HEAVY_COVERAGE)
                        session.choose_director_script_note_action(new["index"], "whole_film")
                    else:  # workhorse — reliable, efficient, no artistic risk-taking either way
                        session.choose_director_casting_action(new["index"], casting.YOUR_ROSTER)
                        session.choose_director_shoot_style_action(new["index"], shoot_style.LEAN_AND_FAST)
                    session.request_director_release_strategy(new["index"], "wide" if tendency == "gambler" else "limited")
                    session.request_director_marketing_push_action(new["index"])
                    status = session.director_status()
            if not status["projects"]:
                continue
            best_project = max(status["projects"], key=lambda s: MOMENTUM_RANK.get(s["momentum_band"], 0))
            project_index = best_project["index"]
            if tendency == "gambler":
                action = "attach_star" if tick % 2 == 0 else "take_to_market"
            elif tendency == "prestige":
                action = "rewrite" if tick % 3 != 0 else "attach_star"
            else:  # workhorse — mostly rewrite (the one lever that raises real script quality),
                # attach_star only occasionally to keep momentum from stalling outright
                action = "rewrite" if tick % 4 != 0 else "attach_star"
            tick += 1
            if action == "attach_star":
                opts = session.attach_star_target_options()
                atype = "bankable" if tendency == "gambler" else attach_type_cycle[tick % len(attach_type_cycle)]
                session.choose_attach_star_target(opts[tick % len(opts)]["id"], atype)
            session.advance_directing(project_index, action)  # v12 — only starts/advances the
            # shoot now; the real result (if any) shows up in end_year()'s own returned list.
            if session.platform_expansion_available():
                session.request_platform_expansion()

        # §11.6 — "the correct move almost nobody makes in time." A real policy, not just present
        # in the engine: once net worth has actually gone negative, take the Affection hit and cut
        # the floor to something a disciplined tendency (prestige, workhorse) can live within; the
        # gambler keeps outspending on purpose, matching their whole "go big" policy above.
        if tendency != "gambler" and session.state.life.money.net_worth < 0.0:
            session.cut_lifestyle_floor(session.state.life.money.lifestyle_floor * 0.5)

        wrapped = session.end_year()
        for result in wrapped:
            films_directed.append({"genre": result["genre"], **result})
        if session.platform_expansion_available():
            session.request_platform_expansion()
        if session.is_over():
            break

    d = session.director_status()
    return {
        "seed": seed, "tendency": tendency, "max_stats": max_stats, "age": session.age(),
        "acting_credits": len(films_acted), "director_credits": d["credits"],
        "director_standing": d["standing"], "agent_tier": session.leverage_status()["agent_tier"],
        "net_worth": round(session.state.life.money.net_worth, 1),
        "actor_standing": {k: round(session.state.actor.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "director_standing_raw": {k: round(session.state.director.standing[k], 1) for k in ("heat", "prestige", "affection", "notoriety")},
        "films_acted": films_acted, "films_directed": films_directed,
        "merchandising_status": session.merchandising_status(),
        "retired_franchises": [
            {"id": fid, "genre": f.genre, "peak_indispensability": round(f.peak_indispensability, 1), "retired_year": f.retired_year}
            for fid, f in session.state.retired_franchises.items()
        ],
        "franchise_status": session.franchise_status(),
    }


if __name__ == "__main__":
    import sys
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 77
    tendency = sys.argv[2] if len(sys.argv) > 2 else "gambler"
    max_stats = (sys.argv[3] == "max") if len(sys.argv) > 3 else False
    data = run(seed, tendency, max_stats=max_stats)
    print(json.dumps(data, indent=2, default=str))
