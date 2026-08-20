"""design/part-07-the-director.md §7.1/§7.7 — "The edit is a decision you make. You roll it, and
you can steer the mean." Where an actor's film gets PostLuck ~ N(52, 14) blindly (actor/reception.py),
a director's own film lets Craft/Efficiency shift that mean before the roll — and, per §7.7, who
actually holds final cut decides whose roll (or what blend of the two) counts.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.actor.reception import POST_LUCK_MEAN, POST_LUCK_SD
from callback.engine.core.util import clamp

STEER_CRAFT_COEF = 0.12
STEER_EFFICIENCY_COEF = 0.06
STEER_CAP = 12.0  # a director can move the mean, not guarantee the outcome


def steered_post_luck(craft: float, efficiency: float, rng: random.Random) -> float:
    shift = clamp(STEER_CRAFT_COEF * (craft - 50.0) + STEER_EFFICIENCY_COEF * (efficiency - 50.0), -STEER_CAP, STEER_CAP)
    return rng.gauss(POST_LUCK_MEAN + shift, POST_LUCK_SD)


# §7.7 — final cut is earned, not bought.
FINAL_CUT_PRESTIGE_THRESHOLD = 70.0
FINAL_CUT_CONSECUTIVE_PROFITABLE = 2


def has_final_cut(prestige: float, consecutive_profitable_films: int, took_fee_cut: bool) -> bool:
    return (
        prestige > FINAL_CUT_PRESTIGE_THRESHOLD
        or consecutive_profitable_films >= FINAL_CUT_CONSECUTIVE_PROFITABLE
        or took_fee_cut
    )


# The studio's own roll is biased commercial — §7.7's text names a separate +Audience/-Critic
# split, but post_luck_override is a single scalar in this engine's reception.py; a real two-channel
# split would mean breaking that term in two inside reception.py itself, out of scope for this pass.
# This collapses to one modest net-commercial shift instead — a known, named simplification, not a
# silent one.
STUDIO_ROLL_BIAS = 4.0
DIRECTOR_ROLL_WEIGHT = 0.45
STUDIO_ROLL_WEIGHT = 0.55
TEST_SCREENING_BAD_THRESHOLD = 45.0  # a blended PostLuck below this reads as a bad test score


def studio_post_luck(rng: random.Random) -> float:
    return rng.gauss(POST_LUCK_MEAN + STUDIO_ROLL_BIAS, POST_LUCK_SD)


def blended_post_luck(your_roll: float, studio_roll: float) -> float:
    return DIRECTOR_ROLL_WEIGHT * your_roll + STUDIO_ROLL_WEIGHT * studio_roll


@dataclass(frozen=True)
class EditOutcome:
    post_luck: float
    reshot: bool


def resolve_edit(
    craft: float, efficiency: float, has_cut: bool, contested: bool, rng: random.Random,
) -> EditOutcome:
    """has_cut=True: the director's own steered_post_luck() alone. has_cut=False, contested=False:
    the studio's own roll alone (they simply have it, no negotiation). contested=True: the blended
    roll, re-rolled at most once — a second bad test score locks in the worse result rather than
    triggering another round (§7.7 v10's own reshoot cap; a loop with no cap isn't a decision)."""
    your_roll = steered_post_luck(craft, efficiency, rng)
    if has_cut:
        return EditOutcome(post_luck=your_roll, reshot=False)
    if not contested:
        return EditOutcome(post_luck=studio_post_luck(rng), reshot=False)

    blended = blended_post_luck(your_roll, studio_post_luck(rng))
    if blended < TEST_SCREENING_BAD_THRESHOLD:
        reshot_roll = blended_post_luck(steered_post_luck(craft, efficiency, rng), studio_post_luck(rng))
        return EditOutcome(post_luck=reshot_roll, reshot=True)
    return EditOutcome(post_luck=blended, reshot=False)
