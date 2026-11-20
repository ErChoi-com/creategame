"""awards/ behaviour: narrative bonuses, buzz score, vote splitting, category resolution."""
from __future__ import annotations

import random
import unittest

from callback.engine.awards.awards import (
    AWARD_CATEGORIES,
    AWARD_CEILING_CAP,
    BREAKTHROUGH,
    BREAKTHROUGH_CREDITS_MAX,
    DIRECTOR,
    ENSEMBLE,
    GENRE_EXCELLENCE,
    GENRE_EXCELLENCE_GENRES,
    LEAD_COMEDY,
    LEAD_DRAMA,
    SUPPORTING,
    VOICE_PERFORMANCE,
    NarrativeContext,
    apply_award_ceiling,
    apply_vote_splitting,
    award_ceiling,
    award_win_bonus,
    buzz_score,
    category_fraud,
    eligible_performance_categories,
    ensemble_buzz_score,
    narrative_bonus,
    resolve_category,
)


class TestNarrativeBonus(unittest.TestCase):
    def test_shes_due_applies(self):
        ctx = NarrativeContext(prior_nominations=4, prior_wins=0)
        self.assertEqual(narrative_bonus(ctx), 14.0)

    def test_posthumous_dominates_other_flags(self):
        ctx = NarrativeContext(prior_nominations=4, prior_wins=0, posthumous=True)
        self.assertEqual(narrative_bonus(ctx), 20.0)

    def test_no_flags_is_zero(self):
        self.assertEqual(narrative_bonus(NarrativeContext()), 0.0)

    def test_negative_bonus_applies_when_overexposed(self):
        ctx = NarrativeContext(credits_this_season=5)
        self.assertEqual(narrative_bonus(ctx), -7.0)


class TestBuzzAndVoting(unittest.TestCase):
    def test_higher_spotlight_gives_higher_buzz_on_average(self):
        rng_a, rng_b = random.Random(1), random.Random(1)
        low = buzz_score(30, 50, 1.0, 50, 0, 0, rng_a)
        high = buzz_score(90, 50, 1.0, 50, 0, 0, rng_b)
        self.assertGreater(high, low)

    def test_vote_splitting_penalizes_both_same_film_nominees(self):
        scores = {"a": 60.0, "b": 55.0, "c": 40.0}
        updated = apply_vote_splitting(scores, ["a", "b"])
        self.assertLess(updated["a"], scores["a"])
        self.assertLess(updated["b"], scores["b"])
        self.assertEqual(updated["c"], scores["c"])

    def test_resolve_category_picks_the_highest(self):
        scores = {"a": 60.0, "b": 90.0, "c": 40.0}
        self.assertEqual(resolve_category(scores, random.Random(1)), "b")


class TestAwardCeiling(unittest.TestCase):
    def test_drama_showcase_has_the_highest_ceiling(self):
        self.assertEqual(award_ceiling("drama", "showcase"), AWARD_CEILING_CAP["highest"])

    def test_horror_caps_well_below_drama_regardless_of_depth(self):
        self.assertLess(award_ceiling("horror", "showcase"), award_ceiling("drama", "showcase"))

    def test_underwritten_hard_caps_even_in_a_highest_ceiling_genre(self):
        self.assertLess(award_ceiling("drama", "underwritten"), AWARD_CEILING_CAP["very_low"])

    def test_genre_and_depth_gates_are_independent_the_tighter_one_wins(self):
        # A showcase role in a low-ceiling genre should still land at the GENRE cap, not the
        # depth cap — depth never raises a genre's own ceiling above what §9.1 allows it.
        self.assertEqual(award_ceiling("horror", "showcase"), AWARD_CEILING_CAP["very_low"])

    def test_every_genre_in_the_roster_has_a_defined_ceiling(self):
        from callback.engine.actor.persona import GENRES
        for genre in GENRES:
            self.assertGreater(award_ceiling(genre, "standard"), 0.0)

    def test_apply_award_ceiling_never_exceeds_the_cap(self):
        capped = apply_award_ceiling(99.0, "horror", "underwritten")
        self.assertEqual(capped, award_ceiling("horror", "underwritten"))

    def test_apply_award_ceiling_leaves_a_buzz_already_under_cap_untouched(self):
        self.assertEqual(apply_award_ceiling(10.0, "drama", "showcase"), 10.0)

    def test_genre_excellence_bypasses_horrors_own_prestige_ceiling(self):
        # The entire real-world reason Saturn Awards exist: a horror performance shouldn't be
        # judged against drama's own ceiling on ITS circuit.
        prestige_ceiling = award_ceiling("horror", "showcase")
        genre_excellence_ceiling = award_ceiling("horror", "showcase", category=GENRE_EXCELLENCE)
        self.assertGreater(genre_excellence_ceiling, prestige_ceiling)

    def test_voice_performance_bypasses_the_genre_ceiling_too(self):
        prestige_ceiling = award_ceiling("family", "showcase")
        voice_ceiling = award_ceiling("family", "showcase", category=VOICE_PERFORMANCE)
        self.assertGreater(voice_ceiling, prestige_ceiling)

    def test_second_circuit_is_still_gated_by_role_depth(self):
        # Bypassing the genre penalty isn't a free pass — a genuinely thin genre role still caps
        # hard, same as it would on the prestige circuit.
        self.assertLess(
            award_ceiling("horror", "underwritten", category=GENRE_EXCELLENCE),
            award_ceiling("horror", "showcase", category=GENRE_EXCELLENCE),
        )

    def test_second_circuit_is_not_as_high_as_the_prestige_circuits_own_highest(self):
        self.assertLess(award_ceiling("horror", "showcase", category=GENRE_EXCELLENCE), AWARD_CEILING_CAP["highest"])


