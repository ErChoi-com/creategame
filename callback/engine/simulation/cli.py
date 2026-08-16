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

from callback.engine.simulation.session import Session


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


def _print_listings(listings: list[dict]) -> None:
    for o in listings:
        state = "" if o["available"] else "  (an audition — but it doesn't come through this year)"
        print(f"  [{o['index'] + 1}] {o['genre'].title()} · {o['billing']} · {o['budget_millions']:.2f}M — "
              f"{o['studio_name']}{_franchise_tag(o)}{state}")
        print(f"       {o['studio_tagline']}")


OFFER_BOARD_HARD_CAP = 200  # a safety valve, not a design cap — see generate_more_listings()


def offer_board_screen(session: Session, auto: bool) -> int | None:
    listings = session.offer_board()
    print(f"\n--- THIS YEAR'S OFFER BOARD ({len(listings)} listings) ---")
    _print_listings(listings)

    while True:
        available = [o for o in listings if o["available"]]
        can_keep_looking = len(listings) < OFFER_BOARD_HARD_CAP
        options = [(str(o["index"]), f"{o['genre'].title()} ({o['billing']}, {o['budget_millions']:.2f}M) — "
                                      f"{o['studio_name']}{_franchise_tag(o)}")
                   for o in available]
        if can_keep_looking:
            options.append(("__more__", "Keep looking — generate more listings"))
        options.append(("__skip__", "Pass on everything this year"))
        # default to "keep looking" if nothing's on yet and there's still room to look
        default_index = 0 if (available or not can_keep_looking) else len(options) - 2
        pick = choose(options, "  [A]udition/accept which one, keep looking, or skip?", default_index, auto)

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


def deal_screen(session: Session, auto: bool) -> None:
    want_bonus = False
    if session.box_office_bonus_available():
        bonus_choice = prompt(
            "  THE DEAL: you've got the weight for a real backend point — negotiate a box office "
            "bonus? [Y]/[N]", "N", auto,
        )
        want_bonus = bonus_choice.upper() == "Y"

    if not session.approvals_available():
        print("  THE DEAL: standard terms — you're not there yet for approvals.")
        session.choose_deal(False, want_box_office_bonus=want_bonus)
        if want_bonus:
            print("    (Box office bonus negotiated — 3% of gross, if it clears break-even.)")
        return
    choice = prompt("  THE DEAL: [1] Take the money  [2] Take less, get more say (script + co-star approval)", "1", auto)
    fee = session.choose_deal(choice == "2", want_box_office_bonus=want_bonus)
    if fee is not None:
        print(f"    (Fee cut to {fee:.2f}M — script and co-star approval, yours now.)")
    if want_bonus:
        print("    (Box office bonus negotiated — 3% of gross, if it clears break-even.)")


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
    print("  THE SHOOT — three scenes.")
    positions = session.position_options()
    for scene_name in session.scene_names():
        print(f"    Scene — {scene_name}:")
        choices = {}
        for dial_key, dial_label in session.dial_options():
            options_str = "/".join(f"[{i+1}]{label}" for i, (_, label) in enumerate(positions))
            pick = prompt(f"      {dial_label}: {options_str}", "1", auto)
            idx = int(pick) - 1 if pick.isdigit() and 1 <= int(pick) <= len(positions) else 0
            choices[dial_key] = positions[idx][0]
        session.play_scene(choices)


def release_screen(session: Session, auto: bool) -> dict:
    print("  RELEASE STRATEGY:")
    key = choose(session.release_options(), "  Choose:", 0, auto)
    if key != "streaming":
        return session.choose_release(key)

    def pick_bid(bids):
        # Resolved after the film is actually made — quality decided who showed up to bid.
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

    return session.choose_release(key, streaming_bid_selector=pick_bid)


