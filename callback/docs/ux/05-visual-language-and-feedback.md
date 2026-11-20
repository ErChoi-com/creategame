# 05 — VISUAL LANGUAGE AND FEEDBACK

Every screen in §01–§04 leans on three patterns repeatedly enough that they need one canonical
definition instead of forty slightly-different reinventions of the same idea. This file is that
definition.

## The words-not-numbers pass

**Every hidden stat in `../design/` converts to player-facing text through the same three-step
pass, every time, in every screen:**

1. **Find the band.** Almost every stat in the mechanics doc already has (or trivially implies) a
   qualitative table — §6.4's Recasts freely → Unthinkable, §4.2's Low/Mid/High Legibility effects,
   the addiction stages in §11.2. Where no band exists yet, one gets defined *once*, in this
   document, and reused everywhere that stat appears — never invented fresh per screen.
2. **Write the band as something a person would say**, not as a label. "Unthinkable" (§6.4) is
   already good; "High Legibility" is not — it should render as "Casting directors know exactly
   what to do with you, and only that." A rule of thumb: if the phrase could appear as a line of
   dialogue from an agent, a director, or a trade headline, it's ready. If it still sounds like a
   UI label, it isn't.
3. **Never show the number behind it, anywhere the player can reach**, including debug-adjacent
   surfaces like a long-press or a stats screen. The four exceptions are Heat, Prestige, Affection,
   and Notoriety (§15) — and even those render as a short bar plus the same qualitative word, the
   number available only via an explicit "show the number" toggle in settings for players who want
   it, off by default.

This is the same pass every screen in §01–§04 already applies to Fit, Indispensability,
Command/Craft, and Notices/Ensemble — `../design/`'s own recent language cleanup pass exists so
that step 2 above has a real gloss to draw from instead of a raw formula name. **A UI implementer
reading this document and `../design/` together should never need to invent player-facing copy for
a stat neither document already glosses; if that happens, the gloss is missing from `../design/`
and belongs there before it belongs in an implementation.**

## The attribution card

One component, reused everywhere an outcome could otherwise read as arbitrary: a short, ordered
list of causes, each rendered as a single clause, always in the order cause precedes effect. §03's
Post & Release screen is the canonical instance (*"Your work: strong. The edit: buried you.
Critics: mixed. Opening: soft."*) but the same component renders:

- A lost audition (*"They wanted someone more established. This one wasn't about you."*)
- A failed holdout (*"They called your bluff. It happens more than agents like to admit."*)
- A scandal's resolution (*"You went quiet. It worked, mostly — but the story ran two more cycles
  than you'd have liked."*)
- The Reckoning's year-end note (§03)

**The card never exceeds four lines.** A causal chain that needs a fifth line to explain itself is
a sign the underlying formula has too many simultaneously-legible inputs for one screen, which is a
`../design/` problem to solve (usually by picking which two or three factors actually matter to
show), not a UI problem to solve by making the card longer.

## Notification and pacing rules

- **A push screen is the only thing allowed to interrupt.** Nothing else — not a trades update, not
  a Rolodex change, not a background film resolving — ever produces a system notification, a badge,
  or an unsolicited full-screen takeover. §02 already states this for the hub; it's restated here
  as a rule that applies to every future screen this document doesn't yet cover (director mode,
  studio mode): **if it isn't one of the seven push moments in §03's loop, it does not interrupt.**
- **The only badge in the entire application** is the trades' once-a-year unread dot (§04). Every
  other pull surface is silent by design, on the theory that a player who wants to know what's new
  in their Rolodex or Leverage catalogue will check, and a player who doesn't shouldn't be nagged
  into caring — matching §0.3 Rule 1's no-upkeep principle exactly.
- **Loading and waiting never simulate suspense the mechanics don't have.** The Performance number
  is genuinely hidden from the player (§4.7) — that's real, earned uncertainty, and the reveal
  screen (§03's Post & Release stop) can sit with it for a beat. A spinner dressed up as tension where the outcome was
  never actually withheld (e.g., artificially delaying an Offer Board refresh) is manufacturing a
  feeling the system doesn't back up, and it reads as such within a session or two.

## Tone and visual register

- **Photographic, not illustrated.** Faces, sets, and posters read as stills from a film that could
  exist, not as stylised avatars — the game's whole premise is that this industry is real enough to
  hurt, and cartoon chrome undercuts that in the first five seconds of every session.
- **Type carries more weight than color.** Given how much of this document is "a sentence, not a
  number," typography — weight, size, one accent color used sparingly for the thing that actually
  changed — is the primary tool for drawing attention, not a palette of status colors. A screen with
  five different colored badges is a screen that stopped trusting its own sentences.
- **Silence is a valid screen state**, not a placeholder waiting to be filled in. An empty quarter
  (§02), a Rolodex entry with nothing new, a trades digest with one quiet line about nothing much —
  all of these are real, intended states, and none of them should be dressed up with filler content
  to avoid looking sparse. The sparseness is the design working.

## What this file deliberately doesn't specify

Exact colors, typefaces, and pixel-level spacing are implementation decisions for whoever builds
this, not design decisions this document needs to lock down — the same relationship §12's data
schemas have to `../design/`'s formulas: this document specifies *what* every screen has to
communicate and in what order; a visual designer chooses the specific *how*. The one constraint
that does carry forward non-negotiably is the three patterns above — the words-not-numbers pass,
the attribution card, and the push/pull interrupt rule — because those aren't style, they're the
UI-level expression of `../design/part-00-design-rules-and-cut-list.md`'s own four rules, and
loosening them loosens the design itself.
