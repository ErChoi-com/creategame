#!/usr/bin/env python3
"""A terminal-playable prototype following design/ux/'s exact screen flow: character creation
(ux/01), the hub (ux/02), and the season loop (ux/03) — Offer Board -> the Deal -> Prep -> the
Shoot -> Post & Release -> the Reckoning. Every hidden number renders through
simulation/bands.py's words-not-numbers pass (ux/05), never as a raw score.

    python3 -m callback.engine.simulation.cli            # interactive
    python3 -m callback.engine.simulation.cli --auto      # self-playing demo, no input needed
"""
from __future__ import annotations

import random
import sys
from dataclasses import replace

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.offers import resolve_casting_path, offer_probability
from callback.engine.actor.persona import GENRES
from callback.engine.actor.positions import DIAL_LABELS, DIALS, PLAYER_LABELS, POSITIONS
from callback.engine.actor.prep import PREP_OPTIONS, WING_IT
from callback.engine.actor.release import FESTIVAL, LIMITED, SHELVED, STREAMING, WIDE, weekly_gross_curve
from callback.engine.leverage.approvals import can_negotiate_approvals, fee_after_approvals
from callback.engine.life.money import MoneyState
from callback.engine.simulation.bands import audience_band, critic_band, performance_band, roi_band, standing_band
from callback.engine.simulation.career import ActorState
from callback.engine.simulation.full_career import (
    accept_and_play,
    advance_between_years,
    decline_and_resolve,
    new_full_state,
    obituary,
    offer_this_year,
    utility_for,
)
from callback.engine.world.trades import generate_digest

BACKGROUNDS = {
    "1": ("Conservatory", "Trained. Broke. Unknown.", Attributes(craft=62, instinct=45, presence=35, resilience=50)),
    "2": ("Discovered", "A manager, momentum, and no technique yet.", Attributes(craft=28, instinct=55, presence=70, resilience=45)),
    "3": ("Regional stage", "Years of range. No union credits. Not young anymore.", Attributes(craft=70, instinct=50, presence=45, resilience=55)),
    "4": ("Family money", "The rent's solved. The room can tell.", Attributes(craft=45, instinct=45, presence=35, resilience=35)),
}
REGIONAL_STAGE_START_AGE = 33


def prompt(msg: str, auto_default: str, auto: bool) -> str:
    if auto:
        print(f"{msg} -> {auto_default}")
        return auto_default
    try:
        val = input(f"{msg} ").strip()
    except EOFError:
        return auto_default
    return val or auto_default


def character_creation(rng: random.Random, auto: bool) -> tuple[ActorState, str]:
    print("\nYou do not control whether the film is good.\n")
    print("BACKGROUND")
    for key, (name, tagline, _) in BACKGROUNDS.items():
        print(f"  {key}. {name} — {tagline}")
    choice = prompt("Choose (1-4):", "1", auto)
    name, _, attrs = BACKGROUNDS.get(choice, BACKGROUNDS["1"])
    start_age = REGIONAL_STAGE_START_AGE if name == "Regional stage" else 22

    print(f"\nYou are, at heart, {name}.\n")
    state = new_full_state(rng, start_age=start_age)
    state = replace(state, actor=replace(state.actor, attrs=attrs.clamped()))

    if name == "Family money":
        state = replace(state, life=replace(state.life, money=MoneyState(net_worth=2.0)))

    print("AMBITION — this decides what your obituary measures you against; it gates nothing.")
    ambitions = ["The Work", "The Prize", "The Fortune", "The Run", "The Franchise", "The Voice"]
    for i, a in enumerate(ambitions, 1):
        print(f"  {i}. {a}")
    amb_choice = prompt("Choose (1-6):", "1", auto)
    ambition = ambitions[int(amb_choice) - 1] if amb_choice.isdigit() and 1 <= int(amb_choice) <= 6 else ambitions[0]
    print(f"You're chasing {ambition}. You can change your mind once, later.\n")

    return state, ambition


def offer_board_screen(state, rng, auto: bool):
    role = offer_this_year(state, rng)
    print(f"\n--- THIS YEAR'S OFFER ---")
    print(f"  {role.genre.title()} · {role.billing} · {role.budget_for_role:.2f}M budget")
    u = utility_for(state, role)
    path = resolve_casting_path(u, role)
    would_offer = path == "direct_offer" or rng.random() < offer_probability(u, role.difficulty)
    if not would_offer:
        print("  (An audition — but it doesn't come through this year.)")
        return role, False
    choice = prompt("  [A]udition/accept or [D]ecline?", "A", auto)
    return role, choice.upper() != "D"


def deal_screen(state, auto: bool) -> frozenset[str]:
    """design/part-06 §6.3: script/co-star approval for a 30%-per-approval fee cut, gated at
    Standing 65+ — the Deal screen's real fork, not a cosmetic label."""
    standing_score = state.actor.standing.weighted_score({"heat": 0.4, "prestige": 0.3, "affection": 0.3})
    if not can_negotiate_approvals(standing_score):
        print("  THE DEAL: standard terms — you're not there yet for approvals.")
        return frozenset()
    choice = prompt("  THE DEAL: [1] Take the money  [2] Take less, get more say (script + co-star approval)", "1", auto)
    return frozenset({"script", "costar"}) if choice == "2" else frozenset()


