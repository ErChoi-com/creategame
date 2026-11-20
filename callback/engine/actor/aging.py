"""design/part-04-the-actor.md §4.9 — the body, and the ageism curve.

§4.9 presents role volume by age as a qualitative dot-density table, not a formula. This module's
`role_volume_multiplier` is a documented numeric reading of that table (dots / 5, the max density
in any cell) — the interpolation this pass needed to make it usable by actor/offers.py.
"""
from __future__ import annotations

from callback.engine.core.util import clamp

# LookCurve(age): peaks 22-32, -0.9/yr to 45, -1.6/yr to 60, -2.2/yr after.
LOOK_PEAK_LO, LOOK_PEAK_HI = 22, 32


def look_curve_delta(age: int) -> float:
    """Per-year Look change implied by age alone (before upkeep). Zero across the peak band."""
    if LOOK_PEAK_LO <= age <= LOOK_PEAK_HI:
        return 0.0
    if age < LOOK_PEAK_LO:
        return 0.0  # rising into the peak isn't specified as a curve; treated as flat pre-peak
    if age <= 45:
        return -0.9
    if age <= 60:
        return -1.6
    return -2.2


def apply_look_curve(look: float, age: int) -> float:
    return clamp(look + look_curve_delta(age), 0.0, 100.0)


# §4.9's role-volume-by-age table, read as dots/5 (5 = the densest cell in any row).
_ROLE_VOLUME_BANDS = (
    # (age_hi_inclusive, ingenue_romantic, character_authority, lead_overall)
    (27, 5, 0, 3),
    (38, 4, 2, 5),
    (48, 2, 4, 4),
    (60, 0, 5, 3),
    (999, 0, 4, 2),
)


def role_volume_multiplier(age: int, lane: str) -> float:
    """lane is one of "ingenue_romantic", "character_authority", "lead_overall". Returns a 0-1
    multiplier on offer-generation volume for that lane at this age."""
    idx = {"ingenue_romantic": 1, "character_authority": 2, "lead_overall": 3}[lane]
    for age_hi, *dots in _ROLE_VOLUME_BANDS:
        if age <= age_hi:
            return dots[idx - 1] / 5.0
    return 0.0
