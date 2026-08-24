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

from callback.engine.actor.rating import RATING_BAND_ORDER, RATING_CUT, RATING_RELEASE_AS_SHOT, rating_band
from callback.engine.actor.reception import BREAK_EVEN_MARKETING_SHARE, RIGHTS_SHARE
from callback.engine.actor.release import FESTIVAL_ACQUISITION_BASE_MULTIPLIER, STREAMING_BUYOUT_MULTIPLIER
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
    festival_acquisition_multiplier_delta: float  # added to release.py's FESTIVAL_ACQUISITION_
    # BASE_MULTIPLIER when this studio bids to BUY festival distribution rights — a distinct axis
    # from festival_tier_bonus above, which only affects whether a submission gets acquired at all,
    # never what a buyer actually pays for it.
    budget_range: tuple[float, float]  # $M film budget this studio plausibly finances
    preferred_release: str  # release.py strategy key this studio pushes for by default
    rating_ceiling: str  # the harshest rating.RATING_BAND_ORDER label this studio is comfortable
    # financing at full commitment before it starts pushing for a cut — see decide_rating_cut()


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
        festival_acquisition_multiplier_delta=0.20,  # the archetypal festival-acquisitions buyer
        budget_range=(0.0, 15.0), preferred_release="festival", rating_ceiling="NC-17",
    ),
    "mid_major": Studio(
        id="mid_major", name="A mid-major studio",
        tagline="Standard money, standard playbook — a real theatrical push, nothing extravagant.",
        marketing_share=BREAK_EVEN_MARKETING_SHARE, tiered_marketing=False, rights_share_delta=0.0,
        festival_tier_bonus=0.0, streaming_multiplier_delta=0.0,
        festival_acquisition_multiplier_delta=0.0,
        budget_range=(8.0, 55.0), preferred_release="wide", rating_ceiling="R",
    ),
    "prestige": Studio(
        id="prestige", name="A prestige awards house",
        tagline="They spend on campaigns, not trailers — this film is built to be talked about in January.",
        marketing_share=0.50, tiered_marketing=False, rights_share_delta=0.03,
        festival_tier_bonus=0.55, streaming_multiplier_delta=-0.10,
        festival_acquisition_multiplier_delta=0.10,  # pays well for the right title, not the widest net
        budget_range=(12.0, 65.0), preferred_release="limited", rating_ceiling="NC-17",
    ),
    "blockbuster": Studio(
        id="blockbuster", name="A blockbuster machine",
        tagline="Marketing scales with the budget — a wall-to-wall campaign, and a much bigger bill.",
        marketing_share=0.0, tiered_marketing=True, rights_share_delta=-0.05,
        festival_tier_bonus=-0.20, streaming_multiplier_delta=0.0,
        festival_acquisition_multiplier_delta=-0.25,  # not in the small-acquisitions business at all
        budget_range=(45.0, 300.0), preferred_release="wide", rating_ceiling="PG-13",
    ),
    "streamer": Studio(
        id="streamer", name="A streamer-backed production",
        tagline="Almost no theatrical marketing — the payout is flat and guaranteed either way.",
        marketing_share=0.08, tiered_marketing=False, rights_share_delta=-0.02,
        festival_tier_bonus=-0.10, streaming_multiplier_delta=0.18,
        festival_acquisition_multiplier_delta=0.05,  # will scoop up a festival darling, but it's not their lane
        budget_range=(15.0, 130.0), preferred_release="streaming", rating_ceiling="PG-13",
    ),
}

STUDIO_IDS = tuple(STUDIOS.keys())


# The studio has the final say on how a film gets released — your request is real input, not a
# choice you simply get to make. How much it actually sways them is dominated by how big a star
# you are right now (Standing's own standing_score, 0-100) — trust only wobbles that up or down
# within a bounded band, it can never invert the ordering: a real A-lister always outweighs a real
# nobody, no matter how burned the studio is on the star or how much they love the nobody. Fame is
# the lever; trust is the modifier on the lever, not a second lever of the same size. And fame
# itself has to be real: STUDIO_INFLUENCE_IMPORTANCE_POWER=4 means moderate, "rising star" fame
# barely registers — genuine sway only shows up once an actor is very close to the top of the
# scale, not just above-average.
STUDIO_INFLUENCE_BASE = 0.03
STUDIO_INFLUENCE_IMPORTANCE_COEF = 0.85  # importance's ceiling contribution — dominant on purpose
STUDIO_INFLUENCE_IMPORTANCE_POWER = 4.0  # steeply convex: needs top-tier fame, not just above-average, to matter
STUDIO_INFLUENCE_TRUST_SWING = 0.20  # trust can only scale the importance term by +/-20%, never overturn it
STUDIO_INFLUENCE_FLOOR = 0.02  # even a burned, nobody actor sometimes gets their way
STUDIO_INFLUENCE_CEILING = 0.92  # even the biggest, most trusted star doesn't get an automatic yes


