"""simulation/full_career.py — the integrated loop wiring actor/rolodex/leverage/life/world."""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import offer_probability, resolve_casting_path
from callback.engine.simulation.career import default_scene_policy
from callback.engine.simulation.full_career import (
    accept_and_play,
    advance_between_years,
    decline_and_resolve,
    new_full_state,
    obituary,
    offer_this_year,
    utility_for,
)


def _run_years(rng: random.Random, years: int):
    state = new_full_state(rng, start_age=22)
    for _ in range(years):
        role = offer_this_year(state, rng)
        u = utility_for(state, role)
        path = resolve_casting_path(u, role)
        cast = path == "direct_offer" or rng.random() < offer_probability(u, role.difficulty)
        if cast:
            scenes = default_scene_policy(rng)
            state, _ = accept_and_play(state, role, "table_work", scenes, rng)
            state = advance_between_years(state, rng, worked_this_year=True, billing=role.billing)
        else:
            state = decline_and_resolve(state, role, rng)
            state = advance_between_years(state, rng, worked_this_year=False)
    return state


class TestFullCareerIntegration(unittest.TestCase):
    def test_age_advances_every_year(self):
        state = _run_years(random.Random(1), 20)
        self.assertEqual(state.actor.age, 42)


class TestAgeismVolumeCurve(unittest.TestCase):
    """actor.aging.role_volume_multiplier — real and documented (§4.9) but never actually
    consumed anywhere before this pass; wired into offer_this_year for the first time here."""

    def test_an_old_actor_gets_far_fewer_ingenue_romantic_lane_offers_than_a_young_one(self):
        from dataclasses import replace
        from callback.engine.actor.offers import lane_for_role
        seed_rng = random.Random(50)
        young_state = new_full_state(seed_rng, start_age=25)
        old_state = replace(young_state, actor=replace(young_state.actor, age=70))

        def count_lane(state, lane, trials=300):
            rng = random.Random(99)
            return sum(
                1 for _ in range(trials)
                if not (role := offer_this_year(state, rng)).is_animation and lane_for_role(role) == lane
            )

        young_count = count_lane(young_state, "ingenue_romantic")
        old_count = count_lane(old_state, "ingenue_romantic")
        self.assertGreater(young_count, old_count)

    def test_exhausting_rerolls_at_a_zeroed_out_lane_falls_back_to_a_real_animated_offer(self):
        from dataclasses import replace
        state = new_full_state(random.Random(51), start_age=25)
        very_old_state = replace(state, actor=replace(state.actor, age=90))
        rng = random.Random(7)
        saw_animation = False
        for _ in range(200):
            role = offer_this_year(very_old_state, rng)
            if role.is_animation:
                saw_animation = True
        self.assertTrue(saw_animation)

    def test_declined_roles_accumulate(self):
        state = _run_years(random.Random(2), 20)
        self.assertGreater(len(state.declined), 0)

    def test_genre_heat_is_populated_from_background_films(self):
        # A >2.5x-ROI "hit" is rare per project, so a short run can legitimately accumulate none —
        # run enough years/seeds that at least one genuinely should have happened somewhere.
        any_heat = False
        for seed in range(30):
            state = _run_years(random.Random(seed), 25)
            self.assertTrue(all(v >= 0 for v in state.genre_heat.values()))
            any_heat = any_heat or len(state.genre_heat) > 0
        self.assertTrue(any_heat)

    def test_rolodex_stays_at_eight_tracked(self):
        state = _run_years(random.Random(4), 15)
        self.assertEqual(len(state.rolodex.tracked_ids), 8)

    def test_obituary_reflects_full_history(self):
        state = _run_years(random.Random(5), 25)
        ob = obituary(state)
        self.assertEqual(len(ob.filmography), len(state.filmography))
        self.assertEqual(len(ob.declined), len(state.declined))

    def test_money_and_standing_never_produce_nan_or_none(self):
        state = _run_years(random.Random(6), 30)
        self.assertIsNotNone(state.life.money.net_worth)
        for v in state.actor.standing.as_dict().values():
            self.assertTrue(0.0 <= v <= 100.0)


if __name__ == "__main__":
    unittest.main()
