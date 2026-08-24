"""design/part-05-the-work.md §5.3-5.4 — the six-dial film palette, Coherence, and landmarks.

§5.3 states the corr(audience, critic) *results* by genre (Horror +0.52 ... Drama −0.58) as the
tuning target, not the underlying per-genre-per-dial weight table itself, and §5.4's Coherence
references "distance to nearest archetype" without publishing the canonical archetype vectors.
GENRE_DIAL_WEIGHTS and CANONICAL_ARCHETYPES below are this pass's documented, internally
consistent readings, built to reproduce the *sign* of each genre's stated correlation — not a
transcription of undisclosed exact constants. If design/ is ever amended with the literal table,
swap it in here; nothing downstream needs to change shape.
"""
from __future__ import annotations

from dataclasses import dataclass, fields

from callback.engine.core.util import clamp

DIALS = ("pace", "colour", "scale", "intensity", "clarity", "texture")

# (audience_weight, critic_weight) per dial, per genre. Chosen so that dominant-dial signs match
# §5.3's stated corr(audience, critic): Horror +0.52, Comedy +0.19, Sci-fi +0.01, Action −0.10,
# Drama −0.58; other genres given a plausible, unexercised-by-doc reading in the same spirit.
GENRE_DIAL_WEIGHTS: dict[str, dict[str, tuple[float, float]]] = {
    "drama": {"pace": (0.0, 0.0), "colour": (0.0, 0.0), "scale": (0.0, 0.0),
              "intensity": (0.0, 0.0), "clarity": (0.18, -0.22), "texture": (0.0, 0.0)},
    "comedy": {"pace": (0.0, 0.0), "colour": (0.0, 0.0), "scale": (0.0, 0.0),
               "intensity": (0.0, 0.0), "clarity": (0.0, 0.0), "texture": (0.14, 0.10)},
    "action": {"pace": (0.0, 0.0), "colour": (0.0, 0.0), "scale": (0.20, -0.08),
               "intensity": (0.10, -0.02), "clarity": (0.0, 0.0), "texture": (0.0, 0.0)},
    "horror": {"pace": (0.0, 0.0), "colour": (0.0, 0.0), "scale": (0.0, 0.0),
               "intensity": (0.24, 0.22), "clarity": (-0.10, -0.10), "texture": (0.08, 0.06)},
    "thriller": {"pace": (0.12, 0.08), "colour": (0.0, 0.0), "scale": (0.0, 0.0),
                 "intensity": (0.10, 0.04), "clarity": (-0.06, -0.10), "texture": (0.0, 0.0)},
    "romance": {"pace": (0.0, 0.0), "colour": (0.10, 0.06), "scale": (0.0, 0.0),
                "intensity": (0.0, 0.0), "clarity": (0.08, -0.04), "texture": (0.0, 0.0)},
    "scifi": {"pace": (0.0, 0.0), "colour": (0.06, -0.05), "scale": (0.12, -0.10),
              "intensity": (0.0, 0.0), "clarity": (-0.05, 0.06), "texture": (0.0, 0.0)},
    "period": {"pace": (-0.08, 0.06), "colour": (0.10, 0.08), "scale": (0.10, 0.06),
               "intensity": (0.0, 0.0), "clarity": (0.0, 0.0), "texture": (0.0, 0.0)},
    "musical": {"pace": (0.14, 0.10), "colour": (0.16, 0.12), "scale": (0.08, 0.04),
                "intensity": (0.0, 0.0), "clarity": (0.0, 0.0), "texture": (0.0, 0.0)},
    "family": {"pace": (0.0, 0.0), "colour": (0.12, 0.10), "scale": (0.0, 0.0),
               "intensity": (-0.08, -0.06), "clarity": (0.10, 0.08), "texture": (0.0, 0.0)},
    # v19 — five new primary genres (design/part-09 §9.1's table extended, redone from scratch
    # this pass alongside the secondary-genre/hybrid system in genre/hybrids.py — a film picking
    # a secondary genre reads BOTH rows below, averaged, so every new genre needs to stand on its
    # own the same way the original ten do): fantasy reads like scifi's world-building cousin
    # (scale/texture over clarity); crime reads like a grittier thriller (clarity costs critic
    # more, texture pays it back); superhero reads like action turned up (scale/intensity
    # dominant, harder critic cost); war leans on intensity/texture with a heavy critic reward for
    # clarity (the "prestige machine" read from §9.1's table); western is a slower, wide-open
    # cousin of action (scale over pace, texture-heavy, less critic-punishing).
    "fantasy": {"pace": (0.0, 0.0), "colour": (0.12, 0.05), "scale": (0.18, -0.06),
                "intensity": (0.05, -0.02), "clarity": (-0.06, 0.04), "texture": (0.10, 0.06)},
    "crime": {"pace": (0.08, 0.06), "colour": (-0.06, 0.04), "scale": (0.0, 0.0),
              "intensity": (0.08, 0.02), "clarity": (0.10, -0.16), "texture": (0.06, 0.08)},
    "superhero": {"pace": (0.10, -0.04), "colour": (0.08, -0.06), "scale": (0.24, -0.12),
                  "intensity": (0.14, -0.06), "clarity": (0.0, 0.0), "texture": (0.0, 0.0)},
    "war": {"pace": (-0.05, 0.0), "colour": (-0.10, 0.02), "scale": (0.10, 0.0),
            "intensity": (0.18, 0.10), "clarity": (0.06, 0.14), "texture": (0.14, 0.10)},
    "western": {"pace": (-0.10, 0.02), "colour": (0.04, 0.02), "scale": (0.14, 0.0),
                "intensity": (0.06, -0.02), "clarity": (0.0, 0.0), "texture": (0.16, 0.08)},
}

