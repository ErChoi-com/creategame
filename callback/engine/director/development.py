"""design/part-07-the-director.md §7.4 — development hell: PackageStrength, Difficulty, the
greenlight roll, momentum, and one development action per quarter — split across however many
projects are actually in development (§7.4 v16's slate), not locked to a single one.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace

from callback.engine.core.util import clamp, sigmoid

PACKAGE_STAR_WEIGHT = 0.40
PACKAGE_SCRIPT_WEIGHT = 0.30
PACKAGE_STANDING_WEIGHT = 0.30

DIFFICULTY_BASE = 30.0
DIFFICULTY_COEF = 22.0

GREENLIGHT_BASE_PROBABILITY = 0.16
GREENLIGHT_SLOPE = 0.10
MOMENTUM_DECAY = 0.96
MOMENTUM_DEATH_FLOOR = 0.22

# v17 — momentum entered greenlight_probability as a flat multiplier with no read on budget at
# all, so a barely-built-up pitch ("building" momentum) could greenlight a $150M tentpole just as
# readily, mechanically, as a $10M indie, as long as pkg_strength cleared the (already-higher)
# difficulty() bar for that budget. A bigger swing should need more real buzz behind it, not just a
# strong enough package on paper. Reuses difficulty() itself as the read on "how big an ask is
# this" rather than a second budget curve — discounts momentum's effective value once difficulty
# climbs past its own floor (DIFFICULTY_BASE, ~a near-zero-budget project, which pays no discount
# at all), scaling how much bite the discount has via MOMENTUM_BUDGET_DISCOUNT_COEF.
MOMENTUM_BUDGET_DISCOUNT_COEF = 0.12  # v25 -- flattened further from 0.3 (originally 0.8). At a
# $250M tentpole ask this is now only a 1.06x discount -- still a real, directionally-correct cost
# for a bigger swing, but no longer the dominant driver of how long a tentpole takes to get moving.


def momentum_budget_discount(diff: float) -> float:
    return 1.0 + MOMENTUM_BUDGET_DISCOUNT_COEF * max(0.0, diff - DIFFICULTY_BASE) / 100.0

# §7.4 v18 — "rewrite" used to be a flat, guaranteed +6 script quality every single time,
# regardless of who was doing the writing. A real gamble now: the expected gain scales with the
# director's own talent (Craft/Vision — real execution/creative-power stats, deliberately NOT
# Taste, which §7.2 already establishes as perception, not power — Taste moving true outcomes was
# a real bug caught and fixed earlier in this design's own history, "option an adaptation" scaling
# off Taste) blended with whoever's actually attached to write it (screenwriter_skill, a hidden
# per-project trait — see DevProject below). A weak pairing can genuinely make the script worse;
# a strong one still isn't a sure thing, just a better bet.
SCREENWRITER_SKILL_MEAN = 55.0
SCREENWRITER_SKILL_SD = 20.0

# The range itself moves with talent, not just its centre: zero talent can genuinely gut a script
# (a deep floor) and can only rarely luck into a good draft (a low ceiling); full talent can't
# really make it worse (a floor near zero) and has real upside above the old flat +6 baseline. At
# the game's current fixed director talent (50/100, since no attribute customization/growth exists
# yet — real talent variation is screenwriter_skill's job until that changes), the range still sits
# roughly centred on the old +6, not collapsed toward it — the gamble is real without quietly
# nerfing the typical outcome.
REWRITE_GAIN_FLOOR_LO = -6.0  # worst case at zero combined talent — a real, meaningful loss
REWRITE_GAIN_FLOOR_HI = 4.0  # worst case at full talent — genuinely can't do much damage
REWRITE_GAIN_CEILING_LO = 8.0  # best case even at zero talent — pure luck can still land a decent draft
REWRITE_GAIN_CEILING_HI = 18.0  # best case at full talent — a real ceiling above the old flat rate
# At combined=0.5 (today's only real value, since director attributes have no customization or
# growth yet) this ranges -1..+13, averaging 6 — the same expected value the old flat +6 always
# gave, now with a genuine gamble around it instead of quietly landing lower on average.


def rewrite_quality_gain(director_talent: float, screenwriter_skill: float, rng: random.Random) -> float:
    """director_talent: (Craft + Vision) / 2, real power stats — never Taste. screenwriter_skill:
    DevProject's own hidden trait, set once when the project starts (see start_development). Both
    the floor and the ceiling of the roll scale with combined talent — not a fixed spread around a
    talent-shifted mean, an actually wider or narrower range depending on who's doing the writing."""
    combined = clamp(0.5 * director_talent + 0.5 * screenwriter_skill, 0.0, 100.0) / 100.0
    lo = REWRITE_GAIN_FLOOR_LO + (REWRITE_GAIN_FLOOR_HI - REWRITE_GAIN_FLOOR_LO) * combined
    hi = REWRITE_GAIN_CEILING_LO + (REWRITE_GAIN_CEILING_HI - REWRITE_GAIN_CEILING_LO) * combined
    return rng.uniform(lo, hi)


REWRITE_MOMENTUM = 0.20
ATTACH_STAR_MOMENTUM = 0.35
CUT_BUDGET_MOMENTUM = 0.15
CUT_BUDGET_DIFFICULTY_REDUCTION = 8.0
NEW_FINANCIER_MOMENTUM = 0.25
MARKET_MOMENTUM = 0.30

# Self-financing isn't just a better roll — you're taking the project away from whoever's been
# financing it. A limping, low-momentum project isn't worth a studio holding onto (they let it go
# for nothing); a project with real heat, they don't just hand over, and you have to buy them out.
SELF_FINANCE_FREE_RELEASE_BASE = 0.35
SELF_FINANCE_FREE_RELEASE_MOMENTUM_COEF = 0.6
SELF_FINANCE_BUYOUT_FRACTION = 0.15  # of budget_ask, if the studio won't just walk away
SELF_FINANCE_FRANCHISE_VALUE_COEF = 0.35  # per installment past the first — the studio isn't just
# selling a production budget back to you on a franchise entry, it's selling real IP: each further
# installment raises the ask, same "the property itself has value" logic leverage.indispensability.
# RECAST_COST_COEF already prices into a recast. installment_number 0/1 (an original or the first
# entry in a brand-new franchise) leaves the multiplier at 1.0 — nothing about this changes for the
# common, non-franchise case.
SELF_FINANCE_FRANCHISE_GRACE_YEARS = 3  # matches genre.franchise.ANTICIPATION_GAP_YEARS — a normal
# gap between installments isn't dormancy, it's healthy spacing (that module's own spacing_modifier
# rewards exactly this gap with a real audience bonus, not a penalty); the present-value clock below
# only starts once a franchise has gone longer than a normal gap without a release.
SELF_FINANCE_FRANCHISE_VALUE_DECAY = 0.90  # per year beyond the grace period — the track-record
# premium above isn't a fixed asset, it's a live read of the property's own present value: a
# franchise nobody's made a real entry in for years isn't worth a buyer paying a premium for today,
# no matter how many installments it racked up while it was active. Fades the premium back toward
# the flat SELF_FINANCE_BUYOUT_FRACTION rate the longer it's sat genuinely dormant, never below it —
# installment count still sets the ceiling, recency decides how much of it is still real.
SELF_FINANCE_VALUE_MULTIPLIER_CAP = 6.0  # even the deepest, freshest franchise entry doesn't turn a
# buyout into an unplayable number

DEV_ACTIONS = (
    "rewrite", "attach_star", "cut_budget", "new_financier", "take_to_market", "self_finance", "drawer",
    "call_in_favour", "option_adaptation",
)

