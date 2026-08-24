"""A real trade, not modeled under this name in design/ but a direct mechanical extension of the
same risk/reward shape the Indispensability holdout (leverage/indispensability.py) and Disappear
(§6.6) already use: lock in guaranteed work and a fixed floor budget across several future films
with one studio, in exchange for the freedom to negotiate a better deal project-by-project. The
studio pays a premium over your quote right now to buy that certainty from you; walking away from
a signed deal early costs real reputation, the same asymmetric-trust read simulation/_relationships
.py already applies to a studio you've burned.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

MULTI_PICTURE_MIN_STANDING = 40.0  # you need to already be a real quantity for a studio to bother locking you in
MULTI_PICTURE_MIN_FILMS = 2
MULTI_PICTURE_MAX_FILMS = 5

DEAL_LOCKED_QUOTE_PREMIUM = 1.15  # the studio pays over your quote *right now* to buy the certainty
BREAK_NOTORIETY_PENALTY = 12.0  # walking away from a signed deal early costs real reputation


@dataclass(frozen=True)
class MultiPictureDeal:
    studio_id: str
    films_remaining: int
    guaranteed_budget_millions: float  # per-film floor for the life of the deal
    signed_year: int


def deal_terms(quote_value: float, film_count: int) -> tuple[float, float]:
    """Returns (per-film guaranteed budget floor, total value across the deal)."""
    guaranteed = quote_value * DEAL_LOCKED_QUOTE_PREMIUM
    return guaranteed, guaranteed * film_count


def sign_deal(studio_id: str, quote_value: float, film_count: int, current_year: int) -> MultiPictureDeal:
    guaranteed, _ = deal_terms(quote_value, film_count)
    return MultiPictureDeal(studio_id=studio_id, films_remaining=film_count,
                             guaranteed_budget_millions=guaranteed, signed_year=current_year)


def fulfill_one(deal: MultiPictureDeal) -> MultiPictureDeal | None:
    """Called when the actor takes a guaranteed listing from the deal's own studio. Returns None
    once the deal is fully worked off."""
    remaining = deal.films_remaining - 1
    if remaining <= 0:
        return None
    return replace(deal, films_remaining=remaining)
