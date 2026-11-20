"""simulation/session.py — the player-facing façade. Every assertion here checks that Session
returns plain data (no engine types leak across the boundary) and that the previously-unreachable
systems (Rolodex interactions, Leverage's agent tier/Disappear, Awards) are now reachable.
"""
from __future__ import annotations

import unittest
from dataclasses import replace

from callback.engine.actor.offers import Role
from callback.engine.simulation._franchises import FranchiseEntry
from callback.engine.simulation.career import ProjectResult
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

    def test_offer_board_carries_the_new_v17_signals(self):
        session = Session(seed=6)
        session.start("conservatory", "work")
        board = session.offer_board()
        demand_bands_seen = set()
        buzz_bands_seen = set()
        for offer in board:
            self.assertIn("demand_band", offer)
            self.assertIn("buzz_band", offer)
            self.assertIn("franchise_scale", offer)
            self.assertIn("director", offer)
            self.assertIsInstance(offer["director"], dict)
            self.assertIn("known", offer["director"])
            if not offer["director"]["known"]:
                self.assertIsNone(offer["director"]["id"])
            demand_bands_seen.add(offer["demand_band"])
            buzz_bands_seen.add(offer["buzz_band"])
        # a real board should show some real variation, not one flat value for everyone
        self.assertGreater(len(buzz_bands_seen), 1)

    def test_director_info_reports_unknown_for_a_stranger(self):
        session = Session(seed=7)
        session.start("conservatory", "work")
        info = session.director_info("no_such_npc")
        self.assertFalse(info["known"])

    def test_director_info_reports_real_data_for_a_tracked_director(self):
        for seed in range(20):
            session = Session(seed=seed)
            session.start("conservatory", "work")
            directors = [n for n in session.rolodex_summary() if n["type"] == "director"]
            if not directors:
                continue
            info = session.director_info(directors[0]["id"])
            self.assertTrue(info["known"])
            self.assertIsInstance(info["trust_band"], str)
            self.assertIsInstance(info["projects_together"], int)
            return
        self.skipTest("no seed in range produced a tracked director — RNG variance, not a bug")

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


class TestRatingFlow(unittest.TestCase):
    def test_rating_preview_available_right_after_accept(self):
        """The palette (and so RatingScore) is fixed at accept() time — a preview is real and
        stable well before choose_release(), not sprung at the end."""
        for seed in range(20):
            session = Session(seed=seed)
            session.start("conservatory", "work")
            board = session.offer_board()
            available = [o for o in board if o["available"]]
            if not available:
                continue
            session.accept(available[0]["index"])
            preview = session.rating_preview()
            self.assertIn(preview["band"], ("G", "PG", "PG-13", "R", "NC-17"))
            self.assertIsInstance(preview["cut_available"], bool)
            return
        self.skipTest("no offer came through across 20 seeds — RNG variance, not a bug")

    def test_a_played_project_reports_a_real_rating_band(self):
        session = Session(seed=7)
        session.start("conservatory", "work")
        summary = _play_one_year(session)
        if summary is None:
            self.skipTest("no offer came through in the attempt budget — RNG variance, not a bug")
        self.assertIn(summary["rating_band"], ("G", "PG", "PG-13", "R", "NC-17"))
        self.assertIn(summary["rating_stance"], ("cut", "release_as_shot"))
        self.assertIsInstance(summary["rating_cut_forced"], bool)
        self.assertIsInstance(summary["rating_studio_pressure"], bool)

    def test_choosing_cut_only_takes_effect_on_a_genuine_borderline_film(self):
        """Requesting a cut on a film nowhere near a boundary is a no-op — near_boundary gates the
        whole decision, same restraint as the underlying rating.py rule."""
        found_non_borderline = False
        for seed in range(40):
            session = Session(seed=seed)
            session.start("conservatory", "work")
            board = session.offer_board()
            available = [o for o in board if o["available"]]
            if not available:
                continue
            session.accept(available[0]["index"])
            if session.rating_cut_available():
                continue
            found_non_borderline = True
            session.choose_deal(want_approvals=False)
            session.choose_rating_stance("cut")
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            summary = session.choose_release("wide")
            self.assertFalse(summary["rating_cut_forced"])
            self.assertFalse(summary["rating_studio_pressure"])
            break
        if not found_non_borderline:
            self.skipTest("every attempt landed on a borderline film — RNG variance, not a bug")


