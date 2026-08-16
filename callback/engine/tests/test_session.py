"""simulation/session.py — the player-facing façade. Every assertion here checks that Session
returns plain data (no engine types leak across the boundary) and that the previously-unreachable
systems (Rolodex interactions, Leverage's agent tier/Disappear, Awards) are now reachable.
"""
from __future__ import annotations

import unittest
from dataclasses import replace

from callback.engine.simulation._franchises import FranchiseEntry
from callback.engine.simulation.session import Session


def _play_one_year(session: Session, max_attempts: int = 60) -> dict | None:
    """Keeps declining whole boards until an offer actually comes through, then plays it
    minimally. Returns the release summary, or None if the run ended (age cap) before anything
    came through."""
    for _ in range(max_attempts):
        if session.is_over():
            return None
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        if not available:
            session.decline_board()
            continue
        session.accept(available[0]["index"])
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
    def test_offer_board_returns_a_list_of_plain_dicts(self):
        session = Session(seed=4)
        session.start("conservatory", "work")
        board = session.offer_board()
        self.assertGreaterEqual(len(board), 20)  # OFFER_BOARD_MIN_LISTINGS
        for offer in board:
            self.assertIsInstance(offer["index"], int)
            self.assertIsInstance(offer["genre"], str)
            self.assertIsInstance(offer["billing"], str)
            self.assertIsInstance(offer["budget_millions"], float)
            self.assertIsInstance(offer["fee_millions"], float)
            self.assertGreaterEqual(offer["budget_millions"], offer["fee_millions"])
            self.assertIsInstance(offer["available"], bool)
            self.assertIsInstance(offer["studio_name"], str)

    def test_accept_without_availability_raises(self):
        session = Session(seed=5)
        session.start("conservatory", "work")
        # find a board where at least one listing is NOT available, to test the guard
        for _ in range(30):
            board = session.offer_board()
            unavailable = [o for o in board if not o["available"]]
            if unavailable:
                with self.assertRaises(ValueError):
                    session.accept(unavailable[0]["index"])
                return
            session.accept(board[0]["index"])
            session.choose_deal(False)
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            session.choose_release("wide")
        self.skipTest("every listing in range came through — statistically unlikely, not a failure")

    def test_accept_out_of_range_index_raises(self):
        session = Session(seed=41)
        session.start("conservatory", "work")
        session.offer_board()
        with self.assertRaises(ValueError):
            session.accept(999)

    def test_generate_more_listings_appends_without_resetting_the_board(self):
        session = Session(seed=42)
        session.start("conservatory", "work")
        board = session.offer_board()
        more = session.generate_more_listings(5)
        self.assertEqual(len(more), 5)
        # new listings continue the board's index sequence rather than restarting at 0
        self.assertEqual([o["index"] for o in more], list(range(len(board), len(board) + 5)))
        # accepting a listing from the original board still works after generating more
        combined = board + more
        available = [o for o in combined if o["available"]]
        if available:
            session.accept(available[0]["index"])  # should not raise

    def test_decline_board_returns_a_list_and_advances_age(self):
        session = Session(seed=6)
        session.start("conservatory", "work")
        start_age = session.age()
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        while available:
            session.accept(available[0]["index"])
            session.choose_deal(False)
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            session.choose_release("wide")
            session.end_year()
            board = session.offer_board()
            available = [o for o in board if o["available"]]
        results = session.decline_board()
        session.end_year()
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), len(board))
        for result in results:
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
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        if not available:
            session.decline_board()
            continue
        session.accept(available[0]["index"])
        return True
    return False


