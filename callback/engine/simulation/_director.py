"""Session-level orchestration of the director career (director/) — fused into the same
FullState/Session as the actor's, rather than a second, parallel Session. Development hell
(director/development.py), a director's own Craft/Efficiency steering the edit
(director/edit.py), and their own Standing (the same core.meters.StandingModel actor/standing.py
already configures — one spine, per design/part-03 §3.3) share the actor's calendar: a year spent
developing or shooting a directed project is a year not spent acting, and vice versa, but Standing
decay, Life, the Guild, and Rolodex re-ranking all still run once a year regardless of which track
you worked, through full_career.advance_between_years exactly as they already do for acting.

Explicitly out of scope for this pass, same as the acting-only build originally was for several
systems: a directed film doesn't participate in the franchise/sequel system (simulation/
_franchises.py). A real, bounded follow-up, not attempted here.

Three actor-side mechanics are ported onto the director track, reusing the same underlying
formulas rather than inventing parallel ones: script notes (a director's own three-of-four —
clarity/ambiguity/whole-film; "your part" doesn't apply, they have no part), a release-strategy
request, and a marketing-push request. The latter two use studios.decide_release_strategy()/
decide_marketing_spend() exactly as the actor path does, but with director_influence_on_studio_
decision() in place of the actor curve — a director asking for their own film starts from a real,
higher floor and climbs faster, though never past the same ceiling an A-list actor already has.
No persistent director-studio relationship is tracked yet (unlike studio_relations on the acting
side) — DIRECTOR_STUDIO_TRUST is a flat, neutral stand-in until that's built out.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field, replace

from callback.engine.actor.rating import near_boundary, rating_band as compute_rating_band, rating_score
from callback.engine.actor.reception import BREAK_EVEN_MARKETING_SHARE, RIGHTS_SHARE, ReceptionResult, resolve_reception
from callback.engine.actor.release import (
    FESTIVAL, LIMITED, RELEASE_STRATEGIES, STREAMING, STREAMING_BUYOUT_MULTIPLIER, WIDE,
    apply_release_strategy, weekly_gross_curve,
)
from callback.engine.core.script_notes import DIRECTOR_SCRIPT_NOTE_OPTIONS, ScriptNoteEffect, apply_script_note
from callback.engine.actor.standing import (
    AFFECTION_DECAY,
    HEAT_KEEP,
    NOTORIETY_DECAY,
    PRESTIGE_DECAY,
    delta_affection,
    delta_heat,
    delta_prestige,
    new_standing_model,
    standing_score,
    star_power,
)
from callback.engine.actor.studios import (
    MARKETING_PUSH_BONUS,
    OPENING_MARKETING_COEF,
    decide_marketing_spend,
    decide_release_strategy,
    director_influence_on_studio_decision,
    marketing_share_for,
    pick_studio,
    quality_adjusted_bids,
    STUDIOS,
)
from callback.engine.core.meters import StandingModel
from callback.engine.core.util import clamp
from callback.engine.leverage.approvals import (
    BOX_OFFICE_BONUS_TYPES,
    DIRECTOR_FEE_SHARE_HIRE_RANGE,
    DIRECTOR_FEE_SHARE_STUDIO_RANGE,
    negotiated_director_fee_share,
    box_office_bonus_earned,
    can_negotiate_box_office_bonus,
    negotiated_bonus_share,
)
from callback.engine.director.attributes import DirectorAttributes, perceived_script_quality
from callback.engine.director import casting as director_casting
from callback.engine.director import shoot_style as director_shoot_style
from callback.engine.director.development import (
    ATTACHMENT_BANKABLE,
    ATTACHMENT_GENRE_FIT,
    ATTACHMENT_TYPES,
    ATTACH_GENRE_FIT_BUDGET_DISCOUNT,
    Attachment,
    DevProject,
    age_attachments,
    apply_action,
    apply_neglect,
    advance_quarter,
    attach_momentum,
    attachment_offer_probability,
    adaptation_momentum,
    adaptation_option_cost,
    apply_event_delta,
    attempt_self_finance,
    bankability_multiplier,
    director_momentum_command_multiplier,
    director_quarters_efficiency_multiplier,
    director_spectacle_bonus,
    format_adjusted_roi,
    initial_momentum,
    MAX_CONCURRENT_SHOOTS,
    quarters_for_directed_film,
    schedule_trust_penalty,
    self_finance_rush_penalty,
    studio_expected_quarters,
    EVENT_MOMENTUM_HI,
    EVENT_MOMENTUM_LO,
    favour_momentum,
    momentum_band,
    package_strength,
    rewrite_quality_gain,
    rival_poach_notoriety_cost,
    SCREENWRITER_SKILL_MEAN,
    SCREENWRITER_SKILL_SD,
    self_finance_buyout_cost,
)

EVENT_PROBABILITY_LO = 0.06
EVENT_PROBABILITY_HI = 0.18

# v12 — a live shoot advances on its own real calendar (simulation.session.Session.end_year()),
# mirrored here rather than imported (session.py's own QUARTERS_PER_YEAR — this module doesn't
# depend upward on simulation.session).
SHOOT_QUARTERS_PER_YEAR = 4
from callback.engine.director.edit import has_final_cut, resolve_edit
from callback.engine.director.skill import director_skill, ENGAGEMENT_PASSION_PROJECT
from callback.engine.genre.franchise import sequel_bonus, spacing_modifier
from callback.engine.simulation._franchises import FranchiseEntry, recast_audience_penalty, studio_protectiveness, writeout_audience_delta
from callback.engine.simulation._relationships import STUDIO_TRUST_UTILITY_COEF, TRUST_DEFAULT, financing_studio_weight, trust_of
from callback.engine.world.genre_cycle import genre_demand as world_genre_demand
from callback.engine.simulation.bands import ROI_BANDS

ATTACH_STAR_BANKABILITY_GAIN = 25.0
NEW_PROJECT_SCRIPT_QUALITY_MEAN = 58.0
NEW_PROJECT_SCRIPT_QUALITY_SD = 14.0
PASSION_PROJECT_STAR_THRESHOLD = 10.0  # under this attached-star bankability, it reads as a passion project
DIRECTOR_STUDIO_TRUST = 50.0  # neutral baseline — no persistent director-studio relationship tracked yet
PROFITABLE_ROI_THRESHOLD = next(lower for lower, label in ROI_BANDS if label == "profitable")
HIRE_FILM_HEAT_MULTIPLIER = 1.25  # §7.13 v10 — real visibility, the studio's own reach behind it
HIRE_FILM_PRESTIGE_MULTIPLIER = 0.70  # commercial work, not your own vision

# director.development.bankability_multiplier's own input — recency-weighted, not a lifetime
# average, so a real recovery actually counts: a director who's turned it around isn't still
# paying for films from a decade ago.
TRAILING_ROI_DECAY = 0.7  # this film's ROI counts for 30% of the new trailing read

# §7.4 v23 — directing had no income mechanic at all: not a studio fee, not a self-financed film's
# own real "you keep all of it" payoff the rights_share=1.0 comment already promised but the code
# never actually credited. Three real shapes, matched to who's actually taking the financial risk:
DIRECTOR_FEE_SHARE_STUDIO = 0.05  # of budget — a modest, real quote for directing someone else's
# film the ordinary way (you pitched it, a studio's financing it)
DIRECTOR_FEE_SHARE_HIRE = 0.08  # a hire's whole point, per §7.10's own "sellout" framing, is a
# bigger guaranteed personal payday in exchange for less creative control — the fee reflects that
# A self-financed film pays neither fee — you ARE the studio, so the real income is the film's own
# net proceeds after covering the costs you already took on (gross*rights_share, less marketing —
# the production budget was already paid out at the moment this film was greenlit).
FINAL_CUT_CONTEST_PRESTIGE_FLOOR = 40.0  # below this, there's no real leverage to contest with —
# not full final cut, but not a total nobody either. Fills a real gap the original §7.7 text left
# unspecified (when a cut is "Contested" rather than flatly the studio's).

# director_shoot_style.overage_percent already computed a real, Efficiency-driven schedule-overrun
# fraction, previously used only to gate final cut eligibility. A schedule overrun IS a real driver
# of real film budget overruns, but not a dollar-for-dollar one — plenty of a production's own cost
# is fixed regardless of how long the shoot runs (sets already built, deals already signed, gear
# already rented at a flat rate), so only part of the extra time actually shows up as extra money.
# v14 — was 1.0 (one-to-one), which at the kind of overage a genuinely bad Efficiency score
# produces (routinely 80-120%) was reliably doubling the real budget — real, but landing as
# absurd rather than "expensive." Dampened so the cost still bites hard, just not literally 1:1.
OVERRUN_BUDGET_COEF = 0.45

# v29 — a real gap the OVERRUN_BUDGET_COEF fix above never closed: overage was a pure MONEY cost,
# with zero path into the finished film's own quality. Worse, actor.reception.resolve_reception's
# role_budget_millions/cost_budget_millions split (added the same pass this closes) means the
# money side is now correctly walled off from production_value()/Opening — but that split alone
# left overage completely quality-NEUTRAL, when a genuinely troubled shoot should sometimes read
# as a worse film, not just a more expensive one. And director.edit.resolve_edit's own "lost the
# cut" path isn't a penalty either — studio_post_luck() carries a small POSITIVE commercial bias
# (STUDIO_ROLL_BIAS=+4), the opposite of "the studio's rushed recut made it worse." Nothing in
# this engine, anywhere, currently makes a bad overrun read as a worse film — only a costlier one.
#
# Three real, already-tracked signals decide who actually takes this hit, rather than one flat
# number applied to everyone:
#  1. self_financed: zero penalty, unconditionally. There's no studio to hand a worse recut to —
#     see overage_stripped_cut's own docstring below for why this can't just reuse has_cut/
#     contested (their own formula never checks self_financed either, a real, separate, older gap
#     this isn't attempting to close).
#  2. overage_stripped_cut: real Prestige/streak/fee-cut can already, on their own, earn a director
#     final cut outright (director.edit.has_final_cut) — but overage_percent's own AND-clause
#     (see has_cut just below) strips that back off the moment the shoot blows past
#     OVERAGE_FINAL_CUT_THRESHOLD, regardless of how earned it was. A director who'd have kept
#     the cut on merit alone and only lost it to their OWN bad scheduling is the real, self-
#     inflicted case this penalty targets. A nobody who was never going to hold the cut either way
#     (no Prestige, no streak, no fee-cut) loses nothing ADDITIONAL to overage specifically —
#     nothing was actually taken from them, so no separate control-tier multiplier is layered on
#     top of Prestige/streak here the way an earlier draft of this fix did (that draft was also
#     quietly double-rewarding Command with a THIRD free bonus on top of its two existing ones —
#     dropped entirely, not carried into this version).
#  3. severity: a continuous ramp, not a step — how far past the threshold the overage actually
#     lands, the same shortfall-ramp shape bankability_multiplier's own shortfall/overage_shortfall
#     terms already use elsewhere in this file.
#  4. efficiency_share: overage_percent (director.shoot_style) is linear/additively separable
#     before its own clamp (0.9*ambition - 0.9*efficiency + 1.0*chaos + noise) — a director whose
#     Efficiency sits at or above the same neutral-50 point this file's OWN DIRECTOR_QUARTERS_EFF_
#     NEUTRAL/MOMENTUM_COMMAND_NEUTRAL already use isn't the one who caused this, even if ambition
#     or an unlucky ensemble pushed the number up anyway — only the shortfall below that neutral
#     point is charged against them.
OVERAGE_QUALITY_PENALTY_CEILING = 16.0  # craft_contribution points, at full severity/efficiency-
# shortfall on a director who'd otherwise have held the cut — sized against this SAME formula's
# own existing deltas (BANKABLE_WRONG_FIT's fit_penalty=18, LONG_TAKES' +10) so the worst case is
# a real, felt hit, not a rounding error, without alone being able to zero out a strong craft_
# contribution reading on its own.
OVERAGE_QUALITY_PENALTY_SPAN = 0.50  # severity reaches 1.0 a full 50 points of overage past the
# final-cut threshold — a real disaster shoot, not a merely-late one.
OVERAGE_QUALITY_PENALTY_EFF_NEUTRAL = 50.0  # matches DIRECTOR_QUARTERS_EFF_NEUTRAL/MOMENTUM_
# COMMAND_NEUTRAL's own neutral-50 convention — an average Efficiency isn't charged at all.


def overage_quality_penalty(
    overage: float, self_financed: bool, overage_stripped_cut: bool, efficiency: float,
) -> float:
    """Returns a real, bounded craft_contribution deduction — 0.0 for the common case (modest
    overage, or a director who was never going to hold the cut regardless, or self-financed).
    Only bites for the specific, self-inflicted case overage_stripped_cut names: real leverage
    that overage itself took away."""
    if self_financed or not overage_stripped_cut:
        return 0.0
    severity = clamp(
        (overage - director_shoot_style.OVERAGE_FINAL_CUT_THRESHOLD) / OVERAGE_QUALITY_PENALTY_SPAN,
        0.0, 1.0,
    )
    efficiency_share = clamp(
        (OVERAGE_QUALITY_PENALTY_EFF_NEUTRAL - efficiency) / OVERAGE_QUALITY_PENALTY_EFF_NEUTRAL, 0.0, 1.0,
    )
    return OVERAGE_QUALITY_PENALTY_CEILING * severity * efficiency_share

# §7.4 v10 — generalized "attach a star": relationship tiers §10.0's Rolodex already tracks.
# Estranged/Severed/Legacy fall back to the cold "stranger" behaviour — the action doesn't crash,
# it just can't reopen that bridge, exactly as the design doc states.
ATTACH_STAR_TIER_FALLBACK = {"estranged": "stranger", "severed": "stranger", "legacy": "stranger"}

# §7.4 v16 — limbo: crossing MOMENTUM_DEATH_FLOOR isn't flatly "the project dies" anymore. What
# actually happens is a real, dynamic mix, read off what's genuinely in the project (how much
# money's already committed, how far under the floor it fell) and who you are (your own Standing —
# real leverage against just being replaced). Every path reuses an existing formula rather than
# inventing a fifth: the self-finance branch below IS attempt_self_finance(), the same free-release/
# buyout/can't-afford roll "self_finance" the dev action already offers, just triggered here as a
# real consequence of neglect instead of only ever a deliberate choice.
LIMBO_MOMENTUM_THRESHOLD = 0.22  # same number as development.MOMENTUM_DEATH_FLOOR — the line a
# project has to fall under (whether from neglect or a bad active quarter) before anything below
# can happen to it at all.
LIMBO_FIRED_BASE = 0.15
LIMBO_FIRED_BUDGET_COEF = 0.12  # more of the studio's money already in it → likelier they just
# replace you and keep going, rather than eat the whole loss (same log-budget shape Difficulty uses)
LIMBO_FIRED_STANDING_RELIEF = 0.20  # your own Standing is real leverage against being the one who
# gets swapped out — a nobody is trivially easy to replace, an in-demand director much less so
LIMBO_CANCELED_BASE = 0.30
LIMBO_CANCELED_SEVERITY_COEF = 0.35  # how far under the floor it's actually fallen, not just that
# it crossed the line — a project barely under is a real save candidate; one that's cratered is
# much likelier to just be scrapped outright
LIMBO_FIRED_NOTORIETY_LO = 3.0
LIMBO_FIRED_NOTORIETY_HI = 10.0  # getting visibly pulled off your own project is a real public cost


def limbo_probabilities(budget_ask: float, director_standing_score: float, severity: float) -> tuple[float, float]:
    """Returns (p_fired, p_canceled). The remaining probability mass (never less than 10%) always
    goes to attempt_self_finance()'s own real shot — every combination of factors still leaves some
    chance the studio just hands it over or names a price, never a guaranteed loss."""
    budget_term = clamp(math.log10(budget_ask + 1.0) / math.log10(101.0), 0.0, 1.0)
    standing_relief = clamp(director_standing_score / 100.0, 0.0, 1.0)
    p_fired = clamp(
        LIMBO_FIRED_BASE + LIMBO_FIRED_BUDGET_COEF * budget_term - LIMBO_FIRED_STANDING_RELIEF * standing_relief,
        0.02, 0.6,
    )
    p_canceled = clamp(LIMBO_CANCELED_BASE + LIMBO_CANCELED_SEVERITY_COEF * clamp(severity, 0.0, 1.0), 0.05, 0.75)
    if p_fired + p_canceled > 0.9:
        scale = 0.9 / (p_fired + p_canceled)
        p_fired *= scale
        p_canceled *= scale
    return p_fired, p_canceled


@dataclass(frozen=True)
class LimboOutcome:
    kind: str  # "fired" | "canceled" | "handed_free" | "buyout_paid" | "could_not_afford"
    project: DevProject | None  # None whenever the project is gone (fired/canceled/could_not_afford)
    cost_paid: float = 0.0
    buyout_offered: float = 0.0  # what a "could_not_afford" outcome would have cost, for the player to see


def resolve_limbo(
    project: DevProject, director_standing_score: float, available_money: float, rng: random.Random,
    years_since_last_release: int = 0,
) -> LimboOutcome:
    severity = clamp((LIMBO_MOMENTUM_THRESHOLD - project.momentum) / LIMBO_MOMENTUM_THRESHOLD, 0.0, 1.0)
    p_fired, p_canceled = limbo_probabilities(project.budget_ask, director_standing_score, severity)
    roll = rng.random()
    if roll < p_canceled:
        return LimboOutcome("canceled", None)
    if roll < p_canceled + p_fired:
        return LimboOutcome("fired", None)
    outcome = attempt_self_finance(project, rng, available_money, years_since_last_release)
    if outcome.acquired:
        kind = "handed_free" if outcome.released_free else "buyout_paid"
        # No longer dying — it's safely yours now, the same "acquisition is its own beat, making
        # the film is a later action" two-step attempt_self_finance's own docstring already spells
        # out for the deliberate self_finance action; a limbo-triggered acquisition follows the
        # same rule rather than a special-cased instant resolution.
        saved_project = replace(outcome.project, dead=False)
        return LimboOutcome(kind, saved_project, cost_paid=outcome.cost_paid)
    return LimboOutcome(
        "could_not_afford", None,
        buyout_offered=self_finance_buyout_cost(project.budget_ask, project.installment_number, years_since_last_release),
    )


# §7.4 v16 — the slate: a director works on however many projects they can juggle, and pays for
# neglecting any of them, rather than being locked to a single one gated behind Standing. A flat,
# always-available cap keeps the list from growing without bound (§0.1's own "too many options"
# discipline), but nothing about *starting* a second or third project depends on reputation — the
# real cost of running more than one is apply_neglect()'s own momentum decay, not a capacity gate.
MAX_PROJECTS = 4


@dataclass(frozen=True)
class ProjectSlot:
    """One project in development, bundled with everything specific to it — every project is a
    ProjectSlot, there's no separate "the active one." Which slot gets this quarter's real action
    is a per-call choice (apply_dev_action_and_advance's project_index), not a standing field."""
    project: DevProject
    genre: str
    true_script_quality: float
    perceived_script_quality: float = 50.0  # v21 -- director.attributes.perceived_script_quality
    # ("Taste makes you see clearly") existed but was never actually wired to anything anywhere in
    # the engine -- a real, previously-dead mechanic. Rolled fresh (with the director's own Taste)
    # whenever true_script_quality actually changes (project creation, "rewrite"), then carried
    # forward unchanged otherwise -- never recomputed live at read time, matching director_status()'s
    # own RNG-free, pure-read convention.
    pending_script_note: ScriptNoteEffect = field(default_factory=ScriptNoteEffect)
    pending_release_request: str | None = None
    pending_marketing_push: bool = False
    pending_casting_choice: str = director_casting.YOUR_ROSTER
    pending_shoot_style: str = director_shoot_style.LEAN_AND_FAST
    took_fee_cut_for_cut: bool = False


@dataclass(frozen=True)
class DirectorState:
    attrs: DirectorAttributes = DirectorAttributes()
    standing: StandingModel = None  # set to new_standing_model() by new_director_state()
    credits: int = 0
    consecutive_profitable_films: int = 0
    projects: tuple[ProjectSlot, ...] = ()  # §7.4 v16 — every project currently in development
    trailing_roi: float = 1.0  # director.development.bankability_multiplier's own input — a
    # recency-weighted read of recent ROI (TRAILING_ROI_DECAY below), not a lifetime average, so an
    # old flop streak a director has since recovered from doesn't haunt them forever. 1.0
    # (breakeven) is the neutral starting point — a brand-new director carries no bankability
    # penalty at all until they actually establish a real track record, good or bad.
    trailing_overage: float = 0.0  # v18 — same shape as trailing_roi, reading schedule_overage
    # instead: a real "reputation for being expensive" that used to only cost trust with the ONE
    # studio actually burned (schedule_trust_penalty/financing_studio_weight). This is the missing
    # career-wide half — a chronically late/over-budget director should find EVERY studio warier on
    # the next big ask, not just the one they already burned. 0.0 (on schedule) is neutral.


def new_director_state() -> DirectorState:
    return DirectorState(standing=new_standing_model())


def projects_in_play(state: DirectorState) -> int:
    return len(state.projects)


def can_start_new_project(state: DirectorState) -> bool:
    return len(state.projects) < MAX_PROJECTS


# v20 — a director's fee used to negotiate off Standing alone, the same single lever the box-
# office bonus already uses. A real salary negotiation reads more than fame: a track record of
# actually making money (trailing_roi — the same read bankability_multiplier already uses),
# reliability (trailing_overage, inverted — the same read that same function's overage penalty
# uses), and a real hot streak (consecutive_profitable_films) all genuinely move what a studio
# offers, on top of raw Standing. Kept as a separate composite from the bonus/financing-studio
# director_leverage above rather than swapping that one out too — a bonus is closer to "are you
# famous enough that we owe you backend," a fee is closer to "what do you cost us," and those are
# real, different questions a studio asks.
DIRECTOR_FEE_LEVERAGE_STANDING_WEIGHT = 0.50
DIRECTOR_FEE_LEVERAGE_ROI_WEIGHT = 0.25
DIRECTOR_FEE_LEVERAGE_STREAK_WEIGHT = 0.15
DIRECTOR_FEE_LEVERAGE_OVERAGE_PENALTY_WEIGHT = 0.20
DIRECTOR_FEE_LEVERAGE_STREAK_SATURATION = 5.0  # consecutive profitable films for the full streak bonus


def director_fee_leverage(state: DirectorState) -> float:
    standing_component = clamp(standing_score(state.standing) / 100.0, 0.0, 1.0)
    # trailing_roi=1.0 (breakeven) reads as neutral (0.5); a real hit streak pulls toward 1.0, a
    # real loss streak pulls toward 0.0 — the same ROI_CENTRE=1.0 framing bankability_multiplier
    # already uses, just read as a bonus instead of a penalty.
    roi_component = clamp(0.5 + (state.trailing_roi - 1.0) * 0.5, 0.0, 1.0)
    streak_component = clamp(state.consecutive_profitable_films / DIRECTOR_FEE_LEVERAGE_STREAK_SATURATION, 0.0, 1.0)
    overage_penalty = clamp(state.trailing_overage, 0.0, 1.0)
    raw = (
        DIRECTOR_FEE_LEVERAGE_STANDING_WEIGHT * standing_component
        + DIRECTOR_FEE_LEVERAGE_ROI_WEIGHT * roi_component
        + DIRECTOR_FEE_LEVERAGE_STREAK_WEIGHT * streak_component
        - DIRECTOR_FEE_LEVERAGE_OVERAGE_PENALTY_WEIGHT * overage_penalty
    )
    return clamp(raw, 0.0, 1.0)


def _pick_financing_studio(budget_ask: float, studio_relations: dict, rng: random.Random):
    """Same budget-fit gate pick_studio() (actor/studios.py) already uses, but weighted by
    financing_studio_weight — a studio you've burned on schedule overruns is less likely to be the
    one who calls next, and one that trusts you is more likely to, so bad-Efficiency trust damage
    actually compounds career-long instead of getting wiped by a fresh, uniformly-random studio
    every single project."""
    fits = [s for s in STUDIOS.values() if s.budget_range[0] <= budget_ask <= s.budget_range[1]]
    if not fits:
        return STUDIOS["mid_major"]
    weights = [financing_studio_weight(trust_of(studio_relations, s.id)) for s in fits]
    return rng.choices(fits, weights=weights, k=1)[0]


PLAYER_DIRECTOR_ID = "__you__"  # v27 — simulation._franchises.FranchiseEntry.last_director_npc_id
# expects a real NPC id (a director-for-hire's own continuity, actor-track only); the player
# directing their own franchise has no npc_id of their own, so this sentinel stands in for "the
# player themselves directed the prior installment" wherever that comparison is made.


def start_development(
    state: DirectorState, genre: str, budget_ask: float, rng: random.Random,
    self_financed: bool = False, studio_relations: dict | None = None,
    franchise: FranchiseEntry | None = None, current_year: int = 0, new_franchise: bool = False,
    cast_decision: str | None = None,
) -> DirectorState:
    """Appends a new project to the slate. A no-op if can_start_new_project() is already False —
    callers (Session) should check first to give the player a real reason, but this stays safe
    either way. Never displaces anything already in development.

    self_financed: §7.4 v22 — a genuinely independent project, no studio ever attached, not one
    later bought out of an existing deal (the "self_finance" dev action's own two-step acquisition
    — see attempt_self_finance's own docstring — is a *different* path onto the same flag). Starts
    exactly where a buyout lands: project.self_financed=True routes it through the same "no one
    else's yes to wait on" branch apply_dev_action_and_advance already gives any self-financed
    project — the very next action taken resolves the film outright, the same real trade a mid-
    development buyout already carries (no development runway left to build momentum/script
    quality first; the whole budget comes out of your own money the moment it's made, whether or
    not you can actually afford it — see Session.advance_directing's own net-worth deduction, the
    same one an acquired-then-resolved project already goes through).

    franchise: v27 — directors now participate in the SAME shared FullState.franchises pool the
    actor track already uses, not a second system. Pass an existing FranchiseEntry to pitch the
    next installment (genre is overridden to the franchise's own, matching how a sequel role's
    genre already works on the actor side) — this locks in genre.franchise.sequel_bonus +
    spacing_modifier, plus director_continuity_bonus's own passion-project engagement bump if the
    player directed the prior installment themselves (PLAYER_DIRECTOR_ID). new_franchise=True
    starts a brand-new property instead — installment 1, no bonus yet (nothing to be a sequel to),
    the same "not registered in the shared dict until the first installment actually resolves"
    shape update_franchise_after_project already establishes for the actor path.

    cast_decision: v28 — compartmentalized from the franchise-bonus block above; only meaningful
    alongside a real `franchise` (a sequel pitch). "recast"/"write_out" reuse simulation._
    franchises' own recast_audience_penalty/writeout_audience_delta — the SAME two real outcomes
    a lost actor holdout already resolves through, just director-initiated this time instead of
    triggered by an actor's own leverage failure. None (or any other value) means "keep the
    returning cast" — no penalty, no roll, the default."""
    if not can_start_new_project(state):
        return state
    screenwriter_skill = clamp(rng.gauss(SCREENWRITER_SKILL_MEAN, SCREENWRITER_SKILL_SD), 0.0, 100.0)
    bonus_type, bonus_share = None, 0.0
    financing_studio_id = None
    negotiated_fee_share = None
    franchise_id = None
    installment_number = 1
    locked_franchise_bonus = 0.0
    if franchise is not None:
        genre = franchise.genre
        franchise_id = franchise.franchise_id
        installment_number = franchise.installments_starred + 1
        years_since_last = current_year - franchise.last_installment_year
        continuity = ENGAGEMENT_PASSION_PROJECT if franchise.last_director_npc_id == PLAYER_DIRECTOR_ID else 0.0
        locked_franchise_bonus = sequel_bonus(installment_number, franchise.prior_audience_score) + spacing_modifier(installment_number, years_since_last) + continuity
        if cast_decision == "recast":
            locked_franchise_bonus -= recast_audience_penalty(studio_protectiveness(franchise), rng)
        elif cast_decision == "write_out":
            locked_franchise_bonus += writeout_audience_delta(rng)
    elif new_franchise:
        franchise_id = f"fr_{rng.randrange(10**6):06d}"
    if not self_financed:
        # §7.4 v24 — a real negotiated backend for a studio-backed director, same Standing-gated,
        # ranged-share shape actor/leverage already uses. Self-financed already keeps full net
        # proceeds (see the income block in _resolve_directed_film); a hire's flat "sellout" fee is
        # its own separate trade (§7.10) and doesn't stack a second bonus on top.
        director_leverage = clamp(standing_score(state.standing) / 100.0, 0.0, 1.0)
        for candidate in BOX_OFFICE_BONUS_TYPES:
            if can_negotiate_box_office_bonus(standing_score(state.standing), candidate):
                bonus_type = candidate
                bonus_share = negotiated_bonus_share(candidate, director_leverage, rng)
                break  # first_dollar_gross checked first — take the harder-to-get, better deal
        negotiated_fee_share = negotiated_director_fee_share(DIRECTOR_FEE_SHARE_STUDIO_RANGE, director_fee_leverage(state), rng)
        # v11 fix — the studio you're actually courting is real from day one, not a random pick
        # conjured fresh only once you're already greenlit. Lets a real, existing studio_relations
        # trust read actually influence THIS project's own greenlight odds (apply_dev_action_and_
        # advance), and lets _resolve_directed_film use the SAME studio it was scored against
        # instead of silently re-rolling a different one at the last second.
        financing_studio_id = _pick_financing_studio(budget_ask, studio_relations or {}, rng).id
    project = DevProject(
        script_id=f"d_{rng.randrange(10**6):06d}", budget_ask=budget_ask, screenwriter_skill=screenwriter_skill,
        momentum=initial_momentum(standing_score(state.standing)),
        self_financed=self_financed, box_office_bonus_type=bonus_type, box_office_bonus_share=bonus_share,
        negotiated_fee_share=negotiated_fee_share, financing_studio_id=financing_studio_id,
        franchise_id=franchise_id, installment_number=installment_number,
        locked_franchise_audience_bonus=locked_franchise_bonus,
    )
    quality = clamp(rng.gauss(NEW_PROJECT_SCRIPT_QUALITY_MEAN, NEW_PROJECT_SCRIPT_QUALITY_SD), 0.0, 100.0)
    perceived_quality = perceived_script_quality(quality, state.attrs.taste, rng)
    slot = ProjectSlot(project=project, genre=genre, true_script_quality=quality, perceived_script_quality=perceived_quality)
    return replace(state, projects=state.projects + (slot,))


def scrap_project(state: DirectorState, project_index: int) -> DirectorState:
    """§7.4 v16 — real, no-cost, no-roll permission to just walk away and free the slot, distinct
    from "drawer" (which freezes a project in place but keeps its slot, in case a stalled deal is
    worth reviving later). scrap_project drops it outright."""
    if project_index < 0 or project_index >= len(state.projects):
        return state
    return replace(state, projects=state.projects[:project_index] + state.projects[project_index + 1:])


def choose_director_casting(state: DirectorState, project_index: int, choice: str) -> DirectorState:
    if choice not in director_casting.CASTING_CHOICES or project_index < 0 or project_index >= len(state.projects):
        return state
    projects = list(state.projects)
    projects[project_index] = replace(projects[project_index], pending_casting_choice=choice)
    return replace(state, projects=tuple(projects))


def choose_director_shoot_style(state: DirectorState, project_index: int, style: str) -> DirectorState:
    if style not in director_shoot_style.SHOOT_STYLES or project_index < 0 or project_index >= len(state.projects):
        return state
    projects = list(state.projects)
    projects[project_index] = replace(projects[project_index], pending_shoot_style=style)
    return replace(state, projects=tuple(projects))


def request_final_cut_fee_cut(state: DirectorState, project_index: int) -> DirectorState:
    """§7.7 — final cut can be earned outright by taking a real fee cut, independent of Prestige or
    a profitable streak. A one-time, explicit trade, not a standing condition."""
    if project_index < 0 or project_index >= len(state.projects):
        return state
    projects = list(state.projects)
    projects[project_index] = replace(projects[project_index], took_fee_cut_for_cut=True)
    return replace(state, projects=tuple(projects))


def director_deal_available(state: DirectorState, project_index: int) -> bool:
    """§7.4 v25 — the director's own mirror of the actor's Deal screen: whether this project can
    still push for a real backend against a lower guaranteed base rate. Off the table for a
    project already self-financed (there's no studio fee to trade away — you already keep
    everything) or a for-hire guaranteed greenlight (§7.10's flat "sellout" fee is its own
    separate, already-better trade, not stacked with this one)."""
    if project_index < 0 or project_index >= len(state.projects):
        return False
    project = state.projects[project_index].project
    return not project.self_financed and not project.guaranteed_greenlight


def director_box_office_bonus_available(state: DirectorState, bonus_type: str) -> bool:
    """Same Standing bar box_office_bonus_available() already reads for an actor — see
    can_negotiate_box_office_bonus's own docstring for why first_dollar_gross needs real Standing
    above net_points."""
    return can_negotiate_box_office_bonus(standing_score(state.standing), bonus_type)


def push_director_deal_for_backend(
    state: DirectorState, project_index: int, bonus_type: str, rng: random.Random,
) -> DirectorState:
    """The deliberate ask start_development() never rolls for free: pins this project's own
    negotiated fee to DIRECTOR_FEE_SHARE_STUDIO_RANGE's own floor — real money given up, not a
    free upgrade — for a real shot at the box-office bonus can_negotiate_box_office_bonus() would
    otherwise only grant automatically to a high-Standing director at project creation. Same trade
    shape as leverage.approvals.fee_after_approvals on the acting side: less guaranteed, more
    upside, both real. A no-op (returns state unchanged) if director_deal_available() or
    director_box_office_bonus_available() says no — mirrors choose_deal()'s own quiet gating."""
    if not director_deal_available(state, project_index) or not director_box_office_bonus_available(state, bonus_type):
        return state
    leverage = clamp(standing_score(state.standing) / 100.0, 0.0, 1.0)
    bonus_share = negotiated_bonus_share(bonus_type, leverage, rng)
    floor_fee_share, _hi = DIRECTOR_FEE_SHARE_STUDIO_RANGE
    slot = state.projects[project_index]
    new_project = replace(
        slot.project, negotiated_fee_share=floor_fee_share, box_office_bonus_type=bonus_type, box_office_bonus_share=bonus_share,
    )
    projects = list(state.projects)
    projects[project_index] = replace(slot, project=new_project)
    return replace(state, projects=tuple(projects))


def choose_director_script_note(state: DirectorState, project_index: int, choice: str, rng: random.Random) -> DirectorState:
    """A director's own notes pass — see DIRECTOR_SCRIPT_NOTE_OPTIONS for the three real choices.
    script_quality_delta applies immediately (same as a rewrite); the audience/critic deltas are
    held until the film actually resolves (see _resolve_directed_film). v21 — perceived_script_
    quality rerolls here too, same as a rewrite, since true_script_quality genuinely moved."""
    if choice not in DIRECTOR_SCRIPT_NOTE_OPTIONS or project_index < 0 or project_index >= len(state.projects):
        return state
    effect = apply_script_note(choice)
    slot = state.projects[project_index]
    new_quality = clamp(slot.true_script_quality + effect.script_quality_delta, 0.0, 100.0)
    new_perceived_quality = perceived_script_quality(new_quality, state.attrs.taste, rng)
    projects = list(state.projects)
    projects[project_index] = replace(
        slot, true_script_quality=new_quality, perceived_script_quality=new_perceived_quality, pending_script_note=effect,
    )
    return replace(state, projects=tuple(projects))


def request_director_release(state: DirectorState, project_index: int, strategy: str) -> DirectorState:
    """A request, not a command — resolved the same way an actor's is, at greenlight time, via
    decide_release_strategy() and director_influence_on_studio_decision()."""
    if strategy not in RELEASE_STRATEGIES or project_index < 0 or project_index >= len(state.projects):
        return state
    projects = list(state.projects)
    projects[project_index] = replace(projects[project_index], pending_release_request=strategy)
    return replace(state, projects=tuple(projects))


def request_director_marketing_push(state: DirectorState, project_index: int) -> DirectorState:
    if project_index < 0 or project_index >= len(state.projects):
        return state
    projects = list(state.projects)
    projects[project_index] = replace(projects[project_index], pending_marketing_push=True)
    return replace(state, projects=tuple(projects))


def _resolve_directed_film(
    state: DirectorState, slot: ProjectSlot, project: DevProject, genre: str, genre_demand: float, rng: random.Random,
) -> tuple[ReceptionResult, str, bool, float, float, str | None]:
    """Returns (reception, actual_release_strategy, marketing_push_honored, effective_budget,
    schedule_overage, financing_studio_id).

    effective_budget/schedule_overage — director.shoot_style.overage_percent already computed a
    real, Efficiency-driven "went over schedule" fraction (ambition/chaos push it up, Efficiency
    pulls it down, no correlation with Heat anywhere in that formula) but never actually cost
    anything before this — it only gated the final-cut threshold. Real film economics: a schedule
    overrun IS the mechanism behind most real budget overruns, so a positive overage now inflates
    the real budget the film's own reception/ROI reads, one-for-one. Coming in under schedule
    (negative overage) never discounts it — nobody hands back unspent money; see OVERRUN_BUDGET_
    COEF below. financing_studio_id is None for a self-financed or hire-guaranteed project (no
    studio relationship to speak of); the caller (simulation.session.Session.advance_directing)
    feeds it into the same studio_relations trust ledger the acting track already builds — a
    director who burns a studio with a bad overrun is burning the same relationship their acting
    career would feel too, not a second, disconnected number.

    A self-financed project (project.self_financed) skips the studio entirely — there's no one to
    negotiate marketing spend or release strategy with, because there's no one else's money in the
    film. Every call a studio would normally make (how much to spend marketing it, how wide to
    release it, and the full rights_share that would otherwise go to a financing studio) is
    genuinely the director's own instead of a request that can be overruled; the tradeoff for that
    control is real (apply_dev_action_and_advance deducts the whole budget from the director's own
    money the moment this resolves).

    §7.5/§7.6/§7.7 v10 — Casting, the Shoot, and the Edit now resolve as three real formula calls
    instead of a single blind sample apiece, reading slot.pending_casting_choice/pending_shoot_style
    (set once per project, §7.4 v16's own per-ProjectSlot fields) and project.attached_star_bankability
    — the star attached in development, if any, IS the Casting lead per design/part-07 §7.4's own
    reconciliation note, not a second, disconnected pick."""
    cast_result = director_casting.resolve_casting(
        slot.pending_casting_choice, project.attached_star_bankability, rng,
    )
    passion_project = project.attached_star_bankability < PASSION_PROJECT_STAR_THRESHOLD
    skill = director_skill(state.attrs, passion_project, rng)

    style_result = director_shoot_style.resolve_shoot_style(
        slot.pending_shoot_style, instinct=state.attrs.vision, craft=state.attrs.craft,
    )
    base_chaos = cast_result.chaos_delta + director_shoot_style.ensemble_chaos_total(project.attachments)
    # director.shoot_style.overage_percent's v11 fix: chaos is already the fractional read
    # ensemble_chaos_total/cast_result.chaos_delta naturally produce — no more redundant *100
    # pre-scale (that was half of the old unit-mismatch bug).
    overage = director_shoot_style.overage_percent(
        ambition=state.attrs.vision, chaos=base_chaos, efficiency=state.attrs.efficiency, rng=rng,
    )
    # Hoisted up from where `has_cut` used to compute this inline (see overage_quality_penalty's
    # own docstring) — real Prestige/streak/fee-cut can earn final cut outright, but a bad-enough
    # overage strips it back off regardless of how earned it was. Needed here, before craft_
    # contribution is finalized, so a director who lost real, earned leverage specifically to their
    # own scheduling failure takes a real quality hit for it, not just a budget one.
    would_have_earned_cut = has_final_cut(
        state.standing["prestige"], state.consecutive_profitable_films, slot.took_fee_cut_for_cut,
    )
    overage_stripped_cut = would_have_earned_cut and overage > director_shoot_style.OVERAGE_FINAL_CUT_THRESHOLD
    rush_penalty = (
        self_finance_rush_penalty(project.locked_momentum_at_greenlight, project.budget_ask)
        if project.self_financed and project.locked_momentum_at_greenlight is not None
        else 0.0
    )
    craft_contribution = clamp(
        55.0 + 0.10 * state.attrs.command + style_result.craft_contribution_delta - cast_result.fit_penalty
        - overage_quality_penalty(overage, project.self_financed, overage_stripped_cut, state.attrs.efficiency)
        - rush_penalty,
        0.0, 100.0,
    )
    cast_star_power = cast_result.cast_star_power

    has_cut = would_have_earned_cut and overage <= director_shoot_style.OVERAGE_FINAL_CUT_THRESHOLD
    # "Contested" only when there's real leverage to contest with (some Prestige, just not enough
    # for outright final cut) — a total newcomer has nothing to contest, it's flatly the studio's
    # cut. A gap the original v8/v9 text left unspecified; filled here rather than left undefined.
    contested = (not has_cut) and state.standing["prestige"] > FINAL_CUT_CONTEST_PRESTIGE_FLOOR
    edit_outcome = resolve_edit(state.attrs.craft, state.attrs.efficiency, has_cut, contested, rng)
    steered_luck = edit_outcome.post_luck

    # v11 fix — reuse the same studio project.financing_studio_id already names (set at
    # start_development()/accept_hire_offer() time) instead of re-rolling a fresh one here. Before
    # this, the studio a project's greenlight/trust could theoretically be scored against and the
    # studio that actually ends up financing the film could silently be two different ones.
    financing_studio_id = project.financing_studio_id
    if project.self_financed:
        marketing_share = BREAK_EVEN_MARKETING_SHARE + (MARKETING_PUSH_BONUS if slot.pending_marketing_push else 0.0)
        rights_share = 1.0  # no studio anywhere in this film's money — you keep all of it
        festival_tier_bonus = 0.0
        # No outside studio to sell it to and no financing studio's own delta to read either — the
        # actor track's own real-buyer auction (quality_adjusted_bids) doesn't apply when there's
        # no seller in the transaction; the flat base rate is the honest answer here, same as it
        # always was.
        streaming_multiplier = STREAMING_BUYOUT_MULTIPLIER
        actual_strategy = slot.pending_release_request or WIDE  # your call, not a request
        push_honored = slot.pending_marketing_push  # your own money, your own campaign — always honored
    else:
        studio = STUDIOS[financing_studio_id] if financing_studio_id is not None else pick_studio(project.budget_ask, rng)
        financing_studio_id = studio.id
        director_importance = standing_score(state.standing)
        marketing = decide_marketing_spend(
            studio, project.budget_ask, DIRECTOR_STUDIO_TRUST, star_power(state.standing), genre_demand,
            is_franchise_or_adaptation=project.is_adaptation, requested_push=slot.pending_marketing_push, rng=rng,
            influence_fn=director_influence_on_studio_decision,
        )
        marketing_share = marketing.marketing_share
        rights_share = RIGHTS_SHARE + studio.rights_share_delta
        festival_tier_bonus = studio.festival_tier_bonus
        # Real streaming_multiplier is resolved below, after reception (real quality) is known —
        # see the quality_adjusted_bids call past resolve_reception(). None here is just "not
        # computed yet," never actually read by apply_release_strategy unless something's wrong.
        streaming_multiplier = None
        actual_strategy = decide_release_strategy(
            studio, slot.pending_release_request or WIDE, DIRECTOR_STUDIO_TRUST, director_importance, rng,
            influence_fn=director_influence_on_studio_decision,
        )
        push_honored = marketing.push_honored

    # The studio (or your own pocket, if self-financed) was picked/budgeted against project.
    # budget_ask, the original pitch — nobody knows about an overrun until the shoot actually runs
    # long. The REAL economics (what the film actually cost) use the inflated effective_budget —
    # but only for the money side. What the film reads as WORTH, to critics and audiences alike
    # (production_value()'s contribution to project_quality, and Opening, both real, positive
    # channels) stays keyed to the film's own planned scale (project.budget_ask), never the
    # overrun on top of it — an overrun is Efficiency's own real cost, not a quiet, unintended
    # bonus to how big or how polished the finished film reads. See resolve_reception's own
    # cost_budget_millions docstring for the full accounting. Never discounted for finishing
    # early — OVERRUN_BUDGET_COEF only ever applies to the positive side of overage.
    effective_budget = project.budget_ask * (1.0 + OVERRUN_BUDGET_COEF * max(0.0, overage))

    reception = resolve_reception(
        script_quality=slot.true_script_quality,
        director_skill=skill,
        craft_contribution=craft_contribution,
        genre=genre,
        role_budget_millions=project.budget_ask,
        cost_budget_millions=effective_budget,
        director_prestige=state.standing["prestige"],
        staleness_penalty=0.0,
        cast_star_power=cast_star_power,
        genre_demand=genre_demand,
        rng=rng,
        palette_audience_effect=slot.pending_script_note.audience_delta + project.locked_franchise_audience_bonus,
        palette_critic_effect=slot.pending_script_note.critic_delta,
        marketing_share=marketing_share,
        rights_share=rights_share,
        opening_marketing_coef=OPENING_MARKETING_COEF,
        post_luck_override=steered_luck,
        director_spectacle_bonus=director_spectacle_bonus(state.attrs.vision),
    )
    if streaming_multiplier is None:
        # §7.10 v26 — matches the acting track's own resolve_release_schedule exactly: the sale
        # happens after the film's real quality is known, not before. quality_adjusted_bids()
        # already includes the financing studio's own two moves — sell it themselves at the same
        # quality-scaled rate an outside buyer would, or just self-distribute it at
        # SELF_DISTRIBUTE_MULTIPLIER (1.0, true breakeven, always on the table) — so a director's
        # own bad film can genuinely land at a real 1.0x ROI instead of always clearing the flat
        # STREAMING_BUYOUT_MULTIPLIER floor regardless of how it turned out. No interactive
        # bid-picker here (a directed film resolves in one shot at end_year(), same as it always
        # has) — auto-accepts the best payout, same default choose_release() falls back to.
        if actual_strategy == STREAMING:
            bids = quality_adjusted_bids(
                project.budget_ask, financing_studio_id, reception.film_critic_score, reception.audience_score, rng,
            )
            streaming_multiplier = max(bids, key=lambda b: b.payout_millions).multiplier
        else:
            streaming_multiplier = STREAMING_BUYOUT_MULTIPLIER  # unused by apply_release_strategy
            # outside a STREAMING strategy — a harmless placeholder, not a real economic value.
    resolved = apply_release_strategy(
        reception, actual_strategy, rng, cast_star_power=cast_star_power,
        festival_tier_bonus=festival_tier_bonus,
        marketing_share=marketing_share, rights_share=rights_share,
        streaming_multiplier=streaming_multiplier,
    )
    return resolved, actual_strategy, push_honored, effective_budget, overage, financing_studio_id


def apply_dev_action_and_advance(
    state: DirectorState, project_index: int, action: str, genre_demand: float, rng: random.Random,
    available_money: float = 0.0,
    attach_star_target_tier: str | None = None,
    attach_star_target_bankability: float | None = None,
    attach_star_target_npc_id: str | None = None,
    attach_attachment_type: str | None = None,
    attach_star_rivalry_depth: float = 0.5,
    favour_size: float = 3.0,
    licensing_cost_fraction: float = 0.5,
    adaptation_source_type: str = "novel",
    genre_heat_signal: float | None = None,
    has_tracked_rival_same_genre: bool = False,
    studio_trust: float = TRUST_DEFAULT,
    current_year: int = 0,
    franchise_last_release_year: dict | None = None,
) -> tuple[DirectorState, dict]:
    """One quarter's directing work: apply the chosen development action to state.projects[project_
    index], attempt a greenlight, and resolve the film immediately if it lands. Every *other*
    project in state.projects pays real neglect this same quarter (development.apply_neglect — the
    same momentum decay/death-floor shape a failed active roll already applies) — the real cost of
    running more than one project at once, §7.4 v16's replacement for gating project count behind
    Standing. Any project, worked or neglected, that crosses LIMBO_MOMENTUM_THRESHOLD this quarter
    resolves through resolve_limbo() — fired, canceled, handed over free, or bought out, a real
    dynamic mix read off the project's own budget/momentum and the director's own Standing, never a
    flat "the project dies."

    available_money: the director's own current net worth (Session's to know, not DirectorState's —
    this module stays money-agnostic otherwise), consulted for both a deliberate "self_finance"
    action and any limbo resolution that offers a buyout this same quarter (a running total, so two
    limbo buyouts in the same quarter can't both claim the same money).

    §7.4 v10 — attach_star_target_tier/attach_star_target_bankability: the real Rolodex relationship
    state and Bankability of whoever "attach_star" targets (the generalized action). None defaults
    to a flat "stranger" tier at Bankability 50 — the same neutral fallback a headless caller (tests,
    verify.py) gets without needing real Rolodex context. attach_star_rivalry_depth only matters when
    tier == "rival". favour_size/licensing_cost_fraction scale "call_in_favour"/"option_adaptation".
    genre_heat_signal/has_tracked_rival_same_genre feed this quarter's development-event roll — the
    event's own odds/type selection happens here, in simulation/, never inside director/development.py,
    which stays a generic formula module reading no world state of its own. genre_heat_signal=None
    falls back to reading genre_demand itself (already the real, normalized GenreHeat reading a
    caller with no separate raw signal can reuse).

    current_year/franchise_last_release_year: Session's to know (FullState.franchises' own real
    calendar), same "this module stays money/world-agnostic otherwise" convention available_money
    already follows — read live, at self_finance/limbo-buyout time, by whichever project(s) this
    quarter's neglect or a deliberate self_finance action actually touches, not locked at
    project-creation time. franchise_last_release_year=None (a headless caller with no real
    franchise ledger) reads as "just released" for every project — no dormancy discount, same as
    an original."""
    def _years_since_last_release(p: DevProject) -> int:
        if p.franchise_id is None or not franchise_last_release_year:
            return 0
        last = franchise_last_release_year.get(p.franchise_id)
        return 0 if last is None else max(0, current_year - last)

    if project_index < 0 or project_index >= len(state.projects):
        return state, {"error": "no such project", "greenlit": False, "dead": False, "frozen": False, "limbo_events": []}
    if state.projects[project_index].project.quarters_remaining_in_shoot is not None:
        # v12 — already shooting; nothing left to develop. It advances on its own real calendar
        # (advance_shoots_and_resolve, called once a year from Session.end_year()), not through a
        # dev action spent on it.
        p = state.projects[project_index].project
        return state, {
            "error": "already shooting", "greenlit": False, "dead": False, "frozen": False,
            "shooting": True, "quarters_remaining_in_shoot": p.quarters_remaining_in_shoot,
            "momentum": round(p.momentum, 2), "momentum_band": momentum_band(p.momentum),
            "dropped_attachments": [], "attachment_offer_accepted": None, "limbo_events": [],
        }

    remaining_money = available_money
    adaptation_cost_added = 0.0
    limbo_events: list[dict] = []

    def _fire_notoriety_hit(inner_state: DirectorState) -> DirectorState:
        hit = LIMBO_FIRED_NOTORIETY_LO + (LIMBO_FIRED_NOTORIETY_HI - LIMBO_FIRED_NOTORIETY_LO) * rng.random()
        standing = inner_state.standing.copy()
        standing.add("notoriety", hit)
        return replace(inner_state, standing=standing)

    slot = state.projects[project_index]
    project = slot.project
    genre = slot.genre
    true_quality = slot.true_script_quality
    perceived_quality = slot.perceived_script_quality
    notoriety_delta = 0.0
    self_finance_info = None

    if action == "self_finance" and not project.self_financed:
        # Acquiring the project is its own beat, distinct from actually making the film — a studio
        # that hasn't let go yet isn't going to also greenlight it the same quarter you buy them out.
        years_dormant = _years_since_last_release(project)
        outcome = attempt_self_finance(project, rng, remaining_money, years_dormant)
        remaining_money -= outcome.cost_paid
        project = outcome.project
        self_finance_info = {
            "greenlit": False, "dead": False, "frozen": False, "momentum": round(project.momentum, 2),
            "momentum_band": momentum_band(project.momentum),
            "self_finance_acquired": outcome.just_acquired,
            "self_finance_released_free": outcome.released_free,
            "self_finance_cost_paid": outcome.cost_paid,
            "self_finance_could_not_afford": outcome.could_not_afford,
            "self_finance_buyout_cost": self_finance_buyout_cost(project.budget_ask, project.installment_number, years_dormant),
        }
        dropped_attachments = ()
        attachment_offer_accepted = None
    else:
        dropped_attachments = ()
        attachment_offer_accepted = None
        momentum_before_action = project.momentum
        if action == "attach_star":
            raw_tier = attach_star_target_tier or "stranger"
            tier = ATTACH_STAR_TIER_FALLBACK.get(raw_tier, raw_tier)
            target_bankability = clamp(
                attach_star_target_bankability if attach_star_target_bankability is not None else 50.0, 0.0, 100.0,
            )
            attachment_type = attach_attachment_type if attach_attachment_type in ATTACHMENT_TYPES else ATTACHMENT_BANKABLE

            # §7.4 v12 — the only real input is the offer itself; whether they take it is a real roll
            # reading the project's own momentum and the director's own Standing, not a guarantee.
            offer_p = attachment_offer_probability(
                target_bankability, tier, attachment_type, project.momentum, standing_score(state.standing),
            )
            attachment_offer_accepted = rng.random() < offer_p

            if attachment_offer_accepted:
                momentum_gain = attach_momentum(target_bankability, tier, attachment_type, rng)
                attachment_id = attach_star_target_npc_id or f"cold_{rng.randrange(10**6):06d}"
                new_attachment = Attachment(attachment_id, target_bankability, attachment_type)
                project = replace(project, attachments=project.attachments + (new_attachment,))

                if attachment_type == ATTACHMENT_BANKABLE:
                    best_bankable = max((a.bankability for a in project.attachments if a.attachment_type == ATTACHMENT_BANKABLE), default=0.0)
                    project = replace(project, attached_star_bankability=best_bankable)
                elif attachment_type == ATTACHMENT_GENRE_FIT:
                    project = replace(project, budget_ask=max(1.0, project.budget_ask * ATTACH_GENRE_FIT_BUDGET_DISCOUNT))

                project = replace(project, momentum=project.momentum + momentum_gain)
                if tier == "rival":
                    notoriety_delta = rival_poach_notoriety_cost(attach_star_rivalry_depth)
            # A pass costs nothing extra beyond the quarter already spent making the offer — the
            # same real opportunity cost a declined pitch already carries elsewhere in this design.
        elif action == "call_in_favour":
            project = replace(project, momentum=project.momentum + favour_momentum(favour_size, rng))
        elif action == "option_adaptation":
            # v20 — licensing_cost_fraction used to be a pure flavor number (momentum scaled off
            # it, but no money was ever actually deducted or chosen by the player); v19 fixed that
            # by paying it out of the director's own pocket, but a real rights fee is production
            # financing, not a personal expense — the studio (or your own self-financed budget)
            # actually carries it, the same way a bigger cast or a longer shoot inflates the real
            # budget rather than coming out of your wallet directly. Adds straight onto budget_ask
            # instead: a real, felt cost (harder to greenlight via difficulty()/momentum_budget_
            # discount, bigger break-even to clear, and for a self-financed project, more of your
            # own money on the line at greenlight) rather than a side-channel deduction. source_type
            # (adaptation_option_cost/adaptation_momentum) makes neither the cost nor the payoff a
            # flat percentage — a toy line costs far more than a public-domain novel and brings a
            # far bigger built-in audience with it.
            adaptation_cost_added = adaptation_option_cost(project.budget_ask, licensing_cost_fraction, adaptation_source_type)
            project = replace(
                project, budget_ask=project.budget_ask + adaptation_cost_added, is_adaptation=True,
                momentum=project.momentum + adaptation_momentum(licensing_cost_fraction, adaptation_source_type),
            )
        else:
            if action == "rewrite":
                # §7.4 v18 — a real gamble now, not a flat guaranteed gain: reads the director's
                # own talent (Craft/Vision — real power stats, never Taste, per §7.2's own rule)
                # blended with whoever's actually attached to write it this project.
                director_talent = 0.5 * state.attrs.craft + 0.5 * state.attrs.vision
                gain = rewrite_quality_gain(director_talent, project.screenwriter_skill, rng)
                true_quality = clamp(true_quality + gain, 0.0, 100.0)
                perceived_quality = perceived_script_quality(true_quality, state.attrs.taste, rng)
            project = apply_action(project, action)

        # v15 — momentum is packaging/dealmaking (attaching stars, calling in favours, courting
        # financiers), not on-set schedule discipline. Efficiency's identity everywhere else in this
        # engine is specifically production/shoot organization, so an earlier version of this that
        # scaled momentum gain by Efficiency was reusing the wrong number just because it was handy.
        # Command (leadership/persuasion) is the honest fit for "gets people to say yes faster," and
        # deliberately uses a smaller, milder curve than the shoot-quarters one — see
        # director_momentum_command_multiplier. Only scales THIS quarter's own deliberate action —
        # the event roll right below (real-world things happening to the project) isn't about the
        # director's own persuasiveness, so it's untouched.
        momentum_gain_this_quarter = project.momentum - momentum_before_action
        if momentum_gain_this_quarter:
            momentum_command_mult = director_momentum_command_multiplier(state.attrs.command)
            project = replace(project, momentum=momentum_before_action + momentum_gain_this_quarter * momentum_command_mult)

        # §7.4 v10 — development isn't silent between actions: one event roll, independent of the
        # action just taken, reading real world state. Never fires for a project that's already
        # frozen or self-financed — there's no studio/rival dynamic left for either to disturb.
        if not project.self_financed and not project.frozen:
            heat_signal = clamp(genre_heat_signal if genre_heat_signal is not None else genre_demand, 0.0, 100.0)
            event_p = EVENT_PROBABILITY_LO + (EVENT_PROBABILITY_HI - EVENT_PROBABILITY_LO) * heat_signal / 100.0
            if rng.random() < event_p:
                event_types = ["financier_cold_feet", "market_window"]
                if has_tracked_rival_same_genre:
                    event_types.append("rival_attachment_scare")
                event_type = rng.choice(event_types)
                magnitude = rng.uniform(EVENT_MOMENTUM_LO, EVENT_MOMENTUM_HI)
                sign = -1.0 if event_type in ("financier_cold_feet", "rival_attachment_scare") else 1.0
                project = apply_event_delta(project, sign * magnitude)

        # §7.4 v11 — every attached person ages one quarter and independently rolls whether they
        # walk, regardless of what action you took.
        if project.attachments:
            kept, dropped_attachments = age_attachments(project.attachments, rng)
            project = replace(project, attachments=kept)
            if any(a.attachment_type == ATTACHMENT_BANKABLE for a in dropped_attachments):
                best_bankable = max((a.bankability for a in kept if a.attachment_type == ATTACHMENT_BANKABLE), default=0.0)
                project = replace(project, attached_star_bankability=best_bankable)

    if notoriety_delta:
        standing = state.standing.copy()
        standing.add("notoriety", notoriety_delta)
        state = replace(state, standing=standing)

    dropped_ids = [a.attachment_id for a in dropped_attachments]

    # ---- §7.4 v16 — every OTHER project pays for the quarter it didn't get: real neglect, and a
    # real dynamic resolution for any that crosses the limbo threshold as a result. A project put
    # deliberately "in the drawer" (frozen) is exempt — that's a pause you chose, not neglect. ----
    projects: list[ProjectSlot | None] = list(state.projects)
    for i in range(len(projects)):
        if i == project_index:
            continue
        other_slot = projects[i]
        p = other_slot.project
        if p.frozen or p.quarters_remaining_in_shoot is not None:
            # A shooting project isn't being neglected — it's genuinely in production, running on
            # its own real calendar (advance_shoots_and_resolve), same exemption logic as an
            # explicit "in the drawer" pause.
            continue
        p = apply_neglect(p)
        if p.attachments:
            kept, dropped = age_attachments(p.attachments, rng)
            p = replace(p, attachments=kept)
            if any(a.attachment_type == ATTACHMENT_BANKABLE for a in dropped):
                best = max((a.bankability for a in kept if a.attachment_type == ATTACHMENT_BANKABLE), default=0.0)
                p = replace(p, attached_star_bankability=best)
        if p.dead:
            outcome = resolve_limbo(p, standing_score(state.standing), remaining_money, rng, _years_since_last_release(p))
            remaining_money -= outcome.cost_paid
            limbo_events.append({
                "genre": other_slot.genre, "budget_millions": round(p.budget_ask, 1), "kind": outcome.kind,
                "cost_paid": round(outcome.cost_paid, 2), "buyout_offered": round(outcome.buyout_offered, 2),
            })
            if outcome.kind == "fired":
                state = _fire_notoriety_hit(state)
            projects[i] = None if outcome.project is None else replace(other_slot, project=outcome.project)
        else:
            projects[i] = replace(other_slot, project=p)

    if self_finance_info is not None:
        projects[project_index] = replace(slot, project=project, true_script_quality=true_quality, perceived_script_quality=perceived_quality)
        new_state = replace(state, projects=tuple(p for p in projects if p is not None))
        return new_state, {**self_finance_info, "limbo_events": limbo_events}

    if project.frozen:
        projects[project_index] = replace(slot, project=project, true_script_quality=true_quality, perceived_script_quality=perceived_quality)
        new_state = replace(state, projects=tuple(p for p in projects if p is not None))
        return new_state, {
            "greenlit": False, "dead": False, "frozen": True,
            "momentum": round(project.momentum, 2), "momentum_band": momentum_band(project.momentum),
            "dropped_attachments": dropped_ids, "attachment_offer_accepted": attachment_offer_accepted,
            "limbo_events": limbo_events, "adaptation_cost_added": round(adaptation_cost_added, 2),
        }

    if project.self_financed and remaining_money < project.budget_ask:
        # §7.4 v23 — self-financing was never actually gated on having the money: a self-financed
        # project used to greenlight unconditionally and let net worth go arbitrarily negative
        # covering it. Real gate now — no studio anywhere in this film's money means there's also
        # no one else to cover the gap if you can't afford it yourself. Doesn't kill the project or
        # decay it — you own it outright already; you just can't shoot until you actually have the
        # budget. quarters_in_dev doesn't advance either — this wasn't a real dev-hell attempt,
        # it's a financing wall.
        projects[project_index] = replace(slot, project=project, true_script_quality=true_quality, perceived_script_quality=perceived_quality)
        blocked = replace(state, projects=tuple(p for p in projects if p is not None))
        return blocked, {
            "greenlit": False, "dead": False, "frozen": False, "blocked_on_money": True,
            "shortfall": round(project.budget_ask - max(0.0, remaining_money), 2),
            "momentum": round(project.momentum, 2), "momentum_band": momentum_band(project.momentum),
            "dropped_attachments": dropped_ids, "attachment_offer_accepted": attachment_offer_accepted,
            "limbo_events": limbo_events, "adaptation_cost_added": round(adaptation_cost_added, 2),
        }

    # MAX_CONCURRENT_SHOOTS — only one production can ever be actively shooting at once (a
    # director can develop several projects in parallel, but can't physically be on two sets at
    # the same time). Without this, nothing stops several huge productions each running their own
    # independent countdown in parallel and all wrapping around the same time.
    concurrent_shoots = sum(1 for p in state.projects if p.project.quarters_remaining_in_shoot is not None)
    shoot_slot_free = concurrent_shoots < MAX_CONCURRENT_SHOOTS

    if not shoot_slot_free:
        # Fully ready to go (the studio would say yes, or it's already yours to self-finance), but
        # nowhere to put it yet — the dev action already landed above (momentum, script quality,
        # whatever this quarter's real work was), it just doesn't convert into a greenlight this
        # quarter. Waits, harmlessly, for the current shoot to wrap and free the one shoot slot.
        new_project, greenlit = project, False
    elif project.self_financed or project.guaranteed_greenlight:
        # No studio's yes to wait on — self-financing (or a director-for-hire offer, §7.13 v10)
        # means there's nothing to ask. (Affordability for the self-financed case is checked above
        # — this branch only runs once that's already confirmed, or for a hire offer, which is the
        # studio's money, not yours.)
        new_project, greenlit = project, True
    else:
        pkg_strength = package_strength(project.attached_star_bankability, true_quality, standing_score(state.standing))
        # v11 fix (closing the incompleteness named when this project's own studio-view of
        # Efficiency was first built): a studio that trusts you — or doesn't, off real history in
        # simulation._relationships.studio_relations, now including a director's own past overruns
        # with them, not just an actor's own credits — actually moves THIS project's own greenlight
        # odds. Reuses the exact same coefficient the acting track's utility_bonus_from_trust
        # already applies, rather than a second, director-specific number.
        pkg_strength += STUDIO_TRUST_UTILITY_COEF * (studio_trust - TRUST_DEFAULT)
        bankability = bankability_multiplier(state.trailing_roi, project.budget_ask, state.trailing_overage)
        new_project, greenlit = advance_quarter(project, pkg_strength, rng, bankability)

    if not greenlit:
        if new_project.dead:
            # The worked project itself crossed the floor this quarter — the same dynamic
            # resolution a neglected project gets, never a flat "dies."
            outcome = resolve_limbo(new_project, standing_score(state.standing), remaining_money, rng, _years_since_last_release(new_project))
            remaining_money -= outcome.cost_paid
            limbo_events.append({
                "genre": genre, "budget_millions": round(new_project.budget_ask, 1), "kind": outcome.kind,
                "cost_paid": round(outcome.cost_paid, 2), "buyout_offered": round(outcome.buyout_offered, 2),
            })
            if outcome.kind == "fired":
                state = _fire_notoriety_hit(state)
            if outcome.project is None:
                projects[project_index] = None
                cleared = replace(state, projects=tuple(p for p in projects if p is not None))
                return cleared, {
                    "greenlit": False, "dead": True, "frozen": False,
                    "momentum": round(new_project.momentum, 2), "momentum_band": momentum_band(new_project.momentum),
                    "dropped_attachments": dropped_ids, "attachment_offer_accepted": attachment_offer_accepted,
                    "limbo_events": limbo_events, "limbo_outcome": outcome.kind,
                    "adaptation_cost_added": round(adaptation_cost_added, 2),
                }
            # handed_free / buyout_paid — saved, but still needs a future action to actually make it.
            projects[project_index] = replace(slot, project=outcome.project, true_script_quality=true_quality, perceived_script_quality=perceived_quality)
            saved = replace(state, projects=tuple(p for p in projects if p is not None))
            return saved, {
                "greenlit": False, "dead": False, "frozen": False,
                "momentum": round(outcome.project.momentum, 2), "momentum_band": momentum_band(outcome.project.momentum),
                "dropped_attachments": dropped_ids, "attachment_offer_accepted": attachment_offer_accepted,
                "limbo_events": limbo_events, "limbo_outcome": outcome.kind,
                "adaptation_cost_added": round(adaptation_cost_added, 2),
            }
        projects[project_index] = replace(slot, project=new_project, true_script_quality=true_quality, perceived_script_quality=perceived_quality)
        updated = replace(state, projects=tuple(p for p in projects if p is not None))
        return updated, {
            "greenlit": False, "dead": False, "frozen": False,
            "momentum": round(new_project.momentum, 2), "momentum_band": momentum_band(new_project.momentum),
            "dropped_attachments": dropped_ids, "attachment_offer_accepted": attachment_offer_accepted,
            "limbo_events": limbo_events, "adaptation_cost_added": round(adaptation_cost_added, 2),
        }

    # v12 — greenlit no longer means resolved. A self-financed/hire project used to greenlight AND
    # fully resolve in the same instant, the moment any dev action landed — a $2M passion project
    # and a $300M tentpole cost the exact same thing: one quarter's attention. Real productions
    # don't. Everything decided BEFORE a camera rolls (casting, the ensemble's own chaos, and so
    # the schedule) locks in right here; everything only knowable once the film is actually
    # finished (the edit, the reception, the release) waits for simulation._director.
    # advance_shoots_and_resolve, called once a year from Session.end_year() — the shoot itself
    # runs on its own real calendar, not the director's own quarterly attention.
    base_chaos = director_shoot_style.ensemble_chaos_total(new_project.attachments)
    schedule_overage = director_shoot_style.overage_percent(
        ambition=state.attrs.vision, chaos=base_chaos * 100.0, efficiency=state.attrs.efficiency, rng=rng,
    )
    quarters_needed = quarters_for_directed_film(project.budget_ask, state.attrs.efficiency, state.attrs.vision)
    expected_quarters = (
        None if project.self_financed else studio_expected_quarters(project.budget_ask, state.trailing_overage)
    )

    shooting_project = replace(
        new_project,
        quarters_remaining_in_shoot=quarters_needed,
        locked_schedule_overage=schedule_overage,
        locked_quarters_needed=quarters_needed,
        locked_studio_expected_quarters=expected_quarters,
        locked_momentum_at_greenlight=new_project.momentum if new_project.self_financed else None,
    )
    projects[project_index] = replace(slot, project=shooting_project, true_script_quality=true_quality, perceived_script_quality=perceived_quality)
    new_state = replace(state, projects=tuple(p for p in projects if p is not None))
    return new_state, {
        "greenlit": True, "resolved": False, "shooting": True, "dead": False, "frozen": False,
        "quarters_remaining_in_shoot": quarters_needed, "self_financed": project.self_financed,
        "momentum": 1.0, "momentum_band": momentum_band(1.0),
        "genre": genre, "budget_ask": round(project.budget_ask, 2),
        "dropped_attachments": dropped_ids, "attachment_offer_accepted": attachment_offer_accepted,
        "limbo_events": limbo_events, "adaptation_cost_added": round(adaptation_cost_added, 2),
    }


def _finish_directed_film(
    state: DirectorState, slot: ProjectSlot, genre_demand: float, rng: random.Random,
) -> tuple[DirectorState, dict]:
    """Called once a shooting project's quarters_remaining_in_shoot reaches 0 (simulation._
    director.advance_shoots_and_resolve). Everything here used to run inline, instantly, the
    moment a project was greenlit — now it runs once the shoot has actually run its real course.
    schedule_overage/financing_studio_id are read from what was already locked in at greenlight
    (slot.project.locked_schedule_overage/financing_studio_id) rather than re-rolled, so the
    schedule that determined how long the wait was is the same one the final budget reads."""
    project = slot.project
    genre = slot.genre
    reception, actual_strategy, push_honored, effective_budget, schedule_overage, financing_studio_id = (
        _resolve_directed_film(state, slot, project, genre, genre_demand, rng)
    )

    billing_weight = 1.0  # you're always the whole show on your own film
    heat_delta = delta_heat(billing_weight, state.credits, project.budget_ask, reception.roi, reception.audience_score)
    # delta_prestige wants two genuinely independent signals — what critics thought
    # (film_critic_score, centred on 57) and a separate visibility term (your_spotlight, centred
    # on 54). A director has no on-screen Spotlight of their own; audience_score is the real
    # analog (how much the audience actually embraced the film), not a second read of the same
    # critic number.
    prestige_delta = delta_prestige(billing_weight, state.credits, reception.film_critic_score, reception.audience_score)
    if project.guaranteed_greenlight:
        # §7.13 v10 — a hire's own trade: real visibility, less of it reads as yours creatively.
        heat_delta *= HIRE_FILM_HEAT_MULTIPLIER
        prestige_delta *= HIRE_FILM_PRESTIGE_MULTIPLIER
    standing = state.standing.copy()
    standing.add("heat", heat_delta)
    standing.add("prestige", prestige_delta)
    standing.add("affection", delta_affection(billing_weight, state.credits, project.budget_ask, reception.audience_score))

    # director.development.format_adjusted_roi — a Limited/acquired-Festival release's own ROI
    # formula caps out far below a wide release's by construction, so both the profitability streak
    # and the trailing-ROI track record read the film's ROI relative to what THAT release strategy
    # could realistically clear, not a flat wide-release bar every format was never chasing. An
    # unsold festival submission still reads against the full bar — see that function's own note.
    effective_roi = format_adjusted_roi(reception.roi, actual_strategy, reception.gross)

    # §7.7 v10 — final cut is earned partly by "two consecutive profitable films"; that streak has
    # to actually be tracked somewhere, or the bar is unreachable by construction.
    was_profitable = effective_roi >= PROFITABLE_ROI_THRESHOLD
    new_streak = state.consecutive_profitable_films + 1 if was_profitable else 0
    new_trailing_roi = TRAILING_ROI_DECAY * state.trailing_roi + (1.0 - TRAILING_ROI_DECAY) * effective_roi
    new_trailing_overage = TRAILING_ROI_DECAY * state.trailing_overage + (1.0 - TRAILING_ROI_DECAY) * schedule_overage

    # §7.4 v23 — real director income, finally. Self-financed: you already paid the production
    # budget to get here (Session deducts it at greenlight time, unchanged) — what actually lands
    # in your pocket now is the release's own net proceeds: full gross (rights_share=1.0, the "you
    # keep all of it" this design already promised) less the marketing you also had to cover
    # yourself. Studio-backed: a real, modest director's fee off the budget — nothing before this
    # pass ever paid a director anything for directing. Hire: the "sellout" pays better, per §7.10.
    if project.self_financed:
        director_income = reception.gross - reception.marketing
    elif project.guaranteed_greenlight:
        fee_share = project.negotiated_fee_share if project.negotiated_fee_share is not None else DIRECTOR_FEE_SHARE_HIRE
        director_income = fee_share * project.budget_ask
    else:
        fee_share = project.negotiated_fee_share if project.negotiated_fee_share is not None else DIRECTOR_FEE_SHARE_STUDIO
        director_income = fee_share * project.budget_ask
        if project.box_office_bonus_type is not None:
            director_income += box_office_bonus_earned(
                reception.gross, reception.break_even, project.box_office_bonus_share, project.box_office_bonus_type,
            )

    resolved_state = replace(
        state, standing=standing, credits=state.credits + 1, consecutive_profitable_films=new_streak,
        trailing_roi=new_trailing_roi, trailing_overage=new_trailing_overage,
    )

    # §5.19 v10 — a directed film gets a real content rating too, not just an actor's. A director's
    # film never generates a full six-dial Palette (out of scope this pass), so Vision (§7.2's own
    # "originality and ambition") stands in for Intensity's real driver, with real noise — a named,
    # honest simplification, not a second rating system.
    synthetic_intensity = clamp(rng.gauss(state.attrs.vision - 50.0, 15.0), -50.0, 50.0)
    film_rating_score = rating_score(synthetic_intensity, genre)
    film_rating_band = compute_rating_band(film_rating_score)

    quarters_taken = project.locked_quarters_needed if project.locked_quarters_needed is not None else 0

    info = {
        "greenlit": True, "resolved": True, "dead": False, "frozen": False,
        "momentum": 1.0, "momentum_band": momentum_band(1.0),
        "genre": genre, "budget": round(effective_budget, 2), "budget_ask": round(project.budget_ask, 2),
        "franchise_id": project.franchise_id, "installment_number": project.installment_number,
        "schedule_overage_pct": round(schedule_overage * 100.0, 1),
        "quarters_taken": quarters_taken,
        "studio_expected_quarters": (
            round(project.locked_studio_expected_quarters, 1) if project.locked_studio_expected_quarters is not None else None
        ),
        "financing_studio_id": financing_studio_id, "self_financed": project.self_financed,
        "critic_score": round(reception.film_critic_score),
        "film_critic_score": reception.film_critic_score,
        "audience_score": reception.audience_score,
        "roi": round(reception.roi, 2),
        "gross_millions": round(reception.gross, 1),
        "marketing_millions": round(reception.marketing, 1),
        "director_income": round(director_income, 2),
        "box_office_bonus_type": project.box_office_bonus_type,
        "box_office_bonus_share": round(project.box_office_bonus_share, 4) if project.box_office_bonus_type else None,
        "requested_release": slot.pending_release_request,
        "release_strategy": actual_strategy,
        "release_overruled": slot.pending_release_request is not None and slot.pending_release_request != actual_strategy,
        "marketing_push_requested": slot.pending_marketing_push,
        "marketing_push_honored": push_honored,
        "casting_choice": slot.pending_casting_choice,
        "shoot_style": slot.pending_shoot_style,
        "rating_band": film_rating_band,
        "opening_millions": reception.opening,
        "legs": reception.legs,
        "final_attachment_count": len(project.attachments),
    }
    return resolved_state, info


def advance_shoots_and_resolve(state: DirectorState, genre_heat: dict, rng: random.Random) -> tuple[DirectorState, list[dict]]:
    """Called once a year, from simulation.session.Session.end_year() — a live shoot runs on its
    own real calendar, not the director's own quarterly attention, so every project currently
    shooting (quarters_remaining_in_shoot is not None) advances by a full QUARTERS_PER_YEAR here
    regardless of what the director spent their own actions on elsewhere this year. Any that
    reach 0 actually wrap and resolve (_finish_directed_film) — schedule_trust_penalty is computed
    by the caller (Session has studio_relations, this module doesn't), off each resolved film's own
    quarters_taken/studio_expected_quarters. Returns (new_state, resolved_films) — resolved_films
    is almost always 0 or 1 entries (MAX_CONCURRENT_SHOOTS=1 means at most one thing is ever
    shooting), kept as a list for safety rather than assuming that invariant holds forever."""
    projects = list(state.projects)
    resolved_films = []
    for i, slot in enumerate(projects):
        p = slot.project
        if p.quarters_remaining_in_shoot is None:
            continue
        remaining = p.quarters_remaining_in_shoot - SHOOT_QUARTERS_PER_YEAR
        if remaining > 0:
            projects[i] = replace(slot, project=replace(p, quarters_remaining_in_shoot=remaining))
            continue
        genre_demand = world_genre_demand(genre_heat, slot.genre)
        state, info = _finish_directed_film(state, slot, genre_demand, rng)
        info["genre"] = slot.genre
        resolved_films.append(info)
        projects[i] = None
    return replace(state, projects=tuple(p for p in projects if p is not None)), resolved_films


@dataclass(frozen=True)
class DirectedReleaseSnapshot:
    """What a follow-up "push for a wider release" (§7.12 v10) needs to know about a film that
    already resolved Limited or Festival — kept as its own small snapshot rather than reaching back
    into the resolved DirectorState, which no longer holds a reference to a project once it's done."""
    genre: str
    budget_millions: float
    release_strategy: str
    rating_band: str
    film_critic_score: float
    audience_score: float
    opening_millions: float
    legs: float
    roi: float
    expansion_used: bool = False


# §7.12 v10 — platform expansion, the trimmed single-ask version: one real negotiation, not a
# ladder. Availability itself is the first gate, off the film's own already-resolved reception.
EXPANSION_MIN_CRITIC = 65.0  # bands.CRITIC_BANDS' own "warm" cutoff
EXPANSION_MIN_AUDIENCE = 65.0  # bands.AUDIENCE_BANDS' own "a real draw" cutoff
EXPANSION_OPENING_MULTIPLIER = 2.5  # a real, bigger screen count — not a second, unrelated roll
EXPANSION_WEEKS = 4
EXPANSION_MARKETING_SHARE = 0.35  # a genuine second cost, not a free upgrade

RATING_DAMPENER_RANGES = {
    "G": (1.0, 1.0), "PG": (1.0, 1.0),
    "PG-13": (0.85, 0.95), "R": (0.65, 0.85), "NC-17": (0.45, 0.65),
}
# Where a studio's own identity sits within each band's range — the same "a specialty distributor
# is genuinely more willing to go wide with an R" idea studios.effective_rating_ceiling() already
# reads from the other direction (the studio's own pressure toward a cut), not a second number.
STUDIO_TOLERANCE_POSITION = {"indie": 1.0, "prestige": 0.9, "mid_major": 0.5, "streamer": 0.3, "blockbuster": 0.0}


def expansion_available(snapshot: DirectedReleaseSnapshot | None) -> bool:
    if snapshot is None or snapshot.expansion_used:
        return False
    if snapshot.release_strategy not in (LIMITED, FESTIVAL):
        return False
    if snapshot.release_strategy == FESTIVAL and snapshot.roi <= 0.0:
        return False  # an unsold festival submission has nothing to expand
    return snapshot.film_critic_score >= EXPANSION_MIN_CRITIC or snapshot.audience_score >= EXPANSION_MIN_AUDIENCE


def rating_dampener(band: str, studio_id: str) -> float:
    lo, hi = RATING_DAMPENER_RANGES.get(band, (1.0, 1.0))
    position = STUDIO_TOLERANCE_POSITION.get(studio_id, 0.5)
    return lo + (hi - lo) * position


@dataclass(frozen=True)
class ExpansionOutcome:
    granted: bool
    studio_id: str | None
    extra_gross_millions: float
    extra_marketing_millions: float


def resolve_expansion(
    snapshot: DirectedReleaseSnapshot, trust: float, importance: float, rng: random.Random,
    influence_fn=director_influence_on_studio_decision,
) -> ExpansionOutcome:
    """One real negotiation, reusing what's already built: influence_fn is the same fame-gated
    curve every other studio ask in this design uses; the rating dampener is a real but secondary
    term (even at its floor it only cuts the odds by roughly half — it can never zero them out the
    way expansion_available()'s own gate already can)."""
    studio = pick_studio(snapshot.budget_millions, rng)
    p = clamp(influence_fn(trust, importance) * rating_dampener(snapshot.rating_band, studio.id), 0.0, 1.0)
    if rng.random() >= p:
        return ExpansionOutcome(granted=False, studio_id=studio.id, extra_gross_millions=0.0, extra_marketing_millions=0.0)
    bigger_opening = snapshot.opening_millions * EXPANSION_OPENING_MULTIPLIER
    extra_gross = sum(weekly_gross_curve(bigger_opening, snapshot.legs, weeks=EXPANSION_WEEKS))
    extra_marketing = extra_gross * EXPANSION_MARKETING_SHARE
    return ExpansionOutcome(granted=True, studio_id=studio.id, extra_gross_millions=extra_gross, extra_marketing_millions=extra_marketing)


# §7.13 v10 — director-for-hire: the studio comes to you. Mechanizes §7.10's own "sellout
# decision," previously only narrated. genre_fit_term is a flat, honest placeholder (1.0) until
# Signature/Legibility (§7.8) is actually built — that section's own non-monotonic shape (narrows
# general studio access, sharpens fit for one genre) is a real constraint on this term once it
# exists; a naive "more fame, more offers" version was explicitly rejected during design (see
# design/part-07 §7.13's own verification note), so a neutral placeholder is the honest stand-in,
# not a silent guess at what that term will eventually read.
HIRE_OFFER_BASE_PROBABILITY = 0.10


def hire_offer_probability(director_standing_score: float, genre_heat_signal: float) -> float:
    standing_term = clamp(director_standing_score / 100.0, 0.0, 1.0)
    genre_fit_term = 1.0  # placeholder — see module-level note above
    heat_term = clamp(genre_heat_signal / 100.0, 0.0, 1.0)
    return clamp(HIRE_OFFER_BASE_PROBABILITY * standing_term * genre_fit_term * heat_term, 0.0, 1.0)


@dataclass(frozen=True)
class HireOffer:
    genre: str
    budget_millions: float
    studio_id: str


def roll_hire_offer(
    director_standing_score: float, genre: str, genre_heat_signal: float, budget_tiers: dict, rng: random.Random,
) -> HireOffer | None:
    """genre is picked by the caller (Session has the real genre list and GenreHeat dict already;
    this module stays consistent with its own existing pattern of consuming plain, pre-computed
    reads rather than importing world/ state itself)."""
    if rng.random() >= hire_offer_probability(director_standing_score, genre_heat_signal):
        return None
    budget = rng.choice(list(budget_tiers.values()))
    studio = pick_studio(budget, rng)
    return HireOffer(genre=genre, budget_millions=budget, studio_id=studio.id)


def accept_hire_offer(state: DirectorState, offer: HireOffer, rng: random.Random) -> DirectorState:
    """Skips development hell outright — no momentum, no Difficulty check. Final cut still reads
    the normal has_final_cut() bar at resolution time (Prestige/streak/fee-cut) — a hire offer adds
    no shortcut toward it the way self-financing would; §7.10's "sellout" trade is real precisely
    because it doesn't also buy you creative control.

    §7.4 v16 — appends as a new project slot rather than displacing anything; Session is expected
    to only offer accept_hire_offer() when can_start_new_project() is True. Safe no-op otherwise."""
    if not can_start_new_project(state):
        return state
    screenwriter_skill = clamp(rng.gauss(SCREENWRITER_SKILL_MEAN, SCREENWRITER_SKILL_SD), 0.0, 100.0)
    project = DevProject(
        script_id=f"hire_{rng.randrange(10**6):06d}", budget_ask=offer.budget_millions,
        momentum=1.0, guaranteed_greenlight=True, screenwriter_skill=screenwriter_skill,
        negotiated_fee_share=negotiated_director_fee_share(DIRECTOR_FEE_SHARE_HIRE_RANGE, director_fee_leverage(state), rng),
        financing_studio_id=offer.studio_id,  # a hire offer already names its own studio — no
        # random pick needed, and the studio_relations trust ledger still deserves updating even
        # though guaranteed_greenlight skips the greenlight roll itself.
    )
    quality = clamp(rng.gauss(NEW_PROJECT_SCRIPT_QUALITY_MEAN, NEW_PROJECT_SCRIPT_QUALITY_SD), 0.0, 100.0)
    perceived_quality = perceived_script_quality(quality, state.attrs.taste, rng)
    slot = ProjectSlot(project=project, genre=offer.genre, true_script_quality=quality, perceived_script_quality=perceived_quality)
    return replace(state, projects=state.projects + (slot,))


def decay_director_standing(state: DirectorState) -> DirectorState:
    """Same yearly upkeep actor/standing.py's own decay does — run once a year through
    full_career.advance_between_years regardless of whether the year was spent directing.

    v14, fix — a real bug, found by chasing why Director Standing never grew across dozens of
    seeded careers: this used HEAT_KEEP["idle"] (0.80/yr, a ~20% Heat loss every single year)
    unconditionally, including every year of an active development cycle. That constant was
    calibrated for an actor's occasional fallow year between offers — genuinely rare for an actor,
    who gets a real offer most years. A director's development cycle routinely runs 15-20+ years
    before a single greenlight, so the same 20%/yr loss was compounding continuously:
    0.80**20 ≈ 0.012, effectively erasing nearly all Heat between films regardless of how the
    films themselves actually did. Real development work (momentum building, real actions taken)
    is a real, ongoing industry signal, just not the market-moving kind an actual release is — it
    decays at the same modest rate Prestige/Affection already use (PRESTIGE_DECAY, no floor term
    of its own, still real decay), not Heat's steep idle rate. Only truly idle — no project at all
    in the slate — gets the harsher rate.

    v16 — "in development" now reads across the whole slate (any project neither frozen nor dead),
    not a single current_project field; running several projects at once is real, ongoing industry
    presence exactly the same way running one is."""
    standing = state.standing.copy()
    in_development = any(not s.project.frozen and not s.project.dead for s in state.projects)
    heat_keep = PRESTIGE_DECAY if in_development else HEAT_KEEP["idle"]
    standing.decay({
        "heat": heat_keep,
        "prestige": PRESTIGE_DECAY,
        "affection": AFFECTION_DECAY,
        "notoriety": NOTORIETY_DECAY,
    })
    return replace(state, standing=standing)
