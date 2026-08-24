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
    "fantasy", "crime", "superhero", "war", "western",
)
ARCHETYPES = (
    # design/part-09-genres-franchises-and-tie-ins.md's own §14 (creative-revamp-plan.md v4) —
    # redone critically from the original nine. `character_actor` cut: not a story function a
    # role has, it's a reputation an actor earns over a career for range across many archetypes —
    # that now falls out of a low Legibility spread across the filmography instead of being a
    # static, un-earnable field. `wildcard` cut: an undefined grab-bag, replaced by a properly
    # defined `ensemble`. `mentor`/`narrator`/`ensemble` added as the only genuinely missing
    # functions (deuteragonist/henchman/tragic-figure/breakout/foil were all considered and
    # rejected as redundant with billing or the new role-depth axis — see the design doc).
    "leading_hero", "romantic_lead", "villain", "everyman",
    "ingenue", "authority", "comic_relief", "mentor", "narrator", "ensemble",
)

# design/part-09 §14.2 — a role's depth is independent of both archetype and billing: a supporting
# role can be a showcase, a lead can be underwritten. Ordered low to high on purpose (callers that
# want "at least rich" can index-compare instead of set-membership testing).
ROLE_DEPTHS = ("underwritten", "standard", "rich", "showcase")

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

# §4.2's own "breaking type" payoff — a successful type-break resets Legibility toward the middle,
# not all the way. 0.5 pulls each affinity value halfway to the vector's own mean: a real, felt
# loosening (the whole point of taking the gamble), but the years spent building a lane aren't
# erased in one film.
LEGIBILITY_RESET_PULL = 0.5


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

    def top_genre(self) -> str:
        return max(self.genre_affinity, key=self.genre_affinity.get)

    def top_archetype(self) -> str:
        return max(self.archetype_affinity, key=self.archetype_affinity.get)

    def reset_toward_middle(self, pull: float = LEGIBILITY_RESET_PULL) -> "Persona":
        """The breaking-type payoff — called on top of the normal update() for the same project,
        not instead of it: the role you just broke type with still registers its own real affinity
        gain first, and only then does the whole profile loosen around it."""
        def pulled(v: dict[str, float]) -> dict[str, float]:
            mean = sum(v.values()) / len(v)
            return {k: val + pull * (mean - val) for k, val in v.items()}

        return replace(self, genre_affinity=pulled(self.genre_affinity), archetype_affinity=pulled(self.archetype_affinity))

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
