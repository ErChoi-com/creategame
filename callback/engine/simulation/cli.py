#!/usr/bin/env python3
"""A terminal-playable prototype following design/ux/'s exact screen flow: character creation
(ux/01), the hub (ux/02), and the season loop (ux/03) — Offer Board -> the Deal -> Prep -> the
Shoot -> Post & Release -> the Reckoning -> the pull menu (Rolodex/Leverage/Trades, ux/04).

This file imports exactly one thing from the engine: simulation.session.Session. Every hidden
number it shows the player is already a plain string or number Session handed it — no formula,
dataclass, or internal constant from actor/, rolodex/, leverage/, life/, or world/ appears here.
That boundary is the point: a UI only ever needs to know what Session's methods return, never how.

    python3 -m callback.engine.simulation.cli            # interactive
    python3 -m callback.engine.simulation.cli --auto      # self-playing demo, no input needed
"""
from __future__ import annotations

import sys

from callback.engine.simulation.session import QUARTERS_PER_YEAR, Session


def prompt(msg: str, auto_default: str, auto: bool) -> str:
    if auto:
        print(f"{msg} -> {auto_default}")
        return auto_default
    try:
        val = input(f"{msg} ").strip()
    except EOFError:
        return auto_default
    return val or auto_default


def choose(options: list[tuple[str, str]], msg: str, auto_default_index: int, auto: bool) -> str:
    for i, (_, label) in enumerate(options, 1):
        print(f"    {i}. {label}")
    default = str(auto_default_index + 1)
    pick = prompt(msg, default, auto)
    idx = int(pick) - 1 if pick.isdigit() and 1 <= int(pick) <= len(options) else auto_default_index
    return options[idx][0]


def character_creation(session: Session, auto: bool) -> None:
    print("\nYou do not control whether the film is good.\n")
    print("BACKGROUND")
    bg_options = [(k, f"{name} — {tagline}") for k, name, tagline in session.background_options()]
    bg_key = choose(bg_options, "Choose:", 0, auto)

    print("\nAMBITION — this decides what your obituary measures you against; it gates nothing.")
    amb_key = choose(session.ambition_options(), "Choose:", 0, auto)

    print(f"\n{session.start(bg_key, amb_key)}\n")


def _franchise_tag(o: dict) -> str:
    n = o.get("installment_number", 0)
    if n >= 2:
        return f"  [SEQUEL — Part {n}]"
    if n == 1:
        return "  [NEW FRANCHISE]"
    return ""


def _genre_label(o: dict) -> str:
    """design/part-09 §9.2 — a hybrid listing reads as "Sci-fi Horror," not just its primary
    genre; a plain listing (secondary_genre absent or None, every non-hybrid caller/test fixture)
    is unaffected."""
    secondary = o.get("secondary_genre")
    if secondary:
        return f"{o['genre'].title()}-{secondary.title()}"
    return o["genre"].title()


def _listing_tags(o: dict) -> str:
    tag = _franchise_tag(o)
    if o.get("source_material"):
        pop = o.get("source_material_popularity")
        pop_tag = f", {pop}" if pop else ""
        tag += f"  [ADAPTED FROM A {o['source_material'].replace('_', ' ').upper()}{pop_tag}]"
    if o.get("guaranteed"):
        tag += "  [GUARANTEED — your deal/spin-off]"
    return tag


def _print_listings(listings: list[dict]) -> None:
    for o in listings:
        state = "" if o["available"] else "  (an audition — but it doesn't come through this year)"
        fee = f"  (your fee: ${o['fee_millions']:.2f}M)" if "fee_millions" in o else ""
        print(f"  [{o['index'] + 1}] {_genre_label(o)} · {o['billing']} · ${o['budget_millions']:.2f}M film{fee} — "
              f"{o['studio_name']}{_listing_tags(o)}{state}")
        print(f"       {o['studio_tagline']}")
        # §4.4 v17 — the offer board's own new signals: real, but never a raw number.
        director = o.get("director") or {"known": False}
        director_line = (
            f"director: {director['id']} ({director['relationship']})" if director["known"]
            else "director: unfamiliar"
        )
        franchise_scale = o.get("franchise_scale")
        franchise_tag = f"  ·  {franchise_scale}" if franchise_scale and franchise_scale != "not a franchise" else ""
        print(f"       demand: {o.get('demand_band', '?')}  ·  buzz: {o.get('buzz_band', '?')}  ·  {director_line}{franchise_tag}")


OFFER_BOARD_HARD_CAP = 200  # a safety valve, not a design cap — see generate_more_listings()


