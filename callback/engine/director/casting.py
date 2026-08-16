"""design/part-07-the-director.md §7.1 — "Casting is a gate you try to pass (actor) -> You
operate the gate (director): you run the utility function in §4.4 from the other side."

No new formula: this is a thin, discoverable wrapper naming that reuse, not a second Utility.
"""
from __future__ import annotations

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.offers import Role, utility
from callback.engine.actor.persona import Persona
from callback.engine.core.meters import StandingModel


def evaluate_candidate(
    candidate_attrs: Attributes,
    candidate_persona: Persona,
    candidate_standing: StandingModel,
    role: Role,
    candidate_age: int,
    candidate_quote: float,
) -> float:
    """The director's read on a candidate actor for a role — literally actor.offers.utility(),
    run with the candidate as the subject rather than the player."""
    return utility(candidate_attrs, candidate_persona, candidate_standing, role, candidate_age, candidate_quote)
