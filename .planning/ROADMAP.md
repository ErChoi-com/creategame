# Roadmap: Callback — Playtest & Balance Pass

## Overview

This milestone runs the Callback engine through a systematic playtest-and-tune pipeline rather than adding new gameplay. It starts by mapping the full decision space and building scripted policies that exercise it, then runs automated sweeps at volume to collect outcome data, analyzes that data for dominant strategies/dead ends/low-variance clustering, applies research-informed engine tuning to fix what's found (keeping tests and design docs in sync), and closes the loop by re-sweeping to confirm the fixes landed cleanly before writing up a findings report. Each phase is a horizontal layer of the same discover-tune-verify pipeline — earlier phases build the harness later phases depend on.

**Guiding philosophy — immersiveness first.** The measurable balance goals (no dominant strategy, no dead ends, meaningful variance, emotional highs/lows) are the mechanism, not the point. At every stage — analysis in Phase 3, the fixes themselves in Phase 4, the write-up in Phase 5 — the standing question is whether a change makes the simulated career feel like a believable Hollywood career, not just whether it flattens a stat curve. A numerically "balanced" outcome that reads as arbitrary or gamey is a failure of this pass even if the stats look clean.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Decision Space & Playtest Policy Coverage** - Catalog every reachable decision point and build scripted policies that collectively exercise all of them
- [x] **Phase 2: Automated Sweep Infrastructure** - Run the full policy set at volume across seeds, producing outcome stats and distinct dead-end flagging
- [ ] **Phase 3: Balance Analysis** - Analyze sweep data for dominant strategies, dead ends, and low-variance outcome clusters
- [ ] **Phase 4: Research-Informed Tuning** - Fix identified imbalances in the engine, informed by comparable-game research, with tests and design docs kept in sync
- [ ] **Phase 5: Verification Loop & Findings Report** - Re-sweep and re-analyze to confirm fixes landed cleanly, then document what changed and why

## Phase Details

### Phase 1: Decision Space & Playtest Policy Coverage

**Goal**: Every reachable gameplay decision point is documented as ground truth, and scripted playtest policies exist that collectively exercise all of them.
**Depends on**: Nothing (first phase)
**Requirements**: MAP-01, POLICY-01, POLICY-02
**Success Criteria** (what must be TRUE):

  1. A reference document catalogs every distinct decision point in the engine — background/ambition choices, offer/prep/scene decisions, leverage plays, franchise/adaptation decisions, director-mode choices, life/relationship choices — each entry citing the source module/function that implements it.
  2. At least 8 distinct scripted playtest policies exist representing different archetypes/goals (e.g. prestige-chaser, franchise-maximizer, indie-purist, risk-averse, gambler, director-track, family-first, burnout-avoider), built by extending the existing `_full_data_report.py` / `_quality_report.py` / `_smart_report.py` / `_sim_policy_shared.py` infrastructure rather than a parallel harness.
  3. Cross-referencing the policy set against the decision map shows every cataloged option is reachable by at least one policy — zero decision points go untested by the policy set.

**Plans**: 5/5 plans executed

- [x] 01-01-PLAN.md — decision-map.md catalog + coverage tool + prestige_chaser/franchise_maximizer archetypes (tracer)
- [x] 01-02-PLAN.md — indie_purist, risk_averse, gambler archetypes (acting-lane coverage)
- [x] 01-03-PLAN.md — director_track archetype (all director-only coverage gaps)
- [x] 01-04-PLAN.md — family_first, burnout_avoider archetypes (completes the 8-archetype minimum)
- [x] 01-05-PLAN.md — full coverage-check run, gap closure, zero-gap gate test

### Phase 2: Automated Sweep Infrastructure

**Goal**: The full policy set from Phase 1 can be run at volume across many seeds in one invocation, producing per-policy outcome statistics and distinctly flagging stuck/dead-end runs.
**Depends on**: Phase 1
**Requirements**: SWEEP-01, SWEEP-02
**Success Criteria** (what must be TRUE):

  1. A sweep script runs every policy from Phase 1 across many seeds each (e.g. 50+ per policy) in a single invocation and completes without crashing.
  2. Sweep output reports, per policy, aggregate outcome statistics: career length, income, prestige/heat/affection trajectories, obituary quality, and franchise outcomes.
  3. Sweep output separately counts/flags runs that ended in a stuck/dead-end state (stranded with no meaningful further options) apart from runs with a normal career ending.

