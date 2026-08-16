"""simulation/session.py — the player-facing façade. Every assertion here checks that Session
returns plain data (no engine types leak across the boundary) and that the previously-unreachable
systems (Rolodex interactions, Leverage's agent tier/Disappear, Awards) are now reachable.
"""
from __future__ import annotations

import unittest

from callback.engine.simulation.session import Session


def _play_one_year(session: Session, max_attempts: int = 60) -> dict | None:
    """Keeps declining until an offer actually comes through, then plays it minimally. Returns
    the release summary, or None if the run ended (age cap) before anything came through."""
    for _ in range(max_attempts):
        if session.is_over():
            return None
        offer = session.roll_offer()
        if not offer["available"]:
            session.decline()
            continue
        session.accept()
        session.choose_deal(want_approvals=False)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        return session.choose_release("wide")
    return None


class TestCharacterCreation(unittest.TestCase):
    def test_background_and_ambition_options_are_plain_data(self):
        session = Session(seed=1)
        for key, name, tagline in session.background_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(name, str)
            self.assertIsInstance(tagline, str)
        for key, name in session.ambition_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(name, str)

    def test_start_returns_a_string_and_initializes_state(self):
        session = Session(seed=2)
        msg = session.start("conservatory", "work")
        self.assertIsInstance(msg, str)
        self.assertEqual(session.age(), 22)
        self.assertEqual(session.ambition, "The Work")

    def test_regional_stage_starts_older(self):
        session = Session(seed=3)
        session.start("regional_stage", "work")
        self.assertEqual(session.age(), 33)


class TestOfferBoardTypes(unittest.TestCase):
    def test_roll_offer_returns_plain_dict(self):
        session = Session(seed=4)
        session.start("conservatory", "work")
        offer = session.roll_offer()
        self.assertIsInstance(offer, dict)
        self.assertIsInstance(offer["genre"], str)
        self.assertIsInstance(offer["billing"], str)
        self.assertIsInstance(offer["budget_millions"], float)
        self.assertIsInstance(offer["available"], bool)

    def test_accept_without_availability_raises(self):
        session = Session(seed=5)
        session.start("conservatory", "work")
        # find a year where the offer is NOT available, to test the guard
        for _ in range(30):
            offer = session.roll_offer()
            if not offer["available"]:
                with self.assertRaises(ValueError):
                    session.accept()
                return
            session.accept()
            session.choose_deal(False)
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            session.choose_release("wide")
        self.skipTest("every offer in range came through — statistically unlikely, not a failure")

    def test_decline_returns_plain_dict_and_advances_age(self):
        session = Session(seed=6)
        session.start("conservatory", "work")
        start_age = session.age()
        offer = session.roll_offer()
        while offer["available"]:
            session.accept()
            session.choose_deal(False)
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            session.choose_release("wide")
            offer = session.roll_offer()
        result = session.decline()
        self.assertIsInstance(result, dict)
        self.assertIsInstance(result["roi_band"], str)
        self.assertGreater(session.age(), start_age)


class TestFullProjectFlow(unittest.TestCase):
    def test_a_played_project_returns_a_plain_summary(self):
        session = Session(seed=7)
        session.start("conservatory", "work")
        summary = _play_one_year(session)
        if summary is None:
            self.skipTest("no offer came through in the attempt budget — RNG variance, not a bug")
        self.assertIsInstance(summary["performance_band"], str)
        self.assertIsInstance(summary["critic_score"], int)
        self.assertIsInstance(summary["gross_millions"], float)

    def test_release_options_are_plain_tuples(self):
        for key, label in Session.release_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)


def _get_to_prep(session: Session, max_attempts: int = 60) -> bool:
    """Advances until an offer comes through and is accepted, stopping right after the Deal.
    Returns False if the run ended before anything came through (RNG variance)."""
    for _ in range(max_attempts):
        if session.is_over():
            return False
        offer = session.roll_offer()
        if not offer["available"]:
            session.decline()
            continue
        session.accept()
        return True
    return False


