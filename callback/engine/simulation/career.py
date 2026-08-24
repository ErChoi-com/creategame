"""Orchestrates one actor's season loop (design/part-03-design-overview.md §3.4) out of the
actor/ Stages: casting -> prep -> the shoot (palette/positions/shape) -> performance -> reception
-> standing/persona update.

Depends only on each actor/ module's public functions — never imports simulation/ from actor/,
and never reaches past a stage's public entry point into its internals.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.actor.aging import apply_look_curve
from callback.engine.actor.attributes import Attributes
from callback.engine.actor.offers import (
    Role,
    fit_score,
    in_lane_audience_bonus,
    is_breaking_type,
    is_offered_non_union,
    offer_probability,
    resolve_casting_path,
    sample_role,
    type_break_difficulty_tax,
    utility,
)
from callback.engine.actor.palette import CANONICAL_ARCHETYPES, Palette, palette_reception_effect
from callback.engine.actor.performance import PerformanceResult, resolve_performance
from callback.engine.actor.persona import Persona
from callback.engine.actor.rating import (
    CUT_CRITIC_PENALTY_HI,
    CUT_CRITIC_PENALTY_LO,
    RATING_CUT,
    RATING_RELEASE_AS_SHOT,
    RELEASE_AS_SHOT_EXEMPT_GENRES,
    RELEASE_AS_SHOT_REACH_PENALTY_COEF,
    friendlier_band,
    near_boundary,
    nearest_boundary_distance,
    rating_band,
    rating_score,
)
from callback.engine.actor.positions import (
    DIALS,
    POSITIONS,
    ModifierResult,
    contrast_budget,
    overspend_penalty,
    resolve_scene_positions,
)
from callback.engine.actor.prep import PrepResult, resolve_prep
from callback.engine.actor.reception import RIGHTS_SHARE, ReceptionResult, resolve_reception
from callback.engine.actor.release import FESTIVAL, LIMITED, STREAMING, STREAMING_BUYOUT_MULTIPLIER, WIDE, apply_release_strategy
from callback.engine.core.script_notes import ACTOR_FILM_NOTE_WEIGHT, ScriptNoteEffect, sample_director_note
from callback.engine.actor.shape import resolve_shape
from callback.engine.genre.adaptation import adaptation_audience_bonus, adaptation_critic_risk
from callback.engine.genre.hybrids import hybrid_demand
from callback.engine.director.composer import Composer, resolve_score_effect
from callback.engine.actor.studios import (
    OPENING_MARKETING_COEF,
    STUDIOS,
    FestivalBid,
    MarketingDecision,
    RatingCutDecision,
    Studio,
    StreamingBid,
    decide_marketing_spend,
    decide_rating_cut,
    quality_adjusted_bids,
    quality_adjusted_festival_bids,
)
from callback.engine.actor.standing import (
    RecognitionMeter,
    HEAT_KEEP,
    AFFECTION_DECAY,
    NOTORIETY_DECAY,
    PRESTIGE_DECAY,
    delta_affection,
    delta_heat,
    delta_prestige,
    new_standing_model,
    quote,
    standing_score,
    star_power,
)
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp

SceneChoice = dict[str, str]  # one of DIALS -> one of POSITIONS, per scene

BILLING_WEIGHT = {"lead": 1.0, "supporting": 0.55, "bit": 0.2, "extra": 0.0}


@dataclass(frozen=True)
class ActorState:
    age: int
    attrs: Attributes
    persona: Persona
    standing: StandingModel
    recognition: RecognitionMeter = field(default_factory=RecognitionMeter)
    credits: int = 0
    union_credits: int = 0
    roi_history: tuple[float, ...] = ()
    award_nominations: int = 0  # awards.NarrativeContext.prior_nominations's real source — a
    # career total, incremented by simulation/session.py.run_awards_campaign on every nomination.
    # 0 (every existing caller) means "she's due" (3+ nominations, 0 wins) starts unreachable,
    # exactly as before this field existed, not a behavior change for anyone who doesn't use it.
    award_wins: int = 0

    def recent_roi_normalized(self) -> float:
        """ROI history isn't specified with a normalization by design/; this pass reads the
        trailing-3-project mean ROI onto a 0-100 scale centred on ROI=1.0 (break-even)."""
        if not self.roi_history:
            return 50.0
        recent = self.roi_history[-3:]
        return clamp(50.0 + 50.0 * (sum(recent) / len(recent) - 1.0), 0.0, 100.0)

    def quote_value(self, era_multiplier: float = 1.0) -> float:
        return quote(self.standing, self.recent_roi_normalized(), era_multiplier)


def new_actor(age: int = 22, attrs: Attributes | None = None) -> ActorState:
    return ActorState(age=age, attrs=(attrs or Attributes()).clamped(), persona=Persona(), standing=new_standing_model())


@dataclass(frozen=True)
class ProjectResult:
    role: Role
    cast_via: str
    spotlight: float
    craft_contribution: float
    performance: float
    project_quality: float
    film_critic_score: float
    audience_score: float
    roi: float
    budget: float  # production budget only — see marketing below
    marketing: float
    gross: float
    opening: float
    legs: float
    release_strategy: str
    heat_delta: float
    prestige_delta: float
    affection_delta: float
    npc_affinity_delta: float = 0.0
    favour_gain: float = 0.0
    studio_id: str = "mid_major"
    marketing_push_requested: bool = False
    marketing_push_honored: bool = False
    director_note_choice: str = ""
    rating_band: str = ""
    rating_cut_available: bool = False
    rating_stance_requested: str = RATING_RELEASE_AS_SHOT
    rating_stance_applied: str = RATING_RELEASE_AS_SHOT
    rating_cut_forced: bool = False
    rating_studio_pressure: bool = False
    break_even: float = 0.0  # §6.5 v21 — budget + marketing recouped-at point; a net_points box
    # office bonus only pays above this, scaled to the real profit past it, not raw gross
    transformation: bool = False  # design/part-04 §4.2 — a successful, deliberate type-break;
    # feeds simulation.session.Session.run_awards_campaign's own award-narrative bonus.


def default_scene_policy(rng: random.Random) -> tuple[SceneChoice, SceneChoice, SceneChoice]:
    """A simple headless default: mostly restrained, occasionally shaped — not tuned against any
    §14.6 target, just enough to exercise the shoot end to end. simulation/verify.py uses fixed,
    named allocations instead of this policy for the actual §14.6 checks."""
    weights = {"with": 0.40, "beneath": 0.30, "beyond": 0.20, "against": 0.10}
    choices = []
    for _ in range(3):
        choices.append({d: rng.choices(POSITIONS, weights=[weights[p] for p in POSITIONS])[0] for d in DIALS})
    return tuple(choices)  # type: ignore[return-value]


def generate_palette(genre: str, rng: random.Random) -> Palette:
    """The film's shape is set by its director, not the player (§5.3) — sampled near the genre's
    canonical archetype with noise, standing in for an NPC director's choice."""
    archetype = CANONICAL_ARCHETYPES[genre]
    return Palette(**{d: clamp(archetype[d] + rng.gauss(0, 8), -50, 50) for d in archetype}).clamped()


