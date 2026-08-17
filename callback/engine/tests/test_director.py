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
    SELF_FINANCE_BUYOUT_FRACTION,
    advance_quarter,
    apply_action,
    attempt_self_finance,
    difficulty,
    self_finance_buyout_cost,
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


if __name__ == "__main__":
    unittest.main()
