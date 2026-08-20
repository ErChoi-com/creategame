"""design/part-04-the-actor.md §4.11 — BuzzScore, narrative bonuses, category strategy, vote
splitting, campaign cost. "Awards do not reward being good; they reward being seen to be good" —
BuzzScore reads YourSpotlight, not the hidden Performance number.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.core.util import clamp

BUZZ_SPOTLIGHT_WEIGHT = 0.34
BUZZ_CRITIC_WEIGHT = 0.20
BUZZ_CAMPAIGN_WEIGHT = 0.14
BUZZ_PRESTIGE_WEIGHT = 0.12
BUZZ_NARRATIVE_WEIGHT = 0.10
BUZZ_CATEGORY_WEIGHT = 0.10
BUZZ_NOISE_SD = 9.0

CAMPAIGN_COST_LO = 0.4  # $M
CAMPAIGN_COST_HI = 3.0

CATEGORY_ADVANTAGE_LEAD_IN_SUPPORTING = 18.0
CATEGORY_FRAUD_CAUGHT_CHANCE = 0.35
CATEGORY_FRAUD_NOTORIETY = 6.0

VOTE_SPLITTING_PENALTY = -9.0

NARRATIVE_BONUSES = {
    "shes_due": 14.0,
    "transformation": 12.0,
    "comeback": 11.0,
    "final_bow": 10.0,
    "newcomer": 8.0,
    "posthumous": 20.0,
    "too_commercial": -10.0,
    "overexposed": -7.0,
}


@dataclass(frozen=True)
class NarrativeContext:
    prior_nominations: int = 0
    prior_wins: int = 0
    transformation_flag: bool = False
    heat_years_below_25: int = 0
    age: int = 30
    announced_retirement: bool = False
    is_first_nomination: bool = False
    posthumous: bool = False
    tentpoles_last_3_years: int = 0
    credits_this_season: int = 1


def narrative_bonus(ctx: NarrativeContext) -> float:
    """Multiple flags can be true at once; design/ presents them as a lookup table, not a stack —
    this pass's reading takes the single largest-magnitude applicable bonus (a career doesn't get
    both "the comeback" and "the final bow" bonus stacked in the same season)."""
    applicable = []
    if ctx.posthumous:
        applicable.append(NARRATIVE_BONUSES["posthumous"])
    if ctx.prior_nominations >= 3 and ctx.prior_wins == 0:
        applicable.append(NARRATIVE_BONUSES["shes_due"])
    if ctx.transformation_flag:
        applicable.append(NARRATIVE_BONUSES["transformation"])
    if ctx.heat_years_below_25 >= 4:
        applicable.append(NARRATIVE_BONUSES["comeback"])
    if ctx.age >= 70 or ctx.announced_retirement:
        applicable.append(NARRATIVE_BONUSES["final_bow"])
    if ctx.is_first_nomination and ctx.age < 28:
        applicable.append(NARRATIVE_BONUSES["newcomer"])
    if ctx.tentpoles_last_3_years >= 2:
        applicable.append(NARRATIVE_BONUSES["too_commercial"])
    if ctx.credits_this_season >= 4:
        applicable.append(NARRATIVE_BONUSES["overexposed"])
    if not applicable:
        return 0.0
    return max(applicable, key=abs)


def category_fraud(rng: random.Random) -> tuple[float, bool, float]:
    """Lead-in-supporting campaign strategy. Returns (category_advantage, caught, notoriety_delta)."""
    caught = rng.random() < CATEGORY_FRAUD_CAUGHT_CHANCE
    notoriety_delta = CATEGORY_FRAUD_NOTORIETY if caught else 0.0
    return CATEGORY_ADVANTAGE_LEAD_IN_SUPPORTING, caught, notoriety_delta


def buzz_score(
    your_spotlight: float,
    film_critic_score: float,
    campaign_spend: float,
    prestige: float,
    narrative_bonus_value: float,
    category_advantage: float,
    rng: random.Random,
) -> float:
    return clamp(
        BUZZ_SPOTLIGHT_WEIGHT * your_spotlight
        + BUZZ_CRITIC_WEIGHT * film_critic_score
        + BUZZ_CAMPAIGN_WEIGHT * campaign_spend
        + BUZZ_PRESTIGE_WEIGHT * prestige
        + BUZZ_NARRATIVE_WEIGHT * narrative_bonus_value
        + BUZZ_CATEGORY_WEIGHT * category_advantage
        + rng.gauss(0.0, BUZZ_NOISE_SD),
        0.0, 100.0,
    )


def apply_vote_splitting(buzz_scores: dict[str, float], same_film_candidate_ids: list[str]) -> dict[str, float]:
    if len(same_film_candidate_ids) < 2:
        return buzz_scores
    updated = dict(buzz_scores)
    for cid in same_film_candidate_ids:
        if cid in updated:
            updated[cid] = clamp(updated[cid] + VOTE_SPLITTING_PENALTY, 0.0, 100.0)
    return updated


def resolve_category(buzz_scores: dict[str, str | float], rng: random.Random) -> str:
    """buzz_scores: candidate_id -> BuzzScore. Highest wins; ties broken by rng, since a real
    vote tally isn't modeled at that resolution."""
    best = max(buzz_scores.values())
    winners = [cid for cid, score in buzz_scores.items() if score == best]
    return rng.choice(winners)