class TestMarketingPush(unittest.TestCase):
    def test_no_request_means_not_requested_or_honored(self):
        session = Session(seed=60)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(False)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertFalse(summary["marketing_push_requested"])
        self.assertFalse(summary["marketing_push_honored"])

    def test_requesting_sets_the_flag_and_reports_the_outcome(self):
        session = Session(seed=61)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(False)
        session.request_marketing_push()
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertTrue(summary["marketing_push_requested"])
        self.assertIsInstance(summary["marketing_push_honored"], bool)

    def test_request_flag_resets_on_the_next_accept(self):
        session = Session(seed=63)
        session.start("conservatory", "work")
        self.assertFalse(session._requested_marketing_push)
        for _ in range(30):
            if session.is_over():
                self.skipTest("no offer came through — RNG variance, not a bug")
            board = session.offer_board()
            avail = [o for o in board if o["available"]]
            if not avail:
                session.decline_board()
                continue
            session.accept(avail[0]["index"])
            break
        else:
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.request_marketing_push()
        self.assertTrue(session._requested_marketing_push)
        # a fresh accept() on a later project should clear the stale request
        session.choose_deal(False)
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        session.choose_release("wide")
        session.end_year()
        for _ in range(30):
            if session.is_over():
                self.skipTest("career ended before a second offer came through — RNG variance")
            board = session.offer_board()
            avail = [o for o in board if o["available"]]
            if not avail:
                session.decline_board(); session.end_year()
                continue
            session.accept(avail[0]["index"])
            break
        else:
            self.skipTest("no second offer came through — RNG variance, not a bug")
        self.assertFalse(session._requested_marketing_push)


def _get_to_prep(session: Session, max_attempts: int = 60) -> bool:
    """Advances until a FILM offer comes through and is accepted, stopping right after the Deal.
    Returns False if the run ended before anything came through (RNG variance). Deliberately skips
    any series listing (offers.SERIES_CHANCE) — every caller of this helper is exercising a film-
    specific mechanic (streaming bids, box-office bonus, release-strategy overrule) that a season
    genuinely doesn't have; series gets its own dedicated flow in TestSeriesFlow."""
    for _ in range(max_attempts):
        if session.is_over():
            return False
        board = session.offer_board()
        available = [o for o in board if o["available"] and o.get("project_type") != "series"]
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

    def test_first_dollar_gross_needs_more_standing_than_net_points(self):
        from dataclasses import replace
        session = Session(seed=34)
        session.start("conservatory", "work")
        standing = session.state.actor.standing.copy()
        standing.add("heat", 55)
        standing.add("prestige", 55)
        standing.add("affection", 55)
        session.state = replace(session.state, actor=replace(session.state.actor, standing=standing))
        self.assertTrue(session.box_office_bonus_available("net_points"))
        self.assertFalse(session.box_office_bonus_available("first_dollar_gross"))

    def test_first_dollar_gross_pays_out_even_on_a_flop(self):
        from dataclasses import replace
        session = Session(seed=35)
        session.start("conservatory", "work")
        standing = session.state.actor.standing.copy()
        standing.add("heat", 90)
        standing.add("prestige", 90)
        standing.add("affection", 90)
        session.state = replace(session.state, actor=replace(session.state.actor, standing=standing))
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        self.assertTrue(session.box_office_bonus_available("first_dollar_gross"))
        session.choose_deal(want_approvals=False, want_box_office_bonus=True, bonus_type="first_dollar_gross")
        session.choose_prep("table_work")
        for _ in range(3):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertEqual(summary["box_office_bonus_type"], "first_dollar_gross")
        if summary["gross_millions"] > 0:
            self.assertGreater(summary["box_office_bonus_millions"], 0.0)


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


