"""design/part-08-the-studio.md §8.2's Marketing(b) curve and the broader "different money plays
differently" idea, read down onto a single actor's project rather than a studio-executive slate.
Every film you're offered comes from a producing studio with its own money and its own instincts
for spending it — that's a real difference in how your film reaches an audience, on top of (never
instead of) the release-strategy choice you already make at Post & Release.

reception.py's BREAK_EVEN_MARKETING_SHARE (0.45) stays the sane default for anything that doesn't
pass a studio through — this module is additive, not a replacement for that baseline.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.actor.reception import BREAK_EVEN_MARKETING_SHARE, RIGHTS_SHARE
from callback.engine.actor.release import STREAMING_BUYOUT_MULTIPLIER
from callback.engine.core.util import clamp

# How much a marketing share above/below the 0.45 baseline moves the opening-weekend multiplier.
# A studio spending 10 points of budget more than baseline buys roughly a 6% bigger opening —
# visibility, not quality; resolve_reception's quality terms (script/director/craft_contribution) are
# untouched by any of this, exactly as release.py's own docstring insists a release strategy
# never changes whether the film is good.
OPENING_MARKETING_COEF = 0.60


@dataclass(frozen=True)
class Studio:
    id: str
    name: str
    tagline: str
    marketing_share: float  # fraction of budget spent on marketing, at a mid-size budget
    tiered_marketing: bool  # True: recompute per §8.2's Marketing(b) curve instead of a flat share
    rights_share_delta: float  # added to RIGHTS_SHARE — how much of the gross reaches you at all
    festival_tier_bonus: float  # added to festival_acquisition_probability's sigmoid input
    streaming_multiplier_delta: float  # added to release.py's STREAMING_BUYOUT_MULTIPLIER
    budget_range: tuple[float, float]  # $M film budget this studio plausibly finances
    preferred_release: str  # release.py strategy key this studio pushes for by default


# §8.2's own tiered curve, ported here (not re-derived) for the one studio whose whole identity
# is "marketing scales with budget the way the tentpole machine actually spends":
# Marketing(b) = 0.35b if b<10; 0.48b if b<50; 0.55b if b<100; 0.80b otherwise
def _tentpole_marketing_share(budget_millions: float) -> float:
    if budget_millions < 10:
        return 0.35
    if budget_millions < 50:
        return 0.48
    if budget_millions < 100:
        return 0.55
    return 0.80


STUDIOS: dict[str, Studio] = {
    "indie": Studio(
        id="indie", name="A small indie house",
        tagline="No marketing budget to speak of — they're betting on festivals and word of mouth.",
        marketing_share=0.20, tiered_marketing=False, rights_share_delta=0.08,
        festival_tier_bonus=0.35, streaming_multiplier_delta=-0.05,
        budget_range=(0.0, 15.0), preferred_release="festival",
    ),
    "mid_major": Studio(
        id="mid_major", name="A mid-major studio",
        tagline="Standard money, standard playbook — a real theatrical push, nothing extravagant.",
        marketing_share=BREAK_EVEN_MARKETING_SHARE, tiered_marketing=False, rights_share_delta=0.0,
        festival_tier_bonus=0.0, streaming_multiplier_delta=0.0,
        budget_range=(8.0, 55.0), preferred_release="wide",
    ),
    "prestige": Studio(
        id="prestige", name="A prestige awards house",
        tagline="They spend on campaigns, not trailers — this film is built to be talked about in January.",
        marketing_share=0.50, tiered_marketing=False, rights_share_delta=0.03,
        festival_tier_bonus=0.55, streaming_multiplier_delta=-0.10,
        budget_range=(12.0, 65.0), preferred_release="limited",
    ),
    "blockbuster": Studio(
        id="blockbuster", name="A blockbuster machine",
        tagline="Marketing scales with the budget — a wall-to-wall campaign, and a much bigger bill.",
        marketing_share=0.0, tiered_marketing=True, rights_share_delta=-0.05,
        festival_tier_bonus=-0.20, streaming_multiplier_delta=0.0,
        budget_range=(45.0, 300.0), preferred_release="wide",
    ),
    "streamer": Studio(
        id="streamer", name="A streamer-backed production",
        tagline="Almost no theatrical marketing — the payout is flat and guaranteed either way.",
        marketing_share=0.08, tiered_marketing=False, rights_share_delta=-0.02,
        festival_tier_bonus=-0.10, streaming_multiplier_delta=0.18,
        budget_range=(15.0, 130.0), preferred_release="streaming",
    ),
}

STUDIO_IDS = tuple(STUDIOS.keys())


# The studio has the final say on how a film gets released — your request is real input, not a
# choice you simply get to make. How much it actually sways them scales with how much they trust
# you (studio_relations) and how big a star you currently are (Standing's own standing_score,
# 0-100): a nobody's ask is noise against the studio's own preferred_release; a trusted A-lister's
# is close to a mandate.
STUDIO_INFLUENCE_BASE = 0.10
STUDIO_INFLUENCE_TRUST_COEF = 0.35  # (trust-50)/100 -> -0.35..0.35
STUDIO_INFLUENCE_IMPORTANCE_COEF = 0.45  # standing_score/100 -> 0..0.45
STUDIO_INFLUENCE_FLOOR = 0.03  # even a burned, nobody actor sometimes gets their way
STUDIO_INFLUENCE_CEILING = 0.92  # even the biggest star doesn't always overrule the studio


def actor_influence_on_release(trust: float, actor_importance: float) -> float:
    """Probability the studio actually goes with the actor's requested release strategy instead
    of its own preferred_release."""
    trust_component = (trust - 50.0) / 100.0
    importance_component = actor_importance / 100.0
    influence = (
        STUDIO_INFLUENCE_BASE
        + STUDIO_INFLUENCE_TRUST_COEF * trust_component
        + STUDIO_INFLUENCE_IMPORTANCE_COEF * importance_component
    )
    return clamp(influence, STUDIO_INFLUENCE_FLOOR, STUDIO_INFLUENCE_CEILING)


def decide_release_strategy(
    studio: Studio, requested_strategy: str, trust: float, actor_importance: float, rng: random.Random,
) -> str:
    """The studio's actual call — requested_strategy only wins with probability
    actor_influence_on_release(); otherwise the studio releases the film its own way."""
    influence = actor_influence_on_release(trust, actor_importance)
    return requested_strategy if rng.random() < influence else studio.preferred_release


def marketing_share_for(studio: Studio, budget_millions: float) -> float:
    if studio.tiered_marketing:
        return _tentpole_marketing_share(budget_millions)
    return studio.marketing_share


def pick_studio(budget_millions: float, rng: random.Random) -> Studio:
    """A film's budget determines who could plausibly be financing it — a $4M film never lands
    at the blockbuster machine, a $200M one never lands at the indie house. Picks uniformly among
    whichever studios' budget_range actually contains this film (ranges overlap in the middle on
    purpose, so a $30M film could be a mid-major or a prestige play), falling back to mid_major
    for anything outside every range."""
    fits = [s for s in STUDIOS.values() if s.budget_range[0] <= budget_millions <= s.budget_range[1]]
    if not fits:
        return STUDIOS["mid_major"]
    return rng.choice(fits)


# A streaming buyer who isn't in the business of financing your kind of film at all doesn't bid —
# the same budget-range gate pick_studio() already uses, not a second concept.
def _can_credibly_bid(studio: Studio, budget_millions: float) -> bool:
    lo, hi = studio.budget_range
    return lo * 0.5 <= budget_millions <= hi * 1.5  # a wider band than financing — buying rights
    #                                                   is a smaller commitment than making it


SELF_DISTRIBUTE_MULTIPLIER = 1.0  # your own financing studio just puts it up — you get your budget
                                   # back and nothing more, the "for nothing" option


def streaming_bidders(budget_millions: float, financing_studio_id: str) -> list[Studio]:
    """The candidate pool by budget alone — every studio whose money actually plays in this budget
    range, deterministic (no rng). This is a wide, pre-sale "who could plausibly buy this" list;
    it says nothing about whether any of them actually want THIS film once it's finished — see
    quality_adjusted_bids() for the real offers once the movie is made. Always includes the film's
    own financing studio, who can either bid their normal streaming terms or — see
    SELF_DISTRIBUTE_MULTIPLIER — just put it up for nothing rather than sell the rights at all."""
    financing = STUDIOS[financing_studio_id]
    bidders = [s for s in STUDIOS.values() if _can_credibly_bid(s, budget_millions)]
    if financing not in bidders:
        bidders = [financing, *bidders]
    return bidders


# "Perception can differ and vary within a certain range" — each outside bidder reads the finished
# film's quality with its own noise, not one shared number.
QUALITY_PERCEPTION_SPREAD = 10.0
# Below this perceived quality a non-financing buyer just doesn't bid at all — an awful, un-hyped
# film can draw zero outside offers, not merely a cheap one.
QUALITY_BID_FLOOR = 30.0
QUALITY_MULTIPLIER_FLOOR = 0.55
QUALITY_MULTIPLIER_CEILING = 1.45


def _quality_multiplier(perceived_quality: float) -> float:
    # 50 (an average film) leaves the base streaming multiplier unchanged; better or worse
    # perceived quality scales the payout up or down from there.
    return clamp(0.5 + perceived_quality / 100.0, QUALITY_MULTIPLIER_FLOOR, QUALITY_MULTIPLIER_CEILING)


@dataclass(frozen=True)
class StreamingBid:
    studio_id: str
    studio_name: str
    multiplier: float
    payout_millions: float
    self_distribute: bool


def quality_adjusted_bids(
    budget_millions: float,
    financing_studio_id: str,
    film_critic_score: float,
    audience_score: float,
    rng: random.Random,
) -> list[StreamingBid]:
    """The real streaming offers — resolved once the film is actually finished and its quality is
    known, not a budget-only preview. A great film draws more bidders at better terms; an awful one
    draws few or none, since each outside buyer's read on it varies (QUALITY_PERCEPTION_SPREAD)
    instead of everyone agreeing on the same verdict. The financing studio's own offer (its normal
    terms, plus the always-available SELF_DISTRIBUTE_MULTIPLIER "for nothing" option) is unaffected
    by quality — they already own the film either way."""
    financing = STUDIOS[financing_studio_id]
    quality = (film_critic_score + audience_score) / 2.0
    pool = [s for s in STUDIOS.values() if _can_credibly_bid(s, budget_millions) and s is not financing]

    bids: list[StreamingBid] = []
    for studio in pool:
        perceived = clamp(rng.gauss(quality, QUALITY_PERCEPTION_SPREAD), 0.0, 100.0)
        if perceived < QUALITY_BID_FLOOR:
            continue  # this buyer passes on it entirely
        multiplier = (STREAMING_BUYOUT_MULTIPLIER + studio.streaming_multiplier_delta) * _quality_multiplier(perceived)
        bids.append(StreamingBid(
            studio.id, studio.name, round(multiplier, 2), round(budget_millions * multiplier, 2), False,
        ))

    financing_multiplier = STREAMING_BUYOUT_MULTIPLIER + financing.streaming_multiplier_delta
    bids.append(StreamingBid(
        financing.id, financing.name, round(financing_multiplier, 2),
        round(budget_millions * financing_multiplier, 2), False,
    ))
    bids.append(StreamingBid(
        financing.id, financing.name, SELF_DISTRIBUTE_MULTIPLIER,
        round(budget_millions * SELF_DISTRIBUTE_MULTIPLIER, 2), True,
    ))
    return bids
