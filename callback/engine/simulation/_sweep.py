"""Automated sweep infrastructure (SWEEP-01/SWEEP-02) — runs the completed 8-archetype policy
set from Phase 1 (`_archetype_policies.ARCHETYPE_NAMES`) at volume across many seeds, producing
per-policy outcome statistics and separately flagging stuck/dead-end runs.

Not a design-doc-spec implementer — this module's job is measurement, not mechanics, the same
role `simulation/verify.py` plays for individual formulas. It calls the archetype functions built
in Phase 1 exactly as they are; it never reaches into engine internals.

Trajectory sampling note: individual archetype functions only return an endpoint standing
snapshot, not a full yearly time series. Rather than instrument all 8 functions to record one,
this module gets real trajectory data for free by re-running the SAME (seed, archetype) pair at
several truncated `years` values — archetype functions are pure given (seed, years), and the
engine's RNG consumption is strictly sequential, so a shorter run reproduces the same career up to
where it stops. Trajectory sampling is deliberately restricted to a handful of seeds per archetype
(not the full sweep) to keep sweep runtime reasonable — see TRAJECTORY_SEED_COUNT.
"""
from __future__ import annotations

import statistics as st
from collections import Counter
from dataclasses import dataclass, field

from callback.engine.simulation import _archetype_policies as ap
from callback.engine.simulation._decision_coverage import ARCHETYPE_NAMES

# A run is classified a "dead end" when the career never really got off the ground AND ends in
# financial distress — the concrete, checkable proxy for ROADMAP Phase 2's "stranded with no
# meaningful further options" (the engine has no separate death/retirement mechanic; every run
# otherwise ends the same way, at MAX_AGE, so "how it ends" can't be the signal — "what state it's
# stuck in" has to be). Both bars are deliberately low: a real career only needs a handful of
# credits to be "on its way", and net_worth < 0 means life.money's own lifestyle-floor-cut logic
# has already fired at least once this run.
DEAD_END_CREDITS_MAX = 2
DEAD_END_NET_WORTH_MAX = 0.0

TRAJECTORY_SEED_COUNT = 3
TRAJECTORY_YEAR_CHECKPOINTS = (15, 30, 45, 60)


def _credits_of(result: dict) -> int:
    return result.get("acting_credits", 0) + result.get("director_credits", 0)


def _standing_of(result: dict) -> dict:
    return result.get("actor_standing") or result.get("director_standing") or {}


def _is_dead_end(result: dict) -> bool:
    return _credits_of(result) <= DEAD_END_CREDITS_MAX and result.get("net_worth", 0.0) < DEAD_END_NET_WORTH_MAX


@dataclass
class PolicyStats:
    archetype: str
    runs: int
    dead_end_runs: int
    dead_end_rate: float
    age_mean: float
    net_worth_mean: float
    net_worth_median: float
    net_worth_stdev: float
    credits_mean: float
    standing_means: dict
    obituary_credits_mean: float
    trajectories: list = field(default_factory=list)  # [{seed, checkpoints: [{year, standing}]}]
    franchise_holders: int = 0  # runs that ever held a franchise (archetypes that track one)


