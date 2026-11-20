"""actor/offers.py's Role.latent_quality (§4.4 v17) — a real, persisted script-quality fact about
a listing, sampled once at generation time rather than re-rolled blind at resolution. Verifies it
actually drives simulation/career.py's resolve_quality (so the offer board's "buzz" signal is
predictive, not decorative) and that sample_role() produces real variation.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import LATENT_QUALITY_MEAN, Role, sample_role
from callback.engine.actor.positions import DIALS, WITH
from callback.engine.simulation.career import new_actor, simulate_project

_SCENE = {d: WITH for d in DIALS}


def _role(**overrides) -> Role:
    base = dict(
        project_id="p_000001", genre="action", archetype="everyman", billing="lead",
        char_age=35, type_strictness=0.5, difficulty=50.0, budget_for_role=10.0, gatekeeper="studio_tentpole",
        film_budget_millions=30.0,
    )
    base.update(overrides)
    return Role(**base)


class TestLatentQualitySampling(unittest.TestCase):
    def test_sample_role_produces_real_variation(self):
        rng = random.Random(1)
        values = [sample_role(rng).latent_quality for _ in range(200)]
        self.assertGreater(max(values) - min(values), 20.0)

    def test_sample_role_centres_near_the_documented_mean(self):
        rng = random.Random(2)
        values = [sample_role(rng).latent_quality for _ in range(500)]
        avg = sum(values) / len(values)
        self.assertAlmostEqual(avg, LATENT_QUALITY_MEAN, delta=3.0)


class TestLatentQualityDrivesResolution(unittest.TestCase):
    def test_a_higher_latent_quality_role_reads_as_a_better_film_on_average(self):
        state = new_actor()
        weak_scores = []
        strong_scores = []
        for seed in range(40):
            _, weak_result = simulate_project(
                state, _role(latent_quality=20.0), "table_work", (_SCENE, _SCENE, _SCENE), random.Random(seed),
            )
            weak_scores.append(weak_result.film_critic_score)

            _, strong_result = simulate_project(
                state, _role(latent_quality=90.0), "table_work", (_SCENE, _SCENE, _SCENE), random.Random(seed),
            )
            strong_scores.append(strong_result.film_critic_score)

        avg_weak = sum(weak_scores) / len(weak_scores)
        avg_strong = sum(strong_scores) / len(strong_scores)
        self.assertGreater(avg_strong, avg_weak)


if __name__ == "__main__":
    unittest.main()
