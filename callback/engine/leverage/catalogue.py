"""design/part-06-leverage.md §6.6 — a representative subset of the ~40-verb action catalogue.
Not all forty verbs (many need systems out of this pass's scope — crew loyalty, a script market,
festivals); this covers one grounded, mechanically-real verb per category §6.6 itself uses to
organize the catalogue, each wired to a real state change rather than flavor text.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from callback.engine.core.util import clamp

# --- Change your own standing: Disappear (§6.6) ---
SCARCITY_GAIN_PER_YEAR_IDLE = 12.0
SCARCITY_CAP = 40.0
SCARCITY_QUALITY_COEF = 0.4  # offer quality tier bump on return
SCARCITY_FEE_COEF = 0.010  # first offer's fee multiplier on return


def accumulate_scarcity(scarcity: float, years_idle_this_step: int = 1) -> float:
    return clamp(scarcity + SCARCITY_GAIN_PER_YEAR_IDLE * years_idle_this_step, 0.0, SCARCITY_CAP)


def scarcity_return_bonus(scarcity: float) -> tuple[float, float]:
    """Returns (offer_quality_bonus, fee_multiplier) for the first offer after returning."""
    return SCARCITY_QUALITY_COEF * scarcity, 1.0 + SCARCITY_FEE_COEF * scarcity


# --- Change your own standing: A season of theatre (§6.6) ---
THEATRE_PRESTIGE_DELTA = 6.0
THEATRE_CRAFT_DELTA = 3.0
THEATRE_HEAT_DECAY_EXTRA = 0.85  # multiplies Heat on top of normal decay


# --- Get work that wasn't offered you: Sign with a bigger agency (§6.6, v9) ---
AGENT_TIERS = ("unrepresented", "regional", "boutique", "major", "powerhouse")
AGENT_TIER_STANDING_THRESHOLD = {"regional": 15.0, "boutique": 35.0, "major": 55.0, "powerhouse": 75.0}


def next_agent_tier(current: str) -> str | None:
    idx = AGENT_TIERS.index(current)
    return AGENT_TIERS[idx + 1] if idx + 1 < len(AGENT_TIERS) else None


def can_advance_agent_tier(current: str, standing_score: float) -> bool:
    nxt = next_agent_tier(current)
    return nxt is not None and standing_score >= AGENT_TIER_STANDING_THRESHOLD[nxt]


def advance_agent_tier(current: str, standing_score: float) -> str:
    return next_agent_tier(current) if can_advance_agent_tier(current, standing_score) else current


# --- Get work that wasn't offered you: Ask your agency to package (§6.6, requires Powerhouse) ---
PACKAGE_OFFER_FEE_SHARE = 0.15  # "guaranteed offer, no audition, 15% forever"


@dataclass(frozen=True)
class LeverageState:
    agent_tier: str = "unrepresented"
    scarcity: float = 0.0
    blacklisted: frozenset[str] = field(default_factory=frozenset)
    recommended: dict[str, float] = field(default_factory=dict)


def new_leverage_state() -> LeverageState:
    return LeverageState()


def blacklist(state: LeverageState, npc_id: str) -> LeverageState:
    return replace(state, blacklisted=state.blacklisted | {npc_id})


def recommend(state: LeverageState, npc_id: str, boost: float = 0.5) -> LeverageState:
    rec = dict(state.recommended)
    rec[npc_id] = boost
    return replace(state, recommended=rec)
