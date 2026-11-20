"""The Stage convention every actor/ formula module's main entry point follows.

This is not a generic auto-composing pipeline — each step of the season loop takes differently
shaped input (a role listing, a prep choice, three scene decisions, a finished performance...) so
there's no single State type to chain them through. What Stage buys instead is a *convention*,
enforced by the type checker rather than just prose:

  - every stage's public entry point has the exact shape (state, rng) -> result
  - simulation/career.py depends on that shape only — it never reaches past a stage's function
    signature into its module-level constants or helper functions
  - any stage can be swapped for a stub or tested in isolation, because its entire contract is
    that one call signature

Stage functions in actor/ don't inherit from anything or import this module at all — they satisfy
Stage structurally, which is what keeps the dependency direction one-way (actor/ never imports
simulation/, and doesn't need to import core.pipeline either to conform to it).
"""
from __future__ import annotations

import random
from typing import Protocol, TypeVar

StateT = TypeVar("StateT", contravariant=True)
ResultT = TypeVar("ResultT", covariant=True)


class Stage(Protocol[StateT, ResultT]):
    """A single resolvable step of the season loop: (state, rng) -> result, nothing else."""

    def __call__(self, state: StateT, rng: random.Random) -> ResultT: ...