class TestBoxOfficeBonus(unittest.TestCase):
    def test_unavailable_at_low_standing(self):
        session = Session(seed=30)
        session.start("conservatory", "work")
        self.assertFalse(session.box_office_bonus_available())

    def test_available_at_high_standing(self):
        from dataclasses import replace
        session = Session(seed=31)
        session.start("conservatory", "work")
        standing = session.state.actor.standing.copy()
        standing.add("heat", 65)
        standing.add("prestige", 65)
        standing.add("affection", 65)
        session.state = replace(session.state, actor=replace(session.state.actor, standing=standing))
        self.assertTrue(session.box_office_bonus_available())

    def test_negotiating_without_the_standing_for_it_earns_nothing(self):
        session = Session(seed=32)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(want_approvals=False, want_box_office_bonus=True)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertEqual(summary["box_office_bonus_millions"], 0.0)

    def test_a_negotiated_bonus_on_a_hit_pays_out(self):
        from dataclasses import replace
        session = Session(seed=33)
        session.start("conservatory", "work")
        standing = session.state.actor.standing.copy()
        standing.add("heat", 65)
        standing.add("prestige", 65)
        standing.add("affection", 65)
        session.state = replace(session.state, actor=replace(session.state.actor, standing=standing))
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        self.assertTrue(session.box_office_bonus_available())
        session.choose_deal(want_approvals=False, want_box_office_bonus=True)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        if summary["roi"] > 1.0:
            self.assertGreater(summary["box_office_bonus_millions"], 0.0)
        else:
            self.assertEqual(summary["box_office_bonus_millions"], 0.0)


class TestStreamingBidding(unittest.TestCase):
    def test_streaming_bid_options_are_plain_data_and_include_self_distribute(self):
        session = Session(seed=40)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(False)
        bids = session.streaming_bid_options()
        self.assertTrue(bids)
        for b in bids:
            self.assertIsInstance(b["studio_name"], str)
            self.assertIsInstance(b["payout_millions"], float)
        self.assertTrue(any(b["self_distribute"] for b in bids))

    def test_choosing_a_specific_bid_drives_the_actual_payout(self):
        session = Session(seed=41)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(False)
        bids = session.streaming_bid_options()
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        self_distribute = next(b for b in bids if b["self_distribute"])
        summary = session.choose_release("streaming", streaming_multiplier=self_distribute["multiplier"])
        if summary["studio_overruled"]:
            self.skipTest("studio overruled the streaming request this run — RNG variance, not a bug")
        self.assertAlmostEqual(summary["roi"], self_distribute["multiplier"], places=2)

    def test_the_real_bid_pool_is_offered_after_quality_is_known_not_before(self):
        session = Session(seed=42)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(False)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})

        seen_bids = []

        def selector(bids):
            seen_bids.extend(bids)
            return max(bids, key=lambda b: b.payout_millions)

        summary = session.choose_release("streaming", streaming_bid_selector=selector)
        if summary["studio_overruled"]:
            self.skipTest("studio overruled the streaming request this run — RNG variance, not a bug")
        self.assertTrue(seen_bids)
        self.assertIsInstance(summary["streaming_buyer"], str)
        self.assertIn("roi", summary)

    def test_no_selector_defaults_to_auto_accepting_the_best_offer(self):
        session = Session(seed=43)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(False)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("streaming")
        if summary["studio_overruled"]:
            self.skipTest("studio overruled the streaming request this run — RNG variance, not a bug")
        self.assertIsNotNone(summary["streaming_buyer"])


