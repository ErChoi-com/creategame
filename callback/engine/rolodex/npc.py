"""design/part-04-the-actor.md §4.12 (the Rolodex edges) + design/part-10-the-world.md §10.0
(Agendas, the relationship arc) + design/ux/04-pull-systems.md (the player-facing shape).

An NPC carries the four raw §4.12 fields (affinity, grudge, shared_projects, last_contact) plus
§10.0's hidden Agenda and named relationship state. Tracked NPCs (the "eight" — see rolodex.py)
also carry a lightweight StandingModel of their own, reusing core.meters exactly the way
actor/standing.py configures one for the player — this is design/part-03 §3.3's "one Standing
model" rule holding for NPCs, not just the player.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field, replace

from callback.engine.core.meters import Meter, StandingModel
from callback.engine.core.util import clamp

NPC_TYPES = ("director", "casting_director", "producer", "agent", "costar", "critic")

# §10.0's six Agendas, with which NPC types they're common in (informational only — any type can
# carry any Agenda; this just matches the doc's own "common in" column when generating NPCs).
ASCENT, LEGACY, LOYALTY, REDEMPTION, VINDICATION, MENTORSHIP = (
    "ascent", "legacy", "loyalty", "redemption", "vindication", "mentorship",
)
AGENDAS = (ASCENT, LEGACY, LOYALTY, REDEMPTION, VINDICATION, MENTORSHIP)
AGENDA_COMMON_TYPES = {
    ASCENT: ("agent", "costar"),
    LEGACY: ("director", "costar"),
    LOYALTY: ("director", "producer"),
    REDEMPTION: ("producer", "costar", "critic"),
    VINDICATION: ("costar",),
    MENTORSHIP: ("director", "costar"),
}

# §10.0's relationship arc.
STRANGER, FAMILIAR, ALLY, RIVAL, LOYAL, ESTRANGED, LEGACY_STATE, SEVERED = (
    "stranger", "familiar", "ally", "rival", "loyal", "estranged", "legacy", "severed",
)

# §10.0's transition thresholds, read off the same fields §4.12 already tracks.
ALLY_AFFINITY_THRESHOLD = 50.0
LOYAL_AFFINITY_THRESHOLD = 70.0
ESTRANGED_GRUDGE_THRESHOLD = 40.0

# §10.0's InteractionEffect multiplier: serves their Agenda / neutral / ignores it.
AGENDA_SERVED_MULT = 1.6
AGENDA_NEUTRAL_MULT = 1.0
AGENDA_IGNORED_MULT = 0.6


@dataclass(frozen=True)
class NPC:
    npc_id: str
    name: str
    npc_type: str
    agenda: str
    affinity: float = 0.0
    grudge: float = 0.0
    shared_projects: int = 0
    last_contact_year: int | None = None
    on_loyalty_roster: bool = False
    relationship_state: str = STRANGER
    active: bool = True  # False once retired/dead — becomes "legacy" and stops taking interactions
    standing: StandingModel | None = None  # only populated for tracked NPCs (rolodex.py)

    def clamped(self) -> "NPC":
        return replace(self, affinity=clamp(self.affinity, -100.0, 100.0), grudge=clamp(self.grudge, 0.0, 100.0))

    def state_after_update(self) -> str:
        """Recompute relationship_state from current affinity/grudge/loyalty-roster status. Never
        moves a Severed or Legacy NPC back automatically — those only change via an explicit
        reconciliation action (rolodex/interactions.py) or the NPC's own career ending."""
        if self.relationship_state in (SEVERED, LEGACY_STATE):
            return self.relationship_state
        if self.grudge >= ESTRANGED_GRUDGE_THRESHOLD:
            return ESTRANGED
        if self.on_loyalty_roster and self.affinity >= LOYAL_AFFINITY_THRESHOLD:
            return LOYAL
        if self.affinity >= ALLY_AFFINITY_THRESHOLD:
            return ALLY
        if self.relationship_state == RIVAL:
            return RIVAL  # rivalry is assigned externally (rolodex.py's ranking), not derived here
        if self.shared_projects >= 1 or self.last_contact_year is not None:
            return FAMILIAR
        return STRANGER

    def agenda_multiplier(self, serves_agenda: bool | None) -> float:
        """serves_agenda: True (action targets their Agenda), False (visibly ignores it), or None
        (neutral action, e.g. a plain professional interaction)."""
        if serves_agenda is None:
            return AGENDA_NEUTRAL_MULT
        return AGENDA_SERVED_MULT if serves_agenda else AGENDA_IGNORED_MULT


def generate_npc(rng: random.Random, npc_id: str, npc_type: str | None = None) -> NPC:
    npc_type = npc_type or rng.choice(NPC_TYPES)
    # Agenda draw is weighted toward the types §10.0 calls common for it, but any type can get any.
    weights = [3.0 if npc_type in AGENDA_COMMON_TYPES[a] else 1.0 for a in AGENDAS]
    agenda = rng.choices(AGENDAS, weights=weights)[0]
    name = f"NPC-{npc_id}"  # a naming/generation layer is a UI concern, not this engine's
    standing = None
    if npc_type in ("director", "costar", "producer"):
        standing = StandingModel(meters={
            "heat": Meter("heat", clamp(rng.gauss(30, 20), 0, 100)),
            "prestige": Meter("prestige", clamp(rng.gauss(35, 20), 0, 100)),
            "affection": Meter("affection", clamp(rng.gauss(30, 20), 0, 100)),
            "notoriety": Meter("notoriety", clamp(rng.gauss(10, 12), 0, 100)),
        })
    return NPC(npc_id=npc_id, name=name, npc_type=npc_type, agenda=agenda, standing=standing)
