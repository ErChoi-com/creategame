"""design/part-07-the-director.md §7.4 — development hell: PackageStrength, Difficulty, the
greenlight roll, momentum, and one development action per project per year.
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

DEV_ACTIONS = ("rewrite", "attach_star", "cut_budget", "new_financier", "take_to_market", "self_finance", "drawer")


def package_strength(attached_star_bankability: float, script_quality: float, director_standing: float) -> float:
    return (
        PACKAGE_STAR_WEIGHT * attached_star_bankability
        + PACKAGE_SCRIPT_WEIGHT * script_quality
        + PACKAGE_STANDING_WEIGHT * director_standing
    )


def difficulty(budget_millions: float) -> float:
    return DIFFICULTY_BASE + DIFFICULTY_COEF * math.log10(budget_millions + 1.0)


def greenlight_probability(pkg_strength: float, diff: float, momentum: float) -> float:
    """momentum has no upper bound of its own (it compounds across quarters, uncapped) and enters
    here as a flat multiplier — nothing else in this formula stops the product from exceeding 1.0
    at a high enough momentum, which isn't a meaningful probability. Never observed in practice at
    realistic momentum/package values, but clamped explicitly so it's provably safe rather than
    safe-by-coincidence."""
    return clamp(GREENLIGHT_BASE_PROBABILITY * sigmoid(GREENLIGHT_SLOPE * (pkg_strength - diff)) * momentum, 0.0, 1.0)


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


def apply_action(project: DevProject, action: str, script_quality_delta: float = 0.0) -> DevProject:
    if action == "rewrite":
        return replace(project, momentum=project.momentum + REWRITE_MOMENTUM)
    if action == "attach_star":
        return replace(project, momentum=project.momentum + ATTACH_STAR_MOMENTUM)
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


def studio_release_probability(momentum: float) -> float:
    """Whether the financing studio just lets a stalled project go for nothing, rather than making
    you pay for it. A low-momentum project isn't worth holding onto; one with real heat, they don't
    just hand over."""
    return clamp(SELF_FINANCE_FREE_RELEASE_BASE - SELF_FINANCE_FREE_RELEASE_MOMENTUM_COEF * momentum, 0.05, 0.9)


def self_finance_buyout_cost(budget_ask: float) -> float:
    return budget_ask * SELF_FINANCE_BUYOUT_FRACTION


@dataclass(frozen=True)
class SelfFinanceOutcome:
    project: DevProject
    acquired: bool  # True if the project is self_financed after this call — already was, or just became
    just_acquired: bool  # True only if it became True this call
    cost_paid: float = 0.0
    released_free: bool = False
    could_not_afford: bool = False


def attempt_self_finance(project: DevProject, rng: random.Random, available_money: float) -> SelfFinanceOutcome:
    """The acquisition step: does the financing studio let this project go? A project already
    self-financed is a no-op here (already yours). Otherwise, roll studio_release_probability() —
    on a miss, the studio wants paid for it (self_finance_buyout_cost()), and the acquisition only
    goes through if available_money actually covers that. Doesn't touch momentum either way — this
    is a negotiation, not a development beat; the project's own progress is untouched by it."""
    if project.self_financed:
        return SelfFinanceOutcome(project, acquired=True, just_acquired=False)
    if rng.random() < studio_release_probability(project.momentum):
        return SelfFinanceOutcome(replace(project, self_financed=True), acquired=True, just_acquired=True, released_free=True)
    cost = self_finance_buyout_cost(project.budget_ask)
    if cost <= available_money:
        return SelfFinanceOutcome(replace(project, self_financed=True), acquired=True, just_acquired=True, cost_paid=cost)
    return SelfFinanceOutcome(project, acquired=False, just_acquired=False, could_not_afford=True)


def advance_quarter(project: DevProject, pkg_strength: float, rng: random.Random) -> tuple[DevProject, bool]:
    """Returns (new_project, greenlit)."""
    if project.frozen or project.dead:
        return project, False

    diff = difficulty(project.budget_ask)
    p = greenlight_probability(pkg_strength, diff, project.momentum)
    if rng.random() < p:
        return replace(project, momentum=1.0), True

    new_momentum = project.momentum * MOMENTUM_DECAY
    dead = new_momentum < MOMENTUM_DEATH_FLOOR
    return replace(project, momentum=new_momentum, quarters_in_dev=project.quarters_in_dev + 1, dead=dead), False
