"""actor/studios.py — every studio actually spends different money on your film, and that money
(not just your release-strategy choice) shows up in Opening/ROI/streaming payouts.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.reception import BREAK_EVEN_MARKETING_SHARE, RIGHTS_SHARE, resolve_reception
from callback.engine.actor.release import STREAMING_BUYOUT_MULTIPLIER, STREAMING, apply_release_strategy
from callback.engine.actor.studios import (
    SELF_DISTRIBUTE_MULTIPLIER,
    STUDIOS,
    actor_influence_on_release,
    decide_release_strategy,
    marketing_share_for,
    pick_studio,
    quality_adjusted_bids,
    streaming_bidders,
)


class TestStudioProfiles(unittest.TestCase):
    def test_every_studio_has_a_plausible_marketing_share(self):
        for studio in STUDIOS.values():
            for budget in (5.0, 30.0, 150.0):
                share = marketing_share_for(studio, budget)
                self.assertGreaterEqual(share, 0.0)
                self.assertLessEqual(share, 1.0)

    def test_blockbuster_uses_tiered_curve_not_flat_share(self):
        blockbuster = STUDIOS["blockbuster"]
        self.assertLess(marketing_share_for(blockbuster, 5.0), marketing_share_for(blockbuster, 150.0))

    def test_indie_spends_less_than_blockbuster_at_comparable_budget(self):
        indie, blockbuster = STUDIOS["indie"], STUDIOS["blockbuster"]
        self.assertLess(marketing_share_for(indie, 12.0), marketing_share_for(blockbuster, 12.0))


class TestPickStudio(unittest.TestCase):
    def test_tiny_budget_never_lands_at_the_blockbuster_machine(self):
        rng = random.Random(1)
        for _ in range(200):
            studio = pick_studio(3.0, rng)
            self.assertNotEqual(studio.id, "blockbuster")

    def test_huge_budget_never_lands_at_the_indie_house(self):
        rng = random.Random(2)
        for _ in range(200):
            studio = pick_studio(200.0, rng)
            self.assertNotEqual(studio.id, "indie")


class TestMarketingAffectsReception(unittest.TestCase):
    def _resolve(self, marketing_share, rng):
        return resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng,
            marketing_share=marketing_share, opening_marketing_coef=0.60,
        )

    def test_higher_marketing_share_buys_a_bigger_opening_at_same_budget(self):
        low = self._resolve(0.20, random.Random(10))
        high = self._resolve(0.80, random.Random(10))
        self.assertGreater(high.opening, low.opening)

    def test_marketing_is_a_separate_tracked_figure_not_folded_into_budget(self):
        low = self._resolve(0.20, random.Random(11))
        high = self._resolve(0.80, random.Random(11))
        self.assertEqual(low.budget, high.budget)  # production budget itself never moves
        self.assertLess(low.marketing, high.marketing)  # only the marketing figure does
        self.assertAlmostEqual(low.marketing, 0.20 * low.budget)
        self.assertAlmostEqual(high.marketing, 0.80 * high.budget)

    def test_default_marketing_share_matches_flat_baseline_behaviour(self):
        rng_a, rng_b = random.Random(5), random.Random(5)
        default_result = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng_a,
        )
        explicit_result = self._resolve(BREAK_EVEN_MARKETING_SHARE, rng_b)
        # opening_marketing_coef=0 by default, so an explicit baseline share matches the old flat path
        self.assertAlmostEqual(default_result.opening, resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=random.Random(5),
            marketing_share=BREAK_EVEN_MARKETING_SHARE, opening_marketing_coef=0.0,
        ).opening)


class TestStreamerBuyoutBonus(unittest.TestCase):
    def test_streamer_studio_bonus_multiplier_beats_flat_preset(self):
        rng = random.Random(3)
        reception = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng,
        )
        streamer = STUDIOS["streamer"]
        boosted = apply_release_strategy(
            reception, STREAMING, rng, streaming_multiplier=STREAMING_BUYOUT_MULTIPLIER + streamer.streaming_multiplier_delta,
        )
        flat = apply_release_strategy(reception, STREAMING, rng)
        self.assertGreater(boosted.gross, flat.gross)


class TestStreamingBidders(unittest.TestCase):
    def test_financing_studio_is_always_in_the_pool(self):
        bidders = streaming_bidders(30.0, "prestige")
        self.assertIn(STUDIOS["prestige"], bidders)

    def test_bigger_budgets_draw_more_bidders_than_a_tiny_indie_film(self):
        small = streaming_bidders(3.0, "indie")
        big = streaming_bidders(30.0, "mid_major")
        self.assertGreaterEqual(len(big), len(small))

    def test_bidders_are_deterministic_no_rng_needed(self):
        first = streaming_bidders(30.0, "mid_major")
        second = streaming_bidders(30.0, "mid_major")
        self.assertEqual([s.id for s in first], [s.id for s in second])

    def test_self_distribute_multiplier_is_break_even_only(self):
        # "for nothing" — you get exactly your budget back, no more, no less.
        self.assertEqual(SELF_DISTRIBUTE_MULTIPLIER, 1.0)


class TestQualityAdjustedBids(unittest.TestCase):
    def test_an_awful_film_draws_fewer_outside_bidders_than_a_great_one(self):
        awful_count = sum(
            len(quality_adjusted_bids(30.0, "mid_major", 10.0, 10.0, random.Random(i))) for i in range(50)
        )
        great_count = sum(
            len(quality_adjusted_bids(30.0, "mid_major", 90.0, 90.0, random.Random(i))) for i in range(50)
        )
        self.assertLess(awful_count, great_count)

    def test_an_awful_film_can_draw_zero_outside_bidders(self):
        # financing studio's own offer + self-distribute always remain — but nobody else bites.
        bids = quality_adjusted_bids(30.0, "mid_major", 2.0, 2.0, random.Random(7))
        non_financing = [b for b in bids if b.studio_id != "mid_major"]
        self.assertEqual(non_financing, [])

    def test_financing_studio_and_self_distribute_are_always_present_regardless_of_quality(self):
        bids = quality_adjusted_bids(30.0, "mid_major", 0.0, 0.0, random.Random(1))
        self.assertTrue(any(b.studio_id == "mid_major" and not b.self_distribute for b in bids))
        self.assertTrue(any(b.self_distribute for b in bids))

    def test_perception_varies_bidder_to_bidder_not_one_shared_number(self):
        bids = quality_adjusted_bids(30.0, "mid_major", 60.0, 60.0, random.Random(3))
        outside = [b for b in bids if b.studio_id != "mid_major" and not b.self_distribute]
        self.assertGreaterEqual(len(outside), 2)
        self.assertGreater(len({b.multiplier for b in outside}), 1)

    def test_a_great_film_earns_more_than_a_mediocre_one_from_the_same_bidder_pool(self):
        rng_a, rng_b = random.Random(9), random.Random(9)
        mediocre = quality_adjusted_bids(30.0, "mid_major", 50.0, 50.0, rng_a)
        great = quality_adjusted_bids(30.0, "mid_major", 95.0, 95.0, rng_b)
        self.assertGreater(max(b.payout_millions for b in great), max(b.payout_millions for b in mediocre))


class TestReleaseDecision(unittest.TestCase):
    def test_trusted_a_lister_has_far_more_influence_than_a_burned_nobody(self):
        low = actor_influence_on_release(trust=10.0, actor_importance=5.0)
        high = actor_influence_on_release(trust=90.0, actor_importance=95.0)
        self.assertLess(low, high)
        self.assertGreaterEqual(low, 0.0)
        self.assertLessEqual(high, 1.0)

    def test_studio_always_has_final_say_never_a_guarantee_either_way(self):
        self.assertLess(actor_influence_on_release(trust=100.0, actor_importance=100.0), 1.0)
        self.assertGreater(actor_influence_on_release(trust=0.0, actor_importance=0.0), 0.0)

    def test_low_influence_reliably_lands_on_the_studios_own_preference(self):
        studio = STUDIOS["mid_major"]  # preferred_release="wide"
        rng = random.Random(5)
        outcomes = [decide_release_strategy(studio, "streaming", 10.0, 5.0, rng) for _ in range(200)]
        self.assertGreater(outcomes.count(studio.preferred_release), outcomes.count("streaming"))

    def test_high_influence_reliably_honors_the_actors_request(self):
        studio = STUDIOS["mid_major"]
        rng = random.Random(6)
        outcomes = [decide_release_strategy(studio, "streaming", 95.0, 95.0, rng) for _ in range(200)]
        self.assertGreater(outcomes.count("streaming"), outcomes.count(studio.preferred_release))

    def test_a_real_a_lister_always_outweighs_a_real_nobody_no_matter_how_trust_swings(self):
        # the exact case that broke the old additive formula: a highly-trusted nobody used to be
        # able to out-influence a moderately-famous but less-trusted actor.
        worst_case_alister = actor_influence_on_release(trust=0.0, actor_importance=40.0)
        best_case_nobody = actor_influence_on_release(trust=100.0, actor_importance=0.0)
        self.assertGreater(worst_case_alister, best_case_nobody)

    def test_a_total_nobody_gets_no_lift_from_trust_at_all(self):
        # zero importance means zero leverage to modulate — trust can't invent fame that isn't there.
        self.assertAlmostEqual(
            actor_influence_on_release(trust=0.0, actor_importance=0.0),
            actor_influence_on_release(trust=100.0, actor_importance=0.0),
        )

    def test_influence_scales_steeply_not_linearly(self):
        # a convex curve: the jump from mid to high importance should dwarf the jump from low to mid.
        low_to_mid = actor_influence_on_release(50.0, 50.0) - actor_influence_on_release(50.0, 25.0)
        mid_to_high = actor_influence_on_release(50.0, 100.0) - actor_influence_on_release(50.0, 75.0)
        self.assertGreater(mid_to_high, low_to_mid)

    def test_merely_above_average_fame_still_gets_overruled_most_of_the_time(self):
        # "rising star" territory (importance 75) shouldn't be mistaken for real pull.
        self.assertLess(actor_influence_on_release(trust=50.0, actor_importance=75.0), 0.35)

    def test_real_command_requires_near_top_of_scale_fame(self):
        self.assertGreater(actor_influence_on_release(trust=50.0, actor_importance=97.0), 0.60)


if __name__ == "__main__":
    unittest.main()