class TestScriptNotes(unittest.TestCase):
    def test_unavailable_without_script_approval(self):
        session = Session(seed=20)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(want_approvals=False)
        self.assertFalse(session.script_notes_available())

    def test_options_are_plain_tuples(self):
        for key, label in Session.script_note_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)

    def test_choosing_a_note_does_not_crash_the_project(self):
        session = Session(seed=21)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(want_approvals=True)  # may or may not grant approvals depending on Standing
        if session.script_notes_available():
            session.choose_script_note("whole_film")
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertIsInstance(summary["performance_band"], str)


class TestSceneOrientation(unittest.TestCase):
    def test_orientation_options_are_plain_tuples(self):
        for key, label in Session.orientation_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)

    def test_generous_orientation_credits_the_costar_a_favour(self):
        session = Session(seed=22)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(want_approvals=False)
        costars = session.costar_options()
        self.assertTrue(costars)
        costar_id = costars[0]["id"]
        session.choose_orientation(costar_id, "generous")
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        session.choose_release("wide")
        self.assertGreater(session.state.leverage.favours.balance(costar_id), 0)


class TestDirectorRequest(unittest.TestCase):
    def test_available_directors_returns_plain_dicts(self):
        session = Session(seed=23)
        session.start("conservatory", "work")
        for d in session.available_directors():
            self.assertIsInstance(d["id"], str)
            self.assertIsInstance(d["favour_balance"], int)

    def test_request_fails_without_enough_favours(self):
        session = Session(seed=24)
        session.start("conservatory", "work")
        directors = session.available_directors()
        self.assertTrue(directors)
        result = session.request_director(directors[0]["id"])
        self.assertIn("don't owe you enough", result)

    def test_request_succeeds_once_favours_are_credited(self):
        from dataclasses import replace
        session = Session(seed=25)
        session.start("conservatory", "work")
        director_id = session.available_directors()[0]["id"]
        favours = session.state.leverage.favours.credit(director_id, 5)
        session.state = replace(session.state, leverage=replace(session.state.leverage, favours=favours))
        result = session.request_director(director_id)
        self.assertIn("directing this one", result)
        self.assertEqual(session.state.leverage.favours.balance(director_id), 3)  # 5 - cost of 2


class TestRolodexAndLeverageReachable(unittest.TestCase):
    def test_rolodex_summary_and_interact_are_reachable(self):
        session = Session(seed=8)
        session.start("conservatory", "work")
        summary = session.rolodex_summary()
        self.assertEqual(len(summary), 8)
        npc_id = summary[0]["id"]
        result = session.interact(npc_id, "check_in")
        self.assertIsInstance(result, str)

    def test_leverage_status_and_agent_tier_progression_are_reachable(self):
        session = Session(seed=9)
        session.start("conservatory", "work")
        status = session.leverage_status()
        self.assertEqual(status["agent_tier"], "unrepresented")
        message = session.try_advance_agent_tier()
        self.assertIsInstance(message, str)

    def test_disappear_is_reachable_and_advances_the_year(self):
        session = Session(seed=10)
        session.start("conservatory", "work")
        start_age = session.age()
        message = session.disappear()
        self.assertIsInstance(message, str)
        self.assertGreater(session.age(), start_age)
        self.assertGreater(session.leverage_status()["scarcity"], 0)

    def test_trades_is_reachable(self):
        session = Session(seed=11)
        session.start("conservatory", "work")
        digest = session.trades()
        self.assertIsInstance(digest, list)
        self.assertTrue(all(isinstance(line, str) for line in digest))


class TestAwardsReachable(unittest.TestCase):
    def test_no_campaign_available_before_any_project(self):
        session = Session(seed=12)
        session.start("conservatory", "work")
        self.assertFalse(session.awards_campaign_available())


class TestObituary(unittest.TestCase):
    def test_obituary_summary_is_plain_data(self):
        session = Session(seed=13)
        session.start("conservatory", "work")
        for _ in range(10):
            if session.is_over():
                break
            offer = session.roll_offer()
            if offer["available"]:
                session.accept()
                session.choose_deal(False)
                session.choose_prep("table_work")
                for _ in range(3):
                    session.play_scene({d: "with" for d, _ in session.dial_options()})
                session.choose_release("wide")
            else:
                session.decline()
        summary = session.obituary_summary()
        self.assertIsInstance(summary["credits"], int)
        self.assertIsInstance(summary["declined"], list)


if __name__ == "__main__":
    unittest.main()
