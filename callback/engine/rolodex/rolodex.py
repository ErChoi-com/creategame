"""design/part-04-the-actor.md §4.12 — the Rolodex container: a background cast of ~40 NPCs, with
eight dynamically tracked in full detail by weighted contact, grudge, and stakes.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.rolodex.npc import NPC, RIVAL, generate_npc

BACKGROUND_SIZE = 40
TRACKED_SIZE = 8
RIVAL_COLLISION_THRESHOLD = 3

# tracking_score weights — §4.12: "chosen dynamically: whoever you've worked with most, plus
# anyone currently holding a grudge or owing a favour."
CONTACT_WEIGHT = 1.0
RECENCY_WEIGHT = 8.0  # a bonus for contact within the last few years, decaying with time
GRUDGE_WEIGHT = 1.2
STAKES_WEIGHT = 0.6  # abs(affinity) as a proxy for "this relationship matters, good or bad"


@dataclass(frozen=True)
class Rolodex:
    npcs: dict[str, NPC] = field(default_factory=dict)
    tracked_ids: tuple[str, ...] = ()
    collision_counts: dict[str, int] = field(default_factory=dict)

    def tracked(self) -> tuple[NPC, ...]:
        return tuple(self.npcs[i] for i in self.tracked_ids if i in self.npcs)

    def background(self) -> tuple[NPC, ...]:
        return tuple(n for i, n in self.npcs.items() if i not in self.tracked_ids)


def new_rolodex(rng: random.Random, size: int = BACKGROUND_SIZE) -> Rolodex:
    npcs = {}
    for i in range(size):
        npc_id = f"n_{i:03d}"
        npcs[npc_id] = generate_npc(rng, npc_id)
    return Rolodex(npcs=npcs)


def _tracking_score(npc: NPC, current_year: int) -> float:
    recency = 0.0
    if npc.last_contact_year is not None:
        years_since = max(0, current_year - npc.last_contact_year)
        recency = RECENCY_WEIGHT * max(0.0, 1.0 - years_since / 6.0)
    return (
        CONTACT_WEIGHT * npc.shared_projects
        + recency
        + GRUDGE_WEIGHT * npc.grudge
        + STAKES_WEIGHT * abs(npc.affinity)
    )


def recompute_tracked(rolodex: Rolodex, current_year: int) -> Rolodex:
    """Re-rank the background cast and pick the top TRACKED_SIZE by tracking_score. Already-
    tracked NPCs whose state is Loyal/Legacy are pinned (they don't fall out just because a
    newer contact scored marginally higher — §4.12's own "the rest are real but quiet" framing
    implies the eight aren't recomputed so aggressively they feel arbitrary)."""
    pinned = [i for i in rolodex.tracked_ids if rolodex.npcs.get(i) and rolodex.npcs[i].relationship_state in ("loyal", "legacy")]
    remaining_slots = TRACKED_SIZE - len(pinned)
    candidates = [n for i, n in rolodex.npcs.items() if i not in pinned]
    ranked = sorted(candidates, key=lambda n: _tracking_score(n, current_year), reverse=True)
    new_tracked = tuple(pinned + [n.npc_id for n in ranked[:remaining_slots]])
    return replace(rolodex, tracked_ids=new_tracked)


def register_contact(rolodex: Rolodex, npc_id: str, year: int, shared_project: bool = False) -> Rolodex:
    npc = rolodex.npcs[npc_id]
    updated = replace(npc, last_contact_year=year, shared_projects=npc.shared_projects + (1 if shared_project else 0))
    updated = replace(updated, relationship_state=updated.state_after_update()).clamped()
    npcs = dict(rolodex.npcs)
    npcs[npc_id] = updated
    return replace(rolodex, npcs=npcs)


def apply_affinity_grudge(rolodex: Rolodex, npc_id: str, affinity_delta: float = 0.0, grudge_delta: float = 0.0) -> Rolodex:
    npc = rolodex.npcs[npc_id]
    updated = replace(npc, affinity=npc.affinity + affinity_delta, grudge=npc.grudge + grudge_delta).clamped()
    updated = replace(updated, relationship_state=updated.state_after_update())
    npcs = dict(rolodex.npcs)
    npcs[npc_id] = updated
    return replace(rolodex, npcs=npcs)


def register_collision(rolodex: Rolodex, npc_id: str) -> Rolodex:
    """§10.0 — a rival "falls out of the ranking on its own" from repeated collision: the same
    category twice, up for the same part three times, one franchise between you. This is the
    generic hook other systems (awards.py, offers.py) call when such a collision happens."""
    counts = dict(rolodex.collision_counts)
    counts[npc_id] = counts.get(npc_id, 0) + 1
    npc = rolodex.npcs[npc_id]
    if counts[npc_id] >= RIVAL_COLLISION_THRESHOLD and npc.relationship_state not in ("loyal", "ally"):
        npcs = dict(rolodex.npcs)
        npcs[npc_id] = replace(npc, relationship_state=RIVAL)
        return replace(rolodex, npcs=npcs, collision_counts=counts)
    return replace(rolodex, collision_counts=counts)


def rivals(rolodex: Rolodex) -> tuple[NPC, ...]:
    return tuple(n for n in rolodex.tracked() if n.relationship_state == RIVAL)
