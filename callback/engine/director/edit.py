"""design/part-07-the-director.md §7.1 — "The edit is a decision you make. You roll it, and you
can steer the mean." Where an actor's film gets PostLuck ~ N(52, 14) blindly (actor/reception.py),
a director's own film lets Craft/Efficiency shift that mean before the roll.
"""
from __future__ import annotations

import random

from callback.engine.actor.reception import POST_LUCK_MEAN, POST_LUCK_SD
from callback.engine.core.util import clamp

STEER_CRAFT_COEF = 0.12
STEER_EFFICIENCY_COEF = 0.06
STEER_CAP = 12.0  # a director can move the mean, not guarantee the outcome


def steered_post_luck(craft: float, efficiency: float, rng: random.Random) -> float:
    shift = clamp(STEER_CRAFT_COEF * (craft - 50.0) + STEER_EFFICIENCY_COEF * (efficiency - 50.0), -STEER_CAP, STEER_CAP)
    return rng.gauss(POST_LUCK_MEAN + shift, POST_LUCK_SD)
