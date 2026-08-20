"""simulation/_franchises.py — the sequel-value curve (genre/franchise.py) and Indispensability
holdout (leverage/indispensability.py), composed into the actor's game loop and interacting with
Standing, the Rolodex-requested director, and the studio that financed the original film.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.offers import Role
from callback.engine.actor.standing import new_standing_model
from callback.engine.genre.franchise import SEQUEL_BONUS_AUDIENCE_CENTRE
from callback.engine.simulation._franchises import (
    advance_franchises_without_you,
    apply_exit,
    decline_continuation_probability,
    FranchiseEntry,
    RECAST_AUDIENCE_PENALTY_CEILING,
    RECAST_AUDIENCE_PENALTY_FLOOR,
    REBOOT_MIN_DORMANT_YEARS,
    SEQUEL_CHANCE_BASE,
    SEQUEL_CHANCE_CEILING,
    SPINOFF_INDISPENSABILITY_THRESHOLD,
    create_spinoff_entry,
    director_continuity_bonus,
    franchise_audience_bonus,
    maybe_attach_franchise,
    reboot_probability,
    recast_audience_penalty,
    resolve_reboots,
    sequel_probability,
    spinoff_available,
    studio_protectiveness,
    update_franchise_after_project,
    writeout_audience_delta,
    written_out_probability,
)
from callback.engine.simulation.session import Session


def _role(**overrides) -> Role:
    base = dict(
        project_id="p_000001", genre="action", archetype="everyman", billing="supporting",
        char_age=35, type_strictness=0.5, difficulty=50.0, budget_for_role=10.0, gatekeeper="studio_tentpole",
    )
    base.update(overrides)
    return Role(**base)


class TestMaybeAttachFranchise(unittest.TestCase):
    def test_can_start_a_new_franchise_from_an_original_role(self):
        rng = random.Random(1)
        attached_any = False
        for _ in range(200):
            role = maybe_attach_franchise(_role(), {}, current_year=0, rng=rng)
            if role.franchise_id is not None:
                self.assertEqual(role.installment_number, 1)
                attached_any = True
        self.assertTrue(attached_any)

    def test_can_attach_a_sequel_to_an_eligible_open_franchise(self):
        rng = random.Random(2)
        franchise = FranchiseEntry(franchise_id="fr_001", genre="horror", studio_id="indie",
                                    installments_starred=1, last_installment_year=10)
        attached_sequel = False
        for _ in range(200):
            role = maybe_attach_franchise(_role(genre="comedy", studio="mid_major"), {"fr_001": franchise},
                                           current_year=11, rng=rng)
            if role.franchise_id == "fr_001":
                self.assertEqual(role.installment_number, 2)
                self.assertEqual(role.genre, "horror")  # continuity — the sequel keeps the franchise's genre
                self.assertEqual(role.studio, "indie")  # and its studio
                attached_sequel = True
        self.assertTrue(attached_sequel)

    def test_a_long_dormant_franchise_is_not_eligible_for_a_new_sequel(self):
        rng = random.Random(3)
        franchise = FranchiseEntry(franchise_id="fr_002", genre="horror", studio_id="indie",
                                    installments_starred=1, last_installment_year=0)
        for _ in range(200):
            role = maybe_attach_franchise(_role(), {"fr_002": franchise}, current_year=50, rng=rng)
            self.assertNotEqual(role.franchise_id, "fr_002")

    def test_a_hit_franchise_gets_sequels_far_more_often_than_a_flop(self):
        # The whole point of the rebalance: two otherwise-identical franchises should no longer
        # compete for the same flat 35% shot — a beloved hit and a poorly-received flop need to
        # produce visibly different sequel rates over enough rolls.
        hit = FranchiseEntry(franchise_id="fr_hit", genre="action", studio_id="indie",
                              installments_starred=1, last_installment_year=10, prior_audience_score=95.0)
        flop = FranchiseEntry(franchise_id="fr_flop", genre="action", studio_id="indie",
                               installments_starred=1, last_installment_year=10, prior_audience_score=10.0)
        hit_sequels = 0
        flop_sequels = 0
        rng = random.Random(11)
        for _ in range(500):
            if maybe_attach_franchise(_role(), {"fr_hit": hit}, current_year=11, rng=rng).franchise_id == "fr_hit":
                hit_sequels += 1
        for _ in range(500):
            if maybe_attach_franchise(_role(), {"fr_flop": flop}, current_year=11, rng=rng).franchise_id == "fr_flop":
                flop_sequels += 1
        self.assertGreater(hit_sequels, flop_sequels * 2)

    def test_multiple_eligible_franchises_each_get_their_own_independent_roll(self):
        hit = FranchiseEntry(franchise_id="fr_hit", genre="action", studio_id="indie",
                              installments_starred=1, last_installment_year=10, prior_audience_score=95.0)
        flop = FranchiseEntry(franchise_id="fr_flop", genre="action", studio_id="indie",
                               installments_starred=1, last_installment_year=10, prior_audience_score=10.0)
        hit_count = 0
        flop_count = 0
        rng = random.Random(12)
        for _ in range(500):
            role = maybe_attach_franchise(_role(), {"fr_hit": hit, "fr_flop": flop}, current_year=11, rng=rng)
            if role.franchise_id == "fr_hit":
                hit_count += 1
            elif role.franchise_id == "fr_flop":
                flop_count += 1
        self.assertGreater(hit_count, flop_count)


class TestSequelProbability(unittest.TestCase):
    def test_average_reception_and_zero_indispensability_matches_the_base_rate(self):
        self.assertAlmostEqual(sequel_probability(SEQUEL_BONUS_AUDIENCE_CENTRE, 0.0), SEQUEL_CHANCE_BASE, places=6)

    def test_better_reception_raises_the_probability(self):
        low = sequel_probability(20.0, 0.0)
        high = sequel_probability(90.0, 0.0)
        self.assertGreater(high, low)

    def test_higher_indispensability_raises_the_probability_independent_of_reception(self):
        base = sequel_probability(SEQUEL_BONUS_AUDIENCE_CENTRE, 0.0)
        boosted = sequel_probability(SEQUEL_BONUS_AUDIENCE_CENTRE, 80.0)
        self.assertGreater(boosted, base)

    def test_never_exceeds_the_ceiling_even_at_extreme_inputs(self):
        self.assertLessEqual(sequel_probability(100.0, 100.0), SEQUEL_CHANCE_CEILING)

    def test_never_goes_negative_at_extreme_low_reception(self):
        self.assertGreaterEqual(sequel_probability(0.0, 0.0), 0.0)


class TestFranchiseAudienceBonus(unittest.TestCase):
    def test_non_franchise_role_gets_no_bonus(self):
        self.assertEqual(franchise_audience_bonus(_role(), {}, current_year=10), 0.0)

    def test_a_well_received_prior_installment_gives_a_bigger_bonus_than_a_poorly_received_one(self):
        role = _role(franchise_id="fr_003", installment_number=2)
        strong_prior = {"fr_003": FranchiseEntry(franchise_id="fr_003", genre="action", studio_id="mid_major",
                                                  prior_audience_score=90.0, last_installment_year=5)}
        weak_prior = {"fr_003": FranchiseEntry(franchise_id="fr_003", genre="action", studio_id="mid_major",
                                                prior_audience_score=20.0, last_installment_year=5)}
        self.assertGreater(
            franchise_audience_bonus(role, strong_prior, current_year=10),
            franchise_audience_bonus(role, weak_prior, current_year=10),
        )

    def test_a_rushed_sequel_reads_worse_than_a_well_spaced_one(self):
        role = _role(franchise_id="fr_005", installment_number=2)
        rushed = {"fr_005": FranchiseEntry(franchise_id="fr_005", genre="action", studio_id="mid_major",
                                            prior_audience_score=65.0, last_installment_year=9)}
        well_spaced = {"fr_005": FranchiseEntry(franchise_id="fr_005", genre="action", studio_id="mid_major",
                                                 prior_audience_score=65.0, last_installment_year=5)}
        self.assertGreater(
            franchise_audience_bonus(role, well_spaced, current_year=10),
            franchise_audience_bonus(role, rushed, current_year=10),
        )


class TestSpinoff(unittest.TestCase):
    def test_not_available_below_the_indispensability_threshold(self):
        f = FranchiseEntry(franchise_id="fr_006", genre="action", studio_id="mid_major",
                            indispensability=SPINOFF_INDISPENSABILITY_THRESHOLD - 1.0)
        self.assertFalse(spinoff_available(f))

    def test_available_at_or_above_the_threshold(self):
        f = FranchiseEntry(franchise_id="fr_007", genre="action", studio_id="mid_major",
                            indispensability=SPINOFF_INDISPENSABILITY_THRESHOLD)
        self.assertTrue(spinoff_available(f))

    def test_spinoff_inherits_studio_and_genre_and_a_real_head_start(self):
        parent = FranchiseEntry(franchise_id="fr_008", genre="horror", studio_id="indie", indispensability=80.0)
        entry = create_spinoff_entry(parent, "fr_008_spinoff", current_year=12)
        self.assertEqual(entry.genre, "horror")
        self.assertEqual(entry.studio_id, "indie")
        self.assertGreater(entry.prior_audience_score, SEQUEL_BONUS_AUDIENCE_CENTRE)
        self.assertEqual(entry.installments_starred, 0)

    def test_spinoff_is_touched_this_year_so_it_survives_immediate_dormant_decay(self):
        from callback.engine.simulation._franchises import decay_dormant_franchises
        parent = FranchiseEntry(franchise_id="fr_009", genre="drama", studio_id="prestige", indispensability=60.0)
        entry = create_spinoff_entry(parent, "fr_009_spinoff", current_year=20)
        active, retired = decay_dormant_franchises({"fr_009_spinoff": entry}, current_year=20)
        self.assertIn("fr_009_spinoff", active)
        self.assertEqual(retired, {})


class TestDirectorContinuityBonus(unittest.TestCase):
    def test_the_same_returning_director_earns_a_bonus(self):
        role = _role(franchise_id="fr_004", installment_number=2)
        franchises = {"fr_004": FranchiseEntry(franchise_id="fr_004", genre="action", studio_id="mid_major",
                                                last_director_npc_id="n_001")}
        self.assertGreater(director_continuity_bonus(role, franchises, "n_001"), 0.0)

    def test_a_different_or_no_director_earns_nothing(self):
        role = _role(franchise_id="fr_005", installment_number=2)
        franchises = {"fr_005": FranchiseEntry(franchise_id="fr_005", genre="action", studio_id="mid_major",
                                                last_director_npc_id="n_001")}
        self.assertEqual(director_continuity_bonus(role, franchises, "n_002"), 0.0)
        self.assertEqual(director_continuity_bonus(role, franchises, None), 0.0)


class TestUpdateFranchiseAfterProject(unittest.TestCase):
    def test_installments_and_indispensability_grow_across_sequels(self):
        standing = new_standing_model()
        franchises = {}
        role1 = _role(franchise_id="fr_006", installment_number=1)
        franchises = update_franchise_after_project(franchises, role1, spotlight=70.0, audience_score=75.0,
                                                      standing_model=standing, current_year=0,
                                                      requested_director_npc_id="n_010")
        f1 = franchises["fr_006"]
        self.assertEqual(f1.installments_starred, 1)

        role2 = _role(franchise_id="fr_006", installment_number=2)
        franchises = update_franchise_after_project(franchises, role2, spotlight=75.0, audience_score=80.0,
                                                      standing_model=standing, current_year=2,
                                                      requested_director_npc_id="n_010")
        f2 = franchises["fr_006"]
        self.assertEqual(f2.installments_starred, 2)
        self.assertGreaterEqual(f2.indispensability, f1.indispensability)
        self.assertEqual(f2.last_director_npc_id, "n_010")


class TestStudioProtectiveness(unittest.TestCase):
    def test_a_brand_new_franchise_has_no_real_protectiveness(self):
        f = FranchiseEntry(franchise_id="fr_p1", genre="action", studio_id="mid_major",
                            installments_starred=1, prior_audience_score=54.0)
        self.assertLess(studio_protectiveness(f), 15.0)

    def test_a_long_running_hit_earns_real_protectiveness(self):
        f = FranchiseEntry(franchise_id="fr_p2", genre="action", studio_id="mid_major",
                            installments_starred=8, prior_audience_score=90.0)
        self.assertGreater(studio_protectiveness(f), 70.0)

    def test_one_hit_installment_alone_does_not_max_it_out(self):
        f = FranchiseEntry(franchise_id="fr_p3", genre="action", studio_id="mid_major",
                            installments_starred=1, prior_audience_score=95.0)
        self.assertLess(studio_protectiveness(f), 50.0)

    def test_never_exceeds_100(self):
        f = FranchiseEntry(franchise_id="fr_p4", genre="action", studio_id="mid_major",
                            installments_starred=50, prior_audience_score=100.0)
        self.assertLessEqual(studio_protectiveness(f), 100.0)


class TestPeakIndispensability(unittest.TestCase):
    def test_peak_grows_with_a_hit_installment(self):
        standing = new_standing_model()
        role = _role(franchise_id="fr_peak", installment_number=1)
        franchises = update_franchise_after_project(
            {}, role, spotlight=90.0, audience_score=95.0,
            standing_model=standing, current_year=0, requested_director_npc_id=None,
        )
        f = franchises["fr_peak"]
        self.assertGreater(f.peak_indispensability, 0.0)
        self.assertEqual(f.peak_indispensability, f.indispensability)

    def test_peak_survives_a_later_dormant_decay_that_lowers_current_indispensability(self):
        from callback.engine.simulation._franchises import decay_dormant_franchises
        standing = new_standing_model()
        role = _role(franchise_id="fr_peak2", installment_number=1)
        franchises = update_franchise_after_project(
            {}, role, spotlight=90.0, audience_score=95.0,
            standing_model=standing, current_year=0, requested_director_npc_id=None,
        )
        peak = franchises["fr_peak2"].peak_indispensability
        active, _ = decay_dormant_franchises(franchises, current_year=1)  # dormant this year -> decays
        self.assertLess(active["fr_peak2"].indispensability, peak)
        self.assertEqual(active["fr_peak2"].peak_indispensability, peak)  # the record itself never falls


class TestReboot(unittest.TestCase):
    def test_too_recently_retired_never_reboots(self):
        self.assertEqual(reboot_probability(years_dormant=REBOOT_MIN_DORMANT_YEARS - 1, peak_indispensability=100.0), 0.0)

    def test_a_franchise_that_peaked_higher_is_more_likely_to_reboot(self):
        low_peak = reboot_probability(years_dormant=10, peak_indispensability=10.0)
        high_peak = reboot_probability(years_dormant=10, peak_indispensability=90.0)
        self.assertGreater(high_peak, low_peak)

    def test_resolve_reboots_moves_a_revived_franchise_out_of_retired(self):
        retired = {
            "fr_r1": FranchiseEntry(franchise_id="fr_r1", genre="action", studio_id="mid_major",
                                     peak_indispensability=100.0, retired_year=0),
        }
        rng = random.Random(1)
        still_retired, revived = None, None
        for _ in range(500):
            still_retired, revived = resolve_reboots(retired, current_year=50, rng=rng)
            if revived:
                break
        self.assertIn("fr_r1", revived)
        self.assertNotIn("fr_r1", still_retired)

    def test_a_revived_franchise_is_immediately_eligible_for_a_sequel_next_offer(self):
        retired = {
            "fr_r2": FranchiseEntry(franchise_id="fr_r2", genre="horror", studio_id="indie",
                                     peak_indispensability=100.0, retired_year=0),
        }
        rng = random.Random(2)
        revived = {}
        for _ in range(500):
            _, revived = resolve_reboots(retired, current_year=50, rng=rng)
            if revived:
                break
        self.assertTrue(revived)
        f = revived["fr_r2"]
        self.assertEqual(f.last_installment_year, 50)
        self.assertIsNone(f.retired_year)
        self.assertGreater(f.indispensability, 0.0)

    def test_a_franchise_never_rolled_reboot_stays_retired_and_unchanged(self):
        retired = {
            "fr_r3": FranchiseEntry(franchise_id="fr_r3", genre="drama", studio_id="mid_major",
                                     peak_indispensability=0.0, retired_year=0),
        }
        # peak_indispensability=0.0 -> reboot_probability's base+coef*0 is still REBOOT_CHANCE_BASE,
        # so use years_dormant below the minimum instead for a deterministic zero-probability case.
        still_retired, revived = resolve_reboots(retired, current_year=REBOOT_MIN_DORMANT_YEARS - 1, rng=random.Random(3))
        self.assertEqual(revived, {})
        self.assertIn("fr_r3", still_retired)


class TestExitOutcome(unittest.TestCase):
    """resolve_exit_type's own branch: recast vs written_out, and the flexible (never one fixed
    number) ranges each branch's audience effect draws from."""

    def test_higher_character_id_makes_recast_more_likely_than_written_out(self):
        high = written_out_probability(character_id=95.0, rng=random.Random(1))
        low = written_out_probability(character_id=5.0, rng=random.Random(1))
        self.assertLess(high, low)

    def test_recast_penalty_stays_in_a_flexible_range_and_is_shielded_by_protectiveness(self):
        rng = random.Random(2)
        weak = [recast_audience_penalty(0.0, rng) for _ in range(200)]
        strong = [recast_audience_penalty(100.0, rng) for _ in range(200)]
        self.assertTrue(all(RECAST_AUDIENCE_PENALTY_FLOOR <= v <= RECAST_AUDIENCE_PENALTY_CEILING for v in weak + strong))
        self.assertLess(sum(strong) / len(strong), sum(weak) / len(weak))
        self.assertGreater(len(set(round(v, 4) for v in weak)), 1)  # never the same number twice

    def test_writeout_delta_can_land_either_direction(self):
        deltas = [writeout_audience_delta(random.Random(i)) for i in range(200)]
        self.assertTrue(any(d < 0 for d in deltas))
        self.assertTrue(any(d > 0 for d in deltas))


