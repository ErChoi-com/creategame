"""design/part-03-design-overview.md §3.4's core loop names this as its own step — "5. POST &
RELEASE | Edit can help or hurt you. Festival vs wide vs dumped vs shelved" — but design/ never
built the mechanic past that one line. This module is that mechanic: reception.resolve_reception()
still computes a film's actual quality (ProjectQuality/FilmCriticScore/AudienceScore) exactly as
before — a release strategy never changes whether the film is good — but the box-office numbers
riding on top of that quality (Opening/Legs/Gross/ROI) depend heavily on how it reaches an
audience, and that's a real, consequential choice.

Festival acquisition reuses design/part-10-the-world.md §10.3's own published formula
(P(acquired) = sigmoid(...), unsold films return ROI = 0) rather than inventing a new one.
"""
from __future__ import annotations

import random
from dataclasses import replace

from callback.engine.actor.reception import BREAK_EVEN_MARKETING_SHARE, RIGHTS_SHARE, ReceptionResult
from callback.engine.core.util import sigmoid

WIDE, LIMITED, FESTIVAL, STREAMING, SHELVED = "wide", "limited", "festival", "streaming", "shelved"
RELEASE_STRATEGIES = (WIDE, LIMITED, FESTIVAL, STREAMING, SHELVED)

# Limited/platform release (§3.4): smaller opening, word-of-mouth (already-computed Legs) matters
# proportionally more than a wide release's marketing-driven opening weekend.
LIMITED_OPENING_SHARE = 0.22
LIMITED_LEGS_BONUS = 1.35

# §10.3's festival acquisition formula, quoted directly:
# P(acquired) = sigmoid(0.08*(FilmCriticScore-55) + 0.05*(CastStarPower-40)
#                        + festivalTierBonus + audienceAwardBonus)
FESTIVAL_CRITIC_COEF = 0.08
FESTIVAL_CRITIC_CENTRE = 55.0
FESTIVAL_STAR_COEF = 0.05
FESTIVAL_STAR_CENTRE = 40.0

# §8.3's streamer-buyout preset: "Budget plus 20% guaranteed, no backend, no theatrical."
STREAMING_BUYOUT_MULTIPLIER = 1.20

# A festival-acquisition sale is a genuine distribution guarantee, not a streamer's full-budget-
# plus-margin buyout — the buyer is committing to P&A spend and a real box-office bet on a small
# film, not covering the whole production. Calibrated below STREAMING_BUYOUT_MULTIPLIER's own floor
# so selling at a festival is a real, sometimes-worse-than-self-releasing tradeoff, not a strictly
# dominant option — see actor/studios.py's quality_adjusted_festival_bids for the competing-offer
# resolution built on top of this base (this module never imports studios.py — see apply_release_
# strategy's festival_sale_resolver param for how that bidding gets wired in from outside instead).
FESTIVAL_ACQUISITION_BASE_MULTIPLIER = 0.55

SHELVED_ROI = -1.0  # a total loss on the budget — "the film didn't come out"


def festival_acquisition_probability(
    film_critic_score: float,
    cast_star_power: float,
    festival_tier_bonus: float = 0.0,
    audience_award_bonus: float = 0.0,
) -> float:
    return sigmoid(
        FESTIVAL_CRITIC_COEF * (film_critic_score - FESTIVAL_CRITIC_CENTRE)
        + FESTIVAL_STAR_COEF * (cast_star_power - FESTIVAL_STAR_CENTRE)
        + festival_tier_bonus
        + audience_award_bonus
    )


def _marketing(reception: ReceptionResult, marketing_share: float) -> float:
    return marketing_share * reception.budget


def _roi(gross: float, budget: float, marketing: float, rights_share: float) -> float:
    return (rights_share * gross) / (budget + marketing) if (budget + marketing) > 0 else 0.0