def offer_board_screen(session: Session, auto: bool) -> int | None:
    listings = session.offer_board()
    print(f"\n--- THIS YEAR'S OFFER BOARD ({len(listings)} listings) ---")
    _print_listings(listings)

    while True:
        available = [o for o in listings if o["available"]]
        can_keep_looking = len(listings) < OFFER_BOARD_HARD_CAP
        options = [(str(o["index"]), f"{_genre_label(o)} ({o['billing']}, {o['budget_millions']:.2f}M) — "
                                      f"{o['studio_name']}{_listing_tags(o)}")
                   for o in available]
        if can_keep_looking:
            options.append(("__more__", "Keep looking — generate more listings"))
        options.append(("__skip__", "Pass on everything this year"))
        options.append(("__director__", "Click on a director for more on them"))
        # default to "keep looking" if nothing's on yet and there's still room to look
        default_index = 0 if (available or not can_keep_looking) else len(options) - 3
        pick = choose(options, "  [A]udition/accept which one, keep looking, or skip?", default_index, auto)

        if pick == "__director__":
            npc_id = prompt("  Whose id? (see 'director: <id>' on a listing)", "", auto)
            if npc_id:
                info = session.director_info(npc_id)
                if not info["known"]:
                    print("    You don't know enough about them yet.")
                else:
                    print(f"    {info['id']} — {info['relationship']}, {info['trust_band']}, "
                          f"{info['projects_together']} project(s) together, net P&L ${info['net_profit_millions']:.1f}M")
            continue
        if pick == "__more__":
            more = session.generate_more_listings()
            print(f"\n  ({len(more)} more listings)")
            _print_listings(more)
            listings = listings + more
            continue
        if pick == "__skip__":
            if not available:
                print("  Nothing on the board came through this year.")
            return None
        return int(pick)


def franchise_screen(session: Session, auto: bool) -> bool:
    """Only reachable right after accept()-ing a sequel to a franchise you've built real
    Indispensability in. Returns False if a failed holdout got the part recast out from under
    you — the project doesn't happen this year — True otherwise (including "never came up")."""
    if not session.holdout_available():
        return True
    choice = prompt("  You're indispensable to this franchise now — hold out for more money? [Y]/[N]", "N", auto)
    if choice.upper() != "Y":
        return True
    result = session.request_holdout()
    if result["paid"]:
        print(f"    They paid — your fee just went up {result['raise_multiplier']}x.")
    elif result["recast"]:
        print("    They called your bluff and recast the part. You're out of the franchise.")
    else:
        print("    They didn't budge, but you're still in — proceeding at the original terms.")
    return result["proceeds"]


def _negotiate_bonus_type(session: Session, auto: bool) -> tuple[bool, str]:
    """§6.5 v21 — two real deal shapes, each with its own Standing bar. first_dollar_gross is
    rarer and needs more weight than net_points; a player who clears both gets an actual choice."""
    net_ok = session.box_office_bonus_available("net_points")
    gross_ok = session.box_office_bonus_available("first_dollar_gross")
    if not net_ok and not gross_ok:
        return False, "net_points"
    options = []
    if gross_ok:
        options.append(("first_dollar_gross", "First-dollar gross — paid from dollar one, regardless of profit"))
    if net_ok:
        options.append(("net_points", "Net points — a real share of actual profit, only once the studio's whole"))
    options.append(("none", "No bonus — just the fee"))
    bonus_type = prompt(
        "  THE DEAL: you've got the weight for a real backend point. "
        + "  ".join(f"[{i+1}] {label}" for i, (_, label) in enumerate(options)),
        "3" if len(options) == 3 else "2", auto,
    )
    idx = int(bonus_type) - 1 if bonus_type.isdigit() and 1 <= int(bonus_type) <= len(options) else len(options) - 1
    key = options[idx][0]
    return key != "none", key if key != "none" else "net_points"


def deal_screen(session: Session, auto: bool) -> None:
    want_bonus, bonus_type = _negotiate_bonus_type(session, auto)

    if not session.approvals_available():
        print("  THE DEAL: standard terms — you're not there yet for approvals.")
        session.choose_deal(False, want_box_office_bonus=want_bonus, bonus_type=bonus_type)
        if want_bonus:
            print(f"    (Box office bonus negotiated — {bonus_type.replace('_', ' ')}.)")
        return
    choice = prompt("  THE DEAL: [1] Take the money  [2] Take less, get more say (script + co-star approval)", "1", auto)
    fee = session.choose_deal(choice == "2", want_box_office_bonus=want_bonus, bonus_type=bonus_type)
    if fee is not None:
        print(f"    (Fee cut to {fee:.2f}M — script and co-star approval, yours now.)")
    if want_bonus:
        print(f"    (Box office bonus negotiated — {bonus_type.replace('_', ' ')}.)")


def marketing_push_screen(session: Session, auto: bool) -> None:
    choice = prompt("  Lobby the studio for a bigger marketing campaign on this one? [Y]/[N]", "N", auto)
    if choice.upper() == "Y":
        session.request_marketing_push()


