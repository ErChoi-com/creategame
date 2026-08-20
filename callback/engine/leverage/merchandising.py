"""A new mechanic, not adapted from an existing one: every other deal in this engine — a fee, a
box-office bonus, a director's income — pays out once, at resolution time. Merchandising royalties
are the first genuinely ongoing, multi-year income stream in the whole design: the real reason a
voice actor on a beloved animated franchise keeps earning off the toy shelf years after the film
itself has been made and forgotten, independent of whether they ever work again.

Deliberately compartmentalized, the same way leverage/indispensability.py already is: this module
knows nothing about Role, FranchiseEntry, or Session — every function takes plain floats/dataclasses
of its own. The caller (simulation/full_career.py) reads whatever franchise-state numbers it needs
(indispensability, studio_protectiveness) and hands them in; this module never imports simulation._
franchises or actor.offers, so it stays testable and reusable on its own, and a future caller
outside the actor track (a director's own franchise, say) could reuse it without dragging in
anything actor-specific.

Only the negotiation and the annual payout are built this pass. Deliberately out of scope, written
up in design/ instead of built: a studio buyout offer on the stream, renegotiating a locked share
as the franchise grows past what it was worth at signing, a notoriety-driven suspension clause, and
a lifetime-royalty line in the obituary — real, bounded follow-ups, not attempted here.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.core.util import clamp

# Only an animated franchise role can negotiate this at all — merchandising in the toy-shelf sense
# modeled here is a real, dominant revenue stream specifically for animation (see actor/offers.py's
# own Role.is_animation), not live action's own, rarer, differently-shaped licensing deals. The
# caller enforces the is_animation/franchise_id gate; this module only knows about Standing.
MERCH_STANDING_THRESHOLD = 55.0  # a real ask — roughly halfway between approvals (65) and nothing

# A real royalty-point range, not a flat number — the same negotiated-position-in-a-band shape
# leverage.approvals.negotiated_bonus_share already uses. Small, compounding percentages: this
# pays on raw merchandising revenue, not net profit, the same "the studio eats the risk, so the
# percentage itself runs low" logic first-dollar-gross already established.
MERCH_SHARE_RANGE = (0.01, 0.06)
MERCH_SHARE_MIDPOINT = sum(MERCH_SHARE_RANGE) / 2.0
MERCH_SHARE_NEGOTIATION_NOISE_SD = 0.15

# The same "the studio protects the property, not the individual" pull already established twice
# this pass (leverage.indispensability.resolve_holdout's recast pull, actor.studios.
# quality_adjusted_bids' bid floor) — reused here as a third consumer of the same idea rather than
# a new formula: a studio protecting a proven character doesn't give up a big cut of its own
# merchandising on it easily.
MERCH_PROTECTIVENESS_SHARE_COEF = 0.006

# The annual payout: a real multiplier off the character's own CURRENT indispensability
# (leverage/indispensability.py) — already exactly the right signal (how attached audiences still
# are to this character), and it already decays on its own as a franchise goes dormant. No separate
# decay curve lives here at all — the caller reads live indispensability fresh every year, so a
# fading franchise's royalty fades with it automatically, and a revived one (a reboot) pays out
# again just as automatically, for free, with no special-case code anywhere in this module.
MERCH_ANNUAL_BASE_MILLIONS = 0.35  # a baseline year's royalty at MERCH_SHARE_RANGE's own midpoint
# share and MERCH_INDISPENSABILITY_MIDPOINT indispensability — small individually, real over a
# decade-plus run on a beloved character.
MERCH_INDISPENSABILITY_MIDPOINT = 50.0


def can_negotiate_merchandising(standing_score: float) -> bool:
    return standing_score >= MERCH_STANDING_THRESHOLD


def negotiated_merch_share(actor_leverage: float, studio_protectiveness: float, rng: random.Random) -> float:
    """actor_leverage (0-1, typically standing_score/100) pulls the negotiated share toward the
    top of MERCH_SHARE_RANGE; studio_protectiveness (0-100, simulation._franchises.
    studio_protectiveness()) pulls it back down — real noise on top means it never lands on the
    same number twice."""
    lo, hi = MERCH_SHARE_RANGE
    position = clamp(
        actor_leverage - MERCH_PROTECTIVENESS_SHARE_COEF * studio_protectiveness
        + rng.gauss(0.0, MERCH_SHARE_NEGOTIATION_NOISE_SD),
        0.0, 1.0,
    )
    return lo + (hi - lo) * position


@dataclass(frozen=True)
class MerchandisingDeal:
    franchise_id: str
    royalty_share: float  # locked at signing — never renegotiated by this pass, see module docstring
    signed_year: int


def annual_royalty_payout(royalty_share: float, character_indispensability: float) -> float:
    """character_indispensability: the franchise's own current indispensability, 0-100, read fresh
    every year by the caller — not a value snapshotted at signing. Zero indispensability (a
    property that's fully released the actor, per leverage.indispensability.decay_dormant) pays
    exactly zero; there's no floor and no separate cap here, the same uncapped shape leverage.
    approvals.box_office_bonus_earned already uses for an ongoing hit."""
    share_factor = royalty_share / MERCH_SHARE_MIDPOINT
    indispensability_factor = character_indispensability / MERCH_INDISPENSABILITY_MIDPOINT
    return max(0.0, MERCH_ANNUAL_BASE_MILLIONS * share_factor * indispensability_factor)
