# CALLBACK — project bundle

A design document for a film-industry career life simulator, developed from a teardown of
BitLife's Actor Pack, plus the simulation harnesses used to tune and then stress-test it.

## Files

| File | What it is |
|---|---|
| **design/** | The design document, split one file per Part — was a single 2,775-line file, now 16 part files plus an index. Start at `design/00-index.md`: front matter, the v9 changelog, and a table of contents. Then Part 0 (design rules and cut list), then Part 5 (the work itself — this is the core loop). Every v9 change is marked `*(v9 — ...)*` in place, next to the v8 text it corrects, so each part reads as one continuous account of what was tried and what was wrong with it, not a separate changelog. |
| **callback-design-review.md** | **Read this second.** An adversarial review plus the first end-to-end career simulation, run against the *original* v8 text. It finds that the game, as specified, does not produce a career. Fix list is in section 10 — v9 folds that list back into the sections it applies to. |
| **callback-sim.py** | Tuning harness. Seven subsystem verifications, against the *original* v8 constants — not yet updated for v9's fixes (see below). |
| **callback-career-sim.py** | End-to-end career simulation against the *original* v8 constants — wires the subsystems together and runs 4,000 careers against the doc's own targets. Fails all of them, which is what v9's §4.3 fixes. |

### `design/` layout

| File | Part |
|---|---|
| `00-index.md` | Front matter, the v9 changelog, table of contents |
| `part-00-design-rules-and-cut-list.md` | 0 — the rules every system has to pass, the decision budget, Ambitions, what got cut and why |
| `part-01-bitlife-teardown.md` | 1 — how BitLife's Actor Pack actually works |
| `part-02-whats-missing.md` | 2 — six structural gaps in it |
| `part-03-design-overview.md` | 3 — the pitch, the five pillars, the shared spine |
| `part-04-the-actor.md` | 4 — attributes, Persona, Standing *(v9-fixed)*, the offer board *(v9-fixed)*, the deal, prep, the shoot, the calendar, aging, reception *(v9-fixed)*, awards, the Rolodex, scandal |
| `part-05-the-work.md` | 5 — the six-dial palette *(v9 relabelled)*, coherence, landmarks, the four-position performance *(v9 relabelled)*, shape as three real scenes *(v9-rewritten)* |
| `part-06-leverage.md` | 6 — favours, approvals *(v9-fixed)*, indispensability *(v9-fixed)*, franchise leverage, the ~40-verb action catalogue |
| `part-07-the-director.md` | 7 — the director as a full parallel career (unbuilt) |
| `part-08-the-studio.md` | 8 — the studio-executive layer (unbuilt) |
| `part-09-genres-franchises-and-tie-ins.md` | 9 — genres as economies, merchandise, shared universes (unbuilt) |
| `part-10-the-world.md` | 10 — guilds, strikes, festivals, territories, tech eras (unbuilt) |
| `part-11-the-life.md` | 11 — health, addiction, family, politics, money, the obituary (unbuilt) |
| `part-12-data-schemas.md` | 12 — data schemas |
| `part-13-build-plan.md` | 13 — the phased build plan |
| `part-14-tuning-targets.md` | 14 — what's verified against what; §14.9 now shows real measured numbers |
| `part-15-risks.md` | 15 — risks and mitigations, plus the closing one-line summary |

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
haven't been built or touched — but a full connective pass has since gone across all of them
looking specifically for §3.3's own rule (one Standing model, one Legibility engine, one Rolodex,
one calendar) stated but not honoured: a box-office model duplicated between §4.10 and §8.2 with
different constants, a director-side formula amendment that never actually landed in the actor
formula it amended, a handful of mechanics specified twice in different Parts with no link between
them. All now cross-referenced or unified — see `design/00-index.md`'s changelog for the full list.

**The industry now runs in the background, not just on the offer board.** §10.0, new, is the
mechanism §9.3's genre cycles, §4.12's self-running Rolodex NPCs, and §5.17/§11.8's declined-offer
payoff all assumed but never built: a role you don't take is cast with someone else through §4.4's
own casting formula, and that film gets made and resolved through §4.7 and §4.10 like any of yours.
It's what makes "your rival wins the award you wanted and flames out five years later" a real query
against simulated history instead of a scripted line, and it's scoped on purpose — full simulation
only for the people and franchises the player actually tracks, aggregate outcomes for everyone
else, the same principle §10.5 already applies to its four built industries.

A short follow-up carried that mechanism into the rest of the document: the leverage catalogue's
"Blacklist"/"Recommend" verbs and the franchise holdout now name it as what they actually move; the
director career gets a rival mechanism (§7.3) and an explanation of what development-hell
`Difficulty` was always implicitly pricing in (§7.4); franchise recasts and shared universes (§9.5,
§9.6) resolve through it instead of an unspecified process; the data schema (Part 12) gained a
pointer field so the obituary can read a declined role's real resolved outcome instead of a
hardcoded example string; and the build plan, tuning targets, and risk list each got the one-line
acknowledgment they were missing. See `design/00-index.md`'s changelog for the file-by-file list.

**The Rolodex now has a relationship layer, not just a casting weight.** Built into §10.0, kept
in the world doc on purpose rather than spread across files: NPCs carry a hidden Agenda (six
types) that shapes both their own background career and how much a player's actions actually land;
relationships move through named states (`Stranger → Familiar → Ally/Rival → Loyal/Estranged →
Legacy/Severed`) instead of a raw affinity number; new pull actions build a relationship instead of
spending one; a small, budget-capped set of NPC-initiated moments make the relationship feel like
it runs on its own; and losing someone — their own simulated career ending — has real, bounded,
one-time weight instead of just going quiet.

**A language audit then closed the gaps the earlier plain-language pass missed.** That pass
(§4.1, §5.3, §5.5) cleaned the palette dials, the four positions, and Notices/Ensemble in the
sections it touched directly, but didn't propagate everywhere: **Fit** never got the gloss
Legibility did, `YourNotices` leaked back into prose after §5.6 had already settled on "Notices,"
**Indispensability** read as a raw stat with no stated link to the doc's own "shown as words, not
numbers" rule (§15), and the director's attribute table (§7.2) looked like a raw stat block despite
§15 saying it gets the same word-only treatment as the actor's. All four fixed — a gloss, a term
swap, or an explicit citation of a rule the document already had, nothing mechanical changed.

**Not yet folded back in:** `callback-sim.py` and `callback-career-sim.py` still test the *original*
v8 constants, so running them now reproduces the review's failing numbers on purpose — they haven't
been updated to check v9's formulas. Re-tuning them against the corrected §4.3/§4.4/§4.10 is the
natural next step if this design is implemented again.
