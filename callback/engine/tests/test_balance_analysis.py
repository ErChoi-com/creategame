"""simulation/_balance_analysis.py — tests for ANLZ-01/02/03 balance analysis."""
from __future__ import annotations

import unittest

from callback.engine.simulation._balance_analysis import (
    Finding, find_dead_ends, find_dominant_strategy, find_low_variance_clusters, run_full_analysis,
)
from callback.engine.simulation._sweep import PolicyStats


def _stats(archetype, net_worth_mean, credits_mean, age_mean, dead_end_rate=0.0, standing_means=None):
    return PolicyStats(
        archetype=archetype, runs=10, dead_end_runs=round(dead_end_rate * 10), dead_end_rate=dead_end_rate,
        age_mean=age_mean, net_worth_mean=net_worth_mean, net_worth_median=net_worth_mean, net_worth_stdev=1.0,
        credits_mean=credits_mean, standing_means=standing_means or {"heat": 20.0, "prestige": 20.0, "affection": 20.0},
        obituary_credits_mean=credits_mean,
    )


class TestFindDominantStrategy(unittest.TestCase):
    def test_detects_a_true_dominant_strategy(self):
        stats = {
            "winner": _stats("winner", 100.0, 50, 80),
            "loser_a": _stats("loser_a", 1.0, 1, 30),
            "loser_b": _stats("loser_b", 2.0, 2, 40),
        }
        finding = find_dominant_strategy(stats)
        self.assertEqual(finding.kind, "dominant_strategy")
        self.assertIn("winner", finding.summary)

    def test_confirms_no_dominance_when_leaders_split(self):
        stats = {
            "rich": _stats("rich", 100.0, 1, 30),
            "prolific": _stats("prolific", 1.0, 50, 30),
            "long_lived": _stats("long_lived", 1.0, 1, 90),
        }
        finding = find_dominant_strategy(stats)
        self.assertEqual(finding.kind, "no_dominance")


class TestFindDeadEnds(unittest.TestCase):
    def test_flags_high_dead_end_rate(self):
        stats = {"risky": _stats("risky", -5.0, 1, 30, dead_end_rate=0.5)}
        findings = find_dead_ends(stats)
        dead_end_findings = [f for f in findings if "risky" in f.summary]
        self.assertEqual(len(dead_end_findings), 1)

    def test_does_not_flag_low_dead_end_rate(self):
        stats = {"safe": _stats("safe", 5.0, 10, 60, dead_end_rate=0.02, standing_means={"heat": 60.0, "prestige": 60.0, "affection": 60.0})}
        findings = find_dead_ends(stats)
        dead_end_findings = [f for f in findings if "safe" in f.summary and "dead_end_rate" in f.evidence]
        self.assertEqual(len(dead_end_findings), 0)

    def test_flags_standing_axis_never_reaching_elite_floor(self):
        stats = {"a": _stats("a", 5.0, 10, 60, standing_means={"heat": 10.0, "prestige": 10.0, "affection": 10.0})}
        findings = find_dead_ends(stats)
        axis_findings = [f for f in findings if "Standing" in f.summary]
        self.assertEqual(len(axis_findings), 3)  # heat, prestige, affection all under floor


class TestFindLowVarianceClusters(unittest.TestCase):
    def test_clusters_similar_outcomes(self):
        stats = {
            "a": _stats("a", 1.0, 10, 60), "b": _stats("b", 2.0, 10, 60), "c": _stats("c", 100.0, 10, 60),
        }
        findings = find_low_variance_clusters(stats, net_worth_gap_floor=3.0)
        cluster_findings = [f for f in findings if f.kind == "low_variance_cluster" and "converge" in f.summary]
        self.assertEqual(len(cluster_findings), 1)
        self.assertIn("a", cluster_findings[0].evidence["archetypes"])
        self.assertIn("b", cluster_findings[0].evidence["archetypes"])
        self.assertNotIn("c", cluster_findings[0].evidence["archetypes"])

    def test_no_cluster_when_all_spread_out(self):
        stats = {"a": _stats("a", 1.0, 10, 60), "b": _stats("b", 50.0, 10, 60), "c": _stats("c", 100.0, 10, 60)}
        findings = find_low_variance_clusters(stats, net_worth_gap_floor=3.0)
        cluster_findings = [f for f in findings if "converge" in f.summary]
        self.assertEqual(len(cluster_findings), 0)


class TestRunFullAnalysis(unittest.TestCase):
    def test_returns_all_three_analysis_dimensions(self):
        stats = {
            "a": _stats("a", 1.0, 10, 60, dead_end_rate=0.3),
            "b": _stats("b", 2.0, 10, 60),
        }
        analysis = run_full_analysis(stats)
        self.assertIn("dominant_strategy", analysis)
        self.assertIn("dead_ends", analysis)
        self.assertIn("low_variance_clusters", analysis)
        self.assertIsInstance(analysis["dominant_strategy"], Finding)


if __name__ == "__main__":
    unittest.main()
