---
phase: 1
slug: decision-space-playtest-policy-coverage
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-20
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | `unittest` (stdlib), auto-discovered; `pytest` also runs the same suite |
| **Config file** | none — `python3 -m unittest discover callback/engine/tests` |
| **Quick run command** | `python3 -m unittest -v callback.engine.tests.test_archetype_policies` |
| **Full suite command** | `python3 -m unittest discover callback/engine/tests` |
| **Estimated runtime** | ~30-60 seconds (117+ existing tests, plus new archetype/coverage tests) |

---

## Sampling Rate

- **After every task commit:** Run the specific new/changed archetype's smoke test (single-archetype invocation over a short `years` value, e.g. 10-15)
- **After every plan wave:** Run `python3 -m unittest -v callback.engine.tests.test_archetype_policies callback.engine.tests.test_decision_coverage`
- **Before `/gsd-verify-work`:** `python3 -m unittest discover callback/engine/tests` must be fully green (confirms this additive-only phase touched nothing in existing engine internals), AND the coverage report must show zero gaps
- **Max feedback latency:** ~60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 0 | MAP-01, POLICY-01, POLICY-02 | — / N/A | N/A (offline stdlib sim, no auth/network surface) | unit | `python3 -m unittest -v callback.engine.tests.test_archetype_policies` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 0 | POLICY-02 | — / N/A | N/A | unit/integration | `python3 -m unittest -v callback.engine.tests.test_decision_coverage` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

*Detailed per-task rows are filled in by the planner once PLAN.md task IDs exist; the two rows above are the Wave 0 anchors research identified.*

---

## Wave 0 Requirements

- [ ] `callback/engine/tests/test_archetype_policies.py` — smoke-tests each of the 8+ archetype functions (new)
- [ ] `callback/engine/tests/test_decision_coverage.py` — asserts the coverage tool reports zero gaps across the full archetype set at a fixed seed/seed range (new)
- [ ] `callback/engine/simulation/_decision_coverage.py` (or equivalent) — the coverage-check tool itself; nothing like it exists in `simulation/` today
- [ ] `callback/engine/simulation/_archetype_policies.py` — the archetype policy functions themselves (new)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Decision-map doc is internally consistent — every row cites a real, currently-existing module/function | MAP-01 | A Markdown doc has no executable assertion surface | Planner/verifier spot-checks a sample of catalog rows against the cited source locations during plan-check and verify-work |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending

---

## Security Note

`security_enforcement` is `true` in `.planning/config.json` (project default), so this section is retained per protocol, but per Research §Security Domain it is not meaningfully applicable: this is an offline, single-process, stdlib-only simulation engine with no auth, network, session, or crypto surface (`ARCHITECTURE.md`: "Authentication: Not applicable"). New archetype policy code in this phase accepts no external/untrusted input — seeds are internal integers, the decision-map is a static doc. No `<threat_model>` block content beyond this note is warranted for this phase's PLAN.md.
