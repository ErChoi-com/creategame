# Phase 1: Decision Space & Playtest Policy Coverage - Research

**Researched:** 2026-08-20
**Domain:** Internal codebase inventory (Python stdlib game engine) — no external libraries, no new dependencies. All research this session is direct code-reading of `callback/engine/`, verified with `Read`/`Grep` against the live source tree.
**Confidence:** HIGH — every claim below is either `[VERIFIED: file:lines]` (I opened the file this session and quote the exact source) or explicitly marked `[ASSUMED]`/`[Open Question]` where the engine's own behavior is ambiguous or untested.

## Summary

This phase has two deliverables: a decision-map document (`callback/docs/design/decision-map.md`) cataloging every mechanically-branching player choice in the engine, and a set of ≥8 archetype policy functions (`simulation/_archetype_policies.py`) that collectively exercise every cataloged option, verified by a coverage-check tool.

The engine's entire player-facing decision surface is `simulation/session.py`'s `Session` class (2235 lines) — this is the single source of truth to walk for MAP-01, and I walked it in full this session. It exposes roughly **37 distinct decision categories** (character creation, offer/deal/prep/scene/release, leverage plays, franchise plays, 12 director-mode decisions, rolodex pulls, awards) which expand to well over 100 individual discrete options once each category's enum values are itemized (5 director casting choices, 9 director dev actions, 4×4 scene-dial positions, 8 adaptation source types, etc.).

Five headless "report" scripts already exist under `simulation/` (`_full_data_report.py`, `_quality_report.py`, `_smart_report.py`, `_report_sim.py`, `_director_report.py`) plus a shared scene-position constant (`_sim_policy_shared.py`). **`_full_data_report.py` is the current, most-complete pattern** — its own docstring and every other script's docstring say so explicitly (`_smart_report.py`, `_report_sim.py`, and `_director_report.py` all open with "Superseded by `_full_data_report.py`..."; `_quality_report.py`'s docstring says the same, noting it's kept only for its narrated per-year printout). `_full_data_report.py` implements 4 policy "tendencies" (gambler, prestige, workhorse, opportunist) driving both acting and directing tracks through `Session` every year for up to 60 years.

Despite five scripts and four tendencies, **cross-referencing every script against the full `Session` surface turns up roughly 20 decision points/options with zero current coverage** — including two entire subsystems (multi-picture deals, the franchise holdout) that are fully implemented and tested in `leverage/`/`simulation/_franchises.py` but never called by any policy script. The awards system appears to be exercised in only one script (`_quality_report.py`), and that call site is missing a required positional argument (`category`) — **as written it would raise `TypeError` the moment `awards_campaign_available()` first returns `True`**, meaning the actor awards decision point has effectively never been exercised in practice either. See "Coverage Gap Inventory" below for the full list — this is the concrete starting checklist for POLICY-02's "zero gaps" bar.

**Primary recommendation:** Build the decision map directly off `session.py`'s public method surface (one row per method/option), write `_archetype_policies.py` as 8+ functions following `_full_data_report.py`'s parametrized-tendency shape (one function per archetype, each calling `Session` the same way the existing tendencies do), explicitly route each of the ~20 currently-uncovered decision points into at least one archetype's policy logic, and build the coverage-check as a simple tally dict keyed by decision-point name that each policy call increments — no new instrumentation layer needed; `Session`'s own return dicts already carry every signal required to detect which branch was taken.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Decision-point catalog (MAP-01) | Docs (`callback/docs/design/`) | — | A design-doc-style reference, not runtime code; mirrors existing `part-NN-*.md` convention. |
| Archetype policies (POLICY-01/02) | `simulation/` (orchestration layer) | `actor/`, `director/`, `leverage/`, `rolodex/`, `life/` (read-only, via `Session`) | Policies are pure callers of `Session` — no new engine logic, no new package. Same tier as the existing `_*_report.py` scripts. |
| Coverage-check tool | `simulation/` (orchestration layer) | `tests/` (if wired into a regression test) | Consumes `Session`/policy-run output only; never reaches into `actor`/`director`/etc. internals — stays inside the one-way dependency rule. |
| Decision-point source of truth | `simulation/session.py` (`Session`) | `actor/`, `director/`, `leverage/`, `rolodex/`, `life/`, `genre/` (the option enums `Session` re-exports) | `Session` is the only class the CLI (and therefore any player) can reach; every decision point must have a `Session`-level entry point or it is unreachable and out of scope for this catalog. |

## User Constraints

<user_constraints>
### Locked Decisions (from CONTEXT.md)