# design/part-07 §7.4 v10 — momentum is a raw internal number; §15's word-only rule applies to it
# exactly as it applies to Indispensability and the director's own five attributes. This is the
# band a caller shows a player, never the float itself.
MOMENTUM_BANDS: tuple[tuple[float, str], ...] = (
    (0.0, "dead"), (0.22, "fading"), (0.40, "building"), (0.70, "real heat"), (1.0, "can't-miss"),
)


def momentum_band(momentum: float) -> str:
    label = MOMENTUM_BANDS[0][1]
    for lower, text in MOMENTUM_BANDS:
        if momentum >= lower:
            label = text
    return label


# §7.4 v10 — "attach a star" isn't one flat number: who you're attaching sets the real range.
# Every tier reads the same one input, the target's own AttachedStarBankability (0-100); only a
# Rival poach uses the elevated range, because it's taking something already spoken for.
ATTACH_STAR_MOMENTUM_LO = 0.25
ATTACH_STAR_MOMENTUM_HI = 0.40
ATTACH_STAR_RIVAL_MOMENTUM_LO = 0.35
ATTACH_STAR_RIVAL_MOMENTUM_HI = 0.60
ATTACH_STAR_NOISE_SD = 0.02  # real, but never the dominant term — bankability sets the range

RIVAL_POACH_NOTORIETY_LO = 2.0
RIVAL_POACH_NOTORIETY_HI = 8.0

# Favour cost scales down with relationship depth — a Loyal contact costs less than an Ally, both
# less than the flat "Familiar/Stranger" market rate. Not used for a Rival poach, which pays in
# Notoriety instead, never a favour discount.
ATTACH_STAR_FAVOUR_DISCOUNT = {"loyal": 0.5, "ally": 0.75}


def attach_star_momentum(target_bankability: float, tier: str, rng: random.Random) -> float:
    """tier: "loyal" | "ally" | "familiar" | "stranger" | "rival" — only "rival" uses the elevated
    range. target_bankability (0-100) sets where in that range the result lands."""
    lo, hi = (
        (ATTACH_STAR_RIVAL_MOMENTUM_LO, ATTACH_STAR_RIVAL_MOMENTUM_HI) if tier == "rival"
        else (ATTACH_STAR_MOMENTUM_LO, ATTACH_STAR_MOMENTUM_HI)
    )
    base = lo + (hi - lo) * clamp(target_bankability, 0.0, 100.0) / 100.0
    return max(0.0, base + rng.gauss(0.0, ATTACH_STAR_NOISE_SD))


# §7.4 v11 — attaching someone isn't only ever "the star." Three real reasons to attach, three real
# mechanical effects — not one formula dressed up as three labels:
ATTACHMENT_BANKABLE = "bankable"       # the original case — fame, real PackageStrength weight
ATTACHMENT_GENRE_FIT = "genre_fit"     # not famous, but right for it — eases the ask itself
ATTACHMENT_STUDIO_FAVORITE = "studio_favorite"  # the studio already trusts them — reliable, modest
ATTACHMENT_TYPES = (ATTACHMENT_BANKABLE, ATTACHMENT_GENRE_FIT, ATTACHMENT_STUDIO_FAVORITE)

# A genre-fit attach doesn't move PackageStrength's star term — it makes the package itself easier
# to finance, the same real lever Cut the budget already uses (a smaller Difficulty(budget) read),
# just smaller and attached to a person instead of a one-time budget cut.
ATTACH_GENRE_FIT_MOMENTUM_LO = 0.10
ATTACH_GENRE_FIT_MOMENTUM_HI = 0.20
ATTACH_GENRE_FIT_BUDGET_DISCOUNT = 0.95

# A studio favourite is reliable specifically *because* it isn't fame-scaled — the studio already
# likes them, full stop. Flat range, not bankability-driven, the one attachment type where a total
# unknown is exactly as useful as a star.
ATTACH_STUDIO_FAVORITE_MOMENTUM_LO = 0.15
ATTACH_STUDIO_FAVORITE_MOMENTUM_HI = 0.25


def attach_momentum(target_bankability: float, tier: str, attachment_type: str, rng: random.Random) -> float:
    if attachment_type == ATTACHMENT_GENRE_FIT:
        base = ATTACH_GENRE_FIT_MOMENTUM_LO + (ATTACH_GENRE_FIT_MOMENTUM_HI - ATTACH_GENRE_FIT_MOMENTUM_LO) * clamp(target_bankability, 0.0, 100.0) / 100.0
        return max(0.0, base + rng.gauss(0.0, ATTACH_STAR_NOISE_SD))
    if attachment_type == ATTACHMENT_STUDIO_FAVORITE:
        return rng.uniform(ATTACH_STUDIO_FAVORITE_MOMENTUM_LO, ATTACH_STUDIO_FAVORITE_MOMENTUM_HI)
    return attach_star_momentum(target_bankability, tier, rng)


# §7.4 v12 — attaching someone was a guaranteed yes, which skipped the actual decision: real
# people read a project before committing to it. The only input this ever needs is the offer
# itself; whether they take it reads real, already-existing numbers — not a fourth roll bolted on.
ATTACHMENT_OFFER_BASE_GENRE_FIT = 0.75    # they want this kind of project, full stop
ATTACHMENT_OFFER_BASE_STUDIO_FAVORITE = 0.80  # reliable by construction — that's the whole point
ATTACHMENT_OFFER_BANKABLE_BASE = 0.75
# v13 — retuned after an empirical check: the v12 coefficients (0.50 resistance, 0.05 floor)
# measured across 10 seeded careers averaged 4.1 films/career pre-change, 2.7 post — a ~35% output
# cut from one gate, landing worse than this design's own "bleak newcomer" 30-year baseline even
# under a policy actively working every year. Not verified against §7.4's own simulation standard
# yet, but retuned toward it rather than left at a number known to be too harsh.
ATTACHMENT_OFFER_FAME_RESISTANCE_COEF = 0.30  # a bigger name has more offers competing for their time
ATTACHMENT_OFFER_MOMENTUM_PULL_COEF = 0.20   # real heat on the project is its own real pull
ATTACHMENT_OFFER_STANDING_PULL_COEF = 0.20   # so is a director's own reputation
ATTACHMENT_OFFER_TIER_BONUS = {"loyal": 0.15, "ally": 0.08, "familiar": 0.0, "stranger": -0.05, "rival": -0.10}
ATTACHMENT_OFFER_FLOOR = 0.15
ATTACHMENT_OFFER_CEILING = 0.95


def attachment_offer_probability(
    target_bankability: float, tier: str, attachment_type: str, project_momentum: float, director_standing_score: float,
) -> float:
    """The real "will they say yes" — reads the project's own current momentum (a package with real
    heat is a genuinely easier sell) and the director's own Standing (a bigger name is its own real
    pull), not just who's being asked. A bankable target resists more the bigger they already are —
    the same "harder to land, bigger swing if you do" tension casting's own bankable-star choice
    already carries, read from the offer side instead of the outcome side."""
    if attachment_type == ATTACHMENT_GENRE_FIT:
        base = ATTACHMENT_OFFER_BASE_GENRE_FIT
    elif attachment_type == ATTACHMENT_STUDIO_FAVORITE:
        base = ATTACHMENT_OFFER_BASE_STUDIO_FAVORITE
    else:
        fame_resistance = clamp(target_bankability, 0.0, 100.0) / 100.0
        pull = ATTACHMENT_OFFER_MOMENTUM_PULL_COEF * clamp(project_momentum, 0.0, 2.0) / 2.0
        pull += ATTACHMENT_OFFER_STANDING_PULL_COEF * clamp(director_standing_score, 0.0, 100.0) / 100.0
        base = ATTACHMENT_OFFER_BANKABLE_BASE - ATTACHMENT_OFFER_FAME_RESISTANCE_COEF * fame_resistance + pull
    tier_bonus = ATTACHMENT_OFFER_TIER_BONUS.get(tier, 0.0)
    return clamp(base + tier_bonus, ATTACHMENT_OFFER_FLOOR, ATTACHMENT_OFFER_CEILING)