def actor_influence_on_studio_decision(trust: float, actor_importance: float) -> float:
    """The shared "how much does the studio actually listen to you" curve — used for both the
    release-strategy request and the marketing-push request below, since it's the same underlying
    social dynamic (how much say a working relationship buys you) either time. actor_importance is
    the dominant, steeply-scaling term (a real A-lister at any trust level always outweighs a real
    nobody at any trust level — a total-nobody's importance term is 0, so trust can't move them off
    the floor at all); trust only modulates an already-famous actor's own leverage up or down by a
    bounded +/-20%. The power-4 curve means real influence takes real, top-tier fame — an actor
    who's merely above average still gets mostly overruled."""
    importance_term = STUDIO_INFLUENCE_IMPORTANCE_COEF * (max(actor_importance, 0.0) / 100.0) ** STUDIO_INFLUENCE_IMPORTANCE_POWER
    trust_multiplier = 1.0 + STUDIO_INFLUENCE_TRUST_SWING * (trust - 50.0) / 50.0
    influence = STUDIO_INFLUENCE_BASE + importance_term * trust_multiplier
    return clamp(influence, STUDIO_INFLUENCE_FLOOR, STUDIO_INFLUENCE_CEILING)


# Backward-compatible name — release-strategy call sites keep importing this exact function.
actor_influence_on_release = actor_influence_on_studio_decision

# A director asking the studio to release or market *their own* film starts from a genuinely
# stronger position than a hired actor lobbying on someone else's — it's their picture, their name
# on it either way. Same shape of curve (still convex, still bounded, still never a guaranteed
# yes), but a real, higher floor (0.08 vs 0.02) and a gentler power (3 vs 4) so it climbs faster
# through the low-and-middle range — without raising the ceiling at all: even the biggest director
# tops out at the same 0.92 an A-lister actor does, not higher.
DIRECTOR_INFLUENCE_BASE = 0.10
DIRECTOR_INFLUENCE_IMPORTANCE_COEF = 0.85
DIRECTOR_INFLUENCE_IMPORTANCE_POWER = 3.0
DIRECTOR_INFLUENCE_TRUST_SWING = 0.20
DIRECTOR_INFLUENCE_FLOOR = 0.08
DIRECTOR_INFLUENCE_CEILING = STUDIO_INFLUENCE_CEILING  # same cap as an actor — better odds, not a higher roof


def director_influence_on_studio_decision(trust: float, director_importance: float) -> float:
    """The director-side version of actor_influence_on_studio_decision() — same convex shape, a
    higher floor and gentler power so a director's own say on their own film climbs faster through
    ordinary Standing levels, but never a higher ceiling than an actor's own best case."""
    importance_term = DIRECTOR_INFLUENCE_IMPORTANCE_COEF * (max(director_importance, 0.0) / 100.0) ** DIRECTOR_INFLUENCE_IMPORTANCE_POWER
    trust_multiplier = 1.0 + DIRECTOR_INFLUENCE_TRUST_SWING * (trust - 50.0) / 50.0
    influence = DIRECTOR_INFLUENCE_BASE + importance_term * trust_multiplier
    return clamp(influence, DIRECTOR_INFLUENCE_FLOOR, DIRECTOR_INFLUENCE_CEILING)


def decide_release_strategy(
    studio: Studio, requested_strategy: str, trust: float, actor_importance: float, rng: random.Random,
    influence_fn=actor_influence_on_release,
) -> str:
    """The studio's actual call — requested_strategy only wins with probability influence_fn()
    (actor_influence_on_release by default; pass director_influence_on_studio_decision for a
    director's own request); otherwise the studio releases the film its own way."""
    influence = influence_fn(trust, actor_importance)
    return requested_strategy if rng.random() < influence else studio.preferred_release