# --- a project's resolution, as separate stages ------------------------------------------------
# One project used to be a single ~150-line function. It's split here into the same named stages
# design/ itself already treats as distinct (the shoot, the film's own quality, how it reaches an
# audience, what it leaves on the actor) so each is independently callable and testable — but
# simulate_project still calls them as plain, inlined function calls in one straight line, not
# through core.pipeline's Stage indirection or extra object churn, so the split costs nothing at
# runtime beyond ordinary Python call overhead. The relative order below is load-bearing: it's the
# exact sequence the old monolithic function drew from `rng` in, preserved stage-by-stage so every
# existing seed still reproduces byte-for-byte identical runs.


@dataclass(frozen=True)
class DirectorTerms:
    skill: float
    command: float
    prestige: float


def resolve_director(director_override: tuple[float, float, float] | None, rng: random.Random) -> DirectorTerms:
    if director_override is not None:
        skill, command, prestige = director_override
        return DirectorTerms(skill, command, prestige)
    # NPC director — the director career (Part 7) isn't modeled in this pass; sampled per §7.3's
    # own verification convention (attributes ~ N(58, 16)) rather than invented fresh.
    return DirectorTerms(
        skill=clamp(rng.gauss(58, 16), 5, 100),
        command=clamp(rng.gauss(58, 16), 5, 100),
        prestige=clamp(rng.gauss(50, 20), 0, 100),
    )


@dataclass(frozen=True)
class ShootResult:
    """The physical work of making the film — prep, fit, chemistry, the Performance roll, and the
    three-scene shape it produces. Nothing here is the finished film's quality or box office —
    those are resolve_quality's job, next."""
    prep_result: PrepResult
    perf_result: PerformanceResult
    spotlight: float
    craft_contribution: float
    npc_affinity_delta: float
    director_note_choice: str
    director_note: ScriptNoteEffect


