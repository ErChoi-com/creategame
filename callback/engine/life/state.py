"""Combines health/addiction/family/money into one LifeState with a yearly advance step —
the life-layer analogue of simulation/career.py's simulate_year().
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.life.addiction import AddictionState, advance as advance_addiction, advance_recovery
from callback.engine.life.family import FamilyState, maybe_generate_caretaking
from callback.engine.life.health import HealthState, after_idle_year, condition
from callback.engine.life.money import MoneyState, apply_year as apply_money_year


@dataclass(frozen=True)
class LifeState:
    health: HealthState = field(default_factory=HealthState)
    addiction: AddictionState = field(default_factory=AddictionState)
    family: FamilyState = field(default_factory=FamilyState)
    money: MoneyState = field(default_factory=MoneyState)

    def condition(self, resilience: float) -> float:
        return condition(self.health, resilience, self.addiction.substance_load())

    def is_insurable(self) -> bool:
        return self.addiction.insurable


def advance_year(
    state: LifeState, rng: random.Random, gross_income_millions: float, worked_this_year: bool, age: int = 30,
    windfall_income_millions: float = 0.0,
) -> tuple[LifeState, dict[str, float]]:
    """One year of the life layer. Returns (new_state, standing_deltas) — deltas from addiction
    progression (resilience/notoriety/affection) that the caller applies to the actor's own
    Standing/attributes, since LifeState doesn't hold those itself.

    windfall_income_millions: a one-time payout (a box-office bonus) — see money.apply_year's own
    docstring for why this is kept separate from gross_income_millions rather than pre-summed."""
    health = state.health if worked_this_year else after_idle_year(state.health)

    if state.addiction.stage == "recovery":
        addiction = advance_recovery(state.addiction, rng)
        deltas: dict[str, float] = {}
    else:
        addiction, deltas = advance_addiction(state.addiction, rng)

    money = apply_money_year(state.money, gross_income_millions, rng, windfall_income_millions=windfall_income_millions)
    family = maybe_generate_caretaking(state.family, age, rng)

    return replace(state, health=health, addiction=addiction, money=money, family=family), deltas
