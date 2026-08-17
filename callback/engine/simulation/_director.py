"""Session-level orchestration of the director career (director/) — fused into the same
FullState/Session as the actor's, rather than a second, parallel Session. Development hell
(director/development.py), a director's own Craft/Efficiency steering the edit
(director/edit.py), and their own Standing (the same core.meters.StandingModel actor/standing.py
already configures — one spine, per design/part-03 §3.3) share the actor's calendar: a year spent
developing or shooting a directed project is a year not spent acting, and vice versa, but Standing
decay, Life, the Guild, and Rolodex re-ranking all still run once a year regardless of which track
you worked, through full_career.advance_between_years exactly as they already do for acting.

Explicitly out of scope for this pass, same as the acting-only build originally was for several
systems: a directed film doesn't participate in the franchise/sequel system (simulation/
_franchises.py). A real, bounded follow-up, not attempted here.

Three actor-side mechanics are ported onto the director track, reusing the same underlying
formulas rather than inventing parallel ones: script notes (a director's own three-of-four —
clarity/ambiguity/whole-film; "your part" doesn't apply, they have no part), a release-strategy
request, and a marketing-push request. The latter two use studios.decide_release_strategy()/
decide_marketing_spend() exactly as the actor path does, but with director_influence_on_studio_
decision() in place of the actor curve — a director asking for their own film starts from a real,
higher floor and climbs faster, though never past the same ceiling an A-list actor already has.
No persistent director-studio relationship is tracked yet (unlike studio_relations on the acting
side) — DIRECTOR_STUDIO_TRUST is a flat, neutral stand-in until that's built out.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.actor.reception import RIGHTS_SHARE, ReceptionResult, resolve_reception
from callback.engine.actor.release import RELEASE_STRATEGIES, STREAMING_BUYOUT_MULTIPLIER, WIDE, apply_release_strategy
from callback.engine.core.script_notes import DIRECTOR_SCRIPT_NOTE_OPTIONS, ScriptNoteEffect, apply_script_note
from callback.engine.actor.standing import (
    AFFECTION_DECAY,
    HEAT_KEEP,
    NOTORIETY_DECAY,
    PRESTIGE_DECAY,
    delta_affection,
    delta_heat,
    delta_prestige,
    new_standing_model,
    standing_score,
    star_power,
)
from callback.engine.actor.studios import (
    OPENING_MARKETING_COEF,
    decide_marketing_spend,
    decide_release_strategy,
    director_influence_on_studio_decision,
    marketing_share_for,
    pick_studio,
)
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp
from callback.engine.director.attributes import DirectorAttributes
from callback.engine.director.development import DevProject, apply_action, advance_quarter, package_strength
from callback.engine.director.edit import steered_post_luck
from callback.engine.director.skill import director_skill

ATTACH_STAR_BANKABILITY_GAIN = 25.0
REWRITE_SCRIPT_QUALITY_GAIN = 6.0
NEW_PROJECT_SCRIPT_QUALITY_MEAN = 58.0
NEW_PROJECT_SCRIPT_QUALITY_SD = 14.0
PASSION_PROJECT_STAR_THRESHOLD = 10.0  # under this attached-star bankability, it reads as a passion project
DIRECTOR_STUDIO_TRUST = 50.0  # neutral baseline — no persistent director-studio relationship tracked yet


@dataclass(frozen=True)
class DirectorState:
    attrs: DirectorAttributes = DirectorAttributes()
    standing: StandingModel = None  # set to new_standing_model() by new_director_state()
    credits: int = 0
    current_project: DevProject | None = None
    current_genre: str | None = None
    current_true_script_quality: float = 0.0
    pending_script_note: ScriptNoteEffect = field(default_factory=ScriptNoteEffect)
    pending_release_request: str | None = None
    pending_marketing_push: bool = False


def new_director_state() -> DirectorState:
    return DirectorState(standing=new_standing_model())


def start_development(state: DirectorState, genre: str, budget_ask: float, rng: random.Random) -> DirectorState:
    project = DevProject(script_id=f"d_{rng.randrange(10**6):06d}", budget_ask=budget_ask)
    quality = clamp(rng.gauss(NEW_PROJECT_SCRIPT_QUALITY_MEAN, NEW_PROJECT_SCRIPT_QUALITY_SD), 0.0, 100.0)
    return replace(
        state, current_project=project, current_genre=genre, current_true_script_quality=quality,
        pending_script_note=ScriptNoteEffect(), pending_release_request=None, pending_marketing_push=False,
    )


def choose_director_script_note(state: DirectorState, choice: str) -> DirectorState:
    """A director's own notes pass — see DIRECTOR_SCRIPT_NOTE_OPTIONS for the three real choices.
    script_quality_delta applies immediately (same as a rewrite); the audience/critic deltas are
    held until the film actually resolves (see _resolve_directed_film)."""
    if choice not in DIRECTOR_SCRIPT_NOTE_OPTIONS:
        return state
    effect = apply_script_note(choice)
    new_quality = clamp(state.current_true_script_quality + effect.script_quality_delta, 0.0, 100.0)
    return replace(state, current_true_script_quality=new_quality, pending_script_note=effect)


def request_director_release(state: DirectorState, strategy: str) -> DirectorState:
    """A request, not a command — resolved the same way an actor's is, at greenlight time, via
    decide_release_strategy() and director_influence_on_studio_decision()."""
    if strategy not in RELEASE_STRATEGIES:
        return state
    return replace(state, pending_release_request=strategy)


def request_director_marketing_push(state: DirectorState) -> DirectorState:
    return replace(state, pending_marketing_push=True)


def _resolve_directed_film(
    state: DirectorState, project: DevProject, genre: str, genre_demand: float, rng: random.Random,
) -> tuple[ReceptionResult, str, bool]:
    """Returns (reception, actual_release_strategy, marketing_push_honored)."""
    studio = pick_studio(project.budget_ask, rng)
    director_importance = standing_score(state.standing)

    marketing = decide_marketing_spend(
        studio, project.budget_ask, DIRECTOR_STUDIO_TRUST, star_power(state.standing), genre_demand,
        is_franchise_or_adaptation=False, requested_push=state.pending_marketing_push, rng=rng,
        influence_fn=director_influence_on_studio_decision,
    )
    marketing_share = marketing.marketing_share

    cast_star_power = clamp(30.0 + 0.5 * project.attached_star_bankability + rng.gauss(0.0, 10.0), 0.0, 100.0)
    craft_contribution = clamp(rng.gauss(55.0 + 0.10 * state.attrs.command, 15.0), 0.0, 100.0)
    passion_project = project.attached_star_bankability < PASSION_PROJECT_STAR_THRESHOLD
    skill = director_skill(state.attrs, passion_project, rng)
    steered_luck = steered_post_luck(state.attrs.craft, state.attrs.efficiency, rng)

    reception = resolve_reception(
        script_quality=state.current_true_script_quality,
        director_skill=skill,
        craft_contribution=craft_contribution,
        genre=genre,
        role_budget_millions=project.budget_ask,
        director_prestige=state.standing["prestige"],
        staleness_penalty=0.0,
        cast_star_power=cast_star_power,
        genre_demand=genre_demand,
        rng=rng,
        palette_audience_effect=state.pending_script_note.audience_delta,
        palette_critic_effect=state.pending_script_note.critic_delta,
        marketing_share=marketing_share,
        rights_share=RIGHTS_SHARE + studio.rights_share_delta,
        opening_marketing_coef=OPENING_MARKETING_COEF,
        post_luck_override=steered_luck,
    )

    actual_strategy = decide_release_strategy(
        studio, state.pending_release_request or WIDE, DIRECTOR_STUDIO_TRUST, director_importance, rng,
        influence_fn=director_influence_on_studio_decision,
    )
    resolved = apply_release_strategy(
        reception, actual_strategy, rng, cast_star_power=cast_star_power,
        festival_tier_bonus=studio.festival_tier_bonus,
        marketing_share=marketing_share, rights_share=RIGHTS_SHARE + studio.rights_share_delta,
        streaming_multiplier=STREAMING_BUYOUT_MULTIPLIER + studio.streaming_multiplier_delta,
    )
    return resolved, actual_strategy, marketing.push_honored


def apply_dev_action_and_advance(state: DirectorState, action: str, genre_demand: float, rng: random.Random) -> tuple[DirectorState, dict]:
    """One year's directing work: apply the chosen development action, attempt a greenlight, and
    resolve the film immediately if it lands. Mirrors simulate_project's one-project-a-year cadence
    on the acting side."""
    project = state.current_project
    genre = state.current_genre
    true_quality = state.current_true_script_quality

    if action == "attach_star":
        project = replace(project, attached_star_bankability=clamp(
            project.attached_star_bankability + ATTACH_STAR_BANKABILITY_GAIN, 0.0, 100.0))
    if action == "rewrite":
        true_quality = clamp(true_quality + REWRITE_SCRIPT_QUALITY_GAIN, 0.0, 100.0)

    project = apply_action(project, action)

    if project.frozen:
        new_state = replace(state, current_project=project, current_true_script_quality=true_quality)
        return new_state, {"greenlit": False, "dead": False, "frozen": True, "momentum": round(project.momentum, 2)}

    pkg_strength = package_strength(project.attached_star_bankability, true_quality, standing_score(state.standing))
    new_project, greenlit = advance_quarter(project, pkg_strength, rng)

    if not greenlit:
        if new_project.dead:
            cleared = replace(state, current_project=None, current_genre=None, current_true_script_quality=0.0)
            return cleared, {"greenlit": False, "dead": True, "frozen": False, "momentum": round(new_project.momentum, 2)}
        updated = replace(state, current_project=new_project, current_true_script_quality=true_quality)
        return updated, {"greenlit": False, "dead": False, "frozen": False, "momentum": round(new_project.momentum, 2)}

    working_state = replace(state, current_project=new_project, current_true_script_quality=true_quality)
    reception, actual_strategy, push_honored = _resolve_directed_film(working_state, new_project, genre, genre_demand, rng)

    billing_weight = 1.0  # you're always the whole show on your own film
    standing = state.standing.copy()
    standing.add("heat", delta_heat(billing_weight, state.credits, project.budget_ask, reception.roi, reception.audience_score))
    # delta_prestige wants two genuinely independent signals — what critics thought
    # (film_critic_score, centred on 57) and a separate visibility term (your_spotlight, centred
    # on 54). A director has no on-screen Spotlight of their own; audience_score is the real
    # analog (how much the audience actually embraced the film), not a second read of the same
    # critic number — reusing film_critic_score for both args here used to double-weight critical
    # reception (0.11+0.26 combined) while the film's actual audience reach never factored in.
    standing.add("prestige", delta_prestige(billing_weight, state.credits, reception.film_critic_score, reception.audience_score))
    standing.add("affection", delta_affection(billing_weight, state.credits, project.budget_ask, reception.audience_score))

    resolved_state = DirectorState(
        attrs=state.attrs, standing=standing, credits=state.credits + 1,
        current_project=None, current_genre=None, current_true_script_quality=0.0,
    )
    info = {
        "greenlit": True, "dead": False, "frozen": False, "momentum": 1.0,
        "genre": genre, "budget": project.budget_ask,
        "critic_score": round(reception.film_critic_score),
        "film_critic_score": reception.film_critic_score,
        "audience_score": reception.audience_score,
        "roi": round(reception.roi, 2),
        "gross_millions": round(reception.gross, 1),
        "marketing_millions": round(reception.marketing, 1),
        "requested_release": state.pending_release_request,
        "release_strategy": actual_strategy,
        "release_overruled": state.pending_release_request is not None and state.pending_release_request != actual_strategy,
        "marketing_push_requested": state.pending_marketing_push,
        "marketing_push_honored": push_honored,
    }
    return resolved_state, info


def decay_director_standing(state: DirectorState) -> DirectorState:
    """Same yearly upkeep actor/standing.py's own decay does — run once a year through
    full_career.advance_between_years regardless of whether the year was spent directing."""
    standing = state.standing.copy()
    standing.decay({
        "heat": HEAT_KEEP["idle"],  # a year in development hell isn't a released credit yet
        "prestige": PRESTIGE_DECAY,
        "affection": AFFECTION_DECAY,
        "notoriety": NOTORIETY_DECAY,
    })
    return replace(state, standing=standing)
