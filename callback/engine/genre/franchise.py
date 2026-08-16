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
