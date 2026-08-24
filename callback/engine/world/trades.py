"""design/part-10-the-world.md §10.0 — the trades: a once-a-year, pull-only, five-line digest of
what the background industry just did. Pure presentation over state other modules already hold.
"""
from __future__ import annotations

from callback.engine.rolodex.npc import LOYAL, RIVAL
from callback.engine.rolodex.rolodex import Rolodex
from callback.engine.world.genre_cycle import booming_genres, busting_genres

MAX_DIGEST_LINES = 5


def generate_digest(heat: dict[str, float], rolodex: Rolodex, all_genres: tuple[str, ...]) -> list[str]:
    lines: list[str] = []

    booming = booming_genres(heat)
    if booming:
        lines.append(f"{booming[0].title()} is booming — every studio wants one.")

    busting = busting_genres(heat, all_genres)
    if busting:
        lines.append(f"{busting[0].title()} scripts are dead on arrival this year.")

    for n in rolodex.tracked():
        if n.relationship_state == RIVAL:
            lines.append(f"{n.name} is having a moment — and it isn't yours.")
            break

    for n in rolodex.tracked():
        if n.relationship_state == LOYAL and n.standing is not None and n.standing["heat"] > 70:
            lines.append(f"{n.name}'s new film is the one everyone's talking about.")
            break

    if not lines:
        lines.append("A quiet year. Nothing much moved.")

    return lines[:MAX_DIGEST_LINES]
