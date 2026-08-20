"""simulation/_archetype_policies.py — smoke tests for the playtest archetype policies, each
exercising decision points catalogued in docs/design/decision-map.md."""
from __future__ import annotations

import unittest
from collections import Counter

from callback.engine.simulation._archetype_policies import franchise_maximizer, prestige_chaser


class TestPrestigeChaser(unittest.TestCase):
    def test_runs_to_completion_without_raising(self):
        result = prestige_chaser(seed=1, years=15)
        self.assertIsInstance(result, dict)
        self.assertGreater(result["age"], 22)

    def test_tallies_awards_and_your_part_script_note(self):
        # A longer window (40 years) to reliably reach the awards-eligibility spotlight threshold
        # at least once — engine RNG makes exact hit-rates non-deterministic across environments
        # even at a fixed seed if the seed/rng-consumption pattern shifts, so this asserts presence
        # rather than an exact count.
        visited: Counter = Counter()
        prestige_chaser(seed=1, years=40, visited=visited)
        self.assertGreater(visited["script_note.actor.your_part"], 0)
        award_categories_visited = [k for k in visited if k.startswith("awards.actor.category.")]
        self.assertTrue(award_categories_visited, f"expected at least one awards category tallied, got {dict(visited)}")


class TestFranchiseMaximizer(unittest.TestCase):
    def test_runs_to_completion_without_raising(self):
        result = franchise_maximizer(seed=3, years=40)
        self.assertIsInstance(result, dict)
        self.assertGreater(result["age"], 22)

    def test_tracks_franchise_continuity(self):
        result = franchise_maximizer(seed=3, years=40)
        self.assertIsInstance(result["held_franchise_ids"], list)

        # Franchise offers are randomly generated — a single seed isn't guaranteed to reach the
        # multi-picture-deal Standing threshold (MULTI_PICTURE_MIN_STANDING=40.0) within a 40-year
        # window, so try a small fixed seed set and use the first one that gets there.
        reached_deal = False
        for seed in (3, 7, 21):
            visited: Counter = Counter()
            franchise_maximizer(seed=seed, years=40, visited=visited)
            if visited["multi_picture_deal.sign"] > 0:
                reached_deal = True
                break
        self.assertTrue(reached_deal, "expected at least one of seeds [3, 7, 21] to sign a multi-picture deal within 40 years")


if __name__ == "__main__":
    unittest.main()
