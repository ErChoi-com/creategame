"""design/part-04-the-actor.md §4.2 — the Persona (the typecasting engine).

Two affinity vectors plus a scalar. GenreAffinity/ArchetypeAffinity track what the industry thinks
you're for; Legibility measures how sharply concentrated that picture is.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace

from callback.engine.core.util import clamp

GENRES = (
    "drama", "comedy", "action", "horror", "thriller",
    "romance", "scifi", "period", "musical", "family",
)
ARCHETYPES = (
    "leading_hero", "romantic_lead", "villain", "everyman", "character_actor",
    "ingenue", "authority", "comic_relief", "wildcard",
)

# §4.2 update rule constants.
AFFINITY_GAIN = 6.0
AFFINITY_BLEED = 0.8
BILLING_WEIGHT = {"lead": 1.0, "supporting": 0.55, "bit": 0.2, "extra": 0.0}

# §4.2 Legibility bands.
LEGIBILITY_LOW_MAX = 35
LEGIBILITY_MID_MAX = 70

# §4.2 staleness penalty (applied to FilmCriticScore in reception.py, tracked here since
# consecutive-same-lane is Persona state). Returned as a non-negative magnitude — "critic score
# penalty of -2 x (consecutiveSameLane - 2), floored at -12" describes the score *effect*
# (subtract up to 12 points), not a pre-negated value to add back in.
STALENESS_COEF = 2.0
STALENESS_CAP = 12.0


def reception_factor(audience_score: float) -> float:
    """clamp(0.4 + AudienceScore/100, 0.4, 1.6) — how much a project's audience reception
    amplifies or dampens the Persona update below."""
    return clamp(0.4 + audience_score / 100.0, 0.4, 1.6)


@dataclass(frozen=True)
class Persona:
    genre_affinity: dict[str, float] = field(default_factory=lambda: {g: 20.0 for g in GENRES})
    archetype_affinity: dict[str, float] = field(default_factory=lambda: {a: 20.0 for a in ARCHETYPES})
    consecutive_same_lane: int = 0

    def legibility(self) -> float:
        """100 × (max(v) − mean(v)) / max(v), averaged across both vectors."""
        def concentration(v: dict[str, float]) -> float:
            values = list(v.values())
            peak = max(values)
            if peak <= 0:
                return 0.0
            return 100.0 * (peak - (sum(values) / len(values))) / peak

        return (concentration(self.genre_affinity) + concentration(self.archetype_affinity)) / 2.0

    def legibility_band(self) -> str:
        leg = self.legibility()
        if leg <= LEGIBILITY_LOW_MAX:
            return "low"
        if leg <= LEGIBILITY_MID_MAX:
            return "mid"
        return "high"

    def staleness_penalty(self) -> float:
        """Non-negative magnitude to subtract from FilmCriticScore (0 while consecutive_same_lane
        <= 2, growing by 2/credit thereafter, capped at 12)."""
        return clamp(STALENESS_COEF * (self.consecutive_same_lane - 2), 0.0, STALENESS_CAP)

    def update(self, genre: str, archetype: str, billing: str, audience_score: float) -> "Persona":
        """Apply §4.2's post-project update rule for a completed project."""
        bw = BILLING_WEIGHT[billing]
        rf = reception_factor(audience_score)
        gain = AFFINITY_GAIN * bw * rf
        bleed = AFFINITY_BLEED * bw

        new_genre = {
            g: clamp(v + gain if g == genre else v - bleed, 0.0, 100.0)
            for g, v in self.genre_affinity.items()
        }
        new_archetype = {
            a: clamp(v + gain if a == archetype else v - bleed, 0.0, 100.0)
            for a, v in self.archetype_affinity.items()
        }
        same_lane = self.consecutive_same_lane + 1 if bw >= 0.55 else 0
        return replace(
            self,
            genre_affinity=new_genre,
            archetype_affinity=new_archetype,
            consecutive_same_lane=same_lane,
        )
