"""Session-level orchestration of design/part-09's sequel-value curve (genre/franchise.py) and
design/part-06's Indispensability holdout (leverage/indispensability.py) — composing both, plus a
returning director's own continuity across installments, into the actor's regular game loop.

Kept alongside full_career.py's other simulation-layer state (Rolodex/Leverage/Life) rather than
inside actor/ itself: "is this offer a sequel to a franchise you're already in" needs the
FullState's franchise history, not just a single Role, so the orchestration belongs here.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, replace

from callback.engine.actor.offers import Role
from callback.engine.actor.standing import star_power
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp, sigmoid
from callback.engine.director.skill import ENGAGEMENT_PASSION_PROJECT
from callback.engine.genre.franchise import SEQUEL_BONUS_AUDIENCE_CENTRE, sequel_bonus, spacing_modifier
from callback.engine.leverage.indispensability import character_identification, decay_dormant, indispensability

NEW_FRANCHISE_CHANCE = 0.05  # a fresh franchise starting from an original role, per offer rolled
SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS = 4  # a franchise dormant longer than this isn't greenlighting a sequel

# A studio doesn't roll one flat number for "is this a sequel year" regardless of how the last
# installment actually did — sequel_probability() reads the same prior_audience_score the sequel-
# value curve (genre/franchise.py) already tracks, plus how indispensable the lead has become.
# SEQUEL_CHANCE_BASE is what a franchise gets at exactly-average reception (audience score at
# SEQUEL_BONUS_AUDIENCE_CENTRE) with no built-up indispensability — the same 0.35 this used to be
# unconditionally, now a baseline rather than the whole story.
SEQUEL_CHANCE_BASE = 0.35
SEQUEL_AUDIENCE_SLOPE = 0.045  # how hard reception swings the odds around that baseline
SEQUEL_INDISPENSABILITY_COEF = 0.006  # a beloved, hard-to-recast lead keeps a studio coming back
SEQUEL_CHANCE_CEILING = 0.75  # even a beloved hit franchise isn't greenlit on autopilot every year


def sequel_probability(prior_audience_score: float, franchise_indispensability: float) -> float:
    """How likely a studio is to greenlight the next installment this year, given an eligible,
    non-dormant franchise. sigmoid(...) * 2 centres on 1.0 at exactly-average reception (so
    SEQUEL_CHANCE_BASE is unchanged at that point), climbing for a franchise that actually landed
    with audiences and falling for one that didn't — a $3M flop's sequel is a real long shot, not
    the same coin flip as a $200M runaway hit's. Indispensability layers a second, independent
    reason on top: a character audiences have identified with keeps a studio coming back even if
    the numbers alone wouldn't justify it."""
    reception_multiplier = sigmoid(SEQUEL_AUDIENCE_SLOPE * (prior_audience_score - SEQUEL_BONUS_AUDIENCE_CENTRE)) * 2.0
    indispensability_multiplier = 1.0 + SEQUEL_INDISPENSABILITY_COEF * max(franchise_indispensability, 0.0)
    return clamp(SEQUEL_CHANCE_BASE * reception_multiplier * indispensability_multiplier, 0.0, SEQUEL_CHANCE_CEILING)
FRANCHISE_INDISPENSABILITY_HOLDOUT_THRESHOLD = 30.0
DEFAULT_CONTRACTUAL_HOLD = 50.0  # §6.4 names this as a real input; not otherwise modeled this pass
DEFAULT_CAST_AVERAGE_STAR_POWER = 50.0  # same — the rest of the cast's own star power isn't tracked per-NPC

# A spin-off is a real player-initiated action, not a passive roll like maybe_attach_franchise:
# once a character has become genuinely indispensable to its franchise, the actor can pitch a new
# property built off that same standing (the same studio, usually the same genre, seeded with a
# starting audience bonus off the parent's own indispensability instead of starting cold).
SPINOFF_INDISPENSABILITY_THRESHOLD = 55.0
SPINOFF_AUDIENCE_BONUS_COEF = 0.35  # how much of the parent's indispensability carries over as a head start


@dataclass(frozen=True)
class FranchiseEntry:
    franchise_id: str
    genre: str
    studio_id: str  # a franchise stays with the studio that made it — real continuity, not flavor
    installments_starred: int = 0
    character_id: float = 20.0
    indispensability: float = 0.0
    prior_audience_score: float = SEQUEL_BONUS_AUDIENCE_CENTRE
    last_installment_year: int = -999
    prior_holdouts: int = 0
    last_director_npc_id: str | None = None