class TestFranchiseExit(unittest.TestCase):
    def test_apply_exit_flips_the_lead_flag_and_snapshots_audience_score(self):
        f = FranchiseEntry(franchise_id="fr_rc1", genre="action", studio_id="mid_major",
                            installments_starred=3, prior_audience_score=70.0)
        exited = apply_exit(f, current_year=10, rng=random.Random(5))
        self.assertFalse(exited.you_are_current_lead)
        self.assertIn(exited.exit_type, ("recast", "written_out"))
        self.assertEqual(exited.exit_year, 10)
        self.assertEqual(exited.audience_score_at_exit, 70.0)

    def test_exited_franchise_is_never_offered_back_as_a_role(self):
        exited = apply_exit(
            FranchiseEntry(franchise_id="fr_rc4", genre="drama", studio_id="indie",
                            installments_starred=2, prior_audience_score=90.0, last_installment_year=0),
            current_year=0, rng=random.Random(7),
        )
        rng = random.Random(7)
        offered_it = False
        for _ in range(300):
            role = maybe_attach_franchise(_role(), {"fr_rc4": exited}, current_year=1, rng=rng)
            if role.franchise_id == "fr_rc4":
                offered_it = True
                break
        self.assertFalse(offered_it)

    def test_spinoff_unavailable_once_you_have_left_even_at_high_indispensability(self):
        f = FranchiseEntry(franchise_id="fr_rc5", genre="action", studio_id="mid_major",
                            indispensability=SPINOFF_INDISPENSABILITY_THRESHOLD + 10.0)
        self.assertTrue(spinoff_available(f))
        self.assertFalse(spinoff_available(apply_exit(f, 0, random.Random(1))))

    def test_advance_franchises_without_you_only_touches_entries_youve_left(self):
        led = FranchiseEntry(franchise_id="fr_rc6", genre="action", studio_id="mid_major",
                              prior_audience_score=90.0, indispensability=90.0, last_installment_year=0)
        exited = apply_exit(
            FranchiseEntry(franchise_id="fr_rc7", genre="action", studio_id="mid_major",
                            prior_audience_score=90.0, indispensability=90.0, last_installment_year=0),
            current_year=0, rng=random.Random(3),
        )
        rng = random.Random(3)
        updated = advance_franchises_without_you({"fr_rc6": led, "fr_rc7": exited}, current_year=1, rng=rng)
        self.assertEqual(updated["fr_rc6"], led)  # untouched — the player still leads this one
        # A high audience/indispensability franchise should greenlight virtually every year.
        self.assertGreaterEqual(updated["fr_rc7"].installments_starred, exited.installments_starred)

    def test_a_stale_exited_franchise_does_not_quietly_advance(self):
        exited = apply_exit(
            FranchiseEntry(franchise_id="fr_rc8", genre="action", studio_id="mid_major",
                            prior_audience_score=90.0, indispensability=90.0, last_installment_year=0),
            current_year=0, rng=random.Random(1),
        )
        updated = advance_franchises_without_you({"fr_rc8": exited}, current_year=999, rng=random.Random(1))
        self.assertEqual(updated["fr_rc8"], exited)

    def test_reboot_restores_you_as_lead_and_clears_the_exit_snapshot(self):
        exited = apply_exit(
            FranchiseEntry(franchise_id="fr_rc9", genre="action", studio_id="mid_major",
                            peak_indispensability=100.0, retired_year=0),
            current_year=0, rng=random.Random(4),
        )
        rng = random.Random(4)
        revived = {}
        for _ in range(500):
            _, revived = resolve_reboots({"fr_rc9": exited}, current_year=50, rng=rng)
            if revived:
                break
        self.assertTrue(revived)
        f = revived["fr_rc9"]
        self.assertTrue(f.you_are_current_lead)
        self.assertIsNone(f.exit_type)
        self.assertIsNone(f.exit_year)
        self.assertIsNone(f.audience_score_at_exit)

    def test_a_more_protected_franchise_is_more_likely_to_proceed_without_you_on_a_decline(self):
        self.assertGreater(
            decline_continuation_probability(protectiveness=100.0), decline_continuation_probability(protectiveness=0.0),
        )


