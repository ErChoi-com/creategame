"""design/part-09-genres-franchises-and-tie-ins.md §9.2 — hybrids, a film's secondary genre.

A hybrid isn't a third tuning system alongside genre/subgenres — it's a role carrying a second
genre tag (Role.secondary_genre) alongside its primary one, resolved by averaging the two parents'
own already-existing numbers rather than inventing new per-hybrid constants. Same abstraction
shape as genre/subgenres.py's own "no separate mechanic to maintain" note: the only genuinely new
things here are the marketing penalty and the quality-gated critic bonus §9.2 names, both flat and
genre-independent, applied by simulation.career.resolve_quality/actor.reception.resolve_reception
only when Role.secondary_genre is set — None (the default, every existing Role) leaves every
non-hybrid film's numbers exactly as before.
"""
from __future__ import annotations

# §9.2 — "Hybrids average the demand of both parents, take a −8 marketing penalty (harder to sell
# in one sentence), and get a +6 critic bonus if ProjectQuality > 70."
HYBRID_MARKETING_PENALTY = -8.0
HYBRID_CRITIC_BONUS = 6.0
HYBRID_CRITIC_BONUS_QUALITY_THRESHOLD = 70.0


def hybrid_demand(primary_demand: float, secondary_demand: float) -> float:
    """§9.2's own "average the demand of both parents" — the only genre-cycle wiring a hybrid
    needs, since world/genre_cycle.py already produces a real per-genre GenreDemand for whichever
    tag is asked of it, primary or secondary alike."""
    return (primary_demand + secondary_demand) / 2.0


def hybrid_critic_bonus(project_quality: float) -> float:
    """The +6 critic bonus is quality-gated — a hybrid only reads as a genuine creative swing
    ("elevated," in the language critics use for exactly this) once the film clears the bar; a bad
    hybrid gets no credit just for being one."""
    return HYBRID_CRITIC_BONUS if project_quality > HYBRID_CRITIC_BONUS_QUALITY_THRESHOLD else 0.0
