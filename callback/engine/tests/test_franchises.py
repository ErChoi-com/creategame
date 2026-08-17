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
    FranchiseEntry,
    SEQUEL_CHANCE_BASE,
    SEQUEL_CHANCE_CEILING,
    SPINOFF_INDISPENSABILITY_THRESHOLD,
    create_spinoff_entry,
    director_continuity_bonus,
    franchise_audience_bonus,
    maybe_attach_franchise,
    sequel_probability,
    spinoff_available,
    update_franchise_after_project,
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
        franchises = decay_dormant_franchises({"fr_009_spinoff": entry}, current_year=20)
        self.assertIn("fr_009_spinoff", franchises)


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


if __name__ == "__main__":
    unittest.main()