def prep_screen(auto: bool) -> str:
    print("  PREP:")
    options = [o for o in PREP_OPTIONS if o != WING_IT]
    for i, o in enumerate(options, 1):
        print(f"    {i}. {o.replace('_', ' ')}")
    choice = prompt(f"  Choose (1-{len(options)}):", "1", auto)
    idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(options) else 0
    return options[idx]


def shoot_screen(rng, auto: bool):
    print("  THE SHOOT — three scenes.")
    scene_names = ["Scene 1 — the setup", "Scene 2 — the turn", "Scene 3 — the resolution"]
    scenes = []
    for scene_name in scene_names:
        print(f"    {scene_name}:")
        choice = {}
        for dial in DIALS:
            label = DIAL_LABELS[dial]
            options_str = "/".join(f"[{i+1}]{PLAYER_LABELS[p]}" for i, p in enumerate(POSITIONS))
            pick = prompt(f"      {label}: {options_str}", "1", auto)
            idx = int(pick) - 1 if pick.isdigit() and 1 <= int(pick) <= 4 else 0
            choice[dial] = POSITIONS[idx]
        scenes.append(choice)
    return tuple(scenes)


RELEASE_LABELS = {
    WIDE: "Wide — full theatrical push",
    LIMITED: "Limited — platform release, word of mouth does the work",
    FESTIVAL: "Festival — you find out if anyone even buys it",
    STREAMING: "Streaming — a flat guaranteed payout, no upside",
    SHELVED: "Shelved — it doesn't come out at all",
}
RELEASE_ORDER = (WIDE, LIMITED, FESTIVAL, STREAMING, SHELVED)


def release_screen(auto: bool) -> str:
    print("  RELEASE STRATEGY:")
    for i, strat in enumerate(RELEASE_ORDER, 1):
        print(f"    {i}. {RELEASE_LABELS[strat]}")
    choice = prompt(f"  Choose (1-{len(RELEASE_ORDER)}):", "1", auto)
    idx = int(choice) - 1 if choice.isdigit() and 1 <= int(choice) <= len(RELEASE_ORDER) else 0
    return RELEASE_ORDER[idx]


def post_release_screen(result):
    print("  --- POST & RELEASE ---")
    print(f"    Your work: {performance_band(result.performance)}")
    print(f"    Critics: {critic_band(result.film_critic_score)} ({result.film_critic_score:.0f}/100)")
    print(f"    Audience: {audience_band(result.audience_score)}")
    print(f"    Release: {RELEASE_LABELS[result.release_strategy]}")
    if result.gross <= 0:
        print(f"    Box office: {roi_band(result.roi)} — never really had one.")
        return
    print(f"    Box office: {roi_band(result.roi)} — ${result.gross:.1f}M on a ${result.budget:.1f}M budget (ROI {result.roi:.2f}x)")
    if result.release_strategy in (WIDE, LIMITED):
        curve = weekly_gross_curve(result.opening, result.legs, weeks=5)
        weeks_str = "  ".join(f"Wk{i+1} ${w:.1f}M" for i, w in enumerate(curve))
        print(f"      {weeks_str}")


def reckoning_screen(state):
    sc = state.actor.standing
    print(f"  RECKONING — you are {standing_band(sc.weighted_score({'heat': 0.4, 'prestige': 0.3, 'affection': 0.3}))} now.")


def run(auto: bool, seed: int, max_years: int) -> None:
    rng = random.Random(seed)
    state, ambition = character_creation(rng, auto)

    for _ in range(max_years):
        if state.actor.age >= 90:
            break
        print(f"\n=== AGE {state.actor.age} ===")
        role, take_it = offer_board_screen(state, rng, auto)

        if take_it:
            approvals = deal_screen(state, auto)
            if approvals:
                fee = fee_after_approvals(role.budget_for_role, approvals)
                print(f"    (Fee cut to {fee:.2f}M — script and co-star approval, yours now.)")
            prep_choice = prep_screen(auto)
            scenes = shoot_screen(rng, auto)
            strategy = release_screen(auto)
            state, result = accept_and_play(state, role, prep_choice, scenes, rng, release_strategy=strategy)
            post_release_screen(result)
            state = advance_between_years(state, rng, worked_this_year=True, billing=role.billing)
        else:
            state = decline_and_resolve(state, role, rng)
            state = advance_between_years(state, rng, worked_this_year=False)

        reckoning_screen(state)

        if state.actor.age % 5 == 0:
            print("  THE TRADES:")
            for line in generate_digest(state.genre_heat, state.rolodex, GENRES):
                print(f"    - {line}")

        if not auto:
            cont = prompt("\n[Enter] to continue, [q] to end the run:", "", auto)
            if cont.lower() == "q":
                break

    print("\n=== THE OBITUARY ===")
    ob = obituary(state)
    print(f"  {len(ob.filmography)} credited roles played.")
    print(f"  {len(ob.declined)} roles turned down — here's what became of them:")
    for d in ob.declined[:5]:
        r = d.result.reception
        print(f"    - A {d.role_genre} film you passed on: {roi_band(r.roi)} (${r.gross:.1f}M, {r.roi:.2f}x), "
              f"{critic_band(r.film_critic_score)} reviews ({r.film_critic_score:.0f}/100).")
    print(f"  {len(ob.kept)} relationships you kept. {len(ob.lost)} you lost.")
    if ob.best_hidden_performance:
        r = ob.best_hidden_performance
        print(f"  Your best hidden performance: a {r.role.genre} film — {performance_band(r.performance)} work nobody quite noticed.")


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
