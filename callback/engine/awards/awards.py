"""design/part-04-the-actor.md §4.11 — BuzzScore, narrative bonuses, category strategy, vote
splitting, campaign cost. "Awards do not reward being good; they reward being seen to be good" —
BuzzScore reads YourNotices, not the hidden Performance number.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.core.util import clamp

BUZZ_NOTICES_WEIGHT = 0.34
BUZZ_CRITIC_WEIGHT = 0.20
BUZZ_CAMPAIGN_WEIGHT = 0.14
BUZZ_PRESTIGE_WEIGHT = 0.12
BUZZ_NARRATIVE_WEIGHT = 0.10
BUZZ_CATEGORY_WEIGHT = 0.10
BUZZ_NOISE_SD = 9.0

CAMPAIGN_COST_LO = 0.4  # $M
CAMPAIGN_COST_HI = 3.0

CATEGORY_ADVANTAGE_LEAD_IN_SUPPORTING = 18.0
CATEGORY_FRAUD_CAUGHT_CHANCE = 0.35
CATEGORY_FRAUD_NOTORIETY = 6.0

VOTE_SPLITTING_PENALTY = -9.0

NARRATIVE_BONUSES = {
    "shes_due": 14.0,
    "transformation": 12.0,
    "comeback": 11.0,
    "final_bow": 10.0,
    "newcomer": 8.0,
    "posthumous": 20.0,
    "too_commercial": -10.0,
    "overexposed": -7.0,
}


@dataclass(frozen=True)
class NarrativeContext:
    prior_nominations: int = 0
    prior_wins: int = 0
    transformation_flag: bool = False
    heat_years_below_25: int = 0
    age: int = 30
    announced_retirement: bool = False
    is_first_nomination: bool = False
    posthumous: bool = False
    tentpoles_last_3_years: int = 0
    credits_this_season: int = 1


def narrative_bonus(ctx: NarrativeContext) -> float:
    """Multiple flags can be true at once; design/ presents them as a lookup table, not a stack —
    this pass's reading takes the single largest-magnitude applicable bonus (a career doesn't get
    both "the comeback" and "the final bow" bonus stacked in the same season)."""
    applicable = []
    if ctx.posthumous:
        applicable.append(NARRATIVE_BONUSES["posthumous"])
    if ctx.prior_nominations >= 3 and ctx.prior_wins == 0:
        applicable.append(NARRATIVE_BONUSES["shes_due"])
    if ctx.transformation_flag:
        applicable.append(NARRATIVE_BONUSES["transformation"])
    if ctx.heat_years_below_25 >= 4:
        applicable.append(NARRATIVE_BONUSES["comeback"])
    if ctx.age >= 70 or ctx.announced_retirement:
        applicable.append(NARRATIVE_BONUSES["final_bow"])
    if ctx.is_first_nomination and ctx.age < 28:
        applicable.append(NARRATIVE_BONUSES["newcomer"])
    if ctx.tentpoles_last_3_years >= 2:
        applicable.append(NARRATIVE_BONUSES["too_commercial"])
    if ctx.credits_this_season >= 4:
        applicable.append(NARRATIVE_BONUSES["overexposed"])
    if not applicable:
        return 0.0
    return max(applicable, key=abs)


def category_fraud(rng: random.Random) -> tuple[float, bool, float]:
    """Lead-in-supporting campaign strategy. Returns (category_advantage, caught, notoriety_delta)."""
    caught = rng.random() < CATEGORY_FRAUD_CAUGHT_CHANCE
    notoriety_delta = CATEGORY_FRAUD_NOTORIETY if caught else 0.0
    return CATEGORY_ADVANTAGE_LEAD_IN_SUPPORTING, caught, notoriety_delta


def buzz_score(
    your_notices: float,
    film_critic_score: float,
    campaign_spend: float,
    prestige: float,
    narrative_bonus_value: float,
    category_advantage: float,
    rng: random.Random,
) -> float:
    return clamp(
        BUZZ_NOTICES_WEIGHT * your_notices
        + BUZZ_CRITIC_WEIGHT * film_critic_score
        + BUZZ_CAMPAIGN_WEIGHT * campaign_spend
        + BUZZ_PRESTIGE_WEIGHT * prestige
        + BUZZ_NARRATIVE_WEIGHT * narrative_bonus_value
        + BUZZ_CATEGORY_WEIGHT * category_advantage
        + rng.gauss(0.0, BUZZ_NOISE_SD),
        0.0, 100.0,
    )


def apply_vote_splitting(buzz_scores: dict[str, float], same_film_candidate_ids: list[str]) -> dict[str, float]:
    if len(same_film_candidate_ids) < 2:
        return buzz_scores
    updated = dict(buzz_scores)
    for cid in same_film_candidate_ids:
        if cid in updated:
            updated[cid] = clamp(updated[cid] + VOTE_SPLITTING_PENALTY, 0.0, 100.0)
    return updated


def resolve_category(buzz_scores: dict[str, str | float], rng: random.Random) -> str:
    """buzz_scores: candidate_id -> BuzzScore. Highest wins; ties broken by rng, since a real
    vote tally isn't modeled at that resolution."""
    best = max(buzz_scores.values())
    winners = [cid for cid, score in buzz_scores.items() if score == best]
    return rng.choice(winners)
