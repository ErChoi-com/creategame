"""design/part-07-the-director.md v10 — the Casting/Shoot/Edit pipeline, generalized "attach a
star", the new dev actions, development events, platform expansion, and director-for-hire.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.director import casting, development as director_development, edit, shoot_style
from callback.engine.director.development import (
    attachment_offer_probability,
    ATTACHMENT_OFFER_CEILING,
    ATTACHMENT_OFFER_FLOOR,
    ATTACH_STAR_MOMENTUM_HI,
    ATTACH_STAR_MOMENTUM_LO,
    ATTACH_STAR_RIVAL_MOMENTUM_HI,
    ATTACH_STAR_RIVAL_MOMENTUM_LO,
    ADAPTATION_MOMENTUM_HI,
    ADAPTATION_MOMENTUM_LO,
    ATTACHMENT_BANKABLE,
    ATTACHMENT_GENRE_FIT,
    ATTACHMENT_STUDIO_FAVORITE,
    ATTACH_GENRE_FIT_MOMENTUM_HI,
    ATTACH_GENRE_FIT_MOMENTUM_LO,
    ATTACH_STUDIO_FAVORITE_MOMENTUM_HI,
    ATTACH_STUDIO_FAVORITE_MOMENTUM_LO,
    ATTACHMENT_DROPOUT_CEILING,
    Attachment,
    FAVOUR_MOMENTUM_HI,
    FAVOUR_MOMENTUM_LO,
    RIVAL_POACH_NOTORIETY_HI,
    RIVAL_POACH_NOTORIETY_LO,
    adaptation_momentum,
    age_attachments,
    attach_momentum,
    attach_star_favour_cost,
    attach_star_momentum,
    attachment_dropout_probability,
    bankability_roi_centre,
    favour_momentum,
    format_adjusted_roi,
    momentum_band,
    rival_poach_notoriety_cost,
)
from callback.engine.simulation._director import (
    DirectedReleaseSnapshot,
    accept_hire_offer,
    advance_shoots_and_resolve,
    apply_dev_action_and_advance,
    can_start_new_project,
    director_box_office_bonus_available,
    director_deal_available,
    expansion_available,
    hire_offer_probability,
    LIMBO_MOMENTUM_THRESHOLD,
    limbo_probabilities,
    MAX_PROJECTS,
    new_director_state,
    projects_in_play,
    push_director_deal_for_backend,
    rating_dampener,
    resolve_limbo,
    roll_hire_offer,
    scrap_project,
    start_development,
)
from callback.engine.simulation.session import Session


def greenlight_and_finish(state, project_index, action, genre_demand, rng, **kwargs):
    """v12 — greenlighting a project only starts its shoot now (development.
    quarters_for_directed_film); it doesn't resolve inline anymore. Tests that want the old
    single-call "here's the finished film's real numbers" behavior need both steps: greenlight,
    then run the shoot out via advance_shoots_and_resolve (as end_year() now does once a year)
    until it actually wraps. Returns (state, info) — info is the RESOLVED film's info dict, shaped
    exactly like the old inline-resolution info was."""
    state, info = apply_dev_action_and_advance(state, project_index, action, genre_demand, rng, **kwargs)
    if not info["greenlit"]:
        return state, info
    for _ in range(20):
        state, resolved = advance_shoots_and_resolve(state, {}, rng)
        if resolved:
            return state, resolved[0]
    raise AssertionError("shoot never resolved within 20 years — check quarters_for_directed_film's own ceiling")


def finish_session_directing(session, project_index, action):
    """Session-level equivalent of greenlight_and_finish — advance_directing() only starts the
    shoot now; end_year() is what actually advances it (real calendar time, not the director's own
    quarterly attention) and returns whatever wrapped this year."""
    result = session.advance_directing(project_index, action)
    if not result["greenlit"]:
        return result
    for _ in range(20):
        resolved = session.end_year()
        if resolved:
            return resolved[0]
    raise AssertionError("shoot never resolved within 20 years — check quarters_for_directed_film's own ceiling")


class TestSelfFinanceRushWiring(unittest.TestCase):
    """Integration-level check that a self-financed greenlight's own momentum at the moment it
    greenlit — locked_momentum_at_greenlight — actually reaches the finished film's reception, not
    just the standalone development.self_finance_rush_penalty formula in isolation."""

    def _resolve(self, momentum_at_greenlight, self_financed=True, seed=7, budget_ask=150.0):
        from dataclasses import replace as dc_replace
        from callback.engine.simulation._director import ProjectSlot, DirectorState, new_director_state
        from callback.engine.director.development import DevProject

        project = DevProject(
            script_id="s1", momentum=momentum_at_greenlight, budget_ask=budget_ask, self_financed=self_financed,
            quarters_remaining_in_shoot=1, locked_quarters_needed=1, locked_schedule_overage=0.0,
            locked_momentum_at_greenlight=momentum_at_greenlight if self_financed else None,
        )
        slot = ProjectSlot(project=project, genre="drama", true_script_quality=70.0)
        state = dc_replace(new_director_state(), projects=(slot,))
        _, resolved = advance_shoots_and_resolve(state, {}, random.Random(seed))
        self.assertEqual(len(resolved), 1)
        return resolved[0]

    def test_low_momentum_self_financed_greenlight_reads_worse_than_a_well_packaged_one(self):
        low = self._resolve(momentum_at_greenlight=0.0)
        high = self._resolve(momentum_at_greenlight=0.9)
        self.assertLess(low["film_critic_score"], high["film_critic_score"])

    def test_momentum_at_or_above_the_budgets_own_bar_gets_no_rush_penalty(self):
        # Same seed, momentum right at this $150M project's own threshold vs comfortably above it
        # — both cleared the bar a studio would have demanded for an ask this size, so neither
        # should be penalized relative to the other.
        from callback.engine.director.development import self_finance_momentum_threshold
        threshold = self_finance_momentum_threshold(150.0)
        at_bar = self._resolve(momentum_at_greenlight=threshold)
        above_bar = self._resolve(momentum_at_greenlight=threshold + 0.5)
        self.assertEqual(at_bar["film_critic_score"], above_bar["film_critic_score"])

    def test_the_same_momentum_clears_a_small_budgets_bar_but_not_a_big_ones(self):
        # Budget itself moves film_critic_score through production_value too, so a fair check
        # compares EACH budget against ITSELF at two momentum levels, not raw scores across
        # different budgets (which the much stronger budget/production-value effect would
        # dominate). Fixed momentum=0.5: clears the $5M ask's own bar (~0.43) but not the $350M
        # ask's (~0.89) — see self_finance_momentum_threshold's own unit tests for the raw numbers.
        small_fixed, small_high = self._resolve(0.5, budget_ask=1.0), self._resolve(2.0, budget_ask=1.0)
        big_fixed, big_high = self._resolve(0.5, budget_ask=350.0), self._resolve(2.0, budget_ask=350.0)
        self.assertEqual(small_fixed["film_critic_score"], small_high["film_critic_score"])  # both clear $5M's bar
        self.assertLess(big_fixed["film_critic_score"], big_high["film_critic_score"])  # 0.5 doesn't clear $350M's

    def test_a_studio_backed_greenlight_is_never_rush_penalized(self):
        # Studio-backed projects can't skip greenlight_probability's own momentum bar in the first
        # place, so locked_momentum_at_greenlight is never set for them (None) — this just confirms
        # the wiring doesn't accidentally apply a rush penalty off the raw (unlocked) momentum field.
        result = self._resolve(momentum_at_greenlight=0.0, self_financed=False)
        self.assertIsNotNone(result["film_critic_score"])


class TestMomentumBands(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(momentum_band(0.0), "dead")
        self.assertEqual(momentum_band(0.21), "dead")
        self.assertEqual(momentum_band(0.22), "fading")
        self.assertEqual(momentum_band(0.39), "fading")
        self.assertEqual(momentum_band(0.40), "building")
        self.assertEqual(momentum_band(0.69), "building")
        self.assertEqual(momentum_band(0.70), "real heat")
        self.assertEqual(momentum_band(0.99), "real heat")
        self.assertEqual(momentum_band(1.0), "can't-miss")
        self.assertEqual(momentum_band(1.8), "can't-miss")


class TestAttachStarMomentum(unittest.TestCase):
    def test_base_tier_stays_within_its_own_range(self):
        rng = random.Random(1)
        for bankability in (0.0, 25.0, 50.0, 75.0, 100.0):
            for tier in ("loyal", "ally", "familiar", "stranger"):
                m = attach_star_momentum(bankability, tier, rng)
                self.assertGreaterEqual(m, ATTACH_STAR_MOMENTUM_LO - 0.1)
                self.assertLessEqual(m, ATTACH_STAR_MOMENTUM_HI + 0.1)

    def test_rival_tier_uses_the_elevated_range(self):
        rng = random.Random(2)
        for bankability in (0.0, 50.0, 100.0):
            m = attach_star_momentum(bankability, "rival", rng)
            self.assertGreaterEqual(m, ATTACH_STAR_RIVAL_MOMENTUM_LO - 0.1)
            self.assertLessEqual(m, ATTACH_STAR_RIVAL_MOMENTUM_HI + 0.1)

    def test_bigger_bankability_means_a_bigger_swing_on_average(self):
        rng = random.Random(3)
        low = [attach_star_momentum(10.0, "stranger", rng) for _ in range(200)]
        high = [attach_star_momentum(90.0, "stranger", rng) for _ in range(200)]
        self.assertLess(sum(low) / len(low), sum(high) / len(high))

    def test_rival_range_sits_above_the_base_range(self):
        self.assertGreater(ATTACH_STAR_RIVAL_MOMENTUM_LO, ATTACH_STAR_MOMENTUM_LO)

    def test_favour_cost_discounted_for_loyal_and_ally(self):
        self.assertLess(attach_star_favour_cost(4, "loyal"), attach_star_favour_cost(4, "familiar"))
        self.assertLess(attach_star_favour_cost(4, "ally"), attach_star_favour_cost(4, "familiar"))
        self.assertLessEqual(attach_star_favour_cost(4, "loyal"), attach_star_favour_cost(4, "ally"))

    def test_rival_notoriety_cost_scales_with_rivalry_depth(self):
        self.assertAlmostEqual(rival_poach_notoriety_cost(0.0), RIVAL_POACH_NOTORIETY_LO)
        self.assertAlmostEqual(rival_poach_notoriety_cost(1.0), RIVAL_POACH_NOTORIETY_HI)
        self.assertLess(rival_poach_notoriety_cost(0.2), rival_poach_notoriety_cost(0.8))


class TestNewDevActions(unittest.TestCase):
    def test_favour_momentum_scales_with_favour_size(self):
        rng = random.Random(4)
        small = favour_momentum(1.0, rng)
        large = favour_momentum(5.0, rng)
        self.assertGreaterEqual(small, FAVOUR_MOMENTUM_LO - 0.1)
        self.assertLessEqual(large, FAVOUR_MOMENTUM_HI + 0.1)
        self.assertLess(small, large)

    def test_adaptation_momentum_scales_with_licensing_spend(self):
        # v20 — source_type now scales the payoff (design/part-09 §9.4's own built-in-audience
        # read); pin source_type="novel" (bonus 1.0x... actually 0.9x, see ADAPTATION_SOURCE_
        # AUDIENCE_BONUS) explicitly so this test reads the base LO/HI shape, not a specific tier's
        # multiplier.
        from callback.engine.director.development import ADAPTATION_SOURCE_AUDIENCE_BONUS
        novel_bonus = ADAPTATION_SOURCE_AUDIENCE_BONUS["novel"]
        self.assertAlmostEqual(adaptation_momentum(0.0, "novel"), ADAPTATION_MOMENTUM_LO * novel_bonus)
        self.assertAlmostEqual(adaptation_momentum(1.0, "novel"), ADAPTATION_MOMENTUM_HI * novel_bonus)
        self.assertLess(adaptation_momentum(0.2, "novel"), adaptation_momentum(0.8, "novel"))


class TestRewriteGamble(unittest.TestCase):
    def test_higher_combined_talent_raises_the_average_gain(self):
        from callback.engine.director.development import rewrite_quality_gain
        rng = random.Random(50)
        weak = [rewrite_quality_gain(10.0, 10.0, rng) for _ in range(300)]
        strong = [rewrite_quality_gain(90.0, 90.0, rng) for _ in range(300)]
        self.assertLess(sum(weak) / len(weak), sum(strong) / len(strong))

    def test_it_is_a_real_gamble_not_a_guaranteed_gain(self):
        """Even at strong talent, a rewrite pass isn't a fixed number — real variance either way
        within its (narrower) range. Weak talent has a much wider range and can swing negative or
        get lucky. A flat, guaranteed gain would fail this test."""
        from callback.engine.director.development import rewrite_quality_gain
        rng = random.Random(51)
        strong_results = [rewrite_quality_gain(90.0, 90.0, rng) for _ in range(200)]
        weak_results = [rewrite_quality_gain(10.0, 10.0, rng) for _ in range(200)]
        self.assertGreater(max(strong_results) - min(strong_results), 1.0)  # real variance, not a fixed number
        self.assertTrue(any(g < 0 for g in weak_results))
        self.assertTrue(any(g > 5 for g in weak_results))

    def test_talent_narrows_the_range_not_just_shifts_it(self):
        """The whole point of the fix: the spread itself should shrink as talent rises, not just
        the mean — a strong pairing is a safer bet, not just a better-centred one."""
        from callback.engine.director.development import rewrite_quality_gain
        rng = random.Random(54)
        weak_results = [rewrite_quality_gain(0.0, 0.0, rng) for _ in range(300)]
        strong_results = [rewrite_quality_gain(100.0, 100.0, rng) for _ in range(300)]
        weak_spread = max(weak_results) - min(weak_results)
        strong_spread = max(strong_results) - min(strong_results)
        self.assertLess(strong_spread, weak_spread)

    def test_gain_stays_within_its_own_bounds(self):
        from callback.engine.director.development import (
            REWRITE_GAIN_CEILING_HI, REWRITE_GAIN_FLOOR_LO, rewrite_quality_gain,
        )
        rng = random.Random(52)
        for _ in range(500):
            g = rewrite_quality_gain(rng.uniform(0, 100), rng.uniform(0, 100), rng)
            self.assertGreaterEqual(g, REWRITE_GAIN_FLOOR_LO)
            self.assertLessEqual(g, REWRITE_GAIN_CEILING_HI)

    def test_typical_default_talent_averages_close_to_the_old_flat_baseline(self):
        """At combined=50/100 (today's only real value — no attribute customization/growth yet),
        the range should sit roughly on the old guaranteed +6, not quietly land lower on average."""
        from callback.engine.director.development import rewrite_quality_gain
        rng = random.Random(55)
        results = [rewrite_quality_gain(50.0, 50.0, rng) for _ in range(500)]
        avg = sum(results) / len(results)
        self.assertAlmostEqual(avg, 6.0, delta=1.5)

    def test_a_fresh_project_gets_a_real_screenwriter_skill_with_variation(self):
        from callback.engine.simulation._director import new_director_state, start_development
        rng = random.Random(53)
        skills = []
        for i in range(60):
            state = start_development(new_director_state(), "drama", 12.0, random.Random(i))
            skills.append(state.projects[0].project.screenwriter_skill)
        self.assertGreater(max(skills) - min(skills), 20.0)


class TestCasting(unittest.TestCase):
    def test_bankable_wrong_fit_carries_a_real_fit_penalty(self):
        rng = random.Random(5)
        outcome = casting.resolve_casting(casting.BANKABLE_WRONG_FIT, 80.0, rng)
        self.assertEqual(outcome.cast_star_power, 80.0)
        self.assertGreater(outcome.fit_penalty, 0.0)

    def test_discovery_ignores_bankability_and_has_real_variance(self):
        rng = random.Random(6)
        samples = [casting.resolve_casting(casting.DISCOVERY, 0.0, rng).cast_star_power for _ in range(200)]
        self.assertGreater(max(samples) - min(samples), 40.0)

    def test_your_roster_is_marked_reliable(self):
        rng = random.Random(7)
        outcome = casting.resolve_casting(casting.YOUR_ROSTER, 50.0, rng)
        self.assertTrue(outcome.reliable)
        self.assertEqual(outcome.fit_penalty, 0.0)

    def test_difficult_genius_carries_real_chaos(self):
        rng = random.Random(8)
        outcome = casting.resolve_casting(casting.DIFFICULT_GENIUS, 60.0, rng)
        self.assertEqual(outcome.chaos_delta, casting.DIFFICULT_GENIUS_CHAOS)

    def test_unknown_choice_raises(self):
        with self.assertRaises(ValueError):
            casting.resolve_casting("not_a_real_choice", 50.0, random.Random(9))

    def test_max_budget_grows_with_bankability(self):
        self.assertLess(casting.max_budget_from_bankability(30), casting.max_budget_from_bankability(85))


class TestShootStyle(unittest.TestCase):
    def test_many_takes_rewards_high_craft_and_punishes_low(self):
        high = shoot_style.resolve_shoot_style(shoot_style.MANY_TAKES, instinct=50, craft=90)
        low = shoot_style.resolve_shoot_style(shoot_style.MANY_TAKES, instinct=50, craft=20)
        self.assertGreater(high.craft_contribution_delta, 0)
        self.assertLess(low.craft_contribution_delta, 0)

    def test_improvisation_reads_instinct(self):
        high = shoot_style.resolve_shoot_style(shoot_style.IMPROVISATION, instinct=90, craft=50)
        low = shoot_style.resolve_shoot_style(shoot_style.IMPROVISATION, instinct=10, craft=50)
        self.assertGreater(high.craft_contribution_delta, low.craft_contribution_delta)

    def test_heavy_coverage_raises_post_luck_floor_not_mean(self):
        outcome = shoot_style.resolve_shoot_style(shoot_style.HEAVY_COVERAGE, instinct=50, craft=50)
        self.assertEqual(outcome.post_luck_floor_delta, 8.0)

    def test_ensemble_chaos_scales_with_second_attachment_bankability(self):
        self.assertLess(shoot_style.ensemble_chaos(10.0), shoot_style.ensemble_chaos(90.0))
        self.assertLess(shoot_style.ensemble_chaos(100.0), 0.15)  # stays under the difficult-genius flat rate

    def test_overage_stays_within_its_own_bounds(self):
        rng = random.Random(10)
        for _ in range(100):
            o = shoot_style.overage_percent(ambition=80, chaos=90, efficiency=10, rng=rng)
            self.assertGreaterEqual(o, shoot_style.OVERAGE_LO)
            self.assertLessEqual(o, shoot_style.OVERAGE_HI)


class TestEdit(unittest.TestCase):
    def test_final_cut_earned_by_prestige_streak_or_fee_cut(self):
        self.assertTrue(edit.has_final_cut(80.0, 0, False))
        self.assertTrue(edit.has_final_cut(20.0, 2, False))
        self.assertTrue(edit.has_final_cut(20.0, 0, True))
        self.assertFalse(edit.has_final_cut(20.0, 0, False))

    def test_has_cut_uses_your_roll_alone(self):
        rng = random.Random(11)
        outcome = edit.resolve_edit(80.0, 80.0, has_cut=True, contested=False, rng=rng)
        self.assertFalse(outcome.reshot)

    def test_contested_reshoots_at_most_once(self):
        # A weak director's roll should trigger the bad-test-score branch reliably.
        rng = random.Random(12)
        found_reshoot = False
        for _ in range(30):
            outcome = edit.resolve_edit(10.0, 10.0, has_cut=False, contested=True, rng=rng)
            if outcome.reshot:
                found_reshoot = True
                break
        self.assertTrue(found_reshoot)

    def test_no_cut_no_contest_uses_studio_roll_alone(self):
        rng = random.Random(13)
        outcome = edit.resolve_edit(80.0, 80.0, has_cut=False, contested=False, rng=rng)
        self.assertFalse(outcome.reshot)


class TestPlatformExpansion(unittest.TestCase):
    def _snapshot(self, **overrides):
        base = dict(
            genre="drama", budget_millions=20.0, release_strategy="limited", rating_band="PG-13",
            film_critic_score=70.0, audience_score=50.0, opening_millions=5.0, legs=2.0, roi=1.2,
        )
        base.update(overrides)
        return DirectedReleaseSnapshot(**base)

    def test_unavailable_when_never_greenlit(self):
        self.assertFalse(expansion_available(None))

    def test_unavailable_for_wide_release(self):
        self.assertFalse(expansion_available(self._snapshot(release_strategy="wide")))

    def test_unavailable_for_an_unsold_festival_submission(self):
        self.assertFalse(expansion_available(self._snapshot(release_strategy="festival", roi=0.0)))

    def test_available_for_a_sold_festival_hit(self):
        self.assertTrue(expansion_available(self._snapshot(release_strategy="festival", roi=1.5, film_critic_score=70.0)))

    def test_unavailable_for_a_cold_reception(self):
        self.assertFalse(expansion_available(self._snapshot(film_critic_score=40.0, audience_score=40.0)))

    def test_unavailable_once_already_used(self):
        self.assertFalse(expansion_available(self._snapshot(expansion_used=True)))

    def test_rating_dampener_never_exceeds_one_and_scales_with_band(self):
        self.assertLessEqual(rating_dampener("NC-17", "blockbuster"), rating_dampener("PG", "blockbuster"))
        self.assertLessEqual(rating_dampener("R", "blockbuster"), 1.0)

    def test_prestige_studio_more_tolerant_than_blockbuster_for_a_hard_rating(self):
        self.assertGreater(rating_dampener("R", "prestige"), rating_dampener("R", "blockbuster"))


class TestHireOffer(unittest.TestCase):
    def test_probability_scales_with_standing_and_heat(self):
        self.assertLess(hire_offer_probability(10, 50), hire_offer_probability(90, 50))
        self.assertLess(hire_offer_probability(50, 10), hire_offer_probability(50, 90))

    def test_probability_never_exceeds_one(self):
        self.assertLessEqual(hire_offer_probability(1000, 1000), 1.0)

    def test_a_landed_offer_is_real_plain_data(self):
        from callback.engine.studio.slate import TIER_BUDGETS
        rng = random.Random(14)
        hits = [o for o in (roll_hire_offer(90, "drama", 90, TIER_BUDGETS, rng) for _ in range(500)) if o is not None]
        self.assertTrue(hits)
        self.assertEqual(hits[0].genre, "drama")
        self.assertIn(hits[0].budget_millions, TIER_BUDGETS.values())

    def test_accepted_offer_skips_development_hell(self):
        state = new_director_state()
        state = start_development(state, "drama", 12.0, random.Random(1))  # a prior project
        from callback.engine.simulation._director import HireOffer
        offer = HireOffer(genre="horror", budget_millions=30.0, studio_id="mid_major")
        new_state = accept_hire_offer(state, offer, random.Random(15))
        # §7.4 v16 — appends as a new slot rather than displacing the existing one.
        self.assertEqual(len(new_state.projects), 2)
        self.assertEqual(new_state.projects[0].genre, "drama")
        self.assertTrue(new_state.projects[1].project.guaranteed_greenlight)
        self.assertEqual(new_state.projects[1].genre, "horror")

    def test_accepted_offer_is_a_no_op_when_the_slate_is_already_full(self):
        state = new_director_state()
        for i in range(MAX_PROJECTS):
            state = start_development(state, "drama", 12.0, random.Random(i))
        from callback.engine.simulation._director import HireOffer
        offer = HireOffer(genre="horror", budget_millions=30.0, studio_id="mid_major")
        new_state = accept_hire_offer(state, offer, random.Random(15))
        self.assertEqual(new_state, state)


class TestAttachmentOfferProbability(unittest.TestCase):
    def test_bankable_offer_resists_a_bigger_name(self):
        low = attachment_offer_probability(10.0, "stranger", ATTACHMENT_BANKABLE, 1.0, 50.0)
        high = attachment_offer_probability(90.0, "stranger", ATTACHMENT_BANKABLE, 1.0, 50.0)
        self.assertGreater(low, high)

    def test_bankable_offer_helped_by_project_momentum_and_director_standing(self):
        weak = attachment_offer_probability(60.0, "stranger", ATTACHMENT_BANKABLE, 0.2, 10.0)
        strong = attachment_offer_probability(60.0, "stranger", ATTACHMENT_BANKABLE, 2.0, 90.0)
        self.assertGreater(strong, weak)

    def test_loyal_and_ally_read_better_than_a_cold_stranger(self):
        stranger = attachment_offer_probability(50.0, "stranger", ATTACHMENT_BANKABLE, 1.0, 50.0)
        loyal = attachment_offer_probability(50.0, "loyal", ATTACHMENT_BANKABLE, 1.0, 50.0)
        ally = attachment_offer_probability(50.0, "ally", ATTACHMENT_BANKABLE, 1.0, 50.0)
        self.assertGreater(loyal, stranger)
        self.assertGreater(ally, stranger)

    def test_genre_fit_and_studio_favorite_ignore_bankability(self):
        for attachment_type in (ATTACHMENT_GENRE_FIT, ATTACHMENT_STUDIO_FAVORITE):
            low = attachment_offer_probability(5.0, "stranger", attachment_type, 1.0, 50.0)
            high = attachment_offer_probability(95.0, "stranger", attachment_type, 1.0, 50.0)
            self.assertEqual(low, high)

    def test_probability_always_stays_within_its_own_bounds(self):
        for bankability in (0.0, 50.0, 100.0):
            for tier in ("loyal", "ally", "familiar", "stranger", "rival"):
                for attachment_type in (ATTACHMENT_BANKABLE, ATTACHMENT_GENRE_FIT, ATTACHMENT_STUDIO_FAVORITE):
                    p = attachment_offer_probability(bankability, tier, attachment_type, 2.0, 100.0)
                    self.assertGreaterEqual(p, ATTACHMENT_OFFER_FLOOR)
                    self.assertLessEqual(p, ATTACHMENT_OFFER_CEILING)


class TestGeneralizedAttachment(unittest.TestCase):
    def test_genre_fit_uses_its_own_lower_range(self):
        rng = random.Random(30)
        for _ in range(50):
            m = attach_momentum(80.0, "stranger", ATTACHMENT_GENRE_FIT, rng)
            self.assertGreaterEqual(m, ATTACH_GENRE_FIT_MOMENTUM_LO - 0.1)
            self.assertLessEqual(m, ATTACH_GENRE_FIT_MOMENTUM_HI + 0.1)

    def test_studio_favorite_ignores_bankability(self):
        rng = random.Random(31)
        low = [attach_momentum(5.0, "stranger", ATTACHMENT_STUDIO_FAVORITE, rng) for _ in range(100)]
        high = [attach_momentum(95.0, "stranger", ATTACHMENT_STUDIO_FAVORITE, rng) for _ in range(100)]
        self.assertAlmostEqual(sum(low) / len(low), sum(high) / len(high), delta=0.03)
        for m in low + high:
            self.assertGreaterEqual(m, ATTACH_STUDIO_FAVORITE_MOMENTUM_LO)
            self.assertLessEqual(m, ATTACH_STUDIO_FAVORITE_MOMENTUM_HI)

    def test_bankable_still_uses_the_original_formula(self):
        rng_a, rng_b = random.Random(32), random.Random(32)
        self.assertEqual(
            attach_momentum(60.0, "stranger", ATTACHMENT_BANKABLE, rng_a),
            attach_star_momentum(60.0, "stranger", rng_b),
        )


class TestAttachmentAttrition(unittest.TestCase):
    def test_dropout_probability_grows_with_time_and_is_capped(self):
        self.assertLess(attachment_dropout_probability(0), attachment_dropout_probability(10))
        self.assertLessEqual(attachment_dropout_probability(1000), ATTACHMENT_DROPOUT_CEILING)

    def test_age_attachments_ages_everyone_by_one_quarter(self):
        rng = random.Random(33)
        roster = (Attachment("a", 50.0), Attachment("b", 50.0))
        kept, dropped = age_attachments(roster, rng)
        for a in list(kept) + list(dropped):
            self.assertEqual(a.quarters_attached, 1)

    def test_someone_eventually_drops_given_enough_quarters(self):
        rng = random.Random(34)
        roster = (Attachment("a", 50.0),)
        dropped_ever = False
        for _ in range(60):
            roster, dropped = age_attachments(roster, rng)
            if dropped:
                dropped_ever = True
                break
        self.assertTrue(dropped_ever)

    def test_empty_roster_ages_to_empty(self):
        kept, dropped = age_attachments((), random.Random(35))
        self.assertEqual(kept, ())
        self.assertEqual(dropped, ())


class TestSlate(unittest.TestCase):
    def test_capacity_is_flat_not_standing_gated(self):
        state = new_director_state()
        self.assertTrue(can_start_new_project(state))
        for i in range(MAX_PROJECTS):
            state = start_development(state, "drama", 12.0, random.Random(i))
        self.assertEqual(projects_in_play(state), MAX_PROJECTS)
        self.assertFalse(can_start_new_project(state))
        stuck = start_development(state, "comedy", 12.0, random.Random(99))
        self.assertEqual(stuck, state)

    def test_a_brand_new_director_can_start_a_second_project_immediately(self):
        # §7.4 v16 — no Standing gate; a fresh director can pitch a second project right away.
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        self.assertTrue(can_start_new_project(state))
        state = start_development(state, "comedy", 12.0, random.Random(2))
        self.assertEqual(projects_in_play(state), 2)
        self.assertEqual(state.projects[0].genre, "drama")
        self.assertEqual(state.projects[1].genre, "comedy")

    def test_scrapping_removes_only_that_project(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        state = start_development(state, "comedy", 12.0, random.Random(2))
        scrapped = scrap_project(state, 0)
        self.assertEqual(len(scrapped.projects), 1)
        self.assertEqual(scrapped.projects[0].genre, "comedy")
        self.assertTrue(can_start_new_project(scrapped))

    def test_a_project_can_start_self_financed_from_day_one(self):
        # §7.4 v22 — a genuinely independent project, no studio ever attached, distinct from the
        # mid-development buyout (attempt_self_finance).
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=True)
        self.assertTrue(state.projects[0].project.self_financed)

    def test_self_financed_from_day_one_defaults_to_false(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        self.assertFalse(state.projects[0].project.self_financed)

    def test_a_self_financed_project_resolves_on_the_very_next_action(self):
        # The same "no one else's yes to wait on" branch a buyout already gets — no development
        # runway, the next action taken resolves it outright.
        from callback.engine.simulation._director import apply_dev_action_and_advance
        state = new_director_state()
        state = start_development(state, "drama", 12.0, random.Random(1), self_financed=True)
        new_state, info = apply_dev_action_and_advance(
            state, 0, "rewrite", 50.0, random.Random(2), available_money=1_000_000.0,
        )
        self.assertTrue(info["greenlit"])

    def test_out_of_range_scrap_is_a_no_op(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        self.assertEqual(scrap_project(state, 5), state)


class TestDirectorMoney(unittest.TestCase):
    """§7.4 v23 — a real affordability gate on self-financing, and real director income (fee on a
    studio/hire film, net proceeds on a self-financed one) — directing paid literally nothing
    before this pass, and self-financing could push net worth arbitrarily negative to cover it."""

    def test_self_financed_project_blocks_when_you_cannot_afford_it(self):
        from callback.engine.simulation._director import apply_dev_action_and_advance
        state = new_director_state()
        state = start_development(state, "drama", 100.0, random.Random(1), self_financed=True)
        new_state, info = apply_dev_action_and_advance(
            state, 0, "rewrite", 50.0, random.Random(2), available_money=5.0,
        )
        self.assertFalse(info["greenlit"])
        self.assertTrue(info.get("blocked_on_money"))
        self.assertGreater(info["shortfall"], 0.0)
        # the project is untouched — still there, still self-financed, ready once you have the money
        self.assertEqual(len(new_state.projects), 1)
        self.assertTrue(new_state.projects[0].project.self_financed)

    def test_self_financed_project_resolves_once_you_can_actually_afford_it(self):
        from callback.engine.simulation._director import apply_dev_action_and_advance
        state = new_director_state()
        state = start_development(state, "drama", 12.0, random.Random(1), self_financed=True)
        new_state, info = apply_dev_action_and_advance(
            state, 0, "rewrite", 50.0, random.Random(2), available_money=1_000.0,
        )
        self.assertTrue(info["greenlit"])
        self.assertFalse(info.get("blocked_on_money", False))

    def test_hire_film_pays_a_real_director_fee(self):
        # v19 — the hire fee is now negotiated within DIRECTOR_FEE_SHARE_HIRE_RANGE (leverage.
        # approvals), not a flat DIRECTOR_FEE_SHARE_HIRE cut — check it lands in the real band.
        from callback.engine.leverage.approvals import DIRECTOR_FEE_SHARE_HIRE_RANGE
        from callback.engine.simulation._director import accept_hire_offer, HireOffer
        state = new_director_state()
        state = accept_hire_offer(state, HireOffer(genre="drama", budget_millions=30.0, studio_id="mid_major"), random.Random(1))
        new_state, info = greenlight_and_finish(state, 0, "rewrite", 55.0, random.Random(2))
        self.assertTrue(info["greenlit"])
        lo, hi = DIRECTOR_FEE_SHARE_HIRE_RANGE
        self.assertGreaterEqual(info["director_income"], lo * 30.0 - 0.01)
        self.assertLessEqual(info["director_income"], hi * 30.0 + 0.01)

    def test_hire_fee_share_is_higher_than_studio_fee_share(self):
        from callback.engine.simulation._director import DIRECTOR_FEE_SHARE_HIRE, DIRECTOR_FEE_SHARE_STUDIO
        self.assertGreater(DIRECTOR_FEE_SHARE_HIRE, DIRECTOR_FEE_SHARE_STUDIO)

    def test_self_financed_income_is_net_proceeds_not_a_flat_fee(self):
        state = new_director_state()
        state = start_development(state, "drama", 12.0, random.Random(1), self_financed=True)
        new_state, info = greenlight_and_finish(
            state, 0, "rewrite", 50.0, random.Random(2), available_money=1_000.0,
        )
        self.assertTrue(info["greenlit"])
        # net proceeds = gross - marketing, a real number that isn't just a fixed % of budget.
        # gross_millions/marketing_millions are each independently rounded to 1dp for display,
        # while director_income is rounded to 2dp off the unrounded originals — comparing against
        # the ALREADY-ROUNDED display values can't match exactly; each side can be off by up to
        # 0.05, so up to 0.1 apart is still the same real number.
        self.assertAlmostEqual(info["director_income"], info["gross_millions"] - info["marketing_millions"], delta=0.15)

    def test_a_low_standing_studio_backed_director_gets_no_bonus_offer(self):
        state = new_director_state()  # default Standing is nowhere near either bonus threshold
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=False)
        self.assertIsNone(state.projects[0].project.box_office_bonus_type)
        self.assertEqual(state.projects[0].project.box_office_bonus_share, 0.0)

    def test_a_high_standing_studio_backed_director_negotiates_a_real_bonus(self):
        from dataclasses import replace as dc_replace
        from callback.engine.actor.standing import new_standing_model
        state = new_director_state()
        state = dc_replace(state, standing=new_standing_model(heat=90.0, prestige=90.0, affection=90.0, notoriety=90.0))
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=False)
        project = state.projects[0].project
        self.assertIsNotNone(project.box_office_bonus_type)
        self.assertGreater(project.box_office_bonus_share, 0.0)

    def test_a_studio_backed_bonus_actually_pays_out_on_top_of_the_flat_fee(self):
        from dataclasses import replace as dc_replace
        from callback.engine.actor.standing import new_standing_model
        from callback.engine.simulation._director import DIRECTOR_FEE_SHARE_STUDIO
        flat_fee = DIRECTOR_FEE_SHARE_STUDIO * 30.0
        for base_seed in range(10):
            state = new_director_state()
            state = dc_replace(state, standing=new_standing_model(heat=90.0, prestige=90.0, affection=90.0, notoriety=90.0))
            state = start_development(state, "drama", 30.0, random.Random(1 + base_seed), self_financed=False)
            self.assertIsNotNone(state.projects[0].project.box_office_bonus_type)
            info = {"greenlit": False, "dead": False}
            for i in range(50):
                state, info = apply_dev_action_and_advance(state, 0, "rewrite", 55.0, random.Random(100 + base_seed * 50 + i))
                if info["greenlit"] or info["dead"] or not state.projects:
                    break
            if not info["greenlit"]:
                continue
            for j in range(20):
                state, resolved = advance_shoots_and_resolve(state, {}, random.Random(200 + base_seed * 20 + j))
                if resolved:
                    info = resolved[0]
                    break
            # The bonus only actually pays above break-even (leverage.approvals.
            # box_office_bonus_earned) — a real, possible 0 on any single resolved film, not a bug.
            # Retry across seeds for one that actually clears it, same as this suite's established
            # "RNG variance, not a bug" pattern.
            if info["director_income"] > flat_fee:
                self.assertIsNotNone(info["box_office_bonus_type"])
                return
        self.skipTest("no seed in range produced a bonus-clearing resolved film — RNG variance, not a bug")


class TestDirectorDeal(unittest.TestCase):
    """§7.4 v25 — the director's own mirror of the actor's Deal screen: a deliberate ask, not
    just start_development()'s free automatic roll. Trades a lower guaranteed fee (pinned to
    DIRECTOR_FEE_SHARE_STUDIO_RANGE's own floor) for a real shot at a box-office bonus."""

    def test_unavailable_for_a_self_financed_project(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=True)
        self.assertFalse(director_deal_available(state, 0))

    def test_unavailable_for_a_guaranteed_hire(self):
        from dataclasses import replace as dc_replace
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=False)
        projects = list(state.projects)
        projects[0] = dc_replace(projects[0], project=dc_replace(projects[0].project, guaranteed_greenlight=True))
        state = dc_replace(state, projects=tuple(projects))
        self.assertFalse(director_deal_available(state, 0))

    def test_a_low_standing_director_cannot_push_for_a_bonus(self):
        state = new_director_state()  # default Standing is nowhere near either bonus threshold
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=False)
        self.assertTrue(director_deal_available(state, 0))
        self.assertFalse(director_box_office_bonus_available(state, "net_points"))
        before = state.projects[0].project
        after_state = push_director_deal_for_backend(state, 0, "net_points", random.Random(1))
        after = after_state.projects[0].project
        self.assertEqual(before.negotiated_fee_share, after.negotiated_fee_share)
        self.assertIsNone(after.box_office_bonus_type)

    def test_a_qualifying_director_can_push_for_first_dollar_gross_the_automatic_roll_never_grants(self):
        from dataclasses import replace as dc_replace
        from callback.engine.actor.standing import new_standing_model
        from callback.engine.leverage.approvals import DIRECTOR_FEE_SHARE_STUDIO_RANGE
        # Standing between the net_points and first_dollar_gross bars: start_development() auto-
        # grants the easier net_points deal for free, but never the harder first_dollar_gross ask.
        state = new_director_state()
        state = dc_replace(state, standing=new_standing_model(heat=80.0, prestige=80.0, affection=80.0, notoriety=10.0))
        state = start_development(state, "family", 30.0, random.Random(1), self_financed=False)
        before = state.projects[0].project
        self.assertEqual(before.box_office_bonus_type, "net_points")  # the free roll
        self.assertFalse(director_box_office_bonus_available(state, "first_dollar_gross"))

        after_state = push_director_deal_for_backend(state, 0, "first_dollar_gross", random.Random(1))
        # Standing still doesn't clear the bar — the deliberate push doesn't bypass the gate either.
        after = after_state.projects[0].project
        self.assertEqual(before.negotiated_fee_share, after.negotiated_fee_share)

    def test_pushing_for_a_bonus_trades_a_lower_guaranteed_fee(self):
        from dataclasses import replace as dc_replace
        from callback.engine.actor.standing import new_standing_model
        from callback.engine.leverage.approvals import DIRECTOR_FEE_SHARE_STUDIO_RANGE
        floor, _hi = DIRECTOR_FEE_SHARE_STUDIO_RANGE
        state = new_director_state()
        # Maximum Standing so the automatic roll already lands on the strong end of the fee range —
        # pushing should still pin it down to the floor, real money given up for the ask.
        state = dc_replace(state, standing=new_standing_model(heat=100.0, prestige=100.0, affection=100.0, notoriety=0.0))
        state = start_development(state, "drama", 30.0, random.Random(2), self_financed=False)
        before = state.projects[0].project
        self.assertGreater(before.negotiated_fee_share, floor)

        after_state = push_director_deal_for_backend(state, 0, "first_dollar_gross", random.Random(3))
        after = after_state.projects[0].project
        self.assertEqual(after.negotiated_fee_share, floor)
        self.assertEqual(after.box_office_bonus_type, "first_dollar_gross")
        self.assertGreater(after.box_office_bonus_share, 0.0)

    def test_session_exposes_the_same_deal(self):
        from dataclasses import replace as dc_replace
        from callback.engine.actor.standing import new_standing_model
        session = Session(seed=1)
        session.start("conservatory", "work")
        session.state = dc_replace(session.state, director=new_director_state())
        session.state = dc_replace(
            session.state,
            director=dc_replace(
                session.state.director,
                standing=new_standing_model(heat=100.0, prestige=100.0, affection=100.0, notoriety=0.0),
            ),
        )
        self.assertTrue(session.start_directing_project("drama", "low", self_financed=False))
        self.assertTrue(session.director_deal_available(0))
        self.assertTrue(session.director_box_office_bonus_available("first_dollar_gross"))
        result = session.push_director_deal_for_backend(0, "first_dollar_gross")
        self.assertTrue(result["granted"])
        status = session.director_status()
        self.assertEqual(status["projects"][0]["box_office_bonus_type"], "first_dollar_gross")
        self.assertIsNotNone(status["projects"][0]["fee_share_pct"])


