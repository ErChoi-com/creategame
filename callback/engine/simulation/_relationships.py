"""Studios and directors both remember how a project with you actually turned out. Profit and
loss builds or costs real trust — asymmetrically, the same loss-averse read every other
risk-facing formula in this engine already uses (a big loss costs more trust than an equivalent
win earns back) — and that trust then changes real numbers going forward: a studio that trusts
you casts you more easily next time, and a director you've made money with reads as sharper on
your next film together, stacking with (not replacing) simulation/_franchises.py's franchise-
specific continuity bonus for a *returning* director.

Kept as one shared module rather than two near-identical ones: a studio and a requested director
are the same relationship shape — an id, a project count, a running P&L, and a trust score that
moves off ROI — so one Relationship type and one update function serve both.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from callback.engine.core.util import clamp

TRUST_DEFAULT = 50.0
TRUST_GAIN_COEF = 6.0  # trust earned per point of ROI above 1.0
TRUST_LOSS_COEF = 14.0  # trust lost per point of ROI below 1.0 — losing their money costs more than making it
TRUST_MAX_DELTA = 18.0  # no single project swings trust further than this either way

# How much trust above/below the 50 baseline shifts the numbers that actually matter downstream.
STUDIO_TRUST_UTILITY_COEF = 0.12  # a studio's trust in you shifts how easily they cast you (offers.utility())
DIRECTOR_TRUST_SKILL_COEF = 0.10  # a director's trust in you shifts their own skill/command reading


@dataclass(frozen=True)
class Relationship:
    subject_id: str
    projects_together: int = 0
    net_profit_millions: float = 0.0
    trust: float = TRUST_DEFAULT


def _trust_delta(roi: float) -> float:
    surplus = roi - 1.0
    coef = TRUST_GAIN_COEF if surplus >= 0 else TRUST_LOSS_COEF
    return clamp(surplus * coef, -TRUST_MAX_DELTA, TRUST_MAX_DELTA)


def update_relationship(relations: dict, subject_id: str, budget_millions: float, roi: float, gross_millions: float) -> dict:
    prior = relations.get(subject_id) or Relationship(subject_id=subject_id)
    profit = gross_millions - budget_millions  # a plain P&L reading, not the studio's own rights-share cut
    trust = clamp(prior.trust + _trust_delta(roi), 0.0, 100.0)
    updated = replace(
        prior, projects_together=prior.projects_together + 1,
        net_profit_millions=prior.net_profit_millions + profit, trust=trust,
    )
    return {**relations, subject_id: updated}


def utility_bonus_from_trust(relations: dict, subject_id: str) -> float:
    rel = relations.get(subject_id)
    if rel is None:
        return 0.0
    return STUDIO_TRUST_UTILITY_COEF * (rel.trust - TRUST_DEFAULT)


def director_skill_bonus_from_trust(relations: dict, npc_id: str | None) -> float:
    if npc_id is None:
        return 0.0
    rel = relations.get(npc_id)
    if rel is None:
        return 0.0
    return DIRECTOR_TRUST_SKILL_COEF * (rel.trust - TRUST_DEFAULT)


def trust_band(trust: float) -> str:
    if trust >= 75.0:
        return "they trust you"
    if trust >= 55.0:
        return "good standing"
    if trust >= 45.0:
        return "neutral"
    if trust >= 25.0:
        return "wary of you"
    return "burned before, and they remember"