def marketing_share_for(studio: Studio, budget_millions: float) -> float:
    if studio.tiered_marketing:
        return _tentpole_marketing_share(budget_millions)
    return studio.marketing_share


# The marketing decision is deliberately NOT a function of the film's actual resolved quality —
# no studio executive gets to peek at the finished film's real critic/audience score before
# setting the campaign budget; that decision gets made off what's actually knowable beforehand
# (the studio's own instincts, the relationship, the star, the genre's mood) plus real, irreducible
# uncertainty. That's the point: a big campaign can still get thrown at a film that flops, and a
# real sleeper can still go out under-marketed — nobody in this model can reliably predict which.
MARKETING_TRUST_COEF = 0.06          # (trust-50)/100 -> +/-0.06 around baseline
MARKETING_STARPOWER_COEF = 0.08      # (star_power-50)/100 -> +/-0.08 — a known lead is easier to sell
MARKETING_GENRE_DEMAND_COEF = 0.05   # (genre_demand-50)/100 -> +/-0.05 — ride the wave or don't fight it
MARKETING_FRANCHISE_DISCOUNT = -0.04  # built-in awareness needs less spend to reach the same audience
MARKETING_PUSH_BONUS = 0.12          # extra share if a requested campaign push is actually honored
MARKETING_NOISE_SD = 0.16            # the dominant term on purpose — real, irreducible unpredictability
MARKETING_SHARE_FLOOR = 0.05
MARKETING_SHARE_CEILING = 0.95


@dataclass(frozen=True)
class MarketingDecision:
    marketing_share: float
    push_requested: bool
    push_honored: bool


def decide_marketing_spend(
    studio: Studio,
    film_budget_millions: float,
    trust: float,
    actor_star_power: float,
    genre_demand: float,
    is_franchise_or_adaptation: bool,
    requested_push: bool,
    rng: random.Random,
    influence_fn=actor_influence_on_studio_decision,
) -> MarketingDecision:
    """How much of this film's real budget the studio actually spends marketing it — reactive to
    everything actually knowable at that point (trust, the actor's own pull, the genre's mood,
    whether the built-in-awareness discount applies, and whether a lobbied-for push landed), but
    dominated by real noise (MARKETING_NOISE_SD) rather than the film's own quality, which nobody
    — including the studio — has a reliable read on yet. influence_fn: which "how much does the
    studio listen to this push" curve to use — pass director_influence_on_studio_decision for a
    director's own request."""
    baseline = marketing_share_for(studio, film_budget_millions)
    trust_component = MARKETING_TRUST_COEF * (trust - 50.0) / 100.0
    star_component = MARKETING_STARPOWER_COEF * (actor_star_power - 50.0) / 100.0
    genre_component = MARKETING_GENRE_DEMAND_COEF * (genre_demand - 50.0) / 100.0
    franchise_component = MARKETING_FRANCHISE_DISCOUNT if is_franchise_or_adaptation else 0.0
    noise = rng.gauss(0.0, MARKETING_NOISE_SD)

    push_honored = False
    push_component = 0.0
    if requested_push:
        influence = influence_fn(trust, actor_star_power)
        push_honored = rng.random() < influence
        push_component = MARKETING_PUSH_BONUS if push_honored else 0.0

    share = baseline + trust_component + star_component + genre_component + franchise_component + noise + push_component
    return MarketingDecision(
        marketing_share=clamp(share, MARKETING_SHARE_FLOOR, MARKETING_SHARE_CEILING),
        push_requested=requested_push,
        push_honored=push_honored,
    )


# The studio's rating tolerance isn't just its own identity — a real tentpole budget pulls the
# ceiling down regardless of who's financing it (four-quadrant economics beats studio personality),
# and an open franchise/adaptation tightens it by one more step (real brand stakes, the same
# built-in-awareness idea MARKETING_FRANCHISE_DISCOUNT already prices in from the spend side).
RATING_TENTPOLE_BUDGET_THRESHOLD = 100.0  # $M — same tier break _tentpole_marketing_share uses
RATING_FRANCHISE_CEILING_TIGHTEN = 1  # steps down RATING_BAND_ORDER


