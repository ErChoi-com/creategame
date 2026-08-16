"""design/part-09-genres-franchises-and-tie-ins.md §9.5 — the sequel-value curve, fitted to real
box-office data: the first two installments usually out-earn the third, reception bottoms around
the fifth or sixth. Franchise leverage itself (recast cost, the holdout) lives in leverage/
indispensability.py; this is just the box-office bonus a given installment number carries.
"""
from __future__ import annotations

SEQUEL_BASE_BONUS = {1: 32.0, 2: 30.0, 3: 20.0, 4: 12.0, 5: 6.0, 6: 2.0}
SEQUEL_BONUS_AUDIENCE_CENTRE = 65.0


def sequel_bonus(installment_number: int, prior_audience_score: float) -> float:
    base = SEQUEL_BASE_BONUS.get(installment_number, 0.0)
    return base * (prior_audience_score / SEQUEL_BONUS_AUDIENCE_CENTRE)


# Not in design/ under this name, but a direct read of the same sequel-value curve's own logic:
# rushing installments out reads as cynical/oversaturated (a real audience penalty, not just
# flavor), while a well-spaced sequel benefits from real anticipation building in the gap.
# Neither applies to installment 1 — there's no "since last time" yet.
FATIGUE_WINDOW_YEARS = 1  # installments this close together read as rushed
FATIGUE_PENALTY = -8.0
ANTICIPATION_GAP_YEARS = 3  # a gap at least this long earns the anticipation bump instead
ANTICIPATION_BONUS = 5.0


def spacing_modifier(installment_number: int, years_since_last_installment: int) -> float:
    if installment_number <= 1:
        return 0.0
    if years_since_last_installment <= FATIGUE_WINDOW_YEARS:
        return FATIGUE_PENALTY
    if years_since_last_installment >= ANTICIPATION_GAP_YEARS:
        return ANTICIPATION_BONUS
    return 0.0
