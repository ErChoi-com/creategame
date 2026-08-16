"""genre/adaptation.py + simulation/_adaptations.py — a film adapted from an existing property
carries a built-in audience bonus and a critical-fidelity risk, and only rolls onto original
(non-franchise) roles.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import Role
from callback.engine.genre.adaptation import adaptation_audience_bonus, adaptation_critic_risk
from callback.engine.simulation._adaptations import maybe_attach_adaptation


def _role(**overrides) -> Role:
    base = dict(
        project_id="p_000001", genre="action", archetype="everyman", billing="supporting",
        char_age=35, type_strictness=0.5, difficulty=50.0, budget_for_role=10.0, gatekeeper="studio_tentpole",
    )
    base.update(overrides)
    return Role(**base)


class TestAdaptationBonusAndRisk(unittest.TestCase):
    def test_no_source_material_means_no_bonus_or_risk(self):
        self.assertEqual(adaptation_audience_bonus(None), 0.0)
        self.assertEqual(adaptation_critic_risk(None), 0.0)

    def test_an_adaptation_gets_a_real_audience_bonus_and_a_real_critic_risk(self):
        self.assertGreater(adaptation_audience_bonus("novel"), 0.0)
        self.assertLess(adaptation_critic_risk("novel"), 0.0)


class TestMaybeAttachAdaptation(unittest.TestCase):
    def test_can_attach_to_an_original_role(self):
        rng = random.Random(1)
        attached_any = False
        for _ in range(200):
            role = maybe_attach_adaptation(_role(), rng)
            if role.source_material is not None:
                attached_any = True
        self.assertTrue(attached_any)

    def test_never_attaches_to_a_franchise_role(self):
        rng = random.Random(2)
        for _ in range(200):
            role = maybe_attach_adaptation(_role(franchise_id="fr_001", installment_number=2), rng)
            self.assertIsNone(role.source_material)

    def test_never_double_attaches(self):
        rng = random.Random(3)
        already = _role(source_material="comic")
        role = maybe_attach_adaptation(already, rng)
        self.assertEqual(role.source_material, "comic")


if __name__ == "__main__":
    unittest.main()
