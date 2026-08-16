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


def accept_and_play(
    state: FullState,
    role: Role,
    prep_choice: str,
    scene_choices: tuple[dict[str, str], dict[str, str], dict[str, str]],
    rng: random.Random,
    release_strategy: str | None = None,
) -> tuple[FullState, ProjectResult]:
    # §9.3's GenreHeat, accumulated from every resolved film (yours and the background
    # industry's, §10.0) feeds real GenreDemand back into this project's own box office —
    # a hot genre isn't just trades-digest flavor, it changes what your film actually earns.
    demand = world_genre_demand(state.genre_heat, role.genre)
    new_actor_state, result = simulate_project(
        state.actor, role, prep_choice, scene_choices, rng,
        genre_demand_override=demand, release_strategy=release_strategy,
    )

    rolodex = state.rolodex
    if rng.random() < CONTACT_CHANCE_ON_PROJECT and rolodex.tracked_ids:
        npc_id = rng.choice(rolodex.tracked_ids)
        rolodex = register_contact(rolodex, npc_id, current_year(state), shared_project=True)

    guild = add_residual_stream(state.guild, result.roi, role.budget_for_role)
    genre_heat = accumulate_heat(state.genre_heat, role.genre, result.roi)

    new_state = replace(state, actor=new_actor_state, rolodex=rolodex, guild=guild, genre_heat=genre_heat,
                         filmography=(*state.filmography, result))
    return new_state, result


def decline_and_resolve(state: FullState, role: Role, rng: random.Random) -> FullState:
    demand = world_genre_demand(state.genre_heat, role.genre)
    rolodex, cast_result = resolve_declined_role(role, state.rolodex, current_year(state), rng, genre_demand_override=demand)
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
    life, life_deltas = advance_life_year(state.life, rng, gross_income, worked_this_year)

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
    actor = replace(state.actor, standing=standing, age=new_age, attrs=aged_attrs)

    guild = advance_guild_year(state.guild, gross_income)
    genre_heat = decay_all(state.genre_heat)
    rolodex = recompute_tracked(state.rolodex, current_year(state))
    strikes = advance_grievance(state.strikes, rng)

    return replace(state, actor=actor, life=life, guild=guild, genre_heat=genre_heat,
                   rolodex=rolodex, strikes=strikes)


def obituary(state: FullState) -> Obituary:
    return generate_obituary(list(state.filmography), list(state.declined), state.rolodex)
