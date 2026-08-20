"""Superseded by _full_data_report.py for new work (same read-only-state-access shape, plus named
tendencies and a full JSON dump). Kept as the simplest/oldest of these scripts — useful as a quick
sanity smoke test when you don't need the fuller report.

One-off reporting script: runs a full auto-played career through Session (the real
player-facing API — same path the CLI uses) and prints a data-dense report, reaching past the
Session facade only to read final state for numbers Session doesn't yet surface to a player
(net worth, raw Standing meters) — same read-only access verify.py already uses for reporting.
"""
from __future__ import annotations

import statistics
import sys
from collections import Counter

from callback.engine.simulation.session import Session
from callback.engine.simulation._sim_policy_shared import SCENE_POSITIONS


def run(seed: int) -> None:
    session = Session(seed=seed)
    session.start("conservatory", "work")

    projects = []
    directed_films = []
    rating_bands = Counter()
    rating_forced = 0
    rating_pressure_held = 0
    rating_no_pressure = 0
    genre_counts = Counter()
    studio_counts = Counter()
    release_counts = Counter()
    critic_bands = Counter()
    audience_bands = Counter()
    roi_bands = Counter()
    franchise_max_installment = 0
    total_gross = 0.0
    total_budget = 0.0
    total_marketing = 0.0
    years_with_no_offer = 0
    directing_years = 0

    max_years = 90
    for _ in range(max_years):
        if session.is_over():
            break
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        if not available:
            session.decline_board()
            years_with_no_offer += 1
        else:
            # Take the best-fee available listing — a simple, consistent auto-policy.
            best = max(available, key=lambda o: o["fee_millions"])
            genre_counts[best["genre"]] += 1
            age_this_year = session.age()
            session.accept(best["index"])
            session.choose_deal(want_approvals=session.approvals_available())
            if session.script_notes_available():
                session.choose_script_note("whole_film")
            session.choose_orientation(None, "neutral")
            session.choose_prep("table_work")
            for scene_choice in SCENE_POSITIONS:
                session.play_scene(scene_choice)
            if session.rating_cut_available():
                # Always request the film as shot — the studio's own pressure is what we're
                # measuring, not player timidity.
                session.choose_rating_stance("release_as_shot")
            summary = session.choose_release("wide")

            rating_bands[summary["rating_band"]] += 1
            if summary["rating_cut_forced"]:
                rating_forced += 1
            elif summary["rating_studio_pressure"]:
                rating_pressure_held += 1
            else:
                rating_no_pressure += 1
            studio_counts[summary["studio_name"]] += 1
            release_counts[summary["release_label"]] += 1
            critic_bands[summary["critic_band"]] += 1
            audience_bands[summary["audience_band"]] += 1
            roi_bands[summary["roi_band"]] += 1
            total_gross += summary["gross_millions"]
            total_budget += summary["budget_millions"]
            total_marketing += summary["marketing_millions"]
            franchise_max_installment = max(franchise_max_installment, summary["franchise_installment"])
            summary["age"] = age_this_year
            summary["genre"] = best["genre"]
            summary["fee_millions"] = best["fee_millions"]
            projects.append(summary)

        # A deterministic cross into directing, not a coin flip — this run is explicitly "also a
        # director," so pursue it every single year once unlocked (directing_unlocked() is always
        # True; the trigger here is just "give the acting career a handful of credits first").
        if not session.is_directing() and session.state.actor.credits >= 3:
            session.become_director()
        if session.is_directing():
            directing_years += 1
            director_age = session.age()
            status = session.director_status()
            if not status["in_development"]:
                genre = session.rng.choice([g for g, _ in session.director_genre_options()])
                session.start_directing_project(genre, "mid")
            else:
                dev_genre = status["genre"]
                result = session.advance_directing("rewrite" if status["momentum"] < 5 else "take_to_market")
                if result["greenlit"]:
                    directed_films.append({
                        "age": director_age, "genre": dev_genre,
                        "budget_millions": result["budget_millions"],
                        "marketing_millions": result["marketing_millions"],
                        "gross_millions": result["gross_millions"], "roi": result["roi"],
                        "roi_band": result["roi_band"], "critic_band": result["critic_band"],
                        "critic_score": result["critic_score"], "audience_band": result["audience_band"],
                        "release_label": result["release_label"], "self_financed": result["self_financed"],
                    })

        session.end_year()

    ob = session.obituary_summary()
    state = session.state  # reading past the facade for reporting only — see module docstring

    print(f"=== CAREER REPORT — seed {seed} ===\n")
    print(f"Age at end: {session.age()}  ·  Standing band: {session.standing_summary()}")
    sm = state.actor.standing
    print(f"Raw Standing meters — Heat {sm['heat']:.1f}  Prestige {sm['prestige']:.1f}  "
          f"Affection {sm['affection']:.1f}  Notoriety {sm['notoriety']:.1f}")
    print(f"Net worth: ${state.life.money.net_worth:,.1f}M")
    print(f"Credits: {ob['credits']}  ·  Years with no offer taken: {years_with_no_offer}  ·  "
          f"Years spent directing: {directing_years}")
    print()

    print("--- CONTENT RATINGS ---")
    for band in ("G", "PG", "PG-13", "R", "NC-17"):
        if rating_bands[band]:
            print(f"  {band}: {rating_bands[band]}")
    total_rated = sum(rating_bands.values())
    if total_rated:
        print(f"  Studio forced a cut: {rating_forced} ({100*rating_forced/total_rated:.0f}%)")
        print(f"  Player held the line against studio pressure: {rating_pressure_held} "
              f"({100*rating_pressure_held/total_rated:.0f}%)")
        print(f"  No studio pressure at all: {rating_no_pressure} ({100*rating_no_pressure/total_rated:.0f}%)")
    print()

    print("--- STUDIOS WORKED WITH ---")
    for studio, n in studio_counts.most_common():
        print(f"  {studio}: {n}")
    print()

    print("--- RELEASE STRATEGIES ---")
    for strat, n in release_counts.most_common():
        print(f"  {strat}: {n}")
    print()

    print("--- RECEPTION ---")
    print("  Critics:", dict(critic_bands))
    print("  Audience:", dict(audience_bands))
    print("  ROI bands:", dict(roi_bands))
    print()

    print("--- MONEY (production side, not your own fee) ---")
    print(f"  Total production budget across career: ${total_budget:,.1f}M")
    print(f"  Total marketing spend: ${total_marketing:,.1f}M")
    print(f"  Total gross: ${total_gross:,.1f}M")
    if total_budget:
        print(f"  Career-wide ROI: {total_gross/total_budget:.2f}x")
    print()

    if projects:
        print("--- FILM-BY-FILM BOX OFFICE ---")
        header = (f"  {'Age':>3}  {'Genre':<9} {'Your fee':>9} {'Budget':>9} {'Marketing':>10} "
                  f"{'Gross':>10} {'ROI':>6}  {'Rated':<6} {'Critics':<8} {'Audience':<12} {'Release':<10}")
        print(header)
        print("  " + "-" * (len(header) - 2))
        for p in projects:
            franchise_tag = f" [F#{p['franchise_installment']}]" if p["franchise_installment"] else ""
            print(f"  {p['age']:>3}  {p['genre']:<9} ${p['fee_millions']:>7.2f}M ${p['budget_millions']:>7.1f}M "
                  f"${p['marketing_millions']:>8.1f}M ${p['gross_millions']:>8.1f}M {p['roi']:>5.2f}x  "
                  f"{p['rating_band']:<6} {p['critic_band']:<8} {p['audience_band']:<12} "
                  f"{p['release_label'].split(' —')[0]:<10}{franchise_tag}")
        print()

        rois = [p["roi"] for p in projects]
        grosses = [p["gross_millions"] for p in projects]
        print("--- DISTRIBUTION ---")
        print(f"  ROI — median {statistics.median(rois):.2f}x, best {max(rois):.2f}x, worst {min(rois):.2f}x")
        print(f"  Gross — median ${statistics.median(grosses):.1f}M, biggest ${max(grosses):.1f}M")
        print()

        print("  Top 5 grossing:")
        for p in sorted(projects, key=lambda p: -p["gross_millions"])[:5]:
            print(f"    Age {p['age']} · {p['genre']} · {p['studio_name']} · ${p['gross_millions']:.1f}M gross "
                  f"(ROI {p['roi']:.2f}x) · rated {p['rating_band']}")
        print("  Worst 5 by ROI:")
        for p in sorted(projects, key=lambda p: p["roi"])[:5]:
            print(f"    Age {p['age']} · {p['genre']} · {p['studio_name']} · ${p['gross_millions']:.1f}M gross "
                  f"(ROI {p['roi']:.2f}x) · rated {p['rating_band']}")
        print()

    print("--- DIRECTING CAREER ---")
    if directing_years:
        final_director_status = session.director_status()
        print(f"  Years spent directing: {directing_years}  ·  Films directed: {len(directed_films)}  ·  "
              f"Directing credits: {final_director_status['credits']}  ·  "
              f"Directing standing: {final_director_status['standing']}")
        if directed_films:
            print()
            print("  --- DIRECTED FILM-BY-FILM BOX OFFICE (full ledger) ---")
            dheader = (f"  {'Age':>3}  {'Genre':<9} {'Budget':>9} {'Marketing':>10} {'Gross':>10} "
                       f"{'ROI':>6}  {'Critics':<8} {'Audience':<12} {'Release':<10} {'Self-fin.':<9}")
            print(dheader)
            print("  " + "-" * (len(dheader) - 2))
            for f in directed_films:
                print(f"  {f['age']:>3}  {f['genre']:<9} ${f['budget_millions']:>7.1f}M "
                      f"${f['marketing_millions']:>8.1f}M ${f['gross_millions']:>8.1f}M {f['roi']:>5.2f}x  "
                      f"{f['critic_band']:<8} {f['audience_band']:<12} "
                      f"{f['release_label'].split(' —')[0]:<10} {'yes' if f['self_financed'] else 'no':<9}")
            d_gross = sum(f["gross_millions"] for f in directed_films)
            d_budget = sum(f["budget_millions"] for f in directed_films)
            print(f"  Directing totals — gross ${d_gross:,.1f}M on ${d_budget:,.1f}M budget "
                  f"({d_gross/d_budget:.2f}x combined ROI)" if d_budget else "")
        else:
            print("  Crossed into directing but never got a project greenlit.")
    else:
        print("  Never crossed into directing this run.")
    print()

    print(f"--- FRANCHISE ---")
    print(f"  Deepest franchise run reached: installment #{franchise_max_installment}" if franchise_max_installment
          else "  No franchise ever took off.")
    fs = session.franchise_status()
    for f in fs:
        print(f"  {f}")
    print()

    print("--- STUDIO RELATIONSHIPS (trust, remembered P&L) ---")
    for rel in session.studio_relations_status():
        print(f"  {rel['studio_name']}: {rel['trust_band']}, {rel['projects_together']} films, "
              f"net ${rel['net_profit_millions']:.1f}M")
    print()

    print("--- OBITUARY ---")
    print(f"  {ob['credits']} credited roles played.")
    print(f"  {len(ob['declined'])} declined roles shown (sample).")
    print(f"  Relationships kept: {ob['kept']}  ·  lost: {ob['lost']}")
    if ob["best_hidden_performance"]:
        bh = ob["best_hidden_performance"]
        print(f"  Best hidden performance: a {bh['genre']} film — {bh['band']}.")


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 101
    run(seed)
