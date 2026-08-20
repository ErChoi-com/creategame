"""design/part-05-the-work.md §5.18 — a season isn't a film with a different budget line, it's
several episodes' worth of reception compressed into one commitment. The premiere and finale are
played in full (three scenes each, §5.6, against that episode's own script); everything between
resolves at a flat, discounted echo of the premiere — the studio isn't reshooting your best work
for episode six, but it isn't letting a mid-season episode surprise you upward either.

Pure aggregation math only — this module never touches ActorState or FullState. The caller
(simulation/full_career.py's accept_and_play_season) is responsible for actually resolving the
premiere and finale each through the existing career.simulate_project pipeline and handing the two
real ProjectResults here.
"""
from __future__ import annotations

from dataclasses import dataclass

from callback.engine.core.util import clamp

MIN_EPISODES = 4
MAX_EPISODES = 13  # one range regardless of renewable — see the module-level note in offers.py on
# why episode count and renewability are independent settings, not two separate tiers.

# §5.18's own flat echo discount — a middle episode reads as a real, slightly-lesser version of the
# premiere, not a fresh roll and not a cliff.
ECHO_DISCOUNT = 0.94

# v2 fix — RETENTION_BASE=0.90 with a +0.002/point critic coefficient meant every critic score at
# or above the 50-centred neutral clamped the per-episode step to 1.0 (zero decay): since resolve_
# reception's own project_quality centres around 50-60, nearly every real season in practice got
# literally no week-to-week bleed at all, dead on arrival for "a bad show bleeds its audience."
# Recentred around RETENTION_CRITIC_CENTRE (roughly this engine's own real critic-score population
# median) with RETENTION_BASE itself already below 1.0 — an exactly-average show has real, felt
# decay; only a genuinely good one earns close to full retention, and even a great one keeps some
# natural churn rather than clamping to a hard ceiling.
RETENTION_BASE = 0.91
RETENTION_CRITIC_CENTRE = 55.0
RETENTION_CRITIC_COEF = 0.0025  # a good show holds its audience week to week; a bad one bleeds it

RENEWAL_BASE = 0.20
RENEWAL_AUDIENCE_COEF = 0.01
RENEWAL_RETENTION_COEF = 0.15
RENEWAL_FLOOR = 0.05
RENEWAL_CEILING = 0.85

# A season isn't sold to theaters or streamed for a one-time buyout the way a film is — the studio/
# network already committed to a distribution model the moment it financed the show (role.studio
# already tells you whether that's a streamer or a network deal; there's no separate release-
# strategy choice layered on top the way a film has). What the studio actually pays is a license
# fee off the season's own budget, adjusted for how the show actually performed with audiences —
# a hit season earns a real renewal-and-syndication premium; a weak one doesn't recoup the license
# the studio committed to. This replaces box-office gross/opening/legs entirely for a season —
# reusing that machinery would have been borrowing theatrical distribution economics for something
# that was never distributed that way.
LICENSE_VALUE_BASE = 1.0  # at exactly-average SeasonAudience (50), license value matches budget
LICENSE_VALUE_AUDIENCE_COEF = 0.02
LICENSE_VALUE_FLOOR_MULT = 0.5
LICENSE_VALUE_CEILING_MULT = 2.5


def license_value_multiplier(season_audience: float) -> float:
    return clamp(
        LICENSE_VALUE_BASE + LICENSE_VALUE_AUDIENCE_COEF * (season_audience - 50.0),
        LICENSE_VALUE_FLOOR_MULT, LICENSE_VALUE_CEILING_MULT,
    )


def sample_episode_count(rng) -> int:
    return rng.randint(MIN_EPISODES, MAX_EPISODES)


def _echoed_series(premiere_value: float, finale_value: float, n_episodes: int) -> list[float]:
    """episode[0] and episode[N-1] are the two real, played values; everything between is the
    premiere's own value discounted flat, never re-rolled and never compounding further."""
    if n_episodes <= 1:
        return [premiere_value]
    if n_episodes == 2:
        return [premiere_value, finale_value]
    middle = [premiere_value * ECHO_DISCOUNT] * (n_episodes - 2)
    return [premiere_value, *middle, finale_value]