def multi_picture_deal_screen(session: Session, auto: bool) -> None:
    """Future terms, not just this project's — offered right after accepting a role, once
    standing clears the bar. Once signed, this studio owes a guaranteed listing every year until
    it's worked off (see Session._guaranteed_listing)."""
    if not session.multi_picture_deal_available():
        return
    choice = prompt(
        "  FUTURE TERMS: this studio would lock in several films with you right now, at a premium "
        "over your quote — take it? [Y]/[N]", "N", auto,
    )
    if choice.upper() != "Y":
        return
    terms = session.multi_picture_deal_terms(3)
    print(f"    Preview: {terms['films']} films with {terms['studio_name']} at "
          f"${terms['per_film_budget_millions']:.1f}M each (${terms['total_value_millions']:.1f}M total).")
    confirm = prompt("    Sign it? [Y]/[N]", "Y", auto)
    if confirm.upper() == "Y":
        result = session.sign_multi_picture_deal(3)
        print(f"    Signed — {result['films']} films guaranteed with {result['studio_name']}.")


def script_notes_screen(session: Session, auto: bool) -> None:
    if not session.script_notes_available():
        return
    key = choose(session.script_note_options(), "  SCRIPT NOTES — you earned a say. Choose:", 0, auto)
    session.choose_script_note(key)


def director_screen(session: Session, auto: bool) -> None:
    directors = session.available_directors()
    if not directors:
        return
    options = [("__none__", "Let them assign whoever")] + [
        (d["id"], f"{d['id']} ({d['relationship']}) — owes you {d['favour_balance']}, costs "
                  f"{session.DIRECTOR_REQUEST_FAVOUR_COST}"
                  + (f", {d['trust']['trust_band']} ({d['trust']['projects_together']} film(s) together)" if d["trust"] else ""))
        for d in directors
    ]
    key = choose(options, "  WHO'S DIRECTING — call in a favour to request someone specific:", 0, auto)
    if key != "__none__":
        print(f"    {session.request_director(key)}")


def costar_screen(session: Session, auto: bool) -> None:
    costars = session.costar_options()
    if not costars:
        return
    options = [("__none__", "No one worth centring on this time")] + [
        (c["id"], f"{c['id']} ({c['relationship']})") for c in costars
    ]
    costar_key = choose(options, "  SCENE PARTNER — who are you playing off of?", 0, auto)
    if costar_key == "__none__":
        session.choose_orientation(None, "neutral")
        return
    orientation_key = choose(session.orientation_options(), "  How do you play it toward them?", 0, auto)
    session.choose_orientation(costar_key, orientation_key)


def prep_screen(session: Session, auto: bool) -> None:
    print("  PREP:")
    key = choose(session.prep_options(), "  Choose:", 0, auto)
    session.choose_prep(key)


def shoot_screen(session: Session, auto: bool) -> None:
    positions = session.position_options()
    for episode_label in session.episode_labels():
        header = f"  THE SHOOT — {episode_label.upper()}, three scenes." if episode_label else "  THE SHOOT — three scenes."
        print(header)
        for scene_name in session.scene_names():
            print(f"    Scene — {scene_name}:")
            choices = {}
            for dial_key, dial_label in session.dial_options():
                options_str = "/".join(f"[{i+1}]{label}" for i, (_, label) in enumerate(positions))
                pick = prompt(f"      {dial_label}: {options_str}", "1", auto)
                idx = int(pick) - 1 if pick.isdigit() and 1 <= int(pick) <= len(positions) else 0
                choices[dial_key] = positions[idx][0]
            session.play_scene(choices)


def rating_screen(session: Session, auto: bool) -> None:
    """§5.19 — only a real decision on a genuine borderline film; the studio's own preference
    (a forced cut, or real pressure toward one) is resolved silently inside choose_release() and
    reported on the Post & Release screen, not asked here."""
    preview = session.rating_preview()
    if not preview["cut_available"]:
        return
    print(f"  RATING — this one's landing right on the line ({preview['band']}).")
    key = choose(session.rating_cut_options(), "  Choose:", 1, auto)
    session.choose_rating_stance(key)


