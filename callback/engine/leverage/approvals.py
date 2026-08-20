"""design/part-06-leverage.md §6.3 — Approvals: contractual rights over a production, traded for
fee. "A fee cut of 30% for script and co-star approval is often the highest-value decision
available."
"""
from __future__ import annotations

import random

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

# §6.5 v21 — two real, distinct deal shapes, not one flat "backend point":
#
# First-dollar gross: paid on gross from the very first dollar, whether or not the film ever
# actually turns a profit — the studio eats that risk, which is exactly why only the biggest
# names ever get it. Rarer than a net-points deal — a higher Standing bar to access it at all —
# but the two real axes here are deliberately separate, matching how this actually works: whether
# you can get a first-dollar-gross deal at all is one negotiation; what percentage you land within
# it is a second, independent one. And because the studio is taking on real risk paying out
# regardless of profit, the percentage RANGE studios actually offer for first-dollar gross runs
# noticeably lower than the range for net points — even though net points nominally look bigger,
# they're the ones "Hollywood accounting" famously guts before they ever pay out.
#
# Net/backend points: the far more common deal — nothing pays out until the studio has actually
# recouped its own break-even (budget + marketing), and even then it's a real share of the actual
# profit above that line, not a flat cut of the whole gross regardless of how big a hit it was.
BOX_OFFICE_BONUS_TYPES = ("first_dollar_gross", "net_points")
FIRST_DOLLAR_GROSS_STANDING_THRESHOLD = 85.0  # clearly above net points' own 75 — the rarer ask

# The negotiated percentage itself — a real range, not a flat number, the same
# negotiated-position-in-a-band shape offers.negotiated_fee_share() already uses for the fee
# itself: actor_leverage (0-1, typically standing_score/100) pulls the outcome toward the top of
# the band, real noise on top means it never lands on the exact same number twice. First-dollar
# gross's own range sits below net points' — the real, lower offer range studios actually extend
# for a deal that pays out unconditionally, independent of the (harder) Standing bar to get one.
FIRST_DOLLAR_GROSS_SHARE_RANGE = (0.010, 0.035)  # of raw gross
NET_POINTS_SHARE_RANGE = (0.05, 0.20)  # of actual profit above break-even
BONUS_SHARE_NEGOTIATION_NOISE_SD = 0.15


def can_negotiate_approvals(standing_score: float) -> bool:
    return standing_score >= APPROVAL_STANDING_THRESHOLD


def fee_after_approvals(base_fee: float, approvals: frozenset[str]) -> float:
    """Each approval traded for costs a flat 30% of fee — §6.3's own worked example (script +
    co-star approval = 30% cut) generalized per-approval rather than only for that specific pair."""
    discount = min(0.85, FEE_DISCOUNT_PER_APPROVAL * len(approvals))
    return base_fee * (1.0 - discount)


def can_negotiate_box_office_bonus(standing_score: float, bonus_type: str = "net_points") -> bool:
    """Whether this deal shape is on the table at all — a separate question from what share you
    actually land within it (see negotiated_bonus_share())."""
    if bonus_type == "first_dollar_gross":
        return standing_score >= FIRST_DOLLAR_GROSS_STANDING_THRESHOLD
    return standing_score >= BOX_OFFICE_BONUS_STANDING_THRESHOLD


def negotiated_bonus_share(bonus_type: str, actor_leverage: float, rng: random.Random) -> float:
    """Where in this bonus type's own range (FIRST_DOLLAR_GROSS_SHARE_RANGE / NET_POINTS_SHARE_
    RANGE) the actual negotiated percentage lands — mirrors offers.negotiated_fee_share()'s own
    shape exactly. actor_leverage (0-1) pulls toward the top of the band; real noise on top means
    even a maximally leveraged negotiation doesn't land on the same number twice."""
    lo, hi = FIRST_DOLLAR_GROSS_SHARE_RANGE if bonus_type == "first_dollar_gross" else NET_POINTS_SHARE_RANGE
    position = max(0.0, min(1.0, actor_leverage + rng.gauss(0.0, BONUS_SHARE_NEGOTIATION_NOISE_SD)))
    return lo + (hi - lo) * position


# v19 — directing's own base fee (simulation._director.DIRECTOR_FEE_SHARE_STUDIO/HIRE) was a flat
# constant, never negotiated at all — every director earned the exact same cut of budget
# regardless of Standing, unlike the box-office bonus just above (a real band, leverage-scaled)
# or the actor track's own negotiated_fee_share (actor/offers.py), which this mirrors exactly.
DIRECTOR_FEE_SHARE_STUDIO_RANGE = (0.03, 0.08)  # of budget — studio-backed, midpoint matches the
# old flat 0.05 so an average-leverage director sees roughly the same fee as before this pass
DIRECTOR_FEE_SHARE_HIRE_RANGE = (0.06, 0.12)  # of budget — a hire's "sellout" premium, midpoint
# matches the old flat 0.08
DIRECTOR_FEE_NEGOTIATION_NOISE_SD = 0.15


def negotiated_director_fee_share(fee_range: tuple[float, float], director_leverage: float, rng: random.Random) -> float:
    """Same band-position shape as negotiated_bonus_share/actor.offers.negotiated_fee_share:
    director_leverage (0-1, typically standing_score/100) pulls toward the top of the band, real
    noise on top means even a maximally-leveraged negotiation doesn't land on the same cut twice."""
    lo, hi = fee_range
    position = max(0.0, min(1.0, director_leverage + rng.gauss(0.0, DIRECTOR_FEE_NEGOTIATION_NOISE_SD)))
    return lo + (hi - lo) * position


def box_office_bonus_earned(gross_millions: float, break_even_millions: float, share: float, bonus_type: str = "net_points") -> float:
    """share: the real, already-negotiated percentage (negotiated_bonus_share(), rolled once at
    Deal time — never re-rolled at payout). "first_dollar_gross" pays on raw gross regardless of
    profitability. "net_points" (the default) pays nothing below break_even_millions, and above it
    pays `share` of the actual profit — genuinely based on how profitable the film turned out to
    be, not a flat cut of its whole gross."""
    if bonus_type == "first_dollar_gross":
        return share * max(0.0, gross_millions)
    profit = max(0.0, gross_millions - break_even_millions)
    return share * profit
