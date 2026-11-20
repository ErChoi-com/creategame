"""design/part-04-the-actor.md §4.7 — the shoot & the Performance roll.

Performance is private: the caller may report a qualitative, confidence-graded estimate of it to
a player, but the number itself is never revealed within a run. This module just resolves it.

Condition (§11.1 — health, burnout debt, substance load, Resilience) is part of the Life layer,
out of this pass's scope; resolve_performance takes `condition` as a direct 0-100 input rather
than computing it, with a documented healthy-baseline default for callers that don't have a Life
layer yet.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.actor.attributes import Attributes
from callback.engine.core.util import clamp

BASE_CRAFT = 0.28
BASE_INSTINCT = 0.18
BASE_PRESENCE = 0.16
BASE_FIT = 0.16
BASE_PREP = 0.12
BASE_CHEMISTRY = 0.10
BASE_DIRECTOR_COMMAND = 0.06
DIRECTOR_COMMAND_CENTRE = 50.0

DIRECTION_MULT_BASE = 0.86
DIRECTION_MULT_COEF = 0.0028

CONDITION_MULT_BASE = 0.80
CONDITION_MULT_COEF = 0.0020
DEFAULT_CONDITION = 78.0  # a healthy baseline, absent a Life-layer Condition model

ROLL_SIGMA_BASE = 16.0
ROLL_SIGMA_CRAFT_COEF = 0.09  # craft = consistency

TRANSCENDENCE_INSTINCT_DIVISOR = 320.0
TRANSCENDENCE_LO = 9.0
TRANSCENDENCE_HI = 26.0


@dataclass(frozen=True)
class PerformanceResult:
    performance: float
    base: float
    direction_mult: float
    condition_mult: float
    roll: float
    transcendent: bool


def resolve_performance(
    attrs: Attributes,
    fit: float,
    prep: float,
    chemistry: float,
    director_command: float,
    director_skill: float,
    rng: random.Random,
    condition: float = DEFAULT_CONDITION,
) -> PerformanceResult:
    base = (
        BASE_CRAFT * attrs.craft
        + BASE_INSTINCT * attrs.instinct
        + BASE_PRESENCE * attrs.presence
        + BASE_FIT * fit
        + BASE_PREP * prep
        + BASE_CHEMISTRY * chemistry
        + BASE_DIRECTOR_COMMAND * (director_command - DIRECTOR_COMMAND_CENTRE)
    )
    direction_mult = DIRECTION_MULT_BASE + DIRECTION_MULT_COEF * director_skill
    condition_mult = CONDITION_MULT_BASE + CONDITION_MULT_COEF * condition

    sigma = max(0.1, ROLL_SIGMA_BASE - ROLL_SIGMA_CRAFT_COEF * attrs.craft)
    roll = rng.gauss(0.0, sigma)

    performance = base * direction_mult * condition_mult + roll

    transcendent = rng.random() < attrs.instinct / TRANSCENDENCE_INSTINCT_DIVISOR
    if transcendent:
        performance += rng.uniform(TRANSCENDENCE_LO, TRANSCENDENCE_HI)

    performance = clamp(performance, 0.0, 100.0)

    return PerformanceResult(
        performance=performance,
        base=base,
        direction_mult=direction_mult,
        condition_mult=condition_mult,
        roll=roll,
        transcendent=transcendent,
    )