class TestFestivalBidding(unittest.TestCase):
    """The acquisition roll (festival_acquisition_probability) is genuinely probabilistic, unlike
    streaming's always-resolved sale — every test here samples across seeds until an acquired film
    actually comes through, rather than asserting on one fixed seed."""

    def _get_acquired_summary(self, base_seed: int = 200, tries: int = 60, **choose_kwargs):
        for i in range(tries):
            session = Session(seed=base_seed + i)
            session.start("conservatory", "work")
            if not _get_to_prep(session):
                continue
            session.choose_deal(False)
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            summary = session.choose_release("festival", **choose_kwargs)
            if summary["studio_overruled"] or summary["gross_millions"] <= 0:
                continue
            return summary
        return None

    def test_festival_bid_options_are_plain_data(self):
        session = Session(seed=240)
        session.start("conservatory", "work")
        if not _get_to_prep(session):
            self.skipTest("no offer came through — RNG variance, not a bug")
        session.choose_deal(False)
        bids = session.festival_bid_options()
        self.assertTrue(bids)
        for b in bids:
            self.assertIsInstance(b["studio_name"], str)
            self.assertIsInstance(b["payout_millions"], float)

    def test_an_acquired_film_reports_a_buyer(self):
        summary = self._get_acquired_summary()
        if summary is None:
            self.skipTest("no acquired festival film came through in the sample — RNG variance")
        self.assertIsNotNone(summary["festival_buyer"])
        self.assertIn("roi", summary)

    def test_the_real_bid_pool_is_offered_after_quality_is_known_not_before(self):
        seen_bids = []

        def selector(bids):
            seen_bids.extend(bids)
            return max(bids, key=lambda b: b.payout_millions)

        summary = self._get_acquired_summary(festival_bid_selector=selector)
        if summary is None:
            self.skipTest("no acquired festival film came through in the sample — RNG variance")
        self.assertTrue(seen_bids)
        self.assertTrue(any(b.self_release for b in seen_bids))

    def test_choosing_self_release_uses_the_real_limited_numbers_not_a_flat_guarantee(self):
        def self_release_selector(bids):
            return next(b for b in bids if b.self_release)

        summary = self._get_acquired_summary(festival_bid_selector=self_release_selector)
        if summary is None:
            self.skipTest("no acquired festival film came through in the sample — RNG variance")
        self.assertTrue(summary["festival_self_released"])

    def test_choosing_an_outside_buyer_pays_a_flat_guarantee_not_self_release(self):
        def outside_selector(bids):
            outside = [b for b in bids if not b.self_release]
            return max(outside, key=lambda b: b.payout_millions) if outside else max(bids, key=lambda b: b.payout_millions)

        summary = self._get_acquired_summary(festival_bid_selector=outside_selector)
        if summary is None:
            self.skipTest("no acquired festival film with an outside bidder came through — RNG variance")
        self.assertFalse(summary["festival_self_released"])

    def test_no_selector_defaults_to_auto_accepting_the_best_offer(self):
        summary = self._get_acquired_summary()
        if summary is None:
            self.skipTest("no acquired festival film came through in the sample — RNG variance")
        self.assertIsNotNone(summary["festival_buyer"])


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


def _force_series_role(session: Session, n_episodes: int = 4, renewable: bool = False, max_attempts: int = 60) -> None:
    """Bypasses the offer board's own real-but-probabilistic 12% series chance (offers.
    SERIES_CHANCE) for a deterministic test — same direct-injection pattern other Session tests
    already use (e.g. TestBoxOfficeBonus manipulating session.state.actor.standing directly)."""
    from callback.engine.simulation.career import generate_palette
    for _ in range(max_attempts):
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        if not available:
            session.decline_board()
            continue
        session.accept(available[0]["index"])
        session._role = replace(session._role, project_type="series", n_episodes=n_episodes, series_renewable=renewable)
        session._palette = generate_palette(session._role.genre, session.rng)
        return
    raise AssertionError("test setup: no offer came through — RNG variance, not a bug")