@dataclass(frozen=True)
class Attachment:
    attachment_id: str  # a real Rolodex npc_id, or a synthetic "cold_<n>" for an untracked pick
    bankability: float
    attachment_type: str = ATTACHMENT_BANKABLE
    quarters_attached: int = 0


# The longer a project sits with someone attached but not yet shooting, the more likely they've
# got somewhere else to be — a real, growing risk, not a one-time coin flip at attach time.
ATTACHMENT_DROPOUT_BASE = 0.03
ATTACHMENT_DROPOUT_QUARTERS_COEF = 0.02
ATTACHMENT_DROPOUT_CEILING = 0.55


def attachment_dropout_probability(quarters_attached: int) -> float:
    return clamp(
        ATTACHMENT_DROPOUT_BASE + ATTACHMENT_DROPOUT_QUARTERS_COEF * quarters_attached,
        0.0, ATTACHMENT_DROPOUT_CEILING,
    )


def age_attachments(attachments: tuple[Attachment, ...], rng: random.Random) -> tuple[tuple[Attachment, ...], tuple[Attachment, ...]]:
    """Call once per dev-action year, on every attached person at once, independent of what action
    you took — the risk runs whether or not you're doing anything about it. Returns (kept, dropped)."""
    kept: list[Attachment] = []
    dropped: list[Attachment] = []
    for a in attachments:
        aged = replace(a, quarters_attached=a.quarters_attached + 1)
        if rng.random() < attachment_dropout_probability(aged.quarters_attached):
            dropped.append(aged)
        else:
            kept.append(aged)
    return tuple(kept), tuple(dropped)


def attach_star_favour_cost(base_cost: int, tier: str) -> int:
    discount = ATTACH_STAR_FAVOUR_DISCOUNT.get(tier, 1.0)
    return max(1, round(base_cost * discount))


def rival_poach_notoriety_cost(rivalry_depth: float) -> float:
    """rivalry_depth in [0,1] — how established the Rival relationship already is (§10.0's own
    relationship-state depth), not a flat number: a fresh rivalry costs less to provoke further
    than a long-standing one."""
    return RIVAL_POACH_NOTORIETY_LO + (RIVAL_POACH_NOTORIETY_HI - RIVAL_POACH_NOTORIETY_LO) * clamp(rivalry_depth, 0.0, 1.0)


# §7.4 v10 — two new dev actions, both ranges rather than flat numbers.
FAVOUR_MOMENTUM_LO = 0.20
FAVOUR_MOMENTUM_HI = 0.35
ADAPTATION_MOMENTUM_LO = 0.08
ADAPTATION_MOMENTUM_HI = 0.22


def favour_momentum(favour_size: float, rng: random.Random) -> float:
    """favour_size: the real Leverage favour balance spent (0+, typically a small int) — the size
    of the ask, not a flat toggle. Saturates at FAVOUR_SIZE_SATURATION so an enormous favour
    balance doesn't blow past the range's own ceiling."""
    frac = clamp(favour_size / FAVOUR_SIZE_SATURATION, 0.0, 1.0)
    return FAVOUR_MOMENTUM_LO + (FAVOUR_MOMENTUM_HI - FAVOUR_MOMENTUM_LO) * frac + rng.gauss(0.0, ATTACH_STAR_NOISE_SD)


FAVOUR_SIZE_SATURATION = 5.0


def adaptation_momentum(licensing_cost_fraction: float, source_type: str = "novel") -> float:
    """licensing_cost_fraction in [0,1] — how much of this source's own real option-cost ceiling
    (adaptation_option_cost) you actually paid. A cut-rate option on obscure material barely moves
    momentum; paying closer to the going rate pulls harder — no rng here, this one is a pure
    economic trade, not a roll. source_type scales the payoff by ADAPTATION_SOURCE_AUDIENCE_BONUS
    — design/part-09 §9.4's own "built-in audience" column: a toy line or comic brings a real,
    existing fanbase into the room that a foreign remake or public-domain public-domain property
    doesn't, and that shows up here as more momentum for the same fraction paid."""
    frac = clamp(licensing_cost_fraction, 0.0, 1.0)
    base = ADAPTATION_MOMENTUM_LO + (ADAPTATION_MOMENTUM_HI - ADAPTATION_MOMENTUM_LO) * frac
    return base * ADAPTATION_SOURCE_AUDIENCE_BONUS.get(source_type, 1.0)


# v20 — design/part-09-genres-franchises-and-tie-ins.md §9.4's own "where scripts come from" table
# names real, distinct source types, each with its own rights-cost tier and built-in-audience size
# — "option_adaptation" used to treat every source identically (one flat 3% ceiling, one flat
# momentum payoff), which both flattened that table into nothing and made the "cost" a fixed
# percentage regardless of what was actually being optioned, when in reality a public-domain novel
# and a toy line are nowhere near the same negotiation. Reusing the design doc's own qualitative
# tiers (Cheap/Moderate/High/Very high/Free rights cost; None/Small/Large/Enormous built-in
# audience) rather than inventing a new axis.
ADAPTATION_SOURCE_TYPES = (
    "public_domain", "foreign_remake", "novel", "stage_play", "true_story", "comic", "video_game", "toy_line",
)
ADAPTATION_SOURCE_COST_CEILING_FRACTION = {
    "public_domain": 0.0,     # Free
    "foreign_remake": 0.015,  # Low-moderate
    "novel": 0.03,            # Moderate
    "stage_play": 0.03,       # Moderate
    "true_story": 0.035,      # "Life rights" — its own moderate-ish real cost
    "comic": 0.07,            # High
    "video_game": 0.07,       # High
    "toy_line": 0.12,         # Very high
}
ADAPTATION_SOURCE_AUDIENCE_BONUS = {
    "public_domain": 0.6,   # "Everyone knows it" — but so does every rival studio
    "foreign_remake": 0.6,  # None domestically
    "novel": 0.9,           # Small, loyal
    "stage_play": 0.8,      # Prestige audience, not a mass one
    "true_story": 0.9,      # Moderate
    "comic": 1.3,           # Large, vocal
    "video_game": 1.3,      # Large, young
    "toy_line": 1.6,        # Enormous
}


def adaptation_option_cost(budget_ask: float, licensing_cost_fraction: float, source_type: str = "novel") -> float:
    """v19/v20 — a real production cost, not a fixed percentage: the ceiling itself varies by
    source_type (ADAPTATION_SOURCE_COST_CEILING_FRACTION), and licensing_cost_fraction [0,1] is how
    much of THAT ceiling you actually offered — haggling a toy line down still costs more in
    absolute terms than paying full price for a public-domain novel."""
    frac = clamp(licensing_cost_fraction, 0.0, 1.0)
    ceiling_fraction = ADAPTATION_SOURCE_COST_CEILING_FRACTION.get(source_type, ADAPTATION_SOURCE_COST_CEILING_FRACTION["novel"])
    return ceiling_fraction * budget_ask * frac


