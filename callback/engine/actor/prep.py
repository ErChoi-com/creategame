"""design/part-04-the-actor.md §4.6 — Prep.

Six preparation choices, one pick per project. §4.6 gives each option's weeks, effect, and the
Prep formula, but not the per-option base Prep value that formula reads (beyond "wing it" being a
flat 20 that bypasses the formula entirely) — PREP_BASE below is this pass's documented reading,
ordered to match each option's stated depth of commitment.
"""
from __future__ import annotations

from dataclasses import dataclass

from callback.engine.core.util import clamp

TABLE_WORK = "table_work"
RESEARCH = "research"
DIALECT = "dialect"
PHYSICAL_TRANSFORMATION = "physical_transformation"
LIVE_IT = "live_it"
WING_IT = "wing_it"

PREP_OPTIONS = (TABLE_WORK, RESEARCH, DIALECT, PHYSICAL_TRANSFORMATION, LIVE_IT, WING_IT)

WEEKS = {
    TABLE_WORK: 2,
    RESEARCH: 3,
    DIALECT: 4,
    PHYSICAL_TRANSFORMATION: 9,  # §4.6's range is 6-12; 9 is this pass's representative value
    LIVE_IT: 8,
    WING_IT: 0,
}

# This pass's documented base-Prep reading (§4.6 doesn't give these numerically).
PREP_BASE = {
    TABLE_WORK: 55.0,
    RESEARCH: 65.0,
    DIALECT: 70.0,
    PHYSICAL_TRANSFORMATION: 80.0,
    LIVE_IT: 95.0,
}

PREP_RESILIENCE_COEF = 0.004
PREP_RESILIENCE_BASE = 0.8
WING_IT_FLAT_PREP = 20.0

CRAFT_GAIN_TABLE_WORK = 0.4  # "tiny, permanent"
RESILIENCE_HIT_TRANSFORMATION = -0.6  # "small permanent Resilience hit"
RESILIENCE_HIT_LIVE_IT = -8.0


@dataclass(frozen=True)
class PrepResult:
    choice: str
    prep: float
    craft_delta: float = 0.0
    resilience_delta: float = 0.0
    removes_voice_gate: bool = False
    removes_physicality_look_gate: bool = False
    transformation_flag: bool = False
    on_set_conflict_risk: float = 0.0  # 0-1, read by the shoot's event pool later


def resolve_prep(choice: str, resilience: float, is_biographical_or_period: bool = False) -> PrepResult:
    if choice == WING_IT:
        return PrepResult(choice=choice, prep=WING_IT_FLAT_PREP)

    base = PREP_BASE[choice]
    if choice == RESEARCH and is_biographical_or_period:
        base += 15.0  # "large bonus if biographical/period"

    prep = clamp(base * (PREP_RESILIENCE_BASE + PREP_RESILIENCE_COEF * resilience), 0.0, 100.0)

    craft_delta = CRAFT_GAIN_TABLE_WORK if choice == TABLE_WORK else 0.0
    resilience_delta = 0.0
    removes_voice = choice == DIALECT
    removes_phys_look = choice == PHYSICAL_TRANSFORMATION
    transformation_flag = choice in (PHYSICAL_TRANSFORMATION, LIVE_IT)
    conflict_risk = 0.0

    if choice == PHYSICAL_TRANSFORMATION:
        resilience_delta = RESILIENCE_HIT_TRANSFORMATION
    elif choice == LIVE_IT:
        resilience_delta = RESILIENCE_HIT_LIVE_IT
        conflict_risk = 0.25

    return PrepResult(
        choice=choice,
        prep=prep,
        craft_delta=craft_delta,
        resilience_delta=resilience_delta,
        removes_voice_gate=removes_voice,
        removes_physicality_look_gate=removes_phys_look,
        transformation_flag=transformation_flag,
        on_set_conflict_risk=conflict_risk,
    )
