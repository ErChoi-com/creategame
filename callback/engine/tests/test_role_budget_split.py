"""actor/offers.py's Role.film_budget_millions vs. budget_for_role split: the whole film's
production budget (drives reception/marketing/ROI/studio-relations P&L, and studio selection) is a
real, independently-sampled number, distinct from the actor's own fee (a negotiated, billing-scaled
slice of it — see negotiated_fee_share() — used only for Deal negotiation and quote comparisons).
Before this fix, budget_for_role stood in for both at once, discarding the real, larger film budget
after it picked the studio, AND was sampled from one flat 5-35% range regardless of billing — a bit
part could draw a lead-sized fee purely by chance.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import BILLING_FEE_SHARE, Role, negotiated_fee_share, sample_role


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
            lo, hi = BILLING_FEE_SHARE[role.billing]
            self.assertLessEqual(role.budget_for_role / role.film_budget_millions, hi + 1e-9)


class TestNegotiatedFeeByBilling(unittest.TestCase):
    def test_a_bit_part_earns_far_less_on_average_than_a_lead_on_the_same_film(self):
        # the exact bug this fixes: a bit role used to be able to draw the same 5-35% fee range
        # as a lead, on the same budget, purely by chance. At matched leverage, the bands
        # themselves guarantee a bit role's *typical* fee stays a small fraction of a lead's.
        rng = random.Random(1)
        film_budget = 150.0
        bit_fees = [film_budget * negotiated_fee_share("bit", 0.5, rng) for _ in range(500)]
        lead_fees = [film_budget * negotiated_fee_share("lead", 0.5, rng) for _ in range(500)]
        self.assertLess(sum(bit_fees) / len(bit_fees), (sum(lead_fees) / len(lead_fees)) * 0.15)

    def test_higher_leverage_pushes_the_fee_share_up_on_average(self):
        rng = random.Random(2)
        low = [negotiated_fee_share("lead", 0.0, rng) for _ in range(400)]
        high = [negotiated_fee_share("lead", 1.0, rng) for _ in range(400)]
        self.assertGreater(sum(high) / len(high), sum(low) / len(low))

    def test_share_always_stays_within_the_billings_own_band(self):
        rng = random.Random(3)
        for billing, (lo, hi) in BILLING_FEE_SHARE.items():
            for leverage in (0.0, 0.5, 1.0):
                for _ in range(100):
                    share = negotiated_fee_share(billing, leverage, rng)
                    self.assertGreaterEqual(share, lo)
                    self.assertLessEqual(share, hi)

    def test_a_bit_role_on_a_huge_tentpole_still_earns_a_plausible_fee_not_tens_of_millions(self):
        rng = random.Random(4)
        max_bit_fee_on_a_300m_film = max(
            300.0 * negotiated_fee_share("bit", 1.0, rng) for _ in range(500)
        )
        self.assertLess(max_bit_fee_on_a_300m_film, 15.0)


if __name__ == "__main__":
    unittest.main()
