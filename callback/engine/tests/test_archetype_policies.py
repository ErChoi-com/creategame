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

    def test_tallies_awards(self):
        # A longer window (40 years) to reliably reach the awards-eligibility spotlight threshold
        # at least once — engine RNG makes exact hit-rates non-deterministic across environments
        # even at a fixed seed if the seed/rng-consumption pattern shifts, so this asserts presence
        # rather than an exact count.
        awards_seen = False
        last_visited: Counter = Counter()
        for seed in (1, 2, 3, 4, 5):
            visited: Counter = Counter()
            prestige_chaser(seed=seed, years=40, visited=visited)
            last_visited = visited
            if any(k.startswith("awards.actor.category.") for k in visited):
                awards_seen = True
                break
        self.assertTrue(awards_seen, f"expected at least one awards category tallied across 5 seeds, last run: {dict(last_visited)}")

    def test_script_note_your_part_is_currently_unreachable_finding(self):
        # FINDING (flagged for Phase 3/4 tuning, not a policy bug): script/costar approval
        # negotiation requires crossing APPROVAL_STANDING_THRESHOLD (65.0 weighted Standing,
        # leverage/approvals.py). Across a 59-seed x 60-year sweep of prestige_chaser — an
        # archetype built specifically to chase Standing — the best weighted score reached was
        # ~17.8, roughly a quarter of the threshold (see decision-map.md's Approvals callout).
        # This decision point (script_note.actor.your_part) is not proven reachable by any
        # archetype in Phase 1 — recorded here as a known, honest gap rather than force-passed
        # with a lucky-seed search, per CONTEXT.md's "no silent drops" rule. Phase 3's balance
        # analysis should treat "elite Standing tiers are effectively unreachable through normal
        # play" as a first-class finding, and Phase 4 decides whether APPROVAL_STANDING_THRESHOLD,
        # or the Standing gain/decay curve feeding it, is the correct lever.
        visited: Counter = Counter()
        prestige_chaser(seed=1, years=40, visited=visited)
        self.assertEqual(
            visited["script_note.actor.your_part"], 0,
            "If this now fails, the underlying imbalance was fixed — update decision-map.md's "
            "Approvals callout and this test to assert reachability instead of documenting the gap.",
        )


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