def release_screen(session: Session, auto: bool) -> dict:
    # It's a request, not a choice — the studio has the final say (see choose_release's docstring).
    print("  RELEASE STRATEGY — your request to the studio:")
    key = choose(session.release_options(), "  Ask for:", 0, auto)

    def pick_bid(bids):
        # Only invoked once the studio's actual decision turns out to be "streaming" — resolved
        # after the film is actually made, so quality already decided who showed up to bid.
        print("  STREAMING RIGHTS — the finished film draws its own offers:")
        options = [
            (str(i), (f"{b.studio_name} — puts it up for nothing, you just get your budget back"
                       if b.self_distribute else
                       f"{b.studio_name} — ${b.payout_millions:.1f}M ({b.multiplier}x budget)"))
            for i, b in enumerate(bids)
        ]
        if len(bids) == 1:
            print(f"    Nobody else bit — {bids[0].studio_name} is the only offer on the table.")
        best_index = max(range(len(bids)), key=lambda i: bids[i].payout_millions)
        pick = choose(options, "  Sell to:", best_index, auto)
        return bids[int(pick)]

    def pick_festival_bid(bids):
        # Only invoked once the submission actually clears the acquisition gate — resolved after
        # the single "all reviews land at once" premiere reveal, so quality already decided who
        # showed up to bid, and whether anyone did at all.
        print("  FESTIVAL ACQUISITION — the finished film draws its own offers:")
        options = [
            (str(i), (f"{b.studio_name} — keep it and release it yourselves: ${b.payout_millions:.1f}M "
                       "(the real box office, not a guarantee)"
                       if b.self_release else
                       f"{b.studio_name} buys distribution rights — ${b.payout_millions:.1f}M ({b.multiplier}x budget)"))
            for i, b in enumerate(bids)
        ]
        if len(bids) == 1:
            print(f"    Nobody else bit — {bids[0].studio_name} is the only option.")
        best_index = max(range(len(bids)), key=lambda i: bids[i].payout_millions)
        pick = choose(options, "  Sell to:", best_index, auto)
        return bids[int(pick)]

    summary = session.choose_release(key, streaming_bid_selector=pick_bid, festival_bid_selector=pick_festival_bid)
    if summary["studio_overruled"]:
        print(f"    (You asked for {summary['requested_release']} — the studio went with "
              f"{summary['release_label']} instead.)")
    return summary


DIRECTOR_NOTE_LABELS = {
    "clarity": "the director pushed for clarity",
    "ambiguity": "the director pushed for ambiguity",
    "whole_film": "the director pushed for the whole film",
}


def post_release_screen(summary: dict) -> None:
    print("  --- POST & RELEASE ---")
    print(f"    {summary['studio_name']}")
    note_label = DIRECTOR_NOTE_LABELS.get(summary.get("director_note_choice", ""))
    if note_label:
        print(f"    Notes: {note_label} — it's their film to call, whatever you pushed for on top.")
    print(f"    Your work: {summary['performance_band']}")
    print(f"    Critics: {summary['critic_band']} ({summary['critic_score']}/100)")
    print(f"    Audience: {summary['audience_band']}")
    print(f"    Release: {summary['release_label']}")
    if summary.get("rating_band"):
        rating_note = ""
        if summary.get("rating_cut_forced"):
            rating_note = " — the studio forced a cut for it"
        elif summary.get("rating_studio_pressure"):
            rating_note = " — you held the line against the studio's own push for a cut"
        print(f"    Rated: {summary['rating_band']}{rating_note}")
    if summary["franchise_installment"] >= 2:
        print(f"    Franchise: installment #{summary['franchise_installment']}")
    elif summary["franchise_installment"] == 1:
        print("    Franchise: the first installment — a new one, starting here")
    print(f"    Production budget: ${summary['budget_millions']:.1f}M  ·  "
          f"Marketing: ${summary['marketing_millions']:.1f}M")
    if summary["marketing_push_requested"]:
        print(f"    (Your lobbying for a bigger campaign was "
              f"{'honored' if summary['marketing_push_honored'] else 'ignored'}.)")
    if summary["gross_millions"] <= 0:
        print(f"    Box office: {summary['roi_band']} — never really had one.")
        return
    print(f"    Box office: {summary['roi_band']} — ${summary['gross_millions']:.1f}M gross "
          f"(ROI {summary['roi']:.2f}x)")
    if summary["weekly_gross"]:
        weeks_str = "  ".join(f"Wk{i+1} ${w:.1f}M" for i, w in enumerate(summary["weekly_gross"]))
        print(f"      {weeks_str}")
    if summary.get("box_office_bonus_millions"):
        type_tag = f" ({summary['box_office_bonus_type'].replace('_', ' ')} at {summary['box_office_bonus_share_pct']:.2f}%)" \
            if summary.get("box_office_bonus_type") else ""
        print(f"    Your negotiated bonus{type_tag}: ${summary['box_office_bonus_millions']:.2f}M")


AWARD_CATEGORY_LABELS = {
    "lead_drama": "Lead Performance — Drama",
    "lead_comedy": "Lead Performance — Musical/Comedy",
    "supporting": "Supporting Performance",
    "ensemble": "Ensemble Cast",
    "breakthrough": "Breakthrough Performance",
    "genre_excellence": "Genre Excellence (Sci-Fi/Fantasy/Horror/Action)",
    "voice_performance": "Voice Performance (Animation)",
}


