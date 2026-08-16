"""design/part-11-the-life.md §11.1 — health. Condition (the multiplier actor/performance.py's
resolve_performance() reads) is derived from Health, burnout debt, substance load, and Resilience.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from callback.engine.core.util import clamp

CONDITION_BASE = 70.0
CONDITION_HEALTH_COEF = 0.20
CONDITION_HEALTH_CENTRE = 50.0
CONDITION_RESILIENCE_COEF = 0.10
CONDITION_RESILIENCE_CENTRE = 50.0

BURNOUT_GAIN_PER_PROJECT = 4.0
BURNOUT_RECOVERY_PER_IDLE_YEAR = 6.0
INJURY_HEALTH_COST = 15.0
INJURY_PHYSICALITY_CAP_CHANCE = 0.30  # of an injury event, the chance it permanently caps Physicality


@dataclass(frozen=True)
class HealthState:
    health: float = 75.0
    burnout_debt: float = 0.0
    conditions: tuple[str, ...] = ()  # permanent flags, e.g. "knee_reconstruction"

    def clamped(self) -> "HealthState":
        return replace(self, health=clamp(self.health, 0.0, 100.0), burnout_debt=clamp(self.burnout_debt, 0.0, 60.0))


def condition(health_state: HealthState, resilience: float, substance_load: float) -> float:
    return clamp(
        CONDITION_BASE
        + CONDITION_HEALTH_COEF * (health_state.health - CONDITION_HEALTH_CENTRE)
        - health_state.burnout_debt
        - substance_load
        + CONDITION_RESILIENCE_COEF * (resilience - CONDITION_RESILIENCE_CENTRE),
        0.0, 100.0,
    )


def after_project(health_state: HealthState) -> HealthState:
    return replace(health_state, burnout_debt=health_state.burnout_debt + BURNOUT_GAIN_PER_PROJECT).clamped()


def after_idle_year(health_state: HealthState) -> HealthState:
    return replace(health_state, burnout_debt=max(0.0, health_state.burnout_debt - BURNOUT_RECOVERY_PER_IDLE_YEAR)).clamped()


def apply_injury(health_state: HealthState, flag: str) -> HealthState:
    return replace(
        health_state,
        health=health_state.health - INJURY_HEALTH_COST,
        conditions=(*health_state.conditions, flag),
    ).clamped()
