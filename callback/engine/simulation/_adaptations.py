"""Session-level orchestration of genre/adaptation.py's built-in-audience curve — deciding
*whether* a freshly-sampled role turns out to be an adaptation needs an rng draw and a role to
mutate, which is simulation/'s job (same split as simulation/_franchises.py: the pure curve lives
in genre/, the "does this happen" call lives here).
"""
from __future__ import annotations

import random
from dataclasses import replace

from callback.engine.actor.offers import Role
from callback.engine.genre.adaptation import (
    ADAPTATION_CHANCE, SOURCE_MATERIAL_TYPES, SOURCE_POPULARITY_TIERS, SOURCE_POPULARITY_WEIGHTS,
)


def maybe_attach_adaptation(role: Role, rng: random.Random) -> Role:
    """Only original (non-franchise) roles roll for this — a franchise sequel's audience is
    already accounted for by genre/franchise.py's own sequel curve, and a role can't be both at
    once without double-counting the same "people already know this" bonus."""
    if role.franchise_id or role.source_material:
        return role
    if rng.random() < ADAPTATION_CHANCE:
        popularity = rng.choices(SOURCE_POPULARITY_TIERS, weights=SOURCE_POPULARITY_WEIGHTS)[0]
        return replace(role, source_material=rng.choice(SOURCE_MATERIAL_TYPES), source_material_popularity=popularity)
    return role
