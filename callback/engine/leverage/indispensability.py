"""design/part-06-leverage.md §6.4-6.5 — Indispensability, RecastCost, and the holdout.

The v9 fix this module must not regress: Indispensability has to be able to fall all the way to
zero (decay runs at every level once a property is live, not gated behind "still above 30") or a
finished franchise stays open forever, silently blocking every franchise after it.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.core.util import clamp, sigmoid

CHARACTER_ID_WEIGHT = 0.35
INSTALLMENTS_WEIGHT = 0.25
INSTALLMENTS_COEF = 22.0
STAR_POWER_WEIGHT = 0.20
CONTRACTUAL_HOLD_WEIGHT = 0.20

RECAST_COST_COEF = 0.55

# §6.4's v9 fix — decay always runs, not gated behind a "still above 30" threshold.
INDISPENSABILITY_DECAY = 0.92  # per year the property is dormant (no installment)
INDISPENSABILITY_FLOOR_RELEASE = 8.0  # below this, the property releases you entirely

# The holdout (§6.5).
HOLDOUT_PAY_CAP = 0.85
HOLDOUT_PAY_SLOPE = 0.085
HOLDOUT_PAY_CENTRE = 58.0
HOLDOUT_RECAST_CHANCE = 0.65
HOLDOUT_RAISE_BASE = 1.35
HOLDOUT_RAISE_COEF = 0.013
HOLDOUT_RAISE_CENTRE = 50.0
HOLDOUT_RAISE_CAP = 2.40
HOLDOUT_FAILURE_NOTORIETY = 15.0
HOLDOUT_REPEAT_PENALTY = -8.0


def character_identification(prior: float, notices_this_installment: float, memorability: float) -> float:
    """Grows with installments, with Notices in the role, and with the character's memorability.
    design/ doesn't publish an exact growth formula beyond "grows with" these three; this pass's
    documented reading is an additive nudge, capped 0-100."""
    growth = 0.15 * max(0.0, notices_this_installment - 50.0) + 0.10 * memorability
    return clamp(prior + growth, 0.0, 100.0)


def indispensability(
    character_id: float,
    installments_starred: int,
    your_star_power: float,
    cast_average_star_power: float,
    contractual_hold: float,
) -> float:
    star_power_term = clamp(50.0 * (your_star_power / max(1.0, cast_average_star_power)), 0.0, 100.0)
    return clamp(
        CHARACTER_ID_WEIGHT * character_id
        + INSTALLMENTS_WEIGHT * min(100.0, INSTALLMENTS_COEF * installments_starred)
        + STAR_POWER_WEIGHT * star_power_term
        + CONTRACTUAL_HOLD_WEIGHT * contractual_hold,
        0.0, 100.0,
    )


def recast_cost(indispensability_value: float) -> float:
    return RECAST_COST_COEF * indispensability_value


def decay_dormant(indispensability_value: float) -> tuple[float, bool]:
    """One year of a property sitting dormant. Returns (new_value, released) — released is True
    once the value crosses the floor, at which point the franchise lets the actor go entirely
    (the v9 fix: this must run unconditionally, never gated on the value already being high)."""
    new_value = indispensability_value * INDISPENSABILITY_DECAY
    return new_value, new_value < INDISPENSABILITY_FLOOR_RELEASE


@dataclass(frozen=True)
class HoldoutResult:
    they_paid: bool
    recast: bool  # only meaningful if they_paid is False
    raise_multiplier: float
    notoriety_delta: float


def resolve_holdout(indispensability_value: float, prior_holdouts: int, rng: random.Random) -> HoldoutResult:
    effective_indispensability = indispensability_value + HOLDOUT_REPEAT_PENALTY * prior_holdouts
    p_pay = HOLDOUT_PAY_CAP * sigmoid(HOLDOUT_PAY_SLOPE * (effective_indispensability - HOLDOUT_PAY_CENTRE))
    they_paid = rng.random() < p_pay

    if they_paid:
        raise_mult = min(
            HOLDOUT_RAISE_BASE + HOLDOUT_RAISE_COEF * (effective_indispensability - HOLDOUT_RAISE_CENTRE),
            HOLDOUT_RAISE_CAP,
        )
        return HoldoutResult(they_paid=True, recast=False, raise_multiplier=raise_mult, notoriety_delta=0.0)

    recast = rng.random() < HOLDOUT_RECAST_CHANCE
    return HoldoutResult(they_paid=False, recast=recast, raise_multiplier=1.0,
                          notoriety_delta=HOLDOUT_FAILURE_NOTORIETY if recast else 0.0)
