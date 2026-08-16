"""design/part-04-the-actor.md §4.1 — the actor's seven 0-100 attributes.

Craft, Instinct, Presence, Resilience are "core": they drive the Performance roll (§4.7).
Voice, Physicality, Look are "gates": they decide what roles are reachable at all and never
appear in the Performance roll itself.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace

from callback.engine.core.util import clamp

CORE_ATTRS = ("craft", "instinct", "presence", "resilience")
GATE_ATTRS = ("voice", "physicality", "look")

# v9 fix (§4.1): "Your Notices floor = 0.42 x Presence — was 0.10; at that weight the floor could
# never bind against a Notices mean of 58, so the verb never actually fired for anyone." At 0.42
# it does: a magnetic actor can be still and be noticed for it. This is the floor Presence sets on
# whatever shape.py computes for Notices, applied by simulation/career.py after the shoot resolves.
PRESENCE_NOTICES_FLOOR_COEF = 0.42


@dataclass(frozen=True)
class Attributes:
    craft: float = 50.0
    instinct: float = 50.0
    presence: float = 50.0
    voice: float = 50.0
    physicality: float = 50.0
    look: float = 50.0
    resilience: float = 50.0

    def clamped(self) -> "Attributes":
        return replace(self, **{f.name: clamp(getattr(self, f.name), 0.0, 100.0) for f in fields(self)})

    def age_decay(self, age: int) -> "Attributes":
        """One year's passive attribute decay from aging (§4.1's decay column). Craft, Instinct,
        and Resilience have no stated decay curve and are left untouched."""
        return replace(
            self,
            presence=self.presence - (0.5 if age > 55 else 0.0),
            voice=self.voice - (1.0 if age > 60 else 0.0),
            physicality=self.physicality - (2.0 if age > 45 else 0.0),
        ).clamped()

    def with_deltas(self, **deltas: float) -> "Attributes":
        """Generic growth hook: simulation/career.py applies post-project attribute nudges (e.g.
        Craft from coaching or working with a great director) through this rather than each caller
        touching dataclass fields directly. No growth logic lives here yet — §4.1's growth column
        (coaching, theatre work, repetition) is Rolodex/Prep-dependent and lands in a later pass;
        this method exists now so that pass doesn't need to change this class's shape."""
        return replace(self, **{k: getattr(self, k) + v for k, v in deltas.items()}).clamped()

    def notices_floor(self) -> float:
        return PRESENCE_NOTICES_FLOOR_COEF * self.presence
