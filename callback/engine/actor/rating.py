"""design/part-05-the-work.md §5.19 — the content rating.

Like the palette itself, a film's rating isn't chosen, it's read off what the film already is:
a pure function of the six-dial palette's own Intensity axis (§5.3) plus a per-genre baseline —
the same Intensity setting that reads PG-13 in a thriller reads R in a horror film, because a
horror audience's whole relationship to the genre is calibrated around what that rating signals.

Nothing here decides anything by itself. career.py reads rating_score()/rating_band() off a
project's already-generated Palette, and actor/studios.py's decide_rating_cut() is the one real
negotiation the rating creates: whether the film ships as shot or gets trimmed for the friendlier
neighboring band. Both stay separate from this module on purpose — rating.py is the read, not the
decision, same split palette.py keeps between the six dials and coherence()/landmark_bonus().
"""
from __future__ import annotations

from callback.engine.core.util import clamp

# RatingScore = 0.70 * Intensity + genreBaseline[genre]. Intensity is §5.3's own Gentle<->Intense
# palette dial (-50..50); the genre baseline is the honest work — the same Intensity setting reads
# a different rating depending on what the audience already expects from the genre.
INTENSITY_WEIGHT = 0.70

GENRE_RATING_BASELINE: dict[str, float] = {
    "family": -22.0, "musical": -10.0, "comedy": -4.0, "romance": -2.0, "period": 0.0,
    "drama": 4.0, "scifi": 2.0, "fantasy": 4.0, "thriller": 6.0, "superhero": 6.0,
    "action": 8.0, "crime": 10.0, "horror": 18.0,
}

# Animation pulls toward the friendlier bands at the same Intensity setting as its live-action
# counterpart — composes additively with the genre baseline above (an animated horror film still
# reads more intense than an animated family comedy, just less intense than live-action horror
# would at the same dial), the same honest-additive shape GENRE_RATING_BASELINE already uses.
ANIMATION_RATING_OFFSET = -18.0

# (upper_bound, label) — RatingScore < the first bound's upper_bound lands in that band.
RATING_BANDS: tuple[tuple[float, str], ...] = (
    (-25.0, "G"), (0.0, "PG"), (25.0, "PG-13"), (50.0, "R"), (float("inf"), "NC-17"),
)
RATING_BAND_ORDER: tuple[str, ...] = tuple(label for _, label in RATING_BANDS)

# The one real decision this creates: available only on a genuine borderline film, within this
# many points of a band edge — not a lever on every film (§5.19's own restraint, the same instinct
# §5.12's situational moment pool already applies to which moments even get asked).
BOUNDARY_MARGIN = 6.0

# Cut for the friendlier rating: Intensity's realized effect trimmed just enough to cross the
# line; the compromise shows on screen as a real critic-score cost, regardless of genre.
CUT_CRITIC_PENALTY_LO = 3.0
CUT_CRITIC_PENALTY_HI = 6.0

# Release as shot: the film as made, the harder rating, the narrower reach — except for horror and
# action, where the rating was never the problem for that audience, it was the point.
RELEASE_AS_SHOT_EXEMPT_GENRES = frozenset({"horror", "action"})
# Per point RatingScore sits past the boundary it missed — bounded by BOUNDARY_MARGIN itself
# (this only ever fires on a genuine borderline film), so the real range is a few AudienceScore
# points, the same order of magnitude as CUT's own FilmCritic cost, not a dominant term.
RELEASE_AS_SHOT_REACH_PENALTY_COEF = 0.6

RATING_CUT = "cut"
RATING_RELEASE_AS_SHOT = "release_as_shot"
RATING_STANCES = (RATING_CUT, RATING_RELEASE_AS_SHOT)


def rating_score(intensity: float, genre: str, is_animation: bool = False) -> float:
    offset = ANIMATION_RATING_OFFSET if is_animation else 0.0
    return INTENSITY_WEIGHT * intensity + GENRE_RATING_BASELINE.get(genre, 0.0) + offset


def rating_band(score: float) -> str:
    for upper, label in RATING_BANDS:
        if score < upper:
            return label
    return RATING_BANDS[-1][1]  # unreachable (last bound is +inf), kept for clarity


def _boundaries() -> list[float]:
    return [upper for upper, _ in RATING_BANDS[:-1]]


def nearest_boundary_distance(score: float) -> float:
    return min(abs(score - b) for b in _boundaries())


def near_boundary(score: float, margin: float = BOUNDARY_MARGIN) -> bool:
    return nearest_boundary_distance(score) <= margin


def friendlier_band(score: float) -> str:
    """The band one step safer than score's own — what a successful cut actually buys. A cut only
    ever moves toward the nearer boundary it's already sitting next to, never further."""
    idx = RATING_BAND_ORDER.index(rating_band(score))
    return RATING_BAND_ORDER[max(idx - 1, 0)]