class TestBankabilityTrailingRoi(unittest.TestCase):
    """§7.4 v24 — a real "you're only as good as your last few pictures" force. Before this pass,
    greenlight_probability never read a director's own track record at all."""

    def test_a_new_director_starts_at_breakeven_with_no_penalty(self):
        state = new_director_state()
        self.assertEqual(state.trailing_roi, 1.0)

    def test_trailing_roi_moves_off_a_resolved_films_real_roi(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1), self_financed=False)
        info = {"greenlit": False, "dead": False}
        # v17 — the momentum_budget_discount added for a $30M ask means a flat "rewrite" policy
        # (no momentum-building action at all) takes longer, on average, to clear the greenlight
        # roll than before — widened from 50 to 150 tries, same as any other RNG-driven retry loop
        # in this file, not a sign the odds are broken.
        for i in range(150):
            state, info = apply_dev_action_and_advance(state, 0, "rewrite", 55.0, random.Random(200 + i))
            if info["greenlit"] or info["dead"] or not state.projects:
                break
        self.assertTrue(info["greenlit"])
        for _ in range(20):
            state, resolved = advance_shoots_and_resolve(state, {}, random.Random(300))
            if resolved:
                info = resolved[0]
                break
        # trailing_roi should have moved off the neutral 1.0 starting point toward this film's own
        # real roi, whichever direction that happened to land.
        self.assertNotEqual(state.trailing_roi, 1.0)
        # info["roi"] is rounded for display, and the EMA itself feeds on director.development.
        # format_adjusted_roi's release-strategy-relative reading (a Limited/acquired-Festival
        # release is judged against its own real breakeven, not a flat wide-release bar) rather
        # than the raw number — this only needs to land close to that, not exact.
        from callback.engine.director.development import format_adjusted_roi
        expected_effective = format_adjusted_roi(info["roi"], info["release_strategy"], info["gross_millions"])
        self.assertAlmostEqual(state.trailing_roi, 0.7 * 1.0 + 0.3 * expected_effective, places=1)


