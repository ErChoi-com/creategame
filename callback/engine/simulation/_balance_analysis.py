"""Balance analysis (ANLZ-01/02/03) — reads PolicyStats from `_sweep.py` and surfaces dominant
strategies, dead ends, and low-variance outcome clusters. Each finding is framed by why it matters
in career-simulation/believability terms, not just as a stat anomaly, per this milestone's
immersiveness-first philosophy (ROADMAP.md's Overview).

Not a design-doc-spec implementer — this module's job is interpretation over `_sweep.py`'s
numbers, the way `_sweep.py` itself is measurement over the archetype policies.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from callback.engine.simulation._sweep import PolicyStats

# A policy "dominates" only if it beats every other policy on ALL of these metrics at once —
# a single-metric leader (e.g. highest net worth) is common and not itself concerning; true
# dominance (nothing else is ever a better choice on any axis that matters) is the real target.
DOMINANCE_METRICS = ("net_worth_mean", "credits_mean", "age_mean")

# A believability-relevant "elite tier" ceiling — used to flag when NO policy ever gets there,
# distinct from ordinary win/lose variance. Mirrors Phase 1's own Flagged Balance Findings.
ELITE_STANDING_FLOOR = 50.0


@dataclass
class Finding:
    kind: str  # "dominant_strategy" | "dead_end" | "low_variance_cluster" | "no_dominance"
    summary: str
    believability_note: str
    evidence: dict = field(default_factory=dict)


def find_dominant_strategy(stats_by_archetype: dict[str, PolicyStats]) -> Finding:
    """ANLZ-01: ranks policies on DOMINANCE_METRICS; only reports an actual dominant policy if
    one archetype is strictly best on every metric — otherwise explicitly confirms none does."""
    names = list(stats_by_archetype.keys())
    best_per_metric = {}
    for metric in DOMINANCE_METRICS:
        ranked = sorted(names, key=lambda n: getattr(stats_by_archetype[n], metric), reverse=True)
        best_per_metric[metric] = ranked[0]

    unique_leaders = set(best_per_metric.values())
    if len(unique_leaders) == 1:
        winner = next(iter(unique_leaders))
        return Finding(
            kind="dominant_strategy",
            summary=f"{winner} leads every dominance metric ({', '.join(DOMINANCE_METRICS)}) — a real dominant strategy.",
            believability_note=(
                f"If {winner} is simply the objectively correct way to play, every other archetype's "
                "distinct approach (different backgrounds, risk profiles, career shapes) becomes "
                "flavor text rather than a real choice — the opposite of this milestone's Core Value."
            ),
            evidence={"best_per_metric": best_per_metric, "stats": {n: vars(s) for n, s in stats_by_archetype.items()}},
        )
    return Finding(
        kind="no_dominance",
        summary=f"No single policy dominates every metric — leaders split across {unique_leaders}.",
        believability_note="Different archetypes trade off differently, which is the intended shape of a believable career-choice space.",
        evidence={"best_per_metric": best_per_metric},
    )


def find_dead_ends(stats_by_archetype: dict[str, PolicyStats], dead_end_rate_floor: float = 0.15) -> list[Finding]:
    """ANLZ-02: flags any archetype whose sweep-measured dead_end_rate exceeds the floor, and
    separately flags any Standing axis that NO archetype's sweep ever got near ELITE_STANDING_FLOOR
    — a structural dead end in the underlying mechanic, not any one policy's fault."""
    findings = []
    for name, s in stats_by_archetype.items():
        if s.dead_end_rate > dead_end_rate_floor:
            findings.append(Finding(
                kind="dead_end",
                summary=f"{name}: {s.dead_end_rate*100:.0f}% of runs ended stranded (low credits, negative net worth).",
                believability_note=(
                    f"A player choosing {name} more than 1-in-{round(1/s.dead_end_rate) if s.dead_end_rate else 0} times "
                    "ends up broke and unemployed with nothing to show for a whole career — that reads as a punishing "
                    "trap, not a real Hollywood career arc with recoverable low points."
                ),
                evidence={"dead_end_rate": s.dead_end_rate, "dead_end_runs": s.dead_end_runs, "runs": s.runs},
            ))

    all_axes = set()
    for s in stats_by_archetype.values():
        all_axes.update(s.standing_means.keys())
    for axis in sorted(all_axes):
        peak = max((s.standing_means.get(axis, 0.0) for s in stats_by_archetype.values()), default=0.0)
        if peak < ELITE_STANDING_FLOOR:
            findings.append(Finding(
                kind="dead_end",
                summary=f"No archetype's mean {axis} Standing ever approaches {ELITE_STANDING_FLOOR} (peak observed: {peak:.1f}).",
                believability_note=(
                    f"An engine where nobody, playing any way, ever becomes a real {axis}-driven star reads as a "
                    "capped, small-time industry rather than one where a rare few actually break through — the "
                    "believable version of Hollywood has real A-listers, even if most careers never get there."
                ),
                evidence={"axis": axis, "peak_mean": peak, "per_archetype": {n: s.standing_means.get(axis) for n, s in stats_by_archetype.items()}},
            ))
    return findings


