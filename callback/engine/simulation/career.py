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
from callback.engine.actor.performance import resolve_performance
from callback.engine.actor.persona import Persona
from callback.engine.actor.positions import (
    DIALS,
    POSITIONS,
    ModifierResult,
    contrast_budget,
    overspend_penalty,
    resolve_scene_positions,
)
from callback.engine.actor.prep import resolve_prep
from callback.engine.actor.reception import RIGHTS_SHARE, resolve_reception
from callback.engine.actor.release import STREAMING, STREAMING_BUYOUT_MULTIPLIER, WIDE, apply_release_strategy
from callback.engine.actor.script_notes import ScriptNoteEffect
from callback.engine.actor.shape import resolve_shape
from callback.engine.actor.studios import OPENING_MARKETING_COEF, STUDIOS, StreamingBid, marketing_share_for, quality_adjusted_bids
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
)
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp

SceneChoice = dict[str, str]  # one of DIALS -> one of POSITIONS, per scene


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
    """
    palette = palette or generate_palette(role.genre, rng)

    if director_override is not None:
        director_skill, director_command, director_prestige = director_override
    else:
        # NPC director — the director career (Part 7) isn't modeled in this pass; sampled per
        # §7.3's own verification convention (attributes ~ N(58, 16)) rather than invented fresh.
        director_skill = clamp(rng.gauss(58, 16), 5, 100)
        director_command = clamp(rng.gauss(58, 16), 5, 100)
        director_prestige = clamp(rng.gauss(50, 20), 0, 100)

    prep_result = resolve_prep(prep_choice, state.attrs.resilience, is_biographical_or_period=(role.genre == "period"))
    fit = fit_score(state.attrs, state.persona, role, state.age)
    if script_note is not None:
        fit = clamp(fit + script_note.fit_delta, 0.0, 100.0)
    chemistry = clamp(rng.gauss(60, 18), 0, 100)

    perf_result = resolve_performance(
        state.attrs, fit, prep_result.prep, chemistry, director_command, director_skill, rng,
    )

    budget = contrast_budget(state.attrs.craft, director_command)
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

    # genre_demand_override lets a caller with real §9.3 GenreHeat (simulation/full_career.py,
    # which tracks it) feed the actual background-industry cycle in instead of this fallback
    # sample — kept here, not removed, so simulate_project stays usable standalone (verify.py's
    # checks, unit tests) without requiring a world/ import.
    genre_demand = genre_demand_override if genre_demand_override is not None else clamp(rng.gauss(55, 15), 0, 100)
    cast_star_power = clamp(rng.gauss(50, 20), 0, 100)
    script_quality = clamp(rng.gauss(60, 14), 0, 100)
    palette_aud_effect, palette_crit_effect = palette_reception_effect(palette, role.genre)
    palette_aud_effect += franchise_audience_bonus
    staleness = state.persona.staleness_penalty()

    if script_note is not None:
        script_quality = clamp(script_quality + script_note.script_quality_delta, 0.0, 100.0)
        palette_aud_effect += script_note.audience_delta
        palette_crit_effect += script_note.critic_delta

    studio = STUDIOS[role.studio]
    marketing_share = marketing_share_for(studio, role.budget_for_role)

    reception = resolve_reception(
        script_quality=script_quality,
        director_skill=director_skill,
        craft_contribution=craft_contribution,
        genre=role.genre,
        role_budget_millions=role.budget_for_role,
        director_prestige=director_prestige,
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
    if release_strategy is not None:
        if release_strategy == STREAMING and streaming_multiplier_override is None:
            # Quality (film_critic_score/audience_score, on `reception` above) is already resolved
            # — the sale happens after the movie has been made, and it shows: a bad film draws a
            # thinner, worse pool than a good one.
            bids = quality_adjusted_bids(
                role.budget_for_role, role.studio, reception.film_critic_score, reception.audience_score, rng,
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
        reception = apply_release_strategy(
            reception, release_strategy, rng, cast_star_power=cast_star_power,
            festival_tier_bonus=studio.festival_tier_bonus,
            marketing_share=marketing_share, rights_share=RIGHTS_SHARE + studio.rights_share_delta,
            streaming_multiplier=streaming_multiplier,
        )

    bw = {"lead": 1.0, "supporting": 0.55, "bit": 0.2, "extra": 0.0}[role.billing]
    heat_delta = delta_heat(bw, state.credits, role.budget_for_role, reception.roi, reception.audience_score)
    prestige_delta = delta_prestige(bw, state.credits, reception.film_critic_score, spotlight)
    affection_delta = delta_affection(bw, state.credits, role.budget_for_role, reception.audience_score)

    new_standing = state.standing.copy()
    new_standing.add("heat", heat_delta)
    new_standing.add("prestige", prestige_delta)
    new_standing.add("affection", affection_delta)

    new_persona = state.persona.update(role.genre, role.archetype, role.billing, reception.audience_score)
    new_attrs = state.attrs.with_deltas(craft=prep_result.craft_delta, resilience=prep_result.resilience_delta)
    new_recognition = state.recognition.add(spotlight) if role.billing in ("supporting", "bit") else state.recognition

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

    result = ProjectResult(
        role=role,
        cast_via="project",
        spotlight=spotlight,
        craft_contribution=craft_contribution,
        performance=perf_result.performance,
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
        heat_delta=heat_delta,
        prestige_delta=prestige_delta,
        affection_delta=affection_delta,
        npc_affinity_delta=npc_affinity_delta,
        favour_gain=orientation_effect.you_favour if orientation_effect is not None else 0.0,
        studio_id=role.studio,
    )
    return new_state, result


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
