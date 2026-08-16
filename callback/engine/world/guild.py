"""design/part-10-the-world.md §10.1 — guilds and unions: eligibility, scale minimum, residuals,
the health-plan cliff, and pension.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

# §4.0/§10.1 — three credited union jobs to join.
ELIGIBILITY_CREDITS = 3
SCALE_MINIMUM_FEE = 0.045  # $M/yr — "protects new actors; also means low-Standing actors can survive"

# §10.1's health-plan cliff — "$28K in current-era dollars," expressed in $M.
HEALTH_PLAN_THRESHOLD = 0.028
PENSION_VESTING_YEARS = 10
PENSION_START_AGE = 65

# Residuals — era-dependent in design/ (§10.6); this pass's fixed reading: a resolved project
# with ROI above break-even keeps paying a small trickle for years afterward.
RESIDUAL_ROI_THRESHOLD = 1.0
RESIDUAL_RATE = 0.02  # of the project's original budget, per year, while still paying out
RESIDUAL_YEARS = 12
RESIDUAL_DECAY = 0.85


@dataclass(frozen=True)
class GuildState:
    member: bool = False
    qualifying_earnings_ytd: float = 0.0
    pension_years: int = 0
    residual_streams: float = 0.0  # $M/yr, current trickle from past work
    strikes_held: int = 0
    strikes_crossed: int = 0


def is_eligible(union_credits: int) -> bool:
    return union_credits >= ELIGIBILITY_CREDITS


def scale_fee(negotiated_fee: float) -> float:
    return max(negotiated_fee, SCALE_MINIMUM_FEE)


def has_health_plan(qualifying_earnings_ytd: float) -> bool:
    return qualifying_earnings_ytd >= HEALTH_PLAN_THRESHOLD


def advance_year(state: GuildState, gross_income_millions: float) -> GuildState:
    qualifies = gross_income_millions >= HEALTH_PLAN_THRESHOLD
    pension_years = state.pension_years + (1 if qualifies else 0)
    residuals = state.residual_streams * RESIDUAL_DECAY
    return replace(state, qualifying_earnings_ytd=gross_income_millions, pension_years=pension_years, residual_streams=residuals)


def add_residual_stream(state: GuildState, project_roi: float, project_budget_millions: float) -> GuildState:
    if project_roi < RESIDUAL_ROI_THRESHOLD:
        return state
    return replace(state, residual_streams=state.residual_streams + RESIDUAL_RATE * project_budget_millions)


def pension_active(state: GuildState, age: int) -> bool:
    return state.pension_years >= PENSION_VESTING_YEARS and age >= PENSION_START_AGE
