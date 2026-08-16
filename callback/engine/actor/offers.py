"""design/part-04-the-actor.md §4.4 — the Offer Board & casting.

FitScore, Utility, offer probability, and casting-path resolution. RelationshipBonus is stubbed
at 0 (the Rolodex, §4.12, isn't modeled in this pass) but takes the real inputs already, so wiring
in the Rolodex later is additive, not a rewrite.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.persona import ARCHETYPES, GENRES, Persona
from callback.engine.actor.standing import GATEKEEPER_WEIGHTS
from callback.engine.actor.studios import pick_studio
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp, positive_part, sigmoid

# Utility formula weights (§4.4).
UTILITY_STANDING_WEIGHT = 0.40
UTILITY_FIT_WEIGHT = 0.35
UTILITY_ATTR_WEIGHT = 0.15
UTILITY_ATTR_CRAFT_SHARE = 0.6
UTILITY_ATTR_INSTINCT_SHARE = 0.4
UTILITY_OVERPRICE_COEF = 12.0

# ageMismatchPenalty constants.
AGE_MISMATCH_FREE_BAND = 4
AGE_MISMATCH_COEF = 2.2
AGE_MISMATCH_EXPONENT = 1.35
AGE_MISMATCH_CAP = 70.0
AGE_MISMATCH_YOUNGER_MULT = 1.6  # playing younger costs 1.6x more than playing older

# FitScore's genre/archetype terms.
TYPECASTING_PENALTY_COEF = 0.45

# P(offer) sigmoid slope.
OFFER_PROBABILITY_SLOPE = 0.11

# v9 fix (design/part-04 §4.4): the open-offer path fires above this Utility-minus-difficulty
# margin. The original spec used 25, which made this path unreachable in practice.
OPEN_OFFER_UTILITY_MARGIN = 14.0

# §4.0's non-union opening act.
NON_UNION_CREDIT_THRESHOLD = 3
NON_UNION_SUBSTITUTION_CHANCE = 0.25
NON_UNION_PAY_FRACTION = 1.0 / 3.0

BILLINGS = ("lead", "supporting", "bit", "extra")

# A film's total budget (§4.4's listing generator, this pass's reading — see sample_role's
# docstring): log-normal rather than a handful of fixed tiers, so nothing about the distribution
# a player sees is a hard-coded step function. Median lands near BUDGET_MEDIAN, and the tail can
# reach BUDGET_MAX (a real $300M tentpole) but only rarely — most films this samples are small.
BUDGET_MIN = 1.5
BUDGET_MAX = 300.0
BUDGET_MEDIAN = 12.0
BUDGET_LOGNORMAL_SIGMA = 1.15


def sample_budget_millions(rng: random.Random) -> float:
    return clamp(rng.lognormvariate(math.log(BUDGET_MEDIAN), BUDGET_LOGNORMAL_SIGMA), BUDGET_MIN, BUDGET_MAX)


@dataclass(frozen=True)
class Role:
    project_id: str
    genre: str
    archetype: str
    billing: str
    char_age: int
    type_strictness: float  # 0-1
    difficulty: float
    budget_for_role: float  # $M — the fee ceiling this role can pay
    gatekeeper: str  # key into standing.GATEKEEPER_WEIGHTS
    requirements: dict[str, float] = field(default_factory=dict)  # subset of voice/physicality/look
    union: bool = True
    studio: str = "mid_major"  # key into studios.STUDIOS — who's actually financing this film
    franchise_id: str | None = None  # set by simulation._franchises.maybe_attach_franchise
    installment_number: int = 0  # 0 = not a franchise entry; 1 = a new franchise; 2+ = a sequel


def age_mismatch_penalty(char_age: int, your_age: int) -> float:
    d = abs(char_age - your_age)
    if d <= AGE_MISMATCH_FREE_BAND:
        return 0.0
    penalty = AGE_MISMATCH_COEF * (d - AGE_MISMATCH_FREE_BAND) ** AGE_MISMATCH_EXPONENT
    if char_age < your_age:  # playing younger
        penalty *= AGE_MISMATCH_YOUNGER_MULT
    return min(penalty, AGE_MISMATCH_CAP)


def hard_gate_penalty(attrs: Attributes, requirements: dict[str, float]) -> float:
    """§4.4 names this term without a formula; shortfall-below-requirement, uncapped positive
    part, is this pass's documented reading — a role with no stated requirement costs nothing."""
    return sum(max(0.0, req - getattr(attrs, gate)) for gate, req in requirements.items())


