# Codebase Concerns

**Analysis Date:** 2026-08-19

## Tech Debt

**`simulation/session.py` is a 2,000-line, 114-method God-facade:**
- Issue: `Session` is intentionally the single player-facing API (per `callback/engine/README.md`'s "one spine" design), but as a result every new system (franchises, directing, multi-picture deals, script notes, marketing pushes, etc.) adds more methods to one file/class rather than splitting into sub-facades.
- Files: `callback/engine/simulation/session.py` (2000 lines)
- Impact: Any change touching the player boundary requires navigating a very large single file; merge conflicts likely when multiple systems are worked on in parallel; onboarding cost is high.
- Fix approach: Consider splitting `Session` into per-domain mixins (acting, directing, leverage, franchises) composed onto one class, preserving the single public type while reducing per-file size.

**Five overlapping one-off reporting/simulation scripts in `simulation/`:**
- Issue: `_report_sim.py`, `_smart_report.py`, `_quality_report.py`, `_director_report.py` are explicitly documented in their own docstrings as "superseded by `_full_data_report.py`" but are kept in the tree anyway ("kept as its own script for X reason").
- Files: `callback/engine/simulation/_report_sim.py`, `_smart_report.py`, `_quality_report.py`, `_director_report.py`, `_full_data_report.py` (277–425 lines each)
- Impact: ~1,400 lines of largely-duplicated policy logic (offer scoring, triage heuristics, casting/shoot choices) across five scripts that must be kept in sync by hand when `Session`'s API changes; easy for one script to silently drift out of date since none are covered by the test suite (`callback/engine/tests/`).
- Fix approach: Either delete the four "superseded" scripts now that `_full_data_report.py` covers their scenarios, or extract the shared policy heuristics into a single importable module the scripts compose (partial start already exists in `simulation/_sim_policy_shared.py`, 26 lines — underused).

**Large uncommitted working tree spanning nearly every engine module:**
- Issue: `git status` shows 29 modified files and 17 new/untracked files (new modules: `actor/rating.py`, `actor/series.py`, `director/shoot_style.py`, `leverage/merchandising.py`, five `simulation/_*_report.py` scripts, six new test files) with no commits yet capturing this work.
- Files: see `git status --short` at repo root; largest diffs in `callback/engine/simulation/session.py`, `tests/test_session.py` (+324), `tests/test_leverage.py` (+126), `tests/test_studios.py` (+60)
- Impact: A crash, `git clean`, or bad `git reset` before these are committed would lose substantial unrecorded work (6,391 insertions across 37 files per `git diff --stat`).
- Fix approach: Commit in logical, reviewable slices (e.g., merchandising, series/rating, shoot_style, reports) rather than one giant commit.

**Self-documented, unimplemented/simplified systems (from `callback/engine/README.md`'s "Known gaps" section):**
- Issue: Several systems are intentional placeholders rather than full implementations:
  - `actor/offers.py`'s `sample_role()` doesn't scale role difficulty to the actor's own Standing — a real Standing-aware listing generator is still needed.
  - `actor/palette.py`'s `GENRE_DIAL_WEIGHTS`/`CANONICAL_ARCHETYPES` are this pass's own readings, not verified `design/` constants.
  - Directing never participates in the franchise/sequel system (`simulation/_franchises.py`).
  - The full multi-offer calendar/deal-negotiation UI isn't built (one project per year only).
  - `world/guild.py`'s `is_eligible()` isn't wired into `actor/offers.py`'s separately-implemented union-credit check.
  - Politics, festivals-as-submission beyond the acquisition formula, international industries, tech eras, censorship, and merchandise/tie-ins (§9.7–9.9, though `leverage/merchandising.py` is now a new untracked file that may address part of this) are unimplemented.
- Files: `callback/engine/actor/offers.py`, `callback/engine/actor/palette.py`, `callback/engine/simulation/_franchises.py`, `callback/engine/world/guild.py`, `callback/engine/README.md` (lines 536–583)
- Impact: Headless/simulated careers land relatively few credits per offer seen because most rolls are too hard for a fresh actor — a known, self-diagnosed structural gap, not a bug.
- Fix approach: README already names the fix direction for each (a Standing-aware listing generator is the biggest lever); no action needed beyond tracking as backlog.

**v10/v13/v15 director-mode numbers unverified against the simulation-verification pipeline:**
- Issue: `README.md`'s v10 section states plainly that Bankability-scaled ranges, event-probability formulas, the rating dampener, and the hire-offer probability have not been run through `verify.py`'s statistical checks the way earlier systems were (`design/part-07` §7.4/§7.12/§7.13/§7.14 "verification status" notes still open).
- Files: `callback/engine/simulation/verify.py`, `callback/engine/director/casting.py`, `callback/engine/director/shoot_style.py`, `callback/engine/director/development.py`
- Impact: New director-mode balance numbers could be off (too easy/too hard) without anyone having done the statistical check that caught real issues in earlier systems (e.g., the Affection decay and box-office-bonus threshold fixes documented in the same README).
- Fix approach: Run `python3 -m callback.engine.simulation.verify all` equivalents (or extend `verify.py`) against the new director-mode constants; the `_director_report.py`/`_full_data_report.py` scripts already produce the raw data needed.

## Known Bugs

No open/reproducible bugs found in the current tree — the full test suite passes (536 passed, 6 skipped, `callback/engine/tests/`). `README.md` documents several *already-fixed* historical bugs (Streaming ROI scale bug, role-fee billing-tier bug, budget/fee conflation bug) inline at their fix sites; these are resolved, not outstanding.

## Security Considerations

**Not applicable / low risk:** This is an offline, single-player terminal simulation (`callback/engine/simulation/cli.py`) with no network I/O, no user-supplied file paths, no external API calls, and no persisted credentials found in the engine package. No `.env`, credential, or secret files were found in `callback/engine/`.

## Performance Bottlenecks

**None significant detected.** Full test suite (536 tests) runs in ~1.3 seconds. `simulation/session.py`'s `offer_board()` generates 20+ listings per year (`OFFER_BOARD_MIN_LISTINGS`/`OFFER_BOARD_MAX_LISTINGS`/`OFFER_BOARD_HARD_CAP` in `callback/engine/simulation/session.py`), each scored through `utility()`/`offer_probability()` — bounded and capped, not a concern at current scale. No profiling data exists; if a future GUI/web frontend is layered on `Session` per the README's stated design, per-request cost of `offer_board()` should be re-checked.

## Fragile Areas

**`director/casting.py` was previously accidentally overwritten by a `Write`-tool edit:**
- Files: `callback/engine/director/casting.py`
- Why fragile: README documents that an early draft used a file-overwrite operation instead of extending the pre-existing, committed `evaluate_candidate()` wrapper, and was only caught because `test_director.py` failed to import — recovered from git history.
- Safe modification: Always read the existing file before editing/extending `director/casting.py` (or any file in this codebase) rather than regenerating it wholesale; rely on the test suite import checks as a tripwire.
- Test coverage: `callback/engine/tests/test_director_mode.py`, `callback/engine/tests/test_director_v10.py` cover this module; both currently pass.

**`simulation/session.py` and `simulation/_director.py` (1,410 lines) are the two largest, most-interconnected modules:**
- Files: `callback/engine/simulation/session.py`, `callback/engine/simulation/_director.py`
- Why fragile: Both files sit at the composition point for nearly every subsystem (actor, director, leverage, franchises, studios, life) — the highest blast radius for any change of the whole engine. `_director.py` alone had a `pass  #`-style stub pattern flagged during the concerns scan (one occurrence via grep, worth a manual review before extending).
- Safe modification: Change one subsystem's Session methods at a time, run the full test suite (`python3 -m pytest callback/engine/tests -q` or `python3 -m unittest discover callback/engine/tests`) after each, and prefer adding new methods over modifying existing method signatures (per README's explicit "plain data in/out" contract at the Session boundary).
- Test coverage: `callback/engine/tests/test_session.py` (944 lines, recently +324 in the current diff) and `callback/engine/tests/test_director_v10.py` (1000 lines, new/untracked) are both large and actively growing alongside these modules — coverage looks proportionate to risk.

**Windows line-ending churn on every touched file:**
- Files: repo-wide (`README.md`, `director/casting.py`, `tests/test_director_mode.py` observed emitting LF→CRLF warnings during `git diff`)
- Why fragile: No `.gitattributes` enforcing consistent line endings was found; mixed LF/CRLF handling by git on Windows checkouts risks noisy diffs and potential merge friction across contributors on different OSes.
- Safe modification: Add a `.gitattributes` normalizing text files to LF (or explicit CRLF) if multiple contributors/OSes are expected.

## Scaling Limits

**Not applicable.** Single-process, single-player, in-memory simulation with no database, no concurrent users, and no external service dependencies. `Session(seed=...)` state lives entirely in Python objects for the duration of one process run (`callback/engine/simulation/session.py`).

## Dependencies at Risk

**None detected.** No `requirements.txt`, `pyproject.toml`, or third-party package imports were found in `callback/engine/` beyond the Python standard library (`statistics`, `collections`, `dataclasses`, etc.) and `pytest`/`unittest` for testing. This minimizes supply-chain risk but means dependency management conventions (lockfiles, version pinning) are effectively nonexistent — worth establishing before any external package is introduced.

## Missing Critical Features

**Politics, international industries, tech eras, censorship, and full merchandise/tie-in systems (design Parts 9.7–9.9, 10.5–10.7, 11.5) are unbuilt:**
- Problem: These design-doc systems (`callback/docs/design/part-09-genres-franchises-and-tie-ins.md` and related parts) have no corresponding engine implementation, per the README's own "known gaps" list.
- Blocks: Any milestone requiring these systems must design and build them from scratch; `leverage/merchandising.py` (new, untracked) may be a first step toward tie-ins but has not yet been reviewed/confirmed complete.

**Full multi-offer calendar / overlapping-deal negotiation is not built:**
- Problem: The engine models exactly one project resolution per year; the richer "multiple simultaneous offers, full fee/billing/options/pay-or-play negotiation space" described in the design docs isn't implemented — only the approvals-for-fee trade exists.
- Blocks: Any phase aiming for a more realistic overlapping-project calendar will need new scheduling/negotiation logic in `simulation/career.py` / `simulation/session.py`.

## Test Coverage Gaps

**New/untracked modules and their test files exist together, but overall coverage of the new work is unverified against the statistical `verify.py` pipeline:**
- What's not tested: `actor/rating.py`, `actor/series.py`, `director/shoot_style.py`, `leverage/merchandising.py` each have a paired new test file (`tests/test_rating.py`, `tests/test_series.py`, implicitly covered by `test_director_v10.py`, `tests/test_merchandising.py`), and unit tests pass — but none of these have been run through `simulation/verify.py`'s design-doc statistical conformance checks the way earlier systems (reception, creative) were.
- Files: `callback/engine/actor/rating.py`, `callback/engine/actor/series.py`, `callback/engine/director/shoot_style.py`, `callback/engine/leverage/merchandising.py`, `callback/engine/simulation/verify.py`
- Risk: Unit tests confirm functions behave as coded, not that the coded behavior matches the design doc's intended statistical targets (e.g., correlation targets in `design/part-05` §5.3 style checks).
- Priority: Medium — flagged explicitly in-repo by the README's own "known gaps" section as an open item for v10+ work, not a silent gap.

**No coverage found for the five `simulation/_*_report.py` one-off scripts:**
- What's not tested: `_report_sim.py`, `_smart_report.py`, `_quality_report.py`, `_director_report.py`, `_full_data_report.py` have no corresponding test files in `callback/engine/tests/`.
- Files: `callback/engine/simulation/_*_report.py`
- Risk: These scripts exercise `Session` end-to-end under realistic policies and could silently break against a `Session` API change without any test catching it — the only detection mechanism is manually running them.
- Priority: Low — they are explicitly "one-off reporting scripts," not shipped product code, but given four of five are self-described as superseded/duplicated, the cleanup fix (see Tech Debt) also resolves this gap by reducing surface area.

---

*Concerns audit: 2026-08-19*