class TestMerchandisingIntegration(unittest.TestCase):
    def _get_to_prep_with_standing(self, session: Session, max_attempts: int = 60) -> bool:
        # A series never touches the franchise-tracking system at all (simulation.full_career.
        # accept_and_play_season never calls update_franchise_after_project — a real, separate
        # design boundary, not a bug) — this helper is specifically for film-path merchandising/
        # franchise tests, so it holds out for a film rather than accepting the first available
        # listing regardless of project_type.
        from dataclasses import replace
        standing = session.state.actor.standing.copy()
        standing.add("heat", 60)
        standing.add("prestige", 60)
        standing.add("affection", 60)
        session.state = replace(session.state, actor=replace(session.state.actor, standing=standing))
        for _ in range(max_attempts):
            if session.is_over():
                return False
            board = session.offer_board()
            available = [o for o in board if o["available"] and o.get("project_type", "film") == "film"]
            if not available:
                session.decline_board()
                continue
            session.accept(available[0]["index"])
            return True
        return False

    def test_a_negotiated_deal_pays_a_real_ongoing_royalty(self):
        from dataclasses import replace
        session = Session(seed=200)
        session.start("conservatory", "work")
        self.assertTrue(self._get_to_prep_with_standing(session))
        session._role = replace(session._role, is_animation=True, franchise_id="fr_merch_test", installment_number=1)
        self.assertTrue(session.merchandising_available())

        session.choose_deal(want_approvals=False, want_merchandising=True)
        self.assertTrue(session._merch_negotiated)
        self.assertGreater(session._merch_share, 0.0)

        session.choose_prep("table_work")
        for episode in session.episode_labels():
            for _ in range(len(session.scene_names())):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
        summary = session.choose_release("wide")
        self.assertTrue(summary["merchandising_negotiated"])
        self.assertIsNotNone(summary["merchandising_share_pct"])

        deals = session.state.merchandising_deals
        self.assertEqual(len(deals), 1)
        self.assertEqual(deals[0].franchise_id, "fr_merch_test")

        status = session.merchandising_status()
        self.assertEqual(len(status), 1)
        self.assertTrue(status[0]["still_active"])
        self.assertGreater(status[0]["this_years_payout_millions"], 0.0)

    def test_unavailable_below_standing_threshold(self):
        from dataclasses import replace
        session = Session(seed=201)
        session.start("conservatory", "work")
        for _ in range(30):
            if session.is_over():
                break
            board = session.offer_board()
            available = [o for o in board if o["available"]]
            if not available:
                session.decline_board()
                continue
            session.accept(available[0]["index"])
            session._role = replace(session._role, is_animation=True, franchise_id="fr_low_standing")
            self.assertFalse(session.merchandising_available())
            return
        self.skipTest("no offer came through — RNG variance, not a bug")

    def test_a_live_action_franchise_role_cannot_negotiate_merchandising(self):
        from dataclasses import replace
        session = Session(seed=202)
        session.start("conservatory", "work")
        self.assertTrue(self._get_to_prep_with_standing(session))
        session._role = replace(session._role, is_animation=False, franchise_id="fr_live_action")
        self.assertFalse(session.merchandising_available())