def retention_curve(season_critic: float, n_episodes: int) -> list[float]:
    """Retention[0] = 1.0 (everyone who watched the premiere); each subsequent episode holds a
    real, critic-quality-dependent share of the episode before it. Expressed 0-1 (a fraction of
    the premiere's own audience), not §5.18's own 0-100 reading — renewal_probability's own
    RENEWAL_RETENTION_COEF is calibrated to this scale."""
    step = clamp(RETENTION_BASE + RETENTION_CRITIC_COEF * (season_critic - RETENTION_CRITIC_CENTRE), 0.0, 1.0)  # never grows the
    # audience past the premiere's own — a step >= 1.0 at very high SeasonCritic would mean "gains
    # viewers episode over episode," which retention isn't modeling
    retention = [1.0]
    for _ in range(1, n_episodes):
        retention.append(retention[-1] * step)
    return retention


def renewal_probability(season_audience: float, final_retention: float) -> float:
    """§5.18's own formula: a season that opens strong and bleeds retention through a sagging
    middle can still get cancelled on a weak finale even with a fine average across the whole run
    — final_retention (the LAST episode's own held share, not an average) is deliberately the
    number this reads, the same real-world shape where the finale is what a network's renewal
    meeting is actually looking at."""
    return clamp(
        RENEWAL_BASE + RENEWAL_AUDIENCE_COEF * (season_audience - 50.0) + RENEWAL_RETENTION_COEF * final_retention,
        RENEWAL_FLOOR, RENEWAL_CEILING,
    )


@dataclass(frozen=True)
class SeasonAggregate:
    n_episodes: int
    season_notices: float  # mean Spotlight across the season
    season_ensemble: float  # mean CraftContribution across the season
    season_critic: float
    season_audience: float
    season_budget: float
    season_marketing: float
    license_value: float  # the real money figure — a ratings-adjusted license fee, not box office
    retention: tuple[float, ...]
    renewal_chance: float


def aggregate_season(
    premiere_spotlight: float, finale_spotlight: float,
    premiere_craft: float, finale_craft: float,
    premiere_critic: float, finale_critic: float,
    premiere_audience: float, finale_audience: float,
    premiere_budget: float, finale_budget: float,
    premiere_marketing: float, finale_marketing: float,
    n_episodes: int,
) -> SeasonAggregate:
    """Every per-episode reading follows the same premiere/echo/finale shape (§5.18's own pattern,
    applied uniformly rather than re-deriving reception from raw inputs a second time) — critic and
    audience score included, since in this engine both are already real downstream reads of the
    same Ensemble/craft_contribution the premiere and finale each actually earned. No gross/opening/
    legs here at all — see license_value_multiplier's own module-level note on why box-office
    machinery doesn't fit a season."""
    notices = _echoed_series(premiere_spotlight, finale_spotlight, n_episodes)
    ensemble = _echoed_series(premiere_craft, finale_craft, n_episodes)
    critic = _echoed_series(premiere_critic, finale_critic, n_episodes)
    audience = _echoed_series(premiere_audience, finale_audience, n_episodes)
    budget = _echoed_series(premiere_budget, finale_budget, n_episodes)
    marketing = _echoed_series(premiere_marketing, finale_marketing, n_episodes)

    season_critic = sum(critic) / len(critic)
    season_audience = sum(audience) / len(audience)
    season_budget = sum(budget)
    retention = tuple(retention_curve(season_critic, n_episodes))

    return SeasonAggregate(
        n_episodes=n_episodes,
        season_notices=sum(notices) / len(notices),
        season_ensemble=sum(ensemble) / len(ensemble),
        season_critic=season_critic,
        season_audience=season_audience,
        season_budget=season_budget,
        season_marketing=sum(marketing),
        license_value=season_budget * license_value_multiplier(season_audience),
        retention=retention,
        renewal_chance=renewal_probability(season_audience, retention[-1]),
    )
