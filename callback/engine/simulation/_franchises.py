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
    peak_indispensability: float = 0.0  # the character's own career-best — tracked continuously,
    # not just at retirement, since it's the real "how beloved did this ever get" read a reboot
    # roll needs (current indispensability is nearly always near the release floor by the time a
    # franchise actually retires, so it can't answer that question on its own).
    retired_year: int | None = None  # set only once this entry moves into the retired archive
    # (simulation._franchises.decay_dormant_franchises) — None for anything still active.
    you_are_current_lead: bool = True  # flips False on an exit (apply_exit below); a franchise
    # doesn't end just because the player leaves it — the studio owns the property, not the actor
    # (the same "protects the property, not the individual" framing studio_protectiveness already
    # names), so it keeps being cast, sequeled, and rebooted without them.
    exit_type: str | None = None  # "recast" or "written_out" — None while still active. See
    # resolve_exit_type below: which one happens isn't a single mechanic, it's two genuinely
    # different outcomes with different consequences.
    exit_year: int | None = None  # None unless you_are_current_lead is False
    audience_score_at_exit: float | None = None  # a frozen snapshot of prior_audience_score the
    # moment you left — franchise_status() diffs this against the live prior_audience_score so the
    # player can see, in real numbers, whether it did better or worse without them.


def maybe_attach_franchise(role: Role, franchises: dict, current_year: int, rng: random.Random) -> Role:
    """Called on a freshly-sampled Role before it's ever shown on the board: with some chance,
    turns it into either the next installment of an existing open franchise (same genre/studio,
    continuity intact) or the first installment of a brand-new one."""
    eligible = [
        f for f in franchises.values()
        if current_year - f.last_installment_year <= SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS
        and f.you_are_current_lead  # recast franchises keep going (advance_franchises_without_you
        # below), just never as a role offered back to the person who was replaced.
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
        peak_indispensability=max(prior.peak_indispensability, new_indispensability),
    )
    return {**franchises, role.franchise_id: updated}


def decay_dormant_franchises(franchises: dict, current_year: int) -> tuple[dict, dict]:
    """§6.4's v9 fix, honored here too: decay runs unconditionally every dormant year. A property
    that crosses the release floor no longer just vanishes, though — it moves into a second
    returned dict (newly retired this year) rather than being discarded outright, so reboot_
    probability() below has something real to roll against later. Returns (active, newly_retired)."""
    active = {}
    newly_retired = {}
    for franchise_id, f in franchises.items():
        if f.last_installment_year == current_year:
            active[franchise_id] = f  # touched this year — already fresh, nothing to decay
            continue
        new_value, released = decay_dormant(f.indispensability)
        if released:
            newly_retired[franchise_id] = replace(f, indispensability=new_value, retired_year=current_year)
            continue
        active[franchise_id] = replace(f, indispensability=new_value)
    return active, newly_retired


# The positive mirror of decay_dormant_franchises's own one-way "fades to nothing" arc — a
# retired property doesn't just vanish from the industry's memory. A real, small, per-year chance
# of a reboot: an anniversary re-release, a streaming-era revival, a straight remake — the same
# real-world shape actual dormant IP coming back has. Nobody reboots something that only just
# ended (REBOOT_MIN_DORMANT_YEARS), and a franchise that peaked higher is more likely to come back
# than one that was always a footnote.
REBOOT_MIN_DORMANT_YEARS = 5
REBOOT_CHANCE_BASE = 0.02
REBOOT_PEAK_COEF = 0.0025
REBOOT_CHANCE_CEILING = 0.20
# A reboot doesn't hand back full peak value — a real, partial second life, the same "seeded off
# the parent's own real number, not starting cold" logic create_spinoff_entry already uses.
REBOOT_REVIVAL_INDISPENSABILITY_SHARE = 0.55


def reboot_probability(years_dormant: int, peak_indispensability: float) -> float:
    if years_dormant < REBOOT_MIN_DORMANT_YEARS:
        return 0.0
    return clamp(REBOOT_CHANCE_BASE + REBOOT_PEAK_COEF * peak_indispensability, 0.0, REBOOT_CHANCE_CEILING)


