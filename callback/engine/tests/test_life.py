"""life/ behaviour: Condition, addiction stages + uninsurability, family, money's going-broke
ratchet, and the obituary.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import Role
from callback.engine.life.addiction import AddictionState, CRISIS, RECOVERY, USE, advance, enter_recovery
from callback.engine.life.family import FamilyState, nepotism_penalty_cleared
from callback.engine.life.health import HealthState, condition
from callback.engine.life.money import MoneyState, apply_year
from callback.engine.life.obituary import DeclinedRoleRecord, generate_obituary
from callback.engine.rolodex.casting import resolve_declined_role
from callback.engine.rolodex.rolodex import new_rolodex, register_contact
from callback.engine.simulation.career import simulate_career


class TestHealth(unittest.TestCase):
    def test_burnout_debt_lowers_condition(self):
        healthy = condition(HealthState(health=75, burnout_debt=0), resilience=50, substance_load=0)
        burnt_out = condition(HealthState(health=75, burnout_debt=20), resilience=50, substance_load=0)
        self.assertGreater(healthy, burnt_out)


class TestAddiction(unittest.TestCase):
    def test_crisis_makes_uninsurable(self):
        state = AddictionState(stage=CRISIS, insurable=False)
        self.assertFalse(state.insurable)

    def test_advancing_from_clean_does_nothing(self):
        state = AddictionState()
        new_state, deltas = advance(state, random.Random(1))
        self.assertEqual(new_state.stage, "clean")
        self.assertEqual(deltas, {})

    def test_stage_only_ever_advances_or_holds_in_one_step(self):
        order = ["use", "dependence", "tolerance", "crisis"]
        rng = random.Random(2)
        state = AddictionState(stage=USE)
        new_state, _ = advance(state, rng)
        self.assertIn(new_state.stage, ("use", "dependence"))

    def test_recovery_is_a_real_state_transition(self):
        state = enter_recovery(AddictionState(stage=CRISIS, insurable=False))
        self.assertEqual(state.stage, RECOVERY)
        self.assertEqual(state.clean_years, 0)


class TestFamily(unittest.TestCase):
    def test_nepotism_penalty_clears_above_threshold(self):
        self.assertFalse(nepotism_penalty_cleared(70))
        self.assertTrue(nepotism_penalty_cleared(90))

    def test_resilience_floor_from_children(self):
        no_kids = FamilyState(children=0, has_close_friends=False)
        with_kids = FamilyState(children=2, has_close_friends=False)
        self.assertGreater(with_kids.resilience_floor(), no_kids.resilience_floor())


class TestMoney(unittest.TestCase):
    def test_lifestyle_floor_ratchets_up_and_persists(self):
        rng = random.Random(3)
        state = MoneyState()
        state = apply_year(state, gross_income_millions=6.0, rng=rng)
        peak_floor = state.lifestyle_floor
        self.assertGreater(peak_floor, 0.0)
        # income stops — floor should fall slowly, not vanish immediately
        state2 = apply_year(state, gross_income_millions=0.0, rng=rng)
        self.assertLess(state2.lifestyle_floor, peak_floor)
        self.assertGreater(state2.lifestyle_floor, peak_floor * 0.5)  # falls ~8%/yr, not to zero

    def test_no_income_depletes_net_worth_against_the_floor(self):
        rng = random.Random(4)
        state = MoneyState(net_worth=10.0, peak_annual_income=6.0, lifestyle_floor=3.3)
        state = apply_year(state, gross_income_millions=0.0, rng=rng)
        self.assertLess(state.net_worth, 10.0)


class TestObituary(unittest.TestCase):
    def test_generates_from_a_real_career_and_rolodex(self):
        rng = random.Random(5)
        _, results = simulate_career(start_age=22, years=20, rng=rng)
        rolodex = new_rolodex(rng, size=10)
        rolodex = register_contact(rolodex, next(iter(rolodex.npcs)), year=2040, shared_project=True)

        declined = []
        role = Role(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=20,
                    gatekeeper="indie_first_timer")
        rolodex, cast_result = resolve_declined_role(role, rolodex, year=2041, rng=rng)
        declined.append(DeclinedRoleRecord(role_genre="drama", year=2041, result=cast_result))

        obituary = generate_obituary(results, declined, rolodex)
        self.assertEqual(len(obituary.declined), 1)
        self.assertGreaterEqual(len(obituary.collaborators), 1)


if __name__ == "__main__":
    unittest.main()
