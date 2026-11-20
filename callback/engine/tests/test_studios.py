"""actor/studios.py — every studio actually spends different money on your film, and that money
(not just your release-strategy choice) shows up in Opening/ROI/streaming payouts.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.reception import BREAK_EVEN_MARKETING_SHARE, RIGHTS_SHARE, resolve_reception
from callback.engine.actor.release import (
    FESTIVAL_ACQUISITION_BASE_MULTIPLIER,
    STREAMING_BUYOUT_MULTIPLIER,
    STREAMING,
    apply_release_strategy,
)
from callback.engine.actor.studios import (
    DIRECTOR_INFLUENCE_CEILING,
    DIRECTOR_INFLUENCE_FLOOR,
    MARKETING_SHARE_CEILING,
    MARKETING_SHARE_FLOOR,
    SELF_DISTRIBUTE_MULTIPLIER,
    STUDIO_INFLUENCE_CEILING,
    STUDIOS,
    actor_influence_on_release,
    decide_marketing_spend,
    decide_release_strategy,
    director_influence_on_studio_decision,
    festival_bidders,
    marketing_share_for,
    pick_studio,
    quality_adjusted_bids,
    quality_adjusted_festival_bids,
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


class TestAnimationOpeningMix(unittest.TestCase):
    def test_star_power_matters_less_for_an_animated_opening(self):
        rng_a, rng_b = random.Random(20), random.Random(20)
        low_star = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="family",
            role_budget_millions=40, director_prestige=50, staleness_penalty=0,
            cast_star_power=10, genre_demand=55, rng=rng_a, is_animation=True,
        )
        high_star = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="family",
            role_budget_millions=40, director_prestige=50, staleness_penalty=0,
            cast_star_power=90, genre_demand=55, rng=rng_b, is_animation=True,
        )
        animated_gap = high_star.opening - low_star.opening

        rng_c, rng_d = random.Random(20), random.Random(20)
        live_low = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="family",
            role_budget_millions=40, director_prestige=50, staleness_penalty=0,
            cast_star_power=10, genre_demand=55, rng=rng_c, is_animation=False,
        )
        live_high = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="family",
            role_budget_millions=40, director_prestige=50, staleness_penalty=0,
            cast_star_power=90, genre_demand=55, rng=rng_d, is_animation=False,
        )
        live_gap = live_high.opening - live_low.opening
        self.assertLess(animated_gap, live_gap)

    def test_default_is_animation_matches_prior_unparameterized_behavior(self):
        rng_a, rng_b = random.Random(21), random.Random(21)
        base = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng_a,
        )
        explicit = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng_b, is_animation=False,
        )
        self.assertAlmostEqual(base.opening, explicit.opening)


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

    def test_a_protected_franchise_draws_a_thinner_outside_pool_at_the_same_quality(self):
        unprotected_count = sum(
            len(quality_adjusted_bids(30.0, "mid_major", 60.0, 60.0, random.Random(i))) for i in range(50)
        )
        protected_count = sum(
            len(quality_adjusted_bids(30.0, "mid_major", 60.0, 60.0, random.Random(i), franchise_protectiveness=100.0))
            for i in range(50)
        )
        self.assertLess(protected_count, unprotected_count)

    def test_default_protectiveness_matches_the_original_unparameterized_behavior(self):
        rng_a, rng_b = random.Random(4), random.Random(4)
        base = quality_adjusted_bids(30.0, "mid_major", 55.0, 55.0, rng_a)
        explicit = quality_adjusted_bids(30.0, "mid_major", 55.0, 55.0, rng_b, franchise_protectiveness=0.0)
        self.assertEqual([b.studio_id for b in base], [b.studio_id for b in explicit])


class TestFestivalBidders(unittest.TestCase):
    def test_financing_studio_is_always_in_the_pool(self):
        bidders = festival_bidders(8.0, "prestige")
        self.assertIn(STUDIOS["prestige"], bidders)

    def test_none_financing_studio_id_is_tolerated_for_a_self_financed_project(self):
        bidders = festival_bidders(3.0, None)
        self.assertTrue(bidders)  # still a real outside pool, just no financing entry forced in

    def test_bidders_are_deterministic_no_rng_needed(self):
        first = festival_bidders(8.0, "indie")
        second = festival_bidders(8.0, "indie")
        self.assertEqual([s.id for s in first], [s.id for s in second])

    def test_blockbuster_machine_is_out_of_its_lane_on_a_tiny_festival_budget(self):
        bidders = festival_bidders(2.0, "indie")
        self.assertNotIn(STUDIOS["blockbuster"], bidders)


class TestQualityAdjustedFestivalBids(unittest.TestCase):
    def test_an_awful_film_draws_fewer_outside_bidders_than_a_great_one(self):
        awful_count = sum(
            len(quality_adjusted_festival_bids(8.0, "indie", 10.0, 10.0, random.Random(i))) for i in range(50)
        )
        great_count = sum(
            len(quality_adjusted_festival_bids(8.0, "indie", 90.0, 90.0, random.Random(i))) for i in range(50)
        )
        self.assertLess(awful_count, great_count)

    def test_an_awful_film_can_draw_zero_outside_bidders(self):
        # financing studio's own guaranteed offer remains — but nobody else bites.
        bids = quality_adjusted_festival_bids(8.0, "indie", 2.0, 2.0, random.Random(7))
        non_financing = [b for b in bids if b.studio_id != "indie"]
        self.assertEqual(non_financing, [])

    def test_financing_studio_offer_is_always_present_regardless_of_quality(self):
        bids = quality_adjusted_festival_bids(8.0, "indie", 0.0, 0.0, random.Random(1))
        self.assertTrue(any(b.studio_id == "indie" for b in bids))

    def test_none_financing_studio_id_omits_the_financing_side_offer(self):
        # A genuinely independent, never-studio-attached self-financed project — no financing
        # identity to draw a guaranteed offer from, only outside bids.
        bids = quality_adjusted_festival_bids(8.0, None, 90.0, 90.0, random.Random(1))
        self.assertTrue(all(not b.self_release for b in bids))

    def test_a_great_film_earns_more_than_a_mediocre_one_from_the_same_bidder_pool(self):
        rng_a, rng_b = random.Random(9), random.Random(9)
        mediocre = quality_adjusted_festival_bids(8.0, "indie", 50.0, 50.0, rng_a)
        great = quality_adjusted_festival_bids(8.0, "indie", 95.0, 95.0, rng_b)
        self.assertGreater(max(b.payout_millions for b in great), max(b.payout_millions for b in mediocre))

    def test_no_bid_here_is_ever_flagged_self_release(self):
        # release.py's own festival_sale_resolver adds the self_release option separately, using
        # the real reception numbers this module never sees.
        bids = quality_adjusted_festival_bids(8.0, "indie", 80.0, 80.0, random.Random(2))
        self.assertTrue(all(not b.self_release for b in bids))

    def test_festival_acquisition_multiplier_is_below_the_streaming_buyout_floor(self):
        # a theatrical acquisition guarantee is a smaller commitment than a streamer's full-budget-
        # plus-margin buyout — selling at a festival should be a real, not strictly dominant, choice.
        self.assertLess(FESTIVAL_ACQUISITION_BASE_MULTIPLIER, STREAMING_BUYOUT_MULTIPLIER)


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


class TestMarketingDecision(unittest.TestCase):
    def test_not_a_function_of_film_quality_at_all(self):
        # decide_marketing_spend takes no quality argument whatsoever — this test exists to lock
        # in the design intent: nobody, including the studio, gets to peek at the real score.
        import inspect
        params = inspect.signature(decide_marketing_spend).parameters
        self.assertNotIn("quality", params)
        self.assertNotIn("film_critic_score", params)
        self.assertNotIn("audience_score", params)

    def test_higher_trust_pushes_spend_up_on_average(self):
        studio = STUDIOS["mid_major"]
        low = [decide_marketing_spend(studio, 30.0, 5.0, 50.0, 50.0, False, False, random.Random(i)).marketing_share for i in range(300)]
        high = [decide_marketing_spend(studio, 30.0, 95.0, 50.0, 50.0, False, False, random.Random(i)).marketing_share for i in range(300)]
        self.assertGreater(sum(high) / len(high), sum(low) / len(low))

    def test_higher_star_power_pushes_spend_up_on_average(self):
        studio = STUDIOS["mid_major"]
        low = [decide_marketing_spend(studio, 30.0, 50.0, 5.0, 50.0, False, False, random.Random(i)).marketing_share for i in range(300)]
        high = [decide_marketing_spend(studio, 30.0, 50.0, 95.0, 50.0, False, False, random.Random(i)).marketing_share for i in range(300)]
        self.assertGreater(sum(high) / len(high), sum(low) / len(low))

    def test_hotter_genre_demand_pushes_spend_up_on_average(self):
        studio = STUDIOS["mid_major"]
        cold = [decide_marketing_spend(studio, 30.0, 50.0, 50.0, 5.0, False, False, random.Random(i)).marketing_share for i in range(300)]
        hot = [decide_marketing_spend(studio, 30.0, 50.0, 50.0, 95.0, False, False, random.Random(i)).marketing_share for i in range(300)]
        self.assertGreater(sum(hot) / len(hot), sum(cold) / len(cold))

    def test_franchise_or_adaptation_gets_a_real_efficiency_discount_on_average(self):
        studio = STUDIOS["mid_major"]
        original = [decide_marketing_spend(studio, 30.0, 50.0, 50.0, 50.0, False, False, random.Random(i)).marketing_share for i in range(400)]
        franchise = [decide_marketing_spend(studio, 30.0, 50.0, 50.0, 50.0, True, False, random.Random(i)).marketing_share for i in range(400)]
        self.assertLess(sum(franchise) / len(franchise), sum(original) / len(original))

    def test_a_nobodys_push_is_rarely_honored_a_top_stars_usually_is(self):
        studio = STUDIOS["mid_major"]
        nobody_honors = sum(
            decide_marketing_spend(studio, 30.0, 50.0, 5.0, 50.0, False, True, random.Random(i)).push_honored
            for i in range(300)
        )
        alister_honors = sum(
            decide_marketing_spend(studio, 30.0, 50.0, 97.0, 50.0, False, True, random.Random(i)).push_honored
            for i in range(300)
        )
        self.assertLess(nobody_honors, 40)
        self.assertGreater(alister_honors, 200)

    def test_no_push_requested_means_never_honored(self):
        studio = STUDIOS["mid_major"]
        for i in range(50):
            decision = decide_marketing_spend(studio, 30.0, 50.0, 95.0, 50.0, False, False, random.Random(i))
            self.assertFalse(decision.push_requested)
            self.assertFalse(decision.push_honored)

    def test_identical_inputs_can_still_produce_meaningfully_different_spend(self):
        # the headline point: nobody can reliably predict the outcome, even holding every known
        # signal fixed — real, substantial noise dominates the decision.
        studio = STUDIOS["mid_major"]
        shares = [
            decide_marketing_spend(studio, 30.0, 50.0, 50.0, 50.0, False, False, random.Random(i)).marketing_share
            for i in range(500)
        ]
        self.assertGreater(max(shares) - min(shares), 0.4)

    def test_share_always_stays_within_the_sane_floor_and_ceiling(self):
        studio = STUDIOS["blockbuster"]
        for i in range(500):
            decision = decide_marketing_spend(studio, 250.0, 0.0, 0.0, 0.0, True, False, random.Random(i))
            self.assertGreaterEqual(decision.marketing_share, MARKETING_SHARE_FLOOR)
            self.assertLessEqual(decision.marketing_share, MARKETING_SHARE_CEILING)


class TestDirectorInfluenceCurve(unittest.TestCase):
    def test_higher_floor_than_the_actor_curve(self):
        self.assertGreater(
            director_influence_on_studio_decision(trust=50.0, director_importance=0.0),
            actor_influence_on_release(50.0, 0.0),
        )
        self.assertGreaterEqual(director_influence_on_studio_decision(0.0, 0.0), DIRECTOR_INFLUENCE_FLOOR)

    def test_scales_faster_through_the_middle_than_the_actor_curve(self):
        director_mid = director_influence_on_studio_decision(trust=50.0, director_importance=50.0)
        actor_mid = actor_influence_on_release(trust=50.0, actor_importance=50.0)
        self.assertGreater(director_mid, actor_mid)

    def test_never_exceeds_the_same_ceiling_the_actor_curve_has(self):
        self.assertEqual(DIRECTOR_INFLUENCE_CEILING, STUDIO_INFLUENCE_CEILING)
        director_top = director_influence_on_studio_decision(trust=100.0, director_importance=100.0)
        self.assertLessEqual(director_top, STUDIO_INFLUENCE_CEILING)

    def test_decide_release_strategy_accepts_the_director_influence_curve(self):
        studio = STUDIOS["mid_major"]  # preferred_release="wide"
        rng = random.Random(7)
        outcomes = [
            decide_release_strategy(studio, "streaming", 50.0, 90.0, rng, influence_fn=director_influence_on_studio_decision)
            for _ in range(200)
        ]
        self.assertGreater(outcomes.count("streaming"), 0)

    def test_decide_marketing_spend_accepts_the_director_influence_curve(self):
        studio = STUDIOS["mid_major"]
        rng = random.Random(8)
        honored = sum(
            decide_marketing_spend(
                studio, 30.0, 50.0, 90.0, 50.0, False, True, random.Random(i),
                influence_fn=director_influence_on_studio_decision,
            ).push_honored
            for i in range(200)
        )
        self.assertGreater(honored, 0)


if __name__ == "__main__":
    unittest.main()
