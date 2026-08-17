"""simulation/_director.py and Session's directing_unlocked()/become_director()/
advance_directing() — the director career fused into the same Session/FullState as the actor,
sharing one calendar and one Standing philosophy rather than a second, parallel Session.
"""
from __future__ import annotations

import random
import unittest
from unittest.mock import patch

from callback.engine.actor.reception import ReceptionResult
from callback.engine.actor.standing import delta_prestige
from callback.engine.director.development import greenlight_probability
from callback.engine.simulation._director import (
    apply_dev_action_and_advance,
    choose_director_script_note,
    new_director_state,
    request_director_marketing_push,
    request_director_release,
    start_development,
)
from callback.engine.simulation.session import Session


class TestDirectorScriptNoteReleaseAndMarketingPending(unittest.TestCase):
    def test_your_part_is_not_offered_to_a_director(self):
        from callback.engine.actor.script_notes import DIRECTOR_SCRIPT_NOTE_OPTIONS
        self.assertNotIn("your_part", DIRECTOR_SCRIPT_NOTE_OPTIONS)

    def test_choosing_a_script_note_applies_quality_immediately_and_holds_the_rest_pending(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        quality_before = state.current_true_script_quality
        state = choose_director_script_note(state, "whole_film")
        self.assertGreater(state.current_true_script_quality, quality_before)
        self.assertNotEqual(state.pending_script_note.script_quality_delta, 0.0)

    def test_an_unknown_choice_is_a_no_op(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        same = choose_director_script_note(state, "your_part")
        self.assertEqual(same, state)

    def test_release_request_only_accepts_a_real_strategy(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        updated = request_director_release(state, "streaming")
        self.assertEqual(updated.pending_release_request, "streaming")
        rejected = request_director_release(state, "not_a_real_strategy")
        self.assertIsNone(rejected.pending_release_request)

    def test_marketing_push_request_sets_the_flag(self):
        state = new_director_state()
        updated = request_director_marketing_push(state)
        self.assertTrue(updated.pending_marketing_push)

    def test_starting_a_new_project_clears_stale_pending_choices(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        state = choose_director_script_note(state, "clarity")
        state = request_director_release(state, "streaming")
        state = request_director_marketing_push(state)
        fresh = start_development(state, "comedy", 12.0, random.Random(2))
        self.assertEqual(fresh.pending_script_note.script_quality_delta, 0.0)
        self.assertIsNone(fresh.pending_release_request)
        self.assertFalse(fresh.pending_marketing_push)


class TestDirectorPrestigeUsesAudienceScoreNotDoubledCritic(unittest.TestCase):
    def test_greenlit_film_prestige_delta_reads_audience_score_independently(self):
        # Regression test for a real bug: the greenlight resolution used to pass
        # film_critic_score into BOTH delta_prestige args, double-weighting critic reception
        # (0.11+0.26 combined) while a director's actual audience reach never factored in at all.
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))

        fake_reception = ReceptionResult(
            project_quality=60.0, film_critic_score=80.0, audience_score=20.0,  # deliberately far apart
            budget=30.0, marketing=15.0, break_even=45.0, opening=20.0, zeitgeist=50.0, legs=2.0,
            gross=60.0, roi=1.5,
        )
        prestige_before = state.standing["prestige"]
        with patch("callback.engine.simulation._director.advance_quarter", return_value=(state.current_project, True)), \
             patch("callback.engine.simulation._director._resolve_directed_film", return_value=(fake_reception, "wide", False)):
            new_state, info = apply_dev_action_and_advance(state, "rewrite", genre_demand=55.0, rng=random.Random(2))

        self.assertTrue(info["greenlit"])
        actual_delta = new_state.standing["prestige"] - prestige_before
        expected_delta = delta_prestige(1.0, state.credits, fake_reception.film_critic_score, fake_reception.audience_score)
        wrong_doubled_delta = delta_prestige(1.0, state.credits, fake_reception.film_critic_score, fake_reception.film_critic_score)
        self.assertAlmostEqual(actual_delta, expected_delta, places=6)
        self.assertNotAlmostEqual(actual_delta, wrong_doubled_delta, places=6)


class TestGreenlightProbabilityIsClamped(unittest.TestCase):
    def test_never_exceeds_one_even_at_extreme_momentum(self):
        p = greenlight_probability(pkg_strength=100.0, diff=0.0, momentum=50.0)
        self.assertLessEqual(p, 1.0)

    def test_never_goes_negative_at_extreme_low_inputs(self):
        p = greenlight_probability(pkg_strength=0.0, diff=200.0, momentum=0.0)
        self.assertGreaterEqual(p, 0.0)

    def test_stays_unclamped_in_ordinary_ranges(self):
        # a realistic case shouldn't get artificially capped by the safety clamp
        p = greenlight_probability(pkg_strength=70.0, diff=60.0, momentum=1.0)
        self.assertGreater(p, 0.0)
        self.assertLess(p, 1.0)


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
    def test_directing_is_accessible_from_the_very_start_no_gate(self):
        # Real performance comes entirely from DirectorAttributes (director/attributes.py) once
        # you're in the chair — a completely separate stat block that never reads the actor's own
        # Standing — so there's nothing on the acting side to unlock first.
        session = Session(seed=10)
        session.start("conservatory", "work")
        self.assertTrue(session.directing_unlocked())
        self.assertFalse(session.is_directing())  # accessible, but not opted into yet

    def test_become_director_succeeds_immediately_from_a_fresh_session(self):
        session = Session(seed=11)
        session.start("conservatory", "work")
        msg = session.become_director()
        self.assertIn("step behind the camera", msg.lower())
        self.assertTrue(session.is_directing())

    def test_becoming_director_twice_is_a_no_op_message(self):
        session = Session(seed=12)
        session.start("conservatory", "work")
        session.become_director()
        msg = session.become_director()
        self.assertIn("already directing", msg.lower())

    def test_director_status_is_plain_data(self):
        session = Session(seed=13)
        session.start("conservatory", "work")
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

    def test_advance_directing_leaves_the_calendar_to_end_year(self):
        session = Session(seed=14)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        start_age = session.age()
        result = session.advance_directing("rewrite")
        self.assertIn("greenlit", result)
        self.assertIn("momentum", result)
        self.assertEqual(session.age(), start_age)  # advance_directing() no longer touches the calendar
        session.end_year()
        self.assertGreater(session.age(), start_age)

    def test_acting_and_directing_can_both_happen_in_the_same_year(self):
        session = Session(seed=20)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        start_age = session.age()

        session.advance_directing("rewrite")  # directing work this year

        board = session.offer_board()
        available = [o for o in board if o["available"]]
        if available:  # RNG-dependent; only meaningful when an offer actually came through
            session.accept(available[0]["index"])
            session.choose_deal(False)
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            session.choose_release("wide")  # acting work the SAME year

        session.end_year()  # the calendar advances exactly once for both
        self.assertEqual(session.age(), start_age + 1)

    def test_a_directed_project_can_eventually_greenlight_and_resolve(self):
        session = Session(seed=15)
        session.start("conservatory", "work")
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


class TestSessionDirectorCreativeOptions(unittest.TestCase):
    def test_script_note_options_exposed_and_settable(self):
        session = Session(seed=30)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        keys = [k for k, _ in session.director_script_note_options()]
        self.assertIn("clarity", keys)
        self.assertNotIn("your_part", keys)
        session.choose_director_script_note_action("clarity")
        self.assertNotEqual(session.state.director.pending_script_note.audience_delta, 0.0)

    def test_release_request_and_marketing_push_reach_the_resolved_greenlight(self):
        session = Session(seed=31)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        session.request_director_release_strategy("streaming")
        session.request_director_marketing_push_action()

        resolved = False
        for _ in range(50):
            if not session.director_status()["in_development"]:
                session.start_directing_project("drama", "low")
                session.request_director_release_strategy("streaming")
                session.request_director_marketing_push_action()
            result = session.advance_directing("attach_star")
            if result["greenlit"]:
                self.assertIn(result["requested_release"], (None, "Streaming — a flat guaranteed payout, no upside"))
                self.assertIsInstance(result["release_overruled"], bool)
                self.assertIsInstance(result["marketing_push_requested"], bool)
                self.assertIsInstance(result["marketing_push_honored"], bool)
                resolved = True
                break
        self.assertTrue(resolved)

    def test_no_request_means_not_requested_or_honored(self):
        session = Session(seed=32)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        resolved = False
        for _ in range(50):
            if not session.director_status()["in_development"]:
                session.start_directing_project("drama", "low")
            result = session.advance_directing("attach_star")
            if result["greenlit"]:
                self.assertIsNone(result["requested_release"])
                self.assertFalse(result["release_overruled"])
                self.assertFalse(result["marketing_push_requested"])
                self.assertFalse(result["marketing_push_honored"])
                resolved = True
                break
        self.assertTrue(resolved)


if __name__ == "__main__":
    unittest.main()
