"""design/ux/04-pull-systems.md's Rolodex tab — pull actions that build a relationship instead of
spending one. design/ doesn't publish exact numeric effects for these (they're a UX-level
addition, not a §4.12/§10.0 formula); the constants below are this pass's documented reading,
sized consistently with the magnitudes elsewhere in Part 4/6 (a favour-sized action moves
affinity by low single digits; a "show up" gesture is worth several times that).
"""
from __future__ import annotations

from dataclasses import replace

from callback.engine.rolodex.npc import NPC

CHECK_IN_AFFINITY = 2.0
SHOW_UP_AFFINITY = 8.0
SHOW_UP_ABSENCE_DECAY = -3.0  # applied by callers who track "years since last shown up," not here
VOUCH_AFFINITY = 4.0
VOUCH_STANDING_BOOST = 6.0  # to the NPC's own Prestige/Affection, if they have a StandingModel

AGENDA_ACTION_BASE_EFFECT = 5.0


def check_in(npc: NPC, year: int) -> NPC:
    updated = replace(npc, affinity=npc.affinity + CHECK_IN_AFFINITY, last_contact_year=year)
    return replace(updated, relationship_state=updated.state_after_update()).clamped()


def show_up_for_them(npc: NPC, year: int) -> NPC:
    updated = replace(npc, affinity=npc.affinity + SHOW_UP_AFFINITY, last_contact_year=year)
    return replace(updated, relationship_state=updated.state_after_update()).clamped()


def read_agenda_and_act(npc: NPC, served_agenda: bool, year: int) -> NPC:
    """served_agenda: the player's guess at what this NPC's Agenda actually is, correct or not.
    §10.0's InteractionEffect multiplier (1.6x served, 0.6x ignored) applies to the base gesture."""
    effect = AGENDA_ACTION_BASE_EFFECT * npc.agenda_multiplier(served_agenda)
    updated = replace(npc, affinity=npc.affinity + effect, last_contact_year=year)
    return replace(updated, relationship_state=updated.state_after_update()).clamped()


def vouch_for_them(npc: NPC, year: int) -> NPC:
    """Same substrate as the Leverage catalogue's "Recommend someone" (design/part-06 §6.6) —
    aimed specifically at rebuilding a Redemption-agenda NPC's standing rather than landing them
    one job."""
    updated = replace(npc, affinity=npc.affinity + VOUCH_AFFINITY, last_contact_year=year)
    if updated.standing is not None:
        boosted = updated.standing.copy()
        boosted.add("prestige", VOUCH_STANDING_BOOST)
        boosted.add("affection", VOUCH_STANDING_BOOST)
        updated = replace(updated, standing=boosted)
    return replace(updated, relationship_state=updated.state_after_update()).clamped()
