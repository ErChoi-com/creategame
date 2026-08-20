"""simulation/_decision_coverage.py — unit tests for the coverage-check tool, checked against
docs/design/decision-map.md's own ID vocabulary."""
from __future__ import annotations

import unittest
from collections import Counter

from callback.engine.simulation._archetype_policies import prestige_chaser
from callback.engine.simulation._decision_coverage import check_coverage, load_expected_ids, run_with_coverage


class TestCheckCoverage(unittest.TestCase):
    def test_reports_ids_with_zero_count(self):
        expected = frozenset({"a", "b", "c"})
        visited = Counter({"a": 2})
        self.assertEqual(check_coverage(visited, expected), ["b", "c"])

    def test_reports_empty_list_when_all_visited(self):
        expected = frozenset({"a", "b", "c"})
        visited = Counter({"a": 1, "b": 1, "c": 1})
        self.assertEqual(check_coverage(visited, expected), [])

    def test_load_expected_ids_excludes_header_row(self):
        ids = load_expected_ids()
        self.assertNotIn("ID", ids)
        self.assertGreaterEqual(len(ids), 50)


class TestCoverageIntegration(unittest.TestCase):
    def test_prestige_chaser_visits_are_all_known_ids(self):
        summary, visited = run_with_coverage(prestige_chaser, seed=1, years=15)
        self.assertIsInstance(summary, dict)
        expected = load_expected_ids()
        unknown = [key for key in visited if key not in expected]
        self.assertEqual(unknown, [], f"visited IDs not present in decision-map.md: {unknown}")


if __name__ == "__main__":
    unittest.main()
