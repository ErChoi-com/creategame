# PART 12 — DATA SCHEMAS

```jsonc
// ── ROLE listing on the offer board ──────────────────────────────
{
  "id": "r_8812", "projectId": "p_2201",
  "characterName": "Marisol Vega",
  "billing": "lead",              // lead | supporting | bit | extra | recurring
  "archetype": "authority",
  "charAge": 47,
  "typeStrictness": 0.8,
  "difficulty": 68,
  "requirements": { "voice": 60, "physicality": 30, "look": 45 },
  "shootWindow": { "startQuarter": 2, "blocks": 2 },
  "flags": ["biographical", "period", "accent_required"]
}

// ── PROJECT ──────────────────────────────────────────────────────
{
  "id": "p_2201", "title": "The Quiet Hours",
  "medium": "film",               // film | tv | limited | theatre | voice
  "genre": "drama", "region": "hollywood",
  "budget": 24, "marketing": 11.5,
  "scriptQuality": 81,            // TRUE value; players see it through Taste noise
  "directorId": "d_04", "studioId": "s_02",
  "gatekeeperProfile": "prestige_auteur",
  "chaos": 0.35,
  "finalCut": "director",         // director | studio | contested
  "shootingStyle": "long_takes",
  "financing": { "equity": 9, "presales": 8, "taxCredit": 5, "gapDebt": 2,
                 "bondCompany": "bc_1", "shootLocation": "budapest" },
  "unit": { "dp": "c_11", "editor": "c_23", "composer": "c_31" },
  "castIds": [], "releaseStrategy": "festival_platform",
  "franchise": { "id": "f_03", "installment": 2 },
  "releaseDate": { "year": 2041, "week": 46 },
  "resolved": { "projectQuality": null, "filmCritic": null, "audience": null,
                "zeitgeist": null, "gross": null, "acquired": null }
}

// ── PLAYER: shared spine across all careers ──────────────────────
{
  "activeCareers": ["actor", "director"],
  "standing": {                    // per region
    "hollywood": { "heat": 58, "prestige": 71, "affection": 63, "notoriety": 22 },
    "europe":    { "heat": 12, "prestige": 44, "affection": 18, "notoriety": 4 }
  },
  "quote": 2.9,
  "calendar": [ { "year": 2041, "q": ["p_2201","p_2201","campaign","caretaking"] } ],
  "rolodex": [ { "npcId": "d_04", "affinity": 78, "grudge": 0,
                 "sharedProjects": 2, "onLoyaltyRoster": true,
                 "flags": ["held_the_line_together"],
                 "simulatedInFull": true, "rivalOf": null } ],  // §10.0's scoping rule:
                                                                  // true only for tracked/rival/
                                                                  // franchise members; everyone
                                                                  // else resolves in aggregate
  "declined": [ { "roleId": "r_7734", "year": 2039, "resolvedProjectId": "p_5561" } ],
    // resolves against the PROJECT schema above — §10.0 cast, made, and reviewed
    // this the same way it would have resolved one of yours

  "actor": {
    "core":  { "craft": 74, "instinct": 61, "presence": 80, "resilience": 49 },
    "gates": { "look": 68, "voice": 55, "physicality": 42 },
    "persona": { "genre": { "drama": 84, "thriller": 52, "comedy": 11 },
                 "archetype": { "authority": 77, "character_actor": 61 },
                 "legibility": 64, "consecutiveSameLane": 3 }
  },

  "director": {
    "attributes": { "vision": 71, "command": 83, "craft": 62,
                    "taste": 44, "efficiency": 39 },
    "signature": { "visual": { "naturalist": 72 }, "tonal": { "bleak": 68 },
                   "thematic": { "family": 81 }, "legibility": 58,
                   "lateStyle": false },
    "devSlate": [ { "scriptId": "sc_88", "momentum": 0.71, "budgetAsk": 30,
                    "attachedStarId": null, "quartersInDev": 6 } ],
    "unit": { "dp": { "id": "c_11", "loyalty": 84 },
              "editor": { "id": "c_23", "loyalty": 91 } },
    "finalCutEarned": true
  },

  "studio": {
    "tier": "independent_producer", "capital": 180,
    "slate": ["p_2201","p_2209"], "library": ["f_03"],
    "executiveStanding": 54, "boardPatience": 2,
    "releaseDatesHeld": [ { "year": 2042, "week": 27, "projectId": "p_2209" } ],
    "talentDeals": [ { "npcId": "a_17", "type": "first_look", "cost": 2.5 } ]
  },

  "life": {
    "health": 71, "conditions": ["knee_reconstruction"],
    "substance": { "stage": "dependence", "insurable": true, "cleanYears": 0 },
    "therapy": true, "burnoutDebt": 14,
    "family": { "partnerId": "n_09", "partnerInIndustry": false,
                "childIds": ["n_44"], "caretakingLoad": 1 },
    "politics": { "positions": ["labor"], "factionStanding": {} },
    "finance": { "netWorth": 12.4, "lifestyleFloor": 3.3, "peakIncome": 6.0,
                 "residualStreams": 0.42, "teamTakePct": 0.22 },
    "guild": { "member": true, "qualifyingEarningsYTD": 19000,
               "healthPlanThreshold": 28000, "pensionYears": 14,
               "strikeRecord": { "held": 2, "crossed": 0 } }
  }
}
```

---