# design/part-09 §9.1's own genre award-ceiling column, wired in for the first time — previously
# stated in design/ but never read by this module. Five tiers instead of the doc's six ("Separate
# category" is animation's own is_animation gate, handled by the caller, not a ceiling tier here).
AWARD_CEILING_TIERS = ("very_low", "low", "medium", "high", "highest")
AWARD_CEILING_CAP = {"very_low": 40.0, "low": 55.0, "medium": 72.0, "high": 86.0, "highest": 100.0}

# §9.1's table plus this pass's own reading for the five genres added since that table was
# written (fantasy/crime/superhero/war/western — actor/palette.py's v19 roster): fantasy and
# crime read like their nearest §9.1 cousins (sci-fi, thriller) at medium; superhero reads like
# action turned up, same low ceiling; war matches §9.1's own explicit "period/war: high" entry;
# western is a genuine prestige lane in its own right (a long real-world Oscar history) but not
# drama's tier, so medium-high rounds to "high" alongside musical/period.
GENRE_AWARD_CEILING = {
    "horror": "very_low", "comedy": "low", "drama": "highest", "action": "low",
    "thriller": "medium", "scifi": "medium", "romance": "low", "musical": "high",
    "period": "high", "family": "low", "fantasy": "medium", "crime": "medium",
    "superhero": "low", "war": "high", "western": "high",
}

# design/part-09 (creative-revamp-plan.md) §14.3 — role depth is a SECOND gate alongside genre,
# not a replacement for it: a showcase role in a low-ceiling genre is still a real nomination
# shot; an underwritten role in a high-ceiling genre still isn't. underwritten hard-caps well
# below even "very_low"'s own genre floor — a role that thin was never a contender regardless of
# what film it's in.
ROLE_DEPTH_AWARD_CEILING_CAP = {"underwritten": 35.0, "standard": 70.0, "rich": 88.0, "showcase": 100.0}