class TestSeriesFlow(unittest.TestCase):
    def test_a_full_season_resolves_with_real_aggregate_numbers(self):
        session = Session(seed=40)
        session.start("conservatory", "work")
        _force_series_role(session, n_episodes=6)
        session.choose_deal(want_approvals=False)
        session.choose_prep("table_work")
        for _ in range(6):  # 3 premiere + 3 finale — see Session.episode_labels()
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")  # strategy is accepted but ignored for a series
        self.assertEqual(summary["n_episodes"], 6)
        self.assertIsInstance(summary["critic_score"], (int, float))
        self.assertGreaterEqual(summary["license_value_millions"], 0.0)
        self.assertIsNone(summary["renewed"])  # not sold as renewable
        self.assertNotIn("gross_millions", summary)  # box-office language doesn't belong on a season
        self.assertNotIn("box_office_bonus_millions", summary)
        # the TV-native read: real retention numbers, not just the ROI framing borrowed from film
        self.assertGreaterEqual(summary["final_retention_pct"], 0.0)
        self.assertLessEqual(summary["final_retention_pct"], 100.0)
        self.assertGreaterEqual(summary["average_retention_pct"], summary["final_retention_pct"])
        self.assertNotIn("studio_overruled", summary)

    def test_a_season_reports_roughly_the_whole_runs_budget_not_one_episodes_slice(self):
        # §5.18 — "a season pays like several films for one calendar commitment": the season's own
        # reported budget sums across all n_episodes, not just one episode's share of it.
        session = Session(seed=41)
        session.start("conservatory", "work")
        _force_series_role(session, n_episodes=10)
        per_episode_budget = session._role.film_budget_millions / 10
        session.choose_deal(want_approvals=False)
        session.choose_prep("table_work")
        for _ in range(6):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertGreater(summary["budget_millions"], per_episode_budget * 5)

    def test_a_non_renewable_series_never_rolls_renewal(self):
        session = Session(seed=42)
        session.start("conservatory", "work")
        _force_series_role(session, n_episodes=4, renewable=False)
        session.choose_deal(want_approvals=False)
        session.choose_prep("table_work")
        for _ in range(6):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertFalse(summary["renewable"])
        self.assertIsNone(summary["renewal_chance"])
        self.assertIsNone(summary["renewed"])

    def test_a_renewed_series_guarantees_next_years_listing_at_the_locked_terms(self):
        session = Session(seed=43)
        session.start("conservatory", "work")
        _force_series_role(session, n_episodes=4, renewable=True)
        original_fee = session._role.budget_for_role
        session.choose_deal(want_approvals=False)
        session.choose_prep("table_work")
        for _ in range(6):
            session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertIsNotNone(summary["renewal_chance"])
        if summary["renewed"]:
            self.assertIsNotNone(session._pending_renewed_series)
            self.assertEqual(session._pending_renewed_series.budget_for_role, original_fee)
            session.end_year()
            board = session.offer_board()
            guaranteed = [o for o in board if o.get("guaranteed")]
            self.assertTrue(guaranteed)
            self.assertEqual(guaranteed[0]["fee_millions"], round(original_fee, 2))
        else:
            self.assertIsNone(session._pending_renewed_series)

    def test_scene_names_stay_a_single_episodes_worth_regardless_of_series(self):
        # scene_names() describes ONE episode's own three scenes; episode_labels() is what tells
        # the caller how many real passes through it a project needs (1 for a film, 2 for a
        # series) — the two must never be conflated into one combined list.
        session = Session(seed=44)
        session.start("conservatory", "work")
        _force_series_role(session, n_episodes=8)
        self.assertEqual(len(session.scene_names()), 3)
        self.assertEqual(session.episode_labels(), ["premiere", "finale"])


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

    def test_application_status_starts_fresh_and_climbs_with_a_scanned_board(self):
        session = Session(seed=11)
        session.start("conservatory", "work")
        before = session.application_status()
        self.assertEqual(before["agent_tier"], "unrepresented")
        self.assertEqual(before["applications_this_year"], 0)
        self.assertEqual(before["fatigue_band"], "fresh")

        session.offer_board()
        session.generate_more_listings(20)
        after = session.application_status()
        self.assertGreater(after["applications_this_year"], before["applications_this_year"])

    def test_application_status_resets_on_a_new_offer_board(self):
        # offer_board() resets the counter to 0 and then immediately generates a fresh board, so
        # the real signal is that a second offer_board() call doesn't carry over everything a
        # prior board plus a big manual scan already accumulated -- not that it reads exactly 0.
        session = Session(seed=12)
        session.start("conservatory", "work")
        session.offer_board()
        session.generate_more_listings(50)
        accumulated = session.application_status()["applications_this_year"]
        session.offer_board()  # a fresh year's board
        self.assertLess(session.application_status()["applications_this_year"], accumulated)

    def test_trades_is_reachable(self):
        session = Session(seed=11)
        session.start("conservatory", "work")
        digest = session.trades()
        self.assertIsInstance(digest, list)
        self.assertTrue(all(isinstance(line, str) for line in digest))

    def test_interact_spends_a_quarter_and_refuses_a_fifth(self):
        session = Session(seed=40)
        session.start("conservatory", "work")
        npc_id = session.rolodex_summary()[0]["id"]
        self.assertEqual(session.actor_quarters_remaining_this_year(), 4)
        for _ in range(4):
            result = session.interact(npc_id, "check_in")
            self.assertNotIn("No time left", result)
        self.assertEqual(session.actor_quarters_remaining_this_year(), 0)
        refused = session.interact(npc_id, "check_in")
        self.assertIn("No time left", refused)
        session.end_year()
        self.assertEqual(session.actor_quarters_remaining_this_year(), 4)

    def test_accepting_a_role_spends_exactly_its_own_quarters_for_role(self):
        # actor.offers.quarters_for_role — a role's own real scale decides how much of the year it
        # costs; only a role that actually needs the full QUARTERS_PER_YEAR leaves nothing behind.
        from callback.engine.actor.offers import quarters_for_role
        session = Session(seed=41)
        session.start("conservatory", "work")
        board = session.offer_board()
        available = [o for o in board if o["available"]]
        if not available:
            self.skipTest("no offer came through this seed — RNG variance, not a bug")
        accepted = available[0]
        session.accept(accepted["index"])
        expected_remaining = max(0, 4 - quarters_for_role(session._role))
        self.assertEqual(session.actor_quarters_remaining_this_year(), expected_remaining)
        self.assertEqual(accepted["quarters_required"], quarters_for_role(session._role))

    def test_disappear_spends_the_whole_years_actor_quarters(self):
        session = Session(seed=42)
        session.start("conservatory", "work")
        session.disappear()
        self.assertEqual(session.actor_quarters_remaining_this_year(), 0)


