"""design/part-10-the-world.md §10.0 — CastingResolution: a role the player doesn't take isn't
removed from the game, it's cast with someone else, and that film gets made through the same
formulas as any of the player's.

Full per-project simulation (a real Performance + reception) is worth running for tracked Rolodex
members; everyone else resolves in aggregate through the same reception.resolve_reception formula
with sampled inputs standing in for a full ActorState — §10.0's own scoping rule, applied here.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

from callback.engine.actor.offers import Role
from callback.engine.actor.reception import ReceptionResult, resolve_reception
from callback.engine.core.util import clamp
from callback.engine.rolodex.npc import NPC
from callback.engine.rolodex.rolodex import Rolodex, register_collision, register_contact

BACKGROUND_CANDIDATE_WEIGHT_MEAN = 40.0
BACKGROUND_CANDIDATE_WEIGHT_SD = 20.0
TRACKED_CANDIDATE_STANDING_WEIGHT = {"heat": 0.35, "prestige": 0.35, "affection": 0.20, "notoriety": -0.10}


@dataclass(frozen=True)
class CastingResult:
    filled_by: str  # npc_id, or "background"
    reception: ReceptionResult


def _candidate_weight(npc: NPC | None, role: Role) -> float:
    if npc is not None and npc.standing is not None:
        return max(1.0, npc.standing.weighted_score(TRACKED_CANDIDATE_STANDING_WEIGHT))
    return 1.0  # background candidates are weighted via their own sampled draw at pick time


def resolve_declined_role(
    role: Role,
    rolodex: Rolodex,
    year: int,
    rng: random.Random,
    blacklisted: frozenset[str] = frozenset(),
    recommended: dict[str, float] | None = None,
) -> tuple[Rolodex, CastingResult]:
    """weightedPick over Rolodex members (of a compatible type) union generated background
    actors, weight = Utility(candidate, role) — a simplified reading of §4.4's own Utility for
    NPCs we don't hold full actor state for (their gate/persona/attribute detail isn't tracked;
    their Standing-derived weight stands in for it).

    blacklisted/recommended (design/part-06 §6.6's "Blacklist someone"/"Recommend someone") shift
    a named candidate's weight down to near-exclusion or up, respectively — the exact mechanism
    those two leverage verbs move (leverage/catalogue.py calls this with the player's choices)."""
    recommended = recommended or {}
    eligible = [n for n in rolodex.npcs.values() if n.npc_type == "costar" and n.active]
    candidates: list[tuple[str | None, float]] = []
    for n in eligible:
        weight = _candidate_weight(n, role)
        if n.npc_id in blacklisted:
            weight *= 0.02
        if n.npc_id in recommended:
            weight *= (1.0 + recommended[n.npc_id])
        candidates.append((n.npc_id, weight))
    n_background = max(3, 10 - len(candidates))
    for _ in range(n_background):
        candidates.append((None, max(1.0, rng.gauss(BACKGROUND_CANDIDATE_WEIGHT_MEAN, BACKGROUND_CANDIDATE_WEIGHT_SD))))

    ids, weights = zip(*candidates)
    winner_id = rng.choices(ids, weights=weights)[0]

    if winner_id is not None:
        rolodex = register_contact(rolodex, winner_id, year, shared_project=False)
        rolodex = register_collision(rolodex, winner_id)
        winner = rolodex.npcs[winner_id]
        director_prestige = winner.standing["prestige"] if winner.standing else clamp(rng.gauss(45, 20), 0, 100)
        director_skill = clamp(rng.gauss(55, 16), 5, 100)
        cast_star_power = winner.standing["heat"] if winner.standing else clamp(rng.gauss(40, 20), 0, 100)
    else:
        director_prestige = clamp(rng.gauss(45, 20), 0, 100)
        director_skill = clamp(rng.gauss(55, 16), 5, 100)
        cast_star_power = clamp(rng.gauss(40, 20), 0, 100)

    ensemble = clamp(rng.gauss(58, 16), 0, 100)
    script_quality = clamp(rng.gauss(58, 15), 0, 100)
    genre_demand = clamp(rng.gauss(55, 15), 0, 100)

    reception = resolve_reception(
        script_quality=script_quality,
        director_skill=director_skill,
        ensemble=ensemble,
        genre=role.genre,
        role_budget_millions=role.budget_for_role,
        director_prestige=director_prestige,
        staleness_penalty=0.0,
        cast_star_power=cast_star_power,
        genre_demand=genre_demand,
        rng=rng,
    )

    if winner_id is not None and winner_id in rolodex.npcs:
        winner = rolodex.npcs[winner_id]
        if winner.standing is not None:
            new_standing = winner.standing.copy()
            new_standing.add("heat", 0.15 * reception.roi * 10)
            new_standing.add("prestige", 0.1 * (reception.film_critic_score - 50))
            npcs = dict(rolodex.npcs)
            npcs[winner_id] = replace(winner, standing=new_standing)
            rolodex = replace(rolodex, npcs=npcs)

    return rolodex, CastingResult(filled_by=winner_id or "background", reception=reception)
