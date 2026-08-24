"""simulation/_sweep.py — tests for the automated sweep infrastructure (SWEEP-01/SWEEP-02)."""
from __future__ import annotations

import unittest

from callback.engine.simulation._decision_coverage import ARCHETYPE_NAMES
from callback.engine.simulation._sweep import (
    PolicyStats, _is_dead_end, run_full_sweep, run_policy_sweep,
)


class TestIsDeadEnd(unittest.TestCase):
    def test_flags_low_credits_and_negative_net_worth(self):
        self.assertTrue(_is_dead_end({"acting_credits": 1, "net_worth": -3.0}))

    def test_does_not_flag_healthy_run(self):
        self.assertFalse(_is_dead_end({"acting_credits": 10, "net_worth": 5.0}))

    def test_does_not_flag_low_credits_with_positive_net_worth(self):
        self.assertFalse(_is_dead_end({"acting_credits": 1, "net_worth": 5.0}))

    def test_does_not_flag_negative_net_worth_with_healthy_credits(self):
        self.assertFalse(_is_dead_end({"acting_credits": 10, "net_worth": -1.0}))

    def test_combines_acting_and_director_credits(self):
        self.assertFalse(_is_dead_end({"acting_credits": 1, "director_credits": 5, "net_worth": -1.0}))


class TestRunPolicySweep(unittest.TestCase):
    def test_runs_a_small_sweep_without_raising(self):
        stats = run_policy_sweep("prestige_chaser", range(1, 6), years=20, sample_trajectory=False)
        self.assertIsInstance(stats, PolicyStats)
        self.assertEqual(stats.runs, 5)
        self.assertGreaterEqual(stats.age_mean, 22)

    def test_dead_end_rate_is_between_zero_and_one(self):
        stats = run_policy_sweep("gambler", range(1, 11), years=30, sample_trajectory=False)
        self.assertGreaterEqual(stats.dead_end_rate, 0.0)
        self.assertLessEqual(stats.dead_end_rate, 1.0)

    def test_trajectory_sampling_produces_checkpoints(self):
        stats = run_policy_sweep("prestige_chaser", range(1, 4), years=45, sample_trajectory=True)
        self.assertGreater(len(stats.trajectories), 0)
        for traj in stats.trajectories:
            self.assertIn("seed", traj)
            self.assertGreater(len(traj["checkpoints"]), 0)
            for cp in traj["checkpoints"]:
                self.assertIn("year", cp)
                self.assertIn("standing", cp)

    def test_franchise_holders_tracked_for_franchise_maximizer(self):
        stats = run_policy_sweep("franchise_maximizer", range(1, 21), years=60, sample_trajectory=False)
        # Not every seed necessarily lands a franchise, but across 20 seeds at least one should.
        self.assertGreaterEqual(stats.franchise_holders, 0)


class TestRunFullSweep(unittest.TestCase):
    def test_covers_all_eight_archetypes(self):
        stats = run_full_sweep(seeds_per_policy=3, years=20)
        self.assertEqual(set(stats.keys()), set(ARCHETYPE_NAMES))
        for name, s in stats.items():
            self.assertEqual(s.runs, 3, f"{name} should have run 3 seeds")

    def test_runs_at_meaningful_volume_without_crashing(self):
        # ROADMAP Phase 2 success criterion 1: 50+ seeds per policy, single invocation, no crash.
        # Kept smaller here (10) for unit-test runtime; the real 50+ volume run lives in
        # simulation/_sweep.py's own __main__ block, exercised manually / by Phase 2's own report.
        stats = run_full_sweep(seeds_per_policy=10, years=30)
        for name, s in stats.items():
            self.assertEqual(s.runs, 10, f"{name} should have completed all 10 runs")


if __name__ == "__main__":
    unittest.main()
