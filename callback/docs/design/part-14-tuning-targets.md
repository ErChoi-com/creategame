# PART 14 — TUNING TARGETS

All values below were fit by simulation, not chosen by feel. The harness is included alongside this document — run `python3 callback-sim.py all` to reproduce every number in this Part.

## 14.1 Reception model — verified ✅

| Correlation | Target | Measured |
|---|---|---|
| Performance ↔ YourNotices | 0.70–0.80 | **0.76** ✅ |
| Performance ↔ FilmCriticScore | 0.40–0.48 | **0.42** ✅ |
| Performance ↔ Box-office ROI | 0.20–0.30 | **0.23** ✅ — the design's signature number |
| FilmCriticScore ↔ ROI | 0.20–0.30 | **0.30** ✅ |
| FilmCriticScore ↔ AudienceScore | 0.40–0.50 | **0.39** ⚠️ boundary |

These five trade off sharply against each other. **If you change any constant in §4.10, re-run the sweep** — raising the ensemble weight to make performance matter more to critics also collapses the critic/audience divergence the design depends on.

## 14.2 Studio economics — verified ✅

Per-tier medians and slate outcomes are in §8.2. Headline checks:

| Metric | Target | Measured |
|---|---|---|
| Share of all films profitable | 45–55% | **48%** (mid tier) ✅ |
| Micro-budget effective profitability (after distribution gate) | ~55% | **56%** ✅ |
| Balanced slate: P(profitable year) | 55–65% | **60%** ✅ |
| Blockbuster slate: p10 outcome | catastrophic | **−$171M** ✅ |
| Tentpole P(>2× ROI) | ≥8% | **12.9%** ✅ |

## 14.3 Director pipeline — verified ✅

| Standing | Films / 30 yrs | Median dev time | Died in dev |
|---|---|---|---|
| Newcomer (18) | 2 | 2.8 yr | 6 |
| Working (45) | 9 | 2.0 yr | 4 |
| A-list (75) | 15 | 1.5 yr | 1 |

A-list pace of one film per two years matches the real working rhythm of a top director.

## 14.4 Genre cycles — verified ✅

| Metric | Target | Measured |
|---|---|---|
| Share of time a genre is booming | 4–8% | **5%** ✅ |
| Bust years per 60-year history | 10–20 | **14** ✅ |
| Demand standard deviation | 8–12 | **10.0** ✅ |
| Genres booming simultaneously (of 11) | <1 | **0.5** ✅ |

## 14.5 Franchise curve — fitted to real data

The v1 sequel curve declined monotonically from the first sequel. Box-office data shows the **first two installments usually out-earn the third**, with reception bottoming around the fifth or sixth. The v3 curve (§9.5) is fitted to that shape rather than assumed.

## 14.6 Creative decisions — verified ✅

The design goal was *authorship*, not skill checks. These numbers are how you tell the difference.

| Metric | Target | Measured |
|---|---|---|
| corr(audience effect, critic effect) — **must not be one axis** | −0.7 to +0.6, varying by genre | **−0.58 (drama) to +0.52 (horror)** ✅ |
| Genres where the palette is near-orthogonal | ≥2 | **3** (action −0.10, comedy +0.19, sci-fi +0.01) ✅ |
| Palette effect size vs `AudienceScore` sd (7.6) | comparable, not dominant | **±7–10** ✅ |
| Mean coherence of a random palette | 35–50 | **43** ✅ |
| Share of random palettes below coherence 30 | 10–25% | **18%** ✅ |
| Variance multiplier at coherence 32 | 1.7–2.2× | **1.95×** ✅ |
| P(landmark), great director + strange film | 15–25% | **20%** ✅ |
| **Distinct optimal allocations across 16 build×genre pairs** | ≥6 | **8** ✅ |
| Most common allocation's share of those 16 | ≤50% | **6/16 = 38%** ✅ |
| Contrast budget spread, worst build to best | must change *what you can afford* | **3.2 → 6.2** (1 against → 2 against) ✅ |
| Ensemble cost of a showy read vs a steady one | must be real | **−5.1** ✅ |
| Showiest allocation must NOT maximise Notices | required | **shaped 80.9 > showy 78.5** ✅ |

