"""awards/ behaviour: narrative bonuses, buzz score, vote splitting, category resolution."""
from __future__ import annotations

import random
import unittest

from callback.engine.awards.awards import (
    NarrativeContext,
    apply_vote_splitting,
    buzz_score,
    narrative_bonus,
    resolve_category,
)


class TestNarrativeBonus(unittest.TestCase):
    def test_shes_due_applies(self):
        ctx = NarrativeContext(prior_nominations=4, prior_wins=0)
        self.assertEqual(narrative_bonus(ctx), 14.0)

    def test_posthumous_dominates_other_flags(self):
        ctx = NarrativeContext(prior_nominations=4, prior_wins=0, posthumous=True)
        self.assertEqual(narrative_bonus(ctx), 20.0)

    def test_no_flags_is_zero(self):
        self.assertEqual(narrative_bonus(NarrativeContext()), 0.0)

    def test_negative_bonus_applies_when_overexposed(self):
        ctx = NarrativeContext(credits_this_season=5)
        self.assertEqual(narrative_bonus(ctx), -7.0)


class TestBuzzAndVoting(unittest.TestCase):
    def test_higher_spotlight_gives_higher_buzz_on_average(self):
        rng_a, rng_b = random.Random(1), random.Random(1)
        low = buzz_score(30, 50, 1.0, 50, 0, 0, rng_a)
        high = buzz_score(90, 50, 1.0, 50, 0, 0, rng_b)
        self.assertGreater(high, low)

    def test_vote_splitting_penalizes_both_same_film_nominees(self):
        scores = {"a": 60.0, "b": 55.0, "c": 40.0}
        updated = apply_vote_splitting(scores, ["a", "b"])
        self.assertLess(updated["a"], scores["a"])
        self.assertLess(updated["b"], scores["b"])
        self.assertEqual(updated["c"], scores["c"])

    def test_resolve_category_picks_the_highest(self):
        scores = {"a": 60.0, "b": 90.0, "c": 40.0}
        self.assertEqual(resolve_category(scores, random.Random(1)), "b")


if __name__ == "__main__":
    unittest.main()
