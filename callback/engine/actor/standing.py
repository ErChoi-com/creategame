"""design/part-04-the-actor.md §4.3 — Standing.

Four meters (Heat/Prestige/Affection/Notoriety), built on core.meters.StandingModel, plus the
derived scalars (StarPower, Standing, Bankability, Quote) and the gatekeeper weight table §4.4
reads to compute an offer's StandingScore.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from callback.engine.core.meters import Meter, StandingModel
from callback.engine.core.util import clamp

METER_NAMES = ("heat", "prestige", "affection", "notoriety")

# §4.3 baseline yearly decay — Prestige/Affection/Notoriety are fixed; Heat's is billing-aware
# (HEAT_KEEP below) so it isn't listed here.
PRESTIGE_DECAY = 0.985
# Affection had no billing-aware keep rate the way Heat does, and no base gain per film the way
# Heat's HEAT_BASE gives it either — delta_affection is pure signed audience-score-vs-centre with
# nothing to offset a "steady" (average) film, so 0.96 (4%/yr) meant it could barely ever
# outrun its own decay even for a genuinely well-liked star, decaying back to near-zero within a
# few years of anything less than a sustained hit streak. A first pass moved this to 0.975; still
# not quite reasonable — Affection is the one meter with no per-film floor at all, so it should
# decay no faster than Prestige's own rate, not just "less fast than before." Matched to
# PRESTIGE_DECAY directly: still real decay, still needs tending, just no longer the one meter
# structurally harder to hold onto than every other.
AFFECTION_DECAY = PRESTIGE_DECAY
NOTORIETY_DECAY = 0.84

# §4.3 — "the tier you can reach has to be able to outrun the decay on that tier."
HEAT_KEEP = {"idle": 0.80, "bit": 0.865, "supporting": 0.888, "lead": 0.925}

# ΔHeat constants.
HEAT_BASE = 7.9  # working at all is worth something
HEAT_ROI_COEF = 9.0
HEAT_ROI_CENTRE = 0.90  # below the median outcome
HEAT_AUD_COEF = 0.20
HEAT_AUD_CENTRE = 52.0

# ΔPrestige / ΔAffection constants.
PRESTIGE_CRITIC_COEF = 0.11
PRESTIGE_CRITIC_CENTRE = 57.0
PRESTIGE_SPOTLIGHT_COEF = 0.26
PRESTIGE_SPOTLIGHT_CENTRE = 54.0
AFFECTION_AUD_COEF = 0.10
AFFECTION_AUD_CENTRE = 55.0

# Recognition — the bridge out of bit parts, deliberately not Standing (§4.3).
RECOGNITION_COEF = 0.42
RECOGNITION_SPOTLIGHT_CENTRE = 51.0
RECOGNITION_DECAY = 0.90
RECOGNITION_DECAY_FAST = 0.80  # once Standing clears 45, it's done its job

# Derived-scalar weights.
STARPOWER_HEAT = 0.45
STARPOWER_AFFECTION = 0.30
STARPOWER_PRESTIGE = 0.25
NOTORIETY_PENALTY_THRESHOLD = 55.0
NOTORIETY_PENALTY_COEF = 0.20

BANKABILITY_HEAT = 0.60
BANKABILITY_ROI = 0.25
BANKABILITY_AFFECTION = 0.15
BANKABILITY_NOTORIETY_COEF = 0.20

QUOTE_BASE = 0.05
QUOTE_EXP_COEF = 0.070

# §4.4 gatekeeper weight table (also lives here, next to the meters it weighs).
GATEKEEPER_WEIGHTS: dict[str, dict[str, float]] = {
    "studio_tentpole": {"heat": 0.55, "prestige": 0.05, "affection": 0.30, "notoriety": -0.40},
    "prestige_auteur": {"heat": 0.10, "prestige": 0.65, "affection": 0.05, "notoriety": 0.05},
    "indie_first_timer": {"heat": 0.15, "prestige": 0.40, "affection": 0.10, "notoriety": 0.00},
    "streamer_volume": {"heat": 0.35, "prestige": 0.15, "affection": 0.30, "notoriety": 0.15},
    "network_tv": {"heat": 0.30, "prestige": 0.10, "affection": 0.45, "notoriety": -0.55},
    "franchise_reboot": {"heat": 0.45, "prestige": 0.10, "affection": 0.35, "notoriety": -0.30},
}


def new_standing_model(heat=20.0, prestige=20.0, affection=20.0, notoriety=5.0) -> StandingModel:
    return StandingModel(meters={
        "heat": Meter("heat", heat),
        "prestige": Meter("prestige", prestige),
        "affection": Meter("affection", affection),
        "notoriety": Meter("notoriety", notoriety),
    })


def discovery(credits: int) -> float:
    """Up to 2.4x across the first 9 credits, tapering to 1x. §4.3 gives the endpoints, not an
    exact curve between them; linear taper is this pass's documented interpretation."""
    if credits >= 9:
        return 1.0
    return 2.4 - (1.4 * credits / 9.0)