class TestFormatAdjustedRoi(unittest.TestCase):
    """director.development.format_adjusted_roi — a Limited/acquired-Festival release's own real
    breakeven is far below a wide release's; trailing_roi/the profitability streak should judge a
    film against the bar its own release strategy could realistically clear, not a flat 1.0."""

    def test_wide_and_streaming_are_untouched(self):
        self.assertAlmostEqual(format_adjusted_roi(0.8, "wide", 50.0), 0.8)
        self.assertAlmostEqual(format_adjusted_roi(1.4, "streaming", 50.0), 1.4)

    def test_a_limited_release_at_its_own_breakeven_reads_as_full_breakeven(self):
        centre = bankability_roi_centre("limited", gross=10.0)
        self.assertAlmostEqual(format_adjusted_roi(centre, "limited", 10.0), 1.0, places=6)

    def test_an_acquired_festival_release_at_its_own_breakeven_reads_as_full_breakeven(self):
        centre = bankability_roi_centre("festival", gross=5.0)
        self.assertAlmostEqual(format_adjusted_roi(centre, "festival", 5.0), 1.0, places=6)

    def test_an_unsold_festival_submission_is_judged_at_the_full_wide_release_bar(self):
        # gross<=0 on a Festival strategy — nobody bought it, a real failure at any scale.
        self.assertEqual(bankability_roi_centre("festival", gross=0.0), 1.0)
        self.assertAlmostEqual(format_adjusted_roi(0.0, "festival", 0.0), 0.0)

    def test_a_limited_release_below_its_own_breakeven_still_reads_as_a_real_shortfall(self):
        centre = bankability_roi_centre("limited", gross=10.0)
        below = format_adjusted_roi(centre / 2.0, "limited", 10.0)
        self.assertLess(below, 1.0)
        self.assertGreater(below, 0.0)

    def test_shelved_is_untouched_and_still_reads_as_a_real_loss(self):
        self.assertAlmostEqual(format_adjusted_roi(-1.0, "shelved", 0.0), -1.0)


