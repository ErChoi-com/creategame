"""simulation/_relationships.py — studios and requested directors both remember profit and loss,
and that trust feeds back into real casting odds and director skill, not just a P&L ledger nobody
reads.
"""
from __future__ import annotations

import unittest

from callback.engine.simulation._relationships import (
    TRUST_DEFAULT,
    director_skill_bonus_from_trust,
    trust_band,
    update_relationship,
    utility_bonus_from_trust,
)


class TestUpdateRelationship(unittest.TestCase):
    def test_a_profitable_film_raises_trust(self):
        relations = update_relationship({}, "studio_a", budget_millions=10.0, roi=2.0, gross_millions=25.0)
        self.assertGreater(relations["studio_a"].trust, TRUST_DEFAULT)
        self.assertEqual(relations["studio_a"].projects_together, 1)

    def test_a_money_losing_film_lowers_trust_more_than_an_equivalent_win_raises_it(self):
        win = update_relationship({}, "studio_a", budget_millions=10.0, roi=1.3, gross_millions=13.0)
        loss = update_relationship({}, "studio_b", budget_millions=10.0, roi=0.7, gross_millions=7.0)
        win_delta = win["studio_a"].trust - TRUST_DEFAULT
        loss_delta = TRUST_DEFAULT - loss["studio_b"].trust
        self.assertGreater(loss_delta, win_delta)  # losses hurt more than equivalent gains help

    def test_repeated_projects_accumulate_net_profit_and_count(self):
        relations = {}
        relations = update_relationship(relations, "studio_a", 10.0, 1.5, 15.0)
        relations = update_relationship(relations, "studio_a", 20.0, 1.2, 24.0)
        rel = relations["studio_a"]
        self.assertEqual(rel.projects_together, 2)
        self.assertAlmostEqual(rel.net_profit_millions, (15.0 - 10.0) + (24.0 - 20.0))

    def test_trust_never_leaves_0_100(self):
        relations = {}
        for _ in range(20):
            relations = update_relationship(relations, "studio_a", 10.0, 5.0, 50.0)
        self.assertLessEqual(relations["studio_a"].trust, 100.0)
        relations = {}
        for _ in range(20):
            relations = update_relationship(relations, "studio_b", 10.0, 0.1, 1.0)
        self.assertGreaterEqual(relations["studio_b"].trust, 0.0)


class TestTrustBonuses(unittest.TestCase):
    def test_no_relationship_means_no_bonus(self):
        self.assertEqual(utility_bonus_from_trust({}, "studio_a"), 0.0)
        self.assertEqual(director_skill_bonus_from_trust({}, "n_001"), 0.0)
        self.assertEqual(director_skill_bonus_from_trust({}, None), 0.0)

    def test_high_trust_gives_a_positive_bonus_low_trust_a_negative_one(self):
        relations = update_relationship({}, "studio_a", 10.0, 3.0, 30.0)  # a big hit -> high trust
        self.assertGreater(utility_bonus_from_trust(relations, "studio_a"), 0.0)
        relations2 = update_relationship({}, "studio_b", 10.0, 0.1, 1.0)  # a near-total loss -> low trust
        self.assertLess(utility_bonus_from_trust(relations2, "studio_b"), 0.0)


class TestTrustBand(unittest.TestCase):
    def test_bands_cover_the_full_range_and_are_strings(self):
        for t in (0, 10, 30, 50, 60, 80, 100):
            self.assertIsInstance(trust_band(t), str)


if __name__ == "__main__":
    unittest.main()
