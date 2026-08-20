"""This policy is now also available as _full_data_report.py's "prestige" tendency (it explicitly
reuses this script's policy) — prefer that one for new work; it adds a "gambler" tendency to
compare against and dumps the full per-film JSON. Kept as its own script for the exhaustive,
narrated per-year ledger below, which _full_data_report.py doesn't print.

One-off reporting script: a genuinely QUALITY-SEEKING actor/director (as opposed to
_smart_report.py's throughput-maximizing policy) — every choice aimed at craft/critical reception,
not just volume. Prints an exhaustive per-year ledger: every offer considered, every choice made
and why, full box-office/reception detail per film, standing traces, financial trace, and a full
obituary at the end.

Policy, actor side:
  - Scores every offer on genre-demand fit + billing, not just billing/budget — and will DECLINE
    the whole board in a weak year rather than take a bad-fit lead role.
  - Always negotiates script + costar approval and the box-office bonus when Standing allows.
  - Requests a trusted Rolodex director when one is available (real chemistry, not a stranger).
  - Plays generous toward a real Rolodex costar when one's attached, building a favour and a real
    craft contribution instead of leaving orientation neutral.
  - Prep: physical_transformation — real craft investment, without live_it's harsh Resilience cost.
  - Scenes: "Match it" on setup/resolution (craft-safe); the turn spikes real personal Spotlight on
    two dials (Beneath) — Spotlight carries 0.26 weight in delta_prestige vs critic score's 0.11,
    and "Match it" everywhere was crushing it to near-zero regardless of how the film scored.
  - Script note: "whole_film" — the one note that improves the film with no tradeoff.
  - Release: limited/festival for anything under a real tentpole budget (a genuine platform/awards
    play), wide only for the biggest films where audience reach still matters more than critics.
  - Always requests the marketing push; always runs an awards campaign when spotlight qualifies.

Policy, director side:
  - Casting: your_roster — reliable, a real Chemistry bonus, no fit penalty.
  - Shoot style: heavy_coverage — the safe, quality-floor choice, fixable in the edit.
  - Script note: whole_film, same as the acting side.
  - Attach type: genre_fit preferred over bankable — eases the ask instead of chasing fame, avoids
    the ensemble-chaos cost a second "bankable" name would add.
  - Dev actions: rewrite dominates the mix (the one lever that raises true script quality) —
    attach_star/call_in_favour only often enough to keep momentum from flatlining.
  - Budget tier stays matched to current Standing (never chases a tier PackageStrength can't clear).
  - Release: limited, same auteur-platform logic as the acting side.
"""
from __future__ import annotations

from callback.engine.director import casting, shoot_style
from callback.engine.simulation.session import Session
from callback.engine.simulation._sim_policy_shared import SCENE_POSITIONS
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand

MOMENTUM_RANK = {"dead": 0, "fading": 1, "building": 2, "real heat": 3, "can't-miss": 4}
BILLING_RANK = {"lead": 3, "supporting": 2, "bit": 1, "extra": 0}
BUZZ_RANK = {
    "nothing you've heard": 0, "quiet": 1, "some heat": 2, "real buzz": 3, "the talk of the town": 4,
}
# The real payoff a billing tier buys in delta_prestige (career.py's BILLING_WEIGHT) — a great-buzz
# bit part is nearly worthless for Prestige no matter how the film does, so the fit score has to
# multiply by this, not just add a small billing bonus on the side.
PRESTIGE_BILLING_WEIGHT = {"lead": 1.0, "supporting": 0.55, "bit": 0.2, "extra": 0.0}
TENTPOLE_BUDGET_THRESHOLD = 60.0  # above this, wide release for reach; below, platform for prestige


