"""design/part-04-the-actor.md §4.2 — typecasting given real mechanical depth: Persona.legibility()
wired into the offer board and reception (previously computed, fully tested, never consumed), and
the "breaking type" payoff (a large Prestige bonus, a Legibility reset, a transformation flag)
built for the first time.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.attributes import Attributes
from callback.engine.actor.offers import Role
from callback.engine.actor.persona import Persona
from callback.engine.simulation.career import (
    ActorState,
    TRANSFORMATION_PRESTIGE_BONUS,
    default_scene_policy,
    new_actor,
    simulate_project,
)
from callback.engine.actor.standing import new_standing_model


def _legible_persona() -> Persona:
    other_genres = ["comedy", "action", "horror", "thriller", "romance", "scifi", "period", "musical", "family"]
    other_archetypes = ["romantic_lead", "villain", "everyman", "mentor", "ingenue",
                         "authority", "comic_relief", "ensemble"]
    return Persona(
        genre_affinity={"drama": 100.0, **{g: 0.0 for g in other_genres}},
        archetype_affinity={"leading_hero": 100.0, **{a: 0.0 for a in other_archetypes}},
    )


def _off_lane_role(**overrides) -> Role:
    base = dict(
        project_id="p1", genre="horror", archetype="ensemble", billing="lead",
        char_age=35, type_strictness=1.0, difficulty=50.0, budget_for_role=10.0,
        gatekeeper="indie_first_timer",
    )
    base.update(overrides)
    return Role(**base)


class TestTransformationPayoff(unittest.TestCase):
    def _legible_actor(self, age: int = 35) -> ActorState:
        return ActorState(age=age, attrs=Attributes(), persona=_legible_persona(), standing=new_standing_model())

    def test_a_successful_type_break_flags_transformation_and_resets_legibility(self):
        state = self._legible_actor()
        role = _off_lane_role()
        pre_legibility = state.persona.legibility()

        found = False
        for seed in range(400):
            rng = random.Random(seed)
            scenes = default_scene_policy(rng)
            new_state, result = simulate_project(state, role, "table_work", scenes, rng)
            if result.transformation:
                found = True
                break
        self.assertTrue(found, "expected at least one seed in range to land a successful type-break")
        self.assertTrue(result.transformation)
        # Legibility should have loosened relative to the untouched profile's own concentration.
        self.assertLess(new_state.persona.legibility(), pre_legibility)

    def test_a_transformation_prestige_delta_exceeds_an_ordinary_projects(self):
        state = self._legible_actor()
        role = _off_lane_role()
        transformation_delta = None
        ordinary_role = Role(
            project_id="p2", genre="drama", archetype="leading_hero", billing="lead",
            char_age=35, type_strictness=1.0, difficulty=50.0, budget_for_role=10.0,
            gatekeeper="indie_first_timer",
        )
        for seed in range(400):
            rng = random.Random(seed)
            scenes = default_scene_policy(rng)
            _, result = simulate_project(state, role, "table_work", scenes, rng)
            if result.transformation:
                transformation_delta = result.prestige_delta
                break
        self.assertIsNotNone(transformation_delta)
        ordinary_deltas = []
        for seed in range(20):
            rng = random.Random(1000 + seed)
            scenes = default_scene_policy(rng)
            _, result = simulate_project(state, ordinary_role, "table_work", scenes, rng)
            ordinary_deltas.append(result.prestige_delta)
        self.assertGreater(transformation_delta, max(ordinary_deltas))

    def test_playing_your_own_established_lane_never_flags_transformation(self):
        # The same legible actor, cast squarely in their own top genre/archetype -- nothing here
        # is a stretch, so transformation should never fire regardless of how well it's received.
        state = self._legible_actor()
        role = Role(
            project_id="p3", genre="drama", archetype="leading_hero", billing="lead",
            char_age=35, type_strictness=1.0, difficulty=50.0, budget_for_role=10.0,
            gatekeeper="indie_first_timer",
        )
        for seed in range(50):
            rng = random.Random(seed)
            scenes = default_scene_policy(rng)
            _, result = simulate_project(state, role, "table_work", scenes, rng)
            self.assertFalse(result.transformation)


if __name__ == "__main__":
    unittest.main()