# ---- distinct award categories, researched against how real ceremonies actually differ from one
# another rather than invented from scratch:
#   - the Academy splits Lead/Supporting by billing only (no genre split)
#   - the Golden Globes splits LEAD (only) into Drama vs. Musical/Comedy, leaving Supporting
#     genre-blind
#   - SAG's signature category judges the whole cast as an Ensemble rather than any one
#     performance
#   - Gotham/Spirit/Critics-Choice-style bodies run a separate, genuinely easier Breakthrough
#     lane for new talent
#   - the Saturn Awards (Academy of Science Fiction, Fantasy & Horror Films) exist specifically
#     because "the Academy and Golden Globe Awards... gave little recognition to acting quality"
#     in genre film — a real, second circuit for horror/sci-fi/fantasy/superhero/action, not a
#     lesser version of the prestige one
#   - the Annie Awards separately reward Voice Acting in an animated feature — its own circuit,
#     not folded into whatever live-action genre the story happens to be
# Eight categories total, each reading a genuinely different real input already tracked by this
# engine — not the same BuzzScore formula eight times with new labels.
LEAD_DRAMA = "lead_drama"
LEAD_COMEDY = "lead_comedy"
SUPPORTING = "supporting"
ENSEMBLE = "ensemble"
BREAKTHROUGH = "breakthrough"
GENRE_EXCELLENCE = "genre_excellence"
VOICE_PERFORMANCE = "voice_performance"
DIRECTOR = "director"
AWARD_CATEGORIES = (
    LEAD_DRAMA, LEAD_COMEDY, SUPPORTING, ENSEMBLE, BREAKTHROUGH,
    GENRE_EXCELLENCE, VOICE_PERFORMANCE, DIRECTOR,
)

# The Globes' own split — Lead only, never Supporting. Reusing GENRES' own comedy/musical tags
# (actor/palette.py) rather than a new, separate genre-flavor list.
COMEDY_MUSICAL_GENRES = frozenset({"comedy", "musical"})

# The Saturn Awards' own real, historical scope: sci-fi, fantasy, and horror from the start, with
# superhero/action folded in as the ceremony itself expanded to cover "action-adventure" genre
# film. Deliberately NOT every low-ceiling genre (romance/family stay in the prestige circuit
# alone — there's no real second circuit for them) — this maps onto the one that actually exists.
GENRE_EXCELLENCE_GENRES = frozenset({"horror", "scifi", "fantasy", "superhero", "action"})

# Genre Excellence and Voice Performance are their OWN circuits, not the prestige one — a horror
# or animated performance isn't competing to clear drama's own ceiling here, it's competing on
# its own circuit's terms, the entire real-world reason these ceremonies exist. Flat "high" cap
# (not "highest" — this is still a second circuit, not a prestige-circuit replacement), role
# depth still gates it: a genuinely thin genre role isn't a real contender just because the
# genre-ceiling penalty is bypassed.
GENRE_EXCELLENCE_CEILING = AWARD_CEILING_CAP["high"]
VOICE_PERFORMANCE_CEILING = AWARD_CEILING_CAP["high"]

# §9.1's table plus this pass's own reading for the five genres added since that table was
# written (fantasy/crime/superhero/war/western — actor/palette.py's v19 roster): fantasy and
# crime read like their nearest §9.1 cousins (sci-fi, thriller) at medium; superhero reads like
# action turned up, same low ceiling; war matches §9.1's own explicit "period/war: high" entry;
# western is a genuine prestige lane in its own right (a long real-world Oscar history) but not
# drama's tier, so medium-high rounds to "high" alongside musical/period. This table is the
# PRESTIGE circuit's own ceiling — Genre Excellence/Voice Performance bypass it entirely (above).
GENRE_AWARD_CEILING = {
    "horror": "very_low", "comedy": "low", "drama": "highest", "action": "low",
    "thriller": "medium", "scifi": "medium", "romance": "low", "musical": "high",
    "period": "high", "family": "low", "fantasy": "medium", "crime": "medium",
    "superhero": "low", "war": "high", "western": "high",
}

# design/part-09 (creative-revamp-plan.md) §14.3 — role depth is a SECOND gate alongside genre,
# not a replacement for it: a showcase role in a low-ceiling genre is still a real nomination
# shot; an underwritten role in a high-ceiling genre still isn't. underwritten hard-caps well
# below even "very_low"'s own genre floor — a role that thin was never a contender regardless of
# what film it's in.
ROLE_DEPTH_AWARD_CEILING_CAP = {"underwritten": 35.0, "standard": 70.0, "rich": 88.0, "showcase": 100.0}


