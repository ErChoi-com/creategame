"""leverage/merchandising.py — tested fully in isolation, the same way the module itself is
compartmentalized (no Role/FranchiseEntry/Session imports, plain floats in and out)."""
from __future__ import annotations

import random
import unittest

from callback.engine.leverage.merchandising import (
    MERCH_SHARE_RANGE,
    MERCH_STANDING_THRESHOLD,
    annual_royalty_payout,
    can_negotiate_merchandising,
    negotiated_merch_share,
)


class TestCanNegotiateMerchandising(unittest.TestCase):
    def test_below_threshold_is_unavailable(self):
        self.assertFalse(can_negotiate_merchandising(MERCH_STANDING_THRESHOLD - 1.0))

    def test_at_or_above_threshold_is_available(self):
        self.assertTrue(can_negotiate_merchandising(MERCH_STANDING_THRESHOLD))


class TestNegotiatedMerchShare(unittest.TestCase):
    def test_stays_within_the_real_range(self):
        rng = random.Random(1)
        for _ in range(200):
            share = negotiated_merch_share(actor_leverage=rng.random(), studio_protectiveness=rng.uniform(0, 100), rng=rng)
            self.assertGreaterEqual(share, MERCH_SHARE_RANGE[0])
            self.assertLessEqual(share, MERCH_SHARE_RANGE[1])

    def test_higher_leverage_pulls_the_share_up_on_average(self):
        rng_a, rng_b = random.Random(2), random.Random(2)
        low = sum(negotiated_merch_share(0.1, 0.0, rng_a) for _ in range(300)) / 300
        high = sum(negotiated_merch_share(0.9, 0.0, rng_b) for _ in range(300)) / 300
        self.assertGreater(high, low)

    def test_a_protective_studio_pulls_the_share_down_on_average(self):
        rng_a, rng_b = random.Random(3), random.Random(3)
        unprotected = sum(negotiated_merch_share(0.5, 0.0, rng_a) for _ in range(300)) / 300
        protected = sum(negotiated_merch_share(0.5, 100.0, rng_b) for _ in range(300)) / 300
        self.assertGreater(unprotected, protected)


class TestAnnualRoyaltyPayout(unittest.TestCase):
    def test_zero_indispensability_pays_nothing(self):
        self.assertEqual(annual_royalty_payout(royalty_share=0.05, character_indispensability=0.0), 0.0)

    def test_a_higher_share_pays_more_at_the_same_indispensability(self):
        low = annual_royalty_payout(royalty_share=0.01, character_indispensability=50.0)
        high = annual_royalty_payout(royalty_share=0.06, character_indispensability=50.0)
        self.assertGreater(high, low)

    def test_a_fresher_character_pays_more_than_a_faded_one_at_the_same_share(self):
        # This is the whole mechanism a fading/reviving franchise relies on — no decay curve lives
        # in this module at all; the caller just reads a different indispensability each year.
        faded = annual_royalty_payout(royalty_share=0.04, character_indispensability=10.0)
        fresh = annual_royalty_payout(royalty_share=0.04, character_indispensability=90.0)
        self.assertGreater(fresh, faded)

    def test_never_negative(self):
        self.assertGreaterEqual(annual_royalty_payout(royalty_share=0.01, character_indispensability=0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
