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

# A box-office bonus (a real backend point, not the fee-vs-approvals trade above) needs a higher
# bar than approvals — §6.5's own executive-producer-credit row already gates a small backend
# behind Indispensability 55; this is the general-case version, gated on Standing instead, and set
# higher than the 65 approvals ask on purpose: real profit participation is a rarer, harder get
# than script/co-star/director/cut approval. Originally 80 — checked against the actor's Standing
# *before* that year's own film (the only sensible timing; you negotiate before you shoot), a real
# trial run genuinely sustaining "a star"-tier Standing for over a decade straight (weighted score
# 68-79.8 for 25+ consecutive years) still only crossed 80 exactly once in a 45-year career. That's
# not a stale-check bug, it's a threshold so narrow it was barely reachable even at the top of the
# game — brought down to 75, still a real bar clearly above approvals' 65, but one a sustained star
# can actually clear and hold rather than a single-year fluke.
BOX_OFFICE_BONUS_STANDING_THRESHOLD = 75.0
BOX_OFFICE_BONUS_SHARE = 0.03  # of the film's Gross, paid only if it actually clears break-even


def can_negotiate_approvals(standing_score: float) -> bool:
    return standing_score >= APPROVAL_STANDING_THRESHOLD


def fee_after_approvals(base_fee: float, approvals: frozenset[str]) -> float:
    """Each approval traded for costs a flat 30% of fee — §6.3's own worked example (script +
    co-star approval = 30% cut) generalized per-approval rather than only for that specific pair."""
    discount = min(0.85, FEE_DISCOUNT_PER_APPROVAL * len(approvals))
    return base_fee * (1.0 - discount)


def can_negotiate_box_office_bonus(standing_score: float) -> bool:
    return standing_score >= BOX_OFFICE_BONUS_STANDING_THRESHOLD


def box_office_bonus_earned(gross_millions: float, roi: float) -> float:
    """A real backend point only pays out if the film actually made its money back — a bonus on
    a film that lost money is worth zero, the same way a real gross-points deal would be."""
    if roi <= 1.0:
        return 0.0
    return BOX_OFFICE_BONUS_SHARE * gross_millions
