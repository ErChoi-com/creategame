"""design/part-04-the-actor.md §4.10 — Reception: the decoupling.

Takes Spotlight/CraftContribution from actor/shape.py rather than recomputing them — §4.10's own v9 note
states there is now exactly one code path producing those two numbers, and this module is the
consumer, not a second producer.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from callback.engine.core.util import clamp
from callback.engine.genre.hybrids import HYBRID_MARKETING_PENALTY, hybrid_critic_bonus

# ProjectQuality weights.
PQ_SCRIPT = 0.31
PQ_DIRECTOR_SKILL = 0.22
PQ_CRAFT_CONTRIBUTION = 0.29
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
# v21 — director_spectacle_bonus is already pre-scaled to a 0-12 range (director.development.
# director_spectacle_bonus), not the 0-100 scale star_power/genre_demand use — this coefficient
# is picked so its max contribution to the bracket (~0.42) lands in the same order as star_power/
# demand's own max (~0.5 each), a real but not dominant addition.
OPENING_DIRECTOR_SPECTACLE_COEF = 0.035

# An animated film's opening is driven by brand/franchise/genre appeal, not any one voice
# performer's own draw — audiences turn out for "the new Pixar movie," not for whoever's speaking.
# Real, different economics from live action: star power matters far less, genre demand matters
# more, at the same total weight (so this isn't just "animation opens bigger," it's a genuinely
# different mix of what's actually driving the number).
ANIMATION_OPENING_STAR_POWER_COEF = 0.001
ANIMATION_OPENING_DEMAND_COEF = 0.009
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
    budget: float  # production budget — never includes marketing
    marketing: float  # a separate spend, tracked in its own right, not folded silently into budget
    break_even: float
    opening: float
    zeitgeist: float
    legs: float
    gross: float
    roi: float


def resolve_reception(
    script_quality: float,
    director_skill: float,
    craft_contribution: float,
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
    marketing_share: float | None = None,
    rights_share: float | None = None,
    opening_marketing_coef: float = 0.0,
    post_luck_override: float | None = None,
    is_animation: bool = False,
    director_spectacle_bonus: float = 0.0,
    cost_budget_millions: float | None = None,
    is_hybrid: bool = False,
) -> ReceptionResult:
    """marketing_share/rights_share: a producing studio's own money terms (actor/studios.py),
    overriding this module's flat BREAK_EVEN_MARKETING_SHARE/RIGHTS_SHARE defaults when given.
    opening_marketing_coef: how much a marketing_share above baseline buys extra opening-weekend
    visibility (actor/studios.OPENING_MARKETING_COEF) — 0.0 leaves Opening exactly as before.
    post_luck_override: director/edit.py's steered_post_luck() — a director's own Craft/Efficiency
    shifting PostLuck's mean before the roll (§7.1), in place of this module's blind N(52, 14)
    sample. None (the actor path) leaves PostLuck exactly as before.
    is_animation: swaps in ANIMATION_OPENING_STAR_POWER_COEF/ANIMATION_OPENING_DEMAND_COEF for
    Opening only — quality/critic/audience formulas are untouched, this is purely a box-office-mix
    difference (see the module-level note on those two constants).
    director_spectacle_bonus: director.development.director_spectacle_bonus(vision) — v21, a
    director's own scale/ambition selling tickets on spectacle alone, same shape as star_power/
    genre_demand just below but Vision-sourced. Reaches Opening ONLY, never project_quality or
    audience_score/critic_score — 0.0 (every non-director call site) leaves this exactly as
    before.
    cost_budget_millions: the REAL money actually spent — separate from role_budget_millions (the
    film's own planned/perceived scale) specifically so a schedule overrun (director.shoot_style.
    overage_percent, folded into simulation._director's effective_budget) can be a pure cost with
    no quiet upside. Before this parameter existed, callers fed the SAME overrun-inflated number
    into role_budget_millions for everything at once — which meant an overrun also bought a real,
    unintended bump to production_value() (a real term in project_quality) and to Opening (which
    scales close to linearly with budget), both net-positive, while only break_even/ROI read it as
    a cost. The two positive channels reliably outweighed the one negative one for a director
    whose underlying craft was already strong — the opposite of the design's own stated intent
    ("a real, felt cost"). None (every existing caller) means cost_budget_millions == role_budget_
    millions, an identity fallback that leaves every non-director call site's behavior unchanged.
    Only marketing/break_even/roi/ReceptionResult.budget (the real financial ledger) read the cost
    figure; production_value()/Opening (perception — what the film reads as being worth, to
    critics and audiences alike) keep reading role_budget_millions, the film's planned scale.
    is_hybrid: design/part-09 §9.2 — Role.secondary_genre is set (genre_demand has already been
    averaged with the secondary genre's own demand by the caller, since only genre_heat has both
    genres' numbers). Applies the flat, genre-independent −8 marketing penalty to Opening
    unconditionally and the +6 critic bonus only once project_quality clears 70 — the bonus is
    gated here, not by the caller, because project_quality isn't known until this function
    computes it. False (every existing caller) leaves this exactly as before."""
    post_luck = post_luck_override if post_luck_override is not None else rng.gauss(POST_LUCK_MEAN, POST_LUCK_SD)
    project_quality = clamp(
        PQ_SCRIPT * script_quality
        + PQ_DIRECTOR_SKILL * director_skill
        + PQ_CRAFT_CONTRIBUTION * craft_contribution
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
        + (hybrid_critic_bonus(project_quality) if is_hybrid else 0.0)
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

    m_share = marketing_share if marketing_share is not None else BREAK_EVEN_MARKETING_SHARE
    r_share = rights_share if rights_share is not None else RIGHTS_SHARE

    # `budget` (perception — what the film reads as being worth) drives production_value() above
    # and Opening below; `cost` (the real financial ledger — overrun included) drives marketing
    # dollars, break_even, ROI, and ReceptionResult.budget. Identical when cost_budget_millions
    # isn't given (every non-director caller), so this is a pure split, not a behavior change,
    # for anyone who doesn't pass the new parameter.
    budget = role_budget_millions / era_multiplier
    cost = (cost_budget_millions if cost_budget_millions is not None else role_budget_millions) / era_multiplier
    marketing = m_share * cost
    break_even = cost * (1.0 + m_share) / r_share
    star_power_coef = ANIMATION_OPENING_STAR_POWER_COEF if is_animation else OPENING_STAR_POWER_COEF
    demand_coef = ANIMATION_OPENING_DEMAND_COEF if is_animation else OPENING_DEMAND_COEF
    opening = budget * (
        OPENING_BASE + star_power_coef * cast_star_power + demand_coef * genre_demand
        + opening_marketing_coef * (m_share - BREAK_EVEN_MARKETING_SHARE)
        + OPENING_DIRECTOR_SPECTACLE_COEF * director_spectacle_bonus
        + (HYBRID_MARKETING_PENALTY / 100.0 if is_hybrid else 0.0)
    ) * (max(budget, 0.01) / 30.0) ** OPENING_BUDGET_EXPONENT
    zeitgeist = audience_score + ZEITGEIST_DEMAND_COEF * (genre_demand - 50.0) + rng.gauss(0.0, ZEITGEIST_NOISE_SD)
    legs = clamp(
        LEGS_BASE
        + LEGS_AUDIENCE_COEF * (audience_score - LEGS_AUDIENCE_CENTRE)
        + LEGS_ZEITGEIST_COEF * max(0.0, zeitgeist - LEGS_ZEITGEIST_THRESHOLD) ** 1.5,
        LEGS_LO, LEGS_HI,
    )
    gross = opening * legs
    roi = (r_share * gross) / (cost + marketing) if (cost + marketing) > 0 else 0.0

    return ReceptionResult(
        project_quality=project_quality,
        film_critic_score=film_critic_score,
        audience_score=audience_score,
        budget=cost,
        marketing=marketing,
        break_even=break_even,
        opening=opening,
        zeitgeist=zeitgeist,
        legs=legs,
        gross=gross,
        roi=roi,
    )