def resolve_shoot(
    state: ActorState,
    role: Role,
    prep_choice: str,
    scene_choices: tuple[SceneChoice, SceneChoice, SceneChoice],
    director: DirectorTerms,
    rng: random.Random,
    script_note: ScriptNoteEffect | None = None,
    orientation_effect: ModifierResult | None = None,
) -> ShootResult:
    # The director's own creative push on this film — sampled once here (the primary, dominant
    # note) and combined with the actor's own note (secondary, if they hold script approval) inside
    # resolve_quality. fit_delta stays the actor's alone: their own read on their own part isn't
    # something the director's note touches.
    director_note_choice, director_note = sample_director_note(director.skill, director.command, rng)
    prep_result = resolve_prep(prep_choice, state.attrs.resilience, is_biographical_or_period=(role.genre == "period"))
    fit = fit_score(state.attrs, state.persona, role, state.age)
    if script_note is not None:
        fit = clamp(fit + script_note.fit_delta, 0.0, 100.0)
    chemistry = clamp(rng.gauss(60, 18), 0, 100)

    perf_result = resolve_performance(
        state.attrs, fit, prep_result.prep, chemistry, director.command, director.skill, rng,
    )

    budget = contrast_budget(state.attrs.craft, director.command)
    scene_reads = tuple(resolve_scene_positions(choice, role.genre, budget) for choice in scene_choices)
    shape_result = resolve_shape(scene_reads, perf_result.performance)  # type: ignore[arg-type]

    spotlight_pen, craft_contribution_pen = overspend_penalty(shape_result.total_overspend)
    spotlight = max(shape_result.spotlight + spotlight_pen, state.attrs.spotlight_floor())
    craft_contribution = shape_result.craft_contribution + craft_contribution_pen

    npc_affinity_delta = 0.0
    if orientation_effect is not None:
        spotlight = spotlight + orientation_effect.you_spotlight
        craft_contribution = craft_contribution + orientation_effect.film_craft_contribution
        npc_affinity_delta = orientation_effect.affinity_delta

    return ShootResult(
        prep_result, perf_result, spotlight, craft_contribution, npc_affinity_delta,
        director_note_choice, director_note,
    )


@dataclass(frozen=True)
class RatingOutcome:
    """design/part-05 §5.19 — read off the palette's own Intensity dial the moment it's generated,
    never touched by anything downstream (script notes, prep, the shoot). cut_available mirrors
    rating.near_boundary(score): only a genuine borderline film ever has a real stance to resolve;
    everything else ships with stance_applied left at whatever was requested, inert."""
    score: float
    band: str
    cut_available: bool
    stance_requested: str
    stance_applied: str
    forced: bool
    studio_pressure: bool
    critic_delta: float
    audience_delta: float


def resolve_rating(
    palette: Palette,
    role: Role,
    studio: Studio,
    studio_trust: float,
    actor_importance: float,
    requested_stance: str,
    rng: random.Random,
    influence_fn=None,
) -> RatingOutcome:
    """The one real decision the rating creates: cut for the friendlier band, or release as shot.
    influence_fn: passed straight to studios.decide_rating_cut() — director_influence_on_studio_
    decision() for a director's own project, the default actor curve otherwise."""
    score = rating_score(palette.intensity, role.genre, role.is_animation)
    base_band = rating_band(score)
    if not near_boundary(score):
        return RatingOutcome(score, base_band, False, requested_stance, requested_stance, False, False, 0.0, 0.0)

    kwargs = {} if influence_fn is None else {"influence_fn": influence_fn}
    is_franchise_or_adaptation = bool(role.franchise_id or role.source_material)
    decision: RatingCutDecision = decide_rating_cut(
        studio, score, role.film_budget_millions, is_franchise_or_adaptation,
        requested_stance, studio_trust, actor_importance, rng, **kwargs,
    )

    if decision.actual_stance == RATING_CUT:
        critic_delta = -rng.uniform(CUT_CRITIC_PENALTY_LO, CUT_CRITIC_PENALTY_HI)
        return RatingOutcome(
            score, friendlier_band(score), True, requested_stance, RATING_CUT,
            decision.forced, decision.studio_wanted_cut, critic_delta, 0.0,
        )

    audience_delta = 0.0
    if role.genre not in RELEASE_AS_SHOT_EXEMPT_GENRES:
        audience_delta = -RELEASE_AS_SHOT_REACH_PENALTY_COEF * nearest_boundary_distance(score)
    return RatingOutcome(
        score, base_band, True, requested_stance, RATING_RELEASE_AS_SHOT,
        decision.forced, decision.studio_wanted_cut, 0.0, audience_delta,
    )