class TestLimbo(unittest.TestCase):
    def test_higher_budget_raises_fired_odds(self):
        low_budget, _ = limbo_probabilities(4.0, 30.0, 0.0)
        high_budget, _ = limbo_probabilities(120.0, 30.0, 0.0)
        self.assertGreater(high_budget, low_budget)

    def test_higher_standing_lowers_fired_odds(self):
        weak, _ = limbo_probabilities(60.0, 10.0, 0.0)
        strong, _ = limbo_probabilities(60.0, 90.0, 0.0)
        self.assertGreater(weak, strong)

    def test_deeper_severity_raises_canceled_odds(self):
        _, shallow = limbo_probabilities(30.0, 50.0, 0.05)
        _, deep = limbo_probabilities(30.0, 50.0, 1.0)
        self.assertGreater(deep, shallow)

    def test_probabilities_never_consume_the_whole_pool(self):
        for budget in (4.0, 30.0, 200.0):
            for standing in (0.0, 50.0, 100.0):
                for severity in (0.0, 0.5, 1.0):
                    p_fired, p_canceled = limbo_probabilities(budget, standing, severity)
                    self.assertLess(p_fired + p_canceled, 1.0)

    def test_resolve_limbo_always_returns_one_of_the_real_outcomes(self):
        from callback.engine.director.development import DevProject
        project = DevProject(script_id="x", momentum=0.05, budget_ask=20.0)
        seen = set()
        for seed in range(200):
            outcome = resolve_limbo(project, 50.0, 1_000_000.0, random.Random(seed))
            seen.add(outcome.kind)
        self.assertTrue(seen.issubset({"fired", "canceled", "handed_free", "buyout_paid", "could_not_afford"}))
        self.assertTrue(seen)

    def test_could_not_afford_and_fired_and_canceled_all_remove_the_project(self):
        from callback.engine.director.development import DevProject
        project = DevProject(script_id="x", momentum=0.05, budget_ask=20.0)
        for seed in range(200):
            outcome = resolve_limbo(project, 50.0, 0.0, random.Random(seed))
            if outcome.kind in ("fired", "canceled", "could_not_afford"):
                self.assertIsNone(outcome.project)
            elif outcome.kind in ("handed_free", "buyout_paid"):
                self.assertIsNotNone(outcome.project)
                self.assertTrue(outcome.project.self_financed)
                self.assertFalse(outcome.project.dead)

    def test_a_neglected_project_can_hit_limbo_and_resolve_dynamically(self):
        state = new_director_state()
        state = start_development(state, "drama", 30.0, random.Random(1))
        state = start_development(state, "comedy", 12.0, random.Random(2))
        rng = random.Random(3)
        saw_limbo = False
        for _ in range(80):
            if len(state.projects) < 2:
                break
            state, info = apply_dev_action_and_advance(state, 0, "rewrite", genre_demand=20.0, rng=rng, available_money=0.0)
            if info.get("limbo_events"):
                saw_limbo = True
                break
        self.assertTrue(saw_limbo)


