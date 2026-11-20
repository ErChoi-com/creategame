# Phase 1: Decision Space & Playtest Policy Coverage — Summary

**Status:** Complete
**Requirements satisfied:** MAP-01, POLICY-01, POLICY-02

## What was built

- `callback/docs/design/decision-map.md` — the ground-truth catalog of every mechanically-branching decision point reachable through `Session`, one row per option, each citing source module/function and design-doc section.
- `callback/engine/simulation/_decision_coverage.py` — coverage-check tool: parses `decision-map.md`'s own ID column (never a duplicate hardcoded list) and reports which IDs a policy run's `Counter` never visited.
- `callback/engine/simulation/_archetype_policies.py` — 8 scripted playtest archetypes (`prestige_chaser`, `franchise_maximizer`, `indie_purist`, `risk_averse`, `gambler`, `director_track`, `family_first`, `burnout_avoider`), each driving a full simulated career through `Session` and tallying every decision point it exercises.
- `callback/engine/simulation/_sim_policy_shared.py` — added `CONTRAST_SCENE_POSITIONS` (gambler's extreme-swing scene default).
- `callback/engine/tests/test_archetype_policies.py`, `test_decision_coverage.py` — smoke tests per archetype plus `TestFullEightArchetypeCoverage`, the real POLICY-02 verification gate.

## Coverage result

Starting from a full cross-reference against `decision-map.md`, the 8-archetype set closed 69 initial gaps (found after the first 5 archetypes) down to **zero required gaps**, verified at realistic sampling volume (prestige_chaser across 120 seeds for the two rarest awards categories, 14+ seeds per remaining archetype).

## Flagged findings (real balance signal, not policy bugs)

Five decision points are excluded from required coverage because they are genuinely threshold-blocked under current tuning, not reachable by any archetype's simulated play:

1. Approvals (script/costar negotiation) — `APPROVAL_STANDING_THRESHOLD = 65.0`; best achieved across a 59-seed sweep was ~18.
2. First-dollar-gross box-office bonus — `FIRST_DOLLAR_GROSS_STANDING_THRESHOLD = 85.0`.
3. Merchandising — animated-franchise-role AND Standing gate, compounding.
4. Actor-track franchise spin-off launch — `SPINOFF_INDISPENSABILITY_THRESHOLD = 55.0` + lead requirement.
5. Director-track franchise spin-off pitch — same threshold, no lead requirement.

Full rationale and citations are in `decision-map.md`'s "Flagged Balance Findings" section. **These five all point at the same underlying pattern — elite Standing/Indispensability tiers are effectively unreachable through normal simulated play — which Phase 3's balance analysis should treat as one first-class finding, not five unrelated ones.** Phase 4 decides whether the thresholds or the Standing/Indispensability gain-decay curves are the correct lever.

Two additional decision points (`awards.actor.category.breakthrough`, `awards.actor.category.lead_comedy`) are rare but confirmed reachable at wider seed volume — they remain required coverage and were not excluded.

Also documented (not a coverage gap, a pre-existing bug): `simulation/_quality_report.py:213` calls `run_awards_campaign` without the required `category` argument — a latent `TypeError` in a superseded script this phase didn't touch. Every new archetype calls it correctly.

## Verification

`python3 -m unittest discover callback/engine/tests` — 680 tests, all green (6 skipped, pre-existing/unrelated).

## Next

Phase 2 (Automated Sweep Infrastructure) builds a volume runner over this 8-archetype policy set, producing per-policy outcome statistics and flagging stuck/dead-end runs.