def post_release_screen(summary: dict) -> None:
    print("  --- POST & RELEASE ---")
    print(f"    {summary['studio_name']}")
    print(f"    Your work: {summary['performance_band']}")
    print(f"    Critics: {summary['critic_band']} ({summary['critic_score']}/100)")
    print(f"    Audience: {summary['audience_band']}")
    print(f"    Release: {summary['release_label']}")
    if summary["franchise_installment"] >= 2:
        print(f"    Franchise: installment #{summary['franchise_installment']}")
    elif summary["franchise_installment"] == 1:
        print("    Franchise: the first installment — a new one, starting here")
    print(f"    Production budget: ${summary['budget_millions']:.1f}M  ·  "
          f"Marketing: ${summary['marketing_millions']:.1f}M")
    if summary["gross_millions"] <= 0:
        print(f"    Box office: {summary['roi_band']} — never really had one.")
        return
    print(f"    Box office: {summary['roi_band']} — ${summary['gross_millions']:.1f}M gross "
          f"(ROI {summary['roi']:.2f}x)")
    if summary["weekly_gross"]:
        weeks_str = "  ".join(f"Wk{i+1} ${w:.1f}M" for i, w in enumerate(summary["weekly_gross"]))
        print(f"      {weeks_str}")
    if summary.get("box_office_bonus_millions"):
        print(f"    Your negotiated bonus: ${summary['box_office_bonus_millions']:.2f}M")


def awards_screen(session: Session, auto: bool) -> None:
    if not session.awards_campaign_available():
        return
    choice = prompt("  That work was noticed. Run an awards campaign? [Y]es/[N]o", "Y", auto)
    if choice.upper() != "Y":
        return
    outcome = session.run_awards_campaign()
    if outcome["won"]:
        print("    You won.")
    elif outcome["nominated"]:
        print("    Nominated. Didn't win.")
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
            script_notes_screen(session, auto)
            director_screen(session, auto)
            costar_screen(session, auto)
            prep_screen(session, auto)
            shoot_screen(session, auto)
            summary = release_screen(session, auto)
            post_release_screen(summary)
            awards_screen(session, auto)
        else:
            print("    No project this year — the franchise moved on without you.")
    else:
        for result in session.decline_board():
            print(f"    A {result['genre']} film went to someone else: {result['roi_band']}, {result['critic_band']} reviews.")


def directing_block(session: Session, auto: bool) -> None:
    """One full directing turn — development hell through a greenlit film, if it lands. Does not
    advance the calendar (see Session.end_year())."""
    if not session.is_directing():
        choice = prompt(
            "  You've got real weight in the room now — someone would finance your own film. "
            "Step behind the camera? [Y]/[N]", "Y", auto,
        )
        if choice.upper() != "Y":
            return
        print(f"    {session.become_director()}")

    status = session.director_status()
    print(f"\n  --- DIRECTING ({status['standing']}, {status['credits']} credit(s)) ---")
    if not status["in_development"]:
        genre_key = choose(session.director_genre_options(), "  DEVELOPMENT — pick a genre to develop:", 0, auto)
        tier_key = choose(session.director_budget_tier_options(), "  Pick a budget tier to pursue:", 1, auto)
        session.start_directing_project(genre_key, tier_key)
        status = session.director_status()
    else:
        print(f"    Still developing: {status['genre']} · ${status['budget_ask']:.0f}M · "
              f"momentum {status['momentum']} · {status['quarters_in_dev']} quarter(s) in")

    action_key = choose(session.director_dev_action_options(), "  DEVELOPMENT HELL — this year's move:", 0, auto)
    result = session.advance_directing(action_key)

    if result["greenlit"]:
        print(f"    GREENLIT — ${result['budget_millions']:.1f}M production, "
              f"${result['marketing_millions']:.1f}M marketing. Critics {result['critic_band']} "
              f"({result['critic_score']}), audience {result['audience_band']}, "
              f"{result['roi_band']} (ROI {result['roi']:.2f}x), ${result['gross_millions']:.1f}M gross.")
    elif result["dead"]:
        print("    The project died in development hell.")
    elif result["frozen"]:
        print("    Shelved in the drawer for now.")
    else:
        print(f"    Still in development — momentum now {result['momentum']}.")


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
