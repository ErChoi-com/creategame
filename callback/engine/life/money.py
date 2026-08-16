"""design/part-11-the-life.md §11.6 — money, and the going-broke ratchet: how a person who made
$40M ends up bankrupt, which turns out to be pure arithmetic.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

from callback.engine.core.util import clamp

AGENT_SHARE = 0.10
MANAGER_SHARE = 0.05
LAWYER_SHARE = 0.05
PUBLICIST_FLAT_ANNUAL = 0.070  # $M/yr
TEAM_TAKE_PCT = AGENT_SHARE + MANAGER_SHARE + LAWYER_SHARE  # ~0.20, plus the flat publicist fee
BUSINESS_MANAGER_SHARE = 0.03
EMBEZZLEMENT_CHANCE = 0.01
EMBEZZLEMENT_LOSS_SHARE = 0.30  # of net worth, if it happens

TAX_RATE_DEFAULT = 0.45  # era-dependent 35-70%+ in design/; this pass's fixed default

LIFESTYLE_FLOOR_RATIO = 0.55
LIFESTYLE_FLOOR_DECAY = 0.92  # falls 8%/yr once income drops


@dataclass(frozen=True)
class MoneyState:
    net_worth: float = 0.0
    peak_annual_income: float = 0.0
    lifestyle_floor: float = 0.0
    tax_rate: float = TAX_RATE_DEFAULT

    def clamped(self) -> "MoneyState":
        return replace(self, lifestyle_floor=max(0.0, self.lifestyle_floor))


def net_income(gross_income_millions: float, tax_rate: float = TAX_RATE_DEFAULT) -> float:
    after_team = gross_income_millions * (1.0 - TEAM_TAKE_PCT) - PUBLICIST_FLAT_ANNUAL
    after_business_manager = after_team * (1.0 - BUSINESS_MANAGER_SHARE)
    after_tax = after_business_manager * (1.0 - tax_rate)
    return max(0.0, after_tax)


def apply_year(state: MoneyState, gross_income_millions: float, rng: random.Random) -> MoneyState:
    income = net_income(gross_income_millions, state.tax_rate)
    peak = max(state.peak_annual_income, gross_income_millions)

    target_floor = LIFESTYLE_FLOOR_RATIO * peak
    if target_floor > state.lifestyle_floor:
        floor = target_floor  # ratchets up instantly to the new peak
    else:
        floor = state.lifestyle_floor * LIFESTYLE_FLOOR_DECAY  # falls only 8%/yr

    net_worth = state.net_worth + income - floor
    if rng.random() < EMBEZZLEMENT_CHANCE:
        net_worth *= (1.0 - EMBEZZLEMENT_LOSS_SHARE)

    return replace(state, net_worth=net_worth, peak_annual_income=peak, lifestyle_floor=floor).clamped()


def cut_the_floor(state: MoneyState, new_floor: float) -> MoneyState:
    """The correct move almost nobody makes in time — available any time, costs Affection with
    your own entourage (the caller applies that cost), lets the floor drop below the ratchet."""
    return replace(state, lifestyle_floor=min(state.lifestyle_floor, max(0.0, new_floor)))
