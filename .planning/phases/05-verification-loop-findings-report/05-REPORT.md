# Callback — Playtest & Balance Pass: Findings & Changes Report

**Milestone:** v1.0 | **Date:** 2026-08-20 | **Status:** Complete

## Summary

A 5-phase systematic playtest of the Callback engine: catalog every decision point → build 8 scripted playtest archetypes that exercise all of them → run automated sweeps at volume → analyze for balance issues → tune, informed by both engine research and the design doc's own validated targets → re-verify. One root-cause engine change landed; several related findings are documented and deliberately deferred rather than force-fixed.

## Method

- **Decision map:** `callback/docs/design/decision-map.md` — 100+ cataloged decision points across character creation, offers, prep, scenes, leverage, franchises, director mode, life, and awards.
- **Playtest archetypes:** `callback/engine/simulation/_archetype_policies.py` — 8 scripted policies (prestige_chaser, franchise_maximizer, indie_purist, risk_averse, gambler, director_track, family_first, burnout_avoider), each driving a full simulated career and closing specific coverage gaps.
- **Coverage tool:** `_decision_coverage.py` — confirmed 100% required coverage across the 8-archetype set (69 initial gaps found and closed to zero, 5 genuinely threshold-blocked items formally excluded with rationale).
- **Sweep infrastructure:** `_sweep.py` — runs the full policy set at volume (50+ seeds/policy verified without crashing), producing per-policy net worth, credits, Standing, obituary, and franchise statistics, plus dead-end classification.
- **Balance analysis:** `_balance_analysis.py` — dominant-strategy check, dead-end detection (per-archetype rate + structural Standing-ceiling check), low-variance clustering.

## Findings and what changed

| # | Finding | Believability framing | Status | Design-doc section touched |
|---|---------|------------------------|--------|------------------------------|
| 1 | No dominant strategy across archetypes | Different philosophies trade off differently — the intended shape | ✅ Confirmed healthy, no fix needed | — |
| 2 | **Heat Standing ceiling** — no archetype approached the design doc's own validated "~18% of careers reach Heat>80" target (0/59 in a maximally-engaged naive-policy test) | An industry where nobody ever becomes a real heat-driven star reads as capped and small-time | ✅ **Fixed** — `HEAT_BASE` 7.9→8.6; naive-policy ceiling now clears 80 | `actor/standing.py`, cites `design/part-14-tuning-targets.md` §14.9 |
| 3 | **Prestige/Affection/Notoriety ceilings** — no archetype's mean Standing on these axes ever approached 50 | Same "no real stars ever emerge" problem, worse on these axes | ⚠️ **Partially addressed** — coefficients raised ~35-40%, measurable improvement (peaks roughly doubled), but root-cause analysis found none of the 8 archetypes deliberately optimize scene-position choice for these axes, so the real ceiling wasn't fully closed. **Flagged for a future milestone**, not force-tuned further on a hunch. | `actor/standing.py` |
| 4 | **Approvals negotiation unreachable** (`APPROVAL_STANDING_THRESHOLD=65`) | Elite-tier leverage that's mathematically unreachable reads as fake choice architecture | Downstream of #3 — improves as #3 improves, not independently fixed this pass | `decision-map.md` Flagged Balance Findings |
| 5 | **First-dollar-gross bonus unreachable** (`threshold=85`) | Same pattern, higher bar | Downstream of #3 | `decision-map.md` |
| 6 | **Merchandising unreachable** (animated-role + Standing gate) | Same pattern, compounded by animation-role rarity | Downstream of #3, plus a separate rarity issue not investigated this pass | `decision-map.md` |
| 7 | **Both franchise spin-off thresholds unreachable** (`SPINOFF_INDISPENSABILITY_THRESHOLD=55`) | Same "elite tier nobody reaches" pattern, on a separate Indispensability curve | Not investigated this pass — flagged as a same-shaped problem on a different meter | `decision-map.md` |
| 8 | **Net worth low-variance cluster** — 6-7 of 8 archetypes converge within a few million dollars of mean net worth despite very different strategies | Money not tracking player choice reads as cosmetic decisions | ⚠️ **Not fixed this pass** — real, verified finding (stable across 3 independent sweep runs), root cause not yet isolated (candidate levers: `life/money.py` income formulas, fee/bonus scaling vs. `lifestyle_floor`) | Flagged for a future milestone |

## Verification

Re-running the full sweep + analysis after the fix (3 independent runs, 15-20 seeds/policy, seeds not overlapping Phase 1's smoke-test seeds):
- Finding #2 (Heat ceiling): **resolved**, consistently, across all 3 re-runs.
- Findings #3, #8: **persist, unchanged in kind**, consistent magnitude across re-runs (not worsening — no regression).
- **No new findings introduced** by the fix.
- Full engine test suite (680 tests) green after every change, including the one test (`test_director_mode.py`) whose fixture needed updating to reflect the intentional coefficient change (a genuine floor-clamp interaction, not a false pass).

## What's explicitly out of scope / deferred

Per the Consolidated Root-Cause Hypothesis (`03-FINDINGS.md`) and the Change 1 changelog (`04-CHANGELOG.md`), findings #3-#8 above share one underlying pattern — elite Standing/Indispensability tiers are structurally hard to reach — but fully closing it would require either a much larger, less-evidenced coefficient jump, or redesigning archetype scene-position/role-selection strategy to actually pursue these axes (a Phase-1-shaped change, not a tuning-pass change). Consistent with this project's "no dead ends, but don't force a fix you can't justify" philosophy, these are recorded as real, verified findings for a follow-up milestone rather than guessed at further within this pass's scope.

## Requirements closed this milestone

MAP-01, POLICY-01, POLICY-02, SWEEP-01, SWEEP-02, ANLZ-01, ANLZ-02, ANLZ-03, TUNE-01, TUNE-02, TEST-01, RSCH-01, VRFY-01, RPRT-01 — all 14 v1 requirements.