# Canonical "coherent" palette vector per genre, used by coherence() below.
CANONICAL_ARCHETYPES: dict[str, dict[str, float]] = {
    "drama": {"pace": -15, "colour": -10, "scale": -20, "intensity": 5, "clarity": -10, "texture": -10},
    "comedy": {"pace": 20, "colour": 15, "scale": -10, "intensity": -10, "clarity": 10, "texture": 15},
    "action": {"pace": 30, "colour": 10, "scale": 35, "intensity": 30, "clarity": 15, "texture": 25},
    "horror": {"pace": 10, "colour": -15, "scale": -15, "intensity": 40, "clarity": -20, "texture": 20},
    "thriller": {"pace": 20, "colour": -5, "scale": 0, "intensity": 25, "clarity": -15, "texture": 15},
    "romance": {"pace": -10, "colour": 20, "scale": -20, "intensity": -5, "clarity": 5, "texture": -5},
    "scifi": {"pace": 5, "colour": 10, "scale": 30, "intensity": 15, "clarity": -10, "texture": 10},
    "period": {"pace": -20, "colour": 15, "scale": 25, "intensity": -5, "clarity": -5, "texture": -5},
    "musical": {"pace": 25, "colour": 30, "scale": 15, "intensity": 0, "clarity": 15, "texture": 20},
    "family": {"pace": 5, "colour": 20, "scale": 5, "intensity": -20, "clarity": 20, "texture": 5},
    "fantasy": {"pace": 10, "colour": 25, "scale": 35, "intensity": 10, "clarity": -15, "texture": 25},
    "crime": {"pace": 5, "colour": -15, "scale": -5, "intensity": 15, "clarity": -20, "texture": 20},
    "superhero": {"pace": 25, "colour": 15, "scale": 40, "intensity": 25, "clarity": 10, "texture": 15},
    "war": {"pace": -10, "colour": -20, "scale": 20, "intensity": 30, "clarity": 15, "texture": 30},
    "western": {"pace": -15, "colour": 5, "scale": 25, "intensity": 5, "clarity": 0, "texture": 35},
}

COHERENCE_DISTANCE_COEF = 2.2
LANDMARK_COHERENCE_THRESHOLD = 60.0
LANDMARK_SKILL_THRESHOLD = 70.0
LANDMARK_BASE = 0.02
LANDMARK_COEF = 0.00022
LANDMARK_CAP = 0.20


@dataclass(frozen=True)
class Palette:
    pace: float = 0.0
    colour: float = 0.0
    scale: float = 0.0
    intensity: float = 0.0
    clarity: float = 0.0
    texture: float = 0.0

    def clamped(self) -> "Palette":
        from dataclasses import replace
        return replace(self, **{f.name: clamp(getattr(self, f.name), -50.0, 50.0) for f in fields(self)})

    def as_dict(self) -> dict[str, float]:
        return {d: getattr(self, d) for d in DIALS}


def palette_reception_effect(palette: Palette, genre: str) -> tuple[float, float]:
    """Returns (audience_delta, critic_delta) — Σ weight[genre][dial] × setting/100 for each."""
    weights = GENRE_DIAL_WEIGHTS[genre]
    settings = palette.as_dict()
    audience = sum(weights[d][0] * settings[d] / 100.0 for d in DIALS)
    critic = sum(weights[d][1] * settings[d] / 100.0 for d in DIALS)
    return audience, critic


def distance_to_nearest_archetype(palette: Palette) -> float:
    settings = palette.as_dict()
    best = float("inf")
    for archetype in CANONICAL_ARCHETYPES.values():
        dist = sum((settings[d] - archetype[d]) ** 2 for d in DIALS) ** 0.5
        best = min(best, dist)
    return best


def coherence(palette: Palette) -> float:
    return clamp(100.0 - COHERENCE_DISTANCE_COEF * distance_to_nearest_archetype(palette), 0.0, 100.0)


def outcome_variance_multiplier(coherence_value: float) -> float:
    return 1.0 + 0.014 * (100.0 - coherence_value)


def landmark_probability(coherence_value: float, skill: float) -> float:
    """skill stands in for (Craft + DirectorVision) / 2 — the director isn't modeled in this
    pass, so callers pass a single scalar for that average."""
    if coherence_value >= LANDMARK_COHERENCE_THRESHOLD or skill <= LANDMARK_SKILL_THRESHOLD:
        return 0.0
    p = LANDMARK_BASE + LANDMARK_COEF * (60.0 - coherence_value) * (skill - LANDMARK_SKILL_THRESHOLD)
    return clamp(p, 0.0, LANDMARK_CAP)


def landmark_roll(coherence_value: float, skill: float, rng) -> bool:
    return rng.random() < landmark_probability(coherence_value, skill)
