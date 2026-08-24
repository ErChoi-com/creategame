"""core/ behaviour in isolation — no actor/ import."""
from __future__ import annotations

import unittest

from callback.engine.core.meters import Meter, StandingModel
from callback.engine.core.util import clamp, positive_part, sigmoid


class TestUtil(unittest.TestCase):
    def test_clamp(self):
        self.assertEqual(clamp(150, 0, 100), 100)
        self.assertEqual(clamp(-5, 0, 100), 0)
        self.assertEqual(clamp(50, 0, 100), 50)

    def test_sigmoid_centre(self):
        self.assertAlmostEqual(sigmoid(0.0), 0.5)

    def test_sigmoid_extremes_bounded(self):
        self.assertEqual(sigmoid(1000), 1.0)
        self.assertEqual(sigmoid(-1000), 0.0)

    def test_positive_part(self):
        self.assertEqual(positive_part(-5), 0.0)
        self.assertEqual(positive_part(5), 5.0)


class TestMeter(unittest.TestCase):
    def test_clamps_on_set(self):
        m = Meter("heat", 50)
        m.set(150)
        self.assertEqual(m.clamped(), 100)

    def test_add(self):
        m = Meter("heat", 50)
        m.add(10)
        self.assertEqual(m.clamped(), 60)

    def test_decay_multiplicative(self):
        m = Meter("prestige", 50)
        m.decay_multiplicative(0.5)
        self.assertEqual(m.clamped(), 25)


class TestStandingModel(unittest.TestCase):
    def _model(self) -> StandingModel:
        return StandingModel(meters={
            "heat": Meter("heat", 40),
            "prestige": Meter("prestige", 60),
        })

    def test_weighted_score(self):
        model = self._model()
        score = model.weighted_score({"heat": 0.5, "prestige": 0.5})
        self.assertEqual(score, 50)

    def test_copy_does_not_alias_meters(self):
        original = self._model()
        copy = original.copy()
        copy.add("heat", 50)
        self.assertEqual(original["heat"], 40)
        self.assertEqual(copy["heat"], 90)

    def test_decay_applies_per_meter_factor(self):
        model = self._model()
        model.decay({"heat": 0.5, "prestige": 1.0})
        self.assertEqual(model["heat"], 20)
        self.assertEqual(model["prestige"], 60)


if __name__ == "__main__":
    unittest.main()
