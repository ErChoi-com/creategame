"""Integrates every system built so far into one playable state: the actor's core loop
(simulation/career.py) plus the Rolodex, Leverage, Life layer, Guild, and the background
industry's genre cycle — the full loop simulation/cli.py drives interactively.

Kept separate from simulation/career.py (which stays a tested, minimal actor-only loop) rather
than rewriting it in place — this module composes those tested pieces instead of duplicating them.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.actor.aging import apply_look_curve
from callback.engine.actor.offers import Role, is_offered_non_union, sample_role, utility
from callback.engine.actor.standing import AFFECTION_DECAY, HEAT_KEEP, NOTORIETY_DECAY, PRESTIGE_DECAY
from callback.engine.leverage.catalogue import LeverageState, new_leverage_state
from callback.engine.life.family import FamilyState
from callback.engine.life.health import HealthState
from callback.engine.life.money import MoneyState
from callback.engine.life.obituary import DeclinedRoleRecord, Obituary, generate_obituary
from callback.engine.life.state import LifeState, advance_year as advance_life_year
from callback.engine.rolodex.casting import resolve_declined_role
from callback.engine.rolodex.rolodex import Rolodex, new_rolodex, recompute_tracked, register_contact
from callback.engine.simulation.career import ActorState, ProjectResult, new_actor, simulate_project
from callback.engine.world.genre_cycle import accumulate_heat, decay_all
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand
from callback.engine.world.guild import GuildState, add_residual_stream
from callback.engine.world.guild import advance_year as advance_guild_year
from callback.engine.world.strikes import StrikeState, advance_grievance

# Known gap: actor/offers.py's non-union-substitution check (§4.0) already reads union_credits
# directly rather than going through world.guild.is_eligible() — the two are consistent (both use
# the 3-credit threshold) but not literally wired together. Full guild membership gating of which
# roles even appear is a follow-up, not attempted in this pass.

CONTACT_CHANCE_ON_PROJECT = 0.6  # a project's costar is drawn from your Rolodex this often


@dataclass(frozen=True)
class FullState:
    actor: ActorState
    rolodex: Rolodex
    leverage: LeverageState
    life: LifeState
    guild: GuildState
    strikes: StrikeState
    genre_heat: dict[str, float] = field(default_factory=dict)
    filmography: tuple[ProjectResult, ...] = ()
    declined: tuple[DeclinedRoleRecord, ...] = ()


def new_full_state(rng: random.Random, start_age: int = 22) -> FullState:
    return FullState(
        actor=new_actor(start_age),
        rolodex=recompute_tracked(new_rolodex(rng), current_year=0),
        leverage=new_leverage_state(),
        life=LifeState(health=HealthState(), family=FamilyState(), money=MoneyState()),
        guild=GuildState(),
        strikes=StrikeState(),
    )


def current_year(state: FullState) -> int:
    return state.actor.age  # a simple proxy — the CLI reports it as a calendar year offset


def offer_this_year(state: FullState, rng: random.Random) -> Role:
    role = sample_role(rng)
    if role.union and is_offered_non_union(state.actor.union_credits, rng):
        role = replace(role, union=False, budget_for_role=role.budget_for_role / 3.0)
    return role


def utility_for(state: FullState, role: Role) -> float:
    quote_value = state.actor.quote_value()
    return utility(state.actor.attrs, state.actor.persona, state.actor.standing, role, state.actor.age, quote_value)


def director_terms_for(rolodex: Rolodex, npc_id: str) -> tuple[float, float, float]:
    """A requested (Rolodex-tracked) director's own Standing, read as the three terms
    simulate_project's director_override wants — the same "no second stat block for NPCs"
    reuse §10.0 and director/skill.py's docstring already establish."""
    npc = rolodex.npcs[npc_id]
    if npc.standing is None:
        return 55.0, 55.0, 50.0
    return npc.standing["prestige"], npc.standing["heat"], npc.standing["prestige"]


