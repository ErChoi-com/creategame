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