def _offer_fit_score(session: Session, offer: dict) -> float:
    # §4.4 v18 — buzz sets the ceiling on how good the film can be; billing sets how much of that
    # actually reaches the actor's own Prestige. Multiplying, not adding, is the real fix: a
    # great-buzz bit part and a great-buzz lead are not comparable picks, because delta_prestige
    # scales by BILLING_WEIGHT — 0.2 for a bit part regardless of the film's own reception.
    buzz = BUZZ_RANK.get(offer.get("buzz_band"), 0) * 30.0
    demand = world_genre_demand(session.state.genre_heat, offer["genre"])
    billing_payoff = PRESTIGE_BILLING_WEIGHT.get(offer["billing"], 0.0)
    return (buzz + demand * 0.5) * billing_payoff


def _pick_best_offer(session: Session, board: list[dict]) -> dict | None:
    available = [o for o in board if o["available"]]
    if not available:
        return None
    best = max(available, key=lambda o: _offer_fit_score(session, o))
    # A genuinely quality-seeking actor turns down a bad-fit lead in a cold genre rather than
    # padding the résumé — the real "waiting for a better shot" behavior. Raised from "some heat"
    # to "real buzz" — the earlier bar accepted roughly the top half of the distribution, landing
    # picks barely above the neutral critic centre instead of genuinely good ones.
    if best["billing"] == "extra" or BUZZ_RANK.get(best.get("buzz_band"), 0) < 3:
        return None
    return best


def _spend_actor_quarters(session: Session, log: list[str]) -> None:
    while session.actor_quarters_remaining_this_year() > 0:
        lev_status = session.leverage_status()
        if lev_status["next_tier"]:
            msg = session.try_advance_agent_tier()
            if "Signed with" in msg:
                log.append(f"    [quarter] {msg}")
                continue
        roster = session.rolodex_summary()
        target = next((n for n in roster if n["relationship"] not in ("loyal", "legacy")), None)
        if target is None:
            break
        before = session.actor_quarters_remaining_this_year()
        msg = session.interact(target["id"], "check_in")
        if session.actor_quarters_remaining_this_year() == before:
            break
        log.append(f"    [quarter] check in with {target['id']} ({target['relationship']}) — {msg}")


