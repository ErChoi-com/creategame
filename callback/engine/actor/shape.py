"""design/part-05-the-work.md §5.6 — Shape: the single canonical Notices/Ensemble resolution.

Three scenes (setup / turn / resolution), each an independent position decision (positions.py).
This is the one place YourNotices/EnsembleScore are computed — reception.py consumes this
module's output rather than recomputing it, matching §4.10's own v9 note that there is now
exactly one code path between the two.

§5.6's formula text gives the three pieces (the per-scene READ-table average, a beat-weighted
"peak" term keyed to spikiness, and a −4.0×spikiness Ensemble penalty) without fully specifying
how "peak(scene)" and "spikiness" are computed from the three raw scene reads. This module's
reading, documented inline: spikiness is the dispersion (population stdev) of the three scenes'
raw for_you values; the turn scene — structurally the emotional peak of any three-scene shape,
per §5.6's own per-genre "the turn" table — is the scene the beat-weighting is centred on.
"""
from __future__ import annotations

import statistics as st
from dataclasses import dataclass

from callback.engine.actor.positions import SceneRead

SETUP, TURN, RESOLUTION = 0, 1, 2

LIFT_COEF = 9.0
BEAT_WEIGHT = {SETUP: -0.65, TURN: 1.30, RESOLUTION: -0.65}

NOTICES_PEAK_WEIGHT = 0.55
NOTICES_PERFORMANCE_WEIGHT = 0.45
ENSEMBLE_SPIKINESS_COEF = 4.0

# §5.6 — per-genre identity of "the turn."
GENRE_TURN = {
    "horror": "first kill / threat confirmed real",
    "action": "the set piece",
    "drama": "the confrontation",
    "comedy": "the set-piece farce / loaded joke",
    "romance": "the falling-out",
    "thriller": "the reveal",
    "scifi": "the reveal (world rule made visible)",
    "musical": "the number",
    "period": "the era's weight becomes personal",
    "family": "the scene remembered at 40",
}


@dataclass(frozen=True)
class ShapeResult:
    notices: float
    ensemble: float
    spikiness: float
    total_overspend: float


def spikiness(scene_reads: tuple[SceneRead, SceneRead, SceneRead]) -> float:
    for_you_values = [s.for_you for s in scene_reads]
    if len(set(for_you_values)) == 1:
        return 0.0
    return st.pstdev(for_you_values)


def resolve_shape(
    scene_reads: tuple[SceneRead, SceneRead, SceneRead],
    your_performance_shape: float,
) -> ShapeResult:
    spike = spikiness(scene_reads)
    lift = LIFT_COEF * spike

    mean_for_you = sum(s.for_you for s in scene_reads) / 3.0
    mean_for_film = sum(s.for_film for s in scene_reads) / 3.0

    peak = scene_reads[TURN].for_you + BEAT_WEIGHT[TURN] * lift

    notices = NOTICES_PEAK_WEIGHT * peak + NOTICES_PERFORMANCE_WEIGHT * your_performance_shape + mean_for_you
    ensemble = your_performance_shape - ENSEMBLE_SPIKINESS_COEF * spike + mean_for_film

    total_overspend = sum(s.overspend for s in scene_reads)

    return ShapeResult(notices=notices, ensemble=ensemble, spikiness=spike, total_overspend=total_overspend)
