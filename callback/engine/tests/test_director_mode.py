"""simulation/_director.py and Session's directing_unlocked()/become_director()/
advance_directing() — the director career fused into the same Session/FullState as the actor,
sharing one calendar and one Standing philosophy rather than a second, parallel Session.
"""
from __future__ import annotations

import random
import unittest
from dataclasses import replace as dc_replace
from unittest.mock import patch

from callback.engine.actor.reception import ReceptionResult
from callback.engine.actor.standing import delta_prestige
from callback.engine.director.development import bankability_multiplier, greenlight_probability
from callback.engine.simulation._director import (
    DirectedReleaseSnapshot,
    advance_shoots_and_resolve,
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
        from callback.engine.core.script_notes import DIRECTOR_SCRIPT_NOTE_OPTIONS
        self.assertNotIn("your_part", DIRECTOR_SCRIPT_NOTE_OPTIONS)

    def test_choosing_a_script_note_applies_quality_immediately_and_holds_the_rest_pending(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        quality_before = state.projects[0].true_script_quality
        state = choose_director_script_note(state, 0, "whole_film", random.Random(2))
        self.assertGreater(state.projects[0].true_script_quality, quality_before)
        self.assertNotEqual(state.projects[0].pending_script_note.script_quality_delta, 0.0)

    def test_an_unknown_choice_is_a_no_op(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        same = choose_director_script_note(state, 0, "your_part", random.Random(2))
        self.assertEqual(same, state)

    def test_release_request_only_accepts_a_real_strategy(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        updated = request_director_release(state, 0, "streaming")
        self.assertEqual(updated.projects[0].pending_release_request, "streaming")
        rejected = request_director_release(state, 0, "not_a_real_strategy")
        self.assertIsNone(rejected.projects[0].pending_release_request)

    def test_marketing_push_request_sets_the_flag(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        updated = request_director_marketing_push(state, 0)
        self.assertTrue(updated.projects[0].pending_marketing_push)

    def test_starting_a_second_project_never_touches_the_first_ones_pending_choices(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        state = choose_director_script_note(state, 0, "clarity", random.Random(2))
        state = request_director_release(state, 0, "streaming")
        state = request_director_marketing_push(state, 0)
        fresh = start_development(state, "comedy", 12.0, random.Random(2))
        # §7.4 v16 — starting a second project never displaces or resets the first; project count
        # is flat-capped (MAX_PROJECTS), never gated behind Standing.
        self.assertEqual(len(fresh.projects), 2)
        self.assertEqual(fresh.projects[0].genre, "drama")
        self.assertEqual(fresh.projects[0].pending_release_request, "streaming")
        self.assertEqual(fresh.projects[1].genre, "comedy")
        self.assertIsNone(fresh.projects[1].pending_release_request)

    def test_starting_beyond_max_projects_is_a_no_op(self):
        from callback.engine.simulation._director import MAX_PROJECTS
        state = new_director_state()
        for i in range(MAX_PROJECTS):
            state = start_development(state, "drama", 12.0, random.Random(i))
        self.assertEqual(len(state.projects), MAX_PROJECTS)
        stuck = start_development(state, "comedy", 12.0, random.Random(99))
        self.assertEqual(stuck, state)


class TestDirectorPrestigeUsesAudienceScoreNotDoubledCritic(unittest.TestCase):
    def test_greenlit_film_prestige_delta_reads_audience_score_independently(self):
        # Regression test for a real bug: the greenlight resolution used to pass
        # film_critic_score into BOTH delta_prestige args, double-weighting critic reception
        # (0.11+0.26 combined) while a director's actual audience reach never factored in at all.
        # v12 — greenlighting only starts the shoot now; the actual reception (and so this delta)
        # only applies once advance_shoots_and_resolve wraps it, so the film is self-financed here
        # purely to make the greenlight itself unconditional and land in one call.
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=True)
        state, shooting_info = apply_dev_action_and_advance(
            state, 0, "rewrite", genre_demand=55.0, rng=random.Random(2), available_money=1_000_000.0,
        )
        self.assertTrue(shooting_info["greenlit"])

        fake_reception = ReceptionResult(
            project_quality=60.0, film_critic_score=80.0, audience_score=20.0,  # deliberately far apart
            budget=30.0, marketing=15.0, break_even=45.0, opening=20.0, zeitgeist=50.0, legs=2.0,
            gross=60.0, roi=1.5,
        )
        prestige_before = state.standing["prestige"]
        with patch("callback.engine.simulation._director._resolve_directed_film", return_value=(fake_reception, "wide", False, 30.0, 0.0, None)):
            new_state, resolved = advance_shoots_and_resolve(state, {}, random.Random(3))

        self.assertTrue(resolved)
        info = resolved[0]
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


class TestBankabilityMultiplier(unittest.TestCase):
    def test_breakeven_or_better_never_pays_any_penalty(self):
        self.assertEqual(bankability_multiplier(trailing_roi=1.0, budget_ask=300.0), 1.0)
        self.assertEqual(bankability_multiplier(trailing_roi=2.5, budget_ask=300.0), 1.0)

    def test_a_small_project_is_barely_touched_by_a_real_flop_streak(self):
        mult = bankability_multiplier(trailing_roi=0.2, budget_ask=5.0)
        self.assertGreater(mult, 0.95)

    def test_a_big_project_takes_a_real_but_soft_hit_from_a_flop_streak(self):
        small = bankability_multiplier(trailing_roi=0.2, budget_ask=5.0)
        big = bankability_multiplier(trailing_roi=0.2, budget_ask=280.0)
        self.assertLess(big, small)
        self.assertGreater(big, 0.75)  # a real, felt effect, never crushing

    def test_never_drops_below_the_floor_even_at_extreme_inputs(self):
        mult = bankability_multiplier(trailing_roi=0.0, budget_ask=10_000.0)
        self.assertGreaterEqual(mult, 0.45)

    def test_scales_softly_not_linearly_between_two_budget_sizes(self):
        # the whole point: doubling the budget doesn't double the penalty — it's a log curve
        mid = 1.0 - bankability_multiplier(trailing_roi=0.3, budget_ask=50.0)
        high = 1.0 - bankability_multiplier(trailing_roi=0.3, budget_ask=100.0)
        self.assertLess(high, mid * 2.0)


class TestDirectorStateBasics(unittest.TestCase):
    def test_start_development_sets_a_project_and_a_genre(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        self.assertEqual(len(state.projects), 1)
        self.assertEqual(state.projects[0].genre, "drama")
        self.assertEqual(state.projects[0].project.budget_ask, 30.0)

    def test_attach_star_raises_bankability_when_the_offer_is_accepted(self):
        # v12 — attaching is a real offer now, not a guarantee; retry across seeds until one lands
        # to confirm the accepted case still raises bankability the way it always has.
        for seed in range(20):
            state = new_director_state()
            state = start_development(state, "drama", 30.0, random.Random(seed))
            before = state.projects[0].project.attached_star_bankability
            state, info = apply_dev_action_and_advance(state, 0, "attach_star", genre_demand=55.0, rng=random.Random(seed))
            if info["greenlit"] or info["dead"]:
                continue
            if info["attachment_offer_accepted"]:
                self.assertGreater(state.projects[0].project.attached_star_bankability, before)
                return
        self.skipTest("no accepted attach offer across 20 seeds — RNG variance, not a bug")

    def test_attach_star_leaves_bankability_unchanged_when_declined(self):
        for seed in range(20):
            state = new_director_state()
            state = start_development(state, "drama", 30.0, random.Random(seed))
            before = state.projects[0].project.attached_star_bankability
            state, info = apply_dev_action_and_advance(state, 0, "attach_star", genre_demand=55.0, rng=random.Random(seed))
            if info["greenlit"] or info["dead"]:
                continue
            if not info["attachment_offer_accepted"]:
                self.assertEqual(state.projects[0].project.attached_star_bankability, before)
                return
        self.skipTest("no declined attach offer across 20 seeds — RNG variance, not a bug")

    def test_a_project_eventually_resolves_one_way_or_another(self):
        """Repeatedly applying rewrite should either greenlight, die, or keep going — never crash,
        and eventually stop being 'in development forever' within a generous attempt budget."""
        state = new_director_state()
        state = start_development(state, "drama", 12.0, random.Random(3))
        rng = random.Random(3)
        resolved = False
        for _ in range(50):
            state, info = apply_dev_action_and_advance(state, 0, "rewrite", genre_demand=55.0, rng=rng)
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
        self.assertEqual(status["projects"], [])

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


class TestDirectorAwardsCampaign(unittest.TestCase):
    """awards/ §DIRECTOR — a director's own award campaign, judged on director inputs (Vision/
    Command/Craft) against other directors, not folded into the actor pool."""

    def _snapshot(self, film_critic_score=90.0, genre="drama"):
        return DirectedReleaseSnapshot(
            genre=genre, budget_millions=20.0, release_strategy="wide", rating_band="R",
            film_critic_score=film_critic_score, audience_score=70.0, opening_millions=10.0,
            legs=1.5, roi=2.0,
        )

    def test_not_available_before_any_directed_release(self):
        session = Session(seed=20)
        session.start("conservatory", "work")
        session.become_director()
        self.assertFalse(session.director_awards_campaign_available())

    def test_available_once_a_release_clears_the_threshold(self):
        session = Session(seed=21)
        session.start("conservatory", "work")
        session.become_director()
        session._last_directed_release = self._snapshot()
        self.assertTrue(session.director_awards_campaign_available())

    def test_campaign_returns_the_director_category(self):
        session = Session(seed=22)
        session.start("conservatory", "work")
        session.become_director()
        session._last_directed_release = self._snapshot()
        result = session.run_director_awards_campaign(spend_millions=1.5)
        self.assertEqual(result["category"], "director")
        self.assertIn("won", result)
        self.assertIn("nominated", result)

    def test_a_win_moves_director_prestige_and_nothing_else(self):
        for seed in range(40):
            session = Session(seed=seed + 300)
            session.start("conservatory", "work")
            session.become_director()
            session._last_directed_release = self._snapshot()
            prestige_before = session.state.director.standing["prestige"]
            affection_before = session.state.director.standing["affection"]
            result = session.run_director_awards_campaign(spend_millions=2.0)
            if result["won"]:
                self.assertGreater(session.state.director.standing["prestige"], prestige_before)
                self.assertEqual(session.state.director.standing["affection"], affection_before)
                return
        self.skipTest("no director win landed across 40 seeds — RNG variance, not a bug")

    def test_a_campaign_is_not_available_again_off_the_same_release(self):
        # One shot per film — a director who spends several years developing the next project
        # shouldn't be able to keep re-campaigning (and re-winning) the same old release every
        # year in between, the way a stale _last_directed_release snapshot used to allow.
        session = Session(seed=23)
        session.start("conservatory", "work")
        session.become_director()
        session._last_directed_release = self._snapshot()
        self.assertTrue(session.director_awards_campaign_available())
        session.run_director_awards_campaign(spend_millions=1.5)
        self.assertFalse(session.director_awards_campaign_available())

    def test_advance_directing_leaves_the_calendar_to_end_year(self):
        session = Session(seed=14)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        start_age = session.age()
        result = session.advance_directing(0, "rewrite")
        self.assertIn("greenlit", result)
        self.assertIn("momentum", result)
        self.assertEqual(session.age(), start_age)  # advance_directing() no longer touches the calendar
        session.end_year()
        self.assertGreater(session.age(), start_age)

    def test_advance_directing_spends_a_quarter_and_refuses_a_fifth(self):
        session = Session(seed=16)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        for _ in range(4):
            result = session.advance_directing(0, "rewrite")
            self.assertNotIn("error", result)
            if result["greenlit"] or result["dead"]:
                session.start_directing_project("drama", "low")
        self.assertEqual(session.quarters_remaining_this_year(), 0)
        refused = session.advance_directing(0, "rewrite")
        self.assertIn("error", refused)
        session.end_year()
        self.assertEqual(session.quarters_remaining_this_year(), 4)

    def test_acting_and_directing_can_both_happen_in_the_same_year(self):
        session = Session(seed=20)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        start_age = session.age()

        session.advance_directing(0, "rewrite")  # directing work this year

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
        # v12 — greenlighting only starts the shoot now (director.development.quarters_for_
        # directed_film); the real, resolved film comes back from end_year() instead of from
        # advance_directing() itself, once the shoot actually wraps.
        session = Session(seed=15)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        resolved = False
        for _ in range(50):
            if session.is_over():
                break
            if not session.director_status()["projects"]:
                session.start_directing_project("drama", "low")
            if session.quarters_remaining_this_year() <= 0:
                wrapped = session.end_year()
                if wrapped:
                    result = wrapped[0]
                    self.assertIsInstance(result["critic_band"], str)
                    self.assertIsInstance(result["roi"], float)
                    resolved = True
                    break
                continue
            session.advance_directing(0, "attach_star")
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
        session.choose_director_script_note_action(0, "clarity")
        self.assertNotEqual(session.state.director.projects[0].pending_script_note.audience_delta, 0.0)

    def test_release_request_and_marketing_push_reach_the_resolved_greenlight(self):
        session = Session(seed=31)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        session.request_director_release_strategy(0, "streaming")
        session.request_director_marketing_push_action(0)

        resolved = False
        for _ in range(50):
            if not session.director_status()["projects"]:
                session.start_directing_project("drama", "low")
                session.request_director_release_strategy(0, "streaming")
                session.request_director_marketing_push_action(0)
            if session.quarters_remaining_this_year() <= 0:
                wrapped = session.end_year()
                if wrapped:
                    result = wrapped[0]
                    self.assertIn(result["requested_release"], (None, "Streaming — a flat guaranteed payout, no upside"))
                    self.assertIsInstance(result["release_overruled"], bool)
                    self.assertIsInstance(result["marketing_push_requested"], bool)
                    self.assertIsInstance(result["marketing_push_honored"], bool)
                    resolved = True
                    break
                continue
            session.advance_directing(0, "attach_star")
        self.assertTrue(resolved)

    def test_no_request_means_not_requested_or_honored(self):
        session = Session(seed=32)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        resolved = False
        for _ in range(50):
            if not session.director_status()["projects"]:
                session.start_directing_project("drama", "low")
            if session.quarters_remaining_this_year() <= 0:
                wrapped = session.end_year()
                if wrapped:
                    result = wrapped[0]
                    self.assertIsNone(result["requested_release"])
                    self.assertFalse(result["release_overruled"])
                    self.assertFalse(result["marketing_push_requested"])
                    self.assertFalse(result["marketing_push_honored"])
                    resolved = True
                    break
                continue
            session.advance_directing(0, "attach_star")
        self.assertTrue(resolved)


class TestSelfFinanceAcquisitionFlow(unittest.TestCase):
    """Self-financing is now a real two-step negotiation, not a same-year guarantee: the studio
    has to actually let the project go (free, or bought out) before it's yours, and only once it's
    yours does choosing self_finance again guarantee the film gets made."""

    def test_acquisition_year_never_greenlights_even_when_successful(self):
        state = new_director_state()
        state = start_development(state, "drama", 170.0, random.Random(9))
        state, info = apply_dev_action_and_advance(
            state, 0, "self_finance", genre_demand=55.0, rng=random.Random(1), available_money=1_000_000.0,
        )
        self.assertFalse(info["greenlit"])
        self.assertIn("self_finance_acquired", info)

    def test_cannot_afford_it_leaves_the_project_with_the_studio(self):
        found_failure = False
        for seed in range(30):
            trial_state = start_development(new_director_state(), "drama", 170.0, random.Random(9))
            trial_state, info = apply_dev_action_and_advance(
                trial_state, 0, "self_finance", genre_demand=55.0, rng=random.Random(seed), available_money=0.0,
            )
            if not info["self_finance_acquired"]:
                found_failure = True
                self.assertFalse(trial_state.projects[0].project.self_financed)
                self.assertTrue(info["self_finance_could_not_afford"] or not info["self_finance_released_free"])
                break
        self.assertTrue(found_failure)

    def test_once_acquired_the_next_self_finance_call_guarantees_a_greenlight(self):
        state = new_director_state()
        state = start_development(state, "drama", 170.0, random.Random(9))
        state, acquire_info = apply_dev_action_and_advance(
            state, 0, "self_finance", genre_demand=55.0, rng=random.Random(1), available_money=1_000_000.0,
        )
        self.assertTrue(acquire_info["self_finance_acquired"])
        self.assertTrue(state.projects[0].project.self_financed)
        # A deliberately weak package (low script quality, no attached star, low standing) that
        # would almost never clear a real studio greenlight roll — self-financing bypasses that
        # check entirely once the project is actually owned (real money still has to be there —
        # §7.4 v23's own affordability gate — so this call still needs to bring it).
        state, info = apply_dev_action_and_advance(
            state, 0, "self_finance", genre_demand=55.0, rng=random.Random(2), available_money=1_000_000.0,
        )
        self.assertTrue(info["greenlit"])
        self.assertTrue(info["self_financed"])

    def test_release_and_marketing_are_always_honored_once_self_financed(self):
        session = Session(seed=44)
        session.start("conservatory", "work")
        session.become_director()
        # §7.4 v23 — self-financing now genuinely requires the money; give this character enough
        # to actually cover it, since that's not what this test is checking.
        session.state = dc_replace(session.state, life=dc_replace(session.state.life, money=dc_replace(session.state.life.money, net_worth=1_000_000.0)))
        session.start_directing_project("drama", "low")
        session.request_director_release_strategy(0, "streaming")
        session.request_director_marketing_push_action(0)
        result = session.advance_directing(0, "self_finance")
        attempts = 0
        while not result.get("self_finance_acquired") and not result["dead"] and not result["greenlit"]:
            if session.quarters_remaining_this_year() <= 0:
                session.end_year()
            result = session.advance_directing(0, "self_finance")
            attempts += 1
            self.assertLess(attempts, 200)
        self.assertTrue(result["self_finance_acquired"])
        if session.quarters_remaining_this_year() <= 0:
            session.end_year()
        result = session.advance_directing(0, "self_finance")
        self.assertTrue(result["greenlit"])  # v12 — just started shooting; run it out to resolve
        wrapped = []
        for _ in range(20):
            wrapped = session.end_year()
            if wrapped:
                break
        self.assertTrue(wrapped)
        result = wrapped[0]
        self.assertFalse(result["release_overruled"])
        self.assertTrue(result["marketing_push_honored"])

    def test_buyout_cost_is_deducted_from_net_worth(self):
        session = Session(seed=7)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "tentpole")  # high budget -> real buyout cost, studio holds on more
        before = session.state.life.money.net_worth
        for _ in range(30):
            if session.quarters_remaining_this_year() <= 0:
                session.end_year()
            result = session.advance_directing(0, "self_finance")
            if result.get("self_finance_acquired") and result.get("self_finance_cost_paid", 0.0) > 0.0:
                self.assertLess(session.state.life.money.net_worth, before)
                return
            if result.get("self_finance_acquired"):
                return  # released free — nothing to assert about cost here
        self.skipTest("project never acquired within 30 attempts at this seed — RNG variance, not a bug")


if __name__ == "__main__":
    unittest.main()