def awards_screen(session: Session, auto: bool) -> None:
    if not session.awards_campaign_available():
        return
    categories = session.available_award_categories()
    if not categories:
        return
    choice = prompt("  That work was noticed. Run an awards campaign? [Y]es/[N]o", "Y", auto)
    if choice.upper() != "Y":
        return
    category = choose(
        [(c, AWARD_CATEGORY_LABELS[c]) for c in categories], "    Which category?", 0, auto,
    )
    fraud_available = category == "supporting"
    attempt_fraud = False
    if fraud_available:
        fraud_choice = prompt(
            "    Campaign it as Supporting when it's really a lead performance — better odds, "
            "real risk if caught? [Y]es/[N]o",
            "N", auto,
        )
        attempt_fraud = fraud_choice.upper() == "Y"
    outcome = session.run_awards_campaign(category, attempt_category_fraud=attempt_fraud)
    if outcome["category_fraud_attempted"]:
        if outcome["category_fraud_caught"]:
            print("    The category play got noticed. It's a story now, not just a campaign.")
        else:
            print("    Nobody called it out.")
    if outcome["won"]:
        print(f"    You won — {AWARD_CATEGORY_LABELS[category]}.")
    elif outcome["nominated"]:
        print(f"    Nominated for {AWARD_CATEGORY_LABELS[category]}. Didn't win.")
    else:
        print("    No nomination this time.")


def director_awards_screen(session: Session, auto: bool) -> None:
    if not session.director_awards_campaign_available():
        return
    choice = prompt("  The film was noticed. Run an awards campaign? [Y]es/[N]o", "Y", auto)
    if choice.upper() != "Y":
        return
    outcome = session.run_director_awards_campaign()
    if outcome["won"]:
        print("    You won — Director.")
    elif outcome["nominated"]:
        print("    Nominated for Director. Didn't win.")
    else:
        print("    No nomination this time.")


def pull_menu(session: Session, auto: bool) -> None:
    """The one screen the player never has to open — ux/04's whole point. Auto mode always
    skips it; an interactive player can check the Rolodex or Leverage between offers for free."""
    if auto:
        return
    choice = prompt("\n[Enter] to see this year's offer, or [p] to check the Rolodex/Leverage:", "", auto)
    if choice.lower() != "p":
        return

    print(f"\n  This year's free quarters (Rolodex/Leverage): {session.actor_quarters_remaining_this_year()}/{QUARTERS_PER_YEAR}"
          f" — accepting a role spends the rest of them at once.")

    print("\n  ROLODEX")
    for npc in session.rolodex_summary():
        print(f"    {npc['id']} ({npc['type']}) — {npc['relationship']}")
    npc_choice = prompt("  Check in with someone? Enter their id, or blank to skip:", "", auto)
    if npc_choice:
        print(f"    {session.interact(npc_choice, 'check_in')}")

    status = session.leverage_status()
    print(f"\n  LEVERAGE — agent tier: {status['agent_tier']}, scarcity: {status['scarcity']}")
    if status["next_tier"]:
        lev_choice = prompt(f"  Try to sign with a {status['next_tier']} agency? [Y]/[N]", "N", auto)
        if lev_choice.upper() == "Y":
            print(f"    {session.try_advance_agent_tier()}")

    franchises = session.franchise_status()
    if franchises:
        print("\n  FRANCHISES")
        for f in franchises:
            print(f"    {f['genre'].title()} ({f['studio_name']}) — {f['installments']} installment(s), "
                  f"indispensability {f['indispensability']}, recast cost ${f['recast_cost_millions']}M")

    spinoffs = session.spinoff_options()
    if spinoffs:
        print("\n  SPIN-OFF POTENTIAL")
        for sp in spinoffs:
            print(f"    {sp['genre'].title()} ({sp['studio_name']}) — indispensability {sp['indispensability']}")
        choice = prompt("  Pitch a spin-off? Enter the franchise's genre, or blank to skip:", "", auto)
        match = next((sp for sp in spinoffs if sp["genre"] == choice), None)
        if match:
            print(f"    {session.launch_spinoff(match['franchise_id'])}")

    if session.is_directing() and session.platform_expansion_available():
        print("\n  PLATFORM EXPANSION — your last Limited/Festival release earned real notice.")
        expand_choice = prompt("  Push the studio for a wider release? [Y]/[N]", "N", auto)
        if expand_choice.upper() == "Y":
            outcome = session.request_platform_expansion()
            if outcome["granted"]:
                print(f"    {outcome['studio_name']} said yes — an extra ${outcome['extra_gross_millions']:.1f}M gross "
                      f"(${outcome['extra_marketing_millions']:.1f}M more spent getting there).")
            else:
                print(f"    {outcome['studio_name']} passed. It stays where it is.")

    deal = session.multi_picture_deal_status()
    if deal:
        print(f"\n  FUTURE TERMS — {deal['films_remaining']} film(s) left with {deal['studio_name']} "
              f"at ${deal['guaranteed_budget_millions']:.1f}M each")
        break_choice = prompt("  Walk away from this deal early? [Y]/[N]", "N", auto)
        if break_choice.upper() == "Y":
            print(f"    {session.break_multi_picture_deal()}")

    studio_rels = session.studio_relations_status()
    if studio_rels:
        print("\n  STUDIO RELATIONSHIPS")
        for r in studio_rels:
            print(f"    {r['studio_name']} — {r['projects_together']} film(s) together, {r['trust_band']}, "
                  f"net P&L ${r['net_profit_millions']:.1f}M")

    director_rels = session.director_relationship_status()
    if director_rels:
        print("\n  DIRECTORS YOU'VE WORKED WITH")
        for r in director_rels:
            print(f"    {r['id']} — {r['projects_together']} film(s) together, {r['trust_band']}, "
                  f"net P&L ${r['net_profit_millions']:.1f}M")