class TestCategoryFraud(unittest.TestCase):
    def test_advantage_is_always_the_flat_constant(self):
        for seed in range(20):
            advantage, _caught, _notoriety = category_fraud(random.Random(seed))
            self.assertEqual(advantage, 18.0)

    def test_caught_always_carries_a_real_notoriety_cost(self):
        for seed in range(50):
            _advantage, caught, notoriety = category_fraud(random.Random(seed))
            if caught:
                self.assertGreater(notoriety, 0.0)
            else:
                self.assertEqual(notoriety, 0.0)

    def test_gets_caught_sometimes_and_not_others_over_many_rolls(self):
        rng = random.Random(7)
        results = {category_fraud(rng)[1] for _ in range(100)}
        self.assertEqual(results, {True, False})


class TestEligiblePerformanceCategories(unittest.TestCase):
    def test_lead_drama_role(self):
        cats = eligible_performance_categories("drama", "lead", credits=10)
        self.assertIn(LEAD_DRAMA, cats)
        self.assertNotIn(LEAD_COMEDY, cats)
        self.assertNotIn(SUPPORTING, cats)

    def test_lead_comedy_and_musical_share_the_comedy_lane(self):
        self.assertIn(LEAD_COMEDY, eligible_performance_categories("comedy", "lead", credits=10))
        self.assertIn(LEAD_COMEDY, eligible_performance_categories("musical", "lead", credits=10))

    def test_supporting_is_genre_blind_unlike_lead(self):
        # The real Globes/Oscar asymmetry: Lead splits by genre, Supporting never does.
        drama_supporting = eligible_performance_categories("drama", "supporting", credits=10)
        comedy_supporting = eligible_performance_categories("comedy", "supporting", credits=10)
        self.assertEqual(drama_supporting, comedy_supporting)
        self.assertIn(SUPPORTING, drama_supporting)

    def test_bit_and_extra_billing_get_no_personal_lane(self):
        cats = eligible_performance_categories("drama", "bit", credits=10)
        self.assertNotIn(LEAD_DRAMA, cats)
        self.assertNotIn(SUPPORTING, cats)

    def test_ensemble_is_always_eligible(self):
        for billing in ("lead", "supporting", "bit", "extra"):
            self.assertIn(ENSEMBLE, eligible_performance_categories("drama", billing, credits=10))

    def test_breakthrough_gated_to_early_career(self):
        self.assertIn(BREAKTHROUGH, eligible_performance_categories("drama", "lead", credits=BREAKTHROUGH_CREDITS_MAX))
        self.assertNotIn(BREAKTHROUGH, eligible_performance_categories("drama", "lead", credits=BREAKTHROUGH_CREDITS_MAX + 1))

    def test_genre_excellence_is_a_second_circuit_not_a_replacement(self):
        # A horror lead is a real (if long-shot) Lead-Drama contender AND a real Genre Excellence
        # contender — Saturn and Oscar nominations aren't mutually exclusive in real awards season.
        cats = eligible_performance_categories("horror", "lead", credits=10)
        self.assertIn(LEAD_DRAMA, cats)
        self.assertIn(GENRE_EXCELLENCE, cats)

    def test_genre_excellence_covers_the_real_saturn_scope_only(self):
        for genre in GENRE_EXCELLENCE_GENRES:
            self.assertIn(GENRE_EXCELLENCE, eligible_performance_categories(genre, "supporting", credits=10))
        # romance/family are real low-ceiling genres but have no real second circuit — they stay
        # prestige-circuit-only, unlike horror/scifi/fantasy/superhero/action.
        self.assertNotIn(GENRE_EXCELLENCE, eligible_performance_categories("romance", "supporting", credits=10))
        self.assertNotIn(GENRE_EXCELLENCE, eligible_performance_categories("family", "supporting", credits=10))

    def test_genre_excellence_not_eligible_for_bit_or_extra(self):
        cats = eligible_performance_categories("horror", "bit", credits=10)
        self.assertNotIn(GENRE_EXCELLENCE, cats)

    def test_voice_performance_only_for_animation(self):
        live_action = eligible_performance_categories("family", "lead", credits=10, is_animation=False)
        animated = eligible_performance_categories("family", "lead", credits=10, is_animation=True)
        self.assertNotIn(VOICE_PERFORMANCE, live_action)
        self.assertIn(VOICE_PERFORMANCE, animated)

    def test_animation_goes_to_voice_performance_not_genre_excellence_even_in_a_saturn_genre(self):
        # An animated horror film campaigns Voice Performance (Annie's own scope), not Genre
        # Excellence (Saturn's) — the two circuits don't overlap on the same role.
        cats = eligible_performance_categories("horror", "lead", credits=10, is_animation=True)
        self.assertIn(VOICE_PERFORMANCE, cats)
        self.assertNotIn(GENRE_EXCELLENCE, cats)