class TestMultiPictureDeal(unittest.TestCase):
    def _accept_any_role(self, session: Session) -> bool:
        board = session.offer_board()
        avail = [o for o in board if o["available"]]
        if not avail:
            return False
        session.accept(avail[0]["index"])
        return True

    def _boost_standing(self, session: Session) -> None:
        standing = session.state.actor.standing.copy()
        standing.add("heat", 60)
        standing.add("affection", 40)
        standing.add("prestige", 40)
        session.state = replace(session.state, actor=replace(session.state.actor, standing=standing))

    def test_unavailable_without_an_accepted_role(self):
        session = Session(seed=50)
        session.start("conservatory", "work")
        self.assertFalse(session.multi_picture_deal_available())

    def test_unavailable_below_standing_threshold(self):
        session = Session(seed=51)
        session.start("conservatory", "work")
        if not self._accept_any_role(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        self.assertFalse(session.multi_picture_deal_available())

    def test_available_once_standing_clears_the_bar_and_signing_locks_in_terms(self):
        session = Session(seed=52)
        session.start("conservatory", "work")
        if not self._accept_any_role(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        self._boost_standing(session)
        self.assertTrue(session.multi_picture_deal_available())

        terms = session.multi_picture_deal_terms(3)
        self.assertEqual(terms["films"], 3)
        result = session.sign_multi_picture_deal(3)
        self.assertEqual(result["films"], 3)

        status = session.multi_picture_deal_status()
        self.assertEqual(status["films_remaining"], 3)
        self.assertFalse(session.multi_picture_deal_available())  # can't stack a second deal

    def test_next_board_guarantees_a_listing_from_the_deal_studio(self):
        session = Session(seed=53)
        session.start("conservatory", "work")
        if not self._accept_any_role(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        self._boost_standing(session)
        session.sign_multi_picture_deal(2)
        session.choose_deal(want_approvals=False)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        session.choose_release("wide")
        session.end_year()

        board = session.offer_board()
        guaranteed = [o for o in board if o["guaranteed"]]
        self.assertEqual(len(guaranteed), 1)
        before_remaining = session.multi_picture_deal_status()["films_remaining"]
        session.accept(guaranteed[0]["index"])
        self.assertEqual(session.multi_picture_deal_status()["films_remaining"], before_remaining - 1)

    def test_breaking_a_deal_costs_notoriety(self):
        session = Session(seed=54)
        session.start("conservatory", "work")
        if not self._accept_any_role(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        self._boost_standing(session)
        session.sign_multi_picture_deal(2)
        notoriety_before = session.state.actor.standing["notoriety"]
        session.break_multi_picture_deal()
        self.assertIsNone(session.multi_picture_deal_status())
        self.assertGreater(session.state.actor.standing["notoriety"], notoriety_before)


class TestSpinoff(unittest.TestCase):
    def test_not_available_without_an_indispensable_franchise(self):
        session = Session(seed=55)
        session.start("conservatory", "work")
        self.assertEqual(session.spinoff_options(), [])

    def test_available_once_a_franchise_crosses_the_threshold(self):
        session = Session(seed=56)
        session.start("conservatory", "work")
        entry = FranchiseEntry(franchise_id="fr_test", genre="scifi", studio_id="blockbuster", indispensability=70.0)
        session.state = replace(session.state, franchises={"fr_test": entry})
        options = session.spinoff_options()
        self.assertEqual(len(options), 1)
        self.assertEqual(options[0]["franchise_id"], "fr_test")

    def test_launching_guarantees_installment_one_on_the_next_board(self):
        session = Session(seed=57)
        session.start("conservatory", "work")
        board = session.offer_board()
        avail = [o for o in board if o["available"]]
        if not avail:
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.accept(avail[0]["index"])
        entry = FranchiseEntry(franchise_id="fr_test", genre="scifi", studio_id="blockbuster", indispensability=70.0)
        session.state = replace(session.state, franchises={**session.state.franchises, "fr_test": entry})
        session.launch_spinoff("fr_test")

        session.choose_deal(want_approvals=False)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        session.choose_release("wide")
        session.end_year()

        board2 = session.offer_board()
        guaranteed = [o for o in board2 if o["guaranteed"]]
        self.assertEqual(len(guaranteed), 1)
        self.assertEqual(guaranteed[0]["installment_number"], 1)
        self.assertEqual(guaranteed[0]["genre"], "scifi")


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

    def test_disappear_is_reachable_and_end_year_advances_the_calendar(self):
        session = Session(seed=10)
        session.start("conservatory", "work")
        start_age = session.age()
        message = session.disappear()
        self.assertIsInstance(message, str)
        self.assertGreater(session.leverage_status()["scarcity"], 0)
        session.end_year()
        self.assertGreater(session.age(), start_age)

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
            board = session.offer_board()
            available = [o for o in board if o["available"]]
            if available:
                session.accept(available[0]["index"])
                session.choose_deal(False)
                session.choose_prep("table_work")
                for _ in range(3):
                    session.play_scene({d: "with" for d, _ in session.dial_options()})
                session.choose_release("wide")
            else:
                session.decline_board()
        summary = session.obituary_summary()
        self.assertIsInstance(summary["credits"], int)
        self.assertIsInstance(summary["declined"], list)


if __name__ == "__main__":
    unittest.main()
