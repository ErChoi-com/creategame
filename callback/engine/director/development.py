"""design/part-07-the-director.md §7.4 — development hell: PackageStrength, Difficulty, the
greenlight roll, momentum, and one development action per project per year.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, replace

from callback.engine.core.util import sigmoid

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
    return GREENLIGHT_BASE_PROBABILITY * sigmoid(GREENLIGHT_SLOPE * (pkg_strength - diff)) * momentum


@dataclass(frozen=True)
class DevProject:
    script_id: str
    momentum: float = 0.5
    budget_ask: float = 30.0
    attached_star_bankability: float = 0.0
    quarters_in_dev: int = 0
    frozen: bool = False
    dead: bool = False


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
        return replace(project, momentum=1.0)
    if action == "drawer":
        return replace(project, frozen=True)
    return project


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
