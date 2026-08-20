# Requirements: Callback — Playtest & Balance Pass

**Defined:** 2026-08-20
**Core Value:** Every meaningfully different way to play should lead to a distinct, engaging career arc with real ups and downs — no path strictly best, none a dead end.

## v1 Requirements

Requirements for this milestone. Each maps to roadmap phases.

### Decision Map

- [ ] **MAP-01**: A reference document catalogs every distinct gameplay option/decision point reachable in the engine — background/ambition choices, offer/prep/scene decisions, leverage plays, franchise/adaptation decisions, director-mode choices, life/relationship choices — as the ground truth for what "the full decision space" is

### Playtest Policies

- [ ] **POLICY-01**: Scripted decision policies exist for a wide variety of player archetypes/goals (e.g. prestige-chaser, franchise-maximizer, indie-purist, risk-averse, gambler, director-track, family-first, burnout-avoider), extending the existing `_full_data_report.py`/`_quality_report.py`/`_smart_report.py`/`_sim_policy_shared.py` infrastructure
- [ ] **POLICY-02**: Policies collectively exercise every option cataloged in MAP-01 at least once across the policy set — no gameplay option goes untested

### Automated Sweeps

- [ ] **SWEEP-01**: Automated playthroughs run at volume (many seeds per policy) across the full policy set and produce outcome statistics (career length, income, prestige/heat/affection trajectories, obituary quality, franchise outcomes)
- [ ] **SWEEP-02**: Sweep output flags stuck/dead-end states (a run that gets stranded with no meaningful further options) distinctly from normal career endings

### Balance Analysis

- [ ] **ANLZ-01**: Sweep data is analyzed to identify dominant strategies — any policy/build objectively outperforming all others on the outcome metrics that matter
- [ ] **ANLZ-02**: Sweep data is analyzed to identify dead ends — choices or states that lead to boring, stuck, or unrecoverable outcomes
- [ ] **ANLZ-03**: Sweep data is analyzed to identify low-variance clusters — meaningfully different choices that converge on statistically similar outcomes

### Tuning

- [ ] **TUNE-01**: Each identified imbalance (from ANLZ-01/02/03) gets a corresponding fix to the responsible engine constant/formula, with the change traced to the design-doc section it implements (updating that section if the intended target itself changes)
- [ ] **TUNE-02**: Tuning changes follow existing engine conventions — frozen dataclasses updated via `dataclasses.replace`, no engine dataclass crossing the `Session` boundary into `cli.py`, one-way `core → actor → other packages → simulation` dependency direction preserved

### Test Suite

- [ ] **TEST-01**: Existing tests whose assertions encode pre-tuning values are updated to match each intentional tuning change, so the suite reflects current design intent rather than stale numbers

### Verification Loop

- [ ] **VRFY-01**: After each round of tuning changes, the sweep (SWEEP-01/02) and analysis (ANLZ-01/02/03) re-run to confirm the targeted imbalance is resolved and no new one was introduced

### Research

- [ ] **RSCH-01**: Comparable career/Hollywood/RPG progression-sim games are researched for how they solve build-variety and immersiveness problems; applicable patterns inform tuning decisions, with immersiveness weighted over raw stat-balance when the two trade off

### Reporting

- [ ] **RPRT-01**: A findings/changes report documents what was found broken or boring, what changed, why, and which design-doc sections were touched

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Content Expansion

- **EXPD-01**: New gameplay systems/content (new career paths, genres, event types) for any gap that playtesting reveals but that isn't a dead-end blocker

### Presentation Polish

- **PRES-01**: CLI text/flow improvements where playtesting reveals confusing or flat presentation

## Out of Scope

| Feature | Reason |
|---------|--------|
| New gameplay systems or content beyond genuine dead-end fixes | This pass tunes what exists; speculative new content is scope creep — deferred to v2 (EXPD-01) |
| CLI/UI text and presentation polish | Engine values/formulas only for this pass — deferred to v2 (PRES-01) |
| Work outside `callback/engine/` unless documenting a tuning decision | Keeps the pass scoped to the simulation engine itself |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| MAP-01 | Phase 1 | Pending |
| POLICY-01 | Phase 1 | Pending |
| POLICY-02 | Phase 1 | Pending |
| SWEEP-01 | Phase 2 | Pending |
| SWEEP-02 | Phase 2 | Pending |
| ANLZ-01 | Phase 3 | Pending |
| ANLZ-02 | Phase 3 | Pending |
| ANLZ-03 | Phase 3 | Pending |
| TUNE-01 | Phase 4 | Pending |
| TUNE-02 | Phase 4 | Pending |
| TEST-01 | Phase 4 | Pending |
| RSCH-01 | Phase 4 | Pending |
| VRFY-01 | Phase 5 | Pending |
| RPRT-01 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-08-20*
*Last updated: 2026-08-20 after roadmap creation*