def resolve_quality(
    state: ActorState,
    role: Role,
    shoot: ShootResult,
    director: DirectorTerms,
    palette: Palette,
    rng: random.Random,
    genre_demand_override: float | None = None,
    franchise_audience_bonus: float = 0.0,
    script_note: ScriptNoteEffect | None = None,
    studio_trust: float = 50.0,
    requested_marketing_push: bool = False,
    requested_rating_stance: str = RATING_RELEASE_AS_SHOT,
    actor_importance: float = 50.0,
    score_genre: str | None = None,
    composer: Composer | None = None,
) -> tuple[ReceptionResult, Studio, MarketingDecision, float, RatingOutcome]:
    """The film's critic/audience quality and its baseline box office — resolved once, before any
    release strategy is chosen or applied, and never touched again afterward (release.py's own
    contract). Returns (reception, studio, marketing_decision, cast_star_power, rating_outcome) —
    the studio/marketing_decision/cast_star_power are needed again, unchanged, by
    resolve_release_schedule; rating_outcome is terminal, nothing downstream reads it further.

    studio_trust/requested_marketing_push feed studios.decide_marketing_spend(): the studio's own
    real-money campaign decision, deliberately NOT a function of this project's own resolved
    quality (nobody, including the studio, has a reliable read on that yet at this point) — see
    that function's own docstring for why.

    requested_rating_stance/actor_importance feed resolve_rating(): §5.19's content rating, read
    off palette.intensity (fixed the moment the palette was generated, untouched by script notes or
    the shoot) the same way studios.decide_release_strategy() reads Standing for a release-strategy
    request — only ever a real decision on a genuine borderline film (rating.near_boundary).

    score_genre/composer: creative-revamp-plan.md §13/§13.1 — the film's own score genre and the
    composer hired to deliver it. Both None (every existing caller) leaves this exactly as before;
    given together, the composer's Skill/style-Fit against score_genre folds one small (audience,
    critic) delta into the same stack franchise/adaptation/hybrid bonuses already build up."""
    # genre_demand_override lets a caller with real §9.3 GenreHeat (simulation/full_career.py,
    # which tracks it) feed the actual background-industry cycle in instead of this fallback
    # sample — kept here, not removed, so simulate_project stays usable standalone (verify.py's
    # checks, unit tests) without requiring a world/ import.
    genre_demand = genre_demand_override if genre_demand_override is not None else clamp(rng.gauss(55, 15), 0, 100)
    cast_star_power = clamp(rng.gauss(50, 20), 0, 100)
    is_hybrid = role.secondary_genre is not None
    if is_hybrid:
        # §9.2 — "hybrids average the demand of both parents." No caller currently tracks a real
        # per-genre GenreHeat for a secondary genre (world/genre_cycle.py is keyed by role.genre
        # alone), so the secondary side falls back to the same blind sample the primary side uses
        # whenever genre_demand_override is absent — same honest uncertainty, not a special case.
        secondary_demand = clamp(rng.gauss(55, 15), 0, 100)
        genre_demand = hybrid_demand(genre_demand, secondary_demand)
    # §4.4 v17 — script_quality is now a real, persisted fact about the role (Role.latent_quality,
    # sampled once at offer-generation time in offers.sample_role) rather than re-rolled blind here.
    # Same (60, 14) distribution as before — this is a wiring change, not a rebalance — but now a
    # "buzz" read on it can be surfaced to the player before they accept (see Session._buzz_band).
    script_quality = role.latent_quality
    palette_aud_effect, palette_crit_effect = palette_reception_effect(palette, role.genre)
    if is_hybrid:
        # design/part-09 §9.2 — a hybrid reads BOTH parent genres' palette weights, averaged, same
        # shape as hybrid_demand() below averaging the two parents' GenreDemand.
        sec_aud, sec_crit = palette_reception_effect(palette, role.secondary_genre)
        palette_aud_effect = (palette_aud_effect + sec_aud) / 2.0
        palette_crit_effect = (palette_crit_effect + sec_crit) / 2.0
    palette_aud_effect += franchise_audience_bonus
    palette_aud_effect += adaptation_audience_bonus(role.source_material, role.source_material_popularity)
    if composer is not None and score_genre is not None:
        # creative-revamp-plan.md §13.1 — the composer hire's whole mechanical contribution: one
        # small (audience, critic) delta, folded in exactly like every other bonus on this stack.
        score_aud, score_crit = resolve_score_effect(composer, score_genre)
        palette_aud_effect += score_aud
        palette_crit_effect += score_crit
    # The critics/audience wedge (design/part-04 §4.2) — comfort casting is a real, distinct
    # audience-side effect from persona.staleness_penalty's own critic-side fatigue below; the two
    # pull the same "played your lane again" choice in opposite directions.
    palette_aud_effect += in_lane_audience_bonus(state.persona, role)
    palette_crit_effect += adaptation_critic_risk(role.source_material, role.source_material_popularity)
    staleness = state.persona.staleness_penalty()

    # The director's note is the film's primary creative signal (full weight, sampled once in
    # resolve_shoot); the actor's own note — real, but secondary on someone else's film — is scaled
    # down before it's added on top. Both genuinely move the finished film; the director's moves it
    # more, matching who actually holds the film's creative authority.
    combined_note = shoot.director_note
    if script_note is not None:
        combined_note = combined_note.combined_with(script_note.scaled(ACTOR_FILM_NOTE_WEIGHT))
    script_quality = clamp(script_quality + combined_note.script_quality_delta, 0.0, 100.0)
    palette_aud_effect += combined_note.audience_delta
    palette_crit_effect += combined_note.critic_delta

    studio = STUDIOS[role.studio]
    rating_outcome = resolve_rating(
        palette, role, studio, studio_trust, actor_importance, requested_rating_stance, rng,
    )
    palette_aud_effect += rating_outcome.audience_delta
    palette_crit_effect += rating_outcome.critic_delta

    marketing_decision = decide_marketing_spend(
        studio, role.film_budget_millions, studio_trust, star_power(state.standing), genre_demand,
        is_franchise_or_adaptation=bool(role.franchise_id or role.source_material),
        requested_push=requested_marketing_push, rng=rng,
    )
    marketing_share = marketing_decision.marketing_share

    reception = resolve_reception(
        script_quality=script_quality,
        director_skill=director.skill,
        craft_contribution=shoot.craft_contribution,
        genre=role.genre,
        role_budget_millions=role.film_budget_millions,
        director_prestige=director.prestige,
        staleness_penalty=staleness,
        cast_star_power=cast_star_power,
        genre_demand=genre_demand,
        rng=rng,
        palette_audience_effect=palette_aud_effect,
        palette_critic_effect=palette_crit_effect,
        marketing_share=marketing_share,
        rights_share=RIGHTS_SHARE + studio.rights_share_delta,
        opening_marketing_coef=OPENING_MARKETING_COEF,
        is_animation=role.is_animation,
        is_hybrid=is_hybrid,
    )
    return reception, studio, marketing_decision, cast_star_power, rating_outcome


