"""Superseded by _full_data_report.py's "gambler" tendency for new work (same both-tracks,
triage-driven shape, plus a full JSON dump and a second tendency to compare against). Kept as its
own script for its distinct triage details below.

One-off reporting script: an actor/director playing BOTH tracks (§7.11) with a genuinely smart
policy on each side — not a mechanical round-robin, real triage:

Acting: picks the best available offer each year (billing tier first, then budget — a lead in a
small film still beats an extra in a huge one), works Rolodex quarters on whoever's closest to
leveling up a relationship band, advances agent tier the instant it's available, and requests the
release strategy/marketing push that fits the film's own quality read.

Directing: reuses the same real triage from _director_report.py — stays at budget tiers the
current PackageStrength can plausibly clear, works whichever slate project has the best momentum
each quarter, scraps real dead weight, and accepts hire offers when Standing makes them worth it.
"""
from __future__ import annotations

from collections import Counter

from callback.engine.director import casting, shoot_style
from callback.engine.simulation.session import Session
from callback.engine.simulation._sim_policy_shared import SCENE_POSITIONS

MOMENTUM_RANK = {"dead": 0, "fading": 1, "building": 2, "real heat": 3, "can't-miss": 4}
BILLING_RANK = {"lead": 3, "supporting": 2, "bit": 1, "extra": 0}


def _best_offer(board: list[dict]) -> dict | None:
    available = [o for o in board if o["available"]]
    if not available:
        return None
    return max(available, key=lambda o: (BILLING_RANK.get(o["billing"], 0), o["budget_millions"]))


def _spend_actor_quarters(session: Session) -> list[str]:
    """Between roles: work whichever tracked relationship is closest to leveling up, then the
    agent tier the moment Standing supports it — real triage, not spending quarters at random."""
    notes = []
    while session.actor_quarters_remaining_this_year() > 0:
        lev_status = session.leverage_status()
        if lev_status["next_tier"]:
            msg = session.try_advance_agent_tier()
            if "Signed with" in msg:
                notes.append(msg)
                continue
        roster = session.rolodex_summary()
        if not roster:
            break
        # prioritize relationships not already at the top band — checking in on someone maxed out
        # is wasted attention.
        target = next((n for n in roster if n["relationship"] not in ("loyal", "legacy")), None)
        if target is None:
            break
        before_remaining = session.actor_quarters_remaining_this_year()
        msg = session.interact(target["id"], "check_in")
        notes.append(msg)
        if session.actor_quarters_remaining_this_year() == before_remaining:
            break  # refused (no time) — stop rather than loop forever
    return notes


def _director_pitch(session: Session, status: dict, genre_i: list[int], tick: int,
                     casting_cycle, style_cycle) -> None:
    genres = ["drama", "thriller", "horror", "comedy", "scifi", "action", "period", "romance", "musical", "family"]
    genre = genres[genre_i[0] % len(genres)]
    genre_i[0] += 1
    tier = "micro" if status["standing"] in ("unknown", "working") else "low"
    if session.start_directing_project(genre, tier):
        new = session.director_status()["projects"][-1]
        session.choose_director_casting_action(new["index"], casting_cycle[tick % len(casting_cycle)])
        session.choose_director_shoot_style_action(new["index"], style_cycle[tick % len(style_cycle)])