# v26 — every new pitch started at the same flat momentum (0.5) whether it came from a total
# rookie or a proven, high-Standing director — a real gap: a studio doesn't greet a bankable
# director's tenth pitch with zero built-in interest the way it would a stranger's first one.
# Neutral at Standing 50 lands exactly on the old flat default (0.5), so an average director's
# pace is completely unchanged — this only speeds up directors who've actually earned it, rather
# than lowering the bar for everyone (the blunt, rejected alternative was GREENLIGHT_BASE_
# PROBABILITY itself, a global constant that would have sped up every director, not just this).
INITIAL_MOMENTUM_NEUTRAL_STANDING = 50.0
INITIAL_MOMENTUM_NEUTRAL = 0.5
INITIAL_MOMENTUM_LO = 0.25   # at Standing 0 — a genuine cold-pitch struggle
INITIAL_MOMENTUM_HI = 2.0    # at Standing 100 — a real, felt head start


def initial_momentum(standing_score: float) -> float:
    s = clamp(standing_score, 0.0, 100.0)
    if s >= INITIAL_MOMENTUM_NEUTRAL_STANDING:
        frac = (s - INITIAL_MOMENTUM_NEUTRAL_STANDING) / (100.0 - INITIAL_MOMENTUM_NEUTRAL_STANDING)
        return INITIAL_MOMENTUM_NEUTRAL + (INITIAL_MOMENTUM_HI - INITIAL_MOMENTUM_NEUTRAL) * frac
    frac = (INITIAL_MOMENTUM_NEUTRAL_STANDING - s) / INITIAL_MOMENTUM_NEUTRAL_STANDING
    return INITIAL_MOMENTUM_NEUTRAL - (INITIAL_MOMENTUM_NEUTRAL - INITIAL_MOMENTUM_LO) * frac


# v21 — Vision and Craft were nearly interchangeable in practice: both fed director_skill at
# similar weight, and rewrite_quality_gain blends them 50/50 with no other real distinction
# between them. Vision's only genuinely separate consequence was a COST (overage_percent's
# ambition term) — never a payoff of its own. Real research on Michael Bay's own critical
# discourse names the actual real-world axis this was missing: scale/spectacle draws an audience
# independent of the story's own quality ("style over substance" is the specific, common
# complaint) — a lever genre_demand/cast_star_power already model for OTHER inputs, but nothing
# reads Vision into it. Deliberately small/capped (nudge, not dominate) and reaches ONLY
# `opening` (actor/reception.py) — never audience_score, never critic_score — so an ambitious,
# expensive-looking production can sell tickets on scale alone without becoming a backdoor
# quality signal that would also (incorrectly) flatter its critical reception.
DIRECTOR_SPECTACLE_BONUS_NEUTRAL = 50.0
DIRECTOR_SPECTACLE_BONUS_MAX = 10.5  # v35 — down from 12.0 at Vision 100 (v36 softened further
# from an initial 9.0 — too harsh a cut). Real, genuine diminishing returns on top:
# DIRECTOR_SPECTACLE_BONUS_POWER < 1.0 means the curve rewards moving off the floor generously but
# the LAST few Vision points toward the cap buy less than a straight line would — both changes
# needed together, since a curve reshape alone (frac**p for p<1) actually raises the value at any
# given frac<1 versus a flat line; only cutting MAX itself keeps a near-maxed director from landing
# at (or above) the old linear number.
DIRECTOR_SPECTACLE_BONUS_POWER = 0.65  # v36 — up from an initial 0.5, a gentler diminishing curve


def director_spectacle_bonus(vision: float) -> float:
    v = clamp(vision, 0.0, 100.0)
    frac = max(0.0, v - DIRECTOR_SPECTACLE_BONUS_NEUTRAL) / (100.0 - DIRECTOR_SPECTACLE_BONUS_NEUTRAL)
    return DIRECTOR_SPECTACLE_BONUS_MAX * frac ** DIRECTOR_SPECTACLE_BONUS_POWER


# §7.4 v10 — development isn't silent between actions. The event's own odds/type selection reads
# real world state (GenreHeat, a tracked Rolodex Rival) and lives in simulation/_director.py, which
# already composes across packages; this module only applies an already-decided magnitude, staying
# exactly as generic as every action above it.
EVENT_MOMENTUM_LO = 0.10
EVENT_MOMENTUM_HI = 0.18


def apply_event_delta(project: DevProject, magnitude: float) -> DevProject:
    return replace(project, momentum=max(0.0, project.momentum + magnitude))


def package_strength(attached_star_bankability: float, script_quality: float, director_standing: float) -> float:
    return (
        PACKAGE_STAR_WEIGHT * attached_star_bankability
        + PACKAGE_SCRIPT_WEIGHT * script_quality
        + PACKAGE_STANDING_WEIGHT * director_standing
    )


def difficulty(budget_millions: float) -> float:
    return DIFFICULTY_BASE + DIFFICULTY_COEF * math.log10(budget_millions + 1.0)


# A real "you're only as good as your last few pictures" force — a director whose films keep
# losing money should find backing progressively harder to get, which greenlight_probability never
# read at all before this: package_strength/difficulty/momentum all reset with every new pitch, so
# a five-flop streak and a clean track record could assemble an identical package and get treated
# identically. Deliberately soft: a real, felt effect, not a crushing one. Two things keep it that
# way — it only ever moves off a real losing streak (a director sitting at or above breakeven pays
# nothing at all), and it scales with budget on a LOG curve, so a small, cheap project is barely
# touched while a real tentpole ask is where a bad track record actually bites — the same "harder
# to get the big swing, not impossible to work at all" shape a real flop-prone director faces.
BANKABILITY_ROI_CENTRE = 1.0  # breakeven or better — no penalty at all
BANKABILITY_BUDGET_LOG_BASE = 10.0  # $M — a project at or under this scale barely feels it
BANKABILITY_COEF = 0.15
# v33 — tightened from 0.75. Checked empirically first: the old floor was a REAL, frequently-
# engaged clamp (a total wipeout on a tentpole ask wants a ~0.90 penalty, ten times deeper than the
# old 0.25 ceiling allowed), but a merely-struggling director (a real slump, not a total disaster —
# trailing_roi=0.3 on a $60M ask) never reached the floor at all (raw penalty ~0.22) — so this only
# ever tightens the specific "chronic disaster chasing the biggest budgets" case, not ordinary bad
# luck. A director who keeps destroying money at the biggest scale should find that scale close to
# off-limits, not just "somewhat harder" — still not a hard lockout (momentum has no ceiling of its
# own, so patience can still eventually clear even a bad multiplier), and trailing_roi/trailing_
# overage's own recency decay means this is never permanent — but a real, felt bite at the top end.
BANKABILITY_FLOOR = 0.45  # even a real flop streak on the biggest ask only ever costs this much

# v18 — the ROI-only version above only ever penalized a director for losing a studio's money,
# never for reliably running late/over-budget getting there — the missing career-wide half of
# "reputation for being expensive" (schedule_trust_penalty/financing_studio_weight only ever
# dents trust with the ONE studio actually burned). Same shape as the ROI shortfall: a real
# tolerance band first (some overage is just how movies get made — OVERAGE_BANKABILITY_NEUTRAL),
# then a real, budget-scaled bite past it, sharing the same overall floor so the two track records
# can't stack into something crushing together.
OVERAGE_BANKABILITY_NEUTRAL = 0.25  # up to 25% over schedule costs nothing at all
OVERAGE_BANKABILITY_COEF = 0.6


def bankability_multiplier(trailing_roi: float, budget_ask: float, trailing_overage: float = 0.0) -> float:
    shortfall = max(0.0, BANKABILITY_ROI_CENTRE - trailing_roi)
    overage_shortfall = max(0.0, trailing_overage - OVERAGE_BANKABILITY_NEUTRAL)
    budget_scale = max(0.0, math.log10(max(budget_ask, 0.0) / BANKABILITY_BUDGET_LOG_BASE + 1.0))
    penalty = BANKABILITY_COEF * shortfall * budget_scale + OVERAGE_BANKABILITY_COEF * overage_shortfall * budget_scale
    return clamp(1.0 - penalty, BANKABILITY_FLOOR, 1.0)