def resolve_release_schedule(
    reception: ReceptionResult,
    role: Role,
    studio: Studio,
    marketing_share: float,
    cast_star_power: float,
    release_strategy: str,
    rng: random.Random,
    streaming_multiplier_override: float | None = None,
    streaming_bid_selector=None,
    festival_bid_selector=None,
    franchise_protectiveness: float = 0.0,
) -> ReceptionResult:
    """How the finished film actually reaches an audience. Only ever called after resolve_quality
    — film_critic_score/audience_score/project_quality are already fixed by then and this stage
    never touches them; only the box-office numbers (gross/roi/marketing/opening/legs) move.

    franchise_protectiveness: simulation._franchises.studio_protectiveness() — a proven franchise's
    financing studio doesn't shop the streaming rights around, or the festival rights, as readily
    (see studios.quality_adjusted_bids's own bid-floor note; quality_adjusted_festival_bids shares
    the same read). 0.0 for any standalone film.

    festival_bid_selector: only consulted when release_strategy == "festival" and the submission
    actually clears festival_acquisition_probability's own gate inside apply_release_strategy — an
    unsold submission never reaches this at all. Called with the real bid pool (studios.
    quality_adjusted_festival_bids's competing distributor guarantees, plus one extra FestivalBid —
    self_release=True — for keeping the film and releasing it yourselves at the real LIMITED-release
    numbers rather than a flat guarantee). Must return the chosen FestivalBid. Defaults to
    auto-accepting the best payout_millions when no selector is given, same as streaming."""
    if release_strategy == STREAMING and streaming_multiplier_override is None:
        # Quality is already resolved — the sale happens after the movie has been made, and it
        # shows: a bad film draws a thinner, worse pool than a good one.
        bids = quality_adjusted_bids(
            role.film_budget_millions, role.studio, reception.film_critic_score, reception.audience_score, rng,
            franchise_protectiveness=franchise_protectiveness,
        )
        chosen = streaming_bid_selector(bids) if streaming_bid_selector is not None else max(
            bids, key=lambda b: b.payout_millions,
        )
        streaming_multiplier = chosen.multiplier
    else:
        streaming_multiplier = (
            streaming_multiplier_override if streaming_multiplier_override is not None
            else STREAMING_BUYOUT_MULTIPLIER + studio.streaming_multiplier_delta
        )

    festival_sale_resolver = None
    if release_strategy == FESTIVAL:
        def festival_sale_resolver(sold_reception, m_share, r_share):
            # The financing side's real, always-available alternative to selling at all: keep the
            # film and release it themselves — the actual LIMITED-release numbers (quality-driven,
            # not a flat guarantee), at their own real marketing/rights terms.
            self_release = apply_release_strategy(
                sold_reception, LIMITED, rng, cast_star_power=cast_star_power,
                marketing_share=m_share, rights_share=r_share,
            )
            outside_bids = quality_adjusted_festival_bids(
                role.film_budget_millions, role.studio,
                sold_reception.film_critic_score, sold_reception.audience_score, rng,
                franchise_protectiveness=franchise_protectiveness,
            )
            self_bid = FestivalBid(
                role.studio, studio.name,
                round(self_release.gross / role.film_budget_millions, 2) if role.film_budget_millions else 0.0,
                round(self_release.gross, 2), True,
            )
            bids = [*outside_bids, self_bid]
            chosen = festival_bid_selector(bids) if festival_bid_selector is not None else max(
                bids, key=lambda b: b.payout_millions,
            )
            if chosen.self_release:
                return self_release
            # Sold outright: a flat guarantee replaces the real box office, same convention the
            # streaming buyout already uses — no theatrical marketing spend on the seller's side.
            return replace(
                sold_reception, gross=chosen.payout_millions, marketing=0.0,
                roi=chosen.payout_millions / sold_reception.budget if sold_reception.budget > 0 else 0.0,
            )

    return apply_release_strategy(
        reception, release_strategy, rng, cast_star_power=cast_star_power,
        festival_tier_bonus=studio.festival_tier_bonus,
        marketing_share=marketing_share, rights_share=RIGHTS_SHARE + studio.rights_share_delta,
        streaming_multiplier=streaming_multiplier,
        festival_sale_resolver=festival_sale_resolver,
    )


