"""design/part-07-the-director.md §7.2 — director attributes (0-100): Vision, Command, Craft,
Taste, Efficiency. Command and Craft are the same-named concepts actor/performance.py and
actor/reception.py already read as director_command/director_skill inputs — this module is where
a real director (player or NPC) produces those numbers instead of a caller sampling them.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace

from callback.engine.core.util import clamp

TASTE_NOISE_BASE = 26.0
TASTE_NOISE_COEF = 0.22  # higher Taste narrows the error band on a script read


@dataclass(frozen=True)
class DirectorAttributes:
    vision: float = 50.0
    command: float = 50.0
    craft: float = 50.0
    taste: float = 50.0
    efficiency: float = 50.0

    def clamped(self) -> "DirectorAttributes":
        return replace(self, **{f.name: clamp(getattr(self, f.name), 0.0, 100.0) for f in fields(self)})


def perceived_script_quality(true_quality: float, taste: float, rng) -> float:
    """§7.2 — "Taste makes you see clearly": PerceivedScriptQuality = TrueScriptQuality +
    N(0, 26 - 0.22*Taste). At Taste 20, reading through +-21 of fog; at Taste 95, +-5."""
    sigma = max(1.0, TASTE_NOISE_BASE - TASTE_NOISE_COEF * taste)
    return clamp(true_quality + rng.gauss(0.0, sigma), 0.0, 100.0)