# A self-financed or hire-guaranteed project used to greenlight AND fully resolve in the same
# instant, the moment any dev action landed — a $2M passion project and a $300M tentpole cost the
# exact same thing: one quarter's attention. Real productions don't work that way. Budget drives a
# real baseline (same log-scaled "bigger ask, taller order" shape used everywhere else in this
# design); Efficiency shifts that baseline by a BOUNDED percentage rather than an unbounded swing —
# a terrible Efficiency score alone can't turn a modest production into a multi-year fiasco, it can
# only make an already-big one meaningfully worse. Anchored so a small ask (~$2M) costs about a
# quarter and a real tentpole (~$170-300M) costs 5-6 quarters BEFORE Efficiency ever enters in —
# only the compounding of a huge budget AND poor Efficiency together should ever approach the
# absolute ceiling.
DIRECTOR_QUARTERS_BASE = -0.223
DIRECTOR_QUARTERS_BUDGET_COEF = 2.563

# v35 — real spectacle costs real time, the same way a bigger budget does: chasing Vision purely
# for director_spectacle_bonus's own audience pull used to be a free lunch, with zero read anywhere
# on how long the shoot actually takes. Same neutral-50 convention as spectacle_bonus itself (an
# average director's own films aren't "slow" for having ordinary ambition) — only pushing Vision
# meaningfully past neutral adds real baseline quarters, on top of whatever budget already demands,
# BEFORE Efficiency's own multiplier gets a chance to compress it back out.
DIRECTOR_QUARTERS_VISION_COEF = 3.0  # v36 — deliberately left soft. An earlier tuning pass pushed
# this to 7.0 specifically so max Vision alone would force even a near-zero-budget film past the
# once-a-year 4-quarter resolution floor (advance_shoots_and_resolve's own SHOOT_QUARTERS_PER_YEAR
# granularity) — closing off low-budget spam entirely. Walked back on purpose: a cheap production
# staying fast even at max Vision is fine, even intended — only a genuine tentpole ask should feel
# real friction from chasing spectacle. At this build's own Vision (96) and Efficiency (90), a
# $150M+ ask now needs real, felt extra time; a $5M one barely notices.

# v13 fix — the first version of this multiplier was linear across the whole 0-100 range, which
# meant even Efficiency 0 (the worst possible score) only reached 1.35x — a director this
# disorganized read as barely slower than an average one. Real, felt severity needs two things a
# flat line can't give: a genuine neutral point (an average director's own films shouldn't read as
# slow at all) and a curve that actually punishes the bad end hard, not a token nudge. Efficiency
# 50 is neutral (1.0x, unchanged from an untouched baseline); above it, a competent director gets a
# real, bounded speed-up down to DIRECTOR_QUARTERS_EFF_MULT_LO; below it, severity climbs on a
# curve (DIRECTOR_QUARTERS_EFF_POWER < 1, convex) rather than a straight line — a merely-below-
# average director is only a little slower, but a genuinely chaotic one (Efficiency in the teens or
# below) runs up against real, severe delay, all the way to DIRECTOR_QUARTERS_EFF_MULT_HI at the
# absolute floor.
DIRECTOR_QUARTERS_EFF_NEUTRAL = 50.0
DIRECTOR_QUARTERS_EFF_MULT_LO = 0.68  # at Efficiency 100 — the fastest this ever gets
DIRECTOR_QUARTERS_EFF_MULT_HI = 4.3   # at Efficiency 0 — genuinely severe, not a token worst case
DIRECTOR_QUARTERS_EFF_POWER = 1.6     # < 1 would front-load the punishment near the neutral point;
# > 1 (used here) keeps it mild just below neutral and lets it climb hard only as Efficiency gets
# genuinely bad — a 35 reads as "a bit slow," a 10 reads as "a real problem," not the same scale.

# The absolute worst case, full stop — no combination of budget and Efficiency can ever exceed
# this, however bad. A genuinely troubled, huge, badly-run production tops out at 2 years, not an
# unbounded spiral.
#
# v30 — DIRECTOR_QUARTERS_SOLO_CEILING (a much tighter 5-quarter cap that applied whenever no
# OTHER project was simultaneously in development) removed outright. It was quietly neutering
# Efficiency's own worst case: a genuinely catastrophic director (Efficiency at or near the floor)
# should be able to run a production for the full 2 years this ceiling allows, budget size and
# real severity permitting — not get capped down to 1.25 years just because a particular
# development policy never happened to have a second project open at the exact moment this one
# greenlit. Whether a second project is in development is a policy/attention choice, not something
# that should change how bad an actually badly-run shoot is allowed to get.
DIRECTOR_QUARTERS_ABSOLUTE_CEILING = 8

# Only one production can ever be actively shooting at once — a director can develop several
# projects in parallel (writing, packaging, courting financiers) but can't physically be on two
# sets at the same time. Without this, nothing stops several tentpoles from each running their own
# independent countdown in parallel and all wrapping around the same time — the same absurdity as
# instant resolution, just spread across projects instead of stacked in one.
MAX_CONCURRENT_SHOOTS = 1


def director_quarters_efficiency_multiplier(efficiency: float) -> float:
    eff = clamp(efficiency, 0.0, 100.0)
    if eff >= DIRECTOR_QUARTERS_EFF_NEUTRAL:
        frac = (eff - DIRECTOR_QUARTERS_EFF_NEUTRAL) / (100.0 - DIRECTOR_QUARTERS_EFF_NEUTRAL)
        return 1.0 - (1.0 - DIRECTOR_QUARTERS_EFF_MULT_LO) * frac
    frac = (DIRECTOR_QUARTERS_EFF_NEUTRAL - eff) / DIRECTOR_QUARTERS_EFF_NEUTRAL
    return 1.0 + (DIRECTOR_QUARTERS_EFF_MULT_HI - 1.0) * (frac ** DIRECTOR_QUARTERS_EFF_POWER)


# v15 — momentum (attaching stars, calling in favours, courting financiers) is packaging/dealmaking,
# not on-set schedule discipline — Efficiency's own established identity everywhere else in this
# file. Command (leadership/authority/persuasion) is the honest fit for "how fast do things move
# in a room." Kept deliberately smaller than the efficiency-on-quarters curve above: a director's
# ability to get people to say yes faster is a real but secondary factor next to the offer itself
# (target bankability, tier, the project's own momentum, Standing) which already does the heavy
# lifting in attachment_offer_probability — this should nudge, not dominate.
# v16 — widened from (0.85, 1.3) after the first pass barely registered above noise in career
# sims. Also fixed a real direction bug here: this multiplies momentum GAIN directly (unlike
# director_quarters_efficiency_multiplier, which multiplies a duration — where LOWER is better).
# For a gain, higher command must mean a HIGHER multiplier, not lower — the first version of this
# curve copied the quarters-multiplier's shape verbatim without flipping that, so Command 100
# quietly gave WORSE momentum gain than Command 0. Still meant to nudge rather than dominate the
# way Efficiency's own quarters curve does, but needed real room to show up against seed variance.
DIRECTOR_MOMENTUM_COMMAND_NEUTRAL = 50.0
DIRECTOR_MOMENTUM_COMMAND_BOOST_HI = 2.0   # at Command 100 — a real, felt boost
DIRECTOR_MOMENTUM_COMMAND_DRAG_LO = 0.32   # at Command 0 — a real, felt drag