def run_policy_sweep(archetype: str, seeds: range, years: int = 60, sample_trajectory: bool = True) -> PolicyStats:
    """Runs one archetype across `seeds`, returns its aggregate PolicyStats. Never raises on an
    individual run's own engine exceptions — a crash IS a finding (a real, load-bearing bug this
    sweep exists to surface), so it propagates rather than being silently swallowed; this function
    itself does no exception handling, matching CLAUDE.md's "defensive math over exceptions" —
    a policy/engine bug should be loud, not absorbed into a stat."""
    fn = getattr(ap, archetype)

    ages, net_worths, credits_list, dead_ends = [], [], [], 0
    standing_axes = Counter()
    standing_counts = Counter()
    obituary_credits = []
    franchise_holders = 0

    for seed in seeds:
        result = fn(seed=seed, years=years)
        ages.append(result["age"])
        net_worths.append(result["net_worth"])
        credits_list.append(_credits_of(result))
        if _is_dead_end(result):
            dead_ends += 1
        for axis, value in _standing_of(result).items():
            standing_axes[axis] += value
            standing_counts[axis] += 1
        obituary_credits.append(result.get("obituary", {}).get("credits", 0))
        if result.get("own_franchise_id") or result.get("held_franchise_ids"):
            franchise_holders += 1

    trajectories = []
    if sample_trajectory:
        for seed in list(seeds)[:TRAJECTORY_SEED_COUNT]:
            checkpoints = []
            for checkpoint_years in TRAJECTORY_YEAR_CHECKPOINTS:
                if checkpoint_years > years:
                    break
                r = fn(seed=seed, years=checkpoint_years)
                checkpoints.append({"year": checkpoint_years, "standing": _standing_of(r)})
            trajectories.append({"seed": seed, "checkpoints": checkpoints})

    n = len(ages)
    return PolicyStats(
        archetype=archetype,
        runs=n,
        dead_end_runs=dead_ends,
        dead_end_rate=round(dead_ends / n, 3) if n else 0.0,
        age_mean=round(st.mean(ages), 1) if ages else 0.0,
        net_worth_mean=round(st.mean(net_worths), 1) if net_worths else 0.0,
        net_worth_median=round(st.median(net_worths), 1) if net_worths else 0.0,
        net_worth_stdev=round(st.pstdev(net_worths), 1) if len(net_worths) > 1 else 0.0,
        credits_mean=round(st.mean(credits_list), 1) if credits_list else 0.0,
        standing_means={axis: round(total / standing_counts[axis], 1) for axis, total in standing_axes.items()},
        obituary_credits_mean=round(st.mean(obituary_credits), 1) if obituary_credits else 0.0,
        trajectories=trajectories,
        franchise_holders=franchise_holders,
    )


def run_full_sweep(
    seeds_per_policy: int = 50, years: int = 60, seed_start: int = 1000, sample_trajectory: bool = False,
) -> dict[str, PolicyStats]:
    """Runs every archetype in ARCHETYPE_NAMES (Phase 1's completed 8-archetype set) across
    `seeds_per_policy` seeds each, in one invocation. `seed_start` deliberately sits well above
    Phase 1's own hand-picked seeds (1-41ish) so a sweep never accidentally re-tests only the
    seeds Phase 1's smoke tests already know behave a certain way.

    `sample_trajectory` defaults to False: each trajectory checkpoint re-runs an archetype from
    seed 1 up to that checkpoint's year (years are not resumable mid-run), so sampling at 4
    checkpoints costs ~2.5x a single full run for just those seeds — real, avoidable overhead for
    a stat most sweep invocations (dead-end/dominance/net-worth checks) never read. Pass
    sample_trajectory=True explicitly when trajectory data is actually wanted."""
    return {
        name: run_policy_sweep(name, range(seed_start, seed_start + seeds_per_policy), years=years, sample_trajectory=sample_trajectory)
        for name in ARCHETYPE_NAMES
    }


def print_sweep_report(stats_by_archetype: dict[str, PolicyStats]) -> None:
    print("=== SWEEP REPORT ===\n")
    header = f"{'Archetype':<20} {'Runs':>5} {'DeadEnd%':>9} {'Age':>6} {'NetWorth':>10} {'Credits':>8}"
    print(header)
    print("-" * len(header))
    for name, s in stats_by_archetype.items():
        print(f"{name:<20} {s.runs:>5} {s.dead_end_rate*100:>8.1f}% {s.age_mean:>6.1f} {s.net_worth_mean:>9.1f}M {s.credits_mean:>8.1f}")
    print()
    for name, s in stats_by_archetype.items():
        print(f"--- {name} ---")
        print(f"  Standing (mean at end): {s.standing_means}")
        print(f"  Obituary credits (mean): {s.obituary_credits_mean}")
        if s.franchise_holders:
            print(f"  Held a franchise in {s.franchise_holders}/{s.runs} runs")
        print()


if __name__ == "__main__":
    import sys
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    stats = run_full_sweep(seeds_per_policy=n)
    print_sweep_report(stats)
