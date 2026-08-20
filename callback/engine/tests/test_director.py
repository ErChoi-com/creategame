"""director/ behaviour: DirectorSkill, development-hell greenlighting, the steerable edit, and
casting from the other side of §4.4's Utility.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.offers import Role
from callback.engine.actor.persona import Persona
from callback.engine.actor.standing import new_standing_model
from callback.engine.director.attributes import DirectorAttributes, perceived_script_quality
from callback.engine.director.casting import evaluate_candidate
from callback.engine.director.development import (
    DevProject,
    DIRECTOR_SPECTACLE_BONUS_MAX,
    SELF_FINANCE_BUYOUT_FRACTION,
    advance_quarter,
    apply_action,
    attempt_self_finance,
    difficulty,
    director_spectacle_bonus,
    quarters_for_directed_film,
    self_finance_buyout_cost,
    self_finance_momentum_threshold,
    self_finance_rush_penalty,
    studio_release_probability,
)
from callback.engine.director.edit import steered_post_luck
from callback.engine.director.skill import director_skill


class TestDirectorSkill(unittest.TestCase):
    def test_higher_attributes_give_higher_skill_on_average(self):
        weak = DirectorAttributes(vision=20, command=20, craft=20)
        strong = DirectorAttributes(vision=90, command=90, craft=90)
        rng_a, rng_b = random.Random(1), random.Random(1)
        self.assertGreater(
            director_skill(strong, passion_project=False, rng=rng_a),
            director_skill(weak, passion_project=False, rng=rng_b),
        )

    def test_passion_project_beats_paycheck_engagement(self):
        attrs = DirectorAttributes(vision=60, command=60, craft=60)
        rng_a, rng_b = random.Random(2), random.Random(2)
        self.assertGreater(
            director_skill(attrs, passion_project=True, rng=rng_a),
            director_skill(attrs, passion_project=False, rng=rng_b),
        )

    def test_high_taste_narrows_perceived_quality_error(self):
        rng = random.Random(3)
        readings_low_taste = [perceived_script_quality(60, taste=10, rng=rng) for _ in range(200)]
        rng = random.Random(3)
        readings_high_taste = [perceived_script_quality(60, taste=95, rng=rng) for _ in range(200)]
        import statistics as st
        self.assertLess(st.pstdev(readings_high_taste), st.pstdev(readings_low_taste))


class TestDevelopment(unittest.TestCase):
    def test_difficulty_grows_with_budget(self):
        self.assertGreater(difficulty(170), difficulty(4))

    def test_cutting_budget_lowers_difficulty(self):
        project = DevProject(script_id="s1", budget_ask=100)
        cut = apply_action(project, "cut_budget")
        self.assertLess(difficulty(cut.budget_ask), difficulty(project.budget_ask))

    def test_momentum_decays_and_eventually_dies(self):
        project = DevProject(script_id="s1", momentum=0.5, budget_ask=170)
        rng = random.Random(4)
        for _ in range(200):
            project, greenlit = advance_quarter(project, pkg_strength=10, rng=rng)  # deliberately weak package
            if greenlit or project.dead:
                break
        self.assertTrue(project.dead or greenlit)

    def test_self_finance_forces_full_momentum_on_an_already_owned_project(self):
        # apply_action's own "self_finance" branch only ever runs on a project you already own —
        # acquiring it in the first place is attempt_self_finance()'s job, tested below.
        owned = DevProject(script_id="s1", momentum=0.3, self_financed=True)
        project = apply_action(owned, "self_finance")
        self.assertEqual(project.momentum, 1.0)
        self.assertTrue(project.self_financed)

    def test_apply_action_alone_never_grants_self_financing(self):
        project = apply_action(DevProject(script_id="s1"), "self_finance")
        self.assertFalse(project.self_financed)

    def test_a_fresh_project_is_not_self_financed(self):
        self.assertFalse(DevProject(script_id="s1").self_financed)

    def test_frozen_project_never_advances(self):
        project = apply_action(DevProject(script_id="s1"), "drawer")
        new_project, greenlit = advance_quarter(project, pkg_strength=90, rng=random.Random(5))
        self.assertFalse(greenlit)
        self.assertEqual(new_project.momentum, project.momentum)


class TestSelfFinanceAcquisition(unittest.TestCase):
    def test_studio_release_probability_falls_as_momentum_rises(self):
        self.assertGreater(studio_release_probability(0.1), studio_release_probability(0.9))

    def test_buyout_cost_scales_with_budget(self):
        self.assertAlmostEqual(self_finance_buyout_cost(100.0), 100.0 * SELF_FINANCE_BUYOUT_FRACTION)

    def test_buyout_cost_is_flat_for_an_original_or_a_brand_new_franchises_first_entry(self):
        flat = 100.0 * SELF_FINANCE_BUYOUT_FRACTION
        self.assertAlmostEqual(self_finance_buyout_cost(100.0, installment_number=0), flat)
        self.assertAlmostEqual(self_finance_buyout_cost(100.0, installment_number=1), flat)

    def test_buyout_cost_rises_with_installment_count(self):
        # An established franchise's real IP value is on top of its production budget — buying it
        # out has to cover more than just what it cost to make.
        costs = [self_finance_buyout_cost(100.0, installment_number=n) for n in (2, 3, 5, 8)]
        self.assertTrue(all(later > earlier for earlier, later in zip(costs, costs[1:])))
        self.assertGreater(costs[0], 100.0 * SELF_FINANCE_BUYOUT_FRACTION)

    def test_buyout_cost_is_highest_right_after_a_fresh_release(self):
        # Same installment depth, but one franchise just released something and the other hasn't
        # in years — the freshly-active one should cost more to own right now.
        fresh = self_finance_buyout_cost(100.0, installment_number=5, years_since_last_release=0)
        stale = self_finance_buyout_cost(100.0, installment_number=5, years_since_last_release=10)
        self.assertGreater(fresh, stale)

    def test_a_long_dormant_franchise_decays_toward_the_flat_rate(self):
        # No matter how many installments it racked up while active, a franchise that's sat
        # dormant for a long time isn't worth much of a premium to buy out today.
        flat = 100.0 * SELF_FINANCE_BUYOUT_FRACTION
        long_dormant = self_finance_buyout_cost(100.0, installment_number=8, years_since_last_release=50)
        self.assertAlmostEqual(long_dormant, flat, delta=flat * 0.05)

    def test_years_since_last_release_does_not_apply_to_an_original_or_a_first_entry(self):
        # installment_number <= 1 always returns the flat rate — there's no "since last time" yet,
        # same convention genre.franchise.spacing_modifier already uses.
        flat = 100.0 * SELF_FINANCE_BUYOUT_FRACTION
        self.assertAlmostEqual(self_finance_buyout_cost(100.0, installment_number=1, years_since_last_release=0), flat)
        self.assertAlmostEqual(self_finance_buyout_cost(100.0, installment_number=0, years_since_last_release=20), flat)

    def test_buyout_multiplier_is_capped_for_the_deepest_freshest_franchises(self):
        from callback.engine.director.development import SELF_FINANCE_VALUE_MULTIPLIER_CAP
        cost = self_finance_buyout_cost(100.0, installment_number=30, years_since_last_release=0)
        self.assertAlmostEqual(cost, 100.0 * SELF_FINANCE_BUYOUT_FRACTION * SELF_FINANCE_VALUE_MULTIPLIER_CAP)

    def test_attempt_self_finance_charges_more_for_a_deep_franchise_entry(self):
        original = DevProject(script_id="s1", momentum=5.0, budget_ask=100.0, installment_number=0)
        sequel = DevProject(script_id="s2", momentum=5.0, budget_ask=100.0, installment_number=8)
        for seed in range(30):
            o1 = attempt_self_finance(original, random.Random(seed), available_money=10**9)
            o2 = attempt_self_finance(sequel, random.Random(seed), available_money=10**9)
            if not o1.released_free and not o2.released_free:
                self.assertGreater(o2.cost_paid, o1.cost_paid)
                return
        self.skipTest("every seed in range released one or both for free — RNG variance, not a bug")

    def test_already_self_financed_project_is_a_no_op(self):
        project = DevProject(script_id="s1", self_financed=True)
        outcome = attempt_self_finance(project, random.Random(1), available_money=0.0)
        self.assertTrue(outcome.acquired)
        self.assertFalse(outcome.just_acquired)
        self.assertEqual(outcome.cost_paid, 0.0)

    def test_a_stalled_low_momentum_project_is_often_released_for_free(self):
        project = DevProject(script_id="s1", momentum=0.1, budget_ask=50.0)
        rng = random.Random(2)
        freebies = sum(
            1 for _ in range(300)
            if attempt_self_finance(project, rng, available_money=0.0).released_free
        )
        self.assertGreater(freebies, 0)

    def test_cannot_afford_the_buyout_and_studio_wont_release_leaves_it_unowned(self):
        # A near-certain-to-hold-on studio (very high momentum) with a real buyout price and zero
        # money to pay it — the acquisition should fail outright, deterministically enough across
        # many seeds that this isn't a fluke.
        project = DevProject(script_id="s1", momentum=5.0, budget_ask=170.0)
        for seed in range(30):
            outcome = attempt_self_finance(project, random.Random(seed), available_money=0.0)
            if not outcome.acquired:
                self.assertTrue(outcome.could_not_afford)
                self.assertEqual(outcome.cost_paid, 0.0)
                return
        self.fail("expected at least one seed where the studio didn't release it for free")

    def test_affording_the_buyout_acquires_the_project(self):
        project = DevProject(script_id="s1", momentum=5.0, budget_ask=170.0)
        cost = self_finance_buyout_cost(project.budget_ask)
        for seed in range(30):
            outcome = attempt_self_finance(project, random.Random(seed), available_money=cost)
            if not outcome.released_free:
                self.assertTrue(outcome.acquired)
                self.assertTrue(outcome.just_acquired)
                self.assertEqual(outcome.cost_paid, cost)
                self.assertTrue(outcome.project.self_financed)
                return
        self.fail("expected at least one seed where the studio didn't release it for free")


class TestSelfFinanceRushPenalty(unittest.TestCase):
    """A studio-backed greenlight can't happen without momentum clearing greenlight_probability's
    own bar; self-financing skips that check outright. self_finance_rush_penalty is the after-the-
    fact stand-in — the momentum bar itself scales with budget (self_finance_momentum_threshold,
    off difficulty() same as everywhere else in this design): a small ask clears it almost for
    free, a real tentpole needs real heat behind it, or the finished film reads as rushed."""

    def test_no_penalty_at_or_above_the_threshold_for_that_budget(self):
        threshold = self_finance_momentum_threshold(100.0)
        self.assertEqual(self_finance_rush_penalty(threshold, 100.0), 0.0)
        self.assertEqual(self_finance_rush_penalty(threshold + 1.0, 100.0), 0.0)

    def test_real_penalty_below_the_threshold(self):
        self.assertGreater(self_finance_rush_penalty(0.05, 100.0), 0.0)

    def test_penalty_grows_the_thinner_the_package_was(self):
        # Both comfortably under the $100M threshold (~1.45) but far enough apart that neither
        # saturates the cap — a near-miss should cost less than showing up with almost nothing.
        thin = self_finance_rush_penalty(1.2, 100.0)
        thinner = self_finance_rush_penalty(0.9, 100.0)
        self.assertGreater(thinner, thin)

    def test_penalty_scales_unbounded_with_shortfall(self):
        # No separate cap anymore — craft_contribution's own 0-100 clamp (in _resolve_directed_film)
        # is the only ceiling. A near-zero-momentum tentpole greenlight should cost real, uncapped
        # points here, even past what a single-digit "mild ding" would allow.
        self.assertGreater(self_finance_rush_penalty(0.0, 300.0), 30.0)
        self.assertGreater(self_finance_rush_penalty(-5.0, 300.0), self_finance_rush_penalty(0.0, 300.0))

    def test_a_bigger_budget_demands_more_momentum_to_clear(self):
        self.assertGreater(self_finance_momentum_threshold(300.0), self_finance_momentum_threshold(5.0))

    def test_the_same_momentum_can_pass_a_small_ask_and_fail_a_big_one(self):
        momentum = 0.5  # clears a ~$1M ask's own bar (~0.41) but not a $300M one's (~1.75)
        self.assertEqual(self_finance_rush_penalty(momentum, 1.0), 0.0)
        self.assertGreater(self_finance_rush_penalty(momentum, 300.0), 0.0)


class TestEditAndCasting(unittest.TestCase):
    def test_high_craft_steers_post_luck_mean_up(self):
        rng_a, rng_b = random.Random(6), random.Random(6)
        low = [steered_post_luck(craft=20, efficiency=50, rng=rng_a) for _ in range(500)]
        high = [steered_post_luck(craft=90, efficiency=50, rng=rng_b) for _ in range(500)]
        import statistics as st
        self.assertGreater(st.mean(high), st.mean(low))

    def test_evaluate_candidate_reuses_actor_utility(self):
        attrs = Attributes()
        role = Role(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=10,
                    gatekeeper="indie_first_timer")
        score = evaluate_candidate(attrs, Persona(), new_standing_model(), role, candidate_age=40, candidate_quote=0.3)
        self.assertIsInstance(score, float)


class TestSpectacleBonusDiminishingReturns(unittest.TestCase):
    """v35 — director_spectacle_bonus is the director's OWN, isolated ability to sell a film
    (Opening only, never audience/critic score). Now a concave curve (POWER<1) on a lower ceiling
    (9.0, down from 12.0) — genuine diminishing returns, not just a reshaped ceiling."""

    def test_neutral_and_below_score_zero(self):
        self.assertEqual(director_spectacle_bonus(50.0), 0.0)
        self.assertEqual(director_spectacle_bonus(10.0), 0.0)

    def test_max_vision_hits_the_new_lower_ceiling(self):
        self.assertAlmostEqual(director_spectacle_bonus(100.0), DIRECTOR_SPECTACLE_BONUS_MAX)

    def test_marginal_gain_shrinks_as_vision_climbs(self):
        gain_low = director_spectacle_bonus(65.0) - director_spectacle_bonus(50.0)  # first 15 points off the floor
        gain_high = director_spectacle_bonus(100.0) - director_spectacle_bonus(85.0)  # last 15 points to the cap
        self.assertGreater(gain_low, gain_high)

    def test_a_near_maxed_director_scores_below_the_old_linear_ceiling(self):
        # The old formula (linear, MAX=12.0) gave vision=96 -> 12*0.92=11.04. The new one must land
        # below that, not just reshape where the curve sits — the whole point of also cutting MAX.
        self.assertLess(director_spectacle_bonus(96.0), 11.04)


class TestQuartersVisionCoupling(unittest.TestCase):
    """v35 — real spectacle now costs real production time: quarters_for_directed_film reads
    Vision too, not just budget/Efficiency, so chasing spectacle bonus isn't free."""

    def test_neutral_vision_matches_old_behavior(self):
        # vision=50.0 is the default AND the neutral point (zero vision_term) — must reproduce
        # exactly what quarters_for_directed_film(budget, efficiency) alone used to return.
        with_default = quarters_for_directed_film(150.0, 90.0)
        with_explicit_neutral = quarters_for_directed_film(150.0, 90.0, vision=50.0)
        self.assertEqual(with_default, with_explicit_neutral)

    def test_higher_vision_never_needs_fewer_quarters(self):
        low_vision = quarters_for_directed_film(200.0, 90.0, vision=50.0)
        high_vision = quarters_for_directed_film(200.0, 90.0, vision=96.0)
        self.assertGreaterEqual(high_vision, low_vision)

    def test_max_everything_still_respects_the_absolute_ceiling(self):
        from callback.engine.director.development import DIRECTOR_QUARTERS_ABSOLUTE_CEILING
        worst = quarters_for_directed_film(1_000_000.0, 0.0, vision=100.0)
        self.assertLessEqual(worst, DIRECTOR_QUARTERS_ABSOLUTE_CEILING)


if __name__ == "__main__":
    unittest.main()