def find_low_variance_clusters(stats_by_archetype: dict[str, PolicyStats], net_worth_gap_floor: float = 3.0) -> list[Finding]:
    """ANLZ-03: groups archetypes into connected clusters whose mean net_worth outcomes are all
    within net_worth_gap_floor (millions) of a neighbor — reported as clusters, not an O(n^2) pair
    list, so 8 archetypes converging on one outcome reads as ONE finding, not 20. Also reports the
    single clearest signal of "does the choice even matter": the full spread across every
    archetype's mean net worth."""
    names = sorted(stats_by_archetype.keys(), key=lambda n: stats_by_archetype[n].net_worth_mean)
    findings = []

    # Union-find over the sorted-by-value list: adjacent archetypes within the gap floor merge
    # into the same cluster (transitively) — a simple, correct clustering for one scalar metric.
    clusters: list[list[str]] = [[names[0]]] if names else []
    for prev, cur in zip(names, names[1:]):
        gap = abs(stats_by_archetype[cur].net_worth_mean - stats_by_archetype[prev].net_worth_mean)
        if gap <= net_worth_gap_floor:
            clusters[-1].append(cur)
        else:
            clusters.append([cur])

    for cluster in clusters:
        if len(cluster) < 2:
            continue
        values = {n: stats_by_archetype[n].net_worth_mean for n in cluster}
        findings.append(Finding(
            kind="low_variance_cluster",
            summary=f"{len(cluster)} archetypes converge on statistically similar net worth: {cluster} (${min(values.values()):.1f}M to ${max(values.values()):.1f}M).",
            believability_note=(
                f"{', '.join(cluster)} represent genuinely different philosophies of how to build a career — if "
                "they all land in roughly the same financial place, the choice between them reads as cosmetic "
                "rather than a real fork with real stakes."
            ),
            evidence={"archetypes": cluster, "net_worth_by_archetype": values},
        ))

    if names:
        overall_spread = stats_by_archetype[names[-1]].net_worth_mean - stats_by_archetype[names[0]].net_worth_mean
        if overall_spread <= net_worth_gap_floor * 2:
            findings.append(Finding(
                kind="low_variance_cluster",
                summary=f"Net worth barely differentiates ANY archetype: full spread across all {len(names)} is only ${overall_spread:.1f}M ({names[0]}={stats_by_archetype[names[0]].net_worth_mean}M to {names[-1]}={stats_by_archetype[names[-1]].net_worth_mean}M).",
                believability_note=(
                    "If a franchise-chaser, a gambler, and a family-first actor all end up financially in the same "
                    "place, money isn't actually shaped by the choices a player makes — a core stat the player "
                    "should be able to meaningfully move isn't responding to strategy at all."
                ),
                evidence={"overall_spread": overall_spread, "lowest": names[0], "highest": names[-1]},
            ))
    return findings


def run_full_analysis(stats_by_archetype: dict[str, PolicyStats]) -> dict[str, list[Finding] | Finding]:
    return {
        "dominant_strategy": find_dominant_strategy(stats_by_archetype),
        "dead_ends": find_dead_ends(stats_by_archetype),
        "low_variance_clusters": find_low_variance_clusters(stats_by_archetype),
    }


def print_analysis_report(analysis: dict) -> None:
    print("=== BALANCE ANALYSIS REPORT ===\n")
    dom = analysis["dominant_strategy"]
    print(f"[{dom.kind.upper()}] {dom.summary}")
    print(f"  Why it matters: {dom.believability_note}\n")

    print(f"--- Dead Ends ({len(analysis['dead_ends'])}) ---")
    for f in analysis["dead_ends"]:
        print(f"  - {f.summary}")
        print(f"    Why it matters: {f.believability_note}")
    print()

    print(f"--- Low-Variance Clusters ({len(analysis['low_variance_clusters'])}) ---")
    for f in analysis["low_variance_clusters"]:
        print(f"  - {f.summary}")
        print(f"    Why it matters: {f.believability_note}")


if __name__ == "__main__":
    import sys
    from callback.engine.simulation._sweep import run_full_sweep

    n = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    stats = run_full_sweep(seeds_per_policy=n)
    analysis = run_full_analysis(stats)
    print_analysis_report(analysis)