def fit_score(attrs: Attributes, persona: Persona, role: Role, your_age: int) -> float:
    age_pen = age_mismatch_penalty(role.char_age, your_age)
    genre_pen = TYPECASTING_PENALTY_COEF * (100.0 - persona.genre_affinity.get(role.genre, 20.0)) * role.type_strictness
    archetype_pen = TYPECASTING_PENALTY_COEF * (100.0 - persona.archetype_affinity.get(role.archetype, 20.0)) * role.type_strictness
    gate_pen = hard_gate_penalty(attrs, role.requirements)
    return clamp(100.0 - age_pen - genre_pen - archetype_pen - gate_pen, 0.0, 100.0)


def relationship_bonus(rolodex_edges: list[tuple[float, float]] | None = None) -> float:
    """Σ 0.30·affinity − 0.55·grudge over Rolodex members attached to the production. The Rolodex
    (§4.12) isn't modeled in this pass; stubbed at 0 by default. Takes real (affinity, grudge)
    pairs so a future Rolodex module plugs in without changing this function's contract."""
    if not rolodex_edges:
        return 0.0
    return sum(0.30 * affinity - 0.55 * grudge for affinity, grudge in rolodex_edges)


def utility(
    attrs: Attributes,
    persona: Persona,
    standing_model: StandingModel,
    role: Role,
    your_age: int,
    quote_value: float,
    rolodex_edges: list[tuple[float, float]] | None = None,
    bypass_standing: bool = False,
) -> float:
    """bypass_standing: design/part-06 §6.6's "Screen-test for free" — "bypasses the Standing
    term in §4.4 entirely." Zeroes StandingScore's contribution rather than skipping the term
    structurally, so the rest of Utility's shape (Fit, attributes, relationships) is unchanged."""
    standing_score = 0.0 if bypass_standing else standing_model.weighted_score(GATEKEEPER_WEIGHTS[role.gatekeeper])
    fit = fit_score(attrs, persona, role, your_age)
    attr_term = UTILITY_ATTR_CRAFT_SHARE * attrs.craft + UTILITY_ATTR_INSTINCT_SHARE * attrs.instinct
    overage = min(quote_value / role.budget_for_role - 1.0, 1.0)
    overprice = UTILITY_OVERPRICE_COEF * positive_part(overage)
    return (
        UTILITY_STANDING_WEIGHT * standing_score
        + UTILITY_FIT_WEIGHT * fit
        + UTILITY_ATTR_WEIGHT * attr_term
        + relationship_bonus(rolodex_edges)
        - overprice
    )


def offer_probability(utility_value: float, difficulty: float) -> float:
    return sigmoid(OFFER_PROBABILITY_SLOPE * (utility_value - difficulty))


def resolve_casting_path(utility_value: float, role: Role) -> str:
    """"direct_offer" | "audition". §4.4's third path — a director's Rolodex affinity>70 handing
    you the part outright regardless of Standing — needs the Rolodex and is out of scope for this
    pass; not silently dropped, just not reachable until that module exists."""
    if utility_value - role.difficulty > OPEN_OFFER_UTILITY_MARGIN:
        return "direct_offer"
    return "audition"


def is_offered_non_union(credits: int, rng: random.Random) -> bool:
    """§4.0 — under 3 union credits, a union-eligible listing has a 25% chance of being offered
    non-union instead (paying NON_UNION_PAY_FRACTION as much)."""
    if credits >= NON_UNION_CREDIT_THRESHOLD:
        return False
    return rng.random() < NON_UNION_SUBSTITUTION_CHANCE


def sample_role(rng: random.Random, budget_millions: float | None = None) -> Role:
    """A minimal role-listing generator for simulation/career.py's headless loop. This is not the
    full offer-board content system (§4.4's own listing generator reads the world's production
    pipeline, §10.0 — out of scope here); it draws a plausible role so casting/Utility can be
    exercised end to end."""
    genre = rng.choice(GENRES)
    archetype = rng.choice(ARCHETYPES)
    billing = rng.choices(BILLINGS[:3], weights=[0.15, 0.45, 0.40])[0]  # leads are rarer to land
    budget = budget_millions if budget_millions is not None else sample_budget_millions(rng)
    gatekeeper = rng.choice(list(GATEKEEPER_WEIGHTS.keys()))
    studio = pick_studio(budget, rng).id  # who's financing scales with the film's own budget, not the role's fee
    return Role(
        project_id=f"p_{rng.randrange(10**6):06d}",
        genre=genre,
        archetype=archetype,
        billing=billing,
        char_age=int(clamp(rng.gauss(38, 12), 8, 85)),
        type_strictness=clamp(rng.gauss(0.6, 0.2), 0.0, 1.0),
        difficulty=clamp(rng.gauss(50, 15), 5, 95),
        budget_for_role=budget * rng.uniform(0.05, 0.35),  # this role's fee ceiling vs. total budget
        gatekeeper=gatekeeper,
        studio=studio,
    )