def resolve_reboots(retired: dict, current_year: int, rng: random.Random) -> tuple[dict, dict]:
    """Rolls each retired franchise's own independent reboot chance. Returns (still_retired,
    revived) — the caller merges revived back into the active franchises dict; a revived entry's
    last_installment_year is stamped to now, so it's immediately eligible for maybe_attach_
    franchise's own sequel roll next time a role is sampled — a real "they're bringing your old
    franchise back" offer, not just a number moving in the background.

    A reboot always sets you_are_current_lead back to True, whether or not you were still the lead
    when it retired — the real-world "legacy sequel" shape (the original cast returning for an
    anniversary/reunion installment after years of someone else carrying it, or nobody at all) is
    exactly the same event as an ordinary reboot here, not a second mechanic. exit_type/exit_year/
    audience_score_at_exit clear along with it — the comparison was against the years you were
    gone; now that you're back, there's nothing left to compare."""
    still_retired = {}
    revived = {}
    for franchise_id, f in retired.items():
        years_dormant = current_year - (f.retired_year if f.retired_year is not None else current_year)
        if rng.random() < reboot_probability(years_dormant, f.peak_indispensability):
            revived[franchise_id] = replace(
                f,
                indispensability=f.peak_indispensability * REBOOT_REVIVAL_INDISPENSABILITY_SHARE,
                last_installment_year=current_year,
                retired_year=None,
                you_are_current_lead=True,
                exit_type=None,
                exit_year=None,
                audience_score_at_exit=None,
            )
        else:
            still_retired[franchise_id] = f
    return still_retired, revived


# The recast-continuation mechanic: losing a role (a lost holdout, or the studio proceeding on a
# sequel you declined) doesn't delete the franchise — it keeps existing, keeps getting sequeled,
# and can keep being rebooted (including, per resolve_reboots above, back to you) exactly like any
# other property. Only the front door — maybe_attach_franchise, gated on you_are_current_lead above
# — actually changes for the player: you stop being offered a part in it.
#
# "Losing the part" isn't one outcome, though — a franchise can either recast the character (someone
# else plays you) or write the character out and lean on the rest of the ensemble instead, and those
# are genuinely different beats, not two names for the same thing. character_id (character_
# identification) is already exactly the right signal for which is plausible: it's the one number
# this engine tracks that measures how much the audience treats THIS character as inseparable from
# the franchise, independent of the property's overall indispensability (installments/star power/
# contractual hold) — a Bond-shaped character has to be recast to continue; a more replaceable one
# inside a real ensemble can just be quietly written around.
WRITEOUT_BASE = 0.55
WRITEOUT_CHARACTER_ID_COEF = 0.008
WRITEOUT_CHARACTER_ID_NOISE_SD = 8.0  # cast chemistry, timing, tone of the exit — real variance a
# single character_id reading can't capture; the same character never resolves identically twice.


def written_out_probability(character_id: float, rng: random.Random) -> float:
    jittered = character_id + rng.gauss(0.0, WRITEOUT_CHARACTER_ID_NOISE_SD)
    return clamp(WRITEOUT_BASE - WRITEOUT_CHARACTER_ID_COEF * max(0.0, jittered), 0.0, 1.0)


def resolve_exit_type(franchise: "FranchiseEntry", rng: random.Random) -> str:
    return "written_out" if rng.random() < written_out_probability(franchise.character_id, rng) else "recast"


# Recast: a fresh face reads as a real, if modest, dip in reception — audiences notice a recast even
# in a well-loved franchise, just less so than in a fragile one. Never a fixed number off protective-
# ness alone — real per-event noise on top, the same "never lands on the same number twice" shape
# leverage.merchandising.negotiated_merch_share already uses for a negotiated position.
RECAST_AUDIENCE_PENALTY_BASE = 8.0
RECAST_PROTECTIVENESS_SHIELD_COEF = 0.06  # studio_protectiveness() shields against it — the same
# "the property is bigger than any one performer" reading that makes a brand-driven franchise barely
# notice a recast, while an actor-driven one takes the fuller hit.
RECAST_AUDIENCE_PENALTY_FLOOR = 1.0  # even the most brand-proof franchise feels something
RECAST_AUDIENCE_PENALTY_CEILING = 14.0
RECAST_AUDIENCE_PENALTY_NOISE_SD = 2.5

# Written out: no jarring replacement to react to, so the range sits near zero rather than being
# pulled one direction by a shield term — some send-offs land as a bold, well-received swerve, most
# land flat, a few land badly. Wider than the recast range, not narrower: there's no protectiveness-
# style force keeping it in a lane.
WRITEOUT_AUDIENCE_DELTA_LOW = -4.0
WRITEOUT_AUDIENCE_DELTA_HIGH = 3.0