def director_momentum_command_multiplier(command: float) -> float:
    cmd = clamp(command, 0.0, 100.0)
    if cmd >= DIRECTOR_MOMENTUM_COMMAND_NEUTRAL:
        frac = (cmd - DIRECTOR_MOMENTUM_COMMAND_NEUTRAL) / (100.0 - DIRECTOR_MOMENTUM_COMMAND_NEUTRAL)
        return 1.0 + (DIRECTOR_MOMENTUM_COMMAND_BOOST_HI - 1.0) * frac
    frac = (DIRECTOR_MOMENTUM_COMMAND_NEUTRAL - cmd) / DIRECTOR_MOMENTUM_COMMAND_NEUTRAL
    return 1.0 - (1.0 - DIRECTOR_MOMENTUM_COMMAND_DRAG_LO) * frac


def quarters_for_directed_film(budget_ask: float, efficiency: float, vision: float = 50.0) -> int:
    vision_term = DIRECTOR_QUARTERS_VISION_COEF * max(0.0, clamp(vision, 0.0, 100.0) - 50.0) / 50.0
    baseline = (
        DIRECTOR_QUARTERS_BASE + DIRECTOR_QUARTERS_BUDGET_COEF * math.log10(max(budget_ask, 0.01) + 1.0) + vision_term
    )
    multiplier = director_quarters_efficiency_multiplier(efficiency)
    return int(round(clamp(baseline * multiplier, 1.0, DIRECTOR_QUARTERS_ABSOLUTE_CEILING)))


# A studio's own patience, set at the deal — before anyone knows how THIS shoot will actually go.
# Budget-only at its core, deliberately no raw Efficiency term: the studio can't see a director's
# own attribute sheet, only their track record. v31 — that track record is real and already
# tracked (DirectorState.trailing_overage, the same recency-weighted "reputation for being
# expensive" read bankability_multiplier already prices into financing terms), so a studio signing
# a director with real history isn't budgeting blind the way a first-time pairing would be. Priced
# in as a genuine hedge, not a full prediction — STUDIO_EXPECTATION_TRAILING_OVERAGE_COEF partially,
# not fully, pads the baseline, because a studio hopes (but can't be sure) the next one goes better.
# Deliberately does NOT double-count what bankability_multiplier already does to financing terms —
# this only shifts what "on schedule" MEANS for schedule_trust_penalty's own read, so a chronic-but-
# consistent offender isn't ALSO bleeding trust every single time for repeating a pattern the studio
# already knew to expect going in; only a genuinely new, worse-than-their-own-history surprise still
# costs them. trailing_overage=0.0 (a fresh director, or any caller not passing it) leaves this
# exactly the flat budget-only baseline it always was — a pure, backward-compatible addition.
STUDIO_EXPECTATION_TRAILING_OVERAGE_COEF = 0.25  # v32 — halved from 0.5. The trust penalty was
# softening too far for a consistently bad director (observed ~50% reduction at realistic worst-
# case trailing_overage) -- still a real, felt hedge, just a smaller one, so chronic disorganization
# still costs real trust, not just reduced trust.
# v31 fix — checked empirically (a 10-career, worst-case-Efficiency sample) rather than assumed:
# trailing_overage is an EMA of overage_percent, itself clamped to OVERAGE_HI=1.20 — an average of
# values that can't exceed 1.20 can never itself exceed 1.20 either, so a 1.5 cap here was already
# unreachable dead code, never once engaging even at Efficiency 0 (observed max ~1.05 across 184
# real greenlights). Tightened to match what the system can actually produce, so this constant
# means what it says rather than implying a wider range than trailing_overage can ever reach.
STUDIO_EXPECTATION_TRAILING_OVERAGE_CAP = 1.2  # matches OVERAGE_HI's own real ceiling directly —
# a studio's own padding tops out at +60% (1 + 0.5*1.2) even against the most chaotic real track
# record this engine can produce, not unbounded.


def studio_expected_quarters(budget_ask: float, trailing_overage: float = 0.0) -> float:
    baseline = DIRECTOR_QUARTERS_BASE + DIRECTOR_QUARTERS_BUDGET_COEF * math.log10(max(budget_ask, 0.01) + 1.0)
    padding = 1.0 + STUDIO_EXPECTATION_TRAILING_OVERAGE_COEF * clamp(
        trailing_overage, 0.0, STUDIO_EXPECTATION_TRAILING_OVERAGE_CAP,
    )
    return clamp(baseline * padding, 1.0, DIRECTOR_QUARTERS_ABSOLUTE_CEILING)


# The real, separate cost of blowing past what you told the studio to expect — distinct from the
# ROI hit the overrun's own inflated budget already causes. A modest, real trust bite per quarter
# over, capped so one bad production can't zero out a relationship outright.
SCHEDULE_TRUST_PENALTY_PER_QUARTER = 3.0
SCHEDULE_TRUST_PENALTY_CAP = 25.0


def schedule_trust_penalty(quarters_taken: int, expected_quarters: float) -> float:
    overrun_quarters = max(0.0, quarters_taken - expected_quarters)
    return min(SCHEDULE_TRUST_PENALTY_CAP, SCHEDULE_TRUST_PENALTY_PER_QUARTER * overrun_quarters)


# BANKABILITY_ROI_CENTRE=1.0 is a wide release's own breakeven bar — the only strategy where
# roi=1.0 genuinely means "made its money back at the scale it was attempting." actor.release.
# apply_release_strategy's own Limited/Festival gross formulas cap out far below that by
# construction (a platform release was never chasing wide-release box office), so trailing_roi
# judging every film against the same 1.0 bar conflated "succeeded at a smaller scale" with
# "failed" — a director who mostly works Limited/Festival could never build a track record no
# matter how well those films actually did within their own format.
#
# The one deliberate exception: an unsold festival submission (gross<=0 on a Festival strategy —
# actor.release.apply_release_strategy's own "unsold" branch) is judged at the full wide-release
# bar, not a lowered one — nobody bought the film at any scale, a real failure regardless of
# format, not a smaller-scale success.
BANKABILITY_ROI_CENTRE_LIMITED = 0.55
BANKABILITY_ROI_CENTRE_FESTIVAL_ACQUIRED = 0.35


def bankability_roi_centre(release_strategy: str, gross: float) -> float:
    if release_strategy == "limited":
        return BANKABILITY_ROI_CENTRE_LIMITED
    if release_strategy == "festival" and gross > 0.0:
        return BANKABILITY_ROI_CENTRE_FESTIVAL_ACQUIRED
    return BANKABILITY_ROI_CENTRE


def format_adjusted_roi(roi: float, release_strategy: str, gross: float) -> float:
    """Rescales roi so that clearing THIS release strategy's own real breakeven reads as exactly
    1.0 — the same number bankability_multiplier/the "two consecutive profitable films" streak
    already compare everything else against. A Limited film that broke exactly even for a Limited
    release (roi == BANKABILITY_ROI_CENTRE_LIMITED) rescales to 1.0, not 0.55; a Limited film at
    half that still rescales to a real, proportional 0.5 shortfall. Wide/Streaming/Shelved are
    untouched (their own centre is already 1.0, an identity rescale)."""
    centre = bankability_roi_centre(release_strategy, gross)
    if centre <= 0.0:
        return roi
    return roi * (BANKABILITY_ROI_CENTRE / centre)


def greenlight_probability(pkg_strength: float, diff: float, momentum: float, bankability: float = 1.0) -> float:
    """momentum has no upper bound of its own (it compounds across quarters, uncapped) and enters
    here as a flat multiplier — nothing else in this formula stops the product from exceeding 1.0
    at a high enough momentum, which isn't a meaningful probability. Never observed in practice at
    realistic momentum/package values, but clamped explicitly so it's provably safe rather than
    safe-by-coincidence.

    bankability: bankability_multiplier(trailing_roi, budget_ask) — a director's own recent
    track record pulling this down, more so the bigger the ask. Default 1.0 (no penalty) leaves
    every existing call site's behavior exactly unchanged."""
    return clamp(GREENLIGHT_BASE_PROBABILITY * sigmoid(GREENLIGHT_SLOPE * (pkg_strength - diff)) * momentum * bankability, 0.0, 1.0)


