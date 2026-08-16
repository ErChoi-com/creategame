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


def offer_board_screen(session: Session, auto: bool) -> tuple[dict, bool]:
    offer = session.roll_offer()
    print("\n--- THIS YEAR'S OFFER ---")
    print(f"  {offer['genre'].title()} · {offer['billing']} · {offer['budget_millions']:.2f}M budget")
    if not offer["available"]:
        print("  (An audition — but it doesn't come through this year.)")
        return offer, False
    choice = prompt("  [A]udition/accept or [D]ecline?", "A", auto)
    return offer, choice.upper() != "D"


def deal_screen(session: Session, auto: bool) -> None:
    if not session.approvals_available():
        print("  THE DEAL: standard terms — you're not there yet for approvals.")
        session.choose_deal(False)
        return
    choice = prompt("  THE DEAL: [1] Take the money  [2] Take less, get more say (script + co-star approval)", "1", auto)
    fee = session.choose_deal(choice == "2")
    if fee is not None:
        print(f"    (Fee cut to {fee:.2f}M — script and co-star approval, yours now.)")


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
    return session.choose_release(key)


def post_release_screen(summary: dict) -> None:
    print("  --- POST & RELEASE ---")
    print(f"    Your work: {summary['performance_band']}")
    print(f"    Critics: {summary['critic_band']} ({summary['critic_score']}/100)")
    print(f"    Audience: {summary['audience_band']}")
    print(f"    Release: {summary['release_label']}")
    if summary["gross_millions"] <= 0:
        print(f"    Box office: {summary['roi_band']} — never really had one.")
        return
    print(f"    Box office: {summary['roi_band']} — ${summary['gross_millions']:.1f}M on a "
          f"${summary['budget_millions']:.1f}M budget (ROI {summary['roi']:.2f}x)")
    if summary["weekly_gross"]:
        weeks_str = "  ".join(f"Wk{i+1} ${w:.1f}M" for i, w in enumerate(summary["weekly_gross"]))
        print(f"      {weeks_str}")


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


def run(auto: bool, seed: int, max_years: int) -> None:
    session = Session(seed=seed)
    character_creation(session, auto)

    for _ in range(max_years):
        if session.is_over():
            break
        print(f"\n=== AGE {session.age()} ===")
        pull_menu(session, auto)
        offer, take_it = offer_board_screen(session, auto)

        if take_it:
            session.accept()
            deal_screen(session, auto)
            prep_screen(session, auto)
            shoot_screen(session, auto)
            summary = release_screen(session, auto)
            post_release_screen(summary)
            awards_screen(session, auto)
        else:
            result = session.decline()
            print(f"    It went to someone else: {result['roi_band']}, {result['critic_band']} reviews.")

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
