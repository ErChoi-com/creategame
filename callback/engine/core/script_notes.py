"""design/part-05-the-work.md §5.15 — script notes, generalized. Shared by both careers rather than
owned by `actor/`: a director shaping their own film and an actor holding script approval on
someone else's are the same underlying choice (push for clarity, ambiguity, or the whole film) at
different weights, not two different mechanics. Lived in `actor/script_notes.py` until the director
port made clear it was career-agnostic — moved here per `core/`'s own layering rule (§3.3: "one
system, not a second hand-rolled version").

The director is the film's primary creative authority — the same real-world default the design
doc's own framing ("anyone holding script approval gets notes") is an exception to. `DIRECTOR_NOTE_
WEIGHT` (1.0) vs `ACTOR_FILM_NOTE_WEIGHT` (0.4) makes that a real number, not just flavor text: an
actor's note still moves the finished film, just not as much as the director's does. What's never
scaled down is `fit_delta` — an actor's own read on their own part is entirely theirs regardless of
who else weighs in, which is the other half of "both have autonomy."
"""
from __future__ import annotations

from dataclasses import dataclass, replace

CLARITY, AMBIGUITY, YOUR_PART, WHOLE_FILM = "clarity", "ambiguity", "your_part", "whole_film"
SCRIPT_NOTE_OPTIONS = (CLARITY, AMBIGUITY, YOUR_PART, WHOLE_FILM)

# A director pushing notes on their own film has no "your part" to push for — that option is
# specifically an actor angling for their own role at the film's expense. The other three (make it
# read clearer, make it read richer, or just make the whole thing better) are exactly the choices
# a director actually faces, and they face them at full weight (see DIRECTOR_NOTE_WEIGHT below).
DIRECTOR_SCRIPT_NOTE_OPTIONS = (CLARITY, AMBIGUITY, WHOLE_FILM)

CLARITY_AUDIENCE_DELTA = 4.0
CLARITY_CRITIC_DELTA = -3.0

AMBIGUITY_CRITIC_DELTA = 4.0
AMBIGUITY_AUDIENCE_DELTA = -3.0
AMBIGUITY_CULT_CHANCE_BONUS = 0.05

YOUR_PART_FIT_DELTA = 6.0
YOUR_PART_SCRIPT_QUALITY_DELTA = -4.0

WHOLE_FILM_SCRIPT_QUALITY_DELTA = 5.0

# Weight applied to the film-wide side of a note (script_quality/audience/critic/cult_chance) based
# on whose note it is. fit_delta is never scaled by either — an actor's read on their own part
# doesn't get diluted by anyone else's opinion of the film.
DIRECTOR_NOTE_WEIGHT = 1.0
ACTOR_FILM_NOTE_WEIGHT = 0.4


@dataclass(frozen=True)
class ScriptNoteEffect:
    fit_delta: float = 0.0
    script_quality_delta: float = 0.0
    audience_delta: float = 0.0
    critic_delta: float = 0.0
    cult_chance_bonus: float = 0.0

    def scaled(self, film_weight: float) -> "ScriptNoteEffect":
        """Scale only the film-wide component (fit_delta is always the actor's own, untouched)."""
        return replace(
            self,
            script_quality_delta=self.script_quality_delta * film_weight,
            audience_delta=self.audience_delta * film_weight,
            critic_delta=self.critic_delta * film_weight,
            cult_chance_bonus=self.cult_chance_bonus * film_weight,
        )

    def combined_with(self, other: "ScriptNoteEffect") -> "ScriptNoteEffect":
        return ScriptNoteEffect(
            fit_delta=self.fit_delta + other.fit_delta,
            script_quality_delta=self.script_quality_delta + other.script_quality_delta,
            audience_delta=self.audience_delta + other.audience_delta,
            critic_delta=self.critic_delta + other.critic_delta,
            cult_chance_bonus=self.cult_chance_bonus + other.cult_chance_bonus,
        )


def apply_script_note(choice: str) -> ScriptNoteEffect:
    if choice == CLARITY:
        return ScriptNoteEffect(audience_delta=CLARITY_AUDIENCE_DELTA, critic_delta=CLARITY_CRITIC_DELTA)
    if choice == AMBIGUITY:
        return ScriptNoteEffect(critic_delta=AMBIGUITY_CRITIC_DELTA, audience_delta=AMBIGUITY_AUDIENCE_DELTA,
                                 cult_chance_bonus=AMBIGUITY_CULT_CHANCE_BONUS)
    if choice == YOUR_PART:
        return ScriptNoteEffect(fit_delta=YOUR_PART_FIT_DELTA, script_quality_delta=YOUR_PART_SCRIPT_QUALITY_DELTA)
    if choice == WHOLE_FILM:
        return ScriptNoteEffect(script_quality_delta=WHOLE_FILM_SCRIPT_QUALITY_DELTA)
    return ScriptNoteEffect()


def sample_director_note(skill: float, command: float, rng) -> tuple[str, ScriptNoteEffect]:
    """The NPC (or player) director's own creative push on a film — the primary signal, applied at
    DIRECTOR_NOTE_WEIGHT (1.0). A more skilled, more commanding director leans harder toward "whole
    film" (§5.15's own quietly-correct answer) rather than chasing a single audience/critic lever;
    a weaker director is more likely to reach for the blunter clarity/ambiguity tools. Returns the
    choice too, so callers (the actor's shoot summary, the CLI) can show whose note it was."""
    whole_film_weight = 1.0 + max(skill, command) / 40.0
    choice = rng.choices(
        DIRECTOR_SCRIPT_NOTE_OPTIONS, weights=[1.0, 1.0, whole_film_weight],
    )[0]
    return choice, apply_script_note(choice)
