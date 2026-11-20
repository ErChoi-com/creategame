"""design/part-10-the-world.md §10.2 — strikes: accumulated grievance triggers a guild-wide
freeze, and the player's response as talent has real, lasting Rolodex consequences.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

from callback.engine.rolodex.rolodex import Rolodex, apply_affinity_grudge

# Grievance accumulation — era-driven triggers (§10.6) are out of this pass's scope; a slow random
# walk stands in for them, documented as such.
GRIEVANCE_GAIN_MEAN = 6.0
GRIEVANCE_GAIN_SD = 4.0
STRIKE_THRESHOLD = 100.0
STRIKE_DURATION_LO, STRIKE_DURATION_HI = 1, 4  # quarters

HOLD_THE_LINE_AFFINITY = 8.0
CROSS_AFFINITY = -40.0
CROSS_PERMANENT_GRUDGE_CHANCE = 0.20
CROSS_GRUDGE_MAGNITUDE = 100.0  # effectively permanent — clamped by NPC.clamped() at 100

HOLD, INTERIM, CROSS = "hold_the_line", "interim", "cross"


@dataclass(frozen=True)
class StrikeState:
    grievance: float = 0.0
    active: bool = False
    quarters_remaining: int = 0


def advance_grievance(state: StrikeState, rng: random.Random) -> StrikeState:
    if state.active:
        remaining = state.quarters_remaining - 1
        return replace(state, active=remaining > 0, quarters_remaining=max(0, remaining))
    grievance = state.grievance + max(0.0, rng.gauss(GRIEVANCE_GAIN_MEAN, GRIEVANCE_GAIN_SD))
    if grievance >= STRIKE_THRESHOLD:
        return StrikeState(grievance=0.0, active=True, quarters_remaining=rng.randint(STRIKE_DURATION_LO, STRIKE_DURATION_HI))
    return replace(state, grievance=grievance)


def resolve_strike_choice(rolodex: Rolodex, choice: str, rng: random.Random) -> Rolodex:
    union_npcs = [n for n in rolodex.npcs.values() if n.npc_type in ("director", "producer", "casting_director")]

    if choice == HOLD:
        for n in union_npcs:
            rolodex = apply_affinity_grudge(rolodex, n.npc_id, affinity_delta=HOLD_THE_LINE_AFFINITY)
        return rolodex

    if choice == CROSS:
        for n in union_npcs:
            grudge_delta = CROSS_GRUDGE_MAGNITUDE if rng.random() < CROSS_PERMANENT_GRUDGE_CHANCE else 0.0
            rolodex = apply_affinity_grudge(rolodex, n.npc_id, affinity_delta=CROSS_AFFINITY, grudge_delta=grudge_delta)
        return rolodex

    return rolodex  # interim: neutral, no Rolodex-wide effect
