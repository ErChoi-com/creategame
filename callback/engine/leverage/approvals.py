"""design/part-06-leverage.md §6.3 — Approvals: contractual rights over a production, traded for
fee. "A fee cut of 30% for script and co-star approval is often the highest-value decision
available."
"""
from __future__ import annotations

SCRIPT, DIRECTOR, COSTAR, CUT = "script", "director", "costar", "cut"
APPROVAL_TYPES = (SCRIPT, DIRECTOR, COSTAR, CUT)

# §6.3's standing gate for negotiating approvals in (design/part-06 §6.5's "Get approvals written
# in | Standing 65+"); this pass applies the same bar to all four types uniformly.
APPROVAL_STANDING_THRESHOLD = 65.0

FEE_DISCOUNT_PER_APPROVAL = 0.30


def can_negotiate_approvals(standing_score: float) -> bool:
    return standing_score >= APPROVAL_STANDING_THRESHOLD


def fee_after_approvals(base_fee: float, approvals: frozenset[str]) -> float:
    """Each approval traded for costs a flat 30% of fee — §6.3's own worked example (script +
    co-star approval = 30% cut) generalized per-approval rather than only for that specific pair."""
    discount = min(0.85, FEE_DISCOUNT_PER_APPROVAL * len(approvals))
    return base_fee * (1.0 - discount)
