"""actor/studios.py — every studio actually spends different money on your film, and that money
(not just your release-strategy choice) shows up in Opening/ROI/streaming payouts.
"""
from __future__ import annotations

import random
import unittest

from callback.engine.actor.reception import BREAK_EVEN_MARKETING_SHARE, RIGHTS_SHARE, resolve_reception
from callback.engine.actor.release import STREAMING_BUYOUT_MULTIPLIER, STREAMING, apply_release_strategy
from callback.engine.actor.studios import STUDIOS, marketing_share_for, pick_studio


class TestStudioProfiles(unittest.TestCase):
    def test_every_studio_has_a_plausible_marketing_share(self):
        for studio in STUDIOS.values():
            for budget in (5.0, 30.0, 150.0):
                share = marketing_share_for(studio, budget)
                self.assertGreaterEqual(share, 0.0)
                self.assertLessEqual(share, 1.0)

    def test_blockbuster_uses_tiered_curve_not_flat_share(self):
        blockbuster = STUDIOS["blockbuster"]
        self.assertLess(marketing_share_for(blockbuster, 5.0), marketing_share_for(blockbuster, 150.0))

    def test_indie_spends_less_than_blockbuster_at_comparable_budget(self):
        indie, blockbuster = STUDIOS["indie"], STUDIOS["blockbuster"]
        self.assertLess(marketing_share_for(indie, 12.0), marketing_share_for(blockbuster, 12.0))


class TestPickStudio(unittest.TestCase):
    def test_tiny_budget_never_lands_at_the_blockbuster_machine(self):
        rng = random.Random(1)
        for _ in range(200):
            studio = pick_studio(3.0, rng)
            self.assertNotEqual(studio.id, "blockbuster")

    def test_huge_budget_never_lands_at_the_indie_house(self):
        rng = random.Random(2)
        for _ in range(200):
            studio = pick_studio(200.0, rng)
            self.assertNotEqual(studio.id, "indie")


class TestMarketingAffectsReception(unittest.TestCase):
    def _resolve(self, marketing_share, rng):
        return resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng,
            marketing_share=marketing_share, opening_marketing_coef=0.60,
        )

    def test_higher_marketing_share_buys_a_bigger_opening_at_same_budget(self):
        low = self._resolve(0.20, random.Random(10))
        high = self._resolve(0.80, random.Random(10))
        self.assertGreater(high.opening, low.opening)

    def test_default_marketing_share_matches_flat_baseline_behaviour(self):
        rng_a, rng_b = random.Random(5), random.Random(5)
        default_result = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng_a,
        )
        explicit_result = self._resolve(BREAK_EVEN_MARKETING_SHARE, rng_b)
        # opening_marketing_coef=0 by default, so an explicit baseline share matches the old flat path
        self.assertAlmostEqual(default_result.opening, resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=random.Random(5),
            marketing_share=BREAK_EVEN_MARKETING_SHARE, opening_marketing_coef=0.0,
        ).opening)


class TestStreamerBuyoutBonus(unittest.TestCase):
    def test_streamer_studio_bonus_multiplier_beats_flat_preset(self):
        rng = random.Random(3)
        reception = resolve_reception(
            script_quality=60, director_skill=60, craft_contribution=60, genre="drama",
            role_budget_millions=30, director_prestige=50, staleness_penalty=0,
            cast_star_power=50, genre_demand=55, rng=rng,
        )
        streamer = STUDIOS["streamer"]
        boosted = apply_release_strategy(
            reception, STREAMING, rng, streaming_multiplier=STREAMING_BUYOUT_MULTIPLIER + streamer.streaming_multiplier_delta,
        )
        flat = apply_release_strategy(reception, STREAMING, rng)
        self.assertGreater(boosted.gross, flat.gross)


if __name__ == "__main__":
    unittest.main()