def acting_block(session: Session, auto: bool) -> None:
    """One full acting turn — Offer Board through Post & Release. Does not advance the calendar
    (see Session.end_year(), called once per year by run())."""
    chosen_index = offer_board_screen(session, auto)

    if chosen_index is not None:
        session.accept(chosen_index)
        proceeds = franchise_screen(session, auto)
        if proceeds:
            deal_screen(session, auto)
            multi_picture_deal_screen(session, auto)
            marketing_push_screen(session, auto)
            script_notes_screen(session, auto)
            director_screen(session, auto)
            costar_screen(session, auto)
            prep_screen(session, auto)
            shoot_screen(session, auto)
            rating_screen(session, auto)
            summary = release_screen(session, auto)
            post_release_screen(summary)
            awards_screen(session, auto)
        else:
            print("    No project this year — the franchise moved on without you.")
    else:
        for result in session.decline_board():
            print(f"    A {result['genre']} film went to someone else: {result['roi_band']}, {result['critic_band']} reviews.")


def hire_offer_screen(session: Session, auto: bool) -> bool:
    """§7.13 v10 — a real, rare, pushed notification only when the roll actually lands. Returns
    True if the offer was accepted (the year's directing turn is already resolved in that case)."""
    offer = session.check_for_hire_offer()
    if offer is None:
        return False
    print(f"\n  A STUDIO CALLS — {offer['studio_name']} wants you for a {offer['genre']} picture, "
          f"${offer['budget_millions']:.0f}M.")
    choice = prompt("  Take it? Skips development hell, but they hold final cut by default. [Y]/[N]", "N", auto)
    if choice.upper() != "Y":
        session.decline_hire_offer()
        return False
    result = session.accept_hire_offer()
    _print_directing_result(result)
    return True


def attach_star_screen(session: Session, auto: bool) -> None:
    options = session.attach_star_target_options()
    labels = [(str(i), f"{o['label']} ({o['relationship']}, bankability ~{o['bankability']:.0f})") for i, o in enumerate(options)]
    idx = int(choose(labels, "  ATTACH SOMEONE — who are you going after?", 0, auto))
    type_key = choose(session.attach_star_type_options(), "  Why attach them?", 0, auto)
    session.choose_attach_star_target(options[idx]["id"], type_key)


def _print_limbo_events(events: list[dict]) -> None:
    """§7.4 v16 — a neglected (or actively-worked but flatlined) project crossing the limbo
    threshold resolves to one of several real outcomes; print whichever one actually happened."""
    for e in events:
        tag = f"{e['genre']} (${e['budget_millions']:.0f}M)"
        if e["kind"] == "fired":
            print(f"    LIMBO — {tag}: the studio pulled you off it and kept going without you.")
        elif e["kind"] == "canceled":
            print(f"    LIMBO — {tag}: the studio just killed it. Nobody makes this one.")
        elif e["kind"] == "handed_free":
            print(f"    LIMBO — {tag}: the studio let it go for nothing. It's entirely yours now.")
        elif e["kind"] == "buyout_paid":
            print(f"    LIMBO — {tag}: bought it out for ${e['cost_paid']:.1f}M — it's yours now.")
        elif e["kind"] == "could_not_afford":
            print(f"    LIMBO — {tag}: the studio wanted ${e['buyout_offered']:.1f}M for it and you "
                  f"didn't have it. Gone.")


