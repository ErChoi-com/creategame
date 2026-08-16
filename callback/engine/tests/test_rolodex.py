"""rolodex/ behaviour: tracking, relationship-state transitions, interactions, CastingResolution."""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import Role
from callback.engine.rolodex import interactions
from callback.engine.rolodex.casting import resolve_declined_role
from callback.engine.rolodex.npc import ALLY, ESTRANGED, FAMILIAR, STRANGER
from callback.engine.rolodex.rolodex import (
    apply_affinity_grudge,
    new_rolodex,
    recompute_tracked,
    register_collision,
    register_contact,
    rivals,
)


class TestRolodexTracking(unittest.TestCase):
    def test_new_rolodex_has_background_size(self):
        r = new_rolodex(random.Random(1), size=40)
        self.assertEqual(len(r.npcs), 40)
        self.assertEqual(r.tracked_ids, ())

    def test_recompute_tracked_picks_eight(self):
        rng = random.Random(2)
        r = new_rolodex(rng, size=40)
        npc_id = next(iter(r.npcs))
        r = register_contact(r, npc_id, year=2040, shared_project=True)
        r = apply_affinity_grudge(r, npc_id, affinity_delta=50)
        r = recompute_tracked(r, current_year=2040)
        self.assertEqual(len(r.tracked_ids), 8)
        self.assertIn(npc_id, r.tracked_ids)  # highest-contact NPC should make the cut


class TestRelationshipArc(unittest.TestCase):
    def test_stranger_becomes_familiar_on_contact(self):
        r = new_rolodex(random.Random(3), size=5)
        npc_id = next(iter(r.npcs))
        self.assertEqual(r.npcs[npc_id].relationship_state, STRANGER)
        r = register_contact(r, npc_id, year=2040, shared_project=True)
        self.assertEqual(r.npcs[npc_id].relationship_state, FAMILIAR)

    def test_high_affinity_becomes_ally(self):
        r = new_rolodex(random.Random(4), size=5)
        npc_id = next(iter(r.npcs))
        r = apply_affinity_grudge(r, npc_id, affinity_delta=60)
        self.assertEqual(r.npcs[npc_id].relationship_state, ALLY)

    def test_high_grudge_becomes_estranged_even_with_high_affinity(self):
        r = new_rolodex(random.Random(5), size=5)
        npc_id = next(iter(r.npcs))
        r = apply_affinity_grudge(r, npc_id, affinity_delta=80, grudge_delta=50)
        self.assertEqual(r.npcs[npc_id].relationship_state, ESTRANGED)

    def test_collision_threshold_marks_rival(self):
        r = new_rolodex(random.Random(6), size=5)
        npc_id = next(iter(r.npcs))
        for _ in range(3):
            r = register_collision(r, npc_id)
        self.assertEqual(r.npcs[npc_id].relationship_state, "rival")

    def test_rivals_surfaces_only_tracked_rivals(self):
        from dataclasses import replace as _replace
        r = new_rolodex(random.Random(6), size=5)
        npc_id = next(iter(r.npcs))
        for _ in range(3):
            r = register_collision(r, npc_id)
        r = _replace(r, tracked_ids=(npc_id,))
        self.assertEqual([n.npc_id for n in rivals(r)], [npc_id])


class TestInteractions(unittest.TestCase):
    def test_check_in_raises_affinity(self):
        r = new_rolodex(random.Random(7), size=5)
        npc = r.npcs[next(iter(r.npcs))]
        updated = interactions.check_in(npc, year=2040)
        self.assertGreater(updated.affinity, npc.affinity)
        self.assertEqual(updated.last_contact_year, 2040)

    def test_read_agenda_served_beats_ignored(self):
        r = new_rolodex(random.Random(8), size=5)
        npc = r.npcs[next(iter(r.npcs))]
        served = interactions.read_agenda_and_act(npc, served_agenda=True, year=2040)
        ignored = interactions.read_agenda_and_act(npc, served_agenda=False, year=2040)
        self.assertGreater(served.affinity, ignored.affinity)


class TestCastingResolution(unittest.TestCase):
    def test_resolves_to_a_real_reception(self):
        rng = random.Random(9)
        rolodex = new_rolodex(rng, size=20)
        role = Role(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=20,
                    gatekeeper="indie_first_timer")
        new_rd, result = resolve_declined_role(role, rolodex, year=2040, rng=rng)
        self.assertIsNotNone(result.filled_by)
        self.assertGreaterEqual(result.reception.roi, 0.0)
        self.assertTrue(0.0 <= result.reception.film_critic_score <= 100.0)


if __name__ == "__main__":
    unittest.main()