def award_ceiling(genre: str, role_depth: str, category: str | None = None) -> float:
    """The real cap on a campaign's BuzzScore — genre (or, for Genre Excellence/Voice
    Performance, that circuit's own flat cap) and role depth are two independent gates, and the
    tighter one wins, same as any other min-of-two-caps shape in this engine."""
    if category in (GENRE_EXCELLENCE, VOICE_PERFORMANCE):
        genre_cap = GENRE_EXCELLENCE_CEILING if category == GENRE_EXCELLENCE else VOICE_PERFORMANCE_CEILING
    else:
        genre_cap = AWARD_CEILING_CAP[GENRE_AWARD_CEILING.get(genre, "medium")]
    depth_cap = ROLE_DEPTH_AWARD_CEILING_CAP.get(role_depth, ROLE_DEPTH_AWARD_CEILING_CAP["standard"])
    return min(genre_cap, depth_cap)


def apply_award_ceiling(buzz: float, genre: str, role_depth: str, category: str | None = None) -> float:
    return min(buzz, award_ceiling(genre, role_depth, category))


# §4.4's own "she's due"/"newcomer" threshold reused here for what counts as early-career, so
# Breakthrough eligibility and the newcomer narrative bonus agree on the same number rather than
# drifting apart as two separately-tuned constants.
BREAKTHROUGH_CREDITS_MAX = 3


def eligible_performance_categories(genre: str, billing: str, credits: int, is_animation: bool = False) -> tuple[str, ...]:
    """The real, honest lane(s) a completed role can campaign in — Ensemble is always available
    (it's a judgment on the film, not on billing), Breakthrough only for an early-career actor,
    Genre Excellence/Voice Performance are a genuine second circuit a role can ALSO campaign in
    alongside its prestige-circuit lane (not instead of it — a horror lead is a real, if
    long-shot, Lead-Drama contender AND a real Genre Excellence contender, same as an actual
    Saturn-nominated performance can also chase an Oscar nod), and exactly one of Lead-Drama/
    Lead-Comedy/Supporting off billing+genre. category_fraud (above)
    is what lets a player campaign a lead performance in Supporting anyway — a deliberate departure
    from this honest list, not a second eligibility rule."""
    categories = [ENSEMBLE]
    if billing == "lead":
        categories.append(LEAD_COMEDY if genre in COMEDY_MUSICAL_GENRES else LEAD_DRAMA)
    elif billing == "supporting":
        categories.append(SUPPORTING)
    if credits <= BREAKTHROUGH_CREDITS_MAX:
        categories.append(BREAKTHROUGH)
    if billing in ("lead", "supporting"):
        if is_animation:
            categories.append(VOICE_PERFORMANCE)
        elif genre in GENRE_EXCELLENCE_GENRES:
            categories.append(GENRE_EXCELLENCE)
    return tuple(categories)


# Ensemble reads the FILM, not the performance — SAG's real logic ("was this a great cast," not
# "were you personally the best in it"). A distinct weight table, not buzz_score reused with
# different arguments: film_critic_score and project_quality dominate, your own spotlight and
# campaign spend still matter but far less than in any individual category above.
ENSEMBLE_CRITIC_WEIGHT = 0.42
ENSEMBLE_QUALITY_WEIGHT = 0.28
ENSEMBLE_SPOTLIGHT_WEIGHT = 0.20
ENSEMBLE_CAMPAIGN_WEIGHT = 0.10


def ensemble_buzz_score(
    film_critic_score: float, project_quality: float, your_spotlight: float, campaign_spend: float, rng: random.Random,
) -> float:
    return clamp(
        ENSEMBLE_CRITIC_WEIGHT * film_critic_score
        + ENSEMBLE_QUALITY_WEIGHT * project_quality
        + ENSEMBLE_SPOTLIGHT_WEIGHT * your_spotlight
        + ENSEMBLE_CAMPAIGN_WEIGHT * campaign_spend
        + rng.gauss(0.0, BUZZ_NOISE_SD),
        0.0, 100.0,
    )


