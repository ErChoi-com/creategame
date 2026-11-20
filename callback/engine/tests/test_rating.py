"""actor/rating.py (§5.19 — the content rating) and studios.decide_rating_cut() — the studio's own
pressure on a genuine borderline film's rating.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.rating import (
    ANIMATION_RATING_OFFSET,
    BOUNDARY_MARGIN,
    RATING_CUT,
    RATING_RELEASE_AS_SHOT,
    friendlier_band,
    near_boundary,
    nearest_boundary_distance,
    rating_band,
    rating_score,
)
from callback.engine.actor.studios import (
    STUDIOS,
    decide_rating_cut,
    effective_rating_ceiling,
)


class TestRatingScoreAndBands(unittest.TestCase):
    def test_band_boundaries(self):
        self.assertEqual(rating_band(-30.0), "G")
        self.assertEqual(rating_band(-25.1), "G")
        self.assertEqual(rating_band(-24.9), "PG")
        self.assertEqual(rating_band(-0.1), "PG")
        self.assertEqual(rating_band(0.1), "PG-13")
        self.assertEqual(rating_band(24.9), "PG-13")
        self.assertEqual(rating_band(25.1), "R")
        self.assertEqual(rating_band(49.9), "R")
        self.assertEqual(rating_band(50.1), "NC-17")

    def test_genre_baseline_makes_identical_intensity_read_differently(self):
        """The doc's own headline claim: the same Intensity dial setting reads a harder rating in
        horror than in thriller, because the genre baseline is doing real work, not excuse-making."""
        intensity = 20.0
        horror_score = rating_score(intensity, "horror")
        thriller_score = rating_score(intensity, "thriller")
        self.assertGreater(horror_score, thriller_score)
        self.assertNotEqual(rating_band(horror_score), rating_band(thriller_score))

    def test_family_genre_pulls_the_score_down(self):
        intensity = 0.0
        self.assertLess(rating_score(intensity, "family"), rating_score(intensity, "drama"))

    def test_animation_pulls_the_score_down_at_the_same_intensity_and_genre(self):
        intensity = 10.0
        live_action = rating_score(intensity, "horror", is_animation=False)
        animated = rating_score(intensity, "horror", is_animation=True)
        self.assertAlmostEqual(animated, live_action + ANIMATION_RATING_OFFSET)
        self.assertLess(animated, live_action)

    def test_animation_composes_additively_with_genre_not_instead_of_it(self):
        # An animated horror film still reads more intense than an animated family comedy at the
        # same Intensity dial — animation shifts the baseline, it doesn't erase the genre's own.
        intensity = 10.0
        animated_horror = rating_score(intensity, "horror", is_animation=True)
        animated_family = rating_score(intensity, "family", is_animation=True)
        self.assertGreater(animated_horror, animated_family)

    def test_near_boundary_only_true_within_margin(self):
        # PG-13/R boundary sits at 25.0.
        self.assertTrue(near_boundary(25.0 - BOUNDARY_MARGIN))
        self.assertTrue(near_boundary(25.0 + BOUNDARY_MARGIN))
        self.assertFalse(near_boundary(25.0 - BOUNDARY_MARGIN - 0.1))
        self.assertFalse(near_boundary(25.0 + BOUNDARY_MARGIN + 0.1))

    def test_far_from_any_boundary_is_not_near(self):
        # Deep inside PG-13, nowhere near 0 or 25.
        self.assertFalse(near_boundary(12.5))

    def test_friendlier_band_only_moves_one_step_toward_the_nearer_boundary(self):
        score = 27.0  # R, just past the R boundary at 25.0
        self.assertEqual(rating_band(score), "R")
        self.assertEqual(friendlier_band(score), "PG-13")

    def test_friendlier_band_never_moves_below_g(self):
        self.assertEqual(friendlier_band(-40.0), "G")

    def test_nearest_boundary_distance_is_symmetric_around_a_boundary(self):
        self.assertAlmostEqual(nearest_boundary_distance(25.0 - 3.0), 3.0)
        self.assertAlmostEqual(nearest_boundary_distance(25.0 + 3.0), 3.0)


class TestEffectiveRatingCeiling(unittest.TestCase):
    def test_base_ceiling_is_the_studios_own(self):
        self.assertEqual(effective_rating_ceiling(STUDIOS["prestige"], 20.0, False), "NC-17")
        self.assertEqual(effective_rating_ceiling(STUDIOS["blockbuster"], 20.0, False), "PG-13")

    def test_tentpole_budget_clamps_any_studio_to_pg13(self):
        # Even the most rating-tolerant studio identity in the table blanches at a $150M film.
        self.assertEqual(effective_rating_ceiling(STUDIOS["prestige"], 150.0, False), "PG-13")
        self.assertEqual(effective_rating_ceiling(STUDIOS["indie"], 150.0, False), "PG-13")

    def test_franchise_tightens_ceiling_by_one_step(self):
        base = effective_rating_ceiling(STUDIOS["mid_major"], 20.0, False)
        franchise = effective_rating_ceiling(STUDIOS["mid_major"], 20.0, True)
        self.assertEqual(base, "R")
        self.assertEqual(franchise, "PG-13")

    def test_ceiling_never_drops_below_the_bands_own_floor(self):
        # A studio already at G-equivalent tolerance plus every tightening factor still resolves
        # to a real band, not an index error.
        self.assertIn(effective_rating_ceiling(STUDIOS["blockbuster"], 150.0, True), ("G", "PG"))


class TestDecideRatingCut(unittest.TestCase):
    def test_no_pressure_when_studio_ceiling_not_exceeded(self):
        rng = random.Random(1)
        # mid_major's ceiling is R; a PG-13 film never triggers studio pressure.
        decision = decide_rating_cut(
            STUDIOS["mid_major"], score=10.0, film_budget_millions=20.0,
            is_franchise_or_adaptation=False, requested_stance=RATING_RELEASE_AS_SHOT,
            trust=50.0, importance=50.0, rng=rng,
        )
        self.assertFalse(decision.studio_wanted_cut)
        self.assertFalse(decision.forced)
        self.assertEqual(decision.actual_stance, RATING_RELEASE_AS_SHOT)

    def test_top_tier_importance_holds_the_line_against_pressure(self):
        rng = random.Random(0)
        # blockbuster's ceiling is PG-13; a real R-band score (score=30) exceeds it on a tentpole.
        decision = decide_rating_cut(
            STUDIOS["blockbuster"], score=30.0, film_budget_millions=150.0,
            is_franchise_or_adaptation=False, requested_stance=RATING_RELEASE_AS_SHOT,
            trust=80.0, importance=99.0, rng=rng,
        )
        self.assertTrue(decision.studio_wanted_cut)
        self.assertFalse(decision.forced)
        self.assertEqual(decision.actual_stance, RATING_RELEASE_AS_SHOT)

    def test_nobody_importance_gets_forced(self):
        rng = random.Random(3)
        decision = decide_rating_cut(
            STUDIOS["blockbuster"], score=30.0, film_budget_millions=150.0,
            is_franchise_or_adaptation=False, requested_stance=RATING_RELEASE_AS_SHOT,
            trust=20.0, importance=1.0, rng=rng,
        )
        self.assertTrue(decision.studio_wanted_cut)
        self.assertTrue(decision.forced)
        self.assertEqual(decision.actual_stance, RATING_CUT)

    def test_forced_outcome_is_always_the_cut_never_the_requested_stance(self):
        rng = random.Random(4)
        decision = decide_rating_cut(
            STUDIOS["blockbuster"], score=30.0, film_budget_millions=150.0,
            is_franchise_or_adaptation=False, requested_stance=RATING_CUT,
            trust=20.0, importance=1.0, rng=rng,
        )
        self.assertEqual(decision.requested_stance, RATING_CUT)
        self.assertEqual(decision.actual_stance, RATING_CUT)
        self.assertTrue(decision.forced)

    def test_forced_vs_requested_split_tracks_the_shared_influence_curve(self):
        """Same shape as the rest of the engine's studio-negotiation tests: sweep importance at
        fixed trust and confirm the forced/held split moves the direction actor_influence_on_
        studio_decision() says it should — reusing that curve, not a second one."""
        rng = random.Random(5)
        low_importance_forced = 0
        high_importance_forced = 0
        trials = 200
        for _ in range(trials):
            d = decide_rating_cut(
                STUDIOS["blockbuster"], score=30.0, film_budget_millions=150.0,
                is_franchise_or_adaptation=False, requested_stance=RATING_RELEASE_AS_SHOT,
                trust=50.0, importance=5.0, rng=rng,
            )
            low_importance_forced += d.forced
        for _ in range(trials):
            d = decide_rating_cut(
                STUDIOS["blockbuster"], score=30.0, film_budget_millions=150.0,
                is_franchise_or_adaptation=False, requested_stance=RATING_RELEASE_AS_SHOT,
                trust=50.0, importance=98.0, rng=rng,
            )
            high_importance_forced += d.forced
        self.assertGreater(low_importance_forced, high_importance_forced)

    def test_uses_supplied_influence_fn(self):
        rng = random.Random(6)
        decision = decide_rating_cut(
            STUDIOS["blockbuster"], score=30.0, film_budget_millions=150.0,
            is_franchise_or_adaptation=False, requested_stance=RATING_RELEASE_AS_SHOT,
            trust=50.0, importance=50.0, rng=rng,
            influence_fn=lambda trust, importance: 1.0,  # always holds
        )
        self.assertFalse(decision.forced)


if __name__ == "__main__":
    unittest.main()