- Decision-map catalog lives at `callback/docs/design/decision-map.md`, following the project's existing design-doc convention — it becomes the index other tuning work (Phase 3 findings, Phase 4 fixes) cites back to.
- Granularity: one entry per discrete choice the engine actually branches on (each background option, each prep option, each scene-position axis, each leverage play, each life-event choice, each casting/development/edit choice in director mode) — fine enough to drive real policy coverage, not one entry per system.
- Each entry cites both the design-doc section it implements AND the source module/function that implements it.
- Only choices that affect simulated state/outcomes count as decision points — purely cosmetic/flavor text with no mechanical branch is excluded.
- New archetype policies are organized one-function-per-archetype in a new `simulation/_archetype_policies.py`, following the existing pattern in `_full_data_report.py` / `_quality_report.py` / `_smart_report.py` — extends that infrastructure rather than building a parallel harness.
- Scene-position strategy differs per archetype where scene choice is the actual differentiator (e.g. gambler picks extreme contrast positions, indie-purist stays craft-safe); archetypes where scene choice isn't the point reuse `_sim_policy_shared.py`'s existing `SCENE_POSITIONS` default.
- Archetype list (minimum 8): prestige-chaser, franchise-maximizer, indie-purist, risk-averse, gambler, director-track, family-first, burnout-avoider.
- Director-mode gets its own standalone archetype (director-track) AND is folded as a variant into at least one acting archetype, mirroring `_smart_report.py`'s existing "both tracks" pattern.
- A reusable coverage-check function cross-references the decision-map catalog against a log of which decision points each policy actually visits during a sample run, producing a coverage report (built as something Phase 2's sweep infrastructure calls again, not a Phase-1-only throwaway).
- "Reachable" means a policy actually triggers the option/gate in a sampled run — not merely that some policy's code references the path.
- Phase 1 is not complete until the coverage report shows zero gaps: any decision point unreachable by the current archetype set gets a policy fix within this phase. Gaps are not deferred to Phase 4.

### Claude's Discretion
No open items — all three grey areas were accepted as recommended during smart discuss.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. Unreachable decision points are explicitly NOT deferred; they get fixed within Phase 1.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MAP-01 | Reference document catalogs every distinct gameplay option/decision point reachable in the engine | Full `Session` method walk below ("Full Decision-Point Inventory") gives every method, its options, and its source module/function/line range — directly usable as the catalog's row data. |
| POLICY-01 | Scripted decision policies exist for ≥8 archetypes, extending existing report-script infrastructure | `_full_data_report.py`'s 4-tendency pattern (parametrized `run(seed, tendency, ...)`) is the concrete template to extend to 8+ archetypes; exact call shapes for every `Session` method are documented below. |
| POLICY-02 | Policies collectively exercise every cataloged option at least once | "Coverage Gap Inventory" below lists every decision point/option NOT currently exercised by any existing script — the exact list the new archetypes must specifically target. |
</phase_requirements>

## Standard Stack

Not applicable in the conventional sense — this phase adds zero third-party dependencies. Everything is implemented against `callback/engine/simulation/session.py` using Python's own `unittest`/stdlib, matching every existing report script.

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib only | 3.13.1 / 3.14.3 (both confirmed present) `[VERIFIED: python --version / python3 --version this session]` | Everything — `random.Random`, `dataclasses`, `collections.Counter` for tallying | Matches project constraint: zero third-party packages anywhere in `callback/engine/` `[VERIFIED: callback/engine/README.md:66 — "python3 -m unittest discover callback/engine/tests # 117 tests"]` |

### Package Legitimacy Audit

**Not applicable.** No external packages are installed or proposed by this phase — the decision-map doc and `_archetype_policies.py` are pure additions to the existing internal `callback/engine/simulation/` package, importing only from `callback.engine.*` (matching every existing report script's import block). Skip the legitimacy gate entirely.

## Architecture Patterns

### System Architecture Diagram

```text
┌────────────────────────────────────────────────────────────────────┐
│  callback/docs/design/decision-map.md   (NEW — MAP-01)              │
│  static reference: decision point -> design §, module/function,     │
│  option enum, gating condition (if any)                             │
└───────────────────────────────┬─────────────────────────────────────┘
                                 │ read by (documentation, not import)
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│  simulation/_archetype_policies.py   (NEW — POLICY-01)              │
│  8+ functions: prestige_chaser(seed,...), franchise_maximizer(...),  │
│  indie_purist(...), risk_averse(...), gambler(...), director_track   │
│  (...), family_first(...), burnout_avoider(...)                     │
│  — each: Session(seed) -> loop over years -> Session method calls   │
│  — each records which decision-point/option it exercised this call  │
└───────────────────────────────┬─────────────────────────────────────┘
                                 │ drives, method calls in / plain data out
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│  simulation/session.py  (Session)  — EXISTING, read-only this phase │
│  offer_board/accept/choose_deal/choose_prep/play_scene/              │
│  choose_release/request_holdout/sign_multi_picture_deal/             │
│  start_directing_project/advance_directing/interact/...             │
└───────────────────────────────┬─────────────────────────────────────┘
                                 │ composes
                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│  full_career.py (FullState) -> actor/ director/ leverage/ rolodex/   │
│  life/ genre/ studio/ awards/ world/  — EXISTING, untouched          │
└────────────────────────────────────────────────────────────────────┘

              ┌──────────────────────────────────────────────────┐
              │  simulation/_decision_coverage.py (NEW, or a      │
              │  function inside _archetype_policies.py)          │
              │  input: decision-map entries + a policy run's own │
              │  tallied visit-log (Counter keyed by decision id) │
              │  output: coverage report — visited / not-visited  │
              └──────────────────────────────────────────────────┘
```

### Recommended Project Structure
```
callback/
├── docs/design/
│   └── decision-map.md              # NEW — MAP-01 catalog
└── engine/simulation/
    ├── _sim_policy_shared.py        # EXISTING — SCENE_POSITIONS; extend with more
    │                                 #   position sets if archetypes need contrast/craft-safe variants
    ├── _archetype_policies.py       # NEW — POLICY-01/02, one function per archetype
    ├── _decision_coverage.py        # NEW (or a section of the above) — coverage-check tool
    └── _full_data_report.py         # EXISTING — the pattern being extended, read for reference
```

### Pattern 1: The parametrized-tendency policy function
**What:** A single `run(seed, ..., years=60) -> dict` function per archetype that drives `Session` end-to-end for a whole career, returning a summary dict (and, for this phase, also a visit-tally).
**When to use:** Every one of the 8 archetypes — this is the established shape, not a new one.
**Example (existing pattern to mirror, not new code):**
```python
# Source: callback/engine/simulation/_full_data_report.py:41-107 (verified read this session)
def run(seed: int, tendency: str, years: int = 60, max_stats: bool = False) -> dict:
    session = Session(seed=seed)
    session.start("conservatory", "work")   # <- background/ambition currently hard-coded here;
    session.become_director()               #    an archetype should vary background (see Pitfall 1)
    for year in range(years):
        board = session.offer_board()
        ...
        best = max(available, key=lambda o: (...))   # per-tendency scoring function
        if best is not None:
            session.accept(best["index"])
            session.choose_deal(want_approvals=..., want_box_office_bonus=True, bonus_type=bonus_type,
                                 want_merchandising=session.merchandising_available())
            session.choose_prep(...)
            for scene_choice in SCENE_POSITIONS:
                session.play_scene(scene_choice)
            result = session.choose_release(strategy)
        ...
        session.end_year()
        if session.is_over():
            break
    return {...}
```

### Pattern 2: Tallying decision-point coverage without a logging layer
**What:** The engine has no logging framework by design `[VERIFIED: callback/engine/README.md ARCHITECTURE.md cross-cutting-concerns — "Logging: None — the engine communicates entirely through return values"]`. Coverage tracking must therefore live entirely in the **caller** (the policy function / a wrapper around `Session`), using `Session`'s own return values and a `collections.Counter`, exactly like every existing report script already does for its own stats (`Counter()` used in `_smart_report.py`, `_director_report.py`, `_report_sim.py`).
**When to use:** The coverage-check function (POLICY-02's verification tool).
**Example approach:**
```python
# Not existing code — the recommended shape, following the Counter convention
# already used in _smart_report.py:19,82 and _director_report.py:17,31-33.
from collections import Counter

def run_with_coverage(policy_run_fn, seed: int) -> tuple[dict, Counter]:
    visited = Counter()
    # Simplest reliable approach: instrument the ARGUMENTS passed to Session, not Session's
    # internals — e.g. wrap session.choose_prep(key) to record key, wrap session.choose_release
    # (strategy) to record the *actual* resolved strategy (result["release_label"]) not just the
    # request, since the studio can overrule it (session.py:1184-1185, "overruled = actual_strategy
    # != strategy"). Reachability per the CONTEXT.md decision means the option was ACTUALLY TAKEN
    # in a sampled run, so tally off return-value fields (e.g. result["rating_stance"],
    # result["release_label"], result["box_office_bonus_type"]) wherever a request can be overruled.
    ...
    summary = policy_run_fn(seed, visited=visited)
    return summary, visited
```
A thin subclass or wrapper object around `Session` (recording every method call's arguments and — where relevant — the resolved outcome field from the return dict) is the lowest-risk way to get this without touching `Session` itself. This keeps the coverage tool entirely outside the `core → actor → other → simulation` dependency chain (it only ever calls `Session` public methods) and never needs a new instrumentation layer inside the engine.

### Anti-Patterns to Avoid
- **Adding a logging/telemetry layer inside `Session` or any engine module:** CLAUDE.md is explicit — "no new logging/exception frameworks." Coverage tracking belongs entirely in the new `simulation/_archetype_policies.py` / `_decision_coverage.py` caller code, wrapping `Session`, never inside it.
- **Treating "the code path exists" as coverage:** CONTEXT.md's own Coverage Verification decision states reachability means the option was actually triggered in a sampled run. A dev-action cycle list that *contains* `"self_finance"` is not evidence of coverage unless a run's tally actually shows it fired — several existing scripts' cycle lists include actions that never actually get reached because of loop/tick timing (see Pitfall 2 below).
- **Re-deriving casting/Utility/Standing math inside a policy function:** every existing script reads `Session`'s own return dicts (`buzz_band`, `momentum_band`, `demand_band`, etc.) to make decisions — never reaches past `Session` into `actor.offers`/`director.development` internals for its own scoring. New archetypes must do the same (this is also required by the `Session`-boundary constraint in CLAUDE.md).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Scene-position defaults for archetypes where scene choice isn't the differentiator | A fresh flat-`"with"` scene dict | `simulation/_sim_policy_shared.py`'s `SCENE_POSITIONS` | Its own docstring documents a real regression (v20 flat-WITH policy silently zeroing Prestige) — re-deriving this is a documented, named bug trap `[VERIFIED: callback/engine/simulation/_sim_policy_shared.py:8-21, quoted in full below]`. |
| Offer/casting/reception scoring for a new archetype's decision logic | A parallel re-implementation of `actor.offers.utility()`/`offer_probability()` | Read `Session.offer_board()`'s own returned dict fields (`buzz_band`, `demand_band`, `in_your_lane`, `quarters_required`, etc.) and score off those, exactly as every existing tendency does | `Session` already surfaces every signal a player-facing policy needs; reaching past it duplicates engine math and risks drifting from the real formulas as Phase 4 tunes them. |
| Coverage tallying / "did this decision fire" detection | A new engine-side event/log system | A `Counter` in the calling policy code, keyed by decision-point id, incremented off arguments passed to `Session` methods and (where a request can be overruled) off the *resolved* fields in the returned dict | Matches the existing `Counter`-based stat-tallying convention already used in `_smart_report.py`, `_director_report.py`, `_report_sim.py`; needs no new engine surface. |

**Key insight:** Every "don't hand-roll" here reduces to the same rule already encoded in this project's CLAUDE.md: `Session` is the only legal seam, and its return values already carry everything a policy or a coverage tool needs. The temptation in this phase specifically is to reach into `director.development`/`actor.offers`/`leverage.indispensability` "just to read one gating constant" — resist it; `Session` methods like `holdout_available()`, `multi_picture_deal_available()`, `merchandising_available()` already surface every gate as a boolean/dict a caller can act on.

## Full Decision-Point Inventory

Enumerated by walking `simulation/session.py` in full this session (2235 lines, read start to finish) `[VERIFIED: callback/engine/simulation/session.py, full file read this session]`. Grouped by package boundary per `ARCHITECTURE.md`'s own layer breakdown. "Options" lists the exact enum values available; "Currently exercised by" cross-references the five existing report scripts (`FDR`=`_full_data_report.py`, `QR`=`_quality_report.py`, `SR`=`_smart_report.py`, `RS`=`_report_sim.py`, `DR`=`_director_report.py`).

### Character creation
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Background | `conservatory`, `discovered`, `regional_stage`, `family_money` — 4 options, each sets different starting `Attributes`/money/start_age `[VERIFIED: callback/engine/simulation/_backgrounds.py:13-20]` | `Session.background_options()`/`start()` — `session.py:296-318` | Only `"conservatory"` — every script (FDR/QR/SR/RS/DR) calls `session.start("conservatory", "work")` verbatim. **`discovered`/`regional_stage`/`family_money` = 0% coverage.** |
| Ambition | `work`, `prize`, `fortune`, `run`, `franchise`, `voice` — 6 labels `[VERIFIED: session.py:302-306]` | `Session.ambition_options()`/`start()` | **NOT a decision point per CONTEXT.md's own exclusion rule** — `self.ambition` is written once at `session.py:317` and read nowhere else in `session.py` besides the one greeting string at `session.py:318` (`grep` of `self.ambition` in `session.py` returns only those two lines). It has **zero mechanical effect** on any formula in the engine as of this session. Exclude from the catalog's countable rows; flag as an `Open Question` (see below) since the phase description names it as if it branches. |

### Offer board / casting (actor/)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Accept vs. decline an offer | accept(index) / decline_board() | `actor/offers.py` (`resolve_casting_path`, `offer_probability`) via `session.py:334-604` | All 5 scripts — well covered. |
| `generate_more_listings()` (scan deeper than the initial board) | n/a (batch call) | `session.py:355-359` | Only FDR's `"opportunist"` tendency (`_full_data_report.py:68-72`, `OPORTUNIST_SCAN_BATCHES=25`). |
| Multi-picture deal guaranteed slot / spinoff guaranteed slot / renewed-series guaranteed slot | n/a — automatic once triggered | `session.py:425-488` (`_guaranteed_listing`) | Never reached by any script, because none of them ever call `sign_multi_picture_deal`/`launch_spinoff`, and series/renewal only fires if a `series_renewable` role is accepted (possible by chance, but never deliberately pursued). |

### The Deal (leverage/approvals.py, leverage/merchandising.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Approvals request | `want_approvals: bool` | `session.py:913-945` | FDR (prestige/opportunist), QR — covered. FDR gambler/workhorse deliberately pass `False`. |
| Box-office bonus type | `net_points`, `first_dollar_gross` `[VERIFIED: session.py:897-902]` | `session.py:888-902` | Both — FDR always tries `first_dollar_gross` first, falling back to `net_points` (`_full_data_report.py:113`). |
| Merchandising | `want_merchandising: bool` | `session.py:904-912` | FDR (`want_merch = session.merchandising_available()`) — covered whenever an animated franchise role is accepted at sufficient Standing; gated (see Gated Decisions below). |

### Script notes (core/script_notes.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Actor script note | `clarity`, `ambiguity`, `your_part`, `whole_film` `[VERIFIED: session.py:952-959]` | `session.py:961-962` | Only `"whole_film"` — FDR (prestige/opportunist) and QR both hard-code `"whole_film"`. **`clarity`/`ambiguity`/`your_part` = 0% coverage.** |

### Rating stance (actor/rating.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Rating stance | `RATING_CUT` ("cut for the friendlier rating"), `RATING_RELEASE_AS_SHOT` `[VERIFIED: session.py:975-980]` | `session.py:982-983` | Only `RATING_RELEASE_AS_SHOT` — every script that calls `choose_rating_stance` passes `"release_as_shot"` (FDR:144, QR:179, RS:68). **`RATING_CUT` = 0% coverage as a deliberate player choice** (a cut can still happen via studio override — see `rating_cut_forced` — but the player never *asks* for it). |

### Costar orientation (actor/positions.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Orientation toward scene partner | `neutral`, `generous`, `upstage` `[VERIFIED: session.py:1038-1043]` | `session.py:1045-1052` | `neutral` (RS:61) and `generous` (QR:160) only. **`upstage` = 0% coverage.** |

### Prep (actor/prep.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Prep choice | `table_work`, `research`, `dialect`, `physical_transformation`, `live_it` (5 player-facing options; `wing_it` exists in the engine as `PREP_OPTIONS[5]` but is explicitly excluded from `Session.prep_options()`'s menu) `[VERIFIED: callback/engine/actor/prep.py:19-21 — "WING_IT = \"wing_it\"" / "PREP_OPTIONS = (TABLE_WORK, RESEARCH, DIALECT, PHYSICAL_TRANSFORMATION, LIVE_IT, WING_IT)"; session.py:1056-1058 — "return [(o, o.replace(\"_\", \" \")) for o in PREP_OPTIONS if o != WING_IT]"]` | `session.py:1060-1061` | `table_work` (FDR workhorse/RS), `physical_transformation` (FDR prestige, QR), `live_it` (FDR gambler). **`research`/`dialect` = 0% coverage.** |

### The shoot — scene positions (actor/positions.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Per-dial scene position (4 dials × 3 scenes for a film, 6 for a series) | Dials: `energy`, `volume`, `warmth`, `speed`. Positions per dial: `with`, `beneath`, `beyond`, `against` `[VERIFIED: callback/engine/actor/positions.py:9,17 — "POSITIONS = (WITH, BENEATH, BEYOND, AGAINST)" / "DIALS = (\"energy\", \"volume\", \"warmth\", \"speed\")"]` | `session.py:1074-1088` | Every script uses `_sim_policy_shared.SCENE_POSITIONS`, which is `[{with×4}, {beneath×4}, {with×4}]` `[VERIFIED: callback/engine/simulation/_sim_policy_shared.py:22-26]` — **`beyond` and `against` are never used on any dial by any existing script.** |

### Release (actor/release.py, actor/studios.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Release strategy request | `wide`, `limited`, `festival`, `streaming`, `shelved` `[VERIFIED: callback/engine/actor/release.py:20-21 — "WIDE, LIMITED, FESTIVAL, STREAMING, SHELVED = \"wide\", \"limited\", \"festival\", \"streaming\", \"shelved\"" / "RELEASE_STRATEGIES = (WIDE, LIMITED, FESTIVAL, STREAMING, SHELVED)"]` | `session.py:1092-1268` | Only `wide`/`limited` are ever explicitly requested (FDR budget-threshold branches, QR's `TENTPOLE_BUDGET_THRESHOLD` branch, RS always `"wide"`). **`festival`/`streaming`/`shelved` are never explicitly requested by the player in any script.** They can still occur as the *actual* outcome when the studio overrules a request toward its own `preferred_release` (`indie`→festival, `streamer`→streaming `[VERIFIED: callback/engine/actor/studios.py:68,100]`) — but **no studio's `preferred_release` is `"shelved"`** `[VERIFIED: callback/engine/actor/studios.py:61-102, full STUDIOS dict — none of the 5 entries sets preferred_release="shelved"]`, so `shelved` can currently ONLY ever be reached by a deliberate player request that also wins the influence roll. **This makes `shelved` a decision point with zero current coverage by construction, not just by omission.** |
| `streaming_bid_selector` / `festival_bid_selector` (custom bid picking) | Any `Callable[[list[Bid]], Bid]` — default is "pick the best payout" | `session.py:1146-1219` | Never customized by any script — always the default max-payout selector. |

### Marketing push (actor/studios.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Request marketing push | boolean call | `session.py:585-589` | FDR, QR — covered. |

### Multi-picture deals (leverage/multi_picture_deal.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Sign a multi-picture deal | `film_count` (2–5, `MULTI_PICTURE_MIN_FILMS`/`MAX_FILMS`) `[VERIFIED: callback/engine/leverage/multi_picture_deal.py:13-15 — "MULTI_PICTURE_MIN_STANDING = 40.0" / "MULTI_PICTURE_MIN_FILMS = 2" / "MULTI_PICTURE_MAX_FILMS = 5"]` | `session.py:826-859` (`multi_picture_deal_available`/`_terms`/`sign_multi_picture_deal`) | **Never called by any existing script. 0% coverage of the entire subsystem.** |
| Break a multi-picture deal early | boolean call | `session.py:871-880` | **Never called. 0% coverage.** |

### Franchise holdout (leverage/indispensability.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Request a holdout on a sequel | boolean call (outcome: paid / recast / bluff-called) | `session.py:740-795` (`holdout_available`/`request_holdout`) | **Never called by any existing script. 0% coverage.** |

### Spin-offs — actor track (simulation/_franchises.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Launch a spin-off | `franchise_id` (any franchise past `SPINOFF_INDISPENSABILITY_THRESHOLD`) | `session.py:799-822` | **Never called by any existing script. 0% coverage.** |

### Awards (awards/awards.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Actor awards campaign category | `LEAD`, `SUPPORTING`, `ENSEMBLE`, `BREAKTHROUGH` (from `eligible_performance_categories`) | `session.py:1359-1447` (`run_awards_campaign` — `category` is a **required positional argument**, no default) | **Effectively 0% coverage.** Only `_quality_report.py:213` attempts this, calling `session.run_awards_campaign(spend_millions=2.0)` — **`category` is not supplied and has no default value in the signature** `[VERIFIED: session.py:1373 — "def run_awards_campaign(self, category: str, spend_millions: float = 1.0, attempt_category_fraud: bool = False) -> dict:"]`. This call would raise `TypeError: run_awards_campaign() missing 1 required positional argument: 'category'` the first time `awards_campaign_available()` returns `True` in a `_quality_report.py` run. See Pitfall 3. |
| `attempt_category_fraud` | boolean | `session.py:1373,1401-1407` | Never set `True` anywhere — 0% coverage, compounded by the bug above. |
| Director awards campaign | `DIRECTOR` category only (single-category by design) | `session.py:1452-1489` | **Never called by any existing script. 0% coverage.** |

### Leverage — agent/scarcity (leverage/catalogue.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Advance agent tier | n/a — automatic-if-eligible | `session.py:1571-1582`. Tiers: `unrepresented → regional → boutique → major → powerhouse` `[VERIFIED: callback/engine/leverage/catalogue.py:57 — "AGENT_TIERS = (\"unrepresented\", \"regional\", \"boutique\", \"major\", \"powerhouse\")"]` | FDR, SR, QR — called opportunistically whenever quarters are free; naturally reaches all 5 tiers over a long enough run. Covered probabilistically, not by explicit per-tier targeting. |
| Disappear (bank Scarcity) | boolean call | `session.py:1584-1594` | **Never called by any existing script. 0% coverage.** |

### Rolodex pulls (rolodex/interactions.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Interact with a tracked NPC | `check_in`, `show_up`, `read_agenda`, `vouch` `[VERIFIED: callback/engine/rolodex/interactions.py:22,27,32,40 — function names "check_in", "show_up_for_them", "read_agenda_and_act", "vouch_for_them"]` | `session.py:1503-1538` | Only `"check_in"` — every script's `_spend_actor_quarters` helper hard-codes `session.interact(target["id"], "check_in")`. **`show_up`/`read_agenda`/`vouch` = 0% coverage.** |

### Life (life/money.py)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Cut lifestyle floor | `new_floor_millions: float` | `session.py:2109-2126` | FDR — all non-gambler tendencies call it once net worth goes negative (`_full_data_report.py:242-243`). Covered. |
| Health/addiction/family state | — | `life/health.py`, `life/addiction.py`, `life/family.py` | **No player-facing decision exists anywhere in `Session` for these** — confirmed by grepping `Session` for `def choose_/request_/try_` (full list captured this session) and finding zero methods referencing health/addiction/family. These systems are automatic background state, not decision points, and are correctly out of MAP-01's scope per CONTEXT.md's "only choices that affect simulated state... purely cosmetic/flavor... excluded" rule (they're the inverse case: real mechanical effect, zero player choice). |

### Director mode (director/)
| Decision point | Options | Source | Currently exercised by |
|---|---|---|---|
| Become director | one-time unlock | `session.py:1611-1615` | All 5 scripts. |
| `start_directing_project` — genre | any of 10 `GENRES` | `session.py:1684-1730` | All. |
| `start_directing_project` — budget tier | `micro`, `low`, `mid`, `upper`, `tentpole` `[VERIFIED: callback/engine/studio/slate.py:14 — "TIER_BUDGETS = {\"micro\": 4.0, \"low\": 12.0, \"mid\": 30.0, \"upper\": 60.0, \"tentpole\": 170.0}"]` | Only `micro`/`low` (FDR prestige/workhorse, QR, SR, DR — all gate on Standing band) and `upper` (FDR gambler). **`mid`/`tentpole` = 0% coverage.** |
| `start_directing_project` — `self_financed=True` | boolean | `session.py:1684-1727` | **Never passed `True` by any script (always default `False`).** |
| `start_directing_project` — `franchise_id`/`new_franchise` | pitch a sequel to an existing franchise / register a brand-new franchise on first resolve | `session.py:1704-1709` | **Never passed by any script — every directed project is an ungated original.** 0% coverage of directing-side franchise sequels. |
| `start_directing_project` — `cast_decision` | `"recast"`, `"write_out"`, `None` (only meaningful with `franchise_id`) | `session.py:1711-1715` | **0% coverage** (depends on the never-used `franchise_id` param above). |
| Scrap a directing project | n/a | `session.py:1732-1734` | Called opportunistically by FDR/QR/SR/DR when a project's momentum band is `"dead"` — covered. |
| Attach a star — target | `None` (cold approach) or any tracked NPC id | `session.py:1738-1749` | Covered — all scripts cycle through `attach_star_target_options()`. |
| Attach a star — type | `bankable`, `genre_fit`, `studio_favorite` `[VERIFIED: session.py:1751-1757]` | `session.py:1759-1761` | All 3 covered across scripts (FDR cycles all 3; QR uses `genre_fit`; SR cycles all 3). |
| Adaptation source type | `public_domain`, `foreign_remake`, `novel`, `stage_play`, `true_story`, `comic`, `video_game`, `toy_line` `[VERIFIED: callback/engine/director/development.py:318-320 — "ADAPTATION_SOURCE_TYPES = (\"public_domain\", \"foreign_remake\", \"novel\", \"stage_play\", \"true_story\", \"comic\", \"video_game\", \"toy_line\")"]` | `session.py:1763-1783` | **Never called by any script** — `choose_adaptation_source_type()` is never invoked, so the `"option_adaptation"` dev action (which IS in every script's `dev_action_cycle`) always runs against the default `"novel"` source. **7 of 8 source types = 0% coverage.** |
| Adaptation licensing fraction | `float 0.0–1.0` | `session.py:1785-1794` | **Never called** — always resolves at the hard-coded default `0.5`. |
| Director casting choice | `bankable_wrong_fit`, `right_actor_no_heat`, `discovery`, `your_roster`, `difficult_genius` `[VERIFIED: callback/engine/director/casting.py:34-40 — "BANKABLE_WRONG_FIT = \"bankable_wrong_fit\"" ... "CASTING_CHOICES = (BANKABLE_WRONG_FIT, RIGHT_ACTOR_NO_HEAT, DISCOVERY, YOUR_ROSTER, DIFFICULT_GENIUS)"]` | `session.py:1809-1810` | All 5 covered — FDR/SR/DR all cycle the full `casting_cycle`; QR/RS use only `your_roster`. |
| Director's own Deal (backend push) | `push_director_deal_for_backend(project_index, bonus_type)` | `session.py:1818-1840` | **Never called by any script. 0% coverage.** |
| Director shoot style | `heavy_coverage`, `long_takes`, `many_takes`, `improvisation`, `lean_and_fast` `[VERIFIED: callback/engine/director/shoot_style.py:18 — "SHOOT_STYLES = (HEAVY_COVERAGE, LONG_TAKES, MANY_TAKES, IMPROVISATION, LEAN_AND_FAST)"]` | `session.py:1853-1854` | All 5 covered across FDR/SR/DR's `style_cycle`; QR uses only `heavy_coverage`. |
| Director script note | `clarity`, `ambiguity`, `whole_film` `[VERIFIED: session.py:1865-1872]` (narrower set than the actor's 4-option `script_note_options()`) | `session.py:1874-1875` | Only `whole_film` (FDR prestige, QR). **`clarity`/`ambiguity` = 0% coverage.** |
| Director release strategy request | Same 5 `RELEASE_STRATEGIES` as actor track | `session.py:1877-1882` | Only `wide`/`limited` (FDR: `"wide" if tendency == "gambler" else "limited"`). **`festival`/`streaming`/`shelved` = 0% coverage.** |
| Director marketing push | boolean | `session.py:1884-1885` | FDR — covered. |
| Director dev action | `rewrite`, `attach_star`, `cut_budget`, `new_financier`, `take_to_market`, `self_finance`, `drawer`, `call_in_favour`, `option_adaptation` — 9 options `[VERIFIED: callback/engine/director/development.py:111-114 — "DEV_ACTIONS = (\"rewrite\", \"attach_star\", \"cut_budget\", \"new_financier\", \"take_to_market\", \"self_finance\", \"drawer\", \"call_in_favour\", \"option_adaptation\")"]` | `session.py:1888-1901,1906-2007` | Every script's `dev_action_cycle` is `["attach_star","attach_star","rewrite","cut_budget","call_in_favour","option_adaptation","new_financier","take_to_market"]` — **`"self_finance"` and `"drawer"` never appear in any cycle list. 0% coverage of 2 of 9 dev actions.** |
| Directing franchise pitch (sequel to an active franchise) | `directing_franchise_options()` → pass `franchise_id` to `start_directing_project` | `session.py:631-648` | **0% coverage** (see `start_directing_project — franchise_id` above). |
| Directing reboot pitch (revive a retired franchise) | `directing_reboot_options()`/`pitch_reboot(franchise_id)` | `session.py:653-693` | **Never called. 0% coverage.** Requires a franchise to have gone fully dormant/retired first (`REBOOT_MIN_DORMANT_YEARS = 5` `[VERIFIED: callback/engine/simulation/_franchises.py:194]`) — a genuinely long-horizon setup, see Gated Decisions below. |
| Directing spin-off pitch | `directing_spinoff_options()`/`launch_directing_spinoff(franchise_id)` | `session.py:698-720` | **Never called. 0% coverage.** |
| Hire offer accept/decline | boolean | `session.py:2151-2181` | Covered by all 5 (varying accept-thresholds). |
| Platform expansion request | boolean | `session.py:2130-2147` | Covered by FDR/QR/SR whenever `platform_expansion_available()`. |

## Coverage Gap Inventory

Consolidated checklist — **the exact set of decision points the new 8+ archetype policies must specifically target** to satisfy POLICY-02's "zero decision points go untested" bar. (Cross-referenced against every table above; each line names the option and the file/line where it's defined.)

1. Background: `discovered`, `regional_stage`, `family_money` (`_backgrounds.py:13-20`)
2. Actor script note: `clarity`, `ambiguity`, `your_part` (`session.py:952-959`)
3. Rating stance: `RATING_CUT` requested deliberately (`session.py:975-980`)
4. Costar orientation: `upstage` (`session.py:1038-1043`)
5. Prep: `research`, `dialect` (`actor/prep.py:19-21`)
6. Scene positions: `beyond`, `against` on any dial (`actor/positions.py:9`)
7. Release request: `festival`, `streaming`, `shelved` explicitly requested (`actor/release.py:20-21`) — `shelved` in particular is unreachable any other way (no studio prefers it: `actor/studios.py:61-102`)
8. Custom `streaming_bid_selector` / `festival_bid_selector` (`session.py:1146-1219`)
9. Multi-picture deal: sign, terms preview, break (`session.py:826-880`) — entire subsystem
10. Franchise holdout: `holdout_available`/`request_holdout` (`session.py:740-795`)
11. Actor-track spin-off launch (`session.py:799-822`)
12. Actor awards campaign — fix the missing-`category` call and exercise `LEAD`/`SUPPORTING`/`ENSEMBLE`/`BREAKTHROUGH` (`session.py:1359-1447`)
13. `attempt_category_fraud=True` (`session.py:1401-1407`)
14. Director awards campaign (`session.py:1452-1489`)
15. `disappear()` — bank Scarcity (`session.py:1584-1594`)
16. Rolodex: `show_up`, `read_agenda`, `vouch` (`rolodex/interactions.py:22-50`)
17. Director budget tiers: `mid`, `tentpole` (`studio/slate.py:14`)
18. Director project: `self_financed=True` at `start_directing_project` (`session.py:1684-1727`)
19. Director project: `franchise_id`/`new_franchise`/`cast_decision` (sequels, `"recast"`/`"write_out"`) (`session.py:1704-1715`)
20. Adaptation source type: all except default `novel` — `public_domain`, `foreign_remake`, `stage_play`, `true_story`, `comic`, `video_game`, `toy_line` (`director/development.py:318-320`)
21. Adaptation licensing fraction — any non-default value (`session.py:1785-1794`)
22. `push_director_deal_for_backend` (director's own backend deal) (`session.py:1818-1840`)
23. Director script note: `clarity`, `ambiguity` (`session.py:1865-1872`)
24. Director release request: `festival`, `streaming`, `shelved` (`session.py:1877-1882`)
25. Director dev actions: `self_finance`, `drawer` (`director/development.py:111-114`)
26. Directing franchise sequel pitch (`session.py:631-648`)
27. Directing reboot pitch (`session.py:653-693`)
28. Directing spin-off pitch (`session.py:698-720`)

**Not a gap (excluded per CONTEXT.md rule):** Ambition (`session.py:302-318`) — confirmed zero mechanical effect this session; do not spend an archetype's policy logic trying to "cover" it. Document its exclusion explicitly in the decision-map so a future contributor doesn't assume it was missed.

## Gated Decision Points (require deliberate engineering, not just capability)

Per research question 4 — these decision points have real prerequisite state a policy must actively build toward; simply calling the method once with default engine state will silently no-op (`False`/empty-list return) rather than exercise the real branch.

| Decision point | Gate | Exact threshold |
|---|---|---|
| `holdout_available()`/`request_holdout()` | Must have just `accept()`-ed installment 2+ of a franchise already at real Indispensability | `FRANCHISE_INDISPENSABILITY_HOLDOUT_THRESHOLD = 30.0` `[VERIFIED: callback/engine/simulation/_franchises.py:48]` — requires a policy to deliberately re-accept the SAME `franchise_id` across multiple years, since offer generation is random per year (no explicit "chase this franchise" API — the policy must scan `offer_board()`/`generate_more_listings()` results for a `franchise_id` matching one it already holds). |
| `spinoff_options()`/`launch_spinoff()` (actor track) | Franchise indispensability | `SPINOFF_INDISPENSABILITY_THRESHOLD = 55.0` `[VERIFIED: callback/engine/simulation/_franchises.py:56]` — higher bar than holdout; needs an even longer multi-installment run on one franchise. |
| `multi_picture_deal_available()` | Standing score, right after `accept()` | `MULTI_PICTURE_MIN_STANDING = 40.0` `[VERIFIED: callback/engine/leverage/multi_picture_deal.py:13]` — reachable by any archetype that gets a lead role and builds Standing normally; call `sign_multi_picture_deal()` immediately after `accept()`, before `choose_deal()`. |
| `directing_franchise_options()` (sequel pitch) | Franchise not too dormant | `SEQUEL_ELIGIBLE_MAX_DORMANT_YEARS = 4` `[VERIFIED: callback/engine/simulation/_franchises.py:23]` — a director-track policy must first build (or inherit, via the shared franchise pool) a franchise with a recent installment, i.e. pass `new_franchise=True` on `start_directing_project` early, then pitch a sequel to the SAME `franchise_id` within 4 years of the last installment. |
| `directing_reboot_options()`/`pitch_reboot()` | Franchise fully retired and dormant long enough | `REBOOT_MIN_DORMANT_YEARS = 5` `[VERIFIED: callback/engine/simulation/_franchises.py:194]` — this requires letting a franchise decay all the way to `retired_franchises` (a background process — `decay_dormant_franchises`, not directly controllable) and then waiting ≥5 more years. Longest-horizon gate in the engine; a 60-year `years` budget is enough but the archetype must NOT keep the franchise alive (i.e. deliberately stop pitching sequels to it) to let it retire in the first place. |
| `merchandising_available()` | Animated + franchise role + Standing | `can_negotiate_merchandising(standing_score)` gate in `leverage/merchandising.py` (threshold not re-verified this session — reachable opportunistically since FDR already conditions on it: `_full_data_report.py:116`) `[CITED: leverage/merchandising.py, referenced via session.py:904-912]` | Already probabilistically reachable in existing scripts whenever an animated franchise role happens to be offered at sufficient Standing — no extra engineering needed beyond accepting such a role when it appears. |
| `directing_spinoff_options()` | Franchise indispensability (director side has NO `you_are_current_lead` gate, unlike the actor path) | `SPINOFF_INDISPENSABILITY_THRESHOLD = 55.0` (same constant, reused — `session.py:698-706` docstring confirms it's the same bar minus the lead-actor gate) | Same multi-installment build-up as the actor-track spinoff, but reachable even after being recast/written out as the actor, since directing reads the shared franchise pool. |

**Practical implication for the planner:** at least one archetype (the natural candidate per CONTEXT.md's own naming is `franchise-maximizer`) needs a policy that specifically re-accepts/re-pitches the SAME franchise repeatedly across a run (rather than every existing script's "take the best offer this year regardless of continuity" logic) to ever reach holdout/spinoff/reboot territory. This is a genuinely different targeting strategy than anything in the 5 existing scripts, which never track `franchise_id` continuity across years at all — `grep`-confirmed: none of `FDR`/`QR`/`SR`/`RS`/`DR`'s offer-scoring functions read `o["franchise_id"]` or `o["installment_number"]` when picking `best`.

## Common Pitfalls

### Pitfall 1: Hard-coded `session.start("conservatory", "work")` everywhere
**What goes wrong:** Every existing script literally starts with `session.start("conservatory", "work")`, so 3 of 4 backgrounds get zero exercise no matter how many tendencies you add unless a new archetype explicitly varies it.
**Why it happens:** The scripts predate the coverage requirement — they were written to compare *policy* differences with a fixed starting point, not to cover the option space.
**How to avoid:** Assign a distinct background to at least one archetype apiece where it's thematically sensible (e.g. `family_money` for `family-first` or `indie-purist`, `discovered` for `gambler`, `regional_stage` for a late-starting `burnout-avoider`) — this "covers" background almost for free while also giving each archetype a more distinct starting shape.
**Warning signs:** A coverage report still showing background gaps after 8 archetype runs — check every `session.start(...)` call site first.

### Pitfall 2: A cycle list containing an option is not proof the option ever fires
**What goes wrong:** `dev_action_cycle` in every existing script *lists* 8 of the 9 `DEV_ACTIONS`, but which action is actually invoked depends on `tick % len(dev_action_cycle)`, and `tick` only increments inside the `while session.quarters_remaining_this_year() > 0:` loop when a project actually exists to work on. A short/early career, or a career where `can_start_new_project` gates delay the slate, can walk through many quarters without ever landing on a low-frequency list index. **This is exactly why `self_finance`/`drawer` show 0% coverage despite being technically representable in a cycle format for other scripts.**
**Why it happens:** Modulo-cycling against a mutable `tick` that's shared across acting AND directing loops (in FDR) makes the actual sequence of actions non-obvious from reading the list alone.
**How to avoid:** For the coverage-critical archetypes, don't rely on modulo-cycling through a list that also contains higher-priority actions (`attach_star` appears twice in every existing cycle, further diluting the low-frequency entries). Either give a dedicated archetype a dev-action policy that explicitly forces `self_finance`/`drawer` under specific conditions (e.g., "drawer" whenever momentum is `"fading"` and money is tight; "self_finance" whenever a project's been sitting at `"building"` momentum for N quarters), or verify via the coverage tally — don't assume a list literal is coverage.
**Warning signs:** Coverage report shows 0 visits for an option that visibly appears in a policy's own source-level constant list — this pitfall is the actual observed cause of the `self_finance`/`drawer` gap above.

### Pitfall 3: `_quality_report.py`'s awards-campaign call is missing a required argument
**What goes wrong:** `session.run_awards_campaign(spend_millions=2.0)` at `_quality_report.py:213` omits `category`, which has no default in `Session.run_awards_campaign(self, category: str, spend_millions: float = 1.0, attempt_category_fraud: bool = False)` (`session.py:1373`). If `awards_campaign_available()` (gated on `spotlight >= AWARDS_SPOTLIGHT_THRESHOLD = 68.0`, `session.py:196,1359-1360`) ever returns `True` during a `_quality_report.py` run, this call raises `TypeError` and the script crashes.
**Why it happens:** Likely written before `category` became a required parameter, or the call was never actually exercised in a test run that reached a high-spotlight film (spotlight ≥68 is a real bar, so it may simply never have fired against the seeds this script was smoke-tested with).
**How to avoid:** Any new archetype policy exercising awards must call with an explicit category, e.g. `session.run_awards_campaign(category=session.available_award_categories()[0], spend_millions=2.0)` (or pick deliberately among `LEAD`/`SUPPORTING`/`ENSEMBLE`/`BREAKTHROUGH` per archetype to cover all 4). Do not copy `_quality_report.py`'s call site as-is.
**Warning signs:** A `TypeError: run_awards_campaign() missing 1 required positional argument: 'category'` traceback the first time a policy run produces a genuinely great film. This is a **pre-existing bug in `_quality_report.py`**, independent of anything Phase 1 adds — worth a one-line note in the phase's findings even though fixing legacy scripts isn't itself an explicit success criterion (the new archetype code must not repeat it).

### Pitfall 4: Studio overrule means "requested" ≠ "resolved" — coverage must tally the right field
**What goes wrong:** `choose_release(strategy)` treats `strategy` as a *request*; the actually-resolved strategy is `decide_release_strategy()`'s output, reported back as `result["release_label"]`, with `result["studio_overruled"]` telling you whether they differed (`session.py:1184-1185,1237-1253`). A coverage tool that tallies off the *argument passed to* `choose_release` will over-report `wide`/`limited` coverage (since a request can be silently overruled into whatever the studio prefers) and under-report `festival`/`streaming`/`shelved` (which might occasionally occur via overrule even when never requested).
**Why it happens:** The natural instrumentation point (wrapping the method call) sees the argument, not the resolved outcome, unless the wrapper also inspects the return dict.
**How to avoid:** The coverage tool must tally BOTH the requested value (did the player-facing decision get exercised) AND the resolved value (did the actual outcome branch fire) — CONTEXT.md's "reachable... a policy actually triggers the option/gate" language supports treating the *request* as the countable decision point (the player's choice), with the resolved outcome as a secondary, informative signal, not the primary coverage metric. Be explicit about which one the coverage report is measuring, and say so in the decision-map's own header.
**Warning signs:** Coverage report claims 100% on `festival`/`streaming`/`shelved` release strategies despite no archetype ever explicitly requesting them — a sign the tool is reading resolved outcomes instead of requests.

### Pitfall 5: Series projects (`project_type == "series"`) skip the entire release/box-office decision branch
**What goes wrong:** `Session.choose_release()` dispatches to `_choose_release_series()` whenever `is_series()` is true (`session.py:1176-1177`), which — per its own docstring — has **no release-strategy question and no box-office bonus at all**, "deliberately... unlike a film, a season isn't sold to theaters or shopped for streaming rights after the fact" (`session.py:1270-1290`). Any archetype/coverage tally that assumes every accepted role goes through the film-shaped `choose_release` options will silently skip real decision points (renewal, in particular) whenever a series role is accepted.
**Why it happens:** `offer_this_year`/`sample_role` can generate `project_type == "series"` roles at random; no existing script special-cases them beyond `episode_labels()` for scene count.
**How to avoid:** The coverage tool should treat "series renewal" (whether `role.series_renewable` and the resulting `renewed` boolean) as its own decision-adjacent outcome to track separately, and should not count a series project's *absence* of a release-strategy request as a coverage failure — it's structurally not applicable to that project type.
**Warning signs:** A coverage report flagging "release strategy never requested" for a run-year that was actually a series project, not a missed decision.

## Code Examples

### Reading `Session`'s own return-value fields instead of engine internals (the pattern every new archetype must follow)
```python
# Source: callback/engine/simulation/_quality_report.py:58-66 (verified read this session) —
# scoring an offer using ONLY fields Session.offer_board() already returns, never actor.offers
# internals directly.
def _offer_fit_score(session: Session, offer: dict) -> float:
    buzz = BUZZ_RANK.get(offer.get("buzz_band"), 0) * 30.0
    demand = world_genre_demand(session.state.genre_heat, offer["genre"])  # <- the one place every
    # existing script reaches past Session (session.state.genre_heat) for a read-only signal Session
    # itself doesn't yet surface as a method — matches the project's own documented precedent
    # ("verify.py already uses this same read-only access for reporting" — _report_sim.py:6-8).
    billing_payoff = PRESTIGE_BILLING_WEIGHT.get(offer["billing"], 0.0)
    return (buzz + demand * 0.5) * billing_payoff
```

### The exact call sequence for a full acting decision chain (every decision point in order)
```python
# Source: callback/engine/simulation/_full_data_report.py:109-158 (verified read this session,
# lightly excerpted for the full decision-order reference — a new archetype extends this shape).
session.accept(best["index"])
bonus_type = "first_dollar_gross" if session.box_office_bonus_available("first_dollar_gross") else "net_points"
want_merch = session.merchandising_available()
session.choose_deal(want_approvals=..., want_box_office_bonus=True, bonus_type=bonus_type, want_merchandising=want_merch)
session.choose_prep(...)
for episode in session.episode_labels():          # 1 pass (film) or 2 (series premiere+finale)
    for scene_choice in SCENE_POSITIONS:            # 3 scenes each
        session.play_scene(scene_choice)
if session.rating_cut_available():
    session.choose_rating_stance(...)
session.request_marketing_push()
result = session.choose_release(strategy)
```

### The exact call sequence for one quarter of directing (order matters — attach target must be set before `advance_directing`)
```python
# Source: callback/engine/simulation/session.py:1918-1936 (advance_directing's own attach_star
# handling — verified read this session), showing WHY choose_attach_star_target must precede
# advance_directing(project_index, "attach_star").
if action == "attach_star":
    opts = session.attach_star_target_options()
    session.choose_attach_star_target(opts[i]["id"], atype)   # <- must be called first
result = session.advance_directing(project_index, action)      # <- reads self._director_attach_target_npc_id
```

## State of the Art

Not applicable to this phase's domain — this is a closed, internal, stdlib-only engine with no upstream ecosystem to track (per CLAUDE.md, no third-party framework choices are in play). The only "state of the art" question is internal: which of the 5 existing report scripts is current. That is answered definitively by the scripts' own docstrings (all cross-reference each other):

| Superseded script | Superseded by | Per its own docstring |
|---|---|---|
| `_smart_report.py` | `_full_data_report.py`'s `"gambler"` tendency | `_smart_report.py:1-3` — `"Superseded by _full_data_report.py's 'gambler' tendency for new work..."` |
| `_report_sim.py` | `_full_data_report.py` | `_report_sim.py:1-2` — `"Superseded by _full_data_report.py for new work..."` |
| `_director_report.py` | `_full_data_report.py` | `_director_report.py:1-3` — `"Superseded by _full_data_report.py for new work..."` |
| `_quality_report.py` | `_full_data_report.py`'s `"prestige"` tendency (which it explicitly reuses) | `_quality_report.py:1-4` — `"This policy is now also available as _full_data_report.py's 'prestige' tendency... prefer that one for new work; ... Kept as its own script for the exhaustive, narrated per-year ledger below."` |

**Conclusion:** `_full_data_report.py` is the pattern to extend for `_archetype_policies.py`. The other four remain useful as *reference* for decision-call-order and narration style (especially `_quality_report.py`'s printed ledger, useful as a debugging aid while building new archetypes) but should not be duplicated or extended themselves.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `can_negotiate_merchandising`'s exact Standing threshold in `leverage/merchandising.py` was not read this session (only cross-referenced via `session.py`'s call site and `_full_data_report.py`'s conditional use of it) | Gated Decision Points table | Low — the gate is already handled opportunistically by existing scripts' `merchandising_available()` check; a new archetype doesn't need the exact number, just to call the check before asking. |
| A2 | The exact `AWARDS_SPOTLIGHT_THRESHOLD = 68.0` gate difficulty (how often a real career actually produces a spotlight-68+ film) was not empirically sampled this session — I know the constant `[VERIFIED: session.py:196]` but not its typical hit-rate across a 60-year run | Coverage Gap #12 | Medium — if spotlight-68 films are rare under most archetype policies, the planner may need a dedicated high-quality archetype (prestige-chaser is the natural fit) with several film attempts to guarantee at least one awards-eligible result per coverage run; worth a quick empirical check during planning/execution rather than assuming one run suffices. |

**If this table is empty:** N/A — two items above; both are low/medium risk and don't block planning, only inform how thoroughly the planner should budget "does this reach the awards branch at all" verification.

## Open Questions

1. **Should `ambition` remain a purely cosmetic field, or is fixing its zero-mechanical-effect status in scope for a later phase?**
   - What we know: `self.ambition` (session.py:245,317-318) is read nowhere else in the codebase this session's `grep` could find — it has zero effect on any formula.
   - What's unclear: The phase description text lists "background/ambition choices" together as if both branch mechanically; CONTEXT.md's own exclusion rule ("purely cosmetic/flavor text... excluded") means ambition is correctly excluded from MAP-01's catalog as currently implemented, but this may not be what the original design docs intended (the design docs weren't checked for an `ambition` mechanical spec this session — out of this research's scope but worth a design-doc grep in Phase 3/4 if "ambition never matters" turns up as a real balance finding).
   - Recommendation: Note the exclusion explicitly in the decision-map doc (a one-line callout, not a full row) so it reads as "investigated and confirmed cosmetic-only," not "forgotten." Do not attempt to fix it in Phase 1 — out of this phase's scope (MAP-01/POLICY-01/POLICY-02 only).

2. **Exact `can_negotiate_merchandising` Standing threshold (see Assumption A1)**
   - What we know: it's Standing-gated and animation+franchise-gated; existing scripts already call it opportunistically.
   - What's unclear: the exact numeric bar, and therefore how reliably any given archetype reaches it within a 60-year run.
   - Recommendation: the planner/executor should read `leverage/merchandising.py`'s `can_negotiate_merchandising` directly when implementing the archetype that's meant to guarantee this decision point's coverage (likely `franchise-maximizer`), rather than relying on the probabilistic "whenever it happens to come up" pattern every existing script uses.

## Environment Availability

Skipped — this phase has no external dependencies. Python 3.13.1 and 3.14.3 are both confirmed present on the dev machine `[VERIFIED: python --version / python3 --version, this session]`, matching `callback/engine/README.md`'s documented run commands; the engine is 100% stdlib, and the new decision-map doc is plain Markdown. No fallback planning needed.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | `unittest` (stdlib), auto-discovered; `pytest` also works against the same suite (a `.pytest_cache/` exists at repo root per `STRUCTURE.md`, though no `pytest.ini` configures it) `[VERIFIED: callback/engine/README.md:66]` |
| Config file | none — `python3 -m unittest discover callback/engine/tests` |
| Quick run command | `python3 -m unittest callback.engine.tests.test_session -v` (or a new `test_archetype_policies` module, once created) |
| Full suite command | `python3 -m unittest discover callback/engine/tests` (117+ tests as of `README.md`) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| MAP-01 | Decision-map doc exists and is internally consistent (every row cites a real module/function) | manual-only (a Markdown doc has no executable assertion surface) | n/a — reviewed by the planner/verifier reading the file | n/a |
| POLICY-01 | ≥8 archetype functions exist in `_archetype_policies.py`, each runnable end-to-end without raising | unit/smoke | `python3 -m unittest -v callback.engine.tests.test_archetype_policies` (new file, one test per archetype calling `run(seed=<fixed>, years=<short>)` and asserting no exception + a sane summary shape) | ❌ Wave 0 — file does not exist yet |
| POLICY-02 | Coverage report shows zero decision points unvisited across the full archetype set | unit/integration | `python3 -m unittest -v callback.engine.tests.test_decision_coverage` (new file — runs the full 8-archetype set at a fixed seed set and asserts the coverage tool's gap list is empty) | ❌ Wave 0 — file does not exist yet, and the coverage tool itself does not exist yet |

### Sampling Rate
- **Per task commit:** run the specific new/changed archetype's smoke test (`python3 -m unittest -v callback.engine.tests.test_archetype_policies.TestPrestigeChaser` or equivalent single-archetype invocation) — each archetype run over even a short `years` value (10–15) is enough to smoke-test that it doesn't crash; a longer run (60, matching every existing script's default) is needed for the actual coverage assertion.
- **Per wave merge:** full `test_archetype_policies` + `test_decision_coverage` suite.
- **Phase gate:** `python3 -m unittest discover callback/engine/tests` green (the whole existing 117+-test suite, to confirm nothing in `session.py`/engine internals was accidentally touched — this phase should be additive-only) AND the coverage report showing zero gaps, before `/gsd-verify-work`.

### Wave 0 Gaps
- [ ] `callback/engine/tests/test_archetype_policies.py` — smoke-tests each of the 8+ archetype functions (new)
- [ ] `callback/engine/tests/test_decision_coverage.py` — asserts the coverage tool reports zero gaps across the full archetype set at a fixed seed (or seed range) (new)
- [ ] `simulation/_decision_coverage.py` (or equivalent module/function) — the coverage-check tool itself; nothing like it exists yet anywhere in `simulation/` (confirmed by `grep`ing `_full_data_report`/`_quality_report`/`_smart_report`/`_report_sim`/`_director_report`/`_sim_policy_shared` against `callback/engine/tests/` — zero matches, i.e. none of the 5 existing report scripts is even referenced by the test suite today)
- Framework install: none — `unittest` is stdlib, no install step.

## Security Domain

`security_enforcement` is `true` in `.planning/config.json`, so this section is included per protocol, but it is **almost entirely not applicable** to this phase's actual content.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Single-process, offline, no accounts, no network layer `[VERIFIED: callback/engine README/ARCHITECTURE.md — "Authentication: Not applicable — single-process, offline, no network layer"]`. |
| V3 Session Management | No | `Session` here is a gameplay-state class, not an auth session; no cookies/tokens exist. |
| V4 Access Control | No | No multi-user/permission model exists in this engine. |
| V5 Input Validation | Marginally yes, for the new code only | New archetype policy code accepts no external/untrusted input (seeds are internal integers, decision-map is a static doc) — this phase introduces no new input-validation surface. If the coverage tool ever grows a CLI wrapper, validate seed/years as ints per existing `cli.py`'s own safe-default convention (`auto_default_index`-style clamping, `ARCHITECTURE.md`'s Error Handling section), not by adding a new validation framework. |
| V6 Cryptography | No | No secrets, no crypto anywhere in this engine. |

### Known Threat Patterns for this stack
Not applicable — this is an offline, single-player, stdlib-only simulation with no network/database/auth surface. No STRIDE-relevant patterns apply to a decision-map Markdown doc or to policy functions that only call an already-tested, already-trusted `Session` API with internally-generated seeds. Skip formal threat-pattern documentation for this phase; it is not a meaningful use of the planner's or verifier's attention here.

## Sources

### Primary (HIGH confidence — all read directly this session via `Read`/`Grep`, cited with exact line ranges throughout this document)
- `callback/engine/simulation/session.py` — full file (2235 lines), read start to finish this session.
- `callback/engine/simulation/_full_data_report.py`, `_quality_report.py`, `_smart_report.py`, `_report_sim.py`, `_director_report.py`, `_sim_policy_shared.py` — full files, read this session.
- `callback/engine/actor/prep.py`, `actor/positions.py`, `actor/release.py`, `actor/studios.py` — relevant sections/full files, read this session.
- `callback/engine/director/development.py`, `director/casting.py`, `director/shoot_style.py` — relevant sections, read this session.
- `callback/engine/leverage/catalogue.py`, `leverage/indispensability.py`, `leverage/multi_picture_deal.py` — relevant sections, read this session.
- `callback/engine/rolodex/interactions.py` — full file, read this session.
- `callback/engine/simulation/_backgrounds.py`, `simulation/_franchises.py`, `studio/slate.py` — relevant sections, read this session.
- `callback/engine/README.md`, `.planning/codebase/ARCHITECTURE.md`, `.planning/codebase/STRUCTURE.md` — read this session (pre-existing codebase-map documents).
- `.planning/phases/01-decision-space-playtest-policy-coverage/01-CONTEXT.md`, `.planning/REQUIREMENTS.md`, `.planning/STATE.md`, `.planning/PROJECT.md`, `.planning/config.json` — read this session.

### Secondary (MEDIUM confidence)
None — no web/external documentation was consulted (all research providers are disabled in `.planning/config.json`, and none were needed: this phase's entire domain is the local codebase).

### Tertiary (LOW confidence)
None.

## Metadata

**Confidence breakdown:**
- Decision-point inventory (MAP-01 support): HIGH — every entry cites a file/line I opened this session; the `Session` file was read in full, not sampled.
- Coverage gap analysis (POLICY-02 support): HIGH — cross-referenced against the full text of all 5 existing report scripts, also read in full.
- Gated-decision thresholds: HIGH for the ones quoted with exact constants; MEDIUM for the two items in the Assumptions Log (merchandising threshold, awards spotlight hit-rate) which were not independently sampled/verified this session.
- Architecture/pattern recommendations: HIGH — directly mirror the existing, working `_full_data_report.py` pattern; no novel architecture proposed.

**Research date:** 2026-08-20
**Valid until:** Effectively indefinite for the inventory itself (it's a snapshot of committed source, stable until someone changes `session.py`), but re-verify line numbers if any `session.py`/`development.py`/`release.py`/etc. edits land between this research and PLAN.md execution — recommend a fresh `grep` of the specific line-cited claims immediately before planning if more than a few days elapse.