def _print_directing_result(result: dict) -> None:
    _print_limbo_events(result.get("limbo_events", []))
    if result.get("attachment_offer_accepted") is not None:
        print(f"    {'They said yes — attached.' if result['attachment_offer_accepted'] else 'They passed on it.'}")
    if result.get("dropped_attachments"):
        who = ", ".join(result["dropped_attachments"])
        print(f"    Lost the attachment: {who} — it took too long, and they had somewhere else to be.")
    if "self_finance_acquired" in result:
        if result["self_finance_acquired"]:
            if result["self_finance_released_free"]:
                print("    The studio let the project go — it's entirely yours now, no strings attached.")
            else:
                print(f"    Bought the studio out for ${result['self_finance_cost_paid']:.1f}M — "
                      f"it's your own money in it now, and your own call on everything from here.")
        elif result["self_finance_could_not_afford"]:
            print(f"    The studio wants ${result['self_finance_buyout_cost']:.1f}M for it and you don't "
                  f"have that kind of money — still theirs.")
    elif result["greenlit"]:
        print(f"    GREENLIT — ${result['budget_millions']:.1f}M production, "
              f"${result['marketing_millions']:.1f}M marketing. Rated {result['rating_band']}. "
              f"Critics {result['critic_band']} ({result['critic_score']}), audience {result['audience_band']}, "
              f"{result['roi_band']} (ROI {result['roi']:.2f}x), ${result['gross_millions']:.1f}M gross.")
        print(f"    Cast via: {result['casting_choice'].replace('_', ' ')}  ·  Shot: {result['shoot_style'].replace('_', ' ')}")
        print(f"    Release: {result['release_label']}"
              + (f" (you asked for {result['requested_release']} — overruled)" if result['release_overruled'] else ""))
        if result["marketing_push_requested"]:
            print(f"    (Your lobbying for a bigger campaign was "
                  f"{'honored' if result['marketing_push_honored'] else 'ignored'}.)")
        income = result.get("director_income_millions", 0.0)
        if result["self_financed"]:
            verb = "made" if income >= 0 else "lost"
            print(f"    Your own money, your own film — you {verb} ${abs(income):.1f}M in net proceeds after marketing.")
        elif income:
            bonus_type = result.get("box_office_bonus_type")
            bonus_note = f" (includes a negotiated {bonus_type.replace('_', ' ')} bonus)" if bonus_type else ""
            print(f"    Director's fee: ${income:.1f}M{bonus_note}.")
    elif result.get("blocked_on_money"):
        print(f"    Ready to shoot, but you're ${result['shortfall']:.1f}M short — can't self-finance this one yet.")
    elif result["dead"]:
        print("    The project died in development hell.")
    elif result["frozen"]:
        print("    Shelved in the drawer for now.")
    else:
        print(f"    Still in development — momentum: {result['momentum_band']}.")


def _maybe_pitch_new_project(session: Session, auto: bool, prompt_text: str, default: str = "N") -> None:
    status = session.director_status()
    if not status["can_start_new_project"]:
        return
    pitch_choice = prompt(
        f"{prompt_text} ({len(status['projects'])}/{status['max_projects']} in the slate) [Y]/[N]", default, auto,
    )
    if pitch_choice.upper() != "Y":
        return
    genre_key = choose(session.director_genre_options(), "  Pick a genre:", 0, auto)
    tier_key = choose(session.director_budget_tier_options(), "  Pick a budget tier:", 0, auto)
    indie_choice = prompt(
        "  Go fully independent — no studio ever involved, entirely your own money? "
        "Real trade: no development runway, the next thing you do resolves the film outright, "
        "and the whole budget comes out of your own pocket the moment it's made. [Y]/[N]", "N", auto,
    )
    self_financed = indie_choice.upper() == "Y"
    if session.start_directing_project(genre_key, tier_key, self_financed=self_financed):
        status = session.director_status()
        new = status["projects"][-1]
        tag = " — self-financed, no studio, ready to shoot on your next move" if self_financed else ""
        print(f"    In the slate: {new['genre']} · ${new['budget_ask']:.0f}M{tag}.")
        note_key = choose(session.director_script_note_options(), "  Your own notes pass on the script:", 0, auto)
        session.choose_director_script_note_action(new["index"], note_key)
        release_key = choose(session.director_release_options(), "  How do you want this one released, if it lands?", 0, auto)
        session.request_director_release_strategy(new["index"], release_key)
        push_choice = prompt("  Lobby the studio for a bigger marketing campaign, if it lands? [Y]/[N]", "N", auto)
        if push_choice.upper() == "Y":
            session.request_director_marketing_push_action(new["index"])
        cast_key = choose(session.director_casting_options(), "  Casting, if it lands:", 3, auto)
        session.choose_director_casting_action(new["index"], cast_key)
        style_key = choose(session.director_shoot_style_options(), "  Shooting style, if it lands:", 4, auto)
        session.choose_director_shoot_style_action(new["index"], style_key)


