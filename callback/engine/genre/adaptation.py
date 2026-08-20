"""A film adapted from an existing property (a novel, comic, true story, or video game) carries a
built-in audience the way a sequel does, without needing any installments of its own — people show
up already knowing the story. Kept as its own curve, separate from genre/franchise.py's sequel
bonus, because the source of the audience's familiarity is different: reputation you inherited
from the source material, not reputation you and this cast/crew built together across films.
"""
from __future__ import annotations

SOURCE_MATERIAL_TYPES = ("novel", "comic", "true_story", "video_game", "stage")

# The built-in-awareness bump — smaller than a fresh sequel's (people know the STORY, not this
# specific cast/crew's prior work), but real, and it doesn't decay across installments the way
# genre/franchise.py's SEQUEL_BASE_BONUS curve does.
ADAPTATION_AUDIENCE_BONUS = 10.0

# The "the book was better" risk — an adaptation draws fidelity scrutiny an original screenplay
# never has to answer for. Applied at a flat rate this pass; a per-adaptation fidelity dial (how
# closely the film actually follows its source) is a natural follow-up, not modeled here.
ADAPTATION_CRITIC_RISK = -5.0

# How often a freshly-sampled, non-franchise role turns out to be an adaptation of something.
ADAPTATION_CHANCE = 0.12

# §4.4 v17 — "adaptation" used to be binary: the same +10 audience bonus and -5 critic risk
# whether the source was an obscure short story or a genuine bestseller. Real popularity now
# scales both — a beloved property brings a much bigger built-in audience, but also a much bigger
# fidelity risk if the film doesn't deliver; an obscure one barely moves either.
SOURCE_POPULARITY_TIERS = ("obscure", "known", "beloved")
SOURCE_POPULARITY_WEIGHTS = (0.45, 0.40, 0.15)  # most adaptations are of something modest, not a phenomenon
SOURCE_POPULARITY_MULTIPLIER = {"obscure": 0.4, "known": 1.0, "beloved": 2.0}


def adaptation_audience_bonus(source_material: str | None, popularity: str | None = None) -> float:
    if not source_material:
        return 0.0
    return ADAPTATION_AUDIENCE_BONUS * SOURCE_POPULARITY_MULTIPLIER.get(popularity, 1.0)


def adaptation_critic_risk(source_material: str | None, popularity: str | None = None) -> float:
    if not source_material:
        return 0.0
    return ADAPTATION_CRITIC_RISK * SOURCE_POPULARITY_MULTIPLIER.get(popularity, 1.0)
