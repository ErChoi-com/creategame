"""design/part-06-leverage.md §6.6 — a representative subset of the ~40-verb action catalogue.
Not all forty verbs (many need systems out of this pass's scope — crew loyalty, a script market,
festivals); this covers one grounded, mechanically-real verb per category §6.6 itself uses to
organize the catalogue, each wired to a real state change rather than flavor text.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.core.util import clamp
from callback.engine.leverage.favours import FavourLedger

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


@dataclass(frozen=True)
class TheatreSeasonEffect:
    prestige_delta: float
    craft_delta: float
    heat_decay_extra: float


def theatre_season() -> TheatreSeasonEffect:
    return TheatreSeasonEffect(THEATRE_PRESTIGE_DELTA, THEATRE_CRAFT_DELTA, THEATRE_HEAT_DECAY_EXTRA)


# --- Change other people: Start a feud / Publicly defend someone (§6.6) ---
FEUD_NOTORIETY_SELF = 8.0
FEUD_NOTORIETY_TARGET = 8.0

DEFEND_NOTORIETY_SELF = 6.0
DEFEND_FAVOUR_GAIN = 3
DEFEND_AFFINITY_GAIN = 8.0


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


# §4.4's offer board can be scanned and applied to without limit — the fix for "unlimited scanning
# defeats any real Difficulty bar" isn't a cap on how many times you can look or apply (tried and
# explicitly rejected in favor of this), it's making WHO you are while applying actually matter on
# every single attempt, and making repeated attempts within the same year carry a real, felt cost.
#
# The boost: real representation opens real doors, on every application, not just a rationed few —
# but it's never the same flat number twice. Sampled fresh per application from a real range, the
# same "never lands on the same number twice" shape leverage.merchandising.negotiated_merch_share
# already uses for a negotiated position. unrepresented has nothing to draw on at all.
AGENT_APPLICATION_BOOST_RANGE = {
    "unrepresented": (0.0, 0.0),
    "regional": (6.0, 14.0),
    "boutique": (14.0, 24.0),
    "major": (22.0, 34.0),
    "powerhouse": (30.0, 46.0),
}


def agent_application_boost(agent_tier: str, rng: random.Random) -> float:
    lo, hi = AGENT_APPLICATION_BOOST_RANGE.get(agent_tier, (0.0, 0.0))
    return rng.uniform(lo, hi)


# The fatigue tax: applying to role after role in the same year isn't free just because looking is
# — the more you've been out there asking, the harder each NEXT ask gets, and how fast that bites
# depends entirely on who's doing the asking. An unrepresented actor cold-submitting to their 15th
# role this year reads as increasingly desperate to whoever's on the other end; a powerhouse
# client's agent is the one placing every call, so volume barely shows up as volume at all. The
# underlying trend has to keep climbing with real applications — that's the whole signal — so only
# the noise on top of it is randomized, never the trend itself.
AGENT_FATIGUE_RATE = {
    "unrepresented": 0.8, "regional": 0.4, "boutique": 0.2, "major": 0.07, "powerhouse": 0.013,
}
# Calibrated against real yearly volume, not just the abusive case: simulation.session.Session's
# own offer_board() auto-generates roughly 20-30 listings every single year on its own, with no
# scanning at all — an early draft of this rate (6.0 for unrepresented) meant an ordinary first
# board, before a player had done anything, could already accumulate over +100 difficulty by its
# own back half. That's not "unlimited scanning defeats Difficulty," that's ordinary play breaking.
# This rate makes a normal ~25-listing year cost an unrepresented actor something real but
# survivable (~20, on the same order as actor.offers.TYPE_BREAK_DIFFICULTY_TAX); sustained,
# deliberate over-scanning (250+ listings) is where it actually turns crushing (~200).
AGENT_FATIGUE_NOISE_SD = 2.0

# application_status()'s own read on the accumulated (noiseless) trend value, not the tier-specific
# raw applications count — this is what lets one banding scale mean something consistent across
# every agent tier, since the same application count produces wildly different trend values
# depending on who's actually making the calls.
FATIGUE_BAND_THRESHOLDS = (
    (0.0, "fresh"), (15.0, "getting known"), (35.0, "flooding the market"), (60.0, "overexposed"),
)


def agent_fatigue_trend(agent_tier: str, applications_already_this_year: int) -> float:
    """The deterministic, always-climbing part — application_fatigue_tax adds real noise on top
    of this for the actual difficulty roll, but this raw trend value is also what application_
    status() bands, so the player's own read on "how oversaturated do I look right now" never
    jitters from one application to the next."""
    rate = AGENT_FATIGUE_RATE.get(agent_tier, AGENT_FATIGUE_RATE["unrepresented"])
    return rate * applications_already_this_year


def application_fatigue_tax(agent_tier: str, applications_already_this_year: int, rng: random.Random) -> float:
    trend = agent_fatigue_trend(agent_tier, applications_already_this_year)
    return max(0.0, trend + rng.gauss(0.0, AGENT_FATIGUE_NOISE_SD))


def fatigue_band(agent_tier: str, applications_already_this_year: int) -> str:
    trend = agent_fatigue_trend(agent_tier, applications_already_this_year)
    band = FATIGUE_BAND_THRESHOLDS[0][1]
    for lower, label in FATIGUE_BAND_THRESHOLDS:
        if trend >= lower:
            band = label
    return band


# --- Get work that wasn't offered you: Ask your agency to package (§6.6, requires Powerhouse) ---
PACKAGE_OFFER_FEE_SHARE = 0.15  # "guaranteed offer, no audition, 15% forever"


@dataclass(frozen=True)
class LeverageState:
    agent_tier: str = "unrepresented"
    scarcity: float = 0.0
    blacklisted: frozenset[str] = field(default_factory=frozenset)
    recommended: dict[str, float] = field(default_factory=dict)
    favours: FavourLedger = field(default_factory=FavourLedger)


def new_leverage_state() -> LeverageState:
    return LeverageState()


def blacklist(state: LeverageState, npc_id: str) -> LeverageState:
    return replace(state, blacklisted=state.blacklisted | {npc_id})


def recommend(state: LeverageState, npc_id: str, boost: float = 0.5) -> LeverageState:
    rec = dict(state.recommended)
    rec[npc_id] = boost
    return replace(state, recommended=rec)