def _directing_quarter(session: Session, auto: bool) -> None:
    """One quarter's real directing action: pick which project in the slate gets it (or scrap a
    dead-weight one, or pitch a fresh one if there's room), then spend the action. §7.4 v16 —
    directing spends its action per quarter, not per year; this runs up to QUARTERS_PER_YEAR times
    from directing_block()."""
    status = session.director_status()
    if not status["projects"]:
        print("\n  Nothing in development — time to pitch something.")
        _maybe_pitch_new_project(session, auto, "  Pitch a project?", default="Y")
        status = session.director_status()
        if not status["projects"]:
            return
    else:
        print(f"\n  --- QUARTER {status['quarters_this_year'] + 1}/{status['quarters_per_year']} — THE SLATE ---")
        for s in status["projects"]:
            tag = " (in the drawer)" if s["frozen"] else ""
            print(f"    [{s['index']}] {s['genre']} · ${s['budget_ask']:.0f}M · momentum: {s['momentum_band']} · "
                  f"{s['quarters_in_dev']} quarter(s) in · {len(s['attachments'])} attached{tag}")
        scrap_choice = prompt(
            "  Scrap one of these before choosing? Enter its number, or [Enter] to skip:", "", auto,
        )
        if scrap_choice.strip().isdigit():
            session.scrap_directing_project(int(scrap_choice.strip()))
            status = session.director_status()
        _maybe_pitch_new_project(session, auto, "  Pitch another project on the side?")
        status = session.director_status()
        if not status["projects"]:
            return

    labels = [(str(s["index"]), f"{s['genre']} · ${s['budget_ask']:.0f}M · momentum: {s['momentum_band']}") for s in status["projects"]]
    project_index = int(choose(labels, "  Spend this quarter's action on:", 0, auto))

    action_key = choose(session.director_dev_action_options(), "  DEVELOPMENT HELL — this quarter's move:", 0, auto)
    if action_key == "attach_star":
        attach_star_screen(session, auto)
    result = session.advance_directing(project_index, action_key)
    _print_directing_result(result)


def directing_block(session: Session, auto: bool) -> None:
    """One full directing turn — up to QUARTERS_PER_YEAR real quarters of directing work this
    year, each spent on whichever project in the slate needs it most. Does not advance the calendar
    (see Session.end_year())."""
    if not session.is_directing():
        choice = prompt(
            "  Step behind the camera and direct your own film? [Y]/[N]", "Y", auto,
        )
        if choice.upper() != "Y":
            return
        print(f"    {session.become_director()}")

    status = session.director_status()
    print(f"\n  --- DIRECTING ({status['standing']}, {status['credits']} credit(s)) ---")

    while session.quarters_remaining_this_year() > 0:
        if hire_offer_screen(session, auto):
            continue  # a hire offer resolves its own quarter and moves straight to the next
        _directing_quarter(session, auto)
        if not auto:
            more = prompt("  Spend another quarter directing this year? [Y]/[N]",
                           "Y" if session.quarters_remaining_this_year() > 0 else "N", auto)
            if more.upper() != "Y":
                break
    director_awards_screen(session, auto)


def year_screen(session: Session, auto: bool) -> None:
    """This year's single work menu: acting and directing are each a clean either/or pick — you
    can't do both at once — but the menu loops, so you can do one block, then come back and do
    the other, both landing in the same year. Session.end_year() (called by run(), once) is what
    actually advances the calendar."""
    acted = False
    directed = False
    while True:
        options = []
        if not acted:
            options.append(("act", "Work on acting"))
        if session.directing_unlocked() and not directed:
            options.append(("direct", "Work on directing"))
        if not options:
            break
        options.append(("done", "That's it for this year"))
        # index 0 is always whatever's still available to pick (act, then direct, then done) —
        # auto mode naturally works through both blocks in order before ending the year.
        choice = choose(options, "  This year, work on:", 0, auto)

        if choice == "done":
            break
        if choice == "act":
            acting_block(session, auto)
            acted = True
        elif choice == "direct":
            directing_block(session, auto)
            directed = True


def run(auto: bool, seed: int, max_years: int) -> None:
    session = Session(seed=seed)
    character_creation(session, auto)

    for _ in range(max_years):
        if session.is_over():
            break
        print(f"\n=== AGE {session.age()} ===")
        pull_menu(session, auto)

        year_screen(session, auto)

        session.end_year()
        print(f"  RECKONING — you are {session.standing_summary()} now.")

        if session.age() % 5 == 0:
            print("  THE TRADES:")
            for line in session.trades():
                print(f"    - {line}")

        if not auto:
            cont = prompt("\n[Enter] to continue, [q] to end the run:", "", auto)
            if cont.lower() == "q":
                break

    print("\n=== THE OBITUARY ===")
    ob = session.obituary_summary()
    print(f"  {ob['credits']} credited roles played.")
    print(f"  {len(ob['declined'])} roles turned down — here's what became of them:")
    for d in ob["declined"][:5]:
        print(f"    - A {d['genre']} film you passed on: {d['roi_band']}, {d['critic_band']} reviews.")
    print(f"  {ob['kept']} relationships you kept. {ob['lost']} you lost.")
    if ob["best_hidden_performance"]:
        b = ob["best_hidden_performance"]
        print(f"  Your best hidden performance: a {b['genre']} film — {b['band']} work nobody quite noticed.")


def main() -> int:
    auto = "--auto" in sys.argv
    seed = 7
    for arg in sys.argv:
        if arg.startswith("--seed="):
            seed = int(arg.split("=", 1)[1])
    run(auto=auto, seed=seed, max_years=40)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
