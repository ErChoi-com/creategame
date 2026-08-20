"""Superseded by _full_data_report.py for new work (it covers this same director-triage policy
plus acting, both tendencies, and a full JSON dump) — kept as-is since it's still a real, narrower
harness for director-only runs. Prefer _full_data_report.py unless you specifically want acting
out of the picture.

One-off reporting script: a director-focused career through Session — real per-quarter dev
actions across a real slate, casting/shoot choices, hire offers, platform expansion, and limbo
consequences (fired/canceled/handed-free/bought-out) — printing everything notable.

§7.4 v16 policy ("genuine direction"): each quarter, triage across the whole slate rather than
grinding one project blindly — pitch a second/third project once there's real slack, prioritize
whichever project has the best momentum this quarter, and only stay at budget tiers this
director's current PackageStrength can plausibly clear.
"""
from __future__ import annotations

from collections import Counter

from callback.engine.director import casting, shoot_style
from callback.engine.simulation.session import Session

MOMENTUM_RANK = {"dead": 0, "fading": 1, "building": 2, "real heat": 3, "can't-miss": 4}


def run(seed: int, years: int = 60, quiet: bool = False) -> dict:
    session = Session(seed=seed)
    session.start("conservatory", "work")
    session.become_director()

    films = []
    dev_action_counts = Counter()
    momentum_band_seen = Counter()
    limbo_kind_counts = Counter()
    hire_offers_seen = 0
    hire_offers_accepted = 0
    expansions_attempted = 0
    expansions_granted = 0
    dead_projects = 0
    scrapped_projects = 0
    projects_started = 0

    dev_action_cycle = ["attach_star", "attach_star", "rewrite", "cut_budget", "call_in_favour", "option_adaptation", "new_financier", "take_to_market"]
    casting_cycle = [casting.YOUR_ROSTER, casting.DIFFICULT_GENIUS, casting.DISCOVERY, casting.BANKABLE_WRONG_FIT, casting.RIGHT_ACTOR_NO_HEAT]
    style_cycle = [shoot_style.LONG_TAKES, shoot_style.LEAN_AND_FAST, shoot_style.MANY_TAKES, shoot_style.IMPROVISATION, shoot_style.HEAVY_COVERAGE]
    attachment_type_cycle = ["bankable", "genre_fit", "studio_favorite"]
    genre_i = 0
    genres = ["drama", "thriller", "horror", "comedy", "scifi", "action", "period", "romance", "musical", "family"]
    tick = 0  # counts quarters, for cycling actions/casting/style deterministically
    total_attached = 0
    total_dropped = 0
    max_slate_seen = 0
    offers_made = 0
    offers_accepted = 0

    def pitch(status):
        nonlocal genre_i, projects_started
        genre = genres[genre_i % len(genres)]
        genre_i += 1
        # genuine direction: stay at a tier this director's real Standing can plausibly clear —
        # the instrumented PackageStrength/Difficulty gap makes "upper" a trap for a newcomer.
        tier = "micro" if status["standing"] in ("unknown", "working") else "low"
        if session.start_directing_project(genre, tier):
            projects_started += 1
            new = session.director_status()["projects"][-1]
            session.choose_director_casting_action(new["index"], casting_cycle[tick % len(casting_cycle)])
            session.choose_director_shoot_style_action(new["index"], style_cycle[tick % len(style_cycle)])

    for year in range(years):
        offer = session.check_for_hire_offer()
        if offer is not None:
            hire_offers_seen += 1
            accept = session.rng.random() < 0.7
            if accept:
                hire_offers_accepted += 1
                offer_genre = offer["genre"]
                result = session.accept_hire_offer()
                if result["greenlit"]:
                    films.append({**result, "via": "hire", "genre": offer_genre})
                limbo_kind_counts.update(e["kind"] for e in result.get("limbo_events", []))
            else:
                session.decline_hire_offer()

        while session.quarters_remaining_this_year() > 0:
            status = session.director_status()

            # scrap anything that's been sitting dead-in-the-water (flat "dead" band) — real
            # dead weight, free the slot rather than let it squat.
            for s in status["projects"]:
                if s["momentum_band"] == "dead":
                    session.scrap_directing_project(s["index"])
                    scrapped_projects += 1
                    status = session.director_status()
                    break

            if status["can_start_new_project"]:
                pitch(status)
                status = session.director_status()

            if not status["projects"]:
                break  # nothing to do this quarter — a rare gap right after everything resolved

            max_slate_seen = max(max_slate_seen, len(status["projects"]))
            # triage: work whichever project currently has the best momentum band
            best = max(status["projects"], key=lambda s: MOMENTUM_RANK.get(s["momentum_band"], 0))
            project_index = best["index"]

            action = dev_action_cycle[tick % len(dev_action_cycle)]
            tick += 1
            if action == "attach_star":
                opts = session.attach_star_target_options()
                atype = attachment_type_cycle[tick % len(attachment_type_cycle)]
                session.choose_attach_star_target(opts[tick % len(opts)]["id"], atype)
                offers_made += 1
            dev_action_counts[action] += 1
            result = session.advance_directing(project_index, action)
            momentum_band_seen[result.get("momentum_band", "")] += 1
            limbo_kind_counts.update(e["kind"] for e in result.get("limbo_events", []))
            if result.get("attachment_offer_accepted") is True:
                offers_accepted += 1
                total_attached += 1
            total_dropped += len(result.get("dropped_attachments", []))
            if result["greenlit"]:
                films.append({**result, "via": "own", "genre": best["genre"]})
            elif result["dead"]:
                dead_projects += 1

            if session.platform_expansion_available():
                expansions_attempted += 1
                outcome = session.request_platform_expansion()
                if outcome["granted"]:
                    expansions_granted += 1

        session.end_year()
        if session.is_over():
            break

    d = session.director_status()
    summary = {
        "seed": seed, "age": session.age(), "credits": d["credits"], "standing": d["standing"],
        "films": len(films), "dead_projects": dead_projects, "scrapped_projects": scrapped_projects,
        "projects_started": projects_started, "max_slate_seen": max_slate_seen,
        "hire_offers_seen": hire_offers_seen, "hire_offers_accepted": hire_offers_accepted,
        "limbo_kind_counts": dict(limbo_kind_counts),
        "heat": session.state.director.standing["heat"], "prestige": session.state.director.standing["prestige"],
    }

    if quiet:
        return summary

    print(f"=== DIRECTOR CAREER REPORT — seed {seed} ===\n")
    print(f"Age at end: {session.age()}")
    print(f"Director credits: {d['credits']}  ·  Director Standing: {d['standing']}")
    print(f"Projects started: {projects_started}  ·  scrapped: {scrapped_projects}  ·  largest slate at once: {max_slate_seen}")
    print(f"Hire offers seen: {hire_offers_seen}  ·  accepted: {hire_offers_accepted}")
    print(f"Projects that hit the limbo threshold: {sum(limbo_kind_counts.values())}")
    for kind, n in limbo_kind_counts.most_common():
        print(f"  {kind}: {n}")
    print(f"Attach offers made: {offers_made}  ·  accepted: {offers_accepted} "
          f"({100*offers_accepted/offers_made:.0f}%)  ·  dropped before greenlight: {total_dropped}" if offers_made else "No attach offers made.")
    print(f"Platform expansion attempts: {expansions_attempted}  ·  granted: {expansions_granted}")
    print()

    print("--- DEV ACTIONS TAKEN ---")
    for a, n in dev_action_counts.most_common():
        print(f"  {a}: {n}")
    print()

    print("--- MOMENTUM BAND (each dev-action quarter, worked project only) ---")
    for band, n in momentum_band_seen.most_common():
        print(f"  {band}: {n}")
    print()

    if films:
        print(f"--- FILMS DIRECTED: {len(films)} ---")
        header = (f"  {'Genre':<9} {'Via':<5} {'Budget':>8} {'Marketing':>10} {'Gross':>9} {'ROI':>6}  "
                  f"{'Rated':<6} {'Critics':<8} {'Audience':<12} {'Release':<10} {'Cast':<18} {'Shot':<15}")
        print(header)
        print("  " + "-" * (len(header) - 2))
        for f in films:
            print(f"  {f['genre']:<9} {f['via']:<5} ${f['budget_millions']:>6.1f}M ${f['marketing_millions']:>8.1f}M "
                  f"${f['gross_millions']:>7.1f}M {f['roi']:>5.2f}x  {f['rating_band']:<6} {f['critic_band']:<8} "
                  f"{f['audience_band']:<12} {f['release_label'].split(' —')[0]:<10} "
                  f"{f.get('casting_choice','')[:18]:<18} {f.get('shoot_style','')[:15]:<15}")
        print()
        total_gross = sum(f["gross_millions"] for f in films)
        total_budget = sum(f["budget_millions"] for f in films)
        print(f"Totals — ${total_budget:,.1f}M budget, ${total_gross:,.1f}M gross, "
              f"{total_gross/total_budget:.2f}x combined ROI" if total_budget else "")
        hire_films = [f for f in films if f["via"] == "hire"]
        if hire_films:
            print(f"Hire films: {len(hire_films)} of {len(films)} — "
                  f"avg ROI {sum(f['roi'] for f in hire_films)/len(hire_films):.2f}x")
    else:
        print("No films ever got made — every project died in development.")

    print()
    print("--- STANDING (raw meters) ---")
    sm = session.state.director.standing
    print(f"  Heat {sm['heat']:.1f}  Prestige {sm['prestige']:.1f}  Affection {sm['affection']:.1f}  Notoriety {sm['notoriety']:.1f}")
    return summary


if __name__ == "__main__":
    import sys
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 7)
