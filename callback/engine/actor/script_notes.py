"""design/part-05-the-work.md §5.15 — Script notes: "Anyone holding script approval (§6.3) gets
notes. What you push for is a real choice with real costs." Four options, each a real trade
between how the film reads and how you read in it — including "push for the whole film," which
should be the quietly correct answer often enough that players discover it themselves.
"""
from __future__ import annotations

from dataclasses import dataclass

CLARITY, AMBIGUITY, YOUR_PART, WHOLE_FILM = "clarity", "ambiguity", "your_part", "whole_film"
SCRIPT_NOTE_OPTIONS = (CLARITY, AMBIGUITY, YOUR_PART, WHOLE_FILM)

# A director pushing notes on their own film has no "your part" to push for — that option is
# specifically an actor angling for their own role at the film's expense. The other three (make it
# read clearer, make it read richer, or just make the whole thing better) are exactly the choices
# a director actually faces.
DIRECTOR_SCRIPT_NOTE_OPTIONS = (CLARITY, AMBIGUITY, WHOLE_FILM)

CLARITY_AUDIENCE_DELTA = 4.0
CLARITY_CRITIC_DELTA = -3.0

AMBIGUITY_CRITIC_DELTA = 4.0
AMBIGUITY_AUDIENCE_DELTA = -3.0
AMBIGUITY_CULT_CHANCE_BONUS = 0.05

YOUR_PART_FIT_DELTA = 6.0
YOUR_PART_SCRIPT_QUALITY_DELTA = -4.0

WHOLE_FILM_SCRIPT_QUALITY_DELTA = 5.0


@dataclass(frozen=True)
class ScriptNoteEffect:
    fit_delta: float = 0.0
    script_quality_delta: float = 0.0
    audience_delta: float = 0.0
    critic_delta: float = 0.0
    cult_chance_bonus: float = 0.0


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
