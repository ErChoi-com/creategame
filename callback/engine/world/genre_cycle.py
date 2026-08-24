"""design/part-09-genres-franchises-and-tie-ins.md §9.3 — genre cycles, fed by every resolved
film in the background industry (design/part-10 §10.0), not just the player's own.
"""
from __future__ import annotations

from callback.engine.core.util import clamp

GENRE_HEAT_ROI_THRESHOLD = 2.5
GENRE_HEAT_GAIN = 30.0
GENRE_HEAT_DECAY = 0.85
BOOM_THRESHOLD = 55.0
BUST_THRESHOLD = 10.0


def accumulate_heat(heat: dict[str, float], genre: str, roi: float) -> dict[str, float]:
    if roi <= GENRE_HEAT_ROI_THRESHOLD:
        return heat
    new_heat = dict(heat)
    new_heat[genre] = clamp(new_heat.get(genre, 0.0) + GENRE_HEAT_GAIN, 0.0, 200.0)
    return new_heat


def decay_all(heat: dict[str, float]) -> dict[str, float]:
    return {g: v * GENRE_HEAT_DECAY for g, v in heat.items()}


def booming_genres(heat: dict[str, float]) -> list[str]:
    return [g for g, v in heat.items() if v >= BOOM_THRESHOLD]


def busting_genres(heat: dict[str, float], all_genres: tuple[str, ...]) -> list[str]:
    return [g for g in all_genres if heat.get(g, 0.0) <= BUST_THRESHOLD]


def genre_demand(heat: dict[str, float], genre: str, base: float = 50.0) -> float:
    """A hot genre's GenreDemand (actor/reception.py's genre_demand input) reads higher than
    baseline; this is the wire from the background industry's heat back into a single project's
    reception numbers."""
    return clamp(base + 0.4 * heat.get(genre, 0.0), 0.0, 100.0)
