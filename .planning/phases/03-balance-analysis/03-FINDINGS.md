# Phase 3: Balance Analysis — Findings

**Method:** `_sweep.run_full_sweep()` across all 8 Phase 1 archetypes, 20-40 seeds each at `years=60`, fed into `_balance_analysis.run_full_analysis()`. Findings were stable across independent runs at 10, 20, and (partial) 40 seeds/policy — not seed-noise.

## ANLZ-01: Dominant Strategy — NONE CONFIRMED

Leaders split across different metrics (e.g. `burnout_avoider`/`prestige_chaser` trade the age/credits/net-worth lead depending on the run) — no single archetype is objectively best on every metric. This is the intended shape: different philosophies trade off differently. **No fix needed for this finding.**

## ANLZ-02: Dead Ends — Standing ceiling, confirmed across all 4 axes

No archetype's **mean** Standing (heat/prestige/affection/notoriety) across a 60-year career ever approaches 50 on any axis — peaks observed: heat ~46, prestige ~11-15, affection ~6-10, notoriety ~5-7. This directly corroborates Phase 1's Flagged Balance Findings (`decision-map.md`): the Approvals threshold (65), first-dollar-gross bonus (85), and both franchise spin-off thresholds (55) were found unreachable by individual archetypes there; this sweep confirms it's not one archetype's policy design — **no archetype, across any strategy, builds Standing anywhere near those gates.**

**Believability read:** an industry where nobody, playing any way, ever becomes a real star reads as capped and small-time rather than one where rare breakthroughs happen. This is the single most load-bearing finding of the whole pass.

## ANLZ-03: Low-Variance Cluster — net worth barely responds to strategy

7 of 8 archetypes (all except `prestige_chaser`) converge within a $3-7M band of mean net worth, despite representing genuinely different philosophies (franchise-chasing, risk-aversion, gambling, family-first, pure directing). Money isn't tracking the player's actual choices.

## Consolidated root-cause hypothesis (for Phase 4)

Both ANLZ-02 and ANLZ-03 plausibly trace to the same root: **Standing gain-per-project is too small relative to its own yearly decay, and/or acceptance volume (offers actually taken) is too low across all archetypes to compound.** Every archetype's own smoke-test data (Phase 1) showed the same pattern — modest per-project gains against `PRESTIGE_DECAY = 0.985`/`AFFECTION_DECAY` compounding down every non-working year. Phase 4 should treat the Standing formula (`actor/standing.py`) and its decay constants as the primary tuning target, not each individual threshold — moving `APPROVAL_STANDING_THRESHOLD` etc. down without also looking at *why* Standing tops out around 15-45 would just move the wall, not fix the ceiling.

## Full traced findings list for Phase 4

1. **Standing ceiling** (ANLZ-02, this phase) — no archetype's Standing approaches elite tiers on any axis. Candidate levers: `actor/standing.py` gain formulas (`delta_heat`/`delta_prestige`/`delta_affection`), `PRESTIGE_DECAY`/`AFFECTION_DECAY`/`HEAT_KEEP`.
2. **Approvals unreachable** (Phase 1 flagged finding) — `APPROVAL_STANDING_THRESHOLD = 65.0` (`leverage/approvals.py`), downstream of finding 1.
3. **First-dollar-gross bonus unreachable** (Phase 1 flagged finding) — `FIRST_DOLLAR_GROSS_STANDING_THRESHOLD = 85.0`, downstream of finding 1.
4. **Merchandising unreachable** (Phase 1 flagged finding) — compounds finding 1 with an animation-role rarity issue.
5. **Both franchise spin-off thresholds unreachable** (Phase 1 flagged finding) — `SPINOFF_INDISPENSABILITY_THRESHOLD = 55.0` (`simulation/_franchises.py`), a separate Indispensability curve, same pattern.
6. **Net worth low-variance** (ANLZ-03, this phase) — money doesn't differentiate strategy; candidate levers: `life/money.py` income formulas, project fee/bonus scaling relative to `lifestyle_floor`.

Findings 2-5 are downstream of finding 1 and should very likely be fixed together, not as five separate tuning passes.