def effective_rating_ceiling(studio: Studio, film_budget_millions: float, is_franchise_or_adaptation: bool) -> str:
    idx = RATING_BAND_ORDER.index(studio.rating_ceiling)
    if film_budget_millions >= RATING_TENTPOLE_BUDGET_THRESHOLD:
        idx = min(idx, RATING_BAND_ORDER.index("PG-13"))
    if is_franchise_or_adaptation:
        idx = max(idx - RATING_FRANCHISE_CEILING_TIGHTEN, 0)
    return RATING_BAND_ORDER[idx]


@dataclass(frozen=True)
class RatingCutDecision:
    actual_stance: str  # rating.RATING_CUT or rating.RATING_RELEASE_AS_SHOT — what actually happens
    studio_wanted_cut: bool  # did the studio's own ceiling get exceeded at all
    forced: bool  # the studio's preference overrode the requested stance
    requested_stance: str  # what was asked for, unchanged, for the caller to report against


def decide_rating_cut(
    studio: Studio,
    score: float,
    film_budget_millions: float,
    is_franchise_or_adaptation: bool,
    requested_stance: str,
    trust: float,
    importance: float,
    rng: random.Random,
    influence_fn=actor_influence_on_studio_decision,
) -> RatingCutDecision:
    """The studio's real pressure on a borderline film's rating — the mirror image of
    decide_release_strategy(): there, the actor/director requests and the studio grants with
    probability influence_fn(); here, the studio has the preference (a cut, once its own effective_
    rating_ceiling is exceeded) and influence_fn() is the probability the creative side's own
    requested_stance holds anyway. A top-tier star or director can refuse a cut and make it stick;
    someone with real influence over neither the studio nor the industry gets overruled outright —
    same curve, same trust-swing, same floor/ceiling actor_influence_on_studio_decision() already
    uses for every other studio negotiation in this engine, not a second formula.

    Only meaningful for a film already sitting near a band boundary (rating.near_boundary(score)) —
    the caller enforces that gate; a studio comfortably inside its own ceiling has no preference at
    all, and requested_stance is simply honored."""
    ceiling = effective_rating_ceiling(studio, film_budget_millions, is_franchise_or_adaptation)
    wants_cut = RATING_BAND_ORDER.index(ceiling) < RATING_BAND_ORDER.index(rating_band(score))
    if not wants_cut:
        return RatingCutDecision(requested_stance, studio_wanted_cut=False, forced=False, requested_stance=requested_stance)

    influence = influence_fn(trust, importance)
    creative_side_holds = rng.random() < influence
    if creative_side_holds:
        return RatingCutDecision(requested_stance, studio_wanted_cut=True, forced=False, requested_stance=requested_stance)
    return RatingCutDecision(RATING_CUT, studio_wanted_cut=True, forced=True, requested_stance=requested_stance)


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

# simulation._franchises.studio_protectiveness's pull on this same bid floor — a financing studio
# protecting a proven property doesn't shop it around to competitors as readily; only a genuinely
# enthusiastic outside buyer clears the raised bar, so a strong franchise draws a thinner outside
# pool and leans harder toward the financing studio's own (self-distribute or otherwise) terms.
# Default 0.0 leaves every existing call site's behavior exactly unchanged.
PROTECTIVENESS_BID_FLOOR_COEF = 0.5


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
    franchise_protectiveness: float = 0.0,
) -> list[StreamingBid]:
    """The real streaming offers — resolved once the film is actually finished and its quality is
    known, not a budget-only preview. A great film draws more bidders at better terms; an awful one
    draws few or none, since each outside buyer's read on it varies (QUALITY_PERCEPTION_SPREAD)
    instead of everyone agreeing on the same verdict. The financing studio's own offer (its normal
    terms, plus the always-available SELF_DISTRIBUTE_MULTIPLIER "for nothing" option) is unaffected
    by quality — they already own the film either way.

    franchise_protectiveness: simulation._franchises.studio_protectiveness(), 0-100 — 0.0 (the
    default, any standalone film) leaves the bid floor exactly where it's always been."""
    financing = STUDIOS[financing_studio_id]
    quality = (film_critic_score + audience_score) / 2.0
    pool = [s for s in STUDIOS.values() if _can_credibly_bid(s, budget_millions) and s is not financing]
    bid_floor = QUALITY_BID_FLOOR + PROTECTIVENESS_BID_FLOOR_COEF * franchise_protectiveness

    bids: list[StreamingBid] = []
    for studio in pool:
        perceived = clamp(rng.gauss(quality, QUALITY_PERCEPTION_SPREAD), 0.0, 100.0)
        if perceived < bid_floor:
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