def maybe_attach_franchise(role: Role, franchises: dict, current_year: int, rng: random.Random) -> Role:
    """Called on a freshly-sampled Role before it's ever shown on the board: with some chance,
    turns it into either the next installment of an existing open franchise (same genre/studio,
    continuity intact) or the first installment of a brand-new one."""
    eligible = [
        f for f in franchises.values()
        if current_year - f.last_installment_year <= SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS
    ]
    # Each eligible franchise gets its own independent roll, in shuffled order (so with several
    # open franchises it isn't always the same one checked first) — a beloved hit and a franchise
    # nobody liked are no longer competing for the same flat chance, each stands on its own
    # reception. First one to clear its own bar wins the slot.
    for f in rng.sample(eligible, len(eligible)):
        if rng.random() < sequel_probability(f.prior_audience_score, f.indispensability):
            return replace(role, genre=f.genre, studio=f.studio_id, franchise_id=f.franchise_id,
                            installment_number=f.installments_starred + 1)
    if rng.random() < NEW_FRANCHISE_CHANCE:
        franchise_id = f"fr_{rng.randrange(10**6):06d}"
        return replace(role, franchise_id=franchise_id, installment_number=1)
    return role


def franchise_audience_bonus(role: Role, franchises: dict, current_year: int) -> float:
    """§9.5's sequel-value curve — a real box-office bonus, applied straight onto AudienceScore,
    scaled by how well the last installment actually landed (not just "it's a sequel") — plus a
    spacing modifier (genre.franchise.spacing_modifier): a rushed sequel reads as oversaturated,
    a well-spaced one benefits from real anticipation."""
    if not role.franchise_id:
        return 0.0
    f = franchises.get(role.franchise_id)
    prior_audience = f.prior_audience_score if f else SEQUEL_BONUS_AUDIENCE_CENTRE
    years_since_last = current_year - f.last_installment_year if f else 999
    return sequel_bonus(role.installment_number, prior_audience) + spacing_modifier(role.installment_number, years_since_last)


def director_continuity_bonus(role: Role, franchises: dict, requested_director_npc_id: str | None) -> float:
    """A director returning to their own franchise gets the same passion-project engagement bump
    director/skill.py already defines for a genuinely personal project — continuity is rewarded
    mechanically, not just described in flavor text."""
    if not role.franchise_id or requested_director_npc_id is None:
        return 0.0
    f = franchises.get(role.franchise_id)
    if f and f.last_director_npc_id == requested_director_npc_id:
        return ENGAGEMENT_PASSION_PROJECT
    return 0.0


def update_franchise_after_project(
    franchises: dict,
    role: Role,
    spotlight: float,
    audience_score: float,
    standing_model: StandingModel,
    current_year: int,
    requested_director_npc_id: str | None,
) -> dict:
    if not role.franchise_id:
        return franchises
    prior = franchises.get(role.franchise_id) or FranchiseEntry(
        franchise_id=role.franchise_id, genre=role.genre, studio_id=role.studio,
    )
    new_character_id = character_identification(prior.character_id, spotlight, memorability=audience_score)
    new_installments = prior.installments_starred + 1
    new_indispensability = indispensability(
        new_character_id, new_installments, star_power(standing_model),
        DEFAULT_CAST_AVERAGE_STAR_POWER, DEFAULT_CONTRACTUAL_HOLD,
    )
    updated = replace(
        prior, installments_starred=new_installments, character_id=new_character_id,
        indispensability=new_indispensability, prior_audience_score=audience_score,
        last_installment_year=current_year, last_director_npc_id=requested_director_npc_id,
    )
    return {**franchises, role.franchise_id: updated}


def decay_dormant_franchises(franchises: dict, current_year: int) -> dict:
    """§6.4's v9 fix, honored here too: decay runs unconditionally every dormant year, and a
    property that crosses the release floor drops out of tracking entirely rather than sticking
    around forever at a near-zero value."""
    result = {}
    for franchise_id, f in franchises.items():
        if f.last_installment_year == current_year:
            result[franchise_id] = f  # touched this year — already fresh, nothing to decay
            continue
        new_value, released = decay_dormant(f.indispensability)
        if released:
            continue
        result[franchise_id] = replace(f, indispensability=new_value)
    return result


def spinoff_available(franchise: "FranchiseEntry") -> bool:
    return franchise.indispensability >= SPINOFF_INDISPENSABILITY_THRESHOLD


def create_spinoff_entry(parent: "FranchiseEntry", new_franchise_id: str, current_year: int) -> FranchiseEntry:
    """A spin-off starts as its own franchise (installment 1 next time it's cast) rather than
    continuing the parent's own installment count — but it isn't starting cold: prior_audience_
    score is seeded off the parent's real indispensability, a genuine head start sequel_bonus()
    reads the same way it reads a real prior installment's own audience_score. last_installment_
    year is stamped to now, not left dormant — a brand-new entry's indispensability starts at 0,
    and decay_dormant_franchises() releases anything at 0 the moment it isn't "touched this year";
    without this it would vanish before ever actually being cast."""
    seeded_audience = SEQUEL_BONUS_AUDIENCE_CENTRE + SPINOFF_AUDIENCE_BONUS_COEF * parent.indispensability
    return FranchiseEntry(
        franchise_id=new_franchise_id, genre=parent.genre, studio_id=parent.studio_id,
        prior_audience_score=seeded_audience, last_installment_year=current_year,
    )
