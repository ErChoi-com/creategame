"""actor/ formula edge cases, including the two v9-fixed values this pass must not regress:
the open-offer Utility margin (14, not the broken pre-v9 25) and the Presence Spotlight-floor
coefficient (0.42, not the pre-v9 0.10 that never bound against a Spotlight mean of ~58).
"""
from __future__ import annotations

import unittest

from callback.engine.actor.attributes import Attributes, PRESENCE_SPOTLIGHT_FLOOR_COEF
from callback.engine.actor.offers import (
    OPEN_OFFER_UTILITY_MARGIN,
    Role,
    age_mismatch_penalty,
    fit_score,
    resolve_casting_path,
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
        other_archetypes = ["romantic_lead", "villain", "everyman", "character_actor", "ingenue",
                             "authority", "comic_relief", "wildcard"]
        p = Persona(
            genre_affinity={"drama": 100.0, **{g: 0.0 for g in other_genres}},
            archetype_affinity={"leading_hero": 100.0, **{a: 0.0 for a in other_archetypes}},
        )
        self.assertGreater(p.legibility(), LEGIBILITY_MID_MAX)
        self.assertEqual(p.legibility_band(), "high")


if __name__ == "__main__":
    unittest.main()
