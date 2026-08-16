"""Meter and StandingModel — the reusable shape behind design/part-04-the-actor.md §4.3's
Standing (Heat/Prestige/Affection/Notoriety) and, later, any other career's equivalent.

design/part-03-design-overview.md §3.3 states the rule in prose: "one Standing model... if a new
career needs its own version of any of those systems, the design is wrong." This module is that
rule as code — a future DirectorStanding or ExecutiveStanding is a second *instantiation* of
StandingModel with its own meter names and gatekeeper weights, not a second implementation of
clamping, decay, and weighted-score reduction.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from callback.engine.core.util import clamp


@dataclass
class Meter:
    """A single bounded, named stat. No career-specific meaning lives here — Heat and a future
    ExecutiveStanding's "board patience" are both just a Meter with different names and bounds."""

    name: str
    value: float
    lo: float = 0.0
    hi: float = 100.0

    def clamped(self) -> float:
        return clamp(self.value, self.lo, self.hi)

    def set(self, value: float) -> None:
        self.value = clamp(value, self.lo, self.hi)

    def add(self, delta: float) -> None:
        self.set(self.value + delta)

    def decay_multiplicative(self, factor: float) -> None:
        """Proportional decay: value *= factor. This is the shape every meter in design/ uses —
        including Heat, whose factor just happens to be computed elsewhere (it depends on this
        year's billing tier) rather than being a fixed constant like Prestige's 0.985."""
        self.set(self.value * factor)


@dataclass
class StandingModel:
    """A named collection of Meters plus a weighted-scalar reducer.

    Deliberately career-agnostic: it knows nothing about "Heat" or "acting" specifically. A
    concrete career (actor/standing.py) configures one of these with its own meter names, initial
    values, and gatekeeper weight table; the reduction logic (weighted_score) is shared.
    """

    meters: dict[str, Meter] = field(default_factory=dict)

    def copy(self) -> "StandingModel":
        """A deep-enough copy for functional-update use: fresh Meter instances, so mutating the
        copy (via add()/decay()) never touches the original's meters. Plain dict(self.meters)
        would copy the dict but alias the same Meter objects — this avoids that trap."""
        return StandingModel(meters={name: Meter(m.name, m.value, m.lo, m.hi) for name, m in self.meters.items()})

    def __getitem__(self, name: str) -> float:
        return self.meters[name].clamped()

    def add(self, name: str, delta: float) -> None:
        self.meters[name].add(delta)

    def decay(self, factors: dict[str, float]) -> None:
        """Apply one decay step. `factors` maps meter name -> multiplicative retention factor for
        this step. Callers compute the (possibly context-dependent, e.g. billing-tier-aware)
        factor and pass it in — StandingModel itself holds no career-specific decay logic."""
        for name, factor in factors.items():
            self.meters[name].decay_multiplicative(factor)

    def weighted_score(self, weights: dict[str, float]) -> float:
        """Σ weight[m] * meter[m] — the StandingScore/gatekeeper-weighting pattern (§4.3's
        gatekeeper table). Any career's own gatekeeper weighting reuses this same reduction."""
        return sum(w * self[name] for name, w in weights.items())

    def as_dict(self) -> dict[str, float]:
        return {name: m.clamped() for name, m in self.meters.items()}
