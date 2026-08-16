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
    is_offered_non_union,
    offer_probability,
    resolve_casting_path,
    sample_role,
    utility,
)
from callback.engine.actor.palette import CANONICAL_ARCHETYPES, Palette, palette_reception_effect
from callback.engine.actor.performance import PerformanceResult, resolve_performance
from callback.engine.actor.persona import Persona
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
from callback.engine.actor.release import STREAMING, STREAMING_BUYOUT_MULTIPLIER, WIDE, apply_release_strategy
from callback.engine.actor.script_notes import ScriptNoteEffect
from callback.engine.actor.shape import resolve_shape
from callback.engine.genre.adaptation import adaptation_audience_bonus, adaptation_critic_risk
from callback.engine.actor.studios import (
    OPENING_MARKETING_COEF,
    STUDIOS,
    MarketingDecision,
    Studio,
    StreamingBid,
    decide_marketing_spend,
    quality_adjusted_bids,
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

    return ShootResult(prep_result, perf_result, spotlight, craft_contribution, npc_affinity_delta)


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
) -> tuple[ReceptionResult, Studio, MarketingDecision, float]:
    """The film's critic/audience quality and its baseline box office — resolved once, before any
    release strategy is chosen or applied, and never touched again afterward (release.py's own
    contract). Returns (reception, studio, marketing_decision, cast_star_power) — the studio/
    marketing_decision/cast_star_power are needed again, unchanged, by resolve_release_schedule.

    studio_trust/requested_marketing_push feed studios.decide_marketing_spend(): the studio's own
    real-money campaign decision, deliberately NOT a function of this project's own resolved
    quality (nobody, including the studio, has a reliable read on that yet at this point) — see
    that function's own docstring for why."""
    # genre_demand_override lets a caller with real §9.3 GenreHeat (simulation/full_career.py,
    # which tracks it) feed the actual background-industry cycle in instead of this fallback
    # sample — kept here, not removed, so simulate_project stays usable standalone (verify.py's
    # checks, unit tests) without requiring a world/ import.
    genre_demand = genre_demand_override if genre_demand_override is not None else clamp(rng.gauss(55, 15), 0, 100)
    cast_star_power = clamp(rng.gauss(50, 20), 0, 100)
    script_quality = clamp(rng.gauss(60, 14), 0, 100)
    palette_aud_effect, palette_crit_effect = palette_reception_effect(palette, role.genre)
    palette_aud_effect += franchise_audience_bonus
    palette_aud_effect += adaptation_audience_bonus(role.source_material)
    palette_crit_effect += adaptation_critic_risk(role.source_material)
    staleness = state.persona.staleness_penalty()

    if script_note is not None:
        script_quality = clamp(script_quality + script_note.script_quality_delta, 0.0, 100.0)
        palette_aud_effect += script_note.audience_delta
        palette_crit_effect += script_note.critic_delta

    studio = STUDIOS[role.studio]
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
    )
    return reception, studio, marketing_decision, cast_star_power


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
) -> ReceptionResult:
    """How the finished film actually reaches an audience. Only ever called after resolve_quality
    — film_critic_score/audience_score/project_quality are already fixed by then and this stage
    never touches them; only the box-office numbers (gross/roi/marketing/opening/legs) move."""
    if release_strategy == STREAMING and streaming_multiplier_override is None:
        # Quality is already resolved — the sale happens after the movie has been made, and it
        # shows: a bad film draws a thinner, worse pool than a good one.
        bids = quality_adjusted_bids(
            role.film_budget_millions, role.studio, reception.film_critic_score, reception.audience_score, rng,
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
    return apply_release_strategy(
        reception, release_strategy, rng, cast_star_power=cast_star_power,
        festival_tier_bonus=studio.festival_tier_bonus,
        marketing_share=marketing_share, rights_share=RIGHTS_SHARE + studio.rights_share_delta,
        streaming_multiplier=streaming_multiplier,
    )


@dataclass(frozen=True)
class StandingUpdate:
    state: ActorState
    heat_delta: float
    prestige_delta: float
    affection_delta: float


def resolve_standing_update(state: ActorState, role: Role, reception: ReceptionResult, shoot: ShootResult) -> StandingUpdate:
    """Everything a resolved project leaves behind on the actor themselves — Standing, Persona,
    Attributes, Recognition, credits/ROI history. No rng of its own; purely a function of what
    resolve_quality/resolve_release_schedule already produced."""
    bw = BILLING_WEIGHT[role.billing]
    heat_delta = delta_heat(bw, state.credits, role.film_budget_millions, reception.roi, reception.audience_score)
    prestige_delta = delta_prestige(bw, state.credits, reception.film_critic_score, shoot.spotlight)
    affection_delta = delta_affection(bw, state.credits, role.film_budget_millions, reception.audience_score)

    new_standing = state.standing.copy()
    new_standing.add("heat", heat_delta)
    new_standing.add("prestige", prestige_delta)
    new_standing.add("affection", affection_delta)

    new_persona = state.persona.update(role.genre, role.archetype, role.billing, reception.audience_score)
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
    return StandingUpdate(new_state, heat_delta, prestige_delta, affection_delta)


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
    streaming_multiplier_override: float | None = None,
    streaming_bid_selector=None,
    studio_trust: float = 50.0,
    requested_marketing_push: bool = False,
) -> tuple[ActorState, ProjectResult]:
    """script_note: design/part-05 §5.15's script-notes push (actor/script_notes.py), only
    meaningful if the player holds script approval — the caller enforces that gate.
    orientation_effect: positions.generosity()/upstaging(), the player's declared stance toward
    their scene partner this project.
    director_override: (director_skill, director_command, director_prestige) — a specific,
    requested director (e.g. a tracked Rolodex NPC) standing in for the usual random NPC sample.
    franchise_audience_bonus: §9.5's sequel-value curve (simulation._franchises.franchise_audience_
    bonus), a real AudienceScore bonus for a franchise installment — 0.0 for a standalone film.
    streaming_bid_selector: only consulted when release_strategy == "streaming" and no explicit
    streaming_multiplier_override is given. The film's quality is known by this point (resolve_
    reception has already run) — called with the real, quality-adjusted bid pool (studios.
    quality_adjusted_bids: fewer or zero outside bidders for a bad film, each buyer's own noisy
    read on it) and must return the chosen StreamingBid. Defaults to auto-accepting the best offer
    when no selector is given, so callers that don't care about the sale (verify.py, tests, the
    rest of simulate_career's loop) don't need to supply one.
    studio_trust/requested_marketing_push: fed straight to studios.decide_marketing_spend() inside
    resolve_quality — how much this studio actually spends marketing the film, deliberately not a
    function of the film's own resolved quality (see that function's docstring).
    """
    palette = palette or generate_palette(role.genre, rng)
    director = resolve_director(director_override, rng)
    shoot = resolve_shoot(state, role, prep_choice, scene_choices, director, rng, script_note, orientation_effect)
    reception, studio, marketing_decision, cast_star_power = resolve_quality(
        state, role, shoot, director, palette, rng, genre_demand_override, franchise_audience_bonus, script_note,
        studio_trust=studio_trust, requested_marketing_push=requested_marketing_push,
    )
    if release_strategy is not None:
        reception = resolve_release_schedule(
            reception, role, studio, marketing_decision.marketing_share, cast_star_power, release_strategy, rng,
            streaming_multiplier_override=streaming_multiplier_override,
            streaming_bid_selector=streaming_bid_selector,
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
    cast = path == "direct_offer" or rng.random() < offer_probability(u, role.difficulty)

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
