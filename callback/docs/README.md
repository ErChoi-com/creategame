# CALLBACK — project bundle

A design document for a film-industry career life simulator, developed from a teardown of
BitLife's Actor Pack, plus the simulation harnesses used to tune and then stress-test it.

## Files

| File | What it is |
|---|---|
| **callback-design-doc-v8.md** | The design document — still named for its original v8 draft, now carrying a v9 revision inline. 2,775 lines, 15 parts. Start at Part 0 (design rules and cut list), then Part 5 (the work itself — this is the core loop). Every v9 change is marked `*(v9 — ...)*` in place, next to the v8 text it corrects, so the document reads as one continuous account of what was tried and what was wrong with it, not a separate changelog. |
| **callback-design-review.md** | **Read this second.** An adversarial review plus the first end-to-end career simulation, run against the *original* v8 text. It finds that the game, as specified, does not produce a career. Fix list is in section 10 — v9 folds that list back into the sections it applies to. |
| **callback-sim.py** | Tuning harness. Seven subsystem verifications, against the *original* v8 constants — not yet updated for v9's fixes (see below). |
| **callback-career-sim.py** | End-to-end career simulation against the *original* v8 constants — wires the subsystems together and runs 4,000 careers against the doc's own targets. Fails all of them, which is what v9's §4.3 fixes. |

## Running the sims

No dependencies beyond the Python standard library. Python 3.8+.

```bash
python3 callback-sim.py all          # all seven subsystem checks
python3 callback-sim.py reception    # 4.10  reception-model correlations
python3 callback-sim.py palette      # 5.3-5.7 film palette, coherence, actor positions
python3 callback-sim.py leverage     # 6.4-6.5 indispensability + the holdout
python3 callback-sim.py director     # 7.4   development pipeline
python3 callback-sim.py studio       # 8.2   per-tier ROI + slate outcomes
python3 callback-sim.py genre        # 9.3   genre boom/bust cycles
python3 callback-sim.py budget       # 0.2   decision-load audit

python3 callback-career-sim.py       # the end-to-end test that fails
```

Every table in Part 14 of the design doc is reproducible from `callback-sim.py`. If you change a
constant in the doc, re-run the relevant section — several of them trade off sharply against each
other and the document records two occasions where an untested change broke something upstream.

## State of the design (v9)

The reception model (§4.10), studio slate economics (§8.2), genre cycles (§9.3) and the director
pipeline (§7.4) are real, simulated, and tuned — unchanged from v8.

The actor spine (Parts 0, 4, 5, 6) was built and played end to end, and this revision is what that
found, folded back into the document:

- **The Standing economy closes now.** §4.3 has the fix — re-centred, billing-aware, proportional
  decay instead of gains that were billing-weighted against a flat rate no beginner could outrun.
  §14.9 went from "to be verified" to a table of what a 3,000-career simulation actually measures,
  seven for seven.
- **Notices and Ensemble are defined once**, in §5.6, and §4.10 reads that single definition instead
  of restating its own.
- **Character creation and the opening hour are designed** — §4.0, new. Four backgrounds, and the
  union catch-22 §10.1 never explained a way into.
- **The shoot's three beats are three scenes, actually played** — §5.6's biggest change, done after
  the rest of the spine was already verified: what used to be one contrast-budget choice spread
  across `intro`/`turn`/`reso` by a formula is now three real decisions, with a real (bounded) cost
  attached to the dailies read between them.
- **Two smaller dead ends, found by asking what a player could never recover from**: an
  Indispensability decay that could freeze a franchise open forever instead of ending it (§6.4), and
  an agent tier nobody could ever change, which made an entire leverage move permanently unreachable
  (§4.5, §6.6).

Every `*(v9 — ...)*` note in the design doc marks one of these, in place, next to the v8 text it
corrects — there is no separate delta document. Parts 1–3, 7–13, and 15 are original v8 text and
haven't been built or touched.

**Not yet folded back in:** `callback-sim.py` and `callback-career-sim.py` still test the *original*
v8 constants, so running them now reproduces the review's failing numbers on purpose — they haven't
been updated to check v9's formulas. Re-tuning them against the corrected §4.3/§4.4/§4.10 is the
natural next step if this design is implemented again.
