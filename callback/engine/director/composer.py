"""design/part-09-genres-franchises-and-tie-ins.md's own creative-revamp-plan.md §13/§13.1 — the
score genre a film picks, and the composer hired to deliver it.

Deliberately compartmentalized the same way genre/hybrids.py and leverage/merchandising.py already
are: no Role/Session/FranchiseEntry imports, every function takes plain values. Three real inputs
on a composer — Skill, Background (a scene tier crossed with a style), and the salary it costs to
hire them — and nothing else. Style Fit is the only thing that touches the creative delta; scene
tier is informational next to Fit and does exactly one other thing, drive Salary. No second payoff
for hiring above your tier, on purpose — see §13.1's own note against double-counting the same
signal.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from callback.engine.core.util import clamp

# §13 — the film's own one-time, film-wide pick. Real, nameable genres instead of the abstract
# "orchestral_traditional"/"electronic_modern"/... descriptors an earlier draft used — see the
# design doc's own note on why that first list was ditched.
SCORE_GENRES = ("orchestral", "pop", "electronic", "country", "rock", "hip_hop")

# §13.1 — a composer's Background is a real combination, not a single tag off SCORE_GENRES: a
# scene/stature half crossed with a style half. "Indie Pop," "Superstar Country," "Legacy
# Orchestral" — 4 scenes x 6 styles = 24 distinct, nameable backgrounds from two small lists.
COMPOSER_SCENES = ("indie", "mainstream", "superstar", "legacy")

# Salary multiplier per scene tier — the composer's only other mechanical lever (§13.1). Roughly
# doubling per tier, the same shape a real gap between an indie composer and a superstar reads as.
COMPOSER_SCENE_SALARY_MULT = {"indie": 1.0, "mainstream": 2.2, "superstar": 5.0, "legacy": 4.0}

# A base fee, $M, at SCORE_SKILL_MIDPOINT skill and an "indie" scene tier — small next to a film's
# own production budget, on purpose (§13.1's "underlying, minor effect" principle applies to cost
# too, not just to the creative delta).
COMPOSER_BASE_FEE_MILLIONS = 0.15
SCORE_SKILL_MIDPOINT = 50.0
COMPOSER_SKILL_FEE_COEF = 0.55  # a max-skill composer costs roughly 1 + this much more than midpoint
FEE_NEGOTIATION_NOISE_SD = 0.15

# §13.1 — style Fit is the only creative-delta input. A matched style is a real, modest bonus; a
# mismatch is a real, modest penalty, both scaled by Skill (a skilled composer sells a mismatched
# style better than an unskilled one whiffs a matched one).
SCORE_FIT_AUDIENCE_DELTA = 2.0
SCORE_FIT_CRITIC_DELTA = 2.5
SCORE_MISMATCH_CRITIC_PENALTY = 1.5


@dataclass(frozen=True)
class Composer:
    scene: str  # one of COMPOSER_SCENES — informational next to Fit; drives salary only
    style: str  # one of SCORE_GENRES — the only input to Fit
    skill: float  # 0-100, same shape as DirectorAttributes.craft


def style_fit(composer_style: str, score_genre: str) -> bool:
    return composer_style == score_genre


def resolve_score_effect(composer: Composer, score_genre: str) -> tuple[float, float]:
    """Returns (audience_delta, critic_delta) — folds into the same palette_aud_effect/
    palette_crit_effect stack simulation.career.resolve_quality already builds up. Magnitudes stay
    modest by design: this is one input among many, never a min-maxing target on its own."""
    skill_factor = clamp(composer.skill, 0.0, 100.0) / 100.0
    if style_fit(composer.style, score_genre):
        return SCORE_FIT_AUDIENCE_DELTA * skill_factor, SCORE_FIT_CRITIC_DELTA * skill_factor
    # A mismatch still gets something out of raw skill, just never as much as a real fit would —
    # the same "unskilled inverts the bonus" shape director.shoot_style.MANY_TAKES already uses.
    return 0.0, SCORE_MISMATCH_CRITIC_PENALTY * (skill_factor - 0.5)


def composer_salary_millions(composer: Composer, rng: random.Random) -> float:
    """No relationship to Fit at all — a mismatched-style superstar still costs a superstar's fee.
    Skill and scene tier are independent multipliers on the same base fee."""
    scene_mult = COMPOSER_SCENE_SALARY_MULT[composer.scene]
    skill_mult = 1.0 + COMPOSER_SKILL_FEE_COEF * (clamp(composer.skill, 0.0, 100.0) - SCORE_SKILL_MIDPOINT) / SCORE_SKILL_MIDPOINT
    noise = 1.0 + rng.gauss(0.0, FEE_NEGOTIATION_NOISE_SD)
    return max(0.0, COMPOSER_BASE_FEE_MILLIONS * scene_mult * skill_mult * noise)


# §13 — needle drops. A scarce token, not a menu: 1-2 per film, spent on a scene, never a dropdown
# of song genres to optimize. Only plausible off a genre a real needle-drop moment comes from.
NEEDLE_DROP_GENRES = frozenset({"pop", "hip_hop", "rock", "country"})
NEEDLE_DROP_TOKENS_BASE = 1
NEEDLE_DROP_BUDGET_THRESHOLD_MILLIONS = 40.0  # a real marketing budget to clear for a second token


def needle_drop_tokens(score_genre: str, film_budget_millions: float) -> int:
    if score_genre not in NEEDLE_DROP_GENRES:
        return 0
    return NEEDLE_DROP_TOKENS_BASE + (1 if film_budget_millions >= NEEDLE_DROP_BUDGET_THRESHOLD_MILLIONS else 0)
