"""actor/ formula edge cases, including the two v9-fixed values this pass must not regress:
the open-offer Utility margin (14, not the broken pre-v9 25) and the Presence Spotlight-floor
coefficient (0.42, not the pre-v9 0.10 that never bound against a Spotlight mean of ~58).
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.attributes import Attributes, PRESENCE_SPOTLIGHT_FLOOR_COEF
from callback.engine.actor.offers import (
    ANIMATION_AGE_MISMATCH_MULT,
    BREAKING_TYPE_THRESHOLD,
    OPEN_OFFER_UTILITY_MARGIN,
    Role,
    age_mismatch_penalty,
    fit_score,
    gatekeeper_legibility_multiplier,
    in_lane,
    in_lane_audience_bonus,
    is_breaking_type,
    lane_for_role,
    quarters_for_role,
    resolve_casting_path,
    role_difficulty,
    ROLE_QUARTERS_ANIMATION,
    ROLE_QUARTERS_MAX,
    type_break_difficulty_tax,
    typecasting_penalty,
)
from callback.engine.actor.persona import LEGIBILITY_MID_MAX, Persona
from callback.engine.actor.positions import contrast_budget, overspend_penalty


class TestV9Fixes(unittest.TestCase):
    def test_open_offer_margin_is_14_not_25(self):
        self.assertEqual(OPEN_OFFER_UTILITY_MARGIN, 14.0)

    def test_notices_floor_coefficient_is_0_42_not_0_10(self):
        self.assertEqual(PRESENCE_SPOTLIGHT_FLOOR_COEF, 0.42)

    def test_spotlight_floor_binds_for_high_presence(self):
        # A Spotlight mean around 58 (per §14.1) should be bindable by a high-Presence floor at the
        # v9 coefficient — the exact failure mode the v9 note describes for the old 0.10 value.
        attrs = Attributes(presence=90)
        self.assertGreater(attrs.spotlight_floor(), 37.0)  # 0.42 * 90 = 37.8
        low_presence = Attributes(presence=20)
        self.assertLess(low_presence.spotlight_floor(), 10.0)  # 0.42 * 20 = 8.4, well under a 58 mean

    def test_direct_offer_requires_margin_above_14(self):
        role = Role(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                     char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=10,
                     gatekeeper="indie_first_timer")
        self.assertEqual(resolve_casting_path(50 + 15, role), "direct_offer")
        self.assertEqual(resolve_casting_path(50 + 10, role), "audition")


class TestFitScore(unittest.TestCase):
    def _role(self, **overrides) -> Role:
        base = dict(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=10,
                    gatekeeper="indie_first_timer")
        base.update(overrides)
        return Role(**base)

    def test_perfect_persona_match_scores_higher_than_mismatch(self):
        attrs = Attributes()
        matched_persona = Persona(genre_affinity={"drama": 100.0})
        role = self._role(char_age=40)
        high = fit_score(attrs, matched_persona, role, your_age=40)
        low = fit_score(attrs, Persona(), role, your_age=40)
        self.assertGreaterEqual(high, low)

    def test_age_mismatch_within_free_band_costs_nothing(self):
        self.assertEqual(age_mismatch_penalty(char_age=42, your_age=40), 0.0)

    def test_playing_younger_costs_more_than_playing_older(self):
        # A 10-year gap in each direction — small enough that neither hits the 70-point cap,
        # so the asymmetry (playing younger costs 1.6x more) is actually observable.
        younger = age_mismatch_penalty(char_age=30, your_age=40)
        older = age_mismatch_penalty(char_age=50, your_age=40)
        self.assertGreater(younger, older)

    def test_fit_score_never_negative(self):
        attrs = Attributes(voice=0, physicality=0, look=0)
        role = self._role(char_age=90, requirements={"voice": 80, "physicality": 80})
        self.assertGreaterEqual(fit_score(attrs, Persona(), role, your_age=20), 0.0)

    def test_animation_heavily_reduces_age_mismatch_penalty(self):
        live_action = age_mismatch_penalty(char_age=25, your_age=60, is_animation=False)
        animated = age_mismatch_penalty(char_age=25, your_age=60, is_animation=True)
        self.assertGreater(live_action, 0.0)
        self.assertAlmostEqual(animated, live_action * ANIMATION_AGE_MISMATCH_MULT)
        self.assertLess(animated, live_action)


class TestLaneForRole(unittest.TestCase):
    def _role(self, **overrides) -> Role:
        base = dict(project_id="p1", genre="drama", archetype="everyman", billing="supporting",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=10,
                    gatekeeper="indie_first_timer")
        base.update(overrides)
        return Role(**base)

    def test_ingenue_and_romantic_lead_share_a_lane(self):
        self.assertEqual(lane_for_role(self._role(archetype="ingenue")), "ingenue_romantic")
        self.assertEqual(lane_for_role(self._role(archetype="romantic_lead")), "ingenue_romantic")

    def test_authority_has_a_lane(self):
        self.assertEqual(lane_for_role(self._role(archetype="authority")), "character_authority")

    def test_lead_billing_is_lead_overall_regardless_of_archetype(self):
        self.assertEqual(lane_for_role(self._role(billing="lead", archetype="everyman")), "lead_overall")

    def test_uncovered_archetypes_have_no_lane(self):
        for archetype in ("everyman", "villain", "comic_relief", "mentor", "narrator", "ensemble"):
            self.assertIsNone(lane_for_role(self._role(billing="supporting", archetype=archetype)))


class TestContrastBudget(unittest.TestCase):
    def test_overspend_penalizes_spotlight_and_craft_contribution(self):
        spotlight_pen, craft_contribution_pen = overspend_penalty(2.0)
        self.assertEqual(spotlight_pen, -10.0)  # -5 * 2
        self.assertEqual(craft_contribution_pen, -6.0)  # -3 * 2

    def test_no_overspend_no_penalty(self):
        self.assertEqual(overspend_penalty(0.0), (0.0, 0.0))
        self.assertEqual(overspend_penalty(-1.0), (0.0, 0.0))

    def test_budget_grows_with_craft_and_command(self):
        low = contrast_budget(craft=30, director_command=30)
        high = contrast_budget(craft=90, director_command=84)
        self.assertGreater(high, low)


class TestLegibility(unittest.TestCase):
    def test_flat_affinity_is_low_legibility(self):
        p = Persona()  # every entry starts equal
        self.assertEqual(p.legibility(), 0.0)
        self.assertEqual(p.legibility_band(), "low")

    def test_concentrated_affinity_is_high_legibility(self):
        # Legibility averages concentration across BOTH vectors — concentrating only genre and
        # leaving archetype flat drags the average down, so both need to be concentrated here.
        other_genres = ["comedy", "action", "horror", "thriller", "romance", "scifi", "period", "musical", "family"]
        other_archetypes = ["romantic_lead", "villain", "everyman", "mentor", "ingenue",
                             "authority", "comic_relief", "ensemble"]
        p = Persona(
            genre_affinity={"drama": 100.0, **{g: 0.0 for g in other_genres}},
            archetype_affinity={"leading_hero": 100.0, **{a: 0.0 for a in other_archetypes}},
        )
        self.assertGreater(p.legibility(), LEGIBILITY_MID_MAX)
        self.assertEqual(p.legibility_band(), "high")


class TestRoleDifficultyScalesWithBudget(unittest.TestCase):
    """actor.offers.role_difficulty — a role's own Difficulty used to be pure noise, independent
    of the film's own budget. A tentpole-scale lead should be a genuinely taller bar than a
    scrappy indie one, the same "studios protect their bigger investments" logic
    director.development.difficulty already applies on the financing side."""

    def test_bigger_budgets_are_reliably_harder_on_average(self):
        rng = random.Random(1)
        small = [role_difficulty(2.0, rng) for _ in range(500)]
        big = [role_difficulty(250.0, rng) for _ in range(500)]
        self.assertGreater(sum(big) / len(big), sum(small) / len(small))

    def test_stays_within_the_documented_bounds(self):
        rng = random.Random(2)
        for budget in (0.0, 1.5, 300.0, 1000.0):
            d = role_difficulty(budget, rng)
            self.assertGreaterEqual(d, 5.0)
            self.assertLessEqual(d, 95.0)


class TestQuartersForRole(unittest.TestCase):
    """actor.offers.quarters_for_role — a role's own real scale (animation, budget, episode
    count) decides how much of the year it costs, not a flat QUARTERS_PER_YEAR every time."""

    def _role(self, **overrides) -> Role:
        base = dict(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=0.5, difficulty=50, budget_for_role=10.0,
                    gatekeeper="indie_first_timer", film_budget_millions=10.0)
        base.update(overrides)
        return Role(**base)

    def test_animation_is_always_one_quarter_regardless_of_budget(self):
        cheap = self._role(is_animation=True, film_budget_millions=2.0)
        tentpole = self._role(is_animation=True, film_budget_millions=250.0)
        self.assertEqual(quarters_for_role(cheap), ROLE_QUARTERS_ANIMATION)
        self.assertEqual(quarters_for_role(tentpole), ROLE_QUARTERS_ANIMATION)

    def test_bigger_live_action_budgets_cost_more_quarters(self):
        small = self._role(film_budget_millions=1.5)
        big = self._role(film_budget_millions=300.0)
        self.assertLess(quarters_for_role(small), quarters_for_role(big))
        self.assertEqual(quarters_for_role(big), ROLE_QUARTERS_MAX)

    def test_stays_within_bounds(self):
        for budget in (0.0, 1.5, 12.0, 300.0, 10_000.0):
            q = quarters_for_role(self._role(film_budget_millions=budget))
            self.assertGreaterEqual(q, 1)
            self.assertLessEqual(q, ROLE_QUARTERS_MAX)

    def test_series_scales_with_episode_count(self):
        short_season = self._role(project_type="series", n_episodes=4)
        long_season = self._role(project_type="series", n_episodes=13)
        self.assertLess(quarters_for_role(short_season), quarters_for_role(long_season))
        self.assertEqual(quarters_for_role(short_season), 1)
        self.assertEqual(quarters_for_role(long_season), ROLE_QUARTERS_MAX)

    def test_animation_overrides_series_episode_scaling_too(self):
        role = self._role(project_type="series", n_episodes=13, is_animation=True)
        self.assertEqual(quarters_for_role(role), ROLE_QUARTERS_ANIMATION)


class TestTypecastingDepth(unittest.TestCase):
    """actor.offers's gatekeeper-conditional Fit, the critics/audience wedge, the breaking-type
    detection, and the type-break difficulty tax — wiring Persona.legibility() into real mechanics
    for the first time."""

    def _role(self, **overrides) -> Role:
        base = dict(project_id="p1", genre="drama", archetype="everyman", billing="lead",
                    char_age=40, type_strictness=1.0, difficulty=50, budget_for_role=10,
                    gatekeeper="indie_first_timer")
        base.update(overrides)
        return Role(**base)

    def _legible_persona(self) -> Persona:
        # Fully concentrated on drama/leading_hero — a role in that lane reads as in_lane and a
        # role well outside it reads as breaking type.
        other_genres = ["comedy", "action", "horror", "thriller", "romance", "scifi", "period", "musical", "family"]
        other_archetypes = ["romantic_lead", "villain", "everyman", "mentor", "ingenue",
                             "authority", "comic_relief", "ensemble"]
        return Persona(
            genre_affinity={"drama": 100.0, **{g: 0.0 for g in other_genres}},
            archetype_affinity={"leading_hero": 100.0, **{a: 0.0 for a in other_archetypes}},
        )

    def test_studio_tentpole_forgives_typecasting_more_than_prestige_auteur(self):
        legibility = 100.0
        tentpole = gatekeeper_legibility_multiplier("studio_tentpole", legibility)
        auteur = gatekeeper_legibility_multiplier("prestige_auteur", legibility)
        self.assertLess(tentpole, 1.0)
        self.assertGreater(auteur, 1.0)
        self.assertLess(tentpole, auteur)

    def test_gatekeeper_multiplier_is_neutral_at_zero_legibility(self):
        self.assertAlmostEqual(gatekeeper_legibility_multiplier("prestige_auteur", 0.0), 1.0)
        self.assertAlmostEqual(gatekeeper_legibility_multiplier("studio_tentpole", 0.0), 1.0)

    def test_unknown_gatekeeper_is_neutral_rather_than_crashing(self):
        self.assertEqual(gatekeeper_legibility_multiplier("studio_head", 100.0), 1.0)

    def test_fit_score_reads_worse_at_a_prestige_auteur_than_a_tentpole_for_the_same_off_lane_role(self):
        persona = self._legible_persona()
        attrs = Attributes()
        off_lane_role_tentpole = self._role(genre="horror", archetype="ensemble", gatekeeper="studio_tentpole")
        off_lane_role_auteur = self._role(genre="horror", archetype="ensemble", gatekeeper="prestige_auteur")
        tentpole_fit = fit_score(attrs, persona, off_lane_role_tentpole, your_age=40)
        auteur_fit = fit_score(attrs, persona, off_lane_role_auteur, your_age=40)
        self.assertGreater(tentpole_fit, auteur_fit)

    def test_in_lane_matches_top_genre_or_top_archetype(self):
        persona = self._legible_persona()
        self.assertTrue(in_lane(persona, self._role(genre="drama", archetype="ensemble")))
        self.assertTrue(in_lane(persona, self._role(genre="horror", archetype="leading_hero")))
        self.assertFalse(in_lane(persona, self._role(genre="horror", archetype="ensemble")))

    def test_in_lane_audience_bonus_requires_in_lane_and_scales_with_legibility(self):
        legible = self._legible_persona()
        flat = Persona()
        in_lane_role = self._role(genre="drama", archetype="leading_hero")
        off_lane_role = self._role(genre="horror", archetype="ensemble")
        self.assertGreater(in_lane_audience_bonus(legible, in_lane_role), 0.0)
        self.assertEqual(in_lane_audience_bonus(legible, off_lane_role), 0.0)
        self.assertEqual(in_lane_audience_bonus(flat, in_lane_role), 0.0)

    def test_is_breaking_type_fires_on_a_real_stretch_not_an_ordinary_mismatch(self):
        legible = self._legible_persona()
        far_role = self._role(genre="horror", archetype="ensemble")
        near_role = self._role(genre="drama", archetype="leading_hero")
        self.assertGreaterEqual(typecasting_penalty(legible, far_role), BREAKING_TYPE_THRESHOLD)
        self.assertTrue(is_breaking_type(legible, far_role))
        # The exact same actor, cast in their own established lane, isn't breaking anything.
        self.assertFalse(is_breaking_type(legible, near_role))

    def test_type_break_difficulty_tax_only_applies_when_breaking_type(self):
        legible = self._legible_persona()
        far_role = self._role(genre="horror", archetype="ensemble")
        near_role = self._role(genre="drama", archetype="leading_hero")
        self.assertGreater(type_break_difficulty_tax(legible, far_role), 0.0)
        self.assertEqual(type_break_difficulty_tax(legible, near_role), 0.0)


if __name__ == "__main__":
    unittest.main()
