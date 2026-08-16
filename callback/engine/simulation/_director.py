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
_franchises.py) or offer a release-strategy choice — every directed film is a straight Wide
release. Both are real, bounded follow-ups, not attempted here.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

from callback.engine.actor.reception import RIGHTS_SHARE, ReceptionResult, resolve_reception
from callback.engine.actor.release import STREAMING_BUYOUT_MULTIPLIER, WIDE, apply_release_strategy
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
)
from callback.engine.actor.studios import OPENING_MARKETING_COEF, marketing_share_for, pick_studio
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp
from callback.engine.director.attributes import DirectorAttributes
from callback.engine.director.development import DevProject, apply_action, advance_quarter, package_strength
from callback.engine.director.edit import steered_post_luck
from callback.engine.director.skill import director_skill

DIRECTOR_UNLOCK_PRESTIGE = 55.0  # real weight in the room, not a rubber stamp
DIRECTOR_UNLOCK_MIN_CREDITS = 5

ATTACH_STAR_BANKABILITY_GAIN = 25.0
REWRITE_SCRIPT_QUALITY_GAIN = 6.0
NEW_PROJECT_SCRIPT_QUALITY_MEAN = 58.0
NEW_PROJECT_SCRIPT_QUALITY_SD = 14.0
PASSION_PROJECT_STAR_THRESHOLD = 10.0  # under this attached-star bankability, it reads as a passion project


@dataclass(frozen=True)
class DirectorState:
    attrs: DirectorAttributes = DirectorAttributes()
    standing: StandingModel = None  # set to new_standing_model() by new_director_state()
    credits: int = 0
    current_project: DevProject | None = None
    current_genre: str | None = None
    current_true_script_quality: float = 0.0


def new_director_state() -> DirectorState:
    return DirectorState(standing=new_standing_model())


def start_development(state: DirectorState, genre: str, budget_ask: float, rng: random.Random) -> DirectorState:
    project = DevProject(script_id=f"d_{rng.randrange(10**6):06d}", budget_ask=budget_ask)
    quality = clamp(rng.gauss(NEW_PROJECT_SCRIPT_QUALITY_MEAN, NEW_PROJECT_SCRIPT_QUALITY_SD), 0.0, 100.0)
    return replace(state, current_project=project, current_genre=genre, current_true_script_quality=quality)


def _resolve_directed_film(
    state: DirectorState, project: DevProject, genre: str, genre_demand: float, rng: random.Random,
) -> ReceptionResult:
    studio = pick_studio(project.budget_ask, rng)
    marketing_share = marketing_share_for(studio, project.budget_ask)

    cast_star_power = clamp(30.0 + 0.5 * project.attached_star_bankability + rng.gauss(0.0, 10.0), 0.0, 100.0)
    ensemble = clamp(rng.gauss(55.0 + 0.10 * state.attrs.command, 15.0), 0.0, 100.0)
    passion_project = project.attached_star_bankability < PASSION_PROJECT_STAR_THRESHOLD
    skill = director_skill(state.attrs, passion_project, rng)
    steered_luck = steered_post_luck(state.attrs.craft, state.attrs.efficiency, rng)

    reception = resolve_reception(
        script_quality=state.current_true_script_quality,
        director_skill=skill,
        ensemble=ensemble,
        genre=genre,
        role_budget_millions=project.budget_ask,
        director_prestige=state.standing["prestige"],
        staleness_penalty=0.0,
        cast_star_power=cast_star_power,
        genre_demand=genre_demand,
        rng=rng,
        marketing_share=marketing_share,
        rights_share=RIGHTS_SHARE + studio.rights_share_delta,
        opening_marketing_coef=OPENING_MARKETING_COEF,
        post_luck_override=steered_luck,
    )
    return apply_release_strategy(
        reception, WIDE, rng, cast_star_power=cast_star_power,
        marketing_share=marketing_share, rights_share=RIGHTS_SHARE + studio.rights_share_delta,
        streaming_multiplier=STREAMING_BUYOUT_MULTIPLIER + studio.streaming_multiplier_delta,
    )


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
    reception = _resolve_directed_film(working_state, new_project, genre, genre_demand, rng)

    billing_weight = 1.0  # you're always the whole show on your own film
    standing = state.standing.copy()
    standing.add("heat", delta_heat(billing_weight, state.credits, project.budget_ask, reception.roi, reception.audience_score))
    standing.add("prestige", delta_prestige(billing_weight, state.credits, reception.film_critic_score, reception.film_critic_score))
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
