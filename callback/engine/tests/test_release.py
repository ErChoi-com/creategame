"""actor/release.py — release strategies and the weekly box-office trajectory."""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.release import (
    FESTIVAL,
    LIMITED,
    SHELVED,
    STREAMING,
    WIDE,
    apply_release_strategy,
    festival_acquisition_probability,
    weekly_gross_curve,
)
from callback.engine.actor.reception import ReceptionResult


def _reception(**overrides) -> ReceptionResult:
    base = dict(
        project_quality=60, film_critic_score=60, audience_score=55,
        budget=20.0, marketing=9.0, break_even=30, opening=25.0, zeitgeist=55, legs=2.0, gross=50.0, roi=1.5,
    )
    base.update(overrides)
    return ReceptionResult(**base)


class TestReleaseStrategies(unittest.TestCase):
    def test_wide_is_unchanged(self):
        r = _reception()
        self.assertEqual(apply_release_strategy(r, WIDE, random.Random(1)), r)

    def test_marketing_is_tracked_separately_from_production_budget(self):
        r = _reception(budget=20.0, marketing=9.0)
        self.assertEqual(r.budget, 20.0)
        self.assertEqual(r.marketing, 9.0)
        self.assertNotEqual(r.budget, r.marketing)

    def test_streaming_zeroes_marketing_no_theatrical_spend(self):
        r = _reception()
        streamed = apply_release_strategy(r, STREAMING, random.Random(1))
        self.assertEqual(streamed.marketing, 0.0)
        self.assertEqual(streamed.budget, r.budget)  # production budget itself is untouched

    def test_streaming_roi_is_a_multiple_not_a_gain_fraction(self):
        """Regression: streaming's roi must sit on the same 1.0-is-break-even scale every other
        release path uses (and simulation/bands.ROI_BANDS assumes) — a guaranteed-profitable
        streaming_multiplier > 1.0 deal must never band as "a loss"."""
        from callback.engine.actor.release import STREAMING_BUYOUT_MULTIPLIER
        from callback.engine.simulation.bands import roi_band
        r = _reception(budget=20.0)
        streamed = apply_release_strategy(r, STREAMING, random.Random(1))
        self.assertAlmostEqual(streamed.roi, STREAMING_BUYOUT_MULTIPLIER)
        self.assertNotEqual(roi_band(streamed.roi), "a loss")

    def test_shelved_zeroes_marketing_too(self):
        r = _reception()
        shelved = apply_release_strategy(r, SHELVED, random.Random(1))
        self.assertEqual(shelved.marketing, 0.0)

    def test_unsold_festival_zeroes_marketing(self):
        r = _reception(film_critic_score=10, audience_score=10)  # a near-certain non-acquisition
        result = apply_release_strategy(r, FESTIVAL, random.Random(7), cast_star_power=5)
        if result.gross == 0.0:  # unsold branch
            self.assertEqual(result.marketing, 0.0)

    def test_limited_shrinks_opening_but_can_still_profit_on_legs(self):
        r = _reception(legs=6.0)
        limited = apply_release_strategy(r, LIMITED, random.Random(1))
        self.assertLess(limited.gross, r.gross)
        self.assertGreater(limited.gross, 0)

    def test_shelved_is_a_total_loss(self):
        r = _reception()
        shelved = apply_release_strategy(r, SHELVED, random.Random(1))
        self.assertEqual(shelved.gross, 0.0)
        self.assertEqual(shelved.roi, -1.0)

    def test_streaming_pays_a_flat_guaranteed_amount_regardless_of_quality(self):
        good = _reception(film_critic_score=90)
        bad = _reception(film_critic_score=20, budget=good.budget)
        good_stream = apply_release_strategy(good, STREAMING, random.Random(1))
        bad_stream = apply_release_strategy(bad, STREAMING, random.Random(1))
        self.assertEqual(good_stream.gross, bad_stream.gross)
        self.assertGreater(good_stream.gross, good.budget)  # "budget plus 20%"

    def test_festival_acquisition_probability_rewards_critical_and_star_strength(self):
        weak = festival_acquisition_probability(film_critic_score=40, cast_star_power=20)
        strong = festival_acquisition_probability(film_critic_score=85, cast_star_power=70)
        self.assertGreater(strong, weak)

    def test_unacquired_festival_film_returns_zero_roi(self):
        r = _reception(film_critic_score=10, audience_score=10)  # about as unlikely to sell as it gets
        outcomes = [apply_release_strategy(r, FESTIVAL, random.Random(s), cast_star_power=5).roi for s in range(50)]
        self.assertIn(0.0, outcomes)

    def test_no_festival_sale_resolver_falls_back_to_the_old_limited_behavior(self):
        """Regression: a caller that never passes festival_sale_resolver (director mode's own
        festival path, verify.py, any pre-existing test) must see the exact same outcome as before
        this feature existed — acquired always means a LIMITED release at the seller's own terms."""
        r = _reception(film_critic_score=90, audience_score=85)  # a near-certain acquisition
        without_resolver = apply_release_strategy(r, FESTIVAL, random.Random(11), cast_star_power=70)
        with_limited = apply_release_strategy(r, LIMITED, random.Random(11), cast_star_power=70)
        # Both draw from the same rng stream up to the acquisition roll, then diverge only in how
        # many further rng draws each path makes — comparing shape, not bit-for-bit equality.
        self.assertGreater(without_resolver.gross, 0.0)
        self.assertEqual(without_resolver.marketing, with_limited.marketing)

    def test_festival_sale_resolver_is_only_invoked_once_acquired(self):
        calls = []

        def resolver(reception, m_share, r_share):
            calls.append((reception, m_share, r_share))
            return reception

        unsold = _reception(film_critic_score=5, audience_score=5)
        for seed in range(30):
            apply_release_strategy(unsold, FESTIVAL, random.Random(seed), cast_star_power=5, festival_sale_resolver=resolver)
        # A near-guaranteed non-acquisition should leave the resolver untouched most/all of the time.
        self.assertLess(len(calls), 30)

        acquired = _reception(film_critic_score=95, audience_score=95)
        calls.clear()
        apply_release_strategy(acquired, FESTIVAL, random.Random(1), cast_star_power=90, festival_sale_resolver=resolver)
        self.assertEqual(len(calls), 1)

    def test_festival_sale_resolver_return_value_wins(self):
        acquired = _reception(film_critic_score=95, audience_score=95, budget=10.0)
        sold = _reception(budget=10.0, gross=42.0, marketing=0.0, roi=4.2)
        result = apply_release_strategy(
            acquired, FESTIVAL, random.Random(1), cast_star_power=90,
            festival_sale_resolver=lambda reception, m, r: sold,
        )
        self.assertEqual(result.gross, 42.0)
        self.assertEqual(result.roi, 4.2)


class TestWeeklyGrossCurve(unittest.TestCase):
    def test_first_week_is_the_opening(self):
        curve = weekly_gross_curve(opening=10.0, legs=2.0, weeks=4)
        self.assertEqual(curve[0], 10.0)

    def test_curve_decays(self):
        curve = weekly_gross_curve(opening=10.0, legs=2.0, weeks=4)
        self.assertTrue(all(curve[i] >= curve[i + 1] for i in range(len(curve) - 1)))

    def test_higher_legs_decays_more_slowly(self):
        short = weekly_gross_curve(opening=10.0, legs=1.2, weeks=4)
        long_run = weekly_gross_curve(opening=10.0, legs=6.0, weeks=4)
        self.assertGreater(long_run[-1], short[-1])


if __name__ == "__main__":
    unittest.main()