def apply_release_strategy(
    reception: ReceptionResult,
    strategy: str,
    rng: random.Random,
    cast_star_power: float = 50.0,
    festival_tier_bonus: float = 0.0,
    audience_award_bonus: float = 0.0,
    marketing_share: float | None = None,
    rights_share: float | None = None,
    streaming_multiplier: float = STREAMING_BUYOUT_MULTIPLIER,
    festival_sale_resolver=None,
) -> ReceptionResult:
    """Takes an already-resolved (wide-release-shaped) ReceptionResult — quality scores untouched
    — and adjusts only Gross/ROI for the chosen release strategy. Additive: doesn't change
    resolve_reception()'s signature or any of its other callers.

    marketing_share/rights_share: the producing studio's own money terms (actor/studios.py),
    defaulting to this module's flat constants when a caller doesn't have a studio to hand.
    streaming_multiplier: a studio's own streamer-buyout multiplier, defaulting to the flat
    §8.3 preset (STREAMING_BUYOUT_MULTIPLIER) when not given.
    festival_sale_resolver: (reception, marketing_share, rights_share) -> ReceptionResult, called
    only once a festival submission actually clears festival_acquisition_probability's own gate —
    an unsold submission never reaches it. This module can't build the real competing-distributor
    bid pool itself (actor/studios.py imports FROM here, so importing it back would be circular);
    the caller (simulation.career.resolve_release_schedule) builds the resolver externally, using
    studios.quality_adjusted_festival_bids for outside offers plus the financing side's own real
    self-release LIMITED numbers, and hands back whichever the chosen bid implies. None (every
    caller that doesn't care who buys it — verify.py, tests, simulation._director's own festival
    path) falls back to the old behavior: acquired always means a LIMITED release at the financing
    side's own terms, no sale price of its own."""
    m_share = marketing_share if marketing_share is not None else BREAK_EVEN_MARKETING_SHARE
    r_share = rights_share if rights_share is not None else RIGHTS_SHARE

    if strategy == WIDE:
        return reception

    marketing = _marketing(reception, m_share)

    if strategy == LIMITED:
        gross = reception.opening * LIMITED_OPENING_SHARE * (reception.legs * LIMITED_LEGS_BONUS)
        return replace(reception, gross=gross, marketing=marketing, roi=_roi(gross, reception.budget, marketing, r_share))

    if strategy == FESTIVAL:
        p_acquired = festival_acquisition_probability(
            reception.film_critic_score, cast_star_power, festival_tier_bonus, audience_award_bonus,
        )
        if rng.random() >= p_acquired:
            # §10.3 — unsold: no distributor ever bought it, so no theatrical marketing was ever spent.
            return replace(reception, gross=0.0, marketing=0.0, roi=0.0)
        if festival_sale_resolver is not None:
            return festival_sale_resolver(reception, m_share, r_share)
        return apply_release_strategy(
            reception, LIMITED, rng, cast_star_power, marketing_share=m_share, rights_share=r_share,
        )  # acquired -> a platform release

    if strategy == STREAMING:
        # §8.3's own framing: "no theatrical" — the flat buyout replaces marketing spend entirely.
        # roi is a multiple (1.0 = exact break-even), matching every other release path and
        # simulation/bands.ROI_BANDS' own scale — NOT a gain fraction (0.0 = break-even), which
        # would silently misband a guaranteed-profitable streaming_multiplier > 1.0 deal as a loss.
        payout = reception.budget * streaming_multiplier
        roi = payout / reception.budget if reception.budget > 0 else 0.0
        return replace(reception, gross=payout, marketing=0.0, roi=roi)

    if strategy == SHELVED:
        # the film never reached an audience — whatever was budgeted for marketing was never spent.
        return replace(reception, gross=0.0, marketing=0.0, roi=SHELVED_ROI)

    return reception


def weekly_gross_curve(opening: float, legs: float, weeks: int = 6) -> list[float]:
    """A derived visualization of Gross, not a new formula affecting ROI — geometric decay whose
    ratio is chosen so the (infinite) series sums to legs weeks of "opening," giving a real
    week-by-week trajectory (the shape "legs" is actually named after) instead of one flat total."""
    ratio = max(0.0, min(0.85, 1.0 - 1.0 / max(legs, 1.01)))
    return [opening * (ratio ** i) for i in range(weeks)]
