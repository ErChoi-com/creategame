"""design/part-11-the-life.md §11.8 — the obituary: a generated retrospective covering every
career the player had. Pure presentation-layer aggregation over data other modules already
produced — no new formulas, just the read-back §11.8 promises.

life/ sits below simulation/ in this package's one-way dependency order (core -> actor -> every
other package -> simulation composes all of them), so this module reads a filmography structurally
(via ProjectLike below) instead of importing simulation.career.ProjectResult by name — the same
"plain data across a boundary" discipline simulation.session.Session enforces on its own player
-facing edge, just applied to this internal one. Any caller's real ProjectResult already satisfies
ProjectLike without either module needing to know about the other's concrete type.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from callback.engine.rolodex.casting import CastingResult
from callback.engine.rolodex.npc import LEGACY_STATE, LOYAL, SEVERED
from callback.engine.rolodex.rolodex import Rolodex


class ProjectLike(Protocol):
    performance: float
    film_critic_score: float


@dataclass(frozen=True)
class DeclinedRoleRecord:
    """§10.0's mechanism read back: a role you didn't take, and what became of it."""
    role_genre: str
    year: int
    result: CastingResult


@dataclass(frozen=True)
class Obituary:
    filmography: tuple[ProjectLike, ...]
    declined: tuple[DeclinedRoleRecord, ...]
    collaborators: tuple[tuple[str, int], ...]  # (npc_id, shared_projects), most-frequent first
    kept: tuple[str, ...]  # npc_ids that ended Loyal or Legacy
    lost: tuple[str, ...]  # npc_ids that ended Severed
    best_hidden_performance: ProjectLike | None  # "brilliant and nobody knew"


def generate_obituary(
    filmography: list[ProjectLike],
    declined: list[DeclinedRoleRecord],
    rolodex: Rolodex,
) -> Obituary:
    collaborators = sorted(
        ((n.npc_id, n.shared_projects) for n in rolodex.npcs.values() if n.shared_projects > 0),
        key=lambda pair: pair[1], reverse=True,
    )
    kept = tuple(n.npc_id for n in rolodex.npcs.values() if n.relationship_state in (LOYAL, LEGACY_STATE))
    lost = tuple(n.npc_id for n in rolodex.npcs.values() if n.relationship_state == SEVERED)

    best_hidden = None
    if filmography:
        # "brilliant and nobody knew" — the largest gap between your performance and how the
        # film (and thus you, publicly) was received.
        best_hidden = max(filmography, key=lambda r: r.performance - r.film_critic_score)

    return Obituary(
        filmography=tuple(filmography),
        declined=tuple(declined),
        collaborators=tuple(collaborators),
        kept=kept,
        lost=lost,
        best_hidden_performance=best_hidden,
    )
