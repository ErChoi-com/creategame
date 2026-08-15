# CALLBACK — project bundle

A design document for a film-industry career life simulator, developed from a teardown of
BitLife's Actor Pack, plus the simulation harnesses used to tune and then stress-test it.

## Files

| File | What it is |
|---|---|
| **callback-design-doc-v8.md** | The design document. 2,659 lines, 15 parts. Start at Part 0 (design rules and cut list), then Part 5 (the work itself — this is the core loop). |
| **callback-design-review.md** | **Read this second.** An adversarial review plus the first end-to-end career simulation. It finds that the game, as specified, does not produce a career. Fix list is in section 10. |
| **callback-sim.py** | Tuning harness. Seven subsystem verifications. |
| **callback-career-sim.py** | End-to-end career simulation — wires the subsystems together and runs 4,000 careers against the doc's own targets. Currently fails all of them. |

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

## State of the project

The reception model (§4.10), studio slate economics (§8.2), genre cycles (§9.3) and the director
pipeline (§7.4) are real, simulated, and tuned.

The **Standing economy does not close** — Standing gains are billing-weighted and decay is not, so
a beginner can never climb out of bit parts. 80% of simulated careers never play a lead. This is
the first thing to fix and nothing else matters until it is. See review section 1.

Part 5 (the creative system) and Part 4 (the actor) define "Notices" and "Ensemble" as different
quantities and have never been reconciled. See review section 2.

There is no design yet for character creation, the opening hour, or the interface.
See review section 4.
