"""genre/ and studio/ behaviour: the sequel curve and slate tier economics."""
from __future__ import annotations

import random
import unittest

from callback.engine.genre.franchise import sequel_bonus
from callback.engine.studio.slate import marketing_spend, resolve_slate_film, simulate_slate


class TestFranchise(unittest.TestCase):
    def test_first_sequel_beats_later_ones(self):
        self.assertGreater(sequel_bonus(1, 65), sequel_bonus(4, 65))

    def test_bonus_scales_with_prior_reception(self):
        self.assertGreater(sequel_bonus(2, 90), sequel_bonus(2, 40))

    def test_far_installments_have_no_bonus(self):
        self.assertEqual(sequel_bonus(9, 65), 0.0)


class TestSlate(unittest.TestCase):
    def test_marketing_curve_is_tiered(self):
        self.assertAlmostEqual(marketing_spend(5), 0.35 * 5)
        self.assertAlmostEqual(marketing_spend(30), 0.48 * 30)
        self.assertAlmostEqual(marketing_spend(80), 0.55 * 80)
        self.assertAlmostEqual(marketing_spend(150), 0.80 * 150)

    def test_resolve_slate_film_returns_real_reception(self):
        result = resolve_slate_film("tentpole", "action", random.Random(1))
        self.assertTrue(0.0 <= result.film_critic_score <= 100.0)
        self.assertGreaterEqual(result.roi, 0.0)

    def test_simulate_slate_returns_one_result_per_film(self):
        results = simulate_slate(["micro", "mid", "tentpole"], ["drama", "action", "scifi"], random.Random(2))
        self.assertEqual(len(results), 3)


if __name__ == "__main__":
    unittest.main()
