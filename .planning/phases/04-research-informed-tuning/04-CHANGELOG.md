# Phase 4: Research-Informed Tuning — Changelog

## Change 1: Standing gain coefficients (`actor/standing.py`)

- `HEAT_BASE`: 7.9 → 8.6
- `PRESTIGE_CRITIC_COEF`: 0.11 → 0.15
- `PRESTIGE_SPOTLIGHT_COEF`: 0.26 → 0.35
- `AFFECTION_AUD_COEF`: 0.10 → 0.14

**Traced to:** Phase 3 findings 1-5 (Standing ceiling, downstream Approvals/first-dollar-gross/merchandising/spin-off unreachability) — `.planning/phases/03-balance-analysis/03-FINDINGS.md`. Grounded in `design/part-14-tuning-targets.md` §14.9's own validated target ("careers reaching Heat > 80 at any point: ~18%") — verified a maximally-engaged naive policy peaked at Heat 79.5/100 across 59 seeds (0% crossing 80) before the fix, and above 80 after.

**Verified effect:** re-running the full 8-archetype sweep (15 seeds/policy, years=60) after the fix: dead-end findings dropped from 4 to 3 (the Heat-ceiling finding resolved), low-variance net-worth cluster shrank from 7 to 6 archetypes.

**Not fully resolved:** Prestige/Affection/Notoriety still don't approach the 50-Standing floor (peaks ~4-12 after the fix, up from ~2-9 before). Root-cause analysis (see below) found the actual per-worked-year gain for these axes is far smaller than the coefficient math alone suggests, because none of Phase 1's 8 archetypes deliberately optimize scene-position choice for Prestige/Affection specifically — 6 of 8 reuse the shared `SCENE_POSITIONS` default (tuned only to avoid the historical v20 flat-WITH bug, not to maximize spotlight/critic score), so measured critic/spotlight outcomes sit close to the population mean regardless of archetype intent, netting each delta close to zero even after the coefficient bump.

**Deliberately not pursued further this pass:** closing this gap fully would require either (a) a much larger coefficient multiplier (~5x from original, estimated via the decay-equilibrium math in this changelog's working notes) — risky and disproportionate without more evidence it's the right lever, or (b) giving archetypes real Prestige/Affection-optimizing scene-position strategies (a Phase 1-style archetype-design change, not a constant tune) — out of scope for a single Phase 4 pass. **Flagged as a follow-up finding for a future milestone** rather than force-tuned on a hunch.

## Change 2: `test_director_mode.py` fixture fix (TEST-01)

`TestDirectorPrestigeUsesAudienceScoreNotDoubledCritic` failed after Change 1 — confirmed via `git stash` that it passed before and failed after. Root cause: the test's fixture (deliberately extreme critic=80/audience=20 reception) produced a prestige delta that, with the larger `PRESTIGE_SPOTLIGHT_COEF`, now drives the starting ~20 Prestige below Meter's 0.0 floor, so the observed delta reflected clamping, not the formula. Fixed by giving the fixture 60 points of headroom before the extreme-reception step — the test's actual assertion (no accidental critic/audience double-counting) is unchanged and still meaningful.

## TUNE-02 compliance check

- `dataclasses.replace(...)` pattern: unchanged — this pass only edited module-level constants, no state-shape changes.
- `Session` boundary: unchanged — no engine dataclass newly crosses into `cli.py`.
- One-way dependency direction: unchanged — `actor/standing.py` still imports only from `core`.
- Design-doc citation: `standing.py`'s inline comments cite `design/part-14-tuning-targets.md` §14.9 and this milestone's own findings docs directly at the changed constants.