# design/part-04 §4.2 — "breaking type ... but on success: a large Prestige bonus, a Legibility
# reset toward the middle, and an award-narrative flag (transformation)." "Success" reads as the
# same real, already-established "critically warm" bar simulation._director.EXPANSION_MIN_CRITIC
# uses for a platform expansion — a role fighting your Persona that only lands as mediocre isn't a
# transformation, it's a miscast.
TRANSFORMATION_CRITIC_THRESHOLD = 65.0
# A flat, billing-weighted bonus on top of the normal delta_prestige read — "large" relative to an
# ordinary project's own Prestige delta (typically single digits), not a second full formula. Tuned
# to clearly outweigh type_break_difficulty_tax's own cost of entry — the gamble has to be a good
# bet on paper, not just a survivable one, or no one ever takes it.
TRANSFORMATION_PRESTIGE_BONUS = 10.0


@dataclass(frozen=True)
class StandingUpdate:
    state: ActorState
    heat_delta: float
    prestige_delta: float
    affection_delta: float
    transformation: bool = False


def resolve_standing_update(state: ActorState, role: Role, reception: ReceptionResult, shoot: ShootResult) -> StandingUpdate:
    """Everything a resolved project leaves behind on the actor themselves — Standing, Persona,
    Attributes, Recognition, credits/ROI history. No rng of its own; purely a function of what
    resolve_quality/resolve_release_schedule already produced."""
    bw = BILLING_WEIGHT[role.billing]
    heat_delta = delta_heat(bw, state.credits, role.film_budget_millions, reception.roi, reception.audience_score)
    prestige_delta = delta_prestige(bw, state.credits, reception.film_critic_score, shoot.spotlight)
    affection_delta = delta_affection(bw, state.credits, role.film_budget_millions, reception.audience_score)

    # Read against the Persona the actor walked in WITH — the role's own genre/archetype gain
    # (persona.update below) hasn't happened yet, and shouldn't count toward "was this a stretch."
    transformation = is_breaking_type(state.persona, role) and reception.film_critic_score >= TRANSFORMATION_CRITIC_THRESHOLD
    if transformation:
        prestige_delta += bw * TRANSFORMATION_PRESTIGE_BONUS

    new_standing = state.standing.copy()
    new_standing.add("heat", heat_delta)
    new_standing.add("prestige", prestige_delta)
    new_standing.add("affection", affection_delta)

    new_persona = state.persona.update(role.genre, role.archetype, role.billing, reception.audience_score)
    if transformation:
        new_persona = new_persona.reset_toward_middle()
    new_attrs = state.attrs.with_deltas(craft=shoot.prep_result.craft_delta, resilience=shoot.prep_result.resilience_delta)
    new_recognition = state.recognition.add(shoot.spotlight) if role.billing in ("supporting", "bit") else state.recognition

    new_state = replace(
        state,
        attrs=new_attrs,
        persona=new_persona,
        standing=new_standing,
        recognition=new_recognition,
        credits=state.credits + 1,
        union_credits=state.union_credits + (1 if role.union else 0),
        roi_history=(*state.roi_history, reception.roi)[-10:],
    )
    return StandingUpdate(new_state, heat_delta, prestige_delta, affection_delta, transformation)