@dataclass(frozen=True)
class FestivalBid:
    studio_id: str
    studio_name: str
    multiplier: float
    payout_millions: float
    self_release: bool  # True: the financing side keeps the film and releases it themselves, at
    # the real, quality-dependent LIMITED-release numbers — not a flat guarantee like every other
    # bid here. release.py fills this bid in (see resolve_release_schedule's festival_sale_resolver
    # in simulation/career.py), since this module never touches a resolved ReceptionResult.


def festival_bidders(budget_millions: float, financing_studio_id: str | None) -> list[Studio]:
    """The pre-sale, budget-only candidate pool for a festival acquisition — same shape and same
    _can_credibly_bid() gate as streaming_bidders() (buying distribution rights to a finished film
    is a smaller commitment than financing production, so the pool is wider than pick_studio's own
    financing range). financing_studio_id may be None for a genuinely independent, never-studio-
    attached self-financed project (director.development.DevProject.financing_studio_id) — the
    financing side's own guaranteed offer only appears when a real studio identity exists."""
    bidders = [s for s in STUDIOS.values() if _can_credibly_bid(s, budget_millions)]
    financing = STUDIOS.get(financing_studio_id) if financing_studio_id else None
    if financing is not None and financing not in bidders:
        bidders = [financing, *bidders]
    return bidders


def quality_adjusted_festival_bids(
    budget_millions: float,
    financing_studio_id: str | None,
    film_critic_score: float,
    audience_score: float,
    rng: random.Random,
    franchise_protectiveness: float = 0.0,
) -> list[FestivalBid]:
    """The real acquisition offers — resolved once the film has actually premiered and its quality
    is known (§10.3's own "all reviews land at once" reveal), same quality-perception/bid-floor
    mechanism quality_adjusted_bids() already uses for streaming, read against a different (lower,
    theatrical-guarantee-shaped) base multiplier. Every bid here is a competing DISTRIBUTOR's flat
    guarantee; the financing side's own option to keep the film and self-release it instead (a real,
    quality-dependent LIMITED release, not a flat number) is added by the caller (simulation.career.
    resolve_release_schedule's festival_sale_resolver), which has the actual reception this module
    never sees.

    financing_studio_id may be None for a genuinely independent, never-studio-attached self-financed
    project — no financing-side guaranteed offer is added in that case, only outside bids.

    franchise_protectiveness: simulation._franchises.studio_protectiveness() — same bid-floor pull
    quality_adjusted_bids() already documents. 0.0 for any standalone film."""
    quality = (film_critic_score + audience_score) / 2.0
    financing = STUDIOS.get(financing_studio_id) if financing_studio_id else None
    pool = [s for s in STUDIOS.values() if _can_credibly_bid(s, budget_millions) and s is not financing]
    bid_floor = QUALITY_BID_FLOOR + PROTECTIVENESS_BID_FLOOR_COEF * franchise_protectiveness

    bids: list[FestivalBid] = []
    for studio in pool:
        perceived = clamp(rng.gauss(quality, QUALITY_PERCEPTION_SPREAD), 0.0, 100.0)
        if perceived < bid_floor:
            continue  # this buyer passes on it entirely
        multiplier = (FESTIVAL_ACQUISITION_BASE_MULTIPLIER + studio.festival_acquisition_multiplier_delta) * _quality_multiplier(perceived)
        bids.append(FestivalBid(
            studio.id, studio.name, round(multiplier, 2), round(budget_millions * multiplier, 2), False,
        ))

    if financing is not None:
        financing_multiplier = FESTIVAL_ACQUISITION_BASE_MULTIPLIER + financing.festival_acquisition_multiplier_delta
        bids.append(FestivalBid(
            financing.id, financing.name, round(financing_multiplier, 2),
            round(budget_millions * financing_multiplier, 2), False,
        ))
    return bids
