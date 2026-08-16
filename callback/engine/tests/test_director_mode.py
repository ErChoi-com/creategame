"""simulation/_director.py and Session's directing_unlocked()/become_director()/
advance_directing() — the director career fused into the same Session/FullState as the actor,
sharing one calendar and one Standing philosophy rather than a second, parallel Session.
"""
from __future__ import annotations

import random
import unittest
from dataclasses import replace

from callback.engine.simulation._director import (
    DIRECTOR_UNLOCK_MIN_CREDITS,
    DIRECTOR_UNLOCK_PRESTIGE,
    apply_dev_action_and_advance,
    new_director_state,
    start_development,
)
from callback.engine.simulation.session import Session


def _unlock_directing(session: Session) -> None:
    standing = session.state.actor.standing.copy()
    standing.add("prestige", DIRECTOR_UNLOCK_PRESTIGE + 5.0)
    session.state = replace(session.state, actor=replace(
        session.state.actor, standing=standing, credits=DIRECTOR_UNLOCK_MIN_CREDITS + 1,
    ))


class TestDirectorStateBasics(unittest.TestCase):
    def test_start_development_sets_a_project_and_a_genre(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        self.assertIsNotNone(state.current_project)
        self.assertEqual(state.current_genre, "drama")
        self.assertEqual(state.current_project.budget_ask, 30.0)

    def test_attach_star_raises_bankability(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(2))
        before = state.current_project.attached_star_bankability
        state, info = apply_dev_action_and_advance(state, "attach_star", genre_demand=55.0, rng=random.Random(2))
        if not info["greenlit"] and not info["dead"]:
            self.assertGreater(state.current_project.attached_star_bankability, before)

    def test_a_project_eventually_resolves_one_way_or_another(self):
        """Repeatedly applying rewrite should either greenlight, die, or keep going — never crash,
        and eventually stop being 'in development forever' within a generous attempt budget."""
        state = new_director_state()
        state = start_development(state, "drama", 12.0, random.Random(3))
        rng = random.Random(3)
        resolved = False
        for _ in range(50):
            state, info = apply_dev_action_and_advance(state, "rewrite", genre_demand=55.0, rng=rng)
            if info["greenlit"] or info["dead"]:
                resolved = True
                break
        self.assertTrue(resolved)


class TestSessionDirectorIntegration(unittest.TestCase):
    def test_directing_locked_by_default(self):
        session = Session(seed=10)
        session.start("conservatory", "work")
        self.assertFalse(session.directing_unlocked())
        self.assertFalse(session.is_directing())

    def test_become_director_requires_unlock(self):
        session = Session(seed=11)
        session.start("conservatory", "work")
        msg = session.become_director()
        self.assertIn("weight in the room", msg)
        self.assertFalse(session.is_directing())

    def test_become_director_succeeds_once_unlocked(self):
        session = Session(seed=12)
        session.start("conservatory", "work")
        _unlock_directing(session)
        self.assertTrue(session.directing_unlocked())
        msg = session.become_director()
        self.assertIn("step behind the camera", msg.lower())
        self.assertTrue(session.is_directing())

    def test_director_status_is_plain_data(self):
        session = Session(seed=13)
        session.start("conservatory", "work")
        _unlock_directing(session)
        session.become_director()
        status = session.director_status()
        self.assertIsInstance(status["credits"], int)
        self.assertIsInstance(status["standing"], str)
        self.assertFalse(status["in_development"])

    def test_directing_options_are_plain_tuples(self):
        for key, label in Session.director_genre_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)
        for key, label in Session.director_budget_tier_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)
        for key, label in Session.director_dev_action_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)

    def test_advance_directing_advances_the_shared_calendar(self):
        session = Session(seed=14)
        session.start("conservatory", "work")
        _unlock_directing(session)
        session.become_director()
        session.start_directing_project("drama", "low")
        start_age = session.age()
        result = session.advance_directing("rewrite")
        self.assertIn("greenlit", result)
        self.assertIn("momentum", result)
        self.assertGreater(session.age(), start_age)

    def test_a_directed_project_can_eventually_greenlight_and_resolve(self):
        session = Session(seed=15)
        session.start("conservatory", "work")
        _unlock_directing(session)
        session.become_director()
        session.start_directing_project("drama", "low")
        resolved = False
        for _ in range(50):
            if session.is_over():
                break
            if not session.director_status()["in_development"]:
                session.start_directing_project("drama", "low")
            result = session.advance_directing("attach_star")
            if result["greenlit"]:
                self.assertIsInstance(result["critic_band"], str)
                self.assertIsInstance(result["roi"], float)
                resolved = True
                break
        self.assertTrue(resolved)


if __name__ == "__main__":
    unittest.main()
