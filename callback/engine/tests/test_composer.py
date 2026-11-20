"""director/composer.py — tested fully in isolation, the same way the module itself is
compartmentalized (no Role/Session imports, plain values in and out)."""
from __future__ import annotations

import random
import unittest

from callback.engine.director.composer import (
    COMPOSER_SCENES,
    NEEDLE_DROP_BUDGET_THRESHOLD_MILLIONS,
    SCORE_GENRES,
    Composer,
    composer_salary_millions,
    needle_drop_tokens,
    resolve_score_effect,
    style_fit,
)


class TestStyleFit(unittest.TestCase):
    def test_matching_style_is_a_fit(self):
        self.assertTrue(style_fit("country", "country"))

    def test_mismatched_style_is_not_a_fit(self):
        self.assertFalse(style_fit("country", "electronic"))


class TestResolveScoreEffect(unittest.TestCase):
    def test_fit_at_full_skill_gives_the_full_bonus(self):
        composer = Composer(scene="indie", style="pop", skill=100.0)
        aud, crit = resolve_score_effect(composer, "pop")
        self.assertAlmostEqual(aud, 2.0)
        self.assertAlmostEqual(crit, 2.5)

    def test_fit_scales_down_with_skill(self):
        skilled = resolve_score_effect(Composer(scene="indie", style="pop", skill=100.0), "pop")
        unskilled = resolve_score_effect(Composer(scene="indie", style="pop", skill=10.0), "pop")
        self.assertGreater(skilled[0], unskilled[0])
        self.assertGreater(skilled[1], unskilled[1])

    def test_mismatch_never_gets_the_audience_bonus(self):
        aud, _ = resolve_score_effect(Composer(scene="indie", style="pop", skill=100.0), "country")
        self.assertEqual(aud, 0.0)

    def test_a_skilled_mismatch_costs_less_than_an_unskilled_one(self):
        _, skilled_crit = resolve_score_effect(Composer(scene="indie", style="pop", skill=90.0), "country")
        _, unskilled_crit = resolve_score_effect(Composer(scene="indie", style="pop", skill=10.0), "country")
        self.assertGreater(skilled_crit, unskilled_crit)

    def test_scene_never_touches_the_creative_delta(self):
        """§13.1 — stature is informational next to Fit, not a fit input. An indie and a superstar
        with identical style/skill must resolve identically."""
        indie = resolve_score_effect(Composer(scene="indie", style="rock", skill=70.0), "rock")
        superstar = resolve_score_effect(Composer(scene="superstar", style="rock", skill=70.0), "rock")
        self.assertEqual(indie, superstar)


class TestComposerSalary(unittest.TestCase):
    def test_higher_scene_tier_costs_more_on_average(self):
        rng_a, rng_b = random.Random(1), random.Random(1)
        indie = sum(composer_salary_millions(Composer("indie", "pop", 50.0), rng_a) for _ in range(300)) / 300
        superstar = sum(composer_salary_millions(Composer("superstar", "pop", 50.0), rng_b) for _ in range(300)) / 300
        self.assertGreater(superstar, indie)

    def test_mismatched_style_costs_the_same_as_a_matched_one(self):
        """Salary has no relationship to Fit at all — a mismatched-style superstar still costs a
        superstar's fee."""
        rng_a, rng_b = random.Random(2), random.Random(2)
        matched = sum(composer_salary_millions(Composer("mainstream", "pop", 60.0), rng_a) for _ in range(300)) / 300
        mismatched = sum(composer_salary_millions(Composer("mainstream", "country", 60.0), rng_b) for _ in range(300)) / 300
        self.assertAlmostEqual(matched, mismatched, delta=matched * 0.15)

    def test_never_negative(self):
        rng = random.Random(3)
        for scene in COMPOSER_SCENES:
            for _ in range(50):
                self.assertGreaterEqual(composer_salary_millions(Composer(scene, "pop", 20.0), rng), 0.0)


class TestNeedleDropTokens(unittest.TestCase):
    def test_non_needle_drop_genres_get_zero(self):
        self.assertEqual(needle_drop_tokens("orchestral", 100.0), 0)
        self.assertEqual(needle_drop_tokens("electronic", 100.0), 0)

    def test_small_budget_gets_one_token(self):
        self.assertEqual(needle_drop_tokens("pop", NEEDLE_DROP_BUDGET_THRESHOLD_MILLIONS - 1.0), 1)

    def test_large_budget_gets_a_second_token(self):
        self.assertEqual(needle_drop_tokens("rock", NEEDLE_DROP_BUDGET_THRESHOLD_MILLIONS), 2)

    def test_every_score_genre_is_covered_by_exactly_one_branch(self):
        for genre in SCORE_GENRES:
            self.assertIn(needle_drop_tokens(genre, 1.0), (0, 1))
