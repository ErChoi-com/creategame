"""design/part-11-the-life.md §11.2 — addiction as an arc, not a flag.

    USE -> DEPENDENCE -> TOLERANCE -> CRISIS -> { RECOVERY | DECLINE }

Uninsurability at Crisis is "the mechanically exact expression of 'the industry stopped hiring
them'" — an insurance-underwriter fact, not moral judgement, with a clear, earnable way out.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

CLEAN, USE, DEPENDENCE, TOLERANCE, CRISIS, RECOVERY, DECLINE = (
    "clean", "use", "dependence", "tolerance", "crisis", "recovery", "decline",
)

# Per-year stage-advance probabilities. design/ doesn't publish exact odds (a design decision the
# doc leaves to tuning); these are this pass's documented, deliberately slow-moving defaults —
# addiction is meant to be a years-long arc, not a coin flip most careers hit. CLEAN's own entry
# probability (industry exposure — the doc's own "Use... social lubricant, genuinely works at
# first" framing) was missing from an earlier pass: with no CLEAN->USE edge, no career could ever
# begin the arc at all, which silently made the entire addiction system dead code.
ADVANCE_PROBABILITY = {CLEAN: 0.03, USE: 0.08, DEPENDENCE: 0.15, TOLERANCE: 0.20}
STAGE_ORDER = [CLEAN, USE, DEPENDENCE, TOLERANCE, CRISIS]

USE_CONDITION_SHORT_TERM = 8.0
USE_CONDITION_ACCUMULATING = -2.0
DEPENDENCE_RESILIENCE_DECAY = -3.0
TOLERANCE_NOTORIETY_GAIN = 6.0
CRISIS_NOTORIETY_GAIN = 25.0
CRISIS_AFFECTION_LOSS = -15.0

RECOVERY_BLOCKS_COST = 2
INSURABLE_CLEAN_YEARS = 2
RELAPSE_BASE_PROBABILITY = 0.35
RELAPSE_DECAY_PER_CLEAN_YEAR = 0.85  # multiplicative, never reaches exactly zero
RELAPSE_FLOOR = 0.03
COMEBACK_NARRATIVE_BONUS = 11.0  # design/part-04 §4.11's NarrativeBonus table, "the comeback"


@dataclass(frozen=True)
class AddictionState:
    stage: str = CLEAN
    clean_years: int = 0
    insurable: bool = True

    def substance_load(self) -> float:
        """Feeds health.condition()'s substance_load term."""
        if self.stage == USE:
            return -USE_CONDITION_ACCUMULATING  # net negative contribution, expressed as a load
        if self.stage in (DEPENDENCE, TOLERANCE, CRISIS):
            return 6.0
        return 0.0


def advance(state: AddictionState, rng: random.Random) -> tuple[AddictionState, dict[str, float]]:
    """One year's progression. Returns (new_state, deltas) where deltas may include any of
    resilience/notoriety/affection, applied by the caller to the actor's own state. CRISIS is a
    ceiling here — the only way out is the player's own choice, enter_recovery()."""
    deltas: dict[str, float] = {}

    if state.stage not in ADVANCE_PROBABILITY:
        return state, deltas  # CRISIS/RECOVERY/DECLINE progress through their own functions

    if rng.random() < ADVANCE_PROBABILITY[state.stage]:
        new_stage = STAGE_ORDER[STAGE_ORDER.index(state.stage) + 1]
    else:
        new_stage = state.stage

    if new_stage == DEPENDENCE:
        deltas["resilience"] = DEPENDENCE_RESILIENCE_DECAY
    elif new_stage == TOLERANCE:
        deltas["notoriety"] = TOLERANCE_NOTORIETY_GAIN
    elif new_stage == CRISIS and state.stage != CRISIS:
        deltas["notoriety"] = CRISIS_NOTORIETY_GAIN
        deltas["affection"] = CRISIS_AFFECTION_LOSS

    insurable = new_stage != CRISIS
    return replace(state, stage=new_stage, insurable=insurable), deltas


def enter_recovery(state: AddictionState) -> AddictionState:
    """A real, spendable choice (2 blocks + money) — the caller is responsible for charging both;
    this just moves the stage."""
    return replace(state, stage=RECOVERY, clean_years=0)


def advance_recovery(state: AddictionState, rng: random.Random) -> AddictionState:
    """One clean year, with a relapse chance that decays but never reaches zero."""
    if state.stage != RECOVERY:
        return state
    clean_years = state.clean_years + 1
    relapse_p = max(RELAPSE_FLOOR, RELAPSE_BASE_PROBABILITY * (RELAPSE_DECAY_PER_CLEAN_YEAR ** clean_years))
    if rng.random() < relapse_p:
        return replace(state, stage=DEPENDENCE, clean_years=0, insurable=False)
    insurable = clean_years >= INSURABLE_CLEAN_YEARS
    return replace(state, stage=RECOVERY, clean_years=clean_years, insurable=insurable)


def comeback_eligible(state: AddictionState, heat_years_below_25: int) -> bool:
    return state.stage == RECOVERY and heat_years_below_25 >= 4