@dataclass(frozen=True)
class DevProject:
    script_id: str
    momentum: float = 0.5
    budget_ask: float = 30.0
    attached_star_bankability: float = 0.0
    quarters_in_dev: int = 0
    frozen: bool = False
    dead: bool = False
    self_financed: bool = False  # you're the studio now — see apply_action("self_finance")
    franchise_id: str | None = None  # v27 — directors now participate in the SAME shared
    # simulation._franchises.py pool the actor track already uses (one FullState.franchises dict,
    # not a second parallel system). None means an original, non-franchise project.
    installment_number: int = 1  # 1 for an original/new-franchise pitch; N for a sequel — mirrors
    # actor.offers.Role's own field exactly, same meaning.
    locked_franchise_audience_bonus: float = 0.0  # rolled once at start_development() time (genre.
    # franchise.sequel_bonus + spacing_modifier + director_continuity_bonus if you directed the
    # prior installment yourself), same "lock at greenlight-adjacent time, read at resolution"
    # shape schedule_overage/box_office_bonus_share/negotiated_fee_share already use — not re-rolled
    # if the franchise's own state moves before this film actually resolves.
    is_adaptation: bool = False  # v23 — set True the moment "option_adaptation" is actually taken.
    # actor.studios.decide_marketing_spend/effective_rating_ceiling both read an is_franchise_or_
    # adaptation flag (a real marketing-discount and rating-ceiling difference for adapted material)
    # that simulation._director hardcoded False regardless — a real project that actually licensed
    # IP got none of the real-world marketing/rating treatment adaptations get. Never set back to
    # False once true.
    guaranteed_greenlight: bool = False  # §7.13 v10 — a director-for-hire offer: skips the
    # momentum/Difficulty roll entirely, but (unlike self_financed) the studio is still financing
    # it and still holds final cut by default — the two flags are independent on purpose.
    attachments: tuple["Attachment", ...] = ()  # §7.4 v11 — the real, ageing roster. attached_
    # star_bankability stays the derived read PackageStrength/Casting already consume: the
    # strongest "bankable"-type attachment, not the whole roster — genre_fit/studio_favorite
    # attachments move the project a different way (see attach_momentum's own docstring).
    screenwriter_skill: float = SCREENWRITER_SKILL_MEAN  # §7.4 v18 — whoever's actually writing
    # this project, a hidden per-project trait sampled once at start_development(). Never shown to
    # the player as a raw number — it's read entirely through how "rewrite" actually goes.
    box_office_bonus_type: str | None = None  # §7.4 v24 — studio-backed only; negotiated once at
    # start_development() alongside the flat director's fee, same leverage.negotiated_bonus_share()
    # shape actors already use. None means no bonus was on the table (Standing too low) or this
    # project isn't studio-backed (self-financed/hire already have their own income shape).
    box_office_bonus_share: float = 0.0
    negotiated_fee_share: float | None = None  # v19 — the real, negotiated cut of budget this
    # project's own director fee actually landed at (leverage.approvals.negotiated_director_fee_
    # share), rolled once at start_development()/accept_hire_offer() time, same shape/timing as
    # box_office_bonus_share above. None only for a self-financed project (no fee at all — full net
    # proceeds instead) or a not-yet-negotiated fixture built directly in a test.
    financing_studio_id: str | None = None  # v11 fix — a studio-backed project now knows WHICH
    # studio it's courting from the moment development starts (set once in start_development, via
    # the same actor.studios.pick_studio() call simulation._director._resolve_directed_film used
    # to only make fresh at resolution time — a real inconsistency before this: the studio scored
    # for trust purposes and the studio actually financing the film could silently be two different
    # ones). None for a self-financed project (no studio relationship exists) or a hire offer (its
    # own separate guaranteed-greenlight terms, not a courted relationship).
    quarters_remaining_in_shoot: int | None = None  # None while still in development; a real,
    # counting-down int once greenlit (see quarters_for_directed_film) — the project stays in
    # state.projects the whole time, occupying a real slate slot, but no longer accepts dev actions.
    locked_schedule_overage: float | None = None  # rolled once, at the moment of greenlight (via
    # director.shoot_style.overage_percent, off attachment-driven chaos — known before the shoot
    # even starts), reused at wrap time instead of re-rolled, so the schedule that determined how
    # long the wait was is the same schedule the final budget/reception actually reads.
    locked_quarters_needed: int | None = None  # the ORIGINAL total this project was assigned at
    # greenlight — quarters_remaining_in_shoot counts down to 0 and loses that number, but the
    # schedule-trust penalty (simulation.session.Session.advance_directing) needs to know how long
    # it actually took, not just that it's done.
    locked_studio_expected_quarters: float | None = None  # None for a self-financed project (no
    # studio patience to burn); the studio's own budget-only expectation otherwise, set at the same
    # moment financing_studio_id is.
    locked_momentum_at_greenlight: float | None = None  # rolled once, at the moment of greenlight —
    # a studio-backed project can't greenlight without momentum clearing greenlight_probability's own
    # bar, so it never needs this read. A self-financed project skips that check entirely (you ARE
    # the studio saying yes), so this is the one thing standing in for it afterward: how real was
    # the package you actually greenlit, not just whether you could afford to.


def apply_action(project: DevProject, action: str, script_quality_delta: float = 0.0) -> DevProject:
    """The flat, no-extra-inputs path — still correct for "rewrite"/"cut_budget"/etc. For
    "attach_star", "call_in_favour", and "option_adaptation", callers who have the real scaling
    inputs (target Bankability/tier, favour size, licensing spend) should use attach_star_momentum()
    / favour_momentum() / adaptation_momentum() directly instead and apply the result themselves —
    this fallback exists only so a caller with no such context (tests, a headless sim) still gets a
    sane, mid-range number rather than an error."""
    if action == "rewrite":
        return replace(project, momentum=project.momentum + REWRITE_MOMENTUM)
    if action == "attach_star":
        return replace(project, momentum=project.momentum + ATTACH_STAR_MOMENTUM)
    if action == "call_in_favour":
        return replace(project, momentum=project.momentum + (FAVOUR_MOMENTUM_LO + FAVOUR_MOMENTUM_HI) / 2.0)
    if action == "option_adaptation":
        return replace(project, momentum=project.momentum + (ADAPTATION_MOMENTUM_LO + ADAPTATION_MOMENTUM_HI) / 2.0)
    if action == "cut_budget":
        return replace(
            project,
            momentum=project.momentum + CUT_BUDGET_MOMENTUM,
            budget_ask=max(1.0, project.budget_ask * 0.7),
        )
    if action == "new_financier":
        return replace(project, momentum=project.momentum + NEW_FINANCIER_MOMENTUM)
    if action == "take_to_market":
        return replace(project, momentum=project.momentum + MARKET_MOMENTUM)
    if action == "self_finance":
        # Only reached once the project is already yours (see attempt_self_finance below — the
        # acquisition itself, from a studio that hasn't yet let go, is a separate step with its own
        # rng/cost and doesn't route through here). A renewed vote of confidence on a project you
        # already own: momentum resets, self_financed was already True and stays that way.
        return replace(project, momentum=1.0)
    if action == "drawer":
        return replace(project, frozen=True)
    return project


