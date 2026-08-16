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
        budget=20.0, break_even=30, opening=25.0, zeitgeist=55, legs=2.0, gross=50.0, roi=1.5,
    )
    base.update(overrides)
    return ReceptionResult(**base)


class TestReleaseStrategies(unittest.TestCase):
    def test_wide_is_unchanged(self):
        r = _reception()
        self.assertEqual(apply_release_strategy(r, WIDE, random.Random(1)), r)

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
