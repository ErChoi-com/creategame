"""design/part-07-the-director.md §7.3 — DirectorSkill: the bridge to the actor model.

DirectorPrestige/DirectorStanding are not parallel stats invented for this Part — they're the
same Standing meters actor/standing.py already defines, read for whoever is directing. This
module configures no new Standing model; callers use actor.standing.new_standing_model() /
StandingModel for a director's own Standing exactly as they would for an actor's.
"""
from __future__ import annotations

import random

from callback.engine.core.util import clamp
from callback.engine.director.attributes import DirectorAttributes

VISION_WEIGHT = 0.34
COMMAND_WEIGHT = 0.28
CRAFT_WEIGHT = 0.38
NOISE_SD = 11.0

ENGAGEMENT_PASSION_PROJECT = 6.0
ENGAGEMENT_PAYCHECK = -8.0


def engagement_modifier(passion_project: bool) -> float:
    return ENGAGEMENT_PASSION_PROJECT if passion_project else ENGAGEMENT_PAYCHECK


def director_skill(attrs: DirectorAttributes, passion_project: bool, rng: random.Random) -> float:
    base = VISION_WEIGHT * attrs.vision + COMMAND_WEIGHT * attrs.command + CRAFT_WEIGHT * attrs.craft
    return clamp(base + engagement_modifier(passion_project) + rng.gauss(0.0, NOISE_SD), 0.0, 100.0)