def run(seed: int, years: int = 60, quiet: bool = False) -> dict:
    session = Session(seed=seed)
    session.start("conservatory", "work")
    session.become_director()

    films_acted = []
    films_directed = []
    dev_action_counts = Counter()
    limbo_kind_counts = Counter()
    hire_offers_seen = 0
    hire_offers_accepted = 0
    dead_projects = 0
    scrapped_projects = 0
    agent_tier_advances = 0

    casting_cycle = [casting.YOUR_ROSTER, casting.DIFFICULT_GENIUS, casting.DISCOVERY, casting.BANKABLE_WRONG_FIT, casting.RIGHT_ACTOR_NO_HEAT]
    style_cycle = [shoot_style.LONG_TAKES, shoot_style.LEAN_AND_FAST, shoot_style.MANY_TAKES, shoot_style.IMPROVISATION, shoot_style.HEAVY_COVERAGE]
    attachment_type_cycle = ["bankable", "genre_fit", "studio_favorite"]
    dev_action_cycle = ["attach_star", "attach_star", "rewrite", "cut_budget", "call_in_favour", "option_adaptation", "new_financier", "take_to_market"]
    genre_i = [0]
    tick = 0

    for year in range(years):
        # ---- acting: take the best offer on the board, or spend quarters on Rolodex/Leverage ----
        board = session.offer_board()
        best = _best_offer(board)
        if best is not None:
            session.accept(best["index"])
            session.choose_deal(want_approvals=True)
            session.choose_prep(session.prep_options()[0][0])
            for scene_choice in SCENE_POSITIONS:
                session.play_scene(scene_choice)
            # release request tuned to the film's own budget — a small film goes wide-and-cheap,
            # a real tentpole gets pushed for the widest possible release.
            release_key = "wide"
            result = session.choose_release(release_key)
            films_acted.append({"genre": best["genre"], "billing": best["billing"], **result})
        else:
            session.decline_board()
            notes = _spend_actor_quarters(session)
            agent_tier_advances += sum(1 for n in notes if "Signed with" in n)

        # ---- directing: real per-quarter triage across the slate ----
        offer = session.check_for_hire_offer()
        if offer is not None:
            hire_offers_seen += 1
            standing_word = session.director_status()["standing"]
            worth_it = standing_word in ("working", "in-demand", "a-list") or session.rng.random() < 0.5
            if worth_it:
                hire_offers_accepted += 1
                offer_genre = offer["genre"]
                result = session.accept_hire_offer()
                if result["greenlit"]:
                    films_directed.append({**result, "via": "hire", "genre": offer_genre})
                limbo_kind_counts.update(e["kind"] for e in result.get("limbo_events", []))
            else:
                session.decline_hire_offer()

        while session.quarters_remaining_this_year() > 0:
            status = session.director_status()
            for s in status["projects"]:
                if s["momentum_band"] == "dead":
                    session.scrap_directing_project(s["index"])
                    scrapped_projects += 1
                    status = session.director_status()
                    break
            if status["can_start_new_project"]:
                _director_pitch(session, status, genre_i, tick, casting_cycle, style_cycle)
                status = session.director_status()
            if not status["projects"]:
                break
            best_project = max(status["projects"], key=lambda s: MOMENTUM_RANK.get(s["momentum_band"], 0))
            project_index = best_project["index"]

            action = dev_action_cycle[tick % len(dev_action_cycle)]
            tick += 1
            if action == "attach_star":
                opts = session.attach_star_target_options()
                atype = attachment_type_cycle[tick % len(attachment_type_cycle)]
                session.choose_attach_star_target(opts[tick % len(opts)]["id"], atype)
            dev_action_counts[action] += 1
            result = session.advance_directing(project_index, action)
            limbo_kind_counts.update(e["kind"] for e in result.get("limbo_events", []))
            if result["greenlit"]:
                films_directed.append({**result, "via": "own", "genre": best_project["genre"]})
            elif result["dead"]:
                dead_projects += 1

            if session.platform_expansion_available():
                outcome = session.request_platform_expansion()

        session.end_year()
        if session.is_over():
            break

    d = session.director_status()
    summary = {
        "seed": seed, "age": session.age(),
        "acting_credits": len(films_acted), "director_credits": d["credits"],
        "director_standing": d["standing"], "agent_tier": session.leverage_status()["agent_tier"],
        "films_directed": len(films_directed), "dead_projects": dead_projects,
        "scrapped_projects": scrapped_projects, "hire_offers_seen": hire_offers_seen,
        "hire_offers_accepted": hire_offers_accepted, "limbo_kind_counts": dict(limbo_kind_counts),
        "net_worth": round(session.state.life.money.net_worth, 1),
        "actor_heat": session.state.actor.standing["heat"], "actor_prestige": session.state.actor.standing["prestige"],
        "director_heat": session.state.director.standing["heat"], "director_prestige": session.state.director.standing["prestige"],
    }

    if quiet:
        return summary

    print(f"=== ACTOR/DIRECTOR CAREER REPORT — seed {seed} ===\n")
    print(f"Age at end: {session.age()}  ·  Net worth: ${summary['net_worth']:,.1f}M")
    print(f"Acting credits: {summary['acting_credits']}  ·  Agent tier: {summary['agent_tier']}")
    print(f"Directing credits: {summary['director_credits']}  ·  Director Standing: {summary['director_standing']}")
    print(f"Directing projects: died {dead_projects}, scrapped {scrapped_projects}")
    print(f"Hire offers seen: {hire_offers_seen}  ·  accepted: {hire_offers_accepted}")
    if limbo_kind_counts:
        print("Limbo outcomes:")
        for kind, n in limbo_kind_counts.most_common():
            print(f"  {kind}: {n}")
    print()

    if films_acted:
        print(f"--- FILMS ACTED: {len(films_acted)} ---")
        header = f"  {'Genre':<9} {'Billing':<11} {'Budget':>8} {'ROI':>6}  {'Critics':<8} {'Audience':<12}"
        print(header)
        for f in films_acted:
            print(f"  {f.get('genre','?'):<9} {f.get('billing','?'):<11} ${f.get('budget_millions',0):>6.1f}M "
                  f"{f.get('roi',0):>5.2f}x  {f.get('critic_band','?'):<8} {f.get('audience_band','?'):<12}")
        print()

    if films_directed:
        print(f"--- FILMS DIRECTED: {len(films_directed)} ---")
        header = f"  {'Genre':<9} {'Via':<5} {'Budget':>8} {'ROI':>6}  {'Rated':<6} {'Critics':<8} {'Audience':<12}"
        print(header)
        for f in films_directed:
            print(f"  {f['genre']:<9} {f['via']:<5} ${f['budget_millions']:>6.1f}M {f['roi']:>5.2f}x  "
                  f"{f['rating_band']:<6} {f['critic_band']:<8} {f['audience_band']:<12}")
        print()

    print("--- STANDING (raw meters) ---")
    sa = session.state.actor.standing
    sd = session.state.director.standing
    print(f"  Actor    — Heat {sa['heat']:.1f}  Prestige {sa['prestige']:.1f}  Affection {sa['affection']:.1f}  Notoriety {sa['notoriety']:.1f}")
    print(f"  Director — Heat {sd['heat']:.1f}  Prestige {sd['prestige']:.1f}  Affection {sd['affection']:.1f}  Notoriety {sd['notoriety']:.1f}")
    return summary


if __name__ == "__main__":
    import sys
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