def simulate_project(
    state: ActorState,
    role: Role,
    prep_choice: str,
    scene_choices: tuple[SceneChoice, SceneChoice, SceneChoice],
    rng: random.Random,
    palette: Palette | None = None,
    genre_demand_override: float | None = None,
    release_strategy: str | None = None,
    script_note: ScriptNoteEffect | None = None,
    orientation_effect: ModifierResult | None = None,
    director_override: tuple[float, float, float] | None = None,
    franchise_audience_bonus: float = 0.0,
    franchise_protectiveness: float = 0.0,
    streaming_multiplier_override: float | None = None,
    streaming_bid_selector=None,
    festival_bid_selector=None,
    studio_trust: float = 50.0,
    requested_marketing_push: bool = False,
    requested_rating_stance: str = RATING_RELEASE_AS_SHOT,
    actor_importance: float | None = None,
) -> tuple[ActorState, ProjectResult]:
    """script_note: design/part-05 §5.15's script-notes push (core/script_notes.py), only
    meaningful if the player holds script approval — the caller enforces that gate. Combined inside
    resolve_quality with the film's own NPC director's note (sampled in resolve_shoot), which
    applies at full weight while the actor's applies at core.script_notes.ACTOR_FILM_NOTE_WEIGHT —
    the director is this film's primary creative authority, not the actor.
    orientation_effect: positions.generosity()/upstaging(), the player's declared stance toward
    their scene partner this project.
    director_override: (director_skill, director_command, director_prestige) — a specific,
    requested director (e.g. a tracked Rolodex NPC) standing in for the usual random NPC sample.
    franchise_audience_bonus: §9.5's sequel-value curve (simulation._franchises.franchise_audience_
    bonus), a real AudienceScore bonus for a franchise installment — 0.0 for a standalone film.
    franchise_protectiveness: simulation._franchises.studio_protectiveness() — fed straight to
    resolve_release_schedule's own streaming-bid-floor read. 0.0 for a standalone film.
    streaming_bid_selector: only consulted when release_strategy == "streaming" and no explicit
    streaming_multiplier_override is given. The film's quality is known by this point (resolve_
    reception has already run) — called with the real, quality-adjusted bid pool (studios.
    quality_adjusted_bids: fewer or zero outside bidders for a bad film, each buyer's own noisy
    read on it) and must return the chosen StreamingBid. Defaults to auto-accepting the best offer
    when no selector is given, so callers that don't care about the sale (verify.py, tests, the
    rest of simulate_career's loop) don't need to supply one.
    festival_bid_selector: the same idea, for release_strategy == "festival" — see resolve_release_
    schedule's own docstring for the bid shape (studios.quality_adjusted_festival_bids's competing
    guarantees plus a self_release=True option for keeping the film). Only ever consulted once the
    submission clears the acquisition gate; unreached (and irrelevant) for an unsold festival film.
    studio_trust/requested_marketing_push: fed straight to studios.decide_marketing_spend() inside
    resolve_quality — how much this studio actually spends marketing the film, deliberately not a
    function of the film's own resolved quality (see that function's docstring).
    requested_rating_stance/actor_importance: fed straight to resolve_rating() inside resolve_
    quality. actor_importance defaults to state.standing's own standing_score when not given, the
    same real Standing-derived importance studios.decide_release_strategy() already reads for a
    release-strategy request — a rating negotiation uses the same fame, not a second number.
    """
    palette = palette or generate_palette(role.genre, rng)
    director = resolve_director(director_override, rng)
    shoot = resolve_shoot(state, role, prep_choice, scene_choices, director, rng, script_note, orientation_effect)
    importance = actor_importance if actor_importance is not None else standing_score(state.standing)
    reception, studio, marketing_decision, cast_star_power, rating_outcome = resolve_quality(
        state, role, shoot, director, palette, rng, genre_demand_override, franchise_audience_bonus, script_note,
        studio_trust=studio_trust, requested_marketing_push=requested_marketing_push,
        requested_rating_stance=requested_rating_stance, actor_importance=importance,
    )
    if release_strategy is not None:
        reception = resolve_release_schedule(
            reception, role, studio, marketing_decision.marketing_share, cast_star_power, release_strategy, rng,
            streaming_multiplier_override=streaming_multiplier_override,
            streaming_bid_selector=streaming_bid_selector,
            festival_bid_selector=festival_bid_selector,
            franchise_protectiveness=franchise_protectiveness,
        )
    update = resolve_standing_update(state, role, reception, shoot)

    result = ProjectResult(
        role=role,
        cast_via="project",
        spotlight=shoot.spotlight,
        craft_contribution=shoot.craft_contribution,
        performance=shoot.perf_result.performance,
        project_quality=reception.project_quality,
        film_critic_score=reception.film_critic_score,
        audience_score=reception.audience_score,
        roi=reception.roi,
        budget=reception.budget,
        marketing=reception.marketing,
        gross=reception.gross,
        opening=reception.opening,
        legs=reception.legs,
        release_strategy=release_strategy or WIDE,
        heat_delta=update.heat_delta,
        prestige_delta=update.prestige_delta,
        affection_delta=update.affection_delta,
        npc_affinity_delta=shoot.npc_affinity_delta,
        favour_gain=orientation_effect.you_favour if orientation_effect is not None else 0.0,
        studio_id=role.studio,
        marketing_push_requested=marketing_decision.push_requested,
        marketing_push_honored=marketing_decision.push_honored,
        director_note_choice=shoot.director_note_choice,
        rating_band=rating_outcome.band,
        rating_cut_available=rating_outcome.cut_available,
        rating_stance_requested=rating_outcome.stance_requested,
        rating_stance_applied=rating_outcome.stance_applied,
        rating_cut_forced=rating_outcome.forced,
        rating_studio_pressure=rating_outcome.studio_pressure,
        break_even=reception.break_even,
        transformation=update.transformation,
    )
    return update.state, result


