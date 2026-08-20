"""Coverage-check tool for docs/design/decision-map.md (POLICY-02) — cross-references the
decision-map catalog's ID vocabulary against a `Counter` of decision points a policy run actually
visited, and reports which cataloged IDs were never visited. Not a design-doc-spec implementer
like the rest of `callback/engine/` — this module's spec is decision-map.md itself, the same way
this whole phase's new policy code cites that doc rather than a `part-NN-*.md` section.

Mirrors `simulation/verify.py`'s shape: a plain-function module, no classes, with a `__main__` CLI
block printing an OK/gap-list report. Coverage tracking lives entirely in the caller (the archetype
policy functions in `_archetype_policies.py`), using a `collections.Counter` — no logging/telemetry
layer is added to `Session` or any engine module, matching CLAUDE.md's "no new logging framework"
rule and RESEARCH.md's Pattern 2 (Coverage Gap Inventory tallying via caller-side Counter).
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

# callback/engine/simulation/_decision_coverage.py -> parents[2] is callback/, so this resolves to
# callback/docs/design/decision-map.md regardless of the caller's own working directory.
DECISION_MAP_PATH = Path(__file__).resolve().parents[2] / "docs" / "design" / "decision-map.md"

# The full archetype roster this phase's plans build out across Plans 01-05 (POLICY-01's ≥8
# minimum). Only prestige_chaser/franchise_maximizer exist after Plan 01 — referencing all 8 names
# here now is safe because run_full_coverage_check resolves each one lazily via getattr() only when
# actually called, so this tuple's shape never needs to change again as later plans fill it in.
ARCHETYPE_NAMES = (
    "prestige_chaser", "franchise_maximizer", "indie_purist", "risk_averse",
    "gambler", "director_track", "family_first", "burnout_avoider",
)

# A decision-map table row looks like "| `some.id` | ... |" once past the header/separator rows
# ("| ID | ... |" and "|---|---|..."). Matching a backtick-wrapped token as the very first cell is
# sufficient to distinguish a real ID row from either of those — no markdown-table parser needed.
_ID_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|")


def load_expected_ids(path: Path = DECISION_MAP_PATH) -> frozenset[str]:
    """Parses decision-map.md's own ID column at call time — the single source of truth for what
    counts as a cataloged decision point. Never hardcode a duplicate ID list anywhere else; any
    such list can silently drift from the doc as rows are added/renamed."""
    text = path.read_text(encoding="utf-8")
    ids: set[str] = set()
    for line in text.splitlines():
        match = _ID_ROW.match(line.strip())
        if match is None:
            continue
        candidate = match.group(1).strip()
        # Guards against accidentally matching a header row (literally "ID") or a markdown
        # separator row rendered as backticked dashes — neither is a real decision-point id.
        if not candidate or candidate == "ID" or set(candidate) <= {"-"}:
            continue
        ids.add(candidate)
    return frozenset(ids)


def check_coverage(visited: Counter, expected: frozenset[str] | None = None) -> list[str]:
    """Returns the sorted list of expected IDs that `visited` never recorded (count of zero or
    simply absent). Defaults `expected` to the full decision-map catalog."""
    if expected is None:
        expected = load_expected_ids()
    return sorted(id_ for id_ in expected if visited.get(id_, 0) == 0)


def run_with_coverage(policy_fn, seed: int, **kwargs) -> tuple[dict, Counter]:
    """Runs a single archetype policy function with a fresh Counter passed through as its
    `visited` kwarg, returning both the policy's own summary dict and the Counter it tallied
    against. `policy_fn` must accept `seed` and `visited` keyword arguments (every archetype in
    `_archetype_policies.py` does)."""
    visited: Counter = Counter()
    summary = policy_fn(seed=seed, visited=visited, **kwargs)
    return summary, visited


def run_full_coverage_check(seeds: list[int], years: int = 60) -> list[str]:
    """Runs every archetype in ARCHETYPE_NAMES, at every seed in `seeds`, accumulating all of
    their tallies into one shared Counter, then returns the merged gap list. Only meaningful once
    every archetype in ARCHETYPE_NAMES actually exists (Plan 05) — until then this reports many
    gaps by construction, which is the expected, correct behavior at every earlier stage of this
    phase, not a bug to chase."""
    from callback.engine.simulation import _archetype_policies

    merged: Counter = Counter()
    for name in ARCHETYPE_NAMES:
        policy_fn = getattr(_archetype_policies, name, None)
        if policy_fn is None:
            continue
        for seed in seeds:
            policy_fn(seed=seed, years=years, visited=merged)
    return check_coverage(merged)


if __name__ == "__main__":
    gaps = run_full_coverage_check(seeds=[1, 2], years=60)
    if gaps:
        for decision_id in gaps:
            print(f"<<< UNVISITED  {decision_id}")
    else:
        print("OK - zero gaps")