# Breakthrough's real mechanical difference from every other category: a smaller, genuinely
# weaker field, not a separate formula. The same buzz_score() a Lead campaign uses, just judged
# against first-timers instead of the whole industry.
BREAKTHROUGH_COMPETITOR_SPOTLIGHT_MEAN = 40.0
BREAKTHROUGH_COMPETITOR_SPOTLIGHT_SD = 12.0
BREAKTHROUGH_COMPETITOR_CRITIC_MEAN = 45.0
BREAKTHROUGH_COMPETITOR_CRITIC_SD = 10.0

# Standard-field competitor sampling (Lead/Supporting/Director) — the same distribution
# simulation/session.py's own run_awards_campaign has always sampled rivals from, named here so
# Breakthrough's own weaker field reads as a deliberate, visible contrast rather than a magic
# number duplicated in two places.
FIELD_COMPETITOR_SPOTLIGHT_MEAN = 55.0
FIELD_COMPETITOR_SPOTLIGHT_SD = 15.0
FIELD_COMPETITOR_CRITIC_MEAN = 55.0
FIELD_COMPETITOR_CRITIC_SD = 10.0

# §the request this pass answers directly: "winning gives some small amount of benefit, nothing
# too significant." Every win moves exactly one existing Standing meter (StandingModel.add — the
# same mechanism category-fraud's own notoriety penalty already uses), by a small, capped amount.
# Which meter differs by category on purpose: Lead/Supporting/Director are a personal statement
# (Prestige); Ensemble is industry goodwill from being part of something loved (Affection), not a
# personal one; Breakthrough is fresh momentum, not prestige a first-timer hasn't earned yet (Heat).
AWARD_WIN_PRESTIGE_BONUS = 3.0
AWARD_WIN_SUPPORTING_PRESTIGE_BONUS = 2.0  # a real, smaller win — Supporting's own lesser weight
AWARD_WIN_ENSEMBLE_AFFECTION_BONUS = 3.0
AWARD_WIN_BREAKTHROUGH_HEAT_BONUS = 4.0
# A real, respected win within its own circle — genuinely smaller than the prestige circuit's own
# Lead win, the same honest "second circuit, not a lesser copy of the first one" distinction the
# Saturn/Annie Awards actually carry in real awards culture.
AWARD_WIN_GENRE_CIRCUIT_BONUS = 2.5

AWARD_WIN_METER = {
    LEAD_DRAMA: "prestige", LEAD_COMEDY: "prestige", DIRECTOR: "prestige",
    SUPPORTING: "prestige", ENSEMBLE: "affection", BREAKTHROUGH: "heat",
    GENRE_EXCELLENCE: "prestige", VOICE_PERFORMANCE: "prestige",
}
AWARD_WIN_BONUS = {
    LEAD_DRAMA: AWARD_WIN_PRESTIGE_BONUS, LEAD_COMEDY: AWARD_WIN_PRESTIGE_BONUS,
    DIRECTOR: AWARD_WIN_PRESTIGE_BONUS, SUPPORTING: AWARD_WIN_SUPPORTING_PRESTIGE_BONUS,
    ENSEMBLE: AWARD_WIN_ENSEMBLE_AFFECTION_BONUS, BREAKTHROUGH: AWARD_WIN_BREAKTHROUGH_HEAT_BONUS,
    GENRE_EXCELLENCE: AWARD_WIN_GENRE_CIRCUIT_BONUS, VOICE_PERFORMANCE: AWARD_WIN_GENRE_CIRCUIT_BONUS,
}


def award_win_bonus(category: str) -> tuple[str, float]:
    """Returns (meter_name, delta) — the caller applies it via StandingModel.add(), same as every
    other small Standing nudge in this engine. One small, one-time, capped bonus per win; nothing
    compounding, nothing that reshapes a career on its own."""
    return AWARD_WIN_METER[category], AWARD_WIN_BONUS[category]
