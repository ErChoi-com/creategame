# PART 13 — BUILD PLAN

| Phase | Scope | Ship criterion |
|---|---|---|
| **0a. Cut list** | Apply Part 0 before writing any code. The Decision Test kills features cheaply on paper and expensively in an engine. | For every system, the optimal play takes more than one sentence to state. |
| **0b. Spreadsheet** | Every formula in Parts 4–11 in a sheet. Simulate headless: 200 acting careers, 200 directing careers, 500 studio-years. | Distributions match Part 14. **Do this before any UI.** The v1 formulas failed this check badly and had to be re-derived — assume yours will too. |
| **1. Actor vertical slice** | One era, one region, 15 NPCs, 6 genres. No scandal, no calendar. | A playtester independently says *"the movie was bad but I was good"* without being told that's possible. If they don't, stop and fix it. |
| **1b. The Work** | The six film dials, coherence, performance contrast, the three on-set moments | Two playtesters given the identical script produce films that are recognisably different and both defensible. Build before the calendar — it's the core loop. |
| **2. Calendar + Deal** | Quarters, overlapping offers, deal terms, agents, packaging | Playtesters visibly agonize over a scheduling conflict. |
| **3. Persona + typecasting** | Affinity vectors, Legibility, break-type arc, the age cliff | Two players describe their actors in different words without prompting. |
| **4. Rolodex** | Full graph, loyalty rosters, NPC arcs | A player names a specific director as their favorite thing in the game. |
| **5. Awards season** | Campaign block, narratives, category fraud, vote splitting | Losing an award feels like a story, not a bad roll. |
| **5b. Leverage** | Favours, approvals, Indispensability, the holdout, the pull-action menu | A player describes a career win that the game never prompted them to attempt. |
| **6. Director career** | Attributes, Taste-as-noise, dev hell, casting from the other side, **the edit as three real choices (§5.8)**, final cut, the Unit | An actor player *chooses* to direct because they got burned in post — not because a menu appeared. |
| **7. Life layer** | Health, addiction + uninsurability, family, caretaking, the money ratchet | A career ends for a reason that has nothing to do with talent, and the player agrees it was fair. |
| **8. Genre & IP layer** | Genre economies, boom/bust cycles, adaptation market, franchise shapes, merchandising, tie-ins, brand money | A player deliberately makes a horror film because it's the only thing they can get financed — and it works. |
| **9. World layer** | Guilds, health-plan cliff, strikes, festivals, territories | A player turns down a good role to hit their health-plan threshold. |
| **10. Studio** | Slate, financing stack, script market, IP decay, date warfare, the board | A player gets fired from a studio and immediately wants to run another one. |
| **11. Eras + regions + legacy** | Tech shifts, obsolescence events, international industries, likeness economy, obituary, second generation | A 60-year run has three distinct acts and the obituary makes someone quiet. |

**Scope reality check.** Phases 0–5 are a complete, shippable game — that's the actor sim, and it's enough. Phase 6 roughly doubles the design surface. Phase 10 doubles it again and is closer to a strategy game than a life sim; it deserves to be evaluated on its own merits and possibly shipped as a separate mode or an expansion.

**The dependency that matters:** the Rolodex (phase 4) must exist before the director career (phase 6), because career-switching is only interesting if relationships carry over. Building the director first produces two disconnected games sharing a menu.

---