class TestSessionFranchiseIntegration(unittest.TestCase):
    def test_franchise_status_and_holdout_are_plain_data(self):
        session = Session(seed=2026)
        session.start("conservatory", "work")
        for f in session.franchise_status():
            self.assertIsInstance(f["id"], str)
            self.assertIsInstance(f["indispensability"], float)
        self.assertFalse(session.holdout_available())  # nothing accepted yet

    def test_a_full_run_can_produce_a_tracked_franchise(self):
        session = Session(seed=2026)
        session.start("conservatory", "work")
        for _ in range(15):
            if session.is_over():
                break
            board = session.offer_board()
            available = [o for o in board if o["available"]]
            if not available:
                session.decline_board()
                continue
            session.accept(available[0]["index"])
            if session.holdout_available():
                session.request_holdout()
            if session._role is None:
                continue  # a failed holdout got the part recast — no project this year
            session.choose_deal(False)
            session.choose_prep("table_work")
            for _ in range(3):
                session.play_scene({d: "with" for d, _ in session.dial_options()})
            session.choose_release("wide")
        # not asserting a franchise necessarily formed (RNG-dependent) — just that the run didn't crash
        # and franchise_status() stays plain data throughout.
        for f in session.franchise_status():
            self.assertIsInstance(f["genre"], str)

    def test_a_pruned_pending_spinoff_does_not_crash_the_next_offer_board(self):
        # A signed multi-picture deal takes the guaranteed slot over a spin-off launched the same
        # year (_guaranteed_listing's own documented priority) — the spin-off's own franchise entry
        # never gets "touched" that year, and decay_dormant_franchises() prunes an untouched,
        # still-zero-indispensability entry. The dangling _pending_spinoff_franchise_id pointer used
        # to crash the very next offer_board() with a KeyError; it should now just no-op instead.
        session = Session(seed=99)
        session.start("conservatory", "work")
        session._pending_spinoff_franchise_id = "fr_spinoff_does_not_exist"
        listings = session.offer_board()  # must not raise
        self.assertIsNone(session._pending_spinoff_franchise_id)
        self.assertGreater(len(listings), 0)


if __name__ == "__main__":
    unittest.main()
