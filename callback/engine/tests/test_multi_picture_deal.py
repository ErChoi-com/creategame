"""leverage/multi_picture_deal.py — locking in guaranteed work and a fixed budget floor across
several future films with one studio, at a premium over the actor's quote right now.
"""
from __future__ import annotations

import unittest

from callback.engine.leverage.multi_picture_deal import (
    DEAL_LOCKED_QUOTE_PREMIUM,
    deal_terms,
    fulfill_one,
    sign_deal,
)


class TestDealTerms(unittest.TestCase):
    def test_guaranteed_budget_is_a_premium_over_quote(self):
        per_film, _ = deal_terms(quote_value=5.0, film_count=3)
        self.assertAlmostEqual(per_film, 5.0 * DEAL_LOCKED_QUOTE_PREMIUM)

    def test_total_value_scales_with_film_count(self):
        _, total_two = deal_terms(quote_value=5.0, film_count=2)
        _, total_four = deal_terms(quote_value=5.0, film_count=4)
        self.assertAlmostEqual(total_four, total_two * 2)


class TestSignAndFulfill(unittest.TestCase):
    def test_sign_deal_sets_films_remaining(self):
        deal = sign_deal("mid_major", quote_value=5.0, film_count=3, current_year=10)
        self.assertEqual(deal.films_remaining, 3)
        self.assertEqual(deal.studio_id, "mid_major")

    def test_fulfilling_decrements_films_remaining(self):
        deal = sign_deal("mid_major", quote_value=5.0, film_count=3, current_year=10)
        deal = fulfill_one(deal)
        self.assertEqual(deal.films_remaining, 2)

    def test_fulfilling_the_last_film_clears_the_deal(self):
        deal = sign_deal("mid_major", quote_value=5.0, film_count=1, current_year=10)
        self.assertIsNone(fulfill_one(deal))


if __name__ == "__main__":
    unittest.main()
