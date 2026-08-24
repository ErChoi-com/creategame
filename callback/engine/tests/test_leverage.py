"""leverage/ behaviour: indispensability decay-to-zero, the holdout, favours, approvals, catalogue."""
from __future__ import annotations

import random
import unittest

from callback.engine.leverage.approvals import (
    APPROVAL_STANDING_THRESHOLD,
    box_office_bonus_earned,
    BOX_OFFICE_BONUS_STANDING_THRESHOLD,
    can_negotiate_box_office_bonus,
    fee_after_approvals,
    FIRST_DOLLAR_GROSS_SHARE_RANGE,
    FIRST_DOLLAR_GROSS_STANDING_THRESHOLD,
    negotiated_bonus_share,
    NET_POINTS_SHARE_RANGE,
)
from callback.engine.leverage.catalogue import (
    accumulate_scarcity,
    advance_agent_tier,
    agent_application_boost,
    agent_fatigue_trend,
    application_fatigue_tax,
    can_advance_agent_tier,
    fatigue_band,
    FATIGUE_BAND_THRESHOLDS,
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

    def test_a_protective_studio_is_more_willing_to_let_a_star_go(self):
        # A strong franchise's studio doesn't need to keep paying up to keep any one person on it
        # — real, even at otherwise-high personal indispensability.
        rng = random.Random(3)
        unprotected = sum(
            1 for _ in range(500) if resolve_holdout(80, prior_holdouts=0, rng=rng, studio_protectiveness=0.0).they_paid
        )
        rng = random.Random(3)
        protected = sum(
            1 for _ in range(500) if resolve_holdout(80, prior_holdouts=0, rng=rng, studio_protectiveness=100.0).they_paid
        )
        self.assertGreater(unprotected, protected)

    def test_default_protectiveness_matches_the_original_unparameterized_behavior(self):
        rng_a, rng_b = random.Random(9), random.Random(9)
        self.assertEqual(
            resolve_holdout(65, prior_holdouts=1, rng=rng_a).they_paid,
            resolve_holdout(65, prior_holdouts=1, rng=rng_b, studio_protectiveness=0.0).they_paid,
        )


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

    def test_first_dollar_gross_needs_a_real_bar_above_net_points(self):
        # Access (can you get this deal shape at all) is one axis, gated by Standing.
        self.assertGreater(FIRST_DOLLAR_GROSS_STANDING_THRESHOLD, BOX_OFFICE_BONUS_STANDING_THRESHOLD)
        self.assertFalse(can_negotiate_box_office_bonus(80.0, "first_dollar_gross"))
        self.assertTrue(can_negotiate_box_office_bonus(90.0, "first_dollar_gross"))
        # net_points is unaffected by the new, rarer bar
        self.assertTrue(can_negotiate_box_office_bonus(76.0, "net_points"))

    def test_first_dollar_gross_offer_range_sits_below_net_points_range(self):
        # The second, independent axis: what percentage you land within the deal, once you've
        # cleared the (harder) access bar. Real studios offer a lower percentage range for
        # first-dollar gross specifically because they're paying out regardless of profit.
        self.assertLess(FIRST_DOLLAR_GROSS_SHARE_RANGE[1], NET_POINTS_SHARE_RANGE[1])
        self.assertLessEqual(FIRST_DOLLAR_GROSS_SHARE_RANGE[0], NET_POINTS_SHARE_RANGE[0])

    def test_negotiated_share_stays_within_its_own_range_and_scales_with_leverage(self):
        rng = random.Random(10)
        low_leverage = [negotiated_bonus_share("net_points", 0.0, rng) for _ in range(200)]
        high_leverage = [negotiated_bonus_share("net_points", 1.0, rng) for _ in range(200)]
        lo, hi = NET_POINTS_SHARE_RANGE
        for v in low_leverage + high_leverage:
            self.assertGreaterEqual(v, lo - 0.02)
            self.assertLessEqual(v, hi + 0.02)
        self.assertLess(sum(low_leverage) / len(low_leverage), sum(high_leverage) / len(high_leverage))

    def test_net_points_pay_nothing_below_break_even(self):
        self.assertEqual(box_office_bonus_earned(50.0, 80.0, 0.12, "net_points"), 0.0)

    def test_net_points_scale_with_real_profit_not_raw_gross(self):
        small_hit = box_office_bonus_earned(100.0, 90.0, 0.12, "net_points")  # $10M profit
        big_hit = box_office_bonus_earned(300.0, 90.0, 0.12, "net_points")  # $210M profit
        self.assertGreater(big_hit, small_hit)
        self.assertGreater(small_hit, 0.0)

    def test_first_dollar_gross_pays_even_on_a_film_that_never_broke_even(self):
        payout = box_office_bonus_earned(50.0, 200.0, 0.02, "first_dollar_gross")  # a real flop
        self.assertGreater(payout, 0.0)

    def test_first_dollar_gross_and_net_points_are_genuinely_different_shapes(self):
        # Same film, same numbers, same negotiated share — the two deal types should not converge
        # to the same payout: one reads raw gross, the other reads profit above break-even.
        gross, break_even, share = 120.0, 90.0, 0.10
        first_dollar = box_office_bonus_earned(gross, break_even, share, "first_dollar_gross")
        net = box_office_bonus_earned(gross, break_even, share, "net_points")
        self.assertNotAlmostEqual(first_dollar, net, delta=0.01)


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


class TestAgentApplicationBoost(unittest.TestCase):
    """leverage.catalogue's real, felt boost applied to every single application (not a rationed
    few) — sampled fresh from a range each time, never a flat number."""

    def test_unrepresented_has_nothing_to_draw_on(self):
        rng = random.Random(1)
        for _ in range(50):
            self.assertEqual(agent_application_boost("unrepresented", rng), 0.0)

    def test_higher_tiers_boost_more_on_average_and_never_the_same_number_twice(self):
        rng = random.Random(2)
        regional = [agent_application_boost("regional", rng) for _ in range(200)]
        powerhouse = [agent_application_boost("powerhouse", rng) for _ in range(200)]
        self.assertGreater(sum(powerhouse) / len(powerhouse), sum(regional) / len(regional))
        self.assertGreater(len(set(round(v, 4) for v in powerhouse)), 1)

    def test_unknown_tier_is_neutral_rather_than_crashing(self):
        self.assertEqual(agent_application_boost("nonexistent_tier", random.Random(3)), 0.0)


class TestAgentFatigue(unittest.TestCase):
    """The fatigue tax — a real, deterministically-climbing trend with an unrepresented actor's
    own applications this year, at a rate that depends entirely on who's making the calls."""

    def test_trend_climbs_with_applications(self):
        self.assertEqual(agent_fatigue_trend("unrepresented", 0), 0.0)
        self.assertGreater(agent_fatigue_trend("unrepresented", 10), agent_fatigue_trend("unrepresented", 1))

    def test_unrepresented_climbs_far_faster_than_powerhouse(self):
        apps = 10
        self.assertGreater(agent_fatigue_trend("unrepresented", apps), agent_fatigue_trend("powerhouse", apps))

    def test_tax_carries_real_noise_around_the_trend_but_never_goes_negative(self):
        rng = random.Random(4)
        values = [application_fatigue_tax("unrepresented", 5, rng) for _ in range(200)]
        self.assertGreater(len(set(round(v, 4) for v in values)), 1)
        self.assertTrue(all(v >= 0.0 for v in values))

    def test_fatigue_band_climbs_with_applications_and_resets_conceptually_at_zero(self):
        self.assertEqual(fatigue_band("unrepresented", 0), "fresh")
        early = fatigue_band("unrepresented", 1)
        late = fatigue_band("unrepresented", 20)
        bands_in_order = [label for _, label in FATIGUE_BAND_THRESHOLDS]
        self.assertLessEqual(bands_in_order.index(early), bands_in_order.index(late))

    def test_the_same_application_count_reads_differently_by_tier(self):
        # Real representation means the same volume just doesn't read as volume.
        self.assertNotEqual(fatigue_band("unrepresented", 50), fatigue_band("powerhouse", 50))


if __name__ == "__main__":
    unittest.main()
