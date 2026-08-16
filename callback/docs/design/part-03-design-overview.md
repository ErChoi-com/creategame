# PART 3 — CALLBACK: DESIGN OVERVIEW

## 3.1 Pitch

> A career simulator where you play one actor from their first student film to their last. You do not control whether the movie is good. You control what you say yes to, how you prepare, who you keep in the room, and what you're willing to trade. The industry remembers everything, and it changes shape underneath you.

## 3.2 The five pillars

| Pillar | What it replaces in BitLife | One-line statement |
|---|---|---|
| **1. The Performance / Project split** | fused success roll | Your work and the film's fate are separate rolls that only partially correlate. |
| **2. The Persona** | acting skill % | You are not "good at acting," you are *a particular kind of presence* the market prices. |
| **3. The Rolodex** | anonymous NPCs | A persistent graph of ~40 industry figures with memory, careers, and agendas. |
| **4. The Calendar** | one role per year | Time is the scarce resource. Every yes is a no. |
| **5. The Era** | static world | The industry mutates on a 10–15 year cycle and can obsolete you. |

## 3.3 One spine, many careers

Actor, director, and studio executive are three games. They are playable in the same run,
simultaneously or in sequence, and they are only worth building because **they share one
spine** rather than being three parallel systems bolted together:

| Shared system | Actor | Director | Studio |
|---|---|---|---|
| **Standing** (Heat / Prestige / Affection / Notoriety) | your market value | your financing power | your board's patience |
| **Legibility** (the typecasting engine) | Persona — what roles you get | Signature — whether studios will hire you | Brand — what films you're expected to make |
| **The Rolodex** | who casts you | who finances you | who sells to you |
| **The Calendar** | which role you take | which film gets made | which slot on the release grid |
| **Leverage** (Part 6) | favours, indispensability, approvals | favours, final cut, packaging | capital, release dates, talent deals |
| **The Work** (Part 5) | performance dials, contrast, signature | the palette, coherence, the edit | which films get to be difficult |

Career switching is therefore not a mode change: your Rolodex transfers at **100%**,
Prestige at 60%, Heat at 35%. The relationships you built as an actor are the reason
you can get a first feature financed as a director. That is the single design decision
that makes a multi-career game cohere instead of fragment.

**If a newly added career needs its own version of any of those systems, the design is wrong.**
That rule is the whole scope defence.

And because the spine is shared, **there is no career ladder.** You can start as any of them, add
any of them at any age, hold all of them at once, or drop one for a decade and come back. The only
things gating content are Standing, Favours, Indispensability and money — resources, not
permissions. See §6.7.

## 3.4 The core loop

```
        ┌─────────────────────────────────────────────────────┐
        │  SEASON (one in-game year = 4 quarters)             │
        └─────────────────────────────────────────────────────┘
              │
   ┌──────────▼──────────┐
   │ 1. THE OFFER BOARD  │  Roles surface based on Persona fit,
   │                     │  Rolodex relationships, Standing, Quote
   └──────────┬──────────┘
              │  audition / negotiate / decline
   ┌──────────▼──────────┐
   │ 2. THE DEAL         │  Fee vs. backend, billing, options,
   │                     │  schedule blocks consumed
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │ 3. PREP             │  Allocate weeks: coach, research,
   │                     │  physical transformation, dialect
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │ 4. THE SHOOT        │  Event chain. Chemistry, director
   │                     │  conflict, injury, weather, rewrites
   └──────────┬──────────┘
              │  → PERFORMANCE SCORE (yours, private)
   ┌──────────▼──────────┐
   │ 5. POST & RELEASE   │  Edit can help or hurt you. Festival
   │                     │  vs wide vs dumped vs shelved
   └──────────┬──────────┘
              │  → CRITIC SCORE, AUDIENCE SCORE, GROSS
   ┌──────────▼──────────┐
   │ 6. THE SEASON       │  Awards campaign, press, scandal
   │                     │  management, Rolodex maintenance
   └──────────┬──────────┘
              │
   ┌──────────▼──────────┐
   │ 7. RECKONING        │  Standing recalculated. Quote reset.
   │                     │  Persona drift. Body & life costs.
   └──────────┬──────────┘
              └──────────► next season
```

---