def accept_and_play(
    state: FullState,
    role: Role,
    prep_choice: str,
    scene_choices: tuple[dict[str, str], dict[str, str], dict[str, str]],
    rng: random.Random,
    release_strategy: str | None = None,
    script_note=None,
    orientation_npc_id: str | None = None,
    orientation_effect=None,
    requested_director_npc_id: str | None = None,
) -> tuple[FullState, ProjectResult]:
    """script_note: actor.script_notes.ScriptNoteEffect, from a Session-level script-approval
    push. orientation_npc_id + orientation_effect: the tracked co-star this project centres on
    and positions.generosity()/upstaging()'s resulting ModifierResult. requested_director_npc_id:
    a tracked Rolodex director pulled onto the project in place of the usual random NPC sample —
    the caller (Session) is responsible for having already spent the favour this costs."""
    # §9.3's GenreHeat, accumulated from every resolved film (yours and the background
    # industry's, §10.0) feeds real GenreDemand back into this project's own box office —
    # a hot genre isn't just trades-digest flavor, it changes what your film actually earns.
    demand = world_genre_demand(state.genre_heat, role.genre)
    director_override = (
        director_terms_for(state.rolodex, requested_director_npc_id)
        if requested_director_npc_id is not None else None
    )
    new_actor_state, result = simulate_project(
        state.actor, role, prep_choice, scene_choices, rng,
        genre_demand_override=demand, release_strategy=release_strategy,
        script_note=script_note, orientation_effect=orientation_effect, director_override=director_override,
    )

    rolodex = state.rolodex
    costar_id = orientation_npc_id
    if costar_id is None and rng.random() < CONTACT_CHANCE_ON_PROJECT and rolodex.tracked_ids:
        costar_id = rng.choice(rolodex.tracked_ids)
    if costar_id is not None:
        rolodex = register_contact(rolodex, costar_id, current_year(state), shared_project=True)
        if result.npc_affinity_delta:
            from callback.engine.rolodex.rolodex import apply_affinity_grudge
            rolodex = apply_affinity_grudge(rolodex, costar_id, affinity_delta=result.npc_affinity_delta)

    leverage = state.leverage
    if result.favour_gain and costar_id is not None:
        leverage = replace(leverage, favours=leverage.favours.credit(costar_id, int(result.favour_gain)))

    guild = add_residual_stream(state.guild, result.roi, role.budget_for_role)
    genre_heat = accumulate_heat(state.genre_heat, role.genre, result.roi)

    new_state = replace(state, actor=new_actor_state, rolodex=rolodex, leverage=leverage, guild=guild,
                         genre_heat=genre_heat, filmography=(*state.filmography, result))
    return new_state, result


def decline_and_resolve(state: FullState, role: Role, rng: random.Random) -> FullState:
    demand = world_genre_demand(state.genre_heat, role.genre)
    # Blacklist/Recommend (design/part-06 §6.6) were previously implemented in three places —
    # casting.py accepted them, catalogue.py stored them — but never actually connected: this
    # call is where that connection was missing. Without it, blacklisting or recommending
    # someone had zero effect on who ever got cast.
    rolodex, cast_result = resolve_declined_role(
        role, state.rolodex, current_year(state), rng, genre_demand_override=demand,
        blacklisted=state.leverage.blacklisted, recommended=state.leverage.recommended,
    )
    genre_heat = accumulate_heat(state.genre_heat, role.genre, cast_result.reception.roi)
    declined = (*state.declined, DeclinedRoleRecord(role_genre=role.genre, year=current_year(state), result=cast_result))
    return replace(state, rolodex=rolodex, genre_heat=genre_heat, declined=declined)


def advance_between_years(state: FullState, rng: random.Random, worked_this_year: bool, billing: str | None = None) -> FullState:
    """End-of-year housekeeping. simulate_project() (called from accept_and_play) resolves a
    single project's Standing *deltas* but — unlike simulation/career.py's own simulate_year —
    does not age the actor or apply Standing's yearly decay; those are exactly this function's
    job, run once per year regardless of whether a project was played. Also: life-layer advance,
    guild bookkeeping, genre-heat decay, Rolodex re-ranking, strikes."""
    gross_income = state.actor.quote_value() if worked_this_year else 0.0
    life, life_deltas = advance_life_year(state.life, rng, gross_income, worked_this_year, age=state.actor.age)

    standing = state.actor.standing.copy()
    for meter, delta in life_deltas.items():
        if meter in standing.meters:
            standing.add(meter, delta)
    heat_tier = billing if (worked_this_year and billing) else "idle"
    standing.decay({
        "heat": HEAT_KEEP.get(heat_tier, HEAT_KEEP["idle"]),
        "prestige": PRESTIGE_DECAY,
        "affection": AFFECTION_DECAY,
        "notoriety": NOTORIETY_DECAY,
    })

    new_age = state.actor.age + 1
    aged_attrs = state.actor.attrs.age_decay(new_age)
    aged_attrs = replace(aged_attrs, look=apply_look_curve(aged_attrs.look, new_age)).clamped()
    # §11.4's resilience floor (partner, children, close friends) was computed but never
    # actually applied anywhere — the whole point of a floor is that Resilience can't be pushed
    # below it by everything else this function does.
    floor = life.family.resilience_floor()
    if aged_attrs.resilience < floor:
        aged_attrs = replace(aged_attrs, resilience=floor).clamped()
    actor = replace(state.actor, standing=standing, age=new_age, attrs=aged_attrs)

    guild = advance_guild_year(state.guild, gross_income)
    genre_heat = decay_all(state.genre_heat)
    rolodex = recompute_tracked(state.rolodex, current_year(state))
    strikes = advance_grievance(state.strikes, rng)

    return replace(state, actor=actor, life=life, guild=guild, genre_heat=genre_heat,
                   rolodex=rolodex, strikes=strikes)


def obituary(state: FullState) -> Obituary:
    return generate_obituary(list(state.filmography), list(state.declined), state.rolodex)
