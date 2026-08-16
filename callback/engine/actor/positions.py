"""design/part-05-the-work.md §5.5, §5.7 — the four positions, the contrast budget, and the two
named modifiers (Generosity, Upstaging) that consume/produce Notices and Ensemble around a scene.
"""
from __future__ import annotations

from dataclasses import dataclass

WITH, BENEATH, BEYOND, AGAINST = "with", "beneath", "beyond", "against"
POSITIONS = (WITH, BENEATH, BEYOND, AGAINST)

# §5.5 — internal vocabulary -> what the player actually clicks. Not used by any formula below;
# kept here because it's the canonical mapping and this is where a UI layer should read it from.
PLAYER_LABELS = {WITH: "Match it", BENEATH: "Hold back", BEYOND: "Go big", AGAINST: "Play against it"}

POSITION_COST = {WITH: 0, BENEATH: 1, BEYOND: 2, AGAINST: 3}

DIALS = ("energy", "volume", "warmth", "speed")
# §5.5 — internal dial name -> player-facing label (Energy and Warmth are shown unchanged).
DIAL_LABELS = {"energy": "Energy", "volume": "Size", "warmth": "Warmth", "speed": "Tempo"}

# (whatItDoesForYou, whatItDoesForTheFilm) per dial per position — §5.5's READ table.
READ_TABLE: dict[str, dict[str, tuple[float, float]]] = {
    "energy": {WITH: (0.5, 1.5), BENEATH: (2.5, 1.0), BEYOND: (1.0, -0.5), AGAINST: (4.5, 0.5)},
    "volume": {WITH: (0.5, 1.5), BENEATH: (3.0, 1.5), BEYOND: (0.5, -1.5), AGAINST: (3.5, 0.0)},
    "warmth": {WITH: (0.5, 1.5), BENEATH: (1.5, 0.5), BEYOND: (2.0, 0.5), AGAINST: (4.0, -0.5)},
    "speed": {WITH: (0.5, 1.5), BENEATH: (2.0, 1.0), BEYOND: (2.5, 0.0), AGAINST: (3.0, 0.5)},
}

# §5.5's own worked examples of genre reweighting: "stillness worth 1.5x in horror, 0.7x in
# action" (read as the Beneath position specifically — the position that embodies stillness);
# "speed worth 1.6x in comedy, 0.8x in drama" (read as the Speed dial, any position on it). Genres
# not listed default to 1.0 (unweighted) — these four are the only pairs design/ states explicitly.
GENRE_POSITION_REWEIGHT: dict[tuple[str, str], float] = {
    ("horror", BENEATH): 1.5,
    ("action", BENEATH): 0.7,
}
GENRE_DIAL_REWEIGHT: dict[tuple[str, str], float] = {
    ("comedy", "speed"): 1.6,
    ("drama", "speed"): 0.8,
}

CONTRAST_BUDGET_DIVISOR = 28.0
OVERSPEND_NOTICES_COEF = 5.0
OVERSPEND_ENSEMBLE_COEF = 3.0

GENEROSITY_YOU_NOTICES = -1.5
GENEROSITY_THEM_NOTICES = 2.5
GENEROSITY_FILM_ENSEMBLE = 1.5
GENEROSITY_FAVOUR = 1

UPSTAGING_YOU_NOTICES = 2.0
UPSTAGING_THEM_NOTICES = -2.0
UPSTAGING_FILM_ENSEMBLE = -1.5


def contrast_budget(craft: float, director_command: float) -> float:
    return (craft + director_command) / CONTRAST_BUDGET_DIVISOR


def _reweight(genre: str, dial: str, position: str) -> float:
    return GENRE_POSITION_REWEIGHT.get((genre, position), 1.0) * GENRE_DIAL_REWEIGHT.get((genre, dial), 1.0)


@dataclass(frozen=True)
class SceneRead:
    for_you: float
    for_film: float
    cost: float
    overspend: float


def resolve_scene_positions(choices: dict[str, str], genre: str, budget: float) -> SceneRead:
    """choices maps each of DIALS to one of POSITIONS. Returns the combined read plus any
    overspend against `budget` (already computed via contrast_budget())."""
    total_cost = sum(POSITION_COST[choices[d]] for d in DIALS)
    overspend = max(0.0, total_cost - budget)

    for_you = 0.0
    for_film = 0.0
    for d in DIALS:
        position = choices[d]
        base_you, base_film = READ_TABLE[d][position]
        w = _reweight(genre, d, position)
        for_you += base_you * w
        for_film += base_film * w

    return SceneRead(for_you=for_you, for_film=for_film, cost=total_cost, overspend=overspend)


def overspend_penalty(overspend: float) -> tuple[float, float]:
    """Returns (notices_penalty, ensemble_penalty) — both already negative-signed deltas."""
    if overspend <= 0:
        return 0.0, 0.0
    return -OVERSPEND_NOTICES_COEF * overspend, -OVERSPEND_ENSEMBLE_COEF * overspend


@dataclass(frozen=True)
class ModifierResult:
    you_notices: float
    them_notices: float
    film_ensemble: float
    you_favour: float = 0.0
    affinity_delta: float = 0.0


def generosity(their_affinity_gain: float = 0.0) -> ModifierResult:
    """Playing Beneath on a dial where your scene partner plays Beyond or Against."""
    return ModifierResult(
        you_notices=GENEROSITY_YOU_NOTICES,
        them_notices=GENEROSITY_THEM_NOTICES,
        film_ensemble=GENEROSITY_FILM_ENSEMBLE,
        you_favour=GENEROSITY_FAVOUR,
        affinity_delta=their_affinity_gain,
    )


def upstaging(affinity_loss: float = -1.0) -> ModifierResult:
    """Playing Beyond in a scene partner's moment."""
    return ModifierResult(
        you_notices=UPSTAGING_YOU_NOTICES,
        them_notices=UPSTAGING_THEM_NOTICES,
        film_ensemble=UPSTAGING_FILM_ENSEMBLE,
        affinity_delta=affinity_loss,
    )
