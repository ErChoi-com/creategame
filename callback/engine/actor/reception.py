"""design/part-04-the-actor.md §4.10 — Reception: the decoupling.

Takes Notices/Ensemble from actor/shape.py rather than recomputing them — §4.10's own v9 note
states there is now exactly one code path producing those two numbers, and this module is the
consumer, not a second producer.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from callback.engine.core.util import clamp

# ProjectQuality weights.
PQ_SCRIPT = 0.31
PQ_DIRECTOR_SKILL = 0.22
PQ_ENSEMBLE = 0.29
PQ_PRODUCTION_VALUE = 0.08
PQ_POST_LUCK = 0.10
POST_LUCK_MEAN = 52.0
POST_LUCK_SD = 14.0

# FilmCriticScore.
CRITIC_DIRECTOR_PRESTIGE_COEF = 0.10
CRITIC_DIRECTOR_PRESTIGE_CENTRE = 50.0
CRITIC_NOISE_SD = 4.6
# §4.10's genre bias table lists these four explicitly; unlisted genres default to 0.
GENRE_CRITIC_BIAS = {"drama": 4.0, "horror": -5.0, "comedy": -4.0, "action": -3.0}

# Box office.
BREAK_EVEN_MARKETING_SHARE = 0.45  # §4.10's own flat approximation for a single release card
RIGHTS_SHARE = 0.62
OPENING_BASE = 0.92
OPENING_STAR_POWER_COEF = 0.005
OPENING_DEMAND_COEF = 0.005
OPENING_BUDGET_EXPONENT = -0.10
ZEITGEIST_DEMAND_COEF = 0.5
ZEITGEIST_NOISE_SD = 12.0
LEGS_BASE = 1.7
LEGS_AUDIENCE_COEF = 0.048
LEGS_AUDIENCE_CENTRE = 50.0
LEGS_ZEITGEIST_COEF = 0.032
LEGS_ZEITGEIST_THRESHOLD = 70.0
LEGS_LO, LEGS_HI = 1.15, 8.0


def production_value(budget_millions: float) -> float:
    """§4.10 names ProductionValue(budget) as an input without publishing its formula; this
    pass's documented reading is a log-scaled curve (diminishing returns on budget, as every
    other budget-driven curve in design/ — reach(), Marketing() — is also log/tiered)."""
    return clamp(30.0 + 20.0 * math.log10(budget_millions + 1.0), 0.0, 100.0)


@dataclass(frozen=True)
class ReceptionResult:
    project_quality: float
    film_critic_score: float
    audience_score: float
    budget: float
    break_even: float
    opening: float
    zeitgeist: float
    legs: float
    gross: float
    roi: float


def resolve_reception(
    script_quality: float,
    director_skill: float,
    ensemble: float,
    genre: str,
    role_budget_millions: float,
    director_prestige: float,
    staleness_penalty: float,
    cast_star_power: float,
    genre_demand: float,
    rng: random.Random,
    era_multiplier: float = 1.0,
    cliche_penalty: float = 0.0,
    palette_audience_effect: float = 0.0,
    palette_critic_effect: float = 0.0,
) -> ReceptionResult:
    post_luck = rng.gauss(POST_LUCK_MEAN, POST_LUCK_SD)
    project_quality = clamp(
        PQ_SCRIPT * script_quality
        + PQ_DIRECTOR_SKILL * director_skill
        + PQ_ENSEMBLE * ensemble
        + PQ_PRODUCTION_VALUE * production_value(role_budget_millions)
        + PQ_POST_LUCK * post_luck,
        0.0, 100.0,
    )

    film_critic_score = clamp(
        project_quality
        + GENRE_CRITIC_BIAS.get(genre, 0.0)
        + CRITIC_DIRECTOR_PRESTIGE_COEF * (director_prestige - CRITIC_DIRECTOR_PRESTIGE_CENTRE)
        - staleness_penalty
        - cliche_penalty
        + palette_critic_effect
        + rng.gauss(0.0, CRITIC_NOISE_SD),
        0.0, 100.0,
    )

    # AudienceScore weights match callback-sim.py's tuned constants (§4.10, ported directly).
    audience_score = clamp(
        0.62 * project_quality
        + 0.17 * genre_demand
        + 0.11 * cast_star_power
        + 0.06 * (100.0 - project_quality)
        + palette_audience_effect
        + rng.gauss(0.0, 4.5),
        0.0, 100.0,
    )

    budget = role_budget_millions / era_multiplier
    marketing = BREAK_EVEN_MARKETING_SHARE * budget
    break_even = budget * (1.0 + BREAK_EVEN_MARKETING_SHARE) / RIGHTS_SHARE
    opening = budget * (OPENING_BASE + OPENING_STAR_POWER_COEF * cast_star_power + OPENING_DEMAND_COEF * genre_demand) * (max(budget, 0.01) / 30.0) ** OPENING_BUDGET_EXPONENT
    zeitgeist = audience_score + ZEITGEIST_DEMAND_COEF * (genre_demand - 50.0) + rng.gauss(0.0, ZEITGEIST_NOISE_SD)
    legs = clamp(
        LEGS_BASE
        + LEGS_AUDIENCE_COEF * (audience_score - LEGS_AUDIENCE_CENTRE)
        + LEGS_ZEITGEIST_COEF * max(0.0, zeitgeist - LEGS_ZEITGEIST_THRESHOLD) ** 1.5,
        LEGS_LO, LEGS_HI,
    )
    gross = opening * legs
    roi = (RIGHTS_SHARE * gross) / (budget + marketing) if (budget + marketing) > 0 else 0.0

    return ReceptionResult(
        project_quality=project_quality,
        film_critic_score=film_critic_score,
        audience_score=audience_score,
        budget=budget,
        break_even=break_even,
        opening=opening,
        zeitgeist=zeitgeist,
        legs=legs,
        gross=gross,
        roi=roi,
    )
