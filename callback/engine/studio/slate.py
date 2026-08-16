"""design/part-08-the-studio.md §8.2 — the slate: tier economics and the Marketing(b) curve.
Box office itself reuses actor/reception.py's single canonical model (§8.2's own v9 note: this
section used to carry a second, diverging copy — one model now, this reads it) rather than a
second implementation.
"""
from __future__ import annotations

import random

from callback.engine.actor.reception import ReceptionResult, resolve_reception
from callback.engine.core.util import clamp

TIER_BUDGETS = {"micro": 4.0, "low": 12.0, "mid": 30.0, "upper": 60.0, "tentpole": 170.0}
TIER_MEDIAN_ROI = {"micro": 1.24, "low": 1.03, "mid": 0.99, "upper": 0.95, "tentpole": 0.95}


def marketing_spend(budget_millions: float) -> float:
    if budget_millions < 10:
        return 0.35 * budget_millions
    if budget_millions < 50:
        return 0.48 * budget_millions
    if budget_millions < 100:
        return 0.55 * budget_millions
    return 0.80 * budget_millions


def resolve_slate_film(tier: str, genre: str, rng: random.Random) -> ReceptionResult:
    budget = TIER_BUDGETS[tier]
    return resolve_reception(
        script_quality=clamp(rng.gauss(62.0 - 0.020 * budget, 14), 0, 100),  # §8.2 — bigger budgets, worse scripts
        director_skill=clamp(rng.gauss(58, 16), 5, 100),
        ensemble=clamp(rng.gauss(58, 16), 0, 100),
        genre=genre,
        role_budget_millions=budget,
        director_prestige=clamp(rng.gauss(50, 20), 0, 100),
        staleness_penalty=0.0,
        cast_star_power=clamp(rng.gauss(35 + 0.19 * budget, 16), 0, 100),  # §8.2 — budget buys star power
        genre_demand=clamp(rng.gauss(52 + 0.10 * budget, 13), 0, 100),
        rng=rng,
    )


def simulate_slate(tiers: list[str], genres: list[str], rng: random.Random) -> list[ReceptionResult]:
    return [resolve_slate_film(tier, genre, rng) for tier, genre in zip(tiers, genres)]