class TestEnsembleBuzzScore(unittest.TestCase):
    def test_film_quality_moves_it_more_than_your_own_spotlight(self):
        rng_a, rng_b = random.Random(1), random.Random(1)
        low_film = ensemble_buzz_score(film_critic_score=30, project_quality=30, your_spotlight=95, campaign_spend=2.0, rng=rng_a)
        high_film = ensemble_buzz_score(film_critic_score=90, project_quality=90, your_spotlight=30, campaign_spend=2.0, rng=rng_b)
        self.assertGreater(high_film, low_film)

    def test_stays_in_bounds(self):
        rng = random.Random(2)
        for _ in range(50):
            score = ensemble_buzz_score(rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 100), rng.uniform(0, 3), rng)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 100.0)


class TestAwardWinBonus(unittest.TestCase):
    def test_every_category_has_a_defined_bonus(self):
        for category in AWARD_CATEGORIES:
            meter, delta = award_win_bonus(category)
            self.assertIn(meter, ("heat", "prestige", "affection", "notoriety"))
            self.assertGreater(delta, 0.0)

    def test_bonuses_stay_small(self):
        """§ the request this pass answers — "nothing too significant." Every win bonus should
        read as a small nudge on a 0-100 meter, not a swing."""
        for category in AWARD_CATEGORIES:
            _meter, delta = award_win_bonus(category)
            self.assertLessEqual(delta, 5.0)

    def test_ensemble_moves_affection_breakthrough_moves_heat(self):
        self.assertEqual(award_win_bonus(ENSEMBLE)[0], "affection")
        self.assertEqual(award_win_bonus(BREAKTHROUGH)[0], "heat")
        self.assertEqual(award_win_bonus(DIRECTOR)[0], "prestige")

    def test_supporting_bonus_is_smaller_than_lead(self):
        self.assertLess(award_win_bonus(SUPPORTING)[1], award_win_bonus(LEAD_DRAMA)[1])

    def test_genre_excellence_and_voice_performance_move_prestige_but_less_than_lead(self):
        self.assertEqual(award_win_bonus(GENRE_EXCELLENCE)[0], "prestige")
        self.assertEqual(award_win_bonus(VOICE_PERFORMANCE)[0], "prestige")
        self.assertLess(award_win_bonus(GENRE_EXCELLENCE)[1], award_win_bonus(LEAD_DRAMA)[1])
        self.assertLess(award_win_bonus(VOICE_PERFORMANCE)[1], award_win_bonus(LEAD_DRAMA)[1])


if __name__ == "__main__":
    unittest.main()
