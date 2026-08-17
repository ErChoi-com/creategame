"""leverage/ behaviour: indispensability decay-to-zero, the holdout, favours, approvals, catalogue."""
from __future__ import annotations

import random
import unittest

from callback.engine.leverage.approvals import (
    APPROVAL_STANDING_THRESHOLD,
    BOX_OFFICE_BONUS_STANDING_THRESHOLD,
    can_negotiate_box_office_bonus,
    fee_after_approvals,
)
from callback.engine.leverage.catalogue import (
    accumulate_scarcity,
    advance_agent_tier,
    can_advance_agent_tier,
    new_leverage_state,
    recommend,
)
from callback.engine.leverage.favours import FavourLedger
from callback.engine.leverage.indispensability import (
    decay_dormant,
    indispensability,
    recast_cost,
    resolve_holdout,
)


class TestIndispensability(unittest.TestCase):
    def test_dormant_property_decays_to_release(self):
        value = 90.0
        released = False
        for _ in range(60):  # enough years that a real franchise would end
            value, released = decay_dormant(value)
            if released:
                break
        self.assertTrue(released, "a dormant franchise must eventually release the actor (v9 fix)")
        self.assertLess(value, 10.0)

    def test_recast_cost_scales_with_indispensability(self):
        self.assertGreater(recast_cost(90), recast_cost(20))

    def test_high_indispensability_favors_holding_out(self):
        rng = random.Random(1)
        pays = sum(1 for _ in range(500) if resolve_holdout(90, prior_holdouts=0, rng=rng).they_paid)
        self.assertGreater(pays / 500, 0.7)

    def test_repeat_holdouts_get_harder(self):
        rng = random.Random(2)
        fresh = sum(1 for _ in range(500) if resolve_holdout(70, prior_holdouts=0, rng=rng).they_paid)
        rng = random.Random(2)
        repeated = sum(1 for _ in range(500) if resolve_holdout(70, prior_holdouts=3, rng=rng).they_paid)
        self.assertGreater(fresh, repeated)


class TestFavours(unittest.TestCase):
    def test_credit_and_spend(self):
        ledger = FavourLedger().credit("n1", 3)
        self.assertEqual(ledger.balance("n1"), 3)
        ledger = ledger.spend("n1", 2)
        self.assertEqual(ledger.balance("n1"), 1)

    def test_overspend_raises(self):
        ledger = FavourLedger().credit("n1", 1)
        with self.assertRaises(ValueError):
            ledger.spend("n1", 5)

    def test_clear_removes_debt(self):
        ledger = FavourLedger().credit("n1", 3).clear("n1")
        self.assertEqual(ledger.balance("n1"), 0)


class TestApprovals(unittest.TestCase):
    def test_more_approvals_cost_more_fee(self):
        one = fee_after_approvals(100, frozenset({"script"}))
        two = fee_after_approvals(100, frozenset({"script", "costar"}))
        self.assertLess(two, one)

    def test_box_office_bonus_bar_is_still_above_approvals_but_reachable(self):
        # A real, sustained "a star"-tier career should be able to hold this line, not just brush
        # past it once in a lucky year — the old 80.0 threshold turned out to be barely reachable
        # even at the top of the game (see leverage/approvals.py's own note on the trial that
        # found this). Still meaningfully harder than approvals' 65, just not a single-year fluke.
        self.assertGreater(BOX_OFFICE_BONUS_STANDING_THRESHOLD, APPROVAL_STANDING_THRESHOLD)
        self.assertLess(BOX_OFFICE_BONUS_STANDING_THRESHOLD, 80.0)
        self.assertFalse(can_negotiate_box_office_bonus(70.0))
        self.assertTrue(can_negotiate_box_office_bonus(76.0))


class TestCatalogue(unittest.TestCase):
    def test_scarcity_caps(self):
        s = 0.0
        for _ in range(20):
            s = accumulate_scarcity(s)
        self.assertEqual(s, 40.0)

    def test_agent_tier_progression(self):
        self.assertFalse(can_advance_agent_tier("unrepresented", standing_score=5))
        self.assertTrue(can_advance_agent_tier("unrepresented", standing_score=20))
        self.assertEqual(advance_agent_tier("unrepresented", standing_score=20), "regional")

    def test_recommend_stores_boost(self):
        state = recommend(new_leverage_state(), "n1", boost=0.5)
        self.assertEqual(state.recommended["n1"], 0.5)


if __name__ == "__main__":
    unittest.main()
