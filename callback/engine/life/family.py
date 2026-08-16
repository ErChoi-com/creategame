"""design/part-11-the-life.md §11.4 — family, and the caretaking block."""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

OUTSIDE, INSIDE = "outside", "inside"

PARTNER_OUTSIDE_RESILIENCE_FLOOR = 10.0
PARTNER_INSIDE_SCANDAL_MULTIPLIER = 2.0
CHILD_RESILIENCE_FLOOR = 6.0
FRIENDS_RESILIENCE_ANCHOR = 8.0  # "the strongest Resilience anchor available"

CARETAKING_REFUSAL_RESILIENCE_COST = 8.0
# §11.4's example is "a 47-year-old actor" — aging-parent caretaking risk rises with the actor's
# own age. Nothing previously set caretaking_load; this is the trigger that was missing.
CARETAKING_BASE_CHANCE = 0.015
CARETAKING_AGE_START = 40
CARETAKING_AGE_CHANCE_COEF = 0.004

# §11.4's second-generation transfer — deliberately a harder cut than §7.11's career-switch
# transfer (Rolodex 100%, Prestige 60%, Heat 35%, Affection 80% there).
SECOND_GEN_ROLODEX_TRANSFER = 0.70
SECOND_GEN_PRESTIGE_TRANSFER = 0.0  # not carried — a new career starts on its own merit
SECOND_GEN_NEPOTISM_PENALTY = -15.0
SECOND_GEN_NEPOTISM_CLEAR_NOTICES = 82.0


@dataclass(frozen=True)
class FamilyState:
    partner: str | None = None
    partner_in_industry: bool = False
    children: int = 0
    caretaking_load: int = 0  # blocks/yr consumed by aging parents
    has_close_friends: bool = True

    def resilience_floor(self) -> float:
        floor = 0.0
        if self.partner == OUTSIDE:
            floor = max(floor, PARTNER_OUTSIDE_RESILIENCE_FLOOR)
        if self.children > 0:
            floor = max(floor, CHILD_RESILIENCE_FLOOR)
        if self.has_close_friends:
            floor = max(floor, FRIENDS_RESILIENCE_ANCHOR)
        return floor

    def scandal_exposure_multiplier(self) -> float:
        return PARTNER_INSIDE_SCANDAL_MULTIPLIER if self.partner_in_industry else 1.0


def refuse_caretaking(family: FamilyState) -> tuple[FamilyState, float]:
    """Returns (new_family, resilience_cost). Refusing costs Resilience and generates guilt
    events (the event itself is a caller/UI concern); this just clears the load."""
    return replace(family, caretaking_load=0), CARETAKING_REFUSAL_RESILIENCE_COST


def maybe_generate_caretaking(family: FamilyState, age: int, rng: random.Random) -> FamilyState:
    """One year's chance of a caretaking block appearing, if there isn't one already — "no
    villain, no scandal, just arithmetic." Rises with age past 40."""
    if family.caretaking_load > 0:
        return family
    chance = CARETAKING_BASE_CHANCE + CARETAKING_AGE_CHANCE_COEF * max(0, age - CARETAKING_AGE_START)
    if rng.random() < chance:
        return replace(family, caretaking_load=rng.choice([1, 2]))
    return family


def nepotism_penalty_cleared(your_notices: float) -> bool:
    return your_notices > SECOND_GEN_NEPOTISM_CLEAR_NOTICES
