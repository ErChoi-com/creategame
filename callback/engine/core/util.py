"""Small numeric helpers shared across core/ and actor/. No dependency on either."""
from __future__ import annotations

import math


def clamp(x: float, lo: float, hi: float) -> float:
    """Constrain x to [lo, hi]. Used everywhere a meter or score has a hard floor/ceiling."""
    return max(lo, min(hi, x))


def sigmoid(x: float) -> float:
    """Standard logistic function, used by every probability formula in design/ (offer odds,
    holdout odds, etc.) — always of the shape 1 / (1 + e^-(k * (x - centre)))."""
    # Guard against overflow for extreme inputs (careers can produce large Utility gaps).
    if x < -60:
        return 0.0
    if x > 60:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def positive_part(x: float) -> float:
    """The ⁺ notation used throughout design/ (e.g. Utility's overpriced-actor penalty term)."""
    return max(0.0, x)
