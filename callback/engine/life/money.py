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

# §11.6 v2 — the ratchet was locking in real bankruptcy by construction, not just as a real risk:
# 55% of a single peak year, decaying only 8%/yr, meant one big year committed a career to over a
# decade of outspending any ordinary year that followed it. Against genuinely lumpy income (a rare
# box-office bonus or director payday spiking one year, most years far more modest), that's a
# guaranteed multi-decade bleed, not a real "stay disciplined or go broke" choice — there was no
# discipline that could outrun it once one big year happened. Lowered spend and sped up the climb-
# down so the ratchet is still a real, felt cost of a big year (this isn't free money, lifestyle
# still moves with success) without being mathematically destined to end in ruin over a long career.
LIFESTYLE_FLOOR_RATIO = 0.32
LIFESTYLE_FLOOR_DECAY = 0.80  # falls 20%/yr once income drops — a lean stretch actually corrects

# §11.6 v2 — a one-time windfall (a negotiated box-office bonus, mainly) used to count toward the
# ratchet exactly like a sustained acting fee — a single $300M+ bonus year permanently set the
# lifestyle floor as if that were the new normal salary, which no amount of the rate/decay tuning
# above can fix on its own (the floor was reacting correctly to a number that was never a real
# income level to begin with). Real windfalls still count in full toward net worth — you keep the
# money — they just don't get to reset how much you're "expected" to spend every year afterward.
WINDFALL_LIFESTYLE_WEIGHT = 0.15


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


def apply_year(state: MoneyState, gross_income_millions: float, rng: random.Random, windfall_income_millions: float = 0.0) -> MoneyState:
    """gross_income_millions: steady income (an acting quote, a director's fee) — counts in full
    toward both net worth and the lifestyle-floor ratchet. windfall_income_millions: a real but
    one-time payout (a box-office bonus) — counts in full toward net worth, but only
    WINDFALL_LIFESTYLE_WEIGHT of it toward the ratchet, so one huge year doesn't permanently commit
    a career to spending at that rate (see the module-level note above)."""
    total_income_millions = gross_income_millions + windfall_income_millions
    income = net_income(total_income_millions, state.tax_rate)
    lifestyle_relevant_income = gross_income_millions + WINDFALL_LIFESTYLE_WEIGHT * windfall_income_millions
    # peak_annual_income itself has to decay during a dry spell, or it pins target_floor at the
    # old ceiling forever: the floor would decay one year then instantly ratchet back up the next
    # (decay < target, so target > floor triggers the ratchet-up branch), oscillating instead of
    # ever actually falling. Decaying peak at the same rate as the floor keeps them moving together
    # so a real dry spell corrects the floor instead of just alternating around it.
    peak = max(lifestyle_relevant_income, state.peak_annual_income * LIFESTYLE_FLOOR_DECAY)

    target_floor = LIFESTYLE_FLOOR_RATIO * peak
    if target_floor > state.lifestyle_floor:
        floor = target_floor  # ratchets up instantly to the new peak
    else:
        floor = state.lifestyle_floor * LIFESTYLE_FLOOR_DECAY  # falls only 20%/yr

    net_worth = state.net_worth + income - floor
    if rng.random() < EMBEZZLEMENT_CHANCE:
        net_worth *= (1.0 - EMBEZZLEMENT_LOSS_SHARE)

    return replace(state, net_worth=net_worth, peak_annual_income=peak, lifestyle_floor=floor).clamped()


CUT_THE_FLOOR_AFFECTION_COST = 8.0  # a real, felt cost (see multi_picture_deal.BREAK_NOTORIETY_
# PENALTY for the same shape on the notoriety axis) — your entourage/team feels a real cut to their
# own cut, not a free reset. The caller (Session) applies this to actor Standing.


def cut_the_floor(state: MoneyState, new_floor: float) -> MoneyState:
    """The correct move almost nobody makes in time — available any time, costs Affection with
    your own entourage (the caller applies that cost), lets the floor drop below the ratchet."""
    return replace(state, lifestyle_floor=min(state.lifestyle_floor, max(0.0, new_floor)))