**Plans**: TBD

### Phase 3: Balance Analysis

**Goal**: Sweep data is interpreted to surface which builds dominate, which choices dead-end, and which meaningfully-different choices converge on statistically similar outcomes — read for immersion-breaking patterns, not just raw stat outliers.
**Depends on**: Phase 2
**Requirements**: ANLZ-01, ANLZ-02, ANLZ-03
**Success Criteria** (what must be TRUE):

  1. An analysis pass ranks policies/builds on the outcome metrics that matter and explicitly names any policy that dominates all others on those metrics, or confirms none does.
  2. An analysis pass lists specific choices/states identified as dead ends, each backed by the sweep runs that got stuck there.
  3. An analysis pass identifies clusters of meaningfully different choices whose sweep outcomes are statistically indistinguishable (low variance), each backed by the supporting sweep data.
  4. Each finding is annotated with why it matters in career-simulation terms (e.g. "a franchise-maximizer never goes broke regardless of choices" reads as immersion-breaking, not just as a stat anomaly) — findings are framed as believability problems the tuning phase must fix, not only as numbers to flatten.
  5. All findings sets (dominant strategies, dead ends, low-variance clusters, each with its believability framing) are written down together as the input list Phase 4 works from.

**Plans**: TBD

### Phase 4: Research-Informed Tuning

**Goal**: Every imbalance identified in Phase 3 gets a corresponding engine fix, informed by patterns from comparable games and prioritizing immersiveness over raw stat-flattening, with tests and design docs kept in sync with the new intended behavior.
**Depends on**: Phase 3
**Requirements**: RSCH-01, TUNE-01, TUNE-02, TEST-01
**Success Criteria** (what must be TRUE):

  1. A research note documents how comparable career/Hollywood/RPG progression-sim games solve build-variety and immersiveness problems, with each applied pattern linked to the specific tuning decision it informed.
  2. Every dominant-strategy/dead-end/low-variance finding from Phase 3's list has a corresponding engine constant/formula change, with each change's docstring/comment citing the design-doc section it implements (and that section updated if the intended target itself changed).
  3. Each fix is chosen for what it does to the believability of a career arc, not only to flatten a metric — a fix that resolves a stat imbalance by making the simulation feel arbitrary or gamey is rejected in favor of one that reads as a plausible Hollywood career consequence; where the two goals conflict, the fix note says which way it was resolved and why.
  4. All tuning changes follow existing conventions on inspection: frozen dataclasses updated via `dataclasses.replace(...)`, no engine dataclass crossing the `Session` boundary into `cli.py`, and the one-way `core → actor → other packages → simulation` dependency direction preserved.
  5. `python -m unittest discover -s callback/engine/tests` passes, with every test whose assertions encoded a pre-tuning value updated to match the new intentional behavior.

**Plans**: TBD

### Phase 5: Verification Loop & Findings Report

**Goal**: The tuning changes are confirmed to have resolved the targeted imbalances without introducing new ones, and the full pass — including its immersiveness tradeoffs — is documented for future reference.
**Depends on**: Phase 4
**Requirements**: VRFY-01, RPRT-01
**Success Criteria** (what must be TRUE):

  1. Re-running the Phase 2 sweep and Phase 3 analysis after tuning shows each originally-flagged dominant strategy, dead end, and low-variance cluster resolved.
  2. The re-run analysis introduces no new dominant strategy, dead end, or low-variance cluster as a side effect of the tuning changes (any that appear are looped back through Phase 4 before this phase is considered done).
  3. A findings/changes report exists summarizing what was found broken or boring, what changed in response, why, which design-doc sections were touched, and — for each change — how it affects the sense of an immersive, believable Hollywood career, not just its statistical effect.
  4. The report's list of changes is traceable one-to-one against the Phase 3 findings list — nothing flagged is left undocumented, nothing documented was never actually flagged.

**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Decision Space & Playtest Policy Coverage | 5/5 | Complete | 2026-08-20 |
| 2. Automated Sweep Infrastructure | 1/1 | Complete | 2026-08-20 |
| 3. Balance Analysis | 0/TBD | Not started | - |
| 4. Research-Informed Tuning | 0/TBD | Not started | - |
| 5. Verification Loop & Findings Report | 0/TBD | Not started | - |