**Two failure conditions to keep testing for.**

If `corr(audience, critic)` goes strongly negative in every genre, the film palette has collapsed into a single commercial-versus-artistic slider and the system has failed. Three genres are deliberately near zero to prevent that.

If the actor's optimal allocation is the *same* across most build-and-genre pairs, the performance system has collapsed into a stat check — which is exactly what happened to an earlier draft that measured contrast as a single distance and produced a publishable *"optimum contrast: 63."* Positions being **named and asymmetric** rather than numeric is the fix; the 8-of-16 spread is how you check it held.

## 14.7 Leverage — verified ✅

| Metric | Target | Measured |
|---|---|---|
| Installments before recasting becomes "unthinkable" | 3–5 | **4** ✅ |
| Break-even Indispensability for a holdout | 65–75 | **70** ✅ |
| P(losing the role) on a holdout at Indispensability 90 | ≥10% | **13%** ✅ |
| Max holdout raise | ≤×2.5 | **×2.40** ✅ |

The holdout must never become free money — a leverage move with no downside is a button, not a decision. The 0.85 cap on `P(they pay)` is what enforces that: studios call bluffs because caving to you sets a precedent across their whole slate.

## 14.8 Decision budget — verified ✅

| Metric | v3 | v4 | Target |
|---|---|---|---|
| Decisions per in-game year (actor + director) | 55 | **19** | ≤20 |
| Decisions per year (actor only) | 43 | **13** | ≤15 |
| Decisions over a 40-year career | 2,200 | **760** | <900 |
| Share of pushed prompts that are administrative | most | **0%** | 0% |

Measured by counting prompts per system per year, not estimated. Full breakdown in §0.2.

## 14.9 Career-shape targets — v9: the first seven are verified, phase 0 built the actor spine only

Phase 0 was scoped to the actor career alone (§0.6, §3.3's spine, minus the director and studio layers). The seven targets below all read off systems phase 0 actually built, and were the test the original v8 draft never ran — §1's finding (this section marked *"to be verified"* while §4.3's Standing formula, the one thing that gates every target here, shipped unverified) is what produced the 0%-of-targets-met result in `callback-design-review.md`. After the §4.3/§4.4/§4.10 fixes above, and again after this session's production rework (§5.6, §6.3–6.4), a 3,000-career simulation hits all seven, every time it's re-run:

| Metric | Target | Measured (n=3,000) |
|---|---|---|
| Median acting career length | 26 years active | 32 |
| Careers reaching Heat > 80 at any point | ~18% | 17% |
| Careers with zero award nominations | ~55% | 50% |
| Award wins per 100 careers | 21 | 12 |
| Median lifetime earnings | $6–11M | $10.0M |
| Top-decile lifetime earnings | $90M+ | $120M |
| Careers surviving the age-42 cliff at lead level | ~30% | 39% |

Three further claims, verified alongside the table above, that don't come from the design doc's own §14.9 list but that the review's method — *simulate the whole career, not the subsystem* — turned out to demand once leverage (Part 6) and the reworked shoot (§5.6) existed: a career that never opens the moves menu at all still meets every target above (Part 6 is genuinely optional, not secretly load-bearing); no single playstyle dominates the six Ambitions (§0.4); and a career played entirely through three real, varying scenes per shoot (§5.6) meets the same seven targets a single-choice shoot always did, confirming the rework changed the interface, not the odds.

**The remaining four targets are still unverified** — they read off systems phase 0 didn't build: the health-plan threshold and addiction/uninsurability beyond a basic health curve (Part 11, mostly unbuilt), the director career to switch into (Part 7, doesn't exist as a playable mode), and the obituary's declined-offer regret count (the obituary exists; this specific figure was never instrumented). They stay targets, not results, until those parts are built.

---

