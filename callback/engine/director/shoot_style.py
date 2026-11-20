"""design/part-07-the-director.md §7.6 — the shoot, style as a real choice. Five named approaches,
each a genuine performance/schedule trade, plus the real Overage% roll that decides whether final
cut stays with the director.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.core.util import clamp

HEAVY_COVERAGE = "heavy_coverage"
LONG_TAKES = "long_takes"
MANY_TAKES = "many_takes"
IMPROVISATION = "improvisation"
LEAN_AND_FAST = "lean_and_fast"

SHOOT_STYLES = (HEAVY_COVERAGE, LONG_TAKES, MANY_TAKES, IMPROVISATION, LEAN_AND_FAST)

MANY_TAKES_CRAFT_THRESHOLD = 70.0


@dataclass(frozen=True)
class ShootStyleOutcome:
    style: str
    craft_contribution_delta: float
    post_luck_floor_delta: float  # heavy coverage only — raises the edit's floor, not its mean
    critic_bonus: float  # long takes only — a real §7.7 Craft/critic bump


def resolve_shoot_style(style: str, instinct: float, craft: float) -> ShootStyleOutcome:
    if style == HEAVY_COVERAGE:
        return ShootStyleOutcome(style, craft_contribution_delta=-6.0, post_luck_floor_delta=8.0, critic_bonus=0.0)
    if style == LONG_TAKES:
        return ShootStyleOutcome(style, craft_contribution_delta=10.0, post_luck_floor_delta=0.0, critic_bonus=5.0)
    if style == MANY_TAKES:
        delta = 8.0 if craft > MANY_TAKES_CRAFT_THRESHOLD else -5.0
        return ShootStyleOutcome(style, craft_contribution_delta=delta, post_luck_floor_delta=0.0, critic_bonus=0.0)
    if style == IMPROVISATION:
        delta = 0.10 * (instinct - 50.0)
        return ShootStyleOutcome(style, craft_contribution_delta=delta, post_luck_floor_delta=0.0, critic_bonus=0.0)
    if style == LEAN_AND_FAST:
        return ShootStyleOutcome(style, craft_contribution_delta=-8.0, post_luck_floor_delta=0.0, critic_bonus=0.0)
    raise ValueError(f"unknown shoot style: {style}")


# §7.6 formula. v11 fix: the original v8/v9 coefficients were calibrated for 0-1 fraction inputs,
# but every real caller passes ambition/efficiency straight off DirectorAttributes' own 0-100
# scale, and chaos pre-scaled by *100 on top of that — raw landed an order of magnitude past
# OVERAGE_LO/HI for almost any realistic input, so this always saturated the clamp regardless of
# the noise term. Never actually caught before this pass because the only prior consumer (the
# final-cut gate, overage <= OVERAGE_FINAL_CUT_THRESHOLD) only ever read a boolean off it, never
# the real number — exactly the kind of dead-number bug this design has caught before. Now:
# ambition/efficiency are rescaled internally to 0-1 (callers keep passing the raw 0-100
# attribute, ergonomically); chaos is expected already-fractional (director/skill.py's own
# ensemble_chaos_total range, ~0-0.3 typically) — the call site's own redundant *100 is removed.
OVERAGE_AMBITION_COEF = 0.9
OVERAGE_CHAOS_COEF = 1.0
OVERAGE_EFFICIENCY_COEF = 0.9
OVERAGE_NOISE_SD = 0.12
OVERAGE_LO = -0.20
OVERAGE_HI = 1.20
OVERAGE_FINAL_CUT_THRESHOLD = 0.25
OVERAGE_DIFFICULTY_PENALTY = 12.0

# §7.6 v10 — an ensemble package from the generalized "attach a star" (a second name on a project
# that already has one) raises chaos here, scaled by that second name's own Bankability, capped
# below "the difficult genius" cast choice's own flat +0.15.
ENSEMBLE_CHAOS_LO = 0.04
ENSEMBLE_CHAOS_HI = 0.13


def ensemble_chaos(second_attachment_bankability: float) -> float:
    frac = clamp(second_attachment_bankability, 0.0, 100.0) / 100.0
    return ENSEMBLE_CHAOS_LO + (ENSEMBLE_CHAOS_HI - ENSEMBLE_CHAOS_LO) * frac


def ensemble_chaos_total(attachments) -> float:
    """§7.4 v11 — a real roster, not just "the lead plus one more." Every attachment beyond the
    first adds its own chaos share (summed, not multiplied out pairwise — a five-person ensemble
    is a real handful, not a combinatorial explosion)."""
    if len(attachments) <= 1:
        return 0.0
    return sum(ensemble_chaos(a.bankability) for a in attachments[1:])


def overage_percent(ambition: float, chaos: float, efficiency: float, rng: random.Random) -> float:
    """ambition/efficiency: 0-100, DirectorAttributes' own scale (vision/efficiency respectively).
    chaos: an already-fractional read (director.shoot_style.ensemble_chaos_total's own range),
    never pre-scaled by the caller. No correlation with Heat anywhere in this formula, by design."""
    raw = (
        OVERAGE_AMBITION_COEF * (ambition / 100.0) + OVERAGE_CHAOS_COEF * chaos
        - OVERAGE_EFFICIENCY_COEF * (efficiency / 100.0) + rng.gauss(0.0, OVERAGE_NOISE_SD)
    )
    return clamp(raw, OVERAGE_LO, OVERAGE_HI)
