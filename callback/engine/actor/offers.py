"""design/part-04-the-actor.md §4.4 — the Offer Board & casting.

FitScore, Utility, offer probability, and casting-path resolution. RelationshipBonus is stubbed
at 0 (the Rolodex, §4.12, isn't modeled in this pass) but takes the real inputs already, so wiring
in the Rolodex later is additive, not a rewrite.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.persona import ARCHETYPES, GENRES, ROLE_DEPTHS, Persona
from callback.engine.actor.series import MAX_EPISODES, MIN_EPISODES, sample_episode_count
from callback.engine.actor.standing import GATEKEEPER_WEIGHTS
from callback.engine.actor.studios import pick_studio
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp, positive_part, sigmoid

# Utility formula weights (§4.4).
UTILITY_STANDING_WEIGHT = 0.40
UTILITY_FIT_WEIGHT = 0.35
UTILITY_ATTR_WEIGHT = 0.15
UTILITY_ATTR_CRAFT_SHARE = 0.6
UTILITY_ATTR_INSTINCT_SHARE = 0.4
UTILITY_OVERPRICE_COEF = 12.0

# ageMismatchPenalty constants.
AGE_MISMATCH_FREE_BAND = 4
AGE_MISMATCH_COEF = 2.2
AGE_MISMATCH_EXPONENT = 1.35
AGE_MISMATCH_CAP = 70.0
AGE_MISMATCH_YOUNGER_MULT = 1.6  # playing younger costs 1.6x more than playing older

# Animation — voice work, not a genre. The audience never sees who's speaking, so the two real
# levers a physical performance always carries (does your face match the character's age, does
# your face match the part at all) mostly stop applying — real, but heavily reduced rather than
# zeroed: some animated child roles are still genuinely cast to a similarly-aged voice, and a
# prestige production sometimes wants an age-authentic read anyway. ANIMATION_AGE_MISMATCH_MULT
# scales age_mismatch_penalty down to a fraction of its live-action bite for an animated role.
ANIMATION_AGE_MISMATCH_MULT = 0.15

# aging.role_volume_multiplier's own three lanes, read off fields this module already has —
# archetype (persona.ARCHETYPES) and billing. Any archetype outside these three groups (everyman,
# villain, comic_relief, mentor, narrator, ensemble) isn't covered by §4.9's own dot-density table
# and isn't gated by it here either — the table only ever named three lanes, not a blanket age
# curve on every part.
ROLE_VOLUME_LANES = {
    "ingenue": "ingenue_romantic", "romantic_lead": "ingenue_romantic",
    "authority": "character_authority",
    "leading_hero": "lead_overall",
}

# FitScore's genre/archetype terms.
TYPECASTING_PENALTY_COEF = 0.45

# P(offer) sigmoid slope.
OFFER_PROBABILITY_SLOPE = 0.11

# v9 fix (design/part-04 §4.4): the open-offer path fires above this Utility-minus-difficulty
# margin. The original spec used 25, which made this path unreachable in practice.
OPEN_OFFER_UTILITY_MARGIN = 14.0

# §4.0's non-union opening act.
NON_UNION_CREDIT_THRESHOLD = 3
NON_UNION_SUBSTITUTION_CHANCE = 0.25
NON_UNION_PAY_FRACTION = 1.0 / 3.0

BILLINGS = ("lead", "supporting", "bit", "extra")

# What billing tier a role's fee can plausibly land in, as a share of the film's own budget — a
# lead genuinely competes for a real cut of the budget; a bit or extra part earns scale, not a
# meaningful fraction of it, regardless of how big the film is. No single number inside either
# band is "the" fee — see negotiated_fee_share() below for how the actual figure gets picked.
BILLING_FEE_SHARE = {
    "lead": (0.010, 0.30),
    "supporting": (0.003, 0.09),
    "bit": (0.0006, 0.020),
    "extra": (0.0001, 0.004),
}
FEE_NEGOTIATION_NOISE_SD = 0.18  # real negotiations don't land exactly where leverage alone predicts

# A film's total budget (§4.4's listing generator, this pass's reading — see sample_role's
# docstring): log-normal rather than a handful of fixed tiers, so nothing about the distribution
# a player sees is a hard-coded step function. Median lands near BUDGET_MEDIAN, and the tail can
# reach BUDGET_MAX (a real $300M tentpole) but only rarely — most films this samples are small.
BUDGET_MIN = 1.5
BUDGET_MAX = 300.0
BUDGET_MEDIAN = 12.0
BUDGET_LOGNORMAL_SIGMA = 1.15

# §4.4 v17 — the same (60, 14) reading simulation/career.py's resolve_quality has always sampled
# script_quality from; moved here so it's a real, persisted fact about the listing instead of a
# fresh roll no one (including the player) can see coming.
LATENT_QUALITY_MEAN = 60.0
LATENT_QUALITY_SD = 14.0

# §5.18 v9 — how often a fresh listing is a series instead of a film, and whether it's sold with a
# renewal on the table at all. Renewable stays a minority of series on purpose: most real pitches
# aren't sold as open-ended, and the locked-quote trap (§9.6) is a real, chosen risk, not the norm.
SERIES_CHANCE = 0.12
SERIES_RENEWABLE_CHANCE = 0.35

# How often a fresh listing is animation — independent of, and rolled separately from, whether
# it's a film or a series (either can be animated).
ANIMATION_CHANCE = 0.10

# design/part-09 §9.2 — how often a fresh listing carries a real secondary genre ("sci-fi
# horror"), rolled independently of everything else above. Rare on purpose: §9.2's own marketing
# penalty makes a hybrid a genuine minority pitch, not a routine one.
HYBRID_CHANCE = 0.12


def sample_budget_millions(rng: random.Random) -> float:
    return clamp(rng.lognormvariate(math.log(BUDGET_MEDIAN), BUDGET_LOGNORMAL_SIGMA), BUDGET_MIN, BUDGET_MAX)


# A role's own Difficulty used to be pure noise, entirely independent of the film's own budget —
# a $200M tentpole lead and a $2M indie lead drew from the exact same distribution, so nothing
# about a bigger production's own real stakes ever made it harder to land. Real studios protect
# their bigger investments: a tentpole-scale lead gets a genuinely tighter search, more scrutiny,
# more competition for the part than a scrappy indie one — the same log-scaled "bigger ask, taller
# bar" shape director.development.difficulty already uses for a director's own budget request, read
# from the casting side instead of the financing side. Calibrated so the old flat mean (50, at
# BUDGET_MEDIAN=$12M) is unchanged at a typical film's own scale — only the tails actually move.
ROLE_DIFFICULTY_BASE = 27.0
ROLE_DIFFICULTY_BUDGET_COEF = 20.5
ROLE_DIFFICULTY_NOISE_SD = 15.0


def role_difficulty(budget_millions: float, rng: random.Random) -> float:
    base = ROLE_DIFFICULTY_BASE + ROLE_DIFFICULTY_BUDGET_COEF * math.log10(max(budget_millions, 0.01) + 1.0)
    return clamp(base + rng.gauss(0.0, ROLE_DIFFICULTY_NOISE_SD), 5.0, 95.0)


# design/part-09 §14.2/§14.3 — role depth, independent of archetype and billing. Skewed toward
# "standard": most parts are just a job; a showcase is meant to be rare and worth noticing.
ROLE_DEPTH_WEIGHTS = {"underwritten": 0.20, "standard": 0.50, "rich": 0.22, "showcase": 0.08}

# §14.3's "showcase and mentor/narrator roles raise effective competition" — a real, small
# difficulty bump, not a hard gate. Additive with role_difficulty(), same units (0-100 scale).
ROLE_DEPTH_DIFFICULTY_BONUS = {"underwritten": -4.0, "standard": 0.0, "rich": 5.0, "showcase": 11.0}
DEPTH_SOUGHT_AFTER_ARCHETYPES = frozenset({"mentor", "narrator"})
ARCHETYPE_DIFFICULTY_BONUS = 6.0


def sample_role_depth(rng: random.Random) -> str:
    return rng.choices(ROLE_DEPTHS, weights=[ROLE_DEPTH_WEIGHTS[d] for d in ROLE_DEPTHS])[0]


def role_depth_difficulty_bonus(depth: str, archetype: str) -> float:
    return ROLE_DEPTH_DIFFICULTY_BONUS[depth] + (ARCHETYPE_DIFFICULTY_BONUS if archetype in DEPTH_SOUGHT_AFTER_ARCHETYPES else 0.0)


# Every accepted role used to cost the whole year's calendar (simulation.session.QUARTERS_PER_YEAR
# — 4, mirrored here as ROLE_QUARTERS_MAX rather than imported, since actor/ sits below simulation/
# in this package's one-way dependency order) regardless of scale — a quick animated voice gig and
# a real tentpole shoot both simply ate the whole year. Real productions don't: a small film wraps
# in a fraction of a year; animation is a real voice-work time commitment, not a physical shoot, and
# is flat-cheap in calendar terms regardless of budget; a big series order runs longer than a short
# one. Freed-up quarters aren't wasted — simulation.session.Session.actor_quarters_remaining_this_
# year() already gates Rolodex check-ins, agent-tier pushes, and Disappear; a quick role now
# genuinely leaves room for those in the same year, for free, off machinery that already existed.
ROLE_QUARTERS_MAX = 4
ROLE_QUARTERS_ANIMATION = 1  # flat, regardless of budget — a real, named simplification: this is
# the actor's OWN time commitment (voice sessions), not the production's real timeline, which for
# animation is often actually longer behind the scenes than live action's.

# Same log-budget shape as role_difficulty/director.development.difficulty, anchored so the median
# film (BUDGET_MEDIAN=$12M) costs about 2 quarters, a small indie ($1.5M) costs 1, and a real
# tentpole ($300M) costs the full 4.
ROLE_QUARTERS_FILM_BASE = 0.426
ROLE_QUARTERS_FILM_BUDGET_COEF = 1.441

# A series scales with its own real episode order (actor.series.MIN_EPISODES..MAX_EPISODES),
# linearly rather than log-scaled — episode count doesn't span the same multi-order-of-magnitude
# range budget does. A minimum-order season costs 1 quarter; a full 13-episode order costs 4.
ROLE_QUARTERS_SERIES_MIN = 1.0
ROLE_QUARTERS_SERIES_MAX = float(ROLE_QUARTERS_MAX)


def quarters_for_role(role: "Role") -> int:
    if role.is_animation:
        return ROLE_QUARTERS_ANIMATION
    if role.project_type == "series" and role.n_episodes:
        frac = clamp((role.n_episodes - MIN_EPISODES) / max(1, MAX_EPISODES - MIN_EPISODES), 0.0, 1.0)
        raw = ROLE_QUARTERS_SERIES_MIN + frac * (ROLE_QUARTERS_SERIES_MAX - ROLE_QUARTERS_SERIES_MIN)
        return int(round(clamp(raw, 1.0, ROLE_QUARTERS_MAX)))
    raw = ROLE_QUARTERS_FILM_BASE + ROLE_QUARTERS_FILM_BUDGET_COEF * math.log10(max(role.film_budget_millions, 0.01) + 1.0)
    return int(round(clamp(raw, 1.0, ROLE_QUARTERS_MAX)))


# Every accepted role used to cost the whole year's calendar (simulation.session.QUARTERS_PER_YEAR
# quarters), animation and tentpole alike — nothing about a role's own real scale changed how much
# of your year it actually consumed. Real productions don't work that way: a quick animation
# recording session and a year-long tentpole shoot cost wildly different amounts of an actor's own
# calendar. quarters_for_role reads only the role itself (never a director's own attributes — an
# acting role is always someone ELSE'S production from the actor's own point of view, so there's no
# honest Efficiency number to read the way there is on the director's own track).
ROLE_QUARTERS_MAX = 4  # matches simulation.session.QUARTERS_PER_YEAR — kept as a local literal
# rather than an import, since actor/ sits below simulation/ in this package's one-way dependency
# order and never imports back up into it.
ROLE_QUARTERS_ANIMATION = 1  # voice work is genuinely a much smaller time commitment than a
# physical shoot — this is about the actor's OWN calendar cost, not how long the finished film
# actually takes a studio to produce (animation pipelines often run long behind the scenes; that's
# a separate, unmodeled fact this doesn't contradict).
# Same log-budget shape role_difficulty/director.development.difficulty already use, calibrated so
# a small indie ($1.5M) costs 1 quarter and a real tentpole ($300M) costs the full year, with the
# median film (~$12M) landing around 2.
ROLE_QUARTERS_FILM_BASE = 0.426
ROLE_QUARTERS_FILM_BUDGET_COEF = 1.441


def quarters_for_role(role: "Role") -> int:
    if role.is_animation:
        return ROLE_QUARTERS_ANIMATION
    if role.project_type == "series" and role.n_episodes:
        frac = clamp((role.n_episodes - MIN_EPISODES) / max(1, MAX_EPISODES - MIN_EPISODES), 0.0, 1.0)
        return round(clamp(1.0 + frac * (ROLE_QUARTERS_MAX - 1), 1, ROLE_QUARTERS_MAX))
    base = ROLE_QUARTERS_FILM_BASE + ROLE_QUARTERS_FILM_BUDGET_COEF * math.log10(max(role.film_budget_millions, 0.01) + 1.0)
    return round(clamp(base, 1, ROLE_QUARTERS_MAX))


def negotiated_fee_share(billing: str, actor_leverage: float, rng: random.Random) -> float:
    """Where in this billing tier's own band (BILLING_FEE_SHARE) the fee actually lands — a real
    negotiation outcome, not a fixed point or a billing-blind roll. actor_leverage (0-1, typically
    the actor's own standing_score/100 — how big a name they currently are) pulls the outcome
    toward the top of the band; real noise on top means even a maximally leveraged negotiation
    doesn't land on the exact same number twice, and a total nobody can still occasionally get a
    surprisingly generous offer, or a big name a surprisingly stingy one."""
    lo, hi = BILLING_FEE_SHARE[billing]
    position = clamp(actor_leverage + rng.gauss(0.0, FEE_NEGOTIATION_NOISE_SD), 0.0, 1.0)
    return lo + (hi - lo) * position


@dataclass(frozen=True)
class Role:
    project_id: str
    genre: str
    archetype: str
    billing: str
    char_age: int
    type_strictness: float  # 0-1
    difficulty: float
    budget_for_role: float  # $M — the fee ceiling this role can pay
    gatekeeper: str  # key into standing.GATEKEEPER_WEIGHTS
    requirements: dict[str, float] = field(default_factory=dict)  # subset of voice/physicality/look
    union: bool = True
    studio: str = "mid_major"  # key into studios.STUDIOS — who's actually financing this film
    franchise_id: str | None = None  # set by simulation._franchises.maybe_attach_franchise
    installment_number: int = 0  # 0 = not a franchise entry; 1 = a new franchise; 2+ = a sequel
    source_material: str | None = None  # set by simulation._adaptations.maybe_attach_adaptation;
    # one of genre.adaptation.SOURCE_MATERIAL_TYPES, or None for an original screenplay
    source_material_popularity: str | None = None  # one of genre.adaptation.SOURCE_POPULARITY_TIERS,
    # set alongside source_material — how well-known the property is, scaling both the built-in
    # audience bonus and the fidelity-scrutiny risk. None whenever source_material is None.
    latent_quality: float = 60.0  # §4.4 v17 — the film's real, underlying script quality, sampled
    # once here rather than re-rolled blind at resolution (simulation/career.py's resolve_quality
    # now reads this directly). Never shown to the player as a raw number — offer_board() exposes
    # only a noisy, banded "buzz" read on it (see Session._buzz_band). Default 60.0 (this module's
    # own long-standing resolution mean) keeps any hand-built Role from earlier tests/verify.py
    # behaving exactly as before.
    director_npc_id: str | None = None  # a tracked Rolodex director attached to this listing, when
    # one plausibly would be (set by simulation/session.py at listing-generation time, which has
    # the real Rolodex to draw from — this module stays Rolodex-agnostic like the rest of actor/).
    # None most of the time — an unfamiliar director you have no real read on yet, same honest
    # uncertainty as any other stranger in the industry.
    film_budget_millions: float | None = None  # the WHOLE film's production budget — distinct from
    # budget_for_role (your own fee, a 5-35% slice of it). Drives reception/marketing/ROI/box-
    # office math and studio selection; budget_for_role drives only the Deal's fee negotiation and
    # quote comparisons. Defaults to budget_for_role in __post_init__ for any caller built before
    # this field existed (hand-built test Roles, etc.) — sample_role() is the only place that sets
    # a real, independently-sampled film budget.
    project_type: str = "film"  # "film" | "series" — design/part-05 §5.18. n_episodes/
    # series_renewable are independent settings on the same type, not two separate tiers to
    # maintain: the real difference between a bounded limited-series pitch and a returning show
    # isn't the episode count, it's whether renewal was ever on the table.
    n_episodes: int | None = None  # None for a film; a real episode count for a series
    series_renewable: bool = False  # only meaningful when project_type == "series" — whether this
    # was sold with a season 2 on the table at all. False (the common case) means the finale is a
    # real ending: no renewal roll, no locked-in future season.
    is_animation: bool = False  # orthogonal to project_type and genre, same as the film/series
    # split — an animated family comedy is genre="family", is_animation=True; nothing about the
    # project_type axis changes. Voice work, not a genre of its own.
    secondary_genre: str | None = None  # design/part-09 §9.2 — a real second genre tag (e.g.
    # genre="scifi", secondary_genre="horror" reads as "sci-fi horror"), not a separate subgenre
    # mechanic. None (the default) is a pure single-genre film with every number exactly as
    # before; set, it's resolved by genre.hybrids averaging the two parents' own already-existing
    # numbers — see simulation/career.resolve_quality and actor/reception.resolve_reception's
    # is_hybrid parameter.
    role_depth: str = "standard"  # design/part-09 §14.2 — one of persona.ROLE_DEPTHS, independent
    # of both archetype and billing. "standard" (the default) is every hand-built Role from before
    # this field existed; sample_role() is the only place that rolls a real distribution.

    def __post_init__(self) -> None:
        if self.film_budget_millions is None:
            object.__setattr__(self, "film_budget_millions", self.budget_for_role)


def age_mismatch_penalty(char_age: int, your_age: int, is_animation: bool = False) -> float:
    d = abs(char_age - your_age)
    if d <= AGE_MISMATCH_FREE_BAND:
        return 0.0
    penalty = AGE_MISMATCH_COEF * (d - AGE_MISMATCH_FREE_BAND) ** AGE_MISMATCH_EXPONENT
    if char_age < your_age:  # playing younger
        penalty *= AGE_MISMATCH_YOUNGER_MULT
    penalty = min(penalty, AGE_MISMATCH_CAP)
    return penalty * ANIMATION_AGE_MISMATCH_MULT if is_animation else penalty


def lane_for_role(role: "Role") -> str | None:
    """Which of aging.role_volume_multiplier's three named lanes this role falls into, if any —
    None for anything §4.9's own dot-density table doesn't cover."""
    if role.billing == "lead" or role.archetype == "leading_hero":
        return "lead_overall"
    return ROLE_VOLUME_LANES.get(role.archetype)


def hard_gate_penalty(attrs: Attributes, requirements: dict[str, float]) -> float:
    """§4.4 names this term without a formula; shortfall-below-requirement, uncapped positive
    part, is this pass's documented reading — a role with no stated requirement costs nothing."""
    return sum(max(0.0, req - getattr(attrs, gate)) for gate, req in requirements.items())


def typecasting_penalty(persona: Persona, role: Role) -> float:
    """The raw, actor-only reading — how much of a stretch this role is against your own Persona,
    independent of who's asking. fit_score below applies gatekeeper_legibility_multiplier on top
    of this for the actual Fit number; is_breaking_type reads this raw value instead, since whether
    something is genuinely a type-break is about who you are, not which studio is casting."""
    genre_pen = TYPECASTING_PENALTY_COEF * (100.0 - persona.genre_affinity.get(role.genre, 20.0)) * role.type_strictness
    archetype_pen = TYPECASTING_PENALTY_COEF * (100.0 - persona.archetype_affinity.get(role.archetype, 20.0)) * role.type_strictness
    return genre_pen + archetype_pen


# Different gatekeepers don't read Legibility the same way — a studio tentpole wants a known,
# reliable quantity (real box-office predictability), a prestige auteur wants range (a legible
# "type" reads as less interesting casting, not more castable). Rather than a second hand-tuned
# table, this derives straight from standing.GATEKEEPER_WEIGHTS' own existing prestige-vs-heat
# split, already used for exactly this same character trait elsewhere — a gatekeeper that weights
# Prestige heavily amplifies the typecasting penalty; one that weights Heat heavily forgives it.
# Scaled by the actor's own Legibility, so this only actually matters once you're genuinely typecast
# — an undefined actor reads the same to every gatekeeper.
LEGIBILITY_GATEKEEPER_COEF = 0.9


def gatekeeper_legibility_multiplier(gatekeeper: str, legibility: float) -> float:
    weights = GATEKEEPER_WEIGHTS.get(gatekeeper)
    if weights is None:
        return 1.0
    lean = weights["prestige"] - weights["heat"]
    base = 1.0 + LEGIBILITY_GATEKEEPER_COEF * lean
    return 1.0 + (base - 1.0) * clamp(legibility, 0.0, 100.0) / 100.0


def fit_score(attrs: Attributes, persona: Persona, role: Role, your_age: int) -> float:
    age_pen = age_mismatch_penalty(role.char_age, your_age, role.is_animation)
    type_pen = typecasting_penalty(persona, role) * gatekeeper_legibility_multiplier(role.gatekeeper, persona.legibility())
    gate_pen = hard_gate_penalty(attrs, role.requirements)
    return clamp(100.0 - age_pen - type_pen - gate_pen, 0.0, 100.0)


# design/part-04 §4.2's "breaking type" — a role that genuinely fights your Persona, not just one
# a shade off it. typecasting_penalty's own combined terms range 0-90 (two 0-45 halves, at
# type_strictness=1.0); this threshold sits well above what an ordinary mixed-lane role produces,
# so it only fires on a real, deliberate stretch.
BREAKING_TYPE_THRESHOLD = 40.0


def is_breaking_type(persona: Persona, role: Role) -> bool:
    return typecasting_penalty(persona, role) >= BREAKING_TYPE_THRESHOLD


def in_lane(persona: Persona, role: Role) -> bool:
    """§4.2's own "flood of offers in your lane" — whether this role sits in either of your two
    strongest-affinity slots."""
    return role.genre == persona.top_genre() or role.archetype == persona.top_archetype()


# The critics/audience wedge — real typecasting is a split reaction, not one flat penalty. Critics
# tire of repetition fast (persona.staleness_penalty, already built, hits FilmCriticScore only);
# audiences often get MORE comfortable seeing you play what you're known for, the more you do it.
# Scaled by Legibility, same as the gatekeeper multiplier above — an actor with no defined lane
# yet has no "comfort casting" bonus to draw on.
IN_LANE_AUDIENCE_BONUS_COEF = 0.12  # at full Legibility (100), a +12 AudienceScore bonus — the
# same order of magnitude as genre.adaptation.ADAPTATION_AUDIENCE_BONUS (10.0), a real, comparable
# reception effect, not a token nudge.


def in_lane_audience_bonus(persona: Persona, role: Role) -> float:
    if not in_lane(persona, role):
        return 0.0
    return IN_LANE_AUDIENCE_BONUS_COEF * persona.legibility()


# The one added friction on a genuine type-break attempt (deliberately just one, not stacked with
# a second economic penalty on top of the Fit penalty already in play) — the industry's own
# institutional risk-aversion toward an off-lane cast, separate from "you don't read right on paper"
# (which the Fit penalty above already covers). Flat, not scaled: if it's a real type-break at all,
# it's harder to land, full stop — a second, independent hurdle stacked onto (not multiplying) Fit.
TYPE_BREAK_DIFFICULTY_TAX = 12.0


def type_break_difficulty_tax(persona: Persona, role: Role) -> float:
    return TYPE_BREAK_DIFFICULTY_TAX if is_breaking_type(persona, role) else 0.0


def relationship_bonus(rolodex_edges: list[tuple[float, float]] | None = None) -> float:
    """Σ 0.30·affinity − 0.55·grudge over Rolodex members attached to the production. The Rolodex
    (§4.12) isn't modeled in this pass; stubbed at 0 by default. Takes real (affinity, grudge)
    pairs so a future Rolodex module plugs in without changing this function's contract."""
    if not rolodex_edges:
        return 0.0
    return sum(0.30 * affinity - 0.55 * grudge for affinity, grudge in rolodex_edges)


def utility(
    attrs: Attributes,
    persona: Persona,
    standing_model: StandingModel,
    role: Role,
    your_age: int,
    quote_value: float,
    rolodex_edges: list[tuple[float, float]] | None = None,
    bypass_standing: bool = False,
) -> float:
    """bypass_standing: design/part-06 §6.6's "Screen-test for free" — "bypasses the Standing
    term in §4.4 entirely." Zeroes StandingScore's contribution rather than skipping the term
    structurally, so the rest of Utility's shape (Fit, attributes, relationships) is unchanged."""
    standing_score = 0.0 if bypass_standing else standing_model.weighted_score(GATEKEEPER_WEIGHTS[role.gatekeeper])
    fit = fit_score(attrs, persona, role, your_age)
    attr_term = UTILITY_ATTR_CRAFT_SHARE * attrs.craft + UTILITY_ATTR_INSTINCT_SHARE * attrs.instinct
    overage = min(quote_value / role.budget_for_role - 1.0, 1.0)
    overprice = UTILITY_OVERPRICE_COEF * positive_part(overage)
    return (
        UTILITY_STANDING_WEIGHT * standing_score
        + UTILITY_FIT_WEIGHT * fit
        + UTILITY_ATTR_WEIGHT * attr_term
        + relationship_bonus(rolodex_edges)
        - overprice
    )


def offer_probability(utility_value: float, difficulty: float) -> float:
    return sigmoid(OFFER_PROBABILITY_SLOPE * (utility_value - difficulty))


def resolve_casting_path(utility_value: float, role: Role) -> str:
    """"direct_offer" | "audition". §4.4's third path — a director's Rolodex affinity>70 handing
    you the part outright regardless of Standing — needs the Rolodex and is out of scope for this
    pass; not silently dropped, just not reachable until that module exists."""
    if utility_value - role.difficulty > OPEN_OFFER_UTILITY_MARGIN:
        return "direct_offer"
    return "audition"


def is_offered_non_union(credits: int, rng: random.Random) -> bool:
    """§4.0 — under 3 union credits, a union-eligible listing has a 25% chance of being offered
    non-union instead (paying NON_UNION_PAY_FRACTION as much)."""
    if credits >= NON_UNION_CREDIT_THRESHOLD:
        return False
    return rng.random() < NON_UNION_SUBSTITUTION_CHANCE


def sample_role(rng: random.Random, budget_millions: float | None = None, actor_leverage: float | None = None) -> Role:
    """A minimal role-listing generator for simulation/career.py's headless loop. This is not the
    full offer-board content system (§4.4's own listing generator reads the world's production
    pipeline, §10.0 — out of scope here); it draws a plausible role so casting/Utility can be
    exercised end to end.

    actor_leverage: 0-1, typically the actor's own standing_score/100 — how much real pull they
    bring into the fee negotiation for this listing. None (the default, used by any caller without
    a real actor in hand — verify.py, standalone tests) falls back to a random position, same as
    treating every anonymous listing as negotiated by an unknown quantity."""
    genre = rng.choice(GENRES)
    secondary_genre = None
    if rng.random() < HYBRID_CHANCE:
        other = rng.choice([g for g in GENRES if g != genre])
        secondary_genre = other
    archetype = rng.choice(ARCHETYPES)
    role_depth = sample_role_depth(rng)
    billing = rng.choices(BILLINGS[:3], weights=[0.15, 0.45, 0.40])[0]  # leads are rarer to land
    budget = budget_millions if budget_millions is not None else sample_budget_millions(rng)
    gatekeeper = rng.choice(list(GATEKEEPER_WEIGHTS.keys()))
    studio = pick_studio(budget, rng).id  # who's financing scales with the film's own budget, not the role's fee
    leverage = actor_leverage if actor_leverage is not None else rng.random()
    is_series = rng.random() < SERIES_CHANCE
    return Role(
        project_id=f"p_{rng.randrange(10**6):06d}",
        genre=genre,
        archetype=archetype,
        billing=billing,
        char_age=int(clamp(rng.gauss(38, 12), 8, 85)),
        type_strictness=clamp(rng.gauss(0.6, 0.2), 0.0, 1.0),
        difficulty=clamp(role_difficulty(budget, rng) + role_depth_difficulty_bonus(role_depth, archetype), 5.0, 95.0),
        budget_for_role=budget * negotiated_fee_share(billing, leverage, rng),  # a negotiated fee, not a hard number
        gatekeeper=gatekeeper,
        studio=studio,
        film_budget_millions=budget,  # the real film budget — kept, not discarded, for reception/ROI/marketing
        latent_quality=clamp(rng.gauss(LATENT_QUALITY_MEAN, LATENT_QUALITY_SD), 0.0, 100.0),
        project_type="series" if is_series else "film",
        n_episodes=sample_episode_count(rng) if is_series else None,
        series_renewable=is_series and rng.random() < SERIES_RENEWABLE_CHANCE,
        is_animation=rng.random() < ANIMATION_CHANCE,
        secondary_genre=secondary_genre,
        role_depth=role_depth,
    )