def simulate_year(
    state: ActorState,
    rng: random.Random,
    scene_policy=default_scene_policy,
    prep_choice: str = "table_work",
) -> tuple[ActorState, ProjectResult | None]:
    """0-1 projects per year — a simplified block-availability check, not the full multi-offer
    calendar/scheduling UI (out of scope for this pass)."""
    role = sample_role(rng)
    quote_value = state.quote_value()

    if role.union and is_offered_non_union(state.union_credits, rng):
        role = replace(role, union=False, budget_for_role=role.budget_for_role / 3.0)

    u = utility(state.attrs, state.persona, state.standing, role, state.age, quote_value)
    path = resolve_casting_path(u, role)
    difficulty = role.difficulty + type_break_difficulty_tax(state.persona, role)
    cast = path == "direct_offer" or rng.random() < offer_probability(u, difficulty)

    # end-of-year decay always applies, whether or not a project happened this year.
    decayed_standing = state.standing.copy()
    heat_tier = role.billing if cast else "idle"
    decayed_standing.decay({
        "heat": HEAT_KEEP.get(heat_tier, HEAT_KEEP["idle"]),
        "prestige": PRESTIGE_DECAY,
        "affection": AFFECTION_DECAY,
        "notoriety": NOTORIETY_DECAY,
    })
    new_age = state.age + 1
    aged_attrs = state.attrs.age_decay(new_age)
    aged_attrs = replace(aged_attrs, look=apply_look_curve(aged_attrs.look, new_age)).clamped()
    state = replace(state, standing=decayed_standing, age=new_age, attrs=aged_attrs)

    if not cast:
        return state, None

    scene_choices = scene_policy(rng)
    return simulate_project(state, role, prep_choice, scene_choices, rng)


def simulate_career(
    start_age: int,
    years: int,
    rng: random.Random,
    attrs: Attributes | None = None,
) -> tuple[ActorState, list[ProjectResult]]:
    state = new_actor(start_age, attrs)
    results: list[ProjectResult] = []
    for _ in range(years):
        state, result = simulate_year(state, rng)
        if result is not None:
            results.append(result)
    return state, results