def reach(budget_millions: float) -> float:
    """clamp(0.46 + 0.50 * log10(budget), 0.3, 1.7)."""
    return clamp(0.46 + 0.50 * math.log10(max(budget_millions, 0.01)), 0.3, 1.7)


def delta_heat(billing_weight: float, credits: int, budget_millions: float, roi: float, audience_score: float) -> float:
    r = HEAT_BASE + HEAT_ROI_COEF * clamp(roi - HEAT_ROI_CENTRE, -0.6, 2.2) + HEAT_AUD_COEF * (audience_score - HEAT_AUD_CENTRE)
    return billing_weight * discovery(credits) * reach(budget_millions) * r


def delta_prestige(billing_weight: float, credits: int, film_critic_score: float, your_spotlight: float) -> float:
    return billing_weight * discovery(credits) * (
        PRESTIGE_CRITIC_COEF * (film_critic_score - PRESTIGE_CRITIC_CENTRE)
        + PRESTIGE_SPOTLIGHT_COEF * (your_spotlight - PRESTIGE_SPOTLIGHT_CENTRE)
    )


def delta_affection(billing_weight: float, credits: int, budget_millions: float, audience_score: float) -> float:
    return billing_weight * discovery(credits) * reach(budget_millions) * AFFECTION_AUD_COEF * (audience_score - AFFECTION_AUD_CENTRE)


def delta_recognition(your_spotlight: float) -> float:
    return RECOGNITION_COEF * max(0.0, your_spotlight - RECOGNITION_SPOTLIGHT_CENTRE)


def star_power(standing_model: StandingModel) -> float:
    return (
        STARPOWER_HEAT * standing_model["heat"]
        + STARPOWER_AFFECTION * standing_model["affection"]
        + STARPOWER_PRESTIGE * standing_model["prestige"]
    )


def standing_score(standing_model: StandingModel) -> float:
    """StarPower net of scandal — the scalar every gatekeeper weighting and leverage system in
    design/ gates on, computed once, here."""
    sp = star_power(standing_model)
    notoriety_penalty = NOTORIETY_PENALTY_COEF * max(0.0, standing_model["notoriety"] - NOTORIETY_PENALTY_THRESHOLD)
    return clamp(sp - notoriety_penalty, 0.0, 100.0)


def bankability(standing_model: StandingModel, recent_roi_normalized: float) -> float:
    """recent_roi_normalized is a 0-100 read of recent box-office ROI; design/ names the input
    without specifying its normalization, so the caller (simulation/career.py) is responsible for
    turning a raw ROI history into this scale."""
    notoriety_penalty = BANKABILITY_NOTORIETY_COEF * max(0.0, standing_model["notoriety"] - NOTORIETY_PENALTY_THRESHOLD)
    return (
        BANKABILITY_HEAT * standing_model["heat"]
        + BANKABILITY_ROI * recent_roi_normalized
        + BANKABILITY_AFFECTION * standing_model["affection"]
        - notoriety_penalty
    )


def quote(standing_model: StandingModel, recent_roi_normalized: float, era_multiplier: float = 1.0) -> float:
    """Asking price, in $M."""
    return QUOTE_BASE * math.exp(QUOTE_EXP_COEF * bankability(standing_model, recent_roi_normalized)) * era_multiplier


@dataclass(frozen=True)
class RecognitionMeter:
    """The way-in for supporting/bit roles (§4.3) — deliberately separate from Standing itself,
    only ever read by offers.py for non-lead casting paths."""

    value: float = 0.0

    def add(self, your_spotlight: float) -> "RecognitionMeter":
        return RecognitionMeter(clamp(self.value + delta_recognition(your_spotlight), 0.0, 100.0))

    def decay(self, standing: float) -> "RecognitionMeter":
        factor = RECOGNITION_DECAY_FAST if standing >= 45.0 else RECOGNITION_DECAY
        return RecognitionMeter(clamp(self.value * factor, 0.0, 100.0))
