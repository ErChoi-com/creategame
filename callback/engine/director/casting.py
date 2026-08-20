"""design/part-07-the-director.md §7.1/§7.5 — "Casting is a gate you try to pass (actor) -> You
operate the gate (director): you run the utility function in §4.4 from the other side," and the
five real, in-project choices §7.5 builds on top of that reuse — each a genuine trade on the
eventual film's cast_star_power/fit/chaos, and for a bankable pick, the budget tier itself (§7.5's
own maxBudget formula) — not a blind sample the way an NPC-directed project still is.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.offers import Role, utility
from callback.engine.actor.persona import Persona
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp


def evaluate_candidate(
    candidate_attrs: Attributes,
    candidate_persona: Persona,
    candidate_standing: StandingModel,
    role: Role,
    candidate_age: int,
    candidate_quote: float,
) -> float:
    """The director's read on a candidate actor for a role — literally actor.offers.utility(),
    run with the candidate as the subject rather than the player. No new formula: this is a thin,
    discoverable wrapper naming that reuse, not a second Utility."""
    return utility(candidate_attrs, candidate_persona, candidate_standing, role, candidate_age, candidate_quote)


BANKABLE_WRONG_FIT = "bankable_wrong_fit"
RIGHT_ACTOR_NO_HEAT = "right_actor_no_heat"
DISCOVERY = "discovery"
YOUR_ROSTER = "your_roster"
DIFFICULT_GENIUS = "difficult_genius"

CASTING_CHOICES = (BANKABLE_WRONG_FIT, RIGHT_ACTOR_NO_HEAT, DISCOVERY, YOUR_ROSTER, DIFFICULT_GENIUS)

# §7.5's own budget-unlock formula — bankability is literally how films get financed.
MAX_BUDGET_COEF = 3.0
MAX_BUDGET_EXP_COEF = 0.041


def max_budget_from_bankability(bankability: float) -> float:
    return MAX_BUDGET_COEF * math.exp(MAX_BUDGET_EXP_COEF * clamp(bankability, 0.0, 100.0))


FIT_PENALTY_WRONG_FIT = 18.0
DISCOVERY_MEAN = 35.0
DISCOVERY_VARIANCE_SD = 22.0
DIFFICULT_GENIUS_CHAOS = 0.15


@dataclass(frozen=True)
class CastingOutcome:
    choice: str
    cast_star_power: float
    fit_penalty: float
    chaos_delta: float
    reliable: bool  # "your roster" — a real Chemistry bonus, below-quote cost


def resolve_casting(choice: str, candidate_bankability: float, rng: random.Random) -> CastingOutcome:
    """candidate_bankability: the attached/considered actor's own Bankability (0-100) — for
    "discovery", this is ignored in favour of real, high-variance sampling instead (nobody knows
    what an unknown will do)."""
    b = clamp(candidate_bankability, 0.0, 100.0)
    if choice == BANKABLE_WRONG_FIT:
        return CastingOutcome(choice, cast_star_power=b, fit_penalty=FIT_PENALTY_WRONG_FIT, chaos_delta=0.0, reliable=False)
    if choice == RIGHT_ACTOR_NO_HEAT:
        return CastingOutcome(choice, cast_star_power=clamp(b * 0.4, 0.0, 100.0), fit_penalty=0.0, chaos_delta=0.0, reliable=False)
    if choice == DISCOVERY:
        star_power = clamp(rng.gauss(DISCOVERY_MEAN, DISCOVERY_VARIANCE_SD), 0.0, 100.0)
        return CastingOutcome(choice, cast_star_power=star_power, fit_penalty=0.0, chaos_delta=0.0, reliable=False)
    if choice == YOUR_ROSTER:
        return CastingOutcome(choice, cast_star_power=b, fit_penalty=0.0, chaos_delta=0.0, reliable=True)
    if choice == DIFFICULT_GENIUS:
        return CastingOutcome(choice, cast_star_power=b, fit_penalty=0.0, chaos_delta=DIFFICULT_GENIUS_CHAOS, reliable=False)
    raise ValueError(f"unknown casting choice: {choice}")
