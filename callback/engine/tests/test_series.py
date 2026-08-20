"""actor/series.py — §5.18's season aggregation math, tested in isolation from Session."""
from __future__ import annotations

import unittest

from callback.engine.actor.series import (
    MAX_EPISODES,
    MIN_EPISODES,
    aggregate_season,
    license_value_multiplier,
    renewal_probability,
    retention_curve,
)


class TestRetentionCurve(unittest.TestCase):
    def test_starts_at_full_retention(self):
        curve = retention_curve(season_critic=60.0, n_episodes=8)
        self.assertAlmostEqual(curve[0], 1.0)

    def test_a_good_show_holds_its_audience_better_than_a_bad_one(self):
        good = retention_curve(season_critic=90.0, n_episodes=8)
        bad = retention_curve(season_critic=10.0, n_episodes=8)
        self.assertGreater(good[-1], bad[-1])

    def test_retention_only_ever_falls_or_holds_never_rises(self):
        curve = retention_curve(season_critic=95.0, n_episodes=10)
        for earlier, later in zip(curve, curve[1:]):
            self.assertLessEqual(later, earlier)

    def test_length_matches_episode_count(self):
        curve = retention_curve(season_critic=50.0, n_episodes=6)
        self.assertEqual(len(curve), 6)

    def test_an_average_critic_score_still_produces_real_decay(self):
        # Regression: the original (RETENTION_BASE=0.90, uncentred +0.002/critic-point) formula
        # clamped the per-episode step to 1.0 for any critic score at or above 50 — since this
        # engine's own project_quality centres around 50-60, nearly every real season got zero
        # week-to-week bleed at all, dead on arrival for "a bad show bleeds its audience."
        curve = retention_curve(season_critic=55.0, n_episodes=8)
        self.assertLess(curve[-1], 0.9)
        self.assertGreater(curve[-1], 0.1)  # a real, felt decay — not a total collapse either

    def test_only_a_genuinely_excellent_show_holds_close_to_full_retention(self):
        curve = retention_curve(season_critic=90.0, n_episodes=8)
        self.assertGreater(curve[-1], 0.9)


class TestRenewalProbability(unittest.TestCase):
    def test_bounded_within_floor_and_ceiling(self):
        self.assertGreaterEqual(renewal_probability(0.0, 0.0), 0.05)
        self.assertLessEqual(renewal_probability(100.0, 1.0), 0.85)

    def test_a_strong_finale_retention_raises_odds_over_a_weak_one(self):
        self.assertGreater(renewal_probability(60.0, 0.9), renewal_probability(60.0, 0.3))

    def test_a_weak_finale_can_sink_a_season_with_a_fine_average(self):
        # The whole point of reading final_retention rather than an average: a season that opened
        # strong and bled out badly should read as a real cancellation risk.
        strong_open_weak_close = renewal_probability(season_audience=65.0, final_retention=0.15)
        self.assertLess(strong_open_weak_close, 0.5)


class TestLicenseValueMultiplier(unittest.TestCase):
    def test_average_audience_leaves_license_value_at_budget(self):
        self.assertAlmostEqual(license_value_multiplier(50.0), 1.0)

    def test_a_hit_earns_a_real_premium_over_budget(self):
        self.assertGreater(license_value_multiplier(90.0), 1.0)

    def test_a_flop_earns_less_than_budget_but_never_zero(self):
        mult = license_value_multiplier(0.0)
        self.assertLess(mult, 1.0)
        self.assertGreater(mult, 0.0)


class TestAggregateSeason(unittest.TestCase):
    def test_license_value_scales_with_budget_and_ratings_not_box_office(self):
        agg = aggregate_season(
            premiere_spotlight=60.0, finale_spotlight=65.0,
            premiere_craft=60.0, finale_craft=65.0,
            premiere_critic=60.0, finale_critic=65.0,
            premiere_audience=90.0, finale_audience=90.0,
            premiere_budget=5.0, finale_budget=5.0,
            premiere_marketing=2.0, finale_marketing=2.0,
            n_episodes=8,
        )
        # a real hit (audience 90) should earn a real premium over the season's own budget
        self.assertGreater(agg.license_value, agg.season_budget)
        self.assertEqual(agg.n_episodes, 8)

    def test_middle_episodes_are_a_flat_discount_of_the_premiere_not_a_fresh_roll(self):
        agg = aggregate_season(
            premiere_spotlight=70.0, finale_spotlight=40.0,
            premiere_craft=70.0, finale_craft=40.0,
            premiere_critic=70.0, finale_critic=40.0,
            premiere_audience=70.0, finale_audience=40.0,
            premiere_budget=5.0, finale_budget=5.0,
            premiere_marketing=2.0, finale_marketing=2.0,
            n_episodes=6,
        )
        # notices mean sits between premiere and finale, pulled toward the premiere since 4 of 6
        # episodes echo it — not equal to a plain average of the two endpoints.
        plain_average = (70.0 + 40.0) / 2.0
        self.assertGreater(agg.season_notices, plain_average)

    def test_a_two_episode_season_has_no_middle_to_echo(self):
        agg = aggregate_season(
            premiere_spotlight=50.0, finale_spotlight=60.0,
            premiere_craft=50.0, finale_craft=60.0,
            premiere_critic=50.0, finale_critic=60.0,
            premiere_audience=50.0, finale_audience=60.0,
            premiere_budget=2.0, finale_budget=2.0,
            premiere_marketing=1.0, finale_marketing=1.0,
            n_episodes=2,
        )
        self.assertAlmostEqual(agg.season_notices, 55.0)

    def test_default_episode_range_is_sane(self):
        self.assertLess(MIN_EPISODES, MAX_EPISODES)
        self.assertGreaterEqual(MIN_EPISODES, 1)


if __name__ == "__main__":
    unittest.main()
