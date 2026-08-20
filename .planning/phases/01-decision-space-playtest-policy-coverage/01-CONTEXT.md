# Phase 1: Decision Space & Playtest Policy Coverage - Context

**Gathered:** 2026-08-20
**Status:** Ready for planning

<domain>
## Phase Boundary

Every reachable gameplay decision point in the engine gets documented as ground truth in a single catalog, and scripted playtest policies are built/extended so that every cataloged option is exercised by at least one policy. This phase produces the reference map and the policy roster that Phase 2's automated sweeps will run at volume — it does not run sweeps or tune values itself.

</domain>

<decisions>
## Implementation Decisions

### Decision Map — Scope & Format
- The catalog lives at `callback/docs/design/decision-map.md`, following the project's existing design-doc convention — it becomes the index other tuning work (Phase 3 findings, Phase 4 fixes) cites back to.
- Granularity: one entry per discrete choice the engine actually branches on (each background option, each prep option, each scene-position axis, each leverage play, each life-event choice, each casting/development/edit choice in director mode) — fine enough to drive real policy coverage, not one entry per system.
- Each entry cites both the design-doc section it implements AND the source module/function that implements it (matches `CONVENTIONS.md`'s doc-citation standard).
- Only choices that affect simulated state/outcomes count as decision points — purely cosmetic/flavor text with no mechanical branch is excluded, since this catalog exists to drive playtest coverage, not to be an exhaustive UX inventory.

### Playtest Policy Set — Archetypes & Structure
- New archetype policies are organized one-function-per-archetype in a new `simulation/_archetype_policies.py`, following the existing pattern in `_full_data_report.py` / `_quality_report.py` / `_smart_report.py` — extends that infrastructure rather than building a parallel harness.
- Scene-position strategy differs per archetype where scene choice is the actual differentiator (e.g. gambler picks extreme contrast positions, indie-purist stays craft-safe); archetypes where scene choice isn't the point reuse `_sim_policy_shared.py`'s existing `SCENE_POSITIONS` default.
- Archetype list (minimum 8, per ROADMAP Phase 1 success criterion #2): prestige-chaser, franchise-maximizer, indie-purist, risk-averse, gambler, director-track, family-first, burnout-avoider.
- Director-mode gets its own standalone archetype (director-track) AND is folded as a variant into at least one acting archetype, mirroring `_smart_report.py`'s existing "both tracks" pattern (§7.11).

### Coverage Verification
- A reusable coverage-check function cross-references the decision-map catalog against a log of which decision points each policy actually visits during a sample run, producing a coverage report (built as something Phase 2's sweep infrastructure calls again, not a Phase-1-only throwaway).
- "Reachable" means a policy actually triggers the option/gate in a sampled run — not merely that some policy's code references the path.
- Phase 1 is not complete until the coverage report shows zero gaps: any decision point unreachable by the current archetype set gets a policy fix (new archetype behavior, adjusted thresholds targeted) within this phase, per POLICY-02's explicit "zero decision points go untested" bar. Gaps are not deferred to Phase 4.

### Claude's Discretion
No open items — all three grey areas were accepted as recommended during smart discuss.

</decisions>

<code_context>
## Existing Code Insights

### Reusable Assets
- `simulation/_sim_policy_shared.py` — shared `SCENE_POSITIONS` default (WITH/BENEATH/WITH), documented with a specific historical bug note (v20, flat-WITH policies silently zeroing Prestige) — new policies should import this rather than redefine scene defaults, per its own module docstring warning.
- `simulation/_full_data_report.py`, `_quality_report.py`, `_smart_report.py`, `_report_sim.py`, `_director_report.py` — existing one-off headless policy runners against `Session`/`full_career.py`. `_smart_report.py` already demonstrates a real "both tracks" (actor + director) triage policy — the pattern to mirror for the director-track archetype's dual-track variant.
- `simulation/verify.py` — existing statistical harness reproducing design-doc §14 targets (correlation helper `corr()`, `_sample_actor`, `_one_project`) — a model for how to structure a coverage/stats report, though it samples raw formulas rather than running full policies.
- `simulation/full_career.py` — the actual composed full-loop state (`FullState`) integrating actor career, Rolodex, Leverage, Life, Guild, genre cycle — this is what a real policy drives end-to-end, not `career.py` alone (which stays the minimal tested actor-only loop by design).

### Established Patterns
- Every module docstring cites its design-doc section (e.g. `"""design/part-04-the-actor.md §4.2..."""`) — the new decision-map doc and any new policy module should follow the same citation habit.
- `rng: random.Random` is threaded explicitly everywhere randomness is needed — new policy functions must accept and pass through an `rng` parameter, never touch global `random` state.
- Frozen dataclasses + `dataclasses.replace(...)` for all state updates — policy code reads state and calls existing engine functions; it does not mutate `FullState`/`ActorState` directly.

### Integration Points
- New archetype policies plug into `simulation/full_career.py`'s `FullState` loop the same way `_smart_report.py`'s triage functions do — calling existing `Session`-level or `full_career.py`-level functions, not reimplementing casting/reception/leverage logic.
- The decision-map catalog should enumerate options exposed through `actor/offers.py`, `actor/prep.py`, `actor/positions.py`/`shape.py`, `leverage/*.py`, `genre/franchise.py`/`adaptation.py`, `director/*.py`, `life/*.py`, and `rolodex/*.py` — matching the package boundaries `ARCHITECTURE.md` already documents.

</code_context>

<specifics>
## Specific Ideas

No additional specific ideas beyond the accepted grey-area decisions above — proceed per those decisions and the ROADMAP Phase 1 success criteria.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Note: unreachable decision points are explicitly NOT deferred per the Coverage Verification decision above — they get fixed within Phase 1.)

</deferred>