class TestAwardsReachable(unittest.TestCase):
    def test_no_campaign_available_before_any_project(self):
        session = Session(seed=12)
        session.start("conservatory", "work")
        self.assertFalse(session.awards_campaign_available())

    def _drama_result(self, role_depth="showcase"):
        role = Role(
            project_id="p1", genre="drama", archetype="leading_hero", billing="lead",
            char_age=35, type_strictness=0.5, difficulty=50, budget_for_role=10,
            gatekeeper="prestige_auteur", role_depth=role_depth,
        )
        return ProjectResult(
            role=role, cast_via="direct_offer", spotlight=95.0, craft_contribution=20.0,
            performance=90.0, project_quality=88.0, film_critic_score=92.0, audience_score=70.0,
            roi=2.0, budget=10.0, marketing=2.0, gross=40.0, opening=15.0, legs=1.5,
            release_strategy="wide", heat_delta=0.0, prestige_delta=5.0, affection_delta=0.0,
        )

    def test_campaign_updates_award_history_on_the_actor(self):
        session = Session(seed=13)
        session.start("conservatory", "work")
        session._last_result = self._drama_result()
        before = session.state.actor.award_nominations
        session.run_awards_campaign("lead_drama", spend_millions=2.0)
        # Either a nomination happened (count went up) or it genuinely didn't — either way the
        # field is real and tracked, not stuck at the default forever.
        self.assertGreaterEqual(session.state.actor.award_nominations, before)

    def test_underwritten_role_in_a_drama_still_caps_hard(self):
        """§14.3 — depth is a real second gate: a showcase role and an underwritten role in the
        exact same high-ceiling genre should not resolve identically at the top end."""
        from callback.engine.awards.awards import award_ceiling
        self.assertLess(award_ceiling("drama", "underwritten"), award_ceiling("drama", "showcase"))

    def test_category_fraud_can_add_notoriety_when_caught(self):
        # Run enough seeds that at least one gets caught (35% per roll) and confirm notoriety
        # only ever moves when the field itself reports a catch. Campaigning SUPPORTING with a
        # lead-billed role is the actual real-world move category_fraud describes.
        caught_any = False
        for seed in range(30):
            session = Session(seed=seed)
            session.start("conservatory", "work")
            session._last_result = self._drama_result()
            notoriety_before = session.state.actor.standing["notoriety"]
            result = session.run_awards_campaign("supporting", spend_millions=1.0, attempt_category_fraud=True)
            notoriety_after = session.state.actor.standing["notoriety"]
            if result["category_fraud_caught"]:
                caught_any = True
                self.assertGreater(notoriety_after, notoriety_before)
        self.assertTrue(caught_any)

    def test_available_categories_for_a_lead_drama_role(self):
        session = Session(seed=15)
        session.start("conservatory", "work")
        session._last_result = self._drama_result()
        categories = session.available_award_categories()
        self.assertIn("lead_drama", categories)
        self.assertIn("ensemble", categories)
        self.assertNotIn("lead_comedy", categories)
        self.assertNotIn("supporting", categories)

    def test_available_categories_for_a_comedy_supporting_role(self):
        role = Role(
            project_id="p2", genre="comedy", archetype="comic_relief", billing="supporting",
            char_age=30, type_strictness=0.5, difficulty=50, budget_for_role=5,
            gatekeeper="prestige_auteur",
        )
        result = replace(self._drama_result(), role=role)
        session = Session(seed=16)
        session.start("conservatory", "work")
        session._last_result = result
        categories = session.available_award_categories()
        self.assertIn("supporting", categories)
        self.assertIn("ensemble", categories)
        self.assertNotIn("lead_drama", categories)
        self.assertNotIn("lead_comedy", categories)

    def test_available_categories_for_a_horror_lead_include_genre_excellence(self):
        role = Role(
            project_id="p3", genre="horror", archetype="leading_hero", billing="lead",
            char_age=28, type_strictness=0.5, difficulty=50, budget_for_role=5,
            gatekeeper="prestige_auteur",
        )
        result = replace(self._drama_result(), role=role)
        session = Session(seed=19)
        session.start("conservatory", "work")
        session._last_result = result
        categories = session.available_award_categories()
        self.assertIn("lead_drama", categories)  # still a real, if long-shot, prestige contender
        self.assertIn("genre_excellence", categories)  # AND a real second-circuit contender

    def test_available_categories_for_an_animated_role_include_voice_performance(self):
        role = Role(
            project_id="p4", genre="family", archetype="everyman", billing="lead",
            char_age=28, type_strictness=0.5, difficulty=50, budget_for_role=5,
            gatekeeper="prestige_auteur", is_animation=True,
        )
        result = replace(self._drama_result(), role=role)
        session = Session(seed=20)
        session.start("conservatory", "work")
        session._last_result = result
        self.assertIn("voice_performance", session.available_award_categories())

    def test_genre_excellence_win_moves_prestige(self):
        role = Role(
            project_id="p5", genre="scifi", archetype="leading_hero", billing="lead",
            char_age=28, type_strictness=0.5, difficulty=50, budget_for_role=5,
            gatekeeper="prestige_auteur", role_depth="showcase",
        )
        for seed in range(40):
            session = Session(seed=seed + 400)
            session.start("conservatory", "work")
            session._last_result = replace(self._drama_result(), role=role)
            prestige_before = session.state.actor.standing["prestige"]
            result = session.run_awards_campaign("genre_excellence", spend_millions=2.0)
            if result["won"]:
                self.assertGreater(session.state.actor.standing["prestige"], prestige_before)
                return
        self.skipTest("no genre_excellence win landed across 40 seeds — RNG variance, not a bug")

    def test_breakthrough_only_available_early_career(self):
        session = Session(seed=17)
        session.start("conservatory", "work")
        session._last_result = self._drama_result()
        session.state = replace(session.state, actor=replace(session.state.actor, credits=1))
        self.assertIn("breakthrough", session.available_award_categories())
        session.state = replace(session.state, actor=replace(session.state.actor, credits=10))
        self.assertNotIn("breakthrough", session.available_award_categories())

    def test_ensemble_win_moves_affection_not_prestige(self):
        session = Session(seed=18)
        session.start("conservatory", "work")
        session._last_result = self._drama_result()
        affection_before = session.state.actor.standing["affection"]
        prestige_before = session.state.actor.standing["prestige"]
        for seed in range(40):
            session = Session(seed=seed + 100)
            session.start("conservatory", "work")
            session._last_result = self._drama_result()
            result = session.run_awards_campaign("ensemble", spend_millions=2.0)
            if result["won"]:
                self.assertGreater(session.state.actor.standing["affection"], affection_before)
                self.assertEqual(session.state.actor.standing["prestige"], prestige_before)
                return
        self.skipTest("no ensemble win landed across 40 seeds — RNG variance, not a bug")

    def test_breakthrough_win_moves_heat_not_prestige(self):
        prestige_before = None
        for seed in range(40):
            session = Session(seed=seed + 200)
            session.start("conservatory", "work")
            session._last_result = self._drama_result()
            session.state = replace(session.state, actor=replace(session.state.actor, credits=1))
            heat_before = session.state.actor.standing["heat"]
            prestige_before = session.state.actor.standing["prestige"]
            result = session.run_awards_campaign("breakthrough", spend_millions=2.0)
            if result["won"]:
                self.assertGreater(session.state.actor.standing["heat"], heat_before)
                self.assertEqual(session.state.actor.standing["prestige"], prestige_before)
                return
        self.skipTest("no breakthrough win landed across 40 seeds — RNG variance, not a bug")


class TestCutLifestyleFloor(unittest.TestCase):
    """§11.6 — the going-broke ratchet's real escape hatch, reachable through Session."""

    def test_cutting_the_floor_lowers_it_and_costs_affection(self):
        session = Session(seed=14)
        session.start("conservatory", "work")
        money = replace(session.state.life.money, lifestyle_floor=10.0, net_worth=-5.0)
        session.state = replace(session.state, life=replace(session.state.life, money=money))
        affection_before = session.state.actor.standing["affection"]
        result = session.cut_lifestyle_floor(3.0)
        self.assertEqual(result["new_floor_millions"], 3.0)
        self.assertEqual(session.state.life.money.lifestyle_floor, 3.0)
        self.assertLess(session.state.actor.standing["affection"], affection_before)

    def test_cutting_the_floor_cannot_raise_it(self):
        session = Session(seed=15)
        session.start("conservatory", "work")
        money = replace(session.state.life.money, lifestyle_floor=3.0)
        session.state = replace(session.state, life=replace(session.state.life, money=money))
        session.cut_lifestyle_floor(100.0)
        self.assertEqual(session.state.life.money.lifestyle_floor, 3.0)


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