def run(seed: int, years: int = 60) -> None:
    session = Session(seed=seed)
    msg = session.start("conservatory", "work")
    print(f"=== A QUALITY-SEEKING CAREER — seed {seed} ===\n")
    print(msg)
    msg = session.become_director()
    print(msg)
    print()

    films_acted = []
    films_directed = []
    declined_years = 0
    awards_won = 0
    awards_nominated = 0
    limbo_kind_counts = {}
    hire_offers_seen = 0
    hire_offers_accepted = 0
    dead_projects = 0
    scrapped_projects = 0
    net_worth_trace = []
    actor_standing_trace = []
    director_standing_trace = []
    tick = 0

    for year in range(years):
        age = session.age()
        print(f"\n{'='*90}\nYEAR {year}  (age {age})\n{'='*90}")

        # ================= ACTING =================
        board = session.offer_board()
        print(f"  OFFER BOARD — {len(board)} listing(s):")
        for o in board:
            tag = "GUARANTEED" if o.get("guaranteed") else ("available" if o["available"] else "no offer came through")
            fit = round(_offer_fit_score(session, o), 1) if o["available"] else "-"
            print(f"    [{o['index']}] {o['genre']:<9} {o['billing']:<10} ${o['budget_millions']:>7.1f}M budget  "
                  f"${o['fee_millions']:>6.2f}M fee  {o['studio_name']:<22} fit={fit:<5} — {tag}")

        best = _pick_best_offer(session, board)
        if best is not None:
            demand = round(world_genre_demand(session.state.genre_heat, best["genre"]), 1)
            print(f"  -> ACCEPTING [{best['index']}] {best['genre']} / {best['billing']} at {best['studio_name']} "
                  f"(genre demand {demand})")
            session.accept(best["index"])

            fee = session.choose_deal(want_approvals=True, want_box_office_bonus=True)
            print(f"    Deal: script+costar approval negotiated"
                  f"{' + box-office bonus' if session.box_office_bonus_available() else ''}"
                  f"{f' — fee after approvals ${fee:.2f}M' if fee is not None else ''}")

            directors = session.available_directors()
            trusted = [d for d in directors if d["relationship"] in ("loyal", "ally") or (d["trust"] and d["trust"]["trust_band"] not in ("wary", "cold"))]
            if trusted:
                pick = trusted[0]
                print(f"    Requesting director: {session.request_director(pick['id'])} ({pick['id']}, {pick['relationship']})")

            costars = session.costar_options()
            if costars:
                partner = costars[0]
                session.choose_orientation(partner["id"], "generous")
                print(f"    Orientation toward {partner['id']} ({partner['relationship']}): generous — let them have the moment")
            else:
                session.choose_orientation(None, "neutral")

            session.choose_prep("physical_transformation")
            print("    Prep: physical transformation — real craft investment")

            if session.script_notes_available():
                session.choose_script_note("whole_film")
                print("    Script note: push for the whole film")

            for i, name in enumerate(session.scene_names()):
                session.play_scene(SCENE_POSITIONS[i])
                tag = "Match it on every dial" if i != 1 else "spiking Energy/Volume for real Spotlight, Match it elsewhere"
                print(f"    Scene {i+1} ({name}): {tag}")

            if session.rating_cut_available():
                preview = session.rating_preview()
                session.choose_rating_stance("release_as_shot")
                print(f"    Rating: {preview['band']} — near a boundary, releasing as shot (the film you made)")

            session.request_marketing_push()
            strategy = "wide" if best["budget_millions"] >= TENTPOLE_BUDGET_THRESHOLD else "limited"
            result = session.choose_release(strategy)
            print(f"    Requested release: {strategy}")

            record = {"genre": best["genre"], "billing": best["billing"], "studio": best["studio_name"], **result}
            films_acted.append(record)

            if "release_label" in result:  # a film
                print(f"    >>> RESULT: {result['release_label']}"
                      + (f" (studio overruled your {strategy} request)" if result["studio_overruled"] else ""))
                print(f"        Budget ${result['budget_millions']:.1f}M · Marketing ${result['marketing_millions']:.1f}M · "
                      f"Gross ${result['gross_millions']:.1f}M · ROI {result['roi']:.2f}x ({result['roi_band']})")
                if result["box_office_bonus_millions"] > 0:
                    print(f"        Box-office bonus earned: ${result['box_office_bonus_millions']:.2f}M")
                if result["weekly_gross"]:
                    print(f"        Weekly gross curve: {result['weekly_gross']}")
            else:  # a season (simulation.session._choose_release_series) — no release/box-office concepts
                print(f"    >>> SEASON RESULT: {result['n_episodes']} episodes on {result['studio_name']}")
                print(f"        Budget ${result['budget_millions']:.1f}M · Marketing ${result['marketing_millions']:.1f}M · "
                      f"License value ${result['license_value_millions']:.1f}M · ROI {result['roi']:.2f}x ({result['roi_band']})")
                if result["renewable"]:
                    print(f"        Renewal chance: {result['renewal_chance']*100:.0f}% — {'RENEWED' if result['renewed'] else 'not renewed'}")
            print(f"        Critics: {result['critic_band']} ({result['critic_score']}) · Audience: {result['audience_band']} · "
                  f"Performance: {result['performance_band']}")
            print(f"        Rating: {result['rating_band']} ({result['rating_stance']}"
                  + (", cut forced by the studio" if result["rating_cut_forced"] else "") + ")")
            if result["marketing_push_requested"]:
                print(f"        Marketing push: {'honored' if result['marketing_push_honored'] else 'ignored'}")

            if session.awards_campaign_available():
                outcome = session.run_awards_campaign(spend_millions=2.0)
                if outcome["won"]:
                    awards_won += 1
                    print("        AWARDS: won.")
                elif outcome["nominated"]:
                    awards_nominated += 1
                    print("        AWARDS: nominated, did not win.")
                else:
                    print("        AWARDS: campaign run, no nomination.")
        else:
            declined_years += 1
            print("  -> No offer worth taking this year (weak fit or nothing real on the board) — declining the board.")
            declined = session.decline_board()
            for d in declined:
                print(f"      passed on a {d['genre']} film: {d['roi_band']}, {d['critic_band']} reviews (someone else made it)")
            log: list[str] = []
            _spend_actor_quarters(session, log)
            for line in log:
                print(line)

        # ================= DIRECTING =================
        offer = session.check_for_hire_offer()
        if offer is not None:
            hire_offers_seen += 1
            standing_word = session.director_status()["standing"]
            worth_it = standing_word in ("working", "in-demand", "sought-after", "a star")
            print(f"\n  HIRE OFFER: {offer['studio_name']} wants a {offer['genre']} picture at ${offer['budget_millions']:.0f}M — "
                  f"{'accepting' if worth_it else 'declining (not worth the loss of creative control yet)'}")
            if worth_it:
                hire_offers_accepted += 1
                offer_genre = offer["genre"]
                result = session.accept_hire_offer()
                if result["greenlit"]:
                    films_directed.append({**result, "via": "hire", "genre": offer_genre})
                for e in result.get("limbo_events", []):
                    limbo_kind_counts[e["kind"]] = limbo_kind_counts.get(e["kind"], 0) + 1
            else:
                session.decline_hire_offer()

        quarter_n = 0
        while session.quarters_remaining_this_year() > 0:
            quarter_n += 1
            status = session.director_status()
            for s in status["projects"]:
                if s["momentum_band"] == "dead":
                    session.scrap_directing_project(s["index"])
                    scrapped_projects += 1
                    print(f"\n  DIRECTING Q{quarter_n}: scrapped a dead {s['genre']} project (${s['budget_ask']:.0f}M, "
                          f"{s['quarters_in_dev']} quarters sunk)")
                    status = session.director_status()
                    break

            if status["can_start_new_project"]:
                genre = ["drama", "thriller", "horror", "comedy", "scifi", "action", "period", "romance", "musical", "family"][tick % 10]
                tier = "micro" if status["standing"] in ("unknown", "working") else "low"
                if session.start_directing_project(genre, tier):
                    new = session.director_status()["projects"][-1]
                    session.choose_director_casting_action(new["index"], casting.YOUR_ROSTER)
                    session.choose_director_shoot_style_action(new["index"], shoot_style.HEAVY_COVERAGE)
                    session.choose_director_script_note_action(new["index"], "whole_film")
                    session.request_director_release_strategy(new["index"], "limited")
                    session.request_director_marketing_push_action(new["index"])
                    print(f"\n  DIRECTING Q{quarter_n}: pitched a new {genre} project (${new['budget_ask']:.0f}M) — "
                          f"your roster casting, heavy coverage, pushing for the whole film")
                    status = session.director_status()

            if not status["projects"]:
                continue

            best_project = max(status["projects"], key=lambda s: MOMENTUM_RANK.get(s["momentum_band"], 0))
            project_index = best_project["index"]

            # rewrite dominates the mix — the one real lever on true script quality — mixed with
            # just enough momentum-building to keep the package from flatlining.
            action = "rewrite" if tick % 3 != 0 else "attach_star"
            tick += 1
            if action == "attach_star":
                opts = session.attach_star_target_options()
                session.choose_attach_star_target(opts[tick % len(opts)]["id"], "genre_fit")
            result = session.advance_directing(project_index, action)
            for e in result.get("limbo_events", []):
                limbo_kind_counts[e["kind"]] = limbo_kind_counts.get(e["kind"], 0) + 1
                print(f"  DIRECTING Q{quarter_n}: LIMBO — {e['genre']} (${e['budget_millions']:.0f}M): {e['kind']}"
                      + (f", cost ${e['cost_paid']:.1f}M" if e.get("cost_paid") else ""))
            print(f"  DIRECTING Q{quarter_n}: worked {best_project['genre']} (${best_project['budget_ask']:.0f}M) "
                  f"with '{action}' — momentum now {result['momentum_band']}")
            if result["greenlit"]:
                films_directed.append({**result, "via": "own", "genre": best_project["genre"]})
                print(f"    >>> GREENLIT: ${result['budget_millions']:.1f}M production, {result['rating_band']}, "
                      f"critics {result['critic_band']} ({result['critic_score']}), audience {result['audience_band']}, "
                      f"{result['roi_band']} (ROI {result['roi']:.2f}x), ${result['gross_millions']:.1f}M gross, "
                      f"{result['release_label']}")
            elif result["dead"]:
                dead_projects += 1
                print("    >>> project died in development")

            if session.platform_expansion_available():
                outcome = session.request_platform_expansion()
                if outcome["granted"]:
                    print(f"    Platform expansion: granted — {outcome['studio_name']} (+${outcome['extra_gross_millions']:.1f}M gross)")
                else:
                    print(f"    Platform expansion: {outcome['studio_name']} passed")

        net_worth_trace.append(round(session.state.life.money.net_worth, 1))
        actor_standing_trace.append(round(session.state.actor.standing.weighted_score({"heat": 0.45, "prestige": 0.25, "affection": 0.30, "notoriety": -0.20}), 1))
        director_standing_trace.append(round(session.state.director.standing.weighted_score({"heat": 0.45, "prestige": 0.25, "affection": 0.30, "notoriety": -0.20}), 1))

        rels = session.rolodex_summary()
        print(f"\n  Net worth: ${session.state.life.money.net_worth:,.1f}M  ·  "
              f"Actor Standing score {actor_standing_trace[-1]}  ·  Director Standing score {director_standing_trace[-1]}")
        print(f"  Rolodex ({len(rels)}): " + ", ".join(f"{n['id']}({n['relationship']})" for n in rels[:6]) + (" ..." if len(rels) > 6 else ""))

        session.end_year()
        if session.is_over():
            print("\n  Career over.")
            break

    # ================= FINAL REPORT =================
    print(f"\n\n{'#'*90}\nFINAL CAREER REPORT — seed {seed}\n{'#'*90}\n")
    print(f"Age at end: {session.age()}")
    print(f"Years worked as actor: {years - declined_years} of {min(years, session.age() - 18 if session.age() > 18 else years)}  ·  years declined: {declined_years}")
    d = session.director_status()
    print(f"Acting credits: {len(films_acted)}  ·  Directing credits: {d['credits']}")
    print(f"Agent tier: {session.leverage_status()['agent_tier']}  ·  Director Standing: {d['standing']}")
    print(f"Awards: {awards_won} won, {awards_nominated} nominated (of films that qualified for a campaign)")
    print(f"Directing: {dead_projects} died in development, {scrapped_projects} scrapped, "
          f"{hire_offers_accepted}/{hire_offers_seen} hire offers accepted")
    if limbo_kind_counts:
        print("Limbo outcomes across the whole career:")
        for kind, n in sorted(limbo_kind_counts.items(), key=lambda kv: -kv[1]):
            print(f"  {kind}: {n}")
    print(f"Final net worth: ${session.state.life.money.net_worth:,.1f}M")
    print()

    if films_acted:
        print(f"--- FULL ACTING FILMOGRAPHY ({len(films_acted)}) ---")
        header = (f"  {'Genre':<9} {'Billing':<11} {'Studio':<20} {'Budget':>8} {'Mktg':>7} {'Gross':>8} {'ROI':>6}  "
                  f"{'Rated':<6} {'Critics':<8} {'Audience':<12} {'Release':<10}")
        print(header)
        for f in films_acted:
            money = f.get("gross_millions", f.get("license_value_millions", 0.0))
            release = f.get("release_label", f"season, {f.get('n_episodes')} ep").split(" —")[0]
            print(f"  {f['genre']:<9} {f['billing']:<11} {f['studio']:<20} ${f['budget_millions']:>6.1f}M "
                  f"${f['marketing_millions']:>5.1f}M ${money:>6.1f}M {f['roi']:>5.2f}x  "
                  f"{f['rating_band']:<6} {f['critic_band']:<8} {f['audience_band']:<12} {release:<10}")
        total_gross = sum(f.get("gross_millions", f.get("license_value_millions", 0.0)) for f in films_acted)
        total_budget = sum(f["budget_millions"] for f in films_acted)
        print(f"  Totals — ${total_budget:,.1f}M budget, ${total_gross:,.1f}M gross, "
              f"{total_gross/total_budget:.2f}x combined ROI" if total_budget else "")
        avg_critic = sum(f["critic_score"] for f in films_acted) / len(films_acted)
        print(f"  Average critic score: {avg_critic:.1f}")
        print()

    if films_directed:
        print(f"--- FULL DIRECTING FILMOGRAPHY ({len(films_directed)}) ---")
        header = f"  {'Genre':<9} {'Via':<5} {'Budget':>8} {'ROI':>6}  {'Rated':<6} {'Critics':<8} {'Audience':<12}"
        print(header)
        for f in films_directed:
            print(f"  {f['genre']:<9} {f['via']:<5} ${f['budget_millions']:>6.1f}M {f['roi']:>5.2f}x  "
                  f"{f['rating_band']:<6} {f['critic_band']:<8} {f['audience_band']:<12}")
        avg_critic_d = sum(f["critic_score"] for f in films_directed) / len(films_directed)
        print(f"  Average critic score: {avg_critic_d:.1f}")
        print()

    print("--- STANDING TRACES (weighted score, every year) ---")
    print("  Actor:    " + " ".join(str(v) for v in actor_standing_trace))
    print("  Director: " + " ".join(str(v) for v in director_standing_trace))
    print()
    print("--- NET WORTH TRACE (every year, $M) ---")
    print("  " + " ".join(str(v) for v in net_worth_trace))
    print()

    print("--- FINAL STANDING (raw meters) ---")
    sa = session.state.actor.standing
    sd = session.state.director.standing
    print(f"  Actor    — Heat {sa['heat']:.1f}  Prestige {sa['prestige']:.1f}  Affection {sa['affection']:.1f}  Notoriety {sa['notoriety']:.1f}")
    print(f"  Director — Heat {sd['heat']:.1f}  Prestige {sd['prestige']:.1f}  Affection {sd['affection']:.1f}  Notoriety {sd['notoriety']:.1f}")
    print()

    print("--- STUDIO RELATIONSHIPS ---")
    for r in session.studio_relations_status():
        print(f"  {r['studio_name']} — {r['projects_together']} film(s), {r['trust_band']}, net P&L ${r['net_profit_millions']:.1f}M")

    print("\n--- DIRECTOR RELATIONSHIPS ---")
    for r in session.director_relationship_status():
        print(f"  {r['id']} — {r['projects_together']} film(s), {r['trust_band']}, net P&L ${r['net_profit_millions']:.1f}M")

    print("\n--- ROLODEX (final state) ---")
    for n in session.rolodex_summary():
        print(f"  {n['id']} ({n['type']}) — {n['relationship']}")

    franchises = session.franchise_status()
    if franchises:
        print("\n--- FRANCHISES ---")
        for f in franchises:
            print(f"  {f['genre'].title()} ({f['studio_name']}) — {f['installments']} installment(s), "
                  f"indispensability {f['indispensability']}, recast cost ${f['recast_cost_millions']}M")

    print("\n--- OBITUARY ---")
    ob = session.obituary_summary()
    print(f"  {ob['credits']} credited roles played.")
    print(f"  {len(ob['declined'])} roles turned down (sample):")
    for d in ob["declined"][:8]:
        print(f"    - a {d['genre']} film passed on: {d['roi_band']}, {d['critic_band']} reviews")
    print(f"  {ob['kept']} relationships kept, {ob['lost']} lost.")
    if ob.get("best_hidden_performance"):
        bhp = ob["best_hidden_performance"]
        print(f"  Best hidden performance: a {bhp['genre']} film — {bhp['band']}")


if __name__ == "__main__":
    import sys
    run(int(sys.argv[1]) if len(sys.argv) > 1 else 40)
