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
    """A real bidding pool, not one flat number: every studio whose money actually plays in this
    budget range makes an offer at its own §8.3-style terms (STREAMING_BUYOUT_MULTIPLIER +
    streaming_multiplier_delta) — deliberately deterministic (no rng) so the pool is a stable menu
    a player can compare and choose from, not a fresh roll each look. Always includes the film's
    own financing studio, who can either bid their normal streaming terms or — see
    SELF_DISTRIBUTE_MULTIPLIER — just put it up for nothing rather than sell the rights at all."""
    financing = STUDIOS[financing_studio_id]
    bidders = [s for s in STUDIOS.values() if _can_credibly_bid(s, budget_millions)]
    if financing not in bidders:
        bidders = [financing, *bidders]
    return bidders