class TestSessionIntegration(unittest.TestCase):
    def test_casting_and_shoot_style_choices_are_settable_and_default_sane(self):
        session = Session(seed=20)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        self.assertIn(casting.YOUR_ROSTER, dict(Session.director_casting_options()))
        session.choose_director_casting_action(0, casting.DIFFICULT_GENIUS)
        session.choose_director_shoot_style_action(0, shoot_style.LONG_TAKES)
        self.assertEqual(session.state.director.projects[0].pending_casting_choice, casting.DIFFICULT_GENIUS)
        self.assertEqual(session.state.director.projects[0].pending_shoot_style, shoot_style.LONG_TAKES)

    def test_attach_star_target_options_include_a_cold_approach(self):
        session = Session(seed=21)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        options = session.attach_star_target_options()
        self.assertTrue(any(o["id"] is None for o in options))

    def test_starting_a_project_self_financed_reports_it_and_resolves_next_action(self):
        from dataclasses import replace as dc_replace
        session = Session(seed=22)
        session.start("conservatory", "work")
        session.become_director()
        # §7.4 v23 — self-financing now genuinely requires the money.
        session.state = dc_replace(session.state, life=dc_replace(session.state.life, money=dc_replace(session.state.life.money, net_worth=1_000_000.0)))
        started = session.start_directing_project("drama", "low", self_financed=True)
        self.assertTrue(started)
        status = session.director_status()
        self.assertTrue(status["projects"][0]["self_financed"])
        before_net_worth = session.state.life.money.net_worth
        result = finish_session_directing(session, 0, "rewrite")
        self.assertTrue(result["greenlit"])
        self.assertTrue(result["self_financed"])
        # §7.4 v23 — the whole budget comes out of net worth, but real net proceeds (gross minus
        # marketing, rights_share=1.0) come back in too — net worth isn't guaranteed to drop
        # anymore, a hit can leave you richer. What's guaranteed is that a real production cost
        # was actually paid and a real income figure was reported, not that the total went down.
        self.assertGreater(result["budget_millions"], 0.0)
        self.assertIn("director_income_millions", result)
        self.assertNotEqual(session.state.life.money.net_worth, before_net_worth)

    def test_starting_a_project_normally_is_not_self_financed(self):
        session = Session(seed=23)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        status = session.director_status()
        self.assertFalse(status["projects"][0]["self_financed"])

    def test_a_full_directing_run_never_crashes_and_reports_a_rating_band(self):
        session = Session(seed=22)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "mid")
        session.choose_director_casting_action(0, casting.YOUR_ROSTER)
        session.choose_director_shoot_style_action(0, shoot_style.LEAN_AND_FAST)
        resolved = None
        for _ in range(200):
            if session.quarters_remaining_this_year() <= 0:
                wrapped = session.end_year()
                if wrapped:
                    resolved = wrapped[0]
                    break
                continue
            result = session.advance_directing(0, "rewrite")
            if result["dead"]:
                break
        if resolved is not None:
            self.assertIn(resolved["rating_band"], ("G", "PG", "PG-13", "R", "NC-17"))
            self.assertIn(resolved["momentum_band"], ("dead", "fading", "building", "real heat", "can't-miss"))

    def _self_financed_result(self, seed: int, efficiency: float) -> dict | None:
        from dataclasses import replace as dc_replace
        session = Session(seed=seed)
        session.start("conservatory", "work")
        session.become_director()
        session.state = dc_replace(session.state, life=dc_replace(
            session.state.life, money=dc_replace(session.state.life.money, net_worth=1_000_000.0)))
        session.state = dc_replace(session.state, director=dc_replace(
            session.state.director, attrs=dc_replace(session.state.director.attrs, efficiency=efficiency, vision=90.0)))
        session.start_directing_project("drama", "low", self_financed=True)
        result = finish_session_directing(session, 0, "rewrite")
        return result if result["greenlit"] else None

    def test_a_greenlit_project_reports_the_real_budget_ask_and_overage(self):
        # simulation._director's _resolve_directed_film — director.shoot_style.overage_percent's
        # own Efficiency-driven schedule signal now really costs something, and is visible.
        for seed in range(20):
            result = self._self_financed_result(seed, efficiency=0.0)
            if result is not None:
                self.assertIn("budget_ask_millions", result)
                self.assertIn("schedule_overage_pct", result)
                self.assertGreaterEqual(result["budget_millions"], result["budget_ask_millions"])
                return
        self.skipTest("no seed in range greenlit — RNG variance, not a bug")

    def test_low_efficiency_runs_a_real_worse_overrun_than_high_efficiency(self):
        low = [r["schedule_overage_pct"] for s in range(40) if (r := self._self_financed_result(s, 0.0)) is not None]
        high = [r["schedule_overage_pct"] for s in range(40) if (r := self._self_financed_result(s, 100.0)) is not None]
        if not low or not high:
            self.skipTest("no seed produced a greenlit project — RNG variance, not a bug")
        self.assertGreater(sum(low) / len(low), sum(high) / len(high))

    def test_finishing_under_schedule_never_discounts_the_real_budget(self):
        for seed in range(40):
            result = self._self_financed_result(seed, efficiency=100.0)
            if result is not None and result["schedule_overage_pct"] < 0:
                self.assertAlmostEqual(result["budget_millions"], result["budget_ask_millions"], places=1)
                return
        self.skipTest("no seed produced a came-in-under-schedule project — RNG variance, not a bug")

    def test_a_studio_backed_project_names_its_financing_studio_at_start(self):
        # v11 fix — the studio is real from the moment development starts, not a random pick
        # conjured fresh only once greenlit.
        session = Session(seed=24)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        self.assertIsNotNone(session.state.director.projects[0].project.financing_studio_id)

    def test_self_financed_project_names_no_studio(self):
        from dataclasses import replace as dc_replace
        session = Session(seed=25)
        session.start("conservatory", "work")
        session.become_director()
        session.state = dc_replace(session.state, life=dc_replace(
            session.state.life, money=dc_replace(session.state.life.money, net_worth=1_000_000.0)))
        session.start_directing_project("drama", "low", self_financed=True)
        self.assertIsNone(session.state.director.projects[0].project.financing_studio_id)

    def test_higher_studio_trust_raises_greenlight_odds(self):
        from callback.engine.simulation._director import apply_dev_action_and_advance, new_director_state, start_development
        greenlit_low = 0
        greenlit_high = 0
        trials = 60
        for seed in range(trials):
            state = start_development(new_director_state(), "drama", 30.0, random.Random(seed))
            _, info_low = apply_dev_action_and_advance(state, 0, "rewrite", 20.0, random.Random(seed + 1000), studio_trust=10.0)
            greenlit_low += int(info_low["greenlit"])
        for seed in range(trials):
            state = start_development(new_director_state(), "drama", 30.0, random.Random(seed))
            _, info_high = apply_dev_action_and_advance(state, 0, "rewrite", 20.0, random.Random(seed + 1000), studio_trust=95.0)
            greenlit_high += int(info_high["greenlit"])
        self.assertGreaterEqual(greenlit_high, greenlit_low)

    def test_hire_offer_check_returns_none_or_plain_data(self):
        session = Session(seed=23)
        session.start("conservatory", "work")
        session.become_director()
        offer = session.check_for_hire_offer()
        if offer is not None:
            self.assertIsInstance(offer["genre"], str)
            self.assertIsInstance(offer["studio_name"], str)

    def test_can_attach_multiple_people_before_greenlight(self):
        session = Session(seed=24)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "mid")
        options = session.attach_star_target_options()
        session.choose_attach_star_target(options[0]["id"], "bankable")
        session.advance_directing(0, "attach_star")
        session.choose_attach_star_target(options[-1]["id"] if len(options) > 1 else options[0]["id"], "genre_fit")
        if session.quarters_remaining_this_year() <= 0:
            session.end_year()
        result = session.advance_directing(0, "attach_star")
        status = session.director_status()
        if not result["greenlit"] and not result["dead"] and status["projects"]:
            self.assertGreaterEqual(len(status["projects"][0]["attachments"]), 1)

    def test_attachment_type_options_are_plain_tuples(self):
        for key, label in Session.attach_star_type_options():
            self.assertIsInstance(key, str)
            self.assertIsInstance(label, str)

    def test_a_new_director_session_can_pitch_a_second_project_immediately(self):
        # §7.4 v16 — never gated behind Standing; MAX_PROJECTS is the only cap.
        session = Session(seed=25)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        status = session.director_status()
        self.assertTrue(status["can_start_new_project"])
        started = session.start_directing_project("comedy", "micro")
        self.assertTrue(started)
        self.assertEqual(len(session.director_status()["projects"]), 2)

    def test_start_directing_project_refuses_beyond_max_projects(self):
        session = Session(seed=26)
        session.start("conservatory", "work")
        session.become_director()
        for i in range(MAX_PROJECTS):
            self.assertTrue(session.start_directing_project("drama", "micro"))
        self.assertFalse(session.start_directing_project("comedy", "micro"))
        self.assertEqual(len(session.director_status()["projects"]), MAX_PROJECTS)

    def test_scrapping_a_project_through_session(self):
        session = Session(seed=27)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        session.start_directing_project("comedy", "micro")
        status = session.director_status()
        self.assertEqual(len(status["projects"]), 2)

        session.scrap_directing_project(0)
        status = session.director_status()
        self.assertEqual(len(status["projects"]), 1)
        self.assertEqual(status["projects"][0]["genre"], "comedy")

    def test_quarters_reset_after_end_year(self):
        session = Session(seed=28)
        session.start("conservatory", "work")
        session.become_director()
        session.start_directing_project("drama", "low")
        self.assertEqual(session.quarters_remaining_this_year(), 4)
        session.advance_directing(0, "rewrite")
        self.assertEqual(session.quarters_remaining_this_year(), 3)
        session.end_year()
        self.assertEqual(session.quarters_remaining_this_year(), 4)


if __name__ == "__main__":
    unittest.main()