# A self-financed greenlight skips greenlight_probability entirely — there's no studio's own
# momentum bar to clear, you ARE the yes. But "enough momentum" isn't a flat number: a $2M passion
# project genuinely doesn't need much behind it to feel real, while a $300M tentpole with the same
# thin momentum a scrappy indie would've been fine with reads as a genuine gamble, not confidence.
# Reuses difficulty() — already the engine's own "how big an ask is this" read, the same one
# momentum_budget_discount and package_strength already scale against — rather than a second,
# disconnected budget curve.
SELF_FINANCE_MOMENTUM_THRESHOLD_BASE = 0.22  # MOMENTUM_BANDS[1][0] ("fading") — a near-zero-budget
# ask clears this almost automatically, same free pass difficulty()/momentum_budget_discount give
# a small project everywhere else in this design.
SELF_FINANCE_MOMENTUM_THRESHOLD_BUDGET_COEF = 2.8  # a $300M-scale ask (difficulty ~85) pushes the
# bar up past 1.7 — genuinely hard to clear even for an established director (this director's own
# momentum at greenlight typically runs 1.3-2.0 off Standing alone), the same way a real tentpole
# is genuinely hard to greenlight for real at a studio regardless of who's attached.
SELF_FINANCE_LOW_MOMENTUM_QUALITY_COEF = 20.0  # no separate cap — craft_contribution's own 0-100
# clamp (simulation._director._resolve_directed_film) is the only ceiling on how much a genuinely
# rushed, huge-budget self-financed greenlight can cost. A near-miss stays mild; showing up with
# almost nothing behind a real tentpole can gut the film outright, the same way it would in reality.


def self_finance_momentum_threshold(budget_millions: float) -> float:
    diff = difficulty(budget_millions)
    return SELF_FINANCE_MOMENTUM_THRESHOLD_BASE + SELF_FINANCE_MOMENTUM_THRESHOLD_BUDGET_COEF * max(
        0.0, diff - DIFFICULTY_BASE,
    ) / 100.0


def self_finance_rush_penalty(momentum_at_greenlight: float, budget_millions: float) -> float:
    threshold = self_finance_momentum_threshold(budget_millions)
    shortfall = max(0.0, threshold - momentum_at_greenlight)
    return SELF_FINANCE_LOW_MOMENTUM_QUALITY_COEF * shortfall


def studio_release_probability(momentum: float) -> float:
    """Whether the financing studio just lets a stalled project go for nothing, rather than making
    you pay for it. A low-momentum project isn't worth holding onto; one with real heat, they don't
    just hand over."""
    return clamp(SELF_FINANCE_FREE_RELEASE_BASE - SELF_FINANCE_FREE_RELEASE_MOMENTUM_COEF * momentum, 0.05, 0.9)


def self_finance_buyout_cost(budget_ask: float, installment_number: int = 0, years_since_last_release: int = 0) -> float:
    """installment_number 0/1: an original, or a brand-new franchise's own first entry — the flat
    fraction of budget, unchanged (years_since_last_release doesn't apply — there's no "since last
    time" yet, same convention genre.franchise.spacing_modifier already uses). Otherwise, the
    franchise's track record (installment_number, same shape leverage.indispensability.
    RECAST_COST_COEF already prices into a recast) sets a real premium on top of the flat rate.
    That premium holds at full strength through SELF_FINANCE_FRANCHISE_GRACE_YEARS — a normal gap
    between installments, not dormancy — then decays the longer it's genuinely gone since the
    franchise last released anything (SELF_FINANCE_FRANCHISE_VALUE_DECAY), so a long-abandoned
    franchise costs close to the flat rate to buy out no matter how many installments it has, while
    one still on a healthy release rhythm costs its full track-record premium regardless of the
    exact gap."""
    if installment_number <= 1:
        return budget_ask * SELF_FINANCE_BUYOUT_FRACTION
    track_record_premium = SELF_FINANCE_FRANCHISE_VALUE_COEF * (installment_number - 1)
    years_dormant = max(0, years_since_last_release - SELF_FINANCE_FRANCHISE_GRACE_YEARS)
    decay = SELF_FINANCE_FRANCHISE_VALUE_DECAY ** years_dormant
    franchise_multiplier = min(1.0 + track_record_premium * decay, SELF_FINANCE_VALUE_MULTIPLIER_CAP)
    return budget_ask * SELF_FINANCE_BUYOUT_FRACTION * franchise_multiplier


@dataclass(frozen=True)
class SelfFinanceOutcome:
    project: DevProject
    acquired: bool  # True if the project is self_financed after this call — already was, or just became
    just_acquired: bool  # True only if it became True this call
    cost_paid: float = 0.0
    released_free: bool = False
    could_not_afford: bool = False


def attempt_self_finance(
    project: DevProject, rng: random.Random, available_money: float, years_since_last_release: int = 0,
) -> SelfFinanceOutcome:
    """The acquisition step: does the financing studio let this project go? A project already
    self-financed is a no-op here (already yours). Otherwise, roll studio_release_probability() —
    on a miss, the studio wants paid for it (self_finance_buyout_cost(), scaled by how long it's
    been since this franchise last actually released anything — see that function's own
    docstring), and the acquisition only goes through if available_money actually covers that.
    Doesn't touch momentum either way — this is a negotiation, not a development beat; the
    project's own progress is untouched by it. years_since_last_release: Session's to know (the
    real FullState.franchises calendar), same "this module stays money/world-agnostic otherwise"
    convention available_money already follows."""
    if project.self_financed:
        return SelfFinanceOutcome(project, acquired=True, just_acquired=False)
    if rng.random() < studio_release_probability(project.momentum):
        return SelfFinanceOutcome(replace(project, self_financed=True), acquired=True, just_acquired=True, released_free=True)
    cost = self_finance_buyout_cost(project.budget_ask, project.installment_number, years_since_last_release)
    if cost <= available_money:
        return SelfFinanceOutcome(replace(project, self_financed=True), acquired=True, just_acquired=True, cost_paid=cost)
    return SelfFinanceOutcome(project, acquired=False, just_acquired=False, could_not_afford=True)


def apply_neglect(project: DevProject) -> DevProject:
    """§7.4 v16 — a quarter's real action goes to exactly one project; every project you're
    *not* spending it on this quarter still pays for the neglect, the same momentum decay (and the
    same death floor) a failed greenlight attempt already applies, just without ever getting the
    attempt itself — no attention, no roll. A project you've deliberately put "in the drawer"
    (frozen) is the one real exception: that's an explicit choice to pause with no further cost,
    not neglect. Reuses advance_quarter's own decay/death shape rather than a second formula."""
    if project.frozen or project.dead:
        return project
    new_momentum = project.momentum * MOMENTUM_DECAY
    dead = new_momentum < MOMENTUM_DEATH_FLOOR
    return replace(project, momentum=new_momentum, quarters_in_dev=project.quarters_in_dev + 1, dead=dead)


def advance_quarter(project: DevProject, pkg_strength: float, rng: random.Random, bankability: float = 1.0) -> tuple[DevProject, bool]:
    """Returns (new_project, greenlit). bankability: see greenlight_probability's own docstring."""
    if project.frozen or project.dead:
        return project, False

    diff = difficulty(project.budget_ask)
    effective_momentum = project.momentum / momentum_budget_discount(diff)
    p = greenlight_probability(pkg_strength, diff, effective_momentum, bankability)
    if rng.random() < p:
        return replace(project, momentum=1.0), True

    new_momentum = project.momentum * MOMENTUM_DECAY
    dead = new_momentum < MOMENTUM_DEATH_FLOOR
    return replace(project, momentum=new_momentum, quarters_in_dev=project.quarters_in_dev + 1, dead=dead), False
