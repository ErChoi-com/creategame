"""world/ behaviour: guild eligibility/health plan, strikes, genre cycles, the trades digest."""
from __future__ import annotations

import random
import unittest

from callback.engine.rolodex.rolodex import new_rolodex
from callback.engine.world.genre_cycle import accumulate_heat, decay_all, genre_demand
from callback.engine.world.guild import GuildState, add_residual_stream, has_health_plan, is_eligible
from callback.engine.world.strikes import CROSS, HOLD, StrikeState, advance_grievance, resolve_strike_choice
from callback.engine.world.trades import generate_digest


class TestGuild(unittest.TestCase):
    def test_eligibility_at_three_credits(self):
        self.assertFalse(is_eligible(2))
        self.assertTrue(is_eligible(3))

    def test_health_plan_gate(self):
        self.assertFalse(has_health_plan(0.01))
        self.assertTrue(has_health_plan(0.03))

    def test_residuals_accumulate_only_above_roi_threshold(self):
        state = GuildState()
        state = add_residual_stream(state, project_roi=0.8, project_budget_millions=30)
        self.assertEqual(state.residual_streams, 0.0)
        state = add_residual_stream(state, project_roi=1.5, project_budget_millions=30)
        self.assertGreater(state.residual_streams, 0.0)


class TestStrikes(unittest.TestCase):
    def test_grievance_eventually_triggers_a_strike(self):
        rng = random.Random(1)
        state = StrikeState()
        for _ in range(100):
            state = advance_grievance(state, rng)
            if state.active:
                break
        self.assertTrue(state.active)

    def test_crossing_costs_more_affinity_than_holding_the_line(self):
        rng = random.Random(2)
        rolodex = new_rolodex(rng, size=10)
        held = resolve_strike_choice(rolodex, HOLD, rng)
        crossed = resolve_strike_choice(rolodex, CROSS, rng)
        held_affinity = sum(n.affinity for n in held.npcs.values())
        crossed_affinity = sum(n.affinity for n in crossed.npcs.values())
        self.assertGreater(held_affinity, crossed_affinity)


class TestGenreCycle(unittest.TestCase):
    def test_high_roi_films_accumulate_heat(self):
        heat = accumulate_heat({}, "horror", roi=3.0)
        self.assertGreater(heat["horror"], 0)

    def test_low_roi_does_not_accumulate(self):
        heat = accumulate_heat({}, "horror", roi=1.0)
        self.assertEqual(heat.get("horror", 0.0), 0.0)

    def test_heat_decays(self):
        heat = {"horror": 100.0}
        decayed = decay_all(heat)
        self.assertLess(decayed["horror"], 100.0)

    def test_genre_demand_reads_heat(self):
        self.assertGreater(genre_demand({"horror": 100.0}, "horror"), genre_demand({}, "horror"))


class TestTrades(unittest.TestCase):
    def test_digest_never_exceeds_five_lines(self):
        rng = random.Random(3)
        rolodex = new_rolodex(rng, size=10)
        heat = {"horror": 100.0, "comedy": 90.0, "action": 80.0}
        digest = generate_digest(heat, rolodex, all_genres=("drama", "horror", "comedy", "action"))
        self.assertLessEqual(len(digest), 5)
        self.assertGreaterEqual(len(digest), 1)

    def test_quiet_year_still_produces_a_line(self):
        rng = random.Random(4)
        rolodex = new_rolodex(rng, size=5)
        digest = generate_digest({}, rolodex, all_genres=("drama",))
        self.assertEqual(len(digest), 1)


if __name__ == "__main__":
    unittest.main()
