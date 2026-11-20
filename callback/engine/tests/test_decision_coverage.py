"""simulation/_decision_coverage.py — unit tests for the coverage-check tool, checked against
docs/design/decision-map.md's own ID vocabulary."""
from __future__ import annotations

import unittest
from collections import Counter

from callback.engine.simulation import _archetype_policies as ap
from callback.engine.simulation._archetype_policies import prestige_chaser
from callback.engine.simulation._decision_coverage import ARCHETYPE_NAMES, check_coverage, load_expected_ids, run_with_coverage


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


class TestFullEightArchetypeCoverage(unittest.TestCase):
    """POLICY-02's concrete verification (Plan 05): the completed 8-archetype set, run at real
    volume, must reach every decision-map.md ID that decision-map.md's own Flagged Balance
    Findings section didn't explicitly exclude. Excluded IDs (Approvals-gated script notes,
    first-dollar-gross bonus, merchandising, both franchise spin-off pitches) are genuinely
    threshold-blocked under current tuning, not policy gaps — see decision-map.md for the full
    rationale and the 59-seed/60-year sweep that established it. This test intentionally uses a
    wider seed budget than any single archetype's own smoke test (prestige_chaser needs
    seeds 100-219 specifically to land the two rare-but-reachable awards categories,
    breakthrough and lead_comedy) — this is the one place in the suite where that's appropriate,
    since this test's whole job is confirming reachability at realistic volume, not smoke-testing
    a single run."""

    def test_zero_gaps_across_full_archetype_set(self):
        visited: Counter = Counter()
        for seed in range(100, 220):
            prestige_chaser(seed=seed, years=15, visited=visited)
        for name in ARCHETYPE_NAMES:
            if name == "prestige_chaser":
                continue
            fn = getattr(ap, name)
            for seed in range(1, 15):
                fn(seed=seed, years=60, visited=visited)

        gaps = check_coverage(visited)
        self.assertEqual(
            gaps, [],
            f"Coverage gap(s) found across the full 8-archetype set: {gaps}. Per CONTEXT.md's "
            "'no silent drops' rule, do not weaken this test to pass — either extend the "
            "responsible archetype's policy logic to reach the gap, or add a documented "
            "Flagged Balance Finding to decision-map.md excluding it with a real, cited "
            "threshold rationale (matching the pattern already used for Approvals/spin-offs).",
        )


if __name__ == "__main__":
    unittest.main()
