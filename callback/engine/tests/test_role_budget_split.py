"""actor/offers.py's Role.film_budget_millions vs. budget_for_role split: the whole film's
production budget (drives reception/marketing/ROI/studio-relations P&L, and studio selection) is a
real, independently-sampled number, distinct from the actor's own fee (a 5-35% slice of it, used
only for Deal negotiation and quote comparisons). Before this fix, budget_for_role stood in for
both at once, discarding the real, larger film budget after it picked the studio.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import Role, sample_role


class TestFilmBudgetVsFee(unittest.TestCase):
    def test_hand_built_role_defaults_film_budget_to_fee_for_backward_compatibility(self):
        role = Role(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=10.0,
                    gatekeeper="indie_first_timer")
        self.assertEqual(role.film_budget_millions, 10.0)

    def test_explicit_film_budget_is_kept_as_given(self):
        role = Role(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=10.0,
                    gatekeeper="indie_first_timer", film_budget_millions=120.0)
        self.assertEqual(role.film_budget_millions, 120.0)
        self.assertEqual(role.budget_for_role, 10.0)

    def test_sample_role_gives_a_film_budget_at_least_as_large_as_the_fee(self):
        rng = random.Random(1)
        for _ in range(500):
            role = sample_role(rng)
            self.assertGreaterEqual(role.film_budget_millions, role.budget_for_role)

    def test_sample_role_can_produce_real_tentpole_scale_film_budgets(self):
        # the whole point of the fix: real $150M+ productions should show up sometimes, not just
        # a fee-sized number that never clears the tens of millions.
        rng = random.Random(2)
        max_film_budget = max(sample_role(rng).film_budget_millions for _ in range(5000))
        self.assertGreater(max_film_budget, 150.0)

    def test_the_fee_is_a_modest_slice_of_the_film_budget_not_the_whole_thing(self):
        rng = random.Random(3)
        role = sample_role(rng)
        if role.film_budget_millions > 0:
            self.assertLessEqual(role.budget_for_role / role.film_budget_millions, 0.35 + 1e-9)


if __name__ == "__main__":
    unittest.main()