def recast_audience_penalty(protectiveness: float, rng: random.Random) -> float:
    return clamp(
        RECAST_AUDIENCE_PENALTY_BASE + rng.gauss(0.0, RECAST_AUDIENCE_PENALTY_NOISE_SD)
        - RECAST_PROTECTIVENESS_SHIELD_COEF * protectiveness,
        RECAST_AUDIENCE_PENALTY_FLOOR, RECAST_AUDIENCE_PENALTY_CEILING,
    )


def writeout_audience_delta(rng: random.Random) -> float:
    return rng.uniform(WRITEOUT_AUDIENCE_DELTA_LOW, WRITEOUT_AUDIENCE_DELTA_HIGH)


def apply_exit(franchise: "FranchiseEntry", current_year: int, rng: random.Random) -> FranchiseEntry:
    """The single place a franchise actually loses its player-lead — called from both trigger
    points (a lost Indispensability holdout, and the studio proceeding on a declined sequel without
    you). Rolls which of the two real outcomes happens (resolve_exit_type) and snapshots the
    audience score at the moment of the split, so franchise_status() has a real before/after to
    show either way."""
    exit_type = resolve_exit_type(franchise, rng)
    if exit_type == "recast":
        delta = -recast_audience_penalty(studio_protectiveness(franchise), rng)
    else:
        delta = writeout_audience_delta(rng)
    return replace(
        franchise,
        you_are_current_lead=False,
        exit_type=exit_type,
        exit_year=current_year,
        audience_score_at_exit=franchise.prior_audience_score,
        prior_audience_score=clamp(franchise.prior_audience_score + delta, 0.0, 100.0),
    )


# Once you're gone, the franchise keeps moving off-screen either way — the studio doesn't need your
# participation to greenlight, shoot, and release its own sequels. Reuses sequel_probability (the
# same greenlight odds any installment rolls against) rather than a second gate, and a mild random
# walk in place of a full off-screen shoot resolution: no new actor or storyline is modeled, just
# whether audiences kept showing up. The two exit types get their own drift width, not a shared one
# — a recast continuation is genuinely noisier (audiences adjusting to someone new in the part) than
# a written-out one (the property's own trend was never disrupted, just redirected).
WITHOUT_YOU_AUDIENCE_DRIFT_SD_RECAST = 6.0
WITHOUT_YOU_AUDIENCE_DRIFT_SD_WRITTEN_OUT = 3.0
WITHOUT_YOU_AUDIENCE_PULL_TO_CENTRE = 0.10  # a small regression toward average each installment —
# absent whatever made the original casting work, an off-screen franchise drifts toward ordinary
# rather than sustaining a hit's own momentum indefinitely.
WITHOUT_YOU_INDISPENSABILITY_FADE = 0.95  # neither outcome quite recaptures what the original had


def advance_franchises_without_you(franchises: dict, current_year: int, rng: random.Random) -> dict:
    """Called once a year (simulation.full_career.advance_between_years) against whatever's still
    active after this year's decay/reboot pass. Only touches entries with you_are_current_lead
    False; every franchise the player still leads is entirely unaffected — those already advance
    through the player's own accept_and_play."""
    updated = dict(franchises)
    for franchise_id, f in franchises.items():
        if f.you_are_current_lead:
            continue
        if current_year - f.last_installment_year > SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS:
            continue  # too stale for a quiet off-screen sequel — decay_dormant_franchises and a
            # real reboot roll are what bring a franchise back from here, not this function
        if rng.random() >= sequel_probability(f.prior_audience_score, f.indispensability):
            continue
        drift_sd = (
            WITHOUT_YOU_AUDIENCE_DRIFT_SD_WRITTEN_OUT if f.exit_type == "written_out"
            else WITHOUT_YOU_AUDIENCE_DRIFT_SD_RECAST
        )
        drifted = f.prior_audience_score + rng.gauss(0.0, drift_sd)
        new_audience = clamp(
            drifted + WITHOUT_YOU_AUDIENCE_PULL_TO_CENTRE * (SEQUEL_BONUS_AUDIENCE_CENTRE - drifted),
            0.0, 100.0,
        )
        updated[franchise_id] = replace(
            f, installments_starred=f.installments_starred + 1, prior_audience_score=new_audience,
            indispensability=f.indispensability * WITHOUT_YOU_INDISPENSABILITY_FADE,
            last_installment_year=current_year,
        )
    return updated


# The studio proceeding on a sequel you declined, rather than just letting the franchise go
# dormant — reuses studio_protectiveness the same way the holdout's own recast pull already does:
# a franchise the studio has built real, sustained protectiveness around is one they're more
# willing to carry on without you, not less. This only decides WHETHER they proceed; apply_exit's
# own resolve_exit_type decides the separate question of HOW (recast vs written out).
DECLINE_CONTINUATION_CHANCE_BASE = 0.5
DECLINE_CONTINUATION_PROTECTIVENESS_COEF = 0.005

# How big a public story losing the part becomes — scaled by franchise size (min(installments, 8)),
# but the per-installment weight itself is drawn from a range, not fixed: an exit from a small
# franchise occasionally becomes a bigger deal than expected (a cult favorite), and a big one
# occasionally passes quietly. A written-out exit reads as a story choice, not a public replacement,
# so it draws from a much smaller range — some grumbling is still possible, just rarely real news.
EXIT_NOTORIETY_COEF_RANGE_RECAST = (0.3, 0.8)
EXIT_NOTORIETY_COEF_RANGE_WRITTEN_OUT = (0.0, 0.15)


def decline_continuation_probability(protectiveness: float) -> float:
    return clamp(
        DECLINE_CONTINUATION_CHANCE_BASE + DECLINE_CONTINUATION_PROTECTIVENESS_COEF * protectiveness, 0.0, 1.0,
    )


def exit_notoriety_delta(exit_type: str, installments_starred: int, rng: random.Random) -> float:
    lo, hi = EXIT_NOTORIETY_COEF_RANGE_RECAST if exit_type == "recast" else EXIT_NOTORIETY_COEF_RANGE_WRITTEN_OUT
    return rng.uniform(lo, hi) * min(installments_starred, 8)


# The same written-out discount applied to a lost holdout's own notoriety hit (leverage.
# indispensability.resolve_holdout's HOLDOUT_FAILURE_NOTORIETY) — that number is about the failed
# negotiation itself, not franchise size, so it isn't rebuilt here, just softened when the studio's
# actual response turns out to be a quiet write-out rather than a visible recast.
WRITEOUT_HOLDOUT_NOTORIETY_DISCOUNT = 0.2


# A studio protecting a proven property, not a modeled character — deliberately independent of
# Indispensability (leverage/indispensability.py), which answers "how hard is *this actor* to
# replace." This answers "how much does the studio value *the property itself*, regardless of who's
# in it" — built entirely off track record already tracked here (installments_starred, prior_
# audience_score), no per-actor read at all. A single hit installment doesn't max this out; it
# takes a real, sustained run to earn full protectiveness, same as an actual long-running franchise.
PROTECTIVENESS_INSTALLMENT_COEF = 9.0
PROTECTIVENESS_INSTALLMENT_CAP = 8
PROTECTIVENESS_AUDIENCE_COEF = 0.7


def studio_protectiveness(franchise: "FranchiseEntry") -> float:
    """How hard the studio holds onto this property once it's proven itself — pulls two real
    levers, both scaled from this one number: it makes the studio LESS willing to give up
    ownership of the property to anyone (leverage.indispensability's streaming-buyout floor), and
    MORE willing to let go of any one person attached to it, including its own star
    (leverage.indispensability.resolve_holdout's recast pull) — the studio protects the property,
    not the individual."""
    installment_term = PROTECTIVENESS_INSTALLMENT_COEF * min(franchise.installments_starred, PROTECTIVENESS_INSTALLMENT_CAP)
    audience_term = PROTECTIVENESS_AUDIENCE_COEF * max(0.0, franchise.prior_audience_score - 50.0)
    return clamp(installment_term + audience_term, 0.0, 100.0)


def spinoff_available(franchise: "FranchiseEntry") -> bool:
    # A character you've been recast out of isn't yours to pitch a new property off of anymore —
    # that standing belongs to whoever's playing the part now (nobody, mechanically), not you.
    return franchise.you_are_current_lead and franchise.indispensability >= SPINOFF_INDISPENSABILITY_THRESHOLD


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
